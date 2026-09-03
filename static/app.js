let memory = { core: {}, moment: {}, preferences: {}, dislikes: [], history: [], learning: {} };
let currentLanguage = "en";
let currentResult = null;
let recognition = null;
let listening = false;
let speaking = false;

// Configuración del Círculo Respiratorio Variable Profesional (Ciclos eficientes de 4 minutos)
let breathingTimer = null;
let breathingSeconds = 240; 
let breathingActive = false;

const $ = id => document.getElementById(id);

const TRANSLATIONS = {
    en: {
        heroTitle: "Streamlined Execution.",
        heroSub: "Your private ecosystem. Speak or input your requirements below.",
        placeholder: "Command your rhythm...",
        mapsBtn: "✨ Exclusive Maps",
        musicBtn: "🎵 Acoustic Space",
        conciergeBtn: "✦ Request Concierge",
        back: "← Back"
    },
    es: {
        heroTitle: "Ejecución Inmediata.",
        heroSub: "Su ecosistema privado. Hable o escriba sus requerimientos.",
        placeholder: "Ordene su ritmo...",
        mapsBtn: "✨ Mapas Exclusivos",
        musicBtn: "🎵 Espacio Acústico",
        conciergeBtn: "✦ Solicitar Conserje",
        back: "← Volver"
    }
};

function applyLanguageUI(lang) {
    currentLanguage = lang;
    const t = TRANSLATIONS[lang];
    $("heroTitle").textContent = t.heroTitle;
    $("heroSub").textContent = t.heroSub;
    $("messageInput").placeholder = t.placeholder;
    $("mapsButton").textContent = t.mapsBtn;
    $("musicButton").textContent = t.musicBtn;
    $("conciergeButton").textContent = t.conciergeBtn;
    $("closeMemory").textContent = t.back;
}

function showDeck(id) {
    document.querySelectorAll(".deck").forEach(d => d.classList.remove("active"));
    $(id).classList.add("active");
}

async function askMirror() {
    const input = $("messageInput");
    const text = input.value.trim();
    if (!text) return;

    input.value = "";
    input.style.height = "auto";
    
    try {
        const response = await fetch("/api/mirror", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text, language: currentLanguage, memory: memory })
        });
        const data = await response.json();
        if (data.ok) {
            memory = data.memory;
            currentResult = data.plan;
            currentLanguage = data.understanding.language;
            applyLanguageUI(currentLanguage);
            renderEcosystem(data);
        }
    } catch (e) {
        console.error("Execution anomaly");
    }
}

function renderEcosystem(data) {
    $("planTitle").textContent = data.plan.title;
    $("planReply").textContent = data.plan.reply;
    
    const dirBox = $("directions");
    dirBox.innerHTML = "";
    data.plan.direction.forEach(d => {
        const el = document.createElement("div");
        el.className = "premium-direction-item";
        el.textContent = d;
        dirBox.appendChild(el);
    });

    $("planArea").classList.remove("hidden");
    
    // Si la intención es bienestar, despliega y autoconfigura el círculo respiratorio profesional
    if (data.understanding.intent === "WELLBEING") {
        $("breathingPhase").textContent = data.understanding.breathing_mode || "CALM";
        $("breathingArea").classList.remove("hidden");
    } else {
        $("breathingArea").classList.add("hidden");
    }

    if (data.plan.reply && !speaking) {
        speakHighFidelity(data.plan.reply);
    }
}

// Círculo Respiratorio Profesional Variable de Relación Cuadrada Rápida (Inhala 4s, Retiene 4s, Exhala 4s, Rest 4s)
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
    
    const mins = Math.floor(breathingSeconds / 60);
    const secs = breathingSeconds % 60;
    $("breathingTimer").textContent = `${String(mins).padStart(2,"0")}:${String(secs).padStart(2,"0")}`;
}

function toggleBreathing() {
    if (breathingActive) {
        clearInterval(breathingTimer);
        breathingActive = false;
        $("breathingControlBtn").textContent = "Resume";
    } else {
        breathingActive = true;
        $("breathingControlBtn").textContent = "Pause";
        breathingTimer = setInterval(() => {
            breathingSeconds--;
            if (breathingSeconds <= 0) {
                clearInterval(breathingTimer);
                breathingActive = false;
                breathingSeconds = 240;
            }
            syncBreathingCycle();
        }, 1000);
    }
}

function speakHighFidelity(text) {
    if (!("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = currentLanguage === "es" ? "es-US" : "en-US";
    utter.rate = 1.0; 
    utter.pitch = 0.95; // Tono elegante, profundo y maduro
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

function init() {
    applyLanguageUI("en");
    
    $("langToggle").onclick = () => {
        applyLanguageUI(currentLanguage === "en" ? "es" : "en");
    };
    $("memoryButton").onclick = () => showDeck("memoryScreen");
    $("closeMemory").onclick = () => showDeck("mainDeck");
    $("sendButton").onclick = askMirror;
    $("voiceButton").onclick = toggleVoiceRecognition;
    $("breathingControlBtn").onclick = toggleBreathing;
    
    $("mapsButton").onclick = async () => {
        const dest = currentResult?.destination || "";
        const res = await fetch(`/api/maps?destination=${encodeURIComponent(dest)}`);
        const data = await res.json();
        window.open(data.url, "_blank");
    };
    
    $("musicButton").onclick = async () => {
        const res = await fetch(`/api/music`);
        const data = await res.json();
        window.open(data.url, "_blank");
    };

    $("conciergeButton").onclick = () => {
        speakHighFidelity(currentLanguage === "es" ? "Contacto directo establecido con su Conserje de Línea Ejecutiva." : "Direct contact established with your Executive Line Concierge.");
    };

    $("messageInput").addEventListener("keydown", e => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            askMirror();
        }
    });
}

document.addEventListener("DOMContentLoaded", init);
