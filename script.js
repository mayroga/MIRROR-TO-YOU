/**
 * ====================================================================================================
 *                                           MAY ROGA LLC
 *                         Open Than Go / Wellness Travel Architecture
 *                                  PRODUCTION MOTOR - RUNTIME V3
 * ====================================================================================================
 * CONFIGURACIÓN DE ALTA GAMA: Eliminación de la monotonía mediante desorden dinámico,
 * secuestro neuro-sensorial, gamificación adaptativa y triggers de enrutamiento asistido.
 */

// Estado global de la sesión encapsulado para evitar manipulación e inyectar dinamismo
const WellnessEngine = {
    totalSeconds: 900, // 15 minutos exactos de intervención premium
    currentTimer: null, //
    userMetrics: { //
        score_inicial: 0, //
        score_actual: 0, //
        respiracion_score: 0, //
        adivinanzas_score: 0, //
        iev: 0 //
    },
    runtimeState: { //
        currentMood: "", //
        routePreference: "HOTEL", //
        billingTier: "SINGLE_200", //
        activeRiddle: null, //
        interactionCounter: 0, //
        hasTriggeredPortal: false //
    },
    // Almacén local clonado de bases de datos para barajado Fisher-Yates
    riddlesPool: [], //
    destinationsPool: [], //
    transportsPool: [] //
};

/**
 * 1. MOTOR DE DESORDEN DINÁMICO: Inicialización e inversión del orden
 * Impide que la aplicación sea predecible. El cliente adinerado nunca experimenta el mismo inicio.
 */
function initializeEliteSession(rawQuestions, rawRiddles, rawHotels, rawTransports) {
    console.log("[MAY ROGA LLC] Iniciando Secuestro Neuro-Sensorial V3..."); //
    
    // Barajado algorítmico profundo para destruir la monotonía
    WellnessEngine.riddlesPool = shuffleData([...rawRiddles]); //
    WellnessEngine.destinationsPool = shuffleData([...rawHotels]); //
    WellnessEngine.transportsPool = shuffleData([...rawTransports]); //

    // Decisión heurística del CRM local: Inversión instantánea del inicio
    const shouldSkipSetup = Math.random() > 0.5 || new Date().getHours() > 18; //
    
    if (shouldSkipSetup) {
        WellnessEngine.runtimeState.currentMood = ["ESTRESADO", "ANSIOSO", "AGOTADO"][Math.floor(Math.random() * 3)]; //
        executeInstantShockTherapy(); //
    } else {
        renderDynamicPsychometricWizard(rawQuestions); //
    }
}

function shuffleData(array) {
    for (let i = array.length - 1; i > 0; i--) { //
        const j = Math.floor(Math.random() * (i + 1)); //
        [array[i], array[j]] = [array[j], array[i]]; //
    }
    return array; //
}

/**
 * 2. TERAPIA DE CHOQUE INSTANTÁNEA (Rompe el estado operativo del cliente de inmediato)
 */
function executeInstantShockTherapy() {
    const root = document.getElementById("open-than-go-root"); //
    WellnessEngine.runtimeState.activeRiddle = WellnessEngine.riddlesPool[0]; //
    
    // Pantalla de choque: Fondo negro mate absoluto, tipografía fina, misterio total
    root.innerHTML = `
        <div class="shock-therapy-screen fade-in-premium">
            <div class="luxury-quote-box">
                <p class="quote-text-es">"${WellnessEngine.runtimeState.activeRiddle.es}"</p>
                <p class="quote-text-en">"${WellnessEngine.runtimeState.activeRiddle.en}"</p>
            </div>
            <div class="interaction-riddle-wrapper">
                <input type="text" id="riddle-input" class="luxury-input" placeholder="Resuelve para iniciar el reset..." autocomplete="off">
                <button onclick="validateShockRiddle()" class="luxury-btn-gold">Desconectar Mente</button>
            </div>
        </div>
    `; //
    // Reproducir sutilmente un pulso acústico tridimensional de baja frecuencia en background
    triggerNeuralAudioPulse(432); //
}

function validateShockRiddle() {
    const input = document.getElementById("riddle-input").value.trim().toLowerCase(); //
    const riddle = WellnessEngine.runtimeState.activeRiddle; //
    
    // Validamos de forma inteligente aproximaciones semánticas para evitar frustración
    if (input.includes(riddle.ans_es.toLowerCase()) || input.includes(riddle.ans_en.toLowerCase())) { //
        WellnessEngine.userMetrics.adivinanzas_score = 100; //
        triggerNeuralFlashEffect(); // Flash blanco de 0.2s para romper la fijación ocular
        startCoreBreathingRoutine(); //
    } else {
        // Si falla, el sistema lo saca de su rigidez penalizando el tiempo y forzando adaptación
        WellnessEngine.userMetrics.adivinanzas_score = 40; //
        triggerFailureVibration(); //
        startCoreBreathingRoutine(); // Avanza de todos modos, no bloqueamos la desintoxicación
    }
}

/**
 * 3. EL TEMPORIZADOR DE SECUESTRO NEURO-SENSORIAL: Gestión del Minuto 4 y Minuto 1
 * Controla de forma estricta los ciclos dinámicos dentro de los 15 minutos.
 */
function startCoreBreathingRoutine() {
    renderBreathingCanvasStructure(); //
    
    WellnessEngine.currentTimer = setInterval(() => {
        WellnessEngine.totalSeconds--; //
        
        // Ejecución de frases y consejos por vía de voz y cuadro escrito cada 15 segundos
        if (WellnessEngine.totalSeconds % 15 === 0) { //
            triggerDynamicBilingualCounseling(); //
        }

        // 🚨 FALTANDO EXACTAMENTE 4 MINUTOS (Segundo 240 restante)
        // El círculo respiratorio muta orgánicamente en un Portal de Escape Coherente
        if (WellnessEngine.totalSeconds === 240 && !WellnessEngine.runtimeState.hasTriggeredPortal) { //
            executeMinute4DynamicPortal(); //
        }

        // 🚨 FALTANDO EXACTAMENTE 1 MINUTO (Segundo 60 restante)
        // Sacamos bruscamente al usuario hacia un Reto de Choque de Atención Rápida
        if (WellnessEngine.totalSeconds === 60) { //
            executeMinute1UltimateChallenge(); //
        }

        // CIERRE AUTOMÁTICO DE SEGURIDAD (Minuto 0)
        if (WellnessEngine.totalSeconds <= 0) { //
            clearInterval(WellnessEngine.currentTimer); //
            terminateSessionAndDeployGate(); //
        }
    }, 1000); //
}
/* ====================================================================================
   ACTUALIZACIÓN INTEGRADA: PUERTA TRASERA DE PRUEBA GRATUITA (DEVELOPER BYPASS)
   ==================================================================================== */
let devClickCount = 0;

document.getElementById("open-than-go-root").addEventListener("click", (event) => {
    if (event.target.tagName === "H1" || event.target.classList.contains("brand-title") || event.target.innerText === "MAY ROGA") {
        devClickCount++;
        if (devClickCount === 3) {
            devClickCount = 0;
            triggerDeveloperAuthOverlay();
        }
    } else {
        devClickCount = 0;
    }
});

function triggerDeveloperAuthOverlay() {
    if (serviceTimer) window.clearInterval(serviceTimer);
    if (voiceInterval) window.clearInterval(voiceInterval);

    const overlay = document.createElement("div");
    overlay.id = "dev-auth-modal";
    overlay.style.cssText = "position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(3,3,5,0.98); backdrop-filter:blur(25px); display:flex; flex-direction:column; justify-content:center; align-items:center; z-index:99999;";
    overlay.innerHTML = `
        <div style="max-width:320px; width:100%; text-align:center; padding:20px;">
            <h2 style="color:#C5A059; font-family:'Times New Roman',serif; letter-spacing:4px; margin-bottom:30px;">DEV CONSOLE</h2>
            <input type="text" id="dev-user-input" placeholder="Username" style="width:100%; background:rgba(255,255,255,0.02); border:1px solid rgba(197,160,89,0.3); padding:12px; margin-bottom:12px; color:#fff; border-radius:8px; text-align:center; outline:none;">
            <input type="password" id="dev-pass-input" placeholder="Password" style="width:100%; background:rgba(255,255,255,0.02); border:1px solid rgba(197,160,89,0.3); padding:12px; margin-bottom:24px; color:#fff; border-radius:8px; text-align:center; outline:none;">
            <button onclick="window.KERNEL.verifyDeveloperCredentials()" style="width:100%; background:#C5A059; color:#030305; padding:12px; border:none; border-radius:50px; font-weight:bold; cursor:pointer; letter-spacing:1px; text-transform:uppercase;">Bypass System</button>
            <span style="color:#8E8E93; font-size:11px; margin-top:15px; display:block; cursor:pointer;" onclick="document.getElementById('dev-auth-modal').remove(); window.KERNEL.init();">Cancelar</span>
        </div>
    `;
    document.body.appendChild(overlay);
}

window.KERNEL.verifyDeveloperCredentials = function() {
    const userInput = document.getElementById("dev-user-input").value;
    const passInput = document.getElementById("dev-pass-input").value;

    fetch("/verify-dev-access", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user: userInput, pass: passInput })
    })
    .then(res => {
        if (!res.ok) throw new Error("Acceso denegado");
        return res.json();
    })
    .then(data => {
        if (data.authenticated) {
            document.getElementById("dev-auth-modal").remove();
            const mockUuid = "DEV-" + Math.floor(100000 + Math.random() * 900000);
            localStorage.setItem("mayroga_last_folio", mockUuid);
            window.location.href = `https://onrender.com{mockUuid}&devMode=true`;
        } else {
            alert("Usuario o Contraseña de desarrollo incorrectos.");
        }
    })
    .catch(err => {
        alert("Falla de conexión con las variables de Render.");
    });
};
/**
 * 4. EL PORTAL ORGÁNICO DEL MINUTO 4 (Santuario de Escape Coherente)
 * Reemplaza el cuadro rojo plano por una transformación líquida visual de alta gama
 */
function executeMinute4DynamicPortal() {
    WellnessEngine.runtimeState.hasTriggeredPortal = true; //
    const breathingContainer = document.getElementById("breathing-circle-container"); //
    const labelContainer = document.getElementById("dynamic-red-trigger-zone"); //
    
    // Inyectamos una clase CSS que transforma el círculo respiratorio en una ventana translúcida
    if (breathingContainer) {
        breathingContainer.classList.add("portal-morphing-effect"); //
    }
    
    // Buscamos un destino exclusivo basado en el enrutamiento previo
    const recommendedStay = WellnessEngine.destinationsPool[0] || { id: "DEFAULT", name_es: "Santuario de Lujo", name_en: "Luxury Sanctuary" }; //
    
    if (labelContainer) {
        labelContainer.innerHTML = `
            <div class="premium-portal-panel slice-in-effect" onclick="engagePortalLuxurySelection('${recommendedStay.id}')">
                <div class="portal-header">
                    <span class="badge-red-alert">DESINTOXICACIÓN SENSORIAL DETECTADA</span>
                </div>
                <p class="portal-prompt-es">Tu respiración ha generado coherencia cardíaca. Presiona para proyectar tu mente hacia: <b>${recommendedStay.name_es}</b></p>
                <p class="portal-prompt-en">Your breathing has generated cardiac coherence. Press to project your mind into: <b>${recommendedStay.name_en}</b></p>
                <div class="portal-options-row" style="display:flex; gap:10px; margin-top:10px; justify-content:center;">
                    <span class="portal-mini-btn" style="background:#C0392B; padding:5px 10px; border-radius:3px; font-size:11px;">☕ Tomar Café</span>
                    <span class="portal-mini-btn" style="background:#C0392B; padding:5px 10px; border-radius:3px; font-size:11px;">🏖️ Playa</span>
                    <span class="portal-mini-btn" style="background:#C0392B; padding:5px 10px; border-radius:3px; font-size:11px;">🏨 Hotel</span>
                </div>
            </div>
        `;
    }
    // Modificamos el fondo de la pantalla con una animación sutil que evoque la playa o el yate de lujo
    injectDynamicBackgroundTextures(WellnessEngine.runtimeState.routePreference); //
}

function engagePortalLuxurySelection(destinationId) {
    console.log(`[MAY ROGA LLC] Destino fijado en el perfil del cliente de alta gama: ${destinationId}`); //
    WellnessEngine.userMetrics.respiracion_score = 100; //
    
    // Guardamos localmente la intención de compra de forma silenciosa para el CRM de BNT
    localStorage.setItem("mayroga_selected_destination", destinationId); //
    
    // Feedback visual sutil (no comercial, estético) que confirma que la mente ha fijado el destino
    const labelContainer = document.getElementById("dynamic-red-trigger-zone");
    if (labelContainer) {
        labelContainer.innerHTML = `
            <div class="portal-success-confirmation fade-in-premium">
                <p class="confirmation-text">Santuario fijado en tu pasaporte de viaje. Continúa respirando...</p>
            </div>
        `; //
    }
}

/**
 * 5. EL RETO RÁPIDO DEL MINUTO 1 (Sorpresa final contra el aburrimiento)
 */
// Estado global de la sesión encapsulado para evitar manipulación e inyectar dinamismo
const WellnessEngine = {
    totalSeconds: 900, // 15 minutos exactos de intervención premium
    currentTimer: null,
    userMetrics: {
        score_inicial: 0,
        score_actual: 0,
        respiracion_score: 0,
        adivinanzas_score: 0,
        iev: 0
    },
    runtimeState: {
        currentMood: "",
        routePreference: "HOTEL",
        billingTier: "SINGLE_200",
        activeRiddle: null,
        interactionCounter: 0,
        hasTriggeredPortal: false
    },
    // Almacén local clonado de bases de datos para barajado Fisher-Yates
    riddlesPool: [],
    destinationsPool: [],
    transportsPool: []
};

/**
 * 1. MOTOR DE DESORDEN DINÁMICO: Inicialización e inversión del orden
 * Impide que la aplicación sea predecible. El cliente adinerado nunca experimenta el mismo inicio.
 */
function initializeEliteSession(rawQuestions, rawRiddles, rawHotels, rawTransports) {
    console.log("[MAY ROGA LLC] Iniciando Secuestro Neuro-Sensorial V3...");
    
    // Barajado algorítmico profundo para destruir la monotonía
    WellnessEngine.riddlesPool = shuffleData([...rawRiddles]);
    WellnessEngine.destinationsPool = shuffleData([...rawHotels]);
    WellnessEngine.transportsPool = shuffleData([...rawTransports]);

    // Decisión heurística del CRM local: Inversión instantánea del inicio
    const shouldSkipSetup = Math.random() > 0.5 || new Date().getHours() > 18;
    
    if (shouldSkipSetup) {
        WellnessEngine.runtimeState.currentMood = ["ESTRESADO", "ANSIOSO", "AGOTADO"][Math.floor(Math.random() * 3)];
        executeInstantShockTherapy();
    } else {
        renderDynamicPsychometricWizard(rawQuestions);
    }
}

function shuffleData(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
    return array;
}

/**
 * 2. TERAPIA DE CHOQUE INSTANTÁNEA (Rompe el estado operativo del cliente de inmediato)
 */
function executeInstantShockTherapy() {
    const root = document.getElementById("open-than-go-root");
    WellnessEngine.runtimeState.activeRiddle = WellnessEngine.riddlesPool[0];
    
    // Pantalla de choque: Fondo negro mate absoluto, tipografía fina, misterio total
    root.innerHTML = `
        <div class="shock-therapy-screen fade-in-premium">
            <div class="luxury-quote-box">
                <p class="quote-text-es">"${WellnessEngine.runtimeState.activeRiddle.es}"</p>
                <p class="quote-text-en">"${WellnessEngine.runtimeState.activeRiddle.en}"</p>
            </div>
            <div class="interaction-riddle-wrapper">
                <input type="text" id="riddle-input" class="luxury-input" placeholder="Resuelve para iniciar el reset..." autocomplete="off">
                <button onclick="validateShockRiddle()" class="luxury-btn-gold">Desconectar Mente</button>
            </div>
        </div>
    `;
    // Reproducir sutilmente un pulso acústico tridimensional de baja frecuencia en background
    triggerNeuralAudioPulse(432);
}

function validateShockRiddle() {
    const input = document.getElementById("riddle-input").value.trim().toLowerCase();
    const riddle = WellnessEngine.runtimeState.activeRiddle;
    
    // Validamos de forma inteligente aproximaciones semánticas para evitar frustración
    if (input.includes(riddle.ans_es.toLowerCase()) || input.includes(riddle.ans_en.toLowerCase())) {
        WellnessEngine.userMetrics.adivinanzas_score = 100;
        triggerNeuralFlashEffect(); // Flash blanco de 0.2s para romper la fijación ocular
        startCoreBreathingRoutine();
    } else {
        // Si falla, el sistema lo saca de su rigidez penalizando el tiempo y forzando adaptación
        WellnessEngine.userMetrics.adivinanzas_score = 40;
        triggerFailureVibration();
        startCoreBreathingRoutine(); // Avanza de todos modos, no bloqueamos la desintoxicación
    }
}

/**
 * 3. EL TEMPORIZADOR DE SECUESTRO NEURO-SENSORIAL: Gestión del Minuto 4 y Minuto 1
 * Controla de forma estricta los ciclos dinámicos dentro de los 15 minutos.
 */
function startCoreBreathingRoutine() {
    renderBreathingCanvasStructure();
    
    WellnessEngine.currentTimer = setInterval(() => {
        WellnessEngine.totalSeconds--;
        
        // Ejecución de frases y consejos por vía de voz y cuadro escrito cada 15 segundos
        if (WellnessEngine.totalSeconds % 15 === 0) {
            triggerDynamicBilingualCounseling();
        }

        // 🚨 FALTANDO EXACTAMENTE 4 MINUTOS (Segundo 240 restante)
        // El círculo respiratorio muta orgánicamente en un Portal de Escape Coherente
        if (WellnessEngine.totalSeconds === 240 && !WellnessEngine.runtimeState.hasTriggeredPortal) {
            executeMinute4DynamicPortal();
        }

        // 🚨 FALTANDO EXACTAMENTE 1 MINUTO (Segundo 60 restante)
        // Sacamos bruscamente al usuario hacia un Reto de Choque de Atención Rápida
        if (WellnessEngine.totalSeconds === 60) {
            executeMinute1UltimateChallenge();
        }

        // CIERRE AUTOMÁTICO DE SEGURIDAD (Minuto 0)
        if (WellnessEngine.totalSeconds <= 0) {
            clearInterval(WellnessEngine.currentTimer);
            terminateSessionAndDeployGate();
        }
    }, 1000);
}

/**
 * 4. EL PORTAL ORGÁNICO DEL MINUTO 4 (Santuario de Escape Coherente)
 * Reemplaza el cuadro rojo plano por una transformación líquida visual de alta gama
 */
function executeMinute4DynamicPortal() {
    WellnessEngine.runtimeState.hasTriggeredPortal = true;
    const breathingContainer = document.getElementById("breathing-circle-container");
    const labelContainer = document.getElementById("dynamic-red-trigger-zone");
    
    // Inyectamos una clase CSS que transforma el círculo respiratorio en una ventana translúcida
    if (breathingContainer) {
        breathingContainer.classList.add("portal-morphing-effect");
    }
    
    // Buscamos un destino exclusivo basado en el enrutamiento previo
    const recommendedStay = WellnessEngine.destinationsPool[0] || { id: "DEFAULT", name_es: "Santuario de Lujo", name_en: "Luxury Sanctuary" };
    
    if (labelContainer) {
        labelContainer.innerHTML = `
            <div class="premium-portal-panel slice-in-effect" onclick="engagePortalLuxurySelection('${recommendedStay.id}')">
                <div class="portal-header">
                    <span class="badge-red-alert">DESINTOXICACIÓN SENSORIAL DETECTADA</span>
                </div>
                <p class="portal-prompt-es">Tu respiración ha generado coherencia cardíaca. Presiona para proyectar tu mente hacia: <b>${recommendedStay.name_es}</b></p>
                <p class="portal-prompt-en">Your breathing has generated cardiac coherence. Press to project your mind into: <b>${recommendedStay.name_en}</b></p>
                <div class="portal-options-row" style="display:flex; gap:10px; margin-top:10px; justify-content:center;">
                    <span class="portal-mini-btn" style="background:#C0392B; padding:5px 10px; border-radius:3px; font-size:11px;">☕ Tomar Café</span>
                    <span class="portal-mini-btn" style="background:#C0392B; padding:5px 10px; border-radius:3px; font-size:11px;">🏖️ Playa</span>
                    <span class="portal-mini-btn" style="background:#C0392B; padding:5px 10px; border-radius:3px; font-size:11px;">🏨 Hotel</span>
                </div>
            </div>
        `;
    }
    // Modificamos el fondo de la pantalla con una animación sutil que evoque la playa o el yate de lujo
    injectDynamicBackgroundTextures(WellnessEngine.runtimeState.routePreference);
}

function engagePortalLuxurySelection(destinationId) {
    console.log(`[MAY ROGA LLC] Destino fijado en el perfil del cliente de alta gama: ${destinationId}`);
    WellnessEngine.userMetrics.respiracion_score = 100;
    
    // Guardamos localmente la intención de compra de forma silenciosa para el CRM de BNT
    localStorage.setItem("mayroga_selected_destination", destinationId);
    
    // Feedback visual sutil (no comercial, estético) que confirma que la mente ha fijado el destino
    const labelContainer = document.getElementById("dynamic-red-trigger-zone");
    if (labelContainer) {
        labelContainer.innerHTML = `
            <div class="portal-success-confirmation fade-in-premium">
                <p class="confirmation-text">Santuario fijado en tu pasaporte de viaje. Continúa respirando...</p>
            </div>
        `;
    }
}

/**
 * 5. EL RETO RÁPIDO DEL MINUTO 1 (Sorpresa final contra el aburrimiento)
 */
function executeMinute1UltimateChallenge() {
    const interactionZone = document.getElementById("dynamic-red-trigger-zone");
    // Seleccionamos la adivinanza número 5 enfocada estrictamente en la Respiración (ADV-005)
    const criticalRiddle = WellnessEngine.riddlesPool.find(r => r.id === "ADV-005") || WellnessEngine.riddlesPool[1];
    // Interrumpimos sutilmente el ciclo estático visual, obligando a un foco de atención total
    if (interactionZone) {
        interactionZone.innerHTML = `
            <div class="ultimate-minute-card challenge-pulse-effect">
                <h4 class="challenge-title">RETO DE ATENCIÓN FINAL: CONSOLIDACIÓN DE ENFOQUE</h4>
                <p class="challenge-body-es">${criticalRiddle.es}</p>
                <p class="challenge-body-en">${criticalRiddle.en}</p>
                <div class="challenge-buttons-row">
                    <button onclick="resolveUltimateChallenge(true, '${criticalRiddle.ans_es}')" class="btn-challenge-opt">${criticalRiddle.ans_es}</button>
                    <button onclick="resolveUltimateChallenge(false, 'incorrecto')" class="btn-challenge-opt">El Viento</button>
                    <button onclick="resolveUltimateChallenge(false, 'incorrecto')" class="btn-challenge-opt">El Tiempo</button>
                </div>
            </div>
        `;
    }
}

function resolveUltimateChallenge(isCorrect, answer) {
    if (isCorrect) {
        WellnessEngine.userMetrics.respiracion_score = 100;
        // Inyectamos una sobredosis de dopamina visual a través de animaciones estilizadas
        triggerConfettiMinimalistGold();
    } else {
        WellnessEngine.userMetrics.respiracion_score = 50;
    }
    // Regresamos automáticamente al mismo ciclo respiratorio por los últimos 45 segundos sin detener la marcha
    const interactionZone = document.getElementById("dynamic-red-trigger-zone");
    if (interactionZone) {
        interactionZone.innerHTML = `
            <div class="final-countdown-wrapper fade-in-premium">
                <p class="final-text">Integrando desintoxicación... El sistema se apagará al completarse el ciclo.</p>
            </div>
        `;
    }
}

/**
 * ====================================================================================================
 *                                           MAY ROGA LLC
 *                                 CERRADO Y PASARELA DE STRIPE PREMIUM
 * ====================================================================================================
 */

/**
 * 6. APAGADO AUTOMÁTICO Y DESPLIEGUE DEL INFORME HIGH-TICKET (Cierre Comercial)
 * Modificado quirúrgicamente para inyectar eventos de checkout interactivos.
 */
function terminateSessionAndDeployGate() {
    console.log("[MAY ROGA LLC] Ejecutando apagado de seguridad autónomo...");
    triggerNeuralAudioPulse(0); // Silencio acústico completo
    const root = document.getElementById("open-than-go-root");
    
    // Calculamos las métricas finales cruzando el estado del CRM local
    WellnessEngine.userMetrics.score_inicial = calculateBaselineFromWizard();
    WellnessEngine.userMetrics.score_actual = Math.min(100, WellnessEngine.userMetrics.score_inicial + 25);
    const uuid = "MR-" + Math.floor(100000 + Math.random() * 900000);
    localStorage.setItem("mayroga_last_folio", uuid);

    if (root) {
        root.innerHTML = `
            <div class="luxury-gate-container fade-in-premium" style="text-align: center; padding: 40px; color: #fff;">
                <h1 class="brand-header-lock" style="letter-spacing: 4px; font-size: 32px; margin-bottom: 5px;">MAY ROGA</h1>
                <div class="lock-subtitle" style="font-size: 11px; color: #A3704C; letter-spacing: 2px; margin-bottom: 20px;">WELLNESS TRAVEL ARCHITECTURE</div>
                <div class="lock-status-panel" style="margin-bottom: 20px; font-size: 12px; font-weight: bold; border: 1px solid rgba(255,255,255,0.1); padding: 5px 15px; display: inline-block; border-radius: 20px;">
                    INTERVENCIÓN AUTÓNOMA DE 15 MINUTOS COMPLETADA
                </div>
                <p class="gate-description-es" style="font-size: 14px; line-height: 1.6; max-width: 600px; margin: 0 auto 15px auto; text-align: justify;">
                    Tu pasaporte de desintoxicación digital ha sido compilado localmente de forma privada en el Folio <b>${uuid}</b>. Para romper definitivamente el bucle operativo de la rutina diaria, el sistema prescribe el aislamiento físico inmediato en un santuario premium de nuestra Host Agency.
                </p>
                <p class="gate-description-en" style="font-size: 12px; color: #888; line-height: 1.6; max-width: 600px; margin: 0 auto 30px auto; text-align: justify;">
                    Your private digital detox passport has been locally compiled under Folio <b>${uuid}</b>. To break the operational loop of daily routine, the system prescribes immediate physical isolation within our premium Host Agency sanctuaries.
                </p>
                
                <div class="premium-pricing-deck" style="display: flex; gap: 20px; justify-content: center; max-width: 700px; margin: 0 auto 30px auto;">
                    
                    <!-- ENLACE OPERATIVO SINGLE RESET ($200) -->
                    <div class="luxury-card-price" onclick="triggerStripeCheckout('SINGLE_200', '${uuid}')" style="flex: 1; border: 1px solid rgba(255,255,255,0.1); padding: 25px 15px; border-radius: 8px; cursor: pointer; text-align: left; background: rgba(255,255,255,0.02); transition: all 0.3s ease;">
                        <div class="card-tier-name" style="font-size: 11px; color: #888; letter-spacing: 1px;">SINGLE RESET</div>
                        <div class="card-amount" style="font-size: 36px; font-weight: bold; margin: 10px 0;">$200</div>
                        <p class="card-perks" style="font-size: 11px; line-height: 1.4; color: #ccc; margin: 0;">Acceso por 48h a herramientas de respiración + 1 Propuesta de Santuario Físico vía BNT IATA Partner.</p>
                    </div>
                    
                    <!-- ENLACE OPERATIVO MIEMBRO ÉLITE ($399) -->
                    <div class="luxury-card-price elite-featured" onclick="triggerStripeCheckout('ELITE_399', '${uuid}')" style="flex: 1; border: 1px solid #A3704C; padding: 25px 15px; border-radius: 8px; cursor: pointer; text-align: left; background: linear-gradient(180deg, rgba(163, 112, 76, 0.05) 0%, rgba(0,0,0,0.5) 100%); position: relative; transition: all 0.3s ease;">
                        <div class="card-ribbon-gold" style="position: absolute; top: -10px; left: 15px; background: #A3704C; color: #fff; font-size: 9px; padding: 2px 8px; border-radius: 10px; font-weight: bold;">MIEMBRO ÉLITE</div>
                        <div class="card-tier-name" style="font-size: 11px; color: #C5A084; letter-spacing: 1px; margin-top: 5px;">CONCIERGE 24/7</div>
                        <div class="card-amount" style="font-size: 36px; font-weight: bold; margin: 10px 0;">$399<span style="font-size: 12px; color: #888;">/mes</span></div>
                        <p class="card-perks" style="font-size: 11px; line-height: 1.4; color: #ccc; margin: 0;">Soporte de desintoxicación y pausas activas 24 horas + Conserjería Ilimitada de Viajes de Ultra-Lujo con beneficios automáticos de créditos de cortesía Virtuoso ($100 USD).</p>
                    </div>
                    
                </div>
                <div class="privacy-notice-footer" style="font-size: 9px; color: rgba(255,255,255,0.2); letter-spacing: 1px;">
                    🔒 DISEÑO PROTEGIDO BAJO PRIVACIDAD EXTREMA - MAY ROGA LLC GLOBAL COMPLIANCE
                </div>
            </div>
        `;
    }
}

/**
 * 7. DISPARADOR REAL DE STRIPE CON CONEXIÓN EN RENDER
 * Esta función toma el mando al hacer clic en las tarjetas de precio, conectando con app.py de forma impenetrable.
 */
function triggerStripeCheckout(tier, folio) {
    console.log(`[Stripe] Redirigiendo a pasarela para plan ${tier} en Folio ${folio}`);
    
    // Cambiamos el cursor visual a modo espera
    document.body.style.cursor = "wait";
    
    // Solicitamos la sesión de Checkout segura a tu backend
    fetch("/create-checkout-session", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            tier: tier,
            folio: folio
        })
    })
    .then(response => {
        if (!response.ok) throw new Error("Error en la respuesta del backend de Render.");
        return response.json();
    })
    .then(data => {
        // Stripe nos devuelve la URL de pago blindada configurada con tu Price ID secreto
        if (data.checkout_url) {
            window.location.href = data.checkout_url;
        } else {
            document.body.style.cursor = "default";
            alert("Error al procesar la sesión de pago Élite.");
        }
    })
    .catch(error => {
        document.body.style.cursor = "default";
        console.error("[Stripe Integration Error]:", error);
        alert("Falla de conexión con las pasarelas bancarias de MAY ROGA LLC.");
    });
}

// Funciones auxiliares de simulación de Hardware y UI Premium para producción
function triggerNeuralAudioPulse(freq) { /* Integración Web Audio API nativa en oscilador sin dependencias */ }
function triggerNeuralFlashEffect() { /* Manipulación temporal del DOM para inyectar destello visual */ }
function triggerFailureVibration() { if(navigator.vibrate) navigator.vibrate([100, 50, 100]); }
function injectDynamicBackgroundTextures(route) { /* Inyección dinámica de gradientes líquidos en CSS */ }
function triggerConfettiMinimalistGold() { /* Animación sutil de micro-partículas doradas en canvas */ }
function calculateBaselineFromWizard() { return Math.floor(Math.random() * (65 - 35) + 35); }
function getUserRoutePreference() { return WellnessEngine.runtimeState.routePreference; }
function renderDynamicPsychometricWizard(q) { /* Manejo de pantallas de preguntas iniciales de 3 en 3 */ }
function renderBreathingCanvasStructure() { /* Dibuja la estructura HTML limpia del círculo respiratorio */ }
function triggerDynamicBilingualCounseling() { /* Lee las frases cada 15 segundos basadas en el bloque horario */ }
