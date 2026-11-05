'use client';

import React, { useEffect, useRef, useState } from 'react';
import {
  AlertTriangle,
  Camera,
  CheckCircle2,
  Eye,
  Hand,
  Loader2,
  ShieldAlert,
  ShieldCheck,
  Shirt,
  Upload,
  VideoOff,
} from 'lucide-react';
import { PresetKiosco, RespuestaKiosco } from '@/types/kiosco';
import { PrendaEPP } from '@/types/hallazgos';
import { evaluarKioscoImagenB64, evaluarKioscoPreset } from '@/lib/api/analisis';
import { DICCIONARIO_PRENDAS, ORDEN_PRENDAS, traducirEstadoPrenda } from '@/lib/formatters/contract';
import { ICONO_PANTALLA } from '@/components/iconos';
import { TituloPagina } from '@/components/layout/TituloPagina';

const PRESETS: { id: PresetKiosco; etiqueta: string; descripcion: string }[] = [
  { id: 'completo', etiqueta: 'EPP Completo (3/3)', descripcion: 'Lentes + Chaleco + Guantes' },
  { id: 'sin_lentes', etiqueta: 'Sin Lentes', descripcion: 'Falta protección ocular' },
  { id: 'sin_guantes', etiqueta: 'Sin Guantes', descripcion: 'Falta protección anticorte' },
  { id: 'sin_chaleco', etiqueta: 'Sin Chaleco', descripcion: 'Falta alta visibilidad' },
  {
    id: 'incompleto_multiple',
    etiqueta: 'Múltiple Faltante',
    descripcion: 'Sin lentes ni guantes',
  },
];

const ICONO_PRENDA: Record<PrendaEPP, React.ElementType> = {
  lentes: Eye,
  chaleco: Shirt,
  guantes: Hand,
};

export function KioscoView() {
  const [presetActivo, setPresetActivo] = useState<PresetKiosco>('completo');
  const [resultado, setResultado] = useState<RespuestaKiosco | null>(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [camaraActiva, setCamaraActiva] = useState(false);

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const correrPreset = async (preset: PresetKiosco) => {
    setPresetActivo(preset);
    setCargando(true);
    setError(null);
    try {
      const res = await evaluarKioscoPreset(preset);
      setResultado(res);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'No se pudo evaluar en el kiosco');
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    correrPreset('completo');
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }
    };
  }, []);

  const alternarCamara = async () => {
    if (camaraActiva) {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
      }
      setCamaraActiva(false);
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 1280, height: 720 },
      });
      streamRef.current = stream;
      setCamaraActiva(true);
      setTimeout(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      }, 50);
    } catch {
      setError(
        'No se detectó cámara web local disponible. Puedes usar los 5 escenarios en vivo o subir una fotografía.'
      );
    }
  };

  const capturarCuadroCamara = async () => {
    if (!videoRef.current) return;
    const canvas = document.createElement('canvas');
    canvas.width = videoRef.current.videoWidth || 1280;
    canvas.height = videoRef.current.videoHeight || 720;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
    const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
    setCargando(true);
    setError(null);
    try {
      const res = await evaluarKioscoImagenB64(dataUrl);
      setResultado(res);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Error al evaluar captura');
    } finally {
      setCargando(false);
    }
  };

  const subirFoto = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async () => {
      if (typeof reader.result === 'string') {
        setCargando(true);
        setError(null);
        try {
          const res = await evaluarKioscoImagenB64(reader.result);
          setResultado(res);
        } catch (err: unknown) {
          setError(err instanceof Error ? err.message : 'Error al evaluar imagen');
        } finally {
          setCargando(false);
        }
      }
    };
    reader.readAsDataURL(file);
  };

  const autorizado = resultado?.estado_acceso === 'autorizado';

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <TituloPagina
          icono={ICONO_PANTALLA.kiosco}
          titulo="Kiosco de Pase de Turno en Vivo (< 300 ms)"
        >
          Inspección instantánea en torniquete antes de entrar a piso de producción (3 prendas
          obligatorias: Lentes, Chaleco y Guantes).
        </TituloPagina>

        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={alternarCamara}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold transition-colors"
          >
            {camaraActiva ? <VideoOff className="w-4 h-4" /> : <Camera className="w-4 h-4" />}
            {camaraActiva ? 'Apagar cámara web' : 'Usar cámara web'}
          </button>

          <label className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-semibold cursor-pointer transition-colors">
            <Upload className="w-4 h-4 text-slate-500" />
            Evaluar foto
            <input type="file" accept="image/*" onChange={subirFoto} className="hidden" />
          </label>
        </div>
      </div>

      {/* Selector de 5 escenarios en vivo con 1 clic */}
      <section className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Simulador de Torniquete · Prueba los 5 casos con el motor en vivo
          </span>
          {resultado && (
            <span className="font-mono text-xs text-slate-500 font-tabular">
              Inferencia: <strong className="text-slate-800">{resultado.ms_proceso} ms</strong>
            </span>
          )}
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5">
          {PRESETS.map((p) => {
            const activo = presetActivo === p.id;
            return (
              <button
                key={p.id}
                type="button"
                data-testid={`kiosco-preset-${p.id}`}
                onClick={() => correrPreset(p.id)}
                disabled={cargando}
                className={`p-3 rounded-lg border text-left transition-all ${
                  activo
                    ? 'bg-slate-900 text-white border-slate-900 shadow-sm'
                    : 'bg-slate-50 hover:bg-slate-100 text-slate-800 border-slate-200'
                }`}
              >
                <div className="font-semibold text-xs">{p.etiqueta}</div>
                <div
                  className={`text-[11px] mt-0.5 ${
                    activo ? 'text-slate-300' : 'text-slate-500'
                  }`}
                >
                  {p.descripcion}
                </div>
              </button>
            );
          })}
        </div>
      </section>

      {error && (
        <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-800 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0 text-amber-600" />
          {error}
        </div>
      )}

      {/* Visor principal + Veredicto y Gemelo Anatómico de 3 zonas */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <section className="lg:col-span-7 bg-slate-950 rounded-xl border border-slate-800 overflow-hidden shadow-sm flex flex-col justify-between">
          <div className="p-4 border-b border-slate-800 flex items-center justify-between text-xs text-slate-300">
            <span className="font-mono font-semibold text-white">
              CÁMARA DE FILTRO · TORNIQUETE ACCESO NORTE
            </span>
            <span className="inline-flex items-center gap-1.5 text-teal-400 font-mono">
              <span className="w-2 h-2 rounded-full bg-teal-400 animate-pulse" />
              YOLO11 · 3 ZONAS ACTIVAS
            </span>
          </div>

          <div className="relative aspect-video bg-slate-900 flex items-center justify-center overflow-hidden">
            {camaraActiva ? (
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="w-full h-full object-cover"
              />
            ) : resultado?.imagen_anotada_b64 ? (
              <img
                src={resultado.imagen_anotada_b64}
                alt="Inspección de kiosco anotada"
                className="w-full h-full object-contain"
              />
            ) : (
              <div className="text-slate-400 text-sm flex items-center gap-2">
                <Loader2 className="w-5 h-5 animate-spin" />
                Iniciando visor de kiosco...
              </div>
            )}

            {cargando && (
              <div className="absolute inset-0 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center text-white text-sm font-semibold gap-2">
                <Loader2 className="w-5 h-5 animate-spin text-teal-400" />
                Evaluando Lentes, Chaleco y Guantes...
              </div>
            )}
          </div>

          {camaraActiva && (
            <div className="p-4 bg-slate-900 border-t border-slate-800 flex justify-end">
              <button
                type="button"
                onClick={capturarCuadroCamara}
                className="px-4 py-2 rounded-lg bg-teal-600 hover:bg-teal-500 text-white text-xs font-bold"
              >
                Capturar y Evaluar Trabajador Ahora
              </button>
            </div>
          )}
        </section>

        {/* Panel derecho: Veredicto de Torniquete y 3 Zonas Anatómicas */}
        <section className="lg:col-span-5 flex flex-col justify-between gap-4">
          <div
            data-testid="kiosco-veredicto"
            className={`p-6 rounded-xl border-2 shadow-sm transition-colors ${
              autorizado
                ? 'bg-emerald-50/90 border-emerald-500 text-emerald-950'
                : 'bg-rose-50/90 border-rose-500 text-rose-950'
            }`}
          >
            <div className="flex items-center gap-3">
              {autorizado ? (
                <ShieldCheck className="w-10 h-10 text-emerald-600 shrink-0" />
              ) : (
                <ShieldAlert className="w-10 h-10 text-rose-600 shrink-0" />
              )}
              <div>
                <div className="text-xs font-bold uppercase tracking-wider opacity-75">
                  Veredicto de Torniquete Pre-Turno
                </div>
                <h3 className="text-xl font-extrabold tracking-tight">
                  {autorizado ? 'PASE DE TURNO AUTORIZADO' : 'ACCESO DETENIDO · FALTA EPP'}
                </h3>
              </div>
            </div>
            <p className="mt-3 text-sm font-medium">
              {resultado?.mensaje ?? 'Evaluando trabajador...'}
            </p>
          </div>

          {/* Desglose de las 3 Zonas Anatómicas */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-3 flex-1">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-bold text-slate-900">
                Verificación Anatómica por Zona (3/3)
              </h4>
              <span className="text-xs text-slate-500">Sin casco ni mascarilla</span>
            </div>

            <div className="space-y-2.5">
              {ORDEN_PRENDAS.map((pr) => {
                const info = DICCIONARIO_PRENDAS[pr];
                const ev = resultado?.zonas?.[pr];
                const estado = ev?.estado ?? 'dudoso';
                const Icon = ICONO_PRENDA[pr];

                const badgeClass =
                  estado === 'ok'
                    ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                    : estado === 'falta'
                    ? 'bg-rose-100 text-rose-800 border-rose-300'
                    : 'bg-amber-100 text-amber-800 border-amber-300';

                return (
                  <div
                    key={pr}
                    data-testid={`kiosco-prenda-${pr}`}
                    className="p-3.5 rounded-lg border border-slate-200 bg-slate-50/70 flex items-center justify-between gap-3"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <span
                        className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${
                          estado === 'ok'
                            ? 'bg-emerald-100 text-emerald-700'
                            : estado === 'falta'
                            ? 'bg-rose-100 text-rose-700'
                            : 'bg-amber-100 text-amber-700'
                        }`}
                      >
                        <Icon className="w-5 h-5" />
                      </span>
                      <div className="min-w-0">
                        <div className="font-semibold text-sm text-slate-900">{info.nombre}</div>
                        <div className="text-xs text-slate-500 truncate">
                          {info.norma} · {info.zona}
                        </div>
                      </div>
                    </div>

                    <div className="text-right shrink-0">
                      <span
                        className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold border ${badgeClass}`}
                      >
                        {estado === 'ok' && <CheckCircle2 className="w-3.5 h-3.5" />}
                        {traducirEstadoPrenda(estado)}
                      </span>
                      {ev && (
                        <div className="text-[11px] text-slate-500 font-tabular mt-1">
                          Confianza {Math.round(ev.confianza * 100)}%
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
