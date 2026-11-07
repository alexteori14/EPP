'use client';

import React, { useEffect, useRef, useState } from 'react';
import {
  AlertTriangle,
  Camera,
  CheckCircle2,
  Ear,
  Eye,
  Hand,
  Loader2,
  ShieldAlert,
  ShieldCheck,
  Shirt,
  Upload,
  VideoOff,
  Volume2,
} from 'lucide-react';
import { PresetKiosco, RespuestaKiosco } from '@/types/kiosco';
import { PrendaEPP } from '@/types/hallazgos';
import { evaluarKioscoImagenB64, evaluarKioscoPreset } from '@/lib/api/analisis';
import { DICCIONARIO_PRENDAS, ORDEN_PRENDAS, traducirEstadoPrenda } from '@/lib/formatters/contract';
import { ICONO_PANTALLA } from '@/components/iconos';
import { TituloPagina } from '@/components/layout/TituloPagina';

const PRESETS: { id: PresetKiosco; etiqueta: string; descripcion: string }[] = [
  {
    id: 'completo',
    etiqueta: 'EPP Completo (4/4)',
    descripcion: 'Lentes + Tapones + Chaleco + Guantes',
  },
  { id: 'sin_lentes', etiqueta: 'Sin Lentes', descripcion: 'Falta protección ocular' },
  {
    id: 'sin_tapones',
    etiqueta: 'Sin Tapones Auditivos',
    descripcion: 'Sin inserción auditiva (>85 dB)',
  },
  {
    id: 'sin_guantes',
    etiqueta: 'Sin Guantes',
    descripcion: 'Condicional según puesto',
  },
  { id: 'sin_chaleco', etiqueta: 'Sin Chaleco', descripcion: 'Falta alta visibilidad' },
  {
    id: 'incompleto_multiple',
    etiqueta: 'Múltiple Faltante',
    descripcion: 'Sin lentes, tapones ni guantes',
  },
];

const ICONO_PRENDA: Record<PrendaEPP, React.ElementType> = {
  lentes: Eye,
  tapones: Ear,
  chaleco: Shirt,
  guantes: Hand,
};

export function KioscoView() {
  const [presetActivo, setPresetActivo] = useState<PresetKiosco>('completo');
  const [requiereGuantes, setRequiereGuantes] = useState<boolean>(true);
  const [resultado, setResultado] = useState<RespuestaKiosco | null>(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [camaraActiva, setCamaraActiva] = useState(false);

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const correrPreset = async (preset: PresetKiosco, reqGuantes = requiereGuantes) => {
    setPresetActivo(preset);
    setCargando(true);
    setError(null);
    try {
      const res = await evaluarKioscoPreset(preset, reqGuantes);
      setResultado(res);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'No se pudo evaluar en el kiosco');
    } finally {
      setCargando(false);
    }
  };

  const cambiarPerfilPuesto = async (exigeGuantes: boolean) => {
    setRequiereGuantes(exigeGuantes);
    await correrPreset(presetActivo, exigeGuantes);
  };

  useEffect(() => {
    correrPreset('completo', true);
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
        'No se detectó cámara web local disponible. Puedes usar los 6 escenarios en vivo o subir una fotografía.'
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
      const res = await evaluarKioscoImagenB64(dataUrl, requiereGuantes);
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
          const res = await evaluarKioscoImagenB64(reader.result, requiereGuantes);
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

  const estadoAcceso = resultado?.estado_acceso ?? 'revisar';
  const autorizado = estadoAcceso === 'autorizado';
  const esRevision = estadoAcceso === 'revisar' || estadoAcceso === 'sin_persona';

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <TituloPagina
          icono={ICONO_PANTALLA.kiosco}
          titulo="Caseta de Torniquete Biométrico en Vivo (< 300 ms)"
        >
          Verifica las 4 zonas anatómicas antes de liberar el torniquete: Lentes, Tapones Auditivos
          de Inserción y Chaleco (obligatorios generales) + Guantes (según el puesto).
        </TituloPagina>

        <div className="flex items-center gap-2.5 shrink-0">
          <button
            type="button"
            onClick={alternarCamara}
            className="inline-flex items-center gap-2 px-3.5 py-2.5 rounded bg-amber-500 hover:bg-amber-400 text-slate-950 font-mono text-xs font-extrabold uppercase transition-colors"
          >
            {camaraActiva ? <VideoOff className="w-4 h-4" /> : <Camera className="w-4 h-4" />}
            {camaraActiva ? 'APAGAR CÁMARA' : 'ACTIVAR CÁMARA WEB'}
          </button>

          <label className="inline-flex items-center gap-2 px-3.5 py-2.5 rounded bg-slate-900 border border-slate-700 hover:border-amber-500/50 text-slate-200 font-mono text-xs font-bold uppercase cursor-pointer transition-colors">
            <Upload className="w-4 h-4 text-amber-400" />
            EVALUAR FOTO
            <input type="file" accept="image/*" onChange={subirFoto} className="hidden" />
          </label>
        </div>
      </div>

      {/* Selector de Perfil de Puesto (Guantes Obligatorios vs Opcionales) + 6 Escenarios */}
      <section className="panel-caseta rounded-lg p-5 space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 border-b border-slate-800 pb-4">
          <div className="space-y-1">
            <div className="text-[11px] font-mono font-bold uppercase tracking-wider text-amber-400">
              CONFIGURACIÓN DE PUESTO EN TORNIQUETE // REGLA DE GUANTES CONDICIONALES
            </div>
            <p className="text-xs text-slate-400">
              Los guantes solo son obligatorios para puestos de contacto mecánico/térmico. Cambia el
              perfil para comprobar cómo responde el torniquete:
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2 bg-slate-950 p-1.5 rounded border border-slate-800">
            <button
              type="button"
              data-testid="kiosco-rol-con-guantes"
              onClick={() => cambiarPerfilPuesto(true)}
              className={`px-3 py-1.5 rounded font-mono text-xs font-bold transition-all ${
                requiereGuantes
                  ? 'bg-amber-500 text-slate-950 shadow'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              PUESTO OPERATIVO · EXIGE GUANTES (4/4 EPP)
            </button>
            <button
              type="button"
              data-testid="kiosco-rol-sin-guantes"
              onClick={() => cambiarPerfilPuesto(false)}
              className={`px-3 py-1.5 rounded font-mono text-xs font-bold transition-all ${
                !requiereGuantes
                  ? 'bg-cyan-400 text-slate-950 shadow'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              SUPERVISIÓN / MONTACARGAS · GUANTES OPCIONALES (3/3 EPP)
            </button>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400">
            SIMULADOR DE ESCENARIOS EN TORNIQUETE (6 PRUEBAS EN VIVO)
          </span>
          {resultado && (
            <span className="font-mono text-xs text-slate-400 font-tabular">
              TIEMPO DE RESPUESTA:{' '}
              <strong className="text-amber-400">{resultado.ms_proceso} ms</strong>
            </span>
          )}
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
          {PRESETS.map((p) => {
            const activo = presetActivo === p.id;
            return (
              <button
                key={p.id}
                type="button"
                data-testid={`kiosco-preset-${p.id}`}
                onClick={() => correrPreset(p.id)}
                disabled={cargando}
                className={`p-3 rounded border text-left transition-all ${
                  activo
                    ? 'bg-amber-500/15 text-amber-300 border-amber-400 shadow-[inset_0_0_12px_rgba(245,158,11,0.2)]'
                    : 'bg-slate-950/90 hover:bg-slate-900 text-slate-300 border-slate-800'
                }`}
              >
                <div className="font-mono font-bold text-xs">{p.etiqueta}</div>
                <div className="text-[11px] mt-0.5 text-slate-400">{p.descripcion}</div>
              </button>
            );
          })}
        </div>
      </section>

      {error && (
        <div className="p-4 rounded bg-amber-950/60 border border-amber-500/50 text-xs text-amber-200 font-mono flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0 text-amber-400" />
          {error}
        </div>
      )}

      {/* Visor Óptico de Torniquete + Semáforo de Acceso y 4 Zonas Anatómicas */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <section className="lg:col-span-7 bg-slate-950 rounded-lg border border-slate-800 overflow-hidden shadow-xl flex flex-col justify-between">
          <div className="px-4 py-3 bg-[#060911] border-b border-slate-800 flex flex-wrap items-center justify-between gap-2 text-xs font-mono text-slate-300">
            <span className="font-bold text-white flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
              CAM-01 // TORNIQUETE ACCESO NORTE
            </span>
            <span className="inline-flex items-center gap-1.5 text-amber-400">
              <Volume2 className="w-3.5 h-3.5" />
              ZONA 94 dB(A) · 4 ZONAS ANATÓMICAS ACTIVAS
            </span>
          </div>

          <div className="relative aspect-video bg-black flex items-center justify-center overflow-hidden">
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
              <div className="text-slate-400 text-sm font-mono flex items-center gap-2">
                <Loader2 className="w-5 h-5 animate-spin text-amber-400" />
                INICIANDO ESCÁNER DE TORNIQUETE...
              </div>
            )}

            {cargando && (
              <div className="absolute inset-0 bg-slate-950/75 backdrop-blur-sm flex items-center justify-center text-amber-300 text-xs font-mono font-bold gap-2">
                <Loader2 className="w-5 h-5 animate-spin text-amber-400" />
                ESCANEANDO 4 ZONAS (OJOS · OÍDOS · TORSO · MANOS)...
              </div>
            )}
          </div>

          {camaraActiva && (
            <div className="p-4 bg-slate-900 border-t border-slate-800 flex justify-end">
              <button
                type="button"
                onClick={capturarCuadroCamara}
                className="px-4 py-2 rounded bg-amber-500 hover:bg-amber-400 text-slate-950 font-mono text-xs font-extrabold uppercase"
              >
                CAPTURAR Y VALIDAR PASE DE TURNO
              </button>
            </div>
          )}
        </section>

        {/* Panel derecho: Semáforo de Torniquete y 4 Zonas Anatómicas */}
        <section className="lg:col-span-5 flex flex-col justify-between gap-4">
          <div
            data-testid="kiosco-veredicto"
            className={`p-6 rounded-lg border-2 shadow-lg transition-colors ${
              autorizado
                ? 'bg-emerald-950/50 border-emerald-500 text-emerald-100'
                : esRevision
                ? 'bg-amber-950/50 border-amber-500 text-amber-100'
                : 'bg-rose-950/50 border-rose-500 text-rose-100'
            }`}
          >
            <div className="flex items-center gap-3.5">
              {autorizado ? (
                <ShieldCheck className="w-11 h-11 text-emerald-400 shrink-0" />
              ) : esRevision ? (
                <AlertTriangle className="w-11 h-11 text-amber-400 shrink-0" />
              ) : (
                <ShieldAlert className="w-11 h-11 text-rose-400 shrink-0" />
              )}
              <div>
                <div className="text-[11px] font-mono font-bold uppercase tracking-wider opacity-80">
                  SEMÁFORO DE TORNIQUETE PRE-TURNO
                </div>
                <h3 className="text-xl font-black tracking-tight">
                  {autorizado
                    ? 'PASE DE TURNO AUTORIZADO'
                    : esRevision
                    ? 'VERIFICACIÓN EN CASETA · LECTURA DUDOSA'
                    : 'ACCESO DETENIDO · FALTA EPP'}
                </h3>
              </div>
            </div>
            <p className="mt-3 text-xs sm:text-sm font-mono">{resultado?.mensaje ?? 'Evaluando...'}</p>
          </div>

          {/* Desglose de las 4 Zonas Anatómicas */}
          <div className="panel-caseta rounded-lg p-5 space-y-3 flex-1">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
              <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-amber-400">
                AUDITORÍA POR ZONA ANATÓMICA ({resultado?.prendas_completas ?? 0}/
                {resultado?.prendas_requeridas ?? 4} REQUERIDAS)
              </h4>
              <span className="text-[11px] font-mono text-slate-400">SIN CASCO NI MASCARILLA</span>
            </div>

            <div className="space-y-2.5">
              {ORDEN_PRENDAS.map((pr) => {
                const info = DICCIONARIO_PRENDAS[pr];
                const ev = resultado?.zonas?.[pr];
                const estado = ev?.estado ?? 'dudoso';
                const requerida = ev?.requerida ?? (pr !== 'guantes' || requiereGuantes);
                const esOpcionalNoPortado = !requerida && estado !== 'ok';
                const Icon = ICONO_PRENDA[pr];

                const badgeClass = esOpcionalNoPortado
                  ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
                  : estado === 'ok'
                  ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                  : estado === 'falta'
                  ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                  : 'bg-amber-500/20 text-amber-300 border-amber-500/40';

                return (
                  <div
                    key={pr}
                    data-testid={`kiosco-prenda-${pr}`}
                    className="p-3.5 rounded border border-slate-800 bg-slate-950/80 flex items-center justify-between gap-3"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <span
                        className={`w-9 h-9 rounded flex items-center justify-center shrink-0 border ${
                          esOpcionalNoPortado
                            ? 'bg-cyan-950/60 text-cyan-300 border-cyan-500/40'
                            : estado === 'ok'
                            ? 'bg-emerald-950/60 text-emerald-400 border-emerald-500/40'
                            : estado === 'falta'
                            ? 'bg-rose-950/60 text-rose-400 border-rose-500/40'
                            : 'bg-amber-950/60 text-amber-400 border-amber-500/40'
                        }`}
                      >
                        <Icon className="w-5 h-5" />
                      </span>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-sm text-white">{info.nombre}</span>
                          {!requerida && (
                            <span className="text-[10px] font-mono font-bold px-1.5 py-0.2 rounded bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">
                              OPCIONAL EN ESTE PUESTO
                            </span>
                          )}
                        </div>
                        <div className="text-[11px] font-mono text-slate-400 truncate">
                          {info.norma} · {info.zona}
                        </div>
                      </div>
                    </div>

                    <div className="text-right shrink-0">
                      <span
                        className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-mono font-bold border ${badgeClass}`}
                      >
                        {estado === 'ok' && <CheckCircle2 className="w-3.5 h-3.5" />}
                        {traducirEstadoPrenda(estado, requerida)}
                      </span>
                      {ev && (
                        <div className="text-[11px] font-mono text-slate-400 font-tabular mt-1">
                          Conf. {Math.round(ev.confianza * 100)}%
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
