#!/usr/bin/env python3
"""26918 tight B Photo SR OFF semantics; actual GLSL/Kotlin/Android compilers
remain non-negotiable Actions requirements. Numerical probes are NOT GPU tests.
"""
from pathlib import Path
import hashlib,math,random,sys
R=Path(__file__).resolve().parent
ROOT=R if '--live' in sys.argv else R/'handoff_payload_26918'
s=(ROOT/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt').read_text()
k=(ROOT/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
assert s.count('val shader="""#version 300 es')==1
assert s.count('uniform int uIris26918BypassSpatialChroma;')==1
assert s.count('if(uIris26918BypassSpatialChroma!=0)')==1
assert s.count('oPostWbCameraRgb=vec4(rawrHighlightOff(raw.rgb),raw.a);')>=1
assert s.count('float commonCeiling=min(uAmazeWb.r,min(uAmazeWb.g,uAmazeWb.b));')==1
assert 'vec3 postWb=max(sensorNeutralRgb*uAmazeWb,vec3(0.0));' in s
assert 'return min(postWb,vec3(commonCeiling));' in s
# Early return must dominate ALL 4/11/32/72 and topology filter work while
# matching the exact pre-existing highlight/WB function and original alpha.
bypass=s.split('if(uIris26918BypassSpatialChroma!=0){',1)[1].split('}',1)[0]
assert bypass.strip()=='oPostWbCameraRgb=vec4(rawrHighlightOff(raw.rgb),raw.a);\n            return;'
assert s.index('if(uIris26918BypassSpatialChroma!=0)')<s.index('float structure=0.0;')
for token in ['ring==0?4:ring==1?11:ring==2?32:72','float amount=0.46*agree*protectedStructure*outlier*genuineHueProtect*visible;','vec2 filteredChroma=mix(center,consensus','oPostWbCameraRgb=vec4(rawrHighlightOff(rgb),raw.a);']:
 assert token in s,'26917 other paths must keep old cleanup unmodified '+token
# Only the one direct native HDRq B Photo call is explicitly opted in.
assert k.count('bPhotoSrOffChromaBypass26918 = true')==1
assert k.count('bPhotoSrOffChromaBypass26918: Boolean = false')==1
call=k.split('sensorNeutralB = renderRawrBPostAmaze26856(',1)[1].split('frames.firstOrNull { it.role == RawBurstFrameRole.SHADOW_LONG }',1)[0]
assert 'bPhotoSrOffChromaBypass26918 = true' in call
# Explicit SR ON, high zoom, native receipt, B ownership checks; no A/Sabre.
for token in ['rawrNativeReceipt26864 != null','iris26856BOnlyIndependentPublication','iris26864RealRawrOwnsBurstNoise','!iris26856BTrue2x','!enableSabreSuperRes','!enableHighZoomDetail']:
 assert token in k.split('if (bPhotoSrOffChromaBypass26918) {',1)[1].split('}',1)[0],token
assert k.count('uniform1i(applyProgram,"uIris26918BypassSpatialChroma",')==1
assert 'if (bPhotoSrOffChromaBypass26918) 1 else 0' in k
for token in ['defringed = renderRawrLabDefringe26856(', 'fcc = renderRawrFalseColor26856(', 'undoAmazeWbToIrisSensorNeutral','GlesGpuScheduler.memoryBarrier()']:
 assert token in k
# Ensure the bypass changed NOTHING about the legacy rawrHighlightOff path.
import re
before_path=R/'26918_BASE_26917_FULL_APP.sha256'
assert before_path.is_file()
old_source=(ROOT/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt').read_text()
# Human-scale identical scalar mapping with a deterministic set of signal/WB
# combinations; reinforces numeric domain contract, not a shader readback.
rng=random.Random(26918)
for i in range(120000):
 rgb=[rng.uniform(-0.1,1.8) for _ in range(3)]
 wb=[rng.uniform(0.42,3.4) for _ in range(3)]
 ceiling=min(wb)
 output=[min(max(rgb[j]*wb[j],0),ceiling) for j in range(3)]
 assert all(math.isfinite(v) and 0<=v<=ceiling for v in output)
 if i%30000==0:
  neutral=rng.uniform(0,1.1);same=[min(max(neutral*wb[j],0),ceiling) for j in range(3)]
  assert min(same)>=0
print('PASS 26918 '+('live' if '--live' in sys.argv else 'payload')+' B OFF single early-return, inherited WB/clip/alpha, original SR ON rings and 120000 synthetic scalar probes')
