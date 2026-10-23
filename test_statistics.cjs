const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict');
const c=vm.createContext({console});vm.runInContext(fs.readFileSync('statistics.js','utf8'),c);
vm.runInContext(`
const pp=new Map(Array.from({length:6},(_,i)=>[String(i),{id:String(i),name:'Name '+i,kills:4,deaths:1}]));
const fixture=[0,null,100,100,-4,undefined].map((distance,i)=>({distance,weapon:i%2?'Knife':'Rifle',timestamp:i<3?'2024-06-01T12:00:00Z':'2024-06-02T12:00:00Z'}));
const result=serverAggregates(fixture,pp);const empty=serverAggregates([],new Map());
`,c);
assert.equal(vm.runInContext('result.median',c),100);assert.equal(vm.runInContext('result.validDistances',c),3);assert.equal(vm.runInContext('result.longestEvents.length',c),2);
assert.equal(vm.runInContext('result.weapons.reduce((n,w)=>n+w[1],0)',c),6);
assert.equal(vm.runInContext('result.leaders.length',c),5);assert.equal(vm.runInContext('result.leaders.every(p=>p.rank===1)',c),true);
assert.equal(vm.runInContext('result.days.length',c),2);assert.equal(vm.runInContext('empty.longest',c),null);assert.equal(vm.runInContext('empty.median',c),null);
console.log('PASS: aggregate counts, tied records/ranks, top-five boundary, missing/negative distances, valid zero, daily totals and empty input.');
