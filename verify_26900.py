#!/usr/bin/env python3
"""Photon 26900: exact successful 26899 V2 bytes, scoped B/OFF shader, real patch CLI.

Validators must execute on actual successful parent and actual candidate bytes; no
synthetic substitute for source identity. Historical 26899 is independently replayed
with its own frozen successful 26898 source by its original unchanged validator.
"""
from pathlib import Path
import hashlib,re,sys,shutil,tempfile,subprocess
R=Path(__file__).resolve().parent
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
RUNNER_PARENT_SHA='a253dd089fdbdb9fc0829d165a42a1645b35405427f8ae369cfa1e08233331d7'
TAR_SHA='b468173a2eae7100f3180b8a178e37961dc1c0465560fad90113e8181507c80f'
ART_SHA='de648a61f7c4639c84c384d2ff6cbec1d057d9377cb1b47a52e0d5bc34036ff9'
SCOPE=['app/src/main/assets/shaders/motionv2/iris26899_b_off_zoom_luma_sharpen.glsl','app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','app/version.properties']
def manifest(name):
 d={}
 for line in (R/name).read_text().splitlines():
  h,sep,p=line.partition('  ')
  assert sep=='  ' and re.fullmatch('[0-9a-f]{64}',h) and p and p not in d,(name,line)
  d[p]=h
 return d
OLD=manifest('26900_BASE_FULL_APP.sha256');NEW=manifest('26900_EXPECTED_CANDIDATE_FULL_APP.sha256');PRO=manifest('26900_UNCHANGED_PROTECTED.sha256')
MOD=sorted(k for k in OLD.keys()&NEW.keys() if OLD[k]!=NEW[k]);ADD=sorted(NEW.keys()-OLD.keys());DEL=sorted(OLD.keys()-NEW.keys())
assert len(OLD)==len(NEW)==2026 and len(PRO)==2022,(len(OLD),len(NEW),len(PRO))
assert MOD==SCOPE and not ADD and not DEL
assert MOD==(R/'26900_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert not (R/'26900_ADDITIONS.txt').read_bytes() and not (R/'26900_DELETIONS.txt').read_bytes()
assert set(PRO)==set(OLD)-set(MOD) and all(OLD[k]==NEW[k]==PRO[k] for k in PRO)
PAY=R/'handoff_payload_26900'
assert {p.relative_to(PAY).as_posix() for p in PAY.rglob('*') if p.is_file()}=={p[4:] for p in MOD}
assert all(H(PAY/p[4:])==NEW[p] for p in MOD)
assert 'VERSION_NAME=0.9726900' in (PAY/'version.properties').read_text().splitlines() and 'VERSION_BUILD=26900' in (PAY/'version.properties').read_text().splitlines()
def checked(root,manifest):
 files={p.relative_to(root).as_posix():H(p) for p in (root/'app').rglob('*') if p.is_file()}
 assert files==manifest,(len(files),len(manifest),[(p,manifest[p],files.get(p)) for p in manifest if files.get(p)!=manifest[p]][:6])
def candidate(base,cand,transform=False):
 checked(base,OLD)
 if transform:
  assert not cand.exists(),('refuse overwriting frozen candidate',cand)
  shutil.copytree(base,cand)
  for k in MOD:
   dst=cand/k;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(PAY/k[4:],dst)
 checked(cand,NEW)
 print('PASS 26900 actual successful 26899 2026 -> 26900 2026; 4 exact existing changed, zero add/delete, 2022 protected')
def src(cand,name):return (cand/'app/src/main/assets/shaders/motionv2'/name).read_text()
def semantic(base,cand):
 checked(base,OLD);checked(cand,NEW)
 render=src(cand,'render.glsl');sharp=src(cand,'iris26899_b_off_zoom_luma_sharpen.glsl')
 original_render=src(base,'render.glsl');original_sharp=src(base,'iris26899_b_off_zoom_luma_sharpen.glsl')
 j=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
 oldj=(base/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
 assert 'IRIS_26900_B_FROZEN_OFF_BICUBIC_LUMA_RESAMPLE' in render and 'uniform int iris26900BOffBicubic;' in render
 assert render.count('iris26900BicubicLumaPreserveChroma(sourcePixel)')==1
 assert render.count('iris26524BilinearInput(sourcePixel)')==1
 assert 'iris26900BOffBicubic!=0' in render and 'iris26718HighZoomLogDetail(sourcePixel)' in render
 assert render.index('iris26900BicubicLumaPreserveChroma(sourcePixel)')<render.index('iris26718HighZoomLogDetail(sourcePixel)')
 assert all(x in render for x in ('iris26900CubicWeights','for(int iy=0;iy<4;iy++)','for(int ix=0;ix<4;ix++)','localMin=min(localMin,y)','localMax=max(localMax,y)','float targetY=clamp(cubicY,localMin,localMax)','bilinear*(max(targetY,0.0)/baseY)'))
 assert render.count('uniform int iris26900BOffBicubic;')==1
 assert len(render)>len(original_render) and render.count('void main()')==1
 assert 'uniform float iris26900RenderPixelScale;' in sharp and sharp.count('uniform float iris26899AdditionalPct;')==1
 assert 'int radius=int(clamp(floor(1.0+0.80*max(physicalScale-1.0,0.0)+0.5),2.0,24.0));' in sharp
 assert 'iris26900RenderPixelScale' in sharp and 'iris26899AdditionalPct' in sharp
 assert 'float mediumWeight=mix(0.26,0.50,smoothstep(3.0,12.0,physicalScale));' in sharp
 assert 'clamp(relativeGain * 1.20 * gate * detail, -0.082, 0.082)' in sharp
 assert 'Output = clamp(rgb * ratio, vec3(0.0), vec3(1.0));' in sharp
 assert 'smoothstep(0.0025, 0.012, contrastEvidence)' not in sharp and 'float evidence =' not in sharp
 assert 'float gate=shadowGate*highlightGate;' in sharp
 assert j.count('glProg.setVar("iris26900BOffBicubic",')==1
 fragment=j[j.index('glProg.setVar("iris26900BOffBicubic",'):][:730]
 assert all(x in fragment for x in ('iris26899BOffZoomSharpenEnabled','motionV2Active','!basePipeline.mParameters.irisNightActive', '!basePipeline.mParameters.motionV2SuperResOutputEnabled', 'Float.isFinite(basePipeline.mParameters.motionV2GlobalZoom)', 'motionV2GlobalZoom >= 1.10f', 'irisOutputZoom > 1.00001f'))
 assert j.count('glProg.setVar("iris26900RenderPixelScale", irisOutputZoom);')==1
 assert j.index('glProg.setVar("iris26900BOffBicubic",')<j.index('glProg.drawBlocks(WorkingTexture);')
 assert j.index('glProg.setVar("iris26900RenderPixelScale", irisOutputZoom);')>j.index('glProg.drawBlocks(WorkingTexture);')
 assert j.index('glProg.setVar("iris26900RenderPixelScale", irisOutputZoom);')<j.index('WorkingTexture = iris26899Destination;')
 assert j.count('useAssetProgram("motionv2/iris26899_b_off_zoom_luma_sharpen")')==1
 assert 'iris26899Zoom <= 10.0f' in j and 'iris26899Zoom <= 20.0f' in j and 'Math.min(200.0f' in j
 assert 'iris26899AdditionalPct' in j and j.count('iris26899BOffZoomSharpenEnabled')>=2
 assert j.index('WorkingTexture = iris26899Destination;')<j.index('pipeline.motionV2GainMapBitmap = null;')
 # Enforce zero changes to everything outside exactly the bounded shader and renderer owner.
 assert all('cpp/' not in k and 'Dng' not in k and 'DNG' not in k for k in MOD)
 assert not any(k.startswith('app/src/main/java/com/hinnka/') for k in MOD)
 assert 'VERSION_BUILD=26899' in (base/'app/version.properties').read_text()
 assert 'VERSION_BUILD=26900' in (cand/'app/version.properties').read_text()
 # Exact global strength owner intact, no duplicate CPU or GPU copy stage.
 for x in ['iris26899Zoom <= 10.0f','100.0f + 5.0f * (iris26899Zoom - 10.0f)','150.0f + 5.0f * (iris26899Zoom - 20.0f)']:
  assert x in j
 assert oldj.count('glProg.drawBlocks(WorkingTexture);')==j.count('glProg.drawBlocks(WorkingTexture);')
 print('PASS 26900 B shutter frozen SR-OFF >=1.10, actual software scale, luma Catmull-Rom and aggressive 26899 curve; source domains protected')
def patch(base,cand,forward,back):
 candidate(base,cand)
 for abbrev in (7,12,40):
  with tempfile.TemporaryDirectory(prefix='photon_26900_real_patch_') as d:
   t=Path(d)
   for k in MOD:
    p=t/k;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(base/k,p)
   for pp in (forward,back):
    assert pp.is_file() and pp.stat().st_size>100
   def cmd(*args):
    p=subprocess.run(['git','-c',f'core.abbrev={abbrev}','-C',str(t),'apply',*args],capture_output=True,text=True)
    assert p.returncode==0,(abbrev,args,p.stderr)
   cmd('--check','--unidiff-zero',str(forward));cmd('--unidiff-zero',str(forward))
   assert all((t/k).read_bytes()==(cand/k).read_bytes() for k in MOD)
   cmd('--check','--unidiff-zero',str(back));cmd('--unidiff-zero',str(back))
   assert all((t/k).read_bytes()==(base/k).read_bytes() for k in MOD)
 print('PASS 26900 original 4-argument exact runner patch CLI, full-index forward and rollback, abbrev 7/12/40, fuzz=0, byte-perfect reversal')
def tamper(base,cand):
 candidate(base,cand)
 for f in MOD:
  with tempfile.TemporaryDirectory(prefix='photon_26900_tamper_') as d:
   t=Path(d);cp=t/f;cp.parent.mkdir(parents=True,exist_ok=True);cp.write_bytes((cand/f).read_bytes()+b'\n// forbidden mutation\n')
   assert H(cp)!=NEW[f]
 print('PASS 26900 negative tamper on all 4 modified real source files')
def shader(p):
 s=p.read_text();assert s.startswith('#version 310 es\n\n#line 1\n')
 t=re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S)
 for word in ('sample','input','output','filter','attribute','varying'):
  assert not re.search(r'\b'+word+r'\b',t),(p,word)
 assert t.count('void main()')==1
 print('PASS exact expanded ESSL310 full modified shader reserved-name scan:',p.name)
def artifact(root,runner):
 assert H(root/'build_26899_iris_rawr_outputs/26899_candidate_app_source.tar.gz')==TAR_SHA
 assert H(root/'build_26899_iris_rawr_outputs/exact_generated_runner/build_26899_iris_rawr.sh')==RUNNER_PARENT_SHA
 assert H(R/'build_26899_iris_rawr.sh')==RUNNER_PARENT_SHA
 t=runner.read_text()
 # Catch ANY stale artifact path whose exact counterpart isn't in the successful 26899 ZIP.
 paths=set(re.findall(r'\$ARTDIR/([^\s\"\'\)]+)',t))
 for path in paths:
  path=path.rstrip(';,')
  assert path.startswith('build_26899_iris_rawr_outputs/'),('stale artifact output prefix',path)
  if '$' not in path and '*' not in path:
   pp=root/path
   assert pp.is_file() and pp.stat().st_size>0,('missing from successful 26899 V2 artifact',path)
 for path in ['26888_modified_shader_spirv/Iris26887BOffHdrqMerge_prod.spv','26898_historical_candidate_app_source.tar.gz','26897_historical_candidate_app_source.tar.gz']:
  assert (root/'build_26899_iris_rawr_outputs'/path).is_file(),path
 assert 'verify_26889_compiled_push_abi.py "$ARTDIR/build_26899_iris_rawr_outputs/26888_modified_shader_spirv/Iris26887BOffHdrqMerge_prod.spv"' in t
 assert '$ARTDIR/build_26898_iris_rawr_outputs/' not in t and '$ARTDIR/build_26897_iris_rawr_outputs/' not in t
 print('PASS 26900 all real successful 26899 artifact file operands and historical 26899 V1 stale-path negative')
if __name__=='__main__':
 a=sys.argv[1:];assert a
 if a[0]=='candidate':assert len(a) in (3,4) and (len(a)==3 or a[3]=='--transform');candidate(Path(a[1]),Path(a[2]),len(a)==4)
 elif a[0]=='semantics':assert len(a)==3;semantic(Path(a[1]),Path(a[2]))
 elif a[0]=='patch':assert len(a)==5;patch(Path(a[1]),Path(a[2]),R/a[3],R/a[4])
 elif a[0]=='tamper':assert len(a)==3;tamper(Path(a[1]),Path(a[2]))
 elif a[0]=='shader':assert len(a)==2;shader(Path(a[1]))
 elif a[0]=='artifact':assert len(a)==3;artifact(Path(a[1]),Path(a[2]))
 else:raise AssertionError(('unknown exact 26900 CLI',a))
