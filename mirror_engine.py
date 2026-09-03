```python
"""
MIRROR TO YOU
The Private Life Concierge
Core Intelligence Engine

Version: 1.0.0

Purpose:
- Understand natural-language requests.
- Convert requests into structured intent.
- Combine CORE MEMORY + TODAY'S MOMENT.
- Build personalized plans.
- Score possible decisions.
- Detect privacy, urgency and complexity.
- Decide when human Concierge support is appropriate.
- Manage mission lifecycle.
- Learn from client feedback.
- Never pretend that an external action was completed when it was not.

Important:
Personal memory should remain on the client's device.
This module does NOT create a permanent server-side personal profile.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import re


ENGINE_NAME = "MIRROR TO YOU"
ENGINE_VERSION = "1.0.0"


# ============================================================
# BASIC UTILITIES
# ============================================================

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalize_text(value: Any) -> str:
    text = clean_text(value).lower()
    text = re.sub(r"\s+", " ", text)
    return text


def unique_list(items: List[Any]) -> List[Any]:
    result = []
    seen = set()

    for item in items:
        key = normalize_text(item)

        if not key or key in seen:
            continue

        seen.add(key)
        result.append(item)

    return result


# ============================================================
# DEFAULT MEMORY
# ============================================================

def default_memory() -> Dict[str, Any]:
    """
    Memory structure intentionally mirrors the structure expected
    by main.py and the browser application.

    CORE:
        Stable preferences.

    MOMENT:
        What matters today.

    PREFERENCES:
        Additional explicit preferences.

    DISLIKES:
        Things MIRROR should avoid.

    HISTORY:
        Local interaction history.

    LEARNING:
        Feedback-derived behavioral signals.
    """

    return {
        "core": {},
        "moment": {},
        "preferences": {},
        "dislikes": [],
        "history": [],
        "learning": {},
    }


def normalize_memory(memory: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    base = default_memory()

    if not isinstance(memory, dict):
        return base

    for key in base:
        value = memory.get(key)

        if key in ("core", "moment", "preferences", "learning"):
            if isinstance(value, dict):
                base[key] = deepcopy(value)

        elif key in ("dislikes", "history"):
            if isinstance(value, list):
                base[key] = deepcopy(value)

    return base


# ============================================================
# INTENT TAXONOMY
# ============================================================

INTENTS = {
    "TRAVEL",
    "ACCOMMODATION",
    "DINING",
    "TRANSPORT",
    "PRIVATE_LIFE",
    "EXPERIENCE",
    "ESCAPE",
    "WELLBEING",
    "CONCIERGE",
    "UNKNOWN",
}


INTENT_KEYWORDS = {
    "ACCOMMODATION": [
        "hotel",
        "resort",
        "villa",
        "suite",
        "penthouse",
        "room",
        "stay",
        "hospedaje",
        "alojamiento",
        "habitación",
        "habitacion",
    ],
    "DINING": [
        "restaurant",
        "restaurante",
        "dinner",
        "cena",
        "lunch",
        "almuerzo",
        "chef",
        "private dining",
        "dining",
        "food",
        "comida",
        "wine",
        "vino",
        "bar",
        "menu",
    ],
    "TRANSPORT": [
        "driver",
        "chauffeur",
        "car",
        "vehicle",
        "transport",
        "airport transfer",
        "transfer",
        "limousine",
        "limo",
        "conductor",
        "chofer",
        "transporte",
        "auto",
    ],
    "TRAVEL": [
        "travel",
        "trip",
        "flight",
        "fly",
        "airport",
        "airline",
        "vacation",
        "holiday",
        "viaje",
        "vuelo",
        "aeropuerto",
        "vacaciones",
    ],
    "EXPERIENCE": [
        "experience",
        "excursion",
        "tour",
        "concert",
        "show",
        "event",
        "yacht",
        "boat",
        "spa",
        "museum",
        "gallery",
        "experience",
        "experiencia",
        "excursión",
        "excursion",
        "evento",
        "yate",
        "barco",
        "concierto",
        "show",
    ],
    "PRIVATE_LIFE": [
        "private",
        "personal",
        "family",
        "birthday",
        "anniversary",
        "gift",
        "surprise",
        "celebration",
        "celebrate",
        "familia",
        "cumpleaños",
        "cumpleanos",
        "aniversario",
        "regalo",
        "sorpresa",
        "celebración",
        "celebracion",
    ],
    "ESCAPE": [
        "escape",
        "getaway",
        "disconnect",
        "quiet",
        "retreat",
        "hideaway",
        "escape",
        "escapada",
        "desconectar",
        "tranquilo",
        "retiro",
        "refugio",
    ],
    "WELLBEING": [
        "relax",
        "relaxing",
        "rest",
        "peace",
        "calm",
        "stress",
        "sleep",
        "wellness",
        "relaj",
        "descans",
        "paz",
        "calma",
        "estrés",
        "estres",
        "dormir",
        "bienestar",
    ],
    "CONCIERGE": [
        "concierge",
        "handle this",
        "take care",
        "arrange",
        "organize",
        "find",
        "help me",
        "book",
        "reserve",
        "coordinate",
        "encárgate",
        "encargate",
        "organiza",
        "coordina",
        "ayúdame",
        "ayudame",
        "reserva",
        "buscar",
    ],
}


# ============================================================
# PRIORITY
# ============================================================

HIGH_PRIORITY_TERMS = [
    "urgent",
    "urgently",
    "asap",
    "right now",
    "immediately",
    "tonight",
    "today",
    "emergency",
    "deadline",
    "ahora",
    "urgente",
    "inmediatamente",
    "esta noche",
    "hoy",
    "emergencia",
    "último minuto",
    "ultimo minuto",
]


def detect_priority(text: str) -> str:
    normalized = normalize_text(text)

    for term in HIGH_PRIORITY_TERMS:
        if term in normalized:
            return "HIGH"

    return "NORMAL"


# ============================================================
# PRIVACY
# ============================================================

PRIVACY_TERMS = [
    "private",
    "privacy",
    "discreet",
    "discretion",
    "confidential",
    "anonymous",
    "quiet",
    "no publicity",
    "no photos",
    "exclusive",
    "privado",
    "privacidad",
    "discreto",
    "discreción",
    "confidencial",
    "anónimo",
    "sin publicidad",
    "sin fotos",
    "exclusivo",
]


def detect_privacy(text: str, memory: Dict[str, Any]) -> str:
    normalized = normalize_text(text)

    for term in PRIVACY_TERMS:
        if term in normalized:
            return "HIGH"

    core = memory.get("core", {})
    preferences = memory.get("preferences", {})

    values = [
        core.get("privacy"),
        core.get("privacy_level"),
        preferences.get("privacy"),
        preferences.get("privacy_level"),
    ]

    for value in values:
        if normalize_text(value) in {
            "high",
            "maximum",
            "max",
            "private",
            "very private",
            "alto",
            "máxima",
            "maxima",
        }:
            return "HIGH"

    return "NORMAL"


# ============================================================
# BUDGET
# ============================================================

BUDGET_PATTERNS = [
    r"\$\s?(\d[\d,]*(?:\.\d+)?)",
    r"(\d[\d,]*(?:\.\d+)?)\s?(?:usd|dollars|dólares|dolares)",
    r"(?:budget|presupuesto)\s*(?:of|de)?\s*\$?\s?(\d[\d,]*(?:\.\d+)?)",
]


def extract_budget(text: str) -> Optional[float]:
    for pattern in BUDGET_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)

        if not match:
            continue

        try:
            value = match.group(1).replace(",", "")
            return float(value)
        except (TypeError, ValueError):
            continue

    return None


# ============================================================
# DESTINATION / PLACE EXTRACTION
# ============================================================

DESTINATION_PATTERNS = [
    r"\b(?:to|in|near|around|from)\s+([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s'-]{2,50})",
    r"\b(?:a|en|cerca de|desde)\s+([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s'-]{2,50})",
]


STOP_WORDS = {
    "for",
    "with",
    "this",
    "that",
    "tomorrow",
    "today",
    "tonight",
    "next",
    "week",
    "weeks",
    "days",
    "people",
    "person",
    "me",
    "my",
    "the",
    "un",
    "una",
    "unos",
    "unas",
    "para",
    "con",
    "hoy",
    "mañana",
    "manana",
    "esta",
    "este",
    "próxima",
    "proxima",
}


def extract_destination(text: str) -> Optional[str]:
    for pattern in DESTINATION_PATTERNS:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)

        for match in matches:
            candidate = clean_text(match)
            words = candidate.split()

            while words and normalize_text(words[-1]) in STOP_WORDS:
                words.pop()

            candidate = " ".join(words).strip(" .,!?;:")

            if len(candidate) >= 3:
                return candidate

    return None


# ============================================================
# PEOPLE / COMPANIONS
# ============================================================

def extract_people(text: str) -> Optional[int]:
    patterns = [
        r"\bfor\s+(\d+)\s+(?:people|persons|guests)\b",
        r"\b(\d+)\s+(?:people|persons|guests)\b",
        r"\bpara\s+(\d+)\s+(?:personas|personas)\b",
        r"\b(\d+)\s+personas\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass

    return None


# ============================================================
# DATE / TIME SIGNALS
# ============================================================

DATE_SIGNALS = [
    "today",
    "tomorrow",
    "tonight",
    "this weekend",
    "next weekend",
    "next week",
    "this week",
    "hoy",
    "mañana",
    "manana",
    "esta noche",
    "este fin de semana",
    "próximo fin de semana",
    "proximo fin de semana",
    "la próxima semana",
    "la proxima semana",
]


def detect_time_signal(text: str) -> Optional[str]:
    normalized = normalize_text(text)

    for signal in DATE_SIGNALS:
        if signal in normalized:
            return signal

    return None


# ============================================================
# INTENT DETECTION
# ============================================================

def detect_intent(text: str) -> str:
    normalized = normalize_text(text)

    scores: Dict[str, int] = {
        intent: 0 for intent in INTENTS
    }

    for intent, keywords in INTENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in normalized:
                scores[intent] += 1

    best_intent = max(scores, key=scores.get)

    if scores[best_intent] == 0:
        return "UNKNOWN"

    return best_intent


# ============================================================
# REQUEST UNDERSTANDING
# ============================================================

def understand_request(
    message: str,
    memory: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:

    text = clean_text(message)
    normalized = normalize_text(text)
    memory_data = normalize_memory(memory)

    intent = detect_intent(text)
    priority = detect_priority(text)
    privacy = detect_privacy(text, memory_data)
    budget = extract_budget(text)
    destination = extract_destination(text)
    people = extract_people(text)
    time_signal = detect_time_signal(text)

    return {
        "raw_message": text,
        "normalized_message": normalized,
        "intent": intent,
        "priority": priority,
        "privacy": privacy,
        "budget": budget,
        "destination": destination,
        "people": people,
        "time_signal": time_signal,
        "language_hint": detect_language_hint(text),
        "requires_clarification": requires_clarification(
            intent=intent,
            message=text,
        ),
    }


def detect_language_hint(text: str) -> str:
    normalized = normalize_text(text)

    spanish_markers = [
        "quiero",
        "necesito",
        "para",
        "con",
        "en",
        "una",
        "un",
        "me gustaría",
        "me gustaria",
        "puedes",
        "ayúdame",
        "ayudame",
    ]

    english_markers = [
        "i want",
        "i need",
        "for",
        "with",
        "in",
        "a",
        "an",
        "i would like",
        "can you",
        "help me",
    ]

    spanish_score = sum(
        1 for marker in spanish_markers if marker in normalized
    )

    english_score = sum(
        1 for marker in english_markers if marker in normalized
    )

    if spanish_score > english_score:
        return "es"

    if english_score > spanish_score:
        return "en"

    return "en"


def requires_clarification(
    intent: str,
    message: str,
) -> bool:

    if not clean_text(message):
        return True

    if intent == "UNKNOWN":
        return len(normalize_text(message).split()) < 5

    return False


# ============================================================
# MEMORY SIGNALS
# ============================================================

def memory_value(
    memory: Dict[str, Any],
    *keys: str,
) -> Any:

    for section_name in (
        "core",
        "preferences",
        "moment",
        "learning",
    ):
        section = memory.get(section_name, {})

        if not isinstance(section, dict):
            continue

        for key in keys:
            value = section.get(key)

            if value not in (None, "", [], {}):
                return value

    return None


def get_avoid_rules(memory: Dict[str, Any]) -> List[str]:
    dislikes = memory.get("dislikes", [])

    if not isinstance(dislikes, list):
        return []

    return unique_list(dislikes)


def get_history(memory: Dict[str, Any]) -> List[Any]:
    history = memory.get("history", [])

    if not isinstance(history, list):
        return []

    return history


# ============================================================
# PERSONALIZATION
# ============================================================

def personalize_request(
    understanding: Dict[str, Any],
    memory: Optional[Dict[str, Any]],
) -> Dict[str, Any]:

    memory_data = normalize_memory(memory)

    personalization = {
        "travel_style": memory_value(
            memory_data,
            "travel_style",
            "travelStyle",
        ),
        "hotel_style": memory_value(
            memory_data,
            "hotel_style",
            "accommodation_style",
        ),
        "dining_style": memory_value(
            memory_data,
            "dining_style",
            "food_style",
        ),
        "luxury_level": memory_value(
            memory_data,
            "luxury_level",
            "luxury",
        ),
        "privacy_level": memory_value(
            memory_data,
            "privacy_level",
            "privacy",
        ),
        "preferred_destinations": memory_value(
            memory_data,
            "preferred_destinations",
            "favorite_destinations",
        ),
        "preferred_airlines": memory_value(
            memory_data,
            "preferred_airlines",
            "airlines",
        ),
        "preferred_hotels": memory_value(
            memory_data,
            "preferred_hotels",
            "favorite_hotels",
        ),
        "food_preferences": memory_value(
            memory_data,
            "food_preferences",
            "diet",
            "cuisine_preferences",
        ),
        "companions": memory_value(
            memory_data,
            "companions",
            "travel_companions",
        ),
        "avoid": get_avoid_rules(memory_data),
        "recent_history": get_history(memory_data)[-10:],
    }

    return personalization


# ============================================================
# DECISION SCORING
# ============================================================

def score_option(
    option: Dict[str, Any],
    understanding: Dict[str, Any],
    memory: Optional[Dict[str, Any]] = None,
) -> float:

    memory_data = normalize_memory(memory)

    score = 50.0

    option_text = normalize_text(
        " ".join(
            str(option.get(key, ""))
            for key in (
                "name",
                "description",
                "style",
                "category",
                "destination",
            )
        )
    )

    # --------------------------------------------------------
    # Privacy
    # --------------------------------------------------------

    if understanding.get("privacy") == "HIGH":
        privacy_level = normalize_text(
            option.get("privacy_level", "")
        )

        if privacy_level in {
            "high",
            "maximum",
            "max",
            "private",
            "exclusive",
        }:
            score += 15

        elif privacy_level in {
            "low",
            "public",
        }:
            score -= 15

    # --------------------------------------------------------
    # Luxury
    # --------------------------------------------------------

    luxury = normalize_text(
        memory_value(
            memory_data,
            "luxury_level",
            "luxury",
        )
    )

    if luxury in {"high", "luxury", "premium", "ultra", "maximum"}:
        option_luxury = normalize_text(
            option.get("luxury_level", "")
        )

        if option_luxury in {
            "high",
            "luxury",
            "premium",
            "ultra",
            "maximum",
        }:
            score += 12

    # --------------------------------------------------------
    # Destination
    # --------------------------------------------------------

    requested_destination = normalize_text(
        understanding.get("destination")
    )

    option_destination = normalize_text(
        option.get("destination")
    )

    if requested_destination and option_destination:
        if (
            requested_destination in option_destination
            or option_destination in requested_destination
        ):
            score += 20

    # --------------------------------------------------------
    # Budget
    # --------------------------------------------------------

    budget = understanding.get("budget")
    option_price = option.get("price")

    if isinstance(budget, (int, float)) and isinstance(
        option_price,
        (int, float),
    ):
        if option_price <= budget:
            score += 10
        else:
            score -= min(
                20,
                ((option_price - budget) / max(budget, 1)) * 20,
            )

    # --------------------------------------------------------
    # Avoid rules
    # --------------------------------------------------------

    for avoid in get_avoid_rules(memory_data):
        if normalize_text(avoid) in option_text:
            score -= 25

    # --------------------------------------------------------
    # History / repetition
    # --------------------------------------------------------

    recent_history = get_history(memory_data)

    for previous in recent_history[-10:]:
        if not isinstance(previous, dict):
            continue

        previous_name = normalize_text(
            previous.get("name")
            or previous.get("title")
            or previous.get("destination")
        )

        option_name = normalize_text(
            option.get("name")
            or option.get("title")
            or option.get("destination")
        )

        if previous_name and option_name:
            if previous_name == option_name:
                score -= 8

    return round(max(0.0, min(100.0, score)), 2)


# ============================================================
# PLAN GENERATION
# ============================================================

def build_personalized_plan(
    understanding: Dict[str, Any],
    memory: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:

    memory_data = normalize_memory(memory)
    intent = understanding.get("intent", "UNKNOWN")
    destination = understanding.get("destination")
    budget = understanding.get("budget")
    priority = understanding.get("priority", "NORMAL")
    privacy = understanding.get("privacy", "NORMAL")

    personalization = personalize_request(
        understanding,
        memory_data,
    )

    plan_style = personalization.get("travel_style")

    if intent == "ACCOMMODATION":
        title = "A private stay designed around you."
        category = "ACCOMMODATION"

    elif intent == "DINING":
        title = "A dining experience selected for your moment."
        category = "DINING"

    elif intent == "TRANSPORT":
        title = "A seamless private transportation plan."
        category = "TRANSPORT"

    elif intent == "TRAVEL":
        title = "A travel plan designed around your preferences."
        category = "TRAVEL"

    elif intent == "EXPERIENCE":
        title = "An experience chosen for the way you want to feel."
        category = "EXPERIENCE"

    elif intent == "PRIVATE_LIFE":
        title = "A private-life arrangement handled with discretion."
        category = "PRIVATE_LIFE"

    elif intent == "ESCAPE":
        title = "A private escape designed for this moment."
        category = "ESCAPE"

    elif intent == "WELLBEING":
        title = "A calmer plan for the moment you are in."
        category = "WELLBEING"

    else:
        title = "A personalized MIRROR plan."
        category = "CONCIERGE"

    steps = []

    if destination:
        steps.append(
            f"Use {destination} as the geographic focus."
        )
    else:
        steps.append(
            "Identify the best geographic option from your preferences."
        )

    if plan_style:
        steps.append(
            f"Prioritize your {plan_style} preference."
        )
    else:
        steps.append(
            "Apply your known preferences before considering generic options."
        )

    if privacy == "HIGH":
        steps.append(
            "Prioritize discretion, privacy and low-friction coordination."
        )

    if budget:
        steps.append(
            f"Keep the proposal aligned with the stated budget of ${budget:,.0f}."
        )

    if priority == "HIGH":
        steps.append(
            "Treat this as a priority request and minimize unnecessary steps."
        )

    steps.append(
        "Present the strongest option first instead of overwhelming you with choices."
    )

    steps.append(
        "Move to Concierge or a real provider connection when actual execution is required."
    )

    return {
        "title": title,
        "category": category,
        "privacy": privacy,
        "priority": priority,
        "budget": budget,
        "destination": destination,
        "steps": steps,
        "personalization": personalization,
        "status": "PROPOSAL",
        "execution_available": False,
        "verification_required": True,
        "provider_connection_required": True,
    }


# ============================================================
# CLARIFICATION
# ============================================================

def clarification_questions(
    understanding: Dict[str, Any],
) -> List[str]:

    questions = []

    intent = understanding.get("intent")

    if intent == "UNKNOWN":
        questions.append(
            "Tell me what you would like me to take care of."
        )

    if not understanding.get("destination") and intent in {
        "TRAVEL",
        "ACCOMMODATION",
        "DINING",
        "TRANSPORT",
        "EXPERIENCE",
        "ESCAPE",
    }:
        questions.append(
            "Where would you like this to happen, if you have a place in mind?"
        )

    if not understanding.get("time_signal") and intent in {
        "TRAVEL",
        "ACCOMMODATION",
        "DINING",
        "TRANSPORT",
        "EXPERIENCE",
    }:
        questions.append(
            "When would you like it?"
        )

    return questions


# ============================================================
# CONCIERGE DECISION
# ============================================================

def concierge_required(
    understanding: Dict[str, Any],
    plan: Dict[str, Any],
) -> Tuple[bool, List[str]]:

    reasons = []

    intent = understanding.get("intent")
    priority = understanding.get("priority")
    privacy = understanding.get("privacy")

    if priority == "HIGH":
        reasons.append(
            "The request has elevated urgency."
        )

    if privacy == "HIGH":
        reasons.append(
            "The request benefits from additional discretion."
        )

    if intent in {
        "PRIVATE_LIFE",
        "EXPERIENCE",
        "TRANSPORT",
    }:
        reasons.append(
            "The request may require real-world coordination."
        )

    if plan.get("provider_connection_required"):
        reasons.append(
            "Actual execution requires a verified provider connection."
        )

    return bool(reasons), reasons


# ============================================================
# RESPONSE GENERATION
# ============================================================

def generate_response(
    understanding: Dict[str, Any],
    plan: Dict[str, Any],
    language: str = "en",
) -> str:

    language = "es" if language == "es" else "en"

    destination = plan.get("destination")
    priority = plan.get("priority")
    privacy = plan.get("privacy")

    if language == "es":
        opening = "Entiendo lo que buscas."

        if destination:
            opening = (
                f"Entiendo lo que buscas y tomaré {destination} "
                "como punto de partida."
            )

        lines = [
            opening,
            "No quiero darte una lista interminable. "
            "Quiero reducir la decisión a lo que realmente encaja contigo.",
        ]

        if privacy == "HIGH":
            lines.append(
                "También priorizaré la discreción y la privacidad."
            )

        if priority == "HIGH":
            lines.append(
                "Lo trataré como una solicitud prioritaria."
            )

        lines.append(
            "He preparado un plan inicial. "
            "Si te gusta la dirección, MIRROR puede llevarlo al siguiente paso."
        )

        lines.append(
            "Para una reserva, compra o coordinación real, "
            "necesitaremos una conexión con el proveedor correspondiente "
            "o la intervención de Concierge."
        )

        return " ".join(lines)

    opening = "I understand what you are looking for."

    if destination:
        opening = (
            f"I understand what you are looking for, "
            f"and I will use {destination} as the starting point."
        )

    lines = [
        opening,
        "I do not want to overwhelm you with a list. "
        "I want to narrow the decision to what actually fits you.",
    ]

    if privacy == "HIGH":
        lines.append(
            "I will also prioritize discretion and privacy."
        )

    if priority == "HIGH":
        lines.append(
            "I will treat this as a priority request."
        )

    lines.append(
        "I have prepared an initial plan. "
        "If the direction feels right, MIRROR can take it to the next step."
    )

    lines.append(
        "For a real booking, purchase or coordination, "
        "MIRROR will need a verified provider connection "
        "or Concierge assistance."
    )

    return " ".join(lines)


# ============================================================
# MEMORY LEARNING
# ============================================================

def generate_memory_update(
    understanding: Dict[str, Any],
    feedback: Optional[str] = None,
) -> Dict[str, Any]:

    update: Dict[str, Any] = {
        "moment": {},
        "preferences": {},
        "dislikes": [],
        "learning": {},
    }

    intent = understanding.get("intent")
    destination = understanding.get("destination")
    privacy = understanding.get("privacy")
    priority = understanding.get("priority")
    budget = understanding.get("budget")

    if intent and intent != "UNKNOWN":
        update["moment"]["last_intent"] = intent

    if destination:
        update["moment"]["last_destination"] = destination

    if privacy == "HIGH":
        update["preferences"]["privacy_level"] = "high"

    if priority == "HIGH":
        update["moment"]["priority"] = "high"

    if budget:
        update["moment"]["last_budget"] = budget

    if feedback:
        normalized_feedback = normalize_text(feedback)

        update["learning"]["last_feedback"] = feedback

        positive_terms = [
            "right",
            "love",
            "perfect",
            "great",
            "yes",
            "good",
            "like",
            "correct",
            "bien",
            "perfecto",
            "me gusta",
            "sí",
            "si",
        ]

        negative_terms = [
            "no",
            "wrong",
            "bad",
            "hate",
            "different",
            "not this",
            "incorrect",
            "malo",
            "diferente",
            "no me gusta",
            "incorrecto",
        ]

        if any(term in normalized_feedback for term in positive_terms):
            update["learning"]["last_feedback_signal"] = "POSITIVE"

        elif any(term in normalized_feedback for term in negative_terms):
            update["learning"]["last_feedback_signal"] = "NEGATIVE"

    return update


def merge_memory(
    memory: Optional[Dict[str, Any]],
    update: Optional[Dict[str, Any]],
) -> Dict[str, Any]:

    base = normalize_memory(memory)

    if not isinstance(update, dict):
        return base

    for section in (
        "core",
        "moment",
        "preferences",
        "learning",
    ):
        incoming = update.get(section)

        if not isinstance(incoming, dict):
            continue

        if not isinstance(base.get(section), dict):
            base[section] = {}

        base[section].update(deepcopy(incoming))

    incoming_dislikes = update.get("dislikes")

    if isinstance(incoming_dislikes, list):
        base["dislikes"] = unique_list(
            base.get("dislikes", []) + incoming_dislikes
        )

    incoming_history = update.get("history")

    if isinstance(incoming_history, list):
        base["history"] = (
            base.get("history", []) + deepcopy(incoming_history)
        )[-100:]

    return base


# ============================================================
# HISTORY EVENT
# ============================================================

def create_history_event(
    understanding: Dict[str, Any],
    plan: Optional[Dict[str, Any]] = None,
    feedback: Optional[str] = None,
) -> Dict[str, Any]:

    return {
        "timestamp": now_iso(),
        "intent": understanding.get("intent"),
        "destination": understanding.get("destination"),
        "priority": understanding.get("priority"),
        "privacy": understanding.get("privacy"),
        "budget": understanding.get("budget"),
        "plan_title": (
            plan.get("title")
            if isinstance(plan, dict)
            else None
        ),
        "feedback": feedback,
    }


# ============================================================
# COMPLETE MIRROR ANALYSIS
# ============================================================

def analyze(
    message: str,
    memory: Optional[Dict[str, Any]] = None,
    language: str = "en",
) -> Dict[str, Any]:

    memory_data = normalize_memory(memory)

    understanding = understand_request(
        message,
        memory_data,
    )

    personalization = personalize_request(
        understanding,
        memory_data,
    )

    plan = build_personalized_plan(
        understanding,
        memory_data,
    )

    clarification = clarification_questions(
        understanding
    )

    needs_concierge, concierge_reasons = concierge_required(
        understanding,
        plan,
    )

    response = generate_response(
        understanding,
        plan,
        language,
    )

    memory_update = generate_memory_update(
        understanding
    )

    history_event = create_history_event(
        understanding,
        plan,
    )

    memory_update["history"] = [history_event]

    return {
        "engine": ENGINE_NAME,
        "engine_version": ENGINE_VERSION,
        "timestamp": now_iso(),
        "understanding": understanding,
        "personalization": personalization,
        "plan": plan,
        "response": response,
        "clarification_questions": clarification,
        "needs_clarification": bool(clarification),
        "concierge": {
            "required": needs_concierge,
            "reasons": concierge_reasons,
        },
        "memory_update": memory_update,
        "execution": {
            "status": "NOT_EXECUTED",
            "verified": False,
            "provider_connected": False,
        },
    }


# ============================================================
# PLAN REVISION
# ============================================================

def revise_plan(
    plan: Dict[str, Any],
    revision: str,
    memory: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:

    revised = deepcopy(plan)
    memory_data = normalize_memory(memory)

    instruction = normalize_text(revision)

    if not instruction:
        return revised

    # --------------------------------------------------------
    # More private
    # --------------------------------------------------------

    if any(
        term in instruction
        for term in (
            "more private",
            "more discreet",
            "more exclusive",
            "más privado",
            "mas privado",
            "más discreto",
            "mas discreto",
            "más exclusivo",
            "mas exclusivo",
        )
    ):
        revised["privacy"] = "HIGH"

        revised["steps"].insert(
            0,
            "Increase discretion and prioritize private or low-profile options."
        )

    # --------------------------------------------------------
    # More luxurious
    # --------------------------------------------------------

    if any(
        term in instruction
        for term in (
            "luxury",
            "luxurious",
            "premium",
            "upscale",
            "más lujo",
            "mas lujo",
            "lujoso",
            "premium",
        )
    ):
        revised["steps"].insert(
            0,
            "Raise the service level and prioritize premium options."
        )

        revised["personalization"]["luxury_level"] = "high"

    # --------------------------------------------------------
    # Simpler
    # --------------------------------------------------------

    if any(
        term in instruction
        for term in (
            "simpler",
            "simple",
            "easier",
            "less complicated",
            "más simple",
            "mas simple",
            "más fácil",
            "mas facil",
            "menos complicado",
        )
    ):
        revised["steps"] = [
            step
            for step in revised["steps"]
            if "generic" not in normalize_text(step)
        ]

        revised["steps"].append(
            "Keep the final experience simple and frictionless."
        )

    # --------------------------------------------------------
    # Different
    # --------------------------------------------------------

    if any(
        term in instruction
        for term in (
            "different",
            "surprise me",
            "something else",
            "diferente",
            "sorpréndeme",
            "sorprendeme",
            "otra cosa",
        )
    ):
        revised["variation_requested"] = True

        revised["steps"].insert(
            0,
            "Avoid repeating recent choices and search for a meaningfully different direction."
        )

    # --------------------------------------------------------
    # Preserve avoidance rules
    # --------------------------------------------------------

    revised["avoid"] = get_avoid_rules(memory_data)

    revised["status"] = "REVISED"

    return revised


# ============================================================
# FEEDBACK PROCESSING
# ============================================================

def process_feedback(
    understanding: Dict[str, Any],
    feedback: str,
    memory: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:

    normalized = normalize_text(feedback)

    positive = any(
        term in normalized
        for term in (
            "yes",
            "right",
            "perfect",
            "great",
            "love",
            "like",
            "good",
            "sí",
            "si",
            "correcto",
            "perfecto",
            "me gusta",
            "bien",
        )
    )

    negative = any(
        term in normalized
        for term in (
            "no",
            "wrong",
            "different",
            "bad",
            "hate",
            "not this",
            "diferente",
            "malo",
            "no me gusta",
            "incorrecto",
        )
    )

    if positive and not negative:
        signal = "POSITIVE"

    elif negative and not positive:
        signal = "NEGATIVE"

    else:
        signal = "NEUTRAL"

    update = generate_memory_update(
        understanding,
        feedback,
    )

    return {
        "signal": signal,
        "feedback": feedback,
        "memory_update": update,
        "learning": {
            "intent": understanding.get("intent"),
            "signal": signal,
            "timestamp": now_iso(),
        },
    }


# ============================================================
# MISSION STATE MACHINE
# ============================================================

MISSION_STATES = [
    "NEW",
    "UNDERSTANDING",
    "PLANNING",
    "PROPOSAL",
    "CLIENT_APPROVAL",
    "EXECUTION",
    "COMPLETED",
    "LEARNING",
]


ALLOWED_TRANSITIONS = {
    "NEW": {"UNDERSTANDING"},
    "UNDERSTANDING": {"PLANNING"},
    "PLANNING": {"PROPOSAL"},
    "PROPOSAL": {
        "CLIENT_APPROVAL",
        "PLANNING",
    },
    "CLIENT_APPROVAL": {
        "EXECUTION",
        "PLANNING",
    },
    "EXECUTION": {
        "COMPLETED",
    },
    "COMPLETED": {
        "LEARNING",
    },
    "LEARNING": set(),
}


def can_transition(
    current_state: str,
    new_state: str,
) -> bool:

    if current_state == new_state:
        return True

    allowed = ALLOWED_TRANSITIONS.get(
        current_state,
        set(),
    )

    return new_state in allowed


def transition_mission(
    mission: Dict[str, Any],
    new_state: str,
) -> Dict[str, Any]:

    current_state = mission.get(
        "status",
        "NEW",
    )

    if not can_transition(
        current_state,
        new_state,
    ):
        raise ValueError(
            f"Invalid mission transition: "
            f"{current_state} -> {new_state}"
        )

    updated = deepcopy(mission)

    updated["status"] = new_state
    updated["updated_at"] = now_iso()

    return updated


# ============================================================
# EXECUTION SAFETY
# ============================================================

def execution_status(
    *,
    provider_connected: bool = False,
    provider_verified: bool = False,
    client_approved: bool = False,
) -> Dict[str, Any]:

    if not client_approved:
        return {
            "status": "AWAITING_CLIENT_APPROVAL",
            "verified": False,
            "executed": False,
        }

    if not provider_connected:
        return {
            "status": "REQUIRES_PROVIDER",
            "verified": False,
            "executed": False,
        }

    if not provider_verified:
        return {
            "status": "REQUIRES_PROVIDER_VERIFICATION",
            "verified": False,
            "executed": False,
        }

    return {
        "status": "READY_FOR_EXECUTION",
        "verified": True,
        "executed": False,
    }


# ============================================================
# MEMORY RECOVERY
# ============================================================

RECOVERY_QUESTIONS = [
    {
        "id": "travel_style",
        "question_en": "When you travel, what feels most like you?",
        "question_es": "Cuando viajas, ¿qué se siente más como tú?",
        "options": [
            {
                "value": "quiet_luxury",
                "en": "Quiet luxury",
                "es": "Lujo discreto",
            },
            {
                "value": "adventure",
                "en": "Adventure",
                "es": "Aventura",
            },
            {
                "value": "culture",
                "en": "Culture",
                "es": "Cultura",
            },
            {
                "value": "relaxation",
                "en": "Complete relaxation",
                "es": "Relajación total",
            },
        ],
    },
    {
        "id": "privacy_level",
        "question_en": "How important is privacy to you?",
        "question_es": "¿Qué importancia tiene la privacidad para ti?",
        "options": [
            {
                "value": "normal",
                "en": "Important",
                "es": "Importante",
            },
            {
                "value": "high",
                "en": "Very important",
                "es": "Muy importante",
            },
            {
                "value": "maximum",
                "en": "Non-negotiable",
                "es": "No negociable",
            },
        ],
    },
    {
        "id": "luxury_level",
        "question_en": "What level of service feels right?",
        "question_es": "¿Qué nivel de servicio se siente correcto?",
        "options": [
            {
                "value": "comfortable",
                "en": "Comfortable",
                "es": "Cómodo",
            },
            {
                "value": "premium",
                "en": "Premium",
                "es": "Premium",
            },
            {
                "value": "luxury",
                "en": "Luxury",
                "es": "Lujo",
            },
            {
                "value": "ultra",
                "en": "Exceptional",
                "es": "Excepcional",
            },
        ],
    },
    {
        "id": "dining_style",
        "question_en": "What kind of dining usually attracts you?",
        "question_es": "¿Qué tipo de gastronomía suele atraerte?",
        "options": [
            {
                "value": "fine_dining",
                "en": "Fine dining",
                "es": "Alta gastronomía",
            },
            {
                "value": "local",
                "en": "Authentic local",
                "es": "Local auténtica",
            },
            {
                "value": "private",
                "en": "Private dining",
                "es": "Dining privado",
            },
            {
                "value": "casual",
                "en": "Relaxed and casual",
                "es": "Relajado e informal",
            },
        ],
    },
    {
        "id": "experience_style",
        "question_en": "What would make an experience memorable for you?",
        "question_es": "¿Qué haría memorable una experiencia para ti?",
        "options": [
            {
                "value": "exclusivity",
                "en": "Exclusivity",
                "es": "Exclusividad",
            },
            {
                "value": "beauty",
                "en": "Beauty",
                "es": "Belleza",
            },
            {
                "value": "discovery",
                "en": "Discovery",
                "es": "Descubrimiento",
            },
            {
                "value": "connection",
                "en": "Connection",
                "es": "Conexión",
            },
        ],
    },
]


def get_recovery_questions(
    language: str = "en",
) -> List[Dict[str, Any]]:

    lang = "es" if language == "es" else "en"

    result = []

    for question in RECOVERY_QUESTIONS:
        result.append(
            {
                "id": question["id"],
                "question": question[
                    f"question_{lang}"
                ],
                "options": [
                    {
                        "value": option["value"],
                        "label": option[lang],
                    }
                    for option in question["options"]
                ],
            }
        )

    return result


def recover_memory(
    answers: Dict[str, Any],
    existing_memory: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:

    memory = normalize_memory(
        existing_memory
    )

    if not isinstance(answers, dict):
        return memory

    for question_id, answer in answers.items():

        if not answer:
            continue

        if question_id == "travel_style":
            memory["core"]["travel_style"] = answer

        elif question_id == "privacy_level":
            memory["core"]["privacy_level"] = answer

        elif question_id == "luxury_level":
            memory["core"]["luxury_level"] = answer

        elif question_id == "dining_style":
            memory["core"]["dining_style"] = answer

        elif question_id == "experience_style":
            memory["core"]["experience_style"] = answer

    memory["learning"]["memory_recovery_at"] = now_iso()

    return memory


# ============================================================
# ENGINE PUBLIC API
# ============================================================

class MirrorEngine:
    """
    Object-oriented wrapper around the MIRROR engine.

    The class does not own permanent personal memory.
    Memory is supplied by the client application for each request.
    """

    name = ENGINE_NAME
    version = ENGINE_VERSION

    def analyze(
        self,
        message: str,
        memory: Optional[Dict[str, Any]] = None,
        language: str = "en",
    ) -> Dict[str, Any]:

        return analyze(
            message=message,
            memory=memory,
            language=language,
        )

    def revise(
        self,
        plan: Dict[str, Any],
        revision: str,
        memory: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        return revise_plan(
            plan=plan,
            revision=revision,
            memory=memory,
        )

    def feedback(
        self,
        understanding: Dict[str, Any],
        feedback: str,
        memory: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        return process_feedback(
            understanding=understanding,
            feedback=feedback,
            memory=memory,
        )

    def recover(
        self,
        answers: Dict[str, Any],
        existing_memory: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        return recover_memory(
            answers=answers,
            existing_memory=existing_memory,
        )

    def recovery_questions(
        self,
        language: str = "en",
    ) -> List[Dict[str, Any]]:

        return get_recovery_questions(
            language=language,
        )

    def transition(
        self,
        mission: Dict[str, Any],
        new_state: str,
    ) -> Dict[str, Any]:

        return transition_mission(
            mission=mission,
            new_state=new_state,
        )


mirror = MirrorEngine()


__all__ = [
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "INTENTS",
    "MISSION_STATES",
    "MirrorEngine",
    "mirror",
    "default_memory",
    "normalize_memory",
    "understand_request",
    "personalize_request",
    "score_option",
    "build_personalized_plan",
    "clarification_questions",
    "concierge_required",
    "generate_response",
    "generate_memory_update",
    "merge_memory",
    "create_history_event",
    "analyze",
    "revise_plan",
    "process_feedback",
    "can_transition",
    "transition_mission",
    "execution_status",
    "get_recovery_questions",
    "recover_memory",
]
```
