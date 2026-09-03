import os
import json
import re
import random
import urllib.request
import urllib.parse
from datetime import datetime, timezone

OPENAI_API_KEY=os.getenv("OPENAI_API_KEY","").strip()
GEMINI_API_KEY=os.getenv("GEMINI_API_KEY","").strip()
OPENAI_MODEL=os.getenv("OPENAI_MODEL","gpt-5-mini").strip()
GEMINI_MODEL=os.getenv("GEMINI_MODEL","gemini-2.5-flash").strip()

try:
    AI_TIMEOUT=float(os.getenv("MIRROR_AI_TIMEOUT","35"))
except (TypeError,ValueError):
    AI_TIMEOUT=35.0

SYSTEM_MEMORY_RULES=[
    "daily_priority",
    "today_first",
    "avoid_same_day_repetition",
    "adapt_when_similar",
    "respect_explicit_request",
    "learn_from_feedback",
    "never_claim_unconfirmed_execution",
    "ai_invisible_to_client",
    "use_memory_before_decision",
    "breathing_available_when_context_supports_it"
]

BREATHING_PATTERNS=[
    {"id":"breath_01","name":"Calma suave","inhale":4,"hold":0,"exhale":4,"pause":0},
    {"id":"breath_02","name":"Exhalación larga","inhale":4,"hold":0,"exhale":6,"pause":0},
    {"id":"breath_03","name":"Ritmo ligero","inhale":3,"hold":0,"exhale":5,"pause":0},
    {"id":"breath_04","name":"Soltar tensión","inhale":4,"hold":2,"exhale":6,"pause":0},
    {"id":"breath_05","name":"Equilibrio","inhale":4,"hold":4,"exhale":6,"pause":0},
    {"id":"breath_06","name":"Respiración estable","inhale":5,"hold":0,"exhale":5,"pause":0},
    {"id":"breath_07","name":"Descarga","inhale":3,"hold":3,"exhale":6,"pause":0},
    {"id":"breath_08","name":"Preparación tranquila","inhale":4,"hold":7,"exhale":4,"pause":0},
    {"id":"breath_09","name":"Recuperación","inhale":5,"hold":0,"exhale":7,"pause":0},
    {"id":"breath_10","name":"Espacio","inhale":4,"hold":1,"exhale":5,"pause":0}
]

BREATHING_NEEDS=[
    "calm",
    "slow_down",
    "release_tension",
    "regain_focus",
    "prepare_for_sleep",
    "wake_gently",
    "recover_energy",
    "create_space",
    "reset_attention",
    "reduce_overload",
    "clear_the_mind",
    "pause",
    "ground",
    "feel_present",
    "transition",
    "prepare_for_day",
    "prepare_for_meeting",
    "prepare_for_trip",
    "recover_after_travel",
    "settle_emotions",
    "reduce_rushing",
    "restore_patience",
    "soften_frustration",
    "recover_from_disappointment",
    "create_distance",
    "think_clearly",
    "make_a_decision",
    "before_important_message",
    "after_difficult_message",
    "reduce_social_pressure",
    "prepare_to_speak",
    "prepare_to_listen",
    "recover_after_conversation",
    "quiet_the_day",
    "start_again",
    "end_the_day",
    "change_scene",
    "leave_a_bad_moment",
    "enter_a_new_moment",
    "restore_balance",
    "slow_thoughts",
    "organize_thoughts",
    "reduce_distraction",
    "support_concentration",
    "prepare_for_creativity",
    "open_imagination",
    "restore_curiosity",
    "make_room_for_ideas",
    "recover_motivation",
    "begin_small",
    "finish_something",
    "release_perfectionism",
    "accept_uncertainty",
    "reduce_control",
    "create_confidence",
    "prepare_for_change",
    "adapt_to_change",
    "recover_after_surprise",
    "restore_composure",
    "before_travel",
    "during_travel",
    "after_arrival",
    "before_rest",
    "during_rest",
    "after_rest",
    "morning_reset",
    "afternoon_reset",
    "evening_reset",
    "night_reset",
    "between_tasks",
    "before_sleep",
    "after_waking",
    "after_long_screen_time",
    "after_noise",
    "after_crowd",
    "after_waiting",
    "before_choice",
    "after_choice",
    "before_purchase_decision",
    "before_planning",
    "after_planning",
    "when_time_feels_short",
    "when_day_feels_full",
    "when_everything_feels_same",
    "when_need_is_unclear",
    "when_words_are_difficult",
    "when_attention_is_scattered",
    "when_energy_is_low",
    "when_energy_is_high",
    "when_needing_a_pause",
    "when_needing_movement",
    "when_needing_stillness",
    "when_needing_privacy",
    "when_needing_connection",
    "when_needing_a_fresh_start",
    "when_needing_closure",
    "when_needing_a_small_win",
    "when_needing_a_new_view"
]

def now_utc():
    return datetime.now(timezone.utc)

def today_key():
    return now_utc().strftime("%Y-%m-%d")

def safe_text(value,default=""):
    if value is None:
        return default
    if isinstance(value,str):
        return value.strip()
    return str(value).strip()

def clean_list(value):
    if not isinstance(value,list):
        return []
    return [safe_text(x) for x in value if safe_text(x)]

def normalize_memory(memory):
    if not isinstance(memory,dict):
        memory={}

    memory.setdefault("core",{})
    memory.setdefault("preferences",{})
    memory.setdefault("dislikes",[])
    memory.setdefault("history",[])
    memory.setdefault("daily",{})
    memory.setdefault("feedback",[])
    memory.setdefault("profile",{})

    if not isinstance(memory["core"],dict):
        memory["core"]={}

    if not isinstance(memory["preferences"],dict):
        memory["preferences"]={}

    if not isinstance(memory["dislikes"],list):
        memory["dislikes"]=[]

    if not isinstance(memory["history"],list):
        memory["history"]=[]

    if not isinstance(memory["daily"],dict):
        memory["daily"]={}

    if not isinstance(memory["feedback"],list):
        memory["feedback"]=[]

    if not isinstance(memory["profile"],dict):
        memory["profile"]={}

    key=today_key()

    if not isinstance(memory["daily"].get(key),list):
        memory["daily"][key]=[]

    memory["daily"][key]=memory["daily"][key][-120:]
    memory["history"]=memory["history"][-100:]
    memory["feedback"]=memory["feedback"][-50:]

    return memory

def today_history(memory):
    memory=normalize_memory(memory)
    return memory["daily"].get(today_key(),[])

def used_today(memory):
    history=today_history(memory)

    result={
        "exercise_ids":set(),
        "patterns":set(),
        "actions":set(),
        "phrases":set(),
        "titles":set(),
        "experience_ids":set()
    }

    for item in history:
        if not isinstance(item,dict):
            continue

        for key in result:
            value=item.get(key)

            if isinstance(value,list):
                for entry in value:
                    if safe_text(entry):
                        result[key].add(
                            safe_text(entry).lower()
                        )
            elif safe_text(value):
                result[key].add(
                    safe_text(value).lower()
                )

        breathing=item.get("breathing")

        if isinstance(breathing,dict):
            exercise_id=safe_text(
                breathing.get("exercise_id")
            ).lower()

            pattern=safe_text(
                breathing.get("pattern")
            ).lower()

            if exercise_id:
                result["exercise_ids"].add(exercise_id)

            if pattern:
                result["patterns"].add(pattern)

    return result

def remember_today(memory,experience):
    memory=normalize_memory(memory)

    key=today_key()

    memory["daily"].setdefault(key,[])
    memory["daily"][key].append(experience)
    memory["daily"][key]=memory["daily"][key][-120:]

    memory["history"].append(experience)
    memory["history"]=memory["history"][-100:]

    return memory

def extract_signals(message):
    text=safe_text(message).lower()
    signals=[]

    mapping={
        "stress":[
            "stress","estres","tension","tenso",
            "overwhelmed","agobiad","pressure","presion"
        ],
        "anxiety":[
            "anxious","ansiedad","nervous",
            "nervioso","worried","preocup"
        ],
        "fatigue":[
            "tired","cansado","fatiga",
            "exhausted","agotado","low energy"
        ],
        "sleep":[
            "sleep","dormir","insomnia",
            "insomnio","night","noche","bed","cama"
        ],
        "focus":[
            "focus","concentr","attention",
            "atencion","distracted","distraido"
        ],
        "calm":[
            "calm","calma","relax",
            "relajar","peace","tranquilo"
        ],
        "decision":[
            "decision","decidir","choose",
            "elegir","choice","opcion"
        ],
        "travel":[
            "travel","viaje","trip","vacation",
            "vacaciones","flight","vuelo"
        ],
        "music":[
            "music","musica","song",
            "cancion","youtube"
        ],
        "map":[
            "map","mapa","location",
            "ubicacion","place","lugar"
        ],
        "privacy":[
            "private","privado","privacy",
            "privacidad","discreet","discreto"
        ],
        "urgent":[
            "urgent","urgente","asap",
            "immediately","ahora"
        ],
        "rest":[
            "rest","descanso","break",
            "pausa","pause"
        ],
        "energy":[
            "energy","energia","wake",
            "despertar","active","activo"
        ],
        "money":[
            "budget","presupuesto",
            "cost","precio","expensive","caro"
        ]
    }

    for signal,words in mapping.items():
        if any(word in text for word in words):
            signals.append(signal)

    return signals

def detect_intent(message):
    text=safe_text(message).lower()

    if any(x in text for x in [
        "map","mapa","where","donde",
        "location","ubicacion"
    ]):
        return "location"

    if any(x in text for x in [
        "music","musica","song",
        "cancion","listen","escuchar"
    ]):
        return "music"

    if any(x in text for x in [
        "hotel","flight","vuelo",
        "trip","viaje","travel",
        "vacation","vacaciones"
    ]):
        return "travel"

    if any(x in text for x in [
        "book","reserve",
        "reservation","reservar","reserva"
    ]):
        return "reservation"

    if any(x in text for x in [
        "decide","decision",
        "choose","elegir",
        "should i","deberia"
    ]):
        return "decision"

    if any(x in text for x in [
        "breathe","breathing",
        "respirar","respiracion"
    ]):
        return "breathing"

    if any(x in text for x in [
        "sleep","dormir",
        "rest","descanso"
    ]):
        return "rest"

    return "concierge"

def detect_duration(message):
    text=safe_text(message)

    matches=re.findall(
        r"(\d+)\s*(?:min|mins|minute|minutes|minuto|minutos)",
        text,
        re.I
    )

    if matches:
        try:
            return int(matches[0])
        except (TypeError,ValueError):
            pass

    return None

def detect_budget(message):
    text=safe_text(message)

    patterns=[
        r"\$\s?(\d+(?:[.,]\d+)?)",
        r"(?:under|menos de|hasta|maximo|máximo)\s+\$?\s?(\d+(?:[.,]\d+)?)"
    ]

    for pattern in patterns:
        match=re.search(pattern,text,re.I)

        if match:
            try:
                return float(
                    match.group(1).replace(",","")
                )
            except (TypeError,ValueError):
                pass

    return None

def detect_destination(message):
    text=safe_text(message)

    patterns=[
        r"(?:to|en|para|from|desde)\s+([A-Za-zÀ-ÿ0-9 .,'-]{2,50})"
    ]

    for pattern in patterns:
        match=re.search(pattern,text,re.I)

        if match:
            value=match.group(1).strip(
                " .,!?:;"
            )

            if value:
                return value

    return None

def detect_companion(message):
    text=safe_text(message).lower()

    if any(x in text for x in [
        "alone","solo","sola",
        "myself","yo solo"
    ]):
        return "alone"

    if any(x in text for x in [
        "wife","esposa","husband",
        "esposo","partner","pareja"
    ]):
        return "partner"

    if any(x in text for x in [
        "family","familia","children",
        "hijos","kids","niños"
    ]):
        return "family"

    if any(x in text for x in [
        "friend","amigo","amiga",
        "friends","amigos"
    ]):
        return "friends"

    return None

def understand(message):
    message=safe_text(message)

    return {
        "message":message,
        "intent":detect_intent(message),
        "signals":extract_signals(message),
        "duration":detect_duration(message),
        "budget":detect_budget(message),
        "destination":detect_destination(message),
        "companion":detect_companion(message)
    }

def personalize_local(understanding,memory):
    memory=normalize_memory(memory)
    history=today_history(memory)
    used=used_today(memory)

    return {
        "core":memory.get("core",{}),
        "preferences":memory.get("preferences",{}),
        "dislikes":memory.get("dislikes",[]),
        "profile":memory.get("profile",{}),
        "today_experiences":history[-30:],
        "today_count":len(history),
        "avoid_today":{
            "exercise_ids":list(
                used["exercise_ids"]
            ),
            "patterns":list(
                used["patterns"]
            ),
            "actions":list(
                used["actions"]
            ),
            "phrases":list(
                used["phrases"]
            ),
            "titles":list(
                used["titles"]
            ),
            "experience_ids":list(
                used["experience_ids"]
            )
        }
    }

def decide(understanding,personalization):
    signals=set(
        understanding.get("signals",[])
    )

    intent=understanding.get(
        "intent",
        "concierge"
    )

    breathing_needed=(
        intent=="breathing"
        or bool(
            signals.intersection({
                "stress",
                "anxiety",
                "fatigue",
                "sleep",
                "focus",
                "calm",
                "rest",
                "energy"
            })
        )
    )

    if intent=="travel":
        category="travel"
    elif intent=="location":
        category="location"
    elif intent=="music":
        category="music"
    elif intent=="reservation":
        category="reservation"
    elif intent=="decision":
        category="decision"
    else:
        category="concierge"

    priority="high" if "urgent" in signals else "normal"

    return {
        "category":category,
        "priority":priority,
        "breathing_recommended":breathing_needed,
        "reason":"context_match",
        "today_count":personalization.get(
            "today_count",
            0
        )
    }

def build_breathing_exercises():
    purposes=[
        "calm",
        "focus",
        "reset",
        "rest",
        "energy",
        "grounding",
        "transition",
        "clarity",
        "patience",
        "space",
        "confidence",
        "presence",
        "release",
        "renewal"
    ]

    exercises=[]

    for pattern in BREATHING_PATTERNS:
        for purpose in purposes:
            exercises.append({
                "exercise_id":(
                    f'{pattern["id"]}_{purpose}'
                ),
                "pattern_id":pattern["id"],
                "purpose":purpose,
                "name":(
                    f'{pattern["name"]} · {purpose}'
                ),
                "inhale":pattern["inhale"],
                "hold":pattern["hold"],
                "exhale":pattern["exhale"],
                "pause":pattern["pause"]
            })

    return exercises

BREATHING_EXERCISES=build_breathing_exercises()

def choose_need(understanding):
    signals=set(
        understanding.get("signals",[])
    )

    if "sleep" in signals:
        return "prepare_for_sleep"

    if "focus" in signals:
        return "regain_focus"

    if "fatigue" in signals:
        return "recover_energy"

    if "stress" in signals or "anxiety" in signals:
        return "calm"

    if "rest" in signals:
        return "create_space"

    if "energy" in signals:
        return "wake_gently"

    if "decision" in signals:
        return "make_a_decision"

    return random.choice(
        BREATHING_NEEDS
    )

def select_breathing_from_library(
    understanding,
    personalization
):
    used=personalization.get(
        "avoid_today",
        {}
    )

    used_ids={
        safe_text(x).lower()
        for x in used.get(
            "exercise_ids",
            []
        )
    }

    used_patterns={
        safe_text(x).lower()
        for x in used.get(
            "patterns",
            []
        )
    }

    need=choose_need(
        understanding
    )

    candidates=[
        x for x in BREATHING_EXERCISES
        if x["exercise_id"].lower()
        not in used_ids
        and x["pattern_id"].lower()
        not in used_patterns
    ]

    if not candidates:
        candidates=[
            x for x in BREATHING_EXERCISES
            if x["exercise_id"].lower()
            not in used_ids
        ]

    if not candidates:
        candidates=list(
            BREATHING_EXERCISES
        )

    preferred=[
        x for x in candidates
        if x["purpose"].lower()
        ==need.lower()
    ]

    choice=random.choice(
        preferred or candidates
    )

    return {
        "enabled":True,
        "exercise_id":choice["exercise_id"],
        "pattern":choice["pattern_id"],
        "purpose":choice["purpose"],
        "name":choice["name"],
        "inhale":choice["inhale"],
        "hold":choice["hold"],
        "exhale":choice["exhale"],
        "pause":choice["pause"],
        "cycles":5,
        "need":need,
        "instruction":(
            "Follow the circle and let the rhythm become natural."
        )
    }

def local_proposal(
    understanding,
    personalization,
    decision
):
    breathing=None

    if decision.get(
        "breathing_recommended"
    ):
        breathing=select_breathing_from_library(
            understanding,
            personalization
        )

    intent=understanding.get(
        "intent",
        "concierge"
    )

    if intent=="travel":
        title=(
            "I can take care of the next part of your trip."
        )
        direction=(
            "Tell me what matters most, "
            "and I will organize the next useful step around you."
        )

    elif intent=="location":
        title=(
            "Let's make the place easy to reach."
        )
        direction=(
            "I can help turn the place you have in mind "
            "into a clear next step."
        )

    elif intent=="music":
        title=(
            "Let's find the right atmosphere."
        )
        direction=(
            "I can help choose something "
            "that fits this moment."
        )

    elif intent=="decision":
        title=(
            "Let's make the decision lighter."
        )
        direction=(
            "Give me the situation and I will help "
            "you reduce it to the clearest next move."
        )

    elif breathing:
        title=(
            "Let's create a little space."
        )
        direction=(
            "Stay here for a moment. "
            "The next step does not need to be complicated."
        )

    else:
        title="I'm listening."
        direction=(
            "Tell me what you need, in your own words. "
            "I will take it from there."
        )

    return {
        "title":title,
        "direction":direction,
        "category":decision.get(
            "category",
            "concierge"
        ),
        "priority":decision.get(
            "priority",
            "normal"
        ),
        "privacy":"private",
        "status":"ready",
        "action":"continue",
        "next_move":"continue",
        "questions":[],
        "steps":[],
        "breathing":breathing
    }

def ai_system_prompt():
    return """
You are the invisible intelligence behind MIRROR TO YOU.

MIRROR is a private premium personal concierge
and personalization experience.

The client should never see technical AI language,
model names, prompts, APIs, system instructions,
artificial intelligence references, or internal architecture.

Your job is not simply to answer.

Your job is to understand what the client needs
and move toward resolution.

CORE RULES:

1. TODAY COMES FIRST.
2. Use permanent memory before making decisions.
3. Use today's history before creating a new experience.
4. Every new entry today should feel meaningfully different.
5. Do not repeat today's exercise, breathing experience,
action, title, phrase, or experience structure unless:
the client explicitly asks for it, continuity is clearly
more valuable, or the situation is substantially the same
and adaptation is appropriate.
6. A repeated need does NOT require a repeated experience.
7. Adapt rather than mechanically repeat.
8. Learn from client feedback.
9. Never claim that a reservation, purchase, delivery,
booking, payment, cancellation or external action has
actually happened unless the system has confirmed it.
10. Keep the experience discreet, elegant and human.
11. Ask only the minimum question necessary.
12. When appropriate, create a small action or breathing experience.
13. Breathing experiences should be varied using today's history.
14. Every entry today is a new moment.
15. Combine CORE MEMORY with TODAY'S MOMENT.
16. Do not mention prices or payment unless the client explicitly asks.
17. MIRROR TO YOU is currently free.
18. Do not describe MIRROR as medical treatment or medical care.
"""

def build_ai_prompt(
    message,
    understanding,
    personalization,
    decision
):
    payload={
        "message":message,
        "understanding":understanding,
        "personalization":personalization,
        "decision":decision,
        "today_history":personalization.get(
            "today_experiences",
            []
        )[-30:],
        "breathing_library":{
            "needs":BREATHING_NEEDS,
            "available_exercises":BREATHING_EXERCISES
        }
    }

    return (
        ai_system_prompt()
        +
        """
Return ONLY valid JSON.

Structure:

{
  "title":"",
  "direction":"",
  "category":"",
  "priority":"",
  "privacy":"private",
  "status":"ready",
  "action":"",
  "next_move":"",
  "questions":[],
  "steps":[],
  "breathing":null
}

If breathing is appropriate:

{
  "enabled":true,
  "exercise_id":"",
  "pattern":"",
  "purpose":"",
  "name":"",
  "inhale":4,
  "hold":0,
  "exhale":6,
  "pause":0,
  "cycles":5,
  "need":"",
  "instruction":""
}

Never repeat an exercise_id or pattern already
used today unless adaptation or explicit continuity
is necessary.

CLIENT DATA:

"""
        +
        json.dumps(
            payload,
            ensure_ascii=False
        )
    )

def http_json(
    url,
    payload,
    headers=None,
    timeout=None
):
    data=json.dumps(
        payload,
        ensure_ascii=False
    ).encode("utf-8")

    request=urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type":"application/json",
            **(headers or {})
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout or AI_TIMEOUT
        ) as response:
            raw=response.read().decode(
                "utf-8"
            )
            return json.loads(raw)
    except Exception:
        return None

def call_openai(prompt):
    if not OPENAI_API_KEY:
        return None

    payload={
        "model":OPENAI_MODEL,
        "messages":[
            {
                "role":"system",
                "content":ai_system_prompt()
            },
            {
                "role":"user",
                "content":prompt
            }
        ],
        "temperature":0.85,
        "response_format":{
            "type":"json_object"
        }
    }

    result=http_json(
        "https://api.openai.com/v1/chat/completions",
        payload,
        headers={
            "Authorization":
            f"Bearer {OPENAI_API_KEY}"
        }
    )

    if not result:
        return None

    try:
        content=(
            result
            ["choices"]
            [0]
            ["message"]
            ["content"]
        )

        return json.loads(content)

    except Exception:
        return None

def call_gemini(prompt):
    if not GEMINI_API_KEY:
        return None

    url=(
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/"
        f"{GEMINI_MODEL}:generateContent"
    )

    payload={
        "contents":[
            {
                "role":"user",
                "parts":[
                    {
                        "text":prompt
                    }
                ]
            }
        ],
        "generationConfig":{
            "temperature":0.85,
            "responseMimeType":"application/json"
        }
    }

    result=http_json(
        url,
        payload,
        headers={
            "x-goog-api-key":GEMINI_API_KEY
        }
    )

    if not result:
        return None

    try:
        text=(
            result
            ["candidates"]
            [0]
            ["content"]
            ["parts"]
            [0]
            ["text"]
        )

        return json.loads(text)

    except Exception:
        return None

def sanitize_ai(
    ai_result,
    understanding,
    personalization,
    decision
):
    local=local_proposal(
        understanding,
        personalization,
        decision
    )

    if not isinstance(
        ai_result,
        dict
    ):
        return local

    result={
        "title":safe_text(
            ai_result.get("title")
        ) or local["title"],
        "direction":safe_text(
            ai_result.get("direction")
        ) or local["direction"],
        "category":safe_text(
            ai_result.get("category")
        ) or local["category"],
        "priority":safe_text(
            ai_result.get("priority")
        ) or local["priority"],
        "privacy":"private",
        "status":safe_text(
            ai_result.get("status")
        ) or "ready",
        "action":safe_text(
            ai_result.get("action")
        ) or "continue",
        "next_move":safe_text(
            ai_result.get("next_move")
        ) or "continue",
        "questions":clean_list(
            ai_result.get("questions")
        ),
        "steps":clean_list(
            ai_result.get("steps")
        ),
        "breathing":None
    }

    breathing=ai_result.get(
        "breathing"
    )

    if (
        isinstance(breathing,dict)
        and breathing.get("enabled")
    ):
        breathing_id=safe_text(
            breathing.get("exercise_id")
        )

        pattern=safe_text(
            breathing.get("pattern")
        )

        used=personalization.get(
            "avoid_today",
            {}
        )

        used_ids={
            safe_text(x).lower()
            for x in used.get(
                "exercise_ids",
                []
            )
        }

        used_patterns={
            safe_text(x).lower()
            for x in used.get(
                "patterns",
                []
            )
        }

        valid_id=(
            breathing_id
            and breathing_id.lower()
            not in used_ids
        )

        valid_pattern=(
            not pattern
            or pattern.lower()
            not in used_patterns
        )

        if valid_id and valid_pattern:
            try:
                inhale=int(
                    breathing.get(
                        "inhale",
                        4
                    )
                )
            except Exception:
                inhale=4

            try:
                hold=int(
                    breathing.get(
                        "hold",
                        0
                    )
                )
            except Exception:
                hold=0

            try:
                exhale=int(
                    breathing.get(
                        "exhale",
                        6
                    )
                )
            except Exception:
                exhale=6

            try:
                pause=int(
                    breathing.get(
                        "pause",
                        0
                    )
                )
            except Exception:
                pause=0

            try:
                cycles=int(
                    breathing.get(
                        "cycles",
                        5
                    )
                )
            except Exception:
                cycles=5

            result["breathing"]={
                "enabled":True,
                "exercise_id":breathing_id,
                "pattern":pattern or "custom",
                "purpose":(
                    safe_text(
                        breathing.get(
                            "purpose"
                        )
                    ) or "reset"
                ),
                "name":(
                    safe_text(
                        breathing.get(
                            "name"
                        )
                    ) or "A moment for you"
                ),
                "inhale":max(
                    1,
                    min(inhale,10)
                ),
                "hold":max(
                    0,
                    min(hold,10)
                ),
                "exhale":max(
                    1,
                    min(exhale,12)
                ),
                "pause":max(
                    0,
                    min(pause,10)
                ),
                "cycles":max(
                    1,
                    min(cycles,12)
                ),
                "need":(
                    safe_text(
                        breathing.get(
                            "need"
                        )
                    ) or choose_need(
                        understanding
                    )
                ),
                "instruction":(
                    safe_text(
                        breathing.get(
                            "instruction"
                        )
                    )
                    or
                    "Follow the circle and let the rhythm become natural."
                )
            }

    if (
        decision.get(
            "breathing_recommended"
        )
        and result["breathing"] is None
    ):
        result["breathing"]=_select_unique_breathing(
            understanding,
            personalization
        )

    return result

def _select_unique_breathing(
    understanding,
    personalization
):
    return select_breathing_from_library(
        understanding,
        personalization
    )

def make_experience_record(
    message,
    understanding,
    decision,
    proposal
):
    breathing=proposal.get(
        "breathing"
    )

    timestamp=now_utc().isoformat()

    experience_id=(
        "exp_"
        +
        now_utc().strftime(
            "%Y%m%d%H%M%S%f"
        )
    )

    record={
        "experience_id":experience_id,
        "timestamp":timestamp,
        "date":today_key(),
        "message":safe_text(message),
        "category":proposal.get(
            "category"
        ),
        "title":proposal.get(
            "title"
        ),
        "action":proposal.get(
            "action"
        ),
        "intent":understanding.get(
            "intent"
        ),
        "signals":understanding.get(
            "signals",
            []
        ),
        "experience_ids":[
            experience_id
        ],
        "exercise_ids":[],
        "patterns":[],
        "actions":[
            proposal.get(
                "action",
                ""
            )
        ],
        "phrases":[
            proposal.get(
                "direction",
                ""
            )
        ],
        "titles":[
            proposal.get(
                "title",
                ""
            )
        ],
        "breathing":breathing
    }

    if breathing:
        exercise_id=safe_text(
            breathing.get(
                "exercise_id"
            )
        )

        pattern=safe_text(
            breathing.get(
                "pattern"
            )
        )

        if exercise_id:
            record["exercise_ids"].append(
                exercise_id
            )

        if pattern:
            record["patterns"].append(
                pattern
            )

    return record

def update_learning(
    memory,
    understanding,
    proposal
):
    memory=normalize_memory(
        memory
    )

    profile=memory.setdefault(
        "profile",
        {}
    )

    intent=understanding.get(
        "intent"
    )

    if intent:
        profile["last_intent"]=intent

    signals=understanding.get(
        "signals",
        []
    )

    if signals:
        profile["recent_signals"]=signals[-10:]

    destination=understanding.get(
        "destination"
    )

    if destination:
        profile["last_destination"]=destination

    companion=understanding.get(
        "companion"
    )

    if companion:
        profile["last_companion"]=companion

    budget=understanding.get(
        "budget"
    )

    if budget is not None:
        profile["last_budget"]=budget

    category=proposal.get(
        "category"
    )

    if category:
        profile["last_category"]=category

    return memory

def process(
    message,
    memory=None
):
    message=safe_text(
        message
    )

    memory=normalize_memory(
        memory
    )

    understanding=understand(
        message
    )

    personalization=personalize_local(
        understanding,
        memory
    )

    decision=decide(
        understanding,
        personalization
    )

    prompt=build_ai_prompt(
        message,
        understanding,
        personalization,
        decision
    )

    ai_result=None

    try:
        ai_result=call_openai(
            prompt
        )
    except Exception:
        ai_result=None

    if ai_result is None:
        try:
            ai_result=call_gemini(
                prompt
            )
        except Exception:
            ai_result=None

    proposal=sanitize_ai(
        ai_result,
        understanding,
        personalization,
        decision
    )

    record=make_experience_record(
        message,
        understanding,
        decision,
        proposal
    )

    memory=remember_today(
        memory,
        record
    )

    memory=update_learning(
        memory,
        understanding,
        proposal
    )

    return {
        "message":message,
        "understanding":understanding,
        "personalization":personalization,
        "decision":decision,
        "proposal":proposal,
        "memory":memory,
        "today":{
            "date":today_key(),
            "count":len(
                today_history(memory)
            ),
            "used":used_today(
                memory
            )
        }
    }

def response_text(result):
    if not isinstance(
        result,
        dict
    ):
        return (
            "I'm here. "
            "Tell me what you need."
        )

    proposal=result.get(
        "proposal",
        {}
    )

    breathing=proposal.get(
        "breathing"
    )

    if (
        isinstance(breathing,dict)
        and breathing.get("enabled")
    ):
        direction=safe_text(
            proposal.get(
                "direction"
            ),
            "Let's create a little space."
        )

        instruction=safe_text(
            breathing.get(
                "instruction"
            ),
            "Follow the circle and let the rhythm become natural."
        )

        return (
            f"{direction} "
            f"{instruction}"
        )

    return safe_text(
        proposal.get(
            "direction"
        ),
        "Tell me what you need, in your own words."
    )

def engine_status():
    return {
        "status":"ready",
        "ai_primary":(
            "openai"
            if OPENAI_API_KEY
            else "local"
        ),
        "ai_fallback":(
            "gemini"
            if GEMINI_API_KEY
            else "local"
        ),
        "ai_invisible":True,
        "today_first":True,
        "anti_repetition":True,
        "breathing_library":len(
            BREATHING_EXERCISES
        ),
        "breathing_patterns":len(
            BREATHING_PATTERNS
        ),
        "breathing_needs":len(
            BREATHING_NEEDS
        ),
        "memory_mode":"client_memory_supported",
        "payments":False,
        "free":True
    }

def feedback(
    memory,
    experience_id,
    value,
    message=""
):
    memory=normalize_memory(
        memory
    )

    item={
        "timestamp":now_utc().isoformat(),
        "experience_id":safe_text(
            experience_id
        ),
        "value":safe_text(
            value
        ),
        "message":safe_text(
            message
        )
    }

    memory["feedback"].append(
        item
    )

    memory["feedback"]=memory[
        "feedback"
    ][-50:]

    return memory

def revise(
    memory,
    experience_id,
    instruction
):
    memory=normalize_memory(
        memory
    )

    return {
        "memory":memory,
        "revision":{
            "experience_id":safe_text(
                experience_id
            ),
            "instruction":safe_text(
                instruction
            ),
            "status":"ready"
        }
    }

def understand_message(message):
    return understand(
        message
    )

def personalize(
    understanding,
    memory
):
    return personalize_local(
        understanding,
        normalize_memory(
            memory
        )
    )

def propose(
    understanding,
    personalization,
    decision
):
    return local_proposal(
        understanding,
        personalization,
        decision
    )
