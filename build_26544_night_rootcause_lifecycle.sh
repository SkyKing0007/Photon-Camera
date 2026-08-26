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

ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
BASE_26543_HEAD="7c6fa593abf9c50464e6093a1af75e92c2685705"
BASE_RUN_ID="32927284550"
BASE_ARTIFACT_ID="9592028495"
BASE_ARTIFACT_NAME="photon-26543-owner-memory-figure7"
BASE_ARTIFACT_SHA="8116403e8a7f21672e194294e359c5b289d424ef6bf47cbc06ebbbb6dbc4437b"
BASE_TAR_SHA="18e380899a2d1817ccdcc840f30ba69290b3a1c6541d9083796062f22d229c48"
BASE_MANIFEST_SHA="9ac60d97d8ccad91a4957ac23e1bd728166ededcfde622848ed1d09b2f82a8fb"
VERSION_NAME="0.9726544"
VERSION_BUILD="26544"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"

BASE_PIN="$ROOT/26544_BASE_26543_CANDIDATE_SOURCE.sha256"
BASE_TAR_PIN="$ROOT/26544_BASE_26543_CANDIDATE_TAR.sha256"
RUNTIME_LIST="$ROOT/26544_RUNTIME_FILES.txt"
FORWARD="$ROOT/26544_RUNTIME_DELTA_FROM_26543.patch"
ROLLBACK="$ROOT/26544_RUNTIME_ROLLBACK_TO_26543.patch"
VALIDATE="$ROOT/validate_26544_night_rootcause_lifecycle.py"
HANDOFF_HASHES="$ROOT/26544_HANDOFF_HASHES.sha256"
OLD_GLSL_PREFLIGHT="$ROOT/preflight_26543_changed_syntax.py"
OUT="$ROOT/build_26544_night_rootcause_lifecycle_outputs"
WORK="$ROOT/.build_26544_night_rootcause_lifecycle_work"
ARTZIP="$WORK/26543_artifact.zip"
ARTDIR="$WORK/26543_artifact"
BASE="$WORK/exact_tested_26543"
AFTER="$WORK/candidate_26544"
PATCHREPO="$WORK/patchrepo"
FORWARDCHECK="$WORK/forwardcheck"
ROLLBACKCHECK="$WORK/rollbackcheck"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-night-rootcause-lifecycle-debug.apk"

mapfile -t RUNTIME_FILES < "$RUNTIME_LIST"
[[ "${#RUNTIME_FILES[@]}" -eq 6 ]] || fail "runtime file inventory is not exactly six"

rm -rf "$OUT" "$WORK"
rm -f "$FINAL"
mkdir -p "$OUT" "$WORK" "$ARTDIR"

cat > "$OUT/26544_COMPILER_STATUS.txt" <<'EOF'
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
EOF

echo "=== 26544 GATE 0: exact branch / lineage / handoff integrity ==="
[[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch: $(git branch --show-current)"
git merge-base --is-ancestor "$BASE_26543_HEAD" HEAD || fail "handoff is not descended from exact tested 26543 V1.4"
[[ -n "$TOKEN" ]] || fail "GitHub token unavailable for exact successful 26543 artifact"
for f in "$BASE_PIN" "$BASE_TAR_PIN" "$RUNTIME_LIST" "$FORWARD" "$ROLLBACK" "$VALIDATE" "$HANDOFF_HASHES" "$OLD_GLSL_PREFLIGHT"; do
  [[ -f "$f" ]] || fail "required file missing: $f"
done
sha256sum -c "$HANDOFF_HASHES"
[[ "$(sha "$BASE_PIN")" == "$BASE_MANIFEST_SHA" ]] || fail "base manifest pin SHA drift"
[[ "$(wc -l < "$BASE_PIN")" -eq 967 ]] || fail "base manifest pin is not 967 files"
grep -Fx "$BASE_TAR_SHA  26543_candidate_app_source.tar.gz" "$BASE_TAR_PIN" >/dev/null || fail "base tar pin drift"

python3 - "$BASE_26543_HEAD" <<'PY'
import subprocess,sys
base=sys.argv[1]
allowed={
'.github/workflows/build-26544-night-rootcause-lifecycle.yml',
'26544_BASE_26543_CANDIDATE_SOURCE.sha256',
'26544_BASE_26543_CANDIDATE_TAR.sha256',
'26544_BASE_PROVENANCE.txt',
'26544_HANDOFF_HASHES.sha256',
'26544_LOCAL_VALIDATION.txt',
'26544_RUNTIME_DELTA_FROM_26543.patch',
'26544_RUNTIME_FILES.txt',
'26544_RUNTIME_ROLLBACK_TO_26543.patch',
'26544_UPLOAD_INSTRUCTIONS.md',
'build_26544_night_rootcause_lifecycle.sh',
'validate_26544_night_rootcause_lifecycle.py',
}
actual=set(subprocess.check_output(['git','diff','--name-only',base+'..HEAD'],text=True).splitlines())
extra=sorted(actual-allowed)
missing=sorted(allowed-actual)
if extra: raise SystemExit('FAIL: handoff commit changed forbidden repo files: '+repr(extra))
if missing: raise SystemExit('FAIL: handoff commit is incomplete: '+repr(missing))
print('PASS: repository commit contains only the exact 12-file 26544 handoff; no app/src hand edit')
PY
pass "handoff integrity + repository source isolation"

echo "=== 26544 GATE 1: download exact successful user-tested 26543 V1.4 artifact ==="
URL="https://api.github.com/repos/${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}/actions/artifacts/${BASE_ARTIFACT_ID}/zip"
curl --fail --location --silent --show-error --retry 5 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "$URL" -o "$ARTZIP"
[[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "26543 artifact ZIP SHA mismatch"
unzip -q "$ARTZIP" -d "$ARTDIR"
BASE_OUT="$ARTDIR/build_26543_owner_memory_figure7_outputs"
BASE_TAR="$BASE_OUT/26543_candidate_app_source.tar.gz"
BASE_MANIFEST="$BASE_OUT/26543_candidate_source.sha256"
[[ -f "$BASE_TAR" && -f "$BASE_MANIFEST" ]] || fail "26543 artifact lacks authoritative candidate source"
[[ "$(sha "$BASE_TAR")" == "$BASE_TAR_SHA" ]] || fail "26543 candidate TAR SHA mismatch"
[[ "$(sha "$BASE_MANIFEST")" == "$BASE_MANIFEST_SHA" ]] || fail "26543 candidate manifest file SHA mismatch"
cmp -s "$BASE_MANIFEST" "$BASE_PIN" || fail "artifact manifest is not the exact user-tested 26543 pin"
mkdir -p "$BASE"
tar -xzf "$BASE_TAR" -C "$BASE"
(cd "$BASE" && sha256sum -c "$BASE_PIN" >/dev/null)
manifest_all "$BASE" "$OUT/26543_base_reverified.sha256"
cmp -s "$OUT/26543_base_reverified.sha256" "$BASE_PIN" || fail "clean-extracted 26543 is not exact 967-file authority"
pass "artifact id=$BASE_ARTIFACT_ID run=$BASE_RUN_ID exact ZIP/TAR/967-file source authority"

echo "=== 26544 GATE 2: candidate-first exact transform ==="
mkdir -p "$AFTER"
cp -a "$BASE/." "$AFTER/"
(
  cd "$AFTER"
  patch --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 < "$FORWARD" >/dev/null
)
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" | tee "$OUT/26544_prebuild_contract.txt"
manifest_all "$AFTER" "$OUT/26544_candidate_source.sha256"
[[ "$(wc -l < "$OUT/26544_candidate_source.sha256")" -eq 967 ]] || fail "candidate manifest is not 967 files"
ACTUAL_CHANGED="$OUT/26544_actual_changed_files.txt"
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
mb,mc=m(b),m(c)
changed=sorted(k for k in set(mb)|set(mc) if mb.get(k)!=mc.get(k))
o.write_text('\n'.join(changed)+'\n')
PY
cmp -s "$ACTUAL_CHANGED" "$RUNTIME_LIST" || fail "actual runtime changed scope differs from six-file allowlist"
pass "candidate-first transform exact six-file scope"

echo "=== 26544 GATE 3: inherited real GLSL regression proof ==="
GLSLANG="$(command -v glslangValidator || true)"
[[ -n "$GLSLANG" ]] || fail "pinned glslangValidator not on PATH"
"$GLSLANG" --version | grep -F '16.5.0' >/dev/null || fail "wrong glslangValidator version"
python3 "$OLD_GLSL_PREFLIGHT" --root "$AFTER" --validator "$GLSLANG" \
  | tee "$OUT/26544_real_glslang_regression.txt"
# No GLSL/Kotlin source changed; exact full-manifest comparison proves shader bytes inherited from tested 26543.
! grep -E '\.(glsl|kt)$' "$ACTUAL_CHANGED" >/dev/null || fail "unexpected GLSL/Kotlin source change"
sed -i 's/^REAL GLSL COMPILE:.*/REAL GLSL COMPILE: PASS (glslangValidator 16.5.0; active embedded Figure-7 shaders recompiled)/' "$OUT/26544_COMPILER_STATUS.txt"
pass "REAL GLSL COMPILE"

echo "=== 26544 GATE 4: canonical deterministic forward/rollback proof ==="
mkdir -p "$PATCHREPO"
cp -a "$BASE/." "$PATCHREPO/"
(
 cd "$PATCHREPO"
 git init -q
 git config user.email photon-local@example.invalid
 git config user.name Photon26544
 git add -A && git commit -qm exact-26543
 BASE_COMMIT="$(git rev-parse HEAD)"
 cp -a "$AFTER/app/src/main/." app/src/main/
 cp "$AFTER/app/version.properties" app/version.properties
 cp "$AFTER/app/build.gradle" app/build.gradle
 git add -A && git commit -qm candidate-26544
 CAND_COMMIT="$(git rev-parse HEAD)"
 for abbrev in 7 12 40; do
   git -c core.abbrev="$abbrev" diff --binary --full-index --no-ext-diff "$BASE_COMMIT" "$CAND_COMMIT" -- "${RUNTIME_FILES[@]}" > "$WORK/forward.$abbrev.patch"
   git -c core.abbrev="$abbrev" diff --binary --full-index --no-ext-diff "$CAND_COMMIT" "$BASE_COMMIT" -- "${RUNTIME_FILES[@]}" > "$WORK/rollback.$abbrev.patch"
   cmp -s "$WORK/forward.$abbrev.patch" "$FORWARD" || fail "forward patch differs at core.abbrev=$abbrev"
   cmp -s "$WORK/rollback.$abbrev.patch" "$ROLLBACK" || fail "rollback patch differs at core.abbrev=$abbrev"
 done
)
cp -a "$BASE" "$FORWARDCHECK"
(cd "$FORWARDCHECK" && patch --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 < "$FORWARD" >/dev/null)
manifest_all "$FORWARDCHECK" "$OUT/26544_forwardcheck.sha256"
cmp -s "$OUT/26544_forwardcheck.sha256" "$OUT/26544_candidate_source.sha256" || fail "fuzz=0 forward is not exact candidate"
cp -a "$AFTER" "$ROLLBACKCHECK"
(cd "$ROLLBACKCHECK" && patch --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 < "$ROLLBACK" >/dev/null)
manifest_all "$ROLLBACKCHECK" "$OUT/26544_rollbackcheck.sha256"
cmp -s "$OUT/26544_rollbackcheck.sha256" "$BASE_PIN" || fail "fuzz=0 rollback is not exact 26543"
pass "canonical full-index patch deterministic at abbrev 7/12/40 + forward/rollback fuzz=0 exact"

echo "=== 26544 GATE 5: install exact audited candidate into ephemeral Actions runtime ==="
rm -rf "$ROOT/app/src/main"
mkdir -p "$ROOT/app/src"
cp -a "$AFTER/app/src/main" "$ROOT/app/src/"
cp "$AFTER/app/version.properties" "$ROOT/app/version.properties"
cp "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"
manifest_all "$ROOT" "$OUT/26544_installed_pre_gradle.sha256"
cmp -s "$OUT/26544_installed_pre_gradle.sha256" "$OUT/26544_candidate_source.sha256" || fail "installed runtime differs from audited candidate"
grep -Fx "VERSION_NAME=$VERSION_NAME" "$ROOT/app/version.properties" >/dev/null || fail "version name not exact"
grep -Fx "VERSION_BUILD=$VERSION_BUILD" "$ROOT/app/version.properties" >/dev/null || fail "version build not exact"
python3 "$VALIDATE" --base "$BASE" --candidate "$ROOT" > "$OUT/26544_installed_pre_gradle_contract.txt"
echo "PRE-BUILD SAFETY PROOF PASSED"
pass "version increment + exact runtime installation are in this same authoritative build invocation"

echo "=== 26544 GATE 6: REAL PROJECT COMPILERS ==="
chmod +x "$ROOT/gradlew"
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace
sed -i 's/^REAL KOTLIN COMPILE:.*/REAL KOTLIN COMPILE: PASS (:app:compileDebugKotlin)/' "$OUT/26544_COMPILER_STATUS.txt"
sed -i 's/^REAL JAVA COMPILE:.*/REAL JAVA COMPILE: PASS (:app:compileDebugJavaWithJavac)/' "$OUT/26544_COMPILER_STATUS.txt"
pass "REAL KOTLIN COMPILE"
pass "REAL JAVA COMPILE"

echo "=== 26544 GATE 7: FULL ANDROID ASSEMBLE ==="
./gradlew :app:assembleDebug --stacktrace
sed -i 's/^FULL ANDROID ASSEMBLE:.*/FULL ANDROID ASSEMBLE: PASS (:app:assembleDebug)/' "$OUT/26544_COMPILER_STATUS.txt"
pass "FULL ANDROID ASSEMBLE"

echo "=== 26544 GATE 8: post-compiler source invariance + one APK ==="
manifest_all "$ROOT" "$OUT/26544_post_gradle_runtime.sha256"
cmp -s "$OUT/26544_post_gradle_runtime.sha256" "$OUT/26544_candidate_source.sha256" || fail "Gradle changed audited runtime source"
python3 "$VALIDATE" --base "$BASE" --candidate "$ROOT" > "$OUT/26544_postbuild_contract.txt"
mapfile -t APKS < <(find "$ROOT/app/build/outputs/apk/debug" -maxdepth 1 -type f -name '*.apk' -print | sort)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one Gradle APK, got ${#APKS[@]}"
cp "${APKS[0]}" "$FINAL"
sha256sum "$FINAL" | tee "$OUT/26544_APK.sha256"
cat > "$OUT/26544_SCOPE_PROVENANCE.txt" <<EOF
Target: $VERSION_NAME / $VERSION_BUILD
Exact base GitHub commit: $BASE_26543_HEAD
Exact successful run: $BASE_RUN_ID
Exact artifact ID: $BASE_ARTIFACT_ID
Exact artifact ZIP SHA256: $BASE_ARTIFACT_SHA
Exact 26543 candidate TAR SHA256: $BASE_TAR_SHA
Exact 26543 manifest SHA256: $BASE_MANIFEST_SHA
Runtime changed files: 6
No GLSL or Kotlin changed.
Iris Night capture/exposure/MGC/post/Jin ownership preserved.
26543 async live-Camera2-Image spool removed.
Cold process start forces Motion before Settings construction.
Process-death evidence: fsync lifecycle + ApplicationExitInfo + process-state summary.
EOF
tar -czf "$OUT/26544_candidate_app_source.tar.gz" -C "$ROOT" app/src/main app/version.properties app/build.gradle
sha256sum "$OUT/26544_candidate_app_source.tar.gz" > "$OUT/26544_candidate_app_source.tar.gz.sha256"
cat "$OUT/26544_COMPILER_STATUS.txt"
echo "PASS: 26544 exact artifact authority"
echo "PASS: 26544 runtime ownership + deterministic rollback"
echo "PASS: 26544 REAL GLSL/KOTLIN/JAVA + FULL ANDROID ASSEMBLE"
echo "APK: $FINAL"
