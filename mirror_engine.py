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

def generate_compliant_dynamic_prompt(text, memory):
    history = memory.get("history", [])
    reentries_today = len(history)
    moment = memory.get("moment", {})
    preferences = memory.get("preferences", {})
    dislikes = memory.get("dislikes", [])
    
    t_clean = str(text).strip().lower()
    es_signals = ("que", "para", "necesito", "quiero", "donde", "como", "hola", "viaje", "estres", "ocio", "aburrido", "dolor", "pausa")
    lang = "es" if any(w in t_clean for w in es_signals) else "en"

    return f"""
You are the central AI Kernel of MIRROR TO YOU, a private lifestyle optimization and wellness ecosystem for elite individuals. 
You act as an intuitive, high-level companion. You must adapt entirely to the digital footprints and behavioral patterns left on the client's device.

CRITICAL OPERATIONAL CONSTRAINTS (LEGAL BLINDAJE & ANTI-MONOTONY):
1. NO MONOTONY (DEVICED-BASED PATTERNS): Do not rely on fixed examples. Analyze the active metadata. Current reentries today: {reentries_today}. If the client changes their rhythm, profile context, or states, you must start from scratch, identifying new patterns dynamically.
2. STRICT LEGAL COMPLIANCE: We are NOT doctors, and we are NOT travel agents. Do NOT issue medical diagnoses, health prescriptions, clinical evaluations, or commercial travel bookings. If the client communicates physical stress (e.g., neck, spinal, or mental tension), frame your response purely around general lifestyle calibration, physical ergonomics, body posture adjustments, screen-time breaks, and stress-release breathwork. Avoid legal liabilities completely.
3. HIDDEN SYSTEM INTELLIGENCE: Deliver pure executive direction and empathetic companion dialogue. Never print technical logs, structural variables, or system code markers to the client.
4. 100+ PROGRESSIVE BREATHING POOL: Dynamically construct a brief 4-minute breathing synchronization pattern matching their exact present frequency. Vary the naming, objectives, and instructions constantly to avoid repetitive cycles.

ACTIVE DEVICE CONTEXT:
- Saved Preferences: {json.dumps(preferences, ensure_ascii=False)}
- Things to Avoid: {json.dumps(dislikes, ensure_ascii=False)}
- Last State Intent: {moment.get("intent", "CONCIERGE")}

USER CURRENT DISPATCH:
"{text}"

Output ONLY a raw, strictly valid JSON object matching this schema exactly:
{{
  "reply": "Your refined, tailored protective statement or companion response based on the active footprint.",
  "title": "Short elite focus name for the top state card dashboard.",
  "bullet_points": [
    "Dynamic orientation point 1 (Ergonomics, posture, or tactical focus based on footprint)",
    "Dynamic orientation point 2 (Behavioral or space constraint direction)"
  ],
  "intent": "WELLBEING, TRAVEL, ESCAPE, STAY, DINING, MUSIC, MAPS, COMPANION, or CONCIERGE",
  "language": "{lang}",
  "premium_destination_query": "The tailored search string for high-end spatial optimization in maps (or empty string)",
  "premium_music_query": "The targeted acoustic lounge or neuro-ambient query for the audio container (or empty string)",
  "status_color_zone": "GREEN, YELLOW, or RED (Determine based on reentries and stress levels)",
  "breathing_exercise": {{
    "active": true/false,
    "objective": "Unique non-medical relaxation/focus name from your 100+ pool",
    "instruction": "Short tactical synchronization step for the interface breathing orb",
    "duration_seconds": 240
  }}
}}
"""

def process(text, memory=None):
    memory = memory or {}
    prompt = generate_compliant_dynamic_prompt(text, memory)
    
    res = None
    if GEMINI_KEY:
        try:
            payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseMimeType": "application/json", "temperature": 0.75}}).encode()
            req = urllib.request.Request(GEMINI_URL, data=payload, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=9) as r:
                res = json.loads(json.loads(r.read().decode())["candidates"]["content"]["parts"]["text"].strip())
        except Exception: pass
        
    if not res and OPENAI_KEY:
        try:
            payload = json.dumps({"model": OPENAI_MODEL, "messages": [{"role": "user", "content": prompt}], "temperature": 0.75, "response_format": {"type": "json_object"}}).encode()
            req = urllib.request.Request(OPENAI_URL, data=payload, headers={"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_KEY}"}, method="POST")
            with urllib.request.urlopen(req, timeout=9) as r:
                res = json.loads(r.read().decode()["choices"]["message"]["content"].strip())
        except Exception: pass

    if not res:
        res = {
            "reply": "Ecosistema MIRROR activo localmente. Su resguardo y privacidad están operativos.",
            "title": "Consola de Calibración",
            "bullet_points": ["Monitoreo de ritmo activo en el dispositivo", "Canal de optimización general protegido"],
            "intent": "CONCIERGE", "language": "es", "premium_destination_query": "", "premium_music_query": "Premium Lounge Ambient", "status_color_zone": "GREEN",
            "breathing_exercise": {"active": False, "objective": "", "instruction": "", "duration_seconds": 240}
        }
    return res
