#!/usr/bin/env python3
"""RawLens 2.3.94 exact two independent radii + less-chromatic selection; no green blur."""
import math,re,sys,random
from build_26952_incremental import R,fail
src=(R/('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932RawLensMedian.kt' if '--live' in sys.argv else 'handoff_payload_26952/app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932RawLensMedian.kt')).read_text()
glsl=src.split('"""#version 300 es',1)[1].split('""".trimIndent()',1)[0]
network='p1,p2 p4,p5 p7,p8 p0,p1 p3,p4 p6,p7 p1,p2 p4,p5 p7,p8 p0,p3 p5,p8 p4,p7 p3,p6 p1,p4 p2,p5 p4,p7 p4,p2 p6,p4 p4,p2'.split()
actual=re.findall(r'CC_SORT\((p[0-8]),(p[0-8])\)',glsl)
want=[tuple(x.split(',')) for x in network]
if actual!=want:fail('not original RawLens 19-exchange per-channel median sequence')
if glsl.count('cc_median(p,m0,1)')!=1 or glsl.count('cc_median(p,m0,2)')!=1:fail('two independent medians not exactly one each')
if 'dot(wide,wide)<dot(fine,fine)?wide:fine;' not in glsl:fail('upstream smaller-color-norm rule absent')
if 'medianRgb=max(vec3(c.g+d.x,c.g,c.g+d.y),vec3(0.0))' not in glsl:fail('green/luminance sample changes')
if 'u_defringe' in glsl or 'nativeSetKernelNetDenoise' in glsl:fail('unrequested defringe/additional denoiser')
# Direct parity of upstream network on 5x5 color-difference samples, R-G/B-G only.
random.seed(26952)
def median(values):
 p=list(values)
 for a,b in want:
  ai=int(a[1]);bi=int(b[1]);v=p[ai];w=p[bi]
  p[ai]=tuple(min(v[k],w[k]) for k in (0,1));p[bi]=tuple(max(v[k],w[k]) for k in (0,1))
 return p[4]
def run(patch):
 def med(radius):
  return median([patch[(x*radius,y*radius)] for y in (-1,0,1) for x in (-1,0,1)])
 f=med(1);w=med(2)
 return w if sum(x*x for x in w)<sum(x*x for x in f) else f
for _ in range(500):
 d=(random.uniform(-.25,.25),random.uniform(-.25,.25))
 patch={(x,y):d for x in range(-2,3) for y in range(-2,3)}
 assert run(patch)==d
# Simulate a thin 1-2 pixel cyan/yellow color island: wide ring must veto it.
for d in ((0.3,-.27),(-.31,.32),(.2,.29),(-.2,-.28)):
 patch={(x,y):(0.,0.) for x in range(-2,3) for y in range(-2,3)}
 patch[(0,0)]=d
 assert run(patch)==(0.,0.)
# True broad saturated surfaces must not be erased by neutral false-color rule.
for d in ((.18,-.07),(-.14,.21)):
 patch={(x,y):d for x in range(-2,3) for y in range(-2,3)}
 assert run(patch)==d
# The bridge preserving 3x2 sets native iteration and data steps explicitly.
bridge=(R/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26931LkrBridge.java') if '--live' in sys.argv else None
if bridge:
 s=bridge.read_text()
 if 'T=3, DATA_STEPS=2, OUTPUT_SCALE=2' not in s:fail('restored prohibited 8x4 schedule')
print('PASS 26952 original RawLens 2.3.94 two-radius Paeth median, neutral high-frequency alias, true color islands, no green/zipper alteration, 3x2')
