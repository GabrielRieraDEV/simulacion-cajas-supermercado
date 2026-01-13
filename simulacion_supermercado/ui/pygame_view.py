"""Visualización básica del sistema mediante Pygame."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List

try:
    import pygame
except ImportError as exc:  # pragma: no cover - dependencia opcional
    raise RuntimeError(
        "Se requiere pygame para la visualización. Instálalo e intenta nuevamente."
    ) from exc

from simulacion_supermercado.simulation.cliente import Cliente
from simulacion_supermercado.simulation.escenarios import Escenario

WIDTH, HEIGHT = 900, 600
BACKGROUND = (18, 18, 32)
COLORS = {
    "tradicional": (0, 173, 181),
    "automatica": (238, 82, 83),
    "rapida": (255, 211, 42),
    "texto": (236, 240, 241),
    "cola": (255, 255, 255),
}

POSITIONS = {
    "tradicional": (80, 120),
    "automatica": (80, 280),
    "rapida": (80, 440),
}


class PygameVisualizer:
    """Muestra de forma simple las cajas y sus colas resultantes."""

    def __init__(self, escenario: Escenario, clientes: Iterable[Cliente]):
        self.escenario = escenario
        self.clientes = list(clientes)
        self.clientes_por_tipo = self._agrupar_clientes()
        self.cajas_por_tipo = self._contar_cajas()

    def run(self) -> None:
        pygame.init()
        pantalla = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Simulación de cajas - Vista básica")
        clock = pygame.time.Clock()
        font = pygame.font.Font(None, 26)

        ejecutando = True
        while ejecutando:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    ejecutando = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    ejecutando = False

            pantalla.fill(BACKGROUND)
            self._dibujar_textos(pantalla, font)
            self._dibujar_cajas(pantalla, font)
            self._dibujar_colas(pantalla)

            pygame.display.flip()
            clock.tick(30)

        pygame.quit()

    def _dibujar_textos(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        titulo = font.render(
            f"Escenario: {self.escenario.nombre}", True, COLORS["texto"]
        )
        surface.blit(titulo, (20, 20))

        abandonos = sum(1 for c in self.clientes if c.abandono)
        procesados = sum(1 for c in self.clientes if not c.abandono)
        texto_stats = font.render(
            f"Procesados: {procesados} | Abandonos: {abandonos}",
            True,
            COLORS["texto"],
        )
        surface.blit(texto_stats, (20, 60))

    def _dibujar_cajas(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        for tipo, (x, y) in POSITIONS.items():
            cantidad = self.cajas_por_tipo.get(tipo, 0)
            color = COLORS.get(tipo, COLORS["cola"])
            label = font.render(tipo.capitalize(), True, COLORS["texto"])
            surface.blit(label, (x, y - 40))

            for idx in range(cantidad):
                rect = pygame.Rect(x + idx * 60, y, 50, 40)
                pygame.draw.rect(surface, color, rect, border_radius=6)

    def _dibujar_colas(self, surface: pygame.Surface) -> None:
        radio = 8
        separacion = 20
        for tipo, clientes in self.clientes_por_tipo.items():
            if tipo not in POSITIONS:
                continue
            base_x, y = POSITIONS[tipo]
            base_x += 250
            for idx, cliente in enumerate(clientes[:25]):
                color = COLORS.get(tipo, COLORS["cola"])
                x = base_x + (idx % 25) * separacion
                pygame.draw.circle(surface, color, (x, y + 20), radio)

    def _agrupar_clientes(self) -> Dict[str, List[Cliente]]:
        grupos: Dict[str, List[Cliente]] = defaultdict(list)
        for cliente in self.clientes:
            tipo = cliente.tipo_caja_asignada or "sin_caja"
            grupos[tipo].append(cliente)
        for lista in grupos.values():
            lista.sort(key=lambda c: c.tiempo_llegada)
        return grupos

    def _contar_cajas(self) -> Dict[str, int]:
        conteo = defaultdict(int)
        for caja in self.escenario.cajas:
            conteo[caja.tipo.value] += 1
        return conteo
