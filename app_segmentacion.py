import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import tempfile

# Configuración de la página
st.set_page_config(
    page_title="Segmentación de Leads",
    page_icon="📊",
    layout="wide"
)

# Título de la aplicación
st.title("📊 Segmentación de Leads")
st.markdown("""
**Carga tus archivos Excel y descarga los reportes segmentados individualmente.**
""")

# Función para limpiar datos
def limpiar_nombre(nombre):
    return str(nombre).split()[0].lower().capitalize() if pd.notna(nombre) else ''

def limpiar_telefono(numero):
    if pd.isna(numero): return ''
    return ''.join(filter(str.isdigit, str(numero)))

# Widget para subir archivos
uploaded_files = st.file_uploader(
    "Sube tus archivos Excel (puedes seleccionar varios)",
    type=["xls", "xlsx"],
    accept_multiple_files=True
)

# Definición de grupos
grupos = [
    {
        'nombre': "Se brinda información",
        'resoluciones': ["Se brinda información", "Se brinda información Whatsapp", "Volver a llamar"],
        'dias_antes': 1
    },
    {
        'nombre': "Analizando propuesta",
        'resoluciones': ["Analizando propuesta", "Oportunidad de venta", "En proceso de pago"],
        'dias_antes': 2
    },
    {
        'nombre': "Le parece caro",
        'resoluciones': ["Le parece caro", "Siguiente cohorte", "Motivos personales", "No es la oferta buscada"],
        'dias_antes': 2
    },
    {
        'nombre': "No contesta",
        'resoluciones': ["No contesta", "NotProcessed"],
        'dias_antes': None
    },
    {
        'nombre': "Spam",
        'resoluciones': ["Spam - Desconoce haber solicitado informacion", "Telefono erroneo o fuera de servicio", "Pide no ser llamado", "Imposible contactar"],
        'dias_antes': [0, 1]
    }
]

if uploaded_files and st.button("🚀 Ejecutar Segmentación"):
    with st.spinner("Procesando archivos..."):
        try:
            # Leer todos los archivos subidos
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
            
            hoy = datetime.now().date()
            resultados = []
            
            # Procesar cada grupo
            for grupo in grupos:
                df_filtrado = df_unificado[df_unificado['Resolución'].isin(grupo['resoluciones'])]
                
                # Filtrar por fecha
                if grupo['dias_antes'] is not None:
                    if isinstance(grupo['dias_antes'], list):
                        fechas = [hoy - timedelta(days=d) for d in grupo['dias_antes']]
                        df_filtrado = df_filtrado[df_filtrado['Fecha_Lead'].isin(fechas)]
                    else:
                        fecha_objetivo = hoy - timedelta(days=grupo['dias_antes'])
                        df_filtrado = df_filtrado[df_filtrado['Fecha_Lead'] == fecha_objetivo]
                
                if not df_filtrado.empty:
                    resultado = df_filtrado.rename(columns={
                        'teltelefono': 'Telefono',
                        'emlMail': 'Email',
                        'Carrera Interes': 'Programa',
                        'TelWhatsapp': 'Whatsapp',
                        'Fecha Insert Lead': 'Fecha_Contacto'
                    })
                    
                    resultados.append({
                        'nombre': grupo['nombre'],
                        'data': resultado,
                        'filename': f"{grupo['nombre']} {hoy.strftime('%d-%m')}.xlsx"
                    })
            
            # Mostrar resultados para descarga individual
            if resultados:
                st.success("✅ Procesamiento completado!")
                st.subheader("📥 Descargar archivos individuales")
                
                for resultado in resultados:
                    with st.expander(resultado['nombre']):
                        st.dataframe(resultado['data'].head(3))
                        
                        # Convertir DataFrame a Excel en memoria
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            resultado['data'].to_excel(writer, index=False)
                        excel_data = output.getvalue()
                        
                        st.download_button(
                            label=f"Descargar {resultado['nombre']}",
                            data=excel_data,
                            file_name=resultado['filename'],
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
            else:
                st.info("No se generaron archivos (ningún grupo produjo resultados)")
                
        except Exception as e:
            st.error(f"❌ Error en el procesamiento: {str(e)}")

# Instrucciones
with st.expander("ℹ️ Instrucciones de uso"):
    st.markdown("""
    1. **Sube tus archivos Excel** (pueden ser varios)
    2. Haz clic en **Ejecutar Segmentación**
    3. **Descarga los resultados** individualmente desde cada sección
    
    Los archivos generados seguirán el formato:
    - `[Nombre del grupo] [fecha actual].xlsx`
    - Ejemplo: `Se brinda información 25-07.xlsx`
    """)