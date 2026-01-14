"""
Generador de reportes y gráficas con Matplotlib
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List, Optional
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from datetime import datetime

from config import COLORES, TipoCaja
from simulacion.estadisticas import EstadisticasSimulacion
from .comparador import ComparadorEscenarios


class GeneradorReportes:
    """Genera reportes visuales y documentos de análisis"""
    
    def __init__(self, directorio_salida: str = "reportes"):
        self.directorio = directorio_salida
        os.makedirs(directorio_salida, exist_ok=True)
        
        # Configurar estilo de matplotlib
        plt.style.use('seaborn-v0_8-whitegrid')
        plt.rcParams['figure.figsize'] = (12, 6)
        plt.rcParams['font.size'] = 10
    
    def graficar_histograma_espera(
        self,
        stats: EstadisticasSimulacion,
        titulo: str = "Distribución de Tiempos de Espera",
        guardar: bool = True
    ) -> plt.Figure:
        """Genera histograma de tiempos de espera"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if stats._tiempos_espera:
            ax.hist(stats._tiempos_espera, bins=25, color='#3498db', 
                   edgecolor='white', alpha=0.8)
            ax.axvline(stats.tiempo_espera_promedio, color='#e74c3c', 
                      linestyle='--', linewidth=2, 
                      label=f'Promedio: {stats.tiempo_espera_promedio:.1f} min')
        
        ax.set_xlabel('Tiempo de Espera (minutos)')
        ax.set_ylabel('Frecuencia')
        ax.set_title(titulo)
        ax.legend()
        
        plt.tight_layout()
        
        if guardar:
            path = os.path.join(self.directorio, "histograma_espera.png")
            plt.savefig(path, dpi=150, bbox_inches='tight')
            print(f"📊 Guardado: {path}")
        
        return fig
    
    def graficar_evolucion_colas(
        self,
        stats: EstadisticasSimulacion,
        titulo: str = "Evolución de la Longitud de Cola",
        guardar: bool = True
    ) -> plt.Figure:
        """Genera gráfica de evolución temporal de colas"""
        fig, ax = plt.subplots(figsize=(12, 5))
        
        if stats.historico_cola:
            tiempos = [h[0] for h in stats.historico_cola]
            colas = [h[1] for h in stats.historico_cola]
            
            ax.fill_between(tiempos, colas, alpha=0.3, color='#3498db')
            ax.plot(tiempos, colas, color='#2980b9', linewidth=1.5)
        
        ax.set_xlabel('Tiempo (minutos)')
        ax.set_ylabel('Clientes en Cola')
        ax.set_title(titulo)
        
        plt.tight_layout()
        
        if guardar:
            path = os.path.join(self.directorio, "evolucion_colas.png")
            plt.savefig(path, dpi=150, bbox_inches='tight')
            print(f"📊 Guardado: {path}")
        
        return fig
    
    def graficar_comparacion_escenarios(
        self,
        comparador: ComparadorEscenarios,
        guardar: bool = True
    ) -> plt.Figure:
        """Genera gráficas comparativas de escenarios"""
        if not comparador.resultados:
            print("No hay resultados para graficar")
            return None
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        nombres = list(comparador.resultados.keys())
        esperas = [r['stats'].tiempo_espera_promedio for r in comparador.resultados.values()]
        abandonos = [r['stats'].tasa_abandono for r in comparador.resultados.values()]
        throughputs = [r['costo_beneficio']['throughput_hora'] for r in comparador.resultados.values()]
        costos = [r['costo_beneficio']['costo_operacional_hora'] for r in comparador.resultados.values()]
        
        # Tiempo de espera
        ax1 = axes[0, 0]
        bars1 = ax1.bar(nombres, esperas, color='#3498db')
        ax1.set_ylabel('Minutos')
        ax1.set_title('Tiempo de Espera Promedio')
        ax1.tick_params(axis='x', rotation=45)
        self._destacar_mejor(ax1, bars1, esperas, menor_es_mejor=True)
        
        # Tasa de abandono
        ax2 = axes[0, 1]
        bars2 = ax2.bar(nombres, abandonos, color='#e74c3c')
        ax2.set_ylabel('Porcentaje (%)')
        ax2.set_title('Tasa de Abandono')
        ax2.tick_params(axis='x', rotation=45)
        self._destacar_mejor(ax2, bars2, abandonos, menor_es_mejor=True)
        
        # Throughput
        ax3 = axes[1, 0]
        bars3 = ax3.bar(nombres, throughputs, color='#2ecc71')
        ax3.set_ylabel('Clientes/hora')
        ax3.set_title('Throughput (Capacidad de Atención)')
        ax3.tick_params(axis='x', rotation=45)
        self._destacar_mejor(ax3, bars3, throughputs, menor_es_mejor=False)
        
        # Costo operacional
        ax4 = axes[1, 1]
        bars4 = ax4.bar(nombres, costos, color='#9b59b6')
        ax4.set_ylabel('USD/hora')
        ax4.set_title('Costo Operacional')
        ax4.tick_params(axis='x', rotation=45)
        self._destacar_mejor(ax4, bars4, costos, menor_es_mejor=True)
        
        plt.suptitle('Comparación de Escenarios - SuperLatino', fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        if guardar:
            path = os.path.join(self.directorio, "comparacion_escenarios.png")
            plt.savefig(path, dpi=150, bbox_inches='tight')
            print(f"📊 Guardado: {path}")
        
        return fig
    
    def _destacar_mejor(self, ax, bars, valores, menor_es_mejor=True):
        """Destaca la mejor barra en verde"""
        if menor_es_mejor:
            mejor_idx = np.argmin(valores)
        else:
            mejor_idx = np.argmax(valores)
        
        bars[mejor_idx].set_color('#27ae60')
        bars[mejor_idx].set_edgecolor('#1e8449')
        bars[mejor_idx].set_linewidth(2)
    
    def graficar_costo_beneficio(
        self,
        comparador: ComparadorEscenarios,
        guardar: bool = True
    ) -> plt.Figure:
        """Gráfica de análisis costo-beneficio"""
        if not comparador.resultados:
            return None
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        for nombre, resultado in comparador.resultados.items():
            cb = resultado['costo_beneficio']
            x = cb['costo_operacional_hora']
            y = cb['throughput_hora']
            
            scatter = ax.scatter(x, y, s=200, alpha=0.7)
            ax.annotate(nombre, (x, y), textcoords="offset points", 
                       xytext=(5, 5), fontsize=9)
        
        ax.set_xlabel('Costo Operacional ($/hora)')
        ax.set_ylabel('Throughput (clientes/hora)')
        ax.set_title('Análisis Costo-Beneficio por Escenario')
        
        # Añadir línea de eficiencia ideal
        min_costo = min(r['costo_beneficio']['costo_operacional_hora'] 
                       for r in comparador.resultados.values())
        max_costo = max(r['costo_beneficio']['costo_operacional_hora'] 
                       for r in comparador.resultados.values())
        
        plt.tight_layout()
        
        if guardar:
            path = os.path.join(self.directorio, "costo_beneficio.png")
            plt.savefig(path, dpi=150, bbox_inches='tight')
            print(f"📊 Guardado: {path}")
        
        return fig
    
    def graficar_distribucion_por_tipo(
        self,
        stats: EstadisticasSimulacion,
        guardar: bool = True
    ) -> plt.Figure:
        """Gráfica de distribución de clientes por tipo de caja"""
        df = stats.to_dataframe()
        if df.empty:
            return None
        
        df_atendidos = df[~df['abandono']]
        if df_atendidos.empty:
            return None
        
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        
        # Pie chart de clientes por tipo
        por_tipo = df_atendidos['tipo_caja'].value_counts()
        colores_tipo = {
            'humana': '#3498db',
            'automatica': '#2ecc71', 
            'rapida': '#f1c40f'
        }
        colors = [colores_tipo.get(t, '#95a5a6') for t in por_tipo.index]
        
        axes[0].pie(por_tipo.values, labels=por_tipo.index, colors=colors,
                   autopct='%1.1f%%', startangle=90)
        axes[0].set_title('Distribución de Clientes por Tipo de Caja')
        
        # Box plot de tiempos por tipo
        tipos_unicos = df_atendidos['tipo_caja'].unique()
        datos_box = [df_atendidos[df_atendidos['tipo_caja'] == t]['tiempo_espera'].values 
                    for t in tipos_unicos]
        
        bp = axes[1].boxplot(datos_box, labels=tipos_unicos, patch_artist=True)
        for patch, tipo in zip(bp['boxes'], tipos_unicos):
            patch.set_facecolor(colores_tipo.get(tipo, '#95a5a6'))
        
        axes[1].set_ylabel('Tiempo de Espera (minutos)')
        axes[1].set_title('Tiempo de Espera por Tipo de Caja')
        
        plt.tight_layout()
        
        if guardar:
            path = os.path.join(self.directorio, "distribucion_tipos.png")
            plt.savefig(path, dpi=150, bbox_inches='tight')
            print(f"📊 Guardado: {path}")
        
        return fig
    
    def generar_reporte_completo(
        self,
        comparador: ComparadorEscenarios,
        nombre_reporte: str = "reporte_simulacion"
    ):
        """Genera un reporte completo con todas las gráficas"""
        print("\n" + "=" * 60)
        print("GENERANDO REPORTE COMPLETO")
        print("=" * 60)
        
        # Generar gráficas
        self.graficar_comparacion_escenarios(comparador)
        self.graficar_costo_beneficio(comparador)
        
        # Para cada escenario, generar gráficas individuales
        for nombre, resultado in comparador.resultados.items():
            stats = resultado['stats']
            
            self.graficar_histograma_espera(
                stats, 
                titulo=f"Tiempos de Espera - {nombre}",
                guardar=True
            )
            plt.close()
        
        # Guardar tabla comparativa
        tabla = comparador.obtener_tabla_comparativa()
        tabla_path = os.path.join(self.directorio, f"{nombre_reporte}.csv")
        tabla.to_csv(tabla_path, index=False)
        print(f"📋 Tabla guardada: {tabla_path}")
        
        # Generar resumen en texto
        self._generar_resumen_texto(comparador, nombre_reporte)
        
        print(f"\n✅ Reporte completo generado en: {self.directorio}/")
    
    def _generar_resumen_texto(
        self,
        comparador: ComparadorEscenarios,
        nombre_reporte: str
    ):
        """Genera resumen en formato texto"""
        path = os.path.join(self.directorio, f"{nombre_reporte}.txt")
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("REPORTE DE SIMULACIÓN - SUPERMERCADO SUPERLATINO\n")
            f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write("=" * 70 + "\n\n")
            
            f.write("RESUMEN DE ESCENARIOS EVALUADOS\n")
            f.write("-" * 40 + "\n\n")
            
            for nombre, resultado in comparador.resultados.items():
                stats = resultado['stats']
                cb = resultado['costo_beneficio']
                config = resultado['config_cajas']
                
                f.write(f"📌 {nombre.upper()}\n")
                f.write(f"   Configuración: {config.descripcion()}\n")
                f.write(f"   Política: {resultado['politica']}\n")
                f.write(f"   Demanda: {'Alta' if resultado['alta_demanda'] else 'Normal'}\n")
                f.write(f"   \n")
                f.write(f"   Clientes atendidos: {stats.clientes_atendidos}\n")
                f.write(f"   Abandonos: {stats.clientes_abandonaron} ({stats.tasa_abandono:.1f}%)\n")
                f.write(f"   Tiempo espera promedio: {stats.tiempo_espera_promedio:.2f} min\n")
                f.write(f"   Throughput: {cb['throughput_hora']:.1f} clientes/hora\n")
                f.write(f"   Costo operacional: ${cb['costo_operacional_hora']:.2f}/hora\n")
                f.write(f"   Eficiencia: {cb['eficiencia']:.2f}\n")
                f.write("\n")
            
            f.write("\nRECOMENDACIONES\n")
            f.write("-" * 40 + "\n")
            for rec in comparador.generar_recomendaciones():
                f.write(f"  {rec}\n")
            
            f.write("\n" + "=" * 70 + "\n")
        
        print(f"📝 Resumen guardado: {path}")


def main():
    """Ejemplo de generación de reportes"""
    from .comparador import ComparadorEscenarios
    
    # Crear comparador y ejecutar simulaciones
    comparador = ComparadorEscenarios()
    comparador.ejecutar_todos_escenarios(alta_demanda=False)
    
    # Generar reportes
    generador = GeneradorReportes()
    generador.generar_reporte_completo(comparador)


if __name__ == "__main__":
    main()
