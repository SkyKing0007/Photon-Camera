#!/usr/bin/env python3
"""Replay the EXACT 26948 glslang/SPIR-V body on unchanged live shader bytes.

The original 26948 script's --live *source-only* checker requires version=26948
and the ten-file 26948 allowlist; those requirements cannot hold in the verified
26949 candidate. Replay the identical checker against its own SHA-sealed 26948
payload, then execute the full unchanged real-compiler body against the 26949
live shader files. No compiler, optimizer, validation step, or source gate removed.
"""
import hashlib
import pathlib
import subprocess
import sys
from build_26949_incremental import R, parse, sha, fail

OLD_COMPILER = R / 'compile_26948_shaders.sh'
OLD_GIT_BLOB = '2e02b430e62790beaed47d7f0679c63622bab326'
ORIGINAL_CHECK = 'python3 -S test_26948_sdr_hdr_math.py --live'
REPLAY_CHECK = 'python3 -S test_26948_sdr_hdr_math.py --payload'
# These are ALL five shaders read or emitted by the original real 26948 compiler.
UNALTERED = (
    'app/src/main/assets/shaders/motionv2/render.glsl',
    'app/src/main/assets/shaders/motionv2/gainmap.glsl',
    'app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag',
    'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26856True2xCfa.kt',
    'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
)

def run(cmd):
    subprocess.run(cmd, cwd=R, check=True)

def check():
    b = OLD_COMPILER.read_bytes()
    blob = hashlib.sha1(b'blob ' + str(len(b)).encode('ascii') + b'\x00' + b).hexdigest()
    if blob != OLD_GIT_BLOB:
        fail('actual historical 26948 GLSL compiler is NOT exact successful 26948 script')
    src = b.decode('utf-8')
    if src.count(ORIGINAL_CHECK) != 1 or REPLAY_CHECK in src:
        fail('historical 26948 live-source gate changed or missing')
    old = parse(R / '26949_BASE_26948_FULL_APP.sha256')
    new = parse(R / '26949_EXPECTED_FULL_APP.sha256')
    for p in UNALTERED:
        if p not in old or old[p] != new.get(p) or not (R/p).is_file() or sha(R/p) != old[p]:
            fail('26948 real compiled source not byte-identical in 26949 '+p)
    if old.get('app/version.properties') == new.get('app/version.properties'):
        fail('regression invalid: 26949 version must differ from 26948')
    if ORIGINAL_CHECK not in src.splitlines()[4:9]:
        fail('unexpected historical checker position (unsafe substitution)')
    rewritten = src.replace(ORIGINAL_CHECK, REPLAY_CHECK, 1)
    if rewritten.replace(REPLAY_CHECK, ORIGINAL_CHECK, 1) != src:
        fail('historical full real GLSL/SPIR-V compiler body not preserved')
    return rewritten

def main():
    rewritten = check()
    if '--preflight' in sys.argv:
        print('PASS original 26948 historical compiler locked, original live-source mismatch detected, five compiled shaders byte-identical, 26949 candidate source intact')
        return
    # Strict historical source gate still runs, but only on its own SEALED 26948
    # stage payload. It must never be asked to attest to 26949 live sources.
    run([sys.executable, '-S', 'build_26948_incremental.py', 'seal'])
    run([sys.executable, '-S', 'test_26948_sdr_hdr_math.py', '--payload'])
    run([sys.executable, '-S', 'test_26949_source.py', '--live'])
    # Original script runs from repo root because $0 points to original script.
    # The ONLY change is using --payload for the historical-version source test.
    # All actual glslang 16.5, SPIR-V val/opt, emitted shader source and receipt
    # commands remain byte-for-byte identical to successful 26948.
    run(['bash', '-c', rewritten, str(OLD_COMPILER)])
    log = R/'photon_26948_outputs/26948_REAL_GLSL_SPIRV_COMPILER.txt'
    if not log.is_file() or 'PASS 26948 real pinned GLES/SPIR-V current three shader sources' not in log.read_text():
        fail('full 26948 real pinned shader compiler/optimizer did not PASS')
    for p in UNALTERED[:3]:
        if sha(R/p) not in log.read_text():
            fail('26948 historical actual source checksum not in real compile receipt '+p)
    run([sys.executable, '-S', 'test_26949_source.py', '--live'])
    print('PASS original 26948 real shader/SPIR-V compilation on unchanged 26949 byte-exact shaders; 26949 runtime source protected')

if __name__ == '__main__':
    try:main()
    except Exception as exc:
        print(str(exc),file=sys.stderr)
        sys.exit(1)
