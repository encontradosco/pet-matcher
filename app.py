"""Servicio de embeddings para mascotas. Un único endpoint: recibe una foto,
devuelve un vector. No compara nada y no guarda nada — esa lógica y las
reglas de privacidad viven en encontrados.co (Node), que es quien lo consume.

Sin autenticación todavía — ver README, "Pendiente antes de exponerlo a
internet de verdad". No exponer a internet sin agregarla primero.
"""
import io
from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image

from model import MODEL_NAME, _load, embed_image


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

    @app.post('/embed')
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
