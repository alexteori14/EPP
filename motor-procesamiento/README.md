# Motor de Procesamiento y Cruce Operativo — Vigía EPP

Este directorio contiene el motor de visión artificial (`motor/`), el pipeline de entrenamiento con datasets reales de Kaggle (`entrenamiento/`), el motor de reglas financieras y API HTTP (`cruce/`), y el simulador determinista de turnos (`simulador/`).

## Restricción de Dominio (3 Prendas de EPP)

El modelo `modelos/epp.pt` (YOLO11n) y el asociador geométrico `motor/asociar.py` evalúan exclusivamente las **3 prendas obligatorias de la planta** (excluyendo casco y mascarilla):

| ID Clase | Nombre Canónico | Zona Anatómica Relativa (`y` dentro de `persona`) |
|---|---|---|
| `0` | `persona` | Contenedor base `[0.00, 1.00]` |
| `1` / `2` | `chaleco` / `sin_chaleco` | Torso `[0.16, 0.72]` |
| `3` / `4` | `lentes` / `sin_lentes` | Ojos / Cabeza `[0.00, 0.32]` |
| `5` / `6` | `guantes` / `sin_guantes` | Manos / Muñecas `[0.28, 0.96]` |

## Comandos principales

```bash
# Ejecutar las 18 pruebas unitarias y de integración
./.venv/bin/python -m pytest -v

# Regenerar el turno demostrativo, las 4 tarjetas del Modo Jurado y publicar a Frontend/public/
./.venv/bin/python -m simulador.render_turno --salida .
./.venv/bin/python -m motor.pipeline --video video/recorrido_turno.mp4 --escena escena/escena.json --salida salida
./.venv/bin/python -m simulador.tarjetas
./.venv/bin/python -m cruce.publicar

# Evaluar precisión del motor contra la verdad de escena.json
./.venv/bin/python -m herramientas.evaluar_motor

# Levantar la API HTTP en el puerto 8000
./.venv/bin/python -m cruce.api --puerto 8000
```
