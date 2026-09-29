#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,re,subprocess,tempfile,shutil
ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('base'); ap.add_argument('cand'); ap.add_argument('--compiler'); a=ap.parse_args()
pkg=Path(a.root); base=Path(a.base); cand=Path(a.cand); out=Path(tempfile.mkdtemp(prefix='i26733_expanded_'))
vrel='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
srel='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
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
 # IRIS_26733_INHERIT_26729_R1_EXACT_KOTLIN_RUNTIME_SHADER_EXPANSION
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
embedded=['seed','localClamp','localMedian','directionalSmooth','restoreDirection','iirRgb','calculateError','iirError','blendChroma','finalCameraRgb','universalAdaptiveColor26561']
changed_embedded={n for n in embedded if runtime_shader(base,vrel,n)!=runtime_shader(cand,vrel,n)}
assert changed_embedded=={'seed','localMedian','directionalSmooth','universalAdaptiveColor26561'},changed_embedded
bm=load_manifest('26733_RUNTIME_EXPANDED_BASE.sha256'); cm=load_manifest('26733_RUNTIME_EXPANDED_CANDIDATE.sha256'); assert len(bm)==len(cm)==16
specs=[
(vrel,'seed','26733_vgn_seed.comp','comp',True),
(vrel,'localMedian','26733_vgn_local_median.comp','comp',True),
(vrel,'directionalSmooth','26733_vgn_directional.comp','comp',True),
(vrel,'iirRgb','26733_vgn_iir_rgb.comp','comp',False),
(vrel,'universalAdaptiveColor26561','26733_universal_adaptive_color.comp','comp',True),
(srel,'restoreExtendedHdrAfterVgn','26728_restore_extended_hdr_after_vgn.frag','frag',False)]
reserved=set('attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 vec2 vec3 vec4 ivec2 ivec3 ivec4 uvec2 uvec3 uvec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint lowp mediump highp precision struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 filter sizeof cast namespace using row_major'.split())
typepat=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w*|[iu]?image\w*|atomic_uint|void)'
def scan(fn,src):
 clean=re.sub(r'/\*.*?\*/',' ',src,flags=re.S); clean=re.sub(r'//.*',' ',clean)
 ids=re.findall(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\b',clean)+re.findall(r'\bstruct\s+([A-Za-z_]\w*)\b',clean)
 bad=sorted(set(ids)&reserved); impl=sorted(set(x for x in ids if '__' in x or x.startswith('gl_')))
 assert not bad and not impl,(fn,bad,impl); assert clean.count('{')==clean.count('}'),fn; assert '#import' not in clean,fn
for relp,name,fn,stage,modified in specs:
 bs=runtime_shader(base,relp,name); cs=runtime_shader(cand,relp,name)
 assert hashlib.sha256(bs.encode()).hexdigest()==bm[fn],('base shader hash',fn)
 assert hashlib.sha256(cs.encode()).hexdigest()==cm[fn],('candidate shader hash',fn)
 assert (bs!=cs)==modified,('modified expectation',fn)
 scan(fn,cs); (out/fn).write_text(cs)
# Preserve the exact 26732 direct runtime high-zoom owners and established compiler-tested bytes.
flow=runtime_shader(cand,srel,'highZoomFlowRefine26724'); rgb=runtime_shader(cand,srel,'highZoomRgbProtect26724')
assert hashlib.sha256(flow.encode()).hexdigest()==cm['26724_highzoom_flow_refine.frag']=='3afef77f38b551aebe0de01a911ef863fcbebd44676a941312dd4feceea50cdf'
assert hashlib.sha256(rgb.encode()).hexdigest()==cm['26724_highzoom_native_chroma_protect.frag']=='1c5487547bcdd5aba53c3e6bd63d85bb276a1c718744ff6405ab73a39cd3c6bc'
for fn,src in [('26724_highzoom_flow_refine.frag',flow),('26724_highzoom_native_chroma_protect.frag',rgb)]: scan(fn,src); (out/fn).write_text(src)
seed=runtime_shader(cand,vrel,'seed'); med=runtime_shader(cand,vrel,'localMedian'); directional=runtime_shader(cand,vrel,'directionalSmooth'); adaptive=runtime_shader(cand,vrel,'universalAdaptiveColor26561')
for t in ['IRIS_26733_INHERITED_HIGHLIGHT_HEADROOM_OWNER','IRIS_26733_EARLY_ACHROMATIC_STRUCTURE_OWNER','neutralStructure << 14','highlightColorOwnershipPermission']: assert t in seed,t
for t in ['IRIS_26731_FROZEN_RECIPROCAL_MATERIAL_OWNERSHIP','IRIS_26733_HEADROOM_FAILS_NEUTRAL','IRIS_26733_ACHROMATIC_STRUCTURE_CLEANUP']: assert t in med,t
for t in ['IRIS_26731_DIRECTION_PAIR_GEOMETRY','IRIS_26731_RECIPROCAL_ONE_SIDED_DIRECTIONAL','neutralStructureAt','originalHuePermission']: assert t in directional,t
for t in ['IRIS_26733_HEADROOM_PRECEDES_COLOR_OWNERSHIP','IRIS_26733_NEUTRAL_FLOOR_VETO','IRIS_26728_PHYSICALLY_SUPPORTED_CHROMA_MAGNITUDE']: assert t in adaptive,t
for t in ['uNoiseShot','robustSolveWeight']: assert t in flow,t
for t in ['IRIS_26724_WEAK_DISAGREEING_NATIVE_CHROMA_ADAPTATION','IRIS_26724_HIGH_ZOOM_STRUCTURAL_LUMA_REINFORCEMENT']: assert t in rgb,t
if a.compiler:
 comp=Path(a.compiler); assert comp.exists(),comp
 compile_specs=[(x[2],x[3]) for x in specs]+[('26724_highzoom_flow_refine.frag','frag'),('26724_highzoom_native_chroma_protect.frag','frag')]
 for fn,stage in compile_specs:
  cp=subprocess.run([str(comp),'-S',stage,str(out/fn)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
  if cp.returncode:
   print(cp.stdout); raise SystemExit(f'glslang FAIL {fn}')
shutil.rmtree(out,ignore_errors=True)
print(f'PASS 26733 shaders: 271-asset universe unchanged; exact 16 tracked runtime-expanded variants; exact Kotlin interpolation; 4 VGN shaders modified; 26731 IIR and 26732 direct high-zoom runtime owners inherited; reserved/structure clean; real_compiler={bool(a.compiler)}')
