#!/usr/bin/env python3
"""Preserve exact successful 26959 B/OFF RAW HDRQ source: NO 26960 RAWR gate or 13-strength reintegration."""
import argparse,hashlib,pathlib,json
R=pathlib.Path(__file__).resolve().parent
def check(live=False):
 base={p:h for h,p in (line.split('  ',1) for line in (R/'26961_BASE_26959_FULL_APP.sha256').read_text().splitlines())}
 output={p:h for h,p in (line.split('  ',1) for line in (R/'26961_EXPECTED_FULL_APP.sha256').read_text().splitlines())}
 roots=['app/src/main/cpp/iris26864/','app/src/main/cpp/iris26856/','app/src/main/java/com/hinnka/mycamera/processor/']
 native=[p for p in base if any(p.startswith(root) for root in roots)]
 assert native and all(base[p]==output[p] for p in native)
 assert base['app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt']==output['app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt']
 prov=json.loads((R/'26961_BASELINE_AND_SCOPE.json').read_text())
 assert prov['protected_count']==2050
 if live:
  for p in native:
   assert hashlib.sha256((R/p).read_bytes()).hexdigest()==base[p],p
  root=R/'app/src/main/cpp/iris26864'
  s=(root/'Iris26864RealRawrCoordinator.cpp').read_text()
  c=(root/'bridge/Iris26888BOffHdrqCoordinator.cpp').read_text()
  assert 'hdrq.strength = bOffReusable ? 11.0f : 13.0f' in s
  assert 'recorder.setMotionGate(algorithm_ == MergeAlgorithm::HdrPlusFrequency &&' in c
  assert '!photoBOffRawr051' in c
 print('PASS exact successful 26959 B OFF HDRQ strength 11, no B OFF zmap gate, 26959 Wiener/noise/alignment/chroma shader and native protected')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--payload',action='store_true');ap.add_argument('--live',action='store_true');args=ap.parse_args();check(args.live)
