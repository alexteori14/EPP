import numpy as np
from entrenamiento.preparar_epp import (
    clave_base_roboflow,
    mapear_etiqueta_linea,
    mapear_texto_anotacion,
)
from motor.asociar import Deteccion
from motor.detector import anotar_con_supervision, proveedores_aceleracion


def test_mapear_etiqueta_descarta_casco_y_mascarilla():
    nombres_ndomalau = ["helmet", "no_helmet", "no_vest", "person", "vest"]
    assert mapear_etiqueta_linea("0 0.5 0.5 0.2 0.2", nombres_ndomalau) is None  # helmet descartado
    assert mapear_etiqueta_linea("1 0.5 0.5 0.2 0.2", nombres_ndomalau) is None  # no_helmet descartado
    assert mapear_etiqueta_linea("3 0.5 0.5 0.4 0.8", nombres_ndomalau) == "0 0.5 0.5 0.4 0.8"  # person -> 0
    assert mapear_etiqueta_linea("4 0.5 0.5 0.3 0.4", nombres_ndomalau) == "1 0.5 0.5 0.3 0.4"  # vest -> 1
    assert mapear_etiqueta_linea("2 0.5 0.5 0.3 0.4", nombres_ndomalau) == "2 0.5 0.5 0.3 0.4"  # no_vest -> 2


def test_mapear_etiqueta_shlokraval_y_slimese():
    nombres_14 = [
        "Fall-Detected", "Gloves", "Goggles", "Hardhat", "Ladder", "Mask",
        "NO-Gloves", "NO-Goggles", "NO-Hardhat", "NO-Mask", "NO-Safety Vest",
        "Person", "Safety Cone", "Safety Vest",
    ]
    assert mapear_etiqueta_linea("2 0.5 0.2 0.1 0.1", nombres_14) == "3 0.5 0.2 0.1 0.1"  # Goggles -> 3
    assert mapear_etiqueta_linea("7 0.5 0.2 0.1 0.1", nombres_14) == "4 0.5 0.2 0.1 0.1"  # NO-Goggles -> 4
    assert mapear_etiqueta_linea("1 0.4 0.7 0.1 0.1", nombres_14) == "5 0.4 0.7 0.1 0.1"  # Gloves -> 5
    assert mapear_etiqueta_linea("6 0.4 0.7 0.1 0.1", nombres_14) == "6 0.4 0.7 0.1 0.1"  # NO-Gloves -> 6
    assert mapear_etiqueta_linea("5 0.5 0.2 0.1 0.1", nombres_14) is None                 # Mask descartado
    assert mapear_etiqueta_linea("3 0.5 0.2 0.1 0.1", nombres_14) is None                 # Hardhat descartado
    assert mapear_etiqueta_linea("8 0.5 0.2 0.1 0.1", nombres_14) is None                 # NO-Hardhat descartado
    assert mapear_etiqueta_linea("9 0.5 0.2 0.1 0.1", nombres_14) is None                 # NO-Mask descartado


def test_mapear_etiqueta_sh17_y_roboflow_tapones():
    nombres_sh17 = [
        "ear", "ear-mufs", "face", "face-guard", "face-mask", "foot",
        "glasses", "gloves", "hands", "head", "helmet", "medical-suit",
        "person", "safety-suit", "safety-vest", "shoes", "tool",
    ]
    assert mapear_etiqueta_linea("1 0.5 0.15 0.05 0.05", nombres_sh17) == "7 0.5 0.15 0.05 0.05"  # ear-mufs -> 7 (tapones)
    assert mapear_etiqueta_linea("0 0.5 0.15 0.04 0.04", nombres_sh17) == "8 0.5 0.15 0.04 0.04"  # ear -> 8 (sin_tapones)
    assert mapear_etiqueta_linea("10 0.5 0.1 0.2 0.2", nombres_sh17) is None                      # helmet descartado

    nombres_rf = ["earplugs", "no_earplugs", "BlueWhite", "GreenWhite", "OrangeWhite"]
    assert mapear_etiqueta_linea("0 0.4 0.2 0.04 0.04", nombres_rf) == "7 0.4 0.2 0.04 0.04"
    assert mapear_etiqueta_linea("1 0.4 0.2 0.04 0.04", nombres_rf) == "8 0.4 0.2 0.04 0.04"
    assert mapear_etiqueta_linea("2 0.4 0.2 0.04 0.04", nombres_rf) == "7 0.4 0.2 0.04 0.04"


def test_clave_base_roboflow_evita_fuga_entre_v1_y_v4():
    assert clave_base_roboflow("000005_jpg.rf.fc2bef6376.jpg") == "000005_jpg"
    assert clave_base_roboflow("000005_jpg.rf.aaaaaaaaaa.jpg") == "000005_jpg"
    assert clave_base_roboflow("img (105).jpg") == "img (105)"


def test_mapear_texto_anotacion_completo():
    nombres_14 = [
        "Fall-Detected", "Gloves", "Goggles", "Hardhat", "Ladder", "Mask",
        "NO-Gloves", "NO-Goggles", "NO-Hardhat", "NO-Mask", "NO-Safety Vest",
        "Person", "Safety Cone", "Safety Vest",
    ]
    raw = "11 0.5 0.5 0.5 0.9\n3 0.5 0.1 0.2 0.2\n2 0.5 0.2 0.1 0.1\n6 0.3 0.7 0.1 0.1\n"
    out, clases_vistas = mapear_texto_anotacion(raw, nombres_14)
    assert out.splitlines() == [
        "0 0.5 0.5 0.5 0.9",
        "3 0.5 0.2 0.1 0.1",
        "6 0.3 0.7 0.1 0.1",
    ]
    assert clases_vistas == {0, 3, 6}


def test_plugins_supervision_y_proveedores_aceleracion():
    info = proveedores_aceleracion()
    assert "onnxruntime_providers" in info
    assert info["onnxruntime_version"] is not None

    lienzo = np.zeros((120, 120, 3), dtype=np.uint8)
    dets = [Deteccion(clase="tapones", confianza=0.91, caja=(20.0, 20.0, 60.0, 60.0))]
    anotada = anotar_con_supervision(lienzo, dets)
    assert anotada.shape == (120, 120, 3)
    assert int(anotada.sum()) > 0
