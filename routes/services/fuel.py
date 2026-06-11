# Cost-optimal "gas station" planning: coast to the next cheaper station buying only what's
# needed, fill up when nothing cheaper is in range. The car starts on a full tank (see README).
EPS = 1e-9


class NoFuelError(Exception):
    pass


def _stop(node, gallons, cost):
    return {
        "name": node["name"],
        "city": node["city"],
        "state": node["state"],
        "address": node["address"],
        "latitude": node.get("lat"),
        "longitude": node.get("lng"),
        "price_per_gallon": round(node["price"], 3),
        "mile_marker": round(node["mile"], 1),
        "off_route_miles": node["off_route_miles"],
        "gallons": round(gallons, 2),
        "cost": round(cost, 2),
    }


def plan_fuel_stops(stations, total_miles, tank_range, mpg):
    if total_miles <= tank_range:
        return [], 0.0

    nodes = sorted((s for s in stations if 0 < s["mile"] < total_miles), key=lambda s: s["mile"])
    nodes.append({"mile": float(total_miles), "price": 0.0})  # destination sentinel
    n = len(nodes)

    stops = []
    total_cost = 0.0
    position = 0.0
    fuel = float(tank_range)  # remaining range in miles; tank starts full
    price = float("inf")      # price at the current node (origin = free starting tank only)
    current = None

    while position < total_miles - EPS:
        in_range = [j for j in range(n) if position + EPS < nodes[j]["mile"] <= position + tank_range + EPS]
        if not in_range:
            raise NoFuelError(f"no fuel station within {tank_range:.0f} miles near mile {position:.0f}")

        cheaper = [j for j in in_range if nodes[j]["price"] < price]
        if cheaper:  # coast to the nearest cheaper station, buying only what's needed to get there
            target = min(cheaper, key=lambda j: nodes[j]["mile"])
            buy = max(0.0, (nodes[target]["mile"] - position) - fuel)
        else:  # nothing cheaper ahead: top up here and push to the cheapest station in range
            target = min(in_range, key=lambda j: nodes[j]["price"])
            buy = tank_range - fuel

        if current is not None and buy > EPS:
            gallons = buy / mpg
            total_cost += gallons * price
            stops.append(_stop(current, gallons, gallons * price))
            fuel += buy

        fuel -= nodes[target]["mile"] - position
        position = nodes[target]["mile"]
        current = nodes[target]
        price = current["price"]

    return stops, round(total_cost, 2)
