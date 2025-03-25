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
    page_title="🚀 Segmentación Avanzada de Leads",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal con estilo mejorado
st.title("📊 **Segmentación de Leads**")
st.markdown("""
    *Personaliza los grupos y criterios de segmentación antes de procesar.*  
    **👈 Configura todo en la barra lateral ↓**
""")

# ====================
# FUNCIONES PRINCIPALES (Mejoradas)
# ====================
def limpiar_nombre(nombre: str) -> str:
    """Limpia y formatea el nombre (primera palabra, formato título)."""
    return str(nombre).split()[0].lower().capitalize() if pd.notna(nombre) else ''

def limpiar_telefono(numero: str) -> str:
    """Elimina caracteres no numéricos de teléfonos (incluye manejo de NaN)."""
    return ''.join(filter(str.isdigit, str(numero))) if pd.notna(numero) else ''

def cargar_archivos(uploaded_files: List) -> Optional[pd.DataFrame]:
    """Carga y concatena archivos Excel con manejo robusto de formatos."""
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
            os.unlink(tmp_path)
        except Exception as e:
            st.warning(f"⚠️ No se pudo procesar {uploaded_file.name}: {str(e)}")
            continue
    
    return pd.concat(dfs, ignore_index=True) if dfs else None

# ====================
# INTERFAZ DE CONFIGURACIÓN (Mejorada)
# ====================
with st.sidebar:
    st.header("⚙️ **Configuración Avanzada**")
    
    # 1. Selector de fecha de referencia
    fecha_referencia = st.date_input(
        "📅 Fecha base para segmentación",
        datetime.now(),
        help="Los leads se compararán con esta fecha según los días configurados en cada grupo."
    )
    
    # 2. Configuración global
    with st.expander("🔧 **Opciones Generales**", expanded=True):
        eliminar_duplicados = st.checkbox(
            "Eliminar duplicados (por teléfono)",
            value=False,
            help="Si está activado, elimina registros con el mismo número telefónico."
        )
        
        mostrar_vista_previa = st.checkbox(
            "Mostrar vista previa de datos",
            value=True,
            help="Muestra un preview de 3 registros antes de descargar."
        )
    
    # 3. Editor completo de grupos
    st.header("✏️ Editor de Grupos")
    
    # Botón para añadir nuevo grupo
    if st.button("➕ Añadir Grupo", use_container_width=True):
        if 'grupos' not in st.session_state:
            st.session_state.grupos = []
        st.session_state.grupos.append({
            'nombre': f"Nuevo Grupo {len(st.session_state.grupos) + 1}",
            'resoluciones': ["Ejemplo Resolución 1", "Ejemplo Resolución 2"],
            'dias_antes': 1,
            'activo': True
        })
    
    # Editor dinámico de grupos
    if 'grupos' not in st.session_state:
        st.session_state.grupos = [
            {
                'nombre': "Se brinda información",
                'resoluciones': ["Se brinda información", "Se brinda información Whatsapp", "Volver a llamar"],
                'dias_antes': 1,
                'activo': True
            },
            {
                'nombre': "No contesta",
                'resoluciones': ["No contesta", "NotProcessed"],
                'dias_antes': None,
                'activo': True
            }
        ]
    
    for i, grupo in enumerate(st.session_state.grupos):
        with st.expander(f"Grupo {i+1}: {grupo['nombre']}", expanded=True):
            cols = st.columns([0.7, 0.3])
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
            
            # Selector de días (flexible para números o listas)
            if st.checkbox("Usar múltiples días", value=isinstance(grupo['dias_antes'], list), key=f"multidias_{i}"):
                grupo['dias_antes'] = st.multiselect(
                    "Días a incluir (relativos a la fecha base)",
                    options=[0, 1, 2, 3, 4, 5, 6, 7],
                    default=grupo['dias_antes'] if isinstance(grupo['dias_antes'], list) else [1],
                    key=f"dias_ms_{i}"
                )
            else:
                grupo['dias_antes'] = st.number_input(
                    "Días antes de la fecha base",
                    min_value=0,
                    value=grupo['dias_antes'] if isinstance(grupo['dias_antes'], int) else 1,
                    key=f"dias_num_{i}"
                )
            
            # Editor avanzado de resoluciones
            st.markdown("**Resoluciones a incluir:**")
            resoluciones_texto = "\n".join(grupo['resoluciones'])
            nuevas_resoluciones = st.text_area(
                "Una por línea",
                value=resoluciones_texto,
                key=f"res_{i}",
                height=100,
                help="Escribe cada resolución en una línea separada."
            )
            grupo['resoluciones'] = [r.strip() for r in nuevas_resoluciones.split('\n') if r.strip()]
            
            # Botón para eliminar grupo
            if st.button(f"❌ Eliminar este grupo", key=f"del_{i}"):
                st.session_state.grupos.pop(i)
                st.rerun()

# ====================
# PROCESAMIENTO PRINCIPAL (Optimizado)
# ====================
uploaded_files = st.file_uploader(
    "📤 **Sube tus archivos Excel** (.xls o .xlsx)",
    type=["xls", "xlsx"],
    accept_multiple_files=True,
    help="Puedes seleccionar múltiples archivos del mismo formato."
)

if uploaded_files and st.button("🚀 **Ejecutar Segmentación**", type="primary", use_container_width=True):
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Etapa 1: Carga y unificación
        status_text.info("📂 Cargando y unificando archivos...")
        df_unificado = cargar_archivos(uploaded_files)
        progress_bar.progress(15)
        
        if df_unificado is None or df_unificado.empty:
            st.error("❌ No se encontraron datos válidos en los archivos subidos.")
            st.stop()
        
        # Etapa 2: Limpieza de datos
        status_text.info("🧼 Limpiando y formateando datos...")
        df_unificado['Nombre'] = df_unificado['Nombre'].apply(limpiar_nombre)
        df_unificado['teltelefono'] = df_unificado['teltelefono'].apply(limpiar_telefono)
        df_unificado['TelWhatsapp'] = df_unificado['TelWhatsapp'].apply(limpiar_telefono)
        
        # Etapa 3: Procesamiento de fechas
        df_unificado['Fecha_Lead'] = pd.to_datetime(
            df_unificado['Fecha Insert Lead'], 
            format='%d-%m-%Y %H:%M:%S',
            errors='coerce'
        ).dt.date
        
        # Filtrar inválidos y mostrar advertencia
        registros_invalidos = df_unificado['Fecha_Lead'].isna().sum()
        if registros_invalidos > 0:
            st.warning(f"⚠️ Se omitieron {registros_invalidos} registros con fechas no reconocidas")
            df_unificado = df_unificado.dropna(subset=['Fecha_Lead'])
        
        progress_bar.progress(40)
        
        # Etapa 4: Procesamiento por grupos
        resultados = []
        grupos_activos = [g for g in st.session_state.grupos if g['activo']]
        
        for i, grupo in enumerate(grupos_activos):
            status_text.info(f"🔍 Procesando grupo: {grupo['nombre']} ({i+1}/{len(grupos_activos)})")
            
            # Filtrar por resoluciones
            df_filtrado = df_unificado[df_unificado['Resolución'].isin(grupo['resoluciones'])]
            
            # Filtrar por fecha si aplica
            if grupo['dias_antes'] is not None:
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
            
            progress_bar.progress(40 + int((i+1) * 50/len(grupos_activos)))
        
        # Resultados finales
        progress_bar.progress(100)
        time.sleep(0.5)
        progress_bar.empty()
        status_text.empty()
        
        if resultados:
            st.balloons()
            st.success(f"✅ ¡Procesamiento completado con éxito! ({len(resultados)} grupos generados)")
            
            # Métricas resumidas
            cols = st.columns(3)
            cols[0].metric("📂 Archivos cargados", len(uploaded_files))
            cols[1].metric("🧑‍💻 Leads procesados", len(df_unificado))
            cols[2].metric("📊 Grupos válidos", len(resultados))
            
            # Descargas individuales con vista previa
            st.subheader("📥 Descargar Reportes", divider="rainbow")
            for resultado in resultados:
                with st.expander(
                    f"**{resultado['nombre']}** ({resultado['registros']} registros)", 
                    expanded=True
                ):
                    if mostrar_vista_previa:
                        st.dataframe(
                            resultado['data'].head(3),
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "Telefono": st.column_config.NumberColumn(format="%d")
                            }
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
            st.info("📭 No se generaron archivos. Revisa la configuración de grupos.")
    
    except Exception as e:
        progress_bar.empty()
        status_text.error(f"❌ Error crítico: {str(e)}")
        st.exception(e)

# ====================
# SECCIÓN DE AYUDA MEJORADA
# ====================
with st.expander("📚 **Guía Completa de Uso**", expanded=False):
    st.markdown("""
    ### 🎯 **Cómo usar la herramienta**
    1. **Configura los grupos** en la barra lateral:
       - ✏️ Edita nombres, resoluciones y días
       - ➕/❌ Añade o elimina grupos
    2. **Sube tus archivos Excel** (.xls o .xlsx)
    3. **Ejecuta la segmentación**
    4. **Descarga los reportes** individualmente

    ### ⚡ **Consejos avanzados**
    - Para **múltiples fechas**: Activa "Usar múltiples días" en un grupo
    - **Resoluciones**: Escribe exactamente como aparece en el Excel
    - **Eliminar duplicados**: Recomendado para evitar registros repetidos
    """)

# Créditos
st.caption("""
    *Sistema de segmentación automatizada | Actualizado: {date}*  
    *Los datos no se almacenan después de cerrar la sesión.*
""".format(date=datetime.now().strftime("%d/%m/%Y")))