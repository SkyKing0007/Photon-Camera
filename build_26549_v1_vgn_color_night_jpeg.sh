#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }

manifest_audited(){
  local root="$1" out="$2"
  (cd "$root" && {
    find app/src/main -type f \
      ! -path 'app/src/main/cpp/third_party_26507/*' \
      ! -path 'app/src/main/cpp/deps/*' -print
    [[ -f app/src/main/cpp/deps/.gitignore ]] && echo app/src/main/cpp/deps/.gitignore
    echo app/version.properties
    echo app/build.gradle
  } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done) > "$out"
}

vendor_manifest(){
  local root="$1" out="$2"
  (cd "$root" && {
    [[ -d app/src/main/cpp/third_party_26507 ]] && find app/src/main/cpp/third_party_26507 -type f -print
    [[ -d app/src/main/cpp/deps ]] && find app/src/main/cpp/deps -type f -print
  } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done) > "$out"
}

exact_tree_equal(){
  python3 - "$1" "$2" <<'PY'
from pathlib import Path
import hashlib,sys
def m(root):
 root=Path(root); d={}
 for p in root.rglob('*'):
  if p.is_file() and '.git' not in p.parts:
   d[p.relative_to(root).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
 return d
ma,mb=m(sys.argv[1]),m(sys.argv[2])
if ma!=mb:
 bad=[k for k in sorted(set(ma)|set(mb)) if ma.get(k)!=mb.get(k)]
 raise SystemExit('tree mismatch: '+repr(bad[:30]))
PY
}

ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
REPO_BASE_HEAD="5b2b6a791d18fd0c5ff2eef4cd147619176a0d81"
BASE_SUCCESS_COMMIT="5b2b6a791d18fd0c5ff2eef4cd147619176a0d81"
BASE_RUN_ID="33112963353"
BASE_ARTIFACT_ID="9663418274"
BASE_ARTIFACT_NAME="photon-26548-v1-2-night-owner-contract"
BASE_ARTIFACT_SHA="4cfe83bddd72ef7f9b2f9fbc14fb281121595ff95fa442e2ab7abf4f087f1b60"
BASE_TAR_SHA="ec9f745c00f66e56b2a289a987b7ec8e955098b7969cc1455bc47b0926e3e531"
BASE_MANIFEST_SHA="b0ba7f1024c85bafef8422386b5eb89c0228adec5b842cc7bb8f8a0256654e4f"
CAND_MANIFEST_SHA="717f10740b832c9feee6854cb974ded8e181dd992ffe0ab5d8b9be5f55997374"
BASE_APK_SHA="b789c32ef1f791dffaff09d4002dd4036415796c0733687c16e47ce5fb34cbe4"
VERSION_NAME="0.9726549"
VERSION_BUILD="26549"
REVISION="V1"
GLSLANG_PKG_VERSION="15.1.0-2~ubuntu0.24.04.2"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"

BASE_PIN="$ROOT/V1_26549_BASE_26548_V1_2_AUDITED_RUNTIME.sha256"
BASE_TAR_PIN="$ROOT/V1_26549_BASE_26548_V1_2_CANDIDATE_TAR.sha256"
CAND_PIN="$ROOT/V1_26549_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256"
RUNTIME_LIST="$ROOT/V1_26549_RUNTIME_FILES.txt"
PREWRITE_HASHES="$ROOT/V1_26549_PREWRITE_CHANGED_SOURCE_HASHES.sha256"
FORWARD="$ROOT/V1_26549_RUNTIME_DELTA_FROM_26548_V1_2.patch"
ROLLBACK="$ROOT/V1_26549_RUNTIME_ROLLBACK_TO_26548_V1_2.patch"
VALIDATE="$ROOT/validate_26549_v1_vgn_color_night_jpeg.py"
EXTRACT="$ROOT/extract_26549_vgn_shaders.py"
HANDOFF_HASHES="$ROOT/V1_26549_HANDOFF_HASHES.sha256"
VENDOR_MANIFEST="$ROOT/V1_26549_NATIVE_VENDOR_DEPENDENCIES.sha256"
OUT="$ROOT/build_26549_v1_vgn_color_night_jpeg_outputs"
WORK="$ROOT/.build_26549_v1_vgn_color_night_jpeg_work"
ARTZIP="$WORK/26548_v1_2_artifact.zip"
ARTDIR="$WORK/26548_v1_2_artifact"
BASE="$WORK/exact_26548_v1_2_compiled_candidate"
AFTER="$WORK/candidate_26549_v1"
PATCHREPO="$WORK/patchrepo"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-v1-vgn-color-night-jpeg-debug.apk"

mapfile -t RUNTIME_FILES < "$RUNTIME_LIST"
[[ "${#RUNTIME_FILES[@]}" -eq 4 ]] || fail "runtime file inventory is not exactly 4"
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER"

cat > "$OUT/26549_V1_COMPILER_STATUS.txt" <<'EOF'
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF
cat > "$OUT/26549_V1_STRICT_HANDOFF_REPORT.txt" <<'EOF'
EXACT PRIOR RUNTIME AUTHORITY: NOT RUN
CHANGED RUNTIME SCOPE: NOT RUN
VGN FULL ARTIFACT AUTHORITY: NOT RUN
VGN TRUE-COLOR CONSERVATION: NOT RUN
VGN ERROR-GATED FINAL IIR: NOT RUN
NIGHT EXPLICIT JPEG TARGET: NOT RUN
NIGHT JPEG CODEC DIAGNOSTICS: NOT RUN
26548 V1.2 OWNER FIX PRESERVATION: NOT RUN
MOTION PUBLICATION INVARIANCE: NOT RUN
REAL GLSL COMPILE: NOT RUN
REAL KOTLIN COMPILE: NOT RUN
REAL JAVA COMPILE: NOT RUN
FULL ANDROID ASSEMBLE: NOT RUN
FORWARD PATCH FUZZ=0: NOT RUN
ROLLBACK PATCH FUZZ=0: NOT RUN
POST-BUILD INVARIANCE: NOT RUN
CLEAN ARTIFACT SOURCE EXPORT: NOT RUN
BACKUP BRANCH: NOT REQUIRED (explicit user instruction; canonical forward/rollback patch safety)
TARGET VERSION/BUILD: 0.9726549 / 26549 V1
EOF
set_report(){ python3 - "$OUT/26549_V1_STRICT_HANDOFF_REPORT.txt" "$1" "$2" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); key=sys.argv[2]; val=sys.argv[3]; lines=p.read_text().splitlines(); found=False
for i,x in enumerate(lines):
 if x.startswith(key+':'): lines[i]=key+': '+val; found=True; break
if not found: raise SystemExit('missing report key '+key)
p.write_text('\n'.join(lines)+'\n')
PY
}

echo "=== 26549 GATE 0: sealed handoff / branch / workflow scope ==="
[[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
git merge-base --is-ancestor "$REPO_BASE_HEAD" HEAD || fail "not descended from exact successful 26548 V1.2 handoff commit"
[[ -n "$TOKEN" ]] || fail "GitHub token unavailable"
sha256sum -c "$HANDOFF_HASHES"
python3 -m py_compile "$VALIDATE" "$EXTRACT"
python3 "$VALIDATE" --self-test
bash -n "$0"
[[ "$(sha "$BASE_PIN")" == "$BASE_MANIFEST_SHA" ]] || fail "base manifest SHA drift"
[[ "$(wc -l < "$BASE_PIN")" -eq 969 ]] || fail "base manifest count"
[[ "$(sha "$CAND_PIN")" == "$CAND_MANIFEST_SHA" ]] || fail "candidate manifest SHA drift"
[[ "$(wc -l < "$CAND_PIN")" -eq 969 ]] || fail "candidate manifest count"
grep -F "$BASE_TAR_SHA" "$BASE_TAR_PIN" >/dev/null || fail "base TAR pin drift"
python3 - "$REPO_BASE_HEAD" <<'PY'
import subprocess,sys
base=sys.argv[1]
allowed={
'.github/workflows/build-26549-v1-vgn-color-night-jpeg.yml',
'V1_26549_BASE_26548_V1_2_AUDITED_RUNTIME.sha256','V1_26549_BASE_26548_V1_2_CANDIDATE_TAR.sha256',
'V1_26549_BASE_PROVENANCE.txt','V1_26549_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256',
'V1_26549_HANDOFF_HASHES.sha256','V1_26549_LOCAL_VALIDATION.txt','V1_26549_NATIVE_VENDOR_DEPENDENCIES.sha256',
'V1_26549_PREWRITE_CHANGED_SOURCE_HASHES.sha256','V1_26549_RUNTIME_DELTA_FROM_26548_V1_2.patch',
'V1_26549_RUNTIME_FILES.txt','V1_26549_RUNTIME_ROLLBACK_TO_26548_V1_2.patch','V1_26549_UPLOAD_INSTRUCTIONS.md',
'build_26549_v1_vgn_color_night_jpeg.sh','extract_26549_vgn_shaders.py','validate_26549_v1_vgn_color_night_jpeg.py'}
actual=set(subprocess.check_output(['git','diff','--name-only',base+'..HEAD'],text=True).splitlines())
if actual!=allowed: raise SystemExit('handoff scope mismatch extra=%r missing=%r'%(sorted(actual-allowed),sorted(allowed-actual)))
print('PASS: exactly 16-file 26549 handoff; repository app/src untouched')
PY
! git diff --name-only "$REPO_BASE_HEAD..HEAD" | grep -E '^app/' >/dev/null || fail "handoff directly changed app source"
pass "sealed handoff and non-overlapping candidate-first source ownership"

echo "=== 26549 GATE 1: recover exact successful compiled 26548 V1.2 authority ==="
REPO_API="https://api.github.com/repos/${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}"
RUN_META="$WORK/base_run.json"
curl --fail --location --silent --show-error --retry 5 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "$REPO_API/actions/runs/${BASE_RUN_ID}" -o "$RUN_META"
python3 - "$RUN_META" "$BASE_RUN_ID" "$BASE_SUCCESS_COMMIT" "$EXPECTED_BRANCH" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); assert str(d.get('id'))==sys.argv[2]; assert d.get('conclusion')=='success'; assert d.get('head_sha')==sys.argv[3]; assert d.get('head_branch')==sys.argv[4]
print('PASS exact 26548 V1.2 run success/commit/branch')
PY
curl --fail --location --silent --show-error --retry 5 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "$REPO_API/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"
[[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "base artifact ZIP SHA mismatch"
unzip -q "$ARTZIP" -d "$ARTDIR"
BASE_OUT="$ARTDIR/build_26548_v1_2_night_owner_contract_outputs"
BASE_TAR="$BASE_OUT/26548_V1_2_candidate_app_source.tar.gz"
BASE_AUDITED="$BASE_OUT/26548_V1_2_candidate_source.sha256"
BASE_APK_HASH="$BASE_OUT/26548_V1_2_APK.sha256"
BASE_COMPILER="$BASE_OUT/26548_V1_2_COMPILER_STATUS.txt"
BASE_REPORT="$BASE_OUT/26548_V1_2_STRICT_HANDOFF_REPORT.txt"
for f in "$BASE_TAR" "$BASE_AUDITED" "$BASE_APK_HASH" "$BASE_COMPILER" "$BASE_REPORT"; do [[ -f "$f" ]] || fail "base artifact missing $f"; done
[[ "$(sha "$BASE_TAR")" == "$BASE_TAR_SHA" ]] || fail "base TAR SHA mismatch"
[[ "$(sha "$BASE_AUDITED")" == "$BASE_MANIFEST_SHA" ]] || fail "base manifest SHA mismatch"
cmp -s "$BASE_AUDITED" "$BASE_PIN" || fail "base manifest bytes differ"
grep -F "$BASE_APK_SHA" "$BASE_APK_HASH" >/dev/null || fail "base APK hash mismatch"
for proof in 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do grep -F "$proof" "$BASE_COMPILER" >/dev/null || fail "missing persisted base proof $proof"; done
for proof in 'RUNTIME OWNERSHIP: PASS' 'NIGHT SABRE OWNER-AWARE POST GRAPH: PASS' 'SPATIAL NODE CROSS-OWNER REJECTION: PASS' 'LEGACY NIGHT ROUTE REJECTION: PASS' 'POST-BUILD INVARIANCE: PASS' 'CLEAN ARTIFACT SOURCE EXPORT: PASS' 'TARGET VERSION/BUILD: 0.9726548 / 26548 V1.2'; do grep -F "$proof" "$BASE_REPORT" >/dev/null || fail "missing base report proof $proof"; done
tar -xzf "$BASE_TAR" -C "$BASE"
manifest_audited "$BASE" "$OUT/26549_base_reconstructed.sha256"; cmp -s "$OUT/26549_base_reconstructed.sha256" "$BASE_PIN" || fail "base reconstruction mismatch"
vendor_manifest "$BASE" "$OUT/26549_vendor_base.txt"; cmp -s "$OUT/26549_vendor_base.txt" "$VENDOR_MANIFEST" || fail "base vendor mismatch"
(cd "$BASE" && sha256sum -c "$PREWRITE_HASHES") > "$OUT/26549_prewrite_hashes_verified.txt"
set_report "EXACT PRIOR RUNTIME AUTHORITY" "PASS (run ${BASE_RUN_ID}, artifact ${BASE_ARTIFACT_ID}, compiled V1.2)"
pass "exact successful 26548 V1.2 compiled candidate recovered"

echo "=== 26549 GATE 2: candidate-first exact four-file transform ==="
rsync -a --delete "$BASE/" "$AFTER/"
(cd "$AFTER" && patch --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 < "$FORWARD" >/dev/null)
python3 "$VALIDATE" "$BASE" "$AFTER" | tee "$OUT/26549_runtime_contract.txt"
manifest_audited "$AFTER" "$OUT/26549_candidate_source.sha256"; cmp -s "$OUT/26549_candidate_source.sha256" "$CAND_PIN" || fail "candidate manifest mismatch"
python3 - "$BASE" "$AFTER" "$OUT/26549_actual_changed_files.txt" <<'PY'
from pathlib import Path
import hashlib,sys
def m(r):
 d={}; r=Path(r)
 for p in r.rglob('*'):
  if p.is_file(): d[p.relative_to(r).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
 return d
b,c=m(sys.argv[1]),m(sys.argv[2]); ch=sorted(k for k in set(b)|set(c) if b.get(k)!=c.get(k)); Path(sys.argv[3]).write_text('\n'.join(ch)+'\n')
PY
cmp -s "$OUT/26549_actual_changed_files.txt" "$RUNTIME_LIST" || fail "changed allowlist mismatch"
set_report "CHANGED RUNTIME SCOPE" "PASS (exact four files)"
set_report "VGN FULL ARTIFACT AUTHORITY" "PASS (strength=1 and zero color confidence reproduces full correction authority)"
set_report "VGN TRUE-COLOR CONSERVATION" "PASS (coherent pre-median hue/magnitude support protects real chroma)"
set_report "VGN ERROR-GATED FINAL IIR" "PASS (IIR1/error unchanged; IIR3 uses existing 100..300 error domain)"
set_report "NIGHT EXPLICIT JPEG TARGET" "PASS (.jpg destination, Night only)"
set_report "NIGHT JPEG CODEC DIAGNOSTICS" "PASS (target/TurboJPEG/Android fallback persisted)"
set_report "26548 V1.2 OWNER FIX PRESERVATION" "PASS"
set_report "MOTION PUBLICATION INVARIANCE" "PASS (Hdrx/Motion/native JPEG files byte-identical)"
pass "26549 semantic/runtime contract"

echo "=== 26549 GATE 3: deterministic forward/rollback BEFORE live source write ==="
rm -rf "$PATCHREPO" "$WORK/forwardcheck" "$WORK/rollbackcheck"; rsync -a "$BASE/" "$PATCHREPO/"
(cd "$PATCHREPO"; git init -q; git config user.name Photon26549; git config user.email photon26549@example.invalid; git add -A; git commit -qm base; rsync -a --delete --exclude=.git "$AFTER/" "$PATCHREPO/"; for a in 7 12 40; do git -c core.abbrev="$a" diff --binary --full-index --no-ext-diff > "$WORK/f.$a"; cmp -s "$WORK/f.$a" "$FORWARD" || fail "forward nondeterministic $a"; done; git add -A; git commit -qm candidate; rsync -a --delete --exclude=.git "$BASE/" "$PATCHREPO/"; for a in 7 12 40; do git -c core.abbrev="$a" diff --binary --full-index --no-ext-diff > "$WORK/r.$a"; cmp -s "$WORK/r.$a" "$ROLLBACK" || fail "rollback nondeterministic $a"; done)
rsync -a "$BASE/" "$WORK/forwardcheck/"; (cd "$WORK/forwardcheck" && patch --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 < "$FORWARD" >/dev/null); exact_tree_equal "$WORK/forwardcheck" "$AFTER"
rsync -a "$AFTER/" "$WORK/rollbackcheck/"; (cd "$WORK/rollbackcheck" && patch --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 < "$ROLLBACK" >/dev/null); exact_tree_equal "$WORK/rollbackcheck" "$BASE"
set_report "FORWARD PATCH FUZZ=0" "PASS (core.abbrev 7/12/40 byte-identical)"; set_report "ROLLBACK PATCH FUZZ=0" "PASS (core.abbrev 7/12/40 byte-identical)"
pass "patch determinism and exact rollback"

echo "=== 26549 GATE 4: install exact candidate into ephemeral Actions checkout ==="
rsync -a --delete "$AFTER/app/" "$ROOT/app/"
manifest_audited "$ROOT" "$OUT/26549_installed_precompiler.sha256"; cmp -s "$OUT/26549_installed_precompiler.sha256" "$CAND_PIN" || fail "installed candidate mismatch"
vendor_manifest "$ROOT" "$OUT/26549_vendor_precompiler.txt"; cmp -s "$OUT/26549_vendor_precompiler.txt" "$VENDOR_MANIFEST" || fail "vendor drift before compiler"
grep -Fx 'VERSION_NAME=0.9726549' app/version.properties >/dev/null; grep -Fx 'VERSION_BUILD=26549' app/version.properties >/dev/null
pass "version increment and candidate installation are in this same build invocation"

echo "=== 26549 GATE 5: pinned REAL glslangValidator for modified embedded active GLSL ==="
sudo apt-get update -qq
apt-cache madison glslang-tools | grep -F "$GLSLANG_PKG_VERSION" >/dev/null || fail "pinned glslang package unavailable"
sudo apt-get install -y --no-install-recommends "glslang-tools=${GLSLANG_PKG_VERSION}"
[[ "$(dpkg-query -W -f='${Version}' glslang-tools)" == "$GLSLANG_PKG_VERSION" ]] || fail "glslang package version mismatch"
glslangValidator --version | tee "$OUT/26549_glslang_version.txt"
SHDIR="$WORK/26549_embedded_glsl"; python3 "$EXTRACT" "$AFTER/app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt" "$SHDIR" | tee "$OUT/26549_shader_extraction.txt"
for sh in "$SHDIR/directionalSmooth.comp" "$SHDIR/iirRgb.comp"; do glslangValidator -S comp "$sh" | tee -a "$OUT/26549_glslang_compile.txt"; done
sed -i 's/REAL GLSL COMPILE: NOT RUN YET/REAL GLSL COMPILE: PASS (pinned glslangValidator 15.1.0-2~ubuntu0.24.04.2; 2 modified embedded compute shaders)/' "$OUT/26549_V1_COMPILER_STATUS.txt"
set_report "REAL GLSL COMPILE" "PASS (pinned 15.1.0-2~ubuntu0.24.04.2; directionalSmooth + iirRgb)"
pass "real pinned glslang"

echo "=== 26549 GATE 6: REAL Kotlin + Java compilers ==="
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace
sed -i 's/REAL KOTLIN COMPILE: NOT RUN YET/REAL KOTLIN COMPILE: PASS/' "$OUT/26549_V1_COMPILER_STATUS.txt"; sed -i 's/REAL JAVA COMPILE: NOT RUN YET/REAL JAVA COMPILE: PASS/' "$OUT/26549_V1_COMPILER_STATUS.txt"
set_report "REAL KOTLIN COMPILE" "PASS"; set_report "REAL JAVA COMPILE" "PASS"
grep -F 'java.nio.ByteBuffer source = plane.getBuffer().duplicate();' app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java >/dev/null || fail "permanent 26545 javac ByteBuffer regression"
python3 "$VALIDATE" "$BASE" "$AFTER" > "$OUT/26549_postcompiler_contract.txt"
pass "real project language compilers"

echo "=== 26549 GATE 7: FULL assemble / exactly one APK ==="
./gradlew :app:assembleDebug --stacktrace
mapfile -t APKS < <(find app/build/outputs/apk/debug -maxdepth 1 -type f -name '*.apk' | LC_ALL=C sort)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one APK; found ${#APKS[@]}"
cp "${APKS[0]}" "$FINAL"; [[ -s "$FINAL" ]] || fail "final APK empty"; sha256sum "$FINAL" > "$OUT/26549_V1_APK.sha256"
sed -i 's/FULL ANDROID ASSEMBLE: NOT RUN YET/FULL ANDROID ASSEMBLE: PASS/' "$OUT/26549_V1_COMPILER_STATUS.txt"; set_report "FULL ANDROID ASSEMBLE" "PASS"
pass "full Android assemble"

echo "=== 26549 GATE 8: post-build invariance + export exact next authority ==="
manifest_audited "$ROOT" "$OUT/26549_postbuild_runtime.sha256"; cmp -s "$OUT/26549_postbuild_runtime.sha256" "$CAND_PIN" || fail "runtime source changed during build"
manifest_audited "$AFTER" "$OUT/26549_frozen_candidate_postbuild.sha256"; cmp -s "$OUT/26549_frozen_candidate_postbuild.sha256" "$CAND_PIN" || fail "frozen candidate changed"
vendor_manifest "$ROOT" "$OUT/26549_vendor_postbuild.txt"; cmp -s "$OUT/26549_vendor_postbuild.txt" "$VENDOR_MANIFEST" || fail "native/vendor changed"
python3 "$VALIDATE" "$BASE" "$AFTER" > "$OUT/26549_postbuild_contract.txt"
sed -i 's/POST-BUILD INVARIANCE: NOT RUN YET/POST-BUILD INVARIANCE: PASS/' "$OUT/26549_V1_COMPILER_STATUS.txt"; set_report "POST-BUILD INVARIANCE" "PASS"
tar -czf "$OUT/26549_V1_candidate_app_source.tar.gz" -C "$AFTER" app
sha256sum "$OUT/26549_V1_candidate_app_source.tar.gz" > "$OUT/26549_V1_candidate_app_source.tar.gz.sha256"
cp "$CAND_PIN" "$OUT/26549_V1_candidate_source.sha256"; cp "$RUNTIME_LIST" "$OUT/26549_V1_actual_runtime_scope.txt"; set_report "CLEAN ARTIFACT SOURCE EXPORT" "PASS"
cat >> "$OUT/26549_V1_STRICT_HANDOFF_REPORT.txt" <<EOF
FINAL APK: $(basename "$FINAL")
FINAL APK SHA-256: $(sha "$FINAL")
BASE RUN/ARTIFACT: ${BASE_RUN_ID} / ${BASE_ARTIFACT_ID}
BASE ARTIFACT SHA-256: ${BASE_ARTIFACT_SHA}
BASE CANDIDATE TAR SHA-256: ${BASE_TAR_SHA}
BASE AUDITED MANIFEST SHA-256: ${BASE_MANIFEST_SHA}
CANDIDATE AUDITED MANIFEST SHA-256: ${CAND_MANIFEST_SHA}
EOF
cat "$OUT/26549_V1_COMPILER_STATUS.txt"; cat "$OUT/26549_V1_STRICT_HANDOFF_REPORT.txt"
echo "PRE-BUILD SAFETY PROOF PASSED"
echo "26549 V1 BUILD SUCCESS"
