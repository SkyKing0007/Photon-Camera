#!/usr/bin/env python3
from pathlib import Path
import argparse, tarfile, tempfile
def check(root):
    k=(root/"app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt").read_text()
    if "val expectedNormalDngFrames = inputImages.count" not in k: raise RuntimeError("role-aware NORMAL-count contract missing")
    if "stacked.normalStackedDngFrameCount == expectedNormalDngFrames" not in k: raise RuntimeError("DNG parity contract missing")
    j=(root/"app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java").read_text()
    sig="float wbR, float wbB, float greenNoiseS, float greenNoiseO,\n            float kDetail, float kDenoise, float dTh, float dTr, float kStretch, float kShrink)"
    if sig not in j: raise RuntimeError("Java covariance signature drift")
    if j.count('useAssetProgram("motionv2/mfsr_mgc_covariance", true)')!=3: raise RuntimeError("live covariance dispatch count drift")
    for u in ["kDetail","kDenoise","Dth","Dtr","kStretch","kShrink"]:
        if j.count('setVar("'+u+'"')!=3: raise RuntimeError("every live covariance dispatch must bind "+u)
    if j.count("iris26501RenderRgbCovariance(")!=5: raise RuntimeError("RGB covariance helper/call count drift")
    print("PASS: 26542 Java/Kotlin compile-contract preflight")
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--root"); ap.add_argument("--self-test",action="store_true"); a=ap.parse_args()
    if a.self_test:
        with tempfile.TemporaryDirectory() as td:
            r=Path(td)
            with tarfile.open(Path(__file__).resolve().parent/"26542_RUNTIME_PAYLOAD.tar.gz","r:gz") as tf: tf.extractall(r)
            check(r)
        return
    check(Path(a.root).resolve())
if __name__=="__main__": main()
