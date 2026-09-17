"""2.1: todos los href/src de las 66 paginas PUBLICADAS (a, link, img, script, svg, style url(), JSON-LD, og),
codigo de respuesta de cada uno, anclas, pares de idioma, wa.me, tel:, mailto:."""
import re, json, urllib.request, urllib.parse, sys, collections, html as htmlmod, concurrent.futures, os, pathlib
os.chdir(pathlib.Path(__file__).resolve().parent.parent)   # raiz del repo
import yaml as _y
B = _y.safe_load(open('_data/global.yml', encoding='utf-8'))['site']['url'].rstrip('/')
UA = {'User-Agent': 'Mozilla/5.0 (auditoria)', 'Cache-Control': 'no-cache'}
def fetch(u, head=False):
    try:
        req = urllib.request.Request(u, headers=UA, method='HEAD' if head else 'GET')
        r = urllib.request.urlopen(req, timeout=30)
        return r.status, (r.read().decode('utf-8', 'replace') if not head else '')
    except urllib.error.HTTPError as e:
        return e.code, ''
    except Exception as e:
        return str(e)[:40], ''
sm = fetch(B + '/sitemap.xml')[1]
urls = re.findall(r'<loc>([^<]+)</loc>', sm)
pages = {}
for u in urls:
    st, h = fetch(u); pages[u] = h
print(f'{len(pages)} paginas descargadas')
refs = collections.defaultdict(set)   # ref -> paginas
anchors_needed = collections.defaultdict(set)
ids = {}
wa, tel, mail = {}, set(), set()
for u, h in pages.items():
    ids[u] = set(re.findall(r'\sid="([^"]+)"', h))
    found = set()
    found |= set(re.findall(r'\s(?:href|src|content|poster)="([^"]+)"', h))
    found |= set(re.findall(r"url\(['\"]?([^'\")]+)['\"]?\)", h))
    for ld in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
        found |= set(re.findall(r'"(https?://[^"]+)"', ld))
    for r in found:
        r = htmlmod.unescape(r)
        if r.startswith('data:') or r in ('#', ''): continue
        if r.startswith('https://wa.me/'): wa[(u, r)] = 1; continue
        if r.startswith('tel:'): tel.add((u, r)); continue
        if r.startswith('mailto:'): mail.add((u, r)); continue
        if r.startswith('#'): anchors_needed[u].add(r[1:]); continue
        if r.startswith('/'):
            if '#' in r:
                path, frag = r.split('#', 1); anchors_needed[B + path].add(frag); r = path
            refs[B + r].add(u)
        elif r.startswith('http'):
            if '#' in r and r.startswith(B):
                path, frag = r.split('#', 1); anchors_needed[path].add(frag); r = path
            refs[r].add(u)
        else:
            refs['RELATIVO: ' + r].add(u)
print(f'{len(refs)} destinos distintos')
internal = [r for r in refs if r.startswith(B)]; external = [r for r in refs if r.startswith('http') and not r.startswith(B)]; relative = [r for r in refs if r.startswith('RELATIVO')]
with concurrent.futures.ThreadPoolExecutor(12) as ex:
    codes = dict(zip(internal + external, ex.map(lambda r: fetch(r, head=False)[0] if r.startswith(B) else fetch(r, head=True)[0], internal + external)))
bad_int = [(r, codes[r], sorted(refs[r])[:2]) for r in internal if codes[r] != 200]
bad_ext = [(r, codes[r], len(refs[r])) for r in external if codes[r] != 200]
print('\n== internos:', len(internal), 'con problema:', len(bad_int)); [print('  ', x) for x in bad_int]
print('== externos:', len(external)); [print('  ', x) for x in bad_ext] or print('   todos 200')
print('== relativos (deberian ser 0):', relative[:5])
# anclas
missing = []
for page, frags in anchors_needed.items():
    if page not in pages: continue
    for f in frags:
        if f and f not in ids[page]: missing.append((page.replace(B, ''), f))
print('== anclas que no existen en su destino:', missing or 'ninguna')
# pares de idioma: el selector ES|EN
pair_bad = []
for u, h in pages.items():
    for lang, href in re.findall(r'<a href="([^"]+)" hreflang="(es|en)"', h)[:0]: pass
    for href, lang in re.findall(r'<a href="([^"]+)" hreflang="(es|en)" lang="\2"', h):
        target = href if href.startswith('http') else (u if href.startswith('#') else B + href)
        alt = re.search(rf'<link rel="alternate" hreflang="{lang}" href="([^"]+)"', h)
        expected = alt.group(1) if alt else None
        if expected and target.split('#')[0] != expected: pair_bad.append((u.replace(B, ''), lang, href, expected.replace(B, '')))
print('== selector de idioma que no lleva a la gemela declarada:', pair_bad or 'ninguno')
# wa.me
print('== wa.me:', len(wa), 'enlaces;', len({r for _, r in wa}), 'mensajes distintos')
msgs = sorted({r for _, r in wa})
for r in msgs:
    q = urllib.parse.urlparse(r).query; t = urllib.parse.parse_qs(q).get('text', [''])[0]
    bad = ('%' in t) or any(ord(c) > 127 and c not in 'áéíóúñÁÉÍÓÚÑü' for c in t)
    print(f'   {"!!" if bad else "  "} {r.split("?")[0][-15:]} :: {t}')
print('== tel:', sorted({r for _, r in tel})); print('== mailto:', sorted({r for _, r in mail}))
