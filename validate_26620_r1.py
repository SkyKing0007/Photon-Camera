#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
if len(sys.argv)!=3: raise SystemExit('usage: validate_26620_r1.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2])
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'app').rglob('*')) if p.is_file()}
bh,ch=H(B),H(C)
assert len(bh)==1708 and len(ch)==1711,(len(bh),len(ch))
changed=sorted(p for p in set(bh)|set(ch) if bh.get(p)!=ch.get(p))
expected=sorted([
'app/src/main/assets/shaders/motionv2/local_laplacian_correction_26620.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_downsample_26620.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_seed_26620.glsl',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/version.properties'])
assert changed==expected,(changed,expected)
ver=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726620' in ver and 'VERSION_BUILD=26620' in ver
# Image-formation, exposure solver, color, gainmap, graph routing and DNG owners are not reopened.
protected=[
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2DngColorShadow.java']
for rel in protected: assert (B/rel).read_bytes()==(C/rel).read_bytes(),f'protected owner changed: {rel}'
# Exact 26614 global presentation functions stay byte-identical inside the modified render shader.
def func(text,name):
    m=re.search(r'(^|\n)(?:[A-Za-z_][\w<>]*\s+)+%s\s*\([^\n]*\)\s*\{'%re.escape(name),text)
    assert m,f'function missing {name}'
    start=m.start()+ (1 if text[m.start():m.start()+1]=='\n' else 0)
    brace=text.find('{',m.start()); depth=0
    for i in range(brace,len(text)):
        if text[i]=='{': depth+=1
        elif text[i]=='}':
            depth-=1
            if depth==0: return text[start:i+1]
    raise AssertionError(f'unclosed function {name}')
br=(B/'app/src/main/assets/shaders/motionv2/render.glsl').read_text(); cr=(C/'app/src/main/assets/shaders/motionv2/render.glsl').read_text()
for name in ['iris26614MapMotionSdrFinalGuide','mapFinalSdrGuide','mapExtendedLinearHeadroom','fitDisplayGamut']:
    assert func(br,name)==func(cr,name),f'26614 global tone/gamut function changed: {name}'
# One local owner lives inside MotionV2Render after the exact global map, not as a graph node.
rj=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
for tok in ['IRIS_26620_MULTISCALE_LOCAL_LAPLACIAN_OWNER','IRIS_26620_LAPLACIAN_LEVELS = 8',
            'iris26620BuildLocalLaplacianCorrection(extendedLinearHdr)','motionv2/local_laplacian_seed_26620',
            'motionv2/local_laplacian_downsample_26620','motionv2/local_laplacian_correction_26620',
            'motionV2DisplayGain','OUTPUT_EXPOSURE_SCALE','rgbScalarOnly=true','true2xSharedMap=']:
    assert tok in rj,tok
assert rj.count('iris26620BuildLocalLaplacianCorrection(extendedLinearHdr)')==1
# Seed computes source/global log guides using the exact 26614 gain formula; later pyramid stages have no exposure input.
seed=(C/'app/src/main/assets/shaders/motionv2/local_laplacian_seed_26620.glsl').read_text()
down=(C/'app/src/main/assets/shaders/motionv2/local_laplacian_downsample_26620.glsl').read_text()
corr=(C/'app/src/main/assets/shaders/motionv2/local_laplacian_correction_26620.glsl').read_text()
for tok in ['uniform float displayGain','uniform float outputExposureScale','iris26614MapMotionSdrFinalGuide','requestedFinalGain=max(displayGain,1.0e-6)*max(outputExposureScale,1.0e-6)','out vec2 Output']:
    assert tok in seed,tok
for later in [down,corr]:
    assert 'displayGain' not in later and 'outputExposureScale' not in later,'duplicate exposure authority in local pyramid'
for tok in ['center=q*2','sum*(1.0/256.0)']:
    assert tok in down,tok
for tok in ['IRIS_26620_MULTISCALE_LOCAL_LAPLACIAN_PRESENTATION','preserveCompressedBand','compression=max(as-am,0.0)',
            'return mix(mappedBand,sourceBand,blend)','p0.g-p1.g,p0.r-p1.r,0.00','IRIS_26620_BLACK_CRUSH_PROTECTION',
            'smoothstep(0.080,0.200,mappedGuide)','softLimit(correctionEv,0.55)']:
    assert tok in corr,tok
# Final application is a common RGB scalar after the unchanged global map, with explicit positive headroom guard.
for tok in ['linearSrgb=mapExtendedLinearHeadroom(linearSrgb);','iris26620LocalLaplacianEnabled','sourcePixel*0.5',
            'availableUpEv','linearSrgb*=exp2(correctionEv);','linearSrgb=fitDisplayGamut(linearSrgb);']:
    assert tok in cr,tok
assert cr.find('linearSrgb=mapExtendedLinearHeadroom(linearSrgb);') < cr.find('linearSrgb*=exp2(correctionEv);') < cr.find('linearSrgb=fitDisplayGamut(linearSrgb);')
assert 'sourcePixel=vec2(sourceXY);' in cr,'26614 left-edge source coordinate not propagated to local field'
# True-2x shares the exact produced correction field; no separate true-2x local-tone solve.
params=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java').read_text()
enc=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java').read_text()
cpp=(C/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
for tok in ['motionV2LocalLaplacianMap','motionV2LocalLaplacianWidth','motionV2LocalLaplacianHeight','motionV2LocalLaplacianSourceWidth','motionV2LocalLaplacianSourceHeight']:
    assert tok in params and tok in enc,tok
for tok in ['localLaplacianMap','localLaplacianW','localLaplacianH','localLaplacianSourceW','localLaplacianSourceH']:
    assert tok in cpp,tok
for tok in ['IRIS_26620_TRUE2X_SHARED_LOCAL_LAPLACIAN_MAP','localLaplacianEv','mapCoord=oneSource*0.5',
            'IRIS_26620_TRUE2X_LOCAL_LAPLACIAN_AFTER_GLOBAL','uLocalLaplacianMap','IRIS_26620_TRUE2X_LOCAL_LAPLACIAN_GPU_SHARED_FIELD',
            'iris26564::halfToFloat']:
    assert tok in cpp,tok
# Permanent 26619 native-name-resolution regression: any inherited smooth01 call in this translation unit
# must remain explicitly namespace-qualified unless it is a local lambda/definition; the new 26620 path
# itself uses no unqualified smooth01 symbol.
ll=cpp[cpp.index('/* IRIS_26620_TRUE2X_SHARED_LOCAL_LAPLACIAN_MAP'):cpp.index('inline Vec3 mat',cpp.index('/* IRIS_26620_TRUE2X_SHARED_LOCAL_LAPLACIAN_MAP'))]
assert 'smooth01(' not in ll,'26619 unqualified native helper regression in 26620 owner'
# Java JNI declaration and C++ entry point must carry the same five Local-Laplacian parameters in order.
jsig='ByteBuffer localLaplacianMap, int localLaplacianWidth, int localLaplacianHeight,\n            int localLaplacianSourceWidth, int localLaplacianSourceHeight'
csig='jobject localLaplacianBuffer,jint localLaplacianW,jint localLaplacianH,jint localLaplacianSourceW,jint localLaplacianSourceH'
assert jsig in enc and csig in cpp,'true2x JNI Local-Laplacian signature mismatch'
# Later failed experimental presentation owners must not be resurrected from repository source.
owned='\n'.join([seed,down,corr,cr,rj])
for forbidden in ['guided_base_detail_ltm','adaptive_wronski','IRIS_26618_GUIDED','IRIS_26619_GUIDED']:
    assert forbidden not in owned,forbidden
print('PASS 26620 semantic/ownership/domain validation: exact 9-path delta from successful 26614; one display-gain owner; multiscale scalar local presentation shared by 1x/true2x')
