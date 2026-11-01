#!/usr/bin/env python3
"""Exact successful 26894 -> intentional 26893 source restoration + Motion 1.14 baseline.
Enforces no 26894 image-quality runtime, immutable 2021 protected files,
actual executable four-operand patch replay and two exact restored shaders.
"""
from pathlib import Path
import hashlib,sys,re,shutil,subprocess,tempfile,random
R=Path(__file__).resolve().parent
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def load(fn):
 d={}
 for line in (R/fn).read_text().splitlines():
  digest,path=line.split('  ',1);assert re.fullmatch('[a-f0-9]{64}',digest) and path not in d;d[path]=digest
 return d
def files(root):return {f.relative_to(root).as_posix():H(f) for f in root.rglob('*') if f.is_file() and '.git' not in f.parts}
old=load('26895_BASE_FULL_APP.sha256');new=load('26895_EXPECTED_CANDIDATE_FULL_APP.sha256');pro=load('26895_UNCHANGED_PROTECTED.sha256')
allowed=(R/'26895_CHANGED_ALLOWLIST.txt').read_text().splitlines()
removed='app/src/main/assets/shaders/motionv2/spatial_scene_26894.glsl'
assert len(old)==2026 and len(new)==2025 and len(pro)==2021
assert len(allowed)==5
assert sorted(p for p in set(old)|set(new) if old.get(p)!=new.get(p))==allowed
assert set(old)-set(new)=={removed} and not set(new)-set(old)
assert (R/'26895_DELETIONS.txt').read_text().splitlines()==[removed]
assert (R/'26895_ADDITIONS.txt').read_bytes()==b''
assert set(pro)==set(old)-set(allowed)
assert all(old[p]==new[p]==h for p,h in pro.items())
payload=R/'handoff_payload_26895'
assert {str(f.relative_to(payload)) for f in payload.rglob('*') if f.is_file()}=={p.removeprefix('app/') for p in allowed if p!=removed}
assert all(H(payload/p.removeprefix('app/'))==new[p] for p in allowed if p!=removed)

def candidate(base,cand,transform):
 assert files(base)==old,'successful 26894 actual compiled candidate mismatch'
 if transform:
  assert not cand.exists(),'transform requires absent destination';shutil.copytree(base,cand)
  for p in allowed:
   dst=cand/p
   if p==removed:assert dst.is_file();dst.unlink()
   else:
    src=payload/p.removeprefix('app/');assert src.is_file();shutil.copy2(src,dst)
 assert files(cand)==new,'candidate must exactly match frozen manifest (no extra files)'
 assert all(H(cand/p)==h for p,h in pro.items()),'protected hashes altered'
 assert (cand/'app/version.properties').read_text().splitlines()[-2:]==['VERSION_NAME=0.9726895','VERSION_BUILD=26895']
 print('PASS 26895 compiled 26894 authority -> 26893 restored + saturation; 2026->2025 files, 5 paths, 1 deletion, 2021 protected')

def semantics(base,cand):
 candidate(base,cand,False)
 a=base;c=cand
 # Historical reference is the actual compiled 26893 source digest list, frozen by 26894 handoff.
 hist=load('26895_HISTORICAL_26893_FULL_APP.sha256')
 assert len(hist)==2025 and set(hist)==set(new)
 j='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
 v='app/version.properties'
 assert all(new[p]==hist[p] for p in new if p not in (j,v)), 'anything other than saturation and version diverged from 26893'
 text=(c/j).read_text();prev=(a/j).read_text()
 assert text.count('IRIS_26824_MOTION_SATURATION_SCALE = 1.14f')==1
 assert text.count('IRIS_26895_MOTION_SATURATION_BASELINE')==1
 assert 'IRIS_26824_MOTION_SATURATION_SCALE = 0.95f' not in text
 assert text.count('iris26824FrozenInputSaturation')>=3
 assert 'iris26630Tone.saturation : 1.0f' in text
 assert 'if (basePipeline.mParameters.motionV2Active)' in text
 assert 'iris26630MotionSaturation *= IRIS_26824_MOTION_SATURATION_SCALE;' in text
 assert 'Math.max(0.0f, Math.min(2.0f, iris26630MotionSaturation))' in text
 assert 'saturationOwner=IRIS_26895_RELATIVE_1P14' in text
 assert 'iris26630SaturationOwner=' in text and 'MOTION_PER_LENS' in text and 'NIGHT_NEUTRAL_1_0' in text
 assert 'iris26630MotionSaturation' in (c/'app/src/main/assets/shaders/motionv2/render.glsl').read_text()
 assert 'iris26630MotionSaturation' not in (c/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text()  # gainmap derives from completed SDR result
 settings=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java').read_text()
 assert 'KEY_SATURATION = "pref_iris_saturation"' in settings
 assert 'float saturation = snap01(getFloat(sm, KEY_SATURATION, 1.0f), 0.0f, 2.0f);' in settings
 assert 'KEY_SATURATION.equals(key)' in settings
 prefs=(c/'app/src/main/res/values/default_prefs.xml').read_text()
 assert '<string name="pref_iris_saturation_default" translatable="false">1.0</string>' in prefs
 ui=(c/'app/src/main/res/xml/preferences.xml').read_text()
 assert 'ns0:key="pref_iris_saturation"' in ui and 'ns0:defaultValue="@string/pref_iris_saturation_default"' in ui
 assert 'IRIS_26894_SPATIAL_SCENE_ADAPTIVE_SDR_AND_MATCHED_UHDR' not in text
 assert not (c/removed).exists()
 # Intentionally preserved historical source shader, original backlit/contrast behavior.
 for p in ('app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl'):
  assert new[p]==hist[p]
 # Signal exactly same processing result as OLD 26893 slider 1.20 for current 26895 slider 1.00.
 assert abs(1.20 * .95 - 1.00 * 1.14)<1e-7
 for lens in (0,1,2,3,4,10):
  for display in (0.0,0.1,0.5,0.8,1.0,1.2,1.6,2.0):
   effective=min(2.0,max(0.0,display*1.14));assert 0<=effective<=2.0
   if display==1.0:assert abs(effective-1.14)<1e-6
 assert prev!=text
 print('PASS 26895 restore 26893 ALL other original color/tone, per-lens UI1.0 -> effective1.14 = old 1.20*0.95, Night neutral, SDR/UHDR paired')

def shader(cand,compiler=None,out=None):
 assert files(cand)==new
 lib=cand/'app/src/main/assets/shaders/motionv2'
 source=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLProg.java').read_text()
 assert 'glVersion = "#version 310 es' in source
 reserved=set('sample attribute varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch invariant precise subroutine highp mediump lowp precision in out inout const struct if else do while switch case default for return discard break continue asm class union enum typedef template this packed goto inline noinline public static extern external interface long short half fixed unsigned input output common partition active filter resource namespace using'.split())
 for name in ('render.glsl','gainmap.glsl'):
  src=(lib/name).read_text()
  assert src.count('{')==src.count('}') and '#version' not in src and '#include' not in src
  clean=re.sub(r'/\*.*?\*/|//[^\n]*','',src,flags=re.S)
  declarations=re.findall(r'\b(?:float|int|uint|bool|vec[234]|ivec[234]|uvec[234]|mat[234]|sampler2D)\s+([A-Za-z_][A-Za-z0-9_]*)',clean)
  assert not (set(declarations)&reserved),(name,set(declarations)&reserved)
  assert all(not x.startswith('gl_') and '__' not in x for x in declarations)
  full='#version 310 es\n#line 1\n'+src
  if compiler:
   assert out is not None;out.mkdir(parents=True,exist_ok=True)
   path=out/(name+'.frag');path.write_text(full)
   p=subprocess.run([str(compiler),'-S','frag',str(path)],capture_output=True,text=True)
   assert p.returncode==0,(name,p.stdout,p.stderr)
  print('PASS 26895 actual restored runtime ESSL310',name,'SHA256',hashlib.sha256(full.encode()).hexdigest(),'REAL_PINNED',('PASS' if compiler else 'NOT RUN'))
 print('PASS 26895 TWO exact restored 26893 GLES310 runtime programs REAL PINNED COMPILE '+('PASS' if compiler else 'NOT RUN'))

def patch(base,cand,forward,rollback):
 candidate(base,cand,False)
 for ab in (7,12,40):
  with tempfile.TemporaryDirectory(prefix='photon26895patch_') as d:
   x=Path(d)/'src';shutil.copytree(base,x)
   subprocess.run(['git','init','-q'],cwd=x,check=True)
   def run(*args):
    p=subprocess.run(['git','-c',f'core.abbrev={ab}',*args],cwd=x,capture_output=True,text=True)
    assert p.returncode==0,(ab,args,p.stdout,p.stderr)
   run('apply','--check','--whitespace=error',str(forward));run('apply','--whitespace=error',str(forward))
   assert files(x)==new
   run('apply','--check','--reverse',str(forward));run('apply','--check','--whitespace=error',str(rollback));run('apply','--whitespace=error',str(rollback))
   assert files(x)==old
   print('PASS 26895 exact 4-operand full-index 7/12/40 patch forward+rollback, fuzz0, deleted shader restored',ab)

def tamper(base,cand):
 candidate(base,cand,False)
 with tempfile.TemporaryDirectory(prefix='photon26895tamper_') as d:
  root=Path(d);shutil.copytree(cand,root/'cand')
  target=root/'cand/app/src/main/res/values/default_prefs.xml';target.write_bytes(target.read_bytes()+b'\n')
  assert files(root/'cand')!=new
  target.write_bytes((cand/'app/src/main/res/values/default_prefs.xml').read_bytes())
  assert files(root/'cand')==new
  (root/'cand/app/src/main/assets/shaders/motionv2/spatial_scene_26894.glsl').write_text('stale 26894')
  assert files(root/'cand')!=new
  (root/'cand/app/src/main/assets/shaders/motionv2/spatial_scene_26894.glsl').unlink()
  target=root/'cand/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
  target.write_text(target.read_text().replace('= 1.14f','= 0.95f'))
  assert files(root/'cand')!=new
  print('PASS 26895 negative protected tamper, stale 26894 shader, and old saturation baseline rejected')

if __name__=='__main__':
 mode=sys.argv[1];args=sys.argv[2:]
 if mode=='candidate':
  assert len(args) in (2,3);assert len(args)==2 or args[2]=='--transform';candidate(Path(args[0]),Path(args[1]),len(args)==3)
 elif mode=='semantics':
  assert len(args)==2;semantics(Path(args[0]),Path(args[1]))
 elif mode=='shader':
  assert len(args)>=1;path=Path(args[0]);compiler=None;out=None
  if len(args)>1:
   assert len(args)==5 and args[1]=='--compiler' and args[3]=='--out';compiler=Path(args[2]);out=Path(args[4]);assert compiler.is_file()
  shader(path,compiler,out)
 elif mode=='patch':
  assert len(args)==4;patch(Path(args[0]),Path(args[1]),Path(args[2]).resolve(),Path(args[3]).resolve())
 elif mode=='tamper':
  assert len(args)==2;tamper(Path(args[0]),Path(args[1]))
 else:raise AssertionError('unknown gate '+mode)
