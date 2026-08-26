#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, xml.etree.ElementTree as ET

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def fail(m): raise SystemExit('FAIL: '+m)
def need(c,m):
    if not c: fail(m)
def txt(root,rel): return (root/rel).read_text()

def audited_manifest(root):
    files=[]
    for p in (root/'app/src/main').rglob('*'):
        if not p.is_file(): continue
        rel=str(p.relative_to(root))
        if rel.startswith('app/src/main/cpp/third_party_26507/') or rel.startswith('app/src/main/cpp/deps/'):
            if rel=='app/src/main/cpp/deps/.gitignore': files.append(p)
            continue
        files.append(p)
    for rel in ('app/version.properties','app/build.gradle'):
        p=root/rel
        if p.is_file(): files.append(p)
    return ''.join(f'{sha(p)}  {p.relative_to(root)}\n' for p in sorted(files,key=lambda p:str(p.relative_to(root))))

def filemap(root):
    d={}
    for p in (root/'app/src/main').rglob('*'):
        if not p.is_file(): continue
        rel=str(p.relative_to(root))
        if rel.startswith('app/src/main/cpp/third_party_26507/') or rel.startswith('app/src/main/cpp/deps/'):
            if rel!='app/src/main/cpp/deps/.gitignore': continue
        d[rel]=p
    for rel in ('app/build.gradle','app/version.properties'):
        p=root/rel
        if p.is_file(): d[rel]=p
    return d

ALLOWED=sorted('''
app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt
app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt
app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
app/src/main/java/com/hinnka/mycamera/processor/MgcSabreKernelTuning.kt
app/src/main/java/com/hinnka/mycamera/processor/MgcSabreRejectionTuning.kt
app/src/main/java/com/hinnka/mycamera/raw/MgcFullResolutionDenoise.kt
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt
app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java
app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java
app/src/main/res/values/arrays.xml
app/src/main/res/values/default_prefs.xml
app/src/main/res/values/strings.xml
app/src/main/res/xml/preferences.xml
app/version.properties
'''.strip().splitlines())

PROTECTED=[
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IsoExpoSelector.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/UltraHdrSaver.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightMgc1271Bridge.kt',
]

def run(base,cand,base_pin):
    need(base.is_dir() and cand.is_dir(),'base/candidate directory missing')
    bm=audited_manifest(base)
    need(bm==base_pin.read_text(),'base is not exact frozen 26544 audited Iris authority')
    need(len(bm.splitlines())==967,'base audited authority is not 967 files')
    mb,mc=filemap(base),filemap(cand)
    changed=sorted(k for k in set(mb)|set(mc) if (sha(mb[k]) if k in mb else None)!=(sha(mc[k]) if k in mc else None))
    need(changed==ALLOWED,'changed runtime scope mismatch: '+repr(changed))
    for rel in PROTECTED:
        need(sha(base/rel)==sha(cand/rel),'protected control owner changed: '+rel)

    fusion=txt(cand,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt')
    bridge=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
    settings=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java')
    processor=txt(cand,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt')
    stack=txt(cand,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
    shaders=txt(cand,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
    hdrx=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java')
    prefs=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java')
    settings_activity=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java')
    denoise=txt(cand,'app/src/main/java/com/hinnka/mycamera/raw/MgcFullResolutionDenoise.kt')
    px=txt(cand,'app/src/main/res/xml/preferences.xml')
    defaults=txt(cand,'app/src/main/res/values/default_prefs.xml')
    strings=txt(cand,'app/src/main/res/values/strings.xml')
    version=txt(cand,'app/version.properties')
    need('VERSION_NAME=0.9726545' in version and 'VERSION_BUILD=26545' in version,'target version/build drift')

    for m in ['SPATIAL_RGB("spatial_rgb")','SABRE("sabre")','KEY_RECONSTRUCTION = "pref_iris_motion_reconstruction"']:
        need(m in settings,'settings selector contract missing '+m)
    need('return new Snapshot(Reconstruction.SPATIAL_RGB, source.noiseReductionEnabled' in settings,'Night snapshot does not force Spatial selector isolation')
    need('val sabreSelected = !parameters.irisNightActive &&' in bridge,'Sabre is not hard-gated away from Night')
    need('irisSettings.reconstruction == IrisMotionSettings.Reconstruction.SABRE' in bridge,'Motion setting does not select Sabre')
    need('pref_iris_motion_reconstruction' in px and 'defaultValue="spatial_rgb"' in px,'UI selector/default missing')
    need('map.putIfAbsent("pref_iris_motion_reconstruction", "spatial_rgb")' in prefs,'Motion selector default missing')
    need('KEY_LUMA_DENOISE = "pref_iris_luma_denoise_v2"' in settings,'functional luma v2 key missing')
    need('getFloat(sm, KEY_LUMA_DENOISE, 0.0f)' in settings,'functional luma default is not zero')
    need('0.0f, source.chromaDenoise' in settings,'Night luma is not frozen at zero')
    need('pref_iris_luma_denoise_v2' in px and 'pref_iris_luma_denoise"' not in px,'UI still consumes legacy ignored luma key')
    need('<string name="pref_iris_luma_denoise_default" translatable="false">0.0</string>' in defaults,'luma UI default is not zero')
    need('pref_iris_chroma_denoise_default" translatable="false">1.0</string>' in defaults,'chroma default drift')
    need('both Spatial RGB and Sabre' in strings,'custom .c UI does not state shared reconstruction ownership')
    need('removePreferenceAnywhere(IrisMotionSettings.KEY_RECONSTRUCTION);' in settings_activity,'reconstruction selector visible outside Motion')

    need('return GlesIris26545SabreProcessor(' in fusion,'Fusion SABRE does not route to Iris owner')
    need('GlesIris26521SpatialRgbStacker' in fusion,'Spatial RGB no longer routes to proven owner')
    need('mergeMethod = MgcMergeMethod.SABRE' in processor and 'processorPipeline = MgcRawProcessorPipeline.SABRE' in processor,'Sabre pipeline activation missing')
    need('frames[index].role == RawBurstFrameRole.NORMAL' in processor,'Sabre NORMAL-only frame admission missing')
    need('excluded.forEach { frames[it].image.close() }' in processor,'excluded bracket frame close missing')
    need('MgcSabreResolver.resolve(' in stack,'ResolveSabre missing')
    need('RunMotionV2FloatCfa' in hdrx and 'rcdBypassed=true demosaicBypassed=true' in hdrx,'direct-RGB post contract missing')

    need('mergeMethod = if (sabreSelected) MgcMergeMethod.SABRE else MgcMergeMethod.SPATIAL_RGB' in bridge,'selector merge routing missing')
    need('outputMode = MgcSpatialOutputMode.RGB' in bridge,'common linear RGB output missing')
    need('gpuLinearRgbStorage = GpuLinearRgbStorage.RGBA16F' in bridge,'common RGBA16F carrier changed')
    need('parameters.motionV2DisplayGain = 1.0f' in bridge,'existing display-gain owner missing')

    # One physical noise selection feeds both reconstruction methods; user sliders act later only.
    need(fusion.count('noiseProfileSelection = noiseProfileSelection') >= 2,
         'selected noise profile is not passed to both Sabre and Spatial owners')
    need('RawNoiseProfileSelection.Calibrated(profile)' in bridge,'custom .c is not reconstruction noise authority')
    need('profile.evaluate(mgcBase.motionV2ActualIso)' in bridge,'custom .c residual noise is not evaluated at actual MGC base ISO')
    need('baseNoiseModel.canonicalChannelPairs()' in bridge,'custom .c canonical denoise pairs missing')
    need('denoiseChannelNoiseProfile = mgcBase.motionV2NoiseProfile.copyOf()' in bridge,
         'Camera2 residual denoise does not use actual MGC base noise metadata')
    need('mgcSabreNoiseModelScale = if (sabreSelected) sabreNoiseScale else null' in bridge,
         'measured Sabre noise scale not handed to residual denoise')
    need('val denoisePass = if (sabreSelected)' in bridge and
         'MgcFullResolutionDenoise.Pass.SABRE_DEFAULT' in bridge and
         'MgcFullResolutionDenoise.Pass.SPATIAL_DEFAULT' in bridge,
         'shared residual denoise pass selection missing')
    need('val runFullResolutionDenoise = irisSettings.noiseReductionEnabled &&' in bridge,
         'shared residual denoise master gate missing')
    need('!sabreSelected && irisSettings.noiseReductionEnabled' not in bridge,
         'Sabre is still excluded from user residual denoise')
    need('val lumaScale = requestedLumaScale' in bridge and
         'val chromaScale = irisSettings.chromaDenoise.coerceIn(0f, 2f)' in bridge,
         'luma/chroma sliders are not direct residual strength controls')
    denoise_call=bridge.index('MgcFullResolutionDenoise.denoise(')
    float_convert=bridge.index('convertHalfRgbaToFloatRgba(')
    need(denoise_call < float_convert,'residual denoise moved after Motion carrier conversion')
    bridge_call=hdrx.index('PhotonMotionMgc1271Bridge.reconstruct(')
    post_call=hdrx.index('RunMotionV2FloatCfa')
    need(bridge_call < post_call,'residual denoise/reconstruction moved after PostPipeline/tone entry')
    need('sliderAffectsMerge=false sliderAffectsExposure=false sliderAffectsTone=false' in bridge,
         'slider ownership diagnostic missing')
    need('DenoiseStrength.clamp(lumaStrengthScale)' in denoise and
         'DenoiseStrength.clamp(chromaStrengthScale)' in denoise,
         'denoise host does not independently clamp user strengths')
    need('val lumaEnabled = finiteLumaScale > 0f' in denoise and
         'val chromaEnabled = finiteChromaScale > 0f' in denoise,
         '0=off component semantics missing')
    need('.withStrengthScale(finiteLumaScale)' in denoise and
         '.withStrengthScale(finiteChromaScale)' in denoise,
         'user sliders do not scale only denoise tuning')
    need('IRIS_26545_MEASURED_SABRE_RESIDUAL_NOISE' in denoise,
         'Sabre residual noise-model authority marker missing')
    need('reciprocal SNR-table reduction' not in denoise,
         'retired Sabre SNR lookup-table denoise authority survived')
    need('irisSettings.lumaDenoise' not in stack and 'irisSettings.chromaDenoise' not in stack,
         'user denoise strength leaked into reconstruction owner')

    need('IRIS_26545_SABRE_MEASURED_SUPPORT' in stack,'measured support marker missing')
    need('val sabreAverageMergeFactor = readSabreAverageMergeFactor(' in stack,'measured Sabre merge factor missing')
    need('val sabreNoiseModelScale = sabreAverageMergeFactor' in stack,'measured Sabre scale not propagated')
    need('classicSabreNoiseModelScale' not in stack and 'SABRE_DENOISE_' not in stack,'stale pre-merge Sabre noise owner survived')
    need('reciprocalGreenWeight4x4' in shaders and 'weightQ8 = max(floor(weight * 256.0 + 0.5), 1.0)' in shaders,'current Q8 support shader missing')
    need('Half.toFloat' in stack,'half-float measured support readback missing')
    need('mgcDenoiseTuningSnr = kernelTuning.referenceSnr / sqrt(sabreNoiseModelScale)' in stack,'measured output SNR not propagated')

    need('const val SABRE_GUIDE_BORDER_PIXELS = 2.5f' in stack,'Sabre guide border drift')
    need('const val SABRE_SAMPLE_BORDER_PIXELS = 1.5f' in stack,'Sabre sample border drift')
    for m in ['uFlowScaleOffset','flowVariationThresholds','forceReferenceColorRgb']:
        need(m in stack or m in shaders,'current Sabre geometry/rejection contract missing '+m)

    need('exportNormalStackedDng = produceNormalStackedDng' in bridge,'shared RAW request routing missing')
    need('layout(location = 0) out vec2 oSignalAndWeight' in shaders,'Sabre Bayer DNG signal/weight merge missing')
    need('uniform vec4 uPhaseGains;' in shaders and 'uniform vec4 uPhaseBlackTerms;' in shaders,'DNG exposure/black normalization missing')
    need('sameSabreFlow=true sameSabreRejection=true sameSabreCovariance=true' in stack,'DNG Sabre evidence provenance missing')
    need('resolveSabre=false demosaic=false wb=false lsc=false denoise=false' in stack,'DNG no-baked-processing invariant missing')
    need('fullRangeNormalized16=true blackLevel=0 whiteLevel=65535' in stack,'DNG normalized16 invariant missing')
    need('saveNormalized16StackedRaw' in hdrx,'normalized16 DNG writer missing')
    need('sameAdmittedNormalPopulation=true' in hdrx and 'shortLongBentoExcludedFromDng=true' in hdrx,'JPEG/DNG population invariant missing')
    need('output == iris26480DeferredDng' in hdrx,'JPEG/DNG buffer alias guard missing')

    need('val normalDngAccumulator = if (exportNormalStackedDng)' in stack,'DNG accumulator is not request-gated')
    need(stack.count('val normalDngAccumulator = if (exportNormalStackedDng)')==1,'multiple persistent Sabre DNG accumulators')
    need('releaseTexturesFrom(transientTextureStart)' in stack,'per-frame transient texture release missing')
    need('LargeDirectBuffer.free(normalStackedDngRaw16)' in stack,'DNG failure cleanup missing')

    for bad in ['PyramidAlignment','PyramidMerging','ExposureFusionBayer2','ADRC']:
        need(bad not in processor,'legacy owner leaked into Sabre adapter: '+bad)
    for rel in ['app/src/main/res/xml/preferences.xml','app/src/main/res/values/arrays.xml','app/src/main/res/values/default_prefs.xml','app/src/main/res/values/strings.xml']:
        ET.parse(cand/rel)

    print('PASS: EXACT PRIOR RUNTIME AUTHORITY 26544 frozen 967-file Iris manifest')
    print('PASS: CHANGED RUNTIME SCOPE exact 18 files')
    print('PASS: RUNTIME OWNERSHIP Motion selector -> Iris Sabre -> ResolveSabre -> common Iris RGB')
    print('PASS: DORMANT-OWNER REJECTION Spatial control unchanged; Night/legacy owners excluded')
    print('PASS: capture/exposure/UHDR/PostPipeline/Night/Spatial control hashes unchanged')
    print('PASS: current Sabre sparse-flow/rejection + measured merge-support propagation')
    print('PASS: Sabre normalized16 stacked Bayer DNG same-normal-population/no-baked-processing contract')
    print('PASS: bounded request-only DNG accumulator + per-frame transient release')
    print('PASS: shared .c/Camera2 noise authority + independent 0..2 luma/chroma pre-tone controls')
    print('PASS: modified Android resource XML parses')

def self_test():
    assert len(ALLOWED)==18 and len(set(ALLOWED))==18
    assert len(PROTECTED)==8 and len(set(PROTECTED))==8
    print('PASS: 26545 validator self-test')

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--base'); ap.add_argument('--candidate'); ap.add_argument('--base-pin'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args()
    if a.self_test: self_test()
    else:
        if not (a.base and a.candidate and a.base_pin): ap.error('--base --candidate --base-pin required')
        run(Path(a.base),Path(a.candidate),Path(a.base_pin))
