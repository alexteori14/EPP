import {
  AnalisisMeta,
  EstadoAsistente,
  ListaAnalisis,
  MensajeChat,
  RespuestaChat,
} from '@/types/analisis';
import { RespuestaEnsayoJurado, SalidaHallazgos } from '@/types/hallazgos';
import { PresetKiosco, RespuestaKiosco } from '@/types/kiosco';

const BASE = '/motor/analisis';

export const EXTENSIONES_VIDEO = ['.mp4', '.mov', '.m4v', '.avi', '.mkv', '.webm'];
export const MAX_BYTES_VIDEO = 2 * 1024 ** 3;

async function pedir<T>(url: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(url, { cache: 'no-store', ...init });
  } catch {
    throw new Error('La API del motor no responde.');
  }
  const datos = await res.json().catch(() => null);
  if (!res.ok) {
    throw new Error(datos?.error || `La API del motor respondió ${res.status}.`);
  }
  return datos as T;
}

export const listarAnalisis = () => pedir<ListaAnalisis>(BASE);
export const consultarAnalisis = (id: string) => pedir<AnalisisMeta>(`${BASE}/${id}`);
export const activarAnalisis = (id: string | null) =>
  pedir<{ ok: boolean; activo: string | null }>(`${BASE}/${id ?? 'demo'}/activar`, { method: 'POST' });
export const borrarAnalisis = (id: string) => pedir<{ ok: boolean }>(`${BASE}/${id}`, { method: 'DELETE' });

/**
 * Persiste en disco la resolución ("Autorizar tras entrega") de un hallazgo de EPP.
 */
export const actualizarHallazgoCorregido = (
  corridaId: string,
  hallazgoId: string,
  corregido: boolean
) =>
  pedir<SalidaHallazgos>(`${BASE}/${corridaId}/hallazgos/${hallazgoId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ corregido }),
  });

/**
 * Modo Jurado en vivo: ejecuta la tarjeta con la API local o cae al ensayo precalculado en /ensayos/.
 */
export async function ejecutarTarjetaJurado(tarjeta: string): Promise<RespuestaEnsayoJurado> {
  try {
    return await pedir<RespuestaEnsayoJurado>('/motor/procesar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tarjeta }),
    });
  } catch {
    const res = await fetch(`/ensayos/${tarjeta}/resultado.json`, { cache: 'no-store' });
    if (!res.ok) {
      throw new Error(`No se encontró el ensayo ${tarjeta}`);
    }
    return (await res.json()) as RespuestaEnsayoJurado;
  }
}

/**
 * Kiosco de turno en vivo: evalúa un preset demostrativo o una foto capturada en base64.
 */
export const evaluarKioscoPreset = (preset: PresetKiosco) =>
  pedir<RespuestaKiosco>('/motor/kiosco/evaluar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ preset }),
  });

export const evaluarKioscoImagenB64 = (imagen_b64: string) =>
  pedir<RespuestaKiosco>('/motor/kiosco/evaluar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ imagen_b64 }),
  });

/** Asistente RAG sobre la corrida activa o "demo". */
export const preguntarCorrida = (id: string, pregunta: string, historial: MensajeChat[]) =>
  pedir<RespuestaChat>(`${BASE}/${id}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      pregunta,
      historial: historial.map(({ rol, texto }) => ({ rol, texto })),
    }),
  });

export const estadoAsistente = () => pedir<EstadoAsistente>('/motor/chat');

export function subirVideo(
  archivo: File,
  alAvanzar: (fraccion: number) => void
): Promise<AnalisisMeta> {
  const q = new URLSearchParams({ nombre: archivo.name });
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${BASE}?${q}`);
    xhr.setRequestHeader('Content-Type', archivo.type || 'application/octet-stream');
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) alAvanzar(e.loaded / e.total);
    };
    xhr.onload = () => {
      let datos: AnalisisMeta | { error?: string } | null = null;
      try {
        datos = JSON.parse(xhr.responseText);
      } catch {
        // sin JSON
      }
      if (xhr.status >= 200 && xhr.status < 300 && datos && 'id' in datos) {
        resolve(datos as AnalisisMeta);
      } else {
        const msg = datos && 'error' in datos && datos.error ? datos.error : `Error ${xhr.status}`;
        reject(new Error(msg));
      }
    };
    xhr.onerror = () => reject(new Error('La API del motor no responde.'));
    xhr.send(archivo);
  });
}
