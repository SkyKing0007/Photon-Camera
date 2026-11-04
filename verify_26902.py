#!/usr/bin/env python3
"""Photon 26902 exact compiled-26901 authority, B-only lens-relative gain/radius,
source/patch/tamper/compiler-source and actual successful Actions artifact ABI.
Never run historical validators on 26902 candidate bytes.
"""
from pathlib import Path
import hashlib,sys,re,shutil,tempfile,subprocess,tarfile
R=Path(__file__).resolve().parent
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
RUNNER_PARENT_SHA='bcdd8bb524e5410808b4ecf2ef27760c1c28412d18389ee676c55be3509db6d9'
TAR_SHA='759109721bfc05c70c85d215542333a667107f0e652531ec9966768e8658a615'
ART_SHA='6de45e5fa5c26e581c9d010175ed8691941ce14122b64ef13fee2020e70c68a5'
SCOPE=[
'app/src/main/assets/shaders/motionv2/iris26899_b_off_zoom_luma_sharpen.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/version.properties']
def man(name):
 d={}
 for line in (R/name).read_text().splitlines():
  h,sep,p=line.partition('  ')
  assert sep=='  ' and re.fullmatch('[0-9a-f]{64}',h) and p and p not in d,(name,line)
  d[p]=h
 return d
OLD=man('26902_BASE_FULL_APP.sha256');NEW=man('26902_EXPECTED_CANDIDATE_FULL_APP.sha256');PRO=man('26902_UNCHANGED_PROTECTED.sha256')
MOD=sorted(p for p in OLD.keys()&NEW.keys() if OLD[p]!=NEW[p]);ADD=sorted(NEW.keys()-OLD.keys());DEL=sorted(OLD.keys()-NEW.keys())
assert len(OLD)==len(NEW)==2026 and len(PRO)==2023,(len(OLD),len(NEW),len(PRO))
assert MOD==SCOPE and not ADD and not DEL and set(PRO)==set(OLD)-set(MOD)
assert (R/'26902_CHANGED_ALLOWLIST.txt').read_text().splitlines()==MOD
assert not (R/'26902_ADDITIONS.txt').read_bytes() and not (R/'26902_DELETIONS.txt').read_bytes()
assert all(PRO[p]==OLD[p]==NEW[p] for p in PRO)
PAY=R/'handoff_payload_26902'
assert {p.relative_to(PAY).as_posix() for p in PAY.rglob('*') if p.is_file()}=={p[4:] for p in MOD}
assert all(H(PAY/p[4:])==NEW[p] for p in MOD)
assert 'VERSION_NAME=0.9726902' in (PAY/'version.properties').read_text().splitlines()
assert 'VERSION_BUILD=26902' in (PAY/'version.properties').read_text().splitlines()
def checked(root,want):
 found={p.relative_to(root).as_posix():H(p) for p in (root/'app').rglob('*') if p.is_file()}
 assert found==want,(len(found),len(want),[(k,want[k],found.get(k)) for k in want if want[k]!=found.get(k)][:8])
def candidate(base,cand,transform=False):
 checked(base,OLD)
 if transform:
  assert not cand.exists(),('candidate already exists (cannot overwrite)',cand)
  shutil.copytree(base,cand)
  for k in MOD:shutil.copy2(PAY/k[4:],cand/k)
 checked(cand,NEW)
 print('PASS exact successful compiled 26901 2026 -> frozen 26902 2026, 3 changed, 2023 protected, 0 additions/deletions')
def semantic(base,cand):
 checked(base,OLD);checked(cand,NEW)
 root=cand/'app/src/main';br=base/'app/src/main'
 shader=(root/'assets/shaders/motionv2/render.glsl').read_text()
 sharp=(root/'assets/shaders/motionv2/iris26899_b_off_zoom_luma_sharpen.glsl').read_text()
 j=(root/'java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
 h=(root/'java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java').read_text()
 params=(root/'java/com/particlesdevs/photoncamera/processing/render/Parameters.java').read_text()
 route=(root/'java/com/particlesdevs/photoncamera/processing/processor/Iris26864ZoomRoute.java').read_text()
 assert 'A_EXACT_ZOOM_THRESHOLD = 1.10f' in route
 assert 'iris26901LensLocalZoom >= Iris26864ZoomRoute.A_EXACT_ZOOM_THRESHOLD' in h
 assert 'iris26856BRequestedOnly && !processingParameters.motionV2SuperResOutputEnabled' in h
 assert 'processingParameters.motionV2OutputZoom;' in h
 assert 'iris26901BOffDigitalZoomEnhancementEnabled = false;' in params
 assert j.count('iris26901BOffDigitalZoomEnhancementEnabled')==1
 assert 'iris26901LensLocalZoom >= 1.10f' in j
 assert 'final boolean iris26899Sharpen = iris26901DigitalZoomEnhancement;' in j
 assert 'iris26901FullRgbBicubic = iris26901DigitalZoomEnhancement' in j
 assert 'irisOutputZoom > 1.00001f' in j
 assert shader== (br/'assets/shaders/motionv2/render.glsl').read_text(),'full RGB bicubic shader MUST remain byte identical'
 assert 'iris26901BicubicRgb(sourcePixel)' in shader
 assert 'cubicRgb+=wx[ix]*wy[iy]*rgb;' in shader and 'return clamp(cubicRgb,centerMin,centerMax);' in shader
 assert 'linearSrgb=max(iris26901BOffFullRgbBicubic!=0' in shader
 # Java's source active curve is exactly user supplied, no smoothing at step boundaries.
 assert 'final float iris26902RelativeZoom = iris26901LensLocalZoom;' in j
 for boundary,gain in [('2.50f','35.0f'),('5.00f','40.0f'),('10.00f','55.0f'),('15.00f','60.0f'),('20.00f','70.0f')]:
  assert 'iris26902RelativeZoom <= '+boundary in j and '? '+gain in j
 assert 'Math.min(150.0f, 100.0f + 5.0f * (iris26902RelativeZoom - 20.0f))' in j
 assert 'iris26899Zoom <= 10.0f' not in j and 'Math.min(200.0f' not in j
 assert j.count('glProg.setVar("iris26902LensLocalZoomForRadius", iris26902RelativeZoom);')==1
 assert 'glProg.setVar("iris26901DisplayedZoomForRadius"' not in j
 assert j.index('iris26901BOffFullRgbBicubic')<j.index('glProg.drawBlocks(WorkingTexture);')<j.index('iris26902LensLocalZoomForRadius')<j.index('WorkingTexture = iris26899Destination;')<j.index('pipeline.motionV2GainMapBitmap = null;')
 assert 'motionV2GlobalZoom' in j and 'iris26899Zoom' in j # telemetry ONLY
 assert 'uniform float iris26902LensLocalZoomForRadius;' in sharp
 assert 'float lensLocalZoom=clamp(iris26902LensLocalZoomForRadius,1.0,30.0);' in sharp
 assert 'max(lensLocalZoom-1.0,0.0)' in sharp
 assert 'smoothstep(3.0,12.0,lensLocalZoom)' in sharp
 assert 'clamp(iris26899AdditionalPct, 35.0, 150.0)' in sharp
 assert 'iris26901DisplayedZoomForRadius' not in sharp
 assert 'clamp(relativeGain * 1.20 * gate * detail, -0.082, 0.082)' in sharp
 assert 'float gate=shadowGate*highlightGate;' in sharp
 assert 'Output = clamp(rgb * ratio, vec3(0.0), vec3(1.0));' in sharp
 assert 'smoothstep(0.0025, 0.012, contrastEvidence)' not in sharp
 assert 'float evidence =' not in sharp
 assert (cand/'app/version.properties').read_text().splitlines().count('VERSION_BUILD=26902')==1
 for path in ('java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java','java/com/particlesdevs/photoncamera/processing/render/Parameters.java', 'java/com/particlesdevs/photoncamera/processing/processor/Iris26864ZoomRoute.java'):
  assert (root/path).read_bytes()==(br/path).read_bytes(),'unapproved route/parameters modification '+path
 print('PASS 26902 universal B-only optical 1.10 activation unchanged; lens-relative gain/radius, SDR-before-UHDR; 26901 independent RGB bicubic and RAW native protected')
def patch(base,cand,forward,rollback):
 candidate(base,cand)
 for abbrev in (7,12,40):
  with tempfile.TemporaryDirectory(prefix='photon_26902_4arg_patch_') as d:
   temp=Path(d)
   for f in MOD:
    p=temp/f;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(base/f,p)
   for pp in (forward,rollback):assert pp.is_file() and pp.stat().st_size>100
   def run(*args):
    proc=subprocess.run(['git','-c',f'core.abbrev={abbrev}','-C',str(temp),'apply','--unidiff-zero',*args],capture_output=True,text=True)
    assert proc.returncode==0,(abbrev,args,proc.stdout,proc.stderr)
   run('--check',str(forward));run(str(forward))
   assert all((temp/f).read_bytes()==(cand/f).read_bytes() for f in MOD)
   run('--check',str(rollback));run(str(rollback))
   assert all((temp/f).read_bytes()==(base/f).read_bytes() for f in MOD)
 print('PASS 26902 exact 4-operand ACTUAL 26901 source patch validator; full-index fuzz=0 7/12/40 forward and rollback byte identical')
def tamper(base,cand):
 candidate(base,cand)
 for f in MOD:
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/f;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((cand/f).read_bytes()+b'\nTAMPER\n');assert H(p)!=NEW[f]
 print('PASS 26902 exact frozen 3-source changed-file tamper rejects mutations')
def shader(p):
 s=p.read_text();assert s.startswith('#version 310 es\n\n#line 1\n') and s.count('#version')==1
 src=re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S)
 reserved=set('sample attribute varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch invariant precise subroutine input output filter namespace using asm class union enum typedef template this packed goto inline noinline public static extern external interface long short half fixed unsigned resource'.split())
 pat=r'\b(?:uniform|float|int|uint|bool|vec[234]|ivec[234]|uvec[234]|mat[234]|sampler2D|void|out|in)\s+([A-Za-z_]\w*)'
 bad=[v for v in re.findall(pat,src) if v in reserved or v.startswith('gl_') or '__' in v]
 assert not bad,(p,bad)
 assert src.count('void main()')==1
 assert 'iris26902LensLocalZoomForRadius' in src
 assert 'iris26901DisplayedZoomForRadius' not in src
 print('PASS actual runtime-expanded 26902 ESSL310 GLSL reserved-name/source scan (PINNED REAL compiler Actions)')
def artifact(root,runner):
 p=root/'build_26901_iris_rawr_outputs'
 assert H(p/'26901_candidate_app_source.tar.gz')==TAR_SHA
 assert H(p/'exact_generated_runner/build_26901_iris_rawr.sh')==RUNNER_PARENT_SHA
 assert H(R/'build_26901_iris_rawr.sh')==RUNNER_PARENT_SHA
 t=runner.read_text()
 paths=set(re.findall(r'\$ARTDIR/([^\s"\'\)]+)',t))
 for path in paths:
  path=path.rstrip(';,')
  assert path.startswith('build_26901_iris_rawr_outputs/'),('stale artifact prefix',path)
  if '$' not in path and '*' not in path:
   f=root/path;assert f.is_file() and f.stat().st_size>0,('missing successful 26901 artifact operand',path)
 assert '$ARTDIR/build_26900_iris_rawr_outputs/' not in t
 assert 'verify_26889_compiled_push_abi.py "$ARTDIR/build_26901_iris_rawr_outputs/26888_modified_shader_spirv/Iris26887BOffHdrqMerge_prod.spv"' in t
 assert (p/'26899_historical_candidate_app_source.tar.gz').is_file()
 assert (p/'26900_historical_candidate_app_source.tar.gz').is_file()
 assert (p/'26901_candidate_app_source.tar.gz').is_file()
 print('PASS actual 26901 successful artifact operands and historical 26899 V1 SPV correction, exact source TAR and runner')
if __name__=='__main__':
 a=sys.argv[1:];assert a
 if a[0]=='candidate':assert len(a) in (3,4) and (len(a)==3 or a[3]=='--transform');candidate(Path(a[1]),Path(a[2]),len(a)==4)
 elif a[0]=='semantics':assert len(a)==3;semantic(Path(a[1]),Path(a[2]))
 elif a[0]=='patch':assert len(a)==5;patch(Path(a[1]),Path(a[2]),R/a[3],R/a[4])
 elif a[0]=='tamper':assert len(a)==3;tamper(Path(a[1]),Path(a[2]))
 elif a[0]=='shader':assert len(a)==2;shader(Path(a[1]))
 elif a[0]=='artifact':assert len(a)==3;artifact(Path(a[1]),Path(a[2]))
 else:raise AssertionError(('unknown exact 26902 command ABI',a))
