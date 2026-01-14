"""
Script para lanzar el dashboard de forma independiente
"""
import os
import sys

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.app import ejecutar_dashboard

if __name__ == "__main__":
    ejecutar_dashboard(debug=True)
