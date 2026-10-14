/* KBO HUB 공통 스크립트: 데이터 로드, 헤더/푸터, 화면 조각 함수 */
const TC={"KT":["#1a1a1a","#EB1C24"],"삼성":["#074CA1","#9FB5D6"],"KIA":["#EA0029","#1a1a1a"],"LG":["#C30452","#1a1a1a"],"두산":["#131230","#E60012"],"SSG":["#CE0E2D","#F2B705"],"롯데":["#041E42","#D00F31"],"NC":["#315288","#AF917B"],"한화":["#E8590C","#1a1a1a"],"키움":["#570514","#C69B5B"]};
const NAV=[["index.html","홈"],["schedule.html","일정"],["results.html","결과"],["standings.html","팀 순위"],["postseason.html","포스트시즌"],["teams.html","팀"],["leaders.html","선수 순위"],["players.html","선수"]];
const $=id=>document.getElementById(id);
function themeNow(){return document.documentElement.dataset.theme==="dark"?"dark":"light"}
function setTheme(t){document.documentElement.dataset.theme=t;try{localStorage.setItem("kbo-theme",t)}catch(e){}const b=$("themeBtn");if(b)b.textContent=t==="dark"?"☀️ 라이트":"🌙 다크"}
const esc=s=>String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const q=k=>new URLSearchParams(location.search).get(k);
let D,TEAMS;
function sty(t){const c=TC[t];return c?`style="--c1:${c[0]};--c2:${c[1]}"`:""}
function bd(t){return `<span class="bd" ${sty(t)}>${t==="키움"?"키":t.length>2?t[0]:t}</span>`}
function tl(t){return TEAMS.includes(t)?`<a class="clk" href="team.html?t=${encodeURIComponent(t)}">${bd(t)}${t}</a>`:esc(t)}
function pl(n,t){return `<a class="clk" href="player.html?n=${encodeURIComponent(n)}&t=${encodeURIComponent(t)}">${esc(n)}</a>`}
function gameRow(g){return `<div class="game"><div class="t ${g.as>g.hs?'win':''}">${tl(g.away)}</div><div class="m"><span class="score">${g.as} : ${g.hs}</span><br>${g.date} · ${g.place}</div><div class="t r ${g.hs>g.as?'win':''}">${tl(g.home)}</div></div>`}
function schRow(g){return `<div class="game"><div class="t">${tl(g.away)}</div><div class="m"><b>${g.stage}</b>${g.note?' · '+esc(g.note):''}<br>${g.date} ${g.time} · ${g.place}</div><div class="t r">${tl(g.home)}</div></div>`}
function table(h,rows,left=[0]){return `<div class="wrap"><table><thead><tr>${h.map((x,i)=>`<th class="${left.includes(i)?'l':''}">${x}</th>`).join("")}</tr></thead><tbody>${rows}</tbody></table></div>`}
function stRow(r,i){return `<tr ${sty(r[0])}><td style="border-left:4px solid var(--c1)">${i+1}</td><td class="l"><b>${tl(r[0])}</b></td><td>${r[1]}</td><td>${r[2]}</td><td>${r[3]}</td><td>${r[4]}</td><td>${r[5]}</td><td>${r[6]}</td><td>${r[7]}</td><td>${r[8]}</td></tr>`}
const ST_H=["순위","팀","경기","승","패","무","승률","게임차","최근10경기","연속"];
/* 선수 목록: 기록 TOP5에 오른 선수 */
function players(){const m={};Object.entries(D.leaders).forEach(([k,o])=>o.v.forEach((r,i)=>{const key=r[0]+"|"+r[1];(m[key]=m[key]||{n:r[0],t:r[1],g:o.g,recs:[]}).recs.push({k,u:o.u,rank:i+1,val:r[2]})}));return Object.values(m).sort((a,b)=>b.recs.length-a.recs.length)}
function head(active){
  $("hd").innerHTML=`<nav><div class="logo"><a href="index.html"><img src="logo-sm.png" alt="한국 프로야구 한눈에" class="logo-img"><span class="logo-tx">KBO<span>●</span>HUB</span></a></div><ul>${NAV.map(([h,n])=>`<li><a href="${h}" class="${h===active?'on':''}">${n}</a></li>`).join("")}</ul><button class="theme" id="themeBtn" type="button"></button></nav>`;
  $("themeBtn").onclick=()=>setTheme(themeNow()==="dark"?"light":"dark");setTheme(themeNow());
  $("ft").innerHTML=`마지막 갱신: ${esc(D.updated||'-')}<br>KBO HUB · 팬이 만든 비공식 정보 사이트 · 기록 출처 <a href="https://www.koreabaseball.com" target="_blank" rel="noopener">KBO</a>`;
}
function pageHead(title,sub,crumb){return `<div class="pagehead"><div>${crumb?`<div class="crumb">${crumb}</div>`:""}<h1>${title}</h1>${sub?`<p>${sub}</p>`:""}</div></div>`}
async function init(active,render){
  try{D=await (await fetch("data.json?t="+Date.now())).json()}
  catch(e){document.body.innerHTML='<p style="padding:24px">data.json을 불러오지 못했습니다. 파일로 직접 열었다면 <code>python -m http.server</code>로 실행하거나 GitHub Pages에 올려서 확인하세요.</p>';return}
  TEAMS=D.standings.map(r=>r[0]);head(active);render();
}
