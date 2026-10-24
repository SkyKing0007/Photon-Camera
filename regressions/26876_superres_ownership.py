#!/usr/bin/env python3
"""26876 B-only Wronski/clip/GPU publication regressions on real authority files."""
from pathlib import Path
import sys,re
base,cand=(Path(sys.argv[1]),Path(sys.argv[2]))
kpath='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
cpath='app/src/main/cpp/motionv2_jpeg444_jni.cpp'
bk=(base/kpath).read_text();ck=(cand/kpath).read_text()
bc=(base/cpath).read_text();cc=(cand/cpath).read_text()
assert 'IRIS_26864_ACTUAL_PINNED_WRONSKI_TRUE2X_PUBLISHER' in bk
assert 'IRIS_26876_B_SINGLE_WRONSKI_NORMAL' not in bk
assert 'IRIS_26876_B_SINGLE_WRONSKI_NORMAL' in ck
assert ck.count('IRIS_26876_B_SINGLE_WRONSKI_NORMAL')==1
section=ck.split('private fun processIris26868DirectB(',1)[1].split('private fun renderIris26868IndependentLongShadowGuide',1)[0]
assert section.count('iris26856AmazeCfaConsumer)(')==1
assert section.index('if (iris26856BTrue2x) {')<section.index('iris26856AmazeCfaConsumer)(')
assert section.count('reconstructIris26864PinnedWronski2x(')==1
assert 'nativeGuide1x' in section and 'nativeClip1x' in section
assert 'RAW' not in ''  # no inferred Camera2 fallback
assert 'IRIS_26876_B_ONLY_PARALLEL_SENSOR_CLIP_CORRECTION' in cc
assert 'trueMaskBitsPath' in cc and 'mfd>=0' in cc
assert cc.count('kIris26571PublicationCompute=R"GLSL(')==1
assert cc.count('kIris26876BPublicationCompute=R"GLSL(')==1
assert 'iris26876B?kIris26876BPublicationCompute:kIris26571PublicationCompute' in cc
assert 'std::strstr(rp.c,"/iris26864_b_wronski_")' in cc
assert 'motionFast&&(iris26876BSource||' in cc
assert '!water.enabled()&&p.dcpHueSatMap.empty()&&p.dcpLookMap.empty()' in cc
assert cc.count('IRIS_26876_B_GPU_DCP_WATERMARK_FULL_PROFILE')==1
assert 'glDeleteProgram(rgbDown)' in ck and 'glDeleteProgram(clipDown)' in ck
# Protect unchanged A producer; B native additions are isolated source markers.
assert 'IRIS_26570_TRUE2X_RENDER_ENCODE_PIPELINE' in cc
assert 'IRIS_26864_WRONSKI_STRIPED_RGBA16F_TRANSPORT' in ck
assert (cand/'app/version.properties').read_text().splitlines()[-2:]==['VERSION_NAME=0.9726876','VERSION_BUILD=26876']
print('26876 B SINGLE WRONSKI + SENSOR CLIP + GPU DCP/WATERMARK OWNER PASS')
