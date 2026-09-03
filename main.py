# main.py
import os
import uuid
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from mirror_engine import process

BASE = Path(__file__).resolve().parent
STATIC = BASE / "static"

app = FastAPI(title="MIRROR TO YOU", version="6.0")

if STATIC.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")

class Memory(BaseModel):
    core: dict = Field(default_factory=dict)
    moment: dict = Field(default_factory=dict)
    preferences: dict = Field(default_factory=dict)
    dislikes: list = Field(default_factory=list)
    history: list = Field(default_factory=list)
    learning: dict = Field(default_factory=dict)

class MirrorRequest(BaseModel):
    message: str = ""
    language: str = "es"
    device_id: str = ""
    memory: Memory = Field(default_factory=Memory)

@app.get("/")
async def home():
    return FileResponse(STATIC / "index.html")

@app.post("/api/mirror")
async def mirror(data: MirrorRequest):
    memory_dict = data.memory.model_dump()
    
    ai_plan = process(data.message.strip(), memory_dict)
    
    memory_dict["history"].append({
        "at": datetime.now().isoformat(),
        "intent": ai_plan.get("intent", "CONCIERGE")
    })
    
    memory_dict["moment"] = {
        "intent": ai_plan.get("intent"),
        "language": ai_plan.get("language"),
        "destination": ai_plan.get("premium_destination_query"),
        "status_color_zone": ai_plan.get("status_color_zone")
    }

return {
    "ok": True,
    "message": ai_plan.get("reply"), # Acceso directo y seguro mediante .get() al plano de la IA
    "understanding": memory_dict["moment"], # Lectura sincronizada de la huella local actualizada
    "plan": ai_plan,
    "memory": memory_dict
}

@app.get("/api/maps")
async def maps(destination: str = ""):
    import urllib.parse
    q = urllib.parse.quote(destination.strip() or "Luxury Elite Private Space")
    return {"ok": True, "url": f"https://google.com{q}"}

@app.get("/api/music")
async def music(query: str = ""):
    import urllib.parse
    q = urllib.parse.quote(query.strip() or "Premium Neuro Ambient Lounge")
    return {"ok": True, "url": f"https://youtube.com{q}"}
