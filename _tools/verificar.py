"""Site-wide checks on the generated HTML: canonical/hreflang clusters, sitemap alternates,
JSON-LD validity, internal links, noindex, Jinja leftovers, title/description lengths."""
import re, json, pathlib, sys, os
os.chdir(pathlib.Path(__file__).resolve().parent.parent)   # raiz del repo
ROOT = pathlib.Path('.')
import yaml as _y
SITE = _y.safe_load(open('_data/global.yml', encoding='utf-8'))['site']['url'].rstrip('/')
pages = [p for p in ROOT.rglob('index.html') if not p.as_posix().startswith(('_', '.git'))]
errors, canon, rows = [], {}, []
_red = _y.safe_load(open('_data/redirects.yml', encoding='utf-8'))
REDIR_EXACTAS = {r['from'].rstrip('/') for k in ('prototipo', 'migracion', 'migracion_blog') for r in _red.get(k) or []}
REDIR_PREFIJOS = [r['match'] for r in _red.get('patrones') or []]
avisos = []
for p in pages:
    h = p.read_text(encoding='utf-8')
    url = '/' + p.as_posix()[:-len('index.html')]
    if url == '/.': url = '/'
    url = url.replace('/./', '/')
    if '{{' in h or '{%' in h: errors.append(f'{url}: jinja sin renderizar')
    c = re.search(r'<link rel="canonical" href="([^"]+)"', h).group(1)
    if c != SITE + url: errors.append(f'{url}: canonical {c}')
    alts = dict(re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"', h))
    canon[c] = alts
    if re.search(r'<meta property="og:url" content="([^"]+)"', h).group(1) != c: errors.append(f'{url}: og:url != canonical')
    NOINDEX = _y.safe_load(open('_data/global.yml', encoding='utf-8'))['site'].get('noindex')
    tiene = 'name="robots" content="noindex' in h
    if NOINDEX and not tiene: errors.append(f'{url}: falta noindex')
    if not NOINDEX and tiene: errors.append(f'{url}: noindex en produccion')
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
        try: j = json.loads(m.group(1))
        except Exception as e: errors.append(f'{url}: JSON-LD invalido: {e}'); continue
        for su in set(re.findall(r'"(' + re.escape(SITE) + r'[^"]*)"', m.group(1))):
            path = su[len(SITE):].split('#')[0]
            if path.startswith('/assets/'):
                if not (ROOT / path.lstrip('/')).exists(): errors.append(f'{url}: JSON-LD asset roto {su}')
            elif not (ROOT / path.lstrip('/') / 'index.html').exists(): errors.append(f'{url}: JSON-LD URL rota {su}')
    for m in re.findall(r"url\((['\"]?)([^)'\"]+)\1\)", h):
        u = m[1]
        if not u.startswith(('http', 'data:', '/', '#')): errors.append(f'{url}: url() relativa {u}')
        elif u.startswith('/') and not (ROOT / u.lstrip('/')).exists(): errors.append(f'{url}: url() rota {u}')
    for href in re.findall(r'(?:href|src)="(/[^"#]*)', h):
        if href.rstrip('/') in REDIR_EXACTAS and not (ROOT / href.lstrip('/') / 'index.html').exists():
            errors.append(f'{url}: enlace a {href}, que pasa por una redireccion (301): enlazar el destino final'); continue
        f = ROOT / href.lstrip('/')
        if href.endswith('/'): f = f / 'index.html'
        if not f.exists(): errors.append(f'{url}: enlace roto {href}')
    # enlaces absolutos al propio dominio en el cuerpo (los del <head> son canonical/hreflang/og, ya revisados)
    for su in set(re.findall(r'(?:href|src)="(' + re.escape(SITE) + r'[^"#?]*)', h[h.index('<body'):])):
        path = su[len(SITE):] or '/'
        f = ROOT / path.lstrip('/')
        if path.endswith('/'): f = f / 'index.html'
        if f.exists(): continue
        if path.rstrip('/') in REDIR_EXACTAS or any(path.startswith(x) for x in REDIR_PREFIJOS):
            errors.append(f'{url}: enlace a {path}, que pasa por una redireccion (301): enlazar el destino final')
        else:
            errors.append(f'{url}: enlace absoluto roto {su}')
    for href in re.findall(r'href="(/[^"]*#[^"]+)"', h):
        path, frag = href.split('#', 1)
        f = ROOT / path.lstrip('/') / 'index.html'
        if f.exists() and f'id="{frag}"' not in f.read_text(encoding='utf-8'):
            errors.append(f'{url}: ancla inexistente {href}')
    title = re.search(r'<title>(.*?)</title>', h).group(1)
    desc = re.search(r'<meta name="description" content="(.*?)" />', h).group(1)
    h1 = re.findall(r'<h1[^>]*>', h)
    rows.append((url, len(title), len(desc), len(h1)))
    if not 50 <= len(title) <= 60: errors.append(f'{url}: title {len(title)} chars')
    if not 140 <= len(desc) <= 160: errors.append(f'{url}: description {len(desc)} chars')
    if len(h1) != 1: errors.append(f'{url}: {len(h1)} h1')
# --- paginas huerfanas: enlaces entrantes desde otras paginas (total y sin cabecera/pie)
inbound = {u: set() for u in [c[len(SITE):] for c in canon]}
inbound_ctx = {u: set() for u in inbound}
for p in pages:
    h = p.read_text(encoding='utf-8')
    src = '/' + p.as_posix()[:-len('index.html')]
    src = '/' if src == '/.' else src.replace('/./', '/')
    body = h[h.index('<body>'):]
    nav_end = body.index('</div>', body.index('<div class="mobile-menu"')) if '<div class="mobile-menu"' in body else 0
    foot = body.index('<footer>') if '<footer>' in body else len(body)
    def targets(chunk):
        out = set()
        for href in re.findall(r'href="(/[^"#?]*)', chunk):
            u = href if href.endswith('/') else href + '/'
            if u in inbound and u != src: out.add(u)
        return out
    for u in targets(body): inbound[u].add(src)
    for u in targets(body[nav_end:foot]): inbound_ctx[u].add(src)
orphans = [u for u, v in inbound.items() if not v]
orphans_ctx = [u for u, v in inbound_ctx.items() if not v]
print(f'enlaces entrantes: minimo {min(len(v) for v in inbound.values())}, sin cabecera/pie minimo {min(len(v) for v in inbound_ctx.values())}')
if orphans: errors.append('HUERFANAS: ' + ', '.join(orphans))
print('sin enlace contextual (solo cabecera/pie):', orphans_ctx or 'ninguna')
for c, alts in canon.items():
    for lang, u in alts.items():
        if u not in canon: errors.append(f'{c}: hreflang {lang} -> {u} no es canonical')
        elif lang != 'x-default' and canon[u] != alts: errors.append(f'{c}: cluster distinto de {u}')
# ---- comprobaciones baratas anadidas en la pasada de entrega (16-09-2026)
ASSETS = {p.as_posix() for p in pathlib.Path('assets').rglob('*') if p.is_file()}
ES_LEAK = re.compile(r'\b(enviad[oa]|suscrit[oa]|despachos?|salas?|reuniones|ciudades|centros|empresas|precio|desde|llamar|contacto|enviar|nombre|tel[eé]fono|leer|art[ií]culo|solicitud|horario|acceso|reserva|recepci[oó]n|hasta)\b', re.I)
EN_LEAK = re.compile(r'\b(offices?|rooms?|cities|companies|price|call|contact|send|phone|read|article|request|hours|access|booking|reception|your|name)\b', re.I)
for p in pages:
    h = p.read_text(encoding='utf-8'); url = '/' + p.as_posix()[:-len('index.html')]; url = '/' if url == '/.' else url.replace('/./', '/')
    lang = 'en' if url.startswith('/en/') else 'es'
    # mayusculas/minusculas: GitHub Pages y Linux distinguen; Windows no
    for r in set(re.findall(r'(?:src|href)="(/assets/[^"#?]+)"', h)) | set(re.findall(r"url\('(/assets/[^']+)'\)", h)):
        if r.lstrip('/') not in ASSETS: errors.append(f'{url}: asset con nombre que no coincide exactamente: {r}')
    # texto pegado: dos elementos en linea seguidos sin espacio. En pantalla los separa el CSS (flex/gap), pero al
    # copiar, en lectores de pantalla y para Google se lee "desde8,50 €/hora+ IVA". Se excluye el logo (OficinasYA!
    # va junto) y la palabra partida por una negrita ("c</strong><strong>asi").
    cuerpo = re.sub(r'<script.*?</script>|<style.*?</style>|<svg.*?</svg>', '', h[h.index('<body'):], flags=re.S)
    for m in re.finditer(r'([\w€².)!?:»"])((?:</(?:span|b|strong|em|small|a|i|label)>)+)((?:<(?:span|b|strong|em|small|a|i|label)\b[^>]*>)+)([\w€+(«"¿¡])', cuerpo):
        if 'logo-ya' in m.group(3) or (m.group(1).isalpha() and m.group(4).islower()): continue
        izq = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', cuerpo[max(0, m.start() - 80):m.start() + 1])).strip()[-25:]
        der = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', cuerpo[m.end() - 1:m.end() + 60])).strip()[:25]
        errors.append(f'{url}: texto pegado sin espacio: "{izq.strip()}" + "{der.strip()}"')
    # las otras dos formas: palabra pegada a una etiqueta que se abre ("como<strong>Mi") o que se cierra ("</a></strong>que")
    _IN = r'(?:span|b|strong|em|small|a|i|label)'
    for m in re.finditer(r'([A-Za-zÁÉÍÓÚÑáéíóúñ]{2})((?:<' + _IN + r'\b[^>]*>)+)([A-ZÁÉÍÓÚÑa-záéíóúñ]{2})|([A-Za-zÁÉÍÓÚÑáéíóúñ]{2})((?:</' + _IN + r'>)+)([a-záéíóúñ]{2})', cuerpo):
        if 'logo-ya' in (m.group(2) or '') or 'class="ya"' in (m.group(2) or ''): continue
        txt = re.sub(r'<[^>]+>', '', m.group(0))
        errors.append(f'{url}: texto pegado sin espacio: "{txt}"')
    # animaciones sin @keyframes: el elemento se queda en su estado inicial (asi estuvo el boton de WhatsApp,
    # con opacidad 0, en 58 paginas: @keyframes up solo existia en cuatro plantillas)
    css_pag = ' '.join(re.findall(r'<style[^>]*>(.*?)</style>', h, re.S)) + ' ' + ' '.join(re.findall(r'style="([^"]*)"', h))
    definidas = set(re.findall(r'@keyframes\s+([\w-]+)', css_pag))
    for am in re.finditer(r'animation(?:-name)?\s*:\s*([^;}"]+)', css_pag):
        for tok in am.group(1).replace(',', ' ').split():
            if re.match(r'^[a-zA-Z][\w-]*$', tok) and tok not in ('forwards', 'backwards', 'both', 'none', 'infinite', 'ease', 'linear', 'alternate', 'reverse', 'normal', 'running', 'paused', 'ease-in', 'ease-out', 'ease-in-out', 'var') and tok not in definidas:
                errors.append(f'{url}: animacion "{tok}" sin @keyframes'); break
    for m in re.finditer(r'<img\b[^>]*>', h):
        if ' alt=' not in m.group(0): errors.append(f'{url}: <img> sin alt: {m.group(0)[:80]}')
    ids = re.findall(r'\sid="([^"]+)"', h)
    for d in sorted({i for i in ids if ids.count(i) > 1}): errors.append(f'{url}: id duplicado "{d}"')
    for m in re.finditer(r'<a\b[^>]*target="_blank"[^>]*>', h):
        if 'noopener' not in m.group(0): errors.append(f'{url}: _blank sin rel="noopener": {m.group(0)[:80]}')
    # fuga de idioma en atributos y mensajes de JS (el texto visible se revisa en auditoria_coherencia.py)
    attrs = ' '.join(re.findall(r'(?:alt|aria-label|placeholder)="([^"]*)"', h)) + ' ' + ' '.join(s for a in re.findall(r"textContent\s*=\s*([^;]+);", h) for s in re.findall(r"'([^']*)'", a))
    leak = (ES_LEAK if lang == 'en' else EN_LEAK).findall(attrs)
    leak = [x for x in leak if x.lower() not in ('contact', 'request')]   # nombres propios/plantilla compartidos
    if leak: errors.append(f'{url}: texto en el otro idioma en atributos/JS: {sorted(set(leak))[:5]}')
    # el sameAs de Organization debe coincidir con las redes del pie
    if url in ('/', '/en/'):
        same = set(re.findall(r'"sameAs":\s*\[(.*?)\]', h, re.S)[0].split('"')[1::2]) if '"sameAs"' in h else set()
        foot = {a or b for a, b in re.findall(r'class="soc"[^>]*href="([^"]+)"|href="([^"]+)" class="soc"', h)}
        if same and not foot: errors.append(f'{url}: hay sameAs pero no encuentro las redes del pie (class="soc")')
        elif same and same != foot: errors.append(f'{url}: sameAs del JSON-LD != redes del pie: {sorted(same ^ foot)}')
# las redirecciones con ancla (/oficinas-en-madrid/#serrano) llevan a un id que existe en su destino
_red = _y.safe_load((ROOT / '_data' / 'redirects.yml').read_text(encoding='utf-8'))
for _sec in ('prototipo', 'migracion', 'migracion_blog', 'patrones'):
    for _r in _red.get(_sec) or []:
        if '#' not in _r['to']: continue
        _p, _a = _r['to'].split('#', 1)
        _f = ROOT / _p.strip('/') / 'index.html' if _p.strip('/') else ROOT / 'index.html'
        if not _f.exists() or f'id="{_a}"' not in _f.read_text(encoding='utf-8'):
            errors.append(f'redirects.yml: {_r.get("from") or _r.get("match")} -> {_r["to"]}: ese ancla no existe en la pagina')
# la configuracion del servidor copiada en _docs/CONFIGURACION-SERVIDOR.md es la que genera _build.py
# (si se cambia redirects.yml y no se regenera el documento, el tecnico pegaria reglas viejas)
import subprocess
_doc = (ROOT / '_docs' / 'CONFIGURACION-SERVIDOR.md').read_text(encoding='utf-8').replace('\r\n', '\n')
for _lang, _flag in (('apache', '--htaccess'), ('nginx', '--nginx')):
    _gen = subprocess.run([sys.executable, str(ROOT / '_build.py'), _flag], capture_output=True, text=True, encoding='utf-8',
                          env=dict(os.environ, PYTHONIOENCODING='utf-8')).stdout.rstrip('\n')
    _m = re.search(r'```' + _lang + r'\n(.*?)\n```', _doc, re.S)
    if not _gen or not _m or _m.group(1) != _gen:
        errors.append(f'_docs/CONFIGURACION-SERVIDOR.md: el bloque {_lang} no coincide con `python _build.py {_flag}`: regenerarlo')
    # el mismo bloque, solo, para copiarlo y pegarlo en el gestor de archivos
    if _lang == 'apache':
        _txt = (ROOT / '_docs' / 'bloque-htaccess.txt').read_text(encoding='utf-8').replace('\r\n', '\n').rstrip('\n')
        if _txt != _gen: errors.append('_docs/bloque-htaccess.txt no coincide con `python _build.py --htaccess`: regenerarlo')
single = {c for c, a in canon.items() if not a}
sm = (ROOT / 'sitemap.xml').read_text(encoding='utf-8')
blocks = re.findall(r'<url>(.*?)</url>', sm, re.S)
for b in blocks:
    loc = re.search(r'<loc>([^<]+)', b).group(1)
    n_alt = len(re.findall(r'xhtml:link', b))
    if n_alt not in (0, 3): errors.append(f'sitemap {loc}: alternates != 3')
    if n_alt == 0 and loc not in single: errors.append(f'sitemap {loc}: sin alternates pero la pagina declara hreflang')
    if loc not in canon: errors.append(f'sitemap {loc}: no es canonical')
print(f'{len(pages)} paginas, {len(blocks)} en sitemap')
for r in sorted(rows): print(f'{r[0]:28} title {r[1]:3} desc {r[2]:3} h1 {r[3]}')
for a in avisos: print('AVISO', a)
print('\n'.join(errors) if errors else 'SIN ERRORES')
sys.exit(1 if errors else 0)
