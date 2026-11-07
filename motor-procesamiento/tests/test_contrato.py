from pathlib import Path
from motor import contrato


def test_clases_y_prendas_sin_casco_ni_mascarilla():
    assert contrato.PRENDAS == ("lentes", "tapones", "chaleco", "guantes")
    assert contrato.PRENDAS_GENERALES == ("lentes", "tapones", "chaleco")
    assert "casco" not in contrato.CLASES
    assert "mascarilla" not in contrato.CLASES
    assert len(contrato.CLASES) == 9
    assert contrato.CLASES == (
        "persona",
        "chaleco",
        "sin_chaleco",
        "lentes",
        "sin_lentes",
        "guantes",
        "sin_guantes",
        "tapones",
        "sin_tapones",
    )


def test_leer_turnos_y_guantes_opcionales_por_puesto(tmp_path: Path):
    csv_file = tmp_path / "turnos.csv"
    csv_file.write_text(
        "posicion,linea,id_empleado,nombre,puesto,orden\n"
        "L1-T1,L1,EMP-101,Carlos Mendoza,Operador de Corte CNC,1\n"
        "L3-T1,L3,EMP-301,Alejandro Cabrera,Inspector de Calidad,2\n",
        encoding="utf-8",
    )
    turnos = contrato.leer_turnos(csv_file)
    assert len(turnos) == 2
    assert turnos[0].posicion == "L1-T1"
    assert turnos[0].requiere_guantes is True
    assert turnos[0].prendas_requeridas == ("lentes", "tapones", "chaleco", "guantes")

    assert turnos[1].posicion == "L3-T1"
    assert turnos[1].requiere_guantes is False
    assert turnos[1].prendas_requeridas == ("lentes", "tapones", "chaleco")
    assert turnos[1].prendas_opcionales == ("guantes",)
