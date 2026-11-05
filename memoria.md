# Memoria de Contexto Rápido para Agentes de IA — Vigía EPP (`memoria.md`)

> **Propósito de este archivo:** Permitir que cualquier agente de IA futuro comprenda la totalidad del proyecto **Vigía EPP** en **menos de 2 minutos y con mínimo consumo de tokens**, sin tener que leer todos los archivos fuente.

---

## 1. Regla de Oro del Dominio (¡NUNCA VIOLAR!)
- **SOLO SE EVALÚAN 3 PRENDAS DE EPP:**
  1. `lentes` (`sin_lentes`) — Zona Ojos: `y_rel ∈ [0.00, 0.32]`
  2. `chaleco` (`sin_chaleco`) — Zona Torso: `y_rel ∈ [0.16, 0.72]`
  3. `guantes` (`sin_guantes`) — Zona Manos: `y_rel ∈ [0.28, 0.96]`
- **PROHIBIDO agregar `casco` o `mascarilla`:** En la planta donde se instala el software no se requieren. `motor/contrato.py` define `PRENDAS_REQUERIDAS = ("lentes", "chaleco", "guantes")` y las 7 clases de `modelos/epp.pt`:
  `0: persona, 1: chaleco, 2: sin_chaleco, 3: lentes, 4: sin_lentes, 5: guantes, 6: sin_guantes`.

---

## 2. Mapa de Archivos Clave y Responsabilidades

### Backend (`motor-procesamiento/`) — Python 3.12 en `motor-procesamiento/.venv`
- [`motor/contrato.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/motor/contrato.py): Fuente única de verdad para clases YOLO (`CLASES_EPP`), zonas anatómicas (`ZONAS_RELATIVAS`), tipos de hallazgo (`TIPOS_HALLAZGO`) y umbral de confianza (`UMBRAL_CONFIANZA_PRENDA = 0.60`).
- [`motor/detector.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/motor/detector.py): Wrapper `DetectorEPP` sobre `ultralytics.YOLO("modelos/epp.pt")`.
- [`motor/asociar.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/motor/asociar.py): `asociar_epp_a_personas(detecciones)` -> vincula cada prenda detectada a su `persona` usando contención + banda vertical `ZONAS_RELATIVAS` + distancia al centro ideal de la zona.
- [`motor/rastreo.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/motor/rastreo.py): `RastreadorPersonas` -> empareja trabajadores entre cuadros por IoU, suaviza cajas con EMA y vota el estado de `lentes`, `chaleco` y `guantes` por mayoría ponderada.
- [`motor/kiosco.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/motor/kiosco.py): `evaluar_imagen(img_bgr, detector)` -> evalúa un solo frame en `<300 ms` (`~3.3 ms` en GPU) y devuelve `{estado_acceso, mensaje, zonas, faltantes, dudosas, ms_proceso, imagen_anotada_b64}`.
- [`motor/pipeline.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/motor/pipeline.py): Procesa un video completo -> genera `observaciones.json`, `recorrido_anotado.mp4` (H.264) y `recortes/L{i}-T{j}.jpg`.
- [`cruce/hallazgos.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/cruce/hallazgos.py): Cruza `observaciones.json` con `datos/sistema/{turnos,inventario_epp,reglas_riesgo}.csv` para producir `hallazgos.json`. Incluye `actualizar_corregido(ruta_json, hallazgo_id, corregido)` que persiste en disco y recalcula `dinero_en_riesgo_diario` y `dinero_recuperado_diario`.
- [`cruce/red.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/cruce/red.py): Construye `red.json` separando problemas sistémicos (`multiples_epp_faltantes`, `epp_agotado_en_caseta`) de omisiones locales en 18 plantas.
- [`cruce/chat.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/cruce/chat.py): Asistente RAG híbrido (usa Gemini si `APIGEMINI` está en `.env`, o motor RAG determinista local offline si no hay clave/red).
- [`cruce/api.py`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/cruce/api.py): Servidor HTTP multihilo en `127.0.0.1:8000`.

### Frontend (`Frontend/`) — Next.js 15.1.7 + React 19 + Tailwind CSS
- **Proxy interno (`next.config.ts`):** Reescribe `/motor/:path*` hacia `${P4_API_URL || 'http://localhost:8000'}/:path*`.
- **Tipos (`Frontend/types/`):** `hallazgos.ts`, `kiosco.ts`, `red.ts`, `analisis.ts`.
- **Cliente API (`Frontend/lib/api/analisis.ts`):** Funciones para Kiosco (`evaluarKioscoPreset`, `evaluarKioscoImagenB64`), Modo Jurado (`ejecutarTarjetaJurado`), persistencia de hallazgos (`actualizarHallazgoCorregido`), subida de video (`subirVideo`) y chat RAG (`preguntarCorrida`).
- **8 Pantallas (`Frontend/components/` y `Frontend/app/`):**
  1. `/resumen` -> `ResumenView.tsx`
  2. `/kiosco` -> `KioscoView.tsx`
  3. `/recorrido` -> `RecorridoView.tsx`
  4. `/cuadrilla` -> `CuadrillaView.tsx` (contiene `SiluetaAnatomica3Zonas` SVG)
  5. `/hallazgos` -> `HallazgosView.tsx`
  6. `/red` -> `RedView.tsx`
  7. `/analizar` -> `AnalizarView.tsx`
  8. `/asistente` -> `AsistenteView.tsx`

---

## 3. Cifras de Referencia de la Corrida Demostrativa
- **Frase Hero:** `"7 trabajadores sin EPP completo · US$3,280.00 al día en riesgo"`
- **Distribución de las 12 estaciones (`3 líneas × 4 posiciones`):**
  - `4` estaciones `ok` (`3/3 EPP`): `L1-T1`, `L1-T3`, `L3-T1`, `L3-T4` (`33.3 %` cumplimiento).
  - `7` estaciones `error`:
    - `L1-T2` (`Marco Antonio Ríos`): falta `lentes + guantes` -> `US$760.00/día`
    - `L2-T4` (`Héctor Navarro`): falta `lentes + chaleco` -> `US$710.00/día`
    - `L1-T4` (`Jorge Alberto Soto`): falta `lentes` -> `US$420.00/día`
    - `L3-T2` (`Sergio Valenzuela`): falta `lentes` -> `US$420.00/día`
    - `L2-T2` (`Roberto Domínguez`): falta `guantes` -> `US$340.00/día`
    - `L3-T3` (`Miguel Ángel Luna`): falta `guantes` -> `US$340.00/día`
    - `L2-T1` (`Ricardo Morales`): falta `chaleco` -> `US$290.00/día`
  - `1` estación `revisar`: `L2-T3` (`Daniel Espinoza`, guantes con confianza `0.48`) -> `US$0.00/día`.

---

## 4. Comandos Rápidos de Verificación y Mantenimiento

```bash
# 1. Ejecutar tests unitarios y de integración de Python (18 tests en ~1.5 s)
motor-procesamiento/.venv/bin/python -m pytest -v

# 2. Verificar tipos y build de producción de Next.js
npm --prefix Frontend run typecheck && npm --prefix Frontend run build

# 3. Regenerar datos demostrativos y publicar hacia Frontend/public/
cd motor-procesamiento && ./.venv/bin/python -m cruce.publicar

# 4. Arrancar todo el sistema (:8000 API + :3000 Frontend)
./iniciar.sh
```

---

## 5. Recetas Rápidas para Cambios Futuros
- **Cambiar el costo diario de una multa/riesgo:** Edita [`motor-procesamiento/datos/sistema/reglas_riesgo.csv`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/datos/sistema/reglas_riesgo.csv) y ejecuta `cd motor-procesamiento && ./.venv/bin/python -m cruce.publicar`.
- **Cambiar el stock de EPP en caseta:** Edita [`motor-procesamiento/datos/sistema/inventario_epp.csv`](file:///home/alexteori/Documentos/repositorios/EPP/motor-procesamiento/datos/sistema/inventario_epp.csv) y vuelve a correr `cruce.publicar`.
- **Re-entrenar `modelos/epp.pt` con más épocas:** Ejecuta `cd motor-procesamiento && ./.venv/bin/python -m entrenamiento.entrenar_yolo --epochs 50 --batch 16`.
