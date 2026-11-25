#!/usr/bin/env python3
"""Actual 26983 V1 step-60 regression: V10 historical fixture must include the 26982-evolved RAW processor.
Replay the unmodified historical script and exact three historical source files only in a temporary copy.
Verify current source remains intact; no historical assertion or real compiler gate is relaxed.
"""
import argparse, hashlib, pathlib, shutil, subprocess, sys, tempfile
R=pathlib.Path(__file__).resolve().parent
B='app/src/main/java/com/hinnka/mycamera/processor/experimentc/'
PINS={
 B+'Iris26975CPinnedDonorProEngine.kt':('f29e1c0be1b41a643a8eb0443903e15444b9671d8b8c949f98135d8aae49b1b8','02b8856cb235602dfb35160a604a8b6278b9b5c71bd177e478d18ebb6fc97137'),
 B+'original129/gallery/Jpeg444ExportEncoder.kt':('8beb2bd0a886361c9c329338f84c9c0d1f33689d94a782685efc826043a25874','ca10af41309e16f96eb4dbe13d0601b27a7301609f93f6ae907b14dfc4789538'),
 B+'original129/raw/RawDemosaicProcessor.kt':('a1331d2720df39570afe10c79a74d0a9054f183b0a8788f20a47c651d005aee2','0de87713fc701e8d0f253f5c43fe4ac6243cc2803071bb663332f6431af44cd9'),
}
FILES={
 'test_26975_v10_minimal_core.py':'7247fc15a79f5196279ebba12cae838109f12d10fed33059359240018119530f',
 '26975_V10_MINIMAL_LUT_REACHABILITY_PROOF.json':'2ba4bf4d29b9827a6b7c061caa8554b69c83785ac1f78f88bd8f31f0bfd0562a',
 '26975_V6_CURRENT_SHADER_INVENTORY.json':'f1995762ae6f346906349ddb0021fa5f5e722a605703c1d862c9f0acfd30c372',
}
RAW=list(PINS)[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def checked_copy(src,dst,want):
 assert sha(src)==want,('historical fixture source SHA',str(src))
 shutil.copyfile(src,dst)
 assert sha(dst)==want,('copied fixture SHA',str(dst))
def run(base,historical,tests,candidate):
 for rel,(current,old) in PINS.items():
  assert sha(base/rel)==current,('actual 26982 SHA',rel)
  assert sha(candidate/rel)==current,('26983 protected source SHA',rel)
  assert sha(historical/rel)==old,('original sealed 26975 SHA',rel)
 with tempfile.TemporaryDirectory(prefix='26983_v10_') as td:
  t=pathlib.Path(td);shutil.copytree(base/'app',t/'app',ignore=shutil.ignore_patterns('build','.cxx'))
  for name,want in FILES.items():checked_copy(tests/name,t/name,want)
  for rel in list(PINS)[:2]:checked_copy(historical/rel,t/rel,PINS[rel][1])
  cmd=[sys.executable,'-S','test_26975_v10_minimal_core.py','--live']
  fail=subprocess.run(cmd,cwd=t,capture_output=True,text=True)
  assert fail.returncode!=0 and 'AssertionError: specialized selected-path source changed: '+RAW in fail.stderr,fail.stdout+fail.stderr
  print('PASS reproduced exact original 26983 V1 step 60 assertion',flush=True)
  checked_copy(historical/RAW,t/RAW,PINS[RAW][1])
  subprocess.run(cmd,cwd=t,check=True)
  protected=B+'original129/raw/RawAdjustmentPass.kt'
  f=t/protected;data=f.read_bytes();f.write_bytes(data+b'\n// negative fixture only\n')
  fail=subprocess.run(cmd,cwd=t,capture_output=True,text=True)
  assert fail.returncode!=0 and 'AssertionError: unchanged donor source changed: '+protected in fail.stderr,fail.stdout+fail.stderr
  f.write_bytes(data)
  subprocess.run(cmd,cwd=t,check=True)
 for rel,(current,old) in PINS.items():
  assert sha(base/rel)==current and sha(candidate/rel)==current,('unexpected live or candidate mutation',rel)
 print('PASS original V10 historical live closure, 3 exact historic source pins, negative protected-file rejection, original 26982 and 26983 untouched',flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--base',type=pathlib.Path,required=True);p.add_argument('--historical',type=pathlib.Path,required=True);p.add_argument('--tests',type=pathlib.Path,required=True);p.add_argument('--candidate',type=pathlib.Path,required=True);a=p.parse_args();run(a.base.resolve(),a.historical.resolve(),a.tests.resolve(),a.candidate.resolve())
