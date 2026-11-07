'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Ear, Eye, Hand, PackageCheck, Shirt } from 'lucide-react';
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
  tapones: Ear,
  chaleco: Shirt,
  guantes: Hand,
};

function colorZonaSvg(estado: EstadoPrenda, requerida = true): { fill: string; stroke: string } {
  if (!requerida && estado !== 'ok') {
    return { fill: '#0891b2', stroke: '#22d3ee' }; // Cian técnico para prenda opcional
  }
  if (estado === 'ok') return { fill: '#10b981', stroke: '#34d399' };
  if (estado === 'falta') return { fill: '#f43f5e', stroke: '#fb7185' };
  return { fill: '#f59e0b', stroke: '#fbbf24' };
}

/**
 * Silueta SVG del Gemelo Anatómico de 4 Zonas:
 * - Zona 1 (Ojos): Lentes de seguridad (obligatorio)
 * - Zona 2 (Oídos): Tapones auditivos de inserción NOM-011 (obligatorio >85 dB)
 * - Zona 3 (Torso): Chaleco reflejante (obligatorio)
 * - Zona 4 (Manos): Guantes anticorte (condicional / opcional según puesto)
 */
function SiluetaAnatomica4Zonas({ posicion }: { posicion: PosicionTurno }) {
  const cLentes = colorZonaSvg(posicion.prendas.lentes?.estado ?? 'dudoso', true);
  const cTapones = colorZonaSvg(posicion.prendas.tapones?.estado ?? 'ok', true);
  const cChaleco = colorZonaSvg(posicion.prendas.chaleco?.estado ?? 'dudoso', true);
  const reqGuantes =
    posicion.prendas.guantes?.requerida ?? posicion.requiere_guantes ?? true;
  const cGuantes = colorZonaSvg(posicion.prendas.guantes?.estado ?? 'dudoso', reqGuantes);

  return (
    <svg
      viewBox="0 0 200 265"
      className="w-40 h-56 mx-auto select-none"
      role="img"
      aria-label={`Escáner anatómico de 4 zonas de ${posicion.trabajador}`}
    >
      {/* Retícula técnica de escáner */}
      <line x1="15" y1="40" x2="185" y2="40" stroke="#1e293b" strokeDasharray="3 3" />
      <line x1="15" y1="115" x2="185" y2="115" stroke="#1e293b" strokeDasharray="3 3" />
      <line x1="15" y1="155" x2="185" y2="155" stroke="#1e293b" strokeDasharray="3 3" />

      {/* Cabeza base */}
      <circle cx="100" cy="42" r="24" fill="#1e293b" stroke="#64748b" strokeWidth="2" />

      {/* ZONA 2: TAPONES AUDITIVOS DE INSERCIÓN EN OÍDOS (y: 0.04 - 0.28) */}
      <g>
        <circle
          cx="73"
          cy="43"
          r="7"
          fill={cTapones.fill}
          stroke={cTapones.stroke}
          strokeWidth="2"
        />
        <circle
          cx="127"
          cy="43"
          r="7"
          fill={cTapones.fill}
          stroke={cTapones.stroke}
          strokeWidth="2"
        />
        {/* Ondas acústicas atenuadas */}
        <path
          d="M 61 36 Q 56 43 61 50"
          fill="none"
          stroke={cTapones.stroke}
          strokeWidth="1.8"
        />
        <path
          d="M 139 36 Q 144 43 139 50"
          fill="none"
          stroke={cTapones.stroke}
          strokeWidth="1.8"
        />
      </g>

      {/* ZONA 1: LENTES DE SEGURIDAD EN OJOS (y: 0.00 - 0.32) */}
      <g>
        <rect
          x="78"
          y="31"
          width="44"
          height="14"
          rx="3"
          fill={cLentes.fill}
          stroke={cLentes.stroke}
          strokeWidth="2"
        />
        <line x1="98" y1="38" x2="102" y2="38" stroke="#0f172a" strokeWidth="2" />
      </g>

      {/* Cuello y piernas */}
      <rect x="92" y="66" width="16" height="10" fill="#334155" />
      <rect x="76" y="164" width="20" height="75" rx="6" fill="#1e293b" stroke="#475569" />
      <rect x="104" y="164" width="20" height="75" rx="6" fill="#1e293b" stroke="#475569" />

      {/* Brazos */}
      <rect x="48" y="78" width="18" height="62" rx="6" fill="#334155" />
      <rect x="134" y="78" width="18" height="62" rx="6" fill="#334155" />

      {/* ZONA 3: CHALECO REFLEJANTE EN TORSO (y: 0.16 - 0.72) */}
      <g>
        <rect
          x="68"
          y="76"
          width="64"
          height="88"
          rx="8"
          fill={cChaleco.fill}
          stroke={cChaleco.stroke}
          strokeWidth="2.5"
        />
        <rect x="70" y="106" width="60" height="7" fill="#fde047" opacity="0.9" />
        <rect x="70" y="133" width="60" height="7" fill="#fde047" opacity="0.9" />
      </g>

      {/* ZONA 4: GUANTES ANTICORTE EN MANOS (y: 0.28 - 0.96, condicional por puesto) */}
      <g>
        <circle
          cx="57"
          cy="154"
          r="13"
          fill={cGuantes.fill}
          stroke={cGuantes.stroke}
          strokeWidth="2.5"
          strokeDasharray={reqGuantes ? undefined : '3 2'}
        />
        <circle
          cx="143"
          cy="154"
          r="13"
          fill={cGuantes.fill}
          stroke={cGuantes.stroke}
          strokeWidth="2.5"
          strokeDasharray={reqGuantes ? undefined : '3 2'}
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
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <TituloPagina
          icono={ICONO_PANTALLA.cuadrilla}
          titulo="Gemelo Anatómico de 4 Zonas y Matriz de Puestos"
        >
          Inspección estación por estación de las 3 líneas del turno. Audita Ojos (Lentes), Oídos
          (Tapones Auditivos), Torso (Chaleco) y Manos (Guantes obligatorios u opcionales según el
          puesto).
        </TituloPagina>

        <div className="flex flex-wrap items-center gap-1.5 bg-slate-950 p-1.5 rounded border border-slate-800 text-xs font-mono">
          {[
            { id: 'todos', label: `TODOS (${posiciones.length})` },
            {
              id: 'error',
              label: `BLOQUEADOS (${posiciones.filter((p) => p.estado === 'error').length})`,
            },
            {
              id: 'revisar',
              label: `DUDOSOS (${posiciones.filter((p) => p.estado === 'revisar').length})`,
            },
            {
              id: 'ok',
              label: `AUTORIZADOS (${posiciones.filter((p) => p.estado === 'ok').length})`,
            },
          ].map((f) => (
            <button
              key={f.id}
              type="button"
              onClick={() => setFiltroEstado(f.id as typeof filtroEstado)}
              className={`px-2.5 py-1.5 rounded font-bold transition-colors ${
                filtroEstado === f.id
                  ? 'bg-amber-500 text-slate-950'
                  : 'text-slate-400 hover:bg-slate-900 hover:text-white'
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
            <div key={linea} className="panel-caseta rounded-lg p-5 space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2.5 font-mono">
                <span className="text-xs font-bold uppercase tracking-wider text-amber-400">
                  LÍNEA DE ACCESO {linea} // TORNIQUETE L{linea}
                </span>
                <span className="text-xs text-slate-400 font-tabular">
                  {estaciones.filter((e) => e.estado === 'ok').length}/{estaciones.length} PASE
                  AUTORIZADO
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {estaciones.map((pos) => {
                  const activa = seleccionada?.id === pos.id;
                  const atenuada = filtroEstado !== 'todos' && pos.estado !== filtroEstado;

                  const borderColor =
                    pos.estado === 'ok'
                      ? 'border-emerald-500/40 bg-emerald-950/20'
                      : pos.estado === 'error'
                      ? 'border-rose-500/50 bg-rose-950/25'
                      : 'border-amber-500/50 bg-amber-950/25';

                  return (
                    <button
                      key={pos.id}
                      type="button"
                      data-testid={`estacion-card-${pos.codigo}`}
                      onClick={() => setSeleccionada(pos)}
                      className={`text-left p-3.5 rounded border transition-all flex items-start gap-3 ${borderColor} ${
                        activa ? 'ring-2 ring-amber-400 border-amber-400 shadow-lg' : ''
                      } ${atenuada ? 'opacity-35' : 'opacity-100'}`}
                    >
                      <img
                        src={pos.evidencia}
                        alt={pos.trabajador}
                        className="w-14 h-14 rounded object-cover border border-slate-700 bg-slate-900 shrink-0"
                      />
                      <div className="min-w-0 flex-1 space-y-1">
                        <div className="flex items-center justify-between gap-1">
                          <span className="font-mono text-xs font-black text-amber-300">
                            {ubicacionCorta(pos)}
                          </span>
                          <PuntosPrendas
                            hay={pos.prendas_completas}
                            esperados={pos.prendas_requeridas}
                          />
                        </div>
                        <div className="font-bold text-sm text-white truncate">{pos.trabajador}</div>
                        <div className="flex items-center justify-between gap-1">
                          <span className="text-xs text-slate-400 truncate">{pos.puesto}</span>
                          {pos.requiere_guantes === false && (
                            <span className="text-[9px] font-mono font-bold px-1.5 py-0.2 rounded bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 shrink-0">
                              GUANTE OPC
                            </span>
                          )}
                        </div>
                        <div className="pt-1 flex items-center justify-between text-[11px] font-mono">
                          <span
                            className={`font-bold ${
                              pos.estado === 'ok'
                                ? 'text-emerald-400'
                                : pos.estado === 'error'
                                ? 'text-rose-400'
                                : 'text-amber-400'
                            }`}
                          >
                            {pos.estado === 'ok'
                              ? `${pos.prendas_completas}/${pos.prendas_requeridas} REQUERIDOS OK`
                              : pos.tipo
                              ? traducirTipoHallazgo(pos.tipo)
                              : 'REVISAR'}
                          </span>
                          {pos.impacto_diario ? (
                            <span className="font-bold text-rose-400 font-tabular">
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

        {/* Derecha: Gemelo Anatómico de 4 Zonas del trabajador seleccionado */}
        {seleccionada && (
          <section
            data-testid="gemelo-anatomico-panel"
            className="lg:col-span-5 panel-caseta rounded-lg p-6 space-y-5 sticky top-36"
          >
            <div className="flex items-start justify-between gap-3 border-b border-slate-800 pb-4">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-black px-2 py-0.5 rounded bg-amber-500 text-slate-950">
                    {seleccionada.codigo}
                  </span>
                  <span className="font-mono text-xs text-slate-400">
                    {seleccionada.id_empleado}
                  </span>
                </div>
                <h3 className="text-lg font-extrabold text-white mt-1">
                  {seleccionada.trabajador}
                </h3>
                <p className="text-xs text-slate-400">{ubicacionLarga(seleccionada)}</p>
              </div>

              <span
                className={`px-2.5 py-1 rounded text-xs font-mono font-bold border ${
                  seleccionada.estado === 'ok'
                    ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                    : seleccionada.estado === 'error'
                    ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                    : 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                }`}
              >
                {traducirEstadoPosicion(seleccionada.estado)}
              </span>
            </div>

            {/* Silueta SVG 4 Zonas + Evidencia fotográfica real lado a lado */}
            <div className="grid grid-cols-2 gap-4 items-center bg-slate-950/90 rounded p-4 border border-slate-800">
              <div className="text-center space-y-1">
                <div className="text-[10px] font-mono font-bold uppercase tracking-wider text-amber-400">
                  ESCÁNER BIOMÉTRICO (4 ZONAS)
                </div>
                <SiluetaAnatomica4Zonas posicion={seleccionada} />
              </div>

              <div className="space-y-2">
                <div className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">
                  EVIDENCIA ÓPTICA DE FILTRO
                </div>
                <img
                  src={seleccionada.evidencia_zona || seleccionada.evidencia}
                  alt={seleccionada.trabajador}
                  className="w-full h-44 object-cover rounded border border-slate-700 bg-slate-900"
                />
                {seleccionada.impacto_diario ? (
                  <div className="p-2 rounded bg-rose-500/20 border border-rose-500/40 text-rose-300 text-xs font-mono font-bold text-center font-tabular">
                    RIESGO: {formatearMoneda(seleccionada.impacto_diario, moneda)}/día
                  </div>
                ) : (
                  <div className="p-2 rounded bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs font-mono font-bold text-center">
                    SIN RIESGO MONETARIO (US$0.00)
                  </div>
                )}
              </div>
            </div>

            {/* Desglose de los 4 componentes de EPP */}
            <div className="space-y-2.5">
              <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-amber-400">
                TELEMETRÍA POR COMPONENTE DE EPP Y STOCK EN CASETA
              </h4>
              {ORDEN_PRENDAS.map((pr) => {
                const detalle = seleccionada.prendas[pr];
                const info = DICCIONARIO_PRENDAS[pr];
                const Icon = ICONO_PRENDA[pr];
                const est = detalle?.estado ?? 'ok';
                const requerida =
                  detalle?.requerida ?? (pr !== 'guantes' || (seleccionada.requiere_guantes ?? true));
                const esOpcionalNoPortado = !requerida && est !== 'ok';

                return (
                  <div
                    key={pr}
                    className="p-3 rounded border border-slate-800 bg-slate-950/70 flex items-center justify-between gap-3"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <span
                        className={`w-8 h-8 rounded flex items-center justify-center shrink-0 border ${
                          esOpcionalNoPortado
                            ? 'bg-cyan-950/60 text-cyan-300 border-cyan-500/40'
                            : est === 'ok'
                            ? 'bg-emerald-950/60 text-emerald-400 border-emerald-500/40'
                            : est === 'falta'
                            ? 'bg-rose-950/60 text-rose-400 border-rose-500/40'
                            : 'bg-amber-950/60 text-amber-400 border-amber-500/40'
                        }`}
                      >
                        <Icon className="w-4 h-4" />
                      </span>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-white">{info.nombre}</span>
                          {!requerida && (
                            <span className="text-[9px] font-mono font-bold px-1.5 py-0.2 rounded bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">
                              OPCIONAL EN SU PUESTO
                            </span>
                          )}
                        </div>
                        <div className="text-[11px] font-mono text-slate-400 truncate">
                          Confianza {Math.round((detalle?.confianza ?? 0.9) * 100)}% ·{' '}
                          {detalle?.lecturas ?? 5} cuadros votados
                        </div>
                      </div>
                    </div>

                    <div className="text-right shrink-0">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-mono font-bold border ${
                          esOpcionalNoPortado
                            ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
                            : est === 'ok'
                            ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                            : est === 'falta'
                            ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                            : 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                        }`}
                      >
                        {traducirEstadoPrenda(est, requerida)}
                      </span>
                      <div className="text-[11px] font-mono text-slate-400 mt-0.5 font-tabular inline-flex items-center gap-1">
                        <PackageCheck className="w-3 h-3 text-amber-400" />
                        {detalle?.stock_caseta ?? 12} en caseta
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {seleccionada.accion && (
              <div className="p-3.5 rounded bg-slate-950 border border-amber-500/40 text-white text-xs space-y-1.5">
                <div className="font-mono font-bold text-amber-400 uppercase tracking-wider text-[11px]">
                  ORDEN OPERATIVA PARA CASETA DE TORNIQUETE
                </div>
                <p className="text-slate-200 leading-relaxed">{seleccionada.accion}</p>
                {seleccionada.hallazgo_id && (
                  <div className="pt-1">
                    <Link
                      href="/hallazgos"
                      className="inline-flex items-center gap-1 font-mono text-amber-400 font-bold hover:underline"
                    >
                      IR A BITÁCORA PARA LIBERAR TORNIQUETE →
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
