import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "doortodoor.db")
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class City(Base):
    __tablename__ = "cities"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    country = Column(String(100), default="India")
    airport_code = Column(String(10), unique=True, index=True)
    airport_name = Column(String(200), nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)

class TransitOption(Base):
    __tablename__ = "transit_options"
    id = Column(Integer, primary_key=True, index=True)
    city_id = Column(Integer, nullable=False)
    origin = Column(String(200), nullable=False)
    destination = Column(String(200), nullable=False)
    transit_mode = Column(String(50), nullable=False) # "prepaid_taxi", "app_cab", "airport_bus", "private_tout"
    title = Column(String(200), nullable=False)
    estimated_price_min = Column(Integer, nullable=False)
    estimated_price_max = Column(Integer, nullable=False)
    travel_time_mins = Column(Integer, nullable=False)
    recommended = Column(Boolean, default=False)
    safety_rating = Column(Float, default=4.5)
    fraud_risk_level = Column(String(20), default="LOW") # "LOW", "MEDIUM", "CRITICAL"
    advice = Column(Text, nullable=False)

class AntiFraudRule(Base):
    __tablename__ = "antifraud_rules"
    id = Column(Integer, primary_key=True, index=True)
    city_id = Column(Integer, nullable=False)
    scam_title = Column(String(200), nullable=False)
    scam_category = Column(String(100), nullable=False) # "airport_taxi", "houseboat_broker", "shopping_commission"
    description = Column(Text, nullable=False)
    prevention_guide = Column(Text, nullable=False)
    official_helpline = Column(String(50), default="112")

class Hotel(Base):
    __tablename__ = "hotels"
    id = Column(Integer, primary_key=True, index=True)
    city_id = Column(Integer, nullable=False)
    name = Column(String(200), nullable=False)
    category = Column(String(50), nullable=False) # "Luxury Houseboat", "Heritage Resort", "Boutique Hotel"
    locality = Column(String(200), nullable=False)
    price_per_night = Column(Integer, nullable=False)
    rating = Column(Float, default=4.8)
    image_url = Column(String(500))
    amenities = Column(String(300))
    verified_badge = Column(Boolean, default=True)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    google_id = Column(String(100), unique=True, index=True, nullable=True)
    email = Column(String(150), unique=True, index=True, nullable=False)
    name = Column(String(150), nullable=False)
    picture = Column(String(500), nullable=True)
    provider = Column(String(50), default="google") # "google", "local"
    role = Column(String(20), default="tourist") # "tourist", "verified_driver", "admin"
    created_at = Column(DateTime, default=datetime.utcnow)

class RoomBooking(Base):
    __tablename__ = "room_bookings"
    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=True)
    guest_name = Column(String(100), nullable=False)
    guest_phone = Column(String(30), nullable=False)
    check_in = Column(String(30), nullable=False)
    nights = Column(Integer, default=1)
    allocated_room_no = Column(String(20), nullable=False)
    total_amount = Column(Integer, nullable=False)
    status = Column(String(30), default="CONFIRMED")
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Seed Srinagar if not present
    if not db.query(City).filter(City.airport_code == "SXR").first():
        srinagar = City(
            name="Srinagar & Kashmir Valley",
            state="Jammu and Kashmir",
            country="India",
            airport_code="SXR",
            airport_name="Sheikh ul-Alam International Airport (Srinagar)",
            lat=33.9871,
            lng=74.7741
        )
        db.add(srinagar)
        db.commit()
        db.refresh(srinagar)
        
        # Anti-fraud rules
        rules = [
            AntiFraudRule(
                city_id=srinagar.id,
                scam_title="Prepaid Airport Taxi Counter vs Touting Drivers",
                scam_category="airport_taxi",
                description="Unregistered drivers linger outside arrival doors claiming app-cabs/taxis are not available and demand ₹2,500 - ₹3,500 for Dal Lake.",
                prevention_guide="Always walk directly to the official J&K Tourism / Traffic Police Prepaid Taxi Booth right inside the terminal gate. The government regulated fare to Boulevard/Dal Lake is fixed around ₹800 - ₹950.",
                official_helpline="Tourist Police Srinagar: +91-194-2452224 / 112"
            ),
            AntiFraudRule(
                city_id=srinagar.id,
                scam_title="Offbeat Valley Touts (Arizal, Sukhnag, Doodhpathri)",
                scam_category="valley_tout",
                description="Unregulated agents at highway crossings claim high-altitude roads to Doodhpathri, Arizal, or Tosamaidan are blocked and force private overpriced escorts.",
                prevention_guide="Verify live transit via official H3 route benchmarks or Tourist Reception Centre Srinagar. Local 4x4 and registered union cabs have fixed rate slips.",
                official_helpline="Budgam District Control: +91-1951-255203 / 112"
            ),
            AntiFraudRule(
                city_id=srinagar.id,
                scam_title="Fake Houseboat 'Closed or Inaccessible' Rumors",
                scam_category="houseboat_broker",
                description="Taxi drivers falsely tell tourists their booked houseboat is submerged, inaccessible, or on strike to redirect them to high-commission unregistered houseboats.",
                prevention_guide="Call your houseboat owner/resort reception directly prior to departure. Never alter your destination based on a driver's unsolicited advice.",
                official_helpline="Tourist Police: 112"
            ),
            AntiFraudRule(
                city_id=srinagar.id,
                scam_title="Pashmina & Saffron Middleman Commissions",
                scam_category="shopping_commission",
                description="Drivers offer 'free shortcuts' to show you authentic Kashmiri saffron and shawls at factories where rates are inflated 300% to pay driver commissions.",
                prevention_guide="Buy GI-tagged Kashmiri Saffron and Pashmina exclusively from government-certified J&K Handloom outlets or direct Kashmir Craft Emporiums.",
                official_helpline="Craft Verification: +91-194-2476073"
            )
        ]
        db.add_all(rules)
        
        # Transit options
        transit = [
            TransitOption(
                city_id=srinagar.id,
                origin="Srinagar Airport (SXR)",
                destination="Dal Lake / Boulevard Road",
                transit_mode="prepaid_taxi",
                title="Official Airport Prepaid Taxi (Govt Regulated)",
                estimated_price_min=850,
                estimated_price_max=950,
                travel_time_mins=35,
                recommended=True,
                safety_rating=4.9,
                fraud_risk_level="LOW",
                advice="Book at Counter #2 inside arrival hall. Zero negotiation needed, police verified receipt."
            ),
            TransitOption(
                city_id=srinagar.id,
                origin="Srinagar Airport (SXR)",
                destination="Dal Lake / Boulevard Road",
                transit_mode="app_cab",
                title="Ola / Local App Verified Cab",
                estimated_price_min=750,
                estimated_price_max=1100,
                travel_time_mins=35,
                recommended=True,
                safety_rating=4.7,
                fraud_risk_level="LOW",
                advice="App operates from designated pickup bay. Ensure OTP matches driver screen before boarding."
            ),
            TransitOption(
                city_id=srinagar.id,
                origin="Srinagar Airport (SXR)",
                destination="Dal Lake / Boulevard Road",
                transit_mode="private_tout",
                title="Unverified Private Touts (Exit Walkway)",
                estimated_price_min=2200,
                estimated_price_max=3500,
                travel_time_mins=45,
                recommended=False,
                safety_rating=2.1,
                fraud_risk_level="CRITICAL",
                advice="HIGH RISK: Drivers will divert via commission shops and charge 3x official rate. Decline politely and use prepaid."
            ),
            TransitOption(
                city_id=srinagar.id,
                origin="Srinagar Airport (SXR)",
                destination="Gulmarg Hill Resort",
                transit_mode="prepaid_taxi",
                title="Official 4x4 / Sedan Transit to Gulmarg",
                estimated_price_min=2400,
                estimated_price_max=2800,
                travel_time_mins=90,
                recommended=True,
                safety_rating=4.8,
                fraud_risk_level="LOW",
                advice="In winter, chained vehicles are arranged from Tangmarg. Official taxi union rate applies."
            ),
            TransitOption(
                city_id=srinagar.id,
                origin="Srinagar Airport (SXR)",
                destination="Doodhpathri (Valley of Milk)",
                transit_mode="prepaid_taxi",
                title="Official Taxi to Doodhpathri Meadow",
                estimated_price_min=1800,
                estimated_price_max=2200,
                travel_time_mins=70,
                recommended=True,
                safety_rating=4.8,
                fraud_risk_level="LOW",
                advice="Scenic drive via Khansahib. Pre-fixed rate through Budgam taxi union."
            ),
            TransitOption(
                city_id=srinagar.id,
                origin="Srinagar Airport (SXR)",
                destination="Arizal & Sukhnag Cascades",
                transit_mode="prepaid_taxi",
                title="Direct Cab to Arizal / Sukhnag Waterfalls",
                estimated_price_min=1700,
                estimated_price_max=2100,
                travel_time_mins=65,
                recommended=True,
                safety_rating=4.7,
                fraud_risk_level="LOW",
                advice="Follow Beerwah-Khag route. Excellent camping and trout angling trail."
            )
        ]
        db.add_all(transit)
        
        # Hotels
        hotels = [
            Hotel(
                city_id=srinagar.id,
                name="Mascot Heritage Houseboats",
                category="Luxury Houseboat",
                locality="Nigeen Lake (Peaceful Zone), Srinagar",
                price_per_night=6500,
                rating=4.9,
                image_url="https://images.unsplash.com/photo-1595846519845-68e298c2edd8?w=800",
                amenities="Shikara Transfers, Traditional Walnut Wood Carvings, Heated Bedrooms, Wazwan Dining",
                verified_badge=True
            ),
            Hotel(
                city_id=srinagar.id,
                name="The Lalit Grand Palace",
                category="Heritage Palace Resort",
                locality="Gupkar Road, Dal Lake, Srinagar",
                price_per_night=18500,
                rating=4.9,
                image_url="https://images.unsplash.com/photo-1566073771259-6a8506099945?w=800",
                amenities="Former Royal Residence, Chinar Gardens, Spa, Indoor Heated Pool, Mountain Views",
                verified_badge=True
            ),
            Hotel(
                city_id=srinagar.id,
                name="Vivanta Dal View by Taj",
                category="5-Star Luxury Resort",
                locality="Kralsangri, Brein, Srinagar",
                price_per_night=16000,
                rating=4.8,
                image_url="https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=800",
                amenities="Panoramic Dal Lake Views, Infinity Pool, Multi-Cuisine Restaurants, Valley Suites",
                verified_badge=True
            ),
            Hotel(
                city_id=srinagar.id,
                name="Nedou's Heritage Hotel",
                category="Heritage Boutique Hotel",
                locality="Maulana Azad Road, Srinagar",
                price_per_night=4200,
                rating=4.6,
                image_url="https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=800",
                amenities="Founded 1888, Lush Lawns, Central City Access, Authentic Kashmiri Hospitality",
                verified_badge=True
            )
        ]
        db.add_all(hotels)
        db.commit()
    db.close()

