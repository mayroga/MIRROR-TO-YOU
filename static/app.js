const API_BASE=window.MIRROR_CONFIG?.apiBase||"";
let memory=null;
let currentMissionId=null;
let recognition=null;
let currentLanguage="en";

const $=id=>document.getElementById(id);
const api=(url,options={})=>fetch(`${API_BASE}${url}`,{
headers:{"Content-Type":"application/json",...(options.headers||{})},
...options
}).then(async r=>{
const data=await r.json().catch(()=>({}));
if(!r.ok)throw new Error(data.detail||data.message||"Request failed");
return data;
});

function deviceId(){
let id=localStorage.getItem("mirror_device_id");
if(!id){
id=crypto?.randomUUID?crypto.randomUUID():`mirror-${Date.now()}-${Math.random().toString(36).slice(2)}`;
localStorage.setItem("mirror_device_id",id);
}
return id;
}

function defaultMemory(){
return{
core:{},
moment:{},
preferences:{},
dislikes:[],
history:[],
learning:{}
};
}

function normalizeMemory(data){
const m=data&&typeof data==="object"?data:{};
return{
core:m.core&&typeof m.core==="object"?m.core:{},
moment:m.moment&&typeof m.moment==="object"?m.moment:{},
preferences:m.preferences&&typeof m.preferences==="object"?m.preferences:{},
dislikes:Array.isArray(m.dislikes)?m.dislikes:[],
history:Array.isArray(m.history)?m.history:[],
learning:m.learning&&typeof m.learning==="object"?m.learning:{}
};
}

function openDB(){
return new Promise((resolve,reject)=>{
const request=indexedDB.open("mirror_to_you",1);
request.onupgradeneeded=()=>{
const db=request.result;
if(!db.objectStoreNames.contains("memory"))db.createObjectStore("memory");
};
request.onsuccess=()=>resolve(request.result);
request.onerror=()=>reject(request.error);
});
}

async function loadMemory(){
try{
const db=await openDB();
const value=await new Promise((resolve,reject)=>{
const tx=db.transaction("memory","readonly");
const req=tx.objectStore("memory").get("client_memory");
req.onsuccess=()=>resolve(req.result);
req.onerror=()=>reject(req.error);
});
db.close();
memory=normalizeMemory(value||defaultMemory());
}catch(e){
memory=normalizeMemory(JSON.parse(localStorage.getItem("mirror_memory")||"null"));
}
return memory;
}

async function saveMemory(data){
memory=normalizeMemory(data);
try{
const db=await openDB();
await new Promise((resolve,reject)=>{
const tx=db.transaction("memory","readwrite");
tx.objectStore("memory").put(memory,"client_memory");
tx.oncomplete=resolve;
tx.onerror=()=>reject(tx.error);
});
db.close();
}catch(e){
localStorage.setItem("mirror_memory",JSON.stringify(memory));
}
}

function language(){
return document.documentElement.lang==="es"?"es":"en";
}

function setText(id,text){
const el=$(id);
if(el&&text!==undefined&&text!==null)el.textContent=String(text);
}

function show(id,visible=true){
const el=$(id);
if(el)el.classList.toggle("hidden",!visible);
}

function escapeHTML(value){
return String(value??"").replace(/[&<>"']/g,c=>({
"&":"&",
"<":"<",
">":">",
'"':""",
"'":"'"
}[c]));
}

function cleanText(value){
if(value===undefined||value===null)return"";
if(typeof value==="string")return value.trim();
if(Array.isArray(value))return value.map(cleanText).filter(Boolean).join(" ");
return String(value).trim();
}

function formatValue(value){
if(value===undefined||value===null||value==="")return"";
if(typeof value==="string")return value;
if(Array.isArray(value))return value.join(", ");
if(typeof value==="object"){
return Object.values(value).filter(v=>v!==null&&v!==undefined&&v!=="").join(", ");
}
return String(value);
}

function speak(text){
if(!window.speechSynthesis||!text)return;
try{
window.speechSynthesis.cancel();
const utterance=new SpeechSynthesisUtterance(cleanText(text));
utterance.lang=language()==="es"?"es-US":"en-US";
utterance.rate=.94;
utterance.pitch=1;
window.speechSynthesis.speak(utterance);
}catch(e){}
}

function showToast(message){
const toast=$("toast");
if(!toast)return;
toast.textContent=message;
toast.classList.remove("hidden");
clearTimeout(window.mirrorToastTimer);
window.mirrorToastTimer=setTimeout(()=>toast.classList.add("hidden"),3500);
}

function showStatus(message,type=""){
const status=$("responseStatus");
if(!status)return;
status.textContent=message||"";
status.className=`response-status ${type}`.trim();
if(!message)status.classList.add("hidden");
else status.classList.remove("hidden");
}

function resetPlanFields(){
[
"planDestinationWrap",
"planBudgetWrap",
"planPrivacyWrap",
"planPriorityWrap",
"mapsBtn",
"musicBtn",
"planQuestions"
].forEach(id=>show(id,false));

setText("planDestination","");
setText("planBudget","");
setText("planPrivacy","");
setText("planPriority","");
setText("planDetails","");
setText("planSteps","");
setText("planQuestions","");
setText("planDirection","");
}

function renderUnderstanding(data){
if(!data||typeof data!=="object"){
show("understandingSection",false);
return;
}

const u=data.understanding||data;
const companion=formatValue(u.companion);
const duration=formatValue(u.duration);
const destination=formatValue(u.destination);

const parts=[];
if(companion)parts.push(companion);
if(duration)parts.push(duration);
if(destination)parts.push(destination);

setText("understandingText",
cleanText(
u.summary||
u.direction||
u.need||
u.intent||
(language()==="es"?"Estoy entendiendo lo que necesitas.":"I'm understanding what you need.")
)
);

setText("understandingCompanion",companion);
setText("understandingDuration",duration);
setText("understandingDestination",destination);

show("understandingCompanion",!!companion);
show("understandingDuration",!!duration);
show("understandingDestination",!!destination);
show("understandingSection",true);
}

function renderSteps(steps){
const container=$("planSteps");
if(!container)return;
container.innerHTML="";

if(!steps){
container.classList.add("hidden");
return;
}

let list=Array.isArray(steps)?steps:[steps];
list=list.map(cleanText).filter(Boolean);

if(!list.length){
container.classList.add("hidden");
return;
}

list.forEach((step,index)=>{
const item=document.createElement("div");
item.className="plan-step";
item.innerHTML=`<span class="plan-step-number">${String(index+1).padStart(2,"0")}</span> <span class="plan-step-text">${escapeHTML(step)}</span>`;
container.appendChild(item);
});

container.classList.remove("hidden");
}

function renderQuestions(questions){
const container=$("planQuestions");
if(!container)return;

container.innerHTML="";
const list=Array.isArray(questions)?questions:[questions];
const valid=list.map(cleanText).filter(Boolean);

if(!valid.length){
show("planQuestions",false);
return;
}

valid.forEach(question=>{
const item=document.createElement("div");
item.className="plan-question";
item.textContent=question;
container.appendChild(item);
});

show("planQuestions",true);
}

function renderPlan(plan){
if(!plan||typeof plan!=="object"){
show("planSection",false);
return;
}

resetPlanFields();

const title=cleanText(plan.title)||
(language()==="es"?"Algo pensado para ti":"Something made for you");

const direction=cleanText(plan.direction);
const destination=formatValue(plan.destination);
const budget=formatValue(plan.budget);
const privacy=formatValue(plan.privacy);
const priority=formatValue(plan.priority);
const details=cleanText(plan.details||plan.description||plan.summary);

setText("planTitle",title);
setText("planDirection",direction);
setText("planDetails",details);

if(destination){
setText("planDestination",destination);
show("planDestinationWrap",true);
}

if(budget){
setText("planBudget",budget);
show("planBudgetWrap",true);
}

if(privacy){
setText("planPrivacy",privacy);
show("planPrivacyWrap",true);
}

if(priority){
setText("planPriority",priority);
show("planPriorityWrap",true);
}

renderSteps(plan.steps||plan.actions||plan.next_steps);
renderQuestions(plan.questions);

currentMissionId=plan.mission_id||plan.id||currentMissionId;

if(destination){
show("mapsBtn",true);
$("mapsBtn").dataset.destination=destination;
}

if(plan.music||plan.mood||plan.music_query){
show("musicBtn",true);
$("musicBtn").dataset.query=formatValue(plan.music||plan.mood||plan.music_query);
}

show("planSection",true);
}

function renderResponse(data){
const text=cleanText(data?.message||data?.response||data?.text);

if(text){
setText("responseText",text);
show("responseSection",true);
}else{
show("responseSection",false);
}

showStatus("", "");
}

function updateMemoryFromResponse(data){
if(data?.memory){
saveMemory(data.memory);
return;
}

if(!memory)return;

if(data?.analysis?.memory)memory=normalizeMemory(data.analysis.memory);
saveMemory(memory);
}

async function askMirror(){
const input=$("messageInput");
const button=$("askBtn");
if(!input||!button)return;

const message=input.value.trim();
if(!message){
input.focus();
showToast(language()==="es"?"Dime qué necesitas.":"Tell me what you need.");
return;
}

button.disabled=true;
button.classList.add("loading");
showStatus(language()==="es"?"Un momento…":"One moment…","working");
show("understandingSection",false);
show("planSection",false);

try{
if(!memory)await loadMemory();

const data=await api("/api/mirror",{
method:"POST",
body:JSON.stringify({
message,
memory,
language:language(),
voice_enabled:true,
client_device_id:deviceId()
})
});

renderResponse(data);
renderUnderstanding(data);
renderPlan(data?.plan||data?.proposal||data?.mission);
updateMemoryFromResponse(data);

if(data?.mission?.id)currentMissionId=data.mission.id;
if(data?.mission_id)currentMissionId=data.mission_id;

const response=cleanText(data?.message||data?.response);
if(response)speak(response);

input.value="";
showStatus("", "");
document.querySelector(".response-section")?.scrollIntoView({behavior:"smooth",block:"center"});
}catch(error){
console.error("MIRROR:",error);
showStatus(
language()==="es"
?"No pude completar esto en este momento. Inténtalo nuevamente."
:"I couldn't complete that right now. Please try again.",
"error"
);
showToast(language()==="es"?"MIRROR necesita otro intento.":"MIRROR needs another try.");
}finally{
button.disabled=false;
button.classList.remove("loading");
}
}

async function feedback(value){
if(!currentMissionId){
showToast(language()==="es"?"Primero crea una experiencia con MIRROR.":"Start an experience with MIRROR first.");
return;
}

try{
await api("/api/missions/feedback",{
method:"POST",
body:JSON.stringify({
mission_id:currentMissionId,
feedback:value,
memory:memory||defaultMemory()
})
});

if(value==="positive"){
showToast(language()==="es"?"Perfecto. MIRROR lo tendrá en cuenta.":"Perfect. MIRROR will keep that in mind.");
}else{
showToast(language()==="es"?"Vamos a buscar otra dirección.":"Let's take it in another direction.");
}
}catch(e){
console.error(e);
}
}

async function revise(){
const input=$("messageInput");
const message=input?.value.trim();

if(message){
await askMirror();
return;
}

if(!currentMissionId){
showToast(language()==="es"?"Dime qué quieres cambiar.":"Tell me what you'd like to change.");
input?.focus();
return;
}

const different=language()==="es"
?"Hazlo diferente. Sorpréndeme con otra dirección."
:"Make it different. Surprise me with another direction.";

try{
showStatus(language()==="es"?"Buscando otra posibilidad…":"Looking at another possibility…","working");

const data=await api("/api/missions/revise",{
method:"POST",
body:JSON.stringify({
mission_id:currentMissionId,
message:different,
memory:memory||defaultMemory(),
language:language()
})
});

renderResponse(data);
renderUnderstanding(data);
renderPlan(data?.plan||data?.proposal||data?.mission);
updateMemoryFromResponse(data);

const response=cleanText(data?.message||data?.response);
if(response)speak(response);

showStatus("", "");
}catch(e){
console.error(e);
showStatus(
language()==="es"
?"No pude cambiarlo ahora."
:"I couldn't change it right now.",
"error"
);
}
}

async function sendConcierge(){
if(!currentMissionId){
showToast(language()==="es"?"Primero dime qué necesitas.":"Tell me what you need first.");
return;
}

const button=$("conciergeBtn");
if(button)button.disabled=true;

try{
const data=await api(`/api/missions/${encodeURIComponent(currentMissionId)}/concierge`,{
method:"POST",
body:JSON.stringify({
memory:memory||defaultMemory(),
language:language()
})
});

const status=cleanText(
data?.message||
data?.status||
(language()==="es"
?"MIRROR ha preparado el siguiente paso."
:"MIRROR has prepared the next step.")
);

setText("conciergeStatus",status);
show("conciergeStatus",true);
showToast(status);
}catch(e){
console.error(e);
showToast(
language()==="es"
?"No fue posible activar el concierge ahora."
:"The concierge could not be activated right now."
);
}finally{
if(button)button.disabled=false;
}
}

function openMaps(){
const button=$("mapsBtn");
const destination=button?.dataset.destination;

if(!destination)return;

const url=`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(destination)}`;
window.open(url,"_blank","noopener,noreferrer");
}

function playMood(){
const button=$("musicBtn");
const query=button?.dataset.query||"relaxing elegant music";

const url=`https://www.youtube.com/results?search_query=${encodeURIComponent(query)}`;
window.open(url,"_blank","noopener,noreferrer");
}

async function loadMissions(){
try{
const data=await api("/api/missions");
const missions=Array.isArray(data)?data:(data?.missions||[]);
const list=$("missionsList");

if(!list||!missions.length){
show("missionsSection",false);
return;
}

list.innerHTML="";

missions.slice(0,8).forEach(mission=>{
const item=document.createElement("button");
item.type="button";
item.className="mission-item";

const title=cleanText(mission.title||mission.name||"MIRROR");
const direction=cleanText(mission.direction||mission.summary);

item.innerHTML=` <span class="mission-item-title">${escapeHTML(title)}</span>
${direction?`<span class="mission-item-text">${escapeHTML(direction)}</span>`:""}
`;

item.addEventListener("click",async()=>{
const id=mission.id||mission.mission_id;
if(!id)return;

try{
const data=await api(`/api/missions/${encodeURIComponent(id)}`);
currentMissionId=id;
renderResponse(data);
renderUnderstanding(data);
renderPlan(data.plan||data.proposal||data.mission);
document.querySelector(".plan-section")?.scrollIntoView({behavior:"smooth",block:"center"});
}catch(e){
console.error(e);
}
});

list.appendChild(item);
});

show("missionsSection",true);
}catch(e){
console.warn("Mission history unavailable:",e);
}
}

function startVoiceRecognition(){
const SpeechRecognition=window.SpeechRecognition||window.webkitSpeechRecognition;

if(!SpeechRecognition){
showToast(language()==="es"
?"El reconocimiento de voz no está disponible en este navegador."
:"Voice recognition is not available in this browser.");
return;
}

if(recognition){
try{
recognition.stop();
}catch(e){}
recognition=null;
}

recognition=new SpeechRecognition();
recognition.lang=language()==="es"?"es-US":"en-US";
recognition.interimResults=true;
recognition.continuous=false;

const button=$("voiceBtn");
button?.classList.add("listening");

recognition.onresult=event=>{
let transcript="";
for(let i=event.resultIndex;i<event.results.length;i++){
transcript+=event.results[i][0].transcript;
}
const input=$("messageInput");
if(input)input.value=transcript.trim();
};

recognition.onerror=event=>{
console.warn("Speech recognition:",event.error);
};

recognition.onend=()=>{
button?.classList.remove("listening");
recognition=null;
};

try{
recognition.start();
}catch(e){
button?.classList.remove("listening");
recognition=null;
}
}

async function loadRecoveryQuestions(){
const container=$("recoveryQuestions");
if(!container)return;

container.innerHTML=`

<div class="recovery-loading">
${language()==="es"?"Preparando unas preguntas sencillas…":"Preparing a few simple questions…"}
</div>`;

try{
const data=await api(`/api/memory/recovery/questions?language=${encodeURIComponent(language())}`);
const questions=Array.isArray(data)?data:(data?.questions||[]);

container.innerHTML="";

questions.forEach((question,index)=>{
const text=cleanText(question.question||question.text||question);
const options=Array.isArray(question.options)?question.options:[];

const wrapper=document.createElement("div");
wrapper.className="recovery-question";
wrapper.dataset.index=index;

wrapper.innerHTML=`

<div class="recovery-question-title">${escapeHTML(text)}</div>
<div class="recovery-options"></div>
`;

const optionsBox=wrapper.querySelector(".recovery-options");

if(options.length){
options.forEach(option=>{
const btn=document.createElement("button");
btn.type="button";
btn.className="recovery-option";
btn.textContent=cleanText(option.label||option.value||option);

btn.dataset.value=cleanText(option.value||option.label||option);

btn.addEventListener("click",()=>{
wrapper.querySelectorAll(".recovery-option").forEach(x=>x.classList.remove("selected"));
btn.classList.add("selected");
});

optionsBox.appendChild(btn);
});
}else{
const field=document.createElement("input");
field.type="text";
field.className="recovery-input";
field.placeholder=language()==="es"?"Tu respuesta…":"Your answer…";
field.dataset.input="true";
wrapper.appendChild(field);
}

container.appendChild(wrapper);
});

if(!questions.length){
container.innerHTML=`

<div class="recovery-question">
<div class="recovery-question-title">
${language()==="es"
?"Cuéntame qué tipo de experiencia prefieres."
:"Tell me what kind of experience you prefer."}
</div>
<input id="recoveryFallback" class="recovery-input" type="text">
</div>`;
}
}catch(e){
console.error(e);
container.innerHTML=`
<div class="recovery-question">
<div class="recovery-question-title">
${language()==="es"
?"¿Qué debería saber MIRROR sobre la experiencia que quieres?"
:"What should MIRROR know about the experience you want?"}
</div>
<input id="recoveryFallback" class="recovery-input" type="text">
</div>`;
}
}

function openRecovery(){
show("recoveryModal",true);
loadRecoveryQuestions();
}

function closeRecovery(){
show("recoveryModal",false);
}

async function submitRecovery(){
const container=$("recoveryQuestions");
if(!container)return;

const answers={};

container.querySelectorAll(".recovery-question").forEach((question,index)=>{
const selected=question.querySelector(".recovery-option.selected");
const input=question.querySelector("input");

if(selected)answers[String(index)]=selected.dataset.value||selected.textContent;
else if(input?.value.trim())answers[String(index)]=input.value.trim();
});

try{
const data=await api("/api/memory/recovery",{
method:"POST",
body:JSON.stringify({
answers,
memory:memory||defaultMemory(),
language:language(),
client_device_id:deviceId()
})
});

if(data?.memory){
memory=normalizeMemory(data.memory);
await saveMemory(memory);
}

closeRecovery();

const message=data?.message||
(language()==="es"
?"Tu experiencia ha sido reconstruida."
:"Your experience has been restored.");

setText("memoryStatus",message);
showToast(message);
}catch(e){
console.error(e);
showToast(
language()==="es"
?"No pude restaurar la experiencia todavía."
:"I couldn't restore the experience yet."
);
}
}

async function backupMemory(){
try{
if(!memory)await loadMemory();

const payload={
product:"MIRROR TO YOU",
version:1,
created_at:new Date().toISOString(),
memory
};

const blob=new Blob([JSON.stringify(payload,null,2)],{type:"application/json"});
const url=URL.createObjectURL(blob);
const a=document.createElement("a");
a.href=url;
a.download=`mirror-to-you-backup-${new Date().toISOString().slice(0,10)}.json`;
document.body.appendChild(a);
a.click();
a.remove();
URL.revokeObjectURL(url);

const message=language()==="es"?"Copia de MIRROR creada.":"MIRROR backup created.";
setText("memoryStatus",message);
showToast(message);
}catch(e){
console.error(e);
showToast(language()==="es"?"No se pudo crear la copia.":"Backup could not be created.");
}
}

function restoreFile(){
const input=$("restoreFile");
if(!input)return;

input.onchange=async()=>{
const file=input.files?.[0];
if(!file)return;

try{
const text=await file.text();
const data=JSON.parse(text);
const restored=normalizeMemory(data.memory||data);

await saveMemory(restored);

const message=language()==="es"
?"Tu experiencia ha sido restaurada."
:"Your experience has been restored.";

setText("memoryStatus",message);
showToast(message);
}catch(e){
console.error(e);
showToast(language()==="es"
?"El archivo no es válido."
:"That backup file is not valid.");
}finally{
input.value="";
}
};
}

function updateStaticLanguage(){
const es=language()==="es";

setText("heroEyebrow",es?"TU MOMENTO PRIVADO":"YOUR PRIVATE MOMENT");
setText("heroTitle",es?"¿De qué quieres que me encargue?":"What can I take care of for you?");
setText("heroText",es
?"Cuéntame lo que necesitas. No tienes que saber exactamente cómo pedirlo."
:"Tell me what you need. You don't have to know exactly what to ask for.");

$("messageInput")?.setAttribute(
"placeholder",
es?"Cuéntale a MIRROR qué necesitas…":"Tell MIRROR what you need…"
);

setText("voiceLabel",es?"Hablar":"Speak");
setText("clearLabel",es?"Limpiar":"Clear");
setText("askLabel",es?"Preguntar a MIRROR":"Ask MIRROR");

setText("planLabel",es?"TU PRÓXIMO PASO":"YOUR NEXT MOVE");
setText("destinationLabel",es?"DÓNDE":"WHERE");
setText("budgetLabel",es?"TU RANGO":"YOUR RANGE");
setText("privacyLabel",es?"PRIVACIDAD":"PRIVACY");
setText("priorityLabel",es?"PRIORIDAD":"PRIORITY");

setText("feedbackYesLabel",es?"Esto se siente bien":"This feels right");
setText("feedbackDifferentLabel",es?"Hazlo diferente":"Make it different");
setText("conciergeLabel",es?"Encárgate de ello":"Take care of it");

setText("momentText",es
?"Cada día puede parecer familiar. El momento no lo es."
:"Every day may look familiar. The moment is not.");

setText("memoryTitle",es
?"MIRROR recuerda tus preferencias."
:"MIRROR remembers your preferences.");

setText("memoryText",es
?"Tu experiencia personal permanece en este dispositivo, salvo que decidas hacer una copia."
:"Your personal experience stays on this device unless you choose to back it up.");

setText("recoveryBtn",es?"Restaurar mi experiencia":"Restore my experience");
setText("backupBtn",es?"Copia de seguridad":"Backup");
setText("restoreBtn",es?"Restaurar":"Restore");

setText("footerText",es?"Privado por diseño.":"Private by design.");
}

function bindEvents(){
$("askBtn")?.addEventListener("click",askMirror);

$("feedbackYes")?.addEventListener("click",()=>feedback("positive"));
$("feedbackDifferent")?.addEventListener("click",revise);
$("conciergeBtn")?.addEventListener("click",sendConcierge);

$("mapsBtn")?.addEventListener("click",openMaps);
$("musicBtn")?.addEventListener("click",playMood);

$("recoveryBtn")?.addEventListener("click",openRecovery);
$("closeRecovery")?.addEventListener("click",closeRecovery);
$("recoverySubmit")?.addEventListener("click",submitRecovery);

$("backupBtn")?.addEventListener("click",backupMemory);
restoreFile();

$("recoveryModal")?.querySelector(".modal-backdrop")?.addEventListener("click",closeRecovery);

$("messageInput")?.addEventListener("keydown",e=>{
if(e.key==="Enter"&&!e.shiftKey){
e.preventDefault();
askMirror();
}
});
}

async function init(){
try{
await loadMemory();
}catch(e){
memory=defaultMemory();
}

bindEvents();
updateStaticLanguage();

if(typeof loadMissions==="function"){
loadMissions();
}
}

window.askMirror=askMirror;
window.startVoiceRecognition=startVoiceRecognition;
window.feedback=feedback;
window.revise=revise;
window.sendConcierge=sendConcierge;
window.openMaps=openMaps;
window.playMood=playMood;
window.openRecovery=openRecovery;
window.closeRecovery=closeRecovery;
window.submitRecovery=submitRecovery;
window.backupMemory=backupMemory;

document.addEventListener("DOMContentLoaded",init);
