import re,html
def tokens(path):
    """Yield ('red',text) / ('line', kind, text) / ('blank',) from the site's HTML."""
    s=open(path,encoding='latin-1').read()
    s=s[s.find('id="cuerpo"'):]; s=s[s.find('>')+1:]
    s=re.sub(r'(?is)<script.*?</script>','',s)
    s=re.sub(r'\s+',' ',s)
    # mark color changes
    s=re.sub(r'(?i)<font color="#FF0000">','\x01R',s); s=re.sub(r'(?i)<font color="#000000">','\x01B',s)
    s=re.sub(r'(?i)</font>','\x01E',s)
    s=re.sub(r'(?i)<br\s*/?>','\x02',s); s=re.sub(r'(?i)<hr\s*/?>','\x02\x03\x02',s)
    s=re.sub(r'<[^>]+>','',s); s=html.unescape(s).replace('\xa0',' ')
    stack=['B']; buf=''; out=[]
    def flush():
        nonlocal buf
        if buf: out.append((stack[-1],buf)); buf=''
    i=0
    while i<len(s):
        c=s[i]
        if c=='\x01':
            flush(); t=s[i+1]
            if t in 'RB': stack.append(t)
            elif len(stack)>1: stack.pop()
            i+=2; continue
        buf+=c; i+=1
    flush()
    # split into lines keeping color segments
    lines=[[]]
    for col,txt in out:
        parts=txt.split('\x02')
        for n,p in enumerate(parts):
            if n: lines.append([])
            if p: lines[-1].append((col,p))
    res=[]
    for ln in lines:
        segs=[(c,t) for c,t in ln if t.strip()]
        if not segs: res.append(('blank',)); continue
        if any('\x03' in t for c,t in segs): res.append(('hr',)); continue
        txt=' '.join(t.strip() for c,t in segs)
        if all(c=='R' for c,t in segs): res.append(('red',txt))
        else:
            pre=' '.join(t.strip() for c,t in segs if c=='R') if segs[0][0]=='R' else ''
            res.append(('line',pre,txt))
    return res
