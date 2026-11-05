'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import {
  AlertTriangle,
  ArrowRight,
  Camera,
  CheckCircle2,
  Eye,
  Hand,
  HelpCircle,
  Loader2,
  Play,
  ShieldAlert,
  Shirt,
  Sparkles,
  Users,
} from 'lucide-react';
import { Hallazgo, RespuestaEnsayoJurado, SalidaHallazgos } from '@/types/hallazgos';
import {
  formatearMoneda,
  ORDEN_PRENDAS,
  totalesPorFamilia,
  traducirPrenda,
  traducirTipoHallazgo,
  ubicacionCorta,
} from '@/lib/formatters/contract';
import { ejecutarTarjetaJurado } from '@/lib/api/analisis';
import { ICONO_PANTALLA } from '@/components/iconos';
import { TituloPagina } from '@/components/layout/TituloPagina';
import { Barra, BarraApilada, Proporcion } from '@/components/graficas/Barras';

const TARJETAS_JURADO = [
  {
    id: 'sin_lentes',
    titulo: 'Trabajador sin Lentes',
    subtitulo: 'Ojos descubiertos · Riesgo US$420/día',
    icono: Eye,
  },
  {
    id: 'sin_guantes',
    titulo: 'Trabajador sin Guantes',
    subtitulo: 'Manos descubiertas · Riesgo US$340/día',
    icono: Hand,
  },
  {
    id: 'sin_chaleco',
    titulo: 'Trabajador sin Chaleco',
    subtitulo: 'Sin alta visibilidad · Riesgo US$290/día',
    icono: Shirt,
  },
  {
    id: 'multiple_faltante',
    titulo: 'Múltiple EPP faltante',
    subtitulo: 'Sin lentes ni guantes · Riesgo US$760/día',
    icono: ShieldAlert,
  },
];

export function ResumenView({ data }: { data: SalidaHallazgos }) {
  const { resumen, posiciones, hallazgos } = data;
  const moneda = resumen.moneda ?? 'US$';

  const [tarjetaActiva, setTarjetaActiva] = useState<string | null>(null);
  const [cargandoJurado, setCargandoJurado] = useState(false);
  const [ensayo, setEnsayo] = useState<RespuestaEnsayoJurado | null>(null);
  const [errorJurado, setErrorJurado] = useState<string | null>(null);

  const hallazgosPendientes = hallazgos.filter((h) => !h.corregido && h.impacto_diario > 0);
  const topPrioridad = [...hallazgosPendientes]
    .sort((a, b) => b.impacto_diario - a.impacto_diario)
    .slice(0, 3);
  const familias = totalesPorFamilia(hallazgos);
  const maxFamiliaMonto = Math.max(...familias.map((f) => f.monto), 1);

  const totalPosiciones = posiciones.length || 12;
  const completasCount = posiciones.filter((p) => p.estado === 'ok').length;
  const errorCount = posiciones.filter((p) => p.estado === 'error').length;
  const revisarCount = posiciones.filter((p) => p.estado === 'revisar').length;

  const probarTarjeta = async (id: string) => {
    setTarjetaActiva(id);
    setCargandoJurado(true);
    setErrorJurado(null);
    try {
      const res = await ejecutarTarjetaJurado(id);
      setEnsayo(res);
    } catch (e: unknown) {
      setErrorJurado(e instanceof Error ? e.message : 'Error al procesar tarjeta');
    } finally {
      setCargandoJurado(false);
    }
  };

  const hallazgoNuevo: Hallazgo | null | undefined = ensayo?.hallazgo_nuevo;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <TituloPagina icono={ICONO_PANTALLA.resumen} titulo="Resumen de Turno y Riesgo Operativo">
          {resumen.planta_nombre ?? 'Planta Monterrey Norte'} ·{' '}
          {resumen.turno_nombre ?? 'Turno Matutino 06:00'} (Evaluando: Lentes, Chaleco y Guantes)
        </TituloPagina>

        <div className="flex items-center gap-2.5">
          <Link
            href="/kiosco"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-teal-600 hover:bg-teal-700 text-white text-sm font-semibold shadow-sm transition-colors"
          >
            <Camera className="w-4 h-4" />
            Abrir Kiosco en Vivo
          </Link>
          <Link
            href="/cuadrilla"
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-sm font-medium transition-colors"
          >
            <Users className="w-4 h-4 text-slate-500" />
            Ver Cuadrilla
          </Link>
        </div>
      </div>

      {/* Bloque Hero: Frase obligatoria de impacto y desglose rápido */}
      <section className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-5">
        <div className="flex flex-col lg:flex-row lg:items-baseline justify-between gap-4 border-b border-slate-100 pb-5">
          <div className="space-y-1.5">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 ring-1 ring-inset ring-rose-200">
              <AlertTriangle className="w-3.5 h-3.5" />
              Filtro de ingreso a planta
            </span>
            <h3
              data-testid="hero-frase"
              className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight font-tabular"
            >
              {resumen.frase}
            </h3>
            <p className="text-sm text-slate-500">
              Cada omisión de EPP representa riesgo de lesión, paro de estación o sanción bajo
              NOM-017-STPS.
            </p>
          </div>

          <div className="flex items-center gap-6 shrink-0">
            <div className="text-right">
              <div className="text-xs text-slate-500 uppercase tracking-wider font-medium">
                Riesgo Diario Activo
              </div>
              <div className="text-2xl font-bold text-rose-600 font-tabular">
                {formatearMoneda(resumen.dinero_en_riesgo_diario, moneda)}
                <span className="text-xs font-normal text-slate-500">/día</span>
              </div>
            </div>
            {(resumen.dinero_recuperado_diario ?? 0) > 0 && (
              <div className="text-right border-l border-slate-200 pl-5">
                <div className="text-xs text-emerald-700 uppercase tracking-wider font-medium">
                  Riesgo Mitigado Hoy
                </div>
                <div className="text-2xl font-bold text-emerald-600 font-tabular">
                  {formatearMoneda(resumen.dinero_recuperado_diario, moneda)}
                  <span className="text-xs font-normal text-slate-500">/día</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* 4 indicadores clave del turno */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200/70">
            <div className="text-xs text-slate-500 font-medium">Cumplimiento de cuadrilla</div>
            <div className="mt-1 flex items-baseline justify-between">
              <span className="text-2xl font-bold text-slate-900 font-tabular">
                {resumen.cumplimiento_turno_pct}%
              </span>
              <span className="text-xs text-slate-500 font-tabular">
                {completasCount}/{totalPosiciones} con 3/3 EPP
              </span>
            </div>
            <Proporcion pct={resumen.cumplimiento_turno_pct} tono="bg-emerald-600" className="mt-2.5" />
          </div>

          <div className="p-4 rounded-lg bg-rose-50/50 border border-rose-200/70">
            <div className="text-xs text-rose-700 font-medium">Trabajadores sin EPP completo</div>
            <div className="mt-1 flex items-baseline justify-between">
              <span className="text-2xl font-bold text-rose-700 font-tabular">
                {resumen.trabajadores_incompletos}
              </span>
              <span className="text-xs text-rose-600">Acceso detenido</span>
            </div>
            <Proporcion
              pct={(resumen.trabajadores_incompletos / totalPosiciones) * 100}
              tono="bg-rose-600"
              className="mt-2.5"
            />
          </div>

          <div className="p-4 rounded-lg bg-amber-50/50 border border-amber-200/70">
            <div className="text-xs text-amber-800 font-medium">Lecturas dudosas (revisar)</div>
            <div className="mt-1 flex items-baseline justify-between">
              <span className="text-2xl font-bold text-amber-700 font-tabular">
                {resumen.lecturas_dudosas}
              </span>
              <span className="text-xs text-amber-700 font-tabular">US$0.00 asignados</span>
            </div>
            <p className="text-[11px] text-amber-700/90 mt-2">
              Honestidad operativa: no se estima multa cuando la zona se vio oculta.
            </p>
          </div>

          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200/70">
            <div className="text-xs text-slate-500 font-medium">Stock en caseta pre-turno</div>
            <div className="mt-1 flex items-baseline justify-between">
              <span className="text-2xl font-bold text-emerald-700 font-tabular">
                {resumen.epp_agotados === 0 ? 'Disponible' : `${resumen.epp_agotados} agotados`}
              </span>
              <span className="text-xs text-slate-500">Entrega inmediata</span>
            </div>
            <p className="text-[11px] text-slate-500 mt-2">
              Lentes (18), Chalecos (12) y Guantes (24) listos en filtro.
            </p>
          </div>
        </div>
      </section>

      {/* Dos columnas: ¿En qué se va el riesgo? y Top 3 urgencias por resolver */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <section className="lg:col-span-6 bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex flex-col justify-between space-y-4">
          <div>
            <h3 className="text-base font-bold text-slate-900">
              Desglose de exposición por tipo de omisión
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Dinero diario en juego agrupado por prenda de protección omitida.
            </p>

            <div className="mt-5 space-y-4">
              {familias.map((fam) => (
                <div key={fam.id} className="space-y-1.5">
                  <div className="flex items-baseline justify-between text-sm">
                    <span className="font-medium text-slate-800">{fam.nombre}</span>
                    <span className="font-semibold text-slate-900 font-tabular">
                      {formatearMoneda(fam.monto, moneda)}/día{' '}
                      <span className="text-xs font-normal text-slate-500">
                        ({fam.cantidad} {fam.cantidad === 1 ? 'caso' : 'casos'})
                      </span>
                    </span>
                  </div>
                  <Barra
                    pct={(fam.monto / maxFamiliaMonto) * 100}
                    tono={fam.monto > 0 ? 'bg-rose-600' : 'bg-amber-500'}
                  />
                </div>
              ))}
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100 text-xs text-slate-500 leading-relaxed">
            <strong className="text-slate-700">Criterio de cálculo:</strong>{' '}
            {resumen.supuestos_calculo}
          </div>
        </section>

        <section className="lg:col-span-6 bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-slate-900">
                Prioridad inmediata en caseta (Top 3)
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Trabajadores que concentran el mayor riesgo diario antes de iniciar turno.
              </p>
            </div>
            <Link
              href="/hallazgos"
              className="text-xs font-semibold text-teal-700 hover:text-teal-800 inline-flex items-center gap-1"
            >
              Ver los {hallazgos.length} hallazgos
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="space-y-3">
            {topPrioridad.map((h, idx) => (
              <div
                key={h.id}
                className="flex items-center gap-3.5 p-3 rounded-lg border border-slate-200 hover:border-slate-300 bg-slate-50/60 transition-colors"
              >
                <div className="w-7 h-7 rounded-full bg-rose-100 text-rose-800 font-bold text-xs flex items-center justify-center shrink-0 font-tabular">
                  #{idx + 1}
                </div>
                <img
                  src={h.evidencia_persona || h.evidencia_crop}
                  alt={h.trabajador}
                  className="w-12 h-12 rounded-lg object-cover border border-slate-200 bg-slate-900 shrink-0"
                />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-semibold px-1.5 py-0.5 rounded bg-slate-200/80 text-slate-800">
                      {h.codigo}
                    </span>
                    <span className="font-semibold text-sm text-slate-900 truncate">
                      {h.trabajador}
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 truncate mt-0.5">
                    {traducirTipoHallazgo(h.tipo)} ·{' '}
                    {h.prendas_faltantes.map(traducirPrenda).join(' + ')}
                  </p>
                </div>
                <div className="text-right shrink-0">
                  <div className="text-sm font-bold text-rose-600 font-tabular">
                    {formatearMoneda(h.impacto_diario, moneda)}/día
                  </div>
                  <Link
                    href={`/cuadrilla?pos=${h.codigo}`}
                    className="text-[11px] font-medium text-teal-700 hover:underline"
                  >
                    Inspeccionar →
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>

      {/* Vista rápida de las 3 líneas del turno */}
      <section className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h3 className="text-base font-bold text-slate-900">
              Mapa rápido de la cuadrilla (3 líneas × 4 estaciones)
            </h3>
            <p className="text-xs text-slate-500">
              Haz clic en cualquier trabajador para abrir su Gemelo Anatómico de 3 zonas (Lentes,
              Chaleco y Guantes).
            </p>
          </div>
          <div className="flex items-center gap-4 text-xs">
            <span className="inline-flex items-center gap-1.5 text-slate-600">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
              3/3 Completo ({completasCount})
            </span>
            <span className="inline-flex items-center gap-1.5 text-slate-600">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
              Incompleto ({errorCount})
            </span>
            <span className="inline-flex items-center gap-1.5 text-slate-600">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
              Revisar ({revisarCount})
            </span>
          </div>
        </div>

        <BarraApilada
          partes={[
            { clave: 'ok', valor: completasCount, tono: 'bg-emerald-500' },
            { clave: 'error', valor: errorCount, tono: 'bg-rose-500' },
            { clave: 'revisar', valor: revisarCount, tono: 'bg-amber-400' },
          ]}
        />

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1">
          {posiciones.map((pos) => {
            const estilos =
              pos.estado === 'ok'
                ? 'border-emerald-200 bg-emerald-50/40 hover:border-emerald-400'
                : pos.estado === 'error'
                ? 'border-rose-200 bg-rose-50/50 hover:border-rose-400'
                : 'border-amber-200 bg-amber-50/50 hover:border-amber-400';

            return (
              <Link
                key={pos.id}
                href={`/cuadrilla?pos=${pos.codigo}`}
                className={`p-3 rounded-lg border transition-all flex flex-col justify-between gap-2 ${estilos}`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-xs font-bold text-slate-800">
                    {ubicacionCorta(pos)}
                  </span>
                  <span
                    className={`text-[11px] font-semibold px-1.5 py-0.5 rounded font-tabular ${
                      pos.estado === 'ok'
                        ? 'bg-emerald-100 text-emerald-800'
                        : pos.estado === 'error'
                        ? 'bg-rose-100 text-rose-800'
                        : 'bg-amber-100 text-amber-800'
                    }`}
                  >
                    {pos.prendas_completas}/{pos.prendas_requeridas} EPP
                  </span>
                </div>
                <div>
                  <div className="text-xs font-semibold text-slate-900 truncate">
                    {pos.trabajador}
                  </div>
                  <div className="text-[11px] text-slate-500 truncate">{pos.puesto}</div>
                </div>
                <div className="flex items-center justify-between pt-1 border-t border-slate-200/60 text-[11px]">
                  <span className="text-slate-600 truncate">
                    {ORDEN_PRENDAS.map((pr) => {
                      const est = pos.prendas[pr]?.estado;
                      return est === 'ok' ? '●' : est === 'falta' ? '○' : '◐';
                    }).join(' ')}{' '}
                    L·C·G
                  </span>
                  {pos.impacto_diario ? (
                    <span className="font-bold text-rose-700 font-tabular">
                      {formatearMoneda(pos.impacto_diario, moneda)}
                    </span>
                  ) : (
                    <span className="text-emerald-700 font-medium">OK</span>
                  )}
                </div>
              </Link>
            );
          })}
        </div>
      </section>

      {/* Modo Jurado en Vivo */}
      <section className="bg-slate-900 text-white rounded-xl border border-slate-800 p-6 shadow-sm space-y-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div className="space-y-1">
            <div className="inline-flex items-center gap-1.5 text-xs font-semibold text-teal-400 uppercase tracking-wider">
              <Sparkles className="w-3.5 h-3.5" />
              Modo Jurado en Vivo · Verificación instantánea del motor
            </div>
            <h3 className="text-lg font-bold text-white">
              Simula un trabajador llegando a la fila sin una prenda obligatoria
            </h3>
            <p className="text-xs text-slate-300">
              Selecciona uno de los 4 escenarios reales para comparar contra la cuadrilla base y
              aislar el incumplimiento nuevo.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {TARJETAS_JURADO.map((t) => {
            const Icon = t.icono;
            const activa = tarjetaActiva === t.id;
            return (
              <button
                key={t.id}
                type="button"
                data-testid={`jurado-btn-${t.id}`}
                onClick={() => probarTarjeta(t.id)}
                disabled={cargandoJurado}
                className={`text-left p-4 rounded-xl border transition-all flex flex-col justify-between gap-3 ${
                  activa
                    ? 'bg-teal-950/90 border-teal-400 ring-1 ring-teal-400'
                    : 'bg-slate-800/80 border-slate-700 hover:border-slate-500 hover:bg-slate-800'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="w-8 h-8 rounded-lg bg-slate-700/80 text-teal-300 flex items-center justify-center">
                    <Icon className="w-4 h-4" />
                  </span>
                  <span className="inline-flex items-center gap-1 text-xs font-semibold text-teal-300">
                    {cargandoJurado && activa ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Play className="w-3.5 h-3.5" />
                    )}
                    Probar
                  </span>
                </div>
                <div>
                  <div className="font-semibold text-sm text-white">{t.titulo}</div>
                  <div className="text-xs text-slate-400 mt-0.5">{t.subtitulo}</div>
                </div>
              </button>
            );
          })}
        </div>

        {errorJurado && (
          <div className="p-4 rounded-lg bg-rose-950/60 border border-rose-700 text-xs text-rose-200">
            {errorJurado}
          </div>
        )}

        {ensayo && hallazgoNuevo && (
          <div
            data-testid="jurado-resultado"
            className="p-5 rounded-xl bg-slate-800/90 border border-teal-500/40 flex flex-col md:flex-row items-start md:items-center justify-between gap-5"
          >
            <div className="flex items-start gap-4">
              <img
                src={hallazgoNuevo.evidencia_persona || hallazgoNuevo.evidencia_crop}
                alt={hallazgoNuevo.trabajador}
                className="w-20 h-20 rounded-lg object-cover border border-slate-600 shrink-0 bg-slate-950"
              />
              <div className="space-y-1.5">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                    ACCESO DETENIDO EN FILTRO
                  </span>
                  <span className="font-mono text-xs text-slate-300">
                    Estación {hallazgoNuevo.codigo} · {hallazgoNuevo.id_empleado}
                  </span>
                  <span className="text-xs text-slate-400 font-tabular">
                    Procesado en {ensayo.segundos_proceso ?? 3.2} s · Confianza{' '}
                    {Math.round(hallazgoNuevo.confianza * 100)}%
                  </span>
                </div>
                <h4 className="text-base font-bold text-white">
                  {hallazgoNuevo.trabajador} — {traducirTipoHallazgo(hallazgoNuevo.tipo)}
                </h4>
                <p className="text-xs text-slate-300">{hallazgoNuevo.descripcion}</p>
                <p className="text-xs text-teal-300 font-medium">
                  Acción: {hallazgoNuevo.accion_sugerida}
                </p>
              </div>
            </div>

            <div className="text-left md:text-right shrink-0 border-t md:border-t-0 md:border-l border-slate-700 pt-3 md:pt-0 md:pl-5">
              <div className="text-xs text-slate-400">Exposición evitada hoy</div>
              <div className="text-2xl font-bold text-rose-400 font-tabular">
                {formatearMoneda(hallazgoNuevo.impacto_diario, moneda)}/día
              </div>
              <div className="mt-1 inline-flex items-center gap-1 text-xs text-emerald-400">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Faltante: {hallazgoNuevo.prendas_faltantes.map(traducirPrenda).join(', ')}
              </div>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
