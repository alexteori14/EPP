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
  '¿A quiénes les faltan los lentes de seguridad y cuánto stock hay en caseta?',
  '¿A quiénes les faltan guantes anticorte o chaleco reflejante?',
  '¿Qué pasó en la estación con lectura dudosa y por qué tiene US$0.00 de impacto?',
];

export function AsistenteView({ data }: { data: SalidaHallazgos }) {
  const corridaId = data.resumen.analisis_id || 'demo';
  const [estado, setEstado] = useState<EstadoAsistente | null>(null);
  const [mensajes, setMensajes] = useState<MensajeChat[]>([
    {
      rol: 'asistente',
      texto: `Hola. Soy el asistente operativo de Vigía EPP para ${
        data.resumen.planta_nombre ?? 'la planta'
      }. Conozco las 12 estaciones del turno, los hallazgos de Lentes, Chaleco y Guantes, y el stock en caseta. ¿Qué deseas consultar?`,
    },
  ]);
  const [pregunta, setPregunta] = useState('');
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    estadoAsistente()
      .then(setEstado)
      .catch(() => setEstado({ configurado: true, gemini_activo: false, modelos: [], embeddings: '' }));
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
          titulo="Asistente Operativo RAG sobre la Corrida Activa"
        >
          Responde preguntas sobre trabajadores, estaciones, prendas faltantes (Lentes, Chaleco y
          Guantes) y stock en caseta citando los fragmentos verificables de la corrida.
        </TituloPagina>

        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-teal-50 border border-teal-200 text-xs font-semibold text-teal-800 shrink-0">
          <Sparkles className="w-3.5 h-3.5 text-teal-600" />
          {estado?.gemini_activo
            ? 'Motor RAG: Gemini + Fragmentos Verificados'
            : 'Motor RAG: Determinista Local Offline Activo'}
        </div>
      </div>

      {/* Botones de preguntas rápidas */}
      <section className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm space-y-2.5">
        <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          Preguntas frecuentes de supervisión pre-turno
        </div>
        <div className="flex flex-wrap gap-2">
          {PREGUNTAS_SUGERIDAS.map((q, i) => (
            <button
              key={i}
              type="button"
              data-testid={`sugerencia-chat-${i}`}
              onClick={() => enviarPregunta(q)}
              disabled={cargando}
              className="text-left text-xs px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-teal-50 hover:text-teal-800 text-slate-700 font-medium border border-slate-200/80 transition-colors"
            >
              {q}
            </button>
          ))}
        </div>
      </section>

      {/* Historial conversacional */}
      <section className="bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col min-h-[420px]">
        <div className="flex-1 p-6 space-y-5 overflow-y-auto max-h-[520px]">
          {mensajes.map((m, idx) => (
            <div
              key={idx}
              className={`flex items-start gap-3.5 ${
                m.rol === 'usuario' ? 'justify-end' : 'justify-start'
              }`}
            >
              {m.rol === 'asistente' && (
                <div className="w-8 h-8 rounded-lg bg-teal-600 text-white flex items-center justify-center shrink-0">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div
                data-testid={m.rol === 'asistente' ? `mensaje-asistente-${idx}` : undefined}
                className={`max-w-3xl rounded-2xl p-4 text-sm space-y-3 ${
                  m.rol === 'usuario'
                    ? 'bg-slate-900 text-white'
                    : 'bg-slate-50 border border-slate-200 text-slate-800'
                }`}
              >
                <div className="whitespace-pre-line leading-relaxed">{m.texto}</div>

                {m.fuentes && m.fuentes.length > 0 && (
                  <div className="pt-3 border-t border-slate-200/80 space-y-2">
                    <div className="inline-flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                      <BookOpen className="w-3.5 h-3.5 text-teal-600" />
                      Fuentes verificables de la corrida ({m.fuentes.length})
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {m.fuentes.map((f) => (
                        <div
                          key={f.id}
                          className="p-2.5 rounded-lg bg-white border border-slate-200 text-xs space-y-0.5"
                        >
                          <div className="font-mono font-bold text-teal-800">
                            [{f.id}] {f.titulo}
                          </div>
                          <p className="text-[11px] text-slate-600 line-clamp-2">{f.texto}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {m.rol === 'usuario' && (
                <div className="w-8 h-8 rounded-lg bg-slate-800 text-white flex items-center justify-center shrink-0">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          ))}

          {cargando && (
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <Loader2 className="w-4 h-4 animate-spin text-teal-600" />
              Consultando fragmentos de la corrida...
            </div>
          )}

          {error && (
            <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-700">
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
          className="p-4 border-t border-slate-200 bg-slate-50 rounded-b-xl flex items-center gap-3"
        >
          <input
            type="text"
            value={pregunta}
            onChange={(e) => setPregunta(e.target.value)}
            placeholder="Pregunta por una estación (ej. L1-T2), un trabajador o una prenda (Lentes, Chaleco, Guantes)..."
            className="flex-1 px-4 py-2.5 rounded-lg border border-slate-300 bg-white text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500"
          />
          <button
            type="submit"
            disabled={cargando || !pregunta.trim()}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white text-sm font-semibold transition-colors"
          >
            <Send className="w-4 h-4" />
            Preguntar
          </button>
        </form>
      </section>
    </div>
  );
}
