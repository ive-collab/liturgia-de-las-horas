"""Comprueba que ningún día tenga el Oficio de lectura sin primera o segunda lectura,
para todos los países y opciones. Uso: python3 audit.py <carpeta app> [desde] [hasta]
Requiere: pip install playwright && playwright install chromium (o Chrome instalado)."""
import sys, json, subprocess, time, os, shutil
from playwright.sync_api import sync_playwright
root = sys.argv[1]; a = sys.argv[2] if len(sys.argv) > 2 else '2025-01-01'; b = sys.argv[3] if len(sys.argv) > 3 else '2030-12-31'
port = '8791'
srv = subprocess.Popen([sys.executable, '-m', 'http.server', port, '-d', root], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
JS = r"""
({a, b}) => {
  const res = {}; const codes = ['', ...Object.keys(LH.countries())];
  for (const code of codes) {
    const t0 = LH.countryTransfers(code) || {};
    const S = { region: code, epiSun: !!t0.epiphanyToSunday, ascSun: !!t0.ascensionToSunday, corpusSun: !!t0.corpusToSunday, usarComun: true };
    const out = []; let n = 0;
    for (let tm = LH.fromIso(a); tm <= LH.fromIso(b); tm += LH.DAY) {
      const d = LH.day(tm, S);
      for (const o of d.options) {
        n++;
        let r; try { r = BOOK.compose(d, o, 'ol', S, null, null); } catch (e) { out.push(`${d.iso} ${o.name}: ERROR ${e}`); continue; }
        const ks = new Set(r.blocks.filter(x => x.idx && x.idx.length).map(x => x.k.replace(/\+$/, '')));
        const miss = ['l1', 'l2'].filter(k => !ks.has(k));
        if (miss.length) out.push(`${d.iso} ${o.name}: falta ${miss.join(', ')}`);
        for (const h of ['l', 'v']) { try { BOOK.compose(d, o, h, S, null, null); } catch (e) { out.push(`${d.iso} ${o.name} [${h}]: ERROR ${e}`); } }
      }
    }
    res[code || 'GENERAL'] = { comprobadas: n, problemas: out };
  }
  return res;
}"""
exe = shutil.which('google-chrome') or shutil.which('chromium')
try:
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=exe, args=['--no-sandbox']) if exe else p.chromium.launch()
        pg = br.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(f'http://localhost:{port}/index.html')
        pg.wait_for_function('typeof BOOK !== "undefined" && BOOK.loaded().length === 5', timeout=180000)
        res = pg.evaluate(JS, {'a': a, 'b': b})
        total = 0
        for k, v in res.items():
            total += len(v['problemas'])
            print(f"{k:8} {v['comprobadas']:6} opciones  {len(v['problemas'])} problemas")
            for x in v['problemas'][:10]: print('    ', x)
        print('Errores de la página:', errs or 'ninguno')
        br.close()
        sys.exit(1 if total or errs else 0)
finally:
    srv.kill()
