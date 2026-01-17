"""
Visualización de la simulación con Pygame
"""
import pygame
import os
import sys
from typing import Dict, List, Optional, Tuple

# Añadir path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    PYGAME_CONFIG, COLORES, TipoCaja, RESOURCE_DIR,
    ConfiguracionSimulacion, ConfiguracionCajas, ESCENARIOS
)
from simulacion.supermercado import Supermercado
from simulacion.cliente import Cliente
from simulacion.caja import Caja


class VisualizadorPygame:
    """Visualizador de la simulación usando Pygame"""
    
    def __init__(
        self,
        config_sim: ConfiguracionSimulacion = None,
        config_cajas: ConfiguracionCajas = None,
        politica: str = "balanceada",
        alta_demanda: bool = False
    ):
        self.config_sim = config_sim or ConfiguracionSimulacion()
        self.config_cajas = config_cajas or ConfiguracionCajas()
        self.politica = politica
        self.alta_demanda = alta_demanda
        
        # Pygame
        pygame.init()
        pygame.font.init()
        
        self.ancho = PYGAME_CONFIG["ancho_ventana"]
        self.alto = PYGAME_CONFIG["alto_ventana"]
        self.fps = PYGAME_CONFIG["fps"]
        
        self.pantalla = pygame.display.set_mode((self.ancho, self.alto))
        pygame.display.set_caption(PYGAME_CONFIG["titulo"])
        
        self.clock = pygame.time.Clock()
        self.running = True
        self.paused = False
        
        # Fuentes
        self.fuente_grande = pygame.font.SysFont("Arial", 24, bold=True)
        self.fuente_normal = pygame.font.SysFont("Arial", 18)
        self.fuente_pequena = pygame.font.SysFont("Arial", 14)
        
        # Cargar recursos
        self._cargar_recursos()
        
        # Simulación
        self.supermercado: Optional[Supermercado] = None
        self.velocidad = 0.4  # Multiplicador de velocidad (más lento)
        
        # Posiciones de cajas
        self.posiciones_cajas: Dict[int, Tuple[int, int]] = {}
        
        # Lista de escenarios y políticas para ciclar
        self.escenarios_nombres = list(ESCENARIOS.keys())
        self.escenario_actual = self.escenarios_nombres.index("hibrido_con_rapidas") if "hibrido_con_rapidas" in self.escenarios_nombres else 0
        self.politicas = ["balanceada", "cola_mas_corta", "prioridad_rapida", "preferir_humana"]
        self.politica_actual = 0
        self.started = False
        self.finished = False
    
    def _cargar_recursos(self):
        """Carga sprites y recursos gráficos"""
        self.sprites = {}
        
        try:
            # Cargar imagen de caja
            caja_path = os.path.join(RESOURCE_DIR, "caja.png")
            if os.path.exists(caja_path):
                img = pygame.image.load(caja_path)
                self.sprites["caja"] = pygame.transform.scale(img, (80, 80))
            else:
                self.sprites["caja"] = None
            
            # Cargar sprites de personajes
            for i in range(1, 4):
                personaje_path = os.path.join(RESOURCE_DIR, f"personaje {i}.png")
                if os.path.exists(personaje_path):
                    img = pygame.image.load(personaje_path)
                    self.sprites[f"cliente_{i}"] = pygame.transform.scale(img, (80, 80))
                else:
                    self.sprites[f"cliente_{i}"] = None
            
            # Cargar mapa de fondo (opcional)
            mapa_path = os.path.join(RESOURCE_DIR, "mapa.jpg")
            if os.path.exists(mapa_path):
                img = pygame.image.load(mapa_path)
                self.sprites["fondo"] = pygame.transform.scale(img, (self.ancho, self.alto))
            else:
                self.sprites["fondo"] = None
                
        except Exception as e:
            print(f"Error cargando recursos: {e}")
    
    def _calcular_posiciones_cajas(self):
        """Calcula posiciones de las cajas en pantalla"""
        if not self.supermercado:
            return
        
        num_cajas = len(self.supermercado.cajas)
        margen_inferior = 250
        margen_lateral = 100
        espacio_disponible = self.ancho - 2 * margen_lateral
        
        # Distribuir cajas horizontalmente en la parte inferior
        if num_cajas > 0:
            espacio_entre = espacio_disponible // (num_cajas + 1)
            
            for i, caja in enumerate(self.supermercado.cajas):
                x = margen_lateral + espacio_entre * (i + 1)
                y = self.alto - margen_inferior
                self.posiciones_cajas[caja.id] = (x, y)
                caja.pos_x = x
                caja.pos_y = y
    
    def iniciar_simulacion(self):
        """Inicializa la simulación"""
        self.supermercado = Supermercado(
            config_sim=self.config_sim,
            config_cajas=self.config_cajas,
            politica=self.politica,
            alta_demanda=self.alta_demanda
        )
        self.supermercado.iniciar()
        self._calcular_posiciones_cajas()
        self.paused = True
        self.started = False
        self.finished = False
        self.supermercado.pausar()
    
    def _dibujar_fondo(self):
        """Dibuja el fondo"""
        if self.sprites.get("fondo"):
            self.pantalla.blit(self.sprites["fondo"], (0, 0))
        else:
            self.pantalla.fill(COLORES["fondo"])
        
        # Overlay semi-transparente solo cuando está en pausa durante ejecución
        if self.started and self.paused and not self.finished:
            overlay = pygame.Surface((self.ancho, self.alto), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, 50))
            self.pantalla.blit(overlay, (0, 0))
    
    def _dibujar_caja(self, caja: Caja):
        """Dibuja una caja registradora"""
        x, y = self.posiciones_cajas.get(caja.id, (0, 0))
        
        # Color según tipo
        color = COLORES[caja.tipo]
        
        # Dibujar base de caja
        rect = pygame.Rect(x - 40, y - 40, 80, 80)
        pygame.draw.rect(self.pantalla, color, rect, border_radius=10)
        pygame.draw.rect(self.pantalla, (0, 0, 0), rect, 3, border_radius=10)
        
        # Sprite de caja si existe
        if self.sprites.get("caja"):
            self.pantalla.blit(self.sprites["caja"], (x - 40, y - 40))
        
        # Indicador de ocupación
        if caja.esta_ocupada():
            pygame.draw.circle(self.pantalla, (46, 204, 113), (x + 30, y + 30), 8)
        else:
            pygame.draw.circle(self.pantalla, (149, 165, 166), (x + 30, y + 30), 8)
        
        # Número de caja
        texto = self.fuente_pequena.render(f"#{caja.id + 1}", True, (255, 255, 255))
        self.pantalla.blit(texto, (x - texto.get_width() // 2, y - 10))
        
        # Tipo de caja
        tipo_texto = caja.tipo.value.upper()[:3]
        texto_tipo = self.fuente_pequena.render(tipo_texto, True, (255, 255, 255))
        self.pantalla.blit(texto_tipo, (x - texto_tipo.get_width() // 2, y + 10))
        
        # Contador de cola
        cola = caja.longitud_cola()
        if cola > 0:
            texto_cola = self.fuente_normal.render(f"Cola: {cola}", True, COLORES["texto"])
            self.pantalla.blit(texto_cola, (x - texto_cola.get_width() // 2, y - 60))
    
    def _dibujar_cola(self, caja: Caja):
        """Dibuja los clientes en cola (hacia arriba desde la caja)"""
        x, y = self.posiciones_cajas.get(caja.id, (0, 0))
        
        # Dibujar clientes en cola visual (hacia arriba)
        max_visibles = 8
        for i, cliente in enumerate(caja.cola_visual[:max_visibles]):
            cliente_y = y - 100 - i * 45  # Hacia arriba
            
            # Sprite o círculo
            sprite_key = f"cliente_{cliente.sprite_index}"
            if self.sprites.get(sprite_key):
                self.pantalla.blit(self.sprites[sprite_key], (x - 32, cliente_y))
            else:
                pygame.draw.circle(self.pantalla, COLORES["cliente"], (x, cliente_y + 30), 24)
            
            # Número de productos
            texto = self.fuente_pequena.render(str(cliente.num_productos), True, COLORES["texto"])
            self.pantalla.blit(texto, (x + 38, cliente_y + 12))
        
        # Indicador de más clientes
        if len(caja.cola_visual) > max_visibles:
            texto = self.fuente_pequena.render(f"+{len(caja.cola_visual) - max_visibles} mas", True, COLORES["texto"])
            self.pantalla.blit(texto, (x - 25, y - 100 - max_visibles * 45))
        
        # Cliente siendo atendido: se resalta directamente en panel, sin círculo adicional
    
    def _dibujar_panel_info(self):
        """Dibuja panel de información y estadísticas"""
        if not self.supermercado:
            return
        mostrar_panel = (not self.started) or self.paused or self.finished
        if not mostrar_panel:
            return
        
        estado = self.supermercado.obtener_estado()
        stats = self.supermercado.estadisticas
        
        # Panel superior
        panel = pygame.Rect(10, 10, self.ancho - 20, 140)
        pygame.draw.rect(self.pantalla, (255, 255, 255, 200), panel, border_radius=10)
        pygame.draw.rect(self.pantalla, COLORES["texto"], panel, 2, border_radius=10)
        
        # Título
        titulo = self.fuente_grande.render("SuperLatino - Simulacion de Cajas", True, COLORES["texto"])
        self.pantalla.blit(titulo, (20, 20))
        y_cursor = 20
        if not self.started:
            estado_texto_menu = "Presiona ESPACIO para iniciar, R reinicia"
            texto_menu = self.fuente_pequena.render(estado_texto_menu, True, (120, 120, 120))
            self.pantalla.blit(texto_menu, (20, 45))
            y_cursor = 70
        else:
            y_cursor = 45
        
        # Tiempo
        minutos = int(estado['tiempo'])
        horas = minutos // 60
        mins = minutos % 60
        tiempo_texto = f"Tiempo: {horas:02d}:{mins:02d}"
        texto = self.fuente_normal.render(tiempo_texto, True, COLORES["texto"])
        self.pantalla.blit(texto, (20, y_cursor))
        y_cursor += 25
        
        # Estado textual
        if not self.started:
            estado_texto = "Presiona ESPACIO para iniciar la simulacion"
        elif self.finished:
            estado_texto = "Simulacion terminada. Presiona R para reiniciar"
        elif self.paused:
            estado_texto = "Simulacion en pausa. ESPACIO para continuar"
        else:
            estado_texto = ""
        if estado_texto:
            texto_estado = self.fuente_normal.render(estado_texto, True, COLORES["texto"])
            self.pantalla.blit(texto_estado, (20, y_cursor))
            y_cursor += 25

        # Estadísticas en línea
        stats_linea = [
            f"Atendidos: {estado['clientes_atendidos']}",
            f"Abandonos: {estado['abandonos']}",
            f"Cola total: {estado['cola_total']}",
            f"Espera prom: {stats.tiempo_espera_promedio:.1f} min",
            f"Tasa abandono: {stats.tasa_abandono:.1f}%"
        ]
        
        x_offset = 20
        linea_y = max(y_cursor + 5, 120)
        for stat in stats_linea:
            texto = self.fuente_pequena.render(stat, True, COLORES["texto"])
            self.pantalla.blit(texto, (x_offset, linea_y))
            x_offset += texto.get_width() + 30
        
        # Configuración actual
        config_texto = f"Política: {self.politica} | Cajas: {self.config_cajas.descripcion()} | {'ALTA DEMANDA' if self.alta_demanda else 'Normal'}"
        texto = self.fuente_pequena.render(config_texto, True, (100, 100, 100))
        self.pantalla.blit(texto, (self.ancho - texto.get_width() - 20, 20))
        
        # Controles
        controles = "ESPACIO:Pausa | Flechas:Velocidad | R:Reiniciar | 1-4:Escenario | D:Demanda | P:Politica"
        texto = self.fuente_pequena.render(controles, True, (100, 100, 100))
        self.pantalla.blit(texto, (self.ancho - texto.get_width() - 20, 45))
        
        # Escenario actual
        escenario_nombre = self.escenarios_nombres[self.escenario_actual] if self.escenario_actual < len(self.escenarios_nombres) else "?"
        esc_texto = f"[{self.escenario_actual + 1}] {escenario_nombre}"
        texto = self.fuente_pequena.render(esc_texto, True, (100, 100, 100))
        self.pantalla.blit(texto, (self.ancho - texto.get_width() - 20, 95))
        
        # Velocidad
        vel_texto = f"Velocidad: {self.velocidad:.1f}x"
        texto = self.fuente_pequena.render(vel_texto, True, COLORES["texto"])
        self.pantalla.blit(texto, (self.ancho - texto.get_width() - 20, 70))
    
    def _dibujar_leyenda(self):
        """Dibuja leyenda de tipos de caja"""
        y_base = self.alto - 80
        x = 20
        
        leyenda = [
            (TipoCaja.HUMANA, "Caja Humana"),
            (TipoCaja.AUTOMATICA, "Self-Checkout"),
            (TipoCaja.RAPIDA, "Caja Rápida (≤10 prod)"),
        ]
        
        for tipo, nombre in leyenda:
            color = COLORES[tipo]
            pygame.draw.rect(self.pantalla, color, (x, y_base, 20, 20), border_radius=3)
            texto = self.fuente_pequena.render(nombre, True, COLORES["texto"])
            self.pantalla.blit(texto, (x + 30, y_base + 2))
            x += texto.get_width() + 60
    
    def _dibujar_pausa(self):
        """Dibuja overlay de pausa"""
        if self.paused and self.started and not self.finished:
            overlay = pygame.Surface((self.ancho, self.alto), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))
            self.pantalla.blit(overlay, (0, 0))
            
            texto = self.fuente_grande.render("PAUSADO", True, (255, 255, 255))
            x = (self.ancho - texto.get_width()) // 2
            y = (self.alto - texto.get_height()) // 2
            self.pantalla.blit(texto, (x, y))
    
    def _manejar_eventos(self):
        """Procesa eventos de teclado y mouse"""
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.running = False
            
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    self.running = False
                
                elif evento.key == pygame.K_SPACE:
                    if not self.started and self.supermercado:
                        self.started = True
                        self.finished = False
                        self.paused = False
                        self.supermercado.reanudar()
                    else:
                        self.paused = not self.paused
                        if self.supermercado:
                            if self.paused:
                                self.supermercado.pausar()
                            else:
                                self.supermercado.reanudar()
                
                elif evento.key == pygame.K_UP:
                    self.velocidad = min(10.0, self.velocidad + 0.5)
                
                elif evento.key == pygame.K_DOWN:
                    self.velocidad = max(0.2, self.velocidad - 0.3)
                
                elif evento.key == pygame.K_r:
                    self.iniciar_simulacion()
                
                # Cambiar escenario con teclas 1-4
                elif evento.key == pygame.K_1:
                    self._cambiar_escenario(0)
                elif evento.key == pygame.K_2:
                    self._cambiar_escenario(1)
                elif evento.key == pygame.K_3:
                    self._cambiar_escenario(2)
                elif evento.key == pygame.K_4:
                    self._cambiar_escenario(3)
                
                # Alternar demanda con D
                elif evento.key == pygame.K_d:
                    self.alta_demanda = not self.alta_demanda
                    self.iniciar_simulacion()
                
                # Ciclar política con P
                elif evento.key == pygame.K_p:
                    self.politica_actual = (self.politica_actual + 1) % len(self.politicas)
                    self.politica = self.politicas[self.politica_actual]
                    self.iniciar_simulacion()
    
    def _cambiar_escenario(self, indice: int):
        """Cambia al escenario indicado y reinicia"""
        if 0 <= indice < len(self.escenarios_nombres):
            self.escenario_actual = indice
            nombre = self.escenarios_nombres[indice]
            self.config_cajas = ESCENARIOS[nombre]
            self.iniciar_simulacion()
    
    def ejecutar(self):
        """Loop principal de visualización"""
        self.iniciar_simulacion()
        
        while self.running:
            self._manejar_eventos()
            
            # Avanzar simulación
            if not self.paused and self.supermercado:
                delta = (1.0 / self.fps) * self.velocidad * 60  # Convertir a minutos simulados
                self.supermercado.paso(delta)
                
                # Verificar fin de simulación
                if self.supermercado.env.now >= self.config_sim.duracion_simulacion:
                    self.finished = True
                    self.paused = True
                    self.supermercado.pausar()
            
            # Dibujar
            self._dibujar_fondo()
            
            if self.supermercado:
                for caja in self.supermercado.cajas:
                    self._dibujar_caja(caja)
                    self._dibujar_cola(caja)
            
            self._dibujar_panel_info()
            self._dibujar_leyenda()
            self._dibujar_pausa()
            
            pygame.display.flip()
            self.clock.tick(self.fps)
        
        pygame.quit()
        
        # Retornar estadísticas finales
        if self.supermercado:
            return self.supermercado.estadisticas
        return None


def main():
    """Punto de entrada para visualización Pygame"""
    # Configuración por defecto
    config_cajas = ESCENARIOS["hibrido_con_rapidas"]
    
    visualizador = VisualizadorPygame(
        config_cajas=config_cajas,
        politica="balanceada",
        alta_demanda=False
    )
    
    stats = visualizador.ejecutar()
    
    if stats:
        print("\n" + "=" * 50)
        print("RESULTADOS DE LA SIMULACIÓN")
        print("=" * 50)
        for key, value in stats.resumen().items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
