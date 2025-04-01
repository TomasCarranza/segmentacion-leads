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
            if isinstance(grupo['resoluciones'], dict):
                # Para UNAB Nurturing
                st.info("Este grupo usa resoluciones por día de la semana")
                for dia, resoluciones in grupo['resoluciones'].items():
                    grupo['resoluciones'][dia] = st.text_area(
                        f"Resoluciones para {dia}",
                        value="\n".join(resoluciones),
                        key=f"res_{i}_{dia}",
                        height=100
                    ).split('\n')
            else:
                # Para otros grupos
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
            grupos_activos = st.session_state.grupos  # Ya no filtramos por activo
            
            for i, grupo in enumerate(grupos_activos):
                status_text.info(f"🔍 Procesando grupo: {grupo['nombre']} ({i+1}/{len(grupos_activos)})")
                
                # Manejar resoluciones por día de la semana (UNAB Nurturing)
                if isinstance(grupo['resoluciones'], dict):
                    dia_actual = fecha_referencia.strftime('%A')  # Obtener día de la semana
                    resoluciones_dia = grupo['resoluciones'].get(dia_actual, [])
                    df_filtrado = df_unificado[df_unificado['Resolución'].isin(resoluciones_dia)]
                    
                    # Formato especial para UNAB Nurturing
                    nombre_archivo = f"UNAB Nurturing - {dia_actual} - {fecha_referencia.strftime('%d-%m-%Y')}.xlsx"
                else:
                    if grupo['filtro_resolucion']:
                        df_filtrado = df_unificado[df_unificado['Resolución'].isin(grupo['resoluciones'])]
                    else:
                        df_filtrado = df_unificado.copy()  # No filtrar por resolución
                    
                    # Formato estándar para otros clientes
                    nombre_archivo = f"{cliente_seleccionado}_{grupo['nombre']}_{fecha_referencia.strftime('%d-%m-%Y')}.xlsx"
                
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
                    archivo_descarga = generar_archivo_descarga(
                        df_filtrado,
                        config_cliente['columnas_salida'],
                        cliente_seleccionado
                    )
                    
                    resultados.append({
                        'nombre': grupo['nombre'],
                        'data': df_filtrado,
                        'archivo': archivo_descarga,
                        'registros': len(df_filtrado),
                        'filename': nombre_archivo
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
                    file_name=f"{cliente_seleccionado}_Registros_omitidos_{fecha_referencia.strftime('%d-%m-%Y')}.xlsx",
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
    st.markdown(f"""
    ### 🎯 **Cómo usar esta herramienta**
    1. **Selecciona el cliente** en la barra lateral
    2. **Configura los grupos** según la configuración predeterminada
    3. **Sube tus archivos** ({', '.join(['.xls', '.xlsx', '.csv'] if cliente_seleccionado == 'PK_CBA' else ['.xls', '.xlsx'])})
    4. **Ejecuta la segmentación**
    5. **Descarga los reportes** individuales

    ### 📂 **Formato de salida**
    Los archivos descargados contendrán las columnas específicas para {config_cliente['nombre']}:
    {', '.join(config_cliente['columnas_salida'].values())}

    ### ⚠️ **Registros omitidos**
    - Si hay registros con fechas inválidas, podrás descargarlos
    - Revisa el formato de fecha en tus archivos (debe ser DD-MM-AAAA HH:MM:SS)
    """)
