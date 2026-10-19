"""
Panel principal: lo que ve cada usuario después de iniciar sesión.

El panel nunca pregunta "¿es administrador?" o "¿es director?". Le pregunta
al usuario qué puede hacer (puede_generar, puede_aprobar, puede_consultar) y
cada clase de usuario responde a su manera: polimorfismo.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from interfaz.dialogos import DialogoRevision
from interfaz.tabla_horario import TablaHorario
from interfaz.tema import COLORES, COLORES_MATERIA, ESTILO_ESTADO, FUENTE
from modelos.academico import Carrera
from modelos.horario import EstadoHorario, Horario, SesionClase
from modelos.usuarios import Usuario
from servicios.autenticacion import ServicioAutenticacion
from servicios.generador import GeneracionFallida
from servicios.gestor_horarios import GestorHorarios

ESTADO_CORTO = {
    EstadoHorario.PENDIENTE: "Pendiente",
    EstadoHorario.APROBADO: "Aprobado",
    EstadoHorario.RECHAZADO: "Rechazado",
    None: "Sin generar",
}


def _fecha(valor) -> str:
    return valor.strftime("%d/%m/%Y %H:%M")


class PanelPrincipal(ttk.Frame):
    def __init__(self, master, usuario: Usuario, gestor: GestorHorarios,
                 autenticacion: ServicioAutenticacion, al_cerrar_sesion: Callable[[], None]):
        super().__init__(master, style="Fondo.TFrame")
        self.usuario = usuario
        self.gestor = gestor
        self.autenticacion = autenticacion
        self.al_cerrar_sesion = al_cerrar_sesion
        self.carrera: Carrera | None = None
        self.horario: Horario | None = None         # solo si el usuario puede consultarlo
        self.mensaje_vacio = ""
        self.vistas: dict[str, tuple] = {}          # etiqueta → (filtro, modo, disponibilidad)
        self.vista = tk.StringVar()

        self._crear_encabezado()
        cuerpo = ttk.Frame(self, style="Fondo.TFrame", padding=16)
        cuerpo.pack(fill="both", expand=True)
        cuerpo.columnconfigure(1, weight=1)
        cuerpo.rowconfigure(0, weight=1)
        self._crear_barra_lateral(cuerpo)
        self._crear_contenido(cuerpo)

        self._llenar_arbol()
        carreras = self.gestor.carreras_visibles(usuario)
        if carreras:
            self.arbol.selection_set(carreras[0].id)

    # =========================================================== construcción
    def _crear_encabezado(self) -> None:
        barra = ttk.Frame(self, style="Encabezado.TFrame", padding=(22, 12))
        barra.pack(fill="x")
        ttk.Label(barra, text="ACADEMA", style="EncabezadoTitulo.TLabel").pack(side="left")
        ttk.Label(barra, text="Sistema automatizado de horarios académicos",
                  style="EncabezadoTexto.TLabel").pack(side="left", padx=(14, 0), pady=(5, 0))
        ttk.Button(barra, text="Cerrar sesión", style="Encabezado.TButton",
                   command=self.al_cerrar_sesion).pack(side="right")
        datos = ttk.Frame(barra, style="Encabezado.TFrame")
        datos.pack(side="right", padx=18)
        ttk.Label(datos, text=self.usuario.nombre, style="EncabezadoNombre.TLabel").pack(anchor="e")
        ttk.Label(datos, text=f"{self.usuario.rol} · {self.usuario.alcance}",
                  style="EncabezadoTexto.TLabel").pack(anchor="e")

    def _crear_barra_lateral(self, cuerpo) -> None:
        lateral = ttk.Frame(cuerpo, style="Tarjeta.TFrame", padding=14)
        lateral.grid(row=0, column=0, sticky="ns", padx=(0, 16))
        ttk.Label(lateral, text="Facultades y carreras", style="Seccion.TLabel").pack(anchor="w")
        ttk.Label(lateral, text="Seleccione una carrera para ver su horario",
                  style="Suave.TLabel").pack(anchor="w", pady=(0, 8))

        self.arbol = ttk.Treeview(lateral, columns=("estado",), show="tree", selectmode="browse", height=10)
        self.arbol.column("#0", width=250, stretch=True)
        self.arbol.column("estado", width=86, anchor="e", stretch=False)
        self.arbol.pack(fill="both", expand=True)
        self.arbol.bind("<<TreeviewSelect>>", self._al_seleccionar)
        for estado, (color, _fondo) in ESTILO_ESTADO.items():
            self.arbol.tag_configure(self._etiqueta(estado), foreground=color)
        self.arbol.tag_configure("facultad", font=(FUENTE, 10, "bold"))

        self.conteo = ttk.Label(lateral, text="", style="Suave.TLabel", justify="left")
        self.conteo.pack(anchor="w", pady=(10, 10))
        if self.usuario.puede_generar():
            ttk.Button(lateral, text="Generar todos los horarios", style="Primario.TButton",
                       command=self._generar_todos).pack(fill="x")

    def _crear_contenido(self, cuerpo) -> None:
        area = ttk.Frame(cuerpo, style="Tarjeta.TFrame", padding=(22, 16))
        area.grid(row=0, column=1, sticky="nsew")
        area.columnconfigure(0, weight=1)
        area.rowconfigure(3, weight=1)

        cabecera = ttk.Frame(area, style="Blanco.TFrame")
        cabecera.grid(row=0, column=0, sticky="ew")
        cabecera.columnconfigure(0, weight=1)
        self.titulo = ttk.Label(cabecera, text="", style="Titulo.TLabel")
        self.titulo.grid(row=0, column=0, sticky="w")
        self.subtitulo = ttk.Label(cabecera, text="", style="Suave.TLabel")
        self.subtitulo.grid(row=1, column=0, sticky="w")
        self.acciones = ttk.Frame(cabecera, style="Blanco.TFrame")
        self.acciones.grid(row=0, column=1, rowspan=2, sticky="e")

        estado = ttk.Frame(area, style="Blanco.TFrame")
        estado.grid(row=1, column=0, sticky="ew", pady=(12, 10))
        self.chip_estado = tk.Label(estado, text="", font=(FUENTE, 9, "bold"), padx=10, pady=3)
        self.chip_estado.pack(side="left")
        self.validacion = ttk.Frame(estado, style="Blanco.TFrame")
        self.validacion.pack(side="right")
        self.detalle_estado = ttk.Label(estado, text="", style="Texto.TLabel", wraplength=520, justify="left")
        self.detalle_estado.pack(side="left", padx=10)

        barra_vista = ttk.Frame(area, style="Blanco.TFrame")
        barra_vista.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        ttk.Label(barra_vista, text="Ver horario de:", style="Seccion.TLabel").pack(side="left")
        self.selector = ttk.Combobox(barra_vista, textvariable=self.vista, state="readonly", width=32)
        self.selector.pack(side="left", padx=8)
        self.selector.bind("<<ComboboxSelected>>", lambda _e: self._dibujar_tabla())
        self.resumen = ttk.Label(barra_vista, text="", style="Suave.TLabel")
        self.resumen.pack(side="right")

        self.tabla = TablaHorario(area)
        self.tabla.grid(row=3, column=0, sticky="nsew")

        self.leyenda = ttk.Frame(area, style="Blanco.TFrame")       # materias y docentes asignados
        self.leyenda.grid(row=4, column=0, sticky="ew", pady=(12, 0))

    # =========================================================== barra lateral
    @staticmethod
    def _etiqueta(estado: EstadoHorario | None) -> str:
        return estado.name if estado else "SIN_GENERAR"

    def _llenar_arbol(self) -> None:
        for carrera in self.gestor.carreras_visibles(self.usuario):
            nodo = f"fac:{carrera.facultad.id}"
            if not self.arbol.exists(nodo):
                self.arbol.insert("", "end", iid=nodo, text=carrera.facultad.nombre, open=True, tags=("facultad",))
            self.arbol.insert(nodo, "end", iid=carrera.id, text=carrera.nombre)
        self._actualizar_arbol()

    def _actualizar_arbol(self) -> None:
        conteo: dict[EstadoHorario | None, int] = {}
        for carrera in self.gestor.carreras_visibles(self.usuario):
            horario = self.gestor.horario_de(carrera)
            estado = horario.estado if horario else None
            conteo[estado] = conteo.get(estado, 0) + 1
            self.arbol.item(carrera.id, values=(ESTADO_CORTO[estado],), tags=(self._etiqueta(estado),))
        self.conteo.config(text="  ·  ".join(f"{ESTADO_CORTO[e]}: {n}" for e, n in conteo.items()))

    def _al_seleccionar(self, _evento=None) -> None:
        seleccion = self.arbol.selection()
        if not seleccion:
            return
        if seleccion[0].startswith("fac:"):         # al elegir una facultad se abre su primera carrera
            hijos = self.arbol.get_children(seleccion[0])
            if hijos:
                self.arbol.selection_set(hijos[0])
            return
        carrera = self.gestor.catalogo.carrera(seleccion[0])
        if carrera is not self.carrera:
            self.vista.set("")
        self.carrera = carrera
        self._mostrar_carrera()

    # =========================================================== contenido
    def _refrescar(self) -> None:
        self._actualizar_arbol()
        if self.carrera is not None:
            self._mostrar_carrera()

    def _mostrar_carrera(self) -> None:
        carrera = self.carrera
        horario = self.gestor.horario_de(carrera)
        visible = horario is not None and self.usuario.puede_consultar(horario)
        self.horario = horario if visible else None
        if horario is None and self.usuario.puede_generar():
            self.mensaje_vacio = ("Aún no se ha generado el horario de esta carrera.\n"
                                  "Presione «Generar horario» para crear una propuesta automática.")
        elif horario is None:
            self.mensaje_vacio = "El administrador todavía no ha generado el horario de esta carrera."
        else:
            self.mensaje_vacio = "El horario de esta carrera todavía no ha sido aprobado por el director de carrera."

        paralelos = " y ".join(p.nombre for p in carrera.paralelos)
        self.titulo.config(text=carrera.nombre)
        self.subtitulo.config(text=f"{carrera.facultad.nombre}  ·  Nivel 1  ·  Paralelos {paralelos}")
        self._mostrar_estado(horario)
        self._crear_acciones(horario)
        self._preparar_vistas()
        self._dibujar_tabla()
        self._mostrar_leyenda(carrera)
        self._mostrar_validacion()

    def _mostrar_estado(self, horario: Horario | None) -> None:
        estado = horario.estado if horario else None
        color, fondo = ESTILO_ESTADO[estado]
        self.chip_estado.config(text=(estado.value if estado else "Sin generar").upper(), fg=color, bg=fondo)
        if horario is None:
            detalle = "Todavía no existe una propuesta para esta carrera."
        elif estado is EstadoHorario.PENDIENTE:
            detalle = f"Generado el {_fecha(horario.fecha_generacion)}. Esperando la revisión del director de carrera."
        elif estado is EstadoHorario.APROBADO:
            detalle = f"Aprobado por {horario.revisado_por} el {_fecha(horario.fecha_revision)}."
            if horario.observacion:
                detalle += f"  Observación: {horario.observacion}"
        else:
            detalle = (f"Rechazado por {horario.revisado_por} el {_fecha(horario.fecha_revision)}.  "
                       f"Motivo: {horario.observacion}")
        self.detalle_estado.config(text=detalle)

    def _crear_acciones(self, horario: Horario | None) -> None:
        for hijo in self.acciones.winfo_children():
            hijo.destroy()
        botones = []
        if self.usuario.puede_generar():
            if horario is None:
                botones.append(("Generar horario", "Primario.TButton", lambda: self._generar(False)))
            else:
                botones.append(("Regenerar propuesta", "Secundario.TButton", lambda: self._generar(True)))
        if horario is not None and self.usuario.puede_aprobar(horario):
            botones.append(("Rechazar", "Peligro.TButton", lambda: self._revisar(aprobar=False)))
            botones.append(("Aprobar horario", "Exito.TButton", lambda: self._revisar(aprobar=True)))
        for texto, estilo, accion in botones:
            ttk.Button(self.acciones, text=texto, style=estilo, command=accion).pack(side="left", padx=(8, 0))

    # =========================================================== tabla
    def _preparar_vistas(self) -> None:
        self.vistas = {}
        horario = self.horario
        if horario is not None:
            carrera = horario.carrera
            for curso in carrera.paralelos:
                self.vistas[f"Paralelo {curso.nombre}"] = (lambda s, c=curso: s.curso is c, "curso", None)
            self.vistas["Ambos paralelos (A y B)"] = (lambda s: True, "carrera", None)
            for docente in sorted({s.docente for s in horario}, key=lambda d: d.nombre):
                self.vistas[f"Docente · {docente.nombre}"] = (
                    lambda s, d=docente: s.docente is d, "docente", docente.esta_disponible)
            for aula in sorted({s.aula for s in horario}, key=lambda a: (a.es_laboratorio, a.nombre)):
                self.vistas[f"Aula · {aula.nombre}"] = (
                    lambda s, a=aula: s.aula is a, "aula", aula.verificar_disponibilidad)
            for materia in carrera.materias:
                self.vistas[f"Materia · {materia.nombre}"] = (lambda s, m=materia: s.materia is m, "materia", None)
        self.selector.config(values=list(self.vistas), state="readonly" if self.vistas else "disabled")
        if self.vista.get() not in self.vistas:
            self.vista.set(next(iter(self.vistas), ""))

    def _dibujar_tabla(self) -> None:
        if self.horario is None:
            self.tabla.mostrar_mensaje(self.mensaje_vacio)
            self.resumen.config(text="")
            return
        filtro, modo, disponible = self.vistas[self.vista.get()]
        sesiones = [s for s in self.horario if filtro(s)]
        self.tabla.mostrar(self.gestor.catalogo.franjas, sesiones,
                           lambda s: self._texto_celda(s, modo), self._color_materia, disponible)
        horas = sum(s.franja.duracion_horas for s in sesiones)
        en_laboratorio = sum(s.requiere_laboratorio for s in sesiones)
        self.resumen.config(text=f"{len(sesiones)} sesiones  ·  {horas} h semanales  ·  {en_laboratorio} en laboratorio")

    @staticmethod
    def _texto_celda(s: SesionClase, modo: str) -> tuple[str, str]:
        materia = f"{s.materia.nombre} (práctica)" if s.requiere_laboratorio else s.materia.nombre
        if modo == "curso":
            return materia, f"{s.docente.nombre}\n{s.aula.nombre}"
        if modo == "carrera":
            return f"{s.curso.nombre} · {materia}", f"{s.docente.nombre} · {s.aula.nombre}"
        if modo == "docente":
            return materia, f"Paralelo {s.curso.nombre}\n{s.aula.nombre}"
        if modo == "aula":
            return materia, f"Paralelo {s.curso.nombre}\n{s.docente.nombre}"
        return f"Paralelo {s.curso.nombre}", f"{s.docente.nombre}\n{s.aula.nombre}"

    @staticmethod
    def _color_materia(s: SesionClase) -> str:
        indice = s.materia.carrera.materias.index(s.materia)
        return COLORES_MATERIA[indice % len(COLORES_MATERIA)]

    # =========================================================== pie
    def _mostrar_leyenda(self, carrera: Carrera) -> None:
        """Una columna por materia: color, tipo y el docente asignado en cada paralelo."""
        for hijo in self.leyenda.winfo_children():
            hijo.destroy()
        for columna, materia in enumerate(carrera.materias):
            self.leyenda.columnconfigure(columna, weight=1, uniform="materia")
            item = ttk.Frame(self.leyenda, style="Blanco.TFrame")
            item.grid(row=0, column=columna, sticky="nw", padx=(0, 12))
            fila = ttk.Frame(item, style="Blanco.TFrame")
            fila.pack(anchor="w")
            tk.Frame(fila, bg=COLORES_MATERIA[columna % len(COLORES_MATERIA)], width=12, height=12,
                     highlightthickness=1, highlightbackground=COLORES["borde"]).pack(side="left", padx=(0, 6))
            ttk.Label(fila, text=materia.nombre, style="Seccion.TLabel").pack(side="left")
            ttk.Label(item, text=f"{materia.tipo.value} · {materia.sesiones_semanales} ses./sem.",
                      style="Suave.TLabel").pack(anchor="w")
            if self.horario is not None:
                for curso in carrera.paralelos:
                    sesiones = self.horario.sesiones_de(curso=curso, materia=materia)
                    if sesiones:
                        ttk.Label(item, text=f"{curso.nombre}: {sesiones[0].docente.nombre}",
                                  style="Suave.TLabel").pack(anchor="w")

    def _mostrar_validacion(self) -> None:
        for hijo in self.validacion.winfo_children():
            hijo.destroy()
        if self.horario is None:
            return
        conflictos = self.gestor.conflictos(self.horario)
        graves = [c for c in conflictos if c.es_grave]
        if not conflictos:
            color, fondo, texto = COLORES["exito"], "#DFF3E3", "✓  SIN CONFLICTOS"
        elif graves:
            color, fondo, texto = COLORES["peligro"], "#FDE3E1", f"✕  {len(graves)} CONFLICTO(S)"
        else:
            color, fondo, texto = "#8A4B00", "#FFEFD2", f"!  {len(conflictos)} AVISO(S)"
        tk.Label(self.validacion, text=texto, fg=color, bg=fondo, font=(FUENTE, 9, "bold"),
                 padx=10, pady=3).pack(side="left")
        if conflictos:
            ttk.Button(self.validacion, text="Ver detalle", style="Secundario.TButton",
                       command=lambda: self._ver_conflictos(conflictos)).pack(side="left", padx=(8, 0))
        else:
            reglas = len(self.gestor.validador.restricciones)
            ttk.Label(self.validacion, text=f"{reglas} reglas verificadas",
                      style="Suave.TLabel").pack(side="left", padx=(8, 0))

    def _ver_conflictos(self, conflictos) -> None:
        detalle = "\n".join(f"• {c.describir()}" for c in conflictos)
        messagebox.showwarning("Conflictos detectados", detalle, parent=self)

    # =========================================================== acciones
    def _generar(self, regenerar: bool) -> None:
        horario = self.gestor.horario_de(self.carrera)
        if regenerar and horario is not None and horario.estado is EstadoHorario.APROBADO:
            if not messagebox.askyesno(
                    "Regenerar horario aprobado",
                    f"El horario de {self.carrera.nombre} ya fue aprobado.\n"
                    "La nueva propuesta volverá a quedar pendiente de aprobación.\n\n¿Desea continuar?",
                    parent=self):
                return
        self._ejecutar(lambda: self.gestor.generar(self.usuario, self.carrera, regenerar=regenerar))

    def _generar_todos(self) -> None:
        aprobados = [c.nombre for c in self.gestor.carreras_visibles(self.usuario)
                     if (h := self.gestor.horario_de(c)) and h.estado is EstadoHorario.APROBADO]
        if aprobados and not messagebox.askyesno(
                "Generar todos los horarios",
                f"Ya están aprobados: {', '.join(aprobados)}.\n"
                "Si continúa, todos los horarios volverán a quedar pendientes de aprobación.\n\n¿Desea continuar?",
                parent=self):
            return
        self._ejecutar(lambda: self.gestor.generar_todos(self.usuario))

    def _ejecutar(self, accion: Callable[[], object]) -> None:
        ventana = self.winfo_toplevel()
        ventana.config(cursor="watch")
        self.update_idletasks()
        try:
            accion()
        except (GeneracionFallida, PermissionError) as error:
            messagebox.showerror("No se pudo generar el horario", str(error), parent=self)
        finally:
            ventana.config(cursor="")
        self._refrescar()

    def _revisar(self, aprobar: bool) -> None:
        horario = self.gestor.horario_de(self.carrera)

        def confirmar(observacion: str, contrasena: str) -> str | None:
            if not self.autenticacion.confirmar_identidad(contrasena):
                return "Contraseña incorrecta"
            try:
                if aprobar:
                    self.gestor.aprobar(self.usuario, horario, observacion)
                else:
                    self.gestor.rechazar(self.usuario, horario, observacion)
            except (PermissionError, ValueError) as error:
                return str(error)
            self._refrescar()
            return None

        if aprobar:
            DialogoRevision(self, "Aprobar horario",
                            f"Va a aprobar el horario de {self.carrera.nombre} ({len(horario)} sesiones, "
                            "paralelos A y B). Una vez aprobado ya no se podrá modificar.",
                            observacion_obligatoria=False, texto_boton="Aprobar horario",
                            estilo_boton="Exito.TButton", al_confirmar=confirmar)
        else:
            DialogoRevision(self, "Rechazar horario",
                            "Indique qué se debe corregir. El administrador verá el motivo y podrá "
                            "regenerar la propuesta.",
                            observacion_obligatoria=True, texto_boton="Rechazar horario",
                            estilo_boton="Peligro.TButton", al_confirmar=confirmar)
