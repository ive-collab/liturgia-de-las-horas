"""Importa oficios propios nacionales del sitio liturgiadelashoras.github.io (carpeta sync/)
y genera tomos/tomo-5.json en el mismo formato que los demás tomos.
Uso: python3 import_propios.py <carpeta sync> <salida tomo-5.json>"""
import sys, os, re, json, html
sys.path.insert(0, os.path.dirname(__file__))
from gparse import tokens
SYNC, OUT = sys.argv[1], sys.argv[2]

# id, nombre, claves (todas deben aparecer en el nombre de la celebración), rango, carpeta, I vísperas
CELEBS = [
 ('reina-de-la-paz', 'SANTA MARÍA, REINA DE LA PAZ', ['REINA', 'PAZ'], 'm', '2026/ene/24/1', None),
 ('felipe-de-jesus', 'SAN FELIPE DE JESÚS, PROTOMÁRTIR MEXICANO', ['FELIPE', 'JESUS'], 'F', '2026/feb/05/2', None),
 ('valle', 'NUESTRA SEÑORA DEL VALLE', ['VALLE'], 'M', '2026/abr/18/1', None),
 ('lujan', 'NUESTRA SEÑORA DE LUJÁN', ['LUJAN'], 'S', '2025/may/08/1', '2026/may/07/1'),
 ('itati', 'NUESTRA SEÑORA DE ITATÍ', ['ITATI'], 'M', '2026/jul/09/1', None),
 ('chiquinquira', 'NUESTRA SEÑORA DEL ROSARIO DE CHIQUINQUIRÁ', ['CHIQUINQUIRA'], 'F', '2026/jul/09/2', None),
 ('solano', 'SAN FRANCISCO SOLANO, PRESBÍTERO', ['SOLANO'], 'M', '2026/jul/24/1', None),
 ('merced', 'NUESTRA SEÑORA DE LA MERCED', ['MERCED'], 'M', '2026/sep/24/1', None),
 ('medianera', 'MARÍA, MEDIANERA DE TODAS LAS GRACIAS', ['MEDIANERA'], 'M', '2026/nov/07/1', None),
 ('roque-gonzalez', 'SANTOS ROQUE GONZÁLEZ, ALFONSO RODRÍGUEZ Y JUAN DEL CASTILLO, PRESBÍTEROS Y MÁRTIRES', ['ROQUE', 'GONZALEZ'], 'M', '2026/nov/17/1', None),
 ('isabel-hungria', 'SANTA ISABEL DE HUNGRÍA, RELIGIOSA', ['ISABEL', 'HUNGRIA'], 'M', '2026/nov/19/1', None),
]
# Partes que en una memoria NO son propias (vienen del día o del común)
NO_PROPIO_MEM = {'ol': {'salmodia', 'verso', 'l1', 'tedeum'}, 'l': {'salmodia', 'lb', 'rb', 'preces'}, 'v': {'salmodia', 'lb', 'rb', 'preces'}}
SKIP_RED = re.compile(r'^\(|^INVOCACI|^se sigue el esquema|^Padre nuestro|^Of La', re.I)

def esc(s): return html.escape(s, quote=False)
def segments(path, hour):
    """Devuelve lista de (clave, [párrafos]) de una hora."""
    T = tokens(path); segs = []; cur = None; mode = 'inv0'; himnos = 0; seen_ps = False
    def start(k, para):
        nonlocal cur; cur = [k, [para] if para else []]; segs.append(cur)
    for t in T:
        if t[0] == 'red':
            x = t[1].strip(); X = x.upper()
            XC = re.sub(r'[\s.:]+$', '', X)
            if XC in ('CONCLUSIÓN', 'CONCLUSION'): break
            if X == 'INVITATORIO': mode = 'inv'; start('antinv', None); continue
            if re.match(r'SALMO 94\b', X) and mode == 'inv': mode = 'skip'; continue
            if X.startswith('HIMNO:'):
                himnos += 1; mode = 'txt'
                if hour == 'ol' and himnos > 1: start('tedeum', ['l', 'HIMNO <i>Te Deum</i>', 'tedeum'])
                else: start('himno', ['l', 'HIMNO', 'himno']); cur[1].append(['ti', esc(x.split(':', 1)[1].strip())])
                continue
            if X == 'SALMODIA': mode = 'txt'; start('salmodia', ['l', 'SALMODIA', 'salmodia']); continue
            if X.startswith('PRIMERA LECTURA'): mode = 'read'; start('l1', ['l', 'PRIMERA LECTURA', 'l1']); continue
            if X.startswith('SEGUNDA LECTURA'): mode = 'read'; start('l2', ['l', 'SEGUNDA LECTURA', 'l2']); continue
            if XC in ('ORACIÓN', 'ORACION'): mode = 'read'; start('oracion', ['l', 'Oración', 'oracion']); continue
            if X.startswith('LECTURA BREVE'): mode = 'read'; start('lb', ['l', esc(re.sub(r'\s+', ' ', x)), 'lb']); continue
            if X.startswith('RESPONSORIO BREVE'): mode = 'txt'; start('rb', ['l', 'RESPONSORIO BREVE', 'rb']); continue
            if X.startswith('CÁNTICO EVANG') or X.startswith('CANTICO EVANG'): mode = 'txt'; start('ce', ['l', 'CÁNTICO EVANGÉLICO', 'ce']); continue
            if X.startswith('PRECES'): mode = 'txt'; start('preces', ['l', 'PRECES', 'preces']); continue
            if SKIP_RED.search(x) or mode in ('skip', 'inv', 'inv0'): continue
            if cur is None: continue
            m = re.match(r'^((?:Salmo|SALMO|Cántico|Cantico|CÁNTICO)[^-:]*?)(?:\s*[-:]\s*|\s+(?=[A-ZÁÉÍÓÚÑ¿¡]{3}))(.*)$', x)
            if m and cur[0] in ('salmodia', 'ce'):
                cur[1].append(['ps', esc(m.group(1).strip().capitalize() if m.group(1).isupper() else m.group(1).strip())])
                if m.group(2).strip(): cur[1].append(['ti', esc(m.group(2).strip())])
            elif X.startswith('RESPONSORIO'): cur[1].append(['r', esc(re.sub(r'\s+', ' ', x))])
            elif X.startswith('LA PARTE QUE SIGUE') or X.startswith('SE PUEDEN'): cur[1].append(['r', esc(x)])
            else: cur[1].append(['ti', esc(x)])
            continue
        if t[0] in ('blank', 'hr'):
            if cur and cur[1] and cur[1][-1][0] != 'b': cur[1].append(['b', ''])
            continue
        pre, x = t[1], t[2].strip()
        if mode == 'inv0':
            if pre.startswith('Ant') and not any(k == 'antinv' for k, _ in segs): start('antinv', None); cur[1] = [['l', 'INVITATORIO', 'antinv'], ['a', esc(x)]]
            continue
        if mode == 'skip' or cur is None: continue
        if mode == 'inv':
            if pre.startswith('Ant'): cur[1] = [['l', 'INVITATORIO', 'antinv'], ['a', esc(x)]]
            continue
        if re.match(r'^Of La Tr', x): continue
        if hour == 'ol' and cur[0] == 'salmodia' and pre.startswith('V.') and not seen_ps:
            pass
        if hour == 'ol' and cur[0] == 'salmodia' and pre.startswith('V.'):
            start('verso', ['l', 'VERSÍCULO', 'verso'])
        if pre.startswith('Ant'): cur[1].append(['a', esc(x)])
        elif pre.startswith(('V.', 'R.')) or re.match(r'^[VR]\.\s', x): cur[1].append(['v', esc(x)])
        elif mode == 'read' or len(x) > 95: cur[1].append(['t', esc(x)])
        else: cur[1].append(['v', esc(x)])
    out = []
    for k, ps in segs:
        while ps and ps[-1][0] == 'b': ps.pop()
        if len(ps) > 1: out.append((k, ps))
    return out

P = []; santos = []
def add(p): P.append(p); return len(P) - 1
for cid, name, claves, rank, folder, v1 in CELEBS:
    base = os.path.join(SYNC, folder); mem = rank in ('M', 'm')
    s = add(['h', esc(name)]); h = {}
    def hour_block(hkey, label, segs):
        if not segs: return
        add(['hh', label]); a = len(P)
        for k, ps in segs:
            for p in ps: add(p)
        h[hkey] = [a, len(P)]
    ol = segments(os.path.join(base, 'oficio.htm'), 'ol')
    inv = [x for x in ol if x[0] == 'antinv']
    hour_block('inv', 'Invitatorio', inv)
    hour_block('ol', 'Oficio de lectura', [x for x in ol if x[0] != 'antinv' and not (mem and x[0] in NO_PROPIO_MEM['ol'])])
    for hk, f, lab in (('l', 'laudes.htm', 'Laudes'), ('v', 'visperas.htm', 'Vísperas')):
        sg = [x for x in segments(os.path.join(base, f), hk) if x[0] != 'antinv' and not (mem and x[0] in NO_PROPIO_MEM[hk])]
        hour_block(hk, lab, sg)
    if not mem:
        # Hora intermedia: himnos de cada hora, salmodia (del día o complementaria) y lo propio de Tercia, Sexta y Nona
        add(['hh', 'Hora intermedia']); a = len(P)
        hy = {}; rest = {}
        for f, lab in (('tercia.htm', 'Tercia'), ('sexta.htm', 'Sexta'), ('nona.htm', 'Nona')):
            sg = dict(segments(os.path.join(base, f), 'hi'))
            hy[lab] = sg.get('himno', [])[1:]; rest[lab] = [p for k in ('lb', 'oracion') for p in sg.get(k, [])]
        add(['l', 'HIMNO', 'himno'])
        for lab in ('Tercia', 'Sexta', 'Nona'):
            if hy[lab]: add(['r', lab]); [add(p) for p in hy[lab]]; add(['b', ''])
        add(['l', 'SALMODIA', 'salmodia'])
        add(['r', 'Salmodia complementaria.' if rank == 'S' else 'Salmos del día del Salterio.'])
        for lab, key in (('Tercia', 'tercia'), ('Sexta', 'sexta'), ('Nona', 'nona')):
            add(['l', lab, key]); [add(p) for p in rest[lab]]
        h['hi'] = [a, len(P)]
    if v1:
        sg = [x for x in segments(os.path.join(SYNC, v1, 'visperas.htm'), 'v') if x[0] != 'antinv']
        hour_block('v1', 'I vísperas', sg)
    santos.append({'n': name, 'md': '*', 'claves': claves, 'rango': rank, 'id': cid, 's': s, 'e': len(P), 'h': h, 'fuente': folder})
doc = {'formato': 'lh-libro/1', 'vol': 5, 'titulo': 'PROPIO NACIONAL (liturgiadelashoras.github.io)', 'p': P, 'sec': {}, 'santos': santos}
with open(OUT, 'w', encoding='utf8') as f: json.dump(doc, f, ensure_ascii=False, separators=(',', ':'))
for s in santos: print(f"{s['id']:16} {s['rango']} {' '.join(f'{k}:{b-a}' for k,(a,b) in s['h'].items())}")
print(len(P), 'párrafos')
