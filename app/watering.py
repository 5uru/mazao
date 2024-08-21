import requests
from dataclasses import dataclass
from typing import List, Dict, Any
from enum import Enum
from datetime import datetime, timedelta

class WeatherCondition(Enum):
    SUNNY = 80
    PARTLY_CLOUDY = 60
    CLOUDY = 40
    DEFAULT = 50

@dataclass
class Plant:
    name: str
    water_frequency: int  # in days
    base_water_amount: int  # in ml

@dataclass
class HourlyWeatherData:
    datetime: datetime
    temp_c: float
    humidity: float
    light_level: int

@dataclass
class DailyWeatherData:
    date: str
    hourly_data: List[HourlyWeatherData]

class WeatherForecast:
    BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_forecast(self, latitude: float, longitude: float, days: int = 5, units: str = "metric", lang: str = "en") -> Dict[str, Any]:
        params = {
                "lat": latitude,
                "lon": longitude,
                "appid": self.api_key,
                "units": units,
                "lang": lang,
                "cnt": days * 8  # 3-hour intervals, 8 times per day
        }

        response = requests.get(self.BASE_URL, params=params)

        if response.status_code == 200:
            return response.json()
        else:
            raise ValueError(f"Failed to fetch weather data: {response.status_code} - {response.text}")

def estimate_light_level(condition: str) -> int:
    condition_map = {
            "Clear": WeatherCondition.SUNNY,
            "Few clouds": WeatherCondition.PARTLY_CLOUDY,
            "Scattered clouds": WeatherCondition.PARTLY_CLOUDY,
            "Broken clouds": WeatherCondition.CLOUDY,
            "Overcast clouds": WeatherCondition.CLOUDY,
    }
    return condition_map.get(condition, WeatherCondition.DEFAULT).value

def process_forecast(forecast_data: Dict[str, Any]) -> List[DailyWeatherData]:
    daily_data = {}
    for item in forecast_data['list']:
        dt = datetime.fromtimestamp(item['dt'])
        date_str = dt.strftime('%Y-%m-%d')
        hourly_data = HourlyWeatherData(
                datetime=dt,
                temp_c=item['main']['temp'],
                humidity=item['main']['humidity'],
                light_level=estimate_light_level(item['weather'][0]['description'])
        )

        if date_str not in daily_data:
            daily_data[date_str] = []
        daily_data[date_str].append(hourly_data)

    return [DailyWeatherData(date=date, hourly_data=data) for date, data in daily_data.items()]

class AIWateringPlanner:
    def __init__(self, plant: Plant):
        self.plant = plant

    @staticmethod
    def calculate_water_amount(base_amount: int, temperature: float, humidity: float, light_level: int) -> int:
        temp_factor = 1 + (temperature - 20) * 0.02  # 2% increase per degree above 20°C
        humidity_factor = 1 + (50 - humidity) * 0.01  # 1% increase per percentage point below 50%
        light_factor = 1 + (light_level - 50) * 0.005  # 0.5% increase per point above 50

        adjusted_amount = base_amount * temp_factor * humidity_factor * light_factor
        return max(round(adjusted_amount), base_amount // 2)  # Ensure at least half of base amount

    @staticmethod
    def adjust_frequency(original_frequency: int, temperature: float, humidity: float, light_level: int) -> int:
        env_score = (
                (temperature - 20) / 10 +  # Temperature impact
                (50 - humidity) / 20 +     # Humidity impact
                (light_level - 50) / 30    # Light impact
        )

        if env_score > 2:
            return max(1, original_frequency - 1)  # Water more frequently
        elif env_score < -2:
            return original_frequency + 1  # Water less frequently
        else:
            return original_frequency  # No change

    @staticmethod
    def get_special_instructions(temperature: float, humidity: float, light_level: int) -> List[str]:
        instructions = []
        if temperature > 35:
            instructions.append("Consider misting the leaves to cool the plant")
        if humidity < 30:
            instructions.append("Place a humidity tray near the plant")
        if light_level > 90:
            instructions.append("Provide some shade during peak sunlight hours")
        if light_level < 10:
            instructions.append("Consider supplemental grow lights")
        return instructions

    @staticmethod
    def calculate_watering_score(hour_data: HourlyWeatherData) -> float:
        # Lower score is better for watering
        temp_score = abs(hour_data.temp_c - 20)  # Ideal temperature around 20°C
        humidity_score = abs(hour_data.humidity - 60)  # Ideal humidity around 60%
        light_score = abs(hour_data.light_level - 50)  # Moderate light level is ideal

        return temp_score + humidity_score + light_score

    def determine_optimal_hours(self, daily_data: DailyWeatherData, adjusted_frequency: int) -> List[HourlyWeatherData]:
        sorted_hours = sorted(daily_data.hourly_data, key=self.calculate_watering_score)
        return sorted_hours[:adjusted_frequency]

    def generate_watering_plan(self, forecast: List[DailyWeatherData]) -> Dict[str, Any]:
        plan = {
                "plant_name": self.plant.name,
                "original_frequency": self.plant.water_frequency,
                "base_water_amount": self.plant.base_water_amount,
                "daily_plans": []
        }

        for daily_data in forecast:
            avg_temp = sum(h.temp_c for h in daily_data.hourly_data) / len(daily_data.hourly_data)
            avg_humidity = sum(h.humidity for h in daily_data.hourly_data) / len(daily_data.hourly_data)
            avg_light = sum(h.light_level for h in daily_data.hourly_data) / len(daily_data.hourly_data)

            adjusted_frequency = self.adjust_frequency(
                    self.plant.water_frequency,
                    avg_temp,
                    avg_humidity,
                    avg_light
            )

            optimal_hours = self.determine_optimal_hours(daily_data, adjusted_frequency)
            total_water_amount = self.calculate_water_amount(
                    self.plant.base_water_amount,
                    avg_temp,
                    avg_humidity,
                    avg_light
            )

            water_amount_per_session = total_water_amount // adjusted_frequency

            daily_plan = {
                    "date": daily_data.date,
                    "adjusted_frequency": adjusted_frequency,
                    "total_water_amount": total_water_amount,
                    "watering_schedule": []
            }

            for hour_data in optimal_hours:
                special_instructions = self.get_special_instructions(
                        hour_data.temp_c,
                        hour_data.humidity,
                        hour_data.light_level
                )

                description = f"Water with {water_amount_per_session} ml. "
                if special_instructions:
                    description += "Special instructions: " + "; ".join(special_instructions) + "."
                else:
                    description += "No special instructions."

                watering_event = {
                        "time": hour_data.datetime.strftime('%H:%M'),
                        "description": description
                }
                daily_plan["watering_schedule"].append(watering_event)

            plan["daily_plans"].append(daily_plan)

        return plan

def generate_detailed_watering_plan(
        plant_name: str,
        water_frequency: int,
        base_amount: int,
        latitude: float,
        longitude: float,
        api_key: str
) -> Dict[str, Any]:
    plant = Plant(plant_name, water_frequency, base_amount)
    planner = AIWateringPlanner(plant)
    weather = WeatherForecast(api_key)

    forecast_data = weather.get_forecast(latitude, longitude)
    processed_forecast = process_forecast(forecast_data)

    watering_plan = planner.generate_watering_plan(processed_forecast)

    return watering_plan