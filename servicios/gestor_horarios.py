"""
GestorHorarios: coordina generar → validar → guardar → aprobar.

Recibe todas sus dependencias en el constructor (inyección de dependencias):
no crea su generador, su validador ni su repositorio, así que en las
pruebas se le pasa un repositorio en memoria y en la aplicación uno JSON.
"""
from __future__ import annotations

import random

from modelos.academico import Carrera
from modelos.horario import Conflicto, Horario
from modelos.usuarios import Usuario
from repositorios.catalogo import CatalogoAcademico
from repositorios.horarios import RepositorioHorarios
from servicios.generador import GeneradorHorarios
from servicios.validador import ValidadorHorarios


class GestorHorarios:
    def __init__(self, catalogo: CatalogoAcademico, generador: GeneradorHorarios,
                 validador: ValidadorHorarios, repositorio: RepositorioHorarios):
        self.catalogo = catalogo
        self.generador = generador
        self.validador = validador
        self.repositorio = repositorio

    # ---- consultas ----------------------------------------------------------
    def carreras_visibles(self, usuario: Usuario) -> list[Carrera]:
        return [c for c in self.catalogo.carreras if usuario.puede_ver(c)]

    def horario_de(self, carrera: Carrera) -> Horario | None:
        return self.repositorio.obtener(carrera.id)

    def conflictos(self, horario: Horario) -> list[Conflicto]:
        return self.validador.detectar_conflictos(horario, self._sesiones_de_otras(horario.carrera))

    # ---- generación ---------------------------------------------------------
    def generar(self, usuario: Usuario, carrera: Carrera, regenerar: bool = False) -> Horario:
        if not usuario.puede_generar():
            raise PermissionError("Solo el administrador puede generar horarios")
        semilla = random.randrange(1_000_000) if regenerar else None
        horario = self.generador.generar_propuesta(carrera, self._sesiones_de_otras(carrera), semilla)
        self.repositorio.guardar(horario)
        return horario

    def generar_todos(self, usuario: Usuario) -> list[Horario]:
        return [self.generar(usuario, carrera) for carrera in self.carreras_visibles(usuario)]

    # ---- aprobación ---------------------------------------------------------
    def aprobar(self, usuario: Usuario, horario: Horario, observacion: str = "") -> None:
        graves = [c for c in self.conflictos(horario) if c.es_grave]
        if graves:
            raise ValueError(f"No se puede aprobar: el horario tiene {len(graves)} conflicto(s) sin resolver")
        horario.aprobar(usuario, observacion)
        self.repositorio.guardar(horario)

    def rechazar(self, usuario: Usuario, horario: Horario, observacion: str) -> None:
        horario.rechazar(usuario, observacion)
        self.repositorio.guardar(horario)

    def _sesiones_de_otras(self, carrera: Carrera) -> list:
        return [s for h in self.repositorio.listar() if h.carrera is not carrera for s in h]
