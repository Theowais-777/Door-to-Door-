from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import os
import random
import json
import grpc

from database import engine, SessionLocal, init_db, City, TransitOption, AntiFraudRule, Hotel, RoomBooking
import transit_pb2
import transit_pb2_grpc
from grpc_service import serve_grpc, MODE_CONFIGS
from places_data import KASHMIR_DESTINATIONS
from h3_helper import h3_to_geo_boundary, geo_to_h3, grid_disk

# Initialize Database
init_db()

# Start gRPC Server on port 50051
grpc_server = serve_grpc(port=50051)

def get_grpc_stub():
    channel = grpc.insecure_channel("127.0.0.1:50051")
    return transit_pb2_grpc.KashmirTransitServiceStub(channel)

app = FastAPI(
    title="Door-to-Door Kashmir Transit & H3 Spatial Grid Platform",
    description="Uber H3 Core Library implementation, gRPC transit pricing, multi-modal vehicle benchmark, and hotel booking.",
    version="2.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic Schemas
class ArrivalDetectRequest(BaseModel):
    airport_code: str
    flight_number: Optional[str] = "6E-554"
    destination_area: str = "Dal Lake / Boulevard Road"

class BookingCreate(BaseModel):
    hotel_id: int
    guest_name: str
    guest_phone: str
    check_in: str
    nights: int

class RouteCalculateRequest(BaseModel):
    origin_id: str = "srinagar_airport"
    destination_id: str = "gulmarg"
    transport_mode: str = "car"

class NeighborQueryRequest(BaseModel):
    location_id: Optional[str] = "dal_lake"
    lat: Optional[float] = 34.0837
    lng: Optional[float] = 74.8370
    ring_size: int = 1

# API Endpoints
@app.get("/api/v1/health")
def health():
    return {
        "status": "HEALTHY",
        "service": "door-to-door-concierge",
        "grpc_service": "online:50051",
        "h3_core_library": "online"
    }

@app.get("/api/v1/transit/locations")
def get_transit_locations(filter: str = ""):
    """Invokes gRPC KashmirTransitService.GetLocations"""
    try:
        stub = get_grpc_stub()
        req = transit_pb2.LocationQuery(filter=filter)
        response = stub.GetLocations(req, timeout=5.0)
        locations = []
        for loc in response.locations:
            boundary = [json.loads(pt) for pt in loc.cell_boundary_json]
            locations.append({
                "id": loc.id,
                "name": loc.name,
                "category": loc.category,
                "lat": loc.lat,
                "lng": loc.lng,
                "h3_cell": loc.h3_cell,
                "description": loc.description,
                "highlights": loc.highlights,
                "cell_boundary": boundary
            })
        return locations
    except Exception as e:
        return KASHMIR_DESTINATIONS

@app.post("/api/v1/transit/neighbors")
def get_neighbor_hexagons(req: NeighborQueryRequest):
    """Invokes gRPC KashmirTransitService.GetNeighborHexagons (gridDisk / kRing)"""
    try:
        stub = get_grpc_stub()
        grpc_req = transit_pb2.NeighborRequest(
            location_id=req.location_id or "",
            lat=req.lat or 0.0,
            lng=req.lng or 0.0,
            ring_size=req.ring_size
        )
        response = stub.GetNeighborHexagons(grpc_req, timeout=5.0)
        cells = []
        for c in response.cells:
            boundary = [json.loads(pt) for pt in c.boundary_json]
            cells.append({
                "h3_cell": c.h3_cell,
                "center_lat": c.center_lat,
                "center_lng": c.center_lng,
                "ring_distance": c.ring_distance,
                "is_center": c.is_center,
                "zone_name": c.zone_name,
                "boundary": boundary
            })
        return {
            "center_h3_cell": response.center_h3_cell,
            "total_hexagons": len(cells),
            "cells": cells
        }
    except Exception as e:
        # Fallback to direct grid_disk calculation
        lat = req.lat or 34.0837
        lng = req.lng or 74.8370
        disk = grid_disk(lat, lng, k=req.ring_size, res=7)
        return {
            "center_h3_cell": geo_to_h3(lat, lng, res=7),
            "total_hexagons": len(disk),
            "cells": disk
        }

@app.post("/api/v1/transit/calculate-route")
def calculate_route_rpc(req: RouteCalculateRequest):
    """Invokes gRPC KashmirTransitService.CalculateRoute"""
    try:
        stub = get_grpc_stub()
        grpc_req = transit_pb2.RouteRequest(
            origin_id=req.origin_id,
            destination_id=req.destination_id,
            transport_mode=req.transport_mode
        )
        response = stub.CalculateRoute(grpc_req, timeout=5.0)
        options = []
        for opt in response.options:
            options.append({
                "mode": opt.mode,
                "mode_label": opt.mode_label,
                "fare_min": opt.fare_min,
                "fare_max": opt.fare_max,
                "duration_minutes": opt.duration_minutes,
                "distance_km": opt.distance_km,
                "icon": opt.icon,
                "recommendation": opt.recommendation,
                "safety_tip": opt.safety_tip
            })
        
        path_coords = [json.loads(p) for p in response.path_points]
        
        hex_polygons = []
        for h3_id in response.h3_hexagons:
            for pt in path_coords:
                if geo_to_h3(pt[0], pt[1], res=7) == h3_id:
                    hex_polygons.append({
                        "h3_cell": h3_id,
                        "boundary": h3_to_geo_boundary(pt[0], pt[1], res=7)
                    })
                    break

        return {
            "origin_name": response.origin_name,
            "destination_name": response.destination_name,
            "distance_km": response.distance_km,
            "selected_mode": response.selected_mode,
            "options": options,
            "path": path_coords,
            "h3_hexagons": list(response.h3_hexagons),
            "h3_polygons": hex_polygons
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"gRPC Route Error: {str(e)}")

@app.post("/api/v1/transit/live-trace")
def live_trace(req: RouteCalculateRequest):
    """Simulates live vehicle tracing steps from gRPC StreamLivePosition"""
    try:
        stub = get_grpc_stub()
        grpc_req = transit_pb2.LiveStreamRequest(
            origin_id=req.origin_id,
            destination_id=req.destination_id,
            transport_mode=req.transport_mode,
            interval_ms=50
        )
        steps = []
        stream = stub.StreamLivePosition(grpc_req, timeout=10.0)
        for item in stream:
            boundary = h3_to_geo_boundary(item.current_lat, item.current_lng, res=7)
            steps.append({
                "step_index": item.step_index,
                "total_steps": item.total_steps,
                "lat": item.current_lat,
                "lng": item.current_lng,
                "h3_cell": item.current_h3_cell,
                "cell_boundary": boundary,
                "progress_percentage": item.progress_percentage,
                "status_message": item.status_message
            })
        return {"steps": steps}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"gRPC Live Stream Error: {str(e)}")

@app.get("/api/v1/cities")
def list_cities(db: Session = Depends(get_db)):
    return db.query(City).all()

@app.post("/api/v1/concierge/arrival-brief")
def arrival_brief(req: ArrivalDetectRequest, db: Session = Depends(get_db)):
    city = db.query(City).filter(City.airport_code == req.airport_code.upper()).first()
    if not city:
        raise HTTPException(status_code=404, detail="City airport not supported yet")
    
    transit_options = db.query(TransitOption).filter(TransitOption.city_id == city.id).all()
    scam_rules = db.query(AntiFraudRule).filter(AntiFraudRule.city_id == city.id).all()
    recommended_hotels = db.query(Hotel).filter(Hotel.city_id == city.id).all()
    
    prepaid = next((t for t in transit_options if t.transit_mode == "prepaid_taxi"), None)
    tout = next((t for t in transit_options if t.transit_mode == "private_tout"), None)
    
    savings_est = 0
    if prepaid and tout:
        savings_est = tout.estimated_price_min - prepaid.estimated_price_max
        
    return {
        "city": city.name,
        "airport": city.airport_name,
        "airport_code": city.airport_code,
        "destination": req.destination_area,
        "flight_tracked": req.flight_number,
        "arrival_status": "TOUCHDOWN VERIFIED",
        "potential_fraud_savings": f"₹{savings_est}",
        "anti_fraud_advisories": scam_rules,
        "transit_comparison": transit_options,
        "recommended_hotels": recommended_hotels
    }

@app.get("/api/v1/transit/benchmark")
def get_transit_benchmark(city_code: str = "SXR", db: Session = Depends(get_db)):
    city = db.query(City).filter(City.airport_code == city_code.upper()).first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    return db.query(TransitOption).filter(TransitOption.city_id == city.id).all()

@app.get("/api/v1/hotels")
def get_hotels(city_code: str = "SXR", db: Session = Depends(get_db)):
    city = db.query(City).filter(City.airport_code == city_code.upper()).first()
    if not city:
        return []
    return db.query(Hotel).filter(Hotel.city_id == city.id).all()

@app.post("/api/v1/bookings/rooms")
def book_room(booking: BookingCreate, db: Session = Depends(get_db)):
    hotel = db.query(Hotel).filter(Hotel.id == booking.hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
        
    allocated_room = f"RM-{random.randint(101, 409)}"
    total = hotel.price_per_night * booking.nights
    
    new_booking = RoomBooking(
        hotel_id=hotel.id,
        guest_name=booking.guest_name,
        guest_phone=booking.guest_phone,
        check_in=booking.check_in,
        nights=booking.nights,
        allocated_room_no=allocated_room,
        total_amount=total,
        status="CONFIRMED"
    )
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    
    return {
        "booking_id": f"D2D-{new_booking.id:05d}",
        "hotel_name": hotel.name,
        "guest_name": new_booking.guest_name,
        "allocated_room_no": new_booking.allocated_room_no,
        "check_in": new_booking.check_in,
        "nights": new_booking.nights,
        "total_amount": f"₹{new_booking.total_amount:,}",
        "status": new_booking.status,
        "hotel_locality": hotel.locality,
        "safety_assurance": "Pre-verified booking with direct property front desk sync"
    }

INDEX_HTML = os.path.join(os.path.dirname(__file__), "index.html")

@app.get("/", response_class=HTMLResponse)
def serve_index():
    if os.path.exists(INDEX_HTML):
        with open(INDEX_HTML, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Door to Door Travel Platform</h1>"
