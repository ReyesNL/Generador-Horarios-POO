"""
Restricciones (naranja en el diagrama).

Restriccion es una clase ABSTRACTA con el método abstracto validar(). Cada
hija lo redefine con su propia regla. El generador y el validador reciben
una lista de restricciones y llaman validar() sin saber de qué tipo es cada
una (polimorfismo). Para agregar una regla nueva basta con crear otra hija:
no hay que tocar ni el generador ni el validador.

    prioridad 1 = obligatoria (si no se cumple, el horario es inválido)
    prioridad 2+ = deseable   (el generador intenta cumplirla; si no, es un aviso)
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from modelos.horario import SesionClase


class Restriccion(ABC):
    def __init__(self, id: int, tipo: str, descripcion: str, prioridad: int = 1):
        if prioridad < 1:
            raise ValueError("La prioridad empieza en 1 (obligatoria)")
        self.id = id
        self.tipo = tipo
        self.descripcion = descripcion
        self.prioridad = prioridad

    @property
    def es_obligatoria(self) -> bool:
        return self.prioridad == 1

    @abstractmethod
    def validar(self, sesion: SesionClase, sesiones: list[SesionClase]) -> str | None:
        """None si la sesión cumple la regla; si no, un texto que explica el problema.

        `sesiones` son las sesiones ya ubicadas (puede incluir a la propia sesión).
        """

    def __str__(self) -> str:
        nivel = "obligatoria" if self.es_obligatoria else "deseable"
        return f"[{self.tipo} | {nivel}] {self.descripcion}"


class RestriccionDisponibilidad(Restriccion):
    """Docente y aula disponibles en la franja, sin pasar la carga máxima del docente."""

    def __init__(self, id: int, prioridad: int = 1):
        super().__init__(id, "Disponibilidad",
                         "El docente y el aula deben estar disponibles en la franja", prioridad)

    def validar(self, sesion, sesiones):
        docente, aula, franja = sesion.docente, sesion.aula, sesion.franja
        if not docente.esta_disponible(franja):
            return f"{docente.nombre} no está disponible el {franja}"
        if not aula.verificar_disponibilidad(franja):
            return f"{aula.nombre} no está disponible el {franja}"
        horas = docente.calcular_carga_horaria(s for s in sesiones if s is not sesion) + franja.duracion_horas
        if horas > docente.carga_horaria_maxima:
            return f"{docente.nombre} superaría su carga máxima ({horas} h de {docente.carga_horaria_maxima} h)"
        return None


class RestriccionEspacio(Restriccion):
    """El espacio debe tener capacidad y ser del tipo que pide la sesión (aula o laboratorio)."""

    def __init__(self, id: int, prioridad: int = 1):
        super().__init__(id, "Espacio",
                         "El espacio debe tener capacidad suficiente y ser del tipo requerido", prioridad)

    def validar(self, sesion, sesiones):
        aula, curso = sesion.aula, sesion.curso
        if curso.numero_estudiantes > aula.capacidad:
            return (f"{aula.nombre} (capacidad {aula.capacidad}) no alcanza para "
                    f"{curso.numero_estudiantes} estudiantes del paralelo {curso.nombre}")
        if not aula.cumple_requisitos(curso.numero_estudiantes, sesion.especialidad_requerida):
            if sesion.requiere_laboratorio:
                return (f"{sesion.materia.nombre} necesita laboratorio de "
                        f"{sesion.especialidad_requerida} y {aula.nombre} no lo es")
            return f"{aula.nombre} es un laboratorio; la sesión teórica de {sesion.materia.nombre} va en aula"
        return None


class RestriccionCompatibilidadGrupos(Restriccion):
    """Un mismo paralelo, docente o aula no puede tener dos sesiones a la vez."""

    def __init__(self, id: int, prioridad: int = 1):
        super().__init__(id, "Cruce de horarios",
                         "Sin cruces de paralelo, docente o aula en la misma franja", prioridad)

    def validar(self, sesion, sesiones):
        for otra in sesiones:
            if otra is sesion or otra.franja != sesion.franja:
                continue
            if otra.curso is sesion.curso:
                return f"El paralelo {sesion.curso.nombre} tiene dos clases el {sesion.franja}"
            if otra.docente is sesion.docente:
                return f"{sesion.docente.nombre} tiene dos clases el {sesion.franja}"
            if otra.aula is sesion.aula:
                return f"{sesion.aula.nombre} está ocupada dos veces el {sesion.franja}"
        return None


class RestriccionDistribucionSemanal(Restriccion):
    """Deseable: las sesiones de una materia se reparten en días distintos."""

    def __init__(self, id: int, prioridad: int = 2):
        super().__init__(id, "Distribución semanal",
                         "Una materia no debería repetirse el mismo día en un paralelo", prioridad)

    def validar(self, sesion, sesiones):
        for otra in sesiones:
            if (otra is not sesion and otra.curso is sesion.curso and otra.materia is sesion.materia
                    and otra.franja.dia is sesion.franja.dia):
                return (f"{sesion.materia.nombre} se repite el {sesion.franja.dia.value} "
                        f"en el paralelo {sesion.curso.nombre}")
        return None
