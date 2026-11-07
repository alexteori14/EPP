'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Clock, Filter, Loader2, RotateCcw, ShieldCheck } from 'lucide-react';
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
    <div className="space-y-6">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <TituloPagina
          icono={ICONO_PANTALLA.hallazgos}
          titulo="Bitácora de Retenciones, Multas STPS y Liberación de Torniquete"
        >
          Ordenados por exposición diaria en dólares ({moneda}/día). Al entregar la prenda en
          ventanilla y autorizar el pase, el cambio se persiste en disco (`PATCH`) y recalcula el
          riesgo del turno.
        </TituloPagina>

        {/* Tarjeta compacta de riesgo vivo vs recuperado */}
        <div className="flex items-center gap-4 bg-slate-950 px-4 py-3 rounded border border-slate-800 shrink-0 font-mono">
          <div>
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              RIESGO ACTIVO EN FILA
            </div>
            <div
              data-testid="hallazgos-riesgo-activo"
              className="text-lg font-black text-rose-400 font-tabular"
            >
              {formatearMoneda(resumen.dinero_en_riesgo_diario, moneda)}/día
            </div>
          </div>
          <div className="border-l border-slate-800 pl-4">
            <div className="text-[10px] font-bold uppercase tracking-wider text-emerald-400">
              MITIGADO EN CASETA
            </div>
            <div
              data-testid="hallazgos-riesgo-recuperado"
              className="text-lg font-black text-emerald-400 font-tabular"
            >
              {formatearMoneda(resumen.dinero_recuperado_diario ?? 0, moneda)}/día
            </div>
          </div>
        </div>
      </div>

      {/* Controles de filtrado */}
      <section className="panel-caseta rounded-lg p-4 flex flex-wrap items-center justify-between gap-3 font-mono text-xs">
        <div className="flex items-center gap-1.5">
          <Filter className="w-4 h-4 text-amber-400 mr-1" />
          {[
            { id: 'todos', label: `TODOS (${hallazgos.length})` },
            { id: 'pendientes', label: `RETENIDOS (${pendientesCount})` },
            { id: 'corregidos', label: `LIBERADOS (${corregidosCount})` },
          ].map((f) => (
            <button
              key={f.id}
              type="button"
              onClick={() => setFiltroEstado(f.id as typeof filtroEstado)}
              className={`px-3 py-1.5 rounded font-bold transition-colors ${
                filtroEstado === f.id
                  ? 'bg-amber-500 text-slate-950'
                  : 'bg-slate-900 text-slate-400 hover:bg-slate-800 hover:text-white'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-slate-400 font-bold mr-1">FILTRAR POR EPP:</span>
          {[
            { id: 'todas', label: 'TODOS (4 EPP)' },
            { id: 'lentes', label: 'SIN LENTES' },
            { id: 'tapones', label: 'SIN TAPONES AUDITIVOS' },
            { id: 'chaleco', label: 'SIN CHALECO' },
            { id: 'guantes', label: 'SIN GUANTES (PUESTO OP)' },
          ].map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => setFiltroPrenda(p.id as typeof filtroPrenda)}
              className={`px-2.5 py-1.5 rounded font-bold transition-colors ${
                filtroPrenda === p.id
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/60'
                  : 'bg-slate-900 text-slate-400 border border-slate-800 hover:text-white'
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </section>

      {errorMsg && (
        <div className="p-4 rounded bg-rose-950/60 border border-rose-700 text-xs text-rose-200 font-mono">
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
              className={`rounded-lg border p-5 transition-all flex flex-col md:flex-row items-start md:items-center justify-between gap-5 ${
                h.corregido
                  ? 'bg-emerald-950/20 border-emerald-500/40'
                  : h.tipo === 'revisar'
                  ? 'bg-amber-950/20 border-amber-500/40'
                  : 'panel-caseta border-rose-500/40'
              }`}
            >
              <div className="flex items-start gap-4 min-w-0 flex-1">
                <img
                  src={h.evidencia_persona || h.evidencia_crop}
                  alt={h.trabajador}
                  className="w-20 h-20 rounded object-cover border border-slate-700 bg-slate-900 shrink-0"
                />

                <div className="space-y-1.5 min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2 font-mono">
                    <span className="text-xs font-black px-2 py-0.5 rounded bg-amber-500 text-slate-950">
                      {h.codigo}
                    </span>
                    <span className="text-xs text-slate-400">{h.id_empleado}</span>
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-bold border ${
                        h.corregido
                          ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                          : h.tipo === 'revisar'
                          ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                          : 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                      }`}
                    >
                      {h.corregido ? 'TORNIQUETE LIBERADO TRAS DOTACIÓN' : traducirTipoHallazgo(h.tipo)}
                    </span>
                    <Link
                      href={`/recorrido`}
                      className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-amber-300"
                    >
                      <Clock className="w-3 h-3" />
                      {formatearTiempoVideo(h.segundo)} (cuadro #{h.cuadro})
                    </Link>
                  </div>

                  <h3 className="text-base font-extrabold text-white">
                    {h.trabajador}{' '}
                    <span className="text-xs font-normal text-slate-400">· {h.puesto}</span>
                  </h3>

                  <p className="text-xs text-slate-300">{h.descripcion}</p>

                  <div className="pt-1 flex flex-wrap items-center gap-2 text-xs font-mono">
                    <span className="font-bold text-amber-400">PROTOCOLO CASETA:</span>
                    <span className="text-slate-300">{h.accion_sugerida}</span>
                  </div>
                </div>
              </div>

              <div className="flex md:flex-col items-center md:items-end justify-between w-full md:w-auto gap-3 border-t md:border-t-0 border-slate-800 pt-3 md:pt-0 shrink-0 font-mono">
                <div className="text-left md:text-right">
                  <div className="text-[10px] text-slate-400 uppercase tracking-wider">
                    {h.corregido ? 'RIESGO MITIGADO' : 'EXPOSICIÓN DIARIA'}
                  </div>
                  <div
                    className={`text-xl font-black font-tabular ${
                      h.corregido
                        ? 'text-emerald-400 line-through'
                        : h.impacto_diario > 0
                        ? 'text-rose-400'
                        : 'text-amber-400'
                    }`}
                  >
                    {formatearMoneda(h.impacto_diario, moneda)}/día
                  </div>
                  {h.prendas_faltantes.length > 0 && (
                    <div className="text-[11px] text-slate-400">
                      Falta: {h.prendas_faltantes.map(traducirPrenda).join(' + ')}
                    </div>
                  )}
                </div>

                <button
                  type="button"
                  data-testid={`btn-corregir-${h.id}`}
                  disabled={procesando}
                  onClick={() => alternarCorregido(h)}
                  className={`inline-flex items-center gap-2 px-4 py-2 rounded text-xs font-bold uppercase transition-colors ${
                    h.corregido
                      ? 'bg-slate-900 border border-slate-700 text-slate-300 hover:bg-slate-800'
                      : 'bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-extrabold shadow-[0_0_14px_rgba(16,185,129,0.25)]'
                  }`}
                >
                  {procesando ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : h.corregido ? (
                    <RotateCcw className="w-3.5 h-3.5" />
                  ) : (
                    <ShieldCheck className="w-3.5 h-3.5" />
                  )}
                  {h.corregido ? 'Revertir a retenido' : 'Autorizar tras entrega'}
                </button>
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}
