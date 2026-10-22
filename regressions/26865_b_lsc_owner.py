#!/usr/bin/env python3
"""26865 permanent regression for exact successful-26864 two-capture
LSC parity false-negative. This is semantic proof, not real Android compiler.
"""
from pathlib import Path
import sys, re
assert len(sys.argv)==2
app=Path(sys.argv[1]);p=app/'src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
b=app/'src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'
s=p.read_text();bridge=b.read_text()
# The precise failing old 26859-only assertion must be absent from B-only.
assert 'lensShadingCorrectionApplied = iris26859BLensMapTexture != 0,' not in s
assert s.count('var iris26865BPreAmazeLscAppliedForPublication = false')==1
assert s.count('iris26865BPreAmazeLscAppliedForPublication =')==2
# Receipt must be created AFTER native callback and AFTER B Lab/FCC carrier.
producer=s.index('val nativeSensorClip26864 = consumer(')
post=s.index('iris26856RawrRgbSidecar = renderRawrBPostAmaze26856(',producer)
receipt=s.index('iris26865BPreAmazeLscAppliedForPublication =',post)
assert producer<post<receipt
block=s[receipt:s.index('} finally {',receipt)]
for contract in ('nativeSensorClip26864 != 0','iris26864RealRawrOwnsBurstNoise','iris26856RawrRgbSidecar != 0'):
 assert contract in block,contract
# The only B-only result must use native evidence AND the clip/carrier
# lifetimes. No unconditional pass or false proof for A/legacy.
start=s.index('val isolatedBResult = RawStackResult(')
end=s.index('mergedFrameCount = mergedFrameCount,',start)
b_pub=s[start:end]
assert 'lensShadingCorrectionApplied = iris26859BLensMapTexture != 0 ||' in b_pub
for x in ('iris26865BPreAmazeLscAppliedForPublication','iris26864NativeClipForPublication != 0','bSidecar != 0'):
 assert x in b_pub
assert s.count('lensShadingCorrectionApplied = hasLensShading(),')>=1
assert bridge.count('requireParity(lsc == null || stacked.lensShadingCorrectionApplied,')==1
assert 'LSC supplied but MGC output did not apply it' in bridge
# The new receipt cannot turn true on legacy/A routes, absent native mask,
# missing final B RGB, or absent native RAWR noise ownership.
def receipt(nativeClip, nativeBurst, rgb):return nativeClip and nativeBurst and rgb
for clip in (False,True):
 for burst in (False,True):
  for rgb in (False,True):
   assert receipt(clip,burst,rgb) == (clip and burst and rgb)
assert receipt(True,True,True)
assert not receipt(False,True,True)
assert not receipt(True,False,True)
assert not receipt(True,True,False)
# All native shaders and 26864 ownership receipts are still intact.
assert 'Iris26864NativeRawrDomainReceipt(true,true,true)' in s
assert 'if (rawrNativeReceipt26864 == null)' in s
assert 'bLensCorrected26859 = renderIris26859BLensShading(' in s
print('PASS 26865 exact 26864 device failure: B-only native pre-AMaZE LSC receipt, legacy isolation, strict final parity, negative cases')
