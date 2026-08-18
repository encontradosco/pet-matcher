import io
from PIL import Image
from fastapi.testclient import TestClient

from app import create_app

TEST_SECRET = 'prueba-secreta-no-usar-en-produccion'


def fake_embed(image):
    return [0.1, 0.2, 0.3]


def make_test_client():
    return TestClient(create_app(embed_fn=fake_embed))


def make_test_image_bytes():
    img = Image.new('RGB', (10, 10), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    buf.seek(0)
    return buf


def test_health_is_ok_and_never_needs_the_secret(monkeypatch):
    monkeypatch.delenv('PET_MATCH_SHARED_SECRET', raising=False)
    client = make_test_client()
    resp = client.get('/health')
    assert resp.status_code == 200
    assert resp.json() == {'status': 'ok'}


def test_embed_without_the_secret_configured_fails_closed(monkeypatch):
    monkeypatch.delenv('PET_MATCH_SHARED_SECRET', raising=False)
    client = make_test_client()
    resp = client.post(
        '/embed',
        files={'image': ('foto.jpg', make_test_image_bytes(), 'image/jpeg')}
    )
    assert resp.status_code == 503


def test_embed_with_the_wrong_secret_is_a_401(monkeypatch):
    monkeypatch.setenv('PET_MATCH_SHARED_SECRET', TEST_SECRET)
    client = make_test_client()
    resp = client.post(
        '/embed',
        files={'image': ('foto.jpg', make_test_image_bytes(), 'image/jpeg')},
        headers={'x-pet-matcher-secret': 'no-es-el-secreto-correcto'}
    )
    assert resp.status_code == 401


def test_embed_without_any_secret_header_is_a_401(monkeypatch):
    monkeypatch.setenv('PET_MATCH_SHARED_SECRET', TEST_SECRET)
    client = make_test_client()
    resp = client.post(
        '/embed',
        files={'image': ('foto.jpg', make_test_image_bytes(), 'image/jpeg')}
    )
    assert resp.status_code == 401


def test_embed_with_the_right_secret_returns_the_vector_and_model_name(monkeypatch):
    monkeypatch.setenv('PET_MATCH_SHARED_SECRET', TEST_SECRET)
    client = make_test_client()
    resp = client.post(
        '/embed',
        files={'image': ('foto.jpg', make_test_image_bytes(), 'image/jpeg')},
        headers={'x-pet-matcher-secret': TEST_SECRET}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body['embedding'] == [0.1, 0.2, 0.3]
    assert 'model' in body


def test_embed_with_the_right_secret_but_no_image_is_a_client_error(monkeypatch):
    monkeypatch.setenv('PET_MATCH_SHARED_SECRET', TEST_SECRET)
    client = make_test_client()
    resp = client.post('/embed', files={}, headers={'x-pet-matcher-secret': TEST_SECRET})
    assert resp.status_code == 422


def test_embed_with_the_right_secret_but_unreadable_bytes_is_a_400(monkeypatch):
    monkeypatch.setenv('PET_MATCH_SHARED_SECRET', TEST_SECRET)
    client = make_test_client()
    resp = client.post(
        '/embed',
        files={'image': ('foto.jpg', io.BytesIO(b'no es una imagen'), 'image/jpeg')},
        headers={'x-pet-matcher-secret': TEST_SECRET}
    )
    assert resp.status_code == 400
