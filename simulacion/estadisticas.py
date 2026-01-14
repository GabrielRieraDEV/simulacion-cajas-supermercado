"""
Sistema de recolección de estadísticas de la simulación
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from config import TipoCaja, ConfiguracionCajas, CostosOperacionales
import pandas as pd
import numpy as np


@dataclass
class RegistroCliente:
    """Registro de un cliente para análisis"""
    id: int
    tiempo_llegada: float
    tiempo_inicio_servicio: Optional[float]
    tiempo_fin_servicio: Optional[float]
    num_productos: int
    tipo_caja: Optional[str]
    caja_id: Optional[int]
    abandono: bool
    tiempo_espera: float
    tiempo_servicio: float
    tiempo_total: float


@dataclass
class EstadisticasSimulacion:
    """Recolector de estadísticas de la simulación"""
    
    registros: List[RegistroCliente] = field(default_factory=list)
    
    # Contadores en tiempo real
    clientes_totales: int = 0
    clientes_atendidos: int = 0
    clientes_abandonaron: int = 0
    
    # Métricas agregadas
    _tiempos_espera: List[float] = field(default_factory=list)
    _tiempos_servicio: List[float] = field(default_factory=list)
    _tiempos_sistema: List[float] = field(default_factory=list)
    
    # Histórico para gráficas en tiempo real
    historico_cola: List[tuple] = field(default_factory=list)  # (tiempo, longitud)
    historico_throughput: List[tuple] = field(default_factory=list)  # (tiempo, clientes/hora)
    
    def registrar_cliente(
        self,
        cliente,
        tipo_caja: Optional[TipoCaja] = None,
        caja_id: Optional[int] = None
    ):
        """Registra un cliente completado o que abandonó"""
        tiempo_espera = 0.0
        tiempo_servicio = 0.0
        tiempo_total = 0.0
        
        if cliente.tiempo_inicio_cola and cliente.tiempo_inicio_servicio:
            tiempo_espera = cliente.tiempo_inicio_servicio - cliente.tiempo_inicio_cola
        elif cliente.tiempo_inicio_cola and cliente.abandono:
            tiempo_espera = cliente.tolerancia_espera
        
        if cliente.tiempo_inicio_servicio and cliente.tiempo_fin_servicio:
            tiempo_servicio = cliente.tiempo_fin_servicio - cliente.tiempo_inicio_servicio
        
        if cliente.tiempo_fin_servicio:
            tiempo_total = cliente.tiempo_fin_servicio - cliente.tiempo_llegada
        
        registro = RegistroCliente(
            id=cliente.id,
            tiempo_llegada=cliente.tiempo_llegada,
            tiempo_inicio_servicio=cliente.tiempo_inicio_servicio,
            tiempo_fin_servicio=cliente.tiempo_fin_servicio,
            num_productos=cliente.num_productos,
            tipo_caja=tipo_caja.value if tipo_caja else None,
            caja_id=caja_id,
            abandono=cliente.abandono,
            tiempo_espera=tiempo_espera,
            tiempo_servicio=tiempo_servicio,
            tiempo_total=tiempo_total
        )
        
        self.registros.append(registro)
        self.clientes_totales += 1
        
        if cliente.abandono:
            self.clientes_abandonaron += 1
        else:
            self.clientes_atendidos += 1
            self._tiempos_espera.append(tiempo_espera)
            self._tiempos_servicio.append(tiempo_servicio)
            self._tiempos_sistema.append(tiempo_total)
    
    def registrar_estado_cola(self, tiempo: float, longitud_total: int):
        """Registra estado de colas para gráficas"""
        self.historico_cola.append((tiempo, longitud_total))
    
    def registrar_throughput(self, tiempo: float, clientes_hora: float):
        """Registra throughput para gráficas"""
        self.historico_throughput.append((tiempo, clientes_hora))
    
    # ==================== KPIs ====================
    
    @property
    def tiempo_espera_promedio(self) -> float:
        """Tiempo promedio de espera en cola (minutos)"""
        if not self._tiempos_espera:
            return 0.0
        return np.mean(self._tiempos_espera)
    
    @property
    def tiempo_espera_maximo(self) -> float:
        """Tiempo máximo de espera"""
        if not self._tiempos_espera:
            return 0.0
        return np.max(self._tiempos_espera)
    
    @property
    def tiempo_servicio_promedio(self) -> float:
        """Tiempo promedio de servicio"""
        if not self._tiempos_servicio:
            return 0.0
        return np.mean(self._tiempos_servicio)
    
    @property
    def tiempo_sistema_promedio(self) -> float:
        """Tiempo promedio total en el sistema"""
        if not self._tiempos_sistema:
            return 0.0
        return np.mean(self._tiempos_sistema)
    
    @property
    def tasa_abandono(self) -> float:
        """Porcentaje de clientes que abandonaron"""
        if self.clientes_totales == 0:
            return 0.0
        return (self.clientes_abandonaron / self.clientes_totales) * 100
    
    def throughput(self, duracion_horas: float) -> float:
        """Clientes atendidos por hora"""
        if duracion_horas == 0:
            return 0.0
        return self.clientes_atendidos / duracion_horas
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convierte registros a DataFrame para análisis"""
        if not self.registros:
            return pd.DataFrame()
        
        data = [
            {
                'id': r.id,
                'tiempo_llegada': r.tiempo_llegada,
                'tiempo_espera': r.tiempo_espera,
                'tiempo_servicio': r.tiempo_servicio,
                'tiempo_total': r.tiempo_total,
                'num_productos': r.num_productos,
                'tipo_caja': r.tipo_caja,
                'caja_id': r.caja_id,
                'abandono': r.abandono
            }
            for r in self.registros
        ]
        return pd.DataFrame(data)
    
    def resumen(self) -> Dict:
        """Genera resumen de estadísticas"""
        return {
            'clientes_totales': self.clientes_totales,
            'clientes_atendidos': self.clientes_atendidos,
            'clientes_abandonaron': self.clientes_abandonaron,
            'tasa_abandono': f"{self.tasa_abandono:.1f}%",
            'tiempo_espera_promedio': f"{self.tiempo_espera_promedio:.2f} min",
            'tiempo_espera_maximo': f"{self.tiempo_espera_maximo:.2f} min",
            'tiempo_servicio_promedio': f"{self.tiempo_servicio_promedio:.2f} min",
            'tiempo_sistema_promedio': f"{self.tiempo_sistema_promedio:.2f} min",
        }
    
    def calcular_costo_beneficio(
        self,
        config_cajas: ConfiguracionCajas,
        duracion_horas: float,
        costos: CostosOperacionales = None
    ) -> Dict:
        """Calcula métricas de costo-beneficio"""
        if costos is None:
            costos = CostosOperacionales()
        
        costo_hora = costos.calcular_costo_hora(config_cajas)
        costo_total = costo_hora * duracion_horas
        
        throughput_hora = self.throughput(duracion_horas)
        costo_por_cliente = costo_total / max(1, self.clientes_atendidos)
        
        # Estimación de pérdida por abandonos (ingreso promedio por cliente)
        ingreso_promedio_cliente = 25.0  # USD estimado
        perdida_abandonos = self.clientes_abandonaron * ingreso_promedio_cliente
        
        return {
            'costo_operacional_hora': costo_hora,
            'costo_operacional_total': costo_total,
            'throughput_hora': throughput_hora,
            'costo_por_cliente': costo_por_cliente,
            'perdida_por_abandonos': perdida_abandonos,
            'costo_total_real': costo_total + perdida_abandonos,
            'eficiencia': throughput_hora / max(1, costo_hora)
        }
