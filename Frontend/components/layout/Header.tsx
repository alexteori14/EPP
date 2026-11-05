'use client';

import React from 'react';
import { CalendarClock, FlaskConical, ShieldAlert } from 'lucide-react';

function formatearFechaEscaneo(fecha?: string): string | null {
  if (!fecha) return null;
  const d = new Date(fecha);
  if (isNaN(d.getTime())) return null;
  const dia = d.toLocaleDateString('es-MX', { day: '2-digit', month: '2-digit', year: 'numeric' });
  const hora = d.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit', hour12: false });
  return `${dia} ${hora} hrs`;
}

export function Header({
  fechaEscaneo,
  disclaimer = 'Filtro pre-turno · Datos reales de Kaggle + planta demostrativa InduSafe',
}: {
  fechaEscaneo?: string;
  disclaimer?: string;
}) {
  const fecha = formatearFechaEscaneo(fechaEscaneo);
  return (
    <header className="h-12 bg-white/90 backdrop-blur border-b border-slate-200 px-6 flex items-center justify-between gap-4 text-xs text-slate-500 sticky top-0 z-20">
      <div className="flex items-center gap-5 min-w-0">
        <span className="flex items-center gap-1.5 text-slate-600 truncate">
          <FlaskConical className="w-3.5 h-3.5 text-amber-600 shrink-0" aria-hidden />
          <span className="truncate">{disclaimer}</span>
        </span>
        {fecha && (
          <span className="hidden md:inline-flex items-center gap-1.5 shrink-0">
            <CalendarClock className="w-3.5 h-3.5 text-slate-400" aria-hidden />
            Escaneo {fecha}
          </span>
        )}
      </div>
      <div className="hidden lg:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 font-medium shrink-0">
        <ShieldAlert className="w-3.5 h-3.5 text-teal-600" aria-hidden />
        NOM-017-STPS · Lentes + Chaleco + Guantes
      </div>
    </header>
  );
}
