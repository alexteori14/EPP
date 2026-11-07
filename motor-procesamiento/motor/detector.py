"""Envoltura de YOLO11 para las 9 clases de Vigía EPP con soporte multi-plugin.

Plugins integrados:
- Ultralytics (YOLO11): Inferencia nativa sobre `.pt`, `.onnx` y `.engine`.
- PyTorch + OpenCV: Aceleración CUDA en GPU NVIDIA y preprocesamiento BGR.
- Supervision (Roboflow): Conversión estandarizada `sv.Detections.from_ultralytics` y anotadores `sv.BoxAnnotator`.
- ONNX Runtime + NVIDIA TensorRT: Soporte de sesión acelerada con `TensorrtExecutionProvider` y `CUDAExecutionProvider`.
"""
from __future__ import annotations

from pathlib import Path
import numpy as np

from motor import contrato
from motor.asociar import Deteccion


class DetectorEPP:
    """Detector YOLO11 para las 9 clases de Vigía EPP (`persona`, `chaleco`, `sin_chaleco`, `lentes`, `sin_lentes`, `guantes`, `sin_guantes`, `tapones`, `sin_tapones`)."""

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
        self.modelo = YOLO(str(self.ruta_modelo), task="detect")

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

    def detectar_supervision(self, imagenes: list[np.ndarray]) -> list:
        """Ejecuta detección devolviendo objetos `supervision.Detections` (plugin Supervision de Roboflow)."""
        import supervision as sv

        if not imagenes:
            return []
        resultados = self.modelo.predict(
            imagenes,
            imgsz=self.imgsz,
            conf=self.confianza,
            device=self.dispositivo,
            verbose=False,
        )
        return [sv.Detections.from_ultralytics(r) for r in resultados]


def anotar_con_supervision(imagen_bgr: np.ndarray, detecciones: list[Deteccion]) -> np.ndarray:
    """Renderiza cajas delimitadoras y etiquetas utilizando `supervision` (Roboflow)."""
    import supervision as sv

    if not detecciones:
        return imagen_bgr.copy()
    xyxy = np.array([d.caja for d in detecciones], dtype=np.float32)
    confidence = np.array([d.confianza for d in detecciones], dtype=np.float32)
    class_id = np.array(
        [contrato.CLASES.index(d.clase) if d.clase in contrato.CLASES else 0 for d in detecciones],
        dtype=int,
    )
    det_sv = sv.Detections(xyxy=xyxy, confidence=confidence, class_id=class_id)
    etiquetas = [f"{d.clase} {d.confianza * 100:.0f}%" for d in detecciones]
    box_annotator = sv.BoxAnnotator(thickness=2)
    label_annotator = sv.LabelAnnotator(text_scale=0.45, text_thickness=1)
    escena = box_annotator.annotate(scene=imagen_bgr.copy(), detections=det_sv)
    return label_annotator.annotate(scene=escena, detections=det_sv, labels=etiquetas)


def proveedores_aceleracion() -> dict[str, object]:
    """Inspecciona el estado de los plugins de aceleración PyTorch CUDA, ONNX Runtime y NVIDIA TensorRT."""
    info: dict[str, object] = {
        "pytorch_cuda": False,
        "gpu_nombre": "CPU",
        "onnxruntime_version": None,
        "onnxruntime_providers": [],
        "tensorrt_provider_disponible": False,
        "cuda_provider_disponible": False,
    }
    try:
        import torch

        info["pytorch_version"] = torch.__version__
        info["pytorch_cuda"] = bool(torch.cuda.is_available())
        if info["pytorch_cuda"]:
            info["gpu_nombre"] = torch.cuda.get_device_name(0)
    except Exception:
        pass
    try:
        import onnxruntime as ort

        provs = list(ort.get_available_providers())
        info["onnxruntime_version"] = ort.__version__
        info["onnxruntime_providers"] = provs
        info["tensorrt_provider_disponible"] = "TensorrtExecutionProvider" in provs
        info["cuda_provider_disponible"] = "CUDAExecutionProvider" in provs
    except Exception:
        pass
    return info


def _resolver_dispositivo(valor: str) -> str:
    if valor != "auto":
        return valor
    try:
        import torch

        return "cuda:0" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"
