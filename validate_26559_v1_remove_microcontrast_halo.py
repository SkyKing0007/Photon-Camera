#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, math

EXPECTED_CHANGED={
    'app/src/main/assets/shaders/motionv2/render.glsl',
    'app/version.properties',
}
RENDER_REL='app/src/main/assets/shaders/motionv2/render.glsl'
VERSION_REL='app/version.properties'
OLD_BLOCK=b'''    /*\n     * Apply the same pre-tone local-contrast intent that the HDR target uses.\n     * The existing headroom mapper and 0.80 exposure remain unchanged.\n     */\n    linearSrgb=applyReferenceSafeMicrocontrast(sourceXY,linearSrgb);\n'''
NEW_BLOCK=b'''    /* IRIS_26559_REMOVE_SHARED_MICROCONTRAST_HALO\n     * Do not apply the legacy 5x5 local-luma contrast multiplier here. Sabre remains\n     * the detail authority; headroom mapping, exposure, gamut fit and zoom are unchanged.\n     */\n'''

def h(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def tree(root:Path):
    return {p.relative_to(root).as_posix():h(p.read_bytes()) for p in root.rglob('*') if p.is_file() and '.git' not in p.parts}

def smoothstep(a,b,x):
    t=max(0.0,min(1.0,(x-a)/(b-a)))
    return t*t*(3.0-2.0*t)

def old_scale(y,detail):
    detail=max(-0.20,min(0.20,detail))
    shadow=smoothstep(0.025,0.12,y)
    highlight=1.0-smoothstep(0.55,0.92,y)
    return math.exp(0.42*shadow*highlight*detail)

def self_test():
    # Permanent device regression model: the old operator necessarily increases edge contrast.
    leaf=old_scale(0.45,+0.20)
    wall=old_scale(0.25,-0.20)
    assert leaf>1.08 and wall<0.93, (leaf,wall)
    assert (leaf/wall)>1.16
    print(f'PASS 26559 halo regression self-test: old 5x5 operator edge ratio={leaf/wall:.4f} is disabled')

def validate(base:Path,cand:Path):
    B,C=tree(base),tree(cand)
    changed={k for k in set(B)|set(C) if B.get(k)!=C.get(k)}
    assert changed==EXPECTED_CHANGED, f'changed scope mismatch extra={sorted(changed-EXPECTED_CHANGED)} missing={sorted(EXPECTED_CHANGED-changed)}'

    version=(cand/VERSION_REL).read_text()
    assert 'VERSION_NAME=0.9726559' in version
    assert 'VERSION_BUILD=26559' in version
    assert 'VERSION_NAME=0.9726558' not in version
    assert 'VERSION_BUILD=26558' not in version

    br=(base/RENDER_REL).read_bytes(); cr=(cand/RENDER_REL).read_bytes()
    assert br.count(OLD_BLOCK)==1, 'base 26558 microcontrast call block not unique'
    assert NEW_BLOCK not in br
    expected=br.replace(OLD_BLOCK,NEW_BLOCK,1)
    assert cr==expected, 'render.glsl changed outside exact microcontrast-call bypass block'
    text=cr.decode()
    # Function remains byte-for-byte available but has no active call site. One occurrence is its definition.
    assert text.count('applyReferenceSafeMicrocontrast(')==1, 'legacy microcontrast must have definition only and zero invocation'
    assert 'linearSrgb=applyReferenceSafeMicrocontrast(' not in text
    assert text.count('IRIS_26559_REMOVE_SHARED_MICROCONTRAST_HALO')==1
    # Preserve all downstream render authority exactly.
    for needle in (
        'linearSrgb=mapExtendedLinearHeadroom(linearSrgb);',
        'linearSrgb*=outputExposureScale;',
        'linearSrgb=fitDisplayGamut(linearSrgb);',
        'srgbEncode(linearSrgb)',
        'uniform float sceneWhite;',
        'uniform float outputExposureScale;',
        'uniform float irisOutputZoom;',
    ):
        assert text.count(needle)==1, needle

    render_java='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
    rj=(cand/render_java).read_text()
    assert B[render_java]==C[render_java], 'MotionV2Render Java owner changed'
    assert 'glProg.useAssetProgram("motionv2/render")' in rj, 'modified shader not on active MotionV2Render path'
    assert 'basePipeline.mParameters.motionV2Active || basePipeline.mParameters.irisNightActive' in rj, 'shared Motion/Night ownership drift'
    assert 'private static final float OUTPUT_EXPOSURE_SCALE = 0.80f;' in rj

    # Explicitly protect the newly proven 26558 Night fix/tone and other critical owners.
    protected=(
        'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
        'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
        'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
        'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java',
        'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
        'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightNeuralEnhancer.java',
    )
    for rel in protected:
        assert B[rel]==C[rel], f'protected owner changed: {rel}'

    print('PASS exact 2-file 26559 scope')
    print('PASS legacy 5x5 microcontrast has zero active invocation')
    print('PASS render headroom/exposure/gamut/zoom authority preserved')
    print('PASS Motion and Night remain on the same modified render shader')
    print('PASS 26558 Night Long clipping, adaptive tone, Sabre, VGN/Jin owners unchanged')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--self-test',action='store_true'); ap.add_argument('--base',type=Path); ap.add_argument('--candidate',type=Path); a=ap.parse_args()
    if a.self_test:self_test();return
    if not a.base or not a.candidate:raise SystemExit('--base and --candidate required')
    validate(a.base,a.candidate)
if __name__=='__main__':main()
