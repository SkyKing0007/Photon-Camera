#!/usr/bin/env python3
"""26930 original successful 26929 V2 workflow checks inherited exactly; no old APK rebuild."""
from pathlib import Path
import hashlib,re,sys
R=Path(__file__).resolve().parent
wf=(R/'.github/workflows/build-26930-change-aware.yml').read_text()
assert wf.startswith('name: Photon 26930 V1 - successful 26929 source')
assert wf.count('actions/upload-artifact@v4')==1
assert wf.count('actions/checkout@v5')==1
assert 'experimental-clean-photon-rebuild' in wf
assert re.search(r'(?m)^\s+- TRIGGER_26930\.txt\s*$',wf)
assert wf.count('./gradlew --no-daemon --build-cache :app:assembleDebug')==1
assert 'tee photon_26929_outputs/26929_gradle_assemble.log' not in wf
assert 'tee photon_26930_outputs/26930_gradle_assemble.log' in wf
assert wf.count('id: gradle-cache-26930')==1
assert wf.count('id: native-cache-26930')==1
assert wf.index('build_26929_incremental.py verify-compiled')<wf.index('build_26930_incremental.py fetch')
assert wf.index('build_26930_incremental.py fetch')<wf.index('build_26930_incremental.py prepare')
assert wf.index('build_26930_incremental.py prepare')<wf.index('id: gradle-cache-26930')
assert wf.index('build_26930_incremental.py prepare')<wf.index('id: native-cache-26930')
assert wf.index('id: native-cache-26930')<wf.index('compile_26930_hr_spirv.sh')
assert wf.index('compile_26930_hr_spirv.sh')<wf.index('build_26930_incremental.py verify-compiled')
assert wf.index('build_26930_incremental.py verify-compiled')<wf.rfind(':app:assembleDebug')<wf.index('build_26930_incremental.py finalize')
for cmd in ('verify_26904_v2_safety.py','verify_26904_v3_safety.py',
  'test_26903_v3_archive_receipt.py','test_26903_modes.py .',
  'test_26925_shader_abi.py --payload','test_26925_shader_contract.py --payload',
  'test_26926_sealed_negatives.py','test_26927_sealed_negatives.py',
  'test_26928_sealed_negatives.py','test_26929_sealed_negatives.py',
  'test_26930_sealed_negatives.py','test_26930_shader_contract.py --live',
  'test_26930_chroma_math.py --live','test_26920_vulkan_abi.py --live --cmake',
  'test_26930_shader_shadow.py --live --cmake',
  'verify_26906_native_cache.py preflight','verify_26906_native_cache.py postflight',
  'bash compile_26926_shaders.sh','bash compile_26927_shaders.sh',
  'bash compile_26928_shaders.sh','bash compile_26929_shaders.sh',
  'bash compile_26930_shaders.sh','bash compile_26930_hr_spirv.sh',
  'verify_26916_handoff.py','test_26917_border.py --live',
  'actions/cache/restore@v4','actions/cache/save@v4',
  'build_26930_incremental.py finalize','test_26930_source.py --live'):
 assert cmd in wf,cmd
assert 'test_26903_v3_sealed_negatives.py' not in wf
assert 'test_26922_guard.py' not in wf
# Exact previously executed 26929 V2 workflow prefix, byte-for-byte except
# new workflow name and trigger. Not a rewritten/weakened build procedure.
if '--all' in sys.argv:
 prev=R/'.github/workflows/build-26929-change-aware.yml'
 assert prev.is_file()
 original=prev.read_bytes()
 assert hashlib.sha256(original).hexdigest()=='4a8e582844d7df878f90806f9c3ad68831ba3775805edea6bae342a2ab26ed53'
 p=original.decode()
 p=p.replace('name: Photon 26929 V2 - 26928 compiled source B ON local chroma fine-grain',
  'name: Photon 26930 V1 - successful 26929 source physical-LSC chroma noise and natural fine grain',1)
 p=p.replace('      - TRIGGER_26929.txt','      - TRIGGER_26930.txt',1)
 boundary='      - name: Build full 26929 Kotlin/Java/native both ABI Android debug APK with real Gradle compiler'
 assert boundary in p
 assert wf.startswith(p[:p.index(boundary)]),'historical successful workflow prefix mutated'
 assert (R/'TRIGGER_26930.txt').read_text().startswith('RUN_26930_V1_')
for x in ('build_26930_incremental.py','test_26930_source.py','test_26930_chroma_math.py'):
 assert x in wf
executables=set(re.findall(r'\b(?:python3\s+-S\s+|bash\s+)([\w./-]+\.(?:py|sh))\b',wf))|{'./gradlew'}
assert executables==set((R/'26930_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines()),(executables-set((R/'26930_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines()))
if '--all' in sys.argv:
 assert all((R/x).is_file() for x in executables),[x for x in executables if not (R/x).is_file()]
print('PASS 26930 exact successful 26929 V2 historical verification/GLSL prefix, new artifact-first source, one current APK, full pinned compiler gates')
