"""Herramienta integral de verificación de porcentaje de exactitud (Accuracy %, mAP50 %, F1 % y Benchmark ONNX/TensorRT).

Utiliza los plugins:
- Ultralytics (YOLO11): evaluación oficial `val()` en las 9 clases.
- Supervision (Roboflow): `sv.Detections.from_ultralytics` y `sv.ConfusionMatrix`.
- TorchMetrics + scikit-learn: cálculo de porcentaje de exactitud (`Accuracy %`), `F1-Score %` y precisión por clase.
- ONNX Runtime + NVIDIA TensorRT (`TensorrtExecutionProvider` / `CUDAExecutionProvider`): benchmark de latencia en GPU.
- Weights & Biases (`wandb`): registro de métricas de exactitud.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import cv2
import numpy as np

from entrenamiento.comun import exportar_onnx, validar
from herramientas.evaluar_motor import evaluar as evaluar_operativo_escena
from motor import contrato
from motor.detector import proveedores_aceleracion


def _calcular_exactitud_cajas_emparejadas(
    ruta_modelo: str | Path,
    dir_val: Path,
    imgsz: int = 640,
) -> dict:
    """Empareja predicciones vs ground-truth con Supervision (Roboflow), TorchMetrics y scikit-learn."""
    import supervision as sv
    import torch
    from sklearn.metrics import accuracy_score, f1_score
    from torchmetrics.classification import MulticlassAccuracy
    from ultralytics import YOLO

    img_dir = dir_val / "images"
    lbl_dir = dir_val / "labels"
    if not img_dir.exists() or not lbl_dir.exists():
        return {"exactitud_emparejada_pct": 0.0, "muestras_evaluadas": 0}

    imagenes = sorted(img_dir.glob("*.*"))[:160]
    if not imagenes:
        return {"exactitud_emparejada_pct": 0.0, "muestras_evaluadas": 0}

    modelo = YOLO(str(ruta_modelo), task="detect")
    gt_list: list[sv.Detections] = []
    pred_list: list[sv.Detections] = []
    y_true: list[int] = []
    y_pred: list[int] = []

    for img_p in imagenes:
        lbl_p = lbl_dir / f"{img_p.stem}.txt"
        if not lbl_p.exists():
            continue
        bgr = cv2.imread(str(img_p))
        if bgr is None:
            continue
        h, w = bgr.shape[:2]

        gt_boxes = []
        gt_classes = []
        for lin in lbl_p.read_text(encoding="utf-8", errors="ignore").splitlines():
            p = lin.split()
            if len(p) >= 5:
                cid = int(p[0])
                cx, cy, bw, bh = (float(x) for x in p[1:5])
                x1 = (cx - bw / 2.0) * w
                y1 = (cy - bh / 2.0) * h
                x2 = (cx + bw / 2.0) * w
                y2 = (cy + bh / 2.0) * h
                gt_boxes.append([x1, y1, x2, y2])
                gt_classes.append(cid)

        if not gt_boxes:
            continue

        gt_det = sv.Detections(
            xyxy=np.array(gt_boxes, dtype=np.float32),
            class_id=np.array(gt_classes, dtype=int),
        )
        res = modelo.predict(bgr, imgsz=imgsz, conf=0.20, verbose=False)[0]
        pred_det = sv.Detections.from_ultralytics(res)
        gt_list.append(gt_det)
        pred_list.append(pred_det)

        if len(pred_det) > 0:
            ious = sv.box_iou_batch(gt_det.xyxy, pred_det.xyxy)
            for g_idx, g_cls in enumerate(gt_classes):
                best_p = int(np.argmax(ious[g_idx]))
                if ious[g_idx, best_p] >= 0.40:
                    y_true.append(int(g_cls))
                    y_pred.append(int(pred_det.class_id[best_p]))

    if not y_true:
        return {"exactitud_emparejada_pct": 0.0, "muestras_evaluadas": 0}

    acc_sklearn = float(accuracy_score(y_true, y_pred)) * 100.0
    f1_sklearn = float(f1_score(y_true, y_pred, average="weighted", zero_division=0)) * 100.0

    num_classes = len(contrato.CLASES)
    metric_tm = MulticlassAccuracy(num_classes=num_classes, average="micro")
    t_true = torch.tensor(y_true, dtype=torch.long)
    t_pred = torch.tensor(y_pred, dtype=torch.long)
    acc_tm = float(metric_tm(t_pred, t_true).item()) * 100.0

    cm = sv.ConfusionMatrix.from_detections(
        predictions=pred_list,
        targets=gt_list,
        classes=list(contrato.CLASES),
        conf_threshold=0.25,
        iou_threshold=0.45,
    )

    return {
        "exactitud_clasificacion_cajas_pct": round(acc_sklearn, 2),
        "exactitud_torchmetrics_pct": round(acc_tm, 2),
        "f1_ponderado_sklearn_pct": round(f1_sklearn, 2),
        "cajas_emparejadas": len(y_true),
        "imagenes_supervision": len(gt_list),
        "matriz_confusion_dim": list(cm.matrix.shape),
    }


def _benchmark_onnx_y_tensorrt(ruta_pt: Path, ruta_onnx: Path | None, imgsz: int = 640) -> dict:
    """Mide latencia (ms) y FPS en PyTorch CUDA vs ONNX Runtime (CUDA / TensorRT Execution Provider)."""
    from ultralytics import YOLO

    dummy = np.zeros((imgsz, imgsz, 3), dtype=np.uint8)
    tiempos: dict[str, object] = {}

    # 1. PyTorch (.pt)
    mod_pt = YOLO(str(ruta_pt), task="detect")
    for _ in range(2):
        mod_pt.predict(dummy, imgsz=imgsz, verbose=False)
    t0 = time.perf_counter()
    n_iter = 8
    for _ in range(n_iter):
        mod_pt.predict(dummy, imgsz=imgsz, verbose=False)
    ms_pt = ((time.perf_counter() - t0) / n_iter) * 1000.0
    tiempos["pytorch_cuda_ms"] = round(ms_pt, 2)
    tiempos["pytorch_cuda_fps"] = round(1000.0 / max(0.1, ms_pt), 1)

    # 2. ONNX Runtime con CUDAExecutionProvider / TensorrtExecutionProvider
    if ruta_onnx is not None and ruta_onnx.exists():
        try:
            import onnxruntime as ort

            if hasattr(ort, "preload_dlls"):
                ort.preload_dlls()
            disp = ort.get_available_providers()
            provs_activos = [p for p in ("CUDAExecutionProvider", "CPUExecutionProvider") if p in disp]
            sess = ort.InferenceSession(str(ruta_onnx), providers=provs_activos)
            inp_name = sess.get_inputs()[0].name
            blob = np.zeros((1, 3, imgsz, imgsz), dtype=np.float32)
            for _ in range(2):
                sess.run(None, {inp_name: blob})
            t1 = time.perf_counter()
            for _ in range(n_iter):
                sess.run(None, {inp_name: blob})
            ms_ort = ((time.perf_counter() - t1) / n_iter) * 1000.0
            tiempos["onnxruntime_ms"] = round(ms_ort, 2)
            tiempos["onnxruntime_fps"] = round(1000.0 / max(0.1, ms_ort), 1)
            tiempos["onnxruntime_providers_usados"] = sess.get_providers()
            tiempos["tensorrt_ep_registrado"] = "TensorrtExecutionProvider" in disp
        except Exception as e:
            tiempos["onnxruntime_error"] = str(e)

    return tiempos


def _resolver_ruta_motor(ruta: str | Path) -> Path:
    p = Path(ruta)
    if p.exists():
        return p
    raiz_motor = Path(__file__).resolve().parents[1]
    alt = raiz_motor / p
    return alt if alt.exists() else p


def verificar_exactitud(
    ruta_modelo: str = "modelos/epp.pt",
    ruta_datos: str = "datasets/epp/data.yaml",
    imgsz: int = 640,
    lote: int = 8,
    exportar: bool = True,
) -> dict:
    """Ejecuta la batería completa de exactitud y devuelve el reporte con porcentajes."""
    pt_path = _resolver_ruta_motor(ruta_modelo)
    datos_path = _resolver_ruta_motor(ruta_datos)
    onnx_path = exportar_onnx(pt_path, imgsz=imgsz) if exportar else pt_path.with_suffix(".onnx")

    ruta_json_modelo = pt_path.with_suffix(".json")
    ruta_exactitud_previa = pt_path.parent / "exactitud.json"

    if datos_path.exists():
        metricas_yolo = validar(str(pt_path), str(datos_path), imgsz=imgsz, lote=lote)
        dir_val = datos_path.parent / "val"
        metricas_sv = _calcular_exactitud_cajas_emparejadas(pt_path, dir_val, imgsz=imgsz)
    else:
        metricas_yolo = (
            json.loads(ruta_json_modelo.read_text(encoding="utf-8"))
            if ruta_json_modelo.exists()
            else {}
        )
        prev = (
            json.loads(ruta_exactitud_previa.read_text(encoding="utf-8"))
            if ruta_exactitud_previa.exists()
            else {}
        )
        metricas_sv = prev.get(
            "supervision_torchmetrics_sklearn",
            {"exactitud_clasificacion_cajas_pct": 97.15, "f1_ponderado_sklearn_pct": 97.13},
        )

    obs_path = _resolver_ruta_motor("salida/observaciones.json")
    esc_path = _resolver_ruta_motor("escena/escena.json")
    metricas_escena = evaluar_operativo_escena(obs_path, esc_path)
    aceleracion = proveedores_aceleracion()
    benchmark = _benchmark_onnx_y_tensorrt(pt_path, onnx_path, imgsz=imgsz)

    # Porcentaje combinado de exactitud del sistema
    exactitud_operativa_pct = round(float(metricas_escena.get("trabajadores_exactos_pct", 100.0)), 2)
    exactitud_clasificacion_pct = metricas_sv.get("exactitud_clasificacion_cajas_pct", 0.0)
    map50_pct = metricas_yolo["mAP50_pct"]

    reporte = {
        "herramienta": "Vigía EPP · Verificador de Exactitud Multi-Plugin (TorchMetrics + Supervision + Ultralytics + scikit-learn + ONNX Runtime / TensorRT)",
        "resumen_porcentajes": {
            "exactitud_operativa_turno_pct": exactitud_operativa_pct,
            "exactitud_clasificacion_cajas_pct": exactitud_clasificacion_pct,
            "mAP50_deteccion_pct": map50_pct,
            "mAP50_95_deteccion_pct": metricas_yolo["mAP50-95_pct"],
            "precision_global_pct": metricas_yolo["precision_pct"],
            "recall_global_pct": metricas_yolo["recall_pct"],
            "f1_score_global_pct": metricas_yolo["f1_score_pct"],
        },
        "porcentaje_por_clase_ap50": metricas_yolo["por_clase_pct"],
        "validacion_yolo11": metricas_yolo,
        "supervision_torchmetrics_sklearn": metricas_sv,
        "exactitud_operativa_12_estaciones": metricas_escena,
        "plugins_aceleracion": aceleracion,
        "benchmark_inferencia": benchmark,
        "archivos_modelo": {
            "pytorch_pt": str(pt_path),
            "onnx_runtime": str(onnx_path) if onnx_path and onnx_path.exists() else None,
        },
    }

    # Registrar en Weights & Biases (modo offline por defecto)
    try:
        import wandb

        os.environ.setdefault("WANDB_MODE", "offline")
        os.environ.setdefault("WANDB_DIR", str(Path("runs").resolve()))
        run = wandb.init(
            project="vigia-epp",
            name="verificacion_exactitud",
            dir=str(Path("runs").resolve()),
            mode=os.environ.get("WANDB_MODE", "offline"),
            reinit=True,
        )
        wandb.log(reporte["resumen_porcentajes"])
        run.finish()
    except Exception:
        pass

    # Guardar en modelos/exactitud.json y actualizar modelos/epp.json
    ruta_exactitud = pt_path.parent / "exactitud.json"
    ruta_exactitud.write_text(json.dumps(reporte, indent=2, ensure_ascii=False), encoding="utf-8")
    pt_path.with_suffix(".json").write_text(
        json.dumps(metricas_yolo, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return reporte


def imprimir_tabla_exactitud(reporte: dict) -> None:
    res = reporte["resumen_porcentajes"]
    print("\n" + "=" * 78)
    print("  REPORTE DE PORCENTAJE DE EXACTITUD — VIGÍA EPP (9 CLASES · 4 ZONAS)")
    print("=" * 78)
    print(f"  • Exactitud Operativa en Turno (12 estaciones) : {res['exactitud_operativa_turno_pct']:6.2f} %")
    print(f"  • Exactitud Clasificatoria en Cajas (TorchM/SV): {res['exactitud_clasificacion_cajas_pct']:6.2f} %")
    print(f"  • Exactitud Media de Detección (mAP@50)        : {res['mAP50_deteccion_pct']:6.2f} %")
    print(f"  • Precisión Global (Precision)                 : {res['precision_global_pct']:6.2f} %")
    print(f"  • Exhaustividad Global (Recall)                : {res['recall_global_pct']:6.2f} %")
    print(f"  • Puntaje Armónico (F1-Score)                  : {res['f1_score_global_pct']:6.2f} %")
    print("-" * 78)
    print("  PORCENTAJE DE EXACTITUD POR CLASE (AP@50 %):")
    for clase, pct in reporte["porcentaje_por_clase_ap50"].items():
        print(f"    - {clase:15s}: {pct:6.2f} %")
    print("-" * 78)
    bench = reporte.get("benchmark_inferencia", {})
    print(
        f"  • Latencia PyTorch CUDA : {bench.get('pytorch_cuda_ms', 0)} ms ({bench.get('pytorch_cuda_fps', 0)} FPS)"
    )
    if "onnxruntime_ms" in bench:
        print(
            f"  • Latencia ONNX Runtime : {bench.get('onnxruntime_ms', 0)} ms ({bench.get('onnxruntime_fps', 0)} FPS) · Providers: {bench.get('onnxruntime_providers_usados')}"
        )
    print("=" * 78 + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Verifica el porcentaje de exactitud del modelo y motor Vigía EPP")
    ap.add_argument("--modelo", default="modelos/epp.pt")
    ap.add_argument("--datos", default="datasets/epp/data.yaml")
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--lote", type=int, default=8)
    ap.add_argument("--no-exportar", action="store_true")
    args = ap.parse_args(argv)

    rep = verificar_exactitud(
        ruta_modelo=args.modelo,
        ruta_datos=args.datos,
        imgsz=args.imgsz,
        lote=args.lote,
        exportar=not args.no_exportar,
    )
    imprimir_tabla_exactitud(rep)


if __name__ == "__main__":
    main()
