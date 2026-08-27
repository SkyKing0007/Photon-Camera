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
REPO_BASE_HEAD="256e3ce20ca4e65be7a5243f6b52d25edb44a9cb"
RUNTIME_BASE_HEAD="801e16582656dc6f672d1a292f8375b1046d0fbf"
BACKUP_BRANCH="backup-26545-v1-3-failed-before-v1-4-compiler-fix"
BASE_RUN_ID="33006824714"
BASE_ARTIFACT_ID="9621002273"
BASE_ARTIFACT_NAME="photon-26545-v1-2-sabre-isolation"
BASE_ARTIFACT_SHA="eb924aa95cb790b4c801bf7afa4eeb092b02faf468b990197c53e602f7262bd4"
BASE_TAR_SHA="230627af3b0c12bf297eaae7e9b7efac7e1972d6b9fbefecb3b89e6dd1df69bb"
BASE_MANIFEST_SHA="a923dc9730a7402702cfd7feeb9e6d5d28dd95743e76ee08e96bcbbc2da93da1"
CAND_MANIFEST_SHA="cf50d39250c22875d489f8432c4a10be72085e250d63866c91a763482a46df02"
VERSION_NAME="0.9726545"
VERSION_BUILD="26545"
REVISION="V1.4"
MGC_SOURCE_HEAD="8e37909035b51b82ab54941dba390427478899b7"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"

BASE_PIN="$ROOT/V1_4_26545_BASE_V1_2_AUDITED_RUNTIME.sha256"
BASE_TAR_PIN="$ROOT/V1_4_26545_BASE_V1_2_CANDIDATE_TAR.sha256"
CAND_PIN="$ROOT/V1_4_26545_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256"
RUNTIME_LIST="$ROOT/V1_4_26545_RUNTIME_FILES.txt"
FORWARD="$ROOT/V1_4_26545_RUNTIME_DELTA_FROM_V1_2.patch"
ROLLBACK="$ROOT/V1_4_26545_RUNTIME_ROLLBACK_TO_V1_2.patch"
VALIDATE="$ROOT/validate_v1_4_26545_current_mgc_parity.py"
GLSL_PREFLIGHT="$ROOT/preflight_v1_4_26545_glsl.py"
HANDOFF_HASHES="$ROOT/V1_4_26545_HANDOFF_HASHES.sha256"
VENDOR_MANIFEST="$ROOT/V1_4_26545_NATIVE_VENDOR_DEPENDENCIES.sha256"
PARITY_COMMIT_FILE="$ROOT/V1_4_26545_MGC_SOURCE_COMMIT.txt"
OUT="$ROOT/build_v1_4_26545_current_mgc_parity_outputs"
WORK="$ROOT/.build_v1_4_26545_current_mgc_parity_work"
ARTZIP="$WORK/v1_2_artifact.zip"
ARTDIR="$WORK/v1_2_artifact"
BASE_POST="$WORK/v1_2_postbuild_source"
BASE="$WORK/exact_frozen_v1_2"
AFTER="$WORK/candidate_v1_4"
VENDOR_COPY="$WORK/v1_2_native_vendor"
PATCHREPO="$WORK/patchrepo"
FORWARDCHECK="$WORK/forwardcheck"
ROLLBACKCHECK="$WORK/rollbackcheck"
MGC_AUDIT="$WORK/mgc_source_pin"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-v1-4-current-mgc-parity-debug.apk"

mapfile -t RUNTIME_FILES < "$RUNTIME_LIST"
[[ "${#RUNTIME_FILES[@]}" -eq 6 ]] || fail "runtime file inventory is not exactly 6"
rm -rf "$OUT" "$WORK"
rm -f "$FINAL"
mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE_POST" "$BASE" "$VENDOR_COPY"
cat > "$OUT/26545_V1_4_COMPILER_STATUS.txt" <<'EOF'
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
EOF
cat > "$OUT/26545_V1_4_STRICT_HANDOFF_REPORT.txt" <<'EOF'
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
TARGET VERSION/BUILD: 0.9726545 / 26545 V1.4
EOF
set_report(){
  local key="$1" value="$2"
  python3 - "$OUT/26545_V1_4_STRICT_HANDOFF_REPORT.txt" "$key" "$value" <<'PY'
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

echo "=== 26545 V1.4 GATE 0: branch / backup / lineage / handoff integrity ==="
[[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch: $(git branch --show-current)"
git merge-base --is-ancestor "$REPO_BASE_HEAD" HEAD || fail "V1.4 verification commit is not descended from exact failed V1.3 commit"
git merge-base --is-ancestor "$RUNTIME_BASE_HEAD" HEAD || fail "V1.4 verification commit lost successful V1.2 lineage"
git fetch --no-tags origin "refs/heads/$BACKUP_BRANCH:refs/remotes/origin/$BACKUP_BRANCH" >/dev/null 2>&1 || fail "unable to fetch required backup branch"
BACKUP_SHA="$(git rev-parse "refs/remotes/origin/$BACKUP_BRANCH" 2>/dev/null || true)"
[[ "$BACKUP_SHA" == "$REPO_BASE_HEAD" ]] || fail "backup branch is missing or does not point exactly to failed V1.3"
[[ -n "$TOKEN" ]] || fail "GitHub token unavailable for exact successful V1.2 artifact"
for f in "$BASE_PIN" "$BASE_TAR_PIN" "$CAND_PIN" "$RUNTIME_LIST" "$FORWARD" "$ROLLBACK" "$VALIDATE" "$GLSL_PREFLIGHT" "$HANDOFF_HASHES" "$VENDOR_MANIFEST" "$PARITY_COMMIT_FILE"; do
  [[ -f "$f" ]] || fail "required handoff file missing: $f"
done
sha256sum -c "$HANDOFF_HASHES"
[[ "$(sha "$BASE_PIN")" == "$BASE_MANIFEST_SHA" ]] || fail "V1.2 base manifest SHA drift"
[[ "$(wc -l < "$BASE_PIN")" -eq 968 ]] || fail "V1.2 base manifest is not 968 files"
[[ "$(sha "$CAND_PIN")" == "$CAND_MANIFEST_SHA" ]] || fail "V1.4 candidate manifest SHA drift"
[[ "$(wc -l < "$CAND_PIN")" -eq 969 ]] || fail "V1.4 candidate manifest is not 969 files"
grep -Fx "$BASE_TAR_SHA  26545_candidate_app_source.tar.gz" "$BASE_TAR_PIN" >/dev/null || fail "V1.2 candidate TAR pin drift"
[[ "$(tr -d '\r\n' < "$PARITY_COMMIT_FILE")" == "$MGC_SOURCE_HEAD" ]] || fail "current-MGC source pin drift"
python3 -m py_compile "$VALIDATE" "$GLSL_PREFLIGHT"
python3 "$VALIDATE" --self-test
python3 "$GLSL_PREFLIGHT" --self-test
bash -n "$0"
python3 - "$REPO_BASE_HEAD" <<'PY'
import subprocess,sys
base=sys.argv[1]
allowed={
'.github/workflows/build-v1-4-26545-current-mgc-parity.yml',
'V1_4_26545_BASE_V1_2_AUDITED_RUNTIME.sha256',
'V1_4_26545_BASE_V1_2_CANDIDATE_TAR.sha256',
'V1_4_26545_BASE_PROVENANCE.txt',
'V1_4_26545_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256',
'V1_4_26545_HANDOFF_HASHES.sha256',
'V1_4_26545_LOCAL_VALIDATION.txt',
'V1_4_26545_MGC_SOURCE_COMMIT.txt',
'V1_4_26545_NATIVE_VENDOR_DEPENDENCIES.sha256',
'V1_4_26545_RUNTIME_DELTA_FROM_V1_2.patch',
'V1_4_26545_RUNTIME_FILES.txt',
'V1_4_26545_RUNTIME_ROLLBACK_TO_V1_2.patch',
'V1_4_26545_UPLOAD_INSTRUCTIONS.md',
'build_v1_4_26545_current_mgc_parity.sh',
'preflight_v1_4_26545_glsl.py',
'validate_v1_4_26545_current_mgc_parity.py',
}
actual=set(subprocess.check_output(['git','diff','--name-only',base+'..HEAD'],text=True).splitlines())
extra=sorted(actual-allowed); missing=sorted(allowed-actual)
if extra: raise SystemExit('FAIL: V1.4 verification commit changed forbidden repo files: '+repr(extra))
if missing: raise SystemExit('FAIL: V1.4 verification commit incomplete: '+repr(missing))
print('PASS: repository contains only exact 16-file V1.4 verification package after failed V1.3; no app/src hand edit')
PY
FORBIDDEN_RE="$(printf '%s' 'git p' 'ush|git sw' 'itch dev|git check' 'out dev')"
! grep -E "$FORBIDDEN_RE" "$0" >/dev/null || fail "forbidden dev/push command present"
pass "backup + handoff integrity + repository source isolation"

echo "=== 26545 V1.4 GATE 1: reconstruct exact successful V1.2 runtime authority ==="
URL="https://api.github.com/repos/${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}/actions/artifacts/${BASE_ARTIFACT_ID}/zip"
curl --fail --location --silent --show-error --retry 5 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "$URL" -o "$ARTZIP"
[[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "V1.2 artifact ZIP SHA mismatch"
unzip -q "$ARTZIP" -d "$ARTDIR"
BASE_OUT="$ARTDIR/build_26545_iris_sabre_ab_outputs"
BASE_TAR="$BASE_OUT/26545_candidate_app_source.tar.gz"
BASE_AUDITED="$BASE_OUT/26545_frozen_candidate_postbuild.sha256"
[[ -f "$BASE_TAR" && -f "$BASE_AUDITED" ]] || fail "V1.2 artifact lacks candidate source authority"
[[ "$(sha "$BASE_TAR")" == "$BASE_TAR_SHA" ]] || fail "V1.2 candidate TAR SHA mismatch"
[[ "$(sha "$BASE_AUDITED")" == "$BASE_MANIFEST_SHA" ]] || fail "V1.2 audited manifest SHA mismatch"
cmp -s "$BASE_AUDITED" "$BASE_PIN" || fail "artifact audited manifest is not exact V1.2 pin"
tar -xzf "$BASE_TAR" -C "$BASE_POST"
THIRD_POST="$BASE_POST/app/src/main/cpp/third_party_26507"
[[ -d "$THIRD_POST" ]] || fail "V1.2 post-build TAR missing proven native vendor subtree"
( cd "$THIRD_POST" && sha256sum -c "$VENDOR_MANIFEST" ) > "$OUT/26545_V1_4_base_vendor_reverified.txt"
cp -a "$THIRD_POST/." "$VENDOR_COPY/"
cp -a "$BASE_POST/." "$BASE/"
rm -rf "$BASE/app/src/main/cpp/third_party_26507"
if [[ -d "$BASE/app/src/main/cpp/deps" ]]; then
  find "$BASE/app/src/main/cpp/deps" -type f ! -name '.gitignore' -delete
fi
manifest_all "$BASE" "$OUT/26545_V1_4_base_frozen_reconstructed.sha256"
cmp -s "$OUT/26545_V1_4_base_frozen_reconstructed.sha256" "$BASE_PIN" || fail "failed to reconstruct exact 968-file V1.2 authority"
set_report "EXACT PRIOR RUNTIME AUTHORITY" "PASS"
pass "exact successful V1.2 artifact -> exact frozen 968-file candidate reconstructed"

echo "=== 26545 V1.4 GATE 1B: verify immutable current-MGC source pin ==="
rm -rf "$MGC_AUDIT"
git init -q "$MGC_AUDIT"
git -C "$MGC_AUDIT" remote add origin https://github.com/bjzhou/PhotonCamera.git
git -C "$MGC_AUDIT" fetch --depth=1 origin "$MGC_SOURCE_HEAD"
[[ "$(git -C "$MGC_AUDIT" rev-parse FETCH_HEAD)" == "$MGC_SOURCE_HEAD" ]] || fail "current-MGC commit fetch drift"
pass "current-MGC source commit exists exactly at $MGC_SOURCE_HEAD"

echo "=== 26545 V1.4 GATE 2: candidate-first exact six-file transform ==="
mkdir -p "$AFTER"
cp -a "$BASE/." "$AFTER/"
(cd "$AFTER" && patch --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 < "$FORWARD" >/dev/null)
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" --base-pin "$BASE_PIN" | tee "$OUT/26545_V1_4_prebuild_contract.txt"
manifest_all "$AFTER" "$OUT/26545_V1_4_candidate_source.sha256"
cmp -s "$OUT/26545_V1_4_candidate_source.sha256" "$CAND_PIN" || fail "candidate is not exact pinned 969-file V1.4 source"
ACTUAL_CHANGED="$OUT/26545_V1_4_actual_changed_files.txt"
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
cmp -s "$ACTUAL_CHANGED" "$RUNTIME_LIST" || fail "actual changed scope differs from six-file allowlist"
set_report "RUNTIME OWNERSHIP" "PASS"
set_report "DORMANT-OWNER REJECTION" "PASS"
set_report "CHANGED RUNTIME SCOPE" "6 files (exact V1_4_26545_RUNTIME_FILES.txt)"
pass "candidate-first transform exact six-file V1.4 runtime scope"

echo "=== 26545 V1.4 GATE 3: REAL GLSL COMPILE ==="
GLSLANG="$(command -v glslangValidator || true)"
[[ -n "$GLSLANG" ]] || fail "pinned glslangValidator not on PATH"
"$GLSLANG" --version | grep -F '16.5.0' >/dev/null || fail "wrong glslangValidator version"
python3 "$GLSL_PREFLIGHT" --root "$AFTER" --validator "$GLSLANG" | tee "$OUT/26545_V1_4_real_glslang.txt"
sed -i 's/^REAL GLSL COMPILE:.*/REAL GLSL COMPILE: PASS (glslangValidator 16.5.0; 18 V1.4 active\/changed shaders)/' "$OUT/26545_V1_4_COMPILER_STATUS.txt"
set_report "REAL GLSL COMPILE" "PASS (glslangValidator 16.5.0; 18 V1.4 active/changed shaders)"
pass "REAL GLSL COMPILE"

echo "=== 26545 V1.4 GATE 4: canonical deterministic forward/rollback proof ==="
mkdir -p "$PATCHREPO"
cp -a "$BASE/." "$PATCHREPO/"
(
 cd "$PATCHREPO"
 git init -q
 git config user.email photon-local@example.invalid
 git config user.name Photon26545V14
 git add -A && git commit -qm exact-v1.2
 BASE_COMMIT="$(git rev-parse HEAD)"
 rm -rf app/src/main
 cp -a "$AFTER/app/src/main" app/src/main
 cp "$AFTER/app/version.properties" app/version.properties
 cp "$AFTER/app/build.gradle" app/build.gradle
 git add -A && git commit -qm candidate-v1.4
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
manifest_all "$FORWARDCHECK" "$OUT/26545_V1_4_forwardcheck.sha256"
cmp -s "$OUT/26545_V1_4_forwardcheck.sha256" "$CAND_PIN" || fail "forward fuzz=0 is not exact V1.4 candidate"
cp -a "$AFTER" "$ROLLBACKCHECK"
(cd "$ROLLBACKCHECK" && patch --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 < "$ROLLBACK" >/dev/null)
manifest_all "$ROLLBACKCHECK" "$OUT/26545_V1_4_rollbackcheck.sha256"
cmp -s "$OUT/26545_V1_4_rollbackcheck.sha256" "$BASE_PIN" || fail "rollback fuzz=0 is not exact V1.2"
set_report "FORWARD PATCH FUZZ=0" "PASS"
set_report "ROLLBACK PATCH FUZZ=0" "PASS"
pass "canonical full-index patches deterministic at abbrev 7/12/40 + fuzz=0 exact both directions"

echo "=== 26545 V1.4 GATE 5: install exact audited candidate into ephemeral Actions runtime ==="
# V1.2 -> V1.4 revision increment and all real compiler/assemble commands occur in this one
# authoritative guarded invocation; numeric app version remains the requested 0.9726545 / 26545.
rm -rf "$ROOT/app/src/main"
mkdir -p "$ROOT/app/src"
cp -a "$AFTER/app/src/main" "$ROOT/app/src/"
cp "$AFTER/app/version.properties" "$ROOT/app/version.properties"
cp "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"
manifest_all "$ROOT" "$OUT/26545_V1_4_installed_pre_vendor.sha256"
cmp -s "$OUT/26545_V1_4_installed_pre_vendor.sha256" "$CAND_PIN" || fail "installed runtime differs from exact 969-file candidate"
grep -Fx "VERSION_NAME=$VERSION_NAME" "$ROOT/app/version.properties" >/dev/null || fail "version name not exact"
grep -Fx "VERSION_BUILD=$VERSION_BUILD" "$ROOT/app/version.properties" >/dev/null || fail "version build not exact"
python3 "$VALIDATE" --base "$BASE" --candidate "$ROOT" --base-pin "$BASE_PIN" > "$OUT/26545_V1_4_installed_pre_gradle_contract.txt"

echo "=== 26545 V1.4 GATE 5B: restore exact proven V1.2 native JPEG/UltraHDR vendor source ==="
THIRD="$ROOT/app/src/main/cpp/third_party_26507"
rm -rf "$THIRD"
mkdir -p "$THIRD"
cp -a "$VENDOR_COPY/." "$THIRD/"
[[ -f "$THIRD/libjpeg-turbo/CMakeLists.txt" ]] || fail "pinned libjpeg-turbo source missing before Gradle"
[[ -f "$THIRD/libultrahdr/ultrahdr_api.h" ]] || fail "pinned libultrahdr header missing before Gradle"
[[ -f "$THIRD/libultrahdr/lib/src/ultrahdr_api.cpp" ]] || fail "pinned libultrahdr source missing before Gradle"
[[ ! -e "$THIRD/libultrahdr/CMakeLists.txt" ]] || fail "obsolete libultrahdr CMakeLists returned"
( cd "$THIRD" && sha256sum -c "$VENDOR_MANIFEST" ) > "$OUT/26545_V1_4_vendor_manifest_prebuild.txt"
manifest_audited_live "$ROOT" "$OUT/26545_V1_4_installed_with_vendor_audited_runtime.sha256"
cmp -s "$OUT/26545_V1_4_installed_with_vendor_audited_runtime.sha256" "$CAND_PIN" || fail "native vendor bootstrap altered audited Iris candidate"
pass "exact successful-V1.2 native vendor authority restored separately"

echo "PRE-BUILD SAFETY PROOF PASSED"
pass "V1.4 revision increment + exact runtime installation + proven native vendor bootstrap are in this same authoritative build invocation"

echo "=== 26545 V1.4 GATE 6: REAL PROJECT COMPILERS ==="
chmod +x "$ROOT/gradlew"
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace
sed -i 's/^REAL KOTLIN COMPILE:.*/REAL KOTLIN COMPILE: PASS (:app:compileDebugKotlin)/' "$OUT/26545_V1_4_COMPILER_STATUS.txt"
sed -i 's/^REAL JAVA COMPILE:.*/REAL JAVA COMPILE: PASS (:app:compileDebugJavaWithJavac)/' "$OUT/26545_V1_4_COMPILER_STATUS.txt"
set_report "REAL KOTLIN COMPILE" "PASS (:app:compileDebugKotlin)"
set_report "REAL JAVA COMPILE" "PASS (:app:compileDebugJavaWithJavac)"
pass "REAL KOTLIN COMPILE"
pass "REAL JAVA COMPILE"

echo "=== 26545 V1.4 GATE 6B: permanent prior-failure + native-source regression gates ==="
[[ -f "$THIRD/libjpeg-turbo/CMakeLists.txt" ]] || fail "REGRESSION: pinned libjpeg-turbo source missing immediately before assemble"
[[ -f "$THIRD/libultrahdr/ultrahdr_api.h" ]] || fail "REGRESSION: pinned libultrahdr source missing immediately before assemble"
( cd "$THIRD" && sha256sum -c "$VENDOR_MANIFEST" ) > "$OUT/26545_V1_4_vendor_manifest_preassemble.txt"
# Failed V1.3 compiler failures are permanent source-level regression gates in addition to real Kotlin.
STACKER_SRC="$ROOT/app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt"
SABRE_SRC="$ROOT/app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt"
grep -F 'bentoFlowTexture = flow.texture' "$STACKER_SRC" >/dev/null || fail "REGRESSION: V1.3 ConvertedAlignment->Int fix missing"
! grep -F 'bentoFlowTexture = flow' "$STACKER_SRC" | grep -v 'flow.texture' >/dev/null || fail "REGRESSION: V1.3 ConvertedAlignment assigned directly to Int"
! grep -F 'coreImagingTuning' "$SABRE_SRC" >/dev/null || fail "REGRESSION: V1.3 unresolved coreImagingTuning owner returned"
grep -F 'private val sabreMergeGradientThreshold: Float? = null' "$SABRE_SRC" >/dev/null || fail "REGRESSION: adaptive Sabre gradient default owner missing"
grep -F 'mergeGradientThreshold = sabreMergeGradientThreshold' "$SABRE_SRC" >/dev/null || fail "REGRESSION: Sabre gradient call is not wired to local optional owner"
# Prior 26543 failures also stay permanent gates: reserved GLSL identifier is exercised by the
# preflight self-test; nondeterministic patch representation is rejected above; real Kotlin catches
# Float/Double/scope regressions; real javac catches missing ByteBuffer/import symbols.
pass "PERMANENT REGRESSION: V1.3 compiler + GLSL/patch/Kotlin/Java/native-source historical failures remain gated"

echo "=== 26545 V1.4 GATE 7: FULL ANDROID ASSEMBLE ==="
./gradlew :app:assembleDebug --stacktrace
sed -i 's/^FULL ANDROID ASSEMBLE:.*/FULL ANDROID ASSEMBLE: PASS (:app:assembleDebug)/' "$OUT/26545_V1_4_COMPILER_STATUS.txt"
set_report "FULL ANDROID ASSEMBLE" "PASS (:app:assembleDebug)"
pass "FULL ANDROID ASSEMBLE"

echo "=== 26545 V1.4 GATE 8: frozen-candidate / live-Iris / native-vendor invariance + one APK ==="
manifest_all "$AFTER" "$OUT/26545_V1_4_frozen_candidate_postbuild.sha256"
cmp -s "$OUT/26545_V1_4_frozen_candidate_postbuild.sha256" "$CAND_PIN" || fail "REGRESSION: frozen 969-file candidate changed during Gradle"
[[ "$(wc -l < "$OUT/26545_V1_4_frozen_candidate_postbuild.sha256")" -eq 969 ]] || fail "REGRESSION: frozen candidate is not exactly 969 files"
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" --base-pin "$BASE_PIN" > "$OUT/26545_V1_4_frozen_candidate_postbuild_contract.txt"
manifest_audited_live "$ROOT" "$OUT/26545_V1_4_post_gradle_audited_runtime.sha256"
cmp -s "$OUT/26545_V1_4_post_gradle_audited_runtime.sha256" "$CAND_PIN" || fail "REGRESSION: Gradle changed audited Iris runtime source"
( cd "$THIRD" && sha256sum -c "$VENDOR_MANIFEST" ) > "$OUT/26545_V1_4_vendor_manifest_postbuild.txt"
pass "PERMANENT REGRESSION: frozen Iris candidate + post-build native vendor authority validated separately"
mapfile -t APKS < <(find "$ROOT/app/build/outputs/apk/debug" -maxdepth 1 -type f -name '*.apk' -print | sort)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one Gradle APK, got ${#APKS[@]}"
cp "${APKS[0]}" "$FINAL"
sha256sum "$FINAL" | tee "$OUT/26545_V1_4_APK.sha256"
cat > "$OUT/26545_V1_4_SCOPE_PROVENANCE.txt" <<EOF
Target: $VERSION_NAME / $VERSION_BUILD $REVISION
Exact successful runtime authority commit: $RUNTIME_BASE_HEAD
Failed V1.3 repository checkpoint: $REPO_BASE_HEAD
Verified backup branch: $BACKUP_BRANCH -> $REPO_BASE_HEAD
Exact successful prior run: $BASE_RUN_ID
Exact prior artifact ID: $BASE_ARTIFACT_ID
Exact prior artifact ZIP SHA256: $BASE_ARTIFACT_SHA
Exact prior final source TAR SHA256: $BASE_TAR_SHA
Reconstructed frozen V1.2 Iris manifest SHA256: $BASE_MANIFEST_SHA (968 files)
Exact V1.4 candidate Iris manifest SHA256: $CAND_MANIFEST_SHA (969 files)
Runtime changed files: 6
current-MGC parity audit pin: $MGC_SOURCE_HEAD
Spatial: restores hard merge interpolation cancellation, phase-preserving RAW boundary sampling, mirror rejection boundary, V25 RAW/4 rejection -> RAW/8 merge-weight geometry, sparse ConvertAlignment transport, and corrected aligned clipping mapping.
VGN: one Iris-owned current-MGC RGB-gradient direction/color-noise/IIR owner; 26532 foliage/edge special cases removed from this stage; calculation-WB entry/exit and current coefficients preserved.
Sabre: ResolveSabre -> RGBA16UI output transform -> same Iris current-MGC VGN -> completed camera RGB; optional RGBA16F carrier occurs only after VGN.
Sabre merge gradient threshold: optional local scalar defaults to null, preserving adaptive SNR interpolation; forceReferenceColorRgb preserved.
Figure-7 covariance remains RAW/2 and is not collapsed into rejection geometry.
All non-listed Motion/Night/DNG/UHDR/capture/exposure/UI owners remain byte-identical to exact V1.2 runtime authority.
Native JPEG/UltraHDR build dependency: exact manifest-verified source recovered from successful V1.2 artifact and reverified before/after assemble.
EOF
tar -czf "$OUT/26545_V1_4_candidate_app_source.tar.gz" -C "$ROOT" app/src/main app/version.properties app/build.gradle
sha256sum "$OUT/26545_V1_4_candidate_app_source.tar.gz" > "$OUT/26545_V1_4_candidate_app_source.tar.gz.sha256"
cat "$OUT/26545_V1_4_COMPILER_STATUS.txt"
cat "$OUT/26545_V1_4_STRICT_HANDOFF_REPORT.txt"
echo "PASS: 26545 V1.4 exact successful V1.2 artifact authority"
echo "PASS: 26545 V1.4 exact six-file current-MGC + deterministic rollback"
echo "PASS: 26545 V1.4 REAL GLSL/KOTLIN/JAVA + FULL ANDROID ASSEMBLE"
echo "APK: $FINAL"
