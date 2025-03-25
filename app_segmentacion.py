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
    page_title="Segmentación de Leads",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal con estilo mejorado
st.title("📊 **Segmentación de Leads**")
st.markdown("""
    *Personaliza completamente los grupos y criterios de segmentación.*  
    **👈 Configura todo en la barra lateral.** Descarga reportes personalizados ↓
""")

# ====================
# FUNCIONES PRINCIPALES (Optimizadas)
# ====================
def limpiar_nombre(nombre: str) -> str:
    """Limpia y formatea el nombre (primera palabra, formato título)."""
    return str(nombre).split()[0].lower().capitalize() if pd.notna(nombre) else ''

def limpiar_telefono(numero: str) -> str:
    """Elimina caracteres no numéricos de teléfonos."""
    return ''.join(filter(str.isdigit, str(numero))) if pd.notna(numero) else ''

def cargar_archivos(uploaded_files: list) -> pd.DataFrame:
    """Carga y concatena archivos Excel con manejo robusto de formatos."""
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

# ====================
# INTERFAZ DE CONFIGURACIÓN (Mejorada)
# ====================
with st.sidebar:
    # Configuración del ancho de la barra lateral
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
    
    st.header("⚙️ **Configuración Avanzada**")
    
    # 1. Selector de fecha de referencia
    fecha_referencia = st.date_input(
        "📅 Fecha base para segmentación",
        datetime.now(),
        help="Fecha de referencia para calcular los días de filtrado"
    )
    
    # 2. Configuración global
    with st.expander("🔧 **Opciones Generales**", expanded=True):
        eliminar_duplicados = st.checkbox(
            "Eliminar duplicados (por teléfono)",
            value=False, 
            help="Elimina registros con el mismo número telefónico"
        )
        
        mostrar_vista_previa = st.checkbox(
            "Mostrar vista previa",
            value=True,
            help="Muestra las primeras filas de cada grupo"
        )
    
    # 3. Columnas a incluir
    st.header("📋 **Columnas a Incluir**")
    columnas_disponibles = [
        'Nombre', 'teltelefono', 'emlMail', 'Carrera Interes',
        'Resolución', 'Fecha Insert Lead', 'TelWhatsapp'
    ]
    columnas_seleccionadas = st.multiselect(
        "Selecciona las columnas para el reporte final",
        options=columnas_disponibles,
        default=columnas_disponibles,  # Todas seleccionadas por defecto
        help="Elige qué columnas incluir en los archivos de salida"
    )
    
    # 4. Editor completo de grupos
    st.header("✏️ **Editor de Grupos**")
    
    # Inicializar grupos si no existen
    if 'grupos' not in st.session_state:
        st.session_state.grupos = [
            {
                'nombre': "Se brinda información",
                'resoluciones': ["Se brinda información", "Se brinda información Whatsapp", "Volver a llamar"],
                'dias_antes': 1,
                'filtro_fecha': True,
                'activo': True
            },
            {
                'nombre': "No contesta",
                'resoluciones': ["No contesta", "NotProcessed"],
                'dias_antes': None,
                'filtro_fecha': False,
                'activo': True
            }
        ]
    
    # Botón para añadir nuevo grupo
    if st.button("➕ Añadir Grupo", use_container_width=True):
        st.session_state.grupos.append({
            'nombre': f"Nuevo Grupo {len(st.session_state.grupos) + 1}",
            'resoluciones': ["Resolución 1", "Resolución 2"],
            'dias_antes': 1,
            'filtro_fecha': True,
            'activo': True
        })
    
    # Editor dinámico de grupos
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
            
            # Checkbox para activar/desactivar filtro por fecha
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
            
            # Editor de resoluciones
            st.markdown("**Resoluciones a incluir:**")
            grupo['resoluciones'] = st.text_area(
                "Una por línea",
                value="\n".join(grupo['resoluciones']),
                key=f"res_{i}",
                height=100
            ).split('\n')
            
            # Botón para eliminar grupo
            if st.button(f"❌ Eliminar grupo", key=f"del_{i}"):
                st.session_state.grupos.pop(i)
                st.rerun()

# ====================
# PROCESAMIENTO PRINCIPAL (Optimizado)
# ====================
uploaded_files = st.file_uploader(
    "📤 **Sube tus archivos Excel** (.xls o .xlsx)",
    type=["xls", "xlsx"],
    accept_multiple_files=True,
    help="Puedes seleccionar múltiples archivos"
)

if uploaded_files and st.button("🚀 **Ejecutar Segmentación**", type="primary", use_container_width=True):
    with st.spinner("Procesando datos..."):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Etapa 1: Carga de archivos
            status_text.info("📂 Cargando archivos...")
            df_unificado = cargar_archivos(uploaded_files)
            progress_bar.progress(20)
            
            if df_unificado.empty:
                st.error("❌ No se encontraron datos válidos")
                st.stop()
            
            # Verificar columnas seleccionadas
            columnas_faltantes = [col for col in columnas_seleccionadas if col not in df_unificado.columns]
            if columnas_faltantes:
                st.error(f"❌ Columnas no encontradas: {', '.join(columnas_faltantes)}")
                st.stop()
            
            # Etapa 2: Limpieza de datos
            status_text.info("🧹 Limpiando datos...")
            if 'Nombre' in columnas_seleccionadas:
                df_unificado['Nombre'] = df_unificado['Nombre'].apply(limpiar_nombre)
            if 'teltelefono' in columnas_seleccionadas:
                df_unificado['teltelefono'] = df_unificado['teltelefono'].apply(limpiar_telefono)
            if 'TelWhatsapp' in columnas_seleccionadas:
                df_unificado['TelWhatsapp'] = df_unificado['TelWhatsapp'].apply(limpiar_telefono)
            
            # Etapa 3: Procesamiento de fechas
            if 'Fecha Insert Lead' in columnas_seleccionadas:
                df_unificado['Fecha_Lead'] = pd.to_datetime(
                    df_unificado['Fecha Insert Lead'], 
                    format='%d-%m-%Y %H:%M:%S',
                    errors='coerce'
                ).dt.date
                
                # Filtrar inválidos
                n_invalidos = df_unificado['Fecha_Lead'].isna().sum()
                if n_invalidos > 0:
                    st.warning(f"⚠️ Se omitieron {n_invalidos} registros con fechas no reconocidas")
                    df_unificado = df_unificado.dropna(subset=['Fecha_Lead'])
            
            progress_bar.progress(40)
            
            # Etapa 4: Procesamiento por grupos
            resultados = []
            grupos_activos = [g for g in st.session_state.grupos if g['activo']]
            
            for i, grupo in enumerate(grupos_activos):
                status_text.info(f"🔍 Procesando grupo: {grupo['nombre']} ({i+1}/{len(grupos_activos)})")
                
                # Filtrar por resoluciones
                df_filtrado = df_unificado[df_unificado['Resolución'].isin(grupo['resoluciones'])]
                
                # Filtrar por fecha si está activado
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
                    
                    # Seleccionar solo las columnas elegidas
                    df_final = df_filtrado[columnas_seleccionadas].copy()
                    
                    # Renombrar columnas para el output
                    mapeo_nombres = {
                        'teltelefono': 'Telefono',
                        'emlMail': 'Email',
                        'Carrera Interes': 'Programa',
                        'TelWhatsapp': 'Whatsapp',
                        'Fecha Insert Lead': 'Fecha_Contacto'
                    }
                    df_final = df_final.rename(columns={k: v for k, v in mapeo_nombres.items() if k in df_final.columns})
                    
                    resultados.append({
                        'nombre': grupo['nombre'],
                        'data': df_final,
                        'registros': len(df_filtrado),
                        'filename': f"{grupo['nombre']} {fecha_referencia.strftime('%d-%m-%Y')}.xlsx"
                    })
                
                progress_bar.progress(40 + int(50 * (i+1)/len(grupos_activos)))
            
            # Resultados finales
            progress_bar.progress(100)
            time.sleep(0.5)
            progress_bar.empty()
            status_text.empty()
            
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
                        
                        # Generar Excel en memoria
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            resultado['data'].to_excel(writer, index=False)
                        
                        st.download_button(
                            label=f"⬇️ Descargar {resultado['nombre']}",
                            data=output.getvalue(),
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
with st.expander("📚 **Guía Completa**", expanded=False):
    st.markdown("""
    ### 🎯 **Cómo usar esta herramienta**
    1. **Configura los grupos** en la barra lateral
    2. **Selecciona las columnas** a incluir
    3. **Sube tus archivos Excel** (.xls o .xlsx)
    4. **Ejecuta la segmentación**
    5. **Descarga los reportes** individuales

    ### ⚙️ **Funcionalidades clave**
    - **Selección de columnas**: Elige qué datos incluir
    - **Filtro flexible**: Activa/desactiva por grupo
    - **Vista previa**: Antes de descargar
    - **Eliminar duplicados**: Opcional por teléfono

    ### 💡 **Consejos**
    - Para grupos como "No contesta", desactiva el filtro por fecha
    - Revisa las columnas disponibles en tus archivos
    """)

# Créditos
st.caption("""
    *Sistema de segmentación automatizada | v2.2 | {date}*
""".format(date=datetime.now().strftime("%d/%m/%Y")))