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
v=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726840' in v and 'VERSION_BUILD=26840' in v and 'VERSION_MINOR=9726440' in v
bridge=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text(); bb=(B/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text(); shaders=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text(); bs=(B/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text(); stack=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
pos_d=bridge.index('MgcFullResolutionDenoise.denoise('); pos_26728=bridge.index('applyIris26728ProtectedChromaFloor('); pos_owner=bridge.index('IRIS_26837_DEVICE_SAFE_TRUE_FINAL_CLIP_ZONE_CHROMA_OWNER'); pos_carrier=bridge.index('IRIS_26726_UNIVERSAL_RGBA16F_CROSS_CONTEXT_OWNER'); assert pos_d<pos_26728<pos_owner<pos_carrier
assert bridge.count('applyIris26837FinalClipZoneChroma(')==2
s=bridge.index('private fun applyIris26837FinalClipZoneChroma('); e=bridge.index('private fun buildTrue2xRenderCarrier(',s); active=bridge[s:e]
for forbidden in ['GLES31.glBindImageTexture(','GLES31.glDispatchCompute(','GLES31.glBindBufferBase(','GL_SHADER_STORAGE_BUFFER']: assert forbidden not in active,forbidden
for required in ['GlesMgcRawSabreShaders.clipZoneApplyFragment26840','26840 final fragment bindings','26840 final fragment apply','IRIS_26840_CLIP_ZONE_CHROMA','backend=FBO_FRAGMENT_GLES300','inherited26839HueContract=true','maskRegularization=INWARD_3X3_TENT','maskCanExpand=false','maskTailExactNoop=true','boundaryHueDirectionContinuous=true','crossHueBoundaryBlend=false','broadHueAuthority=false','sourceHueDirectionOwner=true','donorMagnitudeOnly=true','neutralWhiteFallback=false','warmTerminalDeepCoreOnly=true','colorDomain=WB_LINEAR','inverseWbRoundTrip=true','insertion=POST_RESIDUAL_POST_26728_PRE_TONE']: assert required in active,required
def normalize_active(x):
 x=x.replace('clipZoneApplyFragment26840','clipZoneApplyFragment26839').replace('26840 final fragment bindings','26839 final fragment bindings').replace('26840 final fragment apply','26839 final fragment apply')
 x=re.sub(r'PLog\.i\(TAG,"IRIS_26840_CLIP_ZONE_CHROMA[^\n]+\)','__LOG__',x); x=re.sub(r'PLog\.i\(TAG,"IRIS_26839_CLIP_ZONE_CHROMA[^\n]+\)','__LOG__',x); return x
bs0=bb[bb.index('private fun applyIris26837FinalClipZoneChroma('):bb.index('private fun buildTrue2xRenderCarrier(',bb.index('private fun applyIris26837FinalClipZoneChroma('))]
assert normalize_active(active)==normalize_active(bs0),'successful 26839 FBO lifecycle/mechanics changed beyond approved shader link/check labels/log'
for name in ['clipZoneApplyFragment26839','clipZoneApplyFragment26838','clipZoneApplyFragment26837','clipZoneApply26834','clipZoneProducts26834']: assert shader(shaders,name)==shader(bs,name),name
frag=shader(shaders,'clipZoneApplyFragment26840')
for required in ['float m=inwardRegularizedMask(p,centerMask);','return min(center,tent);','float own=smoothstep(0.55,0.95,m);','if(own<=0.0) discard;','bool donorCoherent=support>=0.999 && donorCos>=uDirectionCosThreshold && magRatio>=uCoherenceThreshold;','bool sourceHueAgrees=sourceHasHue && sourceSmallCos>=uDirectionCosThreshold && sourceBroadCos>=uDirectionCosThreshold;','bool preserveHue=donorCoherent && sourceHueAgrees;','float targetMag=preserveHue ? trustedMag : min(srcMag,untrustedFloor);','float rolloffMag=mix(srcMag,targetMag,own);','vec2 alongSource=(srcMag>1.0e-6) ? c*(rolloffMag/srcMag) : vec2(0.0);','float terminal=smoothstep(0.90,0.995,m);','vec2 warmFallback=vec2(0.25,-0.65)*uNeutralRms;','vec2 cp=mix(alongSource,warmFallback,terminal);','float g=y-0.25*(dR+dB); vec3 wbDst=vec3(g+dR,g,g+dB);','vec3 cameraDst=wbDst/max(uCalculationWb,vec3(1.0e-6));']: assert required in frag,required
for forbidden in ['vec2 cp=mix(c,target,own);','vec2 target=preserveHue ? preserved : warmFallback;','vec2 fill=mix(safeFill(bg),safeFill(sm),a);','imageStore','buffer Stats','atomicAdd','gl_GlobalInvocationID']: assert forbidden not in frag,forbidden
assert 'return min(center,tent);' in frag and 'max(center,tent)' not in frag
assert 'target=cs' not in frag and 'target=cb' not in frag and 'target=donor' not in frag
for rel in ['app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl','app/src/main/cpp/motionv2_jpeg444_jni.cpp','app/src/main/java/com/particlesdevs/photoncamera/processing/IrisTrue2xSrNative.java','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2DngColorShadow.java']: assert H(B/rel)==H(C/rel),rel
for t in ['longColorAuthority=false','longHueAuthority=false','rgbScaleOnly=true','exactRgbRatioPreserved=true']: assert t in stack,t
print('PASS 26840 semantic validation: exact 3-path scope; successful-26839 hue contract and FBO lifecycle/placement preserved; final mask boundary regularized inward-only by 3x3 tent so it cannot expand into valid pixels; boundary chroma remains on source hue ray and only magnitude rolls smoothly; cross-hue warm fallback delayed to deep unrecoverable core; WB-linear luma invariant; SR/LONG/DNG/high-zoom protected')
