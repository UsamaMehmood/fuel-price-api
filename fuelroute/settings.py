from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Dev key — fine for a local assessment; swap for an env var in production.
SECRET_KEY = "dev-insecure-key-change-me"
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "rest_framework",
    "routes",
]

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "fuelroute.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": []},
    },
]

WSGI_APPLICATION = "fuelroute.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# In-memory cache so repeated routes return instantly and skip the OSRM call.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_AUTHENTICATION_CLASSES": [],  # public API; avoids pulling in django.contrib.auth
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
}

STATIC_URL = "static/"
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Domain settings for the routing/fuel logic.
OSRM_BASE_URL = "https://router.project-osrm.org"
OSRM_TIMEOUT = 10
TANK_RANGE_MILES = 500.0
VEHICLE_MPG = 10.0
ROUTE_BUFFER_MILES = 50.0  # how far off the route a station can be (city-level geocoding needs slack)
ROUTE_CACHE_TIMEOUT = 60 * 60
FUEL_CSV_PATH = BASE_DIR / "data" / "fuel-prices-for-be-assessment.csv"
