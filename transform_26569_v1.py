#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys

EXPECTED = {
    'app/src/main/cpp/motionv2_jpeg444_jni.cpp': ('e6f397e05f413743aaa5f2b1bd2963872ddfd0b5bae1f7941dd6467b53a6ab24', '53cc4bcda8d6fdcd6ba127ce4333ee2dd6ba58b108fd3036c86daceb8e325d7e'),
    'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java': ('780fab8b0c8aea71250a7fc8a38cce900097ef69c28a89d451b8b65fc201e2e5', '5f5f829ede8e76bf6589c14a2d6a6752fcdf432086aa9ebe3ac6e6e3b810f93d'),
    'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java': ('c05582c37bee48db76bf9f7ca2b1ca2a83367a6f1b605318c28785887d3c21d7', '066c077a51cee0ef7adad03b33fccddd90e880bfe5cd1c7d66c32a7139472cce'),
    'app/version.properties': ('d6385dde892fde6ae5822b3a718f49c8b0552865662398abb3588f62c8a8186f', 'f2d694c747673eaab3921dea811086213ffd6afaae6955fa281727b175f54e13'),
}

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fail(m): raise SystemExit('FAIL: '+m)

def main():
    if len(sys.argv)!=2: fail('usage: transform_26569_v1.py CANDIDATE_ROOT')
    root=Path(sys.argv[1]).resolve()
    package=Path(__file__).resolve().parent
    payload=package/'handoff_payload_26569_v1'
    if not (root/'app').is_dir(): fail('candidate app root missing')
    # Exact prior successful 26568 V1.1 source hashes are checked before any runtime write.
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
        tmp=dst.with_name(dst.name+'.iris26569.tmp')
        tmp.write_bytes(src.read_bytes())
        if sha(tmp)!=after: fail('temporary candidate hash mismatch '+rel)
        tmp.replace(dst)
    for rel,(before,after) in EXPECTED.items():
        if sha(root/rel)!=after: fail('final candidate hash mismatch '+rel)
    print(f'PASS deterministic 26569 V1 sealed transform changed_files={len(EXPECTED)}')

if __name__=='__main__': main()
