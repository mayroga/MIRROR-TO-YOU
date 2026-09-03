from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4
import re

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

BASE = Path(__file__).resolve().parent
STATIC = BASE / "static"

app = FastAPI(title="MIRROR TO YOU", version="2.0")
app.mount("/static", StaticFiles(directory=STATIC), name="static")

MISSIONS = {}


class Memory(BaseModel):
    core: dict = Field(default_factory=dict)
    moment: dict = Field(default_factory=dict)
    preferences: list = Field(default_factory=list)
    dislikes: list = Field(default_factory=list)
    history: list = Field(default_factory=list)
    learning: dict = Field(default_factory=dict)


class MirrorRequest(BaseModel):
    message: str
    memory: Memory = Field(default_factory=Memory)
    language: str = "en"
    voice_enabled: bool = False
    client_device_id: str = ""


class FeedbackRequest(BaseModel):
    mission_id: str
    accepted: bool
    feedback: str = ""
    memory: Memory = Field(default_factory=Memory)


class PlanRevisionRequest(BaseModel):
    mission_id: str
    instruction: str


class RecoveryRequest(BaseModel):
    answers: dict = Field(default_factory=dict)
    memory: Memory = Field(default_factory=Memory)


class ConciergeRequest(BaseModel):
    note: str = ""


def now():
    return datetime.now(timezone.utc).isoformat()


def new_id():
    return "mission_" + uuid4().hex[:14]


def clean(text):
    return re.sub(r"\s+", " ", (text or "").strip())


def detect_language(text):
    if re.search(r"\b(quiero|necesito|viaje|hotel|comida|solo|familia)\b", text.lower()):
        return "es"
    return "en"


def detect_intent(text):
    t = text.lower()

    rules = {
        "TRAVEL": ["flight", "fly", "airport", "vuelo", "avión", "aeropuerto"],
        "ACCOMMODATION": ["hotel", "villa", "resort", "suite", "habitación", "alojamiento"],
        "DINING": ["restaurant", "dinner", "lunch", "chef", "restaurant", "cena", "comida"],
        "TRANSPORT": ["driver", "chauffeur", "car", "transfer", "chofer", "auto", "transporte"],
        "EXPERIENCE": ["experience", "concert", "show", "spa", "yacht", "experiencia", "concierto", "yate"],
        "ESCAPE": ["escape", "get away", "disappear", "quiet", "disconnect", "escapada", "desconectar", "desaparecer"],
        "PRIVATE_LIFE": ["birthday", "anniversary", "gift", "surprise", "cumpleaños", "aniversario", "regalo", "sorpresa"],
    }

    for category, words in rules.items():
        if any(w in t for w in words):
            return category

    return "CONCIERGE"


def detect_priority(text):
    t = text.lower()
    if any(x in t for x in ["urgent", "asap", "today", "immediately", "urgente", "hoy", "ahora"]):
        return "HIGH"
    return "NORMAL"


def detect_privacy(text):
    t = text.lower()
    if any(x in t for x in [
        "private", "privacy", "discreet", "alone", "no people",
        "privado", "privacidad", "discreto", "solo", "sin gente"
    ]):
        return "VERY_HIGH"
    return "HIGH"


def detect_budget(text):
    m = re.search(r"(?:\$|usd\s*)(\d[\d,]*(?:\.\d+)?)", text.lower())
    if not m:
        return None
    return float(m.group(1).replace(",", ""))


def detect_duration(text):
    m = re.search(r"(\d+)\s*(day|days|día|días|night|nights|noche|noches)", text.lower())
    if not m:
        return None
    return f"{m.group(1)} {m.group(2)}"


def detect_companion(text):
    t = text.lower()
    if any(x in t for x in ["alone", "solo", "sola", "myself"]):
        return "ALONE"
    if any(x in t for x in ["wife", "husband", "partner", "esposa", "esposo", "pareja"]):
        return "PARTNER"
    if any(x in t for x in ["family", "familia", "kids", "children", "niños", "hijos"]):
        return "FAMILY"
    return None


def detect_destination(text):
    patterns = [
        r"\bto\s+([A-Z][A-Za-zÀ-ÿ]*(?:\s+[A-Z][A-Za-zÀ-ÿ]*){0,2})",
        r"\ba\s+([A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑ]*(?:\s+[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑ]*){0,2})",
    ]
    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            value = clean(m.group(1))
            if value.lower() not in {"take", "do", "get", "mi", "la", "el"}:
                return value
    return None


def analyze(text, memory):
    language = detect_language(text)
    return {
        "language": language,
        "intent": detect_intent(text),
        "priority": detect_priority(text),
        "privacy": detect_privacy(text),
        "budget": detect_budget(text),
        "duration": detect_duration(text),
        "companion": detect_companion(text),
        "destination": detect_destination(text),
        "message": text,
    }


def missing_information(data):
    intent = data["intent"]
    text = data["message"].lower()

    if intent in {"TRAVEL", "ESCAPE"}:
        if not data["destination"] and not any(
            x in text for x in ["somewhere", "anywhere", "someplace", "cualquier lugar", "algún lugar"]
        ):
            return "destination"

    if intent == "ACCOMMODATION" and not data["destination"]:
        return "destination"

    return None


def build_understanding(data, memory):
    details = []

    if data["duration"]:
        details.append(data["duration"])

    if data["companion"] == "ALONE":
        details.append("traveling alone")

    if data["privacy"] == "VERY_HIGH":
        details.append("high privacy")

    if data["destination"]:
        details.append(f"destination: {data['destination']}")

    return details


def build_plan(data, memory):
    intent = data["intent"]
    details = build_understanding(data, memory)

    titles = {
        "TRAVEL": "Your private journey",
        "ACCOMMODATION": "Your private stay",
        "DINING": "Your dining plan",
        "TRANSPORT": "Your private transportation",
        "EXPERIENCE": "Your experience",
        "ESCAPE": "Your private escape",
        "PRIVATE_LIFE": "Your private request",
        "CONCIERGE": "Your MIRROR request",
    }

    title = titles.get(intent, "Your MIRROR plan")

    steps = [
        "Understand what matters to you",
        "Match it with your MIRROR preferences",
        "Build the right direction",
        "Coordinate only when you approve",
    ]

    return {
        "title": title,
        "category": intent,
        "privacy": data["privacy"],
        "priority": data["priority"],
        "budget": data["budget"],
        "destination": data["destination"],
        "duration": data["duration"],
        "companion": data["companion"],
        "details": details,
        "steps": steps,
        "status": "PROPOSAL",
    }


def response_for(data, plan, memory):
    lang = data["language"]
    missing = missing_information(data)

    if missing == "destination":
        if lang == "es":
            return "Entiendo lo que buscas. Antes de decidir por ti, necesito una sola cosa: ¿quieres que elija yo el destino o ya tienes uno en mente?"
        return "I understand what you're looking for. Before I decide the direction for you, I need one thing: would you like me to choose the destination, or do you already have one in mind?"

    if lang == "es":
        return (
            f"Entiendo. Esto no necesita una búsqueda genérica. "
            f"He identificado tu solicitud como {data['intent'].replace('_', ' ').lower()} "
            f"y voy a construirla alrededor de lo que realmente necesitas ahora. "
            f"No se ha reservado ni comprado nada."
        )

    return (
        f"I understand. This does not need a generic search. "
        f"I identified your request as {data['intent'].replace('_', ' ').lower()} "
        f"and I will build it around what you actually need right now. "
        f"Nothing has been booked or purchased."
    )


def memory_update(memory, data, accepted=None, feedback=""):
    m = memory.model_dump()

    core = m.setdefault("core", {})
    moment = m.setdefault("moment", {})
    learning = m.setdefault("learning", {})

    if data.get("destination"):
        core["last_destination"] = data["destination"]

    if data.get("companion"):
        core["travel_companion"] = data["companion"]

    core["privacy_level"] = data["privacy"]

    moment["last_intent"] = data["intent"]
    moment["last_request"] = data["message"]
    moment["updated_at"] = now()

    if accepted is not None:
        learning["last_accepted"] = accepted

    if feedback:
        learning["last_feedback"] = feedback

    return Memory(**m)


@app.get("/")
async def home():
    return FileResponse(STATIC / "index.html")


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": "MIRROR TO YOU", "version": "2.0"}


@app.get("/api/config")
async def config():
    return {
        "app": "MIRROR TO YOU",
        "version": "2.0",
        "local_memory": True,
        "server_persistent_personal_memory": False,
        "voice_input": True,
        "voice_output": True,
        "google_maps": True,
        "youtube": True,
        "missions": True,
        "personalization": True,
        "concierge": True,
    }


@app.post("/api/mirror")
async def mirror(request: MirrorRequest):
    text = clean(request.message)

    if not text:
        return JSONResponse({"error": "Tell MIRROR what you need."}, status_code=400)

    data = analyze(text, request.memory)
    plan = build_plan(data, request.memory)
    message = response_for(data, plan, request.memory)
    updated_memory = memory_update(request.memory, data)

    mission_id = new_id()

    mission = {
        "id": mission_id,
        "created_at": now(),
        "status": "PROPOSAL",
        "request": text,
        "analysis": data,
        "plan": plan,
    }

    MISSIONS[mission_id] = mission

    return {
        "message": message,
        "mission": mission,
        "plan": plan,
        "memory": updated_memory.model_dump(),
        "analysis": data,
    }


@app.get("/api/missions")
async def missions():
    return {"missions": list(MISSIONS.values())[-20:]}


@app.get("/api/missions/{mission_id}")
async def get_mission(mission_id: str):
    mission = MISSIONS.get(mission_id)
    if not mission:
        return JSONResponse({"error": "Mission not found."}, status_code=404)
    return mission


@app.post("/api/missions/feedback")
async def feedback(request: FeedbackRequest):
    mission = MISSIONS.get(request.mission_id)

    if not mission:
        return JSONResponse({"error": "Mission not found."}, status_code=404)

    mission["status"] = "APPROVED" if request.accepted else "REVISE"
    mission["feedback"] = request.feedback
    mission["updated_at"] = now()

    data = mission["analysis"]
    memory = memory_update(
        request.memory,
        data,
        request.accepted,
        request.feedback
    )

    return {
        "ok": True,
        "status": mission["status"],
        "memory": memory.model_dump(),
    }


@app.post("/api/missions/revise")
async def revise(request: PlanRevisionRequest):
    mission = MISSIONS.get(request.mission_id)

    if not mission:
        return JSONResponse({"error": "Mission not found."}, status_code=404)

    instruction = clean(request.instruction)

    if instruction:
        mission["revision"] = instruction

    mission["status"] = "REVISED"
    mission["updated_at"] = now()

    return {
        "ok": True,
        "message": "MIRROR will adjust the proposal around your instruction.",
        "mission": mission,
    }


@app.post("/api/missions/{mission_id}/concierge")
async def concierge(mission_id: str, request: ConciergeRequest):
    mission = MISSIONS.get(mission_id)

    if not mission:
        return JSONResponse({"error": "Mission not found."}, status_code=404)

    mission["status"] = "CONCIERGE_REVIEW"
    mission["concierge_note"] = clean(request.note)
    mission["updated_at"] = now()

    return {
        "ok": True,
        "status": mission["status"],
        "message": "Your request is prepared for concierge handling. No provider has been booked automatically.",
    }


@app.get("/api/maps")
async def maps(destination: str = ""):
    from urllib.parse import quote
    return {
        "url": f"https://www.google.com/maps/search/?api=1&query={quote(destination or 'luxury destination')}"
    }


@app.get("/api/music")
async def music(query: str = "private luxury relaxing music"):
    from urllib.parse import quote
    return {
        "url": f"https://www.youtube.com/results?search_query={quote(query)}"
    }


@app.post("/api/voice/text")
async def voice_text():
    return {
        "ok": True,
        "message": "Voice recognition and speech synthesis are handled securely by the client browser."
    }


@app.get("/api/providers")
async def providers():
    return {
        "flights": {"connected": False, "mode": "CONCIERGE_READY"},
        "hotels": {"connected": False, "mode": "CONCIERGE_READY"},
        "restaurants": {"connected": False, "mode": "CONCIERGE_READY"},
        "transport": {"connected": False, "mode": "CONCIERGE_READY"},
        "experiences": {"connected": False, "mode": "CONCIERGE_READY"},
        "maps": {"connected": True, "mode": "PUBLIC_LINK"},
        "youtube": {"connected": True, "mode": "PUBLIC_LINK"},
    }


@app.get("/api/memory/recovery/questions")
async def recovery_questions():
    return {
        "questions": [
            {
                "id": "travel_style",
                "question": "What kind of travel feels most like you?",
                "options": ["Private", "Luxury", "Adventurous", "Relaxed", "Spontaneous"]
            },
            {
                "id": "privacy",
                "question": "How important is privacy?",
                "options": ["Essential", "Very important", "Important", "Flexible"]
            },
            {
                "id": "pace",
                "question": "How should MIRROR plan your time?",
                "options": ["Minimal effort", "Balanced", "Detailed", "Surprise me"]
            },
            {
                "id": "environment",
                "question": "What environment usually attracts you?",
                "options": ["Beach", "City", "Nature", "Mountains", "Anywhere"]
            }
        ]
    }


@app.post("/api/memory/recovery")
async def recovery(request: RecoveryRequest):
    m = request.memory.model_dump()
    answers = request.answers

    core = m.setdefault("core", {})

    if answers.get("travel_style"):
        core["travel_style"] = answers["travel_style"]

    if answers.get("privacy"):
        core["privacy_preference"] = answers["privacy"]

    if answers.get("pace"):
        core["planning_style"] = answers["pace"]

    if answers.get("environment"):
        core["preferred_environment"] = answers["environment"]

    return {
        "ok": True,
        "memory": Memory(**m).model_dump()
    }


@app.exception_handler(Exception)
async def server_error(_, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "MIRROR encountered an internal error.", "detail": str(exc)}
    )
