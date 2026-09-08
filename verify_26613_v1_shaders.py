#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,re,subprocess,sys,textwrap
if len(sys.argv)<4 or sys.argv[3]!='--out': raise SystemExit('usage: verify_26613_v1_shaders.py BASE CAND --out OUT [--compiler PATH]')
B=Path(sys.argv[1]); C=Path(sys.argv[2]); O=Path(sys.argv[4]); O.mkdir(parents=True,exist_ok=True)
compiler=None
if len(sys.argv)>=7 and sys.argv[5]=='--compiler': compiler=sys.argv[6]
def write(name,src,stage):
    p=O/f'{name}.{stage}'; p.write_text(src); return p
prefix='#version 300 es\n#line 1\n'
spec=[]
for rel,name in [('app/src/main/assets/shaders/motionv2/render.glsl','motionv2_render_26613_fixed_domain'),('app/src/main/assets/shaders/motionv2/gainmap.glsl','motionv2_gainmap_26613_clean_master')]:
    s=(C/rel).read_text(); assert '#version' not in s and '#import' not in s; spec.append((name,prefix+s,'frag'))
a=(C/'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl').read_text(); assert '#version' not in a and '#import' not in a
spec.append(('adaptive_26613_fixed_domain',prefix+a,'frag')); spec.append(('adaptive_26613_fixed_domain_calibrated',prefix+a.replace('#define CALIBRATED_PROFILE 0','#define CALIBRATED_PROFILE 1'),'frag'))
kt=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt').read_text()
m=re.search(r'val universalAdaptiveColor26561 = """\n(.*?)\n\s*"""\.trimIndent\(\)',kt,re.S); assert m
# Kotlin trimIndent semantics for this uniformly-indented GLSL block.
ks=textwrap.dedent(m.group(1)).lstrip('\n')+'\n'; assert ks.startswith('#version 310 es\n'); spec.append(('sabre_support_postvgn_26613',ks,'comp'))
cpp=(C/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text(); m=re.search(r'kIris26571PublicationCompute=R"GLSL\((.*?)\)GLSL";',cpp,re.S); assert m
cs=m.group(1).lstrip('\n'); assert cs.startswith('#version 310 es\n'); spec.append(('true2x_publication_26613',cs,'comp'))
# Targeted complete identifier gate for prior real compiler failures. Comments are removed first.
reserved={'sample','coherent'}
for name,src,stage in spec:
    clean=re.sub(r'/\*.*?\*/',' ',src,flags=re.S); clean=re.sub(r'//.*',' ',clean)
    # declarations/functions whose identifier itself is a reserved prior-failure token.
    for bad in reserved:
        pat=rf'\b(?:float|int|uint|bool|vec[234]|ivec[234]|uvec[234]|mat[234]|sampler\w*|image\w*|uimage\w*|void)\s+{bad}\b'
        assert not re.search(pat,clean), f'{name}: reserved identifier {bad}'
paths=[]
for name,src,stage in spec: paths.append((write(name,src,stage),stage,name))
lines=[]
for p,stage,name in paths:
    lines.append(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}')
(O/'V1_26613_RUNTIME_EXPANDED_SHADERS.sha256').write_text('\n'.join(lines)+'\n')
results=[]
for p,stage,name in paths:
    status='STATIC_PASS'
    if compiler:
        cp=subprocess.run([compiler,'-S',stage,str(p)],capture_output=True,text=True)
        if cp.returncode!=0: raise SystemExit(f'GLSL FAIL {name}\n{cp.stdout}\n{cp.stderr}')
        status='REAL_GLSLANG_PASS'
    results.append({'name':name,'stage':stage,'file':p.name,'status':status})
(O/'V1_26613_SHADER_VERIFICATION.json').write_text(json.dumps({'count':len(results),'compiler':compiler,'results':results},indent=2,sort_keys=True)+'\n')
print(f'PASS 26613 runtime-expanded shader extraction/reserved scan variants={len(results)} real_compiler={bool(compiler)}')
