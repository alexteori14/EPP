'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Activity,
  Bot,
  Building2,
  Camera,
  Ear,
  FileVideo,
  HardHat,
  Radio,
  ShieldAlert,
  ShieldCheck,
  Users,
  Volume2,
} from 'lucide-react';
import { formatearMoneda } from '@/lib/formatters/contract';

interface ModuloHud {
  codigo: string;
  nombre: string;
  ruta: string;
  icono: React.ElementType;
  enVivo?: boolean;
}

const MODULOS_CASETA: ModuloHud[] = [
  { codigo: '01', nombre: 'MONITOR CASETA', ruta: '/resumen', icono: Activity },
  { codigo: '02', nombre: 'TORNIQUETE LIVE', ruta: '/kiosco', icono: Camera, enVivo: true },
  { codigo: '03', nombre: 'GEMELO 4-ZONAS', ruta: '/cuadrilla', icono: Users },
  { codigo: '04', nombre: 'CÁMARAS DE FILA', ruta: '/recorrido', icono: Radio },
  { codigo: '05', nombre: 'BITÁCORA Y MULTAS', ruta: '/hallazgos', icono: ShieldAlert },
  { codigo: '06', nombre: 'RED 18 PLANTAS', ruta: '/red', icono: Building2 },
  { codigo: '07', nombre: 'INGESTA VIDEO', ruta: '/analizar', icono: FileVideo },
  { codigo: '08', nombre: 'INSPECTOR IA', ruta: '/asistente', icono: Bot },
];

function formatearFechaEscaneo(fecha?: string): string | null {
  if (!fecha) return null;
  const d = new Date(fecha);
  if (isNaN(d.getTime())) return null;
  const dia = d.toLocaleDateString('es-MX', { day: '2-digit', month: '2-digit', year: 'numeric' });
  const hora = d.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit', hour12: false });
  return `${dia} ${hora} HRS`;
}

export function Header({
  fechaEscaneo,
  disclaimer = 'Filtro pre-turno · Datos reales de Kaggle + planta demostrativa InduSafe',
  riesgoDiario = 3620,
  incompletos = 7,
  cumplimientoPct = 41.7,
}: {
  fechaEscaneo?: string;
  disclaimer?: string;
  riesgoDiario?: number;
  incompletos?: number;
  cumplimientoPct?: number;
}) {
  const pathname = usePathname();
  const fecha = formatearFechaEscaneo(fechaEscaneo);

  return (
    <header className="sticky top-0 z-40 bg-[#070b12]/95 backdrop-blur-md border-b border-slate-800 select-none">
      {/* Cinta superior de precaución industrial */}
      <div className="h-1.5 w-full franja-precaucion" />

      {/* Barra de telemetría de planta y sensores acústicos */}
      <div className="bg-[#05080f] border-b border-slate-800/90 px-4 sm:px-6 lg:px-8 py-1.5 text-[11px] font-mono flex flex-wrap items-center justify-between gap-3 text-slate-400">
        <div className="flex flex-wrap items-center gap-4 min-w-0">
          <span className="inline-flex items-center gap-1.5 text-amber-400 font-bold tracking-wider">
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
            SCADA // VIGÍA EPP · MTY-N01
          </span>
          <span className="hidden md:inline text-slate-600">|</span>
          <span className="inline-flex items-center gap-1.5 text-rose-300 font-semibold">
            <Volume2 className="w-3.5 h-3.5 text-rose-400" />
            RUIDO EN NAVE: 94.2 dB(A) · NOM-011-STPS (TAPONES OBLIGATORIOS)
          </span>
          <span className="hidden xl:inline text-slate-600">|</span>
          <span className="hidden xl:inline truncate text-slate-400">{disclaimer}</span>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <span className="hidden sm:inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-cyan-300">
            <Ear className="w-3 h-3 text-amber-400" />
            4 ZONAS: LENTES · TAPONES · CHALECO · GUANTES [OPCIONAL POR PUESTO]
          </span>
          {fecha && <span className="text-slate-400">CORTE: {fecha}</span>}
        </div>
      </div>

      {/* Cabecera principal del Centro de Comando y Torniquete */}
      <div className="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-8 py-3 flex flex-col gap-3">
        <div className="flex flex-wrap items-center justify-between gap-4">
          {/* Identidad industrial Vigía EPP */}
          <Link href="/resumen" className="flex items-center gap-3.5 group">
            <div className="w-11 h-11 rounded bg-amber-500 text-slate-950 font-black flex items-center justify-center shadow-[0_0_20px_rgba(245,158,11,0.35)] border border-amber-300">
              <ShieldCheck className="w-6 h-6 stroke-[2.5]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-black tracking-wider uppercase text-white">
                  VIGÍA <span className="text-amber-400">EPP</span>
                </h1>
                <span className="px-2 py-0.5 text-[10px] font-mono font-bold uppercase bg-slate-800 text-amber-300 border border-amber-500/40 rounded">
                  CASETA TORNIQUETE #01
                </span>
              </div>
              <p className="text-xs font-mono text-slate-400">
                CONTROL DE ACCESO BIOMÉTRICO PRE-TURNO · PLANTA MONTERREY NORTE
              </p>
            </div>
          </Link>

          {/* Semáforo físico de torniquete y telemetría de turno */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="hidden sm:flex items-center gap-4 px-3.5 py-2 rounded bg-slate-900/90 border border-slate-800 font-mono text-xs">
              <div>
                <div className="text-[10px] text-slate-400 uppercase">ESTADO TORNIQUETE</div>
                <div className="font-bold text-rose-400 flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
                  {incompletos} RETENCIONES EN FILA
                </div>
              </div>
              <div className="border-l border-slate-800 pl-4">
                <div className="text-[10px] text-slate-400 uppercase">EXPOSICIÓN STPS</div>
                <div className="font-bold text-amber-400 font-tabular">
                  {formatearMoneda(riesgoDiario)}/DÍA
                </div>
              </div>
              <div className="border-l border-slate-800 pl-4">
                <div className="text-[10px] text-slate-400 uppercase">PASE DE CUADRILLA</div>
                <div className="font-bold text-emerald-400 font-tabular">{cumplimientoPct}% OK</div>
              </div>
            </div>

            <Link
              href="/kiosco"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded bg-amber-500 hover:bg-amber-400 text-slate-950 font-mono font-extrabold text-xs uppercase tracking-wider shadow-[0_0_16px_rgba(245,158,11,0.3)] transition-all"
            >
              <Camera className="w-4 h-4 stroke-[2.5]" />
              ESCANEAR EN TORNIQUETE
            </Link>
          </div>
        </div>

        {/* Botonera horizontal táctica de 8 módulos de comando */}
        <nav
          aria-label="Módulos del Centro de Comando Vigía EPP"
          className="flex items-center gap-1.5 overflow-x-auto pb-1 pt-1 border-t border-slate-800/80"
        >
          {MODULOS_CASETA.map((m) => {
            const Icon = m.icono;
            const activo = pathname === m.ruta || (m.ruta === '/resumen' && pathname === '/');
            return (
              <Link
                key={m.ruta}
                href={m.ruta}
                className={`inline-flex items-center gap-2 px-3 py-2 rounded font-mono text-xs font-bold tracking-wide transition-all shrink-0 border ${
                  activo
                    ? 'bg-amber-500/15 text-amber-300 border-amber-500/70 shadow-[inset_0_0_12px_rgba(245,158,11,0.18)]'
                    : 'bg-slate-900/70 text-slate-400 border-slate-800 hover:bg-slate-800/90 hover:text-slate-200 hover:border-slate-700'
                }`}
              >
                <span
                  className={`text-[10px] px-1 py-0.2 rounded ${
                    activo ? 'bg-amber-400 text-slate-950 font-black' : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  {m.codigo}
                </span>
                <Icon className={`w-3.5 h-3.5 ${activo ? 'text-amber-400' : 'text-slate-400'}`} />
                <span>{m.nombre}</span>
                {m.enVivo && (
                  <span className="px-1.5 py-0.2 text-[9px] font-black rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                    LIVE
                  </span>
                )}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
