import './globals.css';
import type { Metadata } from 'next';
import { Header } from '@/components/layout/Header';
import { getHallazgosData } from '@/lib/data/loader';

export const metadata: Metadata = {
  title: 'VIGÍA EPP // Centro de Comando de Torniquete y Seguridad Industrial',
  description:
    'Sistema SCADA de visión artificial con YOLO11 para control de acceso en torniquete: Lentes, Tapones Auditivos y Chaleco obligatorios + Guantes condicionales por puesto.',
};

export const dynamic = 'force-dynamic';

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { resumen } = await getHallazgosData();
  return (
    <html lang="es" className="h-full dark">
      <body className="min-h-screen bg-[#080c14] text-slate-100 antialiased font-sans flex flex-col">
        <Header
          fechaEscaneo={resumen.fecha_escaneo}
          disclaimer={resumen.disclaimer}
          riesgoDiario={resumen.dinero_en_riesgo_diario}
          incompletos={resumen.trabajadores_incompletos}
          cumplimientoPct={resumen.cumplimiento_turno_pct}
        />
        <main className="flex-1 px-4 sm:px-6 lg:px-8 py-6 max-w-[1440px] mx-auto w-full">
          {children}
        </main>
        <footer className="border-t border-slate-800/90 bg-[#060911] px-6 py-3 text-[11px] font-mono text-slate-400 flex flex-wrap items-center justify-between gap-3">
          <span>
            CASETA DE CONTROL PRE-TURNO · PLANTA MTY-N01 · YOLO11 ANATOMICAL ENGINE (4 ZONAS)
          </span>
          <span className="text-amber-400/90">
            OBLIGATORIO GENERAL: LENTES + TAPONES AUDITIVOS + CHALECO · CONDICIONAL POR PUESTO: GUANTES
          </span>
        </footer>
      </body>
    </html>
  );
}
