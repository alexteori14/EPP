"""Evalúa salida/observaciones.json contra la verdad de escena/escena.json."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from motor import contrato


def evaluar(ruta_obs: str | Path, ruta_escena: str | Path) -> dict:
    obs = json.loads(Path(ruta_obs).read_text(encoding="utf-8"))
    esc = json.loads(Path(ruta_escena).read_text(encoding="utf-8"))
    verdad = {p["posicion"]: p["prendas"] for p in esc["posiciones"]}

    total_pos = 0
    pos_exactas = 0
    aciertos_prenda = {pr: 0 for pr in contrato.PRENDAS}
    falsos_positivos = 0

    for p_obs in obs["posiciones"]:
        pos = p_obs["posicion"]
        if pos not in verdad:
            continue
        total_pos += 1
        v_prendas = verdad[pos]
        todas_ok = True
        for pr in contrato.PRENDAS:
            est_obs = p_obs["prendas"][pr]["estado"]
            est_ver = v_prendas[pr]
            if est_obs == est_ver:
                aciertos_prenda[pr] += 1
            else:
                todas_ok = False
                if est_obs == "falta" and est_ver == "ok":
                    falsos_positivos += 1
        if todas_ok:
            pos_exactas += 1

    n = max(1, total_pos)
    return {
        "trabajadores_evaluados": total_pos,
        "trabajadores_exactos_pct": round(100.0 * pos_exactas / n, 1),
        "precision_por_prenda_pct": {
            pr: round(100.0 * aciertos_prenda[pr] / n, 1) for pr in contrato.PRENDAS
        },
        "falsos_positivos": falsos_positivos,
        "segundos_proceso": obs.get("segundos_proceso", 0.0),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Evalúa observaciones.json contra escena.json")
    ap.add_argument("--observaciones", default="salida/observaciones.json")
    ap.add_argument("--escena", default="escena/escena.json")
    args = ap.parse_args(argv)
    m = evaluar(args.observaciones, args.escena)
    print(json.dumps(m, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
