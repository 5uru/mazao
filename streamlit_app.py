import streamlit as st
from app.weather import get_weather
from app.db_managers import add_management_zone
from streamlit_geolocation import streamlit_geolocation


temp, humidity, clouds = get_weather("Cotonou")

st.set_page_config(
    page_title="Mazao",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="auto",
    menu_items=None,
)


@st.dialog("Créer une nouvelle zone de gestion", width="large")
def new_zone():
    name = st.text_input("Nom")
    crop_type = st.selectbox(
        "Type de culture", ["Maïs", "Tomate", "Piment", "Pomme de terre"]
    )
    st.write("Localisation")
    loc1, loc2 = st.columns([8, 2])
    with loc1:
        st.write("Cliquez sur le bouton pour obtenir votre localisation actuelle:")
    with loc2:
        location = streamlit_geolocation()
    loc_longitude, loc_latitude = 0, 0
    if location is not None:
        loc_latitude = location["latitude"]
        loc_longitude = location["longitude"]
    longitude = st.number_input("Longitude", value=loc_longitude)
    latitude = st.number_input("Latitude", value=loc_latitude)
    if st.button("Ajouter"):
        add_management_zone(name, crop_type, longitude, latitude)


st.title("Weather App")

col1, col2 = st.columns([2, 8], gap="large")
with col1:
    if st.button("Nouvelle Zone \n de Gestion"):
        new_zone()


with col2:
    col_temp, col_humidity = st.columns(
        2,
        gap="small",
    )

with col_temp:
    st.metric("Temperature (°C)", temp)
with col_humidity:
    st.metric("Humidité (%)", humidity)
