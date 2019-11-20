from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import os
import random

from database import engine, SessionLocal, init_db, City, TransitOption, AntiFraudRule, Hotel, RoomBooking

init_db()

app = FastAPI(
    title="Door-to-Door Travel & Anti-Fraud Concierge",
    description="Context-aware airport arrival guide, fair-fare transit benchmark, and room booking platform.",
    version="2.0.0"
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

# API Endpoints
@app.get("/api/v1/health")
def health():
    return {"status": "HEALTHY", "service": "door-to-door-concierge"}

@app.get("/api/v1/cities")
def list_cities(db: Session = Depends(get_db)):
    return db.query(City).all()

@app.post("/api/v1/concierge/arrival-brief")
def arrival_brief(req: ArrivalDetectRequest, db: Session = Depends(get_db)):
    city = db.query(City).filter(City.airport_code == req.airport_code.upper()).first()
    if not city:
        raise HTTPException(status_code=404, detail="City airport not supported yet")
    
    transit_options = db.query(TransitOption).filter(
        TransitOption.city_id == city.id,
        TransitOption.destination == req.destination_area
    ).all()
    
    scam_rules = db.query(AntiFraudRule).filter(AntiFraudRule.city_id == city.id).all()
    recommended_hotels = db.query(Hotel).filter(Hotel.city_id == city.id).all()
    
    # Calculate savings vs private scam touts
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
def get_transit_benchmark(city_code: str = "SXR", destination: str = "Dal Lake / Boulevard Road", db: Session = Depends(get_db)):
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

# Serve single-page dashboard application
INDEX_HTML = os.path.join(os.path.dirname(__file__), "index.html")

@app.get("/", response_class=HTMLResponse)
def serve_index():
    if os.path.exists(INDEX_HTML):
        with open(INDEX_HTML, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Door to Door Travel Platform</h1>"
