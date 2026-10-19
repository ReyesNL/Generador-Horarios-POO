"""
Estructura académica (azul en el diagrama).

    Facultad ◆── Carrera ◆── Materia
                         ◆── CursoParalelo
    Docente  (con su DisponibilidadDocente)

Composición: la parte la crea el todo. Facultad.agregar_carrera() crea la
Carrera y Carrera.agregar_materia() crea la Materia, así una carrera nunca
existe sin su facultad.
"""
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from modelos.horario import Horario, SesionClase
    from modelos.tiempo import FranjaHoraria


class TipoMateria(Enum):
    TEORICA = "Teórica"
    PRACTICA = "Práctica"
    TEORICO_PRACTICA = "Teórico-práctica"


class Facultad:
    def __init__(self, id: str, nombre: str):
        self.id = id
        self.nombre = nombre
        self.__carreras: list[Carrera] = []

    def agregar_carrera(self, id: str, nombre: str) -> Carrera:
        carrera = Carrera(id, nombre, self)
        self.__carreras.append(carrera)
        return carrera

    def listar_carreras(self) -> list[Carrera]:
        return list(self.__carreras)

    def __str__(self) -> str:
        return self.nombre


class Carrera:
    PARALELOS_PERMITIDOS = ("A", "B")      # en este avance solo se trabaja con 2 paralelos

    def __init__(self, id: str, nombre: str, facultad: Facultad):
        self.id = id
        self.nombre = nombre
        self.facultad = facultad
        self.__materias: list[Materia] = []
        self.__paralelos: list[CursoParalelo] = []

    @property
    def materias(self) -> tuple[Materia, ...]:
        return tuple(self.__materias)

    @property
    def paralelos(self) -> tuple[CursoParalelo, ...]:
        return tuple(self.__paralelos)

    def agregar_materia(self, id: str, nombre: str, nivel: int, sesiones_semanales: int,
                        tipo: TipoMateria = TipoMateria.TEORICA,
                        especialidad_laboratorio: str | None = None) -> Materia:
        materia = Materia(id, nombre, nivel, sesiones_semanales, tipo, self, especialidad_laboratorio)
        self.__materias.append(materia)
        return materia

    def agregar_paralelo(self, nombre: str, nivel: int, numero_estudiantes: int) -> CursoParalelo:
        if nombre not in self.PARALELOS_PERMITIDOS:
            raise ValueError(f"Paralelo '{nombre}' no permitido. Use: {', '.join(self.PARALELOS_PERMITIDOS)}")
        if any(p.nombre == nombre and p.nivel == nivel for p in self.__paralelos):
            raise ValueError(f"El paralelo {nombre} del nivel {nivel} ya existe en {self.nombre}")
        paralelo = CursoParalelo(f"{self.id}-N{nivel}{nombre}", nombre, nivel, numero_estudiantes, self)
        self.__paralelos.append(paralelo)
        return paralelo

    def __str__(self) -> str:
        return self.nombre


class Materia:
    def __init__(self, id: str, nombre: str, nivel: int, sesiones_semanales: int,
                 tipo: TipoMateria, carrera: Carrera, especialidad_laboratorio: str | None = None):
        if tipo is not TipoMateria.TEORICA and not especialidad_laboratorio:
            raise ValueError(f"{nombre}: una materia {tipo.value.lower()} necesita indicar su laboratorio")
        self.id = id
        self.nombre = nombre
        self.nivel = nivel
        self.tipo = tipo
        self.carrera = carrera
        self.especialidad_laboratorio = None if tipo is TipoMateria.TEORICA else especialidad_laboratorio
        self.sesiones_semanales = sesiones_semanales        # pasa por el setter (validación)

    @property
    def sesiones_semanales(self) -> int:
        return self.__sesiones_semanales

    @sesiones_semanales.setter
    def sesiones_semanales(self, valor: int) -> None:
        if not 1 <= valor <= 5:
            raise ValueError("Una materia debe tener entre 1 y 5 sesiones semanales")
        if self.tipo is TipoMateria.TEORICO_PRACTICA and valor < 2:
            raise ValueError("Una materia teórico-práctica necesita al menos 2 sesiones (teoría y práctica)")
        self.__sesiones_semanales = valor

    @property
    def requiere_laboratorio(self) -> bool:
        return self.tipo is not TipoMateria.TEORICA

    def definir_requisitos_espacio(self) -> list[str | None]:
        """Qué espacio necesita cada sesión de la semana.

        None = aula convencional; un texto = laboratorio de esa especialidad.
        Una materia teórico-práctica tiene 1 sesión práctica y el resto teóricas.
        """
        n = self.sesiones_semanales
        if self.tipo is TipoMateria.TEORICA:
            return [None] * n
        if self.tipo is TipoMateria.PRACTICA:
            return [self.especialidad_laboratorio] * n
        return [None] * (n - 1) + [self.especialidad_laboratorio]

    def __str__(self) -> str:
        return self.nombre


class CursoParalelo:
    def __init__(self, id: str, nombre: str, nivel: int, numero_estudiantes: int, carrera: Carrera):
        self.id = id
        self.nombre = nombre
        self.nivel = nivel
        self.carrera = carrera
        self.numero_estudiantes = numero_estudiantes

    @property
    def numero_estudiantes(self) -> int:
        return self.__numero_estudiantes

    @numero_estudiantes.setter
    def numero_estudiantes(self, valor: int) -> None:
        if valor <= 0:
            raise ValueError("Un paralelo debe tener al menos 1 estudiante")
        self.__numero_estudiantes = valor

    def consultar_horario(self, horario: Horario) -> list[SesionClase]:
        return horario.sesiones_de(curso=self)

    def __str__(self) -> str:
        return f"Nivel {self.nivel} - Paralelo {self.nombre}"


class Docente:
    def __init__(self, id: str, nombre: str, cedula: str, email: str, facultad: Facultad,
                 carga_horaria_maxima: int, funciones: Iterable[str] = ("Docencia",)):
        self.id = id
        self.nombre = nombre
        self.cedula = cedula
        self.email = email
        self.facultad = facultad
        self.carga_horaria_maxima = carga_horaria_maxima
        self.funciones = list(funciones)        # docencia, investigación, vinculación, gestión
        self.__materias_habilitadas: set[str] = set()
        self.__franjas_no_disponibles: set[str] = set()     # DisponibilidadDocente

    def habilitar_materias(self, *materias: Materia) -> None:
        self.__materias_habilitadas.update(m.id for m in materias)

    def puede_dictar(self, materia: Materia) -> bool:
        return materia.id in self.__materias_habilitadas

    def registrar_disponibilidad(self, franja: FranjaHoraria, disponible: bool) -> None:
        if disponible:
            self.__franjas_no_disponibles.discard(franja.id)
        else:
            self.__franjas_no_disponibles.add(franja.id)

    def esta_disponible(self, franja: FranjaHoraria) -> bool:
        return franja.id not in self.__franjas_no_disponibles

    def calcular_carga_horaria(self, sesiones: Iterable[SesionClase]) -> int:
        return sum(s.franja.duracion_horas for s in sesiones if s.docente is self)

    def consultar_horario(self, horario: Horario) -> list[SesionClase]:
        return horario.sesiones_de(docente=self)

    def __str__(self) -> str:
        return self.nombre
