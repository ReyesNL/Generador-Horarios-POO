"""Colores, fuentes y estilos ttk compartidos por todas las pantallas."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from modelos.horario import EstadoHorario

FUENTE = "Segoe UI"

COLORES = {
    "fondo": "#F2F4F8",
    "tarjeta": "#FFFFFF",
    "borde": "#D8DEE8",
    "texto": "#1D2939",
    "texto_suave": "#667085",
    "primario": "#1F4E79",
    "primario_activo": "#163A5A",
    "encabezado_texto": "#C9D8E8",
    "exito": "#1E7B34",
    "exito_activo": "#17602A",
    "peligro": "#B42318",
    "peligro_activo": "#912018",
    "secundario": "#E8EDF4",
    "secundario_activo": "#D9E1EC",
    "celda_vacia": "#FAFBFC",
    "no_disponible": "#E9ECF1",
    "encabezado_tabla": "#E6ECF5",
    "receso": "#F4F6F9",
}

# Un color por materia (en el orden de la carrera).
COLORES_MATERIA = ("#D8E8FA", "#DDF2DA", "#FFEDCC", "#F6DDEB", "#E5DEF8", "#D6F0F0")

# (texto, fondo) de la etiqueta de estado. None = horario aún no generado.
ESTILO_ESTADO = {
    EstadoHorario.PENDIENTE: ("#8A4B00", "#FFEFD2"),
    EstadoHorario.APROBADO: ("#1B6B2E", "#DFF3E3"),
    EstadoHorario.RECHAZADO: ("#A51C12", "#FDE3E1"),
    None: ("#5B6678", "#ECEFF4"),
}


def configurar_estilos(raiz: tk.Tk) -> None:
    c = COLORES
    estilo = ttk.Style(raiz)
    estilo.theme_use("clam")
    raiz.configure(bg=c["fondo"])
    raiz.option_add("*TCombobox*Listbox.font", (FUENTE, 10))

    estilo.configure(".", font=(FUENTE, 10), background=c["fondo"], foreground=c["texto"])
    estilo.configure("Fondo.TFrame", background=c["fondo"])
    estilo.configure("Tarjeta.TFrame", background=c["tarjeta"], bordercolor=c["borde"],
                     relief="solid", borderwidth=1)
    estilo.configure("Blanco.TFrame", background=c["tarjeta"])
    estilo.configure("Encabezado.TFrame", background=c["primario"])

    etiquetas = {
        "Texto.TLabel": (c["tarjeta"], c["texto"], (FUENTE, 10)),
        "Suave.TLabel": (c["tarjeta"], c["texto_suave"], (FUENTE, 9)),
        "Seccion.TLabel": (c["tarjeta"], c["texto"], (FUENTE, 10, "bold")),
        "Titulo.TLabel": (c["tarjeta"], c["texto"], (FUENTE, 17, "bold")),
        "Logo.TLabel": (c["tarjeta"], c["primario"], (FUENTE, 28, "bold")),
        "Error.TLabel": (c["tarjeta"], c["peligro"], (FUENTE, 9)),
        "Exito.TLabel": (c["tarjeta"], c["exito"], (FUENTE, 10)),
        "EncabezadoTitulo.TLabel": (c["primario"], "#FFFFFF", (FUENTE, 15, "bold")),
        "EncabezadoNombre.TLabel": (c["primario"], "#FFFFFF", (FUENTE, 10, "bold")),
        "EncabezadoTexto.TLabel": (c["primario"], c["encabezado_texto"], (FUENTE, 9)),
    }
    for nombre, (fondo, texto, fuente) in etiquetas.items():
        estilo.configure(nombre, background=fondo, foreground=texto, font=fuente)

    botones = {
        "Primario.TButton": (c["primario"], c["primario_activo"], "#FFFFFF"),
        "Exito.TButton": (c["exito"], c["exito_activo"], "#FFFFFF"),
        "Peligro.TButton": (c["peligro"], c["peligro_activo"], "#FFFFFF"),
        "Secundario.TButton": (c["secundario"], c["secundario_activo"], c["texto"]),
        "Encabezado.TButton": (c["primario_activo"], "#0F2A42", "#FFFFFF"),
    }
    for nombre, (fondo, activo, texto) in botones.items():
        estilo.configure(nombre, background=fondo, foreground=texto, bordercolor=fondo,
                         lightcolor=fondo, darkcolor=fondo, focuscolor=fondo,
                         font=(FUENTE, 10, "bold"), padding=(14, 7))
        estilo.map(nombre,
                   background=[("disabled", "#C5CCD6"), ("pressed", activo), ("active", activo)],
                   foreground=[("disabled", "#F5F6F8")],
                   bordercolor=[("active", activo)], lightcolor=[("active", activo)],
                   darkcolor=[("active", activo)])

    estilo.configure("TEntry", padding=6, fieldbackground="#FFFFFF", bordercolor=c["borde"],
                     lightcolor=c["borde"])
    estilo.map("TEntry", bordercolor=[("focus", c["primario"])], lightcolor=[("focus", c["primario"])])
    estilo.configure("TCombobox", padding=5, fieldbackground="#FFFFFF", background="#FFFFFF",
                     bordercolor=c["borde"], arrowcolor=c["primario"])
    estilo.map("TCombobox", fieldbackground=[("readonly", "#FFFFFF")],
               selectbackground=[("readonly", "#FFFFFF")], selectforeground=[("readonly", c["texto"])])

    estilo.configure("Treeview", background=c["tarjeta"], fieldbackground=c["tarjeta"],
                     foreground=c["texto"], rowheight=30, borderwidth=0, font=(FUENTE, 10))
    estilo.map("Treeview", background=[("selected", "#DCE8F5")], foreground=[("selected", c["texto"])])
    estilo.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])     # sin borde
