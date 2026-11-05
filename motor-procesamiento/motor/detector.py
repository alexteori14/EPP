"""Envoltura de YOLO11 para las 7 clases de Vigía EPP."""
from __future__ import annotations

from pathlib import Path
import numpy as np

from motor import contrato
from motor.asociar import Deteccion


class DetectorEPP:
    """Detector YOLO11 para `persona`, `chaleco`, `sin_chaleco`, `lentes`, `sin_lentes`, `guantes`, `sin_guantes`."""

    def __init__(
        self,
        ruta_modelo: str | Path = "modelos/epp.pt",
        imgsz: int = 640,
        confianza: float = 0.25,
        dispositivo: str = "auto",
    ):
        from ultralytics import YOLO

        self.ruta_modelo = Path(ruta_modelo)
        self.imgsz = imgsz
        self.confianza = confianza
        self.dispositivo = _resolver_dispositivo(dispositivo)
        self.modelo = YOLO(str(self.ruta_modelo))

    def detectar(self, imagenes: list[np.ndarray]) -> list[list[Deteccion]]:
        if not imagenes:
            return []
        resultados = self.modelo.predict(
            imagenes,
            imgsz=self.imgsz,
            conf=self.confianza,
            device=self.dispositivo,
            verbose=False,
        )
        salida: list[list[Deteccion]] = []
        for r in resultados:
            nombres = r.names
            dets: list[Deteccion] = []
            if r.boxes is not None and len(r.boxes) > 0:
                xyxy = r.boxes.xyxy.cpu().numpy()
                confs = r.boxes.conf.cpu().numpy()
                clss = r.boxes.cls.cpu().numpy().astype(int)
                for caja, conf, cls_id in zip(xyxy, confs, clss):
                    nombre = nombres.get(int(cls_id), str(cls_id))
                    if nombre in contrato.CLASES:
                        dets.append(
                            Deteccion(
                                clase=nombre,
                                confianza=round(float(conf), 4),
                                caja=(float(caja[0]), float(caja[1]), float(caja[2]), float(caja[3])),
                            )
                        )
            salida.append(dets)
        return salida


def _resolver_dispositivo(valor: str) -> str:
    if valor != "auto":
        return valor
    try:
        import torch

        return "cuda:0" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"
