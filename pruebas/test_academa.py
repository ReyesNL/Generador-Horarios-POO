"""
Pruebas automáticas del avance.

Ejecutar desde la carpeta Academa:
    python -m unittest discover -s pruebas -t .

Gracias a la inyección de dependencias, las pruebas usan un repositorio en
memoria: no tocan el archivo datos/horarios.json de la aplicación.
"""
import tempfile
import unittest
from collections.abc import Collection
from pathlib import Path

from main import construir_servicios
from modelos.academico import TipoMateria
from modelos.espacios import Aula, Laboratorio
from modelos.horario import EstadoHorario, SesionClase
from modelos.usuarios import Usuario
from reglas.restricciones import Restriccion
from repositorios.horarios import RepositorioHorarios, RepositorioHorariosJSON, RepositorioHorariosMemoria
from servicios.autenticacion import CredencialesInvalidas


class PruebaBase(unittest.TestCase):
    def setUp(self):
        self.autenticacion, self.gestor = construir_servicios(lambda _catalogo: RepositorioHorariosMemoria())
        self.catalogo = self.gestor.catalogo
        self.admin = self.autenticacion.iniciar_sesion("admin", "admin123")

    def usuario(self, nombre, contrasena):
        return self.autenticacion.iniciar_sesion(nombre, contrasena)

    def carrera(self, id):
        return self.catalogo.carrera(id)


class PruebasDeDiseno(PruebaBase):
    def test_clases_abstractas_no_se_pueden_instanciar(self):
        with self.assertRaises(TypeError):
            Restriccion(1, "Genérica", "No permitida")
        with self.assertRaises(TypeError):
            Usuario("X", "Nadie", "nadie", "x@x", "123456")
        with self.assertRaises(TypeError):
            RepositorioHorarios()

    def test_laboratorio_hereda_de_aula_y_redefine_requisitos(self):
        self.assertTrue(issubclass(Laboratorio, Aula))
        aula = Aula("A", "Aula", 40, "F")
        laboratorio = Laboratorio("L", "Lab", 30, "F", "Cómputo", ["pc"])
        self.assertTrue(aula.cumple_requisitos(30, None))
        self.assertFalse(aula.cumple_requisitos(30, "Cómputo"))
        self.assertTrue(laboratorio.cumple_requisitos(30, "Cómputo"))
        self.assertFalse(laboratorio.cumple_requisitos(30, "Química"))
        self.assertFalse(laboratorio.cumple_requisitos(31, "Cómputo"))

    def test_horario_es_una_coleccion(self):
        horario = self.gestor.generar(self.admin, self.carrera("SOF"))
        self.assertIsInstance(horario, Collection)
        primera = next(iter(horario))
        self.assertIn(primera, horario)
        self.assertEqual(len(horario), len(list(horario)))

    def test_materia_valida_sus_datos(self):
        software = self.carrera("SOF")
        with self.assertRaises(ValueError):
            software.agregar_materia("X1", "Sin sesiones", 1, 0)
        with self.assertRaises(ValueError):
            software.agregar_materia("X2", "Práctica sin laboratorio", 1, 2, TipoMateria.PRACTICA)


class PruebasDeDatos(PruebaBase):
    def test_tres_facultades_con_sus_laboratorios(self):
        self.assertEqual(len(self.catalogo.facultades), 3)
        for facultad in self.catalogo.facultades:
            laboratorios = [a for a in self.catalogo.aulas_de(facultad) if a.es_laboratorio]
            self.assertTrue(laboratorios, f"{facultad.nombre} no tiene laboratorios")

    def test_cada_carrera_tiene_materias_1_a_5(self):
        for carrera in self.catalogo.carreras:
            self.assertEqual([m.nombre for m in carrera.materias], [f"Materia {n}" for n in range(1, 6)])

    def test_solo_paralelos_a_y_b(self):
        for carrera in self.catalogo.carreras:
            self.assertEqual([p.nombre for p in carrera.paralelos], ["A", "B"])
        with self.assertRaises(ValueError):
            self.carrera("SOF").agregar_paralelo("C", 1, 30)


class PruebasDeGeneracion(PruebaBase):
    def setUp(self):
        super().setUp()
        self.horarios = self.gestor.generar_todos(self.admin)

    def test_genera_todas_las_sesiones_sin_conflictos(self):
        self.assertEqual(len(self.horarios), 3)
        for horario in self.horarios:
            esperadas = sum(m.sesiones_semanales for m in horario.carrera.materias) * 2   # paralelos A y B
            self.assertEqual(len(horario), esperadas)
            self.assertEqual(self.gestor.conflictos(horario), [], horario.carrera.nombre)

    def test_practicas_en_el_laboratorio_correcto_y_teoria_en_aula(self):
        for horario in self.horarios:
            for sesion in horario:
                if sesion.requiere_laboratorio:
                    self.assertTrue(sesion.aula.es_laboratorio, str(sesion))
                    self.assertEqual(sesion.aula.especialidad, sesion.especialidad_requerida)
                else:
                    self.assertFalse(sesion.aula.es_laboratorio, str(sesion))

    def test_respeta_la_disponibilidad_de_docentes_y_aulas(self):
        for horario in self.horarios:
            for sesion in horario:
                self.assertTrue(sesion.docente.esta_disponible(sesion.franja), str(sesion))
                self.assertTrue(sesion.aula.verificar_disponibilidad(sesion.franja), str(sesion))

    def test_un_docente_por_materia_en_cada_paralelo(self):
        for horario in self.horarios:
            for curso in horario.carrera.paralelos:
                for materia in horario.carrera.materias:
                    docentes = {s.docente for s in horario.sesiones_de(curso=curso, materia=materia)}
                    self.assertEqual(len(docentes), 1)

    def test_regenerar_da_otra_propuesta_valida(self):
        for _ in range(5):
            horario = self.gestor.generar(self.admin, self.carrera("MED"), regenerar=True)
            self.assertEqual(self.gestor.conflictos(horario), [])

    def test_el_validador_detecta_un_cruce(self):
        horario = self.gestor.horario_de(self.carrera("SOF"))
        original = next(iter(horario))
        otra_materia = next(m for m in horario.carrera.materias if m is not original.materia)
        cruce = SesionClase(999, otra_materia, original.docente, original.curso, original.aula, original.franja)
        horario.agregar_sesion(cruce)
        tipos = {c.tipo for c in self.gestor.conflictos(horario)}
        self.assertIn("Cruce de horarios", tipos)


class PruebasDeUsuarios(PruebaBase):
    def test_inicio_de_sesion(self):
        with self.assertRaises(CredencialesInvalidas):
            self.usuario("admin", "clave-equivocada")
        with self.assertRaises(CredencialesInvalidas):
            self.usuario("no.existe", "admin123")
        self.assertIs(self.usuario("  ADMIN ", "admin123"), self.admin)
        self.assertTrue(self.admin.sesion_activa)

    def test_la_contrasena_no_se_guarda_en_texto_plano(self):
        self.assertNotIn("admin123", [v for v in vars(self.admin).values() if isinstance(v, str)])

    def test_cambiar_contrasena(self):
        with self.assertRaises(PermissionError):
            self.admin.cambiar_contrasena("otra", "nueva123")
        self.admin.cambiar_contrasena("admin123", "nueva123")
        self.assertTrue(self.admin.verificar_contrasena("nueva123"))
        self.assertFalse(self.admin.verificar_contrasena("admin123"))

    def test_director_solo_ve_su_facultad(self):
        director = self.usuario("director.fcm", "medicina123")
        self.assertEqual([c.id for c in self.gestor.carreras_visibles(director)], ["MED"])
        self.assertEqual(len(self.gestor.carreras_visibles(self.admin)), 3)

    def test_solo_el_administrador_genera(self):
        director = self.usuario("director.fci", "informatica123")
        with self.assertRaises(PermissionError):
            self.gestor.generar(director, self.carrera("SOF"))


class PruebasDeAprobacion(PruebaBase):
    def setUp(self):
        super().setUp()
        self.horario = self.gestor.generar(self.admin, self.carrera("SOF"))

    def test_flujo_completo_de_aprobacion(self):
        consulta = self.usuario("consulta", "consulta123")
        self.assertFalse(consulta.puede_consultar(self.horario))

        with self.assertRaises(PermissionError):
            self.gestor.aprobar(self.admin, self.horario)                   # quien genera no aprueba
        with self.assertRaises(PermissionError):
            self.gestor.aprobar(self.usuario("director.fcq", "quimica123"), self.horario)   # otra facultad

        director = self.usuario("director.fci", "informatica123")
        self.gestor.aprobar(director, self.horario, "Todo en orden")
        self.assertIs(self.horario.estado, EstadoHorario.APROBADO)
        self.assertEqual(self.horario.revisado_por, director.nombre)
        self.assertTrue(consulta.puede_consultar(self.horario))
        self.assertFalse(director.puede_aprobar(self.horario))              # no se aprueba dos veces
        with self.assertRaises(PermissionError):
            self.horario.eliminar_sesion(next(iter(self.horario)))           # aprobado = bloqueado

    def test_rechazo_requiere_motivo(self):
        director = self.usuario("director.fci", "informatica123")
        with self.assertRaises(ValueError):
            self.gestor.rechazar(director, self.horario, "   ")
        self.gestor.rechazar(director, self.horario, "Mover Materia 4 al martes")
        self.assertIs(self.horario.estado, EstadoHorario.RECHAZADO)
        nuevo = self.gestor.generar(self.admin, self.carrera("SOF"), regenerar=True)
        self.assertIs(nuevo.estado, EstadoHorario.PENDIENTE)

    def test_no_se_aprueba_un_horario_con_conflictos(self):
        original = next(iter(self.horario))
        self.horario.agregar_sesion(SesionClase(999, original.materia, original.docente, original.curso,
                                                original.aula, original.franja))
        with self.assertRaises(ValueError):
            self.gestor.aprobar(self.usuario("director.fci", "informatica123"), self.horario)

    def test_el_repositorio_json_conserva_el_estado(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "horarios.json"
            repositorio = RepositorioHorariosJSON(ruta, self.catalogo)
            self.gestor.repositorio = repositorio
            horario = self.gestor.generar(self.admin, self.carrera("QUI"))
            self.gestor.aprobar(self.usuario("director.fcq", "quimica123"), horario, "Listo")

            recargado = RepositorioHorariosJSON(ruta, self.catalogo).obtener("QUI")
            self.assertIs(recargado.estado, EstadoHorario.APROBADO)
            self.assertEqual(recargado.observacion, "Listo")
            self.assertEqual([str(s) for s in recargado], [str(s) for s in horario])


if __name__ == "__main__":
    unittest.main()
