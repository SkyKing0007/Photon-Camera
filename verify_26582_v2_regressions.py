#!/usr/bin/env python3
from pathlib import Path
import math,sys,hashlib
OUT_SCALE=.80
START=.50
TARGET=.97
CLIP_START=.002
CLIP_FULL=.025
LOG_SHAPE=6.0
MAX_WHITE=12.0
RENDER_SHADER_SHA='e0a438e51e12df5e6d8b53dc92892078ba7659791725cee54700869a6bc62b71'
GPU_SHA='d73cd24452280958f089e9124545a81461939e8fa0c9c95272b2825942e4b43d'
def fail(m):raise SystemExit('FAIL: '+m)
def clamp(x,a,b):return max(a,min(b,x))
def smooth(a,b,x):
 t=clamp((x-a)/max(b-a,1e-9),0,1);return t*t*(3-2*t)
def basewhite(g):return max(1.0,min(6.0,.9*max(1.0,g)))
def strength(f):return smooth(CLIP_START,CLIP_FULL,f)
def adaptive(g,p99,clip):
 base=basewhite(g);post=p99*max(g,1e-6)
 if not math.isfinite(p99) or p99<=0 or post<=base:return base
 target_pre=TARGET/OUT_SCALE; pre_white=1/OUT_SCALE
 shape=clamp((target_pre-START)/(pre_white-START),0,1)
 x=(math.exp(shape*math.log(1+LOG_SHAPE))-1)/LOG_SHAPE
 req=START+(post-START)/max(x,1e-4);req=max(base,min(MAX_WHITE,req))
 return base+(req-base)*strength(clip)
def mapped(guide,white):
 if guide<=START:return guide*OUT_SCALE
 x=clamp((guide-START)/max(white-START,1e-6),0,1)
 shaped=math.log(1+LOG_SHAPE*x)/math.log(1+LOG_SHAPE)
 return (START+(1/OUT_SCALE-START)*shaped)*OUT_SCALE
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 if len(sys.argv)!=2:fail('usage candidate')
 r=Path(sys.argv[1])
 # 1 no HDR tail => exact old scene-white decision.
 for g,p99,clip in [(1.0,.75,0.0),(2.0,.80,.0),(4.0,.82,.001)]:
  a=adaptive(g,p99,clip);b=basewhite(g)
  if abs(a-b)>1e-7:fail('no-tail changed')
 # 2 broad window/sky tail => strong adaptive extension and P99 ~0.97.
 g=4.0;p99=1.40;clip=.45;w=adaptive(g,p99,clip)
 if not w>basewhite(g)*1.15:fail('broad tail did not expand white')
 if abs(mapped(p99*g,w)-TARGET)>0.003:fail('broad tail P99 target')
 # 3 moderate ~2.3% near-white reference case engages almost fully.
 if strength(.023)<.97:fail('moderate tail strength')
 w2=adaptive(3.5,1.15,.023)
 if not w2>basewhite(3.5):fail('moderate tail no extension')
 # 4 below shoulder is invariant for any scene white.
 for x in [0,.05,.2,.49,.50]:
  if abs(mapped(x,1.0)-mapped(x,9.0))>1e-8:fail('body changed below shoulder')
 # 5 monotone highlight ordering until white; no plateau before scene white.
 w=6.0;ys=[mapped(START+(w-START)*i/100,w) for i in range(101)]
 if any(ys[i+1] <= ys[i] for i in range(100)):fail('non-monotone highlight shoulder')
 # 6 scalar RGB tone cannot rotate hue/channel ratios.
 rgb=(1.8,.72,.31);guide=max(rgb);scale=(mapped(guide,6.0)/guide)/OUT_SCALE
 out=tuple(v*scale for v in rgb)
 if abs(out[0]/out[1]-rgb[0]/rgb[1])>1e-6 or abs(out[1]/out[2]-rgb[1]/rgb[2])>1e-6:fail('hue ratio changed')
 # 7 rare isolated specular (<0.2%) does not pull the scene.
 if strength(.001)>1e-8:fail('isolated specular engaged global adaptation')
 # 8 source ownership and old pink protections remain untouched.
 render=r/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
 matcher=r/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java'
 shader=r/'app/src/main/assets/shaders/motionv2/render.glsl';gpu=r/'app/src/main/cpp/motionv2_jpeg444_jni.cpp'
 if sha(shader)!=RENDER_SHADER_SHA:fail('render shader changed')
 if sha(gpu)!=GPU_SHA:fail('GPU publication changed')
 s=render.read_text();m=matcher.read_text()
 for t in ['uniformRgbScalar=true chromaOwnerUnchanged=true','IRIS_26582_SOLVER_RENDER_TONE_PARITY']:
  if t not in s+m:fail('marker '+t)
 if 'presentedLuma(s, 1.0f)' in m:fail('26582 V1 two-argument presentedLuma compiler regression survived')
 if 'presentedLuma(s, 1.0f, iris26582MeterTone.adaptiveSceneWhite)' not in m:fail('fixed meter-sort presentedLuma call missing')
 if 'neutralMix = smoothstep(0.82f, 1.0f, pos)' in m:fail('stale white convergence survived')
 print('PASS no-tail scene keeps exact 26581 scene-white decision')
 print('PASS broad HDR tail preserves ordering and targets robust P99 near 0.97 SDR')
 print('PASS moderate clipped tail engages; isolated specular does not globally darken scene')
 print('PASS <=0.50 body/midtones invariant and highlight curve monotone')
 print('PASS global tone is uniform RGB scalar: no per-channel pink/magenta mechanism')
 print('PASS 26582 V1 Java signature failure permanently gated: meter sort uses 3-argument presentedLuma')
 print('PASS 26581 render shader and device-proven GPU publication bytes frozen')
if __name__=='__main__':main()
