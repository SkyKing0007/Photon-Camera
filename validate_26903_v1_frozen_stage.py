#!/usr/bin/env python3
"""Execute the EXACT original 26903 V1 source/staging validator on its OWN
frozen runner bytes, rather than on the corrected 26903 V2 generated runner.
Do not alter, bypass, or rehash the failed V1 handoff's sealed evidence.
"""
from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import tempfile

R=Path(__file__).resolve().parent
SHA_V1='5d932336627107556a1df870802b2e32046467d599ab4648fb57b7f78dc117ad'
SHA02='348b2d617ed36b40744d15eeba762bb64c589e45327f60f18454d54cbc4c64dc'
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert H(R/'build_26902_iris_rawr.sh')==SHA02, 'original successful 26902 runner lost'
paths=(R/'26903_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines()
assert len(paths)==34 and paths==sorted(set(paths)), 'original V1 repository receipt changed'
with tempfile.TemporaryDirectory(prefix='photon26903_original_v1_freeze_') as td:
    root=Path(td)
    for rel in paths+['build_26902_iris_rawr.sh']:
        src=R/rel
        assert src.is_file(),('original V1 source missing',rel)
        dst=root/rel
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(src,dst)
    def run(args):
        p=subprocess.run(args,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        if p.returncode:
            raise RuntimeError('ORIGINAL V1 HISTORICAL VALIDATOR FAILED:\n'+p.stdout[-2500:]+'\n'+p.stderr[-2500:])
    run([sys.executable,'-S','generate_26903_build.py','.'])
    assert H(root/'build_26903_iris_rawr.sh')==SHA_V1, 'V1 original runner source bytes drifted'
    run([sys.executable,'-S','stage_26903_root.py'])
    run([sys.executable,'-S','test_26903_three_stage_negatives.py','--runner'])
    print('PASS ORIGINAL failed V1 immutable payload/real 13-source manifest/negative gates, exact original generated V1 runner SHA; isolated from corrected V2 runner')
