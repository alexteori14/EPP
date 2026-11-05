"""Proyección de riesgo a la red de plantas industriales (`red.json`).

Al igual que en Ubik (que separa lo sistémico de lo local para no inflar la cifra),
Vigía EPP proyecta a las 18 plantas del grupo industrial los riesgos sistémicos de
incumplimiento recurrente / protocolo de dotación en inicio de turno en escenarios
conservadores (10 %, 25 %, 50 % y 100 % de las plantas), manteniendo separados los
hallazgos locales del filtro de hoy.
"""
from __future__ import annotations

import json
from pathlib import Path

PLANTAS_TOTAL = 18
DIAS_MES = 30


def construir(hallazgos_data: dict, plantas_total: int = PLANTAS_TOTAL) -> dict:
    resumen = hallazgos_data["resumen"]
    moneda = resumen.get("moneda", "US$")
    otras_plantas = max(0, plantas_total - 1)

    hallazgos = [
        h for h in hallazgos_data.get("hallazgos", [])
        if h["tipo"] != "revisar" and not h.get("corregido")
    ]
    # Sistémicos: reincidencia de ingreso con múltiples EPP faltantes o desabasto en caseta
    tipos_sistemicos = {"epp_faltante_agotado", "multiples_epp_faltantes"}
    sistemicos_h = [h for h in hallazgos if h["tipo"] in tipos_sistemicos]
    locales_h = [h for h in hallazgos if h["tipo"] not in tipos_sistemicos]

    sistemico_diario = round(sum(h["impacto_diario"] for h in sistemicos_h), 2)
    local_diario = round(sum(h["impacto_diario"] for h in locales_h), 2)
    medido_diario = round(sistemico_diario + local_diario, 2)

    definicion_escenarios = [
        ("bajo", "Bajo (10 % de plantas)", 0.10),
        ("central", "Central (25 % de plantas)", 0.25),
        ("alto", "Alto (50 % de plantas)", 0.50),
        ("peor_caso", "Peor caso (toda la red)", 1.00),
    ]
    escenarios = []
    for id_esc, etiqueta, frac in definicion_escenarios:
        n_plantas = max(1, round(otras_plantas * frac)) if otras_plantas > 0 else 0
        diario_red = round(n_plantas * sistemico_diario, 2)
        escenarios.append(
            {
                "id": id_esc,
                "etiqueta": etiqueta,
                "fraccion": frac,
                "plantas": n_plantas,
                "diario": diario_red,
                "mensual": round(diario_red * DIAS_MES, 2),
            }
        )

    sistemicos_detalle = [
        {
            "codigo": h["codigo"],
            "trabajador": h["trabajador"],
            "puesto": h["puesto"],
            "tipo": h["tipo"],
            "prendas_faltantes": h.get("prendas_faltantes", []),
            "impacto_diario": h["impacto_diario"],
            "peor_caso_diario": round(h["impacto_diario"] * otras_plantas, 2),
        }
        for h in sistemicos_h
    ]

    por_tipo_local: dict[str, dict] = {}
    for h in locales_h:
        t = h["tipo"]
        if t not in por_tipo_local:
            por_tipo_local[t] = {"tipo": t, "cantidad": 0, "impacto_diario": 0.0}
        por_tipo_local[t]["cantidad"] += 1
        por_tipo_local[t]["impacto_diario"] = round(
            por_tipo_local[t]["impacto_diario"] + h["impacto_diario"], 2
        )

    return {
        "red": {
            "plantas_total": plantas_total,
            "otras_plantas": otras_plantas,
            "moneda": moneda,
            "medido_diario": medido_diario,
            "sistemico_diario": sistemico_diario,
            "local_diario": local_diario,
            "problemas_sistemicos": len(sistemicos_h),
            "problemas_locales": len(locales_h),
            "dias_mes": DIAS_MES,
            "supuestos_calculo": resumen.get("supuestos_calculo", ""),
            "dataset_label": resumen.get("disclaimer", ""),
            "fecha_corte": (resumen.get("fecha_escaneo") or "")[:10],
            "origen": resumen.get("video") or "recorrido_turno.mp4",
        },
        "escenarios": escenarios,
        "sistemicos": sistemicos_detalle,
        "locales": list(por_tipo_local.values()),
    }


def desde_archivo(ruta_hallazgos: str | Path) -> dict:
    datos = json.loads(Path(ruta_hallazgos).read_text(encoding="utf-8"))
    return construir(datos)
