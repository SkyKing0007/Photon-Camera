#!/usr/bin/env python3
"""EXACT 26889 Actions-executed 17-stage successor; no stage substitution.
Historical 26889 runner is recovered byte-for-byte, not approximated by a generator.
"""
from pathlib import Path
import hashlib,re,sys
R=(Path(sys.argv[1]) if len(sys.argv)>1 else Path('.')).resolve()
P=R/'build_26889_iris_rawr.sh'
assert P.is_file(),'must first reconstruct actual executed 26889 runner'
assert hashlib.sha256(P.read_bytes()).hexdigest()=='4070c3a0f47fb043d99ad18a1b2d53a629be26891d1147ef9bfc60d790cb7d73','exact successful 26889 archived runner mismatch'
body=P.read_text()
STAGES=('verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay')
rex=re.compile(r'\n([a-z_]+)\(\)\{')
assert tuple(x for x in rex.findall(body) if x in STAGES)==STAGES

def stage(s,n):
 a=s.index('\n'+n+'(){')+1;b=s.index('\n}',a)+2
 return s[a:b]
def edit(n,f):
 global body
 a=stage(body,n);b=f(a)
 assert a!=b and b.startswith(n+'(){') and b.endswith('}'),('stage',n)
 assert body.count(a)==1
 body=body.replace(a,b,1)
def append(s,extra):return s[:-2]+'\n'+extra.strip('\n')+'\n}'
def once(a,b):
 global body
 assert body.count(a)==1,('anchor',a,body.count(a))
 body=body.replace(a,b,1)
for a,b in (
 ('# Successful 26888 Actions compiled candidate is runtime authority.','# Successful 26889 Actions compiled candidate is runtime authority.'),
 ('REPO_SCAFFOLD_BASE_COMMIT="762f5531def4a880d46e144a0e204eebb5ad1d28"','REPO_SCAFFOLD_BASE_COMMIT="17366e5db6359bc68e6098620adb72fd4b3aab0f"'),
 ('RUNTIME_ARTIFACT_ID="12933881423"; RUNTIME_ACTIONS_RUN="40954102038"','RUNTIME_ARTIFACT_ID="12996413398"; RUNTIME_ACTIONS_RUN="41096197467"'),
 ('RUNTIME_AUTHORITY_COMMIT="762f5531def4a880d46e144a0e204eebb5ad1d28"','RUNTIME_AUTHORITY_COMMIT="17366e5db6359bc68e6098620adb72fd4b3aab0f"'),
 ('RUNTIME_ARTIFACT_SHA="68b368663476be9369e72fc305cbdd571d18e7e1b9df3afb0666859be1400d73"','RUNTIME_ARTIFACT_SHA="f04c331fc93159ff44fe685f3de90ae6c28a6be4adec9144b1593d6cdea3e0e2"'),
 ('RUNTIME_TAR_SHA="22f0679109f38c2ec749b1e403dede337464eecfe3049620f445a73881171bfb"','RUNTIME_TAR_SHA="f36462930c90dffe75cc953b733c6c47f271ebd9de5a54b8c918c2bd8ad1b76f"'),
 ('VERSION_NAME="0.9726889"; VERSION_BUILD="26889"','VERSION_NAME="0.9726890"; VERSION_BUILD="26890"'),
 ('OUT="$ROOT/build_26889_iris_rawr_outputs"; WORK="$ROOT/.build_26889_iris_rawr_work"','OUT="$ROOT/build_26890_iris_rawr_outputs"; WORK="$ROOT/.build_26890_iris_rawr_work"'),
 ('ARTZIP="$WORK/26888_artifact.zip"; ARTDIR="$WORK/artifact_26888"','ARTZIP="$WORK/26889_artifact.zip"; ARTDIR="$WORK/artifact_26889"'),
 ('BASE="$WORK/exact_successful_26888_compiled_candidate"; CAND="$WORK/candidate_26889"','BASE="$WORK/exact_successful_26889_compiled_candidate"; CAND="$WORK/candidate_26890"'),
 ('# IRIS_26889_AUTHORITATIVE_ACTIONS_STAGE_ORDER','# IRIS_26890_AUTHORITATIVE_ACTIONS_STAGE_ORDER'),
):once(a,b)
body=body.replace('$OUT/26889_COMPILER_STATUS.txt','$OUT/26890_COMPILER_STATUS.txt')
edit('verify_package',lambda s:append(s,''' test -f TRIGGER_26890.txt && grep -Fx 'RUN_26890_B_TONE_TOE_DEFAULT_B_A_NAME_SINGLE_TRIGGER_V1' TRIGGER_26890.txt >/dev/null || fail '26890 exact trigger byte drift'
 python3 -S stage_26890_root.py
 sha256sum -c 26890_HANDOFF_HASHES.sha256 >/dev/null || fail '26890 sealed package tampered'
 python3 -S -m py_compile generate_26890_build.py verify_26890_candidate.py verify_26890_semantics.py verify_26890_patches.py verify_26890_expanded_glsl.py stage_26890_root.py test_26890_negative_tamper.py test_26890_tone_math.py photon_26890_replay_exact_26889_workflow.py
 test "$(find handoff_payload_26890 -type f | wc -l)" -eq 8 || fail '26890 eight-source allowlist drift'
 python3 -S test_26890_tone_math.py
'''))
edit('verify_scope',lambda s:'''verify_scope(){
 [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail 'wrong branch'
 git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD || fail 'successful 26889 authority not ancestor'
 [[ -z "$(git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD -- app/src app/version.properties)" ]] || fail 'unintended committed live source delta'
 [[ -z "$(git status --porcelain -- app/src app/version.properties)" ]] || fail 'uncommitted app runtime source delta'
 diff -u 26890_REPOSITORY_UPLOAD_ALLOWLIST.txt <(git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | LC_ALL=C sort) >/dev/null || fail '26890 repository upload scope drift'
 [[ "$(sha build_26889_iris_rawr.sh)" == '4070c3a0f47fb043d99ad18a1b2d53a629be26891d1147ef9bfc60d790cb7d73' ]] || fail 'real 26889 executed runner drift'
 [[ "$(git rev-parse "$RUNTIME_AUTHORITY_COMMIT:generate_26889_build.py")" == '60a4d9895229a0ac31d597bd2397602ed863c62f' ]] || fail 'successful 26889 generator blob drift'
 pass '26890 committed-only source scope, actual executed successful 26889 runner and generator pinned'
}''')
edit('obtain_authority',lambda s:'''obtain_authority(){
 [[ -n "$TOKEN" ]] || fail 'GITHUB_TOKEN missing'
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
  "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/runs/${RUNTIME_ACTIONS_RUN}" -o "$WORK/26889_run.json"
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
  "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}" -o "$WORK/26889_artifact_metadata.json"
 python3 -S - "$WORK/26889_run.json" "$WORK/26889_artifact_metadata.json" <<'PY_AUTH_90'
import json,sys
run=json.load(open(sys.argv[1]));art=json.load(open(sys.argv[2]))
assert run['id']==41096197467 and run['conclusion']=='success' and run['head_sha']=='17366e5db6359bc68e6098620adb72fd4b3aab0f' and run['head_branch']=='experimental-clean-photon-rebuild'
assert art['id']==12996413398 and art.get('expired') is False and art.get('digest')=='sha256:f04c331fc93159ff44fe685f3de90ae6c28a6be4adec9144b1593d6cdea3e0e2'
print('PASS actual successful 26889 run, artifact ID and digest')
PY_AUTH_90
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
  "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"
 [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail '26889 successful artifact SHA drift'
 unzip -q "$ARTZIP" -d "$ARTDIR"
 local T="$ARTDIR/build_26889_iris_rawr_outputs/26889_candidate_app_source.tar.gz"
 [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail '26889 actual compiled candidate TAR SHA drift'
 local EXEC="$ARTDIR/build_26889_iris_rawr_outputs/exact_generated_runner/build_26889_iris_rawr.sh"
 [[ -f "$EXEC" && "$(sha "$EXEC")" == '4070c3a0f47fb043d99ad18a1b2d53a629be26891d1147ef9bfc60d790cb7d73' ]] || fail 'actual successful 26889 executed runner mismatch'
 cmp -s "$EXEC" "$ROOT/build_26889_iris_rawr.sh" || fail 'derived 26889 runner not identical to actual executed runner'
 local CS="$ARTDIR/build_26889_iris_rawr_outputs/26889_COMPILER_STATUS.txt"
 for k in 'REAL GLSL COMPILE: PASS' 'REAL SPIR-V VALIDATION: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS';do
  grep -F "$k" "$CS" >/dev/null || fail "26889 real compiler/assemble receipt absent $k"
 done
 mkdir -p "$BASE";tar -xzf "$T" -C "$BASE"
 [[ "$(find "$BASE/app" -type f | wc -l)" -eq 2025 ]] || fail '26889 file count mismatch'
 (cd "$BASE" && sha256sum -c "$ROOT/26890_BASE_FULL_APP.sha256" >/dev/null) || fail '26889 exact source hash mismatch'
 cmp -s "$ARTDIR/build_26889_iris_rawr_outputs/26889_candidate_full_app.sha256" "$ROOT/26890_BASE_FULL_APP.sha256" || fail '26889 Actions candidate manifest drift'
 pass 'actual successful 26889 2025-file compiled TAR, exact executed runner and compiler proofs'
}''')
# Preserve ENTIRE original 26889 candidate-first historical reconstruction, then extend.
old=stage(body,'make_candidate')
assert body.count(old)==1
body=body.replace(old,old.replace('make_candidate(){','historical_26889_make_candidate(){',1),1)
new='''
make_candidate(){
 local H88="$WORK/historical_26888_from_26889" H89="$WORK/historical_26889_replayed"
 cp -a "$BASE" "$H88";git -C "$H88" init -q
 (cd "$H88" && git apply --check --reverse "$ROOT/26889_FORWARD_FULL_INDEX.patch" && \\
  git apply --reverse "$ROOT/26889_FORWARD_FULL_INDEX.patch" && \\
  sha256sum -c "$ROOT/26889_BASE_FULL_APP.sha256" >/dev/null) || fail 'actual 26889 to exact 26888 rollback invalid'
 # Original 26889 validator hashes the whole root, so discard temporary Git metadata.
 rm -rf "$H88/.git"
 ( local BASE="$H88" CAND="$H89";historical_26889_make_candidate )
 diff -qr "$H89/app" "$BASE/app" >/dev/null || fail 'original 26889 candidate generation differs from actual successful compiled 26889 bytes'
 python3 -S verify_26889_candidate.py "$H88" "$BASE"
 python3 -S verify_26889_semantics.py "$H88" "$BASE"
 python3 -S verify_26889_expanded_glsl.py "$BASE"
 python3 -S verify_26889_patches.py "$H88" "$BASE" 26889_FORWARD_FULL_INDEX.patch 26889_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26890_candidate.py "$BASE" "$CAND" --transform
 python3 -S verify_26890_semantics.py "$BASE" "$CAND"
 python3 -S verify_26890_expanded_glsl.py "$CAND"
 python3 -S test_26890_tone_math.py
}
'''
assert '\nverify_successful_mechanics(){' in body
body=body.replace('\nverify_successful_mechanics(){',new+'\nverify_successful_mechanics(){',1)
assert tuple(n for n in rex.findall(body) if n in STAGES)==STAGES

def mechanics(s):
 s=s.replace('verify_26889_candidate.py "$BASE" "$CAND"','verify_26890_candidate.py "$BASE" "$CAND"')
 s=s.replace('verify_26889_semantics.py "$BASE" "$CAND"','verify_26890_semantics.py "$BASE" "$CAND"')
 s=s.replace('"$ARTDIR/build_26888_iris_rawr_outputs/26888_modified_shader_spirv/Iris26887BOffHdrqMerge_prod.spv" "$BASE" "$CAND"',
             '"$ARTDIR/build_26889_iris_rawr_outputs/26888_modified_shader_spirv/Iris26887BOffHdrqMerge_prod.spv" "$WORK/historical_26888_from_26889" "$WORK/historical_26889_replayed"')
 return append(s,''' [[ "$(sha build_26889_iris_rawr.sh)" == '4070c3a0f47fb043d99ad18a1b2d53a629be26891d1147ef9bfc60d790cb7d73' ]] || fail '26889 real Actions successful runner drift'
 python3 -S verify_26890_candidate.py "$BASE" "$CAND"
 python3 -S verify_26890_semantics.py "$BASE" "$CAND"
 python3 -S test_26890_tone_math.py
''')
edit('verify_successful_mechanics',mechanics)
def shaders(s):
 old='verify_26889_expanded_glsl.py "$CAND" --compiler'
 assert s.count(old)==1
 s=s.replace(old,'verify_26889_expanded_glsl.py "$WORK/historical_26889_replayed" --compiler',1)
 return append(s,''' python3 -S verify_26890_expanded_glsl.py "$CAND" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26890_three_current_expanded_gles" | tee "$OUT/26890_real_modified_gles_compile.txt"
 grep -Fx 'PASS 26890 all THREE current exact runtime-expanded GLES fragment programs REAL PINNED COMPILE' "$OUT/26890_real_modified_gles_compile.txt" >/dev/null || fail '26890 real pinned B/SDR/UHDR tone GLSL compiler proof missing'
''')
edit('compile_modified_runtime_shaders',shaders)
# This amendment changes a B/OFF Vulkan compute shader, unlike the original
# seven-file GLSL ES-only 26890. Compile BOTH production/trace variants from
# exact changed candidate, in addition to all inherited real shader checks.
def amended_hdrq_compiler(s):
 return append(s,""" python3 -S verify_26889_expanded_glsl.py "$CAND" --compiler "$IRIS26864_GLSLANG" --spirv-val "$(command -v spirv-val)" --spirv-opt "$(command -v spirv-opt)" --out "$OUT/26890_strength115_real_spirv" | tee "$OUT/26890_strength115_real_compiler_receipt.txt"
 grep -Fx 'PASS 26889 pinned REAL glslang/SPIR-V 3 modified native variants + original ESSL300 LONG' "$OUT/26890_strength115_real_compiler_receipt.txt" >/dev/null || fail '26890 changed B/OFF strength115 GLSL/SPIRV real compiler proof missing'
""")
edit('compile_modified_runtime_shaders',amended_hdrq_compiler)

def patchstage(s):
 s=s.replace('verify_26889_candidate.py "$BASE" "$CAND"','verify_26890_candidate.py "$BASE" "$CAND"')
 s=s.replace('verify_26889_semantics.py "$BASE" "$CAND"','verify_26890_semantics.py "$BASE" "$CAND"')
 s=s.replace('verify_26889_patches.py "$BASE" "$CAND" 26889_FORWARD_FULL_INDEX.patch 26889_ROLLBACK_FULL_INDEX.patch',
             'verify_26890_patches.py "$BASE" "$CAND" 26890_FORWARD_FULL_INDEX.patch 26890_ROLLBACK_FULL_INDEX.patch')
 s=s.replace('26889_patch_validation.txt','26890_patch_validation.txt')
 s=s.replace('test_26889_negative_tamper.py "$BASE" "$CAND"',
             'test_26889_negative_tamper.py "$WORK/historical_26888_from_26889" "$WORK/historical_26889_replayed"')
 s=s.replace("pass 'exact 26889 10 source paths and 2015 protected, full-index forward/rollback 7/12/40 and negative tamper'",
             "pass '26889 original negative tamper on historical bytes, 26890 8-path full-index forward/rollback 7/12/40'")
 return append(s,""" python3 -S test_26890_negative_tamper.py "$BASE" "$CAND"
 python3 -S test_26890_tone_math.py
""")
edit('verify_candidate_patches',patchstage)

def safety(s):
 s=s.replace('verify_26889_candidate.py "$BASE" "$CAND"','verify_26890_candidate.py "$BASE" "$CAND"')
 s=s.replace('26889_UNCHANGED_PROTECTED.sha256','26890_UNCHANGED_PROTECTED.sha256')
 s=s.replace('26889_PREBUILD_SAFETY.txt','26890_PREBUILD_SAFETY.txt')
 s=s.replace('runtime_authority=successful 26888','runtime_authority=successful 26889')
 s=s.replace('runtime_changed_files=10 (9 modified existing including version, 1 B-OFF private addition); 2015 protected, Spektra/DNG/UHDR and non-B owners unchanged',
             'runtime_changed_files=8 (8 existing files, including version; 0 additions/deletions); 2017 protected, B SDR/UHDR mirrored tone, exact B default and JPEG name, A/Night/Spektra/DNG/vendor protected')
 s=s.replace('prior_files=2024','prior_files=2025').replace('candidate_files=2025','candidate_files=2025')
 s=s.replace('protected_source=2015 files byte-identical to successful 26888', 'protected_source=2017 files byte-identical to successful 26889')
 s=s.replace('infrastructure_delta=26889 strict successor workflow/generator/manifests/new native SPIRV/positive-negative regression; exact inherited 17-stage compiler+freeze+assemble mechanics',
             'infrastructure_delta=26890 strict successor workflow single-trigger + source validators; exact inherited 17-stage compiler+freeze+assemble mechanics')
 s=s.replace('verification_mechanics=exact successful 26888','verification_mechanics=exact successful 26889')
 s=s.replace('26889_COMPILER_STATUS.txt','26890_COMPILER_STATUS.txt')
 return s
edit('prebuild_safety',safety)
edit('compile_languages',lambda s:s.replace('26889_gradle_language_compilers.log','26890_gradle_language_compilers.log'))
edit('compile_native',lambda s:s.replace('26889_gradle_native_compiler.log','26890_gradle_native_compiler.log'))
edit('assemble',lambda s:s.replace('26889_','26890_'))
def post(s):
 for a,b in [('26889_','26890_'),('verify_26889_candidate.py','verify_26890_candidate.py')]:s=s.replace(a,b)
 return s
edit('postbuild_proof',post)
def replay(s):
 # Replace ONLY previous-current 26889 validators bound to current 26890 bytes.
 for a,b in [('sha256sum -c 26889_HANDOFF_HASHES.sha256','sha256sum -c 26890_HANDOFF_HASHES.sha256\n sha256sum -c 26889_HANDOFF_HASHES.sha256'),
             ('sha256sum -c 26889_GENERATED_BUILD_SHA256.txt','sha256sum -c 26890_GENERATED_BUILD_SHA256.txt\n sha256sum -c 26889_GENERATED_BUILD_SHA256.txt'),
             ('bash -n build_26889_iris_rawr.sh','bash -n build_26890_iris_rawr.sh\n bash -n build_26889_iris_rawr.sh'),
             ('verify_26889_candidate.py "$BASE" "$replay" --transform','verify_26890_candidate.py "$BASE" "$replay" --transform'),
             ('verify_26889_candidate.py "$BASE" "$exp"','verify_26890_candidate.py "$BASE" "$exp"'),
             ('verify_26889_semantics.py "$BASE" "$exp"','verify_26890_semantics.py "$BASE" "$exp"'),
             ('verify_26889_expanded_glsl.py "$exp"','verify_26890_expanded_glsl.py "$exp"'),
             ('verify_26889_patches.py "$BASE" "$exp" 26889_FORWARD_FULL_INDEX.patch 26889_ROLLBACK_FULL_INDEX.patch',
              'verify_26890_patches.py "$BASE" "$exp" 26890_FORWARD_FULL_INDEX.patch 26890_ROLLBACK_FULL_INDEX.patch'),
             ('26889_candidate_app_source.tar.gz','26890_candidate_app_source.tar.gz'),
             ('26889_final_patch_replay.txt','26890_final_patch_replay.txt'),
             ("grep -Fx 'VERSION_NAME=0.9726889' \"$exp/app/version.properties\"","grep -Fx 'VERSION_NAME=0.9726890' \"$exp/app/version.properties\""),
             ("grep -Fx 'VERSION_BUILD=26889' \"$exp/app/version.properties\"","grep -Fx 'VERSION_BUILD=26890' \"$exp/app/version.properties\"")]:s=s.replace(a,b)
 return append(s,''' python3 -S verify_26889_candidate.py "$WORK/historical_26888_from_26889" "$WORK/historical_26889_replayed"
 python3 -S verify_26889_semantics.py "$WORK/historical_26888_from_26889" "$WORK/historical_26889_replayed"
 python3 -S verify_26889_expanded_glsl.py "$WORK/historical_26889_replayed"
 python3 -S verify_26889_patches.py "$WORK/historical_26888_from_26889" "$WORK/historical_26889_replayed" 26889_FORWARD_FULL_INDEX.patch 26889_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26890_candidate.py "$BASE" "$exp"
 python3 -S verify_26890_semantics.py "$BASE" "$exp"
 python3 -S verify_26890_expanded_glsl.py "$exp"
 python3 -S verify_26890_patches.py "$BASE" "$exp" 26890_FORWARD_FULL_INDEX.patch 26890_ROLLBACK_FULL_INDEX.patch
 python3 -S test_26890_tone_math.py
''')
edit('clean_extract_replay',replay)
assert tuple(n for n in rex.findall(body) if n in STAGES)==STAGES
for c in ('./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace'):
 assert c in body,('inherited real compiler missing',c)
# Preserve the historic 26889 compiler receipt and new successor compiler status.
body=body.replace('26889_COMPILER_STATUS.txt','26890_COMPILER_STATUS.txt')
body=body.replace('build_26889_iris_rawr_outputs/26890_COMPILER_STATUS.txt','build_26889_iris_rawr_outputs/26889_COMPILER_STATUS.txt')
assert 'verify_26889_candidate.py "$BASE" "$CAND"' not in stage(body,'verify_successful_mechanics')
assert 'verify_26889_candidate.py "$BASE" "$exp"' not in stage(body,'clean_extract_replay')
assert stage(body,'compile_modified_runtime_shaders').count('verify_26889_expanded_glsl.py "$CAND"')==1
assert 'verify_26889_patches.py "$BASE" "$exp"' not in stage(body,'clean_extract_replay')
path=R/'build_26890_iris_rawr.sh';path.write_text(body)
h=hashlib.sha256(path.read_bytes()).hexdigest()
(R/'26890_GENERATED_BUILD_SHA256.txt').write_text(f'{h}  build_26890_iris_rawr.sh\n')
print('PASS exact successful 26889 executed runner successor, 17 stages retained, SHA256',h)
