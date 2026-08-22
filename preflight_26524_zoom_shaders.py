#!/usr/bin/env python3
from __future__ import annotations
import argparse, subprocess, tempfile
from pathlib import Path

SHADERS=[
'app/src/main/assets/shaders/preview/main_fs.glsl',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
]
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',required=True,type=Path)
    ap.add_argument('--validator',default='glslangValidator')
    a=ap.parse_args()
    with tempfile.TemporaryDirectory(prefix='iris26524_glsl_') as td:
        td=Path(td)
        for i,rel in enumerate(SHADERS):
            p=a.root/rel
            if not p.is_file(): raise SystemExit('missing '+rel)
            body=p.read_text().replace('\r\n','\n')
            material='#version 300 es\n'+body
            f=td/f'zoom_{i}.frag'
            f.write_text(material)
            cp=subprocess.run([a.validator,'-S','frag',str(f)],
                              stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            if cp.returncode!=0:
                print(cp.stdout)
                raise SystemExit('glslang failed '+rel)
            print('PASS: glslang '+rel)
    print('PASS: all 26524 changed GLSL programs compile')

if __name__=='__main__':
    main()
