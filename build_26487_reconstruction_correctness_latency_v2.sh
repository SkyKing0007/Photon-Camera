#!/usr/bin/env bash
set -euo pipefail

EXPECTED_BRANCH="experimental-clean-photon-rebuild"
EXPECTED_APP_BASE="8233415edf738bf35c0fe1c4907f5dfe51de31a4"
BACKUP_BRANCH="backup-26486-success-before-26487-full-reconstruction-correctness"
BACKUP_EXPECTED="c7b606fde114dd56955fe16f342c3a93740c69a2"

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
TRANSFORM="transform_26487_reconstruction_correctness_latency_v2.py"
TRANSFORM_SHA="3e6413d3711e3fb570c0514cffd6bae6bad6e6864cf68de9b3df388ef6238654"

NEW_VERSION="0.9726487"
NEW_BUILD="26487"
OUTDIR="build_26487_outputs"
APK_NAME="IrisCamera-${NEW_VERSION}-${NEW_BUILD}-reconstruction-correctness-latency-debug.apk"

fail(){ echo "FAIL: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }

REPO="$(pwd)"
rm -rf "$OUTDIR"
mkdir -p "$OUTDIR"
AUDIT="$OUTDIR/26487_source_audit.txt"
CANDLOG="$OUTDIR/26487_temporary_candidate_build.log"
FINALLOG="$OUTDIR/26487_final_build.log"
SHADERLOG="$OUTDIR/26487_shader_validation.txt"
REPORT="$OUTDIR/26487_build_report.txt"
PREPATCH="$OUTDIR/26487_pre_edit_exact_26486_binary.patch"
DELTAOUT="$OUTDIR/26487_delta_from_26486.patch"
SOURCEPATCH="$OUTDIR/26487_source.patch"
AFTERHASH="$OUTDIR/26487_after.sha256"
PREBUILDHASH="$OUTDIR/26487_prebuild_canonical.sha256"

exec > >(tee "$AUDIT") 2>&1
echo "=== 26487 RECONSTRUCTION CORRECTNESS + BOUNDED LATENCY V2 ==="
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
"$TRANSFORM:$TRANSFORM_SHA"
do
    f="${spec%%:*}"; expected="${spec#*:}"
    [[ -f "$f" ]] || fail "missing infrastructure input $f"
    [[ "$(sha "$f")" == "$expected" ]] || fail "identity mismatch $f"
done
python3 -m py_compile "$TRANSFORM26485" "$TRANSFORM26486" "$TRANSFORM"
python3 "$TRANSFORM" --self-test
bash -n "$0"
pass "infrastructure syntax and identity"

# Hard pre-modification backup proof. No app transform/overlay occurs before this.
remote="$(git ls-remote origin "refs/heads/$BACKUP_BRANCH" | awk '{print $1}')"
[[ "$remote" == "$BACKUP_EXPECTED" ]] \
    || fail "backup branch $BACKUP_BRANCH=$remote expected=$BACKUP_EXPECTED"
pass "backup branch exact successful 26486 checkpoint"

TMP="$(mktemp -d)"
BASE="$TMP/base26486"
CAND="$TMP/candidate26487"
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

# Reconstruct the exact successful 26486 APPLICATION source by the same proven
# composition used by builds 26485/26486:
# protected base -> exact 26483 -> exact 26484 -> exact 26485 -> exact 26486.
# Infrastructure commits themselves intentionally never alter app/src/main.
reconstruct26486(){
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

        grep -q '^VERSION_NAME=0\.9726486$' app/version.properties
        grep -q '^VERSION_BUILD=26486$' app/version.properties
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

reconstruct26486 "$BASE"
pass "exact successful 26486 application source reconstructed"

# Required binary backup patch BEFORE any 26487 modification.
(
    cd "$BASE"
    git add -N app/src/main app/version.properties >/dev/null 2>&1 || true
    git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties
) > "$PREPATCH"
[[ -s "$PREPATCH" ]] || fail "26487 pre-edit exact-26486 binary patch empty"
pass "binary pre-edit exact-26486 patch created before modification"

reconstruct26486 "$CAND"
python3 "$REPO/$TRANSFORM" "$CAND"
pass "26487 temporary candidate transform PASS"

cat > "$TMP/allow.txt" <<'EOF'
app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLProg.java
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java
app/src/main/assets/shaders/motionv2/mfsr_wb_cfa.glsl
app/src/main/assets/shaders/motionv2/mfsr_mgc_covariance.glsl
app/src/main/assets/shaders/motionv2/mfsr_chroma_guide.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_guide.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_unblocker.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_base.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_clipped_gaussian_h.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_clipped_gaussian_v.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_reduce4.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_bilateral.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_postprocess.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_dilate.glsl
app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl
app/src/main/assets/shaders/motionv2/mfsr_low_support_reference.glsl
app/src/main/assets/shaders/motionv2/mfsr_finalize.glsl
app/src/main/assets/shaders/motionv2/short_highlight_recover.glsl
app/src/main/assets/shaders/motionv2/mfsr_26487_diag_sample.glsl
EOF

# Exact changed-file allowlist relative to successful 26486.
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
    raise SystemExit("26487 changed-file allowlist mismatch changed="+repr(sorted(changed))+" expected="+repr(sorted(allow)))
print("26487 exact changed-file allowlist PASS")
PY

# Byte-protect every successful-26486 source file not intentionally changed.
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
        raise SystemExit("protected successful-26486 source changed: "+rel)
print("protected successful-26486 source hashes PASS")
PY

# No new whitespace damage: compare successful 26486 directly to 26487.
# git diff --no-index returns 1 merely because files differ, so fail only when
# --check actually emits a whitespace diagnostic.
set +e
iris26487_ws_out="$(git diff --no-index --check "$BASE/app/src/main" "$CAND/app/src/main" 2>&1)"
iris26487_ws_rc=$?
set -e
[[ "$iris26487_ws_rc" -eq 0 || "$iris26487_ws_rc" -eq 1 ]] \
    || fail "26487 scoped diff command failed rc=$iris26487_ws_rc"
[[ -z "$iris26487_ws_out" ]] || { echo "$iris26487_ws_out" >&2; fail "26487 new whitespace damage"; }
pass "scoped 26486-to-26487 whitespace/diff check"

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

# Preserve successful 26486 pre-shutter ZSL/short ownership while intentionally changing
# only the Motion processing backlog/synchronization policy and 26487 reconstruction owners.
for spec in \
"$CAP:IRIS_26486_FREEZE_BUFFER_AT_SHUTTER_NO_TOPUP_WAIT" \
"$CAP:IRIS_26486_EXPOSURE_ENERGY_EV_GROUPING" \
"$CAP:IRIS_26486_WHOLE_GROUP_EXPOSURE_SPAN_PROOF" \
"$CAP:IRIS_26486_NONBLOCKING_SHORT_HIGHLIGHT_TICKET" \
"$CAP:IRIS_26486_BATCH_QUEUE_CAPTURE_OWNERSHIP" \
"$BATCH:IRIS_26486_ASYNC_SHORT_HIGHLIGHT_SLOT" \
"$SAVER:IRIS_26486_MOTIONBATCH_DIRECT_SAVER_HANDOFF" \
"$DEFAULT:IRIS_26486_DEFAULTSAVER_MOTIONBATCH_SOLE_OWNER" \
"$HDRX:IRIS_26486_HDRX_MOTIONBATCH_ENTRY" \
"$CR:IRIS_26487_CAMERA2_PER_CFA_NOISE_AUTHORITY" \
"$CR:IRIS_26487_RECONSTRUCTION_CORRECTNESS_BJZHOU_GRAPH" \
"$CR:IRIS_26487_RECON_DIAGNOSTICS" \
"$CR:IRIS_26487_COARSE_SUPPORT_TELEMETRY_NO_FULLRES_READBACK" \
"$CR:IRIS_26487_PROCESSING_BUDGET" \
"$GLP:IRIS_26487_MOTION_DEFERRED_GPU_SUBMISSION" \
"$WR:IRIS_26487_WRONSKI_DEFERRED_GPU_CHAIN_NO_PER_DISPATCH_FINISH" \
"$CAP:IRIS_26487_SINGLE_ACTIVE_MOTION_PROCESSING_NO_BACKLOG" \
"$ACC:IRIS_26487_CENSORED_OPPONENT_PRECISION_DIRECT_NO_OOB_LOSS" \
"$REFADD:IRIS_26487_REFERENCE_ADD_ONCE_CENSORED_OPPONENT" \
"$FINAL:IRIS_26487_OPPONENT_NORMALIZE_ONCE_NO_SUPPORT_HUE_FADE" \
"$SHORT:IRIS_26487_SHORT_SAME_PHYSICAL_CLIP_AUTHORITY" \
"$SD/mfsr_wb_cfa.glsl:IRIS_26487_SINGLE_CLIPPING_AUTHORITY_WB_ONLY" \
"$SD/mfsr_mgc_covariance.glsl:IRIS_26487_BJZHOU_COVARIANCE_EXACT_GEOMETRY" \
"$SD/mfsr_chroma_guide.glsl:IRIS_26487_PHASE_PRESERVING_CHROMA_GUIDE_BORDER" \
"$SD/mfsr_bjzhou_guide.glsl:IRIS_26487_BJZHOU_GUIDE_EXACT_STRUCTURE" \
"$SD/mfsr_bjzhou_rejection_base.glsl:IRIS_26487_BJZHOU_REJECTION_EXACT_EQUATION" \
"$SD/mfsr_bjzhou_rejection_dilate.glsl:IRIS_26487_BJZHOU_DILATE_MASK_EXACT"
do
    f="${spec%%:*}"; m="${spec#*:}"
    grep -q "$m" "$f" || fail "missing required marker $m"
done
pass "26486 pre-shutter ZSL preserved + 26487 reconstruction/latency ownership markers"

# Hard semantic invariants: source correctness + pre-shutter ZSL + bounded Motion GPU scheduling.
python3 - "$CAP" "$BATCH" "$SAVER" "$DEFAULT" "$HDRX" "$GLP" "$WR" "$CR" "$SD" <<'PY'
from pathlib import Path
import re,sys
cap,batch,saver,default,hdrx,glp,wr,recon=[Path(x).read_text() for x in sys.argv[1:9]]
sd=Path(sys.argv[9])
def text(n): return (sd/n).read_text()
start=cap.index("    private void triggerZslCapture() {")
end=cap.index("    private void captureStillPicture()",start)
body=cap[start:end]
if "CaptureController.isProcessing" in body: raise SystemExit("26487 regressed Motion shutter to global processing wait")
if "pollMotionTopUp();" in body: raise SystemExit("26487 regressed Motion shutter to normal-frame top-up wait")
if "IRIS_26486_FREEZE_BUFFER_AT_SHUTTER_NO_TOPUP_WAIT" not in body: raise SystemExit("pre-shutter freeze owner lost")
if "IRIS_26486_RING_REOPEN_ONLY_AFTER_IMMUTABLE_BATCH" not in body: raise SystemExit("ring reopen owner lost")
if body.index("IRIS_26486_RING_REOPEN_ONLY_AFTER_IMMUTABLE_BATCH") > body.index("processExecutor.execute(() ->"):
    raise SystemExit("ring does not reopen before processing starts")
if "MOTION_26486_MAX_INFLIGHT_BATCHES = 1" not in cap: raise SystemExit("single active Motion processing gate missing")
if "MOTION_26486_MAX_INFLIGHT_BATCHES = 2" in cap: raise SystemExit("two-job Motion backlog survived")
legacy=re.search(r"public void computeAuto\(Point size, int z\) \{(.*?)\n    \}",glp,re.S)
deferred=re.search(r"public void computeAutoDeferred\(Point size, int z\) \{(.*?)\n    \}",glp,re.S)
finisher=re.search(r"public long finishDeferredCompute\(String label\) \{(.*?)\n    \}",glp,re.S)
if not legacy or "glFinish();" not in legacy.group(1): raise SystemExit("legacy computeAuto changed")
if not deferred or "glFinish();" in deferred.group(1) or "GL_ALL_BARRIER_BITS" not in deferred.group(1): raise SystemExit("Motion deferred dispatch contract invalid")
if not finisher or finisher.group(1).count("glFinish();")!=1: raise SystemExit("explicit Motion GPU ownership drain invalid")
if "glProg.computeAuto(" in wr or "glProg.computeAuto(" in recon: raise SystemExit("blocking computeAuto survived active Motion path")
if wr.count("glProg.computeAutoDeferred(")<10 or recon.count("glProg.computeAutoDeferred(")<25: raise SystemExit("deferred Motion compute coverage incomplete")
if recon.count('finishDeferredCompute("MotionV2 final image")')!=1: raise SystemExit("Motion final drain count != 1")
if "mfsr_support_downsample" in recon: raise SystemExit("full-resolution support readback survived")
if "final Point iris26487DiagSize = new Point(48,36)" not in recon: raise SystemExit("48x36 support telemetry grid missing")
if "IRIS_26487_PROCESSING_BUDGET" not in recon or "targetMs=5000" not in recon: raise SystemExit("5-second budget diagnostics missing")
wb=text("mfsr_wb_cfa.glsl");cov=text("mfsr_mgc_covariance.glsl");chroma=text("mfsr_chroma_guide.glsl")
guide=text("mfsr_bjzhou_guide.glsl");unblock=text("mfsr_bjzhou_unblocker.glsl")
rej=text("mfsr_bjzhou_rejection_base.glsl");gh=text("mfsr_bjzhou_clipped_gaussian_h.glsl");gv=text("mfsr_bjzhou_clipped_gaussian_v.glsl")
reduce4=text("mfsr_bjzhou_rejection_reduce4.glsl");bil=text("mfsr_bjzhou_rejection_bilateral.glsl")
post=text("mfsr_bjzhou_rejection_postprocess.glsl");dil=text("mfsr_bjzhou_rejection_dilate.glsl")
acc=text("direct_rgb_accumulate.glsl");ref=text("mfsr_low_support_reference.glsl")
final=text("mfsr_finalize.glsl");short=text("short_highlight_recover.glsl");diag=text("mfsr_26487_diag_sample.glsl")
joined="\n".join([recon,wb,cov,chroma,guide,unblock,rej,gh,gv,reduce4,bil,post,dil,acc,ref,final,short,diag])
for bad in ("repairClipped(","opposedEstimate(","physicalClipStart","physicalClipEnd","0.94f","0.985f","rgAuthority","localReliableHue","MotionV2IpolNoiseCurve"):
    if bad in joined: raise SystemExit("stale conflicting reconstruction authority: "+bad)
if recon.count("IRIS26487_CLIP_THRESHOLD") < 5: raise SystemExit("single clipping authority not propagated")
if "0.25f*s" not in recon or "2.0f*iris26487WbNoise[1]" not in recon: raise SystemExit("two-green MGC noise math missing")
if "c0+t.z,c0-t.z,c1,t.w" not in cov: raise SystemExit("recovered covariance transform missing")
if "diffSq=max(diff*diff-combined" not in rej: raise SystemExit("combined-noise subtraction missing")
if "K[20]" not in gh or "K[20]" not in gv or "min(at(p),f)" not in gh: raise SystemExit("20-tap clipped Gaussian missing")
if "150.0/255.0" not in post or "3.0/255.0" not in post: raise SystemExit("bjzhou postprocess thresholds missing")
if "4.0*sampleCoord" not in dil: raise SystemExit("recovered dilation mapping missing")
if "exp2(-0.5*dist)+0.00005" not in acc: raise SystemExit("bjzhou RGB precision kernel missing")
if "sharedClipValidity" not in acc or "sharedClipValidity" not in ref: raise SystemExit("censored opponent support missing")
if "s.a+=oob;imageStore(outNumerator,p,n);imageStore(outDenominator,p,d);imageStore(outFrameSupport,p,s);" not in acc: raise SystemExit("OOB ping-pong state preservation missing")
if "den.y>1e-10?num.y/den.y:0.0" not in final: raise SystemExit("true opponent denominator normalization missing")
if "x/max(referenceExposureScale,1e-6)" not in short: raise SystemExit("short/reference physical clipping domain mismatch")
if "IRIS_26487_TINY_RUNTIME_RECON_DIAGNOSTICS" not in diag: raise SystemExit("coarse reconstruction diagnostics shader missing")
print("26487 reconstruction + ZSL + bounded-latency hard invariants PASS")
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

# Full shader set: existing 26484 flow/covariance/chroma owners + every new
# rejection/censored-highlight shader. This reproduces both GLSL and Photon's
# line-oriented runtime-layout parser checks before Gradle.
cat > "$TMP/shaders.txt" <<'EOF'
app/src/main/assets/shaders/motionv2/mfsr_wb_cfa.glsl
app/src/main/assets/shaders/motionv2/mfsr_mgc_covariance.glsl
app/src/main/assets/shaders/motionv2/mfsr_chroma_guide.glsl
app/src/main/assets/shaders/motionv2/mfsr_flow_expand.glsl
app/src/main/assets/shaders/motionv2/mfsr_lk_refine_level.glsl
app/src/main/assets/shaders/motionv2/mfsr_lk_select_candidate.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_guide.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_unblocker.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_base.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_clipped_gaussian_h.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_clipped_gaussian_v.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_reduce4.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_bilateral.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_postprocess.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_dilate.glsl
app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl
app/src/main/assets/shaders/motionv2/mfsr_low_support_reference.glsl
app/src/main/assets/shaders/motionv2/mfsr_finalize.glsl
app/src/main/assets/shaders/motionv2/short_highlight_recover.glsl
app/src/main/assets/shaders/motionv2/mfsr_26487_diag_sample.glsl
EOF

python3 - "$CAND" "$TMP/shaders.txt" <<'PY'
from pathlib import Path
import sys
root=Path(sys.argv[1])
for rel in Path(sys.argv[2]).read_text().splitlines():
    p=root/rel
    if not p.is_file(): raise SystemExit("missing shader "+rel)
    for n,line in enumerate(p.read_text().splitlines(),1):
        if line.count("layout(")>1:
            raise SystemExit(f"runtime layout parser hazard {rel}:{n}: {line}")
        if "layout(" in line:
            inside=line[line.find("(")+1:line.rfind(")")]
            for token in inside.split(","):
                t=token.replace(" ","")
                if t.startswith("binding="): int(t.split("=",1)[1])
print("Photon runtime layout-parser compatibility PASS for 26487 shader graph")
PY

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
if [[ "$shader_fail" -ne 0 ]]; then cat "$SHADERLOG"; fail "one or more 26487 shaders failed glslangValidator"; fi
pass "complete 26487 shader graph glslangValidator PASS"

while IFS= read -r rel; do
    f="$CAND/$rel"
    ! grep -Eq 'layout\((rg32f|rg16f|r16f)[^)]*\)[^;]*writeonly image2D' "$f" \
        || fail "Adreno hazardous writable format $(basename "$f")"
    ! grep -Eq '\b(float|vec[234]|int|ivec[234]|uint|uvec[234]|bool)\s+(sample|common|coherent)\b' "$f" \
        || fail "reserved GLSL identifier declaration in $(basename "$f")"
done < "$TMP/shaders.txt"
pass "Adreno runtime-portability guards"

# Exact 26487 functional delta relative to successful 26486 BEFORE version bump.
# git add -N is required so newly-created 26487 files are included in the delta.
(
    cd "$CAND"
    git add -N app/src/main >/dev/null 2>&1 || true
    git diff --binary -- app/src/main
) > "$DELTAOUT"
[[ -s "$DELTAOUT" ]] || fail "26487 functional delta empty"

# Version increment + candidate build proof.
bump "$CAND/app/version.properties" 0.9726486 26486 0.9726487 26487

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
[[ "${PIPESTATUS[0]}" -eq 0 ]] || fail "temporary 26487 candidate Gradle build"
(
    cd "$CAND"
    sha256sum -c "$TMP/candidate_prebuild.sha256" >/dev/null
) || fail "temporary Gradle mutated canonical candidate source"
pass "Temporary-copy validation: PASS"
pass "PRE-BUILD SAFETY PROOF PASSED"

# FINAL BUILD: reconstruct exact successful 26486 again in Action checkout, then overlay
# only the already-built 26487 allowlist. Version bump + APK build are one block.
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
pass "final exact successful 26486 application graph reconstructed"

while IFS= read -r rel; do
    mkdir -p "$(dirname "$rel")"
    cp "$CAND/$rel" "$rel"
done < "$TMP/allow.txt"

{
bump app/version.properties 0.9726486 26486 0.9726487 26487

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
[[ -s "$SOURCEPATCH" ]] || fail "complete 26487 source patch empty"

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
[[ "${PIPESTATUS[0]}" -eq 0 ]] || fail "final 26487 Gradle build"
sha256sum -c "$PREBUILDHASH" >/dev/null || fail "final Gradle mutated canonical source"

mapfile -t apks < <(find app/build/outputs/apk -type f -name '*.apk' | sort)
[[ ${#apks[@]} -ge 1 ]] || fail "no APK output"
rm -f IrisCamera-0.9726487-26487-*.apk
cp "${apks[-1]}" "$APK_NAME"
[[ -s "$APK_NAME" ]] || fail "published 26487 APK missing"

mkdir -p "$OUTDIR/next_baseline_inputs"
cp "$SOURCEPATCH" "$OUTDIR/next_baseline_inputs/26487_successful_source.patch"
cp "$AFTERHASH" "$OUTDIR/next_baseline_inputs/26487_successful_after.sha256"
cp "$DELTAOUT" "$OUTDIR/next_baseline_inputs/26487_delta_from_26486.patch"
cp "$REPO/$TRANSFORM" "$OUTDIR/next_baseline_inputs/"

cat > "$REPORT" <<EOF
26487 RECONSTRUCTION CORRECTNESS + BOUNDED LATENCY V2
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
Transform26487SHA=$TRANSFORM_SHA
APK=$APK_NAME
APK_SHA256=$(sha "$APK_NAME")
SourcePatchSHA256=$(sha "$SOURCEPATCH")
AfterManifestSHA256=$(sha "$AFTERHASH")
Capture=rolling pre-shutter RAW ring preserved; shutter freezes already-buffered normal frames with no top-up wait; ring reopens before processing; one active Motion batch, zero processing backlog
Latency=Motion-only computeAutoDeferred uses GPU memory barriers without per-dispatch glFinish; one explicit GPU drain at final CPU image ownership; 48x36 support/diagnostic readback replaces full-resolution support readback; on-device target <=5000 ms for 15 attempted frames
Noise=Camera2 SENSOR_NOISE_PROFILE retained per CFA phase; exposure/WB affine variance transformed in the comparison domain
Clipping=single physical 250/255 authority; WB is linear-only; synthetic pre-merge CFA highlight repair removed; clipped opponent samples are censored
Rejection=recovered bjzhou guide/unblocker/reverseWeight+pixelDifference/20-tap clipped-Gaussian/4x downsample/7x7 bilateral/postprocess/5x5 dilation equations
Merge=bjzhou precision matrix consumed directly; OOB ping-pong preserves prior accumulators; G/R-G/B-G normalize exactly once without support-ratio hue fade
Diagnostics=48x36 support/opponent/OOB grid + GPU drain/output readback/wall timings; attemptedFrames and effectiveSupport logged separately
NumericalGate=deterministic noise-only 15-frame model must project >14 effective support; WB/noise, clipping/censor, OOB identity, clipped-Gaussian and zero-rejection dilation identities must pass
BuildSafety=exact successful 26486 reconstruction, backup proof, binary pre-edit patch, strict 21-file allowlist, protected 26486 hashes, Java/GLSL/runtime-parser/Adreno gates, temporary Gradle, candidate/final parity, version increment + final Gradle in one guarded block
EOF

sha256sum "$APK_NAME" "$SOURCEPATCH" "$AFTERHASH" "$REPORT" "$DELTAOUT" \
    > "$OUTDIR/26487_artifact_hashes.sha256"

pass "26487 canonical checkpoint package created"
echo "26487_SOURCE_PATCH_SHA256=$(sha "$SOURCEPATCH")"
echo "26487_AFTER_MANIFEST_SHA256=$(sha "$AFTERHASH")"
echo "26487 BUILD SUCCESS"
