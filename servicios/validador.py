"""ValidadorHorarios: revisa un horario completo y reporta sus conflictos."""
from __future__ import annotations

from modelos.horario import Conflicto, Horario, SesionClase
from reglas.restricciones import Restriccion


class ValidadorHorarios:
    def __init__(self, restricciones: list[Restriccion]):
        self.restricciones = list(restricciones)        # inyectadas, igual que en el generador

    def detectar_conflictos(self, horario: Horario, otras_sesiones=()) -> list[Conflicto]:
        """Aplica cada restricción a cada sesión. otras_sesiones = sesiones de otros horarios."""
        todas: list[SesionClase] = list(horario) + list(otras_sesiones)
        conflictos: dict[tuple[str, str], Conflicto] = {}
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

    def validar(self, horario: Horario, otras_sesiones=()) -> bool:
        """True si el horario no tiene conflictos graves (los avisos no lo invalidan)."""
        return not any(c.es_grave for c in self.detectar_conflictos(horario, otras_sesiones))
