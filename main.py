import os
import uuid
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from mirror_engine import process, response_text


BASE = Path(__file__).resolve().parent
STATIC = BASE / "static"
STATIC.mkdir(exist_ok=True)

app = FastAPI(title="MIRROR TO YOU", version="2.0")
app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")

MISSIONS = {}


def now():
    return datetime.now(timezone.utc).isoformat()


def new_id():
    return "m_" + uuid.uuid4().hex[:12]


def clean(value, default=None):
    if value is None:
        return default
    if isinstance(value, str):
        value = value.strip()
        return value or default
    return value


class Memory(BaseModel):
    core: dict = Field(default_factory=dict)
    moment: dict = Field(default_factory=dict)
    preferences: dict = Field(default_factory=dict)
    dislikes: list = Field(default_factory=list)
    history: list = Field(default_factory=list)
    learning: dict = Field(default_factory=dict)


class MirrorRequest(BaseModel):
    message: str
    memory: Memory = Field(default_factory=Memory)
    language: str | None = None
    voice_enabled: bool = False
    client_device_id: str | None = None


class FeedbackRequest(BaseModel):
    mission_id: str
    accepted: bool
    feedback: str = ""
    memory: Memory = Field(default_factory=Memory)


class PlanRevisionRequest(BaseModel):
    mission_id: str
    instruction: str
    memory: Memory = Field(default_factory=Memory)


class ConciergeRequest(BaseModel):
    note: str = ""
    memory: Memory = Field(default_factory=Memory)


class RecoveryRequest(BaseModel):
    answers: dict = Field(default_factory=dict)
    memory: Memory = Field(default_factory=Memory)


def update_memory(memory, understanding, accepted=None, feedback=""):
    data = memory.model_dump() if isinstance(memory, Memory) else dict(memory or {})
    core = data.setdefault("core", {})
    moment = data.setdefault("moment", {})
    preferences = data.setdefault("preferences", {})
    dislikes = data.setdefault("dislikes", [])
    history = data.setdefault("history", [])
    learning = data.setdefault("learning", {})

    for key in ("companion", "destination", "budget", "duration"):
        value = understanding.get(key)
        if value not in (None, "", "unknown"):
            moment[key] = value

    signals = understanding.get("signals") or []
    if signals:
        moment["signals"] = signals

    if understanding.get("privacy"):
        moment["privacy"] = understanding["privacy"]

    if understanding.get("priority"):
        moment["priority"] = understanding["priority"]

    intent = understanding.get("intent")
    if intent:
        moment["intent"] = intent

    if accepted is not None:
        learning["last_accepted"] = bool(accepted)

    if feedback:
        learning["last_feedback"] = feedback[:500]

    if accepted is False and feedback:
        dislikes.append(feedback[:200])
        data["dislikes"] = dislikes[-30:]

    if intent:
        history.append({
            "time": now(),
            "intent": intent,
            "accepted": accepted
        })
        data["history"] = history[-50:]

    if signals:
        for signal in signals:
            preferences[signal.lower()] = True

    data["core"] = core
    data["moment"] = moment
    data["preferences"] = preferences
    data["learning"] = learning
    return data


def public_plan(proposal, mission_id):
    if not proposal:
        return None

    return {
        "title": proposal.get("title") or "Your MIRROR",
        "direction": proposal.get("direction") or [],
        "category": proposal.get("category"),
        "privacy": proposal.get("privacy"),
        "priority": proposal.get("priority"),
        "budget": proposal.get("budget"),
        "destination": proposal.get("destination"),
        "duration": proposal.get("duration"),
        "companion": proposal.get("companion"),
        "signals": proposal.get("signals") or [],
        "confidence": proposal.get("confidence", 0),
        "status": proposal.get("status", "PROPOSAL"),
        "questions": proposal.get("questions") or [],
        "mission_id": mission_id
    }


@app.get("/")
async def home():
    return FileResponse(STATIC / "index.html")


@app.get("/api/health")
async def health():
    return {
        "ok": True,
        "service": "MIRROR TO YOU",
        "version": "2.0",
        "time": now()
    }


@app.get("/api/config")
async def config():
    return {
        "name": "MIRROR TO YOU",
        "version": "2.0",
        "voice": True,
        "memory": "device",
        "ai": True,
        "maps": True,
        "music": True,
        "concierge": True
    }


@app.post("/api/mirror")
async def mirror(data: MirrorRequest):
    message = clean(data.message)

    if not message:
        return JSONResponse(
            {"ok": False, "error": "Tell MIRROR what is on your mind."},
            status_code=400
        )

    memory = data.memory.model_dump()

    try:
        result = process(message, memory)
    except Exception as exc:
        return JSONResponse(
            {
                "ok": False,
                "error": "MIRROR could not complete this moment.",
                "detail": str(exc)
            },
            status_code=500
        )

    understanding = result.get("understanding") or {}
    personalization = result.get("personalization") or {}
    decision = result.get("decision") or {}
    proposal = result.get("proposal") or {}

    language = (
        clean(data.language)
        or understanding.get("language")
        or "en"
    )

    try:
        message_out = response_text(result, language)
    except Exception:
        message_out = (
            "I’m here. Tell me a little more about what you need right now."
            if language.startswith("en")
            else "Estoy aquí. Cuéntame un poco más sobre lo que necesitas ahora."
        )

    updated_memory = update_memory(
        memory,
        understanding
    )

    mission_id = new_id()

    mission = {
        "id": mission_id,
        "created_at": now(),
        "status": (
            "CLARIFY"
            if decision.get("action") in ("ASK", "CLARIFY")
            else "PROPOSAL"
        ),
        "request": message,
        "understanding": understanding,
        "personalization": personalization,
        "decision": decision,
        "proposal": proposal
    }

    MISSIONS[mission_id] = mission

    return {
        "ok": True,
        "message": message_out,
        "language": language,
        "analysis": understanding,
        "understanding": understanding,
        "personalization": personalization,
        "decision": decision,
        "plan": public_plan(proposal, mission_id),
        "mission": {
            "id": mission_id,
            "status": mission["status"]
        },
        "memory": updated_memory
    }


@app.get("/api/missions")
async def missions():
    return {
        "ok": True,
        "missions": [
            {
                "id": m["id"],
                "created_at": m["created_at"],
                "status": m["status"],
                "request": m["request"]
            }
            for m in list(MISSIONS.values())[-30:][::-1]
        ]
    }


@app.get("/api/missions/{mission_id}")
async def mission(mission_id: str):
    item = MISSIONS.get(mission_id)

    if not item:
        return JSONResponse(
            {"ok": False, "error": "Mission not found."},
            status_code=404
        )

    return {
        "ok": True,
        "mission": item
    }


@app.post("/api/missions/feedback")
async def feedback(data: FeedbackRequest):
    item = MISSIONS.get(data.mission_id)

    if not item:
        return JSONResponse(
            {"ok": False, "error": "Mission not found."},
            status_code=404
        )

    item["feedback"] = {
        "accepted": data.accepted,
        "text": clean(data.feedback, ""),
        "time": now()
    }

    item["status"] = "COMPLETED" if data.accepted else "LEARNING"

    understanding = item.get("understanding") or {}
    updated_memory = update_memory(
        data.memory,
        understanding,
        data.accepted,
        data.feedback
    )

    return {
        "ok": True,
        "status": item["status"],
        "memory": updated_memory
    }


@app.post("/api/missions/revise")
async def revise(data: PlanRevisionRequest):
    item = MISSIONS.get(data.mission_id)

    if not item:
        return JSONResponse(
            {"ok": False, "error": "Mission not found."},
            status_code=404
        )

    instruction = clean(data.instruction)

    if not instruction:
        return JSONResponse(
            {"ok": False, "error": "Tell MIRROR what you would change."},
            status_code=400
        )

    original = item.get("request", "")
    combined = f"{original}\n\nAdditional direction: {instruction}"

    try:
        result = process(
            combined,
            data.memory.model_dump()
        )
    except Exception as exc:
        return JSONResponse(
            {
                "ok": False,
                "error": "MIRROR could not revise the experience.",
                "detail": str(exc)
            },
            status_code=500
        )

    proposal = result.get("proposal") or {}
    understanding = result.get("understanding") or {}
    decision = result.get("decision") or {}

    item["understanding"] = understanding
    item["decision"] = decision
    item["proposal"] = proposal
    item["revision"] = instruction
    item["status"] = "PROPOSAL"

    language = (
        understanding.get("language")
        or "en"
    )

    try:
        text = response_text(result, language)
    except Exception:
        text = "I’ve adjusted the direction."

    return {
        "ok": True,
        "message": text,
        "analysis": understanding,
        "decision": decision,
        "plan": public_plan(proposal, data.mission_id),
        "mission": {
            "id": data.mission_id,
            "status": item["status"]
        }
    }


@app.post("/api/missions/{mission_id}/concierge")
async def concierge(mission_id: str, data: ConciergeRequest):
    item = MISSIONS.get(mission_id)

    if not item:
        return JSONResponse(
            {"ok": False, "error": "Mission not found."},
            status_code=404
        )

    item["status"] = "CONCIERGE"
    item["concierge"] = {
        "note": clean(data.note, ""),
        "created_at": now()
    }

    return {
        "ok": True,
        "status": "CONCIERGE",
        "message": (
            "I have your request. A private concierge can take it from here."
        )
    }


@app.get("/api/maps")
async def maps(destination: str = ""):
    destination = clean(destination)

    if not destination:
        return {
            "ok": False,
            "url": None
        }

    url = (
        "https://www.google.com/maps/search/?api=1&query="
        + urllib.parse.quote_plus(destination)
    )

    return {
        "ok": True,
        "destination": destination,
        "url": url
    }


@app.get("/api/music")
async def music(query: str = ""):
    query = clean(query, "calm luxury music")

    url = (
        "https://www.youtube.com/results?search_query="
        + urllib.parse.quote_plus(query)
    )

    return {
        "ok": True,
        "query": query,
        "url": url
    }


class VoiceRequest(BaseModel):
    text: str


@app.post("/api/voice/text")
async def voice_text(data: VoiceRequest):
    text = clean(data.text, "")

    return {
        "ok": True,
        "text": text
    }


@app.get("/api/providers")
async def providers():
    return {
        "ok": True,
        "providers": [],
        "message": "Real providers will be connected only when verified integrations are available."
    }


@app.get("/api/memory/recovery/questions")
async def recovery_questions():
    return {
        "ok": True,
        "questions": [
            {
                "id": "energy",
                "question": "What feels most like you today?",
                "options": [
                    "Quiet",
                    "Movement",
                    "Water",
                    "Music",
                    "Nature"
                ]
            },
            {
                "id": "need",
                "question": "What would you like more of right now?",
                "options": [
                    "Disconnect",
                    "Discover",
                    "Breathe",
                    "Play",
                    "Do nothing"
                ]
            },
            {
                "id": "style",
                "question": "Which experience feels most natural to you?",
                "options": [
                    "Private",
                    "Spontaneous",
                    "Refined",
                    "Simple",
                    "Unexpected"
                ]
            },
            {
                "id": "pace",
                "question": "How should MIRROR move with you?",
                "options": [
                    "Slowly",
                    "Directly",
                    "Quietly",
                    "Playfully",
                    "Surprise me"
                ]
            }
        ]
    }


@app.post("/api/memory/recovery")
async def recovery(data: RecoveryRequest):
    memory = data.memory.model_dump()
    answers = data.answers or {}

    preferences = memory.setdefault("preferences", {})
    moment = memory.setdefault("moment", {})

    for key, value in answers.items():
        value = clean(value)
        if value:
            preferences[key] = value
            moment[key] = value

    memory["recovered_at"] = now()

    return {
        "ok": True,
        "memory": memory,
        "message": "MIRROR is getting to know your rhythm again."
    }


@app.exception_handler(Exception)
async def global_error(request: Request, exc: Exception):
    return JSONResponse(
        {
            "ok": False,
            "error": "MIRROR encountered an unexpected error.",
            "detail": str(exc)
        },
        status_code=500
    )
