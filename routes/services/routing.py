import requests
from django.conf import settings

METERS_PER_MILE = 1609.344


class RoutingError(Exception):
    pass


def get_route(start, finish):
    # one OSRM call -> (path of (lat, lng) vertices, distance in miles)
    coords = f"{start[1]},{start[0]};{finish[1]},{finish[0]}"  # OSRM wants lng,lat
    url = f"{settings.OSRM_BASE_URL}/route/v1/driving/{coords}"
    params = {"overview": "simplified", "geometries": "geojson"}

    try:
        resp = requests.get(url, params=params, timeout=settings.OSRM_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        raise RoutingError(f"routing provider unavailable: {exc}") from exc

    if data.get("code") != "Ok" or not data.get("routes"):
        raise RoutingError("no route found between the given locations")

    route = data["routes"][0]
    path = [(lat, lng) for lng, lat in route["geometry"]["coordinates"]]  # back to lat,lng
    distance_miles = route["distance"] / METERS_PER_MILE
    return path, distance_miles
