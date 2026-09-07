let inactivityTimer;

// Identificadores de control de acceso local vinculados al almacenamiento del navegador
let authType = null;
let clientSessionId = localStorage.getItem('mirror_session_id');

if (!clientSessionId) {
    clientSessionId = 'sess_' + Math.random().toString(36).substring(2, 15) + Date.now().toString(36);
    localStorage.setItem('mirror_session_id', clientSessionId);
}

// Inicialización segura de la variable de idioma compartida en el objeto global de la ventana
if (typeof window.currentLang === 'undefined') {
    window.currentLang = 'es';
}

let conversationMemory = [];
const MAX_MEMORY_TURNS = 15;

function toggleLanguage() {
    window.currentLang = window.currentLang === 'en' ? 'es' : 'en';
    const langBtn = document.getElementById('lang-btn');
    if (langBtn) langBtn.innerText = window.currentLang.toUpperCase();
    
    // Si la función nativa de actualización de textos de tu HTML existe, la ejecuta de inmediato
    if (typeof updateTexts === 'function') {
        updateTexts();
    }
}

async function handleAdminLogin(event) {
    if (event) event.preventDefault();
    const userIn = document.getElementById('admin-username-input').value.trim();
    const passIn = document.getElementById('admin-password-input').value.trim();
    const errBox = document.getElementById('login-error-msg');

    if (!userIn || !passIn) return;

    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: userIn, password: passIn })
        });
        const data = await response.json();

        if (response.ok && data.valid) {
            authType = 'admin';
            sessionStorage.setItem('mirror_auth_type', 'admin');
            unlockApplicationInterface();
        } else {
            if (errBox) {
                errBox.innerText = data.error || 'Credenciales inválidas.';
                errBox.style.display = 'block';
            }
        }
    } catch (err) {
        if (errBox) {
            errBox.innerText = 'Error de comunicación con el servidor.';
            errBox.style.display = 'block';
        }
    }
}

async function redirectToStripe(priceType) {
    try {
        const response = await fetch('/api/checkout/create-session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ priceType: priceType, clientSessionId: clientSessionId })
        });
        
        if (!response.ok) {
            throw new Error(`Server returned code ${response.status}`);
        }
        
        const data = await response.json();
        if (data.url) {
            window.location.href = data.url;
        } else {
            alert('No se pudo generar la sesión de pago.');
        }
    } catch (error) {
        console.error('Error al conectar con Stripe:', error);
        alert('Error interno en la pasarela. Verifica tus llaves en Render.');
    }
}

async function verifyAccessRights() {
    if (sessionStorage.getItem('mirror_auth_type') === 'admin') {
        authType = 'admin';
        unlockApplicationInterface();
        return;
    }

    try {
        const response = await fetch('/api/auth/check-access', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ clientSessionId: clientSessionId })
        });
        const data = await response.json();

        if (data.hasAccess) {
            unlockApplicationInterface();
        } else {
            lockApplicationInterface();
        }
    } catch (error) {
        console.error('Error verificando derechos de acceso:', error);
    }
}

function unlockApplicationInterface() {
    const paywall = document.getElementById('paywallModal');
    const mainApp = document.getElementById('appInterface');
    if (paywall) paywall.style.display = 'none';
    if (mainApp) mainApp.style.display = 'flex';
    resetTimer();
}

function lockApplicationInterface() {
    const paywall = document.getElementById('paywallModal');
    const mainApp = document.getElementById('appInterface');
    if (paywall) paywall.style.display = 'flex';
    if (mainApp) mainApp.style.display = 'none';
    clearTimeout(inactivityTimer);
}

async function sendTravelRequest() {
    const inputField = document.getElementById('travel-input');
    const input = inputField.value.trim();
    if (!input) return;

    const output = document.getElementById('travel-output');
    if (output) output.innerText = window.currentLang === 'es' ? 'Procesando consulta...' : 'Processing directive...';

    conversationMemory.push({ role: 'user', content: input });
    if (conversationMemory.length > MAX_MEMORY_TURNS * 2) {
        conversationMemory = conversationMemory.slice(-MAX_MEMORY_TURNS * 2);
    }

    if (inputField) inputField.value = '';

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                messages: conversationMemory,
                lang: window.currentLang,
                authType: authType,
                clientSessionId: clientSessionId
            })
        });

        const data = await response.json();

        if (response.ok && data.reply) {
            conversationMemory.push({ role: 'assistant', content: data.reply });
            if (output) output.innerText = data.reply;
            if (typeof speak === 'function') speak(data.reply);
            
            if (authType !== 'admin') {
                await verifyAccessRights();
            }
        } else {
            if (output) output.innerText = data.error || 'Error de acceso.';
            if (response.status === 402) {
                lockApplicationInterface();
            }
        }
    } catch (error) {
        if (output) output.innerText = 'Error temporal de conexión con el servidor.';
    }
}

function resetTimer() {
    const mainApp = document.getElementById('appInterface');
    if (!mainApp || mainApp.style.display === 'none') return;

    clearTimeout(inactivityTimer);
    const modal = document.getElementById('warning-modal');
    if (modal) modal.style.display = 'none';
    
    inactivityTimer = setTimeout(() => {
        const warningModal = document.getElementById('warning-modal');
        if (warningModal) warningModal.style.display = 'flex';
    }, 59000);
}

window.onload = () => {
    window.addEventListener('mousemove', resetTimer);
    window.addEventListener('keypress', resetTimer);
    window.addEventListener('touchstart', resetTimer);
    verifyAccessRights();
};
