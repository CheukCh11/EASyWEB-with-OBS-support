#!/usr/bin/env python3
"""
Adds OBS support to EASyWEB.

  python patch_obs.py easyweb.html            -> writes easyweb-obs.html
  python patch_obs.py easyweb.html out.html   -> writes out.html

New URL modes of the patched file:
  easyweb-obs.html?obs      clean display (canvas only, no sidebar/menu) for an OBS Browser Source
  easyweb-obs.html?remote   control panel that drives the ?obs page (use as an OBS Custom Browser Dock)
  easyweb-obs.html          unchanged normal app
Add &ch=name to both URLs if you ever need two separate display/panel pairs.
"""
import sys, pathlib

src = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "easyweb.html")
out = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_name(src.stem + "-obs.html")
h = src.read_text(encoding="utf-8")

if "easyweb-link-" in h:
    sys.exit("This file already has the OBS patch.")

def rep(old, new):
    global h
    n = h.count(old)
    if n != 1:
        sys.exit(f"Could not patch: anchor found {n} times (expected 1):\n  {old[:90]!r}\n"
                 "Is this the same EASyWEB version the patch was written for?")
    h = h.replace(old, new)

# ---------- CSS ----------
CSS = r"""
/* ---- OBS display (?obs) and remote panel (?remote) ---- */
body.obs #menu,body.obs #about,body.rmt #menu,body.rmt #about{display:none!important}
body.obs{overflow:hidden;cursor:none;background:#000}
body.obs .app,body.obs .app[hidden]{display:block!important;min-height:0}
body.obs .side,body.obs #dupq{display:none!important}
body.obs .stage{position:fixed!important;inset:0;height:auto!important;padding:0!important;background:#000}
body.obs #cv{width:100%!important;height:100%!important;max-width:none!important;max-height:none!important;aspect-ratio:auto!important;object-fit:contain}
body.rmt .app,body.rmt .app[hidden]{display:block!important;min-height:0}
body.rmt .stage{display:none!important}
body.rmt .side{max-width:640px;margin:0 auto;border-left:0;box-shadow:none;min-height:0}
body.rmt #fsb,body.rmt #rec,body.rmt #arb{display:none}
body.rmt #log audio,body.rmt #log a{display:none}
#rmbar{display:none}
body.rmt #rmbar{display:grid;gap:10px;max-width:640px;margin:0 auto;padding:14px 20px 0;background:var(--side)}
#rmbar .row{flex-wrap:wrap}
#rmst{font-size:14px;color:#f88}#rmbar.ok #rmst{color:#6f6}
#rmurl{font-size:12px;color:#aaa;overflow-wrap:anywhere;user-select:all}
#rprev{display:none;width:100%;max-width:360px;border:2px solid var(--red);background:#000}
#rmbar.pv #rprev{display:block}
"""
rep("</style></head><body>", CSS + "</style></head><body>")

# ---------- flags, defined at the very top of the script ----------
EARLY = ('\nconst QS=new URLSearchParams(location.search),RMT=QS.has("remote")||QS.has("panel"),OBS=!RMT&&QS.has("obs"),'
         'CHN="easyweb-link-"+(QS.get("ch")||"main");'
         'document.body.classList.toggle("rmt",RMT);document.body.classList.toggle("obs",OBS);')
i = h.find("const $=s=>document.querySelector(s)")
if i < 0:
    sys.exit("Could not find the start of the script.")
j = h.index("\n", i)
h = h[:j] + EARLY + h[j:]

# ---------- small patches to existing functions ----------
rep("function ensure(){if(ctx){ctx.resume();return}", "function ensure(){if(RMT)return;if(ctx){ctx.resume();return}")
rep("function lcd(){const d=new Date,", "function lcd(){if(RMT)return;const d=new Date,")
rep("function frame(now){g.setTransform(1,0,0,1,0,0);", "function frame(now){if(RMT)return;g.setTransform(1,0,0,1,0,0);")
rep("if(!rec&&!recHide&&!(document.fullscreenElement||document.webkitFullscreenElement)){g.save();",
    "if(!OBS&&!rec&&!recHide&&!(document.fullscreenElement||document.webkitFullscreenElement)){g.save();")
rep('function arTick(){if(!arOn||SCR==="menu")return;', 'function arTick(){if(RMT||!arOn||SCR==="menu")return;')
rep("restoreSet();dscRestore();", "if(!RMT){restoreSet();dscRestore()}else dscUi();")
rep("lcd();rafP=true;requestAnimationFrame(raf);", "lcd();rafP=true;if(!RMT)requestAnimationFrame(raf);")

# ---------- the bridge ----------
BRIDGE = r"""
/* ===== OBS display / remote panel bridge (BroadcastChannel) ===== */
(()=>{
if(!RMT&&!OBS)return;
const bc=new BroadcastChannel(CHN),post=m=>{try{bc.postMessage(m)}catch(e){}};
const side=document.querySelector(".side"),app=document.querySelector(".app");
const pathOf=(el,root)=>{const p=[];for(;el&&el!==root;el=el.parentNode)p.unshift([...el.parentNode.children].indexOf(el));return p};
const at=(root,p)=>(p||[]).reduce((n,i)=>n&&n.children[i],root);
const TXT=/^(text|password|number|time)$/;

if(OBS){
 /* ---------- display side: runs the real app, answers the panel ---------- */
 document.title="EASyWEB display";
 let ping=0,okFlag=false,prevOn=false;const ST={h:"",dq:"",sc:"",lc:""};
 window.confirm=()=>okFlag; // a hidden page cannot ask; the panel asks and sends ok:true
 const rootOf=k=>k==="d"?document.getElementById("dupq"):side;
 function snap(){
  const c=side.cloneNode(true),a=side.querySelectorAll("input,select,textarea"),b=c.querySelectorAll("input,select,textarea");
  a.forEach((e,i)=>{const d=b[i];if(!d)return;
   if(e.tagName==="SELECT")[...d.options].forEach((o,k)=>{e.options[k]&&e.options[k].selected?o.setAttribute("selected",""):o.removeAttribute("selected")});
   else if(e.type==="checkbox"||e.type==="radio")e.checked?d.setAttribute("checked",""):d.removeAttribute("checked");
   else if(e.type!=="file")d.setAttribute("value",e.value)});
  c.querySelectorAll("img").forEach(i=>i.removeAttribute("src"));
  const l=c.querySelector("#lcd");if(l)l.innerHTML="";
  return c.innerHTML}
 function push(force){
  const h=snap(),q=document.getElementById("dupq"),dq=q?q.innerHTML:"",sc=app.dataset.scr||"menu";
  if(force||h!==ST.h||dq!==ST.dq||sc!==ST.sc){ST.h=h;ST.dq=dq;ST.sc=sc;post({t:"state",side:h,dup:dq,scr:sc})}
  const l=document.getElementById("lcd"),lc=(l&&l._h)||"";
  if(force||lc!==ST.lc){ST.lc=lc;post({t:"lcd",h:lc})}}
 setInterval(()=>{if(Date.now()-ping<6000)push(false)},250);
 const pc=document.createElement("canvas"),px=pc.getContext("2d");
 setInterval(()=>{if(!prevOn||Date.now()-ping>6000)return;
  try{pc.width=360;pc.height=Math.max(1,Math.round(360*cv.height/cv.width));px.drawImage(cv,0,0,pc.width,pc.height);pc.toBlob(b=>{if(b)post({t:"pv",b})},"image/jpeg",.6)}catch(e){}},500);
 bc.onmessage=e=>{const m=e.data||{};if(!m.t)return;
  if(m.t==="hello"){ping=Date.now();push(true);post({t:"pong"});return}
  if(m.t==="ping"){ping=Date.now();post({t:"pong"});return}
  ping=Date.now();
  try{
   if(m.t==="prev")prevOn=!!m.on;
   else if(m.t==="go"){if(["menu","imp","str","url"].includes(m.s))go(m.s)}
   else if(m.t==="click"){const el=at(rootOf(m.k),m.p);if(el){okFlag=!!m.ok;try{el.click()}finally{okFlag=false}}}
   else if(m.t==="val"){const el=at(rootOf(m.k),m.p);if(el){el.value=m.v;el.dispatchEvent(new Event(m.ev,{bubbles:true}))}}
   else if(m.t==="key"){const el=(m.p&&at(rootOf(m.k),m.p))||document.body;el.dispatchEvent(new KeyboardEvent("keydown",{key:m.key,bubbles:true,cancelable:true}))}
   else if(m.t==="files"){const inp=document.getElementById(m.id);
    if(inp&&inp.type==="file"&&m.files&&m.files.length){const dt=new DataTransfer();m.files.forEach(f=>dt.items.add(f));inp.files=dt.files;inp.dispatchEvent(new Event("change",{bubbles:true}))}}
  }catch(err){console.warn("EASyWEB link:",err)}
  setTimeout(()=>push(false),60)};
}else{
 /* ---------- panel side: a mirror of the display's sidebar; every action is sent over ---------- */
 document.title="EASyWEB remote";
 const LOGO=(side.querySelector("img")||{}).src||"";
 const bar=document.createElement("div");bar.id="rmbar";
 bar.innerHTML='<div><b>EASyWEB remote</b> &nbsp;<span id="rmst">Waiting for the display...</span></div>'
  +'<div class="row"><button class="bv" data-rgo="imp">Import</button><button class="bv" data-rgo="str">Stream</button><button class="bv" data-rgo="url">URL</button><button class="bv" data-rgo="menu">Menu</button></div>'
  +'<div class="row"><label style="display:flex;align-items:center;gap:8px;cursor:pointer"><input type="checkbox" id="rpv"> Preview of the display</label></div>'
  +'<img id="rprev" alt="Display preview"><div id="rmurl"></div>';
 document.body.insertBefore(bar,app);
 bar.querySelector("#rmurl").textContent="Display URL for OBS: "+location.href.split(/[?#]/)[0]+"?obs"+(QS.get("ch")?"&ch="+encodeURIComponent(QS.get("ch")):"");
 const dq=document.createElement("div");dq.id="dupq";document.body.appendChild(dq);
 let pend=null,down=false,curSide=null,curDup="",lcdH="",pong=0,force=0;
 const FILES={ba:"fia",bm:"fim",bi:"fimg",bvd:"fvid",tub:"ftu",ami:"amfile"};
 const rootInfo=el=>{if(!el||!el.closest)return null;if(el.closest(".side"))return["s",side];const d=el.closest("#dupq");return d?["d",d]:null};
 function apply(){
  if(!pend||down)return;
  const a=document.activeElement;if(a&&a.tagName==="SELECT"&&side.contains(a))return; // do not close an open dropdown
  const m=pend;pend=null;
  if(m.dup!==curDup){curDup=m.dup;dq.innerHTML=m.dup}
  app.dataset.scr=m.scr;
  if(m.side===curSide)return;
  curSide=m.side;
  const fo=a&&a!==side&&side.contains(a)?{p:pathOf(a,side),tag:a.tagName,v:a.value,s:a.selectionStart,e:a.selectionEnd}:null;
  side.innerHTML=m.side;
  if(LOGO)side.querySelectorAll("img").forEach(i=>{i.src=LOGO});
  const l=side.querySelector("#lcd");if(l)l.innerHTML=lcdH;
  if(fo){const n=at(side,fo.p);
   if(n&&n.tagName===fo.tag)try{n.focus({preventScroll:true});if(TXT.test(n.type||"")&&Date.now()>force){n.value=fo.v;n.setSelectionRange(fo.s,fo.e)}}catch(e){}}}
 function pickFile(id){const o=document.getElementById(id),i=document.createElement("input");i.type="file";
  const ac=o&&o.getAttribute("accept");if(ac)i.accept=ac;if(o&&o.multiple)i.multiple=true;
  i.onchange=()=>{const f=[...i.files];if(f.length)post({t:"files",id,files:f})};i.click()}
 addEventListener("click",e=>{
  const r=rootInfo(e.target);if(!r)return;
  e.stopImmediatePropagation();
  let el=e.target.closest("button,summary,input,select,a");
  if(!el){const lb=e.target.closest("label");if(lb)el=lb.querySelector("input,select")}
  if(!el||el.tagName==="A")return;
  if(el.tagName==="SELECT"||TXT.test(el.type||"")||el.type==="range"||el.type==="file")return;
  e.preventDefault();if(el.disabled)return;
  if(el.id&&FILES[el.id]){pickFile(FILES[el.id]);return}
  if(el.id==="abt"&&!confirm("Abort the current message and jump to the EOM?\n\nIf it is an EAN, only do this if it did not end correctly or was sent by mistake."))return;
  post({t:"click",k:r[0],p:pathOf(el,r[1]),ok:el.id==="abt"});post({t:"snap"})},true);
 ["input","change"].forEach(ty=>addEventListener(ty,e=>{
  const el=e.target,r=rootInfo(el);if(!r||!/^(INPUT|SELECT|TEXTAREA)$/.test(el.tagName))return;
  e.stopImmediatePropagation();
  if(el.type==="checkbox"||el.type==="radio"||el.type==="file")return;
  post({t:"val",ev:ty,k:r[0],p:pathOf(el,r[1]),v:el.value});
  if(ty==="change"&&el.tagName==="SELECT"){post({t:"snap"});try{el.blur()}catch(x){}}},true));
 addEventListener("keydown",e=>{
  const el=e.target,r=rootInfo(el);
  if(r&&e.key==="Enter"&&el.tagName==="INPUT"&&TXT.test(el.type)){e.stopImmediatePropagation();force=Date.now()+1500;post({t:"key",k:r[0],p:pathOf(el,r[1]),key:"Enter"});post({t:"snap"});return}
  if((e.key==="ArrowLeft"||e.key==="ArrowRight")&&!e.ctrlKey&&!e.metaKey&&!e.altKey&&!e.shiftKey&&!/^(INPUT|SELECT|TEXTAREA)$/.test(el.tagName)){e.stopImmediatePropagation();post({t:"key",p:null,key:e.key})}},true);
 addEventListener("pointerdown",e=>{if(rootInfo(e.target))down=true},true);
 const up=()=>{down=false;setTimeout(apply,30)};
 addEventListener("pointerup",up,true);addEventListener("pointercancel",up,true);addEventListener("blur",up);
 bar.addEventListener("click",e=>{const b=e.target.closest("[data-rgo]");if(b)post({t:"go",s:b.dataset.rgo})});
 bar.querySelector("#rpv").onchange=e=>{bar.classList.toggle("pv",e.target.checked);post({t:"prev",on:e.target.checked})};
 let pvUrl="";
 bc.onmessage=e=>{const m=e.data||{};
  if(m.t==="state"){pong=Date.now();pend=m;apply()}
  else if(m.t==="lcd"){lcdH=m.h;const l=side.querySelector("#lcd");if(l)l.innerHTML=m.h}
  else if(m.t==="pv"&&m.b){const u=URL.createObjectURL(m.b);bar.querySelector("#rprev").src=u;if(pvUrl)URL.revokeObjectURL(pvUrl);pvUrl=u}
  else if(m.t==="pong")pong=Date.now()};
 post({t:"hello"});
 setInterval(()=>{post(Date.now()-pong>5000?{t:"hello"}:{t:"ping"});apply()},2000);
 setInterval(()=>{const ok=Date.now()-pong<5000,s=bar.querySelector("#rmst");bar.classList.toggle("ok",ok);
  s.textContent=ok?"Connected to the display":"Waiting for the display... open the ?obs page in the same browser (OBS Browser Source or a normal window)"},500);
}
})();
"""
k = h.rindex("</script>")
h = h[:k] + BRIDGE + h[k:]

out.write_text(h, encoding="utf-8")
print("Wrote", out)
