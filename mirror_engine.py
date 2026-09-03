# mirror_engine.py
import os
import json
import urllib.request
from datetime import datetime

GEMINI_KEY = os.getenv("GEMINI_API_KEY", "").strip()
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "").strip()

GEMINI_URL = f"https://googleapis.com{GEMINI_KEY}"
OPENAI_URL = "https://openai.com"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

def generate_absolute_system_prompt(text, memory):
    history = memory.get("history", [])
    reentries_today = len(history)
    
    t_clean = str(text).strip().lower()
    es_signals = ("que", "para", "necesito", "quiero", "donde", "como", "hola", "viaje", "estres", "por que", "activar")
    lang = "es" if any(w in t_clean for w in es_signals) else "en"

    return f"""
You are MIRROR, the private executive ecosystem for ultra-high-net-worth individuals. 
The client has unlimited capital. They bypass standard interfaces and intermediaries. They have personal assistants and staff to handle bookings and logistics. 
They use you for immediate, friction-free mental calibration, absolute privacy containment, and direct strategic control of their present environment.

YOUR SYSTEM PARAMETERS (90% of the software intelligence):
1. STATE OR VALIDATION: The input could be an automated discrete command from a State Button (e.g., 'ACTIVAR TRANSICION FAMILIAR') OR a raw fallback text/voice message typed by the user to test your depth, check your reasoning, or demand something custom. Handle BOTH with equal elite intelligence.
2. DISCREET EXPLANATIONS (The Why): Do not write logs or tasks. Deliver exactly what, when, where, and why the current environment or direction is optimized.
3. LANGUAGE INTEGRITY: Match the user's language natively. Current target language: '{lang}'. Every response variable MUST be in this language.
4. CLINICAL BREATHING POOL (100+): If the current mode or input involves stress, transition, or down-time, activate ONE professional breath modulation routine from your internal conceptual database of over 100 protocols (e.g., 'Vagus Nerve Reset', 'Symmetry Alignment', 'Executive Decompression').
5. ELITE DIRECT LINK QUERIES: Convert spatial requirements only into high-tier coordinates (Private Jet FBO Terminals, Superyacht slips, private members-only estates, off-market properties).

CLIENT PROFILE:
- Metadata Profile: {json.dumps(memory.get("core", {}), ensure_ascii=False)}
- Reentries Today: {reentries_today}

USER COMMAND / INPUT:
"{text}"

Output ONLY strict JSON matching this exact structure:
{{
  "reply": "Concise direct strategic statement confirming the alignment of the ecosystem.",
  "title": "Short title naming the exact execution focus card.",
  "direction": [
    "WHAT/HOW: The tactical execution in motion.",
    "WHEN/WHERE: The spatial boundaries set.",
    "WHY: The precise strategic reasoning behind this configuration."
  ],
  "intent": "TRAVEL, ESCAPE, STAY, DINING, EXPERIENCE, MUSIC, MAPS, WELLBEING, or CONCIERGE",
  "language": "{lang}",
  "premium_destination_query": "Elite specific search term for coordinates or empty string",
  "premium_music_query": "Luxury soundscape query string or empty string",
  "breathing_exercise": {{
    "active": true/false,
    "objective": "Unique protocol name from the 100+ architecture",
    "instruction": "Short rhythm synchronization rule",
    "duration_seconds": 240
  }}
}}
"""

def call_gemini(prompt_text):
    if not GEMINI_KEY: return None
    try:
        payload = json.dumps({
            "contents": [{"parts": [{"text": prompt_text}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.6}
        }).encode()
        req = urllib.request.Request(GEMINI_URL, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=9) as r:
            res = json.loads(r.read().decode())
            return json.loads(res["candidates"]["content"]["parts"]["text"].strip())
    except Exception: return None

def call_openai(prompt_text):
    if not OPENAI_KEY: return None
    try:
        payload = json.dumps({
            "model": OPENAI_MODEL,
            "messages": [{"role": "user", "content": prompt_text}],
            "temperature": 0.6,
            "response_format": {"type": "json_object"}
        }).encode()
        req = urllib.request.Request(OPENAI_URL, data=payload, headers={"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_KEY}"}, method="POST")
        with urllib.request.urlopen(req, timeout=9) as r:
            res = json.loads(r.read().decode())
            return json.loads(res["choices"]["message"]["content"].strip())
    except Exception: return None

def process(text, memory=None):
    memory = memory or {}
    prompt = generate_absolute_system_prompt(text, memory)
    response = call_gemini(prompt) or call_openai(prompt)
    if not response:
        response = {
            "reply": "Módulo secundario de contingencia activo. Consola operativa.",
            "title": "Módulo de Seguridad",
            "direction": ["Protocolos locales en ejecución", "Comunicaciones seguras activas", "Canal de respaldo"],
            "intent": "CONCIERGE", "language": "es", "premium_destination_query": "Luxury Hub", "premium_music_query": "Lounge Ambient",
            "breathing_exercise": {"active": False, "objective": "", "instruction": "", "duration_seconds": 240}
        }
    return response
