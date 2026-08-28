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
 root=Path(root); return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file() and '.git' not in p.parts}
a,b=m(sys.argv[1]),m(sys.argv[2])
if a!=b:
 bad=[k for k in sorted(set(a)|set(b)) if a.get(k)!=b.get(k)]
 raise SystemExit('tree mismatch: '+repr(bad[:30]))
PY
}
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
BASE_SUCCESS_COMMIT="857dcc776a7d2fc1328f1e7b9a32383b82de8c2f"
BACKUP_BRANCH="backup-26553-v1-1-before-26554-night-role-recovery"
BASE_RUN_ID="33176439804"
BASE_ARTIFACT_ID="9687928835"
BASE_ARTIFACT_NAME="photon-26553-v1-1-shutter-night-vgn-moto-diagnostic"
BASE_ARTIFACT_SHA="7a56e95bbd87e4cba4aeb472e1f4d40b748aba9e64c00e3cd6b51e74c82406bc"
BASE_TAR_SHA="9963e1ed5c041199f996c4e65cbf4682685719530717948166913abc128e7419"
BASE_MANIFEST_SHA="2a9f76220aaf6a1b1f863d1e693d6575d1abde6cfbb4a5d2a524d7053f3316ae"
CAND_MANIFEST_SHA="93157b96250eecca785695ba21de71ab3d52e0434b16c5f22bddc2afb8714325"
BASE_APK_SHA="8e49841763ae84c6fc83b9c419d2ca163126ba309ed599badafddc80d7870b49"
VENDOR_MANIFEST_SHA="7dbcc5ee5b9040965e431d79c45c5100f559c2b96c50970ca21987c684c825a8"
VERSION_NAME="0.9726554"
VERSION_BUILD="26554"
GLSLANG_PKG_VERSION="15.1.0-2~ubuntu0.24.04.2"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
BASE_PIN="$ROOT/V1_26554_BASE_26553_V1_1_AUDITED_RUNTIME.sha256"
BASE_TAR_PIN="$ROOT/V1_26554_BASE_26553_V1_1_CANDIDATE_TAR.sha256"
CAND_PIN="$ROOT/V1_26554_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256"
RUNTIME_LIST="$ROOT/V1_26554_RUNTIME_FILES.txt"
PREWRITE="$ROOT/V1_26554_PREWRITE_SOURCE_HASHES.sha256"
FORWARD="$ROOT/V1_26554_RUNTIME_DELTA_FROM_26553_V1_1.patch"
ROLLBACK="$ROOT/V1_26554_RUNTIME_ROLLBACK_TO_26553_V1_1.patch"
VALIDATE="$ROOT/validate_26554_v1_night_recovery_jin_ui.py"
EXTRACT_GLSL="$ROOT/extract_26554_protected_glsl.py"
SCAN_GLSL="$ROOT/scan_glsl_reserved_identifiers_26554.py"
PROTECTED_GLSL_PIN="$ROOT/V1_26554_PROTECTED_RUNTIME_GLSL.sha256"
HANDOFF_HASHES="$ROOT/V1_26554_HANDOFF_HASHES.sha256"
VENDOR_PIN="$ROOT/V1_26554_NATIVE_VENDOR_DEPENDENCIES.sha256"
OUT="$ROOT/build_26554_v1_night_recovery_jin_processing_guard_outputs"
WORK="$ROOT/.build_26554_v1_night_recovery_jin_processing_guard_work"
ARTZIP="$WORK/26553_v1_1_artifact.zip"; ARTDIR="$WORK/26553_v1_1_artifact"; BASE="$WORK/exact_26553_v1_1_compiled_candidate"; AFTER="$WORK/candidate_26554"; PATCHREPO="$WORK/patchrepo"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-v1-night-recovery-jin-processing-guard-debug.apk"
mapfile -t RUNTIME_FILES < "$RUNTIME_LIST"; [[ "${#RUNTIME_FILES[@]}" -eq 5 ]] || fail "runtime inventory is not 5 files"
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER"
cat > "$OUT/26554_V1_COMPILER_STATUS.txt" <<'EOF'
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF
cat > "$OUT/26554_V1_STRICT_HANDOFF_REPORT.txt" <<'EOF'
RUNTIME OWNERSHIP: NOT RUN
DORMANT-OWNER REJECTION: NOT RUN
EXACT PRIOR RUNTIME AUTHORITY: NOT RUN
CHANGED RUNTIME SCOPE: NOT RUN
NIGHT HAL QUEUE DRAIN: NOT RUN
NIGHT REQUESTED/ACTUAL ROLE RECOVERY: NOT RUN
TUNDRA 50->39 / 32->25 REGRESSION: NOT RUN
NIGHT REQUEST/EXPOSURE ROUTING INVARIANCE: NOT RUN
NIGHT JIN RGB-GRID BYPASS: NOT RUN
NIGHT SINGLE FINAL PUBLICATION: NOT RUN
PROCESSING MODE TRANSITION GUARD: NOT RUN
PROTECTED SABRE/VGN/UHDR/JIN IMPLEMENTATION: NOT RUN
GLSL RESERVED-IDENTIFIER REGRESSION: NOT RUN
26550 GAINMAP GLSL PREPROCESS REGRESSION: NOT RUN
REAL GLSL COMPILE: NOT RUN
REAL KOTLIN COMPILE: NOT RUN
REAL JAVA COMPILE: NOT RUN
FULL ANDROID ASSEMBLE: NOT RUN
FORWARD PATCH FUZZ=0: NOT RUN
ROLLBACK PATCH FUZZ=0: NOT RUN
POST-BUILD INVARIANCE: NOT RUN
CLEAN ARTIFACT SOURCE EXPORT: NOT RUN
BACKUP BRANCH: NOT RUN
TARGET VERSION/BUILD: 0.9726554 / 26554 V1
EOF
set_report(){ python3 - "$OUT/26554_V1_STRICT_HANDOFF_REPORT.txt" "$1" "$2" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); key=sys.argv[2]; val=sys.argv[3]; lines=p.read_text().splitlines()
for i,x in enumerate(lines):
 if x.startswith(key+':'): lines[i]=key+': '+val; break
else: raise SystemExit('missing report key '+key)
p.write_text('\n'.join(lines)+'\n')
PY
}

echo "=== 26554 GATE 0: sealed handoff / branch / exact package ==="
[[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
[[ "$(git rev-parse HEAD^)" == "$BASE_SUCCESS_COMMIT" ]] || fail "26554 handoff parent is not exact successful 26553 V1.1 commit"
[[ -n "$TOKEN" ]] || fail "GitHub token unavailable"
sha256sum -c "$HANDOFF_HASHES"
python3 -m py_compile "$VALIDATE" "$EXTRACT_GLSL" "$SCAN_GLSL"
python3 "$VALIDATE" --self-test
python3 "$EXTRACT_GLSL" /dev/null "$WORK/extractor-selftest-unused" --self-test
rm -rf "$WORK/extractor-selftest-unused"
python3 "$SCAN_GLSL" --self-test
bash -n "$0"
[[ "$(sha "$BASE_PIN")" == "$BASE_MANIFEST_SHA" ]] || fail "base manifest SHA drift"
[[ "$(wc -l < "$BASE_PIN")" -eq 970 ]] || fail "base manifest count"
[[ "$(sha "$CAND_PIN")" == "$CAND_MANIFEST_SHA" ]] || fail "candidate manifest SHA drift"
[[ "$(wc -l < "$CAND_PIN")" -eq 970 ]] || fail "candidate manifest count"
[[ "$(sha "$VENDOR_PIN")" == "$VENDOR_MANIFEST_SHA" ]] || fail "vendor manifest SHA drift"
[[ "$(wc -l < "$VENDOR_PIN")" -eq 778 ]] || fail "vendor manifest count"
[[ "$(wc -l < "$PROTECTED_GLSL_PIN")" -eq 2 ]] || fail "protected GLSL pin count"
grep -F "$BASE_TAR_SHA" "$BASE_TAR_PIN" >/dev/null || fail "base TAR pin drift"
python3 - "$RUNTIME_LIST" <<'PYPORT'
from pathlib import Path, PurePosixPath
import re,sys
runtime=[x.strip() for x in Path(sys.argv[1]).read_text().splitlines() if x.strip()]
def nonportable(entry):
 return (entry.startswith('/') or entry.startswith('\\\\') or re.match(r'^[A-Za-z]:[\\/]',entry) is not None or '\\' in entry or '..' in PurePosixPath(entry).parts)
# Permanent regression from 26553 V1 Actions run 33175316346/job 98862299994.
if not nonportable('/mnt/data/26553_base/app/version.properties'):
 raise SystemExit('exact /mnt/data path regression not rejected')
for p in sorted(Path('.').glob('V1_26554_*.sha256')):
 entries=[]
 for n,line in enumerate(p.read_text().splitlines(),1):
  if not line.strip(): continue
  parts=line.split(maxsplit=1)
  if len(parts)!=2 or not re.fullmatch(r'[0-9a-fA-F]{64}',parts[0]): raise SystemExit(f'{p}:{n}: malformed SHA manifest')
  entry=parts[1].lstrip('*')
  if nonportable(entry): raise SystemExit(f'{p}:{n}: non-portable path {entry!r}')
  entries.append(entry)
 if not entries: raise SystemExit(f'{p}: empty SHA manifest')
pre=[]
for line in Path('V1_26554_PREWRITE_SOURCE_HASHES.sha256').read_text().splitlines():
 if line.strip(): pre.append(line.split(maxsplit=1)[1].lstrip('*'))
if pre!=runtime: raise SystemExit('prewrite paths differ from runtime inventory')
print('PASS portable SHA manifests; exact 26553 /mnt/data regression rejected')
PYPORT
python3 - "$BASE_SUCCESS_COMMIT" <<'PYSCOPE'
import subprocess,sys
base=sys.argv[1]
allowed={
'.github/workflows/build-26554-v1-night-recovery-jin-processing-guard.yml',
'V1_26554_BASE_26553_V1_1_AUDITED_RUNTIME.sha256','V1_26554_BASE_26553_V1_1_CANDIDATE_TAR.sha256',
'V1_26554_BASE_PROVENANCE.txt','V1_26554_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256','V1_26554_HANDOFF_HASHES.sha256',
'V1_26554_LOCAL_VALIDATION.txt','V1_26554_NATIVE_VENDOR_DEPENDENCIES.sha256','V1_26554_PREWRITE_SOURCE_HASHES.sha256',
'V1_26554_PROTECTED_RUNTIME_GLSL.sha256','V1_26554_RUNTIME_DELTA_FROM_26553_V1_1.patch','V1_26554_RUNTIME_FILES.txt',
'V1_26554_RUNTIME_ROLLBACK_TO_26553_V1_1.patch','V1_26554_UPLOAD_INSTRUCTIONS.md',
'build_26554_v1_night_recovery_jin_processing_guard.sh','extract_26554_protected_glsl.py',
'scan_glsl_reserved_identifiers_26554.py','validate_26554_v1_night_recovery_jin_ui.py'}
actual=set(subprocess.check_output(['git','diff','--name-only',base+'..HEAD'],text=True).splitlines())
if actual!=allowed: raise SystemExit('handoff scope mismatch extra=%r missing=%r'%(sorted(actual-allowed),sorted(allowed-actual)))
if any(x.startswith('app/') for x in actual): raise SystemExit('handoff directly modified repository app source')
print('PASS exactly 18-file 26554 handoff; repository app source untouched')
PYSCOPE
pass "sealed candidate-first handoff"

echo "=== 26554 GATE 1: recover exact successful compiled 26553 V1.1 authority + backup ==="
REPO_API="https://api.github.com/repos/${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}"
curl --fail --location --silent --show-error --retry 5 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "$REPO_API/actions/runs/${BASE_RUN_ID}" -o "$WORK/base_run.json"
python3 - "$WORK/base_run.json" "$BASE_RUN_ID" "$BASE_SUCCESS_COMMIT" "$EXPECTED_BRANCH" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); assert str(d.get('id'))==sys.argv[2]; assert d.get('conclusion')=='success'; assert d.get('head_sha')==sys.argv[3]; assert d.get('head_branch')==sys.argv[4]
print('PASS exact 26553 V1.1 run success/commit/branch')
PY
git show-ref --verify --quiet "refs/remotes/origin/${BACKUP_BRANCH}" || fail "backup branch missing"
[[ "$(git rev-parse "origin/${BACKUP_BRANCH}")" == "$BASE_SUCCESS_COMMIT" ]] || fail "backup branch wrong commit"
set_report "BACKUP BRANCH" "PASS (${BACKUP_BRANCH} @ ${BASE_SUCCESS_COMMIT})"
curl --fail --location --silent --show-error --retry 5 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "$REPO_API/actions/artifacts/${BASE_ARTIFACT_ID}" -o "$WORK/base_artifact.json"
python3 - "$WORK/base_artifact.json" "$BASE_ARTIFACT_ID" "$BASE_ARTIFACT_NAME" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); assert str(d.get('id'))==sys.argv[2]; assert d.get('name')==sys.argv[3]; assert not d.get('expired'); print('PASS exact 26553 V1.1 artifact metadata')
PY
curl --fail --location --silent --show-error --retry 5 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "$REPO_API/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"
[[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "26553 V1.1 artifact ZIP SHA mismatch"
unzip -q "$ARTZIP" -d "$ARTDIR"
BASE_OUT="$ARTDIR/build_26553_v1_shutter_night_vgn_moto_diagnostic_outputs"
BASE_TAR="$BASE_OUT/26553_V1_candidate_app_source.tar.gz"
BASE_AUDITED="$BASE_OUT/26553_V1_candidate_source.sha256"
BASE_APK_HASH="$BASE_OUT/26553_V1_APK.sha256"
BASE_COMPILER="$BASE_OUT/26553_V1_COMPILER_STATUS.txt"
BASE_REPORT="$BASE_OUT/26553_V1_STRICT_HANDOFF_REPORT.txt"
for f in "$BASE_TAR" "$BASE_AUDITED" "$BASE_APK_HASH" "$BASE_COMPILER" "$BASE_REPORT" "$BASE_OUT/26553_vendor_postbuild.txt" "$BASE_OUT/26553_V1_candidate_app_source.tar.gz.sha256"; do [[ -f "$f" ]] || fail "base artifact missing $f"; done
[[ "$(sha "$BASE_TAR")" == "$BASE_TAR_SHA" ]] || fail "26553 V1.1 source TAR SHA mismatch"
grep -F "$BASE_TAR_SHA" "$BASE_OUT/26553_V1_candidate_app_source.tar.gz.sha256" >/dev/null || fail "persisted source TAR proof mismatch"
[[ "$(sha "$BASE_AUDITED")" == "$BASE_MANIFEST_SHA" ]] || fail "base audited manifest SHA mismatch"
cmp -s "$BASE_AUDITED" "$BASE_PIN" || fail "base manifest bytes differ"
grep -F "$BASE_APK_SHA" "$BASE_APK_HASH" >/dev/null || fail "base APK mismatch"
cmp -s "$BASE_OUT/26553_vendor_postbuild.txt" "$VENDOR_PIN" || fail "persisted vendor proof mismatch"
for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do grep -F "$proof" "$BASE_COMPILER" >/dev/null || fail "missing base compiler proof $proof"; done
grep -F 'TARGET VERSION/BUILD: 0.9726553 / 26553 V1.1' "$BASE_REPORT" >/dev/null || fail "base target report mismatch"
tar -xzf "$BASE_TAR" -C "$BASE"
manifest_audited "$BASE" "$OUT/26554_base_reconstructed.sha256"; cmp -s "$OUT/26554_base_reconstructed.sha256" "$BASE_PIN" || fail "base reconstruction mismatch"
vendor_manifest "$BASE" "$OUT/26554_vendor_base.txt"; cmp -s "$OUT/26554_vendor_base.txt" "$VENDOR_PIN" || fail "base vendor mismatch"
(cd "$BASE" && sha256sum -c "$PREWRITE") > "$OUT/26554_prewrite_hashes_verified.txt"
set_report "EXACT PRIOR RUNTIME AUTHORITY" "PASS (run ${BASE_RUN_ID}, artifact ${BASE_ARTIFACT_ID}, compiled 26553 V1.1)"
pass "exact compiled 26553 V1.1 recovered"

echo "=== 26554 GATE 2: candidate-first five-file Night ownership correction ==="
cp -a "$BASE/." "$AFTER/"
(cd "$AFTER" && patch --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 < "$FORWARD" >/dev/null)
manifest_audited "$AFTER" "$OUT/26554_candidate_source.sha256"; cmp -s "$OUT/26554_candidate_source.sha256" "$CAND_PIN" || fail "candidate manifest mismatch"
vendor_manifest "$AFTER" "$OUT/26554_vendor_candidate.txt"; cmp -s "$OUT/26554_vendor_candidate.txt" "$VENDOR_PIN" || fail "candidate vendor drift"
rm -rf "$WORK/protected_glsl_precompiler"; mkdir -p "$WORK/protected_glsl_precompiler"
python3 "$EXTRACT_GLSL" "$AFTER/app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt" "$WORK/protected_glsl_precompiler" | tee "$OUT/26554_protected_glsl_extraction.txt"
(cd "$WORK/protected_glsl_precompiler" && sha256sum -c "$PROTECTED_GLSL_PIN")
python3 "$SCAN_GLSL" --self-test | tee "$OUT/26554_reserved_identifier_regression.txt"
python3 "$SCAN_GLSL" "$WORK/protected_glsl_precompiler/directionalSmooth.comp" "$WORK/protected_glsl_precompiler/iirRgb.comp" | tee "$OUT/26554_protected_reserved_scan.txt"
python3 "$VALIDATE" "$BASE" "$AFTER" --base-manifest "$BASE_PIN" --candidate-manifest "$CAND_PIN" --vendor-manifest "$VENDOR_PIN" --glsl-dir "$WORK/protected_glsl_precompiler" | tee "$OUT/26554_runtime_contract.txt"
set_report "RUNTIME OWNERSHIP" "PASS (Night exact delivered RAW/result/request set -> immutable batch -> unchanged Sabre/VGN/Post/UHDR)"
set_report "DORMANT-OWNER REJECTION" "PASS (IrisNightNeuralEnhancer implementation remains byte-identical but has zero active enhanceInPlace caller)"
set_report "CHANGED RUNTIME SCOPE" "PASS (exact 5 files; 965 audited runtime paths unchanged)"
set_report "NIGHT HAL QUEUE DRAIN" "PASS (all currently available RAWs drained per callback and at bounded sequence grace; no device-name gates)"
set_report "NIGHT REQUESTED/ACTUAL ROLE RECOVERY" "PASS (requested roles immutable provenance; exact delivered roles own processing; >=2 Shorts; no fabrication)"
set_report "TUNDRA 50->39 / 32->25 REGRESSION" "PASS (39S+0L of 40S+10L and 25S+0L of 26S+6L accepted as degraded multiframe Night)"
set_report "NIGHT REQUEST/EXPOSURE ROUTING INVARIANCE" "PASS (Short/Long request targets, tags, exposure math byte-identical to 26553)"
set_report "NIGHT JIN RGB-GRID BYPASS" "PASS (32x32 independent RGB gain application inactive universally; Sabre/VGN/Post/UHDR retained)"
set_report "NIGHT SINGLE FINAL PUBLICATION" "PASS (base checkpoint not gallery completion; exactly one publication after final attempt)"
set_report "PROCESSING MODE TRANSITION GUARD" "PASS (mode ownership unchanged while processing; picker snaps back; wait message shown)"
set_report "PROTECTED SABRE/VGN/UHDR/JIN IMPLEMENTATION" "PASS (protected files byte-identical)"
set_report "GLSL RESERVED-IDENTIFIER REGRESSION" "PASS (exact coherent regression self-test + protected runtime shader scan)"
pass "focused high-risk Night ownership semantics validated"

echo "=== 26554 GATE 3: deterministic full-index patches / fuzz=0 ==="
rm -rf "$PATCHREPO" "$WORK/forwardcheck" "$WORK/rollbackcheck"; mkdir -p "$PATCHREPO"; cp -a "$BASE/." "$PATCHREPO/"
(cd "$PATCHREPO"; git init -q; git config user.name Photon26554; git config user.email photon26554@example.invalid; git add -A; git commit -qm base; find . -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +; cp -a "$AFTER/." .; git add -A; git diff --cached --check HEAD; for a in 7 12 40; do git -c core.abbrev=$a diff --cached --binary --full-index --no-ext-diff --no-renames HEAD > "$WORK/f.$a"; cmp -s "$WORK/f.$a" "$FORWARD" || fail "forward patch nondeterministic $a"; done; git commit -qm candidate; find . -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +; cp -a "$BASE/." .; git add -A; for a in 7 12 40; do git -c core.abbrev=$a diff --cached --binary --full-index --no-ext-diff --no-renames HEAD > "$WORK/r.$a"; cmp -s "$WORK/r.$a" "$ROLLBACK" || fail "rollback patch nondeterministic $a"; done)
mkdir -p "$WORK/forwardcheck" "$WORK/rollbackcheck"; cp -a "$BASE/." "$WORK/forwardcheck/"; (cd "$WORK/forwardcheck" && patch --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 < "$FORWARD" >/dev/null); exact_tree_equal "$WORK/forwardcheck" "$AFTER"; cp -a "$AFTER/." "$WORK/rollbackcheck/"; (cd "$WORK/rollbackcheck" && patch --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 < "$ROLLBACK" >/dev/null); exact_tree_equal "$WORK/rollbackcheck" "$BASE"
set_report "FORWARD PATCH FUZZ=0" "PASS (core.abbrev 7/12/40 byte-identical)"; set_report "ROLLBACK PATCH FUZZ=0" "PASS (core.abbrev 7/12/40 byte-identical)"
pass "patch determinism"

echo "=== 26554 GATE 4: install exact candidate / version in same authoritative script ==="
rsync -a --delete "$AFTER/app/" "$ROOT/app/"
manifest_audited "$ROOT" "$OUT/26554_installed_precompiler.sha256"; cmp -s "$OUT/26554_installed_precompiler.sha256" "$CAND_PIN" || fail "installed candidate mismatch"
vendor_manifest "$ROOT" "$OUT/26554_vendor_precompiler.txt"; cmp -s "$OUT/26554_vendor_precompiler.txt" "$VENDOR_PIN" || fail "vendor drift"
grep -Fx 'VERSION_NAME=0.9726554' app/version.properties >/dev/null; grep -Fx 'VERSION_BUILD=26554' app/version.properties >/dev/null
pass "candidate install + version target"

echo "=== 26554 GATE 5: inherited protected GLSL regressions + REAL pinned compiler ==="
sudo apt-get update -qq
apt-cache madison glslang-tools | grep -F "$GLSLANG_PKG_VERSION" >/dev/null || fail "pinned glslang unavailable"
sudo apt-get install -y --no-install-recommends "glslang-tools=${GLSLANG_PKG_VERSION}"
[[ "$(dpkg-query -W -f='${Version}' glslang-tools)" == "$GLSLANG_PKG_VERSION" ]] || fail "glslang version mismatch"
glslangValidator --version | tee "$OUT/26554_glslang_version.txt"
rm -rf "$WORK/protected_glsl_compiler"; mkdir -p "$WORK/protected_glsl_compiler"
python3 "$EXTRACT_GLSL" app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt "$WORK/protected_glsl_compiler" | tee "$OUT/26554_protected_glsl_compiler_extraction.txt"
(cd "$WORK/protected_glsl_compiler" && sha256sum -c "$PROTECTED_GLSL_PIN")
python3 "$SCAN_GLSL" --self-test | tee "$OUT/26554_reserved_identifier_compiler_regression.txt"
python3 "$SCAN_GLSL" "$WORK/protected_glsl_compiler/directionalSmooth.comp" "$WORK/protected_glsl_compiler/iirRgb.comp" | tee "$OUT/26554_protected_reserved_compiler_scan.txt"
glslangValidator -S comp "$WORK/protected_glsl_compiler/directionalSmooth.comp" | tee "$OUT/26554_glslang_directionalSmooth.txt"
glslangValidator -S comp "$WORK/protected_glsl_compiler/iirRgb.comp" | tee "$OUT/26554_glslang_iirRgb.txt"
RUNTIME_GAINMAP_SHADER="$WORK/26554_inherited_gainmap_runtime_expanded.frag"
python3 - app/src/main/assets/shaders/motionv2/gainmap.glsl app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLProg.java app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLInterface.java "$RUNTIME_GAINMAP_SHADER" <<'PYGLSL'
from pathlib import Path
import sys
asset,glprog,glinterface,out=map(Path,sys.argv[1:]); src=asset.read_text(); gp=glprog.read_text(); gi=glinterface.read_text()
if 'public final static String glVersion = "#version 310 es\\n";' not in gp: raise SystemExit('FAIL GLProg runtime version drift')
if 'String addVersion = glVersion+"\\n"+"#line 1\\n";' not in gi: raise SystemExit('FAIL GLInterface runtime prefix drift')
if '#version' in src or '#import' in src: raise SystemExit('FAIL gainmap preprocessing contract changed')
out.write_text('#version 310 es\n#line 1\n'+src)
PYGLSL
glslangValidator -S frag "$RUNTIME_GAINMAP_SHADER" | tee "$OUT/26554_glslang_inherited_gainmap.txt"
sed -i 's/REAL GLSL COMPILE: NOT RUN YET/REAL GLSL COMPILE: PASS/' "$OUT/26554_V1_COMPILER_STATUS.txt"
set_report "26550 GAINMAP GLSL PREPROCESS REGRESSION" "PASS"; set_report "REAL GLSL COMPILE" "PASS (protected unchanged VGN + inherited gainmap; pinned glslang ${GLSLANG_PKG_VERSION}; no GLSL modified by 26554)"
pass "real protected GLSL compiler regressions"

echo "=== 26554 GATE 6: REAL Kotlin + Java project compilers ==="
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace
sed -i 's/REAL KOTLIN COMPILE: NOT RUN YET/REAL KOTLIN COMPILE: PASS/' "$OUT/26554_V1_COMPILER_STATUS.txt"; sed -i 's/REAL JAVA COMPILE: NOT RUN YET/REAL JAVA COMPILE: PASS/' "$OUT/26554_V1_COMPILER_STATUS.txt"
set_report "REAL KOTLIN COMPILE" "PASS"; set_report "REAL JAVA COMPILE" "PASS"
grep -F 'java.nio.ByteBuffer source = plane.getBuffer().duplicate();' app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java >/dev/null || fail "permanent ByteBuffer javac regression"
grep -F 'import java.io.FileOutputStream;' app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java >/dev/null || fail "FileOutputStream symbol/import regression"
python3 "$VALIDATE" "$BASE" "$AFTER" --base-manifest "$BASE_PIN" --candidate-manifest "$CAND_PIN" --vendor-manifest "$VENDOR_PIN" --glsl-dir "$WORK/protected_glsl_compiler" > "$OUT/26554_postcompiler_contract.txt"
pass "real language compilers"

echo "=== 26554 GATE 7: FULL Android assemble / exactly one Gradle debug APK ==="
./gradlew :app:assembleDebug --stacktrace
mapfile -t APKS < <(find app/build/outputs/apk/debug -maxdepth 1 -type f -name '*.apk' | LC_ALL=C sort)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one Gradle debug APK found ${#APKS[@]}"
cp "${APKS[0]}" "$FINAL"; [[ -s "$FINAL" ]] || fail "final APK empty"
sha256sum "$FINAL" > "$OUT/26554_V1_APK.sha256"
sed -i 's/FULL ANDROID ASSEMBLE: NOT RUN YET/FULL ANDROID ASSEMBLE: PASS/' "$OUT/26554_V1_COMPILER_STATUS.txt"; set_report "FULL ANDROID ASSEMBLE" "PASS"
pass "full assemble"

echo "=== 26554 GATE 8: post-build frozen candidate / protected / vendor invariance ==="
manifest_audited "$ROOT" "$OUT/26554_postbuild_runtime.sha256"; cmp -s "$OUT/26554_postbuild_runtime.sha256" "$CAND_PIN" || fail "runtime changed during build"
manifest_audited "$AFTER" "$OUT/26554_frozen_candidate_postbuild.sha256"; cmp -s "$OUT/26554_frozen_candidate_postbuild.sha256" "$CAND_PIN" || fail "frozen candidate changed"
vendor_manifest "$ROOT" "$OUT/26554_vendor_postbuild.txt"; cmp -s "$OUT/26554_vendor_postbuild.txt" "$VENDOR_PIN" || fail "vendor changed"
rm -rf "$WORK/protected_glsl_postbuild"; python3 "$EXTRACT_GLSL" "$AFTER/app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt" "$WORK/protected_glsl_postbuild" >/dev/null
(cd "$WORK/protected_glsl_postbuild" && sha256sum -c "$PROTECTED_GLSL_PIN")
python3 "$SCAN_GLSL" "$WORK/protected_glsl_postbuild/directionalSmooth.comp" "$WORK/protected_glsl_postbuild/iirRgb.comp" > "$OUT/26554_postbuild_reserved_scan.txt"
python3 "$VALIDATE" "$BASE" "$AFTER" --base-manifest "$BASE_PIN" --candidate-manifest "$CAND_PIN" --vendor-manifest "$VENDOR_PIN" --glsl-dir "$WORK/protected_glsl_postbuild" > "$OUT/26554_postbuild_contract.txt"
sed -i 's/POST-BUILD INVARIANCE: NOT RUN YET/POST-BUILD INVARIANCE: PASS/' "$OUT/26554_V1_COMPILER_STATUS.txt"; set_report "POST-BUILD INVARIANCE" "PASS"
tar -czf "$OUT/26554_V1_candidate_app_source.tar.gz" -C "$AFTER" app
sha256sum "$OUT/26554_V1_candidate_app_source.tar.gz" > "$OUT/26554_V1_candidate_app_source.tar.gz.sha256"
cp "$CAND_PIN" "$OUT/26554_V1_candidate_source.sha256"; cp "$RUNTIME_LIST" "$OUT/26554_V1_actual_runtime_scope.txt"; cp "$PROTECTED_GLSL_PIN" "$OUT/26554_V1_protected_runtime_glsl.sha256"
set_report "CLEAN ARTIFACT SOURCE EXPORT" "PASS"
cat >> "$OUT/26554_V1_STRICT_HANDOFF_REPORT.txt" <<EOF
FINAL APK: $(basename "$FINAL")
FINAL APK SHA-256: $(sha "$FINAL")
BASE RUN/ARTIFACT: ${BASE_RUN_ID} / ${BASE_ARTIFACT_ID}
BASE ARTIFACT SHA-256: ${BASE_ARTIFACT_SHA}
BASE CANDIDATE TAR SHA-256: ${BASE_TAR_SHA}
BASE AUDITED MANIFEST SHA-256: ${BASE_MANIFEST_SHA}
CANDIDATE AUDITED MANIFEST SHA-256: ${CAND_MANIFEST_SHA}
VENDOR MANIFEST SHA-256: ${VENDOR_MANIFEST_SHA}
EOF
cat "$OUT/26554_V1_COMPILER_STATUS.txt"; cat "$OUT/26554_V1_STRICT_HANDOFF_REPORT.txt"
echo "PRE-BUILD SAFETY PROOF PASSED"
echo "26554 V1 BUILD SUCCESS"
