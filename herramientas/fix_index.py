"""Re-index day headings the importer skipped (e.g. 'LUNES DE LA XXXIV SEMANA...')."""
import json, re, sys
HH = {'Vísperas':'v','II vísperas':'v','I vísperas':'v1','Invitatorio':'inv','Oficio de lectura':'ol','Laudes':'l','Hora intermedia':'hi'}
DOW = {'DOMINGO':0,'LUNES':1,'MARTES':2,'MIÉRCOLES':3,'MIERCOLES':3,'JUEVES':4,'VIERNES':5,'SÁBADO':6,'SABADO':6}
ROM = {'I':1,'II':2,'III':3,'IV':4,'V':5,'VI':6,'VII':7,'VIII':8,'IX':9,'X':10}
def roman(s):
    v=0;i=0
    vals={'I':1,'V':5,'X':10,'L':50}
    for j,ch in enumerate(s):
        x=vals[ch]; v+= -x if j+1<len(s) and vals[s[j+1]]>x else x
    return v
def ranges(P, s, e):
    hs=[i for i in range(s+1,e) if P[i][0]=='hh']
    out={}
    for n,i in enumerate(hs):
        k=HH.get(re.sub('<[^>]+>','',P[i][1]).strip())
        if k: out[k]=[i+1, hs[n+1] if n+1<len(hs) else e]
    return out
def key_for(head):
    m=re.match(r'^(\S+)\s+(?:DE LA\s+)?([IVXL]+)\s+(SEMANA DEL TIEMPO ORDINARIO|DE PASCUA|SEMANA DE PASCUA)',head)
    if not m: return None
    w=DOW.get(m.group(1)); n=roman(m.group(2))
    season='ordinario' if 'ORDINARIO' in m.group(3) else 'pascua'
    return f'T:{season}/{n}/{w}'
def main(path, check=False):
    d=json.load(open(path,encoding='utf8')); P=d['p']; sec=d['sec']
    starts=sorted(s['s'] for s in sec.values())
    # self-test: rebuilt ranges must match the importer's for existing T: sections
    bad=0
    for k,s in sec.items():
        if k.startswith('T:') and s.get('h'):
            if ranges(P,s['s'],s['e'])!=s['h']: bad+=1
    changed=[]
    for i,p in enumerate(P):
        if p[0]!='h' or i in starts: continue
        k=key_for(re.sub('<[^>]+>','',p[1]).strip())
        if not k: continue
        e=min([x for x in starts if x>i]+[n for n in range(i+1,len(P)) if P[n][0]=='h'][:1]+[len(P)])
        h=ranges(P,i,e)
        if not h: continue
        old=sec.get(k)
        if old and old.get('h'): continue           # a real section already exists
        sec[k]={'s':i,'e':e,'n':re.sub('<[^>]+>','',p[1]).strip(),'h':h}
        changed.append((k,old and {'s':old['s'],'e':old['e']},sec[k]))
    if not check and changed:
        with open(path,'w',encoding='utf8') as f: json.dump(d,f,ensure_ascii=False,separators=(',',':'))
    return bad, changed
if __name__=='__main__':
    for p in sys.argv[1:]:
        bad,ch=main(p, check='--check' in sys.argv)
        print(p,'range-mismatches vs importer:',bad)
        for c in ch: print('  ',c[0],'replaced stub' if c[1] else 'added',c[2]['s'],c[2]['e'],c[2]['h'])
