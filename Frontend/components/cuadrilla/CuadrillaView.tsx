'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import {
  AlertTriangle,
  CheckCircle2,
  Eye,
  Hand,
  HelpCircle,
  PackageCheck,
  ShieldAlert,
  Shirt,
  UserCheck,
} from 'lucide-react';
import { EstadoPrenda, PosicionTurno, PrendaEPP, SalidaHallazgos } from '@/types/hallazgos';
import {
  DICCIONARIO_PRENDAS,
  formatearMoneda,
  ORDEN_PRENDAS,
  traducirEstadoPosicion,
  traducirEstadoPrenda,
  traducirTipoHallazgo,
  ubicacionCorta,
  ubicacionLarga,
} from '@/lib/formatters/contract';
import { ICONO_PANTALLA } from '@/components/iconos';
import { TituloPagina } from '@/components/layout/TituloPagina';
import { PuntosPrendas } from '@/components/graficas/Barras';

const ICONO_PRENDA: Record<PrendaEPP, React.ElementType> = {
  lentes: Eye,
  chaleco: Shirt,
  guantes: Hand,
};

function colorZonaSvg(estado: EstadoPrenda): { fill: string; stroke: string } {
  if (estado === 'ok') return { fill: '#10b981', stroke: '#047857' };
  if (estado === 'falta') return { fill: '#f43f5e', stroke: '#be123c' };
  return { fill: '#f59e0b', stroke: '#b45309' };
}

/**
 * Silueta SVG del Gemelo Anatómico de 3 Zonas:
 * - Zona 1 (Ojos): Lentes de seguridad
 * - Zona 2 (Torso): Chaleco reflejante
 * - Zona 3 (Manos): Guantes anticorte
 */
function SiluetaAnatomica3Zonas({ posicion }: { posicion: PosicionTurno }) {
  const cLentes = colorZonaSvg(posicion.prendas.lentes?.estado ?? 'dudoso');
  const cChaleco = colorZonaSvg(posicion.prendas.chaleco?.estado ?? 'dudoso');
  const cGuantes = colorZonaSvg(posicion.prendas.guantes?.estado ?? 'dudoso');

  return (
    <svg
      viewBox="0 0 180 260"
      className="w-36 h-52 mx-auto select-none"
      role="img"
      aria-label={`Silueta anatómica de ${posicion.trabajador}`}
    >
      {/* Cabeza base */}
      <circle cx="90" cy="40" r="24" fill="#cbd5e1" stroke="#475569" strokeWidth="2" />

      {/* ZONA 1: LENTES DE SEGURIDAD (y: 0.00 - 0.32) */}
      <g>
        <rect
          x="68"
          y="30"
          width="44"
          height="14"
          rx="4"
          fill={cLentes.fill}
          stroke={cLentes.stroke}
          strokeWidth="2"
        />
        <line x1="88" y1="37" x2="92" y2="37" stroke="#ffffff" strokeWidth="2" />
      </g>

      {/* Cuello y piernas neutros */}
      <rect x="82" y="64" width="16" height="10" fill="#cbd5e1" />
      <rect x="66" y="162" width="20" height="75" rx="8" fill="#64748b" />
      <rect x="94" y="162" width="20" height="75" rx="8" fill="#64748b" />

      {/* Brazos superiores */}
      <rect x="38" y="76" width="18" height="62" rx="8" fill="#94a3b8" />
      <rect x="124" y="76" width="18" height="62" rx="8" fill="#94a3b8" />

      {/* ZONA 2: CHALECO REFLEJANTE EN TORSO (y: 0.16 - 0.72) */}
      <g>
        <rect
          x="58"
          y="74"
          width="64"
          height="88"
          rx="10"
          fill={cChaleco.fill}
          stroke={cChaleco.stroke}
          strokeWidth="2.5"
        />
        {/* Franjas reflejantes del chaleco */}
        <rect x="60" y="105" width="60" height="7" fill="#fef08a" opacity="0.85" />
        <rect x="60" y="132" width="60" height="7" fill="#fef08a" opacity="0.85" />
      </g>

      {/* ZONA 3: GUANTES ANTICORTE EN MANOS (y: 0.28 - 0.96) */}
      <g>
        <circle
          cx="47"
          cy="152"
          r="13"
          fill={cGuantes.fill}
          stroke={cGuantes.stroke}
          strokeWidth="2.5"
        />
        <circle
          cx="133"
          cy="152"
          r="13"
          fill={cGuantes.fill}
          stroke={cGuantes.stroke}
          strokeWidth="2.5"
        />
      </g>
    </svg>
  );
}

export function CuadrillaView({
  data,
  posicionInicial,
}: {
  data: SalidaHallazgos;
  posicionInicial?: string;
}) {
  const { resumen, posiciones } = data;
  const moneda = resumen.moneda ?? 'US$';

  const posInicialObj =
    posiciones.find((p) => p.codigo === posicionInicial || p.id === posicionInicial) ??
    posiciones.find((p) => p.estado === 'error') ??
    posiciones[0];

  const [seleccionada, setSeleccionada] = useState<PosicionTurno | undefined>(posInicialObj);
  const [filtroEstado, setFiltroEstado] = useState<'todos' | 'error' | 'revisar' | 'ok'>('todos');

  const lineas = [1, 2, 3].map((numLinea) => ({
    linea: numLinea,
    estaciones: posiciones.filter((p) => p.linea === numLinea),
  }));

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <TituloPagina
          icono={ICONO_PANTALLA.cuadrilla}
          titulo="Gemelo Digital de Cuadrilla y Anatomía EPP"
        >
          Inspección estación por estación de las 3 líneas del turno. Selecciona un trabajador para
          auditar sus 3 zonas anatómicas (Lentes, Chaleco y Guantes).
        </TituloPagina>

        <div className="flex items-center gap-1.5 bg-white p-1 rounded-lg border border-slate-200 text-xs">
          {[
            { id: 'todos', label: `Todos (${posiciones.length})` },
            {
              id: 'error',
              label: `Incompletos (${posiciones.filter((p) => p.estado === 'error').length})`,
            },
            {
              id: 'revisar',
              label: `Dudosas (${posiciones.filter((p) => p.estado === 'revisar').length})`,
            },
            {
              id: 'ok',
              label: `Completos (${posiciones.filter((p) => p.estado === 'ok').length})`,
            },
          ].map((f) => (
            <button
              key={f.id}
              type="button"
              onClick={() => setFiltroEstado(f.id as typeof filtroEstado)}
              className={`px-2.5 py-1.5 rounded-md font-semibold transition-colors ${
                filtroEstado === f.id
                  ? 'bg-slate-900 text-white'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Izquierda: Matriz de las 3 líneas de formación pre-turno */}
        <section className="lg:col-span-7 space-y-4">
          {lineas.map(({ linea, estaciones }) => (
            <div
              key={linea}
              className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-3"
            >
              <div className="flex items-center justify-between border-b border-slate-100 pb-2.5">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Línea de Formación {linea}
                </span>
                <span className="text-xs text-slate-500 font-tabular">
                  {estaciones.filter((e) => e.estado === 'ok').length}/{estaciones.length} con EPP
                  completo
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {estaciones.map((pos) => {
                  const activa = seleccionada?.id === pos.id;
                  const atenuada = filtroEstado !== 'todos' && pos.estado !== filtroEstado;

                  const borderColor =
                    pos.estado === 'ok'
                      ? 'border-emerald-200 bg-emerald-50/30'
                      : pos.estado === 'error'
                      ? 'border-rose-200 bg-rose-50/40'
                      : 'border-amber-200 bg-amber-50/40';

                  return (
                    <button
                      key={pos.id}
                      type="button"
                      data-testid={`estacion-card-${pos.codigo}`}
                      onClick={() => setSeleccionada(pos)}
                      className={`text-left p-3.5 rounded-xl border transition-all flex items-start gap-3 ${borderColor} ${
                        activa ? 'ring-2 ring-teal-600 border-teal-600 shadow-sm' : ''
                      } ${atenuada ? 'opacity-40' : ' opacity-100'}`}
                    >
                      <img
                        src={pos.evidencia}
                        alt={pos.trabajador}
                        className="w-14 h-14 rounded-lg object-cover border border-slate-200 bg-slate-900 shrink-0"
                      />
                      <div className="min-w-0 flex-1 space-y-1">
                        <div className="flex items-center justify-between gap-1">
                          <span className="font-mono text-xs font-bold text-slate-900">
                            {ubicacionCorta(pos)}
                          </span>
                          <PuntosPrendas
                            hay={pos.prendas_completas}
                            esperados={pos.prendas_requeridas}
                          />
                        </div>
                        <div className="font-bold text-sm text-slate-900 truncate">
                          {pos.trabajador}
                        </div>
                        <div className="text-xs text-slate-500 truncate">{pos.puesto}</div>
                        <div className="pt-1 flex items-center justify-between text-[11px]">
                          <span
                            className={`font-semibold ${
                              pos.estado === 'ok'
                                ? 'text-emerald-700'
                                : pos.estado === 'error'
                                ? 'text-rose-700'
                                : 'text-amber-700'
                            }`}
                          >
                            {pos.estado === 'ok'
                              ? '3/3 Completo'
                              : pos.tipo
                              ? traducirTipoHallazgo(pos.tipo)
                              : 'Revisar'}
                          </span>
                          {pos.impacto_diario ? (
                            <span className="font-bold text-rose-700 font-tabular">
                              {formatearMoneda(pos.impacto_diario, moneda)}
                            </span>
                          ) : null}
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </section>

        {/* Derecha: Gemelo Anatómico de 3 Zonas del trabajador seleccionado */}
        {seleccionada && (
          <section
            data-testid="gemelo-anatomico-panel"
            className="lg:col-span-5 bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-5 sticky top-16"
          >
            <div className="flex items-start justify-between gap-3 border-b border-slate-100 pb-4">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-slate-900 text-white">
                    {seleccionada.codigo}
                  </span>
                  <span className="font-mono text-xs text-slate-500">
                    {seleccionada.id_empleado}
                  </span>
                </div>
                <h3 className="text-lg font-bold text-slate-900 mt-1">{seleccionada.trabajador}</h3>
                <p className="text-xs text-slate-500">{ubicacionLarga(seleccionada)}</p>
              </div>

              <span
                className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                  seleccionada.estado === 'ok'
                    ? 'bg-emerald-100 text-emerald-800'
                    : seleccionada.estado === 'error'
                    ? 'bg-rose-100 text-rose-800'
                    : 'bg-amber-100 text-amber-800'
                }`}
              >
                {traducirEstadoPosicion(seleccionada.estado)}
              </span>
            </div>

            {/* Silueta SVG + Evidencia fotográfica real lado a lado */}
            <div className="grid grid-cols-2 gap-4 items-center bg-slate-50 rounded-xl p-4 border border-slate-200/80">
              <div className="text-center space-y-1">
                <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                  Gemelo Anatómico (3 Zonas)
                </div>
                <SiluetaAnatomica3Zonas posicion={seleccionada} />
              </div>

              <div className="space-y-2">
                <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                  Recorte de Evidencia Real
                </div>
                <img
                  src={seleccionada.evidencia_zona || seleccionada.evidencia}
                  alt={seleccionada.trabajador}
                  className="w-full h-44 object-cover rounded-lg border border-slate-300 bg-slate-900"
                />
                {seleccionada.impacto_diario ? (
                  <div className="p-2 rounded bg-rose-100/80 text-rose-900 text-xs font-bold text-center font-tabular">
                    Riesgo: {formatearMoneda(seleccionada.impacto_diario, moneda)}/día
                  </div>
                ) : (
                  <div className="p-2 rounded bg-emerald-100/80 text-emerald-900 text-xs font-bold text-center">
                    Sin exposición monetaria (US$0.00)
                  </div>
                )}
              </div>
            </div>

            {/* Desglose de las 3 prendas obligatorias */}
            <div className="space-y-2.5">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Estado por prenda obligatoria y stock en caseta
              </h4>
              {ORDEN_PRENDAS.map((pr) => {
                const detalle = seleccionada.prendas[pr];
                const info = DICCIONARIO_PRENDAS[pr];
                const Icon = ICONO_PRENDA[pr];
                const est = detalle?.estado ?? 'dudoso';

                return (
                  <div
                    key={pr}
                    className="p-3 rounded-lg border border-slate-200 flex items-center justify-between gap-3"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <span
                        className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                          est === 'ok'
                            ? 'bg-emerald-100 text-emerald-700'
                            : est === 'falta'
                            ? 'bg-rose-100 text-rose-700'
                            : 'bg-amber-100 text-amber-700'
                        }`}
                      >
                        <Icon className="w-4 h-4" />
                      </span>
                      <div className="min-w-0">
                        <div className="text-xs font-bold text-slate-900">{info.nombre}</div>
                        <div className="text-[11px] text-slate-500 truncate">
                          Confianza {Math.round((detalle?.confianza ?? 0.9) * 100)}% ·{' '}
                          {detalle?.lecturas ?? 5} cuadros votados
                        </div>
                      </div>
                    </div>

                    <div className="text-right shrink-0">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-bold ${
                          est === 'ok'
                            ? 'bg-emerald-100 text-emerald-800'
                            : est === 'falta'
                            ? 'bg-rose-100 text-rose-800'
                            : 'bg-amber-100 text-amber-800'
                        }`}
                      >
                        {traducirEstadoPrenda(est)}
                      </span>
                      <div className="text-[11px] text-slate-500 mt-0.5 font-tabular inline-flex items-center gap-1">
                        <PackageCheck className="w-3 h-3 text-teal-600" />
                        {detalle?.stock_caseta ?? 12} en caseta
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {seleccionada.accion && (
              <div className="p-3.5 rounded-lg bg-slate-900 text-white text-xs space-y-1.5">
                <div className="font-bold text-teal-300 uppercase tracking-wider text-[11px]">
                  Instrucción para Caseta Pre-Turno
                </div>
                <p className="text-slate-200 leading-relaxed">{seleccionada.accion}</p>
                {seleccionada.hallazgo_id && (
                  <div className="pt-1">
                    <Link
                      href="/hallazgos"
                      className="inline-flex items-center gap-1 text-teal-300 font-semibold hover:underline"
                    >
                      Ir a Hallazgos para autorizar tras entrega →
                    </Link>
                  </div>
                )}
              </div>
            )}
          </section>
        )}
      </div>
    </div>
  );
}
