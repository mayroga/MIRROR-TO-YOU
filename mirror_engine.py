import os
import httpx
import stripe
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List

app = FastAPI(title="MIRROR TO YOU", version="1.0.0")

# Inicializar Stripe con la llave secreta y el webhook secret desde Render
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

VOLATILE_KERNEL = {}

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Credenciales de administración/acceso libre obtenidas de Render
ADMIN_USER = os.getenv("ADMIN_USERNAME")
ADMIN_PASS = os.getenv("ADMIN_PASSWORD")

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    lang: str = "en"

class WellnessRequest(BaseModel):
    objective: str
    duration_seconds: int = 60

class CheckoutRequest(BaseModel):
    price_type: str  # "1" para $200 (diario) o "2" para $499 (mensual)

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/create-checkout-session")
async def create_checkout_session(req: CheckoutRequest):
    try:
        # Seleccionar el Price ID correspondiente basado en las variables de Render
        price_id = os.getenv("STRIPE_PRICE_ID1") if req.price_type == "1" else os.getenv("STRIPE_PRICE_ID2")
        
        if not price_id:
            raise HTTPException(status_code=400, detail="Price ID de Stripe no configurado en el servidor.")

        # Obtener el dominio actual o usar la URL de tu app en Render
        domain_url = os.getenv("RENDER_EXTERNAL_URL", "https://mirror-to-you.onrender.com")

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='payment' if req.price_type == "1" else 'subscription',
            success_url=domain_url + "/?success=true",
            cancel_url=domain_url + "/?canceled=true",
        )
        return {"url": checkout_session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    payload = await request.body()

    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=400, detail="Webhook secret not configured.")

    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Respaldo automático: captura cuando un pago o suscripción se completa exitosamente
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        # Aquí puedes registrar la transacción o activar accesos de respaldo en el servidor
        print(f"Pago confirmado mediante Webhook para la sesión: {session.get('id')}")

    return {"status": "success"}

@app.post("/api/login")
async def login_access(req: LoginRequest):
    # Validar contra las variables ADMIN_USERNAME y ADMIN_PASSWORD de Render
    if ADMIN_USER and ADMIN_PASS and req.username == ADMIN_USER and req.password == ADMIN_PASS:
        return {"status": "success", "message": "Acceso autorizado"}
    raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

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
