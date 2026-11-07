"""Entrenamiento YOLO11 reanudable, telemetría Weights & Biases (W&B) y exportación ONNX Runtime / TensorRT."""
from __future__ import annotations

import os
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
    usar_wandb: bool = True,
    **extra,
) -> Path:
    """Entrena (o reanuda si se interrumpió), registra en W&B y copia best.pt a `destino`."""
    from ultralytics import YOLO

    # Configurar Weights & Biases en modo offline por defecto si no hay WANDB_API_KEY
    if usar_wandb and not os.environ.get("WANDB_API_KEY"):
        os.environ.setdefault("WANDB_MODE", "offline")
    os.environ.setdefault("WANDB_DIR", str(Path(proyecto).resolve()))

    wb_run = None
    if usar_wandb:
        try:
            import wandb

            wb_run = wandb.init(
                project="vigia-epp",
                name=nombre,
                dir=str(Path(proyecto).resolve()),
                mode=os.environ.get("WANDB_MODE", "offline"),
                config={
                    "datos": datos,
                    "epocas": epocas,
                    "imgsz": imgsz,
                    "base": base,
                    "batch": lote,
                    "clases": 9,
                },
                reinit=True,
            )
        except Exception as e:
            print(f"[W&B] aviso de inicialización ({e}); continuando entrenamiento local.")

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

    if wb_run is not None:
        try:
            wb_run.finish()
        except Exception:
            pass
    return mejor


def exportar_onnx(ruta_pt: str | Path = "modelos/epp.pt", imgsz: int = 640) -> Path | None:
    """Exporta el modelo entrenado `.pt` a `.onnx` para aceleración con ONNX Runtime y TensorRT Execution Provider."""
    from ultralytics import YOLO

    pt_path = Path(ruta_pt)
    if not pt_path.exists():
        return None
    try:
        exportado = YOLO(str(pt_path)).export(format="onnx", imgsz=imgsz, simplify=True)
        onnx_path = Path(exportado)
        destino_onnx = pt_path.with_suffix(".onnx")
        if onnx_path.resolve() != destino_onnx.resolve():
            shutil.copy(onnx_path, destino_onnx)
        return destino_onnx
    except Exception as e:
        print(f"[ONNX] aviso en exportación ({e})")
        return None


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
    por_clase_pct = {
        nombre: round(val * 100.0, 2) for nombre, val in por_clase.items()
    }
    map50 = round(float(m.box.map50), 4)
    map50_95 = round(float(m.box.map), 4)
    prec = round(float(m.box.mp), 4)
    rec = round(float(m.box.mr), 4)
    f1 = round((2 * prec * rec) / max(1e-8, prec + rec), 4)
    return {
        "mAP50": map50,
        "mAP50_pct": round(map50 * 100.0, 2),
        "mAP50-95": map50_95,
        "mAP50-95_pct": round(map50_95 * 100.0, 2),
        "precision": prec,
        "precision_pct": round(prec * 100.0, 2),
        "recall": rec,
        "recall_pct": round(rec * 100.0, 2),
        "f1_score": f1,
        "f1_score_pct": round(f1 * 100.0, 2),
        "por_clase": por_clase,
        "por_clase_pct": por_clase_pct,
    }
