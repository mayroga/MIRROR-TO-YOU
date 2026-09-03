import os
import re
import json
import uuid
import urllib.request
import urllib.error
from datetime import datetime, timezone

OPENAI_API_KEY=os.getenv("OPENAI_API_KEY","").strip()
GEMINI_API_KEY=os.getenv("GEMINI_API_KEY","").strip()
OPENAI_MODEL=os.getenv("OPENAI_MODEL","gpt-5-mini").strip()
GEMINI_MODEL=os.getenv("GEMINI_MODEL","gemini-2.5-flash").strip()

try:
AI_TIMEOUT=float(os.getenv("MIRROR_AI_TIMEOUT","35"))
except:
AI_TIMEOUT=35.0

MAX_HISTORY=100
MAX_DAILY_HISTORY=120
MAX_TEXT=6000

BREATHING_PATTERNS=[
{"id":"breath_01","pattern":"4-4","inhale":4,"hold":0,"exhale":4,"pause":0,"style":"steady"},
{"id":"breath_02","pattern":"4-6","inhale":4,"hold":0,"exhale":6,"pause":0,"style":"calming"},
{"id":"breath_03","pattern":"3-5","inhale":3,"hold":0,"exhale":5,"pause":0,"style":"gentle"},
{"id":"breath_04","pattern":"4-2-6","inhale":4,"hold":2,"exhale":6,"pause":0,"style":"slow"},
{"id":"breath_05","pattern":"4-4-6","inhale":4,"hold":4,"exhale":6,"pause":0,"style":"grounding"},
{"id":"breath_06","pattern":"5-5","inhale":5,"hold":0,"exhale":5,"pause":0,"style":"balanced"},
{"id":"breath_07","pattern":"3-3-6","inhale":3,"hold":3,"exhale":6,"pause":0,"style":"release"},
{"id":"breath_08","pattern":"4-7","inhale":4,"hold":0,"exhale":7,"pause":0,"style":"quiet"},
{"id":"breath_09","pattern":"5-7","inhale":5,"hold":0,"exhale":7,"pause":0,"style":"deep"},
{"id":"breath_10","pattern":"4-1-5","inhale":4,"hold":1,"exhale":5,"pause":0,"style":"reset"}
]

BREATHING_NEEDS=[
"calm","slow_down","release_tension","regain_focus","prepare_for_sleep",
"wake_gently","recover_energy","create_space","ground_attention",
"prepare_for_travel","wait_patiently","transition","clear_mind",
"change_mood","feel_present","reduce_overwhelm","pause","reset",
"quiet_moment","restore_balance","recover_after_stress","prepare_for_meeting",
"prepare_for_social_moment","prepare_for_rest","recover_from_rush",
"reconnect_with_self","create_confidence","soften_the_day","start_again",
"finish_the_day","enjoy_the_moment","settle_before_decision",
"recover_after_disappointment","prepare_for_change","reduce_restlessness",
"create_focus","slow_thoughts","feel_centered","find_rhythm",
"private_pause","personal_reset","emotional_space","gentle_recovery",
"mental_refresh","body_awareness","attention_shift","comfort",
"anticipation","uncertainty","frustration","impatience","loneliness",
"social_fatigue","travel_fatigue","jet_lag_adjustment","busy_day",
"quiet_start","quiet_finish","creative_space","decision_space",
"confidence_before_action","recovery_between_tasks","recovery_between_places",
"return_to_present","enjoyment","gratitude","curiosity","motivation",
"patience","clarity","composure","lightness","relaxation",
"reconnection","self_attention","personal_time","digital_pause",
"sensory_reset","mental_distance","fresh_start","slow_evening",
"gentle_morning","private_reflection","anticipatory_calm","focus_transition",
"rest_transition","travel_transition","social_transition","work_free_reset",
"personal_ritual","micro_pause","longer_pause","moment_of_choice",
"moment_of_uncertainty","moment_of_change","moment_of_recovery",
"moment_of_presence","moment_of_discovery","moment_of_rest"
]

SYSTEM_MEMORY_RULES={
"daily_priority":True,
"today_first":True,
"avoid_same_day_repetition":True,
"adapt_when_similar":True,
"respect_explicit_request":True,
"learn_from_feedback":True,
"never_claim_unconfirmed_execution":True,
"ai_invisible_to_client":True,
"use_memory_before_decision":True,
"breathing_available_when_context_supports_it":True
}

def now():
return datetime.now(timezone.utc).isoformat()

def today_key():
return datetime.now(timezone.utc).strftime("%Y-%m-%d")

def clean(value,max_len=MAX_TEXT):
if value is None:
return ""
if not isinstance(value,str):
value=str(value)
return " ".join(value.strip().split())[:max_len]

def language_of(text):
text=clean(text).lower()
spanish=[
" que "," necesito "," quiero "," estoy "," para "," con "," una ",
" por "," hoy "," donde "," dónde "," ayuda "," necesito"
]
score=sum(1 for x in spanish if x in f" {text} ")
return "es" if score>=2 else "en"

def normalize_memory(memory):
m=memory if isinstance(memory,dict) else {}
core=m.get("core",{})
moment=m.get("moment",{})
preferences=m.get("preferences",{})
dislikes=m.get("dislikes",[])
history=m.get("history",[])
learning=m.get("learning",{})
daily=m.get("daily",{})

```
if not isinstance(core,dict):
    core={}
if not isinstance(moment,dict):
    moment={}
if not isinstance(preferences,dict):
    preferences={}
if not isinstance(dislikes,list):
    dislikes=[]
if not isinstance(history,list):
    history=[]
if not isinstance(learning,dict):
    learning={}
if not isinstance(daily,dict):
    daily={}

daily_today=daily.get(today_key(),[])
if not isinstance(daily_today,list):
    daily_today=[]

return{
    "core":core,
    "moment":moment,
    "preferences":preferences,
    "dislikes":dislikes[-100:],
    "history":history[-MAX_HISTORY:],
    "learning":learning,
    "daily":{today_key():daily_today[-MAX_DAILY_HISTORY:]},
    "system":SYSTEM_MEMORY_RULES
}
```

def remember_today(memory,entry):
m=normalize_memory(memory)
key=today_key()
daily=m["daily"].setdefault(key,[])
daily.append(entry)
m["daily"][key]=daily[-MAX_DAILY_HISTORY:]
m["history"]=(m.get("history",[])+[entry])[-MAX_HISTORY:]
return m

def today_history(memory):
m=normalize_memory(memory)
return m.get("daily",{}).get(today_key(),[])

def recent_experiences(memory,limit=30):
history=today_history(memory)
return history[-limit:]

def used_today(memory,field):
values=[]
for item in today_history(memory):
value=item.get(field)
if value:
values.append(str(value).lower())
return values

def detect_signals(text):
t=clean(text).lower()
groups={
"calm":["stress","stressed","tense","tension","anxious","overwhelmed","overloaded","nervous","agitated","calma","estrés","estresado","tenso","tensión","ansioso","abrumado","nervioso"],
"fatigue":["tired","exhausted","drained","fatigue","sleepy","cansado","agotado","fatiga","sueño"],
"focus":["focus","concentrate","concentration","clarity","focus","concentración","concentrarme","claridad"],
"rest":["rest","relax","quiet","peace","sleep","descansar","relajar","tranquilo","paz","dormir"],
"energy":["energy","energize","awake","motivation","energía","despertar","motivado"],
"travel":["travel","trip","flight","hotel","destination","viaje","vuelo","hotel","destino"],
"privacy":["private","discreet","quiet","alone","privado","discreto","tranquilo","solo"],
"surprise":["surprise","unexpected","different","sorpréndeme","sorpresa","diferente"],
"decision":["decide","decision","choose","choice","decidir","decisión","elegir"],
"social":["family","friend","partner","friends","familia","amigo","pareja","amigos"],
"rush":["quick","quickly","busy","hurry","fast","rápido","apurado","prisa"],
"sadness":["sad","down","low","lonely","triste","solo","bajoneado","decaído"],
"joy":["happy","excited","celebrate","fun","feliz","emocionado","celebrar","diversión"]
}
found=[]
for key,words in groups.items():
if any(word in t for word in words):
found.append(key)
return found[:10]

def detect_duration(text):
t=clean(text).lower()
patterns=[
(r"(\d+)\s*(?:min|mins|minute|minutes|minuto|minutos)",1),
(r"(\d+)\s*(?:h|hr|hour|hours|hora|horas)",60)
]
for pattern,mult in patterns:
match=re.search(pattern,t)
if match:
try:
return int(match.group(1))*mult
except:
pass
return None

def detect_companion(text):
t=clean(text).lower()
mapping=[
(["alone","myself","solo","sola"],"alone"),
(["partner","spouse","wife","husband","pareja","esposa","esposo"],"partner"),
(["family","familia"],"family"),
(["friend","friends","amigo","amiga","amigos"],"friends"),
(["children","kids","hijos","niños"],"family")
]
for words,value in mapping:
if any(x in t for x in words):
return value
return None

def detect_budget(text):
match=re.search(r"(?:$|usd\s*)?(\d{2,6}(?:[.,]\d{1,2})?)\s*(?:usd|dollars|dólares)?",clean(text).lower())
if not match:
return None
try:
return float(match.group(1).replace(",",""))
except:
return None

def detect_destination(text):
t=clean(text)
patterns=[
r"(?:to|in|at|for|hacia|en|para)\s+([A-Z][A-Za-zÀ-ÿ]*(?:\s+[A-Z][A-Za-zÀ-ÿ]*){0,3})",
r"(?:miami|new york|orlando|los angeles|paris|london|madrid|mexico|cuba|guatemala)"
]
for pattern in patterns:
match=re.search(pattern,t,re.I)
if match:
if match.lastindex:
value=clean(match.group(1))
else:
value=clean(match.group(0))
if len(value)>2:
return value
return None

def infer_intent(text,signals):
t=clean(text).lower()
if any(x in t for x in ["music","playlist","song","música","canción"]):
return "mood"
if any(x in t for x in ["breathe","breathing","breath","respira","respiración","respirar"]):
return "breathing"
if any(x in t for x in ["hotel","flight","trip","travel","destination","hotel","vuelo","viaje","destino"]):
return "travel"
if any(x in t for x in ["restaurant","dinner","lunch","eat","food","restaurante","cena","almuerzo","comer","comida"]):
return "dining"
if any(x in t for x in ["surprise","something special","sorprende","algo especial"]):
return "discovery"
if any(x in t for x in ["what should i","where should i","help me choose","qué hago","qué debería","ayúdame a elegir"]):
return "decision"
if "calm" in signals or "rest" in signals or "sadness" in signals or "rush" in signals:
return "wellbeing_moment"
return "concierge"

def understand_local(text,memory):
signals=detect_signals(text)
return{
"language":language_of(text),
"intent":infer_intent(text,signals),
"signals":signals,
"duration":detect_duration(text),
"companion":detect_companion(text),
"budget":detect_budget(text),
"destination":detect_destination(text),
"today_count":len(today_history(memory))
}

def personalize_local(understanding,memory):
m=normalize_memory(memory)
preferences=m.get("preferences",{})
core=m.get("core",{})
dislikes=m.get("dislikes",[])
today=today_history(m)

```
return{
    "known_preferences":preferences,
    "core":core,
    "dislikes":dislikes[-20:],
    "today_experiences":today[-30:],
    "today_count":len(today),
    "avoid_today":{
        "exercise_ids":used_today(m,"exercise_id"),
        "patterns":used_today(m,"pattern"),
        "actions":used_today(m,"action"),
        "phrases":used_today(m,"phrase"),
        "titles":used_today(m,"title"),
        "experience_ids":used_today(m,"experience_id")
    }
}
```

def local_decision(understanding,personalization):
signals=understanding.get("signals",[])
intent=understanding.get("intent","concierge")

```
breathing_needed=(
    intent=="breathing" or
    intent=="wellbeing_moment" or
    any(x in signals for x in ["calm","fatigue","focus","rest","rush","sadness","energy"])
)

return{
    "intent":intent,
    "priority":"high" if any(x in signals for x in ["calm","rush","decision"]) else "normal",
    "breathing_recommended":breathing_needed,
    "needs_more_information":False,
    "human_coordination":intent in ["travel","dining","concierge"],
    "reason":"Current need and today's experience history should guide the next action."
}
```

def select_breathing_local(understanding,personalization):
used_patterns=set(personalization.get("avoid_today",{}).get("patterns",[]))
used_ids=set(personalization.get("avoid_today",{}).get("exercise_ids",[]))

```
signals=understanding.get("signals",[])
need="calm"

if "focus" in signals:
    need="regain_focus"
elif "fatigue" in signals:
    need="recover_energy"
elif "rest" in signals:
    need="prepare_for_sleep"
elif "rush" in signals:
    need="slow_down"
elif "sadness" in signals:
    need="create_space"
elif "energy" in signals:
    need="wake_gently"

candidates=[
    x for x in BREATHING_PATTERNS
    if x["id"] not in used_ids and x["pattern"].lower() not in used_patterns
]

if not candidates:
    candidates=BREATHING_PATTERNS[:]

index=len(today_history(personalization.get("_memory",{})))%len(candidates) if candidates else 0
selected=candidates[index]

return{
    "enabled":True,
    "exercise_id":selected["id"],
    "need":need,
    "pattern":selected["pattern"],
    "inhale":selected["inhale"],
    "hold":selected["hold"],
    "exhale":selected["exhale"],
    "pause":selected["pause"],
    "style":selected["style"],
    "duration_minutes":understanding.get("duration") or 3,
    "circle":True
}
```

def local_proposal(understanding,personalization,decision):
breathing=None
if decision.get("breathing_recommended"):
breathing=select_breathing_local(
understanding,
{**personalization,"_memory":{}}
)

```
destination=understanding.get("destination")
intent=understanding.get("intent","concierge")

titles={
    "breathing":"A moment made for you",
    "wellbeing_moment":"A moment made for you",
    "travel":"A direction worth exploring",
    "dining":"Something worth discovering",
    "mood":"The right atmosphere",
    "discovery":"Something different",
    "decision":"A clearer next step",
    "concierge":"Let MIRROR take the next step"
}

return{
    "title":titles.get(intent,titles["concierge"]),
    "direction":"I’m shaping this around what you need right now.",
    "category":intent,
    "privacy":"private",
    "priority":decision.get("priority","normal"),
    "budget":understanding.get("budget"),
    "destination":destination,
    "duration":understanding.get("duration"),
    "companion":understanding.get("companion"),
    "signals":understanding.get("signals",[]),
    "confidence":0.55,
    "status":"proposed",
    "questions":[],
    "steps":[],
    "breathing":breathing
}
```

def build_prompt(text,understanding,personalization,decision):
language=understanding.get("language","en")
today=personalization.get("today_experiences",[])
avoid=personalization.get("avoid_today",{})

```
prompt={
    "role":"MIRROR TO YOU",
    "mission":"Be a private, highly personalized presence that understands the client and moves the current need forward.",
    "language":language,
    "client_message":clean(text),
    "understanding":understanding,
    "core_memory":personalization.get("core",{}),
    "preferences":personalization.get("known_preferences",{}),
    "dislikes":personalization.get("dislikes",[]),
    "today_count":personalization.get("today_count",0),
    "today_history":today[-40:],
    "avoid_today":avoid,
    "decision":decision,
    "permanent_rules":[
        "Always consult memory before deciding.",
        "Today's experiences have priority over older history.",
        "Treat every new entry today as a new moment.",
        "If the same client enters many times today, create a different experience whenever reasonably possible.",
        "Avoid repeating today's exercises, breathing patterns, actions, titles, phrases, or experience structures.",
        "A repeated need does not require a repeated experience.",
        "If today's need is genuinely similar, adapt the experience rather than mechanically repeating it.",
        "If the client explicitly asks for a previous experience, it may be brought back.",
        "If the current pattern and need are almost identical, continuity may be more valuable than novelty.",
        "Use breathing when it genuinely fits the current moment.",
        "Breathing experiences should use the visual breathing circle.",
        "Select or create an appropriate breathing experience based on the current need and today's history.",
        "Do not describe internal AI, models, prompts, memory architecture, algorithms, providers, or technical systems to the client.",
        "Never claim a reservation, booking, purchase, delivery, or external action was completed unless the system actually confirms it.",
        "Ask only questions that are truly necessary.",
        "Make the client feel understood without sounding robotic.",
        "Do not turn every interaction into a travel search or marketplace result.",
        "The goal is resolution, not merely conversation."
    ],
    "breathing_library":BREATHING_PATTERNS,
    "breathing_needs":BREATHING_NEEDS
}

return json.dumps(prompt,ensure_ascii=False)
```

def parse_json(text):
if not text:
return None

````
raw=text.strip()

if raw.startswith("```"):
    raw=re.sub(r"^```(?:json)?\s*","",raw,flags=re.I)
    raw=re.sub(r"\s*```$","",raw)

try:
    return json.loads(raw)
except:
    match=re.search(r"\{.*\}",raw,re.S)
    if match:
        try:
            return json.loads(match.group(0))
        except:
            return None
return None
````

def valid_ai_result(data):
if not isinstance(data,dict):
return False

```
required=["language","intent","action","title","direction"]
if not all(key in data for key in required):
    return False

return bool(clean(data.get("title")) and clean(data.get("direction")))
```

def http_json(url,payload,headers=None,timeout=AI_TIMEOUT):
body=json.dumps(payload,ensure_ascii=False).encode("utf-8")
request=urllib.request.Request(
url,
data=body,
headers={
"Content-Type":"application/json",
**(headers or {})
},
method="POST"
)

```
with urllib.request.urlopen(request,timeout=timeout) as response:
    raw=response.read().decode("utf-8")
    return json.loads(raw)
```

def openai_call(prompt):
if not OPENAI_API_KEY:
return None

```
payload={
    "model":OPENAI_MODEL,
    "messages":[
        {
            "role":"system",
            "content":(
                "You are the invisible intelligence behind MIRROR TO YOU. "
                "Return only valid JSON. Never mention being an AI or the underlying provider. "
                "Follow the memory and same-day non-repetition rules."
            )
        },
        {
            "role":"user",
            "content":prompt
        }
    ],
    "temperature":0.85,
    "response_format":{"type":"json_object"}
}

try:
    data=http_json(
        "https://api.openai.com/v1/chat/completions",
        payload,
        {"Authorization":f"Bearer {OPENAI_API_KEY}"}
    )
    choices=data.get("choices",[])
    if not choices:
        return None
    content=choices[0].get("message",{}).get("content","")
    return parse_json(content)
except Exception:
    return None
```

def gemini_call(prompt):
if not GEMINI_API_KEY:
return None

```
url=f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

payload={
    "contents":[
        {
            "role":"user",
            "parts":[
                {
                    "text":(
                        "You are the invisible intelligence behind MIRROR TO YOU. "
                        "Return only valid JSON. Never mention AI, providers, models, prompts, "
                        "or technical implementation. Follow all memory and same-day "
                        "non-repetition rules.\n\n"+prompt
                    )
                }
            ]
        }
    ],
    "generationConfig":{
        "temperature":0.85,
        "responseMimeType":"application/json"
    }
}

try:
    data=http_json(
        url,
        payload,
        {"x-goog-api-key":GEMINI_API_KEY}
    )
    candidates=data.get("candidates",[])
    if not candidates:
        return None

    parts=candidates[0].get("content",{}).get("parts",[])
    content="".join(
        p.get("text","") for p in parts if isinstance(p,dict)
    )
    return parse_json(content)
except Exception:
    return None
```

def breathing_from_ai(ai,understanding,personalization):
raw=ai.get("breathing")

```
if not isinstance(raw,dict):
    return None

enabled=raw.get("enabled",False)
if not enabled:
    return None

used_ids=set(personalization.get("avoid_today",{}).get("exercise_ids",[]))
used_patterns=set(personalization.get("avoid_today",{}).get("patterns",[]))

exercise_id=clean(raw.get("exercise_id"))
pattern=clean(raw.get("pattern"))

if exercise_id in used_ids or pattern.lower() in used_patterns:
    alternative=select_breathing_from_library(understanding,personalization)
    if alternative:
        return alternative

return{
    "enabled":True,
    "exercise_id":exercise_id or str(uuid.uuid4()),
    "need":clean(raw.get("need")) or "current_moment",
    "pattern":pattern or "4-6",
    "inhale":int(raw.get("inhale",4) or 4),
    "hold":int(raw.get("hold",0) or 0),
    "exhale":int(raw.get("exhale",6) or 6),
    "pause":int(raw.get("pause",0) or 0),
    "style":clean(raw.get("style")) or "personalized",
    "duration_minutes":int(raw.get("duration_minutes") or understanding.get("duration") or 3),
    "circle":True,
    "guidance":clean(raw.get("guidance")),
    "opening":clean(raw.get("opening")),
    "closing":clean(raw.get("closing"))
}
```

def select_breathing_from_library(understanding,personalization):
used_ids=set(personalization.get("avoid_today",{}).get("exercise_ids",[]))
used_patterns=set(personalization.get("avoid_today",{}).get("patterns",[]))

```
available=[
    item for item in BREATHING_PATTERNS
    if item["id"] not in used_ids and item["pattern"].lower() not in used_patterns
]

if not available:
    available=BREATHING_PATTERNS[:]

signals=understanding.get("signals",[])

if "focus" in signals:
    order=["steady","balanced","grounding"]
elif "fatigue" in signals:
    order=["gentle","balanced","quiet"]
elif "rest" in signals:
    order=["quiet","calming","slow"]
elif "rush" in signals:
    order=["calming","slow","release"]
else:
    order=["calming","gentle","balanced","grounding"]

selected=None

for style in order:
    selected=next((x for x in available if x["style"]==style),None)
    if selected:
        break

if not selected:
    selected=available[0]

return{
    "enabled":True,
    "exercise_id":selected["id"],
    "need":signals[0] if signals else "current_moment",
    "pattern":selected["pattern"],
    "inhale":selected["inhale"],
    "hold":selected["hold"],
    "exhale":selected["exhale"],
    "pause":selected["pause"],
    "style":selected["style"],
    "duration_minutes":understanding.get("duration") or 3,
    "circle":True
}
```

def sanitize_ai(ai,understanding,personalization,decision):
ai=ai if isinstance(ai,dict) else {}

```
breathing=breathing_from_ai(ai,understanding,personalization)

if not breathing and decision.get("breathing_recommended"):
    breathing=select_breathing_from_library(understanding,personalization)

questions=ai.get("questions",[])
if not isinstance(questions,list):
    questions=[]

steps=ai.get("steps",[])
if not isinstance(steps,list):
    steps=[]

return{
    "language":clean(ai.get("language")) or understanding.get("language","en"),
    "intent":clean(ai.get("intent")) or understanding.get("intent","concierge"),
    "privacy":clean(ai.get("privacy")) or "private",
    "priority":clean(ai.get("priority")) or decision.get("priority","normal"),
    "companion":clean(ai.get("companion")) or understanding.get("companion"),
    "duration":ai.get("duration") or understanding.get("duration"),
    "budget":ai.get("budget") or understanding.get("budget"),
    "destination":clean(ai.get("destination")) or understanding.get("destination"),
    "signals":ai.get("signals") if isinstance(ai.get("signals"),list) else understanding.get("signals",[]),
    "action":clean(ai.get("action")) or "personalized_next_step",
    "confidence":float(ai.get("confidence",0.7) or 0.7),
    "title":clean(ai.get("title")) or "A moment made for you",
    "direction":clean(ai.get("direction")) or "I’m shaping this around what you need right now.",
    "questions":[clean(x) for x in questions if clean(x)][:4],
    "steps":[clean(x) for x in steps if clean(x)][:6],
    "next_move":clean(ai.get("next_move")),
    "breathing":breathing
}
```

def build_experience_record(text,understanding,proposal,response):
breathing=proposal.get("breathing") if isinstance(proposal,dict) else None

```
record={
    "id":str(uuid.uuid4()),
    "timestamp":now(),
    "date":today_key(),
    "message":clean(text,1200),
    "intent":understanding.get("intent"),
    "signals":understanding.get("signals",[]),
    "action":clean(proposal.get("action") or proposal.get("title")),
    "title":clean(proposal.get("title")),
    "phrase":clean(response,500),
    "destination":clean(understanding.get("destination")),
    "exercise_id":clean(breathing.get("exercise_id")) if breathing else "",
    "pattern":clean(breathing.get("pattern")) if breathing else "",
    "need":clean(breathing.get("need")) if breathing else "",
    "experience_id":clean(proposal.get("experience_id")),
    "result":"presented"
}

return record
```

def process(text,memory=None):
text=clean(text)
m=normalize_memory(memory)

```
if not text:
    understanding={
        "language":"en",
        "intent":"concierge",
        "signals":[],
        "duration":None,
        "companion":None,
        "budget":None,
        "destination":None,
        "today_count":len(today_history(m))
    }
else:
    understanding=understand_local(text,m)

personalization=personalize_local(understanding,m)
decision=local_decision(understanding,personalization)

prompt=build_prompt(
    text,
    understanding,
    personalization,
    decision
)

ai=openai_call(prompt)

if not valid_ai_result(ai):
    ai=gemini_call(prompt)

if valid_ai_result(ai):
    sanitized=sanitize_ai(
        ai,
        understanding,
        personalization,
        decision
    )

    proposal={
        "title":sanitized["title"],
        "direction":sanitized["direction"],
        "category":sanitized["intent"],
        "privacy":sanitized["privacy"],
        "priority":sanitized["priority"],
        "budget":sanitized["budget"],
        "destination":sanitized["destination"],
        "duration":sanitized["duration"],
        "companion":sanitized["companion"],
        "signals":sanitized["signals"],
        "confidence":sanitized["confidence"],
        "status":"proposed",
        "questions":sanitized["questions"],
        "steps":sanitized["steps"],
        "action":sanitized["action"],
        "next_move":sanitized["next_move"],
        "breathing":sanitized["breathing"],
        "experience_id":str(uuid.uuid4())
    }

    result={
        "understanding":understanding,
        "personalization":personalization,
        "decision":decision,
        "proposal":proposal,
        "ai_used":True
    }

else:
    proposal=local_proposal(
        understanding,
        personalization,
        decision
    )
    proposal["experience_id"]=str(uuid.uuid4())

    result={
        "understanding":understanding,
        "personalization":personalization,
        "decision":decision,
        "proposal":proposal,
        "ai_used":False
    }

response=response_text(result,m)
record=build_experience_record(
    text,
    understanding,
    proposal,
    response
)

result["memory"]=remember_today(m,record)
result["today"]=result["memory"].get("daily",{}).get(today_key(),[])
result["record"]=record

return result
```

def response_text(result,memory=None):
understanding=result.get("understanding",{})
proposal=result.get("proposal",{})
language=understanding.get("language","en")
questions=proposal.get("questions",[])
breathing=proposal.get("breathing")

```
if questions:
    return questions[0]

if breathing and breathing.get("enabled"):
    opening=clean(breathing.get("opening"))

    if opening:
        return opening

    if language=="es":
        return "Quédate aquí un momento. MIRROR ha elegido una respiración diferente para este momento. Sigue el círculo y deja que el ritmo haga el resto."

    return "Stay here for a moment. MIRROR has chosen a different breathing experience for this moment. Follow the circle and let the rhythm do the rest."

direction=clean(proposal.get("direction"))

if direction:
    return direction

if language=="es":
    return "Estoy aquí. Vamos a ocuparnos de lo que necesitas ahora."

return "I’m here. Let’s take care of what you need right now."
```

def engine_status():
return{
"ready":True,
"openai_configured":bool(OPENAI_API_KEY),
"gemini_configured":bool(GEMINI_API_KEY),
"primary":"openai",
"fallback":"gemini",
"local_fallback":True,
"today_first_memory":True,
"same_day_non_repetition":True,
"breathing_library":len(BREATHING_PATTERNS),
"breathing_needs":len(BREATHING_NEEDS)
}

def understand(text,memory=None):
m=normalize_memory(memory)
understanding=understand_local(text,m)
personalization=personalize_local(understanding,m)
return{
"understanding":understanding,
"personalization":personalization
}

def personalize(text,memory=None):
m=normalize_memory(memory)
understanding=understand_local(text,m)
return personalize_local(understanding,m)

def decide(text,memory=None):
m=normalize_memory(memory)
understanding=understand_local(text,m)
personalization=personalize_local(understanding,m)
return local_decision(understanding,personalization)

def propose(text,memory=None):
m=normalize_memory(memory)
understanding=understand_local(text,m)
personalization=personalize_local(understanding,m)
decision=local_decision(understanding,personalization)
return local_proposal(understanding,personalization,decision)
