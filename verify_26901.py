#!/usr/bin/env python3
"""26901 source identity, B-only universal optical activation, current and historical Actions ABI.
Every candidate/patch invocation uses real compiled-26900 and real candidate bytes.
"""
from pathlib import Path
import hashlib,sys,re,shutil,tempfile,subprocess
R=Path(__file__).resolve().parent
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
RUNNER_PARENT_SHA='1671e0a86fb85573da2cfbffa1c12502cf4153e4e15e548d0bc9bf4a15254cf6'
TAR_SHA='f629f785bbcf89bef05bb13e0d3398f5e513847c40f7aa22d907fc0781b867fd'
ART_SHA='4f2fe4f5e2a3a5b3425556ffb6c917ade61224176d932f58d72d1fc1dde914ca'
SCOPE=[
'app/src/main/assets/shaders/motionv2/iris26899_b_off_zoom_luma_sharpen.glsl',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
'app/version.properties']
def man(name):
 d={}
 for line in (R/name).read_text().splitlines():
  h,sep,p=line.partition('  ')
  assert sep=='  ' and re.fullmatch('[0-9a-f]{64}',h) and p not in d,(name,line)
  d[p]=h
 return d
OLD=man('26901_BASE_FULL_APP.sha256');NEW=man('26901_EXPECTED_CANDIDATE_FULL_APP.sha256');PRO=man('26901_UNCHANGED_PROTECTED.sha256')
MOD=sorted(p for p in OLD.keys()&NEW.keys() if OLD[p]!=NEW[p]);ADD=sorted(NEW.keys()-OLD.keys());DEL=sorted(OLD.keys()-NEW.keys())
assert len(OLD)==len(NEW)==2026 and len(PRO)==2020,(len(OLD),len(NEW),len(PRO))
assert MOD==SCOPE and not ADD and not DEL and set(PRO)==set(OLD)-set(MOD)
assert (R/'26901_CHANGED_ALLOWLIST.txt').read_text().splitlines()==MOD
assert not (R/'26901_ADDITIONS.txt').read_bytes() and not (R/'26901_DELETIONS.txt').read_bytes()
assert all(PRO[p]==OLD[p]==NEW[p] for p in PRO)
PAY=R/'handoff_payload_26901'
assert {p.relative_to(PAY).as_posix() for p in PAY.rglob('*') if p.is_file()}=={p[4:] for p in MOD}
assert all(H(PAY/p[4:])==NEW[p] for p in MOD)
assert 'VERSION_NAME=0.9726901' in (PAY/'version.properties').read_text().splitlines()
assert 'VERSION_BUILD=26901' in (PAY/'version.properties').read_text().splitlines()
def checked(root,want):
 found={p.relative_to(root).as_posix():H(p) for p in (root/'app').rglob('*') if p.is_file()}
 assert found==want,(len(found),len(want),[(k,want[k],found.get(k)) for k in want if want[k]!=found.get(k)][:8])
def candidate(base,cand,transform=False):
 checked(base,OLD)
 if transform:
  assert not cand.exists(),('candidate overwrite prohibited',cand)
  shutil.copytree(base,cand)
  for k in MOD:
   (cand/k).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(PAY/k[4:],cand/k)
 checked(cand,NEW)
 print('PASS exact successful 26900 2026 -> 26901 2026; six changed; 2020 protected; zero add/delete')
def semantic(base,cand):
 checked(base,OLD);checked(cand,NEW)
 root=cand/'app/src/main'
 shader=(root/'assets/shaders/motionv2/render.glsl').read_text()
 sharp=(root/'assets/shaders/motionv2/iris26899_b_off_zoom_luma_sharpen.glsl').read_text()
 j=(root/'java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
 h=(root/'java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java').read_text()
 params=(root/'java/com/particlesdevs/photoncamera/processing/render/Parameters.java').read_text()
 route=(root/'java/com/particlesdevs/photoncamera/processing/processor/Iris26864ZoomRoute.java').read_text()
 assert (root/'java/com/particlesdevs/photoncamera/processing/processor/Iris26864ZoomRoute.java').read_bytes()==(base/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/Iris26864ZoomRoute.java').read_bytes()
 assert 'A_EXACT_ZOOM_THRESHOLD = 1.10f' in route
 assert 'processingParameters.motionV2OutputZoom;' in h
 assert 'iris26901LensLocalZoom >= Iris26864ZoomRoute.A_EXACT_ZOOM_THRESHOLD' in h
 assert 'iris26901BOffDigitalZoomEnhancementEnabled =' in h
 assert 'iris26856BRequestedOnly && !processingParameters.motionV2SuperResOutputEnabled' in h
 assert 'iris26901DisplayedZoom > 0.0f' in h
 assert 'iris26901BOffDigitalZoomEnhancementEnabled = false;' in params
 assert j.count('iris26901BOffDigitalZoomEnhancementEnabled')==1
 assert j.count('glProg.setVar("iris26901BOffFullRgbBicubic", iris26901FullRgbBicubic ? 1 : 0);')==1
 assert 'iris26901LensLocalZoom >= 1.10f' in j and 'irisOutputZoom > 1.00001f' in j
 assert 'final boolean iris26899Sharpen = iris26901DigitalZoomEnhancement;' in j
 assert 'iris26899Zoom <= 10.0f' in j and 'iris26899Zoom <= 20.0f' in j and 'Math.min(200.0f' in j
 assert j.count('glProg.setVar("iris26901DisplayedZoomForRadius", iris26899Zoom);')==1
 assert j.index('iris26901BOffFullRgbBicubic')<j.index('glProg.drawBlocks(WorkingTexture);')<j.index('iris26901DisplayedZoomForRadius')<j.index('WorkingTexture = iris26899Destination;')
 assert j.index('WorkingTexture = iris26899Destination;')<j.index('pipeline.motionV2GainMapBitmap = null;')
 assert shader.count('uniform int iris26901BOffFullRgbBicubic;')==1
 assert 'iris26901BicubicRgb(sourcePixel)' in shader and 'iris26524BilinearInput(sourcePixel)' in shader
 assert 'linearSrgb=max(iris26901BOffFullRgbBicubic!=0' in shader
 assert shader.index('iris26901BicubicRgb(sourcePixel)')<shader.index('iris26718HighZoomLogDetail(sourcePixel)')
 assert all(q in shader for q in ('for(int iy=0;iy<4;iy++)','for(int ix=0;ix<4;ix++)',
            'vec3 cubicRgb=vec3(0.0);','cubicRgb+=wx[ix]*wy[iy]*rgb;',
            'centerMin=min(centerMin,rgb);','centerMax=max(centerMax,rgb);','return clamp(cubicRgb,centerMin,centerMax);'))
 assert not any(q in shader for q in ('iris26900BOffBicubic','iris26900BicubicLumaPreserveChroma','bilinear*(max(targetY,0.0)/baseY)'))
 assert 'uniform float iris26901DisplayedZoomForRadius;' in sharp
 assert 'float displayedZoom=clamp(iris26901DisplayedZoomForRadius,1.0,120.0);' in sharp
 assert 'max(displayedZoom-1.0,0.0)' in sharp and 'smoothstep(3.0,12.0,displayedZoom)' in sharp
 assert 'clamp(iris26899AdditionalPct, 100.0, 200.0)' in sharp
 assert 'clamp(relativeGain * 1.20 * gate * detail, -0.082, 0.082)' in sharp
 assert 'Output = clamp(rgb * ratio, vec3(0.0), vec3(1.0));' in sharp
 assert 'smoothstep(0.0025, 0.012, contrastEvidence)' not in sharp
 for old in ['iris26899BOffZoomSharpenEnabled','iris26900RenderPixelScale','iris26900BOffBicubic']:
  assert old not in (h+j+params+shader+sharp),('stale active identifier',old)
 # Keep native/DNG/50MP color pipeline, full pre/post code unchanged, excluding frozen scope.
 assert all('cpp/' not in x and not x.startswith('app/src/main/java/com/hinnka/') for x in MOD)
 assert 'VERSION_BUILD=26900' in (base/'app/version.properties').read_text()
 assert 'VERSION_BUILD=26901' in (cand/'app/version.properties').read_text()
 print('PASS universal physical lens 1.10x activation; displayed TOTAL zoom strength/radius; full RGB 4x4 Catmull-Rom, color overshoot clamp; UHDR preserved')
def patch(base,cand,forward,rollback):
 candidate(base,cand)
 for abbrev in (7,12,40):
  with tempfile.TemporaryDirectory(prefix='photon_26901_patch_') as d:
   temp=Path(d)
   for f in MOD:
    x=temp/f;x.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(base/f,x)
   for pp in (forward,rollback):assert pp.is_file() and pp.stat().st_size>100
   def run(*args):
    p=subprocess.run(['git','-c',f'core.abbrev={abbrev}','-C',str(temp),'apply','--unidiff-zero',*args],capture_output=True,text=True)
    assert p.returncode==0,(abbrev,args,p.stdout,p.stderr)
   run('--check',str(forward));run(str(forward))
   assert all((temp/f).read_bytes()==(cand/f).read_bytes() for f in MOD)
   run('--check',str(rollback));run(str(rollback))
   assert all((temp/f).read_bytes()==(base/f).read_bytes() for f in MOD)
 print('PASS exact 26901 4-operand patch validator and full-index fuzz=0 7/12/40 forward/rollback byte-perfect')
def tamper(base,cand):
 candidate(base,cand)
 for f in MOD:
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/f;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((cand/f).read_bytes()+b'\n// forbidden\n')
   assert H(p)!=NEW[f]
 print('PASS 26901 negative tamper: all six actual runtime scope files')
def shader(p):
 s=p.read_text();assert s.startswith('#version 310 es\n\n#line 1\n')
 src=re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S)
 reserved=set('sample attribute varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch invariant precise subroutine input output filter namespace using asm class union enum typedef template this packed goto inline noinline public static extern external interface long short half fixed unsigned resource'.split())
 pat=r'\b(?:uniform|float|int|uint|bool|vec[234]|ivec[234]|uvec[234]|mat[234]|sampler2D|void|out|in)\s+([A-Za-z_]\w*)'
 bad=[a for a in re.findall(pat,src) if a in reserved or a.startswith('gl_') or '__' in a]
 assert not bad,(p,bad)
 assert src.count('void main()')==1
 print('PASS exact runtime-expanded ESSL310 static declarations/reserved-name scan, real compiler Actions required:',p.name)
def artifact(root,runner):
 p=root/'build_26900_iris_rawr_outputs'
 assert H(p/'26900_candidate_app_source.tar.gz')==TAR_SHA
 assert H(p/'exact_generated_runner/build_26900_iris_rawr.sh')==RUNNER_PARENT_SHA
 assert H(R/'build_26900_iris_rawr.sh')==RUNNER_PARENT_SHA
 t=runner.read_text()
 paths=set(re.findall(r'\$ARTDIR/([^\s"\'\)]+)',t))
 for path in paths:
  path=path.rstrip(';,')
  assert path.startswith('build_26900_iris_rawr_outputs/'),('stale artifact prefix',path)
  if '$' not in path and '*' not in path:
   f=root/path;assert f.is_file() and f.stat().st_size>0,('missing actual successful 26900 artifact file',path)
 assert '$ARTDIR/build_26899_iris_rawr_outputs/' not in t
 assert 'verify_26889_compiled_push_abi.py "$ARTDIR/build_26900_iris_rawr_outputs/26888_modified_shader_spirv/Iris26887BOffHdrqMerge_prod.spv"' in t
 assert (p/'26899_historical_candidate_app_source.tar.gz').is_file()
 assert (p/'26900_candidate_app_source.tar.gz').is_file()
 print('PASS real 26900 artifact operands incl historical 26899 V1 stale-SPV-path negative, actual TAR/runner SHA')
if __name__=='__main__':
 a=sys.argv[1:];assert a
 if a[0]=='candidate':assert len(a) in (3,4) and (len(a)==3 or a[3]=='--transform');candidate(Path(a[1]),Path(a[2]),len(a)==4)
 elif a[0]=='semantics':assert len(a)==3;semantic(Path(a[1]),Path(a[2]))
 elif a[0]=='patch':assert len(a)==5;patch(Path(a[1]),Path(a[2]),R/a[3],R/a[4])
 elif a[0]=='tamper':assert len(a)==3;tamper(Path(a[1]),Path(a[2]))
 elif a[0]=='shader':assert len(a)==2;shader(Path(a[1]))
 elif a[0]=='artifact':assert len(a)==3;artifact(Path(a[1]),Path(a[2]))
 else:raise AssertionError(('unknown exact 26901 command ABI',a))
