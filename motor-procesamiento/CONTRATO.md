# Contrato de Datos · Vigía EPP (v2.4 · 4 Zonas Anatómicas + Guantes Condicionales por Puesto)

Este documento define las interfaces exactas entre el **motor de visión (`motor/`)**, el **módulo de cruce y API (`cruce/`)** y la **consola SCADA web (`Frontend/`)**.

## 1. Regla de Oro y Equipos Evaluados

En esta instalación industrial **no se solicita casco ni mascarilla**. El filtro previo al inicio de turno verifica **4 Equipos de Protección Personal (EPP)**:
1. **`lentes`** — Lentes / gafas de seguridad ANSI Z87.1 (Zona anatómica 1: Ojos/Cabeza, franja vertical `y ∈ [0.00, 0.32]`) · **Obligatorio General**.
2. **`tapones`** — Tapones auditivos de inserción NRR 32 dB NOM-011-STPS (Zona anatómica 2: Oídos/Cráneo Lateral, franja vertical `y ∈ [0.04, 0.28]`) · **Obligatorio General**.
3. **`chaleco`** — Chaleco reflejante de alta visibilidad Clase 2 (Zona anatómica 3: Torso, franja vertical `y ∈ [0.16, 0.72]`) · **Obligatorio General**.
4. **`guantes`** — Guantes industriales anticorte Nivel A4 (Zona anatómica 4: Manos/Antebrazos, franja vertical `y ∈ [0.28, 0.96]`) · **Condicional según puesto** (obligatorio en puestos operativos/maquinaria; opcional en puestos dentro de `PUESTOS_GUANTES_OPCIONALES`).

### Clases del Detector YOLO11 (`modelos/epp.pt` · 9 Clases Canónicas)

| ID | Clase | Rol |
|---|---|---|
| `0` | `persona` | Trabajador en el filtro de entrada a turno |
| `1` | `chaleco` | Presencia confirmada de chaleco de alta visibilidad |
| `2` | `sin_chaleco` | Ausencia confirmada de chaleco en el torso |
| `3` | `lentes` | Presencia confirmada de lentes/gafas de seguridad |
| `4` | `sin_lentes` | Ausencia confirmada de lentes en el rostro |
| `5` | `guantes` | Presencia confirmada de guantes en manos |
| `6` | `sin_guantes` | Ausencia confirmada de guantes en manos |
| `7` | `tapones` | Presencia confirmada de tapones auditivos de inserción |
| `8` | `sin_tapones` | Ausencia confirmada de tapones auditivos en oídos |

---

## 2. Archivos del Sistema de Planta (`datos/sistema/`)

### `datos/sistema/turnos.csv`
Define las 12 posiciones del filtro de inicio de turno (3 líneas operativas × 4 estaciones por línea) y las prendas obligatorias por puesto:
```csv
posicion,linea,id_empleado,nombre,puesto,orden,prendas_requeridas
L1-T1,L1,EMP-101,Carlos Mendoza,Operador de Corte CNC,1,lentes|tapones|chaleco|guantes
L2-T1,L2,EMP-201,Ricardo Morales,Operador de Montacargas,5,lentes|tapones|chaleco
```

### `datos/sistema/inventario_epp.csv`
Existencia actual en la caseta de entrada y almacén de planta:
```csv
prenda,nombre_comercial,existencia_caseta,stock_minimo,costo_unitario_usd,riesgo_diario_usd,riesgo_paro_usd
lentes,Lentes Policarbonato Anti-Impacto ANSI Z87.1,18,5,14.50,420.00,950.00
tapones,Tapones Auditivos de Inserción NRR 32 dB NOM-011,40,10,6.50,380.00,890.00
chaleco,Chaleco Reflejante Clase 2 Alta Visibilidad,12,5,18.00,290.00,820.00
guantes,Guantes Nitrilo Anticorte Nivel A4,24,8,16.00,340.00,880.00
```

### `datos/sistema/reglas_riesgo.csv`
Desglose normativo (`NOM-017-STPS`, `NOM-011-STPS`, `NOM-006-STPS`, `OSHA`) para defender cada monto en el tablero.

---

## 3. Salida del Motor (`salida/observaciones.json`)

```json
{
  "video": "recorrido_turno.mp4",
  "segundos_proceso": 8.4,
  "posiciones": [
    {
      "posicion": "L1-T2",
      "persona_detectada": true,
      "confianza_persona": 0.96,
      "prendas": {
        "lentes": {"estado": "falta", "confianza": 0.89, "lecturas": 5},
        "tapones": {"estado": "falta", "confianza": 0.89, "lecturas": 5},
        "chaleco": {"estado": "ok", "confianza": 0.92, "lecturas": 5},
        "guantes": {"estado": "falta", "confianza": 0.89, "lecturas": 5}
      },
      "cuadro": 27,
      "recorte_persona": "recortes/L1-T2.jpg",
      "recorte_zona": "recortes/L1-T2_zona.jpg"
    }
  ]
}
```

- `estado` de cada prenda: `"ok"` | `"falta"` | `"dudoso"`.
- Si una zona obligatoria no se vio completa o su confianza es `< 0.55`, sale como `"dudoso"` y el cruce la clasifica como `"revisar"` con `impacto_diario = 0.0`.

---

## 4. Salida del Cruce para el Tablero (`Frontend/public/salida/hallazgos.json`)

Esquema tipado en `Frontend/types/hallazgos.ts`:
- `resumen`: `total_problemas`, `dinero_en_riesgo_diario`, `dinero_recuperado_diario`, `frase`, `trabajadores_incompletos`, `epp_agotados`, `lecturas_dudosas`, `cumplimiento_turno_pct`, `prendas_evaluadas` (`["lentes", "tapones", "chaleco", "guantes"]`), `fecha_escaneo`, `disclaimer`, `moneda`, `video`, `video_url`, `segundos_proceso`, `fps`, `supuestos_calculo`.
- `posiciones[]`: las 12 posiciones del turno (`id`, `codigo`, `linea`, `posicion`, `estado`, `id_empleado`, `trabajador`, `puesto`, `requiere_guantes`, `prendas_completas`, `prendas_requeridas`, `prendas: {lentes, tapones, chaleco, guantes}`, `inventario_caseta`, `hallazgo_id`, `evidencia`).
- `hallazgos[]`: ordenados de mayor a menor `impacto_diario`. Tipos:
  - `epp_faltante_agotado` (sistémico: falta EPP obligatorio y hay 0 en caseta)
  - `multiples_epp_faltantes` (faltan $\ge 2$ prendas obligatorias)
  - `sin_lentes` (`US$420.00/día`)
  - `sin_tapones` (`US$380.00/día`)
  - `sin_guantes` (`US$340.00/día`, solo cuando `requiere_guantes == true`)
  - `sin_chaleco` (`US$290.00/día`)
  - `revisar` (lectura dudosa / zona oculta; `US$0.00`)

---

## 5. Endpoints de la API Local (`cruce/api.py`, puerto `8000`)

- `GET /salud` → `{"ok": true, "servicio": "vigia-epp-motor"}`
- `POST /kiosco/evaluar` → recibe imagen o JSON `{"preset": "completo|sin_lentes|sin_tapones|sin_guantes|sin_chaleco|incompleto_multiple", "requiere_guantes": true|false}` y devuelve en `<300 ms` el pase de turno (`autorizado | bloqueado | revisar | sin_persona`), el estado de las 4 zonas (`lentes`, `tapones`, `chaleco`, `guantes`), recorte anotado en base64 y acción en caseta.
- `POST /procesar` `{"tarjeta": "sin_lentes|sin_tapones|sin_guantes|sin_chaleco|multiple_faltante"}` y `GET /tarjetas` → Modo Jurado en vivo.
- `POST /analisis`, `GET /analisis`, `GET /analisis/<id>`, `GET /analisis/activo`, `GET /analisis/activo/red`, `POST /analisis/<id>/activar`, `DELETE /analisis/<id>`.
- `PATCH /analisis/<id>/hallazgos/<hallazgo_id>` `{"corregido": true|false}` → Persiste en disco la corrección/autorización del hallazgo.
- `POST /analisis/<id>/chat` y `GET /chat` → Asistente RAG Híbrido (Gemini + RAG determinista local).
