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
BASE_SUCCESS_COMMIT="8e4904530e767ac8bdd3fbf3ec8d81e98cd6e8ec"
BASE_RUN_ID="33143648461"
BASE_ARTIFACT_ID="9674993907"
BASE_ARTIFACT_NAME="photon-26552-v1-1-dynamic-night-vgn-shutter-ring"
BASE_ARTIFACT_SHA="44e7b92fe434b2039fef303f0e4f614a022d0a95fbaaa058d7539c9783cd820e"
BASE_TAR_SHA="98fea536c5a4372e09ec9d6d4af2cc871b3534a90afd678dcd265992ef736068"
BASE_MANIFEST_SHA="ee6e36bed22a70b0a658f2d69db0019270333b3739b9a9d6d73e64d06845fb4c"
CAND_MANIFEST_SHA="2a9f76220aaf6a1b1f863d1e693d6575d1abde6cfbb4a5d2a524d7053f3316ae"
BASE_APK_SHA="154585dcfce888acf996c14be94da812d733e93ba90355f1530c2843a0115f6c"
VENDOR_MANIFEST_SHA="7dbcc5ee5b9040965e431d79c45c5100f559c2b96c50970ca21987c684c825a8"
VERSION_NAME="0.9726553"
VERSION_BUILD="26553"
GLSLANG_PKG_VERSION="15.1.0-2~ubuntu0.24.04.2"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
BASE_PIN="$ROOT/V1_26553_BASE_26552_V1_1_AUDITED_RUNTIME.sha256"
BASE_TAR_PIN="$ROOT/V1_26553_BASE_26552_V1_1_CANDIDATE_TAR.sha256"
CAND_PIN="$ROOT/V1_26553_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256"
RUNTIME_LIST="$ROOT/V1_26553_RUNTIME_FILES.txt"
PREWRITE="$ROOT/V1_26553_PREWRITE_SOURCE_HASHES.sha256"
FORWARD="$ROOT/V1_26553_RUNTIME_DELTA_FROM_26552_V1_1.patch"
ROLLBACK="$ROOT/V1_26553_RUNTIME_ROLLBACK_TO_26552_V1_1.patch"
VALIDATE="$ROOT/validate_26553_v1_shutter_night_vgn_moto.py"
EXTRACT_GLSL="$ROOT/extract_26553_embedded_glsl.py"
SCAN_GLSL="$ROOT/scan_glsl_reserved_identifiers_26553.py"
RUNTIME_GLSL_PIN="$ROOT/V1_26553_RUNTIME_EXPANDED_GLSL.sha256"
HANDOFF_HASHES="$ROOT/V1_26553_HANDOFF_HASHES.sha256"
VENDOR_PIN="$ROOT/V1_26553_NATIVE_VENDOR_DEPENDENCIES.sha256"
OUT="$ROOT/build_26553_v1_shutter_night_vgn_moto_diagnostic_outputs"
WORK="$ROOT/.build_26553_v1_shutter_night_vgn_moto_diagnostic_work"
ARTZIP="$WORK/26552_v1_1_artifact.zip"; ARTDIR="$WORK/26552_v1_1_artifact"; BASE="$WORK/exact_26552_v1_1_compiled_candidate"; AFTER="$WORK/candidate_26553"; PATCHREPO="$WORK/patchrepo"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-v1-shutter-night-vgn-moto-diagnostic-debug.apk"
mapfile -t RUNTIME_FILES < "$RUNTIME_LIST"; [[ "${#RUNTIME_FILES[@]}" -eq 5 ]] || fail "runtime inventory is not 5 files"
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER"
cat > "$OUT/26553_V1_COMPILER_STATUS.txt" <<'EOF'
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF
cat > "$OUT/26553_V1_STRICT_HANDOFF_REPORT.txt" <<'EOF'
RUNTIME OWNERSHIP: NOT RUN
DORMANT-OWNER REJECTION: NOT RUN
EXACT PRIOR RUNTIME AUTHORITY: NOT RUN
CHANGED RUNTIME SCOPE: NOT RUN
SHUTTER THREE-SEQUENCE UI CONTRACT: NOT RUN
NIGHT DUPLICATE-ARM REGRESSION: NOT RUN
NIGHT 2..50/SABRE INVARIANCE: NOT RUN
VGN REFERENCE DIRECTIONAL/IIR RESTORATION: NOT RUN
MOTOROLA-A PREVIEW DIAGNOSTICS ISOLATION: NOT RUN
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
BACKUP: NOT REQUIRED (localized correction/diagnostics)
TARGET VERSION/BUILD: 0.9726553 / 26553 V1
EOF
set_report(){ python3 - "$OUT/26553_V1_STRICT_HANDOFF_REPORT.txt" "$1" "$2" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); key=sys.argv[2]; val=sys.argv[3]; lines=p.read_text().splitlines()
for i,x in enumerate(lines):
 if x.startswith(key+':'): lines[i]=key+': '+val; break
else: raise SystemExit('missing report key '+key)
p.write_text('\n'.join(lines)+'\n')
PY
}

echo "=== 26553 GATE 0: sealed handoff / branch / exact package ==="
[[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
[[ "$(git rev-parse HEAD^)" == "$BASE_SUCCESS_COMMIT" ]] || fail "26553 handoff parent is not exact successful 26552 V1.1 commit"
[[ -n "$TOKEN" ]] || fail "GitHub token unavailable"
sha256sum -c "$HANDOFF_HASHES"
python3 -m py_compile "$VALIDATE" "$EXTRACT_GLSL" "$SCAN_GLSL"
python3 "$VALIDATE" --self-test
python3 "$EXTRACT_GLSL" /dev/null "$WORK/extractor-selftest-unused" --self-test
python3 "$SCAN_GLSL" --self-test
bash -n "$0"
[[ "$(sha "$BASE_PIN")" == "$BASE_MANIFEST_SHA" ]] || fail "base manifest SHA drift"
[[ "$(wc -l < "$BASE_PIN")" -eq 970 ]] || fail "base manifest count"
[[ "$(sha "$CAND_PIN")" == "$CAND_MANIFEST_SHA" ]] || fail "candidate manifest SHA drift"
[[ "$(wc -l < "$CAND_PIN")" -eq 970 ]] || fail "candidate manifest count"
[[ "$(sha "$VENDOR_PIN")" == "$VENDOR_MANIFEST_SHA" ]] || fail "vendor manifest SHA drift"
[[ "$(wc -l < "$VENDOR_PIN")" -eq 778 ]] || fail "vendor manifest count"
[[ "$(wc -l < "$RUNTIME_GLSL_PIN")" -eq 2 ]] || fail "expanded GLSL pin count"
grep -F "$BASE_TAR_SHA" "$BASE_TAR_PIN" >/dev/null || fail "base TAR pin drift"
python3 - "$BASE_SUCCESS_COMMIT" <<'PY'
import subprocess,sys
base=sys.argv[1]
allowed={
'.github/workflows/build-26553-v1-shutter-night-vgn-moto-diagnostic.yml',
'V1_26553_BASE_26552_V1_1_AUDITED_RUNTIME.sha256','V1_26553_BASE_26552_V1_1_CANDIDATE_TAR.sha256',
'V1_26553_BASE_PROVENANCE.txt','V1_26553_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256','V1_26553_HANDOFF_HASHES.sha256',
'V1_26553_LOCAL_VALIDATION.txt','V1_26553_NATIVE_VENDOR_DEPENDENCIES.sha256','V1_26553_PREWRITE_SOURCE_HASHES.sha256',
'V1_26553_RUNTIME_DELTA_FROM_26552_V1_1.patch','V1_26553_RUNTIME_EXPANDED_GLSL.sha256','V1_26553_RUNTIME_FILES.txt',
'V1_26553_RUNTIME_ROLLBACK_TO_26552_V1_1.patch','V1_26553_UPLOAD_INSTRUCTIONS.md',
'build_26553_v1_shutter_night_vgn_moto_diagnostic.sh','extract_26553_embedded_glsl.py',
'scan_glsl_reserved_identifiers_26553.py','validate_26553_v1_shutter_night_vgn_moto.py'}
actual=set(subprocess.check_output(['git','diff','--name-only',base+'..HEAD'],text=True).splitlines())
if actual!=allowed: raise SystemExit('handoff scope mismatch extra=%r missing=%r'%(sorted(actual-allowed),sorted(allowed-actual)))
if any(x.startswith('app/') for x in actual): raise SystemExit('handoff directly modified repository app source')
print('PASS exactly 18-file 26553 handoff; repository app source untouched')
PY
pass "sealed candidate-first handoff"

echo "=== 26553 GATE 1: recover exact successful compiled 26552 V1.1 authority ==="
REPO_API="https://api.github.com/repos/${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}"
curl --fail --location --silent --show-error --retry 5 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "$REPO_API/actions/runs/${BASE_RUN_ID}" -o "$WORK/base_run.json"
python3 - "$WORK/base_run.json" "$BASE_RUN_ID" "$BASE_SUCCESS_COMMIT" "$EXPECTED_BRANCH" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); assert str(d.get('id'))==sys.argv[2]; assert d.get('conclusion')=='success'; assert d.get('head_sha')==sys.argv[3]; assert d.get('head_branch')==sys.argv[4]
print('PASS exact 26552 V1.1 run success/commit/branch')
PY
curl --fail --location --silent --show-error --retry 5 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "$REPO_API/actions/artifacts/${BASE_ARTIFACT_ID}" -o "$WORK/base_artifact.json"
python3 - "$WORK/base_artifact.json" "$BASE_ARTIFACT_ID" "$BASE_ARTIFACT_NAME" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); assert str(d.get('id'))==sys.argv[2]; assert d.get('name')==sys.argv[3]; assert not d.get('expired'); print('PASS exact 26552 V1.1 artifact metadata')
PY
curl --fail --location --silent --show-error --retry 5 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "$REPO_API/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"
[[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "26552 V1.1 artifact ZIP SHA mismatch"
unzip -q "$ARTZIP" -d "$ARTDIR"
BASE_OUT="$ARTDIR/build_26552_v1_1_dynamic_night_vgn_shutter_ring_outputs"
BASE_TAR="$BASE_OUT/26552_V1_candidate_app_source.tar.gz"
BASE_AUDITED="$BASE_OUT/26552_V1_candidate_source.sha256"
BASE_APK_HASH="$BASE_OUT/26552_V1_APK.sha256"
BASE_COMPILER="$BASE_OUT/26552_V1_1_COMPILER_STATUS.txt"
BASE_REPORT="$BASE_OUT/26552_V1_1_STRICT_HANDOFF_REPORT.txt"
for f in "$BASE_TAR" "$BASE_AUDITED" "$BASE_APK_HASH" "$BASE_COMPILER" "$BASE_REPORT" "$BASE_OUT/26552_vendor_postbuild.txt" "$BASE_OUT/26552_V1_candidate_app_source.tar.gz.sha256"; do [[ -f "$f" ]] || fail "base artifact missing $f"; done
[[ "$(sha "$BASE_TAR")" == "$BASE_TAR_SHA" ]] || fail "26552 V1.1 source TAR SHA mismatch"
grep -F "$BASE_TAR_SHA" "$BASE_OUT/26552_V1_candidate_app_source.tar.gz.sha256" >/dev/null || fail "persisted source TAR proof mismatch"
[[ "$(sha "$BASE_AUDITED")" == "$BASE_MANIFEST_SHA" ]] || fail "base audited manifest SHA mismatch"
cmp -s "$BASE_AUDITED" "$BASE_PIN" || fail "base manifest bytes differ"
grep -F "$BASE_APK_SHA" "$BASE_APK_HASH" >/dev/null || fail "base APK mismatch"
cmp -s "$BASE_OUT/26552_vendor_postbuild.txt" "$VENDOR_PIN" || fail "persisted vendor proof mismatch"
for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do grep -F "$proof" "$BASE_COMPILER" >/dev/null || fail "missing base compiler proof $proof"; done
grep -F 'TARGET VERSION/BUILD: 0.9726552 / 26552 V1.1' "$BASE_REPORT" >/dev/null || fail "base target report mismatch"
tar -xzf "$BASE_TAR" -C "$BASE"
manifest_audited "$BASE" "$OUT/26553_base_reconstructed.sha256"; cmp -s "$OUT/26553_base_reconstructed.sha256" "$BASE_PIN" || fail "base reconstruction mismatch"
vendor_manifest "$BASE" "$OUT/26553_vendor_base.txt"; cmp -s "$OUT/26553_vendor_base.txt" "$VENDOR_PIN" || fail "base vendor mismatch"
(cd "$BASE" && sha256sum -c "$PREWRITE") > "$OUT/26553_prewrite_hashes_verified.txt"
set_report "EXACT PRIOR RUNTIME AUTHORITY" "PASS (run ${BASE_RUN_ID}, artifact ${BASE_ARTIFACT_ID}, compiled 26552 V1.1)"
pass "exact compiled 26552 V1.1 recovered"

echo "=== 26553 GATE 2: candidate-first five-file correction / focused ownership ==="
cp -a "$BASE/." "$AFTER/"
(cd "$AFTER" && patch --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 < "$FORWARD" >/dev/null)
manifest_audited "$AFTER" "$OUT/26553_candidate_source.sha256"; cmp -s "$OUT/26553_candidate_source.sha256" "$CAND_PIN" || fail "candidate manifest mismatch"
vendor_manifest "$AFTER" "$OUT/26553_vendor_candidate.txt"; cmp -s "$OUT/26553_vendor_candidate.txt" "$VENDOR_PIN" || fail "candidate vendor drift"
mkdir -p "$WORK/runtime_glsl_precompiler"
python3 "$EXTRACT_GLSL" "$AFTER/app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt" "$WORK/runtime_glsl_precompiler" | tee "$OUT/26553_runtime_glsl_extraction.txt"
(cd "$WORK/runtime_glsl_precompiler" && sha256sum -c "$RUNTIME_GLSL_PIN")
python3 "$SCAN_GLSL" --self-test | tee "$OUT/26553_reserved_identifier_exact_coherent_regression.txt"
python3 "$SCAN_GLSL" "$WORK/runtime_glsl_precompiler/directionalSmooth.comp" "$WORK/runtime_glsl_precompiler/iirRgb.comp" | tee "$OUT/26553_reserved_identifier_scan.txt"
python3 "$VALIDATE" "$BASE" "$AFTER" --base-manifest "$BASE_PIN" --candidate-manifest "$CAND_PIN" --vendor-manifest "$VENDOR_PIN" --glsl-dir "$WORK/runtime_glsl_precompiler" | tee "$OUT/26553_runtime_contract.txt"
set_report "RUNTIME OWNERSHIP" "PASS (active still UI/CaptureController/VGN/preview renderer owners proven)"
set_report "DORMANT-OWNER REJECTION" "PASS (validation requires linked VGN strings and live Camera2/renderer owners)"
set_report "CHANGED RUNTIME SCOPE" "PASS (exact 5 files; 965 audited runtime paths unchanged)"
set_report "SHUTTER THREE-SEQUENCE UI CONTRACT" "PASS (cold Motion -> Night capture/process -> Motion; 0.83 still baseline; 1..N Night counter)"
set_report "NIGHT DUPLICATE-ARM REGRESSION" "PASS (AF timeout returns after one dispatch; pending/active/processing single-flight guard)"
set_report "NIGHT 2..50/SABRE INVARIANCE" "PASS (frame/exposure/batch/processor/Sabre files byte-identical)"
set_report "VGN REFERENCE DIRECTIONAL/IIR RESTORATION" "PASS (failed Iris preservation overrides removed; unrelated VGN shaders unchanged)"
set_report "MOTOROLA-A PREVIEW DIAGNOSTICS ISOLATION" "PASS (Camera2/SurfaceTexture/EGL/GL logs only; no preview shader/session routing file changes)"
set_report "GLSL RESERVED-IDENTIFIER REGRESSION" "PASS (complete declared-identifier scan + exact coherent failure self-test)"
pass "focused runtime semantics validated"

echo "=== 26553 GATE 3: deterministic full-index patches / fuzz=0 ==="
rm -rf "$PATCHREPO" "$WORK/forwardcheck" "$WORK/rollbackcheck"; mkdir -p "$PATCHREPO"; cp -a "$BASE/." "$PATCHREPO/"
(cd "$PATCHREPO"; git init -q; git config user.name Photon26553; git config user.email photon26553@example.invalid; git add -A; git commit -qm base; find . -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +; cp -a "$AFTER/." .; git add -A; git diff --cached --check HEAD; for a in 7 12 40; do git -c core.abbrev=$a diff --cached --binary --full-index --no-ext-diff --no-renames HEAD > "$WORK/f.$a"; cmp -s "$WORK/f.$a" "$FORWARD" || fail "forward patch nondeterministic $a"; done; git commit -qm candidate; find . -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +; cp -a "$BASE/." .; git add -A; for a in 7 12 40; do git -c core.abbrev=$a diff --cached --binary --full-index --no-ext-diff --no-renames HEAD > "$WORK/r.$a"; cmp -s "$WORK/r.$a" "$ROLLBACK" || fail "rollback patch nondeterministic $a"; done)
mkdir -p "$WORK/forwardcheck" "$WORK/rollbackcheck"; cp -a "$BASE/." "$WORK/forwardcheck/"; (cd "$WORK/forwardcheck" && patch --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 < "$FORWARD" >/dev/null); exact_tree_equal "$WORK/forwardcheck" "$AFTER"; cp -a "$AFTER/." "$WORK/rollbackcheck/"; (cd "$WORK/rollbackcheck" && patch --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 < "$ROLLBACK" >/dev/null); exact_tree_equal "$WORK/rollbackcheck" "$BASE"
set_report "FORWARD PATCH FUZZ=0" "PASS (core.abbrev 7/12/40 byte-identical)"; set_report "ROLLBACK PATCH FUZZ=0" "PASS (core.abbrev 7/12/40 byte-identical)"
pass "patch determinism"

echo "=== 26553 GATE 4: install exact candidate / version in same authoritative script ==="
rsync -a --delete "$AFTER/app/" "$ROOT/app/"
manifest_audited "$ROOT" "$OUT/26553_installed_precompiler.sha256"; cmp -s "$OUT/26553_installed_precompiler.sha256" "$CAND_PIN" || fail "installed candidate mismatch"
vendor_manifest "$ROOT" "$OUT/26553_vendor_precompiler.txt"; cmp -s "$OUT/26553_vendor_precompiler.txt" "$VENDOR_PIN" || fail "vendor drift"
grep -Fx 'VERSION_NAME=0.9726553' app/version.properties >/dev/null; grep -Fx 'VERSION_BUILD=26553' app/version.properties >/dev/null
pass "candidate install + version target"

echo "=== 26553 GATE 5: complete reserved scan + REAL pinned runtime GLSL compilers ==="
sudo apt-get update -qq
apt-cache madison glslang-tools | grep -F "$GLSLANG_PKG_VERSION" >/dev/null || fail "pinned glslang unavailable"
sudo apt-get install -y --no-install-recommends "glslang-tools=${GLSLANG_PKG_VERSION}"
[[ "$(dpkg-query -W -f='${Version}' glslang-tools)" == "$GLSLANG_PKG_VERSION" ]] || fail "glslang version mismatch"
glslangValidator --version | tee "$OUT/26553_glslang_version.txt"
rm -rf "$WORK/runtime_glsl_compiler"; mkdir -p "$WORK/runtime_glsl_compiler"
python3 "$EXTRACT_GLSL" app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt "$WORK/runtime_glsl_compiler" | tee "$OUT/26553_runtime_glsl_compiler_extraction.txt"
(cd "$WORK/runtime_glsl_compiler" && sha256sum -c "$RUNTIME_GLSL_PIN")
python3 "$SCAN_GLSL" --self-test | tee "$OUT/26553_reserved_identifier_precompiler_regression.txt"
python3 "$SCAN_GLSL" "$WORK/runtime_glsl_compiler/directionalSmooth.comp" "$WORK/runtime_glsl_compiler/iirRgb.comp" | tee "$OUT/26553_reserved_identifier_precompiler_scan.txt"
glslangValidator -S comp "$WORK/runtime_glsl_compiler/directionalSmooth.comp" | tee "$OUT/26553_glslang_directionalSmooth.txt"
glslangValidator -S comp "$WORK/runtime_glsl_compiler/iirRgb.comp" | tee "$OUT/26553_glslang_iirRgb.txt"
# Inherited 26550 runtime-preprocess regression remains applicable to the unchanged gainmap path.
RUNTIME_GAINMAP_SHADER="$WORK/26553_inherited_gainmap_runtime_expanded.frag"
python3 - app/src/main/assets/shaders/motionv2/gainmap.glsl app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLProg.java app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLInterface.java "$RUNTIME_GAINMAP_SHADER" <<'PYGLSL'
from pathlib import Path
import sys
asset, glprog, glinterface, out = map(Path, sys.argv[1:]); src=asset.read_text(); gp=glprog.read_text(); gi=glinterface.read_text()
if 'public final static String glVersion = "#version 310 es\\n";' not in gp: raise SystemExit('FAIL GLProg runtime version drift')
if 'String addVersion = glVersion+"\\n"+"#line 1\\n";' not in gi: raise SystemExit('FAIL GLInterface runtime prefix drift')
if '#version' in src or '#import' in src: raise SystemExit('FAIL gainmap preprocessing contract changed')
out.write_text('#version 310 es\n#line 1\n'+src)
PYGLSL
glslangValidator -S frag "$RUNTIME_GAINMAP_SHADER" | tee "$OUT/26553_glslang_inherited_gainmap.txt"
sed -i 's/REAL GLSL COMPILE: NOT RUN YET/REAL GLSL COMPILE: PASS/' "$OUT/26553_V1_COMPILER_STATUS.txt"
set_report "26550 GAINMAP GLSL PREPROCESS REGRESSION" "PASS"; set_report "REAL GLSL COMPILE" "PASS (exact modified runtime shaders; pinned glslang ${GLSLANG_PKG_VERSION})"
pass "real GLSL compilers"

echo "=== 26553 GATE 6: REAL Kotlin + Java project compilers ==="
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace
sed -i 's/REAL KOTLIN COMPILE: NOT RUN YET/REAL KOTLIN COMPILE: PASS/' "$OUT/26553_V1_COMPILER_STATUS.txt"; sed -i 's/REAL JAVA COMPILE: NOT RUN YET/REAL JAVA COMPILE: PASS/' "$OUT/26553_V1_COMPILER_STATUS.txt"
set_report "REAL KOTLIN COMPILE" "PASS"; set_report "REAL JAVA COMPILE" "PASS"
grep -F 'java.nio.ByteBuffer source = plane.getBuffer().duplicate();' app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java >/dev/null || fail "permanent ByteBuffer javac regression"
grep -F 'import java.io.FileOutputStream;' app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java >/dev/null || fail "FileOutputStream symbol/import regression"
grep -F 'import android.os.Build;' app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java >/dev/null || fail "Build diagnostic symbol/import regression"
python3 "$VALIDATE" "$BASE" "$AFTER" --base-manifest "$BASE_PIN" --candidate-manifest "$CAND_PIN" --vendor-manifest "$VENDOR_PIN" --glsl-dir "$WORK/runtime_glsl_compiler" > "$OUT/26553_postcompiler_contract.txt"
pass "real language compilers"

echo "=== 26553 GATE 7: FULL Android assemble / exactly one Gradle debug APK ==="
./gradlew :app:assembleDebug --stacktrace
mapfile -t APKS < <(find app/build/outputs/apk/debug -maxdepth 1 -type f -name '*.apk' | LC_ALL=C sort)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one Gradle debug APK found ${#APKS[@]}"
cp "${APKS[0]}" "$FINAL"; [[ -s "$FINAL" ]] || fail "final APK empty"
sha256sum "$FINAL" > "$OUT/26553_V1_APK.sha256"
sed -i 's/FULL ANDROID ASSEMBLE: NOT RUN YET/FULL ANDROID ASSEMBLE: PASS/' "$OUT/26553_V1_COMPILER_STATUS.txt"; set_report "FULL ANDROID ASSEMBLE" "PASS"
pass "full assemble"

echo "=== 26553 GATE 8: post-build frozen candidate / vendor invariance ==="
manifest_audited "$ROOT" "$OUT/26553_postbuild_runtime.sha256"; cmp -s "$OUT/26553_postbuild_runtime.sha256" "$CAND_PIN" || fail "runtime changed during build"
manifest_audited "$AFTER" "$OUT/26553_frozen_candidate_postbuild.sha256"; cmp -s "$OUT/26553_frozen_candidate_postbuild.sha256" "$CAND_PIN" || fail "frozen candidate changed"
vendor_manifest "$ROOT" "$OUT/26553_vendor_postbuild.txt"; cmp -s "$OUT/26553_vendor_postbuild.txt" "$VENDOR_PIN" || fail "vendor changed"
rm -rf "$WORK/runtime_glsl_postbuild"; python3 "$EXTRACT_GLSL" "$AFTER/app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt" "$WORK/runtime_glsl_postbuild" >/dev/null
(cd "$WORK/runtime_glsl_postbuild" && sha256sum -c "$RUNTIME_GLSL_PIN")
python3 "$SCAN_GLSL" "$WORK/runtime_glsl_postbuild/directionalSmooth.comp" "$WORK/runtime_glsl_postbuild/iirRgb.comp" > "$OUT/26553_postbuild_reserved_scan.txt"
python3 "$VALIDATE" "$BASE" "$AFTER" --base-manifest "$BASE_PIN" --candidate-manifest "$CAND_PIN" --vendor-manifest "$VENDOR_PIN" --glsl-dir "$WORK/runtime_glsl_postbuild" > "$OUT/26553_postbuild_contract.txt"
sed -i 's/POST-BUILD INVARIANCE: NOT RUN YET/POST-BUILD INVARIANCE: PASS/' "$OUT/26553_V1_COMPILER_STATUS.txt"; set_report "POST-BUILD INVARIANCE" "PASS"
tar -czf "$OUT/26553_V1_candidate_app_source.tar.gz" -C "$AFTER" app
sha256sum "$OUT/26553_V1_candidate_app_source.tar.gz" > "$OUT/26553_V1_candidate_app_source.tar.gz.sha256"
cp "$CAND_PIN" "$OUT/26553_V1_candidate_source.sha256"; cp "$RUNTIME_LIST" "$OUT/26553_V1_actual_runtime_scope.txt"; cp "$RUNTIME_GLSL_PIN" "$OUT/26553_V1_runtime_expanded_glsl.sha256"
set_report "CLEAN ARTIFACT SOURCE EXPORT" "PASS"
cat >> "$OUT/26553_V1_STRICT_HANDOFF_REPORT.txt" <<EOF
FINAL APK: $(basename "$FINAL")
FINAL APK SHA-256: $(sha "$FINAL")
BASE RUN/ARTIFACT: ${BASE_RUN_ID} / ${BASE_ARTIFACT_ID}
BASE ARTIFACT SHA-256: ${BASE_ARTIFACT_SHA}
BASE CANDIDATE TAR SHA-256: ${BASE_TAR_SHA}
BASE AUDITED MANIFEST SHA-256: ${BASE_MANIFEST_SHA}
CANDIDATE AUDITED MANIFEST SHA-256: ${CAND_MANIFEST_SHA}
VENDOR MANIFEST SHA-256: ${VENDOR_MANIFEST_SHA}
EOF
cat "$OUT/26553_V1_COMPILER_STATUS.txt"; cat "$OUT/26553_V1_STRICT_HANDOFF_REPORT.txt"
echo "PRE-BUILD SAFETY PROOF PASSED"
echo "26553 V1 BUILD SUCCESS"
