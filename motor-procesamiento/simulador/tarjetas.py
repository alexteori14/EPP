"""Genera los 4 videos cortos y salidas de ensayo del Modo Jurado (video/tarjetas/<tarjeta>.mp4)."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import cv2

from motor import anotar, contrato
from simulador.datos_prueba import TARJETAS_JURADO, generar_escena
from simulador.render_turno import _buscar_imagenes_kaggle, _construir_frame_estacion


def generar_tarjetas(dir_raiz: Path = Path(".")):
    escena = generar_escena(dir_raiz)
    base_obs_path = dir_raiz / "salida" / "observaciones.json"
    if not base_obs_path.exists():
        from simulador.render_turno import renderizar_todo
        renderizar_todo(dir_raiz)
    base_obs = json.loads(base_obs_path.read_text(encoding="utf-8"))
    candidatos = _buscar_imagenes_kaggle(dir_raiz / "datasets/epp")

    d_tarjetas_vid = dir_raiz / "video" / "tarjetas"
    d_tarjetas_vid.mkdir(parents=True, exist_ok=True)

    for idx_t, (nombre_t, spec) in enumerate(TARJETAS_JURADO.items()):
        pos_id = spec["posicion"]
        pos_escena = next(p for p in escena["posiciones"] if p["posicion"] == pos_id)
        modificada = copy.deepcopy(pos_escena)
        modificada["prendas"] = dict(spec["cambio"])

        img_k = None
        if candidatos:
            img_path, _, _ = candidatos[(idx_t + 3) % len(candidatos)]
            img_k = cv2.imread(str(img_path))

        cuadro_base, pers = _construir_frame_estacion(modificada, img_k, 1280, 720)
        ruta_vid = d_tarjetas_vid / f"{nombre_t}.mp4"
        writer = cv2.VideoWriter(str(ruta_vid), cv2.VideoWriter_fourcc(*"mp4v"), 24.0, (1280, 720))
        for _ in range(24):
            writer.write(cuadro_base)
        writer.release()
        anotar.recodificar_h264(ruta_vid)

        d_sal_t = dir_raiz / "salida_tarjetas" / nombre_t
        d_rec_t = d_sal_t / "recortes"
        d_rec_t.mkdir(parents=True, exist_ok=True)
        rec_p, rec_z = anotar.recortar_persona_y_zona(cuadro_base, pers)
        cv2.imwrite(str(d_rec_t / f"{pos_id}.jpg"), rec_p, [cv2.IMWRITE_JPEG_QUALITY, 90])
        cv2.imwrite(str(d_rec_t / f"{pos_id}_zona.jpg"), rec_z, [cv2.IMWRITE_JPEG_QUALITY, 92])

        obs_t = copy.deepcopy(base_obs)
        obs_t["video"] = f"{nombre_t}.mp4"
        obs_t["segundos_proceso"] = 3.2
        for p_entry in obs_t["posiciones"]:
            if p_entry["posicion"] == pos_id:
                for pr in contrato.PRENDAS:
                    est = spec["cambio"][pr]
                    p_entry["prendas"][pr] = {
                        "estado": est,
                        "confianza": 0.93 if est == "ok" else 0.90,
                        "lecturas": 5,
                    }
        (d_sal_t / "observaciones.json").write_text(
            json.dumps(obs_t, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (d_sal_t / "diagnostico.json").write_text(
            json.dumps({"video": {"fps": 24.0, "cuadros": 24, "resolucion": [1280, 720]}}, indent=2),
            encoding="utf-8",
        )
    print(f"Generadas {len(TARJETAS_JURADO)} tarjetas del Modo Jurado en video/tarjetas/ y salida_tarjetas/.")


if __name__ == "__main__":
    generar_tarjetas()
