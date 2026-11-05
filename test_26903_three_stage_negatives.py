#!/usr/bin/env python3
"""Negative tests against sealed 26903 three-stage source bytes, not fixtures.
Runs exactly the packaged stage_26903_root command in a fresh temporary root.
"""
from pathlib import Path
import hashlib,shutil,subprocess,sys,tempfile
R=Path(__file__).resolve().parent
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def locate(rel):
 p=R/rel
 if p.is_file():return p
 p=R.parent/'STAGE_2_WORKFLOW'/rel
 if p.is_file():return p
 return R.parent/'STAGE_3_UPLOAD_LAST'/rel
allow=(R/'26903_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines()
assert len(allow)>25
with tempfile.TemporaryDirectory(prefix='photon26903_sealed_negative_') as td:
 T=Path(td)
 for rel in allow:
  src=locate(rel)
  assert src.is_file(),rel
  dst=T/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
 root=T/'stage_26903_root.py'
 def gate():
  p=subprocess.run([sys.executable,'-S',str(root)],cwd=T,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
  return p.returncode,p.stdout,p.stderr
 assert gate()[0]==0,('26903 baseline packaged stage failed',gate())
 # Deliberate no-anchor, exact-payload, generator, workflow, trigger, manifest,
 # runner-receipt, unexpected extra scope, late trigger mutation negative cases.
 mutate=[('source','handoff_payload_26903/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightBProcessor26903.java',b'\nTAMPER\n'),
         ('shader','handoff_payload_26903/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag',b'\nTAMPER\n'),
         ('source_controller','handoff_payload_26903/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',b'\nTAMPER\n'),
         ('source_dng','handoff_payload_26903/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',b'\nTAMPER\n'),
         ('parent_authority','26903_BASE_FULL_APP.sha256',b'\nTAMPER\n'),
         ('current_full_manifest','26903_EXPECTED_CANDIDATE_FULL_APP.sha256',b'\nTAMPER\n'),
         ('generator','generate_26903_build.py',b'\nTAMPER\n'),
         ('runner_sha','26903_GENERATED_BUILD_SHA256.txt',b'\nTAMPER\n'),
         ('forward_patch','26903_FORWARD_FULL_INDEX.patch',b'\nTAMPER\n'),
         ('validator','verify_26903.py',b'\nTAMPER\n'),
         ('workflow','.github/workflows/build-26903-iris-rawr.yml',b'\nTAMPER\n'),
         ('trigger','TRIGGER_26903.txt',b'\nTAMPER\n')]
 for label,rel,delta in mutate:
  f=T/rel;original=f.read_bytes();f.write_bytes(original+delta)
  assert gate()[0]!=0,('26903 tamper accepted',label)
  f.write_bytes(original)
 assert gate()[0]==0
 # Strong negative: recompute *all* SHA seals for malicious workflow path filtering.
 wf=T/'.github/workflows/build-26903-iris-rawr.yml';before=wf.read_text()
 wf.write_text(before.replace("      - 'TRIGGER_26903.txt'", "      - 'TRIGGER_26903.txt'\n      - '**/*.py'"))
 sh=T/'26903_HANDOFF_HASHES.sha256';lines=sh.read_text().splitlines()
 sh.write_text('\n'.join((H(T/l.split('  ',1)[1])+'  '+l.split('  ',1)[1]) for l in lines)+'\n')
 assert gate()[0]!=0,'26903 extra premature workflow trigger with rehashed seal ACCEPTED'
 wf.write_text(before)
 sh.write_text('\n'.join((H(T/l.split('  ',1)[1])+'  '+l.split('  ',1)[1]) for l in lines)+'\n')
 assert gate()[0]==0
 # A deliberately deleted candidate source cannot be accepted under a recomputed seal.
 f=T/'handoff_payload_26903/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightBProcessor26903.java';f.unlink()
 assert gate()[0]!=0,'26903 missing real Night B adapter accepted'
print('PASS 26903 actual sealed three-stage + 14 negative source/shader/DNG/generator/runner/workflow/trigger/extras/tamper tests')
if sys.argv[1:]==['--runner']:
 runner=R/'build_26903_iris_rawr.sh'
 expected=(R/'26903_GENERATED_BUILD_SHA256.txt').read_text().split('  ',1)[0]
 assert runner.is_file() and H(runner)==expected,'26903 actual generated runner SHA wrong'
 s=runner.read_text()
 assert '26902_HISTORICAL_GLSL_REAL_COMPILER_RECEIPT.txt' in s
 assert '26902_HISTORICAL_PATCH_PROOF.txt' in s
 assert '$ARTDIR/build_26902_iris_rawr_outputs/26902_candidate_app_source.tar.gz' in s
 assert '$ARTDIR/build_26901_iris_rawr_outputs/' not in s
 assert '$ARTDIR/build_26900_iris_rawr_outputs/' not in s
 print('PASS 26903 generated actual runner SHA and correct successful 26902 artifact operands')
else:assert not sys.argv[1:]
