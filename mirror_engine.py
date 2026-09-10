import os
import time
import httpx
import stripe
from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional

# Inicialización de la aplicación
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

# Núcleo Volátil en Memoria para control de estado sin base de datos
# Estructura: {"session_active": bool, "expires_at": float, "is_premium": bool, "last_directive": str}
VOLATILE_KERNEL = {
    "session_active": False,
    "expires_at": 0.0,
    "is_premium": False,
    "last_directive": None
}

# Modelos de Datos (Pydantic)
class LoginRequest(BaseModel):
    username: str
    password: str

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    lang: str = "en"

class WellnessRequest(BaseModel):
    objective: str
    duration_seconds: int = 60

class StripeSessionRequest(BaseModel):
    price_tier: int  # 1 o 2 para seleccionar el Price ID correspondiente

# Dependencia de seguridad: Bloquea cualquier endpoint si la sesión no está activa o expiró
def verify_active_session():
    global VOLATILE_KERNEL
    current_time = time.time()
    if not VOLATILE_KERNEL.get("session_active", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. No hay ninguna sesión activa o pagada."
        )
    # Si NO es usuario premium ($499), evaluar estrictamente el límite de 10 minutos
    if not VOLATILE_KERNEL.get("is_premium", False):
        if current_time > VOLATILE_KERNEL.get("expires_at", 0.0):
            VOLATILE_KERNEL["session_active"] = False
            VOLATILE_KERNEL["is_premium"] = False
            VOLATILE_KERNEL["expires_at"] = 0.0
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="La sesión de 10 minutos ha expirado por completo. Todo el servicio queda bloqueado."
            )

# 1. Endpoint de Autenticación por Username y Password
@app.post("/api/auth/login")
async def admin_login(req: LoginRequest):
    global VOLATILE_KERNEL  # <-- Forzar alcance global global en servidores asíncronos de Render
    if req.username == ADMIN_USERNAME and req.password == ADMIN_PASSWORD:
        # Activa la sesión inmediatamente por 10 minutos (600 segundos)
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

# 2. Endpoints de Stripe: Creación de Checkout Session (Actualizado con modo Suscripción dinámico)
@app.post("/api/stripe/create-checkout")
async def create_checkout_session(req: StripeSessionRequest, request: Request):
    price_id = STRIPE_PRICE_ID1 if req.price_tier == 1 else STRIPE_PRICE_ID2
    if not price_id:
        raise HTTPException(status_code=500, detail="ID de precio de Stripe no configurado en el servidor.")
    
    # Obtener el dominio base dinámicamente para soportar Render o localhost
    origin = request.headers.get("origin") or f"http://{request.headers.get('host')}"
    
    # REGLA DE NEGOCIO: Si el tier es 1 es un Pago Único ('payment'). Si es tier 2 es Suscripción Mensual ('subscription').
    stripe_mode = 'payment' if req.price_tier == 1 else 'subscription'
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode=stripe_mode,  # <-- Configuración dinámica crucial para habilitar los $499
            success_url=f"{origin}/?stripe_status=success",
            cancel_url=f"{origin}/?stripe_status=cancel",
            metadata={"tier": str(req.price_tier)}  # Guardamos de forma segura el plan comprado
        )
        return {"url": checkout_session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 3. Webhook de Stripe para autorizar el servicio tras el cobro efectivo
@app.post("/api/stripe/webhook")
async def stripe_webhook(request: Request):
    global VOLATILE_KERNEL  # <-- Obligatorio: Sincroniza la escritura del evento de pago hacia Render
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
    
    # Si el pago se procesó de forma exitosa, se concede acceso según los metadatos del tier comprado
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        tier = session.get('metadata', {}).get('tier', '1')
        
        VOLATILE_KERNEL["session_active"] = True
        if tier == "2":
            # Plan Premium de $499: Acceso ilimitado por 30 días (2592000 segundos)
            VOLATILE_KERNEL["is_premium"] = True
            VOLATILE_KERNEL["expires_at"] = time.time() + 2592000.0
        else:
            # Plan Estándar de $200: Acceso tradicional por 10 minutos
            VOLATILE_KERNEL["is_premium"] = False
            VOLATILE_KERNEL["expires_at"] = time.time() + 600.0
        return {"status": "success"}
    return {"status": "event_unhandled"}

# 4. Verificación de Estado de la Sesión Actual (Utilizado por el frontend)
@app.get("/api/auth/session-status")
async def get_session_status():
    global VOLATILE_KERNEL  # <-- Obligatorio: Sincroniza la lectura en tiempo real del estado de compra
    current_time = time.time()
    session_active = VOLATILE_KERNEL.get("session_active", False)
    is_premium = VOLATILE_KERNEL.get("is_premium", False)
    expires_at = VOLATILE_KERNEL.get("expires_at", 0.0)
    
    # Si está activo y es Premium de 30 días, o si el pase de 10 minutos sigue vigente
    if session_active and (is_premium or current_time <= expires_at):
        time_left = max(0, int(expires_at - current_time)) if not is_premium else 2592000
        return {
            "active": True,
            "is_premium": is_premium,
            "time_left": time_left
        }
    
    # Asegura la limpieza total de estados si expiró el tiempo del pase corto o no hay pago válido
    VOLATILE_KERNEL["session_active"] = False
    VOLATILE_KERNEL["is_premium"] = False
    VOLATILE_KERNEL["expires_at"] = 0.0
    return {"active": False, "is_premium": False, "time_left": 0}

# =====================================================================
# Endpoints Protegidos de la Aplicación (Requieren verify_active_session)
# =====================================================================

@app.post("/api/chat", dependencies=[Depends(verify_active_session)])
async def process_chat_directive(req: ChatRequest):
    if req.messages:
        VOLATILE_KERNEL["last_directive"] = req.messages[-1].content
    
    system_prompt = (
        "Eres un asesor experto de bienestar y estilo de vida. Mantén el hilo de la conversación, sé conciso, directo, empático y guía al usuario paso a paso sin perder la coherencia de las preguntas anteriores."
        if req.lang == "es"
        else "You are an expert wellness and lifestyle advisor. Maintain the conversation thread, be concise, direct, empathetic, and guide the user step-by-step without losing coherence from previous questions."
    )
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Intento primario con Gemini
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
                
        except Exception:
            # Conmutación de contingencia automática a OpenAI
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
            except Exception:
                raise HTTPException(status_code=500, detail="No se pudo procesar la respuesta con el motor de asesoría.")

@app.post("/api/wellness", dependencies=[Depends(verify_active_session)])
async def process_wellness_routine(req: WellnessRequest):
    return {
        "status": "active",
        "objective": req.objective,
        "rhythm": "synchronized",
        "message": "Volatile anti-stress routine initiated."
    }

@app.delete("/api/clear")
async def clear_kernel_memory():
    VOLATILE_KERNEL["session_active"] = False
    VOLATILE_KERNEL["expires_at"] = 0.0
    VOLATILE_KERNEL["last_directive"] = None
    return {"status": "cleared", "memory": "zero"}

# Montaje de la carpeta estática para servir el frontend
if os.path.exists("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
