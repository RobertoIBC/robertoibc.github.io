# Web de OficinasYA! — prototipo

Sitio estático en dos idiomas (ES en la raíz, EN en `/en/`). Todo el HTML de
la raíz **se genera**: no se edita a mano. Lo que se edita está en `_data/`,
`_content/` y `_templates/`.

```
_build.py            el generador (Python 3, sin frameworks)
_hooks/pre-commit    aviso al commitear si el HTML no está regenerado
requirements.txt     sus tres dependencias: Jinja2, PyYAML, Markdown
_data/
  global.yml         cifras de la red, precios "desde", teléfono, email, URL del sitio
  i18n.yml           textos de cabecera y pie en ES y EN
  centros.csv        los 35 espacios: ciudad, dirección, horario, m², salas, servicios
  horarios.yml       horario estructurado (schema.org) de cada centro, curado a mano
  ciudades.yml       las 17 ciudades: nombre, slug ES/EN, ancla en el hub
  redirects.yml      rutas antiguas -> nuevas (prototipo y web viva)
_content/
  pages/             las páginas a medida: home, ubicaciones, comunidad, blog, legales
                     (un fichero por página e idioma: home.es.html, home.en.html, ...)
  servicios/         las 4 páginas de servicio, en Markdown con front matter
                     (alquiler-de-despachos.es.md, private-offices.en.md, ...)
  ciudades/          las 17 páginas de ciudad, igual: segovia.es.md, segovia.en.md, ...
_templates/
  base.html          esqueleto común: <head>, cabecera, pie, WhatsApp, JS
  partials/          nav.html, footer.html
  layouts/           la CSS y el JS propios de cada tipo de página
                     (servicio.html construye la página de servicio a partir del Markdown)
  assets/            base.css y base.js, compartidos por todas las páginas
  llms.txt           plantilla del llms.txt
  redirect.html      plantilla de los stubs de redirección
assets/img/          fotos e imagen de Open Graph (esto sí se sube tal cual)
```

Las carpetas que empiezan por `_` **no se publican**: GitHub Pages las excluye
(Jekyll ignora todo lo que empieza por guion bajo). Por eso el repo no debe
tener nunca un fichero `.nojekyll`. Si la web se mueve a otro hosting, hay que
asegurarse por otra vía de que `/_data/`, `/_content/` y `/_templates/` no
sean accesibles.

## Regenerar la web

Una sola vez, instalar las dependencias:

```
pip install -r requirements.txt
```

Y cada vez que se cambie algo en `_data/`, `_content/` o `_templates/`:

```
python _build.py
```

Escribe solo los ficheros que cambian y dice cuáles. Ejecutarlo dos veces
seguidas no cambia nada. `python _build.py --check` comprueba, sin escribir,
que el HTML de la raíz está al día con las fuentes (útil antes de un commit).

Después, `git add -A`, commit y push: GitHub Pages publica en menos de un
minuto.

### El aviso al commitear

Hay un hook de pre-commit en `_hooks/pre-commit`. Se instala una vez:

```
git config core.hooksPath _hooks
```

Al hacer commit ejecuta `python _build.py --check` y, si el HTML de la raíz no
coincide con las fuentes, **avisa**. No regenera nada y no bloquea el commit:
existe para que nadie publique plantillas y HTML divergentes sin enterarse.
Si Python no está instalado, avisa de que no ha podido comprobar y deja pasar.
Para saltarlo en un commit concreto: `git commit --no-verify`.

## Cambiar una cifra (espacios, ciudades, precio, teléfono)

Todo está en `_data/global.yml`. Por ejemplo, si la red pasa a 36 espacios:

```yaml
espacios: 36
```

Regenerar. La cifra cambia en las dos versiones de todas las páginas, en el
JSON-LD, en las descripciones y en `llms.txt`. No hay que buscar nada con grep.

## Cambiar un texto de una página

Cada página vive en `_content/pages/<id>.<idioma>.html`. Empieza con un
bloque de metadatos entre `---` (título, descripción, URL) y sigue con el
HTML de la página. Las cifras compartidas aparecen como `{{ g.espacios }}`,
`{{ g.telefono }}`, etc.: hay que dejarlas así, no sustituirlas por el número.

Si cambias el título o la descripción, respeta los límites: título 50–60
caracteres, descripción 140–160.

## Páginas de servicio (Markdown)

Cada servicio es un fichero por idioma en `_content/servicios/`. Arriba, entre
`---`, los datos estructurados: `title`, `description`, `h1`, `subtitle`,
`ofertas` (qué precio de `global.yml` mostrar y en qué unidad), `incluye`,
`no_incluye`, `csv_key` (qué palabra de la columna `servicios` de
`centros.csv` decide en qué ciudades está disponible) y `faq`. Debajo, el
texto en Markdown con encabezados `##`. El generador construye con eso el
HTML, la lista de ciudades, el JSON-LD (`Service`, `Offer`, `FAQPage`,
`BreadcrumbList`) y los hreflang.

Las dos versiones de una página comparten el mismo `id` en el front matter:
así se enlazan entre sí. Para dar un id a un encabezado (para enlazar a él),
la sintaxis es `## Título {: #mi-ancla }`. No uses `{#mi-ancla}`: `{#` abre
un comentario en Jinja y rompe la página.

Los enlaces a otras páginas se escriben con el mapa de URLs, no a mano:
`[Smart Office]({{ urls['srv-oficina-virtual'] }}#smart-office)`. Así apuntan
a la versión del idioma correcto.

## Páginas de ciudad y cómo añadir una ciudad

Cada ciudad es un fichero por idioma en `_content/ciudades/`. El front matter
lleva `ciudad` (el nombre EXACTO de la columna `ciudad` de `centros.csv`),
`h1`, `subtitle`, `cercanas` (slugs de otras ciudades de la red), `faq` y
`centros`: una entrada por centro, con el `nombre` exacto del CSV, su `foto`
y un `texto` propio. Para ciudades con varias zonas (Madrid) hay además
`zonas`, cada una con `nombre`, `texto` y la lista de `centros` que agrupa.
El cuerpo Markdown es el texto de la ciudad.

La ficha de cada centro —dirección, horario, m², salas, etiquetas de
servicios, acceso 24 h— NO se escribe: sale de `centros.csv`. El JSON-LD
(`LocalBusiness` por centro con `PostalAddress` y, si existe en
`horarios.yml`, `openingHoursSpecification`) también.

Añadir una ciudad, paso a paso. Ejemplo: la red abre un centro en Valladolid.

1. `_data/centros.csv`: una fila por centro, con `ciudad: Valladolid`.
2. `_data/ciudades.yml`: una entrada
   `- { nombre: Valladolid, nombre_en: Valladolid, slug: valladolid, slug_en: valladolid, hub_anchor: card-valladolid }`.
3. `_data/horarios.yml`: el horario estructurado del centro, si la hoja da
   días y horas. Si no, se omite y el centro sale sin horario en el JSON-LD.
4. `_data/global.yml`: subir `espacios` y `ciudades`.
5. `_content/ciudades/valladolid.es.md` y `valladolid.en.md`, copiando la
   estructura de `merida.es.md` (una ciudad de un centro). Regla de oro: cada
   frase sale de la página del centro en oficinasya.es o del CSV; si no hay
   fuente, no se escribe. Título 50–60, description 140–160, FAQ solo con
   hechos locales (mínimo tres o ninguna).
6. `python _build.py`. Mientras la ciudad no tenga página, los enlaces a ella
   van al hub con su ancla; en cuanto existe, apuntan a la página sola.

## Cabecera y pie

Los enlaces y textos de la cabecera y el pie están en `_data/i18n.yml`
(un bloque `es` y otro `en`). El HTML está en `_templates/partials/`.

## Migración a www.oficinasya.es

Dos líneas en `_data/global.yml` y regenerar:

```yaml
site:
  url: https://www.oficinasya.es
  noindex: false
```

Con eso cambian canonical, hreflang, Open Graph, JSON-LD y sitemap en todas
las páginas, y desaparece el `noindex`. Las redirecciones 301 desde las URLs
antiguas las imprime `python _build.py --htaccess`. El detalle completo, con
el orden de las operaciones, está en la CHECKLIST DE MIGRACIÓN del documento
de encargo (fuera del repo).

## Lo que NO está en el repo

`datos-centros.csv`, la hoja del cliente con precios por centro, está en
`.gitignore` y no debe subirse nunca: el repositorio es público y GitHub Pages
sirve todo lo que se commitea. `_data/centros.csv` es la versión sin precios.
