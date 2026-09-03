// static/app.js
let memory = { core: {}, moment: {}, preferences: {}, dislikes: [], history: [], learning: {} };
let currentLanguage = "es";
let currentResult = null;
let recognition = null;
let listening = false;
let speaking = false;

let breathingTimer = null;
let breathingSeconds = 240;
let breathingActive = false;

const $ = id => document.getElementById(id);

function applyInitialState(lang) {
    currentLanguage = lang;
    if (lang === "es") {
        $("messageInput").placeholder = "Validar o consultar requerimiento alternativo...";
        $("closeMemory").textContent = "← Volver";
        $("memoryTitle").textContent = "Ecosistema Confidencial";
        $("clearMemoryButton").textContent = "Purgar Contexto Local";
        $("breathingControlBtn").textContent = "Iniciar Reset";
    } else {
        $("messageInput").placeholder = "Validate or query alternative requirement...";
        $("closeMemory").textContent = "← Back";
        $("memoryTitle").textContent = "Confidential Ecosystem";
        $("clearMemoryButton").textContent = "Purge Local Context";
        $("breathingControlBtn").textContent = "Begin Reset";
    }
}

/**
 * MODO 1: Ejecución de Estado Absoluto por un Solo Toque (Primario)
 */
async function executeState(stateType) {
    // Desactivar activaciones visuales anteriores
    document.querySelectorAll(".state-card").forEach(c => c.classList.remove("active"));
    
    let commandText = "";
    if (stateType === "HIGH_PRESSURE") {
        $("btnStatePressure").classList.add("active");
        commandText = currentLanguage === "es" ? "ACTIVAR ESTADO ALTA PRESION MENTAL" : "ACTIVATE HIGH BUSINESS PRESSURE STATE";
    } else if (stateType === "TRANSITION") {
        $("btnStateTransition").classList.add("active");
        commandText = currentLanguage === "es" ? "ACTIVAR TRANSICION FAMILIAR DESCONEXION" : "ACTIVATE FAMILY TRANSITION DISCONNECT STATE";
    } else if (stateType === "DISCONNECT") {
        $("btnStateDisconnect").classList.add("active");
        commandText = currentLanguage === "es" ? "ACTIVAR PRIVACIDAD ABSOLUTA FUERA DEL RADAR" : "ACTIVATE OFF THE RADAR ABSOLUTE PRIVACY STATE";
    }
    
    await requestEcosystemAPI(commandText);
}

/**
 * MODO 2: Interfaz de Validación Conversacional de Respaldo (Secundario)
 */
async function askMirror() {
    const input = $("messageInput");
    const text = input.value.trim();
    if (!text) return;
    input.value = "";
    input.style.height = "auto";
    await requestEcosystemAPI(text);
}

/**
 * Canal de Comunicación Unificado con el Backend Dual (Gemini / OpenAI Fallback)
 */
async function requestEcosystemAPI(payloadText) {
    try {
        const response = await fetch("/api/mirror", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message: payloadText,
                language: currentLanguage,
                device_id: localStorage.getItem("mirror_device_id") || "secure_vip_terminal",
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
        console.error("Anomaly updating dynamic console parameters.");
    }
}

function renderEcosystem(data) {
    const plan = data.plan;
    
    $("statusBadge").textContent = currentLanguage === "es" ? "EJECUCIÓN EN VIVO" : "LIVE EXECUTION";
    $("planTitle").textContent = plan.title || "CONSOLA DE MANDO";
    $("planReply").textContent = plan.reply;
    
    const dirBox = $("directions");
    dirBox.innerHTML = "";
    if (Array.isArray(plan.direction)) {
        plan.direction.forEach(d => {
            const el = document.createElement("div");
            el.className = "premium-direction-item";
            el.textContent = d;
            dirBox.appendChild(el);
        });
    }
    
    $("planArea").classList.remove("hidden");

    // Despliegue del Círculo Clínico de Respiración Variable (Pool de 100+ de la IA)
    const breath = plan.breathing_exercise;
    if (breath && breath.active) {
        clearInterval(breathingTimer);
        breathingActive = false;
        breathingSeconds = breath.duration_seconds || 240;
        
        $("breathingPhase").textContent = breath.objective.toUpperCase();
        $("breathingInstruction").textContent = breath.instruction;
        $("breathingControlBtn").textContent = currentLanguage === "es" ? "Iniciar" : "Begin";
        $("breathingTimer").textContent = formatTime(breathingSeconds);
        $("breathingArea").classList.remove("hidden");
    } else {
        $("breathingArea").classList.add("hidden");
    }

    // Configuración Automática de Botones Premium con Consultas Exactas de la IA
    $("mapsButton").classList.toggle("hidden", !plan.premium_destination_query);
    $("mapsButton").textContent = currentLanguage === "es" ? "✨ Dirección Destino" : "✨ Target Destination";
    
    $("musicButton").classList.toggle("hidden", !plan.premium_music_query);
    $("musicButton").textContent = currentLanguage === "es" ? "🎵 Entorno Acústico" : "🎵 Acoustic Environment";

    $("conciergeButton").classList.remove("hidden");
    $("conciergeButton").textContent = currentLanguage === "es" ? "✦ Notificar Staff" : "✦ Notify Staff";

    if (plan.reply && !speaking) {
        speakHighFidelity(plan.reply);
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
}

function speakHighFidelity(text) {
    if (!("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = currentLanguage === "es" ? "es-US" : "en-US";
    utter.rate = 1.0;
    window.speechSynthesis.speak(utter);
}

function toggleVoiceRecognition() {
    if (!recognition) {
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SR) return;
        recognition = new SR();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = currentLanguage === "es" ? "es-US" : "en-US";
        recognition.onstart = () => { listening = true; $("voiceButton").classList.add("active-mic"); };
        recognition.onresult = (e) => { $("messageInput").value = e.results[0][0].transcript; askMirror(); };
        recognition.onend = () => { listening = false; $("voiceButton").classList.remove("active-mic"); };
    }
    if (listening) recognition.stop(); else recognition.start();
}

function formatTime(seconds) {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${String(m).padStart(2,"0")}:${String(s).padStart(2,"0")}`;
}

function init() {
    if (!localStorage.getItem("mirror_device_id")) {
        localStorage.setItem("mirror_device_id", "vip_" + Math.random().toString(36).substring(2, 15));
    }
    applyInitialState("es");
    $("langToggle").onclick = () => applyInitialState(currentLanguage === "en" ? "es" : "en");
    $("sendButton").onclick = askMirror;
    $("voiceButton").onclick = toggleVoiceRecognition;
    $("breathingControlBtn").onclick = toggleBreathing;
    $("mapsButton").onclick = openPremiumMap;
    $("musicButton").onclick = playPremiumMusic;
    $("messageInput").addEventListener("keydown", e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); askMirror(); } });
}
document.addEventListener("DOMContentLoaded", init);
