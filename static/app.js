let currentLang = 'en';
let inactivityTimer;

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
        clearBtn.innerText = 'Borrar';
        modalText.innerText = 'Inactividad detectada. Toque la pantalla para mantener la sesión.';
    } else {
        langBtn.innerText = 'ES';
        wellnessTitle.innerText = 'Wellness & Anti-Stress';
        wellnessDesc.innerText = 'Select objective and follow the synchronized rhythm.';
        travelTitle.innerText = 'Private Travel Agent';
        travelInput.placeholder = 'Request private itinerary, luxury charter, or bespoke connections...';
        travelOutput.innerText = 'Secure link established. Awaiting directives...';
        footerText.innerText = 'Encrypted Volatile Session. Zero Data Retained.';
        clearBtn.innerText = 'Clear';
        modalText.innerText = 'Inactivity detected. Touch the screen to maintain session.';
    }
}

function clearData() {
    document.getElementById('travel-input').value = '';
    document.getElementById('travel-output').innerText = currentLang === 'es' ? 'Datos borrados.' : 'Data cleared.';
}

function toggleAudio() {
    const btn = document.getElementById('audio-btn');
    const isHighlighted = btn.style.borderColor === 'rgb(56, 189, 248)';
    btn.style.borderColor = isHighlighted ? 'var(--border-color)' : 'var(--accent-color)';
}

function setBreathingMode(mode) {
    const circle = document.getElementById('b-circle');
    const text = document.getElementById('b-text');
    text.innerText = mode.toUpperCase();
    circle.style.transform = 'scale(1.2)';
    setTimeout(() => {
        circle.style.transform = 'scale(1)';
    }, 3000);
}

function sendTravelRequest() {
    const input = document.getElementById('travel-input').value;
    if (!input) return;
    const output = document.getElementById('travel-output');
    output.innerText = currentLang === 'es' ? 'Procesando directiva con agente privado...' : 'Processing directive with private agent...';
    setTimeout(() => {
        output.innerText = currentLang === 'es' ? 'Itinerario ajustado de forma confidencial.' : 'Itinerary adjusted confidentially.';
    }, 1000);
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
