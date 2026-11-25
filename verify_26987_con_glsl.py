#!/usr/bin/env python3
"""Extract exact reachable C ON static shaders, and verify their sealed inventory."""
import argparse,hashlib,json,re,textwrap,pathlib,importlib.util
R=pathlib.Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--root',default=str(R/'app'));p.add_argument('--inventory',action='store_true');p.add_argument('--emit');o=p.parse_args()
root=pathlib.Path(o.root)/'src/main';k=root/'java/com/hinnka/mycamera/processor';j=root/'java/com/particlesdevs/photoncamera';a=root/'assets'
sha=lambda s:hashlib.sha256(s.encode()).hexdigest();entries=[]
def add(name,source,loc):
 assert source.startswith(('#version 300 es','#version 310 es')),(name,source[:100]);assert not re.search(r'\$\{|\$\w',source),name
 entries.append(dict(file=name,source=source,location=loc.relative_to(root).as_posix(),hash=sha(source)))
def lit(p,n):
 m=re.search(r'\bval '+re.escape(n)+r'\s*=\s*"""(.*?)"""\.trimIndent\(\)',p.read_text(),re.S);assert m,(p,n);return textwrap.dedent(m[1]).strip('\n')
p=k/'GlesGraphicsShader.kt';v=textwrap.dedent(re.search(r'return """(.*?)"""\.trimIndent\(\)',p.read_text(),re.S)[1]).strip('\n').replace('$version','300');add('core.vert',v,p)
for f,n in [('GlesIris26983COnGpuMerge.kt','lensShadeShader'),('GlesIris26983COnGpuMerge.kt','iris26876DerivedGuideShader'),('GlesIris26983COnColorContract.kt','applyAmazeWbForLabFcc'),('GlesIris26983COnRawLensMedian.kt','shader'),('GlesIris26983COnSmoothWhite.kt','shader')]:
 p=k/f;add(f.removesuffix('.kt')+'_'+n+'.frag',lit(p,n),p)
p=k/'GlesIris26983COnGpuSharpest.kt';add('sharp.vert',lit(p,'vertex'),p);add('sharp.frag',lit(p,'fragment'),p)
lab=a/'iris26983/con/lab';common=(lab/'lab_defringe_common.glsl').read_text()
for p in sorted(lab.glob('*.comp')):
 raw=p.read_text();assert raw.count('#include "lab_defringe_common.glsl"')==1;add(p.name,raw.replace('#include "lab_defringe_common.glsl"',common),p)
p=j/'processing/ultrahdr/Iris26983COnGpuFinalRenderer.java';v=re.search(r'private static final String VERT\s*=\s*(.*?);\s*\n',p.read_text(),re.S)[1];v=''.join(json.loads(x) for x in re.findall(r'"(?:[^"\\]|\\.)*"',v));add('final.vert',v,p)
p=a/'shaders/iris26983/con_fused_final_p3_gain.frag';add('final.frag',p.read_text(),p)
p=a/'shaders/iris26983/con_26986_rawlens_cleanup.frag';add('rawLensCleanup.frag',p.read_text(),p)
assert len(entries)==14
# Preserve all dynamically assembled post shader source copies; no pretend compile of templates.
records=json.loads((R/'26987_post_copy_records.json').read_text());shaders=[]
for row in records['copies']:
 if row['copy'].endswith('.glsl'):
  name=row['copy'];src=root/name;orig=root/row['source'];assert src.read_bytes()==orig.read_bytes();shaders.append({'file':name,'sha256':hashlib.sha256(src.read_bytes()).hexdigest()})
assert len(shaders)==15,len(shaders)
manifest={'static_count':len(entries),'static':[dict((k,v) for k,v in e.items() if k!='source') for e in entries],'dynamic_post_source_copies':shaders}
f=R/'26987_CON_SHADER_INVENTORY.json'
if o.inventory:f.write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
else:assert json.loads(f.read_text())==manifest,'C ON shader source inventory mismatch'
if o.emit:
 out=pathlib.Path(o.emit);out.mkdir(parents=True,exist_ok=True)
 for e in entries:(out/e['file']).write_text(e['source'])
 (out/'COMPILATION_METADATA.json').write_text(json.dumps(manifest['static'],indent=2))
print('PASS 14 exact static C ON GLSL stages; 15 exact post source copies (dynamic runtime compilation requires device)')
