# Guion de Demostración Ejecutiva — Vigía EPP (5 Minutos)

## 1. El Problema (0:00 – 0:45)
En plantas de manufactura y logística pesada, el reglamento interno exige que todo operador ingrese a su turno con **3 prendas obligatorias**:
- **Lentes de seguridad ANSI Z87.1**
- **Chaleco reflejante Clase 2**
- **Guantes anticorte Nivel A4** *(en esta planta no se requiere casco ni mascarilla)*.

Sin embargo, a las 06:00 AM durante el cambio de turno, algunos trabajadores entran sin lentes o con las manos descubiertas porque les incomodan. Una sola omisión representa entre **US$290 y US$760 al día** en riesgo de accidentes, paros de línea y sanciones de inspección laboral.

---

## 2. Resumen Ejecutivo y Modo Jurado en Vivo (`/resumen` · 0:45 – 1:45)
1. Abrir **`/resumen`**: el titular cuantifica de inmediato el estado del turno:
   > **"7 trabajadores sin EPP completo · US$3,280.00 al día en riesgo"**
2. Mostrar el desglose por familia de omisión y el **Top 3 de prioridad en caseta** (encabezado por `Marco Antonio Ríos` en `L1-T2`, sin lentes ni guantes, con **US$760.00/día** en riesgo).
3. Bajar a la consola oscura **Modo Jurado en Vivo** y hacer clic en **"Trabajador sin Lentes"**: en segundos el motor compara contra la cuadrilla base y aísla el incumplimiento nuevo con su fotografía de evidencia y la acción exacta en caseta.

---

## 3. Kiosco de Torniquete en Tiempo Real (`/kiosco` · 1:45 – 2:45)
1. Entrar a **`/kiosco`**: aquí opera el filtro individual en la puerta de acceso a planta.
2. Hacer clic en los presets **"EPP Completo (3/3)"**, **"Sin Lentes"**, **"Sin Guantes"** y **"Múltiple Faltante"** (o encender la cámara web en vivo).
3. Mostrar cómo el motor responde en **`~3.3 ms`** con las cajas anotadas sobre la imagen y actualiza el panel de **Verificación Anatómica por Zona (3/3)** cambiando entre `"PASE DE TURNO AUTORIZADO"` (verde esmeralda) y `"ACCESO DETENIDO · FALTA EPP"` (rojo).

---

## 4. Gemelo Digital de Cuadrilla y Anatomía de 3 Zonas (`/cuadrilla` y `/recorrido` · 2:45 – 3:45)
1. Abrir **`/cuadrilla`**: a la izquierda se ven las **3 líneas de formación (12 estaciones)**; a la derecha aparece el **Gemelo Anatómico SVG de 3 Zonas** (`Ojos: Lentes`, `Torso: Chaleco`, `Manos: Guantes`) junto al recorte fotográfico real y el inventario disponible en caseta (`18 lentes`, `12 chalecos`, `24 guantes`).
2. Pasar a **`/recorrido`** y hacer clic en cualquier marcador temporal (`00:01 · L1-T2`, `00:05 · L2-T4`) para saltar al cuadro exacto del video anotado.

---

## 5. Cierre de Circuito en Caseta, Impacto en Red y Asistente IA (`/hallazgos`, `/red`, `/asistente` · 3:45 – 5:00)
1. En **`/hallazgos`**, hacer clic en **"Autorizar tras entrega"** sobre un trabajador: el cambio se persiste en disco mediante `PATCH /motor/analisis/<id>/hallazgos/<h_id>` y descuenta en vivo el dinero en riesgo pasándolo a **Mitigado en Caseta**.
2. En **`/red`**, mostrar cómo los incumplimientos sistémicos se proyectan a las **18 plantas** del grupo industrial.
3. En **`/asistente`**, lanzar una pregunta en lenguaje natural y mostrar la respuesta con **fuentes verificables** de la corrida (con soporte híbrido Gemini + RAG determinista local offline).
