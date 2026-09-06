'use strict';
const $=id=>document.getElementById(id), command=()=>crypto.randomUUID();
const briefId=location.hash.slice(1), base='/api/briefs/'+encodeURIComponent(briefId);
let brief, config, current, highest=1, dirty=false, busy=false;
function status(message){$('status').textContent=message;}
function node(tag,copy){const e=document.createElement(tag);if(copy!==undefined)e.textContent=copy;return e;}
async function api(path,body){
 const response=await fetch(path,{method:body?'POST':'GET',headers:body?{'Content-Type':'application/json'}:{},body:body?JSON.stringify(body):undefined,cache:'no-store'});
 const data=await response.json();
 if(response.status===401){$('workspace').hidden=true;$('source').textContent='';$('fields').replaceChildren();$('tasks').replaceChildren();current=null;throw Error('Open your game idea and unlock the local workspace first.');}
 if(!response.ok)throw Error(typeof data.detail==='string'?data.detail:'Check the fields and try again.');
 return data;
}
function buttons(){if(!busy&&current){$('agree').disabled=dirty||current.stale||!current.scope_agreement_available||current.state==='scope_agreed';}}
async function run(action){if(busy)return;busy=true;document.querySelectorAll('button,input,textarea,select').forEach(e=>e.disabled=true);try{await action();}catch(error){status(error.message);}finally{busy=false;document.querySelectorAll('button,input,textarea,select').forEach(e=>e.disabled=false);buttons();}}
function changed(){dirty=true;$('unsaved').hidden=false;buttons();}
function confirm(title,copy,action){const dialog=$('confirm');if(dialog.open)return;$('confirm-title').textContent=title;$('confirm-copy').textContent=copy;dialog.returnValue='cancel';const closed=()=>{dialog.removeEventListener('close',closed);if(dialog.returnValue==='confirm')action();};dialog.addEventListener('close',closed);dialog.showModal();}
function leave(action){if(dirty)confirm('Leave your unsaved scope?','Your saved versions stay available. Save or copy your current edits before leaving.',action);else action();}
function show(plan){
 current=plan;highest=Math.max(highest,plan.revision);dirty=false;$('unsaved').hidden=true;$('plan').hidden=false;
 $('version').textContent='Plan version '+plan.revision;$('state').textContent=plan.stale?'Brief changed · start a new draft':plan.state==='scope_agreed'?'Scope agreed · development has not started':'Draft · review the assumptions';
 $('fields').replaceChildren();for(const [key,title]of Object.entries(config.labels)){const label=node('label',title),input=node('textarea');input.id='scope-'+key;input.rows=3;input.maxLength=1500;input.value=plan.scope[key];input.oninput=changed;label.htmlFor=input.id;label.append(input);$('fields').append(label);}
 $('engine').value=plan.scope.engine;$('target').value=plan.scope.target;$('allowance').value=plan.scope.token_allowance;
 const b=plan.budget;$('budget').textContent=`Estimated AI usage: ${b.estimated_tokens_min.toLocaleString()}–${b.estimated_tokens_max.toLocaleString()} tokens. Your planned allowance: ${b.token_allowance.toLocaleString()}. Estimated paid API fee on the local-model assumption: CHF ${b.estimated_paid_api_fee}.`;
 $('tasks').replaceChildren();for(const task of plan.leaf_tasks){const item=node('li');const detail=node('details');detail.append(node('summary',task.title));const list=node('ul');for(const check of task.acceptance)list.append(node('li',check));detail.append(list);item.append(detail);$('tasks').append(item);}
 $('limitations').replaceChildren();if(plan.limitations.length){$('limitations').append(node('h2','Before you agree'));for(const limitation of plan.limitations)$('limitations').append(node('p',limitation));}
 $('alternative').textContent=plan.scope.engine==='godot'?'Godot is a planning target. The actual engine and build worker still need qualification.':plan.alternative.description+' Choose Godot and save only if you want this alternative.';
 $('next-action').textContent=plan.execution_next_action;
 $('history').replaceChildren();for(let version=highest;version>=Math.max(1,highest-99);version--){const option=node('option','Version '+version);option.value=version;$('history').append(option);}$('history').value=plan.revision;buttons();
}
async function load(){brief=await api(base);config=await api(base+'/scope');$('source').textContent=brief.original_text;$('brief-version').textContent='Based on saved idea version '+brief.revision;$('workspace').hidden=false;for(const [id,values]of [['engine',config.engines],['target',config.targets]]){$(id).replaceChildren();for(const [key,label]of Object.entries(values)){const option=node('option',label);option.value=key;$(id).append(option);}}if(config.plan){highest=config.plan.revision;show(config.plan);}else{current=null;$('plan').hidden=true;}dirty=false;status('Your saved idea is unchanged.');}
$('back').onclick=()=>leave(()=>{location.href='/#'+encodeURIComponent(briefId);});
$('reload').onclick=()=>leave(()=>run(load));
$('create').onclick=()=>leave(()=>confirm('Create a new first-playable draft?','This creates a separate template proposal from the current saved idea. Existing plans and the original source stay available.',()=>run(async()=>{brief=await api(base);$('brief-version').textContent='Based on saved idea version '+brief.revision;show(await api(base+'/scope',{command_id:command(),expected_brief_revision:brief.revision}));status('Draft created. Review the suggested scope and future roadmap.');})));
for(const id of ['engine','target','allowance'])$(id).oninput=changed;
$('save').onclick=()=>run(async()=>{const scope=Object.fromEntries(Object.keys(config.labels).map(key=>[key,$('scope-'+key).value]));scope.engine=$('engine').value;scope.target=$('target').value;scope.token_allowance=Number($('allowance').value);show(await api(base+'/scope/'+current.id+'/edit',{command_id:command(),expected_brief_revision:current.brief_revision,expected_plan_revision:current.revision,scope}));status('Scope saved. Review the updated tasks and estimate before agreeing.');});
$('agree').onclick=()=>{if(dirty){status('Save your changes first.');return;}confirm('Agree to this saved scope?','Confirm the visible goal, assumptions, exclusions and local AI estimate. This records your scope choice only; no development or payment will start.',()=>run(async()=>{show(await api(base+'/scope/'+current.id+'/agree',{command_id:command(),expected_brief_revision:current.brief_revision,expected_plan_revision:current.revision,confirmed:true}));status('Scope agreement saved. Development still needs separate readiness checks and approval.');}));};
$('view').onclick=()=>leave(()=>run(async()=>{show(await api(base+'/scope/'+current.id+'?revision='+$('history').value));status('Earlier saved plan. Load the latest plan before editing.');}));
run(async()=>{if(!briefId)throw Error('Open a saved game idea first.');await load();});
