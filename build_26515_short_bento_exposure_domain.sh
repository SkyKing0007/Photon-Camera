#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }

ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
SUCCESSFUL_26514_HEAD="e9855a3af7a79801a762ec3f99b441474926f009"
BACKUP_26514="backup-26514-before-26515-short-bento-fix-20260820"
BASE_WORKFLOW="build-26514-iris-profiles-controls.yml"
BASE_ARTIFACT="photon-26514-iris-profiles-controls"
REPO="${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}"
BJZHOU_HEAD="09c76e57e8f01a5a8fc536ab41fc80ba642d4042"
BJZHOU_MANIFEST="$ROOT/26507_BJZHOU_NATIVE_DEPENDENCIES.sha256"
BJZHOU_COMMIT_FILE="$ROOT/26507_BJZHOU_DEPENDENCY_COMMIT.txt"
APPLY_26515="$ROOT/apply_26515_short_bento_exposure_domain.py"
VALIDATE_26515="$ROOT/validate_26515_short_bento_exposure_domain.py"
HANDOFF_26515="$ROOT/26515_HANDOFF_HASHES.sha256"
INERT_DERIVED="$ROOT/patch_26515_derived_builder.py"
OUT="$ROOT/build_26515_short_bento_exposure_domain_outputs"
WORK="$ROOT/.build_26515_direct_26514_work"
ART="$WORK/26514_artifact"
BASE="$WORK/tested26514"
AFTER="$WORK/candidate26515"
BJ="$WORK/bjzhou1271_vendor"
VERSION_NAME="0.9726515"
VERSION_BUILD="26515"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-short-bento-domain-fix-debug.apk"

rm -rf "$OUT" "$WORK"; mkdir -p "$OUT" "$ART" "$BASE" "$AFTER"
exec > >(tee "$OUT/26515_build.log") 2>&1

echo "=== 26515 V4 GATE 0: exact tested-26514 checkpoint + backup + direct-source-only handoff ==="
BRANCH="$(git branch --show-current)"; START_HEAD="$(git rev-parse HEAD)"
[[ "$BRANCH" == "$EXPECTED_BRANCH" && "$BRANCH" != "dev" ]] || fail "wrong/protected branch $BRANCH"
git merge-base --is-ancestor "$SUCCESSFUL_26514_HEAD" HEAD || fail "handoff is not descended from successful 26514 HEAD"
REMOTE_BACKUP="$(git ls-remote origin "refs/heads/$BACKUP_26514" | awk '{print $1}')"
[[ "$REMOTE_BACKUP" == "$SUCCESSFUL_26514_HEAD" ]] || fail "backup missing/wrong: $BACKUP_26514 -> ${REMOTE_BACKUP:-MISSING}; expected $SUCCESSFUL_26514_HEAD"
for f in "$APPLY_26515" "$VALIDATE_26515" "$HANDOFF_26515" "$INERT_DERIVED" "$BJZHOU_MANIFEST" "$BJZHOU_COMMIT_FILE"; do
  [[ -f "$f" ]] || fail "missing $(basename "$f")"
done
sha256sum -c "$HANDOFF_26515"
python3 -m py_compile "$APPLY_26515" "$VALIDATE_26515"
grep -F 'DISABLED_26515_V4_DIRECT_26514_SOURCE' "$INERT_DERIVED" >/dev/null || fail "historical constructor tombstone missing"
[[ "$(tr -d '\r\n' < "$BJZHOU_COMMIT_FILE")" == "$BJZHOU_HEAD" ]] || fail "pinned bjzhou dependency commit drift"

# 26515 handoff commits may not change runtime or build infrastructure before this guarded build.
RUNTIME_DRIFT="$OUT/26515_committed_runtime_drift_after_26514.txt"
git diff --name-only "$SUCCESSFUL_26514_HEAD"..HEAD -- app/src/main app/version.properties > "$RUNTIME_DRIFT"
[[ ! -s "$RUNTIME_DRIFT" ]] || { cat "$RUNTIME_DRIFT" >&2; fail "committed runtime drift exists after tested 26514"; }
PROTECTED_DRIFT="$OUT/26515_protected_build_infrastructure_drift.txt"
git diff --name-only "$SUCCESSFUL_26514_HEAD"..HEAD -- \
  gradlew gradlew.bat gradle build.gradle settings.gradle gradle.properties \
  app/build.gradle app/proguard-rules.pro > "$PROTECTED_DRIFT"
[[ ! -s "$PROTECTED_DRIFT" ]] || { cat "$PROTECTED_DRIFT" >&2; fail "protected Gradle/build infrastructure drifted after tested 26514"; }

# Mechanical prohibition: v4 may reference the 26514 artifact, but no older runtime constructor.
python3 - "$0" <<'PYNOBACK'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text()
bad=(
    'build_'+'26512', 'apply_'+'26513', 'validate_'+'26513',
    'derived_from_exact_'+'26512', 'candidate'+'26512', 'golden'+'26513',
)
found=[x for x in bad if x in s]
if found:
    raise SystemExit('historical runtime constructor reference(s) found: '+', '.join(found))
print('PASS: no 26512/26513 runtime constructor references in v4 builder')
PYNOBACK
pass "exact 26514 HEAD/backup verified; no committed runtime drift; historical constructors prohibited"

echo "=== 26515 V4 GATE 1: recover the ACTUAL source snapshot emitted by successful 26514 ==="
command -v gh >/dev/null || fail "GitHub CLI (gh) unavailable"
[[ -n "${GH_TOKEN:-}" ]] || fail "GH_TOKEN missing; Actions artifact cannot be authenticated"
RUN_JSON="$WORK/26514_runs.json"
gh run list --repo "$REPO" --workflow "$BASE_WORKFLOW" --branch "$EXPECTED_BRANCH" --status success \
  --limit 50 --json databaseId,headSha,conclusion,createdAt > "$RUN_JSON"
RUN_ID="$(python3 - "$RUN_JSON" "$SUCCESSFUL_26514_HEAD" <<'PYRUN'
import json,sys
runs=json.load(open(sys.argv[1])); head=sys.argv[2]
exact=[r for r in runs if r.get('headSha')==head and r.get('conclusion')=='success']
if not exact:
    raise SystemExit('no successful 26514 workflow run found at exact HEAD '+head)
# gh returns newest first; require one exact-head result and use newest if manually re-run.
print(exact[0]['databaseId'])
PYRUN
)"
[[ "$RUN_ID" =~ ^[0-9]+$ ]] || fail "invalid 26514 workflow run id: $RUN_ID"
gh run download "$RUN_ID" --repo "$REPO" --name "$BASE_ARTIFACT" --dir "$ART"
mapfile -t SOURCE_TARS < <(find "$ART" -type f -name '26514_candidate_app_source.tar.gz' -print)
mapfile -t SOURCE_MANIFESTS < <(find "$ART" -type f -name '26514_candidate_source.sha256' -print)
[[ "${#SOURCE_TARS[@]}" -eq 1 ]] || fail "expected one 26514 candidate source archive, found ${#SOURCE_TARS[@]}"
[[ "${#SOURCE_MANIFESTS[@]}" -eq 1 ]] || fail "expected one 26514 source manifest, found ${#SOURCE_MANIFESTS[@]}"
SOURCE_TAR="${SOURCE_TARS[0]}"; SOURCE_MANIFEST="${SOURCE_MANIFESTS[0]}"
BASE_TAR_SHA="$(sha "$SOURCE_TAR")"
SOURCE_MANIFEST_SHA="$(sha "$SOURCE_MANIFEST")"
# Artifact archive must contain only the audited runtime source and version identity.
python3 - "$SOURCE_TAR" <<'PYTAR'
import sys,tarfile
with tarfile.open(sys.argv[1],'r:gz') as t:
    names=[m.name.lstrip('./') for m in t.getmembers() if m.name not in ('.','./')]
for n in names:
    if not (n in {'app','app/','app/src','app/src/','app/src/main','app/src/main/','app/version.properties'} or n.startswith('app/src/main/')):
        raise SystemExit('unexpected path in tested-26514 source archive: '+n)
print('PASS: 26514 artifact source archive contains runtime source + version only')
PYTAR
tar -xzf "$SOURCE_TAR" -C "$BASE"
( cd "$BASE" && sha256sum -c "$SOURCE_MANIFEST" ) > "$OUT/26514_artifact_source_manifest_check.txt"
[[ "$(grep '^VERSION_NAME=' "$BASE/app/version.properties" | cut -d= -f2)" == "0.9726514" ]] || fail "artifact source is not version 0.9726514"
[[ "$(grep '^VERSION_BUILD=' "$BASE/app/version.properties" | cut -d= -f2)" == "26514" ]] || fail "artifact source is not build 26514"
grep -F 'IRIS_26513_RGB_DETAIL_SCALE_MULTIPLIER = 1.10f' "$BASE/app/src/main/java/com/hinnka/mycamera/processor/MgcSpatialMergeTuning.kt" >/dev/null || fail "26513 Spatial detail invariant missing from tested 26514 source"
grep -F 'IRIS_26514_MOTION_USER_CONTROLS_OWNER' "$BASE/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java" >/dev/null || fail "26514 controls owner missing"
grep -F 'return Float.parseFloat(value);' "$BASE/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java" >/dev/null || fail "successful 26514 float-settings CI fix missing"
grep -F 'parameters.motionV2DisplayGain = referenceDisplayGain * baselineScale' "$BASE/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt" >/dev/null || fail "expected pre-26515 mixed Short/display authority not found"
cp -a "$BASE/." "$AFTER/"
cat > "$OUT/26515_BASE_SOURCE_PROVENANCE.txt" <<EOF
BASE_WORKFLOW=$BASE_WORKFLOW
BASE_ARTIFACT=$BASE_ARTIFACT
BASE_RUN_ID=$RUN_ID
BASE_HEAD=$SUCCESSFUL_26514_HEAD
BASE_SOURCE_TAR_SHA256=$BASE_TAR_SHA
BASE_SOURCE_MANIFEST_SHA256=$SOURCE_MANIFEST_SHA
BASE_VERSION=0.9726514/26514
EOF
pass "actual successful-26514 source snapshot recovered and manifest-verified"

echo "=== 26515 V4 GATE 2: create rollback patch FIRST, apply only Short/Bento domain fix, validate exact delta ==="
PATCH="$OUT/26515_RUNTIME_DELTA_FROM_TESTED_26514.patch"
PATCH_SHA="$OUT/26515_RUNTIME_DELTA_FROM_TESTED_26514.patch.sha256"
python3 "$APPLY_26515" "$AFTER" --patch-out "$PATCH" --patch-sha-out "$PATCH_SHA"
( cd "$OUT" && sha256sum -c "$(basename "$PATCH_SHA")" )
python3 "$VALIDATE_26515" --base "$BASE" --candidate "$AFTER" --apply-script "$APPLY_26515"
# Changed-source syntax smoke. Gradle below remains the authoritative Android/Kotlin type check.
python3 - "$AFTER" <<'PYSOURCE'
from pathlib import Path
import sys
r=Path(sys.argv[1])
for rel in (
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
):
    p=r/rel
    assert p.is_file() and p.stat().st_size>0,rel
print('PASS: all four 26515 changed source files materialized')
PYSOURCE
echo "PRE-BUILD SAFETY PROOF PASSED"
pass "rollback/audit patch existed before writes; exact four-file runtime delta validated"

echo "=== 26515 V4 GATE 3: VERSION ${VERSION_NAME}/${VERSION_BUILD} + one APK build in the SAME guarded block ==="
python3 - "$AFTER/app/version.properties" "$VERSION_NAME" "$VERSION_BUILD" <<'PYVER'
from pathlib import Path
import sys
p=Path(sys.argv[1]); vn=sys.argv[2]; vb=sys.argv[3]; s=p.read_text()
assert 'VERSION_NAME=0.9726514' in s and 'VERSION_BUILD=26514' in s
s=s.replace('VERSION_NAME=0.9726514','VERSION_NAME='+vn,1)
s=s.replace('VERSION_BUILD=26514','VERSION_BUILD='+vb,1)
p.write_text(s)
assert 'VERSION_NAME='+vn in p.read_text() and 'VERSION_BUILD='+vb in p.read_text()
PYVER

# Rehydrate only the exact pinned vendor trees deliberately omitted from source snapshots.
rm -rf "$BJ"; git init -q "$BJ"; git -C "$BJ" remote add origin https://github.com/bjzhou/PhotonCamera.git
git -C "$BJ" config core.sparseCheckout true
mkdir -p "$BJ/.git/info"
cat > "$BJ/.git/info/sparse-checkout" <<'SPARSE'
/app/src/main/cpp/libjpeg-turbo/
/app/src/main/cpp/libultrahdr/
SPARSE
git -C "$BJ" fetch --depth=1 origin "$BJZHOU_HEAD"
git -C "$BJ" checkout -q --detach FETCH_HEAD
[[ "$(git -C "$BJ" rev-parse HEAD)" == "$BJZHOU_HEAD" ]] || fail "pinned bjzhou vendor checkout drift"
THIRD="$AFTER/app/src/main/cpp/third_party_26507"
rm -rf "$THIRD"; mkdir -p "$THIRD"
cp -a "$BJ/app/src/main/cpp/libjpeg-turbo" "$THIRD/libjpeg-turbo"
cp -a "$BJ/app/src/main/cpp/libultrahdr" "$THIRD/libultrahdr"
( cd "$THIRD" && sha256sum -c "$BJZHOU_MANIFEST" ) > "$OUT/26515_bjzhou_vendor_manifest_check.txt"
pass "only byte-verified pinned JPEG/UHDR vendor dependencies rehydrated; no historical Iris runtime reconstructed"

# Overlay exactly the tested-26514 source plus the validated four-file 26515 delta.
rm -rf app/src/main
cp -a "$AFTER/app/src/main" app/src/main
cp "$AFTER/app/version.properties" app/version.properties

assert_cpp_deps_exact(){
  local phase="$1" expected actual
  if [[ "$phase" == "pre" ]]; then expected=$'.gitignore';
  else expected=$'.gitignore\narchive.h\narchive_entry.h\ntechnicallyflac.h\ntiny_dng_writer.h'; fi
  actual="$(find app/src/main/cpp/deps -mindepth 1 -maxdepth 1 -type f -printf '%f\n' | LC_ALL=C sort)"
  [[ "$actual" == "$expected" ]] || { printf 'Expected cpp/deps (%s):\n%s\nActual:\n%s\n' "$phase" "$expected" "$actual" >&2; fail "unexpected app/src/main/cpp/deps contents"; }
}
audited_runtime_manifest(){
  { find app/src/main -type f ! -path 'app/src/main/cpp/third_party_26507/*' ! -path 'app/src/main/cpp/deps/*' -print; echo app/src/main/cpp/deps/.gitignore; echo app/version.properties; } |
    LC_ALL=C sort | while read -r f; do sha256sum "$f"; done
}
assert_cpp_deps_exact pre
audited_runtime_manifest > "$OUT/26515_pre_gradle_audited_runtime.sha256"
chmod +x ./gradlew
./gradlew clean :app:assembleDebug --stacktrace
assert_cpp_deps_exact post
audited_runtime_manifest > "$OUT/26515_post_gradle_audited_runtime.sha256"
cmp -s "$OUT/26515_pre_gradle_audited_runtime.sha256" "$OUT/26515_post_gradle_audited_runtime.sha256" || {
  diff -u "$OUT/26515_pre_gradle_audited_runtime.sha256" "$OUT/26515_post_gradle_audited_runtime.sha256" > "$OUT/26515_gradle_runtime_source_diff.txt" || true
  fail "Gradle mutated audited 26515 runtime source"
}
pass "Gradle preserved direct tested-26514 + validated 26515 runtime source"

mapfile -t APKS < <(find app/build -type f -name '*.apk' | sort)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one APK, found ${#APKS[@]}"
[[ "$(basename "${APKS[0]}")" == "IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-debug.apk" ]] || fail "unexpected APK identity $(basename "${APKS[0]}")"
rm -f "$FINAL"; cp "${APKS[0]}" "$FINAL"
sha256sum "$FINAL" > "$OUT/26515_APK.sha256"

# Emit the actual 26515 source snapshot for the NEXT direct incremental build.
rm -rf "$AFTER/app/src/main/cpp/third_party_26507"
( cd "$AFTER" && tar --sort=name --mtime='UTC 2026-08-20 00:00:00' --owner=0 --group=0 --numeric-owner \
    -czf "$OUT/26515_candidate_app_source.tar.gz" app/src/main app/version.properties )
( cd "$AFTER" && { find app/src/main -type f -print; echo app/version.properties; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done ) \
    > "$OUT/26515_candidate_source.sha256"
( cd "$AFTER" && sha256sum -c "$OUT/26515_candidate_source.sha256" ) > "$OUT/26515_candidate_source_manifest_check.txt"

cat >> "$OUT/26515_BASE_SOURCE_PROVENANCE.txt" <<EOF
FINAL_APK=$(basename "$FINAL")
FINAL_APK_SHA256=$(sha "$FINAL")
FINAL_SOURCE_TAR_SHA256=$(sha "$OUT/26515_candidate_app_source.tar.gz")
EOF

echo "=== 26515 V4 SUCCESS ==="
echo "APK: $(basename "$FINAL")"
echo "APK SHA256: $(sha "$FINAL")"
echo "BASE_26514_RUN_ID=$RUN_ID"
echo "BASE_26514_SOURCE_SHA256=$BASE_TAR_SHA"
pass "26515 built directly from tested 26514 artifact source + one validated Short/Bento exposure-domain delta"
