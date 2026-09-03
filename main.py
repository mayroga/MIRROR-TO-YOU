from fastapi import FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import os

app = FastAPI(
    title="MIRROR TO YOU — The Private Life Concierge",
    description="Backend API and Static Server for MIRROR TO YOU private platform.",
    version="1.0.0"
)

# Mount static directory for frontend assets (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# ==========================================
# PYDANTIC MODELS (Data Validation & Schemas)
# ==========================================

class ConciergeRequestInput(BaseModel):
    query: str = Field(..., min_length=3, description="Natural language request from client")
    category: Optional[str] = Field("General Directive", description="Category of request")
    client_id: Optional[str] = Field("client_alpha_01", description="Identifier of the client")

class ConciergeRequestResponse(BaseModel):
    request_id: str
    status: str
    category: str
    description: str
    timestamp: str
    assigned_desk: str
    message: str

class UserProfileModel(BaseModel):
    client_id: str = "client_alpha_01"
    full_name: str = "Maykel Rodríguez García"
    tier: str = "Principal / Elite"
    preferred_language: str = "English"
    secondary_language: str = "Spanish"
    dietary_preferences: List[str] = ["Organic Wellness", "Gluten-Free Selections"]
    travel_preferences: Dict[str, Any] = {
        "max_connections": 1,
        "preferred_cabin": "First / Private Suite",
        "preferred_hotel_types": ["Boutique Luxury", "Private Estates"]
    }
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class ExperienceItem(BaseModel):
    id: str
    title: str
    category: str
    description: str
    status: str
    highlight: str

# ==========================================
# IN-MEMORY DEMO STORAGE (Prepared for DB)
# ==========================================

DEMO_REQUESTS = [
    {
        "request_id": "REQ-8942",
        "status": "IN PROGRESS",
        "category": "Travel & Logistics",
        "description": "Lake Como vehicle transfer child safety profile adjustments updated.",
        "timestamp": "2026-09-02T08:32:00Z",
        "assigned_desk": "Desk Alpha"
    },
    {
        "request_id": "REQ-8910",
        "status": "CONFIRMED",
        "category": "Bespoke Experience",
        "description": "Uffizi Gallery After-Hours Private Access (Florence)",
        "timestamp": "2026-08-28T14:15:00Z",
        "assigned_desk": "Desk Curation"
    }
]

DEMO_PROFILE = {
    "client_id": "client_alpha_01",
    "full_name": "Maykel Rodríguez García",
    "tier": "Principal / Elite",
    "preferred_language": "English",
    "secondary_language": "Spanish",
    "dietary_preferences": ["Organic Wellness", "Gluten-Free Selections"],
    "travel_preferences": {
        "max_connections": 1,
        "preferred_cabin": "First / Private Suite",
        "preferred_hotel_types": ["Boutique Luxury", "Private Estates"]
    },
    "updated_at": datetime.utcnow().isoformat()
}

DEMO_EXPERIENCES = [
    {
        "id": "EXP-01",
        "title": "Private Riva Yacht Excursion",
        "category": "Private Yacht",
        "description": "Exclusive navigation across private waters with dedicated crew and sommelier service.",
        "status": "Available on Request",
        "highlight": "Lake Como / Mediterranean"
    },
    {
        "id": "EXP-02",
        "title": "Private Michelin-Tier Chef Service",
        "category": "Private Chef",
        "description": "Tailored culinary artistry delivered at private residence or estate location.",
        "status": "Available on Request",
        "highlight": "Customized Menu"
    },
    {
        "id": "EXP-03",
        "title": "Historical Estate & Art After-Hours Access",
        "category": "Art Experience",
        "description": "Private gallery walkthroughs curated alongside chief art historians and curators.",
        "status": "Reserved Access",
        "highlight": "Florence / Paris"
    }
]

# ==========================================
# FRONTEND HTML ROUTING ENDPOINTS
# ==========================================

@app.get("/", response_class=FileResponse)
def serve_index():
    return FileResponse("static/index.html")

@app.get("/dashboard", response_class=FileResponse)
def serve_dashboard():
    return FileResponse("static/dashboard.html")

@app.get("/profile", response_class=FileResponse)
def serve_profile():
    return FileResponse("static/profile.html")

@app.get("/concierge", response_class=FileResponse)
def serve_concierge():
    return FileResponse("static/concierge.html")

# ==========================================
# REST API ENDPOINTS
# ==========================================

@app.post("/api/concierge/request", response_model=ConciergeRequestResponse, status_code=status.HTTP_201_CREATED)
def submit_concierge_request(payload: ConciergeRequestInput):
    """
    Receives natural language requests from the client, parses/structures them,
    generates a DEMO tracking identifier, and queues it for human or AI concierge processing.
    """
    new_id = f"MTY-{len(DEMO_REQUESTS) + 1001:04d}"
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    new_entry = {
        "request_id": new_id,
        "status": "NEW",
        "category": payload.category,
        "description": payload.query,
        "timestamp": timestamp,
        "assigned_desk": "Desk Alpha (Pending Review)"
    }
    
    DEMO_REQUESTS.insert(0, new_entry)
    
    return ConciergeRequestResponse(
        request_id=new_id,
        status="NEW",
        category=payload.category,
        description=payload.query,
        timestamp=timestamp,
        assigned_desk="Desk Alpha",
        message="Directive received and secured. Our concierge team is processing your specifications."
    )

@app.get("/api/requests", response_model=List[Dict[str, Any]])
def get_user_requests():
    """
    Retrieves all active and historical requests for the authenticated client.
    """
    return DEMO_REQUESTS

@app.get("/api/profile", response_model=UserProfileModel)
def get_client_profile():
    """
    Retrieves stored profile preferences, dietary choices, and travel configuration.
    """
    return UserProfileModel(**DEMO_PROFILE)

@app.post("/api/profile", response_model=UserProfileModel)
def update_client_profile(payload: UserProfileModel):
    """
    Updates client profile preferences securely.
    """
    global DEMO_PROFILE
    DEMO_PROFILE.update(payload.dict(exclude_unset=True))
    DEMO_PROFILE["updated_at"] = datetime.utcnow().isoformat()
    return UserProfileModel(**DEMO_PROFILE)

@app.get("/api/experiences", response_model=List[ExperienceItem])
def get_exclusive_experiences():
    """
    Returns curated exclusive experiences portfolio.
    """
    return [ExperienceItem(**exp) for exp in DEMO_EXPERIENCES]

# ==========================================
# SERVER INITIALIZATION (Uvicorn Ready)
# ==========================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
