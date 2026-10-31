import logging
import requests
from langchain_core.tools import tool

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@tool
def get_current_weather(location: str) -> dict:
    """Get current weather for a specific location.

    Always include the country when possible.
    Examples:
    - Delhi, India
    - London, United Kingdom
    - Toronto, Canada
    """
    logger.info("Fetching weather data for location: '%s'", location)
    settings = get_settings()

    url = "https://api.weatherapi.com/v1/current.json"
    params = {
        "key": settings.weatherapi_api_key,
        "q": location,
        "aqi": "no",
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        weather_data = {
            "location": data["location"]["name"],
            "region": data["location"]["region"],
            "country": data["location"]["country"],
            "temperature_c": data["current"]["temp_c"],
            "condition": data["current"]["condition"]["text"],
            "humidity": data["current"]["humidity"],
            "wind_kph": data["current"]["wind_kph"],
        }
        logger.debug("Weather data retrieved successfully for '%s': %s", location, weather_data)
        return weather_data

    except requests.exceptions.Timeout as exc:
        logger.error("WeatherAPI timed out for location '%s'", location)
        raise RuntimeError("Weather service timed out.") from exc

    except requests.exceptions.HTTPError as exc:
        logger.error("WeatherAPI returned HTTP error for location '%s': %s", location, exc)
        raise RuntimeError("Weather service returned an HTTP error.") from exc

    except requests.exceptions.RequestException as exc:
        logger.error("Could not connect to WeatherAPI for location '%s': %s", location, exc)
        raise RuntimeError("Could not connect to the weather service.") from exc
