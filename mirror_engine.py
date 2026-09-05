import os,hmac,secrets,sqlite3,stripe,httpx
from datetime import datetime,timezone,timedelta
from typing import List,Optional
from fastapi import FastAPI,HTTPException,Request,Cookie
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app=FastAPI(title="MIRROR TO YOU",version="2.2.0")

# ========================= CONFIG =========================

OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY=os.getenv("GEMINI_API_KEY")
STRIPE_SECRET_KEY=os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET=os.getenv("STRIPE_WEBHOOK_SECRET")
STRIPE_PRICE_ID1=os.getenv("STRIPE_PRICE_ID1") # $200
STRIPE_PRICE_ID2=os.getenv("STRIPE_PRICE_ID2") # $499
STRIPE_PUBLISHABLE_KEY=os.getenv("STRIPE_PUBLISHABLE_KEY")
ADMIN_USERNAME=os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD=os.getenv("ADMIN_PASSWORD")
APP_BASE_URL=os.getenv("APP_BASE_URL","https://mirror-to-you.onrender.com").rstrip("/")
DATABASE_PATH=os.getenv("MIRROR_DATABASE_PATH","mirror_to_you.db")

if STRIPE_SECRET_KEY: stripe.api_key=STRIPE_SECRET_KEY

VOLATILE_KERNEL={}

# ========================= DATABASE =========================

def db():
    x=sqlite3.connect(DATABASE_PATH,check_same_thread=False)
    x.row_factory=sqlite3.Row
    return x

def init_db():
    x=db()
    x.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        stripe_customer_id TEXT,
        subscription_id TEXT,
        subscription_status TEXT,
        one_time_services INTEGER NOT NULL DEFAULT 0,
        admin_access INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL)""")
    x.execute("""CREATE TABLE IF NOT EXISTS sessions(
        token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        expires_at TEXT NOT NULL,
        created_at TEXT NOT NULL)""")
    x.execute("""CREATE TABLE IF NOT EXISTS stripe_events(
        event_id TEXT PRIMARY KEY,
        event_type TEXT NOT NULL,
        created_at TEXT NOT NULL)""")
    x.commit();x.close()

init_db()

def now(): return datetime.now(timezone.utc).isoformat()

# ========================= USERS =========================

def user_id(uid):
    x=db();r=x.execute("SELECT * FROM users WHERE id=?",(uid,)).fetchone();x.close();return r

def user_email(email):
    if not email:return None
    x=db();r=x.execute("SELECT * FROM users WHERE email=?",(email.strip().lower(),)).fetchone();x.close();return r

def make_user(email,customer=None):
    email=email.strip().lower();t=now();x=db()
    r=x.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone()
    if r:
        x.execute("""UPDATE users SET stripe_customer_id=COALESCE(?,stripe_customer_id),
        updated_at=? WHERE id=?""",(customer,t,r["id"]))
    else:
        x.execute("""INSERT INTO users(email,stripe_customer_id,created_at,updated_at)
        VALUES(?,?,?,?)""",(email,customer,t,t))
    x.commit();r=x.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone();x.close();return r

def active_subscription(u):
    return u and u["subscription_status"] in ("active","trialing")

def access(u):
    if not u:return "none"
    if u["admin_access"]:return "admin"
    if active_subscription(u):return "subscription"
    if int(u["one_time_services"] or 0)>0:return "one_time"
    return "none"

def has_access(u): return access(u)!="none"

# ========================= SESSIONS =========================

def new_session(uid):
    token=secrets.token_urlsafe(48)
    exp=(datetime.now(timezone.utc)+timedelta(days=30)).isoformat()
    x=db();x.execute("INSERT INTO sessions VALUES(?,?,?,?)",(token,uid,exp,now()));x.commit();x.close()
    return token

def session_user(token):
    if not token:return None
    x=db();s=x.execute("SELECT * FROM sessions WHERE token=?",(token,)).fetchone()
    if not s:
        x.close();return None
    try:expired=datetime.fromisoformat(s["expires_at"])<=datetime.now(timezone.utc)
    except:expired=True
    if expired:
        x.execute("DELETE FROM sessions WHERE token=?",(token,));x.commit();x.close();return None
    u=x.execute("SELECT * FROM users WHERE id=?",(s["user_id"],)).fetchone();x.close()
    return u

def delete_session(token):
    if token:
        x=db();x.execute("DELETE FROM sessions WHERE token=?",(token,));x.commit();x.close()

def cookie(response,token):
    response.set_cookie("mirror_session",token,httponly=True,secure=True,
                        samesite="lax",max_age=2592000,path="/")

# ========================= MODELS =========================

class Message(BaseModel):
    role:str
    content:str

class ChatRequest(BaseModel):
    messages:List[Message]
    lang:str="en"

class WellnessRequest(BaseModel):
    objective:str
    duration_seconds:int=60

class CheckoutRequest(BaseModel):
    plan:str

class AdminLoginRequest(BaseModel):
    username:str
    password:str

# ========================= ADMIN =========================

@app.post("/api/admin/login")
async def admin_login(r:AdminLoginRequest):
    if not ADMIN_USERNAME or not ADMIN_PASSWORD:
        raise HTTPException(503,"Acceso administrativo no configurado.")
    if not hmac.compare_digest(r.username,ADMIN_USERNAME) or not hmac.compare_digest(r.password,ADMIN_PASSWORD):
        raise HTTPException(401,"Usuario o contraseña incorrectos.")
    u=user_email("admin@mirror-to-you.local") or make_user("admin@mirror-to-you.local")
    x=db();x.execute("UPDATE users SET admin_access=1,updated_at=? WHERE id=?",(now(),u["id"]));x.commit();x.close()
    t=new_session(u["id"]);res=JSONResponse({"status":"authenticated","access":"admin","has_access":True,"unlimited":True});cookie(res,t);return res

@app.post("/api/admin/logout")
async def admin_logout(mirror_session:Optional[str]=Cookie(None)):
    delete_session(mirror_session);r=JSONResponse({"status":"logged_out"});r.delete_cookie("mirror_session",path="/");return r

# ========================= ACCESS =========================

@app.get("/api/access/status")
async def access_status(mirror_session:Optional[str]=Cookie(None)):
    u=session_user(mirror_session)
    if not u:return {"authenticated":False,"has_access":False,"access":"none","one_time_services":0,"subscription_status":None}
    return {"authenticated":True,"has_access":has_access(u),"access":access(u),
            "one_time_services":int(u["one_time_services"] or 0),
            "subscription_status":u["subscription_status"],
            "email":None if access(u)=="admin" else u["email"]}

# ========================= STRIPE CHECKOUT =========================

@app.post("/api/create-checkout-session")
async def checkout(r:CheckoutRequest):
    if not STRIPE_SECRET_KEY or not STRIPE_PRICE_ID1 or not STRIPE_PRICE_ID2:
        raise HTTPException(503,"Stripe no está completamente configurado.")
    plan=r.plan.strip().lower()
    if plan not in ("one_time","subscription"):
        raise HTTPException(400,"Plan no válido.")
    price=STRIPE_PRICE_ID1 if plan=="one_time" else STRIPE_PRICE_ID2
    mode="payment" if plan=="one_time" else "subscription"
    try:
        p={"mode":mode,"line_items":[{"price":price,"quantity":1}],
           "success_url":f"{APP_BASE_URL}/?payment=success&session_id={{CHECKOUT_SESSION_ID}}",
           "cancel_url":f"{APP_BASE_URL}/?payment=cancelled",
           "billing_address_collection":"auto",
           "allow_promotion_codes":True,
           "metadata":{"mirror_plan":plan}}
        if mode=="subscription":p["subscription_data"]={"metadata":{"mirror_plan":"subscription"}}
        s=stripe.checkout.Session.create(**p)
        return {"status":"created","session_id":s.id,"checkout_url":s.url,"plan":plan}
    except stripe.error.StripeError as e:
        raise HTTPException(500,f"No se pudo crear el pago: {e}")

# ========================= WEBHOOK =========================

@app.post("/stripe-webhook")
async def webhook(request:Request):
    if not STRIPE_WEBHOOK_SECRET:raise HTTPException(503,"Webhook no configurado.")
    payload=await request.body();sig=request.headers.get("stripe-signature")
    if not sig:raise HTTPException(400,"Firma Stripe ausente.")
    try:e=stripe.Webhook.construct_event(payload,sig,STRIPE_WEBHOOK_SECRET)
    except ValueError:raise HTTPException(400,"Payload Stripe inválido.")
    except stripe.error.SignatureVerificationError:raise HTTPException(400,"Firma Stripe inválida.")

    eid,typ=e["id"],e["type"];x=db()
    if x.execute("SELECT event_id FROM stripe_events WHERE event_id=?",(eid,)).fetchone():
        x.close();return {"status":"already_processed"}
    x.execute("INSERT INTO stripe_events VALUES(?,?,?)",(eid,typ,now()));x.commit();x.close()

    o=e["data"]["object"]

    if typ=="checkout.session.completed":
        customer=o.get("customer");details=o.get("customer_details") or {};email=details.get("email")
        if not email and customer:
            try:email=stripe.Customer.retrieve(customer).get("email")
            except:email=None
        if email:
            u=make_user(email,customer);plan=(o.get("metadata") or {}).get("mirror_plan")
            if plan=="one_time" and o.get("payment_status")=="paid":
                x=db();x.execute("UPDATE users SET one_time_services=one_time_services+1,updated_at=? WHERE id=?",(now(),u["id"]));x.commit();x.close()
            elif plan=="subscription":
                sid=o.get("subscription");status="active"
                if sid:
                    try:status=stripe.Subscription.retrieve(sid).get("status") or "active"
                    except:pass
                x=db();x.execute("""UPDATE users SET subscription_id=?,subscription_status=?,
                stripe_customer_id=?,updated_at=? WHERE id=?""",(sid,status,customer,now(),u["id"]));x.commit();x.close()

    elif typ=="invoice.paid":
        cid=o.get("customer");sid=o.get("subscription")
        if cid:
            x=db();x.execute("""UPDATE users SET subscription_id=COALESCE(?,subscription_id),
            subscription_status='active',updated_at=? WHERE stripe_customer_id=?""",(sid,now(),cid));x.commit();x.close()

    elif typ=="invoice.payment_failed":
        cid=o.get("customer")
        if cid:
            x=db();x.execute("UPDATE users SET subscription_status='past_due',updated_at=? WHERE stripe_customer_id=?",(now(),cid));x.commit();x.close()

    elif typ=="customer.subscription.updated":
        cid=o.get("customer")
        x=db();x.execute("""UPDATE users SET subscription_id=?,subscription_status=?,updated_at=?
        WHERE stripe_customer_id=?""",(o.get("id"),o.get("status"),now(),cid));x.commit();x.close()

    elif typ=="customer.subscription.deleted":
        cid=o.get("customer")
        x=db();x.execute("UPDATE users SET subscription_status='canceled',updated_at=? WHERE stripe_customer_id=?",(now(),cid));x.commit();x.close()

    return {"status":"received"}

# ========================= PAYMENT ACTIVATION =========================

@app.post("/api/payment/activate")
async def activate(session_id:str):
    if not STRIPE_SECRET_KEY:raise HTTPException(503,"Stripe no configurado.")
    try:s=stripe.checkout.Session.retrieve(session_id)
    except stripe.error.StripeError:raise HTTPException(400,"No se pudo verificar Stripe.")
    if s.get("status")!="complete":raise HTTPException(402,"Checkout no completado.")

    details=s.get("customer_details") or {};email=details.get("email");cid=s.get("customer")
    if not email and cid:
        try:email=stripe.Customer.retrieve(cid).get("email")
        except:email=None
    if not email:raise HTTPException(400,"No se pudo identificar al cliente.")

    try:items=stripe.checkout.Session.list_line_items(session_id,limit=10)
    except stripe.error.StripeError:raise HTTPException(400,"No se pudieron verificar los artículos.")

    valid=None
    for item in items.data:
        pid=(item.get("price") or {}).get("id")
        if pid in (STRIPE_PRICE_ID1,STRIPE_PRICE_ID2):valid=pid;break
    if not valid:raise HTTPException(400,"El pago no corresponde a un plan válido.")

    u=make_user(email,cid)

    if valid==STRIPE_PRICE_ID1:
        if s.get("payment_status")!="paid":raise HTTPException(402,"El pago de $200 no está confirmado.")
        if int(u["one_time_services"] or 0)<=0:
            raise HTTPException(409,"Pago confirmado; esperando confirmación del webhook.")
        t=new_session(u["id"]);res=JSONResponse({"status":"active","access":"one_time","has_access":True,
            "one_time_services":int(u["one_time_services"])});cookie(res,t);return res

    sid=s.get("subscription")
    if not sid:raise HTTPException(402,"No se encontró la suscripción.")
    try:sub=stripe.Subscription.retrieve(sid);status=sub.get("status")
    except stripe.error.StripeError:raise HTTPException(400,"No se pudo verificar la suscripción.")
    if status not in ("active","trialing"):raise HTTPException(402,"La suscripción no está activa.")

    x=db();x.execute("""UPDATE users SET stripe_customer_id=?,subscription_id=?,
    subscription_status=?,updated_at=? WHERE id=?""",(cid,sid,status,now(),u["id"]));x.commit();x.close()
    t=new_session(u["id"]);res=JSONResponse({"status":"active","access":"subscription","has_access":True,"subscription_status":status});cookie(res,t);return res

# ========================= PAYMENT STATUS =========================

@app.get("/api/payment-status")
async def payment_status(session_id:Optional[str]=None,mirror_session:Optional[str]=Cookie(None)):
    u=session_user(mirror_session)
    if u and has_access(u):return {"confirmed":True,"has_access":True,"access":access(u)}
    if not session_id or not STRIPE_SECRET_KEY:return {"confirmed":False,"has_access":False,"access":"none"}
    try:
        s=stripe.checkout.Session.retrieve(session_id)
        return {"confirmed":s.get("status")=="complete","payment_status":s.get("payment_status"),"subscription":s.get("subscription")}
    except stripe.error.StripeError:return {"confirmed":False,"has_access":False,"access":"none"}

# ========================= SERVICE =========================

@app.post("/api/service/start")
async def start_service(mirror_session:Optional[str]=Cookie(None)):
    u=session_user(mirror_session)
    if not u:raise HTTPException(401,"Debes tener acceso al servicio.")
    a=access(u)
    if a in ("admin","subscription"):return {"authorized":True,"access":a,"service_remaining":"unlimited"}
    x=db();c=x.execute("""UPDATE users SET one_time_services=one_time_services-1,
    updated_at=? WHERE id=? AND one_time_services>0""",(now(),u["id"]))
    if c.rowcount!=1:x.rollback();x.close();raise HTTPException(403,"No tienes un servicio disponible.")
    r=x.execute("SELECT one_time_services FROM users WHERE id=?",(u["id"],)).fetchone()
    x.commit();x.close()
    return {"authorized":True,"access":"one_time","service_remaining":int(r["one_time_services"])}

# ========================= AI CHAT =========================

@app.post("/api/chat")
async def chat(r:ChatRequest,mirror_session:Optional[str]=Cookie(None)):
    u=session_user(mirror_session)
    if not u or not has_access(u):raise HTTPException(403,"Acceso requerido.")
    if r.messages:VOLATILE_KERNEL["last_directive"]=r.messages[-1].content
    prompt=("Eres un asesor experto de bienestar y estilo de vida. Mantén el hilo, sé conciso, directo, "
            "empático y guía paso a paso. No presentes tus respuestas como diagnóstico médico."
            if r.lang=="es" else
            "You are an expert wellness and lifestyle advisor. Maintain context, be concise, direct and "
            "empathetic. Guide the user step by step. Do not present responses as medical diagnosis.")
    async with httpx.AsyncClient(timeout=30) as c:
        if GEMINI_API_KEY:
            try:
                contents=[{"role":"user" if m.role=="user" else "model","parts":[{"text":m.content}]} for m in r.messages]
                url=f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
                z=await c.post(url,json={"system_instruction":{"parts":[{"text":prompt}]},"contents":contents})
                if z.status_code==200:
                    d=z.json();p=d.get("candidates",[{}])[0].get("content",{}).get("parts",[{}])[0].get("text")
                    if p:return {"reply":p,"provider":"gemini"}
            except:pass
        if OPENAI_API_KEY:
            try:
                msgs=[{"role":"system","content":prompt}]+[
                    {"role":m.role if m.role in ("user","assistant","system") else "user","content":m.content} for m in r.messages]
                z=await c.post("https://api.openai.com/v1/chat/completions",
                    json={"model":"gpt-4o-mini","messages":msgs,"temperature":.7},
                    headers={"Authorization":f"Bearer {OPENAI_API_KEY}","Content-Type":"application/json"})
                if z.status_code==200:
                    p=z.json().get("choices",[{}])[0].get("message",{}).get("content")
                    if p:return {"reply":p,"provider":"openai"}
            except:pass
    raise HTTPException(500,"No se pudo procesar la respuesta.")

# ========================= WELLNESS =========================

@app.post("/api/wellness")
async def wellness(r:WellnessRequest,mirror_session:Optional[str]=Cookie(None)):
    u=session_user(mirror_session)
    if not u or not has_access(u):raise HTTPException(403,"Acceso requerido.")
    if not 1<=r.duration_seconds<=600:raise HTTPException(400,"La duración debe estar entre 1 y 600 segundos.")
    return {"status":"active","objective":r.objective,"duration_seconds":r.duration_seconds,"rhythm":"synchronized"}

# ========================= CLEAR =========================

@app.delete("/api/clear")
async def clear(mirror_session:Optional[str]=Cookie(None)):
    if not session_user(mirror_session):raise HTTPException(401,"Acceso requerido.")
    VOLATILE_KERNEL.clear()
    return {"status":"cleared","memory":"zero"}

# ========================= STRIPE CONFIG =========================

@app.get("/api/stripe/config")
async def stripe_config():
    return {"publishable_key":STRIPE_PUBLISHABLE_KEY,
            "plans":{
                "one_time":{"amount":200,"currency":"usd","type":"one_time","description":"1 servicio","price_id":STRIPE_PRICE_ID1},
                "subscription":{"amount":499,"currency":"usd","type":"subscription","description":"Uso ilimitado mientras esté activa","price_id":STRIPE_PRICE_ID2}}}

# ========================= HEALTH =========================

@app.get("/api/health")
async def health():
    return {"status":"ok","app":"MIRROR TO YOU","version":"2.2.0",
            "stripe":bool(STRIPE_SECRET_KEY),
            "stripe_prices":bool(STRIPE_PRICE_ID1 and STRIPE_PRICE_ID2),
            "stripe_webhook":bool(STRIPE_WEBHOOK_SECRET),
            "gemini":bool(GEMINI_API_KEY),"openai":bool(OPENAI_API_KEY),
            "admin":bool(ADMIN_USERNAME and ADMIN_PASSWORD)}

# ========================= CLEANUP =========================

@app.post("/api/maintenance/cleanup-sessions")
async def cleanup_sessions():
    x=db();c=x.execute("DELETE FROM sessions WHERE expires_at<=?",(now(),));x.commit();x.close()
    return {"status":"cleaned","deleted_sessions":c.rowcount}

# ========================= STATIC =========================

if os.path.exists("static"):
    app.mount("/",StaticFiles(directory="static",html=True),name="static")
