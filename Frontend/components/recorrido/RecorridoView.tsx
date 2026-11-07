'use client';

import React, { useRef, useState } from 'react';
import Link from 'next/link';
import { Clock, ExternalLink, Play } from 'lucide-react';
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
    <div className="space-y-6">
      <TituloPagina
        icono={ICONO_PANTALLA.recorrido}
        titulo="Recorrido de Fila con Cajas Anatómicas Anotadas (4 Zonas)"
      >
        Inspección cuadro a cuadro del circuito cerrado de ingreso al turno (
        {resumen.video ?? 'recorrido_turno.mp4'}). Haz clic en cualquier marcador para saltar al
        segundo exacto de la retención.
      </TituloPagina>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Reproductor de video anotado */}
        <section className="lg:col-span-8 bg-slate-950 rounded-lg border border-slate-800 overflow-hidden shadow-xl flex flex-col justify-between">
          <div className="px-4 py-3 bg-[#060911] border-b border-slate-800 flex items-center justify-between text-xs font-mono text-slate-300">
            <span className="font-bold text-white">
              {resumen.video ?? 'recorrido_turno.mp4'} · 24 FPS · Lentes, Tapones, Chaleco y Guantes
            </span>
            <span className="text-amber-400 font-bold">
              {ordenadosPorTiempo.length} EVENTOS MARCADOS
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
          <div className="p-4 bg-[#070b12] border-t border-slate-800 space-y-2">
            <div className="text-xs font-mono text-slate-400 font-bold uppercase">
              LÍNEA DE TIEMPO DE RETENCIONES (CLIC PARA SALTAR AL CUADRO):
            </div>
            <div className="flex flex-wrap gap-2">
              {ordenadosPorTiempo.map((h) => {
                const activo = seleccionado?.id === h.id;
                return (
                  <button
                    key={h.id}
                    type="button"
                    onClick={() => saltarASegundo(h)}
                    className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono transition-colors ${
                      activo
                        ? 'bg-amber-500 text-slate-950 font-black'
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
        <section className="lg:col-span-4 panel-caseta rounded-lg p-5 flex flex-col justify-between space-y-4 max-h-[640px] overflow-y-auto">
          <div className="space-y-1">
            <div className="text-[10px] font-mono font-bold uppercase tracking-wider text-amber-400">
              BITÁCORA DE VIDEO // CCTV
            </div>
            <h3 className="text-base font-bold text-white">Momentos clave en el filtro</h3>
            <p className="text-xs text-slate-400">
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
                  className={`p-3 rounded border cursor-pointer transition-all space-y-2 ${
                    activo
                      ? 'border-amber-400 bg-amber-500/10 ring-1 ring-amber-400'
                      : 'border-slate-800 hover:border-slate-600 bg-slate-950/80'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2 font-mono">
                    <span className="inline-flex items-center gap-1.5 text-xs font-bold text-amber-300">
                      <Clock className="w-3.5 h-3.5 text-amber-400" />
                      {formatearTiempoVideo(h.segundo)} (cuadro #{h.cuadro})
                    </span>
                    <span className="text-xs px-1.5 py-0.5 rounded bg-slate-800 text-white font-bold">
                      {h.codigo}
                    </span>
                  </div>

                  <div className="flex items-center gap-3">
                    <img
                      src={h.evidencia_crop}
                      alt={h.trabajador}
                      className="w-12 h-12 rounded object-cover border border-slate-700 bg-slate-900 shrink-0"
                    />
                    <div className="min-w-0 flex-1">
                      <div className="text-xs font-bold text-white truncate">{h.trabajador}</div>
                      <div className="text-[11px] text-slate-400 truncate">
                        {traducirTipoHallazgo(h.tipo)}
                      </div>
                      {h.prendas_faltantes.length > 0 && (
                        <div className="text-[11px] text-rose-400 font-mono font-semibold truncate">
                          Sin: {h.prendas_faltantes.map(traducirPrenda).join(', ')}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-1 border-t border-slate-800 text-xs font-mono">
                    <span className="font-bold text-rose-400 font-tabular">
                      {h.impacto_diario > 0
                        ? `${formatearMoneda(h.impacto_diario, moneda)}/día`
                        : 'US$0.00 (Revisar)'}
                    </span>
                    <Link
                      href={`/cuadrilla?pos=${h.codigo}`}
                      onClick={(e) => e.stopPropagation()}
                      className="inline-flex items-center gap-1 text-[11px] font-bold text-amber-400 hover:underline"
                    >
                      GEMELO 4Z
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
