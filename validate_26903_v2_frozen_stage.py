#!/usr/bin/env python3
"""Execute V2's ORIGINAL full strict runner/source/trigger validator in its OWN
byte-identical, frozen V2 shell runner. New V3 runner is never passed to V2 gate.
Tests both real positive and original archived tamper negative cases.
"""
from pathlib import Path
import hashlib,shutil,subprocess,sys,tempfile
R=Path(__file__).resolve().parent
SHA_V2='8624b1617ba9156af7501667f95e63e69f5fdf6384cec30ed48ee50a9b828762'
SHA_V1='5d932336627107556a1df870802b2e32046467d599ab4648fb57b7f78dc117ad'
SHA_02='348b2d617ed36b40744d15eeba762bb64c589e45327f60f18454d54cbc4c64dc'
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert H(R/'build_26902_iris_rawr.sh')==SHA_02
v1=(R/'26903_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines()
v2=(R/'26903_V2_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines()
assert len(v1)==34 and len(v2)==15 and set(v1).isdisjoint(v2)
with tempfile.TemporaryDirectory(prefix='p26903_exact_historical_V2_runner_') as td:
 T=Path(td)
 for rel in v1+v2+['build_26902_iris_rawr.sh']:
  f=R/rel;assert f.is_file(),rel
  d=T/rel;d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,d)
 def run(argv):
  p=subprocess.run(argv,cwd=T,capture_output=True,text=True)
  assert p.returncode==0,(argv,p.stdout[-1300:],p.stderr[-1600:])
 run([sys.executable,'-S','generate_26903_build.py','.'])
 assert H(T/'build_26903_iris_rawr.sh')==SHA_V1
 run([sys.executable,'-S','generate_26903_v2_build.py','.'])
 assert H(T/'build_26903_iris_rawr.sh')==SHA_V2
 run([sys.executable,'-S','stage_26903_v2_root.py','--runner'])
 run([sys.executable,'-S','test_26903_v2_archive_receipt.py'])
 run([sys.executable,'-S','test_26903_v2_sealed_negatives.py','--runner'])
 print('PASS historical V1/V2 on ORIGINAL exact historical SHA runner/source; V2 staged + negative tests and relocated archive receipt')
