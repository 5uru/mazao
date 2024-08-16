import requests


class Plant:
    """ """
    def __init__(self, name, water_frequency):
        self.name = name
        self.water_frequency = water_frequency  # in days


def _estimate_light_level(condition):
    """

    :param condition:

    """
    sunny_conditions = ["Sunny", "Clear"]
    partly_cloudy_conditions = ["Partly cloudy"]
    cloudy_conditions = ["Cloudy", "Overcast"]

    if any(cond in condition for cond in sunny_conditions):
        return 80
    elif any(cond in condition for cond in partly_cloudy_conditions):
        return 60
    elif any(cond in condition for cond in cloudy_conditions):
        return 40
    else:
        return 50  # Default value for other conditions


def process_forecast(forecast_data):
    """

    :param forecast_data:

    """
    return [
        {
            "date": day["date"],
            "temp_c": day["day"]["avgtemp_c"],
            "humidity": day["day"]["avghumidity"],
            "light_level": _estimate_light_level(day["day"]["condition"]["text"]),
        }
        for day in forecast_data["forecast"]["forecastday"]
    ]


class WeatherForecast:
    """ """
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.weatherapi.com/v1/forecast.json"

    def get_forecast(self, latitude, longitude, days=3):
        """

        :param latitude:
        :param longitude:
        :param days:  (Default value = 3)

        """
        params = {"key": self.api_key, "q": f"{latitude},{longitude}", "days": days}
        response = requests.get(self.base_url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            # sourcery skip: raise-specific-error
            raise Exception(
                f"Failed to fetch weather data: {response.status_code} - {response.text}"
            )


def _calculate_water_amount(temperature, humidity, light_level):
    """

    :param temperature:
    :param humidity:
    :param light_level:

    """
    base_amount = 250  # ml
    if temperature > 30:
        base_amount *= 1.2
    elif temperature < 20:
        base_amount *= 0.8
    if humidity < 40:
        base_amount *= 1.1
    elif humidity > 70:
        base_amount *= 0.9
    if light_level > 80:
        base_amount *= 1.1
    elif light_level < 20:
        base_amount *= 0.9

    return round(base_amount)


def _determine_best_time(temperature, light_level):
    """

    :param temperature:
    :param light_level:

    """
    if temperature > 30 or light_level > 80:
        return "Early morning or late evening"
    elif temperature < 20 or light_level < 20:
        return "Midday"
    else:
        return "Any time of day"


def _get_special_instructions(temperature, humidity, light_level):
    """

    :param temperature:
    :param humidity:
    :param light_level:

    """
    instructions = []
    if temperature > 35:
        instructions.append("Consider misting the leaves to cool the plant")
    if humidity < 30:
        instructions.append("Place a humidity tray near the plant")
    if light_level > 90:
        instructions.append("Provide some shade during peak sunlight hours")
    if light_level < 10:
        instructions.append("Consider supplemental grow lights")
    return instructions or ["No special instructions"]


def _adjust_frequency(original_frequency, temperature, humidity, light_level):
    """

    :param original_frequency:
    :param temperature:
    :param humidity:
    :param light_level:

    """
    adjustment = 0
    if temperature > 30:
        adjustment -= 1
    elif temperature < 20:
        adjustment += 1
    if humidity < 40:
        adjustment -= 1
    elif humidity > 70:
        adjustment += 1
    if light_level > 80:
        adjustment -= 1
    elif light_level < 20:
        adjustment += 1

    return max(1, original_frequency + adjustment)


class AIWateringPlanner:
    """ """
    def __init__(self, plant):
        self.plant = plant

    def generate_watering_plan(self, current_conditions, forecast):
        """

        :param current_conditions:
        :param forecast:

        """
        print(
            f"Current conditions: Temp: {current_conditions['temp_c']:.1f}°C, "
            f"Humidity: {current_conditions['humidity']:.1f}%, "
            f"Light: {current_conditions['light_level']:.1f}%"
        )

        plan = {
            "plant_name": self.plant.name,
            "original_frequency": self.plant.water_frequency,
            "daily_plans": [],
        }

        for day in range(3):
            conditions = current_conditions if day == 0 else forecast[day - 1]
            adjusted_frequency = _adjust_frequency(
                self.plant.water_frequency,
                conditions["temp_c"],
                conditions["humidity"],
                conditions["light_level"],
            )
            water_amount = _calculate_water_amount(
                conditions["temp_c"], conditions["humidity"], conditions["light_level"]
            )
            best_time = _determine_best_time(
                conditions["temp_c"], conditions["light_level"]
            )

            daily_plan = {
                "date": conditions.get("date", "Today"),
                "adjusted_frequency": adjusted_frequency,
                "water_amount": water_amount,
                "best_time": best_time,
                "special_instructions": _get_special_instructions(
                    conditions["temp_c"],
                    conditions["humidity"],
                    conditions["light_level"],
                ),
            }
            plan["daily_plans"].append(daily_plan)

        return plan


def generate_detailed_watering_plan(
    plant_name, water_frequency, latitude, longitude, api_key
):
    """

    :param plant_name:
    :param water_frequency:
    :param latitude:
    :param longitude:
    :param api_key:

    """
    plant = Plant(plant_name, water_frequency)
    planner = AIWateringPlanner(plant)
    weather = WeatherForecast(api_key)

    forecast_data = weather.get_forecast(latitude, longitude)
    processed_forecast = process_forecast(forecast_data)

    current_conditions = {
        "temp_c": forecast_data["current"]["temp_c"],
        "humidity": forecast_data["current"]["humidity"],
        "light_level": _estimate_light_level(
            forecast_data["current"]["condition"]["text"]
        ),
    }

    watering_plan = planner.generate_watering_plan(
        current_conditions, processed_forecast
    )

    print("\nDetailed Watering Plan:")
    print(f"Plant: {watering_plan['plant_name']}")
    print(
        f"Original watering frequency: Every {watering_plan['original_frequency']} days"
    )

    for daily_plan in watering_plan["daily_plans"]:
        print(f"\nDate: {daily_plan['date']}")
        print(
            f"Adjusted watering frequency: Every {daily_plan['adjusted_frequency']} days"
        )
        print(f"Recommended water amount: {daily_plan['water_amount']} ml")
        print(f"Best time to water: {daily_plan['best_time']}")
        print("Special instructions:")
        for instruction in daily_plan["special_instructions"]:
            print(f"  - {instruction}")

    return watering_plan
