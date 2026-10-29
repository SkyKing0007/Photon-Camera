#!/usr/bin/env python3
"""26888 guarded successor of actual successful 26887 V4 runner; mandatory 17-stage preservation."""
from pathlib import Path
import hashlib,re,sys
R=(Path(sys.argv[1]) if len(sys.argv)>1 else Path('.')).resolve()
parent=R/'build_26887_iris_rawr.sh'
assert parent.is_file(),'exact successful 26887 runner not present'
original=parent.read_text()
assert hashlib.sha256(parent.read_bytes()).hexdigest()=='f969d504a59a95c8304e7cc4be6beea3fc404cb6c52e9aba228bfbb694486d56', '26887 runner SHA mismatch'
STAGES=('verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay')
regex=re.compile(r'\n([a-z_]+)\(\)\{')
assert tuple(n for n in regex.findall(original) if n in STAGES)==STAGES
body=original

def stage(s,n):
 a=s.index('\n'+n+'(){')+1;b=s.index('\n}',a)+2
 return s[a:b]
def edit(n,fn):
 global body
 old=stage(body,n);new=fn(old)
 assert old!=new and new.startswith(n+'(){') and new.endswith('}'),('bad stage edit',n)
 assert body.count(old)==1
 body=body.replace(old,new,1)
def append(s,add):
 assert s.endswith('\n}')
 return s[:-2]+'\n'+add.strip('\n')+'\n}'
def once(s,a,b):
 assert s.count(a)==1,('anchor cardinality',a,s.count(a))
 return s.replace(a,b,1)

# Only active 26888 identity changes; historical 26887 records and scripts remain byte-identical.
for a,b in (
 ('# Successful 26886 V6 Actions compiled candidate is runtime authority.','# Successful 26887 V4 Actions compiled candidate is runtime authority.'),
 ('REPO_SCAFFOLD_BASE_COMMIT="97bc96161da6854ef5fcaca16b2a1ae9c020f58d"','REPO_SCAFFOLD_BASE_COMMIT="de478c5c3ce85de56ac74be3cbd885c128ebd833"'),
 ('RUNTIME_ARTIFACT_ID="12792447816"; RUNTIME_ACTIONS_RUN="40633283908"','RUNTIME_ARTIFACT_ID="12870194123"; RUNTIME_ACTIONS_RUN="40810858529"'),
 ('RUNTIME_AUTHORITY_COMMIT="97bc96161da6854ef5fcaca16b2a1ae9c020f58d"','RUNTIME_AUTHORITY_COMMIT="de478c5c3ce85de56ac74be3cbd885c128ebd833"'),
 ('RUNTIME_ARTIFACT_SHA="1a2dbc35cf738be42270cb156b083015b323b3829cae67c3ab33e91de5831335"','RUNTIME_ARTIFACT_SHA="70d2ac2780485a5d845fcca02f0cb7c20a7c262249432b633100d4f369365d41"'),
 ('RUNTIME_TAR_SHA="e2a03925cafa2196884fff02d9320f6ac4020823130b896de7166eb77ded144b"','RUNTIME_TAR_SHA="864312c1fa31b03cf0dd208014f35e8749cbeb21de7be64278c683a69acc8912"'),
 ('VERSION_NAME="0.9726887"; VERSION_BUILD="26887"','VERSION_NAME="0.9726888"; VERSION_BUILD="26888"'),
 ('OUT="$ROOT/build_26887_iris_rawr_outputs"; WORK="$ROOT/.build_26887_iris_rawr_work"','OUT="$ROOT/build_26888_iris_rawr_outputs"; WORK="$ROOT/.build_26888_iris_rawr_work"'),
 ('ARTZIP="$WORK/26886_artifact.zip"; ARTDIR="$WORK/artifact_26886"','ARTZIP="$WORK/26887_artifact.zip"; ARTDIR="$WORK/artifact_26887"'),
 ('BASE="$WORK/exact_successful_26886_compiled_candidate"; CAND="$WORK/candidate_26887"','BASE="$WORK/exact_successful_26887_compiled_candidate"; CAND="$WORK/candidate_26888"'),
 ('# IRIS_26887_AUTHORITATIVE_ACTIONS_STAGE_ORDER','# IRIS_26888_AUTHORITATIVE_ACTIONS_STAGE_ORDER'),
):body=once(body,a,b)
# Existing successful 26887 17 stages are preserved in the same order; only
# the new authority, scope and source-era-specific operands are advanced.
body=once(body,'$OUT/26887_COMPILER_STATUS.txt','$OUT/26888_COMPILER_STATUS.txt') if body.count('$OUT/26887_COMPILER_STATUS.txt')==1 else body.replace('$OUT/26887_COMPILER_STATUS.txt','$OUT/26888_COMPILER_STATUS.txt')

edit('verify_package',lambda s:append(s,'''
 test -f TRIGGER_26888.txt && grep -Fx 'RUN_26888_B_OFF_INDEPENDENT_MOTION_SUPPORT_V1' TRIGGER_26888.txt >/dev/null || fail 'wrong exact-byte 26888 trigger'
 python3 -S stage_26888_root.py
 sha256sum -c 26888_HANDOFF_HASHES.sha256 >/dev/null || fail '26888 sealed staged bytes tampered'
 python3 -S -m py_compile generate_26888_build.py verify_26888_candidate.py verify_26888_semantics.py verify_26888_patches.py verify_26888_expanded_glsl.py stage_26888_root.py regressions/26888_successor_contract.py photon_preserve_successful_runner.py
 python3 -S regressions/26888_successor_contract.py
 sha256sum -c 26888_PAYLOAD_SHA256.txt >/dev/null || fail '26888 payload drift'
 test "$(find handoff_payload_26888 -type f | wc -l)" -eq 9 || fail '26888 frozen B-OFF runtime scope drift'
'''))

def scope(s):
 return '''verify_scope(){
 [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail 'wrong branch'
 git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD || fail 'successful 26887 authority not ancestor'
 [[ -z "$(git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD -- app/src app/version.properties)" ]] || fail 'live runtime source modified'
 [[ -z "$(git status --porcelain -- app/src app/version.properties)" ]] || fail 'uncommitted app source drift'
 [[ -z "$(git ls-files -- glsl_static)" ]] || fail 'shader-generated scaffolding tracked'
 diff -u 26888_REPOSITORY_UPLOAD_ALLOWLIST.txt <(git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | LC_ALL=C sort) >/dev/null || fail 'unexpected 26888 source or infrastructure changed path'
 [[ "$(sha build_26887_iris_rawr.sh)" == 'f969d504a59a95c8304e7cc4be6beea3fc404cb6c52e9aba228bfbb694486d56' ]] || fail 'successful 26887 runner drift'
 [[ "$(git rev-parse "$RUNTIME_AUTHORITY_COMMIT:generate_26887_build.py")" == 'f18d4a78940d0d3ef482a8fa33dd613b9cc1dcc2' ]] || fail 'successful 26887 generator blob drift'
 pass '26888 exact successful 26887 SHA authority, protected source and upload scope'
}'''
edit('verify_scope',scope)

def authority(s):
 s=s.replace('26886','26887').replace('2010','2020').replace('26887_BASE_26887_FULL_APP','26888_BASE_26887_FULL_APP')
 for a,b in (
  ('97bc96161da6854ef5fcaca16b2a1ae9c020f58d','de478c5c3ce85de56ac74be3cbd885c128ebd833'),
  ('12792447816','12870194123'),
  ('40633283908','40810858529'),
  ('photon-26886-b-on-rawr-chroma-denoise-false-color','photon-26887-b-off-raw-witness-hdrq-motion'),
  ('1a2dbc35cf738be42270cb156b083015b323b3829cae67c3ab33e91de5831335','70d2ac2780485a5d845fcca02f0cb7c20a7c262249432b633100d4f369365d41'),
  ('3f816088f564bfd575d5dc8e1681b9b1b18ec435de41ed34f2c22df866c5e8fa','f969d504a59a95c8304e7cc4be6beea3fc404cb6c52e9aba228bfbb694486d56'),
 ):
  s=s.replace(a,b)
 s=s.replace('26887_RESOLVED_AUTHORITIES.txt','26888_RESOLVED_AUTHORITIES.txt')
 s=s.replace('photon-26887-b-on-rawr-chroma-denoise-false-color','photon-26887-b-off-raw-witness-hdrq-motion')
 assert '26888_BASE_26887_FULL_APP.sha256' in s
 assert '[[ "$(find "$BASE/app" -type f | wc -l)" -eq 2020 ]]' in s or '-eq 2020' in s
 return s
edit('obtain_authority',authority)

def candidate(s):
 # The original 26887 make_candidate function is executed with its OWN real
 # successful 26886/26887 universes after verified reversal of 26887 patch.
 old=s[len('make_candidate(){'):-2]
 return '''make_candidate(){
 local NEW_BASE="$BASE" NEW_CAND="$CAND"
 local H86="$WORK/historical_26886_from_26887"
 cp -a "$NEW_BASE" "$H86";git -C "$H86" init -q
 (cd "$H86" && git apply --check --reverse "$ROOT/26887_FORWARD_FULL_INDEX.patch" &&
  git apply --reverse "$ROOT/26887_FORWARD_FULL_INDEX.patch" &&
  sha256sum -c "$ROOT/26887_BASE_26886_FULL_APP.sha256" >/dev/null) || fail '26887 successful-source rollback to exact 26886 failed'
 local BASE="$H86" CAND="$WORK/historical_26887_replayed"
'''+old+'''
 diff -qr "$CAND/app" "$NEW_BASE/app" >/dev/null || fail '26887 own successful historical candidate replay changed bytes'
 python3 -S verify_26888_candidate.py "$NEW_BASE" "$NEW_CAND" --root "$ROOT" --transform
 python3 -S verify_26888_semantics.py "$NEW_BASE" "$NEW_CAND"
 python3 -S verify_26888_expanded_glsl.py "$NEW_CAND"
}'''
edit('make_candidate',candidate)

edit('verify_successful_mechanics',lambda s:append(s,'''
 [[ "$(sha build_26887_iris_rawr.sh)" == 'f969d504a59a95c8304e7cc4be6beea3fc404cb6c52e9aba228bfbb694486d56' ]] || fail 'successful 26887 V4 exact generated runner changed'
 [[ "$(git rev-parse "$RUNTIME_AUTHORITY_COMMIT:generate_26887_build.py")" == 'f18d4a78940d0d3ef482a8fa33dd613b9cc1dcc2' ]] || fail 'successful 26887 V4 generator blob changed'
 python3 -S regressions/26888_successor_contract.py --generated
'''))

def shader(s):
 # Prior 26887 shader compiler receives its own successful compiled source.
 s=s.replace('verify_26887_expanded_glsl.py "$CAND"','verify_26887_expanded_glsl.py "$WORK/historical_26887_replayed"')
 s=s.replace('regressions/26886_historical_scope_all_stages.py "$WORK/historical_26884_from_26885" "$WORK/historical_26885_from_26886" "$BASE"', 'regressions/26886_historical_scope_all_stages.py "$WORK/historical_26884_from_26885" "$WORK/historical_26885_from_26886" "$WORK/historical_26886_from_26887"')
 for name in ('verify_26886_candidate.py','verify_26886_semantics.py'):
  s=s.replace(name+' "$WORK/historical_26885_from_26886" "$BASE"',name+' "$WORK/historical_26885_from_26886" "$WORK/historical_26886_from_26887"')
 s=s.replace('verify_26886_expanded_glsl.py "$BASE"','verify_26886_expanded_glsl.py "$WORK/historical_26886_from_26887"')

 return append(s,'''
 python3 -S verify_26888_expanded_glsl.py "$CAND" --compiler "$IRIS26864_GLSLANG" --spirv-val "$(command -v spirv-val)" --spirv-opt "$(command -v spirv-opt)" --out "$OUT/26888_modified_shader_spirv" | tee "$OUT/26888_real_shader_compile_receipt.txt"
 grep -Fx 'PASS pinned REAL glslang 16.5.0/spirv-val/spirv-opt 5 compiled 26888 shader variants' "$OUT/26888_real_shader_compile_receipt.txt" >/dev/null || fail '26888 real modified runtime GLSL compiler receipts missing'
 python3 -S - "$OUT/26888_modified_shader_spirv" <<'PY_26888_SHADER_RECEIPT'
import hashlib,pathlib,sys
p=pathlib.Path(sys.argv[1]);m=p/'26888_REAL_COMPILED_SHADER_SHA256.txt'
assert m.is_file()
lines=m.read_text().splitlines();assert len(lines)==5
assert len(list(p.glob('*.spv')))==5
for ln in lines:
 h,n=ln.split('  ',1);b=(p/n).read_bytes()
 assert len(b)>80 and b[:4]==bytes.fromhex('03022307')
 assert hashlib.sha256(b).hexdigest()==h
print('PASS 26888 exact five SPIR-V receipts')
PY_26888_SHADER_RECEIPT
''')
edit('compile_modified_runtime_shaders',shader)
# Existing native/Java/GLSL/assemble command ordering inherited without changes.
edit('verify_candidate_patches',lambda s:s.replace('26887','26888').replace('17-file','9-file'))

def safety(s):
 s=s.replace('26887','26888').replace('runtime_authority=successful 26886','runtime_authority=successful 26887')
 s=s.replace('runtime_changed_files=17 (7 modified existing files (including version), 10 new B-only runtime files); 2003 protected','runtime_changed_files=9 (5 modified existing including version, 4 B-OFF private additions); 2015 protected')
 s=s.replace('prior_files=2010','prior_files=2020').replace('candidate_files=2020','candidate_files=2024')
 s=s.replace('protected_source=2003 files','protected_source=2015 files')
 s=s.replace('successfully compiled 26886','successfully compiled 26887')
 s=s.replace('protected_source=2015 files byte-identical to successful 26886','protected_source=2015 files byte-identical to successful 26887')
 s=s.replace('verification_mechanics=exact successful 26886 inherited 17 stages','verification_mechanics=exact successful 26887 inherited 17 stages')
 return s
edit('prebuild_safety',safety)
edit('assemble',lambda s:s.replace('26887','26888'))
edit('postbuild_proof',lambda s:s.replace('26887','26888'))

def replay(s):
 # Historical 26886 and 26887 checks get their OWN verified successful bytes.
 s=s.replace('verify_26887_candidate.py "$BASE"', 'verify_26888_candidate.py "$BASE"')
 s=s.replace('verify_26887_semantics.py "$BASE"', 'verify_26888_semantics.py "$BASE"')
 s=s.replace('verify_26887_patches.py "$BASE"', 'verify_26888_patches.py "$BASE"')
 s=s.replace('verify_26887_expanded_glsl.py "$exp"', 'verify_26888_expanded_glsl.py "$exp"')
 # Older 26886 and 26887 validators MUST be bound to their historical source domains.
 s=s.replace('regressions/26886_chroma_controls.py "$WORK/historical_26885_from_26886" "$BASE"', 'regressions/26886_chroma_controls.py "$WORK/historical_26885_from_26886" "$WORK/historical_26886_from_26887"')
 s=s.replace('"$WORK/historical_26885_from_26886" "$BASE" "$ROOT/build_26885_', '"$WORK/historical_26885_from_26886" "$WORK/historical_26886_from_26887" "$ROOT/build_26885_')
 for name in ('verify_26886_candidate.py','verify_26886_semantics.py'):
  s=s.replace(name+' "$WORK/historical_26885_from_26886" "$BASE"',name+' "$WORK/historical_26885_from_26886" "$WORK/historical_26886_from_26887"')
 s=s.replace('verify_26886_expanded_glsl.py "$BASE"','verify_26886_expanded_glsl.py "$WORK/historical_26886_from_26887"')
 s=s.replace('26887_candidate_app_source.tar.gz','26888_candidate_app_source.tar.gz')
 s=s.replace('26887_final_patch_replay','26888_final_patch_replay')
 s=s.replace('26887_EXPECTED_CANDIDATE_FULL_APP.sha256','26888_EXPECTED_CANDIDATE_FULL_APP.sha256')
 s=s.replace('26887_UNCHANGED_PROTECTED.sha256','26888_UNCHANGED_PROTECTED.sha256')
 s=s.replace('26887_FORWARD_FULL_INDEX.patch','26888_FORWARD_FULL_INDEX.patch')
 s=s.replace('26887_ROLLBACK_FULL_INDEX.patch','26888_ROLLBACK_FULL_INDEX.patch')
 s=s.replace('26887_HANDOFF_HASHES.sha256','26888_HANDOFF_HASHES.sha256')
 s=s.replace('26887_GENERATED_BUILD_SHA256.txt','26888_GENERATED_BUILD_SHA256.txt')
 s=s.replace('bash -n build_26887_iris_rawr.sh','bash -n build_26888_iris_rawr.sh')
 s=s.replace('26887_COMPILER_STATUS.txt','26888_COMPILER_STATUS.txt')
 s=s.replace('VERSION_NAME=0.9726887','VERSION_NAME=0.9726888').replace('VERSION_BUILD=26887','VERSION_BUILD=26888')
 # Check source-domain-specific 26887 historical semantic records with correct bytes.
 return append(s,'''
 python3 -S verify_26887_candidate.py "$WORK/historical_26886_from_26887" "$WORK/historical_26887_replayed"
 python3 -S verify_26887_semantics.py "$WORK/historical_26886_from_26887" "$WORK/historical_26887_replayed"
 python3 -S verify_26887_expanded_glsl.py "$WORK/historical_26887_replayed"
 python3 -S verify_26887_patches.py "$WORK/historical_26886_from_26887" "$WORK/historical_26887_replayed" 26887_FORWARD_FULL_INDEX.patch 26887_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26888_candidate.py "$BASE" "$exp" --root "$ROOT"
 python3 -S verify_26888_semantics.py "$BASE" "$exp"
 python3 -S verify_26888_expanded_glsl.py "$exp"
 python3 -S verify_26888_patches.py "$BASE" "$exp" 26888_FORWARD_FULL_INDEX.patch 26888_ROLLBACK_FULL_INDEX.patch
''')
edit('clean_extract_replay',replay)
# Active candidate and immutable receipt references in late stages.
body=body.replace('"$OUT/26887_COMPILER_STATUS.txt"','"$OUT/26888_COMPILER_STATUS.txt"')
# Native/language compiler gates still run same commands, only write current version receipts.
for n in ('compile_languages','compile_native'):
 edit(n,lambda s:s.replace('26887_gradle','26888_gradle'))
assert tuple(n for n in regex.findall(body) if n in STAGES)==STAGES
for term in ('./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac',
             "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]'",
             './gradlew :app:assembleDebug --stacktrace','PRE-BUILD SAFETY PROOF PASSED'):
 assert body.count(term)>=1,('inherited real compilation command lost',term)
# Direct recorder/GLSL source remains user-provided frozen candidate, not repository app/src.
Path(R/'build_26888_iris_rawr.sh').write_text(body)
print('PASS 26888 generated runner:',hashlib.sha256(body.encode()).hexdigest(),'stages',len(STAGES))
