#!/usr/bin/env python3
"""v0.5.1 B OFF proof against real 26958 full-source manifest, no 26955 copy."""
import argparse,hashlib,pathlib,re,sys
R=pathlib.Path(__file__).resolve().parent
A=(R/'26959_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def parse(name):
 lines=(R/name).read_text().splitlines()
 a={}
 for line in lines:
  h,p=line.split('  ',1)
  assert p.startswith('app/') and re.fullmatch('[a-f0-9]{64}',h) and p not in a
  a[p]=h
 return a
def verify(payload=False,live=False):
 base=parse('26959_BASE_26958_FULL_APP.sha256');after=parse('26959_EXPECTED_FULL_APP.sha256')
 assert len(base)==len(after)==2055 and len(A)==4 and set(base)==set(after)
 assert {k for k in base if base[k]!=after[k]}==set(A)
 assert set(A)=={'app/src/main/assets/shaders/motionv2/render.glsl', 'app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqCoordinator.cpp','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt','app/version.properties'}
 assert {'app/src/main/assets/shaders/motionv2/gainmap.glsl','app/build.gradle'}<=set(base)
 for name in ('app/src/main/assets/shaders/motionv2/gainmap.glsl','app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag'):
  assert name not in A and base[name]==after[name]
 assert all(not any(x in k for x in ('/vendor/','/jniLibs/','/third_party_','/motionv2/gainmap.glsl','/spektra/','/dng/','/heif/')) for k in A)
 protected=parse('26959_PROTECTED_SOURCE.sha256')
 assert len(protected)==2051 and protected=={k:v for k,v in base.items() if k not in A}
 overlay=R/'handoff_payload_26959'
 for name in A:
  p=overlay/name
  assert p.is_file() and digest(p)==after[name]
 assert {x.relative_to(overlay).as_posix() for x in overlay.rglob('*') if x.is_file()}==set(A)
 native=(R/'26959_NATIVE_RELEASE_ALLOWLIST.txt').read_text().splitlines()
 assert len(native)==4 and all('verified_rawlens26931/jniLibs' in x for x in native)
 if live:
  for name,hash_ in after.items():
   p=R/name
   assert p.is_file() and digest(p)==hash_,f'wrong current compiled candidate {name}'
 print('PASS exact 26959 V2 26958 authority, four Boff/EV/version files, 2051 protected')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--payload',action='store_true');ap.add_argument('--live',action='store_true');args=ap.parse_args()
 verify(args.payload,args.live)
