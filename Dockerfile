FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py model.py ./

EXPOSE 5001

# --factory: uvicorn llama a create_app() él mismo, en vez de importar una
# instancia ya construida a nivel de módulo — así test_app.py puede
# importar app.py sin disparar la carga del modelo real (ver create_app en
# app.py). Un solo worker a propósito: cada worker cargaría su propia copia
# del modelo en memoria, y no hace falta más de uno para el tráfico que
# espera este servicio.
CMD ["uvicorn", "app:create_app", "--factory", "--host", "0.0.0.0", "--port", "5001"]
