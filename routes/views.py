import time

from django.conf import settings
from django.core.cache import cache
from django.shortcuts import render
from django.views import View
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import RouteRequestSerializer
from .services import routing
from .services import stations as station_index
from .services.fuel import NoFuelError, plan_fuel_stops


class RouteView(APIView):
    """Route + optimal fuel stops between two US locations."""

    def get(self, request):
        return self._handle(request.query_params)

    def post(self, request):
        return self._handle(request.data)

    def _handle(self, params):
        serializer = RouteRequestSerializer(data=params)
        serializer.is_valid(raise_exception=True)
        start = serializer.validated_data["start_point"]
        finish = serializer.validated_data["finish_point"]

        # Cache by rounded coordinates so identical trips skip the OSRM call entirely.
        cache_key = f"route:{start['lat']:.4f},{start['lng']:.4f}:{finish['lat']:.4f},{finish['lng']:.4f}"
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        started = time.perf_counter()
        try:
            path, distance = routing.get_route((start["lat"], start["lng"]), (finish["lat"], finish["lng"]))
        except routing.RoutingError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        candidates = station_index.get_index().along_route(path, distance, settings.ROUTE_BUFFER_MILES)
        try:
            stops, total_cost = plan_fuel_stops(
                candidates, distance, settings.TANK_RANGE_MILES, settings.VEHICLE_MPG
            )
        except NoFuelError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        payload = {
            "start": start,
            "finish": finish,
            "total_distance_miles": round(distance, 1),
            "vehicle_range_miles": settings.TANK_RANGE_MILES,
            "fuel_mpg": settings.VEHICLE_MPG,
            "total_gallons": round(distance / settings.VEHICLE_MPG, 2),
            "total_fuel_cost": total_cost,
            "fuel_stops": stops,
            "route": {"type": "LineString", "coordinates": [[lng, lat] for lat, lng in path]},
            "map_url": f"/map/?start={start['query']}&finish={finish['query']}",
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 1),
        }
        cache.set(cache_key, payload, settings.ROUTE_CACHE_TIMEOUT)
        return Response(payload)


class MapView(View):
    """Leaflet page that calls the API and draws the route + fuel stops (for the demo)."""

    def get(self, request):
        return render(
            request,
            "map.html",
            {"start": request.GET.get("start", ""), "finish": request.GET.get("finish", "")},
        )
