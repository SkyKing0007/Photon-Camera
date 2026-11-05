#!/usr/bin/env python3
"""Verify a SHA256 archive against an ORIGINAL successful artifact receipt,
without dereferencing the archived runner's old absolute workspace filename.
Requires two exact CLI operands: extracted archive and its archived receipt.
Keep the ORIGINAL receipt byte-identical and fail closed on any ambiguity.
"""
import hashlib
import re
import sys
from pathlib import Path, PurePosixPath

NAME = '26901_historical_candidate_app_source.tar.gz'
OUTDIR = 'build_26902_iris_rawr_outputs'


def verify(archive, receipt):
    a, r = Path(archive), Path(receipt)
    if (a.name != NAME or r.name != NAME + '.sha256' or
            a.parent.resolve() != r.parent.resolve() or
            a.parent.name != OUTDIR or a.is_symlink() or r.is_symlink() or
            not a.is_file() or a.stat().st_size == 0 or
            not r.is_file() or r.stat().st_size == 0):
        raise ValueError('missing/incorrect relocated 26901 archive or original receipt')
    raw = r.read_bytes()
    match = re.fullmatch(rb'([0-9a-f]{64})  ([^\r\n\x00]+)\n?', raw)
    if match is None:
        raise ValueError('historical 26901 archived receipt must have exactly one SHA256 filename row')
    expected = match.group(1).decode('ascii')
    old_name = match.group(2).decode('utf-8', 'strict')
    p = PurePosixPath(old_name)
    if (not p.is_absolute() or p.name != NAME or p.parent.name != OUTDIR or
            '..' in p.parts or '.' in p.parts or not old_name.startswith('/home/runner/work/')):
        raise ValueError('original historical receipt does not identify successful 26902 archive')
    # The embedded old path is METADATA ONLY. Never open or trust it as filesystem path.
    h = hashlib.sha256()
    with a.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024*1024), b''):
            h.update(chunk)
    if h.hexdigest() != expected:
        raise ValueError('actual extracted historical 26901 archive SHA256 mismatch')
    return h.hexdigest()


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit('USAGE: verify_26903_v2_archive_receipt.py <extracted-tar.gz> <original-receipt.sha256>')
    try:
        digest = verify(sys.argv[1], sys.argv[2])
    except (OSError, UnicodeError, ValueError) as exc:
        sys.exit('BLOCK historical 26901 archive/receipt validation: ' + str(exc))
    print('PASS actual relocated 26901 historical TAR SHA256=' + digest + ' via unchanged successful 26902 archived receipt (old absolute filename NOT dereferenced)')
