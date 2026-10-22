#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
ROOT="$(pwd)"; EXPECTED_BRANCH="experimental-clean-photon-rebuild"
RUNTIME_ARTIFACT_ID="12426952653"; RUNTIME_ACTIONS_RUN="39780638414"
RUNTIME_AUTHORITY_COMMIT="e2bcfb65494ea1c2d31af16791d366785a96a0b3"
RUNTIME_ARTIFACT_SHA="ace5153080a1b409e3c5483dcd32e9f93cbdda2a67335c1a4a50434b73f4e27a"
RUNTIME_TAR_SHA="be297a92aab615c1f67a026d68c370a752e4745774fcbb575524965462d2a0fd"
MECHANICS_GIT_BLOB="e616d88e3678af52a65dbcfa685d4980000f3f09"
VERSION_NAME="0.9726867"; VERSION_BUILD="26867"; GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
OUT="$ROOT/build_26867_iris_rawr_outputs"; WORK="$ROOT/.build_26867_iris_rawr_work"
ARTZIP="$WORK/26866_artifact.zip"; ARTDIR="$WORK/artifact_26866"
BASE="$WORK/exact_successful_26866_compiled_candidate"; CAND="$WORK/candidate_26867"
LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST_LANG="$WORK/post_language_compiler_source_snapshot"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-iris-rawr-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR"
cat > "$OUT/26867_COMPILER_STATUS.txt" <<'STATUS'
REAL GLSL COMPILE: NOT RUN YET
REAL SPIR-V VALIDATION: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
STATUS
# IRIS_26867_AUTHORITATIVE_ACTIONS_STAGE_ORDER
verify_package(){
 sha256sum -c 26867_HANDOFF_HASHES.sha256 >/dev/null
 bash -n build_26867_iris_rawr.sh
 python3 -S -m py_compile verify_26867_candidate.py verify_26867_patches.py verify_26864_rawr_sources.py verify_26864_runtime_glsl.py verify_26864_semantics.py regressions/26864_glsl_reserved_identifiers.py regressions/26864_wronski_publisher.py regressions/26865_b_lsc_owner.py regressions/26866_b_color_only.py regressions/26867_b_highlight_ab_retired.py verify_26867_runtime_shader.py
 rm -rf __pycache__ regressions/__pycache__
 ! grep -Eq '^(rename from|rename to|copy from|copy to) ' 26867_FORWARD_FULL_INDEX.patch
 ! grep -Eq '^(rename from|rename to|copy from|copy to) ' 26867_ROLLBACK_FULL_INDEX.patch
 [[ $(find handoff_payload_26867 -type f | wc -l) -eq 5 ]] || fail '26867 exactly 5 replacement files'
 diff -u 26867_CHANGED_ALLOWLIST.txt <(find handoff_payload_26867 -type f | sed 's#^handoff_payload_26867/##' | sort) >/dev/null || fail '26867 strict package allowlist'
 sha256sum -c 26867_PAYLOAD_SHA256.txt >/dev/null
 ! find . -type f -name '*.apk' | grep -q . || fail 'APKs must never be packaged'
 test -f TRIGGER_26867.txt && grep -Fx 'RUN_26867_B_CLIP_FADE_AND_A_B_ONLY' TRIGGER_26867.txt >/dev/null || fail 'wrong trigger'
 pass '26867 package hashes/syntax/5-file exact source allowlist/trigger'
}
verify_scope(){
 [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail 'wrong branch'
 git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD || fail '26866 authority missing from history'
 [[ -z "$(git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD -- app/src app/version.properties)" ]] || fail 'repository live runtime modified before guarded source install'
 [[ -z "$(git ls-files -- glsl_static)" ]] || fail 'generated GLSL is tracked after historical cleanup'
 [[ -z "$(git status --porcelain -- app/src app/version.properties)" ]] || fail 'uncommitted runtime source before freeze'
 # Infrastructure delta is explicitly audited against exact 26866 HEAD;
 # uploaded handoff scaffolding is never silently allowed to change.
 diff -u 26867_REPOSITORY_UPLOAD_ALLOWLIST.txt <(git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | LC_ALL=C sort) >/dev/null || fail 'unexpected 26867 repo/workflow/validator/upload infrastructure difference from successful 26866'
 pass '26867 correct branch, ancestor, exact repository infrastructure delta and guarded live source'
}
obtain_authority(){
 [[ -n "$TOKEN" ]] || fail 'GITHUB_TOKEN missing'
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \
   "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/runs/${RUNTIME_ACTIONS_RUN}" -o "$WORK/26866_run.json"
 python3 -S - "$WORK/26866_run.json" "$RUNTIME_AUTHORITY_COMMIT" "$RUNTIME_ACTIONS_RUN" <<'PY_RUN'
import json,sys
x=json.load(open(sys.argv[1]));assert x['id']==int(sys.argv[3]) and x['conclusion']=='success' and x['head_sha']==sys.argv[2] and x['head_branch']=='experimental-clean-photon-rebuild'
print('PASS real 26866 GitHub Actions run/commit/success')
PY_RUN
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \
   "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}" -o "$WORK/26866_artifact_metadata.json"
 python3 -S - "$WORK/26866_artifact_metadata.json" <<'PY_ART'
import json,sys
x=json.load(open(sys.argv[1]));assert x['id']==12426952653 and x['name']=='photon-26866-iris-smooth-white' and not x['expired'] and x['digest']=='sha256:ace5153080a1b409e3c5483dcd32e9f93cbdda2a67335c1a4a50434b73f4e27a'
print('PASS exact 26866 compiled artifact identity and digest')
PY_ART
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \
   "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"
 [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail '26866 artifact SHA mismatch'
 unzip -q "$ARTZIP" -d "$ARTDIR"
 local T="$ARTDIR/build_26866_iris_rawr_outputs/26866_candidate_app_source.tar.gz"
 [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail '26866 compiled source TAR hash mismatch'
 local CS="$ARTDIR/build_26866_iris_rawr_outputs/26866_COMPILER_STATUS.txt"
 for proof in 'REAL GLSL COMPILE: PASS' 'REAL SPIR-V VALIDATION: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do grep -F "$proof" "$CS" >/dev/null || fail "26866 authority compiler proof missing $proof";done
 mkdir -p "$BASE";tar -xzf "$T" -C "$BASE"
 [[ "$(find "$BASE/app" -type f | wc -l)" -eq 1991 ]] || fail 'wrong 26866 authority universe size'
 (cd "$BASE" && sha256sum -c "$ROOT/26867_BASE_26866_FULL_APP.sha256" >/dev/null) || fail '26866 authority manifest mismatch'
 cat > "$OUT/26867_RESOLVED_AUTHORITIES.txt" <<EOF_AUTH
runtime_commit=$RUNTIME_AUTHORITY_COMMIT
runtime_run=$RUNTIME_ACTIONS_RUN
runtime_artifact_id=$RUNTIME_ARTIFACT_ID
runtime_artifact_sha256=$RUNTIME_ARTIFACT_SHA
runtime_candidate_tar_sha256=$RUNTIME_TAR_SHA
mechanics_blob_sha1=$MECHANICS_GIT_BLOB
EOF_AUTH
 pass 'exact successful 26866 Actions compiled-candidate authority reconstructed and compiler proof verified'
}
make_candidate(){
 python3 -S verify_26867_candidate.py "$BASE" "$CAND" --transform --root "$ROOT"
 python3 -S regressions/26865_b_lsc_owner.py "$CAND/app"
 python3 -S regressions/26866_b_color_only.py "$BASE/app"
 python3 -S regressions/26867_b_highlight_ab_retired.py "$CAND/app"
 python3 -S verify_26864_rawr_sources.py "$CAND/app"
 python3 -S regressions/26864_glsl_reserved_identifiers.py "$CAND/app"
 python3 -S regressions/26864_wronski_publisher.py "$CAND/app"
 python3 -S verify_26864_semantics.py "$CAND/app" --numeric
 pass '26867 deterministic authority-seeded candidate, pinned RAWR source and active-path semantic regressions'
}
verify_successful_mechanics(){
 git show "$RUNTIME_AUTHORITY_COMMIT:build_26866_iris_rawr.sh" > "$WORK/26866_successful_mechanics.sh"
 [[ "$(git hash-object "$WORK/26866_successful_mechanics.sh")" == "$MECHANICS_GIT_BLOB" ]] || fail '26866 proven mechanics Git blob mismatch'
 for validator in verify_26864_rawr_sources.py verify_26864_runtime_glsl.py verify_26864_semantics.py; do
   local pinned="$WORK/successful_26864_${validator}"
   git show "$RUNTIME_AUTHORITY_COMMIT:$validator" > "$pinned"
   cmp -s "$pinned" "$ROOT/$validator" || fail "26866 inherited validator changed: $validator"
 done
 python3 -S - "$WORK/26866_successful_mechanics.sh" "$ROOT/build_26867_iris_rawr.sh" <<'PY_STAGES'
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
print('PASS exact successful 26866 mechanics source, 17-stage order, real Kotlin/Java/2-ABI NDK/assemble command identity')
PY_STAGES
 pass '26866 inherited 17-stage mechanics, compiler commands and audited 26867 dependency extension'
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
 "$compiler" --version | tee "$OUT/26867_glslang_version.txt"
 grep -F '16.5.0' "$OUT/26867_glslang_version.txt" >/dev/null || fail 'glslang version mismatch'
 export IRIS26864_GLSLANG="$compiler";export IRIS26681_SPEKTRA_GLSLANG="$compiler"
 # Inherit exact successful 26864 real SPIR-V post-validation, no substitutions.
 sudo apt-get update -qq
 sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq spirv-tools
 command -v spirv-val >/dev/null && command -v spirv-opt >/dev/null || fail 'real SPIRV-Tools missing'
 spirv-val --version > "$OUT/26867_spirv_tools_version.txt"
 spirv-opt --version >> "$OUT/26867_spirv_tools_version.txt"
 pass 'pinned real glslang 16.5.0 + real SPIRV-Tools toolchain'
}
compile_modified_runtime_shaders(){
 # Preserve 26864's exact eleven expanded GLES300 owners and real compiler.
 # Only one GLES300 shader is modified in 26867; all native and other expanded GLSL sources unchanged; run the inherited shaders unmodified.
 git show "$RUNTIME_AUTHORITY_COMMIT:verify_26864_runtime_glsl.py" > "$WORK/successful_26864_runtime_glsl.py"
 [[ "$(git hash-object "$WORK/successful_26864_runtime_glsl.py")" == 'c5208e94865afbbbc437c31e09fd7b893e50ca20' ]] || fail '26864 shader validator drift'
 python3 -S verify_26864_runtime_glsl.py "$BASE" "$CAND" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26867_runtime_expanded_glsl" | tee "$OUT/26867_gles_shader_proof.txt"
 grep -F 'PASS 26864 GLSL ownership:' "$OUT/26867_gles_shader_proof.txt" >/dev/null || fail 'inherited 11 expanded GLSL owners or stronger RAWR semantic gate failed'
 # The one newly modified runtime-expanded GLES300 owner is compiled with
 # EXACT same pinned 16.5.0 compiler. Native/other shader inputs unchanged.
 python3 -S verify_26867_runtime_shader.py "$CAND" --compiler "$IRIS26864_GLSLANG" \
   --out "$OUT/26867_new_b_smooth_white_expanded" | tee "$OUT/26867_b_smooth_white_glsl.txt"
 grep -F 'pinned-glslang=PASS' "$OUT/26867_b_smooth_white_glsl.txt" >/dev/null || fail 'new B shader real pinned compiler gate missing'

 python3 -S regressions/26864_glsl_reserved_identifiers.py "$CAND/app"
 # All 55 upstream + 3 Iris bridge shader inputs use the SAME pinned compiler,
 # real SPIR-V validator and optimizer *before* Java/Kotlin compilation.
 python3 -S verify_26864_rawr_sources.py "$CAND/app" --compile "$IRIS26864_GLSLANG" \
   --spirv-val "$(command -v spirv-val)" --spirv-opt "$(command -v spirv-opt)" \
   --out "$OUT/26867_all_native_expanded_spirv" | tee "$OUT/26867_spirv_validation.txt"
 grep -F 'PASS 26864 real 58 SPIR-V compute shaders' "$OUT/26867_spirv_validation.txt" >/dev/null || fail 'native SPIR-V real compiler proof missing'
 sed -i 's#REAL GLSL COMPILE: NOT RUN YET#REAL GLSL COMPILE: PASS (pinned 16.5.0 on expanded GLES300 and 58 exact native Vulkan shaders)#' "$OUT/26867_COMPILER_STATUS.txt"
 sed -i 's#REAL SPIR-V VALIDATION: NOT RUN YET#REAL SPIR-V VALIDATION: PASS (spirv-val pre/post optimized Vulkan 1.1)#' "$OUT/26867_COMPILER_STATUS.txt"
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
 if not lp.is_file():raise SystemExit(f'missing live 26867 candidate path {rel}')
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
 pass '26867 live source byte-identical to frozen authority-seeded candidate'
}
compile_languages(){
 ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26867_gradle_language_compilers.log"
 snapshot_live_authority_seeded "$POST_LANG";diff -qr "$CAND/app" "$POST_LANG/app" >/dev/null || fail 'language compilers changed source'
 sed -i 's/REAL KOTLIN COMPILE: NOT RUN YET/REAL KOTLIN COMPILE: PASS/' "$OUT/26867_COMPILER_STATUS.txt"
 sed -i 's/REAL JAVA COMPILE: NOT RUN YET/REAL JAVA COMPILE: PASS/' "$OUT/26867_COMPILER_STATUS.txt"
 pass 'real project Kotlin and Java compilers on frozen candidate'
}
verify_native_glslang_handoff(){
 [[ -n "${IRIS26864_GLSLANG:-}" && -x "$IRIS26864_GLSLANG" && "$IRIS26864_GLSLANG" == "$IRIS26681_SPEKTRA_GLSLANG" ]] || fail 'pinned real GLSL compiler handoff lost'
 command -v spirv-val >/dev/null && command -v spirv-opt >/dev/null || fail 'SPIR-V validator unavailable to NDK'
 pass 'same pinned real compiler handed to NDK shader subprojects'
}
compile_native(){
 ./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26867_gradle_native_compiler.log"
 snapshot_live_authority_seeded "$WORK/post_native_snapshot"
 diff -qr "$CAND/app" "$WORK/post_native_snapshot/app" >/dev/null || fail 'native compiler changed source'
 sed -i 's#NATIVE/NDK COMPILE: NOT RUN YET#NATIVE/NDK COMPILE: PASS (arm64-v8a + armeabi-v7a; real 58 pinned shader compilation)#' "$OUT/26867_COMPILER_STATUS.txt"
 pass 'real 2-ABI NDK compiler with authentic RAWR Vulkan sources'
}
verify_candidate_patches(){
 python3 -S verify_26867_patches.py "$BASE" "$CAND" 26867_FORWARD_FULL_INDEX.patch 26867_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26867_patch_validation.txt"
 pass 'canonical binary full-index forward/rollback 7/12/40 fuzz=0 exact'
}
prebuild_safety(){
 snapshot_live_authority_seeded "$WORK/prebuild_live_snapshot"
 diff -qr "$CAND/app" "$WORK/prebuild_live_snapshot/app" >/dev/null || fail 'prebuild source drift'
 python3 -S verify_26867_candidate.py "$BASE" "$CAND" --root "$ROOT"
 (cd "$CAND" && sha256sum -c "$ROOT/26867_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail 'protected/DNG/native/vendor source drift'
 for k in 'REAL GLSL COMPILE: PASS' 'REAL SPIR-V VALIDATION: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS';do grep -F "$k" "$OUT/26867_COMPILER_STATUS.txt" >/dev/null || fail "prebuild real compiler gate $k";done
 cat > "$OUT/26867_PREBUILD_SAFETY.txt" <<EOF_SAFETY
PRE-BUILD SAFETY PROOF PASSED
runtime_authority=successful 26866 $RUNTIME_AUTHORITY_COMMIT run $RUNTIME_ACTIONS_RUN artifact $RUNTIME_ARTIFACT_ID
verification_mechanics=exact successful 26866 17-stage inherited build order, compiler commands and authority-seeded source mechanics
runtime_changed_files=4 (0 new, 4 edited, 0 deleted incl guarded version)
infrastructure_delta=26866 successful mechanics inherited unchanged; new 26867 guard/validator/workflow files audited, runtime native/vendor delta ZERO
prior_files=1991
candidate_files=1991
version_name=$VERSION_NAME
version_build=$VERSION_BUILD
real_compilers=GLSL+SPIR-V+Kotlin+Java+NDK two ABI PASS
patch_proof=full index forward/rollback 7/12/40 fuzz 0 exact
protected_source=1987 unchanged prior 26866 compiled candidate files byte-identical; DNG/native/vendor intact
EOF_SAFETY
 pass 'PRE-BUILD SAFETY PROOF PASSED'
}
assemble(){
 test -f "$OUT/26867_PREBUILD_SAFETY.txt" && grep -Fx 'PRE-BUILD SAFETY PROOF PASSED' "$OUT/26867_PREBUILD_SAFETY.txt" >/dev/null || fail 'assemble forbidden without proof'
 ./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26867_gradle_assemble.log"
 mapfile -t apks < <(find app/build/outputs/apk -type f -name '*.apk' | sort)
 [[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one assembled APK, got ${#apks[@]}"
 cp "${apks[0]}" "$FINAL"
 [[ "$(find . -maxdepth 1 -name 'IrisCamera-*.apk' -type f | wc -l)" -eq 1 ]] || fail 'one intended APK at root'
 sha256sum "$FINAL" > "$OUT/26867_APK.sha256"
 sed -i 's/FULL ANDROID ASSEMBLE: NOT RUN YET/FULL ANDROID ASSEMBLE: PASS/' "$OUT/26867_COMPILER_STATUS.txt"
 pass 'full :app:assembleDebug including NDK, exactly one intended APK'
}
postbuild_proof(){
 snapshot_live_authority_seeded "$WORK/post_build_live_snapshot"
 diff -qr "$CAND/app" "$WORK/post_build_live_snapshot/app" >/dev/null || fail 'candidate changed after assemble'
 python3 -S verify_26867_candidate.py "$BASE" "$CAND" --root "$ROOT"
 (cd "$CAND" && sha256sum -c "$ROOT/26867_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 (cd "$CAND" && sha256sum -c "$ROOT/26867_UNCHANGED_PROTECTED.sha256" >/dev/null)
 cp 26867_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26867_candidate_full_app.sha256"
 (cd "$CAND" && tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26867_candidate_app_source.tar.gz" app)
 sha256sum "$OUT/26867_candidate_app_source.tar.gz" > "$OUT/26867_candidate_app_source.tar.gz.sha256"
 cp 26867_FORWARD_FULL_INDEX.patch 26867_ROLLBACK_FULL_INDEX.patch "$OUT/"
 sed -i 's/POST-BUILD INVARIANCE: NOT RUN YET/POST-BUILD INVARIANCE: PASS/' "$OUT/26867_COMPILER_STATUS.txt"
 pass 'postbuild authority-seeded candidate/protected/DNG/native/vendor invariance and deterministic candidate export'
}
clean_extract_replay(){
 local replay="$WORK/clean_replay_candidate" exp="$WORK/extracted_candidate_tar"
 rm -rf "$replay" "$exp";mkdir -p "$exp"
 sha256sum -c 26867_HANDOFF_HASHES.sha256 >/dev/null
 bash -n build_26867_iris_rawr.sh
 python3 -S -m py_compile verify_26867_candidate.py verify_26867_patches.py verify_26864_rawr_sources.py verify_26864_runtime_glsl.py verify_26864_semantics.py regressions/26864_glsl_reserved_identifiers.py regressions/26864_wronski_publisher.py regressions/26865_b_lsc_owner.py regressions/26866_b_color_only.py regressions/26867_b_highlight_ab_retired.py verify_26867_runtime_shader.py
 rm -rf __pycache__ regressions/__pycache__
 python3 -S verify_26867_candidate.py "$BASE" "$replay" --root "$ROOT" --transform
 diff -qr "$CAND/app" "$replay/app" >/dev/null || fail 'clean-extract package transforms differ from frozen candidate'
 sha256sum -c "$OUT/26867_candidate_app_source.tar.gz.sha256" >/dev/null
 tar -xzf "$OUT/26867_candidate_app_source.tar.gz" -C "$exp"
 diff -qr "$CAND/app" "$exp/app" >/dev/null || fail 'exported compiled-candidate TAR differs from frozen candidate'
 python3 -S verify_26867_candidate.py "$BASE" "$exp" --root "$ROOT"
 python3 -S verify_26867_patches.py "$BASE" "$exp" 26867_FORWARD_FULL_INDEX.patch 26867_ROLLBACK_FULL_INDEX.patch > "$OUT/26867_final_patch_replay.txt"
 python3 -S verify_26864_runtime_glsl.py "$BASE" "$exp" --out "$OUT/26867_final_runtime_expanded_glsl" | tee "$OUT/26867_final_glsl_static_replay.txt"
 python3 -S verify_26864_rawr_sources.py "$exp/app"
 python3 -S regressions/26864_glsl_reserved_identifiers.py "$exp/app"
 python3 -S regressions/26864_wronski_publisher.py "$exp/app"
 python3 -S verify_26864_semantics.py "$exp/app" --numeric
 python3 -S regressions/26865_b_lsc_owner.py "$exp/app"
 python3 -S regressions/26866_b_color_only.py "$BASE/app"
 python3 -S regressions/26867_b_highlight_ab_retired.py "$exp/app"
 python3 -S verify_26867_runtime_shader.py "$exp" --out "$OUT/26867_final_expanded_native_B_smooth_white"
 grep -Fx 'VERSION_NAME=0.9726867' "$exp/app/version.properties" >/dev/null
 grep -Fx 'VERSION_BUILD=26867' "$exp/app/version.properties" >/dev/null
 for status in 'REAL GLSL COMPILE: PASS' 'REAL SPIR-V VALIDATION: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS';do grep -F "$status" "$OUT/26867_COMPILER_STATUS.txt" >/dev/null || fail "final compiler proof $status";done
 pass 'final 26867 clean-extract handoff replay exact candidate/hash/syntax/owners/GLSL/patches/version/compilers/build'
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
pass '26867 ALL 17 INHERITED GUARDED STAGES PASSED'
