#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, os, sys
from pathlib import Path

TARGET = Path('build_26536_integrated_night_lowlight_reliability.sh')
HANDOFF = Path('26536_HANDOFF_HASHES.sha256')
EXPECTED_V1_SHA256 = '39c192a5570d30330a611e14921cd13ae5a5af90eea96784da62c9c23fab8bea'

BRANCH_BLOCK = ''' # Local-only safety branch; no remote backup branch is created or pushed.\n git branch local-safety-26535-before-26536\n'''
NO_BRANCH_BLOCK = ''' # No backup branch is created; exact rollback patch is retained as recovery proof.\n'''
OLD_PASS = 'pass "exact six-file forward/rollback proof; fuzz=0 both directions; local safety branch only"'
NEW_PASS = 'pass "exact six-file forward/rollback proof; fuzz=0 both directions; no backup branch"'
OLD_GATE5 = 'python3 "$VALIDATE" --base "$BASE" --candidate "$ROOT" | tee "$OUT/26536_postbuild_architecture_validation.txt"'
MARKER = 'IRIS_26536_V1_2_POSTBUILD_SANITIZED_VALIDATION'
NEW_GATE5 = r'''# IRIS_26536_V1_2_POSTBUILD_SANITIZED_VALIDATION
# The 26535-style Gate 5 proofs above remain authoritative for build-time native regions:
#  1) assert_cpp_deps_exact proves the generated cpp/deps file set exactly; and
#  2) the pinned bjzhou manifest proves third_party_26507 byte-for-byte.
# Validate the six-file 26536 runtime contract in a separate copy with only those
# independently proven build-time native additions removed.
POSTCHECK="$WORK/postbuild_validation_candidate"
rm -rf "$POSTCHECK"
mkdir -p "$POSTCHECK/app/src"
cp -a "$ROOT/app/src/main" "$POSTCHECK/app/src/"
cp "$ROOT/app/version.properties" "$POSTCHECK/app/version.properties"
cp "$ROOT/app/build.gradle" "$POSTCHECK/app/build.gradle"
rm -rf "$POSTCHECK/app/src/main/cpp/third_party_26507"
find "$POSTCHECK/app/src/main/cpp/deps" -mindepth 1 -maxdepth 1 -type f ! -name '.gitignore' -delete
assert_cpp_deps_exact "$POSTCHECK" pre
manifest_audited_live "$POSTCHECK" "$OUT/26536_postbuild_sanitized_audited_runtime.sha256"
cmp -s "$OUT/26536_pre_gradle_audited_runtime.sha256" "$OUT/26536_postbuild_sanitized_audited_runtime.sha256" || fail "sanitized post-build runtime differs from canonical 26536 runtime"
python3 "$VALIDATE" --base "$BASE" --candidate "$POSTCHECK" | tee "$OUT/26536_postbuild_architecture_validation.txt"'''

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def one_replace(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise ValueError(f'{label}: expected exactly one anchor, found {n}')
    return text.replace(old, new, 1)

def patch_text(text: str) -> str:
    if MARKER in text:
        raise ValueError('V1.2 marker already present')
    text = one_replace(text, BRANCH_BLOCK, NO_BRANCH_BLOCK, 'backup-branch block')
    text = one_replace(text, OLD_PASS, NEW_PASS, 'Gate 2 PASS text')
    text = one_replace(text, OLD_GATE5, NEW_GATE5, 'Gate 5 raw ROOT validator')
    if 'git branch local-safety-26535-before-26536' in text:
        raise ValueError('backup branch creation survived')
    if OLD_GATE5 in text:
        raise ValueError('raw ROOT Gate 5 validator survived')
    if text.count(MARKER) != 1:
        raise ValueError('V1.2 Gate 5 marker count drift')
    if text.count('python3 "$VALIDATE" --base "$BASE" --candidate "$POSTCHECK"') != 1:
        raise ValueError('sanitized validator count drift')
    # Critical 26535-procedure anchors must survive the infrastructure correction.
    required = [
        'git diff --binary --no-ext-diff -- app/src/main',
        'git diff --binary --no-ext-diff -R -- app/src/main',
        '--fuzz=0 --no-backup-if-mismatch',
        'PRE-BUILD SAFETY PROOF PASSED',
        './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
        './gradlew :app:assembleDebug --stacktrace',
        'assert_cpp_deps_exact "$ROOT" post',
        '26536_postbuild_native_dependency_manifest_check.txt',
        'expected exactly one Gradle APK',
        '26536_candidate_app_source.tar.gz.sha256',
    ]
    for token in required:
        if token not in text:
            raise ValueError('preserved 26535-procedure anchor missing: '+token)
    # Native proofs must occur before the sanitized validator.
    order = [
        text.index('assert_cpp_deps_exact "$ROOT" post'),
        text.index('26536_postbuild_native_dependency_manifest_check.txt'),
        text.index(MARKER),
        text.index('python3 "$VALIDATE" --base "$BASE" --candidate "$POSTCHECK"'),
    ]
    if order != sorted(order):
        raise ValueError('Gate 5 proof ordering drift')
    return text

def update_manifest(text: str, patched_sha: str) -> str:
    old = EXPECTED_V1_SHA256 + '  ./' + str(TARGET)
    if text.splitlines().count(old) != 1:
        raise ValueError('original build-script handoff hash entry count drift')
    new = patched_sha + '  ./' + str(TARGET)
    out = text.replace(old, new, 1)
    if old in out:
        raise ValueError('original build-script hash entry survived')
    return out

def self_test() -> None:
    sample = f'''#!/usr/bin/env bash\n{BRANCH_BLOCK}x\n{OLD_PASS}\n{OLD_GATE5}\n'''
    sample += '\n'.join([
        'git diff --binary --no-ext-diff -- app/src/main',
        'git diff --binary --no-ext-diff -R -- app/src/main',
        '--fuzz=0 --no-backup-if-mismatch',
        'PRE-BUILD SAFETY PROOF PASSED',
        './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
        './gradlew :app:assembleDebug --stacktrace',
        'assert_cpp_deps_exact "$ROOT" post',
        '26536_postbuild_native_dependency_manifest_check.txt',
        'expected exactly one Gradle APK',
        '26536_candidate_app_source.tar.gz.sha256',
    ]) + '\n'
    # reorder the sample so native proofs precede Gate5 as in real script
    sample = sample.replace(OLD_GATE5+'\n', '')
    anchor = '26536_postbuild_native_dependency_manifest_check.txt\n'
    sample = sample.replace(anchor, anchor + OLD_GATE5 + '\n')
    p = patch_text(sample)
    assert MARKER in p
    assert 'git branch local-safety-26535-before-26536' not in p
    assert OLD_GATE5 not in p
    fake = sha256_bytes(p.encode())
    m = EXPECTED_V1_SHA256 + '  ./' + str(TARGET) + '\nabc  ./other\n'
    m2 = update_manifest(m, fake)
    assert fake + '  ./' + str(TARGET) in m2
    try:
        patch_text(p)
    except ValueError as e:
        assert 'already present' in str(e)
    else:
        raise AssertionError('double-patch rejection failed')
    print('PASS: 26536 V1.2 exact-26535-procedure overlay self-test')

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--self-test', action='store_true')
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    if a.self_test:
        self_test(); return 0
    raw = TARGET.read_bytes()
    actual = sha256_bytes(raw)
    if actual != EXPECTED_V1_SHA256:
        raise SystemExit('FAIL: exact original 26536 V1 build script SHA256 mismatch: '+actual)
    patched = patch_text(raw.decode('utf-8')).encode('utf-8')
    patched_sha = sha256_bytes(patched)
    updated = update_manifest(HANDOFF.read_text(encoding='utf-8'), patched_sha)
    if a.check:
        print('PASS: exact original 26536 V1 input + no-backup/Gate5 anchors verified')
        print('PATCHED_SHA256='+patched_sha)
        return 0
    tmp = TARGET.with_name(TARGET.name+'.v1_2_tmp')
    tmp.write_bytes(patched); os.replace(tmp, TARGET)
    htmp = HANDOFF.with_name(HANDOFF.name+'.v1_2_tmp')
    htmp.write_text(updated, encoding='utf-8'); os.replace(htmp, HANDOFF)
    print('PASS: V1.2 removed backup branch creation')
    print('PASS: V1.2 corrected Gate 5 validation boundary only')
    print('PASS: original 26535-style build gates retained')
    print('PATCHED_SHA256='+patched_sha)
    return 0

if __name__ == '__main__':
    sys.exit(main())
