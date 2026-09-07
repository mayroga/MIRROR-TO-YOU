// app.js (Gestión de Interfaz de Usuario, Control de Flujo de Autenticación, Paywall y Stripe Checkout)
let currentLang = 'en';
let inactivityTimer;

// Identificadores de control de acceso local
let authType = null; 
let clientSessionId = localStorage.getItem('mirror_session_id');

// Generar un ID de sesión único permanente si no existe ninguno en el dispositivo
if (!clientSessionId) {
    clientSessionId = 'sess_' + Math.random().toString(36).substring(2, 15) + Date.now().toString(36);
    localStorage.setItem('mirror_session_id', clientSessionId);
}

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

// Ejecución de Login Administrativo gratuito
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
            errBox.innerText = data.error || 'Credenciales inválidas.';
            errBox.style.display = 'block';
        }
    } catch (err) {
        errBox.innerText = 'Error de comunicación con el servidor.';
        errBox.style.display = 'block';
    }
}

// Redirección del usuario hacia las pasarelas externas de Stripe Checkout
async function redirectToStripe(priceType) {
    try {
        const response = await fetch('/api/checkout/create-session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ priceType: priceType, clientSessionId: clientSessionId })
        });
        const data = await response.json();
        if (data.url) {
            window.location.href = data.url; // Redirige a Stripe
        } else {
            alert('No se pudo generar la sesión de pago.');
        }
    } catch (error) {
        console.error('Error al conectar con Stripe:', error);
    }
}

// Verifica de manera asíncrona si la sesión activa cuenta con un pago verificado
async function verifyAccessRights() {
    // Si ya se autenticó como admin en esta pestaña, mantener acceso libre
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
    output.innerText = currentLang === 'es' ? 'Procesando directiva con el asesor privado...' : 'Processing directive with private advisor...';

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
                lang: currentLang,
                authType: authType,
                clientSessionId: clientSessionId
            })
        });

        const data = await response.json();

        if (response.ok && data.reply) {
            // Guardar la respuesta del asesor en la memoria local
            conversationMemory.push({ role: 'assistant', content: data.reply });
            output.innerText = data.reply;
            
            // Si el cliente realizó un pago único, tras realizar la primera consulta el servidor revocará su acceso,
            // por lo que re-verificamos su estado de inmediato para retornar a la pantalla de paywall.
            if (authType !== 'admin') {
                await verifyAccessRights();
            }
        } else {
            output.innerText = data.error || (currentLang === 'es' ? 'Error al procesar la directiva.' : 'Error processing directive.');
            if (response.status === 402) {
                lockApplicationInterface();
            }
        }
    } catch (error) {
        output.innerText = currentLang === 'es' ? 'Error temporal de enlace con el servidor de asesoría.' : 'Temporary advisory server link error.';
    }
}

function resetTimer() {
    // Si la interfaz de la aplicación principal no se encuentra visible, omitimos la ejecución del temporizador
    const mainApp = document.getElementById('appInterface');
    if (!mainApp || mainApp.style.display === 'none') return;

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
    // Escucha de eventos de interacción global para el refresco del temporizador de inactividad
    window.addEventListener('mousemove', resetTimer);
window.addEventListener('keypress', resetTimer);
window.addEventListener('touchstart', resetTimer);

// Evaluación automática inicial de permisos al cargar la ventana del navegador
verifyAccessRights();
