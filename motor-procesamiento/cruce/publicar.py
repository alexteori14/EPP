"""Publica los artefactos del motor y del cruce hacia Frontend/public/."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from cruce import hallazgos, red


def publicar(
    dir_salida: Path = Path("salida"),
    dir_tarjetas: Path = Path("salida_tarjetas"),
    dir_sistema: Path = Path("datos/sistema"),
    dir_web: Path = Path("../Frontend/public"),
):
    sistema = hallazgos.leer_sistema(dir_sistema)
    d_pub_sal = dir_web / "salida"
    d_pub_sal.mkdir(parents=True, exist_ok=True)

    # 1. Recorrido principal
    datos_h = hallazgos.desde_carpeta(
        dir_salida,
        sistema,
        prefijo="/salida",
        video_url="/salida/recorrido_anotado.mp4",
    )
    (dir_salida / "hallazgos.json").write_text(
        json.dumps(datos_h, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (d_pub_sal / "hallazgos.json").write_text(
        json.dumps(datos_h, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if (dir_salida / "recorrido_anotado.mp4").exists():
        shutil.copy2(dir_salida / "recorrido_anotado.mp4", d_pub_sal / "recorrido_anotado.mp4")
    if (dir_salida / "recortes").exists():
        shutil.copytree(dir_salida / "recortes", d_pub_sal / "recortes", dirs_exist_ok=True)

    # 2. Impacto en red
    datos_red = red.construir(datos_h)
    (dir_web / "red.json").write_text(
        json.dumps(datos_red, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 3. Tarjetas de ensayo del Modo Jurado
    if dir_tarjetas.exists():
        d_ensayos = dir_web / "ensayos"
        d_ensayos.mkdir(parents=True, exist_ok=True)
        for sub in sorted(p for p in dir_tarjetas.iterdir() if p.is_dir()):
            if not (sub / "observaciones.json").exists():
                continue
            pref = f"/ensayos/{sub.name}"
            res_t = hallazgos.desde_carpeta(sub, sistema, prefijo=pref)
            nuevos_t = hallazgos.nuevos(datos_h, res_t)
            d_dest = d_ensayos / sub.name
            d_dest.mkdir(parents=True, exist_ok=True)
            if (sub / "recortes").exists():
                shutil.copytree(sub / "recortes", d_dest / "recortes", dirs_exist_ok=True)
            ensayo_payload = {
                "status": "completado",
                "completado": True,
                "tarjeta": sub.name,
                "segundos_proceso": res_t["resumen"]["segundos_proceso"],
                "hallazgo_nuevo": nuevos_t[0] if nuevos_t else None,
                "hallazgos_nuevos": nuevos_t,
            }
            (d_dest / "resultado.json").write_text(
                json.dumps(ensayo_payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )
    print(f"Publicado en {dir_web.resolve()}: {datos_h['resumen']['frase']}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Publica salida/ y red.json hacia Frontend/public")
    ap.add_argument("--salida", default="salida")
    ap.add_argument("--tarjetas", default="salida_tarjetas")
    ap.add_argument("--sistema", default="datos/sistema")
    ap.add_argument("--web", default="../Frontend/public")
    args = ap.parse_args(argv)
    publicar(Path(args.salida), Path(args.tarjetas), Path(args.sistema), Path(args.web))


if __name__ == "__main__":
    main()
