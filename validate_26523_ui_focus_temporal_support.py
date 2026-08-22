#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,importlib.util,re,sys
from pathlib import Path

EXPECTED_CHANGED={
'app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt',
'app/src/main/java/com/particlesdevs/photoncamera/control/TouchFocus.java',
'app/src/main/java/com/particlesdevs/photoncamera/control/Swipe.java',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/res/xml/preferences.xml',
}

def files(root:Path):
    out={}
    for p in (root/'app/src/main').rglob('*'):
        if p.is_file():
            rel=p.relative_to(root).as_posix(); out[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
    return out

def read(root:Path,rel:str)->str:
    return (root/rel).read_text(encoding='utf-8').replace('\r\n','\n').replace('\r','\n')

def triple(text:str,name:str)->str:
    m=re.search(r'(?:(?:const\s+)?val)\s+'+re.escape(name)+r'\s*(?::\s*String)?\s*=\s*"""(.*?)"""(?:\.trimIndent\(\))?',text,re.S)
    if not m: raise AssertionError('embedded shader missing '+name)
    return m.group(1)

def block(text:str,start:str,end:str)->str:
    a=text.find(start); b=text.find(end,a+len(start))
    if a<0 or b<0: raise AssertionError('block boundary missing: '+start+' / '+end)
    return text[a:b]

def require(text:str,tok:str,label:str='token'):
    if tok not in text: raise AssertionError(f'{label} missing: {tok}')

def forbid(text:str,tok:str,label:str='token'):
    if tok in text: raise AssertionError(f'{label} survived unexpectedly: {tok}')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--base',required=True,type=Path)
    ap.add_argument('--candidate',required=True,type=Path)
    ap.add_argument('--apply',required=True,type=Path)
    ap.add_argument('--patch',required=True,type=Path)
    ap.add_argument('--patch-sha',required=True,type=Path)
    a=ap.parse_args()

    # Load the exact handoff transform and prove the candidate equals its deterministic output.
    spec=importlib.util.spec_from_file_location('apply26523',a.apply)
    mod=importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(mod)
    assert set(mod.CHANGED)==EXPECTED_CHANGED, f'apply changed-set drift: {set(mod.CHANGED)^EXPECTED_CHANGED}'

    base_files=files(a.base); cand_files=files(a.candidate)
    assert set(base_files)==set(cand_files), 'runtime files added/removed unexpectedly'
    changed={p for p in base_files if base_files[p]!=cand_files[p]}
    assert changed==EXPECTED_CHANGED, f'26523 runtime changed-set mismatch: {sorted(changed)}'
    assert read(a.base,'app/version.properties')==read(a.candidate,'app/version.properties'), 'version changed before guarded build stage'
    for rel in sorted(EXPECTED_CHANGED):
        expected=mod.expected_for(rel,read(a.base,rel))
        actual=read(a.candidate,rel)
        assert actual==expected, 'candidate is not exact deterministic transform for '+rel

    # Rollback patch must exist and its detached SHA file must verify it.
    patch_bytes=a.patch.read_bytes(); digest=hashlib.sha256(patch_bytes).hexdigest()
    sha_line=a.patch_sha.read_text().strip().split()
    assert len(sha_line)>=2 and sha_line[0]==digest and sha_line[-1]==a.patch.name, 'rollback patch SHA mismatch'
    assert patch_bytes, 'rollback patch empty'

    bshader=read(a.base,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt')
    cshader=read(a.candidate,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt')
    bstack=read(a.base,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt')
    cstack=read(a.candidate,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt')

    # 26522 IQ floor: active RGB reconstruction and DNG normalization are byte-identical.
    assert triple(bshader,'mergeRgb')==triple(cshader,'mergeRgb'), 'ACTIVE mergeRgb changed'
    assert triple(bshader,'normalizeBayer')==triple(cshader,'normalizeBayer'), 'normalizeBayer changed'
    for tok in ('IRIS_26521_V4_DIRECTIONAL_GREEN','IRIS_26521_V4_ROBUST_SPATIAL_KERNEL',
                'IRIS_26521_V4_ROBUST_COLOR_DIFFERENCE','IRIS_26520_V5_CONTINUOUS_FINEST_LK_TRANSPORT'):
        require(cshader,tok,'frozen RGB/alignment marker')
    for tok in ('IRIS_26520_V5_FINAL_FINEST_LK_OWNER','IRIS_26520_V5_MERGE_DOMAIN_REJECTION_FLOW',
                'IRIS_26520_V5_SPATIAL_RGB_TWO_SLOT_RAW_LIFETIME','IRIS_26522_NORMALIZED16_DNG_FULL_PRECISION'):
        require(cstack,tok,'frozen stack marker')
    require(cstack,'normalStackedDngRaw16 = readBayer16(normalizedTexture)','full-range DNG readback')
    forbid(cstack,'convertNormalizedBayer16ToSensorCode','old sensor-code requantization')

    # 26523 support math: keep signal/sum-weight unchanged; fix variance moment at sample level.
    mb=triple(cshader,'mergeBayer')
    for tok in ('IRIS_26523_DNG_FRAME_EQUIVALENT_SUPPORT_MOMENTS',
                'float accumulatedWeightSquared = 0.0;',
                'accumulatedWeightSquared += weight * weight;',
                'accumulatedWeightSquared += otherWeight * otherWeight;',
                'intensity * frameWeight,','contributionWeight,',
                'accumulatedWeightSquared * frameWeight * frameWeight',
                'referenceNormalizedKernelVariance'):
        require(mb,tok,'26523 mergeBayer support')
    forbid(mb,'contributionWeight * contributionWeight / 256.0','26522 biased support moment')
    support=triple(cshader,'normalDngSupportQ8')
    for tok in ('IRIS_26523_DNG_FRAME_EQUIVALENT_SUPPORT_Q8',
                'sumIndividualW2','referenceNormalizedVariance',
                'referenceNormalizedVariance * sumW * sumW / sumIndividualW2',
                'clamp(effective, 1.0, max(uMaximumFrames, 1.0))'):
        require(cshader if tok.startswith('IRIS_') else support,tok,'26523 support shader')
    require(cstack,'IRIS_26523_DNG_FRAME_EQUIVALENT_SUPPORT_STATS','support stats marker')
    require(cstack,'IRIS_26523_DNG_FRAME_EQUIVALENT_SUPPORT grid=','support trace')
    require(cstack,'harmonic reference-frame-equivalent support','DNG noise model comment')

    # DNG metadata: ordinary RAW behavior is preserved; synthetic stacked DNG suppresses the
    # one-frame Description/NoiseProfile before emitting exactly one stacked version.
    dng=read(a.candidate,'app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java')
    saver=read(a.candidate,'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java')
    require(dng,'IRIS_26523_DNG_SINGLE_METADATA_OWNERSHIP')
    require(dng,'setParameters(parameters, true, true);','ordinary DNG wrapper')
    require(dng,'public void setParameters(Parameters parameters, boolean includeDescription, boolean includeNoiseProfile)')
    require(dng,'if (includeDescription) setDescription(parameters.toString());')
    require(dng,'if (includeNoiseProfile && parameters.noiseModeler != null')
    stacked=block(saver,'IRIS_26522_NORMALIZED16_STACKED_DNG_WRITER','public static boolean saveSingleRaw(')
    require(stacked,'dngCreator.setParameters(parameters, false, false);')
    assert stacked.count('dngCreator.setNoiseProfile(noiseProfile);')==1, 'stacked DNG explicit NoiseProfile count != 1'
    assert stacked.count('dngCreator.setDescription(')==1, 'stacked DNG explicit Description count != 1'
    for tok in ('dngCreator.setBitsPerSample(16);','dngCreator.setBlackLevel(new short[]{0, 0, 0, 0});',
                'dngCreator.setWhiteLevel(65535.0);','FrameEquivalentNoiseSupport=',
                'HarmonicReferenceFrameEquivalentSupport','IRIS_26523_SINGLE_METADATA=true'):
        require(stacked,tok,'stacked DNG metadata')
    single=block(saver,'public static boolean saveSingleRaw(','public static boolean saveStackedRaw(') if saver.find('public static boolean saveStackedRaw(',saver.find('public static boolean saveSingleRaw('))>=0 else saver[saver.find('public static boolean saveSingleRaw('):]
    require(single,'dngCreator.setParameters(parameters);','ordinary single RAW metadata path')

    # About screen ends after Your Device and uses the actual launcher icon.
    prefs=read(a.candidate,'app/src/main/res/xml/preferences.xml')
    about=block(prefs,'<PreferenceCategory ns0:layout="@layout/preference_category_layout" ns0:key="@string/pref_category_about_key"','</PreferenceCategory>')
    for tok in ('IRIS_26523_ABOUT_MINIMAL_IRIS','ns0:icon="@mipmap/ic_launcher"','@string/pref_version_key','@string/pref_this_device_key'):
        require(about,tok,'About screen')
    for tok in ('photon_camera_summary','pref_contributors_key','pref_telegram_channel_key','all_devices_names'):
        forbid(about,tok,'removed About row')

    # Touch acceptance is bounded by the rendered GLPreview, not the full black textureHolder.
    swipe=read(a.candidate,'app/src/main/java/com/particlesdevs/photoncamera/control/Swipe.java')
    for tok in ('IRIS_26523_ACTUAL_PREVIEW_TOUCH_BOUNDS','preview.getLocationOnScreen(location)',
                'event.getRawX() - location[0]','event.getRawY() - location[1]',
                'public void onLongPress(MotionEvent e)','touchFocus.processLongPressToLock',
                'touchFocus.isFocusLocked()','touchFocus.unlockFocus()'):
        require(swipe,tok,'Swipe focus gesture')
    old_focus_block=re.search(r'private void startTouchToFocus\(MotionEvent event\).*?\n    \}',swipe,re.S)
    assert old_focus_block and 'layout_viewfinder' not in old_focus_block.group(0), 'old oversized viewfinder focus bounds survived'

    # Focus metering uses active/crop coordinates, has the old x/y clamp defect removed, and uses
    # Camera2 AF trigger state rather than manual lens distance or AE lock.
    tf=read(a.candidate,'app/src/main/java/com/particlesdevs/photoncamera/control/TouchFocus.java')
    for tok in ('IRIS_26523_REAL_AF_LOCK_STATE','IRIS_26523_ACTIVE_CROP_FOCUS_MAPPING',
                'SENSOR_INFO_ACTIVE_ARRAY_SIZE','SENSOR_INFO_PRE_CORRECTION_ACTIVE_ARRAY_SIZE',
                'CaptureRequest.SCALER_CROP_REGION','crop.intersect(coordinateArray)',
                'targetSensorAspect','CaptureRequest.CONTROL_AF_TRIGGER_START',
                'CaptureRequest.CONTROL_AF_TRIGGER_CANCEL','CaptureRequest.CONTROL_AF_TRIGGER_IDLE',
                'processLongPressToLock','resumeLockedFocusAfterCapture','focusLocked = lockRequested'):
        require(tf,tok,'TouchFocus')
    # SENSOR_INFO_PIXEL_ARRAY_SIZE remains only as a last-resort portability fallback if a broken
    # HAL omits active-array metadata; it is not the primary coordinate authority.
    assert tf.find('SENSOR_INFO_ACTIVE_ARRAY_SIZE') < tf.find('SENSOR_INFO_PIXEL_ARRAY_SIZE'), 'pixel array became primary focus domain'
    forbid(tf,'LENS_FOCUS_DISTANCE','manual lens-distance focus')
    forbid(tf,'CONTROL_AE_LOCK','AE lock')
    forbid(tf,'if (x_to_set - width_to_set > sizee.getWidth())\n            y_to_set','historical x/y clamp bug')
    require(tf,'focusCircleView.setOnTouchListener(null);','focus ring pass-through')
    require(tf,'focusCircleView.setClickable(false);','focus ring pass-through')

    cap=read(a.candidate,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
    require(cap,'IRIS_26523_PRESERVE_USER_AF_LOCK_ACROSS_CAPTURE','capture AF lock preservation')
    preserve=block(cap,'IRIS_26523_PRESERVE_USER_AF_LOCK_ACROSS_CAPTURE','IRIS_26484_UNLOCK_FOCUS_NULL_BUILDER_GUARD')
    require(preserve,'mTouchFocus.isFocusLocked()')
    require(preserve,'mTouchFocus.resumeLockedFocusAfterCapture()')

    # No routing/processing fallback families are introduced by this handoff.
    candidate_concat='\n'.join(read(a.candidate,p) for p in EXPECTED_CHANGED)
    for tok in ('PyramidAlignment','MgcSabre','MotionV2CfaReconstruction.reconstruct('):
        forbid(candidate_concat,tok,'forbidden processing path')

    print('PASS: exact eight-file 26523 transform verified')
    print('PASS: 26522 active RGB/alignment/rejection and normalized16 DNG pixels are frozen')
    print('PASS: frame-equivalent support uses individual Spatial sample moments, not 26522 sum-then-square')
    print('PASS: stacked DNG owns one Description/NoiseProfile while ordinary RAW metadata behavior is preserved')
    print('PASS: About + actual-preview focus bounds + active/crop metering + real long-press AF lock verified')

if __name__=='__main__':
    main()
