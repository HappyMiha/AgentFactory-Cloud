'use strict';
const $ = id => document.getElementById(id);
let config, current=null, dirty=false, busy=false, answers={}, highest=1;
const command=()=>crypto.randomUUID();
const status=message=>{$('status').textContent=message;};
function lock(){ $('workspace').hidden=true; $('login').hidden=false; $('logout').hidden=true;current=null;dirty=false;for(const id of ['source','fields','assumptions','questions','answers','ideas'])$(id).replaceChildren();$('original').value='';$('editor').hidden=true;$('intake').hidden=false; }
async function api(path,body){
 const response=await fetch(path,{method:body?'POST':'GET',headers:body?{'Content-Type':'application/json'}:{},body:body?JSON.stringify(body):undefined,cache:'no-store'});
 const data=await response.json();
 if(response.status===401){lock();throw new Error('Unlock the local workspace to continue.');}
 if(!response.ok)throw new Error(typeof data.detail==='string'?data.detail:'The request could not be saved. Check the input and try again.');
 return data;
}
async function run(action){
 if(busy)return;busy=true;document.querySelectorAll('button,input,textarea,select').forEach(b=>b.disabled=true);
 try{await action();}catch(error){status(error.message);}finally{busy=false;document.querySelectorAll('button,input,textarea,select').forEach(b=>b.disabled=false);if(config)$('suggest').disabled=!config.local_ai_enabled;}
}
function confirmChange(title,copy,action){
 const dialog=$('confirm');if(dialog.open)return;
 $('confirm-title').textContent=title;$('confirm-copy').textContent=copy;dialog.returnValue='cancel';
 const closed=()=>{dialog.removeEventListener('close',closed);if(dialog.returnValue==='confirm')action();};
 dialog.addEventListener('close',closed);dialog.showModal();
}
function leaving(action){if(dirty)confirmChange('Leave your unsaved changes?','Your saved versions stay available. Copy or save your current changes before leaving.',action);else action();}
function node(tag,value,className){const element=document.createElement(tag);if(value!==undefined)element.textContent=value;if(className)element.className=className;return element;}
async function list(){
 config=await api('/api/briefs');$('ideas').replaceChildren();
 for(const idea of config.items){const button=node('button',idea.preview);button.onclick=()=>leaving(()=>run(()=>load(idea.id)));$('ideas').append(button);}
 $('ai-route').textContent=config.local_ai_enabled?`Optional suggestion from ${config.model} on this computer. One bounded call, up to 90 seconds; no paid provider.`:'Local AI is off. You can fill in and save your plan yourself.';
 $('suggest').disabled=!config.local_ai_enabled;
 $('workspace').hidden=false;$('login').hidden=true;$('logout').hidden=!config.authentication_required;
}
function show(brief){
 current=brief;highest=Math.max(highest,brief.revision);answers={};dirty=false;
 $('intake').hidden=true;$('editor').hidden=false;$('source').textContent=brief.original_text;
 $('version').textContent=`Version ${brief.revision}`;
 $('kind').textContent=brief.analysis_kind==='ai_proposal'?'AI suggestion · copied from your idea. Check that each sentence is in the right field.':'Your editable plan · saving does not approve development or spending.';
 $('fields').replaceChildren();
 for(const [key,title]of Object.entries(config.fields)){const label=node('label',title),input=node('textarea');input.id='field-'+key;input.maxLength=1500;input.rows=3;input.value=brief.fields[key];input.oninput=()=>{dirty=true;if(key in answers)answers[key]=input.value;};label.htmlFor=input.id;label.append(input);$('fields').append(label);}
 $('questions').replaceChildren();
 for(const question of brief.questions){const section=node('div',undefined,'question'),options=node('div',undefined,'options');section.append(node('h3',question.question));
  for(const option of question.options){const button=node('button',option);button.onclick=()=>{$('field-'+question.field).value=option;answers[question.field]=option;dirty=true;status('Answer added to your plan. Save your changes when ready.');};options.append(button);}
  section.append(options,node('p','Choose an answer or write your own in the matching plan field.'));
  $('field-'+question.field).addEventListener('input',event=>{answers[question.field]=event.target.value;});$('questions').append(section);
 }
 $('assumptions').replaceChildren();if(brief.assumptions.length){$('assumptions').append(node('h3','AI assumptions to check'));const ul=node('ul');for(const assumption of brief.assumptions)ul.append(node('li',assumption));$('assumptions').append(ul);}
 $('answers').replaceChildren();for(const item of brief.clarification_history)$('answers').append(node('li',`Version ${item.answered_at_revision}: ${item.question} — ${item.answer}`));
 $('history').replaceChildren();for(let version=highest;version>=Math.max(1,highest-99);version--){const option=node('option',`Version ${version}`);option.value=version;$('history').append(option);}$('history').value=brief.revision;
 location.hash=brief.id;
}
async function load(id){const brief=await api('/api/briefs/'+encodeURIComponent(id));highest=brief.revision;show(brief);status('Saved idea loaded.');}
$('create').onclick=()=>run(async()=>{const brief=await api('/api/briefs',{original_text:$('original').value,command_id:command()});highest=1;show(brief);await list();status('Your original idea is saved unchanged.');});
$('original').oninput=()=>{dirty=true;};
$('new').onclick=()=>leaving(()=>{current=null;highest=1;dirty=false;location.hash='';$('original').value='';$('editor').hidden=true;$('intake').hidden=false;$('original').focus();status('');});
$('reload').onclick=()=>leaving(()=>run(()=>load(current.id)));
$('save').onclick=()=>run(async()=>{const fields=Object.fromEntries(Object.keys(config.fields).map(key=>[key,$('field-'+key).value]));const brief=await api('/api/briefs/'+current.id+'/edit',{expected_revision:current.revision,command_id:command(),fields,answers});show(brief);await list();status('Your changes are saved as a new version.');});
$('suggest').onclick=()=>{
 if(dirty){status('Save your changes before asking AI to organize this idea.');return;}
 confirmChange('Ask local AI to organize your idea?','This sends your saved idea to the installed local model. It suggests where your original sentences belong. Review every field before using the brief.',()=>run(async()=>{status('Local AI is sorting your original sentences. Your saved version stays available.');const brief=await api('/api/briefs/'+current.id+'/suggest',{expected_revision:current.revision,command_id:command()});show(brief);await list();status('AI suggestion saved. Check the fields against your original idea.');}));
};
$('view-version').onclick=()=>leaving(()=>run(async()=>{show(await api('/api/briefs/'+current.id+'?revision='+$('history').value));status('Earlier saved version. Load the latest version before saving new edits.');}));
$('sign-in').onclick=()=>run(async()=>{await api('/auth/login',{token:$('token').value});$('token').value='';await list();if(location.hash)await load(location.hash.slice(1));status('Workspace unlocked.');});
$('logout').onclick=()=>leaving(()=>run(async()=>{await api('/auth/logout',{});current=null;dirty=false;$('fields').replaceChildren();$('source').textContent='';$('ideas').replaceChildren();$('original').value='';lock();status('Workspace locked.');}));
run(async()=>{await list();if(location.hash)await load(location.hash.slice(1));});

$('plan-first').onclick=()=>leaving(()=>{location.href='/first-playable#'+encodeURIComponent(current.id);});
