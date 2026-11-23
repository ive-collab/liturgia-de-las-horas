"""Genera calendarios.js a partir de calendarios/paises/*.json (extraídos de gcatholic.org).
Uso: python3 build_calendarios.py <carpeta paises> <salida calendarios.js>"""
import json, sys, glob, os
src, out = sys.argv[1], sys.argv[2]
# Países hispanohablantes sin calendario en gcatholic: se ofrecen con el calendario general.
SIN_DATOS = {'SV': 'El Salvador', 'HN': 'Honduras', 'NI': 'Nicaragua', 'CU': 'Cuba',
             'DO': 'República Dominicana', 'UY': 'Uruguay', 'PY': 'Paraguay', 'GQ': 'Guinea Ecuatorial'}
paises = {}
for f in sorted(glob.glob(os.path.join(src, '*.json'))):
    d = json.load(open(f, encoding='utf8'))
    k = d['code']
    ents = []
    for e in d['entries']:
        if e['op'] == 'rename':
            continue  # solo cambia la redacción del nombre; el libro usa la suya
        # Correcciones manuales verificadas
        if k == 'VE' and e['op'] == 'move' and e['es'].startswith('Nuestra Señora de los Dolores'):
            e = {'op': 'add', 'easterOffset': -9, 'rank': 'm', 'es': 'Nuestra Señora de los Dolores (Viernes de Dolores)'}
        ents.append({x: e[x] for x in ('op', 'date', 'genDate', 'easterOffset', 'rank', 'es') if x in e})
    paises[k] = {'nombre': d['name'], 'traslados': d['transfers'], 'cambios': ents}
for k, n in SIN_DATOS.items():
    paises.setdefault(k, {'nombre': n, 'traslados': None, 'cambios': [], 'sinDatos': True})
data = {'fuente': 'GCatholic.org, años 2025-2027', 'paises': paises}
with open(out, 'w', encoding='utf8') as f:
    f.write('// Generado por herramientas/build_calendarios.py — no editar a mano.\n')
    f.write('const CALENDARIOS = ' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n')
print(len(paises), 'países;', sum(len(p['cambios']) for p in paises.values()), 'cambios')
