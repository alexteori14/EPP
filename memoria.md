# Memoria Técnica de Contexto Rápido para IA — Vigía EPP (`memoria.md`)

> **Propósito:** Este documento está diseñado específicamente para que tú (u otra IA en sesiones futuras) recuperes el **100 % del contexto arquitectónico, contratos, funciones, rutas, constantes y métodos** de **Vigía EPP** en una sola lectura, sin gastar tokens abriendo docenas de archivos.

---

## 1. Invariantes Críticas del Dominio (NUNCA ROMPER)

1. **EXCLUSIÓN ABSOLUTA DE CASCO Y MASCARILLA:**
   - En la planta donde opera el software **NO se pide casco (`casco`) ni mascarilla (`mascarilla`)**.
   - Solo existen **3 prendas obligatorias** en todo el sistema (`motor.contrato.PRENDAS`):
     - `"lentes"` (Lentes Policarbonato Anti-Impacto ANSI Z87.1) $\rightarrow$ Riesgo diario: **`US$420.00/día`** · Stock en caseta: **`18`** · Paro: **`US$950.00`**
     - `"chaleco"` (Chaleco Reflejante Clase 2 Alta Visibilidad) $\rightarrow$ Riesgo diario: **`US$290.00/día`** · Stock en caseta: **`12`** · Paro: **`US$820.00`**
     - `"guantes"` (Guantes Nitrilo Anticorte Nivel A4) $\rightarrow$ Riesgo diario: **`US$340.00/día`** · Stock en caseta: **`24`** · Paro: **`US$880.00`**
2. **ESQUEMA CANÓNICO DE 7 CLASES YOLO11 (`motor.contrato.CLASES`):**
   - `0: "persona"`
   - `1: "chaleco"`
   - `2: "sin_chaleco"`
   - `3: "lentes"`
   - `4: "sin_lentes"`
   - `5: "guantes"`
   - `6: "sin_guantes"`
3. **PRINCIPIO DE HONESTIDAD OPERATIVA (`dudoso` / `revisar` = `US$0.00`):**
   - Cuando una zona anatómica está cortada por el borde del encuadre, tiene confianza `< 0.55` (`CONFIANZA_MINIMA_PRENDA`) o hay empate técnico entre clase positiva y negativa (`abs(conf_pos - conf_neg) < 0.15`, `UMBRAL_CONFLICTO_DUDA`), el estado de la prenda es `"dudoso"` y el hallazgo se clasifica como `"revisar"` con **`impacto_diario = 0.0`**.

---

## 2. Resumen de Qué se Hizo, Cómo se Hizo y Con Qué Métodos

### 2.1 Metodología y Plugins Aplicados
- **Análisis y Perfeccionamiento de `ubik` (`/home/alexteori/Documentos/repositorios/ubik`):**
  - Se conservó la separación en 3 capas (`motor/` $\rightarrow$ `cruce/` $\rightarrow$ `Frontend/`) unidas por contratos JSON y el selector de cuadros nítidos por varianza del Laplaciano.
  - Se corrigieron las 4 debilidades de `ubik`:
    1. **Persistencia transaccional en disco (`PATCH /analisis/<id>/hallazgos/<h_id>`):** A diferencia de `ubik` (donde *"Marcar corregido"* solo cambiaba un `useState` temporal), `cruce.hallazgos.actualizar_corregido()` persiste el cambio en disco (`.tmp` + `replace`) tanto en `motor-procesamiento/salida/hallazgos.json` como en `Frontend/public/salida/hallazgos.json` y regenera `red.json`.
    2. **Asistente RAG Híbrido Offline/Online (`cruce/chat.py`):** Funciona con Gemini (`gemini-2.5-flash`) si hay `APIGEMINI` en `.env`, y cae automáticamente a `_responder_rag_local()` (motor RAG determinista local sobre los fragmentos verificados de la corrida) cuando no hay llave o internet.
    3. **Kiosco de Torniquete en Vivo `< 300 ms` (`motor/kiosco.py` + `/kiosco`):** Evalúa cámara WebRTC, fotos o 5 presets en **`~3.3 ms`** en GPU.
    4. **Asociación Geométrica Anatómica de 3 Zonas (`motor/asociar.py`) + Gemelo Anatómico SVG (`SiluetaAnatomica3Zonas` en `CuadrillaView.tsx`).**
- **Stack de Herramientas Instaladas en el Proyecto:**
  - `ui-ux-pro-max-cli` (`.agents/skills/`), `@fission-ai/openspec` (`openspec/`), `obra/superpowers` (ciclo SDD + TDD), `framer-motion`, `ui-skills`, `impeccable`, `@playwright/cli` (`Frontend/tests/e2e.mjs`), `headroom-ai`.

---

## 3. Mapa Exacto de Módulos, Clases y Firmas de Funciones

### 3.1 Capa de Entrenamiento (`motor-procesamiento/entrenamiento/`)
- **[`entrenamiento/descargar_kaggle.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/entrenamiento/descargar_kaggle.py):**
  - Descarga muestras de los 3 datasets de Kaggle (`ndomalau/personal-protective-equipment-ppe-dataset`, `shlokraval/ppe-dataset-yolov8`, `slimese/personal-protective-equipment`) hacia `motor-procesamiento/datos_kaggle/`.
- **[`entrenamiento/preparar_epp.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/entrenamiento/preparar_epp.py):**
  - `MAPEO_NOMBRES: dict[str, int]` $\rightarrow$ mapea nombres en inglés a índices `0..6` y descarta cascos/mascarillas.
  - `clave_base_roboflow(nombre_archivo: str) -> str` $\rightarrow$ corta `.rf.<hash>` para evitar fuga de imágenes entre `shlokraval` (v4) y `slimese` (v1).
  - `mapear_etiqueta_linea(linea: str, nombres_origen: list[str]) -> str | None`
  - `mapear_texto_anotacion(texto: str, nombres_origen: list[str]) -> tuple[str, set[int]]`
  - `preparar_dataset(dir_kaggle="datos_kaggle", dir_salida="datasets/epp", semilla=42) -> dict` $\rightarrow$ genera `datasets/epp/data.yaml` (`658 train`, `164 val`, `75 test`).
- **[`entrenamiento/entrenar_yolo.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/entrenamiento/entrenar_yolo.py):**
  - Entrena `yolo11n.pt` en GPU y exporta [`modelos/epp.pt`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/modelos/epp.pt) y [`modelos/epp.json`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/modelos/epp.json) (`mAP50: 0.672`, `persona: 0.9411`, `chaleco: 0.8676`, `sin_chaleco: 0.7550`, `guantes: 0.6804`, `sin_lentes: 0.5272`, `sin_guantes: 0.5140`, `lentes: 0.4188`).

### 3.2 Capa del Motor de Visión (`motor-procesamiento/motor/`)
- **[`motor/contrato.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/motor/contrato.py):**
  - `CLASES = ("persona", "chaleco", "sin_chaleco", "lentes", "sin_lentes", "guantes", "sin_guantes")`
  - `PRENDAS = ("lentes", "chaleco", "guantes")`
  - `CLASE_POSITIVA = {"lentes": "lentes", "chaleco": "chaleco", "guantes": "guantes"}`
  - `CLASE_NEGATIVA = {"lentes": "sin_lentes", "chaleco": "sin_chaleco", "guantes": "sin_guantes"}`
  - `ZONAS_ANATOMICAS = {"lentes": (0.00, 0.32), "chaleco": (0.16, 0.72), "guantes": (0.28, 0.96)}`
  - `MARGEN_X_ZONA = {"lentes": 0.05, "chaleco": 0.08, "guantes": 0.18}`
  - `NOMBRES_PRENDA = {"lentes": "Lentes de seguridad", "chaleco": "Chaleco reflejante", "guantes": "Guantes anticorte"}`
  - `@dataclass(frozen=True) class TrabajadorTurno(posicion, linea, id_empleado, nombre, puesto, orden, prendas_requeridas=PRENDAS)`
  - `leer_turnos(ruta: str | Path) -> list[TrabajadorTurno]`
- **[`motor/cuadros.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/motor/cuadros.py):**
  - `info_video(ruta: str) -> InfoVideo(cuadros, fps, ancho, alto, segundos)`
  - `nitidez_laplaciano(bgr: np.ndarray) -> float`
  - `elegir_cuadros(ruta: str, cada: int = 12) -> Iterator[CuadroElegido]`
  - `elegir_cuadros_en_hilo(ruta: str, cada: int = 12, buffer: int = 4) -> Iterator[CuadroElegido]`
- **[`motor/detector.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/motor/detector.py):**
  - `class DetectorEPP(ruta_modelo="modelos/epp.pt", imgsz=640, confianza=0.25, dispositivo="auto")`
  - `DetectorEPP.detectar(imagenes: list[np.ndarray]) -> list[list[Deteccion]]`
- **[`motor/asociar.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/motor/asociar.py):**
  - `CONFIANZA_MINIMA_PRENDA = 0.55`, `UMBRAL_CONFLICTO_DUDA = 0.15`
  - `Deteccion(clase, confianza, caja)`, `EstadoPrenda(estado, confianza, caja)`, `PersonaAsociada(caja, confianza, prendas, cuadro)`
  - `asociar_cuadro(detecciones: list[Deteccion], ancho: int, alto: int, cuadro: int = 0) -> list[PersonaAsociada]`
- **[`motor/rastreo.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/motor/rastreo.py):**
  - `class RastreadorTurno(iou_minimo=0.25, max_brecha_cuadros=36)` con `.actualizar(personas, cuadro)` y `.pistas_ordenadas()`
  - `votar_trabajador(vistas: list[PersonaAsociada]) -> dict`
- **[`motor/anotar.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/motor/anotar.py):**
  - `dibujar_persona(img_bgr, persona, titulo) -> np.ndarray`
  - `recortar_persona_y_zona(img_bgr, persona) -> tuple[np.ndarray, np.ndarray]`
  - `recodificar_h264(ruta_mp4: Path)`
- **[`motor/kiosco.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/motor/kiosco.py):**
  - `evaluar_imagen(imagen_bgr: np.ndarray, detector: DetectorEPP | None = None, modelo: str = "modelos/epp.pt") -> dict`
  - Llaves devueltas: `personas_detectadas`, `estado_acceso` (`"autorizado" | "bloqueado" | "revisar" | "sin_persona"`), `mensaje`, `prendas_completas`, `prendas_requeridas`, `faltantes`, `dudosas`, `zonas`, `accion_caseta`, `ms_proceso`, `imagen_anotada_b64`.
- **[`motor/pipeline.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/motor/pipeline.py):**
  - `procesar(video, ruta_turnos, salida, modelo="modelos/epp.pt", cada=10, dispositivo="auto", imgsz=640, confianza=0.25, con_video=True, progreso=None) -> dict`

### 3.3 Capa de Cruce, Reglas, RAG y Servidor HTTP (`motor-procesamiento/cruce/`)
- **[`cruce/hallazgos.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/cruce/hallazgos.py):**
  - `leer_sistema(dir_sistema) -> Sistema(turnos, inventario, reglas)`
  - `clasificar(o, t, sistema) -> str | None` $\rightarrow$ devuelve `"epp_faltante_agotado"`, `"multiples_epp_faltantes"`, `"sin_lentes"`, `"sin_chaleco"`, `"sin_guantes"`, `"revisar"` o `None`.
  - `impacto_diario(tipo, o, t, sistema) -> float`
  - `construir(obs, sistema, fps=24.0, prefijo="/salida", ...) -> dict`
  - `actualizar_corregido(ruta_json: Path, hallazgo_id: str, corregido: bool) -> dict | None`
  - `desde_carpeta(dir_motor, sistema, prefijo="/salida", **opciones) -> dict`
  - `nuevos(base: dict, otro: dict) -> list[dict]`
- **[`cruce/red.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/cruce/red.py):**
  - `construir(datos_hallazgos: dict, plantas_total: int = 18, dias_mes: int = 30) -> dict`
- **[`cruce/publicar.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/cruce/publicar.py):**
  - `publicar(dir_salida=Path("salida"), dir_tarjetas=Path("salida_tarjetas"), dir_sistema=Path("datos/sistema"), dir_web=Path("../Frontend/public"))`
- **[`cruce/chat.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/cruce/chat.py):**
  - `construir_fragmentos_corrida(raiz: Path, corrida: str = "demo") -> list[Fragmento]`
  - `preguntar(raiz: Path, corrida: str, pregunta: str, historial: list[dict] | None = None) -> dict` $\rightarrow$ devuelve `{"respuesta", "fuentes": [{"id", "titulo", "tipo", "texto"}], "modelo", "corrida"}`.
- **[`cruce/api.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/cruce/api.py):**
  - `crear_servidor(puerto=8000, raiz=Path("."), dir_web=Path("../Frontend/public")) -> ThreadingHTTPServer`
  - `evaluar_kiosco_payload(raiz, content_type, raw_body, detector_real) -> dict`

---

## 4. Mapa del Frontend Next.js 15 (`Frontend/`) y Selectores E2E (`data-testid`)

- **Configuración de Proxy ([`Frontend/next.config.ts`](file:///home/alexteori/Documentos/repositorios/EPP/Frontend/next.config.ts)):**
  - Reescribe `/motor/:path*` $\rightarrow$ `${process.env.P4_API_URL || 'http://localhost:8000'}/:path*` con `proxyTimeout: 120_000`.
- **Tipos TypeScript ([`Frontend/types/`](file:///home/alexteori/Documentos/repositorios/EPP/Frontend/types/hallazgos.ts)):**
  - `PrendaEPP = 'lentes' | 'chaleco' | 'guantes'`
  - `TipoHallazgo = 'sin_lentes' | 'sin_guantes' | 'sin_chaleco' | 'multiples_epp_faltantes' | 'epp_faltante_agotado' | 'epp_agotado_en_caseta' | 'revisar'`
  - `RespuestaKiosco.estado_acceso = 'autorizado' | 'bloqueado' | 'revisar' | 'sin_persona'`
- **Selectores `data-testid` verificados por [`Frontend/tests/e2e.mjs`](file:///home/alexteori/Documentos/repositorios/EPP/Frontend/tests/e2e.mjs):**
  - `/resumen`: `hero-frase`, `jurado-btn-sin_lentes`, `jurado-btn-sin_guantes`, `jurado-btn-sin_chaleco`, `jurado-btn-multiple_faltante`, `jurado-resultado`.
  - `/kiosco`: `kiosco-veredicto`, `kiosco-preset-completo`, `kiosco-preset-sin_lentes`, `kiosco-preset-sin_guantes`, `kiosco-preset-sin_chaleco`, `kiosco-preset-incompleto_multiple`, `kiosco-prenda-lentes`, `kiosco-prenda-chaleco`, `kiosco-prenda-guantes`.
  - `/cuadrilla`: `estacion-card-L1-T1` .. `estacion-card-L3-T4`, `gemelo-anatomico-panel`.
  - `/hallazgos`: `hallazgos-riesgo-activo`, `hallazgos-riesgo-recuperado`, `hallazgo-card-<id>`, `btn-corregir-<id>`.
  - `/asistente`: `sugerencia-chat-0` .. `sugerencia-chat-3`, `mensaje-asistente-<idx>`.

---

## 5. Estado de la Corrida Demostrativa Base (`salida/hallazgos.json`)
- **Frase:** `"7 trabajadores sin EPP completo · US$3,280.00 al día en riesgo"`
- **Estaciones `ok` (`4`):** `L1-T1`, `L1-T3`, `L3-T1`, `L3-T4` (`cumplimiento_turno_pct: 33.3`)
- **Estaciones `error` (`7`):**
  - `L1-T2` (`Marco Antonio Ríos`): `multiples_epp_faltantes` (`lentes`, `guantes`) $\rightarrow$ `US$760.00/día`
  - `L2-T4` (`Héctor Navarro`): `multiples_epp_faltantes` (`lentes`, `chaleco`) $\rightarrow$ `US$710.00/día`
  - `L1-T4` (`Jorge Alberto Soto`): `sin_lentes` $\rightarrow$ `US$420.00/día`
  - `L3-T2` (`Sergio Valenzuela`): `sin_lentes` $\rightarrow$ `US$420.00/día`
  - `L2-T2` (`Roberto Domínguez`): `sin_guantes` $\rightarrow$ `US$340.00/día`
  - `L3-T3` (`Miguel Ángel Luna`): `sin_guantes` $\rightarrow$ `US$340.00/día`
  - `L2-T1` (`Ricardo Morales`): `sin_chaleco` $\rightarrow$ `US$290.00/día`
- **Estación `revisar` (`1`):** `L2-T3` (`Daniel Espinoza`, guantes `dudoso` con confianza `0.48`) $\rightarrow$ `US$0.00/día`.

---

## 6. Recetario de Comandos para Futuras Modificaciones

```bash
# 1. Correr los 18 tests de Python (tarda ~0.12 s)
motor-procesamiento/.venv/bin/python -m pytest -v

# 2. Verificar tipos y compilar el Frontend Next.js
npm --prefix Frontend run typecheck && npm --prefix Frontend run build

# 3. Regenerar salida/hallazgos.json, red.json y ensayos hacia Frontend/public/
cd motor-procesamiento && ./.venv/bin/python -m cruce.publicar

# 4. Evaluar precisión del motor contra la verdad de escena/escena.json
cd motor-procesamiento && ./.venv/bin/python -m herramientas.evaluar_motor

# 5. Iniciar todo el sistema (:8000 API + :3000 Tablero Web)
./iniciar.sh
```
