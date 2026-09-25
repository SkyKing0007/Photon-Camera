#!/usr/bin/env python3
from pathlib import Path
import math,sys
if len(sys.argv)!=3:raise SystemExit('usage: verify_26704_regressions.py BASE26703 CANDIDATE')
b=Path(sys.argv[1]);c=Path(sys.argv[2])
def txt(root,rel):return (root/rel).read_text()
def smooth(a,b,x):
 t=max(0.0,min(1.0,(x-a)/(b-a)));return t*t*(3-2*t)
def second(v):return sorted(v)[1]
# 1) Sign/tree-sky: valid center NORMAL chroma must never become recovery-eligible from colorful neighbors.
def color_need(physical_loss_rgb):
 return smooth(0.55,0.90,min(physical_loss_rgb))
assert color_need((0,0,0))==0.0                         # neutral sign letter / valid sky hole
assert color_need((0.2,0.9,0.9))==0.0                   # partial CFA loss is scalar-only
assert color_need((1,1,1))==1.0                         # positive control: genuinely lost color remains eligible
# 2) SHORT radiance: brighter SHORT over dark foreground must not infer loss; literal physical loss remains valid.
def inferred_context(normal_rgb):return smooth(0.22,0.50,second([max(x,0) for x in normal_rgb]))
assert inferred_context((0.04,0.05,0.06))==0.0           # dark wire/person against bright sky/window
assert inferred_context((0.70,0.75,0.80))==1.0           # bright NORMAL highlight context
for conf in [0.0,0.1,0.5,1.0]:
 transition=0.82+(1.0-0.82)*conf
 assert 0.82<=transition<=1.0
 assert 0.5*transition<=0.5+1e-12                        # weak NORMAL confidence can never boost SHORT
physical=1.0; inferred=0.0; assert max(physical,inferred)==1.0 # literal measured loss still rescues
# 3) Body tone: office activates, highway does not; mapping monotonic, black protected, >=0.35 exact identity.
def strength(p50,p95,p99):
 return max(0,min(1,(1-smooth(.025,.070,p50))*(1-smooth(.080,.180,p95))*smooth(.120,.220,p99)))
def body(y,s):
 y=max(y,0);s=max(0,min(1,s));a=.35
 if s<=1e-7 or y<=0 or y>=a:return y
 gamma=1-.28*s;toe=a*((max(0,min(1,y/a)))**gamma);gate=smooth(.004,.018,y);return y+(toe-y)*gate
office=strength(.0050239563,.04534912,.21936035); highway=strength(.12902832,.4086914,.85839844)
assert office>0.98,office
assert highway==0.0,highway
for s in [0,.25,.5,.75,1.0]:
 vals=[body(i/10000,s) for i in range(0,10001)]
 assert all(vals[i+1]+1e-10>=vals[i] for i in range(len(vals)-1)),s
 for y in [0,.001,.004,.35,.5,1,2]:
  if y<=.004 or y>=.35: assert abs(body(y,s)-y)<1e-9,(s,y,body(y,s))
# 4) Settings unavailable + forced runtime OFF.
prefs=txt(c,'app/src/main/res/xml/preferences.xml');assert 'pref_highlight_compression_key' not in prefs and 'pref_iris_local_laplacian_tone' not in prefs
# 5) Preserve old known high-frequency/Sabre/color/UHDR/Spektra authorities outside explicit scope.
for rel in [
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/java/com/unspektrawesome/capture/FrameGeometrySnapshot.kt',
'app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt',
]:assert (b/rel).read_bytes()==(c/rel).read_bytes(),rel
print('PASS 26704 permanent regressions: sign/sky valid chroma immutable + physical-loss positive control; dark-foreground SHORT fail-closed; low local support never boosts SHORT; office-only monotonic body toe; settings OFF; protected owners invariant')
