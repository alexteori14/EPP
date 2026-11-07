import React from 'react';

const recorta = (pct: number) => (Number.isFinite(pct) ? Math.min(100, Math.max(0, pct)) : 0);

/** Barra de un ranking: crece desde la base en consola industrial oscura. */
export function Barra({
  pct,
  tono = 'bg-amber-500',
  className = '',
}: {
  pct: number;
  tono?: string;
  className?: string;
}) {
  const ancho = recorta(pct);
  return (
    <div className={`h-2.5 bg-slate-800/90 rounded overflow-hidden ${className}`} aria-hidden="true">
      {ancho > 0 && (
        <div
          className={`barra-crece h-full rounded-r ${tono}`}
          style={{ width: `max(${ancho}%, 3px)` }}
        />
      )}
    </div>
  );
}

/** Proporción sobre un total: riel oscuro de telemetría y barra de progreso activa. */
export function Proporcion({
  pct,
  tono = 'bg-amber-500',
  className = '',
}: {
  pct: number;
  tono?: string;
  className?: string;
}) {
  return (
    <div className={`h-2 rounded bg-slate-800 overflow-hidden ${className}`} aria-hidden="true">
      <div
        className={`h-full rounded transition-[width] duration-300 ease-out ${tono}`}
        style={{ width: `${recorta(pct)}%` }}
      />
    </div>
  );
}

export interface ParteApilada {
  clave: string;
  valor: number;
  tono: string;
}

/** Partes de un todo en una sola barra de estado de cuadrilla. */
export function BarraApilada({
  partes,
  className = '',
}: {
  partes: ParteApilada[];
  className?: string;
}) {
  const visibles = partes.filter((p) => p.valor > 0);
  if (visibles.length === 0) {
    return <div className={`h-3 rounded bg-slate-800 ${className}`} aria-hidden="true" />;
  }
  return (
    <div className={`flex h-3 gap-1 bg-slate-950 p-0.5 rounded border border-slate-800 ${className}`} aria-hidden="true">
      {visibles.map((p, i) => (
        <div
          key={p.clave}
          className={`h-full ${p.tono} ${i === 0 ? 'rounded-l-sm' : ''} ${
            i === visibles.length - 1 ? 'rounded-r-sm' : ''
          }`}
          style={{ flex: `${p.valor} 1 0%`, minWidth: 4 }}
        />
      ))}
    </div>
  );
}

/** Puntos LED de prendas requeridas completas (3 o 4 según el puesto). */
export function PuntosPrendas({ hay, esperados = 4 }: { hay: number; esperados?: number }) {
  return (
    <span className="inline-flex items-center gap-1" aria-hidden="true">
      {Array.from({ length: Math.max(hay, esperados) }, (_, i) => (
        <span
          key={i}
          className={`w-2.5 h-2.5 rounded-sm ${
            i < hay
              ? 'bg-emerald-400 shadow-[0_0_6px_rgba(16,185,129,0.7)]'
              : 'bg-rose-950 border border-rose-500'
          }`}
        />
      ))}
    </span>
  );
}
