#!/usr/bin/env python3
"""26888 executed generator, phase domain and exact inherited 17-stage runner contract."""
from pathlib import Path
import hashlib,re,sys,subprocess
R=Path(__file__).resolve().parents[1]
source=(R/'generate_26888_build.py').read_text()
assert 'f969d504a59a95c8304e7cc4be6beea3fc404cb6c52e9aba228bfbb694486d56' in source
assert "parent=R/'build_26887_iris_rawr.sh'" in source
assert 'historical_26886_from_26887' in source and 'historical_26887_replayed' in source
assert '26887_FORWARD_FULL_INDEX.patch' in source and '26888_FORWARD_FULL_INDEX.patch' in source
assert 'verify_26888_semantics.py' in source and 'verify_26888_patches.py' in source
assert 'verify_26888_expanded_glsl.py' in source
stages=('verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay')
parent=R/'build_26887_iris_rawr.sh'
if parent.is_file():
 assert hashlib.sha256(parent.read_bytes()).hexdigest()=='f969d504a59a95c8304e7cc4be6beea3fc404cb6c52e9aba228bfbb694486d56'
run=R/'build_26888_iris_rawr.sh'
if '--generated' in sys.argv:
 assert sys.argv[1:]==['--generated']
 assert run.is_file()
 body=run.read_text()
 have=tuple(x for x in re.findall(r'\n([a-z_]+)\(\)\{',body) if x in stages)
 assert have==stages,have
 assert body.count('git apply --reverse "$ROOT/26887_FORWARD_FULL_INDEX.patch"')>=1
 assert 'historical_26887_replayed' in body
 assert 'verify_26887_semantics.py "$WORK/historical_26886_from_26887" "$WORK/historical_26887_replayed"' in body
 assert 'verify_26888_semantics.py "$NEW_BASE" "$NEW_CAND"' in body
 assert "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]'" in body
 assert './gradlew :app:assembleDebug --stacktrace' in body
 assert 'PRE-BUILD SAFETY PROOF PASSED' in body
 assert body.index('verify_package\nverify_scope\nobtain_authority\nmake_candidate')>0
 expected=(R/'26888_GENERATED_BUILD_SHA256.txt').read_text().split('  ',1)[0]
 assert hashlib.sha256(run.read_bytes()).hexdigest()==expected
 # An unexpected byte change must invalidate identity even if Bash syntax remains valid.
 assert hashlib.sha256((body+'\n# tamper').encode()).hexdigest()!=expected
 print('PASS actual deterministic 26888 17-stage inherited runner, 26887 historical rollback, all compiler commands, exact SHA and negative tamper')
else:
 assert sys.argv[1:]==[]
 print('PASS 26888 generator-parent pin, historical source-domain/patch anchors and validated successor modules')
