```javascript
/*
MIRROR TO YOU
The Private Life Concierge
Frontend Controller

Version: 1.0.0

Responsibilities:
- Connect the interface with the FastAPI backend.
- Maintain client-side memory.
- Manage MIRROR conversations.
- Manage missions and plans.
- Handle browser voice input/output.
- Handle memory backup and restoration.
- Handle memory recovery.
- Open Google Maps and YouTube.
- Send feedback and revisions.
- Never claim that a real-world action happened unless the backend confirms it.
*/

"use strict";

/* ============================================================
   GLOBAL STATE
   ============================================================ */

const MIRROR = {
  version: "1.0.0",
  apiBase: "",
  language: "en",
  voiceEnabled: true,
  deviceId: null,
  memory: null,
  currentResult: null,
  currentMission: null,
  config: null,
  recognition: null,
  listening: false,
  speaking: false
};


/* ============================================================
   DEFAULT MEMORY
   ============================================================ */

function defaultMemory() {
  return {
    core: {},
    moment: {},
    preferences: {},
    dislikes: [],
    history: [],
    learning: {}
  };
}


/* ============================================================
   BASIC HELPERS
   ============================================================ */

function $(id) {
  return document.getElementById(id);
}

function safeText(value) {
  return value == null ? "" : String(value).trim();
}

function normalizeText(value) {
  return safeText(value)
    .toLowerCase()
    .replace(/\s+/g, " ");
}

function escapeHTML(value) {
  return safeText(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function uniqueList(items) {
  const result = [];
  const seen = new Set();

  if (!Array.isArray(items)) return result;

  for (const item of items) {
    const value = safeText(item);
    const key = normalizeText(value);

    if (!key || seen.has(key)) continue;

    seen.add(key);
    result.push(value);
  }

  return result;
}

function showElement(element, visible = true) {
  if (!element) return;

  element.hidden = !visible;
  element.style.display = visible ? "" : "none";
}

function setButtonBusy(button, busy, busyText = "WORKING...") {
  if (!button) return;

  if (busy) {
    if (!button.dataset.originalText) {
      button.dataset.originalText = button.textContent;
    }

    button.disabled = true;
    button.textContent = busyText;
  } else {
    button.disabled = false;

    if (button.dataset.originalText) {
      button.textContent = button.dataset.originalText;
    }
  }
}

function notify(message, type = "info") {
  const text = safeText(message);

  if (!text) return;

  let box = $("mirrorNotification");

  if (!box) {
    box = document.createElement("div");
    box.id = "mirrorNotification";
    box.setAttribute("role", "status");

    Object.assign(box.style, {
      position: "fixed",
      left: "50%",
      bottom: "24px",
      transform: "translateX(-50%)",
      zIndex: "99999",
      maxWidth: "90vw",
      padding: "12px 18px",
      borderRadius: "999px",
      background: "rgba(20,20,20,.96)",
      color: "#fff",
      fontSize: "13px",
      letterSpacing: ".03em",
      boxShadow: "0 10px 30px rgba(0,0,0,.35)",
      opacity: "0",
      transition: "opacity .2s ease"
    });

    document.body.appendChild(box);
  }

  box.textContent = text;
  box.dataset.type = type;
  box.style.opacity = "1";

  clearTimeout(box._timer);

  box._timer = setTimeout(() => {
    box.style.opacity = "0";
  }, 3200);
}


/* ============================================================
   DEVICE ID
   ============================================================ */

function getDeviceId() {
  let id = null;

  try {
    id = localStorage.getItem("mirror_to_you_device_id");
  } catch (_) {}

  if (id) {
    MIRROR.deviceId = id;
    return id;
  }

  if (window.crypto && typeof crypto.randomUUID === "function") {
    id = crypto.randomUUID();
  } else {
    id =
      "mirror-" +
      Date.now().toString(36) +
      "-" +
      Math.random().toString(36).slice(2, 12);
  }

  try {
    localStorage.setItem(
      "mirror_to_you_device_id",
      id
    );
  } catch (_) {}

  MIRROR.deviceId = id;

  return id;
}


/* ============================================================
   INDEXEDDB MEMORY
   ============================================================ */

const MEMORY_DB_NAME = "mirror_to_you_memory";
const MEMORY_DB_VERSION = 1;
const MEMORY_STORE = "memory";

function openMemoryDB() {
  return new Promise((resolve, reject) => {
    if (!("indexedDB" in window)) {
      reject(
        new Error("IndexedDB is not available in this browser.")
      );
      return;
    }

    const request = indexedDB.open(
      MEMORY_DB_NAME,
      MEMORY_DB_VERSION
    );

    request.onupgradeneeded = event => {
      const db = event.target.result;

      if (!db.objectStoreNames.contains(MEMORY_STORE)) {
        db.createObjectStore(
          MEMORY_STORE,
          { keyPath: "id" }
        );
      }
    };

    request.onsuccess = () => resolve(request.result);

    request.onerror = () => {
      reject(
        request.error ||
        new Error("Unable to open local memory.")
      );
    };
  });
}


async function getLocalMemory() {
  try {
    const db = await openMemoryDB();

    return await new Promise((resolve, reject) => {
      const tx = db.transaction(
        MEMORY_STORE,
        "readonly"
      );

      const store = tx.objectStore(
        MEMORY_STORE
      );

      const request = store.get("client");

      request.onsuccess = () => {
        resolve(
          request.result
            ? request.result.memory
            : null
        );
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  } catch (error) {
    console.warn(
      "MIRROR local memory unavailable:",
      error
    );

    return null;
  }
}


async function saveLocalMemory(memory) {
  const normalized = normalizeMemory(memory);

  MIRROR.memory = normalized;

  try {
    const db = await openMemoryDB();

    await new Promise((resolve, reject) => {
      const tx = db.transaction(
        MEMORY_STORE,
        "readwrite"
      );

      const store = tx.objectStore(
        MEMORY_STORE
      );

      const request = store.put({
        id: "client",
        updated_at: new Date().toISOString(),
        memory: normalized
      });

      request.onsuccess = () => resolve();

      request.onerror = () => {
        reject(request.error);
      };
    });

    return true;
  } catch (error) {
    console.warn(
      "MIRROR could not save local memory:",
      error
    );

    return false;
  }
}


function normalizeMemory(memory) {
  const base = defaultMemory();

  if (!memory || typeof memory !== "object") {
    return base;
  }

  for (const section of [
    "core",
    "moment",
    "preferences",
    "learning"
  ]) {
    if (
      memory[section] &&
      typeof memory[section] === "object" &&
      !Array.isArray(memory[section])
    ) {
      base[section] = {
        ...memory[section]
      };
    }
  }

  if (Array.isArray(memory.dislikes)) {
    base.dislikes = uniqueList(
      memory.dislikes
    );
  }

  if (Array.isArray(memory.history)) {
    base.history = memory.history.slice(-100);
  }

  return base;
}


function mergeMemory(base, update) {
  const result = normalizeMemory(base);

  if (!update || typeof update !== "object") {
    return result;
  }

  for (const section of [
    "core",
    "moment",
    "preferences",
    "learning"
  ]) {
    if (
      update[section] &&
      typeof update[section] === "object" &&
      !Array.isArray(update[section])
    ) {
      result[section] = {
        ...result[section],
        ...update[section]
      };
    }
  }

  if (Array.isArray(update.dislikes)) {
    result.dislikes = uniqueList([
      ...result.dislikes,
      ...update.dislikes
    ]);
  }

  if (Array.isArray(update.history)) {
    result.history = [
      ...result.history,
      ...update.history
    ].slice(-100);
  }

  return result;
}


/* ============================================================
   API
   ============================================================ */

async function api(
  path,
  options = {}
) {
  const config = {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    }
  };

  let response;

  try {
    response = await fetch(
      MIRROR.apiBase + path,
      config
    );
  } catch (error) {
    throw new Error(
      "MIRROR could not reach the server."
    );
  }

  let data = null;

  try {
    data = await response.json();
  } catch (_) {
    data = null;
  }

  if (!response.ok) {
    const detail =
      data &&
      (
        data.detail ||
        data.message ||
        data.error
      );

    throw new Error(
      detail ||
      `Request failed (${response.status}).`
    );
  }

  return data;
}


/* ============================================================
   CONFIGURATION
   ============================================================ */

async function loadConfig() {
  try {
    MIRROR.config = await api(
      "/api/config"
    );

    if (
      MIRROR.config &&
      MIRROR.config.language
    ) {
      MIRROR.language =
        MIRROR.config.language === "es"
          ? "es"
          : MIRROR.language;
    }

    return MIRROR.config;
  } catch (error) {
    console.warn(
      "MIRROR configuration unavailable:",
      error
    );

    return null;
  }
}


/* ============================================================
   LANGUAGE
   ============================================================ */

function detectBrowserLanguage() {
  const browserLanguage =
    navigator.language ||
    navigator.userLanguage ||
    "en";

  return browserLanguage
    .toLowerCase()
    .startsWith("es")
    ? "es"
    : "en";
}


function setLanguage(language) {
  MIRROR.language =
    language === "es"
      ? "es"
      : "en";

  try {
    localStorage.setItem(
      "mirror_to_you_language",
      MIRROR.language
    );
  } catch (_) {}
}


function loadLanguagePreference() {
  try {
    const saved =
      localStorage.getItem(
        "mirror_to_you_language"
      );

    if (saved === "es" || saved === "en") {
      MIRROR.language = saved;
      return;
    }
  } catch (_) {}

  MIRROR.language =
    detectBrowserLanguage();
}


/* ============================================================
   MIRROR REQUEST
   ============================================================ */

async function askMirror(message = null) {
  const input = $("mirrorInput");

  const text = safeText(
    message !== null
      ? message
      : input
        ? input.value
        : ""
  );

  if (!text) {
    notify(
      MIRROR.language === "es"
        ? "Dime qué quieres que MIRROR se encargue de hacer."
        : "Tell me what you would like MIRROR to take care of.",
      "warning"
    );

    if (input) input.focus();

    return;
  }

  const button =
    $("askMirrorButton") ||
    $("askButton") ||
    document.querySelector(
      '[data-action="ask-mirror"]'
    );

  setButtonBusy(
    button,
    true,
    MIRROR.language === "es"
      ? "PENSANDO..."
      : "THINKING..."
  );

  try {
    const result = await api(
      "/api/mirror",
      {
        method: "POST",
        body: JSON.stringify({
          message: text,
          memory: MIRROR.memory || defaultMemory(),
          language: MIRROR.language,
          voice_enabled: MIRROR.voiceEnabled,
          client_device_id: MIRROR.deviceId
        })
      }
    );

    MIRROR.currentResult = result;

    if (
      result &&
      result.memory_update
    ) {
      const merged = mergeMemory(
        MIRROR.memory,
        result.memory_update
      );

      await saveLocalMemory(
        merged
      );
    }

    renderMirrorResponse(result);
    renderPlan(result);
    updateConciergeUI(result);

    if (
      result &&
      result.mission
    ) {
      MIRROR.currentMission =
        result.mission;
    }

    if (
      result &&
      result.response &&
      MIRROR.voiceEnabled
    ) {
      speak(result.response);
    }

    if (input) {
      input.value = "";
      input.style.height = "";
    }

    await renderMissions();

    return result;
  } catch (error) {
    console.error(
      "MIRROR request error:",
      error
    );

    notify(
      error.message ||
      "MIRROR could not process the request.",
      "error"
    );
  } finally {
    setButtonBusy(
      button,
      false
    );
  }
}


/* ============================================================
   RESPONSE RENDERING
   ============================================================ */

function findResponseElement() {
  return (
    $("mirrorResponse") ||
    $("responseText") ||
    $("mirrorResponseText") ||
    document.querySelector(
      '[data-mirror-response]'
    )
  );
}


function renderMirrorResponse(result) {
  if (!result) return;

  const response =
    safeText(result.response) ||
    safeText(
      result.message
    );

  const element =
    findResponseElement();

  if (!element) return;

  element.textContent =
    response ||
    (
      MIRROR.language === "es"
        ? "Estoy preparando tu respuesta."
        : "I am preparing your response."
    );

  const section =
    $("responseSection") ||
    $("mirrorResponseSection");

  if (section) {
    showElement(
      section,
      true
    );
  }
}


/* ============================================================
   PLAN RENDERING
   ============================================================ */

function renderPlan(result) {
  if (!result) return;

  const plan =
    result.plan ||
    (
      result.mission &&
      result.mission.plan
    );

  if (!plan) return;

  const section =
    $("planSection") ||
    $("mirrorPlanSection");

  if (section) {
    showElement(
      section,
      true
    );
  }

  const title =
    $("planTitle");

  if (title) {
    title.textContent =
      safeText(
        plan.title
      ) ||
      (
        MIRROR.language === "es"
          ? "Tu plan MIRROR"
          : "Your MIRROR plan"
      );
  }

  const missionId =
    $("missionId");

  const mission =
    result.mission ||
    MIRROR.currentMission;

  if (missionId) {
    missionId.textContent =
      mission && mission.id
        ? `MISSION ${mission.id}`
        : "";
  }

  const category =
    $("planCategory");

  if (category) {
    category.textContent =
      safeText(
        plan.category
      ) ||
      "CONCIERGE";
  }

  const privacy =
    $("planPrivacy");

  if (privacy) {
    privacy.textContent =
      safeText(
        plan.privacy
      ) ||
      "NORMAL";
  }

  const priority =
    $("planPriority");

  if (priority) {
    priority.textContent =
      safeText(
        plan.priority
      ) ||
      "NORMAL";
  }

  const budget =
    $("planBudget");

  if (budget) {
    budget.textContent =
      formatBudget(
        plan.budget
      );
  }

  const destination =
    $("planDestination");

  if (destination) {
    destination.textContent =
      safeText(
        plan.destination
      ) ||
      (
        MIRROR.language === "es"
          ? "Por determinar"
          : "To be determined"
      );
  }

  const steps =
    $("planSteps");

  if (steps) {
    steps.innerHTML = "";

    const list =
      Array.isArray(plan.steps)
        ? plan.steps
        : [];

    if (!list.length) {
      const item =
        document.createElement("li");

      item.textContent =
        MIRROR.language === "es"
          ? "MIRROR está afinando el siguiente paso."
          : "MIRROR is refining the next step.";

      steps.appendChild(item);
    } else {
      list.forEach(step => {
        const item =
          document.createElement("li");

        item.textContent =
          safeText(step);

        steps.appendChild(item);
      });
    }
  }

  const execution =
    result.execution ||
    plan.execution;

  const executionLabel =
    $("executionStatus");

  if (executionLabel) {
    executionLabel.textContent =
      formatExecutionStatus(
        execution
      );
  }

  updatePlanButtons(
    result
  );
}


function formatBudget(value) {
  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return (
      MIRROR.language === "es"
        ? "No especificado"
        : "Not specified"
    );
  }

  const number =
    Number(value);

  if (!Number.isFinite(number)) {
    return safeText(value);
  }

  return new Intl.NumberFormat(
    MIRROR.language === "es"
      ? "es-US"
      : "en-US",
    {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0
    }
  ).format(number);
}


function formatExecutionStatus(execution) {
  if (!execution) {
    return "";
  }

  const status =
    safeText(
      execution.status
    );

  if (!status) return "";

  const mapEN = {
    NOT_EXECUTED: "Not executed",
    AWAITING_CLIENT_APPROVAL:
      "Awaiting your approval",
    REQUIRES_PROVIDER:
      "Requires a verified provider",
    REQUIRES_PROVIDER_VERIFICATION:
      "Requires provider verification",
    READY_FOR_EXECUTION:
      "Ready for execution",
    EXECUTED:
      "Executed"
  };

  const mapES = {
    NOT_EXECUTED: "No ejecutado",
    AWAITING_CLIENT_APPROVAL:
      "Esperando tu aprobación",
    REQUIRES_PROVIDER:
      "Requiere un proveedor verificado",
    REQUIRES_PROVIDER_VERIFICATION:
      "Requiere verificación del proveedor",
    READY_FOR_EXECUTION:
      "Listo para ejecutar",
    EXECUTED:
      "Ejecutado"
  };

  const map =
    MIRROR.language === "es"
      ? mapES
      : mapEN;

  return (
    map[status] ||
    status
  );
}


function updatePlanButtons(result) {
  const plan =
    result &&
    result.plan
      ? result.plan
      : null;

  const hasPlan = !!plan;

  const mapButton =
    $("openMapsButton");

  const moodButton =
    $("playMoodButton");

  const rightButton =
    $("rightButton") ||
    $("thisFeelsRightButton");

  const reviseButton =
    $("reviseButton") ||
    $("makeDifferentButton");

  const conciergeButton =
    $("conciergeButton") ||
    $("letConciergeButton");

  if (mapButton) {
    mapButton.disabled =
      !hasPlan ||
      !safeText(
        plan.destination
      );
  }

  if (moodButton) {
    moodButton.disabled =
      !hasPlan;
  }

  if (rightButton) {
    rightButton.disabled =
      !hasPlan;
  }

  if (reviseButton) {
    reviseButton.disabled =
      !hasPlan;
  }

  if (conciergeButton) {
    conciergeButton.disabled =
      !hasPlan;
  }
}


/* ============================================================
   CONCIERGE
   ============================================================ */

function updateConciergeUI(result) {
  if (!result) return;

  const concierge =
    result.concierge;

  if (!concierge) return;

  const box =
    $("conciergeStatus");

  if (!box) return;

  if (concierge.required) {
    box.textContent =
      MIRROR.language === "es"
        ? "Concierge puede encargarse del siguiente paso."
        : "Concierge can take care of the next step.";

    showElement(
      box,
      true
    );
  }
}


async function sendToConcierge() {
  const mission =
    MIRROR.currentMission ||
    (
      MIRROR.currentResult &&
      MIRROR.currentResult.mission
    );

  if (!mission || !mission.id) {
    notify(
      MIRROR.language === "es"
        ? "Primero crea una solicitud para MIRROR."
        : "Create a MIRROR request first.",
      "warning"
    );

    return;
  }

  const button =
    $("conciergeButton") ||
    $("letConciergeButton");

  setButtonBusy(
    button,
    true,
    MIRROR.language === "es"
      ? "ENVIANDO..."
      : "SENDING..."
  );

  try {
    const result = await api(
      `/api/missions/${encodeURIComponent(
        mission.id
      )}/concierge`,
      {
        method: "POST",
        body: JSON.stringify({
          mission_id: mission.id
        })
      }
    );

    MIRROR.currentMission =
      result.mission ||
      result;

    notify(
      MIRROR.language === "es"
        ? "Tu solicitud fue enviada a Concierge."
        : "Your request was sent to Concierge.",
      "success"
    );

    await renderMissions();
  } catch (error) {
    console.error(
      "Concierge error:",
      error
    );

    notify(
      error.message ||
      (
        MIRROR.language === "es"
          ? "No fue posible enviar la solicitud."
          : "The request could not be sent."
      ),
      "error"
    );
  } finally {
    setButtonBusy(
      button,
      false
    );
  }
}


/* ============================================================
   FEEDBACK
   ============================================================ */

async function submitFeedback(
  signal = "POSITIVE"
) {
  const mission =
    MIRROR.currentMission ||
    (
      MIRROR.currentResult &&
      MIRROR.currentResult.mission
    );

  if (!mission || !mission.id) {
    notify(
      MIRROR.language === "es"
        ? "No hay una misión activa."
        : "There is no active mission.",
      "warning"
    );

    return;
  }

  const feedback =
    signal === "POSITIVE"
      ? (
          MIRROR.language === "es"
            ? "Esto se siente correcto."
            : "This feels right."
        )
      : (
          MIRROR.language === "es"
            ? "Quiero algo diferente."
            : "I want something different."
        );

  try {
    const result = await api(
      "/api/missions/feedback",
      {
        method: "POST",
        body: JSON.stringify({
          mission_id: mission.id,
          feedback,
          signal
        })
      }
    );

    if (
      result &&
      result.memory_update
    ) {
      const merged =
        mergeMemory(
          MIRROR.memory,
          result.memory_update
        );

      await saveLocalMemory(
        merged
      );
    }

    if (
      result &&
      result.mission
    ) {
      MIRROR.currentMission =
        result.mission;
    }

    if (signal === "POSITIVE") {
      notify(
        MIRROR.language === "es"
          ? "Perfecto. MIRROR aprenderá de esta elección."
          : "Perfect. MIRROR will learn from this choice.",
        "success"
      );
    } else {
      notify(
        MIRROR.language === "es"
          ? "Entendido. Vamos a cambiar la dirección."
          : "Understood. We will change direction.",
        "info"
      );
    }

    await renderMissions();
  } catch (error) {
    console.error(
      "Feedback error:",
      error
    );

    notify(
      error.message ||
      (
        MIRROR.language === "es"
          ? "No fue posible registrar tu preferencia."
          : "Your preference could not be recorded."
      ),
      "error"
    );
  }
}


/* ============================================================
   PLAN REVISION
   ============================================================ */

async function revisePlan() {
  const mission =
    MIRROR.currentMission ||
    (
      MIRROR.currentResult &&
      MIRROR.currentResult.mission
    );

  if (!mission || !mission.id) {
    notify(
      MIRROR.language === "es"
        ? "Primero crea un plan."
        : "Create a plan first.",
      "warning"
    );

    return;
  }

  const defaultText =
    MIRROR.language === "es"
      ? "Hazlo diferente."
      : "Make it different.";

  const revision =
    window.prompt(
      MIRROR.language === "es"
        ? "¿Qué quieres cambiar?"
        : "What would you like to change?",
      defaultText
    );

  if (!revision) return;

  const button =
    $("reviseButton") ||
    $("makeDifferentButton");

  setButtonBusy(
    button,
    true,
    MIRROR.language === "es"
      ? "CAMBIANDO..."
      : "CHANGING..."
  );

  try {
    const result = await api(
      "/api/missions/revise",
      {
        method: "POST",
        body: JSON.stringify({
          mission_id: mission.id,
          revision,
          memory: MIRROR.memory
        })
      }
    );

    if (
      result &&
      result.plan
    ) {
      if (
        MIRROR.currentResult
      ) {
        MIRROR.currentResult.plan =
          result.plan;
      }

      if (
        MIRROR.currentMission
      ) {
        MIRROR.currentMission.plan =
          result.plan;
      }

      renderPlan(
        MIRROR.currentResult
      );
    }

    notify(
      MIRROR.language === "es"
        ? "He cambiado la dirección del plan."
        : "I changed the direction of the plan.",
      "success"
    );
  } catch (error) {
    console.error(
      "Revision error:",
      error
    );

    notify(
      error.message ||
      (
        MIRROR.language === "es"
          ? "No fue posible revisar el plan."
          : "The plan could not be revised."
      ),
      "error"
    );
  } finally {
    setButtonBusy(
      button,
      false
    );
  }
}


/* ============================================================
   MISSIONS
   ============================================================ */

async function renderMissions() {
  const container =
    $("missionsList") ||
    $("currentMissions");

  if (!container) return;

  try {
    const result =
      await api(
        "/api/missions"
      );

    const missions =
      Array.isArray(result)
        ? result
        : (
            Array.isArray(
              result.missions
            )
              ? result.missions
              : []
          );

    container.innerHTML = "";

    if (!missions.length) {
      container.innerHTML =
        `<div class="mirror-empty">
          ${
            MIRROR.language === "es"
              ? "Tus misiones aparecerán aquí."
              : "Your missions will appear here."
          }
        </div>`;

      return;
    }

    missions
      .slice()
      .reverse()
      .forEach(mission => {
        const item =
          document.createElement("button");

        item.type = "button";
        item.className =
          "mirror-mission-item";

        const title =
          safeText(
            mission.title
          ) ||
          safeText(
            mission.plan &&
            mission.plan.title
          ) ||
          "MIRROR Mission";

        const status =
          safeText(
            mission.status
          ) ||
          "NEW";

        item.innerHTML = `
          <span class="mirror-mission-title">
            ${escapeHTML(title)}
          </span>
          <span class="mirror-mission-status">
            ${escapeHTML(status)}
          </span>
        `;

        item.addEventListener(
          "click",
          () => loadMission(
            mission.id
          )
        );

        container.appendChild(
          item
        );
      });
  } catch (error) {
    console.warn(
      "Mission list unavailable:",
      error
    );
  }
}


async function loadMission(
  missionId
) {
  if (!missionId) return;

  try {
    const result =
      await api(
        `/api/missions/${encodeURIComponent(
          missionId
        )}`
      );

    const mission =
      result.mission ||
      result;

    MIRROR.currentMission =
      mission;

    MIRROR.currentResult = {
      ...(MIRROR.currentResult || {}),
      mission,
      plan: mission.plan,
      response:
        mission.response ||
        (
          MIRROR.currentResult &&
          MIRROR.currentResult.response
        )
    };

    renderPlan(
      MIRROR.currentResult
    );

    if (
      mission.response
    ) {
      renderMirrorResponse({
        response:
          mission.response
      });
    }

    const planSection =
      $("planSection") ||
      $("mirrorPlanSection");

    if (planSection) {
      showElement(
        planSection,
        true
      );

      planSection.scrollIntoView({
        behavior: "smooth",
        block: "center"
      });
    }
  } catch (error) {
    notify(
      error.message ||
      (
        MIRROR.language === "es"
          ? "No fue posible abrir la misión."
          : "The mission could not be opened."
      ),
      "error"
    );
  }
}


/* ============================================================
   MAPS
   ============================================================ */

async function openMaps() {
  const plan =
    MIRROR.currentResult &&
    MIRROR.currentResult.plan;

  if (!plan) {
    notify(
      MIRROR.language === "es"
        ? "Primero crea un plan."
        : "Create a plan first.",
      "warning"
    );

    return;
  }

  const destination =
    safeText(
      plan.destination
    );

  if (!destination) {
    notify(
      MIRROR.language === "es"
        ? "Todavía no tenemos un lugar definido."
        : "We do not have a destination yet.",
      "warning"
    );

    return;
  }

  try {
    const result =
      await api(
        "/api/maps",
        {
          method: "GET"
        }
      );

    let url =
      result &&
      result.url
        ? result.url
        : null;

    if (!url) {
      url =
        "https://www.google.com/maps/search/?api=1&query=" +
        encodeURIComponent(
          destination
        );
    }

    window.open(
      url,
      "_blank",
      "noopener,noreferrer"
    );
  } catch (_) {
    const url =
      "https://www.google.com/maps/search/?api=1&query=" +
      encodeURIComponent(
        destination
      );

    window.open(
      url,
      "_blank",
      "noopener,noreferrer"
    );
  }
}


/* ============================================================
   YOUTUBE / MOOD
   ============================================================ */

async function playMood() {
  const result =
    MIRROR.currentResult;

  const plan =
    result &&
    result.plan;

  const destination =
    plan &&
    safeText(
      plan.destination
    );

  const intent =
    result &&
    result.understanding &&
    safeText(
      result.understanding.intent
    );

  let query;

  if (destination) {
    query =
      `${destination} ${intent || ""} relaxing music`;
  } else {
    query =
      intent
        ? `${intent} relaxing music`
        : "luxury relaxing ambient music";
  }

  try {
    const data =
      await api(
        "/api/music",
        {
          method: "GET"
        }
      );

    let url =
      data &&
      data.url
        ? data.url
        : null;

    if (!url) {
      url =
        "https://www.youtube.com/results?search_query=" +
        encodeURIComponent(
          query
        );
    }

    window.open(
      url,
      "_blank",
      "noopener,noreferrer"
    );
  } catch (_) {
    const url =
      "https://www.youtube.com/results?search_query=" +
      encodeURIComponent(
        query
      );

    window.open(
      url,
      "_blank",
      "noopener,noreferrer"
    );
  }
}


/* ============================================================
   TEXT TO SPEECH
   ============================================================ */

function speechLanguage() {
  return MIRROR.language === "es"
    ? "es-US"
    : "en-US";
}


function speak(text) {
  const content =
    safeText(text);

  if (
    !content ||
    !("speechSynthesis" in window)
  ) {
    return false;
  }

  try {
    window.speechSynthesis.cancel();

    const utterance =
      new SpeechSynthesisUtterance(
        content
      );

    utterance.lang =
      speechLanguage();

    utterance.rate = 0.95;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    utterance.onstart = () => {
      MIRROR.speaking = true;
      updateSpeakButton(true);
    };

    utterance.onend = () => {
      MIRROR.speaking = false;
      updateSpeakButton(false);
    };

    utterance.onerror = () => {
      MIRROR.speaking = false;
      updateSpeakButton(false);
    };

    window.speechSynthesis.speak(
      utterance
    );

    return true;
  } catch (error) {
    console.warn(
      "Speech synthesis failed:",
      error
    );

    return false;
  }
}


function stopSpeaking() {
  if (
    "speechSynthesis" in window
  ) {
    window.speechSynthesis.cancel();
  }

  MIRROR.speaking = false;

  updateSpeakButton(false);
}


function toggleSpeak() {
  if (MIRROR.speaking) {
    stopSpeaking();
    return;
  }

  const result =
    MIRROR.currentResult;

  if (
    result &&
    result.response
  ) {
    speak(
      result.response
    );
  }
}


function updateSpeakButton(
  speaking
) {
  const buttons = [
    $("speakButton"),
    $("responseSpeakButton")
  ];

  buttons.forEach(button => {
    if (!button) return;

    button.textContent =
      speaking
        ? (
            MIRROR.language === "es"
              ? "DETENER"
              : "STOP"
          )
        : (
            MIRROR.language === "es"
              ? "HABLAR"
              : "SPEAK"
          );
  });
}


/* ============================================================
   SPEECH RECOGNITION
   ============================================================ */

function setupSpeechRecognition() {
  const SpeechRecognition =
    window.SpeechRecognition ||
    window.webkitSpeechRecognition;

  if (!SpeechRecognition) {
    MIRROR.recognition = null;
    return false;
  }

  const recognition =
    new SpeechRecognition();

  recognition.continuous = false;
  recognition.interimResults = true;
  recognition.maxAlternatives = 1;

  recognition.lang =
    speechLanguage();

  recognition.onstart = () => {
    MIRROR.listening = true;
    updateVoiceButton(true);
  };

  recognition.onresult = event => {
    const input =
      $("mirrorInput");

    if (!input) return;

    let finalText = "";
    let interimText = "";

    for (
      let i = event.resultIndex;
      i < event.results.length;
      i++
    ) {
      const result =
        event.results[i];

      if (result.isFinal) {
        finalText +=
          result[0].transcript;
      } else {
        interimText +=
          result[0].transcript;
      }
    }

    if (finalText) {
      input.value =
        (
          input.value
            ? input.value + " "
            : ""
        ) +
        finalText.trim();

      autoResizeInput(
        input
      );
    } else if (interimText) {
      input.dataset.interim =
        interimText;
    }
  };

  recognition.onerror = event => {
    MIRROR.listening = false;
    updateVoiceButton(false);

    if (
      event.error !==
      "aborted"
    ) {
      notify(
        MIRROR.language === "es"
          ? "No pude escuchar con claridad. Inténtalo de nuevo."
          : "I could not hear you clearly. Please try again.",
        "warning"
      );
    }
  };

  recognition.onend = () => {
    MIRROR.listening = false;
    updateVoiceButton(false);

    const input =
      $("mirrorInput");

    if (input) {
      delete input.dataset.interim;
    }
  };

  MIRROR.recognition =
    recognition;

  return true;
}


function toggleVoice() {
  if (!MIRROR.recognition) {
    setupSpeechRecognition();
  }

  if (!MIRROR.recognition) {
    notify(
      MIRROR.language === "es"
        ? "Tu navegador no permite entrada de voz."
        : "Your browser does not support voice input.",
      "warning"
    );

    return;
  }

  if (MIRROR.listening) {
    try {
      MIRROR.recognition.stop();
    } catch (_) {}

    return;
  }

  MIRROR.recognition.lang =
    speechLanguage();

  try {
    MIRROR.recognition.start();
  } catch (error) {
    console.warn(
      "Voice recognition could not start:",
      error
    );
  }
}


function updateVoiceButton(
  listening
) {
  const buttons = [
    $("voiceButton"),
    $("micButton"),
    $("voiceInputButton")
  ];

  buttons.forEach(button => {
    if (!button) return;

    button.classList.toggle(
      "is-listening",
      listening
    );

    button.setAttribute(
      "aria-pressed",
      listening
        ? "true"
        : "false"
    );

    button.textContent =
      listening
        ? (
            MIRROR.language === "es"
              ? "ESCUCHANDO..."
              : "LISTENING..."
          )
        : (
            MIRROR.language === "es"
              ? "HABLAR"
              : "VOICE"
          );
  });
}


/* ============================================================
   INPUT
   ============================================================ */

function autoResizeInput(
  input
) {
  if (!input) return;

  input.style.height =
    "auto";

  input.style.height =
    Math.min(
      input.scrollHeight,
      240
    ) + "px";
}


function clearInput() {
  const input =
    $("mirrorInput");

  if (!input) return;

  input.value = "";
  input.style.height = "";
  input.focus();
}


function handleInputKeydown(
  event
) {
  if (
    (event.ctrlKey ||
      event.metaKey) &&
    event.key === "Enter"
  ) {
    event.preventDefault();
    askMirror();
  }
}


/* ============================================================
   MEMORY RECOVERY
   ============================================================ */

async function openRecovery() {
  const modal =
    $("recoveryModal");

  try {
    const result =
      await api(
        `/api/memory/recovery/questions?language=${encodeURIComponent(
          MIRROR.language
        )}`
      );

    const questions =
      Array.isArray(result)
        ? result
        : (
            Array.isArray(
              result.questions
            )
              ? result.questions
              : []
          );

    renderRecoveryQuestions(
      questions
    );

    if (modal) {
      showElement(
        modal,
        true
      );

      modal.setAttribute(
        "aria-hidden",
        "false"
      );
    }
  } catch (error) {
    console.error(
      "Memory recovery error:",
      error
    );

    notify(
      error.message ||
      (
        MIRROR.language === "es"
          ? "No fue posible iniciar la recuperación."
          : "Memory recovery could not be started."
      ),
      "error"
    );
  }
}


function renderRecoveryQuestions(
  questions
) {
  const container =
    $("recoveryQuestions");

  if (!container) return;

  container.innerHTML = "";

  questions.forEach(question => {
    const wrapper =
      document.createElement("div");

    wrapper.className =
      "mirror-recovery-question";

    const title =
      document.createElement("h4");

    title.textContent =
      safeText(
        question.question
      );

    wrapper.appendChild(
      title
    );

    const options =
      document.createElement("div");

    options.className =
      "mirror-recovery-options";

    const optionList =
      Array.isArray(
        question.options
      )
        ? question.options
        : [];

    optionList.forEach(option => {
      const label =
        document.createElement("label");

      label.className =
        "mirror-recovery-option";

      const input =
        document.createElement("input");

      input.type = "radio";
      input.name =
        `recovery_${question.id}`;
      input.value =
        safeText(
          option.value
        );

      const span =
        document.createElement("span");

      span.textContent =
        safeText(
          option.label
        );

      label.appendChild(
        input
      );

      label.appendChild(
        span
      );

      options.appendChild(
        label
      );
    });

    wrapper.appendChild(
      options
    );

    container.appendChild(
      wrapper
    );
  });
}


function closeRecovery() {
  const modal =
    $("recoveryModal");

  if (!modal) return;

  showElement(
    modal,
    false
  );

  modal.setAttribute(
    "aria-hidden",
    "true"
  );
}


async function saveRecovery() {
  const container =
    $("recoveryQuestions");

  if (!container) return;

  const answers = {};

  const groups =
    container.querySelectorAll(
      "input[type='radio']:checked"
    );

  groups.forEach(input => {
    const prefix =
      "recovery_";

    const name =
      safeText(
        input.name
      );

    if (
      name.startsWith(prefix)
    ) {
      const questionId =
        name.slice(
          prefix.length
        );

      answers[questionId] =
        input.value;
    }
  });

  if (!Object.keys(answers).length) {
    notify(
      MIRROR.language === "es"
        ? "Elige al menos una opción."
        : "Choose at least one option.",
      "warning"
    );

    return;
  }

  const button =
    $("saveRecoveryButton") ||
    $("recoverySaveButton");

  setButtonBusy(
    button,
    true,
    MIRROR.language === "es"
      ? "RECONSTRUYENDO..."
      : "REBUILDING..."
  );

  try {
    const result =
      await api(
        "/api/memory/recovery",
        {
          method: "POST",
          body: JSON.stringify({
            answers,
            memory:
              MIRROR.memory ||
              defaultMemory()
          })
        }
      );

    const recovered =
      result.memory ||
      result.updated_memory ||
      result;

    await saveLocalMemory(
      recovered
    );

    closeRecovery();

    notify(
      MIRROR.language === "es"
        ? "Tu MIRROR ha sido reconstruido."
        : "Your MIRROR has been rebuilt.",
      "success"
    );
  } catch (error) {
    console.error(
      "Memory save error:",
      error
    );

    notify(
      error.message ||
      (
        MIRROR.language === "es"
          ? "No fue posible reconstruir tu MIRROR."
          : "Your MIRROR could not be rebuilt."
      ),
      "error"
    );
  } finally {
    setButtonBusy(
      button,
      false
    );
  }
}


/* ============================================================
   MEMORY BACKUP
   ============================================================ */

function exportMemory() {
  const memory =
    normalizeMemory(
      MIRROR.memory
    );

  const payload = {
    application:
      "MIRROR TO YOU",
    format:
      "mirror-memory",
    version:
      "1.0",
    exported_at:
      new Date().toISOString(),
    memory
  };

  const blob =
    new Blob(
      [
        JSON.stringify(
          payload,
          null,
          2
        )
      ],
      {
        type:
          "application/json"
      }
    );

  const url =
    URL.createObjectURL(
      blob
    );

  const link =
    document.createElement("a");

  link.href = url;
  link.download =
    "mirror-to-you-memory.json";

  document.body.appendChild(
    link
  );

  link.click();
  link.remove();

  setTimeout(
    () => URL.revokeObjectURL(url),
    1000
  );

  notify(
    MIRROR.language === "es"
      ? "Tu memoria MIRROR fue preparada para respaldo."
      : "Your MIRROR memory backup is ready.",
    "success"
  );
}


function importMemory() {
  const input =
    $("memoryFileInput") ||
    $("restoreMemoryInput");

  if (!input) {
    notify(
      MIRROR.language === "es"
        ? "No se encontró el selector de memoria."
        : "The memory file selector was not found.",
      "error"
    );

    return;
  }

  input.value = "";
  input.click();
}


async function handleMemoryImport(
  event
) {
  const file =
    event &&
    event.target &&
    event.target.files &&
    event.target.files[0];

  if (!file) return;

  try {
    const text =
      await file.text();

    const parsed =
      JSON.parse(text);

    const memory =
      parsed.memory ||
      parsed;

    const normalized =
      normalizeMemory(
        memory
      );

    await saveLocalMemory(
      normalized
    );

    notify(
      MIRROR.language === "es"
        ? "Tu memoria fue restaurada en este dispositivo."
        : "Your memory was restored on this device.",
      "success"
    );
  } catch (error) {
    console.error(
      "Memory import error:",
      error
    );

    notify(
      MIRROR.language === "es"
        ? "El archivo de memoria no es válido."
        : "The memory file is not valid.",
      "error"
    );
  } finally {
    event.target.value = "";
  }
}


/* ============================================================
   MEMORY STATUS
   ============================================================ */

function updateMemoryStatus() {
  const element =
    $("memoryStatus");

  if (!element) return;

  const history =
    MIRROR.memory &&
    Array.isArray(
      MIRROR.memory.history
    )
      ? MIRROR.memory.history.length
      : 0;

  const core =
    MIRROR.memory &&
    MIRROR.memory.core
      ? Object.keys(
          MIRROR.memory.core
        ).length
      : 0;

  if (
    history ||
    core
  ) {
    element.textContent =
      MIRROR.language === "es"
        ? "Tu MIRROR está aprendiendo de tus preferencias."
        : "Your MIRROR is learning from your preferences.";
  } else {
    element.textContent =
      MIRROR.language === "es"
        ? "Tu memoria MIRROR vive en este dispositivo."
        : "Your MIRROR memory lives on this device.";
  }
}


/* ============================================================
   INITIALIZATION
   ============================================================ */

async function initializeMirror() {
  getDeviceId();
  loadLanguagePreference();

  let memory =
    await getLocalMemory();

  if (!memory) {
    memory =
      defaultMemory();

    await saveLocalMemory(
      memory
    );
  } else {
    MIRROR.memory =
      normalizeMemory(
        memory
      );
  }

  updateMemoryStatus();

  setupSpeechRecognition();

  await loadConfig();

  await renderMissions();

  bindInterface();

  updateMemoryStatus();
}


/* ============================================================
   EVENT BINDING
   ============================================================ */

function bindInterface() {
  const input =
    $("mirrorInput");

  if (input) {
    input.addEventListener(
      "input",
      () => autoResizeInput(
        input
      )
    );

    input.addEventListener(
      "keydown",
      handleInputKeydown
    );
  }

  const askButtons = [
    $("askMirrorButton"),
    $("askButton")
  ];

  askButtons.forEach(button => {
    if (!button) return;

    button.addEventListener(
      "click",
      () => askMirror()
    );
  });

  const voiceButtons = [
    $("voiceButton"),
    $("micButton"),
    $("voiceInputButton")
  ];

  voiceButtons.forEach(button => {
    if (!button) return;

    button.addEventListener(
      "click",
      toggleVoice
    );
  });

  const clearButton =
    $("clearButton") ||
    $("clearInputButton");

  if (clearButton) {
    clearButton.addEventListener(
      "click",
      clearInput
    );
  }

  const speakButtons = [
    $("speakButton"),
    $("responseSpeakButton")
  ];

  speakButtons.forEach(button => {
    if (!button) return;

    button.addEventListener(
      "click",
      toggleSpeak
    );
  });

  const rightButtons = [
    $("rightButton"),
    $("thisFeelsRightButton")
  ];

  rightButtons.forEach(button => {
    if (!button) return;

    button.addEventListener(
      "click",
      () => submitFeedback(
        "POSITIVE"
      )
    );
  });

  const differentButtons = [
    $("reviseButton"),
    $("makeDifferentButton")
  ];

  differentButtons.forEach(button => {
    if (!button) return;

    button.addEventListener(
      "click",
      () => {
        submitFeedback(
          "NEGATIVE"
        );

        revisePlan();
      }
    );
  });

  const conciergeButtons = [
    $("conciergeButton"),
    $("letConciergeButton")
  ];

  conciergeButtons.forEach(button => {
    if (!button) return;

    button.addEventListener(
      "click",
      sendToConcierge
    );
  });

  const mapsButton =
    $("openMapsButton");

  if (mapsButton) {
    mapsButton.addEventListener(
      "click",
      openMaps
    );
  }

  const moodButton =
    $("playMoodButton");

  if (moodButton) {
    moodButton.addEventListener(
      "click",
      playMood
    );
  }

  const recoveryButtons = [
    $("rebuildMirrorButton"),
    $("recoverMemoryButton")
  ];

  recoveryButtons.forEach(button => {
    if (!button) return;

    button.addEventListener(
      "click",
      openRecovery
    );
  });

  const recoveryCloseButtons = [
    $("closeRecoveryButton"),
    $("recoveryCloseButton")
  ];

  recoveryCloseButtons.forEach(button => {
    if (!button) return;

    button.addEventListener(
      "click",
      closeRecovery
    );
  });

  const recoverySaveButtons = [
    $("saveRecoveryButton"),
    $("recoverySaveButton")
  ];

  recoverySaveButtons.forEach(button => {
    if (!button) return;

    button.addEventListener(
      "click",
      saveRecovery
    );
  });

  const backupButtons = [
    $("backupMemoryButton"),
    $("exportMemoryButton")
  ];

  backupButtons.forEach(button => {
    if (!button) return;

    button.addEventListener(
      "click",
      exportMemory
    );
  });

  const restoreButtons = [
    $("restoreMemoryButton"),
    $("importMemoryButton")
  ];

  restoreButtons.forEach(button => {
    if (!button) return;

    button.addEventListener(
      "click",
      importMemory
    );
  });

  const fileInput =
    $("memoryFileInput") ||
    $("restoreMemoryInput");

  if (fileInput) {
    fileInput.addEventListener(
      "change",
      handleMemoryImport
    );
  }

  bindSuggestionButtons();

  bindModalOutsideClick();
}


/* ============================================================
   SUGGESTIONS
   ============================================================ */

function bindSuggestionButtons() {
  const suggestions =
    document.querySelectorAll(
      "[data-mirror-prompt]"
    );

  suggestions.forEach(button => {
    button.addEventListener(
      "click",
      () => {
        const prompt =
          safeText(
            button.dataset.mirrorPrompt
          );

        if (!prompt) return;

        const input =
          $("mirrorInput");

        if (input) {
          input.value =
            prompt;

          autoResizeInput(
            input
          );

          input.focus();
        }
      }
    );
  });

  /*
  Compatibility with the original suggestion chips.
  */

  const chips =
    document.querySelectorAll(
      ".suggestion-chip, .prompt-chip"
    );

  chips.forEach(chip => {
    if (
      chip.dataset.boundMirror
    ) {
      return;
    }

    chip.dataset.boundMirror =
      "true";

    chip.addEventListener(
      "click",
      () => {
        const text =
          safeText(
            chip.dataset.prompt ||
            chip.dataset.mirrorPrompt ||
            chip.textContent
          );

        if (!text) return;

        const input =
          $("mirrorInput");

        if (!input) return;

        input.value =
          text;

        autoResizeInput(
          input
        );

        input.focus();
      }
    );
  });
}


/* ============================================================
   MODAL BEHAVIOR
   ============================================================ */

function bindModalOutsideClick() {
  const modal =
    $("recoveryModal");

  if (!modal) return;

  modal.addEventListener(
    "click",
    event => {
      if (
        event.target === modal
      ) {
        closeRecovery();
      }
    }
  );
}


/* ============================================================
   PAGE VISIBILITY
   ============================================================ */

document.addEventListener(
  "visibilitychange",
  () => {
    if (
      document.hidden &&
      MIRROR.listening &&
      MIRROR.recognition
    ) {
      try {
        MIRROR.recognition.stop();
      } catch (_) {}
    }
  }
);


/* ============================================================
   GLOBAL PUBLIC API
   ============================================================ */

window.MIRROR = MIRROR;

window.askMirror =
  askMirror;

window.toggleVoice =
  toggleVoice;

window.toggleSpeak =
  toggleSpeak;

window.stopSpeaking =
  stopSpeaking;

window.clearInput =
  clearInput;

window.openRecovery =
  openRecovery;

window.closeRecovery =
  closeRecovery;

window.saveRecovery =
  saveRecovery;

window.exportMemory =
  exportMemory;

window.importMemory =
  importMemory;

window.handleMemoryImport =
  handleMemoryImport;

window.openMaps =
  openMaps;

window.playMood =
  playMood;

window.submitFeedback =
  submitFeedback;

window.revisePlan =
  revisePlan;

window.sendToConcierge =
  sendToConcierge;

window.renderMissions =
  renderMissions;


/* ============================================================
   START
   ============================================================ */

if (
  document.readyState ===
  "loading"
) {
  document.addEventListener(
    "DOMContentLoaded",
    initializeMirror,
    {
      once: true
    }
  );
} else {
  initializeMirror();
}
```
