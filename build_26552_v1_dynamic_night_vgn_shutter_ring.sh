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
REPO_BASE_HEAD="69d7e35e032ac8a68b190eefffe8961897c38751"
BASE_SUCCESS_COMMIT="69d7e35e032ac8a68b190eefffe8961897c38751"
BASE_RUN_ID="33137981208"
BASE_ARTIFACT_ID="9672833483"
BASE_ARTIFACT_NAME="photon-26551-v1-night-ui-generation-style"
BASE_ARTIFACT_SHA="8ee52732a1e7b54f5f5e01bb0363ed5f18815a38d347a0046b0820a4dcc8fe4a"
BASE_TAR_SHA="3437de0724fc180b14e6cca3480a0849c77b54c304d626a4cc3be5abe1859924"
BASE_MANIFEST_SHA="c630c4d947d50b39910421ad25b33e1772f4d1e2e44c5da81f563ec16f9a2492"
CAND_MANIFEST_SHA="ee6e36bed22a70b0a658f2d69db0019270333b3739b9a9d6d73e64d06845fb4c"
BASE_APK_SHA="040852655330421cf10e3d1db389411a7825552667428f9d6b634603a818f6aa"
VENDOR_MANIFEST_SHA="7dbcc5ee5b9040965e431d79c45c5100f559c2b96c50970ca21987c684c825a8"
VERSION_NAME="0.9726552"
VERSION_BUILD="26552"
GLSLANG_PKG_VERSION="15.1.0-2~ubuntu0.24.04.2"
BACKUP_BRANCH="backup-26551-before-night-2-50-vgn-ui"
FAILED_V1_HANDOFF_COMMIT="9dd8badacae58823df2f82ba24dd26d24253042a"
FAILED_V1_FORWARD_SHA="84b95396fa1138bdafb982a168343c9fe261807bb77d0330eea961aaa0f60875"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
BASE_PIN="$ROOT/V1_26552_BASE_26551_AUDITED_RUNTIME.sha256"
BASE_TAR_PIN="$ROOT/V1_26552_BASE_26551_CANDIDATE_TAR.sha256"
CAND_PIN="$ROOT/V1_26552_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256"
RUNTIME_LIST="$ROOT/V1_26552_RUNTIME_FILES.txt"
PREWRITE="$ROOT/V1_26552_PREWRITE_SOURCE_HASHES.sha256"
FORWARD="$ROOT/V1_26552_RUNTIME_DELTA_FROM_26551.patch"
ROLLBACK="$ROOT/V1_26552_RUNTIME_ROLLBACK_TO_26551.patch"
VALIDATE="$ROOT/validate_26552_v1_dynamic_night_vgn_shutter_ring.py"
EXTRACT_GLSL="$ROOT/extract_26552_embedded_glsl.py"
RUNTIME_GLSL_PIN="$ROOT/V1_26552_RUNTIME_EXPANDED_GLSL.sha256"
HANDOFF_HASHES="$ROOT/V1_26552_HANDOFF_HASHES.sha256"
VENDOR_PIN="$ROOT/V1_26552_NATIVE_VENDOR_DEPENDENCIES.sha256"
PRECORRECTION_PIN="$ROOT/V1_26552_V1_1_PRECORRECTION_SOURCE.sha256"
OUT="$ROOT/build_26552_v1_1_dynamic_night_vgn_shutter_ring_outputs"
WORK="$ROOT/.build_26552_v1_1_dynamic_night_vgn_shutter_ring_work"
ARTZIP="$WORK/26551_artifact.zip"; ARTDIR="$WORK/26551_artifact"; BASE="$WORK/exact_26551_compiled_candidate"; AFTER="$WORK/candidate_26552"; PATCHREPO="$WORK/patchrepo"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-v1-1-dynamic-night-vgn-shutter-ring-debug.apk"
mapfile -t RUNTIME_FILES < "$RUNTIME_LIST"; [[ "${#RUNTIME_FILES[@]}" -eq 9 ]] || fail "runtime inventory is not 9 files"
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER"
cat > "$OUT/26552_V1_1_COMPILER_STATUS.txt" <<'EOF'
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF
cat > "$OUT/26552_V1_1_STRICT_HANDOFF_REPORT.txt" <<'EOF'
RUNTIME OWNERSHIP: NOT RUN
DORMANT-OWNER REJECTION: NOT RUN
EXACT PRIOR RUNTIME AUTHORITY: NOT RUN
CHANGED RUNTIME SCOPE: NOT RUN
NIGHT 2..50 SHUTTER-FROZEN FRAME PLAN: NOT RUN
NIGHT 2+0 SHORT-ONLY EXPOSURE: NOT RUN
NIGHT N>=3 LONG EXPOSURE MATH INVARIANCE: NOT RUN
NIGHT IMMUTABLE ROLE PLAN: NOT RUN
NIGHT MEMORY/SPOOL OWNERSHIP: NOT RUN
NIGHT SHUTTER-RING/PROCESSING-RING LIFECYCLE: NOT RUN
26551 STALE-CALLBACK GENERATION INVARIANCE: NOT RUN
VGN REAL-COLOR GEOMETRY SUPPORT: NOT RUN
VGN STRONG-HIGHLIGHT AUTHORITY: NOT RUN
VGN NO GLOBAL SATURATION BOOST: NOT RUN
GLSL RESERVED-IDENTIFIER REGRESSION: NOT RUN
26550 GAINMAP GLSL PREPROCESS REGRESSION: NOT RUN
REAL GLSL COMPILE: NOT RUN
REAL KOTLIN COMPILE: NOT RUN
REAL JAVA COMPILE: NOT RUN
FULL ANDROID ASSEMBLE: NOT RUN
FORWARD PATCH FUZZ=0: NOT RUN
ROLLBACK PATCH FUZZ=0: NOT RUN
POST-BUILD INVARIANCE: NOT RUN
CLEAN HANDOFF HASH REPLAY: NOT RUN
CLEAN ARTIFACT SOURCE EXPORT: NOT RUN
BACKUP BRANCH: NOT RUN
TARGET VERSION/BUILD: 0.9726552 / 26552 V1.1
EOF
set_report(){ python3 - "$OUT/26552_V1_1_STRICT_HANDOFF_REPORT.txt" "$1" "$2" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); key=sys.argv[2]; val=sys.argv[3]; lines=p.read_text().splitlines(); found=False
for i,x in enumerate(lines):
 if x.startswith(key+':'): lines[i]=key+': '+val; found=True; break
if not found: raise SystemExit('missing report key '+key)
p.write_text('\n'.join(lines)+'\n')
PY
}

echo "=== 26552 V1.1 GATE 0: sealed handoff / branch / exact package ==="
[[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
git merge-base --is-ancestor "$REPO_BASE_HEAD" HEAD || fail "handoff not descended from exact successful 26551 commit"
git merge-base --is-ancestor "$FAILED_V1_HANDOFF_COMMIT" HEAD || fail "V1.1 handoff not descended from exact failed 26552 V1 handoff commit"
[[ -n "$TOKEN" ]] || fail "GitHub token unavailable"
sha256sum -c "$HANDOFF_HASHES"
python3 -m py_compile "$VALIDATE" "$EXTRACT_GLSL"
python3 "$VALIDATE" --self-test
python3 "$EXTRACT_GLSL" /dev/null "$WORK/extractor-selftest-unused" --self-test
bash -n "$0"
[[ "$(sha "$BASE_PIN")" == "$BASE_MANIFEST_SHA" ]] || fail "base manifest SHA drift"
[[ "$(wc -l < "$BASE_PIN")" -eq 970 ]] || fail "base manifest count"
[[ "$(sha "$CAND_PIN")" == "$CAND_MANIFEST_SHA" ]] || fail "candidate manifest SHA drift"
[[ "$(wc -l < "$CAND_PIN")" -eq 970 ]] || fail "candidate manifest count"
[[ "$(sha "$VENDOR_PIN")" == "$VENDOR_MANIFEST_SHA" ]] || fail "vendor manifest SHA drift"
[[ "$(wc -l < "$VENDOR_PIN")" -eq 778 ]] || fail "vendor manifest count"
[[ "$(wc -l < "$RUNTIME_GLSL_PIN")" -eq 2 ]] || fail "expanded GLSL pin count"
grep -F "$BASE_TAR_SHA" "$BASE_TAR_PIN" >/dev/null || fail "base TAR pin drift"
[[ "$(wc -l < "$PRECORRECTION_PIN")" -eq 1 ]] || fail "V1.1 pre-correction pin count"
grep -F 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt' "$PRECORRECTION_PIN" >/dev/null || fail "V1.1 pre-correction source path drift"
python3 - "$REPO_BASE_HEAD" <<'PY'
import subprocess,sys
base=sys.argv[1]
allowed={
'.github/workflows/build-26552-v1-dynamic-night-vgn-shutter-ring.yml',
'V1_26552_BASE_26551_AUDITED_RUNTIME.sha256','V1_26552_BASE_26551_CANDIDATE_TAR.sha256',
'V1_26552_BASE_PROVENANCE.txt','V1_26552_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256',
'V1_26552_HANDOFF_HASHES.sha256','V1_26552_LOCAL_VALIDATION.txt',
'V1_26552_NATIVE_VENDOR_DEPENDENCIES.sha256','V1_26552_PREWRITE_SOURCE_HASHES.sha256',
'V1_26552_RUNTIME_DELTA_FROM_26551.patch','V1_26552_RUNTIME_FILES.txt',
'V1_26552_RUNTIME_ROLLBACK_TO_26551.patch','V1_26552_RUNTIME_EXPANDED_GLSL.sha256',
'V1_26552_UPLOAD_INSTRUCTIONS.md','V1_26552_V1_1_PRECORRECTION_SOURCE.sha256','build_26552_v1_dynamic_night_vgn_shutter_ring.sh',
'validate_26552_v1_dynamic_night_vgn_shutter_ring.py','extract_26552_embedded_glsl.py'}
actual=set(subprocess.check_output(['git','diff','--name-only',base+'..HEAD'],text=True).splitlines())
if actual!=allowed: raise SystemExit('handoff scope mismatch extra=%r missing=%r'%(sorted(actual-allowed),sorted(allowed-actual)))
print('PASS: exactly 18-file 26552 V1.1 handoff; repository app source untouched')
PY
! git diff --name-only "$REPO_BASE_HEAD..HEAD" | grep -E '^app/' >/dev/null || fail "handoff directly changed app source"
grep -F -- "- 'V1_26551_*'" .github/workflows/build-26551-v1-night-ui-generation-style.yml >/dev/null || fail "26551 trigger contract changed"
set_report "CLEAN HANDOFF HASH REPLAY" "PASS (sealed handoff file hashes)"
pass "sealed candidate-first handoff"

echo "=== 26552 V1.1 GATE 1: recover exact successful compiled 26551 authority + backup ==="
REPO_API="https://api.github.com/repos/${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}"
curl --fail --location --silent --show-error --retry 5 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "$REPO_API/actions/runs/${BASE_RUN_ID}" -o "$WORK/base_run.json"
python3 - "$WORK/base_run.json" "$BASE_RUN_ID" "$BASE_SUCCESS_COMMIT" "$EXPECTED_BRANCH" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); assert str(d.get('id'))==sys.argv[2]; assert d.get('conclusion')=='success'; assert d.get('head_sha')==sys.argv[3]; assert d.get('head_branch')==sys.argv[4]
print('PASS exact 26551 run success/commit/branch')
PY
curl --fail --location --silent --show-error --retry 5 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "$REPO_API/branches/${BACKUP_BRANCH}" -o "$WORK/backup_branch.json"
python3 - "$WORK/backup_branch.json" "$BASE_SUCCESS_COMMIT" "$BACKUP_BRANCH" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); sha=((d.get('commit') or {}).get('sha')); assert sha==sys.argv[2], (sys.argv[3],sha,sys.argv[2]); print('PASS exact backup branch='+sys.argv[3]+' sha='+sha)
PY
set_report "BACKUP BRANCH" "PASS (${BACKUP_BRANCH} @ ${BASE_SUCCESS_COMMIT})"
curl --fail --location --silent --show-error --retry 5 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "$REPO_API/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"
[[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "26551 artifact ZIP SHA mismatch"
unzip -q "$ARTZIP" -d "$ARTDIR"
BASE_OUT="$ARTDIR/build_26551_v1_night_ui_generation_style_outputs"
BASE_TAR="$BASE_OUT/26551_V1_candidate_app_source.tar.gz"
BASE_AUDITED="$BASE_OUT/26551_V1_candidate_source.sha256"
BASE_APK_HASH="$BASE_OUT/26551_V1_APK.sha256"
BASE_COMPILER="$BASE_OUT/26551_V1_COMPILER_STATUS.txt"
BASE_REPORT="$BASE_OUT/26551_V1_STRICT_HANDOFF_REPORT.txt"
for f in "$BASE_TAR" "$BASE_AUDITED" "$BASE_APK_HASH" "$BASE_COMPILER" "$BASE_REPORT" "$BASE_OUT/26551_vendor_postbuild.txt" "$BASE_OUT/26551_V1_candidate_app_source.tar.gz.sha256"; do [[ -f "$f" ]] || fail "base artifact missing $f"; done
[[ "$(sha "$BASE_TAR")" == "$BASE_TAR_SHA" ]] || fail "26551 source TAR SHA mismatch"
grep -F "$BASE_TAR_SHA" "$BASE_OUT/26551_V1_candidate_app_source.tar.gz.sha256" >/dev/null || fail "26551 persisted TAR proof mismatch"
[[ "$(sha "$BASE_AUDITED")" == "$BASE_MANIFEST_SHA" ]] || fail "base audited manifest SHA mismatch"
cmp -s "$BASE_AUDITED" "$BASE_PIN" || fail "base manifest bytes differ"
grep -F "$BASE_APK_SHA" "$BASE_APK_HASH" >/dev/null || fail "base APK mismatch"
cmp -s "$BASE_OUT/26551_vendor_postbuild.txt" "$VENDOR_PIN" || fail "persisted 26551 vendor proof mismatch"
for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do grep -F "$proof" "$BASE_COMPILER" >/dev/null || fail "missing 26551 compiler proof $proof"; done
for proof in 'POST-BUILD INVARIANCE: PASS' 'CLEAN ARTIFACT SOURCE EXPORT: PASS' 'TARGET VERSION/BUILD: 0.9726551 / 26551 V1'; do grep -F "$proof" "$BASE_REPORT" >/dev/null || fail "missing 26551 report proof $proof"; done
tar -xzf "$BASE_TAR" -C "$BASE"
manifest_audited "$BASE" "$OUT/26552_base_reconstructed.sha256"; cmp -s "$OUT/26552_base_reconstructed.sha256" "$BASE_PIN" || fail "base reconstruction mismatch"
vendor_manifest "$BASE" "$OUT/26552_vendor_base.txt"; cmp -s "$OUT/26552_vendor_base.txt" "$VENDOR_PIN" || fail "base vendor mismatch"
(cd "$BASE" && sha256sum -c "$PREWRITE") > "$OUT/26552_prewrite_hashes_verified.txt"
set_report "EXACT PRIOR RUNTIME AUTHORITY" "PASS (run ${BASE_RUN_ID}, artifact ${BASE_ARTIFACT_ID}, compiled 26551)"
pass "exact compiled 26551 recovered"

echo "=== 26552 GATE 2: candidate-first exact nine-file transform / ownership + one-file V1.1 compiler correction ==="
FAILED_V1="$WORK/failed_26552_v1_candidate"
mkdir -p "$FAILED_V1"
cp -a "$BASE/." "$FAILED_V1/"
git show "$FAILED_V1_HANDOFF_COMMIT:V1_26552_RUNTIME_DELTA_FROM_26551.patch" > "$WORK/failed_v1_forward.patch"
[[ "$(sha "$WORK/failed_v1_forward.patch")" == "$FAILED_V1_FORWARD_SHA" ]] || fail "failed V1 forward patch provenance mismatch"
(cd "$FAILED_V1" && patch --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 < "$WORK/failed_v1_forward.patch" >/dev/null && sha256sum -c "$PRECORRECTION_PIN" >/dev/null)
cp -a "$BASE/." "$AFTER/"
(cd "$AFTER" && patch --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 < "$FORWARD" >/dev/null)
python3 - "$FAILED_V1" "$AFTER" <<'PY'
from pathlib import Path
import hashlib,sys
def m(r):
 r=Path(r); return {p.relative_to(r).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in r.rglob('*') if p.is_file()}
a,b=m(sys.argv[1]),m(sys.argv[2]); d=sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k))
want=['app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt']
if d!=want: raise SystemExit('V1 -> V1.1 runtime scope mismatch '+repr(d))
sa=(Path(sys.argv[1])/want[0]).read_text(); sb=(Path(sys.argv[2])/want[0]).read_text()
# Exact corrective semantics: only two code-token replacements; comments/other VGN bytes remain unchanged.
expected=sa.replace('float coherent=smoothstep(2.4,5.2,total);','float coherentSupport=smoothstep(2.4,5.2,total);').replace('float support=max(coherent,max(tangent,oneSided));','float support=max(coherentSupport,max(tangent,oneSided));')
if expected!=sb: raise SystemExit('V1.1 VGN correction is not the exact two-token reserved-word fix')
print('PASS: failed V1 -> V1.1 is exactly one runtime file / two coherent->coherentSupport code-token replacements')
PY
python3 "$VALIDATE" "$BASE" "$AFTER" | tee "$OUT/26552_runtime_contract.txt"
manifest_audited "$AFTER" "$OUT/26552_candidate_source.sha256"; cmp -s "$OUT/26552_candidate_source.sha256" "$CAND_PIN" || fail "candidate manifest mismatch"
python3 - "$BASE" "$AFTER" "$OUT/26552_actual_changed_files.txt" <<'PY'
from pathlib import Path
import hashlib,sys
def m(r):
 r=Path(r); return {p.relative_to(r).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in r.rglob('*') if p.is_file()}
b,c=m(sys.argv[1]),m(sys.argv[2]); ch=sorted(k for k in set(b)|set(c) if b.get(k)!=c.get(k)); Path(sys.argv[3]).write_text('\n'.join(ch)+'\n')
PY
cmp -s "$OUT/26552_actual_changed_files.txt" "$RUNTIME_LIST" || fail "runtime allowlist mismatch"
mkdir -p "$WORK/26552_runtime_glsl_precompiler"
python3 "$EXTRACT_GLSL" "$AFTER/app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt" "$WORK/26552_runtime_glsl_precompiler" | tee "$OUT/26552_runtime_glsl_extraction.txt"
(cd "$WORK/26552_runtime_glsl_precompiler" && sha256sum -c "$RUNTIME_GLSL_PIN")
python3 "$VALIDATE" --check-glsl "$WORK/26552_runtime_glsl_precompiler" | tee "$OUT/26552_v1_1_glsl_reserved_identifier_regression.txt"
set_report "GLSL RESERVED-IDENTIFIER REGRESSION" "PASS (run 33143071632/job 98758015139 float coherent blocked before compiler)"
set_report "RUNTIME OWNERSHIP" "PASS (Night CaptureController -> frozen Frame/Exposure plan -> immutable IrisNightBatch -> unchanged Night/Sabre; VGN linked by Sabre/Spatial)"
set_report "DORMANT-OWNER REJECTION" "PASS (Night bypasses legacy FrameNumberSelector/Motion ZSL; only linked VGN shader strings satisfy validation)"
set_report "CHANGED RUNTIME SCOPE" "PASS (exact 9 files; 961 audited runtime paths unchanged)"
set_report "NIGHT 2..50 SHUTTER-FROZEN FRAME PLAN" "PASS (N=2 2+0; N>=3 Long=max(1,round(N/5)); max=50)"
set_report "NIGHT 2+0 SHORT-ONLY EXPOSURE" "PASS (unused Long derivation bypassed)"
set_report "NIGHT N>=3 LONG EXPOSURE MATH INVARIANCE" "PASS (26551 +2EV/shake/anti-flicker derivation byte-identical)"
set_report "NIGHT IMMUTABLE ROLE PLAN" "PASS (actual SHORT/LONG roles must equal shutter-frozen requested counts)"
set_report "NIGHT MEMORY/SPOOL OWNERSHIP" "PASS (one in-memory reference; synchronous auxiliary spool; capacity scales with frozen total)"
set_report "NIGHT SHUTTER-RING/PROCESSING-RING LIFECYCLE" "PASS (same Motion-sized processing_progress_bar determinate capture -> indeterminate processing; oversized viewfinder ring hidden)"
set_report "26551 STALE-CALLBACK GENERATION INVARIANCE" "PASS (generation/mode rejection methods byte-identical)"
set_report "VGN REAL-COLOR GEOMETRY SUPPORT" "PASS (coherent/one-sided/thin support + low-chroma cross-edge containment; color identity never selects branch)"
set_report "VGN STRONG-HIGHLIGHT AUTHORITY" "PASS (strong near-clip boundaries disable preservation overrides)"
set_report "VGN NO GLOBAL SATURATION BOOST" "PASS"
pass "runtime semantics validated"

echo "=== 26552 V1.1 GATE 3: deterministic full-index patches BEFORE live source write ==="
rm -rf "$PATCHREPO" "$WORK/forwardcheck" "$WORK/rollbackcheck"; mkdir -p "$PATCHREPO"; cp -a "$BASE/." "$PATCHREPO/"
(cd "$PATCHREPO"; git init -q; git config user.name Photon26552; git config user.email photon26552@example.invalid; git add -A; git commit -qm base; cp -a "$AFTER/." .; git add -A; git diff --cached --check HEAD; for a in 7 12 40; do git -c core.abbrev=$a diff --cached --binary --full-index --no-ext-diff HEAD > "$WORK/f.$a"; cmp -s "$WORK/f.$a" "$FORWARD" || fail "forward patch nondeterministic $a"; done; git commit -qm candidate; find . -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +; cp -a "$BASE/." .; git add -A; for a in 7 12 40; do git -c core.abbrev=$a diff --cached --binary --full-index --no-ext-diff HEAD > "$WORK/r.$a"; cmp -s "$WORK/r.$a" "$ROLLBACK" || fail "rollback patch nondeterministic $a"; done)
mkdir -p "$WORK/forwardcheck" "$WORK/rollbackcheck"; cp -a "$BASE/." "$WORK/forwardcheck/"; (cd "$WORK/forwardcheck" && patch --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 < "$FORWARD" >/dev/null); exact_tree_equal "$WORK/forwardcheck" "$AFTER"; cp -a "$AFTER/." "$WORK/rollbackcheck/"; (cd "$WORK/rollbackcheck" && patch --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 < "$ROLLBACK" >/dev/null); exact_tree_equal "$WORK/rollbackcheck" "$BASE"
set_report "FORWARD PATCH FUZZ=0" "PASS (core.abbrev 7/12/40 byte-identical)"; set_report "ROLLBACK PATCH FUZZ=0" "PASS (core.abbrev 7/12/40 byte-identical)"; pass "patch determinism"

echo "=== 26552 V1.1 GATE 4: install exact candidate into ephemeral checkout ==="
rsync -a --delete "$AFTER/app/" "$ROOT/app/"
manifest_audited "$ROOT" "$OUT/26552_installed_precompiler.sha256"; cmp -s "$OUT/26552_installed_precompiler.sha256" "$CAND_PIN" || fail "installed candidate mismatch"
vendor_manifest "$ROOT" "$OUT/26552_vendor_precompiler.txt"; cmp -s "$OUT/26552_vendor_precompiler.txt" "$VENDOR_PIN" || fail "vendor drift"
grep -Fx 'VERSION_NAME=0.9726552' app/version.properties >/dev/null; grep -Fx 'VERSION_BUILD=26552' app/version.properties >/dev/null
pass "version increment + candidate install same authoritative script"

echo "=== 26552 V1.1 GATE 5: REAL exact-runtime GLSL compilers + permanent reserved/preprocess regressions ==="
sudo apt-get update -qq
apt-cache madison glslang-tools | grep -F "$GLSLANG_PKG_VERSION" >/dev/null || fail "pinned glslang unavailable"
sudo apt-get install -y --no-install-recommends "glslang-tools=${GLSLANG_PKG_VERSION}"
[[ "$(dpkg-query -W -f='${Version}' glslang-tools)" == "$GLSLANG_PKG_VERSION" ]] || fail "glslang version mismatch"
glslangValidator --version | tee "$OUT/26552_glslang_version.txt"
rm -rf "$WORK/26552_runtime_glsl_compiler"; mkdir -p "$WORK/26552_runtime_glsl_compiler"
python3 "$EXTRACT_GLSL" app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt "$WORK/26552_runtime_glsl_compiler" | tee "$OUT/26552_runtime_glsl_compiler_extraction.txt"
(cd "$WORK/26552_runtime_glsl_compiler" && sha256sum -c "$RUNTIME_GLSL_PIN")
python3 "$VALIDATE" --check-glsl "$WORK/26552_runtime_glsl_compiler" | tee "$OUT/26552_v1_1_glsl_reserved_identifier_precompiler.txt"
glslangValidator -S comp "$WORK/26552_runtime_glsl_compiler/directionalSmooth.comp" | tee "$OUT/26552_glslang_directionalSmooth.txt"
glslangValidator -S comp "$WORK/26552_runtime_glsl_compiler/iirRgb.comp" | tee "$OUT/26552_glslang_iirRgb.txt"
RUNTIME_GAINMAP_SHADER="$WORK/26552_inherited_gainmap_runtime_expanded.frag"
python3 - app/src/main/assets/shaders/motionv2/gainmap.glsl app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLProg.java app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLInterface.java "$RUNTIME_GAINMAP_SHADER" <<'PYGLSL'
from pathlib import Path
import sys
asset, glprog, glinterface, out = map(Path, sys.argv[1:])
src=asset.read_text(); gp=glprog.read_text(); gi=glinterface.read_text()
if 'public final static String glVersion = "#version 310 es\\n";' not in gp: raise SystemExit('FAIL: GLProg runtime version drift')
if 'String addVersion = glVersion+"\\n"+"#line 1\\n";' not in gi: raise SystemExit('FAIL: GLInterface runtime prefix drift')
if '#version' in src or '#import' in src: raise SystemExit('FAIL: gainmap preprocessing contract changed')
out.write_text('#version 310 es\n#line 1\n'+src)
print('PASS: exact inherited Photon runtime gainmap expansion generated')
PYGLSL
glslangValidator -S frag "$RUNTIME_GAINMAP_SHADER" | tee "$OUT/26552_glslang_inherited_gainmap.txt"
sed -i 's/REAL GLSL COMPILE: NOT RUN YET/REAL GLSL COMPILE: PASS (exact runtime-expanded modified directionalSmooth + iirRgb; inherited gainmap regression)/' "$OUT/26552_V1_1_COMPILER_STATUS.txt"
set_report "26550 GAINMAP GLSL PREPROCESS REGRESSION" "PASS"
set_report "REAL GLSL COMPILE" "PASS (modified exact runtime-expanded directionalSmooth + iirRgb; inherited gainmap regression; pinned glslang ${GLSLANG_PKG_VERSION})"
pass "real GLSL compilers"

echo "=== 26552 GATE 6: REAL Kotlin + Java project compilers ==="
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace
sed -i 's/REAL KOTLIN COMPILE: NOT RUN YET/REAL KOTLIN COMPILE: PASS/' "$OUT/26552_V1_1_COMPILER_STATUS.txt"
sed -i 's/REAL JAVA COMPILE: NOT RUN YET/REAL JAVA COMPILE: PASS/' "$OUT/26552_V1_1_COMPILER_STATUS.txt"
set_report "REAL KOTLIN COMPILE" "PASS"; set_report "REAL JAVA COMPILE" "PASS"
grep -F 'java.nio.ByteBuffer source = plane.getBuffer().duplicate();' app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java >/dev/null || fail "permanent ByteBuffer javac regression"
grep -F 'import java.io.FileOutputStream;' app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java >/dev/null || fail "FileOutputStream symbol/import regression"
python3 "$VALIDATE" "$BASE" "$AFTER" > "$OUT/26552_postcompiler_contract.txt"
pass "real language compilers"

echo "=== 26552 GATE 7: FULL Android assemble / exactly one Gradle debug APK ==="
./gradlew :app:assembleDebug --stacktrace
mapfile -t APKS < <(find app/build/outputs/apk/debug -maxdepth 1 -type f -name '*.apk' | LC_ALL=C sort)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one Gradle debug APK found ${#APKS[@]}"
cp "${APKS[0]}" "$FINAL"; [[ -s "$FINAL" ]] || fail "final APK empty"
sha256sum "$FINAL" > "$OUT/26552_V1_APK.sha256"
sed -i 's/FULL ANDROID ASSEMBLE: NOT RUN YET/FULL ANDROID ASSEMBLE: PASS/' "$OUT/26552_V1_1_COMPILER_STATUS.txt"; set_report "FULL ANDROID ASSEMBLE" "PASS"
pass "full assemble"

echo "=== 26552 GATE 8: post-build frozen-candidate / protected / native/vendor invariance ==="
manifest_audited "$ROOT" "$OUT/26552_postbuild_runtime.sha256"; cmp -s "$OUT/26552_postbuild_runtime.sha256" "$CAND_PIN" || fail "runtime changed during build"
manifest_audited "$AFTER" "$OUT/26552_frozen_candidate_postbuild.sha256"; cmp -s "$OUT/26552_frozen_candidate_postbuild.sha256" "$CAND_PIN" || fail "frozen candidate changed"
vendor_manifest "$ROOT" "$OUT/26552_vendor_postbuild.txt"; cmp -s "$OUT/26552_vendor_postbuild.txt" "$VENDOR_PIN" || fail "vendor changed"
python3 "$VALIDATE" "$BASE" "$AFTER" > "$OUT/26552_postbuild_contract.txt"
rm -rf "$WORK/26552_runtime_glsl_postbuild"; python3 "$EXTRACT_GLSL" "$AFTER/app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt" "$WORK/26552_runtime_glsl_postbuild" >/dev/null
(cd "$WORK/26552_runtime_glsl_postbuild" && sha256sum -c "$RUNTIME_GLSL_PIN")
sed -i 's/POST-BUILD INVARIANCE: NOT RUN YET/POST-BUILD INVARIANCE: PASS/' "$OUT/26552_V1_1_COMPILER_STATUS.txt"; set_report "POST-BUILD INVARIANCE" "PASS"
tar -czf "$OUT/26552_V1_candidate_app_source.tar.gz" -C "$AFTER" app
sha256sum "$OUT/26552_V1_candidate_app_source.tar.gz" > "$OUT/26552_V1_candidate_app_source.tar.gz.sha256"
cp "$CAND_PIN" "$OUT/26552_V1_candidate_source.sha256"; cp "$RUNTIME_LIST" "$OUT/26552_V1_actual_runtime_scope.txt"; cp "$RUNTIME_GLSL_PIN" "$OUT/26552_V1_runtime_expanded_glsl.sha256"
set_report "CLEAN ARTIFACT SOURCE EXPORT" "PASS"
cat >> "$OUT/26552_V1_1_STRICT_HANDOFF_REPORT.txt" <<EOF
FINAL APK: $(basename "$FINAL")
FINAL APK SHA-256: $(sha "$FINAL")
BASE RUN/ARTIFACT: ${BASE_RUN_ID} / ${BASE_ARTIFACT_ID}
BASE ARTIFACT SHA-256: ${BASE_ARTIFACT_SHA}
BASE CANDIDATE TAR SHA-256: ${BASE_TAR_SHA}
BASE AUDITED MANIFEST SHA-256: ${BASE_MANIFEST_SHA}
CANDIDATE AUDITED MANIFEST SHA-256: ${CAND_MANIFEST_SHA}
VENDOR MANIFEST SHA-256: ${VENDOR_MANIFEST_SHA}
EOF
cat "$OUT/26552_V1_1_COMPILER_STATUS.txt"; cat "$OUT/26552_V1_1_STRICT_HANDOFF_REPORT.txt"
echo "PRE-BUILD SAFETY PROOF PASSED"
echo "26552 V1.1 BUILD SUCCESS"
