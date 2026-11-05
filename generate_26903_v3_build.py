#!/usr/bin/env python3
"""V3 repair of FAILED V2 exact runner. No runtime/17-stage compiler changes.
Preserve original V1/V2 source/runner history and relocate their tests onto
original runner bytes. Apply ONLY V3 cumulative-scope/receipt checks.
"""
import hashlib,re,sys
from pathlib import Path
R=Path(sys.argv[1] if len(sys.argv)==2 else '.').resolve()
P=R/'build_26903_iris_rawr.sh'
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
V2='8624b1617ba9156af7501667f95e63e69f5fdf6384cec30ed48ee50a9b828762'
PARENT='348b2d617ed36b40744d15eeba762bb64c589e45327f60f18454d54cbc4c64dc'
assert H(P)==V2, 'BLOCK V3: actual FAILED V2 executed runner bytes not found or changed'
assert H(R/'build_26902_iris_rawr.sh')==PARENT, 'BLOCK V3: successful 26902 original runner not preserved'
s=P.read_text()
STAGES=('verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay')
FUNC=lambda v:tuple(x for x in re.findall(r'(?m)^([a-z_]+)\(\)\{',v) if x in STAGES)
assert FUNC(s)==STAGES
old=s

def change(a,b,count=1):
 global s
 assert s.count(a)==count,('V3 exact anchor missing or ambiguous',a[:140],s.count(a),count)
 s=s.replace(a,b)

def append(name,fragment):
 global s
 a=s.index('\n'+name+'(){')+1;b=s.index('\n}',a)+2
 old_func=s[a:b];assert old_func.endswith('\n}')
 s=s[:a]+old_func[:-2]+'\n'+fragment.strip('\n')+'\n}'+s[b:]

# Critical: V2 strict validator validates the V2 runner SHA in its original
# successful-from-26902 / V1 V2 isolation, NEVER against V3 runner.
change(' python3 -S stage_26903_v2_root.py --runner', ' python3 -S validate_26903_v2_frozen_stage.py',2)
# V2 SHA receipt is deliberately immutable. New live runner has V3 SHA receipt.
change(' sha256sum -c 26903_V2_GENERATED_BUILD_SHA256.txt >/dev/null || fail \'26903 V2 exact generated/EXECUTED runner mismatch\'',
       ' sha256sum -c 26903_V3_GENERATED_BUILD_SHA256.txt >/dev/null || fail \'26903 V3 exact generated/EXECUTED runner mismatch\'')
change('diff -u 26903_V2_CUMULATIVE_REPOSITORY_ALLOWLIST.txt <(git diff --name-only "$REPO_SCAFFOLD_BASE_COMMIT"..HEAD | LC_ALL=C sort)',
       'diff -u 26903_V3_CUMULATIVE_REPOSITORY_ALLOWLIST.txt <(git diff --name-only "$REPO_SCAFFOLD_BASE_COMMIT"..HEAD | LC_ALL=C sort)')
change(" git merge-base --is-ancestor '7619f129b14d8077811fb3b8b414bc97cdb6c449' HEAD || fail '26903 V2 requires exact failed V1 commit as ancestor, no silent source rollback'",
       " git merge-base --is-ancestor '7619f129b14d8077811fb3b8b414bc97cdb6c449' HEAD || fail '26903 V2 requires exact failed V1 commit as ancestor, no silent source rollback'\n git merge-base --is-ancestor 'a8c121fc4ee9f72ee82f0c5dafc6c1652493ffc8' HEAD || fail '26903 V3 requires exact failed V2 commit as ancestor, no silent source rollback'")
append('verify_package', '''
 # V3 strict independent source/runner scope: original failed V1 and V2
 # validators run in their OWN exact original runner contexts.
 python3 -S stage_26903_v3_root.py --runner
 sha256sum -c 26903_V3_HANDOFF_HASHES.sha256 >/dev/null || fail '26903 V3 sealed staged bytes mismatch'
 python3 -S test_26903_v3_archive_receipt.py
 python3 -S test_26903_v3_sealed_negatives.py
 [[ "$(sha TRIGGER_26903_V3.txt)" == "$(printf 'RUN_26903_B_NIGHT_CORRECT_EXECUTED_RUNNER_RECEIPT_V3\\n' | sha256sum | awk '{print $1}')" ]] || fail '26903 V3 immutable only trigger changed'
''')
append('clean_extract_replay', '''
 # Original V2 regression on frozen V2 source and runner + new SHA-sealed V3.
 python3 -S validate_26903_v2_frozen_stage.py
 python3 -S stage_26903_v3_root.py --runner
 python3 -S test_26903_v3_archive_receipt.py
 python3 -S test_26903_v3_sealed_negatives.py
''')
assert FUNC(s)==STAGES
# Hard fail if any actual compiler function's content or final APK assembly
# differs even in a character; these exact stages are successful V2 provenance.
for name in ('prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','obtain_authority','make_candidate','verify_successful_mechanics'):
 def get(t):
  a=t.index('\n'+name+'(){')+1;b=t.index('\n}',a)+2
  return t[a:b]
 assert get(old)==get(s),('V3 altered proven compiler/patch/authority stage',name)
assert s.count('sha256sum -c 26901_historical_candidate_app_source.tar.gz.sha256')==0
assert s.count('verify_26903_v2_archive_receipt.py "$T01"')==1
assert len(re.findall(r'(?m)^\s*\./gradlew :app:assembleDebug --stacktrace',s))==1
assert '26903_V2_CUMULATIVE_REPOSITORY_ALLOWLIST.txt <(git diff' not in s
assert '26903_V3_CUMULATIVE_REPOSITORY_ALLOWLIST.txt <(git diff' in s
assert s.count('python3 -S validate_26903_v2_frozen_stage.py')==3
assert '$ARTDIR/build_26901_iris_rawr_outputs/' not in s
assert '$ARTDIR/build_26900_iris_rawr_outputs/' not in s
assert 'sha256sum -c "$ARTDIR/' not in s
P.write_text(s)
print('PASS V3 ORIGINAL EXACT 17 stages/compiler unchanged, FULL scope, isolated historical V2, runner_SHA='+H(P))
