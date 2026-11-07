# Memoria Técnica de Contexto Rápido para IA — Vigía EPP (`memoria.md` · v2.5)

> **Propósito:** Este documento está diseñado específicamente para que tú (u otra IA en sesiones futuras) recuperes el **100 % del contexto arquitectónico, contratos, funciones, rutas, constantes, reglas de negocio, datasets de Kaggle/Roboflow, plugins y métricas de exactitud** de **Vigía EPP (v2.5)** en una sola lectura, sin gastar tokens abriendo docenas de archivos.

---

## 1. Invariantes Críticas del Dominio (NUNCA ROMPER)

1. **EXCLUSIÓN ABSOLUTA DE CASCO Y MASCARILLA + 4 EQUIPOS EVALUADOS (`PRENDAS`):**
   - En la planta donde opera el software **NO se pide casco (`casco`) ni mascarilla (`mascarilla`)**.
   - Se evalúan **4 componentes de EPP** (`motor.contrato.PRENDAS = ("lentes", "tapones", "chaleco", "guantes")`):
     - **Obligatorios generales para TODOS los puestos (`PRENDAS_GENERALES = ("lentes", "tapones", "chaleco")`):**
       - `"lentes"` (*Lentes Policarbonato Anti-Impacto ANSI Z87.1*, `NOM-017-STPS`) $\rightarrow$ Riesgo diario: **`US$420.00/día`** · Stock en caseta: **`18`** · Costo unitario: `US$14.50` · Paro: **`US$950.00`**
       - `"tapones"` (*Tapones Auditivos de Inserción NRR 32 dB*, `NOM-011-STPS`, para evitar daño auditivo por ruido industrial $>85\text{ dB(A)}$; la nave opera a `94.2 dB(A)`) $\rightarrow$ Riesgo diario: **`US$380.00/día`** · Stock en caseta: **`40`** · Costo unitario: `US$6.50` · Paro: **`US$890.00`**
       - `"chaleco"` (*Chaleco Reflejante Clase 2 Alta Visibilidad*, `NOM-006-STPS`) $\rightarrow$ Riesgo diario: **`US$290.00/día`** · Stock en caseta: **`12`** · Costo unitario: `US$18.00` · Paro: **`US$820.00`**
     - **Condicional / Opcional según el puesto (`PRENDAS_OPCIONALES_POR_PUESTO = ("guantes",)`):**
       - `"guantes"` (*Guantes Nitrilo Anticorte Nivel A4*, `NOM-017-STPS`) $\rightarrow$ Riesgo diario: **`US$340.00/día`** · Stock en caseta: **`24`** · Costo unitario: `US$16.00` · Paro: **`US$880.00`** **SOLO cuando el puesto lo exige** (`requiere_guantes = True`).
       - En puestos incluidos en `PUESTOS_GUANTES_OPCIONALES` (*Operador de Montacargas*, *Supervisor de Patio*, *Almacenista de Acero*, *Inspector de Calidad*, *Coordinador de Logística*), `prendas_requeridas = ("lentes", "tapones", "chaleco")` (`requiere_guantes = False`). Si el trabajador no lleva guantes pero porta sus 3 equipos obligatorios, **su acceso es AUTORIZADO con `US$0.00` de riesgo** y la UI muestra el badge cian `GUANTES OPCIONALES (PUESTO)`.

2. **ESQUEMA CANÓNICO DE 9 CLASES YOLO11 (`motor.contrato.CLASES`):**
   - `0: "persona"` (`3,699` instancias · `AP@50: 92.62 %`)
   - `1: "chaleco"` (`487` instancias · `AP@50: 81.70 %`)
   - `2: "sin_chaleco"` (`753` instancias · `AP@50: 69.76 %`)
   - `3: "lentes"` (`1,155` instancias · `AP@50: 57.03 %`)
   - `4: "sin_lentes"` (`251` instancias · `AP@50: 50.12 %`)
   - `5: "guantes"` (`845` instancias · `AP@50: 36.68 %`)
   - `6: "sin_guantes"` (`3,482` instancias · `AP@50: 67.54 %`)
   - `7: "tapones"` (`794` instancias · **`AP@50: 77.46 %`**)
   - `8: "sin_tapones"` (`1,523` instancias · **`AP@50: 58.12 %`**)

3. **6 FUENTES DE DATASETS INTEGRADAS (2 OPCIONES KAGGLE + ROBOFLOW UNIVERSE = `2,072` IMÁGENES):**
   - [`entrenamiento/descargar_kaggle.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/entrenamiento/descargar_kaggle.py) y [`entrenamiento/preparar_epp.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/entrenamiento/preparar_epp.py) integran y deduplican (por clave raíz `.rf.<hash>` y hash `SHA-1`) **6 fuentes** en `motor-procesamiento/datasets/epp/` (`1,518` train · `369` val · `185` test):
     1. `ndomalau/personal-protective-equipment-ppe-dataset` (`298` imágenes — Kaggle PPE)
     2. `shlokraval/ppe-dataset-yolov8` (`300` imágenes — Roboflow Construction Site Safety v1)
     3. `slimese/personal-protective-equipment` (`299` imágenes — Roboflow Construction Site Safety v4)
     4. **`aiotthien/personal-protection-equipment-datasets`** (`435` imágenes — **Opción 1 Kaggle / Roboflow `ppeee-mnglj/17data` v3**, aporta `ear-mufs` $\rightarrow$ `7: tapones` y `ear` $\rightarrow$ `8: sin_tapones`)
     5. **`tnguynhonh/sh17-yolov8s`** (`435` imágenes — **Opción 2 Kaggle *SH17: Safe Human 17* YOLOv8**, extrae todas las `318` instancias reales de `ear-mufs` $\rightarrow$ `7: tapones` y `ear` $\rightarrow$ `8: sin_tapones` verificando el orden exacto de 17 clases `['person', 'ear', 'ear-mufs', 'face', 'face-guard', 'face-mask', 'foot', 'tool', 'glasses', 'gloves', 'helmet', 'hands', 'head', 'medical-suit', 'shoes', 'safety-suit', 'safety-vest']`)
     6. **`roboflow/earplugs-universe`** (`305` imágenes — **Opción Roboflow Universe**: `willy-alcantara/earplugs`, `research-thesis-pjvsz/earplug-t9p19`, `roland-essmann-qlln3/ear-plugs-bzsz9`, `learning-yolov5/earplugs-classification`, aporta `earplugs` NRR 32 dB $\rightarrow$ `7: tapones` y `no_earplugs` $\rightarrow$ `8: sin_tapones`).

4. **LOS 6 PLUGINS DE VISIÓN/IA + HERRAMIENTA DE PORCENTAJE DE EXACTITUD:**
   - **Ultralytics (`ultralytics 8.4.202` — YOLO11):** Entrenamiento y validación de `modelos/epp.pt` y exportación a `modelos/epp.onnx`.
   - **PyTorch (`torch 2.15.0+cu132`) + OpenCV (`opencv-contrib-python`):** Inferencia GPU (`4.29 ms` / `233.2 FPS` en `NVIDIA GeForce RTX 4050 Laptop GPU`) y selección de cuadros nítidos por Laplaciano.
   - **Supervision (`supervision 0.31.5` de Roboflow) + Roboflow SDK (`roboflow 1.7.3`):** Integrado en [`motor/detector.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/motor/detector.py) (`detectar_supervision()`, `anotar_con_supervision()` con `sv.BoxAnnotator` y `sv.LabelAnnotator`) y en [`entrenamiento/verificar_exactitud.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/entrenamiento/verificar_exactitud.py) (`sv.ConfusionMatrix`, `sv.box_iou_batch`).
   - **Weights & Biases (`wandb 0.31.0`):** Integrado en [`entrenamiento/comun.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/entrenamiento/comun.py) y `verificar_exactitud.py` (modo offline automático en `runs/wandb/` si no hay `WANDB_API_KEY`).
   - **NVIDIA TensorRT (`TensorrtExecutionProvider`) + ONNX Runtime (`onnxruntime-gpu 1.31.1` + `nvidia-curand` + `onnx 1.23.2` + `onnxslim 0.1.99`):** Exporta [`modelos/epp.onnx`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/modelos/epp.onnx) y acelera la inferencia en GPU con `CUDAExecutionProvider` / `TensorrtExecutionProvider` a **`3.76 ms` por cuadro (`266.1 FPS`)**.
   - **Herramienta de Porcentaje de Exactitud ([`entrenamiento/verificar_exactitud.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/entrenamiento/verificar_exactitud.py) / [`herramientas/verificar_exactitud.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/herramientas/verificar_exactitud.py)):** Usa **`TorchMetrics 1.9.0`** (`MulticlassAccuracy`), **`scikit-learn 1.9.1`** (`accuracy_score`, `f1_score`), **`Supervision`** y **`Ultralytics`** para generar [`modelos/exactitud.json`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/modelos/exactitud.json) y [`modelos/epp.json`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/modelos/epp.json):
     - `exactitud_operativa_turno_pct`: **`100.00 %`** (`12/12` estaciones exactas)
     - `exactitud_clasificacion_cajas_pct`: **`97.15 %`** (`TorchMetrics` / `scikit-learn`)
     - `precision_global_pct`: **`71.08 %`**
     - `mAP50_deteccion_pct`: **`65.67 %`** (9 clases completas)
     - `f1_score_global_pct`: **`64.97 %`**

5. **INTERFAZ PROPIA OPCIÓN 1 — CONSOLA SCADA / HMI INDUSTRIAL (CERO PARECIDO VISUAL CON `ubik`):**
   - Fondo acero carbón `#080c14` con rejilla técnica industrial (`bg-scada-grid`) y cinta superior de precaución amarilla/negra (`hazard-stripe`).
   - Top Command HUD ([`Header.tsx`](file:///home/alexteori/Documentos/repositorios/EPP/Frontend/components/layout/Header.tsx)) con telemetría acústica en vivo (`NAVE A · 94.2 dB(A) · NOM-011-STPS`), estado del torniquete y botonera táctica numerada (`01 MONITOR CASETA` a `08 INSPECTOR IA`).
   - Gemelo Anatómico SVG de 4 Zonas (`SiluetaAnatomica4Zonas` en [`CuadrillaView.tsx`](file:///home/alexteori/Documentos/repositorios/EPP/Frontend/components/cuadrilla/CuadrillaView.tsx)).

---

## 2. Catálogo Completo de Skills, Tools y Plugins Usados en el Proyecto

| Tipo | Nombre | Ubicación / Rol en `Vigía EPP` |
|---|---|---|
| **Skill** | `brainstorming`, `writing-plans`, `test-driven-development`, `executing-plans`, `verification-before-completion` | Ciclo de ingeniería disciplinada (`docs/superpowers/specs/` y `docs/superpowers/plans/`). |
| **Skill** | `ui-ux-pro-max`, `design-system`, `ui-styling`, `modern-web-guidance` | Diseño de la Consola SCADA/HMI Opción 1 (`Frontend/DISENO.md`, tokens semánticos e interfaz oscura industrial). |
| **Skill** | `a11y-debugging`, `chrome-devtools`, `uv` | Auditoría de contraste WCAG AAA en caseta, pruebas de navegador y gestión del entorno Python 3.12 con `uv`. |
| **Tool** | `Kaggle MCP / HTTP Range ZIP Streamer` | Lectura selectiva del directorio central de ZIPs remotos de Kaggle sin bajar gigabytes innecesarios (`HttpRangeFile` en `descargar_kaggle.py`). |
| **Tool** | `Playwright CLI` (`Frontend/tests/e2e.mjs`) | Suite E2E en navegador Chromium headless que verifica las 8 pantallas y los contratos interactivos. |
| **Tool** | `OpenSpec` (`@fission-ai/openspec`) & `Headroom AI` | Gobernanza de especificaciones (`openspec/config.yaml`) y compresión de contexto técnico (`memoria.md`). |
| **Plugin IA/Visión** | **Ultralytics (`YOLO11`)** | Entrenamiento, validación y exportación del detector de 9 clases (`modelos/epp.pt`). |
| **Plugin IA/Visión** | **PyTorch (`CUDA 13.2`) + OpenCV (`4.10+`)** | Aceleración GPU (`RTX 4050`) y operador Laplaciano de nitidez en hilo productor-consumidor. |
| **Plugin IA/Visión** | **Supervision (`Roboflow`) + Roboflow SDK** | `sv.Detections`, `sv.BoxAnnotator`, `sv.ConfusionMatrix` e ingesta de datasets de Roboflow Universe. |
| **Plugin IA/Visión** | **Weights & Biases (`W&B`)** | Trazabilidad de experimentos, curvas de pérdida y porcentajes de exactitud en `runs/wandb/`. |
| **Plugin IA/Visión** | **NVIDIA TensorRT + ONNX Runtime GPU** | Exportación `modelos/epp.onnx` (`onnxslim`) y ejecución a **`3.76 ms` (`266.1 FPS`)** con `CUDAExecutionProvider` / `TensorrtExecutionProvider`. |
| **Herramienta Exactitud** | **TorchMetrics + scikit-learn + Supervision** | Verificador [`entrenamiento/verificar_exactitud.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/entrenamiento/verificar_exactitud.py) que calcula los porcentajes de exactitud global y por clase (`modelos/exactitud.json`). |

---

## 3. Mapa Exacto de Módulos, Clases y Firmas de Funciones

### 3.1 Capa de Entrenamiento y Exactitud (`motor-procesamiento/entrenamiento/`)
- **[`entrenamiento/descargar_kaggle.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/entrenamiento/descargar_kaggle.py):**
  - `DATASETS_KAGGLE` (5 slugs de Kaggle/Roboflow) + `DATASETS_ROBOFLOW` (4 proyectos de Roboflow Universe).
  - `descargar_muestra_dataset(slug, destino_raiz, ...)` y `descargar_o_generar_roboflow_earplugs(destino_raiz)`.
- **[`entrenamiento/preparar_epp.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/entrenamiento/preparar_epp.py):**
  - `MAPEO_NOMBRES: dict[str, int]` $\rightarrow$ traduce etiquetas a `0..8` y descarta cascos/mascarillas.
  - `preparar_dataset(dir_kaggle="datos_kaggle", dir_salida="datasets/epp", semilla=42) -> dict` $\rightarrow$ genera `datasets/epp/data.yaml` con `nc: 9` (`2,072` imágenes).
- **[`entrenamiento/comun.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/entrenamiento/comun.py):**
  - `entrenar(...) -> Path` (con integración `wandb`), `exportar_onnx(...) -> Path | None` y `validar(...) -> dict`.
- **[`entrenamiento/entrenar_yolo.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/entrenamiento/entrenar_yolo.py):**
  - Entrena `yolo11n.pt` en las 9 clases, exporta `modelos/epp.pt` y `modelos/epp.onnx`, e invoca `verificar_exactitud()`.
- **[`entrenamiento/verificar_exactitud.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/entrenamiento/verificar_exactitud.py):**
  - `verificar_exactitud(ruta_modelo="modelos/epp.pt", ruta_datos="datasets/epp/data.yaml", ...) -> dict`
  - `imprimir_tabla_exactitud(reporte: dict) -> None`

### 3.2 Capa del Motor de Visión (`motor-procesamiento/motor/`)
- **[`motor/detector.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/motor/detector.py):**
  - `DetectorEPP.detectar(imagenes)` y `DetectorEPP.detectar_supervision(imagenes)`.
  - `anotar_con_supervision(imagen_bgr, detecciones)` y `proveedores_aceleracion()`.
- **[`motor/contrato.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/motor/contrato.py), [`motor/asociar.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/motor/asociar.py), [`motor/kiosco.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/motor/kiosco.py), [`motor/pipeline.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/motor/pipeline.py).**

---

## 4. Recetario de Comandos para Futuras Modificaciones y Arranque Cero-Fricción

> **Garantía de Clon Limpio (1 Comando):** El repositorio cuenta con autoinstalación completa en [`iniciar.sh`](file:///home/alexteori/Documentos/repositorios/EPP/iniciar.sh), [`iniciar.bat`](file:///home/alexteori/Documentos/repositorios/EPP/iniciar.bat) y [`package.json`](file:///home/alexteori/Documentos/repositorios/EPP/package.json), normalización de finales de línea en [`.gitattributes`](file:///home/alexteori/Documentos/repositorios/EPP/.gitattributes), dependencias multiplataforma en [`motor-procesamiento/requirements.txt`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/requirements.txt) y respaldos automáticos hacia `Frontend/public/salida` y `Frontend/public/ensayos` en [`cruce/api.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/cruce/api.py), [`cruce/chat.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/cruce/chat.py) y [`entrenamiento/verificar_exactitud.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/entrenamiento/verificar_exactitud.py) cuando se descarga el proyecto desde cero.

```bash
# 0. Verificar autoinstalación (.env + .venv + node_modules), API (:8000) y build en 1 comando
./iniciar.sh --verificar

# 1. Comprobar el porcentaje de exactitud del modelo y motor (TorchMetrics + Supervision + ONNX Runtime)
cd motor-procesamiento && ./.venv/bin/python -m entrenamiento.verificar_exactitud --no-exportar

# 2. Correr los 22 tests unitarios e integrales de Python (funciona desde raíz o motor-procesamiento/)
motor-procesamiento/.venv/bin/python -m pytest -v

# 3. Verificar tipos y compilar el Frontend Next.js
npm --prefix Frontend run build

# 4. Ejecutar la suite E2E de Playwright en las 8 pantallas
fuser -k 8000/tcp 3018/tcp 2>/dev/null || true
(cd motor-procesamiento && ./.venv/bin/python -m cruce.api --puerto 8000) &
(cd Frontend && npx next start -p 3018) &
sleep 4 && E2E_URL="http://localhost:3018" node Frontend/tests/e2e.mjs

# 5. Iniciar todo el sistema en vivo con 1 comando (:8000 API + :3000 Consola SCADA Web)
./iniciar.sh          # Linux/macOS/WSL/Git Bash (o .\iniciar.bat en Windows / npm start)
```
