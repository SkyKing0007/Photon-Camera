#!/usr/bin/env bash
set -euo pipefail

fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
hash_eq(){ local f="$1" e="$2"; [[ -f "$f" ]] || fail "missing protected file $f"; [[ "$(sha "$f")" == "$e" ]] || fail "protected hash mismatch $f"; }

EXPECTED_BRANCH="experimental-clean-photon-rebuild"
EXPECTED_SUCCESS_26496="6ac07643aa31605ba364a3f5ff3e3a5bda901872"
EXPECTED_APP_BASE="8233415edf738bf35c0fe1c4907f5dfe51de31a4"
BACKUP_BRANCH="backup-26496-success-before-26497-root-highlight-uhdr"
BASELINE_BUNDLE="26496_successful_app_source.tar.gz"
BASELINE_BUNDLE_SHA="2ef616843f6559dca3406d87470c4502a5d18414f79c3da71cd86f179a863d65"
BASELINE_MANIFEST="26496_successful_after.sha256"
BASELINE_MANIFEST_SHA="cc0371d11a4896aba2190c5558ad038c4408fe175e86f5bc77f324bc3d274ec7"
PATCH="26497_source_delta_from_exact_26496.patch"
PATCH_SHA="307502b7d444371228c86eac48674413b66573f5a99939582660970a644b2060"
VALIDATOR="validate_26497_root_highlight_uhdr.py"
VALIDATOR_SHA="58fcaff99ad4cbde4c4891226f328cde839ee7251e814ae94f60fb691d9f9734"
OLD_VERSION="0.9726496"
OLD_BUILD="26496"
NEW_VERSION="0.9726497"
NEW_BUILD="26497"
APK_NAME="IrisCamera-${NEW_VERSION}-${NEW_BUILD}-root-highlight-uhdr-debug.apk"

REPO="$(pwd)"
OUTDIR="$REPO/build_26497_outputs"
TMP="${RUNNER_TEMP:-/tmp}/photon_26497_$$"
BASE="$TMP/base26496"
CAND="$TMP/candidate26497"
PREPATCH="$OUTDIR/26497_pre_edit_exact_26496_complete_binary.patch"
DELTA="$OUTDIR/26497_delta_from_exact_26496.patch"
AFTERHASH="$OUTDIR/26497_successful_after.sha256"
NEXTBUNDLE="$OUTDIR/26497_successful_app_source.tar.gz"
BUILDLOG="$OUTDIR/26497_build.log"
SHADERLOG="$OUTDIR/26497_shader_validation.txt"
REPORT="$OUTDIR/26497_build_report.txt"

rm -rf "$OUTDIR" "$TMP"
mkdir -p "$OUTDIR" "$TMP"
cleanup(){
  set +e
  git worktree remove --force "$BASE" >/dev/null 2>&1 || true
  git worktree remove --force "$CAND" >/dev/null 2>&1 || true
  rm -rf "$TMP"
}
trap cleanup EXIT

echo "=== 26497 ROOT HIGHLIGHT CORRESPONDENCE + COHERENT CHROMA + SINGLE RCD BORDER + SHARP UHDR ==="
date -Iseconds || true

# Gate 0: exact infrastructure lineage and user-created safety checkpoint.
BRANCH="${GITHUB_REF_NAME:-$(git branch --show-current)}"
[[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || fail "wrong branch=$BRANCH expected=$EXPECTED_BRANCH"
[[ "$BRANCH" != "dev" ]] || fail "dev is protected"
git cat-file -e "$EXPECTED_SUCCESS_26496^{commit}" || fail "successful 26496 checkpoint unavailable"
git cat-file -e "$EXPECTED_APP_BASE^{commit}" || fail "protected app base unavailable"
git merge-base --is-ancestor "$EXPECTED_SUCCESS_26496" HEAD || fail "HEAD does not descend from successful 26496"
git diff --quiet "$EXPECTED_APP_BASE" -- app/src/main app/version.properties   || fail "committed app source changed; infrastructure-only workflow contract violated"
backup="$(git ls-remote origin "refs/heads/$BACKUP_BRANCH" | awk '{print $1}')"
[[ "$backup" == "$EXPECTED_SUCCESS_26496" ]]   || fail "required pre-26497 backup missing/moved: $BACKUP_BRANCH=$backup expected=$EXPECTED_SUCCESS_26496"
pass "successful 26496 lineage + protected app tree + exact pre-26497 backup"

# Gate 1: immutable package identities and deterministic architecture/math tests.
[[ -f "$BASELINE_BUNDLE" && "$(sha "$BASELINE_BUNDLE")" == "$BASELINE_BUNDLE_SHA" ]] || fail "26496 source bundle identity mismatch"
[[ -f "$BASELINE_MANIFEST" && "$(sha "$BASELINE_MANIFEST")" == "$BASELINE_MANIFEST_SHA" ]] || fail "26496 manifest identity mismatch"
[[ -f "$PATCH" && "$(sha "$PATCH")" == "$PATCH_SHA" ]] || fail "26497 source patch identity mismatch"
[[ -f "$VALIDATOR" && "$(sha "$VALIDATOR")" == "$VALIDATOR_SHA" ]] || fail "26497 validator identity mismatch"
python3 -m py_compile "$VALIDATOR" || fail "26497 validator Python syntax"
python3 "$VALIDATOR" || fail "26497 math/architecture self-test"
bash -n "$0" || fail "build script shell syntax"
[[ "$(wc -l < "$BASELINE_MANIFEST")" -eq 857 ]] || fail "26496 manifest count must be 857"
pass "package identities + 26497 root-correction self-tests"

reconstruct_exact_26496(){
  local d="$1"
  git worktree add --detach "$d" "$EXPECTED_APP_BASE" >/dev/null
  rm -rf "$d/app/src/main"
  rm -f "$d/app/version.properties"
  ( cd "$d" && tar -xzf "$REPO/$BASELINE_BUNDLE" ) || fail "extract exact 26496 source bundle"
  python3 - "$d" "$REPO/$BASELINE_MANIFEST" <<'PY_VERIFY'
from pathlib import Path
import hashlib,sys
root=Path(sys.argv[1]); manifest=Path(sys.argv[2])
expected={}
for line in manifest.read_text().splitlines():
    if line.strip():
        h,rel=line.split(None,1); expected[rel.strip()]=h
actual=sorted([str(p.relative_to(root)) for p in (root/'app/src/main').rglob('*') if p.is_file()] + ['app/version.properties'])
if len(expected)!=857: raise SystemExit(f'expected manifest count={len(expected)} !=857')
if actual!=sorted(expected): raise SystemExit('26496 canonical file-set mismatch')
for rel,h in expected.items():
    got=hashlib.sha256((root/rel).read_bytes()).hexdigest()
    if got!=h: raise SystemExit(f'26496 canonical hash mismatch {rel}: {got} != {h}')
ver=(root/'app/version.properties').read_text()
if 'VERSION_NAME=0.9726496' not in ver or 'VERSION_BUILD=26496' not in ver:
    raise SystemExit('exact 26496 version proof failed')
print('PASS: exact successful 26496 source verified 857/857')
PY_VERIFY
}

# Gate 2: two independent exact 26496 copies and mandatory pre-edit binary patch.
reconstruct_exact_26496 "$BASE"
reconstruct_exact_26496 "$CAND"
pass "two independent exact 26496 source copies reconstructed"
(
  cd "$BASE"
  git add -N app/src/main app/version.properties >/dev/null 2>&1 || true
  git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties
) > "$PREPATCH"
[[ -s "$PREPATCH" ]] || fail "pre-edit exact-26496 binary patch empty"
sha256sum "$PREPATCH" > "$PREPATCH.sha256"
pass "binary pre-edit exact-26496 patch created before modification"

# Gate 3: one immutable 26497 patch; exact six-file application scope.
git -C "$CAND" apply --check "$REPO/$PATCH" || fail "26497 source patch preflight"
git -C "$CAND" apply "$REPO/$PATCH" || fail "26497 source patch application"
python3 - "$BASE" "$CAND" <<'PY_SCOPE'
from pathlib import Path
import hashlib,sys
base=Path(sys.argv[1]); cand=Path(sys.argv[2])
modified={
'app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl',
'app/src/main/assets/shaders/motionv2/rcd26496_chroma_complete.glsl',
'app/src/main/assets/shaders/motionv2/rcd26489_write.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2RcdDemosaic.java',
}
def files(root):
    out={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
         for p in (root/'app/src/main').rglob('*') if p.is_file()}
    out['app/version.properties']=hashlib.sha256((root/'app/version.properties').read_bytes()).hexdigest()
    return out
a,b=files(base),files(cand)
if set(a)!=set(b): raise SystemExit('26497 must not add/remove canonical files')
changed={r for r in a if a[r]!=b[r]}
if changed!=modified: raise SystemExit('26497 modified-file scope mismatch: '+repr(sorted(changed)))
if len(a)!=857 or len(b)!=857: raise SystemExit(f'canonical counts base={len(a)} cand={len(b)} expected 857')
if a['app/version.properties']!=b['app/version.properties']:
    raise SystemExit('version changed before pre-build safety gates')
print('PASS: exact pre-version scope = 6 modified files; 851 canonical files byte-identical')
PY_SCOPE
DIFFCHECK="$TMP/26496_to_26497_diff_check.txt"
set +e
git diff --no-index --check -- "$BASE/app/src/main" "$CAND/app/src/main" > "$DIFFCHECK" 2>&1
diffcheck_rc=$?
set -e
[[ "$diffcheck_rc" -le 1 ]] || { cat "$DIFFCHECK"; fail "26497 delta whitespace check execution"; }
[[ ! -s "$DIFFCHECK" ]] || { cat "$DIFFCHECK"; fail "26497 introduced whitespace error"; }
pass "temporary-copy patch + exact scope + delta-only whitespace validation"

# Gate 4: protect the normal Motion/Wronski/capture/tone path byte-for-byte.
M="$CAND/app/src/main"
S="$M/assets/shaders/motionv2"
RECON="$M/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"
RCDHOST="$M/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2RcdDemosaic.java"
SHORT="$S/short_highlight_bayer_recover.glsl"
CHROMA="$S/rcd26496_chroma_complete.glsl"
WRITE="$S/rcd26489_write.glsl"
GAIN="$S/gainmap.glsl"

hash_eq "$S/mfsr_bayer_accumulate.glsl" "40af5a9c0bf3e43ecb5c860b8e0e53c42aaadae3c96c04da7e151aa37dd1ed2b"
hash_eq "$S/mfsr_bayer_normalize.glsl" "1a9fbdcc5472d3bfb49ca8732023c4f50c81fe6a45ec1b6e00824d6fdbf5cc54"
hash_eq "$S/render.glsl" "2a3aa0c6e3cc553e11d4feeb6ecf24768f14e423ce359a3248b9f70dda7a8dbf"
hash_eq "$M/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java" "a542aeae6b484b12fdb89ef97b3a74f694da121707f2d3163b138b34d867b625"
hash_eq "$M/java/com/particlesdevs/photoncamera/capture/CaptureController.java" "b318e84dd5670a01d80597e021663d17df92a4f43c09e57a9e652dc63d9137ab"
hash_eq "$M/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java" "d462f0e2394e5693c1c3847a8202d0d47c16934d6a657c3ff81727820d6f1c37"
for spec in   rcd26489_populate.glsl:769fbe0f2cbf226adaf1b66129f7f45833deaa2c05f6e063c691dc75dfe30b04   rcd26489_vh_direction.glsl:66831dfd1a39a4b5866631f1058a2883dd237961f33cc4c0bd169a7e02a0873e   rcd26489_lpf.glsl:95dff8fa0f3c4420de8e13346b766c7a2a80f76b08634b3b8135f775cac06a0c   rcd26489_green.glsl:4f268056ae8d8f1da8ae5b3936768cbb7d3841f9ac4e4b54ac6f113ca6a55040   rcd26489_diag_residual.glsl:47e7041976905fb76a54acb36e19d30d4d29d8e4dd9d25012f0515978170a2e3   rcd26489_diag_direction.glsl:1bd8f80b12e06f5ab8c19bb65d27e60f31998327557df0e6f551c682bdfc2b0e   rcd26489_opposite.glsl:30e732e00e50aeca0d29d08529230c3d043b81e8df87b0c4504768e89fe80392   rcd26489_green_rb.glsl:b0476f9e5a7b130d7c3edc58b7ba4a033edc5fa2c55605fd446feea8e1b3e4ca; do
  f="${spec%%:*}"; h="${spec##*:}"; hash_eq "$S/$f" "$h"
done

grep -q 'IRIS_26497_SHORT_CORRESPONDENCE_REFINEMENT' "$SHORT" || fail "26497 short refinement marker missing"
grep -q 'float flowConfidence = exp(-80.0 \* variation);' "$SHORT" || fail "interpolation-cancel semantic fix missing"
! grep -q 'cancelled=step\|cancelled = step' "$SHORT" || fail "old interpolation-cancel hard rejection survived"
grep -q 'refineObservableCorrespondence' "$SHORT" || fail "local short correspondence refinement missing"
grep -q 'IRIS_26497_COHERENT_MULTI_DIRECTION_CHROMA' "$CHROMA" || fail "coherent chroma marker missing"
grep -q 'sectors < 2' "$CHROMA" || fail "multi-direction chroma requirement missing"
grep -q 'IRIS_26497_SINGLE_RCD_BORDER_AUTHORITY' "$WRITE" || fail "single RCD border marker missing"
! grep -q 'ppg(' "$WRITE" || fail "PPG border reconstruction survived"
! grep -q 'boundary=' "$WRITE" || fail "hard RCD/PPG border switch survived"
grep -q 'IRIS_26497_NONOVERLAP_LOG_GAIN_FOOTPRINT' "$GAIN" || fail "26497 UHDR ownership marker missing"
grep -q 'const int DOWNSAMPLE = 4;' "$GAIN" || fail "UHDR quarter-resolution ownership changed"
! grep -q 'FILTER_TAPS\|FILTER_START\|KERNEL\[' "$GAIN" || fail "26496 broad UHDR filter survived"
! grep -Eqi 'short[[:space:]_-]*b([^a-zA-Z]|$)|SHORT_B' "$SHORT" "$RECON" || fail "unexpected Short B architecture introduced"
grep -q 'IRIS_26497_SHORT_CORRESPONDENCE_HOST' "$RECON" || fail "26497 short host ownership marker missing"
grep -q 'IRIS_26497_POSTMERGE_RCD_SINGLE_AUTHORITY' "$RCDHOST" || fail "26497 RCD host marker missing"
pass "PRE-BUILD SAFETY PROOF PASSED: normal Wronski/capture/tone protected; root highlight/RCD-border/UHDR owners isolated"

# Gate 5: changed GLSL compile validation with Photon runtime LAYOUT substitution.
{
  echo '#version 310 es'
  echo '#define LAYOUT layout(local_size_x=8, local_size_y=8, local_size_z=1) in;'
  tail -n +3 "$SHORT"
} > "$TMP/short_recover.comp"
{
  echo '#version 310 es'
  echo '#define LAYOUT layout(local_size_x=8, local_size_y=8, local_size_z=1) in;'
  tail -n +3 "$CHROMA"
} > "$TMP/rcd_chroma_complete.comp"
{
  echo '#version 310 es'
  echo '#define LAYOUT layout(local_size_x=8, local_size_y=8, local_size_z=1) in;'
  tail -n +3 "$WRITE"
} > "$TMP/rcd_write.comp"
{
  echo '#version 300 es'
  cat "$GAIN"
} > "$TMP/gainmap.frag"
: > "$SHADERLOG"
for spec in "$TMP/short_recover.comp:comp" "$TMP/rcd_chroma_complete.comp:comp" "$TMP/rcd_write.comp:comp" "$TMP/gainmap.frag:frag"; do
  f="${spec%%:*}"; stage="${spec##*:}"
  glslangValidator -S "$stage" "$f" >> "$SHADERLOG" 2>&1     || { cat "$SHADERLOG"; fail "GLSL validation failed $f"; }
done
pass "all four changed GLSL programs compile"

# Gate 6: version increment occurs only after every safety/source/shader gate, then Java + APK build in this same guarded script.
python3 - "$CAND/app/version.properties" <<'PY_VER'
from pathlib import Path
import sys
p=Path(sys.argv[1]); s=p.read_text()
if s.count('VERSION_NAME=0.9726496')!=1 or s.count('VERSION_BUILD=26496')!=1:
    raise SystemExit('26496 version anchors not unique')
s=s.replace('VERSION_NAME=0.9726496','VERSION_NAME=0.9726497',1)
s=s.replace('VERSION_BUILD=26496','VERSION_BUILD=26497',1)
p.write_text(s)
PY_VER
grep -q '^VERSION_NAME=0.9726497$' "$CAND/app/version.properties" || fail "version name bump failed"
grep -q '^VERSION_BUILD=26497$' "$CAND/app/version.properties" || fail "build bump failed"
pass "version incremented to 0.9726497 / 26497 in guarded build command"

# Save the exact intended 26496->26497 app delta (including version bump) before Gradle.
(
  cd "$CAND"
  git add -N app/src/main app/version.properties >/dev/null 2>&1 || true
  git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties
) > "$DELTA"

# Record canonical pre-build source hashes. Gradle/CMake may create only four known ignored headers.
python3 - "$CAND" "$TMP/prebuild26497.sha256" <<'PY_PRE'
from pathlib import Path
import hashlib,sys
root=Path(sys.argv[1]); out=Path(sys.argv[2])
files=sorted([p for p in (root/'app/src/main').rglob('*') if p.is_file()] + [root/'app/version.properties'])
if len(files)!=857: raise SystemExit(f'prebuild canonical count={len(files)} expected 857')
out.write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(root)}\n' for p in files))
PY_PRE

(
  cd "$CAND"
  ./gradlew --no-daemon :app:compileDebugJavaWithJavac
  ./gradlew --no-daemon assembleDebug
) 2>&1 | tee "$BUILDLOG"

mapfile -t APKS < <(find "$CAND/app/build/outputs/apk/debug" -maxdepth 1 -type f -name '*.apk' | sort)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one debug APK, found ${#APKS[@]}: ${APKS[*]}"
cp "${APKS[0]}" "$REPO/$APK_NAME"

# Gate 7: build may create exactly four known CMake dependency headers, nothing else in canonical source.
python3 - "$CAND" "$TMP/prebuild26497.sha256" <<'PY_POST'
from pathlib import Path
import hashlib,sys
root=Path(sys.argv[1]); pre=Path(sys.argv[2])
expected={}
for line in pre.read_text().splitlines():
    h,rel=line.split(None,1); expected[rel.strip()]=h
all_files={str(p.relative_to(root)):p for p in (root/'app/src/main').rglob('*') if p.is_file()}
all_files['app/version.properties']=root/'app/version.properties'
transient={
'app/src/main/cpp/deps/archive.h',
'app/src/main/cpp/deps/archive_entry.h',
'app/src/main/cpp/deps/technicallyflac.h',
'app/src/main/cpp/deps/tiny_dng_writer.h',
}
extra=set(all_files)-set(expected)
missing=set(expected)-set(all_files)
if missing: raise SystemExit('postbuild missing canonical source: '+repr(sorted(missing)))
if extra!=transient: raise SystemExit('postbuild unexpected source extras: '+repr(sorted(extra)))
for rel,h in expected.items():
    got=hashlib.sha256(all_files[rel].read_bytes()).hexdigest()
    if got!=h: raise SystemExit(f'postbuild canonical source changed {rel}: {got} != {h}')
print('PASS: post-build source = 857 canonical files byte-identical + exactly 4 known CMake headers')
for rel in transient:
    all_files[rel].unlink()
PY_POST

# Emit clean successful 26497 source baseline and manifest for the next build.
(
  cd "$CAND"
  { find app/src/main -type f -print; echo app/version.properties; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done > "$AFTERHASH"
  [[ "$(wc -l < "$AFTERHASH")" -eq 857 ]] || fail "26497 successful manifest count not 857"
  tar -czf "$NEXTBUNDLE" app/src/main app/version.properties
)
sha256sum "$REPO/$APK_NAME" > "$OUTDIR/$APK_NAME.sha256"
sha256sum "$AFTERHASH" "$NEXTBUNDLE" "$DELTA" "$PREPATCH" > "$OUTDIR/26497_artifact_hashes.sha256"
cat > "$REPORT" <<REPORT
26497 BUILD SUCCESS
Branch: $EXPECTED_BRANCH
Protected successful 26496 commit: $EXPECTED_SUCCESS_26496
Backup: $BACKUP_BRANCH
Version/build: $NEW_VERSION / $NEW_BUILD
APK: $APK_NAME
Canonical source files: 857
Normal Wronski/capture/tone: byte-identical to successful 26496
Short HDR: corrected base-flow semantics + bounded local CFA correspondence refinement
Chroma: coherent multi-direction physical evidence; isolated seed cannot propagate
Border: one RCD authority edge-to-edge; PPG handoff removed
UHDR: non-overlapping 4x4 per-pixel log-gain ownership; no cross-cell smoothing
Short B: not introduced
REPORT
pass "post-build canonical source integrity + transient CMake exclusion"
pass "26497 BUILD SUCCESS"
pass "successful 26496 -> scoped root-correction 26497 lineage proven"
pass "APK + canonical 26497 next baseline emitted"
echo "APK: $REPO/$APK_NAME"
