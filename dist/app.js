/* Feed text is always rendered as text, never HTML. */
const $ = id => document.getElementById(id);
const controls = ['search', 'year', 'month', 'type'];
const months = Array.from({length:12}, (_,i) => new Date(2020,i).toLocaleString('en',{month:'long'}));
let entries = [], visible = 16;
function element(tag, text, className) { const e=document.createElement(tag); if(text!==undefined)e.textContent=text; if(className)e.className=className; return e; }
function safeLink(url) { try { return new URL(url).protocol==='https:'; } catch { return false; } }
function filtered() { const q=$('search').value.trim().toLowerCase(); return entries.filter(e => (!$('year').value || e.date.startsWith($('year').value)) && (!$('month').value || e.date.slice(5,7)===$('month').value) && (!$('type').value || e.type===$('type').value) && (!q || [e.title,e.summary,e.publisher].join(' ').toLowerCase().includes(q))); }
function render() {
  const list=filtered(); $('entries').replaceChildren(); $('result-count').textContent=`${list.length} ${list.length===1?'entry':'entries'}`;
  $('timeline').querySelector('h2').textContent=$('year').value ? `${$('month').value ? months[Number($('month').value)-1]+' ' : ''}${$('year').value} developments` : 'Latest developments';
  const params=new URLSearchParams(); controls.forEach(k=>{if($(k).value)params.set(k,$(k).value)}); history.replaceState(null,'',location.pathname+(params.size?'?'+params.toString():'')+location.hash);
  if(!list.length){const box=element('div',undefined,'empty');box.append(element('h3','No matching developments'),element('p','Try another month, clear your search, or reset the filters.'));$('entries').append(box);}
  let lastMonth='';
  list.slice(0,visible).forEach(e=>{
    const key=e.date.slice(0,7);if(key!==lastMonth){$('entries').append(element('h3',`${months[Number(e.date.slice(5,7))-1]} ${e.date.slice(0,4)}`,'month-heading'));lastMonth=key;}
    const article=element('article',undefined,'entry'), date=element('time',new Date(e.date+'T12:00:00Z').toLocaleDateString('en',{month:'short',day:'2-digit',timeZone:'UTC'}));date.dateTime=e.date;
    const body=element('div'),meta=element('div',undefined,'entry-meta');meta.append(element('span',e.type,'tag '+e.type),element('span',e.publisher));if(e.automated)meta.append(element('span','Feed entry','automated'));
    const h=element('h3'),a=element('a',e.title);a.href=e.url; a.target='_blank';a.rel='noopener noreferrer';h.append(a);
    const source=element('a',e.type==='Research'?'Read paper ↗':'Read source ↗','source');source.href=e.url;source.target='_blank';source.rel='noopener noreferrer';
    body.append(meta,h,element('p',e.summary),source);article.append(date,body);$('entries').append(article);
  });$('more').hidden=list.length<=visible;
}
async function init(){
  months.forEach((m,i)=>{const o=element('option',m);o.value=String(i+1).padStart(2,'0');$('month').append(o)});
  for(let y=new Date().getFullYear();y>=2021;y--){const o=element('option',String(y));o.value=String(y);$('year').append(o)}
  const params=new URLSearchParams(location.search);controls.forEach(k=>{if(params.has(k))$(k).value=params.get(k);$(k).addEventListener(k==='search'?'input':'change',()=>{visible=16;render()})});
  $('reset').addEventListener('click',()=>{controls.forEach(k=>$(k).value='');visible=16;render()});$('more').addEventListener('click',()=>{visible+=16;render()});
  try{const r=await fetch('data.json',{cache:'no-cache'});if(!r.ok)throw Error('Archive unavailable');const data=await r.json();entries=data.entries.filter(e=>safeLink(e.url)).sort((a,b)=>b.date.localeCompare(a.date));$('total').textContent=entries.length;
    $('updated').textContent=new Date(data.lastChecked+'T12:00:00Z').toLocaleDateString('en',{day:'numeric',month:'short',year:'numeric',timeZone:'UTC'});
    const failed=(data.feeds||[]).filter(f=>f.status!=='ok');const stale=(Date.now()-Date.parse(data.lastChecked+'T00:00:00Z'))/86400000>9;
    if(failed.length||stale){$('feed-status').hidden=false;$('feed-status').textContent=stale?'Source checks are overdue. The archive remains available; newer developments may be missing.':`Some sources could not be refreshed: ${failed.map(f=>f.name).join(', ')}. Previously collected entries remain available.`;}
    render();
  }catch(error){$('entries').replaceChildren(element('div','The archive could not load. Please reload the page or use the JSON download below.','empty'));$('updated').textContent='Unavailable';}
}init();
