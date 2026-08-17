# pet-matcher

Servicio de embeddings para fotos de mascotas (perros y gatos). Un único
endpoint: recibe una foto, devuelve un vector de 384 números. No compara
nada y no guarda nada — eso, y las reglas de privacidad, viven en
[encontrados.co](https://github.com/encontradosco/encontrados) (Node), que
es quien lo consume.

Modelo: [`AvitoTech/DINO-v2-small-for-animal-identification`](https://huggingface.co/AvitoTech/DINO-v2-small-for-animal-identification)
— 22M parámetros, afinado sobre 695.091 individuos (perros y gatos), elegido
tras comparar 5 candidatos con datos reales: casi el mismo desempeño que el
mejor de los 5, con 9 veces menos parámetros.

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

    python app.py &
    curl -s -F "image=@/ruta/a/una/foto/de/perro-o-gato.jpg" http://localhost:5001/embed \
      | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d['embedding']), d['model'])"

Debe imprimir `384 AvitoTech/DINO-v2-small-for-animal-identification`.

## Contrato

`POST /embed`, multipart con el campo `image` →
`{ "embedding": [...], "model": "..." }`. Sin el campo `image`: `422`
(validación automática de FastAPI). Con una imagen ilegible: `400`.

## Desplegar con Docker

    docker build -t pet-matcher .
    docker run -p 5001:5001 pet-matcher

Un solo worker de `uvicorn` a propósito — ver el comentario en `Dockerfile`.

## Pendiente antes de exponerlo a internet de verdad

- **Sin autenticación todavía.** Cualquiera que tenga la URL puede mandarle
  fotos gratis. Falta un secreto compartido antes de un despliegue real
  (mismo patrón que ya usa encontrados.co para su webhook de WhatsApp).
- Sin límite de tamaño de imagen aceptada.
