import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="EcoBici Real-Time", layout="wide")

st.title("🚲 Tablero EcoBici CDMX")
st.caption("Visualización y Storytelling Usando Datos | Edgar Avalos Gauna, 2026")

# --- 1. FUNCIÓN PARA OBTENER DATOS ---
@st.cache_data(ttl=60) # Cacheamos por 60 segundos para no saturar la API
def cargar_datos():
    url_info = "https://gbfs.mex.lyftbikes.com/gbfs/en/station_information.json"
    url_status = "https://gbfs.mex.lyftbikes.com/gbfs/en/station_status.json"
    
    # Información fija
    res_info = requests.get(url_info).json()
    df_info = pd.DataFrame(res_info['data']['stations'])
    
    # Estatus en tiempo real
    res_status = requests.get(url_status).json()
    df_status = pd.DataFrame(res_status['data']['stations'])
    
    # Unir datos
    df = pd.merge(df_info[['station_id', 'name', 'lat', 'lon']], 
                  df_status[['station_id', 'num_bikes_available', 'num_docks_available']], 
                  on='station_id')
    return df

try:
    df_ecobici = cargar_datos()

    # --- 2. MÉTRICAS RÁPIDAS ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Estaciones", len(df_ecobici))
    col2.metric("Bicis Disponibles", df_ecobici['num_bikes_available'].sum())
    col3.metric("Puertos Libres", df_ecobici['num_docks_available'].sum())

    # --- 3. MAPA INTERACTIVO CON PLOTLY ---
    st.subheader("Mapa de Disponibilidad")

    fig = px.scatter_mapbox(
        df_ecobici,
        lat="lat",
        lon="lon",
        hover_name="name",
        hover_data={
            "num_bikes_available": True,
            "num_docks_available": True,
            "lat": False,
            "lon": False
        },
        color="num_bikes_available", # El color cambia según disponibilidad
        color_continuous_scale=px.colors.cyclical.IceFire,
        size_max=15,
        zoom=12,
        height=600,
        labels={"num_bikes_available": "Bicis"}
    )

    # Estilo del mapa (Open Street Map no requiere Token de Mapbox)
    fig.update_layout(mapbox_style="carto-positron")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    st.plotly_chart(fig, use_container_width=True)

    # --- 4. TABLA DE DATOS (Opcional) ---
    with st.expander("Ver datos detallados"):
        st.dataframe(df_ecobici)

except Exception as e:
    st.error(f"Hubo un problema al cargar los datos: {e}")
