#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys

EXPECTED = {
    'app/src/main/cpp/motionv2_jpeg444_jni.cpp': ('2b244e054f8cb0bf99cc89a01f056e36a494f1559652e1ca5678397a42393f98', 'e6f397e05f413743aaa5f2b1bd2963872ddfd0b5bae1f7941dd6467b53a6ab24'),
    'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt': ('293089e316183980e178dfb42c7dc1d9ebf4de891aff03e2f2bdd34322e9babd', '6b7d49ab6a552249a90f87879d34075fb93ee33631a07033bc003fcf0826f1b5'),
    'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt': ('a7743c18bf25fa2a5758b570288951c7654a317e7ec7f1131ee9bc32bce6e89e', '3ceb550ed03e9974597b743371c3138686e23d15395558fdf36acf2dbd2bb075'),
    'app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt': ('0faec0868416fd8fee2902be102f1f273cb93ae96798e0f2b8b0503cde3df532', 'cdecb5376d435ea80a694d51eba2f7d26d39796a6a97d61770e0300057fc977b'),
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt': ('ce337ea8ab58443c3e05a6a34fd2820f95102fdf4d75852b841d3e5d78c83c0b', '9374cc92223643cd44ed1eb2224c59d19d98d6b52fdb8b6d5f424b892280a476'),
    'app/version.properties': ('01cd38823c2571f74a97ec04ba9bad8ce20ccde89da01c6b7182d75f6cea8d0e', 'd6385dde892fde6ae5822b3a718f49c8b0552865662398abb3588f62c8a8186f'),
}

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fail(m): raise SystemExit('FAIL: '+m)

def main():
    if len(sys.argv)!=2: fail('usage: transform_26568_v1_1.py CANDIDATE_ROOT')
    root=Path(sys.argv[1]).resolve()
    package=Path(__file__).resolve().parent
    payload=package/'handoff_payload_26568_v1_1'
    if not (root/'app').is_dir(): fail('candidate app root missing')
    # Exact prior hashes are checked before any runtime write.
    for rel,(before,after) in EXPECTED.items():
        p=root/rel
        if not p.is_file(): fail('missing prior source '+rel)
        got=sha(p)
        if got!=before: fail(f'prior source hash mismatch {rel}: {got} != {before}')
        q=payload/rel
        if not q.is_file(): fail('sealed payload missing '+rel)
        if sha(q)!=after: fail('sealed payload candidate hash mismatch '+rel)
    # Candidate-first deterministic replacement from sealed exact bytes.
    for rel,(before,after) in EXPECTED.items():
        src=payload/rel; dst=root/rel
        dst.parent.mkdir(parents=True,exist_ok=True)
        data=src.read_bytes()
        tmp=dst.with_name(dst.name+'.iris26568.tmp')
        tmp.write_bytes(data)
        if sha(tmp)!=after: fail('temporary candidate hash mismatch '+rel)
        tmp.replace(dst)
    for rel,(before,after) in EXPECTED.items():
        if sha(root/rel)!=after: fail('final candidate hash mismatch '+rel)
    print(f'PASS deterministic 26568 V1.1 sealed transform changed_files={len(EXPECTED)}')

if __name__=='__main__': main()
