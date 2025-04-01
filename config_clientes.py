from datetime import datetime

# Configuraciones de clientes
CLIENTES = {
    'CREXE': {
        'nombre': 'CREXE',
        'grupos': [
            {
                'nombre': "1 día antes",
                'resoluciones': [
                    "Se brinda información",
                    "Se brinda información Whatsapp",
                    "Volver a llamar"
                ],
                'dias_antes': 1,
                'filtro_fecha': True,
                'activo': True
            },
            {
                'nombre': "2 días antes - Positivos",
                'resoluciones': [
                    "Analizando propuesta",
                    "Oportunidad de venta",
                    "En proceso de pago"
                ],
                'dias_antes': 2,
                'filtro_fecha': True,
                'activo': True
            },
            {
                'nombre': "2 días antes - Negativos",
                'resoluciones': [
                    "Le parece caro",
                    "Siguiente cohorte",
                    "Motivos personales",
                    "No es la oferta buscada"
                ],
                'dias_antes': 2,
                'filtro_fecha': True,
                'activo': True
            },
            {
                'nombre': "Sin filtro de fecha",
                'resoluciones': [
                    "No contesta",
                    "NotProcessed"
                ],
                'dias_antes': None,
                'filtro_fecha': False,
                'activo': True
            },
            {
                'nombre': "1 día antes y día actual - Especiales",
                'resoluciones': [
                    "Spam - Desconoce haber solicitado informacion",
                    "Telefono erroneo o fuera de servicio",
                    "Pide no ser llamado",
                    "Imposible contactar"
                ],
                'dias_antes': [0, 1],
                'filtro_fecha': True,
                'activo': True
            }
        ],
        'columnas_salida': {
            'Nombre': 'Nombre',
            'teltelefono': 'Telefono',
            'emlMail': 'Email',
            'Carrera Interes': 'Programa',
            'TelWhatsapp': 'Whatsapp'
        }
    },
    'UNAB': {
        'nombre': 'UNAB',
        'grupos': [
            {
                'nombre': "Bienvenida UNAB",
                'resoluciones': ["*"],  # Cualquier resolución
                'dias_antes': [0, 1],
                'filtro_fecha': True,
                'activo': True
            },
            {
                'nombre': "Nurturing UNAB",
                'resoluciones': {
                    'Lunes': [
                        "Se brinda información",
                        "Analizando propuesta",
                        "Oportunidad de venta"
                    ],
                    'Martes': [
                        "No contesta",
                        "Buzón de voz",
                        "Teléfono erróneo",
                        "Imposible contactar"
                    ],
                    'Miércoles': [
                        "Volver a llamar",
                        "Volver a llamar ultimo intento"
                    ],
                    'Jueves': [
                        "Dejo de responder",
                        "Le parece caro",
                        "Siguiente cohorte",
                        "Inscripto en otra universidad"
                    ],
                    'Viernes': [
                        "Horarios",
                        "Motivos personales",
                        "Modalidad de cursado",
                        "No es la oferta buscada"
                    ]
                },
                'filtro_fecha': False,
                'activo': True
            }
        ],
        'columnas_salida': {
            'Nombre': 'Nombre',
            'teltelefono': 'Telefono',
            'emlMail': 'Email',
            'Carrera Interes': 'Programa',
            'TelWhatsapp': 'Whatsapp'
        }
    },
    'ULINEA_ANAHUAC': {
        'nombre': 'ULINEA_ANAHUAC',
        'grupos': [
            {
                'nombre': "Segmentación Base",
                'resoluciones': ["*"],  # Cualquier resolución
                'dias_antes': None,
                'filtro_fecha': False,
                'activo': True
            }
        ],
        'columnas_salida': {
            'Nombre': 'Nombre',
            'teltelefono': 'Telefono',
            'emlMail': 'Email',
            'Ultima Resolución': 'Tipificacion',
            'TelWhatsapp': 'Whatsapp'
        },
        'procesamiento_especial': {
            'limpiar_nombre': True,
            'formatear_resolucion': True
        }
    },
    'PK_CBA': {
        'nombre': 'PK_CBA',
        'grupos': [
            {
                'nombre': "Segmentación Base",
                'resoluciones': ["*"],  # Cualquier resolución
                'dias_antes': None,
                'filtro_fecha': False,
                'activo': True
            }
        ],
        'columnas_salida': {
            'Nombre': 'Nombre',
            'Apellido': 'Apellido',
            'e-Mail': 'Email',
            'Móvil': 'Tel',
            'Carrera de Interes': 'Programa',
            'Cod_Programa': 'Cod_Programa'
        },
        'procesamiento_especial': {
            'limpiar_nombre': True,
            'mapeo_programas': {
                'Abogacía': 1,
                'Tecnicatura Universitaria en Martillero Público y Corredor': 2,
                'Licenciatura en Psicopedagogía': 3,
                '*': 4  # Valor por defecto para otros programas
            }
        }
    }
}

def obtener_configuracion_cliente(cliente_id: str) -> dict:
    """Obtiene la configuración de un cliente específico."""
    return CLIENTES.get(cliente_id, {})

def obtener_lista_clientes() -> list:
    """Obtiene la lista de clientes disponibles."""
    return list(CLIENTES.keys()) 