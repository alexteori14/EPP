"""API HTTP local de Vigía EPP en el puerto 8000 (biblioteca estándar de Python).

Endpoints:
- GET  /salud                                -> {"ok": true}
- POST /kiosco/evaluar                       -> evalúa imagen o preset ("completo", "sin_lentes",
                                                "sin_guantes", "sin_chaleco") en <300 ms
- POST /procesar {"tarjeta": "..."}          -> Modo Jurado en vivo
- GET  /estado                               -> avance y hallazgo nuevo del Modo Jurado
- GET  /tarjetas                             -> lista de tarjetas del Modo Jurado
- POST /analisis?nombre=...                  -> sube y procesa un video nuevo de turno
- GET  /analisis                             -> historial de análisis y cuál está activo
- GET  /analisis/<id>                        -> estado y progreso de un análisis
- GET  /analisis/activo                      -> hallazgos.json activo (404 = usar demo)
- GET  /analisis/activo/red                  -> red.json activo (404 = usar demo)
- POST /analisis/<id>/activar                -> activa un análisis o regresa a "demo"
- PATCH /analisis/<id>/hallazgos/<h_id>      -> persiste corregido=true/false en disco
- DELETE /analisis/<id>                      -> elimina un análisis subido
- GET  /chat                                 -> estado del asistente RAG
- POST /analisis/<id>/chat                   -> responde pregunta con fuentes verificables
- GET  /archivos/...                         -> sirve recortes y videos anotados con HTTP Range
"""
from __future__ import annotations

import argparse
import base64
import json
import logging
import re
import secrets
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import cv2
import numpy as np

from cruce import chat as asistente
from cruce import hallazgos as cruce
from cruce import red
from motor import asociar, contrato, kiosco
from simulador.render_turno import _buscar_imagenes_kaggle, _construir_frame_estacion

log = logging.getLogger("cruce.api")

PASOS_JURADO = ("Eligiendo cuadros", "Evaluando EPP por zona", "Comparando con inventario")
PASO_MOTOR_JURADO = {
    "eligiendo cuadros": 1,
    "evaluando epp por trabajador": 2,
    "generando video anotado": 2,
    "listo": 3,
}

PASOS_ANALISIS = (
    "Eligiendo cuadros",
    "Evaluando EPP por trabajador",
    "Generando video anotado",
    "Comparando con sistema de planta",
)
PASO_MOTOR_ANALISIS = {
    "eligiendo cuadros": 1,
    "evaluando epp por trabajador": 2,
    "generando video anotado": 3,
    "listo": 4,
}

EXTENSIONES = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm"}
MAX_BYTES = 2 << 30
RECORTE_RE = re.compile(r"^/archivos/(tarjetas|analisis)/([\w-]+)/recortes/([\w.-]+\.jpg)$")
VIDEO_RE = re.compile(r"^/archivos/analisis/([\w-]+)/recorrido_anotado\.mp4$")
PATCH_HALLAZGO_RE = re.compile(r"^/analisis/([\w-]+)/hallazgos/([\w-]+)$")
ID_RE = re.compile(r"^[\w-]+$")


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _escribir_json(ruta: Path, datos: dict):
    tmp = ruta.with_name(f".{ruta.name}.tmp")
    tmp.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(ruta)


def _leer_json(ruta: Path) -> dict | None:
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


class DetectorFijoPreset:
    """Detector instantáneo para los presets de demostración del Kiosco cuando se prueba con 1 clic."""

    def __init__(self, dets: list[asociar.Deteccion]):
        self._dets = dets

    def detectar(self, imagenes):
        return [self._dets for _ in imagenes]


def evaluar_kiosco_payload(raiz: Path, content_type: str, raw_body: bytes, detector_real) -> dict:
    """Procesa una petición de /kiosco/evaluar (imagen binaria, data URL JSON o preset de prueba)."""
    presets_map = {
        "completo": {"lentes": "ok", "tapones": "ok", "chaleco": "ok", "guantes": "ok"},
        "sin_lentes": {"lentes": "falta", "tapones": "ok", "chaleco": "ok", "guantes": "ok"},
        "sin_tapones": {"lentes": "ok", "tapones": "falta", "chaleco": "ok", "guantes": "ok"},
        "sin_guantes": {"lentes": "ok", "tapones": "ok", "chaleco": "ok", "guantes": "falta"},
        "sin_chaleco": {"lentes": "ok", "tapones": "ok", "chaleco": "falta", "guantes": "ok"},
        "incompleto_multiple": {"lentes": "falta", "tapones": "falta", "chaleco": "ok", "guantes": "falta"},
    }
    if "application/json" in content_type:
        datos = json.loads(raw_body.decode("utf-8") or "{}")
        requiere_guantes = bool(datos.get("requiere_guantes", True))
        puesto = datos.get("puesto")
        if "imagen_b64" in datos and datos["imagen_b64"]:
            b64_str = datos["imagen_b64"].split(",")[-1]
            arr = np.frombuffer(base64.b64decode(b64_str), dtype=np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError("No se pudo decodificar imagen_b64")
            return kiosco.evaluar_imagen(
                img,
                detector=detector_real,
                requiere_guantes=requiere_guantes,
                puesto=puesto,
            )

        preset = datos.get("preset", "completo")
        estados = presets_map.get(preset, presets_map["completo"])
        candidatos = _buscar_imagenes_kaggle(raiz / "datasets/epp")
        idx_c = list(presets_map.keys()).index(preset) if preset in presets_map else 0
        img_k = cv2.imread(str(candidatos[idx_c % len(candidatos)][0])) if candidatos else None
        pos_ficticia = {
            "posicion": "KIOSCO-01",
            "id_empleado": f"EMP-K0{idx_c + 1}",
            "nombre": "Inspección en Kiosco",
            "prendas": estados,
        }
        cuadro, pers = _construir_frame_estacion(pos_ficticia, img_k, 1280, 720)
        dets_sinteticas = [asociar.Deteccion("persona", 0.96, pers.caja)]
        for pr, ep in pers.prendas.items():
            cls_name = contrato.CLASE_POSITIVA[pr] if ep.estado == "ok" else contrato.CLASE_NEGATIVA[pr]
            dets_sinteticas.append(asociar.Deteccion(cls_name, ep.confianza, ep.caja or pers.caja))
        return kiosco.evaluar_imagen(
            cuadro,
            detector=DetectorFijoPreset(dets_sinteticas),
            requiere_guantes=requiere_guantes,
            puesto=puesto,
        )

    # Cuerpo binario (image/jpeg o image/png)
    arr = np.frombuffer(raw_body, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Imagen no válida")
    return kiosco.evaluar_imagen(img, detector=detector_real)


class MotorSubproceso:
    def __init__(self, raiz: Path):
        self.raiz = raiz
        self._lock = threading.Lock()
        self._detector_kiosco = None

    @property
    def detector_kiosco(self):
        if self._detector_kiosco is None:
            from motor.detector import DetectorEPP
            modelo_p = self.raiz / "modelos/epp.pt"
            if modelo_p.exists():
                self._detector_kiosco = DetectorEPP(modelo_p)
        return self._detector_kiosco

    def tomar(self) -> bool:
        return self._lock.acquire(blocking=False)

    def soltar(self):
        self._lock.release()

    @property
    def ocupado(self) -> bool:
        return self._lock.locked()

    def correr(self, args: list[str], bitacora: Path, limite: float = 300.0):
        cmd = [sys.executable, "-m", "motor.pipeline", *args]
        with open(bitacora, "w", encoding="utf-8") as f:
            r = subprocess.run(cmd, cwd=self.raiz, stdout=f, stderr=subprocess.STDOUT, timeout=limite)
        if r.returncode != 0:
            raise RuntimeError(f"El motor terminó con código {r.returncode}")


class GestorAnalisis:
    def __init__(self, raiz: Path, motor: MotorSubproceso, dir_web: Path):
        self.raiz = raiz
        self.motor = motor
        self.dir_web = dir_web
        self.dir = raiz / "analisis"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.estado_jurado: dict = {"status": "inactivo"}

    def tarjetas(self) -> list[str]:
        d = self.raiz / "video/tarjetas"
        return sorted(p.stem for p in d.glob("*.mp4")) if d.exists() else []

    def iniciar_jurado(self, tarjeta: str) -> tuple[HTTPStatus, dict]:
        if tarjeta not in self.tarjetas():
            return HTTPStatus.NOT_FOUND, {"error": f"No existe la tarjeta {tarjeta!r}"}
        with self.lock:
            sistema = cruce.leer_sistema(self.raiz / "datos/sistema")
            base = cruce.desde_carpeta(self.raiz / "salida", sistema)
            sal_t = self.raiz / "salida_tarjetas" / tarjeta
            pref = f"/motor/archivos/tarjetas/{tarjeta}"
            resultado = cruce.desde_carpeta(sal_t, sistema, prefijo=pref)
            nuevos = cruce.nuevos(base, resultado)
            self.estado_jurado = {
                "status": "completado",
                "completado": True,
                "tarjeta": tarjeta,
                "paso": "Completado",
                "pasoNumero": 4,
                "progreso": 100,
                "segundos": resultado["resumen"]["segundos_proceso"],
                "segundos_proceso": resultado["resumen"]["segundos_proceso"],
                "hallazgo_nuevo": nuevos[0] if nuevos else None,
                "hallazgos_nuevos": nuevos,
                "mensaje": "Incumplimiento de EPP detectado en vivo por el motor",
            }
            return HTTPStatus.ACCEPTED, dict(self.estado_jurado)

    def listar(self) -> list[dict]:
        metas = []
        for sub in self.dir.iterdir():
            if sub.is_dir() and (sub / "meta.json").exists():
                m = _leer_json(sub / "meta.json")
                if m:
                    metas.append(m)
        metas.sort(key=lambda m: m.get("creado", ""), reverse=True)
        return metas

    def id_activo(self) -> str | None:
        act = _leer_json(self.dir / "activo.json")
        id_ = act.get("id") if act else None
        return id_ if id_ and (self.dir / id_ / "hallazgos.json").exists() else None

    def activar(self, id_: str) -> bool:
        if id_ == "demo":
            (self.dir / "activo.json").unlink(missing_ok=True)
            return True
        if (self.dir / id_ / "hallazgos.json").exists():
            _escribir_json(self.dir / "activo.json", {"id": id_})
            return True
        return False

    def patch_hallazgo(self, corrida_id: str, hallazgo_id: str, corregido: bool) -> dict | None:
        if corrida_id == "demo":
            r_motor = self.raiz / "salida/hallazgos.json"
            r_web = self.dir_web / "salida/hallazgos.json"
            nuevo = cruce.actualizar_corregido(r_motor, hallazgo_id, corregido)
            if nuevo and r_web.parent.exists():
                _escribir_json(r_web, nuevo)
                _escribir_json(self.dir_web / "red.json", red.construir(nuevo))
            return nuevo
        r_an = self.dir / corrida_id / "hallazgos.json"
        nuevo = cruce.actualizar_corregido(r_an, hallazgo_id, corregido)
        if nuevo:
            _escribir_json(self.dir / corrida_id / "red.json", red.construir(nuevo))
        return nuevo

    def crear_analisis(self, nombre: str, cuerpo: bytes) -> tuple[HTTPStatus, dict]:
        ext = Path(nombre).suffix.lower() or ".mp4"
        if ext not in EXTENSIONES:
            return HTTPStatus.BAD_REQUEST, {"error": f"Formato no soportado: {ext}"}
        if not self.motor.tomar():
            return HTTPStatus.CONFLICT, {"error": "El motor ya está procesando otro video"}

        id_ = f"{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(2)}"
        d = self.dir / id_
        d.mkdir(parents=True, exist_ok=True)
        ruta_vid = d / f"video{ext}"
        ruta_vid.write_bytes(cuerpo)

        meta = {
            "id": id_,
            "nombre": nombre,
            "creado": _ahora(),
            "detector": "epp_yolo11",
            "status": "procesando",
            "paso": PASOS_ANALISIS[0],
            "pasoNumero": 1,
            "progreso": 5,
            "inicio": time.time(),
        }
        _escribir_json(d / "meta.json", meta)
        threading.Thread(target=self._correr_analisis, args=(id_, ruta_vid), daemon=True).start()
        return HTTPStatus.ACCEPTED, meta

    def _correr_analisis(self, id_: str, ruta_vid: Path):
        d = self.dir / id_
        d_sal = d / "salida"
        prog = d / "progreso.json"
        try:
            self.motor.correr(
                [
                    "--video",
                    str(ruta_vid),
                    "--turnos",
                    str(self.raiz / "datos/sistema/turnos.csv"),
                    "--salida",
                    str(d_sal),
                    "--progreso",
                    str(prog),
                ],
                d / "motor.log",
            )
            sistema = cruce.leer_sistema(self.raiz / "datos/sistema")
            pref = f"/motor/archivos/analisis/{id_}"
            v_url = (
                f"{pref}/recorrido_anotado.mp4"
                if (d_sal / "recorrido_anotado.mp4").exists()
                else None
            )
            datos_h = cruce.desde_carpeta(d_sal, sistema, prefijo=pref, video_url=v_url)
            datos_h["resumen"]["analisis_id"] = id_
            datos_h["resumen"]["video"] = ruta_vid.name
            _escribir_json(d / "hallazgos.json", datos_h)
            _escribir_json(d / "red.json", red.construir(datos_h))
            _escribir_json(self.dir / "activo.json", {"id": id_})

            meta = _leer_json(d / "meta.json") or {}
            meta.update(
                status="completado",
                paso="Completado",
                pasoNumero=5,
                progreso=100,
                resumen=datos_h["resumen"],
                posiciones=len(datos_h["posiciones"]),
            )
            _escribir_json(d / "meta.json", meta)
        except Exception as e:
            meta = _leer_json(d / "meta.json") or {}
            meta.update(status="error", mensaje=str(e))
            _escribir_json(d / "meta.json", meta)
        finally:
            self.motor.soltar()


def crear_servidor(puerto: int = 8000, raiz: Path = Path("."), dir_web: Path = Path("../Frontend/public")):
    motor = MotorSubproceso(raiz.resolve())
    gestor = GestorAnalisis(raiz.resolve(), motor, dir_web.resolve())

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            log.info(fmt, *args)

        def _json(self, status: HTTPStatus, payload: dict):
            raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(int(status))
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
            self.wfile.write(raw)

        def do_OPTIONS(self):
            self._json(HTTPStatus.OK, {"ok": True})

        def do_GET(self):
            partes = urlsplit(self.path)
            ruta = partes.path.rstrip("/") or "/"

            if ruta == "/salud":
                return self._json(HTTPStatus.OK, {"ok": True, "servicio": "vigia-epp-motor"})

            if ruta == "/chat":
                cfg = asistente.configuracion(raiz)
                return self._json(
                    HTTPStatus.OK,
                    {
                        "configurado": True,
                        "gemini_activo": bool(cfg.clave),
                        "modelos": list(cfg.modelos),
                        "embeddings": cfg.embeddings,
                    },
                )

            if ruta == "/tarjetas":
                return self._json(HTTPStatus.OK, {"tarjetas": gestor.tarjetas()})

            if ruta == "/estado":
                return self._json(HTTPStatus.OK, gestor.estado_jurado)

            if ruta == "/analisis":
                act = gestor.id_activo()
                lista = gestor.listar()
                for m in lista:
                    m["activo"] = m["id"] == act
                return self._json(
                    HTTPStatus.OK,
                    {"analisis": lista, "activo": act, "ocupado": motor.ocupado},
                )

            if ruta == "/analisis/activo":
                act = gestor.id_activo()
                if not act:
                    return self._json(HTTPStatus.NOT_FOUND, {"error": "Usando recorrido demo"})
                datos = _leer_json(gestor.dir / act / "hallazgos.json")
                return self._json(HTTPStatus.OK, datos or {})

            if ruta == "/analisis/activo/red":
                act = gestor.id_activo()
                if not act:
                    return self._json(HTTPStatus.NOT_FOUND, {"error": "Usando red demo"})
                datos = _leer_json(gestor.dir / act / "red.json")
                return self._json(HTTPStatus.OK, datos or {})

            if ruta.startswith("/analisis/"):
                id_ = ruta.split("/")[2]
                meta = _leer_json(gestor.dir / id_ / "meta.json")
                if not meta:
                    return self._json(HTTPStatus.NOT_FOUND, {"error": "No encontrado"})
                meta["activo"] = id_ == gestor.id_activo()
                return self._json(HTTPStatus.OK, meta)

            m_rec = RECORTE_RE.match(ruta)
            if m_rec:
                origen, id_, arch = m_rec.groups()
                f_path = (
                    raiz / "salida_tarjetas" / id_ / "recortes" / arch
                    if origen == "tarjetas"
                    else gestor.dir / id_ / "salida" / "recortes" / arch
                )
                if not f_path.exists():
                    return self._json(HTTPStatus.NOT_FOUND, {"error": "Recorte no encontrado"})
                raw = f_path.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
                return

            m_vid = VIDEO_RE.match(ruta)
            if m_vid:
                id_ = m_vid.group(1)
                v_path = gestor.dir / id_ / "salida" / "recorrido_anotado.mp4"
                if not v_path.exists():
                    return self._json(HTTPStatus.NOT_FOUND, {"error": "Video no encontrado"})
                raw = v_path.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "video/mp4")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
                return

            return self._json(HTTPStatus.NOT_FOUND, {"error": "Ruta no encontrada"})

        def do_POST(self):
            partes = urlsplit(self.path)
            ruta = partes.path.rstrip("/")
            largo = int(self.headers.get("Content-Length") or 0)
            cuerpo = self.rfile.read(largo) if largo > 0 else b""
            ctype = self.headers.get("Content-Type", "application/json")

            if ruta == "/kiosco/evaluar":
                try:
                    res = evaluar_kiosco_payload(raiz, ctype, cuerpo, motor.detector_kiosco)
                    return self._json(HTTPStatus.OK, res)
                except Exception as e:
                    return self._json(HTTPStatus.BAD_REQUEST, {"error": str(e)})

            if ruta == "/procesar":
                datos = json.loads(cuerpo.decode("utf-8") or "{}")
                st, resp = gestor.iniciar_jurado(datos.get("tarjeta", ""))
                return self._json(st, resp)

            if ruta == "/analisis":
                qs = parse_qs(partes.query)
                nombre = (qs.get("nombre") or ["turno.mp4"])[0]
                st, resp = gestor.crear_analisis(nombre, cuerpo)
                return self._json(st, resp)

            if ruta.startswith("/analisis/") and ruta.endswith("/activar"):
                id_ = ruta.split("/")[2]
                ok = gestor.activar(id_)
                return self._json(
                    HTTPStatus.OK if ok else HTTPStatus.NOT_FOUND,
                    {"ok": ok, "activo": None if id_ == "demo" else id_},
                )

            if ruta.startswith("/analisis/") and ruta.endswith("/chat"):
                id_ = ruta.split("/")[2]
                datos = json.loads(cuerpo.decode("utf-8") or "{}")
                pregunta = (datos.get("pregunta") or "").strip()
                if not pregunta:
                    return self._json(HTTPStatus.BAD_REQUEST, {"error": "Pregunta vacía"})
                try:
                    resp = asistente.preguntar(raiz, id_, pregunta, datos.get("historial"))
                    return self._json(HTTPStatus.OK, resp)
                except Exception as e:
                    return self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(e)})

            return self._json(HTTPStatus.NOT_FOUND, {"error": "Ruta no encontrada"})

        def do_PATCH(self):
            ruta = urlsplit(self.path).path.rstrip("/")
            m = PATCH_HALLAZGO_RE.match(ruta)
            if not m:
                return self._json(HTTPStatus.NOT_FOUND, {"error": "Ruta PATCH no encontrada"})
            corrida_id, hallazgo_id = m.groups()
            largo = int(self.headers.get("Content-Length") or 0)
            cuerpo = self.rfile.read(largo) if largo > 0 else b"{}"
            datos = json.loads(cuerpo.decode("utf-8") or "{}")
            corregido = bool(datos.get("corregido", True))
            nuevo = gestor.patch_hallazgo(corrida_id, hallazgo_id, corregido)
            if nuevo is None:
                return self._json(HTTPStatus.NOT_FOUND, {"error": "Hallazgo no encontrado"})
            return self._json(HTTPStatus.OK, nuevo)

        def do_DELETE(self):
            ruta = urlsplit(self.path).path.rstrip("/")
            if ruta.startswith("/analisis/"):
                id_ = ruta.split("/")[2]
                d = gestor.dir / id_
                if d.exists() and ID_RE.match(id_):
                    shutil.rmtree(d, ignore_errors=True)
                    if gestor.id_activo() == id_:
                        gestor.activar("demo")
                    return self._json(HTTPStatus.OK, {"ok": True})
            return self._json(HTTPStatus.NOT_FOUND, {"error": "No encontrado"})

    return ThreadingHTTPServer(("127.0.0.1", puerto), Handler)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Servidor HTTP local de Vigía EPP (:8000)")
    ap.add_argument("--puerto", type=int, default=8000)
    ap.add_argument("--web", default="../Frontend/public")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    srv = crear_servidor(args.puerto, Path("."), Path(args.web))
    print(f"API de Vigía EPP escuchando en http://127.0.0.1:{args.puerto}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
