import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
import tempfile
import os
import time

# ====================
# CONFIGURACIÓN INICIAL
# ====================
st.set_page_config(
    page_title="🚀 Segmentación Avanzada de Leads",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo para la barra lateral al 40%
st.markdown(
    """
    <style>
        section[data-testid="stSidebar"] {
            width: 40% !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Título principal
st.title("📊 **Segmentación de Leads Avanzada**")
st.markdown("""
    *Personaliza completamente los grupos y criterios de segmentación.*  
    **👈 Configura todo en la barra lateral**
""")

# ====================
# FUNCIONES PRINCIPALES
# ====================
def limpiar_nombre(nombre: str) -> str:
    """Limpia y formatea el nombre."""
    return str(nombre).split()[0].lower().capitalize() if pd.notna(nombre) else ''

def limpiar_telefono(numero: str) -> str:
    """Elimina caracteres no numéricos de teléfonos."""
    return ''.join(filter(str.isdigit, str(numero))) if pd.notna(numero) else ''

def cargar_archivos(uploaded_files: list) -> pd.DataFrame:
    """Carga y concatena archivos Excel."""
    dfs = []
    for uploaded_file in uploaded_files:
        try:
            file_ext = uploaded_file.name.split('.')[-1].lower()
            engine = 'xlrd' if file_ext == 'xls' else 'openpyxl'
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp:
                tmp.write(uploaded_file.getvalue())
                df = pd.read_excel(tmp.name, engine=engine)
                dfs.append(df)
            os.unlink(tmp.name)
        except Exception as e:
            st.warning(f"⚠️ No se pudo procesar {uploaded_file.name}: {str(e)}")
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

def generar_archivo_descarga(df_filtrado: pd.DataFrame) -> bytes:
    """Genera el archivo Excel con las columnas específicas para descarga"""
    # Columnas base que necesitamos
    columnas_base = {
        'Nombre': '',
        'Telefono': '',
        'Email': '',
        'Programa': '',
        'Whatsapp': ''
    }
    
    # Crear DataFrame solo con las columnas deseadas
    df_descarga = pd.DataFrame(columns=columnas_base.keys())
    
    # Mapear las columnas del DataFrame procesado a las de salida
    mapeo_columnas = {
        'Nombre': 'Nombre',
        'teltelefono': 'Telefono',
        'emlMail': 'Email',
        'Carrera Interes': 'Programa',
        'TelWhatsapp': 'Whatsapp'
    }
    
    # Copiar datos de las columnas existentes
    for col_origen, col_destino in mapeo_columnas.items():
        if col_origen in df_filtrado.columns:
            df_descarga[col_destino] = df_filtrado[col_origen]
    
    # Generar el archivo en memoria
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_descarga.to_excel(writer, index=False)
    return output.getvalue()

# ====================
# INTERFAZ DE USUARIO
# ====================
with st.sidebar:
    st.header("⚙️ **Configuración**")
    
    # 1. Fecha de referencia
    fecha_referencia = st.date_input(
        "📅 Fecha base para segmentación",
        datetime.now()
    )
    
    # 2. Opciones generales
    with st.expander("🔧 **Opciones Generales**", expanded=True):
        eliminar_duplicados = st.checkbox(
            "Eliminar duplicados (por teléfono)",
            value=False
        )
        
        mostrar_vista_previa = st.checkbox(
            "Mostrar vista previa",
            value=True
        )
    
    # 3. Editor de grupos
    st.header("✏️ **Editor de Grupos**")
    
    # Inicializar grupos con los valores predeterminados solicitados
if 'grupos' not in st.session_state:
    st.session_state.grupos = [
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
            'dias_antes': [0, 1],  # 0 es el día actual, 1 es un día antes
            'filtro_fecha': True,
            'activo': True
        }
    ]
    
    # Botón para añadir grupo
    if st.button("➕ Añadir Grupo", use_container_width=True):
        st.session_state.grupos.append({
            'nombre': f"Nuevo Grupo {len(st.session_state.grupos) + 1}",
            'resoluciones': ["Resolución 1", "Resolución 2"],
            'dias_antes': 1,
            'filtro_fecha': True,
            'activo': True
        })
    
    # Editor de grupos
    for i, grupo in enumerate(st.session_state.grupos[:]):
        with st.expander(f"**{grupo['nombre']}**", expanded=True):
            grupo['nombre'] = st.text_input(
                "Nombre del grupo",
                value=grupo['nombre'],
                key=f"nombre_{i}"
            )
            
            grupo['activo'] = st.checkbox(
                "Activo",
                value=grupo['activo'],
                key=f"activo_{i}"
            )
            
            grupo['filtro_fecha'] = st.checkbox(
                "Filtrar por fecha",
                value=grupo.get('filtro_fecha', True),
                key=f"filtro_fecha_{i}"
            )
            
            if grupo['filtro_fecha']:
                if st.checkbox("Usar múltiples días", value=isinstance(grupo['dias_antes'], list), key=f"multidias_{i}"):
                    grupo['dias_antes'] = st.multiselect(
                        "Días a incluir",
                        options=list(range(8)),
                        default=grupo['dias_antes'] if isinstance(grupo['dias_antes'], list) else [1],
                        key=f"dias_ms_{i}"
                    )
                else:
                    grupo['dias_antes'] = st.number_input(
                        "Días antes",
                        min_value=0,
                        value=grupo['dias_antes'] if isinstance(grupo['dias_antes'], int) else 1,
                        key=f"dias_num_{i}"
                    )
            else:
                grupo['dias_antes'] = None
            
            st.markdown("**Resoluciones a incluir:**")
            grupo['resoluciones'] = st.text_area(
                "Una por línea",
                value="\n".join(grupo['resoluciones']),
                key=f"res_{i}",
                height=100
            ).split('\n')
            
            if st.button(f"❌ Eliminar grupo", key=f"del_{i}"):
                st.session_state.grupos.pop(i)
                st.rerun()

# ====================
# PROCESAMIENTO PRINCIPAL
# ====================
uploaded_files = st.file_uploader(
    "📤 **Sube tus archivos Excel** (.xls o .xlsx)",
    type=["xls", "xlsx"],
    accept_multiple_files=True
)

if uploaded_files and st.button("🚀 **Ejecutar Segmentación**", type="primary", use_container_width=True):
    with st.spinner("Procesando datos..."):
        progress_bar = st.progress(0)
        status_text = st.empty()
        registros_invalidos = None
        
        try:
            # 1. Carga de archivos
            status_text.info("📂 Cargando archivos...")
            df_unificado = cargar_archivos(uploaded_files)
            progress_bar.progress(20)
            
            if df_unificado.empty:
                st.error("❌ No se encontraron datos válidos")
                st.stop()
            
            # 2. Limpieza de datos
            status_text.info("🧹 Limpiando datos...")
            if 'Nombre' in df_unificado.columns:
                df_unificado['Nombre'] = df_unificado['Nombre'].apply(limpiar_nombre)
            if 'teltelefono' in df_unificado.columns:
                df_unificado['teltelefono'] = df_unificado['teltelefono'].apply(limpiar_telefono)
            if 'TelWhatsapp' in df_unificado.columns:
                df_unificado['TelWhatsapp'] = df_unificado['TelWhatsapp'].apply(limpiar_telefono)
            
            # 3. Procesamiento de fechas
            if 'Fecha Insert Lead' in df_unificado.columns:
                df_unificado['Fecha_Lead'] = pd.to_datetime(
                    df_unificado['Fecha Insert Lead'], 
                    format='%d-%m-%Y %H:%M:%S',
                    errors='coerce'
                ).dt.date
                
                # Identificar registros con fechas inválidas
                registros_invalidos = df_unificado[df_unificado['Fecha_Lead'].isna()].copy()
                n_invalidos = len(registros_invalidos)
                
                if n_invalidos > 0:
                    df_unificado = df_unificado.dropna(subset=['Fecha_Lead'])
            
            progress_bar.progress(40)
            
            # 4. Procesamiento por grupos
            resultados = []
            grupos_activos = [g for g in st.session_state.grupos if g['activo']]
            
            for i, grupo in enumerate(grupos_activos):
                status_text.info(f"🔍 Procesando grupo: {grupo['nombre']} ({i+1}/{len(grupos_activos)})")
                
                df_filtrado = df_unificado[df_unificado['Resolución'].isin(grupo['resoluciones'])]
                
                if grupo['filtro_fecha'] and grupo['dias_antes'] is not None and 'Fecha_Lead' in df_unificado.columns:
                    if isinstance(grupo['dias_antes'], list):
                        fechas = [fecha_referencia - timedelta(days=d) for d in grupo['dias_antes']]
                        df_filtrado = df_filtrado[df_filtrado['Fecha_Lead'].isin(fechas)]
                    else:
                        fecha_objetivo = fecha_referencia - timedelta(days=grupo['dias_antes'])
                        df_filtrado = df_filtrado[df_filtrado['Fecha_Lead'] == fecha_objetivo]
                
                if not df_filtrado.empty:
                    if eliminar_duplicados and 'teltelefono' in df_filtrado.columns:
                        df_filtrado = df_filtrado.drop_duplicates(subset=['teltelefono'])
                    
                    # Generar archivo con columnas específicas
                    archivo_descarga = generar_archivo_descarga(df_filtrado)
                    
                    resultados.append({
                        'nombre': grupo['nombre'],
                        'data': df_filtrado,  # Mantenemos todos los datos para la vista previa
                        'archivo': archivo_descarga,  # Archivo ya formateado
                        'registros': len(df_filtrado),
                        'filename': f"{grupo['nombre']} {fecha_referencia.strftime('%d-%m-%Y')}.xlsx"
                    })
                
                progress_bar.progress(40 + int(50 * (i+1)/len(grupos_activos)))
            
            # Resultados finales
            progress_bar.progress(100)
            time.sleep(0.5)
            progress_bar.empty()
            status_text.empty()
            
            if registros_invalidos is not None and len(registros_invalidos) > 0:
                st.warning(f"⚠️ Se omitieron {len(registros_invalidos)} registros con fechas no reconocidas")
                
                # Botón para descargar registros omitidos
                output_invalidos = io.BytesIO()
                with pd.ExcelWriter(output_invalidos, engine='openpyxl') as writer:
                    registros_invalidos.to_excel(writer, index=False)
                
                st.download_button(
                    label="⬇️ Descargar registros omitidos",
                    data=output_invalidos.getvalue(),
                    file_name=f"Registros_omitidos_{fecha_referencia.strftime('%d-%m-%Y')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            if resultados:
                st.balloons()
                st.success(f"✅ ¡Procesamiento completado! ({len(resultados)} grupos generados)")
                
                # Métricas resumidas
                cols = st.columns(3)
                cols[0].metric("📂 Archivos", len(uploaded_files))
                cols[1].metric("👥 Leads", len(df_unificado))
                cols[2].metric("📊 Grupos", len(resultados))
                
                # Descargas individuales
                st.subheader("📥 **Descargar Reportes**", divider="rainbow")
                for resultado in resultados:
                    with st.expander(f"**{resultado['nombre']}** ({resultado['registros']} registros)", expanded=True):
                        if mostrar_vista_previa:
                            st.dataframe(
                                resultado['data'].head(3),
                                use_container_width=True,
                                hide_index=True
                            )
                        
                        st.download_button(
                            label=f"⬇️ Descargar {resultado['nombre']}",
                            data=resultado['archivo'],
                            file_name=resultado['filename'],
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                            type="primary",
                            key=f"dl_{resultado['filename']}"
                        )
            else:
                st.info("📭 No se generaron resultados. Ajusta tus criterios de filtrado.")
        
        except Exception as e:
            progress_bar.empty()
            status_text.error(f"❌ Error: {str(e)}")
            st.exception(e)

# ====================
# SECCIÓN DE AYUDA
# ====================
with st.expander("📚 **Guía de Uso**", expanded=False):
    st.markdown("""
    ### 🎯 **Cómo usar esta herramienta**
    1. **Configura los grupos** en la barra lateral
    2. **Sube tus archivos Excel** (.xls o .xlsx)
    3. **Ejecuta la segmentación**
    4. **Descarga los reportes** individuales

    ### 📂 **Formato de salida**
    Los archivos descargados contendrán exactamente estas columnas:
    - Nombre
    - Telefono
    - Email
    - Programa
    - Whatsapp

    ### ⚠️ **Registros omitidos**
    - Si hay registros con fechas inválidas, podrás descargarlos
    - Revisa el formato de fecha en tus archivos (debe ser DD-MM-AAAA HH:MM:SS)
    """)

# Créditos
st.caption(f"*Sistema de segmentación automatizada | v2.4 | {datetime.now().strftime('%d/%m/%Y')}*")