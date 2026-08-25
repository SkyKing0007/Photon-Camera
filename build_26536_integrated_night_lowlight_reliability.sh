#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
manifest_all(){ local r="$1" o="$2"; (cd "$r" && find app/src/main app/version.properties app/build.gradle -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum) > "$o"; }
manifest_audited_live(){ local r="$1" o="$2"; (cd "$r" && {
  find app/src/main -type f ! -path 'app/src/main/cpp/third_party_26507/*' ! -path 'app/src/main/cpp/deps/*' -print;
  [[ -f app/src/main/cpp/deps/.gitignore ]] && echo app/src/main/cpp/deps/.gitignore;
  echo app/version.properties; echo app/build.gradle;
} | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done) > "$o"; }

ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
BASE_26535_HANDOFF_HEAD="7a2982a42ed0656b883858f5a025f01d7be30f77"
BASE_ARTIFACT="photon-26535-shared-spatial-rgb-support-guard"
BASE_TAR_REL="build_26535_shared_spatial_rgb_support_outputs/26535_candidate_app_source.tar.gz"
BASE_MANIFEST_REL="build_26535_shared_spatial_rgb_support_outputs/26535_candidate_source.sha256"
EXPECTED_BASE_TAR_SHA="33484a274de4fe6bce35f18110915e501d41c13b5ab88e3f0eb08362155d4756"
EXPECTED_BASE_MANIFEST_SHA="f541c384335ae5faac88466e1fc6676ea270f84f57201de173e894895f8fe7ee"
EXPECTED_BASE_FILES=964
EXPECTED_CANDIDATE_FILES=964
VERSION_NAME="0.9726536"; VERSION_BUILD="26536"
BJZHOU_VENDOR_HEAD="09c76e57e8f01a5a8fc536ab41fc80ba642d4042"
REPO="${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
[[ -n "$TOKEN" ]] || fail "GitHub token unavailable for exact successful 26535 artifact recovery"

APPLY="$ROOT/apply_26536_integrated_night_lowlight_reliability.py"
VALIDATE="$ROOT/validate_26536_integrated_night_lowlight_reliability.py"
SYNTAX="$ROOT/preflight_26536_changed_syntax.py"
FALSE_COLOR_SHADER="$ROOT/preflight_26536_false_color_shader.py"
HANDOFF="$ROOT/26536_HANDOFF_HASHES.sha256"
BASE_MANIFEST_PIN="$ROOT/26536_BASE_26535_CANDIDATE_SOURCE.sha256"
BASE_MANIFEST_PIN_SHA="$ROOT/26536_BASE_26535_CANDIDATE_SOURCE_FILE.sha256"
BASE_HEAD_FILE="$ROOT/26536_BASE_26535_HANDOFF_HEAD.txt"
PROTECTED="$ROOT/26536_PROTECTED_26535_RUNTIME_ANCHORS.sha256"
EXPECTED_PATCH="$ROOT/26536_RUNTIME_DELTA_FROM_26535.patch"
EXPECTED_PATCH_SHA="$ROOT/26536_RUNTIME_DELTA_FROM_26535.patch.sha256"
EXPECTED_ROLLBACK="$ROOT/26536_RUNTIME_ROLLBACK_TO_26535.patch"
EXPECTED_ROLLBACK_SHA="$ROOT/26536_RUNTIME_ROLLBACK_TO_26535.patch.sha256"

# Exact inherited safety checks from the successful 26535 lineage.
V16_PROVENANCE_PREFLIGHT="$ROOT/preflight_26533_v16_provenance_shader.py"
SHADER_PREFLIGHT="$ROOT/preflight_26532_iris_shaders.py"
NATIVE_JPEG_PREFLIGHT="$ROOT/preflight_26532_native_jpeg_syntax.py"
JAVA_XML_PREFLIGHT="$ROOT/preflight_26532_java_xml_syntax.py"
EMBEDDED_PREFLIGHT="$ROOT/preflight_26529_iris_embedded_shaders_v3.py"
INHERITED_SHADER_PREFLIGHT="$ROOT/preflight_26526_inherited_shaders.py"
KOTLIN_API_PREFLIGHT="$ROOT/preflight_26531_iris_kotlin_api_contracts.py"
NATIVE_DNG_PREFLIGHT="$ROOT/preflight_26527_native_syntax.py"
DNG_TEST="$ROOT/test_26527_dng_subifd.py"
BJZHOU_MANIFEST="$ROOT/26507_BJZHOU_NATIVE_DEPENDENCIES.sha256"
BJZHOU_COMMIT_FILE="$ROOT/26507_BJZHOU_DEPENDENCY_COMMIT.txt"

OUT="$ROOT/build_26536_integrated_night_lowlight_reliability_outputs"
WORK="$ROOT/.build_26536_integrated_night_lowlight_reliability_work"
ART="$WORK/26535_artifact"
BASE="$WORK/exact_successful_26535"
AFTER="$WORK/candidate_26536"
PATCHREPO="$WORK/patchrepo"
FORWARDCHECK="$WORK/forwardcheck"
ROLLBACKCHECK="$WORK/rollbackcheck"
BJ="$WORK/bjzhou_vendor"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-integrated-night-lowlight-reliability-debug.apk"
SOURCE_TAR_OUT="$OUT/26536_candidate_app_source.tar.gz"
SOURCE_MANIFEST_OUT="$OUT/26536_candidate_source.sha256"
RUNTIME_FILES=(
  app/src/main/assets/shaders/motionv2/highlight_chroma_reliability.glsl
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2HighlightChromaReliability.java
  app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java
  app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightNeuralEnhancer.java
  app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt
)

rm -rf "$OUT" "$WORK" "$FINAL"; mkdir -p "$OUT" "$WORK"

echo "=== 26536 GATE 0: exact branch/base-head/handoff integrity ==="
[[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch: $(git branch --show-current)"
[[ "$(cat "$BASE_HEAD_FILE" | tr -d '\r\n')" == "$BASE_26535_HANDOFF_HEAD" ]] || fail "26535 base head pin drift"
git merge-base --is-ancestor "$BASE_26535_HANDOFF_HEAD" HEAD || fail "current handoff is not descended from successful 26535 handoff"
sha256sum -c "$HANDOFF"
sha256sum -c "$BASE_MANIFEST_PIN_SHA"
sha256sum -c "$EXPECTED_PATCH_SHA"
sha256sum -c "$EXPECTED_ROLLBACK_SHA"
for f in "$APPLY" "$VALIDATE" "$SYNTAX" "$FALSE_COLOR_SHADER" "$V16_PROVENANCE_PREFLIGHT" "$SHADER_PREFLIGHT" "$NATIVE_JPEG_PREFLIGHT" "$JAVA_XML_PREFLIGHT" "$EMBEDDED_PREFLIGHT" "$INHERITED_SHADER_PREFLIGHT" "$KOTLIN_API_PREFLIGHT" "$NATIVE_DNG_PREFLIGHT" "$DNG_TEST" "$BJZHOU_MANIFEST" "$BJZHOU_COMMIT_FILE"; do [[ -f "$f" ]] || fail "required safety file missing: $f"; done
[[ "$(cat "$BJZHOU_COMMIT_FILE" | tr -d '\r\n')" == "$BJZHOU_VENDOR_HEAD" ]] || fail "bjzhou native dependency pin drift"
FORBIDDEN_RE="$(printf '%s' 'git p' 'ush|git sw' 'itch dev|git check' 'out dev')"
! grep -E "$FORBIDDEN_RE" "$0" >/dev/null || fail "forbidden repository command in build script"
pass "experimental-clean-photon-rebuild lineage + exact successful 26535 head + handoff integrity"

echo "=== 26536 GATE 1: recover exact successful 26535 artifact candidate; repo app/src is NOT authority ==="
rm -rf "$ART" "$BASE"; mkdir -p "$ART" "$BASE"
JSON="$WORK/artifacts.json"
curl --fail --location --silent --show-error --retry 5 \
  -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$REPO/actions/artifacts?name=$BASE_ARTIFACT&per_page=100" -o "$JSON"
python3 - "$JSON" "$WORK/artifact_selection.txt" "$BASE_26535_HANDOFF_HEAD" <<'PY'
import json,sys
j=json.load(open(sys.argv[1])); head=sys.argv[3]
xs=[a for a in j.get('artifacts',[]) if not a.get('expired',False) and a.get('workflow_run',{}).get('head_sha')==head]
if not xs: raise SystemExit('no unexpired exact 26535 artifact at pinned head '+head)
xs.sort(key=lambda a:a.get('created_at',''),reverse=True); a=xs[0]
open(sys.argv[2],'w').write(f"artifact_id={a['id']}\ncreated_at={a.get('created_at')}\nhead_sha={a.get('workflow_run',{}).get('head_sha')}\n")
print(a['id'])
PY
ART_ID="$(head -1 "$WORK/artifact_selection.txt" | cut -d= -f2)"
[[ -n "$ART_ID" ]] || fail "failed to select exact successful 26535 artifact"
ZIP="$WORK/26535_artifact.zip"
curl --fail --location --silent --show-error --retry 5 \
  -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$REPO/actions/artifacts/$ART_ID/zip" -o "$ZIP"
unzip -q "$ZIP" -d "$ART"
[[ -f "$ART/$BASE_TAR_REL" && -f "$ART/$BASE_MANIFEST_REL" ]] || fail "selected 26535 artifact lacks candidate proof bundle"
[[ "$(sha "$ART/$BASE_TAR_REL")" == "$EXPECTED_BASE_TAR_SHA" ]] || fail "26535 candidate TAR hash mismatch"
[[ "$(sha "$ART/$BASE_MANIFEST_REL")" == "$EXPECTED_BASE_MANIFEST_SHA" ]] || fail "26535 candidate manifest-file hash mismatch"
cmp -s "$ART/$BASE_MANIFEST_REL" "$BASE_MANIFEST_PIN" || fail "downloaded 26535 source manifest differs from user-tested artifact authority"
tar -xzf "$ART/$BASE_TAR_REL" -C "$BASE"
(cd "$BASE" && sha256sum -c "$BASE_MANIFEST_PIN") > "$OUT/26536_base_26535_manifest_check.txt"
[[ "$(wc -l < "$BASE_MANIFEST_PIN")" -eq "$EXPECTED_BASE_FILES" ]] || fail "base candidate manifest file count drift"
[[ "$(grep '^VERSION_NAME=' "$BASE/app/version.properties" | cut -d= -f2)" == "0.9726535" ]] || fail "base version name is not 0.9726535"
[[ "$(grep '^VERSION_BUILD=' "$BASE/app/version.properties" | cut -d= -f2)" == "26535" ]] || fail "base build is not 26535"
(cd "$BASE" && sha256sum -c "$PROTECTED") > "$OUT/26536_base_protected_anchor_check.txt"
cp "$WORK/artifact_selection.txt" "$OUT/26536_base_artifact_selection.txt"
pass "exact successful 26535 artifact source recovered and verified 964/964"

echo "=== 26536 GATE 2: transform + exact git diff/git diff -R + zero-fuzz forward/rollback ==="
rm -rf "$AFTER"; cp -a "$BASE" "$AFTER"
python3 "$APPLY" "$AFTER"
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" | tee "$OUT/26536_prebuild_validation.txt"
python3 - "$BASE" "$AFTER" "${RUNTIME_FILES[@]}" <<'PY' > "$OUT/26536_actual_changed_files.txt"
from pathlib import Path
import hashlib,sys
b,c=map(Path,sys.argv[1:3]); expected=sorted(sys.argv[3:])
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def m(root):
 d={}
 for f in (root/'app/src/main').rglob('*'):
  if f.is_file(): d[str(f.relative_to(root))]=h(f)
 return d
mb,mc=m(b),m(c); changed=sorted(k for k in set(mb)|set(mc) if mb.get(k)!=mc.get(k))
if changed!=expected: raise SystemExit('26536 changed-file allowlist mismatch: '+repr(changed))
print('\n'.join(changed))
PY
rm -rf "$PATCHREPO"; cp -a "$BASE" "$PATCHREPO"
(
 cd "$PATCHREPO"; git init -q; git config user.email iris26536@example.invalid; git config user.name Iris26536
 git add app/src/main app/version.properties app/build.gradle; git add -f app/src/main/cpp/deps/.gitignore; git commit -qm exact-successful-26535
 # Local-only safety branch; no remote backup branch is created or pushed.
 git branch local-safety-26535-before-26536
 for rel in "${RUNTIME_FILES[@]}"; do cp "$AFTER/$rel" "$rel"; done
 git diff --binary --no-ext-diff -- app/src/main > "$OUT/26536_regenerated_forward.patch"
 git diff --binary --no-ext-diff -R -- app/src/main > "$OUT/26536_regenerated_rollback.patch"
)
cmp -s "$OUT/26536_regenerated_forward.patch" "$EXPECTED_PATCH" || fail "regenerated 26536 forward patch differs"
cmp -s "$OUT/26536_regenerated_rollback.patch" "$EXPECTED_ROLLBACK" || fail "regenerated 26536 rollback patch differs"
cp "$EXPECTED_ROLLBACK" "$OUT/26536_prechange_exact_rollback.patch"
rm -rf "$FORWARDCHECK"; cp -a "$BASE" "$FORWARDCHECK"
patch -d "$FORWARDCHECK" -p1 --batch --forward --fuzz=0 --no-backup-if-mismatch < "$EXPECTED_PATCH" >/dev/null
manifest_all "$AFTER" "$OUT/26536_candidate_preversion.sha256"; manifest_all "$FORWARDCHECK" "$OUT/26536_forwardcheck.sha256"
cmp -s "$OUT/26536_candidate_preversion.sha256" "$OUT/26536_forwardcheck.sha256" || fail "forward patch does not reproduce exact 26536"
rm -rf "$ROLLBACKCHECK"; cp -a "$AFTER" "$ROLLBACKCHECK"
patch -d "$ROLLBACKCHECK" -p1 --batch --forward --fuzz=0 --no-backup-if-mismatch < "$EXPECTED_ROLLBACK" >/dev/null
manifest_all "$BASE" "$OUT/26536_base_for_rollback.sha256"; manifest_all "$ROLLBACKCHECK" "$OUT/26536_rollbackcheck.sha256"
cmp -s "$OUT/26536_base_for_rollback.sha256" "$OUT/26536_rollbackcheck.sha256" || fail "rollback does not restore exact successful 26535"
pass "exact six-file forward/rollback proof; fuzz=0 both directions; local safety branch only"

echo "=== 26536 GATE 3: changed syntax/shader + inherited shader/API/native/DNG preflights ==="
python3 "$SYNTAX" --root "$AFTER" | tee "$OUT/26536_changed_syntax_preflight.txt"
python3 "$FALSE_COLOR_SHADER" --root "$AFTER" --validator glslangValidator | tee "$OUT/26536_false_color_shader_preflight.txt"
python3 "$V16_PROVENANCE_PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26536_v16_provenance_shader_preflight.txt"
python3 "$SHADER_PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26536_shader_preflight.txt"
python3 "$EMBEDDED_PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26536_embedded_shader_preflight.txt"
python3 "$INHERITED_SHADER_PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26536_inherited_shader_preflight.txt"
python3 "$KOTLIN_API_PREFLIGHT" --root "$AFTER" | tee "$OUT/26536_kotlin_api_preflight.txt"
python3 "$NATIVE_DNG_PREFLIGHT" --root "$AFTER" | tee "$OUT/26536_dng_native_preflight.txt"
python3 "$NATIVE_JPEG_PREFLIGHT" --root "$AFTER" | tee "$OUT/26536_native_jpeg_preflight.txt"
python3 "$JAVA_XML_PREFLIGHT" --root "$AFTER" | tee "$OUT/26536_java_xml_preflight.txt"
python3 "$DNG_TEST" --root "$AFTER" | tee "$OUT/26536_dng_subifd_preflight.txt"
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" | tee "$OUT/26536_architecture_contract_preflight.txt"
echo "PRE-BUILD SAFETY PROOF PASSED"
pass "26536 integrated Night/luma/false-color contracts + inherited safety proof"

echo "=== 26536 GATE 4: increment build ID + exact native restore + compile/assemble in SAME guarded block ==="
{
 sed -i "s/^VERSION_NAME=.*/VERSION_NAME=$VERSION_NAME/; s/^VERSION_BUILD=.*/VERSION_BUILD=$VERSION_BUILD/" "$AFTER/app/version.properties"
 [[ "$(grep '^VERSION_NAME=' "$AFTER/app/version.properties" | cut -d= -f2)" == "$VERSION_NAME" ]] || fail "version increment failed"
 [[ "$(grep '^VERSION_BUILD=' "$AFTER/app/version.properties" | cut -d= -f2)" == "$VERSION_BUILD" ]] || fail "build increment failed"
 python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" | tee "$OUT/26536_versioned_validation.txt"
 manifest_audited_live "$AFTER" "$OUT/26536_pre_gradle_audited_runtime.sha256"
 rm -rf "$BJ"; git init -q "$BJ"; git -C "$BJ" remote add origin https://github.com/bjzhou/PhotonCamera.git
 git -C "$BJ" config core.sparseCheckout true; mkdir -p "$BJ/.git/info"
 cat > "$BJ/.git/info/sparse-checkout" <<'SPARSE'
/app/src/main/cpp/libjpeg-turbo/
/app/src/main/cpp/libultrahdr/
SPARSE
 git -C "$BJ" fetch --depth=1 origin "$BJZHOU_VENDOR_HEAD"
 git -C "$BJ" checkout -q --detach FETCH_HEAD
 [[ "$(git -C "$BJ" rev-parse HEAD)" == "$BJZHOU_VENDOR_HEAD" ]] || fail "native vendor checkout drift"
 THIRD="$AFTER/app/src/main/cpp/third_party_26507"; rm -rf "$THIRD"; mkdir -p "$THIRD"
 cp -a "$BJ/app/src/main/cpp/libjpeg-turbo" "$THIRD/libjpeg-turbo"; cp -a "$BJ/app/src/main/cpp/libultrahdr" "$THIRD/libultrahdr"
 [[ -f "$THIRD/libjpeg-turbo/CMakeLists.txt" && -f "$THIRD/libultrahdr/ultrahdr_api.h" && -f "$THIRD/libultrahdr/lib/src/ultrahdr_api.cpp" ]] || fail "pinned native source incomplete"
 [[ ! -e "$THIRD/libultrahdr/CMakeLists.txt" ]] || fail "obsolete libultrahdr CMakeLists returned"
 ( cd "$THIRD" && sha256sum -c "$BJZHOU_MANIFEST" ) > "$OUT/26536_vendor_manifest_prebuild.txt"
 rm -rf "$ROOT/app/src/main"; mkdir -p "$ROOT/app/src"
 cp -a "$AFTER/app/src/main" "$ROOT/app/src/"; cp "$AFTER/app/version.properties" "$ROOT/app/version.properties"; cp "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"
 assert_cpp_deps_exact(){ local root="$1" phase="$2" expected actual; if [[ "$phase" == pre ]]; then expected=$'.gitignore'; else expected=$'.gitignore\narchive.h\narchive_entry.h\ntechnicallyflac.h\ntiny_dng_writer.h'; fi; actual="$(find "$root/app/src/main/cpp/deps" -mindepth 1 -maxdepth 1 -type f -printf '%f\n' | LC_ALL=C sort)"; [[ "$actual" == "$expected" ]] || fail "unexpected cpp/deps ($phase): [$actual]"; }
 assert_cpp_deps_exact "$ROOT" pre
 manifest_audited_live "$ROOT" "$OUT/26536_installed_pre_gradle_audited_runtime.sha256"
 cmp -s "$OUT/26536_pre_gradle_audited_runtime.sha256" "$OUT/26536_installed_pre_gradle_audited_runtime.sha256" || fail "installed candidate drift before Gradle"
 (cd "$ROOT/app/src/main/cpp/third_party_26507" && sha256sum -c "$BJZHOU_MANIFEST") > "$OUT/26536_installed_vendor_manifest_prebuild.txt"
 chmod +x ./gradlew
 ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace
 pass "real Android Kotlin + Java compile gates passed"
 ./gradlew :app:assembleDebug --stacktrace
 pass "assembleDebug passed"
}

echo "=== 26536 GATE 5: post-build exact source/native/architecture revalidation ==="
assert_cpp_deps_exact "$ROOT" post
manifest_audited_live "$ROOT" "$OUT/26536_post_gradle_audited_runtime.sha256"
cmp -s "$OUT/26536_pre_gradle_audited_runtime.sha256" "$OUT/26536_post_gradle_audited_runtime.sha256" || fail "Gradle mutated audited source"
(cd "$ROOT/app/src/main/cpp/third_party_26507" && sha256sum -c "$BJZHOU_MANIFEST") > "$OUT/26536_postbuild_native_dependency_manifest_check.txt"
python3 "$VALIDATE" --base "$BASE" --candidate "$ROOT" | tee "$OUT/26536_postbuild_architecture_validation.txt"
python3 "$JAVA_XML_PREFLIGHT" --root "$ROOT" | tee "$OUT/26536_postbuild_java_xml_preflight.txt"
python3 "$NATIVE_JPEG_PREFLIGHT" --root "$ROOT" | tee "$OUT/26536_postbuild_native_jpeg_preflight.txt"
python3 "$FALSE_COLOR_SHADER" --root "$ROOT" --validator glslangValidator | tee "$OUT/26536_postbuild_false_color_shader.txt"
pass "post-build source/native/26536 contracts remained exact"

echo "=== 26536 GATE 6: exactly one APK + deterministic next candidate ==="
mapfile -t BUILT_APKS < <(find "$ROOT/app/build/outputs/apk" -type f -name '*.apk' -print 2>/dev/null)
[[ "${#BUILT_APKS[@]}" -eq 1 ]] || fail "expected exactly one Gradle APK, found ${#BUILT_APKS[@]}"
cp "${BUILT_APKS[0]}" "$FINAL"; find "$ROOT/app/build" -type f -name '*.apk' -delete
[[ -f "$FINAL" ]] || fail "final APK missing"
[[ "$(find "$ROOT" -maxdepth 1 -type f -name '*.apk' | wc -l)" -eq 1 ]] || fail "root APK count is not exactly one"
sha256sum "$FINAL" > "$OUT/26536_APK.sha256"
rm -rf "$AFTER/app/src/main/cpp/third_party_26507"
manifest_all "$AFTER" "$SOURCE_MANIFEST_OUT"
[[ "$(wc -l < "$SOURCE_MANIFEST_OUT")" -eq "$EXPECTED_CANDIDATE_FILES" ]] || fail "26536 candidate file count drift"
( cd "$AFTER" && tar --sort=name --mtime='UTC 2026-08-25 00:00:00' --owner=0 --group=0 --numeric-owner -czf "$SOURCE_TAR_OUT" app/src/main app/version.properties app/build.gradle )
sha256sum "$SOURCE_TAR_OUT" > "$OUT/26536_candidate_app_source.tar.gz.sha256"
sha256sum "$SOURCE_MANIFEST_OUT" > "$OUT/26536_candidate_source_manifest_file.sha256"
cat > "$OUT/26536_SCOPE_PROVENANCE.txt" <<SCOPE
BASE_BRANCH=$EXPECTED_BRANCH
BASE_SUCCESSFUL_26535_HANDOFF_HEAD=$BASE_26535_HANDOFF_HEAD
BASE_ARTIFACT=$BASE_ARTIFACT
BASE_SOURCE_TAR_SHA=$EXPECTED_BASE_TAR_SHA
TARGET_VERSION=$VERSION_NAME
TARGET_BUILD=$VERSION_BUILD
RUNTIME_DELTA_FILES=6
MOTION_PRODUCTION=MGC_SPATIAL_RGB_RGBA32F
NIGHT_PRODUCTION=MGC_SPATIAL_RGB_RGBA32F_TO_OPTIONAL_JIN
NIGHT_SECOND_MGC_PASS=false
NIGHT_JIN_NNAPI_CPU_RETRY=true
NIGHT_SAVE_COMPLETED_MGC_BASE_IF_JIN_FAILS=true
PHOTON_NIGHT_FALLBACK=false
ADRC_FALLBACK=false
SINGLE_FRAME_FALLBACK=false
ADAPTIVE_MGC_LUMA=true
NAIVE_FLAT_AREA_CLASSIFIER=false
FALSE_COLOR_NEAR_CLIP_REQUIRED=false
FALSE_COLOR_LOW_RELIABILITY_CONTEXT=true
FALSE_COLOR_HUE_TARGETING=false
EXISTING_VGN_IIR_LOCKED=true
EXISTING_POST_C317_SPATIAL_FIXES_LOCKED=true
DUPLICATE_PRESENTATION_LIMITER=false
PRESENTATION_HEADROOM_OWNER=MotionV2RenderCommonRgbScalar
SHORT_BENTO_REJECTION_UNCHANGED=true
DNG_SR_UHDR_OWNERSHIP_UNCHANGED=true
SCOPE

echo "PASS: 26536 NIGHT JIN RESILIENCE + COMPLETED MGC BASE SAVE"
echo "PASS: 26536 ADAPTIVE TEXTURE-PROTECTIVE MGC LUMA + BROADER RELIABILITY FALSE-COLOR"
echo "PASS: 26536 EXACT SUCCESSFUL-26535 ARTIFACT LINEAGE + 6-FILE DELTA + ONE APK"
