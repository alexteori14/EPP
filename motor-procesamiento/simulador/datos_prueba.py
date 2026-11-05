"""Genera escena/escena.json con las 12 posiciones del turno y los errores sembrados de EPP.

Al igual que en Ubik (8 errores en 12 posiciones), el turno de demostración tiene 12
trabajadores (3 líneas × 4 estaciones) con incumplimientos sembrados en los 3 equipos
obligatorios (Lentes, Chaleco, Guantes) para demostrar todas las reglas del cruce.
"""
from __future__ import annotations

import json
from pathlib import Path
from motor import contrato

# Verdad sembrada para los 12 trabajadores del turno matutino (Planta Monterrey Norte)
ESCENA_DEMO: list[dict] = [
    {
        "posicion": "L1-T1",
        "lentes": "ok",
        "chaleco": "ok",
        "guantes": "ok",
        "nota": "EPP completo (3/3)",
    },
    {
        "posicion": "L1-T2",
        "lentes": "falta",
        "chaleco": "ok",
        "guantes": "falta",
        "nota": "Soldador sin lentes ni guantes (múltiples EPP faltantes: US$760/día)",
    },
    {
        "posicion": "L1-T3",
        "lentes": "ok",
        "chaleco": "ok",
        "guantes": "ok",
        "nota": "EPP completo (3/3)",
    },
    {
        "posicion": "L1-T4",
        "lentes": "falta",
        "chaleco": "ok",
        "guantes": "ok",
        "nota": "Operador de prensa sin lentes de seguridad (US$420/día)",
    },
    {
        "posicion": "L2-T1",
        "lentes": "ok",
        "chaleco": "falta",
        "guantes": "ok",
        "nota": "Operador de montacargas sin chaleco de alta visibilidad (US$290/día)",
    },
    {
        "posicion": "L2-T2",
        "lentes": "ok",
        "chaleco": "ok",
        "guantes": "falta",
        "nota": "Auxiliar de maniobras sin guantes anticorte (US$340/día)",
    },
    {
        "posicion": "L2-T3",
        "lentes": "ok",
        "chaleco": "ok",
        "guantes": "dudoso",
        "nota": "Manos parcialmente fuera de cuadro: lectura dudosa (revisar en caseta, US$0)",
    },
    {
        "posicion": "L2-T4",
        "lentes": "falta",
        "chaleco": "falta",
        "guantes": "ok",
        "nota": "Almacenista sin lentes ni chaleco (múltiples EPP faltantes: US$710/día)",
    },
    {
        "posicion": "L3-T1",
        "lentes": "ok",
        "chaleco": "ok",
        "guantes": "ok",
        "nota": "EPP completo (3/3)",
    },
    {
        "posicion": "L3-T2",
        "lentes": "falta",
        "chaleco": "ok",
        "guantes": "ok",
        "nota": "Operador de esmerilado sin lentes de seguridad (US$420/día)",
    },
    {
        "posicion": "L3-T3",
        "lentes": "ok",
        "chaleco": "ok",
        "guantes": "falta",
        "nota": "Técnico de mantenimiento sin guantes anticorte (US$340/día)",
    },
    {
        "posicion": "L3-T4",
        "lentes": "ok",
        "chaleco": "ok",
        "guantes": "ok",
        "nota": "EPP completo (3/3)",
    },
]

# Las 4 tarjetas del Modo Jurado (cada una introduce un hallazgo nuevo sobre una posición limpia)
TARJETAS_JURADO: dict[str, dict] = {
    "sin_lentes": {
        "posicion": "L1-T1",
        "cambio": {"lentes": "falta", "chaleco": "ok", "guantes": "ok"},
        "descripcion": "Carlos Mendoza (L1-T1) intenta ingresar sin lentes de seguridad",
    },
    "sin_guantes": {
        "posicion": "L1-T3",
        "cambio": {"lentes": "ok", "chaleco": "ok", "guantes": "falta"},
        "descripcion": "Luis Fernando Vega (L1-T3) intenta ingresar sin guantes anticorte",
    },
    "sin_chaleco": {
        "posicion": "L3-T1",
        "cambio": {"lentes": "ok", "chaleco": "falta", "guantes": "ok"},
        "descripcion": "Alejandro Cabrera (L3-T1) intenta ingresar sin chaleco reflejante",
    },
    "multiple_faltante": {
        "posicion": "L3-T4",
        "cambio": {"lentes": "falta", "chaleco": "falta", "guantes": "falta"},
        "descripcion": "Eduardo Castañeda (L3-T4) intenta ingresar sin ningún equipo de protección",
    },
}


def generar_escena(dir_raiz: Path = Path(".")):
    turnos = {t.posicion: t for t in contrato.leer_turnos(dir_raiz / "datos/sistema/turnos.csv")}
    posiciones = []
    for item in ESCENA_DEMO:
        t = turnos[item["posicion"]]
        posiciones.append(
            {
                "posicion": t.posicion,
                "linea": t.linea,
                "id_empleado": t.id_empleado,
                "nombre": t.nombre,
                "puesto": t.puesto,
                "prendas": {
                    "lentes": item["lentes"],
                    "chaleco": item["chaleco"],
                    "guantes": item["guantes"],
                },
                "nota": item["nota"],
            }
        )
    escena = {
        "planta": "Planta Monterrey Norte · Aceros & Logística InduSafe",
        "turno": "Turno Matutino 06:00",
        "fecha": "2026-11-04",
        "posiciones": posiciones,
        "tarjetas_jurado": TARJETAS_JURADO,
    }
    d_esc = dir_raiz / "escena"
    d_esc.mkdir(parents=True, exist_ok=True)
    (d_esc / "escena.json").write_text(
        json.dumps(escena, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return escena


if __name__ == "__main__":
    e = generar_escena()
    print(f"escena/escena.json generada con {len(e['posiciones'])} estaciones de turno.")
