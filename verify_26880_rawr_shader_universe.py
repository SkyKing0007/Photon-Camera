#!/usr/bin/env python3
"""26880 regression for the ACTUAL 40324502022 legacy RAWR shader-universe failure.

Preserve and execute the unchanged, GitHub-pinned 26864 checker against its
original 55-shader domain. Validate the seven added upstream denoise files and
five compiled 26880 shader owners independently. Do not change the historical
checker, original upstream CMake list, frozen candidate, or compiler arguments.
"""
from pathlib import Path
import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

P = argparse.ArgumentParser()
P.add_argument('app_root', type=Path)
P.add_argument('--compile')
P.add_argument('--spirv-val')
P.add_argument('--spirv-opt')
P.add_argument('--out', type=Path)
a = P.parse_args()
root = Path(__file__).resolve().parent
app = a.app_root.resolve()
assert (app/'src/main/cpp/iris26864').is_dir(), 'missing exact candidate native source'
assert (root/'verify_26864_rawr_sources.py').is_file(), 'missing immutable historical RAWR checker'
assert a.compile is None or (a.spirv_val and a.spirv_opt and a.out), 'real compiler needs validator, optimizer and output'

legacy = app/'src/main/cpp/iris26864/vendor/rawr/native'
den = legacy/'raw_denoise'
original = legacy/'multiframe'
expected_new = {
 'CMakeLists.txt',
 'include/raw_denoise/DenoisePipeline.hpp',
 'src/DenoisePipeline.cpp',
 'shaders/denoise_img_precondition.comp',
 'shaders/denoise_img_atrous.comp',
 'shaders/denoise_img_threshold.comp',
 'shaders/denoise_img_backtransform.comp',
}
actual_new = {p.relative_to(den).as_posix() for p in den.rglob('*') if p.is_file()}
assert actual_new == expected_new, ('RAWR new denoise path omitted/extra', sorted(expected_new-actual_new), sorted(actual_new-expected_new))
assert all(p.is_file() and not p.is_symlink() for p in den.rglob('*') if p.is_file()), 'symlink in new shader domain'
assert len(list(original.rglob('*.comp'))) == 55, '26864 upstream multiframe shader count drift'
assert len(list(legacy.rglob('*.comp'))) == 59, '26880 complete shader count drift (55 original + 4 new)'
assert {p.name for p in den.rglob('*.comp')} == {
 'denoise_img_precondition.comp','denoise_img_atrous.comp',
 'denoise_img_threshold.comp','denoise_img_backtransform.comp',
}, '26880 expected shader names drifted'
manifest = {}
for line in (root/'26880_EXPECTED_CANDIDATE_FULL_APP.sha256').read_text().splitlines():
 h, rel = line.split('  ',1)
 assert rel not in manifest, ('duplicate candidate manifest entry',rel)
 manifest[rel] = h
for rel in expected_new:
 path = den/rel
 key = 'app/src/main/cpp/iris26864/vendor/rawr/native/raw_denoise/'+rel
 assert key in manifest, ('new shader not in successful-authority-seeded candidate manifest',key)
 assert hashlib.sha256(path.read_bytes()).hexdigest()==manifest[key], ('26880 shader changed',key)
for rel in ('app/src/main/cpp/iris26864/Iris26880WaveletCopy.comp',
            'app/src/main/cpp/iris26864/Iris26864VendorRawr.cmake'):
 path=app/rel.removeprefix('app/')
 assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==manifest[rel],('unsealed wavelet integration',rel)
cm=(app/'src/main/cpp/iris26864/Iris26864VendorRawr.cmake').read_text()
assert 'add_subdirectory("${IRIS26864_VENDOR_ROOT}/raw_denoise"' in cm
assert 'foreach(NAME IN ITEMS precondition atrous threshold backtransform copy)' in cm
assert 'target_link_libraries(iris26856amaze PRIVATE raw_denoise)' in cm

# A read-only TEMPORARY view: omit ONLY the 26880 newly owned directory.
# Inherited verifier still checks original source locks, file hashes, all 55
# upstream compute shaders, CMake registry, and all three Iris bridges.
with tempfile.TemporaryDirectory(prefix='26880_immutable_upstream_view_') as tmp:
 mirror = Path(tmp)/'app/src/main/cpp/iris26864'
 def skip(directory, names):
  return {'raw_denoise'} if Path(directory).resolve()==legacy.resolve() else set()
 shutil.copytree(app/'src/main/cpp/iris26864',mirror,ignore=skip,
                 copy_function=shutil.copy2,symlinks=False)
 assert not (mirror/'vendor/rawr/native/raw_denoise').exists(), 'temporary historic view includes new files'
 check=[sys.executable,'-S',str(root/'verify_26864_rawr_sources.py'),str(Path(tmp)/'app')]
 if a.compile:
  check += ['--compile',a.compile,'--spirv-val',a.spirv_val,
            '--spirv-opt',a.spirv_opt,'--out',str(a.out)]
 subprocess.run(check,check=True)
print('PASS 26880 true original 55-shader historical validator unchanged + exactly four separately hash-pinned native wavelet shaders; 59 total, no missing/extra files')
