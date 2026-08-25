#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, shutil, tarfile, tempfile
RUNTIME_FILES=['app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt', 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java', 'app/src/main/assets/shaders/motionv2/mfsr_mgc_covariance.glsl', 'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_contribute_26501.glsl', 'app/src/main/assets/shaders/motionv2/mfsr_bayer_accumulate.glsl']
BASE_SHA={'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt': '36cb37270877956e10f49622e301389e81d43938809ac81a67d38e6de6f415f9', 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java': '0cc1d2c260ec839d7838f3a196a89fff531632337cdf44fc87e2b51471602d03', 'app/src/main/assets/shaders/motionv2/mfsr_mgc_covariance.glsl': '70348541932fbd114f547d8e9ccc81209a72cadab2825f55647eb845001cbac4', 'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_contribute_26501.glsl': '331ab14ff1de663e5678f5095beff5ca915c96a74d02a2e4413906b23442ea6b', 'app/src/main/assets/shaders/motionv2/mfsr_bayer_accumulate.glsl': '40af5a9c0bf3e43ecb5c860b8e0e53c42aaadae3c96c04da7e151aa37dd1ed2b'}
CAND_SHA={'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt': 'ecab8661b725fdd2b5061e617e41db816a5bac46c778945e4f4937c0a2081cd2', 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java': '4ac5e6f7ac946bad1cfaca75b7d729c1c895ddb2c06af3b8c1cb5b89ede86d3c', 'app/src/main/assets/shaders/motionv2/mfsr_mgc_covariance.glsl': '6829d326ed76cc4040d23457b43a179851a0d4bb8c4cbb46875cd9ff98287e9e', 'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_contribute_26501.glsl': '66bc3464de625404119139e8171cf66accac4c79f29f8a3ab44e70cca0558c53', 'app/src/main/assets/shaders/motionv2/mfsr_bayer_accumulate.glsl': '065764d267a857cba217e9f25474f46c37cc4fbb15c62d7be52c2c5698e442e3'}
PAYLOAD="26542_RUNTIME_PAYLOAD.tar.gz"
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify_payload(d):
    p=d/PAYLOAD
    if not p.is_file(): raise RuntimeError("26542 runtime payload missing")
    with tempfile.TemporaryDirectory() as td:
        t=Path(td)
        with tarfile.open(p,"r:gz") as tf: tf.extractall(t)
        actual=sorted(str(x.relative_to(t)) for x in t.rglob("*") if x.is_file())
        if actual!=sorted(RUNTIME_FILES): raise RuntimeError("payload allowlist mismatch: "+repr(actual))
        for rel in RUNTIME_FILES:
            if sha(t/rel)!=CAND_SHA[rel]: raise RuntimeError("payload candidate hash mismatch: "+rel)
def transform(root):
    v=(root/"app/version.properties").read_text()
    if "VERSION_NAME=0.9726541" not in v or "VERSION_BUILD=26541" not in v: raise RuntimeError("not exact successful 26541 source/version baseline")
    for rel in RUNTIME_FILES:
        p=root/rel
        if not p.is_file() or sha(p)!=BASE_SHA[rel]: raise RuntimeError("26541 base runtime hash mismatch: "+rel)
    d=Path(__file__).resolve().parent; verify_payload(d)
    with tempfile.TemporaryDirectory() as td:
        t=Path(td)
        with tarfile.open(d/PAYLOAD,"r:gz") as tf: tf.extractall(t)
        for rel in RUNTIME_FILES:
            dst=root/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(t/rel,dst)
            if sha(dst)!=CAND_SHA[rel]: raise RuntimeError("26542 candidate write hash mismatch: "+rel)
    print("PASS: exact five-file 26542 transform from successful 26541 candidate")
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("root",nargs="?"); ap.add_argument("--self-test",action="store_true"); a=ap.parse_args()
    if a.self_test:
        verify_payload(Path(__file__).resolve().parent)
        if set(BASE_SHA)!=set(RUNTIME_FILES) or set(CAND_SHA)!=set(RUNTIME_FILES): raise RuntimeError("runtime hash maps mismatch")
        print("PASS: 26542 transformer self-test"); return
    if not a.root: ap.error("root required")
    transform(Path(a.root).resolve())
if __name__=="__main__": main()
