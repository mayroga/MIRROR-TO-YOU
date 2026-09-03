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

app = FastAPI(title="MIRROR TO YOU", version="5.0")

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
    
    # Procesa de forma unificada comandos de botón o textos libres del chat
    ai_plan = process(data.message.strip(), memory_dict)
    
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
        "memory": memory_dict
    }
