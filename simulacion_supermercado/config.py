"""Configuraciones y parámetros globales del simulador."""

# Parámetros de llegada (λ) expresados en clientes por minuto.
TASA_LLEGADA_NORMAL = 1.8
TASA_LLEGADA_FIN_DE_MES = 3.2

# Tiempo promedio de servicio (1/μ) en minutos por cliente.
TIEMPO_PROMEDIO_SERVICIO = 1.6

# Tiempo máximo de espera tolerado antes de abandono (minutos).
TIEMPO_MAX_ESPERA_TOLERADO = 9.0

DEFAULT_CONFIG = {
    "modo": "operacion",
    "cajas_tradicionales": 0,
    "cajas_automaticas": 0,
    "habilitar_caja_rapida": False,
    "tasa_llegada_normal": TASA_LLEGADA_NORMAL,
    "tasa_llegada_fin_de_mes": TASA_LLEGADA_FIN_DE_MES,
    "tiempo_promedio_servicio": TIEMPO_PROMEDIO_SERVICIO,
    "tiempo_max_espera_tolerado": TIEMPO_MAX_ESPERA_TOLERADO,
}
