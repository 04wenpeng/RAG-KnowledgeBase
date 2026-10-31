/* RAG 知识库 · 浏览器插件（只读） */
const $ = s => document.querySelector(s);
const DEFAULT_URL = 'http://127.0.0.1:8000';
let BASE = DEFAULT_URL;

function esc(s){
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}


/* 答案里的网址变可点链接（先 esc 再替换） */
function linkify(text){
  return text.replace(/(https?:\/\/[^\s<>"）)】]+)/g, function(u){
    return '<a href="' + u + '" target="_blank" rel="noopener">' + u + '</a>';
  });
}

/* ————— 设置：地址保存在 chrome.storage.local ————— */
function loadSettings(){
  return new Promise(resolve => {
    if(!chrome || !chrome.storage) return resolve(DEFAULT_URL);
    chrome.storage.local.get({ kbUrl: DEFAULT_URL }, v => resolve(v.kbUrl || DEFAULT_URL));
  });
}
function saveSettings(url){
  return new Promise(resolve => {
    if(!chrome || !chrome.storage) return resolve();
    chrome.storage.local.set({ kbUrl: url }, resolve);
  });
}

async function ping(url){
  const r = await fetch(url.replace(/\/+$/, '') + '/api/stats', { cache: 'no-store' });
  if(!r.ok) throw new Error('HTTP ' + r.status);
  return r.json();
}

async function refreshState(){
  const el = $('#state');
  el.className = 'hint';
  el.textContent = '检测中…';
  try{
    const d = await ping(BASE);
    el.className = 'hint ok';
    el.textContent = `已连接 · ${d.count} 块 / ${d.files.length} 文件`;
  }catch(e){
    el.className = 'hint bad';
    el.textContent = '连不上（服务没起？地址不对？）';
  }
}

/* ————— 查询 ————— */
async function ask(){
  const q = $('#q').value.trim();
  if(!q) return;
  const btn = $('#go');
  btn.disabled = true;
  btn.innerHTML = '<span class="spin"></span>';
  $('#out').innerHTML = '<p class="empty">检索中…</p>';

  const useLLM = $('#mode').checked;
  const k = Math.max(1, Math.min(10, parseInt($('#k').value, 10) || 4));

  try{
    const r = await fetch(BASE + '/api/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q, k, use_llm: useLLM })
    });
    if(!r.ok){
      const t = await r.text();
      throw new Error('HTTP ' + r.status + ' ' + t.slice(0, 120));
    }
    const d = await r.json();
    render(d);
  }catch(e){
    $('#out').innerHTML = `<div class="err">查询失败：${esc(e.message)}<br>
      检查：知识库那台机器开着吗？服务在跑吗？地址填对了吗？</div>`;
  }finally{
    btn.disabled = false;
    btn.textContent = '查询';
  }
}

function render(d){
  const parts = [];
  parts.push(`<div class="ans">${linkify(esc(d.answer || '（空）'))}</div>`);

  const modeLabel = { lmm: '大模型生成', llm: '大模型生成', extractive: '离线抽取',
                      no_hit: '未命中', empty: '空问题' }[d.mode] || (d.mode || '');
  const srcs = d.sources || [];
  parts.push(`<div class="meta">模式：${esc(modeLabel)} · 命中 ${srcs.length} 段</div>`);

  if(d.note) parts.push(`<div class="err">${esc(d.note)}</div>`);

  srcs.forEach(s => {
    const loc = s.page ? `第 ${s.page} 页` : '';
    parts.push(`<div class="src">
      <div class="top"><span>[${s.index}] ${esc(s.source)} ${esc(loc)}</span>
      <span>${(s.score || 0).toFixed(3)}</span></div>
      <div class="txt">${esc((s.snippet || '').slice(0, 160))}…</div>
    </div>`);
  });

  $('#out').innerHTML = parts.join('');
  $('#out').scrollTop = 0;
}

/* ————— 事件 ————— */
$('#go').onclick = ask;
$('#q').addEventListener('keydown', e => { if(e.key === 'Enter') ask(); });
$('#gear').onclick = () => {
  const box = $('#settings');
  box.classList.toggle('hidden');
  if(!box.classList.contains('hidden')){
    $('#url').value = BASE;
    refreshState();
  }
};
$('#save').onclick = async () => {
  const url = $('#url').value.trim() || DEFAULT_URL;
  BASE = url.replace(/\/+$/, '');
  await saveSettings(BASE);
  await refreshState();
};

/* ————— 启动 ————— */
(async function init(){
  BASE = (await loadSettings()).replace(/\/+$/, '');
  $('#url').value = BASE;
  refreshState();
  $('#q').focus();
})();
