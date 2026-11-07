# Memoria Técnica de Contexto Rápido para IA — Vigía EPP (`memoria.md`)

> **Propósito:** Este documento está diseñado específicamente para que tú (u otra IA en sesiones futuras) recuperes el **100 % del contexto arquitectónico, contratos, funciones, rutas, constantes, reglas de negocio y métodos** de **Vigía EPP (v2.4)** en una sola lectura, sin gastar tokens abriendo docenas de archivos.

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
   - `0: "persona"`
   - `1: "chaleco"`
   - `2: "sin_chaleco"`
   - `3: "lentes"`
   - `4: "sin_lentes"`
   - `5: "guantes"`
   - `6: "sin_guantes"`
   - `7: "tapones"`
   - `8: "sin_tapones"`

3. **AUDITORÍA DE LOS 3 DATASETS BASE DE KAGGLE Y PREPARACIÓN PARA EL 4º DATASET DE TAPONES:**
   - Se verificó al 100 % (tanto en archivos locales `motor-procesamiento/datos_kaggle/` como en los metadatos web de Kaggle) que los 3 datasets iniciales **NO contienen fotos ni etiquetas de tapones auditivos**:
     - `ndomalau/personal-protective-equipment-ppe-dataset`: 5 clases (`helmet`, `no_helmet`, `no_vest`, `person`, `vest`).
     - `shlokraval/ppe-dataset-yolov8`: 14 clases de *Roboflow Construction Site Safety* (`Fall-Detected`, `Gloves`, `Goggles`, `Hardhat`, `Ladder`, `Mask`, `NO-Gloves`, `NO-Goggles`, `NO-Hardhat`, `NO-Mask`, `NO-Safety Vest`, `Person`, `Safety Cone`, `Safety Vest`).
     - `slimese/personal-protective-equipment`: las mismas 14 clases de *Construction Site Safety*.
   - **Listo para conectar el 4º dataset de Kaggle con tapones:** [`entrenamiento/preparar_epp.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/entrenamiento/preparar_epp.py) ya tiene configuradas las traducciones en `MAPEO_NOMBRES` (`earplugs`, `earplug`, `ear_protection`, `earmuffs`, `hearing_protection`, `tapones` $\rightarrow$ `7` y `no_earplugs`, `no-earplugs`, `without_earplugs`, `sin_tapones` $\rightarrow$ `8`). En cuanto el usuario entregue el MCP/slug del 4º dataset de Kaggle, basta descargarlo en `motor-procesamiento/datos_kaggle/`, correr `python -m entrenamiento.preparar_epp` y `python -m entrenamiento.entrenar_yolo`.

4. **INTERFAZ PROPIA OPCIÓN 1 — CONSOLA SCADA / HMI INDUSTRIAL (CERO PARECIDO VISUAL CON `ubik`):**
   - Se eliminó definitivamente `Frontend/components/layout/Sidebar.tsx`, el fondo blanco/claro tipo retail y el acento `teal-600` heredados de `ubik`.
   - Toda la interfaz implementa la **Opción 1: Centro de Comando Industrial y Caseta de Torniquete (*Tactical Dark & High-Vis Safety*)**:
     - **Fondo:** Acero carbón `#080c14` con rejilla técnica industrial (`bg-scada-grid`) y cinta superior de precaución amarilla/negra (`hazard-stripe`).
     - **Semáforo Industrial:** Ámbar de alta visibilidad `#F59E0B` (acento primario y lectura dudosa), Verde torniquete `#10B981` (pase autorizado), Rojo sirena `#F43F5E` (acceso bloqueado / multa STPS) y Cian técnico `#06B6D4` (guantes opcionales según puesto).
     - **Top Command HUD ([`Header.tsx`](file:///home/alexteori/Documentos/repositorios/EPP/Frontend/components/layout/Header.tsx)):** Barra superior horizontal con telemetría acústica en vivo (`NAVE A · 94.2 dB(A) · NOM-011-STPS`), estado del torniquete y botonera táctica numerada (`01 MONITOR CASETA` a `08 INSPECTOR IA`).
     - **Gemelo Anatómico SVG de 4 Zonas (`SiluetaAnatomica4Zonas` en [`CuadrillaView.tsx`](file:///home/alexteori/Documentos/repositorios/EPP/Frontend/components/cuadrilla/CuadrillaView.tsx)):** Representación vectorial interactiva de **Ojos (`lentes`)**, **Oídos (`tapones` con ondas acústicas laterales)**, **Torso (`chaleco`)** y **Manos (`guantes` obligatorios u opcionales)**.

5. **PRINCIPIO DE HONESTIDAD OPERATIVA (`dudoso` / `revisar` = `US$0.00`):**
   - Cuando una zona anatómica obligatoria está cortada por el borde del encuadre, tiene confianza `< 0.55` (`CONFIANZA_MINIMA_PRENDA`) o hay empate técnico entre clase positiva y negativa (`abs(conf_pos - conf_neg) < 0.15`, `UMBRAL_CONFLICTO_DUDA`), el estado de la prenda es `"dudoso"` y el hallazgo se clasifica como `"revisar"` con **`impacto_diario = 0.0`**.

---

## 2. Resumen de Qué se Hizo, Cómo se Hizo y Con Qué Métodos

### 2.1 Metodología y Perfeccionamientos sobre el Proyecto de Referencia (`ubik`)
- **Lo conservado de `ubik` (`/home/alexteori/Documentos/repositorios/ubik`):**
  - Desacoplamiento estricto en 3 capas (`motor/` $\rightarrow$ `cruce/` $\rightarrow$ `Frontend/`) comunicadas por contratos JSON y selección de cuadros nítidos mediante varianza del Laplaciano en hilo productor-consumidor.
- **Lo perfeccionado y rediseñado en `Vigía EPP`:**
  1. **Identidad Visual SCADA/HMI Propia (Opción 1):** Reemplazo total del layout de tienda retail por una consola oscura de caseta de seguridad industrial con telemetría acústica y silueta anatómica de 4 zonas.
  2. **Reglas de EPP Diferenciadas por Puesto (`prendas_requeridas_por_puesto`):** Evaluación de 4 zonas anatómicas donde Lentes, Tapones Auditivos y Chaleco son obligatorios generales, mientras que los Guantes son obligatorios en puestos manuales/maquinaria y opcionales en puestos de supervisión, inspección, almacén o montacargas.
  3. **Persistencia Transaccional en Disco (`PATCH /analisis/<id>/hallazgos/<h_id>`):** `cruce.hallazgos.actualizar_corregido()` escribe atómicamente (`.tmp` + `os.replace`) en `salida/hallazgos.json` y `Frontend/public/salida/hallazgos.json`, recalculando al instante `dinero_en_riesgo_diario`, `dinero_recuperado_diario` y `red.json`.
  4. **Asistente RAG Híbrido Offline/Online (`cruce/chat.py`):** Opera con Gemini (`gemini-2.5-flash`) cuando existe `APIGEMINI` y con `_responder_rag_local()` (motor RAG determinista local con citas textuales verificables) cuando se ejecuta sin internet o sin API key.
  5. **Kiosco de Torniquete en Vivo `< 300 ms` (`motor/kiosco.py` + `/kiosco`):** Evalúa cámara WebRTC, fotos o 6 presets (incluyendo `sin_tapones`) y permite conmutar en vivo si el puesto exige guantes o si son opcionales (`requiere_guantes: boolean`).

---

## 3. Mapa Exacto de Módulos, Clases y Firmas de Funciones

### 3.1 Capa de Entrenamiento (`motor-procesamiento/entrenamiento/`)
- **[`entrenamiento/descargar_kaggle.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/entrenamiento/descargar_kaggle.py):**
  - Descarga los datasets de Kaggle configurados hacia `motor-procesamiento/datos_kaggle/`.
- **[`entrenamiento/preparar_epp.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/entrenamiento/preparar_epp.py):**
  - `MAPEO_NOMBRES: dict[str, int]` $\rightarrow$ traduce etiquetas a los índices `0..8` (`0: persona`, `1: chaleco`, `2: sin_chaleco`, `3: lentes`, `4: sin_lentes`, `5: guantes`, `6: sin_guantes`, `7: tapones`, `8: sin_tapones`) y descarta cascos/mascarillas.
  - `clave_base_roboflow(nombre_archivo: str) -> str` $\rightarrow$ corta `.rf.<hash>` para evitar data leakage entre splits.
  - `mapear_etiqueta_linea(linea: str, nombres_origen: list[str]) -> str | None`
  - `mapear_texto_anotacion(texto: str, nombres_origen: list[str]) -> tuple[str, set[int]]`
  - `preparar_dataset(dir_kaggle="datos_kaggle", dir_salida="datasets/epp", semilla=42) -> dict` $\rightarrow$ genera `datasets/epp/data.yaml` con `nc: 9`.
- **[`entrenamiento/entrenar_yolo.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/entrenamiento/entrenar_yolo.py):**
  - Entrena `yolo11n.pt` en GPU y exporta [`modelos/epp.pt`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/modelos/epp.pt) y [`modelos/epp.json`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/modelos/epp.json).

### 3.2 Capa del Motor de Visión (`motor-procesamiento/motor/`)
- **[`motor/contrato.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/motor/contrato.py):**
  - `CLASES = ("persona", "chaleco", "sin_chaleco", "lentes", "sin_lentes", "guantes", "sin_guantes", "tapones", "sin_tapones")`
  - `PRENDAS = ("lentes", "tapones", "chaleco", "guantes")`
  - `PRENDAS_GENERALES = ("lentes", "tapones", "chaleco")`
  - `PRENDAS_OPCIONALES_POR_PUESTO = ("guantes",)`
  - `PUESTOS_GUANTES_OPCIONALES = frozenset({"Operador de Montacargas", "Supervisor de Patio", "Almacenista de Acero", "Inspector de Calidad", "Coordinador de Logística"})`
  - `ZONAS_ANATOMICAS = {"lentes": (0.00, 0.32), "tapones": (0.04, 0.28), "chaleco": (0.16, 0.72), "guantes": (0.28, 0.96)}`
  - `MARGEN_X_ZONA = {"lentes": 0.05, "tapones": 0.08, "chaleco": 0.08, "guantes": 0.18}`
  - `NOMBRES_PRENDA = {"lentes": "Lentes de seguridad", "tapones": "Tapones auditivos", "chaleco": "Chaleco reflejante", "guantes": "Guantes anticorte"}`
  - `prendas_requeridas_por_puesto(puesto: str) -> tuple[str, ...]`
  - `@dataclass(frozen=True) class TrabajadorTurno(posicion, linea, id_empleado, nombre, puesto, orden, prendas_requeridas=PRENDAS)` con propiedades `.requiere_guantes -> bool` y `.prendas_opcionales -> tuple[str, ...]`.
  - `leer_turnos(ruta: str | Path) -> list[TrabajadorTurno]`
- **[`motor/asociar.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/motor/asociar.py):**
  - `CONFIANZA_MINIMA_PRENDA = 0.55`, `UMBRAL_CONFLICTO_DUDA = 0.15`
  - `asociar_cuadro(detecciones: list[Deteccion], ancho: int, alto: int, cuadro: int = 0) -> list[PersonaAsociada]` (evalúa las 4 zonas anatómicas para cada persona detectada).
- **[`motor/kiosco.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/motor/kiosco.py):**
  - `evaluar_imagen(imagen_bgr: np.ndarray, detector: DetectorEPP | None = None, modelo: str = "modelos/epp.pt", prendas_requeridas: tuple[str, ...] | None = None, requiere_guantes: bool = True) -> dict`
  - Llaves devueltas: `personas_detectadas`, `estado_acceso` (`"autorizado" | "bloqueado" | "revisar" | "sin_persona"`), `mensaje`, `requiere_guantes`, `prendas_completas`, `prendas_requeridas`, `faltantes`, `dudosas`, `zonas` (cada zona incluye `requerida: bool`), `accion_caseta`, `ms_proceso`, `imagen_anotada_b64`.
- **[`motor/pipeline.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/motor/pipeline.py):**
  - `procesar(video, ruta_turnos, salida, modelo="modelos/epp.pt", ...) -> dict` (respeta `t.prendas_requeridas` al evaluar si cada estación de `turnos.csv` está completa).

### 3.3 Capa de Cruce, Reglas, RAG y Servidor HTTP (`motor-procesamiento/cruce/`)
- **[`cruce/hallazgos.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/cruce/hallazgos.py):**
  - `clasificar(o, t, sistema) -> str | None` $\rightarrow$ evalúa únicamente `t.prendas_requeridas` (por lo que si `t.requiere_guantes` es `False` y `guantes == "falta"`, NO genera hallazgo ni multa). Devuelve `"epp_faltante_agotado"`, `"multiples_epp_faltantes"`, `"sin_lentes"`, `"sin_tapones"`, `"sin_chaleco"`, `"sin_guantes"`, `"revisar"` o `None`.
  - `impacto_diario(tipo, o, t, sistema) -> float`
  - `actualizar_corregido(ruta_json: Path, hallazgo_id: str, corregido: bool) -> dict | None`
- **[`cruce/api.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/cruce/api.py):**
  - `PRESETS_KIOSCO` soporta 6 presets: `"completo"`, `"sin_lentes"`, `"sin_tapones"`, `"sin_guantes"`, `"sin_chaleco"`, `"incompleto_multiple"`, respetando `requiere_guantes: bool` enviado en el body JSON de `POST /kiosco/evaluar`.
  - `TARJETAS_JURADO` soporta 5 tarjetas: `"sin_lentes"`, `"sin_tapones"`, `"sin_guantes"`, `"sin_chaleco"`, `"multiple_faltante"`.

---

## 4. Mapa del Frontend Next.js 15 (`Frontend/`) y Selectores E2E (`data-testid`)

- **Layout SCADA sin Sidebar ([`Frontend/app/layout.tsx`](file:///home/alexteori/Documentos/repositorios/EPP/Frontend/app/layout.tsx) + [`Frontend/components/layout/Header.tsx`](file:///home/alexteori/Documentos/repositorios/EPP/Frontend/components/layout/Header.tsx)):**
  - `Header.tsx` renderiza la cinta `hazard-stripe`, el HUD de telemetría (`94.2 dB(A) NOM-011`, estado del torniquete) y la barra horizontal de 8 módulos. (`Sidebar.tsx` fue eliminado).
- **Tipos TypeScript ([`Frontend/types/`](file:///home/alexteori/Documentos/repositorios/EPP/Frontend/types/hallazgos.ts)):**
  - `PrendaEPP = 'lentes' | 'tapones' | 'chaleco' | 'guantes'`
  - `TipoHallazgo = 'sin_lentes' | 'sin_tapones' | 'sin_guantes' | 'sin_chaleco' | 'multiples_epp_faltantes' | 'epp_faltante_agotado' | 'epp_agotado_en_caseta' | 'revisar'`
  - `PresetKiosco = 'completo' | 'sin_lentes' | 'sin_tapones' | 'sin_guantes' | 'sin_chaleco' | 'incompleto_multiple'`
- **Selectores `data-testid` verificados por [`Frontend/tests/e2e.mjs`](file:///home/alexteori/Documentos/repositorios/EPP/Frontend/tests/e2e.mjs):**
  - `/resumen`: `hero-frase`, `jurado-btn-sin_lentes`, `jurado-btn-sin_tapones`, `jurado-btn-sin_guantes`, `jurado-btn-sin_chaleco`, `jurado-btn-multiple_faltante`, `jurado-resultado`.
  - `/kiosco`: `kiosco-toggle-guantes-obligatorios`, `kiosco-toggle-guantes-opcionales`, `kiosco-veredicto`, `kiosco-preset-completo`, `kiosco-preset-sin_lentes`, `kiosco-preset-sin_tapones`, `kiosco-preset-sin_guantes`, `kiosco-preset-sin_chaleco`, `kiosco-preset-incompleto_multiple`, `kiosco-prenda-lentes`, `kiosco-prenda-tapones`, `kiosco-prenda-chaleco`, `kiosco-prenda-guantes`.
  - `/cuadrilla`: `estacion-card-L1-T1` .. `estacion-card-L3-T4`, `gemelo-anatomico-panel` (`SiluetaAnatomica4Zonas`).
  - `/hallazgos`: `hallazgos-riesgo-activo`, `hallazgos-riesgo-recuperado`, `hallazgo-card-<id>`, `btn-corregir-<id>`.
  - `/asistente`: `sugerencia-chat-0` .. `sugerencia-chat-3`, `mensaje-asistente-<idx>`.

---

## 5. Estado Exacto de la Corrida Demostrativa Base (`salida/hallazgos.json`)

- **Frase Titular:** `"7 trabajadores sin EPP completo · US$3,620.00 al día en riesgo"`
- **Estaciones `ok` (`4` de 12 · `cumplimiento_turno_pct: 33.3 %`):**
  - `L1-T1` (`Carlos Mendoza`, *Operador de Corte CNC*, guantes obligatorios: `4/4 ok`)
  - `L1-T3` (`Luis Fernando Vega`, *Técnico de Troquelado*, guantes obligatorios: `4/4 ok`)
  - `L3-T1` (`Alejandro Cabrera`, *Inspector de Calidad*, **guantes opcionales**: lleva `lentes + tapones + chaleco` y `guantes=falta`, pero su puesto solo exige `3/3` $\rightarrow$ **AUTORIZADO `ok` con `US$0.00`**)
  - `L3-T4` (`Eduardo Castañeda`, *Armador de Subensambles*, guantes obligatorios: `4/4 ok`)
- **Estaciones `error` (`7` trabajadores retenidos en torniquete = `US$3,620.00/día`):**
  1. `L1-T2` (`Marco Antonio Ríos`, *Soldador de Estructura*, guantes obligatorios): `multiples_epp_faltantes` (`lentes`, `tapones`, `guantes`) $\rightarrow$ **`US$1,140.00/día`** (`420 + 380 + 340`)
  2. `L2-T4` (`Héctor Navarro`, *Almacenista de Acero*, guantes opcionales): `multiples_epp_faltantes` (`lentes`, `chaleco`) $\rightarrow$ **`US$710.00/día`** (`420 + 290`)
  3. `L1-T4` (`Jorge Alberto Soto`, *Operador de Prensa*, guantes obligatorios): `sin_lentes` $\rightarrow$ **`US$420.00/día`**
  4. `L3-T2` (`Sergio Valenzuela`, *Operador de Esmerilado*, guantes obligatorios): `sin_tapones` $\rightarrow$ **`US$380.00/día`**
  5. `L2-T2` (`Roberto Domínguez`, *Auxiliar de Maniobras*, guantes obligatorios): `sin_guantes` $\rightarrow$ **`US$340.00/día`**
  6. `L3-T3` (`Miguel Ángel Luna`, *Técnico de Mantenimiento*, guantes obligatorios): `sin_guantes` $\rightarrow$ **`US$340.00/día`**
  7. `L2-T1` (`Ricardo Morales`, *Operador de Montacargas*, guantes opcionales): `sin_chaleco` $\rightarrow$ **`US$290.00/día`**
- **Estación `revisar` (`1` lectura dudosa = `US$0.00/día`):**
  - `L2-T3` (`Daniel Espinoza`, *Supervisor de Patio*, guantes opcionales): zona `tapones` en `"dudoso"` (`48 %` de confianza) $\rightarrow$ **`US$0.00/día`**.
- **Proyección en Red de 18 Plantas (`Frontend/public/red.json`):**
  - `medido_diario: US$3,620.00` = `sistemico_diario: US$1,850.00` (`L1-T2` + `L2-T4`) + `local_diario: US$1,770.00` (5 casos individuales).
  - Escenarios en las otras 17 plantas (`30 días/mes`): Bajo (`2 plantas`): `US$3,700/día` (`US$111,000/mes`) · Central (`4 plantas`): `US$7,400/día` (`US$222,000/mes`) · Alto (`8 plantas`): `US$14,800/día` (`US$444,000/mes`) · Peor caso (`17 plantas`): `US$31,450/día` (`US$943,500/mes`).

---

## 6. Recetario de Comandos para Futuras Modificaciones

```bash
# 1. Correr los 19 tests unitarios e integrales de Python (~0.29 s)
motor-procesamiento/.venv/bin/python -m pytest -v

# 2. Verificar tipos y compilar el Frontend Next.js
npm --prefix Frontend run build

# 3. Regenerar video de turno, 5 tarjetas del Modo Jurado, hallazgos.json y red.json hacia Frontend/public/
cd motor-procesamiento && ./.venv/bin/python -m simulador.render_turno && ./.venv/bin/python -m motor.pipeline --video video/recorrido_turno.mp4 --turnos datos/sistema/turnos.csv --salida salida && ./.venv/bin/python -m cruce.publicar

# 4. Ejecutar la suite E2E de Playwright en las 8 pantallas (asegurando que :8000 tenga la API actualizada)
fuser -k 8000/tcp 3018/tcp 2>/dev/null || true
(cd motor-procesamiento && ./.venv/bin/python -m cruce.api --puerto 8000) &
(cd Frontend && npx next start -p 3018) &
sleep 4 && E2E_URL="http://localhost:3018" node Frontend/tests/e2e.mjs

# 5. Iniciar todo el sistema en vivo (:8000 API + :3000 Consola SCADA Web)
./iniciar.sh
```
