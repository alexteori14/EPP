"""Descarga e ingesta selectiva de los 3 datasets de EPP desde Kaggle (API / MCP).

Datasets integrados:
1. ndomalau/personal-protective-equipment-ppe-dataset
2. shlokraval/ppe-dataset-yolov8
3. slimese/personal-protective-equipment

Utiliza lecturas HTTP Range sobre el archivo ZIP firmado de Kaggle para inspeccionar el
directorio central y los archivos de etiquetas (.txt) en bloque, seleccionando muestras
balanceadas de las 7 clases objetivo (`persona`, `chaleco`, `sin_chaleco`, `lentes`,
`sin_lentes`, `guantes`, `sin_guantes`) y descargando las imágenes en paralelo.
"""
from __future__ import annotations

import argparse
import io
import json
import random
import struct
import urllib.request
import zipfile
import zlib
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yaml

from entrenamiento.preparar_epp import clave_base_roboflow, mapear_texto_anotacion

KAGGLE_MCP_SERVER = "https://www.kaggle.com/mcp"
KAGGLE_DOWNLOAD_API = "https://www.kaggle.com/api/v1/datasets/download"

DATASETS_KAGGLE: tuple[str, ...] = (
    "ndomalau/personal-protective-equipment-ppe-dataset",
    "shlokraval/ppe-dataset-yolov8",
    "slimese/personal-protective-equipment",
)


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
    # Agrupar en bloques de hasta 1.5 MB para hacer pocas peticiones HTTP
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
    """Descarga una muestra balanceada y desduplicada de un dataset de Kaggle."""
    nombre_corto = slug.split("/")[1]
    carpeta = destino_raiz / nombre_corto
    meta_path = carpeta / "meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("completado"):
            print(f"[{slug}] ya descargado ({meta.get('total_imagenes', 0)} imágenes)")
            return meta

    print(f"[{slug}] conectando vía Kaggle API/MCP ({KAGGLE_MCP_SERVER})...")
    rf = HttpRangeFile(f"{KAGGLE_DOWNLOAD_API}/{slug}")
    url_firmada = rf.url
    bf = io.BufferedReader(rf, buffer_size=65536)

    with zipfile.ZipFile(bf) as zf:
        infos = zf.infolist()
        yaml_info = next((i for i in infos if i.filename.endswith("data.yaml")), None)
        if yaml_info is None:
            raise RuntimeError(f"No se encontró data.yaml en {slug}")
        yaml_data = yaml.safe_load(zf.read(yaml_info.filename).decode("utf-8", errors="ignore"))
        nombres_clases: list[str] = list(yaml_data["names"])

    por_nombre = {i.filename: i for i in infos}
    rng = random.Random(semilla)
    limites = {"train": max_train, "valid": max_val, "test": max_test}
    total_descargadas = 0
    conteo_por_split: dict[str, int] = {}

    for split, cupo in limites.items():
        if cupo <= 0:
            continue
        lbl_infos = [
            i
            for i in infos
            if f"/{split}/labels/" in f"/{i.filename}" and i.filename.endswith(".txt") and not i.is_dir()
        ]
        rng.shuffle(lbl_infos)
        # Inspeccionar hasta 4x el cupo para priorizar clases raras (lentes, sin_lentes, guantes, sin_guantes)
        candidatos_lbl = lbl_infos[: max(cupo * 4, 300)]
        textos_lbl = _leer_lote_etiquetas(url_firmada, candidatos_lbl)

        puntuados: list[tuple[int, str, str, zipfile.ZipInfo]] = []
        for l_name, raw_txt in textos_lbl.items():
            clave = clave_base_roboflow(Path(l_name).name)
            if claves_globales is not None and clave in claves_globales:
                continue
            txt_mapeado, clases_vistas = mapear_texto_anotacion(raw_txt, nombres_clases)
            if not (clases_vistas & {1, 2, 3, 4, 5, 6}):
                continue
            # Priorizar imágenes que contengan lentes (3,4) y guantes (5,6) además de chaleco (1,2)
            prioridad = (
                3 * len(clases_vistas & {3, 4, 5, 6})
                + 2 * len(clases_vistas & {2, 4, 6})
                + len(clases_vistas & {1, 2})
            )
            base_img = l_name.replace(f"{split}/labels/", f"{split}/images/")[:-4]
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
            lbl_file = d_lbl / Path(l_name).name
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


def main(argv=None):
    ap = argparse.ArgumentParser(description="Descarga muestras de los 3 datasets de EPP desde Kaggle")
    ap.add_argument("--destino", default="datos_kaggle")
    ap.add_argument("--train", type=int, default=300, help="Imágenes de entrenamiento por dataset")
    ap.add_argument("--val", type=int, default=75, help="Imágenes de validación por dataset")
    ap.add_argument("--test", type=int, default=35, help="Imágenes de prueba por dataset")
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
    print(f"\nDescarga completada desde los {len(resumen)} datasets de Kaggle.")


if __name__ == "__main__":
    main()
