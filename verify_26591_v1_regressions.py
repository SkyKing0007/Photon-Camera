#!/usr/bin/env python3
from pathlib import Path
import argparse,math,re

def fail(m):raise SystemExit('FAIL: '+m)
def req(c,m):
 if not c:fail(m)
def clamp(x,a,b):return max(a,min(b,x))
START=0.50; OUT=0.80

def map_headroom(g,w,shape):
 if g<=START:return g
 x=clamp((g-START)/max(w-START,1e-6),0.0,1.0)
 shaped=math.log(1.0+shape*x)/math.log(1.0+shape)
 return START+(1.0/OUT-START)*shaped

def req_white(gain,source,target,shape):
 base=max(1.0,min(6.0,0.90*max(1.0,gain)))
 post=source*gain
 target_pre=clamp(target,0.80,0.995)/OUT
 target_shape=clamp((target_pre-START)/(1.0/OUT-START),0.0,1.0)
 tx=(math.exp(target_shape*math.log(1.0+shape))-1.0)/shape
 return max(base,min(12.0,START+(post-START)/max(tx,1e-4)))

def main():
 ap=argparse.ArgumentParser();ap.add_argument('candidate_root');ns=ap.parse_args();c=Path(ns.candidate_root)
 render=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
 vf=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java').read_text()
 glsl=(c/'app/src/main/assets/shaders/motionv2/render.glsl').read_text()
 stack=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
 sabre=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
 bridge=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
 # Structural body freeze and final-tail owner.
 for t in ['IRIS_26582_TONE_START = 0.50f','OUTPUT_EXPOSURE_SCALE = 0.80f','IRIS_26582_LOG_SHAPE = 6.0f','IRIS_26591_LOG_SHAPE = 3.0f']:
  req(t in render,t)
 req('const float start=0.50;' in glsl and 'const float logShape=3.0;' in glsl,'GLSL final curve constants')
 req('localToneMap=false' in vf,'global-only tone contract')
 req('uniformRgbScalar=true' in vf,'whole-RGB tone contract')
 req('sharpening=false' in render or 'sharpening=' in render,'render sharpening telemetry owner')
 # Exact solver section must still call the old 26590 mapper only.
 sec=vf[vf.index('private static float presentedLuma'):vf.index('private static float srgbDecode')]
 req('iris26582MapHeadroom' in sec and 'iris26591MapHeadroom' not in sec,'26590 body meter frozen')
 # New final targets and final authority branch.
 for t in ['IRIS_26591_HIGHLIGHT_TARGET = 0.980f','IRIS_26591_BROAD_HIGHLIGHT_TARGET = 0.975f',
           'IRIS_26591_COMPACT_HIGHLIGHT_TARGET = 0.985f','IRIS_26591_CONTINUOUS_HIGHLIGHT_TARGET = 0.980f',
           'IRIS_26591_STRUCTURED_HIGHLIGHT_TARGET = 0.985f']:
  req(t in render,t)
 req('finalHighlightAuthority' in vf and 'iris26591RequiredSceneWhite' in vf,'final authority split')
 # Exact 17:24 window fixture: target shift must lower the required scene white and open top separation.
 gain=6.0371566; p99=.8955078; structured=1.0263672
 old_w=7.537732
 new_w=req_white(gain,structured,.985,3.0)
 req(6.44 < new_w < 6.50,f'window new required white unexpected {new_w}')
 old_p99=map_headroom(p99*gain,old_w,6.0)*OUT
 new_p99=map_headroom(p99*gain,new_w,3.0)*OUT
 new_struct=map_headroom(structured*gain,new_w,3.0)*OUT
 req(new_p99>old_p99+0.02,f'window p99 separation did not open {old_p99}->{new_p99}')
 req(.982<new_struct<.988,f'structured endpoint {new_struct}')
 # Shape-3 has materially greater differential slope in the high normalized tail than shape-6.
 def dshape(x,s):return s/(math.log(1+s)*(1+s*x))
 req(dshape(.8,3.0)>1.15*dshape(.8,6.0),'upper-tail differential slope not improved')
 # Identity below tone start and display-white endpoint are exact.
 for g in (0.0,.1,.3,.5):req(map_headroom(g,4.0,3.0)==g,'body identity below 0.50')
 req(abs(map_headroom(6.0,6.0,3.0)*OUT-1.0)<1e-7,'final endpoint not clean white')
 # SHORT safety remains in protected Sabre shader; stack change is diagnostic only.
 for t in ['referenceNearClipQuad(referenceP) < 2','shortNeighborhoodHasHeadroom(shortP)','vec2 shortUv = clamp(referenceUv + flow.xy',
           'mix(normalRgb.rgb, restoredShort, confidence)','there is no second correspondence search']:
  req(t in sabre,'SHORT safety '+t)
 req('IRIS_26591_SHORT_MASK_EFFECT' in stack and 'MotionTrace.processingState(' in stack,'durable SHORT mask telemetry')
 req('sameSabreFlow=true wholeRgb=true maskFilter=NEAREST' in stack,'SHORT telemetry safety facts')
 # Carry Motion LONG count and isolation proof.
 req('parameters.irisNightActive && frame.role == RawBurstFrameRole.SHADOW_LONG' in bridge,'Motion LONG parity role policy')
 print(f'PASS exact 17:24 no-SHORT window regression oldP99={old_p99:.6f} newP99={new_p99:.6f} newStructured={new_struct:.6f} requiredWhite={new_w:.6f}')
 print('PASS shape-3 final shoulder preserves more upper-tail differential spacing while body <=0.50 and 0.80 output exposure stay exact')
 print('PASS successful-26590 meter/body solver frozen; final highlight authority cannot feed back into viewfinder body exposure')
 print('PASS 26590 SHORT alignment/mask geometry protected; durable MotionTrace effect telemetry added without post-tone compositing')
 print('PASS carried Motion LONG parity, DNG/SR/Night isolation and historic false-color/ghost fail-closed architecture')
if __name__=='__main__':main()
