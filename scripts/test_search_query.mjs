import test from 'node:test';
import assert from 'node:assert/strict';
import {existsSync} from 'node:fs';
import {planQuery,roleVocabulary} from '../assets/search/query.mjs';
import {createRanker} from '../assets/search/rank.mjs';

test('role words bridge to real, non-clinical topics and disclose the missing entry',()=>{
 for(const role of roleVocabulary){
  for(const alias of role.aliases){
   const plan=planQuery(alias);
   assert.equal(plan.role.name,role.name);
   assert.match(plan.notice,/no dedicated reference article/);
   assert.match(plan.notice,/role label alone/);
  }
  for(const path of role.topics){
   assert.ok(existsSync(new URL('../'+path.replace('.html','.md'),import.meta.url)),path);
   assert.ok(!path.includes('/pd-'),path);
  }
 }
 assert.deepEqual(planQuery('matriarch').role.topics,planQuery('patriarch').role.topics);
 assert.equal(planQuery('What is a matriarch?').role.name,'Matriarch');
 assert.equal(planQuery('What does matriarch mean?').role.name,'Matriarch');
});

test('short queries receive question context without inventing an unknown definition',()=>{
 assert.equal(planQuery('introvert').embeddingText,'What is introvert?');
 assert.equal(planQuery('Why do I refuse help?').embeddingText,'Why do I refuse help?');
 assert.equal(planQuery('zzqvpxj987').role,null);
 assert.equal(planQuery('matriarchy').role,null);
 assert.equal(planQuery('matriarch',[{title:'Matriarchs and family roles'}]).role,null);
});

test('word-only search also offers clearly marked related role topics',()=>{
 const documents=roleVocabulary[0].topics.map((url,i)=>({url,title:['Family expectations','Changing roles','Culture and power'][i],keywords:''}));
 const passages=documents.map((d,i)=>({document:i,anchor:'main',heading:d.title,text:'Read how this affects expectations and relationships.'}));
 const results=createRanker({documents,passages,dimensions:384})('matriarch');
 assert.equal(results.length,3);
 assert.equal(documents[results[0].document].title,'Family expectations');
 assert.ok(results.every(r=>r.related));
 assert.equal(createRanker({documents,passages,dimensions:384})('zzqvpxj987').length,0);
});

test('reviewed aliases find their actual concept without assigning unknown labels',()=>{
 const documents=[{url:'reference/invisible-work.html',title:'Invisible work',keywords:'',aliases:['mental load']}];
 const passages=[{document:0,anchor:'main',heading:'Invisible work',text:'Planning and coordinating work that otherwise goes unseen.'}];
 const rank=createRanker({documents,passages,dimensions:384});
 assert.equal(rank('mental load')[0].document,0);
 assert.equal(rank('unrecognisedxyz').length,0);
});
