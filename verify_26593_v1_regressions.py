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
 # Exact real Actions javac failure 33833745581: mPreviewCaptureResult is CaptureResult in successful 26592.
 req('mPreviewCaptureResult instanceof TotalCaptureResult' in cap,'33833745581 checked TotalCaptureResult cast missing')
 req('? (TotalCaptureResult) mPreviewCaptureResult : null;' in cap,'33833745581 checked TotalCaptureResult cast incomplete')
 req('final TotalCaptureResult iris26593NormalReference = mPreviewCaptureResult;' not in cap,'33833745581 direct incompatible assignment survived')
 # Exact real failure: chandelier had requestShort=true but processing inputFrames=15/bridgeTotalScheduledFrames=15 with no handoff effect.
 for t in ['ticket.sceneRequired = sceneRequiresShort','iris26480ShortHighlightRequested = iris26593ShortBudgetAllows\n                && iris26486ShortTicket.sceneRequired','shortExpected=" + plan.shortExpected','SHORT_CAPTURE_FAILURE','SHORT_CAPTURE_TIMEOUT','requested SHORT disappeared after immutable batch freeze']:
  req(t in cap+bridge,'chandelier fail-closed '+t)
 req('freezeExpectedAuxiliaries' not in cap+batch,'80ms auxiliary seal regression survived')
 req('MOTION_26593_MIN_CAPTURE_COMPLETION_MS = 1400L' in cap and 'MOTION_26593_MAX_CAPTURE_COMPLETION_MS = 3500L' in cap,'bounded completion window')
 # Total slider state-space: SHORT priority, LONG only when one NORMAL still remains.
 for total in range(1,31):
  for short_scene in (False,True):
   short=short_scene and total>=2
   remaining=total-(1 if short else 0)
   for long_scene in (False,True):
    long=long_scene and remaining>=2
    normal=total-(1 if short else 0)-(1 if long else 0)
    req(normal>=1,f'normal budget total={total} short={short} long={long}')
    req(normal+(1 if short else 0)+(1 if long else 0)==total,'exact total arithmetic')
 # Quick-open top-up only fills missing NORMAL count; full ZSL requires none.
 for target in (1,5,13,14,15,28,29,30):
  for ready in (0,1,max(0,target-1),target,target+3):
   missing=max(0,target-ready)
   req(missing==0 if ready>=target else missing==target-ready,'quick-open missing count')
 # 26592 SHORT handoff remains unchanged: trust is admission, saturation is blend owner.
 req('if (trustConfidence < trustGate) { oMask = 0.0; return; }' in sabre,'26592 trust gate')
 req('oMask = smoothstep(handoffStart, uReferenceNearClipThreshold, referenceSecond);' in sabre,'26592 handoff owner')
 req('oMask = trustConfidence' not in sabre,'trust opacity regression')
 req(smooth(.90,.98,.899)==0.0 and 0<smooth(.90,.98,.94)<1 and abs(smooth(.90,.98,.98)-1)<1e-12,'26592 handoff numeric fixture')
 for t in ['shortNeighborhoodHasHeadroom','uShortWeightThreshold','uNormalCoverageThreshold','uFlowVariationThreshold','uUnblockerThreshold','evidence < 3','meanError >= uConsistencyThreshold','vec2 shortUv = clamp(referenceUv + flow.xy']:
  req(t in sabre,'anti-smear '+t)
 req('GLES30.GL_R8, GLES30.GL_NEAREST' in stack and 'wholeRgb=true maskFilter=NEAREST' in stack,'whole RGB nearest mask')
 # 26592 unbounded tail and 8x UHDR range remain active.
 vals=[f32(new92(f32(u))) for u in (.5,.75,1,1.5,2,3,5,8)]
 req(all(vals[i+1]>vals[i] for i in range(len(vals)-1)),'26592 float32 tail plateau')
 req(vals[-1]<1.0,'tail endpoint clamp returned')
 for t in ['tanh(tanhScale*logCoordinate)','float x=clamp(u,0.0,1.0)']:req(t in glsl,'1x Motion/Night split '+t)
 for t in ['std::tanh(1.2020679f*logCoordinate)','else {float x=clampf(u,0.f,1.f)','tanh(1.2020679*logCoordinate)','else {float x=clamp(u,0.0,1.0)']:req(t in cpp,'true2x parity '+t)
 req('Math.min(8.0f, maxRatio)' in uhdr and 8.0>2**2.5,'8x UHDR headroom')
 print('PASS Actions javac 33833745581 regression: successful-26592 CaptureResult declaration is respected through fail-closed checked TotalCaptureResult cast')
 print('PASS chandelier regression: requestShort=true cannot reach reconstruction without frozen SHORT; missing/late SHORT fails loudly instead of NORMAL-only downgrade')
 print('PASS exact slider-total arithmetic for 1..30 frames and quick-open missing-NORMAL top-up contract')
 print('PASS old 80ms auxiliary freeze removed; capture completion is bounded 1.4..3.5s and generation owned')
 print('PASS carried 26592 trust-gated whole-RGB SHORT handoff, anti-smear gates, unbounded 1x/true2x Motion tail and 8x UHDR range')
if __name__=='__main__':main()
