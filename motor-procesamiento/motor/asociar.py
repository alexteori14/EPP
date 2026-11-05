"""Asociación espacial anatómica Persona ↔ {Lentes, Chaleco, Guantes}."""
from __future__ import annotations

from dataclasses import dataclass, field
from motor import contrato

CONFIANZA_MINIMA_PRENDA = 0.55
UMBRAL_CONFLICTO_DUDA = 0.15


@dataclass(frozen=True)
class Deteccion:
    clase: str
    confianza: float
    caja: tuple[float, float, float, float]  # (x1, y1, x2, y2)


@dataclass(frozen=True)
class EstadoPrenda:
    estado: str  # "ok" | "falta" | "dudoso"
    confianza: float
    caja: tuple[float, float, float, float] | None = None


@dataclass
class PersonaAsociada:
    caja: tuple[float, float, float, float]
    confianza: float
    prendas: dict[str, EstadoPrenda] = field(default_factory=dict)
    cuadro: int = 0


def _area(c: tuple[float, float, float, float]) -> float:
    return max(0.0, c[2] - c[0]) * max(0.0, c[3] - c[1])


def _interseccion(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    x1 = max(a[0], b[0])
    y1 = max(a[1], b[1])
    x2 = min(a[2], b[2])
    y2 = min(a[3], b[3])
    return max(0.0, x2 - x1) * max(0.0, y2 - y1)


def _fraccion_en_zona(
    caja_prenda: tuple[float, float, float, float],
    caja_persona: tuple[float, float, float, float],
    prenda: str,
) -> float:
    """Fracción del área de la prenda que cae dentro de la ventana anatómica de la persona."""
    px1, py1, px2, py2 = caja_persona
    pw = max(1.0, px2 - px1)
    ph = max(1.0, py2 - py1)
    y_ini_rel, y_fin_rel = contrato.ZONAS_ANATOMICAS[prenda]
    margen_x = contrato.MARGEN_X_ZONA[prenda]
    ventana = (
        px1 - pw * margen_x,
        py1 + ph * y_ini_rel,
        px2 + pw * margen_x,
        py1 + ph * y_fin_rel,
    )
    area_p = _area(caja_prenda)
    if area_p <= 0:
        return 0.0
    return _interseccion(caja_prenda, ventana) / area_p


def _zona_cortada_en_borde(
    caja_persona: tuple[float, float, float, float],
    prenda: str,
    ancho: int,
    alto: int,
) -> bool:
    """Detecta si la zona anatómica de la persona está cortada por el borde de la imagen."""
    px1, py1, px2, py2 = caja_persona
    if prenda == "lentes" and py1 <= alto * 0.02:
        return True
    if prenda == "guantes" and (py2 >= alto * 0.98 or px1 <= ancho * 0.01 or px2 >= ancho * 0.99):
        return True
    if prenda == "chaleco" and py2 <= alto * 0.25:
        return True
    return False


def asociar_cuadro(
    detecciones: list[Deteccion],
    ancho: int,
    alto: int,
    cuadro: int = 0,
) -> list[PersonaAsociada]:
    """Asocia cada detección de EPP (lentes, chaleco, guantes y sus negativos) a cada persona."""
    personas_raw = [d for d in detecciones if d.clase == "persona"]
    objetos_epp = [d for d in detecciones if d.clase != "persona"]

    # Si no se detectó la caja 'persona' pero sí objetos de EPP en un recorte cercano, sintetizar envolvente
    if not personas_raw and objetos_epp:
        x1 = max(0.0, min(d.caja[0] for d in objetos_epp) - ancho * 0.1)
        y1 = max(0.0, min(d.caja[1] for d in objetos_epp) - alto * 0.08)
        x2 = min(float(ancho), max(d.caja[2] for d in objetos_epp) + ancho * 0.1)
        y2 = min(float(alto), max(d.caja[3] for d in objetos_epp) + alto * 0.15)
        personas_raw = [Deteccion("persona", 0.75, (x1, y1, x2, y2))]

    # Ordenar personas de izquierda a derecha
    personas_raw.sort(key=lambda d: (d.caja[0] + d.caja[2]) / 2.0)

    salida: list[PersonaAsociada] = []
    for p_det in personas_raw:
        prendas_estado: dict[str, EstadoPrenda] = {}
        for prenda in contrato.PRENDAS:
            c_pos = contrato.CLASE_POSITIVA[prenda]
            c_neg = contrato.CLASE_NEGATIVA[prenda]

            mejores_pos: list[tuple[float, Deteccion]] = []
            mejores_neg: list[tuple[float, Deteccion]] = []

            for obj in objetos_epp:
                if obj.clase not in (c_pos, c_neg):
                    continue
                solape = _fraccion_en_zona(obj.caja, p_det.caja, prenda)
                if solape < 0.25:
                    continue
                puntaje = obj.confianza * (0.5 + 0.5 * min(1.0, solape))
                if obj.clase == c_pos:
                    mejores_pos.append((puntaje, obj))
                else:
                    mejores_neg.append((puntaje, obj))

            mejor_pos = max(mejores_pos, key=lambda x: x[0])[1] if mejores_pos else None
            mejor_neg = max(mejores_neg, key=lambda x: x[0])[1] if mejores_neg else None

            if mejor_pos and mejor_neg:
                # Review Focus #2: si hay conflicto cercano entre positivo y negativo -> dudoso
                if abs(mejor_pos.confianza - mejor_neg.confianza) < UMBRAL_CONFLICTO_DUDA:
                    prendas_estado[prenda] = EstadoPrenda(
                        estado="dudoso",
                        confianza=round(max(mejor_pos.confianza, mejor_neg.confianza), 3),
                        caja=mejor_pos.caja,
                    )
                elif mejor_pos.confianza > mejor_neg.confianza:
                    est = "ok" if mejor_pos.confianza >= CONFIANZA_MINIMA_PRENDA else "dudoso"
                    prendas_estado[prenda] = EstadoPrenda(est, round(mejor_pos.confianza, 3), mejor_pos.caja)
                else:
                    est = "falta" if mejor_neg.confianza >= CONFIANZA_MINIMA_PRENDA else "dudoso"
                    prendas_estado[prenda] = EstadoPrenda(est, round(mejor_neg.confianza, 3), mejor_neg.caja)
            elif mejor_pos:
                est = "ok" if mejor_pos.confianza >= CONFIANZA_MINIMA_PRENDA else "dudoso"
                prendas_estado[prenda] = EstadoPrenda(est, round(mejor_pos.confianza, 3), mejor_pos.caja)
            elif mejor_neg:
                est = "falta" if mejor_neg.confianza >= CONFIANZA_MINIMA_PRENDA else "dudoso"
                prendas_estado[prenda] = EstadoPrenda(est, round(mejor_neg.confianza, 3), mejor_neg.caja)
            else:
                # Review Focus #1: si la zona está cortada en el borde de la imagen -> dudoso
                if _zona_cortada_en_borde(p_det.caja, prenda, ancho, alto):
                    prendas_estado[prenda] = EstadoPrenda("dudoso", 0.0, None)
                else:
                    # Zona visible dentro del cuadro pero sin detección segura -> dudoso
                    prendas_estado[prenda] = EstadoPrenda("dudoso", 0.35, None)

        salida.append(
            PersonaAsociada(
                caja=p_det.caja,
                confianza=round(p_det.confianza, 3),
                prendas=prendas_estado,
                cuadro=cuadro,
            )
        )
    return salida
