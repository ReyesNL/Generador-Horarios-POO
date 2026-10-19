"""Cuadrícula semanal: columnas = días, filas = franjas horarias."""
from __future__ import annotations

import tkinter as tk
from collections import defaultdict
from typing import Callable, Iterable

from interfaz.tema import COLORES, FUENTE
from modelos.horario import SesionClase
from modelos.tiempo import Dia, FranjaHoraria

# Lo que se escribe en una celda: (título en negrita, detalle)
TextoCelda = Callable[[SesionClase], tuple[str, str]]


class TablaHorario(tk.Frame):
    def __init__(self, master):
        # El fondo gris asoma entre celdas y dibuja las líneas de la cuadrícula.
        super().__init__(master, bg=COLORES["borde"])

    def mostrar_mensaje(self, texto: str) -> None:
        self._limpiar()
        tk.Label(self, text=texto, bg=COLORES["celda_vacia"], fg=COLORES["texto_suave"],
                 font=(FUENTE, 11), wraplength=560, justify="center"
                 ).grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

    def mostrar(self, franjas: list[FranjaHoraria], sesiones: Iterable[SesionClase],
                texto_de: TextoCelda, color_de: Callable[[SesionClase], str],
                disponible: Callable[[FranjaHoraria], bool] | None = None) -> None:
        self._limpiar()
        dias = list(Dia)
        horas = sorted({(f.hora_inicio, f.hora_fin) for f in franjas})
        franja_en = {(f.dia, f.hora_inicio): f for f in franjas}
        sesiones_en: dict[tuple, list[SesionClase]] = defaultdict(list)
        for sesion in sesiones:
            sesiones_en[(sesion.franja.dia, sesion.franja.hora_inicio)].append(sesion)

        self._encabezado("Hora", 0, 0)
        for columna, dia in enumerate(dias, 1):
            self._encabezado(dia.value, 0, columna)

        fila, fin_anterior = 1, None
        for inicio, fin in horas:
            if fin_anterior and inicio != fin_anterior:
                tk.Label(self, text=f"{fin_anterior} - {inicio}  ·  Receso", bg=COLORES["receso"],
                         fg=COLORES["texto_suave"], font=(FUENTE, 8)
                         ).grid(row=fila, column=0, columnspan=len(dias) + 1, sticky="nsew", padx=1, pady=1)
                fila += 1
            tk.Label(self, text=f"{inicio}\n{fin}", bg=COLORES["encabezado_tabla"], fg=COLORES["texto"],
                     font=(FUENTE, 9, "bold")).grid(row=fila, column=0, sticky="nsew", padx=1, pady=1)
            for columna, dia in enumerate(dias, 1):
                celda = self._celda(sesiones_en.get((dia, inicio), []), franja_en.get((dia, inicio)),
                                    texto_de, color_de, disponible)
                celda.grid(row=fila, column=columna, sticky="nsew", padx=1, pady=1)
            self.rowconfigure(fila, weight=1, uniform="franja", minsize=54)
            fila, fin_anterior = fila + 1, fin

        self.columnconfigure(0, weight=0, minsize=64)
        for columna in range(1, len(dias) + 1):
            self.columnconfigure(columna, weight=1, uniform="dia")

    # ---- partes ---------------------------------------------------------------
    def _limpiar(self) -> None:
        for hijo in self.winfo_children():
            hijo.destroy()
        columnas, filas = self.grid_size()
        for i in range(columnas):
            self.columnconfigure(i, weight=0, minsize=0, uniform="")
        for i in range(filas):
            self.rowconfigure(i, weight=0, minsize=0, uniform="")

    def _encabezado(self, texto: str, fila: int, columna: int) -> None:
        tk.Label(self, text=texto, bg=COLORES["encabezado_tabla"], fg=COLORES["texto"],
                 font=(FUENTE, 10, "bold"), pady=6).grid(row=fila, column=columna, sticky="nsew", padx=1, pady=1)

    def _celda(self, sesiones, franja, texto_de, color_de, disponible) -> tk.Frame:
        if sesiones:
            fondo = color_de(sesiones[0])
        elif franja is not None and disponible is not None and not disponible(franja):
            fondo = COLORES["no_disponible"]
        else:
            fondo = COLORES["celda_vacia"]
        celda = tk.Frame(self, bg=fondo, padx=4, pady=2)
        contenido = tk.Frame(celda, bg=fondo)
        contenido.pack(expand=True)         # centrado vertical y horizontal

        if not sesiones and fondo == COLORES["no_disponible"]:
            tk.Label(contenido, text="No disponible", bg=fondo, fg=COLORES["texto_suave"],
                     font=(FUENTE, 8, "italic")).pack()
        compacta = len(sesiones) > 1        # varias sesiones en la misma franja: solo los títulos
        for sesion in sesiones:
            titulo, detalle = texto_de(sesion)
            tk.Label(contenido, text=titulo, bg=fondo, fg=COLORES["texto"],
                     font=(FUENTE, 8 if compacta else 9, "bold")).pack()
            if not compacta:
                tk.Label(contenido, text=detalle, bg=fondo, fg=COLORES["texto"], font=(FUENTE, 8),
                         justify="center", wraplength=170).pack()
        return celda
