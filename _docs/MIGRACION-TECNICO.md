# Migración de la web de OficinasYA! al dominio definitivo — guía para el técnico

Escrito para alguien competente que no ha visto nunca este proyecto.
Fecha: 16 de septiembre de 2026. Repositorio: `RobertoIBC/robertoibc.github.io`
(público). Prototipo publicado en https://robertoibc.github.io/.

---

## ⛔ DOS PUNTOS BLOQUEANTES — leer antes de nada

### 1. El `noindex`: no se toca hasta estar en el dominio definitivo

Las 66 páginas llevan `<meta name="robots" content="noindex, nofollow">`. Lo
controla **una sola línea**: `site.noindex: true` en `_data/global.yml`.

- **Mientras la web viva en `robertoibc.github.io` NO se retira.** Si se
  retira ahí, Google indexa el prototipo en un dominio que no es el del
  cliente y lo pone a competir con `www.oficinasya.es` por las mismas
  búsquedas, con títulos y contenido más completos que la web real. Es
  exactamente lo que el `noindex` evita. Aunque el cliente lo pida.
- **El día que el sitio esté servido desde `www.oficinasya.es`**, y solo
  entonces: `site.noindex: false`, regenerar (`python _build.py`) y comprobar
  que ninguna de las 66 páginas conserva la meta (`grep -rL 'content="noindex'
  --include=index.html .` debe devolverlas todas). Está probado: con `false`,
  0 de 66 la llevan; con `true`, 66 de 66.
- `robots.txt` deja el rastreo **abierto a propósito** (sin `Disallow`): si se
  bloqueara, Google no podría leer el `noindex` y las URLs ya indexadas se
  quedarían en el índice. Al migrar, descomentar en `robots.txt` la línea
  `Sitemap: https://www.oficinasya.es/sitemap.xml`.

### 2. El formulario de contacto NO envía nada y dice que sí

El bloque de contacto de la home (`#contact`, en `_content/pages/home.*.html`)
no es un `<form>`: son `<input>` sin `name` y un botón (`#cfbtn`, JS en
`_templates/layouts/home.html`) que al pulsarlo se pone verde con
**"✓ Enviado, te contactamos pronto"** durante cuatro segundos. No hay destino,
no llega correo, no se guarda nada. Lo mismo el formulario de newsletter del
blog (`handleNL` en `_templates/layouts/blog.html`).

**Esto no puede publicarse en el dominio real tal cual**: habrá gente
convencida de que ha contactado. Antes de publicar, una de las dos:

- **Conectarlo** a un backend (el formulario del WordPress de destino, un
  endpoint propio, o un servicio tipo Formspree): poner `<form action=…
  method="post">`, `name` en cada campo, y sustituir el JS del botón por el
  envío real con su respuesta.
- **O retirar el mensaje de éxito falso** y dejar el bloque solo con teléfono
  y WhatsApp, que sí funcionan.

En el HTML de la home hay un **comentario en mayúsculas justo encima del
formulario** que repite esto (es el único comentario de desarrollo que se
publica a propósito). El bloque de contacto, además del formulario, tiene el
teléfono, el WhatsApp y el email como enlaces que sí funcionan.

Mientras tanto, ninguna llamada a la acción del sitio apunta al formulario:
todas van a `tel:` o a WhatsApp (`wa.me/34624119705`, con mensaje
prerrellenado según página y centro).

---

## ⚠️ Commits después de la entrega inicial

El repositorio se entregó en `646f855` (16 de septiembre de 2026) y se ha
seguido moviendo. Si ya lo habías clonado, haz `git pull`. Lo que tocan:

| Commit | Qué cambia |
|---|---|
| `90a2e6a` | Hub: el tooltip del mapa navegaba a `/ubicaciones/[object SVGAnimatedString]` (404). Ahora es un `<a>`. Nueva auditoría de clicks en `_tools/`. |
| `646f855` | Pasada final: fichas en inglés traducidas por tokens, bloque de contacto con enlaces reales y comentario sobre el formulario, redes en `global.yml`, `_tools/`. |
| `b71be62` | Fotos: cabecera con foto real en 9 ciudades (`hero_foto` en el front matter, `assets/img/cabeceras/`, `og/`), galerías en salas y despachos, fotos en las tarjetas de coworking, fichas a 560 px, `ImageObject` en el marcado, `og:image` por ciudad. |
| `dfa19ea` | `parse_m2()` como única lectura de la columna de m² del CSV, comprobación que aborta el build si el mínimo baja de 5 m², `_tools/test_build.py` y `_tools/auditoria_texto.py` (multiconjunto de palabras contra la última versión publicada). |
| `04218b9` | Introducción de las páginas de ciudad: cifras automáticas desde el CSV (`[[cifras]]`), tarjetas "qué centro elegir" (`[[elegir]]`) en las 8 ciudades con más de un centro, párrafo de entrada destacado. Sin cambios de texto. |

## Qué es esto

Un **sitio estático generado con Python**. No hay WordPress, base de datos ni
servidor: el resultado son ficheros HTML en la raíz del repo, que GitHub Pages
sirve tal cual.

```
_build.py           el generador (Python 3, Jinja2, PyYAML, Markdown)
_data/              datos: cifras, textos de cabecera/pie, centros, ciudades, horarios, redirecciones
_templates/         plantillas Jinja (base, cabecera, pie, un layout por tipo de página, parciales)
_content/           contenido: páginas (html), servicios (md), ciudades (md), blog (md)
<raíz>/…/index.html HTML GENERADO — no se edita a mano
sitemap.xml, llms.txt, robots.txt
assets/             CSS/JS inlinados por el generador; imágenes en assets/img/
```

Convenciones: cada página existe en ES y EN con el mismo `id`; la URL de cada
una está en su front matter (`url:`); las cifras (35 espacios, 17 ciudades,
precios "desde", teléfono, WhatsApp) están **una sola vez** en
`_data/global.yml` y se leen como `{{ g.espacios }}`, `{{ p.despacho_mes }}`.
El `README.md` del repo explica cómo añadir una ciudad, un artículo o cambiar
una cifra, con ejemplos completos.

## Instalar y regenerar

```
pip install -r requirements.txt      # Jinja2, PyYAML, Markdown
python _build.py                     # regenera todo (idempotente: solo reescribe lo que cambia)
python _build.py --check             # falla si el HTML generado no coincide con las fuentes
git config core.hooksPath _hooks     # hook de pre-commit que avisa (no bloquea) si falta regenerar
```

**Qué NO se edita a mano:** ningún `index.html` de la raíz, `sitemap.xml`,
`llms.txt` ni las carpetas de redirección (`*.html` de la raíz con meta
refresh). Todo eso lo escribe `_build.py`; un cambio a mano desaparece en la
siguiente regeneración. `_build.manifest` lista lo generado y sirve para borrar
lo que deja de existir.

## Cambiar de dominio: `site.url`

En `_data/global.yml`, `site.url: https://robertoibc.github.io` →
`https://www.oficinasya.es`. Con solo eso, al regenerar cambian:

- `<link rel="canonical">` de las 66 páginas,
- las etiquetas `hreflang` (es, en, x-default) entre versiones de idioma,
- `og:url`,
- las URLs absolutas del JSON-LD (Organization, Service/Offer, LocalBusiness,
  BreadcrumbList, ItemList, BlogPosting),
- `sitemap.xml` (66 URLs con sus alternates),
- `llms.txt`.

Los enlaces internos son relativos a la raíz (`/oficinas-en-madrid/`) y no
cambian. La web debe servirse **en la raíz del dominio**, no en una subcarpeta.

## Las 50 redirecciones 301

`_data/redirects.yml` tiene dos listas:

- **prototipo** (12): rutas antiguas del prototipo (`/ubicaciones.html` →
  `/ubicaciones/`). Hoy el generador escribe en cada una un HTML mínimo con
  `meta refresh 0` + canonical (lo más parecido a un 301 que permite GitHub
  Pages). Con servidor propio, 301 reales.
- **migracion** (38): rutas de la web viva en WordPress (páginas de centro,
  etc.) → páginas nuevas. Hoy no generan nada.

El día de la migración:

```
python _build.py --htaccess > redirecciones.txt
```

imprime las 50 (51 líneas con las dos secciones) en formato
`Redirect 301 /origen /destino`, para pegar en `.htaccess` (Apache) o importar
en el plugin *Redirection* de WordPress. Comprobar después que ninguna
redirección encadena dos saltos.

Los **10 artículos del blog** no necesitan redirección: sus URLs en el
prototipo son el mismo slug que tienen hoy en WordPress
(`/claves-para-mejorar-tu-networking/`), a propósito.

## Puntos de conexión pendientes

| Qué | Estado en el prototipo | Qué espera la migración |
|---|---|---|
| **Formulario de contacto** (home `#contact`) y **newsletter** (blog) | No envían; mensaje de éxito falso. **Bloqueante, ver arriba.** | Backend de envío, o retirarlos. |
| **Comunidad**: "Publicar mi perfil" y "Unirme a la Comunidad" | WhatsApp con mensaje prerrellenado ("Hola, quiero unirme a la Comunidad OficinasYA"). | El formulario de alta de la comunidad (hoy en `www.oficinasya.es/comunidad/`). "Ver todos los miembros" se retiró: si el directorio completo se migra, va en `/comunidad/`. |
| **Blog** | 10 artículos ES con el texto real (traído por `wp-json` del WordPress actual), URL = slug de WordPress. Imagen destacada copiada a `assets/img/blog/` a 1200 px (9 de 10; la décima es un medio privado del WordPress y usa banco de imágenes). | Nada que conectar: las URLs coinciden y las imágenes van con el sitio. |
| **Blog en inglés** | **Decisión consciente, no pendiente**: los artículos no se traducen sin aprobación del cliente. El listado inglés existe con títulos y resúmenes traducidos; cada tarjeta lleva al artículo en español con el aviso "Article available in Spanish". Esas 10 URLs inglesas no existen y no se declara hreflang en los artículos. | Si el cliente aprueba la traducción (pregunta hecha al cliente), se crea `<slug>.en.md` con `url:` y el generador hace el resto. |
| **Redes sociales** (pie) | URLs de la web viva, provisionales. LinkedIn es un perfil personal; hay dos cuentas de Facebook y dos de Instagram. | Las que confirme el cliente (`_templates/partials/footer.html`). Si una cuenta no está activa, quitar el icono. |
| **`sameAs` del JSON-LD** de cada centro (LocalBusiness) | Apunta a la página del centro en `www.oficinasya.es`. | Al migrar son URLs del propio dominio (o redirigen por la lista *migracion*). Nada que hacer. |
| **Imágenes de la home** alojadas en `oficinasya.es/wp-content` (foto de despacho, tres logos de clientes, dos iconos; 0,6 MB) | Enlazadas en caliente. | Al migrar están en el mismo dominio. Opcional: copiarlas a `assets/img/`. |
| **Nombres sin tilde en `centros.csv`** (*Andres Martinez Salazar*, *Dean Marti*, *Recepcion* ×9) | Salen así en fichas y mensajes de WhatsApp. Vienen de la hoja del cliente. | Que el cliente los corrija en su hoja; no corregirlos a mano en el CSV (volverían con la siguiente actualización). |
| **Enlaces rotos dentro de los artículos del blog** (11 externos + 1 imagen 403) | Son contenido del cliente; listados en el documento de preguntas al cliente (fuera del repositorio; lo tiene el responsable del proyecto). | Decisión del cliente. |
| **Datos de ficha en inglés** (horario, salas, despachos) | Se traducen por tokens al generar (`FACT_TOKENS_EN` en `_build.py`). | Si el CSV incorpora una palabra nueva, añadirla al diccionario. |
| **Fotos de cabecera y galerías** (`assets/img/cabeceras/`, `og/`, `salas/`, `despachos/`) | Recortes hechos a partir de originales de las galerías de `www.oficinasya.es`; los originales no están en el repo. | Van con `assets/`. Para añadir una ciudad: cinco líneas de front matter (README, "Foto de cabecera"). |
| **Precios por centro** | No se publican (`publicar_precios_por_centro: false`). | Decisión del cliente. |

## Qué NO puede subirse al servidor

- **`datos-centros.csv`**: la hoja maestra del cliente con precios por centro,
  garantías y fianzas. Está en `.gitignore` y nunca ha estado en el repo. Si
  hace falta para regenerar, se copia en local y no se sube.
- **Las carpetas que empiezan por `_`** (`_data/`, `_templates/`, `_content/`,
  `_hooks/`, `_build.py`, `_build.manifest`): son las fuentes. En GitHub Pages
  no se publican porque Jekyll ignora todo lo que empieza por `_` (por eso
  **no hay ni debe haber un `.nojekyll`** en el repo). **En un servidor propio o
  en WordPress esa protección desaparece**: hay que subir solo el HTML generado
  y `assets/`, o bloquear `_*` en el servidor (`.htaccess`:
  `RedirectMatch 404 ^/_`). Contienen el CSV de centros (sin precios), pero
  no hay motivo para servir las fuentes.
- Los documentos de trabajo con el cliente (preguntas pendientes, auditoría de
  su web, informes) viven **fuera del repositorio** y así deben seguir: llevan
  datos que no son públicos. Este fichero es el único que va dentro, en
  `_docs/` (carpeta con `_`: GitHub Pages no la sirve).
- `README.md`, `requirements.txt` y `_tools/` **no se suben al dominio final**:
  en GitHub Pages el README y el requirements se sirven (200) porque están en
  la raíz; no contienen datos sensibles, pero documentan el generador. En el
  servidor definitivo, solo el HTML generado, `assets/`, `robots.txt`,
  `sitemap.xml` y `llms.txt`.

## Comprobaciones posteriores a la subida, en orden

1. **El dominio sirve la raíz**: `https://www.oficinasya.es/` devuelve la home
   nueva; `/en/`, `/oficinas-en-madrid/`, `/alquiler-de-despachos/` devuelven
   200. Sin subcarpeta.
2. **`noindex` retirado**: `curl -s https://www.oficinasya.es/ | grep -c noindex`
   → 0. Repetir en dos o tres páginas interiores y en `/en/`.
3. **Canonical y hreflang** apuntan al dominio nuevo (no a `robertoibc`):
   `grep -rl robertoibc.github.io --include=index.html .` debe estar vacío
   tras regenerar.
4. **Redirecciones**: las 50 responden 301 al destino correcto y el destino
   responde 200 (un bucle sencillo con `curl -sI`). Sin cadenas.
5. **`sitemap.xml`** accesible, con 66 `<url>` y el dominio nuevo; declarado en
   `robots.txt`; enviado en Search Console.
6. **Formulario**: enviar una prueba real y comprobar que llega (o que el
   bloque ya no promete nada).
7. **WhatsApp y teléfono**: pulsar un CTA de ficha desde el móvil: abre
   WhatsApp con el texto del centro; el `tel:` marca 918 298 500.
8. **JSON-LD**: pasar la home, una página de servicio y una de ciudad por la
   prueba de resultados enriquecidos de Google (Organization, Service +
   Offer, LocalBusiness, FAQPage, BreadcrumbList sin errores).
9. **Fuentes no expuestas**: `https://www.oficinasya.es/_data/centros.csv` debe
   dar 404.
10. **Search Console**: propiedad del dominio nuevo, sitemap enviado, y a los
    pocos días revisar que las URLs antiguas de WordPress figuran como
    redirigidas y no como 404.

---

*Detalle de decisiones y datos pendientes del cliente: documento de preguntas al cliente, fuera del repositorio.
Pasada de comprobación completa: los cuatro scripts de `_tools/` (estático,
clicks en headless, coherencia de cifras e idiomas, enlaces en vivo), descritos
en el README del repo.*
