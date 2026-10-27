from __future__ import annotations

from datetime import datetime



_WEATHER = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Rime fog", 51: "Light drizzle", 53: "Drizzle",
    55: "Heavy drizzle", 56: "Freezing drizzle", 57: "Heavy freezing drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain", 66: "Freezing rain",
    67: "Heavy freezing rain", 71: "Light snow", 73: "Snow", 75: "Heavy snow",
    77: "Snow grains", 80: "Rain showers", 81: "Heavy showers", 82: "Violent showers",
    85: "Snow showers", 86: "Heavy snow showers", 95: "Thunderstorm",
    96: "Thunderstorm with hail", 99: "Severe thunderstorm with hail",
}


def weather_action(parameters: dict, player=None, session_memory=None) -> str:
    city = str((parameters or {}).get("city") or "").strip()
    if not city:
        return "The city is missing for the weather report."
    try:
        import requests
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "en", "format": "json"},
            timeout=8,
        )
        geo.raise_for_status()
        matches = geo.json().get("results") or []
        if not matches:
            return f"I couldn't find a location matching {city}."
        place = matches[0]
        forecast = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": place["latitude"], "longitude": place["longitude"],
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                "forecast_days": 5, "timezone": "auto",
            },
            timeout=8,
        )
        forecast.raise_for_status()
        data = forecast.json()
        current = data.get("current") or {}
        units = data.get("current_units") or {}
        daily = data.get("daily") or {}
        city_label = ", ".join(x for x in (place.get("name"), place.get("admin1"), place.get("country")) if x)
        code = int(current.get("weather_code", -1))
        lines = [
            f"{_WEATHER.get(code, 'Current conditions')}  ·  {current.get('temperature_2m', '—')} {units.get('temperature_2m', '°C')}",
            f"Feels like {current.get('apparent_temperature', '—')}°  ·  Humidity {current.get('relative_humidity_2m', '—')}%  ·  Wind {current.get('wind_speed_10m', '—')} {units.get('wind_speed_10m', 'km/h')}",
            "", "FIVE-DAY OUTLOOK",
        ]
        dates = daily.get("time", [])
        for i, day in enumerate(dates[:5]):
            day_code = int(daily.get("weather_code", [-1] * len(dates))[i])
            hi = daily.get("temperature_2m_max", [None] * len(dates))[i]
            lo = daily.get("temperature_2m_min", [None] * len(dates))[i]
            rain = daily.get("precipitation_probability_max", [None] * len(dates))[i]
            try:
                day_name = datetime.fromisoformat(day).strftime("%a %d %b")
            except ValueError:
                day_name = day
            lines.append(f"{day_name:<10} {_WEATHER.get(day_code, 'Forecast'):<24} {lo}° / {hi}°   Rain {rain if rain is not None else '—'}%")
        summary = "\n".join(lines)
        if player is not None and hasattr(player, "show_weather_preview"):
            player.show_weather_preview(city_label, summary)
        if session_memory:
            try:
                session_memory.set_last_search(query=f"weather in {city_label}", response=summary)
            except Exception:
                pass
        return (f"Weather preview is open in the Mark LVI display for {city_label}. "
                f"Current conditions: {lines[0]}. {lines[1]}")
    except Exception as exc:
        message = f"Weather preview unavailable for {city}: {exc}"
        if player is not None and hasattr(player, "show_weather_preview"):
            player.show_weather_preview(city, message)
        return message


TOOL = {
    "name": "weather_report",
    "description": "Fetches current conditions and a five-day forecast, then previews them inside the Mark LVI display.",
    "parameters": {
        "type": "OBJECT",
        "properties": {"city": {"type": "STRING", "description": "City or place name"}},
        "required": ["city"],
    },
    "handler": weather_action,
}
