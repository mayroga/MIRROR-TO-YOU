import os
import json
import re
import urllib.request
import urllib.error
from datetime import datetime, timezone


OPENAI_KEY = os.getenv("OPENAI_API_KEY", "").strip()
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "").strip()

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

TIMEOUT = int(os.getenv("MIRROR_AI_TIMEOUT", "18"))


def now():
    return datetime.now(timezone.utc).isoformat()


def clean(value, default=None):
    if value is None:
        return default
    if isinstance(value, str):
        value = value.strip()
        return value or default
    return value


def language_of(text):
    t = (text or "").lower()
    spanish = re.search(
        r"\b(quiero|necesito|hoy|mañana|viaje|hotel|solo|sola|"
        r"descansar|escaparme|comida|silencio|tranquilo|días|"
        r"qué|como|dónde|hacer|buscar|ayuda)\b",
        t
    )
    return "es" if spanish else "en"


def normalize_memory(memory):
    memory = memory if isinstance(memory, dict) else {}
    return {
        "core": memory.get("core") or {},
        "moment": memory.get("moment") or {},
        "preferences": memory.get("preferences") or {},
        "dislikes": memory.get("dislikes") or [],
        "history": memory.get("history") or [],
        "learning": memory.get("learning") or {}
    }


def detect_signals(text):
    t = (text or "").lower()
    signals = []

    patterns = {
        "privacy": r"\b(privado|privacidad|private|privacy|nadie|alone|solo|sola)\b",
        "quiet": r"\b(silencio|tranquilo|tranquila|quiet|peaceful|calm|quieto)\b",
        "luxury": r"\b(lujo|lujoso|lujosa|luxury|exclusive|exclusivo|premium|elegante)\b",
        "nature": r"\b(naturaleza|nature|playa|beach|montaña|mountain|bosque|forest)\b",
        "water": r"\b(agua|water|mar|sea|océano|ocean|piscina|pool)\b",
        "food": r"\b(comida|gastronomía|gastronomia|restaurant|restaurante|food|dining|chef)\b",
        "music": r"\b(música|musica|music|canción|song)\b",
        "disconnect": r"\b(desconectar|desconexión|desconexion|disconnect|desaparecer|desaparezco|away)\b",
        "adventure": r"\b(aventura|adventure|explorar|explore|descubrir|discover)\b",
        "wellbeing": r"\b(respirar|breath|breathing|respiración|respiracion|relajar|relax|calma)\b",
        "spontaneous": r"\b(sorpresa|sorpréndeme|sorprendeme|surprise|spontaneous|espontáneo|espontaneo)\b"
    }

    for name, pattern in patterns.items():
        if re.search(pattern, t):
            signals.append(name)

    return signals


def detect_duration(text):
    t = (text or "").lower()

    m = re.search(r"\b(\d+)\s*(?:d[ií]a|d[ií]as|days?)\b", t)
    if m:
        return f"{m.group(1)} days"

    if "fin de semana" in t or "weekend" in t:
        return "weekend"

    if "una semana" in t or "one week" in t:
        return "one week"

    if "hoy" in t or "today" in t:
        return "today"

    return None


def detect_companion(text):
    t = (text or "").lower()

    if re.search(r"\bsolo\b|\bsola\b|\balone\b|\bby myself\b", t):
        return "alone"

    if re.search(r"\bpareja\b|\bpartner\b|\bspouse\b", t):
        return "partner"

    if re.search(r"\bfamilia\b|\bfamily\b|\bchildren\b|\bhijos\b", t):
        return "family"

    if re.search(r"\bamigos\b|\bamigas\b|\bfriends\b", t):
        return "friends"

    return None


def detect_budget(text):
    t = (text or "").lower()

    m = re.search(r"\$?\s?([\d,]+(?:\.\d+)?)", t)
    if m:
        try:
            return float(m.group(1).replace(",", ""))
        except Exception:
            pass

    if re.search(r"\b(sin límite|sin limite|no limit|whatever it costs)\b", t):
        return "flexible"

    if re.search(r"\b(barato|cheap|económico|economico|budget)\b", t):
        return "value"

    if re.search(r"\b(lujo|luxury|premium|exclusive|exclusivo)\b", t):
        return "premium"

    return None


def detect_destination(text):
    t = (text or "").strip()

    patterns = [
        r"\b(?:en|a|para|in|to)\s+([A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ' -]{2,40})",
        r"\b(?:near|cerca de)\s+([A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ' -]{2,40})"
    ]

    stop = {
        "quiero", "quieres", "necesito", "necesitas",
        "un", "una", "el", "la", "que", "para", "con",
        "this", "that", "something", "somewhere"
    }

    for pattern in patterns:
        match = re.search(pattern, t)
        if match:
            value = match.group(1).strip(" .,!?")
            words = value.split()
            if words and words[0].lower() not in stop:
                return value

    return None


def infer_intent(text):
    t = (text or "").lower()

    travel = re.search(
        r"\b(viaje|viajar|escapada|escaparme|hotel|resort|"
        r"trip|travel|escape|getaway|vacation|stay|destination)\b",
        t
    )

    dining = re.search(
        r"\b(restaurante|restaurant|cena|dinner|comida|food|chef|gastronomía|dining)\b",
        t
    )

    music = re.search(r"\b(música|musica|music|canción|song|youtube)\b", t)

    experience = re.search(
        r"\b(hacer algo|something to do|experiencia|experience|"
        r"actividad|activity|sorpresa|surprise|qué hago|what should i do)\b",
        t
    )

    if travel:
        if re.search(r"\b(desaparecer|disconnect|desconectar|quiet|silencio|nadie)\b", t):
            return "PRIVATE_ESCAPE"
        return "TRAVEL"

    if dining:
        return "DINING"

    if music:
        return "MUSIC"

    if experience:
        return "EXPERIENCE"

    if re.search(
        r"\b(cansado|cansada|agotado|agotada|tired|overwhelmed|"
        r"aburrido|aburrida|bored|estresado|estresada|stressed|"
        r"no sé|no se|i don't know|lost|perdido|perdida)\b",
        t
    ):
        return "MOMENT"

    return "CONVERSATION"


def understand_local(text):
    lang = language_of(text)
    intent = infer_intent(text)
    signals = detect_signals(text)

    privacy = "high" if "privacy" in signals else "normal"

    if any(x in signals for x in ("disconnect", "quiet")):
        privacy = "very_high"

    priority = "normal"

    if "disconnect" in signals:
        priority = "personal"

    return {
        "message": text,
        "language": lang,
        "intent": intent,
        "privacy": privacy,
        "priority": priority,
        "companion": detect_companion(text),
        "duration": detect_duration(text),
        "budget": detect_budget(text),
        "destination": detect_destination(text),
        "signals": signals
    }


def personalize_local(understanding, memory):
    memory = normalize_memory(memory)

    core = memory["core"]
    moment = memory["moment"]
    preferences = memory["preferences"]

    signals = list(understanding.get("signals") or [])

    for source in (core, preferences):
        if not isinstance(source, dict):
            continue

        style = str(
            source.get("travel_style")
            or source.get("style")
            or source.get("planning_style")
            or ""
        ).lower()

        if style and style not in signals:
            signals.append(style)

        privacy = str(source.get("privacy") or "").lower()

        if privacy and privacy not in signals:
            signals.append(privacy)

    today = {}
    if isinstance(moment, dict):
        today = {
            k: v for k, v in moment.items()
            if v not in (None, "", [], {})
        }

    return {
        "signals": list(dict.fromkeys(signals)),
        "today": today,
        "known_preferences": core,
        "personalized": bool(core or moment or preferences)
    }


def local_decision(understanding, personalization):
    intent = understanding.get("intent")
    destination = understanding.get("destination")
    duration = understanding.get("duration")
    companion = understanding.get("companion")

    score = 0

    if intent:
        score += 25
    if destination:
        score += 25
    if duration:
        score += 15
    if companion:
        score += 10
    if understanding.get("signals"):
        score += 15
    if personalization.get("personalized"):
        score += 10

    travel_intents = {
        "TRAVEL",
        "PRIVATE_ESCAPE"
    }

    if intent in travel_intents and not destination:
        return {
            "action": "ASK",
            "confidence": min(score, 85),
            "reason": "destination_missing"
        }

    if score < 35:
        return {
            "action": "CLARIFY",
            "confidence": score,
            "reason": "insufficient_context"
        }

    return {
        "action": "PROPOSE",
        "confidence": min(score, 98),
        "reason": "enough_context"
    }


def local_proposal(understanding, personalization, decision):
    lang = understanding.get("language", "en")
    intent = understanding.get("intent")
    signals = personalization.get("signals") or understanding.get("signals") or []

    if decision.get("action") in ("ASK", "CLARIFY"):
        if lang == "es":
            question = (
                "¿Dónde quieres que lo imagine? Puedes darme un lugar "
                "concreto o decirme que estoy abierto a sorprenderte."
            )
        else:
            question = (
                "Where would you like me to place this? Give me a specific "
                "place, or tell me you’re open to being surprised."
            )

        return {
            "status": decision["action"],
            "title": "One thing first",
            "direction": [question],
            "questions": [question],
            "category": intent,
            "privacy": understanding.get("privacy"),
            "priority": understanding.get("priority"),
            "budget": understanding.get("budget"),
            "destination": understanding.get("destination"),
            "duration": understanding.get("duration"),
            "companion": understanding.get("companion"),
            "signals": signals,
            "confidence": decision.get("confidence", 0)
        }

    if intent == "PRIVATE_ESCAPE":
        if lang == "es":
            direction = [
                "Una escapada privada, tranquila y sin ruido alrededor.",
                "Priorizaré privacidad, descanso, buena gastronomía y poca exposición.",
                "No necesitas construir el viaje tú; MIRROR puede encargarse de darle forma."
            ]
            title = "Tu espacio"
        else:
            direction = [
                "A private escape with quiet around you and nothing unnecessary.",
                "I’ll prioritize privacy, rest, excellent food and very little exposure.",
                "You don’t need to build the experience yourself; MIRROR can shape it for you."
            ]
            title = "Your space"

    elif intent == "TRAVEL":
        if lang == "es":
            direction = [
                "Voy a pensar en el viaje como una experiencia, no como una lista de opciones.",
                "Tomaré en cuenta tu ritmo, tus preferencias y lo que parece importante hoy."
            ]
            title = "Tu viaje"

        else:
            direction = [
                "I’ll think about the trip as an experience, not as a list of options.",
                "I’ll account for your rhythm, your preferences and what seems important today."
            ]
            title = "Your journey"

    elif intent == "DINING":
        if lang == "es":
            direction = [
                "No buscaré simplemente un restaurante.",
                "Buscaré el tipo de momento que quieres tener alrededor de la mesa."
            ]
            title = "La mesa"

        else:
            direction = [
                "I won’t simply look for a restaurant.",
                "I’ll look for the kind of moment you want to have around the table."
            ]
            title = "The table"

    elif intent == "MUSIC":
        if lang == "es":
            direction = [
                "Puedo cambiar el ambiente sin pedirte que hagas nada complicado.",
                "La música seguirá el tono de este momento."
            ]
            title = "El ambiente"

        else:
            direction = [
                "I can change the atmosphere without asking you to do anything complicated.",
                "The music will follow the tone of this moment."
            ]
            title = "The atmosphere"

    elif intent == "MOMENT":
        if lang == "es":
            direction = [
                "No voy a asumir que hoy necesitas lo mismo que ayer.",
                "Primero voy a encontrar qué necesita este momento."
            ]
            title = "Ahora"

        else:
            direction = [
                "I won’t assume today needs to feel like yesterday.",
                "First I’ll find what this moment needs."
            ]
            title = "Right now"

    else:
        if lang == "es":
            direction = [
                "Te escucho.",
                "No necesitas formularlo perfectamente. MIRROR puede descubrir contigo qué hay detrás de lo que acabas de decir."
            ]
            title = "Estoy aquí"

        else:
            direction = [
                "I’m listening.",
                "You don’t need to phrase it perfectly. MIRROR can discover with you what is behind what you just said."
            ]
            title = "I’m here"

    return {
        "status": "PROPOSAL",
        "title": title,
        "direction": direction,
        "questions": [],
        "category": intent,
        "privacy": understanding.get("privacy"),
        "priority": understanding.get("priority"),
        "budget": understanding.get("budget"),
        "destination": understanding.get("destination"),
        "duration": understanding.get("duration"),
        "companion": understanding.get("companion"),
        "signals": signals,
        "confidence": decision.get("confidence", 0)
    }


def build_prompt(message, memory):
    memory = normalize_memory(memory)

    compact_memory = {
        "core": memory["core"],
        "moment": memory["moment"],
        "preferences": memory["preferences"],
        "dislikes": memory["dislikes"][-12:],
        "learning": memory["learning"]
    }

    return f"""
You are MIRROR, a discreet private life concierge.

You are not a chatbot, search engine, travel marketplace or generic planner.
Your job is to understand the person, understand what is different today,
and decide the most useful next move.

The client should experience a calm, intelligent, human-like concierge.
Never expose technology, model names, prompts, algorithms, scores,
CRM terminology, JSON, internal classifications or system mechanics.

Never say that you are an AI.
Never say that an AI analyzed the client.
Never mention OpenAI, Gemini, Google, GPT or any model.
Never claim that something was booked, reserved, purchased or confirmed
unless an actual connected service has confirmed it.

The client may speak vaguely. Interpret intent from context.
Use the client's known preferences, but do not invent personal facts.
Use today's moment as distinct from long-term memory.

Do not ask unnecessary questions.
Ask only when the missing information genuinely prevents a useful next step.
Prefer one elegant question at a time.

Avoid generic phrases such as:
"I created a personalized concierge proposal."
"Category: concierge."
"Mission ID."
"Understand, personalize, plan, coordinate."

Instead, respond as MIRROR itself.

The experience should feel different depending on the person's current words,
context, memory and moment. Do not repeat the same wording unnecessarily.

Return ONLY valid JSON with this structure:

{{
  "language": "en or es",
  "intent": "short internal intent",
  "privacy": "normal/high/very_high",
  "priority": "normal/personal/urgent",
  "companion": "string or null",
  "duration": "string or null",
  "budget": "number/string/null",
  "destination": "string or null",
  "signals": ["short", "signals"],
  "action": "ASK or CLARIFY or PROPOSE",
  "confidence": 0,
  "title": "short natural title",
  "direction": ["one to three natural sentences"],
  "questions": ["zero or one question"],
  "next_move": "short internal description"
}}

Current client message:
{message}

Known memory:
{json.dumps(compact_memory, ensure_ascii=False)}
""".strip()


def parse_json(text):
    if not text:
        return None

    text = text.strip()

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text, flags=re.I).strip()
        text = re.sub(r"```$", "", text).strip()

    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, re.S)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                return None

    return None


def valid_ai_result(data):
    if not isinstance(data, dict):
        return False

    required = {
        "language",
        "intent",
        "action",
        "title",
        "direction",
        "questions"
    }

    if not required.issubset(data.keys()):
        return False

    if data.get("action") not in {"ASK", "CLARIFY", "PROPOSE"}:
        return False

    if not isinstance(data.get("direction"), list):
        return False

    if not isinstance(data.get("questions"), list):
        return False

    return True


def openai_call(prompt):
    if not OPENAI_KEY:
        return None

    url = "https://api.openai.com/v1/chat/completions"

    payload = {
        "model": OPENAI_MODEL,
        "temperature": 0.85,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are MIRROR. Return only valid JSON. "
                    "Never mention artificial intelligence or technology."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_KEY}"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            raw = response.read().decode("utf-8")
            data = json.loads(raw)
            content = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            result = parse_json(content)
            return result if valid_ai_result(result) else None
    except Exception:
        return None


def gemini_call(prompt):
    if not GEMINI_KEY:
        return None

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={urllib.parse.quote(GEMINI_KEY)}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.85,
            "responseMimeType": "application/json"
        }
    }

    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            raw = response.read().decode("utf-8")
            data = json.loads(raw)

            candidates = data.get("candidates") or []
            if not candidates:
                return None

            parts = (
                candidates[0]
                .get("content", {})
                .get("parts", [])
            )

            content = "".join(
                p.get("text", "")
                for p in parts
                if isinstance(p, dict)
            )

            result = parse_json(content)
            return result if valid_ai_result(result) else None
    except Exception:
        return None


def sanitize_ai(data, understanding):
    result = dict(data)

    result["language"] = (
        result.get("language")
        if result.get("language") in ("es", "en")
        else understanding.get("language", "en")
    )

    result["intent"] = clean(
        result.get("intent"),
        understanding.get("intent", "CONVERSATION")
    )

    result["privacy"] = clean(
        result.get("privacy"),
        understanding.get("privacy", "normal")
    )

    result["priority"] = clean(
        result.get("priority"),
        understanding.get("priority", "normal")
    )

    result["companion"] = clean(
        result.get("companion"),
        understanding.get("companion")
    )

    result["duration"] = clean(
        result.get("duration"),
        understanding.get("duration")
    )

    result["budget"] = (
        result.get("budget")
        if result.get("budget") not in ("", None)
        else understanding.get("budget")
    )

    result["destination"] = clean(
        result.get("destination"),
        understanding.get("destination")
    )

    signals = result.get("signals")
    if not isinstance(signals, list):
        signals = understanding.get("signals") or []

    result["signals"] = list(dict.fromkeys(
        str(x).strip() for x in signals if str(x).strip()
    ))[:15]

    result["action"] = (
        result.get("action")
        if result.get("action") in {"ASK", "CLARIFY", "PROPOSE"}
        else "CLARIFY"
    )

    result["confidence"] = result.get("confidence", 70)

    try:
        result["confidence"] = max(
            0,
            min(100, int(float(result["confidence"])))
        )
    except Exception:
        result["confidence"] = 70

    result["title"] = clean(
        result.get("title"),
        "Your moment" if result["language"] == "en" else "Tu momento"
    )

    direction = result.get("direction")
    if not isinstance(direction, list):
        direction = []

    result["direction"] = [
        str(x).strip()[:500]
        for x in direction
        if str(x).strip()
    ][:4]

    questions = result.get("questions")
    if not isinstance(questions, list):
        questions = []

    result["questions"] = [
        str(x).strip()[:350]
        for x in questions
        if str(x).strip()
    ][:1]

    if result["action"] in {"ASK", "CLARIFY"} and not result["questions"]:
        if result["language"] == "es":
            result["questions"] = [
                "¿Qué sería más importante para ti en este momento?"
            ]
        else:
            result["questions"] = [
                "What would matter most to you right now?"
            ]

    if result["action"] == "PROPOSE" and not result["direction"]:
        if result["language"] == "es":
            result["direction"] = [
                "Ya veo la dirección. Déjame darle forma contigo."
            ]
        else:
            result["direction"] = [
                "I see the direction. Let me shape it with you."
            ]

    return result


def understand(text):
    return understand_local(text)


def personalize(understanding, memory):
    return personalize_local(understanding, memory)


def decide(understanding, personalization):
    return local_decision(understanding, personalization)


def propose(understanding, personalization, decision):
    return local_proposal(understanding, personalization, decision)


def process(message, memory=None):
    message = clean(message, "")

    if not message:
        fallback = understand_local("")
        personalization = personalize_local(fallback, memory or {})
        decision = {
            "action": "CLARIFY",
            "confidence": 0,
            "reason": "empty_message"
        }
        proposal = local_proposal(
            fallback,
            personalization,
            decision
        )
        return {
            "understanding": fallback,
            "personalization": personalization,
            "decision": decision,
            "proposal": proposal,
            "engine": "local"
        }

    memory = normalize_memory(memory)
    understanding = understand_local(message)
    personalization = personalize_local(
        understanding,
        memory
    )

    prompt = build_prompt(message, memory)

    ai_result = openai_call(prompt)
    engine = "primary"

    if not valid_ai_result(ai_result):
        ai_result = gemini_call(prompt)
        engine = "backup"

    if valid_ai_result(ai_result):
        ai_result = sanitize_ai(
            ai_result,
            understanding
        )

        ai_understanding = dict(understanding)

        for key in (
            "language",
            "intent",
            "privacy",
            "priority",
            "companion",
            "duration",
            "budget",
            "destination",
            "signals"
        ):
            if key in ai_result:
                ai_understanding[key] = ai_result[key]

        decision = {
            "action": ai_result["action"],
            "confidence": ai_result["confidence"],
            "reason": "contextual_reasoning"
        }

        proposal = {
            "status": ai_result["action"],
            "title": ai_result["title"],
            "direction": ai_result["direction"],
            "questions": ai_result["questions"],
            "category": ai_result["intent"],
            "privacy": ai_result["privacy"],
            "priority": ai_result["priority"],
            "budget": ai_result["budget"],
            "destination": ai_result["destination"],
            "duration": ai_result["duration"],
            "companion": ai_result["companion"],
            "signals": ai_result["signals"],
            "confidence": ai_result["confidence"]
        }

        personalization["signals"] = ai_result["signals"]

        return {
            "understanding": ai_understanding,
            "personalization": personalization,
            "decision": decision,
            "proposal": proposal,
            "engine": engine
        }

    decision = local_decision(
        understanding,
        personalization
    )

    proposal = local_proposal(
        understanding,
        personalization,
        decision
    )

    return {
        "understanding": understanding,
        "personalization": personalization,
        "decision": decision,
        "proposal": proposal,
        "engine": "local"
    }


def response_text(result, language="en"):
    proposal = result.get("proposal") or {}
    action = proposal.get("status") or (
        result.get("decision") or {}
    ).get("action")

    language = language if language in ("es", "en") else "en"

    direction = proposal.get("direction") or []
    questions = proposal.get("questions") or []

    if action in ("ASK", "CLARIFY"):
        if direction:
            text = direction[0]
            if len(direction) > 1:
                text += " " + direction[1]
        else:
            text = (
                "Necesito una pequeña pieza de información antes de seguir."
                if language == "es"
                else "I need one small piece of information before I continue."
            )

        if questions:
            text += " " + questions[0]

        return text.strip()

    if direction:
        return " ".join(direction).strip()

    if language == "es":
        return "Estoy contigo. Vamos a darle forma a este momento."
    return "I’m with you. Let’s shape this moment."


def engine_status():
    return {
        "primary_available": bool(OPENAI_KEY),
        "backup_available": bool(GEMINI_KEY),
        "local_continuity": True
    }
