#!/usr/bin/env python3
"""26884 source and numeric regression for RAWR Highlight Reconstruction OFF ONLY.
No ON guide/color propagation, no final native RGB repaint; both native B paths
use one fused WB+common-ceiling owner before existing Lab -> FCC -> inverse WB.
This is a preflight, NOT a glslang/Android/device substitute.
"""
from pathlib import Path
import sys,math
r=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
shade=(r/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt').read_text()
stack=(r/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
assert shade.count('float commonCeiling=min(uAmazeWb.r,min(uAmazeWb.g,uAmazeWb.b));')==1
assert shade.count('return min(postWb,vec3(commonCeiling));')==1
assert shade.count('vec4(rawrHighlightOff(')==5
assert 'uNativeSensorClip' not in shade
assert 'uGuide' not in shade and 'rawrHighlightRecoverDetail' not in shade
assert 'renderIris26866BNativeSensorSmoothWhite' not in stack
assert 'private var iris26866BNativeSmoothWhiteProgram' not in stack
assert 'bindTexture(program, "uPostRawrRgb", 0, fcc)' in stack
assert 'GlesIris26870PostAmazeChroma.shader' in stack
p=stack.index('temporaryPostWb = createTexture',stack.index('private fun renderRawrBPostAmaze26856('))
lab=stack.index('defringed = renderRawrLabDefringe26856(',p)
fcc=stack.index('fcc = renderRawrFalseColor26856(',lab)
inv=stack.index('neutral = createTexture(',fcc)
assert p<lab<fcc<inv
assert 'if (rawrNativeReceipt26864 != null)' in stack[p:lab]
# Both native routing callers preserve their independent native mask/noise and
# reach this exact shared post-AMaZE helper, no Wronski/HDRq changes.
assert stack.count('nativeSensorClipFullRes26866 = nativeClip')>=2
assert 'if (nativeSensorClipFullRes26866 == 0 && bClipRatio26858 != 0)' in stack

def rawr_off(x,g):
 common=min(g)
 return tuple(min(max(x[i]*g[i],0),common) for i in range(3))
# Test full normalized camera RGB range across white WB with various gains.
for g in ((2,1,1.7),(1.8,1,1.2),(1,1,1),(0.8,1,1.4)):
 for i in range(2001):
  k=i/2000
  v=rawr_off((k,k,k),g)
  assert all(v[j] <= k*g[j]+1e-12 for j in range(3))  # no painted/raised light/color
  if i>0:
   last=rawr_off(((i-1)/2000,)*3,g)
   assert all(0<=v[j]-last[j] <= max(g)*0.0005+1e-12 for j in range(3))
  if i==2000:assert max(v)-min(v)<1e-12   # full sensor white becomes neutral
 # Continuity exactly at each channel crossing of shared ceiling.
 for gain in g:
  k0=min(g)/gain
  for j in range(3):
   before=rawr_off((k0-1e-7,)*3,g)[j]
   after=rawr_off((k0+1e-7,)*3,g)[j]
   assert abs(after-before)<max(g)*2.1e-7
 # Test colored light: no fabricated RGB and no chroma diffusion from neighbors
 for color in ((1,0,0),(0,0,1),(1,1,0),(0,0.1,1),(.3,.7,.8)):
  o=rawr_off(color,g)
  assert all(0<=o[j]<=max(color[j]*g[j],0) for j in range(3))
print('PASS RAWR OFF exact shared WB-channel ceiling, all 5 native paths, order, both native B routes, no color/brightness creation and continuous sensor ramp')
