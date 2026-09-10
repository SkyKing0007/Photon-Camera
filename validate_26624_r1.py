#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26624_r1.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2])
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'app').rglob('*')) if p.is_file()}
bh,ch=H(B),H(C); assert len(bh)==1713 and len(ch)==1713,(len(bh),len(ch))
changed=sorted(p for p in set(bh)|set(ch) if bh.get(p)!=ch.get(p))
expected=sorted([
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/version.properties'])
assert changed==expected,(changed,expected)
ver=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726624' in ver and 'VERSION_BUILD=26624' in ver

# Candidate-first exact transformation: only the reviewed 26624 substitutions are allowed.
def expected_sabre_from_base(src:str)->str:
    old='''            float componentBrightness = 0.0;\n            float componentSourceConfidence = 0.0;\n            float literalLossSeen = 0.0;\n            float effectiveLossSeen = 0.0;\n            float anchorConfidenceSum = 0.0;'''
    new='''            float componentBrightness = 0.0;\n            float componentSourceConfidence = 0.0;\n            float literalLossSeen = 0.0;\n            float effectiveLossSeen = 0.0;\n            float effectiveLossComponentConfidence = 0.0;\n            float anchorConfidenceSum = 0.0;'''
    assert src.count(old)==1; src=src.replace(old,new)
    old='''                    if (hasShort) effectiveLossSeen = max(\n                        effectiveLossSeen,\n                        effectiveLossWeight(referenceNormalized, scaledShort));'''
    new='''                    if (hasShort) {\n                        float probeEffectiveLoss = effectiveLossWeight(\n                            referenceNormalized, scaledShort);\n                        effectiveLossSeen = max(effectiveLossSeen, probeEffectiveLoss);\n                        /* IRIS_26624_COMPONENT_OWNED_EFFECTIVE_LOSS_MEMBERSHIP\n                         * Near-saturated NORMAL may already have lost radiometry before literal\n                         * two-phase sensor clipping. Bind that loss to SHORT headroom from the SAME\n                         * probe so an unrelated good SHORT sample elsewhere in the flow cell cannot\n                         * manufacture component membership. This is region membership only; geometry\n                         * trust still requires the unchanged sub-pixel measurable boundary seed. */\n                        effectiveLossComponentConfidence = max(\n                            effectiveLossComponentConfidence,\n                            min(probeSourceConfidence, probeEffectiveLoss));\n                    }'''
    assert src.count(old)==1; src=src.replace(old,new)
    old='''            /* IRIS_26611_CLIPPED_INTERIOR_CANNOT_SELF_SEED\n             * z is region membership only: a two-phase physically censored NORMAL component with\n             * valid SHORT source headroom. It intentionally contains no geometry confidence.\n             * Geometry enters exclusively through w (same-CFA measurable-boundary anchor) and is\n             * then propagated through z by the bottleneck pass. Literal clipping itself can never\n             * create trust. Effective/sub-clipping loss remains telemetry and retains ordinary\n             * exposure-normalized NORMAL rejection. */\n            float componentConfidence = min(\n                componentSourceConfidence, literalLossSeen);'''
    new='''            /* IRIS_26624_BOUNDARY_PROVEN_LITERAL_PLUS_EFFECTIVE_COMPONENT\n             * z remains region membership only and still contains no geometry authority. Preserve\n             * 26611 literal two-phase clipping exactly, but also admit exposure-normalized effective\n             * loss when the SAME probe has valid SHORT headroom. This allows a proven boundary to\n             * carry trust through broad clouds/ground/foliage whose NORMAL signal flattened before\n             * literal clipping. Neither literal nor effective loss can self-seed: geometry enters\n             * exclusively through unchanged w and the CFA-safe bottleneck propagation below. */\n            float literalComponentConfidence = min(\n                componentSourceConfidence, literalLossSeen);\n            float componentConfidence = max(\n                literalComponentConfidence, effectiveLossComponentConfidence);'''
    assert src.count(old)==1; src=src.replace(old,new)
    old='''            /* IRIS_26610_ONLY_PHYSICAL_CENSORSHIP_RELAXES_PHOTOMETRY\n             * effectiveLoss remains useful telemetry/evidence, but cannot replace ordinaryWeight.\n             * Only proven two-phase literal RAW censorship invalidates NORMAL-reference photometry. */\n            float physicalCensoring = clamp(literalLoss, 0.0, 1.0);\n            float finalWeight = mix(ordinaryWeight, censoredCoreWeight, physicalCensoring);\n            oWeight = clamp(finalWeight, 0.0, 1.0);'''
    new='''            /* IRIS_26624_COMPONENT_OWNED_EFFECTIVE_LOSS_RESCUE\n             * Preserve the complete 26611 literal-censoring path byte-for-byte in literalFinalWeight.\n             * For pre-clipping/effective NORMAL loss, componentTrust is the geometry authority: only\n             * boundary-proven trust may expose the already-validated SHORT sample, still capped by\n             * SHORT headroom + ordinary physical rejection and followed by the common 3x3 source-clip\n             * veto. effectiveRescueWeight is additive-only (max), so near-saturation recovery can\n             * never reduce an ordinary valid SHORT weight or alter non-highlight behavior. */\n            float physicalCensoring = clamp(literalLoss, 0.0, 1.0);\n            float literalFinalWeight = mix(\n                ordinaryWeight, censoredCoreWeight, physicalCensoring);\n            float effectiveRescueWeight = censoredCoreWeight * clamp(effectiveLoss, 0.0, 1.0);\n            float finalWeight = max(literalFinalWeight, effectiveRescueWeight);\n            oWeight = clamp(finalWeight, 0.0, 1.0);'''
    assert src.count(old)==1; return src.replace(old,new)

def expected_stacker_from_base(src:str)->str:
    old='''                            "boundaryLocalResidualRequired=true predictorCannotOverrideLocalBoundary=true " +\n                            "literalCoreSelfSeed=false effectiveLossPhotometricBypass=false " +\n                            "shortHeadroomOwner=SAME_AS_COMMON_RBF_FINAL_0P75_PERCENT " +'''
    new='''                            "boundaryLocalResidualRequired=true predictorCannotOverrideLocalBoundary=true " +\n                            "literalCoreSelfSeed=false effectiveCoreSelfSeed=false " +\n                            "componentMembership=LITERAL_PLUS_BOUNDARY_PROVEN_EFFECTIVE_LOSS " +\n                            "effectiveLossPhotometricBypass=BOUNDARY_PROVEN_COMPONENT_ONLY_ADDITIVE " +\n                            "shortInteriorSamples=ACTUAL_ALIGNED_SAME_CFA_SHORT noSpatialFill=true " +\n                            "shortHeadroomOwner=SAME_AS_COMMON_RBF_FINAL_0P75_PERCENT " +'''
    assert src.count(old)==1; src=src.replace(old,new)
    old='''    /* IRIS_26623_SHORT_BROAD_LOSS_SUPPORT_TELEMETRY\n     * Read-only proxy for broad highlight-loss interiors, using data already read for 26607. A\n     * candidate is "broad interior" only when its center and all four cardinal neighbors are\n     * normal-loss candidates. Support is measured from the exact post-source-clip target\n     * accumulator eligibility bytes. No weight, mask, merge, CFA, flow or resolve decision changes. */'''
    new='''    /* IRIS_26624_SHORT_COMPONENT_RECOVERY_TELEMETRY\n     * Preserve 26623's device-proven broad-loss proxy while reporting the result after component-owned\n     * effective-loss rescue. A candidate is broad interior only when center + four cardinal neighbors\n     * are NORMAL-loss candidates. Support remains the exact post-source-clip target-accumulator bytes;\n     * this logger never changes weight, mask, CFA, flow, merge, resolve, or GPU lifetime. */'''
    assert src.count(old)==1; src=src.replace(old,new)
    old='''        val details = "broadInteriorCells=$broadInterior broadSupportedCells=$supported " +\n            "broadUnsupportedCells=$unsupported broadSupportFraction=$fraction " +\n            "definition=centerPlus4CardinalNormalLoss support=postSourceClipTargetAccumulator " +\n            "readOnly=true outputUnchanged=true"\n        PLog.i(SABRE_TAG, "IRIS_26623_SHORT_BROAD_LOSS_SUPPORT $details")\n        MotionTrace.processingState("IRIS_26623_SHORT_BROAD_LOSS_SUPPORT", details)'''
    new='''        val details = "broadInteriorCells=$broadInterior broadSupportedCells=$supported " +\n            "broadUnsupportedCells=$unsupported broadSupportFraction=$fraction " +\n            "definition=centerPlus4CardinalNormalLoss support=postSourceClipTargetAccumulator " +\n            "componentMembership=literalPlusEffective boundaryProofRequired=true " +\n            "actualAlignedSameCfaShort=true noSpatialFill=true readOnly=true"\n        PLog.i(SABRE_TAG, "IRIS_26624_SHORT_COMPONENT_RECOVERY $details")\n        MotionTrace.processingState("IRIS_26624_SHORT_COMPONENT_RECOVERY", details)'''
    assert src.count(old)==1; return src.replace(old,new)

bs=(B/expected[0]).read_text(); cs=(C/expected[0]).read_text(); assert expected_sabre_from_base(bs)==cs,'SabreShaders contains non-reviewed delta'
bk=(B/expected[1]).read_text(); ck=(C/expected[1]).read_text(); assert expected_stacker_from_base(bk)==ck,'SpatialStacker contains non-reviewed delta'

# Every unrelated embedded Sabre shader remains exactly successful-26623.
def embedded(text):
    return {m.group(1):m.group(2) for m in re.finditer(r'\bval\s+(\w+)\s*=\s*"""(.*?)"""\.trimIndent\(\)',text,re.S)}
be,ce=embedded(bs),embedded(cs); assert be.keys()==ce.keys()
mods={n for n in be if be[n]!=ce[n]}; assert mods=={'shortComponentAnchor26607','shortRescueWeight26607'},mods
assert be['shortComponentPropagate26607']==ce['shortComponentPropagate26607'],'CFA-safe component propagation changed'

# Active-program ownership remains one common Sabre tunnel; no old/private SHORT owner is revived.
for tok in ['sabreShortComponentAnchorProgram26607 = linkProgram(','sabreShortComponentPropagateProgram26607 = linkProgram(','sabreShortRescueWeightProgram26607 = linkProgram(']: assert tok in ck,tok
for tok in ['sabreShortBoundaryAnchorProgram26606 = 0','sabreShortBoundaryPropagateProgram26606 = 0','sabreShortRescueWeightProgram26606 = 0','sabreShortRestoreRgba16fProgram26587 = 0']: assert tok in ck,tok
for tok in ['privateShortAccumulator=false','lateRgbBlend=false','shortInteriorSamples=ACTUAL_ALIGNED_SAME_CFA_SHORT noSpatialFill=true','sourceClip3x3Continuous=true','bayerQuadWholeRgb=true']: assert tok in ck,tok

# Entire presentation/color/UHDR/true2x/DNG/native and upstream/downstream reconstruction bytes are frozen.
protected=[
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_downsample_26621.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_accumulate_26621.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_reconstruct_26621.glsl',
'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java']
for p in protected: assert (B/p).read_bytes()==(C/p).read_bytes(),f'protected 26623 owner changed: {p}'
print('PASS 26624 semantic/ownership/domain: exact 3-path delta; existing 26607 component path extended only to boundary-proven effective loss; literal path, CFA-safe propagation, common Sabre merge, 26623 presentation/color/UHDR/true2x/DNG protected')
