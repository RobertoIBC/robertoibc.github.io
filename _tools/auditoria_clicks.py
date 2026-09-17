"""Auditoria de clicks: navegacion que NO sale de un href estatico (JS: location.href, window.open...).
Levanta un servidor local, y para cada pagina que tenga navegacion por JS (o para todas, con --all)
hace hover + click en cada elemento pulsable que no sea un <a> con href (o que este dentro de uno pero con
JS encima) y comprueba que el destino resultante existe en el sitio. Lo que el verificador estatico no ve."""
import re, pathlib, subprocess, sys, os, socket, time, json, threading, http.server, functools
os.chdir(pathlib.Path(__file__).resolve().parent.parent)   # raiz del repo
CH = os.environ.get('CHROME') or next((c for c in [r'C:\Program Files\Google\Chrome\Application\chrome.exe', '/usr/bin/google-chrome', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'] if pathlib.Path(c).exists()), 'google-chrome')
ROOT = pathlib.Path('.')
pages = sorted(p for p in ROOT.rglob('index.html') if not p.as_posix().startswith(('_', '.git')))
known = {'/' + p.as_posix()[:-len('index.html')].replace('./', '') for p in pages}
known = {('/' if u == '/.' else u.replace('/./', '/')) for u in known}
NAV_JS = re.compile(r"location\.(href|assign|replace)|window\.open\(|\.click\(\)|new Event\(['\"]click|setAttribute\(['\"]href|onclick=")
targets = []
for p in pages:
    h = p.read_text(encoding='utf-8'); url = '/' + p.as_posix()[:-len('index.html')]
    url = '/' if url == '/.' else url.replace('/./', '/')
    if '--all' in sys.argv or NAV_JS.search(h):
        targets.append(url)
print(f'{len(targets)} paginas con navegacion por JS: {targets}')
# servidor
with socket.socket() as s: s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]
handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT.resolve()))
class Q(http.server.ThreadingHTTPServer): pass
http.server.SimpleHTTPRequestHandler.log_message = lambda *a: None
srv = Q(('127.0.0.1', port), handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
runner = ROOT / '_clickaudit.html'
runner.write_text("""<body><script>
const TARGETS=%s, KNOWN=new Set(%s), out=[];
function norm(u){u=u.split('#')[0].split('?')[0];if(!u.endsWith('/'))u+='/';return u;}
function load(url){return new Promise(res=>{const f=document.createElement('iframe');f.style.cssText='width:1280px;height:900px;border:0';f.src=url;f.onload=()=>res(f);document.body.appendChild(f);});}
async function audit(url){
  let f=await load(url);let d=f.contentDocument,w=f.contentWindow;
  // candidatos: todo lo que parezca pulsable, incluidos los <a> (el click real puede pasar por JS)
  const sel='a,button,[onclick],[role=button],summary,[tabindex]';
  const all=[...d.querySelectorAll(sel)].concat([...d.querySelectorAll('*')].filter(e=>w.getComputedStyle(e).cursor==='pointer'&&!e.closest('a,button')));
  const cands=[...new Set(all)].filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0;});
  const n=cands.length;let checked=0;
  for(let i=0;i<n;i++){
    const e=cands[i];const label=(e.tagName+'.'+(e.className.baseVal||e.className||'')+' '+(e.getAttribute('href')||'')+' '+(e.textContent||'').trim().slice(0,30)).replace(/\\s+/g,' ');
    const tag=e.tagName.toLowerCase();
    if(tag==='a'){const h=e.getAttribute('href')||'';if(h.startsWith('http')||h.startsWith('tel:')||h.startsWith('mailto:'))continue;}
    try{e.dispatchEvent(new w.Event('mouseenter'));e.dispatchEvent(new w.Event('focus'));}catch(x){}
    await new Promise(r=>setTimeout(r,150));
    // si el hover ha mostrado un tooltip pulsable, pulsarlo tambien
    const tt=d.getElementById('mapTooltip');
    const clickables=(tt&&tt.classList.contains('on')?[tt]:[]).concat([e]);   // primero el tooltip, que desaparece si el elemento navega
    for(const c of clickables){
      const before=w.location.href;
      try{c.dispatchEvent(new w.MouseEvent('click',{bubbles:true,cancelable:true}));}catch(x){}
      // esperar a que la navegacion (si la hay) se materialice: cambia location o se sustituye el documento
      let after=before;for(let t=0;t<12;t++){await new Promise(r=>setTimeout(r,50));try{after=w.location.href;}catch(x){after='(cross-origin)';}if(after!==before||f.contentDocument!==d)break;}
      checked++;
      if(after!==before||f.contentDocument!==d){if(after===before){await new Promise(r=>setTimeout(r,300));try{after=w.location.href;}catch(x){}}
        const path=new URL(after).pathname;const ok=KNOWN.has(norm(path));
        if(!ok)out.push(`${url} :: ${c===tt?'TOOLTIP tras hover en ':''}${label} -> ${decodeURIComponent(path)} (NO EXISTE)`);
        f.remove();f=await load(url);d=f.contentDocument;w=f.contentWindow;
        const again=[...new Set([...d.querySelectorAll(sel)].concat([...d.querySelectorAll('*')].filter(e=>w.getComputedStyle(e).cursor==='pointer'&&!e.closest('a,button'))))].filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0;});
        cands.splice(0,cands.length,...again);
      }
    }
  }
  out.push(`${url}: ${checked} clicks probados`);f.remove();
}
(async()=>{for(const u of TARGETS)await audit(u);document.body.insertAdjacentHTML('beforeend','<pre id=r>'+out.join('\\n')+'</pre>');})();
</script>""" % (json.dumps(targets), json.dumps(sorted(known))), encoding='utf-8')
try:
    r = subprocess.run([CH, '--headless=new', '--disable-gpu', '--no-sandbox', '--virtual-time-budget=300000', '--dump-dom', f'http://127.0.0.1:{port}/_clickaudit.html'], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=600)
finally:
    runner.unlink(); srv.shutdown()
m = re.search(r'<pre id="r">(.*?)</pre>', r.stdout, re.S)
res = re.sub(r'<[^>]+>', '', m.group(1)) if m else '(sin resultado)'
res = res.replace('&gt;', '>').replace('&lt;', '<').replace('&amp;', '&')
print(res)
bad = [l for l in res.splitlines() if 'NO EXISTE' in l]
print('CLICKS ROTOS:', len(bad))
sys.exit(1 if bad else 0)
