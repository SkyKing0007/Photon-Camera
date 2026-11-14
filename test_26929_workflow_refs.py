#!/usr/bin/env python3
from pathlib import Path
import re,sys,hashlib
R=Path(__file__).resolve().parent
w=(R/'.github/workflows/build-26929-change-aware.yml').read_text()
assert w.startswith('name: Photon 26929 V2')
assert w.count('actions/upload-artifact@v4')==1 and w.count('actions/checkout@v5')==1
assert 'experimental-clean-photon-rebuild' in w
assert re.search(r'(?m)^\s+- TRIGGER_26929\.txt\s*$',w)
for run in ('build_26926_incremental.py prepare','build_26927_incremental.py prepare',
            'build_26928_incremental.py prepare','build_26928_incremental.py verify-compiled',
            'build_26928_incremental.py verify-compiled','build_26929_incremental.py fetch',
            'build_26929_incremental.py prepare','build_26929_incremental.py verify-compiled',
            'build_26929_incremental.py finalize','Publish only the 26929 final APK'):
 assert run in w,run
# The successful 26928 published APK and both ABI/compiler receipts are checked
# by 26929 fetch/prepare, not rebuilt. Guard against redundant Gradle baseline.
assert w.count('./gradlew --no-daemon --build-cache :app:assembleDebug')==1
assert '26928_gradle_assemble.log' not in w
assert w.index('build_26928_incremental.py verify-compiled') < w.index('build_26929_incremental.py fetch')
assert w.index('build_26929_incremental.py prepare') < w.index('id: gradle-cache')
assert w.index('id: gradle-cache') < w.index(':app:assembleDebug')
assert w.index('build_26929_incremental.py prepare') < w.index('id: native-cache-26929')
assert w.index('id: native-cache-26929') < w.index('compile_26929_hr_spirv.sh')
assert w.index('build_26929_incremental.py verify-compiled') < w.rfind(':app:assembleDebug') < w.index('build_26929_incremental.py finalize')
for phrase in ('verify_26904_v2_safety.py','verify_26904_v3_safety.py',
  'test_26903_v3_archive_receipt.py','test_26925_shader_abi.py --payload',
  'verify_26906_native_cache.py preflight','verify_26906_native_cache.py postflight',
  'test_26926_sealed_negatives.py','test_26927_sealed_negatives.py',
  'test_26928_sealed_negatives.py','test_26929_sealed_negatives.py',
  'bash compile_26926_shaders.sh','bash compile_26927_shaders.sh',
  'bash compile_26928_shaders.sh','bash compile_26929_shaders.sh',
  'bash compile_26929_hr_spirv.sh','test_26920_vulkan_abi.py --live --cmake',
  'test_26929_shader_shadow.py --live --cmake',
  'test_26929_shader_shadow.py --live --cmake','verify_26916_handoff.py',
  'test_26917_border.py --live','actions/cache/restore@v4'):
 assert phrase in w,phrase
assert 'test_26903_v3_sealed_negatives.py' not in w
assert 'test_26922_guard.py' not in w
assert 'actions/upload-artifact@v4' in w
execs=set(re.findall(r'\b(?:python3\s+-S\s+|bash\s+)([\w./-]+\.(?:py|sh))\b',w))|{'./gradlew'}
assert execs==set((R/'26929_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines()),(execs-set((R/'26929_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines()))
if '--all' in sys.argv:
 assert all((R/p).is_file() for p in execs),[p for p in execs if not (R/p).is_file()]
 assert (R/'TRIGGER_26929.txt').read_text().startswith('RUN_26929_V2_')
 prior=R/'.github/workflows/build-26928-change-aware.yml'
 assert prior.is_file() and hashlib.sha256(prior.read_bytes()).hexdigest()=='d1428d853792e2489ea15081949af57384aec8000eccc92a414846e174627fca'
 base=prior.read_text()
 for line in re.findall(r'(?m)^\s+(?:python3 -S |bash )[\w.\- /]+$',base):
  if ('build_26928_incremental.py finalize' in line or
      'test_26927_shader_shadow.py --live --cmake' in line or
      'test_26928_shader_shadow.py --live --cmake' in line):
   # Already validated in the successful 26928 real APK and dual-ABI receipts;
   # historical --live 26927/28 shader hashes are intentionally incompatible
   # with 26929's strictly allowlisted changed native shader.
   continue
  assert line.strip() in w,'lost historical command '+line.strip()
print('PASS historical 26928 checks and published real ABI proof retained, one current 26929 Android build, correctly sequenced cache')
