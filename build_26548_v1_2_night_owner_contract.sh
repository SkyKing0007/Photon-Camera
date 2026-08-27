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
    ks=sorted(set(ma)|set(mb)); bad=[k for k in ks if ma.get(k)!=mb.get(k)]
    raise SystemExit('tree mismatch: '+repr(bad[:30]))
PY
}

ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
REPO_BASE_HEAD="2b082ed95c347aeb20e207bad5bfc59f8905c3e2"
BASE_SUCCESS_COMMIT="2b082ed95c347aeb20e207bad5bfc59f8905c3e2"
BASE_RUN_ID="33108723192"
BASE_ARTIFACT_ID="9661676421"
BASE_ARTIFACT_NAME="photon-26548-v1-integrated-night-moto-compat"
BASE_ARTIFACT_SHA="60648b892f00bedfdb7b66051aafcf63df5a361d1dff4db4204dffd5924e35d3"
BASE_TAR_SHA="dd6eb66f88bc34d200eb173cefcd639f2e42d0a4facd4d9baaad0802e2bce3ba"
BASE_MANIFEST_SHA="cd80bd15a726f396db9d4774dfec69fd4258f97442b7121ae9b75a3b619bccb1"
CAND_MANIFEST_SHA="b0ba7f1024c85bafef8422386b5eb89c0228adec5b842cc7bb8f8a0256654e4f"
BASE_APK_SHA="f07e9cce8e98e002a413cdd5bba45359e010f170d0336a96c25e12b1a4232e62"
VERSION_NAME="0.9726548"
VERSION_BUILD="26548"
REVISION="V1.2"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"

BASE_PIN="$ROOT/V1_2_26548_BASE_V1_AUDITED_RUNTIME.sha256"
BASE_TAR_PIN="$ROOT/V1_2_26548_BASE_V1_CANDIDATE_TAR.sha256"
CAND_PIN="$ROOT/V1_2_26548_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256"
RUNTIME_LIST="$ROOT/V1_2_26548_RUNTIME_FILES.txt"
PREWRITE_HASHES="$ROOT/V1_2_26548_PREWRITE_CHANGED_SOURCE_HASHES.sha256"
FORWARD="$ROOT/V1_2_26548_RUNTIME_DELTA_FROM_V1.patch"
ROLLBACK="$ROOT/V1_2_26548_RUNTIME_ROLLBACK_TO_V1.patch"
VALIDATE="$ROOT/validate_26548_v1_2_night_owner_contract.py"
HANDOFF_HASHES="$ROOT/V1_2_26548_HANDOFF_HASHES.sha256"
VENDOR_MANIFEST="$ROOT/V1_2_26548_NATIVE_VENDOR_DEPENDENCIES.sha256"
OUT="$ROOT/build_26548_v1_2_night_owner_contract_outputs"
WORK="$ROOT/.build_26548_v1_2_night_owner_contract_work"
ARTZIP="$WORK/26548_v1_artifact.zip"
ARTDIR="$WORK/26548_v1_artifact"
BASE="$WORK/exact_26548_v1_compiled_candidate"
AFTER="$WORK/candidate_26548_v1_2"
PATCHREPO="$WORK/patchrepo"
FORWARDCHECK="$WORK/forwardcheck"
ROLLBACKCHECK="$WORK/rollbackcheck"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-v1-2-night-owner-contract-debug.apk"

mapfile -t RUNTIME_FILES < "$RUNTIME_LIST"
[[ "${#RUNTIME_FILES[@]}" -eq 5 ]] || fail "runtime file inventory is not exactly 5"
rm -rf "$OUT" "$WORK"
rm -f "$FINAL"
mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER"

cat > "$OUT/26548_V1_2_COMPILER_STATUS.txt" <<'EOF'
REAL GLSL COMPILE: PASS (0 modified active GLSL; exact successful 26548 V1 shader bytes protected)
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF
cat > "$OUT/26548_V1_2_STRICT_HANDOFF_REPORT.txt" <<'EOF'
RUNTIME OWNERSHIP: NOT RUN
NIGHT SABRE OWNER-AWARE POST GRAPH: NOT RUN
SPATIAL NODE CROSS-OWNER REJECTION: NOT RUN
LEGACY NIGHT ROUTE REJECTION: NOT RUN
NIGHT SABRE SR STATE: NOT RUN
EXACT PRIOR RUNTIME AUTHORITY: NOT RUN
CHANGED RUNTIME SCOPE: NOT RUN
26548 V1 ROOT-FIX PRESERVATION: NOT RUN
XIAOMI MOTION IQ INVARIANCE: NOT RUN
REAL GLSL COMPILE: PASS (0 modified active GLSL; exact successful 26548 V1 shader bytes protected)
REAL KOTLIN COMPILE: NOT RUN
REAL JAVA COMPILE: NOT RUN
FULL ANDROID ASSEMBLE: NOT RUN
FORWARD PATCH FUZZ=0: NOT RUN
ROLLBACK PATCH FUZZ=0: NOT RUN
POST-BUILD INVARIANCE: NOT RUN
CLEAN ARTIFACT SOURCE EXPORT: NOT RUN
BACKUP BRANCH: NOT REQUIRED (Tier 2 localized owner-routing correction; exact V1 patch/artifact rollback)
TARGET VERSION/BUILD: 0.9726548 / 26548 V1.2
EOF
set_report(){
  local key="$1" value="$2"
  python3 - "$OUT/26548_V1_2_STRICT_HANDOFF_REPORT.txt" "$key" "$value" <<'PY'
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

echo "=== 26548 V1.2 GATE 0: branch / sealed handoff / no runtime source committed ==="
[[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch: $(git branch --show-current)"
git merge-base --is-ancestor "$REPO_BASE_HEAD" HEAD || fail "handoff is not descended from successful 26548 V1.1 workflow commit"
git merge-base --is-ancestor "$BASE_SUCCESS_COMMIT" HEAD || fail "missing successful 26548 V1 authority in lineage"
[[ -n "$TOKEN" ]] || fail "GitHub token unavailable for exact successful 26548 artifact"
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
'.github/workflows/build-26548-v1-2-night-owner-contract.yml',
'V1_2_26548_BASE_V1_AUDITED_RUNTIME.sha256',
'V1_2_26548_BASE_V1_CANDIDATE_TAR.sha256',
'V1_2_26548_BASE_PROVENANCE.txt',
'V1_2_26548_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256',
'V1_2_26548_HANDOFF_HASHES.sha256',
'V1_2_26548_LOCAL_VALIDATION.txt',
'V1_2_26548_NATIVE_VENDOR_DEPENDENCIES.sha256',
'V1_2_26548_PREWRITE_CHANGED_SOURCE_HASHES.sha256',
'V1_2_26548_RUNTIME_DELTA_FROM_V1.patch',
'V1_2_26548_RUNTIME_FILES.txt',
'V1_2_26548_RUNTIME_ROLLBACK_TO_V1.patch',
'V1_2_26548_UPLOAD_INSTRUCTIONS.md',
'build_26548_v1_2_night_owner_contract.sh',
'validate_26548_v1_2_night_owner_contract.py',
}
actual=set(subprocess.check_output(['git','diff','--name-only',base+'..HEAD'],text=True).splitlines())
extra=sorted(actual-allowed); missing=sorted(allowed-actual)
if extra: raise SystemExit('FAIL: handoff commit changed forbidden repo files: '+repr(extra))
if missing: raise SystemExit('FAIL: handoff commit incomplete: '+repr(missing))
print('PASS: repository commit contains exactly the 15-file 26548 V1.2 handoff package; app/src untouched')
PY
! git diff --name-only "$REPO_BASE_HEAD..HEAD" | grep -E '^app/' >/dev/null || fail "handoff commit directly changed app source"
pass "sealed 15-file V1.2 handoff; no backup branch; repository app source untouched"

echo "=== 26548 V1.2 GATE 1: recover exact successful compiled 26548 V1 authority ==="
REPO_API="https://api.github.com/repos/${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}"
RUN_META="$WORK/26548_v1_base_run.json"
RUN_URL="$REPO_API/actions/runs/${BASE_RUN_ID}"
ART_URL="$REPO_API/actions/artifacts/${BASE_ARTIFACT_ID}/zip"
# Permanent V1.2 regression: prove success from GitHub run metadata and persisted artifact files.
# Never require a console-only echo such as `26548 V1 BUILD SUCCESS` to exist inside the artifact.
curl --fail --location --silent --show-error --retry 5 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "$RUN_URL" -o "$RUN_META"
python3 - "$RUN_META" "$BASE_RUN_ID" "$BASE_SUCCESS_COMMIT" "$EXPECTED_BRANCH" <<'PYRUN'
import json, sys
p, run_id, commit, branch = sys.argv[1:]
d = json.load(open(p, 'r', encoding='utf-8'))
assert str(d.get('id')) == run_id, f"run id mismatch: {d.get('id')}"
assert d.get('conclusion') == 'success', f"base run conclusion is {d.get('conclusion')}"
assert d.get('head_sha') == commit, f"base run head_sha mismatch: {d.get('head_sha')}"
assert d.get('head_branch') == branch, f"base run branch mismatch: {d.get('head_branch')}"
print('PASS: exact prior Actions run metadata proves success/commit/branch')
PYRUN
curl --fail --location --silent --show-error --retry 5 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "$ART_URL" -o "$ARTZIP"
[[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "26548 V1 artifact ZIP SHA mismatch"
unzip -q "$ARTZIP" -d "$ARTDIR"
BASE_OUT="$ARTDIR/build_26548_v1_integrated_night_moto_compat_outputs"
BASE_TAR="$BASE_OUT/26548_V1_candidate_app_source.tar.gz"
BASE_AUDITED="$BASE_OUT/26548_V1_candidate_source.sha256"
BASE_APK_HASH="$BASE_OUT/26548_V1_APK.sha256"
BASE_COMPILER="$BASE_OUT/26548_V1_COMPILER_STATUS.txt"
BASE_REPORT="$BASE_OUT/26548_V1_STRICT_HANDOFF_REPORT.txt"
[[ -f "$BASE_TAR" && -f "$BASE_AUDITED" && -f "$BASE_APK_HASH" && -f "$BASE_COMPILER" && -f "$BASE_REPORT" ]] || fail "26548 V1 artifact lacks exact compiled candidate/proof authority"
[[ "$(sha "$BASE_TAR")" == "$BASE_TAR_SHA" ]] || fail "26548 V1 candidate TAR SHA mismatch"
[[ "$(sha "$BASE_AUDITED")" == "$BASE_MANIFEST_SHA" ]] || fail "26548 V1 audited manifest SHA mismatch"
cmp -s "$BASE_AUDITED" "$BASE_PIN" || fail "artifact audited manifest is not exact packaged base pin"
grep -F "$BASE_APK_SHA" "$BASE_APK_HASH" >/dev/null || fail "26548 V1 tested APK hash mismatch"
for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' \
             'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do
  grep -F "$proof" "$BASE_COMPILER" >/dev/null || fail "base compiler-status file missing persisted proof: $proof"
done
for proof in 'RUNTIME OWNERSHIP: PASS' 'DORMANT-OWNER REJECTION: PASS' 'EXACT PRIOR RUNTIME AUTHORITY: PASS' \
             'NIGHT RGBA32F TRANSPORT CORRECTION: PASS' 'XIAOMI MOTION IQ INVARIANCE: PASS' \
             'FORWARD PATCH FUZZ=0: PASS' 'ROLLBACK PATCH FUZZ=0: PASS' \
             'POST-BUILD INVARIANCE: PASS' 'CLEAN ARTIFACT SOURCE EXPORT: PASS' \
             'TARGET VERSION/BUILD: 0.9726548 / 26548 V1'; do
  grep -F "$proof" "$BASE_REPORT" >/dev/null || fail "base strict report missing persisted proof: $proof"
done
tar -xzf "$BASE_TAR" -C "$BASE"
manifest_audited "$BASE" "$OUT/26548_V1_2_base_reconstructed.sha256"
cmp -s "$OUT/26548_V1_2_base_reconstructed.sha256" "$BASE_PIN" || fail "failed to reconstruct exact compiled 26548 V1 runtime authority"
vendor_manifest "$BASE" "$OUT/26548_V1_2_vendor_base.txt"
cmp -s "$OUT/26548_V1_2_vendor_base.txt" "$VENDOR_MANIFEST" || fail "26548 V1 native/vendor authority differs from packaged pin"
(cd "$BASE" && sha256sum -c "$PREWRITE_HASHES") > "$OUT/26548_V1_2_prewrite_source_hashes_verified.txt"
set_report "EXACT PRIOR RUNTIME AUTHORITY" "PASS (run ${BASE_RUN_ID}, artifact ${BASE_ARTIFACT_ID})"
pass "exact successful 26548 V1 compiled artifact recovered; prior real compiler/assemble proof verified"

echo "=== 26548 V1.2 GATE 2: candidate-first 5-file owner-routing correction ==="
rsync -a --delete "$BASE/" "$AFTER/"
(cd "$AFTER" && patch --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 < "$FORWARD" >/dev/null)
python3 "$VALIDATE" "$BASE" "$AFTER" | tee "$OUT/26548_V1_2_runtime_contract.txt"
manifest_audited "$AFTER" "$OUT/26548_V1_2_candidate_source.sha256"
cmp -s "$OUT/26548_V1_2_candidate_source.sha256" "$CAND_PIN" || fail "candidate is not exact pinned 26548 V1.2 source"
python3 - "$BASE" "$AFTER" "$OUT/26548_V1_2_actual_changed_files.txt" <<'PY'
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
cmp -s "$OUT/26548_V1_2_actual_changed_files.txt" "$RUNTIME_LIST" || fail "actual runtime scope differs from 5-file allowlist"
set_report "RUNTIME OWNERSHIP" "PASS (Night and Motion validate the same durable reconstruction owner)"
set_report "NIGHT SABRE OWNER-AWARE POST GRAPH" "PASS (Sabre skips Spatial source/reliability nodes)"
set_report "SPATIAL NODE CROSS-OWNER REJECTION" "PASS (both nodes require explicit Spatial owner in Motion or Night)"
set_report "LEGACY NIGHT ROUTE REJECTION" "PASS (active Night graph has no Bayer/RCD/fusion/Photon sharpening path; dormant legacy entry points caller-free)"
set_report "NIGHT SABRE SR STATE" "PASS (requested vs effective explicit; Sabre remains native-grid)"
set_report "CHANGED RUNTIME SCOPE" "5 files (exact V1_2_26548_RUNTIME_FILES.txt)"
set_report "26548 V1 ROOT-FIX PRESERVATION" "PASS (RGBA32F Night transport + session health + zero-O Camera2 compatibility retained)"
set_report "XIAOMI MOTION IQ INVARIANCE" "PASS (Motion shaders/capture/exposure/alignment/Sabre/VGN/denoise/tone protected)"
pass "candidate-first exact 5-file Night owner-contract correction validated"

echo "=== 26548 V1.2 GATE 3: deterministic full-index forward/rollback proof BEFORE live source write ==="
rm -rf "$PATCHREPO" "$FORWARDCHECK" "$ROLLBACKCHECK"
rsync -a "$BASE/" "$PATCHREPO/"
(
 cd "$PATCHREPO"
 git init -q; git config user.name Photon26548V12; git config user.email photon26548v12@example.invalid
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

echo "=== 26548 V1.2 GATE 4: install exact candidate into ephemeral Actions checkout ==="
# Runtime source writes occur only after exact base/candidate/hash/patch proof above.
rsync -a --delete "$AFTER/app/" "$ROOT/app/"
manifest_audited "$ROOT" "$OUT/26548_V1_2_installed_pre_gradle.sha256"
cmp -s "$OUT/26548_V1_2_installed_pre_gradle.sha256" "$CAND_PIN" || fail "installed candidate differs before compiler"
vendor_manifest "$ROOT" "$OUT/26548_V1_2_vendor_pre_gradle.txt"
cmp -s "$OUT/26548_V1_2_vendor_pre_gradle.txt" "$VENDOR_MANIFEST" || fail "native/vendor source drift before compiler"
grep -Fx 'VERSION_NAME=0.9726548' app/version.properties >/dev/null || fail "version name not installed"
grep -Fx 'VERSION_BUILD=26548' app/version.properties >/dev/null || fail "version build not installed"
pass "exact 26548 V1.2 candidate installed in same authoritative build invocation"

echo "=== 26548 V1.2 GATE 5: REAL PROJECT COMPILERS ==="
# No active GLSL file changes in this exact five-file delta. The exact successful 26548 V1 shader
# bytes are protected by the 969-file base/candidate manifests. Four Java files and one Kotlin file
# changed and therefore must pass the real project compilers.
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace
sed -i 's/REAL KOTLIN COMPILE: NOT RUN YET/REAL KOTLIN COMPILE: PASS/' "$OUT/26548_V1_2_COMPILER_STATUS.txt"
sed -i 's/REAL JAVA COMPILE: NOT RUN YET/REAL JAVA COMPILE: PASS/' "$OUT/26548_V1_2_COMPILER_STATUS.txt"
set_report "REAL KOTLIN COMPILE" "PASS"
set_report "REAL JAVA COMPILE" "PASS"
# Permanent prior Java failure: keep exact ByteBuffer qualification in live source.
grep -F 'java.nio.ByteBuffer source = plane.getBuffer().duplicate();' app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java >/dev/null || fail "permanent ByteBuffer javac regression gate failed"
python3 "$VALIDATE" "$BASE" "$AFTER" > "$OUT/26548_V1_2_postcompiler_runtime_contract.txt"
pass "real Kotlin + Java compilers + permanent prior compiler regressions"

echo "=== 26548 V1.2 GATE 6: FULL ANDROID ASSEMBLE / exactly one APK ==="
./gradlew :app:assembleDebug --stacktrace
mapfile -t APKS < <(find app/build/outputs/apk/debug -maxdepth 1 -type f -name '*.apk' | LC_ALL=C sort)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one debug APK, found ${#APKS[@]}: ${APKS[*]-}"
cp "${APKS[0]}" "$FINAL"
[[ -s "$FINAL" ]] || fail "final APK missing/empty"
sha256sum "$FINAL" > "$OUT/26548_V1_2_APK.sha256"
sed -i 's/FULL ANDROID ASSEMBLE: NOT RUN YET/FULL ANDROID ASSEMBLE: PASS/' "$OUT/26548_V1_2_COMPILER_STATUS.txt"
set_report "FULL ANDROID ASSEMBLE" "PASS"
pass "full assemble + exactly one intended APK"

echo "=== 26548 V1.2 GATE 7: post-build source/native invariance ==="
manifest_audited "$ROOT" "$OUT/26548_V1_2_postbuild_audited_runtime.sha256"
cmp -s "$OUT/26548_V1_2_postbuild_audited_runtime.sha256" "$CAND_PIN" || fail "runtime source changed during build"
manifest_audited "$AFTER" "$OUT/26548_V1_2_frozen_candidate_postbuild.sha256"
cmp -s "$OUT/26548_V1_2_frozen_candidate_postbuild.sha256" "$CAND_PIN" || fail "frozen candidate changed during build"
vendor_manifest "$ROOT" "$OUT/26548_V1_2_vendor_postbuild.txt"
cmp -s "$OUT/26548_V1_2_vendor_postbuild.txt" "$VENDOR_MANIFEST" || fail "native/vendor source changed during build"
python3 "$VALIDATE" "$BASE" "$AFTER" > "$OUT/26548_V1_2_postbuild_runtime_contract.txt"
sed -i 's/POST-BUILD INVARIANCE: NOT RUN YET/POST-BUILD INVARIANCE: PASS/' "$OUT/26548_V1_2_COMPILER_STATUS.txt"
set_report "POST-BUILD INVARIANCE" "PASS"
pass "post-build runtime + frozen candidate + native/vendor invariance"

echo "=== 26548 V1.2 GATE 8: export exact compiled candidate authority ==="
tar -czf "$OUT/26548_V1_2_candidate_app_source.tar.gz" -C "$AFTER" app
sha256sum "$OUT/26548_V1_2_candidate_app_source.tar.gz" > "$OUT/26548_V1_2_candidate_app_source.tar.gz.sha256"
cp "$CAND_PIN" "$OUT/26548_V1_2_candidate_source.sha256"
cp "$RUNTIME_LIST" "$OUT/26548_V1_2_actual_runtime_scope.txt"
set_report "CLEAN ARTIFACT SOURCE EXPORT" "PASS"
pass "compiled V1.2 candidate source exported for exact next-build authority"

cat >> "$OUT/26548_V1_2_STRICT_HANDOFF_REPORT.txt" <<EOF
FINAL APK: $(basename "$FINAL")
FINAL APK SHA-256: $(sha "$FINAL")
BASE ARTIFACT RUN/ID: ${BASE_RUN_ID} / ${BASE_ARTIFACT_ID}
BASE ARTIFACT SHA-256: ${BASE_ARTIFACT_SHA}
BASE CANDIDATE TAR SHA-256: ${BASE_TAR_SHA}
BASE AUDITED MANIFEST SHA-256: ${BASE_MANIFEST_SHA}
CANDIDATE AUDITED MANIFEST SHA-256: ${CAND_MANIFEST_SHA}
EOF

cat "$OUT/26548_V1_2_COMPILER_STATUS.txt"
cat "$OUT/26548_V1_2_STRICT_HANDOFF_REPORT.txt"
echo "PRE-BUILD SAFETY PROOF PASSED"
echo "26548 V1.2 BUILD SUCCESS"
