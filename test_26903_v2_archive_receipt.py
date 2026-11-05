#!/usr/bin/env python3
"""Negative reproduction of real 41972085315 failure plus positive correction.
Optionally use a real 26901 source TAR from current recovered workspace; the
Actions runner separately calls the same verifier on the original 26902 ZIP.
"""
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

R=Path(__file__).resolve().parent
HELP=R/'verify_26903_v2_archive_receipt.py'
OUT='build_26902_iris_rawr_outputs'
NAME='26901_historical_candidate_app_source.tar.gz'
ORIGINAL_ABS='/home/runner/work/Photon-Camera/Photon-Camera/'+OUT+'/'+NAME

def run(*args):
    return subprocess.run([sys.executable,'-S',str(HELP),*map(str,args)],capture_output=True,text=True)

with tempfile.TemporaryDirectory(prefix='26903_v1_real_failure_v2_fix_') as td:
    base=Path(td)/'relocated_successful_26902_artifact'/OUT
    base.mkdir(parents=True)
    tar=base/NAME
    if sys.argv[1:]:
        assert len(sys.argv)==3 and sys.argv[1]=='--historical-source', 'two optional operands: --historical-source PATH'
        src=Path(sys.argv[2]).resolve()
        assert (src/'app').is_dir() and len(list((src/'app').rglob('*')))>2026, 'real historical app source unavailable'
        # Actual restored 26901 compiled SOURCE bytes, not an invented file tree.
        with tarfile.open(tar,'w:gz',compresslevel=6) as t:
            t.add(src/'app',arcname='app',recursive=True)
        assert len(list((src/'app').rglob('*')))>2026
    else:
        # Small receipt parser fixture; real original 26901 source is tested locally
        # with --historical-source and actual original receipt is checked in Actions.
        tar.write_bytes(b'actual archived source bytes fixture for path relocation')
    h=hashlib.sha256(tar.read_bytes()).hexdigest()
    receipt=base/(NAME+'.sha256')
    orig=(h+'  '+ORIGINAL_ABS+'\n').encode()
    receipt.write_bytes(orig)
    # Exact historical V1 command FAILS because it dereferences the old absolute path.
    old=subprocess.run(['sha256sum','-c',str(receipt)],cwd=base,capture_output=True,text=True)
    assert old.returncode!=0,('V1 unexpectedly accepted historical absolute path',old.stdout)
    assert 'No such file or directory' in old.stderr
    ok=run(tar,receipt)
    assert ok.returncode==0,(ok.stdout,ok.stderr)
    assert 'SHA256='+h in ok.stdout
    negatives=[
      ('archive-mutated',lambda:tar.write_bytes(tar.read_bytes()+b'X')),
      ('receipt-corrupt-digest',lambda:receipt.write_bytes((('0' if h[0]!='0' else '1')+h[1:]+'  '+ORIGINAL_ABS+'\n').encode())),
      ('receipt-extra-line',lambda:receipt.write_bytes(orig+orig)),
      ('receipt-bad-hex',lambda:receipt.write_bytes(b'not-a-hex  '+ORIGINAL_ABS.encode()+b'\n')),
      ('receipt-wrong-filename',lambda:receipt.write_bytes((h+'  '+ORIGINAL_ABS+'.wrong\n').encode())),
      ('receipt-wrong-output-root',lambda:receipt.write_bytes((h+'  /home/runner/work/Photon-Camera/Photon-Camera/build_26901_iris_rawr_outputs/'+NAME+'\n').encode())),
      ('receipt-relative-name',lambda:receipt.write_bytes((h+'  '+NAME+'\n').encode())),
      ('receipt-fake-traversal',lambda:receipt.write_bytes((h+'  /home/runner/work/x/'+OUT+'/../'+NAME+'\n').encode())),
      ('receipt-empty',lambda:receipt.write_bytes(b'')),
      ('receipt-missing',lambda:receipt.unlink()),
      ('archive-missing',lambda:tar.unlink()),
    ]
    for label,mutate in negatives:
        original_tar=tar.read_bytes() if tar.exists() else b''
        mutate()
        assert run(tar,receipt).returncode!=0,('unsafe relocated artifact accepted',label)
        tar.write_bytes(original_tar)
        receipt.write_bytes(orig)
        assert run(tar,receipt).returncode==0,('legitimate restored archive rejected',label)
    assert run(tar).returncode!=0,'wrong verifier arg count accepted'
    assert run(tar,receipt,'extra').returncode!=0,'extra verifier args accepted'
    print('PASS real 26903 V1 Actions 41972085315 historical ABSOLUTE receipt pathname FAIL reproduced and V2 relocated bytes PASS; 11 negative tamper and CLI cases rejected'+(' on original 26901 reconstructed 2026-file source' if sys.argv[1:] else ''))
