# Contrato de Datos · Vigía EPP

Este documento define las interfaces exactas entre el **motor de visión (`motor/`)**, el **módulo de cruce y API (`cruce/`)** y el **tablero web (`Frontend/`)**.

## 1. Regla de Oro y Equipos Evaluados

En esta instalación industrial **no se solicita casco ni mascarilla**. El filtro previo al inicio de turno verifica exclusivamente **3 Equipos de Protección Personal (EPP)**:
1. **`lentes`** — Lentes / gafas de seguridad (Zona anatómica 1: Ojos/Cabeza, franja vertical `y ∈ [0.00, 0.30]`).
2. **`chaleco`** — Chaleco reflejante de alta visibilidad (Zona anatómica 2: Torso, franja vertical `y ∈ [0.18, 0.72]`).
3. **`guantes`** — Guantes industriales de seguridad (Zona anatómica 3: Manos/Antebrazos, franja vertical `y ∈ [0.30, 0.96]`).

### Clases del Detector YOLO11 (`modelos/epp.pt`)

| ID | Clase | Rol |
|---|---|---|
| `0` | `persona` | Trabajador en el filtro de entrada a turno |
| `1` | `chaleco` | Presencia confirmada de chaleco de alta visibilidad |
| `2` | `sin_chaleco` | Ausencia confirmada de chaleco en el torso |
| `3` | `lentes` | Presencia confirmada de lentes/gafas de seguridad |
| `4` | `sin_lentes` | Ausencia confirmada de lentes en el rostro |
| `5` | `guantes` | Presencia confirmada de guantes en manos |
| `6` | `sin_guantes` | Ausencia confirmada de guantes en manos |

---

## 2. Archivos del Sistema de Planta (`datos/sistema/`)

### `datos/sistema/turnos.csv`
Define las 12 posiciones del filtro de inicio de turno (3 líneas operativas × 4 estaciones por línea):
```csv
posicion,linea,id_empleado,nombre,puesto,orden
L1-T1,L1,EMP-101,Carlos Mendoza,Operador de Corte CNC,1
```

### `datos/sistema/inventario_epp.csv`
Existencia actual en la caseta de entrada y almacén de planta:
```csv
prenda,nombre_comercial,existencia_caseta,stock_minimo,costo_unitario_usd,riesgo_diario_usd,riesgo_paro_usd
lentes,Lentes Policarbonato Anti-Impacto ANSI Z87.1,18,5,14.50,420.00,950.00
chaleco,Chaleco Reflejante Clase 2 Alta Visibilidad,12,5,18.00,290.00,820.00
guantes,Guantes Nitrilo Anticorte Nivel A4,24,8,16.00,340.00,880.00
```

### `datos/sistema/reglas_riesgo.csv`
Desglose normativo (STPS NOM-017-STPS / OSHA) para defender cada monto en el tablero.

---

## 3. Salida del Motor (`salida/observaciones.json`)

```json
{
  "video": "recorrido_turno.mp4",
  "segundos_proceso": 12.4,
  "posiciones": [
    {
      "posicion": "L1-T1",
      "persona_detectada": true,
      "confianza_persona": 0.94,
      "prendas": {
        "lentes": {"estado": "ok", "confianza": 0.91, "lecturas": 5},
        "chaleco": {"estado": "ok", "confianza": 0.95, "lecturas": 5},
        "guantes": {"estado": "falta", "confianza": 0.88, "lecturas": 4}
      },
      "cuadro": 48,
      "recorte_persona": "recortes/L1-T1.jpg",
      "recorte_zona": "recortes/L1-T1_zona.jpg"
    }
  ]
}
```

- `estado` de cada prenda: `"ok"` | `"falta"` | `"dudoso"`.
- Si una zona no se vio completa o su confianza es `< 0.60` (o `< 2` lecturas en video), sale como `"dudoso"` y el cruce la clasifica como `"revisar"` con `impacto_diario = 0.0`.

---

## 4. Salida del Cruce para el Tablero (`Frontend/public/salida/hallazgos.json`)

Esquema tipado en `Frontend/types/hallazgos.ts`:
- `resumen`: `total_problemas`, `dinero_en_riesgo_diario`, `frase`, `trabajadores_incompletos`, `epp_agotados`, `lecturas_dudosas`, `cumplimiento_turno_pct`, `fecha_escaneo`, `disclaimer`, `moneda`, `video`, `video_url`, `segundos_proceso`, `fps`, `supuestos_calculo`.
- `posiciones[]`: las 12 posiciones del turno (`id: "pos-l1-t1"`, `linea: 1..3`, `posicion: 1..4`, `estado: "ok" | "error" | "revisar"`, `id_empleado`, `trabajador`, `puesto`, `prendas: {lentes, chaleco, guantes}`, `inventario_caseta`, `hallazgo_id`, `evidencia`).
- `hallazgos[]`: ordenados de mayor a menor `impacto_diario`. Tipos:
  - `epp_faltante_agotado` (sistémico: falta EPP y hay 0 en caseta)
  - `multiples_epp_faltantes` (faltan 2 o 3 prendas obligatorias)
  - `sin_lentes` (falta protección ocular)
  - `sin_guantes` (faltan guantes)
  - `sin_chaleco` (falta chaleco)
  - `revisar` (lectura dudosa / zona oculta; US$0.00)

---

## 5. Endpoints de la API Local (`cruce/api.py`, puerto `8000`)

- `GET /salud` → `{"ok": true}`
- `POST /kiosco/evaluar` → recibe imagen (`image/jpeg`, `image/png` o JSON `{"preset": "completo|sin_lentes|sin_guantes|sin_chaleco"}`) y devuelve en `<300 ms` el pase de turno (`autorizado | bloqueado | revisar | sin_persona`), el estado de las 3 zonas (`lentes`, `chaleco`, `guantes`), recorte anotado en base64 y acción en caseta.
- `POST /procesar` `{"tarjeta": "sin_lentes|sin_guantes|sin_chaleco|epp_agotado"}` y `GET /estado` → Modo Jurado en vivo.
- `POST /analisis`, `GET /analisis`, `GET /analisis/<id>`, `GET /analisis/activo`, `GET /analisis/activo/red`, `POST /analisis/<id>/activar`, `DELETE /analisis/<id>`.
- `PATCH /analisis/<id>/hallazgos/<hallazgo_id>` `{"corregido": true|false}` → Persiste en disco la corrección/autorización del hallazgo (`<id>` puede ser `"demo"` o un ID de análisis).
- `POST /analisis/<id>/chat` y `GET /chat` → Asistente RAG con Gemini.
