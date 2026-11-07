'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  CheckCircle2,
  FileVideo,
  Loader2,
  Play,
  RotateCcw,
  Trash2,
  Upload,
} from 'lucide-react';
import { AnalisisMeta } from '@/types/analisis';
import {
  activarAnalisis,
  borrarAnalisis,
  consultarAnalisis,
  EXTENSIONES_VIDEO,
  listarAnalisis,
  subirVideo,
} from '@/lib/api/analisis';
import { formatearMoneda } from '@/lib/formatters/contract';
import { ICONO_PANTALLA } from '@/components/iconos';
import { TituloPagina } from '@/components/layout/TituloPagina';
import { Proporcion } from '@/components/graficas/Barras';

export function AnalizarView() {
  const router = useRouter();
  const [historial, setHistorial] = useState<AnalisisMeta[]>([]);
  const [activoId, setActivoId] = useState<string | null>(null);
  const [subiendoPct, setSubiendoPct] = useState<number | null>(null);
  const [enCurso, setEnCurso] = useState<AnalisisMeta | null>(null);
  const [error, setError] = useState<string | null>(null);

  const cargarHistorial = async () => {
    try {
      const res = await listarAnalisis();
      setHistorial(res.analisis);
      setActivoId(res.activo);
    } catch {
      // API apagada o sin análisis previos
    }
  };

  useEffect(() => {
    cargarHistorial();
  }, []);

  useEffect(() => {
    if (!enCurso || enCurso.status !== 'procesando') return;
    const timer = setInterval(async () => {
      try {
        const meta = await consultarAnalisis(enCurso.id);
        setEnCurso(meta);
        if (meta.status === 'completado' || meta.status === 'error') {
          clearInterval(timer);
          await cargarHistorial();
        }
      } catch {
        clearInterval(timer);
      }
    }, 1200);
    return () => clearInterval(timer);
  }, [enCurso]);

  const manejarArchivo = async (file: File | undefined) => {
    if (!file) return;
    setError(null);
    setSubiendoPct(0);
    try {
      const meta = await subirVideo(file, (f) => setSubiendoPct(Math.round(f * 100)));
      setSubiendoPct(null);
      setEnCurso(meta);
      await cargarHistorial();
    } catch (e: unknown) {
      setSubiendoPct(null);
      setError(e instanceof Error ? e.message : 'Error al subir el video');
    }
  };

  const cambiarActivo = async (id: string | null) => {
    try {
      await activarAnalisis(id);
      await cargarHistorial();
      router.refresh();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'No se pudo cambiar la corrida activa');
    }
  };

  const eliminar = async (id: string) => {
    try {
      await borrarAnalisis(id);
      await cargarHistorial();
      router.refresh();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'No se pudo borrar el análisis');
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <TituloPagina
        icono={ICONO_PANTALLA.analizar}
        titulo="Subir y Procesar Nuevo Video de Turno"
      >
        Sube una grabación de ingreso a turno ({EXTENSIONES_VIDEO.join(', ')}) para ejecutar el
        detector YOLO11 (`modelos/epp.pt`), asociar Lentes, Tapones Auditivos, Chaleco y Guantes por
        trabajador y cruzar contra el inventario de caseta.
      </TituloPagina>

      {/* Zona de carga Drag & Drop */}
      <section className="panel-caseta rounded-lg border-2 border-dashed border-amber-500/40 hover:border-amber-400 p-8 text-center transition-colors space-y-4">
        <div className="w-12 h-12 rounded bg-amber-500/15 text-amber-400 border border-amber-500/40 flex items-center justify-center mx-auto">
          <Upload className="w-6 h-6" />
        </div>
        <div className="space-y-1">
          <h3 className="text-base font-bold text-white">
            Selecciona o arrastra un video de formación pre-turno
          </h3>
          <p className="text-xs text-slate-400 max-w-lg mx-auto">
            El motor seleccionará los cuadros más nítidos, evaluará las 4 zonas anatómicas (Lentes,
            Tapones Auditivos, Chaleco y Guantes según puesto) y generará el video anotado en H.264.
          </p>
        </div>

        <div>
          <label className="inline-flex items-center gap-2 px-5 py-2.5 rounded bg-amber-500 hover:bg-amber-400 text-slate-950 font-mono text-xs font-extrabold uppercase cursor-pointer shadow transition-colors">
            <FileVideo className="w-4 h-4" />
            ELEGIR ARCHIVO DE VIDEO
            <input
              type="file"
              accept={EXTENSIONES_VIDEO.join(',')}
              onChange={(e) => manejarArchivo(e.target.files?.[0])}
              className="hidden"
            />
          </label>
        </div>

        {subiendoPct !== null && (
          <div className="max-w-md mx-auto space-y-1.5 pt-2">
            <div className="flex justify-between text-xs font-mono text-slate-300 font-bold">
              <span>SUBIENDO VIDEO AL MOTOR...</span>
              <span className="font-tabular">{subiendoPct}%</span>
            </div>
            <Proporcion pct={subiendoPct} tono="bg-amber-500" />
          </div>
        )}

        {enCurso && enCurso.status === 'procesando' && (
          <div className="max-w-md mx-auto p-4 rounded bg-slate-950 border border-amber-500/40 text-white text-left space-y-2">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="inline-flex items-center gap-2 font-bold text-amber-300">
                <Loader2 className="w-4 h-4 animate-spin" />
                {enCurso.paso}
              </span>
              <span className="font-tabular">{enCurso.progreso}%</span>
            </div>
            <Proporcion pct={enCurso.progreso} tono="bg-amber-500" />
          </div>
        )}

        {error && (
          <div className="max-w-md mx-auto p-3 rounded bg-rose-950/60 border border-rose-700 text-xs text-rose-200 font-mono">
            {error}
          </div>
        )}
      </section>

      {/* Selector entre recorrido demostrativo e historial de videos subidos */}
      <section className="panel-caseta rounded-lg p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-white">Corridas de inspección disponibles</h3>
            <p className="text-xs text-slate-400">
              Elige qué corrida alimenta los módulos del Centro de Comando Vigía EPP.
            </p>
          </div>

          {activoId !== null && (
            <button
              type="button"
              onClick={() => cambiarActivo(null)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-slate-900 border border-slate-700 hover:border-amber-500/50 text-slate-200 font-mono text-xs font-bold"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              VOLVER A CORRIDA DEMO
            </button>
          )}
        </div>

        <div className="space-y-3">
          {/* Recorrido base demostrativo */}
          <div
            className={`p-4 rounded border flex items-center justify-between gap-4 ${
              activoId === null
                ? 'border-amber-500 bg-amber-500/10 ring-1 ring-amber-500'
                : 'border-slate-800 bg-slate-950/80'
            }`}
          >
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-sm text-white">
                  Recorrido de Demostración · Turno Matutino 06:00 (recorrido_turno.mp4)
                </span>
                {activoId === null && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-amber-500 text-slate-950">
                    <CheckCircle2 className="w-3 h-3" />
                    ACTIVA EN CONSOLA
                  </span>
                )}
              </div>
              <p className="text-xs font-mono text-slate-400 mt-0.5">
                12 estaciones en 3 líneas · 4 zonas (Lentes, Tapones, Chaleco y Guantes según puesto)
              </p>
            </div>

            {activoId !== null && (
              <button
                type="button"
                onClick={() => cambiarActivo(null)}
                className="px-3 py-1.5 rounded bg-amber-500 text-slate-950 font-mono text-xs font-bold"
              >
                USAR ESTA CORRIDA
              </button>
            )}
          </div>

          {/* Videos subidos por el usuario */}
          {historial.map((item) => {
            const esActivo = item.id === activoId;
            return (
              <div
                key={item.id}
                className={`p-4 rounded border flex items-center justify-between gap-4 ${
                  esActivo
                    ? 'border-amber-500 bg-amber-500/10 ring-1 ring-amber-500'
                    : 'border-slate-800 bg-slate-950/80'
                }`}
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-white truncate">{item.nombre}</span>
                    <span className="font-mono text-xs text-slate-400">{item.id}</span>
                  </div>
                  <div className="text-xs font-mono text-slate-400 mt-0.5">
                    Estado: <strong className="text-amber-300">{item.status}</strong>
                    {item.resumen && (
                      <>
                        {' '}
                        · {item.resumen.trabajadores_incompletos} incompletos ·{' '}
                        {formatearMoneda(item.resumen.dinero_en_riesgo_diario)}/día
                      </>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  {item.status === 'completado' && !esActivo && (
                    <button
                      type="button"
                      onClick={() => cambiarActivo(item.id)}
                      className="inline-flex items-center gap-1 px-3 py-1.5 rounded bg-amber-500 text-slate-950 font-mono text-xs font-bold"
                    >
                      <Play className="w-3 h-3" />
                      ACTIVAR
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => eliminar(item.id)}
                    className="p-2 rounded text-slate-400 hover:text-rose-400 hover:bg-rose-950/50"
                    title="Eliminar análisis"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
