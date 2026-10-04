"""Tests del generador. Sin dependencias: python _tools/test_build.py (sale con 1 si algo falla).
Nacieron del bug del "m2": el 2 de la unidad se leyo dos veces como un tamano de despacho."""
import sys, pathlib, csv, importlib.util
ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('build', ROOT / '_build.py'); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
fallos = []
def check(cond, msg):
    if not cond: fallos.append(msg)

# parse_m2: todas las formas en que puede venir la unidad
for texto, esperado in [('10 a 47 m2', (10, 47)), ('10 a 47 m²', (10, 47)), ('10 a 47 m 2', (10, 47)), ('10-47m2', (10, 47)),
                        ('17 a 250 m2', (17, 250)), ('6 a 38 M2', (6, 38)), ('22 metros cuadrados', (22, 22)), ('', None), ('   ', None)]:
    r = b.parse_m2(texto); check(r == esperado, f'parse_m2({texto!r}) = {r}, esperado {esperado}')
check(b.format_m2('10 a 47 m2') == '10 a 47 m²', 'format_m2 es')
check(b.format_m2('10 a 47 m2', 'to') == '10 to 47 m²', 'format_m2 en')

# CSV real: ningun rango por debajo del minimo plausible, y ninguno con el 2 de la unidad colado
with open(ROOT / '_data' / 'centros.csv', encoding='utf-8', newline='') as f:
    rows = [r for r in csv.DictReader(f) if r['activo'].strip().lower() == 'si']
rangos = [(r['centro'], b.parse_m2(r['despachos_m2'])) for r in rows if r['despachos_m2'].strip()]
check(rangos, 'el CSV no tiene ningun rango de m²')
for centro, (lo, hi) in rangos:
    check(lo >= b.M2_MIN_PLAUSIBLE, f'{centro}: minimo {lo} m² < {b.M2_MIN_PLAUSIBLE} (¿el 2 de "m2"?)')
    check(lo <= hi <= 3000, f'{centro}: rango raro {lo}-{hi}')
check(min(lo for _, (lo, hi) in rangos) >= b.M2_MIN_PLAUSIBLE, f'minimo global de m² = {min(lo for _, (lo, hi) in rangos)}')

# el build debe negarse si le cuelan un "2 a 69": load_data() de verdad, con una copia de _data/ cuyo CSV
# lleva ese rango (antes esta prueba se simulaba a si misma y no podia fallar)
import shutil, tempfile
with tempfile.TemporaryDirectory() as tmp:
    datos = pathlib.Path(tmp) / '_data'; shutil.copytree(ROOT / '_data', datos)
    csvp = datos / 'centros.csv'; txt = csvp.read_text(encoding='utf-8')
    filas = txt.splitlines(); cab = filas[0].split(','); i = cab.index('despachos_m2')
    fila = next(r for r in csv.reader(filas[1:]) if r[i].strip())
    fila_mala = list(fila); fila_mala[i] = '2 a 69 m2'
    import io; buf = io.StringIO(); csv.writer(buf, lineterminator='\n').writerow(fila_mala)
    original = io.StringIO(); csv.writer(original, lineterminator='\n').writerow(fila)
    csvp.write_text(txt.replace(original.getvalue().rstrip('\n'), buf.getvalue().rstrip('\n'), 1), encoding='utf-8')
    check('2 a 69 m2' in csvp.read_text(encoding='utf-8'), 'no he podido preparar el CSV de prueba')
    data_real = b.DATA; b.DATA = datos
    try:
        b.load_data(); check(False, 'load_data() acepta un CSV con "2 a 69 m2" (la comprobacion del minimo no salta)')
    except SystemExit as e:
        check('parseo' in str(e), f'load_data() aborta, pero no por el minimo de m²: {e}')
    finally:
        b.DATA = data_real

if fallos:
    print('FALLOS:'); [print('  -', x) for x in fallos]; sys.exit(1)
print(f'test_build: {len(rangos)} rangos de m² del CSV, minimo {min(lo for _, (lo, hi) in rangos)} m², parseo OK')
