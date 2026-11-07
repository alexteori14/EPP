'use client';

import React, { useEffect, useState } from 'react';
import { Bot, BookOpen, Loader2, Send, Sparkles, User } from 'lucide-react';
import { EstadoAsistente, MensajeChat } from '@/types/analisis';
import { SalidaHallazgos } from '@/types/hallazgos';
import { estadoAsistente, preguntarCorrida } from '@/lib/api/analisis';
import { ICONO_PANTALLA } from '@/components/iconos';
import { TituloPagina } from '@/components/layout/TituloPagina';

const PREGUNTAS_SUGERIDAS = [
  '¿Cuáles son los trabajadores con mayor riesgo diario en este turno y qué prendas les faltan?',
  '¿A quiénes les faltan los tapones auditivos de inserción o los lentes de seguridad?',
  '¿En qué puestos son opcionales los guantes y quiénes tienen guantes faltantes obligatorios?',
  '¿Qué pasó en la estación con lectura dudosa y por qué tiene US$0.00 de impacto?',
];

export function AsistenteView({ data }: { data: SalidaHallazgos }) {
  const corridaId = data.resumen.analisis_id || 'demo';
  const [estado, setEstado] = useState<EstadoAsistente | null>(null);
  const [mensajes, setMensajes] = useState<MensajeChat[]>([
    {
      rol: 'asistente',
      texto: `Consola RAG lista para ${
        data.resumen.planta_nombre ?? 'la planta'
      }. Conozco las 12 estaciones del turno, el estado de las 4 zonas anatómicas (Lentes, Tapones Auditivos, Chaleco y Guantes condicionales por puesto) y el stock en caseta. ¿Qué deseas consultar?`,
    },
  ]);
  const [pregunta, setPregunta] = useState('');
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    estadoAsistente()
      .then(setEstado)
      .catch(() =>
        setEstado({ configurado: true, gemini_activo: false, modelos: [], embeddings: '' })
      );
  }, []);

  const enviarPregunta = async (textoPregunta: string) => {
    const limpia = textoPregunta.trim();
    if (!limpia || cargando) return;
    const nuevoHistorial: MensajeChat[] = [...mensajes, { rol: 'usuario', texto: limpia }];
    setMensajes(nuevoHistorial);
    setPregunta('');
    setCargando(true);
    setError(null);
    try {
      const resp = await preguntarCorrida(corridaId, limpia, nuevoHistorial);
      setMensajes([
        ...nuevoHistorial,
        {
          rol: 'asistente',
          texto: resp.respuesta,
          fuentes: resp.fuentes,
          modo: resp.modo,
        },
      ]);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Error al consultar al asistente');
    } finally {
      setCargando(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <TituloPagina
          icono={ICONO_PANTALLA.asistente}
          titulo="Inspector IA RAG sobre la Corrida Activa"
        >
          Responde preguntas sobre trabajadores, estaciones, prendas faltantes (Lentes, Tapones
          Auditivos, Chaleco y Guantes según puesto) citando los fragmentos verificables de la
          corrida.
        </TituloPagina>

        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded bg-amber-500/15 border border-amber-500/40 text-xs font-mono font-bold text-amber-300 shrink-0">
          <Sparkles className="w-3.5 h-3.5 text-amber-400" />
          {estado?.gemini_activo
            ? 'MOTOR RAG: GEMINI + FRAGMENTOS VERIFICADOS'
            : 'MOTOR RAG: DETERMINISTA LOCAL OFFLINE ACTIVO'}
        </div>
      </div>

      {/* Botones de preguntas rápidas */}
      <section className="panel-caseta rounded-lg p-4 space-y-2.5">
        <div className="text-xs font-mono font-bold uppercase tracking-wider text-amber-400">
          CONSULTAS RÁPIDAS DE SUPERVISIÓN EN CASETA
        </div>
        <div className="flex flex-wrap gap-2">
          {PREGUNTAS_SUGERIDAS.map((q, i) => (
            <button
              key={i}
              type="button"
              data-testid={`sugerencia-chat-${i}`}
              onClick={() => enviarPregunta(q)}
              disabled={cargando}
              className="text-left text-xs px-3 py-1.5 rounded bg-slate-950 hover:bg-amber-500/15 hover:text-amber-300 text-slate-300 font-mono border border-slate-800 hover:border-amber-500/50 transition-colors"
            >
              {q}
            </button>
          ))}
        </div>
      </section>

      {/* Historial conversacional */}
      <section className="panel-caseta rounded-lg flex flex-col min-h-[420px]">
        <div className="flex-1 p-6 space-y-5 overflow-y-auto max-h-[520px]">
          {mensajes.map((m, idx) => (
            <div
              key={idx}
              className={`flex items-start gap-3.5 ${
                m.rol === 'usuario' ? 'justify-end' : 'justify-start'
              }`}
            >
              {m.rol === 'asistente' && (
                <div className="w-8 h-8 rounded bg-amber-500 text-slate-950 flex items-center justify-center shrink-0">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div
                data-testid={m.rol === 'asistente' ? `mensaje-asistente-${idx}` : undefined}
                className={`max-w-3xl rounded-lg p-4 text-sm space-y-3 ${
                  m.rol === 'usuario'
                    ? 'bg-amber-500 text-slate-950 font-semibold'
                    : 'bg-slate-950/90 border border-slate-800 text-slate-200'
                }`}
              >
                <div className="whitespace-pre-line leading-relaxed">{m.texto}</div>

                {m.fuentes && m.fuentes.length > 0 && (
                  <div className="pt-3 border-t border-slate-800 space-y-2">
                    <div className="inline-flex items-center gap-1.5 text-[11px] font-mono font-bold uppercase tracking-wider text-amber-400">
                      <BookOpen className="w-3.5 h-3.5" />
                      FUENTES VERIFICABLES DE LA CORRIDA ({m.fuentes.length})
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {m.fuentes.map((f) => (
                        <div
                          key={f.id}
                          className="p-2.5 rounded bg-slate-900 border border-slate-800 text-xs space-y-0.5"
                        >
                          <div className="font-mono font-bold text-amber-300">
                            [{f.id}] {f.titulo}
                          </div>
                          <p className="text-[11px] text-slate-400 line-clamp-2">{f.texto}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {m.rol === 'usuario' && (
                <div className="w-8 h-8 rounded bg-slate-800 text-white flex items-center justify-center shrink-0">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          ))}

          {cargando && (
            <div className="flex items-center gap-2 text-xs font-mono text-amber-300">
              <Loader2 className="w-4 h-4 animate-spin text-amber-400" />
              CONSULTANDO FRAGMENTOS DE LA CORRIDA...
            </div>
          )}

          {error && (
            <div className="p-3 rounded bg-rose-950/60 border border-rose-700 text-xs text-rose-200 font-mono">
              {error}
            </div>
          )}
        </div>

        {/* Caja de entrada */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            enviarPregunta(pregunta);
          }}
          className="p-4 border-t border-slate-800 bg-slate-950/90 rounded-b-lg flex items-center gap-3"
        >
          <input
            type="text"
            value={pregunta}
            onChange={(e) => setPregunta(e.target.value)}
            placeholder="Pregunta por una estación (ej. L1-T2), tapones auditivos, guantes opcionales o riesgo..."
            className="flex-1 px-4 py-2.5 rounded border border-slate-700 bg-slate-900 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-amber-500"
          />
          <button
            type="submit"
            disabled={cargando || !pregunta.trim()}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-slate-950 font-mono text-xs font-extrabold uppercase transition-colors"
          >
            <Send className="w-4 h-4" />
            CONSULTAR
          </button>
        </form>
      </section>
    </div>
  );
}
