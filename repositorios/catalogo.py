"""Catálogo académico: datos de referencia (facultades, docentes, aulas y franjas)."""
from __future__ import annotations

from modelos.academico import Carrera, CursoParalelo, Docente, Facultad, Materia
from modelos.espacios import Aula
from modelos.tiempo import FranjaHoraria, JornadaAcademica


class CatalogoAcademico:
    def __init__(self):
        self.facultades: list[Facultad] = []
        self.docentes: list[Docente] = []
        self.aulas: list[Aula] = []
        self.jornadas: list[JornadaAcademica] = []

    def agregar_facultad(self, facultad: Facultad) -> Facultad:
        self.facultades.append(facultad)
        return facultad

    def agregar_docente(self, docente: Docente) -> Docente:
        self.docentes.append(docente)
        return docente

    def agregar_aula(self, aula: Aula) -> Aula:
        self.aulas.append(aula)
        return aula

    def agregar_jornada(self, jornada: JornadaAcademica) -> JornadaAcademica:
        self.jornadas.append(jornada)
        return jornada

    # ---- colecciones derivadas ----------------------------------------
    @property
    def carreras(self) -> list[Carrera]:
        return [c for f in self.facultades for c in f.listar_carreras()]

    @property
    def franjas(self) -> list[FranjaHoraria]:
        todas = [f for j in self.jornadas for f in j.franjas]
        return sorted(todas, key=lambda f: (f.dia.orden, f.hora_inicio))

    def docentes_de(self, facultad: Facultad) -> list[Docente]:
        return [d for d in self.docentes if d.facultad is facultad]

    def aulas_de(self, facultad: Facultad) -> list[Aula]:
        return [a for a in self.aulas if a.facultad_id == facultad.id]

    # ---- búsquedas por id (las usa el repositorio JSON) ---------------
    def carrera(self, id: str) -> Carrera | None:
        return _buscar(self.carreras, id)

    def materia(self, id: str) -> Materia | None:
        return _buscar([m for c in self.carreras for m in c.materias], id)

    def curso(self, id: str) -> CursoParalelo | None:
        return _buscar([p for c in self.carreras for p in c.paralelos], id)

    def docente(self, id: str) -> Docente | None:
        return _buscar(self.docentes, id)

    def aula(self, id: str) -> Aula | None:
        return _buscar(self.aulas, id)

    def franja(self, id: str) -> FranjaHoraria | None:
        return _buscar(self.franjas, id)


def _buscar(coleccion, id):
    return next((x for x in coleccion if x.id == id), None)
