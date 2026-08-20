#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }

ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
SUCCESSFUL_26515_HEAD="01a53d2301dc32a246eba52e3d2e965f7a498cfd"
FAILED_26516_V1_HEAD="b4461c6c969fd56fee8f353bd58bc444cbb59aee"
FAILED_26516_V2_HEAD="5c527421dc312e998444e4a97683c032faff27ee"
BACKUP_26515="backup-26515-before-26516-profile-viewfinder-20260820"
BACKUP_26516_V1="backup-26516-v1-before-handoff-gate-fix-20260820"
BASE_WORKFLOW="build-26515-short-bento-domain.yml"
BASE_ARTIFACT="photon-26515-short-bento-domain-v4"
REPO="${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}"
BJZHOU_HEAD="09c76e57e8f01a5a8fc536ab41fc80ba642d4042"
BJZHOU_MANIFEST="$ROOT/26507_BJZHOU_NATIVE_DEPENDENCIES.sha256"
BJZHOU_COMMIT_FILE="$ROOT/26507_BJZHOU_DEPENDENCY_COMMIT.txt"
APPLY_26516="$ROOT/apply_26516_profile_viewfinder_match.py"
VALIDATE_26516="$ROOT/validate_26516_profile_viewfinder_match.py"
HANDOFF_26516="$ROOT/26516_HANDOFF_HASHES.sha256"
INERT_DERIVED="$ROOT/patch_26516_derived_builder.py"
OUT="$ROOT/build_26516_profile_viewfinder_match_outputs"
WORK="$ROOT/.build_26516_direct_26515_work"
ART="$WORK/26515_artifact"
BASE="$WORK/tested26515"
AFTER="$WORK/candidate26516"
BJ="$WORK/bjzhou1271_vendor"
VERSION_NAME="0.9726516"
VERSION_BUILD="26516"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-profile-viewfinder-match-debug.apk"

rm -rf "$OUT" "$WORK"; mkdir -p "$OUT" "$ART" "$BASE" "$AFTER"
exec > >(tee "$OUT/26516_build.log") 2>&1

echo "=== 26516 V3 GATE 0: exact successful-26515 runtime + failed-v1 handoff backup + direct-source-only handoff ==="
BRANCH="$(git branch --show-current)"; START_HEAD="$(git rev-parse HEAD)"
[[ "$BRANCH" == "$EXPECTED_BRANCH" && "$BRANCH" != "dev" ]] || fail "wrong/protected branch $BRANCH"
git merge-base --is-ancestor "$SUCCESSFUL_26515_HEAD" HEAD || fail "handoff is not descended from successful 26515 HEAD"
git merge-base --is-ancestor "$FAILED_26516_V1_HEAD" HEAD || fail "v3 correction is not descended from failed 26516 v1 handoff"
git merge-base --is-ancestor "$FAILED_26516_V2_HEAD" HEAD || fail "v3 correction is not descended from failed 26516 v2 handoff"
REMOTE_BACKUP="$(git ls-remote origin "refs/heads/$BACKUP_26515" | awk '{print $1}')"
[[ "$REMOTE_BACKUP" == "$SUCCESSFUL_26515_HEAD" ]] || fail "backup missing/wrong: $BACKUP_26515 -> ${REMOTE_BACKUP:-MISSING}; expected $SUCCESSFUL_26515_HEAD"
REMOTE_V1_BACKUP="$(git ls-remote origin "refs/heads/$BACKUP_26516_V1" | awk '{print $1}')"
[[ "$REMOTE_V1_BACKUP" == "$FAILED_26516_V1_HEAD" ]] || fail "v1 handoff backup missing/wrong: $BACKUP_26516_V1 -> ${REMOTE_V1_BACKUP:-MISSING}; expected $FAILED_26516_V1_HEAD"
for f in "$APPLY_26516" "$VALIDATE_26516" "$HANDOFF_26516" "$INERT_DERIVED" "$BJZHOU_MANIFEST" "$BJZHOU_COMMIT_FILE"; do
  [[ -f "$f" ]] || fail "missing $(basename "$f")"
done
sha256sum -c "$HANDOFF_26516"
python3 -m py_compile "$APPLY_26516" "$VALIDATE_26516"
grep -F 'DISABLED_26516_DIRECT_26515_SOURCE' "$INERT_DERIVED" >/dev/null || fail "direct-source tombstone missing"
[[ "$(tr -d '\r\n' < "$BJZHOU_COMMIT_FILE")" == "$BJZHOU_HEAD" ]] || fail "pinned bjzhou dependency commit drift"

# Handoff commits may add only scripts/docs/workflow; the actual runtime must still be the 26515 branch placeholder.
RUNTIME_DRIFT="$OUT/26516_committed_runtime_drift_after_26515.txt"
git diff --name-only "$SUCCESSFUL_26515_HEAD"..HEAD -- app/src/main app/version.properties > "$RUNTIME_DRIFT"
[[ ! -s "$RUNTIME_DRIFT" ]] || { cat "$RUNTIME_DRIFT" >&2; fail "committed runtime drift exists after successful 26515"; }
PROTECTED_DRIFT="$OUT/26516_protected_build_infrastructure_drift.txt"
git diff --name-only "$SUCCESSFUL_26515_HEAD"..HEAD -- \
  gradlew gradlew.bat gradle build.gradle settings.gradle gradle.properties \
  app/build.gradle app/proguard-rules.pro > "$PROTECTED_DRIFT"
[[ ! -s "$PROTECTED_DRIFT" ]] || { cat "$PROTECTED_DRIFT" >&2; fail "protected Gradle/build infrastructure drifted after successful 26515"; }

# Mechanical prohibition: only the emitted 26515 source artifact may construct runtime 26516.
python3 - "$0" <<'PYNOBACK'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text()
bad=(
    'build_'+'26512', 'apply_'+'26513', 'validate_'+'26513',
    'apply_'+'26514', 'validate_'+'26514',
    'apply_'+'26515', 'validate_'+'26515',
    'derived_from_exact_'+'26512', 'candidate'+'26512', 'golden'+'26513',
)
found=[x for x in bad if x in s]
if found:
    raise SystemExit('historical runtime constructor reference(s) found: '+', '.join(found))
print('PASS: no 26512-26515 runtime constructor invocation in 26516 builder')
PYNOBACK
pass "26515 runtime backup + existing v1 handoff backup verified; exact failed-v2 ancestry verified; no new backup required; no committed runtime/build drift"

echo "=== 26516 V3 GATE 1: recover and trust the ACTUAL manifest-verified source snapshot emitted by successful 26515 ==="
command -v gh >/dev/null || fail "GitHub CLI (gh) unavailable"
[[ -n "${GH_TOKEN:-}" ]] || fail "GH_TOKEN missing; Actions artifact cannot be authenticated"
RUN_JSON="$WORK/26515_runs.json"
gh run list --repo "$REPO" --workflow "$BASE_WORKFLOW" --branch "$EXPECTED_BRANCH" --status success \
  --limit 50 --json databaseId,headSha,conclusion,createdAt > "$RUN_JSON"
RUN_ID="$(python3 - "$RUN_JSON" "$SUCCESSFUL_26515_HEAD" <<'PYRUN'
import json,sys
runs=json.load(open(sys.argv[1])); head=sys.argv[2]
exact=[r for r in runs if r.get('headSha')==head and r.get('conclusion')=='success']
if not exact:
    raise SystemExit('no successful 26515 workflow run found at exact HEAD '+head)
print(exact[0]['databaseId'])
PYRUN
)"
[[ "$RUN_ID" =~ ^[0-9]+$ ]] || fail "invalid 26515 workflow run id: $RUN_ID"
gh run download "$RUN_ID" --repo "$REPO" --name "$BASE_ARTIFACT" --dir "$ART"
mapfile -t SOURCE_TARS < <(find "$ART" -type f -name '26515_candidate_app_source.tar.gz' -print)
mapfile -t SOURCE_MANIFESTS < <(find "$ART" -type f -name '26515_candidate_source.sha256' -print)
[[ "${#SOURCE_TARS[@]}" -eq 1 ]] || fail "expected one 26515 candidate source archive, found ${#SOURCE_TARS[@]}"
[[ "${#SOURCE_MANIFESTS[@]}" -eq 1 ]] || fail "expected one 26515 source manifest, found ${#SOURCE_MANIFESTS[@]}"
SOURCE_TAR="${SOURCE_TARS[0]}"; SOURCE_MANIFEST="${SOURCE_MANIFESTS[0]}"
BASE_TAR_SHA="$(sha "$SOURCE_TAR")"
SOURCE_MANIFEST_SHA="$(sha "$SOURCE_MANIFEST")"
python3 - "$SOURCE_TAR" <<'PYTAR'
import sys,tarfile
with tarfile.open(sys.argv[1],'r:gz') as t:
    names=[m.name.lstrip('./') for m in t.getmembers() if m.name not in ('.','./')]
for n in names:
    if not (n in {'app','app/','app/src','app/src/','app/src/main','app/src/main/','app/version.properties'} or n.startswith('app/src/main/')):
        raise SystemExit('unexpected path in tested-26515 source archive: '+n)
print('PASS: 26515 artifact source archive contains runtime source + version only')
PYTAR
tar -xzf "$SOURCE_TAR" -C "$BASE"
( cd "$BASE" && sha256sum -c "$SOURCE_MANIFEST" ) > "$OUT/26515_artifact_source_manifest_check.txt"
[[ "$(grep '^VERSION_NAME=' "$BASE/app/version.properties" | cut -d= -f2)" == "0.9726515" ]] || fail "artifact source is not version 0.9726515"
[[ "$(grep '^VERSION_BUILD=' "$BASE/app/version.properties" | cut -d= -f2)" == "26515" ]] || fail "artifact source is not build 26515"

# Direct-lineage invariants: these must be present in the actual 26515 source artifact.
grep -F 'IRIS_26513_RGB_DETAIL_SCALE_MULTIPLIER = 1.10f' "$BASE/app/src/main/java/com/hinnka/mycamera/processor/MgcSpatialMergeTuning.kt" >/dev/null || fail "26513 Spatial detail invariant missing"
grep -F 'IRIS_26514_MOTION_USER_CONTROLS_OWNER' "$BASE/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java" >/dev/null || fail "26514 controls owner missing"
grep -F 'IRIS_26515_SHORT_BASELINE_DOMAIN' "$BASE/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt" >/dev/null || fail "26515 Short/Bento domain marker missing"
grep -F 'parameters.motionV2MgcSourceExposureGain = baselineScale' "$BASE/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt" >/dev/null || fail "26515 source-domain owner missing"
grep -F 'parameters.motionV2DisplayGain = referenceDisplayGain' "$BASE/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt" >/dev/null || fail "expected 26515 pre-viewfinder display authority missing"
grep -F 'IRIS_26515_FUSED_LINEAR_SOURCE_RESTORE=true' "$BASE/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java" >/dev/null || fail "26515 fused source restore marker missing"
grep -F 'IRIS_26515_RENDER_EXPOSURE_AUTHORITY_SPLIT=true' "$BASE/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java" >/dev/null || fail "26515 render authority split missing"
grep -F 'IRIS_26514_OPTIONAL_LINEAR_PRESENTATION_CONTROLS' "$BASE/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java" >/dev/null || fail "26514 manual control graph missing"

# IRIS_26516_V3_ARTIFACT_CONTRACT_AUTHORITY
# The successful 26515 artifact + its own manifest are the sole byte authority. Do NOT compare
# artifact files to the repository placeholder app/src/main tree: successful 26515 intentionally
# built from its predecessor artifact and emitted a new source snapshot without committing runtime.
# Instead, dry-run the deterministic 26516 transform against the actual artifact source. Every
# changed-file anchor must resolve before any candidate write occurs. Record the exact artifact
# input hashes for provenance, but do not impose stale repository-derived hash expectations.
python3 - "$BASE" "$APPLY_26516" "$OUT/26516_BASE_CHANGED_INPUTS.sha256" <<'PYBASECOMPAT'
from __future__ import annotations
import hashlib, importlib.util, sys
from pathlib import Path
base=Path(sys.argv[1]).resolve(); script=Path(sys.argv[2]).resolve(); out=Path(sys.argv[3]).resolve()
spec=importlib.util.spec_from_file_location('iris26516apply_basecompat', script)
mod=importlib.util.module_from_spec(spec); assert spec.loader is not None; spec.loader.exec_module(mod)
lines=[]
for rel in sorted(mod.CHANGED):
    p=base/rel
    old=p.read_text() if p.is_file() else ''
    mod.expected_text(rel, old)  # pure in-memory compatibility proof; performs no write
    if p.is_file():
        lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {rel}")
out.write_text("\n".join(lines)+"\n")
print('PASS: semantic 26516 transform contracts resolve against actual manifest-verified 26515 artifact source')
print('PASS: repository-placeholder byte hashes are not used as 26515 runtime authority')
PYBASECOMPAT

cp -a "$BASE/." "$AFTER/"
cat > "$OUT/26516_BASE_SOURCE_PROVENANCE.txt" <<EOF
BASE_WORKFLOW=$BASE_WORKFLOW
BASE_ARTIFACT=$BASE_ARTIFACT
BASE_RUN_ID=$RUN_ID
BASE_HEAD=$SUCCESSFUL_26515_HEAD
BASE_SOURCE_TAR_SHA256=$BASE_TAR_SHA
BASE_SOURCE_MANIFEST_SHA256=$SOURCE_MANIFEST_SHA
BASE_VERSION=0.9726515/26515
EOF
pass "actual successful-26515 source snapshot recovered; manifest + deterministic-transform compatibility proven without repository-placeholder byte assumptions"

echo "=== 26516 V3 GATE 2: rollback patch FIRST; apply only profile/viewfinder delta; exact validator ==="
PATCH="$OUT/26516_RUNTIME_DELTA_FROM_TESTED_26515.patch"
PATCH_SHA="$OUT/26516_RUNTIME_DELTA_FROM_TESTED_26515.patch.sha256"
python3 "$APPLY_26516" "$AFTER" --patch-out "$PATCH" --patch-sha-out "$PATCH_SHA"
( cd "$OUT" && sha256sum -c "$(basename "$PATCH_SHA")" )
python3 "$VALIDATE_26516" --base "$BASE" --candidate "$AFTER" --apply-script "$APPLY_26516"

python3 - "$AFTER" <<'PYSOURCE'
from pathlib import Path
import sys
r=Path(sys.argv[1])
required=(
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2MgcSourceExposure.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionViewfinderMetering.java',
 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/GLPreview.java',
 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java',
 'app/src/main/assets/shaders/motionv2/color_transform.glsl',
 'app/src/main/assets/shaders/motionv2/display_exposure.glsl',
)
for rel in required:
    p=r/rel
    assert p.is_file() and p.stat().st_size>0,rel
print('PASS: all 26516 changed/new source files materialized')
PYSOURCE

echo "PRE-BUILD SAFETY PROOF PASSED"
pass "rollback/audit patch existed before writes; exact 26516 delta validated; capture/MGC/render frozen"

echo "=== 26516 V3 GATE 3: VERSION ${VERSION_NAME}/${VERSION_BUILD} + APK build in the SAME guarded block ==="
python3 - "$AFTER/app/version.properties" "$VERSION_NAME" "$VERSION_BUILD" <<'PYVER'
from pathlib import Path
import sys
p=Path(sys.argv[1]); vn=sys.argv[2]; vb=sys.argv[3]; s=p.read_text()
assert 'VERSION_NAME=0.9726515' in s and 'VERSION_BUILD=26515' in s
s=s.replace('VERSION_NAME=0.9726515','VERSION_NAME='+vn,1)
s=s.replace('VERSION_BUILD=26515','VERSION_BUILD='+vb,1)
p.write_text(s)
assert 'VERSION_NAME='+vn in p.read_text() and 'VERSION_BUILD='+vb in p.read_text()
PYVER

# Rehydrate only the same pinned vendor trees used by the successful 26515 procedure.
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
( cd "$THIRD" && sha256sum -c "$BJZHOU_MANIFEST" ) > "$OUT/26516_bjzhou_vendor_manifest_check.txt"
pass "same byte-verified pinned JPEG/UHDR vendor dependencies rehydrated; no historical Iris runtime reconstructed"

# Overlay exactly the tested-26515 source plus the validated 26516 delta.
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
audited_runtime_manifest > "$OUT/26516_pre_gradle_audited_runtime.sha256"
chmod +x ./gradlew
./gradlew clean :app:assembleDebug --stacktrace
assert_cpp_deps_exact post
audited_runtime_manifest > "$OUT/26516_post_gradle_audited_runtime.sha256"
cmp -s "$OUT/26516_pre_gradle_audited_runtime.sha256" "$OUT/26516_post_gradle_audited_runtime.sha256" || {
  diff -u "$OUT/26516_pre_gradle_audited_runtime.sha256" "$OUT/26516_post_gradle_audited_runtime.sha256" > "$OUT/26516_gradle_runtime_source_diff.txt" || true
  fail "Gradle mutated audited 26516 runtime source"
}
pass "Gradle preserved direct tested-26515 + validated 26516 runtime source"

mapfile -t APKS < <(find app/build -type f -name '*.apk' | sort)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one APK, found ${#APKS[@]}"
[[ "$(basename "${APKS[0]}")" == "IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-debug.apk" ]] || fail "unexpected APK identity $(basename "${APKS[0]}")"
rm -f "$FINAL"; cp "${APKS[0]}" "$FINAL"
sha256sum "$FINAL" > "$OUT/26516_APK.sha256"

# Emit the actual 26516 source snapshot for the NEXT direct incremental build.
rm -rf "$AFTER/app/src/main/cpp/third_party_26507"
( cd "$AFTER" && tar --sort=name --mtime='UTC 2026-08-20 00:00:00' --owner=0 --group=0 --numeric-owner \
    -czf "$OUT/26516_candidate_app_source.tar.gz" app/src/main app/version.properties )
( cd "$AFTER" && { find app/src/main -type f -print; echo app/version.properties; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done ) \
    > "$OUT/26516_candidate_source.sha256"
( cd "$AFTER" && sha256sum -c "$OUT/26516_candidate_source.sha256" ) > "$OUT/26516_candidate_source_manifest_check.txt"

cat >> "$OUT/26516_BASE_SOURCE_PROVENANCE.txt" <<EOF
FINAL_APK=$(basename "$FINAL")
FINAL_APK_SHA256=$(sha "$FINAL")
FINAL_SOURCE_TAR_SHA256=$(sha "$OUT/26516_candidate_app_source.tar.gz")
EOF

echo "=== 26516 V3 SUCCESS ==="
echo "APK: $(basename "$FINAL")"
echo "APK SHA256: $(sha "$FINAL")"
echo "BASE_26515_RUN_ID=$RUN_ID"
echo "BASE_26515_SOURCE_SHA256=$BASE_TAR_SHA"
pass "26516 built directly from successful 26515 artifact source + one validated profile/viewfinder architecture delta"
