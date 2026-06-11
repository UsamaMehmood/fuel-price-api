from django.test import SimpleTestCase

from routes.serializers import RouteRequestSerializer
from routes.services.fuel import NoFuelError, plan_fuel_stops


def station(mile, price):
    return {
        "name": f"Stop@{mile}", "city": "X", "state": "XX", "address": "",
        "price": price, "mile": mile, "off_route_miles": 1.0,
    }


class FuelPlanTests(SimpleTestCase):
    def test_trip_within_range_needs_no_stop(self):
        stops, cost = plan_fuel_stops([station(100, 3.0)], total_miles=400, tank_range=500, mpg=10)
        self.assertEqual(stops, [])
        self.assertEqual(cost, 0.0)

    def test_picks_cheapest_reachable_station(self):
        stations = [station(300, 4.0), station(450, 2.0), station(700, 5.0)]
        stops, cost = plan_fuel_stops(stations, total_miles=900, tank_range=500, mpg=10)
        self.assertEqual(len(stops), 1)
        self.assertEqual(stops[0]["mile_marker"], 450)
        # buy 400 miles of fuel (40 gal) at $2.00 -> $80
        self.assertEqual(cost, 80.0)

    def test_raises_when_gap_exceeds_range(self):
        with self.assertRaises(NoFuelError):
            plan_fuel_stops([station(100, 3.0)], total_miles=1200, tank_range=500, mpg=10)

    def test_look_ahead_is_cost_optimal(self):
        # Coast to mile 100 on the free tank, top up just enough there ($3) to reach the
        # cheap station at mile 600 ($1), then fill there to finish.
        stations = [station(100, 3.0), station(200, 5.0), station(600, 1.0)]
        stops, cost = plan_fuel_stops(stations, total_miles=900, tank_range=500, mpg=10)
        self.assertEqual([s["mile_marker"] for s in stops], [100, 600])
        self.assertEqual([s["gallons"] for s in stops], [10.0, 30.0])
        self.assertEqual(cost, 60.0)


class RouteRequestSerializerTests(SimpleTestCase):
    def test_resolves_us_coordinates(self):
        s = RouteRequestSerializer(data={"start": "40.71,-74.00", "finish": "34.05,-118.24"})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data["start_point"]["lat"], 40.71)

    def test_rejects_location_outside_usa(self):
        s = RouteRequestSerializer(data={"start": "51.5074,-0.1278", "finish": "34.05,-118.24"})
        self.assertFalse(s.is_valid())
        self.assertIn("start", s.errors)

    def test_requires_both_fields(self):
        s = RouteRequestSerializer(data={"start": "40.71,-74.00"})
        self.assertFalse(s.is_valid())
        self.assertIn("finish", s.errors)
