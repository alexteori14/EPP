"""Contrato de datos y constantes anatómicas de Vigía EPP.

En esta planta industrial se evalúan 4 componentes de Equipo de Protección Personal (EPP)
antes de iniciar turno (sin casco ni mascarilla):
1. Lentes de seguridad (`lentes` / `sin_lentes`) — zona cabeza/ojos (obligatorio general).
2. Tapones auditivos de inserción (`tapones` / `sin_tapones`) — zona oídos/cráneo lateral
   para evitar daño auditivo por ruido industrial >85 dB(A) (obligatorio general).
3. Chaleco de alta visibilidad (`chaleco` / `sin_chaleco`) — zona torso (obligatorio general).
4. Guantes de seguridad (`guantes` / `sin_guantes`) — zona manos/antebrazos (condicional/opcional
   según el puesto de trabajo dentro de la fábrica).
"""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

# Las 9 clases canónicas del detector YOLO11 (modelos/epp.pt)
CLASES: tuple[str, ...] = (
    "persona",
    "chaleco",
    "sin_chaleco",
    "lentes",
    "sin_lentes",
    "guantes",
    "sin_guantes",
    "tapones",
    "sin_tapones",
)

# Equipos evaluados en el filtro de inicio de turno (sin casco ni mascarilla)
PRENDAS: tuple[str, ...] = ("lentes", "tapones", "chaleco", "guantes")

# Equipos obligatorios para TODOS los puestos vs condicionales por puesto
PRENDAS_GENERALES: tuple[str, ...] = ("lentes", "tapones", "chaleco")
PRENDAS_OPCIONALES_POR_PUESTO: tuple[str, ...] = ("guantes",)

# Puestos cuyo perfil de riesgo NO exige guantes anticorte (guantes opcionales)
PUESTOS_GUANTES_OPCIONALES: frozenset[str] = frozenset(
    {
        "Operador de Montacargas",
        "Supervisor de Patio",
        "Almacenista de Acero",
        "Inspector de Calidad",
        "Coordinador de Logística",
    }
)

# Mapeo de cada prenda a su clase positiva y negativa en el detector
CLASE_POSITIVA: dict[str, str] = {
    "lentes": "lentes",
    "tapones": "tapones",
    "chaleco": "chaleco",
    "guantes": "guantes",
}
CLASE_NEGATIVA: dict[str, str] = {
    "lentes": "sin_lentes",
    "tapones": "sin_tapones",
    "chaleco": "sin_chaleco",
    "guantes": "sin_guantes",
}

# Franjas verticales relativas (y_min_rel, y_max_rel) dentro de la caja de `persona`
ZONA_LENTES: tuple[float, float] = (0.00, 0.32)
ZONA_TAPONES: tuple[float, float] = (0.04, 0.28)
ZONA_CHALECO: tuple[float, float] = (0.16, 0.72)
ZONA_GUANTES: tuple[float, float] = (0.28, 0.96)

ZONAS_ANATOMICAS: dict[str, tuple[float, float]] = {
    "lentes": ZONA_LENTES,
    "tapones": ZONA_TAPONES,
    "chaleco": ZONA_CHALECO,
    "guantes": ZONA_GUANTES,
}

# Extensión horizontal relativa permitida fuera de la caja de persona (ej. brazos extendidos)
MARGEN_X_ZONA: dict[str, float] = {
    "lentes": 0.05,
    "tapones": 0.08,
    "chaleco": 0.08,
    "guantes": 0.18,
}

NOMBRES_PRENDA: dict[str, str] = {
    "lentes": "Lentes de seguridad",
    "tapones": "Tapones auditivos",
    "chaleco": "Chaleco reflejante",
    "guantes": "Guantes anticorte",
}


def prendas_requeridas_por_puesto(puesto: str) -> tuple[str, ...]:
    """Devuelve las prendas obligatorias según el puesto dentro de la fábrica."""
    if puesto.strip() in PUESTOS_GUANTES_OPCIONALES:
        return PRENDAS_GENERALES
    return PRENDAS


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

    @property
    def requiere_guantes(self) -> bool:
        return "guantes" in self.prendas_requeridas

    @property
    def prendas_opcionales(self) -> tuple[str, ...]:
        return tuple(p for p in PRENDAS if p not in self.prendas_requeridas)


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
            if req_str:
                req = tuple(p.strip() for p in req_str.split("|") if p.strip() in PRENDAS)
            else:
                req = prendas_requeridas_por_puesto(puesto)
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
