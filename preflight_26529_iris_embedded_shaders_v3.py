#!/usr/bin/env python3
from __future__ import annotations
import argparse,re,subprocess,tempfile,sys
from pathlib import Path

FILES={
 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt': {
   'mergeRgb':'frag','normalizeRgb16':'frag','copyRgb16ToFloat':'comp',
 },
 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt': {
   'seed':'comp','localClamp':'comp','localMedian':'comp','directionalSmooth':'comp',
   'restoreDirection':'comp','iirRgb':'comp','calculateError':'comp','iirError':'comp',
   'blendChroma':'comp','finalCameraRgb':'comp',
 },
}

def extract(src,name):
    m=re.search(r'\b(?:private\s+)?val\s+'+re.escape(name)+r'\s*=\s*"""(.*?)"""(?:\.trimIndent\(\))?',src,re.S)
    if not m: raise RuntimeError(f'missing shader string {name}')
    return m.group(1).strip()+"\n"

def resolve(src,shader):
    # Resolve simple Kotlin $foo interpolation used by the Iris-owned postprocessor common block.
    for _ in range(8):
        refs=re.findall(r'\$([A-Za-z_][A-Za-z0-9_]*)',shader)
        if not refs: return shader
        changed=False
        for ref in sorted(set(refs)):
            try: val=extract(src,ref)
            except RuntimeError: continue
            shader=shader.replace('$'+ref,val.rstrip())
            changed=True
        if not changed: break
    refs=re.findall(r'\$([A-Za-z_][A-Za-z0-9_]*)',shader)
    if refs: raise RuntimeError(f'unresolved Kotlin interpolation: {sorted(set(refs))}')
    return shader

def compile_one(validator,name,stage,source):
    with tempfile.TemporaryDirectory() as td:
        ext='.frag' if stage=='frag' else '.comp'; p=Path(td)/(name+ext)
        p.write_text(source)
        cmd=[validator,'-S',stage,str(p)]
        r=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        if r.returncode!=0: raise RuntimeError(f'{name} failed:\n{r.stdout}')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); ap.add_argument('--validator',default='glslangValidator'); a=ap.parse_args()
    root=Path(a.root); total=0
    for rel,names in FILES.items():
        src=(root/rel).read_text()
        for name,stage in names.items():
            shader=resolve(src,extract(src,name))
            compile_one(a.validator,name,stage,shader); total+=1
    print(f'PASS: 26529 V3 embedded shader preflight compiled {total} Iris-owned shaders')
if __name__=='__main__':
    try: main()
    except Exception as e:
        print('ERROR:',e,file=sys.stderr); sys.exit(2)
