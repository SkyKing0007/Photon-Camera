#!/usr/bin/env python3
from pathlib import Path
import re,hashlib,sys,tempfile,subprocess,shutil,argparse
ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('base'); ap.add_argument('cand'); ap.add_argument('--compiler'); ap.add_argument('--emit-hashes'); a=ap.parse_args()
pkg=Path(a.root); base=Path(a.base); root=Path(a.cand); out=Path(tempfile.mkdtemp(prefix='i26741_expanded_'))
vrel=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
srel=Path('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
def raw_triple(rel,name):
 s=(root/rel).read_text(); m=re.search(r'(?:private\s+)?val\s+'+re.escape(name)+r'(?:\s*:\s*String)?\s*=\s*"""(.*?)"""\.trimIndent\(\)',s,re.S)
 if not m: raise AssertionError(f'missing triple {name}')
 return m.group(1)
def trim(v):
 lines=v.replace('\r\n','\n').replace('\r','\n').split('\n')
 if lines and not lines[0].strip(): lines=lines[1:]
 if lines and not lines[-1].strip(): lines=lines[:-1]
 nb=[l for l in lines if l.strip()]; ind=min((len(l)-len(l.lstrip()) for l in nb),default=0)
 return '\n'.join(l[ind:] if l.strip() else '' for l in lines)
def runtime(rel,name):
 raw=raw_triple(rel,name)
 if '$common' in raw: raw=raw.replace('$common',trim(raw_triple(rel,'common')))
 if '$wronskiSensorOutputBody26739' in raw: raw=raw.replace('$wronskiSensorOutputBody26739',trim(raw_triple(srel,'wronskiSensorOutputBody26739')))
 x=trim(raw); assert '$' not in x,(name,'unresolved interpolation'); return x
def once(s,o,n,label):
 assert s.count(o)==1,(label,s.count(o)); return s.replace(o,n,1)
def true2x_26741():
 src=runtime(srel,'true2xGuideRender26568')
 src=once(src,
  'float detailConfidence = confidence * mix(1.0, materialSupportGate, materialBoundary);',
  '/* IRIS_26741_TRUE2X_SHAPE_STABILITY_AND_FAIL_CLOSED_PUBLICATION */\n            float blockShapeTrust26741=maxAbsDetail>1.0e-6?shapeScale:1.0;\n            float materialShapeTrust26741=materialMaxAbs>1.0e-6?materialShapeScale:1.0;\n            float shapeTrust26741=mix(blockShapeTrust26741,materialShapeTrust26741,materialBoundary);\n            float reconstructionConfidence26741=clamp(confidence*shapeTrust26741,0.0,1.0);\n            float publicationAuthority26741=irisSmooth01((reconstructionConfidence26741-0.16)/0.44);\n            float detailConfidence=reconstructionConfidence26741*publicationAuthority26741*\n                mix(1.0,materialSupportGate,materialBoundary);',
  'true2x detail-confidence')
 src=once(src,
  'else if (confidence >= 0.50) reasonClass = 2;\n    else if (confidence > 0.02) reasonClass = 1;',
  'else if (reconstructionConfidence26741 >= 0.50 && publicationAuthority26741 >= 0.50) reasonClass = 2;\n    else if (publicationAuthority26741 > 0.02) reasonClass = 1;',
  'true2x diagnostics')
 return src
reserved=set('attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 vec2 vec3 vec4 ivec2 ivec3 ivec4 uvec2 uvec3 uvec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint lowp mediump highp precision struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 filter sizeof cast namespace using row_major'.split())
typepat=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w*|[iu]?image\w*|atomic_uint|void)'
def scan(fn,src):
 clean=re.sub(r'/\*.*?\*/',' ',src,flags=re.S); clean=re.sub(r'//.*',' ',clean)
 ids=re.findall(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\b',clean)+re.findall(r'\bstruct\s+([A-Za-z_]\w*)\b',clean)
 bad=sorted(set(ids)&reserved); impl=sorted(set(x for x in ids if '__' in x or x.startswith('gl_')))
 assert not bad,(fn,'reserved',bad); assert not impl,(fn,'impl',impl); assert clean.count('{')==clean.count('}'),(fn,'brace mismatch'); assert '#import' not in clean,(fn,'import remains')
specs=[
(vrel,'seed','26741_vgn_seed.comp','comp'),
(vrel,'universalAdaptiveColor26561','26741_universal_adaptive_color.comp','comp'),
(vrel,'localMedian','26741_local_median.comp','comp'),
(None,None,'26741_true2x_guide_render.frag','frag'),
]
expanded={}
for rel,name,fn,stage in specs:
 shader=true2x_26741() if rel is None else runtime(rel,name); scan(fn,shader); expanded[fn]=shader
 if rel is None:
  for t in ['IRIS_26741_TRUE2X_SHAPE_STABILITY_AND_FAIL_CLOSED_PUBLICATION','shapeTrust26741','reconstructionConfidence26741','publicationAuthority26741','uNativeVgnGuide','uPhaseOccupancy','uTemporalLumaStats']:
   assert t in shader,(fn,t)
 q=out/fn; q.write_text(shader)
 if a.compiler:
  cp=subprocess.run([str(Path(a.compiler)),'-S',stage,str(q)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
  if cp.returncode: print(cp.stdout); raise SystemExit(f'glslang FAIL {fn}')
# Candidate semantic markers inside exact expanded shaders.
seed=expanded['26741_vgn_seed.comp']; final=expanded['26741_universal_adaptive_color.comp']; med=expanded['26741_local_median.comp']
for t in ['IRIS_26741_HEADROOM_QUALIFIED_REAL_COLOR_PROOF','physicalHeadroomColorContinuation26741']:
 assert t in seed+final,t
for t in ['IRIS_26741_CLIPPED_FLATTENED_HIGHLIGHT_NEUTRAL_AUTHORITY','clippedFlattenedNeutralAuthority26741 = invalidHighlightCenter','IRIS_26741_STRONG_ACHROMATIC_FINE_STRUCTURE_AUTHORITY']:
 assert t in final,t
for t in ['IRIS_26741_INVALID_HIGHLIGHT_NEUTRAL_DONOR_ONLY','centerNeutralStructure||centerHighlightInvalid']:
 assert t in med,t
for forbidden in ['barcode','fontDetector','textDetector','semanticClass']:
 assert forbidden.lower() not in '\n'.join(expanded.values()).lower(),forbidden
# Asset shader universe remains byte invariant; modified runtime shaders are Kotlin carriers.
def ah(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app/src/main/assets/shaders').rglob('*') if p.is_file()}
assert len(ah(base))==len(ah(root))==271 and ah(base)==ah(root)
hashes={fn:hashlib.sha256(src.encode()).hexdigest() for fn,src in expanded.items()}
if a.emit_hashes:
 q=Path(a.emit_hashes); q.write_text(''.join(f'{hashes[n]}  {n}\n' for n in sorted(hashes)))
else:
 expected={}
 for l in (pkg/'26741_RUNTIME_EXPANDED_CANDIDATE.sha256').read_text().splitlines():
  if l.strip(): h,n=l.split(None,1); expected[n.strip()]=h
 assert expected==hashes,(expected,hashes)
shutil.rmtree(out,ignore_errors=True)
print(f'PASS 26741 shaders: exact 4 changed/new runtime-expanded variants; reserved/structure clean; asset-shader universe 271 invariant; real_compiler={bool(a.compiler)}')
