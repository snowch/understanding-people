// Downloads always require a click. Highlighting only reflects reading preferences.
(()=>{
 const cards=document.querySelectorAll('[data-audiobook-voice]');
 if(!cards.length||!window.BookSettings)return;
 const show=preferences=>{for(const card of cards){
  const preferred=card.dataset.audiobookVoice===preferences.voice;
  card.dataset.preferred=String(preferred);
  const badge=card.querySelector('[data-download-preferred]');if(badge)badge.hidden=!preferred;
 }};
 show(window.BookSettings.get());window.BookSettings.subscribe(show);
})();
