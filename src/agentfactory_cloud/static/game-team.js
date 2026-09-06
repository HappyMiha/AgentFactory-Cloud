"use strict";
(()=>{
 const byId=id=>document.getElementById(id);
 const ident=location.hash.slice(1),url='/api/briefs/'+encodeURIComponent(ident)+'/team';
 byId('scope-link').href='/first-playable'+location.hash;
 let current=null,generation=0,busy=false;
 const make=(tag,text)=>{const n=document.createElement(tag);n.textContent=text;return n;};
 async function call(body){const r=await fetch(url+(body?'/assess':''),{method:body?'POST':'GET',headers:body?{'Content-Type':'application/json'}:{},body:body?JSON.stringify(body):undefined,cache:'no-store'});if(!r.ok)throw Error(r.status===409?'The saved scope changed. Reload and review it before preparing the team.':'The team view is unavailable. Check your access and reload.');return r.json();}
 function render(data){current=data;byId('status').textContent=data.notice;byId('binding').textContent=`Saved idea ${data.brief_revision}; scope ${data.plan_revision||'not yet saved'}; role pack ${data.pack_version}.`;byId('budget').textContent=`Planned tokens: ${data.planned_tokens}. Approved spending: 0. ${data.budget_note}`;byId('roles').replaceChildren();for(const role of data.roles){const card=make('article','');card.append(make('h2',role.title),make('p',role.responsibility),make('p',`Planned tokens: ${role.planned_tokens}. No model assigned; no work running.`));byId('roles').append(card);}byId('confirmed').checked=false;byId('assess').disabled=!data.can_assess;byId('assessment').textContent=data.core_assessment?'Core recorded the missing-capability assessment. No worker was selected and nothing started.':data.can_assess?'Your saved scope is agreed. You can now prepare an assessment.':'Agree to the saved scope before preparing an assessment.';}
 async function load(){if(busy)return;const version=++generation;byId('assess').disabled=true;try{const data=await call();if(version===generation)render(data);}catch(e){if(version===generation){current=null;byId('roles').replaceChildren();for(const id of ['binding','budget','assessment'])byId(id).textContent='';byId('status').textContent=e.message;}}}
 byId('reload').onclick=load;
 byId('assess').onclick=async()=>{if(busy||!current?.can_assess)return;if(!byId('confirmed').checked){byId('status').textContent='Confirm preparation first. No AI will start.';return;}busy=true;++generation;byId('assess').disabled=true;try{render(await call({expected_digest:current.snapshot_digest,confirmed:true}));}catch(e){byId('status').textContent=e.message;}finally{busy=false;}};
 load();
})();
