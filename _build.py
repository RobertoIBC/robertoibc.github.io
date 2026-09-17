#!/usr/bin/env python3
"""Generador estatico de la web de OficinasYA!.

    python _build.py              genera todo el sitio (ES + EN) en la raiz del repo
    python _build.py --check      solo comprueba: falla si el sitio generado no coincide
    python _build.py --htaccess   imprime el bloque de 301 para el dia de la migracion

Fuentes:
    _data/global.yml      cifras, precios "desde", contacto, URL del sitio
    _data/i18n.yml        cadenas de cabecera y pie en cada idioma
    _data/centros.csv     los espacios de la red (sin precios)
    _data/ciudades.yml    nombres y slugs de las ciudades
    _data/redirects.yml   rutas antiguas -> nuevas
    _content/pages/       paginas a medida (home, hub, comunidad, blog, legales): HTML
    _content/servicios/   paginas de servicio: Markdown con front matter
    _content/ciudades/    paginas de ciudad: Markdown con front matter (fase 4)
    _templates/           base.html, layouts/, partials/, assets/base.css y base.js

Salida: un index.html por URL (p. ej. /ubicaciones/index.html), sitemap.xml,
llms.txt y los stubs de redireccion. Idempotente: si nada cambia, no toca
ningun fichero.

No hay dependencias raras: Jinja2, PyYAML y Markdown (ver requirements.txt).
"""
import argparse
import csv
import json
import pathlib
import re
import sys

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

ROOT = pathlib.Path(__file__).resolve().parent
DATA = ROOT / '_data'
CONTENT = ROOT / '_content'
TEMPLATES = ROOT / '_templates'

LANGS = ('es', 'en')
OG_LOCALE = {'es': 'es_ES', 'en': 'en_GB'}
LANG_TAG = {'es': 'es-ES', 'en': 'en-GB'}
DEFAULT_LANG = 'es'
HOME = {'es': '/', 'en': '/en/'}

# Prioridad del sitemap por tipo de pagina; el resto va a 0.2 (legales) o
# a lo que diga SITEMAP_PRIORITY_BY_LAYOUT.
SITEMAP_PRIORITY = {'home': '1.0', 'ubicaciones': '0.9', 'comunidad': '0.7', 'blog': '0.6'}
SITEMAP_PRIORITY_BY_LAYOUT = {'servicio': '0.8', 'ciudad': '0.8', 'articulo': '0.5'}

# Claves de la columna `servicios` de centros.csv que cuentan como cada servicio
SERVICE_KEYS = {
    'despachos': 'despachos',
    'salas': 'salas de reuniones',
    'smart_office': 'smart office',
    'coworking': 'coworking',
    'eventos': 'eventos',
    'aula': 'aula',
    'coliving': 'coliving',
}


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


def front_matter(text, source):
    """Separa el front matter YAML (entre '---') del cuerpo."""
    m = re.match(r'^---\n(.*?)\n---\n', text, re.S)
    if not m:
        raise SystemExit(f'{source}: falta el front matter')
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


def to_jsonld(obj):
    """JSON-LD legible, con tildes tal cual y sangria de dos espacios."""
    return json.dumps(obj, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------- datos
def load_data():
    g = yaml.safe_load(read(DATA / 'global.yml'))
    i18n = yaml.safe_load(read(DATA / 'i18n.yml'))
    redirects = yaml.safe_load(read(DATA / 'redirects.yml'))
    ciudades = yaml.safe_load(read(DATA / 'ciudades.yml'))
    horarios = yaml.safe_load(read(DATA / 'horarios.yml')) or {}
    with open(DATA / 'centros.csv', encoding='utf-8', newline='') as f:
        centros = [r for r in csv.DictReader(f) if r['activo'].strip().lower() == 'si']

    nombres = {c['nombre'] for c in ciudades}
    for c in centros:
        if c['ciudad'] not in nombres:
            raise SystemExit(f"centros.csv: la ciudad '{c['ciudad']}' no esta en ciudades.yml")
        c['acceso_24h'] = '24' in c['horario']
        c['opening_hours'] = horarios.get(f"{c['ciudad']}|{c['centro']}")
        c['address'] = parse_address(c['direccion'], c['ciudad'])
        c['tags'] = [t.strip() for t in c['servicios'].split(',') if t.strip()]

    # Precios por centro: solo si el cliente lo ha aprobado Y la hoja privada existe.
    if g.get('publicar_precios_por_centro'):
        priv = ROOT / 'datos-centros.csv'
        if not priv.exists():
            raise SystemExit('publicar_precios_por_centro=true pero falta datos-centros.csv')
        with open(priv, encoding='utf-8', newline='') as f:
            precios = {(r['ciudad'], r['centro']): r for r in csv.DictReader(f)}
        for c in centros:
            c['precios'] = precios.get((c['ciudad'], c['centro']))
    return g, i18n, redirects, ciudades, centros


def parse_address(direccion, ciudad):
    """'Calle Mayor 22, entreplanta, 02001 Albacete' -> calle, CP y localidad.
    Si no hay codigo postal, la localidad es la ciudad y el CP se omite."""
    m = re.search(r'\b(\d{5})\b\s*([^,]*)', direccion)
    if m:
        street = direccion[:m.start()].rstrip(', ')
        locality = m.group(2).strip() or ciudad
        return {'streetAddress': street, 'postalCode': m.group(1), 'addressLocality': locality}
    parts = [x.strip() for x in direccion.split(',')]
    if len(parts) > 1 and parts[-1] in (ciudad, ciudad.split(' (')[0]):
        return {'streetAddress': ', '.join(parts[:-1]), 'addressLocality': parts[-1]}
    return {'streetAddress': direccion, 'addressLocality': ciudad}


def group_cities(ciudades, centros):
    """Una entrada por ciudad con sus centros, de mas a menos centros."""
    out = []
    for c in ciudades:
        cs = [x for x in centros if x['ciudad'] == c['nombre']]
        if not cs:
            continue
        out.append({**c, 'centros': cs,
                    'tiene_coliving': any('coliving' in x['servicios'] for x in cs)})
    out.sort(key=lambda c: (-len(c['centros']), c['nombre']))
    return out


def service_counts(centros):
    return {k: sum(1 for c in centros if key in c['servicios']) for k, key in SERVICE_KEYS.items()}


# ---------------------------------------------------------------- paginas
class Page(dict):
    """Un dict con acceso por atributo, para que las plantillas lean page.title."""
    def __getattr__(self, k):
        return self.get(k)


def load_pages():
    pages, posts = [], []
    for path in sorted(CONTENT.rglob('*')):
        if path.suffix not in ('.html', '.md') or not path.is_file():
            continue
        meta, body = front_matter(read(path), path)
        page = Page(meta, body=body, source=path, kind=path.suffix[1:])
        if path.parent.name == 'blog':
            # Articulo del blog. Obligatorio: id, lang, titulo, fecha, categoria, resumen.
            for k in ('id', 'lang', 'titulo', 'fecha', 'categoria', 'resumen'):
                if not page.get(k):
                    raise SystemExit(f'{path}: falta "{k}" en el front matter del articulo')
            page['fecha'] = str(page['fecha'])
            if page.get('enlace') and page.get('url'):
                raise SystemExit(f'{path}: un articulo tiene enlace externo O url propia, no los dos')
            if page.get('url'):
                page.setdefault('layout', 'articulo')
                page.setdefault('title', page['titulo'] + ' | OficinasYA!')
                page.setdefault('description', page['resumen'])
                page.setdefault('h1', page['titulo'])
                pages.append(page)
            posts.append(page)
            continue
        pages.append(page)
    urls = {}
    for p in pages:
        for k in ('id', 'lang', 'url', 'layout', 'title', 'description'):
            if not p.get(k):
                raise SystemExit(f'{p.source}: falta "{k}" en el front matter')
        if p.lang not in LANGS:
            raise SystemExit(f'{p.source}: lang debe ser es o en')
        if p.url in urls:
            raise SystemExit(f'URL repetida {p.url}: {p.source} y {urls[p.url]}')
        urls[p.url] = p.source
    return pages, posts


SERVICE_ORDER = ['srv-despachos', 'srv-salas', 'srv-oficina-virtual', 'srv-coworking']


def page_order(p):
    """Home, hub, comunidad, blog, servicios (en su orden), ciudades y despues el resto."""
    prio = SITEMAP_PRIORITY.get(p['id']) or SITEMAP_PRIORITY_BY_LAYOUT.get(p.layout, '0.2')
    srv = SERVICE_ORDER.index(p['id']) if p['id'] in SERVICE_ORDER else 99
    return (-float(prio), p.layout, srv, p['id'])


def link_alternates(pages, site_url, warnings):
    by_id = {}
    for p in sorted(pages, key=page_order):
        by_id.setdefault(p['id'], {})[p.lang] = p
    for p in pages:
        group = by_id[p['id']]
        missing = [l for l in LANGS if l not in group]
        if missing:
            warnings.append(f"'{p['id']}' no tiene version en {', '.join(missing)}: se publica solo en {p.lang}")
        p['abs_url'] = site_url + p.url
        p['og_locale'] = OG_LOCALE[p.lang]
        p['is_home'] = p['id'] == 'home'
        if len(group) < 2:
            alts = []   # sin pareja no hay hreflang que declarar (ni siquiera x-default)
        else:
            alts = [{'lang': l, 'url': site_url + group[l].url, 'og_locale': OG_LOCALE[l]} for l in LANGS if l in group]
            xdef = group.get(DEFAULT_LANG) or p
            alts.append({'lang': 'x-default', 'url': site_url + xdef.url, 'og_locale': None})
        p['alternates'] = alts
        p['pair'] = group
    return by_id


# ---------------------------------------------------------------- JSON-LD de las paginas Markdown
def jsonld_servicio(p, g, site, lang, prices, ciudades_disp, i18n):
    url = site['url']
    offers = []
    for o in p.get('ofertas') or []:
        offers.append({
            '@type': 'Offer',
            'name': o['nombre'],
            'description': o.get('detalle', ''),
            'url': p['abs_url'],
            'priceCurrency': 'EUR',
            'price': json_price(g['precios'][o['precio']]),
            'priceSpecification': {
                '@type': 'UnitPriceSpecification',
                'price': json_price(g['precios'][o['precio']]),
                'priceCurrency': 'EUR',
                'unitCode': o['unit_code'],
                'valueAddedTaxIncluded': False,
            },
            'availability': 'https://schema.org/InStock',
        })
    service = {
        '@type': 'Service',
        '@id': p['abs_url'] + '#service',
        'name': p['h1'],
        'serviceType': p['service_type'],
        'description': p['description'],
        'url': p['abs_url'],
        'inLanguage': LANG_TAG[lang],
        'provider': {'@id': url + '/#organization'},
        'areaServed': [{'@type': 'City', 'name': c['nombre' if lang == 'es' else 'nombre_en']} for c in ciudades_disp],
    }
    if offers:
        service['offers'] = offers
    if p.get('galeria'):   # fotos reales de la galeria de la pagina, como ImageObject
        service['image'] = [{'@type': 'ImageObject', 'contentUrl': url + g_['foto'], 'url': url + g_['foto'], 'caption': f"{g_['titulo']} · {g_['sub']}",
                             'description': g_['alt'], 'width': 900, 'height': 600} for g_ in p['galeria']]
    graph = [
        service,
        {
            '@type': 'WebPage',
            '@id': p['abs_url'],
            'url': p['abs_url'],
            'name': p['title'],
            'description': p['description'],
            'inLanguage': LANG_TAG[lang],
            'isPartOf': {'@id': url + '/#website'},
            'about': {'@id': p['abs_url'] + '#service'},
        },
        {
            '@type': 'BreadcrumbList',
            'itemListElement': [
                {'@type': 'ListItem', 'position': 1, 'name': i18n['breadcrumb_home'], 'item': url + HOME[lang]},
                {'@type': 'ListItem', 'position': 2, 'name': p['h1'], 'item': p['abs_url']},
            ],
        },
    ]
    if p.get('faq'):
        graph.append({
            '@type': 'FAQPage',
            '@id': p['abs_url'] + '#faq',
            'mainEntity': [{
                '@type': 'Question',
                'name': q['q'],
                'acceptedAnswer': {'@type': 'Answer', 'text': q['a']},
            } for q in p['faq']],
        })
    return {'@context': 'https://schema.org', '@graph': graph}


def jsonld_ciudad(p, g, site, lang, i18n, city, centros_ciudad, urls):
    url = site['url']
    name = city['nombre' if lang == 'es' else 'nombre_en']
    items = []
    for i, c in enumerate(centros_ciudad, 1):
        lb = {
            '@type': 'LocalBusiness',
            '@id': p['abs_url'] + '#' + c['anchor'],
            'name': f"OficinasYA! {c['ciudad']} — {c['centro']}",
            'description': c.get('descripcion_corta') or f"Centro de negocios de la red OficinasYA! en {c['ciudad']}.",
            'url': p['abs_url'] + '#' + c['anchor'],
            'telephone': g['tel_e164'],
            'parentOrganization': {'@id': url + '/#organization'},
            'address': {'@type': 'PostalAddress', **c['address'], 'addressCountry': 'ES'},
        }
        if c.get('opening_hours'):
            lb['openingHoursSpecification'] = c['opening_hours']
        if c.get('web'):
            lb['sameAs'] = c['web']
        if c.get('foto'):
            lb['image'] = url + c['foto'] if c['foto'].startswith('/') else c['foto']
        items.append({'@type': 'ListItem', 'position': i, 'item': lb})
    graph = [
        {
            '@type': 'WebPage',
            '@id': p['abs_url'],
            'url': p['abs_url'],
            'name': p['title'],
            'description': p['description'],
            'inLanguage': LANG_TAG[lang],
            'isPartOf': {'@id': url + '/#website'},
            'about': {'@id': url + '/#organization'},
            **({'primaryImageOfPage': {'@type': 'ImageObject', 'contentUrl': url + p['hero_foto'], 'url': url + p['hero_foto'],
                                       'caption': p.get('hero_caption', ''), 'description': p.get('hero_alt', ''), 'width': 1400, 'height': 800,
                                       'representativeOfPage': True}} if p.get('hero_foto') else {}),
        },
        {
            '@type': 'BreadcrumbList',
            'itemListElement': [
                {'@type': 'ListItem', 'position': 1, 'name': i18n['breadcrumb_home'], 'item': url + HOME[lang]},
                {'@type': 'ListItem', 'position': 2, 'name': i18n['ciudad']['locations'], 'item': url + urls['ubicaciones']},
                {'@type': 'ListItem', 'position': 3, 'name': name, 'item': p['abs_url']},
            ],
        },
        {
            '@type': 'ItemList',
            'name': i18n['ciudad']['centres_title'].replace('{ciudad}', name),
            'numberOfItems': len(items),
            'itemListElement': items,
        },
    ]
    if p.get('faq'):
        graph.append({
            '@type': 'FAQPage',
            '@id': p['abs_url'] + '#faq',
            'mainEntity': [{'@type': 'Question', 'name': q['q'],
                            'acceptedAnswer': {'@type': 'Answer', 'text': q['a']}} for q in p['faq']],
        })
    return {'@context': 'https://schema.org', '@graph': graph}


def tag_order(tag):
    order = list(SERVICE_KEYS.values())
    return order.index(tag) if tag in order else 99


def jsonld_hub(p, site, lang, i18n, cities, urls):
    url = site['url']
    return {'@context': 'https://schema.org', '@graph': [
        {'@type': 'WebPage', '@id': p['abs_url'], 'url': p['abs_url'], 'name': p['title'],
         'description': p['description'], 'inLanguage': LANG_TAG[lang],
         'isPartOf': {'@id': url + '/#website'}, 'about': {'@id': url + '/#organization'}},
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': i18n['breadcrumb_home'], 'item': url + HOME[lang]},
            {'@type': 'ListItem', 'position': 2, 'name': i18n['ciudad']['locations'], 'item': p['abs_url']}]},
        {'@type': 'ItemList', 'name': p['h1'] if p.get('h1') else p['title'], 'numberOfItems': len(cities),
         'itemListElement': [{'@type': 'ListItem', 'position': i, 'name': c['label'], 'url': url + c['url']}
                             for i, c in enumerate(cities, 1)]},
    ]}


MESES = {'es': ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'],
         'en': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']}


def fecha_legible(iso, lang):
    y, m, d = iso.split('-')
    return f'{int(d)} {MESES[lang][int(m) - 1]} {y}' if lang == 'es' else f'{int(d)} {MESES[lang][int(m) - 1]} {y}'


def blogposting(a, site, lang, href):
    if a.get('otro_idioma'):
        lang = DEFAULT_LANG   # el articulo enlazado esta en el idioma por defecto
    node = {'@type': 'BlogPosting', 'headline': a['titulo'], 'datePublished': a['fecha'], 'description': a['resumen'],
            'inLanguage': LANG_TAG[lang], 'url': href,
            'author': {'@id': site['url'] + '/#organization'}, 'publisher': {'@id': site['url'] + '/#organization'}}
    if a.get('imagen'):
        node['image'] = a['imagen'] if a['imagen'].startswith('http') else site['url'] + a['imagen']
    return node


def jsonld_blog(p, site, lang, i18n, posts):
    url = site['url']
    return {'@context': 'https://schema.org', '@graph': [
        {'@type': 'Blog', '@id': p['abs_url'] + '#blog', 'url': p['abs_url'], 'name': p['title'],
         'description': p['description'], 'inLanguage': LANG_TAG[lang],
         'publisher': {'@id': url + '/#organization'},
         'blogPost': [blogposting(a, site, lang, a['href'] if a['externo'] else url + a['href']) for a in posts]},
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': i18n['breadcrumb_home'], 'item': url + HOME[lang]},
            {'@type': 'ListItem', 'position': 2, 'name': i18n['nav']['blog'], 'item': p['abs_url']}]},
    ]}


def jsonld_articulo(p, site, lang, i18n, urls):
    url = site['url']
    node = blogposting(p, site, lang, p['abs_url'])
    node.update({'@id': p['abs_url'] + '#article', 'mainEntityOfPage': p['abs_url'],
                 'isPartOf': {'@id': url + urls['blog'] + '#blog'}})
    if p.get('actualizado'):
        node['dateModified'] = str(p['actualizado'])
    return {'@context': 'https://schema.org', '@graph': [node,
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': i18n['breadcrumb_home'], 'item': url + HOME[lang]},
            {'@type': 'ListItem', 'position': 2, 'name': i18n['nav']['blog'], 'item': url + urls['blog']},
            {'@type': 'ListItem', 'position': 3, 'name': p['titulo'], 'item': p['abs_url']}]}]}


# Los datos de ficha (horario, salas, despachos) vienen del CSV en espanol y el cliente los mantiene
# ahi. Para la version inglesa se traducen por tokens al generar; nada que escribir en el CSV.
# "Centro autonomo" se traduce sin afirmar ni negar recepcion (acordado para Albacete).
FACT_TOKENS_EN = [
    (r'Recepci[oó]n', 'Reception'), (r'Centro aut[oó]nomo', 'Autonomous centre'),
    (r'clientes acceso 24/7', 'client access 24/7'), (r'acceso clientes 24/7', 'client access 24/7'),
    (r'[Aa]cceso 24/7', 'access 24/7'), (r'[Aa]cceso 24h', 'access 24h'), (r'acceso bajo petici[oó]n', 'access on request'),
    (r'\bL-J\b', 'Mon–Thu'), (r'\bL-V\b', 'Mon–Fri'), (r'\bS-D\b', 'Sat–Sun'), (r'tardes de L a J', 'afternoons Mon to Thu'),
    (r'\bV hasta\b', 'Fri until'), (r'\bV (?=\d)', 'Fri '), (r'\bJul-sep\b', 'Jul–Sep'), (r'Resto del a[nñ]o', 'Rest of the year'),
    (r'jornada completa', 'full day'), (r'\bverano\b', 'summer'), (r'\bAgosto\b', 'August'),
    (r'\bhasta (?=\d)', 'up to '), (r'\baula\b', 'classroom'), (r'\bsala\b', 'room'), (r'en formato abierto', 'in an open layout'),
    (r'(?<=\d) a (?=\d)', ' to '), (r'(?<=\d) y (?=\d)', ' and '), (r'(?<=\d) y (?=\d)', ' and '), (r'\by\b', 'and'),
]


def facts_en(text):
    for pat, rep_ in FACT_TOKENS_EN:
        text = re.sub(pat, rep_, text)
    return text


def slugify(text):
    import unicodedata
    t = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')


# ---------------------------------------------------------------- render
def make_env():
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES)),
        undefined=StrictUndefined,
        autoescape=False,          # el contenido es HTML de confianza, escrito por nosotros
        keep_trailing_newline=True,
    )
    env.filters['jsonprice'] = json_price
    env.filters['jsonld'] = to_jsonld
    return env


def render_markdown(text):
    return markdown.markdown(text, extensions=['attr_list', 'tables', 'sane_lists'], output_format='html5')


def build(check=False):
    g, i18n, redirects, ciudades_yml, centros = load_data()
    site = g['site']
    env = make_env()
    base_css = read(TEMPLATES / 'assets' / 'base.css').rstrip('\n')
    base_js = read(TEMPLATES / 'assets' / 'base.js').rstrip('\n')
    ciudades = group_cities(ciudades_yml, centros)
    n = service_counts(centros)

    warnings = []
    pages, posts = load_pages()
    by_id = link_alternates(pages, site['url'], warnings)
    # fecha descendente; el articulo marcado `destacado` va primero (es la tarjeta grande del listado)
    posts.sort(key=lambda a: a['fecha'], reverse=True)
    posts.sort(key=lambda a: 0 if a.get('destacado') else 1)
    for c in ciudades:
        grp = by_id.get('ciudad-' + c['slug'], {})
        c['url_es'] = grp['es'].url if 'es' in grp else None

    changed = []
    outputs = set()

    def city_url(city, lang):
        """URL de la pagina de ciudad si existe; si no, el hub con su ancla."""
        pid = 'ciudad-' + city['slug']
        if pid in by_id and lang in by_id[pid]:
            return by_id[pid][lang].url
        return by_id['ubicaciones'][lang].url + '#' + city['hub_anchor']

    # Pasada 1: los textos del front matter pueden usar {{ g.* }}; se renderizan
    # antes de nada para que una pagina pueda citar el h1 de otra.
    for p in pages:
        lang = p.lang
        ctx0 = {'g': g, 'p': {k: fmt_price(v, lang) for k, v in g['precios'].items()},
                'n': n, 'site': site, 't': i18n[lang]}
        # Cualquier texto del front matter (a cualquier profundidad: faq, ofertas, formas, pasos, cifras...)
        def render_deep(v):
            if isinstance(v, str):
                return env.from_string(v).render(ctx0) if '{{' in v else v
            if isinstance(v, list):
                return [render_deep(x) for x in v]
            if isinstance(v, dict) and not isinstance(v, Page):
                return {k: render_deep(x) for k, x in v.items()}
            return v
        for k in list(p.keys()):
            if k not in ('body', 'source', 'kind', 'lang', 'pair', 'alternates'):
                p[k] = render_deep(p[k])

    # Pasada 2: render
    for p in pages:
        lang = p.lang
        t = i18n[lang]
        urls = {pid: group[lang].url if lang in group else HOME[lang] for pid, group in by_id.items()}
        pages_by_id = {pid: group[lang] for pid, group in by_id.items() if lang in group}
        prices = {k: fmt_price(v, lang) for k, v in g['precios'].items()}
        pair = p['pair']
        p['lang_links'] = [{
            'lang': l,
            # sin pareja: un articulo lleva al listado del blog del otro idioma; el resto, a su home
            'href': ('#hero' if p.is_home else p.url) if l == lang else (pair[l].url if l in pair else (by_id['blog'][l].url if p.layout == 'articulo' else HOME[l])),
            'current': l == lang,
            # el title va en el idioma de destino ("Read this page in English" en la ES)
            'title': '' if l == lang else t['lang_other_title'],
        } for l in LANGS]

        # ciudades con enlace y datos de su pagina, para hub, home y listados
        cities_ctx = []
        for c in ciudades:
            cp = pages_by_id.get('ciudad-' + c['slug'])
            fotos = [x.get('foto') for x in (cp.get('centros') if cp else []) or [] if x.get('foto')]
            cities_ctx.append({**c, 'url': city_url(c, lang),
                               'label': c['nombre' if lang == 'es' else 'nombre_en'],
                               'region_label': c['region' if lang == 'es' else 'region_en'],
                               'resumen': cp.get('resumen') if cp else '',
                               'foto': fotos[0] if fotos else None,
                               'tags': sorted({x for cc in c['centros'] for x in cc['tags']}, key=tag_order)})
        # el hub agrupa las tarjetas por zona (`grupo`), en el orden de ciudades.yml
        regiones = []
        for c in cities_ctx:
            key = c['grupo' if lang == 'es' else 'grupo_en']
            r = next((r for r in regiones if r['nombre'] == key), None)
            if not r:
                r = {'nombre': key, 'ciudades': []}; regiones.append(r)
            r['ciudades'].append(c)
        zone_order = ['Norte', 'Noreste', 'Centro', 'Mediterráneo', 'Sur', 'Canarias',
                      'North', 'North-east', 'Centre', 'Mediterranean', 'South', 'Canary Islands']
        regiones.sort(key=lambda r: zone_order.index(r['nombre']) if r['nombre'] in zone_order else 99)

        lang_posts = []
        for a in posts:
            if a['lang'] != lang:
                continue
            enlace = a.get('enlace') or ''
            # enlace externo (http) = tarjeta que sale fuera; enlace interno (/slug/) = articulo que
            # solo existe en otro idioma (los posts del cliente no se traducen sin su aprobacion)
            lang_posts.append({**a, 'href': enlace or a['url'], 'externo': enlace.startswith('http'),
                               'otro_idioma': bool(enlace) and not enlace.startswith('http'),
                               'imagen': a.get('imagen'), 'destacado': bool(a.get('destacado')),
                               'fecha_legible': fecha_legible(a['fecha'], lang)})
        ctx = {
            'site': site, 'g': g, 'p': prices, 't': t, 'page': p, 'urls': urls, 'n': n, 'posts': lang_posts,
            'base_css': base_css, 'base_js': base_js, 'centros': centros, 'ciudades': cities_ctx,
            'lang': lang, 'pages_by_id': pages_by_id, 'regiones': regiones,
            'cu': {c['nombre']: c['url'] for c in cities_ctx},
            'cn': {c['nombre']: len(c['centros']) for c in cities_ctx},
        }

        if p.kind == 'md':
            body = env.from_string(p['body']).render(ctx)
            p['body_html'] = render_markdown(body)
            if p.layout == 'servicio':
                key = p['csv_key']
                p['ciudades_disponibles'] = [c for c in cities_ctx if any(key in x['servicios'] for x in c['centros'])]
                # Bloques maquetados desde el front matter: un parrafo "[[nombre]]" en el Markdown se
                # sustituye por _templates/partials/srv-<nombre>.html (perfiles, formas, incluye, pasos, donde).
                def bloque(m):
                    return env.get_template(f'partials/srv-{m.group(1)}.html').render(ctx)
                p['body_html'] = re.sub(r'<p>\[\[([a-z_]+)\]\]</p>', bloque, p['body_html'])
                p['jsonld'] = to_jsonld(jsonld_servicio(p, g, site, lang, prices, p['ciudades_disponibles'], t))
            if p.layout == 'articulo':
                p['fecha_legible'] = fecha_legible(p['fecha'], lang)
                p['jsonld'] = to_jsonld(jsonld_articulo(p, site, lang, t, urls))
            if p.layout == 'ciudad':
                city = next(c for c in cities_ctx if c['nombre'] == p['ciudad'])
                # Cifras de la ciudad desde el CSV (se pueden sobreescribir con `cifras` en el front matter)
                if not p.get('cifras'):
                    tc = t['ciudad']
                    # OJO: "10 a 47 m2" lleva un 2 en la unidad; se quita antes de leer los numeros
                    m2 = [int(x) for c_ in city['centros'] for x in re.findall(r'\d+', (c_['despachos_m2'] or '').replace('m2', '').replace('m²', ''))]
                    pax_src = [c_['capacidad_salas'] or '' for c_ in city['centros']]
                    pax = [int(x) for src in pax_src for x in re.findall(r'\d+', src)]
                    n_ = len(city['centros']); n24_ = sum(1 for c_ in city['centros'] if c_['acceso_24h'])
                    if n_ == 1:
                        lbl = tc['cif_h24_one'] if n24_ else tc['cif_in'].replace('{ciudad}', city['nombre' if lang == 'es' else 'nombre_en'])
                    else:
                        lbl = tc['cif_h24_all'] if n24_ == n_ else (tc['cif_h24_some'].replace('{n}', str(n24_)) if n24_ else tc['cif_in'].replace('{ciudad}', city['nombre' if lang == 'es' else 'nombre_en']))
                    cif = [{'num': f"{n_} {tc['cif_centre_one'] if n_ == 1 else tc['cif_centre_many']}", 'label': lbl}]
                    if m2: cif.append({'num': f"{min(m2)} {tc['cif_to']} {max(m2)} m²", 'label': tc['cif_m2']})
                    if pax:
                        if min(pax) != max(pax): num = f"{min(pax)} {tc['cif_to']} {max(pax)}"
                        elif any('hasta' in x for x in pax_src): num = f"{tc['cif_upto']} {max(pax)}"
                        else: num = str(max(pax))
                        cif.append({'num': num, 'label': tc['cif_pax']})
                    p['cifras'] = cif
                # Bloques maquetados de la introduccion ([[elegir]], [[cifras]]) desde el front matter
                p['body_html'] = re.sub(r'<p>\[\[([a-z_]+)\]\]</p>', lambda m: env.get_template(f'partials/city-{m.group(1)}.html').render(ctx), p['body_html'])
                overrides = {o['nombre']: o for o in (p.get('centros') or [])}
                for c in city['centros']:
                    o = overrides.get(c['centro'], {})
                    c['anchor'] = slugify(c['centro'])
                    c['foto'] = o.get('foto')
                    c['texto_html'] = render_markdown(env.from_string(o['texto']).render(ctx)) if o.get('texto') else ''
                    c['descripcion_corta'] = o.get('descripcion')
                    c['tag_labels'] = [t['ciudad']['tags'].get(x, x) for x in c['tags']]
                    # datos de ficha en el idioma de la pagina (el CSV esta en espanol)
                    tr = facts_en if lang == 'en' else (lambda x: x)
                    c['horario_txt'] = tr(c['horario'])
                    c['salas_txt'] = tr(c['capacidad_salas']) if c['capacidad_salas'] else ''
                    c['m2_txt'] = tr(c['despachos_m2'].replace('m2', 'm²')) if c['despachos_m2'] else ''
                # grupos: por zonas si la pagina las define, si no un solo grupo sin titulo
                if p.get('zonas'):
                    by_name = {c['centro']: c for c in city['centros']}
                    grupos = []
                    for z in p['zonas']:
                        grupos.append({'nombre': z['nombre'], 'anchor': slugify(z['nombre']),
                                       'texto_html': render_markdown(env.from_string(z.get('texto', '')).render(ctx)),
                                       'centros': [by_name[n] for n in z['centros']]})
                    listed = {n for z in p['zonas'] for n in z['centros']}
                    missing = [c['centro'] for c in city['centros'] if c['centro'] not in listed]
                    if missing:
                        raise SystemExit(f"{p.source}: centros sin zona: {missing}")
                else:
                    grupos = [{'nombre': None, 'anchor': None, 'texto_html': '', 'centros': city['centros']}]
                p['grupos'] = grupos
                p['city'] = city
                tags_city = {x for c in city['centros'] for x in c['tags']}
                p['servicios_ciudad'] = [pages_by_id[t['ciudad']['srv_pages'][k]] for k in
                                         ('despachos', 'salas de reuniones', 'smart office', 'coworking')
                                         if k in tags_city and t['ciudad']['srv_pages'][k] in pages_by_id]
                p['cercanas'] = [c for c in cities_ctx if c['slug'] in (p.get('cercanas') or [])]
                p['jsonld'] = to_jsonld(jsonld_ciudad(p, g, site, lang, t, city, city['centros'], urls))
            html = env.get_template(f'layouts/{p.layout}.html').render(ctx)
        else:
            if p.layout == 'blog':
                p['jsonld'] = to_jsonld(jsonld_blog(p, site, lang, t, lang_posts))
            if p.layout == 'hub':
                mp = pages_by_id.get('ciudad-madrid')
                mcity = next((c for c in cities_ctx if c['nombre'] == 'Madrid'), None)
                cards = []
                if mp and mcity:
                    over = {o['nombre']: o for o in mp.get('centros') or []}
                    zonas = mp.get('zonas') or [{'nombre': None, 'centros': [c['centro'] for c in mcity['centros']]}]
                    by_name = {c['centro']: c for c in mcity['centros']}
                    for z in zonas:
                        for n_ in z['centros']:
                            c = by_name[n_]
                            cards.append({**c, 'zona': z['nombre'], 'foto': over.get(n_, {}).get('foto'),
                                          'anchor': slugify(n_), 'url': mcity['url'] + '#' + slugify(n_),
                                          'tag_labels': [t['ciudad']['tags'].get(x, x) for x in c['tags']]})
                ctx['madrid_cards'] = cards
                ctx['madrid_url'] = mcity['url'] if mcity else urls['ubicaciones']
                p['jsonld'] = to_jsonld(jsonld_hub(p, site, lang, t, cities_ctx, urls))
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
        base = SITEMAP_PRIORITY.get(p['id']) or SITEMAP_PRIORITY_BY_LAYOUT.get(p.layout, '0.2')
        if p.lang == DEFAULT_LANG or base == '0.2':
            return base
        return f'{float(base) - 0.1:.1f}'

    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<!--',
          '  Generado por _build.py a partir de _content/. No editar a mano.',
          '  NO se referencia desde robots.txt mientras el sitio viva en el prototipo:',
          '  el prototipo va noindex y no queremos invitar a su indexacion.',
          '  TODO migracion: cambiar site.url en _data/global.yml y declararlo en robots.txt.',
          '-->',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
          '        xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for p in sorted(pages, key=lambda p: (p.lang != DEFAULT_LANG, page_order(p))):
        sm.append(f'  <url><loc>{p.abs_url}</loc><priority>{prio(p)}</priority>')
        for a in p.alternates:
            sm.append(f'    <xhtml:link rel="alternate" hreflang="{a["lang"]}" href="{a["url"]}"/>')
        sm[-1] += '</url>'
    sm.append('</urlset>\n')
    sitemap = '\n'.join(sm)

    # ---- llms.txt
    pares = [{'es': grp['es'].url, 'en': grp['en'].url} for grp in by_id.values() if 'es' in grp and 'en' in grp]
    servicios = [grp['es'] for grp in by_id.values() if 'es' in grp and grp['es'].layout == 'servicio']
    llms = env.get_template('llms.txt').render(
        site=site, g=g, p={k: fmt_price(v, 'es') for k, v in g['precios'].items()},
        ciudades=ciudades, pares=pares, servicios=servicios, n=n,
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

    # ---- manifiesto: lo generado en la build anterior que ya no se genera se borra
    # (por ejemplo, la pagina de un articulo o una ciudad cuyo fichero se elimino).
    manifest = ROOT / '_build.manifest'
    previous = set(manifest.read_text(encoding='utf-8').splitlines()) if manifest.exists() else set()
    current = {o.relative_to(ROOT).as_posix() for o in outputs}
    stale = [ROOT / rel for rel in sorted(previous - current) if rel]
    if not check:
        for f in stale:
            if f.exists():
                f.unlink(); changed.append(f)
                try:
                    f.parent.rmdir()   # solo si queda vacia
                except OSError:
                    pass
        write_if_changed(manifest, chr(10).join(sorted(current)) + chr(10))
    elif stale:
        changed.extend(f for f in stale if f.exists())
    return changed, outputs, warnings


def print_htaccess(redirects):
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
        _, _, redirects, _, _ = load_data()
        print_htaccess(redirects)
        return

    changed, outputs, warnings = build(check=args.check)
    rel = lambda p: p.relative_to(ROOT).as_posix()
    for w in warnings:
        print('AVISO:', w)
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
