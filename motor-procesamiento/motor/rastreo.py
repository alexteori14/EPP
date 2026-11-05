"""Seguimiento de trabajadores entre cuadros y votación multi-cuadro por prenda."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from motor import contrato
from motor.asociar import PersonaAsociada


def _iou(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    x1 = max(a[0], b[0])
    y1 = max(a[1], b[1])
    x2 = min(a[2], b[2])
    y2 = min(a[3], b[3])
    inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    if inter <= 0:
        return 0.0
    area_a = max(0.0, a[2] - a[0]) * max(0.0, a[3] - a[1])
    area_b = max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


@dataclass
class PistaTrabajador:
    id_pista: int
    primer_cuadro: int
    ultimo_cuadro: int
    ultima_caja: tuple[float, float, float, float]
    vistas: list[PersonaAsociada] = field(default_factory=list)


class RastreadorTurno:
    """Agrupa las vistas de cada trabajador a lo largo de los cuadros del video."""

    def __init__(self, iou_minimo: float = 0.25, max_brecha_cuadros: int = 36):
        self.iou_minimo = iou_minimo
        self.max_brecha_cuadros = max_brecha_cuadros
        self._pistas: list[PistaTrabajador] = []
        self._sig_id = 1

    def actualizar(self, personas: list[PersonaAsociada], cuadro: int):
        usadas: set[int] = set()
        for p in personas:
            mejor_pista: PistaTrabajador | None = None
            mejor_iou = self.iou_minimo
            for pista in self._pistas:
                if pista.id_pista in usadas:
                    continue
                if cuadro - pista.ultimo_cuadro > self.max_brecha_cuadros:
                    continue
                sim = _iou(p.caja, pista.ultima_caja)
                if sim >= mejor_iou:
                    mejor_iou = sim
                    mejor_pista = pista
            if mejor_pista is not None:
                mejor_pista.ultimo_cuadro = cuadro
                mejor_pista.ultima_caja = p.caja
                mejor_pista.vistas.append(p)
                usadas.add(mejor_pista.id_pista)
            else:
                nueva = PistaTrabajador(
                    id_pista=self._sig_id,
                    primer_cuadro=cuadro,
                    ultimo_cuadro=cuadro,
                    ultima_caja=p.caja,
                    vistas=[p],
                )
                self._sig_id += 1
                self._pistas.append(nueva)
                usadas.add(nueva.id_pista)

    def pistas_ordenadas(self) -> list[PistaTrabajador]:
        """Devuelve las pistas en orden de aparición temporal y espacial."""
        return sorted(self._pistas, key=lambda t: (t.primer_cuadro, t.ultima_caja[0]))


def votar_trabajador(vistas: list[PersonaAsociada]) -> dict:
    """Vota el estado de cada una de las 3 prendas (`lentes`, `chaleco`, `guantes`) entre varios cuadros."""
    if not vistas:
        return {
            "persona_detectada": False,
            "confianza_persona": 0.0,
            "cuadro": None,
            "prendas": {
                pr: {"estado": "dudoso", "confianza": 0.0, "lecturas": 0}
                for pr in contrato.PRENDAS
            },
        }

    mejor_vista = max(vistas, key=lambda v: v.confianza)
    prendas_votadas: dict[str, dict] = {}

    for prenda in contrato.PRENDAS:
        pesos: dict[str, float] = defaultdict(float)
        conteos: dict[str, int] = defaultdict(int)
        confs: dict[str, list[float]] = defaultdict(list)

        for v in vistas:
            ep = v.prendas.get(prenda)
            if ep is None:
                continue
            peso = max(0.2, ep.confianza) if ep.estado in ("ok", "falta") else 0.15
            pesos[ep.estado] += peso
            conteos[ep.estado] += 1
            confs[ep.estado].append(ep.confianza)

        # Priorizar votos definitivos (ok / falta) sobre dudoso si hay lecturas claras
        peso_ok = pesos.get("ok", 0.0)
        peso_falta = pesos.get("falta", 0.0)

        if peso_ok == 0.0 and peso_falta == 0.0:
            ganador = "dudoso"
            conf_media = round(sum(confs["dudoso"]) / max(1, len(confs["dudoso"])), 3)
            n_lecturas = conteos["dudoso"]
        elif abs(peso_ok - peso_falta) < 0.15 and peso_ok > 0 and peso_falta > 0:
            ganador = "dudoso"
            todas = confs["ok"] + confs["falta"]
            conf_media = round(sum(todas) / max(1, len(todas)), 3)
            n_lecturas = len(todas)
        elif peso_ok >= peso_falta:
            ganador = "ok"
            conf_media = round(sum(confs["ok"]) / max(1, len(confs["ok"])), 3)
            n_lecturas = conteos["ok"]
            if conf_media < 0.55:
                ganador = "dudoso"
        else:
            ganador = "falta"
            conf_media = round(sum(confs["falta"]) / max(1, len(confs["falta"])), 3)
            n_lecturas = conteos["falta"]
            if conf_media < 0.55:
                ganador = "dudoso"

        prendas_votadas[prenda] = {
            "estado": ganador,
            "confianza": conf_media,
            "lecturas": n_lecturas,
        }

    return {
        "persona_detectada": True,
        "confianza_persona": round(sum(v.confianza for v in vistas) / len(vistas), 3),
        "cuadro": mejor_vista.cuadro,
        "mejor_vista": mejor_vista,
        "prendas": prendas_votadas,
    }
