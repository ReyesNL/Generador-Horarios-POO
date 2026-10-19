# ACADEMA · Primer avance

**Sistema Automatizado para la Planificación y Optimización de Horarios Académicos**
Programación Orientada a Objetos · ULEAM · Periodo 2026-2

Avance preliminar: genera automáticamente los horarios de 3 facultades, valida que no
tengan conflictos y permite que el director de carrera de cada facultad los apruebe o
rechace entrando al sistema con usuario y contraseña.

---

## Cómo ejecutarlo

Requisitos: **Python 3.10 o superior**. No usa librerías externas (Tkinter viene con Python).

```bash
python main.py
```

Si `python` no se reconoce en Windows, con uv también funciona: `uv run main.py`.

Pruebas automáticas (22 pruebas):

```bash
python -m unittest discover -s pruebas -t .
```

Los horarios se guardan en `datos/horarios.json`. Para empezar de cero, borre ese archivo.

## Usuarios de prueba

| Usuario        | Contraseña       | Rol                 | Qué puede hacer                                     |
|----------------|------------------|---------------------|-----------------------------------------------------|
| `admin`        | `admin123`       | Administrador       | Generar y regenerar los horarios de todas las facultades |
| `director.fci` | `informatica123` | Director de carrera | Aprobar o rechazar el horario de Ciencias Informáticas |
| `director.fcm` | `medicina123`    | Director de carrera | Aprobar o rechazar el horario de Ciencias Médicas |
| `director.fcq` | `quimica123`     | Director de carrera | Aprobar o rechazar el horario de Ciencias Químicas |
| `consulta`     | `consulta123`    | Consulta            | Ver solo los horarios ya aprobados                  |

Las contraseñas se guardan como hash (PBKDF2-SHA256 con sal), nunca en texto plano. Al aprobar
o rechazar, el sistema vuelve a pedir la contraseña a modo de firma.

## Guion de demostración

1. Entrar como `admin` → **Generar todos los horarios**. En menos de un segundo aparecen los
   3 horarios, ordenados de lunes a viernes, con la etiqueta *Pendiente de aprobación* y
   *✓ Sin conflictos*.
2. Cambiar la vista con **Ver horario de:** Paralelo A, Paralelo B, ambos paralelos, cada
   docente (sus franjas no disponibles salen en gris), cada aula o cada materia.
3. Cerrar sesión → entrar como `director.fci` → solo ve su facultad → **Aprobar horario**
   (observación opcional + contraseña). El horario queda *Aprobado* y bloqueado.
4. Entrar como `director.fcm` → **Rechazar** con un motivo. Luego entrar como `admin`: verá el
   motivo y podrá usar **Regenerar propuesta**, que vuelve a dejar el horario pendiente.
5. Entrar como `consulta` → solo puede ver el horario aprobado; los demás muestran un aviso.

## Datos del avance

Como todavía no se conocen las materias reales, todo se define en un solo archivo,
[`datos/semilla.py`](datos/semilla.py). Para cargar datos reales basta con cambiar ese archivo.

| Facultad                          | Carrera                | Laboratorios                                |
|-----------------------------------|------------------------|---------------------------------------------|
| Facultad de Ciencias Informáticas | Ingeniería en Software | Lab. Cómputo 1, Lab. Cómputo 2              |
| Facultad de Ciencias Médicas      | Medicina               | Lab. Anatomía, Lab. Simulación Clínica      |
| Facultad de Ciencias Químicas     | Química                | Lab. Química General, Lab. Química Orgánica |

- **Materias genéricas:** Materia 1 a Materia 5 en cada carrera (nivel 1). Hay teóricas (aula),
  una práctica (todas sus sesiones en laboratorio) y una teórico-práctica (2 sesiones en aula
  y 1 en laboratorio).
- **Solo 2 paralelos: A y B.** Están limitados en `Carrera.PARALELOS_PERMITIDOS`; si se intenta
  crear un paralelo "C", el sistema da un error.
- **Jornadas:** matutina (07:00-13:00) y vespertina (14:00-18:00), en bloques de 2 horas.
- **Restricciones de ejemplo:** docentes que no trabajan ciertos días o solo en la mañana o la
  tarde, carga horaria máxima, un aula en mantenimiento y una sala demasiado pequeña para un paralelo.

## Cómo se genera el horario

[`servicios/generador.py`](servicios/generador.py) usa búsqueda con retroceso (*backtracking*):

1. Calcula cada sesión que hay que ubicar: paralelo × materia × sesiones semanales.
2. Ubica primero las más difíciles (laboratorios y materias con pocos docentes habilitados).
3. Para cada sesión prueba combinaciones de franja, docente y aula, en orden de preferencia:
   primero las que cumplen las reglas deseables, después los días con menos clases y al final
   las horas más tempranas. Así el horario sale compacto y repartido en la semana.
4. Solo acepta una combinación que cumpla **todas** las restricciones obligatorias. Si una
   sesión no tiene opción, deshace la anterior y prueba otra.

| Restricción                       | Tipo        | Qué controla                                        |
|-----------------------------------|-------------|-----------------------------------------------------|
| `RestriccionDisponibilidad`       | Obligatoria | Docente y aula disponibles; carga máxima del docente |
| `RestriccionEspacio`              | Obligatoria | Capacidad; teoría en aula y práctica en el laboratorio de su especialidad |
| `RestriccionCompatibilidadGrupos` | Obligatoria | Sin cruces de paralelo, docente o aula              |
| `RestriccionDistribucionSemanal`  | Deseable    | Una materia no se repite el mismo día               |

## Estructura

```
Academa/
├── main.py                  Raíz de composición: crea los objetos y los inyecta
├── modelos/                 Clases del diagrama
│   ├── usuarios.py          Usuario (abstracta) → Administrador, DirectorCarrera, UsuarioConsulta
│   ├── academico.py         Facultad, Carrera, Materia, CursoParalelo, Docente
│   ├── espacios.py          Aula → Laboratorio
│   ├── tiempo.py            Dia, JornadaAcademica, FranjaHoraria
│   └── horario.py           Horario, SesionClase, Conflicto, EstadoHorario
├── reglas/restricciones.py  Restriccion (abstracta) y sus 4 hijas
├── servicios/               generador, validador, autenticación, gestor de horarios
├── repositorios/            catálogo académico y repositorios de horarios (memoria / JSON)
├── interfaz/                Ventanas Tkinter: login, panel, tabla del horario, diálogo de aprobación
├── datos/semilla.py         Facultades, materias, docentes, aulas y usuarios de ejemplo
└── pruebas/test_academa.py  Pruebas unitarias
```

## Conceptos de POO aplicados (links de referencia)

| Concepto | Fuente | Dónde está en el código |
|---|---|---|
| Clase abstracta con `ABC` y `@abstractmethod` | El Libro de Python: *Interfaces y ABC*; atareao: *Clases abstractas* | `Restriccion.validar()`, `Usuario`, `RepositorioHorarios`. Ninguna se puede instanciar (lo verifica una prueba) |
| Propiedad abstracta (`@property` + `@abstractmethod`) | El Libro de Python: *métodos abstractos* | `Usuario.rol`, `Usuario.alcance` |
| Interfaz formal | El Libro de Python; atareao: *Interfaces* | `RepositorioHorarios`: solo métodos abstractos, con 2 implementaciones intercambiables |
| ABC de colecciones (`collections.abc`) | El Libro de Python: *ABC y colecciones* | `Horario(Collection)`: se puede recorrer con `for`, usar `len()` y el operador `in` |
| Herencia y `super()` | El Libro de Python: *Herencia* | `Laboratorio(Aula)`, `DirectorCarrera(Usuario)`, las 4 restricciones, `RepositorioHorariosJSON(RepositorioHorariosMemoria)` |
| Modificar y extender métodos heredados | El Libro de Python: *Extendiendo y modificando métodos* | `Laboratorio.cumple_requisitos()` redefine el método; `UsuarioConsulta.puede_consultar()` y `RepositorioHorariosJSON.guardar()` lo extienden con `super()` |
| Polimorfismo | atareao: *Polimorfismo*; El Libro de Python | El generador y el validador llaman `restriccion.validar()` sin conocer el tipo; el panel pregunta `usuario.puede_aprobar()` y no "¿es director?" |
| Inyección de dependencias por constructor | PyWombat: *Dependency Injection* | `GestorHorarios(catalogo, generador, validador, repositorio)`, `GeneradorHorarios(catalogo, restricciones)`, `ServicioAutenticacion(usuarios)`. Todo se arma en `main.py` y las pruebas inyectan un repositorio en memoria |
| Alta cohesión y responsabilidad única | PyWombat; El Libro de Python: *Cohesión* | Cada servicio hace una sola cosa: generar, validar, autenticar o guardar. La interfaz no contiene lógica de horarios |
| Bajo acoplamiento | El Libro de Python: *Acoplamiento* | La lógica no importa Tkinter; el gestor depende de la interfaz del repositorio, no de JSON |
| Encapsulamiento (`__` y name mangling) | El Libro de Python: *Encapsulamiento* | `Usuario.__hash`, `Horario.__estado`, `Carrera.__materias` |
| `@property` con setter que valida | El Libro de Python: *Decorador property* | `Materia.sesiones_semanales`, `CursoParalelo.numero_estudiantes`; el estado del `Horario` es de solo lectura |
| `@classmethod` y `@staticmethod` | El Libro de Python: *Tipos de métodos* | `Horario.reconstruir()` (constructor alternativo), `Usuario._calcular_hash()` |
| Abstracción | El Libro de Python: *Abstracción* | La interfaz solo llama `gestor.generar()` y `gestor.aprobar()`, sin conocer el algoritmo |

> Las páginas *Métodos dunder* y *Sobreescribiendo métodos mágicos* de El Libro de Python aún
> dicen "Próximamente". De todas formas se usan `__str__`, `__iter__`, `__len__` y `__contains__`.

## Relación con el diagrama de clases

| Diagrama | Código | Nota |
|---|---|---|
| Usuario, Coordinador | `Usuario`, `DirectorCarrera` | Se agregaron `Administrador` y `UsuarioConsulta` |
| Facultad, Carrera, Materia, CursoParalelo, Docente | `modelos/academico.py` | Composición: la facultad crea sus carreras y la carrera sus materias y paralelos |
| Aula, Laboratorio | `modelos/espacios.py` | Herencia `Laboratorio → Aula` |
| JornadaAcademica, FranjaHoraria | `modelos/tiempo.py` | |
| DisponibilidadAula, DisponibilidadDocente | Conjuntos internos de `Aula` y `Docente` | `registrar_disponibilidad()`, `verificar_disponibilidad()` |
| SesionClase, Horario, Conflicto | `modelos/horario.py` | `Horario.generar()/regenerar()` se delegó a `GestorHorarios` (cohesión) |
| GeneradorHorarios, ValidadorHorarios | `servicios/` | `generar_propuesta()`, `aplicar_restricciones()`, `validar()`, `detectar_conflictos()` |
| Restriccion y sus 3 hijas | `reglas/restricciones.py` | Se agregó `RestriccionDistribucionSemanal` (deseable) |
| Tutoria | Pendiente | Próximo avance |

## Pendiente para los siguientes avances

- Tutorías y actividades adicionales de los docentes.
- Registrar y editar datos desde la interfaz (materias, docentes, aulas, disponibilidad).
- Mover sesiones a mano, con revalidación automática.
- Más niveles por carrera y las materias reales de cada facultad.
- Base de datos (por ejemplo SQLite) en lugar del archivo JSON.
- Exportar los horarios aprobados (PDF o Excel).
