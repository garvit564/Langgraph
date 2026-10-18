import requests

from langchain_core.tools import tool

from src.app.core.config import get_settings


@tool
def get_current_weather(location: str) -> dict:
    """Get current weather for a specific location.

    Always include the country when possible.
    Examples:
    - Delhi, India
    - London, United Kingdom
    - Toronto, Canada
    """

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

        return {
            "location": data["location"]["name"],
            "region": data["location"]["region"],
            "country": data["location"]["country"],
            "temperature_c": data["current"]["temp_c"],
            "condition": data["current"]["condition"]["text"],
            "humidity": data["current"]["humidity"],
            "wind_kph": data["current"]["wind_kph"],
        }

    except requests.exceptions.Timeout as exc:
        raise RuntimeError(
            "Weather service timed out."
        ) from exc

    except requests.exceptions.HTTPError as exc:
        raise RuntimeError(
            "Weather service returned an HTTP error."
        ) from exc

    except requests.exceptions.RequestException as exc:
        raise RuntimeError(
            "Could not connect to the weather service."
        ) from exc