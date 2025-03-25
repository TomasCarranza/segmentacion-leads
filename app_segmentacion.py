import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import zipfile
import tempfile

# Configuración de la página
st.set_page_config(
    page_title="Segmentación Avanzada de Leads",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título de la aplicación
st.title("🎚️ Segmentación Avanzada de Leads")
st.markdown("""
**Configura tus parámetros de segmentación y procesa los archivos Excel automáticamente.**
""")

# Función para limpiar datos
def limpiar_nombre(nombre):
    return str(nombre).split()[0].lower().capitalize() if pd.notna(nombre) else ''

def limpiar_telefono(numero):
    if pd.isna(numero): return ''
    return ''.join(filter(str.isdigit, str(numero)))

# Inicializar parámetros en session state
if 'grupos' not in st.session_state:
    st.session_state.grupos = [
        {
            'nombre': "Se brinda información",
            'resoluciones': ["Se brinda información", "Se brinda información Whatsapp", "Volver a llamar"],
            'dias_antes': 1,
            'activo': True
        },
        {
            'nombre': "Analizando propuesta",
            'resoluciones': ["Analizando propuesta", "Oportunidad de venta", "En proceso de pago"],
            'dias_antes': 2,
            'activo': True
        },
        {
            'nombre': "Le parece caro",
            'resoluciones': ["Le parece caro", "Siguiente cohorte", "Motivos personales", "No es la oferta buscada"],
            'dias_antes': 2,
            'activo': True
        },
        {
            'nombre': "No contesta",
            'resoluciones': ["No contesta", "NotProcessed"],
            'dias_antes': None,
            'activo': True
        },
        {
            'nombre': "Spam",
            'resoluciones': ["Spam - Desconoce haber solicitado informacion", "Telefono erroneo o fuera de servicio", "Pide no ser llamado", "Imposible contactar"],
            'dias_antes': [0, 1],
            'activo': True
        }
    ]

# Sidebar para configuración
with st.sidebar:
    st.header("⚙️ Configuración Global")
    fecha_referencia = st.date_input("Fecha de referencia para segmentación", datetime.now())
    
    st.header("🔧 Configurar Grupos")
    
    # Botón para añadir nuevo grupo
    if st.button("➕ Añadir nuevo grupo"):
        st.session_state.grupos.append({
            'nombre': "Nuevo grupo",
            'resoluciones': [],
            'dias_antes': 1,
            'activo': True
        })
    
    # Editar grupos existentes
    for i, grupo in enumerate(st.session_state.grupos):
        with st.expander(f"Grupo: {grupo['nombre']}", expanded=True):
            grupo['activo'] = st.checkbox("Activo", value=grupo['activo'], key=f"activo_{i}")
            grupo['nombre'] = st.text_input("Nombre", value=grupo['nombre'], key=f"nombre_{i}")
            
            # Configurar días antes
            if isinstance(grupo['dias_antes'], list):
                grupo['dias_antes'] = st.multiselect(
                    "Días a incluir",
                    options=[0, 1, 2, 3, 4, 5],
                    default=grupo['dias_antes'],
                    key=f"dias_{i}"
                )
            elif grupo['dias_antes'] is not None:
                grupo['dias_antes'] = st.number_input(
                    "Días antes",
                    min_value=0,
                    value=grupo['dias_antes'],
                    key=f"dias_{i}"
                )
            else:
                st.info("Este grupo incluye todos los registros sin filtrar por fecha")
            
            grupo['resoluciones'] = st.text_area(
                "Resoluciones (una por línea)",
                value="\n".join(grupo['resoluciones']),
                key=f"res_{i}"
            ).split("\n")
            
            # Botón para eliminar grupo
            if st.button(f"❌ Eliminar este grupo", key=f"del_{i}"):
                st.session_state.grupos.pop(i)
                st.rerun()

# Widget para subir archivos
uploaded_files = st.file_uploader(
    "Sube tus archivos Excel (puedes seleccionar varios)",
    type=["xls", "xlsx"],
    accept_multiple_files=True
)

# Procesar archivos
if uploaded_files and st.button("🚀 Ejecutar Segmentación", type="primary"):
    with st.spinner("Procesando archivos..."):
        try:
            # Leer todos los archivos
            dfs = []
            for uploaded_file in uploaded_files:
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    tmp.write(uploaded_file.getvalue())
                    df = pd.read_excel(tmp.name, usecols=[
                        'Nombre', 'teltelefono', 'emlMail', 'Carrera Interes', 
                        'Resolución', 'Fecha Insert Lead', 'TelWhatsapp'
                    ])
                    dfs.append(df)
                os.unlink(tmp.name)
            
            df_unificado = pd.concat(dfs, ignore_index=True)
            
            # Limpieza de datos
            df_unificado['Nombre'] = df_unificado['Nombre'].apply(limpiar_nombre)
            df_unificado['teltelefono'] = df_unificado['teltelefono'].apply(limpiar_telefono)
            df_unificado['TelWhatsapp'] = df_unificado['TelWhatsapp'].apply(limpiar_telefono)
            
            # Procesar fechas
            df_unificado['Fecha_Lead'] = pd.to_datetime(
                df_unificado['Fecha Insert Lead'], 
                format='%d-%m-%Y %H:%M:%S',
                errors='coerce'
            ).dt.date
            
            # Filtrar inválidos
            registros_invalidos = df_unificado['Fecha_Lead'].isna().sum()
            if registros_invalidos > 0:
                st.warning(f"Se descartaron {registros_invalidos} registros con fechas inválidas")
                df_unificado = df_unificado.dropna(subset=['Fecha_Lead'])
            
            # Procesar cada grupo activo
            os.makedirs("resultados", exist_ok=True)
            resultados_generados = []
            
            for grupo in [g for g in st.session_state.grupos if g['activo']]:
                df_filtrado = df_unificado[df_unificado['Resolución'].isin(grupo['resoluciones'])]
                
                # Filtrar por fecha
                if grupo['dias_antes'] is not None:
                    if isinstance(grupo['dias_antes'], list):
                        fechas = [fecha_referencia - timedelta(days=d) for d in grupo['dias_antes']]
                        df_filtrado = df_filtrado[df_filtrado['Fecha_Lead'].isin(fechas)]
                    else:
                        fecha_objetivo = fecha_referencia - timedelta(days=grupo['dias_antes'])
                        df_filtrado = df_filtrado[df_filtrado['Fecha_Lead'] == fecha_objetivo]
                
                if not df_filtrado.empty:
                    resultado = df_filtrado.rename(columns={
                        'teltelefono': 'Telefono',
                        'emlMail': 'Email',
                        'Carrera Interes': 'Programa',
                        'TelWhatsapp': 'Whatsapp',
                        'Fecha Insert Lead': 'Fecha_Contacto'
                    })
                    
                    # Guardar archivo
                    nombre_archivo = f"resultados/{grupo['nombre']} {fecha_referencia.strftime('%d-%m')}.xlsx"
                    resultado.to_excel(nombre_archivo, index=False)
                    resultados_generados.append(nombre_archivo)
            
            # Crear ZIP con resultados
            if resultados_generados:
                with zipfile.ZipFile("resultados.zip", "w") as zipf:
                    for archivo in resultados_generados:
                        zipf.write(archivo)
                
                # Mostrar resultados
                st.success("✅ Procesamiento completado!")
                st.download_button(
                    label="📦 Descargar todos los resultados",
                    data=open("resultados.zip", "rb").read(),
                    file_name="resultados_segmentacion.zip",
                    mime="application/zip"
                )
                
                # Mostrar resumen
                st.subheader("Resumen de ejecución")
                col1, col2 = st.columns(2)
                col1.metric("Registros procesados", len(df_unificado))
                col2.metric("Archivos generados", len(resultados_generados))
                
                # Limpiar archivos temporales
                for archivo in resultados_generados:
                    os.unlink(archivo)
                os.unlink("resultados.zip")
            else:
                st.info("No se generaron archivos (ningún grupo produjo resultados)")
                
        except Exception as e:
            st.error(f"❌ Error en el procesamiento: {str(e)}")
            st.exception(e)

# Instrucciones
with st.expander("📌 Instrucciones de uso", expanded=True):
    st.markdown("""
    1. **Configura los grupos** en el panel lateral (puedes añadir/eliminar/modificar)
    2. **Sube tus archivos Excel** (pueden ser varios)
    3. Haz clic en **Ejecutar Segmentación**
    4. **Descarga los resultados** en formato ZIP
    
    Características:
    - Configuración personalizable de grupos
    - Filtrado flexible por fechas
    - Limpieza automática de datos
    - Soporte para múltiples archivos de entrada
    """)

# Notas
st.caption("""
*Nota: Los archivos se procesan en memoria y no se almacenan en el servidor después de la descarga.*
""")