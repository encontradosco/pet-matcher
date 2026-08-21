# Cómo contribuir

`pet-matcher` es el servicio de embeddings que consume
[encontrados.co](https://github.com/encontradosco/encontrados) para
comparar fotos de mascotas. No guarda nada y no decide nada por su cuenta
— pero si responde mal o se cae, encontrados.co pierde esa función en
medio de una emergencia real. Vale la pena leer esto antes del primer PR.

## Correr local

    python3.11 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    python app.py

Python 3.11 explícito — `torch` no publica wheel para todas las versiones
(detalle en el README).

## Tests

    pytest -v

En verde antes de abrir el PR. Corren contra un `embed_fn` de mentira
inyectado en `create_app` — nunca descargan el modelo real, así que no
necesitas GPU ni red para trabajar.

## Cómo se manda un cambio

**PRs pequeños, sobre `main`.** `main` es producción: cada push la
despliega solo vía `.github/workflows/fly-deploy.yml` — mergear *es*
desplegar, no queda nada pendiente entre el merge y que el cambio esté
vivo. Una rama grande vive más de lo que debería y compite con lo que
sea que alguien más toque después.

1. Rama fresca sobre el `main` actual.
2. `pytest -v` en verde — el CI lo corre igual, pero corrarlo local antes
   ahorra una vuelta.
3. En la descripción: qué cambiaste y cómo lo probaste. Si tocaste
   `fly.toml`, `Dockerfile` o algo del chequeo de secreto en `app.py`,
   dilo explícito — ese cambio se siente en producción apenas se
   mergea.

## Reglas duras

**Nunca subas el secreto real.** `PET_MATCH_SHARED_SECRET` de producción
no va en un test, un commit ni un comentario de PR. Los tests usan un
valor de mentira (ver `test_app.py`); sigue esa convención.

**Nunca subas una foto real** de una mascota o de una persona en un
fixture o un test. Las pruebas generan una imagen en memoria
(`Image.new(...)` en `test_app.py`) — así se quedan.

## La revisión

Un PR necesita `pytest -v` en verde y la aprobación de un mantenedor
listado en [CODEOWNERS](.github/CODEOWNERS). Los cambios a `.github/`,
`fly.toml`, `Dockerfile` o `app.py` tocan el despliegue o el perímetro de
seguridad del servicio — ahí CODEOWNERS pide la aprobación de uno de los
mantenedores core sí o sí, sin excepción de "es un cambio chico".

## El código

Es un solo endpoint — sin abstracciones de más. Antes de agregar una
dependencia nueva a `requirements.txt`, pregúntate si el problema se
resuelve sin ella. Los comentarios explican **por qué**, no qué: el qué
ya está en el código.
