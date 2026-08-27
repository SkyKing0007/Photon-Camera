#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib

REQ_FILES = [
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisNightRgbInput.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java',
'app/src/main/res/values/default_prefs.xml',
'app/src/main/res/values/strings.xml',
'app/src/main/res/xml/preferences.xml',
'app/version.properties',
]

def fail(msg): raise SystemExit('ERROR: '+msg)
def req(text, token, label):
    if token not in text: fail(f'{label}: missing {token!r}')
def forbid(text, token, label):
    if token in text: fail(f'{label}: forbidden {token!r}')

def audited_manifest(root: Path):
    files=[]
    src=root/'app/src/main'
    for p in src.rglob('*'):
        if not p.is_file(): continue
        rel=p.relative_to(root).as_posix()
        if rel.startswith('app/src/main/cpp/third_party_26507/'): continue
        if rel.startswith('app/src/main/cpp/deps/') and rel!='app/src/main/cpp/deps/.gitignore': continue
        files.append(rel)
    for rel in ('app/version.properties','app/build.gradle'):
        if (root/rel).is_file(): files.append(rel)
    out=[]
    for rel in sorted(set(files)):
        out.append(f'{hashlib.sha256((root/rel).read_bytes()).hexdigest()}  {rel}')
    return '\n'.join(out)+'\n'

def changed(base: Path, cand: Path):
    def m(root):
        d={}
        for line in audited_manifest(root).splitlines():
            h,rel=line.split('  ',1); d[rel]=h
        return d
    a,b=m(base),m(cand)
    return sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k))

def validate(base: Path, cand: Path, base_pin: Path|None=None):
    for rel in REQ_FILES:
        if not (cand/rel).is_file(): fail('candidate missing '+rel)
    actual=changed(base,cand)
    if actual != REQ_FILES:
        fail('runtime scope mismatch expected='+repr(REQ_FILES)+' actual='+repr(actual))
    if base_pin and audited_manifest(base) != base_pin.read_text():
        fail('base is not exact pinned successful 26545 V1.4 runtime authority')

    stacker=(cand/REQ_FILES[0]).read_text()
    vgn=(cand/REQ_FILES[1]).read_text()
    sabre=(cand/REQ_FILES[2]).read_text()
    fusion=(cand/REQ_FILES[3]).read_text()
    spatial=(cand/REQ_FILES[4]).read_text()
    capture=(cand/REQ_FILES[5]).read_text()
    night_input=(cand/REQ_FILES[6]).read_text()
    post=(cand/REQ_FILES[7]).read_text()
    settings=(cand/REQ_FILES[8]).read_text()
    night=(cand/REQ_FILES[9]).read_text()
    bridge=(cand/REQ_FILES[10]).read_text()
    prefs=(cand/REQ_FILES[11]).read_text()
    defaults=(cand/REQ_FILES[12]).read_text()
    strings=(cand/REQ_FILES[13]).read_text()
    prefxml=(cand/REQ_FILES[14]).read_text()
    version=(cand/REQ_FILES[15]).read_text()

    # Exact 26545 behavior at slider=1.0 while keeping every VGN stage active.
    req(vgn,'private val chromaCorrectionStrength = chromaCorrectionStrength.coerceIn(0f, 1f)','VGN control')
    req(vgn,'dispatchSeed(assembledRgb, workA)','VGN stage order')
    req(vgn,'dispatchLocal(localClampProgram, workA, workB, "local clamp")','VGN stage order')
    req(vgn,'dispatchLocal(localMedianProgram, workB, assembledRgb, "local median", chromaCorrectionStrength)','VGN stage order')
    req(vgn,'dispatchDirectional(workB, assembledRgb, workA)','VGN stage order')
    req(vgn,'dispatchRestoreDirection(workA, workB, assembledRgb)','VGN stage order')
    req(vgn,'runIirRgb(smoothYccd, scratchYccd, coefficients.pass1, filterLuma = true, "IIR1")','VGN stage order')
    req(vgn,'runIirError(filteredError, spare, coefficients.pass1.a10, coefficients.pass1.b10)','VGN stage order')
    req(vgn,'runIirRgb(filteredYccd, finalScratch, coefficients.pass3, filterLuma = false, "IIR3")','VGN stage order')
    req(vgn,'dispatchFinal(filteredYccd, originalYccd)','VGN stage order')
    # 1.0 endpoint must execute the exact former integer/float expressions, not a rounded mix approximation.
    req(vgn,'strength>=0.9999?sum:','VGN local median exact 1.0 endpoint')
    req(vgn,'strength>=0.9999?fc:','VGN directional exact 1.0 endpoint')
    req(vgn,'if(strength<0.9999){r=strength<=0.0001?inCr:mix(inCr,r,strength);q=strength<=0.0001?inCb:mix(inCb,q,strength);}','VGN IIR exact 1.0 endpoint')
    req(vgn,'if(strength<0.9999)f*=strength;','VGN blend exact 1.0 endpoint')
    for token in ('uniform float uChromaStrength;','GLES31.glUniform1f(host.uniformLocation(directionalProgram, "uChromaStrength"), chromaCorrectionStrength)','GLES31.glUniform1f(host.uniformLocation(blendProgram, "uChromaStrength"), chromaCorrectionStrength)'):
        req(vgn,token,'VGN uniform plumbing')
    for marker in ('IRIS_26532_FOLIAGE_STRUCTURE_GUIDANCE','IRIS_26532_FOLIAGE_LOCAL_MEDIAN_EDGE_GATE','IRIS_26532_NO_EDGE_DESATURATION','IRIS_26532_IIR_CHROMA_EDGE_RESET','IRIS_26532_BLEND_EDGE_CHROMA_PROTECT'):
        forbid(vgn,marker,'VGN rejected older edge policy')
    for coeff in ('0.0674552768f','-1.14298046f','0.00580812711f','-1.86380053f','0.0331984349f','-1.61172712f'):
        req(vgn, coeff, 'VGN current coefficients')

    # End-to-end Motion setting ownership and Night isolation.
    req(settings,'KEY_VGN_CHROMA_CORRECTION = "pref_iris_vgn_chroma_correction"','settings key')
    req(settings,'float vgnChromaCorrection = snap01(getFloat(sm, KEY_VGN_CHROMA_CORRECTION, 1.0f), 0.0f, 1.0f);','settings range/default')
    req(settings,'0.0f, source.chromaDenoise, 1.0f,','Night settings isolation')
    req(prefs,'settingsManager.setInitial(SCOPE_GLOBAL, "pref_iris_vgn_chroma_correction", "1.0");','settings initial')
    req(defaults,'<string name="pref_iris_vgn_chroma_correction_default" translatable="false">1.0</string>','UI default')
    req(strings,'VGN Chroma Correction Strength','UI title')
    req(prefxml,'ns0:key="pref_iris_vgn_chroma_correction"','UI slider')
    req(prefxml,'ns1:maxValue="1.0" ns1:minValue="0.0" ns1:isFloat="true" ns1:stepPerUnit="10"','UI slider range')
    req(bridge,'val vgnChromaCorrectionStrength = if (parameters.irisNightActive) {','bridge owner')
    req(bridge,'1.0f\n            } else {\n                irisSettings.vgnChromaCorrection.coerceIn(0.0f, 1.0f)','Night fixed VGN')
    req(fusion,'vgnChromaCorrectionStrength = vgnChromaCorrectionStrength','fusion propagation')
    req(sabre,'vgnChromaCorrectionStrength = vgnChromaCorrectionStrength','Sabre propagation')
    req(stacker,'chromaCorrectionStrength = vgnChromaCorrectionStrength','Spatial VGN propagation')
    req(spatial,'chromaCorrectionStrength = vgnChromaCorrectionStrength','Sabre VGN propagation')

    # Night still capture must never commandeer the repeating preview surface.
    req(capture,'IRIS_26546_NIGHT_PREVIEW_SURFACE_ISOLATION','Night preview ownership')
    req(capture,'final boolean iris26546AddPreviewTarget = iris26533CaptureMode != CameraMode.NIGHT','Night preview ownership')
    req(capture,'if (iris26546AddPreviewTarget) captureBuilder.addTarget(surface);','Night preview ownership')
    req(capture,'IRIS_26546_NIGHT_PREVIEW_SURFACE_ISOLATED stillTarget=false repeatingPreviewIndependent=true','Night preview telemetry')
    forbid(capture,'final boolean iris26540AddPreviewTarget = iris26533CaptureMode == CameraMode.NIGHT','old Night preview coupling')

    # True two-GPU-buffer Night post entry and early CPU carrier release.
    req(night_input,'basePipeline.main1 = new GLTexture(raw, rgba16f, view, GL_LINEAR, GL_CLAMP_TO_EDGE);','Night main1 upload')
    req(night_input,'basePipeline.main2 = new GLTexture(raw, work, null, GL_LINEAR, GL_CLAMP_TO_EDGE);','Night main2 ping-pong')
    if night_input.count('new GLTexture(') != 2:
        fail('Night input must allocate exactly two GLTexture objects, got '+str(night_input.count('new GLTexture(')))
    req(night_input,'WorkingTexture = basePipeline.main1;','Night upload alias')
    req(night_input,'pipeline.irisNightRgba16f = null;','Night carrier handoff clear')
    req(night_input,'Allocator.free(source);','Night CPU release')
    req(night_input,'basePipeline.main3 = null;','Night no main3')
    req(night_input,'basePipeline.texnum = 1;','Night ping-pong phase')
    if not (night_input.index('Allocator.free(source);') < night_input.index('basePipeline.main2 = new GLTexture')):
        fail('Night CPU carrier is not released before main2 allocation')
    forbid(night_input,'WorkingTexture = new GLTexture','Night third upload texture')

    # PostPipeline is sole post-entry carrier owner; caller cannot double free it.
    req(post,'ByteBuffer unreleasedNightCarrier = irisNightRgba16f;','Night fallback owner')
    req(post,'Allocator.free(unreleasedNightCarrier);','Night fallback release')
    req(post,'NIGHT_POST_CLOSE_BEGIN','Night EGL close-before-Jin')
    req(night,'ByteBuffer postOwnedRgb = rgb;','Night ownership transfer')
    req(night,'rgb = null;\n            img = pipeline.RunIrisNightRgb(postOwnedRgb, p);','Night ownership transfer')
    forbid(night,'try { Allocator.free(rgb); } catch (Throwable ignored) {}\n                Log.critical(TAG, "IRIS_26544_NIGHT_RGBA16F_RELEASED','old caller-owned post release')
    req(night,'Night pre-Jin UltraHDR is forbidden','Night UHDR ownership preserved')

    # Preserve historical compiler fixes and current-MGC owner semantics in touched Kotlin/Java.
    req(stacker,'bentoFlowTexture = flow.texture','26545 V1.3 Kotlin regression')
    forbid(spatial,'coreImagingTuning','26545 V1.3 Kotlin regression')
    req(spatial,'private val sabreMergeGradientThreshold: Float? = null','Sabre adaptive threshold owner')
    req(capture,'java.nio.ByteBuffer source = plane.getBuffer().duplicate();','26543 Java ByteBuffer regression')

    # Version is coupled to this guarded build candidate only.
    req(version,'VERSION_NAME=0.9726546','version')
    req(version,'VERSION_BUILD=26546','build')

    print('PASS: exact 16-file 26545 V1.4 -> 26546 V1 runtime scope')
    print('PASS: VGN 0..1 chroma control with exact 1.0 26545 endpoint and unchanged stage order')
    print('PASS: Motion slider ownership + Night fixed at VGN 1.0')
    print('PASS: Night repeating-preview isolation while RAW still capture remains separate')
    print('PASS: Night true two-GPU-buffer entry + CPU carrier release before main2 allocation')
    print('PASS: post-entry Night carrier ownership and close-before-Jin lifecycle')
    print('PASS: permanent Kotlin/Java compiler-regression contracts retained')

def self_test():
    assert len(REQ_FILES)==16 and len(set(REQ_FILES))==16
    assert REQ_FILES == sorted(REQ_FILES)
    print('PASS: 26546 V1 validator self-test')

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--base'); ap.add_argument('--candidate'); ap.add_argument('--base-pin'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args()
    if a.self_test: self_test()
    else:
        if not a.base or not a.candidate: ap.error('--base and --candidate required')
        validate(Path(a.base),Path(a.candidate),Path(a.base_pin) if a.base_pin else None)
