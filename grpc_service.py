"""
gRPC Server implementation for Kashmir Transit Service.
Implements Uber H3 Core API (https://h3geo.org/docs/core-library/usage/)
Includes:
- GetLocations
- CalculateRoute (with transport modes)
- StreamLivePosition (gRPC stream)
- GetNeighborHexagons (gridDisk / kRing neighbor cell clustering)
"""
import grpc
from concurrent import futures
import time
import json
import math

import transit_pb2
import transit_pb2_grpc
from places_data import KASHMIR_DESTINATIONS
from h3_helper import (
    haversine_distance_km, 
    generate_interpolated_path, 
    lat_lng_to_cell,
    cell_to_boundary,
    grid_disk
)

MODE_CONFIGS = {
    "two_wheeler": {
        "label": "Motorcycle / Scooter (Two-Wheeler)",
        "icon": "bike",
        "rate_per_km": 12,
        "base_fare": 80,
        "avg_speed_kmh": 38,
        "recommendation": "Great for solo travelers, winding trails, and zero traffic delay in valley bazaars.",
        "safety_tip": "Wear ISI helmets; carry warm windproof gear especially in mountain passes."
    },
    "car": {
        "label": "Sedan / Hatchback (Standard Cab)",
        "icon": "car",
        "rate_per_km": 24,
        "base_fare": 350,
        "avg_speed_kmh": 42,
        "recommendation": "Ideal for couples and families up to 4 passengers with normal luggage.",
        "safety_tip": "Check for official union prepaid sticker; insist on fixed rate slip."
    },
    "xl_car": {
        "label": "Innova / Scorpio / 4x4 SUV (XL Car)",
        "icon": "truck",
        "rate_per_km": 36,
        "base_fare": 600,
        "avg_speed_kmh": 46,
        "recommendation": "Essential for mountain terrains like Gulmarg, Tosamaidan & Doodhpathri in snow/slush.",
        "safety_tip": "Ensure 4x4 transfer chains are fitted during winter road advisory periods."
    },
    "bus": {
        "label": "JKSRTC Delux / E-Bus / Shared Coach",
        "icon": "bus",
        "rate_per_km": 4,
        "base_fare": 40,
        "avg_speed_kmh": 28,
        "recommendation": "Most economical option connecting district headquarters and major hill stations.",
        "safety_tip": "Check schedule departures at TRC (Tourist Reception Centre) Srinagar."
    }
}

class KashmirTransitServicer(transit_pb2_grpc.KashmirTransitServiceServicer):
    def GetLocations(self, request, context):
        resp = transit_pb2.LocationListResponse()
        filter_str = request.filter.lower() if request.filter else ""
        for loc in KASHMIR_DESTINATIONS:
            if not filter_str or (filter_str in loc["name"].lower() or filter_str in loc["id"].lower()):
                info = resp.locations.add()
                info.id = loc["id"]
                info.name = loc["name"]
                info.category = loc["category"]
                info.lat = loc["lat"]
                info.lng = loc["lng"]
                info.h3_cell = loc["h3_cell"]
                info.description = loc["description"]
                info.highlights = loc["highlights"]
                for pt in loc["cell_boundary"]:
                    info.cell_boundary_json.append(json.dumps(pt))
        return resp

    def CalculateRoute(self, request, context):
        origin = next((l for l in KASHMIR_DESTINATIONS if l["id"] == request.origin_id), KASHMIR_DESTINATIONS[0])
        destination = next((l for l in KASHMIR_DESTINATIONS if l["id"] == request.destination_id), KASHMIR_DESTINATIONS[1])

        distance_km = haversine_distance_km(origin["lat"], origin["lng"], destination["lat"], destination["lng"])
        road_km = max(round(distance_km * 1.35, 1), 2.0)

        resp = transit_pb2.RouteResponse()
        resp.origin_name = origin["name"]
        resp.destination_name = destination["name"]
        resp.distance_km = road_km
        resp.selected_mode = request.transport_mode or "car"

        for mode_key, cfg in MODE_CONFIGS.items():
            opt = resp.options.add()
            opt.mode = mode_key
            opt.mode_label = cfg["label"]
            opt.icon = cfg["icon"]
            opt.distance_km = road_km
            
            calc_fare = cfg["base_fare"] + (road_km * cfg["rate_per_km"])
            opt.fare_min = int(round(calc_fare * 0.95))
            opt.fare_max = int(round(calc_fare * 1.15))
            
            duration_hr = road_km / cfg["avg_speed_kmh"]
            opt.duration_minutes = max(int(round(duration_hr * 60)), 10)
            opt.recommendation = cfg["recommendation"]
            opt.safety_tip = cfg["safety_tip"]

        path_data = generate_interpolated_path(origin["lat"], origin["lng"], destination["lat"], destination["lng"], steps=30)
        hex_set = set()
        for p in path_data:
            resp.path_points.append(json.dumps([p["lat"], p["lng"]]))
            hex_set.add(p["h3_cell"])
        
        for h in hex_set:
            resp.h3_hexagons.append(h)

        return resp

    def StreamLivePosition(self, request, context):
        origin = next((l for l in KASHMIR_DESTINATIONS if l["id"] == request.origin_id), KASHMIR_DESTINATIONS[0])
        destination = next((l for l in KASHMIR_DESTINATIONS if l["id"] == request.destination_id), KASHMIR_DESTINATIONS[1])
        steps = 20
        path = generate_interpolated_path(origin["lat"], origin["lng"], destination["lat"], destination["lng"], steps=steps)
        interval = (request.interval_ms or 500) / 1000.0

        for idx, pt in enumerate(path):
            resp = transit_pb2.LivePositionResponse()
            resp.step_index = idx
            resp.total_steps = steps
            resp.current_lat = pt["lat"]
            resp.current_lng = pt["lng"]
            resp.current_h3_cell = pt["h3_cell"]
            resp.progress_percentage = round((idx / float(steps)) * 100.0, 1)
            resp.status_message = f"Tracing live transit ({request.transport_mode}) crossing H3 cell {pt['h3_cell']}..."
            yield resp
            time.sleep(interval)

    def GetNeighborHexagons(self, request, context):
        """
        Uber H3 gridDisk / kRing implementation.
        Computes all adjacent hexagonal cells around a selected location or lat/lng.
        """
        target_lat = request.lat
        target_lng = request.lng
        loc_name = "Selected Coordinate"

        if request.location_id:
            loc = next((l for l in KASHMIR_DESTINATIONS if l["id"] == request.location_id), None)
            if loc:
                target_lat = loc["lat"]
                target_lng = loc["lng"]
                loc_name = loc["name"]

        ring_k = request.ring_size if request.ring_size > 0 else 1
        ring_cells = grid_disk(target_lat, target_lng, k=ring_k, res=7)

        resp = transit_pb2.NeighborResponse()
        resp.center_h3_cell = lat_lng_to_cell(target_lat, target_lng, res=7)

        for cell in ring_cells:
            c_info = resp.cells.add()
            c_info.h3_cell = cell["h3_cell"]
            c_info.center_lat = cell["center_lat"]
            c_info.center_lng = cell["center_lng"]
            c_info.ring_distance = cell["ring_distance"]
            c_info.is_center = cell["is_center"]
            if cell["is_center"]:
                c_info.zone_name = f"Center: {loc_name}"
            else:
                c_info.zone_name = f"Hex Neighbor (Ring {cell['ring_distance']})"
            for pt in cell["boundary"]:
                c_info.boundary_json.append(json.dumps(pt))

        return resp

def serve_grpc(port=50051):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    transit_pb2_grpc.add_KashmirTransitServiceServicer_to_server(KashmirTransitServicer(), server)
    server.add_insecure_port(f"127.0.0.1:{port}")
    server.start()
    print(f"gRPC KashmirTransitService running on 127.0.0.1:{port}")
    return server

if __name__ == "__main__":
    s = serve_grpc(50051)
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        s.stop(0)
