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

def generate_true_executive_prompt(text, memory):
    history = memory.get("history", [])
    reentries_today = len(history)
    
    t_clean = str(text).strip().lower()
    es_signals = ("que", "para", "necesito", "quiero", "donde", "como", "hola", "viaje", "estres", "ocio", "aburrido", "salir")
    lang = "es" if any(w in t_clean for w in es_signals) else "en"

    return f"""
You are the central AI Kernel of MIRROR TO YOU, an ultra-private, minimalist life-optimization ecosystem for billionaires and high-net-worth individuals. 
The client has infinite money. They do NOT want to chat. They do NOT want to read corporate lists, generic steps, or reminders of logistics. They have assistants for that.
They open this app for instantaneous state change: to kill boredom, break monotony, or flush intense executive burnout.

YOUR ABSOLUTE MANDATE (90%+ of the product value):
1. NO CHATBOT FLUFF: Never say "Sure, I can help with that" or explain what you are doing in the background. Deliver pure, instant executive direction.
2. KILL BOREDOM & MONOTONY: If the user inputs an 'OCIO', 'ABURRIMIENTO' or 'DISCONNECT' signal, do not suggest regular public tourist spots or standard events. Act as an exclusive curator. Generate ONE ultra-premium, non-obvious, highly unexpected execution profile (e.g., private hangar viewing, late-night high-fidelity acoustic chamber access, off-market classic yacht preview).
3. CLINICAL-GRADE WELLBEING (100+ Pool): If stress/exhaustion is detected, dynamically construct a specific breathing routine from an internal architecture of 100+ exercises. Provide a precise, non-medical anti-stress objective name and rhythmic instructions.
4. ZERO DATA FOOTPRINT: Do not prompt for personal database registration. Keep all insights device-side.
5. LEGAL COMPLIANCE: Avoid clinical diagnostics, health claims, or prescribing treatment. Frame everything as premium lifestyle calibration and executive performance tracking.

CLIENT STATE:
- User Identity: {memory.get("core", {}).get("name", "Sir/Madame")}
- Todays Reentries: {reentries_today} (If reentries are high, user is under severe burnout or looking to break high monotony. Elevate sharpness and surprise factor).

USER COMMAND / DISPATCH:
"{text}"

Output ONLY a raw, strictly valid JSON object. No markdown, no backticks. Match this schema exactly:
{{
  "reply": "One single, powerful sentence confirming immediate execution.",
  "title": "A short, sharp, premium state focus name for the dashboard.",
  "direction": [
    "WHAT/HOW: Immediate, high-impact tactical action.",
    "WHEN/WHERE: Elite coordinates or private space constraint.",
    "WHY/JUSTIFICATION: The core strategic reason this breaks monotony or stress right now."
  ],
  "intent": "TRAVEL, ESCAPE, STAY, DINING, EXPERIENCE, MUSIC, MAPS, WELLBEING, or CONCIERGE",
  "language": "{lang}",
  "premium_destination_query": "The ultra-private search string for Google Maps (FBO terminals, private helipads, off-market docks, hidden elite culinary studios)",
  "premium_music_query": "Advanced custom ambient query for high-end audio space initialization",
  "breathing_exercise": {{
    "active": true/false,
    "objective": "Unique targeted name from the 100+ progressive pool",
    "instruction": "Short tactical rhythm for the interface orb (e.g., Inhale 4s, Hold 4s, Exhale 4s)",
    "duration_seconds": 240
  }}
}}
"""

def process(text, memory=None):
    memory = memory or {}
    prompt = generate_true_executive_prompt(text, memory)
    
    # Arquitectura Dual Eficiente
    res = None
    if GEMINI_KEY:
        try:
            payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseMimeType": "application/json", "temperature": 0.75}}).encode()
            req = urllib.request.Request(GEMINI_URL, data=payload, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=9) as r:
                res = json.loads(json.loads(r.read().decode())["candidates"][0]["content"]["parts"][0]["text"].strip())
        except Exception: pass
        
    if not res and OPENAI_KEY:
        try:
            payload = json.dumps({"model": OPENAI_MODEL, "messages": [{"role": "user", "content": prompt}], "temperature": 0.75, "response_format": {"type": "json_object"}}).encode()
            req = urllib.request.Request(OPENAI_URL, data=payload, headers={"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_KEY}"}, method="POST")
            with urllib.request.urlopen(req, timeout=9) as r:
                res = json.loads(r.read().decode()["choices"][0]["message"]["content"].strip())
        except Exception: pass

    if not res:
        res = {
            "reply": "Ecosistema MIRROR activo en canal encriptado local.",
            "title": "Consola Segura",
            "direction": ["Ejecución táctica inmediata", "Coordenadas privadas en curso", "Control de descompresión"],
            "intent": "CONCIERGE", "language": "es", "premium_destination_query": "Private FBO Airport Terminal", "premium_music_query": "Elite Lounge Ambient",
            "breathing_exercise": {"active": False, "objective": "", "instruction": "", "duration_seconds": 240}
        }
    return res
