#!/usr/bin/env python3
"""Exact Photon 26916 source and B Photo-only universal hue semantics.
Does not replace pinned GLSL or full Android compilation in inherited workflow.
"""
from pathlib import Path
import hashlib,re,sys
R=Path(__file__).resolve().parent
LIVE='--live' in sys.argv
ROOT=R if LIVE else R/'handoff_payload_26916'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(p):
 d={}
 for line in p.read_text().splitlines():
  h,k=line.split('  ',1)
  assert re.fullmatch('[a-f0-9]{64}',h) and k not in d and k.startswith('app/') and '..' not in Path(k).parts
  d[k]=h
 return d
before=manifest(R/'26916_BASE_26915_FULL_APP.sha256')
after=manifest(R/'26916_PRECOMPILE_EXPECTED_FULL_APP.sha256')
changed=(R/'26916_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
added=(R/'26916_ADDED_RUNTIME_PATHS.txt').read_text().splitlines()
deleted=(R/'26916_DELETED_RUNTIME_PATHS.txt').read_text().splitlines()
assert len(before)==len(after)==2036
assert len(changed)==len(set(changed))==3 and not added and not deleted
assert before.keys()==after.keys()
assert {p for p in before if before[p]!=after[p]}==set(changed)
assert len(before)-len(changed)==2033
for p in before:
 if p not in changed and p.startswith(('app/src/main/assets/','app/src/main/cpp/','app/src/main/jniLibs/')):assert before[p]==after[p],p
for p in changed:assert (ROOT/p).is_file() and sha(ROOT/p)==after[p],p
if LIVE:
 actual={p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'app/src').rglob('*') if p.is_file()}
 for p in ['app/build.gradle','app/version.properties']:actual[p]=sha(ROOT/p)
 assert actual==after,{'missing':list(after.keys()-actual.keys())[:5],'extra':list(actual.keys()-after.keys())[:5],'wrong':[p for p in after if actual.get(p)!=after[p]][:7]}
shader=(ROOT/'app/src/main/assets/shaders/motionv2/preview_hue_match_26907.glsl').read_text()
j=(ROOT/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2PreviewHueCalibration.java').read_text()
assert shader.count('rotateHueWithoutTone')>=3
assert 'for(int i=0;i<12;i++)' in shader and 'delta*mid' in shader and '0.5*delta' not in shader
assert 'Output=max(result,vec3(0.0));' in shader
assert 'oldY/newY' in shader and 'chroma=length(lab.yz)' in shader
assert 'MAX_HUE_CHANGE = 0.32f' in j
assert 'off=-1;off<=1;off++' in j and 'wrap(median[k]-median[j])' in j
assert (ROOT/'app/version.properties').read_text().count('VERSION_BUILD=26916')==1
assert 'VERSION_NAME=0.9726916' in (ROOT/'app/version.properties').read_text()
print('PASS 26916 '+('live' if LIVE else 'payload')+' complete source: 2036 authority/candidate, exactly three changed, 2033 protected, native/vendor/AMaZE/other SR unchanged')
