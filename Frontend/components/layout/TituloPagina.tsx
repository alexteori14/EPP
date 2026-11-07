import React from 'react';
import type { LucideIcon } from 'lucide-react';

/** Encabezado técnico de módulo en el Centro de Comando Industrial Vigía EPP. */
export function TituloPagina({
  icono: Icono,
  titulo,
  children,
}: {
  icono: LucideIcon;
  titulo: React.ReactNode;
  children?: React.ReactNode;
}) {
  return (
    <div className="flex items-start gap-3.5">
      <span
        className="mt-0.5 w-10 h-10 rounded bg-amber-500/15 text-amber-400 border border-amber-500/40 flex items-center justify-center shrink-0 shadow-[0_0_15px_rgba(245,158,11,0.15)]"
        aria-hidden="true"
      >
        <Icono className="w-5 h-5" />
      </span>
      <div className="min-w-0">
        <div className="text-[10px] font-mono font-bold uppercase tracking-widest text-amber-400/90">
          CONSOLA DE SEGURIDAD INDUSTRIAL // NOM-017 & NOM-011 STPS
        </div>
        <h2 className="text-2xl font-extrabold text-white tracking-tight">{titulo}</h2>
        {children && <p className="text-slate-400 text-xs sm:text-sm mt-1">{children}</p>}
      </div>
    </div>
  );
}
