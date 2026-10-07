#!/usr/bin/env python3
from pathlib import Path
import re,subprocess,sys,tempfile,textwrap,hashlib
if len(sys.argv)<3: raise SystemExit('usage: verify_26778_embedded_glsl.py BASE CAND [--compiler PATH] [--out DIR]')
base=Path(sys.argv[1]); cand=Path(sys.argv[2]); compiler=None; out=None; i=3
while i<len(sys.argv):
 if sys.argv[i]=='--compiler': compiler=sys.argv[i+1]; i+=2
 elif sys.argv[i]=='--out': out=Path(sys.argv[i+1]); i+=2
 else: raise SystemExit('unknown arg '+sys.argv[i])
ROOT=Path(__file__).resolve().parent
IRIS=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
STACK=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
def vals(root,rel):
 text=(root/rel).read_text()
 return {m.group(1):textwrap.dedent(m.group(2)).strip('\n')+'\n' for m in re.finditer(r'(?:private\s+)?val\s+([A-Za-z0-9_]+)\s*=\s*"""(.*?)"""\.trimIndent\(\)',text,re.S)}
bv,cv=vals(base,IRIS),vals(cand,IRIS)
modified=sorted(n for n in set(bv)|set(cv) if bv.get(n)!=cv.get(n))
EXPECTED_DELTA=['bipolarColorTrust26769','phaseDilate26777','phaseRisk26777','seed']
if modified!=EXPECTED_DELTA: raise SystemExit(f'VGN embedded shader delta differs: {modified}')
for removed in ('phaseDilate26777','phaseRisk26777'):
 if removed not in bv or removed in cv: raise SystemExit(f'expected 26777 shader restoration/removal mismatch: {removed}')
common=cv['common']; shaders={n:cv[n].replace('$common',common) for n in ('bipolarColorTrust26769','seed')}
sv=vals(cand,STACK)
if 'EDGE_FALSE_COLOR_SUPPRESSOR_26778' not in sv: raise SystemExit('26778 suppressor missing')
edge=sv['EDGE_FALSE_COLOR_SUPPRESSOR_26778']; shaders['EDGE_FALSE_COLOR_SUPPRESSOR_26778']=edge
# Exact Claude reference fidelity after only approved GLES3.1/workgroup changes + requested telemetry.
ref=(ROOT/'26778_CLAUDE_EDGE_FALSE_COLOR_REFERENCE.comp').read_text().strip('\n')+'\n'
expected=ref.replace('#version 320 es','#version 310 es',1)
expected=expected.replace('layout(local_size_x = 16, local_size_y = 16) in;','layout(local_size_x = 8, local_size_y = 8) in;',1)
expected=expected.replace('layout(binding = 0) uniform sampler2D uSrc;               // linear RGBA16F','uniform sampler2D uSrc;                                    // linear RGBA16F',1)
expected=expected.replace('layout(rgba16f, binding = 1) writeonly uniform highp image2D uDst;','layout(rgba16f, binding = 1) writeonly uniform highp image2D uDst;\nlayout(std430, binding = 0) buffer Iris26778Stats { uint gateGt05; uint blendGt05Pass1; uint blendGt05Pass2; };\nuniform int uStatsPass;',1)
expected=expected.replace('  float gate = smoothstep(uContrastLo, uContrastHi, contrast);','  float gate = smoothstep(uContrastLo, uContrastHi, contrast);\n  if (uStatsPass == 1 && gate > 0.5) atomicAdd(gateGt05, 1u);',1)
expected=expected.replace('  float w = gate * smoothstep(uOutlierLo, uOutlierHi, dev);','  float w = gate * smoothstep(uOutlierLo, uOutlierHi, dev);\n  if (w > 0.5) {\n    if (uStatsPass == 1) atomicAdd(blendGt05Pass1, 1u);\n    else if (uStatsPass == 2) atomicAdd(blendGt05Pass2, 1u);\n  }',1)
if edge!=expected: raise SystemExit('26778 suppressor differs from Claude reference beyond approved ES3.1/workgroup/sampler compatibility + telemetry')
for token in ('clipMask','isClipped','periodic2Px','phaseRisk','phaseDilate','uClip','uPeriodic'):
 if token in edge: raise SystemExit('forbidden gate introduced into Claude suppressor: '+token)
if 'rgb1 *= (y1 > 1e-8) ? (y0 / y1) : 1.0;' not in edge or 'imageStore(uDst, p, vec4(rgb1, c0.a));' not in edge: raise SystemExit('luma/alpha invariant missing')
# Runtime-expanded static and reserved identifier scan.
decl=re.compile(r'\b(?:void|bool|int|uint|float|vec[234]|ivec[234]|uvec[234]|mat[234]|sampler\w*|usampler\w*|image\w*|uimage\w*)\s+([A-Za-z_]\w*)')
for name,src in shaders.items():
 if '$' in src: raise SystemExit(f'unexpanded Kotlin interpolation remains in {name}')
 if not src.startswith('#version 310 es'): raise SystemExit(f'{name}: wrong version')
 bad=[]
 for ident in decl.findall(src):
  if ident.startswith('gl_') or '__' in ident or (len(ident)>1 and ident[0]=='_' and ident[1].isupper()): bad.append(ident)
 if bad: raise SystemExit(f'{name}: reserved identifiers declared: {sorted(set(bad))}')
 print(f'PASS 26778 reserved-identifier scan {name}: declarations={len(decl.findall(src))} sha256={hashlib.sha256(src.encode()).hexdigest()}')
for marker,name in [
 ('IRIS_26776_RESIDUAL_PERIODIC_CHROMA_OWNER','bipolarColorTrust26769'),
 ('uPhysicalPreVgnValid','seed'),
 ('directionDomain=clamp(linearRgb/physicalMagnitude','seed'),
 ('No clipping test and no periodicity test.','EDGE_FALSE_COLOR_SUPPRESSOR_26778'),
 ('vec4(rgb1, c0.a)','EDGE_FALSE_COLOR_SUPPRESSOR_26778'),
]:
 if marker not in shaders[name]: raise SystemExit(f'{name}: marker missing: {marker}')
if out:
 out.mkdir(parents=True,exist_ok=True)
 for n,s in shaders.items(): (out/f'{n}.comp').write_text(s)
if compiler:
 c=Path(compiler)
 if not c.exists(): raise SystemExit('compiler missing')
 with tempfile.TemporaryDirectory(prefix='iris26778_glsl_') as td:
  td=Path(td)
  for n,s in shaders.items():
   f=td/f'{n}.comp'; f.write_text(s)
   p=subprocess.run([str(c),'-S','comp',str(f)],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
   print(p.stdout,end='')
   if p.returncode: raise SystemExit(f'glslang failed: {n}')
   print(f'PASS 26778 pinned real glslang compile: {n}')
print('PASS 26778 Claude reference exact after approved ES3.1/workgroup/sampler compatibility + telemetry')
print('PASS 26778 exact candidate runtime-expanded shader set compiled/scanned: EDGE_FALSE_COLOR_SUPPRESSOR_26778,bipolarColorTrust26769,seed; 26777 phase shaders removed by explicit 26776 guard restoration')
