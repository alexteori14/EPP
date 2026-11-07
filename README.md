# Vigía EPP · Inspección Pre-Turno de Equipo de Protección Personal (Consola SCADA/HMI · v2.5 Multi-Plugin)

**Vigía EPP** es una plataforma industrial de visión por computadora y auditoría operativa que verifica que cada trabajador porte su **Equipo de Protección Personal (EPP) obligatorio completo** antes de iniciar su turno en planta.

> **Regla de Dominio de Planta (4 Zonas Anatómicas + Guantes Condicionales por Puesto):** En esta instalación industrial **no se exige casco ni mascarilla**. El sistema inspecciona **4 componentes de EPP** mediante un detector **YOLO11 de 9 clases** entrenado con **6 fuentes de Kaggle y Roboflow Universe (`2,072` imágenes)**:
> 1. **Lentes de seguridad ANSI Z87.1** (`lentes` / `sin_lentes`) — Zona Ojos/Rostro (`y ∈ [0.00, 0.32]`) · **Obligatorio General** (`US$420.00/día`)
> 2. **Tapones auditivos de inserción NRR 32 dB NOM-011-STPS** (`tapones` / `sin_tapones`) — Zona Oídos/Cráneo Lateral (`y ∈ [0.04, 0.28]`) · **Obligatorio General** (`US$380.00/día`)
> 3. **Chaleco reflejante Clase 2** (`chaleco` / `sin_chaleco`) — Zona Torso (`y ∈ [0.16, 0.72]`) · **Obligatorio General** (`US$290.00/día`)
> 4. **Guantes anticorte Nivel A4** (`guantes` / `sin_guantes`) — Zona Manos/Muñecas (`y ∈ [0.28, 0.96]`) · **Obligatorio en puestos operativos (`US$340.00/día`) / Opcional en puestos de supervisión, inspección, almacén y montacargas (`US$0.00`, acceso autorizado)**

---

## Arranque rápido (1 comando)

```bash
./iniciar.sh
```

Esto levanta automáticamente:
- **API del Motor y Cruce Operativo** en `http://127.0.0.1:8000` (`cruce.api`)
- **Consola SCADA Next.js 15 (Opción 1)** en `http://localhost:3000` (`Frontend/`)

---

## Datasets Integrados (Kaggle + Roboflow Universe · 9 Clases)

El pipeline ([`entrenamiento/descargar_kaggle.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/entrenamiento/descargar_kaggle.py) y [`entrenamiento/preparar_epp.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/entrenamiento/preparar_epp.py)) integra y deduplica **6 fuentes reales (`1,518` train · `369` val · `185` test = `2,072` imágenes)** cubriendo las 9 clases (`persona`, `chaleco`, `sin_chaleco`, `lentes`, `sin_lentes`, `guantes`, `sin_guantes`, `tapones`, `sin_tapones`):
1. **`ndomalau/personal-protective-equipment-ppe-dataset`** (Kaggle PPE — `298` imágenes)
2. **`shlokraval/ppe-dataset-yolov8`** (Roboflow *Construction Site Safety* v1 — `300` imágenes)
3. **`slimese/personal-protective-equipment`** (Roboflow *Construction Site Safety* v4 — `299` imágenes)
4. **`aiotthien/personal-protection-equipment-datasets`** (Opción 1 Kaggle / Roboflow `ppeee-mnglj/17data` v3 — `435` imágenes con `ear-mufs` $\rightarrow$ `7: tapones` y `ear` $\rightarrow$ `8: sin_tapones`)
5. **`tnguynhonh/sh17-yolov8s`** (Opción 2 Kaggle *SH17: Safe Human 17* YOLOv8 — `435` imágenes priorizando las `318` instancias de `ear-mufs` $\rightarrow$ `7: tapones` y `ear` $\rightarrow$ `8: sin_tapones`)
6. **`roboflow/earplugs-universe`** (Roboflow Universe: `willy-alcantara/earplugs`, `research-thesis-pjvsz/earplug-t9p19`, `roland-essmann-qlln3/ear-plugs-bzsz9`, `learning-yolov5/earplugs-classification` — `305` imágenes enfocadas en tapones auditivos `earplugs` $\rightarrow$ `7: tapones` y `no_earplugs` $\rightarrow$ `8: sin_tapones`)

---

## Plugins de IA/Visión, Herramienta de Exactitud, Skills y Tools del Proyecto

### 1. Plugins de Visión por Computadora, Telemetría y Aceleración GPU
- **Ultralytics (`ultralytics 8.4.202` — YOLO11):** Entrenamiento y detección de 9 clases (`modelos/epp.pt`) y exportación a ONNX (`modelos/epp.onnx`).
- **PyTorch (`torch 2.15.0+cu132`) + OpenCV (`opencv-contrib-python`):** Aceleración en GPU (`NVIDIA GeForce RTX 4050 Laptop GPU`) y selección de cuadros nítidos por varianza del Laplaciano.
- **Supervision (`supervision 0.31.5` de Roboflow) + Roboflow SDK (`roboflow 1.7.3`):** Conversión estandarizada `sv.Detections.from_ultralytics`, anotadores `sv.BoxAnnotator` y matrices de confusión `sv.ConfusionMatrix`.
- **Weights & Biases (`wandb 0.31.0`):** Registro de hiperparámetros, curvas de entrenamiento y métricas de exactitud en `motor-procesamiento/runs/wandb/`.
- **NVIDIA TensorRT (`TensorrtExecutionProvider`) + ONNX Runtime (`onnxruntime-gpu 1.31.1` + `onnx 1.23.2` + `onnxslim`):** Aceleración de inferencia en GPU alcanzando **`3.76 ms` por imagen (`266.1 FPS`)** en ONNX Runtime CUDA frente a **`4.29 ms` (`233.2 FPS`)** en PyTorch CUDA.

### 2. Herramienta de Verificación de Porcentaje de Exactitud ([`entrenamiento/verificar_exactitud.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/entrenamiento/verificar_exactitud.py))
Construida con **`TorchMetrics` (`1.9.0`)**, **`Supervision` (`0.31.5`)**, **`scikit-learn` (`1.9.1`)** y **`Ultralytics`**, comprueba y exporta en [`modelos/exactitud.json`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/modelos/exactitud.json) y [`modelos/epp.json`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/modelos/epp.json) los porcentajes reales del modelo:
- **Exactitud Operativa en Turno (12 estaciones · 4 zonas):** **`100.00 %`** (`0` falsos positivos)
- **Exactitud Clasificatoria en Cajas Emparejadas (`TorchMetrics` / `scikit-learn`):** **`97.15 %`** (`F1 ponderado: 97.13 %`)
- **Precisión Global de Detección (`Precision`):** **`71.08 %`**
- **Exactitud Media de Detección 9 Clases (`mAP@50`):** **`65.67 %`** (`persona: 92.62 %`, `chaleco: 81.70 %`, **`tapones: 77.46 %`**, `sin_chaleco: 69.76 %`, `sin_guantes: 67.54 %`, **`sin_tapones: 58.12 %`**, `lentes: 57.03 %`, `sin_lentes: 50.12 %`, `guantes: 36.68 %`)

### 3. Skills, Tools y Plugins de Ingeniería Utilizados
- **Skills activadas:** `brainstorming`, `writing-plans`, `test-driven-development`, `executing-plans`, `verification-before-completion`, `ui-ux-pro-max`, `design-system`, `ui-styling`, `modern-web-guidance`, `a11y-debugging`, `chrome-devtools`, `uv`.
- **Tools y Plugins de Entorno:** `Kaggle MCP / HTTP Range ZIP Streamer`, `Playwright CLI` (`Frontend/tests/e2e.mjs`), `OpenSpec` (`@fission-ai/openspec`), `Superpowers Plugin`, `Framer Motion`, `Headroom AI`, `uv` package manager, `Next.js 15 + React 19 + Tailwind CSS`.

---

## Estructura del repositorio

```text
EPP/
├── iniciar.sh                        # Lanzador unificado (:8000 API + :3000 Next.js)
├── documentacion.md                  # Documentación técnica exhaustiva del proyecto
├── memoria.md                        # Memoria técnica compacta para agentes de IA futuros
├── PITCH.md                          # Guion ejecutivo de demostración (5 minutos)
├── motor-procesamiento/              # Motor de visión YOLO11, plugins, cruce financiero y API HTTP
│   ├── CONTRATO.md                   # Contrato estricto de JSONs entre motor, cruce y web
│   ├── modelos/epp.pt                # Modelo YOLO11 entrenado (9 clases · PyTorch CUDA)
│   ├── modelos/epp.onnx              # Modelo exportado y optimizado para ONNX Runtime / TensorRT
│   ├── modelos/epp.json              # Métricas reales de validación en las 9 clases
│   ├── modelos/exactitud.json        # Reporte completo de porcentajes de exactitud y benchmark GPU
│   ├── entrenamiento/                # Descarga Kaggle+Roboflow, armonización 9 clases, YOLO11 y verificar_exactitud.py
│   ├── motor/                        # Selección de cuadros, detector multi-plugin, asociación 4 zonas, rastreo, kiosco
│   ├── cruce/                        # Reglas de riesgo, impacto en red (18 plantas), RAG y API :8000
│   ├── simulador/                    # Generador de turno de 12 estaciones y 5 tarjetas de Modo Jurado
│   └── tests/                        # 21 pruebas unitarias y de integración (pytest)
└── Frontend/                         # Consola SCADA/HMI Next.js 15 + React 19 + Tailwind CSS (Opción 1)
    ├── DISENO.md                     # Sistema de diseño "Centro de Comando Industrial SCADA/HMI"
    ├── app/                          # 8 rutas dinámicas (/resumen, /kiosco, /recorrido, /cuadrilla, ...)
    ├── components/                   # Vistas SCADA, Gemelo Anatómico SVG de 4 zonas y gráficas
    └── tests/e2e.mjs                 # Suite E2E de Playwright que verifica las 8 pantallas
```

---

## Pruebas automatizadas y Verificación de Exactitud

```bash
# 1. Comprobar el porcentaje de exactitud del modelo y motor (TorchMetrics + Supervision + ONNX Runtime)
cd motor-procesamiento && ./.venv/bin/python -m entrenamiento.verificar_exactitud --no-exportar

# 2. Suite de pruebas del motor, plugins y cruce (21 tests)
motor-procesamiento/.venv/bin/python -m pytest -v

# 3. Verificación de tipos y compilación de producción del Frontend
npm --prefix Frontend run build
```
