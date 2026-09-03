// static/app.js

let memory = { core: {}, moment: {}, preferences: {}, dislikes: [], history: [], learning: {} };
let currentLanguage = "es";
let currentResult = null;
let recognition = null;
let listening = false;

// Variables de control para el Círculo Respiratorio Variable Profesional
let breathingTimer = null;
let breathingSeconds = 240;
let breathingActive = false;

const $ = id => document.getElementById(id);

/**
 * Inicializa los textos bases de la interfaz según el idioma detectado en la huella.
 * Garantiza que la pantalla esté limpia de textos fijos para que la IA tome el control.
 */
function applyInitialState(lang) {
    currentLanguage = lang;
    if (lang === "es") {
        $("messageInput").placeholder = "Romper monotonía, consultar o validar comando con MIRROR...";
        $("closeMemory").textContent = "← Volver";
        $("memoryTitle").textContent = "Ecosistema Confidencial & Patrones";
        $("clearMemoryButton").textContent = "Purgar Contexto Local";
        $("breathingControlBtn").textContent = "Iniciar Calibración";
    } else {
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
 * MODO 1: Selección de Estado Absoluto por un Solo Toque (Interfaz Primaria)
 * Lee el botón presionado y despacha un comando contextual limpio al backend.
 */
async function executeState(stateType) {
    document.querySelectorAll(".state-card").forEach(c => c.classList.remove("active"));
    
    let commandText = "";
    if (stateType === "HIGH_PRESSURE") {
        $("btnStatePressure").classList.add("active");
        commandText = currentLanguage === "es" ? "CALIBRAR ENFOQUE DIRECTO ALTA PRESION CORPORATIVA" : "CALIBRATE EXECUTIVE HIGH BUSINESS PRESSURE STATE";
    } else if (stateType === "TRANSITION") {
        $("btnStateTransition").classList.add("active");
        commandText = currentLanguage === "es" ? "INICIAR TRANSICION FUERA DEL RADAR MODO FAMILIA" : "START FULL FAMILY MODE OFF THE RADAR TRANSITION";
    } else if (stateType === "DISCONNECT") {
        $("btnStateDisconnect").classList.add("active");
        commandText = currentLanguage === "es" ? "ELIMINAR MONOTONIA ABURRIMIENTO OCIO INTERACCION PREMIUM" : "DESTROY MONOTONY BOREDOM LEISURE HIGH SURPRISE PAUSE";
    }
    
    await requestEcosystemAPI(commandText);
}

/**
 * MODO 2: Sistema de Chat y Validación Conversacional de Respaldo (Interfaz Secundaria)
 * Permite al cliente escribir o hablar para comprobar la inteligencia adaptativa de la app.
 */
async function askMirror() {
    const input = $("messageInput");
    const text = input.value.trim();
    if (!text) return;
    input.value = "";
    await requestEcosystemAPI(text);
}

/**
 * Despacho Unificado al Kernel del Backend Dual (Gemini / OpenAI Fallback)
 * Envía la huella del dispositivo (historial de reentradas y preferencias) de forma confidencial.
 */
async function requestEcosystemAPI(payloadText) {
    try {
        const response = await fetch("/api/mirror", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message: payloadText,
                language: currentLanguage,
                device_id: localStorage.getItem("mirror_device_id") || "secure_handset_token",
                memory: memory
            })
        });
        
        const data = await response.json();
        if (data.ok) {
            memory = data.memory;
            currentResult = data.plan;
            currentLanguage = data.understanding.language || currentLanguage;
            
            // Sincronizar el estado del idioma del cliente al instante
            applyInitialState(currentLanguage);
            renderEcosystem(data);
        }
    } catch (e) {
        console.error("Critical error syncing interface with device footprint.");
    }
}

/**
 * Renderizado Puro controlado en un 97% por la IA.
 * Inyecta las directrices ergonómicas, altera el círculo respiratorio y aplica zonas de color.
 */
function renderEcosystem(data) {
    const plan = data.plan;
    
    // 1. Aplicación de Zonas de Color y Patrones según nivel de fatiga analizado por la IA
    const badge = $("statusBadge");
    const zone = plan.status_color_zone || "GREEN";
    
    badge.className = "status-badge";
    if (zone === "YELLOW") {
        badge.classList.add("zone-yellow");
        badge.textContent = currentLanguage === "es" ? "SENSADO DE PATRÓN: ATENCIÓN" : "PATTERN DETECTION: ATTENTION";
    } else if (zone === "RED") {
        badge.classList.add("zone-red");
        badge.textContent = currentLanguage === "es" ? "SENSADO DE PATRÓN: RESGUARDO" : "PATTERN DETECTION: PROTECTION";
    } else {
        badge.classList.add("zone-green");
        badge.textContent = currentLanguage === "es" ? "SENSADO DE PATRÓN: CALIBRADO" : "PATTERN DETECTION: BALANCED";
    }

    // 2. Inyección de Texto y Puntos de Enfoque Directo de la IA (Sin marcas de código pesadas)
    $("planTitle").textContent = plan.title || "MIRROR CONSOLE";
    $("planReply").textContent = plan.reply;
    
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

    // 3. Inicialización del Círculo Respiratorio Clínico Progresivo (Pool Variable de 100+ de la IA)
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

    // 4. Vinculación de Enlaces de Geolocalización y Audio Premium calculados de forma invisible
    $("mapsButton").classList.toggle("hidden", !plan.premium_destination_query);
    $("mapsButton").textContent = currentLanguage === "es" ? "✨ Espacio Destino" : "✨ Space Destination";
    
    $("musicButton").classList.toggle("hidden", !plan.premium_music_query);
    $("musicButton").textContent = currentLanguage === "es" ? "🎵 Entorno Acústico" : "🎵 Acoustic Environment";

    $("conciergeButton").classList.remove("hidden");
    $("conciergeButton").textContent = currentLanguage === "es" ? "✦ Notificar Staff" : "✦ Notify Staff";

    // Módulo de Audio/Voz de alta fidelidad bilingüe
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

/**
 * Lógica del Ciclo de Respiración Profesional por Software (Relación Cuadrada Terapéutica)
 */
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

/**
 * Despacho y Redirección Real hacia los mapas y entornos acústicos provistos de forma encriptada
 */
async function openPremiumMap() {
    if (!currentResult || !currentResult.premium_destination_query) return;
    const res = await fetch(`/api/maps?destination=${encodeURIComponent(currentResult.premium_destination_query)}`);
    const data = await res.json();
    if (data.url) window.open(data.url, "_blank", "noopener,noreferrer");
}

async function playPremiumMusic() {
    if (!currentResult || !currentResult.premium_music_query) return;
  const responseMusic = await fetch(`/api/music?query=${encodeURIComponent(currentResult.premium_music_query)}`);
  const dataMusic = await responseMusic.json();
  if (dataMusic.url) window.open(dataMusic.url, "_blank", "noopener,noreferrer");
}

function formatTime(seconds) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

/**
 * Renderizado del resumen de Huellas y Patrones almacenados localmente de forma privada
 */
function renderMemorySummary() {
  const box = $("memorySummary");
  box.innerHTML = "";
  const items = [
    ["Identidad de Dispositivo", memory.core?.name || "VIP User Profile"],
    ["Enfoque de Ejecución", memory.moment?.intent || "CONCIERGE"],
    ["Frecuencia de Reentradas Hoy", memory.history ? memory.history.length : 0],
    ["Estatus de Redirecciones", currentResult?.premium_destination_query ? "Configurado" : "En Espera"]
  ];
  items.forEach(([k, v]) => {
    const div = document.createElement("div");
    div.className = "memory-item";
    div.innerHTML = `<span>${k}</span><strong>${v}</strong>`;
    box.appendChild(div);
  });
}

/**
 * Inicialización del Ecosistema y Registro de Eventos Directos (Fricción Cero)
 */
function init() {
  if (!localStorage.getItem("mirror_device_id")) {
    localStorage.setItem("mirror_device_id", "vip_" + Math.random().toString(36).substring(2, 15));
  }
  
  // El sistema inicia nativamente de forma limpia en español
  applyInitialState("es");
  
  $("langToggle").onclick = () => applyInitialState(currentLanguage === "en" ? "es" : "en");
  
  $("memoryButton").onclick = () => {
    renderMemorySummary();
    showDeck("memoryScreen");
  };
  $("closeMemory").onclick = () => showDeck("mainDeck");
  
  $("sendButton").onclick = askMirror;
  
  // Sistema secundario de reconocimiento por Voz de Alta Fidelidad
  $("voiceButton").onclick = () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return;
    if (listening) {
      recognition.stop();
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
        // Corrección de lectura de índice de voz nativa del navegador
        $("messageInput").value = e.results[0][0].transcript;
        askMirror();
      };
      
      recognition.onend = () => {
        listening = false;
        $("voiceButton").classList.remove("active-mic");
      };
      recognition.start();
    }
  };
  
  $("breathingControlBtn").onclick = toggleBreathing;
  $("mapsButton").onclick = openPremiumMap;
  $("musicButton").onclick = playPremiumMusic;
  
  // Purga e inicio desde cero de todos los patrones y huellas del dispositivo
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
