# 🛒 SuperLatino - Sistema de Simulación de Cajas Registradoras

Sistema de simulación computacional para analizar y optimizar la configuración del sistema de cajas registradoras del supermercado SuperLatino en Ciudad Bolívar.

## 📋 Descripción del Proyecto

Este proyecto desarrolla un sistema de simulación de eventos discretos que permite:
- Simular diferentes configuraciones de cajas (tradicionales, automáticas, rápidas)
- Analizar tiempos de espera y tasas de abandono
- Comparar escenarios operativos
- Optimizar la relación costo-beneficio

## 🏗️ Stack Tecnológico

| Tecnología | Uso |
|------------|-----|
| **Python 3.11+** | Lenguaje principal |
| **SimPy** | Motor de simulación de eventos discretos |
| **Pygame** | Visualización animada en tiempo real |
| **Dash/Plotly** | Dashboard web interactivo |
| **Matplotlib** | Gráficas y reportes |
| **Pandas** | Análisis de datos |

## 📁 Estructura del Proyecto

```
simulacion-cajas-supermercado/
├── config.py                 # Configuración global
├── main.py                   # Punto de entrada principal
├── requirements.txt          # Dependencias
│
├── simulacion/               # Núcleo de simulación (SimPy)
│   ├── cliente.py           # Modelo de cliente
│   ├── caja.py              # Modelo de caja registradora
│   ├── supermercado.py      # Motor de simulación
│   └── estadisticas.py      # Recolección de métricas
│
├── visualizacion/            # Visualización Pygame
│   └── pygame_sim.py        # Animación en tiempo real
│
├── dashboard/                # Panel web Dash
│   └── app.py               # Dashboard interactivo
│
├── analisis/                 # Análisis y reportes
│   ├── comparador.py        # Comparación de escenarios
│   └── reportes.py          # Generación de gráficas
│
├── scripts/                  # Scripts de ejecución
│   ├── launch_dashboard.py
│   ├── run_pygame.py
│   └── run_analysis.py
│
└── resource/                 # Recursos gráficos
    ├── caja.png
    ├── mapa.jpg
    └── personaje *.png
```

## 🚀 Instalación

```bash
# Clonar el repositorio
git clone https://github.com/GabrielRieraDEV/simulacion-cajas-supermercado.git
cd simulacion-cajas-supermercado

# Crear entorno virtual (recomendado)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt
```

## 💻 Uso

### Menú Interactivo
```bash
python main.py
```

### Modos Específicos
```bash
# Visualización Pygame (animación)
python main.py --modo pygame

# Dashboard web (http://localhost:8050)
python main.py --modo dash

# Análisis comparativo completo
python main.py --modo analisis

# Simulación rápida en consola
python main.py --modo consola
```

## 🎮 Visualización Pygame

Muestra animación en tiempo real de:
- 🔵 **Cajas humanas** (azul)
- 🟢 **Cajas automáticas** (verde)  
- 🟡 **Cajas rápidas** (amarillo)
- Clientes moviéndose y formando colas

**Controles:**
- `ESPACIO` - Iniciar / Pausar la simulación (inicio en pausa)
- `↑ / ↓` - Aumentar / disminuir la velocidad (paso base lento 0.4x)
- `1-4` - Cambiar entre escenarios predefinidos (100% trad, 50/50, híbrido con rápidas, automatizado)
- `D` - Alternar nivel de demanda (Normal / Alta)
- `P` - Cambiar política de asignación (cola más corta, rápidas, humanas, balanceada)
- `R` - Reiniciar simulación en escenario/política actuales
- `ESC` - Salir

## 📊 Escenarios Predefinidos

| Escenario | Humanas | Automáticas | Rápidas |
|-----------|---------|-------------|---------|
| 100% Tradicional | 6 | 0 | 0 |
| 50/50 Híbrido | 3 | 3 | 0 |
| Híbrido con Rápidas | 3 | 2 | 2 |
| Automatizado | 1 | 4 | 2 |

## 📈 KPIs Analizados

- **Tiempo promedio de espera** en cola
- **Tasa de abandono** por tiempo excesivo
- **Throughput** (clientes atendidos/hora)
- **Ocupación** de cada tipo de caja
- **Costo operacional** vs eficiencia
- **ROI** de implementar cajas automáticas

## 🔧 Parámetros de Simulación

```python
# Llegada de clientes (Poisson)
tasa_llegada_normal = 0.5    # 30 clientes/hora
tasa_llegada_alta = 1.5      # 90 clientes/hora (fin de mes)

# Tiempo de servicio (Exponencial)
tiempo_servicio_humana = 3.0 min
tiempo_servicio_automatica = 4.0 min
tiempo_servicio_rapida = 1.5 min

# Tolerancia de espera
tiempo_abandono = 5-15 min
```

## 📝 Objetivos del Proyecto

1. ✅ Simular sistema 100% cajas tradicionales
2. ✅ Evaluar escenarios híbridos 50% auto / 50% tradicional
3. ✅ Implementar cajas rápidas (≤10 productos)
4. ✅ Cuantificar reducción de tiempos de espera
5. ✅ Determinar relación costo-beneficio

## 👥 Contexto

**Supermercado SuperLatino** - Ciudad Bolívar

Problemática:
- Congestión en períodos de pago de salarios
- Abandono de compras por tiempos excesivos
- Distribución ineficiente de recursos

## 📄 Licencia

MIT License - Ver [LICENSE](LICENSE)
