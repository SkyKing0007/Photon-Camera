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
v=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726838' in v and 'VERSION_BUILD=26838' in v and 'VERSION_MINOR=9726440' in v
bridge=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text(); bb=(B/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text(); shaders=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text(); bs=(B/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text(); stack=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
# Preserve successful 26837 owner placement and GLES3 FBO lifecycle.
pos_d=bridge.index('MgcFullResolutionDenoise.denoise('); pos_26728=bridge.index('applyIris26728ProtectedChromaFloor('); pos_owner=bridge.index('IRIS_26837_DEVICE_SAFE_TRUE_FINAL_CLIP_ZONE_CHROMA_OWNER'); pos_carrier=bridge.index('IRIS_26726_UNIVERSAL_RGBA16F_CROSS_CONTEXT_OWNER'); assert pos_d<pos_26728<pos_owner<pos_carrier
assert bridge.count('applyIris26837FinalClipZoneChroma(')==2
s=bridge.index('private fun applyIris26837FinalClipZoneChroma('); e=bridge.index('private fun buildTrue2xRenderCarrier(',s); active=bridge[s:e]
for forbidden in ['GLES31.glBindImageTexture(','GLES31.glDispatchCompute(','GLES31.glBindBufferBase(','GL_SHADER_STORAGE_BUFFER']:
 assert forbidden not in active,forbidden
for required in ['GlesMgcRawSabreShaders.clipZoneApplyFragment26838','26838 final fragment bindings','26838 final fragment apply','IRIS_26838_CLIP_ZONE_CHROMA','backend=FBO_FRAGMENT_GLES300','inherited26837Backend=true','maskTailExactNoop=true','broadHueAuthority=false','donorRequiresSmallBroadSourceConsensus=true','neutralFallback=true','colorDomain=WB_LINEAR','inverseWbRoundTrip=true','insertion=POST_RESIDUAL_POST_26728_PRE_TONE']:
 assert required in active,required
# Allocation / copy / draw/readback mechanics are inherited; only shader linkage, three safety uniforms, labels, telemetry may differ.
def normalize_active(x):
 x=x.replace('clipZoneApplyFragment26838','clipZoneApplyFragment26837').replace('26838 final fragment bindings','26837 final fragment bindings').replace('26838 final fragment apply','26837 final fragment apply')
 x=re.sub(r'GLES30\.glUniform1f\(GLES30\.glGetUniformLocation\(programs\.applyFragment,"uNeutralRms"\),t\.clipZoneNeutralRms\);','',x)
 x=re.sub(r'GLES30\.glUniform1f\(GLES30\.glGetUniformLocation\(programs\.applyFragment,"uCoherenceThreshold"\),t\.clipZoneCoherence\);','',x)
 x=re.sub(r'GLES30\.glUniform1f\(GLES30\.glGetUniformLocation\(programs\.applyFragment,"uDirectionCosThreshold"\),t\.clipZoneDirectionCos\);','',x)
 x=re.sub(r'PLog\.i\(TAG,"IRIS_26838_CLIP_ZONE_CHROMA[^\n]+\)','__LOG__',x)
 x=re.sub(r'PLog\.i\(TAG,"IRIS_26837_CLIP_ZONE_CHROMA[^\n]+\)','__LOG__',x)
 return x
bs0=bb[bb.index('private fun applyIris26837FinalClipZoneChroma('):bb.index('private fun buildTrue2xRenderCarrier(',bb.index('private fun applyIris26837FinalClipZoneChroma('))]
assert normalize_active(active)==normalize_active(bs0),'26837 FBO lifecycle/mechanics changed beyond approved bindings/link/log'
# 26837 active shader remains byte-identical as historical/device-safe reference; products/mask math unchanged.
assert shader(shaders,'clipZoneApplyFragment26837')==shader(bs,'clipZoneApplyFragment26837')
assert shader(shaders,'clipZoneApply26834')==shader(bs,'clipZoneApply26834')
assert shader(shaders,'clipZoneProducts26834')==shader(bs,'clipZoneProducts26834')
frag=shader(shaders,'clipZoneApplyFragment26838')
for required in ['float own=smoothstep(0.55,0.85,m);','if(own<=0.0) discard;','float donorCos=dirCos(cs,cb);','float sourceCos=dirCos(c,donor);','float magRatio=min(length(cs),length(cb))/max(max(length(cs),length(cb)),1.0e-6);','bool donorValid=support>=0.999 && donorCos>=uDirectionCosThreshold && magRatio>=uCoherenceThreshold;','bool sourceAgrees=!sourceNeutral && sourceCos>=uDirectionCosThreshold;','vec2 target=(donorValid && (donorNeutral || sourceAgrees)) ? donor : vec2(0.0);','vec2 cp=mix(c,target,own);','float g=y-0.25*(dR+dB); vec3 wbDst=vec3(g+dR,g,g+dB);','vec3 cameraDst=wbDst/max(uCalculationWb,vec3(1.0e-6));']:
 assert required in frag,required
for forbidden in ['vec2 fill=mix(safeFill(bg),safeFill(sm),a);','vec2 cp=mix(c,fill,m);','imageStore','buffer Stats','atomicAdd','gl_GlobalInvocationID']:
 assert forbidden not in frag,forbidden
# Broad field can only participate in donor consensus; it cannot independently supply target hue.
assert frag.count('safeFill(bg)')==1 and 'vec2 cs=safeFill(sm), cb=safeFill(bg);' in frag
assert 'target=cb' not in frag and 'mix(cb' not in frag and 'mix(safeFill(bg)' not in frag
# Exact frozen domains.
for rel in ['app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl','app/src/main/cpp/motionv2_jpeg444_jni.cpp','app/src/main/java/com/particlesdevs/photoncamera/processing/IrisTrue2xSrNative.java','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2DngColorShadow.java']:
 assert H(B/rel)==H(C/rel),rel
for t in ['longColorAuthority=false','longHueAuthority=false','rgbScaleOnly=true','exactRgbRatioPreserved=true']: assert t in stack,t
print('PASS 26838 semantic validation: exact 3-path scope; successful-26837 FBO lifecycle/placement preserved; low-mask halos exact no-op; broad donor demoted to consensus veto; colored donor requires small+broad+source agreement; incoherent clipped core neutral fallback; WB-linear luma invariant; SR/LONG/DNG/high-zoom protected')
