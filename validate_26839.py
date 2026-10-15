#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
B,C=map(Path,sys.argv[1:3])
CHANGED={'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt','app/version.properties'}
def H(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def U(r): return {str(p.relative_to(r)).replace('\\','/'):H(p) for p in (r/'app').rglob('*') if p.is_file()}
def shader(text,name):
 m=re.search(r'val\s+'+re.escape(name)+r'\s*=\s*"""\n(.*?)\n\s*"""\.trimIndent\(\)',text,re.S); assert m,name; return m.group(1)
b,c=U(B),U(C); assert set(b)==set(c) and len(b)==1786,(len(b),len(c)); delta={p for p in b if b[p]!=c[p]}; assert delta==CHANGED,(delta-CHANGED,CHANGED-delta)
v=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726839' in v and 'VERSION_BUILD=26839' in v and 'VERSION_MINOR=9726440' in v
bridge=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text(); bb=(B/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text(); shaders=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text(); bs=(B/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text(); stack=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
# Preserve successful 26838 owner placement and successful 26837 GLES3 FBO lifecycle.
pos_d=bridge.index('MgcFullResolutionDenoise.denoise('); pos_26728=bridge.index('applyIris26728ProtectedChromaFloor('); pos_owner=bridge.index('IRIS_26837_DEVICE_SAFE_TRUE_FINAL_CLIP_ZONE_CHROMA_OWNER'); pos_carrier=bridge.index('IRIS_26726_UNIVERSAL_RGBA16F_CROSS_CONTEXT_OWNER'); assert pos_d<pos_26728<pos_owner<pos_carrier
assert bridge.count('applyIris26837FinalClipZoneChroma(')==2
s=bridge.index('private fun applyIris26837FinalClipZoneChroma('); e=bridge.index('private fun buildTrue2xRenderCarrier(',s); active=bridge[s:e]
for forbidden in ['GLES31.glBindImageTexture(','GLES31.glDispatchCompute(','GLES31.glBindBufferBase(','GL_SHADER_STORAGE_BUFFER']:
 assert forbidden not in active,forbidden
for required in ['GlesMgcRawSabreShaders.clipZoneApplyFragment26839','26839 final fragment bindings','26839 final fragment apply','IRIS_26839_CLIP_ZONE_CHROMA','backend=FBO_FRAGMENT_GLES300','maskTailExactNoop=true','broadHueAuthority=false','sourceHueDirectionOwner=true','donorMagnitudeOnly=true','hueRequiresSourceSmallBroadConsensus=true','neutralWhiteFallback=false','warmTerminalFallback=true','colorDomain=WB_LINEAR','inverseWbRoundTrip=true','insertion=POST_RESIDUAL_POST_26728_PRE_TONE']:
 assert required in active,required
# Exact successful 26838 FBO allocation/copy/draw/readback mechanics; only shader linkage/check labels/telemetry differ.
def normalize_active(x):
 x=x.replace('clipZoneApplyFragment26839','clipZoneApplyFragment26838').replace('26839 final fragment bindings','26838 final fragment bindings').replace('26839 final fragment apply','26838 final fragment apply')
 x=re.sub(r'PLog\.i\(TAG,"IRIS_26839_CLIP_ZONE_CHROMA[^\n]+\)','__LOG__',x)
 x=re.sub(r'PLog\.i\(TAG,"IRIS_26838_CLIP_ZONE_CHROMA[^\n]+\)','__LOG__',x)
 return x
bs0=bb[bb.index('private fun applyIris26837FinalClipZoneChroma('):bb.index('private fun buildTrue2xRenderCarrier(',bb.index('private fun applyIris26837FinalClipZoneChroma('))]
assert normalize_active(active)==normalize_active(bs0),'successful 26838 FBO lifecycle/mechanics changed beyond approved shader link/check labels/log'
# 26838 active shader and earlier products/mask math remain byte-identical historical references.
for name in ['clipZoneApplyFragment26838','clipZoneApplyFragment26837','clipZoneApply26834','clipZoneProducts26834']:
 assert shader(shaders,name)==shader(bs,name),name
frag=shader(shaders,'clipZoneApplyFragment26839')
for required in ['float own=smoothstep(0.55,0.85,m);','if(own<=0.0) discard;','float donorCos=dirCos(cs,cb);','float sourceSmallCos=dirCos(c,cs);','float sourceBroadCos=dirCos(c,cb);','bool donorCoherent=support>=0.999 && donorCos>=uDirectionCosThreshold && magRatio>=uCoherenceThreshold;','bool sourceHueAgrees=sourceHasHue && sourceSmallCos>=uDirectionCosThreshold && sourceBroadCos>=uDirectionCosThreshold;','bool preserveHue=donorCoherent && sourceHueAgrees;','float safeMag=min(srcMag,agreedMag);','vec2 preserved=(srcMag>1.0e-6) ? c*(safeMag/srcMag) : vec2(0.0);','vec2 warmFallback=vec2(0.25,-0.65)*uNeutralRms;','vec2 target=preserveHue ? preserved : warmFallback;','vec2 cp=mix(c,target,own);','float g=y-0.25*(dR+dB); vec3 wbDst=vec3(g+dR,g,g+dB);','vec3 cameraDst=wbDst/max(uCalculationWb,vec3(1.0e-6));']:
 assert required in frag,required
for forbidden in ['vec2 target=(donorValid && (donorNeutral || sourceAgrees)) ? donor : vec2(0.0);','vec2 fill=mix(safeFill(bg),safeFill(sm),a);','vec2 cp=mix(c,fill,m);','imageStore','buffer Stats','atomicAdd','gl_GlobalInvocationID']:
 assert forbidden not in frag,forbidden
# Donors may validate hue and cap magnitude, but may never rotate accepted source hue.
assert 'c*(safeMag/srcMag)' in frag and 'target=cs' not in frag and 'target=cb' not in frag and 'target=donor' not in frag
# Exact frozen domains.
for rel in ['app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl','app/src/main/cpp/motionv2_jpeg444_jni.cpp','app/src/main/java/com/particlesdevs/photoncamera/processing/IrisTrue2xSrNative.java','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2DngColorShadow.java']:
 assert H(B/rel)==H(C/rel),rel
for t in ['longColorAuthority=false','longHueAuthority=false','rgbScaleOnly=true','exactRgbRatioPreserved=true']: assert t in stack,t
print('PASS 26839 semantic validation: exact 3-path scope; successful-26838 FBO lifecycle/placement preserved; mask tails exact no-op; source hue direction preserved only with source+small+broad consensus; donors cap magnitude only and cannot rotate hue; neutral-white fallback removed; mild warm terminal fallback only when hue unrecoverable; WB-linear luma invariant; SR/LONG/DNG/high-zoom protected')
