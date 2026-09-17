"""Site-wide checks on the generated HTML: canonical/hreflang clusters, sitemap alternates,
JSON-LD validity, internal links, noindex, Jinja leftovers, title/description lengths."""
import re, json, pathlib, sys, os
os.chdir(pathlib.Path(__file__).resolve().parent.parent)   # raiz del repo
ROOT = pathlib.Path('.')
import yaml as _y
SITE = _y.safe_load(open('_data/global.yml', encoding='utf-8'))['site']['url'].rstrip('/')
pages = [p for p in ROOT.rglob('index.html') if not p.as_posix().startswith(('_', '.git'))]
errors, canon, rows = [], {}, []
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
    if 'name="robots" content="noindex' not in h: errors.append(f'{url}: falta noindex')
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
        f = ROOT / href.lstrip('/')
        if href.endswith('/'): f = f / 'index.html'
        if not f.exists(): errors.append(f'{url}: enlace roto {href}')
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
ES_LEAK = re.compile(r'\b(despachos?|salas?|reuniones|ciudades|centros|empresas|precio|desde|llamar|contacto|enviar|nombre|tel[eé]fono|leer|art[ií]culo|solicitud|horario|acceso|reserva|recepci[oó]n|hasta)\b', re.I)
EN_LEAK = re.compile(r'\b(offices?|rooms?|cities|companies|price|call|contact|send|phone|read|article|request|hours|access|booking|reception|your|name)\b', re.I)
for p in pages:
    h = p.read_text(encoding='utf-8'); url = '/' + p.as_posix()[:-len('index.html')]; url = '/' if url == '/.' else url.replace('/./', '/')
    lang = 'en' if url.startswith('/en/') else 'es'
    # mayusculas/minusculas: GitHub Pages y Linux distinguen; Windows no
    for r in set(re.findall(r'(?:src|href)="(/assets/[^"#?]+)"', h)) | set(re.findall(r"url\('(/assets/[^']+)'\)", h)):
        if r.lstrip('/') not in ASSETS: errors.append(f'{url}: asset con nombre que no coincide exactamente: {r}')
    for m in re.finditer(r'<img\b[^>]*>', h):
        if ' alt=' not in m.group(0): errors.append(f'{url}: <img> sin alt: {m.group(0)[:80]}')
    ids = re.findall(r'\sid="([^"]+)"', h)
    for d in sorted({i for i in ids if ids.count(i) > 1}): errors.append(f'{url}: id duplicado "{d}"')
    for m in re.finditer(r'<a\b[^>]*target="_blank"[^>]*>', h):
        if 'noopener' not in m.group(0): errors.append(f'{url}: _blank sin rel="noopener": {m.group(0)[:80]}')
    # fuga de idioma en atributos y mensajes de JS (el texto visible se revisa en auditoria_coherencia.py)
    attrs = ' '.join(re.findall(r'(?:alt|aria-label|placeholder)="([^"]*)"', h)) + ' ' + ' '.join(re.findall(r"textContent = '([^']*)'", h))
    leak = (ES_LEAK if lang == 'en' else EN_LEAK).findall(attrs)
    leak = [x for x in leak if x.lower() not in ('contact', 'request')]   # nombres propios/plantilla compartidos
    if leak: errors.append(f'{url}: texto en el otro idioma en atributos/JS: {sorted(set(leak))[:5]}')
    # el sameAs de Organization debe coincidir con las redes del pie
    if url in ('/', '/en/'):
        same = set(re.findall(r'"sameAs":\s*\[(.*?)\]', h, re.S)[0].split('"')[1::2]) if '"sameAs"' in h else set()
        foot = {a or b for a, b in re.findall(r'class="soc"[^>]*href="([^"]+)"|href="([^"]+)" class="soc"', h)}
        if same and foot and same != foot: errors.append(f'{url}: sameAs del JSON-LD != redes del pie: {sorted(same ^ foot)}')
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
print('\n'.join(errors) if errors else 'SIN ERRORES')
