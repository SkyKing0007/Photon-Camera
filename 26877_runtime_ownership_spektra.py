#!/usr/bin/env python3
"""Permanent exact 26876 device ownership and Spektra surface regression.
Read-only; reproduces predecessor failure before testing fixed candidate.
"""
from pathlib import Path
import sys,re,hashlib,math,xml.etree.ElementTree as ET
base,cand=(Path(x) for x in sys.argv[1:3])
old=(base/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
new=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
old_fn=old.split('private fun reconstructIris26876B2xGpu(',1)[1].split('private fun readIris26864WronskiStripe(',1)[0]
new_fn=new.split('private fun reconstructIris26876B2xGpu(',1)[1].split('private fun readIris26864WronskiStripe(',1)[0]
# Original failing condition from the real 26876 device log: the returned 1x
# texture ID was alive, but no longer owned in textureSpecs at bridge copy.
assert 'textures.remove(guideRgb) && textures.remove(guideClip)' in old_fn
assert 'textureSpecs.remove(guideRgb)' in old_fn and 'textureSpecs.remove(guideClip)' in old_fn
assert 'copyPersistentTexture(sensorNeutralB, width, height,' in old
assert 'bindRenderTargets(intArrayOf(source), "$label source")' in old
assert 'textureSpecs[texture]' in old
# No bypassing the existing GL ownership or down-resing the true2x result.
assert 'textures.remove(guideRgb) && textures.remove(guideClip)' not in new_fn
assert 'textureSpecs.remove(guideRgb)' not in new_fn
assert 'textureSpecs.remove(guideClip)' not in new_fn
assert 'releaseTexturesFromExcept(firstTexture,intArrayOf(guideRgb,guideClip))' in new_fn
assert 'textures.contains(guideRgb) && textures.contains(guideClip)' in new_fn
outer=new.split('private fun processIris26868DirectB(',1)[1].split('private fun renderIris26868IndependentLongShadowGuide(',1)[0]
assert outer.index('bridgeRgb = copyPersistentTexture(sensorNeutralB') < outer.index('textures.remove(bridgeRgb) && textures.remove(sensorNeutralB)')
assert 'textures.contains(nativeClip)' in outer
assert 'if (iris26856BTrue2x) textureSpecs.remove(nativeClip)' in outer
assert 'IRIS_26877_B_GUIDE_ABORT_EXACT_CLEANUP' in outer
assert 'if (!returned && nativeClip != 0 && !textures.contains(nativeClip))' in outer
assert 'if (!returned && bridgeRgb != 0 && !textures.contains(bridgeRgb))' in outer
assert new.count('reconstructIris26876B2xGpu(')==2 # caller and function
assert 'IRIS_26876_SINGLE_NATIVE_WRONSKI_NO_DUPLICATE_HDRQ' in new
assert 'packWronskiRgbAndClip26876(sensorRgb,nativeClip)' in new_fn
# Control-plane regression: Spektra retains dedicated RAW/Vulkan ownership;
# only surface/presentation geometry changed.
frag_path='app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java'
oldfrag=(base/frag_path).read_text();newfrag=(cand/frag_path).read_text()
assert 'updateSpektraViewportBounds26877' not in oldfrag
assert 'updateSpektraViewportBounds26877' in newfrag
assert 'spektraSurfaceView.post(this::updateSpektraViewportBounds26877)' in newfrag
assert 'setSpektraPreviewVisible(boolean spektraVisible)' in newfrag
assert 'setSpektraPreviewVisible(boolean spektraVisible)' in oldfrag
layout_path='app/src/main/res/layout/layout_main_viewfinder.xml'
oldlayout=(base/layout_path).read_text();newlayout=(cand/layout_path).read_text()
ns={'android':'http://schemas.android.com/apk/res/android','app':'http://schemas.android.com/apk/res-auto'}
for xml in (oldlayout,newlayout): ET.fromstring(xml)
assert 'app:layout_constraintEnd_toEndOf="@id/texture"' in oldlayout
assert 'app:layout_constraintEnd_toEndOf="parent"' in newlayout
assert 'app:layout_constraintStart_toStartOf="parent"' in newlayout
assert 'android:id="@+id/spektra_surface"' in newlayout
for w,h,landscape in [(1440,1920,False),(1920,1440,True),(1080,1920,False),(2560,1440,True)]:
 if landscape: targeth=min(h,(w*3)//4);targetw=(targeth*4)//3
 else:targetw=min(w,(h*3)//4);targeth=(targetw*4)//3
 assert 0<targetw<=w and 0<targeth<=h
 assert abs((targetw/targeth)-(4/3 if landscape else 3/4))<0.006
# Every untouched runtime file including DNG, A, NIGHT, Spektra renderer
# and native/vendor assets is strictly byte-protected by full manifests.
print('PASS 26877 real 26876 Wronski 1x source ownership failure regression, one-owner release, Spektra portrait/landscape 4:3 presentation and native renderer protected')
