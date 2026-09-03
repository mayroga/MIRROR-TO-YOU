import os,json,re,urllib.request
from datetime import datetime

AI_KEY=os.getenv("OPENAI_API_KEY","").strip()
AI_MODEL=os.getenv("OPENAI_MODEL","gpt-5-mini").strip()
AI_URL="https://api.openai.com/v1/chat/completions"

INTENTS=("TRAVEL","ESCAPE","STAY","DINING","EXPERIENCE","MUSIC","MAPS","WELLBEING","CONCIERGE","COMPANION")
SIGNALS=("QUIET","PRIVACY","LUXURY","LOW_CROWD","RELAXATION","DINING","NATURE","MUSIC","SURPRISE","SIMPLICITY")

def now():
    return datetime.now().isoformat(timespec="seconds")

def clean(v):
    if v is None:return ""
    return str(v).strip()

def language_of(text):
    t=clean(text).lower()
    es=sum(x in t for x in (" que "," para "," necesito "," quiero "," necesito","donde ","cómo ","como "))
    return "es" if es>=1 else "en"

def detect_intent(text):
    t=clean(text).lower()
    rules={
        "TRAVEL":("viaje","viajar","flight","vuelo","airport","aeropuerto","trip","vacation","vacaciones"),
        "ESCAPE":("escapar","escape","desconectar","disconnect","get away","alejarme","salir"),
        "STAY":("hotel","resort","suite","villa","alojamiento","quedarme","stay"),
        "DINING":("restaurant","restaurante","cena","comer","almuerzo","lunch","dinner","chef","food"),
        "EXPERIENCE":("experiencia","experience","tour","actividad","activity","spa","yacht","arte","art"),
        "MUSIC":("música","musica","music","canción","cancion","playlist","youtube"),
        "MAPS":("mapa","maps","ubicación","ubicacion","dirección","direccion","where is","location"),
        "WELLBEING":("respirar","respiración","respiracion","calma","calmarme","relajar","relax","ansiedad","stress","estres","paz"),
        "COMPANION":("con mi esposa","con mi esposo","con mi pareja","with my wife","with my husband","with my partner","con amigos","with friends")
    }
    for intent,words in rules.items():
        if any(w in t for w in words):return intent
    return "CONCIERGE"

def detect_privacy(text):
    t=clean(text).lower()
    if any(x in t for x in ("privado","privacidad","discreto","discreta","private","privacy","discreet","confidential")):return "HIGH"
    if any(x in t for x in ("exclusivo","exclusive","vip","luxury","lujo")):return "HIGH"
    return "STANDARD"

def detect_priority(text):
    t=clean(text).lower()
    if any(x in t for x in ("urgente","ahora","inmediatamente","urgent","now","asap")):return "URGENT"
    if any(x in t for x in ("importante","important","pronto","soon")):return "HIGH"
    return "NORMAL"

def detect_companion(text):
    t=clean(text).lower()
    if any(x in t for x in ("solo","sola","alone","myself")):return "ALONE"
    if any(x in t for x in ("familia","family","children","niños","ninos")):return "FAMILY"
    if any(x in t for x in ("amigo","amiga","friends")):return "FRIENDS"
    if any(x in t for x in ("pareja","esposa","esposo","partner","wife","husband")):return "PARTNER"
    return ""

def detect_duration(text):
    m=re.search(r"\b(\d+)\s*(minutos?|mins?|minutes?|horas?|hours?|d[ií]as?|days?|semanas?|weeks?)\b",clean(text).lower())
    return m.group(0) if m else ""

def detect_budget(text):
    m=re.search(r"(?:\$|usd\s*)\s?(\d+(?:[.,]\d+)?)",clean(text).lower())
    if not m:
        m=re.search(r"\b(\d+(?:[.,]\d+)?)\s*(?:dollars|usd)\b",clean(text).lower())
    return m.group(0) if m else ""

def detect_destination(text):
    t=clean(text)
    patterns=[
        r"(?:en|in|at|near|cerca de|desde|from|to|hacia)\s+([A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ' -]{2,40})",
        r"(?:Miami|Orlando|New York|New York City|Los Angeles|Las Vegas|Paris|London|Madrid|Barcelona)"
    ]
    for p in patterns:
        m=re.search(p,t,re.I)
        if m:return clean(m.group(1) if m.lastindex else m.group(0))
    return ""

def detect_signals(text):
    t=clean(text).lower()
    words={
        "QUIET":("silencio","tranquilo","quiet","peaceful","calm"),
        "PRIVACY":("privado","privacidad","discreto","private","privacy","discreet"),
        "LUXURY":("lujo","lujoso","luxury","exclusive","exclusivo","vip"),
        "LOW_CROWD":("sin gente","poca gente","less crowded","uncrowded","avoid crowds"),
        "RELAXATION":("relajar","relax","descansar","rest","calma","calm"),
        "DINING":("comida","comer","restaurant","restaurante","dinner","cena"),
        "NATURE":("naturaleza","nature","playa","beach","montaña","mountain","outdoors"),
        "MUSIC":("música","musica","music"),
        "SURPRISE":("sorpréndeme","sorprendeme","surprise me","sorpresa"),
        "SIMPLICITY":("simple","sencillo","sin complicaciones","easy","simple")
    }
    return [k for k,v in words.items() if any(x in t for x in v)]

def understand(text,memory):
    return {
        "intent":detect_intent(text),
        "privacy":detect_privacy(text),
        "priority":detect_priority(text),
        "companion":detect_companion(text),
        "duration":detect_duration(text),
        "budget":detect_budget(text),
        "destination":detect_destination(text),
        "signals":detect_signals(text),
        "language":language_of(text)
    }

def personalize(u,memory):
    memory=memory or {}
    core=memory.get("core") or {}
    moment=memory.get("moment") or {}
    prefs=memory.get("preferences") or {}
    dislikes=memory.get("dislikes") or []
    history=memory.get("history") or []
    learning=memory.get("learning") or {}

    result={
        "known_preferences":prefs,
        "core":core,
        "current_moment":moment,
        "dislikes":dislikes,
        "recent_history":history[-5:],
        "learning":learning,
        "signals":u.get("signals",[])
    }

    if core.get("name"):result["name"]=core["name"]
    return result

def missing_information(u):
    intent=u.get("intent")
    missing=[]

    if intent in ("TRAVEL","STAY","DINING","EXPERIENCE") and not u.get("destination"):
        missing.append("destination")

    if intent=="STAY" and not u.get("duration"):
        missing.append("duration")

    return missing

def decision_for(u,p):
    missing=missing_information(u)
    priority=u.get("priority","NORMAL")
    privacy=u.get("privacy","STANDARD")

    if missing:
        action="ASK"
        reason="More information is needed before making a meaningful proposal."
    elif privacy=="HIGH" or priority=="URGENT":
        action="CONCIERGE"
        reason="The request benefits from careful coordination."
    else:
        action="PROPOSE"
        reason="There is enough context to prepare a personalized direction."

    return {
        "action":action,
        "reason":reason,
        "missing":missing,
        "confidence":0.86 if not missing else 0.58
    }

def title_for(u):
    names={
        "TRAVEL":"Your Next Journey",
        "ESCAPE":"A Moment Away",
        "STAY":"Your Private Stay",
        "DINING":"A Table Worth Your Time",
        "EXPERIENCE":"Something Worth Experiencing",
        "MUSIC":"Your Soundtrack",
        "MAPS":"Your Place",
        "WELLBEING":"A Moment for You",
        "COMPANION":"Time Together",
        "CONCIERGE":"Let MIRROR Take Care of It"
    }
    return names.get(u.get("intent"),"Let MIRROR Take Care of It")

def direction_for(u,p):
    intent=u.get("intent")
    signals=u.get("signals",[])
    directions=[]

    if intent=="TRAVEL":
        directions=["A destination matched to your current rhythm","A simple, private itinerary","Only the details that matter"]
    elif intent=="ESCAPE":
        directions=["A quieter environment","Minimal planning","Time to disconnect"]
    elif intent=="STAY":
        directions=["A stay aligned with your preferences","Privacy and comfort","A frictionless experience"]
    elif intent=="DINING":
        directions=["A dining experience suited to the occasion","Atmosphere before excess","A table chosen with intention"]
    elif intent=="EXPERIENCE":
        directions=["An experience with character","Something matched to your energy","A memorable moment without unnecessary complexity"]
    elif intent=="MUSIC":
        directions=["Music for this moment","A different atmosphere","A soundtrack that follows your mood"]
    elif intent=="MAPS":
        directions=["The place you're looking for","A direct route","Useful location details"]
    elif intent=="WELLBEING":
        directions=["A short breathing reset","A simple mental exercise","A quieter next few minutes"]
    elif intent=="COMPANION":
        directions=["Something meaningful together","Comfort without complication","A shared experience"]
    else:
        directions=["Clarify what matters most","Shape the right solution","Handle the next step"]

    if "PRIVACY" in signals and "Privacy first" not in directions:
        directions.insert(0,"Privacy first")
    if "SURPRISE" in signals:
        directions.insert(0,"A thoughtful surprise")

    return directions[:5]

def questions_for(u,missing):
    if not missing:return ""
    lang=u.get("language","en")
    field=missing[0]
    if lang=="es":
        return {
            "destination":"¿Dónde te gustaría que ocurriera?",
            "duration":"¿Cuánto tiempo quieres dedicarle?",
        }.get(field,"¿Qué detalle debería conocer para hacerlo bien?")
    return {
        "destination":"Where would you like this to happen?",
        "duration":"How much time would you like to dedicate to it?",
    }.get(field,"What detail should I know to get this right?")

def local_response(u,d):
    lang=u.get("language","en")
    if d["action"]=="ASK":
        return questions_for(u,d["missing"])
    if lang=="es":
        return "Entiendo lo que buscas. Voy a enfocarme en lo que realmente importa para ti."
    return "I understand what you're looking for. I'll focus on what actually matters to you."

def ai_prompt(text,u,p,d):
    lang=u.get("language","en")
    return f"""
You are MIRROR TO YOU, a discreet private life concierge.
You communicate as MIRROR itself, naturally and elegantly.
Never describe yourself as an AI, chatbot, model, algorithm, CRM, prompt, API or software system.
Do not mention technical implementation.
Do not invent bookings, reservations, prices, availability, providers or completed actions.
If real-world execution is not available, say that you can prepare the next step or that human concierge coordination is required.
Be concise, warm, intelligent and premium.
Do not overwhelm the client with lists.
Ask only ONE question when essential.
Language: {lang}

CLIENT MESSAGE:
{text}

UNDERSTANDING:
{json.dumps(u,ensure_ascii=False)}

PERSONAL CONTEXT:
{json.dumps(p,ensure_ascii=False)}

DECISION:
{json.dumps(d,ensure_ascii=False)}

Return ONLY valid JSON:
{{
 "reply":"natural response to the client",
 "title":"short elegant title",
 "direction":["up to 5 meaningful directions"],
 "question":"one question only, or empty string",
 "tone":"one short word",
 "next_action":"ASK, PROPOSE, or CONCIERGE"
}}
"""

def call_ai(prompt):
    if not AI_KEY:return None
    payload=json.dumps({
        "model":AI_MODEL,
        "messages":[
            {"role":"system","content":"You are MIRROR TO YOU, a discreet private life concierge."},
            {"role":"user","content":prompt}
        ],
        "temperature":0.9,
        "response_format":{"type":"json_object"}
    }).encode()

    req=urllib.request.Request(
        AI_URL,
        data=payload,
        headers={"Content-Type":"application/json","Authorization":f"Bearer {AI_KEY}"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req,timeout=12) as r:
            data=json.loads(r.read().decode())
        content=data["choices"][0]["message"]["content"]
        result=json.loads(content)
        return result if isinstance(result,dict) else None
    except Exception:
        return None

def proposal_for(text,u,p,d):
    return {
        "title":title_for(u),
        "direction":direction_for(u,p),
        "question":questions_for(u,d.get("missing",[])),
        "action":d["action"],
        "confidence":d["confidence"]
    }

def apply_ai(proposal,ai,d):
    if not ai:return proposal
    if clean(ai.get("title")):proposal["title"]=clean(ai["title"])
    if isinstance(ai.get("direction"),list):
        proposal["direction"]=[clean(x) for x in ai["direction"] if clean(x)][:5]
    proposal["question"]=clean(ai.get("question")) or proposal.get("question","")
    proposal["action"]=clean(ai.get("next_action")) or proposal["action"]
    proposal["tone"]=clean(ai.get("tone"))
    proposal["reply"]=clean(ai.get("reply"))
    return proposal

def process(text,memory=None):
    text=clean(text)
    memory=memory or {}
    u=understand(text,memory)
    p=personalize(u,memory)
    d=decision_for(u,p)
    proposal=proposal_for(text,u,p,d)

    ai=None
    if AI_KEY:
        ai=call_ai(ai_prompt(text,u,p,d))

    proposal=apply_ai(proposal,ai,d)

    if not proposal.get("reply"):
        proposal["reply"]=local_response(u,d)

    status={
        "NEW":"NEW",
        "ASK":"UNDERSTANDING",
        "PROPOSE":"PROPOSAL",
        "CONCIERGE":"CONCIERGE"
    }.get(proposal["action"],"UNDERSTANDING")

    return {
        "understanding":u,
        "personalization":p,
        "decision":d,
        "proposal":proposal,
        "status":status,
        "created_at":now()
    }

def response_text(result,language="en"):
    proposal=result.get("proposal") or {}
    reply=clean(proposal.get("reply"))
    if reply:return reply

    if language=="es":
        return "Estoy aquí. Dime qué quieres que me encargue de resolver."
    return "I'm here. Tell me what you'd like me to take care of."
