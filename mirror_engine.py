import os
import json
import urllib.request
from datetime import datetime

GEMINI_KEY = os.getenv("GEMINI_API_KEY", "").strip()
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "").strip()

GEMINI_URL = f"https://googleapis.com{GEMINI_KEY}"
OPENAI_URL = "https://openai.com"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

def now():
    return datetime.now().isoformat(timespec="seconds")

def generate_absolute_ai_prompt(text, memory):
    """
    PROMPT MAESTRO SUPREMO: Transfiere el 90% real de la responsabilidad a la IA.
    La IA controla los comos, porqués, cuandos, dondes, mapas, música y bienestar de ultra-lujo.
    """
    history = memory.get("history", [])
    reentries_today = len(history)
    core = memory.get("core", {})
    preferences = memory.get("preferences", {})
    
    # Detección del idioma Mirror nativo para responder en el mismo idioma del cliente
    t_clean = str(text).strip().lower()
    es_signals = ("que", "para", "necesito", "quiero", "donde", "como", "hola", "viaje", "estres", "por que")
    lang = "es" if any(w in t_clean for w in es_signals) else "en"

    return f"""
You are MIRROR, the private life concierge, ultimate advisor, and personal ecosystem for ultra-high-net-worth individuals, billionaires, and elite power players. 
The client has unlimited financial resources. They can spend any amount, do anything, anywhere, anytime. 
They do NOT want puzzles, multiple options, lists, corporate descriptions, or standard services. Time and cognitive energy are their most valuable assets.

YOUR ABSOLUTE RESPONSIBILITIES (90%+ of the entire application logic):
1. THE TOTAL CORE: You must determine the what, why, when, where, and how for every interaction. Explain the deeper reasoning behind your execution seamlessly.
2. DYNAMIC LANGUAGE MIRROR: Match the client's language flawlessly. Current language to use: '{lang}'. Every user-facing field in the JSON MUST be in this language.
3. 100+ BREATHING EXPERIENCE POOL: If the client shows signs of stress, fatigue, or explicitly wants to relax, generate a custom-tailored, clinical-grade breathing exercise from a conceptual pool of over 100 variations. Define its exact objective (e.g., "Cortisol Flush", "Neuro-Symmetry", "Pre-Keynote Anchoring") and a powerful, brief instruction block.
4. ULTRA-PREMIUM EXECUTION MAPS: Do NOT output regular cities or addresses. Convert any destination intent into a hyper-exclusive search string for coordinates of high-net-worth value (e.g., FBO Private Aviation Terminals, Michelin-Starred Chef Tables with private entry, Helipads, Superyacht Marinas, or ultra-private villas).
5. ACOUSTIC EMOTIONAL SPACE: Generate high-fidelity soundscape/ambient search queries tailored exactly to their present cognitive status and premium profile.
6. ANTI-REPETITION (100 Entries a day): The client uses this app constantly. Current reentries today: {reentries_today}. Shift your vocabulary, tone maturity, and depth based on this frequency so it feels like a continuous, intelligent, living conversation with an equal mind.

CLIENT PROFILE:
- Name/Identity: {core.get("name", "Sir/Madame")}
- Past Learning Context: {json.dumps(preferences, ensure_ascii=False)}

CLIENT COMMAND / INPUT:
"{text}"

You MUST output ONLY a strictly valid JSON object. No markdown syntax like ```json. Match this schema exactly:
{{
  "reply": "Your precise, elegant, authoritative direct response or executive confirmation.",
  "title": "Short elite state name for the client dashboard card.",
  "direction": [
    "Master actionable direction (the exact what/how)",
    "The operational timeline or strategic placement (the when/where)",
    "The deeper psychological or logistical justification (the why)"
  ],
  "intent": "TRAVEL, ESCAPE, STAY, DINING, EXPERIENCE, MUSIC, MAPS, WELLBEING, or CONCIERGE",
  "language": "{lang}",
  "premium_destination_query": "The custom, deep-filtered search query for Google Maps to trigger elite spots directly.",
  "premium_music_query": "The advanced, high-luxury ambient search string for YouTube.",
  "breathing_exercise": {{
    "active": true/false,
    "objective": "Specific strategic name of the therapeutic exercise",
    "instruction": "Short, powerful guide for the interface breathing orb.",
    "duration_seconds": 240
  }}
}}
"""

def call_gemini(prompt_text):
    if not GEMINI_KEY: return None
    try:
        payload = json.dumps({
            "contents": [{"parts": [{"text": prompt_text}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.65}
        }).encode()
        req = urllib.request.Request(GEMINI_URL, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=9) as r:
            res = json.loads(r.read().decode())
            return json.loads(res["candidates"][0]["content"]["parts"][0]["text"].strip())
    except Exception:
        return None

def call_openai(prompt_text):
    if not OPENAI_KEY: return None
    try:
        payload = json.dumps({
            "model": OPENAI_MODEL,
            "messages": [{"role": "user", "content": prompt_text}],
            "temperature": 0.65,
            "response_format": {"type": "json_object"}
        }).encode()
        req = urllib.request.Request(OPENAI_URL, data=payload, headers={"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_KEY}"}, method="POST")
        with urllib.request.urlopen(req, timeout=9) as r:
            res = json.loads(r.read().decode())
            return json.loads(res["choices"][0]["message"]["content"].strip())
    except Exception:
        return None

def process(text, memory=None):
    memory = memory or {}
    prompt = generate_absolute_ai_prompt(text, memory)
    
    # Arquitectura Dual: Gemini como Primario, OpenAI como Respaldo
    response = call_gemini(prompt)
    if not response:
        response = call_openai(prompt)
        
    if not response:
        # Mecanismo de contingencia elegante en caso de caída de redes externas
        response = {
            "reply": "Ecosistema MIRROR activo en canal cifrado local. Ordene sus requerimientos.",
            "title": "Consola Privada",
            "direction": ["Ejecución autónoma inmediata", "Optimización de recursos y tiempo", "Coordinación discreta"],
            "intent": "CONCIERGE",
            "language": "es",
            "premium_destination_query": "Elite Private Airport Terminal",
            "premium_music_query": "Premium Minimalist Lounge Ambient",
            "breathing_exercise": {"active": False, "objective": "", "instruction": "", "duration_seconds": 240}
        }
    return response
