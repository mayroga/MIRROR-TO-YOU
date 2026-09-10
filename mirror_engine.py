import os,time,httpx,stripe
from fastapi import FastAPI,HTTPException,Request,Depends,status
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List

app=FastAPI(title="MIRROR TO YOU",version="2.2.0")

# CONFIGURACIÓN

ADMIN_USERNAME=os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD=os.getenv("ADMIN_PASSWORD")
GEMINI_API_KEY=os.getenv("GEMINI_API_KEY")
GEMINI_MODEL=os.getenv("GEMINI_MODEL","gemini-2.5-flash")

stripe.api_key=os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET=os.getenv("STRIPE_WEBHOOK_SECRET")
STRIPE_PRICE_ID1=os.getenv("STRIPE_PRICE_ID1")
STRIPE_PRICE_ID2=os.getenv("STRIPE_PRICE_ID2")

# KERNEL DE SESIÓN

VOLATILE_KERNEL={
"session_active":False,
"expires_at":0.0,
"is_premium":False,
"last_directive":None
}

# MODELOS

class LoginRequest(BaseModel):
username:str
password:str

class Message(BaseModel):
role:str
content:str

class ChatRequest(BaseModel):
messages:List
lang:str="en"

class WellnessRequest(BaseModel):
objective:str
duration_seconds:int=60

class StripeSessionRequest(BaseModel):
price_tier:int

# SEGURIDAD

def verify_active_session():
now=time.time()

```
if not VOLATILE_KERNEL.get("session_active"):
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied. No active or paid session."
    )

if not VOLATILE_KERNEL.get("is_premium") and now>VOLATILE_KERNEL.get("expires_at",0):
    VOLATILE_KERNEL.update(
        session_active=False,
        is_premium=False,
        expires_at=0.0
    )
    raise HTTPException(
        status_code=status.HTTP_408_REQUEST_TIMEOUT,
        detail="The 10-minute session has expired."
    )
```

# LOGIN ADMINISTRATIVO

@app.post("/api/auth/login")
async def admin_login(req:LoginRequest):
if req.username==ADMIN_USERNAME and req.password==ADMIN_PASSWORD:
VOLATILE_KERNEL.update(
session_active=True,
is_premium=False,
expires_at=time.time()+600.0,
last_directive=None
)
return {
"status":"success",
"message":"Authentication successful. 10-minute session started.",
"expires_at":VOLATILE_KERNEL
}

```
raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid credentials."
)
```

# STRIPE CHECKOUT

@app.post("/api/stripe/create-checkout")
async def create_checkout_session(req:StripeSessionRequest,request:Request):
if req.price_tier not in (1,2):
raise HTTPException(status_code=400,detail="Invalid price tier.")

```
price_id=STRIPE_PRICE_ID1 if req.price_tier==1 else STRIPE_PRICE_ID2

if not price_id:
    raise HTTPException(
        status_code=500,
        detail="Stripe Price ID is not configured."
    )

origin=request.headers.get("origin")
if not origin:
    host=request.headers.get("host")
    origin=f"http://{host}" if host else "https://mirror-to-you.onrender.com"

mode="payment" if req.price_tier==1 else "subscription"

try:
    session=stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{"price":price_id,"quantity":1}],
        mode=mode,
        success_url=f"{origin}/?stripe_status=success",
        cancel_url=f"{origin}/?stripe_status=cancel",
        metadata={"tier":str(req.price_tier)}
    )
    return {"url":session.url}

except Exception as e:
    print(f"[STRIPE ERROR] {e}")
    raise HTTPException(
        status_code=500,
        detail="Unable to create Stripe checkout session."
    )
```

# STRIPE WEBHOOK

@app.post("/api/stripe/webhook")
async def stripe_webhook(request:Request):
payload=await request.body()
signature=request.headers.get("stripe-signature")

```
try:
    event=stripe.Webhook.construct_event(
        payload,
        signature,
        STRIPE_WEBHOOK_SECRET
    )
except ValueError:
    raise HTTPException(status_code=400,detail="Invalid payload.")
except stripe.error.SignatureVerificationError:
    raise HTTPException(status_code=400,detail="Invalid webhook signature.")

if event["type"]=="checkout.session.completed":
    session=event["data"]["object"]
    metadata=session.get("metadata",{})
    tier=metadata.get("tier","1")

    VOLATILE_KERNEL["session_active"]=True

    if tier=="2":
        VOLATILE_KERNEL["is_premium"]=True
        VOLATILE_KERNEL["expires_at"]=time.time()+2592000.0
    else:
        VOLATILE_KERNEL["is_premium"]=False
        VOLATILE_KERNEL["expires_at"]=time.time()+600.0

    return {"status":"success"}

return {"status":"event_unhandled"}
```

# ESTADO DE SESIÓN

@app.get("/api/auth/session-status")
async def get_session_status():
now=time.time()
active=VOLATILE_KERNEL.get("session_active",False)
premium=VOLATILE_KERNEL.get("is_premium",False)
expires=VOLATILE_KERNEL.get("expires_at",0.0)

```
if active and (premium or now<=expires):
    return {
        "active":True,
        "is_premium":premium,
        "time_left":2592000 if premium else max(0,int(expires-now))
    }

VOLATILE_KERNEL.update(
    session_active=False,
    is_premium=False,
    expires_at=0.0
)

return {
    "active":False,
    "is_premium":False,
    "time_left":0
}
```

# GEMINI — ÚNICO MOTOR DE IA

@app.post("/api/chat",dependencies=[Depends(verify_active_session)])
async def process_chat_directive(req:ChatRequest):
if not req.messages:
raise HTTPException(
status_code=400,
detail="The message history is empty."
)

```
VOLATILE_KERNEL["last_directive"]=req.messages[-1].content

if req.lang=="es":
    system_prompt=(
        "Eres MIRROR TO YOU, un asesor privado de bienestar y estilo de vida. "
        "Mantén siempre el hilo completo de la conversación. "
        "Sé conciso, directo, empático y personalizado. "
        "Guía al usuario paso a paso y evita respuestas genéricas."
    )
else:
    system_prompt=(
        "You are MIRROR TO YOU, a private wellness and lifestyle advisor. "
        "Always maintain the complete conversation thread. "
        "Be concise, direct, empathetic and personalized. "
        "Guide the user step by step and avoid generic responses."
    )

contents=[]

for msg in req.messages:
    role=str(msg.role).lower().strip()
    gemini_role="user" if role in ("user","usuario") else "model"
    contents.append({
        "role":gemini_role,
        "parts":[{"text":msg.content}]
    })

if not GEMINI_API_KEY:
    return {
        "reply":(
            "El servicio de inteligencia no está disponible en este momento."
            if req.lang=="es"
            else
            "The intelligence service is not available at this moment."
        )
    }

url=(
    "https://generativelanguage.googleapis.com/"
    f"v1beta/models/{GEMINI_MODEL}:generateContent"
    f"?key={GEMINI_API_KEY.strip()}"
)

payload={
    "system_instruction":{"parts":[{"text":system_prompt}]},
    "contents":contents,
    "generationConfig":{"temperature":0.7}
}

try:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response=await client.post(url,json=payload)

    if response.status_code!=200:
        print(f"[GEMINI ERROR] {response.status_code}: {response.text[:500]}")
        return {
            "reply":(
                "Estoy procesando tu solicitud. Inténtalo nuevamente."
                if req.lang=="es"
                else
                "I am processing your request. Please try again."
            )
        }

    data=response.json()
    reply=data["candidates"][0]["content"]["parts"][0]["text"]
    return {"reply":reply}

except Exception as e:
    print(f"[GEMINI EXCEPTION] {e}")
    return {
        "reply":(
            "Estoy procesando tu solicitud. Inténtalo nuevamente."
            if req.lang=="es"
            else
            "I am processing your request. Please try again."
        )
    }
```

# WELLNESS

@app.post("/api/wellness",dependencies=[Depends(verify_active_session)])
async def process_wellness_routine(req:WellnessRequest):
return {
"status":"active",
"objective":req.objective,
"rhythm":"synchronized",
"message":"Volatile anti-stress routine initiated."
}

# LIMPIAR SESIÓN

@app.delete("/api/clear")
async def clear_kernel_memory():
VOLATILE_KERNEL.update(
session_active=False,
is_premium=False,
expires_at=0.0,
last_directive=None
)
return {"status":"cleared","memory":"zero"}

# FRONTEND

if os.path.exists("static"):
app.mount("/",StaticFiles(directory="static",html=True),name="static")
