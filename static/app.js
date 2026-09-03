let currentLang = 'en';
let inactivityTimer;

// Memoria contextual local para mantener el hilo de la conversación
let conversationMemory = [];
const MAX_MEMORY_TURNS = 15;

function toggleLanguage() {
    currentLang = currentLang === 'en' ? 'es' : 'en';
    const langBtn = document.getElementById('lang-btn');
    const wellnessTitle = document.getElementById('wellness-title');
    const wellnessDesc = document.getElementById('wellness-desc');
    const travelTitle = document.getElementById('travel-title');
    const travelInput = document.getElementById('travel-input');
    const travelOutput = document.getElementById('travel-output');
    const footerText = document.getElementById('footer-text');
    const clearBtn = document.getElementById('clear-btn');
    const modalText = document.getElementById('modal-text');

    if (currentLang === 'es') {
        langBtn.innerText = 'EN';
        wellnessTitle.innerText = 'Bienestar y Antiestrés';
        wellnessDesc.innerText = 'Seleccione objetivo y siga el ritmo sincronizado.';
        travelTitle.innerText = 'Agente Privado de Viajes';
        travelInput.placeholder = 'Solicite itinerario privado, chárter de lujo o conexiones a medida...';
        travelOutput.innerText = 'Enlace seguro establecido. Esperando directivas...';
        footerText.innerText = 'Sesión Volátil Encriptada. Cero Datos Retenidos.';
        if (clearBtn) clearBtn.innerText = 'Borrar';
        if (modalText) modalText.innerText = 'Inactividad detectada. Toque la pantalla para mantener la sesión.';
    } else {
        langBtn.innerText = 'ES';
        wellnessTitle.innerText = 'Wellness & Anti-Stress';
        wellnessDesc.innerText = 'Select objective and follow the synchronized rhythm.';
        travelTitle.innerText = 'Private Travel Agent';
        travelInput.placeholder = 'Request private itinerary, luxury charter, or bespoke connections...';
        travelOutput.innerText = 'Secure link established. Awaiting directives...';
        footerText.innerText = 'Encrypted Volatile Session. Zero Data Retained.';
        if (clearBtn) clearBtn.innerText = 'Clear';
        if (modalText) modalText.innerText = 'Inactivity detected. Touch the screen to maintain session.';
    }
}

function clearData() {
    document.getElementById('travel-input').value = '';
    conversationMemory = [];
    document.getElementById('travel-output').innerText = currentLang === 'es' ? 'Datos y memoria borrados.' : 'Data and memory cleared.';
}

function toggleAudio() {
    const btn = document.getElementById('audio-btn');
    if (!btn) return;
    const isHighlighted = btn.style.borderColor === 'rgb(56, 189, 248)';
    btn.style.borderColor = isHighlighted ? 'var(--border-color)' : 'var(--accent-color)';
}

function setBreathingMode(mode) {
    const circle = document.getElementById('b-circle');
    const text = document.getElementById('b-text');
    if (!text || !circle) return;
    text.innerText = mode.toUpperCase();
    circle.style.transform = 'scale(1.2)';
    setTimeout(() => {
        circle.style.transform = 'scale(1)';
    }, 3000);
}

async function sendTravelRequest() {
    const inputField = document.getElementById('travel-input');
    const input = inputField.value.trim();
    if (!input) return;

    const output = document.getElementById('travel-output');
    output.innerText = currentLang === 'es' ? 'Procesando directiva con inteligencia artificial...' : 'Processing directive with artificial intelligence...';

    // Añadir mensaje del usuario a la memoria local
    conversationMemory.push({ role: 'user', content: input });
    
    // Limitar el historial a los últimos turnos permitidos
    if (conversationMemory.length > MAX_MEMORY_TURNS * 2) {
        conversationMemory = conversationMemory.slice(-MAX_MEMORY_TURNS * 2);
    }

    inputField.value = '';

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                messages: conversationMemory,
                lang: currentLang
            })
        });

        const data = await response.json();

        if (response.ok && data.reply) {
            // Guardar la respuesta de la IA en la memoria local
            conversationMemory.push({ role: 'assistant', content: data.reply });
            output.innerText = data.reply;
        } else {
            output.innerText = data.error || (currentLang === 'es' ? 'Error al procesar la solicitud.' : 'Error processing request.');
        }
    } catch (error) {
        output.innerText = currentLang === 'es' ? 'Error de conexión con el servidor.' : 'Server connection error.';
    }
}

function resetTimer() {
    clearTimeout(inactivityTimer);
    const modal = document.getElementById('warning-modal');
    if (modal) {
        modal.style.display = 'none';
    }
    inactivityTimer = setTimeout(() => {
        const warningModal = document.getElementById('warning-modal');
        if (warningModal) {
            warningModal.style.display = 'flex';
        }
    }, 59000);
}

function dismissWarning() {
    resetTimer();
}

window.onload = () => {
    window.addEventListener('mousemove', resetTimer);
    window.addEventListener('keypress', resetTimer);
    window.addEventListener('touchstart', resetTimer);
    resetTimer();
};
