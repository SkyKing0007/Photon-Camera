#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,re,textwrap,subprocess,tempfile,shutil
ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('base'); ap.add_argument('cand'); ap.add_argument('--compiler'); a=ap.parse_args()
pkg=Path(a.root); base=Path(a.base); cand=Path(a.cand); out=Path(tempfile.mkdtemp(prefix='i26728_expanded_'))
specs=[
('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt','universalAdaptiveColor26561','26728_universal_adaptive_color.comp','comp'),
('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt','restoreExtendedHdrAfterVgn','26728_restore_extended_hdr_after_vgn.frag','frag')]
def triple(root,rel,name):
 s=(root/rel).read_text(); m=re.search(r'val\s+'+re.escape(name)+r'(?:\s*:\s*String)?\s*=\s*"""\n(.*?)\n\s*"""\.trimIndent\(\)',s,re.S); assert m,name
 return textwrap.dedent(m.group(1))
def load_manifest(n):
 d={}
 for line in (pkg/n).read_text().splitlines():
  if line.strip(): h,p=line.split(None,1); d[p.strip()]=h
 return d
# Assets are byte-invariant; these changes are Kotlin-embedded runtime GLSL only.
def asset_hashes(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'app/src/main/assets/shaders').rglob('*') if p.is_file()}
assert len(asset_hashes(base))==len(asset_hashes(cand))==271 and asset_hashes(base)==asset_hashes(cand)
reserved=set('attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 dvec2 dvec3 dvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 filter sizeof cast namespace using row_major'.split())
typepat=r'(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w*|[iu]?image\w*|atomic_uint|void)'
base_manifest=load_manifest('26728_RUNTIME_EXPANDED_BASE.sha256'); cand_manifest=load_manifest('26728_RUNTIME_EXPANDED_CANDIDATE.sha256')
assert len(base_manifest)==len(cand_manifest)==12
for rel,name,fn,stage in specs:
 bs=triple(base,rel,name); cs=triple(cand,rel,name)
 assert hashlib.sha256(bs.encode()).hexdigest()==base_manifest[fn],('base shader hash',fn)
 assert hashlib.sha256(cs.encode()).hexdigest()==cand_manifest[fn],('candidate shader hash',fn)
 assert bs!=cs,('expected modified runtime shader',fn)
 clean=re.sub(r'/\*.*?\*/',' ',cs,flags=re.S); clean=re.sub(r'//.*',' ',clean)
 ids=re.findall(r'\b'+typepat+r'\s+([A-Za-z_]\w*)\b',clean)+re.findall(r'\bstruct\s+([A-Za-z_]\w*)\b',clean)
 bad=sorted(set(ids)&reserved); impl=sorted(set(x for x in ids if '__' in x or x.startswith('gl_')))
 assert not bad and not impl,(fn,bad,impl); assert clean.count('{')==clean.count('}'),fn; assert '#import' not in clean,fn
 (out/fn).write_text(cs)
# Exact 26728 semantics required in runtime-expanded shaders.
u=triple(cand,specs[0][0],specs[0][1]); r=triple(cand,specs[1][0],specs[1][1])
for t in ['uPhysicalPreVgn','hardArtifactVeto = step(0.50, artifactVeto)','artifactPermission','correctedChroma *= restoredMagnitude / cleanedMagnitude','protectedPreVgnMagnitude']:
 assert t in u,t
assert 'correctedChroma = preVgnChroma' not in u
for t in ['physicalMagnitude = max3(physical)','cleanedDirection','protectedPreVgnChromaMagnitude','oHdr = vec4(max(restored, vec3(0.0)), protectedPreVgnChromaMagnitude)']:
 assert t in r,t
assert 'restored = physical' not in r
if a.compiler:
 comp=Path(a.compiler); assert comp.exists(),comp
 for rel,name,fn,stage in specs:
  cp=subprocess.run([str(comp),'-S',stage,str(out/fn)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
  if cp.returncode:
   print(cp.stdout); raise SystemExit(f'glslang FAIL {fn}')
shutil.rmtree(out,ignore_errors=True)
print(f'PASS 26728 modified runtime shaders: exact 2 expanded variants; full reserved/structure scan; magnitude-only/VGN-direction ownership; real_compiler={bool(a.compiler)}')
