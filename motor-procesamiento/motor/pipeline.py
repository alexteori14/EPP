"""Pipeline principal del motor de visión: video de inicio de turno -> salida/observaciones.json.

    python -m motor.pipeline --video video/recorrido_turno.mp4 \
        --turnos datos/sistema/turnos.csv --salida salida/
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import shutil
import sys
import time
from collections import defaultdict
from pathlib import Path

import cv2

from motor import anotar, asociar, contrato, cuadros, detector as mod_det, rastreo

log = logging.getLogger("motor")
MODELO_DEFECTO = "modelos/epp.pt"


class Tiempos:
    def __init__(self):
        self.t: dict[str, float] = defaultdict(float)

    def medir(self, etapa: str):
        tiempos = self

        class _M:
            def __enter__(self):
                self.t0 = time.perf_counter()

            def __exit__(self, *a):
                tiempos.t[etapa] += time.perf_counter() - self.t0

        return _M()


class Progreso:
    """Escribe {"paso", "porcentaje"} de manera atómica para GET /estado y GET /analisis/<id>."""

    def __init__(self, ruta: str | None):
        self.ruta = Path(ruta) if ruta else None
        self.ultimo = 0.0

    def __call__(self, paso: str, porcentaje: float, forzar: bool = False):
        if self.ruta is None or (not forzar and time.perf_counter() - self.ultimo < 0.4):
            return
        self.ultimo = time.perf_counter()
        tmp = self.ruta.with_name(f".{self.ruta.name}.{os.getpid()}.tmp")
        try:
            tmp.write_text(
                json.dumps({"paso": paso, "porcentaje": round(porcentaje)}, ensure_ascii=False),
                encoding="utf-8",
            )
            tmp.replace(self.ruta)
        except OSError:
            pass


def entrada_vacia(pos: str) -> dict:
    return {
        "posicion": pos,
        "persona_detectada": False,
        "confianza_persona": 0.0,
        "prendas": {
            pr: {"estado": "dudoso", "confianza": 0.0, "lecturas": 0}
            for pr in contrato.PRENDAS
        },
        "cuadro": 0,
        "recorte_persona": None,
        "recorte_zona": None,
    }


def procesar(
    video: str,
    ruta_turnos: str,
    salida: str,
    modelo: str = MODELO_DEFECTO,
    cada: int = 10,
    dispositivo: str = "auto",
    imgsz: int = 640,
    confianza: float = 0.25,
    con_video: bool = True,
    progreso: str | None = None,
) -> dict:
    t_inicio = time.perf_counter()
    avisar = Progreso(progreso)
    avisar("eligiendo cuadros", 2, forzar=True)
    tiempos = Tiempos()

    turnos = contrato.leer_turnos(ruta_turnos)
    info = cuadros.info_video(video)
    d_salida = Path(salida)
    d_recortes = d_salida / "recortes"
    if d_recortes.exists():
        shutil.rmtree(d_recortes)
    d_recortes.mkdir(parents=True, exist_ok=True)

    with tiempos.medir("cargar_modelo"):
        det_epp = mod_det.DetectorEPP(modelo, imgsz=imgsz, confianza=confianza, dispositivo=dispositivo)

    n_estaciones = max(1, len(turnos))
    cuadros_por_estacion = max(1.0, info.cuadros / n_estaciones)
    vistas_por_pos: dict[str, list[asociar.PersonaAsociada]] = defaultdict(list)
    mejor_frame_por_pos: dict[str, tuple[float, int, any, asociar.PersonaAsociada]] = {}
    anotaciones_por_cuadro: dict[int, list[tuple[asociar.PersonaAsociada, str]]] = defaultdict(list)

    elegidos = 0
    for c in cuadros.elegir_cuadros_en_hilo(video, cada=cada):
        elegidos += 1
        avisar("eligiendo cuadros", min(70.0, 70.0 * c.indice / max(1, info.cuadros)))
        with tiempos.medir("yolo_epp"):
            dets = det_epp.detectar([c.imagen])[0]
        with tiempos.medir("asociacion_anatomica"):
            personas = asociar.asociar_cuadro(dets, info.ancho, info.alto, cuadro=c.indice)

        idx_est = min(n_estaciones - 1, int(c.indice / cuadros_por_estacion))
        pos_id = turnos[idx_est].posicion
        if personas:
            principal = max(
                personas,
                key=lambda p: (p.caja[2] - p.caja[0]) * (p.caja[3] - p.caja[1]),
            )
            vistas_por_pos[pos_id].append(principal)
            anotaciones_por_cuadro[c.indice].append((principal, pos_id))
            puntaje = principal.confianza * c.nitidez
            if pos_id not in mejor_frame_por_pos or puntaje > mejor_frame_por_pos[pos_id][0]:
                mejor_frame_por_pos[pos_id] = (puntaje, c.indice, c.imagen.copy(), principal)

    avisar("evaluando epp por trabajador", 78, forzar=True)
    posiciones_salida: list[dict] = []
    diagnostico_pos: dict[str, dict] = {}

    for t in turnos:
        vistas = vistas_por_pos.get(t.posicion, [])
        if not vistas:
            diagnostico_pos[t.posicion] = {"no_cubierta": True}
            continue
        votado = rastreo.votar_trabajador(vistas)
        ent = entrada_vacia(t.posicion)
        ent["persona_detectada"] = votado["persona_detectada"]
        ent["confianza_persona"] = votado["confianza_persona"]
        ent["prendas"] = votado["prendas"]

        if t.posicion in mejor_frame_por_pos:
            _, idx_f, img_f, pers_f = mejor_frame_por_pos[t.posicion]
            # Sincronizar los estados votados en la vista representativa antes de recortar
            for pr in contrato.PRENDAS:
                ep_orig = pers_f.prendas.get(pr)
                pers_f.prendas[pr] = asociar.EstadoPrenda(
                    estado=votado["prendas"][pr]["estado"],
                    confianza=votado["prendas"][pr]["confianza"],
                    caja=ep_orig.caja if ep_orig else None,
                )
            rec_p, rec_z = anotar.recortar_persona_y_zona(img_f, pers_f)
            ruta_p = d_recortes / f"{t.posicion}.jpg"
            ruta_z = d_recortes / f"{t.posicion}_zona.jpg"
            cv2.imwrite(str(ruta_p), rec_p, [cv2.IMWRITE_JPEG_QUALITY, 90])
            cv2.imwrite(str(ruta_z), rec_z, [cv2.IMWRITE_JPEG_QUALITY, 92])
            ent["cuadro"] = int(idx_f)
            ent["recorte_persona"] = f"recortes/{ruta_p.name}"
            ent["recorte_zona"] = f"recortes/{ruta_z.name}"

        posiciones_salida.append(ent)
        diagnostico_pos[t.posicion] = {
            "vistas_evaluadas": len(vistas),
            "prendas": votado["prendas"],
        }

    if con_video:
        avisar("generando video anotado", 88, forzar=True)
        with tiempos.medir("video_anotado"):
            _escribir_video_anotado(video, d_salida / "recorrido_anotado.mp4", info, turnos, mejor_frame_por_pos)

    resultado = {
        "video": Path(video).name,
        "segundos_proceso": round(time.perf_counter() - t_inicio, 1),
        "posiciones": posiciones_salida,
    }
    (d_salida / "observaciones.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (d_salida / "diagnostico.json").write_text(
        json.dumps(
            {
                "video": {
                    "ruta": video,
                    "cuadros": info.cuadros,
                    "fps": info.fps,
                    "resolucion": [info.ancho, info.alto],
                },
                "cuadros_elegidos": elegidos,
                "dispositivo_yolo": det_epp.dispositivo,
                "tiempos_s": {k: round(v, 2) for k, v in tiempos.t.items()},
                "posiciones": diagnostico_pos,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    avisar("listo", 100, forzar=True)
    return resultado


def _escribir_video_anotado(
    video_in: str,
    video_out: Path,
    info: cuadros.InfoVideo,
    turnos: list[contrato.TrabajadorTurno],
    mejor_por_pos: dict,
):
    cap = cv2.VideoCapture(video_in)
    if not cap.isOpened():
        return
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(video_out), fourcc, info.fps, (info.ancho, info.alto))
    n_est = max(1, len(turnos))
    c_por_est = max(1.0, info.cuadros / n_est)
    idx = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                break
            idx_est = min(n_est - 1, int(idx / c_por_est))
            t = turnos[idx_est]
            if t.posicion in mejor_por_pos:
                _, _, _, pers_f = mejor_por_pos[t.posicion]
                titulo = f"{t.posicion} · {t.nombre}"
                frame = anotar.dibujar_persona(frame, pers_f, titulo)
            writer.write(frame)
            idx += 1
    finally:
        cap.release()
        writer.release()
    anotar.recodificar_h264(video_out)


def huella(video: str, args: argparse.Namespace) -> str:
    h = hashlib.sha1()
    with open(video, "rb") as f:
        h.update(f.read(16 << 20))
    h.update(str(os.path.getsize(video)).encode())
    for clave in ("turnos", "modelo", "cada", "imgsz", "confianza", "sin_video"):
        h.update(f"{clave}={getattr(args, clave)}".encode())
    with open(args.turnos, "rb") as f:
        h.update(f.read())
    return h.hexdigest()[:16]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Video de inicio de turno -> observaciones.json")
    ap.add_argument("--video", required=True)
    ap.add_argument("--turnos", default="datos/sistema/turnos.csv")
    ap.add_argument("--salida", default="salida/")
    ap.add_argument("--modelo", default=MODELO_DEFECTO)
    ap.add_argument("--cada", type=int, default=10)
    ap.add_argument("--dispositivo", default="auto")
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--confianza", type=float, default=0.25)
    ap.add_argument("--sin-video", action="store_true")
    ap.add_argument("--cache", help="Carpeta de caché por huella SHA1")
    ap.add_argument("--progreso", help="Ruta del JSON de progreso atómico")
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    for ruidoso in ("ultralytics",):
        logging.getLogger(ruidoso).setLevel(logging.ERROR)

    guardado = Path(args.cache) / huella(args.video, args) if args.cache else None
    if guardado is not None and (guardado / "observaciones.json").exists():
        shutil.copytree(guardado, args.salida, dirs_exist_ok=True)
        r = json.loads((guardado / "observaciones.json").read_text(encoding="utf-8"))
        print(f"resultado desde caché {guardado} ({r['segundos_proceso']} s)")
    else:
        r = procesar(
            args.video,
            args.turnos,
            args.salida,
            args.modelo,
            args.cada,
            args.dispositivo,
            args.imgsz,
            args.confianza,
            not args.sin_video,
            args.progreso,
        )
        if guardado is not None:
            shutil.copytree(args.salida, guardado, dirs_exist_ok=True)

    print(f"\n{r['video']}: {len(r['posiciones'])} trabajadores evaluados en {r['segundos_proceso']} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
