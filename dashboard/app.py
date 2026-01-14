"""
Dashboard interactivo con Dash para visualización de KPIs
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dash import Dash, html, dcc, callback, Output, Input, State
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import threading
import time

from config import (
    DASH_CONFIG, ESCENARIOS, ConfiguracionSimulacion,
    ConfiguracionCajas, CostosOperacionales, TipoCaja
)
from simulacion.supermercado import Supermercado
from simulacion.estadisticas import EstadisticasSimulacion


# Variables globales para estado
simulacion_activa = None
resultados_escenarios = {}


def ejecutar_simulacion_background(escenario_nombre: str, config_cajas: ConfiguracionCajas, 
                                   alta_demanda: bool, politica: str):
    """Ejecuta simulación en segundo plano"""
    global simulacion_activa, resultados_escenarios
    
    config_sim = ConfiguracionSimulacion()
    supermercado = Supermercado(
        config_sim=config_sim,
        config_cajas=config_cajas,
        politica=politica,
        alta_demanda=alta_demanda
    )
    
    simulacion_activa = supermercado
    stats = supermercado.ejecutar()
    
    # Guardar resultados
    resultados_escenarios[escenario_nombre] = {
        'stats': stats,
        'config': config_cajas,
        'alta_demanda': alta_demanda,
        'politica': politica
    }
    
    simulacion_activa = None
    return stats


def crear_grafica_tiempo_espera(stats: EstadisticasSimulacion):
    """Crea histograma de tiempos de espera"""
    if not stats._tiempos_espera:
        return go.Figure()
    
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=stats._tiempos_espera,
        nbinsx=20,
        marker_color='#3498db',
        name='Tiempo de espera'
    ))
    
    fig.add_vline(x=stats.tiempo_espera_promedio, line_dash="dash", 
                  line_color="red", annotation_text=f"Promedio: {stats.tiempo_espera_promedio:.1f} min")
    
    fig.update_layout(
        title="Distribución de Tiempos de Espera",
        xaxis_title="Tiempo (minutos)",
        yaxis_title="Frecuencia",
        template="plotly_white"
    )
    return fig


def crear_grafica_colas(stats: EstadisticasSimulacion):
    """Crea gráfica de evolución de colas"""
    if not stats.historico_cola:
        return go.Figure()
    
    tiempos = [h[0] for h in stats.historico_cola]
    colas = [h[1] for h in stats.historico_cola]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=tiempos, y=colas,
        mode='lines',
        fill='tozeroy',
        fillcolor='rgba(52, 152, 219, 0.3)',
        line=dict(color='#3498db', width=2),
        name='Longitud de cola'
    ))
    
    fig.update_layout(
        title="Evolución de la Longitud de Cola",
        xaxis_title="Tiempo (minutos)",
        yaxis_title="Clientes en cola",
        template="plotly_white"
    )
    return fig


def crear_grafica_throughput(stats: EstadisticasSimulacion):
    """Crea gráfica de throughput"""
    if not stats.historico_throughput:
        return go.Figure()
    
    tiempos = [h[0] for h in stats.historico_throughput]
    throughput = [h[1] for h in stats.historico_throughput]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=tiempos, y=throughput,
        mode='lines',
        line=dict(color='#2ecc71', width=2),
        name='Throughput'
    ))
    
    fig.update_layout(
        title="Throughput (Clientes atendidos por hora)",
        xaxis_title="Tiempo (minutos)",
        yaxis_title="Clientes/hora",
        template="plotly_white"
    )
    return fig


def crear_grafica_por_tipo_caja(stats: EstadisticasSimulacion):
    """Crea gráfica de distribución por tipo de caja"""
    df = stats.to_dataframe()
    if df.empty:
        return go.Figure()
    
    df_atendidos = df[~df['abandono']]
    if df_atendidos.empty:
        return go.Figure()
    
    por_tipo = df_atendidos.groupby('tipo_caja').agg({
        'id': 'count',
        'tiempo_espera': 'mean',
        'tiempo_servicio': 'mean'
    }).reset_index()
    por_tipo.columns = ['tipo_caja', 'clientes', 'espera_prom', 'servicio_prom']
    
    colores = {'humana': '#3498db', 'automatica': '#2ecc71', 'rapida': '#f1c40f'}
    
    fig = make_subplots(rows=1, cols=2, 
                        subplot_titles=('Clientes por Tipo de Caja', 'Tiempo Promedio por Tipo'))
    
    fig.add_trace(go.Bar(
        x=por_tipo['tipo_caja'],
        y=por_tipo['clientes'],
        marker_color=[colores.get(t, '#95a5a6') for t in por_tipo['tipo_caja']],
        name='Clientes'
    ), row=1, col=1)
    
    fig.add_trace(go.Bar(
        x=por_tipo['tipo_caja'],
        y=por_tipo['espera_prom'],
        marker_color=[colores.get(t, '#95a5a6') for t in por_tipo['tipo_caja']],
        name='Tiempo espera',
        showlegend=False
    ), row=1, col=2)
    
    fig.update_layout(template="plotly_white", height=400)
    return fig


def crear_grafica_comparacion_escenarios():
    """Crea gráfica comparando escenarios ejecutados"""
    global resultados_escenarios
    
    if not resultados_escenarios:
        return go.Figure()
    
    nombres = []
    esperas = []
    abandonos = []
    throughputs = []
    costos = []
    
    for nombre, data in resultados_escenarios.items():
        stats = data['stats']
        config = data['config']
        
        nombres.append(nombre)
        esperas.append(stats.tiempo_espera_promedio)
        abandonos.append(stats.tasa_abandono)
        
        duracion_horas = 8.0
        throughputs.append(stats.throughput(duracion_horas))
        
        costos_op = CostosOperacionales()
        costo_hora = costos_op.calcular_costo_hora(config)
        costos.append(costo_hora)
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Tiempo de Espera Promedio (min)',
            'Tasa de Abandono (%)',
            'Throughput (clientes/hora)',
            'Costo Operacional ($/hora)'
        )
    )
    
    fig.add_trace(go.Bar(x=nombres, y=esperas, marker_color='#3498db'), row=1, col=1)
    fig.add_trace(go.Bar(x=nombres, y=abandonos, marker_color='#e74c3c'), row=1, col=2)
    fig.add_trace(go.Bar(x=nombres, y=throughputs, marker_color='#2ecc71'), row=2, col=1)
    fig.add_trace(go.Bar(x=nombres, y=costos, marker_color='#9b59b6'), row=2, col=2)
    
    fig.update_layout(
        template="plotly_white",
        height=600,
        showlegend=False,
        title_text="Comparación de Escenarios"
    )
    return fig


def crear_dashboard():
    """Crea la aplicación Dash"""
    app = Dash(__name__, title="SuperLatino - Dashboard de Simulacion", suppress_callback_exceptions=True)
    
    app.layout = html.Div([
        # Header
        html.Div([
            html.H1("SuperLatino - Dashboard de Simulacion", 
                   style={'color': '#2c3e50', 'marginBottom': '10px'}),
            html.P("Sistema de analisis y optimizacion de cajas registradoras",
                  style={'color': '#7f8c8d'})
        ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#ecf0f1'}),
        
        # Panel de control
        html.Div([
            html.H3("Configuracion de Simulacion", style={'color': '#2c3e50'}),
            
            html.Div([
                # Selector de escenario
                html.Div([
                    html.Label("Escenario:", style={'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        id='escenario-dropdown',
                        options=[
                            {'label': '100% Tradicional (6 humanas)', 'value': '100_tradicional'},
                            {'label': '50/50 Hibrido (3 humanas, 3 auto)', 'value': '50_50_hibrido'},
                            {'label': 'Hibrido con Rapidas (3H, 2A, 2R)', 'value': 'hibrido_con_rapidas'},
                            {'label': 'Automatizado (1H, 4A, 2R)', 'value': 'automatizado'},
                        ],
                        value='hibrido_con_rapidas',
                        style={'width': '100%'}
                    )
                ], style={'width': '25%', 'display': 'inline-block', 'padding': '10px'}),
                
                # Política
                html.Div([
                    html.Label("Politica de Asignacion:", style={'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        id='politica-dropdown',
                        options=[
                            {'label': 'Balanceada (recomendada)', 'value': 'balanceada'},
                            {'label': 'Cola mas corta', 'value': 'cola_mas_corta'},
                            {'label': 'Prioridad rapidas', 'value': 'prioridad_rapida'},
                            {'label': 'Preferir humana', 'value': 'preferir_humana'},
                        ],
                        value='balanceada',
                        style={'width': '100%'}
                    )
                ], style={'width': '25%', 'display': 'inline-block', 'padding': '10px'}),
                
                # Demanda
                html.Div([
                    html.Label("Nivel de Demanda:", style={'fontWeight': 'bold'}),
                    dcc.RadioItems(
                        id='demanda-radio',
                        options=[
                            {'label': 'Normal', 'value': 'normal'},
                            {'label': 'Alta (fin de mes)', 'value': 'alta'},
                        ],
                        value='normal',
                        inline=True
                    )
                ], style={'width': '25%', 'display': 'inline-block', 'padding': '10px'}),
                
                # Botón
                html.Div([
                    html.Button('Ejecutar Simulacion', id='btn-simular', 
                               style={
                                   'backgroundColor': '#2ecc71',
                                   'color': 'white',
                                   'border': 'none',
                                   'padding': '15px 30px',
                                   'fontSize': '16px',
                                   'borderRadius': '5px',
                                   'cursor': 'pointer',
                                   'marginTop': '20px'
                               })
                ], style={'width': '20%', 'display': 'inline-block', 'padding': '10px', 'textAlign': 'center'}),
            ], style={'display': 'flex', 'alignItems': 'center'}),
            
        ], style={'padding': '20px', 'backgroundColor': 'white', 'margin': '20px', 'borderRadius': '10px', 'boxShadow': '0 2px 5px rgba(0,0,0,0.1)'}),
        
        # Estado de simulación
        html.Div(id='estado-simulacion', style={'textAlign': 'center', 'padding': '10px'}),
        
        # KPIs principales
        html.Div(id='kpis-container', style={'padding': '20px'}),
        
        # Gráficas
        html.Div([
            html.Div([
                dcc.Graph(id='grafica-espera')
            ], style={'width': '50%', 'display': 'inline-block'}),
            html.Div([
                dcc.Graph(id='grafica-colas')
            ], style={'width': '50%', 'display': 'inline-block'}),
        ]),
        
        html.Div([
            html.Div([
                dcc.Graph(id='grafica-throughput')
            ], style={'width': '50%', 'display': 'inline-block'}),
            html.Div([
                dcc.Graph(id='grafica-tipos')
            ], style={'width': '50%', 'display': 'inline-block'}),
        ]),
        
        # Comparación de escenarios
        html.Div([
            html.H3("Comparacion de Escenarios", style={'color': '#2c3e50', 'textAlign': 'center'}),
            html.P("Ejecute multiples escenarios para compararlos", style={'textAlign': 'center', 'color': '#7f8c8d'}),
            dcc.Graph(id='grafica-comparacion')
        ], style={'padding': '20px', 'backgroundColor': 'white', 'margin': '20px', 'borderRadius': '10px'}),
        
    ], style={'fontFamily': 'Arial, sans-serif', 'backgroundColor': '#f5f6fa'})
    
    return app


def registrar_callbacks(app):
    """Registra callbacks de la aplicación"""
    
    @app.callback(
        [Output('estado-simulacion', 'children'),
         Output('kpis-container', 'children'),
         Output('grafica-espera', 'figure'),
         Output('grafica-colas', 'figure'),
         Output('grafica-throughput', 'figure'),
         Output('grafica-tipos', 'figure'),
         Output('grafica-comparacion', 'figure')],
        [Input('btn-simular', 'n_clicks')],
        [State('escenario-dropdown', 'value'),
         State('politica-dropdown', 'value'),
         State('demanda-radio', 'value')]
    )
    def ejecutar_y_mostrar(n_clicks, escenario, politica, demanda):
        if not n_clicks:
            # Estado inicial
            return (
                html.P("Configure y ejecute una simulacion", style={'color': '#7f8c8d'}),
                html.Div(),
                go.Figure(),
                go.Figure(),
                go.Figure(),
                go.Figure(),
                crear_grafica_comparacion_escenarios()
            )
        
        # Ejecutar simulación
        config_cajas = ESCENARIOS[escenario]
        alta_demanda = demanda == 'alta'
        
        nombre_sim = f"{escenario}_{politica}_{'alta' if alta_demanda else 'normal'}"
        
        stats = ejecutar_simulacion_background(
            nombre_sim, config_cajas, alta_demanda, politica
        )
        
        # Crear KPIs
        kpis = html.Div([
            html.Div([
                crear_kpi_card("Clientes Atendidos", stats.clientes_atendidos, "#2ecc71"),
                crear_kpi_card("Abandonos", stats.clientes_abandonaron, "#e74c3c"),
                crear_kpi_card("Espera Promedio", f"{stats.tiempo_espera_promedio:.1f} min", "#3498db"),
                crear_kpi_card("Tasa Abandono", f"{stats.tasa_abandono:.1f}%", "#e67e22"),
                crear_kpi_card("Throughput", f"{stats.throughput(8.0):.0f}/hora", "#9b59b6"),
            ], style={'display': 'flex', 'justifyContent': 'space-around', 'flexWrap': 'wrap'})
        ])
        
        return (
            html.P(f"Simulacion completada: {nombre_sim}", style={'color': '#2ecc71', 'fontWeight': 'bold'}),
            kpis,
            crear_grafica_tiempo_espera(stats),
            crear_grafica_colas(stats),
            crear_grafica_throughput(stats),
            crear_grafica_por_tipo_caja(stats),
            crear_grafica_comparacion_escenarios()
        )


def crear_kpi_card(titulo: str, valor, color: str):
    """Crea una tarjeta de KPI"""
    return html.Div([
        html.H4(titulo, style={'color': '#7f8c8d', 'marginBottom': '5px', 'fontSize': '14px'}),
        html.H2(str(valor), style={'color': color, 'margin': '0', 'fontSize': '28px'})
    ], style={
        'backgroundColor': 'white',
        'padding': '20px',
        'borderRadius': '10px',
        'textAlign': 'center',
        'minWidth': '150px',
        'margin': '10px',
        'boxShadow': '0 2px 5px rgba(0,0,0,0.1)'
    })


def ejecutar_dashboard(debug: bool = False):
    """Inicia el dashboard"""
    app = crear_dashboard()
    registrar_callbacks(app)
    
    print(f"\n🚀 Dashboard disponible en: http://{DASH_CONFIG['host']}:{DASH_CONFIG['port']}")
    print("   Presione Ctrl+C para detener\n")
    
    app.run(
        host=DASH_CONFIG['host'],
        port=DASH_CONFIG['port'],
        debug=debug
    )


if __name__ == "__main__":
    ejecutar_dashboard(debug=True)
