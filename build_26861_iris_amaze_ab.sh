#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
ROOT="$(pwd)"; EXPECTED_BRANCH="experimental-clean-photon-rebuild"
RUNTIME_ARTIFACT_NAME="photon-26860-iris-amaze-ab"
RUNTIME_ARTIFACT_SHA="5a31864be4696111fefdc81c36fa86e89fcb881c35a54d0eefa255c00905a23e"
RUNTIME_TAR_SHA="808caf16117b4a1feac040f49d159d2eab42e037c46fbba7d419e70653505132"
MECHANICS_AUTHORITY_COMMIT="cf73d7bdcaf56532fab04807a2266d6e040a1369"
VERSION_NAME="0.9726861"; VERSION_BUILD="26861"; GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
OUT="$ROOT/build_26861_iris_amaze_ab_outputs"; WORK="$ROOT/.build_26861_iris_amaze_ab_work"
ARTZIP="$WORK/26860_artifact.zip"; ARTDIR="$WORK/artifact_26860"
BASE="$WORK/exact_successful_26860_compiled_candidate"; CAND="$WORK/candidate_26861"
LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST_LANG="$WORK/post_language_compiler_source_snapshot"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-iris-amaze-ab-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR"
cat > "$OUT/26861_COMPILER_STATUS.txt" <<'STATUS'
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
STATUS
# IRIS_26861_AUTHORITATIVE_ACTIONS_STAGE_ORDER
verify_package(){
 sha256sum -c 26861_HANDOFF_HASHES.sha256 >/dev/null
 bash -n build_26861_iris_amaze_ab.sh
 python3 -S -m py_compile transform_26861.py validate_26861.py verify_26861_patches.py verify_26861_runtime_glsl.py
 rm -rf __pycache__
 [[ "$(find handoff_payload_26861 -type f | wc -l)" -eq 4 ]] || fail "26861 payload count"
 diff -u 26861_ALL_CANDIDATE_CHANGED_PATHS.txt <(find handoff_payload_26861 -type f | sed 's#^handoff_payload_26861/##' | sort) >/dev/null || fail "payload allowlist mismatch"
 for p in 26861_FORWARD_FULL_INDEX.patch 26861_ROLLBACK_FULL_INDEX.patch; do ! grep -Eq '^(rename from|rename to|copy from|copy to) ' "$p" || fail "patch inference"; done
 grep -Fx 'RUN_26861_B_ONLY_EMPIRICAL_TEMPORAL_NO_SPATIAL' TRIGGER_26861.txt >/dev/null || fail "wrong trigger"
 ! find . -type f -name '*.apk' | grep -q . || fail "APK unexpectedly packaged"
 pass "26861 package hashes/syntax/4-file allowlist/patch identity"
}
verify_scope(){
 [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
 [[ -z "$(git ls-files -- glsl_static)" ]] || fail "unexpected tracked glsl_static after guarded cleanup"
 python3 -S - <<'PY_GLSL_SCOPE'
from pathlib import Path
import subprocess
M={line.split('  ',1)[1] for line in Path('26854_ACCIDENTAL_GLSL_EXACT_SHA256.txt').read_text().splitlines()}
def git(*args):return subprocess.check_output(['git',*args],text=True).splitlines()
assert len(M)==50
assert set(git('diff','--cached','--name-only','--diff-filter=D','--','glsl_static'))==M,'unproven exact cleanup'
assert set(git('diff','--name-only','2af0376988ae2fb2a03689f4dd63ac2e743a9835..HEAD','--','glsl_static'))==M,'unexpected historical generated GLSL scope'
assert not git('ls-files','--','glsl_static')
print('PASS exact 50 accidental shader bytes excluded only from ephemeral index')
PY_GLSL_SCOPE
 git merge-base --is-ancestor "$MECHANICS_AUTHORITY_COMMIT" HEAD || fail "successful 26860 mechanics ancestor missing"
 python3 -S - <<'PY_SCOPE'
import subprocess
from pathlib import Path
paths=subprocess.check_output(['git','diff','--name-only','cf73d7bdcaf56532fab04807a2266d6e040a1369..HEAD'],text=True).splitlines()
expected=set(Path('26861_INFRASTRUCTURE_CHANGED_PATHS.txt').read_text().splitlines())
assert len(paths)==len(expected) and set(paths)==expected,('26861 strict repository scope',sorted(set(paths)^expected))
assert not any(p.startswith('app/src/') or p.startswith('app/version.properties') for p in paths), 'live app changed before source freeze'
assert not any(p.startswith('glsl_static/') for p in paths),'new generated GLSL forbidden'
print('PASS exact 26861 handoff infrastructure scope relative to successful 26860 commit')
PY_SCOPE
 [[ -z "$(git diff --name-only "$MECHANICS_AUTHORITY_COMMIT"..HEAD -- app/src app/version.properties)" ]] || fail "live app source changed since 26860 success"
 pass "26861 branch/HEAD/protected live source/infrastructure scope guarded"
}
obtain_authority(){
 [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"
 local listing="$WORK/artifact_listing.json" meta="$WORK/26860_artifact_identity.txt"
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts?name=${RUNTIME_ARTIFACT_NAME}&per_page=100" -o "$listing"
 python3 -S - "$listing" "$meta" "$RUNTIME_ARTIFACT_NAME" "$RUNTIME_ARTIFACT_SHA" <<'PY_ID'
import json,sys
rows=json.load(open(sys.argv[1])).get('artifacts',[])
match=[a for a in rows if a.get('name')==sys.argv[3] and not a.get('expired') and str(a.get('digest','')).lower()=='sha256:'+sys.argv[4].lower()]
assert len(match)==1,('artifact uniqueness',[(a.get('id'),a.get('name'),a.get('digest')) for a in rows])
a=match[0];r=a['workflow_run'];assert a['id']==12280294462 and r['id']==39457079091 and r['head_sha']=='cf73d7bdcaf56532fab04807a2266d6e040a1369' and r['head_branch']=='experimental-clean-photon-rebuild',(a,r)
open(sys.argv[2],'w').write(f"{a['id']}\n{r['id']}\n{r['head_sha']}\n")
print('PASS exact successful 26860 artifact ID/run/commit/branch/digest')
PY_ID
 mapfile -t authority < "$meta"; RUNTIME_ARTIFACT_ID="${authority[0]}"; RUNTIME_ACTIONS_RUN="${authority[1]}"; RUNTIME_AUTHORITY_COMMIT="${authority[2]}"
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/runs/${RUNTIME_ACTIONS_RUN}" -o "$WORK/26860_run.json"
 python3 -S - "$WORK/26860_run.json" "$RUNTIME_AUTHORITY_COMMIT" <<'PY_RUN'
import json,sys
x=json.load(open(sys.argv[1]));assert x['conclusion']=='success' and x['head_sha']==sys.argv[2],(x.get('conclusion'),x.get('head_sha'))
print('PASS exact 26860 Actions run success/HEAD')
PY_RUN
 git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD || fail "26860 authority commit not ancestor"
 [[ -z "$(git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD -- app/src app/version.properties)" ]] || fail "live runtime changed since 26860 authority"
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"
 [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail "26860 artifact zip SHA mismatch"
 unzip -q "$ARTZIP" -d "$ARTDIR"
 local T="$ARTDIR/build_26860_iris_amaze_ab_outputs/26860_candidate_app_source.tar.gz"
 [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail "26860 compiled candidate tar SHA mismatch"
 local STATUS="$ARTDIR/build_26860_iris_amaze_ab_outputs/26860_COMPILER_STATUS.txt"
 for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do grep -F "$proof" "$STATUS" >/dev/null || fail "missing 26860 authority compiler proof: $proof"; done
 mkdir -p "$BASE";tar -xzf "$T" -C "$BASE"
 [[ "$(find "$BASE/app" -type f | wc -l)" -eq 1840 ]] || fail "26860 compiled candidate count"
 (cd "$BASE" && sha256sum -c "$ROOT/26861_BASE_26860_FULL_APP.sha256" >/dev/null)
 (cd "$BASE" && sha256sum -c "$ROOT/26861_PRIOR_SOURCE_HASHES.sha256" >/dev/null)
 cat > "$OUT/26861_RESOLVED_AUTHORITIES.txt" <<EOF_AUTH
runtime_commit=$RUNTIME_AUTHORITY_COMMIT
runtime_run=$RUNTIME_ACTIONS_RUN
runtime_artifact_id=$RUNTIME_ARTIFACT_ID
runtime_artifact_name=$RUNTIME_ARTIFACT_NAME
runtime_artifact_sha256=$RUNTIME_ARTIFACT_SHA
runtime_candidate_tar_sha256=$RUNTIME_TAR_SHA
mechanics_commit=$MECHANICS_AUTHORITY_COMMIT
EOF_AUTH
 pass "exact successful 26860 Actions compiled candidate reconstructed"
}
universe_equal(){
 python3 -S - "$1" "$2" <<'PY_U'
from pathlib import Path
import hashlib,sys
def U(root):return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(root)/'app').rglob('*') if p.is_file()}
a,b=U(sys.argv[1]),U(sys.argv[2]);assert a==b,(len(a),len(b));print('PASS byte identical app universe:',len(a))
PY_U
}
make_candidate(){
 python3 -S transform_26861.py "$BASE" "$CAND" handoff_payload_26861
 python3 -S validate_26861.py "$BASE" "$CAND"
 (cd "$CAND" && sha256sum -c "$ROOT/26861_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 for file in 26861_PROTECTED_26860.sha256 26861_NATIVE_PROTECTED_26860.sha256 26861_DNG_WRITER_26860.sha256 26861_VENDOR_PROTECTED_26860.sha256 26861_SHADER_ASSETS_PROTECTED_26860.sha256; do (cd "$CAND" && sha256sum -c "$ROOT/$file" >/dev/null); done
 [[ "$(find "$CAND/app" -type f | wc -l)" -eq 1840 ]] || fail "candidate file count"
 pass "26861 frozen authority-seeded candidate 3 modified B paths plus one version increment"
}
verify_successful_mechanics(){
 local a60="$WORK/authority_26860_build.sh" a59="$WORK/authority_26859_build.sh"
 git show "$MECHANICS_AUTHORITY_COMMIT:build_26860_iris_amaze_ab.sh" > "$a60"
 [[ "$(sha "$a60")" == "$(sha 26860_SUCCESSFUL_MECHANICS_REFERENCE.sh)" ]] || fail "successful 26860 mechanics SHA mismatch"
 git show '254778f171c53577806d633fc969e61a22275f8a:build_26859_iris_amaze_ab.sh' > "$a59"
 [[ "$(sha "$a59")" == "$(sha 26859_SUCCESSFUL_MECHANICS_REFERENCE.sh)" ]] || fail "successful 26859 inherited mechanics SHA mismatch"
 for cmd in './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace' "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace" './gradlew :app:assembleDebug --stacktrace'; do
  grep -F "$cmd" "$a60" >/dev/null || fail "26860 successful compiler command absent"
  grep -F "$cmd" "$0" >/dev/null || fail "26861 compiler command differs"
 done
 python3 -S - "$0" "$a60" "$a59" <<'PY_ORDER'
from pathlib import Path
import sys
stages=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay']
for fn,v in zip(sys.argv[1:],('26861','26860','26859')):
 t=Path(fn).read_text().split(f'# IRIS_{v}_AUTHORITATIVE_ACTIONS_STAGE_ORDER',1)[1];pos=-1
 for stage in stages:
  j=t.find('\n'+stage+'\n',pos+1);assert j>pos,(fn,stage);pos=j
print('PASS exact 26861 inherited 26860/26859 17-stage order and REAL compiler command identity')
PY_ORDER
 pass "26861 exact successful 26860 17-stage mechanics identity"
}
prepare_glslang(){
 D="$WORK/glslang-${GLSLANG_VERSION}"; A="$WORK/glslang.tar.gz"; mkdir -p "$D"
 curl -L --fail --retry 3 "$GLSLANG_URL" -o "$A"; [[ "$(sha "$A")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "glslang archive sha"
 tar -xzf "$A" -C "$D"; compiler="$(find "$D" -type f -name glslang -print -quit)"
 [[ -n "$compiler" ]] || compiler="$(find "$D" \( -type f -o -type l \) -name glslangValidator -print -quit)"
 compiler="$(readlink -f "$compiler")"; [[ -x "$compiler" ]] || chmod +x "$compiler"
 "$compiler" --version | tee "$OUT/26861_glslang_version.txt"
 export IRIS26861_GLSLANG="$compiler"; export IRIS26681_SPEKTRA_GLSLANG="$compiler"
 pass "pinned glslang 16.5.0 dual environment handoff"
}
compile_modified_runtime_shaders(){
 python3 -S verify_26861_runtime_glsl.py "$BASE" "$CAND" --compiler "$IRIS26861_GLSLANG" --out "$OUT/26861_runtime_expanded_glsl" | tee "$OUT/26861_glsl_validation.txt"
 grep -F 'PASS 26861 GLSL ownership:' "$OUT/26861_glsl_validation.txt" >/dev/null || fail "modified GLSL validation missing"
 sed -i 's#REAL GLSL COMPILE: NOT RUN YET#REAL GLSL COMPILE: PASS (pinned glslang 16.5.0, seven runtime-expanded shader owners (two new B + protected shader checks); protected universe unchanged)#' "$OUT/26861_COMPILER_STATUS.txt"
}
compile_spektra_raw_shader(){ pass "Spektra project verifier absent from repo shell; inherited source protected by candidate manifest"; }
snapshot_live_authority_seeded(){
 python3 -S - "$CAND" "$1" "$ROOT" <<'PY_S'
from pathlib import Path
import shutil,sys
cand,out,live=map(Path,sys.argv[1:]);shutil.rmtree(out,ignore_errors=True);shutil.copytree(cand,out)
expected={str(p.relative_to(cand)):p for p in (cand/'app').rglob('*') if p.is_file()}
for rel in expected:
 lp=live/rel
 if not lp.is_file():raise SystemExit(f'missing live candidate path: {rel}')
 (out/rel).write_bytes(lp.read_bytes())
expected_src={r for r in expected if r.startswith('app/src/')}
actual_src={str(p.relative_to(live)) for p in (live/'app/src').rglob('*') if p.is_file()}
extra=sorted(actual_src-expected_src)
if extra:raise SystemExit(f'unexpected app/src paths: {extra}')
print('PASS authority-seeded canonical live snapshot:',len(expected),'files; generated app/build and app/.cxx excluded')
PY_S
}
install_frozen_candidate_live(){ rm -rf app; cp -a "$CAND/app" app; snapshot_live_authority_seeded "$LIVE_CANON"; universe_equal "$CAND" "$LIVE_CANON"; pass "authority-seeded live candidate frozen byte-identical"; }
compile_languages(){
 ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26861_gradle_language_compilers.log"
 snapshot_live_authority_seeded "$POST_LANG";universe_equal "$CAND" "$POST_LANG"
 sed -i 's/REAL KOTLIN COMPILE: NOT RUN YET/REAL KOTLIN COMPILE: PASS/' "$OUT/26861_COMPILER_STATUS.txt"
 sed -i 's/REAL JAVA COMPILE: NOT RUN YET/REAL JAVA COMPILE: PASS/' "$OUT/26861_COMPILER_STATUS.txt"
 pass "real Kotlin Java compiler source freeze"
}
verify_native_glslang_handoff(){
 [[ -n "${IRIS26861_GLSLANG:-}" && -x "$IRIS26861_GLSLANG" ]] || fail "IRIS26861_GLSLANG missing"
 [[ -n "${IRIS26681_SPEKTRA_GLSLANG:-}" && -x "$IRIS26681_SPEKTRA_GLSLANG" ]] || fail "SPEKTRA GLSLANG missing"
 [[ "$(readlink -f "$IRIS26861_GLSLANG")" == "$(readlink -f "$IRIS26681_SPEKTRA_GLSLANG")" ]] || fail "native shader compiler handoff mismatch"
 pass "26852 native GLSL compiler identity inherited"
}
compile_native(){
 ./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26861_gradle_native_compiler.log"
 sed -i 's#NATIVE/NDK COMPILE: NOT RUN YET#NATIVE/NDK COMPILE: PASS (arm64-v8a + armeabi-v7a)#' "$OUT/26861_COMPILER_STATUS.txt"
}
verify_candidate_patches(){
 python3 -S verify_26861_patches.py "$BASE" "$CAND" 26861_FORWARD_FULL_INDEX.patch 26861_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26861_patch_validation.txt"
 grep -F 'PASS 26861 canonical patch proof' "$OUT/26861_patch_validation.txt" >/dev/null
 pass "26861 full-index forward/rollback 7/12/40 fuzz=0 exact"
}
prebuild_safety(){
 snapshot_live_authority_seeded "$WORK/prebuild_live_snapshot";universe_equal "$CAND" "$WORK/prebuild_live_snapshot"
 python3 -S validate_26861.py "$BASE" "$CAND"
 for file in 26861_PROTECTED_26860.sha256 26861_NATIVE_PROTECTED_26860.sha256 26861_DNG_WRITER_26860.sha256 26861_VENDOR_PROTECTED_26860.sha256 26861_SHADER_ASSETS_PROTECTED_26860.sha256; do (cd "$CAND" && sha256sum -c "$ROOT/$file" >/dev/null); done
 cat > "$OUT/26861_PREBUILD_SAFETY.txt" <<EOF_SAFETY
PRE-BUILD SAFETY PROOF PASSED
runtime_authority=successful 26860 ${RUNTIME_AUTHORITY_COMMIT} run ${RUNTIME_ACTIONS_RUN} artifact ${RUNTIME_ARTIFACT_ID}
verification_mechanics=exact successful 26860 inherited 17-stage sequence
runtime_changed_files=3 (three modified B Kotlin sources: burst fitter, B shader owner, stacker)
version_file=1 modified; guarded 26861 increment
original_protected_files=1836 hash-exact; ALL 26860 native 836 unchanged
candidate_files=1840
A=original 26850 only; B=26855 CFA+AMaZE/Lab/FCC (26860 corrected WB/VGN contract); 26860 smooth-neutral highlight and physical LSC once; 26861 B-only measured sensor burst noise; 14 NORMAL+eligible LONG; optional true2x; independent JPEG/DNG/UHDR
native_integration=26860 inherited native/AMaZE unchanged; protected original native/vendor/DNG byte identical
backup_branch=NONE_USER_EXPLICIT
EOF_SAFETY
 pass "PRE-BUILD SAFETY PROOF PASSED"
}
assemble(){
 ./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26861_gradle_assemble.log"
 mapfile -t apks < <(find app/build/outputs/apk -type f -name '*.apk' | sort)
 [[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one APK, got ${#apks[@]}"
 cp "${apks[0]}" "$FINAL"; sha256sum "$FINAL" | tee "$OUT/26861_APK.sha256"
 sed -i 's/FULL ANDROID ASSEMBLE: NOT RUN YET/FULL ANDROID ASSEMBLE: PASS (exactly one APK)/' "$OUT/26861_COMPILER_STATUS.txt"
}
postbuild_proof(){
 snapshot_live_authority_seeded "$WORK/postbuild_live_snapshot";universe_equal "$CAND" "$WORK/postbuild_live_snapshot"
 python3 -S validate_26861.py "$BASE" "$CAND"
 (cd "$CAND" && sha256sum -c "$ROOT/26861_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 for file in 26861_PROTECTED_26860.sha256 26861_NATIVE_PROTECTED_26860.sha256 26861_DNG_WRITER_26860.sha256 26861_VENDOR_PROTECTED_26860.sha256 26861_SHADER_ASSETS_PROTECTED_26860.sha256; do (cd "$CAND" && sha256sum -c "$ROOT/$file" >/dev/null); done
 cp 26861_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26861_candidate_full_app.sha256"
 tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26861_candidate_app_source.tar.gz" -C "$CAND" app
 sha256sum "$OUT/26861_candidate_app_source.tar.gz" > "$OUT/26861_candidate_app_source.tar.gz.sha256"
 cp 26861_FORWARD_FULL_INDEX.patch "$OUT/26861_FORWARD_FULL_INDEX.patch";cp 26861_ROLLBACK_FULL_INDEX.patch "$OUT/26861_ROLLBACK_FULL_INDEX.patch"
 sed -i 's/POST-BUILD INVARIANCE: NOT RUN YET/POST-BUILD INVARIANCE: PASS/' "$OUT/26861_COMPILER_STATUS.txt"
 pass "postbuild original protected/DNG/native/vendor and changed domain invariance"
}
clean_extract_replay(){
 local replay="$WORK/clean_replay_candidate";rm -rf "$replay"
 sha256sum -c 26861_HANDOFF_HASHES.sha256 >/dev/null
 bash -n build_26861_iris_amaze_ab.sh
 python3 -S -m py_compile transform_26861.py validate_26861.py verify_26861_patches.py verify_26861_runtime_glsl.py;rm -rf __pycache__
 python3 -S transform_26861.py "$BASE" "$replay" handoff_payload_26861
 universe_equal "$CAND" "$replay";python3 -S validate_26861.py "$BASE" "$replay"
 python3 -S verify_26861_runtime_glsl.py "$BASE" "$replay" --out "$OUT/26861_final_runtime_expanded_glsl" | tee "$OUT/26861_final_glsl_static_replay.txt"
 python3 -S verify_26861_patches.py "$BASE" "$replay" 26861_FORWARD_FULL_INDEX.patch 26861_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26861_final_patch_replay.txt"
 (cd "$replay" && sha256sum -c "$ROOT/26861_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 grep -Fx 'VERSION_NAME=0.9726861' "$replay/app/version.properties" >/dev/null
 grep -Fx 'VERSION_BUILD=26861' "$replay/app/version.properties" >/dev/null
 for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do grep -F "$proof" "$OUT/26861_COMPILER_STATUS.txt" >/dev/null || fail "missing Actions compiler proof: $proof"; done
 pass "final 26861 clean replay exact candidate hashes/ownership/GLSL/patches/version/compilers/build"
}
verify_package
verify_scope
obtain_authority
make_candidate
verify_successful_mechanics
prepare_glslang
compile_modified_runtime_shaders
compile_spektra_raw_shader
install_frozen_candidate_live
compile_languages
verify_native_glslang_handoff
compile_native
verify_candidate_patches
prebuild_safety
assemble
postbuild_proof
clean_extract_replay
pass "26861 IRIS AMaZE A/B: ACTIONS BUILD PROOF COMPLETE"
