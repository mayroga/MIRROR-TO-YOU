import os
import uuid
import urllib.parse
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from mirror_engine import process, response_text

BASE = Path(__file__).resolve().parent
STATIC = BASE / "static"

app = FastAPI(title="MIRROR TO YOU", version="3.0")

if STATIC.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC)),name="static")

MISSIONS = {}

class Memory(BaseModel):
    core: dict = Field(default_factory=dict)
    moment: dict = Field(default_factory=dict)
    preferences: dict = Field(default_factory=dict)
    dislikes: list = Field(default_factory=list)
    history: list = Field(default_factory=list)
    learning: dict = Field(default_factory=dict)

class MirrorRequest(BaseModel):
    message: str = ""
    language: str = "en"
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
    result = process(message, memory_dict)
    
    # Guardar historial para medir reentradas y fijar objetivos dinámicos
    memory_dict["history"].append({
        "at": datetime.now().isoformat(),
        "intent": result["understanding"]["intent"]
    })
    memory_dict["moment"] = result["understanding"]

    mission_id = "premium_" + uuid.uuid4().hex[:12]
    return {
        "ok": True,
        "message": result["proposal"]["reply"],
        "understanding": result["understanding"],
        "plan": result["proposal"],
        "mission": {"id": mission_id, "status": result["status"]},
        "memory": memory_dict
    }

@app.get("/api/maps")
async def maps(destination: str = ""):
    # Redirección directa hacia la experiencia o coordenadas premium filtradas
    q = urllib.parse.quote(destination.strip() or "Luxury Elite Experiences")
    return {"ok": True, "url": f"https://google.com{q}"}

@app.get("/api/music")
async def music(query: str = ""):
    q = urllib.parse.quote(query.strip() or "Premium Private Lounge Ambient")
    return {"ok": True, "url": f"https://youtube.com{q}"}
