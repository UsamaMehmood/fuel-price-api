from rest_framework import serializers

from .services.geocode import geocode_place, in_usa


class RouteRequestSerializer(serializers.Serializer):
    """Validates the request and resolves start/finish into US coordinates."""

    start = serializers.CharField(help_text="'lat,lng' or 'City, ST'")
    finish = serializers.CharField(help_text="'lat,lng' or 'City, ST'")

    def validate(self, attrs):
        attrs["start_point"] = self._resolve("start", attrs["start"])
        attrs["finish_point"] = self._resolve("finish", attrs["finish"])
        return attrs

    @staticmethod
    def _resolve(field, value):
        coords = geocode_place(value)
        if coords is None:
            raise serializers.ValidationError(
                {field: "Could not resolve location. Use 'lat,lng' or 'City, ST'."}
            )
        if not in_usa(*coords):
            raise serializers.ValidationError({field: "Location must be within the contiguous USA."})
        return {"query": value, "lat": coords[0], "lng": coords[1]}
