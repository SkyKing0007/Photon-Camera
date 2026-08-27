#!/usr/bin/env python3
from pathlib import Path
import hashlib, math, sys, re

RUNTIME = [
    'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java',
    'app/version.properties',
]

def files(root):
    root=Path(root); out={}
    for p in root.rglob('*'):
        if p.is_file() and '.git' not in p.parts:
            out[p.relative_to(root).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out

def real_color_confidence(mag, support):
    def smoothstep(a,b,x):
        t=max(0.0,min(1.0,(x-a)/(b-a)))
        return t*t*(3-2*t)
    if mag < 256.0: return 0.0
    return smoothstep(2.5,5.0,support)*smoothstep(256.0,1536.0,mag)

def smoothstep(a,b,x):
    t=max(0.0,min(1.0,(x-a)/(b-a)))
    return t*t*(3-2*t)

def artifact_confidence(error_signal):
    return max(0.0,min(1.0,(error_signal-100.0)/200.0))

def directional_preserve(local_confidence, hue_agreement, filtered_mag):
    return local_confidence * smoothstep(0.84,0.97,hue_agreement) * smoothstep(96.0,384.0,filtered_mag)

def self_test():
    # Full old authority must remain available where color is not coherent.
    p=real_color_confidence(3000,0)
    assert p == 0.0
    strength=1.0
    assert abs(strength*(1.0-p)-1.0) < 1e-9
    # Stable real color is protected only when VGN's directional candidate agrees on hue.
    local=real_color_confidence(3000,8)
    assert local > 0.999
    p=directional_preserve(local, 0.99, 1200.0)
    assert p > 0.99
    assert strength*(1.0-p) < 0.01
    # A coherent false-color patch is NOT protected when VGN points neutral or disagrees in hue.
    assert directional_preserve(local, 0.99, 80.0) == 0.0
    assert directional_preserve(local, 0.20, 1200.0) == 0.0
    # Neutral regions do not get artificial color protection.
    assert real_color_confidence(100,8) == 0.0
    # IIR3 is unchanged at strong VGN error and disabled at low error.
    assert artifact_confidence(100.0) == 0.0
    assert artifact_confidence(300.0) == 1.0
    assert 0.49 < artifact_confidence(200.0) < 0.51
    print('PASS: 26549 VGN confidence/error-gate self-tests')

def validate(base, cand):
    base=Path(base); cand=Path(cand)
    mb,mc=files(base),files(cand)
    changed=sorted(k for k in set(mb)|set(mc) if mb.get(k)!=mc.get(k))
    assert changed == RUNTIME, f'changed scope mismatch: {changed}'

    night=(cand/RUNTIME[2]).read_text()
    saver=(cand/RUNTIME[1]).read_text()
    vgn=(cand/RUNTIME[0]).read_text()
    ver=(cand/'app/version.properties').read_text()

    assert 'ImagePath.getNewImageFilePath("jpg")' in night
    assert 'final Path imageFile = ImagePath.newImageFilePath();' not in night
    assert 'IRIS_26549_NIGHT_EXPLICIT_JPEG_TARGET' in night
    for marker in [
        'IRIS_26549_NIGHT_JPEG_TARGET', 'IRIS_26549_NIGHT_JPEG444_RESULT',
        'IRIS_26549_NIGHT_ANDROID_JPEG_RESULT', 'IRIS_26549_NIGHT_ANDROID_JPEG_FAILED']:
        assert marker in saver, marker
    assert 'MotionV2Jpeg444Encoder.write(absolute, img, jpgQuality)' in saver
    assert 'img.compress(Bitmap.CompressFormat.JPEG, jpgQuality, outputStream)' in saver

    for marker in ['IRIS_26549_VGN_TRUE_COLOR_CONFIDENCE','IRIS_26549_VGN_ERROR_GATED_FINAL_IIR']:
        assert marker in vgn, marker
    # Remove the old unconditional low-saturation override.
    assert 'if(abs(sc.x)+abs(sc.y)<abs(fc.x)+abs(fc.y))fc=sc;' not in vgn
    assert 'float preserve=realColorConfidence(p,vec2(originalChroma));' in vgn
    assert 'float hueAgreement=filteredMag>96.0?dot(vec2(originalChroma),vec2(fc))/max(originalMag*filteredMag,1.0):-1.0;' in vgn
    assert 'preserve*=smoothstep(0.84,0.97,hueAgreement)*smoothstep(96.0,384.0,filteredMag);' in vgn
    assert 'float correctionWeight=strength*(1.0-preserve);' in vgn
    assert 'if(uFilterLuma==0)' in vgn
    assert 'float artifactConfidence=clamp((errorSignal-100.0)/200.0,0.0,1.0);' in vgn
    # VGN error generation and blend thresholds remain present.
    assert 'float errorScale=scale(100.0,decodeU16(s.a)*0.25,300.0);' in vgn
    assert 'dispatchError(originalYccd, smoothYccd, scratchYccd)' in vgn
    # The user-facing default remains full authority.
    pref=(cand/'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java').read_text()
    assert '"pref_iris_vgn_chroma_correction", "1.0"' in pref

    assert 'VERSION_NAME=0.9726549' in ver
    assert 'VERSION_BUILD=26549' in ver
    assert 'VERSION_NAME=0.9726548' not in ver
    assert 'VERSION_BUILD=26548' not in ver

    # Explicitly protect Motion publication ownership and core capture/merge files by equality.
    protected=[
      'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
      'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
      'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
      'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt',
      'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
      'app/src/main/cpp/motionv2_jpeg_r_encoder.cpp',
    ]
    for rel in protected:
        assert mb.get(rel)==mc.get(rel), f'protected file drift: {rel}'

    self_test()
    print('PASS: exact four-file 26549 Night JPEG + VGN true-color contract')

if __name__=='__main__':
    if '--self-test' in sys.argv:
        self_test()
    else:
        if len(sys.argv)!=3: raise SystemExit('usage: validate_26549.py BASE CANDIDATE')
        validate(sys.argv[1],sys.argv[2])
