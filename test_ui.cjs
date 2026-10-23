// Exercise the actual browser application logic against the running Python API.
const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict');
(async()=>{
 const alpha={id:'alpha',name:'Example Alpha'},bravo={id:'bravo',name:'Example Bravo'};
 const messages=Array.from({length:12},(_,i)=>{
  const victim=i%2?alpha:bravo,killer=i%2?bravo:alpha,id=i+1;
  return `<li id="chat-messages-1-${id}"><div><time datetime="2025-01-01T12:00:${String(i).padStart(2,'0')}.000Z">noise</time><div id="message-content-${id}"><a href="https://app.cftools.cloud/profile/${victim.id}"><span>${victim.name}</span></a><span> got killed by </span><a href="https://app.cftools.cloud/profile/${killer.id}">${killer.name}</a><span> (</span><span>VS-89</span><span>, </span><span>10</span><span>m)</span></div></div></li>`;
 }).join('');
 const response=await fetch('http://127.0.0.1:8765/api/import',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({files:[{name:'fixture.txt',text:messages}]})});
 assert.equal(response.status,200);
 const data=await response.json();
 assert.equal(data.events.length,12);
 const nodes=new Map();const get=key=>{if(!nodes.has(key))nodes.set(key,{innerHTML:'',textContent:'',dataset:{},classList:{toggle(){}},parentElement:{classList:{add(){}}},value:key==='#sort'?'kills':'',addEventListener(event,fn){this['on'+event]=fn},setAttribute(){},showModal(){this.open=true},close(){this.open=false}});return nodes.get(key)};
 const context=vm.createContext({document:{querySelector:get,querySelectorAll(){return []},addEventListener(){}},fetch:async()=>({ok:true,json:async()=>data}),console,Set,Map,Date,Number,String,Math,Promise});
 vm.runInContext(fs.readFileSync('statistics.js','utf8'),context);vm.runInContext(fs.readFileSync('app.js','utf8'),context);await new Promise(resolve=>setImmediate(resolve));
 assert.match(get('#profile').innerHTML,/Favorite weapons/);
 get('#search').value='Example Alpha';vm.runInContext('renderPlayers()',context);assert.match(get('#players').innerHTML,/Example Alpha/);
 get('#search').value='impossible-no-player-123';vm.runInContext('renderPlayers()',context);assert.match(get('#players').innerHTML,/No matching players/);
 vm.runInContext("selected=[...players.values()].find(p=>p.names.has('Example Alpha')).id;renderProfile();filter='deaths';renderProfile()",context);
 assert.match(get('#activityRows').innerHTML,/DEATH/);assert.doesNotMatch(get('#activityRows').innerHTML,/ KILL</);
 vm.runInContext("filter='kills';page=1;renderProfile()",context);assert.match(get('#activityRows').innerHTML,/ KILL</);assert.match(get('#pager').innerHTML,/Page 2/);
 get('#survivorImage').onerror();assert.equal(get('#survivorImage').src,'/assets/survivor.png');get('#survivorImage').onerror();assert.equal(get('#survivorImage').hidden,true);
 assert.equal(Object.keys(data.portraits).length,2);assert.equal((await fetch('http://127.0.0.1:8765/assets/survivor.png')).status,200);
 assert.match(get('#summaryContent').innerHTML,/Unparsed messages \(0\)/);
 assert.match(get('#serverStatistics').innerHTML,/Top five players/);assert.match(get('#serverStatistics').innerHTML,/Unusual recorded items/);
 vm.runInContext("for(const id of [...players.keys()].slice(0,7))rememberPlayer(id);rememberPlayer([...players.keys()][3]);",context);
 assert.equal(vm.runInContext('recentIds.length',context),5);assert.equal(vm.runInContext('new Set(recentIds).size',context),5);assert.equal(vm.runInContext('recentIds[0]===[...players.keys()][3]',context),true);
 const valid=await fetch('http://127.0.0.1:8765/api/import',{method:'POST',body:JSON.stringify({files:[{name:'fixture.txt',text:'<li id="chat-messages-1-2"><div id="message-content-2">Review me</div></li>'}]})});
 const imported=await valid.json();assert.equal(imported.unparsed[0].text,'Review me');assert.equal(imported.events.length,0);
 const bad=await fetch('http://127.0.0.1:8765/api/import',{method:'POST',body:JSON.stringify({files:[{name:'empty.txt',text:'not a Discord export'}]})});assert.equal(bad.status,400);
 assert.equal((await fetch('http://127.0.0.1:8765/server.py')).status,404);
 console.log('PASS: fixture import, search, player selection, death/kill filters, pagination, summary, invalid import and private-file restriction.');
})().catch(e=>{console.error(e);process.exitCode=1});
