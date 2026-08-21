# ====================================================================================================
#                                         MAY ROGA LLC
#                       Wellness Travel Architecture & Lifestyle Optimization
#                                    Miami, Florida | USA
#                                 PRODUCTION BACKEND - AUDITED
# ====================================================================================================

import os
import json
import stripe
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

app = FastAPI(
    title="MAY ROGA LLC - Wellness Travel App Production Backend",
    version="1.0.0"
)

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Inicialización segura de Stripe leyendo las variables de entorno de Render
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PRICE_ID1 = os.getenv("STRIPE_PRICE_ID1")  # ID de precio para el plan de $200
STRIPE_PRICE_ID2 = os.getenv("STRIPE_PRICE_ID2")  # ID de precio para el plan de $399

DICTIONARY_BILINGUAL = {
    "ES": {
        "doc_title": "LIBRETA DE VIAJE INDIVIDUAL (PRÁCTICA Y PRIVADA)",
        "folio": "Folio de Acompañamiento",
        "status": "Estatus: Completado Localmente",
        "sec1_title": "1. BALANCE Y AVANCE DE ENFOQUE PERSONAL",
        "m1": "Indicador Evaluado", "m2": "Nivel Inicial", "m3": "Nivel de Cierre",
        "m_pace": "Índice de Fatiga por Rutina",
        "m_breathe": "Calibración por Respiración",
        "m_logic": "Agilidad del Enfoque Lógico",
        "sec2_title": "2. ENRUTAMIENTO EXCLUSIVO DE VIAJE (HOST AGENCY GATEWAY)",
        "stay_lbl": "Santuario Recomendado",
        "desc_lbl": "Detalle del Espacio",
        "air_lbl": "Logística del Aire",
        "sea_lbl": "Pasillo Marítimo",
        "consorcio": "Beneficios Exclusivos Consorcio: Acceso preferencial a créditos de cortesía Virtuoso ($100 para spa y mejoras de habitación de forma automática mediante tu folio).",
        "sec3_title": "3. ÁREAS DE ENFOQUE RECOMENDADAS",
        "cta": "Este reporte es estrictamente práctico y confidencial. Se enfoca en medir si tu sistema cerebral logró mejoría o si debes trabajar más en el desapego a la fatiga rutinaria.",
        "sec4_title": "4. PRIVACIDAD TOTAL MAY ROGA LLC",
        "disclaimer": "Toda la información recopilada para generar esta libreta de viaje se procesa de forma estrictamente local y anónima en el dispositivo del usuario (localStorage). El usuario asume total control sobre sus elecciones de viaje.",
        "ai_foot": "Este documento es para fines informativos y promocionales de viajes de lujo. Para asesoramiento profesional, consulte a un especialista certificado."
    },
    "EN": {
        "doc_title": "PERSONAL TRAVEL PASSPORT (CONFIDENTIAL OVERVIEW)",
        "folio": "Service ID Folio",
        "status": "Status: Locally Processed",
        "sec1_title": "1. WELLNESS BALANCE & ENHANCEMENT SUMMARY",
        "m1": "Wellness Metric Evaluated", "m2": "Initial Baseline", "m3": "Closing Balance",
        "m_pace": "Routine Friction & Pace Index",
        "m_breathe": "Breathing Calibration Rate",
        "m_logic": "Focus Clarity & Logic Rate",
        "sec2_title": "2. YOUR EXCLUSIVE TRAVEL ROUTING (HOST AGENCY GATEWAY)",
        "stay_lbl": "Curated Luxury Oasis",
        "desc_lbl": "Wellness Profile Detail",
        "air_lbl": "Premium Air Logistics",
        "sea_lbl": "Maritime Cruise Corridor",
        "consorcio": "Exclusive Consortium Privileges: Eligible for complimentary Virtuoso/Signature luxury benefits ($100 resort credits for relaxation therapies and priority room upgrades processed automatically via credentials).",
        "sec3_title": "3. SUGGESTED ACTIONABLE FOCUS POINTS",
        "cta": "This report serves as a concise summary of your progress. It benchmarks your clarity index and outlines whether your cognitive system achieved optimization or requires additional technical boundaries against routine exhaustion.",
        "sec4_title": "4. CORPORATE LIFESTYLE PRIVACY ASSURANCE",
        "disclaimer": "All digital metrics gathered to compile this travel passport are processed strictly locally and anonymously on the user's browser terminal via local behavior algorithms (localStorage).",
        "ai_foot": "This document is for informational and promotional travel purposes only. For clinical or medical advice, consult a certified healthcare professional."
    }
}

BACKEND_HOTELES = {
    "H1": {
        "es": {"name": "Eden Roc Cap Cana (República Dominicana)", "desc": "Bungalows de ultra-lujo con alberca propia, jardín privado y aislamiento acústico absoluto."},
        "en": {"name": "Eden Roc Cap Cana (Dominican Republic)", "desc": "Ultra-luxury standalone bungalows with private pools, zen gardens, and total acoustic insulation."}
    },
    "H2": {
        "es": {"name": "Amanera Resort (Playa Grande)", "desc": "Casitas de cristal y ebanistería minimalista suspendidas sobre acantilados masivos frente al mar."},
        "en": {"name": "Amanera Resort (Playa Grande)", "desc": "Minimalist glass casitas perched on massive ocean cliffs blending with pure Caribbean jungle."}
    },
    "H3": {
        "es": {"name": "Grand Velas Riviera Maya (México)", "desc": "Suites de alta gama acompañadas de un circuito hidrotermal de spa guiado de 7 etapas perfectas."},
        "en": {"name": "Grand Velas Riviera Maya (Mexico)", "desc": "Upscale beachfront suites paired with an immersive 7-stage guided hydrothermal spa circuit."}
    }
}

BACKEND_LOGISTICA = {
    "ELITE": {
        "es": {
            "air": "Gulfstream G650 Chárter Privado directo sin filas desde la terminal VIP FBO de Miami.",
            "sea": "The Ritz-Carlton Yacht Collection Suite de popa con terraza privada sobre el océano."
        },
        "en": {
            "air": "Private Aviation Charter (Gulfstream G650) flying direct from Miami's VIP FBO private terminal.",
            "sea": "The Ritz-Carlton Yacht Collection ultra-luxury terrace suite with private ocean overviews."
        }
    },
    "PREMIUM": {
        "es": {
            "air": "Clase Ejecutiva Flagship Suite con asientos Lie-Flat totalmente reclinables en vuelo directo.",
            "sea": "Celebrity Cruises (The Retreat Enclave) con solárium y restaurante de autor VIP."
        },
        "en": {
            "air": "Flagship Business Class Non-Stop Suite configured with fully reclinable Lie-Flat premium seating.",
            "sea": "Celebrity Cruises (The Retreat Private Enclave) granting VIP sundeck access and fine dining."
        }
    }
}

class PDFPayload(BaseModel):
    servicio_id: str
    lang: str
    score_inicial: float
    score_actual: float
    respiracion_score: float
    adivinanzas_score: float
    iev: float
    variante: str
    destino_id: str

class CheckoutPayload(BaseModel):
    tier: str
    folio: str

# ==================================================================================== 
# ACTUALIZACIÓN INTEGRADA: ENDPOINT DE VALIDACIÓN DE CREDENCIALES (DEV VARIABLES) 
# ==================================================================================== 
class DevAuthPayload(BaseModel):
    user: str
    dev_pass: str  # CORREGIDO: Cambiado de 'pass' a 'dev_pass' para evitar el SyntaxError

@app.post("/verify-dev-access")
def verify_dev_access(payload: DevAuthPayload):
    system_dev_user = os.getenv("DEV_USER")
    system_dev_pass = os.getenv("DEV_PASS")
    
    if payload.user == system_dev_user and payload.dev_pass == system_dev_pass:
        return {"authenticated": True}
    
    raise HTTPException(status_code=401, detail="Unauthorized developer credentials.")

@app.post("/create-checkout-session")
def create_checkout_session(payload: CheckoutPayload):
    # Asignación segura del Price ID configurado en las variables de Render
    price_id = STRIPE_PRICE_ID1 if payload.tier == "SINGLE_200" else STRIPE_PRICE_ID2
    
    if not price_id:
        raise HTTPException(status_code=500, detail="Falta la configuración del Price ID de Stripe en Render.")

    try:
        # Generación de la sesión de checkout blindada en servidores de Stripe
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='payment' if payload.tier == "SINGLE_200" else 'subscription',
            # Redirección automática de regreso a tu dominio de Wellness-Travel-
            success_url=f"https://wellness-travel.onrender.com{payload.folio}",
            cancel_url="https://wellness-travel.onrender.com",
            metadata={
                'folio_crm': payload.folio,
                'billing_tier': payload.tier
            }
        )
        return {"checkout_url": checkout_session.url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/generate-pdf")
def generate_pdf(payload: PDFPayload):
    pdf_filename = f"report_{payload.servicio_id}.pdf"
    pdf_path = os.path.join("temp", pdf_filename)
    os.makedirs("temp", exist_ok=True)
    
    doc = SimpleDocTemplate(
        pdf_path, pagesize=letter,
        rightMargin=45, leftMargin=45, topMargin=45, bottomMargin=45,
        title=f"Report {payload.servicio_id}"
    )
    styles = getSampleStyleSheet()
    
    color_primary = colors.HexColor("#1A1A1A")   
    color_gold = colors.HexColor("#A3704C")      
    color_text = colors.HexColor("#333333")      
    color_legal = colors.HexColor("#777777")     
    
    title_style = ParagraphStyle('CorpTitle', parent=styles['Heading1'], fontSize=26, leading=30, textColor=color_primary, alignment=1)
    subtitle_style = ParagraphStyle('CorpSub', parent=styles['Normal'], fontSize=9, leading=13, textColor=color_legal, alignment=1)
    h2_style = ParagraphStyle('SectionHeader', parent=styles['Heading2'], fontSize=12, leading=16, textColor=color_gold, spaceBefore=18, spaceAfter=8)
    body_style = ParagraphStyle('CorpBody', parent=styles['Normal'], fontSize=10, leading=14, textColor=color_text)
    disclaimer_style = ParagraphStyle('LegalText', parent=styles['Normal'], fontSize=7.5, leading=10.5, textColor=color_legal, alignment=4)
    
    # Bloque interno de generate_pdf: Asegurar 4 espacios de sangría al inicio de cada línea
    story = [] 
    lang_key = "EN" if payload.lang.upper() == "EN" else "ES" 
    lang_map = DICTIONARY_BILINGUAL[lang_key] 
    
    story.append(Paragraph("<b>MAY ROGA LLC</b>", title_style)) 
    story.append(Paragraph("Wellness Travel Architecture & Lifestyle Optimization<br/>Miami, Florida | USA", subtitle_style)) 
    story.append(Spacer(1, 15)) 
    
    story.append(Paragraph(f"<b>{lang_map['doc_title']}</b>", ParagraphStyle('RepTitle', parent=styles['Heading3'], fontSize=11, leading=14, alignment=1, textColor=color_primary, spaceAfter=15))) 
    
    meta_text = f"<b>{lang_map['folio']}:</b> {payload.servicio_id} | <b>{lang_map['status']}</b>"
    story.append(Paragraph(meta_text, body_style)) 
    story.append(Spacer(1, 12)) 
    
    story.append(Paragraph(lang_map['sec1_title'], h2_style)) 
    
    metrics_data = [ 
        [Paragraph(f"<b>{lang_map['m1']}</b>", body_style), Paragraph(f"<b>{lang_map['m2']}</b>", body_style), Paragraph(f"<b>{lang_map['m3']}</b>", body_style)], 
        [Paragraph(lang_map['m_pace'], body_style), f"{payload.score_inicial}%", f"{payload.score_actual}%"], 
        [Paragraph(lang_map['m_breathe'], body_style), "0%", f"{payload.respiracion_score}%"], 
        [Paragraph(lang_map['m_logic'], body_style), "0%", f"{payload.adivinanzas_score}%"] 
    ] 
    
    metrics_table = Table(metrics_data, colWidths=[240, 140, 142]) 
    metrics_table.setStyle(TableStyle([ 
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F9F9F9")), 
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E5E5")), 
        ('PADDING', (0, 0), (-1, -1), 6), 
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'), 
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), 
    ])) 
    story.append(metrics_table) 
    story.append(Spacer(1, 12)) 
    
    story.append(Paragraph(lang_map['sec2_title'], h2_style)) 
    
    hotel_id = payload.destino_id 
    if hotel_id in BACKEND_HOTELES: 
        h_name = BACKEND_HOTELES[hotel_id][lang_key.lower()]["name"] 
        h_desc = BACKEND_HOTELES[hotel_id][lang_key.lower()]["desc"] 
    else: 
        h_name = "Eden Roc Cap Cana (Punta Cana)" 
        h_desc = "Villas de ultra-lujo con alberca propia y aislamiento acústico absoluto." 
        
    tier_key = "ELITE" if "ELITE" in payload.variante or payload.score_inicial < 45 else "PREMIUM" 
    logistica = BACKEND_LOGISTICA.get(tier_key, BACKEND_LOGISTICA["ELITE"])[lang_key.lower()] 
    
    dest_html = f"• <b>{lang_map['stay_lbl']}</b>: {h_name}<br/>" 
    dest_html += f"• <b>{lang_map['desc_lbl']}</b>: {h_desc}<br/>" 
    dest_html += f"• <b>{lang_map['air_lbl']}</b>: {logistica['air']}<br/>" 
    dest_html += f"• <b>{lang_map['sea_lbl']}</b>: {logistica['sea']}<br/><br/>" 
    dest_html += f"<i>{lang_map['consorcio']}</i>" 
    
    story.append(Paragraph(dest_html, body_style)) 
    story.append(Spacer(1, 15)) 
    
    story.append(Paragraph(lang_map['sec3_title'], h2_style)) 
    story.append(Paragraph(lang_map['cta'], body_style)) 
    story.append(Spacer(1, 15)) 
    
    story.append(Paragraph(lang_map['sec4_title'], h2_style)) 
    story.append(Paragraph(lang_map['disclaimer'], disclaimer_style)) 
    story.append(Spacer(1, 10)) 
    story.append(Paragraph(lang_map['ai_foot'], disclaimer_style)) 
    
    doc.build(story) 
    return FileResponse(pdf_path, media_type='application/pdf', filename=pdf_filename)

# ==================================================================================== 
# SERVIDOR EN ENTRADA RAÍZ (Al ras del margen izquierdo externo, con 0 espacios)
# ==================================================================================== 
@app.get("/", response_class=HTMLResponse) 
def read_index(): 
    return "<h3>MAY ROGA LLC - Production Backend Operational</h3>"
