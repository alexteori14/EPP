from motor.asociar import Deteccion, asociar_cuadro
from motor.rastreo import RastreadorTurno, votar_trabajador


def test_trabajador_epp_completo_4_zonas_ok():
    dets = [
        Deteccion("persona", 0.94, (100.0, 50.0, 400.0, 650.0)),
        Deteccion("lentes", 0.89, (190.0, 80.0, 290.0, 140.0)),     # zona cabeza/ojos
        Deteccion("tapones", 0.87, (175.0, 95.0, 305.0, 155.0)),    # zona oídos
        Deteccion("chaleco", 0.92, (130.0, 190.0, 370.0, 430.0)),   # zona torso
        Deteccion("guantes", 0.85, (110.0, 380.0, 180.0, 480.0)),   # zona manos
    ]
    personas = asociar_cuadro(dets, ancho=800, alto=700)
    assert len(personas) == 1
    p = personas[0]
    assert p.prendas["lentes"].estado == "ok"
    assert p.prendas["tapones"].estado == "ok"
    assert p.prendas["chaleco"].estado == "ok"
    assert p.prendas["guantes"].estado == "ok"


def test_trabajador_sin_lentes_sin_tapones_ni_guantes():
    dets = [
        Deteccion("persona", 0.95, (100.0, 50.0, 400.0, 650.0)),
        Deteccion("sin_lentes", 0.86, (190.0, 80.0, 290.0, 140.0)),
        Deteccion("sin_tapones", 0.84, (175.0, 95.0, 305.0, 155.0)),
        Deteccion("chaleco", 0.93, (130.0, 190.0, 370.0, 430.0)),
        Deteccion("sin_guantes", 0.84, (110.0, 380.0, 180.0, 480.0)),
    ]
    personas = asociar_cuadro(dets, ancho=800, alto=700)
    assert len(personas) == 1
    p = personas[0]
    assert p.prendas["lentes"].estado == "falta"
    assert p.prendas["tapones"].estado == "falta"
    assert p.prendas["chaleco"].estado == "ok"
    assert p.prendas["guantes"].estado == "falta"


def test_manos_cortadas_en_borde_inferior_sale_dudoso():
    """Review Focus #1: si la persona está cortada abajo (y2 >= alto * 0.98) y no se ven guantes, es dudoso."""
    dets = [
        Deteccion("persona", 0.92, (100.0, 100.0, 400.0, 698.0)),
        Deteccion("lentes", 0.88, (190.0, 120.0, 290.0, 180.0)),
        Deteccion("tapones", 0.86, (175.0, 130.0, 305.0, 190.0)),
        Deteccion("chaleco", 0.91, (130.0, 240.0, 370.0, 500.0)),
    ]
    personas = asociar_cuadro(dets, ancho=800, alto=700)
    assert len(personas) == 1
    assert personas[0].prendas["guantes"].estado == "dudoso"


def test_conflicto_positivo_y_negativo_cercanos_sale_dudoso():
    """Review Focus #2: si chaleco y sin_chaleco tienen confianza muy similar (<0.15), sale dudoso."""
    dets = [
        Deteccion("persona", 0.93, (100.0, 50.0, 400.0, 650.0)),
        Deteccion("chaleco", 0.62, (130.0, 190.0, 370.0, 430.0)),
        Deteccion("sin_chaleco", 0.58, (135.0, 195.0, 365.0, 425.0)),
        Deteccion("lentes", 0.90, (190.0, 80.0, 290.0, 140.0)),
        Deteccion("tapones", 0.88, (175.0, 95.0, 305.0, 155.0)),
        Deteccion("guantes", 0.88, (110.0, 380.0, 180.0, 480.0)),
    ]
    personas = asociar_cuadro(dets, ancho=800, alto=700)
    assert personas[0].prendas["chaleco"].estado == "dudoso"


def test_votacion_multicuadro_y_rastreo():
    dets_ok = [
        Deteccion("persona", 0.95, (100.0, 50.0, 400.0, 650.0)),
        Deteccion("lentes", 0.90, (190.0, 80.0, 290.0, 140.0)),
        Deteccion("tapones", 0.89, (175.0, 95.0, 305.0, 155.0)),
        Deteccion("chaleco", 0.92, (130.0, 190.0, 370.0, 430.0)),
        Deteccion("sin_guantes", 0.87, (110.0, 380.0, 180.0, 480.0)),
    ]
    rastreador = RastreadorTurno()
    for idx_cuadro in (10, 22, 34):
        vistas = asociar_cuadro(dets_ok, ancho=800, alto=700, cuadro=idx_cuadro)
        rastreador.actualizar(vistas, idx_cuadro)
    pistas = rastreador.pistas_ordenadas()
    assert len(pistas) == 1
    res = votar_trabajador(pistas[0].vistas)
    assert res["prendas"]["lentes"]["estado"] == "ok"
    assert res["prendas"]["tapones"]["estado"] == "ok"
    assert res["prendas"]["chaleco"]["estado"] == "ok"
    assert res["prendas"]["guantes"]["estado"] == "falta"
    assert res["prendas"]["guantes"]["lecturas"] == 3
