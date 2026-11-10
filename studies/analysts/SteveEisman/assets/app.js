/* Offline research navigation. Source data is embedded in the HTML. */
const D=JSON.parse(document.getElementById('audit-data').textContent);
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const badge=(v,n)=>`<span class="badge ${esc(v)}">${esc(D.labels[v]||v)}${n===undefined?'':' · '+n}</span>`;
const unitMap=new Map(D.units.map(u=>[u.id,u]));
const claimText=new Map;
for(const c of D.claims)claimText.set(c.unit_id,(claimText.get(c.unit_id)||'')+' '+c.claim+' '+c.reason+' '+c.entities?.join(' '));
function route(){
  const [requested,id,claim]=decodeURIComponent(location.hash.slice(1)).split('/');
  const valid=['summary','takes','repeated','framework','library','claims','tools','method','coverage','episode'];
  const panel=valid.includes(requested)?requested:'summary';
  document.querySelectorAll('.panel').forEach(el=>el.hidden=el.id!==panel);
  document.querySelectorAll('.main-nav a').forEach(a=>{a.classList.toggle('active',a.dataset.panel===panel);a.setAttribute('aria-current',a.dataset.panel===panel?'page':'false')});
  if(panel==='episode'){
    const u=unitMap.get(id);
    $('episode-content').innerHTML=u?D.episode_html[id]:'<div class="note">That review item was not found. Return to the episode library.</div>';
    if(claim){const el=$(claim);if(el){el.querySelector('details')?.setAttribute('open','');requestAnimationFrame(()=>el.scrollIntoView({block:'start'}));}}
    else window.scrollTo({top:0,behavior:'instant'});
  }
}
window.addEventListener('hashchange',route);
route();
function episodes(){
  const q=$('episode-search').value.toLowerCase(),year=$('episode-year').value,status=$('episode-status').value;
  const list=D.units.filter(u=>(!year||u.first_listed_publication.startsWith(year))&&(!status||(status==='complete'?!!u.review:!u.review))&&(!q||[u.title,u.review?.summary,claimText.get(u.id)].join(' ').toLowerCase().includes(q))).sort((a,b)=>b.first_listed_publication.localeCompare(a.first_listed_publication));
  $('episode-count').textContent=`${list.length} review items`;
  $('episode-results').innerHTML=list.map(u=>`<article class="card"><div class="meta">${esc(u.first_listed_publication.slice(0,10))} · ${esc(u.format.replaceAll('_',' '))}</div><h3><a href="#episode/${esc(u.id)}">${esc(u.title)}</a></h3><p>${esc(u.review?.summary||'Review pending.')}</p><div class="badges">${u.review?Object.entries(u.counts).map(([v,n])=>badge(v,n)).join(''):'<span class="badge">Pending</span>'}</div><p class="small card-link"><a href="#episode/${esc(u.id)}">Read review · ${u.claim_count} claims →</a></p></article>`).join('')||'<p class="empty">No review items match these filters.</p>';
}
for(const id of ['episode-search','episode-year','episode-status'])$(id).addEventListener('input',episodes);
episodes();
let limit=50;
function claims(reset=true){
  if(reset)limit=50;
  const q=$('claim-search').value.toLowerCase(),speaker=$('speaker-filter').value,verdict=$('verdict-filter').value,materiality=$('materiality-filter').value,kind=$('kind-filter').value,year=$('claim-year').value;
  const list=D.claims.filter(c=>{
    const own=c.speaker==='Steve Eisman'&&c.synthesis_role!=='reported_third_party_forecast'&&!['reported','rejected'].includes(c.stance)&&!c.exclude_from_eisman_forecast_score;
    return (speaker==='all'||(speaker==='host'?own:!own))&&(!verdict||c.verdict===verdict)&&(!materiality||c.materiality===materiality)&&(!kind||c.kind===kind)&&(!year||c.date.startsWith(year))&&(!q||[c.claim,c.reason,c.speaker,c.family,c.unit_title,c.entities?.join(' '),...(c.evidence||[]).map(e=>e.finding)].join(' ').toLowerCase().includes(q));
  }).sort((a,b)=>b.date.localeCompare(a.date));
  $('claim-count').textContent=`${list.length.toLocaleString()} matching claim occurrences · showing ${Math.min(limit,list.length)}`;
  $('claim-results').innerHTML=list.slice(0,limit).map(c=>`<article class="claim-card"><div class="claim-top"><div><div class="meta">${esc(c.date)} · ${esc(c.speaker)} · ${esc(c.kind)} · ${esc(c.materiality||'not classified')}</div><h3><a href="#episode/${esc(c.unit_id)}/${esc(c.id)}">${esc(c.claim)}</a></h3></div>${badge(c.verdict)}</div><p>${esc(c.reason)}</p><div class="meta">${esc(c.unit_title)} · ${esc(c.source_location)}</div><p class="small card-link"><a href="#episode/${esc(c.unit_id)}/${esc(c.id)}">Read reasoning & evidence →</a> <a target="_blank" rel="noopener" href="${esc(c.source_href)}">Original source ↗</a></p></article>`).join('')||'<p class="empty">No claims match these filters.</p>';
  $('show-more').hidden=limit>=list.length;
}
for(const id of ['claim-search','speaker-filter','verdict-filter','materiality-filter','kind-filter','claim-year'])$(id).addEventListener('input',()=>claims());
$('show-more').onclick=()=>{limit+=50;claims(false)};
claims();
$('listing-search').addEventListener('input',()=>{const q=$('listing-search').value.toLowerCase();document.querySelectorAll('#listing-table tbody tr').forEach(row=>row.hidden=!row.textContent.toLowerCase().includes(q))});
