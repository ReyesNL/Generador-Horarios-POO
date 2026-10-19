"""
Datos de ejemplo para el primer avance.

Todavía no se conocen las materias reales de cada facultad, por eso cada
carrera usa el mismo plan genérico (Materia 1 a Materia 5). Basta con
cambiar este archivo para cargar datos reales; el resto del sistema no cambia.

    3 facultades · 1 carrera cada una · nivel 1 · paralelos A y B
    Cada facultad tiene aulas convencionales y sus propios laboratorios.
"""
from __future__ import annotations

from modelos.academico import Docente, Facultad, TipoMateria
from modelos.espacios import Aula, Laboratorio
from modelos.tiempo import Dia, JornadaAcademica
from modelos.usuarios import Administrador, DirectorCarrera, Usuario, UsuarioConsulta
from repositorios.catalogo import CatalogoAcademico

# Plan genérico de nivel 1: (número, sesiones semanales de 2 h, tipo)
PLAN_GENERICO = [
    (1, 2, TipoMateria.TEORICA),
    (2, 2, TipoMateria.TEORICA),
    (3, 3, TipoMateria.TEORICO_PRACTICA),      # 2 sesiones en aula + 1 en laboratorio
    (4, 2, TipoMateria.PRACTICA),              # todas en laboratorio
    (5, 2, TipoMateria.TEORICA),
]


def crear_catalogo_demo() -> CatalogoAcademico:
    catalogo = CatalogoAcademico()
    matutina = catalogo.agregar_jornada(JornadaAcademica("MAT", "Matutina", "07:00", "13:00"))
    vespertina = catalogo.agregar_jornada(JornadaAcademica("VES", "Vespertina", "14:00", "18:00"))
    matutina.crear_franjas()
    vespertina.crear_franjas()

    def franjas(dia: Dia, jornada: JornadaAcademica | None = None):
        return [f for f in catalogo.franjas if f.dia is dia and (jornada is None or f.jornada == jornada.nombre)]

    # ---------------------------------------------------------------- Informática
    fci = catalogo.agregar_facultad(Facultad("FCI", "Facultad de Ciencias Informáticas"))
    software = fci.agregar_carrera("SOF", "Ingeniería en Software")
    m = _agregar_plan(software, laboratorio_m3="Cómputo", laboratorio_m4="Cómputo")
    catalogo.agregar_aula(Aula("FCI-101", "Aula 101", 40, "FCI", ["proyector"]))
    catalogo.agregar_aula(Aula("FCI-102", "Aula 102", 40, "FCI", ["proyector"]))
    catalogo.agregar_aula(Laboratorio("FCI-LC1", "Lab. Cómputo 1", 35, "FCI", "Cómputo",
                                      ["35 computadoras", "proyector", "red"]))
    catalogo.agregar_aula(Laboratorio("FCI-LC2", "Lab. Cómputo 2", 35, "FCI", "Cómputo",
                                      ["35 computadoras", "pizarra digital"]))

    _docente(catalogo, "FCI-D1", "Ing. Pérez", fci, 20, m[1], m[3], funciones=["Docencia", "Investigación"])
    mora = _docente(catalogo, "FCI-D2", "Ing. Mora", fci, 20, m[2], m[4], funciones=["Docencia", "Vinculación"])
    zambrano = _docente(catalogo, "FCI-D3", "Ing. Zambrano", fci, 16, m[3], m[4], m[5])
    cedeno = _docente(catalogo, "FCI-D4", "Ing. Cedeño", fci, 20, m[1], m[2], m[5], funciones=["Docencia", "Gestión"])
    _no_disponible(mora, franjas(Dia.VIERNES))                       # viernes: vinculación
    for dia in Dia:
        _no_disponible(zambrano, franjas(dia, vespertina))           # solo trabaja en la mañana
    _no_disponible(cedeno, franjas(Dia.LUNES, matutina))             # lunes en la mañana: gestión

    # ---------------------------------------------------------------- Medicina
    fcm = catalogo.agregar_facultad(Facultad("FCM", "Facultad de Ciencias Médicas"))
    medicina = fcm.agregar_carrera("MED", "Medicina")
    m = _agregar_plan(medicina, laboratorio_m3="Anatomía", laboratorio_m4="Simulación clínica")
    catalogo.agregar_aula(Aula("FCM-201", "Aula M-201", 40, "FCM", ["proyector"]))
    catalogo.agregar_aula(Aula("FCM-202", "Aula M-202", 40, "FCM", ["proyector"]))
    catalogo.agregar_aula(Aula("FCM-SEM", "Sala de seminarios", 20, "FCM"))     # muy pequeña para un paralelo
    catalogo.agregar_aula(Laboratorio("FCM-LAN", "Lab. Anatomía", 35, "FCM", "Anatomía",
                                      ["mesas de disección", "modelos anatómicos"]))
    catalogo.agregar_aula(Laboratorio("FCM-LSC", "Lab. Simulación Clínica", 35, "FCM", "Simulación clínica",
                                      ["simuladores de paciente", "camillas"]))

    _docente(catalogo, "FCM-D1", "Dr. Vera", fcm, 20, m[1], m[2])
    loor = _docente(catalogo, "FCM-D2", "Dra. Loor", fcm, 20, m[3], m[4], funciones=["Docencia", "Investigación"])
    macias = _docente(catalogo, "FCM-D3", "Dr. Macías", fcm, 20, m[3], m[4], m[5])
    intriago = _docente(catalogo, "FCM-D4", "Dra. Intriago", fcm, 20, m[1], m[2], m[5])
    _no_disponible(loor, franjas(Dia.MARTES))                        # martes: práctica hospitalaria
    for dia in Dia:
        _no_disponible(macias, franjas(dia, matutina))               # solo trabaja en la tarde
    _no_disponible(intriago, franjas(Dia.JUEVES))

    # ---------------------------------------------------------------- Química
    fcq = catalogo.agregar_facultad(Facultad("FCQ", "Facultad de Ciencias Químicas"))
    quimica = fcq.agregar_carrera("QUI", "Química")
    m = _agregar_plan(quimica, laboratorio_m3="Química", laboratorio_m4="Química")
    catalogo.agregar_aula(Aula("FCQ-301", "Aula Q-301", 40, "FCQ", ["proyector"]))
    q302 = catalogo.agregar_aula(Aula("FCQ-302", "Aula Q-302", 40, "FCQ"))
    catalogo.agregar_aula(Laboratorio("FCQ-LQG", "Lab. Química General", 35, "FCQ", "Química",
                                      ["campana extractora", "balanzas", "reactivos"]))
    catalogo.agregar_aula(Laboratorio("FCQ-LQO", "Lab. Química Orgánica", 35, "FCQ", "Química",
                                      ["campana extractora", "rotavapor"]))
    for franja in franjas(Dia.MIERCOLES, vespertina):
        q302.registrar_no_disponible(franja)                         # miércoles en la tarde: mantenimiento

    _docente(catalogo, "FCQ-D1", "Q.F. Alcívar", fcq, 20, m[1], m[3])
    moreira = _docente(catalogo, "FCQ-D2", "Lic. Moreira", fcq, 20, m[2], m[4])
    _docente(catalogo, "FCQ-D3", "Q.F. Delgado", fcq, 20, m[3], m[4], m[5], funciones=["Docencia", "Investigación"])
    _docente(catalogo, "FCQ-D4", "Lic. Chávez", fcq, 20, m[1], m[2], m[5])
    _no_disponible(moreira, franjas(Dia.LUNES))

    return catalogo


def crear_usuarios_demo(catalogo: CatalogoAcademico) -> list[Usuario]:
    """Usuarios de prueba (las contraseñas se guardan como hash, nunca en texto plano)."""
    fci, fcm, fcq = catalogo.facultades
    return [
        Administrador("U1", "Administrador del sistema", "admin", "admin@academa.local", "admin123"),
        DirectorCarrera("U2", "Director de Software", "director.fci", "director.fci@academa.local",
                        "informatica123", fci),
        DirectorCarrera("U3", "Directora de Medicina", "director.fcm", "director.fcm@academa.local",
                        "medicina123", fcm),
        DirectorCarrera("U4", "Director de Química", "director.fcq", "director.fcq@academa.local",
                        "quimica123", fcq),
        UsuarioConsulta("U5", "Usuario de consulta", "consulta", "consulta@academa.local", "consulta123"),
    ]


# ---- ayudantes ----------------------------------------------------------------
def _agregar_plan(carrera, laboratorio_m3: str, laboratorio_m4: str) -> dict:
    """Crea Materia 1..5 y los paralelos A y B. Devuelve {número: materia}."""
    laboratorios = {3: laboratorio_m3, 4: laboratorio_m4}
    materias = {}
    for numero, sesiones, tipo in PLAN_GENERICO:
        materias[numero] = carrera.agregar_materia(
            f"{carrera.id}-M{numero}", f"Materia {numero}", nivel=1, sesiones_semanales=sesiones,
            tipo=tipo, especialidad_laboratorio=laboratorios.get(numero))
    carrera.agregar_paralelo("A", nivel=1, numero_estudiantes=32)
    carrera.agregar_paralelo("B", nivel=1, numero_estudiantes=30)
    return materias


def _docente(catalogo, id, nombre, facultad, carga_maxima, *materias, funciones=("Docencia",)) -> Docente:
    usuario = nombre.split()[-1].lower().translate(str.maketrans("áéíóúñ", "aeioun"))
    docente = Docente(id, nombre, cedula=f"{len(catalogo.docentes) + 1:010d}", email=f"{usuario}@academa.local",
                      facultad=facultad, carga_horaria_maxima=carga_maxima, funciones=funciones)
    docente.habilitar_materias(*materias)
    return catalogo.agregar_docente(docente)


def _no_disponible(docente: Docente, franjas) -> None:
    for franja in franjas:
        docente.registrar_disponibilidad(franja, disponible=False)
