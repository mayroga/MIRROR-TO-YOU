import os,uuid,urllib.parse
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI,HTTPException
from fastapi.responses import FileResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field
from mirror_engine import process,response_text

BASE=Path(__file__).resolve().parent
STATIC=BASE/"static"

app=FastAPI(title="MIRROR TO YOU",version="2.0")

if STATIC.exists():
    app.mount("/static",StaticFiles(directory=str(STATIC)),name="static")

MISSIONS={}

def now():
    return datetime.now().isoformat(timespec="seconds")

def clean(v):
    if v is None:return ""
    return str(v).strip()

def normalize_memory(data):
    data=data if isinstance(data,dict) else {}
    def obj(v):
        return v if isinstance(v,dict) else {}
    def arr(v):
        return v if isinstance(v,list) else []
    result={
        "core":obj(data.get("core")),
        "moment":obj(data.get("moment")),
        "preferences":obj(data.get("preferences")),
        "dislikes":arr(data.get("dislikes")),
        "history":arr(data.get("history")),
        "learning":obj(data.get("learning"))
    }
    if data.get("recovered_at"):
        result["recovered_at"]=data["recovered_at"]
    return result

class Memory(BaseModel):
    core:dict=Field(default_factory=dict)
    moment:dict=Field(default_factory=dict)
    preferences:dict=Field(default_factory=dict)
    dislikes:list=Field(default_factory=list)
    history:list=Field(default_factory=list)
    learning:dict=Field(default_factory=dict)
    recovered_at:str|None=None

class MirrorRequest(BaseModel):
    message:str=""
    language:str="en"
    device_id:str=""
    memory:Memory=Field(default_factory=Memory)

class FeedbackRequest(BaseModel):
    mission_id:str
    feedback:str=""
    memory:Memory=Field(default_factory=Memory)

class PlanRevisionRequest(BaseModel):
    mission_id:str
    note:str=""
    memory:Memory=Field(default_factory=Memory)

class ConciergeRequest(BaseModel):
    note:str=""
    memory:Memory=Field(default_factory=Memory)

class RecoveryRequest(BaseModel):
    answers:dict=Field(default_factory=dict)
    memory:Memory=Field(default_factory=Memory)

class VoiceRequest(BaseModel):
    text:str=""
    language:str="en"

def update_memory(memory,result):
    memory=normalize_memory(memory)
    u=result.get("understanding") or {}
    p=result.get("personalization") or {}

    if u.get("language"):
        memory["moment"]["language"]=u["language"]
    if u.get("intent"):
        memory["moment"]["intent"]=u["intent"]
    if u.get("destination"):
        memory["moment"]["destination"]=u["destination"]
    if u.get("companion"):
        memory["moment"]["companion"]=u["companion"]
    if u.get("signals"):
        memory["moment"]["signals"]=u["signals"]

    if p.get("name") and not memory["core"].get("name"):
        memory["core"]["name"]=p["name"]

    entry={
        "at":now(),
        "intent":u.get("intent",""),
        "destination":u.get("destination",""),
        "signals":u.get("signals",[])
    }

    memory["history"].append(entry)
    memory["history"]=memory["history"][-30:]
    return memory

def public_plan(result,mission_id):
    u=result.get("understanding") or {}
    p=result.get("proposal") or {}
    d=result.get("decision") or {}

    return {
        "title":p.get("title","Let MIRROR take care of it"),
        "reply":p.get("reply",""),
        "direction":p.get("direction",[]),
        "question":p.get("question",""),
        "action":p.get("action",d.get("action","ASK")),
        "confidence":p.get("confidence",d.get("confidence",0)),
        "destination":u.get("destination",""),
        "intent":u.get("intent",""),
        "mission_id":mission_id
    }

@app.get("/")
async def home():
    index=STATIC/"index.html"
    if not index.exists():
        return JSONResponse({"ok":False,"error":"static/index.html not found"},status_code=500)
    return FileResponse(index)

@app.get("/api/health")
async def health():
    return {
        "ok":True,
        "service":"MIRROR TO YOU",
        "status":"online",
        "time":now()
    }

@app.get("/api/config")
async def config():
    return {
        "ok":True,
        "name":"MIRROR TO YOU",
        "voice":True,
        "memory":"device",
        "breathing":True,
        "maps":True,
        "music":True
    }

@app.post("/api/mirror")
async def mirror(data:MirrorRequest):
    message=clean(data.message)

    if not message:
        return JSONResponse(
            {"ok":False,"error":"Please tell MIRROR what you need."},
            status_code=400
        )

    memory=normalize_memory(data.memory.model_dump())

    try:
        result=process(message,memory)
    except Exception as e:
        return JSONResponse(
            {"ok":False,"error":"MIRROR could not process that request right now."},
            status_code=500
        )

    mission_id="mission_"+uuid.uuid4().hex[:12]
    memory=update_memory(memory,result)

    plan=public_plan(result,mission_id)

    mission={
        "id":mission_id,
        "status":result.get("status","UNDERSTANDING"),
        "created_at":now(),
        "understanding":result.get("understanding",{}),
        "plan":plan
    }

    MISSIONS[mission_id]=mission

    return {
        "ok":True,
        "message":response_text(result,data.language),
        "understanding":result.get("understanding",{}),
        "personalization":result.get("personalization",{}),
        "decision":result.get("decision",{}),
        "plan":plan,
        "mission":{
            "id":mission_id,
            "status":mission["status"]
        },
        "memory":memory
    }

@app.get("/api/missions")
async def missions():
    items=[]
    for m in MISSIONS.values():
        items.append({
            "id":m["id"],
            "status":m["status"],
            "created_at":m["created_at"]
        })
    return {"ok":True,"missions":items[-30:]}

@app.get("/api/missions/{mission_id}")
async def mission(mission_id:str):
    item=MISSIONS.get(mission_id)
    if not item:
        raise HTTPException(status_code=404,detail="Mission not found")
    return {"ok":True,"mission":item}

@app.post("/api/missions/feedback")
async def feedback(data:FeedbackRequest):
    item=MISSIONS.get(data.mission_id)
    if not item:
        raise HTTPException(status_code=404,detail="Mission not found")

    feedback=clean(data.feedback)

    item["feedback"]=feedback
    item["feedback_at"]=now()

    memory=normalize_memory(data.memory.model_dump())
    memory["learning"]["last_feedback"]=feedback

    return {
        "ok":True,
        "message":"MIRROR is learning your preferences.",
        "mission":item,
        "memory":memory
    }

@app.post("/api/missions/revise")
async def revise(data:PlanRevisionRequest):
    item=MISSIONS.get(data.mission_id)
    if not item:
        raise HTTPException(status_code=404,detail="Mission not found")

    note=clean(data.note)
    memory=normalize_memory(data.memory.model_dump())

    if note:
        item["revision"]=note
        item["revision_at"]=now()

    return {
        "ok":True,
        "message":"MIRROR has adjusted the direction.",
        "mission":item,
        "plan":item.get("plan",{}),
        "memory":memory
    }

@app.post("/api/missions/{mission_id}/concierge")
async def concierge(mission_id:str,data:ConciergeRequest):
    item=MISSIONS.get(mission_id)
    if not item:
        raise HTTPException(status_code=404,detail="Mission not found")

    item["status"]="CONCIERGE"
    item["concierge_requested_at"]=now()

    note=clean(data.note)
    if note:
        item["concierge_note"]=note

    return {
        "ok":True,
        "message":"MIRROR has prepared the next step for concierge coordination.",
        "mission":{
            "id":mission_id,
            "status":"CONCIERGE"
        }
    }

@app.get("/api/maps")
async def maps(destination:str=""):
    destination=clean(destination)
    if not destination:
        return JSONResponse(
            {"ok":False,"error":"Destination required"},
            status_code=400
        )

    url="https://www.google.com/maps/search/?api=1&query="+urllib.parse.quote(destination)

    return {
        "ok":True,
        "destination":destination,
        "url":url
    }

@app.get("/api/music")
async def music(query:str="relaxing elegant music"):
    query=clean(query) or "relaxing elegant music"
    url="https://www.youtube.com/results?search_query="+urllib.parse.quote(query)

    return {
        "ok":True,
        "query":query,
        "url":url
    }

@app.post("/api/voice/text")
async def voice_text(data:VoiceRequest):
    text=clean(data.text)

    if not text:
        return JSONResponse(
            {"ok":False,"error":"Text required"},
            status_code=400
        )

    return {
        "ok":True,
        "text":text,
        "language":clean(data.language) or "en"
    }

@app.get("/api/providers")
async def providers():
    return {
        "ok":True,
        "providers":[],
        "message":"Real providers can be connected when execution is enabled."
    }

@app.get("/api/memory/recovery/questions")
async def recovery_questions():
    return {
        "ok":True,
        "questions":[
            "What should MIRROR call you?",
            "What matters most to you right now?",
            "What kind of atmosphere do you prefer?",
            "Anything MIRROR should avoid?"
        ]
    }

@app.post("/api/memory/recovery")
async def recovery(data:RecoveryRequest):
    memory=normalize_memory(data.memory.model_dump())
    answers=data.answers if isinstance(data.answers,dict) else {}

    for key,value in answers.items():
        value=clean(value)
        if not value:
            continue

        if key=="name":
            memory["core"]["name"]=value
        elif key=="avoid":
            memory["dislikes"]=[
                x.strip() for x in value.split(",") if x.strip()
            ]
        else:
            memory["preferences"][key]=value
            memory["moment"][key]=value

    memory["recovered_at"]=now()

    return {
        "ok":True,
        "memory":memory,
        "message":"MIRROR is getting to know your rhythm again."
    }

@app.exception_handler(Exception)
async def global_error(request,exc):
    return JSONResponse(
        {"ok":False,"error":"MIRROR encountered a temporary problem."},
        status_code=500
    )
