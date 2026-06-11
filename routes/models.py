from django.db import models


class FuelStation(models.Model):
    """A truck-stop fuel price, geocoded to a city-level coordinate."""

    opis_id = models.IntegerField(db_index=True)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=128)
    state = models.CharField(max_length=8)
    rack_id = models.IntegerField(null=True, blank=True)
    retail_price = models.DecimalField(max_digits=8, decimal_places=5)
    latitude = models.FloatField()
    longitude = models.FloatField()

    class Meta:
        indexes = [models.Index(fields=["state"])]

    def __str__(self):
        return f"{self.name} ({self.city}, {self.state})"
