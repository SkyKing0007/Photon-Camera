#!/usr/bin/env bash
set -euo pipefail

SRC="/workspaces/Photon-Camera-fresh-iris"
OUT="$SRC/fresh_iris_outputs"
BRANCH="experimental-clean-photon-rebuild"
STAMP="$(date +%Y%m%d_%H%M%S)"
UHDR="app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java"
VERSION="app/version.properties"

fail() { echo "FAIL: $*" >&2; exit 1; }
sha() { sha256sum "$1" | awk '{print toupper($1)}'; }

cd "$SRC" || fail "Missing active Codespace"
mkdir -p "$OUT"

echo "======================================================================"
echo "26433 - 26432 ULTRA HDR JAVAC TYPE FIX ONLY"
echo "======================================================================"

echo "=== GATE 0: EXACT FAILED-26432 STATE ==="
[[ "$(git branch --show-current)" == "$BRANCH" ]] || fail "Wrong branch"
[[ -f local.properties ]] || fail "local.properties missing"
grep -q '^VERSION_NAME=0\.9726432$' "$VERSION" || fail "Expected failed 26432 VERSION_NAME"
grep -q '^VERSION_BUILD=26432$' "$VERSION" || fail "Expected failed 26432 VERSION_BUILD"

grep -q 'IRIS_26432_MOTION_V2_TRUE_ULTRAHDR' "$UHDR" || fail "26432 Ultra HDR helper missing"
grep -q 'catch (Throwable t)' "$UHDR" || fail "Expected exact 26432 javac defect not present"
grep -q 'Log.getStackTraceString(t)' "$UHDR" || fail "Expected failing call not present"

# Prove all intended 26432 architecture is currently present before fixing compilation.
grep -q 'IRIS_26432_STACK_SIZE_INVARIANT_REFERENCE_ROBUSTNESS' \
  app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl || fail "26432 merge robustness missing"
grep -q 'IRIS_26432_REFERENCE_SUPPORT_ANCHOR' \
  app/src/main/assets/shaders/motionv2/direct_rgb_init.glsl || fail "26432 reference anchor missing"
grep -q 'IRIS_26432_26431_TONE_PRESERVED_MINUS_032EV' \
  app/src/main/assets/shaders/motionv2/render.glsl || fail "26432 render missing"
grep -q 'IRIS_26432_TRUE_V2_EXTENDED_LINEAR_GAINMAP' \
  app/src/main/assets/shaders/motionv2/gainmap.glsl || fail "26432 gainmap shader missing"
grep -q 'IRIS_26432_TRUE_V2_ULTRAHDR_ATTACH' \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java || fail "26432 gainmap attach missing"

echo "PASS: failed 26432 source state proven"

echo "=== GATE 1: BACKUP BRANCH + PRE-EDIT PATCH ==="
SAFETY="$OUT/safety_26433_ultrahdr_javac_type_fix_$STAMP"
mkdir -p "$SAFETY/candidate"
BACKUP="backup/codespace-before-26433-ultrahdr-javac-type-fix-$STAMP"
git branch "$BACKUP"
git diff --binary HEAD -- app > "$SAFETY/pre_26433_working_tree.patch"

# Hash every tracked app file except the one Java source + version we intentionally change.
PROTECTED_BEFORE="$SAFETY/protected_before.txt"
PROTECTED_AFTER="$SAFETY/protected_after.txt"

hash_protected() {
  local out="$1"
  : > "$out"
  while IFS= read -r -d '' f; do
    [[ "$f" == "$UHDR" || "$f" == "$VERSION" ]] && continue
    printf '%s  %s\n' "$(sha "$f")" "$f" >> "$out"
  done < <(git ls-files -z app)
  sort -o "$out" "$out"
}
hash_protected "$PROTECTED_BEFORE"

echo "=== GATE 2: TEMPORARY-COPY FIX ==="
cp "$UHDR" "$SAFETY/candidate/MotionV2UltraHdr.java"
cp "$VERSION" "$SAFETY/candidate/version.properties"

python3 - "$SAFETY/candidate/MotionV2UltraHdr.java" "$SAFETY/candidate/version.properties" <<'PY'
from pathlib import Path
import sys

j=Path(sys.argv[1])
v=Path(sys.argv[2])

s=j.read_text()
old='catch (Throwable t)'
new='catch (Exception t)'
if s.count(old) != 1:
    raise SystemExit(f"FAIL: expected exactly one {old!r}, found {s.count(old)}")
s=s.replace(old,new,1)
j.write_text(s)

t=v.read_text()
if 'VERSION_NAME=0.9726432' not in t or 'VERSION_BUILD=26432' not in t:
    raise SystemExit("FAIL: candidate version baseline not 26432")
t=t.replace('VERSION_NAME=0.9726432','VERSION_NAME=0.9726433',1)
t=t.replace('VERSION_BUILD=26432','VERSION_BUILD=26433',1)
v.write_text(t)
PY

grep -q 'catch (Exception t)' "$SAFETY/candidate/MotionV2UltraHdr.java" || fail "Candidate Exception catch missing"
! grep -q 'catch (Throwable t)' "$SAFETY/candidate/MotionV2UltraHdr.java" || fail "Candidate still has Throwable catch"
grep -q 'Log.getStackTraceString(t)' "$SAFETY/candidate/MotionV2UltraHdr.java" || fail "Diagnostic stack trace call changed unexpectedly"
grep -q '^VERSION_NAME=0\.9726433$' "$SAFETY/candidate/version.properties" || fail "Candidate version name wrong"
grep -q '^VERSION_BUILD=26433$' "$SAFETY/candidate/version.properties" || fail "Candidate build wrong"

# Prove literally nothing else in the helper changed except Throwable -> Exception.
python3 - "$UHDR" "$SAFETY/candidate/MotionV2UltraHdr.java" <<'PY'
from pathlib import Path
import sys
a=Path(sys.argv[1]).read_text()
b=Path(sys.argv[2]).read_text()
expected=a.replace('catch (Throwable t)','catch (Exception t)',1)
if b != expected:
    raise SystemExit("FAIL: candidate contains changes beyond the javac type fix")
print("candidate/source validation PASS")
PY

echo "Temporary-copy validation: PASS"

echo "=== GATE 3: APPLY EXACT VALIDATED FIX ==="
cp "$SAFETY/candidate/MotionV2UltraHdr.java" "$UHDR"
cp "$SAFETY/candidate/version.properties" "$VERSION"

hash_protected "$PROTECTED_AFTER"
cmp -s "$PROTECTED_BEFORE" "$PROTECTED_AFTER" || fail "Protected app source changed"

# Re-prove critical 26432 IQ behavior after application.
grep -q 'IRIS_26432_STACK_SIZE_INVARIANT_REFERENCE_ROBUSTNESS' \
  app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl || fail "26432 robust merge changed"
grep -q 'IRIS_26432_26431_TONE_PRESERVED_MINUS_032EV' \
  app/src/main/assets/shaders/motionv2/render.glsl || fail "26432 tone changed"
grep -q 'IRIS_26432_TRUE_V2_EXTENDED_LINEAR_GAINMAP' \
  app/src/main/assets/shaders/motionv2/gainmap.glsl || fail "26432 gainmap changed"
grep -q 'OUTPUT_EXPOSURE_SCALE = 0.80f' \
  app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java || fail "26432 -0.32EV scale changed"
grep -q 'catch (Exception t)' "$UHDR" || fail "Applied compile fix missing"
grep -q '^VERSION_BUILD=26433$' "$VERSION" || fail "Applied version wrong"

git diff --check -- "$UHDR" "$VERSION"

echo "candidate/source validation PASS"
echo "Temporary-copy validation: PASS"
echo "PRE-BUILD SAFETY PROOF PASSED"

git diff --binary HEAD -- app > "$SAFETY/post_26433_working_tree.patch"

echo "=== GATE 4: JAVAC PROOF ==="
COMPILELOG="$OUT/26433_JAVAC_PROOF_$STAMP.txt"
set +e
./gradlew :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$COMPILELOG"
RC=${PIPESTATUS[0]}
set -e
[[ "$RC" -eq 0 ]] || fail "Javac still failed; see $COMPILELOG"
echo "JAVAC PROOF PASSED"

echo "=== GATE 5: FULL BUILD 0.9726433 / 26433 ==="
BUILDLOG="$OUT/build_26433_ultrahdr_javac_type_fix_$STAMP.txt"
set +e
./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$BUILDLOG"
RC=${PIPESTATUS[0]}
set -e
[[ "$RC" -eq 0 ]] || fail "Gradle failed rc=$RC; see $BUILDLOG"
grep -q 'BUILD SUCCESSFUL' "$BUILDLOG" || fail "BUILD SUCCESSFUL not found"

APK_SRC="$(find app/build/outputs/apk -type f -name '*.apk' -printf '%T@ %p\n' | sort -nr | head -1 | cut -d' ' -f2-)"
[[ -n "$APK_SRC" && -f "$APK_SRC" ]] || fail "Built APK not found"

APK="$SRC/IrisCamera-0.9726433-26433-v2-stack-robust-true-ultrahdr-javac-fix-debug.apk"
find "$SRC" -maxdepth 1 -type f -name 'IrisCamera-*.apk' -delete
mv -f "$APK_SRC" "$APK"
find app/build -type f -name '*.apk' -delete

RESULT="$OUT/26433_ULTRAHDR_JAVAC_FIX_RESULT_$STAMP.txt"
cat > "$RESULT" <<EOF
26433 ULTRA HDR JAVAC TYPE FIX
Timestamp: $(date --iso-8601=seconds)
Version/build: 0.9726433 / 26433

ONLY CODE FIX:
- MotionV2UltraHdr catch type changed from Throwable to Exception because this
  Photon Log.getStackTraceString API accepts Exception.
- No image-processing algorithm changed from failed 26432.

PRESERVED:
- 26432 stack-size-invariant reference robustness
- all requested Motion frames remain eligible
- 26431 color behavior
- 26431 tone shape
- shared 0.80 linear output scale (~-0.322 EV)
- V2 extended-linear Ultra HDR gain-map design
- midtone/body gain unity
- 26429 shared-guide/reference geometry architecture

SAFETY:
- Backup branch: $BACKUP
- Pre-edit patch: $SAFETY/pre_26433_working_tree.patch
- Post-edit patch: $SAFETY/post_26433_working_tree.patch
- candidate/source validation PASS
- Temporary-copy validation: PASS
- PRE-BUILD SAFETY PROOF PASSED
- JAVAC PROOF PASSED
- BUILD SUCCESSFUL verified

APK: $APK
Javac log: $COMPILELOG
Build log: $BUILDLOG

No commit.
No push.
dev untouched.
EOF

echo "======================================================================"
echo "26433 BUILD SUCCESSFUL"
echo "APK: $APK"
echo "RESULT: $RESULT"
echo "Exactly one APK. No commit. No push. dev untouched."
echo "======================================================================"
