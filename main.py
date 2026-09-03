# main.py
import os
import uuid
import urllib.parse
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from mirror_engine import process

BASE = Path(__file__).resolve().parent
STATIC = BASE / "static"

app = FastAPI(title="MIRROR TO YOU", version="4.0")

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
    index = STATIC / "index.html"
    if not index.exists():
        return JSONResponse({"ok": False, "error": "static/index.html missing"}, status_code=500)
    return FileResponse(index)

@app.post("/api/mirror")
async def mirror(data: MirrorRequest):
    message = data.message.strip()
    if not message:
        return JSONResponse({"ok": False, "error": "Empty contextual message."}, status_code=400)

    memory_dict = data.memory.model_dump()
    
    # Procesar la instrucción delegando el control lógico absoluto a la IA
    ai_plan = process(message, memory_dict)
    
    # Sincronización limpia de historial y reentradas en base al mapeo directo de la IA
    memory_dict["history"].append({
        "at": datetime.now().isoformat(),
        "intent": ai_plan.get("intent", "CONCIERGE")
    })
    
    memory_dict["moment"] = {
        "intent": ai_plan.get("intent"),
        "language": ai_plan.get("language"),
        "destination": ai_plan.get("premium_destination_query")
    }

    mission_id = "premium_" + uuid.uuid4().hex[:12]
    
    return {
        "ok": True,
        "message": ai_plan.get("reply"),
        "understanding": memory_dict["moment"],
        "plan": ai_plan,
        "mission": {"id": mission_id, "status": ai_plan.get("intent")},
        "memory": memory_dict
    }

@app.get("/api/maps")
async def maps(destination: str = ""):
    # Ruta de geolocalización premium exacta e integrada a la API de mapas
    target = destination.strip() or "Luxury Elite Hub Private Lounge"
    q = urllib.parse.quote(target)
    return {"ok": True, "url": f"https://google.com{q}"}

@app.get("/api/music")
async def music(query: str = ""):
    # Canal de audio premium exacto e integrado a las listas acústicas
    target = query.strip() or "Premium Private Lounge Ambient"
    q = urllib.parse.quote(target)
    return {"ok": True, "url": f"https://youtube.com{q}"}
