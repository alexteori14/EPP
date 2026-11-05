import fs from 'fs';
import path from 'path';
import { SalidaHallazgos } from '@/types/hallazgos';
import { SalidaRed } from '@/types/red';
import { API_MOTOR_URL } from '@/lib/api/session';

/**
 * Obtiene los hallazgos del turno activo desde la API del motor (:8000) o, si no hay corrida
 * subida activa, desde public/salida/hallazgos.json.
 */
export async function getHallazgosData(): Promise<SalidaHallazgos> {
  try {
    const res = await fetch(`${API_MOTOR_URL}/analisis/activo`, {
      cache: 'no-store',
      signal: AbortSignal.timeout(1500),
    });
    if (res.ok) {
      return (await res.json()) as SalidaHallazgos;
    }
  } catch {
    // API apagada o usando recorrido demo
  }
  return getHallazgosDemo();
}

export function getHallazgosDemo(): SalidaHallazgos {
  try {
    const filePath = path.join(process.cwd(), 'public', 'salida', 'hallazgos.json');
    if (fs.existsSync(filePath)) {
      const content = fs.readFileSync(filePath, 'utf-8');
      return JSON.parse(content) as SalidaHallazgos;
    }
  } catch (error) {
    console.error('Error al leer public/salida/hallazgos.json:', error);
  }

  return {
    resumen: {
      total_problemas: 0,
      dinero_en_riesgo_diario: 0,
      dinero_recuperado_diario: 0,
      frase: '0 trabajadores sin EPP completo · US$0.00 al día en riesgo',
      trabajadores_incompletos: 0,
      epp_agotados: 0,
      lecturas_dudosas: 0,
      cumplimiento_turno_pct: 100,
      planta_id: 'MTY-N01',
      planta_nombre: 'Planta Monterrey Norte · Aceros & Logística InduSafe',
      turno_nombre: 'Turno Matutino 06:00',
      prendas_evaluadas: ['lentes', 'chaleco', 'guantes'],
      disclaimer: 'Filtro pre-turno · Datos reales de Kaggle + planta demostrativa InduSafe',
      moneda: 'US$',
    },
    posiciones: [],
    hallazgos: [],
  };
}

export async function getRedData(): Promise<SalidaRed> {
  try {
    const res = await fetch(`${API_MOTOR_URL}/analisis/activo/red`, {
      cache: 'no-store',
      signal: AbortSignal.timeout(1500),
    });
    if (res.ok) {
      return (await res.json()) as SalidaRed;
    }
  } catch {
    // Usar red demo
  }
  return getRedDemo();
}

export function getRedDemo(): SalidaRed {
  try {
    const filePath = path.join(process.cwd(), 'public', 'red.json');
    if (fs.existsSync(filePath)) {
      const content = fs.readFileSync(filePath, 'utf-8');
      return JSON.parse(content) as SalidaRed;
    }
  } catch (error) {
    console.error('Error al leer public/red.json:', error);
  }

  return {
    red: {
      plantas_total: 18,
      otras_plantas: 17,
      moneda: 'US$',
      medido_diario: 0,
      sistemico_diario: 0,
      local_diario: 0,
      problemas_sistemicos: 0,
      problemas_locales: 0,
      dias_mes: 30,
      supuestos_calculo: '',
      dataset_label: 'Filtro pre-turno · Datos reales de Kaggle + planta demostrativa InduSafe',
      fecha_corte: '2026-11-05',
      origen: 'recorrido_turno.mp4',
    },
    escenarios: [],
    sistemicos: [],
    locales: [],
  };
}
