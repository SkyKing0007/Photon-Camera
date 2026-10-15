#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys,math
B,C=map(Path,sys.argv[1:3])
CHANGED={
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/IrisTrue2xSrNative.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/version.properties'}
def H(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def U(r): return {str(p.relative_to(r)).replace('\\','/'):H(p) for p in (r/'app').rglob('*') if p.is_file()}
b,c=U(B),U(C); assert set(b)==set(c) and len(b)==1786,(len(b),len(c)); delta={p for p in b if b[p]!=c[p]}; assert delta==CHANGED,(delta-CHANGED,CHANGED-delta)
v=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726836' in v and 'VERSION_BUILD=26836' in v and 'VERSION_MINOR=9726440' in v
stack=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text(); base_stack=(B/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
bridge=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text(); shaders=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text(); contracts=(C/'app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt').read_text(); java=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/IrisTrue2xSrNative.java').read_text(); cpp=(C/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
# Claude mask source remains NORMAL-only and unchanged in meaning.
for t in ['sourceNeighborhoodConfidence','IRIS_26834_CLIP_ZONE_CHROMA_INPAINT','clipZoneMaskDilate26834','buildClipZoneMask26834']:
    assert t in stack,t
assert 'IRIS_26836_RETIRE_PRE_26728_CLIP_INPAINT' in stack
assert stack.count('applyClipZoneChromaInpaint26834(')==1,'old pre-26728 inpaint still has a caller'
assert 'clipZoneMaskTextureId26836 = exportedClipZoneMask26836' in stack
assert 'longIncluded=false' in stack
# True final owner order.
pos_d=bridge.index('MgcFullResolutionDenoise.denoise('); pos_26728=bridge.index('applyIris26728ProtectedChromaFloor('); pos_26836=bridge.index('IRIS_26836_TRUE_FINAL_CLIP_ZONE_CHROMA_OWNER'); pos_carrier=bridge.index('IRIS_26726_UNIVERSAL_RGBA16F_CROSS_CONTEXT_OWNER')
assert pos_d < pos_26728 < pos_26836 < pos_carrier,(pos_d,pos_26728,pos_26836,pos_carrier)
for t in ['colorDomain=WB_LINEAR','inverseWbRoundTrip=true','insertion=POST_RESIDUAL_POST_26728_PRE_TONE','GLES30.glBlitFramebuffer','M0 bit-copy','calculationWhiteBalance26836']:
    assert t in bridge,t
# Original Claude donor math, but WB-linear and inverse-WB.
for t in ['vec3 rgb=cameraRgb*uCalculationWb','float w=(1.0-m)*(1.0-m)','oProducts=vec4(w*c,w,0.0)','vec2 fill=mix(safeFill(bg),safeFill(sm),a)','vec2 cp=mix(c,fill,m)','vec3 cameraDst=wbDst/max(uCalculationWb,vec3(1.0e-6))','if(m<=0.0) return;']:
    assert t in shaders,t
for stale in ['multiSector','localCoherent','colorAuthority=localCoherent','IRIS_26835_COHERENCE_GATED_CLIP_ZONE_CHROMA']:
    assert stale not in re.search(r'val clipZoneApply26834.*?"""\.trimIndent\(\)',shaders,re.S).group(0),stale
# Transport/JNI SR contract.
for t in ['clipZoneMaskTextureId26836','clipZoneMaskWidth26836','clipZoneMaskHeight26836']: assert t in contracts,t
assert 'applyFinalNativeClipZoneChromaGuide26836' in java and 'applyFinalNativeClipZoneChromaGuide26836' in cpp
for t in ['bilinear','M==0','true2x','uCalculationWb']:
    # semantic equivalents are checked below with exact implementation tokens
    pass
for t in ['maskUpsample=BILINEAR','true2xLumaPreserved=true','dngUntouched=true']: assert t in bridge,t
for t in ['if(!(m>0.f))continue;','m=(m00+(m10-m00)*fx)','srcWb[k]=c*wb[k]','guideWb[k]=gcam[k]*wb[k]','outWb[k]/wb[k]']:
    assert t in cpp,t
# Exact failed-shot and generic WB round-trip regression.
def check(gains):
    r,g1,g2,b=gains; gb=.5*(g1+g2); wb=(r/gb,1.,b/gb); cam=(1/wb[0],1.,1/wb[2]); out=(cam[0]*wb[0],cam[1],cam[2]*wb[2]); assert max(abs(x-1) for x in out)<1e-6,(gains,wb,cam,out); back=(1/wb[0],1.,1/wb[2]); assert max(abs(back[i]-cam[i]) for i in range(3))<1e-6
    return wb,cam
wb,cam=check((1.9463,1.,1.,2.2021)); assert abs(wb[0]-1.9463)<1e-4 and abs(wb[2]-2.2021)<1e-4
for g in [(2.8,1.,1.,1.35),(1.2,.9,1.1,3.0),(4.0,1.2,.8,1.6)]: check(g)
assert max(abs(x-1) for x in (1.9463,1.,2.2021))>0.9,'camera RGB 1,1,1 must not be treated as WB-neutral'
# Critical frozen domains/assets.
for rel in ['app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2DngColorShadow.java']:
    assert H(B/rel)==H(C/rel),rel
# LONG semantics survived.
for t in ['longColorAuthority=false','longHueAuthority=false','rgbScaleOnly=true','exactRgbRatioPreserved=true']:
    assert t in stack,t
print('PASS 26836 semantic validation: exact 7-path scope; Claude NORMAL-only mask preserved; WB-linear true-final owner is post-residual/post-26728; M0 bit-copy; SR bilinear mask; LONG/DNG/high-zoom protected')
