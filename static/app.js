"use strict";

const MIRROR_STORAGE_KEY="mirror_memory";
const MIRROR_DB_NAME="mirror_to_you";
const MIRROR_DB_VERSION=1;
const MIRROR_DB_STORE="memory";
const DEVICE_KEY="mirror_device_id";
const LANG_KEY="mirror_language";
const TODAY_HISTORY_LIMIT=120;

let mirrorMemory=null;
let currentPlan=null;
let currentMission=null;
let currentResponse=null;
let currentLanguage=localStorage.getItem(LANG_KEY)||detectLanguage();
let recognition=null;
let listening=false;
let speechEnabled=true;
let breathingTimer=null;
let breathingRunning=false;
let breathingStartedAt=0;
let breathingElapsed=0;
let breathingRemaining=0;
let breathingPattern=null;
let breathingCycleTimer=null;
let currentBreathingPhaseIndex=0;
let currentBreathingCycle=0;
let todayExperienceSignature=null;

function $(id){
  return document.getElementById(id);
}

function safeText(value){
  return value===null||value===undefined?"":String(value);
}

function detectLanguage(){
  const lang=(navigator.language||"en").toLowerCase();
  return lang.startsWith("es")?"es":"en";
}

function getDeviceId(){
  let id=localStorage.getItem(DEVICE_KEY);
  if(!id){
    id="mirror-"+Date.now().toString(36)+"-"+Math.random().toString(36).slice(2,12);
    localStorage.setItem(DEVICE_KEY,id);
  }
  return id;
}

function getLocalDate(){
  const d=new Date();
  const y=d.getFullYear();
  const m=String(d.getMonth()+1).padStart(2,"0");
  const day=String(d.getDate()).padStart(2,"0");
  return `${y}-${m}-${day}`;
}

function getLocalTime(){
  const d=new Date();
  return d.toTimeString().slice(0,8);
}

function getTimezone(){
  try{
    return Intl.DateTimeFormat().resolvedOptions().timeZone||"UTC";
  }catch(e){
    return "UTC";
  }
}

function createEmptyMemory(){
  return {
    core:{},
    preferences:{},
    dislikes:[],
    daily:{},
    history:[],
    feedback:[],
    device_id:getDeviceId(),
    created_at:new Date().toISOString(),
    updated_at:new Date().toISOString()
  };
}

function normalizeMemory(memory){
  const m=memory&&typeof memory==="object"?memory:createEmptyMemory();

  if(!m.core||typeof m.core!=="object")m.core={};
  if(!m.preferences||typeof m.preferences!=="object")m.preferences={};
  if(!Array.isArray(m.dislikes))m.dislikes=[];
  if(!m.daily||typeof m.daily!=="object")m.daily={};
  if(!Array.isArray(m.history))m.history=[];
  if(!Array.isArray(m.feedback))m.feedback=[];
  if(!m.device_id)m.device_id=getDeviceId();

  const today=getLocalDate();

  if(!Array.isArray(m.daily[today]))m.daily[today]=[];

  Object.keys(m.daily).forEach(day=>{
    if(day!==today&&Object.keys(m.daily).length>14)delete m.daily[day];
  });

  m.daily[today]=m.daily[today].slice(-TODAY_HISTORY_LIMIT);
  m.history=m.history.slice(-100);
  m.feedback=m.feedback.slice(-100);
  m.updated_at=new Date().toISOString();

  return m;
}

function saveMemoryLocal(memory){
  mirrorMemory=normalizeMemory(memory);
  localStorage.setItem(MIRROR_STORAGE_KEY,JSON.stringify(mirrorMemory));
  return mirrorMemory;
}

function loadMemoryLocal(){
  try{
    const raw=localStorage.getItem(MIRROR_STORAGE_KEY);
    if(raw)return normalizeMemory(JSON.parse(raw));
  }catch(e){
    console.warn("MIRROR memory reset:",e);
    localStorage.removeItem(MIRROR_STORAGE_KEY);
  }
  return createEmptyMemory();
}

function openMemoryDB(){
  return new Promise((resolve,reject)=>{
    if(!window.indexedDB){
      resolve(null);
      return;
    }

    const request=indexedDB.open(MIRROR_DB_NAME,MIRROR_DB_VERSION);

    request.onupgradeneeded=()=>{
      const db=request.result;
      if(!db.objectStoreNames.contains(MIRROR_DB_STORE)){
        db.createObjectStore(MIRROR_DB_STORE,{keyPath:"id"});
      }
    };

    request.onsuccess=()=>resolve(request.result);
    request.onerror=()=>reject(request.error);
  });
}

async function saveMemoryIndexedDB(memory){
  try{
    const db=await openMemoryDB();
    if(!db)return;

    await new Promise((resolve,reject)=>{
      const tx=db.transaction(MIRROR_DB_STORE,"readwrite");
      tx.objectStore(MIRROR_DB_STORE).put({
        id:"primary",
        memory:normalizeMemory(memory)
      });
      tx.oncomplete=resolve;
      tx.onerror=()=>reject(tx.error);
    });

    db.close();
  }catch(e){
    console.warn("IndexedDB save failed:",e);
  }
}

async function loadMemoryIndexedDB(){
  try{
    const db=await openMemoryDB();
    if(!db)return null;

    const result=await new Promise((resolve,reject)=>{
      const tx=db.transaction(MIRROR_DB_STORE,"readonly");
      const request=tx.objectStore(MIRROR_DB_STORE).get("primary");
      request.onsuccess=()=>resolve(request.result||null);
      request.onerror=()=>reject(request.error);
    });

    db.close();

    return result&&result.memory?normalizeMemory(result.memory):null;
  }catch(e){
    console.warn("IndexedDB load failed:",e);
    return null;
  }
}

async function loadMemory(){
  const indexed=await loadMemoryIndexedDB();

  if(indexed){
    mirrorMemory=normalizeMemory(indexed);
    localStorage.setItem(MIRROR_STORAGE_KEY,JSON.stringify(mirrorMemory));
    return mirrorMemory;
  }

  mirrorMemory=loadMemoryLocal();
  await saveMemoryIndexedDB(mirrorMemory);
  return mirrorMemory;
}

async function persistMemory(memory){
  mirrorMemory=saveMemoryLocal(memory);
  await saveMemoryIndexedDB(mirrorMemory);
  return mirrorMemory;
}

function todayHistory(){
  if(!mirrorMemory)mirrorMemory=loadMemoryLocal();
  const today=getLocalDate();

  if(!Array.isArray(mirrorMemory.daily[today])){
    mirrorMemory.daily[today]=[];
  }

  return mirrorMemory.daily[today];
}

function getTodayUsed(){
  const history=todayHistory();

  const used={
    experience_ids:new Set(),
    exercise_ids:new Set(),
    breathing_ids:new Set(),
    patterns:new Set(),
    actions:new Set(),
    phrases:new Set(),
    titles:new Set(),
    signatures:new Set()
  };

  history.forEach(item=>{
    if(!item||typeof item!=="object")return;

    [
      ["experience_id","experience_ids"],
      ["exercise_id","exercise_ids"],
      ["breathing_id","breathing_ids"],
      ["pattern","patterns"],
      ["action","actions"],
      ["phrase","phrases"],
      ["title","titles"],
      ["signature","signatures"]
    ].forEach(([field,target])=>{
      const value=item[field];
      if(value!==undefined&&value!==null&&String(value).trim()){
        used[target].add(String(value).trim().toLowerCase());
      }
    });

    if(item.breathing&&typeof item.breathing==="object"){
      const b=item.breathing;

      if(b.id)used.breathing_ids.add(String(b.id).toLowerCase());
      if(b.pattern)used.patterns.add(String(b.pattern).toLowerCase());
      if(b.signature)used.signatures.add(String(b.signature).toLowerCase());
    }
  });

  return used;
}

function addTodayExperience(experience){
  if(!mirrorMemory)mirrorMemory=loadMemoryLocal();

  const today=getLocalDate();

  if(!Array.isArray(mirrorMemory.daily[today])){
    mirrorMemory.daily[today]=[];
  }

  const record={
    ...experience,
    date:today,
    time:getLocalTime(),
    timestamp:new Date().toISOString()
  };

  mirrorMemory.daily[today].push(record);
  mirrorMemory.daily[today]=mirrorMemory.daily[today].slice(-TODAY_HISTORY_LIMIT);

  mirrorMemory.history.push(record);
  mirrorMemory.history=mirrorMemory.history.slice(-100);

  persistMemory(mirrorMemory);
  return record;
}

function buildClientContext(){
  const used=getTodayUsed();

  return {
    device_id:getDeviceId(),
    date:getLocalDate(),
    time:getLocalTime(),
    timezone:getTimezone(),
    language:currentLanguage,
    today_count:todayHistory().length,
    today_history:todayHistory().slice(-40),
    avoid_today:{
      experience_ids:Array.from(used.experience_ids),
      exercise_ids:Array.from(used.exercise_ids),
      breathing_ids:Array.from(used.breathing_ids),
      patterns:Array.from(used.patterns),
      actions:Array.from(used.actions),
      phrases:Array.from(used.phrases),
      titles:Array.from(used.titles),
      signatures:Array.from(used.signatures)
    },
    core:mirrorMemory?.core||{},
    preferences:mirrorMemory?.preferences||{},
    dislikes:mirrorMemory?.dislikes||{}
  };
}

async function api(url,options={}){
  const config={
    method:"GET",
    headers:{
      "Accept":"application/json",
      ...(options.body?{"Content-Type":"application/json"}:{})
    },
    ...options
  };

  const response=await fetch(url,config);
  let data=null;

  try{
    data=await response.json();
  }catch(e){
    data={};
  }

  if(!response.ok){
    const detail=data&&data.detail?
      (typeof data.detail==="string"?data.detail:JSON.stringify(data.detail)):
      `HTTP ${response.status}`;

    throw new Error(detail);
  }

  return data;
}

function setLoading(loading){
  const button=$("askBtn");
  if(button){
    button.disabled=loading;
    button.dataset.originalText=button.dataset.originalText||button.textContent;
    button.textContent=loading?
      (currentLanguage==="es"?"Estoy contigo…":"I'm with you…"):
      button.dataset.originalText;
  }

  document.body.classList.toggle("mirror-loading",loading);
}

function showSection(id,show=true){
  const el=$(id);
  if(el)el.classList.toggle("hidden",!show);
}

function setText(id,text){
  const el=$(id);
  if(el)el.textContent=safeText(text);
}

function setHTML(id,html){
  const el=$(id);
  if(el)el.innerHTML=html;
}

function showToast(message){
  const toast=$("toast");
  if(!toast)return;

  toast.textContent=safeText(message);
  toast.classList.add("show");

  clearTimeout(showToast.timer);
  showToast.timer=setTimeout(()=>{
    toast.classList.remove("show");
  },3200);
}

function speak(text,options={}){
  if(!speechEnabled)return;
  if(!("speechSynthesis" in window))return;

  const value=safeText(text).trim();
  if(!value)return;

  window.speechSynthesis.cancel();

  const utterance=new SpeechSynthesisUtterance(value);
  utterance.lang=options.lang||
    (currentLanguage==="es"?"es-US":"en-US");
  utterance.rate=options.rate||0.95;
  utterance.pitch=options.pitch||1;

  const voices=window.speechSynthesis.getVoices();

  if(voices.length){
    const preferred=voices.find(v=>{
      const l=(v.lang||"").toLowerCase();
      return currentLanguage==="es"?l.startsWith("es"):l.startsWith("en");
    });

    if(preferred)utterance.voice=preferred;
  }

  window.speechSynthesis.speak(utterance);
}

function stopSpeech(){
  if("speechSynthesis" in window){
    window.speechSynthesis.cancel();
  }
}

function getResponseText(data){
  return data?.message||
    data?.response||
    data?.answer||
    data?.direction||
    data?.plan?.direction||
    "";
}

function renderResponse(data){
  currentResponse=data;

  const text=getResponseText(data);

  if(text){
    setText("responseText",text);
    showSection("responseSection",true);
    setText(
      "responseStatus",
      currentLanguage==="es"?"Aquí estoy.":"I'm here."
    );
  }

  if(data?.understanding){
    renderUnderstanding(data.understanding);
  }

  if(data?.personalization){
    renderPersonalization(data.personalization);
  }

  if(data?.plan){
    currentPlan=data.plan;
    renderPlan(data.plan);
  }

  if(data?.mission){
    currentMission=data.mission;
  }

  if(data?.memory){
    persistMemory(data.memory);
  }

  if(text){
    speak(text);
  }
}

function renderUnderstanding(understanding){
  showSection("understandingSection",true);

  let text="";

  if(typeof understanding==="string"){
    text=understanding;
  }else if(understanding&&typeof understanding==="object"){
    text=
      understanding.summary||
      understanding.text||
      understanding.direction||
      understanding.message||
      "";
  }

  setText("understandingText",text);

  const fields={
    companion:understanding?.companion,
    duration:understanding?.duration,
    destination:understanding?.destination
  };

  Object.entries(fields).forEach(([key,value])=>{
    const el=$(key);
    if(el&&value!==undefined&&value!==null){
      el.value=safeText(value);
      el.textContent=safeText(value);
    }
  });
}

function renderPersonalization(personalization){
  if(!personalization)return;

  const values={
    companion:personalization.companion,
    duration:personalization.duration,
    destination:personalization.destination
  };

  Object.entries(values).forEach(([key,value])=>{
    if(value===undefined||value===null)return;

    const el=$(key);
    if(!el)return;

    if("value" in el)el.value=safeText(value);
    else el.textContent=safeText(value);
  });
}

function renderPlan(plan){
  if(!plan)return;

  showSection("planSection",true);

  setText(
    "planTitle",
    plan.title||
    plan.experience_title||
    plan.name||
    (currentLanguage==="es"?"Para este momento":"For this moment")
  );

  setText(
    "planDirection",
    plan.direction||
    plan.next_move||
    plan.action||
    ""
  );

  setText("planDetails",buildPlanDetails(plan));

  renderPlanSteps(plan);
  renderPlanQuestions(plan);
  renderBreathing(plan);

  const destination=plan.destination||plan.destino;

  const destinationWrapper=$("planDestinationWrapper");
  if(destinationWrapper){
    destinationWrapper.classList.toggle("hidden",!destination);
  }

  if(destination){
    setText("planDestination",destination);
  }

  const budgetWrapper=$("planBudgetWrapper");
  if(budgetWrapper){
    budgetWrapper.classList.toggle(
      "hidden",
      !plan.budget
    );
  }

  if(plan.budget)setText("planBudget",plan.budget);

  const privacyWrapper=$("planPrivacyWrapper");
  if(privacyWrapper){
    privacyWrapper.classList.toggle(
      "hidden",
      !plan.privacy
    );
  }

  if(plan.privacy)setText("planPrivacy",plan.privacy);

  const priorityWrapper=$("planPriorityWrapper");
  if(priorityWrapper){
    priorityWrapper.classList.toggle(
      "hidden",
      !plan.priority
    );
  }

  if(plan.priority)setText("planPriority",plan.priority);
}

function buildPlanDetails(plan){
  const pieces=[];

  if(plan.category)pieces.push(plan.category);
  if(plan.duration)pieces.push(plan.duration);
  if(plan.companion)pieces.push(plan.companion);
  if(plan.status)pieces.push(plan.status);

  return pieces.join(" · ");
}

function renderPlanSteps(plan){
  const container=$("planSteps");
  if(!container)return;

  const steps=Array.isArray(plan.steps)?
    plan.steps:
    Array.isArray(plan.actions)?
      plan.actions:
      [];

  container.innerHTML="";

  if(!steps.length){
    container.classList.add("hidden");
    return;
  }

  container.classList.remove("hidden");

  steps.forEach((step,index)=>{
    const item=document.createElement("div");
    item.className="mirror-step";

    const number=document.createElement("span");
    number.className="mirror-step-number";
    number.textContent=String(index+1);

    const content=document.createElement("span");

    if(typeof step==="string"){
      content.textContent=step;
    }else{
      content.textContent=
        step.text||
        step.action||
        step.description||
        step.title||
        "";
    }

    item.append(number,content);
    container.appendChild(item);
  });
}

function renderPlanQuestions(plan){
  const container=$("planQuestions");
  if(!container)return;

  const questions=Array.isArray(plan.questions)?
    plan.questions:
    [];

  container.innerHTML="";

  if(!questions.length){
    container.classList.add("hidden");
    return;
  }

  container.classList.remove("hidden");

  questions.forEach(question=>{
    const item=document.createElement("div");
    item.className="mirror-question";
    item.textContent=typeof question==="string"?
      question:
      question.text||question.question||"";
    container.appendChild(item);
  });
}

function extractBreathing(plan){
  if(!plan)return null;

  return plan.breathing||
    plan.respiracion||
    plan.experience?.breathing||
    plan.experience?.respiracion||
    null;
}

function renderBreathing(plan){
  const breathing=extractBreathing(plan);

  const section=
    $("breathingSection")||
    $("breathingExperience")||
    $("breathingContainer");

  if(!section){
    if(breathing)createBreathingInterface(breathing);
    return;
  }

  if(!breathing){
    section.classList.add("hidden");
    return;
  }

  section.classList.remove("hidden");

  updateBreathingElements(breathing);
}

function createBreathingInterface(breathing){
  if(document.getElementById("mirrorBreathingDynamic"))return;

  const target=
    $("planSection")||
    $("responseSection")||
    document.body;

  const section=document.createElement("section");
  section.id="mirrorBreathingDynamic";
  section.className="mirror-breathing";

  section.innerHTML=`
    <div class="mirror-breathing-inner">
      <div class="mirror-breathing-title" id="mirrorBreathingTitle"></div>
      <div class="mirror-breathing-orb" id="mirrorBreathingOrb">
        <div class="mirror-breathing-phase" id="mirrorBreathingPhase"></div>
      </div>
      <div class="mirror-breathing-time" id="mirrorBreathingTime"></div>
      <div class="mirror-breathing-instruction" id="mirrorBreathingInstruction"></div>
      <button type="button" id="mirrorBreathingStart"></button>
      <button type="button" id="mirrorBreathingStop" class="hidden"></button>
    </div>
  `;

  target.appendChild(section);

  bindBreathingControls();
  updateBreathingElements(breathing);
}

function bindBreathingControls(){
  const start=$("mirrorBreathingStart");
  const stop=$("mirrorBreathingStop");

  if(start&&!start.dataset.bound){
    start.dataset.bound="1";
    start.addEventListener("click",startBreathing);
  }

  if(stop&&!stop.dataset.bound){
    stop.dataset.bound="1";
    stop.addEventListener("click",stopBreathing);
  }
}

function updateBreathingElements(breathing){
  if(!breathing)return;

  bindBreathingControls();

  const section=
    $("breathingSection")||
    $("breathingExperience")||
    $("breathingContainer")||
    $("mirrorBreathingDynamic");

  if(section)section.classList.remove("hidden");

  breathingPattern=normalizeBreathingPattern(breathing);

  setText(
    "mirrorBreathingTitle",
    breathing.title||
    breathing.name||
    (currentLanguage==="es"?"Un momento para ti":"A moment for you")
  );

  setText(
    "mirrorBreathingInstruction",
    breathing.instruction||
    breathing.description||
    breathing.guidance||
    ""
  );

  setText(
    "mirrorBreathingStart",
    currentLanguage==="es"?"Comenzar":"Begin"
  );

  setText(
    "mirrorBreathingStop",
    currentLanguage==="es"?"Detener":"Stop"
  );

  breathingRemaining=
    Number(breathing.duration_seconds||
    breathing.duration||
    breathing.seconds||
    120);

  if(!Number.isFinite(breathingRemaining)||breathingRemaining<=0){
    breathingRemaining=120;
  }

  breathingRemaining=Math.min(breathingRemaining,900);

  updateBreathingTime();
}

function normalizeBreathingPattern(breathing){
  const raw=breathing.patterns||
    breathing.phases||
    breathing.sequence||
    null;

  if(Array.isArray(raw)&&raw.length){
    return raw.map(phase=>{
      if(typeof phase==="string"){
        return {
          name:phase,
          seconds:4
        };
      }

      return {
        name:
          phase.name||
          phase.phase||
          phase.label||
          "Respira",
        seconds:
          Number(
            phase.seconds||
            phase.duration||
            phase.duration_seconds||
            4
          )||4,
        instruction:phase.instruction||""
      };
    }).filter(p=>p.seconds>0);
  }

  const inhale=Number(
    breathing.inhale_seconds||
    breathing.inhale||
    4
  )||4;

  const hold=Number(
    breathing.hold_seconds||
    breathing.hold||
    0
  )||0;

  const exhale=Number(
    breathing.exhale_seconds||
    breathing.exhale||
    6
  )||6;

  const phases=[
    {
      name:currentLanguage==="es"?"Inhala":"Inhale",
      seconds:inhale
    }
  ];

  if(hold>0){
    phases.push({
      name:currentLanguage==="es"?"Mantén":"Hold",
      seconds:hold
    });
  }

  phases.push({
    name:currentLanguage==="es"?"Exhala":"Exhale",
    seconds:exhale
  });

  return phases;
}

function updateBreathingTime(){
  const el=$("mirrorBreathingTime");
  if(!el)return;

  const total=Math.max(0,Math.ceil(breathingRemaining));
  const minutes=Math.floor(total/60);
  const seconds=total%60;

  el.textContent=
    `${minutes}:${String(seconds).padStart(2,"0")}`;
}

function getBreathingPhase(){
  if(!breathingPattern||!breathingPattern.length){
    return null;
  }

  return breathingPattern[
    currentBreathingPhaseIndex%breathingPattern.length
  ];
}

function setBreathingOrb(phase){
  const orb=
    $("mirrorBreathingOrb")||
    $("breathingOrb")||
    $("breathingCircle")||
    $("respiratoryCircle");

  const phaseText=
    $("mirrorBreathingPhase")||
    $("breathingPhase")||
    $("breathingInstruction");

  if(!phase)return;

  const name=safeText(phase.name);

  if(phaseText)phaseText.textContent=name;

  if(!orb)return;

  const normalized=name.toLowerCase();

  let scale=1;

  if(
    normalized.includes("inh")||
    normalized.includes("inhal")||
    normalized.includes("insp")
  ){
    scale=1.45;
  }else if(
    normalized.includes("exh")||
    normalized.includes("exhal")||
    normalized.includes("expir")
  ){
    scale=.82;
  }else{
    scale=1.05;
  }

  orb.style.transform=`scale(${scale})`;
  orb.style.transition=
    `transform ${Math.max(1,Number(phase.seconds)||4)}s ease-in-out`;
}

function startBreathing(){
  if(breathingRunning)return;
  if(!breathingPattern||!breathingPattern.length)return;

  breathingRunning=true;
  breathingStartedAt=Date.now();
  currentBreathingPhaseIndex=0;
  currentBreathingCycle=0;

  const start=$("mirrorBreathingStart");
  const stop=$("mirrorBreathingStop");

  if(start)start.classList.add("hidden");
  if(stop)stop.classList.remove("hidden");

  stopSpeech();
  runBreathingPhase();

  clearInterval(breathingTimer);

  breathingTimer=setInterval(()=>{
    breathingRemaining=Math.max(
      0,
      breathingRemaining-1
    );

    updateBreathingTime();

    if(breathingRemaining<=0){
      finishBreathing();
    }
  },1000);
}

function runBreathingPhase(){
  if(!breathingRunning)return;

  const phase=getBreathingPhase();
  if(!phase)return;

  setBreathingOrb(phase);

  const instruction=
    phase.instruction||
    phase.name||
    "";

  if(instruction){
    speak(instruction,{
      rate:.88,
      pitch:1
    });
  }

  clearTimeout(breathingCycleTimer);

  breathingCycleTimer=setTimeout(()=>{
    if(!breathingRunning)return;

    currentBreathingPhaseIndex++;

    if(currentBreathingPhaseIndex>=breathingPattern.length){
      currentBreathingPhaseIndex=0;
      currentBreathingCycle++;
    }

    runBreathingPhase();
  },Math.max(1,Number(phase.seconds)||4)*1000);
}

function stopBreathing(){
  breathingRunning=false;

  clearInterval(breathingTimer);
  clearTimeout(breathingCycleTimer);

  breathingTimer=null;
  breathingCycleTimer=null;

  stopSpeech();

  const start=$("mirrorBreathingStart");
  const stop=$("mirrorBreathingStop");
  const orb=$("mirrorBreathingOrb");

  if(start)start.classList.remove("hidden");
  if(stop)stop.classList.add("hidden");

  if(orb){
    orb.style.transform="scale(1)";
  }
}

function finishBreathing(){
  if(!breathingRunning)return;

  breathingRunning=false;

  clearInterval(breathingTimer);
  clearTimeout(breathingCycleTimer);

  breathingTimer=null;
  breathingCycleTimer=null;

  const breathing=
    extractBreathing(currentPlan)||{};

  const signature=
    breathing.signature||
    breathing.id||
    `${breathing.pattern||""}-${breathing.duration_seconds||breathing.duration||""}-${breathing.inhale_seconds||""}-${breathing.exhale_seconds||""}`;

  addTodayExperience({
    type:"breathing",
    experience_id:
      breathing.experience_id||
      currentPlan?.experience_id||
      `breathing-${Date.now()}`,
    exercise_id:breathing.exercise_id||breathing.id||null,
    breathing_id:breathing.id||null,
    pattern:breathing.pattern||breathingPattern.map(p=>p.seconds).join("-"),
    signature:String(signature).toLowerCase(),
    title:
      breathing.title||
      currentPlan?.title||
      "",
    action:"breathing_completed",
    phrase:breathing.opening||breathing.instruction||"",
    breathing:{
      id:breathing.id||null,
      pattern:breathing.pattern||breathingPattern.map(p=>p.seconds).join("-"),
      signature:String(signature).toLowerCase()
    }
  });

  const start=$("mirrorBreathingStart");
  const stop=$("mirrorBreathingStop");

  if(start)start.classList.remove("hidden");
  if(stop)stop.classList.add("hidden");

  speak(
    breathing.closing||
    (currentLanguage==="es"?
      "Muy bien. Quédate un instante con esta sensación.":
      "Good. Stay with this feeling for a moment."),
    {rate:.9}
  );

  showToast(
    currentLanguage==="es"?
      "Este momento queda guardado en tu memoria de hoy.":
      "This moment has been kept in today's memory."
  );
}

async function askMirror(){
  const input=$("messageInput");

  if(!input)return;

  const message=input.value.trim();

  if(!message){
    showToast(
      currentLanguage==="es"?
        "Cuéntame qué necesitas.":
        "Tell me what you need."
    );
    input.focus();
    return;
  }

  stopBreathing();
  setLoading(true);

  try{
    if(!mirrorMemory){
      await loadMemory();
    }

    mirrorMemory=normalizeMemory(mirrorMemory);

    const context=buildClientContext();

    const payload={
      message,
      language:currentLanguage,
      device_id:getDeviceId(),
      local_date:getLocalDate(),
      local_time:getLocalTime(),
      timezone:getTimezone(),
      memory:mirrorMemory,
      client_context:context
    };

    const data=await api("/api/mirror",{
      method:"POST",
      body:JSON.stringify(payload)
    });

    renderResponse(data);

    if(data?.memory){
      await persistMemory(data.memory);
    }

    recordResponseExperience(data,message);

    const response=getResponseText(data);

    if(response){
      setText("responseText",response);
    }

    input.value="";
  }catch(error){
    console.error("MIRROR error:",error);

    setText(
      "responseText",
      currentLanguage==="es"?
        "Estoy aquí. Hubo una interrupción momentánea. Inténtalo nuevamente.":
        "I'm here. There was a brief interruption. Please try again."
    );

    showSection("responseSection",true);

    showToast(
      currentLanguage==="es"?
        "No pude completar este momento. Inténtalo otra vez.":
        "I couldn't complete this moment. Please try again."
    );
  }finally{
    setLoading(false);
  }
}

function recordResponseExperience(data,message){
  const plan=data?.plan||{};
  const breathing=extractBreathing(plan);

  const experienceId=
    plan.experience_id||
    data?.experience_id||
    data?.mission?.experience_id||
    null;

  const signature=
    plan.signature||
    data?.signature||
    buildExperienceSignature(plan,message);

  const record={
    type:"mirror_entry",
    experience_id:experienceId,
    exercise_id:
      plan.exercise_id||
      data?.exercise_id||
      null,
    title:
      plan.title||
      plan.experience_title||
      "",
    action:
      plan.action||
      plan.next_move||
      "",
    phrase:
      data?.message||
      plan.direction||
      "",
    signature:signature,
    user_message:message.slice(0,500),
    intent:data?.decision?.intent||null,
    category:plan.category||null
  };

  if(breathing){
    record.breathing={
      id:breathing.id||null,
      pattern:breathing.pattern||
        breathing.patterns||
        breathing.sequence||
        null,
      signature:
        breathing.signature||
        `${breathing.id||""}-${breathing.pattern||""}`
    };
  }

  addTodayExperience(record);
  todayExperienceSignature=signature;
}

function buildExperienceSignature(plan,message){
  const values=[
    plan.title,
    plan.action,
    plan.next_move,
    plan.direction,
    plan.category,
    message
  ]
  .filter(Boolean)
  .map(v=>String(v).trim().toLowerCase())
  .join("|");

  return values.slice(0,500);
}

async function sendFeedback(value){
  try{
    const payload={
      value,
      language:currentLanguage,
      device_id:getDeviceId(),
      memory:mirrorMemory,
      mission_id:currentMission?.id||null,
      experience_id:
        currentPlan?.experience_id||
        currentMission?.experience_id||
        null
    };

    const data=await api("/api/feedback",{
      method:"POST",
      body:JSON.stringify(payload)
    });

    if(data?.memory){
      await persistMemory(data.memory);
    }

    mirrorMemory.feedback.push({
      value,
      timestamp:new Date().toISOString(),
      experience_id:payload.experience_id
    });

    mirrorMemory.feedback=
      mirrorMemory.feedback.slice(-100);

    await persistMemory(mirrorMemory);

    showToast(
      currentLanguage==="es"?
        "Lo tendré en cuenta para lo que sigue.":
        "I'll take that into account going forward."
    );
  }catch(error){
    console.error("Feedback error:",error);
    showToast(
      currentLanguage==="es"?
        "No pude guardar el comentario.":
        "I couldn't save the feedback."
    );
  }
}

async function revisePlan(){
  const request={
    message:
      currentLanguage==="es"?
        "Quiero algo diferente para este momento.":
        "I want something different for this moment.",
    language:currentLanguage,
    device_id:getDeviceId(),
    local_date:getLocalDate(),
    timezone:getTimezone(),
    memory:mirrorMemory,
    today_context:buildClientContext(),
    previous_plan:currentPlan
  };

  try{
    setLoading(true);

    const data=await api("/api/mirror",{
      method:"POST",
      body:JSON.stringify(request)
    });

    renderResponse(data);

    if(data?.memory){
      await persistMemory(data.memory);
    }

    showToast(
      currentLanguage==="es"?
        "He buscado otra experiencia para este momento.":
        "I found a different experience for this moment."
    );
  }catch(error){
    console.error("Revision error:",error);

    showToast(
      currentLanguage==="es"?
        "No pude cambiar la experiencia ahora.":
        "I couldn't change the experience right now."
    );
  }finally{
    setLoading(false);
  }
}

async function requestConcierge(){
  const status=$("conciergeStatus");

  if(status){
    status.textContent=
      currentLanguage==="es"?
        "Estoy preparando lo que necesitas…":
        "I'm preparing what you need…";
  }

  try{
    const data=await api("/api/concierge",{
      method:"POST",
      body:JSON.stringify({
        language:currentLanguage,
        device_id:getDeviceId(),
        memory:mirrorMemory,
        plan:currentPlan,
        mission:currentMission,
        local_date:getLocalDate(),
        timezone:getTimezone()
      })
    });

    const text=
      data?.message||
      data?.status||
      (currentLanguage==="es"?
        "He recibido tu solicitud.":
        "I've received your request.");

    if(status)status.textContent=text;

    speak(text);
  }catch(error){
    console.error("Concierge error:",error);

    if(status){
      status.textContent=
        currentLanguage==="es"?
          "Todavía no puedo coordinar este servicio.":
          "I can't coordinate this service yet.";
    }
  }
}

function openMaps(){
  const destination=
    currentPlan?.destination||
    currentPlan?.destino||
    $("planDestination")?.textContent||
    "";

  if(!destination){
    showToast(
      currentLanguage==="es"?
        "Todavía no hay un lugar concreto.":
        "There isn't a specific place yet."
    );
    return;
  }

  const url=
    `/api/maps?destination=${encodeURIComponent(destination)}`;

  window.open(url,"_blank","noopener,noreferrer");
}

function openMusic(){
  const query=
    currentPlan?.music||
    currentPlan?.music_query||
    currentPlan?.destination||
    (currentLanguage==="es"?
      "música para este momento":
      "music for this moment");

  const url=
    `/api/music?query=${encodeURIComponent(query)}`;

  window.open(url,"_blank","noopener,noreferrer");
}

async function loadMissions(){
  const container=$("missionsContainer")||$("missionsList");
  if(!container)return;

  try{
    const data=await api("/api/missions");

    const missions=
      Array.isArray(data)?
        data:
        data?.missions||[];

    container.innerHTML="";

    if(!missions.length){
      container.classList.add("hidden");
      return;
    }

    missions.forEach(mission=>{
      const item=document.createElement("button");
      item.type="button";
      item.className="mirror-mission";

      item.textContent=
        mission.title||
        mission.name||
        mission.description||
        "";

      item.addEventListener("click",()=>{
        const input=$("messageInput");
        if(!input)return;

        input.value=
          currentLanguage==="es"?
            `Quiero explorar ${mission.title||mission.name||"esto"}.`:
            `I want to explore ${mission.title||mission.name||"this"}.`;

        input.focus();
      });

      container.appendChild(item);
    });

    container.classList.remove("hidden");
  }catch(error){
    console.warn("Mission loading skipped:",error);
  }
}

function clearInput(){
  const input=$("messageInput");
  if(input){
    input.value="";
    input.focus();
  }
}

function startVoiceRecognition(){
  if(listening){
    stopVoiceRecognition();
    return;
  }

  const SpeechRecognition=
    window.SpeechRecognition||
    window.webkitSpeechRecognition;

  if(!SpeechRecognition){
    showToast(
      currentLanguage==="es"?
        "El reconocimiento de voz no está disponible en este navegador.":
        "Voice recognition isn't available in this browser."
    );
    return;
  }

  recognition=new SpeechRecognition();
  recognition.lang=currentLanguage==="es"?"es-US":"en-US";
  recognition.interimResults=true;
  recognition.continuous=false;

  recognition.onstart=()=>{
    listening=true;
    updateVoiceButton();
  };

  recognition.onresult=event=>{
    const input=$("messageInput");
    if(!input)return;

    let transcript="";

    for(let i=event.resultIndex;i<event.results.length;i++){
      transcript+=event.results[i][0].transcript;
    }

    if(transcript){
      input.value=transcript.trim();
    }
  };

  recognition.onerror=event=>{
    console.warn("Voice recognition:",event.error);

    if(event.error==="not-allowed"){
      showToast(
        currentLanguage==="es"?
          "Necesito permiso para usar el micrófono.":
          "I need microphone permission."
      );
    }
  };

  recognition.onend=()=>{
    listening=false;
    updateVoiceButton();
  };

  try{
    recognition.start();
  }catch(error){
    console.warn("Voice start failed:",error);
    listening=false;
    updateVoiceButton();
  }
}

function stopVoiceRecognition(){
  if(recognition){
    try{
      recognition.stop();
    }catch(e){}
  }

  listening=false;
  updateVoiceButton();
}

function updateVoiceButton(){
  const button=$("voiceBtn");
  if(!button)return;

  button.classList.toggle("active",listening);

  button.setAttribute(
    "aria-label",
    listening?
      (currentLanguage==="es"?"Detener voz":"Stop voice"):
      (currentLanguage==="es"?"Hablar con MIRROR":"Speak to MIRROR")
  );
}

function toggleLanguage(){
  currentLanguage=currentLanguage==="es"?"en":"es";

  localStorage.setItem(LANG_KEY,currentLanguage);

  updateStaticLanguage();

  if(recognition){
    recognition.lang=currentLanguage==="es"?"es-US":"en-US";
  }
}

function updateStaticLanguage(){
  const elements=document.querySelectorAll("[data-es][data-en]");

  elements.forEach(el=>{
    const value=
      currentLanguage==="es"?
        el.dataset.es:
        el.dataset.en;

    if(value!==undefined){
      el.textContent=value;
    }
  });

  const input=$("messageInput");

  if(input){
    input.placeholder=
      currentLanguage==="es"?
        "Cuéntame qué necesitas…":
        "Tell me what you need…";
  }

  const languageButton=$("languageBtn");

  if(languageButton){
    languageButton.textContent=
      currentLanguage==="es"?"EN":"ES";
  }

  updateVoiceButton();
}

function bindButton(id,handler){
  const el=$(id);

  if(!el||el.dataset.mirrorBound)return;

  el.dataset.mirrorBound="1";
  el.addEventListener("click",handler);
}

function bindEvents(){
  bindButton("askBtn",askMirror);
  bindButton("clearBtn",clearInput);
  bindButton("voiceBtn",startVoiceRecognition);
  bindButton("languageBtn",toggleLanguage);

  bindButton("feedbackYes",()=>{
    sendFeedback("helpful");
  });

  bindButton("feedbackDifferent",()=>{
    sendFeedback("different");
    revisePlan();
  });

  bindButton("conciergeBtn",requestConcierge);
  bindButton("mapsBtn",openMaps);
  bindButton("musicBtn",openMusic);

  const input=$("messageInput");

  if(input&&!input.dataset.mirrorInputBound){
    input.dataset.mirrorInputBound="1";

    input.addEventListener("keydown",event=>{
      if(event.key==="Enter"&&!event.shiftKey){
        event.preventDefault();
        askMirror();
      }
    });
  }

  document.querySelectorAll("[data-suggestion]").forEach(button=>{
    if(button.dataset.mirrorSuggestionBound)return;

    button.dataset.mirrorSuggestionBound="1";

    button.addEventListener("click",()=>{
      const input=$("messageInput");
      if(!input)return;

      input.value=
        button.dataset.suggestion||
        button.textContent||
        "";

      input.focus();
    });
  });

  const restoreInput=$("restoreInput");

  if(restoreInput&&!restoreInput.dataset.mirrorRestoreBound){
    restoreInput.dataset.mirrorRestoreBound="1";
    restoreInput.addEventListener("change",restoreFile);
  }

  bindBreathingControls();
}

function downloadFile(filename,content,type){
  const blob=new Blob([content],{type});
  const url=URL.createObjectURL(blob);

  const a=document.createElement("a");
  a.href=url;
  a.download=filename;
  document.body.appendChild(a);
  a.click();
  a.remove();

  setTimeout(()=>URL.revokeObjectURL(url),1000);
}

function backupMemory(){
  if(!mirrorMemory)mirrorMemory=loadMemoryLocal();

  const backup={
    version:1,
    app:"MIRROR TO YOU",
    created_at:new Date().toISOString(),
    memory:mirrorMemory
  };

  downloadFile(
    `mirror-memory-${getLocalDate()}.json`,
    JSON.stringify(backup,null,2),
    "application/json"
  );

  showToast(
    currentLanguage==="es"?
      "Tu memoria local fue preparada para respaldo.":
      "Your local memory backup is ready."
  );
}

async function restoreFile(event){
  const file=event.target.files?.[0];

  if(!file)return;

  try{
    const text=await file.text();
    const data=JSON.parse(text);

    const restored=
      data?.memory||
      data;

    if(!restored||typeof restored!=="object"){
      throw new Error("Invalid memory file");
    }

    const normalized=normalizeMemory(restored);

    await persistMemory(normalized);

    showToast(
      currentLanguage==="es"?
        "Memoria restaurada.":
        "Memory restored."
    );

    setTimeout(()=>{
      location.reload();
    },600);
  }catch(error){
    console.error("Restore error:",error);

    showToast(
      currentLanguage==="es"?
        "El archivo de memoria no es válido.":
        "The memory file isn't valid."
    );
  }finally{
    event.target.value="";
  }
}

async function prepareRecovery(){
  const modal=$("recoveryModal");

  if(!modal){
    showToast(
      currentLanguage==="es"?
        "La recuperación estará disponible en breve.":
        "Recovery will be available shortly."
    );
    return;
  }

  modal.classList.remove("hidden");

  const questions=$("recoveryQuestions");

  if(!questions)return;

  questions.innerHTML="";

  try{
    const data=await api("/api/recovery/questions",{
      method:"POST",
      body:JSON.stringify({
        language:currentLanguage,
        device_id:getDeviceId()
      })
    });

    const list=
      data?.questions||
      [];

    list.forEach((question,index)=>{
      const wrapper=document.createElement("label");
      wrapper.className="recovery-question";

      const title=document.createElement("span");
      title.textContent=
        typeof question==="string"?
          question:
          question.question||
          question.text||
          "";

      const input=document.createElement("input");
      input.type="text";
      input.dataset.questionIndex=String(index);

      wrapper.append(title,input);
      questions.appendChild(wrapper);
    });
  }catch(error){
    console.warn("Recovery questions unavailable:",error);
  }
}

function closeRecovery(){
  const modal=$("recoveryModal");
  if(modal)modal.classList.add("hidden");
}

async function submitRecovery(){
  const modal=$("recoveryModal");

  if(!modal)return;

  const inputs=[
    ...modal.querySelectorAll(
      "input[data-question-index]"
    )
  ];

  const answers=inputs.map(input=>({
    index:Number(input.dataset.questionIndex),
    answer:input.value.trim()
  }));

  try{
    const data=await api("/api/recovery",{
      method:"POST",
      body:JSON.stringify({
        language:currentLanguage,
        device_id:getDeviceId(),
        answers
      })
    });

    if(data?.memory){
      await persistMemory(data.memory);
    }

    closeRecovery();

    showToast(
      currentLanguage==="es"?
        "He reconstruido lo que pudimos recuperar.":
        "I've reconstructed what could be recovered."
    );
  }catch(error){
    console.error("Recovery error:",error);

    showToast(
      currentLanguage==="es"?
        "No pude completar la recuperación.":
        "I couldn't complete recovery."
    );
  }
}

function resetTodayOnly(){
  if(!mirrorMemory)mirrorMemory=loadMemoryLocal();

  const today=getLocalDate();

  mirrorMemory.daily[today]=[];

  persistMemory(mirrorMemory);

  showToast(
    currentLanguage==="es"?
      "La memoria de hoy fue reiniciada.":
      "Today's memory was reset."
  );
}

function exposePublicFunctions(){
  window.askMirror=askMirror;
  window.startVoiceRecognition=startVoiceRecognition;
  window.stopVoiceRecognition=stopVoiceRecognition;
  window.clearMirrorInput=clearInput;
  window.toggleMirrorLanguage=toggleLanguage;
  window.startBreathing=startBreathing;
  window.stopBreathing=stopBreathing;
  window.backupMirrorMemory=backupMemory;
  window.prepareRecovery=prepareRecovery;
  window.closeRecovery=closeRecovery;
  window.submitRecovery=submitRecovery;
  window.resetMirrorToday=resetTodayOnly;
}

async function init(){
  getDeviceId();

  mirrorMemory=await loadMemory();

  bindEvents();
  updateStaticLanguage();
  exposePublicFunctions();

  const recoveryButton=$("recoveryBtn");
  if(recoveryButton&&!recoveryButton.dataset.mirrorRecoveryBound){
    recoveryButton.dataset.mirrorRecoveryBound="1";
    recoveryButton.addEventListener("click",prepareRecovery);
  }

  const recoveryClose=$("recoveryClose");
  if(recoveryClose&&!recoveryClose.dataset.mirrorRecoveryCloseBound){
    recoveryClose.dataset.mirrorRecoveryCloseBound="1";
    recoveryClose.addEventListener("click",closeRecovery);
  }

  const recoverySubmit=$("recoverySubmit");
  if(recoverySubmit&&!recoverySubmit.dataset.mirrorRecoverySubmitBound){
    recoverySubmit.dataset.mirrorRecoverySubmitBound="1";
    recoverySubmit.addEventListener("click",submitRecovery);
  }

  const backupButton=$("backupBtn");
  if(backupButton&&!backupButton.dataset.mirrorBackupBound){
    backupButton.dataset.mirrorBackupBound="1";
    backupButton.addEventListener("click",backupMemory);
  }

  await loadMissions();

  window.addEventListener("beforeunload",()=>{
    stopBreathing();
    stopVoiceRecognition();
  });

  document.addEventListener("visibilitychange",()=>{
    if(document.hidden&&breathingRunning){
      stopBreathing();
    }
  });

  console.log(
    "MIRROR TO YOU initialized.",
    "Today:",
    getLocalDate(),
    "Experiences today:",
    todayHistory().length
  );
}

if(document.readyState==="loading"){
  document.addEventListener("DOMContentLoaded",init);
}else{
  init();
}
