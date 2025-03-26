import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
import tempfile
import os

# Configuración inicial
st.set_page_config(
    page_title="Segmentación de Leads",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
    <style>
        section[data-testid="stSidebar"] {
            width: 40% !important;
        }
        .primary-button {
            background-color: #4CAF50 !important;
            color: white !important;
            border: none !important;
        }
        .secondary-button {
            background-color: #f0f2f6 !important;
            color: #333 !important;
            border: 1px solid #ccc !important;
        }
        .danger-button {
            background-color: #ff4444 !important;
            color: white !important;
            border: none !important;
        }
        .group-card {
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 12px;
            background-color: #f9f9f9;
        }
        .client-card {
            border: 1px solid #4CAF50;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 12px;
            background-color: #f0faf0;
        }
    </style>
""", unsafe_allow_html=True)

# Título principal
st.title("📊 Segmentación de Leads")

# Funciones principales
def limpiar_nombre(nombre):
    if pd.isna(nombre):
        return ''
    nombre_str = str(nombre).strip()
    return nombre_str.split()[0].lower().capitalize() if nombre_str else ''

def limpiar_telefono(numero):
    return ''.join(filter(str.isdigit, str(numero))) if pd.notna(numero) else ''

def validar_email(email):
    if pd.isna(email):
        return False
    email_str = str(email).strip()
    return '@' in email_str and '.' in email_str.split('@')[-1]

def obtener_nombre(df):
    # Busca columnas de nombre en diferentes formatos
    for col in ['Nombre y Apellido', 'Nombre', 'nombre', 'NOMBRE']:
        if col in df.columns:
            return df[col].apply(limpiar_nombre)
    return pd.Series([''] * len(df))

def cargar_archivos(uploaded_files):
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
            st.warning(f"No se pudo procesar {uploaded_file.name}: {str(e)}")
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

def generar_archivo_descarga(df):
    columnas_base = ['Nombre', 'Telefono', 'Email', 'Programa', 'Whatsapp']
    df_descarga = pd.DataFrame(columns=columnas_base)
    
    mapeo_columnas = {
        'teltelefono': 'Telefono',
        'emlMail': 'Email',
        'Carrera Interes': 'Programa',
        'TelWhatsapp': 'Whatsapp'
    }
    
    # Manejo especial para el nombre
    df_descarga['Nombre'] = obtener_nombre(df)
    
    for col_origen, col_destino in mapeo_columnas.items():
        if col_origen in df.columns:
            df_descarga[col_destino] = df[col_origen]
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_descarga.to_excel(writer, index=False)
    return output.getvalue()

def guardar_configuracion():
    st.session_state.configuracion = {
        'clientes': st.session_state.clientes,
        'grupos_por_cliente': st.session_state.grupos_por_cliente
    }

def cargar_configuracion():
    if 'clientes' not in st.session_state:
        st.session_state.clientes = ["Cliente 1"]
        
    if 'grupos_por_cliente' not in st.session_state:
        st.session_state.grupos_por_cliente = {
            "Cliente 1": [{
                'nombre': "Grupo 1",
                'resoluciones': ["Resolución 1"],
                'dias_antes': 1,
                'filtro_fecha': True
            }]
        }
    
    if 'cliente_actual' not in st.session_state:
        st.session_state.cliente_actual = st.session_state.clientes[0]

# Inicialización
cargar_configuracion()

# Sidebar - Gestión de clientes
with st.sidebar:
    st.header("👥 Gestión de Clientes")
    
    # Tarjeta de cliente actual
    with st.container():
        st.markdown(f"<div class='client-card'><b>Cliente actual:</b><br>{st.session_state.cliente_actual}</div>", 
                   unsafe_allow_html=True)
    
    # Selector de cliente
    nuevo_cliente = st.text_input("Nombre del nuevo cliente", key="nuevo_cliente")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Agregar", key="add_client", 
                   help="Agregar un nuevo cliente",
                   type="primary"):
            if nuevo_cliente and nuevo_cliente not in st.session_state.clientes:
                st.session_state.clientes.append(nuevo_cliente)
                st.session_state.grupos_por_cliente[nuevo_cliente] = []
                st.session_state.cliente_actual = nuevo_cliente
                guardar_configuracion()
                st.rerun()
    
    with col2:
        if len(st.session_state.clientes) > 1:
            if st.button("🗑️ Eliminar actual", 
                        key="del_client",
                        help="Eliminar el cliente actual",
                        type="secondary"):
                st.session_state.clientes.remove(st.session_state.cliente_actual)
                del st.session_state.grupos_por_cliente[st.session_state.cliente_actual]
                st.session_state.cliente_actual = st.session_state.clientes[0]
                guardar_configuracion()
                st.rerun()
    
    # Lista de clientes
    st.markdown("**Cambiar cliente:**")
    for cliente in st.session_state.clientes:
        if cliente != st.session_state.cliente_actual:
            if st.button(cliente, key=f"sel_{cliente}", 
                        help=f"Seleccionar {cliente}",
                        type="secondary"):
                st.session_state.cliente_actual = cliente
                st.rerun()
    
    st.divider()
    
    # Configuración general
    st.header("⚙️ Configuración")
    fecha_referencia = st.date_input("Fecha base", datetime.now(), key="fecha_ref")
    
    with st.expander("Opciones avanzadas"):
        eliminar_duplicados = st.checkbox("Eliminar duplicados", True, 
                                         help="Eliminar leads con teléfono/email repetidos")
        validar_emails = st.checkbox("Validar emails", True, 
                                    help="Excluir emails con formato inválido")
        mostrar_vista_previa = st.checkbox("Mostrar vista previa", True)
    
    st.divider()
    
    # Gestión de grupos
    st.header("✏️ Grupos")
    
    if st.button("➕ Nuevo grupo", 
                key="add_group",
                help="Agregar un nuevo grupo de segmentación",
                type="primary"):
        nuevo_grupo = {
            'nombre': f"Grupo {len(st.session_state.grupos_por_cliente[st.session_state.cliente_actual]) + 1}",
            'resoluciones': ["Resolución 1"],
            'dias_antes': 1,
            'filtro_fecha': True
        }
        st.session_state.grupos_por_cliente[st.session_state.cliente_actual].append(nuevo_grupo)
        guardar_configuracion()
        st.rerun()
    
    # Lista de grupos
    grupos = st.session_state.grupos_por_cliente.get(st.session_state.cliente_actual, [])
    for i, grupo in enumerate(grupos[:]):
        with st.container():
            st.markdown(f"<div class='group-card'>", unsafe_allow_html=True)
            
            cols = st.columns([4, 1])
            with cols[0]:
                grupo['nombre'] = st.text_input("Nombre del grupo", grupo['nombre'], 
                                              key=f"nombre_{i}",
                                              label_visibility="collapsed")
            with cols[1]:
                if st.button("🗑️", 
                           key=f"del_{i}",
                           help="Eliminar este grupo",
                           type="secondary"):
                    grupos.pop(i)
                    guardar_configuracion()
                    st.rerun()
            
            grupo['resoluciones'] = st.text_area(
                "Resoluciones (una por línea)",
                "\n".join(grupo['resoluciones']),
                key=f"res_{i}",
                height=100
            ).split('\n')
            
            grupo['filtro_fecha'] = st.checkbox(
                "Filtrar por fecha", 
                grupo['filtro_fecha'],
                key=f"filtro_{i}"
            )
            
            if grupo['filtro_fecha']:
                cols = st.columns(2)
                with cols[0]:
                    tipo_filtro = st.radio(
                        "Tipo de filtro",
                        ["Días antes", "Rango de fechas"],
                        key=f"tipo_filtro_{i}",
                        index=0 if isinstance(grupo['dias_antes'], (int, list)) else 1
                    )
                
                with cols[1]:
                    if tipo_filtro == "Días antes":
                        grupo['dias_antes'] = st.multiselect(
                            "Días a incluir",
                            options=list(range(8)),
                            default=grupo['dias_antes'] if isinstance(grupo['dias_antes'], list) else [grupo['dias_antes']] if isinstance(grupo['dias_antes'], int) else [1],
                            key=f"dias_{i}"
                        )
                    else:
                        # Implementar rango de fechas si es necesario
                        pass
            
            st.markdown("</div>", unsafe_allow_html=True)

# Área principal
uploaded_files = st.file_uploader(
    "Subir archivos Excel (.xls, .xlsx)", 
    type=["xls", "xlsx"], 
    accept_multiple_files=True,
    help="Puedes subir uno o varios archivos a la vez"
)

if uploaded_files:
    if st.button("🚀 Procesar archivos", 
                type="primary",
                help="Iniciar el procesamiento de los archivos subidos",
                use_container_width=True):
        with st.spinner("Procesando datos..."):
            try:
                df = cargar_archivos(uploaded_files)
                
                # Limpieza de datos
                df['Nombre'] = obtener_nombre(df)
                
                if 'teltelefono' in df.columns:
                    df['teltelefono'] = df['teltelefono'].apply(limpiar_telefono)
                if 'TelWhatsapp' in df.columns:
                    df['TelWhatsapp'] = df['TelWhatsapp'].apply(limpiar_telefono)
                if validar_emails and 'emlMail' in df.columns:
                    df['email_valido'] = df['emlMail'].apply(validar_email)
                
                # Procesamiento de fechas
                if 'Fecha Insert Lead' in df.columns:
                    df['Fecha_Lead'] = pd.to_datetime(
                        df['Fecha Insert Lead'], 
                        format='%d-%m-%Y %H:%M:%S', 
                        errors='coerce'
                    ).dt.date
                    df = df.dropna(subset=['Fecha_Lead'])
                
                # Eliminar duplicados
                if eliminar_duplicados:
                    subset = ['teltelefono']
                    if validar_emails and 'emlMail' in df.columns:
                        subset.append('emlMail')
                    df = df.drop_duplicates(subset=subset)
                
                # Procesar grupos
                resultados = []
                grupos_activos = st.session_state.grupos_por_cliente[st.session_state.cliente_actual]
                
                for grupo in grupos_activos:
                    df_filtrado = df[df['Resolución'].isin(grupo['resoluciones'])]
                    
                    if grupo['filtro_fecha'] and grupo.get('dias_antes') and 'Fecha_Lead' in df.columns:
                        if isinstance(grupo['dias_antes'], list):
                            fechas = [fecha_referencia - timedelta(days=d) for d in grupo['dias_antes']]
                            df_filtrado = df_filtrado[df_filtrado['Fecha_Lead'].isin(fechas)]
                    
                    if not df_filtrado.empty:
                        archivo = generar_archivo_descarga(df_filtrado)
                        resultados.append({
                            'nombre': grupo['nombre'],
                            'data': df_filtrado,
                            'archivo': archivo,
                            'registros': len(df_filtrado),
                            'filename': f"{grupo['nombre']}_{fecha_referencia.strftime('%Y%m%d')}.xlsx"
                        })
                
                st.session_state.resultados = resultados
                st.success(f"Procesamiento completado: {len(resultados)} grupos creados")
                
            except Exception as e:
                st.error(f"Error durante el procesamiento: {str(e)}")

# Mostrar resultados
if 'resultados' in st.session_state and st.session_state.resultados:
    st.header("📂 Resultados")
    
    cols = st.columns(3)
    cols[0].metric("Archivos procesados", len(uploaded_files))
    cols[1].metric("Total de leads", len(df) if 'df' in locals() else 0)
    cols[2].metric("Grupos generados", len(st.session_state.resultados))
    
    for resultado in st.session_state.resultados:
        with st.expander(f"{resultado['nombre']} ({resultado['registros']} registros)"):
            if mostrar_vista_previa:
                st.dataframe(
                    resultado['data'][['Nombre', 'teltelefono', 'emlMail', 'Resolución', 'Fecha_Lead']].head(5),
                    use_container_width=True,
                    hide_index=True
                )
            
            st.download_button(
                f"⬇️ Descargar {resultado['nombre']}",
                data=resultado['archivo'],
                file_name=resultado['filename'],
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True
            )
    
    if st.button("🔄 Nuevo procesamiento", 
                type="secondary",
                use_container_width=True):
        del st.session_state.resultados
        st.rerun()

# Sección de ayuda
with st.expander("❓ Ayuda"):
    st.markdown("""
    ### Cómo usar esta herramienta
    1. **Configura los grupos** en la barra lateral
    2. **Sube tus archivos Excel** (.xls o .xlsx)
    3. **Haz clic en Procesar**
    4. **Descarga los resultados** que necesites
    
    ### Columnas requeridas
    - Nombre (o 'Nombre y Apellido')
    - teltelefono
    - Resolución
    - Fecha Insert Lead
    - emlMail (opcional para validación)
    
    ### Tips
    - Puedes crear múltiples clientes con configuraciones diferentes
    - Cada cliente puede tener sus propios grupos de segmentación
    - Los resultados permanecen disponibles hasta que cierres la página
    """)

st.caption(f"Versión {datetime.now().strftime('%d/%m/%Y')}")