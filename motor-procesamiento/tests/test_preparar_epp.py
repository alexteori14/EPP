from pathlib import Path
from entrenamiento.preparar_epp import (
    clave_base_roboflow,
    mapear_etiqueta_linea,
    mapear_texto_anotacion,
)


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
