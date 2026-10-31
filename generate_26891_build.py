#!/usr/bin/env python3
"""26891 successor generator from EXACT 26890 SUCCESSFUL EXECUTED 17-stage runner.
No prior runner is substituted; all historical source validators retain original
historical successful bytes. The 26891 correction is 6 exact pre-frozen paths.
"""
from pathlib import Path
import hashlib,re,sys
R=(Path(sys.argv[1]) if len(sys.argv)>1 else Path('.')).resolve()
P=R/'build_26890_iris_rawr.sh'
assert P.is_file(),'restore exact 26890 executed runner before generation'
SHA90='525b56e735d24b24461cf2575bdfcdfe90b242ec87514b9ddfcaf83c442ee3df'
assert hashlib.sha256(P.read_bytes()).hexdigest()==SHA90,'26890 executed runner SHA drift'
s=P.read_text()
STAGES=('verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay')
rex=re.compile(r'\n([a-z_]+)\(\)\{')
assert tuple(x for x in rex.findall(s) if x in STAGES)==STAGES

def once(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a))
 s=s.replace(a,b,1)
def stage(name):
 a=s.index('\n'+name+'(){')+1;b=s.index('\n}',a)+2
 return s[a:b]
def edit(name,fn):
 global s
 a=stage(name);b=fn(a)
 assert b.startswith(name+'(){') and b.endswith('}') and b!=a
 assert s.count(a)==1
 s=s.replace(a,b,1)
def append(body,extra):return body[:-2]+'\n'+extra.strip('\n')+'\n}'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()

# New successful artifact becomes authority; historical 26890 source/runner
# remains the verification authority with unchanged stage order and compilers.
replacements=[
 ('REPO_SCAFFOLD_BASE_COMMIT="17366e5db6359bc68e6098620adb72fd4b3aab0f"','REPO_SCAFFOLD_BASE_COMMIT="90faa0f88ada86b030e24b6e10b6b1e4d762e3f2"'),
 ('RUNTIME_ARTIFACT_ID="12996413398"; RUNTIME_ACTIONS_RUN="41096197467"','RUNTIME_ARTIFACT_ID="13024439725"; RUNTIME_ACTIONS_RUN="41156125594"'),
 ('RUNTIME_AUTHORITY_COMMIT="17366e5db6359bc68e6098620adb72fd4b3aab0f"','RUNTIME_AUTHORITY_COMMIT="90faa0f88ada86b030e24b6e10b6b1e4d762e3f2"'),
 ('RUNTIME_ARTIFACT_SHA="f04c331fc93159ff44fe685f3de90ae6c28a6be4adec9144b1593d6cdea3e0e2"','RUNTIME_ARTIFACT_SHA="14d04be706379ad65966adbb0a343bbc6a3e35275455403ba949c13d8cdde681"'),
 ('RUNTIME_TAR_SHA="f36462930c90dffe75cc953b733c6c47f271ebd9de5a54b8c918c2bd8ad1b76f"','RUNTIME_TAR_SHA="6b7cc1377928ae384b95e0b862169f38d0e278cf90df8bdeb56cc9d30397c0fa"'),
 ('VERSION_NAME="0.9726890"; VERSION_BUILD="26890"','VERSION_NAME="0.9726891"; VERSION_BUILD="26891"'),
 ('OUT="$ROOT/build_26890_iris_rawr_outputs"; WORK="$ROOT/.build_26890_iris_rawr_work"','OUT="$ROOT/build_26891_iris_rawr_outputs"; WORK="$ROOT/.build_26891_iris_rawr_work"'),
 ('ARTZIP="$WORK/26889_artifact.zip"; ARTDIR="$WORK/artifact_26889"','ARTZIP="$WORK/26890_artifact.zip"; ARTDIR="$WORK/artifact_26890"'),
 ('BASE="$WORK/exact_successful_26889_compiled_candidate"; CAND="$WORK/candidate_26890"','BASE="$WORK/exact_successful_26890_compiled_candidate"; CAND="$WORK/candidate_26891"'),
 ('# IRIS_26890_AUTHORITATIVE_ACTIONS_STAGE_ORDER','# IRIS_26891_AUTHORITATIVE_ACTIONS_STAGE_ORDER'),
]
for a,b in replacements:once(a,b)
# Only new receipts use 26891 names; actual *historical* artifact locations
# must remain 26890.
s=s.replace('$OUT/26890_','$OUT/26891_')

def package(p):
 return append(p,''' test -f TRIGGER_26891.txt && grep -Fx 'RUN_26891_B_OFF_HDRQ_RAWR_NORMALIZE_PRESERVE_26890_V1' TRIGGER_26891.txt >/dev/null || fail '26891 trigger drift'
 python3 -S stage_26891_root.py
 sha256sum -c 26891_HANDOFF_HASHES.sha256 >/dev/null || fail '26891 sealed handoff tampered'
 python3 -S -m py_compile generate_26891_build.py verify_26891_candidate.py verify_26891_semantics.py verify_26891_patches.py stage_26891_root.py verify_26891_expanded_glsl.py test_26891_negative_tamper.py photon_26891_replay_exact_26890_workflow.py
 test "$(find handoff_payload_26891 -type f | wc -l)" -eq 6 || fail '26891 six-source allowlist drift'
''')
edit('verify_package',package)
edit('verify_scope',lambda _s:'''verify_scope(){
 [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail 'wrong branch'
 git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD || fail 'successful 26890 authority not ancestor'
 [[ -z "$(git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD -- app/src app/version.properties)" ]] || fail 'unintended committed live runtime delta'
 [[ -z "$(git status --porcelain -- app/src app/version.properties)" ]] || fail 'uncommitted live runtime delta'
 diff -u 26891_REPOSITORY_UPLOAD_ALLOWLIST.txt <(git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | LC_ALL=C sort) >/dev/null || fail '26891 repository upload scope drift'
 [[ "$(sha build_26890_iris_rawr.sh)" == '525b56e735d24b24461cf2575bdfcdfe90b242ec87514b9ddfcaf83c442ee3df' ]] || fail 'actual executed successful 26890 runner drift'
 pass '26891 committed-only scope, exact successful 26890 runner and generator retained'
}''')
edit('obtain_authority',lambda _s:'''obtain_authority(){
 [[ -n "$TOKEN" ]] || fail 'GITHUB_TOKEN missing'
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
  "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/runs/${RUNTIME_ACTIONS_RUN}" -o "$WORK/26890_run.json"
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
  "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}" -o "$WORK/26890_artifact_metadata.json"
 python3 -S - "$WORK/26890_run.json" "$WORK/26890_artifact_metadata.json" <<'PY_AUTH_91'
import json,sys
run=json.load(open(sys.argv[1])); art=json.load(open(sys.argv[2]))
assert run['id']==41156125594 and run['conclusion']=='success' and run['head_sha']=='90faa0f88ada86b030e24b6e10b6b1e4d762e3f2' and run['head_branch']=='experimental-clean-photon-rebuild'
assert art['id']==13024439725 and art.get('expired') is False and art.get('digest')=='sha256:14d04be706379ad65966adbb0a343bbc6a3e35275455403ba949c13d8cdde681'
print('PASS actual successful 26890 run/artifact/digest')
PY_AUTH_91
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
  "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"
 [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail '26890 artifact SHA mismatch'
 unzip -q "$ARTZIP" -d "$ARTDIR"
 local T="$ARTDIR/build_26890_iris_rawr_outputs/26890_candidate_app_source.tar.gz"
 [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail '26890 actual compiled TAR mismatch'
 local EXEC="$ARTDIR/build_26890_iris_rawr_outputs/exact_generated_runner/build_26890_iris_rawr.sh"
 [[ -f "$EXEC" && "$(sha "$EXEC")" == '525b56e735d24b24461cf2575bdfcdfe90b242ec87514b9ddfcaf83c442ee3df' ]] || fail '26890 executed runner mismatch'
 cmp -s "$EXEC" "$ROOT/build_26890_iris_rawr.sh" || fail 'derived 26890 runner not identical to actual executed'
 for k in 'REAL GLSL COMPILE: PASS' 'REAL SPIR-V VALIDATION: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS';do
  grep -F "$k" "$ARTDIR/build_26890_iris_rawr_outputs/26890_COMPILER_STATUS.txt" >/dev/null || fail "26890 compiler receipt missing $k"
 done
 mkdir -p "$BASE";tar -xzf "$T" -C "$BASE"
 [[ "$(find "$BASE/app" -type f | wc -l)" -eq 2025 ]] || fail '26890 compiled file count mismatch'
 (cd "$BASE" && sha256sum -c "$ROOT/26891_BASE_FULL_APP.sha256" >/dev/null) || fail '26890 source SHA manifest mismatch'
 cmp -s "$ARTDIR/build_26890_iris_rawr_outputs/26890_candidate_full_app.sha256" "$ROOT/26891_BASE_FULL_APP.sha256" || fail '26890 Actions candidate manifest mismatch'
 pass 'successful 26890 artifact, runner and 2025 compiled files proven'
}''')
# Reproduce the actual 26890 generator against its OWN 26889 source before
# transforming 26891. All older historical checks remain in its exact body.
old=stage('make_candidate')
assert s.count(old)==1
s=s.replace(old,old.replace('make_candidate(){','historical_26890_make_candidate(){',1),1)
new='''
make_candidate(){
 local H89="$WORK/historical_26889_from_26890" H90="$WORK/historical_26890_replayed"
 cp -a "$BASE" "$H89"; git -C "$H89" init -q
 (cd "$H89" && git apply --check --reverse "$ROOT/26890_FORWARD_FULL_INDEX.patch" && \\
  git apply --reverse "$ROOT/26890_FORWARD_FULL_INDEX.patch" && \\
  sha256sum -c "$ROOT/26890_BASE_FULL_APP.sha256" >/dev/null) || fail '26890 original-source rollback failed'
 rm -rf "$H89/.git"
 ( local BASE="$H89" CAND="$H90"; historical_26890_make_candidate )
 diff -qr "$H90/app" "$BASE/app" >/dev/null || fail 'original generated 26890 candidate != actual compiled 26890'
 python3 -S verify_26890_candidate.py "$H89" "$BASE"
 python3 -S verify_26890_semantics.py "$H89" "$BASE"
 python3 -S verify_26890_expanded_glsl.py "$BASE"
 python3 -S verify_26890_patches.py "$H89" "$BASE" 26890_FORWARD_FULL_INDEX.patch 26890_ROLLBACK_FULL_INDEX.patch
 python3 -S test_26890_negative_tamper.py "$H89" "$BASE"
 python3 -S test_26890_tone_math.py
 python3 -S verify_26891_candidate.py "$BASE" "$CAND" --transform
 python3 -S verify_26891_semantics.py "$BASE" "$CAND"
}
'''
assert '\nverify_successful_mechanics(){' in s
s=s.replace('\nverify_successful_mechanics(){',new+'\nverify_successful_mechanics(){',1)
assert tuple(x for x in rex.findall(s) if x in STAGES)==STAGES

def mechanics(body):
 body=body.replace('verify_26890_candidate.py "$BASE" "$CAND"','verify_26891_candidate.py "$BASE" "$CAND"')
 body=body.replace('verify_26890_semantics.py "$BASE" "$CAND"','verify_26891_semantics.py "$BASE" "$CAND"')
 body=body.replace('"$ARTDIR/build_26889_iris_rawr_outputs/26888_modified_shader_spirv/Iris26887BOffHdrqMerge_prod.spv"',
                   '"$ARTDIR/build_26890_iris_rawr_outputs/26888_modified_shader_spirv/Iris26887BOffHdrqMerge_prod.spv"')
 # Old source proof must use actual original 26889 and compiled 26890 states.
 body=body.replace('"$WORK/historical_26888_from_26889" "$WORK/historical_26889_replayed"',
                   '"$WORK/historical_26888_from_26889" "$WORK/historical_26889_replayed"')
 return append(body,''' [[ "$(sha build_26890_iris_rawr.sh)" == '525b56e735d24b24461cf2575bdfcdfe90b242ec87514b9ddfcaf83c442ee3df' ]] || fail '26890 successfully executed runner drift'
 python3 -S verify_26891_candidate.py "$BASE" "$CAND"
 python3 -S verify_26891_semantics.py "$BASE" "$CAND"
''')
edit('verify_successful_mechanics',mechanics)
# Keep *every* existing inherited GLSL compiler stage. Compile the previous
# 26890-only bespoke changed-tone shader check on its ORIGINAL 26890 sources;
# 26891's exact 26889 tone rollback is covered by successful original owner
# proofs and the inherited 58 native/expanded shader compilation.
def shaders(body):
 body=body.replace('verify_26890_expanded_glsl.py "$CAND"','verify_26890_expanded_glsl.py "$WORK/historical_26890_replayed"')
 # Historical 26890 edited tones still compiled on their exact original bytes.
 # Compile the *current* 26889-restored three GLES310 programs independently.
 return append(body,''' python3 -S verify_26891_expanded_glsl.py "$CAND" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26891_current_reverted_tone_GLES" | tee "$OUT/26891_current_reverted_tone_compiler_receipt.txt"
 grep -Fx 'PASS 26891 THREE current reverted 26889 tone GLES310 REAL PINNED COMPILE' "$OUT/26891_current_reverted_tone_compiler_receipt.txt" >/dev/null || fail '26891 current tone GLSL real compiler missing'
''')
edit('compile_modified_runtime_shaders',shaders)

def patches(body):
 body=body.replace('verify_26890_candidate.py "$BASE" "$CAND"','verify_26891_candidate.py "$BASE" "$CAND"')
 body=body.replace('verify_26890_semantics.py "$BASE" "$CAND"','verify_26891_semantics.py "$BASE" "$CAND"')
 body=body.replace('verify_26890_patches.py "$BASE" "$CAND" 26890_FORWARD_FULL_INDEX.patch 26890_ROLLBACK_FULL_INDEX.patch',
                   'verify_26891_patches.py "$BASE" "$CAND" 26891_FORWARD_FULL_INDEX.patch 26891_ROLLBACK_FULL_INDEX.patch')
 body=body.replace('test_26890_negative_tamper.py "$BASE" "$CAND"','test_26891_negative_tamper.py "$BASE" "$CAND"')
 body=body.replace('26890 8-path full-index forward/rollback','26891 6-path full-index forward/rollback')
 return append(body,''' python3 -S verify_26890_candidate.py "$WORK/historical_26889_from_26890" "$WORK/historical_26890_replayed"
 python3 -S test_26890_negative_tamper.py "$WORK/historical_26889_from_26890" "$WORK/historical_26890_replayed"
''')
edit('verify_candidate_patches',patches)

def safety(body):
 body=body.replace('verify_26890_candidate.py "$BASE" "$CAND"','verify_26891_candidate.py "$BASE" "$CAND"')
 body=body.replace('26890_UNCHANGED_PROTECTED.sha256','26891_UNCHANGED_PROTECTED.sha256')
 body=body.replace('runtime_authority=successful 26889','runtime_authority=successful 26890')
 body=body.replace('verification_mechanics=exact successful 26889','verification_mechanics=exact successful 26890')
 body=body.replace('runtime_changed_files=8 (8 existing files, including version; 0 additions/deletions); 2017 protected, B SDR/UHDR mirrored tone, exact B default and JPEG name, A/Night/Spektra/DNG/vendor protected',
                   'runtime_changed_files=6 (6 existing, 0 additions/deletions); 2019 protected, 26889 exact tone rollback, B-off native HDRQ normalization, B default and A-convention JPEG name retained')
 body=body.replace('infrastructure_delta=26890 strict successor workflow single-trigger + source validators; exact inherited 17-stage compiler+freeze+assemble mechanics',
                   'infrastructure_delta=26891 strict successor workflow single-trigger + source validators; exact inherited 17-stage compiler+freeze+assemble mechanics')
 body=body.replace('protected_source=2017 files byte-identical to successful 26889 compiled candidate; Spektra/A/A+B/Night/LONG/DNG/UHDR protected, B OFF intended changes',
                   'protected_source=2019 files byte-identical to successful 26890 compiled candidate; Spektra/A/A+B/Night/LONG/DNG/UHDR and vendor protected')
 return body
edit('prebuild_safety',safety)

def postbuild(body):
 body=body.replace('verify_26890_candidate.py "$BASE" "$CAND"','verify_26891_candidate.py "$BASE" "$CAND"')
 body=body.replace('26890_EXPECTED_CANDIDATE_FULL_APP.sha256','26891_EXPECTED_CANDIDATE_FULL_APP.sha256')
 body=body.replace('26890_UNCHANGED_PROTECTED.sha256','26891_UNCHANGED_PROTECTED.sha256')
 body=body.replace('cp 26890_FORWARD_FULL_INDEX.patch 26890_ROLLBACK_FULL_INDEX.patch',
                   'cp 26891_FORWARD_FULL_INDEX.patch 26891_ROLLBACK_FULL_INDEX.patch')
 return body
edit('postbuild_proof',postbuild)

def clean(body):
 # The complete 26890 historical tests run on SUCCESSFUL 26890 source bytes.
 body=body.replace('verify_26890_candidate.py "$BASE" "$exp"','verify_26891_candidate.py "$BASE" "$exp"')
 body=body.replace('verify_26890_candidate.py "$BASE" "$replay"','verify_26891_candidate.py "$BASE" "$replay"')
 body=body.replace('verify_26890_semantics.py "$BASE" "$exp"','verify_26891_semantics.py "$BASE" "$exp"')
 body=body.replace('verify_26890_patches.py "$BASE" "$exp" 26890_FORWARD_FULL_INDEX.patch 26890_ROLLBACK_FULL_INDEX.patch',
                   'verify_26891_patches.py "$BASE" "$exp" 26891_FORWARD_FULL_INDEX.patch 26891_ROLLBACK_FULL_INDEX.patch')
 body=body.replace('verify_26890_expanded_glsl.py "$exp"','verify_26890_expanded_glsl.py "$WORK/historical_26890_replayed"')
 body=body.replace('26890_HANDOFF_HASHES.sha256','26891_HANDOFF_HASHES.sha256')
 body=body.replace('26890_GENERATED_BUILD_SHA256.txt','26891_GENERATED_BUILD_SHA256.txt')
 body=body.replace('build_26890_iris_rawr.sh','build_26891_iris_rawr.sh')
 body=body.replace('26890_candidate_app_source.tar.gz','26891_candidate_app_source.tar.gz')
 body=body.replace('26890_EXPECTED_CANDIDATE_FULL_APP.sha256','26891_EXPECTED_CANDIDATE_FULL_APP.sha256')
 body=body.replace('26890_UNCHANGED_PROTECTED.sha256','26891_UNCHANGED_PROTECTED.sha256')
 body=body.replace('26890_FORWARD_FULL_INDEX.patch','26891_FORWARD_FULL_INDEX.patch')
 body=body.replace('26890_ROLLBACK_FULL_INDEX.patch','26891_ROLLBACK_FULL_INDEX.patch')
 body=body.replace('VERSION_NAME=0.9726890','VERSION_NAME=0.9726891')
 body=body.replace('VERSION_BUILD=26890','VERSION_BUILD=26891')
 body=body.replace('verify_26890_candidate.py "$BASE" "$CAND"','verify_26891_candidate.py "$BASE" "$CAND"')
 body=body.replace('verify_26890_semantics.py "$BASE" "$CAND"','verify_26891_semantics.py "$BASE" "$CAND"')
 body=body.replace('verify_26890_expanded_glsl.py "$CAND"','verify_26890_expanded_glsl.py "$WORK/historical_26890_replayed"')
 return append(body,''' python3 -S verify_26891_expanded_glsl.py "$exp"
 python3 -S verify_26891_candidate.py "$BASE" "$exp"
 python3 -S verify_26891_semantics.py "$BASE" "$exp"
 python3 -S test_26891_negative_tamper.py "$BASE" "$exp"
''')
edit('clean_extract_replay',clean)
# Keep old success runner stages identical aside from strictly necessary
# versioned outputs, source callbacks, and historical source operands.
assert tuple(x for x in rex.findall(s) if x in STAGES)==STAGES
for cmd in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace']:
 assert s.count(cmd)>=1,(cmd,s.count(cmd))
assert s.count('          ')>=0
out=R/'build_26891_iris_rawr.sh';out.write_text(s)
print('PASS derived 26891 unchanged 17-stage order/real compilers from exact successful 26890 runner',sha(out))
