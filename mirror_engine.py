import os
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List

app = FastAPI(title="MIRROR TO YOU", version="1.0.0")
# Carga estricta de variables de entorno de Render
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configuración de Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
STRIPE_PRICE_ID1 = os.getenv("STRIPE_PRICE_ID1")
STRIPE_PRICE_ID2 = os.getenv("STRIPE_PRICE_ID2")
# 1. Endpoint de Autenticación por Username y Password
@app.post("/api/auth/login")
async def admin_login(req: LoginRequest):
    global VOLATILE_KERNEL
    if req.username == ADMIN_USERNAME and req.password == ADMIN_PASSWORD:
        VOLATILE_KERNEL["session_active"] = True
        VOLATILE_KERNEL["is_premium"] = False
        VOLATILE_KERNEL["expires_at"] = time.time() + 600.0
        return {
            "status": "success",
            "message": "Autenticación correcta. Sesión de 10 minutos iniciada.",
            "expires_at": VOLATILE_KERNEL["expires_at"]
        }
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales incorrectas."
    )

# 2. Endpoints de Stripe: Creación de Checkout Session
@app.post("/api/stripe/create-checkout")
async def create_checkout_session(req: StripeSessionRequest, request: Request):
    price_id = STRIPE_PRICE_ID1 if req.price_tier == 1 else STRIPE_PRICE_ID2
    if not price_id:
        raise HTTPException(status_code=500, detail="ID de precio de Stripe no configurado en el servidor.")
    origin = request.headers.get("origin") or f"http://{request.headers.get('host')}"
    stripe_mode = 'payment' if req.price_tier == 1 else 'subscription'
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode=stripe_mode,
            success_url=f"{origin}/?stripe_status=success",
            cancel_url=f"{origin}/?stripe_status=cancel",
            metadata={"tier": str(req.price_tier)}
        )
        return {"url": checkout_session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 3. Webhook de Stripe para autorizar el servicio tras el cobro efectivo
@app.post("/api/stripe/webhook")
async def stripe_webhook(request: Request):
    global VOLATILE_KERNEL
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Payload inválido")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Firma de webhook inválida")
    
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        session_dict = session.to_dict()
        metadata = session_dict.get('metadata', {})
        tier = metadata.get('tier', '1') if metadata else '1'
        
        VOLATILE_KERNEL["session_active"] = True
        if tier == "2":
            VOLATILE_KERNEL["is_premium"] = True
            VOLATILE_KERNEL["expires_at"] = time.time() + 2592000.0
        else:
            VOLATILE_KERNEL["is_premium"] = False
            VOLATILE_KERNEL["expires_at"] = time.time() + 600.0
        return {"status": "success"}
    return {"status": "event_unhandled"}

# 4. Verificación de Estado de la Sesión Actual
@app.get("/api/auth/session-status")
async def get_session_status():
    global VOLATILE_KERNEL
    current_time = time.time()
    
    session_active = VOLATILE_KERNEL.get("session_active", False)
    is_premium = VOLATILE_KERNEL.get("is_premium", False)
    expires_at = VOLATILE_KERNEL.get("expires_at", 0.0)
    
    if session_active:
        if is_premium or (current_time <= expires_at):
            time_left = max(0, int(expires_at - current_time)) if not is_premium else 2592000
            return {
                "active": True,
                "is_premium": is_premium,
                "time_left": time_left
            }
    
    VOLATILE_KERNEL["session_active"] = False
    VOLATILE_KERNEL["is_premium"] = False
    VOLATILE_KERNEL["expires_at"] = 0.0
    return {"active": False, "is_premium": False, "time_left": 0}
VOLATILE_KERNEL = {}

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    lang: str = "en"

class WellnessRequest(BaseModel):
    objective: str
    duration_seconds: int = 60

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

if os.path.exists("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
