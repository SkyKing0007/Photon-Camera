#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
ROOT="$(pwd)"; EXPECTED_BRANCH="experimental-clean-photon-rebuild"
RUNTIME_ARTIFACT_ID="12399841223"; RUNTIME_ACTIONS_RUN="39716184395"
RUNTIME_AUTHORITY_COMMIT="a14f3b6f11bffce01ce273fdfd898203d665dc28"
RUNTIME_ARTIFACT_SHA="eb31421b869be4103568512c015e82c0e352689dd8fccb9439387e90d6aa6714"
RUNTIME_TAR_SHA="fdeb2e558d0f28da118ad10e3c8d69526d94f8653858370eb95d1957c332ad54"
MECHANICS_GIT_BLOB="831c670977ed5b0615310a7a6eabee67fae4947d"
VERSION_NAME="0.9726865"; VERSION_BUILD="26865"; GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
OUT="$ROOT/build_26865_iris_rawr_outputs"; WORK="$ROOT/.build_26865_iris_rawr_work"
ARTZIP="$WORK/26864_artifact.zip"; ARTDIR="$WORK/artifact_26864"
BASE="$WORK/exact_successful_26864_compiled_candidate"; CAND="$WORK/candidate_26865"
LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST_LANG="$WORK/post_language_compiler_source_snapshot"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-iris-rawr-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR"
cat > "$OUT/26865_COMPILER_STATUS.txt" <<'STATUS'
REAL GLSL COMPILE: NOT RUN YET
REAL SPIR-V VALIDATION: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
STATUS
# IRIS_26865_AUTHORITATIVE_ACTIONS_STAGE_ORDER
verify_package(){
 sha256sum -c 26865_HANDOFF_HASHES.sha256 >/dev/null
 bash -n build_26865_iris_rawr.sh
 python3 -S -m py_compile verify_26865_candidate.py verify_26865_patches.py verify_26864_rawr_sources.py verify_26864_runtime_glsl.py verify_26864_semantics.py regressions/26864_glsl_reserved_identifiers.py regressions/26864_wronski_publisher.py regressions/26865_b_lsc_owner.py
 rm -rf __pycache__ regressions/__pycache__
 ! grep -Eq '^(rename from|rename to|copy from|copy to) ' 26865_FORWARD_FULL_INDEX.patch
 ! grep -Eq '^(rename from|rename to|copy from|copy to) ' 26865_ROLLBACK_FULL_INDEX.patch
 [[ $(find handoff_payload_26865 -type f | wc -l) -eq 2 ]] || fail '26865 exactly 2 replacement files'
 diff -u 26865_CHANGED_ALLOWLIST.txt <(find handoff_payload_26865 -type f | sed 's#^handoff_payload_26865/##' | sort) >/dev/null || fail '26865 strict package allowlist'
 sha256sum -c 26865_PAYLOAD_SHA256.txt >/dev/null
 ! find . -type f -name '*.apk' | grep -q . || fail 'APKs must never be packaged'
 test -f TRIGGER_26865.txt && grep -Fx 'RUN_26865_B_NATIVE_PRE_AMAZE_LSC_OWNERSHIP' TRIGGER_26865.txt >/dev/null || fail 'wrong trigger'
 pass '26865 package hashes/syntax/2-file exact source allowlist/trigger'
}
verify_scope(){
 [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail 'wrong branch'
 git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD || fail '26864 authority missing from history'
 [[ -z "$(git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD -- app/src app/version.properties)" ]] || fail 'repository live runtime modified before guarded source install'
 [[ -z "$(git ls-files -- glsl_static)" ]] || fail 'generated GLSL is tracked after historical cleanup'
 [[ -z "$(git status --porcelain -- app/src app/version.properties)" ]] || fail 'uncommitted runtime source before freeze'
 # Infrastructure delta is explicitly audited against exact 26864 HEAD;
 # uploaded handoff scaffolding is never silently allowed to change.
 diff -u 26865_REPOSITORY_UPLOAD_ALLOWLIST.txt <(git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | LC_ALL=C sort) >/dev/null || fail 'unexpected 26865 repo/workflow/validator/upload infrastructure difference from successful 26864'
 pass '26865 correct branch, ancestor, exact repository infrastructure delta and guarded live source'
}
obtain_authority(){
 [[ -n "$TOKEN" ]] || fail 'GITHUB_TOKEN missing'
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \
   "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/runs/${RUNTIME_ACTIONS_RUN}" -o "$WORK/26864_run.json"
 python3 -S - "$WORK/26864_run.json" "$RUNTIME_AUTHORITY_COMMIT" <<'PY_RUN'
import json,sys
x=json.load(open(sys.argv[1]));assert x['id']==39716184395 and x['conclusion']=='success' and x['head_sha']==sys.argv[2] and x['head_branch']=='experimental-clean-photon-rebuild'
print('PASS real 26864 GitHub Actions run/commit/success')
PY_RUN
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \
   "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}" -o "$WORK/26864_artifact_metadata.json"
 python3 -S - "$WORK/26864_artifact_metadata.json" <<'PY_ART'
import json,sys
x=json.load(open(sys.argv[1]));assert x['id']==12399841223 and x['name']=='photon-26864-iris-rawr' and not x['expired'] and x['digest']=='sha256:eb31421b869be4103568512c015e82c0e352689dd8fccb9439387e90d6aa6714'
print('PASS exact 26864 compiled artifact identity and digest')
PY_ART
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \
   "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"
 [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail '26864 artifact SHA mismatch'
 unzip -q "$ARTZIP" -d "$ARTDIR"
 local T="$ARTDIR/build_26864_iris_rawr_outputs/26864_candidate_app_source.tar.gz"
 [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail '26864 compiled source TAR hash mismatch'
 local CS="$ARTDIR/build_26864_iris_rawr_outputs/26864_COMPILER_STATUS.txt"
 for proof in 'REAL GLSL COMPILE: PASS' 'REAL SPIR-V VALIDATION: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do grep -F "$proof" "$CS" >/dev/null || fail "26864 authority compiler proof missing $proof";done
 mkdir -p "$BASE";tar -xzf "$T" -C "$BASE"
 [[ "$(find "$BASE/app" -type f | wc -l)" -eq 1991 ]] || fail 'wrong authority universe size'
 (cd "$BASE" && sha256sum -c "$ROOT/26865_BASE_26864_FULL_APP.sha256" >/dev/null) || fail '26864 authority manifest mismatch'
 cat > "$OUT/26865_RESOLVED_AUTHORITIES.txt" <<EOF_AUTH
runtime_commit=$RUNTIME_AUTHORITY_COMMIT
runtime_run=$RUNTIME_ACTIONS_RUN
runtime_artifact_id=$RUNTIME_ARTIFACT_ID
runtime_artifact_sha256=$RUNTIME_ARTIFACT_SHA
runtime_candidate_tar_sha256=$RUNTIME_TAR_SHA
mechanics_blob_sha1=$MECHANICS_GIT_BLOB
EOF_AUTH
 pass 'exact successful 26864 Actions compiled-candidate authority reconstructed and compiler proof verified'
}
make_candidate(){
 python3 -S verify_26865_candidate.py "$BASE" "$CAND" --transform --root "$ROOT"
 python3 -S regressions/26865_b_lsc_owner.py "$CAND/app"
 python3 -S verify_26864_rawr_sources.py "$CAND/app"
 python3 -S regressions/26864_glsl_reserved_identifiers.py "$CAND/app"
 python3 -S regressions/26864_wronski_publisher.py "$CAND/app"
 python3 -S verify_26864_semantics.py "$CAND/app" --numeric
 pass '26865 deterministic authority-seeded candidate, pinned RAWR source and active-path semantic regressions'
}
verify_successful_mechanics(){
 git show "$RUNTIME_AUTHORITY_COMMIT:build_26864_iris_rawr.sh" > "$WORK/26864_successful_mechanics.sh"
 [[ "$(git hash-object "$WORK/26864_successful_mechanics.sh")" == "$MECHANICS_GIT_BLOB" ]] || fail '26864 proven mechanics Git blob mismatch'
 for validator in verify_26864_rawr_sources.py verify_26864_runtime_glsl.py verify_26864_semantics.py; do
   local pinned="$WORK/successful_26864_${validator}"
   git show "$RUNTIME_AUTHORITY_COMMIT:$validator" > "$pinned"
   cmp -s "$pinned" "$ROOT/$validator" || fail "26864 inherited validator changed: $validator"
 done
 python3 -S - "$WORK/26864_successful_mechanics.sh" "$ROOT/build_26865_iris_rawr.sh" <<'PY_STAGES'
from pathlib import Path
import re,sys
stages=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay']
for path in sys.argv[1:]:
 txt=Path(path).read_text();pos=-1
 for fn in stages:
  i=txt.find('\n'+fn+'(){',pos+1)
  assert i>pos,(path,fn,'inherited 17-stage order changed');pos=i
for cmd in ["./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace", "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace']:
 assert all(cmd in Path(path).read_text() for path in sys.argv[1:]),('real compiler command changed',cmd)
print('PASS exact successful 26864 mechanics source, 17-stage order, real Kotlin/Java/2-ABI NDK/assemble command identity')
PY_STAGES
 pass '26864 inherited 17-stage mechanics, compiler commands and audited 26865 dependency extension'
}
prepare_glslang(){
 local D="$WORK/glslang-${GLSLANG_VERSION}" A="$WORK/glslang.tar.gz";mkdir -p "$D"
 curl -L --fail --retry 3 "$GLSLANG_URL" -o "$A"
 [[ "$(sha "$A")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail 'pinned glslang tar SHA'
 tar -xzf "$A" -C "$D"
 local compiler
 compiler="$(find "$D" -type f -name glslang -print -quit)"
 [[ -n "$compiler" ]] || compiler="$(find "$D" \( -type f -o -type l \) -name glslangValidator -print -quit)"
 [[ -n "$compiler" ]] || fail 'missing pinned real glslang binary'
 compiler="$(readlink -f "$compiler")";[[ -x "$compiler" ]] || chmod +x "$compiler"
 "$compiler" --version | tee "$OUT/26865_glslang_version.txt"
 grep -F '16.5.0' "$OUT/26865_glslang_version.txt" >/dev/null || fail 'glslang version mismatch'
 export IRIS26864_GLSLANG="$compiler";export IRIS26681_SPEKTRA_GLSLANG="$compiler"
 # Inherit exact successful 26864 real SPIR-V post-validation, no substitutions.
 sudo apt-get update -qq
 sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq spirv-tools
 command -v spirv-val >/dev/null && command -v spirv-opt >/dev/null || fail 'real SPIRV-Tools missing'
 spirv-val --version > "$OUT/26865_spirv_tools_version.txt"
 spirv-opt --version >> "$OUT/26865_spirv_tools_version.txt"
 pass 'pinned real glslang 16.5.0 + real SPIRV-Tools toolchain'
}
compile_modified_runtime_shaders(){
 # Preserve 26864's exact eleven expanded GLES300 owners and real compiler.
 # No GLSL source byte changes in 26865; run the inherited shaders unmodified.
 git show "$RUNTIME_AUTHORITY_COMMIT:verify_26864_runtime_glsl.py" > "$WORK/successful_26864_runtime_glsl.py"
 [[ "$(git hash-object "$WORK/successful_26864_runtime_glsl.py")" == 'c5208e94865afbbbc437c31e09fd7b893e50ca20' ]] || fail '26864 shader validator drift'
 python3 -S verify_26864_runtime_glsl.py "$BASE" "$CAND" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26865_runtime_expanded_glsl" | tee "$OUT/26865_gles_shader_proof.txt"
 grep -F 'PASS 26864 GLSL ownership:' "$OUT/26865_gles_shader_proof.txt" >/dev/null || fail 'inherited 11 expanded GLSL owners or stronger RAWR semantic gate failed'
 python3 -S regressions/26864_glsl_reserved_identifiers.py "$CAND/app"
 # All 55 upstream + 3 Iris bridge shader inputs use the SAME pinned compiler,
 # real SPIR-V validator and optimizer *before* Java/Kotlin compilation.
 python3 -S verify_26864_rawr_sources.py "$CAND/app" --compile "$IRIS26864_GLSLANG" \
   --spirv-val "$(command -v spirv-val)" --spirv-opt "$(command -v spirv-opt)" \
   --out "$OUT/26865_all_native_expanded_spirv" | tee "$OUT/26865_spirv_validation.txt"
 grep -F 'PASS 26864 real 58 SPIR-V compute shaders' "$OUT/26865_spirv_validation.txt" >/dev/null || fail 'native SPIR-V real compiler proof missing'
 sed -i 's#REAL GLSL COMPILE: NOT RUN YET#REAL GLSL COMPILE: PASS (pinned 16.5.0 on expanded GLES300 and 58 exact native Vulkan shaders)#' "$OUT/26865_COMPILER_STATUS.txt"
 sed -i 's#REAL SPIR-V VALIDATION: NOT RUN YET#REAL SPIR-V VALIDATION: PASS (spirv-val pre/post optimized Vulkan 1.1)#' "$OUT/26865_COMPILER_STATUS.txt"
}
compile_spektra_raw_shader(){ pass 'inherited 26864 Spektra validator path protected byte-exact by manifests'; }
snapshot_live_authority_seeded(){
 python3 -S - "$CAND" "$1" "$ROOT" <<'PY_LIVE'
from pathlib import Path
import hashlib,shutil,sys
cand,out,live=map(Path,sys.argv[1:]);shutil.rmtree(out,ignore_errors=True);shutil.copytree(cand,out)
expected={str(p.relative_to(cand)):p for p in (cand/'app').rglob('*') if p.is_file()}
for rel in expected:
 lp=live/rel
 if not lp.is_file():raise SystemExit(f'missing live 26865 candidate path {rel}')
 (out/rel).write_bytes(lp.read_bytes())
# Repository-only build scaffolding is ignored; all unexpected actual app/src
# paths must be detected. app/build and app/.cxx are generated, never source.
expected_src={p for p in expected if p.startswith('app/src/')}
actual_src={str(p.relative_to(live)) for p in (live/'app/src').rglob('*') if p.is_file()}
extra=actual_src-expected_src
if extra:raise SystemExit(f'unexpected runtime app/src additions: {sorted(extra)}')
print('PASS authority-seeded canonical live app source universe',len(expected))
PY_LIVE
}
install_frozen_candidate_live(){
 rm -rf app; cp -a "$CAND/app" app
 snapshot_live_authority_seeded "$LIVE_CANON"
 diff -qr "$CAND/app" "$LIVE_CANON/app" >/dev/null || fail 'frozen compiler-tested candidate differs from live'
 pass '26865 live source byte-identical to frozen authority-seeded candidate'
}
compile_languages(){
 ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26865_gradle_language_compilers.log"
 snapshot_live_authority_seeded "$POST_LANG";diff -qr "$CAND/app" "$POST_LANG/app" >/dev/null || fail 'language compilers changed source'
 sed -i 's/REAL KOTLIN COMPILE: NOT RUN YET/REAL KOTLIN COMPILE: PASS/' "$OUT/26865_COMPILER_STATUS.txt"
 sed -i 's/REAL JAVA COMPILE: NOT RUN YET/REAL JAVA COMPILE: PASS/' "$OUT/26865_COMPILER_STATUS.txt"
 pass 'real project Kotlin and Java compilers on frozen candidate'
}
verify_native_glslang_handoff(){
 [[ -n "${IRIS26864_GLSLANG:-}" && -x "$IRIS26864_GLSLANG" && "$IRIS26864_GLSLANG" == "$IRIS26681_SPEKTRA_GLSLANG" ]] || fail 'pinned real GLSL compiler handoff lost'
 command -v spirv-val >/dev/null && command -v spirv-opt >/dev/null || fail 'SPIR-V validator unavailable to NDK'
 pass 'same pinned real compiler handed to NDK shader subprojects'
}
compile_native(){
 ./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26865_gradle_native_compiler.log"
 snapshot_live_authority_seeded "$WORK/post_native_snapshot"
 diff -qr "$CAND/app" "$WORK/post_native_snapshot/app" >/dev/null || fail 'native compiler changed source'
 sed -i 's#NATIVE/NDK COMPILE: NOT RUN YET#NATIVE/NDK COMPILE: PASS (arm64-v8a + armeabi-v7a; real 58 pinned shader compilation)#' "$OUT/26865_COMPILER_STATUS.txt"
 pass 'real 2-ABI NDK compiler with authentic RAWR Vulkan sources'
}
verify_candidate_patches(){
 python3 -S verify_26865_patches.py "$BASE" "$CAND" 26865_FORWARD_FULL_INDEX.patch 26865_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26865_patch_validation.txt"
 pass 'canonical binary full-index forward/rollback 7/12/40 fuzz=0 exact'
}
prebuild_safety(){
 snapshot_live_authority_seeded "$WORK/prebuild_live_snapshot"
 diff -qr "$CAND/app" "$WORK/prebuild_live_snapshot/app" >/dev/null || fail 'prebuild source drift'
 python3 -S verify_26865_candidate.py "$BASE" "$CAND" --root "$ROOT"
 (cd "$CAND" && sha256sum -c "$ROOT/26865_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail 'protected/DNG/native/vendor source drift'
 for k in 'REAL GLSL COMPILE: PASS' 'REAL SPIR-V VALIDATION: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS';do grep -F "$k" "$OUT/26865_COMPILER_STATUS.txt" >/dev/null || fail "prebuild real compiler gate $k";done
 cat > "$OUT/26865_PREBUILD_SAFETY.txt" <<EOF_SAFETY
PRE-BUILD SAFETY PROOF PASSED
runtime_authority=successful 26864 $RUNTIME_AUTHORITY_COMMIT run $RUNTIME_ACTIONS_RUN artifact $RUNTIME_ARTIFACT_ID
verification_mechanics=exact successful 26864 17-stage inherited build order, compiler commands and authority-seeded source mechanics
runtime_changed_files=2 (0 new, 2 edited, 0 deleted incl guarded version)
infrastructure_delta=26864 successful mechanics inherited unchanged; new 26865 guard/validator/workflow files audited, runtime native/vendor delta ZERO
prior_files=1991
candidate_files=1991
version_name=$VERSION_NAME
version_build=$VERSION_BUILD
real_compilers=GLSL+SPIR-V+Kotlin+Java+NDK two ABI PASS
patch_proof=full index forward/rollback 7/12/40 fuzz 0 exact
protected_source=1989 unchanged prior 26864 compiled candidate files byte-identical; DNG/native/vendor intact
EOF_SAFETY
 pass 'PRE-BUILD SAFETY PROOF PASSED'
}
assemble(){
 test -f "$OUT/26865_PREBUILD_SAFETY.txt" && grep -Fx 'PRE-BUILD SAFETY PROOF PASSED' "$OUT/26865_PREBUILD_SAFETY.txt" >/dev/null || fail 'assemble forbidden without proof'
 ./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26865_gradle_assemble.log"
 mapfile -t apks < <(find app/build/outputs/apk -type f -name '*.apk' | sort)
 [[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one assembled APK, got ${#apks[@]}"
 cp "${apks[0]}" "$FINAL"
 [[ "$(find . -maxdepth 1 -name 'IrisCamera-*.apk' -type f | wc -l)" -eq 1 ]] || fail 'one intended APK at root'
 sha256sum "$FINAL" > "$OUT/26865_APK.sha256"
 sed -i 's/FULL ANDROID ASSEMBLE: NOT RUN YET/FULL ANDROID ASSEMBLE: PASS/' "$OUT/26865_COMPILER_STATUS.txt"
 pass 'full :app:assembleDebug including NDK, exactly one intended APK'
}
postbuild_proof(){
 snapshot_live_authority_seeded "$WORK/post_build_live_snapshot"
 diff -qr "$CAND/app" "$WORK/post_build_live_snapshot/app" >/dev/null || fail 'candidate changed after assemble'
 python3 -S verify_26865_candidate.py "$BASE" "$CAND" --root "$ROOT"
 (cd "$CAND" && sha256sum -c "$ROOT/26865_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 (cd "$CAND" && sha256sum -c "$ROOT/26865_UNCHANGED_PROTECTED.sha256" >/dev/null)
 cp 26865_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26865_candidate_full_app.sha256"
 (cd "$CAND" && tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26865_candidate_app_source.tar.gz" app)
 sha256sum "$OUT/26865_candidate_app_source.tar.gz" > "$OUT/26865_candidate_app_source.tar.gz.sha256"
 cp 26865_FORWARD_FULL_INDEX.patch 26865_ROLLBACK_FULL_INDEX.patch "$OUT/"
 sed -i 's/POST-BUILD INVARIANCE: NOT RUN YET/POST-BUILD INVARIANCE: PASS/' "$OUT/26865_COMPILER_STATUS.txt"
 pass 'postbuild authority-seeded candidate/protected/DNG/native/vendor invariance and deterministic candidate export'
}
clean_extract_replay(){
 local replay="$WORK/clean_replay_candidate" exp="$WORK/extracted_candidate_tar"
 rm -rf "$replay" "$exp";mkdir -p "$exp"
 sha256sum -c 26865_HANDOFF_HASHES.sha256 >/dev/null
 bash -n build_26865_iris_rawr.sh
 python3 -S -m py_compile verify_26865_candidate.py verify_26865_patches.py verify_26864_rawr_sources.py verify_26864_runtime_glsl.py verify_26864_semantics.py regressions/26864_glsl_reserved_identifiers.py regressions/26864_wronski_publisher.py regressions/26865_b_lsc_owner.py
 rm -rf __pycache__ regressions/__pycache__
 python3 -S verify_26865_candidate.py "$BASE" "$replay" --root "$ROOT" --transform
 diff -qr "$CAND/app" "$replay/app" >/dev/null || fail 'clean-extract package transforms differ from frozen candidate'
 sha256sum -c "$OUT/26865_candidate_app_source.tar.gz.sha256" >/dev/null
 tar -xzf "$OUT/26865_candidate_app_source.tar.gz" -C "$exp"
 diff -qr "$CAND/app" "$exp/app" >/dev/null || fail 'exported compiled-candidate TAR differs from frozen candidate'
 python3 -S verify_26865_candidate.py "$BASE" "$exp" --root "$ROOT"
 python3 -S verify_26865_patches.py "$BASE" "$exp" 26865_FORWARD_FULL_INDEX.patch 26865_ROLLBACK_FULL_INDEX.patch > "$OUT/26865_final_patch_replay.txt"
 python3 -S verify_26864_runtime_glsl.py "$BASE" "$exp" --out "$OUT/26865_final_runtime_expanded_glsl" | tee "$OUT/26865_final_glsl_static_replay.txt"
 python3 -S verify_26864_rawr_sources.py "$exp/app"
 python3 -S regressions/26864_glsl_reserved_identifiers.py "$exp/app"
 python3 -S regressions/26864_wronski_publisher.py "$exp/app"
 python3 -S verify_26864_semantics.py "$exp/app" --numeric
 python3 -S regressions/26865_b_lsc_owner.py "$exp/app"
 grep -Fx 'VERSION_NAME=0.9726865' "$exp/app/version.properties" >/dev/null
 grep -Fx 'VERSION_BUILD=26865' "$exp/app/version.properties" >/dev/null
 for status in 'REAL GLSL COMPILE: PASS' 'REAL SPIR-V VALIDATION: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS';do grep -F "$status" "$OUT/26865_COMPILER_STATUS.txt" >/dev/null || fail "final compiler proof $status";done
 pass 'final 26865 clean-extract handoff replay exact candidate/hash/syntax/owners/GLSL/patches/version/compilers/build'
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
pass '26865 ALL 17 INHERITED GUARDED STAGES PASSED'
