"""Lynthz Weather Tool — OpenWeatherMap"""

import os
import requests


class WeatherTool:
    def __init__(self):
        self.api_key = os.getenv("WEATHER_API_KEY")
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"

    def get_weather(self, location: str) -> dict:
        if not self.api_key:
            return {"error": "No weather API key configured"}
        try:
            resp = requests.get(self.base_url, params={
                "q": location,
                "appid": self.api_key,
                "units": "metric"
            }, timeout=8)
            resp.raise_for_status()
            d = resp.json()
            return {
                "location": d["name"],
                "country": d["sys"]["country"],
                "temp": round(d["main"]["temp"]),
                "feels_like": round(d["main"]["feels_like"]),
                "description": d["weather"][0]["description"].title(),
                "humidity": d["main"]["humidity"],
                "wind_speed": d["wind"]["speed"],
                "icon": d["weather"][0]["icon"]
            }
        except Exception as e:
            return {"error": str(e)}
