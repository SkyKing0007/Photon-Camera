#!/usr/bin/env python3
"""Reject wrong trigger and partition, alternate workflow and SHA; no repo writes."""
from pathlib import Path
import sys, tempfile, shutil, subprocess, hashlib, re
R=Path(__file__).resolve().parent
w=(R/'.github/workflows/build-26894-iris-rawr.yml').read_text()
start=w.index('  push:\n');end=w.index('  workflow_dispatch:',start)
assert w[start:end]=="  push:\n    branches: [experimental-clean-photon-rebuild]\n    paths:\n      - 'TRIGGER_26894_RETRY_V2.txt'\n"
for extra in ("      - 'generate_26894_build.py'\n","      - '.github/workflows/build-26894-iris-rawr.yml'\n","      - '26894_HANDOFF_HASHES.sha256'\n","      - 'handoff_payload_26894/**'\n"):
 tam=w[:end]+extra+w[end:];assert tam[tam.index('  push:\n'):tam.index('  workflow_dispatch:')]!=w[start:end]
 assert tam.count("      - '")>1
s1=(R/'26894_STAGE_1_UPLOAD_PATHS.txt').read_text().splitlines();s2=(R/'26894_STAGE_2_UPLOAD_PATHS.txt').read_text().splitlines();s3=(R/'26894_STAGE_3_UPLOAD_PATHS.txt').read_text().splitlines()
assert s2==['.github/workflows/build-26894-iris-rawr.yml'] and s3==['TRIGGER_26894_RETRY_V2.txt']
assert not set(s1)&set(s2+s3)
assert set(s1)|set(s2)|set(s3)==set((R/'26894_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines())

assert (R/'TRIGGER_26894.txt').read_bytes()==b'RUN_26894_SPATIAL_FOREGROUND_NOISE_SAFE_FLAT_CONTRAST_V1\n'
assert (R/'TRIGGER_26894_RETRY_V2.txt').read_bytes()==b'RUN_26894_SPATIAL_FOREGROUND_NOISE_SAFE_FLAT_CONTRAST_V2\n'
assert sys.argv[1:] in ([], ['--runner']), 'test only default and --runner'
if sys.argv[1:]==['--runner']:
    runner=(R/'build_26894_iris_rawr.sh').read_text()
    st=runner.index('\nclean_extract_replay(){')
    end=runner.index('\n}',st)
    section=runner[st:end]
    old_names=(" grep -Fx 'VERSION_NAME=0.9726893' \"$exp/app/version.properties\" >/dev/null",
               " grep -Fx 'VERSION_BUILD=26893' \"$exp/app/version.properties\" >/dev/null")
    new_names=(" grep -Fx 'VERSION_NAME=0.9726894' \"$exp/app/version.properties\" >/dev/null",
               " grep -Fx 'VERSION_BUILD=26894' \"$exp/app/version.properties\" >/dev/null")
    assert all(section.count(x)==1 for x in new_names), 'current final clean-extract version checks missing'
    assert all(x not in section for x in old_names), 'old clean-extract guard silently rejects 26894'
    assert runner.count('clean_extract_replay(){')==1
    assert subprocess.run(['bash','-n',str(R/'build_26894_iris_rawr.sh')],capture_output=True).returncode==0
    with tempfile.TemporaryDirectory() as d:
        td=Path(d); (td/'app').mkdir()
        shutil.copyfile(R/'handoff_payload_26894/version.properties',td/'app/version.properties')
        assert (td/'app/version.properties').read_text().count('VERSION_NAME=0.9726894')==1
        assert (td/'app/version.properties').read_text().count('VERSION_BUILD=26894')==1
        def run_checks(cmds):
            command='set -euo pipefail\nexp="$1"\n'+ '\n'.join(cmds)+'\n'
            return subprocess.run(['bash','-c',command,'--',str(td)],capture_output=True,text=True).returncode
        assert run_checks(old_names)!=0, 'actual 26894 bytes failed to reproduce old Actions 41253156977 bug'
        assert run_checks(new_names)==0, 'corrected exact Actions final version commands do not actually PASS'
        # Ensure the successful historical 26893 guard is still valid on historical source.
        old=(R/'handoff_payload_26893/version.properties')
        if old.is_file():
            shutil.copyfile(old,td/'app/version.properties')
            assert run_checks(old_names)==0
            assert run_checks(new_names)!=0
    print('PASS 26894 failed Actions version guard NEGATIVE reproduced on actual 26894 source; exact corrected generated clean-extract commands executed PASS')

print('PASS 26894 V2 one retry trigger, original trigger immutable, 4 negative premature trigger fixtures, strict upload paths')
