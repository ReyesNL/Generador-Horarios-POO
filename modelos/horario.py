"""
Núcleo del horario (rojo en el diagrama).

    Horario ◆── SesionClase ──> Materia, Docente, CursoParalelo, Aula, FranjaHoraria
    Horario ─── Conflicto

Horario hereda de collections.abc.Collection: al implementar __iter__,
__len__ y __contains__ se puede recorrer con for, usar len() y el operador
"in", como cualquier colección de Python.
"""
from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from modelos.academico import Carrera, CursoParalelo, Docente, Materia
    from modelos.espacios import Aula
    from modelos.tiempo import FranjaHoraria
    from modelos.usuarios import Usuario
    from reglas.restricciones import Restriccion


class EstadoHorario(Enum):
    PENDIENTE = "Pendiente de aprobación"
    APROBADO = "Aprobado"
    RECHAZADO = "Rechazado"


@dataclass(eq=False)
class SesionClase:
    """Una clase concreta: qué materia, quién la dicta, a qué paralelo, dónde y cuándo."""

    id: int
    materia: Materia
    docente: Docente
    curso: CursoParalelo
    aula: Aula
    franja: FranjaHoraria
    especialidad_requerida: str | None = None    # None = sesión teórica

    @property
    def requiere_laboratorio(self) -> bool:
        return self.especialidad_requerida is not None

    def validar_asignacion(self, restricciones: Iterable[Restriccion],
                           sesiones: list[SesionClase]) -> list[str]:
        """Problemas que tiene esta sesión frente a cada restricción (lista vacía = válida)."""
        return [problema for r in restricciones if (problema := r.validar(self, sesiones))]

    def __str__(self) -> str:
        return (f"{self.materia.nombre} | {self.curso} | {self.docente.nombre} | "
                f"{self.aula.nombre} | {self.franja}")


@dataclass
class Conflicto:
    id: int
    tipo: str
    descripcion: str
    prioridad: int
    sesiones_involucradas: list[SesionClase] = field(default_factory=list)

    @property
    def es_grave(self) -> bool:
        return self.prioridad == 1

    def describir(self) -> str:
        nivel = "ERROR" if self.es_grave else "AVISO"
        return f"[{nivel}] {self.tipo}: {self.descripcion}"


class Horario(Collection):
    """Propuesta de horario de una carrera (sus paralelos A y B) y su estado de aprobación."""

    def __init__(self, id: str, carrera: Carrera, sesiones: Iterable[SesionClase] = (),
                 fecha_generacion: datetime | None = None):
        self.id = id
        self.carrera = carrera
        self.fecha_generacion = fecha_generacion or datetime.now()
        self.__sesiones = list(sesiones)
        self.__estado = EstadoHorario.PENDIENTE
        self.__revisado_por: str | None = None
        self.__fecha_revision: datetime | None = None
        self.__observacion = ""

    @classmethod
    def reconstruir(cls, id: str, carrera: Carrera, sesiones: Iterable[SesionClase],
                    fecha_generacion: datetime, estado: EstadoHorario, revisado_por: str | None = None,
                    fecha_revision: datetime | None = None, observacion: str = "") -> Horario:
        """Constructor alternativo: rearma un horario guardado (lo usan los repositorios)."""
        horario = cls(id, carrera, sesiones, fecha_generacion)
        horario.__estado = estado
        horario.__revisado_por = revisado_por
        horario.__fecha_revision = fecha_revision
        horario.__observacion = observacion
        return horario

    # ---- Collection ---------------------------------------------------
    def __iter__(self):
        return iter(self.__sesiones)

    def __len__(self) -> int:
        return len(self.__sesiones)

    def __contains__(self, sesion) -> bool:
        return sesion in self.__sesiones

    # ---- estado (solo lectura desde fuera) ----------------------------
    @property
    def estado(self) -> EstadoHorario:
        return self.__estado

    @property
    def revisado_por(self) -> str | None:
        return self.__revisado_por

    @property
    def fecha_revision(self) -> datetime | None:
        return self.__fecha_revision

    @property
    def observacion(self) -> str:
        return self.__observacion

    @property
    def editable(self) -> bool:
        return self.__estado is not EstadoHorario.APROBADO

    @property
    def horas_totales(self) -> int:
        return sum(s.franja.duracion_horas for s in self.__sesiones)

    # ---- modificación -------------------------------------------------
    def agregar_sesion(self, sesion: SesionClase) -> None:
        self._exigir_editable()
        self.__sesiones.append(sesion)

    def eliminar_sesion(self, sesion: SesionClase) -> None:
        self._exigir_editable()
        self.__sesiones.remove(sesion)

    def _exigir_editable(self) -> None:
        if not self.editable:
            raise PermissionError("Un horario aprobado no se puede modificar")

    # ---- consultas ----------------------------------------------------
    def sesiones_de(self, curso: CursoParalelo | None = None, docente: Docente | None = None,
                    aula: Aula | None = None, materia: Materia | None = None) -> list[SesionClase]:
        return [s for s in self.__sesiones
                if (curso is None or s.curso is curso)
                and (docente is None or s.docente is docente)
                and (aula is None or s.aula is aula)
                and (materia is None or s.materia is materia)]

    # ---- aprobación ---------------------------------------------------
    def aprobar(self, usuario: Usuario, observacion: str = "") -> None:
        self.__registrar_revision(usuario, EstadoHorario.APROBADO, observacion)

    def rechazar(self, usuario: Usuario, observacion: str) -> None:
        if not observacion.strip():
            raise ValueError("Indique el motivo del rechazo para que el administrador pueda corregirlo")
        self.__registrar_revision(usuario, EstadoHorario.RECHAZADO, observacion)

    def __registrar_revision(self, usuario: Usuario, estado: EstadoHorario, observacion: str) -> None:
        # El horario no pregunta "¿es director?": le pregunta al usuario si puede (polimorfismo).
        if not usuario.puede_aprobar(self):
            raise PermissionError(f"{usuario.nombre} no puede revisar el horario de {self.carrera.nombre}")
        self.__estado = estado
        self.__revisado_por = usuario.nombre
        self.__fecha_revision = datetime.now()
        self.__observacion = observacion.strip()
