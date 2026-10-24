#!/usr/bin/env python3
"""26877 exact 26876 successful compiled-candidate source authority; strict all-file proof."""
import hashlib,re,sys,shutil,argparse
from pathlib import Path
P=Path(__file__).resolve().parent
p=argparse.ArgumentParser()
p.add_argument('base',type=Path);p.add_argument('candidate',type=Path)
p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
p.add_argument('--transform',action='store_true')
a=p.parse_args()
base=a.base.resolve();cand=a.candidate.resolve();source=a.root.resolve()
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def entries(path):return {f:sha for sha,f in (line.split('  ',1) for line in (P/path).read_text().splitlines())}
prior=entries('26877_BASE_26876_FULL_APP.sha256')
expected=entries('26877_EXPECTED_CANDIDATE_FULL_APP.sha256')
protect=entries('26877_UNCHANGED_PROTECTED.sha256')
allow=(P/'26877_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert len(prior)==2001 and len(expected)==2001 and len(protect)==1997
assert len(allow)==4 and allow==sorted(set(allow))
assert set(protect)=={k for k in prior.keys()&expected.keys() if prior[k]==expected[k]}
assert set(allow)=={k for k in prior.keys()|expected.keys() if prior.get(k)!=expected.get(k)}
# IRIS_26877_PRESERVE_ACTIONS_40115605739: inherited guard invokes
# --transform; source verification alone must never silently skip reconstruction.
assert base!=cand and not base.is_relative_to(cand) and not cand.is_relative_to(base)
assert (base/'app').is_dir(), '26876 authority source app missing'
baseuniverse={'app/'+f.relative_to(base/'app').as_posix() for f in (base/'app').rglob('*') if f.is_file() and f.relative_to(base/'app').parts[0] not in ('build','.cxx') and '.git' not in f.parts}
assert baseuniverse==set(prior),'prior successful artifact universe mismatch before candidate writes'
for name,digest in prior.items():assert sha(base/name)==digest,('prior authority sha',name)
old=entries('26877_PRIOR_CHANGED_SHA256.txt')
new=entries('26877_NEW_CHANGED_SHA256.txt')
assert set(old)==set(allow)&set(prior) and set(new)==set(allow) and all(prior[x]==old[x] for x in old) and all(expected[x]==new[x] for x in new)
if a.transform:
 assert (source/'26877_CHANGED_ALLOWLIST.txt').is_file(),'missing intended handoff source domain'
 assert (source/'26877_CHANGED_ALLOWLIST.txt').read_text().splitlines()==allow,'handoff source allowlist drift'
 for name in allow:
  incoming=source/'handoff_payload_26877'/name
  assert incoming.is_file() and sha(incoming)==new[name],('payload integrity',name)
 if cand.exists():shutil.rmtree(cand)
 shutil.copytree(base,cand)
 for name in allow:
  incoming=source/'handoff_payload_26877'/name
  dst=cand/name;dst.parent.mkdir(parents=True,exist_ok=True)
  shutil.copyfile(incoming,dst)
for root,man in ((base,prior),(cand,expected)):
 universe={'app/'+f.relative_to(root/'app').as_posix() for f in (root/'app').rglob('*') if f.is_file() and f.relative_to(root/'app').parts[0] not in ('build','.cxx') and '.git' not in f.parts}
 assert universe==set(man),f'full source file-universe discrepancy missing={set(man)-universe} extra={universe-set(man)}'
 for name,digest in man.items():assert sha(root/name)==digest,('file SHA',name)
for k,h in protect.items():assert prior[k]==expected[k]==h,k
assert (cand/'app/version.properties').read_text().endswith('VERSION_NAME=0.9726877\nVERSION_BUILD=26877\n')
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
# Permanent real device regression: 26876 Wronski 2x survived GPU merge but
# detached the 1x guide before copyPersistentTexture checked textureSpecs.
# The exact failing prior source must reproduce this case; the corrected one
# must preserve registration until bridge copy and release atomically.
from importlib.util import spec_from_file_location, module_from_spec
reg=source/'regressions/26877_runtime_ownership_spektra.py'
assert reg.is_file(), 'missing B/Spektra ownership regression'
assert hashlib.sha256(reg.read_bytes()).hexdigest() == hashlib.sha256((P/'regressions/26877_runtime_ownership_spektra.py').read_bytes()).hexdigest()
print('PASS exact 26876 successful compiled authority 2001 -> 26877 2001; 4 changed; 1997 protected; version and inherited B/RAW ownership')
