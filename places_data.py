"""
Complete database of Kashmir tourist locations with GPS coordinates,
Uber H3 cell IDs, descriptions, and recommended transport options.
"""
from h3_helper import geo_to_h3, h3_to_geo_boundary
import json

KASHMIR_DESTINATIONS = [
    {
        "id": "srinagar_airport",
        "name": "Sheikh ul-Alam Airport (Srinagar)",
        "category": "Airport / Transit Hub",
        "lat": 33.9871,
        "lng": 74.7741,
        "description": "Primary international gateway to Kashmir valley, Badgam district.",
        "highlights": "Official prepaid taxi booth, security check counter, rental cabs"
    },
    {
        "id": "dal_lake",
        "name": "Dal Lake & Boulevard Road",
        "category": "Lake / Heritage",
        "lat": 34.0837,
        "lng": 74.8370,
        "description": "The jewel of Srinagar with wooden houseboats, shikara rides, and floating gardens.",
        "highlights": "Ghats 1 to 18, Char Chinar, Hazratbal, floating vegetable market"
    },
    {
        "id": "mughal_gardens",
        "name": "Mughal Gardens (Nishat & Shalimar)",
        "category": "Heritage Gardens",
        "lat": 34.1250,
        "lng": 74.8722,
        "description": "Terraced Persian-style pleasure gardens with fountains and historic chinar trees.",
        "highlights": "Nishat Bagh, Shalimar Bagh, Chashme Shahi, Pari Mahal"
    },
    {
        "id": "gulmarg",
        "name": "Gulmarg Meadow of Flowers",
        "category": "Alpine Resort / Winter Sports",
        "lat": 34.0484,
        "lng": 74.3805,
        "description": "World-famous ski destination, Gondola cable car up to Apharwat Peak at 4,390m.",
        "highlights": "Gulmarg Gondola (Phase 1 & 2), St Mary's Church, Strawberry Valley"
    },
    {
        "id": "doodhpathri",
        "name": "Doodhpathri (Valley of Milk)",
        "category": "Alpine Meadow / Eco-tourism",
        "lat": 33.8732,
        "lng": 74.5678,
        "description": "Pristine meadow in Budgam with frothy Shaliganga river waters resembling milk.",
        "highlights": "Parihas, Dikshal meadow, pony trekking, serene pine forests"
    },
    {
        "id": "arizal",
        "name": "Arizal (Gateway to Sukhnag)",
        "category": "Offbeat Valley / Budgam",
        "lat": 33.9531,
        "lng": 74.5822,
        "description": "Picturesque village enclave along the Sukhnag river, gateway to untamed cascades.",
        "highlights": "Trout angling, riverside camping, walnut groves, village trails"
    },
    {
        "id": "sukhnag",
        "name": "Sukhnag Waterfalls & Springs",
        "category": "Cascades / Nature Trail",
        "lat": 33.9210,
        "lng": 74.5240,
        "description": "Famous Sukhnag spring and roaring waterfall feeding Budgam canal networks.",
        "highlights": "Trekking trail, Sukhnag stream, crystal water spring, alpine views"
    },
    {
        "id": "khag",
        "name": "Khag Tehsil & Hot Springs",
        "category": "Historic Sub-Alpine",
        "lat": 34.0042,
        "lng": 74.5310,
        "description": "Ancient scenic enclave surrounded by Pir Panjal peaks, Gandhak nag mineral waters.",
        "highlights": "Gandhak Nag (sulfur springs), Naranag Khag, apple orchards"
    },
    {
        "id": "tosamaidan",
        "name": "Tosamaidan Great Meadow",
        "category": "High-Altitude Meadow",
        "lat": 33.9250,
        "lng": 74.4520,
        "description": "Expansive alpine pasture bordered by dense deodars, historically used by Mughals.",
        "highlights": "Camp sites, nomad trails, wilderness hiking, high-plateau panorama"
    },
    {
        "id": "pahalgam",
        "name": "Pahalgam (Valley of Shepherds)",
        "category": "River Valley / Hill Station",
        "lat": 34.0150,
        "lng": 75.3180,
        "description": "Lidder river basin, base camp for the Amarnath Yatra and Betab/Aru valleys.",
        "highlights": "Betaab Valley, Aru Valley, Baisaran mini-Switzerland, Lidder rafting"
    },
    {
        "id": "sonamarg",
        "name": "Sonamarg (Meadow of Gold)",
        "category": "Glacier / Himalayan Pass",
        "lat": 34.3020,
        "lng": 75.2930,
        "description": "Sindh river gorge on the Srinagar-Leh highway, doorway to Thajiwas Glacier.",
        "highlights": "Thajiwas Glacier, Zero Point, Zoji La Pass, trout fishing"
    },
    {
        "id": "aharbal",
        "name": "Aharbal Waterfalls (Niagara of Kashmir)",
        "category": "Waterfalls / Kulgam",
        "lat": 33.6480,
        "lng": 74.7830,
        "description": "Dramatic 25-meter plunge of the Veshav river amid rugged pine gorge cliffs.",
        "highlights": "Aharbal Falls view deck, Kungwattan meadow, Kousarnag alpine trek"
    }
]

# Enrich each destination with H3 cell and boundary polygon
for loc in KASHMIR_DESTINATIONS:
    cell = geo_to_h3(loc["lat"], loc["lng"], res=7)
    boundary = h3_to_geo_boundary(loc["lat"], loc["lng"], res=7)
    loc["h3_cell"] = cell
    loc["cell_boundary"] = boundary

