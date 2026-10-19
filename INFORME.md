# Informe técnico del código · ACADEMA (primer avance)

**Proyecto:** Academa, Sistema Automatizado para la Planificación y Optimización de Horarios Académicos
**Asignatura:** Programación Orientada a Objetos · ULEAM · Periodo 2026-2
**Docente:** Ormaza Sabando Jharol Antonio
**Integrantes:** Carlos Antonio Reyes Carvajal, Leonardo Antonio Delgado Holguín, Aveiga Valencia Juan Pablo,
Jeremy Matthews Reyes Cedeño, Manuel Hernán Soledispa Chávez

Este informe explica las partes más importantes del código: qué hace cada una, por qué es
importante y qué concepto de POO aplica. Los fragmentos son extractos del código real
(algunos recortados con `...` para que se lean mejor).

---

## Índice

1. [Qué hace el avance](#1-qué-hace-el-avance)
2. [Arquitectura general](#2-arquitectura-general)
3. [main.py: la raíz de composición](#3-mainpy-la-raíz-de-composición)
4. [Las restricciones: el corazón de las reglas](#4-las-restricciones-el-corazón-de-las-reglas)
5. [El generador automático de horarios](#5-el-generador-automático-de-horarios)
6. [El validador de conflictos](#6-el-validador-de-conflictos)
7. [Usuarios, contraseñas y permisos](#7-usuarios-contraseñas-y-permisos)
8. [El Horario y su aprobación](#8-el-horario-y-su-aprobación)
9. [El gestor de horarios](#9-el-gestor-de-horarios)
10. [Repositorios: dónde se guardan los datos](#10-repositorios-dónde-se-guardan-los-datos)
11. [Modelos académicos y espacios](#11-modelos-académicos-y-espacios)
12. [La interfaz gráfica](#12-la-interfaz-gráfica)
13. [Flujo completo de uso](#13-flujo-completo-de-uso)
14. [Pruebas automáticas](#14-pruebas-automáticas)
15. [Limitaciones y siguientes pasos](#15-limitaciones-y-siguientes-pasos)

---

## 1. Qué hace el avance

- Maneja **3 facultades** (Ciencias Informáticas, Ciencias Médicas y Ciencias Químicas), con una
  carrera cada una.
- Cada carrera tiene **Materia 1 a Materia 5** (genéricas por ahora) y **solo 2 paralelos: A y B**.
- Cada facultad tiene **aulas convencionales y sus propios laboratorios** (Cómputo, Anatomía,
  Simulación Clínica, Química).
- El **administrador** genera los horarios automáticamente. El sistema ubica 22 sesiones por
  carrera (44 horas semanales), sin cruces, en unos 0.02 segundos.
- El **director de carrera** de cada facultad entra con usuario y contraseña, revisa el horario
  de su facultad y lo **aprueba o rechaza**.
- Un **usuario de consulta** solo puede ver los horarios ya aprobados.

---

## 2. Arquitectura general

El código está separado en capas. Cada capa solo conoce a la de abajo:

```
┌──────────────────────────────────────────────────────────────┐
│  interfaz/      Ventanas Tkinter (login, panel, tabla)       │  ← lo que ve el usuario
├──────────────────────────────────────────────────────────────┤
│  servicios/     GestorHorarios, GeneradorHorarios,           │  ← la lógica de la aplicación
│                 ValidadorHorarios, ServicioAutenticacion     │
├──────────────────────────────────────────────────────────────┤
│  modelos/       Usuario, Facultad, Carrera, Materia, Aula,   │  ← las clases del diagrama
│  reglas/        Horario, SesionClase... y las Restricciones  │
├──────────────────────────────────────────────────────────────┤
│  repositorios/  Catálogo académico y repositorios de horarios│  ← dónde viven los datos
└──────────────────────────────────────────────────────────────┘
        main.py crea todos los objetos y los conecta entre sí
```

**¿Por qué así?** Si mañana se cambia Tkinter por una página web, solo cambia `interfaz/`.
Si se cambia el archivo JSON por una base de datos, solo cambia `repositorios/`. La lógica de
horarios no se toca. Esto es **bajo acoplamiento** y **alta cohesión**: cada parte tiene una
sola responsabilidad y depende lo menos posible de las demás.

---

## 3. main.py: la raíz de composición

📄 [main.py](main.py)

**Qué hace:** es el único lugar donde se crean los objetos concretos y se "enchufan" unos en
otros. El resto del código recibe sus dependencias ya construidas.

```python
def construir_servicios(crear_repositorio=None):
    catalogo = crear_catalogo_demo()
    restricciones = crear_restricciones()
    if crear_repositorio is None:
        repositorio = RepositorioHorariosJSON(RUTA_HORARIOS, catalogo)
    else:
        repositorio = crear_repositorio(catalogo)
    gestor = GestorHorarios(catalogo,
                            GeneradorHorarios(catalogo, restricciones),
                            ValidadorHorarios(restricciones),
                            repositorio)
    autenticacion = ServicioAutenticacion(crear_usuarios_demo(catalogo))
    return autenticacion, gestor
```

**Por qué es importante:**

- Aplica **inyección de dependencias por constructor** (artículo de PyWombat). El
  `GestorHorarios` no crea su generador, su validador ni su repositorio: se los pasan.
- Gracias a eso, la aplicación usa un repositorio que guarda en JSON y **las pruebas usan uno en
  memoria** sin cambiar una sola línea del gestor:

```python
# en pruebas/test_academa.py
construir_servicios(lambda _catalogo: RepositorioHorariosMemoria())
```

- Las mismas `restricciones` se inyectan al generador y al validador, así que los dos aplican
  exactamente las mismas reglas.

---

## 4. Las restricciones: el corazón de las reglas

📄 [reglas/restricciones.py](reglas/restricciones.py)

**Qué hace:** define las reglas que debe cumplir cada sesión de clase. `Restriccion` es una
**clase abstracta**: no se puede instanciar y obliga a cada hija a implementar `validar()`.

```python
class Restriccion(ABC):
    def __init__(self, id, tipo, descripcion, prioridad=1):
        ...
        self.prioridad = prioridad

    @property
    def es_obligatoria(self) -> bool:
        return self.prioridad == 1

    @abstractmethod
    def validar(self, sesion, sesiones) -> str | None:
        """None si la sesión cumple la regla; si no, un texto que explica el problema."""
```

Cada hija redefine `validar()` con su propia regla:

| Clase | Prioridad | Regla |
|---|---|---|
| `RestriccionDisponibilidad` | 1 (obligatoria) | El docente y el aula están disponibles en esa franja y el docente no pasa su carga máxima |
| `RestriccionEspacio` | 1 (obligatoria) | El espacio tiene capacidad y es del tipo correcto (teoría en aula, práctica en el laboratorio de su especialidad) |
| `RestriccionCompatibilidadGrupos` | 1 (obligatoria) | Un mismo paralelo, docente o aula no tiene dos clases a la vez |
| `RestriccionDistribucionSemanal` | 2 (deseable) | Una materia no se repite el mismo día en un paralelo |

Ejemplo de una hija, la que evita los cruces:

```python
class RestriccionCompatibilidadGrupos(Restriccion):
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
```

**Por qué es importante:**

- Es el mejor ejemplo de **polimorfismo** del proyecto. El generador y el validador recorren una
  lista de restricciones y llaman `restriccion.validar()` sin saber de qué tipo es cada una.
- Para agregar una regla nueva (por ejemplo "no dar clases después de las 16:00") basta con
  crear otra hija de `Restriccion` y agregarla en `crear_restricciones()` de `main.py`. **No hay
  que tocar ni el generador ni el validador.**
- La **prioridad** separa las reglas que no se pueden romper (1) de las preferencias (2+).

---

## 5. El generador automático de horarios

📄 [servicios/generador.py](servicios/generador.py)

Es la parte más compleja del avance. Usa un algoritmo de **búsqueda con retroceso**
(*backtracking*), que funciona como armar un rompecabezas: se coloca una pieza; si más adelante
una pieza no entra, se quita la anterior y se prueba otra posición.

### 5.1 Paso 1: calcular qué sesiones hay que ubicar

```python
def _requerimientos(self, carrera):
    requerimientos = [
        RequerimientoSesion(materia, curso, especialidad, numero)
        for curso in carrera.paralelos
        for materia in carrera.materias if materia.nivel == curso.nivel
        for numero, especialidad in enumerate(materia.definir_requisitos_espacio(), 1)
    ]
    ...
    def dificultad(r):
        habilitados = sum(d.puede_dictar(r.materia) for d in docentes)
        return (r.especialidad is None, habilitados, r.materia.id, r.curso.nombre, r.numero)

    return sorted(requerimientos, key=dificultad)
```

- Por cada paralelo (A y B) y cada materia, crea tantas sesiones como `sesiones_semanales`
  tenga la materia. Cada sesión sabe si va en aula (`None`) o en un laboratorio de cierta
  especialidad.
- **Ordena de la más difícil a la más fácil:** primero las de laboratorio (hay pocos) y luego las
  materias con menos docentes habilitados. Ubicar primero lo difícil evita quedarse sin opciones
  al final.

### 5.2 Paso 2: la búsqueda con retroceso

```python
def _asignar(self, b, indice):
    if indice == len(b.requerimientos):
        return True                                   # ¡todas ubicadas!
    req = b.requerimientos[indice]
    clave = (req.curso.id, req.materia.id)
    for candidata in self._candidatas(b, req):
        ...
        if self.aplicar_restricciones(candidata, b.contexto):
            continue                                  # rompe una regla obligatoria: siguiente
        docente_nuevo = clave not in b.docente_de
        if docente_nuevo:
            b.docente_de[clave] = candidata.docente
        b.asignadas.append(candidata)
        b.contexto.append(candidata)
        if self._asignar(b, indice + 1):              # intenta ubicar la siguiente sesión
            return True
        b.asignadas.pop()                             # retroceso: se deshace y se prueba otra
        b.contexto.pop()
        if docente_nuevo:
            del b.docente_de[clave]
    return False
```

- La función es **recursiva**: ubica una sesión y se llama a sí misma para la siguiente.
- Si la siguiente no tiene ninguna opción válida, la llamada devuelve `False`. Entonces se quita
  la sesión actual (`pop()`) y se prueba su siguiente candidata.
- `docente_de` garantiza que **un mismo docente dicte todas las sesiones de una materia en un
  paralelo** (no tendría sentido que Materia 1 del paralelo A la den dos profesores distintos).
- Hay un límite de pasos (`max_pasos`). Si los datos son imposibles de cumplir, el sistema avisa
  con un mensaje claro en vez de quedarse colgado.

### 5.3 Paso 3: probar primero las mejores opciones

```python
def _preferencia(self, b, sesion):
    """Menor = mejor."""
    deseables_incumplidas = len(sesion.validar_asignacion(self.deseables, b.asignadas))
    clases_ese_dia = sum(1 for s in b.asignadas
                         if s.curso is sesion.curso and s.franja.dia is sesion.franja.dia)
    return (deseables_incumplidas, clases_ese_dia, sesion.franja.hora_inicio, b.orden_dias[sesion.franja.dia])
```

Las combinaciones franja + docente + aula se ordenan por esta tupla. Python compara tuplas
elemento por elemento, así que el criterio es:

1. Primero, las que **no rompen reglas deseables** (que la materia no se repita el mismo día).
2. Luego, el **día con menos clases** para ese paralelo, para repartir la semana.
3. Después, la **hora más temprana**, para que el horario salga compacto.
4. Por último, el orden de los días.

Esto es lo que hace que el horario salga **ordenado**: de lunes a viernes, empezando a las 07:00
y sin huecos innecesarios.

Además, en `_candidatas()`:

- Los docentes se ordenan por **carga horaria actual**, para repartir el trabajo.
- Las aulas se ordenan por **capacidad, de menor a mayor**, para no gastar un aula grande cuando
  basta una pequeña.

### 5.4 Generar y regenerar

```python
dias = list(Dia)
azar = None
if semilla is not None:
    azar = random.Random(semilla)
    azar.shuffle(dias)
```

- **Generar** (sin semilla) siempre da el mismo horario ordenado.
- **Regenerar** usa una semilla aleatoria que mezcla el orden de los días y de los docentes con
  igual carga. Así sale **otra propuesta distinta pero igual de válida**. Es útil cuando el
  director rechaza la primera.

---

## 6. El validador de conflictos

📄 [servicios/validador.py](servicios/validador.py)

**Qué hace:** revisa un horario completo y devuelve la lista de conflictos.

```python
def detectar_conflictos(self, horario, otras_sesiones=()):
    todas = list(horario) + list(otras_sesiones)
    conflictos = {}
    for sesion in horario:
        for restriccion in self.restricciones:
            problema = restriccion.validar(sesion, todas)       # polimorfismo
            if not problema:
                continue
            clave = (restriccion.tipo, problema)    # un cruce aparece en las dos sesiones: se une
            if clave not in conflictos:
                conflictos[clave] = Conflicto(len(conflictos) + 1, restriccion.tipo, problema,
                                              restriccion.prioridad)
            conflictos[clave].sesiones_involucradas.append(sesion)
    return sorted(conflictos.values(), key=lambda c: (c.prioridad, c.id))
```

**Por qué es importante:**

- El generador **construye** un horario válido; el validador lo **comprueba**. Es una segunda
  línea de defensa, sobre todo para cuando en el futuro se permita mover sesiones a mano.
- Un cruce entre dos sesiones se detecta dos veces (una desde cada sesión). El diccionario
  `conflictos` las **une en un solo conflicto** con las dos sesiones involucradas.
- `otras_sesiones` permite detectar choques con horarios de **otras carreras** que compartan
  aulas o docentes.
- En la interfaz se muestra como la etiqueta **✓ SIN CONFLICTOS**, o con un botón "Ver detalle"
  si hay problemas.

---

## 7. Usuarios, contraseñas y permisos

📄 [modelos/usuarios.py](modelos/usuarios.py) · [servicios/autenticacion.py](servicios/autenticacion.py)

### 7.1 Usuario es abstracta y cada rol responde a su manera

```python
class Usuario(ABC):
    @property
    @abstractmethod
    def rol(self) -> str: ...

    @abstractmethod
    def puede_generar(self) -> bool: ...

    @abstractmethod
    def puede_ver(self, carrera) -> bool: ...

    @abstractmethod
    def puede_aprobar(self, horario) -> bool: ...

    def puede_consultar(self, horario) -> bool:
        return self.puede_ver(horario.carrera)
```

| Pregunta | Administrador | DirectorCarrera | UsuarioConsulta |
|---|---|---|---|
| `puede_generar()` | Sí | No | No |
| `puede_ver(carrera)` | Todas | Solo las de su facultad | Todas |
| `puede_aprobar(horario)` | No | Sí, si es de su facultad y está pendiente | No |
| `puede_consultar(horario)` | Sí | Sí, de su facultad | Solo si está aprobado |

Ejemplo de herencia que **extiende** un método con `super()`:

```python
class UsuarioConsulta(Usuario):
    def puede_consultar(self, horario):
        return super().puede_consultar(horario) and horario.estado is EstadoHorario.APROBADO
```

**Por qué es importante:** la interfaz y el horario **nunca preguntan "¿es director?"**. Le
preguntan al usuario si puede hacer algo, y cada clase responde a su manera (polimorfismo). Si
se agrega un rol nuevo (por ejemplo "Decano"), basta con crear otra hija de `Usuario`.

Una decisión de diseño: **el administrador genera, pero no aprueba**. Así quien hace el horario
no es quien lo autoriza (separación de funciones).

### 7.2 Las contraseñas nunca se guardan en texto plano

```python
def __init__(self, id, nombre, nombre_usuario, email, contrasena):
    ...
    self.__sal = secrets.token_bytes(16)
    self.__hash = self._calcular_hash(contrasena, self.__sal)

@staticmethod
def _calcular_hash(contrasena, sal):
    return hashlib.pbkdf2_hmac("sha256", contrasena.encode("utf-8"), sal, Usuario.ITERACIONES_HASH)

def verificar_contrasena(self, contrasena):
    return hmac.compare_digest(self._calcular_hash(contrasena, self.__sal), self.__hash)
```

- Se guarda un **hash con sal** (PBKDF2-SHA256, 100 000 iteraciones), no la contraseña. Aunque
  alguien vea los datos del objeto, no puede leer la contraseña.
- `__hash` y `__sal` usan **doble guion bajo** (name mangling): Python los renombra a
  `_Usuario__hash` y quedan protegidos del acceso externo (**encapsulamiento**).
- `_calcular_hash` es un `@staticmethod` porque no necesita ni `self` ni `cls`.
- `hmac.compare_digest` compara en tiempo constante, una buena práctica de seguridad.

### 7.3 Inicio de sesión

```python
def iniciar_sesion(self, nombre_usuario, contrasena):
    usuario = self._usuarios.get(nombre_usuario.strip().lower())
    # Mismo mensaje si falla el usuario o la contraseña: no se revela qué usuarios existen.
    if usuario is None or not usuario.iniciar_sesion(contrasena):
        raise CredencialesInvalidas("Usuario o contraseña incorrectos")
    self._actual = usuario
    return usuario
```

Al aprobar o rechazar, se vuelve a pedir la contraseña con `confirmar_identidad()`, a modo de
**firma**.

---

## 8. El Horario y su aprobación

📄 [modelos/horario.py](modelos/horario.py)

### 8.1 Horario se comporta como una colección de Python

```python
class Horario(Collection):
    def __iter__(self):
        return iter(self.__sesiones)

    def __len__(self):
        return len(self.__sesiones)

    def __contains__(self, sesion):
        return sesion in self.__sesiones
```

Al heredar de `collections.abc.Collection` e implementar esos tres métodos, un horario se puede
usar como cualquier lista: `for sesion in horario`, `len(horario)` y `sesion in horario`. Esto
aplica la sección *ABC y colecciones* de El Libro de Python.

### 8.2 El estado está protegido

```python
@property
def estado(self) -> EstadoHorario:
    return self.__estado
```

`estado` es de **solo lectura**: no existe `horario.estado = ...`. La única forma de cambiarlo es
con `aprobar()` o `rechazar()`, que verifican los permisos:

```python
def rechazar(self, usuario, observacion):
    if not observacion.strip():
        raise ValueError("Indique el motivo del rechazo para que el administrador pueda corregirlo")
    self.__registrar_revision(usuario, EstadoHorario.RECHAZADO, observacion)

def __registrar_revision(self, usuario, estado, observacion):
    # El horario no pregunta "¿es director?": le pregunta al usuario si puede (polimorfismo).
    if not usuario.puede_aprobar(self):
        raise PermissionError(f"{usuario.nombre} no puede revisar el horario de {self.carrera.nombre}")
    self.__estado = estado
    self.__revisado_por = usuario.nombre
    self.__fecha_revision = datetime.now()
    self.__observacion = observacion.strip()
```

- Un horario **aprobado queda bloqueado**: `agregar_sesion()` y `eliminar_sesion()` lanzan
  `PermissionError`.
- Un rechazo **exige un motivo**, para que el administrador sepa qué corregir.

Estados posibles:

```
            generar / regenerar
                    │
                    ▼
           ┌─────────────────┐   aprobar (director)    ┌──────────┐
           │    PENDIENTE    │ ──────────────────────▶ │ APROBADO │ (bloqueado)
           └─────────────────┘                         └──────────┘
                    │ rechazar con motivo (director)
                    ▼
           ┌─────────────────┐
           │    RECHAZADO    │ ── regenerar (admin) ──▶ vuelve a PENDIENTE
           └─────────────────┘
```

### 8.3 Constructor alternativo con @classmethod

```python
@classmethod
def reconstruir(cls, id, carrera, sesiones, fecha_generacion, estado, ...):
    """Constructor alternativo: rearma un horario guardado (lo usan los repositorios)."""
    horario = cls(id, carrera, sesiones, fecha_generacion)
    horario.__estado = estado
    ...
    return horario
```

Cuando el repositorio lee el JSON necesita crear un horario que ya estaba aprobado. Como el
estado es privado, se usa un **constructor alternativo** dentro de la propia clase.

---

## 9. El gestor de horarios

📄 [servicios/gestor_horarios.py](servicios/gestor_horarios.py)

**Qué hace:** coordina todo el proceso. Es el único servicio que usa la interfaz.

```python
def generar(self, usuario, carrera, regenerar=False):
    if not usuario.puede_generar():
        raise PermissionError("Solo el administrador puede generar horarios")
    semilla = random.randrange(1_000_000) if regenerar else None
    horario = self.generador.generar_propuesta(carrera, self._sesiones_de_otras(carrera), semilla)
    self.repositorio.guardar(horario)
    return horario

def aprobar(self, usuario, horario, observacion=""):
    graves = [c for c in self.conflictos(horario) if c.es_grave]
    if graves:
        raise ValueError(f"No se puede aprobar: el horario tiene {len(graves)} conflicto(s) sin resolver")
    horario.aprobar(usuario, observacion)
    self.repositorio.guardar(horario)
```

**Puntos clave:**

- Verifica permisos **antes** de hacer cualquier cosa.
- Al generar una carrera, le pasa al generador las sesiones de **las otras carreras**
  (`_sesiones_de_otras`), para no reservar un aula o un docente que ya está ocupado.
- **No permite aprobar un horario que tenga conflictos graves**, aunque quien lo apruebe sea el
  director correcto.
- Después de cada cambio guarda en el repositorio, sin saber si es JSON o memoria.

---

## 10. Repositorios: dónde se guardan los datos

📄 [repositorios/horarios.py](repositorios/horarios.py) · [repositorios/catalogo.py](repositorios/catalogo.py)

### 10.1 Interfaz formal

```python
class RepositorioHorarios(ABC):
    @abstractmethod
    def guardar(self, horario): ...

    @abstractmethod
    def obtener(self, carrera_id): ...

    @abstractmethod
    def listar(self): ...
```

Es una **interfaz formal**: solo declara métodos, sin implementarlos. Hay dos implementaciones
intercambiables:

```
RepositorioHorarios (interfaz)
  └── RepositorioHorariosMemoria        → guarda en un diccionario (pruebas)
        └── RepositorioHorariosJSON     → además escribe en datos/horarios.json (aplicación)
```

`RepositorioHorariosJSON` **extiende** al de memoria con `super()`:

```python
def guardar(self, horario):
    super().guardar(horario)     # lo guarda en memoria (lógica heredada)
    self._escribir()             # y además lo escribe en disco
```

### 10.2 Escritura segura

```python
temporal = self.ruta.with_suffix(".tmp")
temporal.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
os.replace(temporal, self.ruta)     # reemplazo atómico: nunca queda un archivo a medias
```

Primero se escribe un archivo temporal y luego se reemplaza el original de una sola vez. Si el
programa se cierra a mitad de la escritura, el archivo anterior sigue intacto.

En el JSON se guardan **solo los id** (materia, docente, aula, franja). Al cargar, se buscan en
el catálogo. Si algún dato ya no existe (por ejemplo, se cambió la semilla), ese horario se
descarta con un aviso en vez de romper el programa.

---

## 11. Modelos académicos y espacios

📄 [modelos/academico.py](modelos/academico.py) · [modelos/espacios.py](modelos/espacios.py) · [modelos/tiempo.py](modelos/tiempo.py)

### 11.1 Composición: la parte la crea el todo

```python
class Facultad:
    def agregar_carrera(self, id, nombre) -> Carrera:
        carrera = Carrera(id, nombre, self)
        self.__carreras.append(carrera)
        return carrera
```

Igual que en el diagrama (rombo de composición), la facultad **crea** sus carreras y la carrera
crea sus materias y paralelos. Así una carrera nunca existe sin su facultad.

### 11.2 Solo paralelos A y B

```python
class Carrera:
    PARALELOS_PERMITIDOS = ("A", "B")      # en este avance solo se trabaja con 2 paralelos

    def agregar_paralelo(self, nombre, nivel, numero_estudiantes):
        if nombre not in self.PARALELOS_PERMITIDOS:
            raise ValueError(f"Paralelo '{nombre}' no permitido. ...")
```

El límite es un atributo de clase. Para permitir más paralelos en el futuro basta con cambiar
esa tupla.

### 11.3 Qué espacio necesita cada sesión

```python
def definir_requisitos_espacio(self) -> list[str | None]:
    n = self.sesiones_semanales
    if self.tipo is TipoMateria.TEORICA:
        return [None] * n                                   # todas en aula
    if self.tipo is TipoMateria.PRACTICA:
        return [self.especialidad_laboratorio] * n          # todas en laboratorio
    return [None] * (n - 1) + [self.especialidad_laboratorio]   # teórico-práctica
```

Por ejemplo, Materia 3 (teórico-práctica, 3 sesiones) devuelve `[None, None, "Cómputo"]`: dos
sesiones en aula y una en el laboratorio de Cómputo. Esto responde al caso del documento del
proyecto: *una materia puede requerir una sesión teórica en aula y otra práctica en laboratorio*.

### 11.4 Validación con @property y setter

```python
@property
def sesiones_semanales(self) -> int:
    return self.__sesiones_semanales

@sesiones_semanales.setter
def sesiones_semanales(self, valor: int) -> None:
    if not 1 <= valor <= 5:
        raise ValueError("Una materia debe tener entre 1 y 5 sesiones semanales")
    ...
    self.__sesiones_semanales = valor
```

Aunque se escriba `materia.sesiones_semanales = 0`, el setter lo rechaza. Lo mismo pasa con
`CursoParalelo.numero_estudiantes`. Esto aplica el artículo *Decorador property*.

### 11.5 Laboratorio hereda de Aula

```python
class Aula:
    def cumple_requisitos(self, numero_estudiantes, especialidad):
        """Un aula convencional solo recibe sesiones teóricas (sin especialidad)."""
        return especialidad is None and numero_estudiantes <= self.capacidad

class Laboratorio(Aula):
    def __init__(self, id, nombre, capacidad, facultad_id, especialidad, equipamiento):
        super().__init__(id, nombre, capacidad, facultad_id)
        self.especialidad = especialidad
        self.equipamiento = list(equipamiento)

    def cumple_requisitos(self, numero_estudiantes, especialidad):
        return (self.verificar_equipamiento_requerido(especialidad)
                and numero_estudiantes <= self.capacidad)
```

- `Laboratorio` **reutiliza** el constructor de `Aula` con `super()` y agrega lo suyo
  (herencia).
- `cumple_requisitos()` se **redefine**: un aula acepta solo teoría y un laboratorio acepta
  solo prácticas de su especialidad. El generador pregunta `aula.cumple_requisitos(...)` sin
  saber cuál de las dos es (polimorfismo).

### 11.6 Franjas horarias

`JornadaAcademica.crear_franjas()` divide cada jornada en bloques de 2 horas para cada día:

- Matutina, 07:00 a 13:00: bloques 07-09, 09-11 y 11-13.
- Vespertina, 14:00 a 18:00: bloques 14-16 y 16-18.

En total son 25 franjas por semana. `FranjaHoraria` es un `@dataclass(frozen=True)`: inmutable,
así que se puede comparar y usar como clave de diccionario.

---

## 12. La interfaz gráfica

📄 [interfaz/](interfaz/)

| Archivo | Qué hace |
|---|---|
| `app.py` | Ventana principal; cambia entre el login y el panel |
| `login.py` | Pantalla de inicio de sesión (la contraseña se muestra con •) |
| `panel.py` | Panel principal: lista de carreras, botones según el rol, tabla, leyenda y validación |
| `tabla_horario.py` | Dibuja la cuadrícula semanal (días × franjas, con el receso del almuerzo) |
| `dialogos.py` | Ventana para aprobar o rechazar con observación y contraseña |
| `tema.py` | Colores y estilos compartidos |

### 12.1 Los botones dependen de lo que el usuario puede hacer

```python
def _crear_acciones(self, horario):
    botones = []
    if self.usuario.puede_generar():
        if horario is None:
            botones.append(("Generar horario", "Primario.TButton", lambda: self._generar(False)))
        else:
            botones.append(("Regenerar propuesta", "Secundario.TButton", lambda: self._generar(True)))
    if horario is not None and self.usuario.puede_aprobar(horario):
        botones.append(("Rechazar", "Peligro.TButton", lambda: self._revisar(aprobar=False)))
        botones.append(("Aprobar horario", "Exito.TButton", lambda: self._revisar(aprobar=True)))
```

No hay ningún `if rol == "admin"`. El mismo código muestra **Generar** al administrador y
**Aprobar / Rechazar** al director, porque cada usuario responde distinto a `puede_generar()` y
`puede_aprobar()`.

### 12.2 Varias formas de consultar el horario

El selector **"Ver horario de:"** permite ver el horario por:

- Paralelo A, Paralelo B o ambos.
- Cada **docente**: sus horas no disponibles aparecen en gris.
- Cada **aula o laboratorio**.
- Cada **materia**.

Esto cubre la sección *Consulta de horarios* del documento del proyecto. Cada vista es solo un
filtro sobre las sesiones del horario:

```python
self.vistas[f"Docente · {docente.nombre}"] = (
    lambda s, d=docente: s.docente is d, "docente", docente.esta_disponible)
```

### 12.3 La interfaz no contiene lógica de horarios

El panel solo llama `gestor.generar()`, `gestor.aprobar()`, `gestor.rechazar()` y
`gestor.conflictos()`. No sabe cómo funciona el algoritmo ni cómo se guardan los datos
(**abstracción**).

---

## 13. Flujo completo de uso

```
 ADMINISTRADOR                   SISTEMA                              DIRECTOR DE CARRERA
 ─────────────                   ───────                              ───────────────────
 Inicia sesión ──────────▶ ServicioAutenticacion verifica el hash
 "Generar todos" ────────▶ GestorHorarios.generar()
                             ├─ Usuario.puede_generar()  ✓
                             ├─ GeneradorHorarios.generar_propuesta()
                             │     └─ backtracking + Restriccion.validar()
                             └─ Repositorio.guardar()  → estado PENDIENTE
                                                                      Inicia sesión
                           Panel muestra solo SU facultad ◀────────── (puede_ver)
                           ValidadorHorarios: ✓ Sin conflictos
                                                                      "Aprobar" + contraseña
                           confirmar_identidad() ✓ ◀──────────────────
                           GestorHorarios.aprobar()
                             ├─ ¿conflictos graves?  no
                             ├─ Horario.aprobar() → Usuario.puede_aprobar() ✓
                             └─ Repositorio.guardar() → estado APROBADO
 USUARIO DE CONSULTA
 Inicia sesión ──────────▶ puede_consultar(): solo ve los horarios APROBADOS
```

---

## 14. Pruebas automáticas

📄 [pruebas/test_academa.py](pruebas/test_academa.py). Hay 22 pruebas y todas pasan.

```bash
python -m unittest discover -s pruebas -t .
```

| Grupo | Qué verifica |
|---|---|
| Diseño | Las clases abstractas no se pueden instanciar; `Laboratorio` hereda de `Aula` y redefine sus requisitos; `Horario` es una `Collection`; `Materia` valida sus datos |
| Datos | Hay 3 facultades con laboratorios; cada carrera tiene Materia 1 a 5; solo existen los paralelos A y B (crear "C" da error) |
| Generación | Se ubican todas las sesiones sin conflictos; las prácticas van en el laboratorio correcto y la teoría en aula; se respeta la disponibilidad; un docente por materia y paralelo; regenerar da otra propuesta válida; el validador detecta un cruce provocado a propósito |
| Usuarios | Login correcto e incorrecto; la contraseña no se guarda en texto plano; cambio de contraseña; el director solo ve su facultad; solo el administrador genera |
| Aprobación | Flujo completo (el administrador no puede aprobar, tampoco un director de otra facultad); el rechazo exige motivo; no se aprueba un horario con conflictos; el JSON conserva el estado aprobado |

Gracias a la inyección de dependencias, las pruebas usan un repositorio en memoria y **no
modifican** el archivo `datos/horarios.json` de la aplicación.

---

## 15. Limitaciones y siguientes pasos

**Limitaciones de este avance:**

- Las materias son genéricas (Materia 1 a 5) y solo hay un nivel por carrera.
- Los datos (facultades, docentes, aulas) se definen en `datos/semilla.py`, no desde la interfaz.
- Las tutorías del diagrama todavía no están implementadas.
- No se pueden mover sesiones a mano; para cambiar un horario se regenera.
- Los usuarios viven en memoria: un cambio de contraseña se pierde al cerrar el programa.

**Siguientes pasos propuestos:**

1. Cargar las materias reales y más niveles por carrera.
2. Pantallas para registrar materias, docentes, aulas y disponibilidad.
3. Tutorías como una nueva restricción (una hija más de `Restriccion`).
4. Edición manual de sesiones con revalidación automática (el `ValidadorHorarios` ya está listo).
5. Base de datos (por ejemplo SQLite) como un nuevo `RepositorioHorarios`, sin cambiar el resto.
6. Exportar los horarios aprobados a PDF o Excel.

Los pasos 3 y 5 muestran el beneficio del diseño: **se agregan como clases nuevas, sin modificar
el código que ya funciona.**
