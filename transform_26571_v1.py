#!/usr/bin/env python3
from pathlib import Path
import hashlib,shutil,sys
CHANGED=[
'app/src/main/cpp/CMakeLists.txt',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/version.properties']

def fail(m): raise SystemExit('FAIL: '+m)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read_manifest(p):
    out={}
    for line in p.read_text().splitlines():
        if line.strip():
            h,rel=line.split('  ',1);out[rel]=h
    return out
def main():
    if len(sys.argv)!=3:fail('usage base candidate')
    base,cand=map(Path,sys.argv[1:]);root=Path(__file__).resolve().parent
    pre=read_manifest(root/'V1_26571_PREWRITE_SOURCE_HASHES.sha256')
    exp=read_manifest(root/'V1_26571_EXPECTED_CHANGED_SOURCE_HASHES.sha256')
    payload=root/'handoff_payload_26571_v1'
    if set(pre)!=set(CHANGED) or set(exp)!=set(CHANGED):fail('changed manifest set')
    for rel in CHANGED:
        p=base/rel
        if not p.is_file() or sha(p)!=pre[rel]:fail('prior source authority '+rel)
        src=payload/rel
        if not src.is_file() or sha(src)!=exp[rel]:fail('sealed payload '+rel)
    if cand.exists():shutil.rmtree(cand)
    shutil.copytree(base,cand)
    for rel in CHANGED:
        dst=cand/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(payload/rel,dst)
        if sha(dst)!=exp[rel]:fail('candidate write '+rel)
    print('PASS deterministic candidate transform from exact 26570 authority')
    print('PASS exact 4-file runtime payload applied candidate-first')
if __name__=='__main__':main()
