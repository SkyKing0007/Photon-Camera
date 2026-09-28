#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,re,textwrap,subprocess,tempfile,shutil
ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('base'); ap.add_argument('cand'); ap.add_argument('--compiler'); a=ap.parse_args()
pkg=Path(a.root); base=Path(a.base); cand=Path(a.cand); out=Path(tempfile.mkdtemp(prefix='i26729_expanded_'))
specs=[
('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt','seed','26729_vgn_seed.comp','comp',True),
('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt','localMedian','26729_vgn_local_median.comp','comp',True),
('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt','iirRgb','26729_vgn_iir_rgb.comp','comp',True),
('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt','universalAdaptiveColor26561','26728_universal_adaptive_color.comp','comp',False),
('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt','restoreExtendedHdrAfterVgn','26728_restore_extended_hdr_after_vgn.frag','frag',False)]
def triple(root,rel,name):
 s=(root/rel).read_text(); m=re.search(r'val\s+'+re.escape(name)+r'(?:\s*:\s*String)?\s*=\s*"""\n(.*?)\n\s*"""\.trimIndent\(\)',s,re.S); assert m,name; return textwrap.dedent(m.group(1))
def load_manifest(n):
 d={}
 for line in (pkg/n).read_text().splitlines():
  if line.strip(): h,p=line.split(None,1); d[p.strip()]=h
 return d
def asset_hashes(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'app/src/main/assets/shaders').rglob('*') if p.is_file()}
assert len(asset_hashes(base))==len(asset_hashes(cand))==271 and asset_hashes(base)==asset_hashes(cand)
reserved=set('attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 filter sizeof cast namespace using row_major'.split())
typepat=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w*|[iu]?image\w*|atomic_uint|void)'
bm=load_manifest('26729_RUNTIME_EXPANDED_BASE.sha256'); cm=load_manifest('26729_RUNTIME_EXPANDED_CANDIDATE.sha256'); assert len(bm)==len(cm)==15
for rel,name,fn,stage,modified in specs:
 bs=triple(base,rel,name); cs=triple(cand,rel,name)
 assert hashlib.sha256(bs.encode()).hexdigest()==bm[fn],('base shader hash',fn)
 assert hashlib.sha256(cs.encode()).hexdigest()==cm[fn],('candidate shader hash',fn)
 assert (bs!=cs)==modified,('modified expectation',fn)
 clean=re.sub(r'/\*.*?\*/',' ',cs,flags=re.S); clean=re.sub(r'//.*',' ',clean)
 ids=re.findall(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\b',clean)+re.findall(r'\bstruct\s+([A-Za-z_]\w*)\b',clean)
 bad=sorted(set(ids)&reserved); impl=sorted(set(x for x in ids if '__' in x or x.startswith('gl_')))
 assert not bad and not impl,(fn,bad,impl); assert clean.count('{')==clean.count('}'),fn; assert '#import' not in clean,fn
 (out/fn).write_text(cs)
assert cm['26728_universal_adaptive_color.comp']=='d2b0e15f49800fa27902e41c82a84291d47226c1e79741ea062da3c4eac5418d'
assert cm['26728_restore_extended_hdr_after_vgn.frag']=='ee8a4b306a2e0e2f6ff067f036fb626f75d02ca215a24f83e0cedaa3217d5cc8'
seed=triple(cand,specs[0][0],'seed'); med=triple(cand,specs[1][0],'localMedian'); iir=triple(cand,specs[2][0],'iirRgb')
for t in ['IRIS_26729_COLOR_MATERIAL_DIRECTION_GATE','centerContinuation','neighborContinuation']: assert t in seed,t
for t in ['IRIS_26729_COLOR_MATERIAL_MEDIAN_GATE','colorBoundaryProtection','colorMaterialBoundary']: assert t in med,t
for t in ['IRIS_26729_COLOR_ONLY_IIR_STATE_RESET','colorOnlyMaterialBoundary','topologyBoundary']: assert t in iir,t
if a.compiler:
 comp=Path(a.compiler); assert comp.exists(),comp
 for rel,name,fn,stage,modified in specs:
  cp=subprocess.run([str(comp),'-S',stage,str(out/fn)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
  if cp.returncode:
   print(cp.stdout); raise SystemExit(f'glslang FAIL {fn}')
shutil.rmtree(out,ignore_errors=True)
print(f'PASS 26729 shaders: 271-asset universe unchanged; exact 15 tracked runtime-expanded variants; 3 modified containment shaders + 2 inherited 26728 hue-safety shaders reserved/structure clean; real_compiler={bool(a.compiler)}')
