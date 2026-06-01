import requests
from typing import Optional

HEADERS = {"User-Agent": "Lynthz-AI-Assistant/2.1"}

class GoogleMapsTool:
    NOMINATIM = "https://nominatim.openstreetmap.org"
    OSRM = "http://router.project-osrm.org/route/v1"

    def search_places(self, query, location=None):
        try:
            params = {"q": f"{query} {location}" if location else query, "format": "json", "limit": 5, "addressdetails": 1}
            resp = requests.get(f"{self.NOMINATIM}/search", params=params, headers=HEADERS, timeout=10)
            results = resp.json()
            if not results:
                return {"error": f"No places found for '{query}'"}
            places = [{"name": r.get("display_name", "").split(",")[0], "address": r.get("display_name"), "type": r.get("type")} for r in results]
            return {"query": query, "places": places, "type": "maps_places"}
        except Exception as e:
            return {"error": str(e)}

    def get_directions(self, origin, destination, mode="driving"):
        try:
            orig = self._geocode(origin)
            dest = self._geocode(destination)
            if not orig or not dest:
                return {"error": "Could not find locations"}
            profile = {"driving": "car", "walking": "foot", "cycling": "bike"}.get(mode, "car")
            url = f"{self.OSRM}/{profile}/{orig['lon']},{orig['lat']};{dest['lon']},{dest['lat']}"
            resp = requests.get(url, params={"overview": "false"}, timeout=10)
            data = resp.json()
            if data.get("code") != "Ok":
                return {"error": "Could not calculate route"}
            route = data["routes"][0]
            return {"origin": origin, "destination": destination, "distance": f"{round(route['distance']/1000, 1)} km", "duration": f"{round(route['duration']/60)} minutes", "mode": mode, "type": "maps_directions"}
        except Exception as e:
            return {"error": str(e)}

    def _geocode(self, location):
        try:
            params = {"q": location, "format": "json", "limit": 1}
            resp = requests.get(f"{self.NOMINATIM}/search", params=params, headers=HEADERS, timeout=10)
            results = resp.json()
            if results:
                return {"lat": results[0]["lat"], "lon": results[0]["lon"]}
            return None
        except Exception:
            return None

    def format_for_llm(self, data):
        if "error" in data:
            return f"Maps error: {data['error']}"
        if data.get("type") == "maps_places":
            text = f"Places found for '{data['query']}':\n"
            for i, p in enumerate(data["places"], 1):
                text += f"\n{i}. {p['name']}\n   Address: {p['address']}"
            return text
        if data.get("type") == "maps_directions":
            return f"Directions from {data['origin']} to {data['destination']}:\nDistance: {data['distance']}\nDuration: {data['duration']} by {data['mode']}"
        return str(data)