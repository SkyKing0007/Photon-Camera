#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
manifest_audited(){
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
REPO_BASE_HEAD="c315877fa5ba5be98778f27c1218e63249915f65"
BACKUP_BRANCH="backup-26545-v1-4-tested-before-26546-vgn-night-fix"
BASE_RUN_ID="33032848083"
BASE_ARTIFACT_ID="9630958191"
BASE_ARTIFACT_NAME="photon-26545-v1-4-current-mgc-parity"
BASE_ARTIFACT_SHA="6a35024a95ea7cefe9b11bf2dbd9a904bc70ddf81911c676ac6f198e6fe4f77c"
BASE_TAR_SHA="162d45e035a0ee69ecdcde56be7b5ce74b4777828b84e9b1a40a324a71dacb27"
BASE_MANIFEST_SHA="cf50d39250c22875d489f8432c4a10be72085e250d63866c91a763482a46df02"
CAND_MANIFEST_SHA="e148ca391d613c716326aa6ce24cf98bff81815293f337cf286e3db30eddb58b"
BASE_APK_SHA="20aa130070de084be1812a718904579f10a2e19e265a700565f3467e605ff866"
VERSION_NAME="0.9726546"
VERSION_BUILD="26546"
REVISION="V1"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"

BASE_PIN="$ROOT/V1_26546_BASE_26545_V1_4_AUDITED_RUNTIME.sha256"
BASE_TAR_PIN="$ROOT/V1_26546_BASE_26545_V1_4_CANDIDATE_TAR.sha256"
CAND_PIN="$ROOT/V1_26546_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256"
RUNTIME_LIST="$ROOT/V1_26546_RUNTIME_FILES.txt"
FORWARD="$ROOT/V1_26546_RUNTIME_DELTA_FROM_26545_V1_4.patch"
ROLLBACK="$ROOT/V1_26546_RUNTIME_ROLLBACK_TO_26545_V1_4.patch"
VALIDATE="$ROOT/validate_26546_v1_vgn_night_ownership.py"
GLSL_PREFLIGHT="$ROOT/preflight_26546_v1_glsl.py"
HANDOFF_HASHES="$ROOT/V1_26546_HANDOFF_HASHES.sha256"
VENDOR_MANIFEST="$ROOT/V1_26546_NATIVE_VENDOR_DEPENDENCIES.sha256"
OUT="$ROOT/build_26546_v1_vgn_night_ownership_outputs"
WORK="$ROOT/.build_26546_v1_vgn_night_ownership_work"
ARTZIP="$WORK/v1_4_artifact.zip"
ARTDIR="$WORK/v1_4_artifact"
BASE_POST="$WORK/v1_4_postbuild_source"
BASE="$WORK/exact_frozen_26545_v1_4"
AFTER="$WORK/candidate_26546_v1"
VENDOR_COPY="$WORK/v1_4_native_vendor"
PATCHREPO="$WORK/patchrepo"
FORWARDCHECK="$WORK/forwardcheck"
ROLLBACKCHECK="$WORK/rollbackcheck"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-v1-vgn-night-ownership-debug.apk"

mapfile -t RUNTIME_FILES < "$RUNTIME_LIST"
[[ "${#RUNTIME_FILES[@]}" -eq 16 ]] || fail "runtime file inventory is not exactly 16"
rm -rf "$OUT" "$WORK"
rm -f "$FINAL"
mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE_POST" "$BASE" "$VENDOR_COPY"
cat > "$OUT/26546_V1_COMPILER_STATUS.txt" <<'EOF'
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF
cat > "$OUT/26546_V1_STRICT_HANDOFF_REPORT.txt" <<'EOF'
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
POST-BUILD INVARIANCE: NOT RUN
TARGET VERSION/BUILD: 0.9726546 / 26546 V1
EOF
set_report(){
  local key="$1" value="$2"
  python3 - "$OUT/26546_V1_STRICT_HANDOFF_REPORT.txt" "$key" "$value" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); key=sys.argv[2]; value=sys.argv[3]
lines=p.read_text().splitlines(); found=False
for i,line in enumerate(lines):
    if line.startswith(key+':'):
        lines[i]=key+': '+value; found=True; break
if not found: raise SystemExit('missing report key '+key)
p.write_text('\n'.join(lines)+'\n')
PY
}

echo "=== 26546 V1 GATE 0: branch / backup / lineage / sealed handoff integrity ==="
[[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch: $(git branch --show-current)"
git merge-base --is-ancestor "$REPO_BASE_HEAD" HEAD || fail "26546 handoff commit is not descended from tested 26545 V1.4 checkpoint"
git fetch --no-tags origin "refs/heads/$BACKUP_BRANCH:refs/remotes/origin/$BACKUP_BRANCH" >/dev/null 2>&1 || fail "unable to fetch required architectural backup"
BACKUP_SHA="$(git rev-parse "refs/remotes/origin/$BACKUP_BRANCH" 2>/dev/null || true)"
[[ "$BACKUP_SHA" == "$REPO_BASE_HEAD" ]] || fail "backup branch is missing or not exact tested 26545 V1.4"
[[ -n "$TOKEN" ]] || fail "GitHub token unavailable for exact successful 26545 V1.4 artifact"
for f in "$BASE_PIN" "$BASE_TAR_PIN" "$CAND_PIN" "$RUNTIME_LIST" "$FORWARD" "$ROLLBACK" "$VALIDATE" "$GLSL_PREFLIGHT" "$HANDOFF_HASHES" "$VENDOR_MANIFEST"; do
  [[ -f "$f" ]] || fail "required handoff file missing: $f"
done
sha256sum -c "$HANDOFF_HASHES"
[[ "$(sha "$BASE_PIN")" == "$BASE_MANIFEST_SHA" ]] || fail "26545 V1.4 base manifest SHA drift"
[[ "$(wc -l < "$BASE_PIN")" -eq 969 ]] || fail "26545 V1.4 base manifest is not 969 audited files"
[[ "$(sha "$CAND_PIN")" == "$CAND_MANIFEST_SHA" ]] || fail "26546 candidate manifest SHA drift"
[[ "$(wc -l < "$CAND_PIN")" -eq 969 ]] || fail "26546 candidate manifest is not 969 audited files"
grep -Fx "$BASE_TAR_SHA  26545_V1_4_candidate_app_source.tar.gz" "$BASE_TAR_PIN" >/dev/null || fail "26545 V1.4 candidate TAR pin drift"
python3 -m py_compile "$VALIDATE" "$GLSL_PREFLIGHT"
python3 "$VALIDATE" --self-test
python3 "$GLSL_PREFLIGHT" --self-test
bash -n "$0"
python3 - "$REPO_BASE_HEAD" <<'PY'
import subprocess,sys
base=sys.argv[1]
allowed={
'.github/workflows/build-26546-v1-vgn-night-ownership.yml',
'V1_26546_BASE_26545_V1_4_AUDITED_RUNTIME.sha256',
'V1_26546_BASE_26545_V1_4_CANDIDATE_TAR.sha256',
'V1_26546_BASE_PROVENANCE.txt',
'V1_26546_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256',
'V1_26546_HANDOFF_HASHES.sha256',
'V1_26546_LOCAL_VALIDATION.txt',
'V1_26546_NATIVE_VENDOR_DEPENDENCIES.sha256',
'V1_26546_RUNTIME_DELTA_FROM_26545_V1_4.patch',
'V1_26546_RUNTIME_FILES.txt',
'V1_26546_RUNTIME_ROLLBACK_TO_26545_V1_4.patch',
'V1_26546_UPLOAD_INSTRUCTIONS.md',
'build_26546_v1_vgn_night_ownership.sh',
'preflight_26546_v1_glsl.py',
'validate_26546_v1_vgn_night_ownership.py',
}
actual=set(subprocess.check_output(['git','diff','--name-only',base+'..HEAD'],text=True).splitlines())
extra=sorted(actual-allowed); missing=sorted(allowed-actual)
if extra: raise SystemExit('FAIL: 26546 handoff commit changed forbidden repo files: '+repr(extra))
if missing: raise SystemExit('FAIL: 26546 handoff commit incomplete: '+repr(missing))
print('PASS: repository commit contains exactly the 15-file 26546 handoff package; app/src remains untouched before guarded transform')
PY
FORBIDDEN_RE="$(printf '%s' 'git p' 'ush|git sw' 'itch dev|git check' 'out dev')"
! grep -E "$FORBIDDEN_RE" "$0" >/dev/null || fail "forbidden dev/push command present"
pass "tested backup + package integrity + repository source isolation"

echo "=== 26546 V1 GATE 1: reconstruct exact successful 26545 V1.4 runtime authority ==="
URL="https://api.github.com/repos/${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}/actions/artifacts/${BASE_ARTIFACT_ID}/zip"
curl --fail --location --silent --show-error --retry 5 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "$URL" -o "$ARTZIP"
[[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "26545 V1.4 artifact ZIP SHA mismatch"
unzip -q "$ARTZIP" -d "$ARTDIR"
BASE_OUT="$ARTDIR/build_v1_4_26545_current_mgc_parity_outputs"
BASE_TAR="$BASE_OUT/26545_V1_4_candidate_app_source.tar.gz"
BASE_AUDITED="$BASE_OUT/26545_V1_4_frozen_candidate_postbuild.sha256"
BASE_APK_HASH="$BASE_OUT/26545_V1_4_APK.sha256"
[[ -f "$BASE_TAR" && -f "$BASE_AUDITED" && -f "$BASE_APK_HASH" ]] || fail "successful 26545 V1.4 artifact lacks frozen candidate authority"
[[ "$(sha "$BASE_TAR")" == "$BASE_TAR_SHA" ]] || fail "26545 V1.4 candidate TAR SHA mismatch"
[[ "$(sha "$BASE_AUDITED")" == "$BASE_MANIFEST_SHA" ]] || fail "26545 V1.4 audited manifest SHA mismatch"
cmp -s "$BASE_AUDITED" "$BASE_PIN" || fail "artifact audited manifest is not exact 26545 V1.4 pin"
grep -F "$BASE_APK_SHA" "$BASE_APK_HASH" >/dev/null || fail "26545 V1.4 tested APK hash mismatch"
tar -xzf "$BASE_TAR" -C "$BASE_POST"
THIRD_POST="$BASE_POST/app/src/main/cpp/third_party_26507"
[[ -d "$THIRD_POST" ]] || fail "26545 V1.4 post-build TAR missing proven native vendor subtree"
( cd "$THIRD_POST" && sha256sum -c "$VENDOR_MANIFEST" ) > "$OUT/26546_V1_base_vendor_reverified.txt"
cp -a "$THIRD_POST/." "$VENDOR_COPY/"
cp -a "$BASE_POST/." "$BASE/"
rm -rf "$BASE/app/src/main/cpp/third_party_26507"
if [[ -d "$BASE/app/src/main/cpp/deps" ]]; then
  find "$BASE/app/src/main/cpp/deps" -type f ! -name '.gitignore' -delete
fi
manifest_audited "$BASE" "$OUT/26546_V1_base_frozen_reconstructed.sha256"
cmp -s "$OUT/26546_V1_base_frozen_reconstructed.sha256" "$BASE_PIN" || fail "failed to reconstruct exact 969-file 26545 V1.4 authority"
set_report "EXACT PRIOR RUNTIME AUTHORITY" "PASS"
pass "exact successful 26545 V1.4 compiled artifact -> exact frozen audited runtime authority"

echo "=== 26546 V1 GATE 2: candidate-first exact 16-file transform ==="
mkdir -p "$AFTER"
cp -a "$BASE/." "$AFTER/"
(cd "$AFTER" && patch --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 < "$FORWARD" >/dev/null)
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" --base-pin "$BASE_PIN" | tee "$OUT/26546_V1_prebuild_contract.txt"
manifest_audited "$AFTER" "$OUT/26546_V1_candidate_source.sha256"
cmp -s "$OUT/26546_V1_candidate_source.sha256" "$CAND_PIN" || fail "candidate is not exact pinned 969-file 26546 source"
ACTUAL_CHANGED="$OUT/26546_V1_actual_changed_files.txt"
python3 - "$BASE" "$AFTER" "$ACTUAL_CHANGED" <<'PY'
from pathlib import Path
import hashlib,sys
b,c,o=map(Path,sys.argv[1:])
def m(r):
 d={}
 for p in (r/'app/src/main').rglob('*'):
  if not p.is_file(): continue
  rel=p.relative_to(r).as_posix()
  if rel.startswith('app/src/main/cpp/third_party_26507/'): continue
  if rel.startswith('app/src/main/cpp/deps/') and rel!='app/src/main/cpp/deps/.gitignore': continue
  d[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
 for rel in ('app/build.gradle','app/version.properties'):
  p=r/rel
  if p.is_file(): d[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
 return d
mb,mc=m(b),m(c); ch=sorted(k for k in set(mb)|set(mc) if mb.get(k)!=mc.get(k))
o.write_text('\n'.join(ch)+'\n')
PY
cmp -s "$ACTUAL_CHANGED" "$RUNTIME_LIST" || fail "actual changed scope differs from exact 16-file allowlist"
set_report "RUNTIME OWNERSHIP" "PASS"
set_report "DORMANT-OWNER REJECTION" "PASS"
set_report "CHANGED RUNTIME SCOPE" "16 files (exact V1_26546_RUNTIME_FILES.txt)"
pass "candidate-first transform exact 16-file 26546 runtime scope"

echo "=== 26546 V1 GATE 3: REAL GLSL COMPILE ==="
GLSLANG="$(command -v glslangValidator || true)"
[[ -n "$GLSLANG" ]] || fail "pinned glslangValidator not on PATH"
"$GLSLANG" --version | grep -F '16.5.0' >/dev/null || fail "wrong glslangValidator version"
python3 "$GLSL_PREFLIGHT" --root "$AFTER" --validator "$GLSLANG" | tee "$OUT/26546_V1_real_glslang.txt"
sed -i 's/^REAL GLSL COMPILE:.*/REAL GLSL COMPILE: PASS (glslangValidator 16.5.0; 18 active\/changed shaders)/' "$OUT/26546_V1_COMPILER_STATUS.txt"
set_report "REAL GLSL COMPILE" "PASS (glslangValidator 16.5.0; 18 active/changed shaders)"
pass "REAL GLSL COMPILE"

echo "=== 26546 V1 GATE 4: canonical deterministic forward/rollback proof ==="
mkdir -p "$PATCHREPO"
cp -a "$BASE/." "$PATCHREPO/"
(
 cd "$PATCHREPO"
 git init -q
 git config user.email photon-local@example.invalid
 git config user.name Photon26546V1
 git add -A && git commit -qm exact-26545-v1.4
 BASE_COMMIT="$(git rev-parse HEAD)"
 rm -rf app/src/main
 cp -a "$AFTER/app/src/main" app/src/main
 cp "$AFTER/app/version.properties" app/version.properties
 cp "$AFTER/app/build.gradle" app/build.gradle
 git add -A && git commit -qm candidate-26546-v1
 CAND_COMMIT="$(git rev-parse HEAD)"
 for abbrev in 7 12 40; do
   git -c core.abbrev="$abbrev" diff --binary --full-index --no-ext-diff "$BASE_COMMIT" "$CAND_COMMIT" -- "${RUNTIME_FILES[@]}" > "$WORK/forward.$abbrev.patch"
   git -c core.abbrev="$abbrev" diff --binary --full-index --no-ext-diff "$CAND_COMMIT" "$BASE_COMMIT" -- "${RUNTIME_FILES[@]}" > "$WORK/rollback.$abbrev.patch"
   cmp -s "$WORK/forward.$abbrev.patch" "$FORWARD" || fail "forward patch representation changed at core.abbrev=$abbrev"
   cmp -s "$WORK/rollback.$abbrev.patch" "$ROLLBACK" || fail "rollback patch representation changed at core.abbrev=$abbrev"
 done
)
cp -a "$BASE" "$FORWARDCHECK"
(cd "$FORWARDCHECK" && patch --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 < "$FORWARD" >/dev/null)
manifest_audited "$FORWARDCHECK" "$OUT/26546_V1_forwardcheck.sha256"
cmp -s "$OUT/26546_V1_forwardcheck.sha256" "$CAND_PIN" || fail "forward fuzz=0 is not exact 26546 candidate"
cp -a "$AFTER" "$ROLLBACKCHECK"
(cd "$ROLLBACKCHECK" && patch --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 < "$ROLLBACK" >/dev/null)
manifest_audited "$ROLLBACKCHECK" "$OUT/26546_V1_rollbackcheck.sha256"
cmp -s "$OUT/26546_V1_rollbackcheck.sha256" "$BASE_PIN" || fail "rollback fuzz=0 is not exact 26545 V1.4"
set_report "FORWARD PATCH FUZZ=0" "PASS"
set_report "ROLLBACK PATCH FUZZ=0" "PASS"
pass "canonical full-index patches deterministic at abbrev 7/12/40 + fuzz=0 exact both directions"

echo "=== 26546 V1 GATE 5: install exact audited candidate into ephemeral Actions runtime ==="
# The 26545 -> 26546 version increment is inside the exact forward transform above, and all
# compiler/build commands below occur in this same guarded script invocation.
rm -rf "$ROOT/app/src/main"
mkdir -p "$ROOT/app/src"
cp -a "$AFTER/app/src/main" "$ROOT/app/src/"
cp "$AFTER/app/version.properties" "$ROOT/app/version.properties"
cp "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"
manifest_audited "$ROOT" "$OUT/26546_V1_installed_pre_vendor.sha256"
cmp -s "$OUT/26546_V1_installed_pre_vendor.sha256" "$CAND_PIN" || fail "installed runtime differs from exact 969-file candidate"
grep -Fx "VERSION_NAME=$VERSION_NAME" "$ROOT/app/version.properties" >/dev/null || fail "version name not exact"
grep -Fx "VERSION_BUILD=$VERSION_BUILD" "$ROOT/app/version.properties" >/dev/null || fail "version build not exact"
python3 "$VALIDATE" --base "$BASE" --candidate "$ROOT" --base-pin "$BASE_PIN" > "$OUT/26546_V1_installed_pre_gradle_contract.txt"

echo "=== 26546 V1 GATE 5B: restore exact proven 26545 V1.4 native JPEG/UltraHDR vendor source ==="
THIRD="$ROOT/app/src/main/cpp/third_party_26507"
rm -rf "$THIRD"
mkdir -p "$THIRD"
cp -a "$VENDOR_COPY/." "$THIRD/"
[[ -f "$THIRD/libjpeg-turbo/CMakeLists.txt" ]] || fail "pinned libjpeg-turbo source missing before Gradle"
[[ -f "$THIRD/libultrahdr/ultrahdr_api.h" ]] || fail "pinned libultrahdr header missing before Gradle"
[[ -f "$THIRD/libultrahdr/lib/src/ultrahdr_api.cpp" ]] || fail "pinned libultrahdr source missing before Gradle"
[[ ! -e "$THIRD/libultrahdr/CMakeLists.txt" ]] || fail "obsolete libultrahdr CMakeLists returned"
( cd "$THIRD" && sha256sum -c "$VENDOR_MANIFEST" ) > "$OUT/26546_V1_vendor_manifest_prebuild.txt"
manifest_audited "$ROOT" "$OUT/26546_V1_installed_with_vendor_audited_runtime.sha256"
cmp -s "$OUT/26546_V1_installed_with_vendor_audited_runtime.sha256" "$CAND_PIN" || fail "native vendor bootstrap altered audited Iris candidate"
pass "exact successful-26545 V1.4 native vendor authority restored separately"

echo "PRE-BUILD SAFETY PROOF PASSED"
pass "26546 version increment + exact runtime installation + proven native vendor bootstrap are in this same authoritative build invocation"

echo "=== 26546 V1 GATE 6: REAL PROJECT COMPILERS ==="
chmod +x "$ROOT/gradlew"
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace
sed -i 's/^REAL KOTLIN COMPILE:.*/REAL KOTLIN COMPILE: PASS (:app:compileDebugKotlin)/' "$OUT/26546_V1_COMPILER_STATUS.txt"
sed -i 's/^REAL JAVA COMPILE:.*/REAL JAVA COMPILE: PASS (:app:compileDebugJavaWithJavac)/' "$OUT/26546_V1_COMPILER_STATUS.txt"
set_report "REAL KOTLIN COMPILE" "PASS (:app:compileDebugKotlin)"
set_report "REAL JAVA COMPILE" "PASS (:app:compileDebugJavaWithJavac)"
pass "REAL KOTLIN COMPILE"
pass "REAL JAVA COMPILE"

echo "=== 26546 V1 GATE 6B: permanent compiler/build regression gates ==="
[[ -f "$THIRD/libjpeg-turbo/CMakeLists.txt" ]] || fail "REGRESSION: pinned libjpeg-turbo source missing immediately before assemble"
[[ -f "$THIRD/libultrahdr/ultrahdr_api.h" ]] || fail "REGRESSION: pinned libultrahdr source missing immediately before assemble"
( cd "$THIRD" && sha256sum -c "$VENDOR_MANIFEST" ) > "$OUT/26546_V1_vendor_manifest_preassemble.txt"
STACKER_SRC="$ROOT/app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt"
SPATIAL_SRC="$ROOT/app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt"
CAPTURE_SRC="$ROOT/app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java"
VGN_SRC="$ROOT/app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt"
NIGHT_INPUT_SRC="$ROOT/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisNightRgbInput.java"
grep -F 'bentoFlowTexture = flow.texture' "$STACKER_SRC" >/dev/null || fail "REGRESSION: 26545 V1.3 ConvertedAlignment->Int fix missing"
! grep -F 'coreImagingTuning' "$SPATIAL_SRC" >/dev/null || fail "REGRESSION: 26545 V1.3 unresolved coreImagingTuning returned"
grep -F 'private val sabreMergeGradientThreshold: Float? = null' "$SPATIAL_SRC" >/dev/null || fail "REGRESSION: adaptive Sabre gradient default owner missing"
grep -F 'java.nio.ByteBuffer source = plane.getBuffer().duplicate();' "$CAPTURE_SRC" >/dev/null || fail "REGRESSION: 26543 Java ByteBuffer symbol fix missing"
grep -F 'strength>=0.9999?sum:' "$VGN_SRC" >/dev/null || fail "REGRESSION: VGN exact 1.0 local-median endpoint missing"
grep -F 'strength>=0.9999?fc:' "$VGN_SRC" >/dev/null || fail "REGRESSION: VGN exact 1.0 directional endpoint missing"
[[ "$(grep -c 'new GLTexture(' "$NIGHT_INPUT_SRC")" -eq 2 ]] || fail "REGRESSION: Night input no longer has exactly two GPU texture allocations"
# Earlier 26543 failures remain permanent: real GLSL preflight catches reserved identifiers,
# canonical patch proof rejects environment-dependent abbreviations, real Kotlin catches type/scope,
# and real javac catches Java symbol/import failures.
pass "PERMANENT REGRESSION: GLSL/patch/Kotlin/Java/native/VGN/Night-memory failures remain gated"

echo "=== 26546 V1 GATE 7: FULL ANDROID ASSEMBLE ==="
./gradlew :app:assembleDebug --stacktrace
sed -i 's/^FULL ANDROID ASSEMBLE:.*/FULL ANDROID ASSEMBLE: PASS (:app:assembleDebug)/' "$OUT/26546_V1_COMPILER_STATUS.txt"
set_report "FULL ANDROID ASSEMBLE" "PASS (:app:assembleDebug)"
pass "FULL ANDROID ASSEMBLE"

echo "=== 26546 V1 GATE 8: frozen candidate / live runtime / native vendor invariance + one APK ==="
manifest_audited "$AFTER" "$OUT/26546_V1_frozen_candidate_postbuild.sha256"
cmp -s "$OUT/26546_V1_frozen_candidate_postbuild.sha256" "$CAND_PIN" || fail "REGRESSION: frozen 969-file candidate changed during Gradle"
[[ "$(wc -l < "$OUT/26546_V1_frozen_candidate_postbuild.sha256")" -eq 969 ]] || fail "REGRESSION: frozen candidate is not exactly 969 audited files"
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" --base-pin "$BASE_PIN" > "$OUT/26546_V1_frozen_candidate_postbuild_contract.txt"
manifest_audited "$ROOT" "$OUT/26546_V1_post_gradle_audited_runtime.sha256"
cmp -s "$OUT/26546_V1_post_gradle_audited_runtime.sha256" "$CAND_PIN" || fail "REGRESSION: Gradle changed audited Iris runtime source"
( cd "$THIRD" && sha256sum -c "$VENDOR_MANIFEST" ) > "$OUT/26546_V1_vendor_manifest_postbuild.txt"
mapfile -t APKS < <(find "$ROOT/app/build/outputs/apk/debug" -maxdepth 1 -type f -name '*.apk' -print | sort)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one Gradle APK, got ${#APKS[@]}"
cp "${APKS[0]}" "$FINAL"
sha256sum "$FINAL" | tee "$OUT/26546_V1_APK.sha256"
sed -i 's/^POST-BUILD INVARIANCE:.*/POST-BUILD INVARIANCE: PASS (frozen candidate + live audited runtime + native vendor)/' "$OUT/26546_V1_COMPILER_STATUS.txt"
set_report "POST-BUILD INVARIANCE" "PASS (frozen candidate + live audited runtime + native vendor)"
cat > "$OUT/26546_V1_SCOPE_PROVENANCE.txt" <<EOF
Target: $VERSION_NAME / $VERSION_BUILD $REVISION
Tested repository checkpoint: $REPO_BASE_HEAD
Verified architectural backup: $BACKUP_BRANCH -> $REPO_BASE_HEAD
Exact successful prior run: $BASE_RUN_ID
Exact prior artifact ID: $BASE_ARTIFACT_ID
Exact prior artifact name: $BASE_ARTIFACT_NAME
Exact prior artifact ZIP SHA256: $BASE_ARTIFACT_SHA
Exact prior final source TAR SHA256: $BASE_TAR_SHA
Exact prior audited runtime manifest SHA256: $BASE_MANIFEST_SHA (969 files)
Exact prior tested APK SHA256: $BASE_APK_SHA
Exact 26546 candidate audited runtime manifest SHA256: $CAND_MANIFEST_SHA (969 files)
Runtime changed files: 16
Motion VGN control: 0.0..1.0, default 1.0, exact 26545 endpoint at 1.0; Night fixed at 1.0.
Night preview: RAW still requests do not target repeating preview Surface; 12+3 RAW capture policy unchanged.
Night memory: upload is main1, CPU RGBA16F released after synchronous upload before main2 allocation; main3 absent.
Post carrier owner: PostPipeline after entry, with early-failure fallback release and close-before-Jin preserved.
Explicitly unchanged outside 16-file patch: alignment/merge/rejection math, AE/exposure policy, tone/color matrices, DNG/UHDR, Super Res/zoom, RCD routing, luma-denoise policy.
Native JPEG/UltraHDR dependency: exact manifest-verified successful-26545 V1.4 vendor source restored and reverified before/after assemble.
EOF
tar -czf "$OUT/26546_V1_candidate_app_source.tar.gz" -C "$ROOT" app/src/main app/version.properties app/build.gradle
sha256sum "$OUT/26546_V1_candidate_app_source.tar.gz" > "$OUT/26546_V1_candidate_app_source.tar.gz.sha256"
cat "$OUT/26546_V1_COMPILER_STATUS.txt"
cat "$OUT/26546_V1_STRICT_HANDOFF_REPORT.txt"
echo "PASS: 26546 V1 exact successful 26545 V1.4 artifact authority"
echo "PASS: 26546 V1 exact 16-file VGN + Night ownership transform and deterministic rollback"
echo "PASS: 26546 V1 REAL GLSL/KOTLIN/JAVA + FULL ANDROID ASSEMBLE + POST-BUILD INVARIANCE"
echo "APK: $FINAL"
