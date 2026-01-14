"""
Script para lanzar la visualización Pygame
"""
import os
import sys

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from visualizacion.pygame_sim import main

if __name__ == "__main__":
    main()
