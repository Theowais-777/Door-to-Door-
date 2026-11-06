# Door-to-Door Travel ('19 — '20)

> **High-Performance Travel Concierge & Booking Engine**  
> Built to support over 100,000 monthly transactions with dynamic room allocation, interactive transit benchmarking, and proactive arrival anti-fraud assistance.

---

## ✈️ Overview

When travelers land at an airport, they often face predatory taxi touts, inflated tourist prices, and fake booking agents. **Door-to-Door Travel** acts as an intelligent arrival concierge and hyper-plan navigator:

1. **Airport Arrival Detection & Flight Deck**: Instantly delivers a tailored briefing upon flight landing.
2. **Anti-Fraud Shield**: Real-time warning benchmarks comparing regulated prepaid taxi counters vs. predatory tout rates to safeguard travelers from scams.
3. **Room Allocation & Booking Engine**: Interactive hotel discovery and room allocation prototypes with instant confirmation (`RM-xxx`) and status tracking.
4. **Interactive Hyper-Plan**: Step-by-step route and itinerary recommendations for scenic lakefronts, hill stations, and heritage centers.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.11, [FastAPI](https://fastapi.tiangolo.com/), Pydantic v2
- **Database / ORM**: SQLite / PostgreSQL via [SQLAlchemy](https://www.sqlalchemy.org/)
- **Frontend**: React 18, Tailwind CSS, Lucide Icons
- **Deployment**: Google Cloud Run & Docker ready

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Application
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

### 3. Access the Platform
- **Interactive Web App**: [http://localhost:8080](http://localhost:8080)
- **Interactive API Documentation (Swagger)**: [http://localhost:8080/docs](http://localhost:8080/docs)
- **ReDoc**: [http://localhost:8080/redoc](http://localhost:8080/redoc)

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | System health check & version info |
| `POST` | `/api/v1/concierge/arrival-brief` | Trigger arrival briefing with alerts, transit rates, & hotels |
| `GET` | `/api/v1/transit/benchmark` | Compare regulated taxi rates with predatory street estimates |
| `GET` | `/api/v1/hotels` | Search verified hotels by city code |
| `POST` | `/api/v1/bookings/rooms` | Book room and auto-allocate room number |

---

## 🐳 Docker / Cloud Run

```bash
docker build -t door-to-door .
docker run -p 8080:8080 door-to-door
```

---

## 📄 License & Attribution
Authored by **Owais Khan** ([Theowais-777](https://github.com/Theowais-777))

