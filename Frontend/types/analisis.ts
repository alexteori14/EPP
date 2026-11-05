import { ResumenHallazgos } from './hallazgos';

export interface AnalisisMeta {
  id: string;
  nombre: string;
  creado: string;
  detector: string;
  status: 'procesando' | 'completado' | 'error';
  paso: string;
  pasoNumero: number;
  progreso: number;
  inicio?: number;
  resumen?: ResumenHallazgos;
  posiciones?: number;
  mensaje?: string;
  activo?: boolean;
}

export interface ListaAnalisis {
  analisis: AnalisisMeta[];
  activo: string | null;
  ocupado: boolean;
}

export interface FuenteChat {
  id: string;
  titulo: string;
  tipo: string;
  texto: string;
  codigo?: string;
  segundo?: number;
}

export interface MensajeChat {
  rol: 'usuario' | 'asistente';
  texto: string;
  fuentes?: FuenteChat[];
  modo?: string;
}

export interface RespuestaChat {
  respuesta: string;
  fuentes: FuenteChat[];
  modelo?: string;
  modo?: string;
}

export interface EstadoAsistente {
  configurado: boolean;
  gemini_activo: boolean;
  modelos: string[];
  embeddings: string;
}
