#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
manifest_audited(){ local root="$1" out="$2"; (cd "$root" && { find app/src/main -type f ! -path 'app/src/main/cpp/third_party_26507/*' ! -path 'app/src/main/cpp/deps/*' -print; [[ -f app/src/main/cpp/deps/.gitignore ]] && echo app/src/main/cpp/deps/.gitignore; echo app/version.properties; echo app/build.gradle; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done) > "$out"; }
vendor_manifest(){ local root="$1" out="$2"; (cd "$root" && { [[ -d app/src/main/cpp/third_party_26507 ]] && find app/src/main/cpp/third_party_26507 -type f -print; [[ -d app/src/main/cpp/deps ]] && find app/src/main/cpp/deps -type f -print; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done) > "$out"; }
exact_tree_equal(){ python3 - "$1" "$2" <<'PY'
from pathlib import Path
import hashlib,sys
def m(root):
 root=Path(root);return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file() and '.git' not in p.parts}
a,b=m(sys.argv[1]),m(sys.argv[2])
if a!=b:
 bad=[k for k in sorted(set(a)|set(b)) if a.get(k)!=b.get(k)]
 raise SystemExit('tree mismatch: '+repr(bad[:30]))
PY
}

ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
BASE_SUCCESS_COMMIT="77aee0b9abd18f22cb3f9872d53e3ea1869824fe"
BASE_RUN_ID="33235249721"
BASE_ARTIFACT_ID="9709756680"
BASE_ARTIFACT_NAME="photon-26559-v1-remove-microcontrast-halo"
BASE_ARTIFACT_SHA="33854b4c8a02743d6378577cd73f161de7f4e525445c16b06aa5273b250351ba"
BASE_TAR_SHA="5322e66d997f1724accd2cf34c7a0933b194c857f3fe05cd7ea99bbfad870e6e"
BASE_MANIFEST_SHA="60430f42ae65e934f87278b578e087c1cb4e87f692746c184293a85f95cc501e"
CAND_MANIFEST_SHA="a8249154bdf98d6661f2ca05a8ec2ff47fc76d86dd4475967cbfc5c4e13b0a39"
BASE_APK_SHA="7407cbe4b52c780854d9785041ec7405b6dba49d26ff6bccd7fa8d6072335d49"
VENDOR_MANIFEST_SHA="7dbcc5ee5b9040965e431d79c45c5100f559c2b96c50970ca21987c684c825a8"
PROTECTED_CORE_SHA="685b980681f8749f5736900882418b71734eeb879691124d9b584bdd870687c1"
PROTECTED_GLSL_SHA="4ac601513fe632560317d3d356e2350021e6ec5fd938fc8c320140f7abe10118"
PREWRITE_MANIFEST_SHA="37e69f3722673055d8aff858671ca0364c82fdda1f4026cb68d90e78a327c6ff"
CAND_CHANGED_MANIFEST_SHA="c894f55d204d27731bbd36c8184d865d3fe50634daf166d19137215b41d7aab1"
BACKUP_BRANCH="backup-26559-v1-before-sabre-only-spatial-rgb-sr-transition"
VERSION_NAME="0.9726560"
VERSION_BUILD="26560"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"

BASE_PIN="$ROOT/V1_26560_BASE_26559_V1_AUDITED_RUNTIME.sha256"
BASE_TAR_PIN="$ROOT/V1_26560_BASE_26559_V1_CANDIDATE_TAR.sha256"
CAND_PIN="$ROOT/V1_26560_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256"
VENDOR_PIN="$ROOT/V1_26560_NATIVE_VENDOR_DEPENDENCIES.sha256"
RUNTIME_LIST="$ROOT/V1_26560_RUNTIME_FILES.txt"
DELETED_LIST="$ROOT/V1_26560_DELETED_FILES.txt"
PREWRITE="$ROOT/V1_26560_PREWRITE_SOURCE_HASHES.sha256"
CAND_CHANGED="$ROOT/V1_26560_CANDIDATE_CHANGED_HASHES.sha256"
PROTECTED_CORE="$ROOT/V1_26560_PROTECTED_SABRE_SHARED.sha256"
PROTECTED_GLSL="$ROOT/V1_26560_PROTECTED_UNCHANGED_GLSL.sha256"
FORWARD="$ROOT/V1_26560_RUNTIME_DELTA_FROM_26559_V1.patch"
ROLLBACK="$ROOT/V1_26560_RUNTIME_ROLLBACK_TO_26559_V1.patch"
VALIDATE="$ROOT/validate_26560_v1_sabre_only_spatial_rgb_cleanup.py"
HANDOFF_HASHES="$ROOT/V1_26560_HANDOFF_HASHES.sha256"
OUT="$ROOT/build_26560_v1_sabre_only_spatial_rgb_cleanup_outputs"
WORK="$ROOT/.build_26560_v1_sabre_only_spatial_rgb_cleanup_work"
ARTZIP="$WORK/26559_v1_artifact.zip"; ARTDIR="$WORK/artifact"; BASE="$WORK/exact_26559_compiled_candidate"; AFTER="$WORK/candidate_26560"; PATCHREPO="$WORK/patchrepo"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-v1-sabre-only-spatial-rgb-cleanup-debug.apk"
mapfile -t RUNTIME_FILES < "$RUNTIME_LIST"
mapfile -t DELETED_FILES < "$DELETED_LIST"
[[ "${#RUNTIME_FILES[@]}" -eq 58 ]] || fail "runtime inventory must contain exactly 58 files"
[[ "${#DELETED_FILES[@]}" -eq 45 ]] || fail "deletion inventory must contain exactly 45 files"
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER"

cat > "$OUT/26560_V1_COMPILER_STATUS.txt" <<'EOF'
REAL GLSL COMPILE: N/A (no modified active-path GLSL; all remaining GLSL hash-protected)
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET (covered by full assemble)
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF
cat > "$OUT/26560_V1_STRICT_HANDOFF_REPORT.txt" <<'EOF'
EXACT PRIOR RUNTIME AUTHORITY: NOT RUN
BACKUP STATUS: NOT RUN
CHANGED RUNTIME SCOPE: NOT RUN
SABRE-ONLY ROUTING: NOT RUN
SPATIAL-RGB/HYBRID DELETION REACHABILITY: NOT RUN
MERGE-SELECTION UI/PER-LENS AUTHORITY REMOVAL: NOT RUN
SUPER RES SWITCH RETENTION / NATIVE-GRID PLACEHOLDER: NOT RUN
26558 NIGHT LONG CLIPPING INVARIANCE: NOT RUN
SABRE/VGN/RESOLVE/JIN/RENDER INVARIANCE: NOT RUN
PROTECTED UNCHANGED GLSL INVARIANCE: NOT RUN
REAL GLSL COMPILE: N/A (no modified active-path GLSL)
GLSL RESERVED-IDENTIFIER SCAN: N/A (no modified active-path GLSL)
REAL KOTLIN COMPILE: NOT RUN
REAL JAVA COMPILE: NOT RUN
NATIVE/NDK COMPILE: NOT RUN
FULL ANDROID ASSEMBLE: NOT RUN
FORWARD PATCH FUZZ=0: NOT RUN
ROLLBACK PATCH FUZZ=0: NOT RUN
POST-BUILD INVARIANCE: NOT RUN
CLEAN ARTIFACT SOURCE EXPORT: NOT RUN
TARGET VERSION/BUILD: 0.9726560 / 26560 V1
EOF
set_report(){ python3 - "$OUT/26560_V1_STRICT_HANDOFF_REPORT.txt" "$1" "$2" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); key=sys.argv[2]; value=sys.argv[3]; lines=p.read_text().splitlines(); pref=key+':'
for i,line in enumerate(lines):
 if line.startswith(pref): lines[i]=pref+' '+value; break
else: raise SystemExit('report key missing '+key)
p.write_text('\n'.join(lines)+'\n')
PY
}

echo "=== 26560 GATE 0: sealed handoff / branch / backup / lineage ==="
[[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
[[ "$(git rev-parse HEAD^)" == "$BASE_SUCCESS_COMMIT" ]] || fail "handoff commit must be direct child of successful 26559"
[[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"
sha256sum -c "$HANDOFF_HASHES"
python3 -m py_compile "$VALIDATE"
python3 "$VALIDATE" --self-test
bash -n "$0"
[[ "$(wc -l < "$BASE_PIN")" -eq 970 ]] || fail "base manifest count"
[[ "$(sha "$BASE_PIN")" == "$BASE_MANIFEST_SHA" ]] || fail "base manifest SHA"
[[ "$(wc -l < "$CAND_PIN")" -eq 925 ]] || fail "candidate manifest count"
[[ "$(sha "$CAND_PIN")" == "$CAND_MANIFEST_SHA" ]] || fail "candidate manifest SHA"
[[ "$(wc -l < "$VENDOR_PIN")" -eq 778 ]] || fail "vendor manifest count"
[[ "$(sha "$VENDOR_PIN")" == "$VENDOR_MANIFEST_SHA" ]] || fail "vendor manifest SHA"
[[ "$(wc -l < "$PROTECTED_CORE")" -eq 16 ]] || fail "protected core count"
[[ "$(sha "$PROTECTED_CORE")" == "$PROTECTED_CORE_SHA" ]] || fail "protected core manifest SHA"
[[ "$(wc -l < "$PROTECTED_GLSL")" -eq 251 ]] || fail "protected GLSL count"
[[ "$(sha "$PROTECTED_GLSL")" == "$PROTECTED_GLSL_SHA" ]] || fail "protected GLSL manifest SHA"
[[ "$(wc -l < "$PREWRITE")" -eq 58 ]] || fail "prewrite count"
[[ "$(sha "$PREWRITE")" == "$PREWRITE_MANIFEST_SHA" ]] || fail "prewrite manifest SHA"
[[ "$(wc -l < "$CAND_CHANGED")" -eq 13 ]] || fail "candidate changed-hash count"
[[ "$(sha "$CAND_CHANGED")" == "$CAND_CHANGED_MANIFEST_SHA" ]] || fail "candidate changed manifest SHA"
grep -F "$BASE_TAR_SHA" "$BASE_TAR_PIN" >/dev/null || fail "base TAR pin drift"
BACKUP_SHA="$(git ls-remote origin "refs/heads/${BACKUP_BRANCH}" | awk '{print $1}')"
[[ "$BACKUP_SHA" == "$BASE_SUCCESS_COMMIT" ]] || fail "architectural backup missing/wrong: $BACKUP_SHA"
set_report "BACKUP STATUS" "PASS (${BACKUP_BRANCH} @ ${BASE_SUCCESS_COMMIT})"
python3 - "$BASE_SUCCESS_COMMIT" <<'PY'
import subprocess,sys
base=sys.argv[1]
allowed={
'.github/workflows/build-26560-v1-sabre-only-spatial-rgb-cleanup.yml',
'V1_26560_BASE_26559_V1_AUDITED_RUNTIME.sha256','V1_26560_BASE_26559_V1_CANDIDATE_TAR.sha256',
'V1_26560_BASE_PROVENANCE.txt','V1_26560_CANDIDATE_CHANGED_HASHES.sha256','V1_26560_DELETED_FILES.txt',
'V1_26560_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256','V1_26560_HANDOFF_HASHES.sha256',
'V1_26560_LOCAL_VALIDATION.txt','V1_26560_NATIVE_VENDOR_DEPENDENCIES.sha256',
'V1_26560_PREWRITE_SOURCE_HASHES.sha256','V1_26560_PROTECTED_SABRE_SHARED.sha256',
'V1_26560_PROTECTED_UNCHANGED_GLSL.sha256','V1_26560_RUNTIME_DELTA_FROM_26559_V1.patch',
'V1_26560_RUNTIME_FILES.txt','V1_26560_RUNTIME_ROLLBACK_TO_26559_V1.patch',
'V1_26560_UPLOAD_INSTRUCTIONS.md','build_26560_v1_sabre_only_spatial_rgb_cleanup.sh',
'validate_26560_v1_sabre_only_spatial_rgb_cleanup.py'}
actual=set(subprocess.check_output(['git','diff','--name-only',base+'..HEAD'],text=True).splitlines())
if actual!=allowed: raise SystemExit('handoff scope mismatch extra=%r missing=%r'%(sorted(actual-allowed),sorted(allowed-actual)))
if any(x.startswith('app/') for x in actual): raise SystemExit('handoff directly modified repository app source')
print('PASS exact 19-file handoff scope; repository app source untouched')
PY
! grep -F 'V1_26560_' .github/workflows/build-26559-v1-remove-microcontrast-halo.yml
pass "sealed 26560 package / backup / lineage"

echo "=== 26560 GATE 1: exact successful compiled 26559 runtime authority ==="
REPO_API="https://api.github.com/repos/${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}"
curl --fail --location --silent --show-error --retry 5 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "$REPO_API/actions/runs/${BASE_RUN_ID}" -o "$WORK/base_run.json"
python3 - "$WORK/base_run.json" "$BASE_RUN_ID" "$BASE_SUCCESS_COMMIT" "$EXPECTED_BRANCH" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); assert str(d.get('id'))==sys.argv[2]; assert d.get('conclusion')=='success'; assert d.get('head_sha')==sys.argv[3]; assert d.get('head_branch')==sys.argv[4]
print('PASS exact successful 26559 Actions run')
PY
curl --fail --location --silent --show-error --retry 5 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "$REPO_API/actions/artifacts/${BASE_ARTIFACT_ID}" -o "$WORK/base_artifact.json"
python3 - "$WORK/base_artifact.json" "$BASE_ARTIFACT_ID" "$BASE_ARTIFACT_NAME" "$BASE_ARTIFACT_SHA" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); assert str(d.get('id'))==sys.argv[2]; assert d.get('name')==sys.argv[3]; assert not d.get('expired'); assert d.get('digest')=='sha256:'+sys.argv[4]
print('PASS exact 26559 artifact metadata/digest')
PY
curl --fail --location --silent --show-error --retry 5 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "$REPO_API/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"
[[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "26559 artifact ZIP SHA mismatch"
unzip -q "$ARTZIP" -d "$ARTDIR"
BASE_OUT="$ARTDIR/build_26559_v1_remove_microcontrast_halo_outputs"
BASE_TAR="$BASE_OUT/26559_V1_candidate_app_source.tar.gz"
BASE_AUDITED="$BASE_OUT/26559_V1_candidate_source.sha256"
BASE_APK_HASH="$BASE_OUT/26559_V1_APK.sha256"
BASE_COMPILER="$BASE_OUT/26559_V1_COMPILER_STATUS.txt"
for f in "$BASE_TAR" "$BASE_AUDITED" "$BASE_APK_HASH" "$BASE_COMPILER" "$BASE_OUT/26559_vendor_postbuild.sha256"; do [[ -f "$f" ]] || fail "base artifact missing $f"; done
[[ "$(sha "$BASE_TAR")" == "$BASE_TAR_SHA" ]] || fail "26559 source TAR SHA mismatch"
[[ "$(sha "$BASE_AUDITED")" == "$BASE_MANIFEST_SHA" ]] || fail "26559 audited manifest SHA mismatch"
cmp "$BASE_AUDITED" "$BASE_PIN" >/dev/null || fail "packaged base pin differs from successful 26559 artifact manifest"
for s in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do grep -F "$s" "$BASE_COMPILER" >/dev/null || fail "base compiler proof missing $s"; done
grep -F "$BASE_APK_SHA" "$BASE_APK_HASH" >/dev/null || fail "26559 APK SHA proof mismatch"
tar -xzf "$BASE_TAR" -C "$BASE"
manifest_audited "$BASE" "$OUT/26559_reconstructed_runtime.sha256"
cmp "$OUT/26559_reconstructed_runtime.sha256" "$BASE_PIN" >/dev/null || fail "reconstructed 26559 source not exact"
vendor_manifest "$BASE" "$OUT/26559_vendor_base.sha256"
cmp "$OUT/26559_vendor_base.sha256" "$VENDOR_PIN" >/dev/null || fail "base vendor mismatch"
set_report "EXACT PRIOR RUNTIME AUTHORITY" "PASS (run ${BASE_RUN_ID} artifact ${BASE_ARTIFACT_ID})"
pass "exact successful compiled 26559 authority"

echo "=== 26560 GATE 2: candidate-first Sabre-only cleanup / reachability / invariance ==="
(cd "$BASE" && sha256sum -c "$PREWRITE")
cp -a "$BASE/." "$AFTER/"
(cd "$AFTER" && git init -q && git config user.email audit@example.invalid && git config user.name PhotonAudit && git add -A && git commit -q -m base26559 && git apply --check "$FORWARD" && git apply "$FORWARD")
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" | tee "$OUT/26560_runtime_contract.txt"
manifest_audited "$AFTER" "$OUT/26560_candidate_runtime.sha256"
cmp "$OUT/26560_candidate_runtime.sha256" "$CAND_PIN" >/dev/null || fail "candidate manifest mismatch"
[[ "$(sha "$OUT/26560_candidate_runtime.sha256")" == "$CAND_MANIFEST_SHA" ]] || fail "candidate manifest SHA mismatch"
[[ "$(wc -l < "$OUT/26560_candidate_runtime.sha256")" -eq 925 ]] || fail "candidate manifest count"
vendor_manifest "$AFTER" "$OUT/26560_vendor_candidate.sha256"
cmp "$OUT/26560_vendor_candidate.sha256" "$VENDOR_PIN" >/dev/null || fail "candidate vendor drift"
(cd "$AFTER" && sha256sum -c "$CAND_CHANGED")
(cd "$AFTER" && sha256sum -c "$PROTECTED_CORE") > "$OUT/26560_protected_sabre_shared_invariance.txt"
(cd "$AFTER" && sha256sum -c "$PROTECTED_GLSL") > "$OUT/26560_protected_glsl_invariance.txt"
for f in "${DELETED_FILES[@]}"; do [[ ! -e "$AFTER/$f" ]] || fail "deleted runtime file survived: $f"; done
set_report "CHANGED RUNTIME SCOPE" "PASS (13 modified + 45 deleted + 0 added; version included)"
set_report "SABRE-ONLY ROUTING" "PASS"
set_report "SPATIAL-RGB/HYBRID DELETION REACHABILITY" "PASS (45 exact deletions; validator zero live modified-owner refs)"
set_report "MERGE-SELECTION UI/PER-LENS AUTHORITY REMOVAL" "PASS"
set_report "SUPER RES SWITCH RETENTION / NATIVE-GRID PLACEHOLDER" "PASS (switch/state retained; old Spatial SR backend absent; Sabre outputScale=1)"
set_report "26558 NIGHT LONG CLIPPING INVARIANCE" "PASS"
set_report "SABRE/VGN/RESOLVE/JIN/RENDER INVARIANCE" "PASS (16 protected core files)"
set_report "PROTECTED UNCHANGED GLSL INVARIANCE" "PASS (251 remaining GLSL files)"
pass "Sabre-only cleanup contract + protected runtime invariance"

echo "=== 26560 GATE 3: canonical deterministic patch proof ==="
rm -rf "$PATCHREPO"; cp -a "$BASE" "$PATCHREPO"; cd "$PATCHREPO"
git init -q; git config user.email audit@example.invalid; git config user.name PhotonAudit; git add -A; git commit -q -m base
B=$(git rev-parse HEAD); rm -rf app; cp -a "$AFTER/app" ./app; rm -rf app/.git; git add -A; git diff --cached --check; git commit -q -m candidate; C=$(git rev-parse HEAD)
for ab in 7 12 40; do
 git -c core.abbrev=$ab diff --binary --full-index --no-ext-diff "$B" "$C" > "$WORK/fwd_${ab}.patch"
 git -c core.abbrev=$ab diff --binary --full-index --no-ext-diff "$C" "$B" > "$WORK/rbk_${ab}.patch"
done
cmp "$WORK/fwd_7.patch" "$WORK/fwd_12.patch" >/dev/null; cmp "$WORK/fwd_7.patch" "$WORK/fwd_40.patch" >/dev/null
cmp "$WORK/rbk_7.patch" "$WORK/rbk_12.patch" >/dev/null; cmp "$WORK/rbk_7.patch" "$WORK/rbk_40.patch" >/dev/null
cmp "$WORK/fwd_40.patch" "$FORWARD" >/dev/null || fail "forward patch not canonical regenerated bytes"
cmp "$WORK/rbk_40.patch" "$ROLLBACK" >/dev/null || fail "rollback patch not canonical regenerated bytes"
rm -rf "$WORK/fwd_replay"; cp -a "$BASE" "$WORK/fwd_replay"; (cd "$WORK/fwd_replay" && git init -q && git config user.email audit@example.invalid && git config user.name PhotonAudit && git add -A && git commit -q -m base && git apply --check "$FORWARD" && git apply "$FORWARD")
exact_tree_equal "$WORK/fwd_replay" "$AFTER"
rm -rf "$WORK/rbk_replay"; cp -a "$AFTER" "$WORK/rbk_replay"; rm -rf "$WORK/rbk_replay/.git"; (cd "$WORK/rbk_replay" && git init -q && git config user.email audit@example.invalid && git config user.name PhotonAudit && git add -A && git commit -q -m cand && git apply --check "$ROLLBACK" && git apply "$ROLLBACK")
exact_tree_equal "$WORK/rbk_replay" "$BASE"
set_report "FORWARD PATCH FUZZ=0" "PASS"
set_report "ROLLBACK PATCH FUZZ=0" "PASS"
cd "$ROOT"
pass "canonical patches deterministic and exact"

echo "=== 26560 GATE 4: controlled live install + real project compilers + full assemble ==="
: > "$OUT/26560_repository_prewrite_source_hashes.sha256"
for f in "${RUNTIME_FILES[@]}"; do [[ -f "$ROOT/$f" ]] && sha256sum "$ROOT/$f" >> "$OUT/26560_repository_prewrite_source_hashes.sha256" || true; done
rm -rf "$ROOT/app/src"
cp -a "$AFTER/app/src" "$ROOT/app/src"
cp "$AFTER/app/version.properties" "$ROOT/app/version.properties"
cp "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"
manifest_audited "$ROOT" "$OUT/26560_installed_precompiler.sha256"
cmp "$OUT/26560_installed_precompiler.sha256" "$CAND_PIN" >/dev/null || fail "installed candidate differs before compiler"
vendor_manifest "$ROOT" "$OUT/26560_vendor_precompiler.sha256"
cmp "$OUT/26560_vendor_precompiler.sha256" "$VENDOR_PIN" >/dev/null || fail "vendor drift before compiler"
(cd "$ROOT" && sha256sum -c "$PROTECTED_CORE") > "$OUT/26560_precompiler_protected_core.txt"
(cd "$ROOT" && sha256sum -c "$PROTECTED_GLSL") > "$OUT/26560_precompiler_protected_glsl.txt"
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" > "$OUT/26560_precompiler_contract.txt"
grep -F 'VERSION_NAME=0.9726560' "$ROOT/app/version.properties" >/dev/null || fail "version name"
grep -F 'VERSION_BUILD=26560' "$ROOT/app/version.properties" >/dev/null || fail "version build"
chmod +x ./gradlew
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace
python3 - "$OUT/26560_V1_COMPILER_STATUS.txt" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]);s=p.read_text().replace('REAL KOTLIN COMPILE: NOT RUN YET','REAL KOTLIN COMPILE: PASS').replace('REAL JAVA COMPILE: NOT RUN YET','REAL JAVA COMPILE: PASS');p.write_text(s)
PY
set_report "REAL KOTLIN COMPILE" "PASS"
set_report "REAL JAVA COMPILE" "PASS"
./gradlew :app:assembleDebug --stacktrace
python3 - "$OUT/26560_V1_COMPILER_STATUS.txt" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]);s=p.read_text().replace('NATIVE/NDK COMPILE: NOT RUN YET (covered by full assemble)','NATIVE/NDK COMPILE: PASS (full assemble)').replace('FULL ANDROID ASSEMBLE: NOT RUN YET','FULL ANDROID ASSEMBLE: PASS');p.write_text(s)
PY
set_report "NATIVE/NDK COMPILE" "PASS (full assemble)"
set_report "FULL ANDROID ASSEMBLE" "PASS"
mapfile -t APKS < <(find "$ROOT/app/build/outputs/apk/debug" -maxdepth 1 -type f -name '*.apk' -print)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one debug APK, got ${#APKS[@]}"
cp "${APKS[0]}" "$FINAL"
pass "real Kotlin/Java/NDK project compilers and full assemble"

echo "=== 26560 GATE 5: post-build frozen candidate / protected / native / vendor invariance ==="
manifest_audited "$ROOT" "$OUT/26560_postbuild_runtime.sha256"
cmp "$OUT/26560_postbuild_runtime.sha256" "$CAND_PIN" >/dev/null || fail "runtime source changed during build"
manifest_audited "$AFTER" "$OUT/26560_frozen_candidate_postbuild.sha256"
cmp "$OUT/26560_frozen_candidate_postbuild.sha256" "$CAND_PIN" >/dev/null || fail "frozen candidate changed during build"
vendor_manifest "$ROOT" "$OUT/26560_vendor_postbuild.sha256"
cmp "$OUT/26560_vendor_postbuild.sha256" "$VENDOR_PIN" >/dev/null || fail "vendor changed during build"
(cd "$ROOT" && sha256sum -c "$PROTECTED_CORE") > "$OUT/26560_postbuild_protected_core.txt"
(cd "$ROOT" && sha256sum -c "$PROTECTED_GLSL") > "$OUT/26560_postbuild_protected_glsl.txt"
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" > "$OUT/26560_postbuild_contract.txt"
mapfile -t ROOT_APKS < <(find "$ROOT" -maxdepth 1 -type f -name 'IrisCamera-*-debug.apk' -print)
[[ "${#ROOT_APKS[@]}" -eq 1 && "${ROOT_APKS[0]}" == "$FINAL" ]] || fail "root APK uniqueness"
sha256sum "$FINAL" > "$OUT/26560_V1_APK.sha256"
python3 - "$OUT/26560_V1_COMPILER_STATUS.txt" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]);p.write_text(p.read_text().replace('POST-BUILD INVARIANCE: NOT RUN YET','POST-BUILD INVARIANCE: PASS'))
PY
set_report "POST-BUILD INVARIANCE" "PASS"
pass "post-build invariance"

echo "=== 26560 GATE 6: clean candidate source export ==="
EXPORT="$WORK/export_source"; rm -rf "$EXPORT"; mkdir -p "$EXPORT/app"
cp -a "$AFTER/app/src" "$EXPORT/app/src"; cp "$AFTER/app/version.properties" "$EXPORT/app/version.properties"; cp "$AFTER/app/build.gradle" "$EXPORT/app/build.gradle"
manifest_audited "$EXPORT" "$OUT/26560_V1_candidate_source.sha256"
cmp "$OUT/26560_V1_candidate_source.sha256" "$CAND_PIN" >/dev/null || fail "export manifest mismatch"
tar -C "$EXPORT" -czf "$OUT/26560_V1_candidate_app_source.tar.gz" app
sha256sum "$OUT/26560_V1_candidate_app_source.tar.gz" > "$OUT/26560_V1_candidate_app_source.tar.gz.sha256"
set_report "CLEAN ARTIFACT SOURCE EXPORT" "PASS"
! grep -E 'REAL KOTLIN COMPILE: NOT RUN|REAL JAVA COMPILE: NOT RUN|NATIVE/NDK COMPILE: NOT RUN|FULL ANDROID ASSEMBLE: NOT RUN' "$OUT/26560_V1_STRICT_HANDOFF_REPORT.txt"
pass "26560 V1 BUILD-PROVEN Actions output"
