import numpy as np
from motor.asociar import Deteccion
from motor.kiosco import evaluar_imagen


class DetectorFalso:
    def __init__(self, dets):
        self._dets = dets

    def detectar(self, imagenes):
        return [self._dets for _ in imagenes]


def test_kiosco_imagen_vacia_sin_persona():
    """Review Focus #3: una imagen sin personas devuelve estado_acceso == 'sin_persona' sin error."""
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    res = evaluar_imagen(img, detector=DetectorFalso([]))
    assert res["personas_detectadas"] == 0
    assert res["estado_acceso"] == "sin_persona"
    assert set(res["zonas"].keys()) == {"lentes", "chaleco", "guantes"}


def test_kiosco_trabajador_autorizado_3_de_3():
    img = np.full((600, 500, 3), 120, dtype=np.uint8)
    dets = [
        Deteccion("persona", 0.96, (80.0, 40.0, 420.0, 560.0)),
        Deteccion("lentes", 0.91, (180.0, 70.0, 310.0, 140.0)),
        Deteccion("chaleco", 0.94, (110.0, 180.0, 390.0, 400.0)),
        Deteccion("guantes", 0.89, (90.0, 360.0, 170.0, 480.0)),
    ]
    res = evaluar_imagen(img, detector=DetectorFalso(dets))
    assert res["personas_detectadas"] == 1
    assert res["estado_acceso"] == "autorizado"
    assert res["prendas_completas"] == 3
    assert res["prendas_requeridas"] == 3
    assert res["faltantes"] == []
    assert res["imagen_anotada_b64"].startswith("data:image/jpeg;base64,")


def test_kiosco_trabajador_bloqueado_por_falta_de_lentes():
    img = np.full((600, 500, 3), 120, dtype=np.uint8)
    dets = [
        Deteccion("persona", 0.95, (80.0, 40.0, 420.0, 560.0)),
        Deteccion("sin_lentes", 0.88, (180.0, 70.0, 310.0, 140.0)),
        Deteccion("chaleco", 0.93, (110.0, 180.0, 390.0, 400.0)),
        Deteccion("guantes", 0.90, (90.0, 360.0, 170.0, 480.0)),
    ]
    res = evaluar_imagen(img, detector=DetectorFalso(dets))
    assert res["estado_acceso"] == "bloqueado"
    assert res["faltantes"] == ["lentes"]
    assert res["zonas"]["lentes"]["estado"] == "falta"
    assert res["zonas"]["chaleco"]["estado"] == "ok"
    assert res["zonas"]["guantes"]["estado"] == "ok"
