"""Anotación visual de cuadros, recortes de evidencia y escritura de video H.264."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
import cv2
import numpy as np

from motor import contrato
from motor.asociar import PersonaAsociada

# Colores BGR para las cajas en el video y kiosco
COLOR_OK = (80, 185, 22)        # Verde esmeralda
COLOR_FALTA = (38, 38, 220)     # Rojo alerta
COLOR_DUDOSO = (10, 155, 235)   # Ámbar
COLOR_PERSONA = (180, 160, 20)  # Teal industrial


def dibujar_persona(
    img: np.ndarray,
    persona: PersonaAsociada,
    etiqueta_titulo: str | None = None,
) -> np.ndarray:
    """Dibuja la envolvente del trabajador y el estado de sus 3 zonas anatómicas (lentes, chaleco, guantes)."""
    out = img.copy()
    h, w = out.shape[:2]
    x1, y1, x2, y2 = (int(round(v)) for v in persona.caja)
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w - 1, x2), min(h - 1, y2)

    estados = [persona.prendas[pr].estado for pr in contrato.PRENDAS if pr in persona.prendas]
    if "falta" in estados:
        color_p = COLOR_FALTA
    elif "dudoso" in estados:
        color_p = COLOR_DUDOSO
    else:
        color_p = COLOR_OK

    cv2.rectangle(out, (x1, y1), (x2, y2), color_p, 3)

    # Dibujar las cajas detectadas de cada prenda (o su franja anatómica si falta/dudoso)
    pw = max(1, x2 - x1)
    ph = max(1, y2 - y1)
    for prenda in contrato.PRENDAS:
        ep = persona.prendas.get(prenda)
        if ep is None:
            continue
        c_zona = COLOR_OK if ep.estado == "ok" else COLOR_FALTA if ep.estado == "falta" else COLOR_DUDOSO
        if ep.caja is not None:
            zx1, zy1, zx2, zy2 = (int(round(v)) for v in ep.caja)
        else:
            r_ini, r_fin = contrato.ZONAS_ANATOMICAS[prenda]
            zx1, zy1 = x1 + int(pw * 0.12), y1 + int(ph * r_ini)
            zx2, zy2 = x2 - int(pw * 0.12), y1 + int(ph * r_fin)
        zx1, zy1 = max(0, zx1), max(0, zy1)
        zx2, zy2 = min(w - 1, zx2), min(h - 1, zy2)
        cv2.rectangle(out, (zx1, zy1), (zx2, zy2), c_zona, 2)
        simbolo = "OK" if ep.estado == "ok" else "FALTA" if ep.estado == "falta" else "REVISAR"
        texto_z = f"{prenda.upper()}: {simbolo}"
        _etiqueta_caja(out, texto_z, zx1, max(22, zy1 - 4), c_zona)

    if etiqueta_titulo:
        _etiqueta_caja(out, etiqueta_titulo, x1, max(26, y1 - 8), color_p, escala=0.65)
    return out


def _etiqueta_caja(
    img: np.ndarray,
    texto: str,
    x: int,
    y: int,
    color_fondo: tuple[int, int, int],
    escala: float = 0.52,
):
    fuente = cv2.FONT_HERSHEY_SIMPLEX
    grosor = 2
    (tw, th), baseline = cv2.getTextSize(texto, fuente, escala, grosor)
    y_top = max(0, y - th - 8)
    x_right = min(img.shape[1] - 1, x + tw + 12)
    cv2.rectangle(img, (x, y_top), (x_right, y + baseline), color_fondo, -1)
    cv2.putText(img, texto, (x + 6, y - 4), fuente, escala, (255, 255, 255), grosor, cv2.LINE_AA)


def recortar_persona_y_zona(
    img: np.ndarray,
    persona: PersonaAsociada,
) -> tuple[np.ndarray, np.ndarray]:
    """Devuelve (recorte_persona_anotado, recorte_zona_foco) en formato 16:9 amigable para el tablero."""
    anotada = dibujar_persona(img, persona)
    h, w = img.shape[:2]
    x1, y1, x2, y2 = (int(round(v)) for v in persona.caja)
    pad_x = int((x2 - x1) * 0.25)
    pad_y = int((y2 - y1) * 0.12)
    rx1, ry1 = max(0, x1 - pad_x), max(0, y1 - pad_y)
    rx2, ry2 = min(w, x2 + pad_x), min(h, y2 + pad_y)
    recorte_p = anotada[ry1:ry2, rx1:rx2]
    if recorte_p.size == 0:
        recorte_p = anotada

    # Zona prioritaria: la primera prenda en "falta", o en "dudoso", o el torso
    prenda_foco = "chaleco"
    for pr in contrato.PRENDAS:
        if persona.prendas.get(pr) and persona.prendas[pr].estado == "falta":
            prenda_foco = pr
            break
    else:
        for pr in contrato.PRENDAS:
            if persona.prendas.get(pr) and persona.prendas[pr].estado == "dudoso":
                prenda_foco = pr
                break

    ep = persona.prendas.get(prenda_foco)
    if ep and ep.caja is not None:
        zx1, zy1, zx2, zy2 = (int(round(v)) for v in ep.caja)
    else:
        r_ini, r_fin = contrato.ZONAS_ANATOMICAS[prenda_foco]
        ph = max(1, y2 - y1)
        zx1, zy1 = x1, y1 + int(ph * r_ini)
        zx2, zy2 = x2, y1 + int(ph * r_fin)

    zpad_x = max(40, int((zx2 - zx1) * 0.45))
    zpad_y = max(40, int((zy2 - zy1) * 0.45))
    zx1, zy1 = max(0, zx1 - zpad_x), max(0, zy1 - zpad_y)
    zx2, zy2 = min(w, zx2 + zpad_x), min(h, zy2 + zpad_y)
    recorte_z = anotada[zy1:zy2, zx1:zx2]
    if recorte_z.size == 0:
        recorte_z = recorte_p
    return recorte_p, recorte_z


def recodificar_h264(ruta_mp4: Path):
    """Recodifica con ffmpeg a H.264 (yuv420p, faststart) para reproducción nativa en navegadores."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg or not ruta_mp4.exists():
        return
    tmp = ruta_mp4.with_name(f".{ruta_mp4.stem}.h264.mp4")
    cmd = [
        ffmpeg,
        "-y",
        "-loglevel",
        "error",
        "-i",
        str(ruta_mp4),
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-crf",
        "24",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(tmp),
    ]
    r = subprocess.run(cmd, check=False)
    if r.returncode == 0 and tmp.exists():
        tmp.replace(ruta_mp4)
    else:
        tmp.unlink(missing_ok=True)
