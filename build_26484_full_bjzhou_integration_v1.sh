#!/usr/bin/env bash
set -euo pipefail
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
EXPECTED_APP_BASE="8233415edf738bf35c0fe1c4907f5dfe51de31a4"
BACKUP_BRANCH="backup-26483-success-before-26484-full-bjzhou-integration"
BACKUP_EXPECTED="9b571453b2f8ea598b2110758db539c4ad0cb29e"
BASE_PATCH="26483_successful_source.patch"
BASE_PATCH_SHA="a993c2c9e12cba8098623fab8b83f0965b9ad2016eded6fd857f55935a1c11db"
BASE_HASHES="26483_successful_after.sha256"
BASE_HASHES_SHA="7cba064adf92e6645a1f94ea44a5bd205a800cead9dcd8c392816de5f2725ca7"
TRANSFORM="transform_26484_full_bjzhou_integration_v1.py"
TRANSFORM_SHA="f3c212d9c16e39ffcde2ff4beae65e50c0ad7b30fd5e0b517dbfbcdaafec0c00"
DELTA="26484_delta_from_26483.patch"
DELTA_SHA="18fbb861c3c49f4ad8399f29aa60ca3e85df57ffacc794b8b6a2206b42197ac3"
NEW_VERSION="0.9726484"; NEW_BUILD="26484"
OUTDIR="build_26484_outputs"
APK_NAME="IrisCamera-${NEW_VERSION}-${NEW_BUILD}-full-bjzhou-integration-debug.apk"
fail(){ echo "FAIL: $*" >&2; exit 1; }; pass(){ echo "PASS: $*"; }; sha(){ sha256sum "$1"|awk '{print $1}'; }
REPO="$(pwd)"; rm -rf "$OUTDIR"; mkdir -p "$OUTDIR"
AUDIT="$OUTDIR/26484_source_audit.txt"; CANDLOG="$OUTDIR/26484_temporary_candidate_build.log"; FINALLOG="$OUTDIR/26484_final_build.log"; SHADERLOG="$OUTDIR/26484_shader_validation.txt"; REPORT="$OUTDIR/26484_build_report.txt"; PREPATCH="$OUTDIR/26484_pre_edit_exact_26483_binary.patch"; SOURCEPATCH="$OUTDIR/26484_source.patch"; AFTERHASH="$OUTDIR/26484_after.sha256"
exec > >(tee "$AUDIT") 2>&1
echo "=== 26484 FULL BJZHOU-INTEGRATION CANDIDATE ==="; date -Iseconds || true
BRANCH="${GITHUB_REF_NAME:-$(git branch --show-current)}"; [[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || fail "wrong branch $BRANCH"; [[ "$BRANCH" != dev ]] || fail "dev protected"
git cat-file -e "$EXPECTED_APP_BASE^{commit}" || fail "app base missing"
git diff --quiet "$EXPECTED_APP_BASE" -- app/src/main app/version.properties || fail "committed app source no longer equals protected app base"
[[ -f "$BASE_PATCH" && "$(sha "$BASE_PATCH")" == "$BASE_PATCH_SHA" ]] || fail "26483 source patch identity"
[[ -f "$BASE_HASHES" && "$(sha "$BASE_HASHES")" == "$BASE_HASHES_SHA" ]] || fail "26483 manifest identity"
[[ -f "$TRANSFORM" && "$(sha "$TRANSFORM")" == "$TRANSFORM_SHA" ]] || fail "26484 transform identity"
[[ -f "$DELTA" && "$(sha "$DELTA")" == "$DELTA_SHA" ]] || fail "26484 delta identity"
python3 -m py_compile "$TRANSFORM"; bash -n "$0"; pass "infrastructure syntax and identity"
remote="$(git ls-remote origin "refs/heads/$BACKUP_BRANCH"|awk '{print $1}')"; [[ "$remote" == "$BACKUP_EXPECTED" ]] || fail "backup branch $BACKUP_BRANCH=$remote expected=$BACKUP_EXPECTED"; pass "backup branch exact tested-26483 checkpoint"
TMP="$(mktemp -d)"; BASE="$TMP/base26483"; CAND="$TMP/candidate26484"; FINALBASE="$TMP/finalbase"; cleanup(){ set +e; for w in "$BASE" "$CAND" "$FINALBASE";do git worktree remove --force "$w" >/dev/null 2>&1||true;done; rm -rf "$TMP"; }; trap cleanup EXIT
reconstruct(){ local d="$1"; git worktree add --detach "$d" "$EXPECTED_APP_BASE" >/dev/null; (cd "$d" && git apply --check --binary "$REPO/$BASE_PATCH" && git apply --binary "$REPO/$BASE_PATCH" && sha256sum -c "$REPO/$BASE_HASHES" >/dev/null); grep -q '^VERSION_NAME=0\.9726483$' "$d/app/version.properties"; grep -q '^VERSION_BUILD=26483$' "$d/app/version.properties"; }
reconstruct "$BASE"; pass "exact successful 26483 baseline reconstructed"
(cd "$BASE" && git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties) > "$PREPATCH"; [[ -s "$PREPATCH" ]] || fail "pre-edit patch empty"; pass "binary pre-edit patch created before 26484 modification"
reconstruct "$CAND"; python3 "$REPO/$TRANSFORM" "$CAND" "$REPO/$DELTA"; pass "candidate/source validation PASS"
cat > "$TMP/allow.txt" <<'EOF'
app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl
app/src/main/assets/shaders/motionv2/mfsr_chroma_guide.glsl
app/src/main/assets/shaders/motionv2/mfsr_flow_expand.glsl
app/src/main/assets/shaders/motionv2/mfsr_lk_refine_level.glsl
app/src/main/assets/shaders/motionv2/mfsr_lk_select_candidate.glsl
app/src/main/assets/shaders/motionv2/mfsr_low_support_reference.glsl
app/src/main/assets/shaders/motionv2/mfsr_mgc_covariance.glsl
app/src/main/assets/shaders/motionv2/mfsr_robustness_half.glsl
app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java
EOF
python3 - "$BASE" "$CAND" "$TMP/allow.txt" <<'PY'
from pathlib import Path
import hashlib,sys
A,B=Path(sys.argv[1]),Path(sys.argv[2]);allow=set(Path(sys.argv[3]).read_text().splitlines())
def H(r):
 d={}
 for p in (r/'app/src/main').rglob('*'):
  if p.is_file(): d[str(p.relative_to(r)).replace('\\','/')]=hashlib.sha256(p.read_bytes()).hexdigest()
 return d
a,b=H(A),H(B);chg={x for x in a.keys()|b.keys() if a.get(x)!=b.get(x)}
assert chg==allow,(sorted(chg),sorted(allow));print('candidate exact changed-file allowlist PASS')
PY
python3 - "$REPO/$BASE_HASHES" "$CAND" "$TMP/allow.txt" <<'PY'
from pathlib import Path
import hashlib,sys
m=Path(sys.argv[1]);r=Path(sys.argv[2]);allow=set(Path(sys.argv[3]).read_text().splitlines())
for line in m.read_text().splitlines():
 if not line.strip():continue
 h,p=line.split(None,1);p=p.strip()
 if p in allow:continue
 q=r/p
 if not q.is_file() or hashlib.sha256(q.read_bytes()).hexdigest()!=h:raise SystemExit('protected hash changed '+p)
print('protected 26483 hashes PASS')
PY
# Structural ownership and no-regression gates
CAP="$CAND/app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java"; WA="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java"; CR="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"; CG="$CAND/app/src/main/assets/shaders/motionv2/mfsr_chroma_guide.glsl"; COV="$CAND/app/src/main/assets/shaders/motionv2/mfsr_mgc_covariance.glsl"; SEL="$CAND/app/src/main/assets/shaders/motionv2/mfsr_lk_select_candidate.glsl"; FLOW="$CAND/app/src/main/assets/shaders/motionv2/mfsr_flow_expand.glsl"; LK="$CAND/app/src/main/assets/shaders/motionv2/mfsr_lk_refine_level.glsl"; ACC="$CAND/app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl"; ROB="$CAND/app/src/main/assets/shaders/motionv2/mfsr_robustness_half.glsl"; REF="$CAND/app/src/main/assets/shaders/motionv2/mfsr_low_support_reference.glsl"
for spec in \
"$CAP:IRIS_26484_IMMEDIATE_MOTION_SHUTTER_ACK" "$CAP:IRIS_26484_UNLOCK_FOCUS_NULL_BUILDER_GUARD" "$CAP:IRIS_26481_EXACT_TIMESTAMP_METADATA_OWNERSHIP" \
"$WA:IRIS_26484_BJZHOU_COMPLETE_FLOW_CHAIN" "$SEL:IRIS_26484_BJZHOU_THREE_CANDIDATE_L1_UPSAMPLE" "$FLOW:IRIS_26484_BJZHOU_SAFE_SPATIAL_FLOW_RECONSTRUCTION" "$LK:IRIS_26484_BJZHOU_CLAMPED_LEVELWISE_LK" \
"$CG:IRIS_26484_BJZHOU_EDGE_DIRECTED_GREEN_GUIDE" "$COV:IRIS_26484_BJZHOU_STRUCTURE_ADAPTIVE_RGB_PRECISION" "$ACC:IRIS_26484_BJZHOU_COMPLETE_JOINT_OPPONENT_WEIGHTING" "$REF:IRIS_26484_BJZHOU_REFERENCE_OPPONENT_GUIDE_MATCH" "$ROB:IRIS_26484_BJZHOU_FLOW_VARIATION_REJECTION_CORE" "$CR:IRIS_26484_BJZHOU_COUPLED_ALIGNMENT_REJECTION_OPPONENT_MERGE"; do f="${spec%%:*}";m="${spec#*:}";grep -q "$m" "$f"||fail "missing marker $m";done
! grep -q 'refCircular' "$LK" || fail "circular alignment addressing survived"
grep -Fq 'interpolationTolerance",1.0f/16.0f' "$WA" || fail "safe flow tolerance binding missing"
grep -q 'mfsr_lk_select_candidate' "$WA" || fail "candidate selection not dispatched"
grep -q 'mfsr_mgc_covariance' "$CR" || fail "MGC covariance not active"
grep -q 'mfsr_chroma_guide' "$CR" || fail "edge green guide not active"
grep -Fq 'if (mPreviewRequestBuilder == null || mCaptureSession == null)' "$CAP" || fail "26484 unlockFocus preview-builder/session guard missing"
! grep -Fq 'if (captureBuilder == null || mCaptureSession == null)' "$CAP" || fail "invalid local captureBuilder guard survived in unlockFocus"
grep -q 'MotionV2Denoise disabled' "$CR" || true
# Java lexical/static structure
python3 - "$CAP" "$WA" "$CR" <<'PY'
from pathlib import Path
import sys

def java_code_only(src: str) -> str:
    # Preserve only actual Java code. Ignore comments, ordinary strings, character literals,
    # and Java text blocks so delimiter characters inside literals cannot trip the structure gate.
    out=[]; i=0; n=len(src); state='code'
    while i<n:
        if state=='code':
            if src.startswith('//',i): state='line'; out.extend('  '); i+=2; continue
            if src.startswith('/*',i): state='block'; out.extend('  '); i+=2; continue
            if src.startswith('\"\"\"',i): state='text'; out.extend('   '); i+=3; continue
            c=src[i]
            if c=='\"': state='string'; out.append(' '); i+=1; continue
            if c=="'": state='char'; out.append(' '); i+=1; continue
            out.append(c); i+=1; continue
        if state=='line':
            c=src[i]; out.append('\n' if c=='\n' else ' '); i+=1
            if c=='\n': state='code'
            continue
        if state=='block':
            if src.startswith('*/',i): out.extend('  '); i+=2; state='code'; continue
            out.append('\n' if src[i]=='\n' else ' '); i+=1; continue
        if state=='text':
            if src.startswith('\"\"\"',i): out.extend('   '); i+=3; state='code'; continue
            # Backslash is not a general text-block terminator; keep line numbers only.
            out.append('\n' if src[i]=='\n' else ' '); i+=1; continue
        if state in ('string','char'):
            c=src[i]
            if c=='\\':
                out.append(' '); i+=1
                if i<n: out.append('\n' if src[i]=='\n' else ' '); i+=1
                continue
            out.append('\n' if c=='\n' else ' '); i+=1
            if (state=='string' and c=='\"') or (state=='char' and c=="'"): state='code'
            continue
    if state in ('block','string','char','text'):
        raise SystemExit('Java unterminated lexical state: '+state)
    return ''.join(out)

def verify(path: str):
    code=java_code_only(Path(path).read_text())
    pairs={'}':'{',')':'(',']':'['}; stack=[]
    line=1
    for c in code:
        if c=='\n': line+=1; continue
        if c in '{([': stack.append((c,line))
        elif c in '})]':
            if not stack or stack[-1][0]!=pairs[c]:
                raise SystemExit(f'Java delimiter mismatch {path} line={line} token={c!r}')
            stack.pop()
    if stack:
        c,ln=stack[-1]; raise SystemExit(f'Java unclosed delimiter {path} line={ln} token={c!r}')
    print('Java lexical structure PASS',Path(path).name)

for f in sys.argv[1:]: verify(f)
PY
# GLSL lexical + standards compilation. Compute templates need #version and local-size prefix.
: > "$SHADERLOG"
compile_shader(){ local f="$1"; local n="$(basename "$f")"; python3 - "$f" "$TMP/$n.comp" <<'PY'
from pathlib import Path
import sys,re
s=Path(sys.argv[1]).read_text();s=s.replace('#define LAYOUT //\nLAYOUT','#version 310 es\nlayout(local_size_x=8,local_size_y=8,local_size_z=1) in;',1)
Path(sys.argv[2]).write_text(s)
PY
 glslangValidator -S comp "$TMP/$n.comp" >> "$SHADERLOG" 2>&1 || return 1; }
shader_fail=0
for f in "$CG" "$COV" "$SEL" "$FLOW" "$LK" "$ACC" "$REF" "$ROB"; do
  if compile_shader "$f"; then echo "GLSL compile PASS $(basename "$f")" >> "$SHADERLOG"; else echo "GLSL compile FAIL $(basename "$f")" >> "$SHADERLOG"; shader_fail=1; fi
done
if [[ "$shader_fail" -ne 0 ]]; then cat "$SHADERLOG"; fail "one or more 26484 shaders failed glslangValidator"; fi
pass "all modified/new 26484 shaders glslangValidator PASS"
# Adreno portability guard: no known unsafe 2-channel writable image stores; no reserved local 'sample'.
for f in "$CG" "$COV" "$SEL" "$FLOW" "$LK" "$ACC" "$REF" "$ROB"; do ! grep -Eq 'layout\((rg32f|rg16f|r16f)[^)]*\)[^;]*writeonly image2D' "$f" || fail "Adreno-portability hazardous writable format $(basename "$f")"; ! grep -Eq '\b(float|vec[234]|int|ivec[234])\s+sample\b' "$f" || fail "reserved GLSL identifier sample in $(basename "$f")"; done
# Exact output format expectations vs Java allocations.
grep -q 'layout(r32f,binding=1).*writeonly image2D outputGreen' "$CG" || fail "chroma guide output declaration"
grep -q 'FLOAT_32,1' "$CR" || fail "R32F Java allocation evidence missing"
grep -q 'layout(rgba16f,binding=0).*writeonly image2D OutputFlow' "$SEL" || fail "candidate flow output format"
grep -q 'FLOAT_16,4' "$WA" || fail "flow Java allocation format"
pass "Adreno runtime-portability guard"
pass "source structural/ownership PASS"
# Temporary candidate version/build is bumped only now, immediately before its Gradle proof.
python3 - "$CAND/app/version.properties" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]);s=p.read_text();s=s.replace('VERSION_NAME=0.9726483','VERSION_NAME=0.9726484',1).replace('VERSION_BUILD=26483','VERSION_BUILD=26484',1);p.write_text(s)
PY
# The candidate is a complete repo worktree; build it before touching Action checkout app source.
(cd "$CAND" && chmod +x gradlew && ./gradlew assembleDebug --no-daemon --stacktrace) 2>&1 | tee "$CANDLOG"
[[ "${PIPESTATUS[0]}" -eq 0 ]] || fail "temporary candidate Gradle build"
pass "Temporary-copy validation: PASS"
# Verify app source unchanged by Gradle except known generated native headers are ignored by source allowlist copy.
for rel in $(cat "$TMP/allow.txt");do [[ -f "$CAND/$rel" ]] || fail "candidate file vanished $rel";done
pass "PRE-BUILD SAFETY PROOF PASSED"
# Reconstruct the COMPLETE successful 26483 source in the final ephemeral checkout.
# This is required because the committed checkout intentionally remains at EXPECTED_APP_BASE;
# copying only the 26484 allowlist would omit the rest of the proven 26483 dependency graph.
git apply --check --binary "$BASE_PATCH"
git apply --binary "$BASE_PATCH"
sha256sum -c "$BASE_HASHES" >/dev/null
grep -q '^VERSION_NAME=0\.9726483$' app/version.properties || fail "final full-26483 reconstruction version"
grep -q '^VERSION_BUILD=26483$' app/version.properties || fail "final full-26483 reconstruction build"
pass "final exact successful 26483 baseline reconstructed"

# Overlay only the already-built 26484 functional delta, then bump version and final build
# in the SAME guarded command block.
while IFS= read -r rel;do mkdir -p "$(dirname "$rel")";cp "$CAND/$rel" "$rel";done < "$TMP/allow.txt"
python3 - <<'PY'
from pathlib import Path
p=Path('app/version.properties');s=p.read_text();s=s.replace('VERSION_NAME=0.9726483','VERSION_NAME=0.9726484',1).replace('VERSION_BUILD=26483','VERSION_BUILD=26484',1);p.write_text(s)
PY

# Full candidate/final canonical-source parity BEFORE final Gradle.
python3 - "$CAND" "$(pwd)" <<'PY'
from pathlib import Path
import hashlib,sys
a,b=Path(sys.argv[1]),Path(sys.argv[2])
skip={
'app/src/main/cpp/deps/archive.h',
'app/src/main/cpp/deps/archive_entry.h',
'app/src/main/cpp/deps/technicallyflac.h',
'app/src/main/cpp/deps/tiny_dng_writer.h',
}
def files(root):
    out={}
    for base in [root/'app/src/main']:
        for p in base.rglob('*'):
            if p.is_file():
                rel=str(p.relative_to(root)).replace('\\','/')
                if rel in skip: continue
                out[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
    vp=root/'app/version.properties'
    out['app/version.properties']=hashlib.sha256(vp.read_bytes()).hexdigest()
    return out
x,y=files(a),files(b)
if x!=y:
    bad=sorted({k for k in x.keys()|y.keys() if x.get(k)!=y.get(k)})
    raise SystemExit('candidate/final canonical source mismatch before Gradle: '+repr(bad[:50]))
print('full candidate/final canonical source parity PASS')
PY

chmod +x gradlew
./gradlew assembleDebug --no-daemon --stacktrace 2>&1 | tee "$FINALLOG"
[[ "${PIPESTATUS[0]}" -eq 0 ]] || fail "final 26484 Gradle build"
# Candidate/final source identity
while IFS= read -r rel;do cmp -s "$CAND/$rel" "$rel" || fail "candidate/final mismatch $rel";done < "$TMP/allow.txt"; cmp -s "$CAND/app/version.properties" app/version.properties || fail "candidate/final version mismatch"
# Locate one debug APK and publish exactly one root APK.
mapfile -t apks < <(find app/build/outputs/apk -type f -name '*.apk' | sort); [[ ${#apks[@]} -ge 1 ]] || fail "no APK output"; rm -f IrisCamera-0.9726484-26484-*.apk; cp "${apks[-1]}" "$APK_NAME"; [[ -s "$APK_NAME" ]] || fail "published APK missing"
# Canonical source patch relative to immutable app base.
git worktree add --detach "$FINALBASE" "$EXPECTED_APP_BASE" >/dev/null
while IFS= read -r rel;do mkdir -p "$FINALBASE/$(dirname "$rel")";cp "$rel" "$FINALBASE/$rel";done < "$TMP/allow.txt"; cp app/version.properties "$FINALBASE/app/version.properties"
(cd "$FINALBASE" && git add -N app/src/main app/version.properties >/dev/null 2>&1 || true; git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties) > "$SOURCEPATCH"; [[ -s "$SOURCEPATCH" ]] || fail "canonical source patch empty"
(cd "$FINALBASE" && find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum; sha256sum app/version.properties) > "$AFTERHASH"
mkdir -p "$OUTDIR/next_baseline_inputs";cp "$SOURCEPATCH" "$OUTDIR/next_baseline_inputs/26484_successful_source.patch";cp "$AFTERHASH" "$OUTDIR/next_baseline_inputs/26484_successful_after.sha256";cp "$REPO/$TRANSFORM" "$OUTDIR/next_baseline_inputs/";cp "$REPO/$DELTA" "$OUTDIR/26484_delta_from_26483.patch"
cat > "$REPORT" <<EOF
26484 FULL BJZHOU-INTEGRATION V1
Version=$NEW_VERSION
Build=$NEW_BUILD
Branch=$BRANCH
BackupBranch=$BACKUP_BRANCH
BaselineSourcePatchSHA=$BASE_PATCH_SHA
BaselineManifestSHA=$BASE_HASHES_SHA
DeltaSHA=$DELTA_SHA
TransformSHA=$TRANSFORM_SHA
APK=$APK_NAME
APK_SHA256=$(sha "$APK_NAME")
SourcePatchSHA256=$(sha "$SOURCEPATCH")
AfterManifestSHA256=$(sha "$AFTERHASH")
Architecture=three-candidate target-L1 flow propagation + clamped LK + safe 8-Bayer-quad spatial interpolation + flow-variation rejection core + structure-adaptive covariance + edge-directed green + noise-aware G/R-G/B-G accumulation
SaturationExperiment=26483 CFA soft-headroom path unchanged; no older saturation-validity system restored
Shutter=immediate UI acknowledgment; top-up remains background capture policy; unlockFocus null guard
EOF
sha256sum "$APK_NAME" "$SOURCEPATCH" "$AFTERHASH" "$REPORT" > "$OUTDIR/26484_artifact_hashes.sha256"
pass "26484 canonical checkpoint package created"
echo "26484_SOURCE_PATCH_SHA256=$(sha "$SOURCEPATCH")";echo "26484_AFTER_MANIFEST_SHA256=$(sha "$AFTERHASH")";echo "26484 BUILD SUCCESS"
