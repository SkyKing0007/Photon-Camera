#!/usr/bin/env python3
"""Physical protected-source and Experiment C isolation (no Android compiler substitution)."""
from pathlib import Path
from difflib import SequenceMatcher
import re,sys,json,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_26972_incremental as build
R=build.R
changed,base,cand=build.scope()
if '--live' in sys.argv:
 root=R;prev=build.BASE
 build.exact(root,'26972_EXPECTED_FULL_APP.sha256','C current source complete')
 build.exact(prev,'26972_BASE_26971_FULL_APP.sha256','prior compiled 26971 source complete')
else:
 root=R/'handoff_payload_26972';prev=None
for rel in changed:
 if not (root/rel).is_file() or build.sha(root/rel)!=cand[rel]:build.fail('missing/mutated C source '+rel)
# Source of A/B critical execution bodies is unchanged except C-tagged insertions.
for name in ('CaptureController.java','HdrxProcessor.java','PhotonMotionMgc1271Bridge.kt'):
 path=next(p for p in build.MODIFIED if p.endswith('/'+name))
 if prev:
  old=(prev/path).read_text().splitlines(keepends=True)
  new=(root/path).read_text().splitlines(keepends=True)
  for op,i,j,k,l in SequenceMatcher(None,old,new,autojunk=False).get_opcodes():
   if op=='equal':continue
   if op!='insert' or '26972' not in ''.join(new[k:l]):build.fail('A/B original altered rather than C-only insertion '+path)
 if '26972' not in (root/path).read_text():build.fail('C-owner injection absent '+path)
con=root/'app/src/main/java/com/particlesdevs/photoncamera/processing/experimentc/Iris26972CContract.java'
s=con.read_text()
for marker in ('PRODUCTION_READY = false','ACTUAL_CAMERA2_CALLBACK_WIRED = false','ALLOW_ALTERNATE_RECONSTRUCTOR = false','ALLOW_ALTERNATE_FINISHER = false','MAX_NORMAL_FRAMES = 30'):
 if marker not in s:build.fail('Experiment C firewall changed '+marker)
java=root/'app/src/main/java/com/particlesdevs/photoncamera/processing/experimentc'
cpp=root/'app/src/main/cpp';cmake=(cpp/'CMakeLists.txt').read_text()
match=re.search(r'add_library\(iris26972c\s+SHARED\s+([^\)]+)\)',cmake)
if not match:build.fail('C native CMake target missing')
cs=[p.strip() for p in match.group(1).splitlines() if p.strip()]
if len(cs)!=11 or len(set(cs))!=11:build.fail('C source list must be 11 unique TUs')
# In --payload mode the staged overlay contains all C source, so this is complete.
if set(cs)!={p.relative_to(cpp).as_posix() for p in (cpp/'iris26972c').glob('*.cpp')}:build.fail('C orphaned/absent CMake implementation')
for p in cs:
 if not (cpp/p).is_file():build.fail('C native TU missing '+p)
native=[]
for p in java.glob('Iris26972C*.java'):
 for method in re.findall(r'\bnative\s+(?:boolean|int|long|void)\s+(\w+)\s*\(',p.read_text()):native.append(f'Java_com_particlesdevs_photoncamera_processing_experimentc_{p.stem}_{method}')
export=[]
for p in (cpp/'iris26972c').glob('*_jni.cpp'):
 export+=re.findall(r'\b(Java_com_particlesdevs_photoncamera_processing_experimentc_\w+)\s*\(',p.read_text())
if len(native)!=7 or sorted(native)!=sorted(export) or len(set(native))!=7:build.fail('C 7 JNI names unresolved/duplicate')
for name,want in build.DONOR_SHA.items():
 path=root/'app/src/main/jniLibs'/name.removeprefix('lib/')
 if not path.is_file() or build.sha(path)!=want or f'{path.name}|{want}' not in cmake:build.fail('C donor ELF or CMake SHA mismatch')
color=root/'app/src/main/assets/iris26972c/sRGB.icc'
if build.sha(color)!='78e7ab7ab641965ccafce2b4fdd481c8b90ae15c8c4e9afef649aa9c7b1633c8':build.fail('ICC mutated')
# C-only captured raw role is strict; 50-frame limit is just host-stress, not production.
k=root/'app/src/main/java/com/hinnka/mycamera/processor/Iris26972CCamera2ShutterSession.kt'
if 'session-' not in k.read_text() or 'iris26972c-private' not in k.read_text():build.fail('crash-safe isolated RAW workspace absent')
# Physical shader version + reserved declaration check runs at package seal and again on Actions.
shaders=sorted((R/'26972_EXACT_EXPANDED_C_SHADERS').glob('*.frag'))
if len(shaders)!=24:build.fail('24 exact current C expanded shaders missing')
shader_manifest={line.split('  ',1)[1]:line.split('  ',1)[0] for line in (R/'26972_EXPANDED_SHADER_HASHES.sha256').read_text().splitlines()}
if len(shader_manifest)!=24 or set(shader_manifest)!={p.name for p in shaders}:build.fail('C shader manifest path set mismatch')
reserved=set("""attribute varying precision highp mediump lowp in out inout uniform buffer shared coherent volatile restrict readonly writeonly const invariant layout flat smooth noperspective patch sample centroid subroutine common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output filter sizeof cast namespace using row_major switch default case struct while do for if else continue break return discard true false void int uint float double bool atomic_uint""".split())
reserved.update(('gl_FragColor','gl_FragData','gl_FragCoord','gl_VertexID','gl_Position'))
qualifier=r'(?:\b(?:highp|mediump|lowp|readonly|writeonly|flat|smooth|centroid)\s+)*'
datatype=r'(?:float|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234]|sampler2D|isampler2D|usampler2D|sampler3D|sampler2DArray)'
var=re.compile(r'\b(?:uniform|in|out|const)?\s*'+qualifier+r'\b'+datatype+r'\s+(\w+)\s*(?=[;=,\[])')
# Also scan function parameters, struct members and declarations after a type token.
more=re.compile(r'\b(?:bool|int|uint|float|double|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?|sampler\w*|isampler\w*|usampler\w*)\s+([A-Za-z_]\w*)\b')
versions={'300':0,'310':0}
for shader in shaders:
 src=shader.read_text()
 if build.sha(shader)!=shader_manifest[shader.name]:build.fail('altered expanded C shader '+shader.name)
 if src.startswith('#version 300 es\n'):versions['300']+=1
 elif src.startswith('#version 310 es\n'):versions['310']+=1
 else:build.fail('unexpected GLES version '+shader.name)
 if src.count('void main()')!=1:build.fail('missing/duplicate C shader main '+shader.name)
 code=re.sub(r'/\*.*?\*/|//[^\n]*','',src,flags=re.S)
 for m in list(var.finditer(code))+list(more.finditer(code)):
  name=m.group(1)
  if name in reserved or name.startswith('gl_'):build.fail('reserved GLSL variable or parameter '+shader.name+' '+name)
if versions!={'300':19,'310':5}:build.fail('expected 19 ES300 and 5 ES310 shaders, got '+str(versions))
print('PASS 26972 physical C shader SHA+reserved-variable preflight, 19 ES300 / 5 ES310')
print('PASS 26972 exact compiled-source allowlist, source-current A/B protected, C gate/RAW, 11/11 native, 7/7 JNI, donor SHA pins')
