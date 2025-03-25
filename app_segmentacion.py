import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
import tempfile
import os
from typing import List, Dict, Optional
import time

# ====================
# CONFIGURACIÓN INICIAL
# ====================
st.set_page_config(
    page_title="Segmentación de Leads",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal con estilo
st.title("📊 **Segmentación de Leads**")
st.markdown("""
    *Carga tus archivos Excel (.xls o .xlsx) y genera bases segmentadas.*  
    **↓ Configura los parámetros en la barra lateral ↓**
""")

# ====================
# FUNCIONES PRINCIPALES
# ====================
def limpiar_nombre(nombre: str) -> str:
    """Limpia y formatea el nombre (primera palabra, formato título)."""
    return str(nombre).split()[0].lower().capitalize() if pd.notna(nombre) else ''

def limpiar_telefono(numero: str) -> str:
    """Elimina caracteres no numéricos de teléfonos."""
    if pd.isna(numero):
        return ''
    return ''.join(filter(str.isdigit, str(numero)))

def cargar_archivos(uploaded_files: List) -> Optional[pd.DataFrame]:
    """Carga y concatena archivos Excel, manejando formatos .xls y .xlsx."""
    dfs = []
    for uploaded_file in uploaded_files:
        try:
            file_ext = uploaded_file.name.split('.')[-1].lower()
            engine = 'xlrd' if file_ext == 'xls' else 'openpyxl'
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            
            df = pd.read_excel(
                tmp_path,
                engine=engine,
                usecols=[
                    'Nombre', 'teltelefono', 'emlMail', 'Carrera Interes', 
                    'Resolución', 'Fecha Insert Lead', 'TelWhatsapp'
                ]
            )
            dfs.append(df)
            os.unlink(tmp_path)  # Elimina el temporal
            
        except Exception as e:
            st.error(f"Error al procesar {uploaded_file.name}: {str(e)}")
            continue
    
    return pd.concat(dfs, ignore_index=True) if dfs else None

# ====================
# INTERFAZ DE USUARIO
# ====================
with st.sidebar:
    st.header("⚙️ **Configuración**")
    
    # Selector de fecha de referencia
    fecha_referencia = st.date_input(
        "📅 Fecha de referencia para segmentación",
        datetime.now(),
        help="Las fechas de los leads se compararán con esta fecha."
    )
    
    # Configuración avanzada
    with st.expander("🔧 **Ajustes Avanzados**", expanded=False):
        eliminar_duplicados = st.checkbox(
            "Eliminar registros duplicados (por teléfono)",
            value=True,
            help="Si está activado, elimina leads con el mismo número telefónico."
        )
        
        mostrar_vista_previa = st.checkbox(
            "Mostrar vista previa de datos",
            value=True,
            help="Muestra las primeras filas de cada grupo antes de descargar."
        )

# ====================
# DEFINICIÓN DE GRUPOS (EDITABLE)
# ====================
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

# ====================
# PROCESAMIENTO PRINCIPAL
# ====================
uploaded_files = st.file_uploader(
    "📤 **Sube tus archivos Excel** (arrastra o haz clic)",
    type=["xls", "xlsx"],
    accept_multiple_files=True,
    help="Puedes seleccionar múltiples archivos. Se unirán automáticamente."
)

if uploaded_files:
    if st.button("🚀 **Ejecutar**", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Paso 1: Cargar y unificar archivos
            status_text.text("🔄 Cargando y unificando archivos...")
            df_unificado = cargar_archivos(uploaded_files)
            progress_bar.progress(20)
            
            if df_unificado is None:
                st.error("No se pudo cargar ningún archivo válido.")
                st.stop()
            
            # Paso 2: Limpieza de datos
            status_text.text("🧹 Limpiando y formateando datos...")
            df_unificado['Nombre'] = df_unificado['Nombre'].apply(limpiar_nombre)
            df_unificado['teltelefono'] = df_unificado['teltelefono'].apply(limpiar_telefono)
            df_unificado['TelWhatsapp'] = df_unificado['TelWhatsapp'].apply(limpiar_telefono)
            
            # Paso 3: Procesar fechas
            df_unificado['Fecha_Lead'] = pd.to_datetime(
                df_unificado['Fecha Insert Lead'], 
                format='%d-%m-%Y %H:%M:%S',
                errors='coerce'
            ).dt.date
            
            # Filtrar registros con fechas inválidas
            registros_invalidos = df_unificado['Fecha_Lead'].isna().sum()
            if registros_invalidos > 0:
                st.warning(f"⚠️ Se descartaron {registros_invalidos} registros con fechas inválidas")
                df_unificado = df_unificado.dropna(subset=['Fecha_Lead'])
            
            progress_bar.progress(50)
            
            # Paso 4: Procesar cada grupo
            resultados = []
            for grupo in [g for g in st.session_state.grupos if g['activo']]:
                # Filtrar por resoluciones
                df_filtrado = df_unificado[df_unificado['Resolución'].isin(grupo['resoluciones'])]
                
                # Filtrar por fecha si es necesario
                if grupo['dias_antes'] is not None:
                    if isinstance(grupo['dias_antes'], list):
                        fechas = [fecha_referencia - timedelta(days=d) for d in grupo['dias_antes']]
                        df_filtrado = df_filtrado[df_filtrado['Fecha_Lead'].isin(fechas)]
                    else:
                        fecha_objetivo = fecha_referencia - timedelta(days=grupo['dias_antes'])
                        df_filtrado = df_filtrado[df_filtrado['Fecha_Lead'] == fecha_objetivo]
                
                if not df_filtrado.empty:
                    # Eliminar duplicados si está activado
                    if eliminar_duplicados:
                        df_filtrado = df_filtrado.drop_duplicates(subset=['teltelefono'])
                    
                    resultados.append({
                        'nombre': grupo['nombre'],
                        'data': df_filtrado.rename(columns={
                            'teltelefono': 'Telefono',
                            'emlMail': 'Email',
                            'Carrera Interes': 'Programa',
                            'TelWhatsapp': 'Whatsapp',
                            'Fecha Insert Lead': 'Fecha_Contacto'
                        }),
                        'registros': len(df_filtrado),
                        'filename': f"{grupo['nombre']} {fecha_referencia.strftime('%d-%m-%Y')}.xlsx"
                    })
            
            progress_bar.progress(90)
            
            # Mostrar resultados
            status_text.text("✅ ¡Procesamiento completado!")
            time.sleep(0.5)
            progress_bar.empty()
            status_text.empty()
            
            if resultados:
                st.success(f"**Segmentación completada** - {len(resultados)} grupos generados")
                
                # Mostrar métricas generales
                total_registros = sum(r['registros'] for r in resultados)
                cols = st.columns(3)
                cols[0].metric("📂 Archivos cargados", len(uploaded_files))
                cols[1].metric("🧑‍💻 Leads procesados", len(df_unificado))
                cols[2].metric("📊 Grupos generados", len(resultados))
                
                # Descargas individuales
                st.subheader("📥 Descargar Reportes", divider="blue")
                for resultado in resultados:
                    with st.expander(f"**{resultado['nombre']}** ({resultado['registros']} registros)", expanded=True):
                        if mostrar_vista_previa:
                            st.dataframe(
                                resultado['data'].head(3),
                                use_container_width=True,
                                hide_index=True
                            )
                        
                        # Convertir DataFrame a Excel en memoria
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            resultado['data'].to_excel(writer, index=False)
                        
                        st.download_button(
                            label=f"⬇️ Descargar {resultado['nombre']}",
                            data=output.getvalue(),
                            file_name=resultado['filename'],
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                            key=f"download_{resultado['nombre']}"
                        )
            else:
                st.info("📭 No se generaron archivos (ningún grupo produjo resultados)")
                
        except Exception as e:
            progress_bar.empty()
            status_text.error(f"❌ **Error crítico**: {str(e)}")
            st.exception(e)

# ====================
# SECCIÓN DE AYUDA
# ====================
with st.expander("ℹ️ **Instrucciones detalladas**", expanded=False):
    st.markdown("""
    ### 📌 **Cómo usar esta herramienta**
    1. **Sube tus archivos Excel** (formato .xls o .xlsx)
    2. **Configura los parámetros** en la barra lateral:
       - 📅 Fecha de referencia para la segmentación
       - 🔧 Opciones avanzadas (eliminar duplicados, vista previa)
    3. **Haz clic en 'Ejecutar Segmentación'**
    4. **Descarga los reportes** individualmente desde cada sección

    ### 🔍 **Sobre los grupos**
    - Cada grupo filtra por **resoluciones específicas** y **rango de fechas**
    - Puedes editar los grupos directamente en el código (variable `grupos`)
    - Los archivos generados siguen el formato:  
      `[Nombre del grupo] [Fecha de referencia].xlsx`
    """)

# Nota al pie
st.caption("""
    *Nota: Los datos se procesan en memoria y no se almacenan en el servidor después de cerrar la sesión.*  
""")