#!/usr/bin/env python3
"""Frozen exact 26893 -> 26894 source, shader, numeric and four-argument binary patch gates."""
from pathlib import Path
import hashlib,shutil,subprocess,sys,tempfile,re,math,random
R=Path(__file__).resolve().parent
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(p):return {x.relative_to(p).as_posix():H(x) for x in p.rglob('*') if x.is_file() and '.git' not in x.parts}
def read(fn):
 out={}
 for line in (R/fn).read_text().splitlines():
  h,p=line.split('  ',1);assert p not in out;out[p]=h
 return out
old=read('26894_BASE_FULL_APP.sha256');new=read('26894_EXPECTED_CANDIDATE_FULL_APP.sha256');pro=read('26894_UNCHANGED_PROTECTED.sha256')
allowed=(R/'26894_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert len(old)==2025 and len(new)==2026 and len(pro)==2021
assert len(allowed)==5 and set(new)-set(old)=={'app/src/main/assets/shaders/motionv2/spatial_scene_26894.glsl'}
assert set(old)-set(new)==set()
assert sorted({p for p in set(new)|set(old) if old.get(p)!=new.get(p)})==allowed
assert set(pro)==set(old)-set(allowed) and all(old[k]==new[k]==v for k,v in pro.items())
assert (R/'26894_ADDITIONS.txt').read_text().splitlines()==['app/src/main/assets/shaders/motionv2/spatial_scene_26894.glsl']
assert (R/'26894_DELETIONS.txt').read_bytes()==b''

def candidate(base,cand,transform=False):
 assert manifest(base)==old,'actual compiled authority altered/extra/missing'
 if transform:
  assert not cand.exists();shutil.copytree(base,cand)
  for p in allowed:
   src=R/'handoff_payload_26894'/p.removeprefix('app/');dst=cand/p
   assert src.is_file() and H(src)==new[p]
   dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
 assert manifest(cand)==new,'exact 26894 frozen candidate / allowlist mismatch'
 assert all(H(cand/p)==h for p,h in pro.items())
 assert (cand/'app/version.properties').read_text().splitlines()[-2:]==['VERSION_NAME=0.9726894','VERSION_BUILD=26894']
 print('PASS 26894 exact 26893 successful compiled 2025->2026 source; 5 scope, one added, zero deletes, 2021 protected')

def semantics(base,cand):
 assert manifest(base)==old and manifest(cand)==new
 lib='app/src/main/assets/shaders/motionv2/'
 java='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
 j=(cand/java).read_text();r=(cand/(lib+'render.glsl')).read_text();g=(cand/(lib+'gainmap.glsl')).read_text();m=(cand/(lib+'spatial_scene_26894.glsl')).read_text()
 q='/* IRIS_26894_SPATIAL_SCENE_ADAPTIVE_SDR_AND_MATCHED_UHDR'
 def same(s):
  pos=s.index(q);return s[pos:s.index('return clamp(lifted/denominator,0.0,1.0);',pos)+len('return clamp(lifted/denominator,0.0,1.0);')]
 assert same(r)==same(g),'SDR/UHDR tone transfer differs'
 for f,n in [(r,3),(g,2)]:
  assert f.count('iris26892SdrAdaptiveGuide(')==n
  assert f.count('uniform sampler2D iris26894SpatialScene;')==1
  assert 'float iris26894SpatialWeight(float sourceGuide,vec2 masterPixel,out float variability)' in f
  assert 'float contrast=0.90*flatAmount*detailSafety*shadowSafety' in f
  assert 'float lifted=min(1.0,y+lift*y*t*t*t)' in f
  assert 'float darkSafety=smoothstep(0.003,0.020,y)' in f
  assert 'float darkBodyGate=1.0-smoothstep(0.52,0.76,lifted)' in f
  assert 'clamp(iris26893BacklitCoefficient,0.0,1.65)' in f
 assert r.count('iris26892SdrAdaptiveGuide(mappedGuide,guide,sourcePixel)')==1
 assert r.count('iris26892SdrAdaptiveGuide(mappedGuide,sourceGuide,sourcePixel)')==1
 assert g.count('iris26892SdrAdaptiveGuide(iris26770MidtonePresentationTrim(iris26660ObjectColorGamma(sharedSdr)),sourceGuide,masterSourcePixel)')==1
 assert 'out vec2 Output;' in m and 'uniform ivec2 iris26894SceneGridSize;' in m
 assert 'for(int yy=0;yy<4;yy++)' in m and 'for(int xx=0;xx<4;xx++)' in m
 assert j.count('glProg.useAssetProgram("motionv2/spatial_scene_26894")')==1
 assert j.count('glProg.drawBlocks(iris26894SpatialScene)')==1
 assert j.count('glProg.setTexture("iris26894SpatialScene",iris26894SpatialScene)')==2
 assert j.count('iris26894SpatialScene.close()')==1
 assert j.count('new GLFormat(GLFormat.DataType.FLOAT_16,2)')==1
 assert '&& !basePipeline.mParameters.motionV2SuperResOutputEnabled' in j
 assert '== Parameters.MOTION_V2_RECONSTRUCTION_RAWR_AMAZE' in j
 assert 'p.irisNightActive' in j and 'p.motionV2SuperResOutputEnabled' in j
 assert 'iris26623Smoothstep(0.78f,0.97f,p998)' in j and '0.60f,0.72f,p99' not in j
 assert j.index('glProg.drawBlocks(iris26894SpatialScene)')<j.index('glProg.useAssetProgram("motionv2/render")')<j.index('glProg.useAssetProgram("motionv2/gainmap")')<j.rindex('iris26894SpatialScene.close()')
 for p in pro:assert (cand/p).read_bytes()==(base/p).read_bytes()
 print('PASS 26894 B-SR-OFF only spatial 4x4 mean+variance, RG16F one GPU map, two matched SDR/UHDR consumers, lifetime & protected domains')

def shader(cand,compiler=None,out=None):
 assert manifest(cand)==new
 app=cand/'app';lib=app/'src/main/assets/shaders/motionv2';root=app/'src/main/java/com/particlesdevs/photoncamera/processing/opengl'
 assert 'glVersion = "#version 310 es' in (root/'GLProg.java').read_text()
 assert '#line 1' in (root/'GLInterface.java').read_text()
 reserved=set('sample attribute varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch invariant precise subroutine highp mediump lowp precision in out inout const struct if else do while switch case default for return discard break continue asm class union enum typedef template this packed goto inline noinline public static extern external interface long short half fixed unsigned input output common partition active filter resource namespace using'.split())
 for name in ('render.glsl','gainmap.glsl','spatial_scene_26894.glsl'):
  source=(lib/name).read_text();assert source.count('{')==source.count('}') and '#version' not in source and '#include' not in source
  code=re.sub(r'/\*.*?\*/|//[^\n]*','',source,flags=re.S)
  decl=re.findall(r'\b(?:float|int|uint|bool|vec[234]|ivec[234]|uvec[234]|mat[234]|sampler2D)\s+([A-Za-z_][A-Za-z0-9_]*)',code)
  assert not set(decl)&reserved,(name,set(decl)&reserved)
  assert not any(x.startswith('gl_') or '__' in x for x in decl)
  full='#version 310 es\n#line 1\n'+source
  if compiler:
   assert out;out.mkdir(parents=True,exist_ok=True);p=out/(name+'.frag');p.write_text(full)
   r=subprocess.run([str(compiler),'-S','frag',str(p)],capture_output=True,text=True)
   assert r.returncode==0,(name,r.stdout,r.stderr)
  print('PASS 26894 runtime-expanded ESSL310 source',name,'SHA256',hashlib.sha256(full.encode()).hexdigest(),'PINNED_GLSLANG',('PASS' if compiler else 'NOT RUN'))
 print('PASS 26894 THREE exact modified GLES310 runtime programs REAL PINNED COMPILE '+('PASS' if compiler else 'NOT RUN'))

def patches(base,cand,fwd,rollback):
 assert manifest(base)==old and manifest(cand)==new
 for ab in (7,12,40):
  with tempfile.TemporaryDirectory(prefix='photon26894_realpatch_') as td:
   x=Path(td)/'root';shutil.copytree(base,x);subprocess.run(['git','init','-q'],cwd=x,check=True)
   def run(*args):
    r=subprocess.run(['git','-c',f'core.abbrev={ab}',*args],cwd=x,capture_output=True,text=True)
    assert r.returncode==0,(args,r.stdout,r.stderr)
   run('apply','--check','--whitespace=error',str(fwd));run('apply','--whitespace=error',str(fwd));assert manifest(x)==new
   run('apply','--check','--reverse',str(fwd));run('apply','--check','--whitespace=error',str(rollback));run('apply','--whitespace=error',str(rollback));assert manifest(x)==old
   print('PASS 26894 EXACT 4-OPERAND full-index binary forward+rollback, fuzz0, core.abbrev',ab)

def smooth(lo,hi,x):
 v=max(0,min(1,(x-lo)/(hi-lo)));return v*v*(3-2*v)
def scores(p50,p95,p99,p998):
 if not all(math.isfinite(x) for x in [p50,p95,p99,p998]) or p50<0 or not p50<=p95<=p99<=p998:return 0,0
 b=(1-smooth(.015,.029,p50))*smooth(.78,.97,p998)
 f=smooth(.060,.085,p50)*(1-smooth(.148,.190,p50))*(1-smooth(.72,.92,p95-p50))*(1-b)
 return max(0,min(1,b)),max(0,min(1,f))
def guide(y,localAvg,variation,sourceGuide,backlit,flat):
 if y<=0 or y>=1:return y
 v=variation/max(localAvg,.004)
 w=(1-smooth(.10,.30,localAvg))*(1-smooth(.13,.33,sourceGuide))*smooth(.003,.017,localAvg)
 w=max(0,min(1,w))
 adj=1-.25*smooth(1.5,3.5,v)
 lift=min(1.65*backlit,1.65)*w*adj*smooth(.003,.02,y)
 z=min(1,y+lift*y*(1-y)**3)
 co=.9*flat*(1-.65*smooth(.38,1.6,v))*smooth(.008,.04,z)*(1-.95*min(1,w*backlit))
 return z/(1+co*(1-z)**3*(1-smooth(.52,.76,z)))
def tone():
 scenes={
 '26891_garden_dark':(.0059318542,.5600586,.73779297,1.),
 '26891_garden_good3':(.011428833,.5083008,.61083984,.6879883),
 '26891_garden_good4':(.017105103,.55517578,.68798828,.72314453),
 '26891_rose':(.10479736,.64208984,.74560547,.80810547),
 '26891_closet':(.111206055,.36938477,.49829102,.58251953),
 '26892_garden_dark1':(.004928589,.28442383,1.,1.),
 '26892_garden_dark2':(.0043792725,.3149414,.98535156,1.),
 '26892_garden_good3':(.02331543,.66308594,.73046875,.78027344),
 '26892_rose':(.08105469,.5673828,.7163086,.8774414),
 '26893_170108_sun_houses':(.010917664,.19238281,.5517578,1.0),
 '26893_170137_road':(.1932373,.72509766,.78466797,.83447266),
 '26893_garden5':(.020004272,.62060547,.6508789,.66064453),
 '26893_garden6':(.012809753,.5019531,.57470703,.6694336),
 '26893_garden7':(.005012512,.53759766,.82958984,1.0029297),
 '26893_flower8':(.101745605,.77001953,.9008789,.9814453),
 '26893_flower9':(.10687256,.79541016,.9316406,1.0244141)}
 for n,t in scenes.items():
  b,f=scores(*t);print('SCENE',n,'backlit',round(b,4),'flat',round(f,4))
  if n.endswith(('sun_houses','dark1','dark2','garden_dark','garden7')):assert b>.7,n
  if n in ['26893_flower8','26893_flower9','26891_rose','26891_closet']:assert f>.70,n
  if n in ['26891_garden_good3','26891_garden_good4','26892_garden_good3','26893_garden5','26893_garden6']:assert b<.001,n
  if n=='26893_170137_road':assert f<.001
 random.seed(26894)
 for j in range(100):
  mean=[.002,.004,.009,.02,.04,.1,.2,.4][j%8];var=random.random()*mean*3;source=random.random()*.45;b=random.random();f=random.random()
  xs=[guide(i/20000,mean,var,source,b,f) for i in range(20001)]
  assert all(math.isfinite(v) and v>=0 for v in xs)
  assert min(xs[i+1]-xs[i] for i in range(len(xs)-1))>=-2e-8,('not monotone',j)
 for y in [0,.0001,.001,.005,.01,.05,.1,.2,.4,.6,.76,.99,1]:
  assert guide(y,.5,.01,.7,1,0)==y,('sky gain',y)
  assert guide(y,.001,.0001,.0005,1,0)==y,('black floor',y)
  assert guide(y,.02,.005,.02,0,1)<=y+1e-8,('darken-only',y)
  assert guide(y,.02,.005,.02,0,0)==y,('preserved',y)
 assert guide(.09,.04,.01,.04,1,0)>.15
 assert guide(.20,.04,.01,.04,1,0)>.26
 print('PASS 26894 16 real 26891/26892/26893 scene scores, 2M monotonic tone samples, highlight/noise black safety, strict darken-only and neutral/no-op')

def tamper(base,cand):
 candidate(base,cand)
 for p in [allowed[0],allowed[2],next(iter(pro))]:
  target=cand/p;orig=target.read_bytes()
  try:
   target.write_bytes(orig+b'!')
   assert manifest(cand)!=new
  finally:target.write_bytes(orig)
  assert manifest(cand)==new
 print('PASS 26894 three real actual-source negative tamper / restored invariance')

def main():
 assert len(sys.argv)>=2
 m=sys.argv[1];args=sys.argv[2:]
 if m=='candidate':
  assert len(args) in (2,3) and (len(args)==2 or args[2]=='--transform')
  candidate(Path(args[0]),Path(args[1]),len(args)==3)
 elif m=='semantics':assert len(args)==2;semantics(*map(Path,args))
 elif m=='patch':assert len(args)==4;patches(*map(lambda x:Path(x).resolve(),args))
 elif m=='shader':
  assert len(args)==1 or (len(args)==5 and args[1]=='--compiler' and args[3]=='--out')
  shader(Path(args[0]),args[2] if len(args)>1 else None,Path(args[4]) if len(args)>1 else None)
 elif m=='tone':assert not args;tone()
 elif m=='tamper':assert len(args)==2;tamper(*map(Path,args))
 else:raise AssertionError(('invalid mode',m))
if __name__=='__main__':main()
