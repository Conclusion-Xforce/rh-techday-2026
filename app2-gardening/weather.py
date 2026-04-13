from datetime import date

import httpx

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


async def geocode(location: str) -> dict | None:
    """Geocode a location name to lat/lon using Open-Meteo."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(GEOCODING_URL, params={"name": location, "count": 1})
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results")
        if not results:
            return None
        r = results[0]
        return {
            "name": r["name"],
            "latitude": r["latitude"],
            "longitude": r["longitude"],
            "country": r.get("country", ""),
        }


async def get_weather(latitude: float, longitude: float) -> dict:
    """Fetch current weather from Open-Meteo."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            WEATHER_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
            },
        )
        resp.raise_for_status()
        current = resp.json().get("current", {})
        return {
            "temperature": current.get("temperature_2m"),
            "humidity": current.get("relative_humidity_2m"),
            "precipitation": current.get("precipitation"),
            "wind_speed": current.get("wind_speed_10m"),
        }


def get_season(latitude: float) -> str:
    """Determine the current season based on date and hemisphere."""
    month = date.today().month
    # Meteorological seasons
    if month in (3, 4, 5):
        return "spring" if latitude >= 0 else "autumn"
    elif month in (6, 7, 8):
        return "summer" if latitude >= 0 else "winter"
    elif month in (9, 10, 11):
        return "autumn" if latitude >= 0 else "spring"
    else:
        return "winter" if latitude >= 0 else "summer"
