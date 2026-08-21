#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }

ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
SUCCESSFUL_26519_HEAD="9b59a27235747733bacdde68bf6a888ebffefa18"
BACKUP_26519="backup-26519-before-26520-zsl-stacked-dng"
BASE_WORKFLOW="build-26519-per-lens-viewfinder-response.yml"
BASE_ARTIFACT="photon-26519-per-lens-viewfinder-response-v2"
BASE_SOURCE_TAR_NAME="26519_candidate_app_source.tar.gz"
BASE_SOURCE_MANIFEST_NAME="26519_candidate_source.sha256"
REPO="${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}"
BJZHOU_VENDOR_HEAD="09c76e57e8f01a5a8fc536ab41fc80ba642d4042"
BJZHOU_MANIFEST="$ROOT/26507_BJZHOU_NATIVE_DEPENDENCIES.sha256"
BJZHOU_COMMIT_FILE="$ROOT/26507_BJZHOU_DEPENDENCY_COMMIT.txt"
RELEASE_SPATIAL_HEAD="c4ff5a3e99b5f9f6027ba1c038eb7cc850bb9b01"
RELEASE_STACKER_BLOB="24613918b7d830f19b573346ab02c9684e92eb6f"
RELEASE_SHADERS_BLOB="2d6aea082730d2f6d10f5c6e0930d6e2199006cc"
APPLY="$ROOT/apply_26520_zsl_stacked_dng.py"
VALIDATE="$ROOT/validate_26520_zsl_stacked_dng.py"
HANDOFF="$ROOT/26520_HANDOFF_HASHES.sha256"
REF_FILE="$ROOT/26520_BJZHOU_RELEASE_SPATIAL_REF.txt"
OUT="$ROOT/build_26520_zsl_stacked_dng_outputs"
WORK="$ROOT/.build_26520_direct_26519_work"
ART="$WORK/26519_artifact"; BASE="$WORK/tested26519"; AFTER="$WORK/candidate26520"
REL="$WORK/bjzhou_released_1271_spatial"; BJ="$WORK/bjzhou_vendor"
VERSION_NAME="0.9726520"; VERSION_BUILD="26520"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-zsl-stacked-dng-debug.apk"

rm -rf "$OUT" "$WORK"; mkdir -p "$OUT" "$ART" "$BASE" "$AFTER"
exec > >(tee "$OUT/26520_build.log") 2>&1

echo "=== 26520 GATE 0: exact 26519 + backup + handoff integrity ==="
BRANCH="$(git branch --show-current)"; START_HEAD="$(git rev-parse HEAD)"
[[ "$BRANCH" == "$EXPECTED_BRANCH" && "$BRANCH" != "dev" ]] || fail "wrong/protected branch $BRANCH"
git merge-base --is-ancestor "$SUCCESSFUL_26519_HEAD" HEAD || fail "not descended from latest 26519"
REMOTE_BACKUP="$(git ls-remote origin "refs/heads/$BACKUP_26519" | awk '{print $1}')"
[[ "$REMOTE_BACKUP" == "$SUCCESSFUL_26519_HEAD" ]] || fail "backup missing/wrong $BACKUP_26519 -> ${REMOTE_BACKUP:-MISSING}"
for f in "$APPLY" "$VALIDATE" "$HANDOFF" "$REF_FILE" "$BJZHOU_MANIFEST" "$BJZHOU_COMMIT_FILE"; do [[ -f "$f" ]] || fail "missing $(basename "$f")"; done
sha256sum -c "$HANDOFF"; python3 -m py_compile "$APPLY" "$VALIDATE"; bash -n "$0"
[[ "$(tr -d '\r\n' < "$BJZHOU_COMMIT_FILE")" == "$BJZHOU_VENDOR_HEAD" ]] || fail "vendor dependency commit drift"
grep -F "BJZHOU_RELEASE_SPATIAL_COMMIT=$RELEASE_SPATIAL_HEAD" "$REF_FILE" >/dev/null || fail "c4ff manifest drift"
git diff --name-only "$SUCCESSFUL_26519_HEAD"..HEAD -- app/src/main app/version.properties > "$OUT/26520_committed_runtime_drift_after_26519.txt"
[[ ! -s "$OUT/26520_committed_runtime_drift_after_26519.txt" ]] || fail "committed runtime drift after 26519"
git diff --name-only "$SUCCESSFUL_26519_HEAD"..HEAD -- gradlew gradlew.bat gradle build.gradle settings.gradle gradle.properties app/build.gradle app/proguard-rules.pro > "$OUT/26520_protected_build_drift.txt"
[[ ! -s "$OUT/26520_protected_build_drift.txt" ]] || fail "protected build infrastructure drift"
pass "latest 26519 + exact backup + handoff-only commit verified"

echo "=== 26520 GATE 1: recover successful 26519 artifact source ==="
command -v gh >/dev/null || fail "GitHub CLI unavailable"; [[ -n "${GH_TOKEN:-}" ]] || fail "GH_TOKEN missing"
RUN_JSON="$WORK/26519_runs.json"
gh run list --repo "$REPO" --workflow "$BASE_WORKFLOW" --branch "$EXPECTED_BRANCH" --status success --limit 50 --json databaseId,headSha,conclusion,createdAt > "$RUN_JSON"
RUN_ID="$(python3 - "$RUN_JSON" "$SUCCESSFUL_26519_HEAD" <<'PYRUN'
import json,sys
runs=json.load(open(sys.argv[1])); head=sys.argv[2]
exact=[r for r in runs if r.get('headSha')==head and r.get('conclusion')=='success']
if not exact: raise SystemExit('no successful 26519 workflow at exact HEAD '+head)
print(exact[0]['databaseId'])
PYRUN
)"
[[ "$RUN_ID" =~ ^[0-9]+$ ]] || fail "invalid 26519 run id"
gh run download "$RUN_ID" --repo "$REPO" --name "$BASE_ARTIFACT" --dir "$ART"
mapfile -t SOURCE_TARS < <(find "$ART" -type f -name "$BASE_SOURCE_TAR_NAME" -print)
mapfile -t SOURCE_MANIFESTS < <(find "$ART" -type f -name "$BASE_SOURCE_MANIFEST_NAME" -print)
[[ "${#SOURCE_TARS[@]}" -eq 1 && "${#SOURCE_MANIFESTS[@]}" -eq 1 ]] || fail "26519 source artifact cardinality mismatch"
SOURCE_TAR="${SOURCE_TARS[0]}"; SOURCE_MANIFEST="${SOURCE_MANIFESTS[0]}"
BASE_TAR_SHA="$(sha "$SOURCE_TAR")"; SOURCE_MANIFEST_SHA="$(sha "$SOURCE_MANIFEST")"
tar -xzf "$SOURCE_TAR" -C "$BASE"
( cd "$BASE" && sha256sum -c "$SOURCE_MANIFEST" ) > "$OUT/26519_source_manifest_check.txt"
[[ "$(grep '^VERSION_NAME=' "$BASE/app/version.properties"|cut -d= -f2)" == "0.9726519" ]] || fail "base version name mismatch"
[[ "$(grep '^VERSION_BUILD=' "$BASE/app/version.properties"|cut -d= -f2)" == "26519" ]] || fail "base build mismatch"
grep -F 'IRIS_26519_PER_LENS_VIEWFINDER_RESPONSE' "$BASE/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java" >/dev/null || fail "26519 matcher missing"
grep -F 'pref_motion_viewfinder_match_strength' "$BASE/app/src/main/res/xml/preferences.xml" >/dev/null || fail "26519 slider missing"
grep -F 'IRIS_26518_RELEASED_1271_RESULT_ABI_SNR_BRIDGE' "$BASE/app/src/main/java/com/hinnka/mycamera/processor/GlesMgc1271ReleasedSpatialStacker.kt" >/dev/null || fail "26518 SNR ABI missing"
grep -F 'IRIS_26517_RELEASED_1271_SPATIAL_RGB_OWNER' "$BASE/app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt" >/dev/null || fail "c4ff owner missing"
pass "actual successful 26519 source proven"

echo "=== 26520 GATE 2: patch FIRST; one-frame + shared normal fused-Bayer DNG ==="
cp -a "$BASE/." "$AFTER/"
PATCH="$OUT/26520_RUNTIME_DELTA_FROM_TESTED_26519.patch"; PATCH_SHA="$OUT/26520_RUNTIME_DELTA_FROM_TESTED_26519.patch.sha256"
python3 "$APPLY" "$AFTER" --patch-out "$PATCH" --patch-sha-out "$PATCH_SHA"
( cd "$OUT" && sha256sum -c "$(basename "$PATCH_SHA")" )
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" --apply-script "$APPLY" --patch "$PATCH" --patch-sha "$PATCH_SHA" | tee "$OUT/26520_prebuild_validator.txt"
[[ "$(grep '^VERSION_NAME=' "$AFTER/app/version.properties"|cut -d= -f2)" == "0.9726519" ]] || fail "version changed before build block"
[[ "$(grep '^VERSION_BUILD=' "$AFTER/app/version.properties"|cut -d= -f2)" == "26519" ]] || fail "build changed before build block"
echo "PRE-BUILD SAFETY PROOF PASSED"

echo "=== 26520 GATE 3: VERSION $VERSION_NAME/$VERSION_BUILD + APK build in SAME guarded block ==="
python3 - "$AFTER/app/version.properties" "$VERSION_NAME" "$VERSION_BUILD" <<'PYVER'
from pathlib import Path
import sys
p=Path(sys.argv[1]); vn=sys.argv[2]; vb=sys.argv[3]; s=p.read_text()
assert 'VERSION_NAME=0.9726519' in s and 'VERSION_BUILD=26519' in s
s=s.replace('VERSION_NAME=0.9726519','VERSION_NAME='+vn,1).replace('VERSION_BUILD=26519','VERSION_BUILD='+vb,1)
p.write_text(s)
PYVER

rm -rf "$BJ"; git init -q "$BJ"; git -C "$BJ" remote add origin https://github.com/bjzhou/PhotonCamera.git
git -C "$BJ" config core.sparseCheckout true; mkdir -p "$BJ/.git/info"
cat > "$BJ/.git/info/sparse-checkout" <<'SPARSE'
/app/src/main/cpp/libjpeg-turbo/
/app/src/main/cpp/libultrahdr/
SPARSE
git -C "$BJ" fetch --depth=1 origin "$BJZHOU_VENDOR_HEAD"; git -C "$BJ" checkout -q --detach FETCH_HEAD
[[ "$(git -C "$BJ" rev-parse HEAD)" == "$BJZHOU_VENDOR_HEAD" ]] || fail "vendor checkout drift"
THIRD="$AFTER/app/src/main/cpp/third_party_26507"; rm -rf "$THIRD"; mkdir -p "$THIRD"
cp -a "$BJ/app/src/main/cpp/libjpeg-turbo" "$THIRD/libjpeg-turbo"; cp -a "$BJ/app/src/main/cpp/libultrahdr" "$THIRD/libultrahdr"
( cd "$THIRD" && sha256sum -c "$BJZHOU_MANIFEST" ) > "$OUT/26520_vendor_manifest_check.txt"

rm -rf app/src/main; mkdir -p app/src; cp -a "$AFTER/app/src/main" app/src/main; cp "$AFTER/app/version.properties" app/version.properties
assert_cpp_deps_exact() {
  local phase="$1" expected actual
  if [[ "$phase" == pre ]]; then expected=$'.gitignore'; else expected=$'.gitignore\narchive.h\narchive_entry.h\ntechnicallyflac.h\ntiny_dng_writer.h'; fi
  actual="$(find app/src/main/cpp/deps -mindepth 1 -maxdepth 1 -type f -printf '%f\n' | LC_ALL=C sort)"
  [[ "$actual" == "$expected" ]] || fail "unexpected app/src/main/cpp/deps contents ($phase)"
}
audited_runtime_manifest() {
  { find app/src/main -type f ! -path 'app/src/main/cpp/third_party_26507/*' ! -path 'app/src/main/cpp/deps/*' -print; echo app/src/main/cpp/deps/.gitignore; echo app/version.properties; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done
}
assert_cpp_deps_exact pre; audited_runtime_manifest > "$OUT/26520_pre_gradle_audited_runtime.sha256"
chmod +x ./gradlew; ./gradlew clean :app:assembleDebug --stacktrace
assert_cpp_deps_exact post; audited_runtime_manifest > "$OUT/26520_post_gradle_audited_runtime.sha256"
cmp -s "$OUT/26520_pre_gradle_audited_runtime.sha256" "$OUT/26520_post_gradle_audited_runtime.sha256" || { diff -u "$OUT/26520_pre_gradle_audited_runtime.sha256" "$OUT/26520_post_gradle_audited_runtime.sha256" > "$OUT/26520_gradle_runtime_source_diff.txt" || true; fail "Gradle mutated audited 26520 runtime source"; }
pass "Gradle preserved validated runtime; generated deps exact"

mapfile -t APKS < <(find app/build/outputs/apk/debug -maxdepth 1 -type f -name '*.apk' -print)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one debug APK, found ${#APKS[@]}"
rm -f "$FINAL"; cp "${APKS[0]}" "$FINAL"; [[ -s "$FINAL" ]] || fail "final APK missing"
sha256sum "$FINAL" | tee "$OUT/26520_APK.sha256"

rm -rf "$AFTER/app/src/main/cpp/third_party_26507"
( cd "$AFTER" && { find app/src/main -type f -print; echo app/version.properties; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done ) > "$OUT/26520_candidate_source.sha256"
tar --sort=name --mtime='UTC 2026-08-21 00:00:00' --owner=0 --group=0 --numeric-owner -czf "$OUT/26520_candidate_app_source.tar.gz" -C "$AFTER" app/src/main app/version.properties

cat > "$OUT/26520_FINAL_PROVENANCE.txt" <<EOF
BUILD=0.9726520/26520
BASE_HEAD=$SUCCESSFUL_26519_HEAD
BASE_ARTIFACT=$BASE_ARTIFACT
BACKUP_BRANCH=$BACKUP_26519
C4FF_FROZEN=true
VIEWFINDER_26519_FROZEN=true
ONE_NORMAL_EXPLICIT_VALID=true
MULTIFRAME_SILENT_ONE_FALLBACK=false
FROZEN_METADATA_GRACE_MS=180
POST_SHUTTER_NORMAL_TOPUP=false
EXACT_TIMESTAMP_METADATA_ONLY=true
DNG_NORMAL_POPULATION_EQUALS_JPEG_NORMAL_POPULATION=true
DNG_SOURCE=EXISTING_NORMAL_ONLY_WRONSKI_BAYER_ACCUMULATOR
DNG_SECOND_ALIGNMENT_PASS=false
DNG_PYRAMID_MERGE=false
DNG_SHORT_LONG_BENTO=false
DNG_RGB_TONE_DISPLAY_DENOISE_SHARPEN=false
EOF
echo "PASS 1/3: exact 26519 + backup + frozen c4ff/viewfinder owners"
echo "PASS 2/3: explicit one-normal + frozen exact-metadata grace; no post-shutter normal top-up"
echo "PASS 3/3: shared normal Bayer DNG + same guarded version/build/APK procedure"
