from src.app.infrastructure.tools.weather import get_current_weather


if __name__ == "__main__":
    result = get_current_weather("Delhi")
    print(result)