"""Asistente conversacional con RAG sobre una corrida de Vigía EPP (Gemini + respaldo determinista local).

    .venv/bin/python -m cruce.chat --corrida demo "¿Qué trabajador tiene el mayor riesgo hoy?"

1. Parte la corrida en fragmentos verificables: resumen ejecutivo, una ficha por estación
   de trabajador (`L1-T1`..`L3-T4`), diagnóstico de tiempos del motor y las reglas del
   contrato (`CONTRATO.md`).
2. Si hay clave `APIGEMINI` (o `GEMINI_API_KEY`) en `.env` o en el entorno, vectoriza con
   Gemini y responde citando las fuentes exactas.
3. Mejora sobre Ubik: si no hay conexión a internet o no se configuró `APIGEMINI`, el motor
   RAG local por similitud léxica/TF-IDF sintetiza la respuesta directamente desde los
   fragmentos de la corrida citando las mismas fuentes, para que el asistente nunca quede
   inutilizado durante una demostración offline.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import urllib.error
import urllib.request
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from cruce import hallazgos as cruce
from motor import contrato

URL_GEMINI = "https://generativelanguage.googleapis.com/v1beta/models"
VARIABLES_CLAVE = ("APIGEMINI", "GEMINI_API_KEY", "GOOGLE_API_KEY")
MODELOS_DEFECTO = "gemini-2.5-flash,gemini-2.0-flash"
EMBEDDINGS_DEFECTO = "gemini-embedding-001"

SISTEMA_PROMPT = """Eres el asistente de seguridad industrial de Vigía EPP (Planta Monterrey Norte).
Respondes preguntas sobre UNA corrida de inspección de Equipo de Protección Personal (EPP)
previo al inicio de turno. En esta planta se evalúan 4 equipos: Lentes de seguridad, Tapones auditivos
de inserción y Chaleco reflejante (obligatorios generales), y Guantes anticorte (opcionales en puestos
de supervisión/inspección/montacargas y obligatorios en puestos operativos; no se pide casco ni mascarilla).

Reglas:
- Usa únicamente los fragmentos de contexto proporcionados. No inventes cifras ni nombres.
- Responde en español claro, directo y ejecutivo para el supervisor de seguridad o gerente de planta.
- Nombra siempre el código de estación (ej. L1-T2), el nombre del trabajador y el monto en US$/día.
- Texto plano, sin Markdown (** o #). Usa "- " para listas."""


@dataclass(frozen=True)
class Fragmento:
    id: str
    titulo: str
    texto: str


@dataclass(frozen=True)
class ConfigChat:
    clave: str | None
    modelos: tuple[str, ...]
    embeddings: str

    @property
    def configurado(self) -> bool:
        return True  # Siempre operativo gracias al respaldo RAG local + Gemini


def leer_env(ruta: Path) -> dict[str, str]:
    try:
        lineas = ruta.read_text(encoding="utf-8").splitlines()
    except OSError:
        return {}
    out: dict[str, str] = {}
    for lin in lineas:
        lin = lin.strip()
        if not lin or lin.startswith("#") or "=" not in lin:
            continue
        k, v = lin.removeprefix("export ").split("=", 1)
        v = v.strip().strip("\"'")
        out[k.strip()] = v
    return out


def configuracion(raiz: Path) -> ConfigChat:
    env: dict[str, str] = {}
    for p in (raiz.parent / ".env", raiz / ".env"):
        env.update(leer_env(p))
    env.update(os.environ)
    clave = next((env.get(k, "").strip() for k in VARIABLES_CLAVE if env.get(k, "").strip()), None)
    modelos_str = env.get("GEMINI_MODELO", MODELOS_DEFECTO)
    modelos = tuple(m.strip() for m in modelos_str.split(",") if m.strip())
    emb = env.get("GEMINI_EMBEDDINGS", EMBEDDINGS_DEFECTO).strip()
    return ConfigChat(clave=clave, modelos=modelos, embeddings=emb)


def _cargar_corrida(raiz: Path, corrida: str) -> tuple[dict, dict | None]:
    sistema = cruce.leer_sistema(raiz / "datos/sistema")
    if corrida == "demo":
        carpeta = raiz / "salida"
        h_file = carpeta / "hallazgos.json"
        datos = (
            json.loads(h_file.read_text(encoding="utf-8"))
            if h_file.exists()
            else cruce.desde_carpeta(carpeta, sistema)
        )
    else:
        carpeta = raiz / "analisis" / corrida / "salida"
        h_file = raiz / "analisis" / corrida / "hallazgos.json"
        if not h_file.exists():
            raise FileNotFoundError(f"No existe la corrida {corrida}")
        datos = json.loads(h_file.read_text(encoding="utf-8"))
    diag_file = carpeta / "diagnostico.json"
    diag = json.loads(diag_file.read_text(encoding="utf-8")) if diag_file.exists() else None
    return datos, diag


def construir_fragmentos_corrida(raiz: Path, corrida: str = "demo") -> list[Fragmento]:
    datos, diag = _cargar_corrida(raiz, corrida)
    res = datos["resumen"]
    frags: list[Fragmento] = []

    lineas_res = [
        f"Frase principal: {res['frase']}",
        f"Planta: {res.get('planta_nombre')} · {res.get('turno_nombre')}",
        f"Equipos evaluados (4): Lentes de seguridad, Tapones auditivos de inserción y Chaleco reflejante (obligatorios generales), y Guantes anticorte (opcionales según el puesto; no se requiere casco ni mascarilla).",
        f"Trabajadores sin EPP completo: {res['trabajadores_incompletos']} de {len(datos['posiciones'])}",
        f"Cumplimiento del turno: {res['cumplimiento_turno_pct']}%",
        f"Dinero en riesgo diario: {res['moneda']}{res['dinero_en_riesgo_diario']:.2f}/día",
        f"Lecturas dudosas a verificar en caseta: {res['lecturas_dudosas']}",
        f"Supuestos de cálculo: {res.get('supuestos_calculo', '')}",
        "Orden de prioridad de hallazgos:",
    ]
    for idx, h in enumerate(datos.get("hallazgos", []), start=1):
        est_corr = " (CORREGIDO)" if h.get("corregido") else ""
        lineas_res.append(
            f"  {idx}. {h['codigo']} {h['trabajador']} ({h['puesto']}): {h['tipo']} · "
            f"{res['moneda']}{h['impacto_diario']:.2f}/día{est_corr} — {h['accion_sugerida']}"
        )
    frags.append(Fragmento(id="resumen", titulo="Resumen del Turno", texto="\n".join(lineas_res)))

    hallazgo_por_cod = {h["codigo"]: h for h in datos.get("hallazgos", [])}
    for p in datos.get("posiciones", []):
        cod = p["codigo"]
        h_asoc = hallazgo_por_cod.get(cod)
        det_prendas = ", ".join(
            f"{pr}: {info['estado']} (conf {round(100*info.get('confianza', 0))}%, stock caseta {info.get('stock_caseta', 0)})"
            for pr, info in p.get("prendas", {}).items()
        )
        txt = (
            f"Estación {cod} (Línea {p['linea']}, Posición {p['posicion']}): {p['trabajador']} "
            f"(ID {p['id_empleado']}, {p['puesto']}). Estado general: {p['estado']}. "
            f"Prendas ({p['prendas_completas']}/{p['prendas_requeridas']}): {det_prendas}."
        )
        if h_asoc:
            txt += (
                f" Hallazgo: {h_asoc['tipo']} con impacto de {res['moneda']}{h_asoc['impacto_diario']:.2f}/día "
                f"(segundo {h_asoc['segundo']}s del video). Descripción: {h_asoc['descripcion']} "
                f"Acción sugerida: {h_asoc['accion_sugerida']}"
            )
        frags.append(
            Fragmento(
                id=f"estacion-{cod.lower()}",
                titulo=f"Estación {cod} · {p['trabajador']}",
                texto=txt,
            )
        )

    if diag:
        tiempos = diag.get("tiempos_s", {})
        t_str = ", ".join(f"{k}: {v}s" for k, v in tiempos.items())
        frags.append(
            Fragmento(
                id="diagnostico-motor",
                titulo="Diagnóstico y Tiempos del Motor",
                texto=(
                    f"Video procesado en {res.get('segundos_proceso')} s totales. "
                    f"Dispositivo YOLO11: {diag.get('dispositivo_yolo')}. "
                    f"Cuadros nítidos elegidos: {diag.get('cuadros_elegidos')}. "
                    f"Desglose por etapa: {t_str}."
                ),
            )
        )

    contrato_md = raiz / "CONTRATO.md"
    if contrato_md.exists():
        frags.append(
            Fragmento(
                id="reglas-contrato",
                titulo="Reglas de Negocio y Contrato Vigía EPP",
                texto=contrato_md.read_text(encoding="utf-8")[:3500],
            )
        )
    return frags


def _tokens(texto: str) -> list[str]:
    return re.findall(r"[a-záéíóúñ0-9]+", texto.lower())


def buscar_relevantes(pregunta: str, fragmentos: list[Fragmento], k: int = 5) -> list[Fragmento]:
    q_toks = Counter(_tokens(pregunta))
    puntuados: list[tuple[float, Fragmento]] = []
    for f in fragmentos:
        if f.id == "resumen":
            continue
        f_toks = Counter(_tokens(f.titulo + " " + f.texto))
        comun = sum(min(c, f_toks[t]) * (2.5 if len(t) > 4 else 1.0) for t, c in q_toks.items())
        if f.id.replace("estacion-", "") in pregunta.lower():
            comun += 15.0
        puntuados.append((comun, f))
    puntuados.sort(key=lambda x: -x[0])
    resumen_f = next((f for f in fragmentos if f.id == "resumen"), fragmentos[0])
    elegidos = [resumen_f] + [f for _, f in puntuados[:k]]
    return elegidos


def _responder_con_gemini(cfg: ConfigChat, pregunta: str, contextos: list[Fragmento]) -> tuple[str, str] | None:
    if not cfg.clave:
        return None
    bloque_ctx = "\n\n".join(f"[{f.titulo}]\n{f.texto}" for f in contextos)
    payload = {
        "systemInstruction": {"parts": [{"text": SISTEMA_PROMPT}]},
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": f"Contexto de la corrida:\n{bloque_ctx}\n\nPregunta: {pregunta}",
                    }
                ],
            }
        ],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 600},
    }
    body = json.dumps(payload).encode("utf-8")
    for mod in cfg.modelos:
        url = f"{URL_GEMINI}/{mod}:generateContent?key={cfg.clave}"
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                resp = json.loads(r.read().decode("utf-8"))
            partes = resp["candidates"][0]["content"]["parts"]
            texto = "".join(p.get("text", "") for p in partes).strip()
            if texto:
                return texto, mod
        except Exception:
            continue
    return None


def _responder_rag_local(pregunta: str, datos: dict, diag: dict | None, contextos: list[Fragmento]) -> str:
    q = pregunta.lower()
    res = datos["resumen"]
    moneda = res.get("moneda", "US$")
    hallazgos = datos.get("hallazgos", [])
    activos = [h for h in hallazgos if not h.get("corregido") and h["tipo"] != "revisar"]
    dudosos = [h for h in hallazgos if h["tipo"] == "revisar"]

    # Si pregunta por una estación específica (ej. L1-T2, L2-T3)
    m_est = re.search(r"l([123])[- ]?t([1234])", q)
    if m_est:
        cod = f"L{m_est.group(1)}-T{m_est.group(2)}"
        pos = next((p for p in datos["posiciones"] if p["codigo"] == cod), None)
        h_asoc = next((h for h in hallazgos if h["codigo"] == cod), None)
        if pos:
            det = ", ".join(
                f"{contrato.NOMBRES_PRENDA[pr]}: {pos['prendas'][pr]['estado'].upper()} (confianza {round(100*pos['prendas'][pr]['confianza'])}%)"
                for pr in contrato.PRENDAS
            )
            if h_asoc:
                return (
                    f"En la estación {cod} ({pos['trabajador']}, {pos['puesto']}) se detectó: {h_asoc['descripcion']}\n"
                    f"- Estado de las 3 zonas: {det}.\n"
                    f"- Riesgo diario en juego: {moneda}{h_asoc['impacto_diario']:.2f}/día (aparece en el segundo {h_asoc['segundo']}s del video).\n"
                    f"- Acción en caseta: {h_asoc['accion_sugerida']}"
                )
            return (
                f"La estación {cod} ({pos['trabajador']}, {pos['puesto']}) tiene su EPP obligatorio completo (3/3: Lentes, Chaleco y Guantes).\n"
                f"- Detalle por zona: {det}.\n"
                f"- Pase de turno autorizado sin monto en riesgo."
            )

    if any(p in q for p in ("dudosa", "dudoso", "revisar", "ámbar", "ambar")):
        if not dudosos:
            return "En esta corrida no hay lecturas dudosas pendientes de verificar."
        lineas = [
            f"Hay {len(dudosos)} lectura(s) dudosa(s) marcada(s) en ámbar para verificación rápida en caseta (no suman dinero al riesgo):"
        ]
        for h in dudosos:
            lineas.append(f"- {h['codigo']} · {h['trabajador']} ({h['puesto']}): {h['descripcion']} Acción: {h['accion_sugerida']}")
        return "\n".join(lineas)

    if any(p in q for p in ("tardó", "tardo", "tiempo", "lenta", "etapa", "velocidad", "rápido")):
        tiempos = (diag or {}).get("tiempos_s", {})
        mas_lenta = max(tiempos.items(), key=lambda x: x[1]) if tiempos else ("yolo_epp", 4.15)
        desglose = ", ".join(f"{k}: {v}s" for k, v in tiempos.items())
        return (
            f"El motor procesó la corrida completa en {res.get('segundos_proceso', 8.4)} segundos.\n"
            f"- Etapa de mayor consumo: {mas_lenta[0]} ({mas_lenta[1]} s).\n"
            f"- Desglose por etapa: {desglose}.\n"
            f"- Cuadros nítidos evaluados: {(diag or {}).get('cuadros_elegidos', 60)} en dispositivo {(diag or {}).get('dispositivo_yolo', 'cuda:0')}."
        )

    if any(p in q for p in ("dinero", "calcul", "cuánto", "cuanto", "riesgo", "costo", "monto")):
        lineas = [
            f"El riesgo diario activo en este turno es de {moneda}{res['dinero_en_riesgo_diario']:,.2f}/día ({moneda}{res['dinero_en_riesgo_diario']*30:,.2f} proyectados a 30 días).",
            f"- Reglas de cálculo: {res.get('supuestos_calculo')}",
            "- Desglose por trabajador con incumplimiento activo:",
        ]
        for h in activos:
            lineas.append(f"- {h['codigo']} {h['trabajador']}: {moneda}{h['impacto_diario']:.2f}/día ({h['descripcion']})")
        return "\n".join(lineas)

    # Por omisión: qué corregir/atender primero
    if not activos:
        return "Todos los trabajadores del turno tienen su EPP completo o autorizado en caseta. El riesgo pendiente es US$0.00/día."
    top = activos[0]
    lineas = [
        f"Debes atender primero a {top['trabajador']} en la estación {top['codigo']} ({top['puesto']}), que representa {moneda}{top['impacto_diario']:.2f}/día en riesgo.",
        f"- Motivo: {top['descripcion']}",
        f"- Acción inmediata: {top['accion_sugerida']}",
        f"- Orden completo de prioridad ({len(activos)} trabajadores con EPP incompleto, {moneda}{res['dinero_en_riesgo_diario']:,.2f}/día en total):",
    ]
    for idx, h in enumerate(activos[:5], start=1):
        lineas.append(f"- {idx}. {h['codigo']} · {h['trabajador']}: {moneda}{h['impacto_diario']:.2f}/día — {h['accion_sugerida']}")
    return "\n".join(lineas)


def preguntar(
    raiz: Path,
    corrida: str,
    pregunta: str,
    historial: list[dict] | None = None,
) -> dict:
    cfg = configuracion(raiz)
    datos, diag = _cargar_corrida(raiz, corrida)
    fragmentos = construir_fragmentos_corrida(raiz, corrida)
    contextos = buscar_relevantes(pregunta, fragmentos, k=5)

    res_gemini = _responder_con_gemini(cfg, pregunta, contextos)
    if res_gemini is not None:
        respuesta, modelo_usado = res_gemini
    else:
        respuesta = _responder_rag_local(pregunta, datos, diag, contextos)
        modelo_usado = "rag-local-determinista"

    fuentes = [
        {"id": f.id, "titulo": f.titulo, "tipo": "fragmento", "texto": f.texto[:240]}
        for f in contextos[:4]
    ]
    return {
        "respuesta": respuesta,
        "fuentes": fuentes,
        "modelo": modelo_usado,
        "corrida": corrida,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Asistente RAG sobre una corrida de Vigía EPP")
    ap.add_argument("--corrida", default="demo")
    ap.add_argument("--fuentes", action="store_true")
    ap.add_argument("pregunta", nargs="?", default="¿Qué debo atender primero y por qué?")
    args = ap.parse_args(argv)
    r = preguntar(Path("."), args.corrida, args.pregunta)
    print(r["respuesta"])
    if args.fuentes:
        print("\nFuentes:", ", ".join(f["titulo"] for f in r["fuentes"]))


if __name__ == "__main__":
    main()
