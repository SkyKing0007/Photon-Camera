#!/usr/bin/env python3
"""Actual 26898 compiled source -> 26899 B-only SR-OFF zoom sharpen byte and mode gate."""
from pathlib import Path
import sys, hashlib, re, subprocess, shutil, tempfile
R=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(name):
 d={}
 for line in (R/name).read_text().splitlines():
  h,x=line.split('  ',1)
  assert re.fullmatch('[0-9a-f]{64}',h) and x not in d
  d[x]=h
 return d
OLD=manifest('26899_BASE_FULL_APP.sha256')
NEW=manifest('26899_EXPECTED_CANDIDATE_FULL_APP.sha256')
PRO=manifest('26899_UNCHANGED_PROTECTED.sha256')
MOD=sorted(k for k in OLD.keys() & NEW.keys() if OLD[k]!=NEW[k])
ADD=sorted(NEW.keys()-OLD.keys())
DEL=sorted(OLD.keys()-NEW.keys())
ALLOW=sorted(MOD+ADD)
assert len(OLD)==2025 and len(NEW)==2026 and len(PRO)==2021
assert MOD==[
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
'app/version.properties']
assert ADD==['app/src/main/assets/shaders/motionv2/iris26899_b_off_zoom_luma_sharpen.glsl']
assert not DEL
assert ALLOW==(R/'26899_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert ADD==(R/'26899_ADDITIONS.txt').read_text().splitlines()
assert not (R/'26899_DELETIONS.txt').read_bytes()
assert set(PRO)==set(OLD)-set(MOD)
assert all(OLD[k]==NEW[k]==v for k,v in PRO.items())
PAY=R/'handoff_payload_26899'
assert {q.relative_to(PAY).as_posix() for q in PAY.rglob('*') if q.is_file()}=={p[4:] for p in ALLOW}
assert all(sha(PAY/p[4:])==NEW[p] for p in ALLOW)
assert 'VERSION_NAME=0.9726899' in (PAY/'version.properties').read_text()
assert 'VERSION_BUILD=26899' in (PAY/'version.properties').read_text()
def checked(root,m):
 got={p.relative_to(root).as_posix():sha(p) for p in (root/'app').rglob('*') if p.is_file()}
 assert got==m,(len(got),len(m),[(p,m[p],got.get(p)) for p in m if got.get(p)!=m[p]][:8])
def candidate(base,cand,transform):
 checked(base,OLD)
 if transform:
  assert not cand.exists(),('unsafe overwrite',cand)
  shutil.copytree(base,cand)
  for p in ALLOW:
   q=cand/p;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(PAY/p[4:],q)
 checked(cand,NEW)
 print('PASS actual compiled 26898 2025 -> frozen 26899 2026, exactly 4 modified + one added shader, 2021 protected')
def semantics(base,cand):
 checked(base,OLD);checked(cand,NEW)
 P='app/src/main/java/com/particlesdevs/photoncamera/processing/'
 p=(cand/(P+'render/Parameters.java')).read_text()
 h=(cand/(P+'processor/HdrxProcessor.java')).read_text()
 r=(cand/(P+'opengl/postpipeline/MotionV2Render.java')).read_text()
 g=(cand/'app/src/main/assets/shaders/motionv2/iris26899_b_off_zoom_luma_sharpen.glsl').read_text()
 assert p.count('public boolean iris26899BOffZoomSharpenEnabled = false;')==1
 assert h.count('processingParameters.iris26899BOffZoomSharpenEnabled =')==1
 fragment=h[h.index('processingParameters.iris26899BOffZoomSharpenEnabled ='):][:350]
 assert all(x in fragment for x in ('iris26856BRequestedOnly','!processingParameters.motionV2SuperResOutputEnabled',
 'Float.isFinite(iris26899GlobalZoom)', 'iris26899GlobalZoom >= 1.10f'))
 assert h.count('iris26856FrozenMode == Iris26856ABSettings.Mode.AMAZE_26855')>=1
 assert h.index('processingParameters.motionV2GlobalZoom = mMotion26524GlobalZoom')<h.index('processingParameters.iris26899BOffZoomSharpenEnabled =')
 assert r.count('basePipeline.mParameters.iris26899BOffZoomSharpenEnabled')==1
 assert all(x in r for x in ('basePipeline.mParameters.motionV2Active','!basePipeline.mParameters.irisNightActive',
 '!basePipeline.mParameters.motionV2SuperResOutputEnabled',
 'Float.isFinite(iris26899Zoom)', 'iris26899Zoom >= 1.10f',
 'iris26899Zoom <= 10.0f', '100.0f + 5.0f * (iris26899Zoom - 10.0f)',
 '150.0f + 5.0f * (iris26899Zoom - 20.0f)', 'Math.min(200.0f'))
 assert r.count('useAssetProgram("motionv2/iris26899_b_off_zoom_luma_sharpen")')==1
 assert r.index('glProg.drawBlocks(WorkingTexture);\n            /* IRIS_26899_B_OFF_ONLY_FINAL_SDR_EDGE_AWARE_LUMA_SHARPEN')<r.index('pipeline.motionV2GainMapBitmap = null;')
 assert 'new GLTexture(\n                        new Point(iris26899UnsharpenedSdr.mSize)' in r
 assert 'basePipeline.getMain();\n                if (iris26899Destination' not in r
 assert r.count('glProg.setVar("iris26899AdditionalPct", iris26899AdditionalPct)')==1
 assert all(x in g for x in ('uniform sampler2D InputBuffer;','uniform float iris26899AdditionalPct;',
 'out vec3 Output;', 'fineMean','mediumMean','evidence','shadowGate','highlightGate',
 'clamp(relativeGain * 1.20 * gate * detail, -0.082, 0.082)',
 'Output = clamp(rgb * ratio'))
 assert '#version' not in g # the runtime GLInterface injects exact #version 310 es
 assert not re.search(r'\b(sample|input|output)\s*[=;(\[]',g)
 # Original production output algorithms and any RAW/DNG/writers/other shaders
 # must be binary-identical. The added shader is a NEW, uniquely named owner.
 assert set(PRO)==set(OLD)-set(MOD)
 assert all(not x.startswith('app/src/main/cpp/') for x in MOD+ADD)
 assert all('Dng' not in x and 'DNG' not in x for x in MOD+ADD)
 print('PASS 26899 B frozen, SR OFF, >=1.10 GLOBAL zoom, only B output, 2-scale Y, SDR before existing UHDR gainmap')
def patch(base,cand,forward,rollback):
 checked(base,OLD);checked(cand,NEW)
 for n in (7,12,40):
  with tempfile.TemporaryDirectory(prefix='26899_replay_') as td:
   t=Path(td)
   for p in MOD:
    q=t/p;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(base/p,q)
   def apply(*a):
    proc=subprocess.run(['git','-c',f'core.abbrev={n}','-C',str(t),'apply',*a],capture_output=True,text=True)
    assert proc.returncode==0,(n,a,proc.stderr)
   apply('--check',str(forward));apply(str(forward))
   assert all((t/p).is_file() and (t/p).read_bytes()==(cand/p).read_bytes() for p in ALLOW)
   apply('--check',str(rollback));apply(str(rollback))
   assert all((t/p).is_file() and (t/p).read_bytes()==(base/p).read_bytes() for p in MOD)
   assert all(not (t/p).exists() for p in ADD)
 print('PASS 26899 ACTUAL full-index forward/rollback with one source addition, core.abbrev=7/12/40 fuzz=0 exact byte reversal')
def tamper(base,cand):
 checked(base,OLD);checked(cand,NEW)
 with tempfile.TemporaryDirectory(prefix='26899_bad_source_') as td:
  t=Path(td)/'c';shutil.copytree(cand,t)
  q=t/ADD[0];q.write_bytes(q.read_bytes()+b'\n// bad GLSL negative tamper\n')
  try:checked(t,NEW)
  except AssertionError:pass
  else:raise AssertionError('modified shader not detected')
  q.write_bytes((cand/ADD[0]).read_bytes())
  q=t/MOD[1];q.write_bytes(q.read_bytes()+b'\n// bad route negative tamper\n')
  try:checked(t,NEW)
  except AssertionError:pass
  else:raise AssertionError('modified routing not detected')
 print('PASS 26899 negative modified shader and B routing source tamper detected')
if __name__=='__main__':
 argv=sys.argv[1:];assert argv
 mode=argv[0]
 if mode=='candidate':
  assert len(argv) in (3,4) and (len(argv)==3 or argv[3]=='--transform')
  candidate(Path(argv[1]),Path(argv[2]),len(argv)==4)
 elif mode=='semantics':
  assert len(argv)==3;semantics(Path(argv[1]),Path(argv[2]))
 elif mode=='patch':
  assert len(argv)==5;patch(Path(argv[1]),Path(argv[2]),R/argv[3],R/argv[4])
 elif mode=='tamper':
  assert len(argv)==3;tamper(Path(argv[1]),Path(argv[2]))
 else:raise AssertionError(('unknown validator CLI',argv))
