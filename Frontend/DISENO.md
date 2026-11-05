# Sistema de Diseño — Vigía EPP (Industrial Safety Slate)

## 1. Filosofía visual y principios operativos

**Vigía EPP** está diseñado para dos perfiles de usuario en el mismo sistema:
1. **Guardia / Supervisor de Caseta Pre-Turno (`/kiosco`, `/cuadrilla`, `/hallazgos`)**: toma decisiones de acceso en menos de 3 segundos a distancia de un brazo.
2. **Gerente de Seguridad Industrial EHS / Jurado Técnico (`/resumen`, `/recorrido`, `/red`, `/analizar`, `/asistente`)**: evalúa exposición económica diaria en dólares (`US$/día`), cumplimiento por línea y escalamiento a las 18 plantas de la red.

### Restricción de Dominio Estricta
En esta planta industrial **NO se exige casco ni mascarilla**. El sistema evalúa única y exclusivamente **3 prendas obligatorias de EPP**:
1. **Lentes de seguridad ANSI Z87.1** (`lentes` / `sin_lentes`) — Zona Ojos/Cabeza (`y ∈ [0.00, 0.32]`)
2. **Chaleco de alta visibilidad Clase 2** (`chaleco` / `sin_chaleco`) — Zona Torso (`y ∈ [0.16, 0.72]`)
3. **Guantes anticorte Nivel A4** (`guantes` / `sin_guantes`) — Zona Manos/Muñecas (`y ∈ [0.28, 0.96]`)

---

## 2. Tokens de color (Industrial Safety Slate)

| Uso semántico | Token Tailwind / Hex | Cuándo se aplica |
|---|---|---|
| Lienzo base | `bg-slate-50` (`#F8FAFC`) | Fondo general del tablero (alto contraste en monitores de caseta) |
| Superficie elevada | `bg-white` (`#FFFFFF`) con `border-slate-200` | Tarjetas de hallazgos, gemelo anatómico, tablas y paneles |
| Navegación / Consola Kiosco | `bg-slate-900` (`#0F172A`) / `bg-slate-950` (`#0B1120`) | Barra lateral fija y visor de cámara en vivo `/kiosco` |
| Acento de marca e interactividad | `teal-600` (`#0D9488`) / `teal-500` (`#14B8A6`) | Controles activos, barras de proporción e indicadores primarios |
| **Pase Autorizado / EPP Completo (3/3)** | `emerald-600` (`#059669`) sobre `emerald-50` | Trabajador con Lentes + Chaleco + Guantes verificados |
| **Acceso Detenido / Falta EPP** | `rose-600` (`#E11D48`) sobre `rose-50` | Falta confirmada de Lentes, Chaleco o Guantes (`confianza ≥ 0.60`) |
| **Lectura Dudosa / Revisar** | `amber-600` (`#D97706`) sobre `amber-50` | Zona oculta o confianza `< 0.60` (`US$0.00` hasta verificación humana) |

---

## 3. Tipografía y jerarquía numérica

- **Tipografía de interfaz:** `Inter` local (`@fontsource/inter`, pesos 400, 500, 600, 700), 100 % offline sin llamadas a Google Fonts.
- **Tipografía técnica / códigos:** `Fira Code` (`@fontsource/fira-code`) para códigos de estación (`L1-T2`), IDs de empleado (`EMP-102`), timestamps (`00:05`) y métricas de inferencia (`ms`).
- **Cifras monetarias y conteos:** Todas las cifras de riesgo (`US$3,280.00/día`) usan `.font-tabular` (`font-variant-numeric: tabular-nums`) para alineación vertical perfecta en rankings y tablas.

---

## 4. Componentes firma

1. **Gemelo Anatómico de 3 Zonas (`CuadrillaView` y `KioscoView`)**:
   - Silueta SVG interactiva dividida en **Zona 1 · Ojos (Lentes)**, **Zona 2 · Torso (Chaleco)** y **Zona 3 · Manos (Guantes)** con estado por color, confianza del modelo YOLO11, lecturas confirmadas y stock disponible en caseta.
2. **Modo Jurado en Vivo (`ResumenView`)**:
   - 4 tarjetas de ensayo (`Sin Lentes`, `Sin Guantes`, `Sin Chaleco`, `Múltiple Faltante`) que ejecutan o consultan la corrida real del motor y muestran el hallazgo emergente con recorte fotográfico.
3. **Persistencia Transaccional de Corrección (`HallazgosView`)**:
   - Botón `"Autorizar tras entrega"` que invoca `PATCH /motor/analisis/<id>/hallazgos/<h_id>` y actualiza en tiempo real el dinero recuperado (`US$/día`).
