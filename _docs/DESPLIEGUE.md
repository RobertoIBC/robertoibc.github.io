# ⚠️ NO BORRES NI SOBRESCRIBAS `enviar.php`. ES EL FORMULARIO DE CONTACTO, LO CREÓ EL TÉCNICO Y NO ESTÁ EN ESTE REPOSITORIO: SI SE PIERDE, NO HAY COPIA. HAZ LA COPIA DE SEGURIDAD DEL PASO 1 ANTES DE TOCAR NADA.

# Subir la web a www.oficinasya.es, paso a paso

Para seguirlo en orden, sin saltarse nada. Cada paso dice qué hacer y qué tienes que ver.
La configuración del servidor (el `.htaccess` y la versión nginx) está en [CONFIGURACION-SERVIDOR.md](CONFIGURACION-SERVIDOR.md).

Necesitas: acceso FTP (o el gestor de archivos del hosting) a la raíz de la web, y este repositorio en tu ordenador con `git`.

---

## 1. ANTES DE SUBIR NADA: copia de seguridad del servidor

**Este es el único paso que no tiene vuelta atrás si te lo saltas.** Todo lo demás se puede deshacer subiendo esta copia. `enviar.php` y el `.htaccess` que haya hoy en el servidor no existen en ningún otro sitio.

1. **Antes de subir, sobrescribir o borrar ningún fichero**, conéctate por FTP y descarga **la raíz entera de la web** a una carpeta de tu ordenador llamada `copia-servidor-AAAA-MM-DD`.
2. Activa «mostrar ficheros ocultos» en el cliente FTP **antes de descargar**: el `.htaccess` empieza por punto y, sin esa opción, ni se ve ni se descarga.
3. Abre la carpeta de la copia y comprueba que están, y que no pesan 0 bytes:
   - **`enviar.php`**: tiene que estar sí o sí. Si no está en la copia, para y avisa al técnico.
   - **`.htaccess`**: si estaba en el servidor, tiene que estar en la copia. Si el servidor no tenía, apúntalo («no había `.htaccess`»), porque lo necesitarás en el paso 5.
4. Guarda una segunda copia de esa carpeta en otro sitio (otro disco o la nube).
5. **No sigas al paso 2 hasta tener la copia comprobada.** Si algo sale mal después, se vuelve atrás subiéndola tal cual.

## 2. Preparar el paquete

En la carpeta del repositorio, con todo commiteado, ejecuta:

```
git archive --format=zip -o oficinasya-web.zip HEAD -- . ":(exclude)_*" ":(exclude).gitignore" ":(exclude)README.md" ":(exclude)requirements.txt"
```

Sale `oficinasya-web.zip`, de unos 12 MB y 254 ficheros. Descomprímelo en una carpeta `subir/`. **Lo que hay en `subir/` es exactamente lo que se sube.**

## 3. Qué se sube y qué no

**SE SUBE** (todo lo que hay en `subir/`):
- las carpetas de página: `alquiler-de-despachos/`, `salas-de-reuniones/`, `oficina-virtual/`, `coworking/`, `ubicaciones/`, `comunidad/`, `blog/`, `aviso-legal/`, `politica-de-cookies/`, `politica-de-privacidad/`, las 17 `oficinas-en-…/`, los 10 artículos y `en/` entera;
- `assets/` (imágenes, entre ellas las nuevas de `assets/img/favicon/`, `home/`, `hub/` y `blog/`);
- en la raíz: `index.html`, `favicon.ico`, `robots.txt`, `sitemap.xml`, `llms.txt`;
- en la raíz, los `.html` del prototipo (`ubicaciones.html`, `comunidad.html`, `blog.html`, `aviso-legal.html`, `cookies.html`, `privacidad.html`). Son redirecciones; el `.htaccess` las convierte en 301.

**NO SE SUBE NUNCA:**
- `_build.py`, `_build.manifest`, `_data/`, `_content/`, `_templates/`, `_tools/`, `_docs/`, `_hooks/` (las fuentes);
- `README.md`, `requirements.txt`, `.gitignore`, `.git/`, `.claude/`;
- `datos-centros.csv`, `fotos_nuevas/`, `__pycache__/`, `__b5.py` (ficheros locales; no están en el paquete).

**NO SE TOCA EN EL SERVIDOR:**
- **`enviar.php`**: no está en el paquete; no lo borres ni subas nada con ese nombre;
- **`.htaccess`**: se sustituye en el paso 5, no antes.

## 4. Subir, en este orden (para que la web no quede rota a medias)

Sube **encima** de lo que hay, sobrescribiendo. **No borres antes la carpeta del servidor**: así `enviar.php` se queda donde está.

1. `assets/` entera y `favicon.ico`. Son ficheros nuevos o iguales: la web en vivo no cambia todavía.
2. `en/` y todas las carpetas de página. Sobrescribe los `index.html`.
3. Los ficheros de la raíz: `index.html`, `robots.txt`, `sitemap.xml`, `llms.txt` y los `.html` del prototipo.
4. Abre `https://www.oficinasya.es/` en una ventana privada. Tiene que verse bien, con imágenes e icono en la pestaña. Si algo falla, para aquí y vuelve a subir la copia del paso 1.

## 5. El `.htaccess` (lo último)

1. Abre [CONFIGURACION-SERVIDOR.md](CONFIGURACION-SERVIDOR.md) y copia **entero** el bloque «Apache: `.htaccess`».
2. Si en la copia del paso 1 **no había** `.htaccess`: crea un fichero de texto llamado exactamente `.htaccess`, pega el bloque y súbelo a la raíz.
3. Si **sí había** `.htaccess`: ábrelo, pega el bloque **al principio**, deja debajo lo que tuviera y súbelo.
4. Abre `https://oficinasya.es/` (sin www). Tiene que acabar en `https://www.oficinasya.es/`.
   - Si da «Error 500», sube el `.htaccess` de la copia del paso 1 (o bórralo si no había) y avisa al técnico.
   - Si no da error pero no cambia a www, el servidor no lee `.htaccess`: manda al hosting el bloque nginx de CONFIGURACION-SERVIDOR.md.

## 6. Borrar del servidor lo que no debe estar

Hoy el servidor tiene expuestas las fuentes del prototipo. Con el `.htaccess` ya dan 404, pero bórralas igual. Borra **solo** esto, si existe en la raíz:

`_build.py`, `_build.manifest`, `_data/`, `_content/`, `_templates/`, `_tools/`, `_docs/`, `_hooks/`, `README.md`, `requirements.txt`

No borres nada más. **`enviar.php` se queda.**

## 7. Comprobaciones (en este orden)

Ábrelas en una ventana privada para que el navegador no use lo que tenía guardado. Al lado de cada una va un comando opcional para PowerShell: `curl.exe` viene con Windows.

1. **Sin noindex.** Abre `view-source:https://www.oficinasya.es/`, pulsa Ctrl+F y busca `noindex`.
   Debe decir **0 resultados**. (`curl.exe -s https://www.oficinasya.es/ | findstr noindex` no debe sacar nada.)
2. **Canonical con www.** En esa misma vista, busca `canonical`.
   Debe verse `<link rel="canonical" href="https://www.oficinasya.es/" />`.
3. **Tres URLs antiguas redirigen con 301.** Ábrelas y mira en qué dirección acabas:
   - `https://www.oficinasya.es/despachos/` → `https://www.oficinasya.es/alquiler-de-despachos/`
   - `https://www.oficinasya.es/centros/madrid-serrano/` → `https://www.oficinasya.es/oficinas-en-madrid/#serrano` (baja directo a la ficha de Serrano)
   - `https://www.oficinasya.es/category/blog/page/2/` → `https://www.oficinasya.es/blog/`

   Para ver que es 301: `curl.exe -sI https://www.oficinasya.es/despachos/` → `HTTP/1.1 301` y `Location: https://www.oficinasya.es/alquiler-de-despachos/`.
4. **Las fuentes no se ven.** Estas cuatro deben dar **404 (Not Found)**:
   - `https://www.oficinasya.es/_build.py`
   - `https://www.oficinasya.es/_data/centros.csv`
   - `https://www.oficinasya.es/README.md`
   - `https://www.oficinasya.es/requirements.txt`
5. **Sin www va a www.** Abre `https://oficinasya.es/` y también `https://oficinasya.es/coworking/`.
   La barra de direcciones debe acabar en `https://www.oficinasya.es/` y `https://www.oficinasya.es/coworking/`.
   (`curl.exe -sI https://oficinasya.es/` → `301` y `Location: https://www.oficinasya.es/`.)
6. **Favicon.** Abre `https://www.oficinasya.es/favicon.ico`: se ve el icono naranja.
   En la pestaña de `https://www.oficinasya.es/` aparece ese icono. Si no sale, cierra la pestaña y ábrela en ventana privada: los navegadores guardan el favicon mucho tiempo.
7. **Imágenes de la home.** Abre `https://www.oficinasya.es/`, pulsa F12, ve a la pestaña **Red** (Network), filtra por **Img** y recarga.
   Ninguna fila en rojo. Baja la página entera y comprueba que se ven:
   - los dos iconos de las tarjetas de servicio (sin emoji);
   - la foto de «Crece sin límites»;
   - los tres avatares de los testimonios;
   - las tres tarjetas del blog.
8. **Carpeta sin barra en un salto.** `curl.exe -sI https://www.oficinasya.es/blog` → `301` y `Location: https://www.oficinasya.es/blog/` (con **https**).
9. **El formulario funciona:** ver el apartado 8.

## 8. El formulario

`enviar.php` lo escribió el técnico: el destinatario y el remitente están **dentro de ese fichero**, en el servidor. Desde aquí no se puede saber a qué dirección llegan los mensajes, porque el servidor ejecuta el PHP y nunca lo enseña. **Pregúntaselo al técnico**, o abre `enviar.php` desde la copia del paso 1: es texto y las direcciones están arriba.

Para probarlo:
1. En `https://www.oficinasya.es/#contact` rellena el formulario con nombre `PRUEBA – no contestar`, tu teléfono y tu email, y en el mensaje escribe la fecha y la hora.
2. El botón debe ponerse verde: «✓ Enviado, te contactamos pronto!». Si se pone rojo («✗ No se pudo enviar»), el problema está en `enviar.php` o en el correo del hosting: avisa al técnico.
3. Comprueba que el correo llega a la dirección que te diga el técnico. Mira también la carpeta de spam.
4. Repite en inglés: `https://www.oficinasya.es/en/#contact`.
5. Newsletter: en `https://www.oficinasya.es/blog/`, abajo, suscribe tu email. Debe salir «✓ Suscrito!» y llegar el aviso a la misma dirección.

## 9. Google Search Console

1. Entra en https://search.google.com/search-console y mira qué propiedad hay para el sitio:
   - **Propiedad de dominio `oficinasya.es`**: cubre con y sin www. Sigue en el punto 2.
   - **Solo una propiedad de prefijo `https://oficinasya.es/` (sin www)**: no la borres. Añade otra con «Añadir propiedad» → **Prefijo de la URL** → `https://www.oficinasya.es/`. Verifícala con la opción «Etiqueta HTML» o con Google Analytics si está; si no se puede, pide al hosting que verifique por DNS una propiedad de **Dominio**, que es la mejor opción porque cubre las dos.
   - **No uses «Cambio de dirección»**: es para cambiar de dominio, y aquí el dominio es el mismo.
2. En la propiedad de www (o en la de dominio): menú **Sitemaps** → escribe `sitemap.xml` → **Enviar**.
   A las pocas horas el estado debe ser «Correcto», con **66** URLs descubiertas.
3. Menú **Inspección de URLs** → pega `https://www.oficinasya.es/` → **Solicitar indexación**. Repite con `https://www.oficinasya.es/alquiler-de-despachos/` y `https://www.oficinasya.es/oficinas-en-madrid/`.
4. Dentro de 1 o 2 semanas, en **Páginas**:
   - es normal que crezca «Página con redirección»: son las URLs antiguas;
   - no debe crecer «No se ha encontrado (404)» con URLs del WordPress antiguo; si crece, pásale la lista al técnico.

## 10. GitHub Pages (el prototipo)

El repositorio también se publica en `https://robertoibc.github.io/`. Desde este commit, esa copia **ya no lleva noindex**: Google la puede indexar, aunque su canonical apunta a www.oficinasya.es.
Cuando la web real esté en marcha, desactiva GitHub Pages: en GitHub, el repositorio → **Settings** → **Pages** → **Source: None** (o «Unpublish site»).

## Si algo sale mal

Sube la carpeta `copia-servidor-AAAA-MM-DD` del paso 1 tal cual, sobrescribiendo. La web vuelve a estar como antes, con `enviar.php` y el `.htaccess` originales.
