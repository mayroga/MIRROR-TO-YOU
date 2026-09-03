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

def generate_supreme_prompt(text, memory):
    history = memory.get("history", [])
    reentries = len(history)
    preferences = memory.get("preferences", {})
    dislikes = memory.get("dislikes", [])
    
    t_clean = str(text).strip().lower()
    es_signals = ("que", "para", "necesito", "quiero", "donde", "como", "hola", "estres", "ocio", "aburrido", "dolor", "pausa")
    lang = "es" if any(w in t_clean for w in es_signals) else "en"

    return f"""
You are the absolute AI Kernel of MIRROR TO YOU, a private lifestyle ecosystem for billionaires.
The client bypasses standard public interfaces. They have staff for bookings and logistics.
They open this app for instantaneous state change, mental calibration, and direct environmental control.

OPERATIONAL PARAMETERS (97%+ of system intelligence):
1. STATE OR VALIDATION: Handle automated state button dispatches or raw text/voice backup queries designed to test your intelligence.
2. COMPLIANCE BLINDAJE: We are NOT doctors or travel agents. Avoid medical jargon, clinical diagnostics, or booking confirmations. Frame physical or mental fatigue strictly as lifestyle calibration, ergonomics, screen-time breaks, and body posture stress-release work.
3. ANTI-MONOTONY (100 Entries): Current reentries today: {reentries}. Shift tone, language dynamics, and depth based on this frequency.
4. CLINICAL BREATHING POOL (100+): Generate a unique 4-minute respiratory synchronization rule (objective name and tactical rhythm) matching their exact footprint.
5. HIDDEN LOGISTICS: Never output mechanical system code markers or raw backend structures to the user.

DEVICE FOOTPRINT:
- Preferences: {json.dumps(preferences, ensure_ascii=False)}
- Dislikes: {json.dumps(dislikes, ensure_ascii=False)}

USER DISPATCH:
"{text}"

Output ONLY a raw, strictly valid JSON object matching this schema exactly:
{{
  "reply": "Your powerful, refined companion statement or protective direction based on active footprint.",
  "title": "Short elite focus name for the top state card dashboard.",
  "bullet_points": [
    "Dynamic orientation point 1 (Ergonomics, posture, or tactical focus based on footprint)",
    "Dynamic orientation point 2 (Behavioral or space constraint direction)"
  ],
  "intent": "WELLBEING, TRAVEL, ESCAPE, STAY, DINING, MUSIC, MAPS, COMPANION, or CONCIERGE",
  "language": "{lang}",
  "premium_destination_query": "The tailored search string for high-end spatial optimization in maps (or empty string)",
  "premium_music_query": "The targeted acoustic lounge or neuro-ambient query for the audio container (or empty string)",
  "status_color_zone": "GREEN, YELLOW, or RED",
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
    prompt = generate_supreme_prompt(text, memory)
    
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
