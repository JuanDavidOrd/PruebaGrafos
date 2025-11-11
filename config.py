"""
Configuración de la aplicación NASA Burro Espacial.
Personaliza colores, animaciones, sonidos y reportes.
"""

# ===== CONFIGURACIÓN DE SONIDOS =====
AUDIO_CONFIG = {
    "enabled": True,                          # Habilitar/deshabilitar sonidos
    "death_sound_volume": 1.0,               # Volumen del sonido de muerte (0.0 a 1.0)
    "sound_directory": "assets/sounds",      # Directorio de sonidos
}

# ===== CONFIGURACIÓN DE ANIMACIONES =====
ANIMATION_CONFIG = {
    "enabled": True,                          # Habilitar/deshabilitar animaciones
    "enable_gradient": True,                 # Gradiente de color azul→verde→rojo
    "highlight_visited_stars": True,         # Destacar estrellas visitadas
    "highlight_color": "yellow",             # Color para destacar estrellas
    "highlight_alpha": 0.6,                  # Transparencia del resaltado
    "route_color": "#2ca02c",                # Color de la ruta
    "route_linewidth_base": 2.0,             # Ancho de línea base
    "route_linewidth_max": 4.0,              # Ancho de línea máximo
}

# ===== CONFIGURACIÓN DE REPORTES =====
REPORT_CONFIG = {
    "export_enabled": True,                   # Exportar reportes a archivos
    "export_directory": "reports",            # Directorio de exportación
    "export_formats": ["csv", "json"],        # Formatos de exportación
    "show_dialog": True,                      # Mostrar diálogo de reporte
    "show_summary_on_death": True,            # Mostrar resumen si el burro muere
}

# ===== CONFIGURACIÓN DE COLORES DEL MAPA =====
MAP_COLORS = {
    "background": "white",
    "edge_normal": "black",
    "edge_blocked": "gray",
    "edge_blocked_style": "--",               # Línea punteada
    "node_default": "blue",
    "node_multi_constellation": "#d62728",    # Rojo
    "edge_route": "#2ca02c",                  # Verde
    "edge_route_alpha": 0.9,
}

# ===== CONFIGURACIÓN DE MENSAJES =====
MESSAGES = {
    "death_warning_title": "¡Burro Muerto!",
    "death_warning_message": (
        "El burro ha muerto durante el viaje.\n"
        "La simulación se ha detenido.\n\n"
        "Motivo: {reason}"
    ),
    "route_calculation_error": "No se pudo calcular la ruta (resultado vacío).",
}

# ===== CONFIGURACIÓN AVANZADA =====
ADVANCED_CONFIG = {
    "debug_mode": False,                      # Modo debug (imprime logs)
    "max_steps_simulation": 1000,             # Límite máximo de pasos
    "floating_point_precision": 2,            # Decimales en reportes
}


def get_config(key_path: str, default=None):
    """
    Obtiene un valor de configuración usando ruta de puntos.
    
    Ejemplo:
        get_config("AUDIO_CONFIG.enabled")  -> True
        get_config("ANIMATION_CONFIG.highlight_color")  -> "yellow"
    """
    configs = {
        "AUDIO_CONFIG": AUDIO_CONFIG,
        "ANIMATION_CONFIG": ANIMATION_CONFIG,
        "REPORT_CONFIG": REPORT_CONFIG,
        "MAP_COLORS": MAP_COLORS,
        "MESSAGES": MESSAGES,
        "ADVANCED_CONFIG": ADVANCED_CONFIG,
    }
    
    parts = key_path.split(".")
    value = configs.get(parts[0], {})
    
    for part in parts[1:]:
        if isinstance(value, dict):
            value = value.get(part, default)
        else:
            return default
    
    return value
