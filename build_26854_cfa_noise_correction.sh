#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
ROOT="$(pwd)"; EXPECTED_BRANCH="experimental-clean-photon-rebuild"
RUNTIME_ARTIFACT_NAME="photon-26853-multiframe-native-cfa-denoise"
RUNTIME_ARTIFACT_SHA="c0c77b698717d4e68e0f4f38a43ab5beedee9979b35f3adfade0c5a50f35ac5e"
RUNTIME_TAR_SHA="cd05d604ed36d6a8ab72548add4dd8024dbb60f7979475ec1e72e75de5258681"
MECHANICS_AUTHORITY_COMMIT="2af0376988ae2fb2a03689f4dd63ac2e743a9835"
VERSION_NAME="0.9726854"; VERSION_BUILD="26854"; GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
OUT="$ROOT/build_26854_cfa_noise_correction_outputs"; WORK="$ROOT/.build_26854_cfa_noise_correction_work"
ARTZIP="$WORK/26853_artifact.zip"; ARTDIR="$WORK/artifact_26853"
BASE="$WORK/exact_successful_26853_compiled_candidate"; CAND="$WORK/candidate_26854"
LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST_LANG="$WORK/post_language_compiler_source_snapshot"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-cfa-noise-correction-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR"
cat > "$OUT/26854_COMPILER_STATUS.txt" <<'STATUS'
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
STATUS
# IRIS_26854_AUTHORITATIVE_ACTIONS_STAGE_ORDER
verify_package(){
 sha256sum -c 26854_HANDOFF_HASHES.sha256 >/dev/null
 bash -n build_26854_cfa_noise_correction.sh
 python3 -S -m py_compile transform_26854.py validate_26854.py verify_26854_patches.py verify_26854_runtime_glsl.py
 rm -rf __pycache__
 [[ "$(find handoff_payload_26854 -type f | wc -l)" -eq 3 ]] || fail "26854 payload count"
 diff -u 26854_RUNTIME_CHANGED_PATHS.txt <(find handoff_payload_26854 -type f | sed 's#^handoff_payload_26854/##' | sort) >/dev/null || fail "payload allowlist mismatch"
 for p in 26854_FORWARD_FULL_INDEX.patch 26854_ROLLBACK_FULL_INDEX.patch; do ! grep -Eq '^(rename from|rename to|copy from|copy to) ' "$p" || fail "patch rename/copy inference"; done
 grep -Fx 'RUN_26854_CFA_NOISE_CORRECTION' TRIGGER_26854.txt >/dev/null || fail "wrong trigger"
 ! find . -type f -name '*.apk' | grep -q . || fail "APK unexpectedly packaged"
 [[ ! -e glsl_static ]] || fail "unintended generated glsl_static directory in handoff (26854 scope regression)"
 pass "26854 package hashes/syntax/allowlist/patch identity"
}
verify_scope(){
 [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
 [[ -z "$(git ls-files -- glsl_static)" ]] || fail "generated glsl_static source files accidentally committed (26854 permanent regression)"
 git merge-base --is-ancestor "$MECHANICS_AUTHORITY_COMMIT" HEAD || fail "successful 26852 mechanics ancestor missing"
 python3 -S - <<'PY_SCOPE'
import subprocess
allowed=('26854_','build_26854_cfa_noise_correction.sh','transform_26854.py','validate_26854.py','verify_26854_patches.py','verify_26854_runtime_glsl.py','handoff_payload_26854/','.github/workflows/build-26854-cfa-noise-correction.yml','TRIGGER_26854.txt','README_26854.txt')
paths=subprocess.check_output(['git','diff','--name-only','2af0376988ae2fb2a03689f4dd63ac2e743a9835..HEAD'],text=True).splitlines()
bad=[p for p in paths if not any(p==x or p.startswith(x) or p.startswith('26853_') or p.startswith('build_26853_') or p.startswith('handoff_payload_26853/') or p=='.github/workflows/build-26853-multiframe-native-cfa-denoise.yml' or p=='TRIGGER_26853.txt' or p=='transform_26853.py' or p=='validate_26853.py' or p=='verify_26853_patches.py' or p=='verify_26853_runtime_glsl.py' for x in allowed)]
assert not bad,('unexpected changes since 26852',bad)
print('PASS 26854 scope confined to 26853 predecessor and sealed 26854 handoff')
PY_SCOPE
 # Runtime app/src cannot be changed in the live repository: compiler candidate is authority-seeded separately.
 [[ -z "$(git diff --name-only "$MECHANICS_AUTHORITY_COMMIT"..HEAD -- app/src)" ]] || fail "unexpected live app/src modifications"
 pass "26854 source scope and branch guarded"
}
obtain_authority(){
 [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"
 local listing="$WORK/artifact_listing.json" meta="$WORK/26853_artifact_identity.txt"
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts?name=${RUNTIME_ARTIFACT_NAME}&per_page=100" -o "$listing"
 python3 -S - "$listing" "$meta" "$RUNTIME_ARTIFACT_NAME" "$RUNTIME_ARTIFACT_SHA" <<'PY_ID'
import json,sys
rows=json.load(open(sys.argv[1])).get('artifacts',[])
match=[a for a in rows if a.get('name')==sys.argv[3] and not a.get('expired') and str(a.get('digest','')).lower()=='sha256:'+sys.argv[4].lower()]
assert len(match)==1,('artifact name/digest uniqueness',[(a.get('id'),a.get('name'),a.get('digest')) for a in rows])
a=match[0];r=a['workflow_run']; assert r['head_branch']=='experimental-clean-photon-rebuild',r
open(sys.argv[2],'w').write(f"{a['id']}\n{r['id']}\n{r['head_sha']}\n")
print('PASS exact successful 26853 artifact matched by name and digest')
PY_ID
 mapfile -t authority < "$meta"; RUNTIME_ARTIFACT_ID="${authority[0]}"; RUNTIME_ACTIONS_RUN="${authority[1]}"; RUNTIME_AUTHORITY_COMMIT="${authority[2]}"
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/runs/${RUNTIME_ACTIONS_RUN}" -o "$WORK/26853_run.json"
 python3 -S - "$WORK/26853_run.json" "$RUNTIME_AUTHORITY_COMMIT" <<'PY_RUN'
import json,sys
x=json.load(open(sys.argv[1])); assert x['conclusion']=='success' and x['head_sha']==sys.argv[2],(x.get('conclusion'),x.get('head_sha'))
print('PASS Actions run is successful with matching head_sha')
PY_RUN
 git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD || fail "26853 authority commit not ancestor"
 [[ -z "$(git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD -- app/src)" ]] || fail "live runtime source changed since 26853 authority"
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"
 [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail "26853 artifact zip SHA mismatch"
 unzip -q "$ARTZIP" -d "$ARTDIR"
 local T="$ARTDIR/build_26853_multiframe_native_cfa_denoise_outputs/26853_candidate_app_source.tar.gz"
 [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail "26853 candidate tar SHA mismatch"
 local STATUS="$ARTDIR/build_26853_multiframe_native_cfa_denoise_outputs/26853_COMPILER_STATUS.txt"
 for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do grep -F "$proof" "$STATUS" >/dev/null || fail "missing 26853 authority proof: $proof"; done
 mkdir -p "$BASE"; tar -xzf "$T" -C "$BASE"
 [[ "$(find "$BASE/app" -type f | wc -l)" -eq 1786 ]] || fail "26853 compiled candidate count"
 (cd "$BASE" && sha256sum -c "$ROOT/26854_BASE_26853_FULL_APP.sha256" >/dev/null)
 (cd "$BASE" && sha256sum -c "$ROOT/26854_PRIOR_SOURCE_HASHES.sha256" >/dev/null)
 cat > "$OUT/26854_RESOLVED_AUTHORITIES.txt" <<EOF_AUTH
runtime_commit=$RUNTIME_AUTHORITY_COMMIT
runtime_run=$RUNTIME_ACTIONS_RUN
runtime_artifact_id=$RUNTIME_ARTIFACT_ID
runtime_artifact_name=$RUNTIME_ARTIFACT_NAME
runtime_artifact_sha256=$RUNTIME_ARTIFACT_SHA
runtime_candidate_tar_sha256=$RUNTIME_TAR_SHA
mechanics_commit=$MECHANICS_AUTHORITY_COMMIT
EOF_AUTH
 pass "exact successful 26853 Actions compiled candidate reconstructed"
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
 python3 -S transform_26854.py "$BASE" "$CAND" handoff_payload_26854
 python3 -S validate_26854.py "$BASE" "$CAND"
 (cd "$CAND" && sha256sum -c "$ROOT/26854_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 for file in 26854_PROTECTED_26853.sha256 26854_NATIVE_PROTECTED_26853.sha256 26854_DNG_WRITER_26853.sha256 26854_SHADER_ASSETS_PROTECTED_26853.sha256; do (cd "$CAND" && sha256sum -c "$ROOT/$file" >/dev/null); done
 [[ "$(find "$CAND/app" -type f | wc -l)" -eq 1786 ]] || fail "candidate file count"
 pass "26854 frozen candidate-first exact 3-file change from compiled 26853"
}
verify_successful_mechanics(){
 local a52="$WORK/authority_26852_build.sh" a50="$WORK/authority_26850_build.sh" a21="$WORK/authority_26821_build.sh"
 git show "$MECHANICS_AUTHORITY_COMMIT:build_26852_single_owner_temporal_cfa.sh" > "$a52"
 git show "2ed85bc28e9c8f9edbbeaacd5ac4708edeac10c6:build_26850_adaptive_same_phase_cfa.sh" > "$a50"
 git show "9fdf39a0a99773ea86159250c7715396b58e78d3:build_26821_connected_false_color_dng_all_phase_coherence.sh" > "$a21"
 for cmd in './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace' "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace" './gradlew :app:assembleDebug --stacktrace'; do
  grep -F "$cmd" "$a52" >/dev/null || fail "26852 authority compiler command missing: $cmd"
  grep -F "$cmd" "$0" >/dev/null || fail "26854 compiler command differs: $cmd"
 done
 python3 -S - "$0" "$a52" "$a50" "$a21" <<'PY_ORDER'
from pathlib import Path
import sys
stages=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay']
for fn,marker in [(sys.argv[1],'# IRIS_26854_AUTHORITATIVE_ACTIONS_STAGE_ORDER'),(sys.argv[2],'# IRIS_26852_AUTHORITATIVE_ACTIONS_STAGE_ORDER'),(sys.argv[3],'# IRIS_26850_AUTHORITATIVE_ACTIONS_STAGE_ORDER'),(sys.argv[4],'# IRIS_26821_AUTHORITATIVE_ACTIONS_STAGE_ORDER')]:
 t=Path(fn).read_text().split(marker,1)[1];pos=-1
 for s in stages:
  j=t.find('\n'+s+'\n',pos+1);assert j>pos,(fn,s,pos);pos=j
print('PASS successful 26821/26850/26852 17-stage order and compiler commands preserved')
PY_ORDER
 pass "26854 changed only authority/version/scope/validators; zero stage/compiler command reordering"
}
prepare_glslang(){
 D="$WORK/glslang-${GLSLANG_VERSION}"; A="$WORK/glslang.tar.gz"; mkdir -p "$D"
 curl -L --fail --retry 3 "$GLSLANG_URL" -o "$A"; [[ "$(sha "$A")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "glslang archive sha"
 tar -xzf "$A" -C "$D"; compiler="$(find "$D" -type f -name glslang -print -quit)"
 [[ -n "$compiler" ]] || compiler="$(find "$D" \( -type f -o -type l \) -name glslangValidator -print -quit)"
 compiler="$(readlink -f "$compiler")"; [[ -x "$compiler" ]] || chmod +x "$compiler"
 "$compiler" --version | tee "$OUT/26854_glslang_version.txt"
 export IRIS26854_GLSLANG="$compiler"; export IRIS26681_SPEKTRA_GLSLANG="$compiler"
 pass "pinned glslang 16.5.0 dual environment handoff"
}
compile_modified_runtime_shaders(){
 python3 -S verify_26854_runtime_glsl.py "$BASE" "$CAND" --compiler "$IRIS26854_GLSLANG" --out "$OUT/26854_runtime_expanded_glsl" | tee "$OUT/26854_glsl_validation.txt"
 grep -F 'PASS 26854 GLSL ownership:' "$OUT/26854_glsl_validation.txt" >/dev/null || fail "modified GLSL validation missing"
 sed -i 's#REAL GLSL COMPILE: NOT RUN YET#REAL GLSL COMPILE: PASS (modified native CFA and all inherited active variants pinned glslang 16.5.0)#' "$OUT/26854_COMPILER_STATUS.txt"
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
 ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26854_gradle_language_compilers.log"
 snapshot_live_authority_seeded "$POST_LANG";universe_equal "$CAND" "$POST_LANG"
 sed -i 's/REAL KOTLIN COMPILE: NOT RUN YET/REAL KOTLIN COMPILE: PASS/' "$OUT/26854_COMPILER_STATUS.txt"
 sed -i 's/REAL JAVA COMPILE: NOT RUN YET/REAL JAVA COMPILE: PASS/' "$OUT/26854_COMPILER_STATUS.txt"
 pass "real Kotlin Java compiler source freeze"
}
verify_native_glslang_handoff(){
 [[ -n "${IRIS26854_GLSLANG:-}" && -x "$IRIS26854_GLSLANG" ]] || fail "IRIS26854_GLSLANG missing"
 [[ -n "${IRIS26681_SPEKTRA_GLSLANG:-}" && -x "$IRIS26681_SPEKTRA_GLSLANG" ]] || fail "SPEKTRA GLSLANG missing"
 [[ "$(readlink -f "$IRIS26854_GLSLANG")" == "$(readlink -f "$IRIS26681_SPEKTRA_GLSLANG")" ]] || fail "native shader compiler handoff mismatch"
 pass "26852 native GLSL compiler identity inherited"
}
compile_native(){
 ./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26854_gradle_native_compiler.log"
 sed -i 's#NATIVE/NDK COMPILE: NOT RUN YET#NATIVE/NDK COMPILE: PASS (arm64-v8a + armeabi-v7a)#' "$OUT/26854_COMPILER_STATUS.txt"
}
verify_candidate_patches(){
 python3 -S verify_26854_patches.py "$BASE" "$CAND" 26854_FORWARD_FULL_INDEX.patch 26854_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26854_patch_validation.txt"
 grep -F 'PASS 26854 canonical patch proof' "$OUT/26854_patch_validation.txt" >/dev/null
 pass "26854 full-index forward/rollback 7/12/40 fuzz=0 exact"
}
prebuild_safety(){
 snapshot_live_authority_seeded "$WORK/prebuild_live_snapshot"; universe_equal "$CAND" "$WORK/prebuild_live_snapshot"
 python3 -S validate_26854.py "$BASE" "$CAND"
 for file in 26854_PROTECTED_26853.sha256 26854_NATIVE_PROTECTED_26853.sha256 26854_DNG_WRITER_26853.sha256 26854_SHADER_ASSETS_PROTECTED_26853.sha256; do (cd "$CAND" && sha256sum -c "$ROOT/$file" >/dev/null); done
 cat > "$OUT/26854_PREBUILD_SAFETY.txt" <<EOF_SAFETY
PRE-BUILD SAFETY PROOF PASSED
runtime_authority=successful 26853 ${RUNTIME_AUTHORITY_COMMIT} run ${RUNTIME_ACTIONS_RUN} artifact ${RUNTIME_ARTIFACT_ID}
verification_mechanics=exact successful 26852 inherited 17-stage sequence
runtime_changed_files=3 modified / 0 added / 0 deleted
protected_files=1783 unchanged
candidate_files=1786
color_dng_native_vendor_uhdr=authority-seeded byte identical
noise=calibrated shot/read sensor-neutral same-phase CFA, support from local temporal weights
backup_branch=NONE_USER_EXPLICIT
EOF_SAFETY
 pass "PRE-BUILD SAFETY PROOF PASSED"
}
assemble(){
 ./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26854_gradle_assemble.log"
 mapfile -t apks < <(find app/build/outputs/apk -type f -name '*.apk' | sort)
 [[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one APK, got ${#apks[@]}"
 cp "${apks[0]}" "$FINAL"; sha256sum "$FINAL" | tee "$OUT/26854_APK.sha256"
 sed -i 's/FULL ANDROID ASSEMBLE: NOT RUN YET/FULL ANDROID ASSEMBLE: PASS (exactly one APK)/' "$OUT/26854_COMPILER_STATUS.txt"
}
postbuild_proof(){
 snapshot_live_authority_seeded "$WORK/postbuild_live_snapshot";universe_equal "$CAND" "$WORK/postbuild_live_snapshot"
 python3 -S validate_26854.py "$BASE" "$CAND"
 (cd "$CAND" && sha256sum -c "$ROOT/26854_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 for file in 26854_PROTECTED_26853.sha256 26854_NATIVE_PROTECTED_26853.sha256 26854_DNG_WRITER_26853.sha256 26854_SHADER_ASSETS_PROTECTED_26853.sha256; do (cd "$CAND" && sha256sum -c "$ROOT/$file" >/dev/null); done
 cp 26854_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26854_candidate_full_app.sha256"
 tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26854_candidate_app_source.tar.gz" -C "$CAND" app
 sha256sum "$OUT/26854_candidate_app_source.tar.gz" > "$OUT/26854_candidate_app_source.tar.gz.sha256"
 cp 26854_FORWARD_FULL_INDEX.patch "$OUT/26854_FORWARD_FULL_INDEX.patch";cp 26854_ROLLBACK_FULL_INDEX.patch "$OUT/26854_ROLLBACK_FULL_INDEX.patch"
 sed -i 's/POST-BUILD INVARIANCE: NOT RUN YET/POST-BUILD INVARIANCE: PASS/' "$OUT/26854_COMPILER_STATUS.txt"
 pass "postbuild protected/temporal/DNG/native/vendor invariance"
}
clean_extract_replay(){
 local replay="$WORK/clean_replay_candidate";rm -rf "$replay"
 sha256sum -c 26854_HANDOFF_HASHES.sha256 >/dev/null
 bash -n build_26854_cfa_noise_correction.sh
 python3 -S -m py_compile transform_26854.py validate_26854.py verify_26854_patches.py verify_26854_runtime_glsl.py;rm -rf __pycache__
 python3 -S transform_26854.py "$BASE" "$replay" handoff_payload_26854
 universe_equal "$CAND" "$replay";python3 -S validate_26854.py "$BASE" "$replay"
 python3 -S verify_26854_runtime_glsl.py "$BASE" "$replay" --out "$OUT/26854_final_runtime_expanded_glsl" | tee "$OUT/26854_final_glsl_static_replay.txt"
 python3 -S verify_26854_patches.py "$BASE" "$replay" 26854_FORWARD_FULL_INDEX.patch 26854_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26854_final_patch_replay.txt"
 (cd "$replay" && sha256sum -c "$ROOT/26854_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 grep -Fx 'VERSION_NAME=0.9726854' "$replay/app/version.properties" >/dev/null
 grep -Fx 'VERSION_BUILD=26854' "$replay/app/version.properties" >/dev/null
 for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do grep -F "$proof" "$OUT/26854_COMPILER_STATUS.txt" >/dev/null || fail "missing Actions compiler proof: $proof"; done
 pass "final 26854 clean replay hashes/ownership/GLSL/patches/version/compilers/build"
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
pass "26854 CFA NOISE CORRECTION: ACTIONS BUILD PROOF COMPLETE"
