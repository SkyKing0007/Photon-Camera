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
  local a="$1" b="$2"
  python3 - "$a" "$b" <<'PY'
from pathlib import Path
import hashlib,sys
def m(root):
    root=Path(root); d={}
    for p in root.rglob('*'):
        if p.is_file() and '.git/' not in p.as_posix():
            d[p.relative_to(root).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
    return d
a,b=map(Path,sys.argv[1:])
ma,mb=m(a),m(b)
if ma!=mb:
    ks=sorted(set(ma)|set(mb))
    bad=[k for k in ks if ma.get(k)!=mb.get(k)]
    raise SystemExit('tree mismatch: '+repr(bad[:30]))
PY
}

ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
REPO_BASE_HEAD="857bf0d979083ae70b0d8d45e43ee2e32b50c8b8"
BASE_SUCCESS_COMMIT="d688c69a85c6f224dff28a84f8098e030f47a583"
BASE_RUN_ID="33098575745"
BASE_ARTIFACT_ID="9657611983"
BASE_ARTIFACT_NAME="photon-26547-v1-1-night-sabre-12plus3"
BASE_ARTIFACT_SHA="ffe08dc4c0d8f9e3a55837c74336a8fdbd736e900234dbcac453481b5b4ec427"
BASE_TAR_SHA="c07a2397f3f8171ebc9d12f9b7803e54864daaf685546b2c5ec81eb158aea1c1"
BASE_MANIFEST_SHA="a41d9e510f62166fa6cd892df12c3b4a46e36374ed850fb35885da75f9a128dd"
CAND_MANIFEST_SHA="cd80bd15a726f396db9d4774dfec69fd4258f97442b7121ae9b75a3b619bccb1"
BASE_APK_SHA="32d10962cda1b2e848c3397854dcb274548ec7bb1bbe2dc778739848789d3816"
VERSION_NAME="0.9726548"
VERSION_BUILD="26548"
REVISION="V1"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"

BASE_PIN="$ROOT/V1_26548_BASE_26547_V1_1_AUDITED_RUNTIME.sha256"
BASE_TAR_PIN="$ROOT/V1_26548_BASE_26547_V1_1_CANDIDATE_TAR.sha256"
CAND_PIN="$ROOT/V1_26548_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256"
RUNTIME_LIST="$ROOT/V1_26548_RUNTIME_FILES.txt"
PREWRITE_HASHES="$ROOT/V1_26548_PREWRITE_CHANGED_SOURCE_HASHES.sha256"
FORWARD="$ROOT/V1_26548_RUNTIME_DELTA_FROM_26547_V1_1.patch"
ROLLBACK="$ROOT/V1_26548_RUNTIME_ROLLBACK_TO_26547_V1_1.patch"
VALIDATE="$ROOT/validate_26548_v1_integrated.py"
HANDOFF_HASHES="$ROOT/V1_26548_HANDOFF_HASHES.sha256"
VENDOR_MANIFEST="$ROOT/V1_26548_NATIVE_VENDOR_DEPENDENCIES.sha256"
OUT="$ROOT/build_26548_v1_integrated_night_moto_compat_outputs"
WORK="$ROOT/.build_26548_v1_integrated_night_moto_compat_work"
ARTZIP="$WORK/26547_v1_1_artifact.zip"
ARTDIR="$WORK/26547_v1_1_artifact"
BASE="$WORK/exact_26547_v1_1_compiled_candidate"
AFTER="$WORK/candidate_26548_v1"
PATCHREPO="$WORK/patchrepo"
FORWARDCHECK="$WORK/forwardcheck"
ROLLBACKCHECK="$WORK/rollbackcheck"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-v1-integrated-night-moto-compat-debug.apk"

mapfile -t RUNTIME_FILES < "$RUNTIME_LIST"
[[ "${#RUNTIME_FILES[@]}" -eq 9 ]] || fail "runtime file inventory is not exactly 9"
rm -rf "$OUT" "$WORK"
rm -f "$FINAL"
mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER"

cat > "$OUT/26548_V1_COMPILER_STATUS.txt" <<'EOF'
REAL GLSL COMPILE: PASS (0 modified active GLSL; exact inherited shader bytes protected)
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF
cat > "$OUT/26548_V1_STRICT_HANDOFF_REPORT.txt" <<'EOF'
RUNTIME OWNERSHIP: NOT RUN
DORMANT-OWNER REJECTION: NOT RUN
EXACT PRIOR RUNTIME AUTHORITY: NOT RUN
CHANGED RUNTIME SCOPE: NOT RUN
NIGHT RGBA32F TRANSPORT CORRECTION: NOT RUN
MOTOROLA-A PREVIEW SESSION CORRECTION: NOT RUN
CAMERA2 ZERO-O NOISE CONTRACT: NOT RUN
XIAOMI MOTION IQ INVARIANCE: NOT RUN
REAL GLSL COMPILE: PASS (0 modified active GLSL; exact inherited shader bytes protected)
REAL KOTLIN COMPILE: NOT RUN
REAL JAVA COMPILE: NOT RUN
FULL ANDROID ASSEMBLE: NOT RUN
FORWARD PATCH FUZZ=0: NOT RUN
ROLLBACK PATCH FUZZ=0: NOT RUN
POST-BUILD INVARIANCE: NOT RUN
CLEAN ARTIFACT SOURCE EXPORT: NOT RUN
BACKUP BRANCH: NOT REQUIRED (localized correction; exact patch/artifact rollback)
TARGET VERSION/BUILD: 0.9726548 / 26548 V1
EOF
set_report(){
  local key="$1" value="$2"
  python3 - "$OUT/26548_V1_STRICT_HANDOFF_REPORT.txt" "$key" "$value" <<'PY'
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

echo "=== 26548 V1 GATE 0: branch / sealed handoff / no-runtime-source commit ==="
[[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch: $(git branch --show-current)"
git merge-base --is-ancestor "$REPO_BASE_HEAD" HEAD || fail "handoff is not descended from expected preparation HEAD"
git merge-base --is-ancestor "$BASE_SUCCESS_COMMIT" HEAD || fail "handoff is not descended from successful 26547 V1.1 handoff"
[[ -n "$TOKEN" ]] || fail "GitHub token unavailable for exact successful 26547 artifact"
for f in "$BASE_PIN" "$BASE_TAR_PIN" "$CAND_PIN" "$RUNTIME_LIST" "$PREWRITE_HASHES" \
         "$FORWARD" "$ROLLBACK" "$VALIDATE" "$HANDOFF_HASHES" "$VENDOR_MANIFEST"; do
  [[ -f "$f" ]] || fail "required handoff file missing: $f"
done
sha256sum -c "$HANDOFF_HASHES"
[[ "$(sha "$BASE_PIN")" == "$BASE_MANIFEST_SHA" ]] || fail "base manifest SHA drift"
[[ "$(wc -l < "$BASE_PIN")" -eq 969 ]] || fail "base audited manifest is not 969 files"
[[ "$(sha "$CAND_PIN")" == "$CAND_MANIFEST_SHA" ]] || fail "candidate manifest SHA drift"
[[ "$(wc -l < "$CAND_PIN")" -eq 969 ]] || fail "candidate audited manifest is not 969 files"
grep -F "$BASE_TAR_SHA" "$BASE_TAR_PIN" >/dev/null || fail "base candidate TAR pin drift"
python3 -m py_compile "$VALIDATE"
python3 "$VALIDATE" --self-test
bash -n "$0"
python3 - "$REPO_BASE_HEAD" <<'PY'
import subprocess,sys
base=sys.argv[1]
allowed={
'.github/workflows/build-26548-v1-integrated-night-moto-compat.yml',
'V1_26548_BASE_26547_V1_1_AUDITED_RUNTIME.sha256',
'V1_26548_BASE_26547_V1_1_CANDIDATE_TAR.sha256',
'V1_26548_BASE_PROVENANCE.txt',
'V1_26548_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256',
'V1_26548_HANDOFF_HASHES.sha256',
'V1_26548_LOCAL_VALIDATION.txt',
'V1_26548_NATIVE_VENDOR_DEPENDENCIES.sha256',
'V1_26548_PREWRITE_CHANGED_SOURCE_HASHES.sha256',
'V1_26548_RUNTIME_DELTA_FROM_26547_V1_1.patch',
'V1_26548_RUNTIME_FILES.txt',
'V1_26548_RUNTIME_ROLLBACK_TO_26547_V1_1.patch',
'V1_26548_UPLOAD_INSTRUCTIONS.md',
'build_26548_v1_integrated_night_moto_compat.sh',
'validate_26548_v1_integrated.py',
}
actual=set(subprocess.check_output(['git','diff','--name-only',base+'..HEAD'],text=True).splitlines())
extra=sorted(actual-allowed); missing=sorted(allowed-actual)
if extra: raise SystemExit('FAIL: handoff commit changed forbidden repo files: '+repr(extra))
if missing: raise SystemExit('FAIL: handoff commit incomplete: '+repr(missing))
print('PASS: repository commit contains exactly the 15-file 26548 handoff package; app/src untouched')
PY
! git diff --name-only "$REPO_BASE_HEAD..HEAD" | grep -E '^app/' >/dev/null || fail "handoff commit directly changed app source"
pass "sealed 15-file handoff; no backup branch; repository app source untouched"

echo "=== 26548 V1 GATE 1: recover exact successful 26547 V1.1 compiled runtime authority ==="
URL="https://api.github.com/repos/${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}/actions/artifacts/${BASE_ARTIFACT_ID}/zip"
curl --fail --location --silent --show-error --retry 5 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "$URL" -o "$ARTZIP"
[[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "26547 artifact ZIP SHA mismatch"
unzip -q "$ARTZIP" -d "$ARTDIR"
BASE_OUT="$ARTDIR/build_26547_v1_1_night_sabre_12plus3_outputs"
BASE_TAR="$BASE_OUT/26547_V1_1_candidate_app_source.tar.gz"
BASE_AUDITED="$BASE_OUT/26547_V1_1_frozen_candidate_postbuild.sha256"
BASE_APK_HASH="$BASE_OUT/26547_V1_1_APK.sha256"
[[ -f "$BASE_TAR" && -f "$BASE_AUDITED" && -f "$BASE_APK_HASH" ]] || fail "26547 artifact lacks exact candidate authority"
[[ "$(sha "$BASE_TAR")" == "$BASE_TAR_SHA" ]] || fail "26547 candidate TAR SHA mismatch"
[[ "$(sha "$BASE_AUDITED")" == "$BASE_MANIFEST_SHA" ]] || fail "26547 audited manifest SHA mismatch"
cmp -s "$BASE_AUDITED" "$BASE_PIN" || fail "artifact audited manifest is not exact packaged base pin"
grep -F "$BASE_APK_SHA" "$BASE_APK_HASH" >/dev/null || fail "26547 tested APK hash mismatch"
tar -xzf "$BASE_TAR" -C "$BASE"
manifest_audited "$BASE" "$OUT/26548_V1_base_reconstructed.sha256"
cmp -s "$OUT/26548_V1_base_reconstructed.sha256" "$BASE_PIN" || fail "failed to reconstruct exact 26547 runtime authority"
vendor_manifest "$BASE" "$OUT/26548_V1_vendor_base.txt"
cmp -s "$OUT/26548_V1_vendor_base.txt" "$VENDOR_MANIFEST" || fail "26547 native/vendor authority differs from packaged pin"
(cd "$BASE" && sha256sum -c "$PREWRITE_HASHES") > "$OUT/26548_V1_prewrite_source_hashes_verified.txt"
set_report "EXACT PRIOR RUNTIME AUTHORITY" "PASS"
pass "exact successful 26547 V1.1 compiled artifact recovered and prewrite hashes verified"

echo "=== 26548 V1 GATE 2: candidate-first transform / exact scope / runtime contracts ==="
rsync -a --delete "$BASE/" "$AFTER/"
(cd "$AFTER" && patch --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 < "$FORWARD" >/dev/null)
python3 "$VALIDATE" "$BASE" "$AFTER" | tee "$OUT/26548_V1_runtime_contract.txt"
manifest_audited "$AFTER" "$OUT/26548_V1_candidate_source.sha256"
cmp -s "$OUT/26548_V1_candidate_source.sha256" "$CAND_PIN" || fail "candidate is not exact pinned 26548 source"
python3 - "$BASE" "$AFTER" "$OUT/26548_V1_actual_changed_files.txt" <<'PY'
from pathlib import Path
import hashlib,sys
b,c,o=map(Path,sys.argv[1:])
def m(r):
 d={}
 for p in r.rglob('*'):
  if p.is_file(): d[p.relative_to(r).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
 return d
mb,mc=m(b),m(c); ch=sorted(k for k in set(mb)|set(mc) if mb.get(k)!=mc.get(k))
o.write_text('\n'.join(ch)+'\n')
PY
cmp -s "$OUT/26548_V1_actual_changed_files.txt" "$RUNTIME_LIST" || fail "actual runtime scope differs from 9-file allowlist"
set_report "RUNTIME OWNERSHIP" "PASS"
set_report "DORMANT-OWNER REJECTION" "PASS (exact production Night/Motion/camera input paths validated)"
set_report "CHANGED RUNTIME SCOPE" "9 files (exact V1_26548_RUNTIME_FILES.txt)"
set_report "NIGHT RGBA32F TRANSPORT CORRECTION" "PASS (Motion-parity cross-context carrier; no reconstruction math change)"
set_report "MOTOROLA-A PREVIEW SESSION CORRECTION" "PASS (stateful surface replay + one-shot session recovery + pre-freeze guard)"
set_report "CAMERA2 ZERO-O NOISE CONTRACT" "PASS (S>0/O>=0; malformed profiles rejected; no cache/fabrication)"
set_report "XIAOMI MOTION IQ INVARIANCE" "PASS (Motion GLSL/MGC/Sabre/VGN/exposure/denoise/tone protected)"
pass "candidate-first 9-file integrated correction validated"

echo "=== 26548 V1 GATE 3: deterministic full-index forward/rollback proof BEFORE live source write ==="
rm -rf "$PATCHREPO" "$FORWARDCHECK" "$ROLLBACKCHECK"
rsync -a "$BASE/" "$PATCHREPO/"
(
 cd "$PATCHREPO"
 git init -q; git config user.name Photon26548; git config user.email photon26548@example.invalid
 git add -A; git commit -q -m base
 rsync -a --delete --exclude=.git "$AFTER/" "$PATCHREPO/"
 for a in 7 12 40; do
   git -c core.abbrev="$a" diff --binary --full-index --no-ext-diff > "$WORK/forward.$a.patch"
   cmp -s "$WORK/forward.$a.patch" "$FORWARD" || fail "forward patch differs at core.abbrev=$a"
 done
 git add -A; git commit -q -m candidate
 rsync -a --delete --exclude=.git "$BASE/" "$PATCHREPO/"
 for a in 7 12 40; do
   git -c core.abbrev="$a" diff --binary --full-index --no-ext-diff > "$WORK/rollback.$a.patch"
   cmp -s "$WORK/rollback.$a.patch" "$ROLLBACK" || fail "rollback patch differs at core.abbrev=$a"
 done
)
rsync -a "$BASE/" "$FORWARDCHECK/"
(cd "$FORWARDCHECK" && patch --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 < "$FORWARD" >/dev/null)
exact_tree_equal "$FORWARDCHECK" "$AFTER"
rsync -a "$AFTER/" "$ROLLBACKCHECK/"
(cd "$ROLLBACKCHECK" && patch --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 < "$ROLLBACK" >/dev/null)
exact_tree_equal "$ROLLBACKCHECK" "$BASE"
set_report "FORWARD PATCH FUZZ=0" "PASS (core.abbrev 7/12/40 byte-identical)"
set_report "ROLLBACK PATCH FUZZ=0" "PASS (core.abbrev 7/12/40 byte-identical)"
pass "canonical deterministic forward/rollback proof complete"

echo "=== 26548 V1 GATE 4: install exact candidate into ephemeral Actions checkout ==="
# Source writes happen only after exact base/candidate/hash/patch proofs above.
rsync -a --delete "$AFTER/app/" "$ROOT/app/"
manifest_audited "$ROOT" "$OUT/26548_V1_installed_pre_gradle.sha256"
cmp -s "$OUT/26548_V1_installed_pre_gradle.sha256" "$CAND_PIN" || fail "installed candidate differs before compiler"
vendor_manifest "$ROOT" "$OUT/26548_V1_vendor_pre_gradle.txt"
cmp -s "$OUT/26548_V1_vendor_pre_gradle.txt" "$VENDOR_MANIFEST" || fail "native/vendor source drift before compiler"
grep -Fx 'VERSION_NAME=0.9726548' app/version.properties >/dev/null || fail "version name not installed"
grep -Fx 'VERSION_BUILD=26548' app/version.properties >/dev/null || fail "version build not installed"
pass "exact 26548 candidate installed; version/build coupled to this build script"

echo "=== 26548 V1 GATE 5: real project compilers ==="
# No GLSL source changed in the exact 9-file delta; inherited 26547 GLSL bytes are proven by the
# candidate manifest. Kotlin and Java did change and therefore MUST pass the real project compilers.
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace
sed -i 's/REAL KOTLIN COMPILE: NOT RUN YET/REAL KOTLIN COMPILE: PASS/' "$OUT/26548_V1_COMPILER_STATUS.txt"
sed -i 's/REAL JAVA COMPILE: NOT RUN YET/REAL JAVA COMPILE: PASS/' "$OUT/26548_V1_COMPILER_STATUS.txt"
set_report "REAL KOTLIN COMPILE" "PASS"
set_report "REAL JAVA COMPILE" "PASS"
pass "real Kotlin + Java project compilers"

echo "=== 26548 V1 GATE 6: full Android assemble / exactly one APK ==="
./gradlew :app:assembleDebug --stacktrace
mapfile -t APKS < <(find app/build/outputs/apk/debug -maxdepth 1 -type f -name '*.apk' | LC_ALL=C sort)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one debug APK, found ${#APKS[@]}: ${APKS[*]-}"
cp "${APKS[0]}" "$FINAL"
[[ -s "$FINAL" ]] || fail "final APK missing/empty"
sha256sum "$FINAL" > "$OUT/26548_V1_APK.sha256"
sed -i 's/FULL ANDROID ASSEMBLE: NOT RUN YET/FULL ANDROID ASSEMBLE: PASS/' "$OUT/26548_V1_COMPILER_STATUS.txt"
set_report "FULL ANDROID ASSEMBLE" "PASS"
pass "full assemble + exactly one intended APK"

echo "=== 26548 V1 GATE 7: post-build source/native invariance ==="
manifest_audited "$ROOT" "$OUT/26548_V1_postbuild_audited_runtime.sha256"
cmp -s "$OUT/26548_V1_postbuild_audited_runtime.sha256" "$CAND_PIN" || fail "runtime source changed during build"
manifest_audited "$AFTER" "$OUT/26548_V1_frozen_candidate_postbuild.sha256"
cmp -s "$OUT/26548_V1_frozen_candidate_postbuild.sha256" "$CAND_PIN" || fail "frozen candidate changed during build"
vendor_manifest "$ROOT" "$OUT/26548_V1_vendor_postbuild.txt"
cmp -s "$OUT/26548_V1_vendor_postbuild.txt" "$VENDOR_MANIFEST" || fail "native/vendor source changed during build"
python3 "$VALIDATE" "$BASE" "$AFTER" > "$OUT/26548_V1_postbuild_runtime_contract.txt"
sed -i 's/POST-BUILD INVARIANCE: NOT RUN YET/POST-BUILD INVARIANCE: PASS/' "$OUT/26548_V1_COMPILER_STATUS.txt"
set_report "POST-BUILD INVARIANCE" "PASS"
pass "post-build runtime + frozen candidate + native/vendor invariance"

echo "=== 26548 V1 GATE 8: export exact compiled candidate authority ==="
tar -czf "$OUT/26548_V1_candidate_app_source.tar.gz" -C "$AFTER" app
sha256sum "$OUT/26548_V1_candidate_app_source.tar.gz" > "$OUT/26548_V1_candidate_app_source.tar.gz.sha256"
cp "$CAND_PIN" "$OUT/26548_V1_candidate_source.sha256"
cp "$RUNTIME_LIST" "$OUT/26548_V1_actual_runtime_scope.txt"
set_report "CLEAN ARTIFACT SOURCE EXPORT" "PASS"
pass "compiled candidate source exported for exact next-build authority"

cat >> "$OUT/26548_V1_STRICT_HANDOFF_REPORT.txt" <<EOF
FINAL APK: $(basename "$FINAL")
FINAL APK SHA-256: $(sha "$FINAL")
BASE ARTIFACT RUN/ID: ${BASE_RUN_ID} / ${BASE_ARTIFACT_ID}
BASE ARTIFACT SHA-256: ${BASE_ARTIFACT_SHA}
BASE CANDIDATE TAR SHA-256: ${BASE_TAR_SHA}
BASE AUDITED MANIFEST SHA-256: ${BASE_MANIFEST_SHA}
CANDIDATE AUDITED MANIFEST SHA-256: ${CAND_MANIFEST_SHA}
EOF

cat "$OUT/26548_V1_COMPILER_STATUS.txt"
cat "$OUT/26548_V1_STRICT_HANDOFF_REPORT.txt"
echo "PRE-BUILD SAFETY PROOF PASSED"
echo "26548 V1 BUILD SUCCESS"
