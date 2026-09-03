from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from pathlib import Path
import uuid
import re

APP_NAME = "MIRROR TO YOU"
APP_VERSION = "1.0.0"
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Private Life Concierge Engine for MIRROR TO YOU."
)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ============================================================
# MODELOS
# ============================================================

class Memory(BaseModel):
    core: Dict[str, Any] = Field(default_factory=dict)
    moment: Dict[str, Any] = Field(default_factory=dict)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    dislikes: Dict[str, Any] = Field(default_factory=dict)
    history: List[Dict[str, Any]] = Field(default_factory=list)
    learning: Dict[str, Any] = Field(default_factory=dict)


class MirrorRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    memory: Memory = Field(default_factory=Memory)
    language: str = "en"
    voice_enabled: bool = True
    client_device_id: Optional[str] = None


class MissionCreate(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    memory: Memory = Field(default_factory=Memory)
    language: str = "en"
    client_device_id: Optional[str] = None


class FeedbackRequest(BaseModel):
    mission_id: str
    accepted: bool
    feedback: Optional[str] = None
    memory: Memory = Field(default_factory=Memory)


class PlanRevisionRequest(BaseModel):
    mission_id: str
    instruction: str = Field(..., min_length=1, max_length=5000)
    memory: Memory = Field(default_factory=Memory)


class RecoveryAnswer(BaseModel):
    question_id: str
    answer: str = Field(..., min_length=1, max_length=1000)


class MemoryRecoveryRequest(BaseModel):
    answers: List[RecoveryAnswer] = Field(default_factory=list)
    memory: Memory = Field(default_factory=Memory)


# ============================================================
# ESTADO TEMPORAL DEL SERVIDOR
# ============================================================
# IMPORTANTE:
# Este estado NO contiene la memoria personal del cliente.
# Solo mantiene misiones operativas durante la ejecución.
# La memoria personal permanece en el dispositivo del cliente.

MISSIONS: Dict[str, Dict[str, Any]] = {}


# ============================================================
# UTILIDADES
# ============================================================

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def detect_intent(message: str) -> str:
    text = message.lower()

    if any(word in text for word in [
        "flight", "fly", "airline", "airport", "vuelo", "avión"
    ]):
        return "TRAVEL"

    if any(word in text for word in [
        "hotel", "resort", "villa", "stay", "suite", "alojamiento"
    ]):
        return "ACCOMMODATION"

    if any(word in text for word in [
        "restaurant", "dinner", "lunch", "chef", "food",
        "restaurante", "cena", "almuerzo"
    ]):
        return "DINING"

    if any(word in text for word in [
        "driver", "chauffeur", "car", "transport",
        "conductor", "chofer", "transporte"
    ]):
        return "TRANSPORT"

    if any(word in text for word in [
        "anniversary", "birthday", "surprise", "celebration",
        "aniversario", "cumpleaños", "sorpresa", "celebrar"
    ]):
        return "PRIVATE_LIFE"

    if any(word in text for word in [
        "experience", "adventure", "yacht", "spa",
        "experiencia", "aventura", "yate"
    ]):
        return "EXPERIENCE"

    if any(word in text for word in [
        "weekend", "escape", "getaway", "relax",
        "fin de semana", "escapada", "descansar"
    ]):
        return "ESCAPE"

    return "CONCIERGE"


def detect_priority(message: str) -> str:
    text = message.lower()

    if any(word in text for word in [
        "urgent", "urgently", "today", "tonight", "now",
        "emergency", "urgente", "hoy", "esta noche", "ahora"
    ]):
        return "HIGH"

    if any(word in text for word in [
        "tomorrow", "mañana", "asap", "soon", "pronto"
    ]):
        return "HIGH"

    return "NORMAL"


def detect_privacy(message: str, memory: Memory) -> str:
    text = message.lower()

    if any(word in text for word in [
        "private", "privacy", "secluded", "exclusive",
        "privado", "privacidad", "exclusivo", "aislado"
    ]):
        return "VERY_HIGH"

    existing = memory.preferences.get("privacy")
    if existing:
        return str(existing)

    return "HIGH"


def detect_budget(message: str, memory: Memory) -> Optional[str]:
    text = message.lower()

    money = re.findall(
        r"(?:\$|usd\s*)\s?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)",
        text,
        flags=re.IGNORECASE
    )

    if money:
        return f"${money[0]}"

    existing = memory.preferences.get("budget")
    if existing:
        return str(existing)

    return None


def extract_destination(message: str) -> Optional[str]:
    patterns = [
        r"\bin\s+([A-Z][A-Za-zÀ-ÿ]*(?:\s+[A-Z][A-Za-zÀ-ÿ]*){0,3})",
        r"\bto\s+([A-Z][A-Za-zÀ-ÿ]*(?:\s+[A-Z][A-Za-zÀ-ÿ]*){0,3})",
        r"\ba\s+([A-Z][A-Za-zÀ-ÿ]*(?:\s+[A-Z][A-Za-zÀ-ÿ]*){0,3})"
    ]

    for pattern in patterns:
        match = re.search(pattern, message)
        if match:
            value = clean_text(match.group(1))
            if value.lower() not in {"me", "do", "the"}:
                return value

    return None


def analyze_request(message: str, memory: Memory) -> Dict[str, Any]:
    clean = clean_text(message)

    intent = detect_intent(clean)
    priority = detect_priority(clean)
    privacy = detect_privacy(clean, memory)
    budget = detect_budget(clean, memory)
    destination = extract_destination(clean)

    companions = memory.core.get("companions")
    style = memory.preferences.get("travel_style")

    return {
        "intent": intent,
        "priority": priority,
        "privacy": privacy,
        "budget": budget,
        "destination": destination,
        "companions": companions,
        "style": style,
        "original_request": clean
    }


# ============================================================
# PERSONALIZATION
# ============================================================

def personalize_plan(analysis: Dict[str, Any], memory: Memory) -> Dict[str, Any]:
    preferences = memory.preferences or {}
    dislikes = memory.dislikes or {}
    learning = memory.learning or {}

    return {
        "privacy": analysis["privacy"],
        "budget": analysis["budget"],
        "travel_style": preferences.get("travel_style", "Personalized"),
        "preferred_hotels": preferences.get("hotels"),
        "preferred_food": preferences.get("food"),
        "preferred_transport": preferences.get("transport"),
        "avoid": dislikes,
        "learned_patterns": learning
    }


def build_plan(analysis: Dict[str, Any], memory: Memory) -> Dict[str, Any]:
    personalization = personalize_plan(analysis, memory)

    destination = analysis.get("destination") or "Your destination"

    category_titles = {
        "TRAVEL": "Private Travel Plan",
        "ACCOMMODATION": "Personalized Stay",
        "DINING": "Dining Experience",
        "TRANSPORT": "Private Transportation",
        "PRIVATE_LIFE": "Private Life Experience",
        "EXPERIENCE": "Exclusive Experience",
        "ESCAPE": "Personal Escape",
        "CONCIERGE": "Personal Concierge Plan"
    }

    title = category_titles.get(
        analysis["intent"],
        "MIRROR Personal Plan"
    )

    steps = [
        {
            "order": 1,
            "title": "Understand",
            "description": "MIRROR has analyzed what you asked for and your available preferences."
        },
        {
            "order": 2,
            "title": "Personalize",
            "description": "The proposal is adjusted to your known preferences, dislikes and current needs."
        },
        {
            "order": 3,
            "title": "Plan",
            "description": "MIRROR structures the experience around your request."
        },
        {
            "order": 4,
            "title": "Coordinate",
            "description": "Real providers or a human concierge can be involved when execution is required."
        }
    ]

    if analysis["priority"] == "HIGH":
        steps.append({
            "order": 5,
            "title": "Priority",
            "description": "This request has been marked as high priority."
        })

    return {
        "title": title,
        "destination": destination,
        "category": analysis["intent"],
        "privacy": analysis["privacy"],
        "priority": analysis["priority"],
        "budget": analysis["budget"],
        "personalization": personalization,
        "steps": steps,
        "provider_status": "NOT_CONNECTED",
        "booking_status": "NOT_BOOKED",
        "is_real_booking": False,
        "notice": "This is a personalized planning result. No reservation has been made."
    }


def create_mission(message: str, memory: Memory) -> Dict[str, Any]:
    analysis = analyze_request(message, memory)
    plan = build_plan(analysis, memory)

    mission_id = new_id("mission")

    mission = {
        "id": mission_id,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "status": "PLANNING",
        "analysis": analysis,
        "plan": plan
    }

    MISSIONS[mission_id] = mission
    return mission


# ============================================================
# MEMORY LEARNING
# ============================================================

def generate_memory_update(
    message: str,
    analysis: Dict[str, Any],
    accepted: Optional[bool] = None,
    feedback: Optional[str] = None
) -> Dict[str, Any]:
    update: Dict[str, Any] = {
        "last_interaction": now_iso(),
        "last_intent": analysis.get("intent"),
        "last_priority": analysis.get("priority")
    }

    if analysis.get("destination"):
        update["last_destination"] = analysis["destination"]

    if analysis.get("privacy"):
        update["last_privacy"] = analysis["privacy"]

    if accepted is not None:
        update["last_decision"] = "accepted" if accepted else "rejected"

    if feedback:
        update["last_feedback"] = clean_text(feedback)

    return update


def merge_memory(
    memory: Memory,
    update: Dict[str, Any],
    mission: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    result = memory.model_dump()

    learning = result.setdefault("learning", {})
    learning.update(update)

    history = result.setdefault("history", [])

    if mission:
        history_entry = {
            "mission_id": mission["id"],
            "intent": mission["analysis"].get("intent"),
            "status": mission.get("status"),
            "created_at": mission.get("created_at")
        }
        history.append(history_entry)

        # Limita el tamaño enviado de vuelta al dispositivo.
        result["history"] = history[-100:]

    return result


# ============================================================
# RESPUESTAS NATURALES
# ============================================================

def build_response_text(
    mission: Dict[str, Any],
    language: str
) -> str:
    plan = mission["plan"]
    intent = mission["analysis"]["intent"]

    if language.lower().startswith("es"):
        return (
            f"He entendido lo que necesitas. He creado una propuesta "
            f"personalizada de tipo {intent.replace('_', ' ').lower()}. "
            f"Todavía no se ha realizado ninguna reserva. "
            f"Podemos perfeccionarla antes de pasar a la coordinación."
        )

    return (
        f"I understand what you need. I created a personalized "
        f"{intent.replace('_', ' ').lower()} proposal for you. "
        f"No reservation has been made. "
        f"We can refine it before moving to coordination."
    )


# ============================================================
# RUTAS PRINCIPALES
# ============================================================

@app.get("/")
async def home():
    index_file = STATIC_DIR / "index.html"

    if not index_file.exists():
        return {
            "app": APP_NAME,
            "version": APP_VERSION,
            "status": "online",
            "message": "MIRROR TO YOU engine is running."
        }

    return FileResponse(index_file)


@app.get("/api/health")
async def health():
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "status": "online",
        "time": now_iso(),
        "memory_model": "client_device",
        "server_personal_memory": False
    }


@app.get("/api/config")
async def config():
    return {
        "app_name": APP_NAME,
        "version": APP_VERSION,
        "features": {
            "text": True,
            "voice_input": True,
            "voice_output": True,
            "youtube_music": True,
            "google_maps": True,
            "local_memory": True,
            "missions": True,
            "personalization": True,
            "human_concierge": True
        },
        "privacy": {
            "personal_memory_location": "client_device",
            "server_persistent_personal_memory": False
        }
    }


# ============================================================
# MIRROR — CONVERSACIÓN / SOLICITUD
# ============================================================

@app.post("/api/mirror")
async def mirror(request: MirrorRequest):
    mission = create_mission(request.message, request.memory)

    response_text = build_response_text(
        mission,
        request.language
    )

    memory_update = generate_memory_update(
        request.message,
        mission["analysis"]
    )

    updated_memory = merge_memory(
        request.memory,
        memory_update,
        mission
    )

    return {
        "success": True,
        "message": response_text,
        "mission": mission,
        "memory_update": memory_update,
        "memory": updated_memory,
        "voice": {
            "enabled": request.voice_enabled,
            "text": response_text
        },
        "actions": {
            "maps": True,
            "youtube_music": True,
            "concierge": True
        }
    }


@app.post("/api/concierge/request")
async def concierge_request(request: MissionCreate):
    mission = create_mission(
        request.message,
        request.memory
    )

    mission["status"] = "WAITING_FOR_REVIEW"
    mission["updated_at"] = now_iso()

    MISSIONS[mission["id"]] = mission

    response_text = build_response_text(
        mission,
        request.language
    )

    memory_update = generate_memory_update(
        request.message,
        mission["analysis"]
    )

    updated_memory = merge_memory(
        request.memory,
        memory_update,
        mission
    )

    return {
        "success": True,
        "mission": mission,
        "message": response_text,
        "memory": updated_memory,
        "next_step": "CONCIERGE_REVIEW"
    }


# ============================================================
# MISIONES
# ============================================================

@app.get("/api/missions")
async def get_missions():
    return {
        "success": True,
        "missions": list(MISSIONS.values())
    }


@app.get("/api/missions/{mission_id}")
async def get_mission(mission_id: str):
    mission = MISSIONS.get(mission_id)

    if not mission:
        raise HTTPException(
            status_code=404,
            detail="Mission not found."
        )

    return {
        "success": True,
        "mission": mission
    }


# ============================================================
# REVISION DEL PLAN
# ============================================================

@app.post("/api/missions/revise")
async def revise_plan(request: PlanRevisionRequest):
    mission = MISSIONS.get(request.mission_id)

    if not mission:
        raise HTTPException(
            status_code=404,
            detail="Mission not found."
        )

    instruction = clean_text(request.instruction)

    mission["updated_at"] = now_iso()
    mission["status"] = "PLAN_REVISION"

    revision = {
        "instruction": instruction,
        "created_at": now_iso()
    }

    mission.setdefault("revisions", []).append(revision)

    # En esta primera versión el motor registra la intención
    # de revisión sin inventar disponibilidad o precios reales.
    mission["plan"]["notice"] = (
        "Plan revision requested. Real provider data is not connected yet."
    )

    return {
        "success": True,
        "mission": mission,
        "message": (
            "The plan has been marked for revision. "
            "No external booking has been performed."
        )
    }


# ============================================================
# FEEDBACK / APRENDIZAJE
# ============================================================

@app.post("/api/missions/feedback")
async def mission_feedback(request: FeedbackRequest):
    mission = MISSIONS.get(request.mission_id)

    if not mission:
        raise HTTPException(
            status_code=404,
            detail="Mission not found."
        )

    mission["updated_at"] = now_iso()
    mission["client_decision"] = (
        "ACCEPTED" if request.accepted else "REJECTED"
    )

    if request.feedback:
        mission["client_feedback"] = clean_text(
            request.feedback
        )

    analysis = mission["analysis"]

    memory_update = generate_memory_update(
        analysis.get("original_request", ""),
        analysis,
        request.accepted,
        request.feedback
    )

    updated_memory = merge_memory(
        request.memory,
        memory_update,
        mission
    )

    if request.accepted:
        mission["status"] = "APPROVED"
    else:
        mission["status"] = "REVISION_REQUIRED"

    return {
        "success": True,
        "mission": mission,
        "memory_update": memory_update,
        "memory": updated_memory
    }


# ============================================================
# MEMORY RECOVERY
# ============================================================

@app.get("/api/memory/recovery/questions")
async def memory_recovery_questions():
    return {
        "success": True,
        "questions": [
            {
                "id": "mood",
                "type": "color",
                "question": "What feels right today?",
                "options": [
                    {"value": "calm", "label": "Calm"},
                    {"value": "escape", "label": "Escape"},
                    {"value": "energy", "label": "Energy"},
                    {"value": "discovery", "label": "Discovery"},
                    {"value": "privacy", "label": "Privacy"},
                    {"value": "connection", "label": "Connection"}
                ]
            },
            {
                "id": "experience",
                "type": "choice",
                "question": "What would make today better?",
                "options": [
                    {"value": "relax", "label": "Relax"},
                    {"value": "discover", "label": "Discover"},
                    {"value": "celebrate", "label": "Celebrate"},
                    {"value": "escape", "label": "Escape"},
                    {"value": "indulge", "label": "Indulge"},
                    {"value": "surprise", "label": "Surprise me"}
                ]
            },
            {
                "id": "pace",
                "type": "choice",
                "question": "How should MIRROR approach your day?",
                "options": [
                    {"value": "slow", "label": "Slow"},
                    {"value": "balanced", "label": "Balanced"},
                    {"value": "active", "label": "Active"},
                    {"value": "spontaneous", "label": "Spontaneous"}
                ]
            },
            {
                "id": "privacy",
                "type": "choice",
                "question": "What matters most?",
                "options": [
                    {"value": "privacy", "label": "Privacy"},
                    {"value": "luxury", "label": "Luxury"},
                    {"value": "experience", "label": "Experience"},
                    {"value": "convenience", "label": "Convenience"},
                    {"value": "surprise", "label": "Surprise"}
                ]
            }
        ]
    }


@app.post("/api/memory/recovery")
async def recover_memory(request: MemoryRecoveryRequest):
    current_memory = request.memory.model_dump()

    recovered_signals: Dict[str, Any] = {}

    for answer in request.answers:
        recovered_signals[answer.question_id] = clean_text(
            answer.answer
        )

    current_memory.setdefault("moment", {})
    current_memory["moment"]["recovery_signals"] = recovered_signals
    current_memory["moment"]["recovery_at"] = now_iso()

    current_memory.setdefault("learning", {})
    current_memory["learning"]["last_recovery"] = now_iso()

    return {
        "success": True,
        "memory": current_memory,
        "message": (
            "New preference signals were prepared for local memory. "
            "The server does not permanently store this personal memory."
        )
    }


# ============================================================
# GOOGLE MAPS
# ============================================================

@app.get("/api/maps")
async def maps(query: str):
    query = clean_text(query)

    if not query:
        raise HTTPException(
            status_code=400,
            detail="A place or destination is required."
        )

    # La URL será generada en el frontend cuando el cliente
    # solicite abrir Google Maps.
    maps_url = (
        "https://www.google.com/maps/search/"
        + query.replace(" ", "+")
    )

    return {
        "success": True,
        "query": query,
        "url": maps_url
    }


# ============================================================
# YOUTUBE MUSIC
# ============================================================

@app.get("/api/music")
async def music(query: str = "relaxing luxury lounge music"):
    query = clean_text(query)

    if not query:
        query = "relaxing luxury lounge music"

    youtube_url = (
        "https://www.youtube.com/results?search_query="
        + query.replace(" ", "+")
    )

    return {
        "success": True,
        "query": query,
        "url": youtube_url
    }


# ============================================================
# VOICE
# ============================================================

@app.post("/api/voice/text")
async def voice_text(request: MirrorRequest):
    message = clean_text(request.message)

    if not message:
        raise HTTPException(
            status_code=400,
            detail="Voice text cannot be empty."
        )

    return {
        "success": True,
        "text": message,
        "voice_ready": True,
        "note": (
            "Speech recognition and speech synthesis are handled "
            "by the client device in the frontend."
        )
    }


# ============================================================
# PROVIDER STATUS
# ============================================================

@app.get("/api/providers")
async def providers():
    return {
        "success": True,
        "providers": {
            "flights": {
                "connected": False,
                "status": "READY_FOR_INTEGRATION"
            },
            "hotels": {
                "connected": False,
                "status": "READY_FOR_INTEGRATION"
            },
            "restaurants": {
                "connected": False,
                "status": "READY_FOR_INTEGRATION"
            },
            "transport": {
                "connected": False,
                "status": "READY_FOR_INTEGRATION"
            },
            "experiences": {
                "connected": False,
                "status": "READY_FOR_INTEGRATION"
            },
            "google_maps": {
                "connected": True,
                "status": "LINK_BASED"
            },
            "youtube": {
                "connected": True,
                "status": "LINK_BASED"
            }
        }
    }


# ============================================================
# CONCIERGE STATUS
# ============================================================

@app.post("/api/missions/{mission_id}/concierge")
async def send_to_concierge(mission_id: str):
    mission = MISSIONS.get(mission_id)

    if not mission:
        raise HTTPException(
            status_code=404,
            detail="Mission not found."
        )

    mission["status"] = "CONCIERGE_REVIEW"
    mission["updated_at"] = now_iso()

    return {
        "success": True,
        "mission_id": mission_id,
        "status": mission["status"],
        "message": (
            "The mission is ready for concierge review. "
            "No provider has been contacted automatically."
        )
    }


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return {
        "success": False,
        "error": "MIRROR_ENGINE_ERROR",
        "message": "MIRROR could not complete this operation."
    }
