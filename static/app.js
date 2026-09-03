// static/app.js

let memory = { core: {}, moment: {}, preferences: {}, dislikes: [], history: [], learning: {} };
let currentLanguage = "es";
let currentResult = null;
let recognition = null;
let listening = false;

// Variables de control para el Círculo Respiratorio Profesional Variable
let breathingTimer = null;
let breathingSeconds = 240;
let breathingActive = false;

const $ = id => document.getElementById(id);

/**
 * Sincroniza los identificadores visuales bilingües basándose en la huella del dispositivo.
 * Mantiene la interfaz limpia de textos fijos e independientes para control absoluto de la IA.
 */
function applyInitialState(lang) {
    currentLanguage = lang;
    if (lang === "es") {
        $("sectionLabelState").textContent = "ESTADO DE EJECUCIÓN";
        $("lblPressureTitle").textContent = "Alta Presión";
        $("lblPressureSub").textContent = "Enfoque de Negocios";
        $("lblTransitionTitle").textContent = "Transición";
        $("lblTransitionSub").textContent = "Modo Familia";
        $("lblDisconnectTitle").textContent = "Desconexión";
        $("lblDisconnectSub").textContent = "Privacidad Total";
        $("messageInput").placeholder = "Romper monotonía, consultar o validar comando con MIRROR...";
        $("closeMemory").textContent = "← Volver";
        $("memoryTitle").textContent = "Ecosistema Confidencial & Patrones";
        $("clearMemoryButton").textContent = "Purgar Memoria Local";
        $("breathingControlBtn").textContent = "Iniciar Calibración";
    } else {
        $("sectionLabelState").textContent = "EXECUTION STATE";
        $("lblPressureTitle").textContent = "High Pressure";
        $("lblPressureSub").textContent = "Business Focus";
        $("lblTransitionTitle").textContent = "Transition";
        $("lblTransitionSub").textContent = "Family Mode";
        $("lblDisconnectTitle").textContent = "Disconnection";
        $("lblDisconnectSub").textContent = "Total Privacy";
        $("messageInput").placeholder = "Break monotony, query or validate command with MIRROR...";
        $("closeMemory").textContent = "← Back";
        $("memoryTitle").textContent = "Confidential Ecosystem & Patterns";
        $("clearMemoryButton").textContent = "Purge Local Context";
        $("breathingControlBtn").textContent = "Begin Calibration";
    }
}

function showDeck(id) {
    document.querySelectorAll(".deck").forEach(d => d.classList.remove("active"));
    const el = $(id);
    if (el) el.classList.add("active");
}

/**
 * MODO 1: Control de Estado de Un Solo Toque (Interfaz Primaria para el Cliente)
 */
async function executeState(stateType) {
    document.querySelectorAll(".state-card").forEach(c => c.classList.remove("active"));
    let cmd = "";
    if (stateType === "HIGH_PRESSURE") {
        $("btnStatePressure").classList.add("active");
        cmd = currentLanguage === "es" ? "CALIBRAR ENFOQUE DIRECTO ALTA PRESION CORPORATIVA" : "CALIBRATE EXECUTIVE HIGH BUSINESS PRESSURE STATE";
    } else if (stateType === "TRANSITION") {
        $("btnStateTransition").classList.add("active");
        cmd = currentLanguage === "es" ? "INICIAR TRANSICION FUERA DEL RADAR MODO FAMILIA" : "START FULL FAMILY MODE OFF THE RADAR TRANSITION";
    } else if (stateType === "DISCONNECT") {
        $("btnStateDisconnect").classList.add("active");
        cmd = currentLanguage === "es" ? "ELIMINAR MONOTONIA ABURRIMIENTO OCIO INTERACCION PREMIUM" : "DESTROY MONOTONY BOREDOM LEISURE HIGH SURPRISE PAUSE";
    }
    await requestEcosystemAPI(cmd);
}

/**
 * MODO 2: Interfaz Secundaria de Chat de Respaldo y Validación Conversacional
 */
async function askMirror() {
    const input = $("messageInput");
    const text = input.value.trim();
    if (!text) return;
    input.value = "";
    await requestEcosystemAPI(text);
}

/**
 * Despacho Unificado al Servidor FastAPI con la Huella del Dispositivo Encriptada
 */
async function requestEcosystemAPI(payloadText) {
    try {
        const response = await fetch("/api/mirror", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                message: payloadText, 
                language: currentLanguage, 
                device_id: localStorage.getItem("mirror_device_id") || "secure_vip_token", 
                memory: memory 
            })
        });
        const data = await response.json();
        if (data.ok) {
            memory = data.memory;
            currentResult = data.plan;
            currentLanguage = data.understanding.language || currentLanguage;
            applyInitialState(currentLanguage);
            renderEcosystem(data);
        }
    } catch (e) {
        console.error("Critical ecosystem connection anomaly.");
    }
}

/**
 * Renderizado Puro controlado en su totalidad por las variables del Backend de la IA
 */
function renderEcosystem(data) {
    const plan = data.plan;
    const badge = $("statusBadge");
    const zone = plan.status_color_zone || "GREEN";
    badge.className = "status-badge";
    
    // Zonas de color e identificación táctica de patrones de fatiga
    if (zone === "YELLOW") {
        badge.className = "status-badge zone-yellow";
        badge.textContent = currentLanguage === "es" ? "PATRÓN: ATENCIÓN" : "PATTERN: ATTENTION";
    } else if (zone === "RED") {
        badge.className = "status-badge zone-red";
        badge.textContent = currentLanguage === "es" ? "PATRÓN: RESGUARDO" : "PATTERN: PROTECTION";
    } else {
        badge.className = "status-badge zone-green";
        badge.textContent = currentLanguage === "es" ? "PATRÓN: CALIBRADO" : "PATTERN: BALANCED";
    }

    $("planTitle").textContent = plan.title || "MIRROR KERNEL";
    $("planReply").textContent = plan.reply || data.message;
    
    const dirBox = $("directions");
    dirBox.innerHTML = "";
    if (Array.isArray(plan.bullet_points)) {
        plan.bullet_points.forEach(text => {
            const el = document.createElement("div");
            el.className = "premium-direction-item";
            el.textContent = text;
            dirBox.appendChild(el);
        });
    }
    
    $("planArea").classList.remove("hidden");

    // Configuración del Círculo Clínico de Respiración Variable (Pool 100+ de la IA)
    const breath = plan.breathing_exercise;
    if (breath && breath.active) {
        clearInterval(breathingTimer);
        breathingActive = false;
        breathingSeconds = breath.duration_seconds || 240;
        
        $("breathingPhase").textContent = breath.objective.toUpperCase();
        $("breathingInstruction").textContent = breath.instruction;
        $("breathingTimer").textContent = formatTime(breathingSeconds);
        $("breathingArea").classList.remove("hidden");
    } else {
        $("breathingArea").classList.add("hidden");
    }

    // Visibilidad condicionada y enlace real a destinos premium filtrados
    $("mapsButton").classList.toggle("hidden", !plan.premium_destination_query);
    $("mapsButton").textContent = currentLanguage === "es" ? "✨ Dirección Destino" : "✨ Space Destination";
    
    $("musicButton").classList.toggle("hidden", !plan.premium_music_query);
    $("musicButton").textContent = currentLanguage === "es" ? "🎵 Entorno Acústico" : "🎵 Acoustic Environment";

    $("conciergeButton").classList.remove("hidden");
    $("conciergeButton").textContent = currentLanguage === "es" ? "✦ Notificar Staff" : "✦ Notify Staff";

    if (plan.reply) {
        if ("speechSynthesis" in window) {
            window.speechSynthesis.cancel();
            const utter = new SpeechSynthesisUtterance(plan.reply);
            utter.lang = currentLanguage === "es" ? "es-US" : "en-US";
            utter.rate = 0.95;
            window.speechSynthesis.speak(utter);
        }
    }
}

function syncBreathingCycle() {
    const elapsed = 240 - breathingSeconds;
    const step = elapsed % 16;
    const orb = $("breathingOrb");
    
    orb.className = "professional-orb"; 
    if (step < 4) {
        $("breathingPhase").textContent = currentLanguage === "es" ? "INHALA" : "INHALE";
        orb.classList.add("inhale");
    } else if (step < 8) {
        $("breathingPhase").textContent = currentLanguage === "es" ? "RETIENE" : "HOLD";
        orb.classList.add("hold");
    } else if (step < 12) {
        $("breathingPhase").textContent = currentLanguage === "es" ? "EXHALA" : "EXHALE";
        orb.classList.add("exhale");
    } else {
        $("breathingPhase").textContent = currentLanguage === "es" ? "RECUPERA" : "REST";
        orb.classList.add("rest");
    }
    $("breathingTimer").textContent = formatTime(breathingSeconds);
}

function toggleBreathing() {
    if (breathingActive) {
        clearInterval(breathingTimer);
        breathingActive = false;
        $("breathingControlBtn").textContent = currentLanguage === "es" ? "Reanudar" : "Resume";
    } else {
        breathingActive = true;
        $("breathingControlBtn").textContent = currentLanguage === "es" ? "Pausa" : "Pause";
        breathingTimer = setInterval(() => {
            breathingSeconds--;
            if (breathingSeconds <= 0) {
                clearInterval(breathingTimer);
                breathingActive = false;
                breathingSeconds = 240;
                $("breathingPhase").textContent = "OK";
            } else {
                syncBreathingCycle();
            }
        }, 1000);
    }
}

async function openPremiumMap() {
    if (!currentResult || !currentResult.premium_destination_query) return;
    const res = await fetch(`/api/maps?destination=${encodeURIComponent(currentResult.premium_destination_query)}`);
    const data = await res.json();
    if (data.url) window.open(data.url, "_blank", "noopener,noreferrer");
}

async function playPremiumMusic() {
    if (!currentResult || !currentResult.premium_music_query) return;
    const res = await fetch(`/api/music?query=${encodeURIComponent(currentResult.premium_music_query)}`);
const data = await res.json();
if (data.url) window.open(data.url, "_blank", "noopener,noreferrer");

function formatTime(seconds) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function renderMemorySummary() {
  const box = $("memorySummary");
  box.innerHTML = "";
  const items = [
    ["Identidad de Dispositivo", memory.core?.name || "VIP User Profile"],
    ["Enfoque de Ejecución", memory.moment?.intent || "CONCIERGE"],
    ["Frecuencia de Reentradas Hoy", memory.history ? memory.history.length : 0]
  ];
  items.forEach(([k, v]) => {
    const div = document.createElement("div");
    div.className = "memory-item";
    div.innerHTML = `<span>${k}</span><strong>${v}</strong>`;
    box.appendChild(div);
  });
}

function init() {
  if (!localStorage.getItem("mirror_device_id")) {
    localStorage.setItem("mirror_device_id", "vip_" + Math.random().toString(36).substring(2, 15));
  }
  
  applyInitialState("es");
  
  $("langToggle").onclick = () => applyInitialState(currentLanguage === "en" ? "es" : "en");
  
  $("memoryButton").onclick = () => { 
    renderMemorySummary(); 
    showDeck("memoryScreen"); 
  };
  
  $("closeMemory").onclick = () => showDeck("mainDeck");
  $("sendButton").onclick = askMirror;
  
  $("voiceButton").onclick = () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return;
    
    if (listening) {
      try { recognition.stop(); } catch(e) {}
      listening = false;
      $("voiceButton").classList.remove("active-mic");
    } else {
      recognition = new SR();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = currentLanguage === "es" ? "es-US" : "en-US";
      
      recognition.onstart = () => {
        listening = true;
        $("voiceButton").classList.add("active-mic");
      };
      
      recognition.onresult = (e) => {
        if (e.results && e.results[0] && e.results[0][0]) {
          $("messageInput").value = e.results[0][0].transcript;
          askMirror();
        }
      };
      
      recognition.onend = () => {
        listening = false;
        $("voiceButton").classList.remove("active-mic");
      };
      
      try { recognition.start(); } catch(err) { listening = false; }
    }
  };
  
  $("breathingControlBtn").onclick = toggleBreathing;
  $("mapsButton").onclick = openPremiumMap;
  $("musicButton").onclick = playPremiumMusic;
  
  $("clearMemoryButton").onclick = () => {
    memory = { core: {}, moment: {}, preferences: {}, dislikes: [], history: [], learning: {} };
    localStorage.removeItem("mirror_memory");
    renderMemorySummary();
    showDeck("mainDeck");
  };
  
  $("messageInput").addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      askMirror();
    }
  });
}

document.addEventListener("DOMContentLoaded", init);
