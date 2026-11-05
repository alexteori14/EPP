"""Evaluación en tiempo real para el Kiosco de Inicio de Turno (<300 ms por cuadro/foto)."""
from __future__ import annotations

import base64
import time
import cv2
import numpy as np

from motor import anotar, contrato
from motor.asociar import asociar_cuadro
from motor.detector import DetectorEPP


def evaluar_imagen(
    imagen_bgr: np.ndarray,
    detector: DetectorEPP | None = None,
    modelo: str = "modelos/epp.pt",
) -> dict:
    """Evalúa un cuadro de la cámara del Kiosco o una foto subida y emite el pase de turno."""
    t0 = time.perf_counter()
    if detector is None:
        detector = DetectorEPP(modelo)

    h, w = imagen_bgr.shape[:2]
    dets = detector.detectar([imagen_bgr])[0]
    personas = asociar_cuadro(dets, ancho=w, alto=h, cuadro=0)

    if not personas:
        _, buf = cv2.imencode(".jpg", imagen_bgr, [cv2.IMWRITE_JPEG_QUALITY, 85])
        b64 = base64.b64encode(buf.tobytes()).decode("ascii")
        return {
            "personas_detectadas": 0,
            "estado_acceso": "sin_persona",
            "mensaje": "Sin trabajador frente al kiosco. Colócate de frente dentro del recuadro.",
            "prendas_completas": 0,
            "prendas_requeridas": len(contrato.PRENDAS),
            "faltantes": [],
            "dudosas": list(contrato.PRENDAS),
            "zonas": {
                pr: {
                    "nombre": contrato.NOMBRES_PRENDA[pr],
                    "estado": "dudoso",
                    "confianza": 0.0,
                }
                for pr in contrato.PRENDAS
            },
            "accion_caseta": "Esperando trabajador en zona de escaneo.",
            "ms_proceso": round((time.perf_counter() - t0) * 1000, 1),
            "imagen_anotada_b64": f"data:image/jpeg;base64,{b64}",
        }

    # Elegir a la persona principal (la de mayor área en cámara)
    principal = max(
        personas,
        key=lambda p: (p.caja[2] - p.caja[0]) * (p.caja[3] - p.caja[1]),
    )

    faltantes = [pr for pr in contrato.PRENDAS if principal.prendas[pr].estado == "falta"]
    dudosas = [pr for pr in contrato.PRENDAS if principal.prendas[pr].estado == "dudoso"]
    completas = sum(1 for pr in contrato.PRENDAS if principal.prendas[pr].estado == "ok")

    if faltantes:
        estado_acceso = "bloqueado"
        nombres_f = ", ".join(contrato.NOMBRES_PRENDA[p] for p in faltantes)
        mensaje = f"Acceso detenido: falta {nombres_f}."
        accion = f"Entregar en caseta: {nombres_f} antes de abrir torniquete."
        titulo_img = f"BLOQUEADO ({completas}/3 EPP)"
    elif dudosas:
        estado_acceso = "revisar"
        nombres_d = ", ".join(contrato.NOMBRES_PRENDA[p] for p in dudosas)
        mensaje = f"Lectura dudosa en {nombres_d}. Acércate de frente a la cámara."
        accion = f"Confirmar visualmente {nombres_d} en caseta."
        titulo_img = f"VERIFICAR ({completas}/3 EPP)"
    else:
        estado_acceso = "autorizado"
        mensaje = "Pase de turno autorizado: EPP obligatorio completo (Lentes, Chaleco y Guantes)."
        accion = "Ingreso autorizado a piso de planta."
        titulo_img = "AUTORIZADO (3/3 EPP)"

    img_anotada = anotar.dibujar_persona(imagen_bgr, principal, titulo_img)
    _, buf = cv2.imencode(".jpg", img_anotada, [cv2.IMWRITE_JPEG_QUALITY, 88])
    b64 = base64.b64encode(buf.tobytes()).decode("ascii")

    return {
        "personas_detectadas": len(personas),
        "estado_acceso": estado_acceso,
        "mensaje": mensaje,
        "prendas_completas": completas,
        "prendas_requeridas": len(contrato.PRENDAS),
        "faltantes": faltantes,
        "dudosas": dudosas,
        "zonas": {
            pr: {
                "nombre": contrato.NOMBRES_PRENDA[pr],
                "estado": principal.prendas[pr].estado,
                "confianza": round(principal.prendas[pr].confianza, 3),
            }
            for pr in contrato.PRENDAS
        },
        "accion_caseta": accion,
        "ms_proceso": round((time.perf_counter() - t0) * 1000, 1),
        "imagen_anotada_b64": f"data:image/jpeg;base64,{b64}",
    }
