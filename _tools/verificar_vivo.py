"""Verificacion del sitio EN VIVO (no del local): lo que solo se puede comprobar contra el servidor.

    python _tools/verificar_vivo.py [https://www.oficinasya.es]

1. Las paginas del sitemap: 200 sin redireccion, sin noindex (meta ni cabecera), canonical = su URL,
   y el HTML identico al del repositorio (si no, falta subir algo).
2. Las fuentes y lo que no se publica: 404 (o 403 en lo de .git). Desde fuera no se distingue
   "borrado" de "tapado por el .htaccess": eso se mira en el gestor de archivos.
3. Todas las redirecciones de _data/redirects.yml: 301, en un salto, al destino exacto, y el destino da 200.
4. Dominio, http y carpetas sin barra: en un salto.
5. Lo del tecnico y el cliente: enviar.php, enviar.config.php (sin mostrar su contenido), la verificacion de
   Google, la tienda (oficinavirtual) y OLD/ (que no ejecute PHP).
Sale con 1 si algo falla."""
import re, sys, os, pathlib, yaml, urllib.request, urllib.error
from urllib.parse import urlsplit, quote
from concurrent.futures import ThreadPoolExecutor
ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = (sys.argv[1] if len(sys.argv) > 1 else 'https://www.oficinasya.es').rstrip('/')
HOST = urlsplit(BASE).netloc
UA = {'User-Agent': 'Mozilla/5.0 (verificar_vivo)'}
errors, avisos = [], []


class _NoRedir(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k): return None
_op = urllib.request.build_opener(_NoRedir)


def get(url, body=True):
    """(codigo, cabeceras, cuerpo) sin seguir redirecciones."""
    req = urllib.request.Request(quote(url, safe=':/?#&=%'), headers=UA)
    for intento in range(3):
        try:
            r = _op.open(req, timeout=30)
            return r.status, r.headers, (r.read() if body else b'')
        except urllib.error.HTTPError as e:
            return e.code, e.headers, (e.read() if body else b'')
        except Exception as e:
            err = e
    return 0, {}, str(err).encode()


def cadena(url, max_saltos=10):
    """Sigue las redirecciones a mano: [(url, codigo)], y si hay bucle."""
    vistos, out = set(), []
    while len(out) <= max_saltos:
        c, h, _ = get(url, body=False)
        out.append((url, c))
        if c not in (301, 302, 303, 307, 308): return out, False
        loc = h.get('Location', '')
        url = loc if loc.startswith('http') else f'{urlsplit(url).scheme}://{urlsplit(url).netloc}{loc}'
        if url in vistos: return out + [(url, 'BUCLE')], True
        vistos.add(url)
    return out, True


# ---------- 1. paginas
sm = (ROOT / 'sitemap.xml').read_text(encoding='utf-8')
urls = [urlsplit(u).path for u in re.findall(r'<loc>([^<]+)</loc>', sm)]
def pagina(path):
    c, h, b = get(BASE + path)
    res = []
    if c != 200: return [f'pagina {path}: {c}'], []
    t = b.decode('utf-8', 'ignore')
    if 'noindex' in (h.get('X-Robots-Tag') or '').lower(): res.append(f'pagina {path}: X-Robots-Tag noindex')
    if re.search(r'<meta[^>]+name="robots"[^>]+noindex', t): res.append(f'pagina {path}: meta noindex')
    can = re.search(r'<link rel="canonical" href="([^"]+)"', t)
    if not can or can.group(1) != 'https://www.oficinasya.es' + path: res.append(f'pagina {path}: canonical {can and can.group(1)}')
    local = ROOT / path.lstrip('/') / 'index.html'
    av = [] if local.exists() and local.read_bytes() == b else [f'pagina {path}: el HTML en vivo no es el del repositorio (falta subirla)']
    return res, av
with ThreadPoolExecutor(6) as ex:
    for e, a in ex.map(pagina, urls): errors += e; avisos += a
print(f'1. paginas: {len(urls)} del sitemap comprobadas')

# ---------- 2. fuentes y ficheros que no se publican
FUENTES = ['/_build.py', '/_build.manifest', '/README.md', '/requirements.txt', '/datos-centros.csv', '/__b5.py',
           '/_data/global.yml', '/_data/redirects.yml', '/_content/servicios/alquiler-de-despachos.es.md',
           '/_templates/base.html', '/_tools/verificar.py', '/_docs/DESPLIEGUE.md', '/_hooks/pre-commit',
           '/fotos_nuevas/sanse.jpeg', '/.claude/settings.local.json', '/__pycache__/',
           '/_data/', '/_content/', '/_templates/', '/_tools/', '/_docs/', '/_hooks/', '/fotos_nuevas/', '/.claude/']
for f in FUENTES:
    c, _, b = get(BASE + f)
    if c != 404: errors.append(f'fuente {f}: {c} ({len(b)} bytes); debe ser 404')
for f in ['/.git/HEAD', '/.git/config', '/.gitignore']:
    c, _, b = get(BASE + f)
    if c not in (403, 404): errors.append(f'fuente {f}: {c}; debe ser 403 o 404')
print(f'2. fuentes: {len(FUENTES) + 3} rutas (404 = no se sirven; si estan borradas o solo tapadas se mira en el gestor)')

# ---------- 3. redirecciones
red = yaml.safe_load((ROOT / '_data' / 'redirects.yml').read_text(encoding='utf-8'))
site = 'https://www.oficinasya.es'
casos = []
for sec in ('prototipo', 'migracion', 'migracion_blog'):
    for r in red.get(sec) or []:
        frm = r['from']
        casos.append((frm, site + r['to']))
        alt = frm.rstrip('/') if frm.endswith('/') else frm + '/'
        if not frm.endswith('.html'): casos.append((alt, site + r['to']))
for r in red.get('patrones') or []:
    casos.append((r['match'] + 'prueba-verificar-vivo/', site + r['to']))
destinos_ok = {}
def redir(caso):
    frm, to = caso
    ch, bucle = cadena(BASE + frm)
    if bucle: return f'redireccion {frm}: BUCLE {ch}'
    if len(ch) != 2: return f'redireccion {frm}: {len(ch) - 1} saltos {ch}'
    c, h, _ = get(BASE + frm, body=False)
    loc = h.get('Location', '')
    if c != 301: return f'redireccion {frm}: {c} (debe ser 301)'
    if loc != to: return f'redireccion {frm}: -> {loc} (debe ir a {to})'
    if ch[-1][1] != 200: return f'redireccion {frm}: el destino {ch[-1][0]} da {ch[-1][1]}'
    return None
with ThreadPoolExecutor(6) as ex:
    fallos = [x for x in ex.map(redir, casos) if x]
errors += fallos
print(f'3. redirecciones: {len(casos)} casos ({len(red.get("patrones") or [])} prefijos, con y sin barra final); fallos: {len(fallos)}')

# ---------- 4. dominio, http, carpeta sin barra
for u, dest in [(f'https://oficinasya.es/alquiler-de-despachos/', f'{site}/alquiler-de-despachos/'),
                (f'{BASE}/blog', f'{site}/blog/'), (f'{BASE}/en', f'{site}/en/'),
                (f'https://oficinasya.es/despachos/', f'{site}/alquiler-de-despachos/')]:
    ch, bucle = cadena(u)
    if bucle or ch[-1][1] != 200 or ch[-1][0] != dest or len(ch) != 2:
        errors.append(f'salto {u}: {ch} (debe ser un salto a {dest})')
for u in ['http://www.oficinasya.es/', 'http://oficinasya.es/despachos/']:
    ch, bucle = cadena(u)
    if bucle or ch[-1][1] != 200: errors.append(f'http {u}: {ch}')
    elif len(ch) > 3: avisos.append(f'http {u}: {len(ch) - 1} saltos {ch}')
print('4. dominio, http y carpetas sin barra comprobados')

# ---------- 5. lo del tecnico y del cliente
c, _, b = get(BASE + '/enviar.php')
if c in (0, 404) or c >= 500: errors.append(f'enviar.php: {c}')
c, _, b = get(BASE + '/enviar.config.php')
if c == 200 and (b.strip() or b'<?' in b): errors.append(f'enviar.config.php: muestra {len(b)} bytes de contenido')
c, _, b = get(BASE + '/googlebe6fd46c002206cc.html')
if c != 200 or b'googlebe6fd46c002206cc' not in b: errors.append(f'verificacion de Google: {c}')
c, _, b = get('https://oficinavirtual.oficinasya.es/')
if c != 200 or b'Oficina Virtual' not in b: errors.append(f'tienda oficinavirtual.oficinasya.es: {c}')
c, _, b = get(BASE + '/oficinavirtual/wp-login.php')
if c != 200: errors.append(f'tienda /oficinavirtual/wp-login.php: {c}')
for f in ['/OLD/', '/OLD/index.php', '/OLD/wp-login.php', '/OLD/wp-config.php', '/OLD/xmlrpc.php']:
    c, _, b = get(BASE + f)
    # 404 de nuestro bloque, o 403 de una regla del servidor (wp-config.php la tiene): en los dos casos PHP no llega a
    # ejecutarse. Un 500, un 200 o un cuerpo grande querria decir que el WordPress viejo sigue respondiendo.
    if c not in (403, 404) or len(b) > 1000: errors.append(f'{f}: {c} ({len(b)} bytes); debe ser el 404/403 del servidor, sin PHP')
print('5. enviar.php, enviar.config.php, verificacion de Google, tienda y OLD/ comprobados')

for a in avisos: print('AVISO', a)
print('\n'.join(errors) if errors else 'SIN ERRORES')
sys.exit(1 if errors else 0)
