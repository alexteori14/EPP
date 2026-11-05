import { EstadoPosicion, EstadoPrenda, PrendaEPP, TipoHallazgo } from '@/types/hallazgos';

/**
 * Diccionario de etiquetas humanas para los tipos de hallazgo de EPP.
 */
export const DICCIONARIO_HALLAZGOS: Record<TipoHallazgo, string> = {
  sin_lentes: 'Falta lentes de seguridad',
  sin_guantes: 'Faltan guantes anticorte',
  sin_chaleco: 'Falta chaleco reflejante',
  multiples_epp_faltantes: 'Faltan múltiples prendas de EPP',
  epp_agotado_en_caseta: 'Prenda agotada en caseta',
  revisar: 'Lectura dudosa: revisar en caseta',
};

export const DICCIONARIO_PRENDAS: Record<PrendaEPP, { nombre: string; norma: string; zona: string }> = {
  lentes: {
    nombre: 'Lentes de seguridad',
    norma: 'Policarbonato ANSI Z87.1',
    zona: 'Zona Ojos / Rostro (y: 0.00–0.32)',
  },
  chaleco: {
    nombre: 'Chaleco reflejante',
    norma: 'Alta Visibilidad Clase 2',
    zona: 'Zona Torso (y: 0.16–0.72)',
  },
  guantes: {
    nombre: 'Guantes anticorte',
    norma: 'Nitrilo Nivel A4',
    zona: 'Zona Manos / Muñecas (y: 0.28–0.96)',
  },
};

export const ORDEN_PRENDAS: PrendaEPP[] = ['lentes', 'chaleco', 'guantes'];

export const FAMILIAS_HALLAZGO: { id: string; nombre: string; tipos: TipoHallazgo[] }[] = [
  {
    id: 'multiples',
    nombre: 'Múltiples prendas omitidas (crítico)',
    tipos: ['multiples_epp_faltantes', 'epp_agotado_en_caseta'],
  },
  {
    id: 'ocular',
    nombre: 'Protección ocular (Lentes ANSI Z87.1)',
    tipos: ['sin_lentes'],
  },
  {
    id: 'manual',
    nombre: 'Protección manual (Guantes Nivel A4)',
    tipos: ['sin_guantes'],
  },
  {
    id: 'visibilidad',
    nombre: 'Alta visibilidad (Chaleco Clase 2)',
    tipos: ['sin_chaleco'],
  },
  {
    id: 'revisar',
    nombre: 'Lecturas dudosas (sin estimación de multa)',
    tipos: ['revisar'],
  },
];

export interface TotalFamilia {
  id: string;
  nombre: string;
  cantidad: number;
  monto: number;
}

export function totalesPorFamilia(
  hallazgos: { tipo: string; impacto_diario: number; corregido?: boolean }[]
): TotalFamilia[] {
  const totales = new Map<string, TotalFamilia>();
  for (const h of hallazgos) {
    if (h.corregido) continue;
    const f = FAMILIAS_HALLAZGO.find((fam) => (fam.tipos as string[]).includes(h.tipo)) ?? {
      id: 'otros',
      nombre: 'Otros incumplimientos',
    };
    const t = totales.get(f.id) ?? { id: f.id, nombre: f.nombre, cantidad: 0, monto: 0 };
    t.cantidad += 1;
    t.monto += h.impacto_diario || 0;
    totales.set(f.id, t);
  }
  return [...totales.values()].sort((a, b) => b.monto - a.monto || b.cantidad - a.cantidad);
}

export function traducirTipoHallazgo(tipo?: string | null): string {
  if (!tipo) return 'EPP Completo';
  if (tipo in DICCIONARIO_HALLAZGOS) {
    return DICCIONARIO_HALLAZGOS[tipo as TipoHallazgo];
  }
  return `Incidencia (${tipo})`;
}

export function traducirPrenda(prenda: PrendaEPP): string {
  return DICCIONARIO_PRENDAS[prenda]?.nombre ?? prenda;
}

export function traducirEstadoPosicion(estado: EstadoPosicion): string {
  switch (estado) {
    case 'ok':
      return 'EPP Completo (Autorizado)';
    case 'error':
      return 'Acceso Detenido (Falta EPP)';
    case 'revisar':
      return 'Revisar en caseta';
    default:
      return 'Desconocido';
  }
}

export function traducirEstadoPrenda(estado: EstadoPrenda): string {
  switch (estado) {
    case 'ok':
      return 'Puesto';
    case 'falta':
      return 'Falta';
    case 'dudoso':
      return 'Dudoso';
    default:
      return estado;
  }
}

export function formatearMoneda(monto: number | null | undefined, simbolo = 'US$'): string {
  if (monto === null || monto === undefined || isNaN(monto)) {
    return `${simbolo}0.00`;
  }
  const valorFormateado = new Intl.NumberFormat('es-MX', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(monto);
  return `${simbolo}${valorFormateado}`;
}

export function formatearMonedaUSD(monto: number | null | undefined): string {
  return formatearMoneda(monto, 'US$');
}

export function formatearNumero(numero: number | null | undefined): string {
  if (numero === null || numero === undefined || isNaN(numero)) {
    return '0';
  }
  return new Intl.NumberFormat('es-MX').format(numero);
}

export function ubicacionCorta(p: { codigo?: string; linea: number; posicion: number }): string {
  return p.codigo || `L${p.linea}-T${p.posicion}`;
}

export function ubicacionLarga(p: { codigo?: string; linea: number; posicion: number; puesto?: string }): string {
  const base = `Línea ${p.linea} · Estación ${p.posicion}`;
  return p.puesto ? `${base} (${p.puesto})` : base;
}

export function formatearTiempoVideo(segundos: number): string {
  const mins = Math.floor(segundos / 60);
  const secs = Math.floor(segundos % 60);
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}
