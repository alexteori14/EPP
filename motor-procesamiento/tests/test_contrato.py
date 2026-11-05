from pathlib import Path
from motor import contrato


def test_clases_y_prendas_sin_casco_ni_mascarilla():
    assert contrato.PRENDAS == ("lentes", "chaleco", "guantes")
    assert "casco" not in contrato.CLASES
    assert "mascarilla" not in contrato.CLASES
    assert len(contrato.CLASES) == 7
    assert contrato.CLASES == (
        "persona",
        "chaleco",
        "sin_chaleco",
        "lentes",
        "sin_lentes",
        "guantes",
        "sin_guantes",
    )


def test_leer_turnos(tmp_path: Path):
    csv_file = tmp_path / "turnos.csv"
    csv_file.write_text(
        "posicion,linea,id_empleado,nombre,puesto,orden\n"
        "L1-T1,L1,EMP-101,Carlos Mendoza,Operador CNC,1\n",
        encoding="utf-8",
    )
    turnos = contrato.leer_turnos(csv_file)
    assert len(turnos) == 1
    assert turnos[0].posicion == "L1-T1"
    assert turnos[0].linea == "L1"
    assert turnos[0].id_empleado == "EMP-101"
    assert turnos[0].prendas_requeridas == ("lentes", "chaleco", "guantes")
