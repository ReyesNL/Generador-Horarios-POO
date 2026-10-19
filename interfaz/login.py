"""Pantalla de inicio de sesión."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from interfaz.tema import FUENTE
from modelos.usuarios import Usuario
from servicios.autenticacion import CredencialesInvalidas, ServicioAutenticacion


class PantallaLogin(ttk.Frame):
    def __init__(self, master, autenticacion: ServicioAutenticacion, al_ingresar: Callable[[Usuario], None]):
        super().__init__(master, style="Fondo.TFrame")
        self.autenticacion = autenticacion
        self.al_ingresar = al_ingresar
        self.usuario = tk.StringVar()
        self.contrasena = tk.StringVar()

        tarjeta = ttk.Frame(self, style="Tarjeta.TFrame", padding=(44, 36))
        tarjeta.place(relx=0.5, rely=0.47, anchor="center")

        ttk.Label(tarjeta, text="ACADEMA", style="Logo.TLabel").pack()
        ttk.Label(tarjeta, text="Planificación automática de horarios académicos",
                  style="Suave.TLabel").pack(pady=(0, 26))

        ttk.Label(tarjeta, text="Usuario", style="Seccion.TLabel").pack(anchor="w")
        self.campo_usuario = ttk.Entry(tarjeta, textvariable=self.usuario, width=34, font=(FUENTE, 11))
        self.campo_usuario.pack(fill="x", pady=(4, 14))

        ttk.Label(tarjeta, text="Contraseña", style="Seccion.TLabel").pack(anchor="w")
        self.campo_contrasena = ttk.Entry(tarjeta, textvariable=self.contrasena, show="•", width=34,
                                          font=(FUENTE, 11))
        self.campo_contrasena.pack(fill="x", pady=(4, 6))

        self.mensaje = ttk.Label(tarjeta, text="", style="Error.TLabel")
        self.mensaje.pack(anchor="w", pady=(0, 10))

        ttk.Button(tarjeta, text="Ingresar", style="Primario.TButton",
                   command=self.ingresar).pack(fill="x")
        ttk.Label(tarjeta, text="Usuarios de prueba: ver README.md", style="Suave.TLabel").pack(pady=(18, 0))

        self.campo_usuario.bind("<Return>", lambda _e: self.campo_contrasena.focus_set())
        self.campo_contrasena.bind("<Return>", lambda _e: self.ingresar())
        self.after(50, self.campo_usuario.focus_set)

    def ingresar(self) -> None:
        if not self.usuario.get().strip() or not self.contrasena.get():
            self.mensaje.config(text="Ingrese su usuario y contraseña")
            return
        try:
            usuario = self.autenticacion.iniciar_sesion(self.usuario.get(), self.contrasena.get())
        except CredencialesInvalidas as error:
            self.mensaje.config(text=str(error))
            self.contrasena.set("")
            self.campo_contrasena.focus_set()
            return
        self.al_ingresar(usuario)
