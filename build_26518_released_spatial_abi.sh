#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
SUCCESSFUL_26517_HEAD="0807073b897c057e90f26f557c4b5455762dba70"
BACKUP_26517="backup-26517-before-26518-released-spatial-abi"
BASE_WORKFLOW="build-26517-released-spatial-viewfinder.yml"
BASE_ARTIFACT="photon-26517-released-spatial-viewfinder-v1"
REPO="${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}"
BJZHOU_VENDOR_HEAD="09c76e57e8f01a5a8fc536ab41fc80ba642d4042"
BJZHOU_MANIFEST="$ROOT/26507_BJZHOU_NATIVE_DEPENDENCIES.sha256"
BJZHOU_COMMIT_FILE="$ROOT/26507_BJZHOU_DEPENDENCY_COMMIT.txt"
RELEASE_SPATIAL_HEAD="c4ff5a3e99b5f9f6027ba1c038eb7cc850bb9b01"
RELEASE_STACKER_BLOB="24613918b7d830f19b573346ab02c9684e92eb6f"
APPLY="$ROOT/apply_26518_released_spatial_abi.py"
VALIDATE="$ROOT/validate_26518_released_spatial_abi.py"
HANDOFF="$ROOT/26518_HANDOFF_HASHES.sha256"
REF_FILE="$ROOT/26518_BJZHOU_RELEASE_SPATIAL_REF.txt"
OUT="$ROOT/build_26518_released_spatial_abi_outputs"
WORK="$ROOT/.build_26518_direct_26517_work"
ART="$WORK/26517_artifact"; BASE="$WORK/tested26517"; AFTER="$WORK/candidate26518"; REL="$WORK/bjzhou_released_1271_spatial"; BJ="$WORK/bjzhou_vendor"
VERSION_NAME="0.9726518"; VERSION_BUILD="26518"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-released-spatial-abi-debug.apk"
rm -rf "$OUT" "$WORK"; mkdir -p "$OUT" "$ART" "$BASE" "$AFTER"
exec > >(tee "$OUT/26518_build.log") 2>&1

echo "=== 26518 GATE 0: exact successful-26517 lineage + backup + handoff integrity ==="
BRANCH="$(git branch --show-current)"; START_HEAD="$(git rev-parse HEAD)"
[[ "$BRANCH" == "$EXPECTED_BRANCH" && "$BRANCH" != "dev" ]] || fail "wrong/protected branch $BRANCH"
git merge-base --is-ancestor "$SUCCESSFUL_26517_HEAD" HEAD || fail "26518 handoff is not descended from successful 26517"
REMOTE_BACKUP="$(git ls-remote origin "refs/heads/$BACKUP_26517" | awk '{print $1}')"
[[ "$REMOTE_BACKUP" == "$SUCCESSFUL_26517_HEAD" ]] || fail "backup missing/wrong: $BACKUP_26517 -> ${REMOTE_BACKUP:-MISSING}; expected $SUCCESSFUL_26517_HEAD"
for f in "$APPLY" "$VALIDATE" "$HANDOFF" "$REF_FILE" "$BJZHOU_MANIFEST" "$BJZHOU_COMMIT_FILE"; do [[ -f "$f" ]] || fail "missing $(basename "$f")"; done
sha256sum -c "$HANDOFF"; python3 -m py_compile "$APPLY" "$VALIDATE"; bash -n "$0"
[[ "$(tr -d '\r\n' < "$BJZHOU_COMMIT_FILE")" == "$BJZHOU_VENDOR_HEAD" ]] || fail "pinned vendor dependency commit drift"
grep -F "BJZHOU_RELEASE_SPATIAL_COMMIT=$RELEASE_SPATIAL_HEAD" "$REF_FILE" >/dev/null || fail "released Spatial commit manifest drift"
grep -F "GlesMgcRawSpatialStacker.kt_BLOB=$RELEASE_STACKER_BLOB" "$REF_FILE" >/dev/null || fail "released stacker blob manifest drift"
RUNTIME_DRIFT="$OUT/26518_committed_runtime_drift_after_26517.txt"
git diff --name-only "$SUCCESSFUL_26517_HEAD"..HEAD -- app/src/main app/version.properties > "$RUNTIME_DRIFT"
[[ ! -s "$RUNTIME_DRIFT" ]] || { cat "$RUNTIME_DRIFT" >&2; fail "committed runtime drift exists after successful 26517"; }
PROTECTED_DRIFT="$OUT/26518_protected_build_infrastructure_drift.txt"
git diff --name-only "$SUCCESSFUL_26517_HEAD"..HEAD -- gradlew gradlew.bat gradle build.gradle settings.gradle gradle.properties app/build.gradle app/proguard-rules.pro > "$PROTECTED_DRIFT"
[[ ! -s "$PROTECTED_DRIFT" ]] || { cat "$PROTECTED_DRIFT" >&2; fail "protected build infrastructure drifted after 26517"; }
pass "successful 26517 lineage + exact backup + handoff-only commit verified"

echo "=== 26518 GATE 1: recover ACTUAL successful-26517 source + re-prove exact c4ff owner ==="
command -v gh >/dev/null || fail "GitHub CLI (gh) unavailable"; [[ -n "${GH_TOKEN:-}" ]] || fail "GH_TOKEN missing"
RUN_JSON="$WORK/26517_runs.json"
gh run list --repo "$REPO" --workflow "$BASE_WORKFLOW" --branch "$EXPECTED_BRANCH" --status success --limit 50 --json databaseId,headSha,conclusion,createdAt > "$RUN_JSON"
RUN_ID="$(python3 - "$RUN_JSON" "$SUCCESSFUL_26517_HEAD" <<'PYRUN'
import json,sys
runs=json.load(open(sys.argv[1])); head=sys.argv[2]
exact=[r for r in runs if r.get('headSha')==head and r.get('conclusion')=='success']
if not exact: raise SystemExit('no successful 26517 workflow run found at exact HEAD '+head)
print(exact[0]['databaseId'])
PYRUN
)"
[[ "$RUN_ID" =~ ^[0-9]+$ ]] || fail "invalid 26517 run id: $RUN_ID"
gh run download "$RUN_ID" --repo "$REPO" --name "$BASE_ARTIFACT" --dir "$ART"
mapfile -t SOURCE_TARS < <(find "$ART" -type f -name '26517_candidate_app_source.tar.gz' -print)
mapfile -t SOURCE_MANIFESTS < <(find "$ART" -type f -name '26517_candidate_source.sha256' -print)
[[ "${#SOURCE_TARS[@]}" -eq 1 && "${#SOURCE_MANIFESTS[@]}" -eq 1 ]] || fail "26517 source artifact cardinality mismatch"
SOURCE_TAR="${SOURCE_TARS[0]}"; SOURCE_MANIFEST="${SOURCE_MANIFESTS[0]}"; BASE_TAR_SHA="$(sha "$SOURCE_TAR")"; SOURCE_MANIFEST_SHA="$(sha "$SOURCE_MANIFEST")"
python3 - "$SOURCE_TAR" <<'PYTAR'
import sys,tarfile
with tarfile.open(sys.argv[1],'r:gz') as t: names=[m.name.lstrip('./') for m in t.getmembers() if m.name not in ('.','./')]
for n in names:
    if not (n in {'app','app/','app/src','app/src/','app/src/main','app/src/main/','app/version.properties'} or n.startswith('app/src/main/')): raise SystemExit('unexpected path in 26517 source archive: '+n)
print('PASS: 26517 source archive contains runtime source + version only')
PYTAR
tar -xzf "$SOURCE_TAR" -C "$BASE"
( cd "$BASE" && sha256sum -c "$SOURCE_MANIFEST" ) > "$OUT/26517_artifact_source_manifest_check.txt"
[[ "$(grep '^VERSION_NAME=' "$BASE/app/version.properties"|cut -d= -f2)" == "0.9726517" && "$(grep '^VERSION_BUILD=' "$BASE/app/version.properties"|cut -d= -f2)" == "26517" ]] || fail "artifact source is not 0.9726517/26517"
grep -F 'IRIS_26517_SYMMETRIC_VIEWFINDER_PRESENTATION_SOLVER' "$BASE/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java" >/dev/null || fail "26517 symmetric matcher missing"
grep -F 'IRIS_26517_RELEASED_1271_SPATIAL_RGB_OWNER' "$BASE/app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt" >/dev/null || fail "26517 released route missing"
STACK="$BASE/app/src/main/java/com/hinnka/mycamera/processor/GlesMgc1271ReleasedSpatialStacker.kt"
BRIDGE="$BASE/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt"
grep -F 'private val guideWidth = max(1, width / 4)' "$STACK" >/dev/null || fail "released quarter-guide contract missing in successful 26517"
grep -F 'bayerKernelTuning.referenceSnr' "$STACK" >/dev/null || fail "c4ff referenceSnr computation missing"
! grep -F 'mgcDenoiseTuningSnr =' "$STACK" >/dev/null || fail "26517 unexpectedly already exports newer tuning SNR"
grep -F 'mgcDenoiseTuningSnr' "$BRIDGE" >/dev/null || fail "observed parity consumer missing from recovered bridge"
grep -F 'missing/malformed MGC tuning SNR' "$BRIDGE" >/dev/null || fail "observed 26517 parity failure anchor missing from recovered bridge"
# Preserve the exact failing requireParity source for audit; do not edit it.
python3 - "$BRIDGE" "$OUT/26517_bridge_parity_context.txt" <<'PYBR'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text().splitlines(); hits=[i for i,l in enumerate(s) if 'missing/malformed MGC tuning SNR' in l]
if len(hits)!=1: raise SystemExit('bridge tuning-SNR failure anchor cardinality='+str(len(hits)))
i=hits[0]; a=max(0,i-24); b=min(len(s),i+16); Path(sys.argv[2]).write_text('\n'.join(f'{n+1:5d}: {s[n]}' for n in range(a,b))+'\n')
print('PASS: captured exact successful-26517 bridge parity context without modifying bridge')
PYBR

rm -rf "$REL"; git init -q "$REL"; git -C "$REL" remote add origin https://github.com/bjzhou/PhotonCamera.git; git -C "$REL" config core.sparseCheckout true; mkdir -p "$REL/.git/info"
cat > "$REL/.git/info/sparse-checkout" <<'SPARSE'
/app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
/app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt
/app/build.gradle.kts
SPARSE
git -C "$REL" fetch --depth=1 origin "$RELEASE_SPATIAL_HEAD"; git -C "$REL" checkout -q --detach FETCH_HEAD
[[ "$(git -C "$REL" rev-parse HEAD)" == "$RELEASE_SPATIAL_HEAD" ]] || fail "released Spatial checkout drift"
[[ "$(git -C "$REL" rev-parse HEAD:app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt)" == "$RELEASE_STACKER_BLOB" ]] || fail "released stacker blob drift"
grep -F 'versionName = "1.27.1"' "$REL/app/build.gradle.kts" >/dev/null || fail "c4ff reference is not version 1.27.1"
grep -F 'private val guideWidth = max(1, width / 4)' "$REL/app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt" >/dev/null || fail "c4ff quarter-guide contract missing"
! grep -F 'MgcRawProcessorPipeline' "$REL/app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt" >/dev/null || fail "c4ff unexpectedly contains post-Sabre processor contract"
python3 - "$STACK" "$REL/app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt" <<'PYC4'
from pathlib import Path
import sys
built=Path(sys.argv[1]).read_text().replace('\r\n','\n'); up=Path(sys.argv[2]).read_text().replace('\r\n','\n')
up=up.replace('GlesMgcRawSpatialStacker','GlesMgc1271ReleasedSpatialStacker').replace('GlesMgcRawSpatialShaders','GlesMgc1271ReleasedSpatialShaders')
assert built==up, 'successful 26517 owner is not exact c4ff + symbol rename'
print('PASS: successful 26517 released stacker is exact c4ff with symbol renames only')
PYC4
cat > "$OUT/26518_BASE_SOURCE_PROVENANCE.txt" <<EOF
BASE_HEAD=$SUCCESSFUL_26517_HEAD
BASE_WORKFLOW=$BASE_WORKFLOW
BASE_ARTIFACT=$BASE_ARTIFACT
BASE_RUN_ID=$RUN_ID
BASE_SOURCE_TAR_SHA256=$BASE_TAR_SHA
BASE_SOURCE_MANIFEST_SHA256=$SOURCE_MANIFEST_SHA
RELEASE_SPATIAL_COMMIT=$RELEASE_SPATIAL_HEAD
RELEASE_STACKER_BLOB=$RELEASE_STACKER_BLOB
BACKUP_BRANCH=$BACKUP_26517
CHANGE=RESULT_ABI_ONLY_C4FF_REFERENCE_SNR_EXPORT
EOF
pass "actual successful 26517 runtime and exact c4ff SNR owner proven"

echo "=== 26518 GATE 2: patch FIRST; add result-ABI SNR export only; exact validator ==="
cp -a "$BASE/." "$AFTER/"
PATCH="$OUT/26518_RUNTIME_DELTA_FROM_TESTED_26517.patch"; PATCH_SHA="$OUT/26518_RUNTIME_DELTA_FROM_TESTED_26517.patch.sha256"
python3 "$APPLY" "$AFTER" --patch-out "$PATCH" --patch-sha-out "$PATCH_SHA"
( cd "$OUT" && sha256sum -c "$(basename "$PATCH_SHA")" )
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" --released-root "$REL" --apply-script "$APPLY" --patch "$PATCH" --patch-sha "$PATCH_SHA" | tee "$OUT/26518_prebuild_validator.txt"
[[ "$(grep '^VERSION_NAME=' "$AFTER/app/version.properties"|cut -d= -f2)" == "0.9726517" && "$(grep '^VERSION_BUILD=' "$AFTER/app/version.properties"|cut -d= -f2)" == "26517" ]] || fail "version changed before guarded build block"
echo "PRE-BUILD SAFETY PROOF PASSED"
pass "only released c4ff result ABI changed; bridge/routing/matcher/current-Sabre tree frozen"

echo "=== 26518 GATE 3: VERSION ${VERSION_NAME}/${VERSION_BUILD} + APK build in SAME guarded block ==="
python3 - "$AFTER/app/version.properties" "$VERSION_NAME" "$VERSION_BUILD" <<'PYVER'
from pathlib import Path
import sys
p=Path(sys.argv[1]); vn=sys.argv[2]; vb=sys.argv[3]; s=p.read_text(); assert 'VERSION_NAME=0.9726517' in s and 'VERSION_BUILD=26517' in s
s=s.replace('VERSION_NAME=0.9726517','VERSION_NAME='+vn,1).replace('VERSION_BUILD=26517','VERSION_BUILD='+vb,1); p.write_text(s)
PYVER
# Rehydrate exactly the same pinned JPEG/UHDR vendor trees used by successful 26517.
rm -rf "$BJ"; git init -q "$BJ"; git -C "$BJ" remote add origin https://github.com/bjzhou/PhotonCamera.git; git -C "$BJ" config core.sparseCheckout true; mkdir -p "$BJ/.git/info"
cat > "$BJ/.git/info/sparse-checkout" <<'SPARSE'
/app/src/main/cpp/libjpeg-turbo/
/app/src/main/cpp/libultrahdr/
SPARSE
git -C "$BJ" fetch --depth=1 origin "$BJZHOU_VENDOR_HEAD"; git -C "$BJ" checkout -q --detach FETCH_HEAD
[[ "$(git -C "$BJ" rev-parse HEAD)" == "$BJZHOU_VENDOR_HEAD" ]] || fail "pinned vendor checkout drift"
THIRD="$AFTER/app/src/main/cpp/third_party_26507"; rm -rf "$THIRD"; mkdir -p "$THIRD"; cp -a "$BJ/app/src/main/cpp/libjpeg-turbo" "$THIRD/libjpeg-turbo"; cp -a "$BJ/app/src/main/cpp/libultrahdr" "$THIRD/libultrahdr"
( cd "$THIRD" && sha256sum -c "$BJZHOU_MANIFEST" ) > "$OUT/26518_bjzhou_vendor_manifest_check.txt"
rm -rf app/src/main; cp -a "$AFTER/app/src/main" app/src/main; cp "$AFTER/app/version.properties" app/version.properties
assert_cpp_deps_exact(){ local phase="$1" expected actual; if [[ "$phase" == pre ]]; then expected=$'.gitignore'; else expected=$'.gitignore\narchive.h\narchive_entry.h\ntechnicallyflac.h\ntiny_dng_writer.h'; fi; actual="$(find app/src/main/cpp/deps -mindepth 1 -maxdepth 1 -type f -printf '%f\n'|LC_ALL=C sort)"; [[ "$actual" == "$expected" ]] || fail "unexpected app/src/main/cpp/deps contents ($phase)"; }
audited_runtime_manifest(){ { find app/src/main -type f ! -path 'app/src/main/cpp/third_party_26507/*' ! -path 'app/src/main/cpp/deps/*' -print; echo app/src/main/cpp/deps/.gitignore; echo app/version.properties; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done; }
assert_cpp_deps_exact pre; audited_runtime_manifest > "$OUT/26518_pre_gradle_audited_runtime.sha256"
chmod +x ./gradlew; ./gradlew clean :app:assembleDebug --stacktrace
assert_cpp_deps_exact post; audited_runtime_manifest > "$OUT/26518_post_gradle_audited_runtime.sha256"
cmp -s "$OUT/26518_pre_gradle_audited_runtime.sha256" "$OUT/26518_post_gradle_audited_runtime.sha256" || { diff -u "$OUT/26518_pre_gradle_audited_runtime.sha256" "$OUT/26518_post_gradle_audited_runtime.sha256" > "$OUT/26518_gradle_runtime_source_diff.txt" || true; fail "Gradle mutated audited 26518 runtime source"; }
pass "Gradle preserved validated 26518 runtime source"
mapfile -t APKS < <(find app/build -type f -name '*.apk'|sort); [[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one APK, found ${#APKS[@]}"
[[ "$(basename "${APKS[0]}")" == "IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-debug.apk" ]] || fail "unexpected APK identity $(basename "${APKS[0]}")"
rm -f "$FINAL"; cp "${APKS[0]}" "$FINAL"; sha256sum "$FINAL" > "$OUT/26518_APK.sha256"
rm -rf "$AFTER/app/src/main/cpp/third_party_26507"
( cd "$AFTER" && tar --sort=name --mtime='UTC 2026-08-20 00:00:00' --owner=0 --group=0 --numeric-owner -czf "$OUT/26518_candidate_app_source.tar.gz" app/src/main app/version.properties )
( cd "$AFTER" && { find app/src/main -type f -print; echo app/version.properties; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done ) > "$OUT/26518_candidate_source.sha256"
( cd "$AFTER" && sha256sum -c "$OUT/26518_candidate_source.sha256" ) > "$OUT/26518_candidate_source_manifest_check.txt"
cat >> "$OUT/26518_BASE_SOURCE_PROVENANCE.txt" <<EOF
FINAL_APK=$(basename "$FINAL")
FINAL_APK_SHA256=$(sha "$FINAL")
FINAL_SOURCE_TAR_SHA256=$(sha "$OUT/26518_candidate_app_source.tar.gz")
EOF
echo "=== 26518 SUCCESS ==="; echo "APK: $(basename "$FINAL")"; echo "APK SHA256: $(sha "$FINAL")"; echo "BASE_26517_RUN_ID=$RUN_ID"; echo "RELEASE_SPATIAL_HEAD=$RELEASE_SPATIAL_HEAD"
pass "26518 built directly from successful 26517 artifact; exact c4ff math retained; newer result ABI receives c4ff referenceSnr"
