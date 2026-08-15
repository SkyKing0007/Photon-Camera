#!/usr/bin/env bash
set -euo pipefail

EXPECTED_BRANCH="experimental-clean-photon-rebuild"
EXPECTED_APP_BASE="8233415edf738bf35c0fe1c4907f5dfe51de31a4"
BACKUP_BRANCH="backup-26488-failed-r16ui-before-26488-v2-gles-format-fix"
BACKUP_EXPECTED="a827834a73264a5f7e9b0568e4ec635f9c7993d9"

BASE26483_PATCH="26483_successful_source.patch"
BASE26483_PATCH_SHA="a993c2c9e12cba8098623fab8b83f0965b9ad2016eded6fd857f55935a1c11db"
BASE26483_HASHES="26483_successful_after.sha256"
BASE26483_HASHES_SHA="7cba064adf92e6645a1f94ea44a5bd205a800cead9dcd8c392816de5f2725ca7"
DELTA26484="26484_delta_from_26483.patch"
DELTA26484_SHA="18fbb861c3c49f4ad8399f29aa60ca3e85df57ffacc794b8b6a2206b42197ac3"
TRANSFORM26485="transform_26485_runtime_shutter_full_fix_v1.py"
TRANSFORM26485_SHA="2e04a8e250d0fb64ca3e4a7763ed4943203d7f1ae740283018a7fb1b90c9a461"
TRANSFORM26486="transform_26486_full_bjzhou_censored_opponent_latency_v1.py"
TRANSFORM26486_SHA="3030fa2543c6593711f8822a770c78de25e9347c65717420ffde291c1aad0eca"
TRANSFORM26487="transform_26487_reconstruction_correctness_latency_v2.py"
TRANSFORM26487_SHA="0580c756d1180554621aa4e7a1848271511fc2094a692b16b3b209df9bda5d77"
TRANSFORM="transform_26488_full_merge_rgb_rejection_contract_v1.py"
TRANSFORM_SHA="18ee188dfa25563e839c9d9a76ab6961e738ccc061df88a5b7fd861bc5d8112d"

NEW_VERSION="0.9726488"
NEW_BUILD="26488"
OUTDIR="build_26488_outputs"
APK_NAME="IrisCamera-${NEW_VERSION}-${NEW_BUILD}-full-merge-rgb-rejection-contract-debug.apk"

fail(){ echo "FAIL: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }

REPO="$(pwd)"
rm -rf "$OUTDIR"
mkdir -p "$OUTDIR"
AUDIT="$OUTDIR/26488_source_audit.txt"
CANDLOG="$OUTDIR/26488_temporary_candidate_build.log"
FINALLOG="$OUTDIR/26488_final_build.log"
SHADERLOG="$OUTDIR/26488_shader_validation.txt"
REPORT="$OUTDIR/26488_build_report.txt"
PREPATCH="$OUTDIR/26488_pre_edit_exact_26487_binary.patch"
DELTAOUT="$OUTDIR/26488_delta_from_26487.patch"
SOURCEPATCH="$OUTDIR/26488_source.patch"
AFTERHASH="$OUTDIR/26488_after.sha256"
PREBUILDHASH="$OUTDIR/26488_prebuild_canonical.sha256"

exec > >(tee "$AUDIT") 2>&1
echo "=== 26488 FULL BJZHOU MERGERGB + REJECTION CONTRACT ==="
date -Iseconds || true

BRANCH="${GITHUB_REF_NAME:-$(git branch --show-current)}"
[[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || fail "wrong branch $BRANCH"
[[ "$BRANCH" != "dev" ]] || fail "dev protected"

git cat-file -e "$EXPECTED_APP_BASE^{commit}" || fail "protected app base missing"
git diff --quiet "$EXPECTED_APP_BASE" -- app/src/main app/version.properties \
    || fail "committed app source no longer equals protected app base"

for spec in \
"$BASE26483_PATCH:$BASE26483_PATCH_SHA" \
"$BASE26483_HASHES:$BASE26483_HASHES_SHA" \
"$DELTA26484:$DELTA26484_SHA" \
"$TRANSFORM26485:$TRANSFORM26485_SHA" \
"$TRANSFORM26486:$TRANSFORM26486_SHA" \
"$TRANSFORM26487:$TRANSFORM26487_SHA" \
"$TRANSFORM:$TRANSFORM_SHA"
do
    f="${spec%%:*}"; expected="${spec#*:}"
    [[ -f "$f" ]] || fail "missing infrastructure input $f"
    [[ "$(sha "$f")" == "$expected" ]] || fail "identity mismatch $f"
done
python3 -m py_compile "$TRANSFORM26485" "$TRANSFORM26486" "$TRANSFORM26487" "$TRANSFORM"
python3 "$TRANSFORM" --self-test
bash -n "$0"
pass "infrastructure syntax and identity"

# Hard pre-modification backup proof. No app transform/overlay occurs before this.
remote="$(git ls-remote origin "refs/heads/$BACKUP_BRANCH" | awk '{print $1}')"
[[ "$remote" == "$BACKUP_EXPECTED" ]] \
    || fail "backup branch $BACKUP_BRANCH=$remote expected=$BACKUP_EXPECTED"
pass "backup branch exact successful 26487 checkpoint"

TMP="$(mktemp -d)"
BASE="$TMP/base26487"
CAND="$TMP/candidate26488"
cleanup(){
    set +e
    git worktree remove --force "$BASE" >/dev/null 2>&1 || true
    git worktree remove --force "$CAND" >/dev/null 2>&1 || true
    rm -rf "$TMP"
}
trap cleanup EXIT

bump(){
    local file="$1" oldv="$2" oldb="$3" newv="$4" newb="$5"
    python3 - "$file" "$oldv" "$oldb" "$newv" "$newb" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); oldv,oldb,newv,newb=sys.argv[2:]
s=p.read_text()
a=f"VERSION_NAME={oldv}"; b=f"VERSION_BUILD={oldb}"
if s.count(a)!=1 or s.count(b)!=1:
    raise SystemExit(f"version anchor mismatch {a}={s.count(a)} {b}={s.count(b)}")
p.write_text(s.replace(a,f"VERSION_NAME={newv}",1).replace(b,f"VERSION_BUILD={newb}",1))
PY
}

# Reconstruct the exact successful 26487 APPLICATION source by the same proven
# composition used by builds 26485/26486:
# protected base -> exact 26483 -> exact 26484 -> exact 26485 -> exact 26486 -> exact 26487.
# Infrastructure commits themselves intentionally never alter app/src/main.
reconstruct26487(){
    local d="$1"
    git worktree add --detach "$d" "$EXPECTED_APP_BASE" >/dev/null
    (
        cd "$d"
        git apply --check --binary "$REPO/$BASE26483_PATCH"
        git apply --binary "$REPO/$BASE26483_PATCH"
        sha256sum -c "$REPO/$BASE26483_HASHES" >/dev/null
        grep -q '^VERSION_NAME=0\.9726483$' app/version.properties
        grep -q '^VERSION_BUILD=26483$' app/version.properties

        git apply --check --binary "$REPO/$DELTA26484"
        git apply --binary "$REPO/$DELTA26484"
        bump app/version.properties 0.9726483 26483 0.9726484 26484

        python3 "$REPO/$TRANSFORM26485" "$d"
        bump app/version.properties 0.9726484 26484 0.9726485 26485
        python3 "$REPO/$TRANSFORM26486" "$d"
        bump app/version.properties 0.9726485 26485 0.9726486 26486
        python3 "$REPO/$TRANSFORM26487" "$d"
        bump app/version.properties 0.9726486 26486 0.9726487 26487

        grep -q '^VERSION_NAME=0\.9726487$' app/version.properties
        grep -q '^VERSION_BUILD=26487$' app/version.properties
        grep -q 'IRIS_26485_FULL_PREBUFFER_AUTHORITATIVE_ZSL' \
            app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
        grep -q 'IRIS_26485_FULL_PREBUFFER_IMMEDIATE_PROCESS' \
            app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
        grep -q 'IRIS_26486_FREEZE_BUFFER_AT_SHUTTER_NO_TOPUP_WAIT' \
            app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
        grep -q 'IRIS_26486_NO_IPOL_MONTE_CARLO_ACTIVE_PATH' \
            app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java
        python3 - app/src/main/assets/shaders/motionv2/mfsr_mgc_covariance.glsl <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); lines=p.read_text().splitlines()
for n,line in enumerate(lines,1):
    if line.count("layout(")>1:
        raise SystemExit(f"26485 runtime parser regression at {p}:{n}")
print("26485 runtime shader parser lineage PASS")
PY
    )
}

reconstruct26487 "$BASE"
pass "exact successful 26487 application source reconstructed"

# Required binary backup patch BEFORE any 26487 modification.
(
    cd "$BASE"
    git add -N app/src/main app/version.properties >/dev/null 2>&1 || true
    git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties
) > "$PREPATCH"
[[ -s "$PREPATCH" ]] || fail "26487 pre-edit exact-26487 binary patch empty"
pass "binary pre-edit exact-26487 patch created before modification"

reconstruct26487 "$CAND"
python3 "$REPO/$TRANSFORM" "$CAND"
pass "26488 temporary candidate transform PASS"

cat > "$TMP/allow.txt" <<'EOF'
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java
app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl
app/src/main/assets/shaders/motionv2/mfsr_26487_diag_sample.glsl
app/src/main/assets/shaders/motionv2/mfsr_26488_stage_diag.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_guide.glsl
app/src/main/assets/shaders/motionv2/mfsr_mgc_reference_gray.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_reduce4.glsl
app/src/main/assets/shaders/motionv2/mfsr_chroma_guide.glsl
app/src/main/assets/shaders/motionv2/mfsr_finalize.glsl
app/src/main/assets/shaders/motionv2/mfsr_low_support_reference.glsl
app/src/main/assets/shaders/motionv2/mfsr_mgc_covariance.glsl
app/src/main/assets/shaders/motionv2/mfsr_mgc_reference_gray.glsl
EOF

# Exact changed-file allowlist relative to successful 26487.
python3 - "$BASE" "$CAND" "$TMP/allow.txt" <<'PY'
from pathlib import Path
import hashlib,sys
a,b=Path(sys.argv[1]),Path(sys.argv[2]); allow=set(Path(sys.argv[3]).read_text().splitlines())
def h(root):
    d={}
    for p in (root/"app/src/main").rglob("*"):
        if p.is_file():
            rel=str(p.relative_to(root)).replace("\\","/")
            d[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
    return d
x,y=h(a),h(b); changed={k for k in x.keys()|y.keys() if x.get(k)!=y.get(k)}
if changed!=allow:
    raise SystemExit("26488 changed-file allowlist mismatch changed="+repr(sorted(changed))+" expected="+repr(sorted(allow)))
print("26488 exact changed-file allowlist PASS")
PY

# Byte-protect every successful-26487 source file not intentionally changed.
python3 - "$BASE" "$CAND" "$TMP/allow.txt" <<'PY'
from pathlib import Path
import hashlib,sys
a,b=Path(sys.argv[1]),Path(sys.argv[2]); allow=set(Path(sys.argv[3]).read_text().splitlines())
for p in (a/"app/src/main").rglob("*"):
    if not p.is_file(): continue
    rel=str(p.relative_to(a)).replace("\\","/")
    if rel in allow: continue
    q=b/rel
    if not q.is_file() or hashlib.sha256(p.read_bytes()).digest()!=hashlib.sha256(q.read_bytes()).digest():
        raise SystemExit("protected successful-26487 source changed: "+rel)
print("protected successful-26487 source hashes PASS")
PY

# No new whitespace damage: compare successful 26487 directly to 26487.
# git diff --no-index returns 1 merely because files differ, so fail only when
# --check actually emits a whitespace diagnostic.
set +e
iris26488_ws_out="$(git diff --no-index --check "$BASE/app/src/main" "$CAND/app/src/main" 2>&1)"
iris26488_ws_rc=$?
set -e
[[ "$iris26488_ws_rc" -eq 0 || "$iris26488_ws_rc" -eq 1 ]] \
    || fail "26488 scoped diff command failed rc=$iris26488_ws_rc"
[[ -z "$iris26488_ws_out" ]] || { echo "$iris26488_ws_out" >&2; fail "26488 new whitespace damage"; }
pass "scoped 26487-to-26488 whitespace/diff check"

CAP="$CAND/app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java"
BATCH="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java"
SAVER="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java"
DEFAULT="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/DefaultSaver.java"
HDRX="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java"
GLP="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLProg.java"
WR="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java"
CR="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"
SD="$CAND/app/src/main/assets/shaders/motionv2"
ACC="$SD/direct_rgb_accumulate.glsl"
REFADD="$SD/mfsr_low_support_reference.glsl"
FINAL="$SD/mfsr_finalize.glsl"
SHORT="$SD/short_highlight_recover.glsl"

# Preserve successful 26487 pre-shutter ZSL / single-job latency ownership and require the
# complete 26488 native-RAW MergeRgb + rejection-domain producer/consumer contract.
for spec in \
"$CAP:IRIS_26486_FREEZE_BUFFER_AT_SHUTTER_NO_TOPUP_WAIT" \
"$CAP:IRIS_26486_RING_REOPEN_ONLY_AFTER_IMMUTABLE_BATCH" \
"$CAP:IRIS_26486_NONBLOCKING_SHORT_HIGHLIGHT_TICKET" \
"$CAP:IRIS_26487_SINGLE_ACTIVE_MOTION_PROCESSING_NO_BACKLOG" \
"$BATCH:IRIS_26486_ASYNC_SHORT_HIGHLIGHT_SLOT" \
"$SAVER:IRIS_26486_MOTIONBATCH_DIRECT_SAVER_HANDOFF" \
"$DEFAULT:IRIS_26486_DEFAULTSAVER_MOTIONBATCH_SOLE_OWNER" \
"$HDRX:IRIS_26486_HDRX_MOTIONBATCH_ENTRY" \
"$GLP:IRIS_26487_MOTION_DEFERRED_GPU_SUBMISSION" \
"$WR:IRIS_26487_WRONSKI_DEFERRED_GPU_CHAIN_NO_PER_DISPATCH_FINISH" \
"$CR:IRIS_26488_NATIVE_RAW_MGC_PRODUCERS" \
"$CR:IRIS_26488_RECON_DIAGNOSTICS" \
"$CR:IRIS_26488_TINY_DIAGNOSTICS_BEFORE_SINGLE_GPU_DRAIN" \
"$ACC:IRIS_26488_BJZHOU_NATIVE_RAW_MERGERGB_NO_BLANKET_CENSOR" \
"$ACC:IRIS_26488_BJZHOU_HIGHLIGHT_CALCULATION_DOMAIN_CAMERA_FINALIZE_ONCE" \
"$REFADD:IRIS_26488_REFERENCE_NATIVE_RAW_MERGERGB_IDENTITY_WEIGHT" \
"$FINAL:IRIS_26488_BJZHOU_RGB_NORMALIZE_LSC_CAMERA_DOMAIN" \
"$SD/mfsr_bjzhou_guide.glsl:IRIS_26488_BJZHOU_NATIVE_RAW_GUIDE_EXACT_STRUCTURE" \
"$SD/mfsr_mgc_covariance.glsl:IRIS_26488_BJZHOU_NATIVE_RAW_COVARIANCE_EXACT_GEOMETRY" \
"$SD/mfsr_chroma_guide.glsl:IRIS_26488_BJZHOU_NATIVE_RAW_EDGE_DIRECTED_CHROMA_GUIDE" \
"$SD/mfsr_mgc_reference_gray.glsl:IRIS_26488_BJZHOU_RAW16_TO_GRAY_HALIDE_CONTRACT" \
"$SD/mfsr_bjzhou_rejection_reduce4.glsl:IRIS_26488_BJZHOU_REJECTION_DOWNSAMPLE_NATIVE_GRAY_EXACT" \
"$SD/mfsr_26488_stage_diag.glsl:IRIS_26488_SMALL_PER_FRAME_REJECTION_CONTRACT_ATLAS" \
"$SD/mfsr_bjzhou_rejection_base.glsl:IRIS_26487_BJZHOU_REJECTION_EXACT_EQUATION" \
"$SD/mfsr_bjzhou_rejection_dilate.glsl:IRIS_26487_BJZHOU_DILATE_MASK_EXACT"
do
    f="${spec%%:*}"; m="${spec#*:}"
    grep -q "$m" "$f" || fail "missing required marker $m"
done
pass "26487 ZSL/latency ownership preserved + 26488 full MergeRgb/rejection contracts present"

python3 - "$CAP" "$BATCH" "$SAVER" "$DEFAULT" "$HDRX" "$GLP" "$WR" "$CR" "$SD" <<'PY'
from pathlib import Path
import re,sys
cap,batch,saver,default,hdrx,glp,wr,recon=[Path(x).read_text() for x in sys.argv[1:9]]
sd=Path(sys.argv[9])
def text(n): return (sd/n).read_text()
def compact(s): return re.sub(r"\s+","",s)

# Capture/latency ownership is protected from tested 26487.
start=cap.index("    private void triggerZslCapture() {")
end=cap.index("    private void captureStillPicture()",start)
body=cap[start:end]
if "CaptureController.isProcessing" in body: raise SystemExit("Motion shutter regressed to global processing wait")
if "pollMotionTopUp();" in body: raise SystemExit("Motion shutter regressed to post-press normal-frame top-up")
if "IRIS_26486_FREEZE_BUFFER_AT_SHUTTER_NO_TOPUP_WAIT" not in body: raise SystemExit("pre-shutter freeze owner lost")
if "IRIS_26486_RING_REOPEN_ONLY_AFTER_IMMUTABLE_BATCH" not in body: raise SystemExit("ring reopen owner lost")
if body.index("IRIS_26486_RING_REOPEN_ONLY_AFTER_IMMUTABLE_BATCH") > body.index("processExecutor.execute(() ->"):
    raise SystemExit("rolling RAW ring does not reopen before processing starts")
if "MOTION_26486_MAX_INFLIGHT_BATCHES = 1" not in cap or "MOTION_26486_MAX_INFLIGHT_BATCHES = 2" in cap:
    raise SystemExit("single active Motion processing / zero backlog contract lost")
legacy=re.search(r"public void computeAuto\(Point size, int z\) \{(.*?)\n    \}",glp,re.S)
deferred=re.search(r"public void computeAutoDeferred\(Point size, int z\) \{(.*?)\n    \}",glp,re.S)
finisher=re.search(r"public long finishDeferredCompute\(String label\) \{(.*?)\n    \}",glp,re.S)
if not legacy or "glFinish();" not in legacy.group(1): raise SystemExit("shared legacy computeAuto changed")
if not deferred or "glFinish();" in deferred.group(1) or "GL_ALL_BARRIER_BITS" not in deferred.group(1):
    raise SystemExit("Motion deferred dispatch contract invalid")
if not finisher or finisher.group(1).count("glFinish();")!=1: raise SystemExit("explicit deferred GPU finisher invalid")
if "glProg.computeAuto(" in wr or "glProg.computeAuto(" in recon: raise SystemExit("blocking computeAuto survived active Motion path")
if recon.count('finishDeferredCompute(')!=1 or recon.count('finishDeferredCompute("MotionV2 final image")')!=1:
    raise SystemExit("26488 must have exactly one Motion GPU completion wait")
if "IRIS_26488_TINY_DIAGNOSTICS_BEFORE_SINGLE_GPU_DRAIN" not in recon:
    raise SystemExit("tiny diagnostics are not queued before the one GPU drain")
if "mfsr_support_downsample" in recon: raise SystemExit("full-resolution support readback survived")
if "fullResolutionReadback=false" not in recon: raise SystemExit("no-full-resolution diagnostic assertion missing")

# Complete normal-image producer/consumer contract.
direct=text("direct_rgb_accumulate.glsl");ref=text("mfsr_low_support_reference.glsl")
final=text("mfsr_finalize.glsl");guide=text("mfsr_bjzhou_guide.glsl")
cov=text("mfsr_mgc_covariance.glsl");chroma=text("mfsr_chroma_guide.glsl")
gray=text("mfsr_mgc_reference_gray.glsl");reduce4=text("mfsr_bjzhou_rejection_reduce4.glsl")
unblock=text("mfsr_bjzhou_unblocker.glsl");rej=text("mfsr_bjzhou_rejection_base.glsl")
gh=text("mfsr_bjzhou_clipped_gaussian_h.glsl");gv=text("mfsr_bjzhou_clipped_gaussian_v.glsl")
bil=text("mfsr_bjzhou_rejection_bilateral.glsl");post=text("mfsr_bjzhou_rejection_postprocess.glsl")
dil=text("mfsr_bjzhou_rejection_dilate.glsl");stage=text("mfsr_26488_stage_diag.glsl")
diag=text("mfsr_26487_diag_sample.glsl")

for name,t in (("direct",direct),("reference",ref)):
    for forbidden in ("sharedClipValidity","validSite","censoredOpponent"):
        if forbidden in t: raise SystemExit(f"{name} retained blanket opponent censor {forbidden}")
    if "uniform highp usampler2D rawTexture" not in t or "sensorNormalizedAt" not in t:
        raise SystemExit(f"{name} is not native R16UI RAW authority")
    if "smoothstep(highlightClipThreshold, 1.0, sensor)" not in t:
        raise SystemExit(f"{name} missing genuinely-clipped-site 0.985 soft repair")
    if "calculationFallback" not in t or "/ targetWb" in t:
        raise SystemExit(f"{name} highlight repair left the WB calculation domain early")
if "float opponent = highlightCalculationSampleAt(p) - localGreen" not in direct:
    raise SystemExit("native R-G/B-G semantic observation missing")
if "imageStore(outNumerator, p, numerator)" not in direct or "imageStore(outDenominator, p, denominator)" not in direct or "imageStore(outFrameSupport, p, support)" not in direct:
    raise SystemExit("OOB/invalid direct MergeRgb path does not preserve ping-pong state")

cf=compact(final)
if "den.y>1e-10?num.y/den.y:0.0" not in cf or "den.z>1e-10?num.z/den.z:0.0" not in cf:
    raise SystemExit("independent opponent denominator normalization missing")
if "lensShadingMap" not in final or "0.5*(shading.g+shading.b)" not in cf:
    raise SystemExit("Camera2 four-channel lens shading normalizer missing")
if "wbRgb/vec3(max(wbR,1e-6),max(wbG,1e-6),max(wbB,1e-6))" not in cf:
    raise SystemExit("calculation WB is not removed exactly once at final RGB")

for name,t in (("MGC guide",guide),("covariance",cov),("chroma guide",chroma)):
    if "rawTexture" not in t: raise SystemExit(name+" did not move to native RAW")
if "inputCfa" in guide or "inputCfa" in cov: raise SystemExit("FLOAT16 CFA still owns native MGC guide/covariance")
if "referenceGray" not in reduce4 or "/ 16383.0" not in reduce4:
    raise SystemExit("rejection reduce4 does not consume exact Raw16ToGray scale")
if "layout(r32ui,binding=0)" not in gray:
    raise SystemExit("reference-gray compute output is not GLES-safe r32ui")
if "iris26488ReferenceGray = new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.UNSIGNED_32,1)" not in recon:
    raise SystemExit("reference-gray Java texture is not matching R32UI/UNSIGNED_32")
if "iris26488ReferenceGray = new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.UNSIGNED_16,1)" in recon:
    raise SystemExit("illegal 26488 R16UI image-store carrier survived")
if "32767.0" not in gray or "0.25" not in gray or "0.5" not in gray:
    raise SystemExit("Raw16ToGray clamp/filter contract incomplete")
if "uniform float gain;" not in gray or "uniform vec4 blackLevel;" not in gray:
    raise SystemExit("Raw16ToGray exposure/black calibration missing")

# Recovered bjzhou rejection equations/constants remain intact.
cr=compact(rej); cgh=compact(gh); cgv=compact(gv); cpost=compact(post); cdil=compact(dil); cunblock=compact(unblock); cbil=compact(bil)
if "diffSq=max(diff*diff-combined,vec3(0.0))" not in cr or "combined=max(refNoise+curNoise" not in cr:
    raise SystemExit("combined Camera2 noise subtraction missing from rejection")
if "0.07*dot(diffSq" not in cr or "0.35*diffSq.g" not in cr or "25.0*minimumVariance" not in cr or "boost=6.0" not in cr:
    raise SystemExit("recovered rejection constants changed")
if "K[20]" not in gh or "K[20]" not in gv or "min(at(p),f)" not in cgh or "min(at(p),f)" not in cgv:
    raise SystemExit("20-tap clipped Gaussian contract changed")
if "150.0/255.0" not in cpost or "3.0/255.0" not in cpost:
    raise SystemExit("rejection postprocess thresholds changed")
if "r=(r-0.2)*0.5" not in cdil or cdil.count("sampleCoord(") < 10:
    raise SystemExit("factored 5x5 rejection dilation changed")
if "greenShot" not in unblock or "greenRead" not in unblock or "preVar-4.0*predicted" not in cunblock or "128.0/9.0" not in cunblock:
    raise SystemExit("unblocker recovered variance/noise math changed")
if "0.00005" not in bil or "0.025" not in bil or "2.0*4.0*4.0" not in cbil or "dy=-3" not in cbil or "dx=-3" not in cbil:
    raise SystemExit("bilateral rejection constants changed")

# Diagnostics are observational only and are small enough not to reintroduce latency stalls.
if "IRIS_26488_SMALL_PER_FRAME_REJECTION_CONTRACT_ATLAS" not in stage or "diagSize" not in stage:
    raise SystemExit("per-stage rejection atlas missing")
if "IRIS_26488_TINY_RUNTIME_SUPPORT_AND_DENOMINATOR_DIAGNOSTICS" not in diag:
    raise SystemExit("support/denominator coarse diagnostic missing")
if "new Point(24,18)" not in recon or "new Point(48,36)" not in recon:
    raise SystemExit("bounded diagnostic grid sizes changed")

print("26488 full native-RAW MergeRgb + exact rejection-domain + ZSL/latency invariants PASS")
PY

# Java lexical/delimiter proof for every touched Java owner.
python3 - "$CAP" "$BATCH" "$SAVER" "$DEFAULT" "$HDRX" "$GLP" "$WR" "$CR" <<'PY'
from pathlib import Path
import sys
def code_only(src):
    out=[];i=0;n=len(src);state="code"
    while i<n:
        if state=="code":
            if src.startswith("//",i): state="line";out.extend("  ");i+=2;continue
            if src.startswith("/*",i): state="block";out.extend("  ");i+=2;continue
            if src.startswith('"""',i): state="text";out.extend("   ");i+=3;continue
            c=src[i]
            if c=='"': state="string";out.append(" ");i+=1;continue
            if c=="'": state="char";out.append(" ");i+=1;continue
            out.append(c);i+=1;continue
        if state=="line":
            c=src[i];out.append("\n" if c=="\n" else " ");i+=1
            if c=="\n": state="code"
            continue
        if state=="block":
            if src.startswith("*/",i): out.extend("  ");i+=2;state="code";continue
            out.append("\n" if src[i]=="\n" else " ");i+=1;continue
        if state=="text":
            if src.startswith('"""',i): out.extend("   ");i+=3;state="code";continue
            out.append("\n" if src[i]=="\n" else " ");i+=1;continue
        c=src[i]
        if c=="\\":
            out.append(" ");i+=1
            if i<n: out.append("\n" if src[i]=="\n" else " ");i+=1
            continue
        out.append("\n" if c=="\n" else " ");i+=1
        if (state=="string" and c=='"') or (state=="char" and c=="'"): state="code"
    if state in ("block","string","char","text"): raise SystemExit("unterminated Java lexical state "+state)
    return "".join(out)
for path in sys.argv[1:]:
    code=code_only(Path(path).read_text());stack=[];pairs={"}":"{",")":"(","]":"["};line=1
    for c in code:
        if c=="\n":line+=1;continue
        if c in "{([":stack.append((c,line))
        elif c in "})]":
            if not stack or stack[-1][0]!=pairs[c]:raise SystemExit(f"Java delimiter mismatch {path} line={line}")
            stack.pop()
    if stack:raise SystemExit(f"Java unclosed delimiter {path} {stack[-1]}")
    print("Java lexical structure PASS",Path(path).name)
PY

# Compile every Motion compute shader actually loaded by the active reconstruction + Wronski
# Java owners. The source-to-list coverage gate below prevents future runtime shaders from
# escaping GLSL / Photon getLayouts / Adreno validation.
cat > "$TMP/shaders.txt" <<'EOF'
app/src/main/assets/shaders/motionv2/alignment_guide.glsl
app/src/main/assets/shaders/motionv2/cfa_reconstruct_accumulate.glsl
app/src/main/assets/shaders/motionv2/cfa_reconstruct_init.glsl
app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl
app/src/main/assets/shaders/motionv2/direct_rgb_init.glsl
app/src/main/assets/shaders/motionv2/mfsr_26487_diag_sample.glsl
app/src/main/assets/shaders/motionv2/mfsr_26488_stage_diag.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_clipped_gaussian_h.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_clipped_gaussian_v.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_guide.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_base.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_bilateral.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_dilate.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_postprocess.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_reduce4.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_unblocker.glsl
app/src/main/assets/shaders/motionv2/mfsr_chroma_guide.glsl
app/src/main/assets/shaders/motionv2/mfsr_finalize.glsl
app/src/main/assets/shaders/motionv2/mfsr_flow_expand.glsl
app/src/main/assets/shaders/motionv2/mfsr_ica_reference_gradient.glsl
app/src/main/assets/shaders/motionv2/mfsr_ica_reference_hessian.glsl
app/src/main/assets/shaders/motionv2/mfsr_lk_refine_level.glsl
app/src/main/assets/shaders/motionv2/mfsr_lk_select_candidate.glsl
app/src/main/assets/shaders/motionv2/mfsr_low_support_reference.glsl
app/src/main/assets/shaders/motionv2/mfsr_mgc_covariance.glsl
app/src/main/assets/shaders/motionv2/mfsr_mgc_reference_gray.glsl
app/src/main/assets/shaders/motionv2/mfsr_pyramid_gaussian.glsl
app/src/main/assets/shaders/motionv2/mfsr_wb_cfa.glsl
app/src/main/assets/shaders/motionv2/raw_to_cfa.glsl
app/src/main/assets/shaders/motionv2/short_highlight_recover.glsl
EOF
# Ensure every Motion shader loaded by the active reconstruction/Wronski classes is in the gate.
python3 - "$CR" "$WR" "$TMP/shaders.txt" <<'PY'
from pathlib import Path
import re,sys
java="\n".join(Path(p).read_text() for p in sys.argv[1:3])
loaded={m+".glsl" for m in re.findall(r'useAssetProgram\(\"motionv2/([^\"]+)',java)}
listed={Path(x).name for x in Path(sys.argv[3]).read_text().splitlines() if x.strip()}
missing=sorted(loaded-listed)
extra=sorted(listed-loaded)
if missing: raise SystemExit("active Motion shaders missing from compiler gate: "+repr(missing))
if extra: raise SystemExit("shader gate has stale/non-active entries: "+repr(extra))
print(f"26488 active Motion shader coverage PASS count={len(loaded)}")
PY

# Every uniform/image/sampler declared by every literal active Motion program invocation must be
# supplied by Java after selecting that program. This catches compile-clean runtime omissions.
python3 - "$CAND" "$CR" "$WR" <<'PY'
from pathlib import Path
import re,sys
root=Path(sys.argv[1]); java="\n".join(Path(p).read_text() for p in sys.argv[2:4])
call_re=re.compile(r'useAssetProgram\(\s*"motionv2/([^"]+)"\s*,\s*true\s*\)')
calls=list(call_re.finditer(java)); problems=[]
for index,match in enumerate(calls):
    name=match.group(1); shader=root/f"app/src/main/assets/shaders/motionv2/{name}.glsl"
    if not shader.is_file(): continue
    segment=java[match.end():(calls[index+1].start() if index+1<len(calls) else len(java))]
    source=re.sub(r'/\*.*?\*/','',shader.read_text(),flags=re.S)
    source=re.sub(r'//.*','',source)
    uniforms=[m.group(1) for m in re.finditer(
        r'\buniform\s+(?:highp\s+|mediump\s+|lowp\s+)?(?:readonly\s+|writeonly\s+)?'
        r'(?:[A-Za-z_][A-Za-z0-9_]*\s+)+([A-Za-z_][A-Za-z0-9_]*)\s*(?:\[[^;]*\])?\s*;',
        source)]
    supplied=set(re.findall(r'(?:setVar|setTexture|setTextureCompute)\(\s*"([^"]+)"',segment))
    missing=[u for u in uniforms if u not in supplied]
    if missing: problems.append((name,missing))
if problems: raise SystemExit("active Motion shader uniforms not supplied by Java: "+repr(problems))
print(f"26488 active Motion shader uniform/binding coverage PASS invocations={len(calls)}")
PY

python3 - "$CAND" "$TMP/shaders.txt" "$TRANSFORM" <<'PY'
from pathlib import Path
import importlib.util,sys
root=Path(sys.argv[1]); listing=Path(sys.argv[2]); transform=Path(sys.argv[3])
spec=importlib.util.spec_from_file_location("iris26488_transform_runtime",transform)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
shaders={rel:(root/rel).read_text() for rel in listing.read_text().splitlines()}
m.validate_photon_runtime_layout_parser(shaders)
PY

# A standard GLSL compiler catches reserved keywords, but run the same lexical gate
# before glslang so the failure names the exact identifier/file/line. This covers the
# prior Photon failures involving sample/common/coherent/precision and the rest of the
# GLSL/GLSL-ES reserved namespace, including function parameters and locals.
python3 - "$CAND" "$TMP/shaders.txt" "$TRANSFORM" <<'PY'
from pathlib import Path
import importlib.util,sys
root=Path(sys.argv[1]); listing=Path(sys.argv[2]); transform=Path(sys.argv[3])
spec=importlib.util.spec_from_file_location("iris26488_transform",transform)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
shaders={rel:(root/rel).read_text() for rel in listing.read_text().splitlines()}
m.validate_glsl_reserved_identifiers(shaders)
m.validate_gles_image_store_formats(shaders)
PY
pass "complete 26488 shader graph reserved-identifier + GLES image-format PASS"

: > "$SHADERLOG"
compile_shader(){
    local f="$1" n
    n="$(basename "$f")"
    python3 - "$f" "$TMP/$n.comp" <<'PY'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text()
needle="#define LAYOUT //\nLAYOUT"
if needle not in s: raise SystemExit("missing Photon LAYOUT header")
s=s.replace(needle,"#version 310 es\nlayout(local_size_x=8,local_size_y=8,local_size_z=1) in;",1)
Path(sys.argv[2]).write_text(s)
PY
    glslangValidator -S comp "$TMP/$n.comp" >> "$SHADERLOG" 2>&1
}
shader_fail=0
while IFS= read -r rel; do
    if compile_shader "$CAND/$rel"; then
        echo "GLSL compile PASS $(basename "$rel")" >> "$SHADERLOG"
    else
        echo "GLSL compile FAIL $(basename "$rel")" >> "$SHADERLOG"; shader_fail=1
    fi
done < "$TMP/shaders.txt"
if [[ "$shader_fail" -ne 0 ]]; then cat "$SHADERLOG"; fail "one or more 26488 shaders failed glslangValidator"; fi
pass "complete 26488 shader graph glslangValidator PASS"

while IFS= read -r rel; do
    f="$CAND/$rel"
    ! grep -Eq 'layout\((rg32f|rg16f|r16f|r16ui|rg16ui)[^)]*\)[^;]*(u?image2D|iimage2D)' "$f" \
        || fail "GLES/Adreno hazardous writable image format $(basename "$f")"
    ! grep -Eq '\b(float|vec[234]|int|ivec[234]|uint|uvec[234]|bool|mat[234])\s+(sample|common|coherent|precision)\b' "$f" \
        || fail "reserved GLSL identifier declaration in $(basename "$f")"
done < "$TMP/shaders.txt"
pass "Adreno runtime-portability guards"

# Exact 26488 functional delta relative to successful 26487 BEFORE version bump.
# git add -N is required so the two newly-created 26488 shaders are included in the delta.
(
    cd "$CAND"
    git add -N app/src/main >/dev/null 2>&1 || true
    git diff --binary -- app/src/main
) > "$DELTAOUT"
[[ -s "$DELTAOUT" ]] || fail "26488 functional delta empty"

# Version increment + candidate build proof.
bump "$CAND/app/version.properties" 0.9726487 26487 0.9726488 26488

python3 - "$CAND" "$TMP/candidate_prebuild.sha256" <<'PY'
from pathlib import Path
import hashlib,sys
root=Path(sys.argv[1]);out=Path(sys.argv[2]);ignore={"app/src/main/cpp/deps/archive.h","app/src/main/cpp/deps/archive_entry.h","app/src/main/cpp/deps/technicallyflac.h","app/src/main/cpp/deps/tiny_dng_writer.h"};rows=[]
for p in (root/"app/src/main").rglob("*"):
    if p.is_file():
        rel=str(p.relative_to(root)).replace("\\","/")
        if rel in ignore:continue
        rows.append((rel,hashlib.sha256(p.read_bytes()).hexdigest()))
vp=root/"app/version.properties";rows.append(("app/version.properties",hashlib.sha256(vp.read_bytes()).hexdigest()))
out.write_text("".join(f"{h}  {r}\n" for r,h in sorted(rows)))
PY

(
    cd "$CAND"
    chmod +x gradlew
    ./gradlew assembleDebug --no-daemon --stacktrace
) 2>&1 | tee "$CANDLOG"
[[ "${PIPESTATUS[0]}" -eq 0 ]] || fail "temporary 26488 candidate Gradle build"
(
    cd "$CAND"
    sha256sum -c "$TMP/candidate_prebuild.sha256" >/dev/null
) || fail "temporary Gradle mutated canonical candidate source"
pass "Temporary-copy validation: PASS"
pass "PRE-BUILD SAFETY PROOF PASSED"

# FINAL BUILD: reconstruct exact successful 26487 again in the Action checkout, then overlay
# only the already-validated 26488 11-file allowlist. Version bump + APK build are one block.
git apply --check --binary "$BASE26483_PATCH"
git apply --binary "$BASE26483_PATCH"
sha256sum -c "$BASE26483_HASHES" >/dev/null
git apply --check --binary "$DELTA26484"
git apply --binary "$DELTA26484"
bump app/version.properties 0.9726483 26483 0.9726484 26484
python3 "$TRANSFORM26485" "$(pwd)"
bump app/version.properties 0.9726484 26484 0.9726485 26485
python3 "$TRANSFORM26486" "$(pwd)"
bump app/version.properties 0.9726485 26485 0.9726486 26486
python3 "$TRANSFORM26487" "$(pwd)"
bump app/version.properties 0.9726486 26486 0.9726487 26487
pass "final exact successful 26487 application graph reconstructed"

while IFS= read -r rel; do
    mkdir -p "$(dirname "$rel")"
    cp "$CAND/$rel" "$rel"
done < "$TMP/allow.txt"

{
bump app/version.properties 0.9726487 26487 0.9726488 26488

python3 - "$CAND" "$(pwd)" <<'PY'
from pathlib import Path
import hashlib,sys
a,b=Path(sys.argv[1]),Path(sys.argv[2]);ignore={"app/src/main/cpp/deps/archive.h","app/src/main/cpp/deps/archive_entry.h","app/src/main/cpp/deps/technicallyflac.h","app/src/main/cpp/deps/tiny_dng_writer.h"}
def h(root):
    d={}
    for p in (root/"app/src/main").rglob("*"):
        if p.is_file():
            rel=str(p.relative_to(root)).replace("\\","/")
            if rel in ignore:continue
            d[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
    vp=root/"app/version.properties";d["app/version.properties"]=hashlib.sha256(vp.read_bytes()).hexdigest();return d
x,y=h(a),h(b)
if x!=y:
    bad=sorted(k for k in x.keys()|y.keys() if x.get(k)!=y.get(k))
    raise SystemExit("candidate/final canonical source mismatch BEFORE final Gradle: "+repr(bad[:100]))
print("full candidate/final canonical source parity PASS")
PY

git add -N app/src/main app/version.properties >/dev/null 2>&1 || true
git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties > "$SOURCEPATCH"
[[ -s "$SOURCEPATCH" ]] || fail "complete 26488 source patch empty"

python3 - "$(pwd)" "$AFTERHASH" <<'PY'
from pathlib import Path
import hashlib,sys
root=Path(sys.argv[1]);out=Path(sys.argv[2]);ignore={"app/src/main/cpp/deps/archive.h","app/src/main/cpp/deps/archive_entry.h","app/src/main/cpp/deps/technicallyflac.h","app/src/main/cpp/deps/tiny_dng_writer.h"};rows=[]
for p in (root/"app/src/main").rglob("*"):
    if p.is_file():
        rel=str(p.relative_to(root)).replace("\\","/")
        if rel in ignore:continue
        rows.append((rel,hashlib.sha256(p.read_bytes()).hexdigest()))
vp=root/"app/version.properties";rows.append(("app/version.properties",hashlib.sha256(vp.read_bytes()).hexdigest()))
out.write_text("".join(f"{h}  {r}\n" for r,h in sorted(rows)))
PY
cp "$AFTERHASH" "$PREBUILDHASH"

chmod +x gradlew
./gradlew assembleDebug --no-daemon --stacktrace 2>&1 | tee "$FINALLOG"
}
[[ "${PIPESTATUS[0]}" -eq 0 ]] || fail "final 26488 Gradle build"
sha256sum -c "$PREBUILDHASH" >/dev/null || fail "final Gradle mutated canonical source"

mapfile -t apks < <(find app/build/outputs/apk -type f -name '*.apk' | sort)
[[ ${#apks[@]} -ge 1 ]] || fail "no APK output"
rm -f IrisCamera-0.9726488-26488-*.apk
cp "${apks[-1]}" "$APK_NAME"
[[ -s "$APK_NAME" ]] || fail "published 26488 APK missing"

mkdir -p "$OUTDIR/next_baseline_inputs"
cp "$SOURCEPATCH" "$OUTDIR/next_baseline_inputs/26488_successful_source.patch"
cp "$AFTERHASH" "$OUTDIR/next_baseline_inputs/26488_successful_after.sha256"
cp "$DELTAOUT" "$OUTDIR/next_baseline_inputs/26488_delta_from_26487.patch"
cp "$REPO/$TRANSFORM" "$OUTDIR/next_baseline_inputs/"

cat > "$REPORT" <<EOF
26488 FULL MERGERGB + REJECTION CONTRACT
Version=$NEW_VERSION
Build=$NEW_BUILD
Branch=$BRANCH
BackupBranch=$BACKUP_BRANCH
BackupExpected=$BACKUP_EXPECTED
Base26483PatchSHA=$BASE26483_PATCH_SHA
Base26483ManifestSHA=$BASE26483_HASHES_SHA
Successful26484DeltaSHA=$DELTA26484_SHA
Successful26485TransformSHA=$TRANSFORM26485_SHA
Successful26486TransformSHA=$TRANSFORM26486_SHA
Successful26487TransformSHA=$TRANSFORM26487_SHA
Transform26488SHA=$TRANSFORM_SHA
APK=$APK_NAME
APK_SHA256=$(sha "$APK_NAME")
SourcePatchSHA256=$(sha "$SOURCEPATCH")
AfterManifestSHA256=$(sha "$AFTERHASH")
Capture=successful 26487 rolling pre-shutter RAW ring preserved byte-for-byte; shutter freezes already-buffered normal frames; no top-up wait; ring reopens before processing; one active Motion batch and zero processing backlog
Latency=successful 26487 Motion-only deferred GPU chain preserved; 26488 queues all 24x18 stage and 48x36 support/denominator diagnostics before the same single final GPU drain; no per-frame CPU readback and no second diagnostic glFinish
MergeRgb=native R16UI RAW is authoritative for normal RGB evidence; exact phase black/white/exposure/WB calculation calibration; edge-directed green; covariance precision kernel; R-G/B-G semantic accumulation; independent denominators; no blanket whole-quad opponent censor
Highlight=color-only genuinely-clipped-site repair begins at physical sensor normalized 0.985; cubic opposed-channel estimate stays in WB calculation domain; repaired values never feed temporal rejection/validity; finalizer removes calculation WB once
MGCProducers=guide, covariance and chroma guide all consume native R16UI calibration rather than FLOAT16 CFA color authority; Wronski FLOAT16 WB CFA remains alignment-only
Rejection=reference luma now uses recovered Raw16ToGray contract: per-phase black subtraction, reference exposure gain, equal CFA average, separable 1:2:1 filter, R16UI 0..32767 and reduce4 /16383; recovered rejection/noise/Gaussian/bilateral/postprocess/dilation constants protected
LensShading=Camera2 four-channel gain map applied in linear semantic RGB normalizer as R, average(Gr,Gb), B before one calculation-WB removal; identity map if unavailable
Diagnostics=per-aux 24x18 atlases report flow variation/interpolation-cancel/unblocker/initial rejection, pixelDifference/postRejection/finalWeight/initial accept, and physical 0.985 R/G/B/quad clipping; 48x36 report actual frame support and G/RG/BG denominators
NumericalGate=model-only equation smoke test must remain high-support and is explicitly NOT claimed as proof of phone effective-frame count; phone stage telemetry is authoritative
BuildSafety=exact tested 26487 reconstruction, exact backup proof, binary pre-edit patch before 26488 transform, strict 11-file allowlist, all other tested-26487 app source protected, Java lexical, exact Photon getLayouts simulation, full GLSL reserved-word scan, GLES 3.1 image-format whitelist, glslang full graph, Adreno guards, temporary Gradle, candidate/final source parity, and version increment + final Gradle in one guarded block
EOF
sha256sum "$APK_NAME" "$SOURCEPATCH" "$AFTERHASH" "$REPORT" "$DELTAOUT" \
    > "$OUTDIR/26488_artifact_hashes.sha256"

pass "26488 canonical checkpoint package created"
echo "26488_SOURCE_PATCH_SHA256=$(sha "$SOURCEPATCH")"
echo "26488_AFTER_MANIFEST_SHA256=$(sha "$AFTERHASH")"
echo "26488 BUILD SUCCESS"
