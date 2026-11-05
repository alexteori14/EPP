"""Selección del cuadro más nítido por ventana (varianza del Laplaciano), heredado de Ubik."""
from __future__ import annotations

import queue
import threading
from dataclasses import dataclass
from typing import Iterator

import cv2
import numpy as np


@dataclass
class InfoVideo:
    cuadros: int
    fps: float
    ancho: int
    alto: int
    segundos: float


@dataclass
class CuadroElegido:
    indice: int
    nitidez: float
    imagen: np.ndarray


def info_video(ruta: str) -> InfoVideo:
    cap = cv2.VideoCapture(ruta)
    if not cap.isOpened():
        raise ValueError(f"No se pudo abrir el video: {ruta}")
    cuadros = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0) or 30.0
    ancho = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    alto = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    cap.release()
    return InfoVideo(
        cuadros=cuadros,
        fps=fps,
        ancho=ancho,
        alto=alto,
        segundos=round(cuadros / fps, 2) if fps > 0 else 0.0,
    )


def nitidez_laplaciano(bgr: np.ndarray) -> float:
    """Varianza del Laplaciano en gris a resolución reducida (~480 px de ancho) para velocidad."""
    gris = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY) if bgr.ndim == 3 else bgr
    h, w = gris.shape[:2]
    if w > 480:
        escala = 480.0 / w
        gris = cv2.resize(gris, (480, max(1, int(h * escala))), interpolation=cv2.INTER_AREA)
    return float(cv2.Laplacian(gris, cv2.CV_64F).var())


def elegir_cuadros(ruta: str, cada: int = 12) -> Iterator[CuadroElegido]:
    """Devuelve el cuadro más nítido de cada ventana de `cada` cuadros."""
    cap = cv2.VideoCapture(ruta)
    if not cap.isOpened():
        raise ValueError(f"No se pudo abrir el video: {ruta}")
    ventana = max(1, int(cada))
    mejor: CuadroElegido | None = None
    idx = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                break
            nit = nitidez_laplaciano(frame)
            if mejor is None or nit > mejor.nitidez:
                mejor = CuadroElegido(indice=idx, nitidez=nit, imagen=frame)
            idx += 1
            if idx % ventana == 0 and mejor is not None:
                yield mejor
                mejor = None
        if mejor is not None:
            yield mejor
    finally:
        cap.release()


def elegir_cuadros_en_hilo(ruta: str, cada: int = 12, buffer: int = 4) -> Iterator[CuadroElegido]:
    """Decodifica y selecciona cuadros nítidos en un hilo de fondo mientras la GPU infiere."""
    cola: queue.Queue[CuadroElegido | None] = queue.Queue(maxsize=buffer)

    def _productor():
        try:
            for c in elegir_cuadros(ruta, cada):
                cola.put(c)
        finally:
            cola.put(None)

    threading.Thread(target=_productor, daemon=True).start()
    while True:
        item = cola.get()
        if item is None:
            break
        yield item
