#!/usr/bin/env python3
from pathlib import Path
import sys,hashlib,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26743_regressions.py BASE26742 CAND26743')
b=Path(sys.argv[1]); c=Path(sys.argv[2]); pkg=Path(__file__).resolve().parent
def txt(r,p): return (r/p).read_text()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
expected={
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/version.properties'}
changed=set((pkg/'26743_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()); assert changed==expected,(changed,expected)
v=txt(c,'app/version.properties'); assert 'VERSION_NAME=0.9726743' in v and 'VERSION_BUILD=26743' in v
cppp='app/src/main/cpp/motionv2_jpeg444_jni.cpp'; shp='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'; stp='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'; vgp='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
cpp=txt(c,cppp); sh=txt(c,shp); st=txt(c,stp); vg=txt(c,vgp)
# 26742 wrong-domain experiment must be completely gone from all reconstruction owners.
for t in ['IRIS_26742_SOURCE_VALID_CHROMA_ACCUMULATION','IRIS_26742_SOURCE_HEADROOM_MARGIN','sourceValidMean26742','chromaAuthority26742','IRIS_26742_TRUE2X_SOURCE_VALID_CHROMA','IRIS_26742_TRUE2X_CPU_SOURCE_VALID_CHROMA','clipStart26742']:
 assert t not in cpp+sh+st,t
# Three reconstruction owners are restored byte-for-byte to exact successful 26741 values.
exact26741={
 cppp:'19d78a2cd6ef2a7f1fb74fd10ce0d17f7619b3f148e1eec2cee2c6938a2626fe',
 shp:'95c862d60ca829ad348e3b767f461cbc8d2083eacea07d3cef851a5f38bf1a57',
 stp:'13c3ef68131b2eb3a762935a0bb332b9bd969decb90bede6ce34c090cd0ff9aa'}
for p,h in exact26741.items(): assert sha(c/p)==h,(p,sha(c/p),h)
# Existing NORMAL/SHORT/LONG and high-zoom physical-validity behavior returns to 26741 mechanics.
for t in ['IRIS_26558_SABRE_SHADOW_LONG_SOURCE_CLIP_GUARD','IRIS_26648_SAMPLE_LEVEL_SHORT_VALIDITY','IRIS_26739_HIGH_ZOOM_PHYSICAL_VALIDITY','uSourceClippingPoint*0.9925']:
 assert t in sh+st,t
for t in ['IRIS_26740_HIGH_ZOOM_RECONSTRUCTION_CONFIDENCE_GATE','IRIS_26741_TRUE2X_CONFIDENCE_PUBLICATION','IRIS_26741_TRUE2X_SHAPE_STABILITY_AND_FAIL_CLOSED_PUBLICATION']:
 assert t in sh,t
# Final visual highlight authority is explicit, post-WB, and final after all earlier color owners.
for t in ['IRIS_26743_VISIBLE_HIGHLIGHT_NEUTRALITY_WB_DOMAIN','IRIS_26743_RENDERED_HIGHLIGHT_APPEARANCE_AUTHORITY','IRIS_26743_VISIBLE_FLATTENED_HIGHLIGHT_NEUTRAL_AUTHORITY','visiblePhysicalRgb26743','visibleHighlightLuma26743','visibleHighlightNeutralAuthority26743','correctedRgb * uCalculationGains','neutralizedCalculationRgb26743','protectedPreVgnMagnitude *= 1.0 - visibleHighlightNeutralAuthority26743']:
 assert t in vg,t
assert 'smoothstep(0.72, 0.92, visibleCenterLuma26743)' in vg
assert 'smoothstep(0.58, 0.72, visibleCenterLuma26743)' in vg
assert 'if (uPhysicalPreVgnValid != 0)' in vg and 'return max(loadRgb(q) * uCalculationGains' in vg
# Final owner must occur after existing 26728/26741 restoration logic, so material/topology cannot repaint it.
idx_final=vg.index('IRIS_26743_VISIBLE_FLATTENED_HIGHLIGHT_NEUTRAL_AUTHORITY')
for earlier in ['IRIS_26741_CLIPPED_FLATTENED_HIGHLIGHT_NEUTRAL_AUTHORITY','IRIS_26728_PHYSICALLY_SUPPORTED_CHROMA_MAGNITUDE','IRIS_26740_HEADROOM_OVERRIDE_REQUIRES_PHYSICAL_REAL_COLOR']:
 assert vg.index(earlier)<idx_final,(earlier,idx_final)
# Proven color/material owners stay present for non-extreme brightness.
for t in ['IRIS_26729_COLOR_MATERIAL_DIRECTION_GATE','IRIS_26731_FROZEN_RECIPROCAL_MATERIAL_OWNERSHIP','IRIS_26731_DIRECTION_PAIR_GEOMETRY','IRIS_26735_INDEPENDENT_PHYSICAL_REAL_COLOR_PROOF','IRIS_26741_STRONG_ACHROMATIC_FINE_STRUCTURE_AUTHORITY']:
 assert t in vg,t
# No broad denoise/saturation/sharpening/semantic detector change is part of this build.
joined=(cpp+sh+st+vg).lower()
for forbidden in ['barcode_detector','font_detector','text_detector','semanticclass','plan_b_26743','ipol_26743','chroma_sharpen_26743','global_chroma_denoise_26743']:
 assert forbidden not in joined,forbidden
# Major protected owners remain byte-identical from successful 26742 authority.
protected=[
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java',
'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java',
'app/src/main/java/com/hinnka/mycamera/raw/MgcFullResolutionDenoise.kt']
for p in protected: assert (b/p).read_bytes()==(c/p).read_bytes(),p
print('PASS 26743 regressions: 26742 pre-WB chroma synthesis fully removed; reconstruction owners exact successful 26741; final visible highlight neutrality is calculation-WB-domain, fusion/non-fusion aware, 0.72..0.92 core plus immediate 0.58..0.72 fringe; 26729+/26731 real-color owners preserved below extreme highlight regime')
