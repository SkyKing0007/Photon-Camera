#!/usr/bin/env python3
from pathlib import Path
import argparse,re,subprocess,tempfile

def need(x,msg):
    if not x: raise SystemExit('FAIL: '+msg)
def triple(text,name):
    m=re.search(r'(?:private\s+)?val\s+'+re.escape(name)+r'\s*=\s*"""(.*?)"""\.trimIndent\(\)',text,re.S)
    need(m is not None,'missing '+name)
    return m.group(1).strip()+"\n"
def compile_shader(validator,source,stage,label):
    need(source.startswith('#version '),label+' #version is not first byte')
    with tempfile.TemporaryDirectory(prefix='iris26530v13_glsl_') as td:
        p=Path(td)/(label+'.'+('frag' if stage=='frag' else 'comp'))
        p.write_text(source)
        cp=subprocess.run([validator,'-S',stage,str(p)],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        print(cp.stdout,end='')
        need(cp.returncode==0,'GLSL compile '+label)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); ap.add_argument('--validator',required=True); a=ap.parse_args()
    root=Path(a.root)
    sh=(root/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt').read_text()
    pp=(root/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt').read_text()
    strength=triple(sh,'strengthAlignment')
    common=triple(pp,'common')
    seed=triple(pp,'seed').replace('$common',common.rstrip())
    need('uniform sampler2D uAlignment;' in strength and 'uFlow' not in strength,'strength shader is not final Bayer alignment')
    need('directionMomentAt' not in seed and 'structureScale' not in seed and 'g[i]=rgbGradient' in seed,'seed still uses c317 direction moment')
    compile_shader(a.validator,strength,'frag','v13_strength_alignment')
    compile_shader(a.validator,seed,'comp','v13_rgb_direction_seed')
    print('PASS: 26530 V1.3 final-Bayer-alignment + RGB-direction shaders compile')
if __name__=='__main__': main()
