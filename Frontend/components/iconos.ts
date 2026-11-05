import {
  AlertTriangle,
  Bot,
  Camera,
  Factory,
  LayoutDashboard,
  Upload,
  Users,
  Video,
  type LucideIcon,
} from 'lucide-react';

export const ICONO_PANTALLA = {
  resumen: LayoutDashboard,
  kiosco: Camera,
  recorrido: Video,
  cuadrilla: Users,
  hallazgos: AlertTriangle,
  red: Factory,
  analizar: Upload,
  asistente: Bot,
} satisfies Record<string, LucideIcon>;
