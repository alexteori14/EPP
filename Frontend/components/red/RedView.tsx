'use client';

import React, { useState } from 'react';
import { Building2, ShieldAlert } from 'lucide-react';
import { SalidaRed } from '@/types/red';
import {
  formatearMoneda,
  traducirPrenda,
  traducirTipoHallazgo,
} from '@/lib/formatters/contract';
import { ICONO_PANTALLA } from '@/components/iconos';
import { TituloPagina } from '@/components/layout/TituloPagina';
import { Barra } from '@/components/graficas/Barras';

export function RedView({ data }: { data: SalidaRed }) {
  const { red, escenarios, sistemicos, locales } = data;
  const moneda = red.moneda ?? 'US$';
  const [escenarioId, setEscenarioId] = useState<'bajo' | 'central' | 'alto' | 'peor_caso'>(
    'central'
  );

  const escenarioActivo =
    escenarios.find((e) => e.id === escenarioId) ?? escenarios[1] ?? escenarios[0];
  const maxMensual = Math.max(...escenarios.map((e) => e.mensual), 1);

  return (
    <div className="space-y-6">
      <TituloPagina
        icono={ICONO_PANTALLA.red}
        titulo={`Proyección de Riesgo en Red (${red.plantas_total} Plantas Industriales)`}
      >
        Separa las omisiones individuales de una sola fila frente a las fallas sistémicas de
        control pre-turno que pueden replicarse en las otras {red.otras_plantas} plantas del grupo.
      </TituloPagina>

      {/* Tarjetas de separación: Medido Hoy vs Sistémico vs Local */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="panel-caseta rounded-lg p-5">
          <div className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wider">
            MEDIDO HOY EN PLANTA MTY-N01
          </div>
          <div className="text-2xl font-black text-white mt-1 font-tabular">
            {formatearMoneda(red.medido_diario, moneda)}/día
          </div>
          <p className="text-xs text-slate-400 mt-2">
            Total de exposición en este turno ({red.problemas_sistemicos + red.problemas_locales}{' '}
            trabajadores con omisión).
          </p>
        </div>

        <div className="rounded-lg border border-rose-500/40 bg-rose-950/25 p-5">
          <div className="text-xs font-mono font-bold text-rose-300 uppercase tracking-wider">
            RIESGO SISTÉMICO ESCALABLE ({red.problemas_sistemicos} CASOS)
          </div>
          <div className="text-2xl font-black text-rose-400 mt-1 font-tabular">
            {formatearMoneda(red.sistemico_diario, moneda)}/día
          </div>
          <p className="text-xs text-rose-200/80 mt-2">
            Trabajadores con múltiples prendas obligatorias omitidas o desabasto en caseta que
            reflejan falla de protocolo.
          </p>
        </div>

        <div className="panel-caseta rounded-lg p-5">
          <div className="text-xs font-mono font-bold text-amber-400 uppercase tracking-wider">
            OMISIONES LOCALES DE FILA ({red.problemas_locales} CASOS)
          </div>
          <div className="text-2xl font-black text-amber-300 mt-1 font-tabular">
            {formatearMoneda(red.local_diario, moneda)}/día
          </div>
          <p className="text-xs text-slate-400 mt-2">
            Olvidos individuales de una sola prenda (Lentes, Tapones, Chaleco o Guantes) que no se
            extrapolan a otras plantas.
          </p>
        </div>
      </div>

      {/* Simulador de escenarios en las 17 plantas restantes */}
      <section className="panel-caseta rounded-lg p-6 space-y-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h3 className="text-base font-bold text-white">
              Escenarios de contagio operativo en la red ({red.otras_plantas} plantas adicionales)
            </h3>
            <p className="text-xs text-slate-400">
              Selecciona qué porcentaje de plantas padece la misma relajación de filtro pre-turno.
            </p>
          </div>

          <div className="flex flex-wrap gap-1.5 bg-slate-950 p-1.5 rounded border border-slate-800 text-xs font-mono">
            {escenarios.map((esc) => (
              <button
                key={esc.id}
                type="button"
                onClick={() => setEscenarioId(esc.id)}
                className={`px-3 py-1.5 rounded font-bold transition-colors ${
                  escenarioId === esc.id
                    ? 'bg-amber-500 text-slate-950'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {esc.etiqueta}
              </button>
            ))}
          </div>
        </div>

        {escenarioActivo && (
          <div className="p-5 rounded bg-slate-950 border border-amber-500/40 text-white flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="text-xs font-mono text-amber-400 font-bold uppercase tracking-wider">
                ESCENARIO SELECCIONADO · {escenarioActivo.etiqueta}
              </div>
              <div className="text-lg font-extrabold">
                Si ocurre en {escenarioActivo.plantas} de las {red.otras_plantas} plantas
                adicionales:
              </div>
            </div>
            <div className="flex items-center gap-6 shrink-0 font-mono">
              <div>
                <div className="text-xs text-slate-400">IMPACTO DIARIO EN RED</div>
                <div className="text-xl font-black text-rose-400 font-tabular">
                  {formatearMoneda(escenarioActivo.diario, moneda)}/día
                </div>
              </div>
              <div className="border-l border-slate-800 pl-6">
                <div className="text-xs text-slate-400">PROYECCIÓN MENSUAL ({red.dias_mes}D)</div>
                <div className="text-2xl font-black text-amber-400 font-tabular">
                  {formatearMoneda(escenarioActivo.mensual, moneda)}/mes
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="space-y-3 pt-2">
          {escenarios.map((esc) => (
            <div key={esc.id} className="space-y-1">
              <div className="flex items-baseline justify-between text-xs font-mono">
                <span className="font-bold text-slate-300">
                  {esc.etiqueta} ({esc.plantas} plantas)
                </span>
                <span className="font-bold text-white font-tabular">
                  {formatearMoneda(esc.diario, moneda)}/día ·{' '}
                  <span className="text-rose-400">{formatearMoneda(esc.mensual, moneda)}/mes</span>
                </span>
              </div>
              <Barra
                pct={(esc.mensual / maxMensual) * 100}
                tono={esc.id === escenarioId ? 'bg-amber-500' : 'bg-slate-600'}
              />
            </div>
          ))}
        </div>
      </section>

      {/* Detalle de hallazgos sistémicos vs locales */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <section className="panel-caseta rounded-lg p-6 space-y-4">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-rose-400" />
            <h3 className="text-base font-bold text-white">
              Incumplimientos Sistémicos (Escalan a la Red)
            </h3>
          </div>
          <div className="space-y-3">
            {sistemicos.map((s) => (
              <div
                key={s.codigo}
                className="p-3.5 rounded border border-rose-500/40 bg-rose-950/25 flex items-center justify-between gap-3"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-black px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/40">
                      {s.codigo}
                    </span>
                    <span className="font-bold text-sm text-white">{s.trabajador}</span>
                  </div>
                  <div className="text-xs text-slate-300 mt-0.5">
                    {s.puesto} · Sin {s.prendas_faltantes.map(traducirPrenda).join(' + ')}
                  </div>
                </div>
                <div className="text-right shrink-0 font-mono font-tabular">
                  <div className="text-sm font-bold text-rose-400">
                    {formatearMoneda(s.impacto_diario, moneda)}/día
                  </div>
                  <div className="text-[11px] text-slate-400">
                    Red 100%: {formatearMoneda(s.peor_caso_diario, moneda)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="panel-caseta rounded-lg p-6 space-y-4">
          <div className="flex items-center gap-2">
            <Building2 className="w-5 h-5 text-amber-400" />
            <h3 className="text-base font-bold text-white">
              Omisiones Locales de Planta (No se extrapolan)
            </h3>
          </div>
          <div className="space-y-3">
            {locales.map((l) => (
              <div
                key={l.tipo}
                className="p-3.5 rounded border border-slate-800 bg-slate-950/80 flex items-center justify-between gap-3"
              >
                <div>
                  <div className="font-bold text-sm text-white">
                    {traducirTipoHallazgo(l.tipo)}
                  </div>
                  <div className="text-xs text-slate-400">
                    {l.cantidad} {l.cantidad === 1 ? 'trabajador' : 'trabajadores'} en esta planta
                  </div>
                </div>
                <div className="text-sm font-mono font-bold text-amber-400 font-tabular">
                  {formatearMoneda(l.impacto_diario, moneda)}/día
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
