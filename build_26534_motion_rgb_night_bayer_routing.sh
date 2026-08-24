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
BASE_V16_HANDOFF_HEAD="c6d6d74a38be68f31166d09162adb98a1d41923a"
BASE_V15_HEAD="10d1aa2c1a37adcfd36533ba4c3879046fd29c3e"
BASE_WORKFLOW="build-26533-v15-normalized16-rcd.yml"
BASE_ARTIFACT="photon-26533-v1-5-normalized16-rcd-domain"
BASE_SOURCE_TAR_NAME="26533_v15_candidate_app_source.tar.gz"
BASE_SOURCE_MANIFEST_NAME="26533_v15_candidate_source.sha256"
EXPECTED_BASE_TAR_SHA="2257efa438c2895fa0d516bcff7f6d9ececeff4ce24dafc0237eb1c82356a612"
EXPECTED_BASE_MANIFEST_SHA="8cf21915b0043a6bb4752e6bc184eb40481abec1e96e14e1008350a64b40b1f5"
EXPECTED_FILES=962
VERSION_NAME="0.9726534"; VERSION_BUILD="26534"
BJZHOU_VENDOR_HEAD="09c76e57e8f01a5a8fc536ab41fc80ba642d4042"
REPO="${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}"

APPLY="$ROOT/apply_26534_motion_rgb_night_bayer_routing.py"
VALIDATE="$ROOT/validate_26534_motion_rgb_night_bayer_routing.py"
SYNTAX="$ROOT/preflight_26534_changed_syntax.py"
HANDOFF="$ROOT/26534_HANDOFF_HASHES.sha256"
BASE_HEAD_FILE="$ROOT/26534_BASE_V16_HANDOFF_HEAD.txt"
BASE_V16_MANIFEST="$ROOT/26534_BASE_EXACT_V16_AUDITED_SOURCE.sha256"
BASE_V16_MANIFEST_SHA="$ROOT/26534_BASE_V16_SOURCE_MANIFEST_FILE.sha256"
BASE_V16_ANCHORS="$ROOT/26534_EXACT_V16_RUNTIME_ANCHORS.sha256"
CAND_ANCHORS="$ROOT/26534_EXPECTED_CANDIDATE_ANCHORS.sha256"
EXPECTED_PATCH="$ROOT/26534_RUNTIME_DELTA_FROM_V16.patch"
EXPECTED_PATCH_SHA="$ROOT/26534_RUNTIME_DELTA_FROM_V16.patch.sha256"
EXPECTED_ROLLBACK="$ROOT/26534_RUNTIME_ROLLBACK_TO_V16.patch"
EXPECTED_ROLLBACK_SHA="$ROOT/26534_RUNTIME_ROLLBACK_TO_V16.patch.sha256"

# Inherited exact V1.6 reconstruction and prior strict preflights.
V16_PATCH="$ROOT/26533_V16_RUNTIME_DELTA_FROM_V15.patch"
V16_PATCH_SHA="$ROOT/26533_V16_RUNTIME_DELTA_FROM_V15.patch.sha256"
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

OUT="$ROOT/build_26534_routing_restoration_outputs"
WORK="$ROOT/.build_26534_routing_restoration_work"
ART="$WORK/v15_artifact"
V15="$WORK/tested_v15"
V16="$WORK/exact_v16"
AFTER="$WORK/candidate_26534"
PATCHREPO="$WORK/patchrepo"
FORWARDCHECK="$WORK/forwardcheck"
ROLLBACKCHECK="$WORK/rollbackcheck"
BJ="$WORK/bjzhou_vendor"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-motion-spatial-rgb-night-spatial-bayer-debug.apk"
SOURCE_TAR_OUT="$OUT/26534_candidate_app_source.tar.gz"
SOURCE_MANIFEST_OUT="$OUT/26534_candidate_source.sha256"
RUNTIME_FILES=(
  app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java
  app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java
  app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightMgc1271Bridge.kt
)

rm -rf "$OUT" "$WORK" "$FINAL"
mkdir -p "$OUT" "$ART" "$V15" "$V16" "$AFTER"
find "$ROOT" -maxdepth 1 -type f -name 'IrisCamera-*-debug.apk' -delete
exec > >(tee "$OUT/26534_build.log") 2>&1

echo "=== 26534 GATE 0: exact tested V1.6 handoff lineage + handoff integrity ==="
BRANCH="$(git branch --show-current)"
[[ "$BRANCH" == "$EXPECTED_BRANCH" && "$BRANCH" != "dev" ]] || fail "wrong/protected branch: $BRANCH"
git merge-base --is-ancestor "$BASE_V16_HANDOFF_HEAD" HEAD || fail "handoff is not descended from tested V1.6 handoff"
[[ "$(tr -d '\r\n' < "$BASE_HEAD_FILE")" == "$BASE_V16_HANDOFF_HEAD" ]] || fail "V1.6 handoff HEAD contract drift"
for f in "$APPLY" "$VALIDATE" "$SYNTAX" "$HANDOFF" "$BASE_HEAD_FILE" "$BASE_V16_MANIFEST" "$BASE_V16_MANIFEST_SHA" \
  "$BASE_V16_ANCHORS" "$CAND_ANCHORS" "$EXPECTED_PATCH" "$EXPECTED_PATCH_SHA" "$EXPECTED_ROLLBACK" "$EXPECTED_ROLLBACK_SHA" \
  "$V16_PATCH" "$V16_PATCH_SHA" "$V16_PROVENANCE_PREFLIGHT" "$SHADER_PREFLIGHT" "$NATIVE_JPEG_PREFLIGHT" \
  "$JAVA_XML_PREFLIGHT" "$EMBEDDED_PREFLIGHT" "$INHERITED_SHADER_PREFLIGHT" "$KOTLIN_API_PREFLIGHT" \
  "$NATIVE_DNG_PREFLIGHT" "$DNG_TEST" "$BJZHOU_MANIFEST" "$BJZHOU_COMMIT_FILE"; do [[ -f "$f" ]] || fail "missing $(basename "$f")"; done
sha256sum -c "$HANDOFF"
sha256sum -c "$BASE_V16_MANIFEST_SHA"
sha256sum -c "$EXPECTED_PATCH_SHA"
sha256sum -c "$EXPECTED_ROLLBACK_SHA"
sha256sum -c "$V16_PATCH_SHA"
python3 -m py_compile "$APPLY" "$VALIDATE" "$SYNTAX" "$V16_PROVENANCE_PREFLIGHT" "$SHADER_PREFLIGHT" "$NATIVE_JPEG_PREFLIGHT" "$JAVA_XML_PREFLIGHT" \
  "$EMBEDDED_PREFLIGHT" "$INHERITED_SHADER_PREFLIGHT" "$KOTLIN_API_PREFLIGHT" "$NATIVE_DNG_PREFLIGHT" "$DNG_TEST"
python3 "$APPLY" --self-test
python3 "$VALIDATE" --self-test
bash -n "$0"
command -v gh >/dev/null || fail "GitHub CLI unavailable"
[[ -n "${GH_TOKEN:-}" ]] || fail "GH_TOKEN missing"
command -v glslangValidator >/dev/null || fail "glslangValidator unavailable"
glslangValidator --version | grep -F '16.5.0' >/dev/null || fail "wrong glslangValidator version"
[[ "$(tr -d '\r\n' < "$BJZHOU_COMMIT_FILE")" == "$BJZHOU_VENDOR_HEAD" ]] || fail "native dependency commit drift"
git diff --name-only "$BASE_V16_HANDOFF_HEAD"..HEAD -- app/src/main app/version.properties app/build.gradle > "$OUT/26534_committed_runtime_drift.txt"
[[ ! -s "$OUT/26534_committed_runtime_drift.txt" ]] || fail "committed runtime/build drift after V1.6 handoff"
# Exact inherited files used to reconstruct/build must remain the same objects as V1.6.
for rel in 26533_V16_RUNTIME_DELTA_FROM_V15.patch 26533_V16_RUNTIME_DELTA_FROM_V15.patch.sha256 \
  preflight_26533_v16_provenance_shader.py preflight_26532_iris_shaders.py preflight_26532_native_jpeg_syntax.py \
  preflight_26532_java_xml_syntax.py preflight_26529_iris_embedded_shaders_v3.py preflight_26526_inherited_shaders.py \
  preflight_26531_iris_kotlin_api_contracts.py preflight_26527_native_syntax.py test_26527_dng_subifd.py \
  26507_BJZHOU_NATIVE_DEPENDENCIES.sha256 26507_BJZHOU_DEPENDENCY_COMMIT.txt; do
  [[ "$(git hash-object "$rel")" == "$(git rev-parse "$BASE_V16_HANDOFF_HEAD:$rel")" ]] || fail "inherited proven file drift: $rel"
done
pass "exact V1.6 handoff lineage + new handoff integrity"

echo "=== 26534 GATE 1: recover actual successful V1.5 source and reconstruct exact tested V1.6 runtime ==="
RUN_JSON="$WORK/v15_runs.json"
gh run list --repo "$REPO" --workflow "$BASE_WORKFLOW" --branch "$EXPECTED_BRANCH" --status success --limit 50 --json databaseId,headSha,conclusion,createdAt > "$RUN_JSON"
RUN_ID="$(python3 - "$RUN_JSON" "$BASE_V15_HEAD" <<'PY'
import json,sys
runs=json.load(open(sys.argv[1])); head=sys.argv[2]
xs=[r for r in runs if r.get('headSha')==head and r.get('conclusion')=='success']
if not xs: raise SystemExit('no successful V1.5 workflow at exact HEAD '+head)
xs.sort(key=lambda r:r.get('createdAt',''),reverse=True)
print(xs[0]['databaseId'])
PY
)"
[[ "$RUN_ID" =~ ^[0-9]+$ ]] || fail "invalid V1.5 workflow run id"
echo "$RUN_ID" > "$OUT/26534_base_v15_successful_run_id.txt"
gh run download "$RUN_ID" --repo "$REPO" --name "$BASE_ARTIFACT" --dir "$ART"
mapfile -t SOURCE_TARS < <(find "$ART" -type f -name "$BASE_SOURCE_TAR_NAME" -print)
mapfile -t SOURCE_MANIFESTS < <(find "$ART" -type f -name "$BASE_SOURCE_MANIFEST_NAME" -print)
[[ "${#SOURCE_TARS[@]}" -eq 1 && "${#SOURCE_MANIFESTS[@]}" -eq 1 ]] || fail "V1.5 source artifact cardinality mismatch"
SOURCE_TAR="${SOURCE_TARS[0]}"; SOURCE_MANIFEST="${SOURCE_MANIFESTS[0]}"
[[ "$(sha "$SOURCE_TAR")" == "$EXPECTED_BASE_TAR_SHA" ]] || fail "V1.5 source tar SHA drift"
[[ "$(sha "$SOURCE_MANIFEST")" == "$EXPECTED_BASE_MANIFEST_SHA" ]] || fail "V1.5 source manifest SHA drift"
[[ "$(wc -l < "$SOURCE_MANIFEST")" -eq "$EXPECTED_FILES" ]] || fail "V1.5 source manifest count drift"
tar -xzf "$SOURCE_TAR" -C "$V15"
( cd "$V15" && sha256sum -c "$SOURCE_MANIFEST" ) > "$OUT/26534_base_v15_manifest_check.txt"
cp -a "$V15/." "$V16/"
patch -d "$V16" -p1 --batch --forward --fuzz=0 --no-backup-if-mismatch < "$V16_PATCH" >/dev/null
( cd "$V16" && sha256sum -c "$BASE_V16_MANIFEST" ) > "$OUT/26534_exact_v16_manifest_check.txt"
( cd "$V16" && sha256sum -c "$BASE_V16_ANCHORS" ) | tee "$OUT/26534_exact_v16_anchor_check.txt"
[[ "$(grep '^VERSION_NAME=' "$V16/app/version.properties" | cut -d= -f2)" == "0.9726533" ]] || fail "V1.6 reconstructed version mismatch"
[[ "$(grep '^VERSION_BUILD=' "$V16/app/version.properties" | cut -d= -f2)" == "26533" ]] || fail "V1.6 reconstructed build mismatch"
cp -a "$V16/." "$AFTER/"
pass "exact tested V1.6 runtime reconstructed from successful V1.5 + byte-exact V1.6 patch"

echo "=== 26534 GATE 2: guarded 4-file routing transform + backup/forward/rollback proof ==="
python3 "$APPLY" "$AFTER"
python3 "$VALIDATE" --base "$V16" --candidate "$AFTER" | tee "$OUT/26534_prebuild_validation.txt"
( cd "$AFTER" && sha256sum -c "$CAND_ANCHORS" ) | tee "$OUT/26534_candidate_anchor_check.txt"
python3 - "$V16" "$AFTER" "${RUNTIME_FILES[@]}" <<'PY' | tee "$OUT/26534_actual_changed_files.txt"
from pathlib import Path
import hashlib,sys
b=Path(sys.argv[1]); c=Path(sys.argv[2]); expected=sorted(sys.argv[3:])
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def m(root):
 d={}
 for top in ('app/src/main','app/version.properties','app/build.gradle'):
  p=root/top
  if p.is_file(): d[top]=h(p)
  else:
   for f in p.rglob('*'):
    if not f.is_file(): continue
    rel=str(f.relative_to(root))
    if rel.startswith('app/src/main/cpp/third_party_26507/'): continue
    if rel.startswith('app/src/main/cpp/deps/') and rel!='app/src/main/cpp/deps/.gitignore': continue
    d[rel]=h(f)
 return d
mb,mc=m(b),m(c); changed=sorted(k for k in set(mb)|set(mc) if mb.get(k)!=mc.get(k))
if changed!=expected: raise SystemExit('26534 changed-file allowlist mismatch: '+repr(changed))
print('\n'.join(changed))
PY
rm -rf "$PATCHREPO"; cp -a "$V16" "$PATCHREPO"
(
 cd "$PATCHREPO"; git init -q; git config user.email iris26534@example.invalid; git config user.name Iris26534
 git add app/src/main app/version.properties app/build.gradle; git commit -qm exact-v16
 git branch backup-26533-v16-before-26534
 git format-patch -1 --stdout HEAD > "$OUT/26534_prechange_v16_backup_branch.patch"
 for rel in "${RUNTIME_FILES[@]}"; do cp "$AFTER/$rel" "$rel"; done
 git diff --binary --no-ext-diff -- app/src/main > "$OUT/26534_regenerated_forward.patch"
 git diff --binary --no-ext-diff -R -- app/src/main > "$OUT/26534_regenerated_rollback.patch"
)
cmp -s "$OUT/26534_regenerated_forward.patch" "$EXPECTED_PATCH" || fail "regenerated 26534 forward patch differs"
cmp -s "$OUT/26534_regenerated_rollback.patch" "$EXPECTED_ROLLBACK" || fail "regenerated 26534 rollback patch differs"
rm -rf "$FORWARDCHECK"; cp -a "$V16" "$FORWARDCHECK"
patch -d "$FORWARDCHECK" -p1 --batch --forward --fuzz=0 --no-backup-if-mismatch < "$EXPECTED_PATCH" >/dev/null
manifest_all "$AFTER" "$OUT/26534_candidate_preversion.sha256"; manifest_all "$FORWARDCHECK" "$OUT/26534_forwardcheck.sha256"
cmp -s "$OUT/26534_candidate_preversion.sha256" "$OUT/26534_forwardcheck.sha256" || fail "forward patch does not reproduce 26534"
rm -rf "$ROLLBACKCHECK"; cp -a "$AFTER" "$ROLLBACKCHECK"
patch -d "$ROLLBACKCHECK" -p1 --batch --forward --fuzz=0 --no-backup-if-mismatch < "$EXPECTED_ROLLBACK" >/dev/null
manifest_all "$V16" "$OUT/26534_v16_for_rollback.sha256"; manifest_all "$ROLLBACKCHECK" "$OUT/26534_rollbackcheck.sha256"
cmp -s "$OUT/26534_v16_for_rollback.sha256" "$OUT/26534_rollbackcheck.sha256" || fail "rollback does not restore exact V1.6"
pass "local backup branch + 4-file forward/rollback proof exact"

echo "=== 26534 GATE 3: routing contracts + inherited shader/API/native/DNG preflights ==="
python3 "$SYNTAX" --root "$AFTER" | tee "$OUT/26534_changed_syntax_preflight.txt"
python3 "$V16_PROVENANCE_PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26534_v16_provenance_shader_preflight.txt"
python3 "$SHADER_PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26534_shader_preflight.txt"
python3 "$EMBEDDED_PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26534_embedded_shader_preflight.txt"
python3 "$INHERITED_SHADER_PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26534_inherited_shader_preflight.txt"
python3 "$KOTLIN_API_PREFLIGHT" --root "$AFTER" | tee "$OUT/26534_kotlin_api_preflight.txt"
python3 "$NATIVE_DNG_PREFLIGHT" --root "$AFTER" | tee "$OUT/26534_dng_native_preflight.txt"
python3 "$NATIVE_JPEG_PREFLIGHT" --root "$AFTER" | tee "$OUT/26534_native_jpeg_preflight.txt"
python3 "$JAVA_XML_PREFLIGHT" --root "$AFTER" | tee "$OUT/26534_java_xml_preflight.txt"
python3 "$DNG_TEST" --root "$AFTER" | tee "$OUT/26534_dng_subifd_preflight.txt"
python3 "$VALIDATE" --base "$V16" --candidate "$AFTER" | tee "$OUT/26534_routing_contract_preflight.txt"
echo "PRE-BUILD SAFETY PROOF PASSED"
pass "Motion/Night producer-consumer contracts + inherited safety proof"

echo "=== 26534 GATE 4: increment build ID + exact native restore + compile/assemble in SAME guarded block ==="
{
 sed -i "s/^VERSION_NAME=.*/VERSION_NAME=$VERSION_NAME/; s/^VERSION_BUILD=.*/VERSION_BUILD=$VERSION_BUILD/" "$AFTER/app/version.properties"
 [[ "$(grep '^VERSION_NAME=' "$AFTER/app/version.properties" | cut -d= -f2)" == "$VERSION_NAME" ]] || fail "version increment failed"
 [[ "$(grep '^VERSION_BUILD=' "$AFTER/app/version.properties" | cut -d= -f2)" == "$VERSION_BUILD" ]] || fail "build increment failed"
 python3 "$VALIDATE" --base "$V16" --candidate "$AFTER" | tee "$OUT/26534_versioned_validation.txt"
 manifest_audited_live "$AFTER" "$OUT/26534_pre_gradle_audited_runtime.sha256"
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
 ( cd "$THIRD" && sha256sum -c "$BJZHOU_MANIFEST" ) > "$OUT/26534_vendor_manifest_prebuild.txt"
 rm -rf "$ROOT/app/src/main"; mkdir -p "$ROOT/app/src"
 cp -a "$AFTER/app/src/main" "$ROOT/app/src/"; cp "$AFTER/app/version.properties" "$ROOT/app/version.properties"; cp "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"
 assert_cpp_deps_exact(){ local root="$1" phase="$2" expected actual; if [[ "$phase" == pre ]]; then expected=$'.gitignore'; else expected=$'.gitignore\narchive.h\narchive_entry.h\ntechnicallyflac.h\ntiny_dng_writer.h'; fi; actual="$(find "$root/app/src/main/cpp/deps" -mindepth 1 -maxdepth 1 -type f -printf '%f\n' | LC_ALL=C sort)"; [[ "$actual" == "$expected" ]] || fail "unexpected cpp/deps ($phase): [$actual]"; }
 assert_cpp_deps_exact "$ROOT" pre
 manifest_audited_live "$ROOT" "$OUT/26534_installed_pre_gradle_audited_runtime.sha256"
 cmp -s "$OUT/26534_pre_gradle_audited_runtime.sha256" "$OUT/26534_installed_pre_gradle_audited_runtime.sha256" || fail "installed candidate drift before Gradle"
 (cd "$ROOT/app/src/main/cpp/third_party_26507" && sha256sum -c "$BJZHOU_MANIFEST") > "$OUT/26534_installed_vendor_manifest_prebuild.txt"
 chmod +x ./gradlew
 ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace
 pass "real Android Kotlin + Java compile gates passed"
 ./gradlew :app:assembleDebug --stacktrace
 pass "assembleDebug passed"
}

echo "=== 26534 GATE 5: post-build exact source/native/routing revalidation ==="
assert_cpp_deps_exact "$ROOT" post
manifest_audited_live "$ROOT" "$OUT/26534_post_gradle_audited_runtime.sha256"
cmp -s "$OUT/26534_pre_gradle_audited_runtime.sha256" "$OUT/26534_post_gradle_audited_runtime.sha256" || fail "Gradle mutated audited source"
(cd "$ROOT/app/src/main/cpp/third_party_26507" && sha256sum -c "$BJZHOU_MANIFEST") > "$OUT/26534_postbuild_native_dependency_manifest_check.txt"
python3 "$VALIDATE" --base "$V16" --candidate "$ROOT" | tee "$OUT/26534_postbuild_routing_validation.txt"
python3 "$JAVA_XML_PREFLIGHT" --root "$ROOT" | tee "$OUT/26534_postbuild_java_xml_preflight.txt"
python3 "$NATIVE_JPEG_PREFLIGHT" --root "$ROOT" | tee "$OUT/26534_postbuild_native_jpeg_preflight.txt"
pass "post-build source/native/routing contracts remained exact"

echo "=== 26534 GATE 6: exactly one APK + deterministic next candidate ==="
mapfile -t BUILT_APKS < <(find "$ROOT/app/build/outputs/apk" -type f -name '*.apk' -print 2>/dev/null)
[[ "${#BUILT_APKS[@]}" -eq 1 ]] || fail "expected exactly one Gradle APK, found ${#BUILT_APKS[@]}"
cp "${BUILT_APKS[0]}" "$FINAL"; find "$ROOT/app/build" -type f -name '*.apk' -delete
[[ -f "$FINAL" ]] || fail "final APK missing"
[[ "$(find "$ROOT" -maxdepth 1 -type f -name '*.apk' | wc -l)" -eq 1 ]] || fail "root APK count is not exactly one"
sha256sum "$FINAL" > "$OUT/26534_APK.sha256"
rm -rf "$AFTER/app/src/main/cpp/third_party_26507"
manifest_all "$AFTER" "$SOURCE_MANIFEST_OUT"
[[ "$(wc -l < "$SOURCE_MANIFEST_OUT")" -eq "$EXPECTED_FILES" ]] || fail "26534 candidate file count drift"
( cd "$AFTER" && tar --sort=name --mtime='UTC 2026-08-24 00:00:00' --owner=0 --group=0 --numeric-owner -czf "$SOURCE_TAR_OUT" app/src/main app/version.properties app/build.gradle )
sha256sum "$SOURCE_TAR_OUT" > "$OUT/26534_candidate_app_source.tar.gz.sha256"
sha256sum "$SOURCE_MANIFEST_OUT" > "$OUT/26534_candidate_source_manifest_file.sha256"
cat > "$OUT/26534_SCOPE_PROVENANCE.txt" <<EOF
BASE_BRANCH=$EXPECTED_BRANCH
BASE_TESTED_V16_HANDOFF_HEAD=$BASE_V16_HANDOFF_HEAD
BASE_SUCCESSFUL_V15_HEAD=$BASE_V15_HEAD
BASE_SUCCESSFUL_V15_RUN_ID=$RUN_ID
TARGET_VERSION=$VERSION_NAME
TARGET_BUILD=$VERSION_BUILD
RUNTIME_DELTA_FILES=4
MOTION_PRODUCTION=MGC_SPATIAL_RGB_RGBA32F
MOTION_DNG_SIDECAR_AS_JPEG=false
MOTION_RCD_REDEMOSAIC=false
MOTION_PRESENTATION_CHAIN_PRESERVED=true
NIGHT_PRODUCTION=MGC_SPATIAL_BAYER_R16UI_TO_RCD_TO_JIN
NIGHT_EXPECTED_LAYOUT=CFA
NIGHT_EXPECTS_GPU_BAYER=true
NIGHT_EXPECTS_GPU_RGB=false
NIGHT_SUPER_RES_SECONDARY_EVIDENCE_ONLY=true
NIGHT_EXACT_TIMESTAMP_METADATA_PRESERVED=true
NIGHT_SESSION_STATE_RECOVERY=true
BENTO_REJECTION_UNCHANGED=true
MGC_SPATIAL_RGB_OWNER_UNCHANGED=true
SUPER_RES_OWNER_UNCHANGED=true
DNG_WRITERS_UNCHANGED=true
ULTRAHDR_UNCHANGED=true
JIN_MODEL_UNCHANGED=true
EOF

echo "PASS: 26534 MOTION SPATIAL-RGB / NIGHT SPATIAL-BAYER ROUTING RESTORATION"
echo "PASS: 26534 COMPILE + ASSEMBLE + POSTBUILD ROUTING CONTRACTS"
echo "PASS: 26534 EXACT V1.6 LINEAGE + 4-FILE DELTA + ONE APK"
