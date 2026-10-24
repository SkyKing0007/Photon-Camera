#!/usr/bin/env python3
"""26876 exact 26875 successful compiled-candidate source authority; strict all-file proof."""
import hashlib,re,sys
from pathlib import Path
P=Path(__file__).resolve().parent
base=Path(sys.argv[1]);cand=Path(sys.argv[2])
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def entries(path):return {f:sha for sha,f in (line.split('  ',1) for line in (P/path).read_text().splitlines())}
prior=entries('26876_BASE_26875_FULL_APP.sha256')
expected=entries('26876_EXPECTED_CANDIDATE_FULL_APP.sha256')
protect=entries('26876_UNCHANGED_PROTECTED.sha256')
allow=(P/'26876_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert len(prior)==1997 and len(expected)==2001 and len(protect)==1985
assert len(allow)==16 and allow==sorted(set(allow))
assert set(protect)=={k for k in prior.keys()&expected.keys() if prior[k]==expected[k]}
assert set(allow)=={k for k in prior.keys()|expected.keys() if prior.get(k)!=expected.get(k)}
for root,man in ((base,prior),(cand,expected)):
 universe={'app/'+f.relative_to(root/'app').as_posix() for f in (root/'app').rglob('*') if f.is_file() and f.relative_to(root/'app').parts[0] not in ('build','.cxx') and '.git' not in f.parts}
 assert universe==set(man),f'full source file-universe discrepancy missing={set(man)-universe} extra={universe-set(man)}'
 for name,digest in man.items():assert sha(root/name)==digest,('file SHA',name)
for k,h in protect.items():assert prior[k]==expected[k]==h,k
assert (cand/'app/version.properties').read_text().endswith('VERSION_NAME=0.9726876\nVERSION_BUILD=26876\n')
k=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
seg=k.split('private fun processIris26868DirectB(',1)[1].split('private fun renderIris26868IndependentLongShadowGuide(',1)[0]
assert seg.count('reconstructIris26876B2xGpu(')==1
assert seg.count('nativeClip = checkNotNull(iris26856AmazeCfaConsumer)(')==1
assert seg.index('if (iris26856BTrue2x) {')<seg.index('} else {\n                nativeRgb = createTexture(')
assert 'IRIS_26876_SINGLE_NATIVE_WRONSKI_NO_DUPLICATE_HDRQ' in k
assert 'guideOwner' not in k[k.index('private fun reconstructIris26876B2xGpu('):k.index('private fun readIris26864WronskiStripe(')]
bridge=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
assert 'iris26876B1xForCleanup = packIris26876BFinalGuide(' in bridge
assert 'iris26876B2xForCleanup = stackB26856.iris26876B2xGpuPacked' in bridge
hdr=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java').read_text()
assert 'saveB26876SuperResGpuJpeg(' in hdr and 'saveB26876SuperResGpuHeic(' in hdr
codec=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java').read_text()
assert 'Iris26876BGpuFinalRenderer.render(' in codec and 'writeB26876True2xGpu' in codec
cpp=(cand/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
assert 'packWronskiRgbAndClipNative26876' in cpp and 'Iris26876BGlAhbBinding_bindNative' in cpp
print('PASS exact 26875 compiled authority 1997 -> 26876 2001; 16 changed; 1985 byte-protected; source ownership and version')
