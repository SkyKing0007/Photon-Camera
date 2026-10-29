#!/usr/bin/env python3
"""Archive the EXACT executed Photon guarded runner with successful-build evidence.

Run once AFTER the unchanged guarded build and single-APK verification and BEFORE
upload-artifact. The workflow already uploads build_<VERSION>_iris_rawr_outputs/.
No rewriting of a generated runner and no modifications to the 17 stages.
"""
import argparse
import hashlib
import json
import os
import pathlib
import re
import shutil
import sys
import tarfile
import io


def fail(reason):
    raise SystemExit('PHOTON RUNNER EVIDENCE FAIL: ' + reason)


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as fp:
        for chunk in iter(lambda: fp.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def safe_file(path):
    if not path.is_file() or path.is_symlink() or path.stat().st_size == 0:
        fail(f'missing, empty, or symlinked: {path}')
    return path


def main():
    p = argparse.ArgumentParser()
    p.add_argument('build', type=int)
    p.add_argument('--root', type=pathlib.Path, default=pathlib.Path('.'))
    p.add_argument('--expected-sha256', required=True)
    args = p.parse_args()
    version = str(args.build)
    root = args.root.resolve()
    out = root / f'build_{version}_iris_rawr_outputs'
    runner = safe_file(root / f'build_{version}_iris_rawr.sh')
    generated = safe_file(root / f'{version}_GENERATED_BUILD_SHA256.txt')
    tarball = safe_file(out / f'{version}_candidate_app_source.tar.gz')
    tarreceipt = safe_file(out / f'{version}_candidate_app_source.tar.gz.sha256')
    manifest = safe_file(out / f'{version}_candidate_full_app.sha256')
    compiler = safe_file(out / f'{version}_COMPILER_STATUS.txt')
    apkreceipt = safe_file(out / f'{version}_APK.sha256')
    expected = args.expected_sha256.lower()
    if not re.fullmatch(r'[0-9a-f]{64}', expected):
        fail('expected runner SHA-256 must be 64 hex characters')
    actual = digest(runner)
    if actual != expected:
        fail(f'actual runner SHA-256 {actual} != pinned {expected}')
    lines = generated.read_text().splitlines()
    runnername = runner.name
    if not any(re.fullmatch(r'[0-9a-f]{64}  ' + re.escape(runnername), line) and line[:64] == actual for line in lines):
        fail('generated runner SHA receipt does not pin the exact executed runner')
    tarsha = digest(tarball)
    tarlines = tarreceipt.read_text().splitlines()
    if not any(line.split()[:1] == [tarsha] and pathlib.Path(line.split()[-1]).name == tarball.name for line in tarlines if line.split()):
        fail('compiled candidate TAR checksum receipt mismatch')
    rows = manifest.read_text().splitlines()
    if not rows or any(not re.fullmatch(r'[0-9a-f]{64}  .+', line) for line in rows):
        fail('missing or invalid compiled candidate SHA-256 manifest')
    # Validate the ACTUAL compiled TAR members against the exact full manifest.
    expected_files = {}
    for line in rows:
        sha, rel = line.split('  ', 1)
        if rel in expected_files or rel.startswith('/') or '..' in pathlib.PurePosixPath(rel).parts or not rel.startswith('app/'):
            fail(f'duplicate, unsafe, or non-app manifest path: {rel}')
        expected_files[rel] = sha
    actual_files = set()
    with tarfile.open(tarball, mode='r:gz') as tf:
        for member in tf:
            if member.isdir():
                continue
            if not member.isfile() or member.name not in expected_files or member.name in actual_files:
                fail(f'unexpected, duplicated, or nonregular compiled TAR member: {member.name}')
            fp = tf.extractfile(member)
            if fp is None:
                fail(f'cannot read compiled TAR file: {member.name}')
            h = hashlib.sha256()
            for chunk in iter(lambda: fp.read(1024 * 1024), b''):
                h.update(chunk)
            if h.hexdigest() != expected_files[member.name]:
                fail(f'compiled TAR/source manifest byte mismatch: {member.name}')
            actual_files.add(member.name)
    if actual_files != set(expected_files):
        fail(f'compiled TAR/manifest count or membership mismatch: missing {len(set(expected_files)-actual_files)}')
    cs = compiler.read_text()
    for required in ('REAL GLSL COMPILE: PASS', 'REAL SPIR-V VALIDATION: PASS', 'REAL KOTLIN COMPILE: PASS', 'REAL JAVA COMPILE: PASS', 'NATIVE/NDK COMPILE: PASS', 'FULL ANDROID ASSEMBLE: PASS', 'POST-BUILD INVARIANCE: PASS'):
        if required not in cs:
            fail(f'missing compiler proof {required}')
    if not apkreceipt.read_text().strip():
        fail('empty APK SHA receipt')
    job = os.environ.get('GITHUB_JOB', '').strip()
    run_id = os.environ.get('GITHUB_RUN_ID', '').strip()
    commit = os.environ.get('GITHUB_SHA', '').strip()
    branch = os.environ.get('GITHUB_REF_NAME', '').strip()
    if not (run_id.isdecimal() and re.fullmatch(r'[a-fA-F0-9]{40}', commit) and job and branch == 'experimental-clean-photon-rebuild'):
        fail('not a confirmed Actions job on the experimental branch')
    archive = out / 'exact_generated_runner'
    archive.mkdir(parents=True, exist_ok=True)
    target = archive / runner.name
    shutil.copyfile(runner, target)
    shutil.copyfile(generated, archive / generated.name)
    if digest(target) != actual:
        fail('archived runner bytes differ from executed runner')
    receipt = archive / 'EXACT_EXECUTED_RUNNER.sha256'
    receipt.write_text(f'{actual}  {runner.name}\n')
    evidence = {
        'version_build': args.build,
        'run_id': run_id,
        'job': job,
        'branch': branch,
        'commit_sha': commit,
        'runner_file': runner.name,
        'runner_sha256': actual,
        'candidate_tar_file': tarball.name,
        'candidate_tar_sha256': tarsha,
        'candidate_manifest_file': manifest.name,
        'candidate_manifest_file_sha256': digest(manifest),
        'candidate_manifest_entry_count': len(rows),
        'compiler_status_file_sha256': digest(compiler),
        'apk_receipt_sha256': digest(apkreceipt),
    }
    (archive / 'SUCCESSFUL_ACTIONS_EVIDENCE.json').write_text(json.dumps(evidence, indent=2, sort_keys=True) + '\n')
    print(f'PASS: archived exact executed Photon {version} runner SHA={actual}; compiled candidate TAR SHA={tarsha}; manifest entries={len(rows)}')


if __name__ == '__main__':
    main()
