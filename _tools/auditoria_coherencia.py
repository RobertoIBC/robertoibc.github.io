"""2.3 coherencia de cifras y 2.4 idiomas, sobre el HTML generado (identico al publicado en HEAD)."""
import re, pathlib, os, json, collections, csv
os.chdir(pathlib.Path(__file__).resolve().parent.parent)   # raiz del repo
pages = sorted(p for p in pathlib.Path('.').rglob('index.html') if not p.as_posix().startswith(('_', '.git')))
def url(p):
    u = '/' + p.as_posix()[:-len('index.html')]; return '/' if u == '/.' else u.replace('/./', '/')
def visible(h):
    b = h[h.index('<body>'):]; b = re.sub(r'<script.*?</script>|<style.*?</style>', '', b, flags=re.S)
    return re.sub(r'\s+', ' ', re.sub('<[^>]+>', ' ', b))
docs = {url(p): p.read_text(encoding='utf-8') for p in pages}
# ---- 2.3 cifras en prosa
NUM = {'es': r'(treinta y \w+|cuarenta|veinte|diecis\w+|dieci\w+|quince|catorce|trece|doce|once|diez|nueve|ocho|siete|seis|cinco|cuatro|tres|dos)', 'en': r'(thirty-\w+|forty|twenty|nineteen|eighteen|seventeen|sixteen|fifteen|fourteen|thirteen|twelve|eleven|ten|nine|eight|seven|six|five|four|three|two)'}
KEYS = {'es': r'(centros?|espacios?|ciudades|colivings?|empresas|despachos)', 'en': r'(centres?|spaces?|cities|colivings?|companies|offices)'}
print('== 2.3 recuentos en prosa (numero + palabra clave), por pagina:')
counts = collections.Counter()
for u, h in docs.items():
    lang = 'en' if u.startswith('/en/') else 'es'
    t = visible(h)
    for m in re.finditer(r'(?i)\b(' + NUM[lang] + r'|\d{1,4})\s+' + KEYS[lang] + r'\b', t):
        phrase = m.group(0).lower()
        counts[(lang, phrase)] += 1
for (lang, phrase), n in sorted(counts.items()):
    print(f'   {lang} {n:3}x  {phrase}')
# suma por ciudad y contadores
rows = list(csv.DictReader(open('_data/centros.csv', encoding='utf-8')))
byc = collections.Counter(r['ciudad'] for r in rows)
print('== CSV:', len(rows), 'filas;', len(byc), 'ciudades;', 'colivings:', sum(1 for r in rows if 'coliving' in r['centro'].lower() or 'coliving' in r['servicios'].lower()))
hub = docs['/ubicaciones/']
map_counts = dict(re.findall(r'data-city="([^"]+)" data-count="(\d+) centro', hub))
print('   contadores del mapa:', sum(int(v) for v in map_counts.values()), '| difieren del CSV:', {k: (v, byc[k]) for k, v in map_counts.items() if int(v) != byc[k]})
fichas = {u: len(re.findall(r'<div class="centre(?: no-photo)?" id=', h)) for u, h in docs.items() if '/oficinas-en-' in u}
print('   fichas en paginas de ciudad ES:', sum(fichas.values()), {u.replace('/oficinas-en-', ''): n for u, n in fichas.items() if n != byc[[c for c in byc if re.sub(r'[^a-z]', '', c.lower().replace('ñ', 'n').replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')) == u.replace('/oficinas-en-', '').replace('/', '').replace('-', '')][0]]})
# precios en prosa
print('== precios que aparecen (€ con numero):')
prices = collections.Counter()
for u, h in docs.items():
    for m in re.finditer(r'(?:desde|from)\s*€?\s*([\d,.]+)\s*€?', visible(h), re.I): prices[m.group(1)] += 1
print('  ', dict(prices))
# ---- 2.4 idiomas: palabras españolas en paginas EN y viceversa (atributos y texto)
ES_WORDS = r'\b(despachos?|salas?|reuniones|ciudad(es)?|centros?|empresas?|precio|desde|llamar|contacto|enviar|nombre|teléfono|leer|artículo|ver|más|solicitud|horario|acceso|reserva)\b'
EN_WORDS = r'\b(offices?|rooms?|cities|companies|price|from|call|contact|send|name|phone|read|article|see|more|request|hours|access|booking)\b'
print('== 2.4 texto en el otro idioma (visible + alt/aria/placeholder/title/og:image:alt/JSON-LD):')
for u, h in docs.items():
    lang = 'en' if u.startswith('/en/') else 'es'
    attrs = ' '.join(re.findall(r'(?:alt|aria-label|placeholder|title|content)="([^"]*)"', h))
    ld = ' '.join(re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S))
    js = ' '.join(re.findall(r"textContent = '([^']*)'", h))
    text = visible(h) + ' ' + attrs + ' ' + js
    pat = ES_WORDS if lang == 'en' else EN_WORDS
    hits = collections.Counter(m.group(0).lower() for m in re.finditer(pat, text, re.I))
    # descartar nombres propios/URLs habituales
    for k in ('centro', 'ver', 'more', 'from', 'request', 'name'): hits.pop(k, None)
    if hits: print(f'   {u:45} {dict(hits.most_common(6))}')
# ---- palabras ES vs EN por pareja
print('== palabras ES vs EN por pareja (visible):')
pairs = []
for u, h in docs.items():
    if u.startswith('/en/'): continue
    alt = re.search(r'<link rel="alternate" hreflang="en" href="https://robertoibc.github.io([^"]+)"', h)
    if not alt or alt.group(1) not in docs: continue
    a, b = len(visible(h).split()), len(visible(docs[alt.group(1)]).split())
    pairs.append((u, a, b, round(b / a, 2)))
for u, a, b, r in sorted(pairs, key=lambda x: x[3]):
    flag = ' <<<' if r < 0.85 or r > 1.25 else ''
    print(f'   {u:35} ES {a:5}  EN {b:5}  ratio {r}{flag}')
