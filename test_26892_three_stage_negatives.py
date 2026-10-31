#!/usr/bin/env python3
"""Reject premature 26892 workflow triggers, scope, stage partition tampering."""
from pathlib import Path
import re
R=Path(__file__).resolve().parent
w=(R/'.github/workflows/build-26892-iris-rawr.yml').read_text()
start=w.index('  push:\n')
end=w.index('  workflow_dispatch:',start)
old=w[start:end]
assert old=="  push:\n    branches: [experimental-clean-photon-rebuild]\n    paths:\n      - 'TRIGGER_26892.txt'\n",'trigger stage not sole push path'
for extra in ("      - 'generate_26892_build.py'\n", "      - '.github/workflows/build-26892-iris-rawr.yml'\n", "      - '26892_HANDOFF_HASHES.sha256'\n", "      - 'handoff_payload_26892/**'\n"):
 tam=w[:end]+extra+w[end:]
 assert tam[tam.index('  push:\n'):tam.index('  workflow_dispatch:')]!=old
 assert tam.count("      - '")>1
stage1=(R/'26892_STAGE_1_UPLOAD_PATHS.txt').read_text().splitlines()
stage2=(R/'26892_STAGE_2_UPLOAD_PATHS.txt').read_text().splitlines()
stage3=(R/'26892_STAGE_3_UPLOAD_PATHS.txt').read_text().splitlines()
assert stage2==['.github/workflows/build-26892-iris-rawr.yml']
assert stage3==['TRIGGER_26892.txt']
assert not set(stage1)&set(stage2+stage3)
assert set(stage1)|set(stage2)|set(stage3)==set((R/'26892_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines())
print('PASS real 26892 one-path trigger, 4 premature-trigger negatives, strict Stage1(all)/Stage2(YAML)/Stage3(TXT) partition')
