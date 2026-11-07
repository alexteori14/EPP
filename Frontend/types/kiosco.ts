import { PrendaEPP, EstadoPrenda } from './hallazgos';

export type PresetKiosco =
  | 'completo'
  | 'sin_lentes'
  | 'sin_tapones'
  | 'sin_guantes'
  | 'sin_chaleco'
  | 'incompleto_multiple';

export interface EvaluacionZonaKiosco {
  nombre: string;
  estado: EstadoPrenda;
  confianza: number;
  requerida?: boolean;
}

export interface RespuestaKiosco {
  personas_detectadas: number;
  estado_acceso: 'autorizado' | 'bloqueado' | 'revisar' | 'sin_persona';
  mensaje: string;
  prendas_completas: number;
  prendas_requeridas: number;
  requiere_guantes?: boolean;
  faltantes: PrendaEPP[];
  dudosas: PrendaEPP[];
  zonas: Record<PrendaEPP, EvaluacionZonaKiosco>;
  accion_caseta: string;
  ms_proceso: number;
  imagen_anotada_b64: string;
}
