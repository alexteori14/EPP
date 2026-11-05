"""Contrato de datos y constantes anatómicas de Vigía EPP.

En esta planta industrial solo se evalúan 3 equipos obligatorios antes de iniciar turno:
1. Lentes de seguridad (`lentes` / `sin_lentes`) — zona cabeza/ojos.
2. Chaleco de alta visibilidad (`chaleco` / `sin_chaleco`) — zona torso.
3. Guantes de seguridad (`guantes` / `sin_guantes`) — zona manos/antebrazos.

No se solicita casco ni mascarilla.
"""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

# Las 7 clases canónicas del detector YOLO11 (modelos/epp.pt)
CLASES: tuple[str, ...] = (
    "persona",
    "chaleco",
    "sin_chaleco",
    "lentes",
    "sin_lentes",
    "guantes",
    "sin_guantes",
)

# Equipos obligatorios para iniciar turno (sin casco ni mascarilla)
PRENDAS: tuple[str, ...] = ("lentes", "chaleco", "guantes")

# Mapeo de cada prenda a su clase positiva y negativa en el detector
CLASE_POSITIVA: dict[str, str] = {
    "lentes": "lentes",
    "chaleco": "chaleco",
    "guantes": "guantes",
}
CLASE_NEGATIVA: dict[str, str] = {
    "lentes": "sin_lentes",
    "chaleco": "sin_chaleco",
    "guantes": "sin_guantes",
}

# Franjas verticales relativas (y_min_rel, y_max_rel) dentro de la caja de `persona`
ZONA_LENTES: tuple[float, float] = (0.00, 0.32)
ZONA_CHALECO: tuple[float, float] = (0.16, 0.72)
ZONA_GUANTES: tuple[float, float] = (0.28, 0.96)

ZONAS_ANATOMICAS: dict[str, tuple[float, float]] = {
    "lentes": ZONA_LENTES,
    "chaleco": ZONA_CHALECO,
    "guantes": ZONA_GUANTES,
}

# Extensión horizontal relativa permitida fuera de la caja de persona (ej. brazos extendidos)
MARGEN_X_ZONA: dict[str, float] = {
    "lentes": 0.05,
    "chaleco": 0.08,
    "guantes": 0.18,
}

NOMBRES_PRENDA: dict[str, str] = {
    "lentes": "Lentes de seguridad",
    "chaleco": "Chaleco reflejante",
    "guantes": "Guantes anticorte",
}


@dataclass(frozen=True)
class TrabajadorTurno:
    posicion: str
    linea: str
    id_empleado: str
    nombre: str
    puesto: str
    orden: int
    prendas_requeridas: tuple[str, ...] = PRENDAS

    @property
    def linea_num(self) -> int:
        return linea_a_numero(self.linea)

    @property
    def posicion_num(self) -> int:
        return linea_a_numero(self.posicion.split("-")[-1])


def linea_a_numero(valor: str | int) -> int:
    if isinstance(valor, int):
        return valor
    m = re.search(r"\d+", str(valor))
    return int(m.group(0)) if m else 1


def leer_turnos(ruta: str | Path) -> list[TrabajadorTurno]:
    """Lee datos/sistema/turnos.csv y devuelve la lista ordenada de estaciones del turno."""
    turnos: list[TrabajadorTurno] = []
    with open(ruta, newline="", encoding="utf-8-sig") as f:
        for idx, r in enumerate(csv.DictReader(f), start=1):
            pos = r["posicion"].strip()
            linea = (r.get("linea") or pos.split("-")[0]).strip()
            id_emp = (r.get("id_empleado") or f"EMP-{100 + idx}").strip()
            nombre = (r.get("nombre") or f"Trabajador {idx}").strip()
            puesto = (r.get("puesto") or "Operador de Planta").strip()
            orden = int(r.get("orden") or idx)
            req_str = (r.get("prendas_requeridas") or "").strip()
            req = tuple(p.strip() for p in req_str.split("|") if p.strip() in PRENDAS) if req_str else PRENDAS
            turnos.append(
                TrabajadorTurno(
                    posicion=pos,
                    linea=linea,
                    id_empleado=id_emp,
                    nombre=nombre,
                    puesto=puesto,
                    orden=orden,
                    prendas_requeridas=req,
                )
            )
    turnos.sort(key=lambda t: t.orden)
    return turnos
