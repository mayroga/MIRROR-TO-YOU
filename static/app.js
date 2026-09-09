let currentLang = 'es';
let voiceEnabled = false;
let currentModeInterval = null;
let phraseInterval = null;
let sessionTimer = null;
let timeLeft = 600; // 10 minutos en segundos
let conversationMemory = [];
const MAX_MEMORY_TURNS = 15;

const randomMapsLinks = [
    "https://google.com",
    "https://google.com",
    "https://google.com",
    "https://google.com",
    "https://google.com"
];

// Al cargar la ventana, verifica si el usuario regresa de un pago exitoso de Stripe
window.onload = async () => {
    const urlParams = new URLSearchParams(window.location.search);
    const stripeStatus = urlParams.get('stripe_status');
    
    if (stripeStatus === 'success') {
        // Limpia la barra de direcciones para estética visual
        window.history.replaceState({}, document.title, "/");
        await runLiveSessionVerification();
    } else {
        await runLiveSessionVerification();
    }
};

// Monitoreo en tiempo real del estado de la sesión volátil en el backend
async function runLiveSessionVerification() {
    try {
        const response = await fetch('/api/auth/session-status');
        const status = await response.json();
        
        if (status.active && status.time_left > 0) {
            timeLeft = status.time_left;
            document.getElementById('paywallModal').style.display = 'none';
            document.getElementById('appInterface').style.display = 'flex';
            startSessionTimer();
        } else {
            // Cierre estricto: Oculta la app y fuerza el muro de pago
            document.getElementById('appInterface').style.display = 'none';
            document.getElementById('paywallModal').style.display = 'flex';
        }
    } catch (e) {
        document.getElementById('appInterface').style.display = 'none';
        document.getElementById('paywallModal').style.display = 'flex';
    }
}

// Ejecución del login por credenciales administrativas
async function executeAdminLogin() {
    const userIn = document.getElementById('loginUsername').value.trim();
    const passIn = document.getElementById('loginPassword').value.trim();
    const errorMsg = document.getElementById('loginError');
    
    if (!userIn || !passIn) return;
    
    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: userIn, password: passIn })
        });
        
        if (response.ok) {
            errorMsg.style.display = 'none';
            await runLiveSessionVerification();
        } else {
            errorMsg.style.display = 'block';
        }
    } catch (e) {
        errorMsg.style.display = 'block';
    }
}

// Redirección segura hacia Checkout de Stripe
async function triggerStripePayment(tier) {
    try {
        const response = await fetch('/api/stripe/create-checkout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ price_tier: tier })
        });
        const data = await response.json();
        if (data.url) {
            window.location.href = data.url;
        }
    } catch (e) {
        console.error("Error al conectar con la pasarela de Stripe.");
    }
}

function startSessionTimer() {
    if (sessionTimer) clearInterval(sessionTimer);
    sessionTimer = setInterval(async () => {
        timeLeft--;
        let m = Math.floor(timeLeft / 60);
        let s = timeLeft % 60;
        document.getElementById('timer-display').innerText = `${m}:${s < 10 ? '0' : ''}${s}`;
        
        // Cada 15 segundos valida el estado real con el backend para evitar alteraciones en el cliente
        if (timeLeft % 15 === 0) {
            const check = await fetch('/api/auth/session-status');
            const data = await check.json();
            if (!data.active) timeLeft = 0;
        }

        if (timeLeft <= 0) {
            clearInterval(sessionTimer);
            if (currentModeInterval) clearInterval(currentModeInterval);
            if (phraseInterval) clearInterval(phraseInterval);
            if ('speechSynthesis' in window) window.speechSynthesis.cancel();
            
            // Cierre total instantáneo de la App
            document.getElementById('appInterface').style.display = 'none';
            document.getElementById('shutdown-overlay').style.display = 'flex';
        }
    }, 1000);
}

function closeSession() {
    fetch('/api/clear', { method: 'DELETE' }).then(() => {
        location.reload();
    });
}

// Código base de Mirror to You preservado de manera idéntica
function updateMapsLink() {
    document.getElementById('m-maps').href = randomMapsLinks[Math.floor(Math.random() * randomMapsLinks.length)];
}

const masterPhrases = {
    en: [
        "Release every ounce of shoulder tension right now.",
        "Your mind is clear, powerful, and entirely unburdened.",
        "Banish fatigue; focus only on absolute control and stability.",
        "Let go of urgency. Time bends to your strategic rhythm.",
        "Silence the noise. Your inner sanctuary requires zero friction."
    ],
    es: [
        "Libera cada gramo de tensión en tus hombros ahora mismo.",
        "Tu mente es clara, poderosa y totalmente libre de cargas.",
        "Desvanece el cansancio; concéntrate solo en el control absoluto.",
        "Suelta la urgencia. El tiempo se adapta a tu ritmo estratégico.",
        "Silencia el ruido externo. Tu santuario interior no tiene fricción."
    ]
};

const verifiedStreams = [
    "https://youtube.com",
    "https://youtube.com"
];
let usedIndices = [], streamIndex = 0;

function getSmartPhrase() {
    const list = masterPhrases[currentLang];
    if (usedIndices.length >= list.length) usedIndices = [];
    let idx;
    do { idx = Math.floor(Math.random() * list.length); } while (usedIndices.includes(idx));
    usedIndices.push(idx);
    return list[idx];
}

function toggleLanguage() {
    currentLang = currentLang === 'en' ? 'es' : 'en';
    updateTexts();
}

function updateTexts() {
    document.getElementById('lang-btn').innerText = currentLang === 'es' ? 'ES' : 'EN';
    document.getElementById('wellness-title').innerText = currentLang === 'es' ? 'Bienestar y Antifatiga' : 'Precision Wellness';
    document.getElementById('travel-title').innerText = currentLang === 'es' ? 'Asesor Conversacional' : 'Conversational Advisor';
    document.getElementById('footer-text').innerText = currentLang === 'es' ? 'Sesión Volátil Encriptada. Cero Datos Retenidos.' : 'Encrypted Volatile Session. Zero Data Retained.';
    document.getElementById('close-btn').innerText = currentLang === 'es' ? 'Cerrar' : 'Close';
    document.getElementById('travel-input').placeholder = currentLang === 'es' ? 'Escriba su consulta o use los botones de asistencia...' : 'Type your query or use assistance buttons...';
    document.getElementById('objective-desc').innerText = currentLang === 'es' ? 'Opciones cognitivas sin repetición y streams verificados.' : 'Unrepeated cognitive options and verified streams.';
    document.getElementById('audio-btn').innerText = voiceEnabled ? (currentLang === 'es' ? '🔊 Voz: ON' : '🔊 Voice: ON') : (currentLang === 'es' ? '🔊 Voz: OFF' : '🔊 Voice: OFF');
    document.getElementById('mortals-label').innerText = currentLang === 'es' ? 'Uso para mortales' : 'Standard Access';
    document.getElementById('mortals-sub').innerText = currentLang === 'es' ? 'Enlaces externos' : 'External links';
    document.getElementById('btn-p1').innerText = currentLang === 'es' ? 'Protocolo Antipánico' : 'Anti-Panic Protocol';
    document.getElementById('btn-p2').innerText = currentLang === 'es' ? 'Enfoque Ejecutivo' : 'Executive Focus';
    document.getElementById('btn-p3').innerText = currentLang === 'es' ? 'Restauración Profunda' : 'Deep Restoration';
    document.getElementById('btn-p4').innerText = currentLang === 'es' ? 'Impulso Antifatiga' : 'Anti-Fatigue Boost';
    document.getElementById('btn-p5').innerText = currentLang === 'es' ? '⚡ Reto Vital 60s' : '⚡ 60s Vitality Challenge';
    document.getElementById('btn-p6').innerText = currentLang === 'es' ? '🎵 Frecuencias Antiestrés' : '🎵Anti-Stress Frequencies';
    document.getElementById('btn-no').innerText = currentLang === 'es' ? '❓ No sé' : '❓ No Idea';
    document.getElementById('btn-help').innerText = currentLang === 'es' ? '🤝Ayúdame' : '🤝 Help Me';
    document.getElementById('btn-send').innerText = currentLang === 'es' ? 'Enviar Conversación' : 'Send Conversation';
}

function toggleVoiceGuide() {
    voiceEnabled = !voiceEnabled;
    document.getElementById('audio-btn').innerText = voiceEnabled ? (currentLang === 'es' ? '🔊 Voz: ON' : '🔊 Voice: ON') : (currentLang === 'es' ? '🔊 Voz: OFF' : '🔊 Voice: OFF');
    if (voiceEnabled) speak(currentLang === 'es' ? 'Guía por voz activada.' : 'Voice guide activated.');
}

function speak(text) {
    if (!voiceEnabled || !('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = currentLang === 'es' ? 'es-ES' : 'en-US';
    utterance.rate = 0.95;
    window.speechSynthesis.speak(utterance);
}

function setBreathingMode(mode) {
    if (currentModeInterval) clearInterval(currentModeInterval);
    if (phraseInterval) clearInterval(phraseInterval);
    const speechBox = document.getElementById('dynamic-speech'), initialPhrase = getSmartPhrase();
    speechBox.innerText = initialPhrase;
    speak(initialPhrase);
    
    phraseInterval = setInterval(() => {
        const nextPhrase = getSmartPhrase();
        speechBox.innerText = nextPhrase;
        speak(nextPhrase);
    }, 15000);
    
const circle = document.getElementById('b-circle'),
      phase = document.getElementById('b-phase'),
      counter = document.getElementById('b-counter');

let step = 0;

const sequence = [
    { text: currentLang === 'es' ? 'Inhalar' : 'Inhale', scale: 'scale(1.3)', time: 4 },
    { text: currentLang === 'es' ? 'Retener' : 'Hold', scale: 'scale(1.3)', time: 4 },
    { text: currentLang === 'es' ? 'Exhalar' : 'Exhale', scale: 'scale(1)', time: 4 }
];

function runStep() {
    if (timeLeft <= 0) return;
    const current = sequence[step % sequence.length];
    phase.innerText = current.text;
    circle.style.transform = current.scale;
    let t = current.time;
    counter.innerText = `${t}s`;
    
    currentModeInterval = setInterval(() => {
        t--;
        counter.innerText = `${t}s`;
        if (t <= 0) {
            clearInterval(currentModeInterval);
            step++;
            runStep();
        }
    }, 1000);
}

runStep();

function startChallenge60() {
    if (currentModeInterval) clearInterval(currentModeInterval);
    if (phraseInterval) clearInterval(phraseInterval);
    
    const speechBox = document.getElementById('dynamic-speech'),
          counter = document.getElementById('b-counter'),
          phase = document.getElementById('b-phase');
          
    phase.innerText = currentLang === 'es' ? 'RETO VITAL' : 'VITALITY';
    let totalTime = 60;
    
    const challengeTexts = currentLang === 'es' ? 
        [
            "Silencio absoluto: Desconecta el ruido externo por 60 segundos.",
            "Enfoque: Define con claridad tu próximo destino de paz.",
            "Reinicio físico: Libera tensión acumulada en hombros y cuello."
        ] : 
        [
            "Absolute silence: Disconnect from external noise for 60s.",
            "Focus: Clearly define your next peaceful destination.",
            "Physical reset: Release tension accumulated in shoulders."
        ];
        
    let textIdx = 0;
    speechBox.innerText = challengeTexts[textIdx];
    speak(challengeTexts[textIdx]);
    
    currentModeInterval = setInterval(() => {
        totalTime--;
        counter.innerText = `${totalTime}s`;
        
        if (totalTime % 20 === 0 && textIdx < challengeTexts.length - 1) {
            textIdx++;
            speechBox.innerText = challengeTexts[textIdx];
            speak(challengeTexts[textIdx]);
        }
        
        if (totalTime <= 0) {
            clearInterval(currentModeInterval);
            speechBox.innerText = currentLang === 'es' ? '¡Reto de 60 segundos superado con éxito!' : '60-second challenge successfully completed!';
            speak(speechBox.innerText);
        }
    }, 1000);
}

function toggleMusicModal() {
    const container = document.getElementById('yt-container'),
          player = document.getElementById('yt-player');
          
    if (container.style.display === 'none') {
        player.src = verifiedStreams[streamIndex % verifiedStreams.length];
        streamIndex++;
        container.style.display = 'block';
        speak(currentLang === 'es' ? 'Frecuencia antiestrés activada.' : 'Anti-stress frequency activated.');
    } else {
        player.src = '';
        container.style.display = 'none';
    }
}

function handleNoIdea() {
    const inputField = document.getElementById('travel-input');
    inputField.value = currentLang === 'es' ? "No tengo un rumbo fijo, necesito orientación general." : "I don't have a fixed direction, I need general guidance.";
    resolveTravelDirective();
}

// Corregido: Removida la llave huérfana de cierre que rompía el script aquí.

function handleHelpMe() {
    const inputField = document.getElementById('travel-input');
    inputField.value = currentLang === 'es' ? "Ayúdame a encontrar la mejor opción de bienestar y estabilidad." : "Help me find the best wellness and stability option.";
    resolveTravelDirective();
}

async function resolveTravelDirective() {
    const inputField = document.getElementById('travel-input');
    const userInput = inputField.value.trim();
    const output = document.getElementById('travel-output');
    
    if (!userInput) {
        output.innerText = currentLang === 'es' ? 'Por favor, escribe tu mensaje o usa los botones de asistencia.' : 'Please type your message or use assistance buttons.';
        return;
    }
    
    conversationMemory.push({ role: 'user', content: userInput });
    if (conversationMemory.length > MAX_MEMORY_TURNS * 2) {
        conversationMemory = conversationMemory.slice(-MAX_MEMORY_TURNS * 2);
    }
    
    inputField.value = '';
    output.innerText = currentLang === 'es' ? 'Analizando solicitud, por favor espere un momento...' : 'Analyzing request, please hold a moment...';
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ messages: conversationMemory, lang: currentLang }),
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        
        if (!response.ok) throw new Error('Conexión en curso');
        const data = await response.json();
        let aiResponseText = (data.reply || data.response || data.message || '').trim();
        
        if (!aiResponseText) throw new Error('Respuesta vacía');
        
        conversationMemory.push({ role: 'assistant', content: aiResponseText });
        output.innerText = aiResponseText;
        speak(aiResponseText);
    } catch (error) {
        clearTimeout(timeoutId);
        output.innerText = currentLang === 'es' ? 'Error de conexión o tiempo de espera agotado. Intente nuevamente.' : 'Connection error or timeout. Please try again.';
    }
}

function toggleMortalsDrawer() {
    const drawer = document.getElementById('mortals-drawer');
    drawer.style.display = drawer.style.display === 'block' ? 'none' : 'block';
    updateMapsLink();
}
