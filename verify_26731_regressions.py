#!/usr/bin/env python3
from pathlib import Path
import sys,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26731_regressions.py BASE26730 CAND26731')
b=Path(sys.argv[1]); c=Path(sys.argv[2]); pkg=Path(__file__).resolve().parent
def txt(r,p): return (r/p).read_text()
changed=set((pkg/'26731_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()); assert changed=={'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt','app/version.properties'}
v=txt(c,'app/version.properties'); assert 'VERSION_NAME=0.9726731' in v and 'VERSION_BUILD=26731' in v
vgn=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
# Freeze successful 26729/26730 true-color retention and physical validity owners.
for t in ['IRIS_26729_COLOR_MATERIAL_DIRECTION_GATE','IRIS_26729_COLOR_MATERIAL_MEDIAN_GATE','IRIS_26730_PHYSICAL_VALIDITY_CONTAINMENT_AUTHORITY','IRIS_26730_TRUE_MATERIAL_STEP_GATE','IRIS_26728_PHYSICALLY_SUPPORTED_CHROMA_MAGNITUDE','IRIS_26579_MICRO_OBJECT_COLOR_TOPOLOGY','IRIS_26580_MICRO_OBJECT_AREA_VS_RIBBON']:
 assert t in vgn,t
# 26731 geometry/transport authority.
for t in ['IRIS_26731_ISOLATED_FALSE_COLOR_CLEANUP_FLAG','IRIS_26731_FROZEN_RECIPROCAL_MATERIAL_OWNERSHIP','IRIS_26731_DIRECTION_PAIR_GEOMETRY','IRIS_26731_RECIPROCAL_ONE_SIDED_DIRECTIONAL','cleanupFallbackAt','IRIS_26731_FROZEN_IIR_MATERIAL_OWNERSHIP','layout(rgba16ui,binding=2) readonly uniform highp uimage2D uOwnership;','bindImage(2, ownership, GLES31.GL_READ_ONLY)','smoothYccd, scratchYccd, originalYccd, coefficients.pass1','filteredYccd, finalScratch, originalYccd, coefficients.pass3']:
 assert t in vgn,t
# Exact geometric pairs: W/E, N/S, NE/SW, NW/SE. Old adjacent-bit pairing cannot survive.
for t in ['ivec2(-1,0),3,1,ivec2(1,0),1,3','ivec2(0,-1),0,2,ivec2(0,1),2,0','ivec2(1,-1),4,6,ivec2(-1,1),6,4','ivec2(-1,-1),7,5,ivec2(1,1),5,7']:
 assert t in vgn,t
for bad in ['if((direction&(1<<0))!=0){selected+=vec3(cr[0]','if((direction&(1<<2))!=0){selected+=vec3(cr[1]','colorOnlyMaterialBoundary=','trueMaterialStep=(chromaJump/withinScale)']:
 assert bad not in vgn,bad
assert vgn.count('if(!reciprocalConnected(p,delta)){colorBoundaryProtection=1.0;continue;}')==1
assert vgn.count('bool frozenMaterialBoundary=i>0&&!transportFromPreviousAllowed(p,previousP);')==1
# No settings/native/fusion/bridge changes: the 26730 versions are byte-identical.
for p in [
'app/src/main/java/com/hinnka/mycamera/raw/MgcFullResolutionDenoise.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java']:
 assert (b/p).read_bytes()==(c/p).read_bytes(),p
# Permanent 26729 R2 Java-overload regression remains applicable even though settings are protected.
pk=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java')
assert not re.search(r'setInitial\(\s*SCOPE_GLOBAL\s*,\s*"[^"]+"\s*,\s*(?:true|false)\s*\)',pk)
print('PASS 26731 regressions: 26729/26730 true-color retention frozen; exact direction geometry; reciprocal one-sided chroma transport; frozen IIR ownership; residual MGC/fusion/settings/native/UHDR protected')
