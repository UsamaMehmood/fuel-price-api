from shapely import LineString, Point, STRtree

# rough degrees-per-mile; good enough for a "near the route" buffer at US latitudes
DEGREES_PER_MILE = 1 / 69.0

_index = None


class StationIndex:
    def __init__(self, rows):
        # rows: (lat, lng, price, id, name, city, state, address); shapely points are (x=lng, y=lat)
        self.rows = rows
        self.points = [Point(r[1], r[0]) for r in rows]
        self.tree = STRtree(self.points)

    def __len__(self):
        return len(self.points)

    def along_route(self, path, total_miles, buffer_miles):
        line = LineString([(lng, lat) for lat, lng in path])
        nearby = self.tree.query(line, predicate="dwithin", distance=buffer_miles * DEGREES_PER_MILE)

        stations = []
        for i in nearby:
            lat, lng, price, sid, name, city, state, address = self.rows[i]
            point = self.points[i]
            stations.append({
                "id": sid, "name": name, "city": city, "state": state, "address": address,
                "lat": lat, "lng": lng, "price": float(price),
                "mile": round(line.project(point, normalized=True) * total_miles, 1),
                "off_route_miles": round(line.distance(point) / DEGREES_PER_MILE, 1),
            })
        stations.sort(key=lambda s: s["mile"])
        return stations


def get_index():
    global _index
    if _index is None:
        from routes.models import FuelStation

        _index = StationIndex(list(FuelStation.objects.values_list(
            "latitude", "longitude", "retail_price", "id", "name", "city", "state", "address")))
    return _index


def reset_index():
    global _index
    _index = None
