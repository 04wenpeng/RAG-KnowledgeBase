# -*- coding: utf-8 -*-
"""网页界面：左右分区的应用外壳（左侧栏 + 右主区）。

    /         左侧：导航 + 索引状态 + 示例问题     右侧：对话
    /config   左侧：导航 + 配置列表 + 新增         右侧：选中配置的详情表单
"""

SHARED_CSS = """
  :root{
    --bg:#0b1020; --side:#0d1324; --panel:#141a2e; --panel2:#0f1526; --line:#26304d;
    --fg:#e8ecf7; --muted:#93a0c0; --dim:#6d7b9c;
    --accent:#5b8cff; --accent2:#22d3a6; --warn:#f5b544; --danger:#ff8f8f;
  }
  *{box-sizing:border-box}
  html,body{height:100%}
  body{margin:0;background:var(--bg);color:var(--fg);
       font:14.5px/1.6 "Segoe UI","Microsoft YaHei",system-ui,sans-serif;
       display:flex;overflow:hidden}
  a{color:var(--accent);text-decoration:none}

  /* ————— 左侧栏 ————— */
  .sidebar{flex:0 0 292px;width:292px;background:var(--side);border-right:1px solid var(--line);
           display:flex;flex-direction:column;min-height:0}
  .brand{padding:18px 18px 10px}
  .brand h1{margin:0;font-size:16px;letter-spacing:.3px;display:flex;align-items:center;gap:8px}
  .brand .logo{width:22px;height:22px;border-radius:7px;
               background:linear-gradient(135deg,var(--accent),#7a5cff);display:inline-block}
  .brand p{margin:4px 0 0;font-size:11.5px;color:var(--dim)}
  .nav{padding:8px 10px 4px}
  .nav a{display:flex;align-items:center;gap:9px;padding:9px 12px;border-radius:9px;
         color:var(--muted);font-size:13.5px}
  .nav a:hover{background:#141c33;color:#fff}
  .nav a.on{background:#1b2440;color:#fff}
  .nav .ico{width:16px;text-align:center;opacity:.9}
  .side-sec{padding:16px 18px 6px;font-size:11px;letter-spacing:1.2px;color:#5f6d8f;
            display:flex;align-items:center;justify-content:space-between}
  .side-sec .mini{font-size:11px;color:var(--accent);cursor:pointer;letter-spacing:0}
  .side-list{flex:1;min-height:0;overflow:auto;padding:0 10px 8px}
  .item{padding:9px 11px;border-radius:10px;cursor:pointer;border:1px solid transparent;margin-bottom:5px}
  .item:hover{background:#141c33}
  .item.on{background:#18213c;border-color:#2b3a63}
  .item .t{display:flex;align-items:center;gap:6px;font-size:13px;color:#e8ecf7}
  .item .s{font-size:11.5px;color:#7d8aab;margin-top:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .dot{width:6px;height:6px;border-radius:50%;background:#2b3a63;flex:0 0 auto}
  .dot.live{background:var(--accent2);box-shadow:0 0 6px rgba(34,211,166,.7)}
  .side-foot{border-top:1px solid var(--line);padding:11px 16px;font-size:11.5px;color:#7d8aab;
             display:flex;flex-direction:column;gap:5px;min-width:0}
  .side-foot div{display:flex;gap:6px;min-width:0;align-items:baseline}
  .side-foot div>span{flex:0 0 auto}
  .side-foot b{color:#cdd6ee;font-weight:600;overflow:hidden;text-overflow:ellipsis;
               white-space:nowrap;min-width:0}

  /* ————— 右侧主区 ————— */
  .main{flex:1;min-width:0;display:flex;flex-direction:column;min-height:0;
        background:radial-gradient(900px 420px at 15% -10%,#16203a 0%,var(--bg) 60%)}
  .main-head{flex:0 0 auto;padding:16px 24px;border-bottom:1px solid var(--line);
             display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap}
  .main-head h2{margin:0;font-size:15.5px;display:flex;align-items:center;gap:9px}
  .main-head .sub{font-size:12px;color:var(--dim);margin-top:2px}
  .main-body{flex:1;min-height:0;overflow:auto;padding:20px 24px 28px}

  /* ————— 通用控件 ————— */
  .btn{background:linear-gradient(135deg,var(--accent),#7a5cff);color:#fff;border:0;
       padding:9px 15px;border-radius:9px;font-size:13px;cursor:pointer;font-family:inherit}
  .btn:hover{filter:brightness(1.08)}
  .btn.ghost{background:transparent;border:1px solid var(--line);color:var(--fg)}
  .btn.ghost:hover{border-color:var(--accent);color:#fff}
  .btn.sm{padding:5px 10px;font-size:12px;border-radius:7px}
  .btn.danger{border:1px solid #5b2530;color:#ffb3b3;background:transparent}
  .btn.danger:hover{background:#3a1620}
  .btn:disabled{opacity:.5;cursor:default}
  input,select,textarea{background:var(--panel2);border:1px solid var(--line);color:var(--fg);
    padding:9px 11px;border-radius:9px;font-size:13.5px;outline:none;font-family:inherit;width:100%}
  input:focus,select:focus,textarea:focus{border-color:var(--accent);
    box-shadow:0 0 0 3px rgba(91,140,255,.14)}
  input:disabled,select:disabled{opacity:.5;cursor:not-allowed;background:#0c1122}
  label.f{display:block;font-size:12px;color:var(--muted);margin:14px 0 5px}
  .hintline{font-size:11.5px;color:var(--dim);margin-top:5px}
  .card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:18px 20px}
  .card h3{margin:0 0 4px;font-size:13px;letter-spacing:.6px;color:var(--muted);font-weight:600}
  .row{display:flex;gap:16px;flex-wrap:wrap}
  .row>div{flex:1;min-width:200px}
  .mono{font-family:Consolas,"Cascadia Mono",ui-monospace,monospace;font-size:12.5px}
  .muted{color:var(--muted)} .dim{color:var(--dim)}
  .tag{display:inline-block;font-size:11px;padding:1px 7px;border-radius:5px;background:#1b2440;color:#9fb0d6}
  .tag.live{background:#123c30;color:#5ee3b8}
  .tag.bad{background:#3a1620;color:#ff9b9b}
  .empty{color:var(--muted);font-size:13px;text-align:center;padding:40px 10px}
  .toast{position:fixed;left:50%;top:18px;transform:translateX(-50%);background:#1b2440;
         border:1px solid var(--line);color:#fff;padding:9px 16px;border-radius:9px;font-size:13px;
         opacity:0;transition:.22s;pointer-events:none;z-index:99;max-width:70vw}
  .toast.on{opacity:1}
  .banner{border-radius:11px;padding:10px 14px;font-size:12.5px;margin-bottom:16px;display:none}
  .banner.on{display:block}
  .banner.warn{background:#2a2110;border:1px solid #5b4a1f;color:#f2cf7d}
  .banner.ok{background:#10261f;border:1px solid #1f5b4a;color:#7fe3c0}
  .spin{display:inline-block;width:13px;height:13px;border:2px solid rgba(255,255,255,.3);
        border-top-color:#fff;border-radius:50%;animation:spin .8s linear infinite;vertical-align:-2px;margin-right:6px}
  @keyframes spin{to{transform:rotate(360deg)}}
  ::-webkit-scrollbar{width:9px;height:9px}
  ::-webkit-scrollbar-thumb{background:#243052;border-radius:5px}
  ::-webkit-scrollbar-track{background:transparent}
"""

TOAST = """
<div class="toast" id="toast"></div>
<script>
let _tt=null;
function toast(msg){
  const t=document.getElementById('toast'); t.textContent=msg; t.classList.add('on');
  clearTimeout(_tt); _tt=setTimeout(()=>t.classList.remove('on'),2800);
}
function esc(s){return (s==null?'':String(s)).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
async function api(url, opts){
  const r = await fetch(url, opts);
  const text = await r.text();
  let data=null; try{ data = JSON.parse(text); }catch(e){ data={error:text.slice(0,300)}; }
  if(!r.ok) throw new Error((data&&data.error)||('HTTP '+r.status));
  return data;
}
// 页面脚本出错时别静默失败：直接在页面上报出来，省得"卡在加载中"看不出原因
window.addEventListener('error', function(ev){
  try{
    const el = document.getElementById('toast');
    if(el){ el.textContent = '页面脚本出错：' + (ev.message || '未知错误'); el.classList.add('on'); }
    console.error(ev.error || ev.message);
  }catch(_){}
});
</script>
"""


# ============================================================ 问答页
PAGE_LOGIN = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>访问口令 · RAG 知识库</title><style>
  :root{
    --bg:#f6f7f9; --line:#e6e8ec; --fg:#1f2328; --muted:#6b7280; --dim:#9aa1ab;
    --accent:#4d6bfe; --accent-h:#3d5bf0; --danger:#d92d20;
  }
  *{box-sizing:border-box}
  html,body{height:100%}
  body{margin:0;background:var(--bg);color:var(--fg);display:flex;align-items:center;
       justify-content:center;font:14px/1.65 "Segoe UI","Microsoft YaHei",system-ui,sans-serif}
  .card{width:min(400px,92vw);background:#fff;border:1px solid var(--line);border-radius:14px;
        padding:30px 30px 24px;box-shadow:0 14px 40px rgba(16,24,40,.08)}
  .brand{display:flex;align-items:center;gap:9px;margin-bottom:6px}
  .brand .logo{width:22px;height:22px;border-radius:6px;background:var(--accent)}
  .brand b{font-size:15px}
  h1{margin:14px 0 6px;font-size:17px;font-weight:600}
  p.tip{margin:0 0 18px;color:var(--muted);font-size:12.5px;line-height:1.8}
  input{width:100%;border:1px solid var(--line);border-radius:9px;padding:11px 13px;
        font-size:14px;font-family:inherit;outline:none;background:#fafbfc;color:var(--fg)}
  input:focus{border-color:var(--accent);background:#fff;box-shadow:0 0 0 3px rgba(77,107,254,.12)}
  button{width:100%;margin-top:12px;border:0;border-radius:9px;padding:11px;font-size:14px;
         background:var(--accent);color:#fff;cursor:pointer;font-family:inherit}
  button:hover{background:var(--accent-h)}
  .err{margin-top:10px;font-size:12.5px;color:var(--danger);display:none}
  .err.on{display:block}
  .foot{margin-top:16px;font-size:11.5px;color:var(--dim);text-align:center;line-height:1.7}

  /* 右上角身份与登录 */
  .who-wrap{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
  .who-badge{font-size:12px;padding:3px 10px;border-radius:999px;border:1px solid var(--line);
             color:var(--muted);background:#fff;white-space:nowrap}
  .who-badge.on{color:#0b7a44;background:#e9f8f0;border-color:#bfe8d2;font-weight:600}
  .who-badge.local{color:#3543a8;background:#eef2ff;border-color:#dbe3ff;font-weight:600}
  .role-note{display:none;margin:0 0 12px;padding:8px 12px;border-radius:9px;
             background:#f3f6ff;border:1px solid #dbe3ff;color:#3543a8;font-size:12.5px}
  .role-note.on{display:block}

  /* 访客（未登录）隐藏管理入口 */
  .visitor #addFileBtn,.visitor #hintBox,.visitor .fdel{display:none!important}
  .visitor .toolbar .btn,.visitor #reindexBtn,.visitor #batchbar,
  .visitor .acts .btn.link.del,.visitor #clearSkips{display:none!important}
  .visitor #aSave,.visitor #aCard{display:none!important}
  .visitor .tablebox th:first-child,.visitor .tablebox td:first-child{display:none!important}
</style></head>
<body>
  <form class="card" method="post" action="/login">
    <div class="brand"><span class="logo"></span><b>RAG 知识库</b></div>
    <h1>管理口令</h1>
    <p class="tip">提问、看历史、浏览资料<b>不需要口令</b>，直接回问答页就能用。<br>
      这里只是进入管理功能（改 API 配置、重建索引、删除资料）的入口，
      口令由知识库的主人提供。</p>
    <input name="password" type="password" placeholder="请输入访问口令" autofocus autocomplete="current-password">
    <button type="submit">进入</button>
    <div class="err" id="err">__ERROR__</div>
    <div class="foot"><a href="/" style="color:var(--accent)">← 不用口令，直接去问答</a><br>
      口令在 7 天内只需输入一次</div>
  </form>
</body></html>"""


PAGE_ASK = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>知识库问答 · RAG</title><style>
  :root{
    --bg:#f6f7f9; --card:#fff; --line:#e6e8ec; --line2:#eff1f4;
    --fg:#1f2328; --muted:#6b7280; --dim:#9aa1ab;
    --accent:#4d6bfe; --accent-h:#3d5bf0; --ok:#12a150; --warn:#b45309; --danger:#d92d20;
  }
  *{box-sizing:border-box}
  html,body{height:100%}
  body{margin:0;background:var(--bg);color:var(--fg);display:flex;overflow:hidden;
       font:14px/1.65 "Segoe UI","Microsoft YaHei",system-ui,-apple-system,sans-serif}
  a{color:var(--accent);text-decoration:none}
  .mono{font-family:Consolas,"Cascadia Mono",ui-monospace,monospace;font-size:12.5px}
  .btn{border:1px solid transparent;border-radius:8px;padding:8px 15px;font-size:13.5px;
       cursor:pointer;background:var(--accent);color:#fff;font-family:inherit;white-space:nowrap}
  .btn:hover{background:var(--accent-h)}
  .btn.ghost{background:#fff;border-color:var(--line);color:var(--fg)}
  .btn.ghost:hover{background:#f7f8fa;border-color:#d6dae2}
  .btn.sm{padding:5px 11px;font-size:12.5px;border-radius:7px}
  .btn:disabled{opacity:.55;cursor:not-allowed}

  /* ——— 侧栏 ——— */
  .sidebar{flex:0 0 240px;width:240px;background:#fff;border-right:1px solid var(--line);
           display:flex;flex-direction:column;min-height:0}
  .brand{padding:18px 20px 12px;display:flex;align-items:center;gap:9px}
  .brand .logo{width:22px;height:22px;border-radius:6px;background:var(--accent);flex:0 0 auto}
  .brand b{font-size:15px}
  .nav{padding:0 12px;display:flex;flex-direction:column;gap:2px}
  .nav a{display:flex;align-items:center;gap:9px;padding:8px 12px;border-radius:8px;
         color:#374151;font-size:13.5px}
  .nav a:hover{background:#f3f4f6}
  .nav a.on{background:#eef2ff;color:var(--accent);font-weight:600}
  .nav .ico{width:15px;text-align:center}
  .newchat{padding:12px 12px 4px}
  .newchat .btn{width:100%;padding:8px 12px;font-size:13px}
  .side-sec{padding:12px 18px 6px;font-size:11px;letter-spacing:1.1px;color:#9aa1ab;
            display:flex;align-items:center;justify-content:space-between}
  .side-sec .mini{font-size:11.5px;color:var(--accent);cursor:pointer;letter-spacing:0}

  .chatlist{flex:1;min-height:60px;overflow:auto;padding:0 10px 6px}
  .citem{position:relative;padding:7px 10px;border-radius:8px;cursor:pointer;margin-bottom:2px}
  .citem:hover{background:#f5f6f8}
  .citem.on{background:#eef2ff}
  .citem .ct{font-size:12.5px;color:#374151;overflow:hidden;text-overflow:ellipsis;
             white-space:nowrap;padding-right:16px}
  .citem.on .ct{color:var(--accent);font-weight:600}
  .citem .cs{font-size:10.5px;color:#9aa1ab;margin-top:1px}
  .cdel{position:absolute;right:5px;top:7px;border:0;background:none;color:#c7ccd4;
        font-size:14px;line-height:1;cursor:pointer;padding:1px 4px;border-radius:4px;opacity:0}
  .citem:hover .cdel{opacity:1}
  .cdel:hover{color:#d92d20;background:#fef2f2}
  .nochat{padding:10px 8px;font-size:12px;color:#9aa1ab;line-height:1.8}

  .files{max-height:118px;overflow:auto;padding:0 10px}

  #hintBox{padding:2px 10px 6px}

  #hintBox .drop-hint{margin:0}
  .fitem{display:flex;align-items:center;gap:7px;padding:4px 9px;border-radius:7px;
         font-size:12px;color:#4b5563}
  .fitem:hover{background:#f5f6f8}
  .fitem .nm{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .fitem .sz,.fitem .ico{color:var(--dim);font-size:11px;flex:0 0 auto}
  .fdel{flex:0 0 auto;border:0;background:none;color:#c7ccd4;font-size:14px;line-height:1;
        cursor:pointer;padding:1px 4px;border-radius:4px;opacity:.45;font-family:inherit}
  .fitem:hover .fdel{opacity:1}
  .fdel:hover{color:#d92d20;background:#fef2f2}
  .drop-hint{margin:6px 10px 6px;padding:8px 10px;border:1px dashed #d6dae2;border-radius:8px;
             font-size:11px;color:var(--muted);text-align:center;cursor:pointer;line-height:1.7}
  .drop-hint:hover{border-color:var(--accent);color:var(--accent)}
  .mini-btns{display:flex;gap:5px;justify-content:center;margin-top:6px;flex-wrap:wrap}
  .mini-btn{font-size:10.5px;border:1px solid var(--line);border-radius:6px;padding:1px 7px;
            color:var(--muted);cursor:pointer;background:#fff;font-family:inherit}
  .mini-btn:hover{color:var(--accent);border-color:var(--accent)}

  .side-foot{margin-top:auto;border-top:1px solid var(--line);padding:10px 16px;
             font-size:11.5px;color:var(--muted);display:flex;flex-direction:column;gap:4px}
  .side-foot .row{display:flex;justify-content:space-between;gap:8px}
  .side-foot b{color:var(--fg);font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}

  /* ——— 主区 ——— */
  .main{flex:1;min-width:0;display:flex;flex-direction:column;min-height:0}
  .main-head{flex:0 0 auto;padding:14px 26px;background:#fff;border-bottom:1px solid var(--line);
             display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap}
  .main-head h2{margin:0;font-size:16.5px;font-weight:600;overflow:hidden;
                text-overflow:ellipsis;white-space:nowrap;max-width:60vw}
  .main-head .sub{font-size:12px;color:var(--muted);margin-top:2px}
  .chat{flex:1;min-height:0;overflow:auto;padding:22px 26px 8px}
  .list{max-width:860px;margin:0 auto}

  /* 消息：AI 靠左，你的提问靠右 */
  .msg{display:flex;gap:10px;margin-bottom:16px}
  .who{flex:0 0 26px;width:26px;height:26px;border-radius:7px;background:#eef2ff;color:var(--accent);
       display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:600}
  .msg.me{flex-direction:row-reverse}
  .msg.me .who{background:#e8f5ee;color:var(--ok)}
  .body{flex:1;min-width:0}
  .msg.me .body{flex:0 1 auto;max-width:80%;display:flex;flex-direction:column;align-items:flex-end}
  .who-name{font-size:11.5px;color:var(--dim);margin-bottom:4px}
  .msg.me .who-name{display:none}
  .bubble{background:#fff;border:1px solid var(--line);border-radius:12px;
          border-top-left-radius:4px;padding:12px 15px;
          white-space:pre-wrap;word-break:break-word;font-size:14px;line-height:1.75;max-width:100%}
  .msg.me .bubble{background:#4d6bfe;border-color:#4d6bfe;color:#fff;
                  border-top-left-radius:12px;border-top-right-radius:4px}
  .meta-line{margin-top:6px;font-size:11.5px;color:var(--dim)}
  .note{margin-top:8px;font-size:12.5px;color:var(--warn);background:#fffbeb;
        border:1px solid #fde68a;border-radius:8px;padding:7px 10px}
  .srcs{margin-top:8px;display:flex;flex-direction:column;gap:7px}
  /* 参考资料默认收起，点标题（带箭头）展开 */
  .srcbox{margin-top:8px}
  .srcbox>summary{cursor:pointer;font-size:12px;color:var(--muted);list-style:none;
                  display:inline-flex;align-items:center;gap:6px;padding:4px 9px;
                  border:1px solid var(--line);border-radius:7px;background:#fff;
                  user-select:none;font-family:inherit}
  .srcbox>summary::-webkit-details-marker{display:none}
  .srcbox>summary::before{content:'▸';font-size:10px;display:inline-block;
                          transition:transform .15s;color:var(--dim)}
  .srcbox[open]>summary::before{transform:rotate(90deg)}
  .srcbox>summary:hover{border-color:var(--accent);color:var(--accent)}
  .srcbox[open]>summary{color:var(--accent);border-color:#dbe3ff;background:#f7f9ff}
  .src{background:#fff;border:1px solid var(--line);border-radius:9px;padding:9px 12px}
  .src .top{display:flex;justify-content:space-between;gap:10px;font-size:11.5px;color:var(--muted)}
  .src .txt{margin-top:4px;font-size:12.5px;color:#4b5563;line-height:1.7}
  .bar{height:3px;border-radius:2px;background:#eef1f5;margin-top:6px;overflow:hidden}
  .bar i{display:block;height:100%;background:linear-gradient(90deg,#7fa2ff,var(--accent))}

  /* 欢迎区示例 */
  .welcome .chips{display:flex;gap:7px;flex-wrap:wrap;margin-top:10px}
  .wchip{font-size:12px;padding:4px 11px;border-radius:999px;border:1px solid var(--line);
         background:#fff;color:#4b5563;cursor:pointer}
  .wchip:hover{border-color:var(--accent);color:var(--accent)}

  /* 输入区 */
  .composer{flex:0 0 auto;background:#fff;border-top:1px solid var(--line);padding:12px 26px 14px}
  .composer .box{max-width:860px;margin:0 auto;display:flex;gap:10px;align-items:center}
  .composer input{flex:1;border:1px solid var(--line);border-radius:10px;padding:11px 14px;
                  font-size:14px;font-family:inherit;outline:none;background:#fafbfc;color:var(--fg);
                  width:auto}
  .composer input:focus{border-color:var(--accent);background:#fff;
                        box-shadow:0 0 0 3px rgba(77,107,254,.12)}
  .composer .btn{padding:11px 20px;border-radius:10px;font-size:14px}
  .opts{max-width:860px;margin:8px auto 0;display:flex;gap:18px;align-items:center;
        color:var(--muted);font-size:12px;flex-wrap:wrap}
  .opts input[type=range]{width:110px;vertical-align:middle}
  .opts b{color:var(--fg)}

  #dropOverlay{position:fixed;inset:0;z-index:200;display:none;align-items:center;justify-content:center;
               background:rgba(246,247,249,.86);backdrop-filter:blur(3px)}
  #dropOverlay.on{display:flex}
  #dropOverlay .box{border:2px dashed var(--accent);border-radius:16px;padding:44px 60px;
                    text-align:center;background:#fff;box-shadow:0 18px 48px rgba(16,24,40,.12)}
  #dropOverlay .big{font-size:18px;font-weight:600;margin-bottom:6px}
  #dropOverlay .small{font-size:12.5px;color:var(--muted)}

  .toast{position:fixed;left:50%;top:24px;transform:translateX(-50%);background:#1f2328;color:#fff;
         padding:9px 16px;border-radius:8px;font-size:13px;opacity:0;transition:.2s;
         pointer-events:none;z-index:99;max-width:70vw;box-shadow:0 8px 24px rgba(16,24,40,.18)}
  .toast.on{opacity:1}
  .spin{display:inline-block;width:12px;height:12px;border:2px solid rgba(255,255,255,.4);
        border-top-color:#fff;border-radius:50%;animation:sp .8s linear infinite;
        vertical-align:-2px;margin-right:6px}
  .spin.dark{border-color:rgba(31,35,40,.2);border-top-color:var(--accent)}
  @keyframes sp{to{transform:rotate(360deg)}}
  ::-webkit-scrollbar{width:9px;height:9px}
  ::-webkit-scrollbar-thumb{background:#d8dce3;border-radius:5px}

  /* 右上角身份与登录 */
  .who-wrap{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
  .who-badge{font-size:12px;padding:3px 10px;border-radius:999px;border:1px solid var(--line);
             color:var(--muted);background:#fff;white-space:nowrap}
  .who-badge.on{color:#0b7a44;background:#e9f8f0;border-color:#bfe8d2;font-weight:600}
  .who-badge.local{color:#3543a8;background:#eef2ff;border-color:#dbe3ff;font-weight:600}
  .role-note{display:none;margin:0 0 12px;padding:8px 12px;border-radius:9px;
             background:#f3f6ff;border:1px solid #dbe3ff;color:#3543a8;font-size:12.5px}
  .role-note.on{display:block}

  /* 访客（未登录）隐藏管理入口 */
  .visitor #addFileBtn,.visitor #hintBox,.visitor .fdel{display:none!important}
  .visitor .toolbar .btn,.visitor #reindexBtn,.visitor #batchbar,
  .visitor .acts .btn.link.del,.visitor #clearSkips{display:none!important}
  .visitor #aSave,.visitor #aCard{display:none!important}
  .visitor .tablebox th:first-child,.visitor .tablebox td:first-child{display:none!important}
</style></head>
<body>
<aside class="sidebar">
  <div class="brand"><span class="logo"></span><b>RAG 知识库</b></div>
  <nav class="nav">
    <a href="/" class="on"><span class="ico">◈</span>知识库问答</a>
    <a href="/library"><span class="ico">▤</span>资料库</a>
    <a href="/config"><span class="ico">◎</span>API 配置</a>
  </nav>

  <div class="newchat"><button class="btn" id="newChatBtn">＋ 新建对话</button></div>

  <div class="side-sec">对 话</div>
  <div class="chatlist" id="chatList">加载中…</div>

  <div class="side-sec">资 料 <span class="mini" id="addFileBtn">+ 添加</span></div>
  <div class="files" id="fileList"></div>

  <div id="hintBox"></div>

  <div class="side-foot">
    <div class="row"><span>索引</span><b id="fIdx">-</b></div>
    <div class="row"><span>嵌入</span><b id="fEmb">-</b></div>
    <div class="row"><span>生成</span><b id="fLlm">-</b></div>

  </div>
</aside>

<main class="main">
  <div class="main-head">
    <div>
      <h2 id="chatTitle">知识库问答</h2>
      <div class="sub" id="chatSub">基于 data/ 里的文档回答，每条答案都标注出处</div>
    </div>
    <div class="who-wrap">
      <span class="who-badge" id="whoBadge">…</span>
      <a class="btn ghost sm" href="/config" id="cfgLink">API 配置 →</a>
      <button class="btn ghost sm" id="authBtn">登录</button>
    </div>
  </div>

  <div class="chat" id="chat"><div class="list" id="list"></div></div>

  <div class="composer">
    <div class="box">
      <input id="q" type="text" placeholder="输入问题，回车发送…" autocomplete="off">
      <button class="btn" id="go">发送</button>
    </div>
    <div class="opts">
      <label>召回数量 <input id="k" type="range" min="1" max="10" value="4"><b id="kv">4</b></label>
      <label><input id="usellm" type="checkbox" checked> 用大模型生成</label>
      <span id="hint"></span>
    </div>
  </div>
</main>

<input type="file" id="filePicker" multiple style="display:none"
       accept=".pdf,.docx,.txt,.md,.markdown,.csv,.xlsx,.json">
<input type="file" id="folderPicker" webkitdirectory directory multiple style="display:none">
<div id="dropOverlay">
  <div class="box">
    <div class="big">松手即可加入知识库</div>
    <div class="small">支持 pdf / docx / txt / md / csv / xlsx / json，可一次拖多个</div>
  </div>
</div>

__TOAST__
<script>
const $ = s => document.querySelector(s);
const SAMPLES = ["什么是 RAG？", "RAG 的优势和挑战", "什么是向量数据库？",
                 "chunk_size 默认值是多少", "怎么调召回数量", "检索不准怎么办"];
let CHATS = [];
let ACTIVE = null;      // 当前对话 id
let CHAT = null;        // 当前对话完整数据

$('#k').oninput = e => $('#kv').textContent = e.target.value;

function shortEmb(s){
  if(!s) return '-';
  if(s.indexOf('哈希') >= 0 || s.indexOf('hashing') >= 0) return '离线哈希向量';
  if(s.indexOf('DashScope') >= 0 || s.indexOf('百炼') >= 0) return '百炼嵌入';
  if(s.indexOf('Ollama') >= 0) return '本地 Ollama';
  return s;
}
function modeLabel(m){
  return {llm:'大模型生成', extractive:'离线抽取式', no_hit:'未命中'}[m] || (m || '');
}
function esc2(s){ return esc(s); }



/* 答案里的网址变成可点链接（先 esc 再替换，避免 XSS） */
function linkify(text){
  return text.replace(/(https?:\/\/[^\s<>"）)】]+)/g, function(u){
    return '<a href="' + u + '" target="_blank" rel="noopener">' + u + '</a>';
  });
}

/* ———— 身份：本机管理员 / 管理员 / 访客 ———— */
async function initAuth(){
  let d = {admin:true, local:true, label:'本机管理员'};
  try{ d = await api('/api/whoami'); }catch(e){}
  window.IS_ADMIN = !!d.admin;
  const badge = $('#whoBadge'), btn = $('#authBtn');
  if(badge){
    badge.textContent = d.admin ? (d.local ? '本机管理员' : '管理员') : '访客';
    badge.className = 'who-badge ' + (d.admin ? (d.local ? 'local' : 'on') : '');
  }
  if(btn){
    if(d.admin){
      btn.textContent = '退出登录';
      btn.onclick = () => location.href = '/logout';
    }else{
      btn.textContent = '管理员登录';
      btn.onclick = () => location.href = '/login?next=' +
        encodeURIComponent(location.pathname + location.search);
    }
  }
  if(!d.admin) document.body.classList.add('visitor');
  return d;
}

/* —————————————— 状态 —————————————— */
async function loadStats(){
  try{
    const d = await api('/api/stats');
    $('#fIdx').textContent = `${d.count} 块 / ${d.files.length} 文件`;
    $('#fEmb').textContent = shortEmb(d.embedder);
    $('#fLlm').textContent = d.llm || '离线抽取式';
    if(d.embedding_warning || d.embedder_mismatch){
      $('#hint').innerHTML = '<a href="/config">嵌入模型与索引不一致，去配置页处理 →</a>';
    }else if(!d.llm){
      $('#hint').innerHTML = '<a href="/config">还没配置大模型，点这里添加 →</a>';
    }else{ $('#hint').textContent = ''; }
  }catch(e){}
}

/* —————————————— 对话列表 —————————————— */
async function loadChats(){
  try{
    const d = await api('/api/chats');
    CHATS = d.chats || [];
    renderChatList();
  }catch(e){}
}

function renderChatList(){
  const box = $('#chatList');
  if(!CHATS.length){
    box.innerHTML = '<div class="nochat">还没有对话<br>直接提问，或点上面「新建对话」</div>';
    return;
  }
  box.innerHTML = CHATS.map(c => `
    <div class="citem${ACTIVE === c.id ? ' on' : ''}" data-id="${c.id}">
      <div class="ct" title="${esc(c.title)}">${esc(c.title)}</div>
      <div class="cs">${esc(String(c.updated_at || '').slice(5, 16))} · ${c.count} 条</div>
      <button class="cdel" data-del="${c.id}" title="删除这个对话">×</button>
    </div>`).join('');
}

$('#chatList').addEventListener('click', async e => {
  const del = e.target.closest('.cdel');
  if(del){
    e.stopPropagation();
    const id = del.dataset.del;
    if(!confirm('删除这个对话？删除后不可恢复。')) return;
    try{
      await api('/api/chats/' + id, {method:'DELETE'});
      if(ACTIVE === id){ ACTIVE = null; CHAT = null; clearChat(); showWelcome(); }
      await loadChats();
      toast('已删除对话');
    }catch(err){ toast('删除失败：' + err.message); }
    return;
  }
  const item = e.target.closest('.citem');
  if(item) openChat(item.dataset.id);
});

$('#chatList').addEventListener('dblclick', async e => {
  const ct = e.target.closest('.ct'); if(!ct) return;
  const item = ct.closest('.citem'); const id = item.dataset.id;
  const cur = CHATS.find(c => c.id === id);
  const name = prompt('重命名对话：', cur ? cur.title : '');
  if(!name || !name.trim()) return;
  try{
    await api('/api/chats/' + id, {method:'PUT',
      headers:{'Content-Type':'application/json'}, body: JSON.stringify({title: name.trim()})});
    if(ACTIVE === id) $('#chatTitle').textContent = name.trim();
    await loadChats();
  }catch(err){ toast('重命名失败：' + err.message); }
});

/* —————————————— 渲染消息 —————————————— */
function srcsHtml(sources){
  if(!sources || !sources.length) return '';
  // 默认收起：<details> 不用写 JS，箭头和展开状态交给浏览器
  const body = sources.map(s => {
    const loc = s.page ? `第 ${s.page} 页` : (s.row != null ? `第 ${s.row + 1} 行` : (s.sheet || ''));
    const w = Math.min(100, Math.round((s.score || 0) * 100));
    return `<div class="src">
      <div class="top"><span>[${s.index}] ${esc(s.source)} ${loc ? ('· ' + esc(String(loc))) : ''}</span>
      <span>相关度 ${(s.score || 0).toFixed(3)}</span></div>
      <div class="txt">${esc(s.snippet)}…</div>
      <div class="bar"><i style="width:${w}%"></i></div></div>`;
  }).join('');
  return `<details class="srcbox"><summary>参考资料 · ${sources.length} 段</summary>
    <div class="srcs">${body}</div></details>`;
}

function aiHtml(m, pending){
  if(pending) return '<div class="bubble"><span class="spin dark"></span>检索中…</div>';
  let html = `<div class="bubble">${linkify(esc(m.content))}</div>`;
  if(m.mode) html += `<div class="meta-line">模式：${esc(modeLabel(m.mode))}</div>`;
  if(m.note) html += `<div class="note">${esc(m.note)}</div>`;
  html += srcsHtml(m.sources);
  return html;
}

function addMsgEl(m, opts){
  opts = opts || {};
  const wrap = document.createElement('div');
  const isMe = m.role === 'me';
  wrap.className = 'msg' + (isMe ? ' me' : '');
  wrap.innerHTML = `<div class="who">${isMe ? '你' : 'AI'}</div>
    <div class="body"><div class="who-name">${isMe ? '你' : '知识库'}</div>
    ${isMe ? `<div class="bubble">${linkify(esc(m.content))}</div>` : aiHtml(m, opts.pending)}</div>`;
  $('#list').appendChild(wrap);
  $('#chat').scrollTop = $('#chat').scrollHeight;
  return wrap;
}

function clearChat(){ $('#list').innerHTML = ''; }

function showWelcome(){
  $('#chatTitle').textContent = '知识库问答';
  $('#chatSub').textContent = '基于 data/ 里的文档回答，每条答案都标注出处';
  const wrap = document.createElement('div');
  wrap.className = 'msg welcome';
  wrap.innerHTML = `<div class="who">AI</div>
    <div class="body"><div class="who-name">知识库</div>
      <div class="bubble">你好，我是这个知识库的问答助手。左侧可以直接点历史对话，也可以在下面提问；
        把文件拖进窗口就能直接入库，回答会标注出处（文件名 + 页码）。
        <div class="chips">${SAMPLES.map(s => `<span class="wchip">${esc(s)}</span>`).join('')}</div>
      </div>
    </div>`;
  $('#list').appendChild(wrap);
  wrap.querySelectorAll('.wchip').forEach(el => {
    el.onclick = () => { $('#q').value = el.textContent; ask(); };
  });
}

/* —————————————— 会话操作 —————————————— */
async function newChat(silent){
  try{
    const r = await api('/api/chats', {method:'POST',
      headers:{'Content-Type':'application/json'}, body:'{}'});
    ACTIVE = r.chat.id;
    CHAT = r.chat;
    clearChat();
    showWelcome();
    await loadChats();
    if(!silent) toast('已新建对话');
    $('#q').focus();
  }catch(e){ toast('新建失败：' + e.message); }
}

async function openChat(id){
  try{
    const d = await api('/api/chats/' + id);
    ACTIVE = id;
    CHAT = d.chat;
    clearChat();
    const msgs = d.chat.messages || [];
    if(msgs.length) msgs.forEach(m => addMsgEl(m));
    else showWelcome();
    $('#chatTitle').textContent = d.chat.title || '知识库问答';
    $('#chatSub').textContent = `${msgs.length} 条消息 · 自动保存`;
    await loadChats();
    $('#chat').scrollTop = $('#chat').scrollHeight;
  }catch(e){ toast('打开失败：' + e.message); }
}

async function persist(m){
  if(!ACTIVE) return;
  try{
    await api('/api/chats/' + ACTIVE + '/messages', {method:'POST',
      headers:{'Content-Type':'application/json'}, body: JSON.stringify(m)});
    await loadChats();
  }catch(e){}
}

$('#newChatBtn').onclick = () => newChat(false);

/* —————————————— 提问 —————————————— */
async function ask(){
  const q = $('#q').value.trim();
  if(!q) return;
  if(!ACTIVE) await newChat(true);

  const btn = $('#go'); btn.disabled = true; btn.innerHTML = '<span class="spin"></span>';
  addMsgEl({role:'me', content:q});
  await persist({role:'me', content:q});
  $('#q').value = '';

  const pending = addMsgEl({role:'ai', content:''}, {pending:true});
  try{
    const d = await api('/api/ask', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({question:q, k:parseInt($('#k').value, 10), use_llm:$('#usellm').checked})
    });
    const msg = {
      role:'ai', content:d.answer, mode:d.mode, note:d.note || '',
      sources:(d.sources || []).map(s => ({
        index:s.index, source:s.source, page:s.page, row:s.row, sheet:s.sheet,
        score:s.score, snippet:s.snippet
      }))
    };
    pending.querySelector('.body').innerHTML =
      `<div class="who-name">知识库</div>${aiHtml(msg)}`;
    await persist(msg);
    if(ACTIVE){
      const cur = CHATS.find(c => c.id === ACTIVE);
      if(cur) $('#chatTitle').textContent = cur.title;
      $('#chatSub').textContent = `${(CHAT && CHAT.messages ? CHAT.messages.length : 0) + 2} 条消息 · 自动保存`;
    }
  }catch(e){
    pending.querySelector('.body').innerHTML =
      `<div class="who-name">知识库</div><div class="bubble">请求失败：${esc(String(e.message || e))}</div>`;
  }finally{
    btn.disabled = false; btn.textContent = '发送';
    $('#chat').scrollTop = $('#chat').scrollHeight;
  }
}

$('#go').onclick = ask;
$('#q').addEventListener('keydown', e => { if(e.key === 'Enter') ask(); });

/* —————————————— 资料 —————————————— */
function fmtSize(kb){
  return kb >= 1024 ? (kb/1024).toFixed(1)+' MB' : Math.max(1, Math.round(kb))+' KB';
}

const HINT_HTML = `<div class="drop-hint" id="dropHint">
    拖文件或整个文件夹到这里
    <div class="mini-btns">
      <button class="mini-btn" id="pickFiles">选文件</button>
      <button class="mini-btn" id="pickFolder">选文件夹</button>
      <button class="mini-btn" id="pickPath">填路径</button>
    </div>
  </div>`;

async function renderFiles(){
  try{
    const d = await api('/api/files');
    const box = $('#fileList');
    if(!d.files.length){
      box.innerHTML = '';
      $('#hintBox').innerHTML = HINT_HTML;
      bindHints(); return;
    }
    box.innerHTML = d.files.map(f => `
      <div class="fitem" title="${esc(f.name)} · ${fmtSize(f.kb)} · ${esc(f.mtime)}">
        <span class="ico">▤</span>
        <span class="nm">${esc(f.name)}</span>
        <span class="sz">${fmtSize(f.kb)}</span>
        <button class="fdel" data-name="${esc(f.name)}" title="从知识库移除">×</button>
      </div>`).join('');
    $('#hintBox').innerHTML = HINT_HTML;
    bindHints();
  }catch(e){}
}

$('#fileList').addEventListener('click', async e => {
  const b = e.target.closest('.fdel'); if(!b) return;
  e.stopPropagation();
  const name = b.dataset.name;
  if(!confirm('从知识库移除「' + name + '」？文件会从 data 目录删除，索引会重建。')) return;
  b.disabled = true; b.textContent = '…';
  try{
    const r = await api('/api/files?name=' + encodeURIComponent(name), {method:'DELETE'});
    toast('已移除：' + name + '（现有 ' + r.count + ' 块）');
    await loadStats(); await renderFiles();
  }catch(err){
    toast('移除失败：' + err.message);
    b.disabled = false; b.textContent = '×';
  }
});

function bindHints(){
  const pf = $('#pickFiles'), pd = $('#pickFolder'), pp = $('#pickPath'), h = $('#dropHint');
  if(pf) pf.onclick = e => { e.stopPropagation(); $('#filePicker').click(); };
  if(pd) pd.onclick = e => { e.stopPropagation(); $('#folderPicker').click(); };
  if(pp) pp.onclick = e => { e.stopPropagation(); askFolderPath(); };
  if(h) h.onclick = () => $('#filePicker').click();
}

$('#addFileBtn').onclick = () => $('#filePicker').click();

$('#filePicker').addEventListener('change', e => {
  const files = [...e.target.files]; e.target.value = '';
  if(files.length) uploadFiles(files.map(f => ({file:f, rel:f.name})));
});
$('#folderPicker').addEventListener('change', e => {
  const files = [...e.target.files]; e.target.value = '';
  if(files.length) uploadFiles(files.map(f => ({file:f, rel:f.webkitRelativePath || f.name})));
});

async function askFolderPath(){
  const p = prompt('输入本机文件夹的完整路径（不复制文件，直接读原位置）。例如：D:/资料/产品文档');
  if(!p || !p.trim()) return;
  const pend = addMsgEl({role:'ai', content:''}, {pending:true});
  pend.querySelector('.body').innerHTML =
    '<div class="who-name">知识库</div><div class="bubble"><span class="spin dark"></span>正在扫描并入库…</div>';
  try{
    const r = await api('/api/import_folder', {method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({path: p.trim(), copy:false})});
    const skip = r.skipped_count ? `（跳过 ${r.skipped_count} 个：${(r.skipped || []).join('；')}）` : '';
    pend.querySelector('.body').innerHTML = `<div class="who-name">知识库</div>
      <div class="bubble">已导入文件夹「${esc(r.folder)}」：${r.file_count} 个文件，切分出 ${r.chunks} 个文本块。${esc(skip)}</div>`;
    toast(`已导入 ${r.file_count} 个文件`);
  }catch(err){
    pend.querySelector('.body').innerHTML =
      `<div class="who-name">知识库</div><div class="bubble">导入失败：${esc(err.message)}</div>`;
  }
  await loadStats(); await renderFiles();
}

async function uploadFiles(items){
  if(items.length && items[0] instanceof File) items = items.map(f => ({file:f, rel:f.name}));
  const total = items.length;
  let done = 0, okCount = 0;
  const fails = [];
  const batch = total > 1;
  const pend = addMsgEl({role:'ai', content:''}, {pending:true});
  const bubble = pend.querySelector('.bubble');

  for(const it of items){
    try{
      const url = '/api/upload?name=' + encodeURIComponent(it.rel) + (batch ? '&index=0' : '');
      await api(url, {method:'POST', body:it.file});
      okCount++;
    }catch(err){ fails.push(it.rel + '：' + err.message); }
    done++;
    if(bubble) bubble.innerHTML = `<span class="spin dark"></span>正在上传 ${done}/${total}…`;
  }

  if(batch && okCount){
    if(bubble) bubble.innerHTML = '<span class="spin dark"></span>正在建库…';
    try{ await api('/api/reindex', {method:'POST'}); }
    catch(err){ fails.push('建库失败：' + err.message); }
  }
  pend.remove();

  if(fails.length){
    toast(`成功 ${okCount}/${total} 个，${fails.length} 个失败`);
    addMsgEl({role:'ai', content:'以下文件没能入库：· ' + fails.join('；')});
  }else{
    toast(`已加入 ${okCount} 个文件`);
    addMsgEl({role:'ai', content:`已加入 ${okCount} 个文件，现在可以直接提问了。`});
  }
  await loadStats(); await renderFiles();
}

async function entriesFromDataTransfer(dt){
  const out = [];
  const items = dt.items ? [...dt.items] : [];
  const entries = items.map(i => i.webkitGetAsEntry ? i.webkitGetAsEntry() : null).filter(Boolean);
  if(!entries.length) return [...(dt.files || [])].map(f => ({file:f, rel:f.name}));
  async function walk(entry, prefix){
    if(entry.isFile){
      const file = await new Promise((res, rej) => entry.file(res, rej));
      out.push({file, rel: prefix + file.name});
      return;
    }
    if(entry.isDirectory){
      const reader = entry.createReader();
      for(;;){
        const batch = await new Promise(res => reader.readEntries(res, () => res([])));
        if(!batch.length) break;
        for(const e of batch) await walk(e, prefix + entry.name + '/');
      }
    }
  }
  for(const e of entries) await walk(e, '');
  return out;
}

let dragDepth = 0;
window.addEventListener('dragenter', e => {
  if(!e.dataTransfer || ![...e.dataTransfer.types].includes('Files')) return;
  dragDepth++; $('#dropOverlay').classList.add('on');
});
window.addEventListener('dragover', e => { if(e.dataTransfer) e.preventDefault(); });
window.addEventListener('dragleave', () => {
  dragDepth = Math.max(0, dragDepth - 1);
  if(dragDepth === 0) $('#dropOverlay').classList.remove('on');
});
window.addEventListener('drop', async e => {
  if(!e.dataTransfer) return;
  e.preventDefault();
  dragDepth = 0;
  $('#dropOverlay').classList.remove('on');
  const items = await entriesFromDataTransfer(e.dataTransfer);
  if(items.length) uploadFiles(items);
});

/* —————————————— 启动 —————————————— */
(async function init(){
  await initAuth();
  loadStats(); renderFiles();
  await loadChats();
  if(CHATS.length) await openChat(CHATS[0].id);
  else showWelcome();
  $('#q').focus();
})();
</script>
__UPLOAD_SELFTEST__
</body></html>"""


UPLOAD_SELFTEST = """
<script>
(async function(){
  const qs = location.search;
  if(qs.indexOf('selftest=') < 0) return;
  const out=[]; const log=(k,v)=>out.push(k+'='+v);
  const wait=ms=>new Promise(r=>setTimeout(r,ms));
  const post = async () => {
    try{
      await fetch('/api/selftest_result', {method:'POST',
        headers:{'Content-Type':'application/json'}, body: JSON.stringify({items: out})});
    }catch(e){}
  };

  // selftest=ask：真问一句，检查答案气泡和出处卡片是否渲染出来
  if(qs.indexOf('selftest=ask') >= 0){
    try{
      document.querySelector('#q').value = '什么是向量数据库';
      await ask();
      await wait(600);
      log('bubbles', document.querySelectorAll('.bubble').length);
      log('sources_rendered', document.querySelectorAll('.src').length);
      log('srcbox_closed_by_default',
          String(!document.querySelector('.srcbox').open));
      const sum = document.querySelector('.srcbox > summary');
      if(sum){ sum.click(); await wait(150); }
      log('srcbox_opens_on_click',
          String(!!document.querySelector('.srcbox') && document.querySelector('.srcbox').open));
    }catch(e){ log('error', (e && e.message) || String(e)); }
    await post();
    return;
  }

  if(qs.indexOf('selftest=upload') < 0) return;
  try{
    // 1) 用 File 走一遍真实的上传接口
    const name='浏览器上传测试.txt';
    const f=new File(['浏览器上传测试内容：公司年假为 10 天。'], name, {type:'text/plain'});
    await uploadFiles([f]);
    const d = await (await fetch('/api/files')).json();
    log('uploaded_listed', String(d.files.some(x=>x.name===name)));

    // 2) 拖拽钩子：dragenter 应显示遮罩，dragleave 应隐藏
    const dt = new DataTransfer();
    dt.items.add(new File(['x'], 'dragged.txt', {type:'text/plain'}));
    window.dispatchEvent(new DragEvent('dragenter', {dataTransfer: dt, bubbles:true}));
    await wait(120);
    log('overlay_on_dragenter', String(document.getElementById('dropOverlay').classList.contains('on')));
    window.dispatchEvent(new DragEvent('dragleave', {dataTransfer: dt, bubbles:true}));
    await wait(120);
    log('overlay_off_dragleave', String(!document.getElementById('dropOverlay').classList.contains('on')));

    // 3) 侧栏列表里应能看到刚上传的文件
    await renderFiles();
    log('shown_in_sidebar', String(document.getElementById('fileList').textContent.indexOf(name) >= 0));
  }catch(e){ log('error', (e && e.message) || String(e)); }
  await post();
})();
</script>
"""
CONFIG_SELFTEST = """
<script>
(async function(){
  const wait = ms => new Promise(r=>setTimeout(r,ms));
  const until = async (fn, t=5000) => { const s=Date.now();
    while(Date.now()-s<t){ if(fn()) return true; await wait(80); } return false; };
  const out=[]; const log=(k,v)=>out.push(k+'='+v);
  const $ = s => document.querySelector(s);
  try{
    await until(()=>$('#addBtn'));
    $('#addBtn').click();
    // 必须等服务商下拉里有选项，否则 META.providers 还是空的
    await until(()=>document.querySelectorAll('#f_provider option').length > 0);
    await until(()=>$('#f_name'));
    const prov=$('#f_provider'), name=$('#f_name');
    log('initial_provider', prov.value);
    log('initial_name', name.value);
    log('initial_base_url', $('#f_base_url').value);
    log('initial_model', $('#f_model').value);

    // 离线模式下，嵌入模型/嵌入 Key 都应是禁用且空值（不用用户填）
    log('initial_embed_disabled', String($('#f_embedding_model').disabled));
    log('initial_embed_value', $('#f_embedding_model').value);
    log('initial_embed_key_disabled', String($('#f_embedding_api_key').disabled));
    // 切到百炼嵌入，应自动启用并填好默认模型名
    const embSel = $('#f_embedding');
    embSel.value='dashscope'; embSel.dispatchEvent(new Event('change'));
    log('dashscope_embed_model', $('#f_embedding_model').value);
    log('dashscope_embed_disabled', String($('#f_embedding_model').disabled));
    embSel.value='offline'; embSel.dispatchEvent(new Event('change'));

    const pick = v => { prov.value=v; prov.dispatchEvent(new Event('change')); };
    // 本地 Ollama：不需要 Key，Key 框应被禁用
    pick('ollama');
    log('ollama_base_url', $('#f_base_url').value);
    log('ollama_model', $('#f_model').value);
    log('ollama_key_disabled', String($('#f_api_key').disabled));
    log('ollama_key_placeholder', $('#f_api_key').placeholder);
    pick('deepseek');
    log('back_key_enabled', String(!$('#f_api_key').disabled));

    if(location.search.indexOf('selftest=open') >= 0){
      // 只打开新增表单就停下，用于截图/断言"默认预填"
      throw {stop:true};
    }

    pick('deepseek');  log('deepseek', name.value);
    pick('dashscope'); log('dashscope', name.value);
    pick('openai');    log('openai', name.value);

    name.value='我的自定义名称'; name.dispatchEvent(new Event('input'));
    pick('ollama');    log('custom_then_ollama', name.value);

    name.value=''; name.dispatchEvent(new Event('input'));
    pick('deepseek');  log('cleared_then_deepseek', name.value);

    log('base_url', $('#f_base_url').value);
    log('model', $('#f_model').value);
  }catch(e){ if(!(e && e.stop)) log('error', (e && e.message) || String(e)); }
  const pre=document.createElement('pre');
  pre.id='selftest'; pre.style.display='none';   // 不能影响 body 的 flex 布局
  pre.textContent='SELFTEST_RESULT ' + out.join(' | ');
  document.body.appendChild(pre);
  try{
    await fetch('/api/selftest_result', {method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({items: out})});
  }catch(e){}
})();
</script>
"""

# ============================================================ API 配置页
PAGE_CONFIG = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>API 配置 · RAG 知识库</title><style>
  :root{
    --bg:#f6f7f9; --card:#fff; --line:#e6e8ec; --line2:#eff1f4;
    --fg:#1f2328; --muted:#6b7280; --dim:#9aa1ab;
    --accent:#4d6bfe; --accent-h:#3d5bf0; --ok:#12a150; --warn:#b45309; --danger:#d92d20;
  }
  *{box-sizing:border-box}
  html,body{height:100%}
  body{margin:0;background:var(--bg);color:var(--fg);display:flex;overflow:hidden;
       font:14px/1.65 "Segoe UI","Microsoft YaHei",system-ui,-apple-system,sans-serif}
  a{color:var(--accent);text-decoration:none}
  input,select{width:100%;background:#fff;border:1px solid var(--line);border-radius:8px;
    padding:9px 11px;font-size:13.5px;color:var(--fg);outline:none;font-family:inherit}
  input:focus,select:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(77,107,254,.12)}
  input:disabled,select:disabled{background:#f5f6f8;color:var(--dim);cursor:not-allowed}
  .mono{font-family:Consolas,"Cascadia Mono",ui-monospace,monospace;font-size:12.5px}
  .btn{border:1px solid transparent;border-radius:8px;padding:8px 15px;font-size:13.5px;
       cursor:pointer;background:var(--accent);color:#fff;font-family:inherit;white-space:nowrap}
  .btn:hover{background:var(--accent-h)}
  .btn.ghost{background:#fff;border-color:var(--line);color:var(--fg)}
  .btn.ghost:hover{background:#f7f8fa;border-color:#d6dae2}
  .btn.sm{padding:5px 11px;font-size:12.5px;border-radius:7px}
  .btn.link{background:none;border:0;color:var(--accent);padding:4px 6px;font-size:13px}
  .btn.link:hover{background:#eef2ff;border-radius:6px}
  .btn.link.del{color:var(--danger)}
  .btn.link.del:hover{background:#fef2f2}
  .btn:disabled{opacity:.55;cursor:not-allowed}

  /* ——— 左侧栏 ——— */
  .sidebar{flex:0 0 240px;width:240px;background:#fff;border-right:1px solid var(--line);
           display:flex;flex-direction:column}
  .brand{padding:18px 20px 12px;display:flex;align-items:center;gap:9px}
  .brand .logo{width:22px;height:22px;border-radius:6px;background:var(--accent);flex:0 0 auto}
  .brand b{font-size:15px;letter-spacing:.2px}
  .nav{padding:0 12px;display:flex;flex-direction:column;gap:2px}
  .nav a{display:flex;align-items:center;gap:9px;padding:8px 12px;border-radius:8px;
         color:#374151;font-size:13.5px}
  .nav a:hover{background:#f3f4f6}
  .nav a.on{background:#eef2ff;color:var(--accent);font-weight:600}
  .nav .ico{width:15px;text-align:center;opacity:.9}
  .side-foot{margin-top:auto;border-top:1px solid var(--line);padding:14px 16px;
             font-size:12px;color:var(--muted);display:flex;flex-direction:column;gap:8px}
  .side-foot .row{display:flex;justify-content:space-between;gap:8px}
  .side-foot b{color:var(--fg);font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}

  /* ——— 主区 ——— */
  .main{flex:1;min-width:0;display:flex;flex-direction:column;min-height:0}
  .main-head{flex:0 0 auto;background:#fff;border-bottom:1px solid var(--line);padding:14px 26px;
             display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap}
  .main-head h2{margin:0;font-size:16.5px;font-weight:600}
  .main-head .sub{font-size:12px;color:var(--muted);margin-top:2px}
  .main-body{flex:1;min-height:0;overflow:auto;padding:22px 26px 48px}
  .wrap{max-width:1040px;margin:0 auto}
  h1{margin:0 0 10px;font-size:20px;font-weight:600;letter-spacing:.2px}
  .desc{margin:0 0 14px;color:var(--muted);font-size:13px;line-height:1.85;max-width:820px}
  .toolbar{display:flex;justify-content:flex-end;align-items:center;gap:10px;margin:0 0 14px}
  .chips{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 16px}
  .chip{font-size:12px;color:var(--muted);background:#fff;border:1px solid var(--line);
        border-radius:999px;padding:4px 11px;display:inline-flex;align-items:center;gap:6px}
  .chip b{color:var(--fg);font-weight:600}
  .dot{width:6px;height:6px;border-radius:50%;background:#c7ccd4;flex:0 0 auto}
  .dot.on{background:var(--ok)}

  /* ——— 表格 ——— */
  .tablebox{background:#fff;border:1px solid var(--line);border-radius:10px;overflow:hidden}

  /* ——— 访问口令卡片 ——— */
  .card{margin-top:22px;background:#fff;border:1px solid var(--line);border-radius:10px;padding:18px 20px}
  .card-head{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;
             flex-wrap:wrap;margin-bottom:14px}
  .card-head h3{margin:0 0 4px;font-size:15px;font-weight:600}
  .card-head p{margin:0;font-size:12.5px;color:var(--muted);line-height:1.7;max-width:640px}
  .card .grid2{display:grid;grid-template-columns:1fr 200px;gap:16px}
  .card .hint{font-size:11.5px;color:var(--dim);margin-top:5px;line-height:1.6}
  .card-foot{display:flex;justify-content:space-between;align-items:center;gap:12px;
             margin-top:16px;padding-top:14px;border-top:1px solid var(--line2)}
  .switch{display:inline-flex;align-items:center;gap:7px;font-size:12.5px;color:var(--muted);
          cursor:pointer;white-space:nowrap}
  .switch input{width:15px;height:15px;accent-color:var(--accent)}
  table{width:100%;border-collapse:collapse}
  th{background:#fafbfc;color:var(--muted);font-size:12.5px;font-weight:500;text-align:left;
     padding:12px 18px;border-bottom:1px solid var(--line);white-space:nowrap}
  td{padding:14px 18px;border-bottom:1px solid var(--line2);vertical-align:middle;font-size:13.5px}
  tbody tr:last-child td{border-bottom:0}
  tbody tr:hover td{background:#fafbff}
  .name{display:flex;align-items:center;gap:8px;font-weight:600;color:var(--fg)}
  .tag{font-size:11.5px;padding:1px 8px;border-radius:5px;background:#f3f4f6;color:var(--muted);font-weight:400}
  .tag.live{background:#ecfdf3;color:var(--ok)}
  .tag.bad{background:#fef2f2;color:var(--danger)}
  .sub{font-size:12px;color:var(--dim);margin-top:2px}
  td.acts{text-align:right;white-space:nowrap}
  .empty{padding:52px 18px;text-align:center;color:var(--muted);font-size:13.5px}
  .banner{display:none;background:#fffbeb;border:1px solid #fde68a;color:#92400e;
          border-radius:9px;padding:10px 14px;font-size:12.5px;margin:0 0 14px;line-height:1.8}
  .banner.on{display:block}

  /* ——— 弹窗 ——— */
  .modal{position:fixed;inset:0;background:rgba(17,24,39,.42);display:none;
         align-items:flex-start;justify-content:center;padding:48px 16px;overflow:auto;z-index:60}
  .modal.on{display:flex}
  .modal .box{background:#fff;border-radius:14px;width:min(660px,100%);
              box-shadow:0 18px 48px rgba(16,24,40,.18);overflow:hidden}
  .modal .head{padding:20px 24px 6px;display:flex;justify-content:space-between;align-items:flex-start;gap:12px}
  .modal h2{margin:0;font-size:17px;font-weight:600}
  .modal .head p{margin:6px 0 0;color:var(--muted);font-size:12.5px}
  .modal .close{background:none;border:0;font-size:20px;color:var(--dim);cursor:pointer;line-height:1;padding:2px 6px}
  .modal .close:hover{color:var(--fg)}
  .modal .body{padding:8px 24px 4px}
  .modal .foot{padding:16px 24px 20px;display:flex;justify-content:flex-end;gap:10px;
               border-top:1px solid var(--line2);margin-top:18px}
  .grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
  .grid.one{grid-template-columns:1fr}
  .body > .grid{margin-top:16px}
  .body > .grid:first-of-type{margin-top:2px}
  label.f{display:block;font-size:12.5px;color:var(--muted);margin:14px 0 6px}
  .grid label.f{margin-top:0}
  .hint{font-size:11.5px;color:var(--dim);margin-top:6px;line-height:1.7}
  .keyrow{display:flex;gap:8px;align-items:center}
  .keymask{flex:1;display:flex;align-items:center;justify-content:space-between;gap:10px;
           border:1px solid var(--line);border-radius:8px;padding:9px 11px;background:#fafbfc;
           font-size:12.5px;color:var(--muted)}
  .testbox{display:none;margin-top:14px;border-radius:8px;padding:10px 12px;font-size:12.5px;
           border:1px solid var(--line);background:#fafbfc;white-space:pre-wrap;word-break:break-word}
  .testbox.on{display:block}
  .testbox.ok{border-color:#bbf7d0;background:#f0fdf4;color:#15803d}
  .testbox.bad{border-color:#fecaca;background:#fef2f2;color:#b91c1c}
  .toast{position:fixed;left:50%;top:24px;transform:translateX(-50%);background:#1f2328;color:#fff;
         padding:9px 16px;border-radius:8px;font-size:13px;opacity:0;transition:.2s;
         pointer-events:none;z-index:99;max-width:70vw;box-shadow:0 8px 24px rgba(16,24,40,.18)}
  .toast.on{opacity:1}
  .spin{display:inline-block;width:12px;height:12px;border:2px solid rgba(255,255,255,.4);
        border-top-color:#fff;border-radius:50%;animation:sp .8s linear infinite;vertical-align:-2px;margin-right:6px}
  .spin.dark{border-color:rgba(31,35,40,.25);border-top-color:#1f2328}
  @keyframes sp{to{transform:rotate(360deg)}}
  ::-webkit-scrollbar{width:9px;height:9px}
  ::-webkit-scrollbar-thumb{background:#d8dce3;border-radius:5px}

  /* 右上角身份与登录 */
  .who-wrap{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
  .who-badge{font-size:12px;padding:3px 10px;border-radius:999px;border:1px solid var(--line);
             color:var(--muted);background:#fff;white-space:nowrap}
  .who-badge.on{color:#0b7a44;background:#e9f8f0;border-color:#bfe8d2;font-weight:600}
  .who-badge.local{color:#3543a8;background:#eef2ff;border-color:#dbe3ff;font-weight:600}
  .role-note{display:none;margin:0 0 12px;padding:8px 12px;border-radius:9px;
             background:#f3f6ff;border:1px solid #dbe3ff;color:#3543a8;font-size:12.5px}
  .role-note.on{display:block}

  /* 访客（未登录）隐藏管理入口 */
  .visitor #addFileBtn,.visitor #hintBox,.visitor .fdel{display:none!important}
  .visitor .toolbar .btn,.visitor #reindexBtn,.visitor #batchbar,
  .visitor .acts .btn.link.del,.visitor #clearSkips{display:none!important}
  .visitor #aSave,.visitor #aCard{display:none!important}
  .visitor .tablebox th:first-child,.visitor .tablebox td:first-child{display:none!important}
</style></head>
<body>
<aside class="sidebar">
  <div class="brand"><span class="logo"></span><b>RAG 知识库</b></div>
  <nav class="nav">
    <a href="/"><span class="ico">◈</span>知识库问答</a>
    <a href="/library"><span class="ico">▤</span>资料库</a>
    <a href="/config" class="on"><span class="ico">◎</span>API 配置</a>
  </nav>
  <div class="side-foot">
    <div class="row"><span>索引</span><b id="fIdx">-</b></div>
    <div class="row"><span>嵌入</span><b id="fEmb">-</b></div>
    <button class="btn ghost sm" id="reindexBtn" style="margin-top:2px">重建索引</button>
    <a href="/" style="font-size:12px">← 回问答页</a>
  </div>
</aside>

<main class="main">
  <div class="main-head">
    <div>
      <h2>API 配置</h2>
      <div class="sub">对话模型的接口配置，启用哪套就用哪套</div>
    </div>
    <div class="who-wrap">
      <span class="who-badge" id="whoBadge">…</span>
      <a class="btn ghost sm" href="/">回问答页 →</a>
      <button class="btn ghost sm" id="authBtn">登录</button>
    </div>
  </div>
  <div class="main-body"><div class="wrap">
  <p class="desc">
    这里是<b>对话模型</b>的接口配置。列表内是你全部的大模型 API 配置，Key 仅在本机保存、
    页面只回显掩码。配置好后回到问答页提问，答案就会由所启用的模型生成；
    嵌入方式决定检索精度，换过嵌入式后需要重建索引。
  </p>

  <div class="chips" id="chips"></div>
  <div class="banner" id="banner"></div>

  <div class="toolbar">
    <button class="btn ghost sm" id="testActiveBtn">测试当前</button>
    <button class="btn" id="addBtn">创建 API 配置</button>
  </div>

  <div class="tablebox">
    <table>
      <thead><tr>
        <th style="width:26%">名称</th>
        <th style="width:24%">服务商 / 模型</th>
        <th style="width:16%">Key</th>
        <th style="width:14%">创建时间</th>
        <th style="width:20%">上次测试</th>
        <th></th>
      </tr></thead>
      <tbody id="plist"></tbody>
    </table>
  </div>

  <div class="card" id="accessCard">
    <div class="card-head">
      <div>
        <h3>访问口令</h3>
        <p>别人打开问答页不用口令；改配置、重建索引、删除资料时要输这里这个口令。</p>
      </div>
      <label class="switch"><input type="checkbox" id="a_enabled"> 启用管理口令</label>
    </div>
    <div class="grid2">
      <div>
        <label class="f">当前 / 新口令</label>
        <input id="a_password" placeholder="例如 123456">
        <div class="hint">留空表示不改；保存后旧登录全部失效，需要重新输入</div>
      </div>
      <div>
        <label class="f">登录有效期（天）</label>
        <input id="a_ttl" type="number" min="1" max="90" value="7">
        <div class="hint">输一次口令后，多少天内不用再输</div>
      </div>
    </div>
    <div class="card-foot">
      <span class="hint" id="aState"></span>
      <button class="btn" id="aSave">保存口令设置</button>
    </div>
  </div>
</div></div></main>

<div class="modal" id="modal">
  <div class="box">
    <div class="head">
      <div>
        <h2 id="mTitle">创建 API 配置</h2>
        <p id="mSub">选服务商会自动带出地址、模型名和名称，粘上 Key 就能用</p>
      </div>
      <button class="close" id="mClose" title="关闭">×</button>
    </div>
    <div class="body">
      <div class="grid">
        <div><label class="f">名称</label>
          <input id="f_name" placeholder="例如：DeepSeek 官方"></div>
        <div><label class="f">服务商</label>
          <select id="f_provider"></select></div>
      </div>

      <label class="f">Base URL</label>
      <input id="f_base_url" class="mono" placeholder="https://api.deepseek.com/v1">
      <div class="hint">兼容 OpenAI 协议的服务地址，一般以 <span class="mono">/v1</span> 结尾</div>

      <div class="grid">
        <div><label class="f">模型名</label>
          <input id="f_model" class="mono" placeholder="deepseek-chat"></div>
        <div><label class="f">API Key</label>
          <div class="keyrow" id="keyRow">
            <input id="f_api_key" type="password" autocomplete="off" placeholder="sk-...">
          </div>
          <div class="hint" id="keyHint">Key 只存本机，页面只回显掩码</div>
        </div>
      </div>

      <div class="grid">
        <div><label class="f">嵌入方式</label>
          <select id="f_embedding"></select></div>
        <div><label class="f">嵌入模型</label>
          <input id="f_embedding_model" class="mono" placeholder="text-embedding-v1"></div>
      </div>

      <label class="f">嵌入专用 Key（可选）</label>
      <input id="f_embedding_api_key" type="password" autocomplete="off"
             placeholder="留空则复用上面的 Key（仅百炼可用）">

      <div class="hint" id="provHint"></div>
      <div class="testbox" id="testbox"></div>
    </div>
    <div class="foot">
      <button class="btn ghost" id="cancelBtn">取消</button>
      <button class="btn" id="saveBtn">保存</button>
    </div>
  </div>
</div>

__TOAST__
<script>

/* ———— 身份：本机管理员 / 管理员 / 访客 ———— */
async function initAuth(){
  let d = {admin:true, local:true, label:'本机管理员'};
  try{ d = await api('/api/whoami'); }catch(e){}
  window.IS_ADMIN = !!d.admin;
  const badge = $('#whoBadge'), btn = $('#authBtn');
  if(badge){
    badge.textContent = d.admin ? (d.local ? '本机管理员' : '管理员') : '访客';
    badge.className = 'who-badge ' + (d.admin ? (d.local ? 'local' : 'on') : '');
  }
  if(btn){
    if(d.admin){
      btn.textContent = '退出登录';
      btn.onclick = () => location.href = '/logout';
    }else{
      btn.textContent = '管理员登录';
      btn.onclick = () => location.href = '/login?next=' +
        encodeURIComponent(location.pathname + location.search);
    }
  }
  if(!d.admin) document.body.classList.add('visitor');
  return d;
}

const $ = s => document.querySelector(s);
let META = {providers:{}, embeddings:{}, profiles:[]};
let STATS = {};
let EDIT_ID = null;

function shortEmb(s){
  if(!s) return '-';
  if(s.indexOf('哈希')>=0 || s.indexOf('hashing')>=0) return '离线哈希向量';
  if(s.indexOf('DashScope')>=0 || s.indexOf('百炼')>=0) return '百炼嵌入';
  if(s.indexOf('Ollama')>=0) return '本地 Ollama';
  return s;
}

function fillSelect(sel, obj){
  sel.innerHTML = Object.entries(obj).map(([k,v])=>{
    const label = (typeof v === 'string') ? v : (v.label || k);
    return `<option value="${k}">${esc(label)}</option>`;
  }).join('');
}

/* —————————— 列表 —————————— */
function renderChips(){
  const active = META.profiles.find(p=>p.active);
  $('#chips').innerHTML = [
    `<span class="chip"><span class="dot ${active?'on':''}"></span>当前启用 <b>${esc(active?active.name:'未启用')}</b></span>`,
    `<span class="chip">索引 <b>${STATS.count||0}</b> 块 · <b>${(STATS.files||[]).length}</b> 个文件</span>`,
    `<span class="chip">嵌入 <b>${esc(shortEmb(STATS.embedder_raw||STATS.embedder))}</b></span>`,
    `<span class="chip">共 <b>${META.profiles.length}</b> 套配置</span>`
  ].join('');
}

function renderBanner(){
  const b = $('#banner'), msgs = [];
  if(STATS.embedding_warning) msgs.push(STATS.embedding_warning);
  if(STATS.embedder_mismatch){
    msgs.push(`索引是用「${esc(shortEmb(STATS.built_embedder))}」建的，当前嵌入是「${esc(shortEmb(STATS.embedder_raw))}」，`
      + `两者不一致会让检索严重失准，请点左下角「重建索引」。`);
  }
  if(msgs.length){ b.className='banner on'; b.innerHTML = msgs.join('<br>'); }
  else { b.className='banner'; b.innerHTML=''; }
}

function testCell(p){
  const t = p.last_test || {};
  if(!t.at) return '<span class="sub">还没测试过</span>';
  return `<span class="tag ${t.ok?'live':'bad'}">${t.ok?'连通正常':'连通失败'}</span>`
       + `<div class="sub">${esc(String(t.at).slice(5,16))}${t.latency?(' · '+t.latency+'s'):''}</div>`;
}

function renderTable(){
  const tb = $('#plist');
  if(!META.profiles.length){
    tb.innerHTML = `<tr><td colspan="6" class="empty">
      没有任何 API 配置。点右上角「创建 API 配置」开始，第一套会自动启用。</td></tr>`;
    return;
  }
  tb.innerHTML = META.profiles.map(p=>{
    const prov = (META.providers[p.provider]||{}).label || p.provider;
    const acts = [];
    // 启用中的行：在「测试」前面放一个静态标记；未启用的行：放「启用」按钮
    if(p.active) acts.push('<span class="tag live">启用中</span>');
    else acts.push(`<button class="btn link" data-act="use" data-id="${p.id}">启用</button>`);
    acts.push(`<button class="btn link" data-act="test" data-id="${p.id}">测试</button>`);
    acts.push(`<button class="btn link" data-act="edit" data-id="${p.id}">编辑</button>`);
    acts.push(`<button class="btn link del" data-act="del" data-id="${p.id}">删除</button>`);
    return `<tr>
      <td>
        <div class="name">${esc(p.name)} ${p.active?'<span class="tag live">启用中</span>':''}</div>
        <div class="sub">${esc(p.embedding ? shortEmb(META.embeddings[p.embedding]||p.embedding) : '')}</div>
      </td>
      <td>${esc(prov)}<div class="sub mono">${esc(p.model||'-')}</div></td>
      <td class="mono">${p.has_key?esc(p.api_key_masked):'<span class="sub">未设置</span>'}</td>
      <td class="sub">${esc((p.created_at||'').slice(0,10))}</td>
      <td>${testCell(p)}</td>
      <td class="acts">${acts.join('')}</td>
    </tr>`;
  }).join('');
}

$('#plist').addEventListener('click', async e=>{
  const b = e.target.closest('button'); if(!b) return;
  const id = b.dataset.id, act = b.dataset.act;
  const p = META.profiles.find(x=>x.id===id);
  try{
    if(act==='use'){
      await api('/api/profiles/'+id+'/activate',{method:'POST'});
      toast('已启用：'+(p?p.name:id)); await load();
    }
    if(act==='test'){
      b.disabled = true; b.textContent = '测试中';
      const r = await api('/api/profiles/'+id+'/test',{method:'POST'});
      toast((r.ok?'✓ ':'✗ ')+r.message);
      await load();
    }
    if(act==='edit'){ openModal(p); }
    if(act==='del'){
      if(!confirm('确定删除「'+(p?p.name:id)+'」？删除后不可恢复。')) return;
      await api('/api/profiles/'+id,{method:'DELETE'});
      toast('已删除'); await load();
    }
  }catch(err){ toast('操作失败：'+err.message); }
});

/* —————————— 弹窗 —————————— */
async function openModal(p){
  // 数据还没拉回来就点了"创建"时，先把服务商/嵌入方式补齐，否则下拉是空的
  if(!Object.keys(META.providers).length){
    try{ await load(); }catch(e){}
  }
  EDIT_ID = p ? p.id : null;
  $('#mTitle').textContent = p ? '编辑 API 配置' : '创建 API 配置';
  $('#mSub').textContent = p
    ? 'Key 输入框留空表示保持原 Key 不变'
    : '选服务商会自动带出地址、模型名和名称，粘上 Key 就能用';

  fillSelect($('#f_provider'), META.providers);
  fillSelect($('#f_embedding'), META.embeddings);

  const initKey = p ? p.provider : 'deepseek';
  const preset = META.providers[initKey] || {};
  $('#f_provider').value = initKey;
  syncKeyUI(preset);
  $('#f_name').value = p ? p.name : (preset.label || '');
  $('#f_base_url').value = p ? p.base_url : (preset.base_url || '');
  $('#f_model').value = p ? p.model : (preset.model || '');
  $('#f_embedding').value = p ? p.embedding : 'offline';
  $('#f_embedding_model').value = p ? (p.embedding_model||'') : '';
  $('#f_embedding_api_key').value = '';
  $('#provHint').textContent = preset.hint || '';
  $('#testbox').className = 'testbox';

  // Key 行：编辑已有配置时默认只显示掩码
  const row = $('#keyRow');
  if(p && p.has_key){
    row.innerHTML = `<div class="keymask"><span class="mono">${esc(p.api_key_masked)}</span>
        <button type="button" class="btn ghost sm" id="changeKeyBtn">更换</button></div>
      <input id="f_api_key" type="password" autocomplete="off" placeholder="粘贴新的 Key" style="display:none">`;
    $('#keyHint').textContent = '留空表示保持原 Key 不变';
  }else{
    row.innerHTML = `<input id="f_api_key" type="password" autocomplete="off" placeholder="sk-...">`;
    $('#keyHint').textContent = 'Key 只存本机，页面只回显掩码';
  }
  bindKeyToggle();
  syncEmbeddingUI();
  $('#modal').classList.add('on');
  $('#f_name').focus();
}

function bindKeyToggle(){
  const ck = $('#changeKeyBtn');
  if(ck) ck.onclick = ()=>{
    const mask = $('#keyRow .keymask'), inp = $('#f_api_key');
    if(mask) mask.style.display = 'none';
    if(inp){ inp.style.display = ''; inp.focus(); }
  };
}

function closeModal(){ $('#modal').classList.remove('on'); EDIT_ID = null; }

function syncEmbeddingUI(){
  const mode = $('#f_embedding').value;
  const m = $('#f_embedding_model');
  const k = $('#f_embedding_api_key');
  if(mode === 'offline'){
    m.value = ''; m.disabled = true; m.placeholder = '离线模式无需填写';
    k.disabled = true; k.placeholder = '离线模式无需填写';
  }else{
    m.disabled = false;
    m.placeholder = (mode === 'dashscope') ? 'text-embedding-v1' : 'qwen3-embedding:4b';
    if(!m.value) m.value = m.placeholder;
    k.disabled = false; k.placeholder = '留空则复用上面的 Key（仅百炼可用）';
  }
}


function syncKeyUI(preset){
  const k = $('#f_api_key');
  if(!k) return;
  if(preset && preset.needs_key === false){
    k.value = '';
    k.disabled = true;
    k.placeholder = '本地模型无需 API Key';
  }else{
    k.disabled = false;
    k.placeholder = 'sk-…';
  }
}
$('#f_provider').addEventListener('change', e=>{
  const preset = META.providers[e.target.value] || {};
  if(preset.base_url) $('#f_base_url').value = preset.base_url;
  if(preset.model) $('#f_model').value = preset.model;
  const cur = ($('#f_name').value||'').trim();
  const prev = Object.values(META.providers).map(x=>x.label);
  // 名称没被手动改过（空或等于某个服务商默认名）就跟着变
  if(!cur || prev.indexOf(cur) >= 0) $('#f_name').value = preset.label || '';
  $('#provHint').textContent = preset.hint || '';
  syncKeyUI(preset);
});
$('#f_embedding').addEventListener('change', syncEmbeddingUI);

$('#mClose').onclick = closeModal;
$('#cancelBtn').onclick = closeModal;
$('#modal').addEventListener('click', e=>{ if(e.target.id==='modal') closeModal(); });
$('#addBtn').onclick = ()=>openModal(null);

$('#saveBtn').onclick = async ()=>{
  const body = {
    name: $('#f_name').value.trim(),
    provider: $('#f_provider').value,
    base_url: $('#f_base_url').value.trim(),
    model: $('#f_model').value.trim(),
    api_key: $('#f_api_key').value.trim(),
    embedding: $('#f_embedding').value,
    embedding_model: $('#f_embedding_model').value.trim(),
    embedding_api_key: $('#f_embedding_api_key').value.trim(),
  };
  if(!body.base_url || !body.model){ toast('Base URL 和模型名必须填'); return; }
  const b = $('#saveBtn'); b.disabled = true; b.innerHTML = '<span class="spin"></span>保存中';
  try{
    if(EDIT_ID){
      await api('/api/profiles/'+EDIT_ID, {method:'PUT',
        headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
      toast('已保存修改');
    }else{
      await api('/api/profiles', {method:'POST',
        headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
      toast('已创建并启用');
    }
    closeModal();
    await load();
  }catch(err){ toast('保存失败：'+err.message); }
  finally{ b.disabled = false; b.textContent = '保存'; }
};

$('#testActiveBtn').onclick = async ()=>{
  const a = META.profiles.find(p=>p.active);
  if(!a){ toast('还没有启用中的配置'); return; }
  const b = $('#testActiveBtn'); b.disabled = true; b.innerHTML = '<span class="spin dark"></span>测试中';
  try{
    const r = await api('/api/profiles/'+a.id+'/test',{method:'POST'});
    toast((r.ok?'✓ ':'✗ ')+r.message);
    await load();
  }catch(e){ toast('测试失败：'+e.message); }
  finally{ b.disabled=false; b.textContent='测试当前'; }
};

$('#reindexBtn').onclick = async ()=>{
  const b = $('#reindexBtn'); b.disabled = true; b.textContent = '重建中…';
  try{
    const r = await api('/api/reindex',{method:'POST'});
    toast(`重建完成：${r.chunks} 块 / ${r.files} 个文件`);
    await load();
  }catch(e){ toast('重建失败：'+e.message); }
  finally{ b.disabled=false; b.textContent='重建索引'; }
};

/* —————————— 数据 —————————— */
function renderFoot(){
  $('#fIdx').textContent = `${STATS.count||0} 块 / ${(STATS.files||[]).length} 文件`;
  $('#fEmb').textContent = shortEmb(STATS.embedder_raw || STATS.embedder);
}

async function load(){
  const d = await api('/api/profiles');
  META.providers = d.providers; META.embeddings = d.embeddings;
  META.profiles = d.profiles; STATS = d.stats || {};
  renderFoot(); renderChips(); renderBanner(); renderTable();
}

/* —————— 访问口令 —————— */
async function loadAccess(){
  try{
    const d = await api('/api/access');
    $('#a_enabled').checked = !!d.enabled;
    $('#a_ttl').value = d.ttl_days || 7;
    $('#a_password').value = d.password || '';
    $('#aState').textContent = d.enabled
      ? `当前口令：${d.password || '（未设置）'}　有效期 ${d.ttl_days} 天`
      : '管理口令已关闭 —— 任何拿到地址的人都能改配置、删资料';
    $('#aState').style.color = d.enabled ? '' : 'var(--danger)';
  }catch(e){ $('#aState').textContent = '读取失败：' + e.message; }
}

$('#aSave').onclick = async ()=>{
  const pw = $('#a_password').value.trim();
  const ttl = parseInt($('#a_ttl').value, 10) || 7;
  const body = { ttl_days: ttl, enabled: $('#a_enabled').checked };
  if(pw) body.password = pw;
  const btn = $('#aSave'); btn.disabled = true; btn.textContent = '保存中…';
  try{
    const r = await api('/api/access', {method:'POST',
      headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
    toast(r.secret_rotated ? '已保存：口令已更新，之前登录的会话全部失效' : '已保存');
    await loadAccess();
  }catch(e){ toast('保存失败：' + e.message); }
  finally{ btn.disabled = false; btn.textContent = '保存口令设置'; }
};

initAuth();
loadAccess();
load().catch(e=>toast('加载失败：'+e.message));
</script>
</body></html>"""


# ============================================================ 资料库页
PAGE_LIBRARY = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>资料库 · RAG 知识库</title><style>
  :root{
    --bg:#f6f7f9; --card:#fff; --line:#e6e8ec; --line2:#eff1f4;
    --fg:#1f2328; --muted:#6b7280; --dim:#9aa1ab;
    --accent:#4d6bfe; --accent-h:#3d5bf0; --ok:#12a150; --warn:#b45309; --danger:#d92d20;
  }
  *{box-sizing:border-box}
  html,body{height:100%}
  body{margin:0;background:var(--bg);color:var(--fg);display:flex;overflow:hidden;
       font:14px/1.65 "Segoe UI","Microsoft YaHei",system-ui,-apple-system,sans-serif}
  a{color:var(--accent);text-decoration:none}
  input{background:#fff;border:1px solid var(--line);border-radius:8px;padding:8px 11px;
        font-size:13.5px;font-family:inherit;color:var(--fg);outline:none}
  input:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(77,107,254,.12)}
  .mono{font-family:Consolas,"Cascadia Mono",ui-monospace,monospace;font-size:12.5px}
  .btn{border:1px solid transparent;border-radius:8px;padding:8px 15px;font-size:13.5px;
       cursor:pointer;background:var(--accent);color:#fff;font-family:inherit;white-space:nowrap}
  .btn:hover{background:var(--accent-h)}
  .btn.ghost{background:#fff;border-color:var(--line);color:var(--fg)}
  .btn.ghost:hover{background:#f7f8fa;border-color:#d6dae2}
  .btn.sm{padding:5px 11px;font-size:12.5px;border-radius:7px}
  .btn.link{background:none;border:0;color:var(--accent);padding:3px 6px;font-size:12.5px}
  .btn.link:hover{background:#eef2ff;border-radius:6px}
  .btn.link.del{color:var(--danger)}
  .btn.link.del:hover{background:#fef2f2}
  .btn:disabled{opacity:.5;cursor:not-allowed}

  .sidebar{flex:0 0 240px;width:240px;background:#fff;border-right:1px solid var(--line);
           display:flex;flex-direction:column}
  .brand{padding:18px 20px 12px;display:flex;align-items:center;gap:9px}
  .brand .logo{width:22px;height:22px;border-radius:6px;background:var(--accent);flex:0 0 auto}
  .brand b{font-size:15px}
  .nav{padding:0 12px;display:flex;flex-direction:column;gap:2px}
  .nav a{display:flex;align-items:center;gap:9px;padding:8px 12px;border-radius:8px;
         color:#374151;font-size:13.5px}
  .nav a:hover{background:#f3f4f6}
  .nav a.on{background:#eef2ff;color:var(--accent);font-weight:600}
  .nav .ico{width:15px;text-align:center}
  .side-foot{margin-top:auto;border-top:1px solid var(--line);padding:14px 16px;
             font-size:12px;color:var(--muted);display:flex;flex-direction:column;gap:8px}
  .side-foot .row{display:flex;justify-content:space-between;gap:8px}
  .side-foot b{color:var(--fg);font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}

  .main{flex:1;min-width:0;display:flex;flex-direction:column;min-height:0}
  .main-head{flex:0 0 auto;background:#fff;border-bottom:1px solid var(--line);padding:14px 26px;
             display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap}
  .main-head h2{margin:0;font-size:16.5px;font-weight:600}
  .main-head .sub{font-size:12px;color:var(--muted);margin-top:2px}
  .main-body{flex:1;min-height:0;overflow:auto;padding:22px 26px 48px}
  .wrap{max-width:1040px;margin:0 auto}
  h1{margin:0 0 8px;font-size:20px;font-weight:600}
  .desc{margin:0 0 14px;color:var(--muted);font-size:13px;line-height:1.85;max-width:820px}
  .chips{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 16px}
  .chip{font-size:12px;color:var(--muted);background:#fff;border:1px solid var(--line);
        border-radius:999px;padding:4px 11px}
  .chip b{color:var(--fg);font-weight:600}
  .toolbar{display:flex;gap:9px;align-items:center;margin:0 0 12px;flex-wrap:wrap}
  .toolbar .grow{flex:1}
  .toolbar input{width:240px}
  .batchbar{display:none;align-items:center;gap:12px;background:#eef2ff;border:1px solid #dbe3ff;
            color:#3543a8;border-radius:9px;padding:8px 14px;font-size:13px;margin:0 0 12px}
  .batchbar.on{display:flex}
  .tablebox{background:#fff;border:1px solid var(--line);border-radius:10px;overflow:hidden}
  table{width:100%;border-collapse:collapse}
  th{background:#fafbfc;color:var(--muted);font-size:12.5px;font-weight:500;text-align:left;
     padding:11px 16px;border-bottom:1px solid var(--line);white-space:nowrap}
  td{padding:12px 16px;border-bottom:1px solid var(--line2);vertical-align:middle;font-size:13.5px}
  tbody tr:last-child td{border-bottom:0}
  tbody tr:hover td{background:#fafbff}
  .nm{font-weight:600;color:var(--fg);word-break:break-all}
  .sub{font-size:12px;color:var(--dim);margin-top:2px;word-break:break-all}
  .tag{font-size:11.5px;padding:1px 8px;border-radius:5px;background:#f3f4f6;color:var(--muted)}
  .tag.data{background:#eef2ff;color:#3d5bf0}
  .tag.ext{background:#fffbeb;color:#92400e}
  .tag.orphan{background:#fef2f2;color:#b91c1c}
  td.acts{text-align:right;white-space:nowrap}
  .empty{padding:54px 18px;text-align:center;color:var(--muted);font-size:13.5px}
  input[type=checkbox]{width:15px;height:15px;accent-color:var(--accent);cursor:pointer}

  .skips{background:#fffbeb;border:1px solid #fde68a;border-radius:10px;padding:10px 14px;
         margin:0 0 12px;font-size:12.5px;color:#92400e}  .skips>summary{cursor:pointer;font-weight:600;outline:none}
  .skips>summary .skipsub{font-weight:400;color:#b45309;font-size:11.5px}
  .skiprow{display:flex;justify-content:space-between;gap:12px;padding:5px 0;
           border-bottom:1px dashed #f3e0b5;word-break:break-all}
  .skiprow:last-child{border-bottom:0}
  .skiprow .sn{flex:1}
  .skiprow .sr{color:#b45309;flex:0 0 auto}

  .modal{position:fixed;inset:0;background:rgba(17,24,39,.42);display:none;
         align-items:flex-start;justify-content:center;padding:48px 16px;overflow:auto;z-index:60}
  .modal.on{display:flex}
  .modal .box{background:#fff;border-radius:14px;width:min(760px,100%);
              box-shadow:0 18px 48px rgba(16,24,40,.18)}
  .modal .head{padding:20px 24px 10px;display:flex;justify-content:space-between;gap:12px}
  .modal h2{margin:0;font-size:16.5px}
  .modal .head p{margin:6px 0 0;color:var(--muted);font-size:12.5px;word-break:break-all}
  .modal .close{background:none;border:0;font-size:20px;color:var(--dim);cursor:pointer}
  .modal .body{padding:0 24px 22px;max-height:62vh;overflow:auto}
  .chunk{border:1px solid var(--line);border-radius:9px;padding:10px 12px;margin-top:10px;background:#fafbfc}
  .chunk .top{font-size:11.5px;color:var(--dim);margin-bottom:5px}
  .chunk .txt{font-size:12.5px;color:#374151;white-space:pre-wrap;word-break:break-word}
  .toast{position:fixed;left:50%;top:24px;transform:translateX(-50%);background:#1f2328;color:#fff;
         padding:9px 16px;border-radius:8px;font-size:13px;opacity:0;transition:.2s;
         pointer-events:none;z-index:99;max-width:70vw;box-shadow:0 8px 24px rgba(16,24,40,.18)}
  .toast.on{opacity:1}
  .spin{display:inline-block;width:12px;height:12px;border:2px solid rgba(255,255,255,.4);
        border-top-color:#fff;border-radius:50%;animation:sp .8s linear infinite;
        vertical-align:-2px;margin-right:6px}
  @keyframes sp{to{transform:rotate(360deg)}}
  ::-webkit-scrollbar{width:9px;height:9px}
  ::-webkit-scrollbar-thumb{background:#d8dce3;border-radius:5px}

  /* 右上角身份与登录 */
  .who-wrap{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
  .who-badge{font-size:12px;padding:3px 10px;border-radius:999px;border:1px solid var(--line);
             color:var(--muted);background:#fff;white-space:nowrap}
  .who-badge.on{color:#0b7a44;background:#e9f8f0;border-color:#bfe8d2;font-weight:600}
  .who-badge.local{color:#3543a8;background:#eef2ff;border-color:#dbe3ff;font-weight:600}
  .role-note{display:none;margin:0 0 12px;padding:8px 12px;border-radius:9px;
             background:#f3f6ff;border:1px solid #dbe3ff;color:#3543a8;font-size:12.5px}
  .role-note.on{display:block}

  /* 访客（未登录）隐藏管理入口 */
  .visitor #addFileBtn,.visitor #hintBox,.visitor .fdel{display:none!important}
  .visitor .toolbar .btn,.visitor #reindexBtn,.visitor #batchbar,
  .visitor .acts .btn.link.del,.visitor #clearSkips{display:none!important}
  .visitor #aSave,.visitor #aCard{display:none!important}
  .visitor .tablebox th:first-child,.visitor .tablebox td:first-child{display:none!important}
</style></head>
<body>
<aside class="sidebar">
  <div class="brand"><span class="logo"></span><b>RAG 知识库</b></div>
  <nav class="nav">
    <a href="/"><span class="ico">◈</span>知识库问答</a>
    <a href="/library" class="on"><span class="ico">▤</span>资料库</a>
    <a href="/config"><span class="ico">◎</span>API 配置</a>
  </nav>
  <div class="side-foot">
    <div class="row"><span>索引</span><b id="fIdx">-</b></div>
    <div class="row"><span>嵌入</span><b id="fEmb">-</b></div>
    <button class="btn ghost sm" id="reindexBtn" style="margin-top:2px">重建索引</button>
    <a href="/" style="font-size:12px">← 回问答页</a>
  </div>
</aside>

<main class="main">
  <div class="main-head">
    <div>
      <h2>资料库</h2>
      <div class="sub">管理已索引的资料：看分块、预览内容、删除噪声</div>
    </div>
    <div class="who-wrap">
      <span class="who-badge" id="whoBadge">…</span>
      <a class="btn ghost sm" href="/">回问答页 →</a>
      <button class="btn ghost sm" id="authBtn">登录</button>
    </div>
  </div>
  <div class="main-body"><div class="wrap">
  <p class="desc">
    这里管理知识库里所有已被索引的内容：<b>data 目录里的文件</b>、<b>从本机路径导入的外部文件夹</b>，
    以及索引里还没清掉的残留。每行的「分块」是它实际贡献的检索单元数量——分块异常大通常是日志类文件，
    建议删掉，否则会把真正有用的内容挤出召回结果。
  </p>

  <div class="chips" id="chips"></div>
  <p class="role-note" id="roleNote"></p>

  <details class="skips" id="skipsBox" style="display:none">
    <summary>最近跳过的文件 <b id="skipCount">0</b> <span class="skipsub">（这些没入库，看看是不是你要的）</span></summary>
    <div id="skipList"></div>
    <button class="btn ghost sm" id="clearSkips" style="margin-top:6px">清空记录</button>
  </details>

  <div class="toolbar">
    <input id="q" placeholder="搜索文件名…" autocomplete="off">
    <span class="grow"></span>
    <button class="btn ghost sm" id="addFileBtn">上传文件</button>
    <button class="btn ghost sm" id="addFolderBtn">导入文件夹</button>
    <button class="btn ghost sm" id="addPathBtn">填本机路径</button>
    <button class="btn sm" id="reindexBtn2">重建索引</button>
  </div>

  <div class="batchbar" id="batchbar">
    <span id="batchText">已选 0 项</span>
    <span class="grow" style="flex:1"></span>
    <button class="btn ghost sm" id="clearSel">取消选择</button>
    <button class="btn sm" id="batchDel" style="background:#d92d20">批量删除</button>
  </div>

  <div class="tablebox">
    <table>
      <thead><tr>
        <th style="width:38px"><input type="checkbox" id="checkAll"></th>
        <th style="width:40%">名称</th>
        <th>类型</th>
        <th>大小</th>
        <th>分块</th>
        <th>字数</th>
        <th>加入时间</th>
        <th></th>
      </tr></thead>
      <tbody id="rows"></tbody>
    </table>
  </div>
</div></div></main>

<input type="file" id="filePicker" multiple style="display:none"
       accept=".pdf,.docx,.txt,.md,.markdown,.csv,.xlsx,.json">
<input type="file" id="folderPicker" webkitdirectory directory multiple style="display:none">

<div class="modal" id="modal">
  <div class="box">
    <div class="head">
      <div><h2 id="mTitle">内容预览</h2><p id="mSub"></p></div>
      <button class="close" id="mClose">×</button>
    </div>
    <div class="body" id="mBody"></div>
  </div>
</div>

__TOAST__
<script>

/* ———— 身份：本机管理员 / 管理员 / 访客 ———— */
async function initAuth(){
  let d = {admin:true, local:true, label:'本机管理员'};
  try{ d = await api('/api/whoami'); }catch(e){}
  window.IS_ADMIN = !!d.admin;
  const badge = $('#whoBadge'), btn = $('#authBtn');
  if(badge){
    badge.textContent = d.admin ? (d.local ? '本机管理员' : '管理员') : '访客';
    badge.className = 'who-badge ' + (d.admin ? (d.local ? 'local' : 'on') : '');
  }
  if(btn){
    if(d.admin){
      btn.textContent = '退出登录';
      btn.onclick = () => location.href = '/logout';
    }else{
      btn.textContent = '管理员登录';
      btn.onclick = () => location.href = '/login?next=' +
        encodeURIComponent(location.pathname + location.search);
    }
  }
  if(!d.admin) document.body.classList.add('visitor');
  return d;
}

const $ = s => document.querySelector(s);
let DATA = {items: [], totals: {}, index: {}};
let SEL = new Set();

function fmtSize(kb){
  if(!kb) return '-';
  return kb >= 1024 ? (kb/1024).toFixed(1)+' MB' : Math.max(1, Math.round(kb))+' KB';
}
function fmtNum(n){
  if(n == null) return '-';
  return n >= 10000 ? (n/10000).toFixed(1)+' 万' : String(n);
}
function kindTag(it){
  if(it.skip_reason) return '<span class="tag orphan">已跳过</span>';
  if(it.kind === 'external') return '<span class="tag ext">外部目录</span>';
  if(it.kind === 'orphan') return '<span class="tag orphan">索引残留</span>';
  return `<span class="tag data">${esc((it.ext || 'file').toUpperCase())}</span>`;
}

async function load(){
  const who = await initAuth();
  const note = $('#roleNote');
  if(note){
    note.textContent = who.admin
      ? '你可以上传、删除资料、重建索引。'
      : '你现在是访客：可以查看和预览资料，上传 / 删除 / 重建索引需要管理员登录。';
    note.classList.toggle('on', true);
  }
  const d = await api('/api/library');
  DATA = d;
  renderChips();
  renderRows();
  loadSkips();
}

async function loadSkips(){
  try{
    const d = await api('/api/skips');
    const items = d.skips || [];
    const box = $('#skipsBox');
    if(!items.length){ box.style.display = 'none'; return; }
    box.style.display = '';
    $('#skipCount').textContent = items.length;
    $('#skipList').innerHTML = items.map(s => `
      <div class="skiprow"><span class="sn">${esc(s.name)}</span>
      <span class="sr">${esc(s.reason)}</span></div>`).join('');
  }catch(e){}
}

$('#clearSkips').onclick = async e => {
  e.preventDefault();
  try{
    await api('/api/skips', {method:'DELETE'});
    $('#skipsBox').style.display = 'none';
    toast('记录已清空');
  }catch(err){ toast('清空失败：' + err.message); }
};

function renderChips(){
  const t = DATA.totals || {}, ix = DATA.index || {};
  $('#chips').innerHTML = [
    `<span class="chip">文件 <b>${t.files || 0}</b> 个</span>`,
    `<span class="chip">外部目录 <b>${t.external || 0}</b> 个</span>`,
    `<span class="chip">分块 <b>${t.chunks || 0}</b></span>`,
    `<span class="chip">总字数 <b>${fmtNum(t.chars || 0)}</b></span>`,
    `<span class="chip">后端 <b>${esc(ix.backend || '-')}</b></span>`,
    `<span class="chip">嵌入 <b>${esc(shortEmb(ix.embedder_raw || ix.embedder))}</b></span>`
  ].join('');
  $('#fIdx').textContent = `${ix.count || 0} 块`;
  $('#fEmb').textContent = shortEmb(ix.embedder_raw || ix.embedder);
}

function shortEmb(s){
  if(!s) return '-';
  if(s.indexOf('哈希') >= 0 || s.indexOf('hashing') >= 0) return '离线哈希向量';
  if(s.indexOf('DashScope') >= 0 || s.indexOf('百炼') >= 0) return '百炼嵌入';
  if(s.indexOf('Ollama') >= 0) return '本地 Ollama';
  return s;
}

function visibleItems(){
  const q = $('#q').value.trim().toLowerCase();
  if(!q) return DATA.items;
  return DATA.items.filter(i => (i.name + ' ' + (i.display || '')).toLowerCase().indexOf(q) >= 0);
}

function renderRows(){
  const items = visibleItems();
  const tb = $('#rows');
  if(!items.length){
    tb.innerHTML = `<tr><td colspan="8" class="empty">
      ${DATA.items.length ? '没有匹配的资料' : '资料库是空的，用上面的按钮添加文件或文件夹'}</td></tr>`;
    updateBatch(); return;
  }
  tb.innerHTML = items.map((it, i) => {
    const title = it.display ? `${esc(it.display)}` : esc(it.name);
    const sub = it.display ? esc(it.name)
              : (it.skip_reason ? esc(it.skip_reason) : '');
    return `<tr data-name="${esc(it.name)}" data-kind="${it.kind}">
      <td><input type="checkbox" class="pick" data-name="${esc(it.name)}" ${SEL.has(it.name) ? 'checked' : ''}></td>
      <td><div class="nm">${title}</div>${sub ? `<div class="sub">${sub}</div>` : ''}</td>
      <td>${kindTag(it)}</td>
      <td class="mono">${it.kind === 'data' ? fmtSize(it.size_kb) : (it.file_count ? it.file_count + ' 个文件' : '-')}</td>
      <td class="mono">${it.chunks || 0}</td>
      <td class="mono">${fmtNum(it.chars || 0)}</td>
      <td class="sub">${esc((it.mtime || '').slice(0, 16)) || '-'}</td>
      <td class="acts">
        <button class="btn link" data-act="preview" data-name="${esc(it.name)}">预览</button>
        <button class="btn link del" data-act="del" data-name="${esc(it.name)}">删除</button>
      </td></tr>`;
  }).join('');
  updateBatch();
}

$('#q').addEventListener('input', renderRows);

$('#rows').addEventListener('click', async e => {
  const cb = e.target.closest('.pick');
  if(cb){
    if(cb.checked) SEL.add(cb.dataset.name); else SEL.delete(cb.dataset.name);
    updateBatch(); return;
  }
  const b = e.target.closest('button'); if(!b) return;
  const name = b.dataset.name;
  const item = DATA.items.find(x => x.name === name) || {};
  if(b.dataset.act === 'preview') return preview(item);
  if(b.dataset.act === 'del') return removeOne(item);
});

$('#checkAll').addEventListener('change', e => {
  SEL = new Set();
  if(e.target.checked) visibleItems().forEach(i => SEL.add(i.name));
  renderRows();
});

function updateBatch(){
  const bar = $('#batchbar');
  if(SEL.size){ bar.classList.add('on'); $('#batchText').textContent = `已选 ${SEL.size} 项`; }
  else bar.classList.remove('on');
}
$('#clearSel').onclick = () => { SEL = new Set(); $('#checkAll').checked = false; renderRows(); };

async function preview(item){
  $('#mTitle').textContent = item.display || item.name;
  $('#mSub').textContent = item.kind === 'external'
    ? '外部目录：下面是它贡献的前几段内容'
    : item.name;
  $('#mBody').innerHTML = '<div class="empty">加载中…</div>';
  $('#modal').classList.add('on');
  try{
    const src = item.kind === 'external' ? (item.display + '/') : item.name;
    const d = await api('/api/preview?limit=6&source=' + encodeURIComponent(src));
    if(!d.chunks.length){ $('#mBody').innerHTML = '<div class="empty">索引里没有它的内容（可能还没重建）</div>'; return; }
    $('#mBody').innerHTML = d.chunks.map(c => {
      const loc = c.page ? `第 ${c.page} 页` : (c.row != null ? `第 ${c.row + 1} 行` : '');
      return `<div class="chunk">
        <div class="top">${loc ? esc(loc) + ' · ' : ''}${c.chars} 字</div>
        <div class="txt">${esc(c.text)}…</div></div>`;
    }).join('');
  }catch(err){
    $('#mBody').innerHTML = `<div class="empty">预览失败：${esc(err.message)}</div>`;
  }
}
$('#mClose').onclick = () => $('#modal').classList.remove('on');
$('#modal').addEventListener('click', e => { if(e.target.id === 'modal') $('#modal').classList.remove('on'); });

async function removeOne(item){
  const label = item.display || item.name;
  const extra = item.kind === 'external'
    ? '只会取消登记，原文件夹里的文件不动。'
    : '文件会从 data 目录删除。';
  if(!confirm(`移除「${label}」？${extra}索引会重建。`)) return;
  await doRemove([item]);
}

async function doRemove(items){
  let ok = 0;
  const fails = [];
  for(const it of items){
    try{
      if(it.kind === 'external'){
        await api('/api/external_remove', {method:'POST',
          headers:{'Content-Type':'application/json'}, body: JSON.stringify({path: it.name})});
      }else if(it.kind === 'data'){
        await api('/api/files?name=' + encodeURIComponent(it.name), {method:'DELETE'});
      }else{
        fails.push(it.name + '：索引残留，请点「重建索引」清理');
        continue;
      }
      ok++;
    }catch(err){ fails.push((it.display || it.name) + '：' + err.message); }
  }
  SEL = new Set();
  toast(fails.length ? `成功 ${ok} 个，${fails.length} 个失败` : `已移除 ${ok} 项`);
  if(fails.length) alert('以下项目没能移除：' + fails.join('；'));
  await load();
}

$('#batchDel').onclick = async () => {
  const items = DATA.items.filter(i => SEL.has(i.name));
  if(!items.length) return;
  if(!confirm(`确定移除选中的 ${items.length} 项？索引会重建。`)) return;
  await doRemove(items);
};

/* ———— 导入 ———— */
$('#addFileBtn').onclick = () => $('#filePicker').click();
$('#addFolderBtn').onclick = () => $('#folderPicker').click();

$('#filePicker').addEventListener('change', e => {
  const files = [...e.target.files]; e.target.value = '';
  if(files.length) uploadBatch(files.map(f => ({file: f, rel: f.name})));
});
$('#folderPicker').addEventListener('change', e => {
  const files = [...e.target.files]; e.target.value = '';
  if(files.length) uploadBatch(files.map(f => ({file: f, rel: f.webkitRelativePath || f.name})));
});

async function uploadBatch(items){
  let ok = 0; const fails = [];
  toast(`正在上传 ${items.length} 个文件…`);
  for(const it of items){
    try{
      await api('/api/upload?name=' + encodeURIComponent(it.rel) + '&index=0',
                {method:'POST', body: it.file});
      ok++;
    }catch(err){ fails.push(it.rel + '：' + err.message); }
  }
  if(ok){
    toast('正在建库…');
    try{ await api('/api/reindex', {method:'POST'}); }catch(err){ fails.push('建库失败：' + err.message); }
  }
  toast(fails.length ? `上传 ${ok} 个，${fails.length} 个有问题` : `已加入 ${ok} 个文件`);
  if(fails.length) alert('以下文件被跳过：' + fails.join('；'));
  await load();
}

$('#addPathBtn').onclick = async () => {
  const p = prompt('输入本机文件夹的完整路径（不复制文件，直接读原位置）。例如：D:/资料/产品文档');
  if(!p || !p.trim()) return;
  toast('正在扫描并入库…');
  try{
    const r = await api('/api/import_folder', {method:'POST',
      headers:{'Content-Type':'application/json'}, body: JSON.stringify({path: p.trim(), copy: false})});
    toast(`已导入 ${r.file_count} 个文件${r.skipped_count ? '，跳过 ' + r.skipped_count + ' 个' : ''}`);
    if(r.skipped_count) alert('以下文件被跳过：' + (r.skipped || []).join('；'));
    await load();
  }catch(err){ toast('导入失败：' + err.message); }
};

$('#reindexBtn').onclick = doRebuild;
$('#reindexBtn2').onclick = doRebuild;
async function doRebuild(){
  const b = $('#reindexBtn2'); b.disabled = true; b.innerHTML = '<span class="spin"></span>重建中';
  try{
    const r = await api('/api/reindex', {method:'POST'});
    toast(`重建完成：${r.chunks} 块 / ${r.files} 个来源`);
    await load();
  }catch(err){ toast('重建失败：' + err.message); }
  finally{ b.disabled = false; b.textContent = '重建索引'; }
}

load().catch(e => {
  $('#rows').innerHTML = `<tr><td colspan="8" class="empty">加载失败：${esc(e.message)}</td></tr>`;
});
</script>
</body></html>"""

