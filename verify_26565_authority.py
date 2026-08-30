#!/usr/bin/env python3
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse, hashlib, sys

CHANGED=[
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/UltraHdrSaver.java',
'app/version.properties',
]
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
    return h.hexdigest()
def rels_audited(root):
    root=Path(root); out=[]
    for p in (root/'app/src/main').rglob('*'):
        if not p.is_file(): continue
        r=p.relative_to(root).as_posix()
        if r.startswith('app/src/main/cpp/third_party_26507/') or r.startswith('app/src/main/cpp/deps/'): continue
        out.append(r)
    gi=root/'app/src/main/cpp/deps/.gitignore'
    if gi.is_file(): out.append(gi.relative_to(root).as_posix())
    out+=['app/version.properties','app/build.gradle']; return sorted(set(out))
def rels_vendor(root):
    root=Path(root); out=[]
    for b in ('app/src/main/cpp/third_party_26507','app/src/main/cpp/deps'):
        p=root/b
        if p.is_dir(): out += [x.relative_to(root).as_posix() for x in p.rglob('*') if x.is_file()]
    return sorted(out)
def bytes_manifest(root,rels):
    root=Path(root)
    def one(r): return f'{sha(root/r)}  {r}'
    with ThreadPoolExecutor(max_workers=32) as pool: lines=list(pool.map(one,rels))
    return ('\n'.join(lines)+'\n').encode()
def parse(p):
    out=[]
    for line in Path(p).read_text().splitlines():
        if line.strip(): out.append(tuple(line.split('  ',1)))
    return out
def tree(root):
    root=Path(root); ps=sorted(p for p in (root/'app').rglob('*') if p.is_file())
    def one(p): return p.relative_to(root).as_posix(),sha(p)
    with ThreadPoolExecutor(max_workers=32) as pool: return dict(pool.map(one,ps))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('base'); ap.add_argument('candidate',nargs='?'); ap.add_argument('package'); ap.add_argument('--successful-artifact-manifest'); ap.add_argument('--successful-vendor-manifest'); ap.add_argument('--base-only',action='store_true')
    a=ap.parse_args(); base=Path(a.base); pkg=Path(a.package)
    ba=bytes_manifest(base,rels_audited(base)); bv=bytes_manifest(base,rels_vendor(base))
    assert ba==(pkg/'V1_26565_BASE_26564_V1_4_AUDITED_RUNTIME.sha256').read_bytes(),'base audited manifest mismatch'
    assert bv==(pkg/'V1_26565_NATIVE_VENDOR_DEPENDENCIES.sha256').read_bytes(),'base vendor manifest mismatch'
    assert len(ba.splitlines())==930 and len(bv.splitlines())==778,'base manifest completeness count mismatch'
    if a.successful_artifact_manifest:
        assert ba==Path(a.successful_artifact_manifest).read_bytes(),'base differs from persisted successful 26564 artifact proof'
    if a.successful_vendor_manifest:
        assert bv==Path(a.successful_vendor_manifest).read_bytes(),'base vendor differs from persisted successful 26564 artifact proof'
    bt=tree(base); assert len(bt)==1707,'base full app file-count mismatch'
    pre=parse(pkg/'V1_26565_PREWRITE_SOURCE_HASHES.sha256'); assert [r for _,r in pre]==CHANGED,'prewrite inventory mismatch'
    for h,r in pre: assert bt.get(r)==h,'prewrite hash mismatch '+r
    if a.base_only:
        print('PASS exact successful 26564 base authority: audited=930 vendor=778 app=1707 prewrite=6')
        return
    if not a.candidate: raise SystemExit('candidate required unless --base-only')
    cand=Path(a.candidate); ca=bytes_manifest(cand,rels_audited(cand)); vv=bytes_manifest(cand,rels_vendor(cand))
    assert ca==(pkg/'V1_26565_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256').read_bytes(),'candidate audited manifest mismatch'
    assert vv==(pkg/'V1_26565_NATIVE_VENDOR_DEPENDENCIES.sha256').read_bytes(),'candidate vendor manifest mismatch'
    assert len(ca.splitlines())==930 and len(vv.splitlines())==778,'candidate manifest completeness count mismatch'
    ct=tree(cand); diff=sorted(k for k in set(bt)|set(ct) if bt.get(k)!=ct.get(k))
    assert diff==CHANGED, f'exact changed scope mismatch: {diff}'
    post=parse(pkg/'V1_26565_CANDIDATE_CHANGED_HASHES.sha256')
    assert [r for _,r in post]==CHANGED,'candidate changed hash inventory mismatch'
    for h,r in post: assert ct.get(r)==h, 'candidate changed hash mismatch '+r
    assert len(bt)==1707 and len(ct)==1707,'full app file-count mismatch'
    print('PASS exact 26564 authority + 26565 candidate manifests: audited=930 vendor=778 app=1707 changed=6')
if __name__=='__main__': main()
