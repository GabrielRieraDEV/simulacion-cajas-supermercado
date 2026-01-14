"""
Comparador de escenarios de simulación
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List, Tuple
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from config import (
    ConfiguracionSimulacion, ConfiguracionCajas, 
    CostosOperacionales, ESCENARIOS
)
from simulacion.supermercado import Supermercado
from simulacion.estadisticas import EstadisticasSimulacion


class ComparadorEscenarios:
    """Ejecuta y compara múltiples escenarios de simulación"""
    
    def __init__(self, duracion_simulacion: float = 480.0):
        self.duracion = duracion_simulacion
        self.resultados: Dict[str, Dict] = {}
        self.costos = CostosOperacionales()
    
    def ejecutar_escenario(
        self,
        nombre: str,
        config_cajas: ConfiguracionCajas,
        politica: str = "balanceada",
        alta_demanda: bool = False,
        repeticiones: int = 1
    ) -> Dict:
        """Ejecuta un escenario (opcionalmente múltiples veces para promedio)"""
        
        resultados_rep = []
        
        for i in range(repeticiones):
            config_sim = ConfiguracionSimulacion(duracion_simulacion=self.duracion)
            
            supermercado = Supermercado(
                config_sim=config_sim,
                config_cajas=config_cajas,
                politica=politica,
                alta_demanda=alta_demanda
            )
            
            stats = supermercado.ejecutar()
            
            duracion_horas = self.duracion / 60.0
            costo_beneficio = stats.calcular_costo_beneficio(
                config_cajas, duracion_horas, self.costos
            )
            
            resultados_rep.append({
                'stats': stats,
                'costo_beneficio': costo_beneficio
            })
        
        # Promediar si hay múltiples repeticiones
        if repeticiones > 1:
            resultado_final = self._promediar_resultados(resultados_rep)
        else:
            resultado_final = resultados_rep[0]
        
        resultado_final['nombre'] = nombre
        resultado_final['config_cajas'] = config_cajas
        resultado_final['politica'] = politica
        resultado_final['alta_demanda'] = alta_demanda
        
        self.resultados[nombre] = resultado_final
        return resultado_final
    
    def _promediar_resultados(self, resultados: List[Dict]) -> Dict:
        """Promedia resultados de múltiples ejecuciones"""
        # Tomar el último stats (para el DataFrame)
        stats = resultados[-1]['stats']
        
        # Promediar métricas numéricas
        clientes_atendidos = np.mean([r['stats'].clientes_atendidos for r in resultados])
        clientes_abandonaron = np.mean([r['stats'].clientes_abandonaron for r in resultados])
        tiempo_espera = np.mean([r['stats'].tiempo_espera_promedio for r in resultados])
        
        # Promediar costo-beneficio
        costo_beneficio = {}
        for key in resultados[0]['costo_beneficio'].keys():
            costo_beneficio[key] = np.mean([r['costo_beneficio'][key] for r in resultados])
        
        return {
            'stats': stats,
            'costo_beneficio': costo_beneficio,
            'promedios': {
                'clientes_atendidos': clientes_atendidos,
                'clientes_abandonaron': clientes_abandonaron,
                'tiempo_espera_promedio': tiempo_espera
            }
        }
    
    def ejecutar_todos_escenarios(
        self,
        alta_demanda: bool = False,
        politica: str = "balanceada"
    ):
        """Ejecuta todos los escenarios predefinidos"""
        for nombre, config in ESCENARIOS.items():
            print(f"Ejecutando escenario: {nombre}...")
            self.ejecutar_escenario(
                nombre=nombre,
                config_cajas=config,
                politica=politica,
                alta_demanda=alta_demanda
            )
        print("✅ Todos los escenarios completados")
    
    def comparar_politicas(
        self,
        config_cajas: ConfiguracionCajas,
        alta_demanda: bool = False
    ):
        """Compara diferentes políticas de asignación"""
        politicas = ["cola_mas_corta", "prioridad_rapida", "preferir_humana", "balanceada"]
        
        for politica in politicas:
            nombre = f"politica_{politica}"
            print(f"Probando política: {politica}...")
            self.ejecutar_escenario(
                nombre=nombre,
                config_cajas=config_cajas,
                politica=politica,
                alta_demanda=alta_demanda
            )
    
    def obtener_tabla_comparativa(self) -> pd.DataFrame:
        """Genera tabla comparativa de resultados"""
        datos = []
        
        for nombre, resultado in self.resultados.items():
            stats = resultado['stats']
            cb = resultado['costo_beneficio']
            config = resultado['config_cajas']
            
            datos.append({
                'Escenario': nombre,
                'Cajas Humanas': config.cajas_humanas,
                'Cajas Auto': config.cajas_automaticas,
                'Cajas Rápidas': config.cajas_rapidas,
                'Política': resultado['politica'],
                'Alta Demanda': '✓' if resultado['alta_demanda'] else '',
                'Clientes Atendidos': stats.clientes_atendidos,
                'Abandonos': stats.clientes_abandonaron,
                'Tasa Abandono (%)': round(stats.tasa_abandono, 1),
                'Espera Promedio (min)': round(stats.tiempo_espera_promedio, 2),
                'Espera Máxima (min)': round(stats.tiempo_espera_maximo, 2),
                'Throughput (cli/hora)': round(cb['throughput_hora'], 1),
                'Costo/hora ($)': round(cb['costo_operacional_hora'], 2),
                'Costo/cliente ($)': round(cb['costo_por_cliente'], 2),
                'Eficiencia': round(cb['eficiencia'], 2)
            })
        
        return pd.DataFrame(datos)
    
    def obtener_mejor_escenario(self, criterio: str = "tiempo_espera") -> Tuple[str, Dict]:
        """Encuentra el mejor escenario según un criterio"""
        if not self.resultados:
            return None, None
        
        if criterio == "tiempo_espera":
            mejor = min(self.resultados.items(), 
                       key=lambda x: x[1]['stats'].tiempo_espera_promedio)
        elif criterio == "abandono":
            mejor = min(self.resultados.items(),
                       key=lambda x: x[1]['stats'].tasa_abandono)
        elif criterio == "throughput":
            mejor = max(self.resultados.items(),
                       key=lambda x: x[1]['costo_beneficio']['throughput_hora'])
        elif criterio == "costo":
            mejor = min(self.resultados.items(),
                       key=lambda x: x[1]['costo_beneficio']['costo_operacional_hora'])
        elif criterio == "eficiencia":
            mejor = max(self.resultados.items(),
                       key=lambda x: x[1]['costo_beneficio']['eficiencia'])
        else:
            mejor = list(self.resultados.items())[0]
        
        return mejor
    
    def generar_recomendaciones(self) -> List[str]:
        """Genera recomendaciones basadas en los resultados"""
        if not self.resultados:
            return ["No hay resultados para analizar"]
        
        recomendaciones = []
        
        # Mejor para tiempo de espera
        nombre, datos = self.obtener_mejor_escenario("tiempo_espera")
        recomendaciones.append(
            f"🕐 Para minimizar tiempo de espera: {nombre} "
            f"({datos['stats'].tiempo_espera_promedio:.1f} min promedio)"
        )
        
        # Mejor para abandono
        nombre, datos = self.obtener_mejor_escenario("abandono")
        recomendaciones.append(
            f"🚶 Para reducir abandonos: {nombre} "
            f"({datos['stats'].tasa_abandono:.1f}% tasa de abandono)"
        )
        
        # Mejor costo-eficiencia
        nombre, datos = self.obtener_mejor_escenario("eficiencia")
        recomendaciones.append(
            f"💰 Mejor relación costo-eficiencia: {nombre} "
            f"(eficiencia: {datos['costo_beneficio']['eficiencia']:.2f})"
        )
        
        # Mejor throughput
        nombre, datos = self.obtener_mejor_escenario("throughput")
        recomendaciones.append(
            f"📈 Mayor capacidad de atención: {nombre} "
            f"({datos['costo_beneficio']['throughput_hora']:.0f} clientes/hora)"
        )
        
        return recomendaciones


def main():
    """Ejemplo de uso del comparador"""
    comparador = ComparadorEscenarios(duracion_simulacion=480.0)
    
    print("=" * 60)
    print("ANÁLISIS COMPARATIVO DE ESCENARIOS - SuperLatino")
    print("=" * 60)
    
    # Ejecutar escenarios en demanda normal
    print("\n📊 Ejecutando simulaciones en demanda NORMAL...\n")
    comparador.ejecutar_todos_escenarios(alta_demanda=False)
    
    # Mostrar tabla
    print("\n" + "=" * 60)
    print("RESULTADOS - DEMANDA NORMAL")
    print("=" * 60)
    tabla = comparador.obtener_tabla_comparativa()
    print(tabla.to_string(index=False))
    
    # Recomendaciones
    print("\n" + "=" * 60)
    print("RECOMENDACIONES")
    print("=" * 60)
    for rec in comparador.generar_recomendaciones():
        print(f"  {rec}")
    
    # Guardar resultados
    tabla.to_csv("resultados_comparacion.csv", index=False)
    print("\n✅ Resultados guardados en 'resultados_comparacion.csv'")


if __name__ == "__main__":
    main()
