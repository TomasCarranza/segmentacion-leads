import pandas as pd
import re
import io

def limpiar_nombre(nombre: str) -> str:
    """Limpia y formatea el nombre."""
    if pd.isna(nombre):
        return ''
    # Tomar solo la primera palabra y capitalizar
    return nombre.split()[0].capitalize() if nombre else ''

def limpiar_telefono(telefono: str) -> str:
    """Limpia y formatea el teléfono."""
    if pd.isna(telefono):
        return ''
    # Eliminar caracteres no numéricos
    return ''.join(filter(str.isdigit, str(telefono)))

def limpiar_email(email: str) -> str:
    """Limpia y formatea el email."""
    if pd.isna(email):
        return ''
    return str(email).lower().strip()

def limpiar_programa(programa: str) -> str:
    """Limpia y formatea el programa."""
    if pd.isna(programa):
        return ''
    return str(programa).strip()

def limpiar_resolucion(resolucion: str) -> str:
    """Limpia y formatea la resolución."""
    if pd.isna(resolucion):
        return ''
    
    # Convertir a string y limpiar
    resolucion = str(resolucion).strip()
    
    # Si está vacío, retornar vacío
    if not resolucion:
        return ''
    
    # Para ULINEA y ANAHUAC, extraer solo el número
    if ' - ' in resolucion:
        return resolucion.split(' - ')[0].strip()
    
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
    
    # Limpiar y estandarizar resoluciones (solo limpieza, sin filtrado)
    if 'Ultima Resolución' in df.columns:
        df['Ultima Resolución'] = df['Ultima Resolución'].apply(lambda x: str(x).strip() if pd.notna(x) else '')
    
    return df

def procesar_pk_cba(df: pd.DataFrame) -> pd.DataFrame:
    """Procesa el DataFrame para PK CBA."""
    # Limpiar nombres
    if 'Nombre' in df.columns:
        df['Nombre'] = df['Nombre'].apply(limpiar_nombre)
    
    # Limpiar y estandarizar teléfonos
    if 'Móvil' in df.columns:
        df['Móvil'] = df['Móvil'].apply(limpiar_telefono)
    
    # Limpiar y estandarizar emails
    if 'e-Mail' in df.columns:
        df['e-Mail'] = df['e-Mail'].apply(limpiar_email)
    
    # Limpiar y estandarizar programas
    if 'Carrera de Interes' in df.columns:
        df['Carrera de Interes'] = df['Carrera de Interes'].apply(limpiar_programa)
    
    # Agregar Cod_Programa
    if 'Carrera de Interes' in df.columns:
        df['Cod_Programa'] = df['Carrera de Interes'].apply(lambda x: {
            'Abogacía': '1',
            'Tecnicatura Universitaria en Martillero Público y Corredor': '2',
            'Licenciatura en Psicopedagogía': '3'
        }.get(x, '4'))
    
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
        df['Resolución'] = df['Resolución'].apply(lambda x: str(x).strip() if pd.notna(x) else '')
    
    return df

def procesar_cliente_especifico(df: pd.DataFrame, cliente_id: str) -> pd.DataFrame:
    """Procesa el DataFrame según el cliente específico."""
    # Crear una copia del DataFrame para no modificar el original
    df_procesado = df.copy()
    
    # Mapeo de columnas estándar
    mapeo_estandar = {
        'Email': ['Email', 'e-Mail', 'Correo', 'email', 'e-mail', 'E-mail'],
        'Tel': ['Tel', 'Teléfono', 'Móvil', 'Celular', 'tel', 'telefono', 'Telefono'],
        'Programa': ['Programa', 'Carrera de Interes', 'Carrera', 'programa', 'carrera']
    }
    
    # Encontrar y renombrar columnas según el mapeo
    for col_destino, alternativas in mapeo_estandar.items():
        for alt in alternativas:
            if alt in df_procesado.columns:
                df_procesado[col_destino] = df_procesado[alt]
                break
    
    # Procesar según el cliente
    if cliente_id in ['ULINEA', 'ANAHUAC']:
        if 'Nombre' in df_procesado.columns:
            df_procesado['Nombre'] = df_procesado['Nombre'].apply(limpiar_nombre)
        if 'Tel' in df_procesado.columns:
            df_procesado['Tel'] = df_procesado['Tel'].apply(limpiar_telefono)
        if 'Email' in df_procesado.columns:
            df_procesado['Email'] = df_procesado['Email'].apply(limpiar_email)
        if 'Ultima Resolución' in df_procesado.columns:
            df_procesado['Resolución'] = df_procesado['Ultima Resolución'].apply(lambda x: str(x).strip() if pd.notna(x) else '')
    
    elif cliente_id == 'PK_CBA':
        if 'Nombre' in df_procesado.columns:
            df_procesado['Nombre'] = df_procesado['Nombre'].apply(limpiar_nombre)
        if 'Móvil' in df_procesado.columns:
            df_procesado['Tel'] = df_procesado['Móvil'].apply(limpiar_telefono)
        if 'e-Mail' in df_procesado.columns:
            df_procesado['Email'] = df_procesado['e-Mail'].apply(limpiar_email)
        if 'Carrera de Interes' in df_procesado.columns:
            df_procesado['Programa'] = df_procesado['Carrera de Interes'].apply(limpiar_programa)
    
    elif cliente_id == 'UNAB' or cliente_id == 'CREXE':
        if 'Nombre' in df_procesado.columns:
            df_procesado['Nombre'] = df_procesado['Nombre'].apply(limpiar_nombre)
        if 'Tel' in df_procesado.columns:
            df_procesado['Tel'] = df_procesado['Tel'].apply(limpiar_telefono)
        if 'Email' in df_procesado.columns:
            df_procesado['Email'] = df_procesado['Email'].apply(limpiar_email)
        if 'Programa' in df_procesado.columns:
            df_procesado['Programa'] = df_procesado['Programa'].apply(limpiar_programa)
        if 'Resolución' in df_procesado.columns:
            df_procesado['Resolución'] = df_procesado['Resolución'].apply(lambda x: str(x).strip() if pd.notna(x) else '')
    
    return df_procesado

def cargar_archivo(archivo, cliente_id: str) -> pd.DataFrame:
    """Carga y procesa un archivo según el cliente."""
    try:
        if cliente_id == 'PK_CBA':
            # Intentar diferentes encodings para CSV
            encodings = ['utf-8', 'latin1', 'iso-8859-1']
            for encoding in encodings:
                try:
                    df = pd.read_csv(archivo, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
        else:
            # Para archivos Excel
            df = pd.read_excel(archivo)
        
        return df
    except Exception as e:
        st.error(f"Error al cargar el archivo: {str(e)}")
        return pd.DataFrame()

def generar_archivo_descarga(df: pd.DataFrame, columnas_salida: dict, cliente_id: str) -> bytes:
    """Genera un archivo Excel para descarga sin formato."""
    output = io.BytesIO()
    
    # Crear DataFrame de salida con las columnas solicitadas
    df_salida = pd.DataFrame()
    
    # Copiar las columnas solicitadas
    for col_origen, col_destino in columnas_salida.items():
        if col_origen in df.columns:
            df_salida[col_destino] = df[col_origen]
        else:
            df_salida[col_destino] = ''
    
    # Escribir el archivo sin formato
    with pd.ExcelWriter(output, engine='openpyxl', mode='w') as writer:
        df_salida.to_excel(writer, index=False, sheet_name='Sheet1')
    
    return output.getvalue() 