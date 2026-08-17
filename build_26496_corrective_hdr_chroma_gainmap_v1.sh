#!/usr/bin/env bash
set -euo pipefail

fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
hash_eq(){ local f="$1" e="$2"; [[ -f "$f" ]] || fail "missing protected file $f"; [[ "$(sha "$f")" == "$e" ]] || fail "protected hash mismatch $f"; }

EXPECTED_BRANCH="experimental-clean-photon-rebuild"
EXPECTED_INFRA_26495="a57f40de471b3210184483d17c744b24573ef113"
EXPECTED_FAILED_26496_V1="9ba05fb0e06ce61fb89db3c9c72565e04a4103d0"
EXPECTED_INFRA_26494="287590c2e847522cac06752ecdc6be4c0ca3b42a"
EXPECTED_APP_BASE="8233415edf738bf35c0fe1c4907f5dfe51de31a4"
BACKUP_BRANCH="backup-26495-v1.2-before-26496-corrective-hdr-chroma-gainmap"
FAILED_V1_BACKUP_BRANCH="backup-26496-v1-failed-before-v1.1-java-import-fix"
BASELINE_BUNDLE="26494_successful_app_source.tar.gz"
BASELINE_BUNDLE_SHA="ee4ccb614d9cb216e2e39a76adc8f72ce9fe2a07daa75eb6f705e958502e010b"
BASELINE_MANIFEST="26494_successful_after.sha256"
BASELINE_MANIFEST_SHA="939a7555adaf1b9859e8fc9e40798b38ac5b85343dfbdb45cfe34a4a88b500c7"
PATCH="26496_source_delta_from_exact_26494.patch"
PATCH_SHA="bcaa3a59c3e700356eed72f27c5cc82714f82c5425eb3661fee88654ab572fdb"
VALIDATOR="validate_26496_corrective_hdr_gain.py"
VALIDATOR_SHA="c53477685f6e33b5aca039c1ed819413e782c70213a9440e175ff5ad1ba9e97b"
OLD_VERSION="0.9726494"
OLD_BUILD="26494"
NEW_VERSION="0.9726496"
NEW_BUILD="26496"
APK_NAME="IrisCamera-${NEW_VERSION}-${NEW_BUILD}-corrective-hdr-chroma-gainmap-debug.apk"

REPO="$(pwd)"
OUTDIR="$REPO/build_26496_outputs"
TMP="${RUNNER_TEMP:-/tmp}/photon_26496_$$"
BASE="$TMP/base26494"
CAND="$TMP/candidate26496"
PREPATCH="$OUTDIR/26496_pre_edit_exact_26494_complete_binary.patch"
DELTA="$OUTDIR/26496_delta_from_exact_26494.patch"
AFTERHASH="$OUTDIR/26496_successful_after.sha256"
NEXTBUNDLE="$OUTDIR/26496_successful_app_source.tar.gz"
BUILDLOG="$OUTDIR/26496_build.log"
SHADERLOG="$OUTDIR/26496_shader_validation.txt"
REPORT="$OUTDIR/26496_build_report.txt"

rm -rf "$OUTDIR" "$TMP"
mkdir -p "$OUTDIR" "$TMP"
cleanup(){
    set +e
    git worktree remove --force "$BASE" >/dev/null 2>&1 || true
    git worktree remove --force "$CAND" >/dev/null 2>&1 || true
    rm -rf "$TMP"
}
trap cleanup EXIT

echo "=== 26496 CORRECTIVE HDR EVIDENCE + SMOOTH CHROMA COMPLETION + GAIN-DOMAIN UHDR ==="
date -Iseconds || true

# Gate 0: exact infrastructure lineage. 26496 intentionally returns to the exact
# successful 26494 image-quality source and selectively applies only the audited
# 26496 correction. The checked-out app source must remain infrastructure-only.
BRANCH="${GITHUB_REF_NAME:-$(git branch --show-current)}"
[[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || fail "wrong branch=$BRANCH expected=$EXPECTED_BRANCH"
[[ "$BRANCH" != "dev" ]] || fail "dev is protected"
git cat-file -e "$EXPECTED_INFRA_26495^{commit}" || fail "successful 26495 V1.2 infrastructure checkpoint unavailable"
git cat-file -e "$EXPECTED_FAILED_26496_V1^{commit}" || fail "failed 26496 V1 infrastructure checkpoint unavailable"
git cat-file -e "$EXPECTED_INFRA_26494^{commit}" || fail "26494 infrastructure checkpoint unavailable"
git cat-file -e "$EXPECTED_APP_BASE^{commit}" || fail "protected app base unavailable"
git merge-base --is-ancestor "$EXPECTED_INFRA_26495" HEAD || fail "HEAD does not descend from successful 26495 V1.2 checkpoint"
git merge-base --is-ancestor "$EXPECTED_FAILED_26496_V1" HEAD || fail "HEAD does not descend from failed 26496 V1 checkpoint"
git merge-base --is-ancestor "$EXPECTED_INFRA_26494" HEAD || fail "HEAD does not descend from 26494 checkpoint"
git diff --quiet "$EXPECTED_APP_BASE" -- app/src/main app/version.properties \
    || fail "committed app source changed; infrastructure-only workflow contract violated"
remote_backup="$(git ls-remote origin "refs/heads/$BACKUP_BRANCH" | awk '{print $1}')"
[[ "$remote_backup" == "$EXPECTED_INFRA_26495" ]] \
    || fail "required pre-26496 backup missing/moved: $BACKUP_BRANCH=$remote_backup expected=$EXPECTED_INFRA_26495"
failed_v1_backup="$(git ls-remote origin "refs/heads/$FAILED_V1_BACKUP_BRANCH" | awk '{print $1}')"
[[ "$failed_v1_backup" == "$EXPECTED_FAILED_26496_V1" ]] \
    || fail "required failed-v1 backup missing/moved: $FAILED_V1_BACKUP_BRANCH=$failed_v1_backup expected=$EXPECTED_FAILED_26496_V1"
pass "exact 26495 V1.2 + failed 26496 V1 lineage + protected app tree + both backups"

# Gate 1: immutable package identities and deterministic math self-test.
[[ -f "$BASELINE_BUNDLE" && "$(sha "$BASELINE_BUNDLE")" == "$BASELINE_BUNDLE_SHA" ]] \
    || fail "26494 source bundle identity mismatch"
[[ -f "$BASELINE_MANIFEST" && "$(sha "$BASELINE_MANIFEST")" == "$BASELINE_MANIFEST_SHA" ]] \
    || fail "26494 manifest identity mismatch"
[[ -f "$PATCH" && "$(sha "$PATCH")" == "$PATCH_SHA" ]] || fail "26496 source patch identity mismatch"
[[ -f "$VALIDATOR" && "$(sha "$VALIDATOR")" == "$VALIDATOR_SHA" ]] || fail "26496 validator identity mismatch"
python3 -m py_compile "$VALIDATOR" || fail "26496 validator Python syntax"
python3 "$VALIDATOR" || fail "26496 math/architecture self-test"
bash -n "$0" || fail "build script shell syntax"
[[ "$(wc -l < "$BASELINE_MANIFEST")" -eq 856 ]] || fail "26494 manifest count must be 856"
pass "package identities + 26496 exposure/chroma/UHDR math tests"

reconstruct_exact_26494(){
    local d="$1"
    git worktree add --detach "$d" "$EXPECTED_APP_BASE" >/dev/null
    rm -rf "$d/app/src/main"
    rm -f "$d/app/version.properties"
    ( cd "$d" && tar -xzf "$REPO/$BASELINE_BUNDLE" ) || fail "extract exact 26494 source bundle"
    python3 - "$d" "$REPO/$BASELINE_MANIFEST" <<'PY_VERIFY'
from pathlib import Path
import hashlib,sys
root=Path(sys.argv[1]); manifest=Path(sys.argv[2])
expected={}
for line in manifest.read_text().splitlines():
    if line.strip():
        h,rel=line.split(None,1); expected[rel.strip()]=h
actual=sorted([str(p.relative_to(root)) for p in (root/'app/src/main').rglob('*') if p.is_file()] + ['app/version.properties'])
if len(expected)!=856: raise SystemExit(f'expected manifest count={len(expected)} !=856')
if actual!=sorted(expected):
    raise SystemExit('26494 canonical file-set mismatch')
for rel,h in expected.items():
    got=hashlib.sha256((root/rel).read_bytes()).hexdigest()
    if got!=h: raise SystemExit(f'26494 canonical hash mismatch {rel}: {got} != {h}')
ver=(root/'app/version.properties').read_text()
if 'VERSION_NAME=0.9726494' not in ver or 'VERSION_BUILD=26494' not in ver:
    raise SystemExit('exact 26494 version proof failed')
print('PASS: exact successful 26494 source verified 856/856')
PY_VERIFY
}

# Gate 2: reconstruct independent proof/candidate trees from exact successful 26494.
reconstruct_exact_26494 "$BASE"
reconstruct_exact_26494 "$CAND"
pass "two independent exact 26494 source copies reconstructed"

# Mandatory complete binary pre-modification patch is created BEFORE any 26496
# application-source modification.
(
    cd "$BASE"
    git add -N app/src/main app/version.properties >/dev/null 2>&1 || true
    git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties
) > "$PREPATCH"
[[ -s "$PREPATCH" ]] || fail "pre-edit exact-26494 binary patch empty"
sha256sum "$PREPATCH" > "$PREPATCH.sha256"
pass "binary pre-edit exact-26494 patch created before modification"

# Gate 3: apply one immutable corrective patch and prove exact source scope.
git -C "$CAND" apply --check "$REPO/$PATCH" || fail "26496 source patch preflight"
git -C "$CAND" apply "$REPO/$PATCH" || fail "26496 source patch application"
python3 - "$BASE" "$CAND" <<'PY_SCOPE'
from pathlib import Path
import hashlib,sys
base=Path(sys.argv[1]); cand=Path(sys.argv[2])
modified={
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2RcdDemosaic.java',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
}
created={'app/src/main/assets/shaders/motionv2/rcd26496_chroma_complete.glsl'}
def files(root):
    out={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
         for p in (root/'app/src/main').rglob('*') if p.is_file()}
    out['app/version.properties']=hashlib.sha256((root/'app/version.properties').read_bytes()).hexdigest()
    return out
a,b=files(base),files(cand)
removed=set(a)-set(b); new=set(b)-set(a)
if removed: raise SystemExit('26496 unexpectedly removed files: '+repr(sorted(removed)))
if new!=created: raise SystemExit('26496 new-file scope mismatch: '+repr(sorted(new)))
changed={r for r in set(a)&set(b) if a[r]!=b[r]}
if changed!=modified: raise SystemExit('26496 modified-file scope mismatch: '+repr(sorted(changed)))
if len(a)!=856 or len(b)!=857: raise SystemExit(f'canonical counts base={len(a)} cand={len(b)} expected 856/857')
if a['app/version.properties']!=b['app/version.properties']:
    raise SystemExit('version changed before pre-build safety gates')
print('PASS: exact pre-version scope = 6 modified + 1 new shader; 850 baseline files byte-identical')
PY_SCOPE
DIFFCHECK="$TMP/26494_to_26496_diff_check.txt"
set +e
git diff --no-index --check -- "$BASE/app/src/main" "$CAND/app/src/main" > "$DIFFCHECK" 2>&1
diffcheck_rc=$?
set -e
[[ "$diffcheck_rc" -le 1 ]] || { cat "$DIFFCHECK"; fail "26496 delta whitespace check execution"; }
[[ ! -s "$DIFFCHECK" ]] || { cat "$DIFFCHECK"; fail "26496 introduced whitespace error"; }
pass "temporary-copy patch + exact scope + delta-only whitespace validation"

# Gate 4: protected image-quality architecture hashes and explicit ownership proofs.
M="$CAND/app/src/main"
RCD="$M/assets/shaders/motionv2"
CAP="$M/java/com/particlesdevs/photoncamera/capture/CaptureController.java"
RECON="$M/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"
GLBUFFER="$M/java/com/particlesdevs/photoncamera/processing/opengl/GLBuffer.java"
RCDHOST="$M/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2RcdDemosaic.java"
RENDERHOST="$M/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java"
SHORT="$RCD/short_highlight_bayer_recover.glsl"
CHROMA="$RCD/rcd26496_chroma_complete.glsl"
GAIN="$RCD/gainmap.glsl"

# All nine 26494 RCD directional passes remain byte-identical.
hash_eq "$RCD/rcd26489_populate.glsl" "769fbe0f2cbf226adaf1b66129f7f45833deaa2c05f6e063c691dc75dfe30b04"
hash_eq "$RCD/rcd26489_vh_direction.glsl" "66831dfd1a39a4b5866631f1058a2883dd237961f33cc4c0bd169a7e02a0873e"
hash_eq "$RCD/rcd26489_lpf.glsl" "95dff8fa0f3c4420de8e13346b766c7a2a80f76b08634b3b8135f775cac06a0c"
hash_eq "$RCD/rcd26489_green.glsl" "4f268056ae8d8f1da8ae5b3936768cbb7d3841f9ac4e4b54ac6f113ca6a55040"
hash_eq "$RCD/rcd26489_diag_residual.glsl" "47e7041976905fb76a54acb36e19d30d4d29d8e4dd9d25012f0515978170a2e3"
hash_eq "$RCD/rcd26489_diag_direction.glsl" "1bd8f80b12e06f5ab8c19bb65d27e60f31998327557df0e6f551c682bdfc2b0e"
hash_eq "$RCD/rcd26489_opposite.glsl" "30e732e00e50aeca0d29d08529230c3d043b81e8df87b0c4504768e89fe80392"
hash_eq "$RCD/rcd26489_green_rb.glsl" "b0476f9e5a7b130d7c3edc58b7ba4a033edc5fa2c55605fd446feea8e1b3e4ca"
hash_eq "$RCD/rcd26489_write.glsl" "78b9894e40d584b9bc9abce69c13cdd7057a51fc99e825c6581183d762c882ec"
# Tone/render curve and 26489 accumulator are byte-identical to 26494.
hash_eq "$RCD/render.glsl" "2a3aa0c6e3cc553e11d4feeb6ecf24768f14e423ce359a3248b9f70dda7a8dbf"
hash_eq "$RCD/mfsr_bayer_accumulate.glsl" "40af5a9c0bf3e43ecb5c860b8e0e53c42aaadae3c96c04da7e151aa37dd1ed2b"
hash_eq "$RCD/mfsr_bayer_normalize.glsl" "1a9fbdcc5472d3bfb49ca8732023c4f50c81fe6a45ec1b6e00824d6fdbf5cc54"

# 26489 normal stack invariants and strict exposure cohort stay present.
grep -q 'IRIS_26489_BJZHOU_PERSISTENT_BAYER_HOST' "$RECON" || fail "26489 persistent accumulator host missing"
grep -q 'IRIS_26489_ADMISSION_EQUALS_ACCUMULATOR_CONTRIBUTION_INVARIANT' "$RECON" || fail "26489 admitted==contributed invariant missing"
grep -q 'IRIS_26489_BJZHOU_BAYER_NORMALIZE_EXACTLY_ONCE' "$RECON" || fail "26489 normalize-once owner missing"
grep -q 'MOTION_26486_EXPOSURE_HALF_WINDOW_EV = 0.05' "$CAP" || fail "normal exposure cohort half-window changed"
grep -q '2.0 \* MOTION_26486_EXPOSURE_HALF_WINDOW_EV' "$CAP" || fail "normal exposure cohort span changed"
! grep -q 'IRIS_26497' "$CAP" || fail "future frame-hardening code leaked into 26496"

# Separate highlight-only trigger: old global trigger remains, normal sampler is
# not replaced, and the auxiliary remains an isolated short-capture decision.
grep -q 'IRIS_26496_SPATIALLY_PERSISTENT_HIGHLIGHT_TRIGGER' "$CAP" || fail "26496 spatial highlight trigger missing"
grep -q 'sampleMotion26496SpatialHighlightEvidence' "$CAP" || fail "separate highlight sampler missing"
grep -q 'legacyFractionTrigger' "$CAP" || fail "legacy highlight trigger removed"
grep -q 'MOTION_26496_HIGHLIGHT_EVIDENCE_HOLD_NS = 400_000_000L' "$CAP" || fail "highlight persistence window changed"
grep -q 'MOTION_26480_SHORT_PROTECTION_EV = 2.5f' "$CAP" || fail "Short A physical headroom changed"
grep -q '5.656854249492381' "$CAP" || fail "Short A divisor changed"
grep -q 'IRIS_26495_CLAMP_AWARE_SHORT_RADIOMETRY' "$CAP" || fail "clamp-aware short validation missing"

# Short recovery image logic remains 26494 plus diagnostic-only atomic counters.
grep -q 'IRIS_26494_PER_PHASE_SHORT_VALIDATION' "$SHORT" || fail "26494 per-phase short validation missing"
grep -q 'IRIS_26496_SHORT_FAILURE_REASON_TELEMETRY' "$SHORT" || fail "short failure telemetry missing"
grep -q 'layout(std430, binding = 2) buffer ShortDiagBuf' "$SHORT" || fail "tiny short diagnostic SSBO missing"
hash_eq "$GLBUFFER" "77b69ccd3e547afaaf974724ab408387828882f6e053aa92ea0db3fd8c9f39f9"
grep -q 'import com.particlesdevs.photoncamera.processing.opengl.GLBuffer;' "$RECON" || fail "GLBuffer import missing"
grep -q 'public GLBuffer(int size,GLFormat mFormat)' "$GLBUFFER" || fail "GLBuffer constructor contract changed"
grep -q 'readBufferIntegers(boolean clear)' "$GLBUFFER" || fail "GLBuffer diagnostic readback API changed"
grep -q 'new GLBuffer(' "$RECON" || fail "short diagnostic buffer owner missing"
grep -q '64, new GLFormat(GLFormat.DataType.UNSIGNED_32)' "$RECON" || fail "short diagnostic buffer not 64 uints"
grep -q 'IRIS_26496_SHORT_FAILURE_REASONS' "$RECON" || fail "short diagnostic readback/log missing"

# Original 26494 RCD geometry executes first; the new completion reuses existing
# buffers and may only alter missing opponent chroma near CENSORED provenance.
grep -q 'IRIS_26496_RCD_MISSING_CHROMA_NORMALIZED_CONVOLUTION' "$CHROMA" || fail "26496 chroma completion shader missing"
grep -q 'if (affected\[i\] < 0.5) return' "$CHROMA" || fail "unaffected-region exact no-op missing"
grep -q 'ownTrusted && c == 0' "$CHROMA" || fail "trusted physical red immutability missing"
grep -q 'ownTrusted && c == 2' "$CHROMA" || fail "trusted physical blue immutability missing"
grep -q 'Peak scratch remains exactly nine FLOAT32 band buffers' "$RCDHOST" || fail "RCD buffer-reuse contract missing"
grep -q 'pixels \* 9L \* Float.BYTES' "$RCDHOST" || fail "RCD scratch footprint changed"
grep -q 'extraFullBandScratchBuffers=0' "$RCDHOST" || fail "RCD no-extra-buffer telemetry missing"
python3 - "$RCDHOST" <<'PY_RCD_ORDER'
from pathlib import Path
import re,sys
s=Path(sys.argv[1]).read_text()
programs=re.findall(r'useAssetProgram\("(motionv2/rcd[^" ]+)"',s)
want=[
'motionv2/rcd26489_populate','motionv2/rcd26489_vh_direction','motionv2/rcd26489_lpf',
'motionv2/rcd26489_green','motionv2/rcd26489_diag_residual','motionv2/rcd26489_diag_direction',
'motionv2/rcd26489_opposite','motionv2/rcd26489_green_rb','motionv2/rcd26496_chroma_complete',
'motionv2/rcd26489_write']
if programs!=want: raise SystemExit('RCD program order changed: '+repr(programs))
if s.count('glProg.setVar("mode", 0);')!=1 or s.count('glProg.setVar("mode", 1);')!=1:
    raise SystemExit('RCD completion must run exactly seed + completion dispatch')
print('PASS: original 26494 RCD pass order + post-RCD chroma completion order')
PY_RCD_ORDER
! grep -R -q 'IRIS_26495_RCD_OPPOSITE_PROVENANCE_WEIGHT\|IRIS_26495_RCD_GREEN_SITE_PROVENANCE_WEIGHT\|IRIS_26495_CENSORED_LUMA_ONLY_CHROMA_AUTHORITY' "$M" \
    || fail "rejected 26495 hard chroma-authority implementation reintroduced"
! grep -R -q 'IRIS_26493_FINAL_WRITE_CHROMA' "$M" || fail "rejected 26493 final-RGB repair reintroduced"

# Gain map is formed in full-resolution log-gain domain before filtering; no
# independent HDR/SDR pre-blur. SDR base/tone host is unchanged except telemetry.
grep -q 'IRIS_26496_GUIDED_LOG_GAIN_DECIMATION' "$GAIN" || fail "26496 guided log-gain shader missing"
grep -q 'float logGain=clamp(log2(ratio)' "$GAIN" || fail "log-gain-first math missing"
grep -q 'GUIDE_SIGMA_EV = 0.90' "$GAIN" || fail "gain edge guide changed"
grep -q 'DOWNSAMPLE = 4' "$GAIN" || fail "gain-map 4:1 geometry changed"
! grep -q 'bandlimitedLuminance\|hdrMean\|sdrMean' "$GAIN" || fail "rejected separate HDR/SDR prefilter path present"
grep -q 'GAINMAP_DOWNSAMPLE = 4' "$RENDERHOST" || fail "gain-map dimensions changed"
grep -q 'Math.min(2.5f, OUTPUT_EXPOSURE_SCALE \* postDisplaySensorWhite)' "$RENDERHOST" || fail "UHDR max-gain ownership changed"
grep -q 'fullResolutionLogGainFirst=true' "$RENDERHOST" || fail "26496 UHDR telemetry missing"

# Explicitly forbid previously rejected downstream appearance patches.
! grep -R -q 'MotionV2Denoise' "$M/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2RcdDemosaic.java" || fail "MotionV2Denoise reintroduced in RCD graph"
! grep -R -q 'IRIS_26493_FINAL_WRITE_CHROMA' "$M" || fail "26493 final RGB cleanup present"
pass "PRE-BUILD SAFETY PROOF PASSED: 26489/26494 normal path + tone + RCD geometry protected; 26496 changes isolated"

# Gate 5: type-aware GLSL static compilation for every changed/new shader.
# Photon substitutes LAYOUT at runtime for compute shaders.
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
    echo '#version 300 es'
    cat "$GAIN"
} > "$TMP/gainmap.frag"
: > "$SHADERLOG"
for spec in "$TMP/short_recover.comp:comp" "$TMP/rcd_chroma_complete.comp:comp" "$TMP/gainmap.frag:frag"; do
    f="${spec%%:*}"; stage="${spec##*:}"
    glslangValidator -S "$stage" "$f" >> "$SHADERLOG" 2>&1 \
        || { cat "$SHADERLOG"; fail "GLSL validation failed $f"; }
done
pass "changed/new GLSL compile validation"

# Gate 6: version increment only after every source/math/architecture safety gate,
# in the same invocation that performs the Java/Gradle APK build.
python3 - "$CAND/app/version.properties" <<'PY_VER'
from pathlib import Path
import sys
p=Path(sys.argv[1]); s=p.read_text()
a='VERSION_NAME=0.9726494'; b='VERSION_BUILD=26494'
if s.count(a)!=1 or s.count(b)!=1: raise SystemExit('26494 version anchors not unique')
s=s.replace(a,'VERSION_NAME=0.9726496',1).replace(b,'VERSION_BUILD=26496',1)
p.write_text(s)
PY_VER
grep -q '^VERSION_NAME=0\.9726496$' "$CAND/app/version.properties" || fail "version name bump failed"
grep -q '^VERSION_BUILD=26496$' "$CAND/app/version.properties" || fail "version build bump failed"
pass "version incremented to 0.9726496 / 26496 in build command"

# Human-reviewable complete delta from exact successful 26494 IQ source.
git diff --no-index --binary "$BASE/app" "$CAND/app" > "$DELTA" || [[ $? -eq 1 ]] || fail "26496 delta generation"
[[ -s "$DELTA" ]] || fail "26496 delta empty"

# Gate 7: snapshot exact canonical 26496 source before Gradle/native compilation.
PREBUILD_CANONICAL="$TMP/26496_prebuild_canonical.sha256"
(
    cd "$CAND"
    { find app/src/main -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum; sha256sum app/version.properties; } > "$PREBUILD_CANONICAL"
)
[[ "$(wc -l < "$PREBUILD_CANONICAL")" -eq 857 ]] || fail "pre-build canonical 26496 count not 857"

# Java compiler and complete Android/native APK build are authoritative.
(
    cd "$CAND"
    ./gradlew --no-daemon :app:compileDebugJavaWithJavac
    ./gradlew --no-daemon assembleDebug
) 2>&1 | tee "$BUILDLOG"

mapfile -t APKS < <(find "$CAND/app/build/outputs/apk/debug" -maxdepth 1 -type f -name '*.apk' | sort)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one debug APK, found ${#APKS[@]}: ${APKS[*]}"
cp "${APKS[0]}" "$REPO/$APK_NAME"
[[ -s "$REPO/$APK_NAME" ]] || fail "final APK missing"
sha256sum "$REPO/$APK_NAME" > "$OUTDIR/$APK_NAME.sha256"

# Gate 8: native CMake is known to download exactly four ignored dependency
# headers into the source tree during a successful build. Prove all 857 canonical
# files stayed byte-identical, permit exactly those four side-effects, remove only
# them, then archive the true canonical 26496 source baseline.
python3 - "$CAND" "$PREBUILD_CANONICAL" <<'PY_POSTBUILD'
from pathlib import Path
import hashlib,sys
root=Path(sys.argv[1]); pre=Path(sys.argv[2])
expected={}
for line in pre.read_text().splitlines():
    if line.strip():
        h,rel=line.split(None,1); expected[rel.strip()]=h
if len(expected)!=857:
    raise SystemExit(f'pre-build canonical manifest count={len(expected)} expected=857')
actual={str(p.relative_to(root)) for p in (root/'app/src/main').rglob('*') if p.is_file()} | {'app/version.properties'}
known_generated={
    'app/src/main/cpp/deps/archive.h',
    'app/src/main/cpp/deps/archive_entry.h',
    'app/src/main/cpp/deps/technicallyflac.h',
    'app/src/main/cpp/deps/tiny_dng_writer.h',
}
extra=actual-set(expected); missing=set(expected)-actual
if missing: raise SystemExit('canonical source missing after build: '+repr(sorted(missing)))
if extra!=known_generated:
    raise SystemExit('unexpected post-build source side-effects: '+repr(sorted(extra))+' expected='+repr(sorted(known_generated)))
for rel,h in expected.items():
    got=hashlib.sha256((root/rel).read_bytes()).hexdigest()
    if got!=h: raise SystemExit(f'canonical source mutated by build: {rel} pre={h} post={got}')
for rel in known_generated:
    p=root/rel
    if not p.is_file() or p.stat().st_size<=0:
        raise SystemExit('known generated dependency missing/empty after native build: '+rel)
print('PASS: post-build source = 857 canonical files byte-identical + exactly 4 known CMake headers')
PY_POSTBUILD
rm -f \
    "$CAND/app/src/main/cpp/deps/archive.h" \
    "$CAND/app/src/main/cpp/deps/archive_entry.h" \
    "$CAND/app/src/main/cpp/deps/technicallyflac.h" \
    "$CAND/app/src/main/cpp/deps/tiny_dng_writer.h"

(
    cd "$CAND"
    { find app/src/main -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum; sha256sum app/version.properties; } > "$AFTERHASH"
    tar -czf "$NEXTBUNDLE" app/src/main app/version.properties
)
[[ "$(wc -l < "$AFTERHASH")" -eq 857 ]] || fail "26496 canonical successful manifest count not 857"
cmp -s "$PREBUILD_CANONICAL" "$AFTERHASH" || fail "post-build canonical source differs from exact pre-build 26496 candidate"
[[ "$(tar -tzf "$NEXTBUNDLE" | grep -v '/$' | wc -l)" -eq 857 ]] || fail "26496 canonical bundle file count not 857"
sha256sum "$NEXTBUNDLE" "$AFTERHASH" "$DELTA" > "$OUTDIR/26496_artifact_hashes.sha256"
pass "post-build canonical source integrity + transient CMake exclusion"

cat > "$REPORT" <<EOF
26496 BUILD SUCCESS
Version: $NEW_VERSION / $NEW_BUILD
IQ baseline: exact successful 26494 source (26495 image regressions deliberately not inherited)
Infrastructure parent checkpoint: successful 26495 V1.2 $EXPECTED_INFRA_26495
Required backup branch: $BACKUP_BRANCH
APK: $APK_NAME
APK SHA256: $(sha "$REPO/$APK_NAME")

26496 corrective architecture
1. Normal Motion remains 26489/26494: rolling ZSL, strict equal-exposure cohort, Wronski, frame-0 geometry, persistent R32F Bayer accumulator, admitted==contributed, normalize once.
2. Short A remains isolated at nominal -2.5 EV/same ISO with clamp-aware actual Camera2 metadata validation. It never enters the normal Motion accumulator and cannot own global brightness.
3. The existing 26494 AE/readiness sampler remains its normal authority. A separate 3x3-dithered, spatially persistent highlight-only sampler can request Short A for small coherent LEDs/glints that the old global 0.2% rule missed.
4. Short recovery math keeps 26494 per-phase physical validation. A tiny 64-uint diagnostic SSBO reports exactly why clipped phases remain unresolved: short clipped, flow, correspondence, radiometry, validated, still censored, plus physical-phase and value histograms.
5. All nine original 26494 RCD directional shaders are byte-identical. After them, a two-dispatch missing-chroma completion uses only NORMAL/SHORT_VALIDATED physical R-G/B-G seeds, green-guided normalized convolution, smooth weak-support neutralization, and zero extra full-band scratch buffers.
6. UHDR gain is formed at full resolution first: HDR/SDR -> log2 gain -> positive Gaussian + SDR edge guide -> 4:1 sampling. 26495's rejected blur-HDR + blur-SDR + divide method is absent. Full-resolution SDR and tone are unchanged.

Math/safety proofs
- 2^2.5 = 5.656854249492381; worst accepted short-to-normal scale under +/-0.35 EV tolerance remains <8x.
- Separate 3x3 highlight dither covers sub-cell offsets without changing normal AE statistics.
- Positive symmetric gain kernel response: ~0.0943 at source f=1/8 and ~0.0340 at f=3/16.
- Synthetic step edge: rejected 26495 separate-prefilter gain leak ~1.846x; 26496 guided log-gain result ~1.009x on adjacent low-gain side.
- Missing-chroma normalized convolution preserves constant trusted residuals and fades weak support continuously toward neutral.
- RCD scratch remains 9 FLOAT32 band buffers; no +22% prototype memory expansion.

Frozen/protected
- no frame hardening in 26496
- no normal AE/shutter/ISO/exposure-cohort change
- no Wronski or normal accumulator change
- no Camera2 color-transform change
- no tone/display-exposure curve change
- no MotionV2Denoise or sharpening reintroduction
- no 26493 final-RGB color cleanup
- no 26495 hard 0/1 RCD chroma-authority implementation
EOF

pass "26496 BUILD SUCCESS"
pass "exact 26494 IQ baseline -> scoped corrective 26496 lineage proven"
pass "APK + canonical 26496 next baseline emitted"
echo "APK: $REPO/$APK_NAME"
