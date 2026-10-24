#!/usr/bin/env python3
"""Exact successful 26875 authority-seeded 26876 candidate/protected proof."""
from pathlib import Path
import hashlib,sys
p=Path(__file__).resolve().parent
base=Path(sys.argv[1]); cand=Path(sys.argv[2])
allow=(p/'26876_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert allow==sorted(set(allow)) and len(allow)==3

def file_hash(x):
 h=hashlib.sha256()
 with x.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def entries(x):
 return {name:sha for sha,name in (line.split('  ',1) for line in (p/x).read_text().splitlines())}
prior=entries('26876_BASE_26875_FULL_APP.sha256')
expected=entries('26876_EXPECTED_CANDIDATE_FULL_APP.sha256')
protect=entries('26876_UNCHANGED_PROTECTED.sha256')
assert len(prior)==len(expected)==1997 and len(protect)==1994
assert len(set(prior))==len(set(expected))==1997
assert set(prior)==set(expected) and set(protect)==set(prior)-set(allow)
for root,man in ((base,prior),(cand,expected)):
 universe={'app/'+a.relative_to(root/'app').as_posix() for a in (root/'app').rglob('*') if a.is_file() and not (a.relative_to(root).as_posix().startswith('app/build/') or a.relative_to(root).as_posix().startswith('app/.cxx/') or '.git' in a.parts)}
 assert universe==set(man),f'authority/candidate universe discrepancy missing={set(man)-universe} extra={universe-set(man)}'
 for name,sha in man.items():
  assert file_hash(root/name)==sha,f'full manifest mismatch {name}'
for name,sha in protect.items():
 assert prior[name]==expected[name]==sha,f'protected source changed {name}'
assert {k for k in prior if prior[k]!=expected[k]}==set(allow)
assert (cand/'app/version.properties').read_text().endswith('VERSION_NAME=0.9726876\nVERSION_BUILD=26876\n')
cpp=(cand/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
kt=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
assert 'IRIS_26876_B_ONLY_PARALLEL_SENSOR_CLIP_CORRECTION' in cpp
assert 'const bool iris26876BSource=std::strstr(rp.c,"/iris26864_b_wronski_")!=nullptr;' in cpp
assert 'iris26876B?kIris26876BPublicationCompute:kIris26571PublicationCompute' in cpp
assert 'IRIS_26876_B_SINGLE_WRONSKI_NORMAL' in kt
seg=kt.split('private fun processIris26868DirectB(',1)[1].split('private fun renderIris26868IndependentLongShadowGuide',1)[0]
assert seg.index('if (iris26856BTrue2x) {')<seg.index('iris26856AmazeCfaConsumer)(')
assert seg.count('reconstructIris26864PinnedWronski2x(')==1
assert 'derivedLong26876' in kt and 'retainedNativeClip26876' in kt
print('26876 AUTHORITY-SEEDED CANDIDATE + PROTECTED FILES + ROUTING PASS (1997/1997, protected=1994, changed=3)')
