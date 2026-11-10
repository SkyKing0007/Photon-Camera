#!/usr/bin/env python3
"""Strict 26918 complete compiled-source scope, B Photo-only bypass and frozen border.
Static source verification never substitutes for actual pinned GLSL or Android build.
"""
from pathlib import Path
import hashlib,re,sys
R=Path(__file__).resolve().parent
LIVE='--live' in sys.argv
ROOT=R if LIVE else R/'handoff_payload_26918'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(name):
 d={}
 for line in (R/name).read_text().splitlines():
  h,k=line.split('  ',1)
  assert re.fullmatch('[0-9a-f]{64}',h) and k.startswith('app/') and '..' not in Path(k).parts and k not in d
  d[k]=h
 return d
before=manifest('26918_BASE_26917_FULL_APP.sha256')
after=manifest('26918_PRECOMPILE_EXPECTED_FULL_APP.sha256')
changed=(R/'26918_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
assert len(before)==len(after)==2036 and before.keys()==after.keys()
assert len(set(changed))==len(changed)==3
assert {p for p in before if before[p]!=after[p]}==set(changed)
assert not (R/'26918_ADDED_RUNTIME_PATHS.txt').read_text().strip()
assert not (R/'26918_DELETED_RUNTIME_PATHS.txt').read_text().strip()
assert len(before)-len(changed)==2033
for p in changed:assert sha(ROOT/p)==after[p],p
if LIVE:
 actual={p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'app/src').rglob('*') if p.is_file()}
 for p in ('app/build.gradle','app/version.properties'):actual[p]=sha(ROOT/p)
 assert actual==after,{'missing':list(after.keys()-actual.keys())[:4],'extra':list(actual.keys()-after.keys())[:4],'wrong':[p for p in after if actual.get(p)!=after[p]][:9]}
# Ensure those exact 26917 native/Java/Kotlin/SPV bytes cannot be accidentally
# replaced by an older non-halo version or new untested source.
border=manifest('26918_FROZEN_26917_BORDER.sha256')
assert len(border)==7 and set(border).isdisjoint(changed)
for p,h in border.items():assert before[p]==after[p]==h,p
if LIVE:
 for p,h in border.items():assert sha(ROOT/p)==h,p
for p in before:
 if p not in changed and any(t in p for t in ('/cpp/','/jniLibs/','/vendor/','/amaze/','preview_hue_match_26907.glsl','MotionV2PreviewHueCalibration.java')):
  assert before[p]==after[p],p
s=(ROOT/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt').read_text()
k=(ROOT/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
assert s.count('uniform int uIris26918BypassSpatialChroma;')==1
assert s.count('if(uIris26918BypassSpatialChroma!=0)')==1
assert k.count('bPhotoSrOffChromaBypass26918 = true')==1
assert k.count('bPhotoSrOffChromaBypass26918: Boolean = false')==1
assert 'if (bPhotoSrOffChromaBypass26918) 1 else 0' in k
assert k.count('uniform1i(applyProgram,"uIris26918BypassSpatialChroma",')==1
assert (ROOT/'app/version.properties').read_text().count('VERSION_BUILD=26918')==1
assert 'VERSION_NAME=0.9726918' in (ROOT/'app/version.properties').read_text()
print('PASS 26918 '+('live' if LIVE else 'payload')+' exact 2036 source/3 changed/2033 protected, frozen 26917 physical CFA edge files')
