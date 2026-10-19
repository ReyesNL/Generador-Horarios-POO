"""
ACADEMA · Sistema Automatizado para la Planificación y Optimización de Horarios Académicos
Primer avance · Programación Orientada a Objetos · ULEAM

Este archivo es la "raíz de composición": aquí, y solo aquí, se crean los
objetos concretos y se inyectan unos en otros. El resto del código recibe
sus dependencias ya construidas (inyección de dependencias por constructor).

Ejecutar:   python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable

from datos.semilla import crear_catalogo_demo, crear_usuarios_demo
from reglas.restricciones import (RestriccionCompatibilidadGrupos, RestriccionDisponibilidad,
                                  RestriccionDistribucionSemanal, RestriccionEspacio)
from repositorios.catalogo import CatalogoAcademico
from repositorios.horarios import RepositorioHorarios, RepositorioHorariosJSON
from servicios.autenticacion import ServicioAutenticacion
from servicios.generador import GeneradorHorarios
from servicios.gestor_horarios import GestorHorarios
from servicios.validador import ValidadorHorarios

RUTA_HORARIOS = Path(__file__).resolve().parent / "datos" / "horarios.json"


def crear_restricciones():
    """Reglas activas. Para agregar una nueva basta con crear otra hija de Restriccion y sumarla aquí."""
    return [
        RestriccionDisponibilidad(1),
        RestriccionEspacio(2),
        RestriccionCompatibilidadGrupos(3),
        RestriccionDistribucionSemanal(4),      # deseable (prioridad 2)
    ]


def construir_servicios(crear_repositorio: Callable[[CatalogoAcademico], RepositorioHorarios] | None = None):
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


def _activar_alta_resolucion() -> None:
    """En Windows evita que la ventana se vea borrosa en pantallas con escala mayor a 100 %."""
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass


def main() -> None:
    from interfaz.app import AplicacionAcadema      # tkinter solo se carga al abrir la ventana
    _activar_alta_resolucion()
    autenticacion, gestor = construir_servicios()
    AplicacionAcadema(autenticacion, gestor).mainloop()


if __name__ == "__main__":
    main()
