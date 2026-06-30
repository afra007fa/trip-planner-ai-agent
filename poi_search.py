import requests
import streamlit as st
from feedback_system import get_boost_score

HEADERS = {
    "User-Agent": "TripPlannerAI/1.0"
}

INTEREST_MAP = {
    "history": "museum",
    "food": "restaurant",
    "nature": "park",
    "shopping": "mall",
    "adventure": "attraction",
    "museums": "museum"
}


@st.cache_data
def geocode_city(city):
    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": city,
                "format": "json",
                "limit": 1
            },
            headers=HEADERS,
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        if not data:
            return None

        return (
            float(data[0]["lat"]),
            float(data[0]["lon"])
        )

    except Exception:
        return None


@st.cache_data
def search_pois(city, interests):

    location = geocode_city(city)

    if not location:
        return []

    lat, lon = location

    pois = []

    for interest in interests:

        category = INTEREST_MAP.get(
            interest.lower(),
            "attraction"
        )

        query = f"""
        [out:json][timeout:20];
        (
          node(around:4000,{lat},{lon});
        );
        out 50;
        """

        try:

            response = requests.post(
                "https://overpass-api.de/api/interpreter",
                data=query,
                headers=HEADERS,
                timeout=20
            )

            response.raise_for_status()

            data = response.json()

            if "elements" not in data:
                continue

            count = 0

            for item in data["elements"]:

                if count >= 5:
                    break

                if "lat" not in item or "lon" not in item:
                    continue

                poi = {
                    "poi_id": item["id"],
                    "name": item.get(
                        "tags",
                        {}
                    ).get(
                        "name",
                        f"{category.title()} Spot"
                    ),
                    "category": interest,
                    "lat": item["lat"],
                    "lon": item["lon"],
                    "boost": get_boost_score(
                        city,
                        item["id"]
                    )
                }

                pois.append(poi)
                count += 1

        except Exception:
            continue

    unique = {}

    for poi in pois:
        unique[poi["poi_id"]] = poi

    pois = list(unique.values())

    pois.sort(
        key=lambda x: x["boost"],
        reverse=True
    )

    return pois