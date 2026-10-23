'use strict';
const $=s=>document.querySelector(s);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=n=>n.toLocaleString();
let data,players=new Map(),selected,filter='all',page=0,recentIds=[],longestLimit=10,searchMatches=[];
const pageSize=8;
function load(dataset){
  data=dataset; players=new Map();
  for(const e of data.events){
    for(const role of ['killer','victim']){
      const ref=e[role];
      if(!players.has(ref.id)) players.set(ref.id,{id:ref.id,name:ref.name,names:new Set(),kills:0,deaths:0,weapons:new Map(),events:[]});
      const p=players.get(ref.id);p.names.add(ref.name);
      if(role==='killer'){p.kills++;p.weapons.set(e.weapon,(p.weapons.get(e.weapon)||0)+1)}else p.deaths++;
    }
    players.get(e.killer.id).events.push(e);
    if(e.victim.id!==e.killer.id) players.get(e.victim.id).events.push(e);
  }
  let savedPlayer;try{savedPlayer=localStorage.getItem('dayz-dossier-player')}catch{}
  selected=players.has(savedPlayer)?savedPlayer:[...players.values()].sort((a,b)=>b.kills-a.kills)[0]?.id; filter='all';page=0;
  const weapons=new Set(data.events.map(e=>e.weapon));
  $('#overview').innerHTML=[['Recorded encounters',fmt(data.events.length)],['Identified players',fmt(players.size)],['Weapons recorded',fmt(weapons.size)],['Source exports',fmt(data.files.length)]].map(([l,n])=>`<article><span class="label">${l}</span><strong>${n}</strong></article>`).join('');
  $('#dateRange').textContent=data.events.length?`${new Date(data.events.at(-1).timestamp).toLocaleDateString()} — ${new Date(data.events[0].timestamp).toLocaleDateString()}`:'No parsed events';
  $('#datasetTotals').textContent=`${fmt(players.size)} PLAYERS · ${fmt(data.events.length)} EVENTS · ${data.files.length} EXPORTS`;
  try{recentIds=JSON.parse(localStorage.getItem('dayz-dossier-recent')||'[]')}catch{recentIds=[]}
  recentIds=Array.isArray(recentIds)?[...new Set(recentIds)].filter(id=>players.has(id)).slice(0,5):[];longestLimit=10;
  renderPlayers();renderProfile();renderSummary();renderServerStatistics();
}
function rememberPlayer(id){
  recentIds=[id,...recentIds.filter(x=>x!==id)].slice(0,5);
  try{localStorage.setItem('dayz-dossier-recent',JSON.stringify(recentIds));localStorage.setItem('dayz-dossier-player',id)}catch{}
}
function showView(view){
  $('#profile').hidden=view==='statistics';$('#serverStatistics').hidden=view!=='statistics';
  $('#statisticsNav').classList.toggle('nav-active',view==='statistics');$('#browsePlayers').classList.toggle('nav-active',view!=='statistics');
}
function renderPlayers(){
  $('#recentPlayers').innerHTML=recentIds.length?`<div class="recent-heading">RECENT DOSSIERS</div><div class="recent-list">${recentIds.map(id=>`<button class="recent-player" data-player="${esc(id)}"><span>${esc(players.get(id).name)}</span><span aria-hidden="true">↗</span></button>`).join('')}</div>`:'<p class="recent-empty">Your five most recent selections will appear here.</p>';

  const query=$('#search').value.toLowerCase().trim(),sort=$('#sort').value;
  const list=[...players.values()].filter(p=>p.id.includes(query)||[...p.names].some(n=>n.toLowerCase().includes(query))).sort((a,b)=>sort==='name'?a.name.localeCompare(b.name):b[sort]-a[sort]||a.name.localeCompare(b.name));
  searchMatches=list.map(p=>p.id);
  $('#playerCount').textContent=`${fmt(list.length)} / ${fmt(players.size)}`;
  $('#players').innerHTML=list.length?list.map(p=>`<button class="player ${p.id===selected?'active':''}" data-player="${esc(p.id)}" aria-pressed="${p.id===selected}"><span class="avatar">${esc(p.name.slice(0,2).toUpperCase())}</span><span class="player-text"><span class="player-name">${esc(p.name)}</span><small>${fmt(p.kills)} kills · ${fmt(p.deaths)} deaths</small></span><span class="tally">${p.deaths?(p.kills/p.deaths).toFixed(2):'—'}</span></button>`).join(''):'<p class="empty">No matching players.</p>';
}
function weaponArt(weapon){
  const asset=data.weaponImages?.[weapon];
  return asset?`<img class="weapon-photo" src="${esc(asset.src)}" alt="${esc(weapon)} in-game weapon" title="${esc(asset.note||weapon)}" loading="eager"><a class="image-credit" href="${esc(asset.filePage)}" target="_blank" rel="noopener noreferrer" aria-label="${esc(weapon)} image source">${esc(asset.credit||'DayZ Wiki')} ↗</a>`:'<div class="weapon-unavailable"><span>NO VERIFIED IMAGE</span><small>Exact weapon asset unavailable</small></div>';
}
function associationPanel(p){
  const evidence=data.associations?.profiles?.[p.id]||{team:[],candidates:[]};
  const item=(r,team)=>{
    const other=players.get(r.id),name=other?.name||r.id;
    return `<details class="association-row"><summary><span class="assoc-avatar">${esc(name.slice(0,1).toUpperCase())}</span><span class="assoc-name"><button class="assoc-profile-link" data-player="${esc(r.id)}">${esc(name)}</button>${r.confirmed?'<em class="confirmed-label">Confirmed by you</em>':''}<small>${r.sharedWindows?`${r.sharedWindows} shared-opponent windows · ${r.days} days`:`${r.contextWindows} timing windows · weak evidence`}</small></span><span class="strength">${r.strength}<small>score / 100</small></span></summary><div class="association-evidence"><button class="opponent" data-player="${esc(r.id)}">Open dossier ↗</button><p>${r.sharedWindows} independent shared-opponent windows; ${r.opponents} opponents; ${r.contextWindows} timing windows. ${r.directCombats?`<b>${r.directCombats} direct combat events — excluded from inferred groups.</b>`:'No direct combat recorded in this import.'}</p><table class="component-table"><tbody>${Object.entries(r.components||{}).map(([key,value])=>`<tr><td>${esc(({sharedOpponents:'Shared-opponent patterns',repeatDays:'Repeated dates',timingExcess:'Timing above baseline',timingContext:'Timing context',patternDiversity:'Pattern diversity',graphContext:'Graph context',hourContext:'UTC hour context',distanceContext:'Distance context',directCombatPenalty:'Direct-combat penalty'})[key]||key)}</td><td>${Number(value).toFixed(2)}</td></tr>`).join('')}</tbody></table><p>Raw score: ${r.rawStrength??0} · After shrinkage: ${r.unboundedStrength??0} · ${r.saturated?'Capped at 100':'Rounded to displayed score'}.</p><p>Expected timing windows under the approximate volume baseline: ${r.expectedTimingWindows}. Independent observations: ${r.independentObservations}. Sparse-evidence multiplier: ${r.reliabilityMultiplier}.</p><p>Shared-target / shared-threat / trade-sequence windows: ${r.rolePatterns.sharedTarget||0} / ${r.rolePatterns.sharedThreat||0} / ${r.rolePatterns.tradeSequence||0}. Mutual pattern neighbours: ${r.mutualPatternNeighbours}.</p><p>Distance habit overlap: ${Math.round(r.distanceOverlap*100)} (weak supporting index, not probability).</p><p>UTC event-hour overlap: ${Math.round(r.hourOverlap*100)}% (weak context; not online presence).</p>${r.samples.map(x=>`<p class="evidence-sample">${esc(x.timestamp.slice(0,16).replace('T',' '))} UTC · Opponent: ${esc(players.get(x.opponent)?.name||x.opponent)} · roles ${esc(x.roles.join(' / '))}</p>`).join('')}</div></details>`;
  };
  return `<section class="associations"><div class="panel-heading"><h2>Associated players likelihood</h2><button class="method-button" id="associationMethodButton">How it works ↗</button></div><div class="association-list"><p class="association-section">${evidence.team.some(r=>r.confirmed)?'CONFIRMED MEMBERS · THIRD NOT IDENTIFIED':`INFERRED ${evidence.team.length?evidence.team.length+1+'-PLAYER GROUP':'GROUP'} <span>UNCONFIRMED</span>`}</p>${evidence.team.length?evidence.team.map(r=>item(r,true)).join(''):'<p class="no-team">Insufficient evidence for a consistent duo or trio.</p>'}${evidence.candidates.length?`<p class="association-section">OTHER CANDIDATES · NOT TEAM MEMBERS</p>${evidence.candidates.map(r=>item(r,false)).join('')}`:'<p class="no-team">No temporal or shared-opponent evidence in this import.</p>'}<p class="association-disclaimer">Likelihood score is heuristic and uncalibrated, not a probability. Groups contain at most three people total.</p></div></section>`;
}
function renderProfile(){
  const p=players.get(selected);
  if(!p){$('#profile').innerHTML='<div class="panel empty">No parsed player events. Open the import summary to review the export.</div>';return}
  const top=[...p.weapons].sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0])).slice(0,3);
  $('#profile').innerHTML=`<div class="analyst-grid"><section class="activity" id="activity"><div class="panel-heading"><h2>Recent Kills &amp; Deaths</h2><div class="filters">${['all','kills','deaths'].map(f=>`<button data-filter="${f}" class="${filter===f?'selected':''}" aria-pressed="${filter===f}">${f[0].toUpperCase()+f.slice(1)}</button>`).join('')}</div></div><p class="activity-context">Recorded encounters for <b>${esc(p.name)}</b></p><div class="table-wrap"><table><thead><tr><th>TIME</th><th>EVENT</th><th>PLAYER</th><th>WEAPON</th><th>DISTANCE</th></tr></thead><tbody id="activityRows"></tbody></table></div><div class="pager" id="pager"></div></section><section class="survivor-profile" id="playerStats"><div class="survivor-portrait"><img id="survivorImage" src="${esc(data.portraits?.[p.id]||'/assets/survivor.png')}" alt="Decorative survivor illustration; not this player’s appearance or equipment"><span>ILLUSTRATIVE CHARACTER</span></div><div class="survivor-details"><div class="profile-banner"><div class="identity"><p class="profile-kicker">SURVIVOR DOSSIER</p><h1>${esc(p.name)}</h1><p class="profile-source">CFTools profile · Imported record</p><p class="profile-id">${esc(p.id)}</p></div><div class="metrics">${[['Observed K/D',p.deaths?(p.kills/p.deaths).toFixed(2):'—'],['Kills',fmt(p.kills)],['Deaths',fmt(p.deaths)]].map(([l,n])=>`<div class="metric"><strong>${n}</strong><span>${l}</span></div>`).join('')}</div></div><div class="weapons"><div class="panel-heading"><h2>Favorite weapons</h2><span>BY KILLS</span></div>${top.length?`<div class="weapon-grid">${top.map(([w,n],i)=>`<article class="weapon weapon-${i}"><div class="weapon-visual">${weaponArt(w)}</div><div class="weapon-caption"><h3>${esc(w)}</h3><p>${fmt(n)} kills <span>${Math.round(n/p.kills*100)}%</span></p></div></article>`).join('')}</div><p class="art-note">In-game images · DayZ Wiki / MyDayZ · Rights retained</p>`:'<p class="empty">No weapon kills in this dataset.</p>'}</div></div></section><div class="lower-panels">${associationPanel(p)}<section class="aliases"><div class="panel-heading"><h2>Known Aliases</h2><span>${p.names.size} OBSERVED</span></div><p class="alias-label">CONFIRMED BY PROFILE ID</p><ul>${[...p.names].map(n=>`<li>${esc(n)}${n===p.name?'<span>Latest</span>':''}</li>`).join('')}</ul><p class="alias-note">Names observed on this exact CFTools profile.</p></section></div></div>`;
  const portrait=$('#survivorImage');
  portrait.addEventListener('error',()=>{if(!portrait.dataset.fallback){portrait.dataset.fallback='true';portrait.src='/assets/survivor.png'}else{portrait.hidden=true;portrait.parentElement.classList.add('portrait-unavailable')}});
  document.querySelectorAll('.weapon-photo').forEach(img=>img.addEventListener('error',()=>{img.hidden=true;img.parentElement.classList.add('weapon-image-failed')}));
  renderActivity();
}
function renderActivity(){
  const p=players.get(selected);const events=p.events.filter(e=>filter==='all'||(filter==='kills'?e.killer.id===p.id:e.victim.id===p.id));
  const max=Math.max(0,Math.ceil(events.length/pageSize)-1);page=Math.min(page,max);
  $('#activityRows').innerHTML=events.slice(page*pageSize,(page+1)*pageSize).map(e=>{
    const kill=e.killer.id===p.id,opponent=kill?e.victim:e.killer,date=new Date(e.timestamp);
    return `<tr><td title="${esc(e.timestamp)}">${date.toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})}<small>${date.toLocaleDateString()}</small></td><td><span class="result ${kill?'':'death'}"><span aria-hidden="true">${kill?'×':'●'}</span> ${kill?'KILL':'DEATH'}</span></td><td><button class="opponent" data-player="${esc(opponent.id)}">${esc(opponent.name)}</button></td><td>${esc(e.weapon)}</td><td>${e.distance.toLocaleString(undefined,{maximumFractionDigits:2})} m</td></tr>`;
  }).join('')||'<tr><td colspan="5" class="empty">No encounters in this view.</td></tr>';
  $('#pager').innerHTML=`<span>${fmt(events.length)} encounters · Page ${page+1} of ${max+1}</span><div><button data-page="-1" ${page===0?'disabled':''}>Previous</button> <button data-page="1" ${page===max?'disabled':''}>Next</button></div>`;
}
function renderSummary(){
  const dup=data.files.reduce((n,f)=>n+f.duplicates,0);
  $('#summaryContent').innerHTML=`${data.audit?`<p><b>${fmt(data.audit.rawOccurrences)}</b> raw occurrences = <b>${fmt(data.audit.uniqueMessageIds)}</b> unique Discord message IDs + <b>${fmt(data.audit.duplicateOccurrences)}</b> duplicates. <b>${fmt(data.audit.conflictingIds)}</b> conflicting IDs; <b>${fmt(data.audit.recoveredIds)}</b> incomplete-first copies recovered.</p><details><summary>Audit examples: repeated message IDs</summary>${data.audit.examples.map(x=>`<p>${esc(x.text)}<br>${x.occurrences} occurrences · ${esc(Object.entries(x.sources).map(([name,n])=>name+': '+n).join(' · '))}<br>Message ID ${esc(x.id)}</p>`).join('')}</details>`:''}${(data.conflicts||[]).map(c=>`<details><summary>Conflicting message ${esc(c.id)}</summary><p>${esc(c.reason)} Chosen source: ${esc(c.chosenSource)}</p>${c.variants.map(v=>`<pre>${esc(v.source)} · ${v.parsed?'Parsed':'Unparsed'} · ${esc(v.text)}</pre>`).join('')}</details>`).join('')}<p><b>${fmt(data.events.length)}</b> parsed encounters · <b>${fmt(dup)}</b> duplicate messages removed · <b>${fmt(data.unparsed.length)}</b> unparsed unique messages</p><div class="table-wrap"><table><thead><tr><th>FILE</th><th>MESSAGES</th><th>PARSED</th><th>DUPLICATES</th><th>WITHIN FILE</th><th>OVERLAP IDS</th><th>UNPARSED</th></tr></thead><tbody>${data.files.map(f=>`<tr><td>${esc(f.name)}</td><td>${fmt(f.messages)}</td><td>${fmt(f.parsed)}</td><td>${fmt(f.duplicates)}</td><td>${fmt(f.withinFileDuplicates||0)}</td><td>${fmt(f.overlapIdsWithEarlierFiles||0)}</td><td>${fmt(f.unparsed)}</td></tr>`).join('')}</tbody></table></div><p class="muted">Import a replacement set of exports. Select all files to combine; this view is temporary and restarting restores the project’s exports in the project folder.</p><input id="importFiles" type="file" accept=".txt,.html" multiple aria-label="Choose Discord exports"><p id="importStatus" role="status" class="muted"></p><h2 style="margin:24px 0 12px">Unparsed messages (${fmt(data.unparsed.length)})</h2>${data.unparsed.map(r=>`<details><summary>${esc(r.timestamp||'No timestamp')} · ${esc(r.text.slice(0,100)||'Empty message')}</summary><p>${esc(r.reason)}</p><p>${esc(r.source)} · Message ${esc(r.id)}</p><pre>${esc(r.text)}</pre></details>`).join('')||'<p class="muted">All unique messages were parsed.</p>'}`;
}
function showPlayers(open){$('#playerPicker').hidden=!open;$('#search').setAttribute('aria-expanded',String(open))}
$('#search').addEventListener('input',()=>{renderPlayers();showPlayers(true)});$('#search').addEventListener('focus',()=>showPlayers(true));$('#sort').addEventListener('change',renderPlayers);
$('#browsePlayers').onclick=()=>{showView('player');showPlayers(true);$('#search').focus()};
$('#statisticsNav').onclick=e=>{e.preventDefault();showView('statistics');showPlayers(false)};
$('#activityNav').onclick=()=>showView('player');$('#closePlayers').onclick=()=>showPlayers(false);
function selectPlayer(id){selected=id;rememberPlayer(id);page=0;renderPlayers();renderProfile();showView('player');showPlayers(false)}
document.addEventListener('keydown',e=>{if(e.key==='Escape')showPlayers(false);if(e.key==='Enter'&&e.target.id==='search'&&searchMatches.length===1){e.preventDefault();selectPlayer(searchMatches[0])}});
$('#summaryButton').onclick=()=>$('#summary').showModal();$('#closeSummary').onclick=()=>$('#summary').close();
document.addEventListener('click',e=>{
  if(e.target.closest('[data-longest-more]')){longestLimit+=10;renderServerStatistics()}
  if(e.target.closest('#associationMethodButton'))$('#associationMethod').showModal();
  const player=e.target.closest('[data-player]');if(player){selectPlayer(player.dataset.player)}
  if(!e.target.closest('#playerPicker,.search,#browsePlayers'))showPlayers(false);
  const f=e.target.closest('[data-filter]');if(f){filter=f.dataset.filter;page=0;renderProfile()}
  const pg=e.target.closest('[data-page]');if(pg&&!pg.disabled){page+=Number(pg.dataset.page);renderActivity()}
});
document.addEventListener('change',async e=>{
  if(e.target.id!=='importFiles'||!e.target.files.length)return;
  const input=e.target;input.disabled=true;$('#importStatus').textContent='Reading and parsing exports…';
  try{const files=await Promise.all([...input.files].map(async f=>({name:f.name,text:await f.text()})));const res=await fetch('/api/import',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({files})});const result=await res.json();if(!res.ok)throw Error(result.error);load(result);$('#importStatus').textContent='Import complete.'}catch(err){$('#importStatus').textContent=`Import failed: ${err.message}`;input.disabled=false}
});
fetch('/api/data').then(r=>{if(!r.ok)throw Error('Server unavailable');return r.json()}).then(load).catch(err=>{$('#profile').innerHTML=`<div class="panel empty">Start the Python backend, then open http://127.0.0.1:8765. ${esc(err.message)}</div>`});
