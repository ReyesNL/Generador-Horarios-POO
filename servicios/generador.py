"""
GeneradorHorarios: arma automáticamente una propuesta de horario.

Algoritmo (búsqueda con retroceso o "backtracking"):
  1. Se calcula cada sesión que hay que ubicar: por cada paralelo (A y B) y
     cada materia, tantas sesiones como sesiones_semanales tenga. Cada una
     sabe si necesita aula o un laboratorio de cierta especialidad.
  2. Se ordenan de la más difícil a la más fácil (laboratorios primero,
     luego las materias con menos docentes habilitados).
  3. Para cada sesión se prueban combinaciones franja + docente + aula, en
     orden de preferencia: primero las que cumplen las reglas deseables, los
     días con menos clases para ese paralelo y las horas más tempranas.
     Así el horario sale ordenado y repartido en la semana.
  4. Una combinación se acepta solo si cumple TODAS las restricciones
     obligatorias. Si una sesión no tiene ninguna opción válida, se deshace
     la anterior y se prueba su siguiente opción.

Las restricciones no están escritas aquí dentro: se reciben en el
constructor (inyección de dependencias). El generador solo llama
restriccion.validar(), sin importar qué regla sea.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from modelos.academico import Carrera, CursoParalelo, Docente, Materia
from modelos.horario import Horario, SesionClase
from modelos.tiempo import Dia
from reglas.restricciones import Restriccion
from repositorios.catalogo import CatalogoAcademico


class GeneracionFallida(Exception):
    """No existe (o no se encontró a tiempo) un horario que cumpla las restricciones."""


@dataclass(frozen=True)
class RequerimientoSesion:
    materia: Materia
    curso: CursoParalelo
    especialidad: str | None      # None = aula convencional
    numero: int                   # 1..n dentro de la semana


@dataclass
class _Busqueda:
    """Estado de una ejecución de la búsqueda."""
    requerimientos: list[RequerimientoSesion]
    contexto: list[SesionClase]                     # sesiones de otros horarios + las ya ubicadas
    orden_dias: dict[Dia, int]
    azar: random.Random | None
    asignadas: list[SesionClase] = field(default_factory=list)
    docente_de: dict[tuple[str, str], Docente] = field(default_factory=dict)
    pasos: int = 0


class GeneradorHorarios:
    def __init__(self, catalogo: CatalogoAcademico, restricciones: list[Restriccion],
                 max_pasos: int = 200_000):
        self.catalogo = catalogo
        self.restricciones = list(restricciones)
        self.max_pasos = max_pasos

    @property
    def obligatorias(self) -> list[Restriccion]:
        return [r for r in self.restricciones if r.es_obligatoria]

    @property
    def deseables(self) -> list[Restriccion]:
        return [r for r in self.restricciones if not r.es_obligatoria]

    def generar_propuesta(self, carrera: Carrera, sesiones_ocupadas=(), semilla: int | None = None) -> Horario:
        """Crea un Horario nuevo para la carrera.

        sesiones_ocupadas: sesiones de otros horarios (sus aulas y docentes ya están tomados).
        semilla: None = propuesta ordenada y repetible; un número = otra propuesta válida.
        """
        requerimientos = self._requerimientos(carrera)
        self._verificar_recursos(carrera, requerimientos)

        dias = list(Dia)
        azar = None
        if semilla is not None:
            azar = random.Random(semilla)
            azar.shuffle(dias)
        busqueda = _Busqueda(requerimientos, list(sesiones_ocupadas),
                             {dia: i for i, dia in enumerate(dias)}, azar)

        if not self._asignar(busqueda, 0):
            raise GeneracionFallida(
                f"No existe una combinación que cumpla todas las restricciones para {carrera.nombre}. "
                "Revise la disponibilidad de docentes, aulas y laboratorios.")

        sesiones = sorted(busqueda.asignadas,
                          key=lambda s: (s.curso.nombre, s.franja.dia.orden, s.franja.hora_inicio))
        for numero, sesion in enumerate(sesiones, 1):
            sesion.id = numero
        return Horario(f"H-{carrera.id}", carrera, sesiones)

    def aplicar_restricciones(self, sesion: SesionClase, sesiones: list[SesionClase]) -> list[str]:
        """Problemas de la sesión frente a las restricciones obligatorias."""
        return sesion.validar_asignacion(self.obligatorias, sesiones)

    # ---- preparación ------------------------------------------------------
    def _requerimientos(self, carrera: Carrera) -> list[RequerimientoSesion]:
        requerimientos = [
            RequerimientoSesion(materia, curso, especialidad, numero)
            for curso in carrera.paralelos
            for materia in carrera.materias if materia.nivel == curso.nivel
            for numero, especialidad in enumerate(materia.definir_requisitos_espacio(), 1)
        ]
        docentes = self.catalogo.docentes_de(carrera.facultad)

        def dificultad(r: RequerimientoSesion):
            habilitados = sum(d.puede_dictar(r.materia) for d in docentes)
            return (r.especialidad is None, habilitados, r.materia.id, r.curso.nombre, r.numero)

        return sorted(requerimientos, key=dificultad)

    def _verificar_recursos(self, carrera: Carrera, requerimientos: list[RequerimientoSesion]) -> None:
        """Errores claros antes de buscar: materia sin docente o sesión sin espacio posible."""
        docentes = self.catalogo.docentes_de(carrera.facultad)
        aulas = self.catalogo.aulas_de(carrera.facultad)
        for r in requerimientos:
            if not any(d.puede_dictar(r.materia) for d in docentes):
                raise GeneracionFallida(f"Ningún docente de {carrera.facultad.nombre} está habilitado para {r.materia.nombre}.")
            if not any(a.cumple_requisitos(r.curso.numero_estudiantes, r.especialidad) for a in aulas):
                espacio = f"laboratorio de {r.especialidad}" if r.especialidad else "aula"
                raise GeneracionFallida(
                    f"No hay un {espacio} con capacidad para {r.curso.numero_estudiantes} estudiantes "
                    f"en {carrera.facultad.nombre} ({r.materia.nombre}).")

    # ---- búsqueda -----------------------------------------------------------
    def _asignar(self, b: _Busqueda, indice: int) -> bool:
        if indice == len(b.requerimientos):
            return True
        req = b.requerimientos[indice]
        clave = (req.curso.id, req.materia.id)
        for candidata in self._candidatas(b, req):
            b.pasos += 1
            if b.pasos > self.max_pasos:
                raise GeneracionFallida("La búsqueda tardó demasiado. Revise que las restricciones no sean imposibles de cumplir.")
            if self.aplicar_restricciones(candidata, b.contexto):
                continue
            docente_nuevo = clave not in b.docente_de
            if docente_nuevo:
                b.docente_de[clave] = candidata.docente
            b.asignadas.append(candidata)
            b.contexto.append(candidata)
            if self._asignar(b, indice + 1):
                return True
            b.asignadas.pop()                       # retroceso: se deshace y se prueba otra opción
            b.contexto.pop()
            if docente_nuevo:
                del b.docente_de[clave]
        return False

    def _candidatas(self, b: _Busqueda, req: RequerimientoSesion) -> list[SesionClase]:
        facultad = req.curso.carrera.facultad
        clave = (req.curso.id, req.materia.id)

        # Un mismo docente dicta todas las sesiones de una materia en un paralelo.
        if clave in b.docente_de:
            docentes = [b.docente_de[clave]]
        else:
            docentes = [d for d in self.catalogo.docentes_de(facultad) if d.puede_dictar(req.materia)]
            if b.azar:
                b.azar.shuffle(docentes)        # al regenerar, varía el orden entre docentes con igual carga
            docentes.sort(key=lambda d: d.calcular_carga_horaria(b.contexto))   # repartir la carga

        # El espacio más ajustado primero, para no gastar aulas grandes sin necesidad.
        aulas = sorted((a for a in self.catalogo.aulas_de(facultad)
                        if a.cumple_requisitos(req.curso.numero_estudiantes, req.especialidad)),
                       key=lambda a: a.capacidad)

        candidatas = [SesionClase(0, req.materia, docente, req.curso, aula, franja, req.especialidad)
                      for franja in self.catalogo.franjas
                      for docente in docentes
                      for aula in aulas]
        candidatas.sort(key=lambda s: self._preferencia(b, s))
        return candidatas

    def _preferencia(self, b: _Busqueda, sesion: SesionClase) -> tuple:
        """Menor = mejor. Ordena las opciones para que el horario salga compacto y repartido."""
        deseables_incumplidas = len(sesion.validar_asignacion(self.deseables, b.asignadas))
        clases_ese_dia = sum(1 for s in b.asignadas
                             if s.curso is sesion.curso and s.franja.dia is sesion.franja.dia)
        return (deseables_incumplidas, clases_ese_dia, sesion.franja.hora_inicio, b.orden_dias[sesion.franja.dia])
