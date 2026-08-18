# pet-matcher

Servicio de embeddings para fotos de mascotas (perros y gatos). Un único
endpoint: recibe una foto, devuelve un vector de 384 números. No compara
nada y no guarda nada — eso, y las reglas de privacidad, viven en
[encontrados.co](https://github.com/encontradosco/encontrados) (Node), que
es quien lo consume.

Modelo: [`AvitoTech/DINO-v2-small-for-animal-identification`](https://huggingface.co/AvitoTech/DINO-v2-small-for-animal-identification)
— 22M parámetros, afinado sobre 695.091 individuos (perros y gatos), elegido
tras comparar 5 candidatos con datos reales: casi el mismo desempeño que el
mejor de los 5, con casi 7 veces menos parámetros (22.1M vs. 151.3M).

## Instalar y correr local

    python3.11 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    python app.py

Queda escuchando en http://localhost:5001. (Python 3.11 explícito: `torch`
no publica wheel para todas las versiones de Python — 3.9, por ejemplo, no
tiene la build que pide `requirements.txt`.)

## Probar

    pytest -v

Las pruebas usan una función `embed_fn` de mentira inyectada en `create_app`
— no descargan el modelo real. Verificación manual contra el modelo real:

    export PET_MATCH_SHARED_SECRET=una-prueba-cualquiera
    python app.py &
    curl -s -H "x-pet-matcher-secret: $PET_MATCH_SHARED_SECRET" \
      -F "image=@/ruta/a/una/foto/de/perro-o-gato.jpg" http://localhost:5001/embed \
      | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d['embedding']), d['model'])"

Debe imprimir `384 AvitoTech/DINO-v2-small-for-animal-identification`.

## Contrato

`POST /embed`, multipart con el campo `image`, con el header
`x-pet-matcher-secret` → `{ "embedding": [...], "model": "..." }`. Sin el
header o con el secreto equivocado: `401`. Si el servidor no tiene
`PET_MATCH_SHARED_SECRET` configurado: `503` (falla cerrado — nunca acepta
fotos sin secreto). Con el secreto correcto pero sin el campo `image`: `422`
(validación automática de FastAPI). Con una imagen ilegible: `400`.

`GET /health` no pide secreto — es lo que un orquestador (Fly, el que sea)
usa para preguntar "¿estás vivo?", y no expone nada sensible.

## Autenticación

Mismo patrón que ya usa encontrados.co para su webhook de WhatsApp
(`WHATSAPP_RELAY_SECRET`): un secreto compartido en una variable de entorno,
mandado como header en cada petición a `/embed`. Generar uno:

    openssl rand -hex 32

Poner ese valor en `PET_MATCH_SHARED_SECRET` de este servicio, y el mismo
valor en `PET_MATCH_SHARED_SECRET` del lado de encontrados.co.

## Desplegar con Docker

    docker build -t pet-matcher .
    docker run -p 5001:5001 -e PET_MATCH_SHARED_SECRET=un-secreto-de-verdad pet-matcher

## Desplegado en Fly.io

`pet-matcher.fly.dev`, org `encontrados` de Fly, cuenta de pago —
`fly.toml` deja `min_machines_running = 1`: siempre prendida, sin cold
starts. Cada push a `main` la despliega solo, vía
`.github/workflows/fly-deploy.yml` (mismo principio que "mergear es
desplegar" en encontrados.co: no queda nada pendiente entre el merge y que
el cambio esté vivo). El token vive en el secret `FLY_API_TOKEN` del repo,
limitado a esta app, con vencimiento — hay que regenerarlo cuando expire
(`flyctl tokens create deploy -a pet-matcher`).

Para desplegar a mano (sin esperar el push):

    flyctl deploy

Un solo worker de `uvicorn` a propósito — ver el comentario en `Dockerfile`.

## Pendiente antes de exponerlo a internet de verdad

- Sin límite de tamaño de imagen aceptada.
