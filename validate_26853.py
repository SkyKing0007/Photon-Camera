#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys,textwrap,difflib
B,C=map(Path,sys.argv[1:3])
ALLOW={
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/version.properties'}
def H(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def U(root): return {str(p.relative_to(root)):H(p) for p in (root/'app').rglob('*') if p.is_file()}
def template_map(text):
    out={}
    names=set(re.findall(r'^\s*(?:private\s+)?val\s+([A-Za-z_]\w*)[^\n]*?"""',text,re.M))
    # include lazy multiline declarations
    names |= set(re.findall(r'^\s*(?:private\s+)?val\s+([A-Za-z_]\w*)\s*:\s*String\s+by\s+lazy',text,re.M))
    for name in names:
        pats=[r'^\s*(?:private\s+)?val\s+'+re.escape(name)+r'(?:\s*:\s*String)?\s*=\s*"""',r'^\s*(?:private\s+)?val\s+'+re.escape(name)+r'\s*:\s*String\s+by\s+lazy\s*\{\s*\n\s*"""']
        m=next((re.search(p,text,re.M) for p in pats if re.search(p,text,re.M)),None)
        if not m: continue
        a=text.find('"""',m.start())+3; z=text.find('""".trimIndent()',a)
        if z>=0: out[name]=textwrap.dedent(text[a:z]).strip('\n')
    return out
def function(text,sig):
    a=text.index(sig); brace=text.index('{',a); depth=0; quote=None; esc=False
    for i in range(brace,len(text)):
        ch=text[i]
        if quote:
            if esc: esc=False
            elif ch=='\\': esc=True
            elif ch==quote: quote=None
            continue
        if ch in ('"',"'"): quote=ch; continue
        if ch=='{': depth+=1
        elif ch=='}':
            depth-=1
            if depth==0: return text[a:i+1]
    raise AssertionError(sig)
b,c=U(B),U(C); assert len(b)==1786 and len(c)==1786,(len(b),len(c)); assert set(b)==set(c)
changed={p for p in b if b[p]!=c[p]}; assert changed==ALLOW,(changed,ALLOW)
S='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
T='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
R='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'
bs=(B/S).read_text(); cs=(C/S).read_text(); bt=template_map(bs); ct=template_map(cs)
changed_templates={n for n in set(bt)&set(ct) if bt[n]!=ct[n]}
assert changed_templates=={'normalCfaTemporalAccumulate26852','true2xGuideRender26568'},changed_templates
assert set(ct)-set(bt)=={'normalCfaNoiseClean26853'},set(ct)-set(bt)
assert not(set(bt)-set(ct)),set(bt)-set(ct)
# 26852 reconstruction topology itself is unchanged: this build changes temporal denoise, not CFA->RGB ownership.
for name in ('merge','normalCfaExtract26852','normalDngMerge','highZoomDetailResolve26718','universalNormalMasterShortFusion26651','shadowLongLumaAccumulate26833','shadowLongLumaGainMap26833','shadowLongPostVgnLumaApply26833'):
    assert bt[name]==ct[name],f'protected shader template changed: {name}'
acc=ct['normalCfaTemporalAccumulate26852']; clean=ct['normalCfaNoiseClean26853']; sr=ct['true2xGuideRender26568']
assert cs.count('IRIS_26852_SINGLE_OWNER_TEMPORAL_CFA_ACCUMULATOR')==1
for needle in ['layout(location = 0) out vec4 oPhaseSignal;','layout(location = 1) out vec4 oSharedSupport;','layout(location = 2) out vec4 oPhaseValidity;','IRIS_26853_LOCAL_TEMPORAL_NOISE_MOMENTS','layout(location = 3) out vec2 oTemporalStats26853;','oTemporalStats26853 = vec2(validWeight * validWeight,']:
    assert needle in acc,needle
# Shared temporal admission remains single-owner; no per-channel temporal picking is introduced.
for forbidden in ['redWeight','blueWeight','greenWeight','phaseWeight[','phaseIndependentTemporal','crossPhase','hueDonation','grayFallback']:
    assert forbidden not in acc,(forbidden,'acc')
assert cs.count('IRIS_26853_MULTIFRAME_NATIVE_CFA_DENOISE_OWNER')==1
for needle in ['uniform sampler2D uPhaseSignal;','uniform sampler2D uSharedSupport;','uniform sampler2D uPhaseValidity;','uniform sampler2D uTemporalStats26853;','float effectiveLocalN = clamp((sumW * sumW) / sumW2, 1.0, 32.0);','float temporalVarianceY = max(stats.y / sumW - centerY * centerY, 0.0);','float flatGate = 1.0 - irisSmooth0126853','vec4 phaseCompat = vec4(1.0) - smoothstep','oCleanPhaseSignal = cleaned * sumW;']:
    assert needle in clean,needle
for forbidden in ['globalEffectiveSupport','uEffectiveSupport','hueDonation','mix(center, vec4','vec3(']:
    assert forbidden not in clean,(forbidden,'clean')
# Same-phase-only spatial clean: phase lanes remain independent; guide is only a structural gate.
assert 'vec4 neighbor = mean26853' in clean and 'vec4 w = phaseCompat * neighborValid' in clean
# Super Res must carry the new native guide behavior and gate ONLY its detail confidence, not frame admission/chroma.
for needle in ['IRIS_26853_SUPER_RES_LOCAL_NOISE_GATE','float irisResidualNoiseGate26853','float localNoiseGate26853','detailConfidence *= mix(1.0, localNoiseGate26853, 0.85 * flatShadow26853);']:
    assert needle in sr,needle
assert 'uTemporalLumaStats' in sr
for forbidden in ['uEffectiveSupport','globalEffectiveSupport','directChromaOwner=true','frameAdmission26853']:
    assert forbidden not in sr,(forbidden,'sr')
# Stacker ownership/lifetime.
ctext=(C/T).read_text(); btext=(B/T).read_text()
for marker in ['IRIS_26852_SINGLE_OWNER_TEMPORAL_CFA_CARRIER','IRIS_26852_ONE_TIME_CFA_TO_RGB_RECONSTRUCTION_OWNER','IRIS_26853_MULTIFRAME_NATIVE_CFA_DENOISE_HANDOFF','IRIS_26853_MULTIFRAME_NATIVE_CFA_DENOISE_OWNER']:
    assert ctext.count(marker)==1,marker
for needle in ['val normalCfaTemporalStats26853 = createTexture(','GLES30.GL_RG16F','normalCfaTemporalStats26853, extractedWidth, extractedHeight','temporalStats26853 = normalCfaTemporalStats26853','renderSabreNormalCfaNoiseClean26853(','outputWeightedSignals = referenceExtracted','releaseOwnedTexture(normalCfaSignals26852, "26853 pre-clean temporal CFA signals")','releaseOwnedTexture(normalCfaTemporalStats26853, "26853 consumed local temporal moments")','phaseSignals = referenceExtracted','temporalCfaSignals26852 = referenceExtracted','allNormalAlignmentAttempted=true','globalEffectiveSupport=false']:
    assert needle in ctext,needle
# Denoise completes before delayed full-resolution RGB allocation and one-time reconstruction.
cleanpos=ctext.index('IRIS_26853_MULTIFRAME_NATIVE_CFA_DENOISE_HANDOFF')
adapter=ctext.index('IRIS_26852_DELAYED_RGB_ADAPTER_ALLOCATION')
one=ctext.index('IRIS_26852_ONE_TIME_CFA_TO_RGB_RECONSTRUCTION_OWNER')
assert cleanpos < adapter < one
# Exact high-risk existing functions stay unchanged except the three 26853 helper/lifecycle functions.
for sig in ['private fun clearSabreNormalDngAccumulator(','private fun renderSabreNormalDngMerge(','private fun resolveSabreNormalDngSupportStats(','private fun createSabreNormalDngNoiseProfile(','private fun renderSabreNormalMasterShortFusion26651(','private fun renderSabreShortColorValidityAugment26651(','private fun renderSabreShadowLongLumaAccumulate26833(','private fun renderSabreShadowLongLumaGainMap26833(','private fun renderSabreShadowLongPostVgnLumaApply26833(','private fun renderSabreDehomogenize(']:
    assert function(btext,sig)==function(ctext,sig),sig
# Every NORMAL remains alignment-attempted by inherited loop; this build adds no frame-count reduction owner.
for forbidden in ['take(8)','take(15)','take(20)','dropLast','frameLimit26853','maxFrames26853']:
    assert forbidden not in ctext,forbidden
assert 'sabreNormalCfaNoiseCleanProgram26853 = linkProgram(' in ctext
# Motion bridge: old MGC RGB/YUV residual denoise is bypassed only for Motion; Night condition is semantically inherited.
br=(B/R).read_text(); cr=(C/R).read_text()
for needle in ['IRIS_26853_MOTION_MERGE_NATIVE_DENOISE_OWNER','val motionMergeNativeDenoise26853 = !parameters.irisNightActive','val runFullResolutionDenoise = !motionMergeNativeDenoise26853 &&','motionNoiseOwner=${if (motionMergeNativeDenoise26853) "IRIS_26853_CFA_MERGE" else "LEGACY_MGC_RESIDUAL"}','BYPASSED_IRIS_26853_MERGE_NATIVE']:
    assert needle in cr,needle
# The inherited MGC denoiser call still exists for Night and is still gated by runFullResolutionDenoise.
assert 'if (runFullResolutionDenoise) {' in cr and 'MgcFullResolutionDenoise.denoise(' in cr
# No capture/exposure or PostPipeline owners changed.
protected=['app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','app/src/main/java/com/hinnka/mycamera/processor/MgcSabreResolver.kt','app/src/main/cpp/motionv2_jpeg444_jni.cpp']
for rel in protected:
    if (B/rel).exists(): assert (B/rel).read_bytes()==(C/rel).read_bytes(),rel
SP='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt'; assert (B/SP).read_bytes()==(C/SP).read_bytes()
# All shader assets remain byte-identical.
for p in (B/'app/src/main/assets/shaders').rglob('*'):
    if p.is_file():
        rel=p.relative_to(B); assert p.read_bytes()==(C/rel).read_bytes(),str(rel)
v=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726853' in v and 'VERSION_BUILD=26853' in v
print('PASS 26853 semantic/ownership: successful 26852 CFA-first reference/alignment/rejection and 26846-26852 reconstruction remain; Motion denoise moves into completed shared-admission physical CFA using local multiframe moments; Night/MGC legacy path, DNG/SHORT/LONG/VGN/UHDR and high-zoom owners preserved; Super Res native guide inherits cleaned CFA and direct detail is locally noise-gated')
