#!/usr/bin/env python3
"""Exact 26907 compilation/sample regression, no stubs in place of production code."""
import hashlib,pathlib,subprocess,tempfile
R=pathlib.Path(__file__).resolve().parent

def assert_true(condition,why):
    if not condition:raise RuntimeError('26907 hue source regression failed: '+why)
def parse(path):
    d={}
    for ln in path.read_text().splitlines():
        h,name=ln.split('  ',1); assert_true(name not in d,'duplicate '+name)
        d[name]=h
    return d

def main():
    base=parse(R/'26907_BASE_26906_FULL_APP.sha256')
    expected=parse(R/'26907_PRECOMPILE_EXPECTED_FULL_APP.sha256')
    changed=set((R/'26907_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
    added=set((R/'26907_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
    assert_true(len(base)==2027 and len(expected)==2030 and len(changed)==7 and len(added)==3,'source count')
    assert_true((set(expected)-set(base))==added and not(set(base)-set(expected)),'added or removed source mismatch')
    assert_true({p for p in base if base[p]!=expected[p]}==changed-added,'protected source changed')
    for p in changed:
        f=R/'handoff_payload_26907'/p
        assert_true(f.is_file() and hashlib.sha256(f.read_bytes()).hexdigest()==expected[p], 'payload SHA '+p)
    body=(R/'handoff_payload_26907/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline')
    matcher=(body/'MotionV2ViewfinderExposureMatcher.java').read_text()
    scene=(body/'MotionV2PreviewHueCalibration.java').read_text()
    sampler=(body/'MotionV2PreviewHueMatch.java').read_text()
    graph=(body/'PostPipeline.java').read_text()
    params=(R/'handoff_payload_26907/app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java').read_text()
    shader=(R/'handoff_payload_26907/app/src/main/assets/shaders/motionv2/preview_hue_match_26907.glsl').read_text()
    assert_true(matcher.count('MotionV2PreviewHueMatch.inspectAtExistingMatcher(')==1,'wrong matcher hook')
    assert_true(matcher.count('basePipeline.mParameters.motionV2PreviewHueLut26907 = null;')==1,'missing one-shot reset')
    assert_true(graph.count('add(new MotionV2PreviewHueMatch());')==1,'wrong B Photo-only shader stage')
    hue_node=graph.index('add(new MotionV2PreviewHueMatch());')
    # The same matcher is also used by Night earlier in this file: constrain the
    # order test to the actual B Photo branch owning the new hue node.
    photo_matcher=graph.rfind('add(new MotionV2ViewfinderExposureMatcher());',0,hue_node)
    photo_exposure=graph.index('add(new MotionV2DisplayExposure());',hue_node)
    assert_true(photo_matcher>=0 and photo_matcher<hue_node<photo_exposure,
                'wrong B Photo hue/exposure order')
    assert_true('public float[] motionV2PreviewHueLut26907 = null;' in params,'missing one-shot source LUT')
    assert_true('MotionV2PreviewHueCalibration.measure(' in sampler,'missing actual source comparison')
    assert_true('motionV2SuperResOutputEnabled' in sampler and 'motionV2HighZoomRgbPrepared' in sampler,'missing SR/high-zoom isolation')
    assert_true('actualPreviewMeasured=true' in sampler,'not preview-measured')
    assert_true('MAX_HUE_CHANGE' in scene and 'registration_uncertain' in scene and 'already_consistent' in scene,'missing failsafe proof')
    assert_true('dot(p3,P3_Y)' in shader and 'oldY/newY' in shader,'luma not preserved')
    assert_true('float delta=measuredDelta' in shader and 'chroma=length(lab.yz)' in shader,'not hue-only')
    assert_true('float hue' in shader or 'float position' in shader,'hue table not evaluated')
    assert_true('#version' not in shader,'shader has pre-injected version')
    with tempfile.TemporaryDirectory(prefix='photon26907_javac_') as dst:
        cmd=['javac','-source','17','-target','17','-d',dst,
             str(body/'MotionV2PreviewHueCalibration.java'),
             str(R/'tests_26907/Photon26907HueRegression.java')]
        subprocess.run(cmd,check=True)
        subprocess.run(['java','-cp',dst,'Photon26907HueRegression'],check=True)
    print('PASS 26907 exact seven-path scope, 2023 protected, three added, actual javac calibration math, good/already-match/bad-input regressions, B Photo-SR-OFF hue-only guard')

if __name__=='__main__':main()
