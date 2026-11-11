#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
R=Path(__file__).resolve().parent
LIVE='--live' in sys.argv
ROOT=R if LIVE else R/'handoff_payload_26919'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(path):
 d={}
 for line in (R/path).read_text().splitlines():
  h,k=line.split('  ',1)
  assert re.fullmatch('[0-9a-f]{64}',h) and k.startswith('app/') and '..' not in Path(k).parts and k not in d
  d[k]=h
 return d
before=manifest('26919_BASE_26918_FULL_APP.sha256')
after=manifest('26919_PRECOMPILE_EXPECTED_FULL_APP.sha256')
change=(R/'26919_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
expected={'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26856RawrFalseColor.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/version.properties'}
assert len(before)==len(after)==2036 and before.keys()==after.keys()
assert len(change)==len(set(change))==3 and set(change)==expected
assert {p for p in before if before[p]!=after[p]}==expected
for p in change: assert sha(ROOT/p)==after[p],p
for name in ('26919_ADDED_RUNTIME_PATHS.txt','26919_DELETED_RUNTIME_PATHS.txt'):
 assert not (R/name).read_text().strip()
assert before['app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt']==after['app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt']
frozen=manifest('26919_FROZEN_26917_BORDER.sha256')
assert len(frozen)==7
for p,h in frozen.items(): assert before[p]==after[p]==h
for p in before:
 if p not in change and p.startswith(('app/src/main/cpp/','app/src/main/assets/','app/src/main/jniLibs/')): assert before[p]==after[p],p
if LIVE:
 actual={p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'app/src').rglob('*') if p.is_file()}
 actual['app/build.gradle']=sha(ROOT/'app/build.gradle');actual['app/version.properties']=sha(ROOT/'app/version.properties')
 assert actual==after,{'missing':list(after.keys()-actual.keys())[:4],'extra':list(actual.keys()-after.keys())[:4],'wrong':[p for p in after if after[p]!=actual.get(p)][:4]}
assert 'VERSION_BUILD=26919' in (ROOT/'app/version.properties').read_text()
assert 'VERSION_NAME=0.9726919' in (ROOT/'app/version.properties').read_text()
print('PASS 26919 '+('LIVE' if LIVE else 'payload')+' 2036 source files, exactly 3 changed, 2033 protected, 7 border shaders/native/bridge frozen, original smooth-white WB unchanged')
