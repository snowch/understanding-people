// Retrieval only: rankings are reading suggestions, never an assessment of a person.
const stop = new Set('a an and are as at be been but by can could did do does for from had has have how i if in into is it its me my of on or our should so some someone something than that the their them then there these they this to us was we were what when where which who why will with would you your'.split(' '));
export const normalise = text => text.toLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g,'');
export const terms = text => (normalise(text).match(/[\p{L}\p{N}]+/gu)||[]).filter(w=>!stop.has(w)&&w.length>1);

export function createRanker(index, vectorBytes) {
 const {documents,passages,dimensions}=index;
 const vectors=vectorBytes?new Int8Array(vectorBytes):null;
 if(vectors&&vectors.length!==passages.length*dimensions)throw new Error('Search vectors do not match the book.');
 const frequencies=new Map(),lengths=[],counts=[],norms=[];
 const titleTerms=documents.map(d=>new Set(terms(d.title+' '+d.keywords)));
 for(let i=0;i<passages.length;i++){
  const words=terms(passages[i].text+' '+passages[i].heading),count=new Map();
  for(const word of words)count.set(word,(count.get(word)||0)+1);
  for(const word of count.keys())frequencies.set(word,(frequencies.get(word)||0)+1);
  lengths.push(words.length);counts.push(count);
  if(vectors){let sum=0;for(let j=0;j<dimensions;j++)sum+=vectors[i*dimensions+j]**2;norms.push(Math.sqrt(sum));}
 }
 const average=lengths.reduce((a,b)=>a+b,0)/lengths.length;
 return function rank(query,embedding=null){
  const words=[...new Set(terms(query))],literal=normalise(query).trim(),scores=[];
  const clinicalIntent=/\b(disorder|diagnos\w*|clinical|narciss\w*|borderline|antisocial|avoidant|dependent|paranoid|schiz\w*|histrionic|ocd|ocpd|npd|bpd|dpd)\b/.test(literal);
  const resourceIntent=/\b(library|catalog\w*|sources?|research|bibliograph\w*|references?|contents|author)\b/.test(literal);
  for(let i=0;i<passages.length;i++){
   const p=passages[i],d=documents[p.document];let lexical=0,semantic=0;
   for(const word of words){
    const frequency=counts[i].get(word)||0,df=frequencies.get(word)||0;
    const idf=Math.log(1+(passages.length-df+.5)/(df+.5));
    if(frequency)lexical+=idf*(frequency*2.2)/(frequency+1.2*(.25+.75*lengths[i]/average));
    if(titleTerms[p.document].has(word))lexical+=idf*1.2;
   }
   const exact=literal.length>2&&normalise(d.title)===literal;
   if(exact)lexical+=20;
   if(embedding&&vectors){for(let j=0;j<dimensions;j++)semantic+=embedding[j]*vectors[i*dimensions+j];semantic/=norms[i]||1;}
   if(embedding){if(semantic<.30&&!(lexical>0&&words.length<=2)&&!exact)continue;}
   else if(lexical<=0)continue;
   const wordScore=lexical/(lexical+8);
   const directory=['reference/index.html','reference/sources.html','references.html','contents.html','about.html'].includes(d.url);
   const score=(embedding?semantic*.83+wordScore*.17+(exact?.25:0):lexical)
    -(d.clinical&&!clinicalIntent?(embedding ? 0.18 : 3):0)
    -(directory&&!resourceIntent&&!exact?(embedding ? 0.25 : 5):0);
   scores.push({passage:i,document:p.document,score,semantic,lexical});
  }
  scores.sort((a,b)=>b.score-a.score||a.passage-b.passage);
  const seen=new Set();return scores.filter(r=>{if(seen.has(r.document))return false;seen.add(r.document);return true;}).slice(0,30);
 };
}
