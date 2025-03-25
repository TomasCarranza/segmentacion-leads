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

# Título principal con estilo mejorado
st.title("📊 **Segmentación de Leads Avanzada**")
st.markdown("""
    *Personaliza completamente los grupos y criterios de segmentación.*  
    **👈 Configura todo en la barra lateral** → Descarga reportes personalizados ↓
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
                df = pd.read_excel(tmp.name, engine=engine, usecols=[
                    'Nombre', 'teltelefono', 'emlMail', 'Carrera Interes', 
                    'Resolución', 'Fecha Insert Lead', 'TelWhatsapp'
                ])
                dfs.append(df)
            os.unlink(tmp.name)
        except Exception as e:
            st.warning(f"⚠️ No se pudo procesar {uploaded_file.name}: {str(e)}")
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

# ====================
# INTERFAZ DE CONFIGURACIÓN (Mejorada)
# ====================
with st.sidebar:
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
            value=True,
            help="Elimina registros con el mismo número telefónico"
        )
        
        mostrar_vista_previa = st.checkbox(
            "Mostrar vista previa",
            value=True,
            help="Muestra las primeras filas de cada grupo"
        )
    
    # 3. Editor completo de grupos
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
                'filtro_fecha': False,  # Filtro desactivado por defecto para este grupo
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
    for i, grupo in enumerate(st.session_state.grupos[:]):  # Usamos copia para evitar modificación durante iteración
        with st.expander(f"**{grupo['nombre']}** {'✅' if grupo['activo'] else '❌'}", expanded=True):
            cols = st.columns([4, 1])
            grupo['nombre'] = cols[0].text_input(
                "Nombre del grupo",
                value=grupo['nombre'],
                key=f"nombre_{i}"
            )
            grupo['activo'] = cols[1].checkbox(
                "Activo",
                value=grupo['activo'],
                key=f"activo_{i}"
            )
            
            # Nuevo: Checkbox para activar/desactivar filtro por fecha
            grupo['filtro_fecha'] = st.checkbox(
                "Filtrar por fecha",
                value=grupo.get('filtro_fecha', True),
                key=f"filtro_fecha_{i}",
                help="Desactivar para incluir todos los registros sin filtrar por fecha"
            )
            
            if grupo['filtro_fecha']:
                if st.checkbox("Usar múltiples días", value=isinstance(grupo['dias_antes'], list), key=f"multidias_{i}"):
                    grupo['dias_antes'] = st.multiselect(
                        "Días a incluir",
                        options=list(range(8)),  # 0 a 7 días
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
            
            # Editor de resoluciones mejorado
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
            
            # Etapa 2: Limpieza de datos
            status_text.info("🧹 Limpiando datos...")
            df_unificado['Nombre'] = df_unificado['Nombre'].apply(limpiar_nombre)
            df_unificado['teltelefono'] = df_unificado['teltelefono'].apply(limpiar_telefono)
            df_unificado['TelWhatsapp'] = df_unificado['TelWhatsapp'].apply(limpiar_telefono)
            
            # Etapa 3: Procesamiento de fechas
            df_unificado['Fecha_Lead'] = pd.to_datetime(
                df_unificado['Fecha Insert Lead'], 
                format='%d-%m-%Y %H:%M:%S',
                errors='coerce'
            ).dt.date
            
            # Filtrar inválidos
            n_invalidos = df_unificado['Fecha_Lead'].isna().sum()
            if n_invalidos > 0:
                st.warning(f"⚠️ Se omitieron {n_invalidos} registros con fechas inválidas")
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
                if grupo['filtro_fecha'] and grupo['dias_antes'] is not None:
                    if isinstance(grupo['dias_antes'], list):
                        fechas = [fecha_referencia - timedelta(days=d) for d in grupo['dias_antes']]
                        df_filtrado = df_filtrado[df_filtrado['Fecha_Lead'].isin(fechas)]
                    else:
                        fecha_objetivo = fecha_referencia - timedelta(days=grupo['dias_antes'])
                        df_filtrado = df_filtrado[df_filtrado['Fecha_Lead'] == fecha_objetivo]
                
                if not df_filtrado.empty:
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
    2. **Sube tus archivos Excel** (.xls o .xlsx)
    3. **Ejecuta la segmentación**
    4. **Descarga los reportes** individuales

    ### ⚙️ **Funcionalidades clave**
    - **Filtro de fecha flexible**: Activa/desactiva por grupo
    - **Múltiples días**: Selecciona varios días de diferencia
    - **Eliminar duplicados**: Por número telefónico
    - **Vista previa**: Antes de descargar

    ### 💡 **Consejos**
    - Para grupos como "No contesta", desactiva el filtro por fecha
    - Usa "Eliminar duplicados" para datos más limpios
    """)

# Créditos
st.caption("""
    *Sistema de segmentación automatizada | v2.1 | {date}*
""".format(date=datetime.now().strftime("%d/%m/%Y")))