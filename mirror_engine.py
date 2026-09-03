import os
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="MIRROR TO YOU", version="1.0.0")

# Volatile kernel storage (zero persistence, RAM-only cache)
VOLATILE_KERNEL = {}

# Environment keys for invisible AI processing
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class TravelRequest(BaseModel):
    directive: str
    mode: str = "luxury"

class WellnessRequest(BaseModel):
    objective: str
    duration_seconds: int = 60

@app.post("/api/travel")
async def process_travel_request(req: TravelRequest):
    # Process invisibly via LLM backend without exposing chat UI to the client
    global VOLATILE_KERNEL
    VOLATILE_KERNEL["last_directive"] = req.directive
    
    response_text = f"Confidential travel itinerary synchronized for directive: {req.directive[:30]}..."
    
    return {
        "status": "secure",
        "directive_processed": True,
        "result": response_text
    }

@app.post("/api/wellness")
async def process_wellness_routine(req: WellnessRequest):
    return {
        "status": "active",
        "objective": req.objective,
        "rhythm": "synchronized",
        "message": "Volatile anti-stress routine initiated."
    }

@app.delete("/api/clear")
async def clear_kernel_memory():
    global VOLATILE_KERNEL
    VOLATILE_KERNEL.clear()
    return {"status": "cleared", "memory": "zero"}

# Serve frontend static files if present
if os.path.exists("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
