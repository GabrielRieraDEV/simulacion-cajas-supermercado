"""
Configuración global del sistema de simulación SuperLatino
"""
import os
from dataclasses import dataclass, field
from typing import Dict
from enum import Enum

# Rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCE_DIR = os.path.join(BASE_DIR, "resource")

# ==================== TIPOS DE CAJAS ====================
class TipoCaja(Enum):
    HUMANA = "humana"           # Caja tradicional con cajero
    AUTOMATICA = "automatica"   # Self-checkout
    RAPIDA = "rapida"           # Express (≤10 productos)

# ==================== COLORES PARA VISUALIZACIÓN ====================
COLORES = {
    TipoCaja.HUMANA: (52, 152, 219),      # Azul
    TipoCaja.AUTOMATICA: (46, 204, 113),  # Verde
    TipoCaja.RAPIDA: (241, 196, 15),      # Amarillo
    "fondo": (245, 245, 245),
    "texto": (44, 62, 80),
    "cliente": (155, 89, 182),
    "abandono": (231, 76, 60),
}

# ==================== PARÁMETROS DE SIMULACIÓN ====================
@dataclass
class ConfiguracionSimulacion:
    """Parámetros de la simulación"""
    
    # Tiempo de simulación (minutos)
    duracion_simulacion: float = 480.0  # 8 horas
    
    # Tasa de llegada de clientes (clientes/minuto) - Lambda para Poisson
    tasa_llegada_normal: float = 0.5      # ~30 clientes/hora en día normal
    tasa_llegada_alta: float = 1.5        # ~90 clientes/hora en días pico
    
    # Tiempo de servicio base (minutos) - Media para Exponencial
    tiempo_servicio_humana: float = 3.0     # 3 min promedio
    tiempo_servicio_automatica: float = 4.0  # 4 min (cliente sin experiencia)
    tiempo_servicio_rapida: float = 1.5      # 1.5 min (pocos productos)
    
    # Factor de tiempo por producto (segundos adicionales)
    tiempo_por_producto: float = 0.1  # 6 segundos por producto
    
    # Límites de productos
    max_productos_caja_rapida: int = 10
    productos_cliente_min: int = 1
    productos_cliente_max: int = 50
    
    # Tolerancia de espera (minutos antes de abandonar)
    tiempo_abandono_min: float = 5.0
    tiempo_abandono_max: float = 15.0
    
    # Velocidad de simulación para visualización
    velocidad_simulacion: float = 1.0  # 1.0 = tiempo real


@dataclass
class ConfiguracionCajas:
    """Configuración del número de cajas por tipo"""
    cajas_humanas: int = 4
    cajas_automaticas: int = 2
    cajas_rapidas: int = 1
    
    def total_cajas(self) -> int:
        return self.cajas_humanas + self.cajas_automaticas + self.cajas_rapidas
    
    def descripcion(self) -> str:
        return f"H:{self.cajas_humanas} A:{self.cajas_automaticas} R:{self.cajas_rapidas}"


# ==================== ESCENARIOS PREDEFINIDOS ====================
ESCENARIOS = {
    "100_tradicional": ConfiguracionCajas(cajas_humanas=6, cajas_automaticas=0, cajas_rapidas=0),
    "50_50_hibrido": ConfiguracionCajas(cajas_humanas=3, cajas_automaticas=3, cajas_rapidas=0),
    "hibrido_con_rapidas": ConfiguracionCajas(cajas_humanas=3, cajas_automaticas=2, cajas_rapidas=2),
    "automatizado": ConfiguracionCajas(cajas_humanas=1, cajas_automaticas=4, cajas_rapidas=2),
}

# ==================== COSTOS OPERACIONALES ====================
@dataclass
class CostosOperacionales:
    """Costos por hora de operación"""
    costo_hora_cajero: float = 5.0        # USD/hora por cajero
    costo_hora_caja_auto: float = 1.0     # USD/hora mantenimiento
    costo_hora_supervision: float = 8.0    # Un supervisor para cajas auto
    cajas_auto_por_supervisor: int = 4     # Cuántas cajas auto supervisa una persona
    
    def calcular_costo_hora(self, config: ConfiguracionCajas) -> float:
        costo_humanas = config.cajas_humanas * self.costo_hora_cajero
        costo_rapidas = config.cajas_rapidas * self.costo_hora_cajero
        costo_auto = config.cajas_automaticas * self.costo_hora_caja_auto
        
        # Supervisores necesarios
        supervisores = (config.cajas_automaticas + self.cajas_auto_por_supervisor - 1) // self.cajas_auto_por_supervisor
        costo_supervision = supervisores * self.costo_hora_supervision
        
        return costo_humanas + costo_rapidas + costo_auto + costo_supervision


# ==================== CONFIGURACIÓN DE PYGAME ====================
PYGAME_CONFIG = {
    "ancho_ventana": 1280,
    "alto_ventana": 720,
    "fps": 60,
    "titulo": "SuperLatino - Simulación de Cajas",
}

# ==================== CONFIGURACIÓN DE DASH ====================
DASH_CONFIG = {
    "host": "127.0.0.1",
    "port": 8030,
    "debug": False,
}
