#!/usr/bin/env python3
"""Exact 26959 compiled candidate and 26960 B-only source ownership / stale path check."""
import argparse,hashlib,pathlib,re
R=pathlib.Path(__file__).resolve().parent
A=(R/'26960_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
assert len(A)==7 and A==sorted(A)
def hash(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def scan(name):
 d={}
 for line in (R/name).read_text().splitlines():
  h,p=line.split('  ',1)
  assert p.startswith('app/') and re.fullmatch('[a-f0-9]{64}',h) and p not in d
  d[p]=h
 return d
def check(live=False):
 a=scan('26960_BASE_26959_FULL_APP.sha256');b=scan('26960_EXPECTED_FULL_APP.sha256')
 assert len(a)==len(b)==2055 and set(a)==set(b)
 assert {p for p in a if a[p]!=b[p]}==set(A)
 assert len(scan('26960_PROTECTED_SOURCE.sha256'))==2048
 assert scan('26960_PROTECTED_SOURCE.sha256')=={p:h for p,h in a.items() if p not in A}
 assert not (R/'26960_ADDED_RUNTIME_PATHS.txt').read_text().strip()
 assert not (R/'26960_DELETED_RUNTIME_PATHS.txt').read_text().strip()
 for rel in A:
  assert hash(R/'handoff_payload_26960'/rel)==b[rel],rel
 assert {p.relative_to(R/'handoff_payload_26960').as_posix() for p in (R/'handoff_payload_26960').rglob('*') if p.is_file()}==set(A)
 assert not any(x in p.lower() for p in A for x in ('/vendor/','/spektra/','/dng/','/jniLibs/','/libheif/','/lkrpipeline/'))
 # Probe bit-identical protected visual and pipeline owners, including the
 # already successful sky/border repair, vendor, native and the real UHDR shader.
 for p in ('app/src/main/cpp/iris26864/bridge/Iris26943BOffHdrqBorder.comp',
           'app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqMismatch.comp',
           'app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqMerge.comp',
           'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
           'app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag'):
  assert p not in A and a[p]==b[p],p
 for p in ('app/src/main/assets/shaders/motionv2/render.glsl',
           'app/src/main/assets/shaders/motionv2/gainmap.glsl'):
  s=(R/'handoff_payload_26960'/p).read_text()
  assert s.count('float iris26960BOffSdrColorSpacing(')==1
  assert 'iris26954BOffNight26940Sdr' in s
  assert 'if(iris26941BOffHdrqLowZoom!=0)' in s
  code=re.sub(r'/\*.*?\*/|//[^\n]*',' ',s,flags=re.S)
  assert not re.search(r'\b(?:float|int|uint|vec[234]|mat[234]|bool)\s+(?:coherent|flat|in|out|varying|attribute|uniform|buffer|precision|shared|layout|sample|switch|class|atomic_uint)\b',code),p
  assert code.count('void main()')==1

 if live:
  for p,digest in b.items():
   f=R/p
   assert f.is_file() and hash(f)==digest,p
 print('PASS 26960 2055 actual-26959-derived candidate, seven allowlisted, 2048 protected, sky/native/UHDR owners preserved')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--payload',action='store_true');ap.add_argument('--live',action='store_true');args=ap.parse_args();check(args.live)
