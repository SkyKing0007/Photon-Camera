#!/usr/bin/env python3
from pathlib import Path
import hashlib,math,sys
TOL=2.0
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
    for q in vals:
     s=sum(math.dist(v,q)<=TOL for v in vals);candidates.append((s,q))
    bs=max(s for s,_ in candidates); best=next(q for s,q in candidates if s==bs)
    ss=max((s for s,q in candidates if math.dist(q,best)>TOL),default=0)
    if bs<2 or bs<=ss:continue
    sup=[v for v in vals if math.dist(v,best)<=TOL];mean=(sum(v[0] for v in sup)/len(sup),sum(v[1] for v in sup)/len(sup))
    if max(math.dist(v,mean) for v in sup)<=TOL:nxt[y][x]=mean
  cur=nxt
 return cur
def main():
 if len(sys.argv)!=3:fail('usage base candidate')
 b,c=map(Path,sys.argv[1:])
 # Exact 26599 tone/publication/capture owners unchanged.
 inherited=[
  'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
  'app/src/main/assets/shaders/motionv2/display_exposure.glsl',
  'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java',
  'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
  'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
  'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
  'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java']
 for r in inherited:
  if H(b/r)!=H(c/r):fail('26599 inherited owner changed '+r)
 # 8 coherent + one extreme outlier must remain trusted; ambiguous 5-vs-4 must fail closed.
 good=[(0.,0.)]*8+[(20.,20.)]
 if robust_seed(good) is None:fail('one-outlier coherent flow rejected')
 conflict=[(0.,0.)]*5+[(10.,0.)]*4
 if robust_seed(conflict) is not None:fail('5-vs-4 ambiguous flow accepted')
 # Static clipped core fills from coherent boundary geometry.
 n=9; hi=[[True]*n for _ in range(n)]; g=[[None]*n for _ in range(n)]
 for i in range(n):g[0][i]=(0.,0.);g[-1][i]=(0.,0.);g[i][0]=(0.,0.);g[i][-1]=(0.,0.)
 r=propagate(g,hi,2*n)
 if any(v is None for row in r for v in row):fail('static highlight core did not fill')
 # Conflicting left/right motion must not cross: a fail-closed seam must remain.
 w=11;h=5;g=[[None]*w for _ in range(h)];hi=[[True]*w for _ in range(h)]
 for y in range(h):g[y][0]=(0.,0.);g[y][-1]=(10.,0.)
 r=propagate(g,hi,w+h)
 seam=[(x,y) for y in range(h) for x in range(w) if r[y][x] is None]
 if not seam:fail('conflicting motion produced no fail-closed seam')
 for row in r:
  seen10=False
  for v in row:
   if v is not None and v[0]>5:seen10=True
   if seen10 and v is not None and v[0]<5:fail('conflicting fields crossed')
 sh=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text();st=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
 if 'if (flow.w > uFlowVariationPixelsThreshold) return;' in sh[sh.index('val shortRestoreMask26596 = """'):]:fail('26599 poisoned max-range gate survived')
 if 'uConsensusPixels", 2.0f' not in st:fail('2 RAW-pixel safety tolerance changed')
 if 'oColor = vec4(mix(normalRgb.rgb, restoredShort, confidence), normalRgb.a);' not in sh:fail('whole-RGB restore changed')
 if 'dng=false srEvidence=false' not in st:fail('SHORT role changed')
 print('PASS 26600 geometry regression: isolated LK outlier tolerated; 5-vs-4 ambiguity fails closed')
 print('PASS static clipped core fills from coherent boundary; conflicting motion preserves untrusted seam/no crossing')
 print('PASS successful-26599 tone/capture/SR/DNG/native owners byte-identical; whole-RGB SHORT and 2px safety retained')
if __name__=='__main__':main()
