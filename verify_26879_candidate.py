#!/usr/bin/env python3
"""26879 exact successful compiled 26878 authority, strict five-file candidate."""
from pathlib import Path
import argparse,hashlib,shutil
p=argparse.ArgumentParser();p.add_argument('base',type=Path);p.add_argument('candidate',type=Path);p.add_argument('--transform',action='store_true');p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
a=p.parse_args();P=Path(__file__).resolve().parent;B=a.base.resolve();C=a.candidate.resolve();R=a.root.resolve()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def entries(n):return {p:d for d,p in [l.split('  ',1) for l in (P/n).read_text().splitlines()]}
prior=entries('26879_BASE_26878_FULL_APP.sha256');expected=entries('26879_EXPECTED_CANDIDATE_FULL_APP.sha256');protect=entries('26879_UNCHANGED_PROTECTED.sha256');allow=(P/'26879_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert len(prior)==len(expected)==2001 and len(protect)==1996
assert len(allow)==5 and allow==sorted(set(allow))
assert set(prior)==set(expected)
assert {x for x in prior if prior[x]!=expected[x]}==set(allow)
assert set(protect)=={x for x in prior if prior[x]==expected[x]}
assert set(entries('26879_PRIOR_CHANGED_SHA256.txt'))==set(entries('26879_NEW_CHANGED_SHA256.txt'))==set(allow)
assert all(entries('26879_PRIOR_CHANGED_SHA256.txt')[x]==prior[x] and entries('26879_NEW_CHANGED_SHA256.txt')[x]==expected[x] for x in allow)
assert B!=C and not B.is_relative_to(C) and not C.is_relative_to(B)
def universe(root):
 return {'app/'+x.relative_to(root/'app').as_posix() for x in (root/'app').rglob('*') if x.is_file() and x.relative_to(root/'app').parts[0] not in ('build','.cxx') and '.git' not in x.parts}
assert universe(B)==set(prior),('real successful 26878 unexpected/missing source',len(universe(B)^set(prior)))
for x,d in prior.items():assert sha(B/x)==d,('base SHA mismatch',x)
if a.transform:
 assert (R/'26879_CHANGED_ALLOWLIST.txt').read_text().splitlines()==allow
 for x in allow:
  src=R/'handoff_payload_26879'/x
  assert src.is_file() and sha(src)==expected[x],('handoff payload missing/corrupt',x)
 if C.exists():shutil.rmtree(C)
 shutil.copytree(B,C)
 for x in allow:
  dst=C/x;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/'handoff_payload_26879'/x,dst)
for root,manifest in ((B,prior),(C,expected)):
 assert universe(root)==set(manifest),('actual source universe mismatch',len(universe(root)^set(manifest)))
 for x,d in manifest.items():assert sha(root/x)==d,('candidate hash mismatch',x)
for x,d in protect.items():assert prior[x]==expected[x]==d
assert (C/'app/version.properties').read_text().endswith('VERSION_NAME=0.9726879\nVERSION_BUILD=26879\n')
# Strong semantic gates on exact changed owners and unchanged original preview/native/other modes.
oldhdr=(B/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java').read_text()
hdr=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java').read_text()
assert 'prepareRawrBPublication26856(iris26856BTrue2xRgbPath != null)' in oldhdr
assert 'prepareRawrBPublication26856(iris26856BTrue2xRgbPath != null)' not in hdr
assert 'IRIS_26879_B_50MP_GPU_INTENT_NO_LEGACY_FILE_GATE' in hdr
assert 'processingParameters.prepareRawrBPublication26856(iris26879Requested2x)' in hdr
assert 'iris26879Requested2x != iris26879Gpu2xPresent' in hdr and 'iris26879Requested2x != iris26879GpuGuidePresent' in hdr
assert '26876 B 50MP GPU→private JPEG/R failed; 1x legacy route forbidden' in hdr
shader=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26858BNoiseHighlight.kt').read_text()
assert 'IRIS_26879_NATIVE_B_COLORED_NEON_HUE_GUARD' in shader
assert shader.count('1.0-smoothstep(0.045,0.18,colorStrength)')==2
assert 'smoothstep(0.0,0.25,clippedCoverage)*nearNeutral' in shader
assert 'oRgb=original;return;' in shader
plan=(C/'app/src/main/java/com/unspektrawesome/preview/RawPreviewPlanSelector.kt').read_text()
assert 'IRIS_26879_SPEKTRA_CAPTURE_MATCHED_RAW_FOV' in plan
assert 'RawPreviewPolicy.selectCaptureOutput(eligibleOutputs, candidateFormats)' in plan
assert 'selectedOutput?.let(::listOf)' in plan
mode=(C/'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraModeController.java').read_text()
assert 'RawPreviewQuality.FULL' in mode and 'RawPreviewQuality.LOW,' not in mode
for path in (
 'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
 'app/src/main/java/com/unspektrawesome/capture/FrameGeometrySnapshot.kt',
 'app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt',
 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java',
):assert sha(B/path)==sha(C/path),('26878 runtime owner unexpectedly modified',path)
print('PASS 26879 exact 26878 successful authority 2001 -> 2001, 5 runtime files, 1996 protected, B 50MP + neon + Spektra contracts')
