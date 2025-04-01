import pandas as pd
import re
import io

def limpiar_nombre(nombre: str) -> str:
    """Limpia y formatea el nombre."""
    return str(nombre).split()[0].lower().capitalize() if pd.notna(nombre) else ''

def limpiar_telefono(numero: str) -> str:
    """Elimina caracteres no numéricos de teléfonos."""
    return ''.join(filter(str.isdigit, str(numero))) if pd.notna(numero) else ''

def limpiar_resolucion(resolucion: str) -> str:
    """Limpia y estandariza el formato de resolución."""
    if pd.isna(resolucion):
        return ''
    
    # Convertir a string y limpiar
    resolucion = str(resolucion).strip()
    
    # Si está vacío, retornar vacío
    if not resolucion:
        return ''
    
    # Limitar a 1000 caracteres
    resolucion = resolucion[:1000]
    
    return resolucion

def procesar_ulinea_anahuac(df: pd.DataFrame) -> pd.DataFrame:
    """Procesa el DataFrame para ULINEA y ANAHUAC."""
    # Limpiar nombres
    if 'Nombre' in df.columns:
        df['Nombre'] = df['Nombre'].apply(limpiar_nombre)
    
    # Limpiar y estandarizar teléfonos
    if 'Tel' in df.columns:
        df['Tel'] = df['Tel'].apply(limpiar_telefono)
    
    # Limpiar y estandarizar emails
    if 'Email' in df.columns:
        df['Email'] = df['Email'].apply(limpiar_email)
    
    # Limpiar y estandarizar programas
    if 'Programa' in df.columns:
        df['Programa'] = df['Programa'].apply(limpiar_programa)
    
    # Limpiar y estandarizar resoluciones
    if 'Resolución' in df.columns:
        df['Resolución'] = df['Resolución'].apply(limpiar_resolucion)
        # Limitar a 1000 resoluciones
        df = df[df['Resolución'].str.len() <= 1000]
    
    return df

def procesar_pk_cba(df: pd.DataFrame) -> pd.DataFrame:
    """Procesa el DataFrame para PK CBA."""
    # Limpiar nombres
    if 'Nombre' in df.columns:
        df['Nombre'] = df['Nombre'].apply(limpiar_nombre)
    
    # Agregar Cod_Programa
    if 'Carrera de Interes' in df.columns:
        mapeo_programas = {
            'Abogacía': 1,
            'Tecnicatura Universitaria en Martillero Público y Corredor': 2,
            'Licenciatura en Psicopedagogía': 3
        }
        df['Cod_Programa'] = df['Carrera de Interes'].map(
            lambda x: mapeo_programas.get(str(x).strip(), 4)
        )
    
    # Asegurar que todas las columnas necesarias existan
    columnas_requeridas = {
        'Nombre': 'Nombre',
        'Apellido': 'Apellido',
        'e-Mail': 'Email',
        'Móvil': 'Tel',
        'Carrera de Interes': 'Programa',
        'Cod_Programa': 'Cod_Programa'
    }
    
    for col_origen, col_destino in columnas_requeridas.items():
        if col_origen not in df.columns:
            df[col_origen] = ''  # Agregar columna vacía si no existe
    
    return df

def procesar_unab(df: pd.DataFrame) -> pd.DataFrame:
    """Procesa el DataFrame para UNAB."""
    # Limpiar nombres
    if 'Nombre' in df.columns:
        df['Nombre'] = df['Nombre'].apply(limpiar_nombre)
    
    # Limpiar y estandarizar teléfonos
    if 'Tel' in df.columns:
        df['Tel'] = df['Tel'].apply(limpiar_telefono)
    
    # Limpiar y estandarizar emails
    if 'Email' in df.columns:
        df['Email'] = df['Email'].apply(limpiar_email)
    
    # Limpiar y estandarizar programas
    if 'Programa' in df.columns:
        df['Programa'] = df['Programa'].apply(limpiar_programa)
    
    # Limpiar y estandarizar resoluciones
    if 'Resolución' in df.columns:
        df['Resolución'] = df['Resolución'].apply(limpiar_resolucion)
    
    return df

def procesar_cliente_especifico(df: pd.DataFrame, cliente_id: str) -> pd.DataFrame:
    """Procesa el DataFrame según el cliente específico."""
    if cliente_id == 'ULINEA_ANAHUAC':
        return procesar_ulinea_anahuac(df)
    elif cliente_id == 'PK_CBA':
        return procesar_pk_cba(df)
    elif cliente_id == 'UNAB':
        return procesar_unab(df)
    return df

def cargar_archivo(uploaded_file, cliente_id: str) -> pd.DataFrame:
    """Carga un archivo según el tipo de cliente."""
    try:
        file_ext = uploaded_file.name.split('.')[-1].lower()
        
        if cliente_id == 'PK_CBA' and file_ext == 'csv':
            # Intentar diferentes codificaciones
            codificaciones = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
            for codificacion in codificaciones:
                try:
                    df = pd.read_csv(uploaded_file, encoding=codificacion)
                    if not df.empty and 'Nombre' in df.columns:
                        return df
                except UnicodeDecodeError:
                    continue
            # Si ninguna codificación funciona, intentar con la codificación por defecto
            return pd.read_csv(uploaded_file)
        
        engine = 'xlrd' if file_ext == 'xls' else 'openpyxl'
        return pd.read_excel(uploaded_file, engine=engine)
    except Exception as e:
        raise Exception(f"Error al cargar el archivo {uploaded_file.name}: {str(e)}")

def generar_archivo_descarga(df: pd.DataFrame, columnas_salida: dict, cliente_id: str) -> bytes:
    """Genera el archivo Excel con las columnas específicas para descarga."""
    # Crear DataFrame solo con las columnas deseadas
    df_descarga = pd.DataFrame(columns=columnas_salida.values())
    
    # Copiar datos de las columnas existentes
    for col_origen, col_destino in columnas_salida.items():
        if col_origen in df.columns:
            df_descarga[col_destino] = df[col_origen]
    
    # Generar el archivo en memoria sin formato
    output = io.BytesIO()
    
    # Usar pandas para escribir el archivo sin formato
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Escribir el DataFrame sin formato
        df_descarga.to_excel(writer, index=False, sheet_name='Sheet1')
    
    return output.getvalue() 