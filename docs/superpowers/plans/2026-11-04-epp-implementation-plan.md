# Vigía EPP (Pre-Shift PPE Inspection System) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir **Vigía EPP** en `/home/alexteori/Documentos/repositorios/EPP`, perfeccionando la arquitectura de `ubik` para verificar que cada trabajador porte su EPP completo de 3 elementos (**Chaleco, Lentes de Seguridad y Guantes**, excluyendo casco y mascarilla) antes de iniciar su turno, entrenando un modelo YOLO11 con los 3 datasets de Kaggle e incluyendo Kiosco en Vivo, Gemelo Anatómico de 3 Zonas, Hallazgos Persistentes, Asistente RAG con Gemini y las herramientas/documentación requeridas.

**Architecture:** Sistema desacoplado en dos capas conectadas por contratos JSON (`observaciones.json`, `hallazgos.json`, `red.json`) y API HTTP local (`:8000`): (1) `motor-procesamiento/` en Python 3.12 (`uv`) con YOLO11 entrenado en 7 clases canónicas (`persona`, `chaleco`, `sin_chaleco`, `lentes`, `sin_lentes`, `guantes`, `sin_guantes`), asociación espacial por zonas anatómicas (`motor/asociar.py`), rastreo y votación multi-cuadro (`motor/rastreo.py`), evaluación instantánea para Kiosco (`motor/kiosco.py`) y cruce contra inventario/riesgo diario (`cruce/`); (2) `Frontend/` en Next.js 15 + React 19 + Tailwind CSS + Framer Motion con 8 pantallas offline-first y arranque unificado mediante `./iniciar.sh`.

**Tech Stack:** Python 3.12, `uv`, Ultralytics YOLO11 (`torch` CUDA para RTX 4050 / CPU), OpenCV, Next.js 15, React 19, TypeScript, Tailwind CSS, Framer Motion, Lucide React, `@fontsource/inter`, `ui-ux-pro-max-cli`, `@fission-ai/openspec`, `ui-skills`, `impeccable`, `@playwright/cli`, `headroom-ai`, Gemini API (RAG).

**Spec:** `docs/superpowers/specs/2026-11-04-epp-design.md`

## Global Constraints

- **Sin casco ni mascarilla:** Solo se evalúan 3 equipos obligatorios: `lentes` (ojos/cabeza), `chaleco` (torso) y `guantes` (manos). Las 7 clases del detector son `0: persona`, `1: chaleco`, `2: sin_chaleco`, `3: lentes`, `4: sin_lentes`, `5: guantes`, `6: sin_guantes`.
- **Honestidad con lo dudoso:** Confianza `< 0.60`, menos de 2 lecturas coincidentes en video o zona anatómica fuera de cuadro se clasifica como `revisar` (Ámbar) con `impacto_diario = 0.0`.
- **100% funcional offline:** El tablero debe renderizar todas las pantallas usando `Frontend/public/salida/` aunque la API en `:8000` esté apagada; las fuentes tipográficas son locales (`@fontsource/inter`).
- **Persistencia real:** Marcar un hallazgo como corregido/autorizado actualiza el archivo en disco vía `PATCH /analisis/<id>/hallazgos/<hallazgo_id>` (y persiste al recargar).
- **Entregables documentales obligatorios:** `documentacion.md` (documentación técnica exhaustiva) y `memoria.md` (memoria compacta optimizada en tokens para IAs futuras) en la raíz del proyecto.

## Review Focus

1. **Manos o torso recortados por el borde del encuadre:** Si la caja de `persona` está cortada abajo (`y2 >= alto * 0.98`) y no se detectan `guantes` ni `sin_guantes`, la zona `guantes` debe salir como `dudoso` (`revisar`), nunca como `falta` confirmada.
2. **Detección simultánea de `chaleco` y `sin_chaleco` en la misma persona:** `motor/asociar.py` debe resolver por mayor confianza ponderada por IoU dentro de la franja anatómica del torso, y si ambas confianzas difieren en `< 0.15`, marcar `dudoso`.
3. **Imagen vacía o sin personas en el Kiosco en Vivo (`POST /kiosco/evaluar`):** Debe responder HTTP 200 con `personas_detectadas: 0`, `estado_acceso: "sin_persona"` y mensaje claro sin lanzar excepción 500.
4. **Desduplicación entre `shlokraval` (v4) y `slimese` (v1):** `entrenamiento/preparar_epp.py` debe calcular hash del contenido visual o nombre base antes del hash `.rf.` de Roboflow para impedir que la misma imagen base caiga en `train` y en `val`.
5. **Persistencia de corrección en modo demo (`PATCH /analisis/demo/hallazgos/<id>`):** Debe actualizar `hallazgos.json` y recalcular `dinero_en_riesgo_diario` o mantener `corregido: true` de forma atómica sin corromper el JSON ante peticiones concurrentes.

---

### Task 1: Herramientas del Ecosistema, Estructura Base y Contrato de Datos (`motor/contrato.py`)

**Files:**
- Create: `.gitignore`, `.env.example`, `motor-procesamiento/requirements.txt`, `motor-procesamiento/CONTRATO.md`
- Create: `motor-procesamiento/motor/__init__.py`, `motor-procesamiento/motor/contrato.py`
- Create: `motor-procesamiento/datos/sistema/turnos.csv`, `motor-procesamiento/datos/sistema/inventario_epp.csv`, `motor-procesamiento/datos/sistema/reglas_riesgo.csv`
- Test: `motor-procesamiento/tests/test_contrato.py`

**Interfaces:**
- Produces:
  - `motor.contrato.CLASES: tuple[str, ...]` = `("persona", "chaleco", "sin_chaleco", "lentes", "sin_lentes", "guantes", "sin_guantes")`
  - `motor.contrato.PRENDAS: tuple[str, ...]` = `("lentes", "chaleco", "guantes")`
  - `motor.contrato.TrabajadorTurno(posicion: str, linea: str, id_empleado: str, nombre: str, puesto: str, orden: int, prendas_requeridas: tuple[str, ...])`
  - `motor.contrato.leer_turnos(ruta: str | Path) -> list[TrabajadorTurno]`

- [ ] **Step 1: Inicializar herramientas y plugins solicitados (`openspec`, `ui-ux-pro-max-cli`, `superpowers`, `@playwright/cli`, `headroom-ai`) y entorno Python 3.12 (`uv`)**

Run:
```bash
cd /home/alexteori/Documentos/repositorios/EPP
npx --yes ui-ux-pro-max-cli init --ai antigravity || true
npx --yes @fission-ai/openspec@latest init --tools none || true
/home/alexteori/.local/bin/agy plugin install https://github.com/obra/superpowers || true
npm install -g @playwright/cli@latest || true
uv tool install --python 3.12 "headroom-ai[all]" || true
```
Expected: Directorios de configuración creados y herramientas instaladas o verificadas.

- [ ] **Step 2: Write the failing test in `motor-procesamiento/tests/test_contrato.py`**

```python
from pathlib import Path
from motor import contrato

def test_clases_y_prendas_sin_casco_ni_mascarilla():
    assert contrato.PRENDAS == ("lentes", "chaleco", "guantes")
    assert "casco" not in contrato.CLASES
    assert "mascarilla" not in contrato.CLASES
    assert len(contrato.CLASES) == 7

def test_leer_turnos(tmp_path: Path):
    csv_file = tmp_path / "turnos.csv"
    csv_file.write_text(
        "posicion,linea,id_empleado,nombre,puesto,orden\n"
        "L1-T1,L1,EMP-101,Carlos Mendoza,Operador CNC,1\n",
        encoding="utf-8",
    )
    turnos = contrato.leer_turnos(csv_file)
    assert len(turnos) == 1
    assert turnos[0].posicion == "L1-T1"
    assert turnos[0].prendas_requeridas == ("lentes", "chaleco", "guantes")
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd /home/alexteori/Documentos/repositorios/EPP/motor-procesamiento && .venv/bin/python -m pytest tests/test_contrato.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'motor'`

- [ ] **Step 4: Implement `motor/contrato.py`, `CONTRATO.md` and CSV system files in `datos/sistema/`**

Define `CLASES`, `PRENDAS`, anatomical zone constants (`ZONA_LENTES = (0.0, 0.30)`, `ZONA_CHALECO = (0.18, 0.72)`, `ZONA_GUANTES = (0.30, 0.96)`), `TrabajadorTurno`, `leer_turnos`, and populate `datos/sistema/{turnos.csv,inventario_epp.csv,reglas_riesgo.csv}` for 12 shift positions (`L1-T1`..`L3-T4`).

- [ ] **Step 5: Run test to verify it passes and commit**

Run: `cd /home/alexteori/Documentos/repositorios/EPP/motor-procesamiento && .venv/bin/python -m pytest tests/test_contrato.py -v`
Expected: PASS

---

### Task 2: Descarga de los 3 Datasets de Kaggle, Armonización a 7 Clases y Entrenamiento YOLO11 (`entrenamiento/`)

**Files:**
- Create: `motor-procesamiento/entrenamiento/__init__.py`
- Create: `motor-procesamiento/entrenamiento/descargar_kaggle.py`
- Create: `motor-procesamiento/entrenamiento/preparar_epp.py`
- Create: `motor-procesamiento/entrenamiento/comun.py`
- Create: `motor-procesamiento/entrenamiento/entrenar_yolo.py`
- Test: `motor-procesamiento/tests/test_preparar_epp.py`

**Interfaces:**
- Consumes: `motor.contrato.CLASES`
- Produces:
  - `entrenamiento.preparar_epp.mapear_etiqueta_linea(linea: str, nombres_origen: list[str]) -> str | None`
  - `entrenamiento.preparar_epp.clave_base_roboflow(nombre_archivo: str) -> str`
  - `modelos/epp.pt` and `modelos/epp.json`

- [ ] **Step 1: Write the failing test in `motor-procesamiento/tests/test_preparar_epp.py`**

```python
from entrenamiento.preparar_epp import mapear_etiqueta_linea, clave_base_roboflow

def test_mapear_etiqueta_descarta_casco_y_mascarilla():
    nombres_ndomalau = ["helmet", "no_helmet", "no_vest", "person", "vest"]
    assert mapear_etiqueta_linea("0 0.5 0.5 0.2 0.2", nombres_ndomalau) is None  # helmet descartado
    assert mapear_etiqueta_linea("1 0.5 0.5 0.2 0.2", nombres_ndomalau) is None  # no_helmet descartado
    assert mapear_etiqueta_linea("3 0.5 0.5 0.4 0.8", nombres_ndomalau) == "0 0.5 0.5 0.4 0.8"  # person -> 0
    assert mapear_etiqueta_linea("4 0.5 0.5 0.3 0.4", nombres_ndomalau) == "1 0.5 0.5 0.3 0.4"  # vest -> 1
    assert mapear_etiqueta_linea("2 0.5 0.5 0.3 0.4", nombres_ndomalau) == "2 0.5 0.5 0.3 0.4"  # no_vest -> 2

def test_mapear_etiqueta_shlokraval_y_slimese():
    nombres_14 = [
        "Fall-Detected", "Gloves", "Goggles", "Hardhat", "Ladder", "Mask",
        "NO-Gloves", "NO-Goggles", "NO-Hardhat", "NO-Mask", "NO-Safety Vest",
        "Person", "Safety Cone", "Safety Vest",
    ]
    assert mapear_etiqueta_linea("2 0.5 0.2 0.1 0.1", nombres_14) == "3 0.5 0.2 0.1 0.1"  # Goggles -> 3
    assert mapear_etiqueta_linea("7 0.5 0.2 0.1 0.1", nombres_14) == "4 0.5 0.2 0.1 0.1"  # NO-Goggles -> 4
    assert mapear_etiqueta_linea("1 0.4 0.7 0.1 0.1", nombres_14) == "5 0.4 0.7 0.1 0.1"  # Gloves -> 5
    assert mapear_etiqueta_linea("6 0.4 0.7 0.1 0.1", nombres_14) == "6 0.4 0.7 0.1 0.1"  # NO-Gloves -> 6
    assert mapear_etiqueta_linea("5 0.5 0.2 0.1 0.1", nombres_14) is None                 # Mask descartado

def test_clave_base_roboflow_evita_fuga_entre_v1_y_v4():
    assert clave_base_roboflow("000005_jpg.rf.fc2bef6376.jpg") == "000005_jpg"
    assert clave_base_roboflow("000005_jpg.rf.aaaaaaaaaa.jpg") == "000005_jpg"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/alexteori/Documentos/repositorios/EPP/motor-procesamiento && .venv/bin/python -m pytest tests/test_preparar_epp.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'entrenamiento'`

- [ ] **Step 3: Implement `entrenamiento/descargar_kaggle.py`, `entrenamiento/preparar_epp.py`, `entrenamiento/comun.py`, and `entrenamiento/entrenar_yolo.py`**

`descargar_kaggle.py` downloads `ndomalau/personal-protective-equipment-ppe-dataset` and extracts balanced subsets from `shlokraval/ppe-dataset-yolov8` and `slimese/personal-protective-equipment` (supporting both full archive download and streaming ZIP extraction via Kaggle API/MCP so all 3 datasets contribute real images and annotations without filling the disk with 15 GB of redundant copies). `preparar_epp.py` harmonizes annotations to the 7 classes and deduplicates by `clave_base_roboflow` + SHA1. `entrenar_yolo.py` trains `yolo11n.pt` on the RTX 4050 GPU and saves `modelos/epp.pt` + `modelos/epp.json`.

- [ ] **Step 4: Run pytest and execute dataset preparation + YOLO11 training**

Run:
```bash
cd /home/alexteori/Documentos/repositorios/EPP/motor-procesamiento
.venv/bin/python -m pytest tests/test_preparar_epp.py -v
.venv/bin/python -m entrenamiento.descargar_kaggle
.venv/bin/python -m entrenamiento.preparar_epp
.venv/bin/python -m entrenamiento.entrenar_yolo
```
Expected: All tests PASS; `modelos/epp.pt` and `modelos/epp.json` exist with validation mAP50 metrics.

---

### Task 3: Motor de Visión — Cuadros Nítidos, Asociación Anatómica de 3 Zonas y Votación Multi-Cuadro (`motor/`)

**Files:**
- Create: `motor-procesamiento/motor/cuadros.py`
- Create: `motor-procesamiento/motor/detector.py`
- Create: `motor-procesamiento/motor/asociar.py`
- Create: `motor-procesamiento/motor/rastreo.py`
- Test: `motor-procesamiento/tests/test_asociar_rastreo.py`

**Interfaces:**
- Consumes: `motor.contrato.{CLASES, PRENDAS}`
- Produces:
  - `motor.detector.Deteccion(clase: str, confianza: float, caja: tuple[float, float, float, float])`
  - `motor.asociar.EstadoPrenda(estado: str, confianza: float, caja: tuple[float, float, float, float] | None)` (`estado` in `("ok", "falta", "dudoso")`)
  - `motor.asociar.PersonaAsociada(caja: tuple[float, float, float, float], confianza: float, prendas: dict[str, EstadoPrenda])`
  - `motor.asociar.asociar_cuadro(detecciones: list[Deteccion], ancho: int, alto: int) -> list[PersonaAsociada]`
  - `motor.rastreo.RastreadorTurno` and `votar_trabajador(vistas: list[PersonaAsociada]) -> dict`

- [ ] **Step 1: Write the failing test in `motor-procesamiento/tests/test_asociar_rastreo.py`**

Include tests for:
1. Full PPE worker (`persona` + `lentes` in head zone + `chaleco` in torso zone + `guantes` in hand zone) → all 3 `ok`.
2. Worker missing goggles and gloves (`sin_lentes` and `sin_guantes` inside anatomical zones) → `lentes: falta`, `guantes: falta`, `chaleco: ok`.
3. Worker whose hands are cut off at bottom of frame (`y2 >= alto * 0.98`) with no glove detections → `guantes: dudoso` (Review Focus #1).
4. Conflicting `chaleco` (conf 0.62) and `sin_chaleco` (conf 0.58) on same torso → `chaleco: dudoso` (Review Focus #2).
5. Multi-frame voting across 5 frames.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/alexteori/Documentos/repositorios/EPP/motor-procesamiento && .venv/bin/python -m pytest tests/test_asociar_rastreo.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'motor.asociar'`

- [ ] **Step 3: Implement `motor/cuadros.py`, `motor/detector.py`, `motor/asociar.py`, and `motor/rastreo.py`**

- [ ] **Step 4: Run test to verify it passes and commit**

Run: `cd /home/alexteori/Documentos/repositorios/EPP/motor-procesamiento && .venv/bin/python -m pytest tests/test_asociar_rastreo.py -v`
Expected: PASS

---

### Task 4: Kiosco en Vivo, Anotador de Video, Simulador de Recorrido de Turno y Pipeline Principal (`motor/` + `simulador/`)

**Files:**
- Create: `motor-procesamiento/motor/kiosco.py`
- Create: `motor-procesamiento/motor/anotar.py`
- Create: `motor-procesamiento/motor/pipeline.py`
- Create: `motor-procesamiento/simulador/__init__.py`, `motor-procesamiento/simulador/datos_prueba.py`, `motor-procesamiento/simulador/render_turno.py`, `motor-procesamiento/simulador/tarjetas.py`
- Create: `motor-procesamiento/herramientas/__init__.py`, `motor-procesamiento/herramientas/evaluar_motor.py`
- Test: `motor-procesamiento/tests/test_kiosco_pipeline.py`

**Interfaces:**
- Consumes: `motor.{contrato, cuadros, detector, asociar, rastreo}`
- Produces:
  - `motor.kiosco.evaluar_imagen(imagen_bgr: np.ndarray, detector: DetectorEPP | None = None) -> dict`
  - `motor.pipeline.procesar(video: str, ruta_turnos: str, salida: str, ...) -> dict` (writes `observaciones.json`, `diagnostico.json`, `recorrido_anotado.mp4`, `recortes/*.jpg`)

- [ ] **Step 1: Write the failing test in `motor-procesamiento/tests/test_kiosco_pipeline.py`**

Test `evaluar_imagen` on an empty image (`personas_detectadas == 0`, `estado_acceso == "sin_persona"`, Review Focus #3) and with a mocked/real person detection returning `estado_acceso` in `("autorizado", "bloqueado", "revisar")` and `zonas` for `lentes`, `chaleco`, `guantes`.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/alexteori/Documentos/repositorios/EPP/motor-procesamiento && .venv/bin/python -m pytest tests/test_kiosco_pipeline.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'motor.kiosco'`

- [ ] **Step 3: Implement `motor/kiosco.py`, `motor/anotar.py`, `motor/pipeline.py`, `simulador/`, and `herramientas/evaluar_motor.py`**

`simulador/render_turno.py` builds the pre-shift inspection video (`video/recorrido_turno.mp4`) and the 4 Jury Mode cards (`video/tarjetas/{sin_lentes,sin_guantes,sin_chaleco,epp_agotado}.mp4`) using real held-out test images from the Kaggle datasets placed into the 12 shift stations (`L1-T1`..`L3-T4`), with ground-truth annotations in `escena/escena.json`.

- [ ] **Step 4: Run pytest, generate shift demo videos, run `motor.pipeline` and `herramientas.evaluar_motor`**

Run:
```bash
cd /home/alexteori/Documentos/repositorios/EPP/motor-procesamiento
.venv/bin/python -m pytest tests/test_kiosco_pipeline.py -v
.venv/bin/python -m simulador.datos_prueba
.venv/bin/python -m simulador.render_turno
.venv/bin/python -m simulador.tarjetas
.venv/bin/python -m motor.pipeline --video video/recorrido_turno.mp4 --turnos datos/sistema/turnos.csv --salida salida/
.venv/bin/python -m herramientas.evaluar_motor --observaciones salida/observaciones.json --escena escena/escena.json
```
Expected: All tests PASS, `salida/observaciones.json` and `salida/recorrido_anotado.mp4` generated.

---

### Task 5: Cruce contra Sistema, Impacto Económico/Red, Persistencia, Asistente RAG y API (`cruce/`)

**Files:**
- Create: `motor-procesamiento/cruce/__init__.py`
- Create: `motor-procesamiento/cruce/hallazgos.py`
- Create: `motor-procesamiento/cruce/red.py`
- Create: `motor-procesamiento/cruce/publicar.py`
- Create: `motor-procesamiento/cruce/chat.py`
- Create: `motor-procesamiento/cruce/api.py`
- Test: `motor-procesamiento/tests/test_cruce_api_chat.py`

**Interfaces:**
- Consumes: `salida/observaciones.json`, `datos/sistema/{turnos.csv,inventario_epp.csv,reglas_riesgo.csv}`
- Produces:
  - `cruce.hallazgos.construir(obs: dict, sistema: Sistema, ...) -> dict`
  - `cruce.red.construir(hallazgos_data: dict, ...) -> dict`
  - HTTP API on `:8000`:
    - `GET /salud`
    - `POST /kiosco/evaluar` (evaluates image/webcam frame or demo preset in `<300 ms`)
    - `POST /procesar` & `GET /estado` & `GET /tarjetas` (Jury Mode)
    - `POST /analisis`, `GET /analisis`, `GET /analisis/<id>`, `GET /analisis/activo`, `GET /analisis/activo/red`
    - `PATCH /analisis/<id>/hallazgos/<hallazgo_id>` (persists `corregido: true|false` to disk — Review Focus #5)
    - `POST /analisis/<id>/chat` & `GET /chat` (Gemini RAG assistant)

- [ ] **Step 1: Write the failing tests in `motor-procesamiento/tests/test_cruce_api_chat.py`**

Test all 6 classification rules (`epp_faltante_agotado`, `multiples_epp_faltantes`, `sin_lentes`, `sin_guantes`, `sin_chaleco`, `revisar`), money calculations (`revisar` = US$0.00), plant network projection (`red.py` projecting only `epp_faltante_agotado` systemic stockouts), persistent `PATCH /analisis/demo/hallazgos/<id>` updating disk state atomically, `POST /kiosco/evaluar`, and `chat.py` RAG chunking.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/alexteori/Documentos/repositorios/EPP/motor-procesamiento && .venv/bin/python -m pytest tests/test_cruce_api_chat.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'cruce'`

- [ ] **Step 3: Implement `cruce/hallazgos.py`, `cruce/red.py`, `cruce/publicar.py`, `cruce/chat.py`, and `cruce/api.py`**

- [ ] **Step 4: Run full Python test suite**

Run: `cd /home/alexteori/Documentos/repositorios/EPP/motor-procesamiento && .venv/bin/python -m pytest -v`
Expected: 100% PASS across all Python unit and integration tests.

---

### Task 6: Tablero Next.js 15 Industrial Safety (`Frontend/`) + `./iniciar.sh` + Verificación E2E con Playwright

**Files:**
- Create: `Frontend/package.json`, `Frontend/tsconfig.json`, `Frontend/tailwind.config.ts`, `Frontend/next.config.ts`, `Frontend/postcss.config.mjs`, `Frontend/DISENO.md`
- Create: `Frontend/types/{hallazgos.ts,analisis.ts,red.ts,kiosco.ts}`
- Create: `Frontend/lib/{data/loader.ts,api/analisis.ts,formatters/contract.ts}`
- Create: `Frontend/components/layout/{Sidebar.tsx,Header.tsx,TituloPagina.tsx}`, `Frontend/components/iconos.ts`, `Frontend/components/graficas/Barras.tsx`
- Create: `Frontend/components/resumen/ResumenView.tsx`
- Create: `Frontend/components/kiosco/KioscoView.tsx`
- Create: `Frontend/components/recorrido/RecorridoView.tsx`
- Create: `Frontend/components/cuadrilla/CuadrillaView.tsx`
- Create: `Frontend/components/hallazgos/HallazgosView.tsx`
- Create: `Frontend/components/red/RedView.tsx`
- Create: `Frontend/components/analizar/AnalizarView.tsx`
- Create: `Frontend/components/asistente/AsistenteView.tsx`
- Create: `Frontend/app/{layout.tsx,page.tsx,globals.css,resumen/page.tsx,kiosco/page.tsx,recorrido/page.tsx,cuadrilla/page.tsx,hallazgos/page.tsx,red/page.tsx,analizar/page.tsx,asistente/page.tsx}`
- Create: `iniciar.sh`, `Frontend/tests/e2e.mjs`

- [ ] **Step 1: Initialize Next.js 15 project in `Frontend/`, install `framer-motion`, `lucide-react`, `@fontsource/inter`, `ui-skills` & `impeccable`**

Run:
```bash
cd /home/alexteori/Documentos/repositorios/EPP/Frontend
npm install
npx --yes ui-skills init --yes || true
npx --yes impeccable install || true
```

- [ ] **Step 2: Publish engine output to `Frontend/public/` (`python -m cruce.publicar --web ../Frontend/public`)**

- [ ] **Step 3: Implement all 8 screens (`Resumen`, `Kiosco en Vivo`, `Recorrido`, `Cuadrilla / Gemelo Anatómico 3-Zonas`, `Hallazgos Persistentes`, `Impacto en Red`, `Subir Video`, `Asistente IA`) and `./iniciar.sh`**

Ensure neither `Casco` nor `Mascarilla` appear as required items; the 3-Zone Anatomical Twin highlights **Lentes (Ojos)**, **Chaleco (Torso)**, and **Guantes (Manos)** with real evidence crops, and clicking *"Autorizar / Marcar corregido"* in `HallazgosView` and `CuadrillaView` persists via `PATCH /motor/analisis/.../hallazgos/...`.

- [ ] **Step 4: Build Frontend (`npm run build`) and run Playwright E2E test (`Frontend/tests/e2e.mjs`) verifying all 8 routes, Live Kiosk evaluation, and persistent finding resolution**

Run:
```bash
cd /home/alexteori/Documentos/repositorios/EPP/Frontend
npm run typecheck && npm run build
node tests/e2e.mjs
```
Expected: Next.js build succeeds cleanly and Playwright E2E script passes all checks.

---

### Task 7: Documentación Maestra (`README.md`, `PITCH.md`, `documentacion.md`, `memoria.md`)

**Files:**
- Create: `README.md`, `PITCH.md`, `motor-procesamiento/README.md`
- Create: `documentacion.md` (documentación técnica exhaustiva del proyecto: qué se usó, por qué, arquitectura, contratos, datasets de Kaggle, entrenamiento YOLO11, matemáticas de asociación y cruce, diseño visual y pruebas)
- Create: `memoria.md` (memoria ultra-estructurada de rápido acceso y bajo consumo de tokens para IAs futuras al hacer cambios o mejoras)

- [ ] **Step 1: Write `README.md`, `PITCH.md`, and `motor-procesamiento/README.md` with real benchmark metrics from `modelos/epp.json` and `salida/hallazgos.json`**

- [ ] **Step 2: Write `documentacion.md` and `memoria.md` in the repository root**

- [ ] **Step 3: Verify all files, run full test suites (`pytest` + `npm run build` + `e2e.mjs`), and commit**
