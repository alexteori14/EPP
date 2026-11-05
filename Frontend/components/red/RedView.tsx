'use client';

import React, { useState } from 'react';
import { Building2, ShieldAlert, TrendingUp } from 'lucide-react';
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
    <div className="max-w-6xl mx-auto space-y-6">
      <TituloPagina
        icono={ICONO_PANTALLA.red}
        titulo={`Proyección de Riesgo en Red (${red.plantas_total} Plantas Industriales)`}
      >
        Separa las omisiones individuales de una sola fila frente a las fallas sistémicas de
        control pre-turno que pueden replicarse en las otras {red.otras_plantas} plantas del grupo.
      </TituloPagina>

      {/* Tarjetas de separación: Medido Hoy vs Sistémico vs Local */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Medido Hoy en Planta MTY-N01
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-1 font-tabular">
            {formatearMoneda(red.medido_diario, moneda)}/día
          </div>
          <p className="text-xs text-slate-500 mt-2">
            Total de exposición en este turno ({red.problemas_sistemicos + red.problemas_locales}{' '}
            trabajadores con omisión).
          </p>
        </div>

        <div className="bg-rose-50/60 rounded-xl border border-rose-200 p-5 shadow-sm">
          <div className="text-xs font-semibold text-rose-800 uppercase tracking-wider">
            Riesgo Sistémico Escalable ({red.problemas_sistemicos} casos)
          </div>
          <div className="text-2xl font-bold text-rose-700 mt-1 font-tabular">
            {formatearMoneda(red.sistemico_diario, moneda)}/día
          </div>
          <p className="text-xs text-rose-700/90 mt-2">
            Trabajadores con múltiples prendas omitidas o desabasto en caseta que reflejan falla de
            protocolo.
          </p>
        </div>

        <div className="bg-slate-50 rounded-xl border border-slate-200 p-5 shadow-sm">
          <div className="text-xs font-semibold text-slate-600 uppercase tracking-wider">
            Omisiones Locales de Fila ({red.problemas_locales} casos)
          </div>
          <div className="text-2xl font-bold text-slate-800 mt-1 font-tabular">
            {formatearMoneda(red.local_diario, moneda)}/día
          </div>
          <p className="text-xs text-slate-500 mt-2">
            Olvidos individuales de una sola prenda (Lentes, Chaleco o Guantes) que no se
            extrapolan a otras plantas.
          </p>
        </div>
      </div>

      {/* Simulador de escenarios en las 17 plantas restantes */}
      <section className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h3 className="text-base font-bold text-slate-900">
              Escenarios de contagio operativo en la red ({red.otras_plantas} plantas adicionales)
            </h3>
            <p className="text-xs text-slate-500">
              Selecciona qué porcentaje de plantas padece la misma relajación de filtro pre-turno.
            </p>
          </div>

          <div className="flex flex-wrap gap-1.5 bg-slate-100 p-1 rounded-lg text-xs">
            {escenarios.map((esc) => (
              <button
                key={esc.id}
                type="button"
                onClick={() => setEscenarioId(esc.id)}
                className={`px-3 py-1.5 rounded-md font-semibold transition-colors ${
                  escenarioId === esc.id
                    ? 'bg-slate-900 text-white shadow-sm'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {esc.etiqueta}
              </button>
            ))}
          </div>
        </div>

        {escenarioActivo && (
          <div className="p-5 rounded-xl bg-slate-900 text-white flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="text-xs text-teal-400 font-semibold uppercase tracking-wider">
                Escenario Seleccionado · {escenarioActivo.etiqueta}
              </div>
              <div className="text-lg font-bold">
                Si ocurre en {escenarioActivo.plantas} de las {red.otras_plantas} plantas
                adicionales:
              </div>
            </div>
            <div className="flex items-center gap-6 shrink-0">
              <div>
                <div className="text-xs text-slate-400">Impacto Diario en Red</div>
                <div className="text-xl font-bold text-rose-400 font-tabular">
                  {formatearMoneda(escenarioActivo.diario, moneda)}/día
                </div>
              </div>
              <div className="border-l border-slate-700 pl-6">
                <div className="text-xs text-slate-400">Proyección Mensual ({red.dias_mes}d)</div>
                <div className="text-2xl font-extrabold text-white font-tabular">
                  {formatearMoneda(escenarioActivo.mensual, moneda)}/mes
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="space-y-3 pt-2">
          {escenarios.map((esc) => (
            <div key={esc.id} className="space-y-1">
              <div className="flex items-baseline justify-between text-xs">
                <span className="font-semibold text-slate-700">
                  {esc.etiqueta} ({esc.plantas} plantas)
                </span>
                <span className="font-mono font-bold text-slate-900 font-tabular">
                  {formatearMoneda(esc.diario, moneda)}/día ·{' '}
                  <span className="text-rose-600">{formatearMoneda(esc.mensual, moneda)}/mes</span>
                </span>
              </div>
              <Barra
                pct={(esc.mensual / maxMensual) * 100}
                tono={esc.id === escenarioId ? 'bg-teal-600' : 'bg-slate-400'}
              />
            </div>
          ))}
        </div>
      </section>

      {/* Detalle de hallazgos sistémicos vs locales */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <section className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-rose-600" />
            <h3 className="text-base font-bold text-slate-900">
              Incumplimientos Sistémicos (Escalan a la Red)
            </h3>
          </div>
          <div className="space-y-3">
            {sistemicos.map((s) => (
              <div
                key={s.codigo}
                className="p-3.5 rounded-lg border border-rose-200 bg-rose-50/40 flex items-center justify-between gap-3"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold px-1.5 py-0.5 rounded bg-rose-200 text-rose-900">
                      {s.codigo}
                    </span>
                    <span className="font-bold text-sm text-slate-900">{s.trabajador}</span>
                  </div>
                  <div className="text-xs text-slate-600 mt-0.5">
                    {s.puesto} · Sin {s.prendas_faltantes.map(traducirPrenda).join(' + ')}
                  </div>
                </div>
                <div className="text-right shrink-0 font-tabular">
                  <div className="text-sm font-bold text-rose-700">
                    {formatearMoneda(s.impacto_diario, moneda)}/día
                  </div>
                  <div className="text-[11px] text-slate-500">
                    Red 100%: {formatearMoneda(s.peor_caso_diario, moneda)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-2">
            <Building2 className="w-5 h-5 text-slate-600" />
            <h3 className="text-base font-bold text-slate-900">
              Omisiones Locales de Planta (No se extrapolan)
            </h3>
          </div>
          <div className="space-y-3">
            {locales.map((l) => (
              <div
                key={l.tipo}
                className="p-3.5 rounded-lg border border-slate-200 bg-slate-50 flex items-center justify-between gap-3"
              >
                <div>
                  <div className="font-bold text-sm text-slate-900">
                    {traducirTipoHallazgo(l.tipo)}
                  </div>
                  <div className="text-xs text-slate-500">
                    {l.cantidad} {l.cantidad === 1 ? 'trabajador' : 'trabajadores'} en esta planta
                  </div>
                </div>
                <div className="text-sm font-bold text-slate-800 font-tabular">
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
