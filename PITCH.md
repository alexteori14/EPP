# Guion de Demostración Ejecutiva — Vigía EPP (5 Minutos)

> **Preparación antes de presentar (1 comando desde cero):** Ejecuta `./iniciar.sh` (o `.\iniciar.bat` en Windows / `npm start`). El script crea automáticamente `.env` y `.venv`, instala las dependencias de Python y Frontend si faltan, levanta la API en `:8000` y abre la consola SCADA en `http://localhost:3000`.

## 1. El Problema y la Arquitectura Multi-Plugin (0:00 – 0:45)
En plantas de manufactura y logística pesada con niveles de ruido superiores a `94 dB(A)`, el reglamento interno y las normas `NOM-017-STPS` y `NOM-011-STPS` exigen que todo operador ingrese a su turno con su equipo de protección:
- **Obligatorios generales (toda la planta):** **Lentes ANSI Z87.1**, **Tapones Auditivos de Inserción NRR 32 dB** y **Chaleco Reflejante Clase 2**.
- **Condicional por puesto:** **Guantes Anticorte Nivel A4** (obligatorios en puestos operativos/maquinaria; **opcionales** en puestos de supervisión, inspección, almacén y montacargas). *(En esta planta no se requiere casco ni mascarilla)*.

Para detectarlos con precisión industrial, **Vigía EPP** entrena un modelo **YOLO11 de 9 clases** sobre **6 datasets combinados de Kaggle y Roboflow Universe (`2,072` imágenes reales)** incluyendo `aiotthien/personal-protection-equipment-datasets`, `tnguynhonh/sh17-yolov8s` (*SH17*) y `roboflow/earplugs-universe` (*Willy Alcantara / Roland Essmann / Research Thesis*), potenciado por los plugins **Ultralytics (YOLO11)**, **PyTorch + OpenCV**, **Supervision (Roboflow)**, **Weights & Biases (W&B)**, **NVIDIA TensorRT** y **ONNX Runtime**, auditado mediante la herramienta de porcentaje de exactitud (`entrenamiento/verificar_exactitud.py` con **TorchMetrics + Supervision + scikit-learn**).

---

## 2. Monitor de Caseta y Modo Jurado en Vivo (`/resumen` · 0:45 – 1:45)
1. Abrir **`/resumen`**: la consola SCADA cuantifica de inmediato el estado del turno:
   > **"7 trabajadores sin EPP completo · US$3,620.00 al día en riesgo"**
2. Mostrar el desglose por las **4 familias de omisión** (Lentes, Tapones Auditivos, Guantes y Chaleco) y el **Top 3 de prioridad en caseta** (encabezado por `Marco Antonio Ríos` en `L1-T2`, sin lentes, sin tapones y sin guantes, con **US$1,140.00/día** en riesgo).
3. En la consola **Modo Jurado en Vivo**, hacer clic en **"Sin Tapones Auditivos"**: en segundos el motor compara contra la cuadrilla base y aísla el incumplimiento nuevo (`US$380.00/día · NOM-011-STPS`) con su fotografía de evidencia y la dotación inmediata en caseta (`40 tapones NRR 32 dB disponibles`).

---

## 3. Torniquete en Tiempo Real y Guantes Opcionales por Puesto (`/kiosco` · 1:45 – 2:45)
1. Entrar a **`/kiosco`**: aquí opera el filtro individual en la puerta de acceso a planta acelerado con GPU (`PyTorch CUDA / ONNX Runtime / TensorRT`).
2. Hacer clic en los presets **"EPP Completo (4/4)"**, **"Sin Tapones (NOM-011)"** y **"Sin Guantes"**.
3. Con el preset **"Sin Guantes"** activo, alternar el selector superior de **"Puesto Operativo (Guantes Obligatorios)"** a **"Supervisor / Montacargas / Inspector (Guantes Opcionales)"**: mostrar cómo el veredicto cambia instantáneamente de `"TORNIQUETE BLOQUEADO · FALTA EPP"` a `"TORNIQUETE LIBERADO · PASE AUTORIZADO"` marcando los guantes en color cian (`OPCIONAL EN SU PUESTO`).

---

## 4. Gemelo Anatómico de 4 Zonas (`/cuadrilla` y `/recorrido` · 2:45 – 3:45)
1. Abrir **`/cuadrilla`**: a la izquierda se ven las **3 líneas de formación (12 estaciones)**; a la derecha aparece el **Gemelo Anatómico SVG de 4 Zonas** (`Ojos: Lentes`, `Oídos: Tapones NRR 32 dB`, `Torso: Chaleco`, `Manos: Guantes`) junto al recorte fotográfico real y el inventario disponible en caseta. Seleccionar `L3-T1` (`Alejandro Cabrera · Inspector de Calidad`) para mostrar cómo su acceso es autorizado aunque no porte guantes porque en su puesto son opcionales.
2. Pasar a **`/recorrido`** y hacer clic en cualquier marcador temporal (`00:01 · L1-T2`, `00:07 · L3-T2`) para saltar al cuadro exacto del video anotado.

---

## 5. Cierre de Circuito en Caseta, Impacto en Red y Asistente IA (`/hallazgos`, `/red`, `/asistente` · 3:45 – 5:00)
1. En **`/hallazgos`**, hacer clic en **"Autorizar tras entrega"** sobre un trabajador: el cambio se persiste en disco mediante `PATCH /motor/analisis/<id>/hallazgos/<h_id>` y descuenta en vivo el dinero en riesgo pasándolo a **Mitigado en Caseta**.
2. En **`/red`**, mostrar cómo los incumplimientos sistémicos (`US$1,850.00/día`) se proyectan a las **18 plantas** del grupo industrial.
3. En **`/asistente`**, lanzar una pregunta sobre quiénes olvidaron los tapones auditivos o en qué puestos los guantes son opcionales y mostrar la respuesta con **fuentes verificables** de la corrida.
