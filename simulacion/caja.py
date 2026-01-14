"""
Modelo de Caja Registradora para la simulación
"""
import simpy
import random
from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING
from config import TipoCaja, ConfiguracionSimulacion

if TYPE_CHECKING:
    from .cliente import Cliente


@dataclass
class EstadisticasCaja:
    """Estadísticas de una caja individual"""
    clientes_atendidos: int = 0
    tiempo_ocupado: float = 0.0
    tiempo_ocioso: float = 0.0
    
    def ocupacion(self, tiempo_total: float) -> float:
        """Porcentaje de ocupación"""
        if tiempo_total == 0:
            return 0.0
        return (self.tiempo_ocupado / tiempo_total) * 100


class Caja:
    """Representa una caja registradora"""
    
    def __init__(
        self,
        env: simpy.Environment,
        id: int,
        tipo: TipoCaja,
        config: ConfiguracionSimulacion
    ):
        self.env = env
        self.id = id
        self.tipo = tipo
        self.config = config
        
        # Recurso SimPy (1 servidor por caja)
        self.recurso = simpy.Resource(env, capacity=1)
        
        # Cola de espera visual (para Pygame)
        self.cola_visual: List['Cliente'] = []
        
        # Cliente siendo atendido actualmente
        self.cliente_actual: Optional['Cliente'] = None
        
        # Estadísticas
        self.stats = EstadisticasCaja()
        self._ultimo_tiempo_libre: float = 0.0
        
        # Posición para visualización
        self.pos_x: float = 0.0
        self.pos_y: float = 0.0
    
    @property
    def tiempo_servicio_base(self) -> float:
        """Tiempo base de servicio según tipo de caja"""
        if self.tipo == TipoCaja.HUMANA:
            return self.config.tiempo_servicio_humana
        elif self.tipo == TipoCaja.AUTOMATICA:
            return self.config.tiempo_servicio_automatica
        else:  # RAPIDA
            return self.config.tiempo_servicio_rapida
    
    def calcular_tiempo_servicio(self, cliente: 'Cliente') -> float:
        """Calcula tiempo de servicio para un cliente específico"""
        # Tiempo base exponencial
        tiempo_base = random.expovariate(1.0 / self.tiempo_servicio_base)
        
        # Ajuste por cantidad de productos
        tiempo_productos = cliente.num_productos * self.config.tiempo_por_producto
        
        # Las cajas automáticas son más lentas para clientes inexpertos
        if self.tipo == TipoCaja.AUTOMATICA:
            factor_inexperiencia = random.uniform(1.0, 1.5)
            tiempo_base *= factor_inexperiencia
        
        return tiempo_base + tiempo_productos
    
    def longitud_cola(self) -> int:
        """Número de clientes esperando"""
        return len(self.recurso.queue)
    
    def esta_ocupada(self) -> bool:
        """Verifica si la caja está ocupada"""
        return len(self.recurso.users) > 0
    
    def puede_atender(self, cliente: 'Cliente') -> bool:
        """Verifica si puede atender al cliente"""
        if self.tipo == TipoCaja.RAPIDA:
            return cliente.puede_usar_caja_rapida(self.config.max_productos_caja_rapida)
        return True
    
    def registrar_inicio_servicio(self):
        """Registra inicio de atención"""
        tiempo_ocioso = self.env.now - self._ultimo_tiempo_libre
        self.stats.tiempo_ocioso += max(0, tiempo_ocioso)
    
    def registrar_fin_servicio(self, tiempo_servicio: float):
        """Registra fin de atención"""
        self.stats.clientes_atendidos += 1
        self.stats.tiempo_ocupado += tiempo_servicio
        self._ultimo_tiempo_libre = self.env.now
    
    def __repr__(self):
        return f"Caja({self.id}, tipo={self.tipo.value}, cola={self.longitud_cola()})"
