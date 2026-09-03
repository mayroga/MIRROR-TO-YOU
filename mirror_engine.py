```python
from datetime import datetime, timezone
import re


def now():
    return datetime.now(timezone.utc).isoformat()


def clean(text):
    return re.sub(r"\s+", " ", (text or "").strip())


# ---------------------------------------------------------
# 1. ENTENDER
# ---------------------------------------------------------

INTENTS = {
    "TRAVEL": [
        "flight", "fly", "airport", "vuelo", "avión", "aeropuerto",
        "travel", "viaje"
    ],
    "ESCAPE": [
        "escape", "get away", "disappear", "disconnect", "quiet",
        "escapada", "desconectar", "desaparecer", "tranquilo", "tranquila"
    ],
    "ACCOMMODATION": [
        "hotel", "villa", "resort", "suite", "room",
        "hotel", "villa", "resort", "habitación"
    ],
    "DINING": [
        "restaurant", "dinner", "lunch", "chef", "cena", "comida",
        "restaurante", "chef"
    ],
    "TRANSPORT": [
        "driver", "chauffeur", "car", "transfer", "chofer",
        "transporte", "auto"
    ],
    "EXPERIENCE": [
        "spa", "yacht", "concert", "show", "experience",
        "yate", "concierto", "espectáculo", "experiencia"
    ],
    "PRIVATE_LIFE": [
        "birthday", "anniversary", "gift", "surprise",
        "cumpleaños", "aniversario", "regalo", "sorpresa"
    ],
}


def understand(text):
    text = clean(text)
    low = text.lower()

    intent = "CONCIERGE"
    for name, words in INTENTS.items():
        if any(word in low for word in words):
            intent = name
            break

    privacy = "HIGH" if any(x in low for x in [
        "private", "privacy", "discreet", "alone", "no people",
        "privado", "privacidad", "discreto", "solo", "sin gente"
    ]) else "NORMAL"

    urgency = "HIGH" if any(x in low for x in [
        "urgent", "asap", "today", "now", "immediately",
        "urgente", "hoy", "ahora", "inmediatamente"
    ]) else "NORMAL"

    companion = None
    if any(x in low for x in ["alone", "solo", "sola", "myself"]):
        companion = "ALONE"
    elif any(x in low for x in ["wife", "husband", "partner", "esposa", "esposo", "pareja"]):
        companion = "PARTNER"
    elif any(x in low for x in ["family", "familia", "kids", "children", "hijos", "niños"]):
        companion = "FAMILY"

    duration = None
    m = re.search(
        r"\b(\d+)\s*(day|days|día|días|night|nights|noche|noches)\b",
        low
    )
    if m:
        duration = f"{m.group(1)} {m.group(2)}"

    budget = None
    m = re.search(r"(?:\$|usd\s*)([\d,]+(?:\.\d+)?)", low)
    if m:
        budget = float(m.group(1).replace(",", ""))

    destination = None
    m = re.search(
        r"\b(?:to|en|a)\s+([A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑ]*(?:\s+[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑ]*){0,2})",
        text
    )
    if m:
        destination = clean(m.group(1))

    signals = []

    if any(x in low for x in ["quiet", "tranquilo", "tranquila", "silence", "silencio"]):
        signals.append("QUIET")

    if any(x in low for x in ["luxury", "luxury hotel", "lujo", "premium", "five star", "5 star"]):
        signals.append("LUXURY")

    if any(x in low for x in ["crowd", "crowds", "people", "gente", "multitud"]):
        signals.append("LOW_CROWD")

    if any(x in low for x in ["relax", "rest", "descansar", "relaj"]):
        signals.append("RELAXATION")

    if any(x in low for x in ["food", "dining", "comida", "cena", "gastronomy", "gastronomía"]):
        signals.append("DINING")

    return {
        "message": text,
        "intent": intent,
        "privacy": privacy,
        "priority": urgency,
        "companion": companion,
        "duration": duration,
        "budget": budget,
        "destination": destination,
        "signals": signals,
    }


# ---------------------------------------------------------
# 2. PERSONALIZAR
# ---------------------------------------------------------

def personalize(understanding, memory):
    core = memory.get("core", {}) if isinstance(memory, dict) else {}
    preferences = memory.get("preferences", []) if isinstance(memory, dict) else []
    dislikes = memory.get("dislikes", []) if isinstance(memory, dict) else {}
    moment = memory.get("moment", {}) if isinstance(memory, dict) else {}

    signals = list(understanding.get("signals", []))

    style = core.get("travel_style") or core.get("planning_style")
    privacy = core.get("privacy_preference")

    if style:
        signals.append(str(style).upper())

    if privacy:
        signals.append(str(privacy).upper())

    return {
        "core": core,
        "moment": moment,
        "preferences": preferences,
        "dislikes": dislikes,
        "signals": list(dict.fromkeys(signals)),
        "personalized": bool(core or preferences or dislikes or moment),
    }


# ---------------------------------------------------------
# 3. DECIDIR
# ---------------------------------------------------------

def decide(understanding, personalization):
    intent = understanding["intent"]
    signals = personalization["signals"]
    destination = understanding.get("destination")

    questions = []

    if intent in {"TRAVEL", "ESCAPE", "ACCOMMODATION"} and not destination:
        if not any(x in signals for x in ["ANYWHERE", "SPONTANEOUS"]):
            questions.append("destination_or_permission_to_choose")

    confidence = 0

    if intent != "CONCIERGE":
        confidence += 25
    if destination:
        confidence += 20
    if understanding.get("duration"):
        confidence += 15
    if understanding.get("companion"):
        confidence += 10
    if understanding.get("budget") is not None:
        confidence += 10
    if signals:
        confidence += min(20, len(signals) * 5)

    if questions:
        decision = "ASK"
    elif confidence >= 55:
        decision = "PROPOSE"
    else:
        decision = "CLARIFY"

    return {
        "decision": decision,
        "confidence": min(confidence, 100),
        "questions": questions,
        "reason": (
            "Enough information to create a personalized direction."
            if decision == "PROPOSE"
            else "One important decision is still missing."
        ),
    }


# ---------------------------------------------------------
# 4. PROPONER
# ---------------------------------------------------------

def propose(understanding, personalization, decision):
    intent = understanding["intent"]
    signals = personalization["signals"]
    destination = understanding.get("destination")

    names = {
        "TRAVEL": "Your private journey",
        "ESCAPE": "Your private escape",
        "ACCOMMODATION": "Your private stay",
        "DINING": "Your dining experience",
        "TRANSPORT": "Your private transportation",
        "EXPERIENCE": "Your experience",
        "PRIVATE_LIFE": "Your private request",
        "CONCIERGE": "Your MIRROR request",
    }

    title = names.get(intent, "Your MIRROR proposal")

    if decision["decision"] != "PROPOSE":
        return {
            "title": title,
            "status": decision["decision"],
            "category": intent,
            "reason": decision["reason"],
            "questions": decision["questions"],
        }

    direction = []

    if destination:
        direction.append(f"Focus on {destination}.")

    if "QUIET" in signals or "RELAXATION" in signals:
        direction.append("Prioritize calm, privacy and low-friction experiences.")

    if "LOW_CROWD" in signals:
        direction.append("Avoid crowded environments.")

    if "LUXURY" in signals:
        direction.append("Prioritize high-comfort, discreet and premium options.")

    if understanding.get("companion") == "ALONE":
        direction.append("Keep the experience designed for one person.")

    if understanding.get("duration"):
        direction.append(f"Work around {understanding['duration']}.")

    if understanding.get("budget") is not None:
        direction.append(f"Respect the stated budget of ${understanding['budget']:,.0f}.")

    if not direction:
        direction.append("Build the experience around the client's stated intention and MIRROR preferences.")

    return {
        "title": title,
        "status": "PROPOSAL",
        "category": intent,
        "privacy": understanding["privacy"],
        "priority": understanding["priority"],
        "budget": understanding["budget"],
        "destination": destination,
        "duration": understanding["duration"],
        "companion": understanding["companion"],
        "direction": direction,
        "signals": signals,
        "confidence": decision["confidence"],
    }


# ---------------------------------------------------------
# PIPELINE PRINCIPAL
# ---------------------------------------------------------

def process(message, memory=None):
    memory = memory or {}

    understanding = understand(message)
    personalization = personalize(understanding, memory)
    decision = decide(understanding, personalization)
    proposal = propose(understanding, personalization, decision)

    return {
        "understanding": understanding,
        "personalization": personalization,
        "decision": decision,
        "proposal": proposal,
        "processed_at": now(),
    }


# ---------------------------------------------------------
# TEXTO PARA LA INTERFAZ
# ---------------------------------------------------------

def response_text(result, language="en"):
    understanding = result["understanding"]
    decision = result["decision"]
    proposal = result["proposal"]

    if decision["decision"] in {"ASK", "CLARIFY"}:
        if language == "es":
            return (
                "Entiendo lo que buscas. Antes de construir algo para ti, "
                "necesito una pequeña aclaración para no darte una propuesta genérica."
            )
        return (
            "I understand what you're looking for. Before I build it for you, "
            "I need one small clarification so I don't give you a generic proposal."
        )

    if language == "es":
        return (
            f"Lo entiendo. Esto es una solicitud de {understanding['intent'].lower().replace('_', ' ')}. "
            "Estoy construyendo la propuesta alrededor de tus necesidades, "
            "tus preferencias conocidas y lo que importa ahora. "
            "Nada ha sido reservado ni comprado."
        )

    return (
        f"I understand. This is a {understanding['intent'].lower().replace('_', ' ')} request. "
        "I'm shaping the proposal around your needs, your known preferences, "
        "and what matters right now. Nothing has been booked or purchased."
    )
```
