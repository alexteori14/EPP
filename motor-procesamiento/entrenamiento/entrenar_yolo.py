"""Entrena YOLO11n sobre las 9 clases de Vigía EPP (incluyendo tapones y sin_tapones de Kaggle + Roboflow).

Plugins activos durante el entrenamiento y validación:
- Ultralytics (YOLO11) + PyTorch CUDA + OpenCV
- Supervision (Roboflow) + TorchMetrics + scikit-learn (verificador de porcentaje de exactitud)
- Weights & Biases (W&B) para registro de telemetría
- ONNX Runtime + NVIDIA TensorRT Execution Provider (`modelos/epp.onnx`)

    python -m entrenamiento.descargar_kaggle
    python -m entrenamiento.preparar_epp
    python -m entrenamiento.entrenar_yolo
"""
from __future__ import annotations

import argparse

from entrenamiento.comun import entrenar
from entrenamiento.verificar_exactitud import imprimir_tabla_exactitud, verificar_exactitud


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--datos", default="datasets/epp/data.yaml")
    ap.add_argument("--nombre", default="epp_yolo11_9clases")
    ap.add_argument("--epocas", type=int, default=18)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--lote", type=int, default=16, help="16 cabe holgado en la RTX 4050 (6 GB) a 640px")
    ap.add_argument("--base", default="yolo11n.pt")
    ap.add_argument("--modelo", default="modelos/epp.pt")
    args = ap.parse_args(argv)

    entrenar(
        args.datos,
        args.nombre,
        args.epocas,
        args.imgsz,
        args.base,
        args.lote,
        args.modelo,
        fliplr=0.5,
        flipud=0.0,
        degrees=5.0,
        mosaic=0.8,
        close_mosaic=4,
        workers=4,
    )
    reporte = verificar_exactitud(
        ruta_modelo=args.modelo,
        ruta_datos=args.datos,
        imgsz=args.imgsz,
        lote=args.lote,
        exportar=True,
    )
    imprimir_tabla_exactitud(reporte)


if __name__ == "__main__":
    main()
