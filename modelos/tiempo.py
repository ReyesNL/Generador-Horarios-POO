"""
Tiempo académico (amarillo en el diagrama).

    JornadaAcademica ◆── FranjaHoraria   (una jornada se compone de franjas)
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Dia(Enum):
    LUNES = "Lunes"
    MARTES = "Martes"
    MIERCOLES = "Miércoles"
    JUEVES = "Jueves"
    VIERNES = "Viernes"

    @property
    def orden(self) -> int:
        return list(Dia).index(self)


@dataclass(frozen=True)
class FranjaHoraria:
    """Bloque de tiempo de un día. Es inmutable (frozen) para poder usarla en sets y dicts."""

    id: str
    dia: Dia
    hora_inicio: str      # "07:00"
    hora_fin: str         # "09:00"
    jornada: str          # nombre de la jornada a la que pertenece

    @property
    def duracion_horas(self) -> int:
        return int(self.hora_fin[:2]) - int(self.hora_inicio[:2])

    @property
    def rango(self) -> str:
        return f"{self.hora_inicio} - {self.hora_fin}"

    def __str__(self) -> str:
        return f"{self.dia.value} {self.rango}"


class JornadaAcademica:
    """Matutina, vespertina... Divide su horario en franjas para cada día."""

    def __init__(self, id: str, nombre: str, hora_inicio: str, hora_fin: str):
        self.id = id
        self.nombre = nombre
        self.hora_inicio = hora_inicio
        self.hora_fin = hora_fin
        self.franjas: list[FranjaHoraria] = []

    def crear_franjas(self, dias=tuple(Dia), duracion_horas: int = 2) -> list[FranjaHoraria]:
        inicio, fin = int(self.hora_inicio[:2]), int(self.hora_fin[:2])
        for dia in dias:
            for hora in range(inicio, fin - duracion_horas + 1, duracion_horas):
                self.franjas.append(FranjaHoraria(
                    id=f"{dia.name[:3]}-{hora:02d}",
                    dia=dia,
                    hora_inicio=f"{hora:02d}:00",
                    hora_fin=f"{hora + duracion_horas:02d}:00",
                    jornada=self.nombre,
                ))
        return self.franjas
