"""Armoniza los datasets de Kaggle y Roboflow al esquema de 9 clases de Vigía EPP (sin casco ni mascarilla).

Clases destino (motor.contrato.CLASES):
  0: persona
  1: chaleco
  2: sin_chaleco
  3: lentes
  4: sin_lentes
  5: guantes
  6: sin_guantes
  7: tapones
  8: sin_tapones

Se descartan explícitamente: helmet, no_helmet, Hardhat, NO-Hardhat, Mask, NO-Mask,
face-mask, Face-mask-medical, Fall-Detected, Ladder, Safety Cone, head, face, foot, shoes, tool.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import shutil
from collections import Counter
from pathlib import Path

import yaml

from motor import contrato

# Mapeo de nombres de clase en los datasets de Kaggle y Roboflow -> índice canónico (0..8)
MAPEO_NOMBRES: dict[str, int] = {
    # 0: persona
    "person": 0,
    "Person": 0,
    "worker": 0,
    "Worker": 0,
    # 1: chaleco
    "vest": 1,
    "Safety Vest": 1,
    "Safety-vest": 1,
    "safety_vest": 1,
    "safety-vest": 1,
    # 2: sin_chaleco
    "no_vest": 2,
    "NO-Safety Vest": 2,
    "no-safety-vest": 2,
    "no_safety_vest": 2,
    # 3: lentes
    "goggles": 3,
    "Goggles": 3,
    "glasses": 3,
    "Glasses": 3,
    "safety_glasses": 3,
    "Safety Glasses": 3,
    "safety-glasses": 3,
    # 4: sin_lentes
    "no_goggles": 4,
    "NO-Goggles": 4,
    "no-goggles": 4,
    "no_glasses": 4,
    "NO-Glasses": 4,
    # 5: guantes
    "gloves": 5,
    "Gloves": 5,
    "glove": 5,
    # 6: sin_guantes
    "no_gloves": 6,
    "NO-Gloves": 6,
    "no-gloves": 6,
    "Hands": 6,
    "hands": 6,
    # 7: tapones (protectores auditivos de inserción / auditivos en Kaggle SH17 y Roboflow)
    "earplugs": 7,
    "Earplugs": 7,
    "earplug": 7,
    "Earplug": 7,
    "ear-plugs": 7,
    "ear_plugs": 7,
    "ear-plug": 7,
    "ear_protection": 7,
    "Ear-Protection": 7,
    "Ear Protection": 7,
    "ear-protection": 7,
    "earmuffs": 7,
    "Earmuffs": 7,
    "Ear-mufs": 7,
    "ear-mufs": 7,
    "hearing_protection": 7,
    "BlueWhite": 7,
    "GreenWhite": 7,
    "OrangeWhite": 7,
    "tapones": 7,
    "tapones_auditivos": 7,
    # 8: sin_tapones (oído descubierto sin tapón/protector auditivo)
    "no_earplugs": 8,
    "NO-Earplugs": 8,
    "no-earplugs": 8,
    "no_earplug": 8,
    "no_ear_protection": 8,
    "NO-Ear-Protection": 8,
    "NO-Ear Protection": 8,
    "no-ear-protection": 8,
    "no_earmuffs": 8,
    "NO-Earmuffs": 8,
    "without_earplugs": 8,
    "Ear": 8,
    "ear": 8,
    "sin_tapones": 8,
}


def clave_base_roboflow(nombre_archivo: str) -> str:
    """Extrae el nombre base antes de `.rf.<hash>` para evitar fuga de datos entre v1 y v4."""
    nombre = Path(nombre_archivo).name
    if ".rf." in nombre:
        return nombre.split(".rf.", 1)[0]
    return Path(nombre).stem


def _clave_normalizada(nombre_archivo: str) -> str:
    """Normaliza sufijos `_jpeg`/`_jpg`/`_png` para deduplicar entre exportaciones Roboflow y SH17."""
    base = clave_base_roboflow(nombre_archivo)
    return re.sub(r"_(jpe?g|png)$", "", base, flags=re.IGNORECASE)


def mapear_etiqueta_linea(linea: str, nombres_origen: list[str]) -> str | None:
    """Convierte una línea YOLO al índice canónico 0..8, o devuelve None si es casco/mascarilla."""
    partes = linea.strip().split()
    if len(partes) < 5:
        return None
    try:
        idx_origen = int(partes[0])
    except ValueError:
        return None
    if idx_origen < 0 or idx_origen >= len(nombres_origen):
        return None
    nombre_clase = nombres_origen[idx_origen].strip()
    idx_destino = MAPEO_NOMBRES.get(nombre_clase)
    if idx_destino is None:
        return None
    coords = " ".join(partes[1:5])
    return f"{idx_destino} {coords}"


def mapear_texto_anotacion(texto: str, nombres_origen: list[str]) -> tuple[str, set[int]]:
    """Convierte un archivo .txt completo de etiquetas YOLO y devuelve (texto_nuevo, clases_vistas)."""
    lineas_nuevas: list[str] = []
    clases: set[int] = set()
    for renglon in texto.splitlines():
        m = mapear_etiqueta_linea(renglon, nombres_origen)
        if m is not None:
            lineas_nuevas.append(m)
            clases.add(int(m.split()[0]))
    return "\n".join(lineas_nuevas) + ("\n" if lineas_nuevas else ""), clases


def _sha1_archivo(ruta: Path) -> str:
    h = hashlib.sha1()
    with open(ruta, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def preparar_dataset(
    dir_kaggle: str | Path = "datos_kaggle",
    dir_salida: str | Path = "datasets/epp",
    semilla: int = 42,
) -> dict:
    """Unifica las muestras descargadas de Kaggle y Roboflow en datasets/epp/ (9 clases)."""
    d_in = Path(dir_kaggle)
    d_out = Path(dir_salida)
    if d_out.exists():
        shutil.rmtree(d_out)
    for split in ("train", "val", "test"):
        (d_out / split / "images").mkdir(parents=True, exist_ok=True)
        (d_out / split / "labels").mkdir(parents=True, exist_ok=True)

    claves_vistas: set[str] = set()
    hashes_vistos: set[str] = set()
    conteo_clases: Counter[str] = Counter()
    conteo_splits: Counter[str] = Counter()
    conteo_fuentes: Counter[str] = Counter()

    fuentes = sorted(p for p in d_in.iterdir() if p.is_dir()) if d_in.exists() else []
    rng = random.Random(semilla)

    for fuente_dir in fuentes:
        meta_file = fuente_dir / "meta.json"
        if not meta_file.exists():
            continue
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        nombres_origen: list[str] = meta["names"]
        slug: str = meta.get("slug", fuente_dir.name)

        for split_origen in ("train", "valid", "val", "test"):
            split_destino = "val" if split_origen in ("valid", "val") else split_origen
            img_dir = fuente_dir / split_origen / "images"
            lbl_dir = fuente_dir / split_origen / "labels"
            if not img_dir.exists() or not lbl_dir.exists():
                continue

            imagenes = sorted(img_dir.glob("*.*"))
            rng.shuffle(imagenes)
            for img_path in imagenes:
                lbl_path = lbl_dir / f"{img_path.stem}.txt"
                if not lbl_path.exists():
                    continue
                clave = clave_base_roboflow(img_path.name)
                clave_norm = _clave_normalizada(img_path.name)
                sha = _sha1_archivo(img_path)
                if clave in claves_vistas or clave_norm in claves_vistas or sha in hashes_vistos:
                    continue

                texto_nuevo, clases = mapear_texto_anotacion(
                    lbl_path.read_text(encoding="utf-8", errors="ignore"),
                    nombres_origen,
                )
                # Conservar solo imágenes que tengan al menos una clase de EPP (1..8)
                if not (clases & {1, 2, 3, 4, 5, 6, 7, 8}):
                    continue

                claves_vistas.add(clave)
                claves_vistas.add(clave_norm)
                hashes_vistos.add(sha)

                prefijo = re.sub(r"[^a-z0-9]+", "_", slug.lower()).strip("_")[:12]
                nombre_limpio = f"{prefijo}_{sha[:10]}{img_path.suffix.lower()}"
                shutil.copy2(img_path, d_out / split_destino / "images" / nombre_limpio)
                (d_out / split_destino / "labels" / f"{Path(nombre_limpio).stem}.txt").write_text(
                    texto_nuevo, encoding="utf-8"
                )

                conteo_splits[split_destino] += 1
                conteo_fuentes[slug] += 1
                for linea in texto_nuevo.splitlines():
                    c_idx = int(linea.split()[0])
                    conteo_clases[contrato.CLASES[c_idx]] += 1

    data_yaml = {
        "path": str(d_out.resolve()),
        "train": "train/images",
        "val": "val/images",
        "test": "test/images",
        "nc": len(contrato.CLASES),
        "names": list(contrato.CLASES),
    }
    (d_out / "data.yaml").write_text(
        yaml.safe_dump(data_yaml, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    resumen = {
        "clases": list(contrato.CLASES),
        "splits": dict(conteo_splits),
        "fuentes": dict(conteo_fuentes),
        "instancias_por_clase": dict(conteo_clases),
    }
    (d_out / "resumen_dataset.json").write_text(
        json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return resumen


def main(argv=None):
    ap = argparse.ArgumentParser(description="Armoniza los datasets de Kaggle y Roboflow a las 9 clases de EPP")
    ap.add_argument("--entrada", default="datos_kaggle")
    ap.add_argument("--salida", default="datasets/epp")
    args = ap.parse_args(argv)
    res = preparar_dataset(args.entrada, args.salida)
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
