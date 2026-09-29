#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,re,subprocess,tempfile,shutil
ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('base'); ap.add_argument('cand'); ap.add_argument('--compiler'); a=ap.parse_args()
pkg=Path(a.root); base=Path(a.base); cand=Path(a.cand); out=Path(tempfile.mkdtemp(prefix='i26730_expanded_'))
rel='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
specs=[
(rel,'seed','26730_vgn_seed.comp','comp',True),
(rel,'localMedian','26730_vgn_local_median.comp','comp',True),
(rel,'iirRgb','26730_vgn_iir_rgb.comp','comp',True),
(rel,'universalAdaptiveColor26561','26728_universal_adaptive_color.comp','comp',False),
('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt','restoreExtendedHdrAfterVgn','26728_restore_extended_hdr_after_vgn.frag','frag',False)]
def raw_triple(root,rel,name):
 s=(root/rel).read_text(); m=re.search(r'(?:private\s+)?val\s+'+re.escape(name)+r'(?:\s*:\s*String)?\s*=\s*"""(.*?)"""\.trimIndent\(\)',s,re.S); assert m,name; return m.group(1)
def kotlin_trim_indent(value):
 lines=value.replace('\r\n','\n').replace('\r','\n').split('\n')
 if lines and lines[0].strip()=='': lines=lines[1:]
 if lines and lines[-1].strip()=='': lines=lines[:-1]
 nonblank=[line for line in lines if line.strip()]
 indent=min((len(line)-len(line.lstrip()) for line in nonblank),default=0)
 return '\n'.join(line[indent:] if line.strip() else '' for line in lines)
def runtime_shader(root,rel,name):
 raw=raw_triple(root,rel,name)
 # IRIS_26730_INHERIT_R1_EXACT_KOTLIN_RUNTIME_SHADER_EXPANSION:
 # Kotlin interpolation occurs before the shader template's trimIndent().
 if '$common' in raw:
  common=kotlin_trim_indent(raw_triple(root,rel,'common')); raw=raw.replace('$common',common)
 expanded=kotlin_trim_indent(raw); assert '$' not in expanded,(name,'unresolved Kotlin interpolation'); return expanded
def load_manifest(n):
 d={}
 for line in (pkg/n).read_text().splitlines():
  if line.strip(): h,p=line.split(None,1); d[p.strip()]=h
 return d
def asset_hashes(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'app/src/main/assets/shaders').rglob('*') if p.is_file()}
assert len(asset_hashes(base))==len(asset_hashes(cand))==271 and asset_hashes(base)==asset_hashes(cand)
# Freeze every embedded VGN stage except the three explicitly intended 26730 containment shaders.
embedded=['seed','localClamp','localMedian','directionalSmooth','restoreDirection','iirRgb','calculateError','iirError','blendChroma','finalCameraRgb','universalAdaptiveColor26561']
changed_embedded={n for n in embedded if runtime_shader(base,rel,n)!=runtime_shader(cand,rel,n)}
assert changed_embedded=={'seed','localMedian','iirRgb'},changed_embedded
reserved=set('attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 filter sizeof cast namespace using row_major'.split())
typepat=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w*|[iu]?image\w*|atomic_uint|void)'
bm=load_manifest('26730_RUNTIME_EXPANDED_BASE.sha256'); cm=load_manifest('26730_RUNTIME_EXPANDED_CANDIDATE.sha256'); assert len(bm)==len(cm)==15
for relp,name,fn,stage,modified in specs:
 bs=runtime_shader(base,relp,name); cs=runtime_shader(cand,relp,name)
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
seed=runtime_shader(cand,specs[0][0],'seed'); med=runtime_shader(cand,specs[1][0],'localMedian'); iir=runtime_shader(cand,specs[2][0],'iirRgb')
for t in ['IRIS_26729_COLOR_MATERIAL_DIRECTION_GATE','IRIS_26730_PHYSICAL_VALIDITY_CONTAINMENT_AUTHORITY','IRIS_26730_TRUE_MATERIAL_STEP_GATE','physicalColorTrust','materialStepProof']: assert t in seed,t
for t in ['IRIS_26729_COLOR_MATERIAL_MEDIAN_GATE','IRIS_26730_PHYSICAL_VALIDITY_CONTAINMENT_AUTHORITY','physicalColorTrust','materialStepProof','colorMaterialBoundary']: assert t in med,t
for t in ['IRIS_26729_COLOR_ONLY_IIR_STATE_RESET','IRIS_26730_VALIDITY_OWNED_COLOR_ONLY_IIR_RESET','physicalColorTrust','trueMaterialStep','physicalTrust>0.85']: assert t in iir,t
if a.compiler:
 comp=Path(a.compiler); assert comp.exists(),comp
 for relp,name,fn,stage,modified in specs:
  cp=subprocess.run([str(comp),'-S',stage,str(out/fn)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
  if cp.returncode:
   print(cp.stdout); raise SystemExit(f'glslang FAIL {fn}')
shutil.rmtree(out,ignore_errors=True)
print(f'PASS 26730 shaders: 271-asset universe unchanged; exact 15 tracked runtime-expanded variants; exact Kotlin interpolation before hash/scan/compile; only seed/localMedian/iirRgb modified across full embedded VGN universe; physical-validity + true-material-step containment markers clean; real_compiler={bool(a.compiler)}')
