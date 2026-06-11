from functools import lru_cache

import pgeocode

# rough bounding box for the contiguous US (where the dataset and drivable routes live)
US_LAT_RANGE = (24.0, 49.5)
US_LNG_RANGE = (-125.0, -66.5)


def in_usa(lat, lng):
    return US_LAT_RANGE[0] <= lat <= US_LAT_RANGE[1] and US_LNG_RANGE[0] <= lng <= US_LNG_RANGE[1]


@lru_cache(maxsize=1)
def _city_index():
    # build {(city, state): (lat, lng)} once from the bundled US postal data
    data = pgeocode.Nominatim("us")._data.dropna(subset=["latitude", "longitude"])
    grouped = (
        data.assign(_city=data["place_name"].str.lower().str.strip())
        .groupby(["_city", "state_code"])[["latitude", "longitude"]]
        .mean()
    )
    return {(city, state): (row.latitude, row.longitude) for (city, state), row in grouped.iterrows()}


def geocode_city_state(city, state):
    if not city or not state:
        return None
    return _city_index().get((city.strip().lower(), state.strip().upper()))


def geocode_place(text):
    # accepts "lat,lng" or "City, ST"
    if not text:
        return None
    parts = [p.strip() for p in text.strip().split(",")]
    if len(parts) != 2:
        return None
    try:
        return float(parts[0]), float(parts[1])
    except ValueError:
        return geocode_city_state(parts[0], parts[1])
