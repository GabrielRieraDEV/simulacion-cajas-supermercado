
import sys
sys.path.insert(0, r"C:\Users\gabri\Documents\GitHub\simulacion-cajas-supermercado")
from config import ESCENARIOS
from visualizacion.pygame_sim import VisualizadorPygame

config_cajas = ESCENARIOS["hibrido_con_rapidas"]
viz = VisualizadorPygame(
    config_cajas=config_cajas,
    politica="balanceada",
    alta_demanda=False
)
viz.ejecutar()
