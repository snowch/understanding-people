import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const source=readFileSync(new URL('./service-worker.js',import.meta.url),'utf8')
 .replace('__VERSION__','unit').replace('__FILES__','["./","index.html"]')
 .replace('__SEARCH_VERSION__','unit').replace('__SEARCH_FILES__','["assets/search/model.onnx"]');

function worker(caches,fetch){
 const events={};
 vm.runInNewContext(source,{URL,caches,fetch,self:{registration:{scope:'https://book.test/understanding-people/'},clients:{claim:async()=>{}},addEventListener:(kind,fn)=>events[kind]=fn}});
 return events;
}

test('model response survives unavailable storage and a full cache',async()=>{
 for(const unavailable of [true,false]){
  const response={ok:true,clone(){return this;}};let fetched=0;
  const events=worker({open:async()=>{if(unavailable)throw new Error('Storage blocked');return {match:async()=>null,put:async()=>{throw new Error('Quota full');}};}},async()=>{fetched++;return response;});
  let pending;
  events.fetch({request:{method:'GET',url:'https://book.test/understanding-people/assets/search/model.onnx?v=edition'},respondWith:p=>pending=p});
  assert.equal(await pending,response);assert.equal(fetched,1);
 }
});

test('cached model avoids a network request, while engine upgrades preserve unrelated caches',async()=>{
 const saved={ok:true};const deleted=[];
 const events=worker({open:async()=>({match:async()=>saved}),keys:async()=>['understanding-people-unit','understanding-people-old','up-book-semantic-model-unit','up-book-semantic-model-old','another-book-cache'],delete:async key=>deleted.push(key)},async()=>{throw new Error('Offline');});
 let pending;
 events.fetch({request:{method:'GET',url:'https://book.test/understanding-people/assets/search/model.onnx'},respondWith:p=>pending=p});
 assert.equal(await pending,saved);
 events.activate({waitUntil:p=>pending=p});await pending;
 assert.deepEqual(deleted.sort(),['understanding-people-old','up-book-semantic-model-old'].sort());
});
