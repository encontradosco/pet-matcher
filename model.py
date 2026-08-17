"""Calcula el embedding de una foto de perro o gato.

*** TEMPORAL, SOLO PARA PROBAR EN LOCAL — NO COMMITEAR ***
Cambiado a AvitoTech/DINO-v2-small-for-animal-identification para comparar
contra el modelo real (CLIP-ViT-base, el que sigue en el commit de Task 4).
Revertir antes de seguir con cualquier tarea del plan.
"""
from transformers import AutoModel, AutoImageProcessor
import torch
import torch.nn.functional as F
import threading

MODEL_NAME = "AvitoTech/DINO-v2-small-for-animal-identification"

_model = None
_processor = None
_load_lock = threading.Lock()


def _load():
    global _model, _processor
    # Flask corre threaded por omisión: sin el lock, dos primeras peticiones
    # a la vez podrían pasar juntas el "if _model is None" de afuera y cada
    # una construir su propia copia del modelo. Doble chequeo — el segundo,
    # ya con el lock tomado — para no pagar el costo del lock en cada
    # petición una vez que el modelo ya está cargado.
    if _model is None:
        with _load_lock:
            if _model is None:
                _processor = AutoImageProcessor.from_pretrained(MODEL_NAME)
                _model = AutoModel.from_pretrained(MODEL_NAME)
                _model.eval()
    return _model, _processor


def embed_image(pil_image):
    model, processor = _load()
    inputs = processor(images=pil_image, return_tensors="pt")
    with torch.no_grad():
        out = model(**inputs).last_hidden_state[:, 0, :]  # CLS token
        out = F.normalize(out, dim=1)
    return out[0].tolist()
