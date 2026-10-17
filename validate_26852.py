#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys,textwrap
B,C=map(Path,sys.argv[1:3])
ALLOW={'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/version.properties'}
def H(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def U(root): return {str(p.relative_to(root)):H(p) for p in (root/'app').rglob('*') if p.is_file()}
def template_map(text):
    out={}
    pat=re.compile(r'^\s*(?:private\s+)?val\s+([A-Za-z_]\w*)(?:\s*:\s*String)?(?:\s+by\s+lazy\s*\{)?\s*=??\s*"""',re.M)
    # First handle ordinary '= """' and lazy patterns via line scan.
    names=set(re.findall(r'^\s*(?:private\s+)?val\s+([A-Za-z_]\w*)[^\n]*?"""',text,re.M))
    for name in names:
        pats=[r'^\s*(?:private\s+)?val\s+'+re.escape(name)+r'(?:\s*:\s*String)?\s*=\s*"""',r'^\s*(?:private\s+)?val\s+'+re.escape(name)+r'\s*:\s*String\s+by\s+lazy\s*\{\s*\n\s*"""']
        m=next((re.search(p,text,re.M) for p in pats if re.search(p,text,re.M)),None)
        if not m: continue
        a=text.find('"""',m.start())+3; z=text.find('""".trimIndent()',a)
        if z>=0: out[name]=textwrap.dedent(text[a:z]).strip('\n')
    return out
def function(text,sig):
    a=text.index(sig); brace=text.index('{',a); depth=0; in_str=False; esc=False
    for i in range(brace,len(text)):
        ch=text[i]
        if in_str:
            if esc: esc=False
            elif ch=='\\': esc=True
            elif ch=='"': in_str=False
            continue
        if ch=='"': in_str=True; continue
        if ch=='{': depth+=1
        elif ch=='}':
            depth-=1
            if depth==0: return text[a:i+1]
    raise AssertionError(sig)
b,c=U(B),U(C); assert len(b)==1786 and len(c)==1786; assert set(b)==set(c)
changed={p for p in b if b[p]!=c[p]}; assert changed==ALLOW,(changed,ALLOW)
S='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'; T='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
bs=(B/S).read_text(); cs=(C/S).read_text(); bt=template_map(bs); ct=template_map(cs)
assert 'merge' in bt and 'merge' in ct
assert set(ct)-set(bt)=={'normalCfaTemporalAccumulate26852','normalCfaExtract26852'},set(ct)-set(bt)
for name in sorted(set(bt)&set(ct)):
    if name!='merge': assert bt[name]==ct[name],f'inherited shader template changed: {name}'
cm=ct['merge']; bm=bt['merge']; assert bm!=cm
# Preserve the complete 26846-26851 reconstruction authorities in the one-time adapter.
for marker in ['IRIS_26846_CFA_PHASE_BALANCED_CHROMA_AUTHORITY','IRIS_26847_SAME_MATERIAL_GREEN_TOPOLOGY_OWNER','IRIS_26848_SAME_MATERIAL_RB_TOPOLOGY_OWNER','IRIS_26847_SAME_MATERIAL_RB_DIFFERENCE_INPUT','IRIS_26849_PERIPHERAL_PHASE_SAFE_CFA_LCA_OWNER','IRIS_26849_GLSLANG_DECLARATION_ORDER_REGRESSION','IRIS_26850_ADAPTIVE_SAME_PHASE_CFA_REGISTRATION_OWNER','IRIS_26851_ALL_FIELD_MATERIAL_EDGE_REGISTRATION_OWNER','IRIS_26851_CENTRAL_GREEN_MATERIAL_PROOF']:
    assert cm.count(marker)==1,marker
for marker in ['IRIS_26852_TEMPORAL_CFA_RECONSTRUCTION_INPUT','IRIS_26852_TEMPORAL_CFA_SUPPORT_HANDOFF']:
    assert cm.count(marker)==1,marker
for marker in ['IRIS_26852_SINGLE_OWNER_TEMPORAL_CFA_ACCUMULATOR','IRIS_26852_TEMPORAL_CFA_TO_26851_EXTRACTED_ADAPTER']:
    assert cs.count(marker)==1,marker
# 26849 and 26852 declaration-order regressions must remain pre-use.
for decl,call in [('float peripheralLcaStrength26849(vec2 referenceUv);','peripheralLcaStrength26849(referenceUv26791)'),('float centralMaterialRegistrationGate26851(ivec2 position);','centralMaterialRegistrationGate26851(position)'),('float temporalNormalized26852(ivec2 p);','temporalNormalized26852(p)')]:
    assert decl in cm and call in cm and cm.index(decl)<cm.index(call),(decl,call)
# Successful 26850/51 adaptive acceptance math remains exact in merge.
for needle in ['candidateIndex < 3','? 2.0 : (candidateIndex == 1 ? 4.0 : 6.0)','candidateScore >= 0.82','candidateScore > bestScore + 0.08','Exact 26848 fallback']:
    assert needle in cm,needle
# New temporal carrier: physical four-phase signal + ONE scalar shared temporal admission.
a=ct['normalCfaTemporalAccumulate26852']; x=ct['normalCfaExtract26852']
for needle in ['layout(location = 0) out vec4 oPhaseSignal;','layout(location = 1) out vec4 oSharedSupport;','layout(location = 2) out vec4 oPhaseValidity;','float baseWeight = quadRejection(quadOrigin) * rowReliability(sourceUv.y);','float validWeight = baseWeight *','sharedHeadroom = min(sharedHeadroom, h);','oPhaseSignal = phaseSignal * validWeight;','oSharedSupport = vec4(validWeight, baseWeight, baseWeight * clipConfidence, 0.0);','oPhaseValidity = phaseHeadroom * validWeight;']:
    assert needle in a,needle
for forbidden in ['phaseWeight[','redWeight','blueWeight','greenWeight','vec4 phaseWeight','neutral','hue','mix(phaseSignal','uDngQuadHeadroom','uJpegNeutralClamp']:
    assert forbidden not in a,('temporal accumulator forbidden',forbidden)
for needle in ['vec4 normalized = signal / w;','oExtractedBayer = max(rawCode, vec4(0.0)) + vec4(1.0e-4);']:
    assert needle in x,needle
for forbidden in ['neutral','hue','demosaic','whiteBalance','uJpeg','normalizeBayer']:
    assert forbidden not in x,('extract adapter forbidden',forbidden)
# Temporal source must be consumed only by the one-time merge input; no per-frame RGB temporal owner.
ctext=(C/T).read_text(); btext=(B/T).read_text()
for marker in ['IRIS_26852_SINGLE_OWNER_TEMPORAL_CFA_CARRIER','IRIS_26852_ONE_TIME_CFA_TO_RGB_RECONSTRUCTION_OWNER']:
    assert ctext.count(marker)==1,marker
assert ctext.count('renderSabreNormalCfaTemporalAccumulate26852(')>=3 # definition + reference + alternate
assert 'phaseValidityProvenance=true perFrameRgb=false oneTime26851Reconstruction=true' in ctext
assert 'crossPhaseTemporalSelection=false' in ctext
assert 'normalCfaOwner=26852_SHARED_WEIGHT_TEMPORAL_R_G1_G2_B' in ctext
assert 'temporalCfaSignals26852 = normalCfaSignals26852' in ctext and 'temporalCfaSupport26852 = normalCfaSupport26852' in ctext and 'temporalCfaValidity26852 = normalCfaValidity26852' in ctext
assert 'IRIS_26852_DELAYED_RGB_ADAPTER_ALLOCATION' in ctext
assert ctext.index('IRIS_26852_SINGLE_OWNER_TEMPORAL_CFA_CARRIER') < ctext.index('IRIS_26852_DELAYED_RGB_ADAPTER_ALLOCATION') < ctext.index('IRIS_26852_ONE_TIME_CFA_TO_RGB_RECONSTRUCTION_OWNER')
# The old full-resolution RGB MRTs must not be allocated before temporal completion.
carrier=ctext.index('IRIS_26852_SINGLE_OWNER_TEMPORAL_CFA_CARRIER')
adapter=ctext.index('IRIS_26852_DELAYED_RGB_ADAPTER_ALLOCATION')
assert 'val accumulatedColor = createTexture(' not in ctext[carrier:adapter]
assert 'val accumulatedWeightsGb = createTexture(' not in ctext[carrier:adapter]
assert 'val accumulatedValidity26614 = createTexture(' not in ctext[carrier:adapter]
# The reference + NORMAL branch no longer call renderSabreMerge; LONG still does.
core_start=ctext.index('/* IRIS_26852_SINGLE_OWNER_TEMPORAL_CFA_CARRIER')
one_time=ctext.index('/* IRIS_26852_ONE_TIME_CFA_TO_RGB_RECONSTRUCTION_OWNER')
pre=ctext[core_start:one_time]
assert pre.count('renderSabreMerge(')==1,pre.count('renderSabreMerge(') # LONG-only temporary RGB path
assert 'frame.role == RawBurstFrameRole.SHADOW_LONG' in pre
# DNG, SHORT, LONG and dehomogenize function implementations stay exact inside modified stacker.
for sig in ['private fun clearSabreNormalDngAccumulator(','private fun renderSabreNormalDngMerge(','private fun resolveSabreNormalDngSupportStats(','private fun createSabreNormalDngNoiseProfile(','private fun renderSabreNormalMasterShortFusion26651(','private fun renderSabreShortColorValidityAugment26651(','private fun renderSabreShadowLongLumaAccumulate26833(','private fun renderSabreShadowLongLumaGainMap26833(','private fun renderSabreShadowLongPostVgnLumaApply26833(','private fun renderSabreDehomogenize(']:
    assert function(btext,sig)==function(ctext,sig),sig
# Program lifecycle is inherited: linkProgram registers every program in programs[], release() deletes that set.
for needle in ['programs += program','for (program in programs) GLES30.glDeleteProgram(program)','programs.clear()']:
    assert needle in ctext,needle
assert 'sabreNormalCfaTemporalAccumulateProgram26852 = linkProgram(' in ctext
assert 'sabreNormalCfaExtractProgram26852 = linkProgram(' in ctext
# DNG shader path and DNG publication normalizeBayer remain untouched.
assert bt['normalDngMerge']==ct['normalDngMerge']
SP='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt'; assert (B/SP).read_bytes()==(C/SP).read_bytes()
# Other high-risk downstream owners are outside allowlist and therefore byte-identical.
protected=['app/src/main/java/com/hinnka/mycamera/processor/MgcSabreResolver.kt','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java','app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java','app/src/main/cpp/motionv2_jpeg444_jni.cpp']
for rel in protected:
    if (B/rel).exists(): assert (B/rel).read_bytes()==(C/rel).read_bytes(),rel
v=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726852' in v and 'VERSION_BUILD=26852' in v
# No fallback-owner resurrection.
for forbidden in ['postRgbLca26852','grayFallback26852','neutralFallback26852','crossPhaseTemporal26852','phaseIndependentTemporalWeight26852']:
    assert forbidden not in cs+ctext,forbidden
print('PASS 26852 semantic/ownership: exact successful-26851 first-NORMAL reference/alignment/rejection retained; NORMAL temporal owner becomes shared-admission physical R/G1/G2/B CFA; 26846-26851 reconstruction runs once after temporal completion; DNG/SHORT/LONG/Resolve/VGN/UHDR/high-zoom owners protected')
