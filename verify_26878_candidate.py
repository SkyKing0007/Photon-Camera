#!/usr/bin/env python3
"""26878 exact successful compiled 26877 authority, strict five-file candidate."""
from pathlib import Path
import argparse,hashlib,shutil
p=argparse.ArgumentParser();p.add_argument('base',type=Path);p.add_argument('candidate',type=Path);p.add_argument('--transform',action='store_true');p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
a=p.parse_args();P=Path(__file__).resolve().parent;B=a.base.resolve();C=a.candidate.resolve();R=a.root.resolve()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def entries(n):return {p:d for d,p in [l.split('  ',1) for l in (P/n).read_text().splitlines()]}
prior=entries('26878_BASE_26877_FULL_APP.sha256');expected=entries('26878_EXPECTED_CANDIDATE_FULL_APP.sha256');protect=entries('26878_UNCHANGED_PROTECTED.sha256');allow=(P/'26878_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert len(prior)==len(expected)==2001 and len(protect)==1996
assert len(allow)==5 and allow==sorted(set(allow))
assert set(prior)==set(expected)
assert {x for x in prior if prior[x]!=expected[x]}==set(allow)
assert set(protect)=={x for x in prior if prior[x]==expected[x]}
assert set(entries('26878_PRIOR_CHANGED_SHA256.txt'))==set(entries('26878_NEW_CHANGED_SHA256.txt'))==set(allow)
assert all(entries('26878_PRIOR_CHANGED_SHA256.txt')[x]==prior[x] and entries('26878_NEW_CHANGED_SHA256.txt')[x]==expected[x] for x in allow)
assert B!=C and not B.is_relative_to(C) and not C.is_relative_to(B)
def universe(root):
 return {'app/'+x.relative_to(root/'app').as_posix() for x in (root/'app').rglob('*') if x.is_file() and x.relative_to(root/'app').parts[0] not in ('build','.cxx') and '.git' not in x.parts}
assert universe(B)==set(prior),('real successful 26877 unexpected/missing source',len(universe(B)^set(prior)))
for x,d in prior.items():assert sha(B/x)==d,('base SHA mismatch',x)
if a.transform:
 assert (R/'26878_CHANGED_ALLOWLIST.txt').read_text().splitlines()==allow
 for x in allow:
  src=R/'handoff_payload_26878'/x
  assert src.is_file() and sha(src)==expected[x],('handoff payload missing/corrupt',x)
 if C.exists():shutil.rmtree(C)
 shutil.copytree(B,C)
 for x in allow:
  dst=C/x;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/'handoff_payload_26878'/x,dst)
for root,manifest in ((B,prior),(C,expected)):
 assert universe(root)==set(manifest),('actual source universe mismatch',len(universe(root)^set(manifest)))
 for x,d in manifest.items():assert sha(root/x)==d,('candidate hash mismatch',x)
for x,d in protect.items():assert prior[x]==expected[x]==d
assert (C/'app/version.properties').read_text().endswith('VERSION_NAME=0.9726878\nVERSION_BUILD=26878\n')
g=(C/'app/src/main/java/com/unspektrawesome/capture/FrameGeometrySnapshot.kt').read_text()
assert g.count('fun createFullActivePreview(')==1 and 'sourceCrop = normalizedActive' in g.split('fun createFullActivePreview(',1)[1].split('fun create(',1)[0]
r=(C/'app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt').read_text()
assert r.count('FrameGeometrySnapshot.createFullActivePreview(')==1 and 'FrameGeometrySnapshot.createFullFrameStill(' in r
assert 'IRIS_26878_SPEKTRA_SURFACE_EXTENT_REFRESH' in r and 'renderer.setSurface(null)' in r and 'renderer.setSurface(surface)' in r
bridge=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
assert 'IRIS_26878_B_FINAL_1X_GUIDE_NO_SECOND_EGL_RENDER' in bridge and 'packIris26876BFinalGuide(' in bridge
assert 'iris26876B2xForCleanup = stackB26856.iris26876B2xGpuPacked' in bridge
assert '1x RGB/clip direct EGLImage GPU render failed' not in bridge
saver=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java').read_text()
section=saver.split('public static boolean saveB26876SuperResGpuJpeg(',1)[1].split('public static boolean saveBitmapAsJPGMotionV2(',1)[0]
assert section.index('exif.saveAttributes();')<section.index('published=true;')
assert 'IRIS_26878_B_JPEG_EXIF_COMPLETION_OWNERSHIP' in section
print('PASS 26878 exact 26877 authority 2001 -> 2001, five runtime changes, 1996 protected, 5 owner/quality contracts')
