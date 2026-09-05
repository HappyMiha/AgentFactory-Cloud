'use strict';
const $ = id => document.getElementById(id);
const STORAGE = 'agentfactory-creator-design-v1';
const escape = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const state = {role:'creator',age:'adult',scenario:'first-use',route:'my-games',plan:false,storageAvailable:true,draft:{title:'Moon garden',idea:''}};
let fixtures;
function announce(message) { $('announcement').textContent=message; }
function restore() {
 try {
  const raw=localStorage.getItem(STORAGE);
  if (!raw) return;
  const value=JSON.parse(raw);
  if (value.version!==1 || typeof value.title!=='string' || typeof value.idea!=='string' || value.title.length>80 || value.idea.length>2000) throw new Error();
  state.draft={title:value.title,idea:value.idea};
  state.scenario='resume';
 } catch (_) { announce('The saved draft could not be read. Start a new draft or delete the local copy.'); }
}
function saveDraft() {
 try {
  localStorage.setItem(STORAGE,JSON.stringify({version:1,...state.draft}));
  state.storageAvailable=true;
  $('saved').textContent='Draft saved on this device. Private, with no upload.';
 } catch (_) {
  state.storageAvailable=false;
  $('saved').textContent='This browser could not save. Keep this page open and copy your idea before leaving.';
 }
}
const art = '<div class="landscape" aria-label="Illustrated sample game landscape"><div class="moon"></div><div class="hill back"></div><div class="hill"></div><div class="tree"></div><div class="tree small"></div><span class="art-caption">Concept illustration · not a playable build</span></div>';
function gate() {
 if (state.age==='adult') return '';
 return `<div class="gate" role="status"><strong>${state.age==='teen'?'A supervised pilot needs approval first':'This path is not available for under 12s'}</strong><p>${state.age==='teen'?'Provider account rules, privacy review and a verified guardian process must be approved before a 12–17 pilot. An authorized adult controls spending. No child information is collected here.':'Do not enter a name, contact details or game idea. Ask an adult about age-appropriate options.'}</p></div>`;
}
function technical() { return '<details class="technical"><summary>Optional details</summary><p>This preview has no accepted engine build or playtest. Nothing is sent to a provider. Published content and spending require separate verified decisions.</p></details>'; }
function home() {
 const example=fixtures.scenarios[state.scenario];
 return `<div class="hero"><div class="hero-copy"><span class="pill">${state.scenario==='first-use'?'Make something small':'Your saved space'}</span><h2 style="margin-top:20px">${escape(example.status)}</h2><p>${escape(example.detail)}</p><button data-go="${example.destination}">${escape(example.action)}</button></div>${art}</div><div class="below"><article class="note"><span class="number">1</span><h3>Start with an idea</h3><p>A small first version leaves room to learn and grow.</p></article><article class="note"><span class="number">2</span><h3>Make it yours</h3><p>Review the plan, try a version, then choose what to change.</p></article><article class="note"><span class="number">3</span><h3>Share when ready</h3><p>Keep it private until the checks and your approval are complete.</p></article></div>`;
}
function create() {
 const disabled=state.age!=='adult'?'disabled':'';
 if (state.plan) return `<div class="panel"><p class="eyebrow">Review before starting</p><h2>${escape(state.draft.title || 'Your game')}</h2><p>${escape(state.draft.idea || 'Collect three glowing seeds in a small moonlit garden.')}</p><ul class="checks"><li>First version: one small scene, one goal and simple controls</li><li>Later: extra levels, multiplayer and custom assets</li><li>Cost: no provider connected; starting a real build is unavailable</li><li>Visibility: private until you separately approve sharing</li></ul><p class="hint">This is a fixed sample plan for a design review. It is not an AI analysis of your idea.</p><button data-action="edit">Edit your idea</button>${technical()}</div>`;
 return `${gate()}<div class="form-layout"><section class="panel"><h2>What would you like to make?</h2><p class="hint">Use a made-up idea for this design preview. No names, contact details or private information.</p><label for="game-title">Game name<input id="game-title" maxlength="80" value="${escape(state.draft.title)}" ${disabled}></label><label for="game-idea">Your first small game<textarea id="game-idea" maxlength="2000" ${disabled} placeholder="I want to collect glowing seeds in a moonlit garden…">${escape(state.draft.idea)}</textarea></label><button data-action="review" ${disabled}>Review the sample plan</button></section><aside class="panel"><p class="eyebrow">A little direction</p><h3>One scene is enough</h3><p class="hint">Think about what the player does, what they are trying to achieve and how they know they've won.</p><ul class="checks"><li>Simple controls</li><li>One clear goal</li><li>A small first version</li></ul></aside></div>`;
}
function play() {
 return `<div class="hero">${art}<div class="hero-copy"><span class="pill">Not yet playable</span><h2 style="margin-top:20px">A picture isn't a playtest</h2><p>This sample has no verified playable version. Keep your saved idea and review the next small step.</p><button data-go="change">Review next step</button></div></div>${technical()}`;
}
function change() {
 const cancelled=state.scenario==='cancellation';
 return `<section class="panel status-card"><p class="eyebrow">${cancelled?'Cancelled':'Recovery & changes'}</p><h2>${cancelled?'Your work has stopped':'Keep the good parts. Change the next step.'}</h2><p>${state.scenario==='failure'?'The sample build was interrupted. Your saved idea is safe; no retry happens automatically.':'Your saved draft stays private. Review a new plan before starting another attempt.'}</p><button data-go="create">${cancelled?'Revisit your saved idea':'Edit the next version'}</button><p><button class="text-button" data-action="cancel">Cancel this sample attempt</button></p>${technical()}</section>`;
}
function publish() {
 return `${gate()}<section class="panel"><p class="eyebrow">Private until you decide</p><h2>Sharing starts with a checked version</h2><p>Your game stays private. This design preview cannot publish, list or sell anything.</p><ul class="checks"><li>Playable proof for the exact version — missing</li><li>Asset rights and attribution — not reviewed</li><li>Safety and moderation — not reviewed</li><li>Owner's explicit sharing approval — not recorded</li><li>Spending authority — no payment method connected</li></ul><button data-go="change">Review what is missing</button>${technical()}</section>`;
}
function operator() {
 if (state.role!=='operator') return '<section class="panel"><h2>Operator access required</h2><p>Approvals, worker information and diagnostics belong to an authorized operator.</p><button data-go="my-games">Back to My Games</button></section>';
 return '<div class="gate">Operator view example only. The preview role switch grants no real authority; production access must be verified by the service.</div><div class="operator-grid">'+Object.entries(fixtures.operator_example).map(([name,value])=>`<section class="panel"><p class="eyebrow">${escape(name)}</p><h3>${escape(value)}</h3><p>Sample data · no privileged action is available.</p></section>`).join('')+'</div>';
}
function render() {
 if (!fixtures) return;
 state.route=location.hash.slice(1)||'my-games';
 const screens={'my-games':home,create,play,change,publish,operator};
 const titles={'my-games':'My Games',create:'Create',play:'Play',change:'Change',publish:'Publish',operator:'Operator'};
 if (!screens[state.route]) state.route='my-games';
 if (state.route==='operator' && state.role!=='operator') $('title').textContent='Access';
 else $('title').textContent=titles[state.route];
 $('operator-link').hidden=state.role!=='operator';
 document.querySelectorAll('#navigation a').forEach(a=>a.setAttribute('aria-current',a.hash==='#'+state.route?'page':'false'));
 $('screen').innerHTML=screens[state.route]();
 $('privacy').textContent='Private draft';
}
function navigate(route) { state.plan=false; if(location.hash==='#'+route)render();else location.hash=route; }
function confirmChoice(title,copy,action) {
 const dialog=$('confirm');
 if (dialog.open) return;
 $('confirm-title').textContent=title;$('confirm-copy').textContent=copy;
 dialog.returnValue='cancel';
 const closed=()=>{dialog.removeEventListener('close',closed);if(dialog.returnValue==='confirm')action();};
 dialog.addEventListener('close',closed);dialog.showModal();
}
$('screen').addEventListener('input',event=>{
 if (!['game-title','game-idea'].includes(event.target.id)||state.age!=='adult')return;
 state.draft[event.target.id==='game-title'?'title':'idea']=event.target.value;saveDraft();
});
$('screen').addEventListener('click',event=>{
 const button=event.target.closest('button');if(!button)return;
 if(button.dataset.go)navigate(button.dataset.go);
 if(button.dataset.action==='review' && state.age==='adult'){state.plan=true;render();}
 if(button.dataset.action==='edit'){state.plan=false;render();}
 if(button.dataset.action==='cancel')confirmChoice('Cancel this sample attempt?','The preview will show stopped work. Your saved game idea will be kept.',()=>{state.scenario='cancellation';$('scenario').value=state.scenario;render();announce('Sample attempt cancelled. Your saved draft is kept.');});
});
$('delete').addEventListener('click',()=>confirmChoice('Delete the local draft?','This removes only this preview’s saved draft from this browser. It does not erase a real account or a published game.',()=>{
 try{localStorage.removeItem(STORAGE);}catch(_){announce('This browser could not delete the stored draft. Use browser site settings to clear it.');return;}
 state.draft={title:'',idea:''};state.plan=false;state.scenario='first-use';$('scenario').value=state.scenario;
 $('saved').textContent='Local draft deleted.';render();announce('The local draft was deleted.');
}));
$('role').addEventListener('change',event=>{state.role=event.target.value;render();});
$('age').addEventListener('change',event=>{state.age=event.target.value;state.plan=false;navigate('create');});
$('scenario').addEventListener('change',event=>{state.scenario=event.target.value;navigate('my-games');});
function refreshSample(){if(fixtures)$('privacy').textContent='Private draft · sample status refreshed';}
$('background').addEventListener('click',refreshSample);
window.addEventListener('hashchange',render);
fetch('scenarios.json',{cache:'no-store'}).then(response=>{if(!response.ok)throw new Error();return response.json();}).then(data=>{
 if(data.mode!=='synthetic-design-preview'||data.product_acceptance!=='not-accepted')throw new Error();
 fixtures=data;restore();
 $('scenario').innerHTML=Object.entries(fixtures.scenarios).map(([id,value])=>`<option value="${escape(id)}">${escape(value.label)}</option>`).join('');
 $('scenario').value=state.scenario;render();setInterval(refreshSample,5000);
}).catch(()=>{announce('The design examples could not load. Refresh this page to try again.');$('screen').textContent='No build, payment or account action is available.';});
