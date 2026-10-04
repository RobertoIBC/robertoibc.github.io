# ⚠️ ANTES DE NADA: COPIA DE SEGURIDAD DE `/www`. EN EL SERVIDOR HAY FICHEROS QUE NO ESTÁN EN ESTE REPOSITORIO (`enviar.php`, `enviar.config.php`, `.htaccess`, `.php.ini`, LA VERIFICACIÓN DE GOOGLE Y LA TIENDA DE `/oficinavirtual/`). SI SE PIERDEN, NO HAY OTRA COPIA.

# Subir la web a www.oficinasya.es, paso a paso

Para seguirlo en orden desde el panel web del hosting (gestor de archivos), sin saltarse nada. Cada paso dice qué hacer y qué tienes que ver.
La configuración del servidor (el bloque para `.htaccess` y la versión nginx) está en [CONFIGURACION-SERVIDOR.md](CONFIGURACION-SERVIDOR.md).

## Lo que hay hoy en el servidor

La web se sirve desde **`/www`**, no desde la raíz de la cuenta. Dentro de `/www` hay, además de la web actual:

| Qué | Qué es | Qué se hace |
|---|---|---|
| `enviar.php`, `enviar.config.php` | El formulario de contacto y su configuración (del técnico) | **NO SE TOCA** |
| `.htaccess` (9,4 kB) | Reglas del técnico | Se edita en el paso 6: se añade nuestro bloque **al principio** |
| `.php.ini` | Configuración de PHP | **NO SE TOCA** |
| `googlebe6fd46c002206cc.html` | Verificación de Search Console | **NO SE TOCA** (si se borra, se pierde la propiedad) |
| `oficinavirtual/` | Otra web en marcha: WordPress con WooCommerce («Oficina Virtual de Oficinas YA!») | **NO SE TOCA** |
| `OLD/` | Núcleo del WordPress anterior, con su `wp-config.php` (credenciales) | **NO SE BORRA** (lo decide el técnico). El `.htaccess` nuevo lo bloquea al público |
| `newsite/`, `cache/`, `.tmb/`, `.well-known/` | Carpetas del hosting y del panel | **NO SE TOCAN** |
| `_data/`, `_content/`, `_templates/`, `_tools/`, `_docs/`, `_build.py`, `_build.manifest`, `README.md`, `requirements.txt` | Fuentes del prototipo, subidas por error y **hoy visibles para cualquiera** | **SE BORRAN** en el paso 7 |

---

## 1. COPIA DE SEGURIDAD DE `/www`, ANTES DE SUBIR, SOBRESCRIBIR O BORRAR NADA

**Es el único paso que no tiene vuelta atrás si te lo saltas.** Todo lo demás se deshace subiendo esta copia.

1. En el gestor de archivos, activa **«mostrar ficheros ocultos»** antes de nada: `.htaccess` y `.php.ini` empiezan por punto y, sin esa opción, ni se ven ni se copian.
2. Comprime la carpeta **`/www` entera** con la opción «Comprimir» del panel y **descarga el .zip** a tu ordenador. Llámalo `copia-www-AAAA-MM-DD.zip`.
   Si el panel no deja comprimir algo tan grande (la tienda de `oficinavirtual/` pesa), descarga como mínimo, uno a uno: `.htaccess`, `.php.ini`, `enviar.php`, `enviar.config.php`, `googlebe6fd46c002206cc.html` e `index.html`.
3. Abre la copia en tu ordenador y comprueba que están **`enviar.php`, `enviar.config.php`, `.htaccess` y `.php.ini`**, y que ninguno pesa 0 bytes. El `.htaccess` debe pesar unos 9,4 kB.
4. Guarda una segunda copia en otro sitio (otro disco o la nube).
5. **No sigas hasta tener la copia comprobada.**

## 2. El paquete

El paquete ya está hecho: **`oficinasya-subida-www.zip`** (9,4 MB, 254 ficheros). Lleva exactamente lo que va a `/www`:
- las 66 páginas (`index.html` y las carpetas de cada página, incluida `en/`);
- `assets/` (imágenes, favicon);
- en la raíz: `favicon.ico`, `robots.txt`, `sitemap.xml`, `llms.txt` y los `.html` del prototipo (`ubicaciones.html`, `blog.html`…), que el `.htaccess` convierte en 301.

No lleva nada de lo que empieza por `_`, ni `README.md`, ni `requirements.txt`, ni `.htaccess`, ni `enviar.php`.

Para volver a generarlo desde el repositorio, con todo commiteado:

```
git archive --format=zip -o oficinasya-subida-www.zip HEAD -- . ":(exclude)_*" ":(exclude).gitignore" ":(exclude)README.md" ":(exclude)requirements.txt"
```

## 3. Lo que NO se toca bajo ningún concepto

Ni se borra, ni se sobrescribe, ni se mueve:

- **`enviar.php`** y **`enviar.config.php`**
- **`.php.ini`**
- **`googlebe6fd46c002206cc.html`**
- **`oficinavirtual/`** (la tienda)
- **`OLD/`**, **`newsite/`**, **`cache/`**, **`.tmb/`**, **`.well-known/`**

El `.htaccess` solo se **edita** (paso 6), nunca se sustituye entero.

## 4. Subir el paquete

1. Sube **`oficinasya-subida-www.zip`** a **`/www`**.
2. Descomprímelo **en `/www` mismo** (no en una subcarpeta), con la opción **«sobrescribir los existentes»**.
   El zip no contiene ninguno de los ficheros del paso 3, así que no los toca. Las páginas se sustituyen todas a la vez, en segundos.
3. Borra `oficinasya-subida-www.zip` de `/www` cuando termine de descomprimir.

**Si el panel no puede descomprimir**, sube las carpetas a mano, en este orden, para que ninguna página nueva apunte a una imagen que aún no está:
1. `assets/` entera y `favicon.ico`.
2. `en/` y todas las carpetas de página.
3. Los ficheros de la raíz: `index.html`, `robots.txt`, `sitemap.xml`, `llms.txt` y los `.html` del prototipo.

## 5. Primera comprobación

Abre `https://www.oficinasya.es/` en una ventana privada. Tiene que verse la web nueva, con imágenes y el icono naranja en la pestaña.
**Si algo falla, para aquí** y sube la copia del paso 1.

## 6. El `.htaccess` (lo último que se cambia)

1. En el gestor de archivos, abre **`/www/.htaccess`** con el editor del panel.
2. Abre [CONFIGURACION-SERVIDOR.md](CONFIGURACION-SERVIDOR.md) y copia **entero** el bloque «Apache: `.htaccess`».
3. Pégalo **al principio** del `.htaccess`, antes de la primera línea que ya había, y **deja debajo todo lo que tenía**. Guarda.
4. Abre `https://oficinasya.es/` (sin www). Tiene que acabar en `https://www.oficinasya.es/`.
   - Si da **«Error 500»**: vuelve a poner el `.htaccess` de la copia del paso 1 y avisa al técnico.
   - Si no da error pero no cambia a www: el servidor no lee `.htaccess`. Manda al hosting el bloque nginx de CONFIGURACION-SERVIDOR.md.

## 7. Borrar las fuentes que se subieron por error

Están en `/www` y hoy cualquiera puede descargarlas (`/_build.py` y `/_data/centros.csv` responden). Con el `.htaccess` nuevo ya dan 404, pero hay que borrarlas. Borra **solo** esto, si existe en `/www`:

- las carpetas `_data/`, `_content/`, `_templates/`, `_tools/`, `_docs/`, `_hooks/`
- los ficheros `_build.py`, `_build.manifest`, `README.md`, `requirements.txt`

**Nada más.** Repasa la lista del paso 3 antes de confirmar cada borrado.

## 8. Comprobaciones, en este orden

Ábrelas en una ventana privada. Al lado va un comando opcional para PowerShell (`curl.exe` viene con Windows).

1. **El servidor lee el `.htaccess`.** `https://oficinasya.es/` → acaba en `https://www.oficinasya.es/`, sin «Error 500».
2. **Sin bucle con el https del hosting.** `http://oficinasya.es/blog` → acaba en `https://www.oficinasya.es/blog/` y la página carga.
3. **Sin noindex y con canonical bueno.** En `view-source:https://www.oficinasya.es/` (Chrome; en iPhone, desde el ordenador): buscar «noindex» da 0 resultados, y buscar «canonical» muestra `href="https://www.oficinasya.es/"`.
4. **Las URLs antiguas redirigen.**
   - `https://www.oficinasya.es/despachos/` → `https://www.oficinasya.es/alquiler-de-despachos/`
   - `https://www.oficinasya.es/centros/madrid-serrano/` → `https://www.oficinasya.es/oficinas-en-madrid/#serrano`
   - `curl.exe -sI https://www.oficinasya.es/despachos/` → `301` y `Location: https://www.oficinasya.es/alquiler-de-despachos/`
5. **Las fuentes y el WordPress viejo no se ven.** Deben dar **404**:
   - `https://www.oficinasya.es/_build.py`
   - `https://www.oficinasya.es/_data/centros.csv`
   - `https://www.oficinasya.es/OLD/wp-login.php`
6. **Lo del técnico sigue ahí.**
   - `https://www.oficinasya.es/enviar.php` → se ve `{"ok":false}`. Si sale 404, sube el `enviar.php` de la copia **ya**.
   - `https://www.oficinasya.es/googlebe6fd46c002206cc.html` → se ve `google-site-verification: googlebe6fd46c002206cc.html`.
7. **El formulario envía de verdad.** Ver el apartado 9.
8. **La tienda sigue funcionando.** `https://www.oficinasya.es/oficinavirtual/` → carga igual que antes de la subida. Si da error, quita nuestro bloque del `.htaccess` (vuelve a poner el de la copia) y avisa al técnico.
9. **La home se ve completa.** `https://www.oficinasya.es/` en ventana privada:
   - el icono naranja en la pestaña;
   - «Disponible desde YA!» en una línea;
   - los iconos de las tarjetas de servicio, sin emoji;
   - la foto de «Crece sin límites», los 3 avatares de los testimonios y las 3 tarjetas del blog.

## 9. El formulario

`enviar.php` lo escribió el técnico: el destinatario y el remitente están en `enviar.config.php` (o dentro de `enviar.php`), en el servidor. Desde fuera no se puede saber a qué dirección llegan los mensajes. **Pregúntaselo al técnico**, o míralo en la copia del paso 1.

1. En `https://www.oficinasya.es/#contact`, rellena el formulario con nombre «PRUEBA – no contestar», tu teléfono y tu email, y en el mensaje la fecha y la hora.
2. El botón debe ponerse verde: «✓ Enviado, te contactamos pronto!». Si se pone rojo («✗ No se pudo enviar»), avisa al técnico.
3. Comprueba que el correo llega, también en la carpeta de spam.
4. Repite en inglés: `https://www.oficinasya.es/en/#contact`.
5. Newsletter: en `https://www.oficinasya.es/blog/`, abajo, suscribe tu email. Debe salir «✓ Suscrito!».

## 10. Google Search Console

La verificación por fichero (`googlebe6fd46c002206cc.html`) ya está en `/www`, así que la propiedad existe. Mientras no se borre ese fichero, sigue verificada.

1. Entra en https://search.google.com/search-console y comprueba qué propiedad es: de **dominio** `oficinasya.es`, o de **prefijo** `https://www.oficinasya.es/` o `https://oficinasya.es/`.
   - Si solo hay una de prefijo **sin www**, no la borres: añade otra de prefijo `https://www.oficinasya.es/`; el mismo fichero de verificación sirve.
   - No uses «Cambio de dirección»: el dominio es el mismo.
2. En la propiedad de www (o la de dominio): **Sitemaps** → escribe `sitemap.xml` → **Enviar**. A las pocas horas debe estar «Correcto», con **66** URLs.
3. **Inspección de URLs** → `https://www.oficinasya.es/` → **Solicitar indexación**. Repite con `/alquiler-de-despachos/` y `/oficinas-en-madrid/`.
4. Dentro de 1 o 2 semanas, en **Páginas**: es normal que crezca «Página con redirección» (las URLs antiguas); no debe crecer «No se ha encontrado (404)» con URLs del WordPress antiguo.

## Si algo sale mal

Sube la copia del paso 1 a `/www`, sobrescribiendo. La web vuelve a estar como antes, con `enviar.php`, `enviar.config.php`, `.htaccess` y `.php.ini` originales. La tienda de `oficinavirtual/` no se habrá tocado en ningún momento.
