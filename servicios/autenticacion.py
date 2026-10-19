"""Inicio de sesión con usuario y contraseña."""
from __future__ import annotations

from typing import Iterable

from modelos.usuarios import Usuario


class CredencialesInvalidas(Exception):
    pass


class ServicioAutenticacion:
    def __init__(self, usuarios: Iterable[Usuario]):
        self._usuarios = {u.nombre_usuario.lower(): u for u in usuarios}
        self._actual: Usuario | None = None

    @property
    def usuario_actual(self) -> Usuario | None:
        return self._actual

    def iniciar_sesion(self, nombre_usuario: str, contrasena: str) -> Usuario:
        usuario = self._usuarios.get(nombre_usuario.strip().lower())
        # Mismo mensaje si falla el usuario o la contraseña: no se revela qué usuarios existen.
        if usuario is None or not usuario.iniciar_sesion(contrasena):
            raise CredencialesInvalidas("Usuario o contraseña incorrectos")
        self._actual = usuario
        return usuario

    def cerrar_sesion(self) -> None:
        if self._actual is not None:
            self._actual.cerrar_sesion()
        self._actual = None

    def confirmar_identidad(self, contrasena: str) -> bool:
        """Se pide otra vez la contraseña antes de aprobar o rechazar (a modo de firma)."""
        return self._actual is not None and self._actual.verificar_contrasena(contrasena)
