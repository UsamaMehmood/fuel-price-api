# Fuel Route API

Given a **start** and **finish** in the USA, this API returns the driving route, the
**cost-optimal fuel stops** along it (the vehicle has a 500-mile range), and the **total
fuel cost** at 10 miles per gallon.

Built with **Django 5 + Django REST Framework**.

---

## Highlights

- **One external call per route.** A request makes a single call to the routing API; the
  cheapest-fuel logic runs entirely on local data.
- **Fast.** Local computation is a few milliseconds; identical trips are cached and served
  in ~1 ms.
- **Self-contained data.** Fuel-station coordinates are geocoded **once, offline** at load
  time — no per-request geocoding.

---

## Prerequisites

- **Python 3.10+** (Django 5 requires it). Check with `python3 --version`.
  - If your system Python is older, use [`pyenv`](https://github.com/pyenv/pyenv):
    `pyenv install 3.12.11 && pyenv local 3.12.11`.
- **Internet access** is needed twice: once when loading the data (to fetch the offline
  geocoding dataset) and on each new route (the routing API). Cached routes need no network.
- The fuel-price CSV is included at `data/fuel-prices-for-be-assessment.csv`.

---

## Setup (step by step)

```bash
# 1. Enter the project
cd fuel-route-api

# 2. Create and activate a virtual environment (Python 3.10+)
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create the database tables
python manage.py migrate

# 5. Load + geocode the fuel stations (one-time; needs internet the first time)
python manage.py load_fuel_data
#    -> "Loaded 7524 stations, skipped 627 (no US city match)."

# 6. Run the server
python manage.py runserver
```

The API is now at `http://127.0.0.1:8000/`.

---

## Usage

### Endpoint: `GET` or `POST /api/route/`

| Field | Description |
|---|---|
| `start` | `lat,lng` (e.g. `40.7128,-74.0060`) or `City, ST` (e.g. `New York, NY`) |
| `finish` | same formats |

### Examples

```bash
# by coordinates
curl "http://127.0.0.1:8000/api/route/?start=40.7128,-74.0060&finish=34.0522,-118.2437"

# by city, state
curl "http://127.0.0.1:8000/api/route/?start=New York, NY&finish=Los Angeles, CA"

# POST with JSON
curl -X POST http://127.0.0.1:8000/api/route/ \
  -H "Content-Type: application/json" \
  -d '{"start": "Chicago, IL", "finish": "Houston, TX"}'
```

### Visual map (great for a demo)

Open in a browser:
`http://127.0.0.1:8000/map/?start=New York, NY&finish=Los Angeles, CA`

### Sample response (trimmed)

```json
{
  "start": {"query": "New York, NY", "lat": 40.71, "lng": -74.00},
  "finish": {"query": "Los Angeles, CA", "lat": 34.05, "lng": -118.24},
  "total_distance_miles": 2799.0,
  "vehicle_range_miles": 500.0,
  "fuel_mpg": 10.0,
  "total_gallons": 279.9,
  "total_fuel_cost": 695.9,
  "fuel_stops": [
    {"name": "...", "city": "Waco", "state": "NE", "price_per_gallon": 2.799,
     "mile_marker": 1229.7, "gallons": 50.0, "cost": 139.95,
     "latitude": 40.9, "longitude": -97.4, "off_route_miles": 36.9}
  ],
  "route": {"type": "LineString", "coordinates": [[-74.0, 40.7], "..."]},
  "elapsed_ms": 612.4
}
```

---

## Configuration (`fuelroute/settings.py`)

| Setting | Default | Meaning |
|---|---|---|
| `OSRM_BASE_URL` | `https://router.project-osrm.org` | Free routing API (no key) |
| `TANK_RANGE_MILES` | `500` | Vehicle range on a full tank |
| `VEHICLE_MPG` | `10` | Fuel economy |
| `ROUTE_BUFFER_MILES` | `50` | How far off the route a station may be |
| `ROUTE_CACHE_TIMEOUT` | `3600` | Seconds a route result stays cached |

---

## Assumptions

- The vehicle **starts with a full tank** (500-mile range), so `total_fuel_cost` is the cost
  of refueling along the way; a trip ≤ 500 miles needs no stop.
- Fuel is priced at the station where it's bought; the planner buys enough at each stop to
  reach the next cheaper station or the destination, favoring cheaper stations (this is
  cost-optimal).
- Stations are geocoded at **city level** (the source file has no coordinates), so a chosen
  station can sit up to `ROUTE_BUFFER_MILES` off the route — `off_route_miles` is returned
  for transparency.
- The provided dataset is sparse on the **West Coast**; routes through long station-free
  stretches return `422` with a clear message. Cross-country routes are well covered.

---

## Project structure

```
fuel-route-api/
├── manage.py
├── requirements.txt
├── data/fuel-prices-for-be-assessment.csv
├── fuelroute/                # project config (settings, urls, wsgi)
└── routes/                   # the app
    ├── models.py             # FuelStation
    ├── views.py              # RouteView, MapView
    ├── serializers.py        # request validation
    ├── services/             # routing, geocoding, spatial index, fuel planner
    ├── management/commands/  # load_fuel_data
    └── tests.py
```

A plain-language walkthrough of the design is in **CODE_OVERVIEW.md**.

---

## Troubleshooting

- **`load_fuel_data` is slow or errors on first run** — it downloads a small geocoding
  dataset once; ensure you have internet, then re-run.
- **A route returns 422 "no fuel station within 500 miles"** — the dataset has a gap on that
  corridor (common on the West Coast). Try a cross-country route, or raise
  `ROUTE_BUFFER_MILES`.
- **Routing errors / timeouts** — the public OSRM server is occasionally slow; retry. The
  base URL is configurable if you self-host OSRM.
