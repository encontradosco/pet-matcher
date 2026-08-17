import io
from PIL import Image
from fastapi.testclient import TestClient

from app import create_app


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


def test_embed_returns_the_vector_and_model_name():
    client = make_test_client()
    resp = client.post(
        '/embed',
        files={'image': ('foto.jpg', make_test_image_bytes(), 'image/jpeg')}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body['embedding'] == [0.1, 0.2, 0.3]
    assert 'model' in body


# FastAPI valida el campo requerido antes de que el código llegue a
# ejecutarse — sin "image" responde 422, no 400. Es el comportamiento
# idiomático del framework, documentado tal cual en el README.
def test_embed_without_image_is_a_client_error():
    client = make_test_client()
    resp = client.post('/embed', files={})
    assert resp.status_code == 422


def test_embed_with_unreadable_bytes_is_a_400():
    client = make_test_client()
    resp = client.post(
        '/embed',
        files={'image': ('foto.jpg', io.BytesIO(b'no es una imagen'), 'image/jpeg')}
    )
    assert resp.status_code == 400
