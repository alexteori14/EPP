"""Entrenamiento YOLO11 reanudable y validación por clase (adaptado y mejorado de Ubik)."""
from __future__ import annotations

import shutil
from pathlib import Path


def entrenar(
    datos: str,
    nombre: str,
    epocas: int,
    imgsz: int,
    base: str,
    lote: int,
    destino: str,
    proyecto: str = "runs",
    **extra,
) -> Path:
    """Entrena (o reanuda si se interrumpió) y copia best.pt a `destino`."""
    from ultralytics import YOLO

    carpeta = Path(proyecto).resolve() / nombre
    ultimo = carpeta / "weights" / "last.pt"
    mejor = carpeta / "weights" / "best.pt"
    terminado = (carpeta / "results.csv").exists() and _epocas_hechas(carpeta) >= epocas
    if ultimo.exists() and not terminado:
        print(f"reanudando entrenamiento desde {ultimo}")
        try:
            YOLO(str(ultimo)).train(resume=True)
        except AssertionError as e:
            print(f"no hay nada que reanudar ({e})")
    elif not terminado:
        YOLO(base).train(
            data=datos,
            epochs=epocas,
            imgsz=imgsz,
            batch=lote,
            project=str(carpeta.parent),
            name=nombre,
            exist_ok=True,
            patience=0,
            **extra,
        )
    else:
        print(f"{nombre} ya completó {epocas} épocas")
    Path(destino).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(mejor, destino)
    return mejor


def _epocas_hechas(carpeta: Path) -> int:
    lineas = (carpeta / "results.csv").read_text(encoding="utf-8").strip().splitlines()
    return max(0, len(lineas) - 1)


def validar(modelo: str, datos: str, imgsz: int, lote: int = 8) -> dict:
    from ultralytics import YOLO

    m = YOLO(modelo).val(
        data=datos,
        imgsz=imgsz,
        batch=lote,
        split="val",
        plots=False,
        verbose=False,
    )
    por_clase = {
        m.names[i]: round(float(m.box.ap50[k]), 4)
        for k, i in enumerate(m.box.ap_class_index)
    }
    return {
        "mAP50": round(float(m.box.map50), 4),
        "mAP50-95": round(float(m.box.map), 4),
        "precision": round(float(m.box.mp), 4),
        "recall": round(float(m.box.mr), 4),
        "por_clase": por_clase,
    }
