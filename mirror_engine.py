import os
import httpx
import hmac
import hashlib
import json
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List

app = FastAPI(title="MIRROR TO YOU", version="1.0.0")

VOLATILE_KERNEL = {}

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Credenciales y Configuración de Stripe desde Variables de Entorno de Render
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "password")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
STRIPE_PRICE_ID1 = os.getenv("STRIPE_PRICE_ID1")  # Servicio único ($200)
STRIPE_PRICE_ID2 = os.getenv("STRIPE_PRICE_ID2")  # Suscripción mensual ($499)
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    lang: str = "en"

class WellnessRequest(BaseModel):
    objective: str
    duration_seconds: int = 60

class LoginRequest(BaseModel):
    username: str
    password: str

class CheckoutRequest(BaseModel):
    price_id: str

@app.post("/api/chat")
async def process_chat_directive(req: ChatRequest):
    global VOLATILE_KERNEL
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

            gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
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

                openai_response = await client.post("https://api.openai.com/v1/chat/completions", json=openai_payload, headers=headers)
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

@app.post("/api/login")
async def admin_login(req: LoginRequest):
    if req.username == ADMIN_USERNAME and req.password == ADMIN_PASSWORD:
        return {"status": "success", "message": "Access granted"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/api/stripe-config")
async def get_stripe_config():
    return {
        "publishableKey": STRIPE_PUBLISHABLE_KEY,
        "priceId1": STRIPE_PRICE_ID1,
        "priceId2": STRIPE_PRICE_ID2
    }

@app.post("/api/create-checkout-session")
async def create_checkout_session(req: CheckoutRequest):
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {STRIPE_SECRET_KEY}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        mode = "subscription" if req.price_id == STRIPE_PRICE_ID2 else "payment"
        data = {
            "payment_method_types[0]": "card",
            "line_items[0][price]": req.price_id,
            "line_items[0][quantity]": "1",
            "mode": mode,
            "success_url": "https://mirror-to-you.onrender.com/?success=true",
            "cancel_url": "https://mirror-to-you.onrender.com/?canceled=true"
        }
        response = await client.post("https://api.stripe.com/v1/checkout/sessions", data=data, headers=headers)
        if response.status_code == 200:
            session_data = response.json()
            return {"url": session_data["url"]}
        else:
            raise HTTPException(status_code=500, detail="Error creating Stripe checkout session")

@app.post("/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    payload = await request.body()
    if STRIPE_WEBHOOK_SECRET and stripe_signature:
        try:
            sig_parts = dict(tuple(item.split('=')) for item in stripe_signature.split(','))
            timestamp = sig_parts.get('t')
            v1_sig = sig_parts.get('v1')
            signed_payload = f"{timestamp}.".encode('utf-8') + payload
            expected_sig = hmac.new(
                STRIPE_WEBHOOK_SECRET.encode('utf-8'),
                signed_payload,
                hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(expected_sig, v1_sig):
                raise HTTPException(status_code=400, detail="Invalid webhook signature")
        except Exception:
            pass

    event = json.loads(payload.decode('utf-8'))
    if event.get("type") == "checkout.session.completed":
        session = event["data"]["object"]
        # Registro o activación segura del servicio cumplido
        VOLATILE_KERNEL["last_paid_session"] = session.get("id")

    return {"status": "success"}

if os.path.exists("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
