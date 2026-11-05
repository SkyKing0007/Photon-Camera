#!/usr/bin/env python3
"""Photon 26903. Actual successful 26902 bytes, immutable allowlist, B Night source ownership,
full-index 4-operand patch proof, fail-closed tamper and real expanded GLSL source scans.
Static validation NEVER masquerades as Android/GLSL compilation or hardware validation.
"""
from pathlib import Path
import hashlib, re, shutil, subprocess, sys, tempfile
R=Path(__file__).resolve().parent
SHA=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
PATCH=['26903_FORWARD_FULL_INDEX.patch','26903_ROLLBACK_FULL_INDEX.patch']
def fail(x):raise AssertionError(x)
def read_set(name):return [x.strip() for x in (R/name).read_text().splitlines() if x.strip()]
def manifest(name):
 rows={}
 for line in (R/name).read_text().splitlines():
  s,p=line.split('  ',1);assert re.fullmatch('[0-9a-f]{64}',s) and p not in rows and p.startswith('app/')
  rows[p]=s
 return rows
def files(t):return {p.relative_to(t).as_posix():p for p in (t/'app').rglob('*') if p.is_file()}
def valid_candidate(base,cand,allowTransform=False):
 old=manifest('26903_BASE_FULL_APP.sha256');future=manifest('26903_EXPECTED_CANDIDATE_FULL_APP.sha256')
 protected=manifest('26903_UNCHANGED_PROTECTED.sha256')
 allow=read_set('26903_CHANGED_ALLOWLIST.txt');add=read_set('26903_ADDITIONS.txt');delete=read_set('26903_DELETIONS.txt')
 assert len(old)==2026 and len(future)==2027 and len(protected)==2014
 assert len(allow)==13 and len(add)==1 and not delete
 assert sorted(allow)==allow and len(allow)==len(set(allow))
 assert sorted(set(future)-set(old))==add
 assert sorted(set(old)-set(future))==delete
 assert sorted(x for x in old if x in future and old[x]!=future[x])==sorted(set(allow)-set(add))
 assert {x:old[x] for x in protected}==protected
 assert not set(protected)&set(allow)
 assert all(x.startswith('app/src/main/') or x=='app/version.properties' for x in allow)
 assert not any('/spektra/' in x or '/jni/' in x or '/native/' in x or '/vendor/' in x for x in allow)
 actualbase=files(base)
 assert set(actualbase)==set(old),'26903 base actual source path universe differs successful manifest'
 assert all(SHA(actualbase[x])==s for x,s in old.items()),'26903 base bytes diverge successful source authority'
 if allowTransform:
  if cand.exists():shutil.rmtree(cand)
  shutil.copytree(base,cand,copy_function=shutil.copy2)
  for x in allow:
   src=R/'handoff_payload_26903'/x.removeprefix('app/')
   assert src.exists() and SHA(src)==future[x],('payload',x)
   dst=cand/x;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
 actual=files(cand)
 assert set(actual)==set(future),'26903 candidate unexpected additions/deletions'
 assert all(SHA(actual[x])==s for x,s in future.items()),'26903 candidate source SHA mismatch'
 for x in allow:
  assert (R/'handoff_payload_26903'/x.removeprefix('app/')).is_file()
  assert SHA(R/'handoff_payload_26903'/x.removeprefix('app/'))==future[x]
 assert (cand/'app/version.properties').read_text().count('VERSION_NAME=0.9726903')==1
 assert (cand/'app/version.properties').read_text().count('VERSION_BUILD=26903')==1
 return actualbase,actual,allow

def source_semantics(base,cand):
 valid_candidate(base,cand)
 root=cand/'app/src/main'
 def src(s):return (root/s).read_text()
 a=src('java/com/particlesdevs/photoncamera/capture/CaptureController.java')
 night=src('java/com/particlesdevs/photoncamera/processing/IrisNightBatch.java')
 plan=src('java/com/particlesdevs/photoncamera/processing/parameters/IrisNightFrameSelector.java')
 adapter=src('java/com/particlesdevs/photoncamera/processing/processor/IrisNightBProcessor26903.java')
 hdr=src('java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java')
 bridge=src('java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
 post=src('java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java')
 j=src('java/com/particlesdevs/photoncamera/processing/ultrahdr/Iris26876BGpuFinalRenderer.java')
 sh=src('assets/shaders/iris26876/b_fused_final_p3_gain.frag')
 encoder=src('java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java')
 saver=src('java/com/particlesdevs/photoncamera/processing/ImageSaver.java')
 params=src('java/com/particlesdevs/photoncamera/processing/render/Parameters.java')
 must=[(a,'Iris26856ABSettings.Mode.AMAZE_26855'),(a,'IrisNightFrameSelector.freezeNormalOnlyB'),
 (a,'IrisNightExposureSelector.freezePlan('),(a,'IrisZoomController.applyToRequest('),
 (a,'IrisNightBProcessor26903.process('),(a,'mIrisNight26903ExperimentB'),
 (a,'populateIrisNight26540FrameMetadata'),(a,'mIrisNight26903DngOptions'),
 (night,'experimentB'),(night,'nightBZoom'),(night,'nightBDngOptions'),
 (night,'requestedLongFrames != 0'),(night,'shortCount != frameBudget'),
 (plan,'freezeNormalOnlyB'),(plan,'return new Plan(n, n, 0, true);'),
 (adapter,'batch.frameBudget < 2'),(adapter,'batch.longFrameCount != 0'),
 (adapter,'frame.motionV2ActualExposureNs != baseExposure'),
 (adapter,'frame.motionV2ActualIso != baseIso'),(adapter,'batch.nightBDngOptions'),
 (adapter,'processor.configureIris26903NightB'),(adapter,'processor.startMotion'),(adapter,'ImagePath.newImageFilePath()'),
 (hdr,'mIris26903NightB'),(hdr,'mIris26903NightBJin2x'),
 (hdr,'IrisNightNeuralEnhancer.enhanceInPlaceForTrue2x(img)'),
 (hdr,'IrisNightNeuralEnhancer.enhanceInPlace(img)'),
 (hdr,'IrisNightUltraHdr.prepare'),(hdr,'attachPostJin(img, nightBGain)'),
 (hdr,'mIrisDngIndependentSaved'),(hdr,'mIris26903NightB ? mIris26903NightBJin2x : null'),
 (bridge,'parameters.iris26903NightBFrozenSettings'),(bridge,'parameters.motionV2DngOptions26786'),
 (post,'!mParameters.iris26903NightB'),(post,'mParameters.iris26903NightBFrozenSettings'),
 (params,'public boolean iris26903NightB = false;'),
 (j,'if(nightBFullJin!=null && (params==null || !params.iris26903NightB))'),
 (j,'nightBJinTextures(nightBFullJin)'),
 (j,'GLES30.GL_RGBA32F'),(j,'GLES30.GL_NEAREST'),
 (j,'uniform1i(program,"uNightBJinEnabled",nightBJinApply?1:0);'),
 (j,'if(jinRefTex!=0)GLES30.glDeleteTextures'),
 (sh,'uniform int uNightBJinEnabled;'),(sh,'vec3 iris26903ApplyJin'),
 (sh,'if(uNightBJinEnabled!=0)'),
 (encoder,'nightBFullJin'),(saver,'nightBFullJin')]
 for data,x in must:assert x in data,('missing active ownership invariant',x)
 assert 'IrisNightProcessor.process(batch, cameraEventsListener)' in a
 assert 'if (batch.experimentB)' in a
 assert 'cameraMode == CameraMode.NIGHT' in hdr and '26540 Night must not enter HdrxProcessor.Run' in hdr
 assert 'iris26856BRequestedOnly && !processingParameters.motionV2SuperResOutputEnabled' in hdr
 assert 'Iris26864ZoomRoute.shouldRouteBToExactA(' in hdr
 assert '!parameters.irisNightActive' in bridge
 assert 'if (iris26903NightB)' in a and 'IrisZoomController.applyToRequest(' in a
 assert 'frame.motionV2PhysicalCameraId = actualPhysical26903;' in a
 assert 'actualPhysical26903.equals(mIrisNight26903Zoom.ownerCameraId)' in a
 assert 'ImagePath.getNewImageFilePath(' not in adapter
 assert 'imageFile = Paths.get(iris26856BasePath + iris26856Extension);' in hdr
 assert '!mIris26903NightB' not in sh and 'uNightBJinEnabled!=0' in sh
 # New 50MP shader path is only selected under the immutable Night B model payload.
 assert 'if(nightBFullJin!=null && (params==null || !params.iris26903NightB))' in j
 assert sh.startswith('#version 310 es') and sh.count('void main()')==1
 assert 'VERSION_BUILD=26903' in (cand/'app/version.properties').read_text()
 assert 'build_26902_iris_rawr_outputs/' not in a and 'experimental-clean-photon-rebuild' not in a
 print('PASS 26903 actual B Night exposure/frame capture/RAW/DNG/Jin/50MP owner isolation and 26902 B zoom invariants')

def check_patch(base,cand,forward,rollback):
 forward=forward.resolve();rollback=rollback.resolve()
 old,act,allow=valid_candidate(base,cand)
 assert Path(forward).read_bytes()==(R/PATCH[0]).read_bytes()
 assert Path(rollback).read_bytes()==(R/PATCH[1]).read_bytes()
 assert (R/PATCH[0]).read_bytes().count(b'diff --git')==len(allow)
 assert (R/PATCH[1]).read_bytes().count(b'diff --git')==len(allow)
 with tempfile.TemporaryDirectory(prefix='p26903-real_patch_') as td:
  t=Path(td)
  for x in allow:
   if x in old:
    p=t/x;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(old[x],p)
  for abbrev in (7,12,40):
   # Exact four operands; core.abbrev doesn't change actual full SHA index evidence
   cmd=['git','-c',f'core.abbrev={abbrev}','apply','--unidiff-zero','--whitespace=nowarn']
   for patch in (forward,rollback):
    subprocess.run([*cmd,'--check',str(patch)],cwd=t,check=True,capture_output=True)
    subprocess.run([*cmd,str(patch)],cwd=t,check=True,capture_output=True)
    state=act if patch==forward else old
    assert all((t/x).is_file() and SHA(t/x)==SHA(state[x]) for x in state if x in allow)
    assert all(not (t/x).exists() for x in allow if x not in state)
 print('PASS 26903 actual full-index 4 operand binary forward/rollback 7/12/40 fuzz=0')

def tamper(base,cand):
 _,_,allow=valid_candidate(base,cand)
 old=manifest('26903_BASE_FULL_APP.sha256')
 with tempfile.TemporaryDirectory(prefix='26903_tamper_') as td:
  root=Path(td)
  # Test real copied current source state, no fixtures.
  for typ,path in [('protected',next(p for p in old if p not in allow and p.endswith('.java'))),
                   ('runtime',allow[0]),('version','app/version.properties')]:
   t=root/typ;shutil.copytree(cand,t)
   f=t/path; f.write_bytes(f.read_bytes()+b'\nTAMPER\n')
   try:valid_candidate(base,t)
   except AssertionError:pass
   else:fail('tamper accepted '+typ)
  t=root/'unexpected';shutil.copytree(cand,t)
  p=t/'app/src/main/java/unexpected/HiddenRegression.java';p.parent.mkdir(parents=True,exist_ok=True);p.write_text('class HiddenRegression {}')
  try:valid_candidate(base,t)
  except AssertionError:pass
  else:fail('unexpected runtime addition accepted')
  t=root/'missing';shutil.copytree(cand,t)
  (t/allow[0]).unlink()
  try:valid_candidate(base,t)
  except AssertionError:pass
  else:fail('missing modified source accepted')
 print('PASS 26903 actual-source protected/current/version/extra/missing tamper rejection')

def shader(p):
 data=p.read_text();assert data.startswith('#version 310 es')
 assert len(data)>15000 and 'void main()' in data
 # Simple transparent identifier scan is not a real compiler.
 stripped=re.sub(r'/\*.*?\*/|//[^\n]*',' ',data,flags=re.S)
 forbidden={'sample','input','output','texture2D','half','fixed','double','atomic_uint'}
 for m in re.finditer(r'(?m)\b(?:float|vec[234]|mat[234]|int|ivec[234]|bool|sampler2D)\s+([A-Za-z_]\w*)',stripped):
  assert m.group(1) not in forbidden,('ESSL reserved',m.group(1))
 assert 'uNightBJinEnabled' in data and 'uNightBJinReference' in data
 print('PASS 26903 exact expanded ESSL310 static identifier and shader-semantic scan; GLSLANG REAL compile required Actions')

def main():
 assert len(sys.argv)>=2,'usage: verify_26903.py candidate|semantics|patch|tamper|shader ...'
 mode=sys.argv[1]
 if mode=='shader':assert len(sys.argv)==3;shader(Path(sys.argv[2]));return
 if mode in ('candidate','semantics','tamper'):
  assert len(sys.argv) in (4,5) and (len(sys.argv)==4 or sys.argv[4]=='--transform')
  base,cand=map(Path,sys.argv[2:4]);
  if mode=='candidate':valid_candidate(base,cand,len(sys.argv)==5);print('PASS exact successful 26902 authority -> frozen 26903 candidate 2027, 13 allow, 2014 protected, +1 -0')
  elif mode=='semantics':source_semantics(base,cand)
  else:tamper(base,cand)
 elif mode=='patch':
  assert len(sys.argv)==6,'26903 patch validator EXACT four arguments base/candidate/forward/rollback'
  check_patch(Path(sys.argv[2]),Path(sys.argv[3]),Path(sys.argv[4]),Path(sys.argv[5]))
 else:fail('unknown 26903 validator mode '+mode)
if __name__=='__main__':main()
