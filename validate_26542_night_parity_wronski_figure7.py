#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, tarfile, tempfile
RUNTIME_FILES=['app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt', 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java', 'app/src/main/assets/shaders/motionv2/mfsr_mgc_covariance.glsl', 'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_contribute_26501.glsl', 'app/src/main/assets/shaders/motionv2/mfsr_bayer_accumulate.glsl']
CAND_SHA={'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt': 'ecab8661b725fdd2b5061e617e41db816a5bac46c778945e4f4937c0a2081cd2', 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java': '4ac5e6f7ac946bad1cfaca75b7d729c1c895ddb2c06af3b8c1cb5b89ede86d3c', 'app/src/main/assets/shaders/motionv2/mfsr_mgc_covariance.glsl': '6829d326ed76cc4040d23457b43a179851a0d4bb8c4cbb46875cd9ff98287e9e', 'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_contribute_26501.glsl': '66bc3464de625404119139e8171cf66accac4c79f29f8a3ab44e70cca0558c53', 'app/src/main/assets/shaders/motionv2/mfsr_bayer_accumulate.glsl': '065764d267a857cba217e9f25474f46c37cc4fbb15c62d7be52c2c5698e442e3'}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fail(m): raise RuntimeError(m)
def changed(b,c):
    def m(r): return {str(p.relative_to(r)):sha(p) for p in (r/"app/src/main").rglob("*") if p.is_file()}
    x,y=m(b),m(c); return sorted(k for k in set(x)|set(y) if x.get(k)!=y.get(k))
def core(c):
    for rel in RUNTIME_FILES:
        if not (c/rel).is_file() or sha(c/rel)!=CAND_SHA[rel]: fail("candidate hash mismatch: "+rel)
    k=(c/"app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt").read_text()
    for x in ["IRIS_26542_ROLE_AWARE_NORMAL_DNG_PARITY","val expectedNormalDngFrames = inputImages.count","stacked.normalStackedDngFrameCount == expectedNormalDngFrames","normalStackedDngNoiseEquivalentSupport <= expectedNormalDngFrames.toFloat() + 0.01f"]:
        if x not in k: fail("Night parity contract missing: "+x)
    if "stacked.normalStackedDngFrameCount == inputImages.size" in k: fail("stale total-input DNG parity survived")
    j=(c/"app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java").read_text()
    if j.count('useAssetProgram("motionv2/mfsr_mgc_covariance", true)')!=3: fail("unexpected live covariance dispatch count")
    for u in ["kDetail","kDenoise","Dth","Dtr","kStretch","kShrink"]:
        if j.count('setVar("'+u+'"')!=3: fail("not every live covariance dispatch binds "+u)
    if j.count("iris26501RenderRgbCovariance(")!=5: fail("unexpected RGB covariance helper/call count")
    for x in ["kernelLaw=IPOL_FIGURE7_LINEAR","spatialGaussian=EXP_NEG_HALF_D"]:
        if x not in j: fail("Figure-7 runtime log marker missing: "+x)
    s=(c/"app/src/main/assets/shaders/motionv2/mfsr_mgc_covariance.glsl").read_text()
    for x in ["IRIS_26542_IPOL_FIGURE7_ACTIVE_KERNEL","float A=1.0+sqrt","float D=clamp(1.0-sqrt","0.5*A*(1.0/max(kShrink,1.0e-8)-1.0)","0.5*A*(kStretch-1.0)","float greyVst","vec2 publicGrad","mat2 P=mat2(yy,-xy,-xy,xx)/det"]:
        if x not in s: fail("published-law covariance anchor missing: "+x)
    for stale in ["anisotropic=mix(4.0,6.0","correctedGreenStd","dominant=max(strength"]:
        if stale in s: fail("old MGC covariance law survived: "+stale)
    q=(c/"app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_contribute_26501.glsl").read_text()
    if "IRIS_26542_IPOL_FIGURE7_GAUSSIAN" not in q or "return exp(-0.5*d);" not in q: fail("Spatial-RGB IPOL Gaussian missing")
    if "exp2(-0.5*d)" in q or "return exp(-0.5*d)+0.00005" in q: fail("stale Spatial-RGB Gaussian/floor survived")
    b=(c/"app/src/main/assets/shaders/motionv2/mfsr_bayer_accumulate.glsl").read_text()
    if "IRIS_26542_IPOL_FIGURE7_BAYER_GAUSSIAN" not in b or "return exp(-0.5 * distance);" not in b: fail("Bayer/support IPOL Gaussian missing")
    if "exp2(-0.5 * distance)" in b or "+ 0.00005" in b: fail("stale Bayer Gaussian/floor survived")
def architecture(c):
    n=(c/"app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightFrameSelector.java").read_text()
    if not all(x in n for x in ["SHORT_FRAMES = 12","LONG_FRAMES = 3","TOTAL_FRAMES = SHORT_FRAMES + LONG_FRAMES"]): fail("Night 12+3 policy drift")
    cap=(c/"app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java").read_text()
    if not all(x in cap for x in ["IRIS_26541_NIGHT_SHORT_TAG","IRIS_26541_NIGHT_LONG_TAG","zsl=false"]): fail("Night fresh capture ownership drift")
    e=(c/"app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightExposureSelector.java").read_text()
    if "freshPostShutter=true" not in e or "zsl=false" not in e: fail("Night exposure ownership drift")
    hi=(c/"app/src/main/assets/shaders/motionv2/highlight_chroma_reliability.glsl").read_text()
    if "if(centerClipGate<=0.0){ Output=c; return; }" not in hi: fail("26541 non-clipped highlight no-op lost")
    br=(c/"app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt").read_text()
    if "val lumaScale = 0f" not in br: fail("zero-MGC-luma rollback lost")
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--base"); ap.add_argument("--candidate"); ap.add_argument("--postbuild",action="store_true"); ap.add_argument("--self-test",action="store_true"); a=ap.parse_args()
    if a.self_test:
        d=Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory() as td:
            t=Path(td)
            with tarfile.open(d/"26542_RUNTIME_PAYLOAD.tar.gz","r:gz") as tf: tf.extractall(t)
            core(t)
        print("PASS: 26542 validator self-test"); return
    b=Path(a.base).resolve(); c=Path(a.candidate).resolve()
    ch=changed(b,c)
    if ch!=sorted(RUNTIME_FILES): fail("26542 changed-file allowlist mismatch: "+repr(ch))
    v=(c/"app/version.properties").read_text()
    if a.postbuild:
        if "VERSION_NAME=0.9726542" not in v or "VERSION_BUILD=26542" not in v: fail("postbuild version drift")
    else:
        if "VERSION_NAME=0.9726541" not in v or "VERSION_BUILD=26541" not in v: fail("preversion candidate changed version too early")
    core(c); architecture(c)
    print("PASS: 26542 architecture validation: role-aware Night DNG + exact active IPOL Figure-7 kernel; protected 26541 owners intact")
if __name__=="__main__": main()
