"""Ventana para aprobar o rechazar un horario (con observación y contraseña)."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from interfaz.tema import COLORES, FUENTE


class DialogoRevision(tk.Toplevel):
    """al_confirmar(observacion, contrasena) devuelve None si todo salió bien, o el texto del error."""

    def __init__(self, master, titulo: str, mensaje: str, observacion_obligatoria: bool,
                 texto_boton: str, estilo_boton: str, al_confirmar: Callable[[str, str], str | None]):
        super().__init__(master)
        self.al_confirmar = al_confirmar
        self.observacion_obligatoria = observacion_obligatoria
        self.title(titulo)
        self.configure(bg=COLORES["tarjeta"])
        self.resizable(False, False)
        self.transient(master.winfo_toplevel())

        marco = ttk.Frame(self, style="Blanco.TFrame", padding=24)
        marco.pack(fill="both", expand=True)
        ttk.Label(marco, text=titulo, style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(marco, text=mensaje, style="Texto.TLabel", wraplength=440,
                  justify="left").pack(anchor="w", pady=(6, 16))

        ttk.Label(marco, text="Observación (obligatoria)" if observacion_obligatoria else "Observación (opcional)",
                  style="Seccion.TLabel").pack(anchor="w")
        self.observacion = tk.Text(marco, height=4, width=54, font=(FUENTE, 10), wrap="word",
                                   relief="solid", bd=1, highlightthickness=0)
        self.observacion.pack(fill="x", pady=(4, 14))

        ttk.Label(marco, text="Confirme con su contraseña", style="Seccion.TLabel").pack(anchor="w")
        self.contrasena = ttk.Entry(marco, show="•", width=32)
        self.contrasena.pack(anchor="w", pady=(4, 4))
        self.error = ttk.Label(marco, text="", style="Error.TLabel")
        self.error.pack(anchor="w", pady=(0, 12))

        botones = ttk.Frame(marco, style="Blanco.TFrame")
        botones.pack(fill="x")
        ttk.Button(botones, text=texto_boton, style=estilo_boton, command=self._confirmar).pack(side="right")
        ttk.Button(botones, text="Cancelar", style="Secundario.TButton",
                   command=self.destroy).pack(side="right", padx=(0, 8))

        self.contrasena.bind("<Return>", lambda _e: self._confirmar())
        self.bind("<Escape>", lambda _e: self.destroy())
        self._centrar(master.winfo_toplevel())
        self.grab_set()
        (self.observacion if observacion_obligatoria else self.contrasena).focus_set()

    def _centrar(self, ventana) -> None:
        self.update_idletasks()
        x = ventana.winfo_rootx() + (ventana.winfo_width() - self.winfo_reqwidth()) // 2
        y = ventana.winfo_rooty() + (ventana.winfo_height() - self.winfo_reqheight()) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def _confirmar(self) -> None:
        observacion = self.observacion.get("1.0", "end").strip()
        if self.observacion_obligatoria and not observacion:
            self.error.config(text="Escriba el motivo del rechazo")
            return
        if not self.contrasena.get():
            self.error.config(text="Ingrese su contraseña para confirmar")
            return
        error = self.al_confirmar(observacion, self.contrasena.get())
        if error:
            self.error.config(text=error)
            self.contrasena.delete(0, "end")
        else:
            self.destroy()
