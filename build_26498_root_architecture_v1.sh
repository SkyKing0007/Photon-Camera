#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
hash_eq(){ local f="$1" e="$2"; [[ -f "$f" ]] || fail "missing protected file $f"; [[ "$(sha "$f")" == "$e" ]] || fail "protected hash mismatch $f"; }

EXPECTED_BRANCH="experimental-clean-photon-rebuild"
EXPECTED_INFRA_26497="00deeae2c82518511988ca6267b2e6071300cba6"
EXPECTED_INFRA_26494="287590c2e847522cac06752ecdc6be4c0ca3b42a"
EXPECTED_APP_BASE="8233415edf738bf35c0fe1c4907f5dfe51de31a4"
BACKUP_BRANCH="backup-26497-tested-regression-before-26498-root-architecture"
BASELINE_BUNDLE="26494_successful_app_source.tar.gz"
BASELINE_BUNDLE_SHA="ee4ccb614d9cb216e2e39a76adc8f72ce9fe2a07daa75eb6f705e958502e010b"
BASELINE_MANIFEST="26494_successful_after.sha256"
BASELINE_MANIFEST_SHA="939a7555adaf1b9859e8fc9e40798b38ac5b85343dfbdb45cfe34a4a88b500c7"
PATCH="26498_source_delta_from_exact_26494.patch"
PATCH_SHA="988691939ff9ac70a6c0ece1eae03a44c5d0f46cb4a541448c94bd10ad0106a3"
VALIDATOR="validate_26498_root_architecture.py"
VALIDATOR_SHA="cf0a86765bb078c5f7c611b3d20b3a9cada1a42e5bd623ee98ac0da84cc14f83"
OLD_VERSION="0.9726494"
OLD_BUILD="26494"
NEW_VERSION="0.9726498"
NEW_BUILD="26498"
APK_NAME="IrisCamera-${NEW_VERSION}-${NEW_BUILD}-root-architecture-debug.apk"

REPO="$(pwd)"
OUTDIR="$REPO/build_26498_outputs"
TMP="${RUNNER_TEMP:-/tmp}/photon_26498_$$"
BASE="$TMP/base26494"
CAND="$TMP/candidate26498"
PREPATCH="$OUTDIR/26498_pre_edit_exact_26494_complete_binary.patch"
DELTA="$OUTDIR/26498_delta_from_exact_26494.patch"
AFTERHASH="$OUTDIR/26498_successful_after.sha256"
NEXTBUNDLE="$OUTDIR/26498_successful_app_source.tar.gz"
BUILDLOG="$OUTDIR/26498_build.log"
SHADERLOG="$OUTDIR/26498_shader_validation.txt"
REPORT="$OUTDIR/26498_build_report.txt"
rm -rf "$OUTDIR" "$TMP"; mkdir -p "$OUTDIR" "$TMP"
cleanup(){ set +e; git worktree remove --force "$BASE" >/dev/null 2>&1 || true; git worktree remove --force "$CAND" >/dev/null 2>&1 || true; rm -rf "$TMP"; }
trap cleanup EXIT

echo "=== 26498 ROOT ARCHITECTURE: PROVENANCE-IN-RCD + MIRRORED BOUNDARY + 1:1 UHDR + CHROMA ORIGIN TELEMETRY ==="
date -Iseconds || true

# Gate 0: exact infrastructure lineage and user-created safety checkpoint.
BRANCH="${GITHUB_REF_NAME:-$(git branch --show-current)}"
[[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || fail "wrong branch=$BRANCH expected=$EXPECTED_BRANCH"
[[ "$BRANCH" != "dev" ]] || fail "dev is protected"
git cat-file -e "$EXPECTED_INFRA_26497^{commit}" || fail "26497 infrastructure checkpoint unavailable"
git cat-file -e "$EXPECTED_INFRA_26494^{commit}" || fail "26494 infrastructure checkpoint unavailable"
git cat-file -e "$EXPECTED_APP_BASE^{commit}" || fail "protected app base unavailable"
git merge-base --is-ancestor "$EXPECTED_INFRA_26497" HEAD || fail "HEAD does not descend from tested 26497"
git merge-base --is-ancestor "$EXPECTED_INFRA_26494" HEAD || fail "HEAD does not descend from 26494"
git diff --quiet "$EXPECTED_APP_BASE" -- app/src/main app/version.properties || fail "committed app source changed; infrastructure-only workflow contract violated"
backup="$(git ls-remote origin "refs/heads/$BACKUP_BRANCH" | awk '{print $1}')"
[[ "$backup" == "$EXPECTED_INFRA_26497" ]] || fail "required pre-26498 backup missing/moved: $BACKUP_BRANCH=$backup expected=$EXPECTED_INFRA_26497"
pass "tested 26497 lineage + protected app tree + exact pre-26498 backup"

# Gate 1: immutable package and root-architecture math identities.
[[ -f "$BASELINE_BUNDLE" && "$(sha "$BASELINE_BUNDLE")" == "$BASELINE_BUNDLE_SHA" ]] || fail "26494 source bundle identity mismatch"
[[ -f "$BASELINE_MANIFEST" && "$(sha "$BASELINE_MANIFEST")" == "$BASELINE_MANIFEST_SHA" ]] || fail "26494 manifest identity mismatch"
[[ -f "$PATCH" && "$(sha "$PATCH")" == "$PATCH_SHA" ]] || fail "26498 source patch identity mismatch"
[[ -f "$VALIDATOR" && "$(sha "$VALIDATOR")" == "$VALIDATOR_SHA" ]] || fail "26498 validator identity mismatch"
python3 -m py_compile "$VALIDATOR" || fail "26498 validator Python syntax"
python3 "$VALIDATOR" || fail "26498 root architecture self-test"
bash -n "$0" || fail "build script shell syntax"
[[ "$(wc -l < "$BASELINE_MANIFEST")" -eq 856 ]] || fail "26494 manifest count must be 856"
pass "package identities + 26498 root-architecture synthetic tests"

reconstruct_exact_26494(){
 local d="$1"; git worktree add --detach "$d" "$EXPECTED_APP_BASE" >/dev/null
 rm -rf "$d/app/src/main"; rm -f "$d/app/version.properties"
 (cd "$d" && tar -xzf "$REPO/$BASELINE_BUNDLE") || fail "extract exact 26494 source bundle"
 python3 - "$d" "$REPO/$BASELINE_MANIFEST" <<'PY'
from pathlib import Path
import hashlib,sys
root=Path(sys.argv[1]); manifest=Path(sys.argv[2]); expected={}
for line in manifest.read_text().splitlines():
    if line.strip(): h,rel=line.split(None,1); expected[rel.strip()]=h
actual=sorted([str(p.relative_to(root)) for p in (root/'app/src/main').rglob('*') if p.is_file()]+['app/version.properties'])
if len(expected)!=856: raise SystemExit('26494 manifest count mismatch')
if actual!=sorted(expected): raise SystemExit('26494 canonical file-set mismatch')
for rel,h in expected.items():
    if hashlib.sha256((root/rel).read_bytes()).hexdigest()!=h: raise SystemExit('26494 hash mismatch '+rel)
ver=(root/'app/version.properties').read_text()
if 'VERSION_NAME=0.9726494' not in ver or 'VERSION_BUILD=26494' not in ver: raise SystemExit('26494 version proof failed')
print('PASS: exact successful 26494 source verified 856/856')
PY
}

# Gate 2: two exact source copies + mandatory binary pre-modification patch.
reconstruct_exact_26494 "$BASE"; reconstruct_exact_26494 "$CAND"
pass "two independent exact 26494 source copies reconstructed"
(cd "$BASE"; git add -N app/src/main app/version.properties >/dev/null 2>&1 || true; git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties) > "$PREPATCH"
[[ -s "$PREPATCH" ]] || fail "pre-edit exact-26494 binary patch empty"
sha256sum "$PREPATCH" > "$PREPATCH.sha256"
pass "binary pre-edit exact-26494 patch created before modification"

# Gate 3: one immutable curated root patch and exact source scope.
git -C "$CAND" apply --check "$REPO/$PATCH" || fail "26498 source patch preflight"
git -C "$CAND" apply "$REPO/$PATCH" || fail "26498 source patch application"
python3 - "$BASE" "$CAND" <<'PY'
from pathlib import Path
import hashlib,sys
base=Path(sys.argv[1]); cand=Path(sys.argv[2])
modified={
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2RcdDemosaic.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/StageTelemetry.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java',
}
created={
'app/src/main/assets/shaders/motionv2/rcd26498_populate.glsl',
'app/src/main/assets/shaders/motionv2/rcd26498_vh_direction.glsl',
'app/src/main/assets/shaders/motionv2/rcd26498_lpf.glsl',
'app/src/main/assets/shaders/motionv2/rcd26498_green.glsl',
'app/src/main/assets/shaders/motionv2/rcd26498_diag_residual.glsl',
'app/src/main/assets/shaders/motionv2/rcd26498_opposite.glsl',
'app/src/main/assets/shaders/motionv2/rcd26498_green_rb.glsl',
'app/src/main/assets/shaders/motionv2/rcd26498_write.glsl',
}
def files(root):
 out={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'app/src/main').rglob('*') if p.is_file()}; out['app/version.properties']=hashlib.sha256((root/'app/version.properties').read_bytes()).hexdigest(); return out
a,b=files(base),files(cand)
if set(a)-set(b): raise SystemExit('26498 unexpectedly removed files: '+repr(sorted(set(a)-set(b))))
if set(b)-set(a)!=created: raise SystemExit('26498 created-file scope mismatch: '+repr(sorted(set(b)-set(a))))
changed={r for r in set(a)&set(b) if a[r]!=b[r]}
if changed!=modified: raise SystemExit('26498 modified-file scope mismatch: '+repr(sorted(changed)))
if len(a)!=856 or len(b)!=864: raise SystemExit(f'canonical counts base={len(a)} cand={len(b)} expected 856/864')
if a['app/version.properties']!=b['app/version.properties']: raise SystemExit('version changed before safety gates')
print('PASS: exact pre-version scope = 8 modified + 8 new; 848 baseline files byte-identical')
PY
DIFFCHECK="$TMP/26494_to_26498_diff_check.txt"
set +e; git diff --no-index --check -- "$BASE/app/src/main" "$CAND/app/src/main" > "$DIFFCHECK" 2>&1; rc=$?; set -e
[[ "$rc" -le 1 ]] || { cat "$DIFFCHECK"; fail "26498 delta whitespace check execution"; }
[[ ! -s "$DIFFCHECK" ]] || { cat "$DIFFCHECK"; fail "26498 introduced whitespace error"; }
pass "temporary-copy patch + exact scope + whitespace validation"

# Gate 4: protect normal Motion/Wronski/tone/color architecture; prove only evidence-backed carry-forwards.
M="$CAND/app/src/main"; S="$M/assets/shaders/motionv2"
CAP="$M/java/com/particlesdevs/photoncamera/capture/CaptureController.java"
RECON="$M/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"
RCDHOST="$M/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2RcdDemosaic.java"
RENDERHOST="$M/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java"
TELEM="$M/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/StageTelemetry.java"
POST="$M/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java"
SHORT="$S/short_highlight_bayer_recover.glsl"; GAIN="$S/gainmap.glsl"
hash_eq "$S/mfsr_bayer_accumulate.glsl" "40af5a9c0bf3e43ecb5c860b8e0e53c42aaadae3c96c04da7e151aa37dd1ed2b"
hash_eq "$S/mfsr_bayer_normalize.glsl" "1a9fbdcc5472d3bfb49ca8732023c4f50c81fe6a45ec1b6e00824d6fdbf5cc54"
hash_eq "$S/render.glsl" "2a3aa0c6e3cc553e11d4feeb6ecf24768f14e423ce359a3248b9f70dda7a8dbf"
hash_eq "$S/color_transform.glsl" "4b14131a59e2358a9b8b18ded4c167f15cc0af5e0ab3d380768625017d7a81ac"
hash_eq "$M/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java" "a542aeae6b484b12fdb89ef97b3a74f694da121707f2d3163b138b34d867b625"
hash_eq "$M/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java" "bb3882b6bf8b7a4e4aef7a17ee44d90f68d2ad398a923c4fe46b4aa02201bf45"
for spec in \
 rcd26489_populate.glsl:769fbe0f2cbf226adaf1b66129f7f45833deaa2c05f6e063c691dc75dfe30b04 \
 rcd26489_vh_direction.glsl:66831dfd1a39a4b5866631f1058a2883dd237961f33cc4c0bd169a7e02a0873e \
 rcd26489_lpf.glsl:95dff8fa0f3c4420de8e13346b766c7a2a80f76b08634b3b8135f775cac06a0c \
 rcd26489_green.glsl:4f268056ae8d8f1da8ae5b3936768cbb7d3841f9ac4e4b54ac6f113ca6a55040 \
 rcd26489_diag_residual.glsl:47e7041976905fb76a54acb36e19d30d4d29d8e4dd9d25012f0515978170a2e3 \
 rcd26489_diag_direction.glsl:1bd8f80b12e06f5ab8c19bb65d27e60f31998327557df0e6f551c682bdfc2b0e \
 rcd26489_opposite.glsl:30e732e00e50aeca0d29d08529230c3d043b81e8df87b0c4504768e89fe80392 \
 rcd26489_green_rb.glsl:b0476f9e5a7b130d7c3edc58b7ba4a033edc5fa2c55605fd446feea8e1b3e4ca \
 rcd26489_write.glsl:78b9894e40d584b9bc9abce69c13cdd7057a51fc99e825c6581183d762c882ec; do f="${spec%%:*}"; h="${spec##*:}"; hash_eq "$S/$f" "$h"; done

grep -q 'IRIS_26496_SPATIALLY_PERSISTENT_HIGHLIGHT_TRIGGER' "$CAP" || fail "small-highlight trigger carry-forward missing"
grep -q 'MOTION_26480_SHORT_PROTECTION_EV = 2.5f' "$CAP" || fail "proven -2.5EV Short A missing"
grep -q 'IRIS_26497_SHORT_CORRESPONDENCE_REFINEMENT' "$SHORT" || fail "proven 26497 short semantic correction missing"
grep -q 'float flowConfidence = exp(-80.0 \* variation);' "$SHORT" || fail "flow semantic correction missing"
! grep -q 'cancelled=step\|cancelled = step' "$SHORT" || fail "old interpolation-cancel hard rejection survived"
grep -q 'IRIS_26496_SHORT_FAILURE_DIAGNOSTIC_OWNER' "$RECON" || fail "short evidence telemetry missing"
! grep -Eqi 'short[[:space:]_-]*b([^a-zA-Z]|$)|SHORT_B' "$SHORT" "$RECON" "$CAP" || fail "unexpected Short B introduced"

# New RCD authority: provenance is carried INSIDE the directional solution, not patched after RGB.
grep -q 'IRIS_26498_PROVENANCE_INSIDE_RCD_AND_TRUE_MIRRORED_BOUNDARY' "$RCDHOST" || fail "26498 RCD host missing"
grep -q 'GLBuffer trust = scratch' "$RCDHOST" || fail "RCD trust carrier missing"
grep -q 'raw.x + 2 \* RCD_HALO' "$RCDHOST" || fail "horizontal mirrored halo allocation missing"
grep -q 'coreRows + 2 \* RCD_HALO' "$RCDHOST" || fail "vertical mirrored halo allocation missing"
grep -q 'rcd26498_populate' "$RCDHOST" || fail "26498 populate not active"
grep -q 'rcd26498_write' "$RCDHOST" || fail "26498 writer not active"
! grep -q 'rcd26496_chroma_complete' "$RCDHOST" || fail "post-RCD chroma patch survived active graph"
! grep -q 'ppg' "$RCDHOST" || fail "PPG algorithm switching survived active host"
grep -q 'IRIS_26498_RCD_PROVENANCE_SEED_AUTHORITY' "$S/rcd26498_populate.glsl" || fail "provenance seed shader missing"
grep -q 'trust\[idx\] = measured ? 1.0 : 0.0' "$S/rcd26498_populate.glsl" || fail "CENSORED trust state missing"
grep -q 'IRIS_26498_RCD_DIRECTION_USES_MEASURED_EVIDENCE_ONLY' "$S/rcd26498_vh_direction.glsl" || fail "direction trust gate missing"
grep -q 'IRIS_26498_RCD_OPPONENT_CHROMA_REQUIRES_PHYSICAL_CONSENSUS' "$S/rcd26498_opposite.glsl" || fail "opponent consensus missing"
grep -q 'IRIS_26498_RCD_TRUE_MIRRORED_HALO_BORDER' "$S/rcd26498_write.glsl" || fail "true mirror boundary writer missing"

# UHDR root fix: one gain sample per primary pixel, R8 carrier, no decoder spatial scaling.
grep -q 'GAINMAP_DOWNSAMPLE = 1' "$RENDERHOST" || fail "full-resolution gain map host missing"
grep -q 'new Point(renderedSdrSize)' "$RENDERHOST" || fail "gain map not 1:1 with SDR"
grep -q 'DataType.SIMPLE_8, 1' "$RENDERHOST" || fail "single-channel R8 gain map carrier missing"
grep -q 'IRIS_26498_FULL_RESOLUTION_ULTRAHDR_GAIN_AUTHORITY' "$GAIN" || fail "full-res gain shader missing"
! grep -q 'DOWNSAMPLE\|FOOTPRINT' "$GAIN" || fail "downsampled gain ownership survived"

# Wall/pink origin telemetry is image-pass-through only and has explicit stage boundaries.
grep -q 'IRIS_26498_STAGE_CHROMA_ORIGIN_TELEMETRY' "$TELEM" || fail "chroma origin telemetry missing"
grep -q 'WorkingTexture = source' "$TELEM" || fail "telemetry pass-through invariant missing"
grep -q 'flatLogRGStd' "$TELEM" || fail "flat-region R/G variance metric missing"
grep -q 'flatLogBGStd' "$TELEM" || fail "flat-region B/G variance metric missing"
grep -q 'V2_POST_FUSED_BAYER_CANONICAL' "$POST" || fail "fused CFA telemetry stage missing"
grep -q 'V2_POST_RCD_AFTER_TEMPORAL_MERGE' "$POST" || fail "post-RCD telemetry stage missing"
grep -q 'V2_POST_CAMERA2_COLOR_TRANSFORM' "$POST" || fail "post-color-transform telemetry stage missing"
pass "PRE-BUILD SAFETY PROOF PASSED: curated 26494 image baseline + proven short evidence + provenance-in-RCD + true mirror boundary + 1:1 UHDR + non-image telemetry"

# Gate 5: compile every changed/new GLSL program with Photon runtime LAYOUT substitution.
: > "$SHADERLOG"
compile_comp(){ local src="$1" out="$TMP/$(basename "$src").comp"; { echo '#version 310 es'; echo '#define LAYOUT layout(local_size_x=8, local_size_y=8, local_size_z=1) in;'; tail -n +3 "$src"; } > "$out"; glslangValidator -S comp "$out" >> "$SHADERLOG" 2>&1 || { cat "$SHADERLOG"; fail "GLSL compute validation failed $src"; }; }
compile_comp "$SHORT"
for f in rcd26498_populate rcd26498_vh_direction rcd26498_lpf rcd26498_green rcd26498_diag_residual rcd26498_opposite rcd26498_green_rb rcd26498_write; do compile_comp "$S/$f.glsl"; done
{ echo '#version 300 es'; cat "$GAIN"; } > "$TMP/gainmap.frag"
glslangValidator -S frag "$TMP/gainmap.frag" >> "$SHADERLOG" 2>&1 || { cat "$SHADERLOG"; fail "GLSL fragment validation failed gainmap"; }
pass "all ten changed/new GLSL programs compile"

# Gate 6: version increment only after all source/math/shader gates, then Java + complete APK build in same script.
python3 - "$CAND/app/version.properties" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); s=p.read_text()
if s.count('VERSION_NAME=0.9726494')!=1 or s.count('VERSION_BUILD=26494')!=1: raise SystemExit('26494 version anchors not unique')
s=s.replace('VERSION_NAME=0.9726494','VERSION_NAME=0.9726498',1).replace('VERSION_BUILD=26494','VERSION_BUILD=26498',1); p.write_text(s)
PY
grep -q '^VERSION_NAME=0.9726498$' "$CAND/app/version.properties" || fail "version name bump failed"
grep -q '^VERSION_BUILD=26498$' "$CAND/app/version.properties" || fail "build bump failed"
pass "version incremented to 0.9726498 / 26498 in guarded build command"
(cd "$CAND"; git add -N app/src/main app/version.properties >/dev/null 2>&1 || true; git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties) > "$DELTA"
python3 - "$CAND" "$TMP/prebuild26498.sha256" <<'PY'
from pathlib import Path
import hashlib,sys
root=Path(sys.argv[1]); out=Path(sys.argv[2]); files=sorted([p for p in (root/'app/src/main').rglob('*') if p.is_file()]+[root/'app/version.properties'])
if len(files)!=864: raise SystemExit(f'prebuild canonical count={len(files)} expected 864')
out.write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(root)}\n' for p in files))
PY
(cd "$CAND"; ./gradlew --no-daemon :app:compileDebugJavaWithJavac; ./gradlew --no-daemon assembleDebug) 2>&1 | tee "$BUILDLOG"
mapfile -t APKS < <(find "$CAND/app/build/outputs/apk/debug" -maxdepth 1 -type f -name '*.apk' | sort)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one debug APK, found ${#APKS[@]}: ${APKS[*]}"
cp "${APKS[0]}" "$REPO/$APK_NAME"

# Gate 7: canonical source must remain byte-identical after build except four known CMake generated headers.
python3 - "$CAND" "$TMP/prebuild26498.sha256" <<'PY'
from pathlib import Path
import hashlib,sys
root=Path(sys.argv[1]); pre=Path(sys.argv[2]); expected={}
for line in pre.read_text().splitlines(): h,rel=line.split(None,1); expected[rel.strip()]=h
allf={str(p.relative_to(root)):p for p in (root/'app/src/main').rglob('*') if p.is_file()}; allf['app/version.properties']=root/'app/version.properties'
trans={'app/src/main/cpp/deps/archive.h','app/src/main/cpp/deps/archive_entry.h','app/src/main/cpp/deps/technicallyflac.h','app/src/main/cpp/deps/tiny_dng_writer.h'}
extra=set(allf)-set(expected); missing=set(expected)-set(allf)
if missing: raise SystemExit('postbuild missing canonical source: '+repr(sorted(missing)))
if extra!=trans: raise SystemExit('postbuild unexpected source extras: '+repr(sorted(extra)))
for rel,h in expected.items():
    if hashlib.sha256(allf[rel].read_bytes()).hexdigest()!=h: raise SystemExit('postbuild canonical source changed '+rel)
for rel in trans: allf[rel].unlink()
print('PASS: post-build source = 864 canonical files byte-identical + exactly 4 known CMake headers')
PY
(cd "$CAND"; { find app/src/main -type f -print; echo app/version.properties; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done > "$AFTERHASH"; [[ "$(wc -l < "$AFTERHASH")" -eq 864 ]] || fail "26498 successful manifest count not 864"; tar -czf "$NEXTBUNDLE" app/src/main app/version.properties)
sha256sum "$REPO/$APK_NAME" > "$OUTDIR/$APK_NAME.sha256"
sha256sum "$AFTERHASH" "$NEXTBUNDLE" "$DELTA" "$PREPATCH" > "$OUTDIR/26498_artifact_hashes.sha256"
cat > "$REPORT" <<REPORT
26498 BUILD SUCCESS
Branch: $EXPECTED_BRANCH
Tested-regression rollback: $EXPECTED_INFRA_26497
Curated image baseline: exact successful 26494 source
Backup: $BACKUP_BRANCH
Version/build: $NEW_VERSION / $NEW_BUILD
APK: $APK_NAME
Canonical source files: 864
Normal Wronski accumulator/alignment/tone/color: protected
Short HDR carried forward only where proven: 26496 spatial trigger + -2.5EV Short A + 26497 flow/correspondence semantics
RCD: CENSORED placeholder retained only numerically; TrustBuf prevents it from steering direction/opponent chroma
Border: one RCD algorithm with 12-pixel virtual mirrored CFA halo on all four true-photo sides
Post-RCD chroma completion: absent
Wall/pink diagnosis: non-image-changing stage log-color-ratio variance at fused CFA, post-RCD, post-color-transform, render
UHDR: full-resolution 1:1 R8 logarithmic gain map; no gain-map spatial resampling required
REPORT
pass "post-build canonical source integrity + transient CMake exclusion"
pass "26498 BUILD SUCCESS"
pass "exact 26494 -> curated evidence-backed 26498 lineage proven"
pass "APK + canonical 26498 next baseline emitted"
echo "APK: $REPO/$APK_NAME"
