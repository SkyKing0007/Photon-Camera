#!/usr/bin/env python3
"""Run REAL original V1 + V2 sealed file-byte tamper negatives against a
CLEAN temporary repository with the EXACT staged upload files and old V1 files.
"""
from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import tempfile

R=Path(__file__).resolve().parent
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
v1=(R/'26903_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines()
v2=(R/'26903_V2_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines()
assert len(v1)==34 and len(v2)==15
with tempfile.TemporaryDirectory(prefix='photon26903v2_sealed_actual_source_negative_') as td:
    T=Path(td)
    for rel in sorted(v1+v2+['build_26902_iris_rawr.sh']):
        src=R/rel
        if not src.is_file():
            src=R.parent/'STAGE_2_WORKFLOW'/rel
        if not src.is_file():
            src=R.parent/'STAGE_3_UPLOAD_LAST'/rel
        assert src.is_file(),rel
        dst=T/rel
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(src,dst)
    runner=R/'build_26903_iris_rawr.sh'
    with_runner=sys.argv[1:]==['--runner']
    assert sys.argv[1:] in ([],['--runner'])
    if with_runner:
        assert runner.is_file() and H(runner)==(R/'26903_V2_GENERATED_BUILD_SHA256.txt').read_text().split('  ',1)[0]
        shutil.copyfile(runner,T/runner.name)
    def gate():
        args=[sys.executable,'-S','stage_26903_v2_root.py']+(['--runner'] if with_runner else [])
        return subprocess.run(args,cwd=T,capture_output=True,text=True)
    assert gate().returncode==0,(gate().stdout,gate().stderr)
    mutated=[
        'generate_26903_v2_build.py',
        'verify_26903_v2_archive_receipt.py',
        'validate_26903_v1_frozen_stage.py',
        'test_26903_v2_archive_receipt.py',
        'test_26903_v2_sealed_negatives.py',
        '26903_V2_GENERATED_BUILD_SHA256.txt',
        '26903_V2_CUMULATIVE_REPOSITORY_ALLOWLIST.txt',
        '26903_V2_REPOSITORY_UPLOAD_ALLOWLIST.txt',
        '26903_V2_STAGE_1_UPLOAD_PATHS.txt',
        '26903_V2_STAGE_2_UPLOAD_PATHS.txt',
        '26903_V2_STAGE_3_UPLOAD_PATHS.txt',
        '.github/workflows/build-26903-v2-iris-rawr.yml',
        'TRIGGER_26903_V2.txt',
        'TRIGGER_26903.txt',
        '.github/workflows/build-26903-iris-rawr.yml',
        'generate_26903_build.py',
        'handoff_payload_26903/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightBProcessor26903.java',
        '26903_BASE_FULL_APP.sha256',
        '26903_FORWARD_FULL_INDEX.patch',
    ]
    for rel in mutated:
        f=T/rel
        prior=f.read_bytes()
        f.write_bytes(prior+b'\n26903_V2_BAD\n')
        p=gate()
        assert p.returncode!=0,('V2 accepted tampered REAL source',rel)
        f.write_bytes(prior)
        assert gate().returncode==0,('V2 rejected corrected source after tamper',rel)
    # Reseal original upload-byte digest after widening V2 workflow trigger:
    # the semantic trigger-only validator must still reject the change.
    wf=T/'.github/workflows/build-26903-v2-iris-rawr.yml'
    original=wf.read_text()
    assert original.count("      - 'TRIGGER_26903_V2.txt'")==1
    wf.write_text(original.replace("      - 'TRIGGER_26903_V2.txt'", "      - 'TRIGGER_26903_V2.txt'\n      - '**/*.py'"))
    seal=T/'26903_V2_HANDOFF_HASHES.sha256'
    backup=seal.read_bytes()
    lines=[]
    for l in seal.read_text().splitlines():
        path=l.split('  ',1)[1]
        lines.append(H(T/path)+'  '+path)
    seal.write_text('\n'.join(lines)+'\n')
    assert gate().returncode!=0,'V2 rehashed premature workflow trigger accepted'
    wf.write_text(original)
    seal.write_bytes(backup)
    assert gate().returncode==0
    if with_runner:
        f=T/'build_26903_iris_rawr.sh';old=f.read_bytes();f.write_bytes(old+b'BAD RUNNER')
        assert gate().returncode!=0,'V2 malformed executed runner SHA accepted'
        f.write_bytes(old)
        assert gate().returncode==0
print('PASS 26903 V2 exact original successful 26902/failed V1 source + V2 SHA-sealed 15-path staged-byte negative regression; 19 altered source/trigger/workflow/runner negatives and resealed illicit early trigger rejected')
