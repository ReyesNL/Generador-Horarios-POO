"""
Usuarios del sistema (verde en el diagrama).

Usuario es ABSTRACTA: define lo común (credenciales y sesión) y obliga a cada
rol a responder qué puede hacer. Cada hija responde a su manera a las mismas
preguntas (polimorfismo); la interfaz solo pregunta, nunca revisa "qué tipo
de usuario es".

    Usuario (abstracta)
      ├── Administrador     → genera y regenera los horarios de todas las facultades
      ├── DirectorCarrera   → revisa y aprueba los horarios de SU facultad
      └── UsuarioConsulta   → solo ve horarios ya aprobados (docentes, estudiantes)
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from modelos.horario import EstadoHorario

if TYPE_CHECKING:
    from modelos.academico import Carrera, Facultad
    from modelos.horario import Horario


class Usuario(ABC):
    ITERACIONES_HASH = 100_000

    def __init__(self, id: str, nombre: str, nombre_usuario: str, email: str, contrasena: str):
        self.id = id
        self.nombre = nombre
        self.nombre_usuario = nombre_usuario
        self.email = email
        # Encapsulamiento: la contraseña nunca se guarda en texto plano y el hash
        # queda privado (name mangling: Python lo renombra a _Usuario__hash).
        self.__sal = secrets.token_bytes(16)
        self.__hash = self._calcular_hash(contrasena, self.__sal)
        self.__sesion_activa = False

    # ---- lo que cada rol DEBE definir -------------------------------------
    @property
    @abstractmethod
    def rol(self) -> str:
        """Nombre del rol que se muestra en pantalla."""

    @property
    @abstractmethod
    def alcance(self) -> str:
        """Qué parte de la universidad puede ver este usuario."""

    @abstractmethod
    def puede_generar(self) -> bool:
        """¿Puede generar o regenerar propuestas de horario?"""

    @abstractmethod
    def puede_ver(self, carrera: Carrera) -> bool:
        """¿La carrera aparece en su panel?"""

    @abstractmethod
    def puede_aprobar(self, horario: Horario) -> bool:
        """¿Puede aprobar o rechazar este horario ahora mismo?"""

    def puede_consultar(self, horario: Horario) -> bool:
        """¿Puede ver el detalle del horario? Por defecto, si ve la carrera."""
        return self.puede_ver(horario.carrera)

    # ---- credenciales -----------------------------------------------------
    @staticmethod
    def _calcular_hash(contrasena: str, sal: bytes) -> bytes:
        return hashlib.pbkdf2_hmac("sha256", contrasena.encode("utf-8"), sal, Usuario.ITERACIONES_HASH)

    def verificar_contrasena(self, contrasena: str) -> bool:
        return hmac.compare_digest(self._calcular_hash(contrasena, self.__sal), self.__hash)

    def iniciar_sesion(self, contrasena: str) -> bool:
        self.__sesion_activa = self.verificar_contrasena(contrasena)
        return self.__sesion_activa

    def cerrar_sesion(self) -> None:
        self.__sesion_activa = False

    @property
    def sesion_activa(self) -> bool:
        return self.__sesion_activa

    def cambiar_contrasena(self, actual: str, nueva: str) -> None:
        if not self.verificar_contrasena(actual):
            raise PermissionError("La contraseña actual no es correcta")
        if len(nueva) < 6:
            raise ValueError("La nueva contraseña debe tener al menos 6 caracteres")
        self.__sal = secrets.token_bytes(16)
        self.__hash = self._calcular_hash(nueva, self.__sal)

    def __str__(self) -> str:
        return f"{self.nombre} ({self.rol})"


class Administrador(Usuario):
    @property
    def rol(self) -> str:
        return "Administrador"

    @property
    def alcance(self) -> str:
        return "Todas las facultades"

    def puede_generar(self) -> bool:
        return True

    def puede_ver(self, carrera: Carrera) -> bool:
        return True

    def puede_aprobar(self, horario: Horario) -> bool:
        return False        # quien genera no aprueba: eso le toca al director de la facultad


class DirectorCarrera(Usuario):
    """Director de carrera de una facultad (el «Coordinador» del diagrama)."""

    def __init__(self, id: str, nombre: str, nombre_usuario: str, email: str, contrasena: str,
                 facultad: Facultad):
        super().__init__(id, nombre, nombre_usuario, email, contrasena)
        self.facultad_asignada = facultad

    @property
    def rol(self) -> str:
        return "Director de carrera"

    @property
    def alcance(self) -> str:
        return self.facultad_asignada.nombre

    def puede_generar(self) -> bool:
        return False

    def puede_ver(self, carrera: Carrera) -> bool:
        return carrera.facultad is self.facultad_asignada

    def puede_aprobar(self, horario: Horario) -> bool:
        return self.puede_ver(horario.carrera) and horario.estado is EstadoHorario.PENDIENTE


class UsuarioConsulta(Usuario):
    """Docentes o estudiantes: ven los horarios, pero solo cuando ya están aprobados."""

    @property
    def rol(self) -> str:
        return "Consulta"

    @property
    def alcance(self) -> str:
        return "Horarios aprobados"

    def puede_generar(self) -> bool:
        return False

    def puede_ver(self, carrera: Carrera) -> bool:
        return True

    def puede_aprobar(self, horario: Horario) -> bool:
        return False

    def puede_consultar(self, horario: Horario) -> bool:
        return super().puede_consultar(horario) and horario.estado is EstadoHorario.APROBADO
