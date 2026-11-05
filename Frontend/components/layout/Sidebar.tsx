'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ShieldCheck } from 'lucide-react';
import { ICONO_PANTALLA } from '@/components/iconos';

interface NavItem {
  nombre: string;
  ruta: string;
  icono: React.ElementType;
  badge?: string;
}

const ENTRADA: NavItem[] = [
  { nombre: 'Kiosco en vivo', ruta: '/kiosco', icono: ICONO_PANTALLA.kiosco, badge: 'LIVE' },
  { nombre: 'Subir video', ruta: '/analizar', icono: ICONO_PANTALLA.analizar },
];

const NAVEGACION: NavItem[] = [
  { nombre: 'Resumen de turno', ruta: '/resumen', icono: ICONO_PANTALLA.resumen },
  { nombre: 'Recorrido de fila', ruta: '/recorrido', icono: ICONO_PANTALLA.recorrido },
  { nombre: 'Cuadrilla y EPP', ruta: '/cuadrilla', icono: ICONO_PANTALLA.cuadrilla },
  { nombre: 'Hallazgos', ruta: '/hallazgos', icono: ICONO_PANTALLA.hallazgos },
  { nombre: 'Impacto en red', ruta: '/red', icono: ICONO_PANTALLA.red },
  { nombre: 'Asistente IA', ruta: '/asistente', icono: ICONO_PANTALLA.asistente },
];

export function Sidebar() {
  const pathname = usePathname();

  const enlace = (item: NavItem) => {
    const Icon = item.icono;
    const isActive = pathname === item.ruta || (item.ruta === '/resumen' && pathname === '/');
    return (
      <Link
        key={item.ruta}
        href={item.ruta}
        className={`flex items-center justify-between gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
          isActive
            ? 'bg-slate-800 text-white font-semibold'
            : 'text-slate-400 hover:bg-slate-800/60 hover:text-white'
        }`}
      >
        <span className="flex items-center gap-3 min-w-0">
          <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-teal-400' : 'text-slate-500'}`} />
          <span className="truncate">{item.nombre}</span>
        </span>
        {item.badge && (
          <span className="px-1.5 py-0.5 text-[10px] font-bold tracking-wider uppercase rounded bg-teal-500/20 text-teal-300 ring-1 ring-inset ring-teal-500/30">
            {item.badge}
          </span>
        )}
      </Link>
    );
  };

  return (
    <aside className="w-60 bg-slate-900 text-slate-100 flex flex-col h-screen fixed left-0 top-0 z-30 select-none">
      <div className="px-5 h-16 flex items-center gap-3 border-b border-slate-800/80">
        <div className="w-8 h-8 rounded-lg bg-teal-600 flex items-center justify-center text-white shadow-sm">
          <ShieldCheck className="w-4 h-4" />
        </div>
        <div className="leading-tight min-w-0">
          <h1 className="font-semibold text-sm text-white truncate">Vigía EPP</h1>
          <p className="text-xs text-slate-400 truncate">MTY-N01 · Planta InduSafe</p>
        </div>
      </div>

      <nav className="flex-1 py-3 px-3 space-y-0.5 overflow-y-auto">
        <p className="px-3 py-1 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
          Inspección en vivo
        </p>
        {ENTRADA.map(enlace)}
        <div className="my-3 border-t border-slate-800" />
        <p className="px-3 py-1 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
          Auditoría de turno
        </p>
        {NAVEGACION.map(enlace)}
      </nav>

      <div className="p-3 m-3 rounded-lg bg-slate-800/70 border border-slate-700/60 text-xs text-slate-300 space-y-1">
        <div className="font-semibold text-white">Regla de Planta (3 EPP)</div>
        <p className="text-[11px] text-slate-400 leading-relaxed">
          Obligatorios: <span className="text-teal-300 font-medium">Lentes</span>,{' '}
          <span className="text-teal-300 font-medium">Chaleco</span> y{' '}
          <span className="text-teal-300 font-medium">Guantes</span>.
        </p>
      </div>
    </aside>
  );
}
