#!/usr/bin/env python3
"""Use real exact candidate bytes for negative tamper; restore between tests."""
import pathlib,subprocess,sys,shutil,tempfile
assert len(sys.argv)==3
base=pathlib.Path(sys.argv[1]).resolve();cand=pathlib.Path(sys.argv[2]).resolve();root=pathlib.Path(__file__).resolve().parent
script=root/'verify_26889_candidate.py'
relative=[
 'app/version.properties',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26889BOffSceneMotion.kt',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870GpuSharpest.kt',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26868DirectLong.kt',
 'app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqMerge.comp',
 'app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqRecorder.cpp',
 'app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqMismatch.comp',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26856RawrColorContract.kt',
]
with tempfile.TemporaryDirectory() as d:
 t=pathlib.Path(d)/'candidate';shutil.copytree(cand,t)
 for n in relative:
  q=t/n
  if not q.exists():
   print('SKIP nonexistent requested protected control',n);continue
  original=q.read_bytes()
  q.write_bytes(original+b'\n//IRIS_26889_TAMPER_NEGATIVE\n')
  p=subprocess.run([sys.executable,'-S',str(script),str(base),str(t)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
  assert p.returncode!=0,('failed to reject tamper',n)
  q.write_bytes(original)
  print('PASS reject tamper',n)
 p=subprocess.run([sys.executable,'-S',str(script),str(base),str(t)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 assert p.returncode==0,(p.stdout,p.stderr)
 print('PASS full candidate restored')
