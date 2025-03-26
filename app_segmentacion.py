import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
import tempfile
import os
import time

# Configuración inicial
st.set_page_config(
    page_title="Segmentación de Leads",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos
st.markdown("""
    <style>
        section[data-testid="stSidebar"] {
            width: 40% !important;
        }
        .stButton>button, .stDownloadButton>button {
            width: 100%;
        }
    </style>
""", unsafe_allow_html=True)

# Título
st.title("📊 Segmentación de Leads")

# Funciones principales
def limpiar_nombre(nombre):
    return str(nombre).split()[0].lower().capitalize() if pd.notna(nombre) else ''

def limpiar_telefono(numero):
    return ''.join(filter(str.isdigit, str(numero))) if pd.notna(numero) else ''

def validar_email(email):
    return '@' in str(email) and '.' in str(email).split('@')[-1] if pd.notna(email) else False

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
        'Nombre y Apellido': 'Nombre',
        'teltelefono': 'Telefono',
        'emlMail': 'Email',
        'Carrera Interes': 'Programa',
        'TelWhatsapp': 'Whatsapp'
    }
    
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
                'resoluciones': ["Resolución 1", "Resolución 2"],
                'dias_antes': 1,
                'filtro_fecha': True,
                'activo': True
            }]
        }
    
    if 'cliente_actual' not in st.session_state:
        st.session_state.cliente_actual = st.session_state.clientes[0]

# Interfaz
cargar_configuracion()

with st.sidebar:
    st.header("Clientes")
    
    # Selector de cliente
    cliente_actual = st.selectbox(
        "Seleccionar cliente",
        st.session_state.clientes,
        index=st.session_state.clientes.index(st.session_state.cliente_actual)
    )
    
    if cliente_actual != st.session_state.cliente_actual:
        st.session_state.cliente_actual = cliente_actual
        st.rerun()
    
    # Gestión de clientes
    with st.expander("Administrar clientes"):
        nuevo_cliente = st.text_input("Nuevo cliente")
        if st.button("Agregar") and nuevo_cliente:
            if nuevo_cliente not in st.session_state.clientes:
                st.session_state.clientes.append(nuevo_cliente)
                st.session_state.grupos_por_cliente[nuevo_cliente] = []
                st.session_state.cliente_actual = nuevo_cliente
                guardar_configuracion()
                st.rerun()
        
        if len(st.session_state.clientes) > 1 and st.button("Eliminar actual"):
            st.session_state.clientes.remove(st.session_state.cliente_actual)
            del st.session_state.grupos_por_cliente[st.session_state.cliente_actual]
            st.session_state.cliente_actual = st.session_state.clientes[0]
            guardar_configuracion()
            st.rerun()
    
    st.header("Configuración")
    fecha_referencia = st.date_input("Fecha base", datetime.now())
    
    with st.expander("Opciones"):
        eliminar_duplicados = st.checkbox("Eliminar duplicados", True)
        mostrar_vista_previa = st.checkbox("Mostrar vista previa", True)
        validar_emails = st.checkbox("Validar emails", True)
    
    st.header("Grupos")
    if st.button("➕ Nuevo grupo"):
        st.session_state.grupos_por_cliente[st.session_state.cliente_actual].append({
            'nombre': f"Grupo {len(st.session_state.grupos_por_cliente[st.session_state.cliente_actual]) + 1}",
            'resoluciones': ["Resolución 1"],
            'dias_antes': 1,
            'filtro_fecha': True,
            'activo': True
        })
        guardar_configuracion()
    
    grupos = st.session_state.grupos_por_cliente.get(st.session_state.cliente_actual, [])
    for i, grupo in enumerate(grupos[:]):
        with st.expander(grupo['nombre']):
            grupo['nombre'] = st.text_input("Nombre", grupo['nombre'], key=f"nombre_{i}")
            grupo['activo'] = st.checkbox("Activo", grupo['activo'], key=f"activo_{i}")
            grupo['filtro_fecha'] = st.checkbox("Filtrar por fecha", grupo.get('filtro_fecha', True), key=f"filtro_{i}")
            
            if grupo['filtro_fecha']:
                if st.checkbox("Múltiples días", isinstance(grupo['dias_antes'], list), key=f"multi_{i}"):
                    grupo['dias_antes'] = st.multiselect(
                        "Días",
                        list(range(8)),
                        grupo['dias_antes'] if isinstance(grupo['dias_antes'], list) else [1],
                        key=f"dias_{i}"
                    )
                else:
                    grupo['dias_antes'] = st.number_input(
                        "Días antes",
                        min_value=0,
                        value=grupo['dias_antes'] if isinstance(grupo['dias_antes'], int) else 1,
                        key=f"dias_num_{i}"
                    )
            
            grupo['resoluciones'] = st.text_area(
                "Resoluciones (una por línea)",
                "\n".join(grupo['resoluciones']),
                key=f"res_{i}"
            ).split('\n')
            
            if st.button("❌ Eliminar", key=f"del_{i}"):
                grupos.pop(i)
                guardar_configuracion()
                st.rerun()

# Procesamiento
uploaded_files = st.file_uploader("Subir archivos Excel", type=["xls", "xlsx"], accept_multiple_files=True)

if uploaded_files and st.button("Procesar", type="primary"):
    with st.spinner("Procesando..."):
        try:
            df = cargar_archivos(uploaded_files)
            
            # Limpieza
            if 'Nombre y Apellido' in df.columns:
                df['Nombre'] = df['Nombre y Apellido'].apply(limpiar_nombre)
            if 'teltelefono' in df.columns:
                df['teltelefono'] = df['teltelefono'].apply(limpiar_telefono)
            if 'TelWhatsapp' in df.columns:
                df['TelWhatsapp'] = df['TelWhatsapp'].apply(limpiar_telefono)
            if validar_emails and 'emlMail' in df.columns:
                df['email_valido'] = df['emlMail'].apply(validar_email)
            
            # Fechas
            if 'Fecha Insert Lead' in df.columns:
                df['Fecha_Lead'] = pd.to_datetime(df['Fecha Insert Lead'], format='%d-%m-%Y %H:%M:%S', errors='coerce').dt.date
                df = df.dropna(subset=['Fecha_Lead'])
            
            # Duplicados
            if eliminar_duplicados:
                subset = ['teltelefono']
                if validar_emails and 'emlMail' in df.columns:
                    subset.append('emlMail')
                df = df.drop_duplicates(subset=subset)
            
            # Procesar grupos
            resultados = []
            grupos_activos = [g for g in st.session_state.grupos_por_cliente[st.session_state.cliente_actual] if g['activo']]
            
            for grupo in grupos_activos:
                df_filtrado = df[df['Resolución'].isin(grupo['resoluciones'])]
                
                if grupo['filtro_fecha'] and grupo['dias_antes'] is not None and 'Fecha_Lead' in df.columns:
                    if isinstance(grupo['dias_antes'], list):
                        fechas = [fecha_referencia - timedelta(days=d) for d in grupo['dias_antes']]
                        df_filtrado = df_filtrado[df_filtrado['Fecha_Lead'].isin(fechas)]
                    else:
                        fecha_objetivo = fecha_referencia - timedelta(days=grupo['dias_antes'])
                        df_filtrado = df_filtrado[df_filtrado['Fecha_Lead'] == fecha_objetivo]
                
                if not df_filtrado.empty:
                    archivo = generar_archivo_descarga(df_filtrado)
                    resultados.append({
                        'nombre': grupo['nombre'],
                        'data': df_filtrado,
                        'archivo': archivo,
                        'registros': len(df_filtrado),
                        'filename': f"{grupo['nombre']}.xlsx"
                    })
            
            st.session_state.resultados = resultados
            st.success(f"Procesado: {len(resultados)} grupos")
            
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Resultados
if 'resultados' in st.session_state and st.session_state.resultados:
    st.header("Resultados")
    
    for resultado in st.session_state.resultados:
        with st.expander(f"{resultado['nombre']} ({resultado['registros']} registros)"):
            if mostrar_vista_previa:
                st.dataframe(resultado['data'].head(3), use_container_width=True)
            
            st.download_button(
                f"Descargar {resultado['nombre']}",
                resultado['archivo'],
                resultado['filename'],
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    if st.button("Nuevo procesamiento"):
        del st.session_state.resultados
        st.rerun()

# Ayuda
with st.expander("Ayuda"):
    st.markdown("""
    **Cómo usar:**
    1. Configura los grupos en la barra lateral
    2. Sube tus archivos Excel
    3. Haz clic en Procesar
    4. Descarga los resultados
    
    **Columnas requeridas:**
    - Nombre y Apellido
    - teltelefono
    - Resolución
    - Fecha Insert Lead
    - emlMail (opcional)
    """)

st.caption(f"Versión {datetime.now().strftime('%d/%m/%Y')}")