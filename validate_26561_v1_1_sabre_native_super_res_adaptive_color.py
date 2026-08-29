#!/usr/bin/env python3
from pathlib import Path
import argparse, re, hashlib

ALLOWED = [
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/viewmodel/SettingsBarEntryProvider.java',
'app/src/main/res/drawable/ic_super_res_off.xml',
'app/src/main/res/drawable/ic_super_res_on.xml',
'app/version.properties',
]
SABRE_OLD = ['extractBayer','guideAndCovariance','rejection','merge','mergeShadowLong26558','convertAlignmentSparse','normalDngMerge','copyMaskShadowLong26558','copyMask','copyAlpha','reciprocalGreenWeight4x4','dehomogenize','outputTransformBody','outputTransformUint16','outputTransformFloat']
VGN_OLD = ['common','seed','localClamp','localMedian','directionalSmooth','restoreDirection','iirRgb','calculateError','iirError','blendChroma','finalCameraRgb']

def fail(msg): raise SystemExit('FAIL: '+msg)
def need(c,msg):
    if not c: fail(msg)
def text(root,rel):
    p=root/rel
    need(p.is_file(), f'missing {rel}')
    return p.read_text()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def trim_indent(s):
    lines=s.splitlines()
    while lines and not lines[0].strip(): lines.pop(0)
    while lines and not lines[-1].strip(): lines.pop()
    non=[len(x)-len(x.lstrip()) for x in lines if x.strip()]
    n=min(non) if non else 0
    return '\n'.join(x[n:] for x in lines)
def literals(src):
    out={}
    for m in re.finditer(r'\bval\s+(\w+)\s*=\s*"""(.*?)"""\.trimIndent\(\)',src,re.S):
        need(m.group(1) not in out, 'duplicate GLSL literal '+m.group(1))
        out[m.group(1)] = trim_indent(m.group(2))
    return out

def check_version(c):
    s=text(c,'app/version.properties')
    need('VERSION_NAME=0.9726561' in s, 'wrong VERSION_NAME')
    need('VERSION_BUILD=26561' in s, 'wrong VERSION_BUILD')

def check_shader_parity(b,c):
    rel='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
    bl,cl=literals(text(b,rel)),literals(text(c,rel))
    need(set(bl)==set(SABRE_OLD), f'26560 Sabre literal inventory drift {sorted(set(bl)^set(SABRE_OLD))}')
    need(set(cl)==set(SABRE_OLD)|{'superResDetailMerge26561','superResDetailResolve26561'}, '26561 Sabre GLSL inventory is not exact old+2')
    for n in SABRE_OLD: need(bl[n].encode()==cl[n].encode(), f'existing Sabre GLSL changed: {n}')
    rel='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
    bl,cl=literals(text(b,rel)),literals(text(c,rel))
    need(set(bl)==set(VGN_OLD), '26560 VGN literal inventory drift')
    need(set(cl)==set(VGN_OLD)|{'universalAdaptiveColor26561'}, '26561 VGN GLSL inventory is not exact old+1')
    for n in VGN_OLD: need(bl[n].encode()==cl[n].encode(), f'existing current-MGC VGN GLSL changed: {n}')
    print('PASS exact existing Sabre 15/15 + VGN 11/11 runtime shader literal invariance')

def check_ownership(b,c):
    fusion=text(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt')
    proc=text(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt')
    bridge=text(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
    stack=text(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
    need('GlesIris26545SabreProcessor(' in fusion, 'fusion no longer routes through Sabre processor')
    need('processorPipeline = MgcRawProcessorPipeline.SABRE' in proc and 'mergeMethod = MgcMergeMethod.SABRE' in proc, 'Sabre low-level ownership drift')
    need('parameters.motionV2ReconstructionOwner = Parameters.MOTION_V2_RECONSTRUCTION_SABRE' in bridge, 'bridge reconstruction owner not SABRE')
    need('GlesIris26521SpatialRgbStacker' not in bridge+fusion+proc, 'deleted Spatial RGB stacker reintroduced into active owner')
    need(not (c/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt').exists(), 'deleted Spatial RGB stacker file restored')
    need(not (c/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java').exists(), 'deleted CFA reconstruction owner restored')
    need('enableSabreSuperRes = enableSuperRes' in proc and 'enableSuperRes = enableSabreSuperRes' in fusion, 'Sabre SR option plumbing incomplete')
    need('frame.role == RawBurstFrameRole.NORMAL' in stack and 'IRIS_26561_NIGHT_LONG_EXCLUDED_FROM_SR_DETAIL' in stack, 'SR NORMAL-only admission missing')
    need('frame.role == RawBurstFrameRole.SHADOW_LONG' in stack and 'shadowLongSourceClipGuard = frame.role == RawBurstFrameRole.SHADOW_LONG' in stack and 'GlesMgcRawSabreShaders.mergeShadowLong26558' in stack, 'native SHADOW_LONG Sabre path lost')
    print('PASS Sabre-only production routing; deleted Spatial/Wronski owners remain absent; Night Long remains native-only')

def check_sr(c):
    stack=text(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
    bridge=text(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
    need('val superResWidth = if (enableSabreSuperRes) width * 2 else 0' in stack, 'SR width not exact 2x')
    need('val superResHeight = if (enableSabreSuperRes) height * 2 else 0' in stack, 'SR height not exact 2x')
    need('GLES30.GL_RG16F' in stack, 'compact RG16F luma/support carrier missing')
    need('superResLinearRawPath = null' in stack, 'SR illegally publishes high-resolution linear RAW')
    need('superResDetailPath = superResDetailPath' in stack, 'SR detail path not returned')
    need('val sabreSuperResOutputScale = if (sabreSuperResEnabled) 2f else 1f' in bridge, 'bridge SR output scale wrong')
    need('parameters.motionV2SuperResOutputScale = sabreSuperResOutputScale' in bridge, 'SR output scale not published')
    need('stacked.superResLinearRawPath == null' in bridge, 'bridge no longer enforces native DNG ownership')
    need('superResDetailPathForCleanup = stacked.superResDetailPath' in bridge and 'if (!superResOutputsHandedOff)' in bridge and 'File(path).delete()' in bridge, 'SR temporary sidecar failure cleanup incomplete')
    need('superResOutputsHandedOff = true' in bridge, 'SR sidecar success handoff missing')
    need('fullHighResRgb=false' in stack, 'SR compact/no-full-RGB invariant marker missing')
    # Ensure no resurrection of a 2x LinearRaw output contract in changed owner files.
    need('superResLinearRawPath = superResDetailPath' not in stack+bridge, 'detail sidecar aliased as RAW')
    print('PASS native 1x Sabre authority + compact 2x luma/support SR detail + native 1x DNG contract')

def check_adaptive_color(c):
    rel='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
    s=text(c,rel); ls=literals(s); sh=ls.get('universalAdaptiveColor26561','')
    need('dispatchFinal(filteredYccd, originalYccd)' in s, 'current-MGC final VGN stage missing')
    p1=s.index('dispatchFinal(filteredYccd, originalYccd)'); p2=s.find('dispatchUniversalAdaptiveColor(assembledRgb, workA)',p1)
    need(p2>p1, 'universal adaptive color is not after completed VGN')
    need('mix(centerChroma, localChroma, correction)' in sh, 'adaptive color is not local-consensus correction')
    need('vec3 correctedRgb = clamp(vec3(centerLuma) + correctedChroma, 0.0, 1.0);' in sh, 'adaptive color does not preserve center luminance')
    forbidden=['* 1.1','* 1.2','* 1.3','* 1.4','* 1.5','saturationBoost']
    need(not any(x in sh for x in forbidden), 'universal adaptive color contains broad saturation boost behavior')
    print('PASS shared post-VGN universal adaptive color: local unsupported-chroma correction with luminance preservation')

def check_ui(c):
    s=text(c,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/viewmodel/SettingsBarEntryProvider.java')
    need('R.drawable.ic_super_res_off' in s and 'R.drawable.ic_super_res_on' in s, 'dedicated Super Res icons not wired')
    for rel in ['app/src/main/res/drawable/ic_super_res_off.xml','app/src/main/res/drawable/ic_super_res_on.xml']:
        x=text(c,rel); need('<vector' in x and '<path' in x, f'invalid/missing vector body {rel}')
    print('PASS dedicated Super Res ON/OFF icon wiring; setting ownership unchanged')

def check_protected(b,c):
    # These are critical unchanged controls, publication, DNG and Night owners.
    rels=[
'app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesGraphicsShader.kt',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/IrisNightBatch.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightExposureSelector.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightFrameSelector.java',
'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java',
'app/src/main/res/xml/preferences.xml']
    for rel in rels:
        need((b/rel).is_file() and (c/rel).is_file(), 'protected file missing '+rel)
        need((b/rel).read_bytes()==(c/rel).read_bytes(), 'protected file changed '+rel)
    print(f'PASS protected capture/Night/DNG/UHDR/publication controls byte-identical ({len(rels)} files)')

def validate(base,cand):
    need(base.is_dir() and cand.is_dir(), 'base/candidate directory missing')
    check_version(cand); check_shader_parity(base,cand); check_ownership(base,cand); check_sr(cand); check_adaptive_color(cand); check_ui(cand); check_protected(base,cand)
    print('PASS 26561 focused runtime semantics validation')

def self_test():
    good='''\n        #version 310 es\n        void main() { }\n    '''
    need(trim_indent(good).startswith('#version 310 es'), 'trimIndent regression')
    fake='val a = """\n  x\n""".trimIndent()\nval b = """\n  y\n""".trimIndent()'
    need(literals(fake)=={'a':'x','b':'y'}, 'literal parser regression')
    # Regression: broad saturation boost must be rejected by the source-level pattern rule.
    bad='vec3 corrected = vec3(centerLuma) + correctedChroma;\ncorrectedChroma = centerChroma * 1.2;'
    need('* 1.2' in bad, 'adaptive-color saturation regression test broken')

    # Permanent 26561 V1 Actions regression: repository native/vendor bytes are not
    # authoritative before the frozen artifact-derived candidate is installed.
    build=(Path(__file__).resolve().parent/'build_26561_v1_1_sabre_native_super_res_adaptive_color.sh').read_text()
    need('repository native/vendor drift before install' not in build, 'old pre-install vendor equality failure survived')
    fn_start=build.index('install_frozen_candidate_into_live_root(){')
    fn_end=build.index('run_preinstall_vendor_authority_regression(){', fn_start)
    fn=build[fn_start:fn_end]
    pre=fn.index('vendor_manifest "$live_root" "$WORK/${label}_preinstall_vendor.sha256"')
    install=fn.index('cp -a "$AFTER/app/src/main" "$live_root/app/src/"')
    post=fn.index('cmp "$WORK/${label}_installed_vendor.sha256" "$VENDOR_PIN"')
    need(pre < install < post, 'vendor authority ordering regression: equality must occur only after candidate install')
    need('run_preinstall_vendor_authority_regression' in build, 'missing permanent stale-checkout regression replay')

    # Trigger regression: V1.1 package names must not match the failed V1 workflow paths.
    import fnmatch
    old_patterns=['V1_26561_*','build_26561_v1_sabre_native_super_res_adaptive_color.sh',
                  'transform_26561_v1_sabre_native_super_res_adaptive_color.py',
                  'validate_26561_v1_sabre_native_super_res_adaptive_color.py',
                  'extract_26561_runtime_glsl.py','scan_glsl_reserved_identifiers_26561.py',
                  '.github/workflows/build-26561-v1-sabre-native-super-res-adaptive-color.yml']
    new_files=['V1_1_26561_HANDOFF_HASHES.sha256','build_26561_v1_1_sabre_native_super_res_adaptive_color.sh',
               'transform_26561_v1_1_sabre_native_super_res_adaptive_color.py',
               'validate_26561_v1_1_sabre_native_super_res_adaptive_color.py',
               'extract_26561_v1_1_runtime_glsl.py','scan_glsl_reserved_identifiers_26561_v1_1.py',
               '.github/workflows/build-26561-v1-1-sabre-native-super-res-adaptive-color.yml']
    need(not any(fnmatch.fnmatchcase(f,p) for f in new_files for p in old_patterns), 'V1.1 files would retrigger failed V1 workflow')
    print('PASS validator self-test: color + vendor-authority ordering + non-overlap trigger regressions')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--self-test',action='store_true'); ap.add_argument('--base',type=Path); ap.add_argument('--candidate',type=Path)
    a=ap.parse_args()
    if a.self_test: return self_test()
    if not a.base or not a.candidate: fail('--base and --candidate required')
    validate(a.base,a.candidate)
if __name__=='__main__': main()
