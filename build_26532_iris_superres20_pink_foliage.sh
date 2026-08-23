#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
manifest(){ local r="$1" o="$2"; (cd "$r" && find app/src/main app/version.properties -type f -print0 | sort -z | xargs -0 sha256sum) > "$o"; }

ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
SUCCESSFUL_26531_HEAD="3d0184ea279b2dab166f9837082d57f08c5e7ef4"
BACKUP_BRANCH="backup-26531-before-26532-superres-pink-reset"
BASE_WORKFLOW="build-26531-latest-mgc-spatial-zero-luma-fov.yml"
BASE_ARTIFACT="photon-26531-v1-3-iris-spatial-zero-luma-fov"
BASE_SOURCE_TAR_NAME="26531_candidate_app_source.tar.gz"
BASE_SOURCE_MANIFEST_NAME="26531_candidate_source.sha256"
EXPECTED_BASE_TAR_SHA="9c22f3d3e090607f9266246930d77961948c6b89f0fe708c81b140cfb1349b19"
EXPECTED_BASE_MANIFEST_SHA="87eb558a00ff3b71fd9bad059e502e64b51e94f4bb359f992e34cb39b8201302"
EXPECTED_BASE_FILES=950
EXPECTED_CANDIDATE_FILES=951
BJZHOU_VENDOR_HEAD="09c76e57e8f01a5a8fc536ab41fc80ba642d4042"
BJZHOU_MANIFEST="$ROOT/26507_BJZHOU_NATIVE_DEPENDENCIES.sha256"
BJZHOU_COMMIT_FILE="$ROOT/26507_BJZHOU_DEPENDENCY_COMMIT.txt"
REPO="${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}"
VERSION_NAME="0.9726532"; VERSION_BUILD="26532"

APPLY="$ROOT/apply_26532_iris_superres20_pink_foliage.py"
VALIDATE="$ROOT/validate_26532_iris_superres20_pink_foliage.py"
SHADER_PREFLIGHT="$ROOT/preflight_26532_iris_shaders.py"
NATIVE_JPEG_PREFLIGHT="$ROOT/preflight_26532_native_jpeg_syntax.py"
JAVA_XML_PREFLIGHT="$ROOT/preflight_26532_java_xml_syntax.py"
EMBEDDED_PREFLIGHT="$ROOT/preflight_26529_iris_embedded_shaders_v3.py"
INHERITED_SHADER_PREFLIGHT="$ROOT/preflight_26526_inherited_shaders.py"
KOTLIN_API_PREFLIGHT="$ROOT/preflight_26531_iris_kotlin_api_contracts.py"
NATIVE_DNG_PREFLIGHT="$ROOT/preflight_26527_native_syntax.py"
DNG_TEST="$ROOT/test_26527_dng_subifd.py"
HANDOFF="$ROOT/26532_HANDOFF_HASHES.sha256"
BASE_HEAD_FILE="$ROOT/26532_BASE_SUCCESSFUL_26531_HEAD.txt"
BASE_TAR_SHA_FILE="$ROOT/26532_BASE_SUCCESSFUL_26531_SOURCE_TAR.sha256"
BASE_MANIFEST_SHA_FILE="$ROOT/26532_BASE_SUCCESSFUL_26531_SOURCE_MANIFEST.sha256"
EXPECTED_PATCH="$ROOT/26532_RUNTIME_DELTA_FROM_26531.patch"
EXPECTED_PATCH_SHA="$ROOT/26532_RUNTIME_DELTA_FROM_26531.patch.sha256"
EXPECTED_ROLLBACK="$ROOT/26532_RUNTIME_ROLLBACK_TO_26531.patch"
EXPECTED_ROLLBACK_SHA="$ROOT/26532_RUNTIME_ROLLBACK_TO_26531.patch.sha256"

OUT="$ROOT/build_26532_iris_superres20_pink_foliage_outputs"
WORK="$ROOT/.build_26532_iris_superres20_pink_foliage_work"
ART="$WORK/26531_artifact"
BASE="$WORK/tested26531"
AFTER="$WORK/candidate26532"
ROLL="$WORK/rollbackcheck"
PATCHREPO="$WORK/patchrepo"
BJ="$WORK/bjzhou_vendor"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-superres20-pink-foliage-debug.apk"

rm -rf "$OUT" "$WORK" "$FINAL"
mkdir -p "$OUT" "$ART" "$BASE" "$AFTER"
exec > >(tee "$OUT/26532_build.log") 2>&1

echo "=== 26532 GATE 0: branch + exact 26531 backup + handoff integrity ==="
BRANCH="$(git branch --show-current)"
[[ "$BRANCH" == "$EXPECTED_BRANCH" && "$BRANCH" != "dev" ]] || fail "wrong/protected branch: $BRANCH"
git merge-base --is-ancestor "$SUCCESSFUL_26531_HEAD" HEAD || fail "handoff HEAD is not descended from exact successful 26531"
[[ "$(tr -d '\r\n' < "$BASE_HEAD_FILE")" == "$SUCCESSFUL_26531_HEAD" ]] || fail "26531 base HEAD file drift"
[[ "$(awk '{print $1}' "$BASE_TAR_SHA_FILE")" == "$EXPECTED_BASE_TAR_SHA" ]] || fail "base tar SHA file drift"
[[ "$(awk '{print $1}' "$BASE_MANIFEST_SHA_FILE")" == "$EXPECTED_BASE_MANIFEST_SHA" ]] || fail "base manifest SHA file drift"
for f in "$APPLY" "$VALIDATE" "$SHADER_PREFLIGHT" "$NATIVE_JPEG_PREFLIGHT" "$JAVA_XML_PREFLIGHT" "$HANDOFF" \
         "$BASE_HEAD_FILE" "$BASE_TAR_SHA_FILE" "$BASE_MANIFEST_SHA_FILE" \
         "$EXPECTED_PATCH" "$EXPECTED_PATCH_SHA" "$EXPECTED_ROLLBACK" "$EXPECTED_ROLLBACK_SHA" \
         "$EMBEDDED_PREFLIGHT" "$INHERITED_SHADER_PREFLIGHT" "$KOTLIN_API_PREFLIGHT" \
         "$NATIVE_DNG_PREFLIGHT" "$DNG_TEST" "$BJZHOU_MANIFEST" "$BJZHOU_COMMIT_FILE"; do [[ -f "$f" ]] || fail "missing $(basename "$f")"; done
sha256sum -c "$HANDOFF"
sha256sum -c "$EXPECTED_PATCH_SHA"
sha256sum -c "$EXPECTED_ROLLBACK_SHA"
python3 -m py_compile "$APPLY" "$VALIDATE" "$SHADER_PREFLIGHT" "$NATIVE_JPEG_PREFLIGHT" "$JAVA_XML_PREFLIGHT" \
  "$EMBEDDED_PREFLIGHT" "$INHERITED_SHADER_PREFLIGHT" "$KOTLIN_API_PREFLIGHT" "$NATIVE_DNG_PREFLIGHT" "$DNG_TEST"
bash -n "$0"
command -v gh >/dev/null || fail "GitHub CLI unavailable"
[[ -n "${GH_TOKEN:-}" ]] || fail "GH_TOKEN missing"
command -v glslangValidator >/dev/null || fail "glslangValidator unavailable"
glslangValidator --version | grep -F '16.5.0' >/dev/null || fail "wrong glslangValidator version"
[[ "$(tr -d '\r\n' < "$BJZHOU_COMMIT_FILE")" == "$BJZHOU_VENDOR_HEAD" ]] || fail "native vendor dependency commit drift"

git fetch --no-tags origin "refs/heads/$BACKUP_BRANCH:refs/remotes/origin/$BACKUP_BRANCH"
[[ "$(git rev-parse "refs/remotes/origin/$BACKUP_BRANCH")" == "$SUCCESSFUL_26531_HEAD" ]] || fail "backup branch is not exact 26531"

git diff --name-only "$SUCCESSFUL_26531_HEAD"..HEAD -- app/src/main app/version.properties > "$OUT/26532_committed_runtime_drift_after_26531.txt"
[[ ! -s "$OUT/26532_committed_runtime_drift_after_26531.txt" ]] || fail "committed runtime drift after successful 26531"
git diff --name-only "$SUCCESSFUL_26531_HEAD"..HEAD -- gradlew gradlew.bat gradle build.gradle settings.gradle gradle.properties app/build.gradle app/proguard-rules.pro > "$OUT/26532_protected_build_infrastructure_drift.txt"
[[ ! -s "$OUT/26532_protected_build_infrastructure_drift.txt" ]] || fail "protected build infrastructure drift after successful 26531"
for rel in preflight_26529_iris_embedded_shaders_v3.py preflight_26526_inherited_shaders.py preflight_26531_iris_kotlin_api_contracts.py preflight_26527_native_syntax.py test_26527_dng_subifd.py 26507_BJZHOU_NATIVE_DEPENDENCIES.sha256 26507_BJZHOU_DEPENDENCY_COMMIT.txt; do
  [[ "$(git hash-object "$rel")" == "$(git rev-parse "$SUCCESSFUL_26531_HEAD:$rel")" ]] || fail "inherited preflight drift: $rel"
done
pass "exact 26531 lineage + backup + handoff integrity verified"

echo "=== 26532 GATE 1: recover ACTUAL successful 26531 candidate-source artifact ==="
RUN_JSON="$WORK/26531_runs.json"
gh run list --repo "$REPO" --workflow "$BASE_WORKFLOW" --branch "$EXPECTED_BRANCH" --status success --limit 50 \
  --json databaseId,headSha,conclusion,createdAt > "$RUN_JSON"
RUN_ID="$(python3 - "$RUN_JSON" "$SUCCESSFUL_26531_HEAD" <<'PY'
import json,sys
runs=json.load(open(sys.argv[1])); head=sys.argv[2]
xs=[r for r in runs if r.get('headSha')==head and r.get('conclusion')=='success']
if not xs: raise SystemExit('no successful 26531 workflow at exact HEAD '+head)
xs.sort(key=lambda r:r.get('createdAt',''), reverse=True)
print(xs[0]['databaseId'])
PY
)"
[[ "$RUN_ID" =~ ^[0-9]+$ ]] || fail "invalid 26531 workflow run id"
gh run download "$RUN_ID" --repo "$REPO" --name "$BASE_ARTIFACT" --dir "$ART"
mapfile -t SOURCE_TARS < <(find "$ART" -type f -name "$BASE_SOURCE_TAR_NAME" -print)
mapfile -t SOURCE_MANIFESTS < <(find "$ART" -type f -name "$BASE_SOURCE_MANIFEST_NAME" -print)
[[ "${#SOURCE_TARS[@]}" -eq 1 && "${#SOURCE_MANIFESTS[@]}" -eq 1 ]] || fail "26531 source artifact cardinality mismatch"
SOURCE_TAR="${SOURCE_TARS[0]}"; SOURCE_MANIFEST="${SOURCE_MANIFESTS[0]}"
[[ "$(sha "$SOURCE_TAR")" == "$EXPECTED_BASE_TAR_SHA" ]] || fail "26531 source tar SHA drift"
[[ "$(sha "$SOURCE_MANIFEST")" == "$EXPECTED_BASE_MANIFEST_SHA" ]] || fail "26531 source manifest SHA drift"
[[ "$(wc -l < "$SOURCE_MANIFEST")" -eq "$EXPECTED_BASE_FILES" ]] || fail "26531 source manifest count drift"
tar -xzf "$SOURCE_TAR" -C "$BASE"
( cd "$BASE" && sha256sum -c "$SOURCE_MANIFEST" ) > "$OUT/26531_source_manifest_check.txt"
[[ "$(grep '^VERSION_NAME=' "$BASE/app/version.properties" | cut -d= -f2)" == "0.9726531" ]] || fail "base version name mismatch"
[[ "$(grep '^VERSION_BUILD=' "$BASE/app/version.properties" | cut -d= -f2)" == "26531" ]] || fail "base build mismatch"
python3 "$APPLY" --self-test "$BASE" | tee "$OUT/26532_apply_selftest.txt"
pass "exact successful 26531 candidate recovered; repository app/src is not runtime authority"

echo "=== 26532 GATE 2: apply certified runtime transform + prove forward/rollback ==="
cp -a "$BASE/." "$AFTER/"
python3 "$APPLY" "$AFTER"
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" --patch "$EXPECTED_PATCH" --rollback "$EXPECTED_ROLLBACK" \
  --json-out "$OUT/26532_prebuild_validation.json" | tee "$OUT/26532_prebuild_validator.txt"

# Rebuild the forward patch from a clean mini git repo; new-file intent is required for exact git-diff bytes.
cp -a "$BASE/." "$PATCHREPO/"
(
  cd "$PATCHREPO"
  git init -q; git config user.email iris26532@example.invalid; git config user.name Iris26532
  git add app/src/main app/version.properties; git commit -qm base
  rm -rf app/src/main; cp -a "$AFTER/app/src/main" app/src/
  git add -N app/src/main/java/com/particlesdevs/photoncamera/processing/IrisMotionSuperResDngWriter.java
  git diff --binary --no-ext-diff -- app/src/main > "$OUT/26532_regenerated_forward.patch"
)
cmp -s "$OUT/26532_regenerated_forward.patch" "$EXPECTED_PATCH" || fail "regenerated forward patch is not byte-identical"
sha256sum "$OUT/26532_regenerated_forward.patch" > "$OUT/26532_regenerated_forward.patch.sha256"

cp -a "$AFTER/." "$ROLL/"
patch -d "$ROLL" -p1 --batch --forward --fuzz=0 --no-backup-if-mismatch < "$EXPECTED_ROLLBACK" >/dev/null
manifest "$BASE" "$OUT/26532_base_manifest_for_rollback.sha256"
manifest "$ROLL" "$OUT/26532_rollback_manifest.sha256"
cmp -s "$OUT/26532_base_manifest_for_rollback.sha256" "$OUT/26532_rollback_manifest.sha256" || fail "rollback does not restore exact 26531 runtime"
pass "certified forward patch byte-identical; certified rollback restores exact base"

echo "=== 26532 GATE 3: shader/API/native/DNG preflights ==="
python3 "$SHADER_PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26532_shader_preflight.txt"
python3 "$EMBEDDED_PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26532_26529_embedded_shader_preflight.txt"
python3 "$INHERITED_SHADER_PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26532_inherited_shader_preflight.txt"
python3 "$KOTLIN_API_PREFLIGHT" --root "$AFTER" | tee "$OUT/26532_kotlin_api_preflight.txt"
python3 "$NATIVE_DNG_PREFLIGHT" --root "$AFTER" | tee "$OUT/26532_inherited_dng_native_preflight.txt"
python3 "$NATIVE_JPEG_PREFLIGHT" --root "$AFTER" | tee "$OUT/26532_native_jpeg_preflight.txt"
python3 "$JAVA_XML_PREFLIGHT" --root "$AFTER" | tee "$OUT/26532_java_xml_preflight.txt"
python3 "$DNG_TEST" --root "$AFTER" | tee "$OUT/26532_dng_subifd_preflight.txt"

# Superseded 26531 RGB-only and 26530 2x-cap shader preflights are intentionally not invoked.

echo "PRE-BUILD SAFETY PROOF PASSED"
pass "26532 static ownership + shader + native + DNG safety proof"

echo "=== 26532 GATE 4: freeze candidate, increment version, revalidate ==="
manifest "$AFTER" "$OUT/26532_preversion_candidate.sha256"
sed -i "s/^VERSION_NAME=.*/VERSION_NAME=$VERSION_NAME/; s/^VERSION_BUILD=.*/VERSION_BUILD=$VERSION_BUILD/" "$AFTER/app/version.properties"
[[ "$(grep '^VERSION_NAME=' "$AFTER/app/version.properties" | cut -d= -f2)" == "$VERSION_NAME" ]] || fail "version name increment failed"
[[ "$(grep '^VERSION_BUILD=' "$AFTER/app/version.properties" | cut -d= -f2)" == "$VERSION_BUILD" ]] || fail "build increment failed"
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" --patch "$EXPECTED_PATCH" --rollback "$EXPECTED_ROLLBACK" --versioned \
  --json-out "$OUT/26532_versioned_validation.json" | tee "$OUT/26532_versioned_validator.txt"
manifest "$AFTER" "$OUT/26532_pre_gradle_audited_runtime.sha256"
[[ "$(wc -l < "$OUT/26532_pre_gradle_audited_runtime.sha256")" -eq "$EXPECTED_CANDIDATE_FILES" ]] || fail "26532 candidate source count mismatch"
pass "version increment + pre-Gradle candidate freeze complete"

echo "=== 26532 GATE 4B: restore exact pinned native dependencies inherited from successful 26531 ==="
rm -rf "$BJ"; git init -q "$BJ"
git -C "$BJ" remote add origin https://github.com/bjzhou/PhotonCamera.git
git -C "$BJ" config core.sparseCheckout true
mkdir -p "$BJ/.git/info"
cat > "$BJ/.git/info/sparse-checkout" <<'SPARSE'
/app/src/main/cpp/libjpeg-turbo/
/app/src/main/cpp/libultrahdr/
SPARSE
git -C "$BJ" fetch --depth=1 origin "$BJZHOU_VENDOR_HEAD"
git -C "$BJ" checkout -q --detach FETCH_HEAD
[[ "$(git -C "$BJ" rev-parse HEAD)" == "$BJZHOU_VENDOR_HEAD" ]] || fail "native vendor checkout drift"
THIRD="$AFTER/app/src/main/cpp/third_party_26507"
rm -rf "$THIRD"; mkdir -p "$THIRD"
cp -a "$BJ/app/src/main/cpp/libjpeg-turbo" "$THIRD/libjpeg-turbo"
cp -a "$BJ/app/src/main/cpp/libultrahdr" "$THIRD/libultrahdr"
[[ -f "$THIRD/libjpeg-turbo/CMakeLists.txt" ]] || fail "26507 pinned libjpeg-turbo source missing before Gradle"
[[ -f "$THIRD/libultrahdr/CMakeLists.txt" ]] || fail "26507 pinned libultrahdr source missing before Gradle"
( cd "$THIRD" && sha256sum -c "$BJZHOU_MANIFEST" ) > "$OUT/26532_vendor_manifest_check_prebuild.txt"
pass "exact 26507 native vendor dependencies restored + hash-verified before Gradle"

echo "=== 26532 GATE 5: install exact candidate into disposable Actions workspace + compile ==="
rm -rf "$ROOT/app/src/main"
mkdir -p "$ROOT/app/src"
cp -a "$AFTER/app/src/main" "$ROOT/app/src/"
cp "$AFTER/app/version.properties" "$ROOT/app/version.properties"

assert_cpp_deps_exact(){
  local root="$1" phase="$2" expected actual
  if [[ "$phase" == pre ]]; then expected=$'.gitignore'
  else expected=$'.gitignore\narchive.h\narchive_entry.h\ntechnicallyflac.h\ntiny_dng_writer.h'; fi
  actual="$(find "$root/app/src/main/cpp/deps" -mindepth 1 -maxdepth 1 -type f -printf '%f\n' | LC_ALL=C sort)"
  [[ "$actual" == "$expected" ]] || fail "unexpected app/src/main/cpp/deps contents ($phase): [$actual]"
}
audited_runtime_manifest(){
  local root="$1" out="$2"
  (
    cd "$root"
    {
      find app/src/main -type f ! -path 'app/src/main/cpp/third_party_26507/*' ! -path 'app/src/main/cpp/deps/*' -print
      echo app/src/main/cpp/deps/.gitignore
      echo app/version.properties
    } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done
  ) > "$out"
}
assert_cpp_deps_exact "$ROOT" pre
audited_runtime_manifest "$ROOT" "$OUT/26532_installed_pre_gradle_audited_runtime.sha256"
cmp -s "$OUT/26532_pre_gradle_audited_runtime.sha256" "$OUT/26532_installed_pre_gradle_audited_runtime.sha256" || fail "installed runtime differs before Gradle"
[[ -f "$ROOT/app/src/main/cpp/third_party_26507/libjpeg-turbo/CMakeLists.txt" ]] || fail "pinned libjpeg-turbo missing immediately before Gradle"
[[ -f "$ROOT/app/src/main/cpp/third_party_26507/libultrahdr/CMakeLists.txt" ]] || fail "pinned libultrahdr missing immediately before Gradle"
( cd "$ROOT/app/src/main/cpp/third_party_26507" && sha256sum -c "$BJZHOU_MANIFEST" ) > "$OUT/26532_installed_vendor_manifest_check_prebuild.txt"

./gradlew --no-daemon :app:compileDebugKotlin :app:compileDebugJavaWithJavac
pass "Kotlin + Java compile gates"
./gradlew --no-daemon :app:assembleDebug
pass "assembleDebug"

echo "=== 26532 GATE 6: post-build source + semantic revalidation ==="
assert_cpp_deps_exact "$ROOT" post
audited_runtime_manifest "$ROOT" "$OUT/26532_installed_runtime_after_gradle.sha256"
cmp -s "$OUT/26532_pre_gradle_audited_runtime.sha256" "$OUT/26532_installed_runtime_after_gradle.sha256" || fail "installed audited runtime source drifted during Gradle"
( cd "$ROOT/app/src/main/cpp/third_party_26507" && sha256sum -c "$BJZHOU_MANIFEST" ) > "$OUT/26532_vendor_manifest_check_postbuild.txt"
rm -rf "$AFTER/app/src/main/cpp/third_party_26507"
manifest "$AFTER" "$OUT/26532_post_gradle_candidate.sha256"
cmp -s "$OUT/26532_pre_gradle_audited_runtime.sha256" "$OUT/26532_post_gradle_candidate.sha256" || fail "candidate source mutated during Gradle"
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" --patch "$EXPECTED_PATCH" --rollback "$EXPECTED_ROLLBACK" --versioned \
  --json-out "$OUT/26532_postbuild_validation.json" | tee "$OUT/26532_postbuild_validator.txt"
python3 "$SHADER_PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26532_shader_postbuild.txt"
python3 "$EMBEDDED_PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26532_26529_embedded_shader_postbuild.txt"
python3 "$INHERITED_SHADER_PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26532_inherited_shader_postbuild.txt"
python3 "$KOTLIN_API_PREFLIGHT" --root "$AFTER" | tee "$OUT/26532_kotlin_api_postbuild.txt"
python3 "$NATIVE_DNG_PREFLIGHT" --root "$AFTER" | tee "$OUT/26532_inherited_dng_native_postbuild.txt"
python3 "$NATIVE_JPEG_PREFLIGHT" --root "$AFTER" | tee "$OUT/26532_native_jpeg_postbuild.txt"
python3 "$JAVA_XML_PREFLIGHT" --root "$AFTER" | tee "$OUT/26532_java_xml_postbuild.txt"
python3 "$DNG_TEST" --root "$AFTER" | tee "$OUT/26532_dng_subifd_postbuild.txt"
pass "post-build source and semantic proofs"

echo "=== 26532 GATE 7: one APK + next-candidate archive ==="
mapfile -t APKS < <(find "$ROOT/app/build/outputs/apk" -type f -name '*.apk' -print 2>/dev/null)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one Gradle APK, found ${#APKS[@]}"
mv "${APKS[0]}" "$FINAL"
[[ -s "$FINAL" ]] || fail "final APK missing/empty"
[[ "$(find "$ROOT/app/build/outputs/apk" -type f -name '*.apk' -print 2>/dev/null | wc -l)" -eq 0 ]] || fail "duplicate Gradle APK survived"
sha256sum "$FINAL" | tee "$OUT/26532_APK.sha256"

cp "$OUT/26532_pre_gradle_audited_runtime.sha256" "$OUT/26532_candidate_source.sha256"
tar -czf "$OUT/26532_candidate_app_source.tar.gz" -C "$AFTER" app/src/main app/version.properties
sha256sum "$OUT/26532_candidate_app_source.tar.gz" > "$OUT/26532_candidate_app_source.tar.gz.sha256"
VERIFY="$WORK/verify_next_candidate"; mkdir -p "$VERIFY"; tar -xzf "$OUT/26532_candidate_app_source.tar.gz" -C "$VERIFY"
( cd "$VERIFY" && sha256sum -c "$OUT/26532_candidate_source.sha256" ) > "$OUT/26532_next_candidate_manifest_check.txt"
[[ "$(wc -l < "$OUT/26532_candidate_source.sha256")" -eq "$EXPECTED_CANDIDATE_FILES" ]] || fail "archived candidate count mismatch"

cat > "$OUT/26532_provenance.txt" <<EOF
branch=$EXPECTED_BRANCH
successful_base_head=$SUCCESSFUL_26531_HEAD
backup_branch=$BACKUP_BRANCH
base_artifact=$BASE_ARTIFACT
base_source_tar_sha256=$EXPECTED_BASE_TAR_SHA
base_source_manifest_sha256=$EXPECTED_BASE_MANIFEST_SHA
version_name=$VERSION_NAME
version_build=$VERSION_BUILD
runtime_changed_files=23
candidate_source_files=$EXPECTED_CANDIDATE_FILES
sr_total_limit=20x
super_res_output_scale=2x_linear
normal_dng_path=26531_preserved
sr_dng=streamed_linear_raw_rgb16
sr_jpeg=streamed_highres_luma_detail_native_color_authority
pink_fix=physical_support_continuous_geometry_confidence
foliage_fix=structure_aware_edge_chroma_protection
iso_exposure_policy=unchanged
EOF

# Do not allow any second APK into the uploaded proof bundle.
[[ "$(find "$ROOT" -maxdepth 1 -type f -name '*.apk' -print | wc -l)" -eq 1 ]] || fail "root APK cardinality is not exactly one"
pass "single APK + exact next-candidate source archive"
echo "PASS: 26532 STRICT HANDOFF BUILD COMPLETE"
echo "APK=$FINAL"
