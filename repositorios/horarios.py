"""
Repositorios de horarios.

RepositorioHorarios es una INTERFAZ FORMAL (clase abstracta con solo métodos
abstractos). El GestorHorarios depende de esta interfaz y no de una clase
concreta, así que se le puede inyectar cualquier implementación:

    RepositorioHorariosMemoria → para pruebas (no toca el disco)
    RepositorioHorariosJSON    → para la aplicación (guarda en datos/horarios.json)

Mañana se podría agregar un RepositorioHorariosSQLite sin cambiar nada más.
"""
from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from modelos.horario import EstadoHorario, Horario, SesionClase
from repositorios.catalogo import CatalogoAcademico


class RepositorioHorarios(ABC):
    @abstractmethod
    def guardar(self, horario: Horario) -> None:
        """Guarda (o reemplaza) el horario de una carrera."""

    @abstractmethod
    def obtener(self, carrera_id: str) -> Horario | None:
        """Horario de la carrera, o None si aún no se ha generado."""

    @abstractmethod
    def listar(self) -> list[Horario]:
        """Todos los horarios guardados."""


class RepositorioHorariosMemoria(RepositorioHorarios):
    def __init__(self):
        self._horarios: dict[str, Horario] = {}

    def guardar(self, horario):
        self._horarios[horario.carrera.id] = horario

    def obtener(self, carrera_id):
        return self._horarios.get(carrera_id)

    def listar(self):
        return list(self._horarios.values())


class RepositorioHorariosJSON(RepositorioHorariosMemoria):
    """Igual que el de memoria, pero además escribe cada cambio en un archivo JSON."""

    VERSION = 1

    def __init__(self, ruta: str | Path, catalogo: CatalogoAcademico):
        super().__init__()
        self.ruta = Path(ruta)
        self.catalogo = catalogo
        self._cargar()

    def guardar(self, horario):
        super().guardar(horario)
        self._escribir()

    # ---- disco --------------------------------------------------------
    def _cargar(self) -> None:
        if not self.ruta.exists():
            return
        try:
            datos = json.loads(self.ruta.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            print(f"[Academa] No se pudo leer {self.ruta}: {error}. Se empieza sin horarios.")
            return
        for item in datos.get("horarios", []):
            horario = self._desde_dict(item)
            if horario is not None:
                super().guardar(horario)

    def _escribir(self) -> None:
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        datos = {"version": self.VERSION, "horarios": [self._a_dict(h) for h in self.listar()]}
        temporal = self.ruta.with_suffix(".tmp")
        temporal.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temporal, self.ruta)     # reemplazo atómico: nunca queda un archivo a medias

    @staticmethod
    def _a_dict(horario: Horario) -> dict:
        return {
            "id": horario.id,
            "carrera": horario.carrera.id,
            "fecha_generacion": horario.fecha_generacion.isoformat(timespec="seconds"),
            "estado": horario.estado.name,
            "revisado_por": horario.revisado_por,
            "fecha_revision": horario.fecha_revision.isoformat(timespec="seconds") if horario.fecha_revision else None,
            "observacion": horario.observacion,
            "sesiones": [{
                "id": s.id,
                "materia": s.materia.id,
                "docente": s.docente.id,
                "curso": s.curso.id,
                "aula": s.aula.id,
                "franja": s.franja.id,
                "especialidad": s.especialidad_requerida,
            } for s in horario],
        }

    def _desde_dict(self, item: dict) -> Horario | None:
        c = self.catalogo
        carrera = c.carrera(item["carrera"])
        if carrera is None:
            return None
        sesiones = []
        for s in item["sesiones"]:
            partes = (c.materia(s["materia"]), c.docente(s["docente"]), c.curso(s["curso"]),
                      c.aula(s["aula"]), c.franja(s["franja"]))
            if None in partes:      # los datos de referencia cambiaron: el horario guardado ya no sirve
                print(f"[Academa] Se descarta el horario guardado de {carrera.nombre}: hace referencia a datos que ya no existen.")
                return None
            sesiones.append(SesionClase(s["id"], *partes, s.get("especialidad")))
        fecha_revision = item.get("fecha_revision")
        return Horario.reconstruir(
            item["id"], carrera, sesiones,
            fecha_generacion=datetime.fromisoformat(item["fecha_generacion"]),
            estado=EstadoHorario[item["estado"]],
            revisado_por=item.get("revisado_por"),
            fecha_revision=datetime.fromisoformat(fecha_revision) if fecha_revision else None,
            observacion=item.get("observacion", ""),
        )
