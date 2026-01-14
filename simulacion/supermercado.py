"""
Motor principal de simulación del supermercado usando SimPy
"""
import simpy
import random
from typing import List, Optional, Callable, Dict
from config import (
    TipoCaja, ConfiguracionSimulacion, ConfiguracionCajas
)
from .cliente import Cliente
from .caja import Caja
from .estadisticas import EstadisticasSimulacion


class PoliticaAsignacion:
    """Políticas de asignación de clientes a cajas"""
    
    @staticmethod
    def cola_mas_corta(cajas: List[Caja], cliente: Cliente) -> Optional[Caja]:
        """Asigna a la caja con cola más corta que pueda atender"""
        cajas_validas = [c for c in cajas if c.puede_atender(cliente)]
        if not cajas_validas:
            return None
        return min(cajas_validas, key=lambda c: c.longitud_cola())
    
    @staticmethod
    def prioridad_rapida(cajas: List[Caja], cliente: Cliente, max_productos: int = 10) -> Optional[Caja]:
        """Prioriza cajas rápidas para clientes con pocos productos"""
        if cliente.puede_usar_caja_rapida(max_productos):
            cajas_rapidas = [c for c in cajas if c.tipo == TipoCaja.RAPIDA]
            if cajas_rapidas:
                mejor = min(cajas_rapidas, key=lambda c: c.longitud_cola())
                # Solo usar rápida si la cola no es muy larga
                if mejor.longitud_cola() <= 3:
                    return mejor
        
        # Fallback a cola más corta
        return PoliticaAsignacion.cola_mas_corta(cajas, cliente)
    
    @staticmethod
    def preferir_humana(cajas: List[Caja], cliente: Cliente) -> Optional[Caja]:
        """Clientes con muchos productos prefieren cajas humanas"""
        if cliente.num_productos > 20:
            cajas_humanas = [c for c in cajas if c.tipo == TipoCaja.HUMANA]
            if cajas_humanas:
                mejor = min(cajas_humanas, key=lambda c: c.longitud_cola())
                if mejor.longitud_cola() <= 5:
                    return mejor
        
        return PoliticaAsignacion.cola_mas_corta(cajas, cliente)
    
    @staticmethod
    def balanceada(cajas: List[Caja], cliente: Cliente) -> Optional[Caja]:
        """Política balanceada considerando tipo de cliente y caja"""
        # Clientes con ≤10 productos → priorizar rápidas
        if cliente.num_productos <= 10:
            return PoliticaAsignacion.prioridad_rapida(cajas, cliente)
        
        # Clientes con muchos productos → preferir humanas
        if cliente.num_productos > 25:
            return PoliticaAsignacion.preferir_humana(cajas, cliente)
        
        # Resto → cola más corta
        return PoliticaAsignacion.cola_mas_corta(cajas, cliente)


class Supermercado:
    """Simulación del supermercado SuperLatino"""
    
    def __init__(
        self,
        config_sim: ConfiguracionSimulacion = None,
        config_cajas: ConfiguracionCajas = None,
        politica: str = "balanceada",
        alta_demanda: bool = False
    ):
        self.config_sim = config_sim or ConfiguracionSimulacion()
        self.config_cajas = config_cajas or ConfiguracionCajas()
        self.alta_demanda = alta_demanda
        
        # Seleccionar política
        self.politica = self._seleccionar_politica(politica)
        self.nombre_politica = politica
        
        # SimPy environment
        self.env: Optional[simpy.Environment] = None
        
        # Componentes
        self.cajas: List[Caja] = []
        self.clientes_en_sistema: List[Cliente] = []
        self.estadisticas = EstadisticasSimulacion()
        
        # Control
        self._cliente_id = 0
        self._running = False
        self._paused = False
        
        # Callbacks para visualización
        self.on_cliente_llega: Optional[Callable] = None
        self.on_cliente_asignado: Optional[Callable] = None
        self.on_cliente_atendido: Optional[Callable] = None
        self.on_cliente_abandona: Optional[Callable] = None
        self.on_tick: Optional[Callable] = None
    
    def _seleccionar_politica(self, nombre: str) -> Callable:
        """Selecciona función de política"""
        politicas = {
            "cola_mas_corta": PoliticaAsignacion.cola_mas_corta,
            "prioridad_rapida": PoliticaAsignacion.prioridad_rapida,
            "preferir_humana": PoliticaAsignacion.preferir_humana,
            "balanceada": PoliticaAsignacion.balanceada,
        }
        return politicas.get(nombre, PoliticaAsignacion.balanceada)
    
    @property
    def tasa_llegada(self) -> float:
        """Tasa de llegada según demanda"""
        if self.alta_demanda:
            return self.config_sim.tasa_llegada_alta
        return self.config_sim.tasa_llegada_normal
    
    def _crear_cajas(self):
        """Inicializa las cajas según configuración"""
        self.cajas = []
        caja_id = 0
        
        # Cajas humanas
        for _ in range(self.config_cajas.cajas_humanas):
            caja = Caja(self.env, caja_id, TipoCaja.HUMANA, self.config_sim)
            self.cajas.append(caja)
            caja_id += 1
        
        # Cajas automáticas
        for _ in range(self.config_cajas.cajas_automaticas):
            caja = Caja(self.env, caja_id, TipoCaja.AUTOMATICA, self.config_sim)
            self.cajas.append(caja)
            caja_id += 1
        
        # Cajas rápidas
        for _ in range(self.config_cajas.cajas_rapidas):
            caja = Caja(self.env, caja_id, TipoCaja.RAPIDA, self.config_sim)
            self.cajas.append(caja)
            caja_id += 1
    
    def _proceso_llegada_clientes(self):
        """Proceso SimPy: genera llegadas de clientes (Poisson)"""
        while self._running:
            # Tiempo entre llegadas: exponencial (inverso de Poisson)
            tiempo_entre_llegadas = random.expovariate(self.tasa_llegada)
            yield self.env.timeout(tiempo_entre_llegadas)
            
            if not self._running:
                break
            
            # Crear cliente
            self._cliente_id += 1
            cliente = Cliente.generar(
                self._cliente_id,
                self.env.now,
                self.config_sim
            )
            
            self.clientes_en_sistema.append(cliente)
            
            if self.on_cliente_llega:
                self.on_cliente_llega(cliente)
            
            # Iniciar proceso de atención
            self.env.process(self._proceso_cliente(cliente))
    
    def _proceso_cliente(self, cliente: Cliente):
        """Proceso SimPy: cliente busca caja y es atendido"""
        # Seleccionar caja según política
        caja = self.politica(self.cajas, cliente)
        
        if caja is None:
            # No hay caja disponible (no debería pasar normalmente)
            cliente.abandono = True
            self.estadisticas.registrar_cliente(cliente)
            self.clientes_en_sistema.remove(cliente)
            return
        
        cliente.caja_asignada = caja.id
        cliente.tipo_caja_usada = caja.tipo
        cliente.tiempo_inicio_cola = self.env.now
        
        # Añadir a cola visual
        caja.cola_visual.append(cliente)
        
        if self.on_cliente_asignado:
            self.on_cliente_asignado(cliente, caja)
        
        # Proceso de espera y posible abandono
        with caja.recurso.request() as req:
            # Esperar turno o abandonar
            resultado = yield req | self.env.timeout(cliente.tolerancia_espera)
            
            if req not in resultado:
                # El cliente abandonó
                cliente.abandono = True
                if cliente in caja.cola_visual:
                    caja.cola_visual.remove(cliente)
                
                self.estadisticas.registrar_cliente(cliente, caja.tipo, caja.id)
                
                if cliente in self.clientes_en_sistema:
                    self.clientes_en_sistema.remove(cliente)
                
                if self.on_cliente_abandona:
                    self.on_cliente_abandona(cliente, caja)
                return
            
            # Iniciar servicio
            cliente.tiempo_inicio_servicio = self.env.now
            if cliente in caja.cola_visual:
                caja.cola_visual.remove(cliente)
            caja.cliente_actual = cliente
            caja.registrar_inicio_servicio()
            
            # Tiempo de servicio
            tiempo_servicio = caja.calcular_tiempo_servicio(cliente)
            yield self.env.timeout(tiempo_servicio)
            
            # Fin del servicio
            cliente.tiempo_fin_servicio = self.env.now
            caja.cliente_actual = None
            caja.registrar_fin_servicio(tiempo_servicio)
            
            self.estadisticas.registrar_cliente(cliente, caja.tipo, caja.id)
            
            if cliente in self.clientes_en_sistema:
                self.clientes_en_sistema.remove(cliente)
            
            if self.on_cliente_atendido:
                self.on_cliente_atendido(cliente, caja)
    
    def _proceso_monitoreo(self):
        """Proceso SimPy: monitorea estado cada cierto tiempo"""
        intervalo = 1.0  # Cada minuto
        while self._running:
            yield self.env.timeout(intervalo)
            
            # Registrar longitud de colas
            total_cola = sum(c.longitud_cola() for c in self.cajas)
            self.estadisticas.registrar_estado_cola(self.env.now, total_cola)
            
            # Calcular throughput instantáneo
            if self.env.now > 0:
                horas = self.env.now / 60.0
                throughput = self.estadisticas.clientes_atendidos / horas
                self.estadisticas.registrar_throughput(self.env.now, throughput)
            
            if self.on_tick:
                self.on_tick(self.env.now)
    
    def iniciar(self):
        """Inicializa la simulación"""
        self.env = simpy.Environment()
        self._crear_cajas()
        self._running = True
        self._cliente_id = 0
        self.clientes_en_sistema = []
        self.estadisticas = EstadisticasSimulacion()
        
        # Iniciar procesos
        self.env.process(self._proceso_llegada_clientes())
        self.env.process(self._proceso_monitoreo())
    
    def ejecutar(self, duracion: float = None):
        """Ejecuta la simulación completa"""
        if duracion is None:
            duracion = self.config_sim.duracion_simulacion
        
        self.iniciar()
        self.env.run(until=duracion)
        self._running = False
        
        return self.estadisticas
    
    def paso(self, delta: float = 0.1):
        """Avanza la simulación un paso (para visualización)"""
        if self.env and self._running and not self._paused:
            self.env.run(until=self.env.now + delta)
    
    def pausar(self):
        """Pausa la simulación"""
        self._paused = True
    
    def reanudar(self):
        """Reanuda la simulación"""
        self._paused = False
    
    def detener(self):
        """Detiene la simulación"""
        self._running = False
    
    def longitud_cola_total(self) -> int:
        """Total de clientes en todas las colas"""
        return sum(c.longitud_cola() for c in self.cajas)
    
    def obtener_estado(self) -> Dict:
        """Obtiene estado actual para dashboard"""
        return {
            'tiempo': self.env.now if self.env else 0,
            'clientes_en_sistema': len(self.clientes_en_sistema),
            'cola_total': self.longitud_cola_total(),
            'clientes_atendidos': self.estadisticas.clientes_atendidos,
            'abandonos': self.estadisticas.clientes_abandonaron,
            'tiempo_espera_promedio': self.estadisticas.tiempo_espera_promedio,
            'tasa_abandono': self.estadisticas.tasa_abandono,
            'cajas': [
                {
                    'id': c.id,
                    'tipo': c.tipo.value,
                    'cola': c.longitud_cola(),
                    'ocupada': c.esta_ocupada(),
                    'atendidos': c.stats.clientes_atendidos
                }
                for c in self.cajas
            ]
        }
