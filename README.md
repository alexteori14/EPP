# Vigía EPP · Inspección Pre-Turno de Equipo de Protección Personal

**Vigía EPP** es una plataforma industrial de visión por computadora y auditoría operativa que verifica que cada trabajador porte su **Equipo de Protección Personal (EPP) obligatorio completo** antes de iniciar su turno en planta.

> **Regla de Dominio de Planta:** En esta instalación industrial **no se exige casco ni mascarilla**. El sistema inspecciona única y exclusivamente las **3 prendas obligatorias de planta**:
> 1. **Lentes de seguridad ANSI Z87.1** (`lentes` / `sin_lentes`) — Zona Ojos/Rostro (`y ∈ [0.00, 0.32]`)
> 2. **Chaleco reflejante Clase 2** (`chaleco` / `sin_chaleco`) — Zona Torso (`y ∈ [0.16, 0.72]`)
> 3. **Guantes anticorte Nivel A4** (`guantes` / `sin_guantes`) — Zona Manos/Muñecas (`y ∈ [0.28, 0.96]`)

---

## Arranque rápido (1 comando)

```bash
./iniciar.sh
```

Esto levanta automáticamente:
- **API del Motor y Cruce Operativo** en `http://127.0.0.1:8000` (`cruce.api`)
- **Tablero Next.js 15 (App Router)** en `http://localhost:3000` (`Frontend/`)

---

## Qué resuelve y por qué importa

En turnos industriales de manufactura y logística, una parte de la plantilla intenta ingresar con el EPP incompleto por prisa o incomodidad. La supervisión manual en el cambio de turno deja pasar omisiones que derivan en lesiones oculares/manuales, paros de estación y multas bajo **NOM-017-STPS**.

**Vigía EPP** cubre los dos momentos críticos del control de acceso:
1. **Kiosco de Pase de Turno en Vivo (`/kiosco`)**: Evalúa una cámara web, fotografía o preset de torniquete en **`< 300 ms`** (`3.3 ms` de inferencia en GPU) y emite el veredicto `"PASE DE TURNO AUTORIZADO"` o `"ACCESO DETENIDO · FALTA EPP"` junto con el estado de las 3 zonas anatómicas.
2. **Auditoría de Fila y Cuadrilla (`/resumen`, `/recorrido`, `/cuadrilla`, `/hallazgos`, `/red`, `/analizar`, `/asistente`)**: Analiza el video de formación pre-turno (`recorrido_turno.mp4`), asocia cada prenda a cada trabajador mediante geometría anatómica y votación multi-cuadro, cruza contra el stock disponible en caseta (`inventario_epp.csv`) y prioriza las omisiones en dólares de riesgo diario (`US$3,280.00/día` en la corrida demostrativa).

---

## Estructura del repositorio

```text
EPP/
├── iniciar.sh                        # Lanzador unificado (:8000 API + :3000 Next.js)
├── documentacion.md                  # Documentación técnica exhaustiva del proyecto
├── memoria.md                        # Memoria técnica compacta para agentes de IA futuros
├── PITCH.md                          # Guion ejecutivo de demostración (5 minutos)
├── motor-procesamiento/              # Motor de visión YOLO11, cruce financiero y API HTTP
│   ├── CONTRATO.md                   # Contrato estricto de JSONs entre motor, cruce y web
│   ├── modelos/epp.pt                # Modelo YOLO11 entrenado (7 clases canónicas)
│   ├── modelos/epp.json              # Métricas reales de validación (mAP50: 0.672)
│   ├── entrenamiento/                # Descarga Kaggle MCP, armonización y entrenamiento YOLO11
│   ├── motor/                        # Selección de cuadros, detector, asociación 3 zonas, rastreo, kiosco
│   ├── cruce/                        # Reglas de riesgo, impacto en red (18 plantas), RAG y API :8000
│   ├── simulador/                    # Generador de turno de 12 estaciones y 4 tarjetas de Modo Jurado
│   └── tests/                        # 18 pruebas unitarias y de integración (pytest)
└── Frontend/                         # Aplicación Next.js 15 + React 19 + Tailwind CSS
    ├── DISENO.md                     # Sistema de diseño "Industrial Safety Slate"
    ├── app/                          # 8 rutas dinámicas (/resumen, /kiosco, /recorrido, /cuadrilla, ...)
    ├── components/                   # Vistas interactivas, Gemelo Anatómico SVG de 3 zonas y gráficas
    └── tests/e2e.mjs                 # Suite E2E de Playwright que verifica las 8 pantallas
```

---

## Pruebas automatizadas

```bash
# 1. Suite de pruebas del motor y cruce (18 tests)
motor-procesamiento/.venv/bin/python -m pytest -v

# 2. Verificación de tipos y compilación de producción del Frontend
npm --prefix Frontend run typecheck
npm --prefix Frontend run build
```
