from datetime import datetime

# Configuración de clientes
CLIENTES = {
    'ULINEA': {
        'nombre': 'ULINEA',
        'grupos': [
            {
                'nombre': 'Bienvenida',
                'resoluciones': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'],
                'filtro_resolucion': True,
                'columnas_salida': {
                    'Nombre': 'Nombre',
                    'Apellido': 'Apellido',
                    'Email': 'Email',
                    'Tel': 'Tel',
                    'Programa': 'Programa',
                    'Resolución': 'Resolución'
                }
            }
        ]
    },
    'ANAHUAC': {
        'nombre': 'ANAHUAC',
        'grupos': [
            {
                'nombre': 'Bienvenida',
                'resoluciones': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'],
                'filtro_resolucion': True,
                'columnas_salida': {
                    'Nombre': 'Nombre',
                    'Apellido': 'Apellido',
                    'Email': 'Email',
                    'Tel': 'Tel',
                    'Programa': 'Programa',
                    'Resolución': 'Resolución'
                }
            }
        ]
    },
    'UNAB': {
        'nombre': 'UNAB',
        'grupos': [
            {
                'nombre': 'Bienvenida',
                'resoluciones': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'],
                'filtro_resolucion': True,
                'columnas_salida': {
                    'Nombre': 'Nombre',
                    'Apellido': 'Apellido',
                    'Email': 'Email',
                    'Tel': 'Tel',
                    'Programa': 'Programa',
                    'Resolución': 'Resolución'
                }
            },
            {
                'nombre': 'Nurturing',
                'resoluciones': {
                    'Monday': ['1', '2', '3', '4', '5'],
                    'Tuesday': ['6', '7', '8', '9', '10'],
                    'Wednesday': ['11', '12', '13', '14', '15'],
                    'Thursday': ['16', '17', '18', '19', '20'],
                    'Friday': ['21', '22', '23', '24', '25']
                },
                'filtro_resolucion': True,
                'columnas_salida': {
                    'Nombre': 'Nombre',
                    'Apellido': 'Apellido',
                    'Email': 'Email',
                    'Tel': 'Tel',
                    'Programa': 'Programa',
                    'Resolución': 'Resolución'
                }
            }
        ]
    },
    'PK_CBA': {
        'nombre': 'PK CBA',
        'grupos': [
            {
                'nombre': 'Bienvenida',
                'resoluciones': ['1', '2', '3', '4', '5'],
                'filtro_resolucion': True,
                'columnas_salida': {
                    'Nombre': 'Nombre',
                    'Apellido': 'Apellido',
                    'Email': 'Email',
                    'Tel': 'Tel',
                    'Programa': 'Programa',
                    'Resolución': 'Resolución'
                }
            }
        ]
    }
}

def obtener_configuracion_cliente(cliente_id: str) -> dict:
    """Obtiene la configuración de un cliente específico."""
    return CLIENTES.get(cliente_id, {})

def obtener_lista_clientes() -> list:
    """Obtiene la lista de clientes disponibles."""
    return list(CLIENTES.keys()) 