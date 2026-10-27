#!/usr/bin/env python3
"""26884 RAWR Highlight Reconstruction OFF, active B routes and preserved domains."""
from pathlib import Path
import sys,hashlib,math
B=Path(sys.argv[1]);C=Path(sys.argv[2]);R=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=lambda n:{k:h for h,k in (s.split('  ',1) for s in (R/n).read_text().splitlines())}
base=manifest('26884_BASE_26883_FULL_APP.sha256');new=manifest('26884_EXPECTED_CANDIDATE_FULL_APP.sha256')
allow=(R/'26884_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert len(allow)==3 and len(base)==len(new)==2009
assert set(allow)=={k for k in base if base[k]!=new[k]}
assert all(sha(B/k)==base[k] and sha(C/k)==new[k] for k in allow)
assert (C/'app/version.properties').read_text().splitlines()[-2:]==['VERSION_NAME=0.9726884','VERSION_BUILD=26884']
# Every Spektra, JNI, DNG, UHDR, vendor and native compiled-source byte retained.
for p in ('app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt',
'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraModeController.java',
'app/src/main/java/com/unspektrawesome/capture/FrameGeometrySnapshot.kt',
'app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc',
'app/src/main/cpp/iris26864/Iris26864WronskiPackedCfa2x.comp',
'app/src/main/cpp/iris26864/bridge/Iris26864HdrqCfaToAmaze.comp',
'app/src/main/cpp/iris26864/Iris26864PackedSensorClipToGl.comp',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp'):
 assert base[p]==new[p] and sha(B/p)==sha(C/p),('protected owner altered',p)
for p in base:
 if p not in allow:assert base[p]==new[p],('unexpected change',p)
chroma='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt'
s=(C/chroma).read_text();old=(B/chroma).read_text();stack=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
assert s.count('float commonCeiling=min(uAmazeWb.r,min(uAmazeWb.g,uAmazeWb.b));')==1
assert s.count('return min(postWb,vec3(commonCeiling));')==1
assert s.count('vec4(rawrHighlightOff(')==5
assert 'uGuide' not in s and 'rawrHighlightRecoverDetail' not in s
assert 'rawrHighlightOff' not in old
assert 'renderIris26866BNativeSensorSmoothWhite' not in stack
assert 'private var iris26866BNativeSmoothWhiteProgram' not in stack
assert 'GlesIris26870PostAmazeChroma.shader' in stack
assert 'bindTexture(program, "uPostRawrRgb", 0, fcc)' in stack
p=stack.index('temporaryPostWb = createTexture',stack.index('private fun renderRawrBPostAmaze26856('))
lab=stack.index('defringed = renderRawrLabDefringe26856(',p)
fcc=stack.index('fcc = renderRawrFalseColor26856(',lab)
inv=stack.index('neutral = createTexture(',fcc)
assert p<lab<fcc<inv
assert 'if (rawrNativeReceipt26864 != null)' in stack[p:lab]
assert stack.count('nativeSensorClipFullRes26866 = nativeClip')>=2
assert 'processIris26868DirectB(frames)' in stack and 'reconstructIris26876B2xGpu(' in stack
assert 'uNativeSensorClip' not in s
# Numerical RAWR OFF clamp: never creates luminance, no hue borrowed, continuous.
def clamp_off(c,g):
 ceiling=min(g);return tuple(min(max(c[i]*g[i],0.),ceiling) for i in range(3))
for g in ((2.,1.,1.7),(1.8,1.,1.2),(1.,1.,1.),(.8,1.,1.4)):
 for i in range(2001):
  v=i/2000;result=clamp_off((v,v,v),g)
  assert all(0<=result[j]<=v*g[j]+1e-10 for j in range(3))
  if i:
   prior=clamp_off(((i-1)/2000,)*3,g)
   assert all(0<=result[j]-prior[j]<=max(g)*.0005+1e-9 for j in range(3))
  if i==2000:assert max(result)-min(result)<1e-9
 for c in ((1,0,0),(0,0,1),(1,1,0),(0,.1,1),(.3,.7,.8)):
  r=clamp_off(c,g)
  assert all(0<=r[j]<=max(c[j]*g[j],0) for j in range(3))
print('PASS 26884 exact RAWR OFF fused WB common ceiling before Lab/FCC, both native B routes, no hallucinated/brightened pixels, 2006 immutable incl Spektra')
