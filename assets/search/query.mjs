// Reviewed navigation vocabulary, not new reference entries or inferred motives.
const family=['reference/familynorms.html','reference/life-transitions.html','chapters/07-culture-groups-power.html'];
export const roleVocabulary=[
 {name:'Matriarch',aliases:['matriarch','matriarchs'],definition:'A woman regarded as the head or a leading figure of a family or group.',context:'Family leadership, roles, expectations and culture.',topics:family},
 {name:'Patriarch',aliases:['patriarch','patriarchs'],definition:'A man regarded as the head or a leading figure of a family or group.',context:'Family leadership, roles, expectations and culture.',topics:family},
 {name:'Peacemaker',aliases:['peacemaker','peacemakers','peace maker'],definition:'A person who tries to reduce conflict or help people reach agreement.',context:'Listening, resolving disagreements and making workable agreements.',topics:['reference/listening.html','reference/shared-agreement.html','chapters/08-questions-listening-disagreement.html']},
 {name:'Scapegoat',aliases:['scapegoat','scapegoats'],definition:'A person or group unfairly made to carry blame.',context:'Shifting responsibility, criticism and unequal power.',topics:['reference/blame-shifting.html','reference/criticism.html','reference/power.html']}
];

export function planQuery(query,documents=[]){
 const text=query.trim();
 const key=text.toLowerCase().replace(/[“”"'‘’?!.]+$/g,'').replace(/^[“”"'‘’]+/g,'')
  .replace(/^what (?:is|are) (?:an? |the )?/,'').replace(/^what does (.+) mean$/,'$1')
  .replace(/^(?:define|meaning of) /,'').trim();
 const role=roleVocabulary.find(item=>item.aliases.includes(key));
 const direct=role&&documents.some(d=>role.aliases.some(alias=>(' '+d.title.toLowerCase().replace(/[^\p{L}\p{N}]+/gu,' ')+' ').includes(' '+alias+' ')));
 if(role&&!direct)return {embeddingText:role.name+'. '+role.definition+' '+role.context,role,
  notice:role.name+': '+role.definition+' There is no dedicated entry for this term; the pages below cover related topics. A role label alone does not tell you how someone behaves.'};
 const short=(text.match(/[\p{L}\p{N}]+/gu)||[]).length<=3;
 const question=/^(what|why|how|when|where|who|can|does|is|are|do)\b/i.test(text)||/[?]/.test(text);
 return {embeddingText:short&&!question?'What is '+text+'?':text,role:null,notice:''};
}
