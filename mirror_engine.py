import os
import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import stripe

app = FastAPI(title="MIRROR TO YOU", version="1.0.0")

VOLATILE_KERNEL = {}
ACTIVE_ACCESS = {}  # Memoria volátil para controlar los accesos de pago por sesión temporal

# Carga de variables de entorno desde Render
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
PRICE_ID_SINGLE = os.getenv("STRIPE_PRICE_ID1")     # Pago único de $200
PRICE_ID_MONTHLY = os.getenv("STRIPE_PRICE_ID2")    # Suscripción mensual de $499

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    lang: str = "en"
    authType: Optional[str] = None
    clientSessionId: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class CheckoutRequest(BaseModel):
    priceType: str
    clientSessionId: str

class AccessCheckRequest(BaseModel):
    clientSessionId: str

class WellnessRequest(BaseModel):
    objective: str
    duration_seconds: int = 60

@app.post("/api/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook Error: {str(e)}")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        client_reference_id = session.get("client_reference_id")
        mode = session.get("mode")

        if client_reference_id:
            if mode == "payment":
                ACTIVE_ACCESS[client_reference_id] = {"type": "single", "active": True}
            elif mode == "subscription":
                ACTIVE_ACCESS[client_reference_id] = {"type": "unlimited", "active": True}

    return {"received": True}

@app.post("/api/auth/login")
async def admin_login(req: LoginRequest):
    if req.username == ADMIN_USERNAME and req.password == ADMIN_PASSWORD:
        return {"valid": True, "type": "admin"}
    raise HTTPException(status_code=401, detail="Credenciales inválidas.")

@app.post("/api/checkout/create-session")
async def create_checkout_session(req: CheckoutRequest, request: Request):
    price_id = PRICE_ID_MONTHLY if req.priceType == "unlimited" else PRICE_ID_SINGLE
    mode = "subscription" if req.priceType == "unlimited" else "payment"
    
    # Construcción limpia de URLs dinámicas basadas en la petición de origen para Render
    origin_url = request.headers.get("origin") or str(request.base_url)
    
    try:
        session = stripe.checkout.sessions.create(
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode=mode,
            client_reference_id=req.clientSessionId,
            success_url=f"{origin_url}?payment_status=success&session_id={req.clientSessionId}",
            cancel_url=f"{origin_url}?payment_status=cancel",
        )
        return {"url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/check-access")
async def check_session_access(req: AccessCheckRequest):
    if req.clientSessionId in ACTIVE_ACCESS and ACTIVE_ACCESS[req.clientSessionId]["active"]:
        return {"hasAccess": True, "details": ACTIVE_ACCESS[req.clientSessionId]}
    return {"hasAccess": False}

@app.post("/api/chat")
async def process_chat_directive(req: ChatRequest):
    global VOLATILE_KERNEL
    
    # Barrera e inspección estricta de derechos de acceso activos
    access_granted = False
    if req.authType == "admin":
        access_granted = True
    elif req.clientSessionId in ACTIVE_ACCESS and ACTIVE_ACCESS[req.clientSessionId]["active"]:
        access_granted = True
        # Si el acceso adquirido es de un solo servicio, se consume el token inmediatamente al procesar la primera consulta
        if ACTIVE_ACCESS[req.clientSessionId]["type"] == "single":
            ACTIVE_ACCESS[req.clientSessionId]["active"] = False

    if not access_granted:
        raise HTTPException(status_code=402, detail="Acceso denegado. Requiere autenticación o pago activo.")

    if req.messages:
        VOLATILE_KERNEL["last_directive"] = req.messages[-1].content

    system_prompt = (
        "Eres un asesor experto de bienestar y estilo de vida. Mantén el hilo de la conversación, sé conciso, directo, empático y guía al usuario paso a paso sin perder la coherencia de las preguntas anteriores."
        if req.lang == "es"
        else "You are an expert wellness and lifestyle advisor. Maintain the conversation thread, be concise, direct, empathetic, and guide the user step-by-step without losing coherence from previous questions."
    )

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            formatted_contents = []
            for msg in req.messages:
                gemini_role = "user" if msg.role == "user" else "model"
                formatted_contents.append({
                    "role": gemini_role,
                    "parts": [{"text": msg.content}]
                })

            gemini_url = f"https://googleapis.com{GEMINI_API_KEY}"
            payload = {
                "system_instruction": {"parts": [{"text": system_prompt}]},
                "contents": formatted_contents
            }
            response = await client.post(gemini_url, json=payload)
            if response.status_code == 200:
                data = response.json()
                reply = data["candidates"][0]["content"]["parts"][0]["text"]
                return {"reply": reply, "provider": "gemini"}
            else:
                raise Exception(f"Gemini status {response.status_code}")

        except Exception as gemini_error:
            try:
                openai_messages = [{"role": "system", "content": system_prompt}]
                for msg in req.messages:
                    openai_messages.append({"role": msg.role, "content": msg.content})

                openai_payload = {
                    "model": "gpt-4o-mini",
                    "messages": openai_messages,
                    "temperature": 0.7
                }
                headers = {
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                }

                openai_response = await client.post("https://openai.com", json=openai_payload, headers=headers)
                if openai_response.status_code == 200:
                    openai_data = openai_response.json()
                    reply = openai_data["choices"][0]["message"]["content"]
                    return {"reply": reply, "provider": "openai"}
                else:
                    raise Exception(f"OpenAI status {openai_response.status_code}")

            except Exception as openai_error:
                raise HTTPException(status_code=500, detail="No se pudo procesar la respuesta con el motor de asesoría.")

@app.post("/api/wellness")
async def process_wellness_routine(req: WellnessRequest):
    return {
        "status": "active",
        "objective": req.objective,
        "rhythm": "synchronized",
        "message": "Volatile anti-stress routine initiated."
    }

@app.delete("/api/clear")
async def clear_kernel_memory():
    global VOLATILE_KERNEL
    VOLATILE_KERNEL.clear()
    return {"status": "cleared", "memory": "zero"}

if os.path.exists("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
