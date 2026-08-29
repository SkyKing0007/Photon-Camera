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
BASE_SUCCESS_COMMIT="928bc3d3101864f944228b0ed55b0e789fafb1dd"
BASE_RUN_ID="33233880828"
BASE_ARTIFACT_ID="9709364572"
BASE_ARTIFACT_NAME="photon-26558-v1-night-sabre-tonemap"
BASE_ARTIFACT_SHA="b2c12b144b138f40776fb4ee1a17c54ccf6de93e4198e62e5905fba480f90d52"
BASE_TAR_SHA="6bc435593ab0523b13308748ff4421d3b8752166dde44c6cb772b31ee56e77b9"
BASE_MANIFEST_SHA="348a615d62529bd9019bbd4d1634a1c54645d00f2d702e457cdabeb53289ac8c"
CAND_MANIFEST_SHA="60430f42ae65e934f87278b578e087c1cb4e87f692746c184293a85f95cc501e"
BASE_APK_SHA="29b497b601388562c98ba25889e933787322f0b84d929f9f13ad2c7e27b4f7ed"
VENDOR_MANIFEST_SHA="7dbcc5ee5b9040965e431d79c45c5100f559c2b96c50970ca21987c684c825a8"
PROTECTED_GLSL_MANIFEST_SHA="d97f6bf9c5d492e3c1873f29dfa83fab6701ec60fa9c63f2e745a0535cf28fe6"
EXPANDED_RENDER_SHA="b5baf528708213a6d8bb3dec641c100f13d1184f4114c63faa9a472e07733bcb"
GLSLANG_PKG_VERSION="15.1.0-2~ubuntu0.24.04.2"
VERSION_NAME="0.9726559"
VERSION_BUILD="26559"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"

BASE_PIN="$ROOT/V1_26559_BASE_26558_V1_AUDITED_RUNTIME.sha256"
BASE_TAR_PIN="$ROOT/V1_26559_BASE_26558_V1_CANDIDATE_TAR.sha256"
CAND_PIN="$ROOT/V1_26559_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256"
VENDOR_PIN="$ROOT/V1_26559_NATIVE_VENDOR_DEPENDENCIES.sha256"
RUNTIME_LIST="$ROOT/V1_26559_RUNTIME_FILES.txt"
PREWRITE="$ROOT/V1_26559_PREWRITE_SOURCE_HASHES.sha256"
CAND_CHANGED="$ROOT/V1_26559_CANDIDATE_CHANGED_HASHES.sha256"
FORWARD="$ROOT/V1_26559_RUNTIME_DELTA_FROM_26558_V1.patch"
ROLLBACK="$ROOT/V1_26559_RUNTIME_ROLLBACK_TO_26558_V1.patch"
VALIDATE="$ROOT/validate_26559_v1_remove_microcontrast_halo.py"
EXTRACT_GLSL="$ROOT/extract_26559_runtime_glsl.py"
SCAN_GLSL="$ROOT/scan_glsl_reserved_identifiers_26559.py"
GLSL_PIN="$ROOT/V1_26559_PROTECTED_UNCHANGED_GLSL.sha256"
EXPANDED_GLSL_PIN="$ROOT/V1_26559_RUNTIME_EXPANDED_GLSL.sha256"
HANDOFF_HASHES="$ROOT/V1_26559_HANDOFF_HASHES.sha256"
OUT="$ROOT/build_26559_v1_remove_microcontrast_halo_outputs"
WORK="$ROOT/.build_26559_v1_remove_microcontrast_halo_work"
ARTZIP="$WORK/26558_v1_artifact.zip"; ARTDIR="$WORK/artifact"; BASE="$WORK/exact_26558_compiled_candidate"; AFTER="$WORK/candidate_26559"; PATCHREPO="$WORK/patchrepo"
RUNTIME_GLSL="$WORK/runtime_glsl"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-v1-remove-microcontrast-halo-debug.apk"
mapfile -t RUNTIME_FILES < "$RUNTIME_LIST"
[[ "${#RUNTIME_FILES[@]}" -eq 2 ]] || fail "runtime inventory must contain exactly 2 files"
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER" "$RUNTIME_GLSL"

cat > "$OUT/26559_V1_COMPILER_STATUS.txt" <<'EOF'
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET (covered by full assemble)
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF
cat > "$OUT/26559_V1_STRICT_HANDOFF_REPORT.txt" <<'EOF'
EXACT PRIOR RUNTIME AUTHORITY: NOT RUN
BACKUP STATUS: NO NEW BACKUP REQUIRED (localized shader call-site correction; exact rollback patch)
CHANGED RUNTIME SCOPE: NOT RUN
MICROCONTRAST HALO REGRESSION: NOT RUN
RENDER REMAINDER INVARIANCE: NOT RUN
26558 NIGHT LONG CLIPPING/TONE INVARIANCE: NOT RUN
SABRE/VGN/JIN/UHDR INVARIANCE: NOT RUN
PROTECTED UNCHANGED GLSL INVARIANCE: NOT RUN
RUNTIME-EXPANDED GLSL HASH PROOF: NOT RUN
GLSL RESERVED-IDENTIFIER REGRESSION: NOT RUN
REAL GLSL COMPILE: NOT RUN
REAL KOTLIN COMPILE: NOT RUN
REAL JAVA COMPILE: NOT RUN
NATIVE/NDK COMPILE: NOT RUN
FULL ANDROID ASSEMBLE: NOT RUN
FORWARD PATCH FUZZ=0: NOT RUN
ROLLBACK PATCH FUZZ=0: NOT RUN
POST-BUILD INVARIANCE: NOT RUN
CLEAN ARTIFACT SOURCE EXPORT: NOT RUN
TARGET VERSION/BUILD: 0.9726559 / 26559 V1
EOF
set_report(){ python3 - "$OUT/26559_V1_STRICT_HANDOFF_REPORT.txt" "$1" "$2" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); key=sys.argv[2]; value=sys.argv[3]; lines=p.read_text().splitlines(); pref=key+':'
for i,line in enumerate(lines):
 if line.startswith(pref): lines[i]=pref+' '+value; break
else: raise SystemExit('report key missing '+key)
p.write_text('\n'.join(lines)+'\n')
PY
}

echo "=== 26559 GATE 0: sealed handoff / branch / lineage ==="
[[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
[[ "$(git rev-parse HEAD^)" == "$BASE_SUCCESS_COMMIT" ]] || fail "handoff commit must be direct child of successful 26558"
[[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"
sha256sum -c "$HANDOFF_HASHES"
python3 -m py_compile "$VALIDATE" "$EXTRACT_GLSL" "$SCAN_GLSL"
python3 "$VALIDATE" --self-test
python3 "$EXTRACT_GLSL" --self-test
python3 "$SCAN_GLSL" --self-test
bash -n "$0"
[[ "$(wc -l < "$BASE_PIN")" -eq 970 ]] || fail "base manifest count"
[[ "$(sha "$BASE_PIN")" == "$BASE_MANIFEST_SHA" ]] || fail "base manifest SHA"
[[ "$(wc -l < "$CAND_PIN")" -eq 970 ]] || fail "candidate manifest count"
[[ "$(sha "$CAND_PIN")" == "$CAND_MANIFEST_SHA" ]] || fail "candidate manifest SHA"
[[ "$(wc -l < "$VENDOR_PIN")" -eq 778 ]] || fail "vendor manifest count"
[[ "$(sha "$VENDOR_PIN")" == "$VENDOR_MANIFEST_SHA" ]] || fail "vendor manifest SHA"
[[ "$(wc -l < "$GLSL_PIN")" -eq 286 ]] || fail "protected GLSL count"
[[ "$(sha "$GLSL_PIN")" == "$PROTECTED_GLSL_MANIFEST_SHA" ]] || fail "protected GLSL manifest SHA"
[[ "$(wc -l < "$EXPANDED_GLSL_PIN")" -eq 1 ]] || fail "expanded GLSL pin count"
grep -F "$BASE_TAR_SHA" "$BASE_TAR_PIN" >/dev/null || fail "base TAR pin drift"
grep -F "$EXPANDED_RENDER_SHA  render26559.frag" "$EXPANDED_GLSL_PIN" >/dev/null || fail "expanded shader pin drift"
python3 - "$BASE_SUCCESS_COMMIT" <<'PY'
import subprocess,sys
base=sys.argv[1]
allowed={
'.github/workflows/build-26559-v1-remove-microcontrast-halo.yml',
'V1_26559_BASE_26558_V1_AUDITED_RUNTIME.sha256','V1_26559_BASE_26558_V1_CANDIDATE_TAR.sha256',
'V1_26559_BASE_PROVENANCE.txt','V1_26559_CANDIDATE_CHANGED_HASHES.sha256',
'V1_26559_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256','V1_26559_HANDOFF_HASHES.sha256',
'V1_26559_LOCAL_VALIDATION.txt','V1_26559_NATIVE_VENDOR_DEPENDENCIES.sha256',
'V1_26559_PREWRITE_SOURCE_HASHES.sha256','V1_26559_PROTECTED_UNCHANGED_GLSL.sha256',
'V1_26559_RUNTIME_DELTA_FROM_26558_V1.patch','V1_26559_RUNTIME_EXPANDED_GLSL.sha256',
'V1_26559_RUNTIME_FILES.txt','V1_26559_RUNTIME_ROLLBACK_TO_26558_V1.patch',
'V1_26559_UPLOAD_INSTRUCTIONS.md','build_26559_v1_remove_microcontrast_halo.sh',
'extract_26559_runtime_glsl.py','scan_glsl_reserved_identifiers_26559.py',
'validate_26559_v1_remove_microcontrast_halo.py'}
actual=set(subprocess.check_output(['git','diff','--name-only',base+'..HEAD'],text=True).splitlines())
if actual!=allowed: raise SystemExit('handoff scope mismatch extra=%r missing=%r'%(sorted(actual-allowed),sorted(allowed-actual)))
if any(x.startswith('app/') for x in actual): raise SystemExit('handoff directly modified repository app source')
print('PASS exact 20-file handoff scope; repository app source untouched')
PY
! grep -F 'V1_26559_' .github/workflows/build-26558-v1-night-sabre-tonemap.yml
pass "sealed 26559 package and lineage"

echo "=== 26559 GATE 1: exact successful compiled 26558 runtime authority ==="
REPO_API="https://api.github.com/repos/${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}"
curl --fail --location --silent --show-error --retry 5 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "$REPO_API/actions/runs/${BASE_RUN_ID}" -o "$WORK/base_run.json"
python3 - "$WORK/base_run.json" "$BASE_RUN_ID" "$BASE_SUCCESS_COMMIT" "$EXPECTED_BRANCH" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); assert str(d.get('id'))==sys.argv[2]; assert d.get('conclusion')=='success'; assert d.get('head_sha')==sys.argv[3]; assert d.get('head_branch')==sys.argv[4]
print('PASS exact successful 26558 Actions run')
PY
curl --fail --location --silent --show-error --retry 5 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "$REPO_API/actions/artifacts/${BASE_ARTIFACT_ID}" -o "$WORK/base_artifact.json"
python3 - "$WORK/base_artifact.json" "$BASE_ARTIFACT_ID" "$BASE_ARTIFACT_NAME" "$BASE_ARTIFACT_SHA" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); assert str(d.get('id'))==sys.argv[2]; assert d.get('name')==sys.argv[3]; assert not d.get('expired'); assert d.get('digest')=='sha256:'+sys.argv[4]
print('PASS exact 26558 artifact metadata/digest')
PY
curl --fail --location --silent --show-error --retry 5 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "$REPO_API/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"
[[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "26558 artifact ZIP SHA mismatch"
unzip -q "$ARTZIP" -d "$ARTDIR"
BASE_OUT="$ARTDIR/build_26558_v1_night_sabre_tonemap_outputs"
BASE_TAR="$BASE_OUT/26558_V1_candidate_app_source.tar.gz"
BASE_AUDITED="$BASE_OUT/26558_V1_candidate_source.sha256"
BASE_APK_HASH="$BASE_OUT/26558_V1_APK.sha256"
BASE_COMPILER="$BASE_OUT/26558_V1_COMPILER_STATUS.txt"
for f in "$BASE_TAR" "$BASE_AUDITED" "$BASE_APK_HASH" "$BASE_COMPILER" "$BASE_OUT/26558_vendor_postbuild.sha256"; do [[ -f "$f" ]] || fail "base artifact missing $f"; done
[[ "$(sha "$BASE_TAR")" == "$BASE_TAR_SHA" ]] || fail "26558 source TAR SHA mismatch"
[[ "$(sha "$BASE_AUDITED")" == "$BASE_MANIFEST_SHA" ]] || fail "26558 audited manifest SHA mismatch"
cmp "$BASE_AUDITED" "$BASE_PIN" >/dev/null || fail "packaged base pin differs from successful 26558 artifact manifest"
for s in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do grep -F "$s" "$BASE_COMPILER" >/dev/null || fail "base compiler proof missing $s"; done
grep -F "$BASE_APK_SHA" "$BASE_APK_HASH" >/dev/null || fail "26558 APK SHA proof mismatch"
tar -xzf "$BASE_TAR" -C "$BASE"
manifest_audited "$BASE" "$OUT/26558_reconstructed_runtime.sha256"
cmp "$OUT/26558_reconstructed_runtime.sha256" "$BASE_PIN" >/dev/null || fail "reconstructed 26558 source not exact"
vendor_manifest "$BASE" "$OUT/26558_vendor_base.sha256"
cmp "$OUT/26558_vendor_base.sha256" "$VENDOR_PIN" >/dev/null || fail "base vendor mismatch"
set_report "EXACT PRIOR RUNTIME AUTHORITY" "PASS (run ${BASE_RUN_ID} artifact ${BASE_ARTIFACT_ID})"
pass "exact successful compiled 26558 authority"

echo "=== 26559 GATE 2: candidate-first microcontrast bypass + exact GLSL proof ==="
(cd "$BASE" && sha256sum -c "$PREWRITE")
cp -a "$BASE/." "$AFTER/"
(cd "$AFTER" && git init -q && git config user.email audit@example.invalid && git config user.name PhotonAudit && git add -A && git commit -q -m base26558 && git apply --check "$FORWARD" && git apply "$FORWARD")
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" | tee "$OUT/26559_runtime_contract.txt"
manifest_audited "$AFTER" "$OUT/26559_candidate_runtime.sha256"
cmp "$OUT/26559_candidate_runtime.sha256" "$CAND_PIN" >/dev/null || fail "candidate manifest mismatch"
[[ "$(sha "$OUT/26559_candidate_runtime.sha256")" == "$CAND_MANIFEST_SHA" ]] || fail "candidate manifest SHA mismatch"
[[ "$(wc -l < "$OUT/26559_candidate_runtime.sha256")" -eq 970 ]] || fail "candidate manifest count"
vendor_manifest "$AFTER" "$OUT/26559_vendor_candidate.sha256"
cmp "$OUT/26559_vendor_candidate.sha256" "$VENDOR_PIN" >/dev/null || fail "candidate vendor drift"
(cd "$AFTER" && sha256sum -c "$CAND_CHANGED")
(cd "$AFTER" && sha256sum -c "$GLSL_PIN") > "$OUT/26559_protected_glsl_invariance.txt"
rm -rf "$RUNTIME_GLSL"; mkdir -p "$RUNTIME_GLSL"
python3 "$EXTRACT_GLSL" "$AFTER" "$RUNTIME_GLSL" | tee "$OUT/26559_runtime_glsl_extraction.txt"
(cd "$RUNTIME_GLSL" && sha256sum -c "$EXPANDED_GLSL_PIN") | tee "$OUT/26559_runtime_glsl_hash_proof.txt"
python3 "$SCAN_GLSL" "$RUNTIME_GLSL/render26559.frag" | tee "$OUT/26559_reserved_identifier_scan.txt"
sudo apt-get update -qq
sudo apt-get install -y --no-install-recommends "glslang-tools=${GLSLANG_PKG_VERSION}"
glslangValidator --version | tee "$OUT/26559_glslang_version.txt"
grep -F '15.1.0' "$OUT/26559_glslang_version.txt" >/dev/null || fail "wrong glslang version"
glslangValidator -S frag "$RUNTIME_GLSL/render26559.frag" > "$OUT/26559_glslang_render26559.txt" 2>&1 || { cat "$OUT/26559_glslang_render26559.txt"; fail "real GLSL compile failed"; }
set_report "CHANGED RUNTIME SCOPE" "PASS (2 files including version.properties)"
set_report "MICROCONTRAST HALO REGRESSION" "PASS (zero active legacy 5x5 invocation)"
set_report "RENDER REMAINDER INVARIANCE" "PASS"
set_report "26558 NIGHT LONG CLIPPING/TONE INVARIANCE" "PASS"
set_report "SABRE/VGN/JIN/UHDR INVARIANCE" "PASS"
set_report "PROTECTED UNCHANGED GLSL INVARIANCE" "PASS (286 files)"
set_report "RUNTIME-EXPANDED GLSL HASH PROOF" "PASS (exact active render shader)"
set_report "GLSL RESERVED-IDENTIFIER REGRESSION" "PASS"
set_report "REAL GLSL COMPILE" "PASS (pinned glslang 15.1.0; exact runtime-expanded render shader)"
python3 - "$OUT/26559_V1_COMPILER_STATUS.txt" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]);p.write_text(p.read_text().replace('REAL GLSL COMPILE: NOT RUN YET','REAL GLSL COMPILE: PASS (pinned glslang 15.1.0; exact runtime-expanded render shader)'))
PY
pass "focused halo contract + exact real GLSL compiler"

echo "=== 26559 GATE 3: canonical deterministic patch proof ==="
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

echo "=== 26559 GATE 4: controlled live install + real project compilers + full assemble ==="
: > "$OUT/26559_repository_prewrite_source_hashes.sha256"
for f in "${RUNTIME_FILES[@]}"; do [[ -f "$ROOT/$f" ]] && sha256sum "$ROOT/$f" >> "$OUT/26559_repository_prewrite_source_hashes.sha256" || true; done
rm -rf "$ROOT/app/src"
cp -a "$AFTER/app/src" "$ROOT/app/src"
cp "$AFTER/app/version.properties" "$ROOT/app/version.properties"
cp "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"
manifest_audited "$ROOT" "$OUT/26559_installed_precompiler.sha256"
cmp "$OUT/26559_installed_precompiler.sha256" "$CAND_PIN" >/dev/null || fail "installed candidate differs before compiler"
vendor_manifest "$ROOT" "$OUT/26559_vendor_precompiler.sha256"
cmp "$OUT/26559_vendor_precompiler.sha256" "$VENDOR_PIN" >/dev/null || fail "vendor drift before compiler"
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" > "$OUT/26559_precompiler_contract.txt"
grep -F 'VERSION_NAME=0.9726559' "$ROOT/app/version.properties" >/dev/null || fail "version name"
grep -F 'VERSION_BUILD=26559' "$ROOT/app/version.properties" >/dev/null || fail "version build"
chmod +x ./gradlew
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace
python3 - "$OUT/26559_V1_COMPILER_STATUS.txt" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]);s=p.read_text().replace('REAL KOTLIN COMPILE: NOT RUN YET','REAL KOTLIN COMPILE: PASS').replace('REAL JAVA COMPILE: NOT RUN YET','REAL JAVA COMPILE: PASS');p.write_text(s)
PY
set_report "REAL KOTLIN COMPILE" "PASS"
set_report "REAL JAVA COMPILE" "PASS"
./gradlew :app:assembleDebug --stacktrace
python3 - "$OUT/26559_V1_COMPILER_STATUS.txt" <<'PY'
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

echo "=== 26559 GATE 5: post-build frozen candidate / GLSL / native / vendor invariance ==="
manifest_audited "$ROOT" "$OUT/26559_postbuild_runtime.sha256"
cmp "$OUT/26559_postbuild_runtime.sha256" "$CAND_PIN" >/dev/null || fail "runtime source changed during build"
manifest_audited "$AFTER" "$OUT/26559_frozen_candidate_postbuild.sha256"
cmp "$OUT/26559_frozen_candidate_postbuild.sha256" "$CAND_PIN" >/dev/null || fail "frozen candidate changed during build"
vendor_manifest "$ROOT" "$OUT/26559_vendor_postbuild.sha256"
cmp "$OUT/26559_vendor_postbuild.sha256" "$VENDOR_PIN" >/dev/null || fail "vendor changed during build"
(cd "$ROOT" && sha256sum -c "$GLSL_PIN") > "$OUT/26559_postbuild_protected_glsl_invariance.txt"
rm -rf "$WORK/postbuild_runtime_glsl"; mkdir -p "$WORK/postbuild_runtime_glsl"
python3 "$EXTRACT_GLSL" "$ROOT" "$WORK/postbuild_runtime_glsl" > "$OUT/26559_postbuild_glsl_extraction.txt"
(cd "$WORK/postbuild_runtime_glsl" && sha256sum -c "$EXPANDED_GLSL_PIN") > "$OUT/26559_postbuild_glsl_hash_proof.txt"
python3 "$SCAN_GLSL" "$WORK/postbuild_runtime_glsl/render26559.frag" > "$OUT/26559_postbuild_reserved_scan.txt"
glslangValidator -S frag "$WORK/postbuild_runtime_glsl/render26559.frag" >/dev/null
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" > "$OUT/26559_postbuild_contract.txt"
mapfile -t ROOT_APKS < <(find "$ROOT" -maxdepth 1 -type f -name 'IrisCamera-*-debug.apk' -print)
[[ "${#ROOT_APKS[@]}" -eq 1 && "${ROOT_APKS[0]}" == "$FINAL" ]] || fail "root APK uniqueness"
sha256sum "$FINAL" > "$OUT/26559_V1_APK.sha256"
python3 - "$OUT/26559_V1_COMPILER_STATUS.txt" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]);p.write_text(p.read_text().replace('POST-BUILD INVARIANCE: NOT RUN YET','POST-BUILD INVARIANCE: PASS'))
PY
set_report "POST-BUILD INVARIANCE" "PASS"
pass "post-build invariance"

echo "=== 26559 GATE 6: clean candidate source export ==="
EXPORT="$WORK/export_source"; rm -rf "$EXPORT"; mkdir -p "$EXPORT/app"
cp -a "$AFTER/app/src" "$EXPORT/app/src"; cp "$AFTER/app/version.properties" "$EXPORT/app/version.properties"; cp "$AFTER/app/build.gradle" "$EXPORT/app/build.gradle"
manifest_audited "$EXPORT" "$OUT/26559_V1_candidate_source.sha256"
cmp "$OUT/26559_V1_candidate_source.sha256" "$CAND_PIN" >/dev/null || fail "export manifest mismatch"
tar -C "$EXPORT" -czf "$OUT/26559_V1_candidate_app_source.tar.gz" app
sha256sum "$OUT/26559_V1_candidate_app_source.tar.gz" > "$OUT/26559_V1_candidate_app_source.tar.gz.sha256"
set_report "CLEAN ARTIFACT SOURCE EXPORT" "PASS"
! grep -E 'REAL GLSL COMPILE: NOT RUN|REAL KOTLIN COMPILE: NOT RUN|REAL JAVA COMPILE: NOT RUN|NATIVE/NDK COMPILE: NOT RUN|FULL ANDROID ASSEMBLE: NOT RUN' "$OUT/26559_V1_STRICT_HANDOFF_REPORT.txt"
pass "26559 V1 BUILD-PROVEN Actions output"
