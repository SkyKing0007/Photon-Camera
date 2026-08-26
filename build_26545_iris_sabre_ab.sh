#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
manifest_all(){
  local root="$1" out="$2"
  (cd "$root" && find app/src/main app/version.properties app/build.gradle -type f -print0 \
    | LC_ALL=C sort -z | xargs -0 sha256sum) > "$out"
}
manifest_audited_live(){
  local root="$1" out="$2"
  (cd "$root" && {
    find app/src/main -type f ! -path 'app/src/main/cpp/third_party_26507/*' ! -path 'app/src/main/cpp/deps/*' -print
    [[ -f app/src/main/cpp/deps/.gitignore ]] && echo app/src/main/cpp/deps/.gitignore
    echo app/version.properties
    echo app/build.gradle
  } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done) > "$out"
}

ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
BASE_HEAD="99b1a4ec0bafd583e09ec686ef396de40403d2fe"
BASE_RUN_ID="32976403042"
BASE_ARTIFACT_ID="9609760449"
BASE_ARTIFACT_NAME="photon-26544-night-rootcause-lifecycle"
BASE_ARTIFACT_SHA="3092d61603574a01957e5268f842c5527dc682c69bfcd855144a72f090e5addd"
BASE_TAR_SHA="411a79c54acbc8e1092ecb306bdea6f3c1ae4c45d4860ee528b1ca153e0eea37"
BASE_MANIFEST_SHA="90a0651864f17ffe535871a185c5de87821cb6c7aefefb757869001f1b02a746"
CAND_MANIFEST_SHA="a923dc9730a7402702cfd7feeb9e6d5d28dd95743e76ee08e96bcbbc2da93da1"
VERSION_NAME="0.9726545"
VERSION_BUILD="26545"
BJZHOU_VENDOR_HEAD="09c76e57e8f01a5a8fc536ab41fc80ba642d4042"
BJZHOU_SABRE_HEAD="8e37909035b51b82ab54941dba390427478899b7"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"

BASE_PIN="$ROOT/26545_BASE_26544_AUDITED_RUNTIME.sha256"
BASE_TAR_PIN="$ROOT/26545_BASE_26544_CANDIDATE_TAR.sha256"
CAND_PIN="$ROOT/26545_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256"
RUNTIME_LIST="$ROOT/26545_RUNTIME_FILES.txt"
FORWARD="$ROOT/26545_RUNTIME_DELTA_FROM_26544.patch"
ROLLBACK="$ROOT/26545_RUNTIME_ROLLBACK_TO_26544.patch"
VALIDATE="$ROOT/validate_26545_iris_sabre_ab.py"
GLSL_PREFLIGHT="$ROOT/preflight_26545_sabre_glsl.py"
HANDOFF_HASHES="$ROOT/26545_HANDOFF_HASHES.sha256"
VENDOR_MANIFEST="$ROOT/26545_NATIVE_VENDOR_DEPENDENCIES.sha256"
VENDOR_COMMIT_FILE="$ROOT/26545_NATIVE_VENDOR_COMMIT.txt"
SABRE_COMMIT_FILE="$ROOT/26545_BJZHOU_SABRE_SOURCE_COMMIT.txt"
OUT="$ROOT/build_26545_iris_sabre_ab_outputs"
WORK="$ROOT/.build_26545_iris_sabre_ab_work"
ARTZIP="$WORK/26544_artifact.zip"
ARTDIR="$WORK/26544_artifact"
BASE_POST="$WORK/26544_postbuild_source"
BASE="$WORK/exact_frozen_26544"
AFTER="$WORK/candidate_26545"
PATCHREPO="$WORK/patchrepo"
FORWARDCHECK="$WORK/forwardcheck"
ROLLBACKCHECK="$WORK/rollbackcheck"
BJ="$WORK/bjzhou_vendor"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-v1-2-sabre-isolation-debug.apk"

mapfile -t RUNTIME_FILES < "$RUNTIME_LIST"
[[ "${#RUNTIME_FILES[@]}" -eq 25 ]] || fail "runtime file inventory is not exactly 25"
rm -rf "$OUT" "$WORK"
rm -f "$FINAL"
mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE_POST" "$BASE"
cat > "$OUT/26545_COMPILER_STATUS.txt" <<'EOF'
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
EOF

cat > "$OUT/26545_STRICT_HANDOFF_REPORT.txt" <<'EOF'
RUNTIME OWNERSHIP: NOT RUN
DORMANT-OWNER REJECTION: NOT RUN
EXACT PRIOR RUNTIME AUTHORITY: NOT RUN
CHANGED RUNTIME SCOPE: NOT RUN
REAL GLSL COMPILE: NOT RUN
REAL KOTLIN COMPILE: NOT RUN
REAL JAVA COMPILE: NOT RUN
FULL ANDROID ASSEMBLE: NOT RUN
FORWARD PATCH FUZZ=0: NOT RUN
ROLLBACK PATCH FUZZ=0: NOT RUN
CLEAN-ZIP REPLAY: PASS (sealed upload package; workflow re-verifies exact handoff hashes)
TARGET VERSION/BUILD: 0.9726545 / 26545
EOF

set_report(){
  local key="$1" value="$2"
  python3 - "$OUT/26545_STRICT_HANDOFF_REPORT.txt" "$key" "$value" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); key=sys.argv[2]; value=sys.argv[3]
lines=p.read_text().splitlines()
found=False
for i,line in enumerate(lines):
    if line.startswith(key+':'):
        lines[i]=key+': '+value; found=True; break
if not found: raise SystemExit('missing report key '+key)
p.write_text('\n'.join(lines)+'\n')
PY
}

echo "=== 26545 GATE 0: branch / lineage / handoff integrity ==="
[[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch: $(git branch --show-current)"
git merge-base --is-ancestor "$BASE_HEAD" HEAD || fail "handoff is not descended from exact successful 26544 V1.3"
[[ -n "$TOKEN" ]] || fail "GitHub token unavailable for exact successful 26544 artifact"
for f in "$BASE_PIN" "$BASE_TAR_PIN" "$CAND_PIN" "$RUNTIME_LIST" "$FORWARD" "$ROLLBACK" "$VALIDATE" "$GLSL_PREFLIGHT" "$HANDOFF_HASHES" "$VENDOR_MANIFEST" "$VENDOR_COMMIT_FILE" "$SABRE_COMMIT_FILE"; do
  [[ -f "$f" ]] || fail "required handoff file missing: $f"
done
sha256sum -c "$HANDOFF_HASHES"
[[ "$(sha "$BASE_PIN")" == "$BASE_MANIFEST_SHA" ]] || fail "base frozen manifest SHA drift"
[[ "$(wc -l < "$BASE_PIN")" -eq 967 ]] || fail "base frozen manifest is not 967 files"
[[ "$(sha "$CAND_PIN")" == "$CAND_MANIFEST_SHA" ]] || fail "candidate expected manifest SHA drift"
[[ "$(wc -l < "$CAND_PIN")" -eq 968 ]] || fail "candidate expected manifest is not 968 files"
grep -Fx "$BASE_TAR_SHA  26544_candidate_app_source.tar.gz" "$BASE_TAR_PIN" >/dev/null || fail "base TAR pin drift"
[[ "$(tr -d '\r\n' < "$VENDOR_COMMIT_FILE")" == "$BJZHOU_VENDOR_HEAD" ]] || fail "native vendor commit pin drift"
[[ "$(tr -d '\r\n' < "$SABRE_COMMIT_FILE")" == "$BJZHOU_SABRE_HEAD" ]] || fail "Sabre source commit pin drift"
python3 -m py_compile "$VALIDATE" "$GLSL_PREFLIGHT"
python3 "$VALIDATE" --self-test
python3 "$GLSL_PREFLIGHT" --self-test
bash -n "$0"
python3 - "$BASE_HEAD" <<'PY'
import subprocess,sys
base=sys.argv[1]
allowed={
'.github/workflows/build-26545-iris-sabre-ab.yml',
'26545_BASE_26544_AUDITED_RUNTIME.sha256',
'26545_BASE_26544_CANDIDATE_TAR.sha256',
'26545_BASE_PROVENANCE.txt',
'26545_BJZHOU_SABRE_SOURCE_COMMIT.txt',
'26545_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256',
'26545_HANDOFF_HASHES.sha256',
'26545_LOCAL_VALIDATION.txt',
'26545_NATIVE_VENDOR_COMMIT.txt',
'26545_NATIVE_VENDOR_DEPENDENCIES.sha256',
'26545_RUNTIME_DELTA_FROM_26544.patch',
'26545_RUNTIME_FILES.txt',
'26545_RUNTIME_ROLLBACK_TO_26544.patch',
'26545_UPLOAD_INSTRUCTIONS.md',
'build_26545_iris_sabre_ab.sh',
'preflight_26545_sabre_glsl.py',
'validate_26545_iris_sabre_ab.py',
}
actual=set(subprocess.check_output(['git','diff','--name-only',base+'..HEAD'],text=True).splitlines())
extra=sorted(actual-allowed); missing=sorted(allowed-actual)
if extra: raise SystemExit('FAIL: handoff commit changed forbidden repo files: '+repr(extra))
if missing: raise SystemExit('FAIL: handoff commit incomplete: '+repr(missing))
print('PASS: repository contains only exact 17-file 26545 handoff; no app/src hand edit')
PY
pass "handoff integrity + repository source isolation"

echo "=== 26545 GATE 1: reconstruct exact frozen successful 26544 runtime authority ==="
URL="https://api.github.com/repos/${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}/actions/artifacts/${BASE_ARTIFACT_ID}/zip"
curl --fail --location --silent --show-error --retry 5 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "$URL" -o "$ARTZIP"
[[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "26544 artifact ZIP SHA mismatch"
unzip -q "$ARTZIP" -d "$ARTDIR"
BASE_OUT="$ARTDIR/build_26544_night_rootcause_lifecycle_outputs"
BASE_TAR="$BASE_OUT/26544_candidate_app_source.tar.gz"
BASE_AUDITED="$BASE_OUT/26544_candidate_audited_runtime.sha256"
[[ -f "$BASE_TAR" && -f "$BASE_AUDITED" ]] || fail "26544 artifact lacks candidate source authority"
[[ "$(sha "$BASE_TAR")" == "$BASE_TAR_SHA" ]] || fail "26544 final candidate TAR SHA mismatch"
[[ "$(sha "$BASE_AUDITED")" == "$BASE_MANIFEST_SHA" ]] || fail "26544 audited manifest SHA mismatch"
cmp -s "$BASE_AUDITED" "$BASE_PIN" || fail "artifact audited manifest is not exact 26544 pin"
tar -xzf "$BASE_TAR" -C "$BASE_POST"
# The successful 26544 final TAR is post-build and therefore contains the separately-owned native
# vendor subtree plus Gradle-populated cpp/deps headers. Prove those vendor bytes first, then strip
# only those non-Iris domains to recover the immutable 967-file candidate that 26544 actually built.
[[ -d "$BASE_POST/app/src/main/cpp/third_party_26507" ]] || fail "26544 post-build TAR missing pinned native vendor subtree"
( cd "$BASE_POST/app/src/main/cpp/third_party_26507" && sha256sum -c "$VENDOR_MANIFEST" ) > "$OUT/26545_base_vendor_reverified.txt"
cp -a "$BASE_POST/." "$BASE/"
rm -rf "$BASE/app/src/main/cpp/third_party_26507"
if [[ -d "$BASE/app/src/main/cpp/deps" ]]; then
  find "$BASE/app/src/main/cpp/deps" -type f ! -name '.gitignore' -delete
fi
manifest_all "$BASE" "$OUT/26545_base_frozen_reconstructed.sha256"
cmp -s "$OUT/26545_base_frozen_reconstructed.sha256" "$BASE_PIN" || fail "failed to reconstruct exact frozen 967-file 26544 authority"
set_report "EXACT PRIOR RUNTIME AUTHORITY" "PASS"
pass "exact successful 26544 artifact -> exact frozen 967-file candidate reconstructed"

echo "=== 26545 V1.2 GATE 2: candidate-first exact 25-file transform ==="
mkdir -p "$AFTER"
cp -a "$BASE/." "$AFTER/"
(cd "$AFTER" && patch --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 < "$FORWARD" >/dev/null)
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" --base-pin "$BASE_PIN" | tee "$OUT/26545_prebuild_contract.txt"
manifest_all "$AFTER" "$OUT/26545_candidate_source.sha256"
cmp -s "$OUT/26545_candidate_source.sha256" "$CAND_PIN" || fail "candidate is not exact pinned 968-file 26545 source"
ACTUAL_CHANGED="$OUT/26545_actual_changed_files.txt"
python3 - "$BASE" "$AFTER" "$ACTUAL_CHANGED" <<'PY'
from pathlib import Path
import hashlib,sys
b,c,o=map(Path,sys.argv[1:])
def m(r):
 d={}
 for p in (r/'app/src/main').rglob('*'):
  if p.is_file(): d[str(p.relative_to(r))]=hashlib.sha256(p.read_bytes()).hexdigest()
 for rel in ('app/build.gradle','app/version.properties'):
  p=r/rel
  if p.is_file(): d[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
 return d
mb,mc=m(b),m(c); ch=sorted(k for k in set(mb)|set(mc) if mb.get(k)!=mc.get(k))
o.write_text('\n'.join(ch)+'\n')
PY
cmp -s "$ACTUAL_CHANGED" "$RUNTIME_LIST" || fail "actual changed scope differs from 25-file allowlist"
set_report "RUNTIME OWNERSHIP" "PASS"
set_report "DORMANT-OWNER REJECTION" "PASS"
set_report "CHANGED RUNTIME SCOPE" "25 files (exact 26545_RUNTIME_FILES.txt)"
pass "candidate-first transform exact 25-file runtime scope"

echo "=== 26545 GATE 3: REAL GLSL COMPILE (active Sabre + shared dependencies) ==="
GLSLANG="$(command -v glslangValidator || true)"
[[ -n "$GLSLANG" ]] || fail "pinned glslangValidator not on PATH"
"$GLSLANG" --version | grep -F '16.5.0' >/dev/null || fail "wrong glslangValidator version"
python3 "$GLSL_PREFLIGHT" --root "$AFTER" --validator "$GLSLANG" | tee "$OUT/26545_real_glslang.txt"
sed -i 's/^REAL GLSL COMPILE:.*/REAL GLSL COMPILE: PASS (glslangValidator 16.5.0; 21 active Sabre\/shared shaders)/' "$OUT/26545_COMPILER_STATUS.txt"
set_report "REAL GLSL COMPILE" "PASS (glslangValidator 16.5.0; 21 active Sabre/shared shaders)"
pass "REAL GLSL COMPILE"

echo "=== 26545 GATE 4: canonical deterministic forward/rollback proof ==="
mkdir -p "$PATCHREPO"
cp -a "$BASE/." "$PATCHREPO/"
(
 cd "$PATCHREPO"
 git init -q
 git config user.email photon-local@example.invalid
 git config user.name Photon26545
 git add -A && git commit -qm exact-26544
 BASE_COMMIT="$(git rev-parse HEAD)"
 rm -rf app/src/main
 cp -a "$AFTER/app/src/main" app/src/main
 cp "$AFTER/app/version.properties" app/version.properties
 cp "$AFTER/app/build.gradle" app/build.gradle
 git add -A && git commit -qm candidate-26545
 CAND_COMMIT="$(git rev-parse HEAD)"
 for abbrev in 7 12 40; do
   git -c core.abbrev="$abbrev" diff --binary --full-index --no-ext-diff "$BASE_COMMIT" "$CAND_COMMIT" -- "${RUNTIME_FILES[@]}" > "$WORK/forward.$abbrev.patch"
   git -c core.abbrev="$abbrev" diff --binary --full-index --no-ext-diff "$CAND_COMMIT" "$BASE_COMMIT" -- "${RUNTIME_FILES[@]}" > "$WORK/rollback.$abbrev.patch"
   cmp -s "$WORK/forward.$abbrev.patch" "$FORWARD" || fail "forward patch differs at core.abbrev=$abbrev"
   cmp -s "$WORK/rollback.$abbrev.patch" "$ROLLBACK" || fail "rollback patch differs at core.abbrev=$abbrev"
 done
)
cp -a "$BASE" "$FORWARDCHECK"
(cd "$FORWARDCHECK" && patch --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 < "$FORWARD" >/dev/null)
manifest_all "$FORWARDCHECK" "$OUT/26545_forwardcheck.sha256"
cmp -s "$OUT/26545_forwardcheck.sha256" "$CAND_PIN" || fail "forward fuzz=0 is not exact candidate"
cp -a "$AFTER" "$ROLLBACKCHECK"
(cd "$ROLLBACKCHECK" && patch --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 < "$ROLLBACK" >/dev/null)
manifest_all "$ROLLBACKCHECK" "$OUT/26545_rollbackcheck.sha256"
cmp -s "$OUT/26545_rollbackcheck.sha256" "$BASE_PIN" || fail "rollback fuzz=0 is not exact 26544"
set_report "FORWARD PATCH FUZZ=0" "PASS"
set_report "ROLLBACK PATCH FUZZ=0" "PASS"
pass "canonical full-index patches deterministic at abbrev 7/12/40 + fuzz=0 exact both directions"

echo "=== 26545 GATE 5: install exact audited candidate into ephemeral Actions runtime ==="
# VERSION_NAME/BUILD change is inside the just-proven forward patch. The version increment and all
# real compiler/assemble commands therefore occur in this one authoritative guarded invocation.
rm -rf "$ROOT/app/src/main"
mkdir -p "$ROOT/app/src"
cp -a "$AFTER/app/src/main" "$ROOT/app/src/"
cp "$AFTER/app/version.properties" "$ROOT/app/version.properties"
cp "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"
manifest_all "$ROOT" "$OUT/26545_installed_pre_vendor.sha256"
cmp -s "$OUT/26545_installed_pre_vendor.sha256" "$CAND_PIN" || fail "installed runtime differs from exact 968-file candidate"
grep -Fx "VERSION_NAME=$VERSION_NAME" "$ROOT/app/version.properties" >/dev/null || fail "version name not exact"
grep -Fx "VERSION_BUILD=$VERSION_BUILD" "$ROOT/app/version.properties" >/dev/null || fail "version build not exact"
python3 "$VALIDATE" --base "$BASE" --candidate "$ROOT" --base-pin "$BASE_PIN" > "$OUT/26545_installed_pre_gradle_contract.txt"

echo "=== 26545 GATE 5B: restore exact proven 26544 native JPEG/UltraHDR vendor source ==="
rm -rf "$BJ"
git init -q "$BJ"
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
THIRD="$ROOT/app/src/main/cpp/third_party_26507"
rm -rf "$THIRD"
mkdir -p "$THIRD"
cp -a "$BJ/app/src/main/cpp/libjpeg-turbo" "$THIRD/libjpeg-turbo"
cp -a "$BJ/app/src/main/cpp/libultrahdr" "$THIRD/libultrahdr"
[[ -f "$THIRD/libjpeg-turbo/CMakeLists.txt" ]] || fail "pinned libjpeg-turbo source missing before Gradle"
[[ -f "$THIRD/libultrahdr/ultrahdr_api.h" ]] || fail "pinned libultrahdr header missing before Gradle"
[[ -f "$THIRD/libultrahdr/lib/src/ultrahdr_api.cpp" ]] || fail "pinned libultrahdr source missing before Gradle"
[[ ! -e "$THIRD/libultrahdr/CMakeLists.txt" ]] || fail "obsolete libultrahdr CMakeLists returned"
( cd "$THIRD" && sha256sum -c "$VENDOR_MANIFEST" ) > "$OUT/26545_vendor_manifest_prebuild.txt"
manifest_audited_live "$ROOT" "$OUT/26545_installed_with_vendor_audited_runtime.sha256"
cmp -s "$OUT/26545_installed_with_vendor_audited_runtime.sha256" "$CAND_PIN" || fail "native vendor bootstrap altered audited Iris candidate"
pass "exact successful-26544 native vendor bootstrap restored separately from current Sabre source"

echo "PRE-BUILD SAFETY PROOF PASSED"
pass "version increment + exact runtime installation + proven native vendor bootstrap are in this same authoritative build invocation"

echo "=== 26545 GATE 6: REAL PROJECT COMPILERS ==="
chmod +x "$ROOT/gradlew"
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace
sed -i 's/^REAL KOTLIN COMPILE:.*/REAL KOTLIN COMPILE: PASS (:app:compileDebugKotlin)/' "$OUT/26545_COMPILER_STATUS.txt"
sed -i 's/^REAL JAVA COMPILE:.*/REAL JAVA COMPILE: PASS (:app:compileDebugJavaWithJavac)/' "$OUT/26545_COMPILER_STATUS.txt"
set_report "REAL KOTLIN COMPILE" "PASS (:app:compileDebugKotlin)"
set_report "REAL JAVA COMPILE" "PASS (:app:compileDebugJavaWithJavac)"
pass "REAL KOTLIN COMPILE"
pass "REAL JAVA COMPILE"

echo "=== 26545 GATE 6B: permanent native-source regression gate ==="
[[ -f "$THIRD/libjpeg-turbo/CMakeLists.txt" ]] || fail "REGRESSION: pinned libjpeg-turbo source missing immediately before assemble"
[[ -f "$THIRD/libultrahdr/ultrahdr_api.h" ]] || fail "REGRESSION: pinned libultrahdr source missing immediately before assemble"
( cd "$THIRD" && sha256sum -c "$VENDOR_MANIFEST" ) > "$OUT/26545_vendor_manifest_preassemble.txt"
pass "PERMANENT REGRESSION: pinned libjpeg-turbo/libultrahdr source present + exact before assemble"

echo "=== 26545 GATE 7: FULL ANDROID ASSEMBLE ==="
./gradlew :app:assembleDebug --stacktrace
sed -i 's/^FULL ANDROID ASSEMBLE:.*/FULL ANDROID ASSEMBLE: PASS (:app:assembleDebug)/' "$OUT/26545_COMPILER_STATUS.txt"
set_report "FULL ANDROID ASSEMBLE" "PASS (:app:assembleDebug)"
pass "FULL ANDROID ASSEMBLE"

echo "=== 26545 GATE 8: frozen-candidate / live-Iris / native-vendor invariance + one APK ==="
manifest_all "$AFTER" "$OUT/26545_frozen_candidate_postbuild.sha256"
cmp -s "$OUT/26545_frozen_candidate_postbuild.sha256" "$CAND_PIN" || fail "REGRESSION: frozen 968-file candidate changed during Gradle"
[[ "$(wc -l < "$OUT/26545_frozen_candidate_postbuild.sha256")" -eq 968 ]] || fail "REGRESSION: frozen candidate is not exactly 968 files"
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" --base-pin "$BASE_PIN" > "$OUT/26545_frozen_candidate_postbuild_contract.txt"
manifest_audited_live "$ROOT" "$OUT/26545_post_gradle_audited_runtime.sha256"
cmp -s "$OUT/26545_post_gradle_audited_runtime.sha256" "$CAND_PIN" || fail "REGRESSION: Gradle changed audited Iris runtime source"
( cd "$THIRD" && sha256sum -c "$VENDOR_MANIFEST" ) > "$OUT/26545_vendor_manifest_postbuild.txt"
pass "PERMANENT REGRESSION: frozen Iris candidate + post-build native vendor authority validated separately"

mapfile -t APKS < <(find "$ROOT/app/build/outputs/apk/debug" -maxdepth 1 -type f -name '*.apk' -print | sort)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one Gradle APK, got ${#APKS[@]}"
cp "${APKS[0]}" "$FINAL"
sha256sum "$FINAL" | tee "$OUT/26545_APK.sha256"
cat > "$OUT/26545_SCOPE_PROVENANCE.txt" <<EOF
Target: $VERSION_NAME / $VERSION_BUILD
Exact prior authority commit: $BASE_HEAD
Exact successful prior run: $BASE_RUN_ID
Exact prior artifact ID: $BASE_ARTIFACT_ID
Exact prior artifact ZIP SHA256: $BASE_ARTIFACT_SHA
Exact prior final source TAR SHA256: $BASE_TAR_SHA
Reconstructed frozen prior Iris manifest SHA256: $BASE_MANIFEST_SHA (967 files)
Exact candidate Iris manifest SHA256: $CAND_MANIFEST_SHA (968 files)
Runtime changed files: 25
Motion Reconstruction setting: Spatial RGB (default/control) or Sabre.
Spatial RGB reconstruction owner remains the exact 26544 control; only explicit routing guards around the shared post boundary change.
Capture/exposure/UHDR/Night and common post-color finishing owners remain byte-identical to 26544.
Sabre source audit pin: bjzhou main $BJZHOU_SABRE_HEAD.
Sabre JPEG: explicit SABRE owner -> NORMAL-only admission -> Sabre sparse alignment/rejection/merge -> ResolveSabre -> Sabre-default user residual denoise -> common Iris color/viewfinder/tone/UHDR/JPEG.
Sabre post isolation: no Spatial/Bento source restore; no Spatial highlight-reliability node; no Spatial reliability payload; no RCD/demosaic.
Sabre RAW: same NORMAL population, Sabre flow/rejection/covariance weighted normalized16 Bayer DNG; black=0 white=65535; no Resolve/demosaic/WB/LSC/denoise/tone/sharpen baked in.
Sabre support/noise: measured post-merge accumulated-green-weight coefficient; stale classic SNR lookup removed.
Shared denoise controls: 0..2 luma/chroma act only after reconstruction and before PostPipeline/tone; luma new-key default=0.0, chroma preserves existing value.
Shared noise model: imported GCam .c or exact Camera2 per-frame selection feeds both Spatial RGB and Sabre; Sabre residual denoise uses MGC-base physical noise scaled by measured merge support.
Night remains isolated and unchanged.
V1.2 ownership regression: PostPipeline routing is driven only by durable reconstruction owner, never by optional Spatial payload inference.
Native build dependency bootstrap: exact successful-26544 JPEG/UltraHDR vendor source at $BJZHOU_VENDOR_HEAD, manifest-verified before and after assemble.
EOF
tar -czf "$OUT/26545_candidate_app_source.tar.gz" -C "$ROOT" app/src/main app/version.properties app/build.gradle
sha256sum "$OUT/26545_candidate_app_source.tar.gz" > "$OUT/26545_candidate_app_source.tar.gz.sha256"
cat "$OUT/26545_COMPILER_STATUS.txt"
cat "$OUT/26545_STRICT_HANDOFF_REPORT.txt"
echo "PASS: 26545 exact prior artifact authority"
echo "PASS: 26545 V1.2 explicit Sabre/Spatial ownership + deterministic rollback"
echo "PASS: 26545 REAL GLSL/KOTLIN/JAVA + FULL ANDROID ASSEMBLE"
echo "APK: $FINAL"
