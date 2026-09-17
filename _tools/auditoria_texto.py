"""Auditoria de texto: la regla "el texto no se borra, se reparte", comprobada de verdad.
Para cada fichero de _content/ compara el MULTICONJUNTO de palabras (cada palabra, tantas veces como aparece)
de la version de referencia en git con la del fichero actual, y lista las palabras que han desaparecido.
    python _tools/auditoria_texto.py              # referencia: origin/main (lo ultimo publicado)
    python _tools/auditoria_texto.py HEAD~3       # cualquier ref de git
Solo mira _content/ (paginas, servicios, ciudades, blog): mover una frase del cuerpo al front matter no da
aviso (la palabra sigue en el fichero); borrarla, si. Cazo un parrafo de horarios perdido en Sevilla el
17-09-2026 al repartir la introduccion en tarjetas: nadie lo habria visto a ojo."""
import sys, pathlib, re, subprocess, collections, os
os.chdir(pathlib.Path(__file__).resolve().parent.parent)
ref = sys.argv[1] if len(sys.argv) > 1 else 'origin/main'
def words(s):
    return collections.Counter(re.findall(r"[\wáéíóúñüÁÉÍÓÚÑÜ²]+", s.replace('**', '').lower()))
files = sorted(p for p in pathlib.Path('_content').rglob('*') if p.suffix in ('.md', '.html'))
perdidas = 0; nuevos = 0
for f in files:
    r = subprocess.run(['git', 'show', f'{ref}:{f.as_posix()}'], capture_output=True)
    if r.returncode != 0:
        nuevos += 1; continue   # fichero nuevo respecto a la referencia
    old = r.stdout.decode('utf-8', 'replace'); new = f.read_text(encoding='utf-8')
    diff = words(old) - words(new)
    # palabras de sintaxis que cambian sin que cambie el texto
    for k in ('foto', 'alt', 'titulo', 'texto', 'para', 'centro', 'ancla', 'sub', 'num', 'label', 'elegir', 'cifras', 'galeria', 'tarjetas', 'formas', 'pasos', 'perfiles', 'incluye', 'donde', 'tabla', 'puntos'):
        diff.pop(k, None)
    if diff:
        perdidas += 1
        print(f'{f.as_posix()}: palabras que estaban en {ref} y ya no: {dict(diff.most_common(12))}')
print(f'{len(files)} ficheros de contenido comparados con {ref}; {nuevos} nuevos; con palabras perdidas: {perdidas}')
sys.exit(1 if perdidas else 0)
