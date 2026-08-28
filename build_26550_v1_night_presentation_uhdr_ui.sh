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
  if p.is_file() and '.git' not in p.parts: d[p.relative_to(root).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
 return d
ma,mb=m(sys.argv[1]),m(sys.argv[2])
if ma!=mb:
 bad=[k for k in sorted(set(ma)|set(mb)) if ma.get(k)!=mb.get(k)]
 raise SystemExit('tree mismatch: '+repr(bad[:30]))
PY
}
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
REPO_BASE_HEAD="5f5f2db9fb7216d6a874a6de99bbf2f082bd2ab5"
BASE_SUCCESS_COMMIT="5f5f2db9fb7216d6a874a6de99bbf2f082bd2ab5"
BASE_RUN_ID="33121971246"
BASE_ARTIFACT_ID="9666910595"
BASE_ARTIFACT_NAME="photon-26549-v1-vgn-color-night-jpeg"
BASE_ARTIFACT_SHA="27de9bfbcf814ded3c9fd6363630772a05cbe33036e2c3b733220767c4e0e30e"
BASE_TAR_SHA="57f856bff387b43a5c3b7c2748554a58eb177fb11b319e6b133ca5f7c638d7bd"
BASE_MANIFEST_SHA="717f10740b832c9feee6854cb974ded8e181dd992ffe0ab5d8b9be5f55997374"
CAND_MANIFEST_SHA="adf297a9e6d54777ae4ccb2a36233e1b0faa2d50c983b5c889155866a904d3e3"
BASE_APK_SHA="4d9753180d60bcadde31e238b240b9dce08abee70ac64242f503b281180b0dea"
VERSION_NAME="0.9726550"
VERSION_BUILD="26550"
GLSLANG_PKG_VERSION="15.1.0-2~ubuntu0.24.04.2"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
BASE_PIN="$ROOT/V1_26550_BASE_26549_AUDITED_RUNTIME.sha256"
BASE_TAR_PIN="$ROOT/V1_26550_BASE_26549_CANDIDATE_TAR.sha256"
CAND_PIN="$ROOT/V1_26550_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256"
RUNTIME_LIST="$ROOT/V1_26550_RUNTIME_FILES.txt"
PREWRITE="$ROOT/V1_26550_PREWRITE_CHANGED_SOURCE_HASHES.sha256"
FORWARD="$ROOT/V1_26550_RUNTIME_DELTA_FROM_26549.patch"
ROLLBACK="$ROOT/V1_26550_RUNTIME_ROLLBACK_TO_26549.patch"
VALIDATE="$ROOT/validate_26550_v1_night_presentation_uhdr_ui.py"
HANDOFF_HASHES="$ROOT/V1_26550_HANDOFF_HASHES.sha256"
VENDOR_PIN="$ROOT/V1_26550_NATIVE_VENDOR_DEPENDENCIES.sha256"
OUT="$ROOT/build_26550_v1_night_presentation_uhdr_ui_outputs"
WORK="$ROOT/.build_26550_v1_night_presentation_uhdr_ui_work"
ARTZIP="$WORK/26549_artifact.zip"; ARTDIR="$WORK/26549_artifact"; BASE="$WORK/exact_26549_compiled_candidate"; AFTER="$WORK/candidate_26550"; PATCHREPO="$WORK/patchrepo"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-v1-night-presentation-uhdr-ui-debug.apk"
mapfile -t RUNTIME_FILES < "$RUNTIME_LIST"; [[ "${#RUNTIME_FILES[@]}" -eq 10 ]] || fail "runtime inventory is not 10 files"
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER"
cat > "$OUT/26550_V1_COMPILER_STATUS.txt" <<'EOF'
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF
cat > "$OUT/26550_V1_STRICT_HANDOFF_REPORT.txt" <<'EOF'
EXACT PRIOR RUNTIME AUTHORITY: NOT RUN
CHANGED RUNTIME SCOPE: NOT RUN
NIGHT 12+3 CAPTURE PRESERVATION: NOT RUN
NIGHT ADAPTIVE PRESENTATION: NOT RUN
NIGHT POST-JIN ULTRAHDR: NOT RUN
NIGHT BASE JPEG SURVIVAL: NOT RUN
NIGHT->MOTION UI REARM: NOT RUN
MOTION PRESENTATION INVARIANCE: NOT RUN
VGN 26549 INVARIANCE: NOT RUN
JIN AUTHORITY INVARIANCE: NOT RUN
REAL GLSL COMPILE: NOT RUN
REAL KOTLIN COMPILE: NOT RUN
REAL JAVA COMPILE: NOT RUN
FULL ANDROID ASSEMBLE: NOT RUN
FORWARD PATCH FUZZ=0: NOT RUN
ROLLBACK PATCH FUZZ=0: NOT RUN
POST-BUILD INVARIANCE: NOT RUN
CLEAN ARTIFACT SOURCE EXPORT: NOT RUN
BACKUP BRANCH: NOT REQUIRED (explicit user instruction; exact 26549 rollback patch authority)
TARGET VERSION/BUILD: 0.9726550 / 26550 V1
EOF
set_report(){ python3 - "$OUT/26550_V1_STRICT_HANDOFF_REPORT.txt" "$1" "$2" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); key=sys.argv[2]; val=sys.argv[3]; lines=p.read_text().splitlines(); found=False
for i,x in enumerate(lines):
 if x.startswith(key+':'): lines[i]=key+': '+val; found=True; break
if not found: raise SystemExit('missing report key '+key)
p.write_text('\n'.join(lines)+'\n')
PY
}
echo "=== 26550 GATE 0: sealed handoff / branch / exact package ==="
[[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
git merge-base --is-ancestor "$REPO_BASE_HEAD" HEAD || fail "handoff not descended from successful 26549 commit"
[[ -n "$TOKEN" ]] || fail "GitHub token unavailable"
sha256sum -c "$HANDOFF_HASHES"
python3 -m py_compile "$VALIDATE"; python3 "$VALIDATE" --self-test; bash -n "$0"
[[ "$(sha "$BASE_PIN")" == "$BASE_MANIFEST_SHA" ]] || fail "base manifest SHA drift"
[[ "$(wc -l < "$BASE_PIN")" -eq 969 ]] || fail "base manifest count"
[[ "$(sha "$CAND_PIN")" == "$CAND_MANIFEST_SHA" ]] || fail "candidate manifest SHA drift"
[[ "$(wc -l < "$CAND_PIN")" -eq 970 ]] || fail "candidate manifest count"
grep -F "$BASE_TAR_SHA" "$BASE_TAR_PIN" >/dev/null || fail "base TAR pin drift"
python3 - "$REPO_BASE_HEAD" <<'PY'
import subprocess,sys
base=sys.argv[1]
allowed={'.github/workflows/build-26550-v1-night-presentation-uhdr-ui.yml','V1_26550_BASE_26549_AUDITED_RUNTIME.sha256','V1_26550_BASE_26549_CANDIDATE_TAR.sha256','V1_26550_BASE_PROVENANCE.txt','V1_26550_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256','V1_26550_HANDOFF_HASHES.sha256','V1_26550_LOCAL_VALIDATION.txt','V1_26550_NATIVE_VENDOR_DEPENDENCIES.sha256','V1_26550_PREWRITE_CHANGED_SOURCE_HASHES.sha256','V1_26550_RUNTIME_DELTA_FROM_26549.patch','V1_26550_RUNTIME_FILES.txt','V1_26550_RUNTIME_ROLLBACK_TO_26549.patch','V1_26550_UPLOAD_INSTRUCTIONS.md','build_26550_v1_night_presentation_uhdr_ui.sh','validate_26550_v1_night_presentation_uhdr_ui.py'}
actual=set(subprocess.check_output(['git','diff','--name-only',base+'..HEAD'],text=True).splitlines())
if actual!=allowed: raise SystemExit('handoff scope mismatch extra=%r missing=%r'%(sorted(actual-allowed),sorted(allowed-actual)))
print('PASS: exactly 15-file 26550 handoff; repository app source untouched')
PY
! git diff --name-only "$REPO_BASE_HEAD..HEAD" | grep -E '^app/' >/dev/null || fail "handoff directly changed app source"
pass "sealed candidate-first handoff"

echo "=== 26550 GATE 1: recover exact successful compiled 26549 authority ==="
REPO_API="https://api.github.com/repos/${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}"
curl --fail --location --silent --show-error --retry 5 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "$REPO_API/actions/runs/${BASE_RUN_ID}" -o "$WORK/base_run.json"
python3 - "$WORK/base_run.json" "$BASE_RUN_ID" "$BASE_SUCCESS_COMMIT" "$EXPECTED_BRANCH" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); assert str(d.get('id'))==sys.argv[2]; assert d.get('conclusion')=='success'; assert d.get('head_sha')==sys.argv[3]; assert d.get('head_branch')==sys.argv[4]
print('PASS exact 26549 run success/commit/branch')
PY
curl --fail --location --silent --show-error --retry 5 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "$REPO_API/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"
[[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "26549 artifact ZIP SHA mismatch"
unzip -q "$ARTZIP" -d "$ARTDIR"
BASE_OUT="$ARTDIR/build_26549_v1_vgn_color_night_jpeg_outputs"; BASE_TAR="$BASE_OUT/26549_V1_candidate_app_source.tar.gz"; BASE_AUDITED="$BASE_OUT/26549_V1_candidate_source.sha256"; BASE_APK_HASH="$BASE_OUT/26549_V1_APK.sha256"; BASE_COMPILER="$BASE_OUT/26549_V1_COMPILER_STATUS.txt"; BASE_REPORT="$BASE_OUT/26549_V1_STRICT_HANDOFF_REPORT.txt"
for f in "$BASE_TAR" "$BASE_AUDITED" "$BASE_APK_HASH" "$BASE_COMPILER" "$BASE_REPORT"; do [[ -f "$f" ]] || fail "base artifact missing $f"; done
[[ "$(sha "$BASE_TAR")" == "$BASE_TAR_SHA" ]] || fail "base TAR SHA mismatch"; [[ "$(sha "$BASE_AUDITED")" == "$BASE_MANIFEST_SHA" ]] || fail "base audited manifest SHA mismatch"; cmp -s "$BASE_AUDITED" "$BASE_PIN" || fail "base manifest bytes differ"; grep -F "$BASE_APK_SHA" "$BASE_APK_HASH" >/dev/null || fail "base APK mismatch"
for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do grep -F "$proof" "$BASE_COMPILER" >/dev/null || fail "missing base compiler proof $proof"; done
for proof in 'VGN FULL ARTIFACT AUTHORITY: PASS' 'VGN TRUE-COLOR CONSERVATION: PASS' 'NIGHT EXPLICIT JPEG TARGET: PASS' 'POST-BUILD INVARIANCE: PASS' 'CLEAN ARTIFACT SOURCE EXPORT: PASS' 'TARGET VERSION/BUILD: 0.9726549 / 26549 V1'; do grep -F "$proof" "$BASE_REPORT" >/dev/null || fail "missing 26549 proof $proof"; done
tar -xzf "$BASE_TAR" -C "$BASE"; manifest_audited "$BASE" "$OUT/26550_base_reconstructed.sha256"; cmp -s "$OUT/26550_base_reconstructed.sha256" "$BASE_PIN" || fail "base reconstruction mismatch"; vendor_manifest "$BASE" "$OUT/26550_vendor_base.txt"; cmp -s "$OUT/26550_vendor_base.txt" "$VENDOR_PIN" || fail "base vendor mismatch"; (cd "$BASE" && sha256sum -c "$PREWRITE") > "$OUT/26550_prewrite_hashes_verified.txt"
set_report "EXACT PRIOR RUNTIME AUTHORITY" "PASS (run ${BASE_RUN_ID}, artifact ${BASE_ARTIFACT_ID}, compiled 26549)"; pass "exact compiled 26549 recovered"

echo "=== 26550 GATE 2: candidate-first 10-file transform ==="
cp -a "$BASE/." "$AFTER/"; (cd "$AFTER" && patch --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 < "$FORWARD" >/dev/null)
python3 "$VALIDATE" "$BASE" "$AFTER" | tee "$OUT/26550_runtime_contract.txt"; manifest_audited "$AFTER" "$OUT/26550_candidate_source.sha256"; cmp -s "$OUT/26550_candidate_source.sha256" "$CAND_PIN" || fail "candidate manifest mismatch"
python3 - "$BASE" "$AFTER" "$OUT/26550_actual_changed_files.txt" <<'PY'
from pathlib import Path
import hashlib,sys
def m(r):
 r=Path(r); return {p.relative_to(r).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in r.rglob('*') if p.is_file()}
b,c=m(sys.argv[1]),m(sys.argv[2]); ch=sorted(k for k in set(b)|set(c) if b.get(k)!=c.get(k)); Path(sys.argv[3]).write_text('\n'.join(ch)+'\n')
PY
cmp -s "$OUT/26550_actual_changed_files.txt" "$RUNTIME_LIST" || fail "runtime allowlist mismatch"
set_report "CHANGED RUNTIME SCOPE" "PASS (exact 10 files; one new Night-only helper)"; set_report "NIGHT 12+3 CAPTURE PRESERVATION" "PASS (ExposureSelector/CaptureController/Sabre bytes unchanged; -0.70 EV Short policy retained)"; set_report "NIGHT ADAPTIVE PRESENTATION" "PASS (post-color viewfinder solve; dark-scene strength + P99 headroom cap; capture untouched)"; set_report "NIGHT POST-JIN ULTRAHDR" "PASS (detached Sabre HDR relationship -> post-Jin SDR rebase -> JPEG_R)"; set_report "NIGHT BASE JPEG SURVIVAL" "PASS (plain checkpoint before Jin/UHDR; final packaging cannot destroy checkpoint)"; set_report "NIGHT->MOTION UI REARM" "PASS (frames release -> processing=false -> UI callback; first Motion ring explicitly rearmed)"; set_report "MOTION PRESENTATION INVARIANCE" "PASS (65% preference branch retained; full-res gain-map geometry identity)"; set_report "VGN 26549 INVARIANCE" "PASS (VGN processor byte-identical)"; set_report "JIN AUTHORITY INVARIANCE" "PASS (Jin byte-identical; exposure/HDR owned outside neural stage)"; pass "runtime semantics validated"

echo "=== 26550 GATE 3: deterministic full-index patches BEFORE live source write ==="
rm -rf "$PATCHREPO" "$WORK/forwardcheck" "$WORK/rollbackcheck"; mkdir -p "$PATCHREPO"; cp -a "$BASE/." "$PATCHREPO/"; (cd "$PATCHREPO"; git init -q; git config user.name Photon26550; git config user.email photon26550@example.invalid; git add -A; git commit -qm base; cp -a "$AFTER/." .; git add -A; for a in 7 12 40; do git -c core.abbrev=$a diff --cached --binary --full-index --no-ext-diff HEAD > "$WORK/f.$a"; cmp -s "$WORK/f.$a" "$FORWARD" || fail "forward patch nondeterministic $a"; done; git commit -qm candidate; find . -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +; cp -a "$BASE/." .; git add -A; for a in 7 12 40; do git -c core.abbrev=$a diff --cached --binary --full-index --no-ext-diff HEAD > "$WORK/r.$a"; cmp -s "$WORK/r.$a" "$ROLLBACK" || fail "rollback patch nondeterministic $a"; done)
mkdir -p "$WORK/forwardcheck" "$WORK/rollbackcheck"; cp -a "$BASE/." "$WORK/forwardcheck/"; (cd "$WORK/forwardcheck" && patch --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 < "$FORWARD" >/dev/null); exact_tree_equal "$WORK/forwardcheck" "$AFTER"; cp -a "$AFTER/." "$WORK/rollbackcheck/"; (cd "$WORK/rollbackcheck" && patch --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 < "$ROLLBACK" >/dev/null); exact_tree_equal "$WORK/rollbackcheck" "$BASE"; set_report "FORWARD PATCH FUZZ=0" "PASS (core.abbrev 7/12/40 byte-identical)"; set_report "ROLLBACK PATCH FUZZ=0" "PASS (core.abbrev 7/12/40 byte-identical)"; pass "patch determinism"

echo "=== 26550 GATE 4: install exact candidate into ephemeral checkout ==="
rsync -a --delete "$AFTER/app/" "$ROOT/app/"; manifest_audited "$ROOT" "$OUT/26550_installed_precompiler.sha256"; cmp -s "$OUT/26550_installed_precompiler.sha256" "$CAND_PIN" || fail "installed candidate mismatch"; vendor_manifest "$ROOT" "$OUT/26550_vendor_precompiler.txt"; cmp -s "$OUT/26550_vendor_precompiler.txt" "$VENDOR_PIN" || fail "vendor drift"; grep -Fx 'VERSION_NAME=0.9726550' app/version.properties >/dev/null; grep -Fx 'VERSION_BUILD=26550' app/version.properties >/dev/null; pass "version increment + candidate install same invocation"

echo "=== 26550 GATE 5: REAL pinned glslang for exact runtime-expanded modified shader ==="
sudo apt-get update -qq; apt-cache madison glslang-tools | grep -F "$GLSLANG_PKG_VERSION" >/dev/null || fail "pinned glslang unavailable"; sudo apt-get install -y --no-install-recommends "glslang-tools=${GLSLANG_PKG_VERSION}"; [[ "$(dpkg-query -W -f='${Version}' glslang-tools)" == "$GLSLANG_PKG_VERSION" ]] || fail "glslang version mismatch"
# Permanent 26550 V1.1 regression: Photon asset shaders are runtime-expanded by GLInterface.readProgram().
# IRIS_26550_GLSLANG_RUNTIME_PREPROCESS_PARITY
# Never compile this raw body directly; reproduce the exact #version/#line prefix the runtime supplies.
RUNTIME_GAINMAP_SHADER="$WORK/26550_gainmap_runtime_expanded.frag"
python3 - app/src/main/assets/shaders/motionv2/gainmap.glsl app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLProg.java app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLInterface.java "$RUNTIME_GAINMAP_SHADER" <<'PYGLSL'
from pathlib import Path
import sys
asset, glprog, glinterface, out = map(Path, sys.argv[1:])
src = asset.read_text()
gp = glprog.read_text()
gi = glinterface.read_text()
if 'public final static String glVersion = "#version 310 es\\n";' not in gp:
    raise SystemExit('FAIL: GLProg runtime GLSL version contract drifted')
if 'String addVersion = glVersion+"\\n"+"#line 1\\n";' not in gi:
    raise SystemExit('FAIL: GLInterface runtime shader-prefix contract drifted')
if '#version' in src:
    raise SystemExit('FAIL: gainmap.glsl unexpectedly became self-versioned; update compile parity gate')
if '#import' in src:
    raise SystemExit('FAIL: gainmap.glsl gained #import; exact runtime import expansion must be added to gate')
out.write_text('#version 310 es\n#line 1\n' + src)
print('PASS: exact Photon runtime #version/#line expansion generated for gainmap.glsl')
PYGLSL
head -n 2 "$RUNTIME_GAINMAP_SHADER" | diff -u <(printf '#version 310 es\n#line 1\n') - >/dev/null || fail "runtime-expanded gainmap prefix mismatch"
python3 - "$0" <<'PYRAW'
from pathlib import Path
import sys
text = Path(sys.argv[1]).read_text()
bad = 'glslangValidator -S frag ' + 'app/src/main/assets/shaders/motionv2/gainmap.glsl'
if any(line.strip().startswith(bad) for line in text.splitlines()):
    raise SystemExit('FAIL: permanent raw-asset glslang regression gate failed')
print('PASS: raw asset direct-compile regression excluded')
PYRAW
glslangValidator --version | tee "$OUT/26550_glslang_version.txt"
glslangValidator -S frag "$RUNTIME_GAINMAP_SHADER" | tee "$OUT/26550_glslang_compile.txt"
sed -i 's/REAL GLSL COMPILE: NOT RUN YET/REAL GLSL COMPILE: PASS (pinned glslangValidator 15.1.0-2~ubuntu0.24.04.2; exact Photon runtime-expanded gainmap.glsl)/' "$OUT/26550_V1_COMPILER_STATUS.txt"; set_report "REAL GLSL COMPILE" "PASS (pinned 15.1.0-2~ubuntu0.24.04.2; exact runtime-expanded gainmap.glsl)"; pass "real GLSL compiler on exact runtime-expanded source"

echo "=== 26550 GATE 6: REAL Kotlin + Java project compilers ==="
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace; sed -i 's/REAL KOTLIN COMPILE: NOT RUN YET/REAL KOTLIN COMPILE: PASS/' "$OUT/26550_V1_COMPILER_STATUS.txt"; sed -i 's/REAL JAVA COMPILE: NOT RUN YET/REAL JAVA COMPILE: PASS/' "$OUT/26550_V1_COMPILER_STATUS.txt"; set_report "REAL KOTLIN COMPILE" "PASS"; set_report "REAL JAVA COMPILE" "PASS"; grep -F 'java.nio.ByteBuffer source = plane.getBuffer().duplicate();' app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java >/dev/null || fail "permanent ByteBuffer javac regression"; python3 "$VALIDATE" "$BASE" "$AFTER" > "$OUT/26550_postcompiler_contract.txt"; pass "real language compilers"

echo "=== 26550 GATE 7: FULL Android assemble / exactly one APK ==="
./gradlew :app:assembleDebug --stacktrace; mapfile -t APKS < <(find app/build/outputs/apk/debug -maxdepth 1 -type f -name '*.apk' | LC_ALL=C sort); [[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one APK found ${#APKS[@]}"; cp "${APKS[0]}" "$FINAL"; [[ -s "$FINAL" ]] || fail "final APK empty"; sha256sum "$FINAL" > "$OUT/26550_V1_APK.sha256"; sed -i 's/FULL ANDROID ASSEMBLE: NOT RUN YET/FULL ANDROID ASSEMBLE: PASS/' "$OUT/26550_V1_COMPILER_STATUS.txt"; set_report "FULL ANDROID ASSEMBLE" "PASS"; pass "full assemble"

echo "=== 26550 GATE 8: post-build invariance / export exact authority ==="
manifest_audited "$ROOT" "$OUT/26550_postbuild_runtime.sha256"; cmp -s "$OUT/26550_postbuild_runtime.sha256" "$CAND_PIN" || fail "runtime changed during build"; manifest_audited "$AFTER" "$OUT/26550_frozen_candidate_postbuild.sha256"; cmp -s "$OUT/26550_frozen_candidate_postbuild.sha256" "$CAND_PIN" || fail "frozen candidate changed"; vendor_manifest "$ROOT" "$OUT/26550_vendor_postbuild.txt"; cmp -s "$OUT/26550_vendor_postbuild.txt" "$VENDOR_PIN" || fail "vendor changed"; python3 "$VALIDATE" "$BASE" "$AFTER" > "$OUT/26550_postbuild_contract.txt"; sed -i 's/POST-BUILD INVARIANCE: NOT RUN YET/POST-BUILD INVARIANCE: PASS/' "$OUT/26550_V1_COMPILER_STATUS.txt"; set_report "POST-BUILD INVARIANCE" "PASS"; tar -czf "$OUT/26550_V1_candidate_app_source.tar.gz" -C "$AFTER" app; sha256sum "$OUT/26550_V1_candidate_app_source.tar.gz" > "$OUT/26550_V1_candidate_app_source.tar.gz.sha256"; cp "$CAND_PIN" "$OUT/26550_V1_candidate_source.sha256"; cp "$RUNTIME_LIST" "$OUT/26550_V1_actual_runtime_scope.txt"; set_report "CLEAN ARTIFACT SOURCE EXPORT" "PASS"; cat >> "$OUT/26550_V1_STRICT_HANDOFF_REPORT.txt" <<EOF
FINAL APK: $(basename "$FINAL")
FINAL APK SHA-256: $(sha "$FINAL")
BASE RUN/ARTIFACT: ${BASE_RUN_ID} / ${BASE_ARTIFACT_ID}
BASE ARTIFACT SHA-256: ${BASE_ARTIFACT_SHA}
BASE CANDIDATE TAR SHA-256: ${BASE_TAR_SHA}
BASE AUDITED MANIFEST SHA-256: ${BASE_MANIFEST_SHA}
CANDIDATE AUDITED MANIFEST SHA-256: ${CAND_MANIFEST_SHA}
EOF
cat "$OUT/26550_V1_COMPILER_STATUS.txt"; cat "$OUT/26550_V1_STRICT_HANDOFF_REPORT.txt"; echo "PRE-BUILD SAFETY PROOF PASSED"; echo "26550 V1 BUILD SUCCESS"
