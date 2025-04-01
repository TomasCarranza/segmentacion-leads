from datetime import datetime

# Configuración de clientes
CLIENTES = {
    'CREXE': {
        'nombre': 'CREXE',
        'grupos': [
            {
                'nombre': 'Se brinda info',
                'resoluciones': ['Se brinda información', 'Se brinda información Whatsapp', 'Volver a llamar'],
                'filtro_resolucion': True,
                'filtro_fecha': True,
                'dias_antes': 1,
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
                'nombre': 'Analizando propuesta',
                'resoluciones': ['Analizando propuesta', 'Oportunidad de venta', 'En proceso de pago'],
                'filtro_resolucion': True,
                'filtro_fecha': True,
                'dias_antes': 2,
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
                'nombre': 'Le parece caro',
                'resoluciones': ['Le parece caro', 'Siguiente cohorte', 'Motivos personales', 'No es la oferta buscada'],
                'filtro_resolucion': True,
                'filtro_fecha': True,
                'dias_antes': 2,
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
                'nombre': 'No contesta',
                'resoluciones': ['No contesta', 'NotProcessed'],
                'filtro_resolucion': True,
                'filtro_fecha': False,
                'dias_antes': None,
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
                'nombre': 'Spam',
                'resoluciones': ['Spam - Desconoce haber solicitado informacion', 'Telefono erroneo o fuera de servicio', 'Pide no ser llamado', 'Imposible contactar'],
                'filtro_resolucion': True,
                'filtro_fecha': True,
                'dias_antes': [0, 1],
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
                'resoluciones': None,  # No filtrar por resoluciones
                'filtro_resolucion': False,
                'filtro_fecha': True,
                'dias_antes': [0, 1],
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
                    'Monday': ['Se brinda información', 'Analizando propuesta', 'Oportunidad de venta'],
                    'Tuesday': ['No contesta', 'buzón de voz', 'teléfono erróneo', 'imposible contactar'],
                    'Wednesday': ['Volver a llamar', 'volver a llamar ultimo intento'],
                    'Thursday': ['Dejo de responder', 'Le parece caro', 'Siguiente cohorte', 'Inscripto en otra universidad'],
                    'Friday': ['Horarios', 'Motivos personales', 'Modalidad de cursado', 'No es la oferta buscada']
                },
                'filtro_resolucion': True,
                'filtro_fecha': False,
                'dias_antes': None,
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
    'ULINEA': {
        'nombre': 'ULINEA',
        'grupos': [
            {
                'nombre': 'Bienvenida',
                'resoluciones': None,  # No filtrar por resoluciones
                'filtro_resolucion': False,
                'filtro_fecha': True,
                'dias_antes': 1,
                'columnas_salida': {
                    'Nombre': 'Nombre',
                    'Apellido': 'Apellido',
                    'Email': 'Email',
                    'Tel': 'Tel',
                    'WhatsApp': 'WhatsApp',
                    'Tipificacion': 'Ultima Resolución'
                }
            }
        ]
    },
    'ANAHUAC': {
        'nombre': 'ANAHUAC',
        'grupos': [
            {
                'nombre': 'Bienvenida',
                'resoluciones': None,  # No filtrar por resoluciones
                'filtro_resolucion': False,
                'filtro_fecha': True,
                'dias_antes': 1,
                'columnas_salida': {
                    'Nombre': 'Nombre',
                    'Apellido': 'Apellido',
                    'Email': 'Email',
                    'Tel': 'Tel',
                    'WhatsApp': 'WhatsApp',
                    'Tipificacion': 'Ultima Resolución'
                }
            }
        ]
    },
    'PK_CBA': {
        'nombre': 'PK CBA',
        'grupos': [
            {
                'nombre': 'Bienvenida',
                'resoluciones': ['1', '2', '3', '4', '5'],  # Mantener números para PK CBA
                'filtro_resolucion': True,
                'filtro_fecha': True,
                'dias_antes': 1,
                'columnas_salida': {
                    'Nombre': 'Nombre',
                    'Apellido': 'Apellido',
                    'Email': 'e-Mail',
                    'Tel': 'Móvil',
                    'Programa': 'Carrera de Interes',
                    'Cod_Programa': 'Cod_Programa'
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