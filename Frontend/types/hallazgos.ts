export type PrendaEPP = 'lentes' | 'tapones' | 'chaleco' | 'guantes';

export type EstadoPrenda = 'ok' | 'falta' | 'dudoso';

export type EstadoPosicion = 'ok' | 'error' | 'revisar';

export type TipoHallazgo =
  | 'sin_lentes'
  | 'sin_tapones'
  | 'sin_guantes'
  | 'sin_chaleco'
  | 'multiples_epp_faltantes'
  | 'epp_faltante_agotado'
  | 'epp_agotado_en_caseta'
  | 'revisar';

export interface DetallePrendaPosicion {
  estado: EstadoPrenda;
  confianza: number;
  lecturas: number;
  stock_caseta: number;
  requerida?: boolean;
}

export interface PosicionTurno {
  id: string;
  codigo: string;
  linea: number;
  posicion: number;
  estado: EstadoPosicion;
  id_empleado: string;
  trabajador: string;
  puesto: string;
  requiere_guantes?: boolean;
  prendas_completas: number;
  prendas_requeridas: number;
  prendas: Record<PrendaEPP, DetallePrendaPosicion>;
  inventario_caseta: number;
  hallazgo_id: string | null;
  evidencia: string;
  evidencia_zona?: string;
  tipo?: TipoHallazgo;
  impacto_diario?: number;
  accion?: string;
}

export interface Hallazgo {
  id: string;
  tipo: TipoHallazgo;
  codigo: string;
  trabajador: string;
  id_empleado: string;
  puesto: string;
  requiere_guantes?: boolean;
  linea: number;
  posicion: number;
  prendas_faltantes: PrendaEPP[];
  prendas_completas: number;
  prendas_requeridas: number;
  impacto_diario: number;
  cuadro: number;
  segundo: number;
  descripcion: string;
  accion_sugerida: string;
  evidencia_crop: string;
  evidencia_persona?: string;
  corregido: boolean;
  confianza: number;
}

export interface ResumenHallazgos {
  total_problemas: number;
  dinero_en_riesgo_diario: number;
  dinero_recuperado_diario?: number;
  frase: string;
  trabajadores_incompletos: number;
  epp_agotados: number;
  lecturas_dudosas: number;
  cumplimiento_turno_pct: number;
  planta_id?: string;
  planta_nombre?: string;
  turno_nombre?: string;
  prendas_evaluadas?: PrendaEPP[];
  fecha_escaneo?: string;
  disclaimer: string;
  moneda?: string;
  video?: string;
  video_url?: string | null;
  segundos_proceso?: number;
  fps?: number;
  supuestos_calculo?: string;
  analisis_id?: string;
}

export interface SalidaHallazgos {
  resumen: ResumenHallazgos;
  posiciones: PosicionTurno[];
  hallazgos: Hallazgo[];
}

export interface RespuestaEnsayoJurado {
  status: 'inactivo' | 'procesando' | 'completado' | 'error';
  completado?: boolean;
  tarjeta?: string;
  paso?: string;
  pasoNumero?: number;
  progreso?: number;
  segundos?: number;
  segundos_proceso?: number;
  hallazgo_nuevo?: Hallazgo | null;
  hallazgos_nuevos?: Hallazgo[];
  mensaje?: string;
}
