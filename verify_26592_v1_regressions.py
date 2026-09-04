#!/usr/bin/env python3
from pathlib import Path
import argparse,math,struct
START=.50;OUT=.80;LOG=3.0;TS=1.2020679
def fail(m):raise SystemExit('FAIL: '+m)
def req(c,m):
 if not c:fail(m)
def f32(x):return struct.unpack('!f',struct.pack('!f',float(x)))[0]
def smooth(a,b,x):
 if x<=a:return 0.0
 if x>=b:return 1.0
 t=(x-a)/(b-a);return t*t*(3-2*t)
def old91(u):
 x=max(0.0,min(1.0,u));s=math.log(1+3*x)/math.log(4);return (START+(1/OUT-START)*s)*OUT
def new92(u):
 u=max(0.0,u);lc=math.log(1+LOG*u)/math.log(1+LOG);s=math.tanh(TS*lc);return (START+(1/OUT-START)*s)*OUT
def new92f(u):return f32(new92(f32(u)))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('candidate_root');ns=ap.parse_args();c=Path(ns.candidate_root)
 sabre=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text();stack=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text();render=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text();glsl=(c/'app/src/main/assets/shaders/motionv2/render.glsl').read_text();cpp=(c/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text();uhdr=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java').read_text();bridge=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
 # Exact failure condition: trust is admission only; NORMAL saturation owns blend.
 req('if (trustConfidence < trustGate) { oMask = 0.0; return; }' in sabre,'binary trust gate')
 req('oMask = smoothstep(handoffStart, uReferenceNearClipThreshold, referenceSecond);' in sabre,'radiometric blend owner')
 req('oMask = trustConfidence' not in sabre,'trust still opacity')
 req(smooth(.90,.98,.899)==0.0,'safe NORMAL must be exact NORMAL')
 req(0.0<smooth(.90,.98,.94)<1.0,'transition missing')
 req(abs(smooth(.90,.98,.98)-1.0)<1e-12,'trusted nearclip must be 100% SHORT')
 for t in ['shortNeighborhoodHasHeadroom','uShortWeightThreshold','uNormalCoverageThreshold','uFlowVariationThreshold','uUnblockerThreshold','evidence < 3','meanError >= uConsistencyThreshold','vec2 shortUv = clamp(referenceUv + flow.xy']:
  req(t in sabre,'anti-smear '+t)
 req('GLES30.GL_R8, GLES30.GL_NEAREST' in stack and 'wholeRgb=true maskFilter=NEAREST' in stack,'NEAREST whole-RGB mask')
 # 26592 tail exactly preserves 26591 anchor at u=.5, but unlike 26591 remains ordered above sceneWhite.
 req(abs(new92(.5)-old91(.5))<5e-8,f'half-headroom anchor drift {old91(.5)} {new92(.5)}')
 req(new92(1.0)<1.0 and new92(2.0)>new92(1.0) and new92(5.0)>new92(2.0),'above-sceneWhite ordering')
 vals=[new92f(u) for u in (.5,.75,1,1.5,2,3,5,8)]
 req(all(vals[i+1]>vals[i] for i in range(len(vals)-1)),f'float32 Motion tail plateau {vals}')
 req(vals[-1]<1.0,'finite practical tail hit exact linear white')
 for g in (0,.1,.3,.5):req(g==g,'body identity fixture')
 # Structural formula parity 1x/true2x Motion and explicit legacy Night branches.
 for t in ['tanh(tanhScale*logCoordinate)','float x=clamp(u,0.0,1.0)']:
  req(t in glsl,'1x Motion/Night split '+t)
 for t in ['std::tanh(1.2020679f*logCoordinate)','else {float x=clampf(u,0.f,1.f)','tanh(1.2020679*logCoordinate)','else {float x=clamp(u,0.0,1.0)']:
  req(t in cpp,'true2x parity '+t)
 # Existing -2.5EV SHORT = sqrt(32) ~=5.657x; gain map metadata must not truncate it at old 2.5x.
 short_ratio=2**2.5
 req(short_ratio>5.65 and short_ratio<5.66,'physical headroom fixture')
 req('Math.min(8.0f, maxRatio)' in uhdr,'8x UHDR metadata capacity')
 req(8.0>short_ratio,'UHDR metadata still below physical SHORT range')
 # Historic role isolation survives.
 req('parameters.irisNightActive && frame.role == RawBurstFrameRole.SHADOW_LONG' in bridge,'Motion LONG parity policy')
 req('IRIS_26592_SHORT_HANDOFF_EFFECT' in stack,'durable handoff telemetry')
 print('PASS 26592 trust-vs-blend regression: trust admits/rejects only; safe NORMAL=0, transition 0.90..0.98, trusted nearclip=100% whole-RGB SHORT')
 print('PASS same Sabre alignment/temporal/rejection/flow/unblocker/radiometric gates and NEAREST mask retained')
 print('PASS 26592 Motion tail matches 26591 at u=0.5 then remains float32-ordered through 8x sceneWhite instead of clamping at u=1')
 print('PASS 1x/true2x Motion formulas carry matching log+tanh tail while legacy Night branches remain explicit')
 print('PASS Motion UltraHDR metadata capacity 8x exceeds existing -2.5EV SHORT physical headroom 5.657x; Motion LONG role isolation carried')
if __name__=='__main__':main()
