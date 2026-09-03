"use strict";

const API="/api";
let memory={};
let lastResult=null;
let lastMessage="";
let lastExperienceId=null;
let currentLanguage=localStorage.getItem("mirror_language")||"en";
let recognition=null;
let isListening=false;
let requestBusy=false;
let breathingTimer=null;

const $=id=>document.getElementById(id);
const today=()=>new Date().toISOString().slice(0,10);

const TEXT={
 en:{
  thinking:"MIRROR is thinking...",
  listening:"Listening...",
  tell:"Tell MIRROR what you need.",
  ready:"Ready",
  connection:"Connection error.",
  voice:"Voice input is not available in this browser.",
  voiceError:"Voice input error.",
  noExperience:"There is no experience to rate yet.",
  learned:"MIRROR learned your preference.",
  different:"MIRROR will create a different experience.",
  concierge:"MIRROR is taking care of it...",
  conciergeReady:"MIRROR is handling the next step.",
  conciergeError:"Unable to continue right now.",
  noDestination:"No destination is available.",
  noPlan:"Create a MIRROR experience first.",
  memoryRestored:"MIRROR memory restored.",
  invalidMemory:"Invalid memory file.",
  memoryCleared:"MIRROR memory cleared.",
  recoveryError:"Recovery is not available right now.",
  breathingStart:"START",
  inhale:"Inhale",
  hold:"Hold",
  exhale:"Exhale",
  destination:"Destination",
  budget:"Budget",
  privacy:"Privacy",
  priority:"Priority",
  status:"Ready",
  experience:"MIRROR experience"
 },
 es:{
  thinking:"MIRROR está pensando...",
  listening:"Escuchando...",
  tell:"Dile a MIRROR lo que necesitas.",
  ready:"Listo",
  connection:"Error de conexión.",
  voice:"La entrada por voz no está disponible en este navegador.",
  voiceError:"Error de entrada por voz.",
  noExperience:"Todavía no hay una experiencia para valorar.",
  learned:"MIRROR aprendió tu preferencia.",
  different:"MIRROR creará una experiencia diferente.",
  concierge:"MIRROR se está encargando...",
  conciergeReady:"MIRROR está gestionando el siguiente paso.",
  conciergeError:"No es posible continuar en este momento.",
  noDestination:"No hay un destino disponible.",
  noPlan:"Primero crea una experiencia con MIRROR.",
  memoryRestored:"La memoria de MIRROR fue restaurada.",
  invalidMemory:"El archivo de memoria no es válido.",
  memoryCleared:"La memoria de MIRROR fue eliminada.",
  recoveryError:"La recuperación no está disponible en este momento.",
  breathingStart:"COMENZAR",
  inhale:"Inhala",
  hold:"Mantén",
  exhale:"Exhala",
  destination:"Destino",
  budget:"Presupuesto",
  privacy:"Privacidad",
  priority:"Prioridad",
  status:"Listo",
  experience:"Experiencia MIRROR"
 }
};

function t(key){
  return TEXT[currentLanguage]?.[key]||TEXT.en[key]||key;
}

function setLanguage(lang){
  currentLanguage=lang==="es"?"es":"en";
  localStorage.setItem("mirror_language",currentLanguage);
  memory.preferences=memory.preferences||{};
  memory.preferences.language=currentLanguage;
  saveMemory(memory);
  document.documentElement.lang=currentLanguage;
  document.documentElement.dir="ltr";
  updateStaticLanguage();
}

function updateStaticLanguage(){
  document.documentElement.lang=currentLanguage;
  const b=$("languageBtn");
  if(b)b.textContent=currentLanguage==="es"?"EN":"ES";

  const voice=$("voiceBtn");
  if(voice)voice.setAttribute("aria-label",currentLanguage==="es"?"Entrada por voz":"Voice input");

  const clear=$("clearBtn");
  if(clear)clear.setAttribute("aria-label",currentLanguage==="es"?"Limpiar":"Clear");
}

function toggleLanguage(){
  setLanguage(currentLanguage==="es"?"en":"es");
  toast(currentLanguage==="es"?"Español":"English");
}

function toast(message){
  const e=$("toast");
  if(!e)return;
  e.textContent=String(message||"");
  e.classList.add("show");
  clearTimeout(toast.timer);
  toast.timer=setTimeout(()=>e.classList.remove("show"),2600);
}

async function api(path,options={}){
  const controller=new AbortController();
  const timeout=setTimeout(()=>controller.abort(),45000);

  try{
    const headers={
      "Content-Type":"application/json",
      ...(options.headers||{})
    };

    const response=await fetch(API+path,{
      ...options,
      headers,
      signal:controller.signal
    });

    const raw=await response.text();
    let data={};

    try{
      data=raw?JSON.parse(raw):{};
    }catch{
      data={detail:raw||""};
    }

    if(!response.ok){
      let error=data.detail||data.message||data.error||"Request failed";
      if(typeof error!=="string")error=JSON.stringify(error);
      throw new Error(error);
    }

    return data;
  }catch(error){
    if(error.name==="AbortError")throw new Error(
      currentLanguage==="es"
      ?"La solicitud tardó demasiado."
      :"The request took too long."
    );
    throw error;
  }finally{
    clearTimeout(timeout);
  }
}

function loadMemory(){
  try{
    memory=JSON.parse(localStorage.getItem("mirror_memory")||"{}");
  }catch{
    memory={};
  }

  if(!memory||typeof memory!=="object")memory={};

  memory.core=memory.core||{};
  memory.preferences=memory.preferences||{};
  memory.dislikes=Array.isArray(memory.dislikes)?memory.dislikes:[];
  memory.history=Array.isArray(memory.history)?memory.history:[];
  memory.daily=memory.daily||{};
  memory.feedback=Array.isArray(memory.feedback)?memory.feedback:[];
  memory.profile=memory.profile||{};

  if(memory.preferences.language){
    currentLanguage=memory.preferences.language==="es"?"es":"en";
  }

  return memory;
}

function saveMemory(data){
  if(data&&typeof data==="object")memory=data;

  try{
    localStorage.setItem("mirror_memory",JSON.stringify(memory));
  }catch(error){
    console.warn("Memory save:",error);
  }
}

function deviceId(){
  let id=localStorage.getItem("mirror_device_id");

  if(!id){
    try{
      id=crypto.randomUUID();
    }catch{
      id="m-"+Date.now()+"-"+Math.random().toString(36).slice(2);
    }
    localStorage.setItem("mirror_device_id",id);
  }

  return id;
}

function languagePayload(){
  return {
    language:currentLanguage,
    device_id:deviceId()
  };
}

function rememberResult(data){
  if(!data)return;

  lastResult=data;

  if(data.memory){
    memory=data.memory;
    memory.preferences=memory.preferences||{};
    memory.preferences.language=currentLanguage;
    saveMemory(memory);
  }

  const date=data.today||today();
  const day=memory.daily?.[date]||[];
  const last=day[day.length-1];

  if(last?.experience_id)lastExperienceId=last.experience_id;
  if(data.experience_id)lastExperienceId=data.experience_id;
  if(data.mission?.experience_id)lastExperienceId=data.mission.experience_id;
  if(data.plan?.experience_id)lastExperienceId=data.plan.experience_id;
}

function setText(id,value){
  const e=$(id);
  if(e)e.textContent=value==null?"":String(value);
}

function show(id,visible=true){
  const e=$(id);
  if(e)e.hidden=!visible;
}

function setValue(id,value){
  const e=$(id);
  if(e)e.value=value==null?"":String(value);
}

function escapeHtml(value){
  return String(value??"").replace(/[&<>"']/g,char=>({
    "&":"&amp;",
    "<":"&lt;",
    ">":"&gt;",
    "\"":"&quot;",
    "'":"&#039;"
  }[char]));
}

function textOf(value){
  if(typeof value==="string")return value;
  if(!value||typeof value!=="object")return "";
  return value.text||value.title||value.question||value.name||"";
}

function renderResponse(data){
  if(!data)return;

  const message=
    data.message||
    data.response||
    data.response_text||
    data.plan?.direction||
    "";

  setText("responseText",message);
  setText(
    "responseStatus",
    data.mission?.status||
    data.plan?.status||
    t("ready")
  );

  show("responseSection",!!message);

  const u=data.understanding||{};
  const p=data.personalization||{};
  const a=data.analysis||{};

  setText(
    "understandingText",
    u.summary||
    u.understanding||
    a.summary||
    ""
  );

  setValue(
    "companion",
    u.companion||p.companion||""
  );

  setValue(
    "duration",
    u.duration||p.duration||""
  );

  setValue(
    "destination",
    u.destination||p.destination||""
  );

  show(
    "understandingSection",
    !!(u.summary||u.understanding||a.summary)
  );

  renderPlan(data.plan||{});
  renderBreathing(data.plan?.breathing||data.breathing);
}

function renderPlan(plan){
  if(!plan||typeof plan!=="object"||!Object.keys(plan).length){
    show("planSection",false);
    return;
  }

  show("planSection",true);

  setText(
    "planTitle",
    plan.title||t("experience")
  );

  setText(
    "planDirection",
    plan.direction||
    plan.action||
    ""
  );

  const details=[];

  if(plan.destination)
    details.push(t("destination")+": "+plan.destination);

  if(plan.budget)
    details.push(t("budget")+": "+plan.budget);

  if(plan.privacy)
    details.push(t("privacy")+": "+plan.privacy);

  if(plan.priority)
    details.push(t("priority")+": "+plan.priority);

  setText("planDetails",details.join(" • "));

  renderList("planSteps",plan.steps);
  renderList("planQuestions",plan.questions);

  show("destinationWrap",!!plan.destination);
  show("budgetWrap",!!plan.budget);
  show("privacyWrap",!!plan.privacy);
  show("priorityWrap",!!plan.priority);
}

function renderList(id,items){
  const element=$(id);
  if(!element)return;

  element.innerHTML="";

  if(!Array.isArray(items))return;

  items.forEach(item=>{
    const text=textOf(item);
    if(!text)return;

    const li=document.createElement("li");
    li.textContent=text;
    element.appendChild(li);
  });
}

function renderBreathing(data){
  const section=$("breathingSection")||$("breathing");
  if(!section)return;

  clearInterval(breathingTimer);
  breathingTimer=null;

  if(!data){
    section.hidden=true;
    return;
  }

  const title=
    data.title||
    (currentLanguage==="es"?"Un momento para respirar":"A breathing moment");

  const instruction=
    data.instruction||
    data.text||
    (currentLanguage==="es"
      ?"Respira lentamente y con comodidad."
      :"Breathe slowly and comfortably.");

  section.hidden=false;

  section.innerHTML=
    '<div class="breathing-card">'+
      '<div class="breathing-circle" id="breathingCircle"></div>'+
      '<h3>'+escapeHtml(title)+'</h3>'+
      '<p id="breathingInstruction">'+escapeHtml(instruction)+'</p>'+
      '<button type="button" id="breathingStart">'+
        escapeHtml(t("breathingStart"))+
      '</button>'+
    '</div>';

  const start=$("breathingStart");
  if(start)start.addEventListener("click",startBreathing,{once:false});
}

function startBreathing(){
  clearInterval(breathingTimer);

  const circle=$("breathingCircle");
  const instruction=$("breathingInstruction");

  if(!circle||!instruction)return;

  const phases=[
    {name:"inhale",text:t("inhale"),seconds:4},
    {name:"hold",text:t("hold"),seconds:2},
    {name:"exhale",text:t("exhale"),seconds:6}
  ];

  let phase=0;
  let remaining=phases[0].seconds;

  const update=()=>{
    const current=phases[phase];

    instruction.textContent=
      current.text+" • "+remaining+"s";

    circle.className=
      "breathing-circle "+current.name;

    if(remaining<=1){
      phase=(phase+1)%phases.length;
      remaining=phases[phase].seconds;
    }else{
      remaining--;
    }
  };

  update();
  breathingTimer=setInterval(update,1000);
}

async function askMirror(){
  if(requestBusy)return;

  const input=$("messageInput");
  const message=(input?.value||"").trim();

  if(!message){
    toast(t("tell"));
    input?.focus();
    return;
  }

  requestBusy=true;
  lastMessage=message;

  const ask=$("askBtn");
  if(ask)ask.disabled=true;

  setText("responseText",t("thinking"));
  setText("responseStatus",t("ready"));
  show("responseSection",true);

  try{
    const data=await api("/mirror",{
      method:"POST",
      body:JSON.stringify({
        message,
        memory,
        ...languagePayload()
      })
    });

    rememberResult(data);
    renderResponse(data);

  }catch(error){
    console.error("Mirror error:",error);
    setText(
      "responseText",
      currentLanguage==="es"
      ?"No pude completar la solicitud en este momento."
      :"I couldn't complete that request right now."
    );
    setText("responseStatus",error.message||t("connection"));
    toast(error.message||t("connection"));

  }finally{
    requestBusy=false;
    if(ask)ask.disabled=false;
  }
}

async function sendFeedback(value){
  if(requestBusy)return;

  let id=lastExperienceId;

  if(!id){
    const day=memory.daily?.[today()]||[];
    const last=day[day.length-1];
    id=last?.experience_id||null;
  }

  if(!id){
    toast(t("noExperience"));
    return;
  }

  requestBusy=true;

  try{
    const data=await api("/feedback",{
      method:"POST",
      body:JSON.stringify({
        memory,
        experience_id:String(id),
        value:String(value||""),
        message:value==="different"
          ?(
            currentLanguage==="es"
            ?"Quiero una experiencia diferente."
            :"I want a different experience."
          )
          :"",
        ...languagePayload()
      })
    });

    rememberResult(data);

    toast(
      value==="different"
      ?t("different")
      :t("learned")
    );

  }catch(error){
    console.error("Feedback error:",error);
    toast(error.message||t("connection"));

  }finally{
    requestBusy=false;
  }
}

async function requestConcierge(){
  if(requestBusy)return;

  const input=$("messageInput");
  let message=(input?.value||"").trim();

  if(!message)message=lastMessage;

  if(!message&&lastResult){
    const plan=lastResult.plan||{};
    message=[
      plan.title,
      plan.direction,
      plan.destination
    ].filter(Boolean).join(". ");
  }

  if(!message){
    toast(t("tell"));
    input?.focus();
    return;
  }

  requestBusy=true;

  const button=$("conciergeBtn");
  if(button)button.disabled=true;

  setText("conciergeStatus",t("concierge"));

  try{
    const data=await api("/concierge",{
      method:"POST",
      body:JSON.stringify({
        message,
        memory,
        ...languagePayload()
      })
    });

    rememberResult(data);

    if(data.message||data.response||data.plan)
      renderResponse(data);

    setText(
      "conciergeStatus",
      data.message||data.response||t("conciergeReady")
    );

  }catch(error){
    console.error("Concierge error:",error);
    setText("conciergeStatus",t("conciergeError"));
    toast(error.message||t("connection"));

  }finally{
    requestBusy=false;
    if(button)button.disabled=false;
  }
}

async function revisePlan(){
  if(requestBusy)return;

  if(!lastResult){
    toast(t("noPlan"));
    return;
  }

  requestBusy=true;

  try{
    const data=await api("/revise",{
      method:"POST",
      body:JSON.stringify({
        memory,
        plan:lastResult.plan||{},
        message:lastMessage,
        ...languagePayload()
      })
    });

    rememberResult(data);
    renderResponse(data);

  }catch(error){
    console.error("Revision error:",error);
    toast(error.message||t("connection"));

  }finally{
    requestBusy=false;
  }
}

function openMaps(){
  const plan=lastResult?.plan||{};
  const destination=
    plan.destination||
    $("destination")?.value||
    "";

  if(!destination){
    toast(t("noDestination"));
    return;
  }

  const url=
    "https://www.google.com/maps/search/?api=1&query="+
    encodeURIComponent(destination);

  window.open(url,"_blank","noopener,noreferrer");
}

function openMusic(){
  const plan=lastResult?.plan||{};
  const query=
    plan.title||
    plan.category||
    (currentLanguage==="es"?"música relajante":"relaxing music");

  const url=
    "https://www.youtube.com/results?search_query="+
    encodeURIComponent(query+" music");

  window.open(url,"_blank","noopener,noreferrer");
}

async function loadMissions(){
  try{
    const data=await api("/missions");
    const list=$("missionsList")||$("missions");

    if(!list)return;

    const missions=
      Array.isArray(data)
      ?data
      :(data.missions||[]);

    list.innerHTML="";

    missions.forEach(mission=>{
      const title=
        textOf(mission)||
        (currentLanguage==="es"
          ?"Experiencia MIRROR"
          :"MIRROR experience");

      const element=document.createElement("div");
      element.className="mission-item";
      element.textContent=title;
      list.appendChild(element);
    });

  }catch(error){
    console.warn("Missions:",error.message);
  }
}

function startVoiceRecognition(){
  const SpeechRecognition=
    window.SpeechRecognition||
    window.webkitSpeechRecognition;

  if(!SpeechRecognition){
    toast(t("voice"));
    return;
  }

  if(isListening){
    recognition?.stop();
    return;
  }

  recognition=new SpeechRecognition();

  recognition.lang=
    currentLanguage==="es"
    ?"es-US"
    :"en-US";

  recognition.interimResults=false;
  recognition.continuous=false;
  recognition.maxAlternatives=1;

  recognition.onstart=()=>{
    isListening=true;
    $("voiceBtn")?.classList.add("active");
    toast(t("listening"));
  };

  recognition.onresult=event=>{
    const text=
      event.results?.[0]?.[0]?.transcript||
      "";

    const input=$("messageInput");

    if(input&&text)
      input.value=(input.value+" "+text).trim();
  };

  recognition.onerror=event=>{
    console.error("Voice:",event.error);
    toast(t("voiceError"));
  };

  recognition.onend=()=>{
    isListening=false;
    $("voiceBtn")?.classList.remove("active");
  };

  try{
    recognition.start();
  }catch(error){
    console.warn("Voice start:",error);
    isListening=false;
  }
}

function speak(text){
  if(!text||!window.speechSynthesis)return;

  try{
    speechSynthesis.cancel();

    const utterance=
      new SpeechSynthesisUtterance(String(text));

    utterance.lang=
      currentLanguage==="es"
      ?"es-US"
      :"en-US";

    utterance.rate=.95;
    utterance.pitch=1;

    speechSynthesis.speak(utterance);
  }catch(error){
    console.warn("Speech:",error);
  }
}

function clearAll(){
  clearInterval(breathingTimer);
  breathingTimer=null;

  const input=$("messageInput");
  if(input)input.value="";

  lastMessage="";
  lastResult=null;
  lastExperienceId=null;

  show("responseSection",false);
  show("understandingSection",false);
  show("planSection",false);
  show("breathingSection",false);

  setText("conciergeStatus","");

  if(window.speechSynthesis)
    speechSynthesis.cancel();

  toast(
    currentLanguage==="es"
    ?"Listo para una nueva experiencia."
    :"Ready for a new experience."
  );
}

function backupMemory(){
  try{
    const copy={
      ...memory,
      preferences:{
        ...(memory.preferences||{}),
        language:currentLanguage
      }
    };

    const blob=new Blob(
      [JSON.stringify(copy,null,2)],
      {type:"application/json"}
    );

    const url=URL.createObjectURL(blob);
    const link=document.createElement("a");

    link.href=url;
    link.download="mirror-memory.json";
    document.body.appendChild(link);
    link.click();
    link.remove();

    setTimeout(()=>URL.revokeObjectURL(url),1000);

  }catch(error){
    console.error("Backup:",error);
    toast(
      currentLanguage==="es"
      ?"No se pudo crear la copia."
      :"The backup could not be created."
    );
  }
}

function restoreMemory(file){
  if(!file)return;

  const reader=new FileReader();

  reader.onload=event=>{
    try{
      const restored=JSON.parse(event.target.result);

      if(!restored||typeof restored!=="object")
        throw new Error("Invalid memory");

      memory=restored;
      memory.core=memory.core||{};
      memory.preferences=memory.preferences||{};
      memory.history=Array.isArray(memory.history)
        ?memory.history:[];
      memory.daily=memory.daily||{};
      memory.feedback=Array.isArray(memory.feedback)
        ?memory.feedback:[];
      memory.profile=memory.profile||{};

      if(memory.preferences.language)
        currentLanguage=
          memory.preferences.language==="es"
          ?"es"
          :"en";

      saveMemory(memory);
      updateStaticLanguage();

      toast(t("memoryRestored"));

    }catch(error){
      console.error("Restore:",error);
      toast(t("invalidMemory"));
    }
  };

  reader.onerror=()=>{
    toast(t("invalidMemory"));
  };

  reader.readAsText(file);
}

function clearMemory(){
  const question=
    currentLanguage==="es"
    ?"¿Eliminar la memoria de MIRROR de este dispositivo?"
    :"Clear MIRROR memory from this device?";

  if(!window.confirm(question))return;

  localStorage.removeItem("mirror_memory");

  memory={
    core:{},
    preferences:{language:currentLanguage},
    dislikes:[],
    history:[],
    daily:{},
    feedback:[],
    profile:{}
  };

  saveMemory(memory);
  toast(t("memoryCleared"));
}

async function recovery(){
  try{
    const data=await api(
      "/recovery/questions?language="+
      encodeURIComponent(currentLanguage)
    );

    const modal=$("recoveryModal");

    if(!modal)return;

    modal.hidden=false;

    const content=
      modal.querySelector("[data-recovery-content]")||
      modal;

    content.innerHTML="";

    const questions=data.questions||[];

    questions.forEach(question=>{
      const p=document.createElement("p");
      p.textContent=textOf(question);
      content.appendChild(p);
    });

  }catch(error){
    console.error("Recovery:",error);
    toast(error.message||t("recoveryError"));
  }
}

function closeRecovery(){
  const modal=$("recoveryModal");
  if(modal)modal.hidden=true;
}

function bind(id,event,handler){
  const element=$(id);
  if(element)
    element.addEventListener(event,handler);
}

function bindSuggestions(){
  document.querySelectorAll(
    "[data-message],[data-suggestion]"
  ).forEach(element=>{
    element.addEventListener("click",()=>{
      const input=$("messageInput");
      if(!input)return;

      const value=
        element.dataset.message||
        element.dataset.suggestion||
        element.textContent||
        "";

      input.value=value.trim();
      input.focus();
    });
  });
}

function bindRecovery(){
  const file=$("restoreFile");

  if(file){
    file.addEventListener("change",event=>{
      const selected=event.target.files?.[0];
      restoreMemory(selected);
      event.target.value="";
    });
  }

  document.querySelectorAll(
    "[data-close-recovery]"
  ).forEach(element=>{
    element.addEventListener("click",closeRecovery);
  });
}

function bindKeyboard(){
  const input=$("messageInput");
  if(!input)return;

  input.addEventListener("keydown",event=>{
    if(
      event.key==="Enter"&&
      !event.shiftKey&&
      !event.isComposing
    ){
      event.preventDefault();
      askMirror();
    }
  });
}

function init(){
  loadMemory();
  deviceId();

  if(memory.preferences?.language)
    currentLanguage=
      memory.preferences.language==="es"
      ?"es"
      :"en";

  setLanguage(currentLanguage);

  bind("askBtn","click",askMirror);
  bind("clearBtn","click",clearAll);
  bind("voiceBtn","click",startVoiceRecognition);
  bind("languageBtn","click",toggleLanguage);

  bind("conciergeBtn","click",requestConcierge);
  bind("mapsBtn","click",openMaps);
  bind("musicBtn","click",openMusic);

  bind(
    "feedbackYes",
    "click",
    ()=>sendFeedback("yes")
  );

  bind(
    "feedbackDifferent",
    "click",
    ()=>sendFeedback("different")
  );

  bind(
    "backupBtn",
    "click",
    backupMemory
  );

  bind(
    "clearMemoryBtn",
    "click",
    clearMemory
  );

  bind(
    "recoveryBtn",
    "click",
    recovery
  );

  bind(
    "reviseBtn",
    "click",
    revisePlan
  );

  bindKeyboard();
  bindSuggestions();
  bindRecovery();

  window.askMirror=askMirror;
  window.sendFeedback=sendFeedback;
  window.requestConcierge=requestConcierge;
  window.startVoiceRecognition=startVoiceRecognition;
  window.openMaps=openMaps;
  window.openMusic=openMusic;
  window.clearAll=clearAll;
  window.revisePlan=revisePlan;
  window.speak=speak;

  loadMissions();
}

if(document.readyState==="loading"){
  document.addEventListener(
    "DOMContentLoaded",
    init,
    {once:true}
  );
}else{
  init();
}
