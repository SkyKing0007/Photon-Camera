#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26646_r1.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def txt(root,r): return (root/r).read_text()
def sha(root,r): return hashlib.sha256((root/r).read_bytes()).hexdigest()
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'app').rglob('*')) if p.is_file()}
allow=set(Path(__file__).resolve().with_name('R1_26646_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines())-{''}
a,b=H(base),H(cand); assert len(a)==len(b)==1720
changed={r for r in a if a[r]!=b[r]}; assert changed==allow,(changed,allow); assert len(changed)==9
ver=txt(cand,'app/version.properties'); assert 'VERSION_NAME=0.9726646' in ver and 'VERSION_BUILD=26646' in ver
# SHORT: keep 26644 fail-closed physical support and old literal/effective owners; only new same-domain visual proof bypasses sparse componentTrust.
k0=txt(base,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'); k=txt(cand,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
for m in ['IRIS_26644_SHORT_SOURCE_SUPPORT_FAIL_CLOSED','IRIS_26644_SHORT_WARP_DOMAIN_FAIL_CLOSED','IRIS_26644_SHORT_EXTRACTED_BILINEAR_FAIL_CLOSED','IRIS_26645_PER_PIXEL_VISUAL_RADIANCE_PROOF','IRIS_26646_UNIVERSAL_HIGH_DYNAMIC_RANGE_SHORT_OWNER']:
 assert k.count(m)==1,m
for token in ['smoothstep(0.72, 0.92, predicted)','smoothstep(0.05, 0.12, relativeLoss)','smoothstep(0.94, 0.98, reference)','smoothstep(0.12, 0.22, relativeLoss)']:
 assert k.count(token)==k0.count(token) and k.count(token)>=2,token
assert 'float visualRadianceConfidence = min(shortHeadroom, clamp(visualHighRadiance, 0.0, 1.0));' in k
assert 'float visualRescueWeight = physicalWeight * visualRadianceConfidence;' in k
assert 'visualRescueWeight = censoredCoreWeight * clamp(visualHighRadiance, 0.0, 1.0);' not in k
assert 'float censoredCoreWeight = min(physicalWeight, rescueConfidence);' in k
assert 'if (!shortSupportValid)' in k and 'mirrorUvs(referenceUv + flow.xy)' not in k[k.index('val shortRescueWeight26607'):k.index('""".trimIndent()',k.index('val shortRescueWeight26607'))]
# Tone: carry only bounded same-material interior SourceLinear residual into scalar log-luma presentation.
g=txt(cand,'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl')
for m in ['IRIS_26646_EDGE_ISOLATED_SOURCE_RADIANCE_SURVIVAL','IRIS_26646_EXTENDED_LINEAR_RADIANCE_SURVIVAL_OWNER','IRIS_26645_STRUCTURE_AWARE_HIGHLIGHT_BASE']:
 assert g.count(m)==1,m
for token in ['if(admitted<3||weightSum<2.55) continue;','float boundedMissing=min(missing,0.18);','float reserveEv=0.40*iris26646Radiance.y*iris26646Radiance.z*upperGate;','Output=clamp(outLog,-12.0,0.0);']:
 assert token in g,token
assert 'texelFetch(SourceLinear' in g and 'texelFetch(CurrentToneLog' in g
# HEIC: hardware HEVC encoder/full-range contract remains exact 26645; native publisher adds true2x 2x2 grid with ISO21496 gain relation.
hw='app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHardwareHevcEncoder.java'; assert sha(base,hw)==sha(cand,hw)
hwt=txt(cand,hw); assert 'MediaFormat.KEY_COLOR_RANGE, MediaFormat.COLOR_RANGE_FULL' in hwt and 'outRange != MediaFormat.COLOR_RANGE_FULL' in hwt
assert 'format.setInteger(MediaFormat.KEY_COLOR_STANDARD' not in hwt and 'format.setInteger(MediaFormat.KEY_COLOR_TRANSFER' not in hwt
n=txt(cand,'app/src/main/cpp/iris_heic_jni.cpp')
for token in ['IRIS_26646_TRUE2X_HEIC_GRID_OWNER','heif_context_add_grid_image(ctx','2u, 2u, options, &baseHandle','heif_context_set_primary_image(ctx, baseHandle)','heif_context_add_image_tile(','heif_context_encode_gain_map_image(ctx, baseHandle','halfLinearGain=true','heif_color_primaries_SMPTE_EG_432_1','heif_transfer_characteristic_IEC_61966_2_1','gainmapNclx->full_range_flag = true']:
 assert token in n,token
assert 'isoMetadata.insert' not in n and 'x265' not in n.lower()
c=txt(cand,'app/src/main/cpp/CMakeLists.txt'); assert 'target_link_libraries(irisheic PRIVATE heif jpeg-static iris26507-ultrahdr log jnigraphics android z)' in c
patch='app/src/main/cpp/iris26643_libheif_aosp_contract.patch'; assert sha(base,patch)==sha(cand,patch)
# Route: SR+HEIC is first-class, uses exact true2x renderer, has no 12MP/JPEG fallback; post-save Android recognition is diagnostic only.
h=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHeicUltraHdrEncoder.java')
for token in ['IRIS_26646_TRUE2X_HEIC_ULTRAHDR_GRID_PUBLICATION','writeSuperResGridNative(','IRIS_26646_HEIC_ANDROID_READBACK','destructiveFailure=false','readbackFailureNonDestructive=true']:
 assert token in h,token
assert 'if (!ok) Files.deleteIfExists(output);' not in h
m=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java')
for token in ['IRIS_26646_TRUE2X_HEIC_SHARED_RENDER_OWNER','writeTrue2xHeic(','IrisHeicUltraHdrEncoder.writeSuperResGrid(','jpegRFallback=false native12mpFallback=false']:
 assert token in m,token
i=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java')
for token in ['IRIS_26646_MOTION_HEIC_ULTRAHDR_ROUTE_OWNER','saveBitmapAsHEICUltraHdrMotionV2(','native12mpFallback=false','iris26642ScheduleUltraHdrDecodeProof(fileToSave']:
 assert token in i,token
x=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java')
assert 'IRIS_26646_SUPER_RES_HEIC_ROUTE_ENABLED' in x and 'saveBitmapAsHEICUltraHdrMotionV2(' in x
# 26645 manual popup cleanup is protected unchanged.
u='app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java'; assert sha(base,u)==sha(cand,u)
print('PASS 26646 semantics: universal correlated-radiance SHORT + edge-isolated extended-linear tone survival + true2x hardware-HEVC HEIF grid Ultra HDR + non-destructive Android readback; proven 26645 HEVC/UI owners retained')
