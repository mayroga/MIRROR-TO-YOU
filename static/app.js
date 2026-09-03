// static/app.js
let memory = { core: {}, moment: {}, preferences: {}, dislikes: [], history: [], learning: {} };
let currentLanguage = "es";
let currentResult = null;
let recognition = null;
let listening = false;

let breathingTimer = null;
let breathingSeconds = 240;
let breathingActive = false;

const $ = id => document.getElementById(id);

function applyInitialState(lang) {
    currentLanguage = lang;
    if (lang === "es") {
        $("messageInput").placeholder = "Romper monotonía, consultar o validar comando...";
        $("closeMemory").textContent = "← Volver";
        $("memoryTitle").textContent = "Ecosistema Encriptado";
        $("clearMemoryButton").textContent = "Purgar Memoria Local";
        $("breathingControlBtn").textContent = "Iniciar Calibración";
    } else {
        $("messageInput").placeholder = "Break monotony, query or validate command...";
        $("closeMemory").textContent = "← Back";
        $("memoryTitle").textContent = "Encrypted Ecosystem";
        $("clearMemoryButton").textContent = "Purge Local Context";
        $("breathingControlBtn").textContent = "Begin Calibration";
    }
}

async function executeState(stateType) {
    document.querySelectorAll(".state-card").forEach(c => c.classList.remove("active"));
    let cmd = "";
    if (stateType === "HIGH_PRESSURE") {
        $("btnStatePressure").classList.add("active");
        cmd = currentLanguage === "es" ? "EJECUCION DIRECTA ALTA PRESION CORPORATIVA" : "DIRECT EXECUTION HIGH BUSINESS PRESSURE";
    } else if (stateType === "TRANSITION") {
        $("btnStateTransition").classList.add("active");
        cmd = currentLanguage === "es" ? "ACTIVAR TRANSICION FUERA DEL RADAR MODO FAMILIA" : "ACTIVATE FAMILY MODE OFF THE RADAR TRANSITION";
    } else if (stateType === "DISCONNECT") {
        $("btnStateDisconnect").classList.add("active");
        cmd = currentLanguage === "es" ? "MATAR ABURRIMIENTO OCIO EXPERIENCIA DE SORPRESA EXCLUSIVA" : "KILL BOREDOM OCCUPATION EXCLUSIVE SURPRISE EXPERIENCE";
    }
    await requestEcosystemAPI(cmd);
}

async function askMirror() {
    const input = $("messageInput");
    const text = input.value.trim();
    if (!text) return;
    input.value = "";
    await requestEcosystemAPI(text);
}

async function requestEcosystemAPI(payloadText) {
    try {
        const response = await fetch("/api/mirror", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: payloadText, language: currentLanguage, memory: memory })
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
        console.error("Critical interface synchronization anomaly.");
    }
}

function renderEcosystem(data) {
    const plan = data.plan;
    
    $("statusBadge").textContent = currentLanguage === "es" ? "EJECUCIÓN INMEDIATA" : "IMMEDIATE EXECUTION";
    $("planTitle").textContent = plan.title || "KERNEL CONFIGURATION";
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

    // Inyección e inicialización automática del círculo respiratorio dinámico (Pool 100+)
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

    // Vinculación directa de las URLs exclusivas calculadas por la IA
    $("mapsButton").classList.toggle("hidden", !plan.premium_destination_query);
    $("mapsButton").textContent = currentLanguage === "es" ? "✨ Dirección Destino" : "✨ Target Destination";
    
    $("musicButton").classList.toggle("hidden", !plan.premium_music_query);
    $("musicButton").textContent = currentLanguage === "es" ? "🎵 Entorno Acústico" : "🎵 Acoustic Environment";

    $("conciergeButton").classList.remove("hidden");
    $("conciergeButton").textContent = currentLanguage === "es" ? "✦ Solicitar Conserje" : "✦ Request Concierge";

    if (plan.reply) {
        if ("speechSynthesis" in window) {
            window.speechSynthesis.cancel();
            const utter = new SpeechSynthesisUtterance(plan.reply);
            utter.lang = currentLanguage === "es" ? "es-US" : "en-US";
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
}

function formatTime(seconds) {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${String(m).padStart(2,"0")}:${String(s).padStart(2,"0")}`;
}

function init() {
    applyInitialState("es");
    $("langToggle").onclick = () => applyInitialState(currentLanguage === "en" ? "es" : "en");
    $("sendButton").onclick = askMirror;
    $("voiceButton").onclick = () => {
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SR) return;
        if (listening) { recognition.stop(); listening = false; $("voiceButton").classList.remove("active-mic"); }
        else {
            recognition = new SR(); recognition.continuous = false; recognition.interimResults = false;
            recognition.lang = currentLanguage === "es" ? "es-US" : "en-US";
            recognition.onstart = () => { listening = true; $("voiceButton").classList.add("active-mic"); };
            recognition.onresult = (e) => { $("messageInput").value = e.results[0][0].transcript; askMirror(); };
            recognition.onend = () => { listening = false; $("voiceButton").classList.remove("active-mic"); };
            recognition.start();
        }
    };
    $("breathingControlBtn").onclick = toggleBreathing;
    $("mapsButton").onclick = openPremiumMap;
    $("musicButton").onclick = playPremiumMusic;
    $("messageInput").addEventListener("keydown", e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); askMirror(); } });
}
document.addEventListener("DOMContentLoaded", init);
