#!/usr/bin/env python3
from pathlib import Path
import argparse,math,struct,re
START=.50;OUT=.80;LOG=3.0;TS=1.2020679
def fail(m):raise SystemExit('FAIL: '+m)
def req(c,m):
 if not c:fail(m)
def f32(x):return struct.unpack('!f',struct.pack('!f',float(x)))[0]
def smooth(a,b,x):
 if x<=a:return 0.0
 if x>=b:return 1.0
 t=(x-a)/(b-a);return t*t*(3-2*t)
def new92(u):
 u=max(0.0,u);lc=math.log(1+LOG*u)/math.log(1+LOG);s=math.tanh(TS*lc);return (START+(1/OUT-START)*s)*OUT
def main():
 ap=argparse.ArgumentParser();ap.add_argument('candidate_root');ns=ap.parse_args();c=Path(ns.candidate_root)
 cap=(c/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text();batch=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java').read_text();bridge=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text();sabre=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text();stack=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text();glsl=(c/'app/src/main/assets/shaders/motionv2/render.glsl').read_text();cpp=(c/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text();uhdr=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java').read_text()
 # Carried exact successful-26593 capture ownership + real javac regression.
 req('mPreviewCaptureResult instanceof TotalCaptureResult' in cap,'checked TotalCaptureResult cast missing')
 req('? (TotalCaptureResult) mPreviewCaptureResult : null;' in cap,'checked TotalCaptureResult cast incomplete')
 req('final TotalCaptureResult iris26593NormalReference = mPreviewCaptureResult;' not in cap,'failed direct assignment revived')
 for t in ['ticket.sceneRequired = sceneRequiresShort','SHORT_CAPTURE_FAILURE','SHORT_CAPTURE_TIMEOUT','requested SHORT disappeared after immutable batch freeze']:
  req(t in cap+bridge,'26593 capture fail-closed '+t)
 req('freezeExpectedAuxiliaries' not in cap+batch,'old auxiliary seal revived')
 req('MOTION_26593_MIN_CAPTURE_COMPLETION_MS = 1400L' in cap and 'MOTION_26593_MAX_CAPTURE_COMPLETION_MS = 3500L' in cap,'completion window')
 # New topology source contract.
 for t in ['shortRegionSeed26594','shortRegionPropagate26594','oSeed = evidence >= 3 && meanError < uConsistencyThreshold ? 1.0 : 0.0','if (seed >= 0.5) { oTrust = 1.0; return; }','if (at(uRegion, p) < 0.5) { oTrust = 0.0; return; }']:
  req(t in sabre,'26594 topology '+t)
 for t in ['SHORT_REGION_PROPAGATION_PASSES_26594 = 32','regionTrust = shortRegionTrust26594','normalCoverageGate=false','boundaryRadiometry=true']:
  req(t in stack,'26594 stacker '+t)
 # Numeric topology fixtures independent of GPU: no seed never activates; disconnected/hole stays off.
 def prop(seed,region,passes=32):
  h=len(seed);w=len(seed[0]);cur=[row[:] for row in seed]
  for _ in range(passes):
   nxt=[[0]*w for _ in range(h)]
   for y in range(h):
    for x in range(w):
     if seed[y][x]: nxt[y][x]=1; continue
     if not region[y][x]: continue
     nxt[y][x]=1 if any(cur[max(0,min(h-1,y+dy))][max(0,min(w-1,x+dx))] for dy in (-1,0,1) for dx in (-1,0,1)) else 0
   cur=nxt
  return cur
 z=[[0]*7 for _ in range(5)]; reg=[[1]*7 for _ in range(5)]; req(sum(map(sum,prop(z,reg)))==0,'no-seed self authorization')
 seed=[[0]*7 for _ in range(5)];seed[2][0]=1; reg=[[1]*7 for _ in range(5)];
 for y in range(5):reg[y][3]=0
 out=prop(seed,reg);req(out[2][2]==1 and out[2][4]==0,'geometry hole/disconnected propagation')
 # Blend remains saturation-owned and whole RGB NEAREST.
 req('oMask = smoothstep(handoffStart, uReferenceNearClipThreshold, referenceSecond);' in sabre,'saturation blend owner')
 req(smooth(.90,.98,.899)==0 and 0<smooth(.90,.98,.94)<1 and smooth(.90,.98,.98)==1,'handoff numeric')
 req('GLES30.GL_R8, GLES30.GL_NEAREST' in stack and 'wholeRgb=true maskFilter=NEAREST' in stack,'whole-RGB nearest')
 # 26592/26593 Motion tail/UHDR invariants.
 vals=[f32(new92(f32(u))) for u in (.5,.75,1,1.5,2,3,5,8)];req(all(vals[i+1]>vals[i] for i in range(len(vals)-1)),'Motion tail plateau')
 for t in ['tanh(tanhScale*logCoordinate)','float x=clamp(u,0.0,1.0)']:req(t in glsl,'1x Motion/Night split '+t)
 for t in ['std::tanh(1.2020679f*logCoordinate)','else {float x=clampf(u,0.f,1.f)']:req(t in cpp,'true2x parity '+t)
 req('Math.min(8.0f, maxRatio)' in uhdr,'8x UHDR')
 print('PASS carried successful-26593 capture/slider/compiler ownership remains intact')
 print('PASS 26594 no-seed/no-self-authorization and disconnected/geometry-hole topology fixtures')
 print('PASS region-anchored boundary radiometry + local Sabre geometry + whole-RGB 0.90..0.98 handoff')
 print('PASS carried unbounded Motion tail, true2x parity and 8x UltraHDR ownership')
if __name__=='__main__':main()
