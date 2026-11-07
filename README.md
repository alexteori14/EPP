# Vigía EPP · Inspección Pre-Turno de Equipo de Protección Personal (Consola SCADA/HMI)

**Vigía EPP** es una plataforma industrial de visión por computadora y auditoría operativa que verifica que cada trabajador porte su **Equipo de Protección Personal (EPP) obligatorio completo** antes de iniciar su turno en planta.

> **Regla de Dominio de Planta (4 Zonas Anatómicas + Guantes Condicionales por Puesto):** En esta instalación industrial **no se exige casco ni mascarilla**. El sistema inspecciona **4 componentes de EPP**:
> 1. **Lentes de seguridad ANSI Z87.1** (`lentes` / `sin_lentes`) — Zona Ojos/Rostro (`y ∈ [0.00, 0.32]`) · **Obligatorio General** (`US$420.00/día`)
> 2. **Tapones auditivos de inserción NRR 32 dB NOM-011-STPS** (`tapones` / `sin_tapones`) — Zona Oídos/Cráneo Lateral (`y ∈ [0.04, 0.28]`) · **Obligatorio General** (`US$380.00/día`)
> 3. **Chaleco reflejante Clase 2** (`chaleco` / `sin_chaleco`) — Zona Torso (`y ∈ [0.16, 0.72]`) · **Obligatorio General** (`US$290.00/día`)
> 4. **Guantes anticorte Nivel A4** (`guantes` / `sin_guantes`) — Zona Manos/Muñecas (`y ∈ [0.28, 0.96]`) · **Obligatorio en puestos operativos (`US$340.00/día`) / Opcional en puestos de supervisión, inspección, almacén y montacargas (`US$0.00`, acceso autorizado)**

---

## Arranque rápido (1 comando)

```bash
./iniciar.sh
```

Esto levanta automáticamente:
- **API del Motor y Cruce Operativo** en `http://127.0.0.1:8000` (`cruce.api`)
- **Consola SCADA Next.js 15 (Opción 1)** en `http://localhost:3000` (`Frontend/`)

---

## Qué resuelve y por qué importa

En turnos industriales de manufactura y logística (`94.2 dB(A)` de ruido en nave), una parte de la plantilla intenta ingresar con el EPP incompleto por prisa o incomodidad. La supervisión manual en el cambio de turno deja pasar omisiones que derivan en lesiones oculares, daño auditivo inducido por ruido (`NOM-011-STPS`), cortes manuales, paros de estación y multas bajo **NOM-017-STPS**.

**Vigía EPP** cubre los dos momentos críticos del control de acceso:
1. **Torniquete en Vivo (`/kiosco`)**: Evalúa una cámara web, fotografía o preset de torniquete en **`< 300 ms`** (`3.3 ms` de inferencia en GPU), permite seleccionar si el puesto exige guantes o si son opcionales, y emite el veredicto `"TORNIQUETE LIBERADO · PASE AUTORIZADO"` o `"TORNIQUETE BLOQUEADO · FALTA EPP"` junto con el estado de las 4 zonas anatómicas.
2. **Auditoría de Fila y Cuadrilla (`/resumen`, `/recorrido`, `/cuadrilla`, `/hallazgos`, `/red`, `/analizar`, `/asistente`)**: Analiza el video de formación pre-turno (`recorrido_turno.mp4`), asocia cada prenda a cada trabajador mediante geometría anatómica de 4 zonas y votación multi-cuadro, cruza contra el stock disponible en caseta (`inventario_epp.csv`) y prioriza las omisiones en dólares de riesgo diario (`US$3,620.00/día` en la corrida demostrativa).

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
│   ├── modelos/epp.pt                # Modelo YOLO11 entrenado
│   ├── modelos/epp.json              # Métricas reales de validación (mAP50: 0.672)
│   ├── entrenamiento/                # Descarga Kaggle MCP, armonización a 9 clases y entrenamiento YOLO11
│   ├── motor/                        # Selección de cuadros, detector, asociación 4 zonas, rastreo, kiosco
│   ├── cruce/                        # Reglas de riesgo, impacto en red (18 plantas), RAG y API :8000
│   ├── simulador/                    # Generador de turno de 12 estaciones y 5 tarjetas de Modo Jurado
│   └── tests/                        # 19 pruebas unitarias y de integración (pytest)
└── Frontend/                         # Consola SCADA/HMI Next.js 15 + React 19 + Tailwind CSS (Opción 1)
    ├── DISENO.md                     # Sistema de diseño "Centro de Comando Industrial SCADA/HMI"
    ├── app/                          # 8 rutas dinámicas (/resumen, /kiosco, /recorrido, /cuadrilla, ...)
    ├── components/                   # Vistas SCADA, Gemelo Anatómico SVG de 4 zonas y gráficas
    └── tests/e2e.mjs                 # Suite E2E de Playwright que verifica las 8 pantallas
```

---

## Pruebas automatizadas

```bash
# 1. Suite de pruebas del motor y cruce (19 tests)
motor-procesamiento/.venv/bin/python -m pytest -v

# 2. Verificación de tipos y compilación de producción del Frontend
npm --prefix Frontend run build
```
