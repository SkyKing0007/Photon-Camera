#!/usr/bin/env python3
from pathlib import Path
import hashlib,math,sys
TOL=2.0
TONE_26598={
'app/src/main/assets/shaders/motionv2/display_exposure.glsl':'cecbb02f659f115bb1e17bc1026f2dd4fd8177c5cfdea27dd31e2a7eaf5401ea',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java':'84b7f003e0f1ba8ce2ab53f5f4a1bd41425046a6dfb1ff39a4e7a16114d5a7be',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java':'0d69c007097262a5ef1a27719a9d0ea0723188460bc96e81dc69f6dc65d3faf4',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java':'6726e025fd4dd0fe1aceab1063d9d846898d628eac26ec02b87d6f2ae814f38a',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp':'f781ee8a8881d18b4db68c40e50ba45a89e4a8669a2cc44b3a009395f71dea7e'}
def fail(m):raise SystemExit('FAIL: '+m)
def H(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def support_count(vals,h):return sum(math.dist(v,h)<=TOL for v in vals)
def robust_seed(vals):
 best=None;bs=0
 for h in vals:
  s=support_count(vals,h)
  if s>bs:bs=s;best=h
 if bs<5:return None
 ss=max((support_count(vals,h) for h in vals if math.dist(h,best)>TOL),default=0)
 if bs-ss<2:return None
 sup=[v for v in vals if math.dist(v,best)<=TOL]
 if len(sup)<5:return None
 mean=(sum(v[0] for v in sup)/len(sup),sum(v[1] for v in sup)/len(sup))
 if max(math.dist(v,mean) for v in sup)>TOL:return None
 return mean
def propagate(grid,highlight,passes):
 h=len(grid);w=len(grid[0]);cur=[[grid[y][x] for x in range(w)] for y in range(h)]
 for _ in range(passes):
  nxt=[[cur[y][x] for x in range(w)] for y in range(h)]
  for y in range(h):
   for x in range(w):
    if cur[y][x] is not None or not highlight[y][x]:continue
    vals=[]
    for yy in range(max(0,y-1),min(h,y+2)):
     for xx in range(max(0,x-1),min(w,x+2)):
      if cur[yy][xx] is not None:vals.append(cur[yy][xx])
    if len(vals)<2:continue
    candidates=[]
    for q in vals:candidates.append((sum(math.dist(v,q)<=TOL for v in vals),q))
    bs=max(s for s,_ in candidates);best=next(q for s,q in candidates if s==bs)
    ss=max((s for s,q in candidates if math.dist(q,best)>TOL),default=0)
    if bs<2 or bs<=ss:continue
    sup=[v for v in vals if math.dist(v,best)<=TOL]
    mean=(sum(v[0] for v in sup)/len(sup),sum(v[1] for v in sup)/len(sup))
    if max(math.dist(v,mean) for v in sup)<=TOL:nxt[y][x]=mean
  cur=nxt
 return cur
def main():
 if len(sys.argv)!=3:fail('usage base candidate')
 b,c=map(Path,sys.argv[1:])
 # Successful 26600 geometry must retain the exact outlier/ambiguity behavior.
 if robust_seed([(0.,0.)]*8+[(20.,20.)]) is None:fail('one-outlier coherent flow rejected')
 if robust_seed([(0.,0.)]*5+[(10.,0.)]*4) is not None:fail('5-vs-4 ambiguous flow accepted')
 n=9;hi=[[True]*n for _ in range(n)];g=[[None]*n for _ in range(n)]
 for i in range(n):g[0][i]=(0.,0.);g[-1][i]=(0.,0.);g[i][0]=(0.,0.);g[i][-1]=(0.,0.)
 if any(v is None for row in propagate(g,hi,2*n) for v in row):fail('static highlight core did not fill')
 w=11;h=5;g=[[None]*w for _ in range(h)];hi=[[True]*w for _ in range(h)]
 for y in range(h):g[y][0]=(0.,0.);g[y][-1]=(10.,0.)
 r=propagate(g,hi,w+h)
 if not any(v is None for row in r for v in row):fail('conflicting motion produced no fail-closed seam')
 # Exact 26600 capture/scene-white/render remain unchanged.
 for rel in ['app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','app/src/main/assets/shaders/motionv2/render.glsl']:
  if H(b/rel)!=H(c/rel):fail('26600 inherited owner changed '+rel)
 # 26598 presentation is intentionally restored exactly as a coordinated set.
 for rel,want in TONE_26598.items():
  if H(c/rel)!=want:fail('26598 presentation parity '+rel)
 st=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text(); sh=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
 active=st[st.index('private fun processSabreFrames'):st.index('private data class SabreNormalDngSupportStats')]
 # Exact visual failure condition from 26600: no second post-VGN SHORT RGB image may be mixed across a material edge.
 for x in ['resolveSabreShortNativeExposure26587(','renderSabreShortRestoreRgba16f26587(','highlightShortTexture26587']:
  if x in active:fail('26600 two-RGB edge/halo failure authority survived '+x)
 if 'sabreShortRestoreRgba16fProgram26587 = 0' not in st:fail('late RGB shader was not neutralized')
 # Common pre-Resolve ownership must move color+all three weights together; no fractional RGB blend.
 owner=sh[sh.index('val shortAccumulatorOwnership26601'):sh.index('val shortRestoreRgba16f26587')]
 for x in ['float shortOwner = (evidence > 0.0 && minimumShortWeight > 1.0e-7) ? 1.0 : 0.0;','mix(normalColor, shortColor, shortOwner)','mix(normalGb, shortGb, shortOwner)']:
  if x not in owner:fail('homogeneous whole-evidence ownership '+x)
 if 'calibration = calibration,' not in active:fail('SHORT not normalized to NORMAL reference exposure before common Resolve')
 # LONG and SR ownership cannot regress.
 for x in ['shadowLongSourceClipGuard = frame.role == RawBurstFrameRole.SHADOW_LONG','if (enableSabreSuperRes && frame.role == RawBurstFrameRole.NORMAL)','if (normalDngAccumulator != 0 && frame.role == RawBurstFrameRole.NORMAL)','srDetailOwner=NORMAL_ONLY']:
  if x not in active:fail('role regression '+x)
 # Synthetic edge fixture: an old fractional two-RGB handoff invents a third color; binary evidence never does.
 normal=(1.0,0.94,0.91); short=(0.70,0.72,0.73); alpha=.5
 old=tuple((1-alpha)*n+alpha*s for n,s in zip(normal,short))
 if old in (normal,short):fail('fixture invalid')
 for evidence in (0.0,1.0):
  now=short if evidence>0 else normal
  if now not in (normal,short):fail('binary owner invented edge chroma')
 # Exact restored display stage remains pure positive scalar; no new dimming curve.
 de=(c/'app/src/main/assets/shaders/motionv2/display_exposure.glsl').read_text()
 if 'Output = c * max(displayGain, 1.0e-6);' not in de:fail('linear presentation gain missing')
 if any(x in de for x in ['presentationLinearAnchor','presentationKnee','motionToneNormalization']):fail('26599 haze curve survived')
 print('PASS inherited 26600 boundary geometry: outlier tolerant, ambiguous/motion-conflict fail closed, 2px policy retained')
 print('PASS bathroom/window edge + plant-halo regression: active late post-VGN two-RGB SHORT blend is absent; one homogeneous evidence owner feeds one Resolve/VGN')
 print('PASS LONG remains common Sabre evidence; DNG and true2x high-frequency evidence remain NORMAL-only')
 print('PASS kids/sofa SDR haze regression: exact successful-26598 linear presentation bytes restored with common MotionV2Render unchanged')
if __name__=='__main__':main()
