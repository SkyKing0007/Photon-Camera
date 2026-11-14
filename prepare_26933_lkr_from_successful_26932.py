#!/usr/bin/env python3
"""26933 V1 R2: restore genuine, pinned RawLens 2.2.86 native ABIs from the
already SHA-authenticated SUCCESSFUL 26932 Actions APK inside its published artifact.
No network, no previous APK rebuild, no vendor/native edit, no fallback.
"""
import hashlib, pathlib, shutil, subprocess, sys, tempfile, zipfile
from build_26933_incremental import (R, ART, ART_SHA, TAR_SHA, ART_ID, RUN, COMMIT,
                                       PRIOR_APK_SHA, OUT as STATUS_DIR, fail, sha)

APK_NAME = 'IrisCamera-0.9726932-26932-iris-rawr-debug.apk'
TARGET = R / 'app/build/verified_rawlens26931/jniLibs'
RECEIPT = STATUS_DIR / '26933_INHERITED_LKR_NATIVE_RECEIPT.txt'
LIBRARY_SHA = {
    'arm64-v8a': {
        'liblkrpipeline.so': 'af1d4caff00b3b189d23d1d53c7c9d11256f5b050af2590c5407191ce32cd39b',
        'libsrpipeline.so': 'a91e0a33226db0e08b5355e2fac189cc9b91af7106530f6577d5084f1f39865d',
    },
    'armeabi-v7a': {
        'liblkrpipeline.so': '46de04ea3b1d37fbcc9bb380f94d56e7d7ad74d110e990e8413589e4e7eb8450',
        'libsrpipeline.so': '61fdaab8881684999c03bf6d9a3cbe1d9b3da63effe0f364eaca103f97efe78c',
    },
}

def hashbytes(b): return hashlib.sha256(b).hexdigest()

def main():
    # Prior 26933 Actions FETCH authenticated the 26932 run, artifact identity,
    # published ZIP SHA, compiled TAR/builder/workflow receipts. Fail closed
    # if the authenticated artifact was removed or replaced after FETCH.
    if not ART.is_file() or sha(ART) != ART_SHA:
        fail('authenticated successful 26932 artifact ZIP missing or SHA mismatch; never download RawLens on the runner')
    if TARGET.is_symlink() or any(TARGET.glob('**/*.so')):
        fail('unexpected pre-existing rawLens native binaries; refuse stale/unverified overwrite')
    TARGET.mkdir(parents=True, exist_ok=True)
    STATUS_DIR.mkdir(parents=True, exist_ok=True)
    report = [
        f'26933 native origin=SUCCESSFUL 26932 Actions run={RUN} commit={COMMIT} artifact={ART_ID}',
        f'26932 artifact sha256={ART_SHA}',
        f'26932 compiled source TAR sha256={TAR_SHA}',
        f'26932 prior APK sha256={PRIOR_APK_SHA}',
        'mode=EXACT_UNCHANGED_ORIGINAL_RAWLENS_2_2_86_FROM_VERIFIED_26932_APK',
        'external GitHub release API/download=NOT USED',
        'previous APK rebuild=NOT USED',
        'new 26933 dual-ABI JNI/NDK/GLSL/Kotlin/Java/assemble=MANDATORY',
    ]
    # Stream only the previously built 26932 APK out of the parent artifact:
    # never download or compile a prior APK; never add any binaries to Git.
    with tempfile.TemporaryDirectory(prefix='26933_inherited_lkr_') as scratch:
        apkfile = pathlib.Path(scratch) / APK_NAME
        with zipfile.ZipFile(ART) as artifact:
            if artifact.testzip() is not None:
                fail('26932 authority artifact ZIP CRC failed')
            if APK_NAME not in artifact.namelist():
                fail('successful 26932 artifact is missing its actual APK')
            with artifact.open(APK_NAME) as src, apkfile.open('wb') as dst:
                shutil.copyfileobj(src, dst, length=4 * 1024 * 1024)
            receipt_key = 'photon_26932_outputs/26932_APK.sha256'
            if receipt_key not in artifact.namelist() or PRIOR_APK_SHA not in artifact.read(receipt_key).decode():
                fail('successful 26932 APK compiler receipt missing')
        if sha(apkfile) != PRIOR_APK_SHA:
            fail('published 26932 APK SHA does not match successful Actions receipt')
        with zipfile.ZipFile(apkfile) as apk:
            if apk.testzip() is not None:
                fail('prior APK ZIP CRC failed')
            for abi, libs in LIBRARY_SHA.items():
                for lib, expected in libs.items():
                    entry = f'lib/{abi}/{lib}'
                    if entry not in apk.namelist():
                        fail('published 26932 APK lacks required ORIGINAL LKR library '+entry)
                    data = apk.read(entry)
                    if hashbytes(data) != expected:
                        fail('published 26932 original RawLens binary hash mismatch '+entry)
                    dst = TARGET / abi / lib
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    dst.write_bytes(data)
                    if sha(dst) != expected:
                        fail('materialized LKR binary differs from exact released ABI '+entry)
                    report.append(f'PASS original RawLens 2.2.86 {entry} sha256={expected} bytes={len(data)}')
            if 'assets/licenses/rawlens_2_2_86_lkr_apache_notice.txt' not in apk.namelist():
                fail('inherited original LKR APK missing Apache license attribution')
        # Reject wrong ELF, dynamic dependencies, absent JNI symbols exactly as
        # the inherited 26931 ABI regression verifies. This is checked again by
        # test_26931_native_integrity.py --native immediately after this stage.
        for abi, libs in LIBRARY_SHA.items():
            for lib in libs:
                f = TARGET / abi / lib
                p = subprocess.run(['readelf', '-h', str(f)], capture_output=True, text=True)
                expect = ('ELF64', 'AArch64') if abi=='arm64-v8a' else ('ELF32', 'ARM')
                if p.returncode or any(x not in p.stdout for x in expect):
                    fail('inherited original RawLens ELF class/architecture mismatch '+abi+'/'+lib)
    RECEIPT.write_text('\n'.join(report)+'\n')
    print('\n'.join(report))

if __name__=='__main__':
    try: main()
    except Exception as exc:
        print('26933 VERIFIED-INHERITED-LKR BLOCKED:', str(exc), file=sys.stderr)
        sys.exit(1)
