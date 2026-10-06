# ⚠️ ANTES DE NADA: COPIA DE SEGURIDAD DE `/www`. EN EL SERVIDOR HAY FICHEROS QUE NO ESTÁN EN ESTE REPOSITORIO (`enviar.php`, `enviar.config.php`, `.htaccess`, `.php.ini`, LA VERIFICACIÓN DE GOOGLE Y LA TIENDA DE `/oficinavirtual/`). SI SE PIERDEN, NO HAY OTRA COPIA.

# Subir la web a www.oficinasya.es, paso a paso

Para seguirlo en orden desde el panel web del hosting (gestor de archivos), sin saltarse nada. Cada paso dice qué hacer y qué tienes que ver.
La configuración del servidor (el bloque para `.htaccess` y la versión nginx) está en [CONFIGURACION-SERVIDOR.md](CONFIGURACION-SERVIDOR.md).

## AHORA: corregir la subida del 5 de octubre de 2026 (tres pasos)

**Situación** (comprobada con curl el 5 y el 6 de octubre de 2026): la web nueva está en producción y bien, pero el 5 de octubre se subió **la carpeta entera del repositorio en vez del zip**, y luego se pegó en el `.htaccess` un bloque que **no es el nuestro**. Ese bloque tapa las fuentes con un 404, pero hace otras redirecciones (le faltan `/portfolio_category/…`, `/oficinas-vistuales`, `/experiencia-en-coworking/…`; manda `/web/` a la home y la paginación de los centros a `/ubicaciones/`), y lleva a las URLs antiguas pedidas sin www en dos saltos. **Las fuentes siguen en `/www`, solo tapadas.**

Antes de nada, **el paso 1 de esta guía (copia de seguridad de `/www`)**, aunque ya hicieras una antes de subir: la de ahora es la que tiene el `.htaccess` actual.

### Paso A. Sustituir el bloque del `.htaccess`

1. Abre **`/www/.htaccess`** con el editor del gestor de archivos (con «mostrar ficheros ocultos» activado).
2. **Borra el bloque que pegaste el 5 de octubre, entero.** Nada de él se aprovecha: el nuestro hace todo lo que hacía (bloquear fuentes, redirigir URLs antiguas) y más.
   - **La forma segura:** compara con el `.htaccess` de la copia que hiciste **antes** de subir la web el 5 de octubre (el original del técnico, unos 9,4 kB). **Todo lo que no estaba en ese fichero lo pegaste tú: se borra. Todo lo que sí estaba: se queda**, aunque no lo entiendas.
   - **Si no tienes esa copia**, estas señales distinguen una línea de la otra:

     | Es del bloque pegado (se borra) | Es del técnico o del hosting (se queda) |
     |---|---|
     | `RewriteRule` cuyo destino es una página nueva: `…/alquiler-de-despachos/`, `…/oficinas-en-…/`, `…/blog/`, `…/ubicaciones/`, `…/comunidad/`, `…/oficina-virtual/`, `…/salas-de-reuniones/`, `…/#contact` | Bloques con marcas del hosting o de WordPress: `# BEGIN WordPress`, `# php -- BEGIN cPanel-generated handler`, `# BEGIN LSCACHE`… hasta su `# END` |
     | `RewriteRule` que devuelven 404 a `_`, `.py`, `.md`, `README`, `OLD` (`[R=404]`) | `AddHandler`, `php_value`, `php_flag`, `SetEnv`, `Header set …`, `ErrorDocument`, `DirectoryIndex` |
     | Comentarios que hablan de la web nueva, de fuentes o de redirecciones antiguas | Reglas sobre `enviar.php`, `enviar.config.php`, `.php.ini`, `oficinavirtual`, `wp-config.php`, `.git` o el https (`%{HTTPS}`, `%{SERVER_PORT}`) |
     | Todo lo que esté **encima** del primer bloque que sí es del técnico | `<Files …>`, `<FilesMatch …>`, `<IfModule …>` que no redirigen a páginas nuevas |

     Si una línea no encaja en ninguna columna, **déjala** y pregúntale al técnico. Una línea de más del técnico no estorba: el bloque nuestro va delante.
3. Abre **[`_docs/bloque-htaccess.txt`](bloque-htaccess.txt)** (es el mismo bloque «Apache» de [CONFIGURACION-SERVIDOR.md](CONFIGURACION-SERVIDOR.md), solo), **selecciónalo todo y cópialo**. Empieza por `# BEGIN OficinasYA` y acaba en `# END OficinasYA` (379 líneas, 352 `RewriteRule`).
4. Pégalo **en la primera línea** del `.htaccess`, encima de todo lo que ha quedado. Guarda.
5. En una ventana privada:
   - `https://www.oficinasya.es/` carga. Si da **«Error 500»**, vuelve a poner el `.htaccess` de la copia de hoy y avísame.
   - `https://www.oficinasya.es/portfolio_category/castellon/` → acaba en `https://www.oficinasya.es/oficinas-en-castellon/`. **Si da 404, sigue mandando el bloque viejo**: no se borró entero o el nuevo no quedó arriba.

### Paso B. Borrar las fuentes

**Primero, ¿hay una carpeta `.git` en `/www`?** En el gestor de archivos, con **«mostrar ficheros ocultos»** activado, mira la lista de `/www`. Desde fuera no se puede saber: `/.git/HEAD` y `/.gitignore` responden 403, y eso es lo mismo que respondería una regla del servidor que los proteja aunque no existan.

- **No hay `.git`** → borra la lista de abajo y ya está.
- **Hay `.git`** → depende de cómo llegó:
  - **Si la web la subiste tú con el gestor de archivos o por FTP** (lo que pasó el 5 de octubre), esa `.git` es una copia más de tu carpeta, con **todo el historial del repositorio** dentro. No hay ningún «despliegue» que la use: **bórrala también**, junto con la lista.
  - **Si en el panel hay un apartado «Git» (o «Git Version Control») con este repositorio, o en `/www` hay un fichero `.cpanel.yml`**, alguien montó una subida automática con git. Entonces **no borres nada todavía**: volvería en la siguiente actualización. La solución es que el técnico quite esa subida automática (o la cambie para que copie solo lo que va en el zip); después, se borra la lista. Mientras tanto, el bloque del paso A ya devuelve 404 a todo eso.

**La lista exacta.** En `/www`, y solo en `/www` (no dentro de otras carpetas). Lo que no exista, se salta:

Carpetas:
```
_content
_data
_docs
_hooks
_templates
_tools
__pycache__
fotos_nuevas
.claude
.git        ← solo en el caso «la subiste tú», ver arriba
```

Ficheros:
```
_build.py
_build.manifest
README.md
requirements.txt
datos-centros.csv
__b5.py
.gitignore
```

`datos-centros.csv` es la hoja del cliente con precios y fianzas por centro: si está, es lo más importante de la lista. **No borres nada que no esté aquí**: en especial `.htaccess`, `.php.ini`, `.well-known`, `.tmb`, `cache`, `newsite`, `OLD`, `oficinavirtual`, `enviar.php`, `enviar.config.php`, `googlebe6fd46c002206cc.html`, `assets`, `en` ni ninguna carpeta de página.

**¿Puede romper algo borrarlas con la web en producción?** Lo comprobado:
- **Las páginas no las usan.** La web es HTML estático: ninguno de los 254 ficheros del zip enlaza ni carga nada de esta lista (lo he buscado en todos). Ya hoy esas rutas dan 404 y la web funciona: borrarlas no cambia lo que ve nadie.
- **Google no lo nota**: ya dan 404 y no están en el sitemap.
- **Lo que no puedo ver es `enviar.php`** (es del técnico). Es muy improbable que lea algo de `_data/` o de `datos-centros.csv`, pero **prueba el formulario después** (apartado 9). Si fallara, sube desde la copia solo el fichero que falte y avísame.
- **El riesgo real es humano**: borrar algo de al lado (`cache` por `_content`, `.well-known` por `.claude`, `.htaccess` por `.gitignore`). Por eso: copia antes, la lista de arriba, y **de uno en uno**, sin «seleccionar todo». Muchos paneles borran sin papelera.
- **`.git`**: solo rompe algo si hay una subida automática con git (el segundo caso de arriba).

### Paso C. Subir lo que ha cambiado

Desde lo que hay en producción (el commit `a4afcdd`) solo ha cambiado **una página**: la del artículo de email marketing, al que se le han quitado tres enlaces a sitios que ya no existen. Se sube ese fichero y nada más:

```
dispara-tus-ventas-a-traves-del-email-marketing-con-estas-claves/index.html
```

Súbelo **encima** del que hay en `/www/dispara-tus-ventas-a-traves-del-email-marketing-con-estas-claves/` (sobrescribir). Es un solo fichero que se reemplaza de golpe: la web no queda rota en ningún momento. Lo sacas del zip `oficinasya-subida-www.zip` o del repositorio.

El orden de los tres pasos es **A → B → C**: primero el `.htaccess` (que tapa todo lo que se va a borrar con el comportamiento definitivo), luego el borrado, y la página al final (es independiente).

Cuando acabes, avísame: compruebo todo contra el servidor con `python _tools/verificar_vivo.py` (las 66 páginas, las 345 redirecciones, las fuentes, el formulario, la tienda y `OLD/`) y la auditoría de clics en vivo (`python _tools/auditoria_clicks.py --all --base https://www.oficinasya.es`).

---

## Lo que hay hoy en el servidor

La web se sirve desde **`/www`**, no desde la raíz de la cuenta. Dentro de `/www` hay, además de la web actual:

| Qué | Qué es | Qué se hace |
|---|---|---|
| `enviar.php`, `enviar.config.php` | El formulario de contacto y su configuración (del técnico) | **NO SE TOCA** |
| `.htaccess` | Reglas del técnico; desde el 5 de octubre de 2026, además, un bloque de redirecciones que **no** sale de este repositorio (ver la nota de abajo) | Se edita en el paso 6: nuestro bloque va **al principio** y **sustituye** a ese |
| `.php.ini` | Configuración de PHP | **NO SE TOCA** |
| `googlebe6fd46c002206cc.html` | Verificación de Search Console | **NO SE TOCA** (si se borra, se pierde la propiedad) |
| `oficinavirtual/` | Otra web en marcha: WordPress con WooCommerce («Oficina Virtual de Oficinas YA!»), que se ve en `https://oficinavirtual.oficinasya.es/` | **NO SE TOCA** |
| `OLD/` | Núcleo del WordPress anterior, con su `wp-config.php` (credenciales) | **NO SE BORRA** (lo decide el técnico). El `.htaccess` nuevo lo bloquea al público |
| `newsite/`, `cache/`, `.tmb/`, `.well-known/` | Carpetas del hosting y del panel | **NO SE TOCAN** |
| `_data/`, `_content/`, `_templates/`, `_tools/`, `_docs/`, `_hooks/`, `_build.py`, `_build.manifest`, `README.md`, `requirements.txt`, y quizá `.git/`, `.claude/`, `__pycache__/`, `fotos_nuevas/`, `datos-centros.csv`, `__b5.py`, `.gitignore` | Fuentes y ficheros de trabajo, subidos por error el 5 de octubre de 2026 (la carpeta del repositorio en lugar del zip) | **SE BORRAN**: lista exacta en «Paso B» arriba |

**Cómo estaba el servidor el 5 de octubre de 2026 por la noche** (comprobado con curl, no con capturas de buscador):
- La web nueva está subida, con el contenido del último commit, pero **se subió el repositorio entero, no el zip**: de las 10:50 a las 22:45 aprox. (hora peninsular) `/_build.py`, `/_docs/DESPLIEGUE.md`, `/README.md`… se podían descargar.
- Hacia las 22:45 alguien pegó en el `.htaccess` un bloque que bloquea las fuentes y redirige las URLs antiguas. **No es el de [CONFIGURACION-SERVIDOR.md](CONFIGURACION-SERVIDOR.md)**: le faltan reglas (`/portfolio_category/castellon/`, `/oficinas-vistuales` siguen dando 404) y otras van a otro destino (`/web/` va a la home; `/centros/madrid-serrano/page/2/`, a `/ubicaciones/`). En el paso 6 se sustituye por el nuestro.
- **No hay WordPress sirviéndose** en `/contacto/` ni en `/ubicaciones/`: `/ubicaciones/` es la página nueva y `/contacto/` redirige a `/#contact`. La plantilla antigua que citaba una auditoría es la que **Google y Bing guardan en su índice** (títulos «Contacto - Oficinas YA!», «Ubicaciones - Oficinas YA!»), no la que sirve el servidor. Se irá sola cuando Google vuelva a pasar y encuentre las 301.
- `/.git/` responde 403 (no 404): puede que en `/www` haya una carpeta `.git`, es decir, que la web se esté subiendo con git. Ver el paso 7.

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

**Se sube el zip, no el repositorio.** Ni con el gestor de archivos, ni con FTP, ni con `git clone`/`git pull` en `/www`: el repositorio lleva las fuentes, que no deben estar en el servidor.

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
2. Abre [CONFIGURACION-SERVIDOR.md](CONFIGURACION-SERVIDOR.md) y copia **entero** el bloque «Apache: `.htaccess`». Empieza por `# BEGIN OficinasYA` y acaba en `# END OficinasYA`.
3. **Si el `.htaccess` ya tiene reglas de OficinasYA**, bórralas primero:
   - si hay un `# BEGIN OficinasYA`, borra desde esa línea hasta `# END OficinasYA`, las dos incluidas;
   - si no hay marcas pero arriba hay `RewriteRule` que redirigen URLs antiguas (`despachos`, `centros/…`, `category/`…) o bloquean `_`, son del bloque que se pegó el 5 de octubre de 2026: bórralas hasta donde empiece lo que había antes (compáralo con el `.htaccess` de la copia del paso 1). **Lo del técnico no se toca**; si dudas de una línea, déjala y pregúntale.

   Dos bloques a la vez no se suman: gana la primera regla que coincide, y las viejas taparían a las nuevas.
4. Pega el bloque **al principio** del `.htaccess`, antes de la primera línea que queda, y **deja debajo todo lo que tenía**. Guarda.
5. Abre `https://oficinasya.es/` (sin www). Tiene que acabar en `https://www.oficinasya.es/`.
   - Si da **«Error 500»**: vuelve a poner el `.htaccess` de la copia del paso 1 y avisa al técnico.
   - Si no da error pero no cambia a www: el servidor no lee `.htaccess`. Manda al hosting el bloque nginx de CONFIGURACION-SERVIDOR.md.

## 7. Borrar las fuentes que se subieron por error

Con el `.htaccess` nuevo ya dan 404, pero hay que borrarlas. La lista exacta, y qué hacer si hay una carpeta `.git`, está en **«Paso B. Borrar las fuentes»**, al principio de esta guía.

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
   - **Es nuestro bloque, y no otro:** `https://www.oficinasya.es/portfolio_category/castellon/` → `https://www.oficinasya.es/oficinas-en-castellon/`, y `https://www.oficinasya.es/web/` → `https://www.oficinasya.es/blog/`. Si la primera da 404 o la segunda va a la home, sigue activo el bloque del 5 de octubre: vuelve al paso 6.3.
   - `https://www.oficinasya.es/contacto/` → `https://www.oficinasya.es/#contact`
5. **Las fuentes y el WordPress viejo no se ven.** Deben dar **404**:
   - `https://www.oficinasya.es/_build.py`
   - `https://www.oficinasya.es/_docs/DESPLIEGUE.md`
   - `https://www.oficinasya.es/README.md`
   - `https://www.oficinasya.es/OLD/wp-login.php`
6. **Lo del técnico sigue ahí.**
   - `https://www.oficinasya.es/enviar.php` → se ve `{"ok":false}`. Si sale 404, sube el `enviar.php` de la copia **ya**.
   - `https://www.oficinasya.es/googlebe6fd46c002206cc.html` → se ve `google-site-verification: googlebe6fd46c002206cc.html`.
7. **El formulario envía de verdad.** Ver el apartado 9.
8. **La tienda sigue funcionando.** `https://oficinavirtual.oficinasya.es/` → carga la tienda («Oficina Virtual de Oficinas YA!»). En `https://www.oficinasya.es/oficinavirtual/` responde la misma tienda con su página de «no encontrada»: es normal, ya era así antes. Si da error, quita nuestro bloque del `.htaccess` (vuelve a poner el de la copia) y avisa al técnico.
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
