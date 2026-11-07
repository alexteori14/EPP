import json
from pathlib import Path
from cruce import hallazgos, red, chat


def test_clasificar_y_calcular_impacto_diario():
    sistema = hallazgos.leer_sistema(Path("motor-procesamiento/datos/sistema"))
    t = sistema.turnos[0]

    # 1. Trabajador sin lentes (stock disponible en caseta -> local, US$420)
    obs_sin_lentes = {
        "posicion": "L1-T1",
        "persona_detectada": True,
        "confianza_persona": 0.95,
        "prendas": {
            "lentes": {"estado": "falta", "confianza": 0.91, "lecturas": 5},
            "tapones": {"estado": "ok", "confianza": 0.93, "lecturas": 5},
            "chaleco": {"estado": "ok", "confianza": 0.94, "lecturas": 5},
            "guantes": {"estado": "ok", "confianza": 0.92, "lecturas": 5},
        },
        "cuadro": 24,
        "recorte_persona": "recortes/L1-T1.jpg",
        "recorte_zona": "recortes/L1-T1_zona.jpg",
    }
    tipo = hallazgos.clasificar(obs_sin_lentes, t, sistema)
    assert tipo == "sin_lentes"
    imp = hallazgos.impacto_diario(tipo, obs_sin_lentes, t, sistema)
    assert imp == 420.0

    # 2. Trabajador sin lentes ni guantes (múltiples faltantes -> US$420 + US$340 = US$760)
    obs_multi = {
        "posicion": "L1-T1",
        "persona_detectada": True,
        "confianza_persona": 0.95,
        "prendas": {
            "lentes": {"estado": "falta", "confianza": 0.91, "lecturas": 5},
            "tapones": {"estado": "ok", "confianza": 0.93, "lecturas": 5},
            "chaleco": {"estado": "ok", "confianza": 0.94, "lecturas": 5},
            "guantes": {"estado": "falta", "confianza": 0.89, "lecturas": 5},
        },
        "cuadro": 24,
    }
    tipo_m = hallazgos.clasificar(obs_multi, t, sistema)
    assert tipo_m == "multiples_epp_faltantes"
    assert hallazgos.impacto_diario(tipo_m, obs_multi, t, sistema) == 760.0

    # 3. Lectura dudosa -> revisar, impacto US$0.00 (Principio de honestidad)
    obs_duda = {
        "posicion": "L1-T1",
        "persona_detectada": True,
        "confianza_persona": 0.90,
        "prendas": {
            "lentes": {"estado": "ok", "confianza": 0.91, "lecturas": 5},
            "tapones": {"estado": "ok", "confianza": 0.93, "lecturas": 5},
            "chaleco": {"estado": "ok", "confianza": 0.94, "lecturas": 5},
            "guantes": {"estado": "dudoso", "confianza": 0.45, "lecturas": 1},
        },
        "cuadro": 24,
    }
    tipo_d = hallazgos.clasificar(obs_duda, t, sistema)
    assert tipo_d == "revisar"
    assert hallazgos.impacto_diario(tipo_d, obs_duda, t, sistema) == 0.0

    # 4. Puesto con guantes opcionales (L3-T1 Inspector de Calidad): sin guantes -> autorizado (None)
    t_inspector = next(tr for tr in sistema.turnos if tr.posicion == "L3-T1")
    obs_sin_guantes_opcional = {
        "posicion": "L3-T1",
        "persona_detectada": True,
        "confianza_persona": 0.95,
        "prendas": {
            "lentes": {"estado": "ok", "confianza": 0.92, "lecturas": 5},
            "tapones": {"estado": "ok", "confianza": 0.91, "lecturas": 5},
            "chaleco": {"estado": "ok", "confianza": 0.94, "lecturas": 5},
            "guantes": {"estado": "falta", "confianza": 0.90, "lecturas": 5},
        },
        "cuadro": 150,
    }
    assert hallazgos.clasificar(obs_sin_guantes_opcional, t_inspector, sistema) is None
    assert hallazgos.impacto_diario(None, obs_sin_guantes_opcional, t_inspector, sistema) == 0.0


def test_persistencia_marcar_corregido(tmp_path: Path):
    """Review Focus #5: actualizar el estado corregido de un hallazgo persiste en disco y recalcula."""
    sistema = hallazgos.leer_sistema(Path("motor-procesamiento/datos/sistema"))
    datos = hallazgos.desde_carpeta(Path("motor-procesamiento/salida"), sistema)
    archivo = tmp_path / "hallazgos.json"
    archivo.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")

    primer_id = datos["hallazgos"][0]["id"]
    actualizado = hallazgos.actualizar_corregido(archivo, primer_id, True)
    assert actualizado is not None
    h_mod = next(h for h in actualizado["hallazgos"] if h["id"] == primer_id)
    assert h_mod["corregido"] is True

    releido = json.loads(archivo.read_text(encoding="utf-8"))
    assert next(h for h in releido["hallazgos"] if h["id"] == primer_id)["corregido"] is True


def test_red_proyeccion_plantas():
    sistema = hallazgos.leer_sistema(Path("motor-procesamiento/datos/sistema"))
    datos = hallazgos.desde_carpeta(Path("motor-procesamiento/salida"), sistema)
    datos_red = red.construir(datos)
    assert datos_red["red"]["plantas_total"] == 18
    assert len(datos_red["escenarios"]) == 4
    assert datos_red["red"]["medido_diario"] > 0


def test_chat_fragmentos_rag():
    fragmentos = chat.construir_fragmentos_corrida(Path("motor-procesamiento"))
    assert len(fragmentos) >= 5
    ids = {f.id for f in fragmentos}
    assert "resumen" in ids
    resp = chat.preguntar(Path("motor-procesamiento"), "demo", "¿Quién tiene el mayor riesgo?")
    assert resp["fuentes"]
    assert all("texto" in f and len(f["texto"]) > 0 for f in resp["fuentes"])
