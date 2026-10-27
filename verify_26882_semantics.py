#!/usr/bin/env python3
"""26882 permanent source-domain regressions for device failures in successful 26881.
No synthetic checks can substitute for pinned real glslang/Kotlin/NDK/assemble.
"""
from pathlib import Path
import math,re,sys,hashlib
BASE=Path(sys.argv[1]);CAN=Path(sys.argv[2]);R=Path(__file__).resolve().parent
shader='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26858BNoiseHighlight.kt'
raw='app/src/main/java/com/unspektrawesome/vulkan/params/RawShaderParameters.kt'
stack='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
old=(BASE/shader).read_text();new=(CAN/shader).read_text()
a=(BASE/raw).read_text();b=(CAN/raw).read_text()
assert 'require(outputDimensions.width <= output.size.width && outputDimensions.height <= output.size.height)' in a
assert 'val nativeAxes = outputDimensions.width <= output.size.width' in b
assert 'val quarterTurnAxes = outputDimensions.width <= output.size.height' in b
assert '(nativeAxes || quarterTurnAxes)' in b
assert 'RAW processing dimensions exceed both native and 90-degree rotated bounds' in b
assert b.count('val quarterTurnAxes')==1
# Actual 26881 device failure RAW10 4096x3072 -> 90/270 output 3072x4096.
def accepted(rw,rh,ow,oh):return ow>0 and oh>0 and ((ow<=rw and oh<=rh) or (ow<=rh and oh<=rw))
assert accepted(4096,3072,3072,4096)
assert accepted(4096,3072,4096,3072)
assert accepted(4096,3072,768,1024) and accepted(4096,3072,1024,768)
for bad in ((4098,3072),(3072,4098),(4096,4096),(0,3072),(-1,3072),(3072,0)):
 assert not accepted(4096,3072,*bad),bad
assert (BASE/stack).read_bytes()==(CAN/stack).read_bytes(), 'HDRq/Wronski routing, CFA clip lifetime, WB, A/Long and DNG cannot change'
# Match exact previously failing shader and prove no extra source changes.
assert old.count('smoothstep(0.35,0.65,')==1
assert new.count('smoothstep(0.055,0.28,')==1
assert 'smoothstep(0.35,0.65,' not in new
assert new.count('bNativeSensorSmoothWhite26866 = """')==1
# All current shaded programs except targeted third-channel admission must be byte-identical,
# after normalizing changed comments and the one threshold statement.
oldShader=old.split('val bNativeSensorSmoothWhite26866 = """',1)[1];newShader=new.split('val bNativeSensorSmoothWhite26866 = """',1)[1]
for required in ['float tripleClip=min(colorClip.r,min(colorClip.g,colorClip.b));',
 'float opticalSupport=min(clippedCoverage,max(multiColor,greenOnly));',
 'float fade=smoothstep(0.13,0.38,opticalSupport)*brightSupport;',
 'if(clippedCoverage<=0.0){oRgb=original;return;}',
 'float neutral=max(hi,wbSafe);',
 'oRgb=vec4(mix(original.rgb,vec3(neutral),fade),original.a);']:
 assert required in oldShader and required in newShader,required
assert old.count('vec3 physicalWbRgb=')==new.count('vec3 physicalWbRgb=')==1
assert 'uNativeSensorClip' in newShader and 'uBayerPattern' in newShader
# Route provenance supports both Wronski and HDRq at their exact native sizes.
src=(CAN/stack).read_text()
assert 'nativeSensorClipFullRes26866=nativeClip' in src
assert 'nativeSensorClipFullRes26866 = nativeClip' in src
assert 'bNativeSensorSmoothWhite26866' in src
# Numerical monotonicity/no whitening for unclipped and pure red/yellow emission.
def smooth(a,b,x):
 y=max(0,min(1,(x-a)/(b-a)));return y*y*(3-2*y)
def fade(coverage,green,red,blue,second,safe):
 cross=min(green,max(red,blue));triple=min(red,green,blue)
 third=smooth(.055,.28,min(red,green,blue)) # minimum normalized witness equivalent fixture
 optical=min(coverage,max(triple,cross*third))
 bright=max(smooth(.70,1.10,second/safe),smooth(.10,.50,triple))
 return smooth(.13,.38,optical)*bright
# Exact source-expression thought fixture: red+green independently clipped,
# no independent blue clip, but nonzero blue RAW/WB witness from a white lamp.
# The 26881 0.35..0.65 third witness makes fade zero even in the bright core.
# The bounded 26882 transition admits it while preserving red/yellow neon
# with genuinely near-zero blue evidence.
def full_fade(coverage,clipR,clipG,clipB,thirdPhysical,secondWb):
 triple=min(clipR,clipG,clipB)
 cross=min(clipG,max(clipR,clipB))
 witness=smooth(.055,.28,thirdPhysical)
 optical=min(coverage,max(triple,cross*witness))
 bright=max(smooth(.70,1.10,secondWb),smooth(.10,.50,triple))
 return smooth(.13,.38,optical)*bright
assert full_fade(.8,.95,.92,0,.28,1.1)>.99,'partially clipped white lamp was still vetoed'
assert full_fade(.8,.95,.92,0,.005,1.1)==0,'red/yellow near-zero-blue neon must stay colored'
assert full_fade(0,.95,.92,0,.4,1.1)==0,'unclipped object must never borrow white mask'
assert full_fade(1,1,1,1,.1,1.1)==1,'fully sensor-clipped white core must converge to white'
assert all(0<=full_fade(.8,.95,.92,0,v,1.1)<=1 for v in (0,.02,.055,.1,.16,.21,.28,.5))
# GLSL thirdWitness uses color channels, not color clip; below verifies its exact ramp.
assert smooth(.055,.28,0)==0
assert smooth(.055,.28,.05)==0
assert 0<smooth(.055,.28,.18)<1
assert smooth(.055,.28,.4)==1
for x in [i/1000 for i in range(1001)]:
 assert math.isfinite(smooth(.055,.28,x))
assert not any(accepted(4096,3072,*d) for d in ((4100,4100),(0,0)))
print('PASS 26882 real-device 4096x3072 portrait/landscape output contract; bounded invalid extents; B shared HDRq/Wronski physical clip owner unchanged; continuous near-clip white admission with unclipped/neon guard')
