"use strict";

const API="/api";
let memory={},lastResult=null,lastMessage="",lastExperienceId=null;
let recognition=null,isListening=false;
const $=id=>document.getElementById(id);
const today=()=>new Date().toISOString().slice(0,10);

function toast(msg){
  const e=$("toast");
  if(e){e.textContent=msg;e.classList.add("show");setTimeout(()=>e.classList.remove("show"),2600);}
}

async function api(path,options={}){
  const r=await fetch(API+path,{
    headers:{"Content-Type":"application/json",...(options.headers||{})},
    ...options
  });
  const text=await r.text();
  let data={};
  try{data=text?JSON.parse(text):{};}catch{data={detail:text};}
  if(!r.ok)throw new Error(typeof data.detail==="string"?data.detail:JSON.stringify(data.detail||data));
  return data;
}

function loadMemory(){
  try{memory=JSON.parse(localStorage.getItem("mirror_memory")||"{}");}
  catch{memory={};}
  memory.core=memory.core||{};
  memory.preferences=memory.preferences||{};
  memory.dislikes=memory.dislikes||[];
  memory.history=memory.history||[];
  memory.daily=memory.daily||{};
  memory.feedback=memory.feedback||[];
  memory.profile=memory.profile||{};
  return memory;
}

function saveMemory(m){
  memory=m||memory||{};
  try{localStorage.setItem("mirror_memory",JSON.stringify(memory));}catch{}
}

function deviceId(){
  let id=localStorage.getItem("mirror_device_id");
  if(!id){
    id="m-"+crypto.randomUUID();
    localStorage.setItem("mirror_device_id",id);
  }
  return id;
}

function rememberResult(data){
  if(!data)return;
  lastResult=data;
  if(data.memory){
    memory=data.memory;
    saveMemory(memory);
  }
  const d=data.today||today(),arr=memory.daily?.[d]||[];
  const last=arr[arr.length-1];
  if(last?.experience_id)lastExperienceId=last.experience_id;
  if(data.experience_id)lastExperienceId=data.experience_id;
  if(data.mission?.experience_id)lastExperienceId=data.mission.experience_id;
  if(data.mission?.mission_id)lastResult.mission_id=data.mission.mission_id;
}

function setText(id,text){
  const e=$(id);
  if(e)e.textContent=text??"";
}

function show(id,on=true){
  const e=$(id);
  if(e)e.hidden=!on;
}

function renderResponse(data){
  const text=data.message||data.response||data.response_text||"";
  setText("responseText",text);
  setText("responseStatus",data.mission?.status||data.plan?.status||"Ready");
  show("responseSection",!!text);

  const u=data.understanding||{};
  const p=data.personalization||{};
  setText("understandingText",u.summary||u.understanding||data.analysis?.summary||"");
  setValue("companion",u.companion||p.companion||"");
  setValue("duration",u.duration||p.duration||"");
  setValue("destination",u.destination||p.destination||"");
  show("understandingSection",!!(u.summary||u.understanding||data.analysis));

  renderPlan(data.plan||{});
  renderBreathing(data.plan?.breathing||data.breathing);
}

function setValue(id,value){
  const e=$(id);
  if(e)e.value=value||"";
}

function renderPlan(p){
  if(!p||!Object.keys(p).length){show("planSection",false);return;}
  show("planSection",true);
  setText("planTitle",p.title||"Your MIRROR plan");
  setText("planDirection",p.direction||p.action||"");
  setText("planDetails",[
    p.destination&&"Destination: "+p.destination,
    p.budget&&"Budget: "+p.budget,
    p.privacy&&"Privacy: "+p.privacy,
    p.priority&&"Priority: "+p.priority
  ].filter(Boolean).join(" • "));

  const steps=$("planSteps");
  if(steps){
    steps.innerHTML="";
    (p.steps||[]).forEach(x=>{
      const li=document.createElement("li");
      li.textContent=typeof x==="string"?x:(x.text||x.title||JSON.stringify(x));
      steps.appendChild(li);
    });
  }

  const q=$("planQuestions");
  if(q){
    q.innerHTML="";
    (p.questions||[]).forEach(x=>{
      const li=document.createElement("li");
      li.textContent=typeof x==="string"?x:(x.text||x.question||JSON.stringify(x));
      q.appendChild(li);
    });
  }

  const hasDestination=!!p.destination;
  show("destinationWrap",hasDestination);
  show("budgetWrap",!!p.budget);
  show("privacyWrap",!!p.privacy);
  show("priorityWrap",!!p.priority);
}

function renderBreathing(b){
  const e=$("breathingSection")||$("breathing");
  if(!e)return;
  if(!b){e.hidden=true;return;}
  e.hidden=false;
  const title=b.title||"A breathing moment";
  const instruction=b.instruction||b.text||"Breathe slowly and comfortably.";
  e.innerHTML=
    '<div class="breathing-card">'+
    '<div class="breathing-circle" id="breathingCircle"></div>'+
    '<h3>'+escapeHtml(title)+'</h3>'+
    '<p id="breathingInstruction">'+escapeHtml(instruction)+'</p>'+
    '<button type="button" id="breathingStart">START</button>'+
    '</div>';
  $("breathingStart")?.addEventListener("click",startBreathing);
}

let breathingTimer=null;
function startBreathing(){
  clearInterval(breathingTimer);
  const circle=$("breathingCircle"),instruction=$("breathingInstruction");
  if(!circle||!instruction)return;
  const phases=[
    ["Inhale",4],["Hold",2],["Exhale",6]
  ];
  let i=0,left=phases[0][1];
  const tick=()=>{
    const p=phases[i];
    instruction.textContent=p[0]+" • "+left+"s";
    circle.className="breathing-circle "+p[0].toLowerCase();
    if(left<=0){
      i=(i+1)%phases.length;
      left=phases[i][1];
    }else left--;
  };
  tick();
  breathingTimer=setInterval(tick,1000);
}

function escapeHtml(v){
  return String(v??"").replace(/[&<>"']/g,m=>({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"
  }[m]));
}

async function askMirror(){
  const input=$("messageInput");
  const message=(input?.value||"").trim();
  if(!message){toast("Tell MIRROR what you need.");input?.focus();return;}
  lastMessage=message;
  setText("responseText","MIRROR is thinking...");
  show("responseSection",true);
  try{
    const data=await api("/mirror",{
      method:"POST",
      body:JSON.stringify({message,memory})
    });
    rememberResult(data);
    renderResponse(data);
    if($("conciergeStatus"))$("conciergeStatus").textContent="";
  }catch(e){
    console.error("Mirror error:",e);
    setText("responseText","I couldn't complete that request right now.");
    setText("responseStatus",e.message||"Error");
    toast(e.message||"Connection error.");
  }
}

async function sendFeedback(value){
  let id=lastExperienceId;
  if(!id){
    const arr=memory.daily?.[today()]||[];
    id=arr[arr.length-1]?.experience_id||null;
  }
  if(!id){
    toast("There is no experience to rate yet.");
    return;
  }
  try{
    const data=await api("/feedback",{
      method:"POST",
      body:JSON.stringify({
        memory,
        experience_id:id,
        value,
        message:value==="different"?"Give me something different today.":""
      })
    });
    rememberResult(data);
    toast(value==="yes"?"MIRROR learned your preference.":"MIRROR will change the experience.");
  }catch(e){
    console.error("Feedback error:",e);
    toast("Feedback could not be saved.");
  }
}

async function requestConcierge(){
  const input=$("messageInput");
  let message=(input?.value||"").trim();

  if(!message&&lastMessage)message=lastMessage;

  if(!message&&lastResult){
    const p=lastResult.plan||{};
    message=[p.title,p.direction,p.destination].filter(Boolean).join(". ");
  }

  if(!message){
    toast("Tell MIRROR what you need.");
    input?.focus();
    return;
  }

  try{
    if($("conciergeStatus"))$("conciergeStatus").textContent="MIRROR is taking care of it...";
    const data=await api("/concierge",{
      method:"POST",
      body:JSON.stringify({message,memory})
    });
    rememberResult(data);
    if(data.message||data.response)renderResponse(data);
    if($("conciergeStatus"))$("conciergeStatus").textContent=data.message||"MIRROR is handling the next step.";
  }catch(e){
    console.error("Concierge error:",e);
    if($("conciergeStatus"))$("conciergeStatus").textContent="Unable to continue right now.";
    toast(e.message||"Concierge error.");
  }
}

async function revisePlan(){
  if(!lastResult)return toast("Create a MIRROR experience first.");
  try{
    const data=await api("/revise",{
      method:"POST",
      body:JSON.stringify({
        memory,
        plan:lastResult.plan||{},
        message:lastMessage
      })
    });
    rememberResult(data);
    renderResponse(data);
  }catch(e){toast(e.message||"Could not revise the plan.");}
}

function openMaps(){
  const p=lastResult?.plan||{};
  const q=p.destination||$("destination")?.value||"";
  if(!q)return toast("No destination available.");
  window.open(
    "https://www.google.com/maps/search/?api=1&query="+encodeURIComponent(q),
    "_blank","noopener"
  );
}

function openMusic(){
  const p=lastResult?.plan||{};
  const q=p.title||p.category||"relaxing music";
  window.open(
    "https://www.youtube.com/results?search_query="+encodeURIComponent(q+" music"),
    "_blank","noopener"
  );
}

async function loadMissions(){
  try{
    const data=await api("/missions");
    const list=$("missionsList")||$("missions");
    if(!list)return;
    const missions=data.missions||data||[];
    list.innerHTML="";
    missions.forEach(m=>{
      const el=document.createElement("div");
      el.className="mission-item";
      el.textContent=m.title||m.name||"MIRROR experience";
      list.appendChild(el);
    });
  }catch(e){console.warn("Missions:",e.message);}
}

function startVoiceRecognition(){
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!SR){toast("Voice input is not available in this browser.");return;}
  if(isListening){recognition?.stop();return;}

  recognition=new SR();
  recognition.lang=document.documentElement.lang==="es"?"es-US":"en-US";
  recognition.interimResults=false;
  recognition.continuous=false;

  recognition.onstart=()=>{
    isListening=true;
    $("voiceBtn")?.classList.add("active");
    toast("Listening...");
  };
  recognition.onresult=e=>{
    const text=e.results[0][0].transcript;
    const input=$("messageInput");
    if(input)input.value=(input.value+" "+text).trim();
  };
  recognition.onerror=e=>toast("Voice error: "+e.error);
  recognition.onend=()=>{
    isListening=false;
    $("voiceBtn")?.classList.remove("active");
  };
  recognition.start();
}

function speak(text){
  if(!text||!window.speechSynthesis)return;
  speechSynthesis.cancel();
  const u=new SpeechSynthesisUtterance(text);
  u.lang=document.documentElement.lang==="es"?"es-US":"en-US";
  u.rate=.95;
  speechSynthesis.speak(u);
}

function clearAll(){
  const input=$("messageInput");
  if(input)input.value="";
  lastMessage="";
  lastResult=null;
  lastExperienceId=null;
  ["responseSection","understandingSection","planSection"].forEach(id=>show(id,false));
  setText("conciergeStatus","");
}

function backupMemory(){
  const blob=new Blob([JSON.stringify(memory,null,2)],{type:"application/json"});
  const a=document.createElement("a");
  a.href=URL.createObjectURL(blob);
  a.download="mirror-memory.json";
  a.click();
  setTimeout(()=>URL.revokeObjectURL(a.href),1000);
}

function restoreMemory(file){
  if(!file)return;
  const reader=new FileReader();
  reader.onload=()=>{
    try{
      memory=JSON.parse(reader.result);
      saveMemory(memory);
      toast("MIRROR memory restored.");
    }catch{toast("Invalid memory file.");}
  };
  reader.readAsText(file);
}

function clearMemory(){
  if(!confirm("Clear MIRROR memory on this device?"))return;
  localStorage.removeItem("mirror_memory");
  memory={};
  loadMemory();
  toast("MIRROR memory cleared.");
}

async function recovery(){
  try{
    const data=await api("/recovery/questions");
    const modal=$("recoveryModal");
    if(modal){
      modal.hidden=false;
      const box=modal.querySelector("[data-recovery-content]")||modal;
      box.innerHTML=(data.questions||[]).map(q=>"<p>"+escapeHtml(q.text||q.question||q)+"</p>").join("");
    }
  }catch(e){toast(e.message||"Recovery unavailable.");}
}

function updateStaticLanguage(){
  const lang=localStorage.getItem("mirror_language")||"en";
  document.documentElement.lang=lang;
  const btn=$("languageBtn");
  if(btn)btn.textContent=lang==="es"?"EN":"ES";
}

function toggleLanguage(){
  const current=localStorage.getItem("mirror_language")||"en";
  localStorage.setItem("mirror_language",current==="en"?"es":"en");
  updateStaticLanguage();
}

function bind(id,event,fn){
  $(id)?.addEventListener(event,fn);
}

function init(){
  loadMemory();
  deviceId();
  updateStaticLanguage();

  bind("askBtn","click",askMirror);
  bind("clearBtn","click",clearAll);
  bind("voiceBtn","click",startVoiceRecognition);
  bind("languageBtn","click",toggleLanguage);
  bind("conciergeBtn","click",requestConcierge);
  bind("mapsBtn","click",openMaps);
  bind("musicBtn","click",openMusic);
  bind("feedbackYes","click",()=>sendFeedback("yes"));
  bind("feedbackDifferent","click",()=>sendFeedback("different"));
  bind("backupBtn","click",backupMemory);
  bind("clearMemoryBtn","click",clearMemory);
  bind("recoveryBtn","click",recovery);

  const restore=$("restoreFile");
  if(restore)restore.addEventListener("change",e=>restoreMemory(e.target.files?.[0]));

  const input=$("messageInput");
  if(input){
    input.addEventListener("keydown",e=>{
      if(e.key==="Enter"&&!e.shiftKey){
        e.preventDefault();
        askMirror();
      }
    });
  }

  document.querySelectorAll("[data-message]").forEach(e=>{
    e.addEventListener("click",()=>{
      if(input)input.value=e.dataset.message||e.textContent.trim();
      input?.focus();
    });
  });

  document.querySelectorAll("[data-suggestion]").forEach(e=>{
    e.addEventListener("click",()=>{
      if(input)input.value=e.dataset.suggestion||e.textContent.trim();
      input?.focus();
    });
  });

  window.startVoiceRecognition=startVoiceRecognition;
  window.askMirror=askMirror;
  window.sendFeedback=sendFeedback;
  window.requestConcierge=requestConcierge;
  window.openMaps=openMaps;
  window.openMusic=openMusic;
  window.clearAll=clearAll;

  loadMissions();
}

document.addEventListener("DOMContentLoaded",init);
