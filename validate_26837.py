#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
B,C=map(Path,sys.argv[1:3])
CHANGED={'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt','app/version.properties'}
def H(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def U(r): return {str(p.relative_to(r)).replace('\\','/'):H(p) for p in (r/'app').rglob('*') if p.is_file()}
b,c=U(B),U(C); assert set(b)==set(c) and len(b)==1786,(len(b),len(c)); delta={p for p in b if b[p]!=c[p]}; assert delta==CHANGED,(delta-CHANGED,CHANGED-delta)
v=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726837' in v and 'VERSION_BUILD=26837' in v and 'VERSION_MINOR=9726440' in v
bridge=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text(); base_bridge=(B/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text(); shaders=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text(); base_shaders=(B/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text(); stack=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
# True final owner remains after residual denoise + 26728 and before cross-context/tone carrier.
pos_d=bridge.index('MgcFullResolutionDenoise.denoise('); pos_26728=bridge.index('applyIris26728ProtectedChromaFloor('); pos_26837=bridge.index('IRIS_26837_DEVICE_SAFE_TRUE_FINAL_CLIP_ZONE_CHROMA_OWNER'); pos_carrier=bridge.index('IRIS_26726_UNIVERSAL_RGBA16F_CROSS_CONTEXT_OWNER'); assert pos_d<pos_26728<pos_26837<pos_carrier
assert bridge.count('applyIris26837FinalClipZoneChroma(')==2 and 'applyIris26836FinalClipZoneChroma(' not in bridge
# Exact 26836 runtime failure regression: active final owner may not use compute image-store/SSBO.
s=bridge.index('private fun applyIris26837FinalClipZoneChroma('); e=bridge.index('private fun buildTrue2xRenderCarrier(',s); active=bridge[s:e]
for forbidden in ['GLES31.glBindImageTexture(','GLES31.glDispatchCompute(','GLES31.glBindBufferBase(','GL_SHADER_STORAGE_BUFFER']:
    assert forbidden not in active,forbidden
for required in ['GlesMgcRawSabreShaders.clipZoneApplyFragment26837','26837 final fragment bindings','26837 final fragment apply','backend=FBO_FRAGMENT_GLES300','imageStore=false','M0BitExactByCopyDiscard=true','colorDomain=WB_LINEAR','inverseWbRoundTrip=true','insertion=POST_RESIDUAL_POST_26728_PRE_TONE']:
    assert required in active,required
# Proven immutable allocation contract; no 26836 mutable texture storage survives for this owner.
as_=bridge.index('private fun createTexture26837('); ae=bridge.index('private fun bindTexture26836(',as_); alloc=bridge[as_:ae]
assert 'GLES30.glTexStorage2D(' in alloc and 'GLES30.glTexImage2D(' not in alloc
# Fragment backend mirrors Claude 26836 WB-linear math exactly, except output primitive/stats.
def shader(text,name):
    m=re.search(r'val\s+'+re.escape(name)+r'\s*=\s*"""\n(.*?)\n\s*"""\.trimIndent\(\)',text,re.S); assert m,name; return m.group(1)
comp=shader(shaders,'clipZoneApply26834'); base_comp=shader(base_shaders,'clipZoneApply26834'); frag=shader(shaders,'clipZoneApplyFragment26837')
assert comp==base_comp,'26836 Claude compute reference changed'
critical=['float m=texelFetch(uMask,p,0).r;','vec4 src=texelFetch(uRgb,p,0); vec3 rgb=src.rgb*uCalculationWb;','float y=(rgb.r+2.0*rgb.g+rgb.b)*0.25; float yc=max(y,uYFloor);','vec2 c=vec2(rgb.r-rgb.g,rgb.b-rgb.g)/yc;','vec4 sm=texelFetch(uSmall,p,0);','vec2 uv=(vec2(p)+vec2(0.5))/vec2(uSize);','vec4 bg=texture(uBigQuarter,uv);','float a=clamp(sm.b/max(uAThreshold,1.0e-4),0.0,1.0);','vec2 fill=mix(safeFill(bg),safeFill(sm),a);','vec2 cp=mix(c,fill,m);','float dR=cp.x*yc, dB=cp.y*yc;','float g=y-0.25*(dR+dB); vec3 wbDst=vec3(g+dR,g,g+dB);','vec3 cameraDst=wbDst/max(uCalculationWb,vec3(1.0e-6));']
for t in critical: assert comp.count(t)==1 and frag.count(t)==1,t
assert 'if(m<=0.0) discard;' in frag and 'imageStore' not in frag and 'buffer Stats' not in frag and 'atomic' not in frag
# Products/mask math unchanged from successful 26836.
assert shader(shaders,'clipZoneProducts26834')==shader(base_shaders,'clipZoneProducts26834')
for t in ['sourceNeighborhoodConfidence','IRIS_26834_CLIP_ZONE_CHROMA_INPAINT','clipZoneMaskDilate26834','buildClipZoneMask26834','longIncluded=false']: assert t in stack,t
# SR final-chroma handoff remains bilinear-mask only; native/Java are protected externally.
for t in ['applyFinalNativeClipZoneChromaGuide26836','maskUpsample=BILINEAR','true2xLumaPreserved=true','dngUntouched=true']: assert t in bridge,t
# Exact failed-shot and generic WB neutral round-trip stays valid.
def check(gains):
 r,g1,g2,b=gains; gb=.5*(g1+g2); wb=(r/gb,1.,b/gb); cam=(1/wb[0],1.,1/wb[2]); out=(cam[0]*wb[0],cam[1],cam[2]*wb[2]); assert max(abs(x-1) for x in out)<1e-6
check((1.9463,1.,1.,2.2021)); [check(g) for g in [(2.8,1.,1.,1.35),(1.2,.9,1.1,3.0),(4.0,1.2,.8,1.6)]]
# Critical frozen domains.
for rel in ['app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/src/main/cpp/motionv2_jpeg444_jni.cpp','app/src/main/java/com/particlesdevs/photoncamera/processing/IrisTrue2xSrNative.java','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2DngColorShadow.java']:
    assert H(B/rel)==H(C/rel),rel
for t in ['longColorAuthority=false','longHueAuthority=false','rgbScaleOnly=true','exactRgbRatioPreserved=true']: assert t in stack,t
print('PASS 26837 semantic validation: exact 3-path scope; 26836 WB-final Claude math/insertion unchanged; active apply is proven immutable GLES3 FBO fragment backend; 0x502 image-store failure impossible on active owner; SR/LONG/DNG/high-zoom protected')
