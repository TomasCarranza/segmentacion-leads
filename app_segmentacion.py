import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
import tempfile
import os
import time
from config_clientes import obtener_configuracion_cliente, obtener_lista_clientes
from procesamiento import (
    limpiar_nombre, limpiar_telefono, procesar_cliente_especifico,
    cargar_archivo, generar_archivo_descarga
)

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
# INTERFAZ DE USUARIO
# ====================
with st.sidebar:
    st.header("⚙️ **Configuración**")
    
    # 1. Selección de cliente
    cliente_seleccionado = st.selectbox(
        "🏢 **Seleccionar Cliente**",
        options=obtener_lista_clientes(),
        index=0
    )
    
    # Obtener configuración del cliente
    config_cliente = obtener_configuracion_cliente(cliente_seleccionado)
    
    # 2. Fecha de referencia
    fecha_referencia = st.date_input(
        "📅 Fecha base para segmentación",
        datetime.now()
    )
    
    # 3. Opciones generales
    with st.expander("🔧 **Opciones Generales**", expanded=True):
        eliminar_duplicados = st.checkbox(
            "Eliminar duplicados (por teléfono)",
            value=False
        )
        
        mostrar_vista_previa = st.checkbox(
            "Mostrar vista previa",
            value=True
        )
    
    # 4. Editor de grupos
    st.header("✏️ **Editor de Grupos**")
    
    # Inicializar grupos con la configuración del cliente
    if 'grupos' not in st.session_state or st.session_state.cliente_actual != cliente_seleccionado:
        st.session_state.grupos = config_cliente['grupos']
        st.session_state.cliente_actual = cliente_seleccionado
    
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
            
            grupo['filtro_fecha'] = st.checkbox(
                "Filtrar por fecha",
                value=grupo.get('filtro_fecha', True),
                key=f"filtro_fecha_{i}"
            )
            
            # Agregar opción para filtrar por resolución
            grupo['filtro_resolucion'] = st.checkbox(
                "Filtrar por resolución",
                value=grupo.get('filtro_resolucion', True),
                key=f"filtro_resolucion_{i}"
            )
            
            if grupo['filtro_fecha']:
                # Inicializar dias_antes si no existe
                if 'dias_antes' not in grupo:
                    grupo['dias_antes'] = 1
                
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
            st.subheader("Resoluciones")
            if grupo['resoluciones'] is not None:  # Solo mostrar editor si hay resoluciones
                if isinstance(grupo['resoluciones'], dict):
                    # Para UNAB Nurturing
                    dia_actual = fecha_referencia.strftime('%A')
                    resoluciones_dia = grupo['resoluciones'].get(dia_actual, [])
                    grupo['resoluciones'] = resoluciones_dia
                else:
                    # Para otros grupos
                    resoluciones_texto = st.text_area(
                        "Resoluciones",
                        value="\n".join(grupo['resoluciones']),
                        key=f"resoluciones_{i}"
                    )
                    grupo['resoluciones'] = [r.strip() for r in resoluciones_texto.split('\n') if r.strip()]
            
            if st.button(f"❌ Eliminar grupo", key=f"del_{i}"):
                st.session_state.grupos.pop(i)
                st.rerun()

# ====================
# PROCESAMIENTO PRINCIPAL
# ====================
uploaded_files = st.file_uploader(
    "📤 **Sube tus archivos**",
    type=["xls", "xlsx", "csv"] if cliente_seleccionado == 'PK_CBA' else ["xls", "xlsx"],
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
            dfs = []
            for uploaded_file in uploaded_files:
                df = cargar_archivo(uploaded_file, cliente_seleccionado)
                dfs.append(df)
            df_unificado = pd.concat(dfs, ignore_index=True)
            progress_bar.progress(20)
            
            if df_unificado.empty:
                st.error("❌ No se encontraron datos válidos")
                st.stop()
            
            # 2. Procesamiento específico del cliente
            status_text.info("🔄 Procesando datos específicos del cliente...")
            df_unificado = procesar_cliente_especifico(df_unificado, cliente_seleccionado)
            progress_bar.progress(30)
            
            # 3. Procesamiento de fechas
            if 'Fecha Insert Lead' in df_unificado.columns:
                # Intentar diferentes formatos de fecha
                try:
                    df_unificado['Fecha_Lead'] = pd.to_datetime(
                        df_unificado['Fecha Insert Lead'], 
                        format='%d-%m-%Y %H:%M:%S',
                        errors='coerce'
                    )
                except:
                    try:
                        df_unificado['Fecha_Lead'] = pd.to_datetime(
                            df_unificado['Fecha Insert Lead'], 
                            format='%Y-%m-%d %H:%M:%S',
                            errors='coerce'
                        )
                    except:
                        df_unificado['Fecha_Lead'] = pd.to_datetime(
                            df_unificado['Fecha Insert Lead'], 
                            errors='coerce'
                        )
                
                # Identificar registros con fechas inválidas
                registros_invalidos = df_unificado[df_unificado['Fecha_Lead'].isna()].copy()
                n_invalidos = len(registros_invalidos)
                
                if n_invalidos > 0:
                    st.warning(f"⚠️ Se omitieron {n_invalidos} registros con fechas no reconocidas")
                    df_unificado = df_unificado.dropna(subset=['Fecha_Lead'])
            
            progress_bar.progress(40)
            
            # 4. Procesamiento por grupos
            resultados = []
            grupos_activos = st.session_state.grupos  # Ya no filtramos por activo
            
            for i, grupo in enumerate(grupos_activos):
                status_text.info(f"🔍 Procesando grupo: {grupo['nombre']} ({i+1}/{len(grupos_activos)})")
                
                # Aplicar filtros según configuración
                df_filtrado = df_unificado.copy()
                
                if grupo['filtro_fecha']:
                    if isinstance(grupo['dias_antes'], list):
                        # Para múltiples días
                        fechas_validas = []
                        for dias in grupo['dias_antes']:
                            fecha_limite = fecha_referencia - pd.Timedelta(days=dias)
                            fechas_validas.append(fecha_limite)
                        df_filtrado = df_filtrado[df_filtrado['Fecha_Lead'].dt.date.isin(fechas_validas)]
                    else:
                        # Para un solo día
                        fecha_limite = fecha_referencia - pd.Timedelta(days=grupo['dias_antes'])
                        df_filtrado = df_filtrado[df_filtrado['Fecha_Lead'].dt.date == fecha_limite]
                
                # Filtrar por resolución si está activo
                if grupo['filtro_resolucion'] and grupo['resoluciones'] is not None:
                    col_resolucion = 'Ultima Resolución' if cliente_seleccionado in ['ULINEA', 'ANAHUAC'] else 'Resolución'
                    if col_resolucion in df_filtrado.columns:
                        if isinstance(grupo['resoluciones'], dict):
                            # Para UNAB Nurturing
                            dia_actual = fecha_referencia.strftime('%A')
                            resoluciones_dia = grupo['resoluciones'].get(dia_actual, [])
                            df_filtrado = df_filtrado[df_filtrado[col_resolucion].isin(resoluciones_dia)]
                        else:
                            # Para otros grupos
                            df_filtrado = df_filtrado[df_filtrado[col_resolucion].isin(grupo['resoluciones'])]
                
                # Si no hay registros después del filtrado, mostrar mensaje
                if len(df_filtrado) == 0:
                    st.warning(f"📭 No se generaron resultados para {grupo['nombre']}. Ajusta tus criterios de filtrado.")
                    continue
                
                # Generar archivo de descarga
                archivo_bytes = generar_archivo_descarga(
                    df_filtrado,
                    grupo['columnas_salida'],
                    cliente_seleccionado
                )
                
                # Botón de descarga
                st.download_button(
                    label=f"📥 Descargar {grupo['nombre']}",
                    data=archivo_bytes,
                    file_name=f"{cliente_seleccionado}_{grupo['nombre']}_{fecha_referencia.strftime('%d-%m-%Y')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"download_{i}"
                )
                
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
                    file_name=f"{cliente_seleccionado}_Registros_omitidos_{fecha_referencia.strftime('%d-%m-%Y')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            if resultados:
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
                        
                        # Usar st.download_button con on_click para evitar recarga
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
    st.markdown(f"""
    ### 🎯 **Cómo usar esta herramienta**
    1. **Selecciona el cliente** en la barra lateral
    2. **Configura los grupos** según la configuración predeterminada
    3. **Sube tus archivos** ({', '.join(['.xls', '.xlsx', '.csv'] if cliente_seleccionado == 'PK_CBA' else ['.xls', '.xlsx'])})
    4. **Ejecuta la segmentación**
    5. **Descarga los reportes** individuales

    ### ⚠️ **Registros omitidos**
    - Si hay registros con fechas inválidas, podrás descargarlos
    - Revisa el formato de fecha en tus archivos (debe ser DD-MM-AAAA HH:MM:SS)
    """)
