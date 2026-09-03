const $ = s => document.querySelector(s);
const API = "/api";

let memory = {
core: {},
moment: {},
preferences: {},
dislikes: [],
history: [],
learning: {}
};

let currentMission = null;
let recognition = null;
let listening = false;

const dbName = "mirror_to_you_memory";
const storeName = "memory";

function id() {
return localStorage.getItem("mirror_device_id") ||
(() => {
const v = crypto.randomUUID ? crypto.randomUUID() : "device_" + Date.now();
localStorage.setItem("mirror_device_id", v);
return v;
})();
}

function normalizeMemory(data) {
const m = data && typeof data === "object" ? {...data} : {};

if (!m.core || typeof m.core !== "object" || Array.isArray(m.core)) m.core = {};
if (!m.moment || typeof m.moment !== "object" || Array.isArray(m.moment)) m.moment = {};

if (!m.preferences || typeof m.preferences !== "object" || Array.isArray(m.preferences)) {
m.preferences = {};
}

if (!Array.isArray(m.dislikes)) m.dislikes = [];
if (!Array.isArray(m.history)) m.history = [];
if (!m.learning || typeof m.learning !== "object" || Array.isArray(m.learning)) {
m.learning = {};
}

return {
core: m.core,
moment: m.moment,
preferences: m.preferences,
dislikes: m.dislikes,
history: m.history,
learning: m.learning,
...(m.recovered_at ? {recovered_at: m.recovered_at} : {})
};
}

function openDB() {
return new Promise((resolve, reject) => {
const r = indexedDB.open(dbName, 1);

```
r.onupgradeneeded = () => {
  if (!r.result.objectStoreNames.contains(storeName)) {
    r.result.createObjectStore(storeName);
  }
};

r.onsuccess = () => resolve(r.result);
r.onerror = () => reject(r.error);
```

});
}

async function loadMemory() {
try {
const db = await openDB();

```
return await new Promise(resolve => {
  const r = db
    .transaction(storeName)
    .objectStore(storeName)
    .get("profile");

  r.onsuccess = () => resolve(normalizeMemory(r.result || memory));
  r.onerror = () => resolve(normalizeMemory(memory));
});
```

} catch {
return normalizeMemory(memory);
}
}

async function saveMemory(data) {
memory = normalizeMemory({
...memory,
...(data || {})
});

try {
const db = await openDB();

```
db.transaction(storeName, "readwrite")
  .objectStore(storeName)
  .put(memory, "profile");
```

} catch {}
}

async function api(path, options = {}) {
const r = await fetch(API + path, {
headers: {"Content-Type": "application/json"},
...options
});

const data = await r.json().catch(() => ({}));

if (!r.ok) {
throw new Error(
data.error ||
data.detail ||
`MIRROR could not complete the request (${r.status}).`
);
}

return data;
}

function language() {
return navigator.language?.toLowerCase().startsWith("es") ? "es" : "en";
}

function setText(selector, text) {
const el = $(selector);
if (el) el.textContent = text || "";
}

function speak(text) {
if (!("speechSynthesis" in window) || !text) return;

speechSynthesis.cancel();

const u = new SpeechSynthesisUtterance(text);
u.lang = language() === "es" ? "es-US" : "en-US";
u.rate = .95;

speechSynthesis.speak(u);
}

function showStatus(text) {
const el = $("#conciergeStatus");

if (el) {
el.textContent = text || "";
el.hidden = !text;
}
}

function renderPlan(plan, mission) {
currentMission = mission;

if (!plan) return;

const panel = $("#planPanel");
if (panel) panel.hidden = false;

setText("#planTitle", plan.title);
setText("#missionId", mission?.id || "");
setText("#planCategory", plan.category || "MIRROR");
setText("#planPrivacy", plan.privacy || "HIGH");
setText("#planPriority", plan.priority || "NORMAL");

setText(
"#planBudget",
plan.budget == null
? "Not specified"
: `$${Number(plan.budget).toLocaleString()}`
);

setText(
"#planDestination",
plan.destination || "MIRROR is deciding"
);

const details = $("#planDetails");

if (details) {
details.innerHTML = "";

```
const values = [
  plan.duration && `Duration: ${plan.duration}`,
  plan.companion && `For: ${plan.companion.toLowerCase()}`,
  plan.confidence != null && `Confidence: ${plan.confidence}%`
].filter(Boolean);

values.forEach(v => {
  const li = document.createElement("li");
  li.textContent = v;
  details.appendChild(li);
});
```

}

const steps = $("#planSteps");

if (steps) {
steps.innerHTML = "";

```
(plan.direction || []).forEach((step, i) => {
  const li = document.createElement("li");
  const span = document.createElement("span");
  const strong = document.createElement("strong");

  span.textContent = i + 1;
  strong.textContent = step;

  li.append(span, strong);
  steps.appendChild(li);
});
```

}
}

function renderUnderstanding(data) {
const box = $("#understandingPanel");

if (!box || !data) return;

box.hidden = false;

const items = [
["Intent", data.intent?.replaceAll("_", " ")],
["Privacy", data.privacy],
["Priority", data.priority],
["Destination", data.destination],
["Duration", data.duration],
["Companion", data.companion]
].filter(x => x[1]);

box.innerHTML = items.map(
([a, b]) =>
`<div><small>${a}</small><strong>${b}</strong></div>`
).join("");
}

async function askMirror() {
const input = $("#requestInput") || $("#message");
const text = input?.value.trim();

if (!text) {
input?.focus();
return;
}

const button = $("#askMirrorButton") || $("#askButton");

if (button) button.disabled = true;

showStatus("MIRROR is understanding your request…");

try {
memory = normalizeMemory(memory);

```
const result = await api("/mirror", {
  method: "POST",
  body: JSON.stringify({
    message: text,
    memory,
    language: language(),
    voice_enabled: false,
    client_device_id: id()
  })
});

currentMission = result.mission;

await saveMemory(result.memory || memory);

setText("#mirrorResponse", result.message);

const response = $("#responsePanel");
if (response) response.hidden = false;

renderUnderstanding(
  result.analysis ||
  result.understanding ||
  result.mission?.analysis
);

renderPlan(
  result.plan ||
  result.mission?.plan,
  result.mission
);

showStatus(
  result.plan?.status === "PROPOSAL"
    ? "Your proposal is ready."
    : "MIRROR needs one small clarification before deciding."
);

speak(result.message);
```

} catch (e) {
setText("#mirrorResponse", e.message);

```
const response = $("#responsePanel");
if (response) response.hidden = false;

showStatus("");
```

} finally {
if (button) button.disabled = false;
}
}

async function feedback(accepted, text = "") {
if (!currentMission?.id) return;

try {
memory = normalizeMemory(memory);

```
const result = await api("/missions/feedback", {
  method: "POST",
  body: JSON.stringify({
    mission_id: currentMission.id,
    accepted,
    feedback: text,
    memory
  })
});

if (result.memory) {
  await saveMemory(result.memory);
}

showStatus(
  accepted
    ? "MIRROR has saved your preference."
    : "MIRROR will use your feedback to make the next proposal different."
);

await loadMissions();
```

} catch (e) {
showStatus(e.message);
}
}

async function revise() {
if (!currentMission?.id) return;

const text = prompt(
language() === "es"
? "¿Qué quieres cambiar?"
: "What would you like MIRROR to change?"
);

if (!text?.trim()) return;

try {
memory = normalizeMemory(memory);

```
const result = await api("/missions/revise", {
  method: "POST",
  body: JSON.stringify({
    mission_id: currentMission.id,
    instruction: text.trim(),
    memory
  })
});

if (result.memory) {
  await saveMemory(result.memory);
}

if (result.plan) {
  renderPlan(result.plan, result.mission || currentMission);
}

if (result.analysis) {
  renderUnderstanding(result.analysis);
}

if (result.message) {
  setText("#mirrorResponse", result.message);
  speak(result.message);
}

showStatus(
  result.message ||
  "MIRROR is revising the proposal."
);
```

} catch (e) {
showStatus(e.message);
}
}

async function sendConcierge() {
if (!currentMission?.id) return;

try {
memory = normalizeMemory(memory);

```
const result = await api(
  `/missions/${currentMission.id}/concierge`,
  {
    method: "POST",
    body: JSON.stringify({
      note: "",
      memory
    })
  }
);

showStatus(result.message);

await loadMissions();
```

} catch (e) {
showStatus(e.message);
}
}

async function openMaps() {
const destination =
currentMission?.plan?.destination ||
$("#planDestination")?.textContent;

if (
!destination ||
destination === "MIRROR is deciding"
) return;

try {
const result = await api(
`/maps?destination=${encodeURIComponent(destination)}`
);

```
if (result.url) {
  window.open(
    result.url,
    "_blank",
    "noopener"
  );
}
```

} catch {}
}

async function playMood() {
const category =
currentMission?.plan?.category ||
"luxury relaxing";

const query = `${category} relaxing music`;

try {
const result = await api(
`/music?query=${encodeURIComponent(query)}`
);

```
if (result.url) {
  window.open(
    result.url,
    "_blank",
    "noopener"
  );
}
```

} catch {}
}

async function loadMissions() {
const box = $("#missionsList");

if (!box) return;

try {
const result = await api("/missions");

```
box.innerHTML = "";

(result.missions || []).forEach(m => {
  const item = document.createElement("div");
  item.className = "mission-item";

  const strong = document.createElement("strong");
  strong.textContent = m.request || "MIRROR Mission";

  const small = document.createElement("small");
  small.textContent = m.status || "";

  item.append(strong, small);
  box.appendChild(item);
});
```

} catch {}
}

function setupVoice() {
const SpeechRecognition =
window.SpeechRecognition ||
window.webkitSpeechRecognition;

const button = $("#voiceButton");

if (!SpeechRecognition || !button) {
if (button) button.hidden = true;
return;
}

recognition = new SpeechRecognition();

recognition.lang =
language() === "es"
? "es-US"
: "en-US";

recognition.continuous = false;
recognition.interimResults = true;

recognition.onstart = () => {
listening = true;

```
button.classList.add("listening");
button.setAttribute(
  "aria-label",
  "Stop listening"
);
```

};

recognition.onresult = e => {
const text = [...e.results]
.map(r => r[0].transcript)
.join("");

```
const input =
  $("#requestInput") ||
  $("#message");

if (input) input.value = text;
```

};

recognition.onend = () => {
listening = false;

```
button.classList.remove("listening");

button.setAttribute(
  "aria-label",
  "Speak to MIRROR"
);
```

};

recognition.onerror = () => {
listening = false;
button.classList.remove("listening");
};

button.addEventListener("click", () => {
if (listening) recognition.stop();
else recognition.start();
});
}

async function recovery() {
try {
const result = await api(
"/memory/recovery/questions"
);

```
const modal = $("#recoveryModal");
const box = $("#recoveryQuestions");

if (!modal || !box) return;

const questions = Array.isArray(result.questions)
  ? result.questions
  : [];

box.innerHTML = questions.map(q => `
  <div class="recovery-question">
    <strong>${q.question || ""}</strong>
    <div class="recovery-options">
      ${(Array.isArray(q.options) ? q.options : [])
        .map(o => `
          <button
            type="button"
            data-q="${q.id}"
            data-value="${o}">
            ${o}
          </button>
        `).join("")}
    </div>
  </div>
`).join("");

box.querySelectorAll("button").forEach(b => {
  b.onclick = () => {
    box
      .querySelectorAll(
        `[data-q="${b.dataset.q}"]`
      )
      .forEach(x =>
        x.classList.remove("selected")
      );

    b.classList.add("selected");
  };
});

modal.hidden = false;
```

} catch (e) {
showStatus(e.message);
}
}

async function saveRecovery() {
const box = $("#recoveryQuestions");

if (!box) return;

const answers = {};

box
.querySelectorAll(".selected")
.forEach(b => {
answers[b.dataset.q] = b.dataset.value;
});

if (!Object.keys(answers).length) {
showStatus(
language() === "es"
? "Selecciona al menos una respuesta."
: "Choose at least one answer."
);
return;
}

try {
memory = normalizeMemory(memory);

```
const result = await api(
  "/memory/recovery",
  {
    method: "POST",
    body: JSON.stringify({
      answers,
      memory
    })
  }
);

if (result.memory) {
  await saveMemory(result.memory);
}

const modal = $("#recoveryModal");

if (modal) {
  modal.hidden = true;
}

showStatus(
  result.message ||
  "Your MIRROR experience has been rebuilt."
);
```

} catch (e) {
showStatus(e.message);
}
}

function closeRecovery() {
const modal = $("#recoveryModal");

if (modal) {
modal.hidden = true;
}
}

async function backupMemory() {
memory = normalizeMemory(memory);

const blob = new Blob(
[
JSON.stringify(
{
format: "MIRROR-TO-YOU",
version: 2,
memory
},
null,
2
)
],
{type: "application/json"}
);

const a = document.createElement("a");

a.href = URL.createObjectURL(blob);
a.download = "mirror-to-you-memory.json";

a.click();

URL.revokeObjectURL(a.href);
}

function restoreMemory() {
$("#memoryFile")?.click();
}

async function handleRestore(e) {
const file = e.target.files?.[0];

if (!file) return;

try {
const data =
JSON.parse(await file.text());

```
if (!data.memory) {
  throw new Error(
    "Invalid MIRROR memory file."
  );
}

await saveMemory(data.memory);

showStatus(
  "Your MIRROR memory has been restored."
);
```

} catch (err) {
showStatus(err.message);
}

e.target.value = "";
}

function clearRequest() {
const input =
$("#requestInput") ||
$("#message");

if (input) {
input.value = "";
input.focus();
}
}

function bind(idName, fn) {
const el = document.getElementById(idName);

if (el) {
el.addEventListener("click", fn);
}
}

document.addEventListener(
"DOMContentLoaded",
async () => {
memory = normalizeMemory(
await loadMemory()
);

```
bind(
  "askMirrorButton",
  askMirror
);

bind(
  "askButton",
  askMirror
);

bind(
  "clearButton",
  clearRequest
);

bind(
  "speakButton",
  () =>
    speak(
      $("#mirrorResponse")
        ?.textContent || ""
    )
);

bind(
  "thisFeelsRightButton",
  () => feedback(true)
);

bind(
  "makeDifferentButton",
  revise
);

bind(
  "conciergeButton",
  sendConcierge
);

bind(
  "openMapsButton",
  openMaps
);

bind(
  "playMoodButton",
  playMood
);

bind(
  "rebuildMemoryButton",
  recovery
);

bind(
  "backupMemoryButton",
  backupMemory
);

bind(
  "restoreMemoryButton",
  restoreMemory
);

bind(
  "closeRecoveryButton",
  closeRecovery
);

bind(
  "saveRecoveryButton",
  saveRecovery
);

bind(
  "memoryFile",
  handleRestore
);

document
  .querySelectorAll("[data-request]")
  .forEach(button => {
    button.addEventListener(
      "click",
      () => {
        const input =
          $("#requestInput") ||
          $("#message");

        if (!input) return;

        input.value =
          button.dataset.request;

        input.focus();
      }
    );
  });

const input =
  $("#requestInput") ||
  $("#message");

input?.addEventListener(
  "keydown",
  e => {
    if (
      (e.ctrlKey || e.metaKey) &&
      e.key === "Enter"
    ) {
      askMirror();
    }
  }
);

setupVoice();

await loadMissions();

try {
  await api("/health");
} catch {
  showStatus(
    "MIRROR is temporarily unavailable."
  );
}
```

}
);
