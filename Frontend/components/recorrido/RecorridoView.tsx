'use client';

import React, { useRef, useState } from 'react';
import Link from 'next/link';
import { Clock, ExternalLink, Play, ShieldAlert } from 'lucide-react';
import { Hallazgo, SalidaHallazgos } from '@/types/hallazgos';
import {
  formatearMoneda,
  formatearTiempoVideo,
  traducirPrenda,
  traducirTipoHallazgo,
} from '@/lib/formatters/contract';
import { ICONO_PANTALLA } from '@/components/iconos';
import { TituloPagina } from '@/components/layout/TituloPagina';

export function RecorridoView({ data }: { data: SalidaHallazgos }) {
  const { resumen, hallazgos } = data;
  const moneda = resumen.moneda ?? 'US$';
  const videoUrl = resumen.video_url || '/salida/recorrido_anotado.mp4';

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [seleccionado, setSeleccionado] = useState<Hallazgo | null>(hallazgos[0] ?? null);

  const saltarASegundo = (h: Hallazgo) => {
    setSeleccionado(h);
    if (videoRef.current) {
      videoRef.current.currentTime = h.segundo;
      videoRef.current.play().catch(() => {
        // autoplay bloqueado
      });
    }
  };

  const ordenadosPorTiempo = [...hallazgos].sort((a, b) => a.segundo - b.segundo);

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <TituloPagina
        icono={ICONO_PANTALLA.recorrido}
        titulo="Recorrido de Fila con Cajas Anatómicas Anotadas"
      >
        Inspección cuadro a cuadro del video de ingreso al turno ({resumen.video ?? 'recorrido_turno.mp4'}
        ). Haz clic en cualquier marcador para saltar al segundo exacto.
      </TituloPagina>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Reproductor de video anotado */}
        <section className="lg:col-span-8 bg-slate-950 rounded-xl border border-slate-800 overflow-hidden shadow-sm flex flex-col justify-between">
          <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between text-xs text-slate-300">
            <span className="font-mono font-semibold text-white">
              {resumen.video ?? 'recorrido_turno.mp4'} · 24 FPS · Cajas de Lentes, Chaleco y Guantes
            </span>
            <span className="text-teal-400 font-mono">
              {ordenadosPorTiempo.length} incidencias marcadas
            </span>
          </div>

          <div className="relative aspect-video bg-black">
            <video
              ref={videoRef}
              src={videoUrl}
              controls
              playsInline
              preload="metadata"
              className="w-full h-full object-contain"
            />
          </div>

          {/* Barra de marcadores temporales */}
          <div className="p-4 bg-slate-900 border-t border-slate-800 space-y-2">
            <div className="text-xs text-slate-400 font-medium">
              Línea de tiempo de omisiones detectadas (clic para saltar al cuadro):
            </div>
            <div className="flex flex-wrap gap-2">
              {ordenadosPorTiempo.map((h) => {
                const activo = seleccionado?.id === h.id;
                return (
                  <button
                    key={h.id}
                    type="button"
                    onClick={() => saltarASegundo(h)}
                    className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-mono transition-colors ${
                      activo
                        ? 'bg-teal-600 text-white font-bold'
                        : h.tipo === 'revisar'
                        ? 'bg-amber-950/80 text-amber-300 border border-amber-700/60 hover:bg-amber-900/80'
                        : 'bg-rose-950/80 text-rose-300 border border-rose-700/60 hover:bg-rose-900/80'
                    }`}
                  >
                    <Play className="w-3 h-3" />
                    {formatearTiempoVideo(h.segundo)} · {h.codigo}
                  </button>
                );
              })}
            </div>
          </div>
        </section>

        {/* Lista lateral de eventos del recorrido */}
        <section className="lg:col-span-4 bg-white rounded-xl border border-slate-200 p-5 shadow-sm flex flex-col justify-between space-y-4 max-h-[640px] overflow-y-auto">
          <div className="space-y-1">
            <h3 className="text-base font-bold text-slate-900">Momentos clave en el video</h3>
            <p className="text-xs text-slate-500">
              Ordenados cronológicamente conforme la cámara recorre las 3 líneas del turno.
            </p>
          </div>

          <div className="space-y-2.5 flex-1 overflow-y-auto pr-1">
            {ordenadosPorTiempo.map((h) => {
              const activo = seleccionado?.id === h.id;
              return (
                <div
                  key={h.id}
                  onClick={() => saltarASegundo(h)}
                  className={`p-3 rounded-lg border cursor-pointer transition-all space-y-2 ${
                    activo
                      ? 'border-teal-600 bg-teal-50/40 ring-1 ring-teal-600'
                      : 'border-slate-200 hover:border-slate-300 bg-slate-50/60'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="inline-flex items-center gap-1.5 font-mono text-xs font-bold text-slate-800">
                      <Clock className="w-3.5 h-3.5 text-teal-600" />
                      {formatearTiempoVideo(h.segundo)} (cuadro #{h.cuadro})
                    </span>
                    <span className="font-mono text-xs px-1.5 py-0.5 rounded bg-slate-200 text-slate-800 font-semibold">
                      {h.codigo}
                    </span>
                  </div>

                  <div className="flex items-center gap-3">
                    <img
                      src={h.evidencia_crop}
                      alt={h.trabajador}
                      className="w-12 h-12 rounded-md object-cover border border-slate-200 bg-slate-900 shrink-0"
                    />
                    <div className="min-w-0 flex-1">
                      <div className="text-xs font-bold text-slate-900 truncate">
                        {h.trabajador}
                      </div>
                      <div className="text-[11px] text-slate-600 truncate">
                        {traducirTipoHallazgo(h.tipo)}
                      </div>
                      {h.prendas_faltantes.length > 0 && (
                        <div className="text-[11px] text-rose-700 font-medium truncate">
                          Sin: {h.prendas_faltantes.map(traducirPrenda).join(', ')}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-1 border-t border-slate-200/70 text-xs">
                    <span className="font-bold text-rose-600 font-tabular">
                      {h.impacto_diario > 0
                        ? `${formatearMoneda(h.impacto_diario, moneda)}/día`
                        : 'US$0.00 (Revisar)'}
                    </span>
                    <Link
                      href={`/cuadrilla?pos=${h.codigo}`}
                      onClick={(e) => e.stopPropagation()}
                      className="inline-flex items-center gap-1 text-[11px] font-semibold text-teal-700 hover:underline"
                    >
                      Abrir en Cuadrilla
                      <ExternalLink className="w-3 h-3" />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      </div>
    </div>
  );
}
