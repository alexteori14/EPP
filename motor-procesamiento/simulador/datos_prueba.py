"""Genera escena/escena.json con las 12 posiciones del turno y los errores sembrados de EPP.

Evalúa los 4 componentes de EPP de la planta (sin casco ni mascarilla):
- Obligatorios generales (3): Lentes (`lentes`), Tapones auditivos de inserción (`tapones`) y Chaleco (`chaleco`).
- Condicional / opcional por puesto (1): Guantes anticorte (`guantes`), obligatorios solo en puestos
  operativos de corte/soldadura/prensa/maniobras y opcionales en supervisión/inspección/montacargas.
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
        "tapones": "ok",
        "chaleco": "ok",
        "guantes": "ok",
        "nota": "EPP completo (4/4 requeridos para Corte CNC)",
    },
    {
        "posicion": "L1-T2",
        "lentes": "falta",
        "tapones": "falta",
        "chaleco": "ok",
        "guantes": "falta",
        "nota": "Soldador sin lentes, sin tapones auditivos ni guantes (múltiples EPP faltantes: US$1,140/día)",
    },
    {
        "posicion": "L1-T3",
        "lentes": "ok",
        "tapones": "ok",
        "chaleco": "ok",
        "guantes": "ok",
        "nota": "EPP completo (4/4 requeridos para Troquelado)",
    },
    {
        "posicion": "L1-T4",
        "lentes": "falta",
        "tapones": "ok",
        "chaleco": "ok",
        "guantes": "ok",
        "nota": "Operador de prensa sin lentes de seguridad (US$420/día)",
    },
    {
        "posicion": "L2-T1",
        "lentes": "ok",
        "tapones": "ok",
        "chaleco": "falta",
        "guantes": "falta",
        "nota": "Operador de montacargas sin chaleco (US$290/día · guantes opcionales en su puesto)",
    },
    {
        "posicion": "L2-T2",
        "lentes": "ok",
        "tapones": "ok",
        "chaleco": "ok",
        "guantes": "falta",
        "nota": "Auxiliar de maniobras sin guantes anticorte obligatorios en su puesto (US$340/día)",
    },
    {
        "posicion": "L2-T3",
        "lentes": "ok",
        "tapones": "dudoso",
        "chaleco": "ok",
        "guantes": "falta",
        "nota": "Supervisor de patio: zona auditiva parcialmente oculta (revisar en caseta, US$0 · guantes opcionales)",
    },
    {
        "posicion": "L2-T4",
        "lentes": "falta",
        "tapones": "ok",
        "chaleco": "falta",
        "guantes": "falta",
        "nota": "Almacenista sin lentes ni chaleco (US$710/día · guantes opcionales en almacén)",
    },
    {
        "posicion": "L3-T1",
        "lentes": "ok",
        "tapones": "ok",
        "chaleco": "ok",
        "guantes": "falta",
        "nota": "Inspector de calidad autorizado (3/3 requeridos: Lentes + Tapones + Chaleco · Guantes opcionales)",
    },
    {
        "posicion": "L3-T2",
        "lentes": "ok",
        "tapones": "falta",
        "chaleco": "ok",
        "guantes": "ok",
        "nota": "Operador de esmerilado sin tapones auditivos de inserción en zona de 96 dB (US$380/día)",
    },
    {
        "posicion": "L3-T3",
        "lentes": "ok",
        "tapones": "ok",
        "chaleco": "ok",
        "guantes": "falta",
        "nota": "Técnico de mantenimiento sin guantes anticorte obligatorios (US$340/día)",
    },
    {
        "posicion": "L3-T4",
        "lentes": "ok",
        "tapones": "ok",
        "chaleco": "ok",
        "guantes": "ok",
        "nota": "EPP completo (4/4 requeridos para Subensambles)",
    },
]

# Tarjetas del Modo Jurado (cada una introduce un hallazgo nuevo sobre una posición limpia)
TARJETAS_JURADO: dict[str, dict] = {
    "sin_lentes": {
        "posicion": "L1-T1",
        "cambio": {"lentes": "falta", "tapones": "ok", "chaleco": "ok", "guantes": "ok"},
        "descripcion": "Carlos Mendoza (L1-T1) intenta ingresar sin lentes de seguridad",
    },
    "sin_tapones": {
        "posicion": "L1-T3",
        "cambio": {"lentes": "ok", "tapones": "falta", "chaleco": "ok", "guantes": "ok"},
        "descripcion": "Luis Fernando Vega (L1-T3 · Troquelado 95 dB) intenta ingresar sin tapones auditivos",
    },
    "sin_guantes": {
        "posicion": "L1-T3",
        "cambio": {"lentes": "ok", "tapones": "ok", "chaleco": "ok", "guantes": "falta"},
        "descripcion": "Luis Fernando Vega (L1-T3) intenta ingresar sin guantes anticorte",
    },
    "sin_chaleco": {
        "posicion": "L3-T1",
        "cambio": {"lentes": "ok", "tapones": "ok", "chaleco": "falta", "guantes": "falta"},
        "descripcion": "Alejandro Cabrera (L3-T1) intenta ingresar sin chaleco reflejante",
    },
    "multiple_faltante": {
        "posicion": "L3-T4",
        "cambio": {"lentes": "falta", "tapones": "falta", "chaleco": "falta", "guantes": "falta"},
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
                "requiere_guantes": t.requiere_guantes,
                "prendas_requeridas": list(t.prendas_requeridas),
                "prendas": {
                    "lentes": item["lentes"],
                    "tapones": item["tapones"],
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
