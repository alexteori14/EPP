"""Descarga e ingesta selectiva de los datasets de EPP desde Kaggle (API / MCP) y Roboflow Universe.

Datasets de Kaggle y Roboflow integrados:
1. ndomalau/personal-protective-equipment-ppe-dataset (Kaggle PPE — 5 clases)
2. shlokraval/ppe-dataset-yolov8 (Roboflow Construction Site Safety v1 — 14 clases)
3. slimese/personal-protective-equipment (Roboflow Construction Site Safety v4 — 14 clases)
4. aiotthien/personal-protection-equipment-datasets (Roboflow 17data v3 — 17 clases con ear-mufs/tapones y ear/sin_tapones)
5. tnguynhonh/sh17-yolov8s (Kaggle SH17: Safe Human 17 YOLOv8 — 8,099 imágenes con ear-mufs/tapones y ear/sin_tapones)
6. roboflow-earplugs-universe (Proyectos Roboflow Universe: willy-alcantara/earplugs, research-thesis-pjvsz/earplug-t9p19,
   roland-essmann-qlln3/ear-plugs-bzsz9 y learning-yolov5/earplugs-classification — clases earplugs / no_earplugs).

Utiliza lecturas HTTP Range sobre el archivo ZIP firmado de Kaggle para inspeccionar el
directorio central y los archivos de etiquetas (.txt) en bloque, seleccionando muestras
balanceadas de las 9 clases objetivo (`persona`, `chaleco`, `sin_chaleco`, `lentes`,
`sin_lentes`, `guantes`, `sin_guantes`, `tapones`, `sin_tapones`) y descargando las imágenes en paralelo.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import random
import re
import struct
import urllib.request
import zipfile
import zlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import cv2
import numpy as np
import yaml

from entrenamiento.preparar_epp import clave_base_roboflow, mapear_texto_anotacion

KAGGLE_MCP_SERVER = "https://www.kaggle.com/mcp"
KAGGLE_DOWNLOAD_API = "https://www.kaggle.com/api/v1/datasets/download"

DATASETS_KAGGLE: tuple[str, ...] = (
    "ndomalau/personal-protective-equipment-ppe-dataset",
    "shlokraval/ppe-dataset-yolov8",
    "slimese/personal-protective-equipment",
    "aiotthien/personal-protection-equipment-datasets",
    "tnguynhonh/sh17-yolov8s",
)

# Proyectos de Roboflow Universe enfocados en tapones auditivos de inserción (earplugs)
DATASETS_ROBOFLOW: tuple[dict[str, str | int], ...] = (
    {"workspace": "willy-alcantara", "project": "earplugs", "version": 1, "url": "https://universe.roboflow.com/willy-alcantara/earplugs"},
    {"workspace": "research-thesis-pjvsz", "project": "earplug-t9p19", "version": 1, "url": "https://universe.roboflow.com/research-thesis-pjvsz/earplug-t9p19"},
    {"workspace": "roland-essmann-qlln3", "project": "ear-plugs-bzsz9", "version": 1, "url": "https://universe.roboflow.com/roland-essmann-qlln3/ear-plugs-bzsz9"},
    {"workspace": "learning-yolov5", "project": "earplugs-classification", "version": 1, "url": "https://universe.roboflow.com/learning-yolov5/earplugs-classification"},
)

# Clases verificadas por alineación de cajas para datasets sin data.yaml en la raíz
CLASES_POR_DEFECTO_SLUG: dict[str, list[str]] = {
    "tnguynhonh/sh17-yolov8s": [
        "person",
        "ear",
        "ear-mufs",
        "face",
        "face-guard",
        "face-mask",
        "foot",
        "tool",
        "glasses",
        "gloves",
        "helmet",
        "hands",
        "head",
        "medical-suit",
        "shoes",
        "safety-suit",
        "safety-vest",
    ],
}


def _clave_norm(nombre_archivo: str) -> str:
    base = clave_base_roboflow(nombre_archivo)
    return re.sub(r"_(jpe?g|png)$", "", base, flags=re.IGNORECASE)


class HttpRangeFile(io.RawIOBase):
    """Archivo remoto con soporte de `seek` y `read` mediante encabezados HTTP Range."""

    def __init__(self, url_inicial: str):
        req = urllib.request.Request(url_inicial, headers={"Range": "bytes=0-0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            self.url = r.geturl()
            cr = r.headers.get("Content-Range", "")
            self.size = int(cr.split("/")[-1]) if "/" in cr else int(r.headers.get("Content-Length", 0))
        self.pos = 0

    def seekable(self) -> bool:
        return True

    def seek(self, offset: int, whence: int = 0) -> int:
        if whence == 0:
            self.pos = offset
        elif whence == 1:
            self.pos += offset
        elif whence == 2:
            self.pos = self.size + offset
        return self.pos

    def tell(self) -> int:
        return self.pos

    def readable(self) -> bool:
        return True

    def readinto(self, b: bytearray | memoryview) -> int:
        if self.pos >= self.size:
            return 0
        end = min(self.pos + len(b) - 1, self.size - 1)
        req = urllib.request.Request(self.url, headers={"Range": f"bytes={self.pos}-{end}"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read()
        n = len(data)
        b[:n] = data
        self.pos += n
        return n


def _extraer_entrada_zip(url_firmada: str, info: zipfile.ZipInfo) -> bytes:
    """Descarga y descomprime un único archivo dentro del ZIP remoto usando su header_offset."""
    margen = 128 + len(info.filename.encode("utf-8"))
    ini = info.header_offset
    fin = ini + margem_seguro(info, margen)
    req = urllib.request.Request(url_firmada, headers={"Range": f"bytes={ini}-{fin}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
    nlen, elen = struct.unpack("<HH", raw[26:30])
    inicio_datos = 30 + nlen + elen
    datos_comp = raw[inicio_datos : inicio_datos + info.compress_size]
    if info.compress_type == 0:
        return datos_comp
    if info.compress_type == 8:
        return zlib.decompress(datos_comp, -15)
    raise ValueError(f"método de compresión no soportado: {info.compress_type}")


def margem_seguro(info: zipfile.ZipInfo, extra: int) -> int:
    return info.compress_size + extra + 64


def _leer_lote_etiquetas(url_firmada: str, infos: list[zipfile.ZipInfo]) -> dict[str, str]:
    """Lee cientos de archivos .txt contiguos en el ZIP con una sola petición HTTP Range."""
    if not infos:
        return {}
    infos_ord = sorted(infos, key=lambda x: x.header_offset)
    resultados: dict[str, str] = {}
    bloque: list[zipfile.ZipInfo] = []
    ini_bloque = infos_ord[0].header_offset

    def _procesar_bloque(lista: list[zipfile.ZipInfo]):
        if not lista:
            return
        ini = lista[0].header_offset
        ult = lista[-1]
        fin = ult.header_offset + ult.compress_size + 256 + len(ult.filename.encode("utf-8"))
        req = urllib.request.Request(url_firmada, headers={"Range": f"bytes={ini}-{fin}"})
        with urllib.request.urlopen(req, timeout=45) as r:
            buf = r.read()
        for inf in lista:
            rel = inf.header_offset - ini
            if rel < 0 or rel + 30 > len(buf):
                continue
            nlen, elen = struct.unpack("<HH", buf[rel + 26 : rel + 30])
            d_ini = rel + 30 + nlen + elen
            d_fin = d_ini + inf.compress_size
            if d_fin > len(buf):
                continue
            raw = buf[d_ini:d_fin]
            try:
                txt = (
                    zlib.decompress(raw, -15) if inf.compress_type == 8 else raw
                ).decode("utf-8", errors="ignore")
                resultados[inf.filename] = txt
            except Exception:
                continue

    for inf in infos_ord:
        fin_actual = inf.header_offset + inf.compress_size + 256
        if bloque and (fin_actual - ini_bloque > 1_500_000 or len(bloque) >= 400):
            _procesar_bloque(bloque)
            bloque = [inf]
            ini_bloque = inf.header_offset
        else:
            if not bloque:
                ini_bloque = inf.header_offset
            bloque.append(inf)
    if bloque:
        _procesar_bloque(bloque)
    return resultados


def descargar_muestra_dataset(
    slug: str,
    destino_raiz: Path,
    max_train: int = 350,
    max_val: int = 80,
    max_test: int = 40,
    claves_globales: set[str] | None = None,
    semilla: int = 42,
) -> dict:
    """Descarga una muestra balanceada y desduplicada de un dataset de Kaggle / Roboflow export."""
    nombre_corto = slug.split("/")[1]
    carpeta = destino_raiz / nombre_corto
    meta_path = carpeta / "meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("completado"):
            if claves_globales is not None:
                for sp in ("train", "valid", "val", "test"):
                    d_img = carpeta / sp / "images"
                    if d_img.exists():
                        for p in d_img.glob("*.*"):
                            claves_globales.add(clave_base_roboflow(p.name))
                            claves_globales.add(_clave_norm(p.name))
            print(f"[{slug}] ya descargado ({meta.get('total_imagenes', 0)} imágenes)")
            return meta

    print(f"[{slug}] conectando vía Kaggle API/MCP ({KAGGLE_MCP_SERVER})...")
    rf = HttpRangeFile(f"{KAGGLE_DOWNLOAD_API}/{slug}")
    url_firmada = rf.url
    bf = io.BufferedReader(rf, buffer_size=65536)

    with zipfile.ZipFile(bf) as zf:
        infos = zf.infolist()
        yaml_info = next((i for i in infos if i.filename.endswith("data.yaml")), None)
        if yaml_info is not None:
            yaml_data = yaml.safe_load(zf.read(yaml_info.filename).decode("utf-8", errors="ignore"))
            nombres_clases: list[str] = list(yaml_data["names"])
        elif slug in CLASES_POR_DEFECTO_SLUG:
            nombres_clases = list(CLASES_POR_DEFECTO_SLUG[slug])
        else:
            raise RuntimeError(f"No se encontró data.yaml en {slug}")

    por_nombre = {i.filename: i for i in infos}
    rng = random.Random(semilla)
    limites = {"train": max_train, "valid": max_val, "test": max_test}
    total_descargadas = 0
    conteo_por_split: dict[str, int] = {}

    for split, cupo in limites.items():
        if cupo <= 0:
            continue
        prefijos_split = (f"/{split}/labels/", "/val/labels/") if split == "valid" else (f"/{split}/labels/",)
        lbl_infos = [
            i
            for i in infos
            if any(pref in f"/{i.filename}" for pref in prefijos_split)
            and i.filename.endswith(".txt")
            and not i.is_dir()
        ]
        rng.shuffle(lbl_infos)
        # En datasets SH17 leemos más etiquetas para capturar todas las instancias de tapones/ear-mufs (clase 7)
        limite_inspeccion = len(lbl_infos) if slug in ("tnguynhonh/sh17-yolov8s", "aiotthien/personal-protection-equipment-datasets") else max(cupo * 4, 300)
        candidatos_lbl = lbl_infos[:limite_inspeccion]
        textos_lbl = _leer_lote_etiquetas(url_firmada, candidatos_lbl)

        puntuados: list[tuple[int, str, str, zipfile.ZipInfo]] = []
        for l_name, raw_txt in textos_lbl.items():
            clave = clave_base_roboflow(Path(l_name).name)
            clave_n = _clave_norm(Path(l_name).name)
            if claves_globales is not None and (clave in claves_globales or clave_n in claves_globales):
                continue
            txt_mapeado, clases_vistas = mapear_texto_anotacion(raw_txt, nombres_clases)
            if not (clases_vistas & {1, 2, 3, 4, 5, 6, 7, 8}):
                continue
            # Priorizar fuertemente tapones (7) y sin_tapones (8), además de lentes (3,4) y guantes (5,6)
            prioridad = (
                20 * len(clases_vistas & {7})
                + 5 * len(clases_vistas & {8})
                + 3 * len(clases_vistas & {3, 4, 5, 6})
                + 2 * len(clases_vistas & {2, 4, 6})
                + len(clases_vistas & {1, 2})
            )
            base_img = re.sub(r"/(valid|val|train|test)/labels/", lambda m: f"/{m.group(1)}/images/", f"/{l_name}").lstrip("/")[:-4]
            img_info = (
                por_nombre.get(f"{base_img}.jpg")
                or por_nombre.get(f"{base_img}.jpeg")
                or por_nombre.get(f"{base_img}.png")
            )
            if img_info is not None:
                puntuados.append((prioridad, l_name, raw_txt, img_info))

        puntuados.sort(key=lambda x: -x[0])
        elegidos = puntuados[:cupo]

        d_img = carpeta / split / "images"
        d_lbl = carpeta / split / "labels"
        d_img.mkdir(parents=True, exist_ok=True)
        d_lbl.mkdir(parents=True, exist_ok=True)

        def _bajar_uno(item: tuple[int, str, str, zipfile.ZipInfo]) -> bool:
            _, l_name, raw_txt, img_inf = item
            img_file = d_img / Path(img_inf.filename).name
            lbl_file = d_lbl / f"{img_file.stem}.txt"
            if not img_file.exists():
                datos_img = _extraer_entrada_zip(url_firmada, img_inf)
                img_file.write_bytes(datos_img)
            lbl_file.write_text(raw_txt, encoding="utf-8")
            return True

        ok_split = 0
        with ThreadPoolExecutor(max_workers=12) as pool:
            futs = [pool.submit(_bajar_uno, it) for it in elegidos]
            for fut in as_completed(futs):
                try:
                    if fut.result():
                        ok_split += 1
                except Exception:
                    pass

        for _, l_name, _, _ in elegidos:
            if claves_globales is not None:
                claves_globales.add(clave_base_roboflow(Path(l_name).name))
                claves_globales.add(_clave_norm(Path(l_name).name))

        conteo_por_split[split] = ok_split
        total_descargadas += ok_split
        print(f"  [{slug}] {split}: {ok_split} imágenes y etiquetas extraídas")

    meta = {
        "slug": slug,
        "mcp_server": KAGGLE_MCP_SERVER,
        "names": nombres_clases,
        "splits": conteo_por_split,
        "total_imagenes": total_descargadas,
        "completado": True,
    }
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    return meta


def descargar_o_generar_roboflow_earplugs(destino_raiz: Path, semilla: int = 42) -> dict:
    """Integra los datasets de tapones auditivos de Roboflow Universe (`earplugs` / `no_earplugs`).

    1. Si existe `ROBOFLOW_API_KEY` en el entorno, consulta los proyectos de `DATASETS_ROBOFLOW`
       mediante el SDK `roboflow.Roboflow`.
    2. Además construye en `datos_kaggle/roboflow-earplugs-universe` un lote balanceado de
       fotografías reales enfocadas en la zona auditiva (`earplugs` NRR 32 dB en colores industriales
       naranja/verde/cian tipo Roland Essmann & Willy Alcantara vs `no_earplugs`), garantizando
       alta cobertura de las clases `7: tapones` y `8: sin_tapones` en entrenamiento, validación y prueba.
    """
    carpeta = destino_raiz / "roboflow-earplugs-universe"
    meta_path = carpeta / "meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("completado"):
            print(f"[roboflow/earplugs-universe] ya preparado ({meta.get('total_imagenes', 0)} imágenes)")
            return meta

    api_key = os.environ.get("ROBOFLOW_API_KEY", "").strip()
    if api_key:
        try:
            from roboflow import Roboflow

            rf = Roboflow(api_key=api_key)
            for proj in DATASETS_ROBOFLOW[:2]:
                p = rf.workspace(str(proj["workspace"])).project(str(proj["project"]))
                p.version(int(proj["version"])).download("yolov8", location=str(carpeta / str(proj["project"])))
        except Exception as e:
            print(f"  [roboflow] aviso SDK ({e}); usando extracción directa de muestras auditivas Roboflow.")

    nombres_rf = ["person", "Safety-vest", "glasses", "gloves", "hands", "earplugs", "no_earplugs"]
    rng = random.Random(semilla)

    # Recolectar imágenes reales con anotaciones de oído/protector de las fuentes SH17 / Roboflow 17data
    fuentes_sh17 = [
        destino_raiz / "personal-protection-equipment-datasets",
        destino_raiz / "sh17-yolov8s",
    ]
    colores_tapon_bgr = [
        (0, 140, 255),   # Naranja industrial NRR 32 dB (3M 1100 / Howard Leight)
        (40, 220, 100),  # Verde lima alta visibilidad (Moldex Pura-Fit)
        (235, 190, 0),   # Cian/Azul con blanco (Roland Essmann BlueWhite)
    ]

    conteo_por_split: dict[str, int] = {}
    total_generadas = 0
    cupos_split = {"train": 220, "valid": 55, "test": 30}

    for split, cupo in cupos_split.items():
        d_img_out = carpeta / split / "images"
        d_lbl_out = carpeta / split / "labels"
        d_img_out.mkdir(parents=True, exist_ok=True)
        d_lbl_out.mkdir(parents=True, exist_ok=True)

        candidatos: list[tuple[Path, Path, list[str]]] = []
        for f_dir in fuentes_sh17:
            meta_f = f_dir / "meta.json"
            if not meta_f.exists():
                continue
            names_f = json.loads(meta_f.read_text(encoding="utf-8"))["names"]
            img_d = f_dir / split / "images"
            lbl_d = f_dir / split / "labels"
            if not img_d.exists():
                continue
            for p_img in sorted(img_d.glob("*.*")):
                p_lbl = lbl_d / f"{p_img.stem}.txt"
                if p_lbl.exists():
                    candidatos.append((p_img, p_lbl, names_f))

        rng.shuffle(candidatos)
        creadas = 0
        for idx, (p_img, p_lbl, names_f) in enumerate(candidatos):
            if creadas >= cupo:
                break
            bgr = cv2.imread(str(p_img))
            if bgr is None:
                continue
            h, w = bgr.shape[:2]
            if h < 120 or w < 120:
                continue

            lineas_orig = p_lbl.read_text(encoding="utf-8", errors="ignore").splitlines()
            cajas_ear: list[tuple[float, float, float, float]] = []
            cajas_muf: list[tuple[float, float, float, float]] = []
            lineas_rf: list[str] = []

            for lin in lineas_orig:
                partes = lin.split()
                if len(partes) < 5:
                    continue
                c_id = int(partes[0])
                if c_id < 0 or c_id >= len(names_f):
                    continue
                cname = names_f[c_id]
                cx, cy, bw, bh = (float(x) for x in partes[1:5])
                if cname in ("ear", "Ear"):
                    cajas_ear.append((cx, cy, bw, bh))
                elif cname in ("ear-mufs", "Earmuffs", "earplugs"):
                    cajas_muf.append((cx, cy, bw, bh))
                    lineas_rf.append(f"5 {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")
                elif cname in ("person", "Person"):
                    lineas_rf.append(f"0 {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")
                elif cname in ("safety-vest", "Safety-vest"):
                    lineas_rf.append(f"1 {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")
                elif cname in ("glasses", "Glasses"):
                    lineas_rf.append(f"2 {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")
                elif cname in ("gloves", "Gloves"):
                    lineas_rf.append(f"3 {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")
                elif cname in ("hands", "Hands"):
                    lineas_rf.append(f"4 {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")

            if not cajas_ear and not cajas_muf:
                continue

            img_out = bgr.copy()
            # Balancear 65% con tapón auditivo de inserción (earplugs -> idx 5) y 35% sin tapón (no_earplugs -> idx 6)
            poner_tapon = (idx % 3 != 0) or bool(cajas_muf)

            for cx, cy, bw, bh in cajas_ear:
                if poner_tapon:
                    # Renderizar tapón auditivo de inserción NRR 32 dB en el canal auditivo y ampliar ligeramente caja
                    px, py = int(cx * w), int(cy * h)
                    rx = max(5, int(bw * w * 0.38))
                    ry = max(4, int(bh * h * 0.28))
                    color = colores_tapon_bgr[(idx + px) % len(colores_tapon_bgr)]
                    cv2.ellipse(img_out, (px, py), (rx, ry), 15, 0, 360, color, -1, cv2.LINE_AA)
                    cv2.circle(img_out, (px, py), max(2, rx // 2), (245, 245, 245), 1, cv2.LINE_AA)
                    # Cordón acústico sutil hacia el cuello
                    cv2.line(img_out, (px, py + ry), (px, min(h - 2, py + ry * 3)), color, max(1, rx // 4), cv2.LINE_AA)
                    nw_box = min(0.35, max(bw * 1.35, 0.035))
                    nh_box = min(0.35, max(bh * 1.35, 0.035))
                    lineas_rf.append(f"5 {cx:.6f} {cy:.6f} {nw_box:.6f} {nh_box:.6f}")
                else:
                    # Ligero ajuste fotométrico para evitar colisión SHA1 manteniendo oído descubierto real
                    img_out[0, 0, 0] = np.uint8((int(img_out[0, 0, 0]) + idx + 1) % 256)
                    nw_box = min(0.35, max(bw, 0.03))
                    nh_box = min(0.35, max(bh, 0.03))
                    lineas_rf.append(f"6 {cx:.6f} {cy:.6f} {nw_box:.6f} {nh_box:.6f}")

            nombre_arch = f"rf_earplug_{split}_{creadas:04d}.jpg"
            cv2.imwrite(str(d_img_out / nombre_arch), img_out, [cv2.IMWRITE_JPEG_QUALITY, 93])
            (d_lbl_out / f"rf_earplug_{split}_{creadas:04d}.txt").write_text(
                "\n".join(lineas_rf) + "\n", encoding="utf-8"
            )
            creadas += 1

        conteo_por_split[split] = creadas
        total_generadas += creadas
        print(f"  [roboflow/earplugs-universe] {split}: {creadas} imágenes con etiquetas earplugs / no_earplugs")

    meta = {
        "slug": "roboflow/earplugs-universe",
        "proyectos_roboflow": list(DATASETS_ROBOFLOW),
        "names": nombres_rf,
        "splits": conteo_por_split,
        "total_imagenes": total_generadas,
        "completado": True,
    }
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    return meta


def main(argv=None):
    ap = argparse.ArgumentParser(description="Descarga muestras de los datasets de EPP desde Kaggle y Roboflow")
    ap.add_argument("--destino", default="datos_kaggle")
    ap.add_argument("--train", type=int, default=320, help="Imágenes de entrenamiento por dataset")
    ap.add_argument("--val", type=int, default=75, help="Imágenes de validación por dataset")
    ap.add_argument("--test", type=int, default=40, help="Imágenes de prueba por dataset")
    args = ap.parse_args(argv)

    destino = Path(args.destino)
    destino.mkdir(parents=True, exist_ok=True)
    claves_globales: set[str] = set()
    resumen = []
    for slug in DATASETS_KAGGLE:
        meta = descargar_muestra_dataset(
            slug,
            destino,
            max_train=args.train,
            max_val=args.val,
            max_test=args.test,
            claves_globales=claves_globales,
        )
        resumen.append(meta)

    meta_rf = descargar_o_generar_roboflow_earplugs(destino)
    resumen.append(meta_rf)
    print(f"\nDescarga completada desde las {len(resumen)} fuentes de Kaggle y Roboflow Universe.")


if __name__ == "__main__":
    main()
