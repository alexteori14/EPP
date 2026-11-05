'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import {
  CheckCircle2,
  Clock,
  Filter,
  Loader2,
  RotateCcw,
  ShieldAlert,
  ShieldCheck,
} from 'lucide-react';
import { Hallazgo, PrendaEPP, SalidaHallazgos } from '@/types/hallazgos';
import {
  formatearMoneda,
  formatearTiempoVideo,
  traducirPrenda,
  traducirTipoHallazgo,
} from '@/lib/formatters/contract';
import { actualizarHallazgoCorregido } from '@/lib/api/analisis';
import { ICONO_PANTALLA } from '@/components/iconos';
import { TituloPagina } from '@/components/layout/TituloPagina';

export function HallazgosView({ initialData }: { initialData: SalidaHallazgos }) {
  const [datos, setDatos] = useState<SalidaHallazgos>(initialData);
  const [filtroEstado, setFiltroEstado] = useState<'pendientes' | 'corregidos' | 'todos'>('todos');
  const [filtroPrenda, setFiltroPrenda] = useState<'todas' | PrendaEPP>('todas');
  const [guardandoId, setGuardandoId] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const { resumen, hallazgos } = datos;
  const moneda = resumen.moneda ?? 'US$';
  const corridaId = resumen.analisis_id || 'demo';

  const alternarCorregido = async (h: Hallazgo) => {
    setGuardandoId(h.id);
    setErrorMsg(null);
    const nuevoValor = !h.corregido;
    try {
      const actualizado = await actualizarHallazgoCorregido(corridaId, h.id, nuevoValor);
      setDatos(actualizado);
    } catch (e: unknown) {
      setErrorMsg(
        e instanceof Error
          ? e.message
          : 'No se pudo persistir el cambio en el servidor (:8000).'
      );
    } finally {
      setGuardandoId(null);
    }
  };

  const filtrados = hallazgos.filter((h) => {
    if (filtroEstado === 'pendientes' && h.corregido) return false;
    if (filtroEstado === 'corregidos' && !h.corregido) return false;
    if (filtroPrenda !== 'todas' && !h.prendas_faltantes.includes(filtroPrenda)) return false;
    return true;
  });

  const pendientesCount = hallazgos.filter((h) => !h.corregido).length;
  const corregidosCount = hallazgos.filter((h) => h.corregido).length;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <TituloPagina
          icono={ICONO_PANTALLA.hallazgos}
          titulo="Hallazgos Accionables y Autorización en Caseta"
        >
          Ordenados por exposición diaria en dólares ({moneda}/día). Al entregar la prenda faltante
          y marcar como autorizado, el cambio se guarda en disco y recalcula el riesgo del turno.
        </TituloPagina>

        {/* Tarjeta compacta de riesgo vivo vs recuperado */}
        <div className="flex items-center gap-4 bg-white px-4 py-3 rounded-xl border border-slate-200 shadow-sm shrink-0">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
              Riesgo Activo
            </div>
            <div
              data-testid="hallazgos-riesgo-activo"
              className="text-lg font-bold text-rose-600 font-tabular"
            >
              {formatearMoneda(resumen.dinero_en_riesgo_diario, moneda)}/día
            </div>
          </div>
          <div className="border-l border-slate-200 pl-4">
            <div className="text-[11px] font-semibold uppercase tracking-wider text-emerald-700">
              Mitigado en Caseta
            </div>
            <div
              data-testid="hallazgos-riesgo-recuperado"
              className="text-lg font-bold text-emerald-600 font-tabular"
            >
              {formatearMoneda(resumen.dinero_recuperado_diario ?? 0, moneda)}/día
            </div>
          </div>
        </div>
      </div>

      {/* Controles de filtrado */}
      <section className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-1.5 text-xs">
          <Filter className="w-4 h-4 text-slate-400 mr-1" />
          {[
            { id: 'todos', label: `Todos (${hallazgos.length})` },
            { id: 'pendientes', label: `Pendientes (${pendientesCount})` },
            { id: 'corregidos', label: `Autorizados (${corregidosCount})` },
          ].map((f) => (
            <button
              key={f.id}
              type="button"
              onClick={() => setFiltroEstado(f.id as typeof filtroEstado)}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-colors ${
                filtroEstado === f.id
                  ? 'bg-slate-900 text-white'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-1.5 text-xs">
          <span className="text-slate-500 font-medium mr-1">Filtrar por prenda:</span>
          {[
            { id: 'todas', label: 'Todas (3 EPP)' },
            { id: 'lentes', label: 'Sin Lentes' },
            { id: 'chaleco', label: 'Sin Chaleco' },
            { id: 'guantes', label: 'Sin Guantes' },
          ].map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => setFiltroPrenda(p.id as typeof filtroPrenda)}
              className={`px-2.5 py-1.5 rounded-lg font-medium transition-colors ${
                filtroPrenda === p.id
                  ? 'bg-teal-600 text-white font-semibold'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </section>

      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-800">
          {errorMsg}
        </div>
      )}

      {/* Lista de tarjetas de hallazgos */}
      <div className="space-y-3">
        {filtrados.map((h) => {
          const procesando = guardandoId === h.id;
          return (
            <article
              key={h.id}
              data-testid={`hallazgo-card-${h.id}`}
              className={`rounded-xl border p-5 transition-all flex flex-col md:flex-row items-start md:items-center justify-between gap-5 shadow-sm ${
                h.corregido
                  ? 'bg-emerald-50/40 border-emerald-200'
                  : h.tipo === 'revisar'
                  ? 'bg-amber-50/30 border-amber-200'
                  : 'bg-white border-slate-200'
              }`}
            >
              <div className="flex items-start gap-4 min-w-0 flex-1">
                <img
                  src={h.evidencia_persona || h.evidencia_crop}
                  alt={h.trabajador}
                  className="w-20 h-20 rounded-xl object-cover border border-slate-200 bg-slate-900 shrink-0"
                />

                <div className="space-y-1.5 min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-slate-900 text-white">
                      {h.codigo}
                    </span>
                    <span className="font-mono text-xs text-slate-500">{h.id_empleado}</span>
                    <span
                      className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                        h.corregido
                          ? 'bg-emerald-100 text-emerald-800'
                          : h.tipo === 'revisar'
                          ? 'bg-amber-100 text-amber-800'
                          : 'bg-rose-100 text-rose-800'
                      }`}
                    >
                      {h.corregido ? 'Pase Autorizado tras Entrega' : traducirTipoHallazgo(h.tipo)}
                    </span>
                    <Link
                      href={`/recorrido`}
                      className="inline-flex items-center gap-1 text-xs text-slate-500 hover:text-teal-700 font-mono"
                    >
                      <Clock className="w-3 h-3" />
                      {formatearTiempoVideo(h.segundo)} (cuadro #{h.cuadro})
                    </Link>
                  </div>

                  <h3 className="text-base font-bold text-slate-900">
                    {h.trabajador}{' '}
                    <span className="text-xs font-normal text-slate-500">· {h.puesto}</span>
                  </h3>

                  <p className="text-xs text-slate-600">{h.descripcion}</p>

                  <div className="pt-1 flex flex-wrap items-center gap-2 text-xs">
                    <span className="font-semibold text-slate-800">Acción en caseta:</span>
                    <span className="text-slate-600">{h.accion_sugerida}</span>
                  </div>
                </div>
              </div>

              <div className="flex md:flex-col items-center md:items-end justify-between w-full md:w-auto gap-3 border-t md:border-t-0 border-slate-100 pt-3 md:pt-0 shrink-0">
                <div className="text-left md:text-right">
                  <div className="text-[11px] text-slate-500 uppercase tracking-wider">
                    {h.corregido ? 'Riesgo Mitigado' : 'Exposición Diaria'}
                  </div>
                  <div
                    className={`text-xl font-bold font-tabular ${
                      h.corregido
                        ? 'text-emerald-600 line-through'
                        : h.impacto_diario > 0
                        ? 'text-rose-600'
                        : 'text-amber-700'
                    }`}
                  >
                    {formatearMoneda(h.impacto_diario, moneda)}/día
                  </div>
                  {h.prendas_faltantes.length > 0 && (
                    <div className="text-[11px] text-slate-500">
                      Falta: {h.prendas_faltantes.map(traducirPrenda).join(' + ')}
                    </div>
                  )}
                </div>

                <button
                  type="button"
                  data-testid={`btn-corregir-${h.id}`}
                  disabled={procesando}
                  onClick={() => alternarCorregido(h)}
                  className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-colors shadow-sm ${
                    h.corregido
                      ? 'bg-white border border-slate-300 text-slate-700 hover:bg-slate-100'
                      : 'bg-emerald-600 hover:bg-emerald-700 text-white'
                  }`}
                >
                  {procesando ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : h.corregido ? (
                    <RotateCcw className="w-3.5 h-3.5" />
                  ) : (
                    <ShieldCheck className="w-3.5 h-3.5" />
                  )}
                  {h.corregido ? 'Revertir a pendiente' : 'Autorizar tras entrega'}
                </button>
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}
