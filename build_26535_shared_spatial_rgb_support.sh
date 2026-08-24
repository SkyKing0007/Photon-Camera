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
STRICT_26534_HANDOFF_HEAD="74ba3685f856a2240c4e5eb7224aeb53d8a1c2ee"
BASE_ARTIFACT="photon-26534-v2-motion-spatial-rgb-night-spatial-bayer"
BASE_TAR_REL="build_26534_routing_restoration_outputs/26534_candidate_app_source.tar.gz"
BASE_MANIFEST_REL="build_26534_routing_restoration_outputs/26534_candidate_source.sha256"
EXPECTED_BASE_TAR_SHA="a595fe6e78a96004a4631d6e6e03bae23c7d3cabd02b7e89fab1a177b324a58c"
EXPECTED_BASE_MANIFEST_SHA="5ea3fce04fd92a0dc89a677f9ecbfabbb76060949e09e9e4b7e1209011c9b055"
EXPECTED_BASE_FILES=962
EXPECTED_CANDIDATE_FILES=964
VERSION_NAME="0.9726535"; VERSION_BUILD="26535"
BJZHOU_VENDOR_HEAD="09c76e57e8f01a5a8fc536ab41fc80ba642d4042"
REPO="${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
[[ -n "$TOKEN" ]] || fail "GitHub token unavailable for exact successful 26534 artifact recovery"

APPLY="$ROOT/apply_26535_shared_spatial_rgb_support.py"
VALIDATE="$ROOT/validate_26535_shared_spatial_rgb_support.py"
SYNTAX="$ROOT/preflight_26535_changed_syntax.py"
CHROMA_SHADER="$ROOT/preflight_26535_highlight_chroma_shader.py"
OVERLAY="$ROOT/26535_runtime_overlay"
HANDOFF="$ROOT/26535_HANDOFF_HASHES.sha256"
BASE_MANIFEST_PIN="$ROOT/26535_BASE_26534_CANDIDATE_SOURCE.sha256"
BASE_MANIFEST_PIN_SHA="$ROOT/26535_BASE_26534_CANDIDATE_SOURCE_FILE.sha256"
BASE_HEAD_FILE="$ROOT/26535_BASE_26534_HANDOFF_HEAD.txt"
PROTECTED="$ROOT/26535_PROTECTED_26534_RUNTIME_ANCHORS.sha256"
OVERLAY_HASHES="$ROOT/26535_RUNTIME_OVERLAY.sha256"
EXPECTED_PATCH="$ROOT/26535_RUNTIME_DELTA_FROM_26534.patch"
EXPECTED_PATCH_SHA="$ROOT/26535_RUNTIME_DELTA_FROM_26534.patch.sha256"
EXPECTED_ROLLBACK="$ROOT/26535_RUNTIME_ROLLBACK_TO_26534.patch"
EXPECTED_ROLLBACK_SHA="$ROOT/26535_RUNTIME_ROLLBACK_TO_26534.patch.sha256"

# Exact inherited checks retained from the successful 26533/26534 procedure.
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

OUT="$ROOT/build_26535_shared_spatial_rgb_support_outputs"
WORK="$ROOT/.build_26535_shared_spatial_rgb_support_work"
ART="$WORK/26534_artifact"
BASE="$WORK/exact_successful_26534"
AFTER="$WORK/candidate_26535"
PATCHREPO="$WORK/patchrepo"
FORWARDCHECK="$WORK/forwardcheck"
ROLLBACKCHECK="$WORK/rollbackcheck"
BJ="$WORK/bjzhou_vendor"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-shared-spatial-rgb-support-guard-debug.apk"
SOURCE_TAR_OUT="$OUT/26535_candidate_app_source.tar.gz"
SOURCE_MANIFEST_OUT="$OUT/26535_candidate_source.sha256"
RUNTIME_FILES=(
  app/src/main/assets/shaders/motionv2/highlight_chroma_reliability.glsl
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2HighlightChromaReliability.java
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2MgcSourceExposure.java
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java
  app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java
  app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt
  app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java
  app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java
)

rm -rf "$OUT" "$WORK" "$FINAL"; mkdir -p "$OUT" "$WORK"

echo "=== 26535 GATE 0: exact branch/strict-handoff/handoff integrity ==="
[[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch: $(git branch --show-current)"
[[ "$(cat "$BASE_HEAD_FILE")" == "$STRICT_26534_HANDOFF_HEAD" ]] || fail "26534 strict handoff head pin drift"
git merge-base --is-ancestor "$STRICT_26534_HANDOFF_HEAD" HEAD || fail "current handoff is not descended from strict successful-26534 handoff"
sha256sum -c "$HANDOFF"
sha256sum -c "$BASE_MANIFEST_PIN_SHA"
sha256sum -c "$EXPECTED_PATCH_SHA"
sha256sum -c "$EXPECTED_ROLLBACK_SHA"
(cd "$ROOT" && sha256sum -c "$OVERLAY_HASHES")
for f in "$APPLY" "$VALIDATE" "$SYNTAX" "$CHROMA_SHADER" "$V16_PROVENANCE_PREFLIGHT" "$SHADER_PREFLIGHT" "$NATIVE_JPEG_PREFLIGHT" "$JAVA_XML_PREFLIGHT" "$EMBEDDED_PREFLIGHT" "$INHERITED_SHADER_PREFLIGHT" "$KOTLIN_API_PREFLIGHT" "$NATIVE_DNG_PREFLIGHT" "$DNG_TEST" "$BJZHOU_MANIFEST" "$BJZHOU_COMMIT_FILE"; do [[ -f "$f" ]] || fail "required inherited safety file missing: $f"; done
[[ "$(cat "$BJZHOU_COMMIT_FILE" | tr -d '\r\n')" == "$BJZHOU_VENDOR_HEAD" ]] || fail "bjzhou native dependency pin drift"
! grep -E 'git push|git switch dev|git checkout dev' "$0" >/dev/null || fail "forbidden push/dev command in build script"
pass "exact experimental-clean-photon-rebuild lineage + strict handoff integrity"

echo "=== 26535 GATE 1: recover exact successful 26534 artifact candidate; repo app/src is NOT authority ==="
rm -rf "$ART" "$BASE"; mkdir -p "$ART" "$BASE"
JSON="$WORK/artifacts.json"
curl --fail --location --silent --show-error --retry 5 \
  -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$REPO/actions/artifacts?name=$BASE_ARTIFACT&per_page=100" -o "$JSON"
python3 - "$JSON" "$WORK/artifact_selection.txt" <<'PY'
import json,sys
j=json.load(open(sys.argv[1])); xs=[a for a in j.get('artifacts',[]) if not a.get('expired',False)]
if not xs: raise SystemExit('no unexpired exact 26534 artifact named '+str(j))
xs.sort(key=lambda a:a.get('created_at',''),reverse=True)
a=xs[0]
open(sys.argv[2],'w').write(f"artifact_id={a['id']}\ncreated_at={a.get('created_at')}\nhead_sha={a.get('workflow_run',{}).get('head_sha')}\n")
print(a['id'])
PY
ART_ID="$(head -1 "$WORK/artifact_selection.txt" | cut -d= -f2)"
[[ -n "$ART_ID" ]] || fail "failed to select successful 26534 artifact"
ZIP="$WORK/26534_artifact.zip"
curl --fail --location --silent --show-error --retry 5 \
  -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$REPO/actions/artifacts/$ART_ID/zip" -o "$ZIP"
unzip -q "$ZIP" -d "$ART"
[[ -f "$ART/$BASE_TAR_REL" && -f "$ART/$BASE_MANIFEST_REL" ]] || fail "selected 26534 artifact lacks successful candidate proof bundle"
[[ "$(sha "$ART/$BASE_TAR_REL")" == "$EXPECTED_BASE_TAR_SHA" ]] || fail "26534 candidate TAR hash mismatch"
[[ "$(sha "$ART/$BASE_MANIFEST_REL")" == "$EXPECTED_BASE_MANIFEST_SHA" ]] || fail "26534 candidate manifest-file hash mismatch"
cmp -s "$ART/$BASE_MANIFEST_REL" "$BASE_MANIFEST_PIN" || fail "downloaded 26534 source manifest differs from user-tested artifact authority"
tar -xzf "$ART/$BASE_TAR_REL" -C "$BASE"
(cd "$BASE" && sha256sum -c "$BASE_MANIFEST_PIN") > "$OUT/26535_base_26534_manifest_check.txt"
[[ "$(wc -l < "$BASE_MANIFEST_PIN")" -eq "$EXPECTED_BASE_FILES" ]] || fail "base candidate manifest file count drift"
[[ "$(grep '^VERSION_NAME=' "$BASE/app/version.properties" | cut -d= -f2)" == "0.9726534" ]] || fail "base version name is not 0.9726534"
[[ "$(grep '^VERSION_BUILD=' "$BASE/app/version.properties" | cut -d= -f2)" == "26534" ]] || fail "base build is not 26534"
(cd "$BASE" && sha256sum -c "$PROTECTED") > "$OUT/26535_base_protected_anchor_check.txt"
cp "$WORK/artifact_selection.txt" "$OUT/26535_base_artifact_selection.txt"
pass "exact successful 26534 artifact source recovered and verified 962/962"

echo "=== 26535 GATE 2: transform + exact git diff/git diff -R + zero-fuzz forward/rollback ==="
rm -rf "$AFTER"; cp -a "$BASE" "$AFTER"
python3 "$APPLY" "$AFTER" --overlay "$OVERLAY"
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" | tee "$OUT/26535_prebuild_validation.txt"
python3 - "$BASE" "$AFTER" "${RUNTIME_FILES[@]}" <<'PY' > "$OUT/26535_actual_changed_files.txt"
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
if changed!=expected: raise SystemExit('26535 changed-file allowlist mismatch: '+repr(changed))
print('\n'.join(changed))
PY
rm -rf "$PATCHREPO"; cp -a "$BASE" "$PATCHREPO"
(
 cd "$PATCHREPO"; git init -q; git config user.email iris26535@example.invalid; git config user.name Iris26535
 git add app/src/main app/version.properties app/build.gradle; git add -f app/src/main/cpp/deps/.gitignore; git commit -qm exact-successful-26534
 git branch backup-26534-before-26535
 for rel in "${RUNTIME_FILES[@]}"; do mkdir -p "$(dirname "$rel")"; cp "$AFTER/$rel" "$rel"; done
 git add -N app/src/main/assets/shaders/motionv2/highlight_chroma_reliability.glsl app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2HighlightChromaReliability.java
 git diff --binary --no-ext-diff -- app/src/main > "$OUT/26535_regenerated_forward.patch"
 git diff --binary --no-ext-diff -R -- app/src/main > "$OUT/26535_regenerated_rollback.patch"
 git format-patch -1 --stdout HEAD > "$OUT/26535_prechange_26534_backup_branch.patch"
)
cmp -s "$OUT/26535_regenerated_forward.patch" "$EXPECTED_PATCH" || fail "regenerated 26535 forward patch differs"
cmp -s "$OUT/26535_regenerated_rollback.patch" "$EXPECTED_ROLLBACK" || fail "regenerated 26535 rollback patch differs"
rm -rf "$FORWARDCHECK"; cp -a "$BASE" "$FORWARDCHECK"
patch -d "$FORWARDCHECK" -p1 --batch --forward --fuzz=0 --no-backup-if-mismatch < "$EXPECTED_PATCH" >/dev/null
manifest_all "$AFTER" "$OUT/26535_candidate_preversion.sha256"; manifest_all "$FORWARDCHECK" "$OUT/26535_forwardcheck.sha256"
cmp -s "$OUT/26535_candidate_preversion.sha256" "$OUT/26535_forwardcheck.sha256" || fail "forward patch does not reproduce exact 26535"
rm -rf "$ROLLBACKCHECK"; cp -a "$AFTER" "$ROLLBACKCHECK"
patch -d "$ROLLBACKCHECK" -p1 --batch --forward --fuzz=0 --no-backup-if-mismatch < "$EXPECTED_ROLLBACK" >/dev/null
manifest_all "$BASE" "$OUT/26535_base_for_rollback.sha256"; manifest_all "$ROLLBACKCHECK" "$OUT/26535_rollbackcheck.sha256"
cmp -s "$OUT/26535_base_for_rollback.sha256" "$OUT/26535_rollbackcheck.sha256" || fail "rollback does not restore exact successful 26534"
pass "backup branch + exact 8-file forward/rollback proof; fuzz=0 both directions"

echo "=== 26535 GATE 3: changed syntax/shader + inherited shader/API/native/DNG preflights ==="
python3 "$SYNTAX" --root "$AFTER" | tee "$OUT/26535_changed_syntax_preflight.txt"
python3 "$CHROMA_SHADER" --root "$AFTER" --validator glslangValidator | tee "$OUT/26535_highlight_chroma_shader_preflight.txt"
python3 "$V16_PROVENANCE_PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26535_v16_provenance_shader_preflight.txt"
python3 "$SHADER_PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26535_shader_preflight.txt"
python3 "$EMBEDDED_PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26535_embedded_shader_preflight.txt"
python3 "$INHERITED_SHADER_PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26535_inherited_shader_preflight.txt"
python3 "$KOTLIN_API_PREFLIGHT" --root "$AFTER" | tee "$OUT/26535_kotlin_api_preflight.txt"
python3 "$NATIVE_DNG_PREFLIGHT" --root "$AFTER" | tee "$OUT/26535_dng_native_preflight.txt"
python3 "$NATIVE_JPEG_PREFLIGHT" --root "$AFTER" | tee "$OUT/26535_native_jpeg_preflight.txt"
python3 "$JAVA_XML_PREFLIGHT" --root "$AFTER" | tee "$OUT/26535_java_xml_preflight.txt"
python3 "$DNG_TEST" --root "$AFTER" | tee "$OUT/26535_dng_subifd_preflight.txt"
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" | tee "$OUT/26535_architecture_contract_preflight.txt"
echo "PRE-BUILD SAFETY PROOF PASSED"
pass "shared Spatial-RGB + support/SR/highlight contracts and inherited safety proof"

echo "=== 26535 GATE 4: increment build ID + exact native restore + compile/assemble in SAME guarded block ==="
{
 sed -i "s/^VERSION_NAME=.*/VERSION_NAME=$VERSION_NAME/; s/^VERSION_BUILD=.*/VERSION_BUILD=$VERSION_BUILD/" "$AFTER/app/version.properties"
 [[ "$(grep '^VERSION_NAME=' "$AFTER/app/version.properties" | cut -d= -f2)" == "$VERSION_NAME" ]] || fail "version increment failed"
 [[ "$(grep '^VERSION_BUILD=' "$AFTER/app/version.properties" | cut -d= -f2)" == "$VERSION_BUILD" ]] || fail "build increment failed"
 python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" | tee "$OUT/26535_versioned_validation.txt"
 manifest_audited_live "$AFTER" "$OUT/26535_pre_gradle_audited_runtime.sha256"
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
 ( cd "$THIRD" && sha256sum -c "$BJZHOU_MANIFEST" ) > "$OUT/26535_vendor_manifest_prebuild.txt"
 rm -rf "$ROOT/app/src/main"; mkdir -p "$ROOT/app/src"
 cp -a "$AFTER/app/src/main" "$ROOT/app/src/"; cp "$AFTER/app/version.properties" "$ROOT/app/version.properties"; cp "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"
 assert_cpp_deps_exact(){ local root="$1" phase="$2" expected actual; if [[ "$phase" == pre ]]; then expected=$'.gitignore'; else expected=$'.gitignore\narchive.h\narchive_entry.h\ntechnicallyflac.h\ntiny_dng_writer.h'; fi; actual="$(find "$root/app/src/main/cpp/deps" -mindepth 1 -maxdepth 1 -type f -printf '%f\n' | LC_ALL=C sort)"; [[ "$actual" == "$expected" ]] || fail "unexpected cpp/deps ($phase): [$actual]"; }
 assert_cpp_deps_exact "$ROOT" pre
 manifest_audited_live "$ROOT" "$OUT/26535_installed_pre_gradle_audited_runtime.sha256"
 cmp -s "$OUT/26535_pre_gradle_audited_runtime.sha256" "$OUT/26535_installed_pre_gradle_audited_runtime.sha256" || fail "installed candidate drift before Gradle"
 (cd "$ROOT/app/src/main/cpp/third_party_26507" && sha256sum -c "$BJZHOU_MANIFEST") > "$OUT/26535_installed_vendor_manifest_prebuild.txt"
 chmod +x ./gradlew
 ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace
 pass "real Android Kotlin + Java compile gates passed"
 ./gradlew :app:assembleDebug --stacktrace
 pass "assembleDebug passed"
}

echo "=== 26535 GATE 5: post-build exact source/native/architecture revalidation ==="
assert_cpp_deps_exact "$ROOT" post
manifest_audited_live "$ROOT" "$OUT/26535_post_gradle_audited_runtime.sha256"
cmp -s "$OUT/26535_pre_gradle_audited_runtime.sha256" "$OUT/26535_post_gradle_audited_runtime.sha256" || fail "Gradle mutated audited source"
(cd "$ROOT/app/src/main/cpp/third_party_26507" && sha256sum -c "$BJZHOU_MANIFEST") > "$OUT/26535_postbuild_native_dependency_manifest_check.txt"
python3 "$VALIDATE" --base "$BASE" --candidate "$ROOT" | tee "$OUT/26535_postbuild_architecture_validation.txt"
python3 "$JAVA_XML_PREFLIGHT" --root "$ROOT" | tee "$OUT/26535_postbuild_java_xml_preflight.txt"
python3 "$NATIVE_JPEG_PREFLIGHT" --root "$ROOT" | tee "$OUT/26535_postbuild_native_jpeg_preflight.txt"
python3 "$CHROMA_SHADER" --root "$ROOT" --validator glslangValidator | tee "$OUT/26535_postbuild_highlight_chroma_shader.txt"
pass "post-build source/native/shared-Spatial-RGB contracts remained exact"

echo "=== 26535 GATE 6: exactly one APK + deterministic next candidate ==="
mapfile -t BUILT_APKS < <(find "$ROOT/app/build/outputs/apk" -type f -name '*.apk' -print 2>/dev/null)
[[ "${#BUILT_APKS[@]}" -eq 1 ]] || fail "expected exactly one Gradle APK, found ${#BUILT_APKS[@]}"
cp "${BUILT_APKS[0]}" "$FINAL"; find "$ROOT/app/build" -type f -name '*.apk' -delete
[[ -f "$FINAL" ]] || fail "final APK missing"
[[ "$(find "$ROOT" -maxdepth 1 -type f -name '*.apk' | wc -l)" -eq 1 ]] || fail "root APK count is not exactly one"
sha256sum "$FINAL" > "$OUT/26535_APK.sha256"
rm -rf "$AFTER/app/src/main/cpp/third_party_26507"
manifest_all "$AFTER" "$SOURCE_MANIFEST_OUT"
[[ "$(wc -l < "$SOURCE_MANIFEST_OUT")" -eq "$EXPECTED_CANDIDATE_FILES" ]] || fail "26535 candidate file count drift"
( cd "$AFTER" && tar --sort=name --mtime='UTC 2026-08-24 00:00:00' --owner=0 --group=0 --numeric-owner -czf "$SOURCE_TAR_OUT" app/src/main app/version.properties app/build.gradle )
sha256sum "$SOURCE_TAR_OUT" > "$OUT/26535_candidate_app_source.tar.gz.sha256"
sha256sum "$SOURCE_MANIFEST_OUT" > "$OUT/26535_candidate_source_manifest_file.sha256"
cat > "$OUT/26535_SCOPE_PROVENANCE.txt" <<EOF
BASE_BRANCH=$EXPECTED_BRANCH
BASE_STRICT_26534_HANDOFF_HEAD=$STRICT_26534_HANDOFF_HEAD
BASE_ARTIFACT=$BASE_ARTIFACT
BASE_SOURCE_TAR_SHA=$EXPECTED_BASE_TAR_SHA
TARGET_VERSION=$VERSION_NAME
TARGET_BUILD=$VERSION_BUILD
RUNTIME_DELTA_FILES=8
MOTION_PRODUCTION=MGC_SPATIAL_RGB_RGBA32F
NIGHT_PRODUCTION=MGC_SPATIAL_RGB_RGBA32F_TO_JIN
NIGHT_SECOND_MGC_PASS=false
MOTION_DNG_SIDECAR_AS_JPEG=false
NIGHT_DNG_SIDECAR_AS_JPEG=false
MOTION_RCD_REDEMOSAIC=false
NIGHT_RCD_REDEMOSAIC=false
MGC_NATIVE_RELIABILITY_TELEMETRY=true
SUPER_RES_DETAIL_RELIABILITY_GATE=true
SUPER_RES_BASE_CARRIER_UNCHANGED=true
HIGHLIGHT_CHROMA_GUARD=PRE_PROFILE_CLIP_EDGE_OUTLIER_LUMA_PRESERVING
HIGHLIGHT_HUE_TARGETING=false
SHORT_BENTO_REJECTION_UNCHANGED=true
NIGHT_EXACT_TIMESTAMP_METADATA_PRESERVED=true
JIN_FINISHING_PRESERVED=true
EOF

echo "PASS: 26535 MOTION + NIGHT SHARED SPATIAL-RGB ARCHITECTURE"
echo "PASS: 26535 SR RELIABILITY + HIGHLIGHT CHROMA + TIMING TELEMETRY"
echo "PASS: 26535 EXACT SUCCESSFUL-26534 ARTIFACT LINEAGE + 8-FILE DELTA + ONE APK"
