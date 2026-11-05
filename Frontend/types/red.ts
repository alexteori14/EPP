import { PrendaEPP, TipoHallazgo } from './hallazgos';

export interface ResumenRed {
  plantas_total: number;
  otras_plantas: number;
  moneda: string;
  medido_diario: number;
  sistemico_diario: number;
  local_diario: number;
  problemas_sistemicos: number;
  problemas_locales: number;
  dias_mes: number;
  supuestos_calculo: string;
  dataset_label: string;
  fecha_corte: string;
  origen: string;
}

export interface EscenarioRed {
  id: 'bajo' | 'central' | 'alto' | 'peor_caso';
  etiqueta: string;
  fraccion: number;
  plantas: number;
  diario: number;
  mensual: number;
}

export interface HallazgoSistemicoRed {
  codigo: string;
  trabajador: string;
  puesto: string;
  tipo: TipoHallazgo;
  prendas_faltantes: PrendaEPP[];
  impacto_diario: number;
  peor_caso_diario: number;
}

export interface HallazgoLocalRed {
  tipo: TipoHallazgo;
  cantidad: number;
  impacto_diario: number;
}

export interface SalidaRed {
  red: ResumenRed;
  escenarios: EscenarioRed[];
  sistemicos: HallazgoSistemicoRed[];
  locales: HallazgoLocalRed[];
}
