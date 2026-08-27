#!/usr/bin/env python3
from pathlib import Path
import re, sys
if len(sys.argv)!=3: raise SystemExit('usage: extract_26549_vgn_shaders.py KOTLIN OUTDIR')
s=Path(sys.argv[1]).read_text()
out=Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
def grab(name, private=False):
    pat=(r'private val ' if private else r'val ')+re.escape(name)+r' = """\n(.*?)\n    """\.trimIndent\(\)'
    m=re.search(pat,s,re.S)
    if not m: raise SystemExit('missing shader string '+name)
    # Kotlin trimIndent: remove common leading 8 spaces from shader bodies.
    lines=m.group(1).splitlines()
    nonempty=[len(x)-len(x.lstrip()) for x in lines if x.strip()]
    indent=min(nonempty) if nonempty else 0
    return '\n'.join(x[indent:] if len(x)>=indent else '' for x in lines)+'\n'
common=grab('common',private=True)
for name in ['directionalSmooth','iirRgb']:
    text=grab(name).replace('$common',common.rstrip('\n'))
    if '$' in text: raise SystemExit('unexpanded Kotlin interpolation in '+name)
    p=out/(name+'.comp')
    p.write_text(text)
    print(p)
