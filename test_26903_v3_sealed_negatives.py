#!/usr/bin/env python3
"""CLEAN-EXTRACTED literal V3 15-file upload negative tamper replay. Tests
strict V1/V2 immutable guards, no early workflow triggers, generated runner.
"""
import hashlib,shutil,subprocess,sys,tempfile
from pathlib import Path
R=Path(__file__).resolve().parent
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
runner_sha='a5e9b4923325a13d3ab54fbfe233f3fca0d79b3a6f43ae194fa5edcb1ab67b44'
assert sys.argv[1:] in ([],['--runner'])
with_runner=bool(sys.argv[1:])
v1=(R/'26903_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines()
v2=(R/'26903_V2_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines()
v3=(R/'26903_V3_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines()
assert list(map(len,(v1,v2,v3)))==[34,15,15]
with tempfile.TemporaryDirectory(prefix='photon26903_v3_realsealed_all_path_negatives_') as td:
 T=Path(td)
 for rel in v1+v2+v3+['photon_preserve_successful_runner.py','build_26902_iris_rawr.sh']:
  f=R/rel;assert f.is_file(),rel
  d=T/rel;d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,d)
 if with_runner:
  assert H(R/'build_26903_iris_rawr.sh')==runner_sha
  shutil.copyfile(R/'build_26903_iris_rawr.sh',T/'build_26903_iris_rawr.sh')
 def gate():
  z=subprocess.run([sys.executable,'-S','stage_26903_v3_root.py']+(['--runner'] if with_runner else []),cwd=T,capture_output=True,text=True)
  return z
 p=gate();assert p.returncode==0,(p.stdout,p.stderr)
 checked=[
  'generate_26903_v3_build.py',
  'photon_preserve_26903_v3_runner.py',
  'validate_26903_v2_frozen_stage.py',
  'stage_26903_v3_root.py',
  'test_26903_v3_archive_receipt.py',
  'test_26903_v3_sealed_negatives.py',
  '26903_V3_GENERATED_BUILD_SHA256.txt',
  '26903_V3_CUMULATIVE_REPOSITORY_ALLOWLIST.txt',
  '26903_V3_REPOSITORY_UPLOAD_ALLOWLIST.txt',
  '26903_V3_STAGE_1_UPLOAD_PATHS.txt',
  '26903_V3_STAGE_2_UPLOAD_PATHS.txt',
  '26903_V3_STAGE_3_UPLOAD_PATHS.txt',
  '26903_V3_HANDOFF_HASHES.sha256',
  '.github/workflows/build-26903-v3-iris-rawr.yml',
  'TRIGGER_26903_V3.txt',
  'generate_26903_v2_build.py',
  '26903_V2_GENERATED_BUILD_SHA256.txt',
  '.github/workflows/build-26903-v2-iris-rawr.yml',
  'TRIGGER_26903_V2.txt',
  'generate_26903_build.py',
  '.github/workflows/build-26903-iris-rawr.yml',
  'TRIGGER_26903.txt',
  'handoff_payload_26903/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightBProcessor26903.java',
  '26903_BASE_FULL_APP.sha256',
  '26903_FORWARD_FULL_INDEX.patch',
 ]
 for rel in checked:
  f=T/rel;backup=f.read_bytes();f.write_bytes(backup+b'\nTAMPER_26903_V3\n')
  z=gate()
  assert z.returncode!=0,('accepted tamper',rel,z.stdout,z.stderr)
  f.write_bytes(backup)
  assert gate().returncode==0,('failed to restore',rel)
 # Semantic trigger-only check must reject *after* rehashing YAML upload seal.
 f=T/'.github/workflows/build-26903-v3-iris-rawr.yml';old=f.read_text()
 assert old.count("      - 'TRIGGER_26903_V3.txt'")==1
 f.write_text(old.replace("      - 'TRIGGER_26903_V3.txt'","      - 'TRIGGER_26903_V3.txt'\n      - '**/*.py'"))
 seal=T/'26903_V3_HANDOFF_HASHES.sha256';orig=seal.read_text()
 seal.write_text('\n'.join((H(T/l.split('  ',1)[1])+'  '+l.split('  ',1)[1] for l in orig.splitlines()))+'\n')
 assert gate().returncode!=0,'rehash widened workflow trigger passed'
 f.write_text(old);seal.write_text(orig)
 assert gate().returncode==0
 # Semantic and SHA receipt also fail closed on a narrower/altered workflow.
 f=T/'26903_V3_CUMULATIVE_REPOSITORY_ALLOWLIST.txt';original=f.read_text()
 f.write_text(original+'rogue.unapproved.source\n')
 assert gate().returncode!=0
 f.write_text(original)
 if with_runner:
  f=T/'build_26903_iris_rawr.sh';old=f.read_bytes();f.write_bytes(old+b'\nALTERED_RUNNER\n')
  assert gate().returncode!=0
  f.write_bytes(old)
 assert gate().returncode==0
 print('PASS V3 strict 64-path payload, 25 real V1/V2/V3 source/runner/workflow/trigger/hash mutants rejected, resealed rogue workflow trigger rejected, original source restored')
