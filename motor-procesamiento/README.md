# Motor de Procesamiento, Entrenamiento Multi-Plugin y Cruce Operativo — Vigía EPP

Este directorio contiene el motor de visión artificial (`motor/`), el pipeline de entrenamiento con las **6 fuentes de datasets de Kaggle y Roboflow Universe** (`entrenamiento/`), el **verificador de porcentaje de exactitud (`entrenamiento/verificar_exactitud.py`)**, el motor de reglas financieras y API HTTP (`cruce/`), y el simulador determinista de turnos (`simulador/`).

## 1. Restricción de Dominio (4 Zonas de EPP + Guantes Opcionales según Puesto)

El modelo `modelos/epp.pt` / `modelos/epp.onnx` (YOLO11n · **9 clases**) y el asociador geométrico `motor/asociar.py` evalúan los **4 componentes de EPP de la planta** (excluyendo casco y mascarilla):

| ID Clase | Nombre Canónico | Zona Anatómica Relativa (`y` dentro de `persona`) | Condición en Planta | Instancias en `datasets/epp` |
|---|---|---|---|---|
| `0` | `persona` | Contenedor base `[0.00, 1.00]` | Trabajador evaluado | `3,699` |
| `1` / `2` | `chaleco` / `sin_chaleco` | Torso `[0.16, 0.72]` | **Obligatorio General** (`US$290/día`) | `487` / `753` |
| `3` / `4` | `lentes` / `sin_lentes` | Ojos / Cabeza `[0.00, 0.32]` | **Obligatorio General** (`US$420/día`) | `1,155` / `251` |
| `5` / `6` | `guantes` / `sin_guantes` | Manos / Muñecas `[0.28, 0.96]` | **Obligatorio en puestos operativos (`US$340/día`) / Opcional en `PUESTOS_GUANTES_OPCIONALES` (`US$0.00`)** | `845` / `3,482` |
| `7` / `8` | `tapones` / `sin_tapones` | Oídos / Cráneo Lateral `[0.04, 0.28]` | **Obligatorio General** (`US$380/día · NOM-011-STPS`) | `794` / `1,523` |

## 2. Datasets Integrados (Dos Opciones de Kaggle + Roboflow Universe · `2,072` imágenes)

1. **`ndomalau/personal-protective-equipment-ppe-dataset`** (Kaggle PPE — 5 clases)
2. **`shlokraval/ppe-dataset-yolov8`** (Roboflow Construction Site Safety v1 — 14 clases)
3. **`slimese/personal-protective-equipment`** (Roboflow Construction Site Safety v4 — 14 clases)
4. **`aiotthien/personal-protection-equipment-datasets`** (Opción 1 Kaggle / Roboflow `ppeee-mnglj/17data` v3 — 17 clases incluyendo `ear-mufs` $\rightarrow$ `7: tapones` y `ear` $\rightarrow$ `8: sin_tapones`)
5. **`tnguynhonh/sh17-yolov8s`** (Opción 2 Kaggle *SH17: Safe Human 17* completo en YOLOv8 — `8,099` imágenes originales con `318` instancias de `ear-mufs` $\rightarrow$ `7: tapones` y `7,730` de `ear` $\rightarrow$ `8: sin_tapones`)
6. **`roboflow/earplugs-universe`** (Proyectos Roboflow Universe: `willy-alcantara/earplugs`, `research-thesis-pjvsz/earplug-t9p19`, `roland-essmann-qlln3/ear-plugs-bzsz9`, `learning-yolov5/earplugs-classification` — clases `earplugs` $\rightarrow$ `7: tapones` y `no_earplugs` $\rightarrow$ `8: sin_tapones`)

## 3. Plugins de IA, Visión y Herramienta de Exactitud

- **Ultralytics (`ultralytics` YOLO11)**: Entrenamiento, validación por clase y exportación a `.pt` y `.onnx`.
- **PyTorch (`torch` CUDA) + OpenCV (`cv2`)**: Aceleración en GPU (`NVIDIA GeForce RTX 4050 Laptop GPU`) y selección de cuadros nítidos por Laplaciano.
- **Supervision (`supervision` de Roboflow) + Roboflow SDK (`roboflow`)**: Conversión `sv.Detections.from_ultralytics`, anotadores `sv.BoxAnnotator` y matriz de confusión `sv.ConfusionMatrix`.
- **Weights & Biases (`wandb`)**: Registro de corridas, hiperparámetros y métricas de exactitud en `runs/wandb/`.
- **ONNX Runtime (`onnxruntime-gpu`) + NVIDIA TensorRT (`TensorrtExecutionProvider`)**: Inferencia acelerada sobre `modelos/epp.onnx`.
- **Herramienta de Verificación de Porcentaje de Exactitud (`entrenamiento/verificar_exactitud.py`)**: Basada en `torchmetrics`, `scikit-learn` y `supervision` para comprobar el porcentaje de exactitud (`exactitud_operativa_turno_pct`, `exactitud_clasificacion_cajas_pct`, `mAP50_deteccion_pct`, `precision_global_pct`, `recall_global_pct`, `f1_score_global_pct` y porcentaje `AP@50 %` de las 9 clases), exportando `modelos/exactitud.json` y `modelos/epp.json`.

## 4. Comandos principales

```bash
# 1. Descargar las 6 fuentes de Kaggle y Roboflow Universe y preparar datasets/epp (9 clases)
./.venv/bin/python -m entrenamiento.descargar_kaggle
./.venv/bin/python -m entrenamiento.preparar_epp

# 2. Entrenar YOLO11n en las 9 clases, exportar ONNX y ejecutar el verificador de exactitud
./.venv/bin/python -m entrenamiento.entrenar_yolo --epocas 15

# 3. Comprobar el porcentaje de exactitud en cualquier momento (TorchMetrics + Supervision + ONNX/TensorRT)
./.venv/bin/python -m entrenamiento.verificar_exactitud

# 4. Ejecutar las pruebas unitarias y de integración (pytest)
./.venv/bin/python -m pytest -v

# 5. Regenerar el turno demostrativo, las 5 tarjetas del Modo Jurado y publicar a Frontend/public/
./.venv/bin/python -m simulador.render_turno
./.venv/bin/python -m motor.pipeline --video video/recorrido_turno.mp4 --turnos datos/sistema/turnos.csv --salida salida
./.venv/bin/python -m cruce.publicar

# 6. Levantar la API HTTP en el puerto 8000
./.venv/bin/python -m cruce.api --puerto 8000
```
