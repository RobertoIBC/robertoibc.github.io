#!/usr/bin/env python3
"""Generador estatico de la web de OficinasYA!.

    python _build.py              genera todo el sitio (ES + EN) en la raiz del repo
    python _build.py --check      solo comprueba: falla si el sitio generado no coincide
    python _build.py --htaccess   imprime el bloque de 301 para el dia de la migracion

Fuentes:
    _data/global.yml      cifras, precios "desde", contacto, URL del sitio
    _data/i18n.yml        cadenas de cabecera y pie en cada idioma
    _data/centros.csv     los espacios de la red (sin precios)
    _data/redirects.yml   rutas antiguas -> nuevas
    _content/pages/       paginas a medida (home, hub, comunidad, blog, legales)
    _templates/           base.html, layouts/, partials/, assets/base.css y base.js

Salida: un index.html por URL (p. ej. /ubicaciones/index.html), sitemap.xml,
llms.txt y los stubs de redireccion. Idempotente: si nada cambia, no toca
ningun fichero.

No hay dependencias raras: Jinja2, PyYAML y Markdown (ver requirements.txt).
"""
import argparse
import csv
import pathlib
import re
import sys

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

ROOT = pathlib.Path(__file__).resolve().parent
DATA = ROOT / '_data'
CONTENT = ROOT / '_content'
TEMPLATES = ROOT / '_templates'

LANGS = ('es', 'en')
OG_LOCALE = {'es': 'es_ES', 'en': 'en_GB'}
DEFAULT_LANG = 'es'

# Orden y prioridad del sitemap por tipo de pagina
SITEMAP_PRIORITY = {'home': '1.0', 'ubicaciones': '0.9', 'comunidad': '0.7', 'blog': '0.6'}


# ---------------------------------------------------------------- utilidades
def read(path):
    return path.read_text(encoding='utf-8')


def write_if_changed(path, text):
    """Escribe solo si el contenido cambia: asi el generador es idempotente."""
    path = pathlib.Path(path)
    if path.exists() and read(path) == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8', newline='\n')
    return True


def front_matter(text):
    """Separa el front matter YAML (entre '---') del cuerpo."""
    m = re.match(r'^---\n(.*?)\n---\n', text, re.S)
    if not m:
        raise SystemExit('falta el front matter')
    return yaml.safe_load(m.group(1)), text[m.end():]


def fmt_price(value, lang):
    """8.5 -> '8,5' (es) / '8.50' (en); 270 -> '270' en los dos."""
    if float(value).is_integer():
        return str(int(value))
    return str(value).replace('.', ',') if lang == 'es' else f'{value:.2f}'


def json_price(value):
    return f'{float(value):.2f}'


def url_to_path(url):
    """'/ubicaciones/' -> 'ubicaciones/index.html'; '/' -> 'index.html'."""
    return (url.strip('/') + '/index.html').lstrip('/')


# ---------------------------------------------------------------- datos
def load_data():
    g = yaml.safe_load(read(DATA / 'global.yml'))
    i18n = yaml.safe_load(read(DATA / 'i18n.yml'))
    redirects = yaml.safe_load(read(DATA / 'redirects.yml'))
    with open(DATA / 'centros.csv', encoding='utf-8', newline='') as f:
        centros = [r for r in csv.DictReader(f) if r['activo'].strip().lower() == 'si']

    # Precios por centro: solo si el cliente lo ha aprobado Y la hoja privada existe.
    if g.get('publicar_precios_por_centro'):
        priv = ROOT / 'datos-centros.csv'
        if not priv.exists():
            raise SystemExit('publicar_precios_por_centro=true pero falta datos-centros.csv')
        with open(priv, encoding='utf-8', newline='') as f:
            precios = {(r['ciudad'], r['centro']): r for r in csv.DictReader(f)}
        for c in centros:
            c['precios'] = precios.get((c['ciudad'], c['centro']))
    return g, i18n, redirects, centros


def group_cities(centros):
    """Agrupa los centros por ciudad, en el orden del CSV, de mas a menos centros."""
    by = {}
    for c in centros:
        by.setdefault(c['ciudad'], []).append(c)
    ciudades = []
    for nombre, cs in by.items():
        ciudades.append({
            'nombre': nombre,
            'centros': cs,
            'tiene_coliving': any('coliving' in c['servicios'] for c in cs),
        })
    ciudades.sort(key=lambda c: (-len(c['centros']), c['nombre']))
    return ciudades


# ---------------------------------------------------------------- paginas
class Page(dict):
    """Un dict con acceso por atributo, para que las plantillas lean page.title."""
    def __getattr__(self, k):
        return self.get(k)


def load_pages():
    pages = []
    for path in sorted((CONTENT / 'pages').glob('*.html')):
        meta, body = front_matter(read(path))
        pages.append(Page(meta, body=body, source=path))
    # Comprobaciones de estructura: cada id tiene una version por idioma y URLs unicas
    urls = {}
    for p in pages:
        if p.lang not in LANGS:
            raise SystemExit(f'{p.source}: lang debe ser es o en')
        if p.url in urls:
            raise SystemExit(f'URL repetida {p.url}: {p.source} y {urls[p.url]}')
        urls[p.url] = p.source
    return pages


def page_order(pid):
    """Home, hub, comunidad, blog y despues el resto por orden alfabetico."""
    return (-float(SITEMAP_PRIORITY.get(pid, '0.2')), pid)


def link_alternates(pages, site_url):
    by_id = {}
    for p in sorted(pages, key=lambda p: page_order(p['id'])):
        by_id.setdefault(p['id'], {})[p.lang] = p
    for p in pages:
        group = by_id[p['id']]
        if set(group) != set(LANGS):
            raise SystemExit(f"la pagina '{p['id']}' no tiene version en los dos idiomas")
        p['abs_url'] = site_url + p.url
        p['og_locale'] = OG_LOCALE[p.lang]
        p['is_home'] = p['id'] == 'home'
        alts = [{'lang': l, 'url': site_url + group[l].url, 'og_locale': OG_LOCALE[l]} for l in LANGS]
        alts.append({'lang': 'x-default', 'url': site_url + group[DEFAULT_LANG].url, 'og_locale': None})
        p['alternates'] = alts
        p['pair'] = group
    return by_id


# ---------------------------------------------------------------- render
def make_env():
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES)),
        undefined=StrictUndefined,
        autoescape=False,          # el contenido es HTML de confianza, escrito por nosotros
        keep_trailing_newline=True,
    )
    env.filters['jsonprice'] = json_price
    return env


def build(check=False):
    g, i18n, redirects, centros = load_data()
    site = g['site']
    env = make_env()
    base_css = read(TEMPLATES / 'assets' / 'base.css').rstrip('\n')
    base_js = read(TEMPLATES / 'assets' / 'base.js').rstrip('\n')

    pages = load_pages()
    by_id = link_alternates(pages, site['url'])

    changed = []
    outputs = set()

    for p in pages:
        lang = p.lang
        urls = {pid: group[lang].url for pid, group in by_id.items()}
        prices = {k: fmt_price(v, lang) for k, v in g['precios'].items()}
        pair = p['pair']
        p['lang_links'] = [{
            'lang': l,
            'href': ('#hero' if p.is_home else p.url) if l == lang else pair[l].url,
            'current': l == lang,
            # el title va en el idioma de destino ("Read this page in English" en la ES)
            'title': '' if l == lang else i18n[lang]['lang_other_title'],
        } for l in LANGS]

        ctx = {
            'site': site, 'g': g, 'p': prices, 't': i18n[lang], 'page': p, 'urls': urls,
            'base_css': base_css, 'base_js': base_js, 'centros': centros,
        }
        # title y description tambien pueden usar {{ g.* }}
        p['title'] = env.from_string(p['title']).render(ctx)
        p['description'] = env.from_string(p['description']).render(ctx)

        src = f'{{% extends "layouts/{p.layout}.html" %}}\n' + p['body']
        html = env.from_string(src).render(ctx)
        out = ROOT / url_to_path(p.url)
        outputs.add(out)
        if check:
            if not out.exists() or read(out) != html:
                changed.append(out)
        elif write_if_changed(out, html):
            changed.append(out)

    # ---- sitemap.xml (solo paginas reales; los stubs de redireccion no van)
    def prio(p):
        return SITEMAP_PRIORITY.get(p['id'], '0.2') if p.lang == 'es' else \
            {'1.0': '0.9', '0.9': '0.8', '0.7': '0.6', '0.6': '0.5'}.get(SITEMAP_PRIORITY.get(p['id'], '0.2'), '0.2')

    order = {pid: i for i, pid in enumerate(by_id)}
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<!--',
          '  Generado por _build.py a partir de _content/. No editar a mano.',
          '  NO se referencia desde robots.txt mientras el sitio viva en el prototipo:',
          '  el prototipo va noindex y no queremos invitar a su indexacion.',
          '  TODO migracion: cambiar site.url en _data/global.yml y declararlo en robots.txt.',
          '-->',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
          '        xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for p in sorted(pages, key=lambda p: (p.lang != DEFAULT_LANG, order[p['id']])):
        sm.append(f'  <url><loc>{p.abs_url}</loc><priority>{prio(p)}</priority>')
        for a in p.alternates:
            sm.append(f'    <xhtml:link rel="alternate" hreflang="{a["lang"]}" href="{a["url"]}"/>')
        sm[-1] += '</url>'
    sm.append('</urlset>\n')
    sitemap = '\n'.join(sm)

    # ---- llms.txt
    ciudades = group_cities(centros)
    pares = [{'es': grp['es'].url, 'en': grp['en'].url} for grp in by_id.values()]
    llms = env.get_template('llms.txt').render(
        site=site, g=g, p={k: fmt_price(v, 'es') for k, v in g['precios'].items()},
        ciudades=ciudades, pares=pares,
        n_centros=sum(1 for c in centros if 'coliving' not in c['servicios']),
        n_colivings=sum(1 for c in centros if 'coliving' in c['servicios']),
    )

    # ---- stubs de redireccion del prototipo
    redirect_tpl = env.get_template('redirect.html')
    extra = {ROOT / 'sitemap.xml': sitemap, ROOT / 'llms.txt': llms}
    for r in redirects['prototipo']:
        extra[ROOT / r['from'].lstrip('/')] = redirect_tpl.render(site=site, to=r['to'])

    for out, text in extra.items():
        outputs.add(out)
        if check:
            if not out.exists() or read(out) != text:
                changed.append(out)
        elif write_if_changed(out, text):
            changed.append(out)

    return changed, outputs


def print_htaccess(redirects, site):
    print('# Redirecciones 301 generadas por _build.py --htaccess')
    print('# Pegar en .htaccess (Apache) o importar en el plugin Redirection.')
    for section in ('prototipo', 'migracion'):
        print(f'\n# --- {section}')
        for r in redirects[section]:
            print(f'Redirect 301 {r["from"]} {r["to"]}')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true', help='no escribe; falla si algo esta desactualizado')
    ap.add_argument('--htaccess', action='store_true', help='imprime las redirecciones 301 para la migracion')
    args = ap.parse_args()

    if args.htaccess:
        g, _, redirects, _ = load_data()
        print_htaccess(redirects, g['site'])
        return

    changed, outputs = build(check=args.check)
    rel = lambda p: p.relative_to(ROOT).as_posix()
    if args.check:
        if changed:
            print('DESACTUALIZADO:\n  ' + '\n  '.join(rel(c) for c in changed))
            sys.exit(1)
        print(f'OK: {len(outputs)} ficheros al dia')
    else:
        print(f'{len(outputs)} ficheros generados, {len(changed)} cambiados' +
              (':\n  ' + '\n  '.join(rel(c) for c in changed) if changed else ''))


if __name__ == '__main__':
    main()
