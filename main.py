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

# main.py (Fragmento corregido del endpoint /api/mirror)

@app.post("/api/mirror")
async def mirror(data: MirrorRequest):
    message = data.message.strip()
    if not message:
        return JSONResponse({"ok": False, "error": "Empty contextual message."}, status_code=400)

    memory_dict = data.memory.model_dump()
    
    # Procesa de forma unificada comandos de botón o textos libres del chat
    ai_plan = process(message, memory_dict)
    
    memory_dict["history"].append({
        "at": datetime.now().isoformat(),
        "intent": ai_plan.get("intent", "CONCIERGE")
    })
    
    memory_dict["moment"] = {
        "intent": ai_plan.get("intent"),
        "language": ai_plan.get("language"),
        "destination": ai_plan.get("premium_destination_query")
    }

    # Toda esta estructura debe llevar obligatoriamente 4 espacios de indentación hacia la derecha
    return {
        "ok": True,
        "message": ai_plan.get("reply"),
        "understanding": memory_dict["moment"],
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
