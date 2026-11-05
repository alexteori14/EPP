# Documentación Técnica Maestra — Vigía EPP

**Proyecto:** Vigía EPP — Sistema de Inspección Pre-Turno y Auditoría de Equipo de Protección Personal (EPP)  
**Ubicación del repositorio:** `/home/alexteori/Documentos/repositorios/EPP`  
**Proyecto de referencia analizado y perfeccionado:** `/home/alexteori/Documentos/repositorios/ubik`  
**Arquitectura de visión:** Detector unificado `YOLO11n` (`modelos/epp.pt`) + Asociación Geométrica Anatómica de 3 Zonas (`motor/asociar.py`) + Rastreo y Votación Multi-Cuadro (`motor/rastreo.py`)

---

## 1. Resumen Ejecutivo y Propósito del Sistema

En plantas industriales de manufactura, metalmecánica y logística, el inicio de turno es el punto de control crítico donde se debe verificar que cada trabajador porte su **Equipo de Protección Personal (EPP) completo**. En la operación diaria, diversos trabajadores omiten prendas (por ejemplo, dejan los lentes en el casillero o entran sin guantes anticorte por incomodidad), exponiéndose a accidentes graves y exponiendo a la planta a sanciones regulatorias (**NOM-017-STPS** / **OSHA**) y paros de línea.

### 1.1 Restricción de Dominio Específica de la Planta (Exclusión de Casco y Mascarilla)
Por requerimiento explícito de la instalación donde se despliega el software:
> **En esta planta NO se exige casco (`casco`) ni mascarilla (`mascarilla`).**

Por consiguiente, tanto el dataset armonizado como el modelo neuronal `modelos/epp.pt`, las reglas geométricas de asociación anatómica, los catálogos CSV del sistema y las 8 pantallas del Frontend evalúan **única y exclusivamente 3 prendas obligatorias**:
1. **Lentes de seguridad ANSI Z87.1 (`lentes` / `sin_lentes`)** — Protección ocular contra partículas y rebabas metálicas.
2. **Chaleco reflejante Clase 2 (`chaleco` / `sin_chaleco`)** — Alta visibilidad en pasillos de montacargas y grúas viajeras.
3. **Guantes anticorte Nivel A4 (`guantes` / `sin_guantes`)** — Protección manual en corte, prensa, soldadura y maniobras.

---

## 2. Análisis Profundo del Proyecto `ubik` y Cómo `Vigía EPP` lo Perfecciona

Antes de diseñar la primera línea de código de **Vigía EPP**, se auditó de principio a fin el repositorio `/home/alexteori/Documentos/repositorios/ubik` (cuyo alcance original era auditoría de anaqueles de supermercado para *Glazed Co.*).

### 2.1 Lo Mejor de `ubik` que se Conservó y Adaptó
1. **Separación en 3 Capas Desacopladas por Contratos JSON (`CONTRATO.md`):**
   - **Capa 1 (`motor/`):** Visión pura (selección de cuadros nítidos con Laplaciano + flujo óptico, detección con YOLO11, asociación geométrica, rastreo IoU + EMA y renderizado H.264 con `ffmpeg`) que produce `observaciones.json`, `recorrido_anotado.mp4` y `recortes/*.jpg`.
   - **Capa 2 (`cruce/`):** Cruce contra el sistema de la empresa (`datos/sistema/*.csv`), cuantificación monetaria en dólares por día (`US$/día`), proyección a toda la red de plantas (`red.json`), asistente conversacional RAG con citas verificables y servidor HTTP multihilo en Python estándar (`cruce/api.py` en `:8000`).
   - **Capa 3 (`Frontend/`):** Aplicación Next.js 15 + React 19 + Tailwind CSS 100 % capaz de operar offline con tipografías locales (`@fontsource/inter`, `@fontsource/fira-code`) y proxy transparente `/motor/:path* -> http://127.0.0.1:8000/:path*`.
2. **Principio de Honestidad Operativa (`revisar` = `US$0.00`):**
   - En lugar de inventar multas o detener injustamente a un trabajador cuando una mano o el rostro aparece ocluido o con baja confianza (`< 0.60`), el sistema clasifica la lectura como `"revisar"` y le asigna **`US$0.00`** de impacto hasta que el guardia de caseta lo verifique visualmente.
3. **Modo Jurado en Vivo y Simulador Determinista con Imágenes Reales:**
   - Capacidad de generar un recorrido reproducible (`simulador/render_turno.py`) con verdad absoluta (`escena/escena.json`) y 4 tarjetas de prueba en vivo (`simulador/tarjetas.py`) para demostrar frente a un jurado cómo el motor detecta una omisión nueva en segundos.

### 2.2 Debilidades Técnicas de `ubik` Corregidas en `Vigía EPP`

| Debilidad detectada en `ubik` | Cómo se perfeccionó en `Vigía EPP` |
|---|---|
| **1. "Marcar corregido" efímero:** En `ubik/Road2Tech/Frontend/components/hallazgos/HallazgosView.tsx`, el botón *"Marcar corregido"* solo hacía `useState` local en el navegador; al recargar la página o cambiar de pestaña se perdía la acción y el dinero en riesgo nunca disminuía en el servidor. | Se implementó persistencia atómica en disco mediante `cruce.hallazgos.actualizar_corregido()` y el endpoint `PATCH /analisis/<id>/hallazgos/<hallazgo_id>` en `cruce/api.py`. Al autorizar un hallazgo tras entregar el EPP en caseta, se actualiza tanto `salida/hallazgos.json` como `Frontend/public/salida/hallazgos.json` y `red.json`, recalculando `dinero_en_riesgo_diario` y `dinero_recuperado_diario`. |
| **2. Asistente IA inutilizable sin internet o sin `APIGEMINI`:** En `ubik/motor-procesamiento/cruce/chat.py`, si no existía clave de Gemini en `.env` o fallaba la red, la pantalla `/asistente` quedaba bloqueada con un aviso de error. | `cruce/chat.py` implementa una **arquitectura RAG híbrida**: usa Gemini (`gemini-2.5-flash`) + embeddings cuando `APIGEMINI` está configurada, y cae automáticamente a un **motor RAG determinista local offline** que puntúa léxicamente los mismos fragmentos verificados de la corrida (`[RESUMEN]`, `[REGLAS]`, `[H1..H8]`, `[P1..P12]`) y sintetiza respuestas exactas con citas en `< 15 ms`. |
| **3. Ausencia de modo de inspección en tiempo real (< 300 ms):** `ubik` solo procesaba videos completos en lote (`pipeline.py`), lo cual toma varios segundos y no sirve para un torniquete de acceso en vivo. | Se creó el módulo `motor/kiosco.py`, el endpoint `POST /kiosco/evaluar` y la pantalla `/kiosco` (`KioscoView.tsx`), permitiendo evaluar cuadros de cámara web WebRTC, fotos subidas o 5 presets de torniquete en **`~3.3 ms`** con veredicto instantáneo `"PASE DE TURNO AUTORIZADO"` / `"ACCESO DETENIDO"`. |
| **4. Geometría rectangular rígida de anaquel:** `ubik` dividía el video en celdas fijas de repisas de supermercado. | Se diseñó `motor/asociar.py` con **Geometría Anatómica Relativa de 3 Zonas** dentro de cada caja de `persona` detectada (`Ojos [0.00, 0.32]`, `Torso [0.16, 0.72]`, `Manos [0.28, 0.96]`), combinando contención espacial + cercanía al centro anatómico esperado + prioridad de evidencia positiva sobre negativa según confianza. |

---

## 3. Herramientas, Skills, Plugins y Metodología Utilizados

Durante la construcción del proyecto se instalaron, configuraron y aplicaron las siguientes herramientas solicitadas:

1. **Diseño UI/UX (`ui-ux-pro-max-cli` + `ui-skills` + `impeccable`):**
   - Inicializado en el repositorio con `npx --yes ui-ux-pro-max-cli init --ai antigravity` (instalando los skills de diseño en `.agents/skills/`).
   - Se definió el sistema de diseño **Industrial Safety Slate** en [`Frontend/DISENO.md`](file:///home/alexteori/Documentos/repositorios/EPP/Frontend/DISENO.md), aplicando contraste industrial (`slate-50`, `slate-900`, `teal-600`, `emerald-600`, `rose-600`, `amber-600`) y números tabulares (`font-variant-numeric: tabular-nums`).
2. **Planeación Basada en Especificaciones (`@fission-ai/openspec`):**
   - Inicializado en [`openspec/`](file:///home/alexteori/Documentos/repositorios/EPP/openspec/config.yaml) junto con la especificación formal en [`docs/superpowers/specs/2026-11-04-epp-design.md`](file:///home/alexteori/Documentos/repositorios/EPP/docs/superpowers/specs/2026-11-04-epp-design.md) y el plan de implementación en [`docs/superpowers/plans/2026-11-04-epp-implementation-plan.md`](file:///home/alexteori/Documentos/repositorios/EPP/docs/superpowers/plans/2026-11-04-epp-implementation-plan.md).
3. **Metodología de Ingeniería (`obra/superpowers`):**
   - Ejecución guiada por `brainstorming`, `writing-plans`, `test-driven-development`, `executing-plans` y `verification-before-completion`. Cada tarea fue verificada con pruebas automatizadas antes de avanzar.
4. **Animaciones y Componentes (`framer-motion`, `lucide-react`, Tailwind CSS):**
   - Instalados en [`Frontend/package.json`](file:///home/alexteori/Documentos/repositorios/EPP/Frontend/package.json) para transiciones fluidas y barras de crecimiento (`barra-crece`) con soporte completo para `prefers-reduced-motion`.
5. **Verificación E2E en Navegador Real (`@playwright/cli` / `playwright`):**
   - Automatizado en [`Frontend/tests/e2e.mjs`](file:///home/alexteori/Documentos/repositorios/EPP/Frontend/tests/e2e.mjs) para levantar un navegador Chromium headless real y probar las 8 pantallas, el Kiosco en vivo, el Modo Jurado, la persistencia `PATCH` y el Asistente IA.
6. **Optimización de Contexto (`headroom-ai`):**
   - Instalado vía `uv tool install --python 3.13 "headroom-ai[all]"` y complementado con [`memoria.md`](file:///home/alexteori/Documentos/repositorios/EPP/memoria.md) para minimizar el consumo de tokens en sesiones futuras.

---

## 4. Datasets de Kaggle (vía Kaggle MCP) y Pipeline de Entrenamiento YOLO11

### 4.1 Fuentes de Datos Descargadas
El módulo [`entrenamiento/descargar_kaggle.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/entrenamiento/descargar_kaggle.py) conecta con los 3 datasets de Kaggle especificados para el proyecto:
1. **`ndomalau/personal-protective-equipment-ppe-dataset`**
2. **`shlokraval/ppe-dataset-yolov8`**
3. **`slimese/personal-protective-equipment`**

### 4.2 Descubrimiento Crítico y Deduplicación Anti-Leakage (`preparar_epp.py`)
Al inspeccionar los metadatos y nombres de archivo de los tres datasets, se descubrió que:
- `shlokraval/ppe-dataset-yolov8` y `slimese/personal-protective-equipment` provienen de versiones distintas del mismo proyecto de Roboflow (`personal-protective-equipment-combined-model`), compartiendo miles de imágenes base con sufijos `.rf.<hash>.jpg`.
- Para evitar contaminación entre entrenamiento y validación (*data leakage*), [`entrenamiento/preparar_epp.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/entrenamiento/preparar_epp.py) extrae la clave canónica `clave_base_roboflow()` (eliminando `.rf.<hash>`) además del hash `SHA-1` del archivo binario, garantizando que ninguna imagen aparezca en dos particiones.

### 4.3 Armonización al Esquema Canónico de 7 Clases (Sin Casco ni Mascarilla)
`preparar_epp.py` traduce las etiquetas originales en inglés de los 3 datasets al esquema canónico de 7 clases definido en [`motor/contrato.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/motor/contrato.py), **descartando por completo cualquier etiqueta de casco (`Helmet`, `Hardhat`, `NO-Hardhat`) o mascarilla (`Mask`, `NO-Mask`)**:

| ID | Clase Canónica | Etiquetas de origen mapeadas |
|---|---|---|
| `0` | `persona` | `Person`, `person`, `worker` |
| `1` | `chaleco` | `Safety Vest`, `Vest`, `vest`, `safety-vest` |
| `2` | `sin_chaleco` | `NO-Safety Vest`, `no-vest`, `no_safety_vest` |
| `3` | `lentes` | `Goggles`, `glasses`, `safety-glasses`, `Eye Wear` |
| `4` | `sin_lentes` | `NO-Goggles`, `no-glasses`, `no_goggles` |
| `5` | `guantes` | `Gloves`, `gloves`, `glove` |
| `6` | `sin_guantes` | `NO-Gloves`, `no-gloves`, `no_gloves` |

Además, cuando una imagen contiene las cajas de las prendas pero el anotador original omitió la caja envolvente de `persona`, `_asegurar_caja_persona()` sintetiza una caja anatómica envolvente a partir de las prendas detectadas para no perder supervisión sobre la clase `0: persona`.

### 4.4 Entrenamiento en GPU y Métricas Reales (`modelos/epp.pt` y `modelos/epp.json`)
Se entrenó `yolo11n.pt` mediante [`entrenamiento/entrenar_yolo.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/entrenamiento/entrenar_yolo.py) sobre una **NVIDIA GeForce RTX 4050 Laptop GPU** con partición deduplicada (`658 train`, `164 val`, `75 test`), resolución `640×640`, optimizador `AdamW`, aumentos `mosaic=0.7` y `fliplr=0.5`.

Métricas reales registradas en [`motor-procesamiento/modelos/epp.json`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/modelos/epp.json):
- **`mAP@0.50` global:** **`0.6720`** (`67.2 %`)
- **`mAP@0.50:0.95` global:** **`0.3367`**
- **Precisión global:** **`0.6639`** · **Recall global:** **`0.6008`**
- **Desempeño por clase (`AP@0.50`):**
  - `persona`: **`0.9411`** (`94.1 %`)
  - `chaleco`: **`0.8676`** (`86.8 %`)
  - `sin_chaleco`: **`0.7550`** (`75.5 %`)
  - `guantes`: **`0.6804`** (`68.0 %`)
  - `sin_lentes`: **`0.5272`** (`52.7 %`)
  - `sin_guantes`: **`0.5140`** (`51.4 %`)
  - `lentes`: **`0.4188`** (`41.9 %`)
- **Velocidad de inferencia:** **`3.3 – 3.4 ms` por cuadro** en GPU.

---

## 5. Arquitectura Matemática del Motor de Visión (`motor/`)

### 5.1 Selección de Cuadros Nítidos (`motor/cuadros.py`)
Para evitar procesar cuadros barridos por movimiento cuando la cámara recorre la fila de trabajadores:
1. Se divide el video en ventanas temporales de `~0.5 s`.
2. Para cada cuadro se calcula la **nitidez Laplaciana** $\sigma^2(\nabla^2 I)$ sobre escala de grises y la velocidad horizontal media por flujo óptico o diferencia absoluta.
3. Se elige el cuadro que maximiza $\text{Score} = \frac{\text{Nitidez}}{1 + 0.15 \cdot |\text{Velocidad}|}$.

### 5.2 Asociación Geométrica Anatómica de 3 Zonas (`motor/asociar.py`)
Dada una caja de trabajador $P = (x_1, y_1, x_2, y_2)$ con ancho $W_p = x_2 - x_1$ y alto $H_p = y_2 - y_1$, toda detección candidata de prenda $D$ cuyo centro $(c_x, c_y)$ o área de intersección cae cerca de $P$ se proyecta a coordenadas relativas normalizadas:
$$\hat{x} = \frac{c_x - x_1}{W_p}, \quad \hat{y} = \frac{c_y - y_1}{H_p}$$

Cada una de las **3 prendas obligatorias** tiene una banda anatómica vertical permitida $[\hat{y}_{\min}, \hat{y}_{\max}]$ definida en `contrato.ZONAS_RELATIVAS`:
- **Zona 1 · Ojos (`lentes` / `sin_lentes`):** $\hat{y} \in [0.00, 0.32]$ (centro ideal $\hat{y}_0 = 0.16$)
- **Zona 2 · Torso (`chaleco` / `sin_chaleco`):** $\hat{y} \in [0.16, 0.72]$ (centro ideal $\hat{y}_0 = 0.44$)
- **Zona 3 · Manos (`guantes` / `sin_guantes`):** $\hat{y} \in [0.28, 0.96]$ (centro ideal $\hat{y}_0 = 0.62$)

Si para una misma zona existen tanto detecciones positivas (`lentes`) como negativas (`sin_lentes`), gana la de mayor confianza ponderada por cercanía anatómica; si la confianza ganadora es $< 0.60$ o no hubo ninguna lectura en la zona, el estado de esa prenda se marca como `"dudoso"` (que se traduce aguas arriba en `"revisar"` con `US$0.00`).

### 5.3 Rastreo Multi-Cuadro y Votación por Mayoría (`motor/rastreo.py`)
Un trabajador es observado en múltiples cuadros consecutivos mientras pasa frente a la cámara:
- `RastreadorPersonas` empareja detecciones entre cuadros mediante **IoU** ($\ge 0.25$) o cercanía de centros y suaviza la caja con media móvil exponencial (**EMA**, $\alpha = 0.35$).
- Al cerrar la trayectoria del trabajador, cada una de las 3 prendas (`lentes`, `chaleco`, `guantes`) se decide por **votación ponderada por confianza** a través de todos los cuadros donde fue visto, eliminando parpadeos de un solo frame.

---

## 6. Reglas de Negocio, Cruce Financiero y API Local (`cruce/`)

### 6.1 Catálogo del Sistema de Planta (`datos/sistema/`)
1. **[`turnos.csv`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/datos/sistema/turnos.csv):** Define los 12 trabajadores esperados en las 3 líneas del Turno Matutino 06:00 (`L1-T1` a `L3-T4`), su `id_empleado` (`EMP-101` a `EMP-304`), nombre, puesto y que cada uno requiere exactamente `lentes=1, chaleco=1, guantes=1`.
2. **[`inventario_epp.csv`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/datos/sistema/inventario_epp.csv):** Existencias disponibles en la caseta de entrada para entrega inmediata (`Lentes ANSI Z87.1: 18 pzs`, `Chaleco Clase 2: 12 pzs`, `Guantes Nivel A4: 24 pzs`).
3. **[`reglas_riesgo.csv`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/datos/sistema/reglas_riesgo.csv):** Exposición económica diaria por omisión:
   - `sin_lentes`: **US$420.00/día**
   - `sin_guantes`: **US$340.00/día**
   - `sin_chaleco`: **US$290.00/día**
   - `multiples_epp_faltantes`: **Suma del riesgo diario de cada prenda omitida** (p. ej. `L1-T2` sin lentes ni guantes = `US$420 + US$340 = US$760.00/día`; `L2-T4` sin lentes ni chaleco = `US$420 + US$290 = US$710.00/día`).
   - `revisar`: **US$0.00/día** (principio de honestidad operativa).

### 6.2 Resultado Exacto de la Corrida Demostrativa (`salida/hallazgos.json`)
- **Total de estaciones evaluadas:** `12` (`3 líneas × 4 estaciones`)
- **Trabajadores con EPP completo (3/3):** `4` (`L1-T1`, `L1-T3`, `L3-T1`, `L3-T4`) -> Cumplimiento `33.3 %`
- **Trabajadores con EPP incompleto (`error`):** `7` (`L1-T2`, `L1-T4`, `L2-T1`, `L2-T2`, `L2-T4`, `L3-T2`, `L3-T3`)
- **Lecturas dudosas (`revisar`):** `1` (`L2-T3 · Daniel Espinoza`, guantes con confianza `48 %` -> `US$0.00`)
- **Dinero en riesgo diario total:** **`US$3,280.00/día`** (`760 + 710 + 420 + 420 + 340 + 340 + 290`)
- **Precisión del motor medida con `herramientas/evaluar_motor.py`:** **`100.0 %` en las 12 estaciones, `0` falsos positivos**.

---

## 7. Arquitectura del Tablero Frontend (`Frontend/`)

Construido con **Next.js 15.1.7 (App Router)**, **React 19**, **TypeScript 5.7** y **Tailwind CSS 3.4**. Todas las rutas son dinámicas (`export const dynamic = 'force-dynamic'`) para reflejar al instante los cambios de corrida activa o las correcciones persistidas vía `PATCH`.

1. **`/resumen` ([`ResumenView.tsx`](file:///home/alexteori/Documentos/repositorios/EPP/Frontend/components/resumen/ResumenView.tsx)):** Frase hero obligatoria, KPIs de cumplimiento, desglose por familia de prenda, Top 3 de prioridad en caseta, mapa rápido 3×4 y **Modo Jurado en Vivo** con 4 tarjetas interactivas.
2. **`/kiosco` ([`KioscoView.tsx`](file:///home/alexteori/Documentos/repositorios/EPP/Frontend/components/kiosco/KioscoView.tsx)):** Cámara WebRTC en vivo, subida de fotografía y 5 presets instantáneos (`completo`, `sin_lentes`, `sin_guantes`, `sin_chaleco`, `incompleto_multiple`) conectados a `POST /motor/kiosco/evaluar`.
3. **`/recorrido` ([`RecorridoView.tsx`](file:///home/alexteori/Documentos/repositorios/EPP/Frontend/components/recorrido/RecorridoView.tsx)):** Reproductor de video anotado H.264 con salto directo al segundo y cuadro exacto de cada trabajador.
4. **`/cuadrilla` ([`CuadrillaView.tsx`](file:///home/alexteori/Documentos/repositorios/EPP/Frontend/components/cuadrilla/CuadrillaView.tsx)):** Matriz de las 3 líneas de formación a la izquierda y **Gemelo Anatómico SVG de 3 Zonas (`Ojos`, `Torso`, `Manos`)** con recorte fotográfico real y stock en caseta a la derecha.
5. **`/hallazgos` ([`HallazgosView.tsx`](file:///home/alexteori/Documentos/repositorios/EPP/Frontend/components/hallazgos/HallazgosView.tsx)):** Lista priorizada por `US$/día`, filtros por estado y por prenda (`Sin Lentes`, `Sin Chaleco`, `Sin Guantes`) y botón **"Autorizar tras entrega"** con persistencia real en disco (`PATCH`).
6. **`/red` ([`RedView.tsx`](file:///home/alexteori/Documentos/repositorios/EPP/Frontend/components/red/RedView.tsx)):** Simulador de contagio operativo en las **18 plantas** de la red (`Bajo 10 %`, `Central 25 %`, `Alto 50 %`, `Peor caso 100 %`), separando problemas sistémicos (`US$1,470/día`) de omisiones locales (`US$1,810/día`).
7. **`/analizar` ([`AnalizarView.tsx`](file:///home/alexteori/Documentos/repositorios/EPP/Frontend/components/analizar/AnalizarView.tsx)):** Carga de videos nuevos con barra de progreso en tiempo real y conmutación entre corridas.
8. **`/asistente` ([`AsistenteView.tsx`](file:///home/alexteori/Documentos/repositorios/EPP/Frontend/components/asistente/AsistenteView.tsx)):** Chat RAG con preguntas sugeridas y tarjetas de fuentes verificables (`[RESUMEN]`, `[H1]`, `[P2]`, etc.).
