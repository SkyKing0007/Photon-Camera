#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,subprocess,sys,tempfile,textwrap
if len(sys.argv) not in (3,5): raise SystemExit('usage: verify_26771_shaders.py BASE26770 CAND26771 [--compiler glslangValidator]')
base,cand=map(Path,sys.argv[1:3]); compiler=None
if len(sys.argv)==5:
    assert sys.argv[3]=='--compiler'; compiler=sys.argv[4]
def H(r):
    return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app/src/main/assets/shaders').rglob('*') if p.is_file()}
a,b=H(base),H(cand); assert len(a)==len(b)==271 and a==b
print('PASS 26771 complete 271-file asset shader universe byte-identical to successful 26770')
# Embedded VGN compute carrier is also protected unchanged.
post=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
assert (base/post).read_bytes()==(cand/post).read_bytes()
print('PASS 26771 embedded VGN shader carrier byte-identical to successful 26770')
# Keep the exact 26770 inherited glslang checkpoint live by compiling the same final trust/render/gainmap sources.
def raw(src,name):
    m=re.search(r'\b(?:private\s+)?val\s+'+re.escape(name)+r'\s*=\s*"""(.*?)"""\.trimIndent\(\)',src,re.S)
    assert m,name
    return textwrap.dedent(m.group(1)).lstrip('\n')
def asset(root,rel):
    src=(root/rel).read_text(); assert '#version' not in src and '#import' not in src and '#define' not in src
    return '#version 310 es\n\n#line 1\n'+src
reserved=set('attribute const uniform varying layout centroid flat smooth noperspective break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant discard return mat2 mat3 mat4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision sampler2D usampler2D uimage2D struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output sizeof cast namespace using row_major'.split())
typepat=r'(?:float|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234]|sampler2D|usampler2D|uimage2D)'
def scan(label,shader,stage):
    assert shader.startswith('#version 310 es\n'),label
    t=re.sub(r'/\*.*?\*/|//[^\n]*',' ',shader,flags=re.S); names=[]
    for m in re.finditer(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\s*(?:[=;,\[])',t): names.append(m.group(1))
    for m in re.finditer(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\s*\(',t): names.append(m.group(1))
    bad=sorted({n for n in names if n in reserved or n.startswith('__')}); assert not bad,(label,bad)
    assert shader.count('{')==shader.count('}') and shader.count('(')==shader.count(')'),label
    print(f'PASS 26771 reserved-identifier/structure scan inherited {label}: {len(names)} identifiers')
    if compiler:
        with tempfile.TemporaryDirectory() as td:
            ext='comp' if stage=='comp' else 'frag'; f=Path(td)/(label.replace('/','_')+'.'+ext); f.write_text(shader)
            r=subprocess.run([compiler,'-S',stage,str(f)],text=True,capture_output=True)
            if r.returncode: raise SystemExit(label+'\n'+r.stdout+r.stderr)
        print(f'PASS 26771 pinned real glslang compile inherited runtime-expanded {label}')
bs=(cand/post).read_text(); scan('candidate26771/bipolarColorTrust26769','#version 310 es\n'+raw(bs,'bipolarColorTrust26769'),'comp')
for rel in [Path('app/src/main/assets/shaders/motionv2/render.glsl'),Path('app/src/main/assets/shaders/motionv2/gainmap.glsl')]:
    scan('candidate26771/'+rel.name,asset(cand,rel),'frag')
print('PASS 26771 shader scope: no runtime GLSL changes; successful 26770 shader owners preserved')
