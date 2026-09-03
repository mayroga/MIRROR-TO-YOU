// static/app.js

let memory = { core: {}, moment: {}, preferences: {}, dislikes: [], history: [], learning: {} };
let currentLanguage = "es"; 
let currentResult = null;
let recognition = null;
let listening = false;
let speaking = false;

// Variables de control para el Círculo Respiratorio Profesional
let breathingTimer = null;
let breathingSeconds = 240; 
let breathingActive = false;

const $ = id => document.getElementById(id);

/**
 * Establece el estado de inicialización visual en el idioma nativo seleccionado.
 * Evita textos huérfanos fijos y limpia la interfaz para la IA.
 */
function applyInitialState(lang) {
    currentLanguage = lang;
    if (lang === "es") {
        $("heroTitle").textContent = "Ejecución Inmediata.";
        $("heroSub").textContent = "Su ecosistema privado. Indique sus requerimientos por voz o texto.";
        $("messageInput").placeholder = "Ordene su ritmo...";
        $("closeMemory").textContent = "← Volver";
        $("memoryTitle").textContent = "Memoria del Sistema & Contexto";
        $("clearMemoryButton").textContent = "Purgar Contexto Local";
        $("breathingControlBtn").textContent = "Iniciar";
    } else {
        $("heroTitle").textContent = "Streamlined Execution.";
        $("heroSub").textContent = "Your private ecosystem. Speak or input your requirements below.";
        $("messageInput").placeholder = "Command your rhythm...";
        $("closeMemory").textContent = "← Back";
        $("memoryTitle").textContent = "Ecosystem Memory & Context";
        $("clearMemoryButton").textContent = "Purge Local Context";
        $("breathingControlBtn").textContent = "Begin";
    }
}

function showDeck(id) {
    document.querySelectorAll(".deck").forEach(d => d.classList.remove("active"));
    const el = $(id);
    if (el) el.classList.add("active");
}

function setThinking(on) {
    const el = $("thinking");
    if (el) el.classList.toggle("hidden", !on);
}

/**
 * Envío de comandos directos al ecosistema de IA (Gemini / OpenAI Fallback)
 */
async function askMirror() {
    const input = $("messageInput");
    const text = input.value.trim();
    if (!text) return;

    input.value = "";
    input.style.height = "auto";
    setThinking(true);
    
    try {
        const response = await fetch("/api/mirror", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message: text,
                language: currentLanguage,
                device_id: localStorage.getItem("mirror_device_id") || "vip_secure_handset",
                memory: memory
            })
        });
        
        const data = await response.json();
        if (data.ok) {
            memory = data.memory;
            currentResult = data.plan; // Captura el JSON de control absoluto de la IA
            currentLanguage = data.understanding.language || currentLanguage;
            
            // Re-adaptar entorno bilingüe según decisión de la IA
            applyInitialState(currentLanguage);
            renderEcosystem(data);
        }
    } catch (e) {
        console.error("Anomaly detecting client directive.");
    } finally {
        setThinking(false);
    }
}

/**
 * Renderizado dinámico de la Consola de Mando. 
 * El 100% de los comos, porqués y cuandos son inyectados desde la IA.
 */
function renderEcosystem(data) {
    const plan = data.plan;
    
    // Inyección de textos y justificaciones de la IA
    $("statusBadge").textContent = (currentLanguage === "es" ? "DIRECCIÓN EN VIVO" : "LIVE DIRECTION");
    $("planTitle").textContent = plan.title || "MIRROR CONSOLE";
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

    // Gestión del Círculo de Respiración Profesional Terapéutico (Pool de 100+ Objetivos)
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

    // Visibilidad Condicional Inteligente de Botones según la IA determine los porqués
    $("mapsButton").classList.toggle("hidden", !plan.premium_destination_query);
    $("mapsButton").textContent = currentLanguage === "es" ? "✨ Mapas Exclusivos" : "✨ Exclusive Maps";
    
    $("musicButton").classList.toggle("hidden", !plan.premium_music_query);
    $("musicButton").textContent = currentLanguage === "es" ? "🎵 Espacio Acústico" : "🎵 Acoustic Space";

    $("conciergeButton").classList.remove("hidden");
    $("conciergeButton").textContent = currentLanguage === "es" ? "✦ Solicitar Conserje" : "✦ Request Concierge";

    if (plan.reply && !speaking) {
        speakHighFidelity(plan.reply);
    }
}

/**
 * Lógica del Círculo Respiratorio Profesional (Relación Cuadrada: Inhala, Retiene, Exhala, Recupera)
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
                $("breathingPhase").textContent = currentLanguage === "es" ? "COMPLETO" : "SUCCESS";
            } else {
                syncBreathingCycle();
            }
        }, 1000);
    }
}

/**
 * Redirecciones de Ejecución Real y Filtrado de Ultra-Lujo provistos por la IA
 */
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

/**
 * Modulo de Voz Bidireccional de Alta Fidelidad
 */
function speakHighFidelity(text) {
    if (!("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = currentLanguage === "es" ? "es-US" : "en-US";
    utter.rate = 0.95;
    utter.pitch = 0.95; 
    utter.onstart = () => speaking = true;
    utter.onend = () => speaking = false;
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
        
        recognition.onstart = () => {
            listening = true;
            $("voiceButton").classList.add("active-mic");
        };
        recognition.onresult = (e) => {
            $("messageInput").value = e.results[0][0].transcript;
            askMirror();
        };
        recognition.onend = () => {
            listening = false;
            $("voiceButton").classList.remove("active-mic");
        };
    }
    if (listening) recognition.stop(); else recognition.start();
}

/**
 * Renderizado de Memoria Persistente sin fricciones
 */
function renderMemorySummary() {
    const box = $("memorySummary");
    box.innerHTML = "";
    const items = [
        ["Identidad", memory.core?.name || "Premium Client"],
        ["Enfoque Actual", memory.moment?.intent || "CONCIERGE"],
        ["Idioma Fijo", currentLanguage.toUpperCase()]
    ];
    items.forEach(([k, v]) => {
        const div = document.createElement("div");
        div.className = "memory-item";
        div.innerHTML = `<span>${k}</span><strong>${v}</strong>`;
        box.appendChild(div);
    });
}
function formatTime(seconds) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function autoResize() {
  const el = $("messageInput");
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 140) + "px";
}

/**
 * Inicialización Global y Enlace de Eventos Directos
 */
function init() {
  // Generar ID único discreto si no existe
  if (!localStorage.getItem("mirror_device_id")) {
    localStorage.setItem("mirror_device_id", "vip_" + Math.random().toString(36).substring(2, 15));
  }

  applyInitialState("es"); // Por defecto inicia de forma limpia en español

  $("langToggle").onclick = () => {
    applyInitialState(currentLanguage === "en" ? "es" : "en");
  };
  $("memoryButton").onclick = () => {
    renderMemorySummary();
    showDeck("memoryScreen");
  };
  $("closeMemory").onclick = () => showDeck("mainDeck");
  $("sendButton").onclick = askMirror;
  $("voiceButton").onclick = toggleVoiceRecognition;
  $("breathingControlBtn").onclick = toggleBreathing;
  $("mapsButton").onclick = openPremiumMap;
  $("musicButton").onclick = playPremiumMusic;
  $("conciergeButton").onclick = () => {
    speakHighFidelity(currentLanguage === "es" ? "Línea directa con su conserje privado enlazada." : "Private concierge direct connection locked in.");
  };
  $("clearMemoryButton").onclick = () => {
    memory = { core: {}, moment: {}, preferences: {}, dislikes: [], history: [], learning: {} };
    localStorage.removeItem("mirror_memory");
    renderMemorySummary();
    showDeck("mainDeck");
  };
  $("messageInput").addEventListener("input", autoResize);
  $("messageInput").addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      askMirror();
    }
  });
}

document.addEventListener("DOMContentLoaded", init);
