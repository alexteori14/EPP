# Sistema de Diseño — Vigía EPP (Opción 1: Centro de Comando Industrial SCADA/HMI y Caseta de Torniquete)

## 1. Filosofía visual y principios operativos

**Vigía EPP** utiliza una interfaz **100 % propia para seguridad industrial y control de acceso en planta** (*Tactical Dark & High-Vis Safety*), eliminando cualquier elemento visual tipo retail (`Sidebar.tsx`, fondos blancos, colores comerciales). Está diseñada para dos perfiles de usuario en el mismo sistema:
1. **Guardia / Supervisor de Caseta Pre-Turno (`/kiosco`, `/cuadrilla`, `/hallazgos`)**: toma decisiones de liberación o bloqueo de torniquete en menos de 3 segundos a distancia de un brazo.
2. **Gerente de Seguridad Industrial EHS / Jurado Técnico (`/resumen`, `/recorrido`, `/red`, `/analizar`, `/asistente`)**: evalúa exposición económica diaria en dólares (`US$/día`), cumplimiento de protección auditiva (`NOM-011-STPS`) y ocular (`NOM-017-STPS`), reglas de guantes por puesto y escalamiento a las 18 plantas de la red.

### Restricción de Dominio Estricta (4 Zonas Anatómicas + Guantes Condicionales por Puesto)
En esta planta industrial **NO se exige casco ni mascarilla**. El sistema evalúa **4 componentes de EPP** con un modelo **YOLO11 de 9 clases** entrenado sobre **6 fuentes de Kaggle y Roboflow Universe** (`2,072` imágenes reales):
1. **Lentes de seguridad ANSI Z87.1** (`lentes` / `sin_lentes`) — Zona 1: Ojos/Cabeza (`y ∈ [0.00, 0.32]`) · **Obligatorio General** (`US$420.00/día`)
2. **Tapones auditivos de inserción NRR 32 dB** (`tapones` / `sin_tapones`) — Zona 2: Oídos/Cráneo Lateral (`y ∈ [0.04, 0.28]`) · **Obligatorio General** (`US$380.00/día`, `NOM-011-STPS`)
3. **Chaleco de alta visibilidad Clase 2** (`chaleco` / `sin_chaleco`) — Zona 3: Torso (`y ∈ [0.16, 0.72]`) · **Obligatorio General** (`US$290.00/día`)
4. **Guantes anticorte Nivel A4** (`guantes` / `sin_guantes`) — Zona 4: Manos/Muñecas (`y ∈ [0.28, 0.96]`) · **Obligatorio en puestos operativos (`US$340.00/día`) / Opcional en puestos de supervisión, inspección, almacén y montacargas (`US$0.00`)**

---

## 2. Tokens de color (SCADA Tactical Dark & High-Vis Safety)

| Uso semántico | Token Tailwind / Hex | Cuándo se aplica |
|---|---|---|
| Lienzo base industrial | `#080c14` + `.bg-scada-grid` | Fondo general acero carbón con rejilla técnica industrial |
| Cinta de precaución | `.hazard-stripe` (`#F59E0B` / `#080c14`) | Franja diagonal superior de caseta y paneles críticos |
| Panel de caseta | `.panel-caseta` (`#0f172a` con borde `#1e293b`) | Contenedores de telemetría, tarjetas de hallazgos y gemelo anatómico |
| Acento industrial primario | `amber-500` (`#F59E0B`) / `amber-400` (`#FBBF24`) | Botonera activa del Top Command HUD, alertas acústicas y controles principales |
| **Torniquete Liberado / EPP Completo** | `emerald-500` (`#10B981`) | Trabajador con todo el EPP requerido por su puesto |
| **Torniquete Bloqueado / Falta EPP** | `rose-500` (`#F43F5E`) | Falta confirmada de prenda obligatoria (`confianza ≥ 0.55`) |
| **Guantes Opcionales según Puesto** | `cyan-400` (`#06B6D4`) | Puestos donde los guantes no son obligatorios (`requiere_guantes = false`, `US$0.00`) |
| **Lectura Dudosa / Revisar en Ventanilla** | `amber-400` (`#F59E0B`) | Zona oculta o confianza `< 0.55` (`US$0.00` hasta verificación humana) |

---

## 3. Tipografía y jerarquía numérica

- **Tipografía de interfaz:** `Inter` local (`@fontsource/inter`, pesos 400, 500, 600, 700), 100 % offline sin llamadas a Google Fonts.
- **Tipografía técnica SCADA:** `Fira Code` (`@fontsource/fira-code`) para códigos de estación (`L1-T2`), IDs de empleado (`EMP-102`), telemetría acústica (`94.2 dB(A)`), timestamps (`00:05`) y tiempos de inferencia (`3.3 ms`).
- **Cifras monetarias y conteos:** Todas las cifras de riesgo (`US$3,620.00/día`) usan `.font-tabular` (`font-variant-numeric: tabular-nums`) para alineación vertical exacta.

---

## 4. Componentes firma

1. **Top Command HUD (`Header.tsx`)**:
   - Barra superior de comando (sin sidebar lateral) con franja de precaución, indicador acústico de nave (`94.2 dB(A) · NOM-011`), estado del torniquete y 8 pestañas numeradas (`01 MONITOR CASETA` a `08 INSPECTOR IA`).
2. **Gemelo Anatómico de 4 Zonas (`SiluetaAnatomica4Zonas` en `CuadrillaView`)**:
   - Silueta SVG interactiva dividida en **Zona 1 · Ojos (Lentes)**, **Zona 2 · Oídos (Tapones Auditivos con ondas acústicas laterales)**, **Zona 3 · Torso (Chaleco)** y **Zona 4 · Manos (Guantes obligatorios u opcionales en cian)** con confianza YOLO11 y stock en caseta.
3. **Modo Jurado en Vivo con 5 Escenarios (`ResumenView`)**:
   - 5 tarjetas (`Sin Lentes`, `Sin Tapones Auditivos`, `Sin Guantes`, `Sin Chaleco`, `Múltiple EPP Omitido`) que ejecutan la corrida del motor y muestran el hallazgo emergente con recorte fotográfico.
4. **Persistencia Transaccional de Liberación (`HallazgosView`)**:
   - Botón `"Autorizar tras entrega"` que invoca `PATCH /motor/analisis/<id>/hallazgos/<h_id>` y actualiza en disco el riesgo mitigado (`US$/día`).

---

## 5. Skills, Tools y Plugins utilizados en el Diseño y Motor

- **Skills de Diseño y Frontend:** `ui-ux-pro-max`, `design-system`, `ui-styling`, `modern-web-guidance`, `a11y-debugging`, `chrome-devtools`, `brainstorming`, `writing-plans`, `test-driven-development`, `executing-plans`, `verification-before-completion`.
- **Tools de Desarrollo y E2E:** `Playwright CLI` (`Frontend/tests/e2e.mjs`), `OpenSpec` (`@fission-ai/openspec`), `Framer Motion`, `Tailwind CSS`, `Lucide React`, `uv` package manager, `Headroom AI`.
- **Plugins de IA, Visión y Aceleración integrados con el Tablero:**
  - **Ultralytics (`YOLO11`)** + **PyTorch CUDA (`torch`) + OpenCV (`cv2`)**
  - **Supervision (`supervision` de Roboflow)** + **Roboflow SDK (`roboflow`)**
  - **Weights & Biases (`wandb`)** para trazabilidad de entrenamiento y métricas
  - **ONNX Runtime (`onnxruntime-gpu`)** + **NVIDIA TensorRT (`TensorrtExecutionProvider`)**
  - **Verificador de Porcentaje de Exactitud (`torchmetrics` + `scikit-learn` + `supervision`)** en [`entrenamiento/verificar_exactitud.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/entrenamiento/verificar_exactitud.py).
