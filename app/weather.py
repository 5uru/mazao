import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
API_KEY = os.getenv("OPENWEATHERMAP_API_KEYS")


def get_weather(city):
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": API_KEY, "units": "metric"}  # For Celsius
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise an exception for bad responses
        data = response.json()
        print(data)
        # Extract weather information
        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        clouds = data["clouds"]["all"]

        return temp, humidity, clouds

    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        if (
            isinstance(e, requests.exceptions.HTTPError)
            and e.response.status_code == 401
        ):
            print("Please check your API key.")
    except KeyError as e:
        print(f"Error parsing weather data: {e}")
        print("API Response:", data)
    finally:
        return 0, 0, 0  # Return default values in case of any error
