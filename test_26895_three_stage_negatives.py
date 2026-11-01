#!/usr/bin/env python3
"""Single trigger and actual failed historical version-guard negative / corrected positive."""
from pathlib import Path
import sys,tempfile,subprocess,shutil,hashlib,re
R=Path(__file__).resolve().parent
workflow=R/'.github/workflows/build-26895-iris-rawr.yml'
if not workflow.is_file():workflow=R.parent/'STAGE_2_WORKFLOW/.github/workflows/build-26895-iris-rawr.yml'
w=workflow.read_text();p=w.index('  push:\n');q=w.index('  workflow_dispatch:',p)
assert w[p:q]=="  push:\n    branches: [experimental-clean-photon-rebuild]\n    paths:\n      - 'TRIGGER_26895.txt'\n"
for add in ["      - 'generate_26895_build.py'\n","      - '.github/workflows/build-26895-iris-rawr.yml'\n","      - '26895_HANDOFF_HASHES.sha256'\n","      - 'handoff_payload_26895/**'\n"]:
 tam=w[:q]+add+w[q:];assert tam.count("      - '")>1 and tam[p:tam.index('  workflow_dispatch:',p)]!=w[p:q]
s1=(R/'26895_STAGE_1_UPLOAD_PATHS.txt').read_text().splitlines();s2=(R/'26895_STAGE_2_UPLOAD_PATHS.txt').read_text().splitlines();s3=(R/'26895_STAGE_3_UPLOAD_PATHS.txt').read_text().splitlines()
assert s2==['.github/workflows/build-26895-iris-rawr.yml'] and s3==['TRIGGER_26895.txt']
assert not set(s1)&set(s2+s3)
assert set(s1)|set(s2)|set(s3)==set((R/'26895_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines())
assert sys.argv[1:] in ([],['--runner'])
if sys.argv[1:]==['--runner']:
 runner=(R/'build_26895_iris_rawr.sh').read_text();assert runner.count('clean_extract_replay(){')==1
 start=runner.index('\nclean_extract_replay(){');end=runner.index('\n}',start);body=runner[start:end]
 historic=("grep -Fx 'VERSION_NAME=0.9726894' \"$exp/app/version.properties\" >/dev/null", "grep -Fx 'VERSION_BUILD=26894' \"$exp/app/version.properties\" >/dev/null")
 current=("grep -Fx 'VERSION_NAME=0.9726895' \"$exp95/app/version.properties\" >/dev/null", "grep -Fx 'VERSION_BUILD=26895' \"$exp95/app/version.properties\" >/dev/null")
 assert all(body.count(v)==1 for v in (*historic,*current)),'version check values absent or duplicate'
 assert body.count('26894_historical_candidate_app_source.tar.gz')>=3 and body.count('26895_candidate_app_source.tar.gz')>=2
 assert subprocess.run(['bash','-n',str(R/'build_26895_iris_rawr.sh')],capture_output=True).returncode==0
 with tempfile.TemporaryDirectory(prefix='26895_act_version_') as d:
  td=Path(d);(td/'app').mkdir()
  shutil.copyfile(R/'handoff_payload_26895/version.properties',td/'app/version.properties')
  def run_checks(checks):
   cmds='set -euo pipefail\nexp="$1";exp95="$1"\n'+'\n'.join(checks)+'\n'
   return subprocess.run(['bash','-c',cmds,'--',str(td)],capture_output=True,text=True).returncode
  assert run_checks(historic)!=0, 'historical 26894 version guard wrongly accepts 26895 source'
  assert run_checks(current)==0, '26895 current source version guard missing/pass?'
 print('PASS 26895 ACTUAL emitted runner historical wrong-version NEGATIVE and correct-version POSITIVE, exact staged source')
print('PASS 26895 sole trigger stage3, zero premature path filters, four negative trigger tests, strict upload partitions')
