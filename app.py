import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="EcoBici Real-Time", layout="wide")

st.title("🚲 Tablero EcoBici CDMX")
st.caption("Visualización y Storytelling Usando Datos | Edgar Avalos Gauna, 2026")

# --- 1. FUNCIÓN PARA OBTENER DATOS ---
@st.cache_data(ttl=60)
def cargar_datos():
    url_info = "https://gbfs.mex.lyftbikes.com/gbfs/en/station_information.json"
    url_status = "https://gbfs.mex.lyftbikes.com/gbfs/en/station_status.json"
    
    res_info = requests.get(url_info).json()
    df_info = pd.DataFrame(res_info['data']['stations'])
    
    res_status = requests.get(url_status).json()
    df_status = pd.DataFrame(res_status['data']['stations'])
    
    df = pd.merge(df_info[['station_id', 'name', 'lat', 'lon']], 
                  df_status[['station_id', 'num_bikes_available', 'num_docks_available']], 
                  on='station_id')
    
    # --- CÁLCULO DE NORMALIZACIÓN ---
    # Capacidad total teórica = bicis + puertos libres
    df['total_cap'] = df['num_bikes_available'] + df['num_docks_available']
    # Porcentaje de disponibilidad (evitando división por cero)
    df['disponibilidad_pct'] = (df['num_bikes_available'] / df['total_cap']).fillna(0) * 100
    
    return df

try:
    df_ecobici = cargar_datos()

    # --- 2. BARRA LATERAL (WIDGETS) ---
    st.sidebar.header("Configuración del Mapa")
    
    # Widget 1: Selección de Estación por ID o Nombre
    estaciones_list = sorted(df_ecobici['station_id'].unique(), key=int)
    seleccion_id = st.sidebar.selectbox("Selecciona una Estación (ID):", ["Ninguna"] + estaciones_list)
    
    # Widget 2: Control de Zoom
    zoom_level = st.sidebar.slider("Nivel de Zoom:", min_value=10, max_value=18, value=12)

    # Determinar Centroide o Estación Seleccionada
    if seleccion_id != "Ninguna":
        estacion_sel = df_ecobici[df_ecobici['station_id'] == seleccion_id].iloc[0]
        lat_map, lon_map = estacion_sel['lat'], estacion_sel['lon']
        # Añadimos una columna para resaltar la selección
        df_ecobici['es_seleccionada'] = df_ecobici['station_id'] == seleccion_id
    else:
        lat_map, lon_map = df_ecobici['lat'].mean(), df_ecobici['lon'].mean()
        df_ecobici['es_seleccionada'] = False

    # --- 3. MÉTRICAS RÁPIDAS ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Estaciones", len(df_ecobici))
    col2.metric("Bicis Disponibles", df_ecobici['num_bikes_available'].sum())
    col3.metric("Puertos Libres", df_ecobici['num_docks_available'].sum())

    # --- 4. MAPA INTERACTIVO ---
    st.subheader("Mapa de Disponibilidad Normalizada")
    st.info("El color representa el % de ocupación (Azul = Lleno, Rojo = Vacío).")

    # Tamaño de burbuja: más grande por defecto, y mucho más grande si está seleccionada
    df_ecobici['tamano_marker'] = df_ecobici['es_seleccionada'].map({True: 30, False: 10})

    fig = px.scatter_mapbox(
        df_ecobici,
        lat="lat",
        lon="lon",
        hover_name="name",
        hover_data={
            "station_id": True,
            "num_bikes_available": True,
            "num_docks_available": True,
            "disponibilidad_pct": ":.2f",
            "lat": False,
            "lon": False,
            "tamano_marker": False
        },
        color="disponibilidad_pct",
        color_continuous_scale="RdYlBu", # Rojo (pocas bicis) a Azul (muchas bicis)
        size="tamano_marker",            # Aplicamos el tamaño diferenciado
        size_max=10,
        zoom=zoom_level,
        center={"lat": lat_map, "lon": lon_map},
        height=700,
        labels={"disponibilidad_pct": "% Bicis"}
    )

    fig.update_layout(
        mapbox_style="carto-positron",
        margin={"r":0,"t":0,"l":0,"b":0},
        coloraxis_colorbar=dict(title="% Llenado")
    )

    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Ver tabla de datos calculados"):
        st.dataframe(df_ecobici[['station_id', 'name', 'num_bikes_available', 'total_cap', 'disponibilidad_pct']])

except Exception as e:
    st.error(f"Error en la aplicación: {e}")
