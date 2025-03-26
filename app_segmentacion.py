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
    layout="wide"
)

# Estilos mínimos
st.markdown("""
    <style>
        .primary-button {
            background-color: #2e86de !important;
            color: white !important;
        }
        .secondary-button {
            background-color: #f8f9fa !important;
            border: 1px solid #ddd !important;
        }
    </style>
""", unsafe_allow_html=True)

# Funciones principales
def obtener_nombre(df):
    # Busca columnas de nombre en diferentes formatos
    for col in ['Nombre y Apellido', 'Nombre', 'nombre', 'NOMBRE']:
        if col in df.columns:
            return df[col].apply(lambda x: str(x).split()[0].title() if pd.notna(x) else '')
    return pd.Series([''] * len(df))

def limpiar_telefono(numero):
    if pd.isna(numero):
        return ''
    return ''.join(filter(str.isdigit, str(numero)))

def procesar_archivos(uploaded_files):
    dfs = []
    for uploaded_file in uploaded_files:
        try:
            df = pd.read_excel(uploaded_file, engine='openpyxl')
            dfs.append(df)
        except:
            try:
                df = pd.read_excel(uploaded_file, engine='xlrd')
                dfs.append(df)
            except Exception as e:
                st.warning(f"Error con {uploaded_file.name}: {str(e)}")
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

# Inicialización
if 'clientes' not in st.session_state:
    st.session_state.clientes = {"Cliente 1": {"grupos": []}}

if 'cliente_actual' not in st.session_state:
    st.session_state.cliente_actual = "Cliente 1"

# Sidebar - Gestión de clientes
with st.sidebar:
    st.header("Clientes")
    
    # Selector de cliente
    if 'clientes' in st.session_state and st.session_state.clientes:
        cliente_seleccionado = st.selectbox(
            "Seleccionar cliente",
            list(st.session_state.clientes.keys()),
            index=list(st.session_state.clientes.keys()).index(st.session_state.cliente_actual)
        
        if cliente_seleccionado != st.session_state.cliente_actual:
            st.session_state.cliente_actual = cliente_seleccionado
            st.rerun()
    
    # Agregar nuevo cliente
    with st.form("nuevo_cliente_form"):
        nuevo_cliente = st.text_input("Nombre del nuevo cliente", key="nuevo_cliente_input")
        if st.form_submit_button("Agregar cliente", type="primary") and nuevo_cliente:
            if nuevo_cliente not in st.session_state.clientes:
                st.session_state.clientes[nuevo_cliente] = {"grupos": []}
                st.session_state.cliente_actual = nuevo_cliente
                st.rerun()
    
    # Eliminar cliente actual (si hay más de uno)
    if len(st.session_state.clientes) > 1:
        if st.button("Eliminar cliente actual", type="secondary"):
            del st.session_state.clientes[st.session_state.cliente_actual]
            st.session_state.cliente_actual = list(st.session_state.clientes.keys())[0]
            st.rerun()
    
    st.divider()
    
    # Configuración
    st.header("Configuración")
    fecha_referencia = st.date_input("Fecha base", datetime.now())
    
    st.divider()
    
    # Gestión de grupos
    st.header("Grupos")
    
    # Agregar grupo
    with st.form("nuevo_grupo_form"):
        nombre_grupo = st.text_input("Nombre del nuevo grupo", key="nuevo_grupo_input")
        if st.form_submit_button("Agregar grupo", type="primary") and nombre_grupo:
            st.session_state.clientes[st.session_state.cliente_actual]["grupos"].append({
                "nombre": nombre_grupo,
                "resoluciones": [],
                "dias_antes": [1]  # Por defecto 1 día antes
            })
            st.rerun()
    
    # Lista de grupos
    if st.session_state.cliente_actual in st.session_state.clientes:
        grupos = st.session_state.clientes[st.session_state.cliente_actual]["grupos"]
        for i, grupo in enumerate(grupos):
            st.subheader(grupo["nombre"], divider="gray")
            
            # Resoluciones
            grupo["resoluciones"] = st.text_area(
                "Resoluciones (una por línea)",
                "\n".join(grupo["resoluciones"]),
                key=f"res_{i}",
                height=100
            ).split('\n')
            
            # Configuración de fecha
            grupo["dias_antes"] = st.multiselect(
                "Días antes de la fecha base",
                options=list(range(8)),
                default=grupo["dias_antes"],
                key=f"dias_{i}"
            )
            
            # Eliminar grupo
            if st.button("Eliminar grupo", key=f"del_{i}", type="secondary"):
                grupos.pop(i)
                st.rerun()

# Área principal
st.title("Segmentación de Leads")

uploaded_files = st.file_uploader(
    "Subir archivos Excel (.xls, .xlsx)", 
    type=["xls", "xlsx"], 
    accept_multiple_files=True
)

if uploaded_files:
    if st.button("Procesar archivos", type="primary"):
        with st.spinner("Procesando..."):
            try:
                df = procesar_archivos(uploaded_files)
                
                # Procesamiento básico
                df['Nombre'] = obtener_nombre(df)
                
                if 'teltelefono' in df.columns:
                    df['Telefono'] = df['teltelefono'].apply(limpiar_telefono)
                
                # Procesar grupos
                resultados = []
                grupos = st.session_state.clientes[st.session_state.cliente_actual]["grupos"]
                
                for grupo in grupos:
                    if not grupo["resoluciones"]:
                        continue
                        
                    df_filtrado = df[df['Resolución'].isin(grupo["resoluciones"])]
                    
                    if 'Fecha Insert Lead' in df.columns and grupo["dias_antes"]:
                        df['Fecha_Lead'] = pd.to_datetime(df['Fecha Insert Lead'], errors='coerce').dt.date
                        fechas = [fecha_referencia - timedelta(days=d) for d in grupo["dias_antes"]]
                        df_filtrado = df_filtrado[df_filtrado['Fecha_Lead'].isin(fechas)]
                    
                    if not df_filtrado.empty:
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df_filtrado[['Nombre', 'Telefono', 'emlMail', 'Carrera Interes', 'Resolución']].to_excel(writer, index=False)
                        resultados.append({
                            'nombre': grupo["nombre"],
                            'data': output.getvalue(),
                            'registros': len(df_filtrado)
                        })
                
                st.session_state.resultados = resultados
                st.success("Procesamiento completado")
                
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Mostrar resultados
if 'resultados' in st.session_state and st.session_state.resultados:
    st.header("Resultados")
    
    for resultado in st.session_state.resultados:
        st.download_button(
            label=f"Descargar {resultado['nombre']} ({resultado['registros']} registros)",
            data=resultado['data'],
            file_name=f"{resultado['nombre']}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
    
    if st.button("Nuevo procesamiento", type="secondary"):
        del st.session_state.resultados
        st.rerun()