# Configuración del servidor de www.oficinasya.es

**Qué pegar:** el bloque Apache de abajo, entero, **al principio** del `.htaccess` que ya existe en `/www` (9,4 kB), sin borrar lo que tiene.
**Dónde:** `/www/.htaccess`, la carpeta donde están `index.html` y `enviar.php`.
**Cómo comprobarlo:** abre `https://oficinasya.es/` (sin www): tiene que acabar en `https://www.oficinasya.es/`. Si no cambia, el servidor no lee `.htaccess`: ve a «¿Apache o nginx?».

El paso a paso completo de la subida está en [DESPLIEGUE.md](DESPLIEGUE.md). Este fichero solo contiene la configuración.

---

## ¿Apache o nginx?

Todo apunta a **Apache**:
- las páginas de error del servidor son las de Apache (`<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">`);
- `https://www.oficinasya.es/.htaccess` responde 403, que es lo que hace Apache para proteger ese fichero.

La prueba definitiva es la de arriba: si después de subir el `.htaccess` la dirección sin www pasa a la de www, es Apache y lee el fichero.
Si no pasa nada, el servidor es nginx o tiene `.htaccess` desactivado. En ese caso **no se puede arreglar desde FTP**: hay que mandar al hosting el bloque nginx del final.

## Qué hace la configuración, en este orden

Primero lo que da 404, luego todo lo que redirige, y el dominio al final. Así una URL antigua llega a la nueva **en un solo salto aunque se pida sin www** (`https://oficinasya.es/despachos/` → `https://www.oficinasya.es/alquiler-de-despachos/`), en vez de pasar antes por la versión con www.

1. **Bloqueo** de las fuentes y ficheros internos (responden 404, como si no existieran):
   - todo lo que empieza por `_` en la raíz: `_data`, `_content`, `_templates`, `_tools`, `_docs`, `_hooks`, `_build.py`, `_build.manifest`, `__pycache__`;
   - `/OLD/`, el núcleo del WordPress anterior;
   - los ficheros ocultos (`.git`, `.gitignore`, `.claude`, `.env`…), menos `.well-known`;
   - `README.md`, `requirements.txt`, `datos-centros.csv`;
   - cualquier `.py`, `.pyc`, `.md`, `.yml`, `.yaml`, `.csv` o `.manifest`.

   `enviar.php` **no** se bloquea: es el formulario.
2. **345 redirecciones 301** de las URLs antiguas (todas las que tiene archivadas archive.org), directas a la URL final con www:
   - las del WordPress anterior, incluido el esquema de 2014 (`/oficina/<ciudad>/`, `/oficinas/<centro>/`);
   - las del prototipo (`/ubicaciones.html`…);
   - los prefijos `/category/`, `/tag/`, `/author/`, `/web/`, `/blog/page/` y los archivos por fecha (`/2017/` a `/2021/`) → `/blog/`;
   - la paginación de las fichas de centro (`/centros/<centro>/page/2/`) → su ciudad;
   - lo que quede de `/centros/`, `/oficinas/`, `/oficina/` y `/portfolio_category/` sin regla exacta → `/ubicaciones/`;
   - los prefijos `/actividades/`, `/miembros/` → `/comunidad/`.

   La barra final del origen es opcional.
3. **Carpeta sin barra final** (`/blog` → `https://www.oficinasya.es/blog/`) en un solo salto. Sin esta regla Apache responde a `/blog` con una dirección `http://` y el hosting la devuelve a `https://`: dos saltos de más.
4. **Dominio:** lo que quede en `oficinasya.es` → `www.oficinasya.es`, con 301, en un solo salto y ya en https.
   No hay regla de http → https porque el hosting ya la hace delante de Apache. Añadir una regla `%{HTTPS} off` detrás de un proxy puede crear un bucle de redirecciones.

Se genera con `python _build.py --htaccess` (Apache) y `python _build.py --nginx` desde `_data/redirects.yml`. Si cambia una redirección, se cambia allí y se vuelve a generar: el bloque no se edita a mano.

**El servidor ya tiene un `.htaccess` (del técnico)**: no lo borres. Este bloque va **al principio**, entre `# BEGIN OficinasYA` y `# END OficinasYA`, y debajo se deja todo lo que tenía. Si ya hay un bloque de OficinasYA (de una subida anterior, o reglas de redirección añadidas a mano por otra persona), **se sustituye entero**: dos bloques a la vez no se suman, gana la primera regla que coincide y las viejas taparían a las nuevas. Si después la web da «Error 500», vuelve a subir el `.htaccess` de la copia y avisa al técnico.

**`/oficinavirtual/` es otra web en marcha** (WordPress con WooCommerce, «Oficina Virtual de Oficinas YA!»), que se sirve en `https://oficinavirtual.oficinasya.es/`; en `www.oficinasya.es/oficinavirtual/` responde ese mismo WordPress con su propia página de «no encontrada», y es normal. Estas reglas no la tocan: las redirecciones y los bloqueos van anclados a la raíz, y si esa carpeta tiene su propio `.htaccess` (un WordPress con enlaces amigables lo necesita: compruébalo en la copia del paso 1), Apache no le aplica estas reglas de reescritura. En cualquier caso, la comprobación 8 de DESPLIEGUE.md verifica que la tienda sigue funcionando. **`/OLD/`** (el núcleo del WordPress anterior, con su `wp-config.php`) queda bloqueado al público con un 404; borrarlo lo decide el técnico.

---

## Apache: `.htaccess` (copiar entero)

```apache
# BEGIN OficinasYA
# .htaccess de OficinasYA! -- generado por `python _build.py --htaccess` desde _data/redirects.yml.
# No editar a mano: cambiar redirects.yml y volver a generarlo. Al actualizarlo se sustituye todo lo que
# hay entre BEGIN OficinasYA y END OficinasYA; lo que el tecnico tenga debajo no se toca.
Options -Indexes
RewriteEngine On

# Orden: primero lo que da 404, luego todo lo que redirige (siempre a la URL final, absoluta y con www,
# venga del dominio que venga: un solo salto tambien desde oficinasya.es) y al final el dominio.

# 1. Fuentes y ficheros internos: 404, como si no existieran.
#    Todo lo que empieza por "_" en la raiz (_data, _content, _templates, _tools, _docs, _hooks,
#    _build.py, _build.manifest...), los ficheros ocultos menos .well-known, y estos nombres y extensiones.
RewriteRule ^_ - [R=404,L]
#    OLD/ es el nucleo del WordPress anterior (con su wp-config.php): sigue ejecutando PHP en el
#    servidor. Se bloquea al publico; borrarlo lo decide el tecnico. /oficinavirtual/ (la tienda) no se toca.
RewriteRule ^OLD(/|$) - [R=404,L]
RewriteRule (^|/)\.(?!well-known/) - [R=404,L]
RewriteRule (^|/)(requirements\.txt|datos\-centros\.csv|README\.md)$ - [R=404,L]
RewriteRule \.(py|pyc|md|ya?ml|csv|manifest)$ - [R=404,L]

# 2. Redirecciones 301 de URLs antiguas (345), directas a la URL final. La barra final es opcional.
RewriteRule ^ubicaciones\.html/?$ https://www.oficinasya.es/ubicaciones/ [R=301,L,NE]
RewriteRule ^comunidad\.html/?$ https://www.oficinasya.es/comunidad/ [R=301,L,NE]
RewriteRule ^blog\.html/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^aviso\-legal\.html/?$ https://www.oficinasya.es/aviso-legal/ [R=301,L,NE]
RewriteRule ^privacidad\.html/?$ https://www.oficinasya.es/politica-de-privacidad/ [R=301,L,NE]
RewriteRule ^cookies\.html/?$ https://www.oficinasya.es/politica-de-cookies/ [R=301,L,NE]
RewriteRule ^en/locations\.html/?$ https://www.oficinasya.es/en/locations/ [R=301,L,NE]
RewriteRule ^en/community\.html/?$ https://www.oficinasya.es/en/community/ [R=301,L,NE]
RewriteRule ^en/blog\.html/?$ https://www.oficinasya.es/en/blog/ [R=301,L,NE]
RewriteRule ^en/legal\-notice\.html/?$ https://www.oficinasya.es/en/legal-notice/ [R=301,L,NE]
RewriteRule ^en/privacy\-policy\.html/?$ https://www.oficinasya.es/en/privacy-policy/ [R=301,L,NE]
RewriteRule ^en/cookie\-policy\.html/?$ https://www.oficinasya.es/en/cookie-policy/ [R=301,L,NE]
RewriteRule ^despachos/?$ https://www.oficinasya.es/alquiler-de-despachos/ [R=301,L,NE]
RewriteRule ^salas/?$ https://www.oficinasya.es/salas-de-reuniones/ [R=301,L,NE]
RewriteRule ^oficinas\-virtuales/?$ https://www.oficinasya.es/oficina-virtual/ [R=301,L,NE]
RewriteRule ^centros\-de\-negocio/?$ https://www.oficinasya.es/ubicaciones/ [R=301,L,NE]
RewriteRule ^mapa\-general/?$ https://www.oficinasya.es/ubicaciones/ [R=301,L,NE]
RewriteRule ^madrid\-salamanca\-velazquez\-alquiler\-despachos\-oficinas\-velazquez/?$ https://www.oficinasya.es/oficinas-en-madrid/ [R=301,L,NE]
RewriteRule ^madrid\-salamanca\-gasset\-alquiler\-despachos\-oficinas\-gasset/?$ https://www.oficinasya.es/oficinas-en-madrid/ [R=301,L,NE]
RewriteRule ^madrid\-salamanca\-serrano\-alquiler\-despachos\-oficinas\-serrano/?$ https://www.oficinasya.es/oficinas-en-madrid/ [R=301,L,NE]
RewriteRule ^madrid\-castellana\-capitan\-haya\-alquiler\-despachos\-oficinas\-plaza\-castilla/?$ https://www.oficinasya.es/oficinas-en-madrid/ [R=301,L,NE]
RewriteRule ^madrid\-norte\-las\-tablas\-alquiler\-despachos\-oficinas\-las\-tablas/?$ https://www.oficinasya.es/oficinas-en-madrid/ [R=301,L,NE]
RewriteRule ^madrid\-san\-sebastian\-los\-reyes\-alquiler\-despachos\-oficinas\-san\-sebastian\-los\-reyes/?$ https://www.oficinasya.es/oficinas-en-madrid/ [R=301,L,NE]
RewriteRule ^madrid\-pozuelo\-la\-florida\-alquiler\-despachos\-oficinas\-la\-florida/?$ https://www.oficinasya.es/oficinas-en-madrid/ [R=301,L,NE]
RewriteRule ^albacete\-alquiler\-de\-despachos\-y\-oficinas\-en\-albacete/?$ https://www.oficinasya.es/oficinas-en-albacete/ [R=301,L,NE]
RewriteRule ^alicante\-alquiler\-despachos\-oficinas\-alicante/?$ https://www.oficinasya.es/oficinas-en-alicante/ [R=301,L,NE]
RewriteRule ^barcelona\-alquiler\-de\-despachos\-y\-oficinas\-en\-barcelona\-ii/?$ https://www.oficinasya.es/oficinas-en-barcelona/ [R=301,L,NE]
RewriteRule ^barcelona\-alquiler\-de\-oficinas\-y\-despachos\-en\-barcelona/?$ https://www.oficinasya.es/oficinas-en-barcelona/ [R=301,L,NE]
RewriteRule ^barcelona\-alquiler\-de\-oficinas\-y\-despachos\-en\-barcelona\-sant\-gervasi/?$ https://www.oficinasya.es/oficinas-en-barcelona/ [R=301,L,NE]
RewriteRule ^barcelona\-alquiler\-de\-oficinas\-y\-despachos\-en\-barcelona\-plaza\-urquinaona/?$ https://www.oficinasya.es/oficinas-en-barcelona/ [R=301,L,NE]
RewriteRule ^bilbao\-maximo\-aguirre\-alquiler\-de\-despachos\-y\-oficinas\-en\-bilbao/?$ https://www.oficinasya.es/oficinas-en-bilbao/ [R=301,L,NE]
RewriteRule ^bilbao\-albia\-alquiler\-de\-despachos\-y\-oficinas\-en\-bilbao/?$ https://www.oficinasya.es/oficinas-en-bilbao/ [R=301,L,NE]
RewriteRule ^castellon\-alquiler\-despachos\-oficinas\-castellon/?$ https://www.oficinasya.es/oficinas-en-castellon/ [R=301,L,NE]
RewriteRule ^a\-coruna\-alquiler\-de\-despachos\-y\-oficinas\-en\-a\-coruna/?$ https://www.oficinasya.es/oficinas-en-a-coruna/ [R=301,L,NE]
RewriteRule ^malaga\-alquiler\-de\-oficinas\-y\-despachos\-en\-malaga/?$ https://www.oficinasya.es/oficinas-en-malaga/ [R=301,L,NE]
RewriteRule ^merida\-alquiler\-de\-oficinas\-y\-despachos\-en\-merida/?$ https://www.oficinasya.es/oficinas-en-merida/ [R=301,L,NE]
RewriteRule ^murcia\-alquiler\-de\-despachos\-y\-oficinas\-en\-murcia/?$ https://www.oficinasya.es/oficinas-en-murcia/ [R=301,L,NE]
RewriteRule ^murcia\-alquiler\-de\-despachos\-y\-oficinas\-en\-murcia\-poligono\-industrial\-oeste/?$ https://www.oficinasya.es/oficinas-en-murcia/ [R=301,L,NE]
RewriteRule ^coliving\-murcia\-vive\-y\-trabaja\-en\-un\-lugar\-diferente/?$ https://www.oficinasya.es/oficinas-en-murcia/ [R=301,L,NE]
RewriteRule ^coworking\-salamanca\-alquiler\-de\-despachos\-y\-oficinas\-en\-salamanca/?$ https://www.oficinasya.es/oficinas-en-salamanca/ [R=301,L,NE]
RewriteRule ^segovia\-alquiler\-de\-despachos\-y\-oficinas\-en\-avenida\-padre\-claret/?$ https://www.oficinasya.es/oficinas-en-segovia/ [R=301,L,NE]
RewriteRule ^segovia\-alquiler\-de\-despachos\-y\-oficinas\-en\-paseo\-ezequiel\-gonzalez/?$ https://www.oficinasya.es/oficinas-en-segovia/ [R=301,L,NE]
RewriteRule ^sevilla\-alquiler\-de\-oficinas\-y\-despachos\-en\-sevilla/?$ https://www.oficinasya.es/oficinas-en-sevilla/ [R=301,L,NE]
RewriteRule ^sevilla\-alquiler\-de\-oficinas\-y\-despachos\-en\-sevilla\-galia/?$ https://www.oficinasya.es/oficinas-en-sevilla/ [R=301,L,NE]
RewriteRule ^sevilla\-nervion\-alquiler\-de\-oficinas\-y\-despachos\-en\-sevilla/?$ https://www.oficinasya.es/oficinas-en-sevilla/ [R=301,L,NE]
RewriteRule ^tenerife\-alquiler\-de\-despachos\-y\-oficinas\-en\-tenerife/?$ https://www.oficinasya.es/oficinas-en-tenerife/ [R=301,L,NE]
RewriteRule ^tenerife\-alquiler\-de\-despachos\-y\-oficinas\-en\-tenerife\-2/?$ https://www.oficinasya.es/oficinas-en-tenerife/ [R=301,L,NE]
RewriteRule ^valencia\-alquiler\-de\-despachos\-y\-oficinas\-en\-valencia/?$ https://www.oficinasya.es/oficinas-en-valencia/ [R=301,L,NE]
RewriteRule ^vigo\-alquiler\-de\-oficinas\-y\-despachos\-en\-galicia/?$ https://www.oficinasya.es/oficinas-en-vigo/ [R=301,L,NE]
RewriteRule ^zaragoza\-alquiler\-de\-despachos\-y\-oficinas\-en\-zaragoza/?$ https://www.oficinasya.es/oficinas-en-zaragoza/ [R=301,L,NE]
RewriteRule ^centros/alicante/?$ https://www.oficinasya.es/oficinas-en-alicante/ [R=301,L,NE]
RewriteRule ^centros/madrid\-callao/?$ https://www.oficinasya.es/oficinas-en-madrid/ [R=301,L,NE]
RewriteRule ^madrid\-centro\-gran\-via\-callao\-alquiler\-de\-despachos\-y\-oficinas\-en\-callao/?$ https://www.oficinasya.es/oficinas-en-madrid/ [R=301,L,NE]
RewriteRule ^centros/madrid\-capitan\-haya/?$ https://www.oficinasya.es/oficinas-en-madrid/#capitan-haya [R=301,L,NE]
RewriteRule ^centros/madrid\-las\-tablas/?$ https://www.oficinasya.es/oficinas-en-madrid/#las-tablas [R=301,L,NE]
RewriteRule ^centros/madrid\-ortega\-y\-gasset/?$ https://www.oficinasya.es/oficinas-en-madrid/#gasset [R=301,L,NE]
RewriteRule ^centros/madrid\-pozuelo/?$ https://www.oficinasya.es/oficinas-en-madrid/#la-florida-pozuelo [R=301,L,NE]
RewriteRule ^centros/madrid\-san\-sebastian\-de\-los\-reyes/?$ https://www.oficinasya.es/oficinas-en-madrid/#sanse-san-sebastian-de-los-reyes [R=301,L,NE]
RewriteRule ^centros/madrid\-serrano/?$ https://www.oficinasya.es/oficinas-en-madrid/#serrano [R=301,L,NE]
RewriteRule ^centros/madrid\-velazquez/?$ https://www.oficinasya.es/oficinas-en-madrid/#velazquez [R=301,L,NE]
RewriteRule ^coworking\-en\-la\-calle\-serrano\-tu\-oficina\-al\-mejor\-precio/?$ https://www.oficinasya.es/oficinas-en-madrid/#serrano [R=301,L,NE]
RewriteRule ^coworking\-en\-pozuelo\-eficiencia\-y\-eficacia\-a\-tu\-alcance/?$ https://www.oficinasya.es/oficinas-en-madrid/#la-florida-pozuelo [R=301,L,NE]
RewriteRule ^coworking\-en\-san\-sebastian\-de\-los\-reyes\-calidad\-y\-buen\-precio/?$ https://www.oficinasya.es/oficinas-en-madrid/#sanse-san-sebastian-de-los-reyes [R=301,L,NE]
RewriteRule ^coworking\-en\-san\-sebastian\-de\-los\-reyes/?$ https://www.oficinasya.es/oficinas-en-madrid/#sanse-san-sebastian-de-los-reyes [R=301,L,NE]
RewriteRule ^ofertas\-despachos\-sanse\-1/?$ https://www.oficinasya.es/oficinas-en-madrid/#sanse-san-sebastian-de-los-reyes [R=301,L,NE]
RewriteRule ^coworking\-space\-en\-las\-tablas\-tu\-oficina\-corporativa\-mas\-completa/?$ https://www.oficinasya.es/oficinas-en-madrid/#las-tablas [R=301,L,NE]
RewriteRule ^tu\-coworking\-en\-las\-tablas/?$ https://www.oficinasya.es/oficinas-en-madrid/#las-tablas [R=301,L,NE]
RewriteRule ^porque\-tener\-tu\-negocio\-en\-el\-barrio\-de\-salamanca/?$ https://www.oficinasya.es/oficinas-en-madrid/ [R=301,L,NE]
RewriteRule ^oficinas\-ya\-llega\-barcelona/?$ https://www.oficinasya.es/oficinas-en-barcelona/ [R=301,L,NE]
RewriteRule ^oficinas\-ya\-llega\-vigo/?$ https://www.oficinasya.es/oficinas-en-vigo/ [R=301,L,NE]
RewriteRule ^oficinasya\-llega\-a\-murcia/?$ https://www.oficinasya.es/oficinas-en-murcia/ [R=301,L,NE]
RewriteRule ^salamanca\-ciudad\-de\-talento\-e\-innovacion/?$ https://www.oficinasya.es/oficinas-en-salamanca/ [R=301,L,NE]
RewriteRule ^alquiler\-de\-despachos\-en\-madrid\-noviembre\-oferta/?$ https://www.oficinasya.es/oficinas-en-madrid/ [R=301,L,NE]
RewriteRule ^alquiler\-oficinas\-despachos\-madrid\-julio\-septiembre/?$ https://www.oficinasya.es/oficinas-en-madrid/ [R=301,L,NE]
RewriteRule ^alquiler\-oficinas\-despachos\-madrid\-noviembre/?$ https://www.oficinasya.es/oficinas-en-madrid/ [R=301,L,NE]
RewriteRule ^alquiler\-oficinas\-despachos\-madrid\-noviembre\-2/?$ https://www.oficinasya.es/oficinas-en-madrid/ [R=301,L,NE]
RewriteRule ^oferta\-de\-alquiler\-de\-despachos\-en\-madrid\-junio\-2019/?$ https://www.oficinasya.es/oficinas-en-madrid/ [R=301,L,NE]
RewriteRule ^7\-dias\-gratis\-alquiler\-oficinas\-despachos\-madrid\-julio\-septiembre/?$ https://www.oficinasya.es/oficinas-en-madrid/ [R=301,L,NE]
RewriteRule ^oficina/castellon/?$ https://www.oficinasya.es/oficinas-en-castellon/ [R=301,L,NE]
RewriteRule ^oficina/madrid/?$ https://www.oficinasya.es/oficinas-en-madrid/ [R=301,L,NE]
RewriteRule ^oficina/murcia/?$ https://www.oficinasya.es/oficinas-en-murcia/ [R=301,L,NE]
RewriteRule ^oficina/sevilla/?$ https://www.oficinasya.es/oficinas-en-sevilla/ [R=301,L,NE]
RewriteRule ^oficinas/alicante/?$ https://www.oficinasya.es/oficinas-en-alicante/ [R=301,L,NE]
RewriteRule ^oficinas/barcelona\-alquiler\-oficinas\-despachos\-barcelona/?$ https://www.oficinasya.es/oficinas-en-barcelona/ [R=301,L,NE]
RewriteRule ^oficinas/callao/?$ https://www.oficinasya.es/oficinas-en-madrid/ [R=301,L,NE]
RewriteRule ^oficinas/castellon/?$ https://www.oficinasya.es/oficinas-en-castellon/ [R=301,L,NE]
RewriteRule ^oficinas/gasset/?$ https://www.oficinasya.es/oficinas-en-madrid/#gasset [R=301,L,NE]
RewriteRule ^oficinas/la\-florida/?$ https://www.oficinasya.es/oficinas-en-madrid/#la-florida-pozuelo [R=301,L,NE]
RewriteRule ^oficinas/las\-tablas/?$ https://www.oficinasya.es/oficinas-en-madrid/#las-tablas [R=301,L,NE]
RewriteRule ^oficinas/murcia\-alquiler\-de\-despachos\-y\-oficinas\-en\-murcia/?$ https://www.oficinasya.es/oficinas-en-murcia/ [R=301,L,NE]
RewriteRule ^oficinas/plaza\-de\-castilla\-alquiler\-de\-despachos\-y\-oficinas\-en\-plaza\-de\-castilla/?$ https://www.oficinasya.es/oficinas-en-madrid/#capitan-haya [R=301,L,NE]
RewriteRule ^oficinas/san\-sebastian\-de\-los\-reyes/?$ https://www.oficinasya.es/oficinas-en-madrid/#sanse-san-sebastian-de-los-reyes [R=301,L,NE]
RewriteRule ^oficinas/serrano/?$ https://www.oficinasya.es/oficinas-en-madrid/#serrano [R=301,L,NE]
RewriteRule ^oficinas/sevilla\-alquiler\-de\-oficinas\-y\-despachos\-en\-sevilla/?$ https://www.oficinasya.es/oficinas-en-sevilla/ [R=301,L,NE]
RewriteRule ^oficinas/valencia\-alquiler\-de\-despachos\-y\-oficinas\-en\-valencia/?$ https://www.oficinasya.es/oficinas-en-valencia/ [R=301,L,NE]
RewriteRule ^oficinas/velazquez/?$ https://www.oficinasya.es/oficinas-en-madrid/#velazquez [R=301,L,NE]
RewriteRule ^oficinas/vigo\-alquiler\-oficinas\-despachos\-galicia/?$ https://www.oficinasya.es/oficinas-en-vigo/ [R=301,L,NE]
RewriteRule ^portfolio_category/castellon/?$ https://www.oficinasya.es/oficinas-en-castellon/ [R=301,L,NE]
RewriteRule ^portfolio_category/madrid/?$ https://www.oficinasya.es/oficinas-en-madrid/ [R=301,L,NE]
RewriteRule ^alquilar\-despacho\-horas/?$ https://www.oficinasya.es/alquiler-de-despachos/ [R=301,L,NE]
RewriteRule ^ofertas\-despachos/?$ https://www.oficinasya.es/alquiler-de-despachos/ [R=301,L,NE]
RewriteRule ^7\-dias\-gratis/?$ https://www.oficinasya.es/alquiler-de-despachos/ [R=301,L,NE]
RewriteRule ^oferta\-oficina\-virtual/?$ https://www.oficinasya.es/oficina-virtual/ [R=301,L,NE]
RewriteRule ^domiciliacion\-de\-sociedades\-desde\-solo\-1e\-al\-dia/?$ https://www.oficinasya.es/oficina-virtual/ [R=301,L,NE]
RewriteRule ^cambiodesedesocial/?$ https://www.oficinasya.es/oficina-virtual/ [R=301,L,NE]
RewriteRule ^oficinas\-vistuales/?$ https://www.oficinasya.es/oficina-virtual/ [R=301,L,NE]
RewriteRule ^smart\-office\-lo\-que\-quieres\-como\-quieres\-cuando\-quieres/?$ https://www.oficinasya.es/oficina-virtual/#smart-office [R=301,L,NE]
RewriteRule ^quienes\-somos/?$ https://www.oficinasya.es/ [R=301,L,NE]
RewriteRule ^contacto/?$ https://www.oficinasya.es/#contact [R=301,L,NE]
RewriteRule ^concertar\-visita/?$ https://www.oficinasya.es/#contact [R=301,L,NE]
RewriteRule ^gracias/?$ https://www.oficinasya.es/ [R=301,L,NE]
RewriteRule ^politica\-de\-privacidad\-2/?$ https://www.oficinasya.es/politica-de-privacidad/ [R=301,L,NE]
RewriteRule ^experiencia\-en\-coworking/politica\-de\-privacidad/?$ https://www.oficinasya.es/politica-de-privacidad/ [R=301,L,NE]
RewriteRule ^black\-friday\-2018/?$ https://www.oficinasya.es/ [R=301,L,NE]
RewriteRule ^black\-friday\-2018\-2/?$ https://www.oficinasya.es/ [R=301,L,NE]
RewriteRule ^black\-friday\-2019\-oficinas\-ya/?$ https://www.oficinasya.es/ [R=301,L,NE]
RewriteRule ^portfolio/?$ https://www.oficinasya.es/ [R=301,L,NE]
RewriteRule ^project/?$ https://www.oficinasya.es/ [R=301,L,NE]
RewriteRule ^10\-cosas\-aprender\-del\-marketing\-apple/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^10\-cosas\-que\-no\-debes\-decir\-en\-una\-entrevista\-de\-trabajo/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^abogados\-las\-tablas\-nos\-cuenta\-su\-experiencia\-en\-un\-coworking/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^abre\-tu\-negocio\-a\-otros\-paises\-con\-el\-seo\-multirregional/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^abrir\-un\-negocio\-en\-el\-momento\-actual\-no\-es\-de\-locos/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^adios\-a\-telegram\-motivos\-de\-su\-cierre\-y\-aplicaciones\-alternativas/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^ahorrar\-siendo\-autonomo\-es\-posible/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^alcanza\-todos\-tus\-objetivos\-para\-el\-nuevo\-ano/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^alfa\-inmobiliaria\-nos\-cuenta\-su\-experiencia\-en\-un\-coworking/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^alternativas\-a\-las\-reuniones\-presenciales/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^ambialia\-nos\-cuenta\-su\-experiencia\-en\-un\-coworking/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^aprende\-a\-priorizar\-de\-forma\-rapida\-y\-sencilla/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^aprende\-a\-tener\-iniciativa/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^aprovecha\-las\-ventajas\-de\-la\-ia\-en\-tu\-negocio\-con\-estas\-herramientas\-gratuitas/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^asi\-funciona\-el\-tinder\-para\-empresas\-nosotros\-no\-hacemos\-nada\-es\-la\-maquina\-la\-que\-lo\-hace/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^asi\-pueden\-los\-influencers\-dar\-visibilidad\-a\-tu\-negocio/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^aumenta\-la\-motivacion\-laboral\-de\-tu\-equipo/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^blog\-corporativo\-beneficios\-reglas\-basicas/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^brainstorming\-ideas\-para\-dar\-un\-giro\-a\-tu\-negocio/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^buscas\-planes\-para\-estas\-fiestas\-aqui\-los\-tienes/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^buuuuuh\-los\-mejores\-planes\-para\-la\-noche\-de\-halloween/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^carsharing\-o\-coche\-privado/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^claves\-de\-la\-nueva\-norma\-de\-registro\-de\-la\-jornada\-laboral/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^claves\-para\-mantener\-la\-lealtad\-de\-tus\-clientes/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^claves\-para\-posicionar\-tu\-negocio\-en\-google/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^claves\-para\-que\-tu\-email\-marketing\-sea\-efectivo/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^club\-privado\-carsharing\-oficinas\-ya\-callao/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^como\-aplicar\-la\-subida\-del\-smi\-para\-autonomos\-y\-empresas/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^como\-aprender\-a\-tener\-paciencia/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^como\-aumentar\-la\-motivacion\-de\-tu\-equipo\-de\-trabajo/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^como\-aumentar\-tus\-ventas\-parte\-1/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^como\-aumentar\-tus\-ventas\-parte\-2/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^como\-compartir\-tu\-dni\-por\-internet\-sin\-riesgos\-2\-2/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^como\-contribuyen\-los\-coworkings\-al\-ahorro\-energetico/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^como\-crear\-un\-buen\-entorno\-laboral/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^como\-darle\-valor\-de\-lujo\-a\-tu\-producto/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^como\-elijo\-el\-coworking\-mas\-apropiado\-para\-mi\-negocio/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^como\-evitar\-los\-conflictos\-laborales/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^como\-evitar\-que\-roben\-tus\-datos\-al\-pagar\-con\-el\-movil/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^como\-funciona\-un\-coworking/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^como\-google\-puede\-ayudar\-a\-tu\-negocio\-sin\-coste\-para\-ti/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^como\-hacer\-que\-tu\-equipo\-de\-trabajo\-este\-siempre\-motivado/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^como\-hacer\-que\-tu\-pequeno\-negocio\-parezca\-una\-gran\-empresa\-caso\-practico/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^como\-mejorar\-tu\-economia/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^como\-reducir\-gastos\-de\-oficina\-sin\-perder\-calidad\-oficina\-tradicional\-vs\-coworking/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^como\-responder\-a\-las\-objeciones\-mas\-comunes\-de\-los\-clientes/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^como\-sacar\-partido\-al\-tiempo/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^como\-sacarle\-partido\-a\-linkedin/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^como\-superar\-el\-miedo\-a\-hablar\-en\-publico/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^como\-tener\-exito\-en\-el\-trabajo/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^como\-un\-coworking\-hace\-crecer\-tu\-negocio\-caso\-real/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^conciliacion\-la\-gran\-odisea\-del\-autonomo/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^conectar\-mejor\-con\-tus\-clientes\-mediante\-un\-buen\-relato/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^conoceis\-google\-activate/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^conseguir\-clientes\-nuevos\-y\-retener\-a\-los\-actuales\-durante\-el\-covid19\-es\-posible/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^consejos\-para\-combatir\-las\-olas\-de\-calor\-en\-verano/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^consejos\-para\-ser\-un\-buen\-lider/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^cosas\-deberias\-saber\-abrir\-negocio/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^coworking\-como\-solucion\-al\-estres/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^coworking\-para\-abogados\-privacidad\-y\-profesionalidad/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^coworking\-y\-networking\-conceptos\-clave\-para\-todo\-emprendedor/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^coworking\-y\-networking\-contactos\-laborales\-de\-calidad/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^coworkings\-espacios\-de\-trabajo\-que\-unen\-vida\-social\-y\-laboral/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^creditos\-ico\-paso\-a\-paso/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^de\-la\-oficina\-tradicional\-al\-coworking/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^descubre\-estos\-trucos\-para\-disparar\-tu\-productividad/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^destacar\-curriculum\-la\-competencia/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^diez\-tips\-para\-una\-oratoria\-insuperable/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^diferencias\-entre\-coworking\-oficina\-compartida\-y\-centro\-de\-negocios\-con\-coworking/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^digital\-logic\-system\-nos\-cuenta\-su\-experiencia\-en\-un\-coworking/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^digitalizacion\-analisis\-y\-estrategia/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^el\-coworking\-se\-impone\-en\-el\-sector\-de\-las\-oficinas/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^el\-coworking\-se\-transforma\-en\-oficina\-de\-contingencia/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^el\-coworking\-y\-la\-mujer\-emprendedora/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^el\-creador\-de\-chatgpt\-revela\-sus\-consejos\-para\-emprendedores/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^el\-enriquecimiento\-personal\-y\-laboral\-las\-nuevas\-prioridades/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^el\-gobierno\-actualiza\-el\-calendario\-de\-ayudas\-para\-autonomos/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^el\-gobierno\-anuncia\-el\-nuevo\-kit\-consulting\-para\-pymes/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^el\-nuevo\-coworking\-post\-covid/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^el\-optimismo\-concepto\-clave\-para\-el\-mundo\-laboral/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^el\-precio\-de\-la\-gasolina\-y\-el\-diesel\-se\-ha\-disparado\-en\-2024\-y\-estas\-son\-las\-razones/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^el\-teletrabajo\-ha\-llegado\-a\-su\-fin/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^el\-teletrabajo\-reduce\-la\-productividad\-laboral/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^el\-trabajo\-100\-remoto\-no\-arraiga\-en\-espana/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^eleva\-tu\-economia\-de\-nivel\-con\-estos\-consejos/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^elige\-coworking\-y\-gana\-la\-partida/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^emprendedor\-aumenta\-tus\-probabilidades\-de\-exito/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^emprender\-con\-exito\-2021/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^emprender\-con\-exito/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^en\-oficinas\-ya\-no\-todo\-es\-trabajar/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^enfrentarse\-una\-negociacion\-salir\-victorioso/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^eres\-feliz\-en\-tu\-trabajo/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^es\-el\-verano\-un\-buen\-momento\-para\-emprender/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^esta\-tu\-empresa\-preparada\-para\-afrontar\-el\-coronavirus/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^estas\-son\-las\-cadenas\-de\-gasolineras\-mas\-baratas\-segun\-la\-ocu/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^estas\-son\-las\-mejores\-apps\-para\-aprovechar\-el\-certificado\-digital\-en\-tu\-movil/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^estas\-son\-las\-novedades\-en\-el\-impuesto\-de\-sociedades\-de\-2024/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^estos\-son\-los\-nuevos\-tramos\-para\-pagar\-la\-cuota\-minima\-de\-autonomos\-en\-2024/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^estres\-laboral\-por\-el\-covid\-deshazte\-de\-el/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^eventos\-que\-no\-te\-puedes\-perder\-siendo\-emprendedor/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^experiencia\-en\-coworking/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^fgr\-asesoria\-energetica\-nos\-cuenta\-su\-experiencia\-en\-un\-coworking/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^franquicias\-ventajas\-y\-desventajas/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^freshrules\-nos\-cuenta\-su\-experiencia\-en\-un\-coworking/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^gabinete\-de\-psicologia\-sian\-nos\-cuenta\-su\-experiencia\-en\-un\-coworking/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^gana\-velocidad\-en\-tu\-ordenador/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^genera\-ideas\-de\-negocio\-con\-este\-truco/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^google\-tendra\-un\-nuevo\-servicio\-gratuito\-ya\-no\-habra\-que\-pagar\-por\-su\-vpn/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^guia\-para\-irte\-de\-vacaciones\-en\-una\-camper\-este\-verano/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^habitos\-comunes\-de\-las\-personas\-super\-productivas/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^hacienda\-simplifica\-las\-rectificaciones\-en\-las\-declaraciones\-de\-los\-autonomos/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^hay\-menos\-oficinas\-vacias\-en\-alquiler\-en\-el\-centro\-de\-madrid\-que\-en\-londres/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^herramientas\-para\-trabajar\-desde\-casa/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^hola\-conoces\-a\-luzia/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^hr\-consultores\-nos\-cuenta\-su\-experiencia\-en\-un\-coworking/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^inteligencia\-artificial\-en\-pymes\-innovacion\-y\-competitividad\-en\-el\-mercado/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^la\-estafa\-que\-te\-hara\-leer\-tu\-correo\-con\-mucha\-atencion/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^la\-importancia\-de\-escuchar\-a\-tus\-clientes/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^la\-loteria\-de\-navidad\-la\-veis\-hacienda\-y\-tu/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^la\-oficina\-flexible\-la\-forma\-de\-trabajo\-mas\-demandada/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^la\-oficina\-flexible\-la\-solucion\-favorita\-de\-startups\-pymes\-y\-emprendedores/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^la\-semana\-laboral\-de\-4\-dias\-al\-estilo\-aleman/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^las\-5\-mejores\-tecnicas\-para\-cerrar\-una\-venta/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^las\-oficinas\-sostenibles\-que\-te\-ayudan\-a\-crecer\-y\-reducen\-tus\-gastos/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^lecciones\-aprendidas\-con\-la\-crisis\-del\-covid19/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^llega\-el\-1o\-concurso\-de\-fotografia\-navidena\-de\-oficinas\-ya/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^llega\-la\-cabalgata\-de\-reyes\-a\-madrid\-fechas\-horarios\-y\-recorridos/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^los\-12\-pasos\-de\-una\-presentacion\-perfecta/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^los\-3\-problemas\-mas\-comunes\-de\-un\-emprendedor\-y\-sus\-soluciones/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^los\-6\-mejores\-programas\-erp\-de\-software\-libre\-o\-no/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^los\-autonomos\-ya\-pueden\-consultar\-sus\-datos\-en\-hacienda\-para\-la\-renta/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^los\-coworkings\-de\-oficinas\-ya\-continuan\-operativos\-pese\-a\-la\-gran\-nevada/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^los\-coworkings\-mantienen\-activo\-tu\-negocio\-durante\-tus\-vacaciones/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^los\-destinos\-turisticos\-con\-mas\-sol\-del\-mundo/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^los\-mejores\-descuentos\-encontraras\-este\-black\-friday/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^marca\-personal\-todo\-lo\-que\-necesitas\-saber/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^mas\-del\-65\-de\-abogados\-tiene\-una\-oficina\-virtual/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^mas\-productivo\-trabajo/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^mergetix\-nos\-cuenta\-su\-experiencia\-en\-un\-coworking/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^mi\-dia\-en\-un\-coworking/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^montar\-un\-negocio/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^motivos\-por\-los\-que\-los\-autonomos\-pueden\-perder\-la\-tarifa\-plana\-en\-2024/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^multas\-de\-hasta\-10\-000\-euros\-a\-los\-autonomos\-que\-no\-reduzcan\-la\-jornada\-a\-385\-horas/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^negocio\-online\-claves\-negocio\-sea\-exito/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^networking\-como\-ser\-el\-crack\-de\-los\-contactos/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^neuromarketing\-estrategias\-y\-claves/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^no\-dejes\-pasar\-estos\-gastos\-desgravables\-en\-la\-renta\-2023\-2024/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^oficina\-barata\-en\-madrid\-si\-existe/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^oficina\-virtual\-la\-solucion\-negocio/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^oficina\-vs\-teletrabajo\-and\-the\-real\-winner\-is/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^oficinas\-con\-corazon\-clave\-en\-el\-enriquecimiento\-personal\-y\-laboral/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^oficinas\-nuevos\-cambios\-se\-avecinan/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^oficinas\-para\-la\-contencion\-del\-coronavirus/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^oficinas\-post\-covid\-nuevas\-necesidades\-de\-los\-trabajadores/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^oficinas\-ya\-abrira\-un\-nuevo\-coworking\-en\-el\-amazonas/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^oficinas\-ya\-el\-coworking\-seguro\-frente\-al\-covid\-19/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^oficinas\-ya\-inaugura\-su\-nuevo\-centro\-sensorial/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^pinta\-vida\-naranja/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^ponte\-tu\-mascara\-ha\-llegado\-el\-carnaval/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^por\-que\-algunas\-personas\-trabajan\-mejor\-desde\-casa\-que\-otras/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^por\-que\-el\-trabajo\-a\-distancia\-es\-el\-preferido\-de\-los\-millennials\-y\-nomadas\-digitales/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^potencia\-ya\-el\-valor\-de\-tu\-marca\-y\-llevalo\-al\-siguiente\-nivel/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^preguntas\-mas\-comunes\-entrevista\-trabajo/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^preguntas\-trampa\-mas\-comunes\-en\-una\-entrevista/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^preparate\-para\-la\-convergencia\-real\-tu\-smartphone\-pronto\-sera\-tu\-pc/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^puedes\-circular\-con\-tu\-vehiculo\-en\-las\-zbe/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^que\-cualidades\-debe\-tener\-el\-cofundador\-ideal/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^que\-es\-una\-oficina\-virtual/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^que\-gastos\-puedes\-deducirte\-en\-la\-renta\-si\-eres\-trabajador\-por\-cuenta\-ajena/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^que\-requisitos\-debe\-cumplir\-un\-coworking\-en\-tiempos\-de\-covid/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^que\-va\-a\-preocupar\-a\-las\-pyme\-en\-2024/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^rastreadores\-privados\-en\-los\-coworkings\-de\-oficinas\-ya/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^redes\-sociales\-de\-empresa\-obten\-el\-maximo\-rendimiento/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^renfe\-endurece\-las\-condiciones\-para\-devolver\-dinero\-por\-retrasos/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^sabes\-mantener\-la\-calma/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^sabes\-si\-tu\-compania\-esta\-a\-la\-ultima\-en\-medios\-tecnologicos/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^seguridad\-social\-pide\-datos\-a\-los\-autonomos\-para\-notificarles\-sus\-futuras\-cuotas/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^si\-operas\-en\-wallapop\-o\-en\-airbnb\-hacienda\-quiere\-hablar\-contigo/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^si\-teletrabajas\-haz\-clic\-aqui/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^si\-usas\-bizum\-tienes\-que\-declararte\-ante\-hacienda/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^silbana\-nos\-cuenta\-su\-experiencia\-en\-un\-coworking/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^storytellin\-iii\-los/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^storytelling\-ii\-vender\-con\-cuentos/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^storytelling\-vende\-con\-una\-buena\-historia/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^te\-traemos\-las\-startups\-mas\-innovadoras\-del\-mundo/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^teletrabajo\-sin\-complicaciones/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^tesoros\-que\-podrias\-tener\-olvidados\-en\-el\-trasero/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^tienes\-dudas\-sobre\-la\-factura\-electronica\-sigue\-leyendo/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^tips\-para\-triunfar\-en\-el\-networking/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^todo\-lo\-que\-necesitas\-para\-convertirte\-en\-un\-experto\-en\-ia/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^todo\-lo\-que\-necesitas\-saber\-sobre\-la\-nueva\-ley\-de\-teletrabajo/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^todo\-lo\-que\-requieres\-saber\-sobre\-el\-pago\-con\-criptomonedas/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^toni\-bassols\-nos\-cuenta\-su\-experiencia\-en\-un\-coworking/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^traslado\-masivo\-de\-pequenas\-y\-medianas\-empresas\-a\-business\-centers/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^traslot\-102\-nos\-cuenta\-su\-experiencia\-en\-un\-coworking/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^trucos\-para\-vencer\-el\-sueno\-en\-el\-trabajo/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^tu\-compania\-esta\-a\-la\-ultima\-en\-medios\-tecnologicos/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^ultima\-oportunidad\-para\-ajustar\-la\-cuota\-de\-autonomos/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^un\-metodo\-poco\-conocido\-por\-los\-autonomos\-les\-permite\-hacer\-la\-renta\-de\-forma\-casi\-automatica/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^ventajas\-de\-los\-business\-centers\-frente\-a\-las\-oficinas\-tradicionales/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^ventajas\-del\-networking/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^waze\-o\-google\-maps\-que\-navegador\-es\-mas\-completo/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^y\-si\-te\-dijesen\-que\-nunca\-va\-a\-haber\-vacuna\-para\-el\-covid/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^ya\-es\-oficial\-hacienda\-obligara\-a\-hacer\-la\-proxima\-declaracion\-de\-la\-renta\-solo\-por\-internet/?$ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^category/ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^tag/ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^author/ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^actividades/ https://www.oficinasya.es/comunidad/ [R=301,L,NE]
RewriteRule ^miembros/ https://www.oficinasya.es/comunidad/ [R=301,L,NE]
RewriteRule ^2017/ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^2018/ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^2019/ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^2020/ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^2021/ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^blog/page/ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^web/ https://www.oficinasya.es/blog/ [R=301,L,NE]
RewriteRule ^centros/madrid\-callao/page/ https://www.oficinasya.es/oficinas-en-madrid/ [R=301,L,NE]
RewriteRule ^centros/madrid\-capitan\-haya/page/ https://www.oficinasya.es/oficinas-en-madrid/#capitan-haya [R=301,L,NE]
RewriteRule ^centros/madrid\-ortega\-y\-gasset/page/ https://www.oficinasya.es/oficinas-en-madrid/#gasset [R=301,L,NE]
RewriteRule ^centros/madrid\-pozuelo/page/ https://www.oficinasya.es/oficinas-en-madrid/#la-florida-pozuelo [R=301,L,NE]
RewriteRule ^centros/madrid\-san\-sebastian\-de\-los\-reyes/page/ https://www.oficinasya.es/oficinas-en-madrid/#sanse-san-sebastian-de-los-reyes [R=301,L,NE]
RewriteRule ^centros/madrid\-serrano/page/ https://www.oficinasya.es/oficinas-en-madrid/#serrano [R=301,L,NE]
RewriteRule ^centros/madrid\-velazquez/page/ https://www.oficinasya.es/oficinas-en-madrid/#velazquez [R=301,L,NE]
RewriteRule ^centros/ https://www.oficinasya.es/ubicaciones/ [R=301,L,NE]
RewriteRule ^oficinas/ https://www.oficinasya.es/ubicaciones/ [R=301,L,NE]
RewriteRule ^oficina/ https://www.oficinasya.es/ubicaciones/ [R=301,L,NE]
RewriteRule ^portfolio_category/ https://www.oficinasya.es/ubicaciones/ [R=301,L,NE]

# 3. Carpeta sin barra final (/blog -> /blog/) en un salto y en https. Sin esta regla Apache
#    responde con http:// y el hosting vuelve a https: dos saltos de mas.
RewriteCond %{REQUEST_FILENAME} -d
RewriteRule ^(.+[^/])$ https://www.oficinasya.es/$1/ [R=301,L]

# 4. Dominio canonico: oficinasya.es -> www.oficinasya.es, en un solo salto y ya en https (lo que no haya redirigido antes).
#    (El paso de http a https lo hace hoy el hosting delante de Apache; por eso no hay regla
#    "%{HTTPS} off": detras de un proxy daria un bucle de redirecciones.)
RewriteCond %{HTTP_HOST} ^oficinasya\.es$ [NC]
RewriteRule ^(.*)$ https://www.oficinasya.es/$1 [R=301,L]
# END OficinasYA
```

---

## nginx (solo si el servidor no lee `.htaccess`)

Esto lo pega el hosting, no se sube por FTP. Tiene tres partes: A va en el bloque `http { }`, B es un `server` propio para el dominio sin www, y C va dentro del `server { }` de www.oficinasya.es, antes de cualquier otro `location`.
Después: `nginx -t` (debe decir `syntax is ok`) y `nginx -s reload`.

```nginx
# nginx para OficinasYA! -- generado por `python _build.py --nginx` desde _data/redirects.yml.

# ---- A) En el bloque http { } (fuera de cualquier server): tabla de redirecciones.
map $uri $oya_redirect {
    default "";
    /ubicaciones.html /ubicaciones/;
    /comunidad.html /comunidad/;
    /blog.html /blog/;
    /aviso-legal.html /aviso-legal/;
    /privacidad.html /politica-de-privacidad/;
    /cookies.html /politica-de-cookies/;
    /en/locations.html /en/locations/;
    /en/community.html /en/community/;
    /en/blog.html /en/blog/;
    /en/legal-notice.html /en/legal-notice/;
    /en/privacy-policy.html /en/privacy-policy/;
    /en/cookie-policy.html /en/cookie-policy/;
    /despachos/ /alquiler-de-despachos/;
    /despachos /alquiler-de-despachos/;
    /salas/ /salas-de-reuniones/;
    /salas /salas-de-reuniones/;
    /oficinas-virtuales/ /oficina-virtual/;
    /oficinas-virtuales /oficina-virtual/;
    /centros-de-negocio/ /ubicaciones/;
    /centros-de-negocio /ubicaciones/;
    /mapa-general/ /ubicaciones/;
    /mapa-general /ubicaciones/;
    /madrid-salamanca-velazquez-alquiler-despachos-oficinas-velazquez/ /oficinas-en-madrid/;
    /madrid-salamanca-velazquez-alquiler-despachos-oficinas-velazquez /oficinas-en-madrid/;
    /madrid-salamanca-gasset-alquiler-despachos-oficinas-gasset/ /oficinas-en-madrid/;
    /madrid-salamanca-gasset-alquiler-despachos-oficinas-gasset /oficinas-en-madrid/;
    /madrid-salamanca-serrano-alquiler-despachos-oficinas-serrano/ /oficinas-en-madrid/;
    /madrid-salamanca-serrano-alquiler-despachos-oficinas-serrano /oficinas-en-madrid/;
    /madrid-castellana-capitan-haya-alquiler-despachos-oficinas-plaza-castilla/ /oficinas-en-madrid/;
    /madrid-castellana-capitan-haya-alquiler-despachos-oficinas-plaza-castilla /oficinas-en-madrid/;
    /madrid-norte-las-tablas-alquiler-despachos-oficinas-las-tablas/ /oficinas-en-madrid/;
    /madrid-norte-las-tablas-alquiler-despachos-oficinas-las-tablas /oficinas-en-madrid/;
    /madrid-san-sebastian-los-reyes-alquiler-despachos-oficinas-san-sebastian-los-reyes/ /oficinas-en-madrid/;
    /madrid-san-sebastian-los-reyes-alquiler-despachos-oficinas-san-sebastian-los-reyes /oficinas-en-madrid/;
    /madrid-pozuelo-la-florida-alquiler-despachos-oficinas-la-florida/ /oficinas-en-madrid/;
    /madrid-pozuelo-la-florida-alquiler-despachos-oficinas-la-florida /oficinas-en-madrid/;
    /albacete-alquiler-de-despachos-y-oficinas-en-albacete/ /oficinas-en-albacete/;
    /albacete-alquiler-de-despachos-y-oficinas-en-albacete /oficinas-en-albacete/;
    /alicante-alquiler-despachos-oficinas-alicante/ /oficinas-en-alicante/;
    /alicante-alquiler-despachos-oficinas-alicante /oficinas-en-alicante/;
    /barcelona-alquiler-de-despachos-y-oficinas-en-barcelona-ii/ /oficinas-en-barcelona/;
    /barcelona-alquiler-de-despachos-y-oficinas-en-barcelona-ii /oficinas-en-barcelona/;
    /barcelona-alquiler-de-oficinas-y-despachos-en-barcelona/ /oficinas-en-barcelona/;
    /barcelona-alquiler-de-oficinas-y-despachos-en-barcelona /oficinas-en-barcelona/;
    /barcelona-alquiler-de-oficinas-y-despachos-en-barcelona-sant-gervasi/ /oficinas-en-barcelona/;
    /barcelona-alquiler-de-oficinas-y-despachos-en-barcelona-sant-gervasi /oficinas-en-barcelona/;
    /barcelona-alquiler-de-oficinas-y-despachos-en-barcelona-plaza-urquinaona/ /oficinas-en-barcelona/;
    /barcelona-alquiler-de-oficinas-y-despachos-en-barcelona-plaza-urquinaona /oficinas-en-barcelona/;
    /bilbao-maximo-aguirre-alquiler-de-despachos-y-oficinas-en-bilbao/ /oficinas-en-bilbao/;
    /bilbao-maximo-aguirre-alquiler-de-despachos-y-oficinas-en-bilbao /oficinas-en-bilbao/;
    /bilbao-albia-alquiler-de-despachos-y-oficinas-en-bilbao/ /oficinas-en-bilbao/;
    /bilbao-albia-alquiler-de-despachos-y-oficinas-en-bilbao /oficinas-en-bilbao/;
    /castellon-alquiler-despachos-oficinas-castellon/ /oficinas-en-castellon/;
    /castellon-alquiler-despachos-oficinas-castellon /oficinas-en-castellon/;
    /a-coruna-alquiler-de-despachos-y-oficinas-en-a-coruna/ /oficinas-en-a-coruna/;
    /a-coruna-alquiler-de-despachos-y-oficinas-en-a-coruna /oficinas-en-a-coruna/;
    /malaga-alquiler-de-oficinas-y-despachos-en-malaga/ /oficinas-en-malaga/;
    /malaga-alquiler-de-oficinas-y-despachos-en-malaga /oficinas-en-malaga/;
    /merida-alquiler-de-oficinas-y-despachos-en-merida/ /oficinas-en-merida/;
    /merida-alquiler-de-oficinas-y-despachos-en-merida /oficinas-en-merida/;
    /murcia-alquiler-de-despachos-y-oficinas-en-murcia/ /oficinas-en-murcia/;
    /murcia-alquiler-de-despachos-y-oficinas-en-murcia /oficinas-en-murcia/;
    /murcia-alquiler-de-despachos-y-oficinas-en-murcia-poligono-industrial-oeste/ /oficinas-en-murcia/;
    /murcia-alquiler-de-despachos-y-oficinas-en-murcia-poligono-industrial-oeste /oficinas-en-murcia/;
    /coliving-murcia-vive-y-trabaja-en-un-lugar-diferente/ /oficinas-en-murcia/;
    /coliving-murcia-vive-y-trabaja-en-un-lugar-diferente /oficinas-en-murcia/;
    /coworking-salamanca-alquiler-de-despachos-y-oficinas-en-salamanca/ /oficinas-en-salamanca/;
    /coworking-salamanca-alquiler-de-despachos-y-oficinas-en-salamanca /oficinas-en-salamanca/;
    /segovia-alquiler-de-despachos-y-oficinas-en-avenida-padre-claret/ /oficinas-en-segovia/;
    /segovia-alquiler-de-despachos-y-oficinas-en-avenida-padre-claret /oficinas-en-segovia/;
    /segovia-alquiler-de-despachos-y-oficinas-en-paseo-ezequiel-gonzalez/ /oficinas-en-segovia/;
    /segovia-alquiler-de-despachos-y-oficinas-en-paseo-ezequiel-gonzalez /oficinas-en-segovia/;
    /sevilla-alquiler-de-oficinas-y-despachos-en-sevilla/ /oficinas-en-sevilla/;
    /sevilla-alquiler-de-oficinas-y-despachos-en-sevilla /oficinas-en-sevilla/;
    /sevilla-alquiler-de-oficinas-y-despachos-en-sevilla-galia/ /oficinas-en-sevilla/;
    /sevilla-alquiler-de-oficinas-y-despachos-en-sevilla-galia /oficinas-en-sevilla/;
    /sevilla-nervion-alquiler-de-oficinas-y-despachos-en-sevilla/ /oficinas-en-sevilla/;
    /sevilla-nervion-alquiler-de-oficinas-y-despachos-en-sevilla /oficinas-en-sevilla/;
    /tenerife-alquiler-de-despachos-y-oficinas-en-tenerife/ /oficinas-en-tenerife/;
    /tenerife-alquiler-de-despachos-y-oficinas-en-tenerife /oficinas-en-tenerife/;
    /tenerife-alquiler-de-despachos-y-oficinas-en-tenerife-2/ /oficinas-en-tenerife/;
    /tenerife-alquiler-de-despachos-y-oficinas-en-tenerife-2 /oficinas-en-tenerife/;
    /valencia-alquiler-de-despachos-y-oficinas-en-valencia/ /oficinas-en-valencia/;
    /valencia-alquiler-de-despachos-y-oficinas-en-valencia /oficinas-en-valencia/;
    /vigo-alquiler-de-oficinas-y-despachos-en-galicia/ /oficinas-en-vigo/;
    /vigo-alquiler-de-oficinas-y-despachos-en-galicia /oficinas-en-vigo/;
    /zaragoza-alquiler-de-despachos-y-oficinas-en-zaragoza/ /oficinas-en-zaragoza/;
    /zaragoza-alquiler-de-despachos-y-oficinas-en-zaragoza /oficinas-en-zaragoza/;
    /centros/alicante/ /oficinas-en-alicante/;
    /centros/alicante /oficinas-en-alicante/;
    /centros/madrid-callao/ /oficinas-en-madrid/;
    /centros/madrid-callao /oficinas-en-madrid/;
    /madrid-centro-gran-via-callao-alquiler-de-despachos-y-oficinas-en-callao/ /oficinas-en-madrid/;
    /madrid-centro-gran-via-callao-alquiler-de-despachos-y-oficinas-en-callao /oficinas-en-madrid/;
    /centros/madrid-capitan-haya/ /oficinas-en-madrid/#capitan-haya;
    /centros/madrid-capitan-haya /oficinas-en-madrid/#capitan-haya;
    /centros/madrid-las-tablas/ /oficinas-en-madrid/#las-tablas;
    /centros/madrid-las-tablas /oficinas-en-madrid/#las-tablas;
    /centros/madrid-ortega-y-gasset/ /oficinas-en-madrid/#gasset;
    /centros/madrid-ortega-y-gasset /oficinas-en-madrid/#gasset;
    /centros/madrid-pozuelo/ /oficinas-en-madrid/#la-florida-pozuelo;
    /centros/madrid-pozuelo /oficinas-en-madrid/#la-florida-pozuelo;
    /centros/madrid-san-sebastian-de-los-reyes/ /oficinas-en-madrid/#sanse-san-sebastian-de-los-reyes;
    /centros/madrid-san-sebastian-de-los-reyes /oficinas-en-madrid/#sanse-san-sebastian-de-los-reyes;
    /centros/madrid-serrano/ /oficinas-en-madrid/#serrano;
    /centros/madrid-serrano /oficinas-en-madrid/#serrano;
    /centros/madrid-velazquez/ /oficinas-en-madrid/#velazquez;
    /centros/madrid-velazquez /oficinas-en-madrid/#velazquez;
    /coworking-en-la-calle-serrano-tu-oficina-al-mejor-precio/ /oficinas-en-madrid/#serrano;
    /coworking-en-la-calle-serrano-tu-oficina-al-mejor-precio /oficinas-en-madrid/#serrano;
    /coworking-en-pozuelo-eficiencia-y-eficacia-a-tu-alcance/ /oficinas-en-madrid/#la-florida-pozuelo;
    /coworking-en-pozuelo-eficiencia-y-eficacia-a-tu-alcance /oficinas-en-madrid/#la-florida-pozuelo;
    /coworking-en-san-sebastian-de-los-reyes-calidad-y-buen-precio/ /oficinas-en-madrid/#sanse-san-sebastian-de-los-reyes;
    /coworking-en-san-sebastian-de-los-reyes-calidad-y-buen-precio /oficinas-en-madrid/#sanse-san-sebastian-de-los-reyes;
    /coworking-en-san-sebastian-de-los-reyes/ /oficinas-en-madrid/#sanse-san-sebastian-de-los-reyes;
    /coworking-en-san-sebastian-de-los-reyes /oficinas-en-madrid/#sanse-san-sebastian-de-los-reyes;
    /ofertas-despachos-sanse-1/ /oficinas-en-madrid/#sanse-san-sebastian-de-los-reyes;
    /ofertas-despachos-sanse-1 /oficinas-en-madrid/#sanse-san-sebastian-de-los-reyes;
    /coworking-space-en-las-tablas-tu-oficina-corporativa-mas-completa/ /oficinas-en-madrid/#las-tablas;
    /coworking-space-en-las-tablas-tu-oficina-corporativa-mas-completa /oficinas-en-madrid/#las-tablas;
    /tu-coworking-en-las-tablas/ /oficinas-en-madrid/#las-tablas;
    /tu-coworking-en-las-tablas /oficinas-en-madrid/#las-tablas;
    /porque-tener-tu-negocio-en-el-barrio-de-salamanca/ /oficinas-en-madrid/;
    /porque-tener-tu-negocio-en-el-barrio-de-salamanca /oficinas-en-madrid/;
    /oficinas-ya-llega-barcelona/ /oficinas-en-barcelona/;
    /oficinas-ya-llega-barcelona /oficinas-en-barcelona/;
    /oficinas-ya-llega-vigo/ /oficinas-en-vigo/;
    /oficinas-ya-llega-vigo /oficinas-en-vigo/;
    /oficinasya-llega-a-murcia/ /oficinas-en-murcia/;
    /oficinasya-llega-a-murcia /oficinas-en-murcia/;
    /salamanca-ciudad-de-talento-e-innovacion/ /oficinas-en-salamanca/;
    /salamanca-ciudad-de-talento-e-innovacion /oficinas-en-salamanca/;
    /alquiler-de-despachos-en-madrid-noviembre-oferta/ /oficinas-en-madrid/;
    /alquiler-de-despachos-en-madrid-noviembre-oferta /oficinas-en-madrid/;
    /alquiler-oficinas-despachos-madrid-julio-septiembre/ /oficinas-en-madrid/;
    /alquiler-oficinas-despachos-madrid-julio-septiembre /oficinas-en-madrid/;
    /alquiler-oficinas-despachos-madrid-noviembre/ /oficinas-en-madrid/;
    /alquiler-oficinas-despachos-madrid-noviembre /oficinas-en-madrid/;
    /alquiler-oficinas-despachos-madrid-noviembre-2/ /oficinas-en-madrid/;
    /alquiler-oficinas-despachos-madrid-noviembre-2 /oficinas-en-madrid/;
    /oferta-de-alquiler-de-despachos-en-madrid-junio-2019/ /oficinas-en-madrid/;
    /oferta-de-alquiler-de-despachos-en-madrid-junio-2019 /oficinas-en-madrid/;
    /7-dias-gratis-alquiler-oficinas-despachos-madrid-julio-septiembre/ /oficinas-en-madrid/;
    /7-dias-gratis-alquiler-oficinas-despachos-madrid-julio-septiembre /oficinas-en-madrid/;
    /oficina/castellon/ /oficinas-en-castellon/;
    /oficina/castellon /oficinas-en-castellon/;
    /oficina/madrid/ /oficinas-en-madrid/;
    /oficina/madrid /oficinas-en-madrid/;
    /oficina/murcia/ /oficinas-en-murcia/;
    /oficina/murcia /oficinas-en-murcia/;
    /oficina/sevilla/ /oficinas-en-sevilla/;
    /oficina/sevilla /oficinas-en-sevilla/;
    /oficinas/alicante/ /oficinas-en-alicante/;
    /oficinas/alicante /oficinas-en-alicante/;
    /oficinas/barcelona-alquiler-oficinas-despachos-barcelona/ /oficinas-en-barcelona/;
    /oficinas/barcelona-alquiler-oficinas-despachos-barcelona /oficinas-en-barcelona/;
    /oficinas/callao/ /oficinas-en-madrid/;
    /oficinas/callao /oficinas-en-madrid/;
    /oficinas/castellon/ /oficinas-en-castellon/;
    /oficinas/castellon /oficinas-en-castellon/;
    /oficinas/gasset/ /oficinas-en-madrid/#gasset;
    /oficinas/gasset /oficinas-en-madrid/#gasset;
    /oficinas/la-florida/ /oficinas-en-madrid/#la-florida-pozuelo;
    /oficinas/la-florida /oficinas-en-madrid/#la-florida-pozuelo;
    /oficinas/las-tablas/ /oficinas-en-madrid/#las-tablas;
    /oficinas/las-tablas /oficinas-en-madrid/#las-tablas;
    /oficinas/murcia-alquiler-de-despachos-y-oficinas-en-murcia/ /oficinas-en-murcia/;
    /oficinas/murcia-alquiler-de-despachos-y-oficinas-en-murcia /oficinas-en-murcia/;
    /oficinas/plaza-de-castilla-alquiler-de-despachos-y-oficinas-en-plaza-de-castilla/ /oficinas-en-madrid/#capitan-haya;
    /oficinas/plaza-de-castilla-alquiler-de-despachos-y-oficinas-en-plaza-de-castilla /oficinas-en-madrid/#capitan-haya;
    /oficinas/san-sebastian-de-los-reyes/ /oficinas-en-madrid/#sanse-san-sebastian-de-los-reyes;
    /oficinas/san-sebastian-de-los-reyes /oficinas-en-madrid/#sanse-san-sebastian-de-los-reyes;
    /oficinas/serrano/ /oficinas-en-madrid/#serrano;
    /oficinas/serrano /oficinas-en-madrid/#serrano;
    /oficinas/sevilla-alquiler-de-oficinas-y-despachos-en-sevilla/ /oficinas-en-sevilla/;
    /oficinas/sevilla-alquiler-de-oficinas-y-despachos-en-sevilla /oficinas-en-sevilla/;
    /oficinas/valencia-alquiler-de-despachos-y-oficinas-en-valencia/ /oficinas-en-valencia/;
    /oficinas/valencia-alquiler-de-despachos-y-oficinas-en-valencia /oficinas-en-valencia/;
    /oficinas/velazquez/ /oficinas-en-madrid/#velazquez;
    /oficinas/velazquez /oficinas-en-madrid/#velazquez;
    /oficinas/vigo-alquiler-oficinas-despachos-galicia/ /oficinas-en-vigo/;
    /oficinas/vigo-alquiler-oficinas-despachos-galicia /oficinas-en-vigo/;
    /portfolio_category/castellon/ /oficinas-en-castellon/;
    /portfolio_category/castellon /oficinas-en-castellon/;
    /portfolio_category/madrid/ /oficinas-en-madrid/;
    /portfolio_category/madrid /oficinas-en-madrid/;
    /alquilar-despacho-horas/ /alquiler-de-despachos/;
    /alquilar-despacho-horas /alquiler-de-despachos/;
    /ofertas-despachos/ /alquiler-de-despachos/;
    /ofertas-despachos /alquiler-de-despachos/;
    /7-dias-gratis/ /alquiler-de-despachos/;
    /7-dias-gratis /alquiler-de-despachos/;
    /oferta-oficina-virtual/ /oficina-virtual/;
    /oferta-oficina-virtual /oficina-virtual/;
    /domiciliacion-de-sociedades-desde-solo-1e-al-dia/ /oficina-virtual/;
    /domiciliacion-de-sociedades-desde-solo-1e-al-dia /oficina-virtual/;
    /cambiodesedesocial/ /oficina-virtual/;
    /cambiodesedesocial /oficina-virtual/;
    /oficinas-vistuales/ /oficina-virtual/;
    /oficinas-vistuales /oficina-virtual/;
    /smart-office-lo-que-quieres-como-quieres-cuando-quieres/ /oficina-virtual/#smart-office;
    /smart-office-lo-que-quieres-como-quieres-cuando-quieres /oficina-virtual/#smart-office;
    /quienes-somos/ /;
    /quienes-somos /;
    /contacto/ /#contact;
    /contacto /#contact;
    /concertar-visita/ /#contact;
    /concertar-visita /#contact;
    /gracias/ /;
    /gracias /;
    /politica-de-privacidad-2/ /politica-de-privacidad/;
    /politica-de-privacidad-2 /politica-de-privacidad/;
    /experiencia-en-coworking/politica-de-privacidad/ /politica-de-privacidad/;
    /experiencia-en-coworking/politica-de-privacidad /politica-de-privacidad/;
    /black-friday-2018/ /;
    /black-friday-2018 /;
    /black-friday-2018-2/ /;
    /black-friday-2018-2 /;
    /black-friday-2019-oficinas-ya/ /;
    /black-friday-2019-oficinas-ya /;
    /portfolio/ /;
    /portfolio /;
    /project/ /;
    /project /;
    /10-cosas-aprender-del-marketing-apple/ /blog/;
    /10-cosas-aprender-del-marketing-apple /blog/;
    /10-cosas-que-no-debes-decir-en-una-entrevista-de-trabajo/ /blog/;
    /10-cosas-que-no-debes-decir-en-una-entrevista-de-trabajo /blog/;
    /abogados-las-tablas-nos-cuenta-su-experiencia-en-un-coworking/ /blog/;
    /abogados-las-tablas-nos-cuenta-su-experiencia-en-un-coworking /blog/;
    /abre-tu-negocio-a-otros-paises-con-el-seo-multirregional/ /blog/;
    /abre-tu-negocio-a-otros-paises-con-el-seo-multirregional /blog/;
    /abrir-un-negocio-en-el-momento-actual-no-es-de-locos/ /blog/;
    /abrir-un-negocio-en-el-momento-actual-no-es-de-locos /blog/;
    /adios-a-telegram-motivos-de-su-cierre-y-aplicaciones-alternativas/ /blog/;
    /adios-a-telegram-motivos-de-su-cierre-y-aplicaciones-alternativas /blog/;
    /ahorrar-siendo-autonomo-es-posible/ /blog/;
    /ahorrar-siendo-autonomo-es-posible /blog/;
    /alcanza-todos-tus-objetivos-para-el-nuevo-ano/ /blog/;
    /alcanza-todos-tus-objetivos-para-el-nuevo-ano /blog/;
    /alfa-inmobiliaria-nos-cuenta-su-experiencia-en-un-coworking/ /blog/;
    /alfa-inmobiliaria-nos-cuenta-su-experiencia-en-un-coworking /blog/;
    /alternativas-a-las-reuniones-presenciales/ /blog/;
    /alternativas-a-las-reuniones-presenciales /blog/;
    /ambialia-nos-cuenta-su-experiencia-en-un-coworking/ /blog/;
    /ambialia-nos-cuenta-su-experiencia-en-un-coworking /blog/;
    /aprende-a-priorizar-de-forma-rapida-y-sencilla/ /blog/;
    /aprende-a-priorizar-de-forma-rapida-y-sencilla /blog/;
    /aprende-a-tener-iniciativa/ /blog/;
    /aprende-a-tener-iniciativa /blog/;
    /aprovecha-las-ventajas-de-la-ia-en-tu-negocio-con-estas-herramientas-gratuitas/ /blog/;
    /aprovecha-las-ventajas-de-la-ia-en-tu-negocio-con-estas-herramientas-gratuitas /blog/;
    /asi-funciona-el-tinder-para-empresas-nosotros-no-hacemos-nada-es-la-maquina-la-que-lo-hace/ /blog/;
    /asi-funciona-el-tinder-para-empresas-nosotros-no-hacemos-nada-es-la-maquina-la-que-lo-hace /blog/;
    /asi-pueden-los-influencers-dar-visibilidad-a-tu-negocio/ /blog/;
    /asi-pueden-los-influencers-dar-visibilidad-a-tu-negocio /blog/;
    /aumenta-la-motivacion-laboral-de-tu-equipo/ /blog/;
    /aumenta-la-motivacion-laboral-de-tu-equipo /blog/;
    /blog-corporativo-beneficios-reglas-basicas/ /blog/;
    /blog-corporativo-beneficios-reglas-basicas /blog/;
    /brainstorming-ideas-para-dar-un-giro-a-tu-negocio/ /blog/;
    /brainstorming-ideas-para-dar-un-giro-a-tu-negocio /blog/;
    /buscas-planes-para-estas-fiestas-aqui-los-tienes/ /blog/;
    /buscas-planes-para-estas-fiestas-aqui-los-tienes /blog/;
    /buuuuuh-los-mejores-planes-para-la-noche-de-halloween/ /blog/;
    /buuuuuh-los-mejores-planes-para-la-noche-de-halloween /blog/;
    /carsharing-o-coche-privado/ /blog/;
    /carsharing-o-coche-privado /blog/;
    /claves-de-la-nueva-norma-de-registro-de-la-jornada-laboral/ /blog/;
    /claves-de-la-nueva-norma-de-registro-de-la-jornada-laboral /blog/;
    /claves-para-mantener-la-lealtad-de-tus-clientes/ /blog/;
    /claves-para-mantener-la-lealtad-de-tus-clientes /blog/;
    /claves-para-posicionar-tu-negocio-en-google/ /blog/;
    /claves-para-posicionar-tu-negocio-en-google /blog/;
    /claves-para-que-tu-email-marketing-sea-efectivo/ /blog/;
    /claves-para-que-tu-email-marketing-sea-efectivo /blog/;
    /club-privado-carsharing-oficinas-ya-callao/ /blog/;
    /club-privado-carsharing-oficinas-ya-callao /blog/;
    /como-aplicar-la-subida-del-smi-para-autonomos-y-empresas/ /blog/;
    /como-aplicar-la-subida-del-smi-para-autonomos-y-empresas /blog/;
    /como-aprender-a-tener-paciencia/ /blog/;
    /como-aprender-a-tener-paciencia /blog/;
    /como-aumentar-la-motivacion-de-tu-equipo-de-trabajo/ /blog/;
    /como-aumentar-la-motivacion-de-tu-equipo-de-trabajo /blog/;
    /como-aumentar-tus-ventas-parte-1/ /blog/;
    /como-aumentar-tus-ventas-parte-1 /blog/;
    /como-aumentar-tus-ventas-parte-2/ /blog/;
    /como-aumentar-tus-ventas-parte-2 /blog/;
    /como-compartir-tu-dni-por-internet-sin-riesgos-2-2/ /blog/;
    /como-compartir-tu-dni-por-internet-sin-riesgos-2-2 /blog/;
    /como-contribuyen-los-coworkings-al-ahorro-energetico/ /blog/;
    /como-contribuyen-los-coworkings-al-ahorro-energetico /blog/;
    /como-crear-un-buen-entorno-laboral/ /blog/;
    /como-crear-un-buen-entorno-laboral /blog/;
    /como-darle-valor-de-lujo-a-tu-producto/ /blog/;
    /como-darle-valor-de-lujo-a-tu-producto /blog/;
    /como-elijo-el-coworking-mas-apropiado-para-mi-negocio/ /blog/;
    /como-elijo-el-coworking-mas-apropiado-para-mi-negocio /blog/;
    /como-evitar-los-conflictos-laborales/ /blog/;
    /como-evitar-los-conflictos-laborales /blog/;
    /como-evitar-que-roben-tus-datos-al-pagar-con-el-movil/ /blog/;
    /como-evitar-que-roben-tus-datos-al-pagar-con-el-movil /blog/;
    /como-funciona-un-coworking/ /blog/;
    /como-funciona-un-coworking /blog/;
    /como-google-puede-ayudar-a-tu-negocio-sin-coste-para-ti/ /blog/;
    /como-google-puede-ayudar-a-tu-negocio-sin-coste-para-ti /blog/;
    /como-hacer-que-tu-equipo-de-trabajo-este-siempre-motivado/ /blog/;
    /como-hacer-que-tu-equipo-de-trabajo-este-siempre-motivado /blog/;
    /como-hacer-que-tu-pequeno-negocio-parezca-una-gran-empresa-caso-practico/ /blog/;
    /como-hacer-que-tu-pequeno-negocio-parezca-una-gran-empresa-caso-practico /blog/;
    /como-mejorar-tu-economia/ /blog/;
    /como-mejorar-tu-economia /blog/;
    /como-reducir-gastos-de-oficina-sin-perder-calidad-oficina-tradicional-vs-coworking/ /blog/;
    /como-reducir-gastos-de-oficina-sin-perder-calidad-oficina-tradicional-vs-coworking /blog/;
    /como-responder-a-las-objeciones-mas-comunes-de-los-clientes/ /blog/;
    /como-responder-a-las-objeciones-mas-comunes-de-los-clientes /blog/;
    /como-sacar-partido-al-tiempo/ /blog/;
    /como-sacar-partido-al-tiempo /blog/;
    /como-sacarle-partido-a-linkedin/ /blog/;
    /como-sacarle-partido-a-linkedin /blog/;
    /como-superar-el-miedo-a-hablar-en-publico/ /blog/;
    /como-superar-el-miedo-a-hablar-en-publico /blog/;
    /como-tener-exito-en-el-trabajo/ /blog/;
    /como-tener-exito-en-el-trabajo /blog/;
    /como-un-coworking-hace-crecer-tu-negocio-caso-real/ /blog/;
    /como-un-coworking-hace-crecer-tu-negocio-caso-real /blog/;
    /conciliacion-la-gran-odisea-del-autonomo/ /blog/;
    /conciliacion-la-gran-odisea-del-autonomo /blog/;
    /conectar-mejor-con-tus-clientes-mediante-un-buen-relato/ /blog/;
    /conectar-mejor-con-tus-clientes-mediante-un-buen-relato /blog/;
    /conoceis-google-activate/ /blog/;
    /conoceis-google-activate /blog/;
    /conseguir-clientes-nuevos-y-retener-a-los-actuales-durante-el-covid19-es-posible/ /blog/;
    /conseguir-clientes-nuevos-y-retener-a-los-actuales-durante-el-covid19-es-posible /blog/;
    /consejos-para-combatir-las-olas-de-calor-en-verano/ /blog/;
    /consejos-para-combatir-las-olas-de-calor-en-verano /blog/;
    /consejos-para-ser-un-buen-lider/ /blog/;
    /consejos-para-ser-un-buen-lider /blog/;
    /cosas-deberias-saber-abrir-negocio/ /blog/;
    /cosas-deberias-saber-abrir-negocio /blog/;
    /coworking-como-solucion-al-estres/ /blog/;
    /coworking-como-solucion-al-estres /blog/;
    /coworking-para-abogados-privacidad-y-profesionalidad/ /blog/;
    /coworking-para-abogados-privacidad-y-profesionalidad /blog/;
    /coworking-y-networking-conceptos-clave-para-todo-emprendedor/ /blog/;
    /coworking-y-networking-conceptos-clave-para-todo-emprendedor /blog/;
    /coworking-y-networking-contactos-laborales-de-calidad/ /blog/;
    /coworking-y-networking-contactos-laborales-de-calidad /blog/;
    /coworkings-espacios-de-trabajo-que-unen-vida-social-y-laboral/ /blog/;
    /coworkings-espacios-de-trabajo-que-unen-vida-social-y-laboral /blog/;
    /creditos-ico-paso-a-paso/ /blog/;
    /creditos-ico-paso-a-paso /blog/;
    /de-la-oficina-tradicional-al-coworking/ /blog/;
    /de-la-oficina-tradicional-al-coworking /blog/;
    /descubre-estos-trucos-para-disparar-tu-productividad/ /blog/;
    /descubre-estos-trucos-para-disparar-tu-productividad /blog/;
    /destacar-curriculum-la-competencia/ /blog/;
    /destacar-curriculum-la-competencia /blog/;
    /diez-tips-para-una-oratoria-insuperable/ /blog/;
    /diez-tips-para-una-oratoria-insuperable /blog/;
    /diferencias-entre-coworking-oficina-compartida-y-centro-de-negocios-con-coworking/ /blog/;
    /diferencias-entre-coworking-oficina-compartida-y-centro-de-negocios-con-coworking /blog/;
    /digital-logic-system-nos-cuenta-su-experiencia-en-un-coworking/ /blog/;
    /digital-logic-system-nos-cuenta-su-experiencia-en-un-coworking /blog/;
    /digitalizacion-analisis-y-estrategia/ /blog/;
    /digitalizacion-analisis-y-estrategia /blog/;
    /el-coworking-se-impone-en-el-sector-de-las-oficinas/ /blog/;
    /el-coworking-se-impone-en-el-sector-de-las-oficinas /blog/;
    /el-coworking-se-transforma-en-oficina-de-contingencia/ /blog/;
    /el-coworking-se-transforma-en-oficina-de-contingencia /blog/;
    /el-coworking-y-la-mujer-emprendedora/ /blog/;
    /el-coworking-y-la-mujer-emprendedora /blog/;
    /el-creador-de-chatgpt-revela-sus-consejos-para-emprendedores/ /blog/;
    /el-creador-de-chatgpt-revela-sus-consejos-para-emprendedores /blog/;
    /el-enriquecimiento-personal-y-laboral-las-nuevas-prioridades/ /blog/;
    /el-enriquecimiento-personal-y-laboral-las-nuevas-prioridades /blog/;
    /el-gobierno-actualiza-el-calendario-de-ayudas-para-autonomos/ /blog/;
    /el-gobierno-actualiza-el-calendario-de-ayudas-para-autonomos /blog/;
    /el-gobierno-anuncia-el-nuevo-kit-consulting-para-pymes/ /blog/;
    /el-gobierno-anuncia-el-nuevo-kit-consulting-para-pymes /blog/;
    /el-nuevo-coworking-post-covid/ /blog/;
    /el-nuevo-coworking-post-covid /blog/;
    /el-optimismo-concepto-clave-para-el-mundo-laboral/ /blog/;
    /el-optimismo-concepto-clave-para-el-mundo-laboral /blog/;
    /el-precio-de-la-gasolina-y-el-diesel-se-ha-disparado-en-2024-y-estas-son-las-razones/ /blog/;
    /el-precio-de-la-gasolina-y-el-diesel-se-ha-disparado-en-2024-y-estas-son-las-razones /blog/;
    /el-teletrabajo-ha-llegado-a-su-fin/ /blog/;
    /el-teletrabajo-ha-llegado-a-su-fin /blog/;
    /el-teletrabajo-reduce-la-productividad-laboral/ /blog/;
    /el-teletrabajo-reduce-la-productividad-laboral /blog/;
    /el-trabajo-100-remoto-no-arraiga-en-espana/ /blog/;
    /el-trabajo-100-remoto-no-arraiga-en-espana /blog/;
    /eleva-tu-economia-de-nivel-con-estos-consejos/ /blog/;
    /eleva-tu-economia-de-nivel-con-estos-consejos /blog/;
    /elige-coworking-y-gana-la-partida/ /blog/;
    /elige-coworking-y-gana-la-partida /blog/;
    /emprendedor-aumenta-tus-probabilidades-de-exito/ /blog/;
    /emprendedor-aumenta-tus-probabilidades-de-exito /blog/;
    /emprender-con-exito-2021/ /blog/;
    /emprender-con-exito-2021 /blog/;
    /emprender-con-exito/ /blog/;
    /emprender-con-exito /blog/;
    /en-oficinas-ya-no-todo-es-trabajar/ /blog/;
    /en-oficinas-ya-no-todo-es-trabajar /blog/;
    /enfrentarse-una-negociacion-salir-victorioso/ /blog/;
    /enfrentarse-una-negociacion-salir-victorioso /blog/;
    /eres-feliz-en-tu-trabajo/ /blog/;
    /eres-feliz-en-tu-trabajo /blog/;
    /es-el-verano-un-buen-momento-para-emprender/ /blog/;
    /es-el-verano-un-buen-momento-para-emprender /blog/;
    /esta-tu-empresa-preparada-para-afrontar-el-coronavirus/ /blog/;
    /esta-tu-empresa-preparada-para-afrontar-el-coronavirus /blog/;
    /estas-son-las-cadenas-de-gasolineras-mas-baratas-segun-la-ocu/ /blog/;
    /estas-son-las-cadenas-de-gasolineras-mas-baratas-segun-la-ocu /blog/;
    /estas-son-las-mejores-apps-para-aprovechar-el-certificado-digital-en-tu-movil/ /blog/;
    /estas-son-las-mejores-apps-para-aprovechar-el-certificado-digital-en-tu-movil /blog/;
    /estas-son-las-novedades-en-el-impuesto-de-sociedades-de-2024/ /blog/;
    /estas-son-las-novedades-en-el-impuesto-de-sociedades-de-2024 /blog/;
    /estos-son-los-nuevos-tramos-para-pagar-la-cuota-minima-de-autonomos-en-2024/ /blog/;
    /estos-son-los-nuevos-tramos-para-pagar-la-cuota-minima-de-autonomos-en-2024 /blog/;
    /estres-laboral-por-el-covid-deshazte-de-el/ /blog/;
    /estres-laboral-por-el-covid-deshazte-de-el /blog/;
    /eventos-que-no-te-puedes-perder-siendo-emprendedor/ /blog/;
    /eventos-que-no-te-puedes-perder-siendo-emprendedor /blog/;
    /experiencia-en-coworking/ /blog/;
    /experiencia-en-coworking /blog/;
    /fgr-asesoria-energetica-nos-cuenta-su-experiencia-en-un-coworking/ /blog/;
    /fgr-asesoria-energetica-nos-cuenta-su-experiencia-en-un-coworking /blog/;
    /franquicias-ventajas-y-desventajas/ /blog/;
    /franquicias-ventajas-y-desventajas /blog/;
    /freshrules-nos-cuenta-su-experiencia-en-un-coworking/ /blog/;
    /freshrules-nos-cuenta-su-experiencia-en-un-coworking /blog/;
    /gabinete-de-psicologia-sian-nos-cuenta-su-experiencia-en-un-coworking/ /blog/;
    /gabinete-de-psicologia-sian-nos-cuenta-su-experiencia-en-un-coworking /blog/;
    /gana-velocidad-en-tu-ordenador/ /blog/;
    /gana-velocidad-en-tu-ordenador /blog/;
    /genera-ideas-de-negocio-con-este-truco/ /blog/;
    /genera-ideas-de-negocio-con-este-truco /blog/;
    /google-tendra-un-nuevo-servicio-gratuito-ya-no-habra-que-pagar-por-su-vpn/ /blog/;
    /google-tendra-un-nuevo-servicio-gratuito-ya-no-habra-que-pagar-por-su-vpn /blog/;
    /guia-para-irte-de-vacaciones-en-una-camper-este-verano/ /blog/;
    /guia-para-irte-de-vacaciones-en-una-camper-este-verano /blog/;
    /habitos-comunes-de-las-personas-super-productivas/ /blog/;
    /habitos-comunes-de-las-personas-super-productivas /blog/;
    /hacienda-simplifica-las-rectificaciones-en-las-declaraciones-de-los-autonomos/ /blog/;
    /hacienda-simplifica-las-rectificaciones-en-las-declaraciones-de-los-autonomos /blog/;
    /hay-menos-oficinas-vacias-en-alquiler-en-el-centro-de-madrid-que-en-londres/ /blog/;
    /hay-menos-oficinas-vacias-en-alquiler-en-el-centro-de-madrid-que-en-londres /blog/;
    /herramientas-para-trabajar-desde-casa/ /blog/;
    /herramientas-para-trabajar-desde-casa /blog/;
    /hola-conoces-a-luzia/ /blog/;
    /hola-conoces-a-luzia /blog/;
    /hr-consultores-nos-cuenta-su-experiencia-en-un-coworking/ /blog/;
    /hr-consultores-nos-cuenta-su-experiencia-en-un-coworking /blog/;
    /inteligencia-artificial-en-pymes-innovacion-y-competitividad-en-el-mercado/ /blog/;
    /inteligencia-artificial-en-pymes-innovacion-y-competitividad-en-el-mercado /blog/;
    /la-estafa-que-te-hara-leer-tu-correo-con-mucha-atencion/ /blog/;
    /la-estafa-que-te-hara-leer-tu-correo-con-mucha-atencion /blog/;
    /la-importancia-de-escuchar-a-tus-clientes/ /blog/;
    /la-importancia-de-escuchar-a-tus-clientes /blog/;
    /la-loteria-de-navidad-la-veis-hacienda-y-tu/ /blog/;
    /la-loteria-de-navidad-la-veis-hacienda-y-tu /blog/;
    /la-oficina-flexible-la-forma-de-trabajo-mas-demandada/ /blog/;
    /la-oficina-flexible-la-forma-de-trabajo-mas-demandada /blog/;
    /la-oficina-flexible-la-solucion-favorita-de-startups-pymes-y-emprendedores/ /blog/;
    /la-oficina-flexible-la-solucion-favorita-de-startups-pymes-y-emprendedores /blog/;
    /la-semana-laboral-de-4-dias-al-estilo-aleman/ /blog/;
    /la-semana-laboral-de-4-dias-al-estilo-aleman /blog/;
    /las-5-mejores-tecnicas-para-cerrar-una-venta/ /blog/;
    /las-5-mejores-tecnicas-para-cerrar-una-venta /blog/;
    /las-oficinas-sostenibles-que-te-ayudan-a-crecer-y-reducen-tus-gastos/ /blog/;
    /las-oficinas-sostenibles-que-te-ayudan-a-crecer-y-reducen-tus-gastos /blog/;
    /lecciones-aprendidas-con-la-crisis-del-covid19/ /blog/;
    /lecciones-aprendidas-con-la-crisis-del-covid19 /blog/;
    /llega-el-1o-concurso-de-fotografia-navidena-de-oficinas-ya/ /blog/;
    /llega-el-1o-concurso-de-fotografia-navidena-de-oficinas-ya /blog/;
    /llega-la-cabalgata-de-reyes-a-madrid-fechas-horarios-y-recorridos/ /blog/;
    /llega-la-cabalgata-de-reyes-a-madrid-fechas-horarios-y-recorridos /blog/;
    /los-12-pasos-de-una-presentacion-perfecta/ /blog/;
    /los-12-pasos-de-una-presentacion-perfecta /blog/;
    /los-3-problemas-mas-comunes-de-un-emprendedor-y-sus-soluciones/ /blog/;
    /los-3-problemas-mas-comunes-de-un-emprendedor-y-sus-soluciones /blog/;
    /los-6-mejores-programas-erp-de-software-libre-o-no/ /blog/;
    /los-6-mejores-programas-erp-de-software-libre-o-no /blog/;
    /los-autonomos-ya-pueden-consultar-sus-datos-en-hacienda-para-la-renta/ /blog/;
    /los-autonomos-ya-pueden-consultar-sus-datos-en-hacienda-para-la-renta /blog/;
    /los-coworkings-de-oficinas-ya-continuan-operativos-pese-a-la-gran-nevada/ /blog/;
    /los-coworkings-de-oficinas-ya-continuan-operativos-pese-a-la-gran-nevada /blog/;
    /los-coworkings-mantienen-activo-tu-negocio-durante-tus-vacaciones/ /blog/;
    /los-coworkings-mantienen-activo-tu-negocio-durante-tus-vacaciones /blog/;
    /los-destinos-turisticos-con-mas-sol-del-mundo/ /blog/;
    /los-destinos-turisticos-con-mas-sol-del-mundo /blog/;
    /los-mejores-descuentos-encontraras-este-black-friday/ /blog/;
    /los-mejores-descuentos-encontraras-este-black-friday /blog/;
    /marca-personal-todo-lo-que-necesitas-saber/ /blog/;
    /marca-personal-todo-lo-que-necesitas-saber /blog/;
    /mas-del-65-de-abogados-tiene-una-oficina-virtual/ /blog/;
    /mas-del-65-de-abogados-tiene-una-oficina-virtual /blog/;
    /mas-productivo-trabajo/ /blog/;
    /mas-productivo-trabajo /blog/;
    /mergetix-nos-cuenta-su-experiencia-en-un-coworking/ /blog/;
    /mergetix-nos-cuenta-su-experiencia-en-un-coworking /blog/;
    /mi-dia-en-un-coworking/ /blog/;
    /mi-dia-en-un-coworking /blog/;
    /montar-un-negocio/ /blog/;
    /montar-un-negocio /blog/;
    /motivos-por-los-que-los-autonomos-pueden-perder-la-tarifa-plana-en-2024/ /blog/;
    /motivos-por-los-que-los-autonomos-pueden-perder-la-tarifa-plana-en-2024 /blog/;
    /multas-de-hasta-10-000-euros-a-los-autonomos-que-no-reduzcan-la-jornada-a-385-horas/ /blog/;
    /multas-de-hasta-10-000-euros-a-los-autonomos-que-no-reduzcan-la-jornada-a-385-horas /blog/;
    /negocio-online-claves-negocio-sea-exito/ /blog/;
    /negocio-online-claves-negocio-sea-exito /blog/;
    /networking-como-ser-el-crack-de-los-contactos/ /blog/;
    /networking-como-ser-el-crack-de-los-contactos /blog/;
    /neuromarketing-estrategias-y-claves/ /blog/;
    /neuromarketing-estrategias-y-claves /blog/;
    /no-dejes-pasar-estos-gastos-desgravables-en-la-renta-2023-2024/ /blog/;
    /no-dejes-pasar-estos-gastos-desgravables-en-la-renta-2023-2024 /blog/;
    /oficina-barata-en-madrid-si-existe/ /blog/;
    /oficina-barata-en-madrid-si-existe /blog/;
    /oficina-virtual-la-solucion-negocio/ /blog/;
    /oficina-virtual-la-solucion-negocio /blog/;
    /oficina-vs-teletrabajo-and-the-real-winner-is/ /blog/;
    /oficina-vs-teletrabajo-and-the-real-winner-is /blog/;
    /oficinas-con-corazon-clave-en-el-enriquecimiento-personal-y-laboral/ /blog/;
    /oficinas-con-corazon-clave-en-el-enriquecimiento-personal-y-laboral /blog/;
    /oficinas-nuevos-cambios-se-avecinan/ /blog/;
    /oficinas-nuevos-cambios-se-avecinan /blog/;
    /oficinas-para-la-contencion-del-coronavirus/ /blog/;
    /oficinas-para-la-contencion-del-coronavirus /blog/;
    /oficinas-post-covid-nuevas-necesidades-de-los-trabajadores/ /blog/;
    /oficinas-post-covid-nuevas-necesidades-de-los-trabajadores /blog/;
    /oficinas-ya-abrira-un-nuevo-coworking-en-el-amazonas/ /blog/;
    /oficinas-ya-abrira-un-nuevo-coworking-en-el-amazonas /blog/;
    /oficinas-ya-el-coworking-seguro-frente-al-covid-19/ /blog/;
    /oficinas-ya-el-coworking-seguro-frente-al-covid-19 /blog/;
    /oficinas-ya-inaugura-su-nuevo-centro-sensorial/ /blog/;
    /oficinas-ya-inaugura-su-nuevo-centro-sensorial /blog/;
    /pinta-vida-naranja/ /blog/;
    /pinta-vida-naranja /blog/;
    /ponte-tu-mascara-ha-llegado-el-carnaval/ /blog/;
    /ponte-tu-mascara-ha-llegado-el-carnaval /blog/;
    /por-que-algunas-personas-trabajan-mejor-desde-casa-que-otras/ /blog/;
    /por-que-algunas-personas-trabajan-mejor-desde-casa-que-otras /blog/;
    /por-que-el-trabajo-a-distancia-es-el-preferido-de-los-millennials-y-nomadas-digitales/ /blog/;
    /por-que-el-trabajo-a-distancia-es-el-preferido-de-los-millennials-y-nomadas-digitales /blog/;
    /potencia-ya-el-valor-de-tu-marca-y-llevalo-al-siguiente-nivel/ /blog/;
    /potencia-ya-el-valor-de-tu-marca-y-llevalo-al-siguiente-nivel /blog/;
    /preguntas-mas-comunes-entrevista-trabajo/ /blog/;
    /preguntas-mas-comunes-entrevista-trabajo /blog/;
    /preguntas-trampa-mas-comunes-en-una-entrevista/ /blog/;
    /preguntas-trampa-mas-comunes-en-una-entrevista /blog/;
    /preparate-para-la-convergencia-real-tu-smartphone-pronto-sera-tu-pc/ /blog/;
    /preparate-para-la-convergencia-real-tu-smartphone-pronto-sera-tu-pc /blog/;
    /puedes-circular-con-tu-vehiculo-en-las-zbe/ /blog/;
    /puedes-circular-con-tu-vehiculo-en-las-zbe /blog/;
    /que-cualidades-debe-tener-el-cofundador-ideal/ /blog/;
    /que-cualidades-debe-tener-el-cofundador-ideal /blog/;
    /que-es-una-oficina-virtual/ /blog/;
    /que-es-una-oficina-virtual /blog/;
    /que-gastos-puedes-deducirte-en-la-renta-si-eres-trabajador-por-cuenta-ajena/ /blog/;
    /que-gastos-puedes-deducirte-en-la-renta-si-eres-trabajador-por-cuenta-ajena /blog/;
    /que-requisitos-debe-cumplir-un-coworking-en-tiempos-de-covid/ /blog/;
    /que-requisitos-debe-cumplir-un-coworking-en-tiempos-de-covid /blog/;
    /que-va-a-preocupar-a-las-pyme-en-2024/ /blog/;
    /que-va-a-preocupar-a-las-pyme-en-2024 /blog/;
    /rastreadores-privados-en-los-coworkings-de-oficinas-ya/ /blog/;
    /rastreadores-privados-en-los-coworkings-de-oficinas-ya /blog/;
    /redes-sociales-de-empresa-obten-el-maximo-rendimiento/ /blog/;
    /redes-sociales-de-empresa-obten-el-maximo-rendimiento /blog/;
    /renfe-endurece-las-condiciones-para-devolver-dinero-por-retrasos/ /blog/;
    /renfe-endurece-las-condiciones-para-devolver-dinero-por-retrasos /blog/;
    /sabes-mantener-la-calma/ /blog/;
    /sabes-mantener-la-calma /blog/;
    /sabes-si-tu-compania-esta-a-la-ultima-en-medios-tecnologicos/ /blog/;
    /sabes-si-tu-compania-esta-a-la-ultima-en-medios-tecnologicos /blog/;
    /seguridad-social-pide-datos-a-los-autonomos-para-notificarles-sus-futuras-cuotas/ /blog/;
    /seguridad-social-pide-datos-a-los-autonomos-para-notificarles-sus-futuras-cuotas /blog/;
    /si-operas-en-wallapop-o-en-airbnb-hacienda-quiere-hablar-contigo/ /blog/;
    /si-operas-en-wallapop-o-en-airbnb-hacienda-quiere-hablar-contigo /blog/;
    /si-teletrabajas-haz-clic-aqui/ /blog/;
    /si-teletrabajas-haz-clic-aqui /blog/;
    /si-usas-bizum-tienes-que-declararte-ante-hacienda/ /blog/;
    /si-usas-bizum-tienes-que-declararte-ante-hacienda /blog/;
    /silbana-nos-cuenta-su-experiencia-en-un-coworking/ /blog/;
    /silbana-nos-cuenta-su-experiencia-en-un-coworking /blog/;
    /storytellin-iii-los/ /blog/;
    /storytellin-iii-los /blog/;
    /storytelling-ii-vender-con-cuentos/ /blog/;
    /storytelling-ii-vender-con-cuentos /blog/;
    /storytelling-vende-con-una-buena-historia/ /blog/;
    /storytelling-vende-con-una-buena-historia /blog/;
    /te-traemos-las-startups-mas-innovadoras-del-mundo/ /blog/;
    /te-traemos-las-startups-mas-innovadoras-del-mundo /blog/;
    /teletrabajo-sin-complicaciones/ /blog/;
    /teletrabajo-sin-complicaciones /blog/;
    /tesoros-que-podrias-tener-olvidados-en-el-trasero/ /blog/;
    /tesoros-que-podrias-tener-olvidados-en-el-trasero /blog/;
    /tienes-dudas-sobre-la-factura-electronica-sigue-leyendo/ /blog/;
    /tienes-dudas-sobre-la-factura-electronica-sigue-leyendo /blog/;
    /tips-para-triunfar-en-el-networking/ /blog/;
    /tips-para-triunfar-en-el-networking /blog/;
    /todo-lo-que-necesitas-para-convertirte-en-un-experto-en-ia/ /blog/;
    /todo-lo-que-necesitas-para-convertirte-en-un-experto-en-ia /blog/;
    /todo-lo-que-necesitas-saber-sobre-la-nueva-ley-de-teletrabajo/ /blog/;
    /todo-lo-que-necesitas-saber-sobre-la-nueva-ley-de-teletrabajo /blog/;
    /todo-lo-que-requieres-saber-sobre-el-pago-con-criptomonedas/ /blog/;
    /todo-lo-que-requieres-saber-sobre-el-pago-con-criptomonedas /blog/;
    /toni-bassols-nos-cuenta-su-experiencia-en-un-coworking/ /blog/;
    /toni-bassols-nos-cuenta-su-experiencia-en-un-coworking /blog/;
    /traslado-masivo-de-pequenas-y-medianas-empresas-a-business-centers/ /blog/;
    /traslado-masivo-de-pequenas-y-medianas-empresas-a-business-centers /blog/;
    /traslot-102-nos-cuenta-su-experiencia-en-un-coworking/ /blog/;
    /traslot-102-nos-cuenta-su-experiencia-en-un-coworking /blog/;
    /trucos-para-vencer-el-sueno-en-el-trabajo/ /blog/;
    /trucos-para-vencer-el-sueno-en-el-trabajo /blog/;
    /tu-compania-esta-a-la-ultima-en-medios-tecnologicos/ /blog/;
    /tu-compania-esta-a-la-ultima-en-medios-tecnologicos /blog/;
    /ultima-oportunidad-para-ajustar-la-cuota-de-autonomos/ /blog/;
    /ultima-oportunidad-para-ajustar-la-cuota-de-autonomos /blog/;
    /un-metodo-poco-conocido-por-los-autonomos-les-permite-hacer-la-renta-de-forma-casi-automatica/ /blog/;
    /un-metodo-poco-conocido-por-los-autonomos-les-permite-hacer-la-renta-de-forma-casi-automatica /blog/;
    /ventajas-de-los-business-centers-frente-a-las-oficinas-tradicionales/ /blog/;
    /ventajas-de-los-business-centers-frente-a-las-oficinas-tradicionales /blog/;
    /ventajas-del-networking/ /blog/;
    /ventajas-del-networking /blog/;
    /waze-o-google-maps-que-navegador-es-mas-completo/ /blog/;
    /waze-o-google-maps-que-navegador-es-mas-completo /blog/;
    /y-si-te-dijesen-que-nunca-va-a-haber-vacuna-para-el-covid/ /blog/;
    /y-si-te-dijesen-que-nunca-va-a-haber-vacuna-para-el-covid /blog/;
    /ya-es-oficial-hacienda-obligara-a-hacer-la-proxima-declaracion-de-la-renta-solo-por-internet/ /blog/;
    /ya-es-oficial-hacienda-obligara-a-hacer-la-proxima-declaracion-de-la-renta-solo-por-internet /blog/;
    ~^/category/ /blog/;
    ~^/tag/ /blog/;
    ~^/author/ /blog/;
    ~^/actividades/ /comunidad/;
    ~^/miembros/ /comunidad/;
    ~^/2017/ /blog/;
    ~^/2018/ /blog/;
    ~^/2019/ /blog/;
    ~^/2020/ /blog/;
    ~^/2021/ /blog/;
    ~^/blog/page/ /blog/;
    ~^/web/ /blog/;
    ~^/centros/madrid\-callao/page/ /oficinas-en-madrid/;
    ~^/centros/madrid\-capitan\-haya/page/ /oficinas-en-madrid/#capitan-haya;
    ~^/centros/madrid\-ortega\-y\-gasset/page/ /oficinas-en-madrid/#gasset;
    ~^/centros/madrid\-pozuelo/page/ /oficinas-en-madrid/#la-florida-pozuelo;
    ~^/centros/madrid\-san\-sebastian\-de\-los\-reyes/page/ /oficinas-en-madrid/#sanse-san-sebastian-de-los-reyes;
    ~^/centros/madrid\-serrano/page/ /oficinas-en-madrid/#serrano;
    ~^/centros/madrid\-velazquez/page/ /oficinas-en-madrid/#velazquez;
    ~^/centros/ /ubicaciones/;
    ~^/oficinas/ /ubicaciones/;
    ~^/oficina/ /ubicaciones/;
    ~^/portfolio_category/ /ubicaciones/;
}

# ---- B) Un server propio para el dominio sin www.
server {
    listen 80;
    listen 443 ssl;
    server_name oficinasya.es;
    # (los ssl_certificate del hosting)
    return 301 https://www.oficinasya.es$request_uri;
}

# ---- C) Dentro del server { } de www.oficinasya.es, antes de cualquier otro location.
location ~ ^/_ { return 404; }
location ^~ /OLD/ { return 404; }   # nucleo del WordPress anterior; /oficinavirtual/ no se toca
location ~ /\.(?!well-known/) { return 404; }
location ~ (^|/)(requirements\.txt|datos\-centros\.csv|README\.md)$ { return 404; }
location ~ \.(py|pyc|md|ya?ml|csv|manifest)$ { return 404; }
if ($oya_redirect) { return 301 https://www.oficinasya.es$oya_redirect; }
```
