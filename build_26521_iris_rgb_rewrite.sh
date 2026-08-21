#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }

ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
BASE_HEAD="9b59a27235747733bacdde68bf6a888ebffefa18"
BACKUP="backup-26519-before-26521-iris-rgb-rewrite"
BASE_WORKFLOW="build-26519-per-lens-viewfinder-response.yml"
BASE_ARTIFACT="photon-26519-per-lens-viewfinder-response-v2"
REPO="${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}"
APPLY20="$ROOT/apply_26520_zsl_stacked_dng.py"
APPLY21="$ROOT/apply_26521_iris_rgb_rewrite.py"
VALIDATE="$ROOT/validate_26521_iris_rgb_rewrite.py"
HANDOFF="$ROOT/26521_HANDOFF_HASHES.sha256"
OUT="$ROOT/build_26521_iris_rgb_rewrite_outputs"
WORK="$ROOT/.build_26521_work"
ART="$WORK/26519_artifact"
BASE="$WORK/tested26519"
AFTER="$WORK/candidate26521"
VERSION_NAME="0.9726521"
VERSION_BUILD="26521"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-iris-rgb-rewrite-debug.apk"

rm -rf "$OUT" "$WORK"
mkdir -p "$OUT" "$ART" "$BASE" "$AFTER"
exec > >(tee "$OUT/26521_build.log") 2>&1

echo "=== 26521 GATE 0 ==="
[[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
[[ "$(git branch --show-current)" != "dev" ]] || fail "dev protected"
git merge-base --is-ancestor "$BASE_HEAD" HEAD || fail "not descended from exact 26519"
REMOTE_BACKUP="$(git ls-remote origin "refs/heads/$BACKUP" | awk '{print $1}')"
[[ "$REMOTE_BACKUP" == "$BASE_HEAD" ]] || fail "backup missing/wrong"
sha256sum -c "$HANDOFF"
python3 -m py_compile "$APPLY20" "$APPLY21" "$VALIDATE"
bash -n "$0"
git diff --name-only "$BASE_HEAD"..HEAD -- app/src/main app/version.properties > "$OUT/committed_runtime_drift.txt"
[[ ! -s "$OUT/committed_runtime_drift.txt" ]] || fail "runtime source committed before guarded build"
git diff --name-only "$BASE_HEAD"..HEAD -- gradlew gradlew.bat gradle build.gradle settings.gradle gradle.properties app/build.gradle app/proguard-rules.pro > "$OUT/protected_build_infrastructure_drift.txt"
[[ ! -s "$OUT/protected_build_infrastructure_drift.txt" ]] || fail "protected build infrastructure drift after 26519"
pass "exact 26519 sibling + existing backup verified"

echo "=== 26521 GATE 1: recover exact successful 26519 artifact ==="
command -v gh >/dev/null || fail "gh unavailable"
[[ -n "${GH_TOKEN:-}" ]] || fail "GH_TOKEN missing"
gh run list --repo "$REPO" --workflow "$BASE_WORKFLOW" --branch "$EXPECTED_BRANCH" --status success --limit 50 --json databaseId,headSha,conclusion > "$WORK/runs.json"
RUN_ID="$(python3 - "$WORK/runs.json" "$BASE_HEAD" <<'PY'
import json,sys
r=[x for x in json.load(open(sys.argv[1])) if x.get('headSha')==sys.argv[2] and x.get('conclusion')=='success']
if not r: raise SystemExit('no successful exact 26519 run')
print(r[0]['databaseId'])
PY
)"
gh run download "$RUN_ID" --repo "$REPO" --name "$BASE_ARTIFACT" --dir "$ART"
SOURCE_TAR="$(find "$ART" -type f -name '26519_candidate_app_source.tar.gz' -print -quit)"
SOURCE_MANIFEST="$(find "$ART" -type f -name '26519_candidate_source.sha256' -print -quit)"
[[ -f "$SOURCE_TAR" && -f "$SOURCE_MANIFEST" ]] || fail "26519 source artifact missing"
tar -xzf "$SOURCE_TAR" -C "$BASE"
( cd "$BASE" && sha256sum -c "$SOURCE_MANIFEST" ) > "$OUT/26519_source_manifest_check.txt"
[[ "$(grep '^VERSION_NAME=' "$BASE/app/version.properties"|cut -d= -f2)" == "0.9726519" ]]
[[ "$(grep '^VERSION_BUILD=' "$BASE/app/version.properties"|cut -d= -f2)" == "26519" ]]
pass "successful 26519 source recovered"

echo "=== 26521 GATE 2: combined rollback patch FIRST ==="
cp -a "$BASE/." "$AFTER/"
PATCH="$OUT/26521_COMBINED_RUNTIME_DELTA_FROM_TESTED_26519.patch"
PATCH_SHA="$OUT/26521_COMBINED_RUNTIME_DELTA_FROM_TESTED_26519.patch.sha256"
python3 "$APPLY21" "$AFTER" --apply26520 "$APPLY20" --patch-out "$PATCH" --patch-sha-out "$PATCH_SHA"
( cd "$OUT" && sha256sum -c "$(basename "$PATCH_SHA")" )
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" --apply26520 "$APPLY20" --patch "$PATCH" --patch-sha "$PATCH_SHA" | tee "$OUT/26521_prebuild_validator.txt"
echo "PRE-BUILD SAFETY PROOF PASSED"

echo "=== 26521 GATE 3: version increment + APK build same block ==="
python3 - "$AFTER/app/version.properties" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); s=p.read_text()
assert 'VERSION_NAME=0.9726519' in s and 'VERSION_BUILD=26519' in s
p.write_text(s.replace('VERSION_NAME=0.9726519','VERSION_NAME=0.9726521',1)
              .replace('VERSION_BUILD=26519','VERSION_BUILD=26521',1))
PY

BJ="$WORK/bjzhou_vendor"
VENDOR_HEAD="09c76e57e8f01a5a8fc536ab41fc80ba642d4042"
rm -rf "$BJ"; git init -q "$BJ"; git -C "$BJ" remote add origin https://github.com/bjzhou/PhotonCamera.git
git -C "$BJ" config core.sparseCheckout true; mkdir -p "$BJ/.git/info"
cat > "$BJ/.git/info/sparse-checkout" <<'SPARSE'
/app/src/main/cpp/libjpeg-turbo/
/app/src/main/cpp/libultrahdr/
SPARSE
git -C "$BJ" fetch --depth=1 origin "$VENDOR_HEAD"
git -C "$BJ" checkout -q --detach FETCH_HEAD
THIRD="$AFTER/app/src/main/cpp/third_party_26507"
rm -rf "$THIRD"; mkdir -p "$THIRD"
cp -a "$BJ/app/src/main/cpp/libjpeg-turbo" "$THIRD/libjpeg-turbo"
cp -a "$BJ/app/src/main/cpp/libultrahdr" "$THIRD/libultrahdr"
( cd "$THIRD" && sha256sum -c "$ROOT/26507_BJZHOU_NATIVE_DEPENDENCIES.sha256" ) > "$OUT/vendor_manifest_check.txt"

rm -rf app/src/main; mkdir -p app/src
cp -a "$AFTER/app/src/main" app/src/main
cp "$AFTER/app/version.properties" app/version.properties

assert_cpp_deps_exact(){
  local phase="$1" expected actual
  if [[ "$phase" == pre ]]; then expected=$'.gitignore'; else expected=$'.gitignore\narchive.h\narchive_entry.h\ntechnicallyflac.h\ntiny_dng_writer.h'; fi
  actual="$(find app/src/main/cpp/deps -mindepth 1 -maxdepth 1 -type f -printf '%f\n'|LC_ALL=C sort)"
  [[ "$actual" == "$expected" ]] || fail "unexpected deps ($phase)"
}
audited_manifest(){
  { find app/src/main -type f ! -path 'app/src/main/cpp/third_party_26507/*' ! -path 'app/src/main/cpp/deps/*' -print; echo app/src/main/cpp/deps/.gitignore; echo app/version.properties; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done
}
assert_cpp_deps_exact pre
audited_manifest > "$OUT/pre_gradle_runtime.sha256"
chmod +x ./gradlew
./gradlew clean :app:assembleDebug --stacktrace
assert_cpp_deps_exact post
audited_manifest > "$OUT/post_gradle_runtime.sha256"
cmp -s "$OUT/pre_gradle_runtime.sha256" "$OUT/post_gradle_runtime.sha256" || fail "Gradle mutated audited runtime"
pass "Gradle preserved validated runtime"

mapfile -t APKS < <(find app/build/outputs/apk/debug -maxdepth 1 -type f -name '*.apk' -print)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected one APK"
rm -f "$FINAL"; cp "${APKS[0]}" "$FINAL"
sha256sum "$FINAL" | tee "$OUT/26521_APK.sha256"

rm -rf "$AFTER/app/src/main/cpp/third_party_26507"
( cd "$AFTER" && { find app/src/main -type f -print; echo app/version.properties; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done ) > "$OUT/26521_candidate_source.sha256"
tar --sort=name --mtime='UTC 2026-08-21 00:00:00' --owner=0 --group=0 --numeric-owner -czf "$OUT/26521_candidate_app_source.tar.gz" -C "$AFTER" app/src/main app/version.properties

cat > "$OUT/26521_FINAL_PROVENANCE.txt" <<EOF
BUILD=0.9726521/26521
BASE_HEAD=$BASE_HEAD
BACKUP=$BACKUP
SIBLING_OF_26520=true
ONE_FRAME_FIX_IDENTICAL_TO_26520=true
STACKED_DNG_ARCH_IDENTICAL_TO_26520=true
WRONSKI_ALIGNMENT_FROZEN=true
ACTIVE_C4FF_SPATIAL_RGB=false
RGB_OWNER=IRIS_26521_INDEPENDENT_FUSED_BAYER_EDGE_COLOR_DIFFERENCE
DORMANT_OLD_SPATIAL_CODE_RETAINED_FOR_ROLLBACK=true
EOF

echo "PASS 1/3: exact 26519 sibling + backup"
echo "PASS 2/3: identical 26520 capture/DNG + frozen Wronski"
echo "PASS 3/3: active c4ff Spatial RGB disabled; Iris RGB rewrite built"
