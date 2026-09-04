import os
import httpx
import stripe
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List

app = FastAPI(title="MIRROR TO YOU", version="2.1.0")

VOLATILE_KERNEL = {}

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PRICE_ID1 = os.getenv("STRIPE_PRICE_ID1")
STRIPE_PRICE_ID2 = os.getenv("STRIPE_PRICE_ID2")

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

APP_URL = os.getenv("APP_URL", "https://mirror-to-you.onrender.com")

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
    price_type: str

class LoginRequest(BaseModel):
    username: str
    password: str

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "stripe": bool(stripe.api_key),
        "price1": bool(STRIPE_PRICE_ID1),
        "price2": bool(STRIPE_PRICE_ID2),
        "admin": bool(ADMIN_USERNAME and ADMIN_PASSWORD)
    }

@app.post("/api/create-checkout-session")
async def create_checkout_session(req: CheckoutRequest):
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe is not configured.")

    prices = {
        "1": STRIPE_PRICE_ID1,
        "2": STRIPE_PRICE_ID2
    }

    price_id = prices.get(req.price_type)

    if not price_id:
        raise HTTPException(status_code=400, detail="Invalid or unconfigured Price ID.")

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1
                }
            ],
            success_url=f"{APP_URL}/?payment=success&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{APP_URL}/?payment=cancelled"
        )

        return {
            "status": "created",
            "url": session.url,
            "session_id": session.id
        }

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to create Stripe checkout session."
        )

@app.get("/api/verify-payment")
async def verify_payment(session_id: str):
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe is not configured.")

    if not session_id:
        raise HTTPException(status_code=400, detail="Missing Stripe session ID.")

    try:
        session = stripe.checkout.Session.retrieve(session_id)

        paid = (
            session.payment_status == "paid"
            and session.status == "complete"
        )

        if not paid:
            return {
                "status": "pending",
                "paid": False
            }

        return {
            "status": "success",
            "paid": True,
            "session_id": session.id,
            "payment_status": session.payment_status
        }

    except stripe.error.StripeError:
        raise HTTPException(
            status_code=400,
            detail="Unable to verify Stripe payment."
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Payment verification failed."
        )

@app.post("/api/login")
async def handle_admin_login(req: LoginRequest):
    if not ADMIN_USERNAME or not ADMIN_PASSWORD:
        raise HTTPException(
            status_code=500,
            detail="Administrator credentials are not configured."
        )

    if req.username == ADMIN_USERNAME and req.password == ADMIN_PASSWORD:
        return {
            "status": "success",
            "access": "granted"
        }

    raise HTTPException(
        status_code=401,
        detail="Invalid username or password."
    )

@app.post("/api/chat")
async def process_chat_directive(req: ChatRequest):
    global VOLATILE_KERNEL

    if req.messages:
        VOLATILE_KERNEL["last_directive"] = req.messages[-1].content

    system_prompt = (
        "Eres un asesor experto de bienestar y estilo de vida. "
        "Mantén el hilo de la conversación, sé conciso, directo, "
        "empático y guía al usuario paso a paso sin perder la coherencia."
        if req.lang == "es"
        else
        "You are an expert wellness and lifestyle advisor. "
        "Maintain the conversation thread, be concise, direct, "
        "empathetic, and guide the user step-by-step."
    )

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            if not GEMINI_API_KEY:
                raise Exception("Gemini key unavailable.")

            contents = []

            for msg in req.messages:
                role = "user" if msg.role == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg.content}]
                })

            gemini_url = (
                "https://generativelanguage.googleapis.com/"
                "v1beta/models/gemini-2.5-flash:generateContent"
                f"?key={GEMINI_API_KEY}"
            )

            payload = {
                "system_instruction": {
                    "parts": [{"text": system_prompt}]
                },
                "contents": contents
            }

            response = await client.post(
                gemini_url,
                json=payload
            )

            if response.status_code == 200:
                data = response.json()
                reply = data["candidates"][0]["content"]["parts"][0]["text"]

                return {
                    "reply": reply,
                    "provider": "gemini"
                }

            raise Exception("Gemini unavailable.")

        except Exception:
            try:
                if not OPENAI_API_KEY:
                    raise Exception("OpenAI key unavailable.")

                messages = [
                    {
                        "role": "system",
                        "content": system_prompt
                    }
                ]

                for msg in req.messages:
                    messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })

                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    json={
                        "model": "gpt-4o-mini",
                        "messages": messages,
                        "temperature": 0.7
                    },
                    headers={
                        "Authorization": f"Bearer {OPENAI_API_KEY}",
                        "Content-Type": "application/json"
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    reply = data["choices"][0]["message"]["content"]

                    return {
                        "reply": reply,
                        "provider": "openai"
                    }

                raise Exception("OpenAI unavailable.")

            except Exception:
                raise HTTPException(
                    status_code=500,
                    detail="No se pudo procesar la respuesta con el motor de asesoría."
                )

@app.post("/api/wellness")
async def process_wellness_routine(req: WellnessRequest):
    return {
        "status": "active",
        "objective": req.objective,
        "duration_seconds": req.duration_seconds,
        "rhythm": "synchronized",
        "message": "Volatile anti-stress routine initiated."
    }

@app.delete("/api/clear")
async def clear_kernel_memory():
    global VOLATILE_KERNEL
    VOLATILE_KERNEL.clear()

    return {
        "status": "cleared",
        "memory": "zero"
    }

if os.path.exists("static"):
    app.mount(
        "/",
        StaticFiles(directory="static", html=True),
        name="static"
    )
