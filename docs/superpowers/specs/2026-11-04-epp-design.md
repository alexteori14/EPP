# Diseño del Sistema de Inspección de EPP Pre-Turno (Vigía EPP)

**Fecha:** 2026-11-04  
**Repositorio destino:** `/home/alexteori/Documentos/repositorios/EPP`  
**Proyecto de referencia analizado y perfeccionado:** `/home/alexteori/Documentos/repositorios/ubik`

---

## 1. Intención y el Porqué

En la operación industrial donde se desplegará este software, es obligatorio que cada trabajador porte su **Equipo de Protección Personal (EPP) completo antes de iniciar su turno**. En la práctica, algunos trabajadores omiten parte de su equipo por incomodidad o prisa (por ejemplo, entran con chaleco pero sin lentes de seguridad o sin guantes), y la supervisión manual en el cambio de turno es lenta, subjetiva y no deja evidencia auditable ni cuantifica el riesgo económico y operativo.

En esta instalación específica **no se exige casco ni mascarilla**; el equipo obligatorio de entrada a turno consta exactamente de **3 elementos**:
1. **Lentes de Seguridad (`lentes` / `sin_lentes`)** — Protección ocular (zona anatómica: cabeza/ojos).
2. **Chaleco de Alta Visibilidad (`chaleco` / `sin_chaleco`)** — Visibilidad en piso (zona anatómica: torso).
3. **Guantes de Seguridad (`guantes` / `sin_guantes`)** — Protección manual (zona anatómica: manos/antebrazos).

**En una frase (estilo Ubik):**  
> **Vigía EPP convierte la cámara de acceso al turno o un video de entrada de personal en un filtro inmediato y una lista de incumplimientos ordenada por dinero en riesgo: quién no trae su EPP completo (chaleco, lentes y guantes), qué le falta, cuánto cuesta ese riesgo hoy, si hay stock en caseta para entregárselo al instante y la foto exacta como evidencia.**

---

## 2. Metas, No-Metas y Anti-Metas

### Metas (Goals)
- **Heredar y perfeccionar la arquitectura de Ubik:**
  - `motor-procesamiento/` en Python 3.12 (`uv`), desacoplado por contrato JSON (`CONTRATO.md`), con selección de cuadros nítidos (varianza del Laplaciano), inferencia YOLO11, asociación geométrica persona↔EPP, seguimiento multi-cuadro con votación por confianza, generación de video anotado H.264 + recortes de evidencia y asistente RAG con Gemini (`cruce/chat.py`).
  - Tablero web en Next.js 15 + TypeScript + Tailwind CSS + Framer Motion bajo la **regla de los 10 segundos** y diseño *Precision Industrial Slate* 100% capaz de operar offline (fuentes locales `@fontsource/inter`, datos pre-generados de respaldo en `public/salida/`).
  - Un solo comando de arranque (`./iniciar.sh`) que levanta la API del motor (`:8000`) y el tablero (`:3000`).
- **Corregir las limitaciones detectadas en Ubik:**
  1. **Persistencia real de correcciones/autorizaciones:** En Ubik (`HallazgosView.tsx`), el botón *"Marcar corregido"* solo mutaba un `useState` local y se perdía al recargar. Aquí agregamos `PATCH /analisis/<id>/hallazgos/<hallazgo_id>` (y soporte para la corrida activa/demo) que persiste el estado en disco y recalcula en vivo el riesgo pendiente y recuperado.
  2. **Kiosco de Pase de Turno en Vivo (`/kiosco`) + Modo Jurado en Vivo:** Además de auditar videos de filas/pasillos como Ubik, incorpora una pantalla de Kiosco interactivo (con cámara WebRTC en vivo, subida rápida de foto/ráfaga o tarjetas de prueba del jurado) que evalúa en <1 s a la persona frente a cámara y emite **"Pase de Turno Autorizado (3/3 EPP)"** o **"Acceso Detenido"** con la silueta anatómica de 3 zonas.
  3. **Asociación espacial Persona ↔ EPP (`motor/asociar.py`):** En vez de depender de marcadores ArUco o planogramas rígidos de supermercado, el motor detecta a cada trabajador (`persona`) y ancla geométricamente las detecciones positivas (`chaleco`, `lentes`, `guantes`) y negativas (`sin_chaleco`, `sin_lentes`, `sin_guantes`) a sus 3 regiones anatómicas (cabeza/ojos, torso, manos).
  4. **Honestidad con lo dudoso:** Si una zona anatómica no es visible en el encuadre (ej. manos fuera de cuadro) o tiene baja confianza (< 0.55) / pocas lecturas, se clasifica como **`revisar` (Ámbar)** y no suma dinero al riesgo ni acusa en falso.
- **Entrenamiento real con los 3 datasets de Kaggle:**
  - Descargar e integrar:
    1. `ndomalau/personal-protective-equipment-ppe-dataset`
    2. `shlokraval/ppe-dataset-yolov8`
    3. `slimese/personal-protective-equipment`
  - Filtrar y armonizar las etiquetas al esquema de **7 clases canónicas** del proyecto (`persona`, `chaleco`, `sin_chaleco`, `lentes`, `sin_lentes`, `guantes`, `sin_guantes`), ignorando las clases de casco (`helmet`, `no_helmet`, `Hardhat`, `NO-Hardhat`), mascarilla (`Mask`, `NO-Mask`) y objetos ajenos (`Fall-Detected`, `Ladder`, `Safety Cone`), y desduplicando imágenes entre `shlokraval` (v4) y `slimese` (v1).
- **Integrar las herramientas, skills y plugins solicitados:**
  - Diseño: `ui-ux-pro-max-cli` (`uipro init --ai antigravity`), `ui-skills`, `impeccable`.
  - Planeación: `@fission-ai/openspec` (`openspec/`).
  - Metodología: `superpowers`.
  - Animaciones: `framer-motion`.
  - Plugins: `@playwright/cli@latest` (verificación visual y pruebas E2E automatizadas) y `headroom-ai[all]`.
- **Entregar los dos documentos maestros en la raíz:**
  - `documentacion.md`: documentación técnica exhaustiva (arquitectura, decisiones, datasets, matemáticas del motor y del cruce, contratos, pruebas y guía operativa).
  - `memoria.md`: memoria ejecutiva y técnica ultra-estructurada y compacta en tokens para que cualquier IA futura retome el contexto completo del proyecto en segundos.

### No-Metas (Non-Goals)
- **No evaluar casco ni mascarilla:** Por requerimiento explícito del sitio donde se instalará el software, ni el modelo ni la interfaz pedirán casco o mascarilla.
- **No depender de servicios en la nube para visión:** Todo el procesamiento de video y kiosco corre localmente en la laptop (GPU RTX 4050 6 GB o CPU). Solo el asistente conversacional usa la API de Gemini si hay clave configurada en `.env`.
- **No requerir hardware propietario (torniquetes físicos o marcadores ArUco en la ropa):** Funciona con cualquier cámara web USB/integrada, celular o cámara CCTV de acceso.

### Anti-Metas (Anti-Goals — qué haría fracasar el proyecto aunque funcione técnicamente)
- Acusar a un trabajador de "Sin guantes" cuando sus manos nunca salieron en el cuadro del video (debe marcarse como zona no visible o `revisar`).
- Duplicar imágenes idénticas entre `train` y `val` al mezclar `shlokraval` y `slimese`, inflando artificialmente el mAP50.
- Romper la experiencia del tablero cuando la API de Python esté apagada (el tablero debe seguir mostrando el turno de demostración completo desde `public/salida/`, igual que Ubik).

---

## 3. Enfoques Considerados y Elección

### Enfoque 1 — Detector Unificado YOLO11 (7 Clases) + Anclaje Anatómico + Votación Multi-Cuadro (Elegido)
- **Cómo funciona:**
  1. Se construye un dataset curado y desduplicado a partir de los 3 datasets de Kaggle con 7 clases (`0: persona`, `1: chaleco`, `2: sin_chaleco`, `3: lentes`, `4: sin_lentes`, `5: guantes`, `6: sin_guantes`).
  2. Se entrena un modelo `modelos/epp.pt` basado en `yolo11n.pt` (con soporte de reanudación automática en `entrenamiento/comun.py`).
  3. En inferencia (`motor/pipeline.py` para video y `motor/kiosco.py` para evaluación instantánea), cada cuadro pasa una sola vez por YOLO11.
  4. `motor/asociar.py` empareja cada detección de EPP (positiva o negativa) con la caja `persona` correspondiente usando intersección sobre área del equipo y ventanas anatómicas relativas a la persona:
     - **Ojos / Cabeza (`lentes` / `sin_lentes`):** franja vertical `y ∈ [0.00, 0.30]` de la caja de la persona.
     - **Torso (`chaleco` / `sin_chaleco`):** franja vertical `y ∈ [0.18, 0.70]` de la caja de la persona.
     - **Manos (`guantes` / `sin_guantes`):** franja vertical `y ∈ [0.30, 0.95]` (incluyendo extensión lateral del 15% para brazos extendidos).
  5. Se rastrea a cada trabajador a lo largo del video (`motor/rastreo.py` por IoU + centroide en orden de aparición en el filtro) y se vota cada una de las 3 prendas entre los cuadros más nítidos.
- **Por qué se eligió:** Corre en ~6 ms por cuadro en la RTX 4050, aprovecha directamente las anotaciones negativas (`no_vest`, `NO-Safety Vest`, `NO-Goggles`, `NO-Gloves`) presentes en los datasets de Kaggle, y unifica el motor de video y el Kiosco en Vivo con el mismo modelo y las mismas reglas.

### Enfoque 2 — Cascada en Dos Etapas (YOLO Pose + Clasificador Secundario por Recorte) (Descartado)
- **Cómo funciona:** Detecta keypoints del cuerpo con YOLO-Pose, recorta muñecas, pecho y ojos, y ejecuta un clasificador ViT/DINOv2 sobre cada recorte.
- **Por qué se descartó:** Multiplica por 4×–5× la latencia por persona en cada cuadro, entorpece la fluidez del Kiosco en Vivo y desaprovecha las etiquetas de cajas negativas que ya incluyen los tres datasets de Kaggle.

---

## 4. Arquitectura Detallada del Sistema (Decidida y Propuesta)

### 4.1 Estructura de Carpetas del Repositorio (`/home/alexteori/Documentos/repositorios/EPP`)

```text
EPP/
├── iniciar.sh                        # Arranca API (:8000) y Tablero (:3000) con un solo comando
├── .env.example                      # APIGEMINI y variables opcionales del asistente y motor
├── README.md                         # Guía rápida estilo Ubik
├── PITCH.md                          # Narrativa ejecutiva, problema, solución, métricas y guion de demo
├── documentacion.md                  # Documentación técnica en extremo detalle (entregable obligatorio)
├── memoria.md                        # Memoria compacta de contexto para IAs futuras (entregable obligatorio)
├── docs/superpowers/specs/           # Especificaciones de diseño y planes de implementación
├── openspec/                         # Especificaciones inicializadas con @fission-ai/openspec
├── motor-procesamiento/              # Backend y motor de visión en Python 3.12 (uv)
│   ├── requirements.txt
│   ├── CONTRATO.md                   # Esquema exacto de observaciones.json, hallazgos.json, red.json y API
│   ├── datos/sistema/
│   │   ├── turnos.csv                # Posiciones/trabajadores del filtro de entrada y zona asignada
│   │   ├── inventario_epp.csv        # Existencia en caseta/almacén, costo reposición y riesgo diario US$
│   │   └── reglas_riesgo.csv         # Desglose de multas STPS/OSHA, prima de riesgo y paro por prenda
│   ├── entrenamiento/
│   │   ├── comun.py                  # Entrenamiento YOLO11 reanudable + validación mAP50 por clase
│   │   ├── descargar_kaggle.py       # Descarga y extracción vía endpoint/MCP de Kaggle de los 3 datasets
│   │   ├── preparar_epp.py           # Armonización a 7 clases (sin casco ni mascarilla) y desduplicación SHA1
│   │   └── entrenar_yolo.py          # Entrena modelos/epp.pt y guarda métricas en modelos/epp.json
│   ├── modelos/
│   │   ├── epp.pt                    # Modelo YOLO11 entrenado en las 7 clases de EPP
│   │   └── epp.json                  # Métricas reales de validación (mAP50, mAP50-95 y AP por clase)
│   ├── simulador/
│   │   ├── datos_prueba.py           # Genera datos/sistema/ y escenas de prueba con imágenes reales del test split
│   │   ├── render_turno.py           # Genera el video de recorrido de entrada a turno (4K/1080p) y tarjetas de jurado
│   │   └── tarjetas.py               # Videos cortos para el Modo Jurado en vivo (sin_chaleco, sin_lentes, sin_guantes, sin_lentes_ni_guantes)
│   ├── motor/
│   │   ├── contrato.py               # Constantes, las 3 zonas de EPP y lectura de turnos/inventario
│   │   ├── cuadros.py                # Selección del cuadro más nítido por ventana (varianza del Laplaciano)
│   │   ├── detector.py               # Envoltura de YOLO11 para las 7 clases
│   │   ├── asociar.py                # Anclaje geométrico Persona ↔ {chaleco, lentes, guantes} y sus negativos
│   │   ├── rastreo.py                # Seguimiento de trabajadores entre cuadros y votación multi-cuadro
│   │   ├── kiosco.py                 # Evaluación rápida de imagen/ráfaga para el Kiosco en Vivo (<300 ms)
│   │   ├── anotar.py                 # Video H.264 anotado y recortes de evidencia (persona completa + zona faltante)
│   │   └── pipeline.py               # Orquestador CLI con progreso atómico, caché por huella SHA1 y diagnóstico
│   ├── cruce/
│   │   ├── hallazgos.py              # Cruza observaciones.json vs datos/sistema/ -> hallazgos.json ordenado por US$/día
│   │   ├── red.py                    # Proyecta el riesgo sistémico (EPP agotado en almacén) a la red de plantas
│   │   ├── publicar.py               # Publica salida/, red.json y ensayos/ hacia Frontend/public/
│   │   ├── chat.py                   # Asistente RAG con Gemini + caché de embeddings por corrida
│   │   └── api.py                    # Servidor HTTP (biblioteca estándar): Kiosco, Jurado, Videos, Persistencia y Chat
│   ├── herramientas/
│   │   └── evaluar_motor.py          # Evalúa precisión del motor contra la verdad de escena
│   └── tests/                        # Suite pytest completa (motor, asociación, cruce, kiosco, persistencia, red, chat)
└── Frontend/                         # Tablero Next.js 15 + React 19 + Tailwind + Framer Motion + UI Pro Max
    ├── DISENO.md                     # Manual de sistema visual Industrial Safety Slate
    ├── openspec/
    ├── app/
    │   ├── resumen/page.tsx          # Pantalla 1: Resumen ejecutivo ("X trabajadores sin EPP · US$Y en riesgo hoy")
    │   ├── kiosco/page.tsx           # Pantalla 2: Kiosco de Inicio de Turno en Vivo (Webcam + Foto + Modo Jurado)
    │   ├── recorrido/page.tsx        # Pantalla 3: Video anotado con marcadores en la línea de tiempo por trabajador
    │   ├── cuadrilla/page.tsx        # Pantalla 4: Gemelo Digital de la Fila + Silueta Anatómica de 3 Zonas
    │   ├── hallazgos/page.tsx        # Pantalla 5: Tarjetas ordenadas por dinero con persistencia real al autorizar/corregir
    │   ├── red/page.tsx              # Pantalla 6: Impacto en Red de Plantas (local vs. sistémico por desabasto)
    │   ├── analizar/page.tsx         # Pantalla 7: Subir video de turno + Historial de corridas
    │   └── asistente/page.tsx        # Pantalla 8: Asistente IA con RAG y fuentes verificables
    ├── components/
    ├── lib/
    ├── types/
    └── tests/                        # Pruebas E2E con Playwright CLI verificando cada pantalla
```

### 4.2 Armonización de los 3 Datasets de Kaggle (`entrenamiento/preparar_epp.py`)

Los 3 datasets solicitados tienen esquemas distintos que se unifican automáticamente en `entrenamiento/preparar_epp.py`:

| Dataset en Kaggle | Clases originales | Mapeo a las 7 clases de Vigía EPP | Clases descartadas (no requeridas en planta) |
|---|---|---|---|
| `ndomalau/personal-protective-equipment-ppe-dataset` | `['helmet', 'no_helmet', 'no_vest', 'person', 'vest']` | `person` → `0: persona`<br>`vest` → `1: chaleco`<br>`no_vest` → `2: sin_chaleco` | `helmet`, `no_helmet` |
| `shlokraval/ppe-dataset-yolov8` | `['Fall-Detected', 'Gloves', 'Goggles', 'Hardhat', 'Ladder', 'Mask', 'NO-Gloves', 'NO-Goggles', 'NO-Hardhat', 'NO-Mask', 'NO-Safety Vest', 'Person', 'Safety Cone', 'Safety Vest']` | `Person` → `0: persona`<br>`Safety Vest` → `1: chaleco`<br>`NO-Safety Vest` → `2: sin_chaleco`<br>`Goggles` → `3: lentes`<br>`NO-Goggles` → `4: sin_lentes`<br>`Gloves` → `5: guantes`<br>`NO-Gloves` → `6: sin_guantes` | `Hardhat`, `NO-Hardhat`, `Mask`, `NO-Mask`, `Fall-Detected`, `Ladder`, `Safety Cone` |
| `slimese/personal-protective-equipment` | Mismo esquema de 14 clases (v1 de Roboflow) | Igual que `shlokraval`, filtrando primero por hash perceptual / SHA1 del archivo para no duplicar imágenes entre train y val | Igual que `shlokraval` |

### 4.3 Reglas del Cruce y Cálculo de Dinero en Riesgo (`cruce/hallazgos.py`)

Para cada trabajador evaluado en el filtro de inicio de turno, el motor entrega el estado de sus 3 zonas (`chaleco`, `lentes`, `guantes`): `ok` (equipo detectado), `falta` (se detectó la clase `sin_*` o la zona anatómica se vio nítida sin el equipo) o `dudoso` (confianza < 0.60, menos de 2 lecturas o zona fuera de cuadro).

El cruce compara contra `datos/sistema/inventario_epp.csv` y `reglas_riesgo.csv`:

| Tipo de Hallazgo (`tipo`) | Condición | Impacto Económico Diario (`impacto_diario`) | Sistémico vs. Local | Acción Sugerida |
|---|---|---|---|---|
| `epp_faltante_agotado` | Al trabajador le falta ≥1 EPP y en `inventario_epp.csv` hay **0 piezas** en caseta | Riesgo de multa STPS/OSHA + costo de paro de puesto completo (`riesgo_multa_usd + costo_paro_diario_usd`) | **Sistémico** (desabasto de almacén; se proyecta en `red.json` a otras plantas/turnos) | *"Detener ingreso a piso y solicitar resurtido urgente a almacén central."* |
| `multiples_epp_faltantes` | Al trabajador le faltan **2 o 3 prendas** (ej. sin lentes y sin guantes) pero sí hay stock en caseta | Suma del riesgo operativo diario de cada prenda faltante | **Local** (hábito/omisión en este turno) | *"Detener en filtro y entregar {prendas} desde caseta ({n} disponibles)."* |
| `sin_lentes` | Falta únicamente protección ocular (`lentes`) y hay stock en caseta | Riesgo diario por exposición ocular (`riesgo_diario_usd` de `lentes`, ej. US$420/día) | **Local** | *"Entregar lentes de seguridad en caseta ({n} en stock) antes de autorizar acceso."* |
| `sin_guantes` | Faltan únicamente guantes (`guantes`) y hay stock en caseta | Riesgo diario por exposición manual (`riesgo_diario_usd` de `guantes`, ej. US$340/día) | **Local** | *"Entregar par de guantes en caseta ({n} en stock) antes de autorizar acceso."* |
| `sin_chaleco` | Falta únicamente chaleco (`chaleco`) y hay stock en caseta | Riesgo diario por baja visibilidad en pasillos de montacargas (`riesgo_diario_usd` de `chaleco`, ej. US$290/día) | **Local** | *"Entregar chaleco de alta visibilidad en caseta ({n} en stock) antes de autorizar acceso."* |
| `revisar` | Cualquier prenda quedó con lectura dudosa (`confianza < 0.60` o zona oculta) y ninguna otra salió como `falta` confirmada | **US$0.00** (Principio de honestidad de Ubik: no se suma dinero sobre lecturas dudosas) | No cuenta como error | *"Verificar visualmente {prenda} en caseta (zona parcialmente oculta o borrosa)."* |

---

## 5. Decisiones Técnicas Tomadas por el Diseñador (Propuestas por Defecto)

Las siguientes decisiones técnicas siguen el patrón de Ubik y quedan asentadas salvo que quieras cambiarlas:
1. **7 clases exactas en YOLO11 (`yolo11n.pt`):** `persona`, `chaleco`, `sin_chaleco`, `lentes`, `sin_lentes`, `guantes`, `sin_guantes`.
2. **Muestreo balanceado para entrenamiento rápido y de alta precisión en tu RTX 4050 (6 GB):** Se descargan los paquetes de Kaggle y `preparar_epp.py` construye un dataset limpio y balanceado (ej. ~3,000–4,500 imágenes con todas las instancias de guantes, lentes y chalecos bien representadas y sin duplicados entre splits) entrenado a `imgsz=640` con reanudación automática, logrando tiempos de entrenamiento de ~15–20 minutos en tu RTX 4050 con métricas reales exportadas a `modelos/epp.json`.
3. **Gemelo Digital de Doble Nivel en `/cuadrilla`:**
   - Izquierda (8 columnas): **Rejilla de Cuadrilla por Zona/Línea** (equivalente a las repisas del anaquel en Ubik: Línea A Ensamble, Línea B Montacargas, Línea C Empaque, con 4 trabajadores por línea).
   - Derecha (4 columnas): **Gemelo Anatómico de 3 Zonas** del trabajador seleccionado (Ojos: Lentes, Torso: Chaleco, Manos: Guantes) con foto de evidencia, confianza por prenda y botón para autorizar ingreso tras entrega de EPP en caseta.
4. **Kiosco en Vivo (`/kiosco`):** Permite usar la cámara web en tiempo real, subir una foto instantánea o probar con un clic cualquiera de las **4 tarjetas del Modo Jurado** (Trabajador Completo, Sin Lentes, Sin Guantes, Sin Chaleco + Stock Agotado).

---

## 6. Lo que queda a criterio del Constructor (Builder)

- Ajustes finos de hiperparámetros de entrenamiento (`mosaic`, `fliplr`, `batch=8` o `16` según VRAM libre en la RTX 4050).
- Nombres ficticios de la empresa industrial de demostración (ej. **Aceros & Logística InduSafe · Planta Monterrey Norte**) y de los 12 trabajadores del turno en `datos/sistema/turnos.csv`.
- Diseño detallado de los componentes de interfaz aplicando las reglas generadas por `ui-ux-pro-max-cli`, `ui-skills` e `impeccable`.
