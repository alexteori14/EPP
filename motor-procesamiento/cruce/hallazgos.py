"""Cruce de observaciones del motor contra el sistema de planta -> hallazgos.json.

    python -m cruce.hallazgos --salida-motor salida/ --json salida/hallazgos.json

Evalúa los 3 equipos obligatorios de la planta (Lentes, Chaleco y Guantes; sin casco ni
mascarilla), calcula el riesgo económico diario (US$/día), distingue si hay stock en caseta
para entrega inmediata o desabasto sistémico, y soporta persistencia real al marcar un
hallazgo como corregido/autorizado.
"""
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from motor import contrato

DISCLAIMER = "Filtro pre-turno · Datos reales de Kaggle + planta demostrativa InduSafe"

SUPUESTOS = (
    "Falta Lentes ANSI Z87.1: US$420/día (exposición ocular y multa NOM-017-STPS). "
    "Faltan Guantes Anticorte A4: US$340/día (riesgo de lesión manual). "
    "Falta Chaleco Clase 2: US$290/día (baja visibilidad en pasillos de montacargas). "
    "Múltiples EPP faltantes: suma del riesgo diario de cada prenda omitida. "
    "EPP agotado en caseta: riesgo diario + costo de paro de puesto (sistémico). "
    "Lectura dudosa (zona oculta o confianza < 60 %): US$0.00 (no se estima dinero sin certeza)."
)


@dataclass(frozen=True)
class PrendaInventario:
    prenda: str
    nombre_comercial: str
    existencia_caseta: int
    stock_minimo: int
    costo_unitario_usd: float
    riesgo_diario_usd: float
    riesgo_paro_usd: float


@dataclass
class Sistema:
    turnos: list[contrato.TrabajadorTurno]
    inventario: dict[str, PrendaInventario]
    reglas: dict[str, dict[str, str]]


def leer_sistema(dir_sistema: str | Path) -> Sistema:
    d = Path(dir_sistema)
    turnos = contrato.leer_turnos(d / "turnos.csv")
    inventario: dict[str, PrendaInventario] = {}
    if (d / "inventario_epp.csv").exists():
        with open(d / "inventario_epp.csv", newline="", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                pr = r["prenda"].strip()
                inventario[pr] = PrendaInventario(
                    prenda=pr,
                    nombre_comercial=r["nombre_comercial"].strip(),
                    existencia_caseta=int(float(r["existencia_caseta"])),
                    stock_minimo=int(float(r.get("stock_minimo") or 5)),
                    costo_unitario_usd=float(r.get("costo_unitario_usd") or 15.0),
                    riesgo_diario_usd=float(r["riesgo_diario_usd"]),
                    riesgo_paro_usd=float(r.get("riesgo_paro_usd") or 850.0),
                )
    reglas: dict[str, dict[str, str]] = {}
    if (d / "reglas_riesgo.csv").exists():
        with open(d / "reglas_riesgo.csv", newline="", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                reglas[r["tipo"].strip()] = r
    return Sistema(turnos=turnos, inventario=inventario, reglas=reglas)


def prendas_faltantes(o: dict) -> list[str]:
    prendas = o.get("prendas", {})
    return [pr for pr in contrato.PRENDAS if prendas.get(pr, {}).get("estado") == "falta"]


def prendas_dudosas(o: dict) -> list[str]:
    prendas = o.get("prendas", {})
    return [pr for pr in contrato.PRENDAS if prendas.get(pr, {}).get("estado") == "dudoso"]


def clasificar(o: dict, t: contrato.TrabajadorTurno, sistema: Sistema) -> str | None:
    """Devuelve el tipo de hallazgo del trabajador, o None si trae su EPP 3/3 completo."""
    if not o.get("persona_detectada", True):
        return "revisar"
    faltan = [pr for pr in prendas_faltantes(o) if pr in t.prendas_requeridas]
    dudas = [pr for pr in prendas_dudosas(o) if pr in t.prendas_requeridas]

    if faltan:
        # Verificar si alguna prenda faltante está agotada en caseta (riesgo sistémico)
        for pr in faltan:
            inv = sistema.inventario.get(pr)
            if inv is not None and inv.existencia_caseta <= 0:
                return "epp_faltante_agotado"
        if len(faltan) >= 2:
            return "multiples_epp_faltantes"
        unica = faltan[0]
        return f"sin_{unica}"

    if dudas:
        return "revisar"
    return None


def impacto_diario(tipo: str | None, o: dict, t: contrato.TrabajadorTurno, sistema: Sistema) -> float:
    if tipo is None or tipo == "revisar":
        return 0.0
    faltan = [pr for pr in prendas_faltantes(o) if pr in t.prendas_requeridas]
    if not faltan:
        return 0.0
    total = 0.0
    for pr in faltan:
        inv = sistema.inventario.get(pr)
        if inv is None:
            continue
        if tipo == "epp_faltante_agotado" and inv.existencia_caseta <= 0:
            total += inv.riesgo_paro_usd
        else:
            total += inv.riesgo_diario_usd
    return round(total, 2)


def describir(
    tipo: str,
    o: dict,
    t: contrato.TrabajadorTurno,
    sistema: Sistema,
) -> tuple[str, str]:
    """Devuelve (descripción operativa, acción sugerida en caseta)."""
    faltan = prendas_faltantes(o)
    dudas = prendas_dudosas(o)
    nombres_faltan = [contrato.NOMBRES_PRENDA[p] for p in faltan]
    nombres_dudas = [contrato.NOMBRES_PRENDA[p] for p in dudas]

    if tipo == "epp_faltante_agotado":
        pr_agotadas = [
            contrato.NOMBRES_PRENDA[p]
            for p in faltan
            if (sistema.inventario.get(p) and sistema.inventario[p].existencia_caseta <= 0)
        ]
        lista = ", ".join(pr_agotadas or nombres_faltan)
        return (
            f"{t.nombre} ({t.puesto}) no porta {lista} y el inventario en caseta reporta 0 piezas disponibles.",
            f"Detener ingreso a línea {t.linea} y solicitar resurtido urgente de {lista} a almacén central.",
        )

    if tipo == "multiples_epp_faltantes":
        lista = " y ".join([", ".join(nombres_faltan[:-1]), nombres_faltan[-1]]) if len(nombres_faltan) > 1 else nombres_faltan[0]
        stocks = ", ".join(
            f"{contrato.NOMBRES_PRENDA[p]}: {sistema.inventario[p].existencia_caseta} en caseta"
            for p in faltan
            if p in sistema.inventario
        )
        return (
            f"{t.nombre} ({t.puesto}) intentó ingresar al turno sin {lista}.",
            f"Detener en filtro y entregar {lista} desde caseta ({stocks}) antes de autorizar el pase.",
        )

    if tipo in ("sin_lentes", "sin_chaleco", "sin_guantes"):
        pr = tipo.removeprefix("sin_")
        inv = sistema.inventario.get(pr)
        nom_com = inv.nombre_comercial if inv else contrato.NOMBRES_PRENDA[pr]
        n_stock = inv.existencia_caseta if inv else 10
        return (
            f"{t.nombre} ({t.puesto}) se presentó en la fila sin {contrato.NOMBRES_PRENDA[pr].lower()}.",
            f"Entregar {nom_com} en caseta ({n_stock} piezas disponibles) y re-escanear en kiosco.",
        )

    # revisar
    pr_d = dudas[0] if dudas else "guantes"
    conf = round(100 * (o.get("prendas", {}).get(pr_d, {}).get("confianza") or 0.45))
    lista_d = ", ".join(nombres_dudas) if nombres_dudas else "equipo"
    return (
        f"La zona de {lista_d.lower()} se vio parcialmente oculta o con baja nitidez (confianza {conf} %).",
        f"Verificar visualmente {lista_d.lower()} de {t.nombre} en caseta sin detener la fila.",
    )


def fps_de(dir_motor: Path, defecto: float = 24.0) -> float:
    try:
        diag = json.loads((dir_motor / "diagnostico.json").read_text(encoding="utf-8"))
        return float(diag["video"]["fps"]) or defecto
    except Exception:
        return defecto


def construir(
    obs: dict,
    sistema: Sistema,
    fps: float = 24.0,
    prefijo: str = "/salida",
    fecha_escaneo: str | None = None,
    video_url: str | None = None,
    disclaimer: str = DISCLAIMER,
    moneda: str = "US$",
) -> dict:
    por_pos = {o["posicion"]: o for o in obs.get("posiciones", [])}
    posiciones: list[dict] = []
    hallazgos_lista: list[dict] = []

    for t in sistema.turnos:
        o = por_pos.get(t.posicion)
        if o is None:
            continue
        tipo = clasificar(o, t, sistema)
        clave = t.posicion.lower()
        cuadro = int(o.get("cuadro") or 0)
        prendas_det = o.get("prendas", {})

        rec_persona = o.get("recorte_persona")
        rec_zona = o.get("recorte_zona")
        ev_persona = f"{prefijo.rstrip('/')}/{rec_persona}" if rec_persona else None
        ev_zona = f"{prefijo.rstrip('/')}/{rec_zona}" if rec_zona else ev_persona

        completas = sum(1 for pr in contrato.PRENDAS if prendas_det.get(pr, {}).get("estado") == "ok")
        stock_min = min(
            (sistema.inventario[pr].existencia_caseta for pr in contrato.PRENDAS if pr in sistema.inventario),
            default=12,
        )

        fila = {
            "id": f"pos-{clave}",
            "codigo": t.posicion,
            "linea": t.linea_num,
            "posicion": t.posicion_num,
            "estado": "ok" if tipo is None else "revisar" if tipo == "revisar" else "error",
            "id_empleado": t.id_empleado,
            "trabajador": t.nombre,
            "puesto": t.puesto,
            "prendas_completas": completas,
            "prendas_requeridas": len(t.prendas_requeridas),
            "prendas": {
                pr: {
                    "estado": prendas_det.get(pr, {}).get("estado", "dudoso"),
                    "confianza": prendas_det.get(pr, {}).get("confianza", 0.0),
                    "lecturas": prendas_det.get(pr, {}).get("lecturas", 0),
                    "stock_caseta": sistema.inventario[pr].existencia_caseta if pr in sistema.inventario else 0,
                }
                for pr in contrato.PRENDAS
            },
            "inventario_caseta": stock_min,
            "hallazgo_id": None,
            "evidencia": ev_persona,
            "evidencia_zona": ev_zona,
        }

        if tipo is not None:
            descripcion, accion = describir(tipo, o, t, sistema)
            impacto = impacto_diario(tipo, o, t, sistema)
            faltan = prendas_faltantes(o)
            conf_min = min(
                (prendas_det.get(pr, {}).get("confianza", 0.9) for pr in (faltan or contrato.PRENDAS)),
                default=0.9,
            )
            h = {
                "id": f"hallazgo-{clave}",
                "tipo": tipo,
                "codigo": t.posicion,
                "trabajador": t.nombre,
                "id_empleado": t.id_empleado,
                "puesto": t.puesto,
                "linea": t.linea_num,
                "posicion": t.posicion_num,
                "prendas_faltantes": faltan,
                "prendas_completas": completas,
                "prendas_requeridas": len(t.prendas_requeridas),
                "impacto_diario": impacto,
                "cuadro": cuadro,
                "segundo": round(cuadro / fps, 2),
                "descripcion": descripcion,
                "accion_sugerida": accion,
                "evidencia_crop": ev_zona or ev_persona,
                "evidencia_persona": ev_persona,
                "corregido": False,
                "confianza": round(float(conf_min), 3),
            }
            hallazgos_lista.append(h)
            fila.update(
                hallazgo_id=h["id"],
                tipo=tipo,
                impacto_diario=impacto,
                accion=accion,
            )
        posiciones.append(fila)

    hallazgos_lista.sort(key=lambda h: (-h["impacto_diario"], h["linea"], h["posicion"]))
    recalcular_resumen_en_sitio(
        posiciones,
        hallazgos_lista,
        obs=obs,
        fps=fps,
        fecha_escaneo=fecha_escaneo,
        video_url=video_url,
        disclaimer=disclaimer,
        moneda=moneda,
    )
    return _armar_paquete(
        posiciones,
        hallazgos_lista,
        obs=obs,
        fps=fps,
        fecha_escaneo=fecha_escaneo,
        video_url=video_url,
        disclaimer=disclaimer,
        moneda=moneda,
    )


def _armar_paquete(
    posiciones: list[dict],
    hallazgos_lista: list[dict],
    obs: dict,
    fps: float,
    fecha_escaneo: str | None,
    video_url: str | None,
    disclaimer: str,
    moneda: str,
) -> dict:
    activos = [h for h in hallazgos_lista if not h.get("corregido") and h["tipo"] != "revisar"]
    todos_errores = [h for h in hallazgos_lista if h["tipo"] != "revisar"]
    dudosas = [h for h in hallazgos_lista if h["tipo"] == "revisar"]
    agotados = [h for h in activos if h["tipo"] == "epp_faltante_agotado"]
    total_riesgo = round(sum(h["impacto_diario"] for h in activos), 2)
    riesgo_recuperado = round(sum(h["impacto_diario"] for h in todos_errores if h.get("corregido")), 2)

    ok_count = sum(
        1
        for p in posiciones
        if p["estado"] == "ok"
        or any(h["id"] == p.get("hallazgo_id") and h.get("corregido") for h in hallazgos_lista)
    )
    n_prob = len(activos)
    frase = (
        f"{n_prob} trabajador{'es' if n_prob != 1 else ''} sin EPP completo · "
        f"{moneda}{total_riesgo:,.2f} al día en riesgo"
    )
    resumen = {
        "total_problemas": n_prob,
        "dinero_en_riesgo_diario": total_riesgo,
        "dinero_recuperado_diario": riesgo_recuperado,
        "frase": frase,
        "trabajadores_incompletos": n_prob,
        "epp_agotados": len(agotados),
        "lecturas_dudosas": len(dudosas),
        "cumplimiento_turno_pct": round(100.0 * ok_count / len(posiciones), 1) if posiciones else 100.0,
        "planta_id": "MTY-N01",
        "planta_nombre": "Planta Monterrey Norte · Aceros & Logística InduSafe",
        "turno_nombre": "Turno Matutino 06:00",
        "prendas_evaluadas": list(contrato.PRENDAS),
        "fecha_escaneo": fecha_escaneo or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "disclaimer": disclaimer,
        "moneda": moneda,
        "video": obs.get("video"),
        "video_url": video_url,
        "segundos_proceso": obs.get("segundos_proceso"),
        "fps": fps,
        "supuestos_calculo": SUPUESTOS,
    }
    return {"resumen": resumen, "posiciones": posiciones, "hallazgos": hallazgos_lista}


def recalcular_resumen_en_sitio(*a, **kw):
    return None


def actualizar_corregido(ruta_json: Path, hallazgo_id: str, corregido: bool) -> dict | None:
    """Actualiza de forma atómica el estado `corregido` de un hallazgo en disco y recalcula el resumen."""
    if not ruta_json.exists():
        return None
    datos = json.loads(ruta_json.read_text(encoding="utf-8"))
    encontrado = False
    for h in datos.get("hallazgos", []):
        if h["id"] == hallazgo_id:
            h["corregido"] = bool(corregido)
            encontrado = True
            break
    if not encontrado:
        return None

    res_ant = datos.get("resumen", {})
    obs_meta = {
        "video": res_ant.get("video"),
        "segundos_proceso": res_ant.get("segundos_proceso"),
    }
    nuevo = _armar_paquete(
        datos["posiciones"],
        datos["hallazgos"],
        obs=obs_meta,
        fps=float(res_ant.get("fps") or 24.0),
        fecha_escaneo=res_ant.get("fecha_escaneo"),
        video_url=res_ant.get("video_url"),
        disclaimer=res_ant.get("disclaimer", DISCLAIMER),
        moneda=res_ant.get("moneda", "US$"),
    )
    if "analisis_id" in res_ant:
        nuevo["resumen"]["analisis_id"] = res_ant["analisis_id"]

    tmp = ruta_json.with_name(f".{ruta_json.name}.tmp")
    tmp.write_text(json.dumps(nuevo, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(ruta_json)
    return nuevo


def desde_carpeta(
    dir_motor: str | Path,
    sistema: Sistema,
    prefijo: str = "/salida",
    **opciones,
) -> dict:
    d = Path(dir_motor)
    ruta = d / "observaciones.json"
    obs = json.loads(ruta.read_text(encoding="utf-8"))
    fecha = datetime.fromtimestamp(ruta.stat().st_mtime, timezone.utc).isoformat(timespec="seconds")
    return construir(obs, sistema, fps_de(d), prefijo, fecha, **opciones)


def nuevos(base: dict, otro: dict) -> list[dict]:
    vistos = {(h["linea"], h["posicion"], h["tipo"]) for h in base.get("hallazgos", [])}
    return [
        h
        for h in otro.get("hallazgos", [])
        if (h["linea"], h["posicion"], h["tipo"]) not in vistos
    ]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="observaciones.json + sistema -> hallazgos.json")
    ap.add_argument("--salida-motor", default="salida/")
    ap.add_argument("--sistema", default="datos/sistema/")
    ap.add_argument("--json", default=None)
    ap.add_argument("--prefijo", default="/salida")
    args = ap.parse_args(argv)

    datos = desde_carpeta(args.salida_motor, leer_sistema(args.sistema), args.prefijo)
    destino = Path(args.json or Path(args.salida_motor) / "hallazgos.json")
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{datos['resumen']['frase']} -> {destino}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
