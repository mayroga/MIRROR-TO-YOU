import os
import json
import re
import urllib.request
from datetime import datetime

AI_KEY = os.getenv("OPENAI_API_KEY", "").strip()
AI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()  # Modelo optimizado de alta velocidad
AI_URL = "https://openai.com"

INTENTS = ("TRAVEL", "ESCAPE", "STAY", "DINING", "EXPERIENCE", "MUSIC", "MAPS", "WELLBEING", "CONCIERGE")

def now():
    return datetime.now().isoformat(timespec="seconds")

def clean(v):
    return str(v).strip() if v is not None else ""

def detect_language(text, memory):
    # Respeta la preferencia guardada o analiza el mensaje actual de forma robusta
    saved_lang = memory.get("moment", {}).get("language")
    if saved_lang in ("es", "en"):
        return saved_lang
    t = clean(text).lower()
    es_signals = ("que", "para", "necesito", "quiero", "donde", "como", "buscar", "viaje", "hola")
    es_score = sum(1 for w in es_signals if re.search(r'\b' + w + r'\b', t))
    return "es" if es_score >= 1 else "en"

def detect_intent(text):
    t = clean(text).lower()
    rules = {
        "TRAVEL": ("viaje", "vuelo", "aeropuerto", "jet", "charter", "flight", "airport", "aviation", "helicoptero"),
        "ESCAPE": ("escapar", "escape", "desconectar", "disconnect", "alejarme", "isolated", "hideaway"),
        "STAY": ("hotel", "resort", "suite", "villa", "alojamiento", "stay", "aman", "st regis", "fours seasons"),
        "DINING": ("restaurant", "restaurante", "cena", "comer", "chef", "food", "dinner", "michelin", "caviar"),
        "EXPERIENCE": ("experiencia", "experience", "spa", "yacht", "yate", "golf", "art", "subasta", "gallería"),
        "MUSIC": ("música", "musica", "music", "playlist", "soundtrack", "ambient"),
        "MAPS": ("mapa", "maps", "donde", "ubicacion", "location", "route", "direccion", "cerca", "address"),
        "WELLBEING": ("respirar", "calma", "relax", "estres", "stress", "breathing", "anxiety", "meditar", "peace")
    }
    for intent, words in rules.items():
        if any(w in t for w in words):
            return intent
    return "CONCIERGE"

def process(text, memory=None):
    text = clean(text)
    memory = memory or {}
    
    lang = detect_language(text, memory)
    intent = detect_intent(text)
    
    # Análisis de reentrada dinámica (Manejo de las 100 entradas al día)
    history = memory.get("history", [])
    reentries_today = len(history)
    
    # Filtrado premium para Google Maps (No soluciones genéricas o cotidianas)
    raw_dest = ""
    dest_match = re.search(r"(?:en|in|at|near|hacia|to|para)\s+([A-Z][\w\s'-]{2,30})", text)
    if dest_match:
        raw_dest = clean(dest_match.group(1))
    
    premium_context = "Luxury VIP Experience"
    if intent == "DINING": premium_context = "Michelin Star Restaurant Fine Dining"
    elif intent == "STAY": premium_context = "5 Star Luxury Hotel Villa Suite"
    elif intent == "TRAVEL": premium_context = "Private Jet Airport Terminal Helipad"
    elif intent == "EXPERIENCE": premium_context = "Exclusive Private Access Yacht Spa"
    
    destination_query = f"{raw_dest} {premium_context}".strip() if raw_dest else premium_context

    # Sistema de Objetivos Dinámicos del Cliente de Alto Nivel
    directions = {
        "es": ["Acceso inmediato sin intermediarios", "Coordinación discreta en curso", "Detalles optimizados para su agenda"],
        "en": ["Immediate friction-free access", "Discreet coordination in progress", "Details streamlined for your schedule"]
    }[lang]

    # Configuración dinámica del círculo respiratorio profesional
    breathing_modes = ["CALM / RESET", "FOCUS / CLARITY", "ENERGY / POWER"]
    current_mode = breathing_modes[reentries_today % len(breathing_modes)]

    understanding = {
        "intent": intent,
        "language": lang,
        "destination": destination_query,
        "reentries_today": reentries_today,
        "breathing_mode": current_mode
    }

    # Prompt ultra-exclusivo para la IA
    ai_prompt = f"""
You are MIRROR, the ultimate private life concierge for ultra-high-net-worth individuals.
Speak directly as MIRROR—elegant, hyper-concise, and powerful. 
The client values time above all else. No fluff, no robotic lists, no corporate jargon.
Anticipate elite needs perfectly. 
Language: {lang}
Client current intent: {intent}
Reentries today: {reentries_today} (Acknowledge subtly or vary tone if high)

Formulate a flawless, upscale response. 
Return ONLY a valid JSON object matching this schema exactly:
{{
  "reply": "Your brilliant, ultra-premium sentence response",
  "title": "Short elite title for the current moment",
  "directions": ["Premium actionable direction 1", "Premium actionable direction 2"]
}}
"""
    
    reply_text = "I am ready. Tell me what to streamline for you." if lang == "en" else "Estoy listo. Dígame de qué me encargo hoy."
    title_text = "Private Lounge" if lang == "en" else "Espacio Privado"
    
    if AI_KEY:
        payload = json.dumps({
            "model": AI_MODEL,
            "messages": [{"role": "system", "content": ai_prompt}, {"role": "user", "content": text}],
            "temperature": 0.6,
            "response_format": {"type": "json_object"}
        }).encode()
        req = urllib.request.Request(AI_URL, data=payload, headers={"Content-Type": "application/json", "Authorization": f"Bearer {AI_KEY}"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=8) as r:
                res = json.loads(r.read().decode())
                content = json.loads(res["choices"][0]["message"]["content"])
                reply_text = content.get("reply", reply_text)
                title_text = content.get("title", title_text)
                directions = content.get("directions", directions)
        except Exception:
            pass

    return {
        "understanding": understanding,
        "personalization": {"name": memory.get("core", {}).get("name", "")},
        "decision": {"action": "PROPOSE" if intent != "CONCIERGE" else "CONCIERGE", "confidence": 0.99},
        "proposal": {
            "title": title_text,
            "reply": reply_text,
            "direction": directions,
            "question": ""
        },
        "status": "PROPOSAL" if intent != "CONCIERGE" else "CONCIERGE"
    }

def response_text(result, language="en"):
    return result["proposal"]["reply"]
