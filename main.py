import os
import json
import uuid
import urllib.parse
from typing import Any,Dict,Optional,List

from fastapi import FastAPI,HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse,JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel,Field

from mirror_engine import (
    process,
    response_text,
    engine_status,
    feedback,
    revise
)

app=FastAPI(
    title="MIRROR TO YOU",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)

BASE_DIR=os.path.dirname(os.path.abspath(__file__))
STATIC_DIR=os.path.join(BASE_DIR,"static")

if os.path.isdir(STATIC_DIR):
    app.mount(
        "/static",
        StaticFiles(directory=STATIC_DIR),
        name="static"
    )

MISSIONS:List[Dict[str,Any]]=[]

class Memory(BaseModel):
    core:Dict[str,Any]=Field(default_factory=dict)
    preferences:Dict[str,Any]=Field(default_factory=dict)
    dislikes:List[str]=Field(default_factory=list)
    history:List[Dict[str,Any]]=Field(default_factory=list)
    daily:Dict[str,List[Dict[str,Any]]]=Field(default_factory=dict)
    feedback:List[Dict[str,Any]]=Field(default_factory=list)
    profile:Dict[str,Any]=Field(default_factory=dict)

class MirrorRequest(BaseModel):
    message:str=Field(default="")
    memory:Dict[str,Any]=Field(default_factory=dict)

class FeedbackRequest(BaseModel):
    memory:Dict[str,Any]=Field(default_factory=dict)
    experience_id:str=Field(default="")
    value:str=Field(default="")
    message:str=Field(default="")

class PlanRevisionRequest(BaseModel):
    memory:Dict[str,Any]=Field(default_factory=dict)
    experience_id:str=Field(default="")
    instruction:str=Field(default="")

class RecoveryRequest(BaseModel):
    answers:Dict[str,Any]=Field(default_factory=dict)
    memory:Dict[str,Any]=Field(default_factory=dict)

class ConciergeRequest(BaseModel):
    message:str=Field(default="")
    memory:Dict[str,Any]=Field(default_factory=dict)

def clean(value:Any,default=""):
    if value is None:
        return default
    if isinstance(value,str):
        return value.strip()
    return value

def create_mission(result:Dict[str,Any])->Dict[str,Any]:
    proposal=result.get("proposal",{})
    understanding=result.get("understanding",{})

    mission_id=f"mission_{uuid.uuid4().hex[:12]}"

    mission={
        "mission_id":mission_id,
        "created_at":result.get("today",{}).get("date"),
        "title":proposal.get("title",""),
        "direction":proposal.get("direction",""),
        "category":proposal.get("category","concierge"),
        "priority":proposal.get("priority","normal"),
        "status":proposal.get("status","ready"),
        "action":proposal.get("action",""),
        "next_move":proposal.get("next_move",""),
        "intent":understanding.get("intent"),
        "breathing":proposal.get("breathing")
    }

    MISSIONS.append(mission)

    if len(MISSIONS)>100:
        del MISSIONS[:-100]

    return mission

def public_plan(
    result:Dict[str,Any],
    mission:Dict[str,Any]
)->Dict[str,Any]:

    proposal=result.get("proposal",{})
    understanding=result.get("understanding",{})
    decision=result.get("decision",{})

    breathing=proposal.get("breathing")

    return {
        "title":clean(
            proposal.get("title"),
            "I'm listening."
        ),
        "direction":clean(
            proposal.get("direction"),
            "Tell me what you need, in your own words."
        ),
        "category":clean(
            proposal.get("category"),
            "concierge"
        ),
        "privacy":"private",
        "priority":clean(
            proposal.get("priority"),
            decision.get("priority","normal")
        ),
        "budget":understanding.get("budget"),
        "destination":understanding.get("destination"),
        "duration":understanding.get("duration"),
        "companion":understanding.get("companion"),
        "signals":understanding.get("signals",[]),
        "intent":understanding.get("intent"),
        "confidence":0.95,
        "status":clean(
            proposal.get("status"),
            "ready"
        ),
        "action":clean(
            proposal.get("action"),
            "continue"
        ),
        "next_move":clean(
            proposal.get("next_move"),
            "continue"
        ),
        "questions":proposal.get("questions",[]),
        "steps":proposal.get("steps",[]),
        "breathing":breathing,
        "mission_id":mission.get("mission_id")
    }

@app.get("/")
async def home():
    index_path=os.path.join(STATIC_DIR,"index.html")

    if not os.path.isfile(index_path):
        return JSONResponse(
            {
                "status":"error",
                "message":"MIRROR TO YOU interface not found."
            },
            status_code=500
        )

    return FileResponse(index_path)

@app.get("/favicon.ico")
async def favicon():
    path=os.path.join(STATIC_DIR,"favicon.ico")

    if os.path.isfile(path):
        return FileResponse(path)

    return JSONResponse({},status_code=204)

@app.get("/api/health")
async def health():
    return {
        "status":"ok",
        "service":"MIRROR TO YOU",
        "free":True
    }

@app.get("/api/status")
async def status():
    return engine_status()

@app.post("/api/mirror")
async def mirror(request:MirrorRequest):

    message=clean(request.message)

    if not message:
        raise HTTPException(
            status_code=400,
            detail="Please tell MIRROR what you need."
        )

    memory=request.memory or {}

    try:
        result=process(
            message,
            memory
        )

        mission=create_mission(result)

        plan=public_plan(
            result,
            mission
        )

        return {
            "status":"ok",
            "message":response_text(result),
            "analysis":result.get("decision",{}),
            "understanding":result.get("understanding",{}),
            "personalization":result.get("personalization",{}),
            "decision":result.get("decision",{}),
            "plan":plan,
            "mission":mission,
            "breathing":plan.get("breathing"),
            "memory":result.get("memory",{}),
            "today":result.get("today",{})
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"MIRROR could not process the request: {str(exc)}"
        )

@app.get("/api/missions")
async def get_missions():
    return {
        "status":"ok",
        "missions":MISSIONS[-50:]
    }

@app.get("/api/missions/{mission_id}")
async def get_mission(mission_id:str):

    for mission in reversed(MISSIONS):
        if mission.get("mission_id")==mission_id:
            return {
                "status":"ok",
                "mission":mission
            }

    raise HTTPException(
        status_code=404,
        detail="Mission not found."
    )

@app.post("/api/feedback")
async def send_feedback(request:FeedbackRequest):

    memory=request.memory or {}

    try:
        updated_memory=feedback(
            memory,
            request.experience_id,
            request.value,
            request.message
        )

        return {
            "status":"ok",
            "memory":updated_memory,
            "message":"Feedback received."
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )

@app.post("/api/revise")
async def revise_plan(request:PlanRevisionRequest):

    try:
        result=revise(
            request.memory or {},
            request.experience_id,
            request.instruction
        )

        return {
            "status":"ok",
            **result
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )

@app.post("/api/concierge")
async def concierge(request:ConciergeRequest):

    message=clean(request.message)

    if not message:
        raise HTTPException(
            status_code=400,
            detail="Please tell MIRROR what you need."
        )

    try:
        result=process(
            message,
            request.memory or {}
        )

        mission=create_mission(result)
        plan=public_plan(result,mission)

        return {
            "status":"ok",
            "message":response_text(result),
            "plan":plan,
            "mission":mission,
            "memory":result.get("memory",{}),
            "today":result.get("today",{})
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )

@app.get("/api/maps")
async def maps(
    destination:Optional[str]=None,
    query:Optional[str]=None
):

    search=clean(
        query or destination
    )

    if not search:
        raise HTTPException(
            status_code=400,
            detail="A place or search term is required."
        )

    encoded=urllib.parse.quote_plus(search)

    url=(
        "https://www.google.com/maps/search/"
        f"?api=1&query={encoded}"
    )

    return {
        "status":"ok",
        "destination":search,
        "url":url
    }

@app.get("/api/music")
async def music(
    query:Optional[str]=None
):

    search=clean(query)

    if not search:
        search="music for this moment"

    encoded=urllib.parse.quote_plus(search)

    url=(
        "https://www.youtube.com/results"
        f"?search_query={encoded}"
    )

    return {
        "status":"ok",
        "query":search,
        "url":url
    }

@app.post("/api/voice/text")
async def voice_text(request:MirrorRequest):

    text=clean(request.message)

    return {
        "status":"ok",
        "text":text
    }

@app.get("/api/providers")
async def providers():

    return {
        "status":"ok",
        "providers":[],
        "message":"Real providers will be connected only when verified integrations are available."
    }

@app.get("/api/recovery/questions")
async def recovery_questions():

    return {
        "status":"ok",
        "questions":[
            {
                "id":"favorite_place",
                "question":"What kind of place feels most like you?",
                "type":"text"
            },
            {
                "id":"preferred_pace",
                "question":"Which pace feels most natural to you?",
                "type":"choice",
                "options":[
                    "slow",
                    "balanced",
                    "active"
                ]
            },
            {
                "id":"privacy_level",
                "question":"How private would you like your experience to feel?",
                "type":"choice",
                "options":[
                    "quiet",
                    "private",
                    "very_private"
                ]
            },
            {
                "id":"experience_style",
                "question":"What would you rather receive right now?",
                "type":"choice",
                "options":[
                    "something_simple",
                    "something_special",
                    "something_new",
                    "let_mirror_choose"
                ]
            }
        ]
    }

@app.post("/api/recovery")
async def recovery(request:RecoveryRequest):

    memory=request.memory or {}
    answers=request.answers or {}

    core=memory.setdefault("core",{})
    preferences=memory.setdefault("preferences",{})

    if answers.get("favorite_place"):
        core["favorite_place"]=answers["favorite_place"]

    if answers.get("preferred_pace"):
        preferences["preferred_pace"]=answers["preferred_pace"]

    if answers.get("privacy_level"):
        preferences["privacy_level"]=answers["privacy_level"]

    if answers.get("experience_style"):
        preferences["experience_style"]=answers["experience_style"]

    profile=memory.setdefault("profile",{})
    profile["memory_recovered"]=True

    return {
        "status":"ok",
        "memory":memory,
        "message":"Your preferences have been reconnected."
    }

@app.post("/api/memory/clear")
async def clear_memory():

    return {
        "status":"ok",
        "memory":{
            "core":{},
            "preferences":{},
            "dislikes":[],
            "history":[],
            "daily":{},
            "feedback":[],
            "profile":{}
        }
    }

@app.get("/api/config")
async def config():

    return {
        "status":"ok",
        "name":"MIRROR TO YOU",
        "free":True,
        "payments":False,
        "stripe":False,
        "ai_visible":False,
        "memory":"client_side",
        "maps":True,
        "music":True,
        "breathing":True
    }

@app.exception_handler(Exception)
async def global_exception_handler(request,exc):

    return JSONResponse(
        status_code=500,
        content={
            "status":"error",
            "message":"MIRROR encountered an unexpected problem."
        }
    )

if __name__=="__main__":
    import uvicorn

    port=int(os.getenv("PORT","10000"))

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port
    )
