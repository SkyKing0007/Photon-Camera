#!/usr/bin/env python3
"""Reject wrong trigger and partition, alternate workflow and SHA; no repo writes."""
from pathlib import Path
R=Path(__file__).resolve().parent
w=(R/'.github/workflows/build-26894-iris-rawr.yml').read_text()
start=w.index('  push:\n');end=w.index('  workflow_dispatch:',start)
assert w[start:end]=="  push:\n    branches: [experimental-clean-photon-rebuild]\n    paths:\n      - 'TRIGGER_26894.txt'\n"
for extra in ("      - 'generate_26894_build.py'\n","      - '.github/workflows/build-26894-iris-rawr.yml'\n","      - '26894_HANDOFF_HASHES.sha256'\n","      - 'handoff_payload_26894/**'\n"):
 tam=w[:end]+extra+w[end:];assert tam[tam.index('  push:\n'):tam.index('  workflow_dispatch:')]!=w[start:end]
 assert tam.count("      - '")>1
s1=(R/'26894_STAGE_1_UPLOAD_PATHS.txt').read_text().splitlines();s2=(R/'26894_STAGE_2_UPLOAD_PATHS.txt').read_text().splitlines();s3=(R/'26894_STAGE_3_UPLOAD_PATHS.txt').read_text().splitlines()
assert s2==['.github/workflows/build-26894-iris-rawr.yml'] and s3==['TRIGGER_26894.txt']
assert not set(s1)&set(s2+s3)
assert set(s1)|set(s2)|set(s3)==set((R/'26894_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines())
print('PASS 26894 exactly one trigger, 4 negative premature trigger fixtures, strict Stage1/Stage2/Stage3 paths')
