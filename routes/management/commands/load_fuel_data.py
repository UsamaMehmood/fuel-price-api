import csv
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand

from routes.models import FuelStation
from routes.services.geocode import geocode_city_state
from routes.services.stations import reset_index

PRICE_QUANT = Decimal("0.00001")


class Command(BaseCommand):
    help = "Load and geocode the fuel-price CSV into the database (run once)."

    def add_arguments(self, parser):
        parser.add_argument("--path", default=str(settings.FUEL_CSV_PATH))

    def handle(self, *args, **options):
        FuelStation.objects.all().delete()

        stations, skipped = [], 0
        with open(options["path"], newline="", encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                coords = geocode_city_state(row["City"], row["State"])
                if not coords:  # mostly non-US rows we can't place
                    skipped += 1
                    continue
                stations.append(FuelStation(
                    opis_id=int(row["OPIS Truckstop ID"]),
                    name=row["Truckstop Name"].strip(),
                    address=row["Address"].strip(),
                    city=row["City"].strip(),
                    state=row["State"].strip().upper(),
                    rack_id=int(row["Rack ID"]) if row["Rack ID"].strip() else None,
                    retail_price=Decimal(row["Retail Price"]).quantize(PRICE_QUANT),
                    latitude=coords[0],
                    longitude=coords[1],
                ))

        FuelStation.objects.bulk_create(stations, batch_size=1000)
        reset_index()
        self.stdout.write(self.style.SUCCESS(
            f"Loaded {len(stations)} stations, skipped {skipped} (no US city match)."
        ))
