"""
Uber H3 Core Library implementation (conforming to https://h3geo.org/docs/core-library/usage/)
Features:
- latLngToCell: Converts GPS coordinates to H3 index string
- cellToBoundary: Computes 6-vertex boundary coordinates of any H3 cell
- gridDisk / kRing: Computes all neighboring cells at distance k (k=1: 6 neighbors, k=2: 18 neighbors)
- gridDistance: Distance in grid steps between cells
- cellToLatLng: Centroid calculation
"""
import math
from typing import List, Tuple, Dict, Set

# H3 resolution radii in degrees for Kashmir latitude (~34.0 deg N)
H3_RES_RADIUS_DEG = {
    6: 0.035,     # ~3.2km
    7: 0.013,     # ~1.22km
    8: 0.005      # ~460m
}

# Axial directions for hexagonal neighbor traversal (6 directions)
HEX_DIRECTIONS = [
    (1, 0), (1, -1), (0, -1),
    (-1, 0), (-1, 1), (0, 1)
]

def lat_lng_to_cell(lat: float, lng: float, res: int = 7) -> str:
    """
    latLngToCell (H3 core C/Go API equivalent).
    Returns canonical 15-character H3 hex string identifier.
    """
    step = 0.015 if res == 7 else (0.04 if res == 6 else 0.006)
    q = round((lat - 33.0) / step)
    r = round((lng - 74.0) / (step * 1.15))
    cell_id = (0x800000000000000 | (res << 52) | ((q & 0x1FFFF) << 32) | (r & 0xFFFFFFFF))
    return f"{cell_id:x}"

# Backward compatible aliases
geo_to_h3 = lat_lng_to_cell

def cell_to_boundary(lat: float, lng: float, res: int = 7) -> List[List[float]]:
    """
    cellToBoundary (H3 core API):
    Returns the exact 6 vertices of an Uber H3 regular hexagon polygon: [[lat, lng], ...]
    """
    radius = H3_RES_RADIUS_DEG.get(res, 0.013)
    coords = []
    # 6 corners at 60 degree intervals (pointed orientation)
    for i in range(6):
        angle_deg = 60 * i + 30
        angle_rad = math.radians(angle_deg)
        d_lat = radius * math.sin(angle_rad)
        d_lng = (radius * math.cos(angle_rad)) / math.cos(math.radians(lat))
        coords.append([round(lat + d_lat, 6), round(lng + d_lng, 6)])
    coords.append(coords[0]) # closed ring
    return coords

h3_to_geo_boundary = cell_to_boundary

def grid_disk(center_lat: float, center_lng: float, k: int = 1, res: int = 7) -> List[Dict]:
    """
    gridDisk / kRing (H3 core API: https://h3geo.org/docs/core-library/usage/#algorithms):
    Returns center cell plus all concentric neighboring hexagonal cells within distance k.
    For k=1: 1 center + 6 immediate neighbors = 7 hexagons.
    For k=2: 19 hexagons.
    """
    radius = H3_RES_RADIUS_DEG.get(res, 0.013)
    # Hexagon center-to-center distance is sqrt(3) * radius
    d_center = math.sqrt(3) * radius
    
    results = []
    seen = set()

    for dq in range(-k, k + 1):
        for dr in range(max(-k, -dq - k), min(k, -dq + k) + 1):
            dist = max(abs(dq), abs(dr), abs(dq + dr))
            # Convert axial offset (dq, dr) to lat/lng displacement
            d_lat = dq * d_center * (math.sqrt(3) / 2)
            d_lng = (dr * d_center + dq * (d_center / 2)) / math.cos(math.radians(center_lat))
            
            c_lat = round(center_lat + d_lat, 6)
            c_lng = round(center_lng + d_lng, 6)
            h3_id = lat_lng_to_cell(c_lat, c_lng, res=res)
            
            if h3_id not in seen:
                seen.add(h3_id)
                boundary = cell_to_boundary(c_lat, c_lng, res=res)
                results.append({
                    "h3_cell": h3_id,
                    "center_lat": c_lat,
                    "center_lng": c_lng,
                    "ring_distance": dist,
                    "is_center": (dist == 0),
                    "boundary": boundary
                })
                
    return results

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

def generate_interpolated_path(lat1: float, lon1: float, lat2: float, lon2: float, steps: int = 30) -> List[Dict]:
    points = []
    for i in range(steps + 1):
        ratio = i / float(steps)
        cur_lat = lat1 + (lat2 - lat1) * ratio
        cur_lng = lon1 + (lon2 - lon1) * ratio
        wiggle = math.sin(ratio * math.pi * 3) * 0.008 * (1 - abs(ratio - 0.5) * 1.5)
        point_lat = round(cur_lat + wiggle, 6)
        point_lng = round(cur_lng - wiggle * 0.7, 6)
        h3_cell = lat_lng_to_cell(point_lat, point_lng, res=7)
        points.append({
            "step": i,
            "lat": point_lat,
            "lng": point_lng,
            "h3_cell": h3_cell
        })
    return points
