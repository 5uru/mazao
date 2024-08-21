import datetime
import json
import os

import streamlit as st
from dotenv import load_dotenv
from streamlit_calendar import calendar
from streamlit_geolocation import streamlit_geolocation

from app.db_managers import add_event
from app.db_managers import add_management_zone
from app.db_managers import delete_all_zone_events_by_type
from app.db_managers import get_events_by_zone
from app.db_managers import get_management_zones
from app.predict_plant_disease import predict
from app.watering import generate_detailed_watering_plan
from app.weather import get_weather

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
custom_css = """
            .fc-event-past {
                opacity: 0.8;
            }
            .fc-event-time {
                font-style: italic;
            }
            .fc-event-title {
                font-weight: 700;
            }
            .fc-toolbar-title {
                font-size: 2rem;
            }
        """
st.set_page_config(
    page_title="Mazao",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="auto",
    menu_items=None,
)


@st.cache_data
def get_zone_data(
    zone_id: int, zone_name: str, crop_type: str, longitude: float, latitude: float
):
    """

    :param zone_id: int: 
    :param zone_name: str: 
    :param crop_type: str: 
    :param longitude: float: 
    :param latitude: float: 

    """
    return zone_id, zone_name, crop_type, longitude, latitude


@st.cache_data
def get_weather_data(city: str):
    """

    :param city: str: 

    """
    return get_weather(city)


# Initialize session state
if "current_zone" not in st.session_state:
    st.session_state.current_zone = None

if "watering_plan" not in st.session_state:
    st.session_state.watering_plan = None


@st.dialog("Créer une nouvelle zone de gestion", width="large")
def new_zone():
    """ """
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
        st.rerun()


@st.dialog("Ajouter un événement", width="large")
def add_new_event():
    """ """
    name = st.text_input("Nom")
    date = st.date_input("Date")
    time = st.time_input("Heure")
    event_type = st.selectbox("Type", ["Arrosage", "Soin", "Autre"])
    if event_type == "Arrosage":
        event_type = "green"
    elif event_type == "Soin":
        event_type = "yellow"
    else:
        event_type = "blue"
    description = st.text_area("Description")
    if st.button("Ajouter"):
        add_event(
            name,
            datetime.datetime.combine(date, time),
            st.session_state.current_zone.id,
            event_type,
            description,
        )
        st.rerun()


@st.dialog("Analyser une image", width="large")
def analyze_image():
    """ """
    if not (img_path := st.file_uploader("Sélectionnez une image")):
        return
    st.image(img_path, caption="Image sélectionnée", use_column_width=True)
    if st.button("Analyser"):
        disease = predict(img_path)
        # Path to the JSON file
        file_path = "disease_treatment.json"

        # Read the JSON file
        with open(file_path, "r", encoding="utf-8") as file:
            disease_treatment = json.load(file)
        disease_data = disease_treatment[disease]
        if disease_data["type"] == "maladie":
            st.error(f"Maladie détectée : {disease}")
            st.write(f"*Agent pathogène:* {disease_data['agent_pathogene']}")
            st.write("*Suggestion de traitement:*")
            for traitement in disease_data["traitement"]:
                st.write(f"- {traitement}")
            st.write(
                f"*Suggestion traitement chimique:* {disease_data['suggestion_traitement_chimique']}"
            )
        else:
            st.success("La plante est saine!")


st.title("Weather App")

col1, col2 = st.columns([2, 8], gap="large")
with col1:
    if st.button("Nouvelle Zone \n de Gestion"):
        new_zone()

    management_zones = get_management_zones()
    st.write("###  Zones de gestion")

    for zone in management_zones:
        if st.button(f"{zone.name}"):
            st.session_state.current_zone = zone
            st.session_state.watering_plan = (
                None  # Reset watering plan when changing zones
            )
            st.rerun()

    if st.button("Clear Cache"):
        get_zone_data.clear()
        get_weather_data.clear()
        st.rerun()

with col2:
    if st.session_state.current_zone:
        zone = st.session_state.current_zone
        zone_id, zone_name, crop_type, longitude, latitude = get_zone_data(
            zone.id, zone.name, zone.crop_type, zone.longitude, zone.latitude
        )

        st.write(f"# {zone_name}")

        temp, humidity, _ = get_weather_data(
            f"{latitude},{longitude}"
        )  # Use zone's location

        col_temp, col_humidity = st.columns(2, gap="small")
        col_temp.metric("Temperature (°C)", temp)
        col_humidity.metric("Humidité (%)", humidity)
        col_event, col_add_event, col_disease = st.columns(3)
        with col_event:
            st.write("### Événements")
        with col_add_event:
            if st.button("Ajouter un événement"):
                add_new_event()
        with col_disease:
            if st.button("Analyser une image"):
                analyze_image()
        calendar_events = []
        for event in get_events_by_zone(zone_id):
            event_date = (
                datetime.datetime.strptime(event.date, "%Y-%m-%d %H:%M:%S")
                if isinstance(event.date, str)
                else event.date
            )
            calendar_events.append(
                {
                    "title": f" {event.name} :  {event.description}",
                    "start": event_date.strftime("%Y-%m-%dT%H:%M:%S"),
                    "backgroundColor": event.type,
                }
            )

        calendar = calendar(
            events=calendar_events,
            custom_css=custom_css,
            options={"initialView": "listWeek", "locale": "fr"},
        )

        if st.button("Generer une nouvelle planification"):
            st.session_state.watering_plan = generate_detailed_watering_plan(
                plant_name=crop_type,
                water_frequency=4,
                base_amount=500,
                latitude=latitude,
                longitude=longitude,
                api_key=API_KEY,
            )
            st.rerun()

        if st.session_state.watering_plan:
            st.write("### Plan d'arrosage")
            for plan in st.session_state.watering_plan["daily_plans"]:
                delete_all_zone_events_by_type(zone_id, "green")
                date = datetime.datetime.strptime(plan["date"], "%Y-%m-%d")
                for watering_event in plan["watering_schedule"]:
                    st.write(
                        f"Arrosage {date.strftime('%Y-%m-%d')} {watering_event['time']}"
                    )
                    st.write(watering_event["description"])

            if st.button("Ajouter à l'agenda"):
                for daily_plan in st.session_state.watering_plan["daily_plans"]:

                    date = datetime.datetime.strptime(daily_plan["date"], "%Y-%m-%d")
                    for watering_event in daily_plan["watering_schedule"]:
                        add_event(
                            name="Arrosage",
                            date=datetime.datetime.combine(
                                date,
                                datetime.datetime.strptime(
                                    watering_event["time"], "%H:%M"
                                ).time(),
                            ),
                            event_type="green",
                            management_zone_id=zone_id,
                            description=watering_event["description"],
                        )
                st.success(
                    "Tous les événements ont été ajoutés à l'agenda avec succès!"
                )
                st.session_state.watering_plan = (
                    None  # Reset the plan after adding to agenda
                )
                st.rerun()
    else:
        st.write("Veuillez sélectionner une zone de gestion")
