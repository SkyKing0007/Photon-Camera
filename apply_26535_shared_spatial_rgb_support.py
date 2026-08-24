#!/usr/bin/env python3
from __future__ import annotations
import argparse, shutil
from pathlib import Path

FILES = [
'app/src/main/assets/shaders/motionv2/highlight_chroma_reliability.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2HighlightChromaReliability.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2MgcSourceExposure.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
]

def fail(m): raise SystemExit('FAIL: '+m)
def req(c,m):
    if not c: fail(m)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root',nargs='?'); ap.add_argument('--overlay'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args()
    req(len(FILES)==len(set(FILES))==8,'runtime allowlist must contain exactly 8 unique files')
    if a.self_test:
        print('PASS: 26535 overlay transform self-test'); return
    req(a.root is not None,'candidate root required')
    root=Path(a.root)
    overlay=Path(a.overlay) if a.overlay else Path(__file__).resolve().parent/'26535_runtime_overlay'
    req((root/'app/src/main').is_dir(),'candidate missing app/src/main')
    vp=root/'app/version.properties'; req(vp.is_file(),'base version.properties missing')
    vs=vp.read_text(); req('VERSION_NAME=0.9726534' in vs and 'VERSION_BUILD=26534' in vs,
                           'transform requires exact successful 26534 preversion base')
    present=sorted(str(p.relative_to(overlay)) for p in overlay.rglob('*') if p.is_file())
    req(present==sorted(FILES),f'overlay allowlist mismatch: {present}')
    for rel in FILES:
        src=overlay/rel; dst=root/rel
        if rel not in FILES[:2]: req(dst.is_file(),'expected existing base file missing '+rel)
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(src,dst)
    h=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java').read_text()
    req('IRIS_26535_NIGHT_SHARED_SPATIAL_RGB_SOLE_OWNER' in h,'Night shared RGB marker absent after transform')
    print('PASS: 26535 exact 8-file runtime overlay applied')

if __name__=='__main__': main()
