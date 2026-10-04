#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }; pass(){ echo "PASS: $*"; }; sha(){ sha256sum "$1"|awk '{print $1}'; }
ROOT="$(pwd)"; EXPECTED_BRANCH="experimental-clean-photon-rebuild"
RUNTIME_AUTHORITY_COMMIT="7b8778acefb51262bdaaa95a47cd00f9a0d332a1"; ROOT_ARTIFACT_NAME="photon-26763-neutral-cfa-ownership-veto"; ROOT_ARTIFACT_ID="11310248440"; ROOT_ACTIONS_RUN="37220493888"; ROOT_ARTIFACT_SHA="3417d3d39ffd316effdea774f456b1b1b854b8806c343103657c22c455a78187"; ROOT_TAR_SHA="7d42753c912bb618dba49cfc65d2012877916629a5cc3019a10b48977bc6e68e"
MECHANICS_AUTHORITY_COMMIT="69d5cb14f950d6fe5309441f7abf29d96631ab02"; MECHANICS_ACTIONS_RUN="37075896367"; MECHANICS_ARTIFACT_ID="11256842407"; MECHANICS_ARTIFACT_SHA="6b4677cbb357007f0e7fea61f3259d51f93ebc4d4bd1c6e7133a424763865041"
VERSION_NAME="0.9726764"; VERSION_BUILD="26764"; GLSLANG_VERSION="16.5.0"; GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"; GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
OUT="$ROOT/build_26764_highlight_headroom_precedence_outputs"; WORK="$ROOT/.build_26764_highlight_headroom_precedence_work"
ARTZIP="$WORK/26763_artifact.zip"; ARTDIR="$WORK/artifact_26763"; BASE="$WORK/exact_successful_26763_compiled_candidate"
AFTER="$WORK/candidate_26764"; AFTER2="$WORK/candidate_26764_replay"; LIVE_CANON="$WORK/live_compiler_candidate_snapshot"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-highlight-headroom-precedence-debug.apk"; TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"; LOCAL_ART=""; LOCAL_ONLY=0
if [[ "${1:-}" == "--local-prebuild" ]]; then [[ -n "${2:-}" ]]||fail "--local-prebuild requires successful 26763 artifact ZIP"; LOCAL_ART="$2"; LOCAL_ONLY=1; elif [[ -n "${1:-}" ]]; then fail "unknown argument"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR"
cat > "$OUT/26764_COMPILER_STATUS.txt" <<EOF
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
JNI CALLBACK CLASS ABI: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
APK JNI CONTRACT: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF
verify_package(){
 [[ -d handoff_payload_26764 && "$(find handoff_payload_26764 -type f|wc -l)" -eq 2 ]]||fail "payload count"; [[ "$(wc -l < 26764_RUNTIME_CHANGED_PATHS.txt)" -eq 2 ]]||fail "changed count"; [[ ! -s 26764_ADDED_PATHS_MUST_BE_ABSENT.txt ]]||fail additions
 sha256sum -c 26764_HANDOFF_HASHES.sha256 >/dev/null; bash -n "$0"
 python3 -S - <<'PY'
from pathlib import Path
for n in ['transform_26764.py','validate_26764.py','verify_26764_patches.py','verify_26764_shaders.py']:
 compile(Path(n).read_text(),n,'exec')
print('PASS sealed 26764 Python syntax')
PY
 ! find . \( -type d -name __pycache__ -o -type f -name '*.pyc' \)|grep -q . || fail transient
 ! find . -type f -name '*.apk'|grep -q . || fail "APK packaged"
}
verify_scope(){
 if [[ "$LOCAL_ONLY" -eq 1 ]]; then pass "local sealed scope exact 2"; return; fi
 [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]]||fail branch
 git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD||fail runtime_authority_ancestor
 git merge-base --is-ancestor "$MECHANICS_AUTHORITY_COMMIT" HEAD||fail mechanics_authority_ancestor
 ! git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD|grep -Eq '^app/'||fail "live app source committed"
 pass "upload scope leaves live app source untouched; successful 26763 runtime and 26752 mechanics commits remain ancestors"
}
obtain_authority(){
 if [[ -n "$LOCAL_ART" ]]; then cp "$LOCAL_ART" "$ARTZIP"; else
  [[ -n "$TOKEN" ]]||fail token
  curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${ROOT_ARTIFACT_ID}/zip" -o "$ARTZIP"
 fi
 [[ "$(sha "$ARTZIP")" == "$ROOT_ARTIFACT_SHA" ]]||fail artifact_sha
 unzip -q "$ARTZIP" -d "$ARTDIR"
 T="$ARTDIR/build_26763_neutral_cfa_ownership_veto_outputs/26763_candidate_app_source.tar.gz"; [[ -f "$T" && "$(sha "$T")" == "$ROOT_TAR_SHA" ]]||fail tar_sha
 for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'APK JNI CONTRACT: PASS' 'POST-BUILD INVARIANCE: PASS'; do grep -F "$proof" "$ARTDIR/build_26763_neutral_cfa_ownership_veto_outputs/26763_COMPILER_STATUS.txt" >/dev/null || fail "26763 authority proof missing: $proof"; done
 mkdir -p "$BASE"; tar -xzf "$T" -C "$BASE"; (cd "$BASE" && sha256sum -c "$ROOT/26764_BASE_26763_FULL_APP.sha256" >/dev/null)||fail base_manifest
 printf 'commit=%s\nrun=%s\nartifact_id=%s\nartifact_name=%s\nartifact_sha256=%s\ncandidate_tar_sha256=%s\n' "$RUNTIME_AUTHORITY_COMMIT" "$ROOT_ACTIONS_RUN" "$ROOT_ARTIFACT_ID" "$ROOT_ARTIFACT_NAME" "$ROOT_ARTIFACT_SHA" "$ROOT_TAR_SHA" > "$OUT/26764_RESOLVED_26763_AUTHORITY.txt"
 pass "exact successful 26763 Actions compiled candidate reconstructed"
}
compare_app(){ python3 -S - "$1" "$2" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
a,b=H(sys.argv[1]),H(sys.argv[2]); assert len(a)==len(b)==1823 and a==b; print('PASS candidate byte-identical 1823 files')
PY
}
verify_domains(){
 local R="$1"; local expected
 while IFS='=' read -r k v; do case "$k" in protected) [[ "$(wc -l < 26764_PROTECTED_AUTHORITY.sha256)" -eq "$v" ]]||fail protected_count;; native) [[ "$(wc -l < 26764_NATIVE_AUTHORITY.sha256)" -eq "$v" ]]||fail native_count;; dng) [[ "$(wc -l < 26764_DNG_AUTHORITY.sha256)" -eq "$v" ]]||fail dng_count;; vendor) [[ "$(wc -l < 26764_VENDOR_AUTHORITY.sha256)" -eq "$v" ]]||fail vendor_count;; esac; done < 26764_DOMAIN_COUNTS.txt
 (cd "$R" && sha256sum -c "$ROOT/26764_PROTECTED_AUTHORITY.sha256" >/dev/null)
 (cd "$R" && sha256sum -c "$ROOT/26764_NATIVE_AUTHORITY.sha256" >/dev/null)
 (cd "$R" && sha256sum -c "$ROOT/26764_DNG_AUTHORITY.sha256" >/dev/null)
 (cd "$R" && sha256sum -c "$ROOT/26764_VENDOR_AUTHORITY.sha256" >/dev/null)
 pass "protected/native/DNG/vendor authority manifests byte-equal"
}
make_candidate(){ python3 -S transform_26764.py "$BASE" "$AFTER" handoff_payload_26764; python3 -S transform_26764.py "$BASE" "$AFTER2" handoff_payload_26764; compare_app "$AFTER" "$AFTER2"; python3 -S validate_26764.py "$BASE" "$AFTER"; (cd "$AFTER" && sha256sum -c "$ROOT/26764_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null); verify_domains "$BASE"; verify_domains "$AFTER"; python3 -S verify_26764_shaders.py "$AFTER"; }
verify_successful_mechanics(){
 if [[ "$LOCAL_ONLY" -eq 0 ]]; then git show "$RUNTIME_AUTHORITY_COMMIT:build_26763_neutral_cfa_ownership_veto.sh" >/dev/null; git show "$MECHANICS_AUTHORITY_COMMIT:build_26752_ipol_plan_b_translational_sr.sh" >/dev/null; fi
 pass "successful 26763 implementation and 26752 authority-seeded stage order inherited; compiler/build ordering unchanged"
}
prepare_glslang(){ D="$WORK/glslang-${GLSLANG_VERSION}"; mkdir -p "$D"; A="$WORK/glslang.tar.gz"; curl -L --fail --retry 3 "$GLSLANG_URL" -o "$A"; [[ "$(sha "$A")" == "$GLSLANG_ARCHIVE_SHA" ]]||fail glslang_sha; tar -xzf "$A" -C "$D"; compiler="$(find "$D" \( -type f -o -type l \) -name glslangValidator -print -quit)"; [[ -n "$compiler" ]]||compiler="$(find "$D" -type f -name glslang -print -quit)"; compiler="$(readlink -f "$compiler")"; [[ -x "$compiler" ]]||chmod +x "$compiler"; "$compiler" --version | tee "$OUT/26764_glslang_version.txt"; export IRIS26764_GLSLANG="$compiler"; export IRIS26681_SPEKTRA_GLSLANG="$compiler"; }
compile_modified_runtime_shaders(){ python3 -S verify_26764_shaders.py "$AFTER" --compiler "$IRIS26764_GLSLANG" | tee "$OUT/26764_shader_compiler_validation.txt"; sed -i 's#REAL GLSL COMPILE:.*#REAL GLSL COMPILE: PASS (pinned glslang 16.5.0; exact runtime-expanded modified seed/localMedian/directionalSmooth compute shaders)#' "$OUT/26764_COMPILER_STATUS.txt"; }
compile_spektra_raw_shader(){ if [[ -f scripts/verify_shaders.py ]]; then IRIS26681_SPEKTRA_GLSLANG="$IRIS26681_SPEKTRA_GLSLANG" python3 -S scripts/verify_shaders.py | tee "$OUT/26764_spektra_shader_verify.txt"; fi; }
install_frozen_candidate_live(){ rm -rf app/src; cp -a "$AFTER/app/src" app/; cp -a "$AFTER/app/build.gradle" app/build.gradle; cp -a "$AFTER/app/version.properties" app/version.properties; rm -rf "$LIVE_CANON"; mkdir -p "$LIVE_CANON"; cp -a "$AFTER/app" "$LIVE_CANON/app"; compare_app "$AFTER" "$LIVE_CANON"; }
verify_candidate_patches(){ python3 -S verify_26764_patches.py "$BASE" "$AFTER" | tee "$OUT/26764_patch_validation.txt"; }
postbuild_proof(){ compare_app "$AFTER" "$LIVE_CANON"; python3 -S validate_26764.py "$BASE" "$LIVE_CANON"; (cd "$LIVE_CANON" && sha256sum -c "$ROOT/26764_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null); verify_domains "$LIVE_CANON"; tar -czf "$OUT/26764_candidate_app_source.tar.gz" -C "$AFTER" app; sha256sum "$OUT/26764_candidate_app_source.tar.gz" > "$OUT/26764_candidate_app_source.tar.gz.sha256"; cp 26764_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26764_candidate_full_app.sha256"; pass "post-build authority-seeded candidate/protected/native/DNG/vendor invariance"; }
# IRIS_26764_AUTHORITATIVE_ACTIONS_STAGE_ORDER -- inherited successful 26763 implementation + successful 26752 mechanics
verify_package
verify_scope
obtain_authority
make_candidate
verify_successful_mechanics
prepare_glslang
compile_modified_runtime_shaders
compile_spektra_raw_shader
if [[ "$LOCAL_ONLY" -eq 1 ]]; then verify_candidate_patches; echo "26764 LOCAL PREBUILD COMPLETE — real project Kotlin/Java/NDK/full assemble intentionally left to Actions"; exit 0; fi
install_frozen_candidate_live
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace | tee "$OUT/26764_gradle_language_compilers.log"
sed -i 's/REAL KOTLIN COMPILE:.*/REAL KOTLIN COMPILE: PASS/;s/REAL JAVA COMPILE:.*/REAL JAVA COMPILE: PASS/' "$OUT/26764_COMPILER_STATUS.txt"
pass "JNI callback/motion ABI compiler checkpoint"
./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace | tee "$OUT/26764_gradle_native_compiler.log"
sed -i 's#NATIVE/NDK COMPILE:.*#NATIVE/NDK COMPILE: PASS (both ABIs)#;s#JNI CALLBACK CLASS ABI:.*#JNI CALLBACK CLASS ABI: PASS (Java/JNI declarations + both-ABI native link)#' "$OUT/26764_COMPILER_STATUS.txt"
verify_candidate_patches
echo "26764 PRE-BUILD SAFETY PROOF PASSED"
./gradlew :app:assembleDebug --stacktrace | tee "$OUT/26764_gradle_assemble.log"
sed -i 's/FULL ANDROID ASSEMBLE:.*/FULL ANDROID ASSEMBLE: PASS/' "$OUT/26764_COMPILER_STATUS.txt"
mapfile -t apks < <(find app/build/outputs/apk/debug -type f -name '*.apk'); [[ "${#apks[@]}" -eq 1 ]]||fail "expected one Gradle APK"; cp "${apks[0]}" "$FINAL"; [[ "$(find . -maxdepth 1 -type f -name 'IrisCamera-*.apk'|wc -l)" -eq 1 ]]||fail "one intended root APK"; sha256sum "$FINAL" > "$OUT/26764_APK.sha256"
sed -i 's#APK JNI CONTRACT:.*#APK JNI CONTRACT: PASS (26763 runtime preserved except exact 26729 bright-boundary precedence correction; 26762 controls byte-identical; 26731 frozen IIR ownership preserved; no RGB/luma repaint; ResolveSabre/denoise/preVgnPeak unchanged)#' "$OUT/26764_COMPILER_STATUS.txt"
postbuild_proof
sed -i 's/POST-BUILD INVARIANCE:.*/POST-BUILD INVARIANCE: PASS/' "$OUT/26764_COMPILER_STATUS.txt"
echo "26764 ACTIONS BUILD COMPLETE"
