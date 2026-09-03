import os
import json
import re
import random
import urllib.request
import urllib.error
from datetime import datetime, timezone


AI_KEY = os.getenv("OPENAI_API_KEY", "").strip()
AI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini").strip()
AI_URL = "https://api.openai.com/v1/chat/completions"


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
    es = len(re.findall(
        r"\b(quiero|necesito|hoy|mañana|viaje|hotel|solo|sola|"
        r"descansar|comida|comer|silencio|tranquilo|ayúdame|"
        r"buscar|hacer|sentir|necesito)\b", t
    ))
    en = len(re.findall(
        r"\b(i|want|need|today|tomorrow|trip|hotel|alone|"
        r"rest|food|eat|quiet|help|find|feel|make)\b", t
    ))
    return "es" if es >= en else "en"


def detect_intent(text):
    t = (text or "").lower()

    rules = [
        ("TRAVEL", r"\b(viaje|viajar|trip|travel|vacaciones|vacation|destination|destino|fly|volar|vuelo)\b"),
        ("ESCAPE", r"\b(desaparecer|escapar|escape|get away|getaway|alejarme|irme|disconnect|desconectar)\b"),
        ("STAY", r"\b(hotel|resort|villa|suite|habitación|room|stay|hospedar|alojamiento)\b"),
        ("DINING", r"\b(restaurante|restaurant|comida|cena|dinner|lunch|chef|gastronomía|food)\b"),
        ("EXPERIENCE", r"\b(experiencia|experience|hacer algo|do something|sorpresa|surprise|diferente|different)\b"),
        ("MUSIC", r"\b(música|music|canción|song|playlist|youtube)\b"),
        ("MAPS", r"\b(map|maps|mapa|ubicación|location|dirección|address)\b"),
        ("WELLBEING", r"\b(respirar|respiración|breath|breathe|calmar|calm|pausa|pause|silencio|quiet)\b"),
        ("CONCIERGE", r"\b(encárgate|take care|handle|coordina|coordinate|resuelve|resolve|concierge)\b"),
    ]

    for intent, pattern in rules:
        if re.search(pattern, t):
            return intent

    return "COMPANION"


def detect_privacy(text, memory):
    t = (text or "").lower()
    core = memory.get("core", {}) if isinstance(memory, dict) else {}
    prefs = memory.get("preferences", {}) if isinstance(memory, dict) else {}

    if re.search(r"\b(very private|maximum privacy|private|privado|privacidad|nadie|no me molesten|no interruptions)\b", t):
        return "VERY_HIGH"
    if re.search(r"\b(quiet|tranquilo|tranquila|silence|silencio|secluded|aislado)\b", t):
        return "HIGH"

    value = str(
        core.get("privacy")
        or prefs.get("privacy")
        or ""
    ).upper()

    if value in {"VERY_HIGH", "HIGH", "MEDIUM", "LOW"}:
        return value

    return "NORMAL"


def detect_priority(text):
    t = (text or "").lower()

    if re.search(r"\b(urgent|urgente|asap|ahora mismo|immediately|inmediatamente)\b", t):
        return "URGENT"
    if re.search(r"\b(soon|pronto|esta semana|this week|weekend|fin de semana)\b", t):
        return "HIGH"
    return "NORMAL"


def detect_companion(text):
    t = (text or "").lower()

    if re.search(r"\b(alone|solo|sola|by myself|por mi cuenta)\b", t):
        return "ALONE"
    if re.search(r"\b(my wife|mi esposa|mi marido|my husband|pareja|partner)\b", t):
        return "PARTNER"
    if re.search(r"\b(family|familia|kids|niños|children|hijos)\b", t):
        return "FAMILY"
    if re.search(r"\b(friend|amigo|amiga|friends|amigos)\b", t):
        return "FRIENDS"
    return None


def detect_duration(text):
    t = (text or "").lower()

    patterns = [
        r"(\d+)\s*(?:day|days|día|días)",
        r"(\d+)\s*(?:night|nights|noche|noches)"
    ]

    for pattern in patterns:
        m = re.search(pattern, t)
        if m:
            return m.group(0)

    if re.search(r"\b(weekend|fin de semana)\b", t):
        return "WEEKEND"

    if re.search(r"\b(today|hoy)\b", t):
        return "TODAY"

    return None


def detect_budget(text):
    t = (text or "").lower()

    m = re.search(r"(?:\$|usd\s*)(\d[\d,]*(?:\.\d+)?)", t)
    if m:
        return "$" + m.group(1)

    if re.search(r"\b(luxury|lujo|premium|exclusive|exclusivo|high end)\b", t):
        return "LUXURY"

    if re.search(r"\b(no budget|sin presupuesto|whatever it costs|lo que cueste)\b", t):
        return "OPEN"

    return None


def detect_destination(text):
    t = (text or "").strip()

    patterns = [
        r"\b(?:in|en)\s+([A-Z][A-Za-zÀ-ÿ]*(?:\s+[A-Z][A-Za-zÀ-ÿ]*){0,3})",
        r"\b(?:to|a|hacia)\s+([A-Z][A-Za-zÀ-ÿ]*(?:\s+[A-Z][A-Za-zÀ-ÿ]*){0,3})"
    ]

    for pattern in patterns:
        m = re.search(pattern, t)
        if m:
            value = m.group(1).strip(" .,!?")
            bad = {
                "The", "A", "An", "This", "That",
                "La", "El", "Un", "Una", "Hoy", "Mañana"
            }
            if value not in bad:
                return value

    return None


def detect_signals(text):
    t = (text or "").lower()
    signals = []

    checks = [
        ("QUIET", r"\b(quiet|tranquilo|tranquila|silencio|silencioso|peaceful)\b"),
        ("PRIVACY", r"\b(private|privado|privacidad|secluded|aislado|nadie)\b"),
        ("LUXURY", r"\b(luxury|lujo|premium|exclusive|exclusivo|refined)\b"),
        ("LOW_CROWD", r"\b(no crowds|sin multitudes|no crowd|poca gente|sin gente)\b"),
        ("RELAXATION", r"\b(rest|resting|descansar|relax|relaj|disconnect|desconectar)\b"),
        ("DINING", r"\b(food|comida|dinner|cena|restaurant|restaurante|chef|gastronomía)\b"),
        ("NATURE", r"\b(nature|naturaleza|beach|playa|mountain|montaña|ocean|océano)\b"),
        ("MUSIC", r"\b(music|música|song|canción)\b"),
        ("SURPRISE", r"\b(surprise|sorpresa|unexpected|inesperado|sorpréndeme)\b"),
        ("SIMPLICITY", r"\b(simple|sencillo|sin complicaciones|no planning|no quiero planificar)\b"),
    ]

    for name, pattern in checks:
        if re.search(pattern, t):
            signals.append(name)

    return signals


def understand(text):
    text = clean(text, "")[:5000]
    lang = language_of(text)

    return {
        "message": text,
        "language": lang,
        "intent": detect_intent(text),
        "privacy": detect_privacy(text, {}),
        "priority": detect_priority(text),
        "companion": detect_companion(text),
        "duration": detect_duration(text),
        "budget": detect_budget(text),
        "destination": detect_destination(text),
        "signals": detect_signals(text)
    }


def personalize(understanding, memory):
    memory = memory if isinstance(memory, dict) else {}

    core = memory.get("core") or {}
    moment = memory.get("moment") or {}
    preferences = memory.get("preferences") or {}
    dislikes = memory.get("dislikes") or []
    history = memory.get("history") or []
    learning = memory.get("learning") or {}

    signals = list(understanding.get("signals") or [])

    old_signals = moment.get("signals") or []
    if isinstance(old_signals, list):
        for signal in old_signals:
            if signal not in signals:
                signals.append(signal)

    for key, signal in (
        ("quiet", "QUIET"),
        ("privacy", "PRIVACY"),
        ("luxury", "LUXURY"),
        ("nature", "NATURE"),
        ("music", "MUSIC"),
        ("dining", "DINING"),
    ):
        value = core.get(key, preferences.get(key))
        if value and signal not in signals:
            signals.append(signal)

    return {
        "has_memory": bool(core or preferences or history),
        "core": core,
        "moment": moment,
        "preferences": preferences,
        "dislikes": dislikes[-20:],
        "history_count": len(history),
        "learning": learning,
        "signals": signals,
        "personalized": bool(core or preferences or history)
    }


def missing_information(understanding):
    intent = understanding.get("intent")
    destination = understanding.get("destination")
    duration = understanding.get("duration")
    companion = understanding.get("companion")

    if intent in {"TRAVEL", "ESCAPE", "STAY"}:
        if not destination and not duration and not companion:
            return ["destination_or_direction"]

    return []


def decision_for(understanding, personalization):
    intent = understanding.get("intent")
    text = understanding.get("message", "").lower()
    missing = missing_information(understanding)

    if re.search(
        r"\b(anywhere|wherever|surprise me|sorpréndeme|"
        r"doesn't matter|no importa|somewhere|algún lugar)\b",
        text
    ):
        missing = []

    score = 0

    if intent:
        score += 25
    if understanding.get("duration"):
        score += 20
    if understanding.get("companion"):
        score += 15
    if understanding.get("destination"):
        score += 20
    if understanding.get("signals"):
        score += 15
    if personalization.get("personalized"):
        score += 10

    if missing and score < 55:
        return {
            "action": "ASK",
            "confidence": score,
            "missing": missing
        }

    if score >= 45:
        return {
            "action": "PROPOSE",
            "confidence": min(score, 100),
            "missing": []
        }

    return {
        "action": "CLARIFY",
        "confidence": score,
        "missing": missing or ["meaning"]
    }


def title_for(understanding, lang):
    intent = understanding.get("intent")
    signals = set(understanding.get("signals") or [])

    titles_en = {
        "ESCAPE": "A private escape",
        "TRAVEL": "A journey shaped around you",
        "STAY": "A stay that fits your rhythm",
        "DINING": "Something worth tasting",
        "EXPERIENCE": "Something different",
        "MUSIC": "A different atmosphere",
        "WELLBEING": "A quieter moment",
        "MAPS": "A place worth knowing",
        "CONCIERGE": "Let me take care of it",
        "COMPANION": "Let’s start with today"
    }

    titles_es = {
        "ESCAPE": "Una escapada para ti",
        "TRAVEL": "Un viaje hecho a tu medida",
        "STAY": "Un lugar que siga tu ritmo",
        "DINING": "Algo que valga la pena probar",
        "EXPERIENCE": "Algo diferente",
        "MUSIC": "Una atmósfera diferente",
        "WELLBEING": "Un momento más tranquilo",
        "MAPS": "Un lugar que merece conocerse",
        "CONCIERGE": "Déjamelo a mí",
        "COMPANION": "Empecemos por hoy"
    }

    titles = titles_es if lang == "es" else titles_en

    if "SURPRISE" in signals:
        return "Algo que no esperabas" if lang == "es" else "Something you didn't expect"

    if "PRIVACY" in signals and intent in {"ESCAPE", "TRAVEL", "STAY"}:
        return "Tu espacio, sin interrupciones" if lang == "es" else "Your space, uninterrupted"

    return titles.get(intent, titles["COMPANION"])


def direction_for(understanding, personalization, lang):
    intent = understanding.get("intent")
    signals = set(personalization.get("signals") or [])
    duration = understanding.get("duration")
    companion = understanding.get("companion")
    destination = understanding.get("destination")

    if lang == "es":
        lines = []

        if intent == "ESCAPE":
            lines.append("Una pausa real, no simplemente otro lugar al que ir.")
        elif intent == "TRAVEL":
            lines.append("Un viaje diseñado alrededor de cómo quieres sentirte.")
        elif intent == "STAY":
            lines.append("Un alojamiento elegido por la experiencia que quieres vivir.")
        elif intent == "DINING":
            lines.append("La comida como parte de la experiencia, no como una parada más.")
        elif intent == "EXPERIENCE":
            lines.append("Algo diferente sin obligarte a convertirlo en un itinerario.")
        elif intent == "WELLBEING":
            lines.append("Un cambio pequeño en el momento correcto.")

        if "PRIVACY" in signals or "QUIET" in signals:
            lines.append("Privacidad y tranquilidad tienen prioridad.")
        if "LOW_CROWD" in signals:
            lines.append("Evitaré lugares donde la multitud sea parte de la experiencia.")
        if "LUXURY" in signals:
            lines.append("El nivel de comodidad y detalle debe estar a la altura.")
        if "DINING" in signals:
            lines.append("La gastronomía tendrá un peso importante.")
        if "NATURE" in signals:
            lines.append("La naturaleza puede ser parte del cambio de ritmo.")

        if duration:
            lines.append(f"Duración: {duration}.")
        if companion == "ALONE":
            lines.append("Esta vez, solo tú.")
        if destination:
            lines.append(f"Destino considerado: {destination}.")

        return lines[:5]

    lines = []

    if intent == "ESCAPE":
        lines.append("A real pause, not simply another place to go.")
    elif intent == "TRAVEL":
        lines.append("A journey shaped around how you want to feel.")
    elif intent == "STAY":
        lines.append("A stay chosen around the experience you want.")
    elif intent == "DINING":
        lines.append("Food as part of the experience, not just another stop.")
    elif intent == "EXPERIENCE":
        lines.append("Something different without turning it into a rigid itinerary.")
    elif intent == "WELLBEING":
        lines.append("A small shift at the right moment.")

    if "PRIVACY" in signals or "QUIET" in signals:
        lines.append("Privacy and quiet come first.")
    if "LOW_CROWD" in signals:
        lines.append("I’ll avoid places where crowds are part of the experience.")
    if "LUXURY" in signals:
        lines.append("Comfort and detail should meet your standards.")
    if "DINING" in signals:
        lines.append("Food will be part of the selection.")
    if "NATURE" in signals:
        lines.append("Nature can be part of the change of pace.")

    if duration:
        lines.append(f"Duration: {duration}.")
    if companion == "ALONE":
        lines.append("This one is just for you.")
    if destination:
        lines.append(f"Destination in consideration: {destination}.")

    return lines[:5]


def questions_for(understanding, lang):
    intent = understanding.get("intent")

    if intent in {"TRAVEL", "ESCAPE", "STAY"}:
        if lang == "es":
            return [
                "¿Quieres quedarte cerca o estás abierto a volar?"
            ]
        return [
            "Do you want to stay nearby, or are you open to flying?"
        ]

    if intent == "DINING":
        if lang == "es":
            return ["¿Quieres algo íntimo, social o completamente inesperado?"]
        return ["Do you want something intimate, social, or completely unexpected?"]

    if lang == "es":
        return ["¿Qué te gustaría que cambiara de este momento?"]

    return ["What would you like to feel differently about this moment?"]


def local_response(understanding, personalization, decision):
    lang = understanding.get("language", "en")
    intent = understanding.get("intent")
    signals = set(personalization.get("signals") or [])

    if decision.get("action") in {"ASK", "CLARIFY"}:
        questions = questions_for(understanding, lang)

        if lang == "es":
            if intent in {"TRAVEL", "ESCAPE", "STAY"}:
                text = (
                    "Entiendo la dirección que buscas. "
                    "Antes de moverme necesito una sola cosa: "
                    + questions[0]
                )
            else:
                text = questions[0]
        else:
            if intent in {"TRAVEL", "ESCAPE", "STAY"}:
                text = (
                    "I understand the direction you're looking for. "
                    "Before I move, I need one thing: "
                    + questions[0]
                )
            else:
                text = questions[0]

        return text

    if lang == "es":
        if "PRIVACY" in signals:
            return "Entendido. Voy a tratar este momento como algo tuyo: menos ruido, más intención y nada innecesario."
        if intent == "ESCAPE":
            return "Entendido. No estás buscando simplemente un destino. Estás buscando cambiar de estado durante unos días."
        if intent == "EXPERIENCE":
            return "Entendido. No voy a llenarte de opciones. Voy a buscar una experiencia que tenga sentido para ti ahora."
        if intent == "DINING":
            return "Entendido. La comida es parte de lo que buscas, así que no voy a tratarla como un simple lugar para comer."
        return "Entendido. Ya tengo una primera dirección para este momento."

    if "PRIVACY" in signals:
        return "Understood. I’ll treat this as something personal: less noise, more intention, nothing unnecessary."
    if intent == "ESCAPE":
        return "Understood. You’re not simply looking for a destination. You’re looking to change your state for a few days."
    if intent == "EXPERIENCE":
        return "Understood. I won’t flood you with options. I’ll look for something that makes sense for you now."
    if intent == "DINING":
        return "Understood. Food is part of what you’re looking for, so I won’t treat it as just another place to eat."
    return "Understood. I already have a first direction for this moment."


def ai_prompt(understanding, personalization, decision):
    return f"""
You are MIRROR, a private life concierge.
You are not presented to the client as a chatbot or AI.
Never mention models, prompts, algorithms, CRM, JSON, APIs, automation, or internal systems.

Your job is to understand the person, their current moment, and what they actually need.
Use long-term preferences only as context. The current message always has priority.
Do not invent facts, bookings, prices, availability, providers, or completed actions.

The experience must feel human, discreet, concise, intelligent and highly personalized.
Do not produce generic concierge language.
Do not say "I created a personalized concierge proposal."
Do not expose categories, confidence scores, mission IDs, or technical metadata.

CURRENT UNDERSTANDING:
{json.dumps(understanding, ensure_ascii=False)}

PERSONAL MEMORY:
{json.dumps(personalization, ensure_ascii=False)}

DECISION:
{json.dumps(decision, ensure_ascii=False)}

Return ONLY valid JSON:
{{
  "reply": "natural response to the client",
  "title": "short elegant title",
  "direction": ["up to 5 meaningful directions"],
  "question": "one question only, or empty string",
  "tone": "one short word",
  "next_action": "ASK, PROPOSE, or CONCIERGE"
}}
""".strip()


def call_ai(understanding, personalization, decision):
    if not AI_KEY:
        return None

    payload = {
        "model": AI_MODEL,
        "temperature": 0.9,
        "messages": [
            {
                "role": "system",
                "content": "You are the invisible intelligence behind MIRROR TO YOU."
            },
            {
                "role": "user",
                "content": ai_prompt(
                    understanding,
                    personalization,
                    decision
                )
            }
        ]
    }

    request = urllib.request.Request(
        AI_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {AI_KEY}"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            raw = response.read().decode("utf-8")
            data = json.loads(raw)

        content = data["choices"][0]["message"]["content"].strip()
        content = re.sub(r"^```json\s*", "", content)
        content = re.sub(r"\s*```$", "", content)

        result = json.loads(content)

        if not isinstance(result, dict):
            return None

        return result

    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        TimeoutError,
        KeyError,
        ValueError,
        json.JSONDecodeError
    ):
        return None


def proposal_for(understanding, personalization, decision):
    lang = understanding.get("language", "en")

    if decision.get("action") in {"ASK", "CLARIFY"}:
        return {
            "status": decision.get("action"),
            "title": title_for(understanding, lang),
            "direction": [],
            "questions": questions_for(understanding, lang),
            "category": understanding.get("intent"),
            "privacy": understanding.get("privacy"),
            "priority": understanding.get("priority"),
            "budget": understanding.get("budget"),
            "destination": understanding.get("destination"),
            "duration": understanding.get("duration"),
            "companion": understanding.get("companion"),
            "signals": personalization.get("signals", []),
            "confidence": decision.get("confidence", 0)
        }

    return {
        "status": "PROPOSAL",
        "title": title_for(understanding, lang),
        "direction": direction_for(
            understanding,
            personalization,
            lang
        ),
        "questions": [],
        "category": understanding.get("intent"),
        "privacy": understanding.get("privacy"),
        "priority": understanding.get("priority"),
        "budget": understanding.get("budget"),
        "destination": understanding.get("destination"),
        "duration": understanding.get("duration"),
        "companion": understanding.get("companion"),
        "signals": personalization.get("signals", []),
        "confidence": decision.get("confidence", 0)
    }


def apply_ai(proposal, understanding, personalization, decision):
    ai = call_ai(
        understanding,
        personalization,
        decision
    )

    if not ai:
        return proposal, None

    reply = clean(ai.get("reply"))
    title = clean(ai.get("title"))
    direction = ai.get("direction")

    if reply:
        proposal["_ai_reply"] = reply

    if title:
        proposal["title"] = title

    if isinstance(direction, list):
        proposal["direction"] = [
            str(x).strip()
            for x in direction
            if str(x).strip()
        ][:5]

    if decision.get("action") in {"ASK", "CLARIFY"}:
        question = clean(ai.get("question"))

        if question:
            proposal["questions"] = [question]

    return proposal, ai


def process(message, memory=None):
    message = clean(message, "")

    if not message:
        understanding = {
            "message": "",
            "language": "en",
            "intent": "COMPANION",
            "privacy": "NORMAL",
            "priority": "NORMAL",
            "companion": None,
            "duration": None,
            "budget": None,
            "destination": None,
            "signals": []
        }
    else:
        understanding = understand(message)

    memory = memory if isinstance(memory, dict) else {}

    # Re-evaluate privacy with the actual memory available.
    understanding["privacy"] = detect_privacy(
        understanding.get("message", ""),
        memory
    )

    personalization = personalize(
        understanding,
        memory
    )

    decision = decision_for(
        understanding,
        personalization
    )

    proposal = proposal_for(
        understanding,
        personalization,
        decision
    )

    proposal, ai = apply_ai(
        proposal,
        understanding,
        personalization,
        decision
    )

    return {
        "understanding": understanding,
        "personalization": personalization,
        "decision": decision,
        "proposal": proposal,
        "ai_used": bool(ai)
    }


def response_text(result, language=None):
    understanding = result.get("understanding") or {}
    personalization = result.get("personalization") or {}
    decision = result.get("decision") or {}
    proposal = result.get("proposal") or {}

    lang = language or understanding.get("language") or "en"

    ai_reply = proposal.get("_ai_reply")
    if ai_reply:
        return ai_reply

    return local_response(
        understanding,
        personalization,
        decision
    )
