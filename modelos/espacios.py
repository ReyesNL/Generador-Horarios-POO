"""
Espacios físicos (morado en el diagrama).

    Laboratorio ──▷ Aula   (herencia)

El laboratorio ES un aula con equipamiento especializado: reutiliza todo lo
del aula con super() y redefine cumple_requisitos() (polimorfismo). Quien
pregunta "¿esta aula sirve?" no necesita saber si es aula o laboratorio.
"""
from __future__ import annotations


class Aula:
    """Aula convencional: sirve para sesiones teóricas."""

    def __init__(self, id: str, nombre: str, capacidad: int, facultad_id: str,
                 caracteristicas: list[str] | None = None):
        self.id = id
        self.nombre = nombre
        self.capacidad = capacidad
        self.facultad_id = facultad_id
        self.caracteristicas = list(caracteristicas or [])
        self._franjas_no_disponibles: set[str] = set()     # DisponibilidadAula

    @property
    def tipo(self) -> str:
        return "Aula"

    @property
    def es_laboratorio(self) -> bool:
        return False

    def registrar_no_disponible(self, franja) -> None:
        """Bloquea una franja (mantenimiento, evento, préstamo a otra unidad...)."""
        self._franjas_no_disponibles.add(franja.id)

    def verificar_disponibilidad(self, franja) -> bool:
        return franja.id not in self._franjas_no_disponibles

    def cumple_requisitos(self, numero_estudiantes: int, especialidad: str | None) -> bool:
        """Un aula convencional solo recibe sesiones teóricas (sin especialidad)."""
        return especialidad is None and numero_estudiantes <= self.capacidad

    def __str__(self) -> str:
        return self.nombre


class Laboratorio(Aula):
    """Espacio para sesiones prácticas de una especialidad (Cómputo, Anatomía, Química...)."""

    def __init__(self, id: str, nombre: str, capacidad: int, facultad_id: str,
                 especialidad: str, equipamiento: list[str]):
        super().__init__(id, nombre, capacidad, facultad_id)
        self.especialidad = especialidad
        self.equipamiento = list(equipamiento)

    @property
    def tipo(self) -> str:
        return f"Laboratorio de {self.especialidad}"

    @property
    def es_laboratorio(self) -> bool:
        return True

    def verificar_equipamiento_requerido(self, especialidad: str | None) -> bool:
        return especialidad == self.especialidad

    def cumple_requisitos(self, numero_estudiantes: int, especialidad: str | None) -> bool:
        return (self.verificar_equipamiento_requerido(especialidad)
                and numero_estudiantes <= self.capacidad)
