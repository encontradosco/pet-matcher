"""Servicio de embeddings para mascotas. Un único endpoint: recibe una foto,
devuelve un vector. No compara nada y no guarda nada — esa lógica y las
reglas de privacidad viven en encontrados.co (Node), que es quien lo consume.
"""
import hmac
import io
import os
from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from PIL import Image

from model import MODEL_NAME, _load, embed_image

SECRET_HEADER = 'x-pet-matcher-secret'


# Se lee el valor EN CADA petición, no una vez al arrancar — mismo motivo que
# ya usa notify.js del lado Node para su buzón de avisos: la variable puede
# cambiar entre despliegues sin reiniciar el proceso, y una copia congelada
# se desincroniza sola.
#
# Falla CERRADO si no hay secreto configurado — mismo criterio que
# WHATSAPP_RELAY_SECRET del lado de encontrados.co: un servicio que acepta
# fotos gratis de cualquiera en internet es peor que uno que no arranca. Para
# correr local sin pensar en esto, basta con poner cualquier valor de prueba
# en PET_MATCH_SHARED_SECRET.
def require_shared_secret(x_pet_matcher_secret: str = Header(default='', alias=SECRET_HEADER)):
    expected = os.environ.get('PET_MATCH_SHARED_SECRET')
    if not expected:
        raise HTTPException(status_code=503, detail='PET_MATCH_SHARED_SECRET no está configurado en el servidor')
    if not x_pet_matcher_secret or not hmac.compare_digest(x_pet_matcher_secret, expected):
        raise HTTPException(status_code=401, detail='secreto inválido o ausente')


def create_app(embed_fn=None):
    app = FastAPI()
    if embed_fn is None:
        # Cargar el modelo AL ARRANCAR, no en la primera petición — así el
        # primer reporte real no paga el costo de la descarga/carga del
        # modelo. El camino de pruebas (embed_fn inyectado) nunca debe tocar
        # el modelo real, así que este _load() eager solo corre cuando NO
        # hay una función de mentira.
        _load()
        embed = embed_image
    else:
        embed = embed_fn

    # Para que Fly (o cualquier orquestador) pueda preguntar "¿estás vivo?"
    # con un GET simple — /embed exige una foto, así que no sirve para esto.
    # Sin el secreto a propósito: no expone nada sensible, y un chequeo de
    # salud que necesita autenticación deja de servir para lo que existe.
    @app.get('/health')
    async def health():
        return {'status': 'ok'}

    @app.post('/embed', dependencies=[Depends(require_shared_secret)])
    async def embed_route(image: UploadFile = File(...)):
        raw = await image.read()
        try:
            pil_image = Image.open(io.BytesIO(raw)).convert('RGB')
        except Exception:
            raise HTTPException(status_code=400, detail='no se pudo leer la imagen')
        vector = embed(pil_image)
        return {'embedding': vector, 'model': MODEL_NAME}

    return app


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(create_app(), host='0.0.0.0', port=5001)
