"""Entrena YOLO11n sobre las 7 clases de Vigía EPP (persona, chaleco, sin_chaleco, lentes, sin_lentes, guantes, sin_guantes).

Reanudable automáticamente si se interrumpe. Copia best.pt a modelos/epp.pt y guarda las
métricas de validación en modelos/epp.json.

    python -m entrenamiento.descargar_kaggle
    python -m entrenamiento.preparar_epp
    python -m entrenamiento.entrenar_yolo
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from entrenamiento.comun import entrenar, validar


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--datos", default="datasets/epp/data.yaml")
    ap.add_argument("--nombre", default="epp_yolo11")
    ap.add_argument("--epocas", type=int, default=20)
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
        close_mosaic=5,
        workers=4,
    )
    m = validar(args.modelo, args.datos, args.imgsz, args.lote)
    print(f"\nmAP50 en validación: {m['mAP50']:.3f} · mAP50-95: {m['mAP50-95']:.3f}")
    for clase, ap50 in m["por_clase"].items():
        print(f"  {clase}: {ap50:.3f}")
    print(f"modelo exportado: {args.modelo}")
    Path(args.modelo).with_suffix(".json").write_text(
        json.dumps(m, indent=2, ensure_ascii=False), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
