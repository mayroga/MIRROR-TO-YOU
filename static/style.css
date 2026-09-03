const API_BASE="";
const DB_NAME="mirror_to_you";
const DB_VERSION=1;
const STORE="memory";
let memory={
  core:{},moment:{},preferences:{},dislikes:[],history:[],learning:{}
};
let currentResult=null;
let currentMission=null;
let recognition=null;
let listening=false;
let speaking=false;
let breathingTimer=null;
let breathingRunning=false;
let breathingPaused=false;
let breathingSeconds=600;
let breathingPhaseTimer=null;
let confirmAction=null;

const $=id=>document.getElementById(id);

function normalizeMemory(data){
  data=data&&typeof data==="object"?data:{};
  const obj=v=>v&&typeof v==="object"&&!Array.isArray(v)?v:{};
  const arr=v=>Array.isArray(v)?v:[];
  return{
    core:obj(data.core),
    moment:obj(data.moment),
    preferences:obj(data.preferences),
    dislikes:arr(data.dislikes),
    history:arr(data.history),
    learning:obj(data.learning),
    ...(data.recovered_at?{recovered_at:data.recovered_at}:{})
  };
}

function show(id){
  document.querySelectorAll(".screen").forEach(x=>x.classList.remove("active"));
  const el=$(id);
  if(el)el.classList.add("active");
}

function setHidden(id,hidden=true){
  const el=$(id);
  if(el)el.classList.toggle("hidden",hidden);
}

function toast(message){
  const el=$("toast");
  if(!el)return;
  el.textContent=message||"";
  el.classList.remove("hidden");
  clearTimeout(el._timer);
  el._timer=setTimeout(()=>el.classList.add("hidden"),3500);
}

function setThinking(on){
  setHidden("thinking",!on);
}

function escapeText(value){
  return String(value??"").trim();
}

function openDB(){
  return new Promise((resolve,reject)=>{
    if(!window.indexedDB)return reject(new Error("IndexedDB unavailable"));
    const req=indexedDB.open(DB_NAME,DB_VERSION);
    req.onupgradeneeded=()=>{
      const db=req.result;
      if(!db.objectStoreNames.contains(STORE))db.createObjectStore(STORE);
    };
    req.onsuccess=()=>resolve(req.result);
    req.onerror=()=>reject(req.error||new Error("Database error"));
  });
}

async function saveMemory(data=memory){
  memory=normalizeMemory(data);
  try{
    const db=await openDB();
    await new Promise((resolve,reject)=>{
      const tx=db.transaction(STORE,"readwrite");
      tx.objectStore(STORE).put(memory,"profile");
      tx.oncomplete=resolve;
      tx.onerror=()=>reject(tx.error||new Error("Save error"));
    });
    db.close();
  }catch(e){
    try{localStorage.setItem("mirror_memory",JSON.stringify(memory));}catch(_){}
  }
}

async function loadMemory(){
  try{
    const db=await openDB();
    const data=await new Promise((resolve,reject)=>{
      const tx=db.transaction(STORE,"readonly");
      const req=tx.objectStore(STORE).get("profile");
      req.onsuccess=()=>resolve(req.result);
      req.onerror=()=>reject(req.error);
    });
    db.close();
    if(data){
      memory=normalizeMemory(data);
      await saveMemory(memory);
      return memory;
    }
  }catch(e){}
  try{
    const old=localStorage.getItem("mirror_memory");
    if(old){
      memory=normalizeMemory(JSON.parse(old));
      await saveMemory(memory);
    }
  }catch(e){}
  return memory;
}

function deviceId(){
  let id=localStorage.getItem("mirror_device_id");
  if(!id){
    id=(crypto.randomUUID?crypto.randomUUID():Date.now()+"-"+Math.random());
    localStorage.setItem("mirror_device_id",id);
  }
  return id;
}

async function api(path,options={},timeout=15000){
  const controller=new AbortController();
  const timer=setTimeout(()=>controller.abort(),timeout);
  try{
    const opts={...options,signal:controller.signal,headers:{
      "Content-Type":"application/json",
      ...(options.headers||{})
    }};
    const response=await fetch(API_BASE+path,opts);
    let data=null;
    const type=response.headers.get("content-type")||"";
    if(type.includes("application/json")){
      try{data=await response.json();}catch(_){}
    }else{
      try{data={text:await response.text()};}catch(_){}
    }
    if(!response.ok){
      const detail=data?.error||data?.detail||data?.message||`Request failed (${response.status})`;
      const error=new Error(Array.isArray(detail)?detail.map(x=>x.msg||"Invalid request").join(", "):String(detail));
      error.status=response.status;
      throw error;
    }
    return data||{};
  }catch(e){
    if(e.name==="AbortError")throw new Error("MIRROR took too long to respond. Please try again.");
    if(!navigator.onLine)throw new Error("You appear to be offline.");
    throw e;
  }finally{
    clearTimeout(timer);
  }
}

function addMessage(text,type="mirror"){
  const box=$("conversationMessages");
  if(!box)return;
  const item=document.createElement("div");
  item.className=`message ${type}`;
  const content=document.createElement("div");
  content.className="message-content";
  content.textContent=escapeText(text);
  item.appendChild(content);
  box.appendChild(item);
  box.scrollTop=box.scrollHeight;
}

function clearPlan(){
  setHidden("planArea",true);
  setHidden("questionArea",true);
  setHidden("mapsButton",true);
  setHidden("musicButton",true);
  setHidden("conciergeButton",true);
  const d=$("directions");
  if(d)d.replaceChildren();
}

function renderPlan(result){
  currentResult=result||null;
  currentMission=result?.mission||null;

  const plan=result?.plan||result?.proposal||{};
  const understanding=result?.understanding||result?.analysis||{};
  const reply=result?.message||plan.reply||"";
  const title=plan.title||"Let MIRROR take care of it";
  const directions=Array.isArray(plan.direction)?plan.direction:[];

  $("planTitle").textContent=title;
  $("planReply").textContent=reply;

  const box=$("directions");
  box.replaceChildren();

  directions.slice(0,5).forEach(text=>{
    const item=document.createElement("div");
    item.className="direction";
    item.textContent=escapeText(text);
    box.appendChild(item);
  });

  const question=plan.question||result?.questions?.[0]||"";
  $("mirrorQuestion").textContent=question;
  setHidden("questionArea",!question);

  const intent=understanding.intent||"";
  const destination=understanding.destination||plan.destination||"";
  setHidden("mapsButton",!(destination||intent==="MAPS"));
  setHidden("musicButton",!(intent==="MUSIC"||understanding.signals?.includes?.("MUSIC")));
  setHidden("conciergeButton",!["CONCIERGE","URGENT"].includes(plan.action||result?.decision?.action));

  setHidden("planArea",false);

  if(reply)speak(reply);
}

function updateMemoryFromResult(result){
  const u=result?.understanding||result?.analysis||{};
  const p=result?.personalization||{};
  const stamp={
    at:new Date().toISOString(),
    intent:u.intent||"",
    destination:u.destination||"",
    signals:u.signals||[]
  };

  memory=normalizeMemory(memory);

  if(u.language)memory.moment.language=u.language;
  if(u.companion)memory.moment.companion=u.companion;
  if(u.destination)memory.moment.destination=u.destination;
  if(u.intent)memory.moment.intent=u.intent;
  if(u.signals?.length)memory.moment.signals=u.signals;

  if(p.name&&!memory.core.name)memory.core.name=p.name;

  memory.history.push(stamp);
  if(memory.history.length>30)memory.history=memory.history.slice(-30);

  saveMemory(memory);
}

async function askMirror(){
  const input=$("messageInput");
  const text=escapeText(input?.value);
  if(!text)return;
  if(text.length>2000)return;

  input.value="";
  input.style.height="auto";
  addMessage(text,"client");
  setThinking(true);
  $("sendButton").disabled=true;
  $("voiceButton").disabled=true;

  try{
    memory=normalizeMemory(memory);
    const result=await api("/api/mirror",{
      method:"POST",
      body:JSON.stringify({
        message:text,
        language:navigator.language?.slice(0,2)||"en",
        device_id:deviceId(),
        memory
      })
    },18000);

    updateMemoryFromResult(result);

    const reply=result?.message||result?.plan?.reply||result?.proposal?.reply;
    if(reply)addMessage(reply,"mirror");

    renderPlan(result);

    if(result?.decision?.action==="ASK"){
      setHidden("breathingArea",true);
    }

    if(result?.plan?.intent==="WELLBEING"||result?.understanding?.intent==="WELLBEING"){
      setTimeout(()=>openBreathing(false),500);
    }
  }catch(e){
    addMessage(e.message||"I couldn't complete that request right now.","mirror");
    toast(e.message||"Something went wrong.");
  }finally{
    setThinking(false);
    $("sendButton").disabled=false;
    $("voiceButton").disabled=false;
    input.focus();
  }
}

async function feedback(value){
  if(!currentMission?.id&&!currentResult?.mission?.id)return;
  const missionId=currentMission?.id||currentResult?.mission?.id;
  try{
    await api("/api/missions/feedback",{
      method:"POST",
      body:JSON.stringify({
        mission_id:missionId,
        feedback:value,
        memory:normalizeMemory(memory)
      })
    },10000);
    memory.learning.last_feedback=value;
    await saveMemory(memory);
    toast("MIRROR is learning your preferences.");
  }catch(e){
    toast(e.message);
  }
}

async function revise(note){
  const missionId=currentMission?.id||currentResult?.mission?.id;
  if(!missionId)return;
  try{
    const result=await api("/api/missions/revise",{
      method:"POST",
      body:JSON.stringify({
        mission_id:missionId,
        note:note||"",
        memory:normalizeMemory(memory)
      })
    },12000);
    if(result?.plan)renderPlan({...currentResult,...result});
  }catch(e){
    toast(e.message);
  }
}

async function sendConcierge(){
  const missionId=currentMission?.id||currentResult?.mission?.id;
  if(!missionId){
    toast("Tell MIRROR what you need first.");
    return;
  }

  const button=$("conciergeButton");
  button.disabled=true;

  try{
    const result=await api(`/api/missions/${encodeURIComponent(missionId)}/concierge`,{
      method:"POST",
      body:JSON.stringify({
        note:"",
        memory:normalizeMemory(memory)
      })
    },15000);

    const message=result?.message||"MIRROR has prepared the next step.";
    addMessage(message,"mirror");
    speak(message);
    memory.learning.last_concierge=new Date().toISOString();
    await saveMemory(memory);
  }catch(e){
    toast(e.message);
  }finally{
    button.disabled=false;
  }
}

function openMaps(){
  const u=currentResult?.understanding||currentResult?.analysis||{};
  const plan=currentResult?.plan||{};
  const destination=u.destination||plan.destination||"";

  if(!destination){
    toast("Tell MIRROR the place you have in mind first.");
    return;
  }

  const url="https://www.google.com/maps/search/?api=1&query="+encodeURIComponent(destination);
  window.open(url,"_blank","noopener,noreferrer");
}

function playMood(){
  const u=currentResult?.understanding||currentResult?.analysis||{};
  let query="relaxing elegant music";
  if(u.signals?.includes?.("NATURE"))query="peaceful nature music";
  if(u.signals?.includes?.("LUXURY"))query="luxury lounge music";
  if(u.signals?.includes?.("QUIET"))query="calm ambient music";
  if(u.intent==="MUSIC")query="beautiful music for this moment";

  const url="https://www.youtube.com/results?search_query="+encodeURIComponent(query);
  window.open(url,"_blank","noopener,noreferrer");
}

function speak(text){
  if(!text||!("speechSynthesis"in window)||speaking)return;
  const utter=new SpeechSynthesisUtterance(text);
  utter.lang=(currentResult?.understanding?.language||navigator.language?.slice(0,2)||"en")==="es"?"es-US":"en-US";
  utter.rate=.95;
  utter.pitch=1;
  utter.onstart=()=>speaking=true;
  utter.onend=()=>speaking=false;
  utter.onerror=()=>speaking=false;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utter);
}

function setupRecognition(){
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!SR)return null;

  const r=new SR();
  r.lang=navigator.language||"en-US";
  r.continuous=false;
  r.interimResults=true;
  r.maxAlternatives=1;

  r.onstart=()=>{
    listening=true;
    $("voiceButton").classList.add("listening");
    $("voiceStatus").textContent="Listening...";
    $("voiceStatus").classList.remove("hidden");
  };

  r.onresult=e=>{
    let finalText="";
    let interim="";
    for(let i=e.resultIndex;i<e.results.length;i++){
      const text=e.results[i][0].transcript;
      if(e.results[i].isFinal)finalText+=text;
      else interim+=text;
    }
    const input=$("messageInput");
    if(finalText){
      input.value=(input.value+" "+finalText).trim();
      input.style.height="auto";
      input.style.height=Math.min(input.scrollHeight,150)+"px";
    }else if(interim){
      $("voiceStatus").textContent=interim;
    }
  };

  r.onerror=e=>{
    listening=false;
    $("voiceButton").classList.remove("listening");
    $("voiceStatus").textContent="";
    $("voiceStatus").classList.add("hidden");
    if(e.error!=="aborted")toast("Voice input is unavailable right now.");
  };

  r.onend=()=>{
    listening=false;
    $("voiceButton").classList.remove("listening");
    $("voiceStatus").classList.add("hidden");
  };

  return r;
}

function toggleVoice(){
  if(!recognition){
    recognition=setupRecognition();
    if(!recognition){
      toast("Voice recognition is not supported by this browser.");
      return;
    }
  }

  if(listening){
    try{recognition.stop();}catch(_){}
  }else{
    try{
      recognition.lang=navigator.language||"en-US";
      recognition.start();
    }catch(e){
      try{recognition.stop();}catch(_){}
    }
  }
}

function formatTime(seconds){
  const m=Math.floor(seconds/60);
  const s=seconds%60;
  return `${String(m).padStart(2,"0")}:${String(s).padStart(2,"0")}`;
}

function breathingPhase(elapsed){
  const cycle=16;
  const position=elapsed%cycle;
  if(position<4)return{phase:"INHALE",instruction:"Breathe in slowly.",className:"inhale"};
  if(position<6)return{phase:"HOLD",instruction:"Hold gently.",className:"hold"};
  if(position<14)return{phase:"EXHALE",instruction:"Let the breath leave slowly.",className:"exhale"};
  return{phase:"REST",instruction:"Rest for a moment.",className:"rest"};
}

function updateBreathing(){
  if(!$("breathingTimer"))return;
  $("breathingTimer").textContent=formatTime(breathingSeconds);

  const elapsed=600-breathingSeconds;
  const phase=breathingPhase(elapsed);

  $("breathingPhase").textContent=phase.phase;
  $("breathingInstruction").textContent=phase.instruction;

  const orb=$("breathingOrb");
  orb.classList.remove("inhale","hold","exhale","rest");
  orb.classList.add(phase.className);
}

function startBreathing(){
  if(breathingRunning&&!breathingPaused)return;

  breathingRunning=true;
  breathingPaused=false;

  $("breathingStart").classList.add("hidden");
  $("breathingStop").classList.remove("hidden");
  $("breathingStart").textContent="Resume";

  clearInterval(breathingTimer);
  breathingTimer=setInterval(()=>{
    if(breathingPaused)return;

    breathingSeconds--;

    if(breathingSeconds<=0){
      breathingSeconds=0;
      updateBreathing();
      stopBreathing(true);
      const message="Beautiful. Take one more natural breath and return when you're ready.";
      addMessage(message,"mirror");
      speak(message);
      return;
    }

    updateBreathing();
  },1000);

  updateBreathing();
}

function pauseBreathing(){
  breathingPaused=true;
  $("breathingStop").textContent="Resume";
  $("breathingStop").onclick=()=>{
    breathingPaused=false;
    $("breathingStop").textContent="Pause";
  };
}

function stopBreathing(finished=false){
  clearInterval(breathingTimer);
  breathingTimer=null;
  breathingRunning=false;
  breathingPaused=false;

  $("breathingStart").classList.remove("hidden");
  $("breathingStop").classList.add("hidden");
  $("breathingStart").textContent=finished?"Begin Again":"Begin";
}

function resetBreathing(){
  stopBreathing();
  breathingSeconds=600;
  updateBreathing();
  $("breathingInstruction").textContent="When you're ready, begin.";
  $("breathingPhase").textContent="READY";
  $("breathingOrb").classList.remove("inhale","hold","exhale","rest");
}

function openBreathing(auto=false){
  setHidden("breathingArea",false);
  if(auto&&!breathingRunning)startBreathing();
}

function closeBreathing(){
  resetBreathing();
  setHidden("breathingArea",true);
}

function renderMemory(){
  const box=$("memorySummary");
  if(!box)return;
  box.replaceChildren();

  const values=[];

  if(memory.core.name)values.push(["Name",memory.core.name]);
  Object.entries(memory.preferences||{}).forEach(([key,value])=>{
    if(value)values.push([key.replace(/_/g," "),value]);
  });
  if(memory.moment.intent)values.push(["Current focus",memory.moment.intent.toLowerCase()]);
  if(memory.moment.signals?.length)values.push(["Atmosphere",memory.moment.signals.join(", ").toLowerCase()]);
  if(memory.dislikes.length)values.push(["Avoid",memory.dislikes.join(", ")]);

  if(!values.length){
    const empty=document.createElement("div");
    empty.className="memory-empty";
    empty.textContent="MIRROR is still getting to know your rhythm.";
    box.appendChild(empty);
    return;
  }

  values.slice(0,12).forEach(([key,value])=>{
    const item=document.createElement("div");
    item.className="memory-item";

    const label=document.createElement("span");
    label.className="memory-label";
    label.textContent=key;

    const val=document.createElement("strong");
    val.textContent=String(value);

    item.append(label,val);
    box.appendChild(item);
  });
}

function openMemory(){
  renderMemory();
  show("memoryScreen");
}

function closeMemory(){
  show("conversation");
}

function openRecovery(){
  $("recoveryName").value=memory.core.name||"";
  $("recoveryPriority").value=memory.preferences.priority||"";
  $("recoveryAtmosphere").value=memory.preferences.atmosphere||"";
  $("recoveryAvoid").value=memory.dislikes.join(", ")||"";
  $("recoveryStatus").textContent="";
  $("recoveryModal").classList.remove("hidden");
}

function closeRecovery(){
  $("recoveryModal").classList.add("hidden");
}

async function saveRecoveryForm(){
  const answers={
    name:escapeText($("recoveryName").value),
    priority:escapeText($("recoveryPriority").value),
    atmosphere:escapeText($("recoveryAtmosphere").value),
    avoid:escapeText($("recoveryAvoid").value)
  };

  const hasAnswer=Object.values(answers).some(Boolean);
  if(!hasAnswer){
    $("recoveryStatus").textContent="Choose at least one detail.";
    return;
  }

  const local=normalizeMemory(memory);

  if(answers.name)local.core.name=answers.name;
  if(answers.priority)local.preferences.priority=answers.priority;
  if(answers.atmosphere)local.preferences.atmosphere=answers.atmosphere;
  if(answers.avoid){
    local.dislikes=answers.avoid.split(",").map(x=>x.trim()).filter(Boolean);
  }

  $("recoveryStatus").textContent="Saving...";
  $("saveRecovery").disabled=true;

  try{
    const result=await api("/api/memory/recovery",{
      method:"POST",
      body:JSON.stringify({
        answers,
        memory:local
      })
    },10000);

    memory=normalizeMemory(result?.memory||local);
    await saveMemory(memory);
    renderMemory();
    $("recoveryStatus").textContent="Your context is restored.";
    setTimeout(closeRecovery,700);
  }catch(e){
    memory=local;
    await saveMemory(memory);
    $("recoveryStatus").textContent="Saved locally.";
    toast(e.message||"Saved locally.");
    setTimeout(closeRecovery,900);
  }finally{
    $("saveRecovery").disabled=false;
  }
}

function backupMemory(){
  try{
    const data=JSON.stringify(normalizeMemory(memory),null,2);
    const blob=new Blob([data],{type:"application/json"});
    const url=URL.createObjectURL(blob);
    const a=document.createElement("a");
    a.href=url;
    a.download="mirror-to-you-memory.json";
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(()=>URL.revokeObjectURL(url),1000);
  }catch(e){
    toast("Memory export failed.");
  }
}

function clearMemory(){
  $("confirmTitle").textContent="Clear local memory?";
  $("confirmText").textContent="This will remove the personal context stored on this device.";
  confirmAction=async()=>{
    memory={
      core:{},moment:{},preferences:{},dislikes:[],history:[],learning:{}
    };
    try{
      const db=await openDB();
      await new Promise((resolve,reject)=>{
        const tx=db.transaction(STORE,"readwrite");
        tx.objectStore(STORE).delete("profile");
        tx.oncomplete=resolve;
        tx.onerror=()=>reject(tx.error);
      });
      db.close();
    }catch(_){}
    localStorage.removeItem("mirror_memory");
    renderMemory();
    toast("Local memory cleared.");
  };
  $("confirmModal").classList.remove("hidden");
}

function closeConfirm(){
  $("confirmModal").classList.add("hidden");
  confirmAction=null;
}

async function loadMissions(){
  try{
    const result=await api("/api/missions",{},7000);
    if(!result)return;
  }catch(_){}
}

function autoResize(){
  const el=$("messageInput");
  if(!el)return;
  el.style.height="auto";
  el.style.height=Math.min(el.scrollHeight,150)+"px";
}

function bind(){
  $("startButton").onclick=()=>{
    show("conversation");
    $("messageInput").focus();
  };

  $("memoryButton").onclick=openMemory;
  $("closeMemory").onclick=closeMemory;

  $("sendButton").onclick=askMirror;
  $("voiceButton").onclick=toggleVoice;

  $("messageInput").addEventListener("input",autoResize);
  $("messageInput").addEventListener("keydown",e=>{
    if(e.key==="Enter"&&!e.shiftKey){
      e.preventDefault();
      askMirror();
    }
  });

  $("mapsButton").onclick=openMaps;
  $("musicButton").onclick=playMood;
  $("conciergeButton").onclick=sendConcierge;

  $("recoveryButton").onclick=openRecovery;
  $("closeRecovery").onclick=closeRecovery;
  $("saveRecovery").onclick=saveRecoveryForm;
  $("backupButton").onclick=backupMemory;
  $("clearMemoryButton").onclick=clearMemory;

  $("breathingStart").onclick=startBreathing;
  $("breathingStop").onclick=()=>{
    if(breathingPaused){
      breathingPaused=false;
      $("breathingStop").textContent="Pause";
    }else{
      pauseBreathing();
    }
  };
  $("closeBreathing").onclick=closeBreathing;

  $("closeConfirm").onclick=closeConfirm;
  $("confirmCancel").onclick=closeConfirm;
  $("confirmProceed").onclick=async()=>{
    const action=confirmAction;
    closeConfirm();
    if(action)await action();
  };

  $("recoveryModal").addEventListener("click",e=>{
    if(e.target===$("recoveryModal"))closeRecovery();
  });

  $("confirmModal").addEventListener("click",e=>{
    if(e.target===$("confirmModal"))closeConfirm();
  });
}

async function init(){
  bind();
  memory=normalizeMemory(await loadMemory());
  updateBreathing();
  deviceId();
  await loadMissions();

  if(!("speechSynthesis"in window)){
    $("voiceStatus").textContent="";
  }

  window.addEventListener("beforeunload",()=>{
    clearInterval(breathingTimer);
    try{window.speechSynthesis?.cancel();}catch(_){}
    try{recognition?.abort();}catch(_){}
  });
}

if(document.readyState==="loading"){
  document.addEventListener("DOMContentLoaded",init,{once:true});
}else{
  init();
}
