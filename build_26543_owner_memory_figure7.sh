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
BASE_26542_HANDOFF_HEAD="db3e9aa6490e6fcc84309374a809ed90dfb153de"
BASE_ARTIFACT="photon-26542-night-parity-wronski-figure7"
BASE_ARTIFACT_ID="9586864070"
BASE_ARTIFACT_SHA="77e2e20c767c11d102c8817cf635e22bfdaebaeba506f968163348feeac932bd"
BASE_TAR_REL="build_26542_night_parity_wronski_figure7_outputs/26542_candidate_app_source.tar.gz"
BASE_MANIFEST_REL="build_26542_night_parity_wronski_figure7_outputs/26542_candidate_source.sha256"
EXPECTED_BASE_TAR_SHA="862ed7f08dd56c2359ed57ada73ca1095fddec4c815fd1b814dec7b4f27c5056"
EXPECTED_BASE_MANIFEST_SHA="1bc889af07d5065eda3cc8d499827d3ae5981e46801cefb23f3612710bf09e7a"
EXPECTED_BASE_FILES=967
EXPECTED_CANDIDATE_FILES=967
VERSION_NAME="0.9726543"; VERSION_BUILD="26543"
BJZHOU_VENDOR_HEAD="09c76e57e8f01a5a8fc536ab41fc80ba642d4042"
REPO="${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
[[ -n "$TOKEN" ]] || fail "GitHub token unavailable for exact successful 26542 artifact recovery"

APPLY="$ROOT/apply_26543_owner_memory_figure7.py"
FINISH="$ROOT/finish_26543_banded_figure7_covariance.py"
FIX_V13="$ROOT/fix_26543_v13_kotlin_compile.py"
FIX_V14="$ROOT/fix_26543_v14_javac_import.py"
VALIDATE="$ROOT/validate_26543_owner_memory_figure7.py"
SYNTAX="$ROOT/preflight_26543_changed_syntax.py"
CONTRACT="$ROOT/preflight_26543_java_kotlin_contracts.py"
HANDOFF="$ROOT/26543_HANDOFF_HASHES.sha256"
BASE_MANIFEST_PIN="$ROOT/26543_BASE_26542_CANDIDATE_SOURCE.sha256"
BASE_MANIFEST_PIN_SHA="$ROOT/26543_BASE_26542_CANDIDATE_SOURCE_FILE.sha256"
BASE_HEAD_FILE="$ROOT/26543_BASE_26542_HANDOFF_HEAD.txt"
PROTECTED="$ROOT/26543_PROTECTED_26542_RUNTIME_ANCHORS.sha256"
PAYLOAD="$ROOT/26543_RUNTIME_PAYLOAD.tar.gz"
PAYLOAD_SHA="$ROOT/26543_RUNTIME_PAYLOAD.tar.gz.sha256"
EXPECTED_PATCH="$ROOT/26543_RUNTIME_DELTA_FROM_26542.patch"
EXPECTED_PATCH_SHA="$ROOT/26543_RUNTIME_DELTA_FROM_26542.patch.sha256"
EXPECTED_ROLLBACK="$ROOT/26543_RUNTIME_ROLLBACK_TO_26542.patch"
EXPECTED_ROLLBACK_SHA="$ROOT/26543_RUNTIME_ROLLBACK_TO_26542.patch.sha256"
RUNTIME_LIST="$ROOT/26543_RUNTIME_FILES.txt"
RUNTIME_META="$ROOT/26543_RUNTIME_SHA256.json"

V16_PROVENANCE_PREFLIGHT="$ROOT/preflight_26533_v16_provenance_shader.py"
SHADER_PREFLIGHT="$ROOT/preflight_26532_iris_shaders.py"
NATIVE_JPEG_PREFLIGHT="$ROOT/preflight_26532_native_jpeg_syntax.py"
JAVA_XML_PREFLIGHT="$ROOT/preflight_26532_java_xml_syntax.py"
EMBEDDED_PREFLIGHT="$ROOT/preflight_26529_iris_embedded_shaders_v3.py"
INHERITED_SHADER_PREFLIGHT="$ROOT/preflight_26526_inherited_shaders.py"
KOTLIN_API_PREFLIGHT="$ROOT/preflight_26531_iris_kotlin_api_contracts.py"
NATIVE_DNG_PREFLIGHT="$ROOT/preflight_26527_native_syntax.py"
DNG_TEST="$ROOT/test_26527_dng_subifd.py"
INHERITED_26540_JAVA="$ROOT/preflight_26540_v11_java_compile_contracts.py"
INHERITED_26541_JAVA="$ROOT/preflight_26541_java_compile_contracts.py"
BJZHOU_MANIFEST="$ROOT/26507_BJZHOU_NATIVE_DEPENDENCIES.sha256"
BJZHOU_COMMIT_FILE="$ROOT/26507_BJZHOU_DEPENDENCY_COMMIT.txt"

OUT="$ROOT/build_26543_owner_memory_figure7_outputs"
WORK="$ROOT/.build_26543_owner_memory_figure7_work"
ART="$WORK/26542_artifact"; BASE="$WORK/exact_successful_26542"; AFTER="$WORK/candidate_26543"
PATCHREPO="$WORK/patchrepo"; FORWARDCHECK="$WORK/forwardcheck"; ROLLBACKCHECK="$WORK/rollbackcheck"
BJ="$WORK/bjzhou_vendor"; POSTCHECK="$WORK/postbuild_validation_candidate"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-owner-memory-figure7-debug.apk"
SOURCE_TAR_OUT="$OUT/26543_candidate_app_source.tar.gz"
SOURCE_MANIFEST_OUT="$OUT/26543_candidate_source.sha256"
mapfile -t RUNTIME_FILES < "$RUNTIME_LIST"
[[ "${#RUNTIME_FILES[@]}" -eq 7 ]] || fail "runtime file inventory is not exactly seven"

rm -rf "$OUT" "$WORK"
rm -f "$ROOT"/IrisCamera-*.apk
mkdir -p "$OUT" "$WORK"

echo "=== 26543 GATE 0: exact branch/base-head/handoff integrity ==="
[[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch: $(git branch --show-current)"
[[ "$(tr -d '\r\n' < "$BASE_HEAD_FILE")" == "$BASE_26542_HANDOFF_HEAD" ]] || fail "26542 base head pin drift"
git merge-base --is-ancestor "$BASE_26542_HANDOFF_HEAD" HEAD || fail "current handoff is not descended from successful 26542"
sha256sum -c "$HANDOFF"
sha256sum -c "$BASE_MANIFEST_PIN_SHA"
sha256sum -c "$PAYLOAD_SHA"
sha256sum -c "$EXPECTED_PATCH_SHA"
sha256sum -c "$EXPECTED_ROLLBACK_SHA"
for f in "$APPLY" "$FINISH" "$FIX_V13" "$FIX_V14" "$VALIDATE" "$SYNTAX" "$CONTRACT" "$RUNTIME_META" "$V16_PROVENANCE_PREFLIGHT" "$SHADER_PREFLIGHT" "$NATIVE_JPEG_PREFLIGHT" "$JAVA_XML_PREFLIGHT" "$EMBEDDED_PREFLIGHT" "$INHERITED_SHADER_PREFLIGHT" "$KOTLIN_API_PREFLIGHT" "$NATIVE_DNG_PREFLIGHT" "$DNG_TEST" "$INHERITED_26540_JAVA" "$INHERITED_26541_JAVA" "$BJZHOU_MANIFEST" "$BJZHOU_COMMIT_FILE"; do
  [[ -f "$f" ]] || fail "required safety file missing: $f"
done
[[ "$(tr -d '\r\n' < "$BJZHOU_COMMIT_FILE")" == "$BJZHOU_VENDOR_HEAD" ]] || fail "bjzhou native dependency pin drift"
FORBIDDEN_RE="$(printf '%s' 'git p' 'ush|git sw' 'itch dev|git check' 'out dev')"
! grep -E "$FORBIDDEN_RE" "$0" >/dev/null || fail "forbidden repository command in build script"
BRANCH_CREATE_RE="$(printf '%s' 'git br' 'anch [^-]')"
! grep -E "$BRANCH_CREATE_RE" "$0" >/dev/null || fail "backup/local branch creation is forbidden in 26543 build script"
pass "experimental-clean-photon-rebuild + exact successful 26542 head + no backup/dev/push"

echo "=== 26543 GATE 1: recover ACTUAL successful 26542 candidate artifact ==="
rm -rf "$ART" "$BASE"; mkdir -p "$ART" "$BASE"
META="$WORK/26542_artifact_meta.json"
curl --fail --location --silent --show-error --retry 5 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" "https://api.github.com/repos/$REPO/actions/artifacts/$BASE_ARTIFACT_ID" -o "$META"
python3 - "$META" "$BASE_ARTIFACT_ID" "$BASE_ARTIFACT" "$BASE_26542_HANDOFF_HEAD" "$BASE_ARTIFACT_SHA" "$OUT/26543_base_artifact_selection.txt" <<'PY'
import json,sys
m=json.load(open(sys.argv[1])); aid=int(sys.argv[2]); name=sys.argv[3]; head=sys.argv[4]; digest="sha256:"+sys.argv[5]
assert int(m['id'])==aid,(m.get('id'),aid)
assert m['name']==name,(m.get('name'),name)
assert not m.get('expired',False),'artifact expired'
assert m.get('workflow_run',{}).get('head_sha')==head,m.get('workflow_run',{})
assert m.get('digest')==digest,(m.get('digest'),digest)
open(sys.argv[6],'w').write(f"artifact_id={aid}\nname={name}\nhead_sha={head}\ndigest={digest}\n")
print("PASS: exact 26542 artifact metadata identity")
PY
ZIP="$WORK/26542_artifact.zip"
curl --fail --location --silent --show-error --retry 5 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" "https://api.github.com/repos/$REPO/actions/artifacts/$BASE_ARTIFACT_ID/zip" -o "$ZIP"
[[ "$(sha "$ZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "26542 artifact ZIP digest mismatch"
unzip -q "$ZIP" -d "$ART"
[[ -f "$ART/$BASE_TAR_REL" && -f "$ART/$BASE_MANIFEST_REL" ]] || fail "selected 26542 artifact lacks candidate proof bundle"
[[ "$(sha "$ART/$BASE_TAR_REL")" == "$EXPECTED_BASE_TAR_SHA" ]] || fail "26542 candidate TAR hash mismatch"
[[ "$(sha "$ART/$BASE_MANIFEST_REL")" == "$EXPECTED_BASE_MANIFEST_SHA" ]] || fail "26542 candidate manifest-file hash mismatch"
cmp -s "$ART/$BASE_MANIFEST_REL" "$BASE_MANIFEST_PIN" || fail "downloaded 26542 source manifest differs from uploaded/tested authority"
tar -xzf "$ART/$BASE_TAR_REL" -C "$BASE"
(cd "$BASE" && sha256sum -c "$BASE_MANIFEST_PIN") > "$OUT/26543_base_26542_manifest_check.txt"
[[ "$(wc -l < "$BASE_MANIFEST_PIN")" -eq "$EXPECTED_BASE_FILES" ]] || fail "base candidate manifest count drift"
[[ "$(grep '^VERSION_NAME=' "$BASE/app/version.properties" | cut -d= -f2)" == "0.9726542" ]] || fail "base version name is not 0.9726542"
[[ "$(grep '^VERSION_BUILD=' "$BASE/app/version.properties" | cut -d= -f2)" == "26542" ]] || fail "base build is not 26542"
(cd "$BASE" && sha256sum -c "$PROTECTED") > "$OUT/26543_base_protected_anchor_check.txt"
pass "exact successful 26542 artifact source recovered and verified 967/967; repository app/src is not runtime authority"

echo "=== 26543 GATE 1B: exact seven-file transform + reversible binary proof BEFORE live writes ==="
rm -rf "$AFTER"; cp -a "$BASE" "$AFTER"
python3 "$APPLY" --root "$AFTER"
python3 "$FINISH" --root "$AFTER"
python3 "$FIX_V13" --root "$AFTER"
python3 "$FIX_V14" --root "$AFTER"
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" | tee "$OUT/26543_prebuild_validation.txt"
python3 "$SYNTAX" --root "$AFTER" | tee "$OUT/26543_changed_syntax_preflight.txt"
python3 "$CONTRACT" --root "$AFTER" | tee "$OUT/26543_java_kotlin_contract_preflight.txt"
python3 - "$BASE" "$AFTER" "${RUNTIME_FILES[@]}" <<'PY' > "$OUT/26543_actual_changed_files.txt"
from pathlib import Path
import hashlib,sys
b,c=map(Path,sys.argv[1:3]); expected=sorted(sys.argv[3:])
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def m(root): return {str(f.relative_to(root)):h(f) for f in (root/'app/src/main').rglob('*') if f.is_file()}
mb,mc=m(b),m(c); changed=sorted(k for k in set(mb)|set(mc) if mb.get(k)!=mc.get(k))
if changed!=expected: raise SystemExit("26543 changed-file allowlist mismatch: "+repr(changed))
print("\n".join(changed))
PY
rm -rf "$PATCHREPO"; cp -a "$BASE" "$PATCHREPO"
(
 cd "$PATCHREPO"; git init -q; git config user.email iris26543@example.invalid; git config user.name Iris26543
 git add app/src/main app/version.properties app/build.gradle; git add -f app/src/main/cpp/deps/.gitignore 2>/dev/null || true
 git commit -qm exact-successful-26542
 for rel in "${RUNTIME_FILES[@]}"; do mkdir -p "$(dirname "$rel")"; cp "$AFTER/$rel" "$rel"; done
 git add -N -- app/src/main
 git diff --check
 git diff --binary --full-index --no-ext-diff -- app/src/main > "$OUT/26543_regenerated_forward.patch"
 # Deterministic canonical rollback: commit the audited candidate as baseline, then copy exact 26542 files back.
 # Do not use `git diff -R`: Git versions/configurations may render reversed a/b path prefixes differently.
 git add app/src/main
 git commit -qm candidate-26543-for-rollback
 for rel in "${RUNTIME_FILES[@]}"; do cp "$BASE/$rel" "$rel"; done
 git diff --check
 git diff --binary --full-index --no-ext-diff -- app/src/main > "$OUT/26543_regenerated_rollback.patch"
)
cmp -s "$OUT/26543_regenerated_forward.patch" "$EXPECTED_PATCH" || fail "regenerated 26543 forward patch differs"
cmp -s "$OUT/26543_regenerated_rollback.patch" "$EXPECTED_ROLLBACK" || fail "regenerated 26543 rollback patch differs"
cp "$EXPECTED_ROLLBACK" "$OUT/26543_prechange_exact_rollback.patch"
rm -rf "$FORWARDCHECK"; cp -a "$BASE" "$FORWARDCHECK"
patch -d "$FORWARDCHECK" -p1 --batch --forward --fuzz=0 --no-backup-if-mismatch < "$EXPECTED_PATCH" >/dev/null
manifest_all "$AFTER" "$OUT/26543_candidate_preversion.sha256"; manifest_all "$FORWARDCHECK" "$OUT/26543_forwardcheck.sha256"
cmp -s "$OUT/26543_candidate_preversion.sha256" "$OUT/26543_forwardcheck.sha256" || fail "forward patch does not reproduce exact 26543 candidate"
rm -rf "$ROLLBACKCHECK"; cp -a "$AFTER" "$ROLLBACKCHECK"
patch -d "$ROLLBACKCHECK" -p1 --batch --forward --fuzz=0 --no-backup-if-mismatch < "$EXPECTED_ROLLBACK" >/dev/null
manifest_all "$BASE" "$OUT/26543_base_for_rollback.sha256"; manifest_all "$ROLLBACKCHECK" "$OUT/26543_rollbackcheck.sha256"
cmp -s "$OUT/26543_base_for_rollback.sha256" "$OUT/26543_rollbackcheck.sha256" || fail "rollback does not restore exact successful 26542"
pass "exact seven-file forward/rollback proof; fuzz=0 both directions; live source untouched"

echo "=== 26543 GATE 2: live ownership + bounded memory + Figure-7 + inherited architecture/shader/API/native/DNG safety proof ==="
python3 "$SYNTAX" --root "$AFTER" --validator glslangValidator | tee "$OUT/26543_changed_syntax_glslang_preflight.txt"
python3 "$CONTRACT" --root "$AFTER" | tee "$OUT/26543_java_kotlin_contract_gate2.txt"
python3 "$INHERITED_26540_JAVA" --root "$AFTER" | tee "$OUT/26543_inherited_26540_java_contract.txt"
python3 "$INHERITED_26541_JAVA" --root "$AFTER" | tee "$OUT/26543_inherited_26541_java_contract.txt"
python3 "$V16_PROVENANCE_PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26543_v16_provenance_shader_preflight.txt"
python3 "$SHADER_PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26543_shader_preflight.txt"
python3 "$EMBEDDED_PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26543_embedded_shader_preflight.txt"
python3 "$INHERITED_SHADER_PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26543_inherited_shader_preflight.txt"
python3 "$KOTLIN_API_PREFLIGHT" --root "$AFTER" | tee "$OUT/26543_kotlin_api_preflight.txt"
python3 "$NATIVE_DNG_PREFLIGHT" --root "$AFTER" | tee "$OUT/26543_dng_native_preflight.txt"
python3 "$NATIVE_JPEG_PREFLIGHT" --root "$AFTER" | tee "$OUT/26543_native_jpeg_preflight.txt"
python3 "$JAVA_XML_PREFLIGHT" --root "$AFTER" | tee "$OUT/26543_java_xml_preflight.txt"
python3 "$DNG_TEST" --root "$AFTER" | tee "$OUT/26543_dng_subifd_preflight.txt"
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" | tee "$OUT/26543_architecture_contract_preflight.txt"
echo "PRE-BUILD SAFETY PROOF PASSED"
pass "live-owner Wronski/IPOL Figure-7 + bounded Night RAW/spool + bounded band covariance; 26542 role-aware DNG and 26541 highlight/luma/Night contracts preserved"

echo "=== 26543 GATE 3: VERSION 0.9726543 / 26543 + native restore + compile/assemble in SAME guarded block ==="
{
 sed -i "s/^VERSION_NAME=.*/VERSION_NAME=$VERSION_NAME/; s/^VERSION_BUILD=.*/VERSION_BUILD=$VERSION_BUILD/" "$AFTER/app/version.properties"
 [[ "$(grep '^VERSION_NAME=' "$AFTER/app/version.properties" | cut -d= -f2)" == "$VERSION_NAME" ]] || fail "version increment failed"
 [[ "$(grep '^VERSION_BUILD=' "$AFTER/app/version.properties" | cut -d= -f2)" == "$VERSION_BUILD" ]] || fail "build increment failed"
 python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" --postbuild | tee "$OUT/26543_versioned_validation.txt"
 manifest_audited_live "$AFTER" "$OUT/26543_pre_gradle_audited_runtime.sha256"

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
 ( cd "$THIRD" && sha256sum -c "$BJZHOU_MANIFEST" ) > "$OUT/26543_vendor_manifest_prebuild.txt"

 rm -rf "$ROOT/app/src/main"; mkdir -p "$ROOT/app/src"
 cp -a "$AFTER/app/src/main" "$ROOT/app/src/"; cp "$AFTER/app/version.properties" "$ROOT/app/version.properties"; cp "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"
 assert_cpp_deps_exact(){ local root="$1" phase="$2" expected actual; if [[ "$phase" == pre ]]; then expected=$'.gitignore'; else expected=$'.gitignore\narchive.h\narchive_entry.h\ntechnicallyflac.h\ntiny_dng_writer.h'; fi; actual="$(find "$root/app/src/main/cpp/deps" -mindepth 1 -maxdepth 1 -type f -printf '%f\n' | LC_ALL=C sort)"; [[ "$actual" == "$expected" ]] || fail "unexpected cpp/deps ($phase): [$actual]"; }
 assert_cpp_deps_exact "$ROOT" pre
 manifest_audited_live "$ROOT" "$OUT/26543_installed_pre_gradle_audited_runtime.sha256"
 cmp -s "$OUT/26543_pre_gradle_audited_runtime.sha256" "$OUT/26543_installed_pre_gradle_audited_runtime.sha256" || fail "installed candidate drift before Gradle"
 (cd "$ROOT/app/src/main/cpp/third_party_26507" && sha256sum -c "$BJZHOU_MANIFEST") > "$OUT/26543_installed_vendor_manifest_prebuild.txt"
 python3 "$CONTRACT" --root "$ROOT" | tee "$OUT/26543_java_kotlin_contract_pre_gradle.txt"
 chmod +x ./gradlew
 ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace
 pass "real Android Kotlin + Java compile gates passed"
 ./gradlew :app:assembleDebug --stacktrace
 pass "assembleDebug passed"
}

echo "=== 26543 GATE 4: post-build exact source/native/architecture revalidation ==="
assert_cpp_deps_exact "$ROOT" post
manifest_audited_live "$ROOT" "$OUT/26543_post_gradle_audited_runtime.sha256"
cmp -s "$OUT/26543_pre_gradle_audited_runtime.sha256" "$OUT/26543_post_gradle_audited_runtime.sha256" || fail "Gradle mutated audited source"
(cd "$ROOT/app/src/main/cpp/third_party_26507" && sha256sum -c "$BJZHOU_MANIFEST") > "$OUT/26543_postbuild_native_dependency_manifest_check.txt"
rm -rf "$POSTCHECK"; mkdir -p "$POSTCHECK/app/src"
cp -a "$ROOT/app/src/main" "$POSTCHECK/app/src/"; cp "$ROOT/app/version.properties" "$POSTCHECK/app/version.properties"; cp "$ROOT/app/build.gradle" "$POSTCHECK/app/build.gradle"
rm -rf "$POSTCHECK/app/src/main/cpp/third_party_26507"
find "$POSTCHECK/app/src/main/cpp/deps" -mindepth 1 -maxdepth 1 -type f ! -name '.gitignore' -delete
assert_cpp_deps_exact "$POSTCHECK" pre
manifest_audited_live "$POSTCHECK" "$OUT/26543_postbuild_sanitized_audited_runtime.sha256"
cmp -s "$OUT/26543_pre_gradle_audited_runtime.sha256" "$OUT/26543_postbuild_sanitized_audited_runtime.sha256" || fail "sanitized post-build audited runtime drift"
python3 "$VALIDATE" --base "$BASE" --candidate "$POSTCHECK" --postbuild | tee "$OUT/26543_postbuild_architecture_validation.txt"
python3 "$JAVA_XML_PREFLIGHT" --root "$POSTCHECK" | tee "$OUT/26543_postbuild_java_xml_preflight.txt"
python3 "$CONTRACT" --root "$POSTCHECK" | tee "$OUT/26543_java_kotlin_contract_postbuild.txt"
python3 "$NATIVE_JPEG_PREFLIGHT" --root "$POSTCHECK" | tee "$OUT/26543_postbuild_native_jpeg_preflight.txt"

mapfile -t BUILT_APKS < <(find "$ROOT/app/build/outputs/apk" -type f -name '*.apk' -print)
[[ "${#BUILT_APKS[@]}" -eq 1 ]] || fail "expected exactly one Gradle APK, found ${#BUILT_APKS[@]}"
cp "${BUILT_APKS[0]}" "$FINAL"; find "$ROOT/app/build" -type f -name '*.apk' -delete
[[ -f "$FINAL" ]] || fail "final APK missing"
[[ "$(find "$ROOT" -maxdepth 1 -type f -name '*.apk' | wc -l)" -eq 1 ]] || fail "root APK count is not exactly one"
sha256sum "$FINAL" > "$OUT/26543_APK.sha256"

rm -rf "$AFTER/app/src/main/cpp/third_party_26507"
find "$AFTER/app/src/main/cpp/deps" -mindepth 1 -maxdepth 1 -type f ! -name '.gitignore' -delete
manifest_all "$AFTER" "$SOURCE_MANIFEST_OUT"
[[ "$(wc -l < "$SOURCE_MANIFEST_OUT")" -eq "$EXPECTED_CANDIDATE_FILES" ]] || fail "26543 candidate file count drift"
( cd "$AFTER" && tar --sort=name --mtime='UTC 2026-08-26 01:45:00' --owner=0 --group=0 --numeric-owner -czf "$SOURCE_TAR_OUT" app/src/main app/version.properties app/build.gradle )
sha256sum "$SOURCE_TAR_OUT" > "$OUT/26543_candidate_app_source.tar.gz.sha256"
sha256sum "$SOURCE_MANIFEST_OUT" > "$OUT/26543_candidate_source_manifest_file.sha256"
cat > "$OUT/26543_SCOPE_PROVENANCE.txt" <<EOF
Iris 0.9726543 / 26543
Base: exact successful 26542 Actions candidate, artifact $BASE_ARTIFACT_ID, head $BASE_26542_HANDOFF_HEAD.
Runtime delta: exactly seven files.
Ownership: production Night and Motion reach GlesMgcRawFusion(SPATIAL_RGB) -> GlesIris26521SpatialRgbStacker -> embedded GlesIris26521SpatialRgbShaders covariance/mergeRgb; dormant IrisNightMgc1271Bridge has no callers.
Figure 7: active embedded Spatial-RGB owner uses RAW/2 Bayer-quad covariance, public Wronski/IPOL linear A/D steerable law, kStretch=4, kShrink=2 and exp(-0.5*d), in sensor/exposure-normalized Bayer noise domain.
Memory: Night retains one in-memory SHORT reference; later RAWs spool through a bounded three-Image Camera2 window; active stacker reads only current frame/region; low-memory banded fallback reuses one covariance scratch instead of retaining per-frame RAW/2 covariance textures.
Preserved: 26542 role-aware 12-short stacked-DNG parity, 26541 near-clip highlight exact no-op outside gate, MGC luma=0, dedicated non-ZSL Night 12+3, tone/UHDR/DNG/SR/zoom/Jin.
No Photon Night fallback. No single-frame fallback. No RCD. No dev/push/backup branch.
EOF
pass "post-build exact source/native/architecture checks + one APK + clean 26543 candidate checkpoint"
echo "PASS: 26543 BUILD COMPLETE: $FINAL"
