"""
Modelo de Cliente para la simulación
"""
import random
from dataclasses import dataclass, field
from typing import Optional
from config import ConfiguracionSimulacion, TipoCaja


@dataclass
class Cliente:
    """Representa un cliente en el supermercado"""
    
    id: int
    tiempo_llegada: float
    num_productos: int
    tolerancia_espera: float  # Tiempo máximo que esperará en cola
    
    # Estado del cliente
    tiempo_inicio_cola: Optional[float] = None
    tiempo_inicio_servicio: Optional[float] = None
    tiempo_fin_servicio: Optional[float] = None
    abandono: bool = False
    caja_asignada: Optional[int] = None
    tipo_caja_usada: Optional[TipoCaja] = None
    
    # Posición para visualización
    pos_x: float = 0.0
    pos_y: float = 0.0
    sprite_index: int = 0
    
    @classmethod
    def generar(cls, id: int, tiempo_llegada: float, config: ConfiguracionSimulacion) -> 'Cliente':
        """Genera un cliente con productos y tolerancia aleatorios"""
        num_productos = random.randint(
            config.productos_cliente_min,
            config.productos_cliente_max
        )
        tolerancia = random.uniform(
            config.tiempo_abandono_min,
            config.tiempo_abandono_max
        )
        sprite = random.randint(1, 3)  # 3 sprites disponibles
        
        return cls(
            id=id,
            tiempo_llegada=tiempo_llegada,
            num_productos=num_productos,
            tolerancia_espera=tolerancia,
            sprite_index=sprite
        )
    
    def puede_usar_caja_rapida(self, max_productos: int = 10) -> bool:
        """Verifica si puede usar caja rápida"""
        return self.num_productos <= max_productos
    
    def tiempo_espera(self, tiempo_actual: float) -> float:
        """Calcula tiempo de espera actual en cola"""
        if self.tiempo_inicio_cola is None:
            return 0.0
        if self.tiempo_inicio_servicio is not None:
            return self.tiempo_inicio_servicio - self.tiempo_inicio_cola
        return tiempo_actual - self.tiempo_inicio_cola
    
    def tiempo_total_sistema(self) -> Optional[float]:
        """Tiempo total desde llegada hasta salida"""
        if self.tiempo_fin_servicio is None:
            return None
        return self.tiempo_fin_servicio - self.tiempo_llegada
    
    def debe_abandonar(self, tiempo_actual: float) -> bool:
        """Verifica si el cliente debe abandonar por exceso de espera"""
        return self.tiempo_espera(tiempo_actual) >= self.tolerancia_espera
    
    def __repr__(self):
        estado = "abandonó" if self.abandono else "atendido" if self.tiempo_fin_servicio else "esperando"
        return f"Cliente({self.id}, productos={self.num_productos}, estado={estado})"
