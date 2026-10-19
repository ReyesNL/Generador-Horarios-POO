"""Ventana principal: alterna entre el inicio de sesión y el panel del usuario."""
from __future__ import annotations

import tkinter as tk

from interfaz.login import PantallaLogin
from interfaz.panel import PanelPrincipal
from interfaz.tema import configurar_estilos
from modelos.usuarios import Usuario
from servicios.autenticacion import ServicioAutenticacion
from servicios.gestor_horarios import GestorHorarios


class AplicacionAcadema(tk.Tk):
    def __init__(self, autenticacion: ServicioAutenticacion, gestor: GestorHorarios):
        super().__init__()
        self.autenticacion = autenticacion
        self.gestor = gestor
        self.title("Academa · Horarios académicos")
        configurar_estilos(self)

        ancho = min(1440, self.winfo_screenwidth() - 60)
        alto = min(900, self.winfo_screenheight() - 90)
        x = (self.winfo_screenwidth() - ancho) // 2
        y = max((self.winfo_screenheight() - alto) // 2 - 20, 0)
        self.geometry(f"{ancho}x{alto}+{x}+{y}")
        self.minsize(1080, 640)
        if self.winfo_screenheight() <= 900:
            try:
                self.state("zoomed")        # en pantallas pequeñas se aprovecha toda la altura
            except tk.TclError:
                pass

        self._pantalla: tk.Widget | None = None
        self.mostrar_login()

    def _cambiar_pantalla(self, pantalla: tk.Widget) -> None:
        if self._pantalla is not None:
            self._pantalla.destroy()
        self._pantalla = pantalla
        pantalla.pack(fill="both", expand=True)

    def mostrar_login(self) -> None:
        self._cambiar_pantalla(PantallaLogin(self, self.autenticacion, al_ingresar=self.mostrar_panel))

    def mostrar_panel(self, usuario: Usuario) -> None:
        self._cambiar_pantalla(PanelPrincipal(self, usuario, self.gestor, self.autenticacion,
                                              al_cerrar_sesion=self.cerrar_sesion))

    def cerrar_sesion(self) -> None:
        self.autenticacion.cerrar_sesion()
        self.mostrar_login()
