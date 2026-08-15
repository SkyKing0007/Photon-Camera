#!/usr/bin/env bash
set -euo pipefail

EXPECTED_BRANCH="experimental-effective-stack"
EXPECTED_APP_BASE="8233415edf738bf35c0fe1c4907f5dfe51de31a4"
BACKUP_BRANCH="backup-26485-tested-before-26486-full-bjzhou-censored-opponent-latency"
BACKUP_EXPECTED="1e7c59581c273995ea3cb3baa08e1103b2ae20e0"

BASE26483_PATCH="26483_successful_source.patch"
BASE26483_PATCH_SHA="a993c2c9e12cba8098623fab8b83f0965b9ad2016eded6fd857f55935a1c11db"
BASE26483_HASHES="26483_successful_after.sha256"
BASE26483_HASHES_SHA="7cba064adf92e6645a1f94ea44a5bd205a800cead9dcd8c392816de5f2725ca7"
DELTA26484="26484_delta_from_26483.patch"
DELTA26484_SHA="18fbb861c3c49f4ad8399f29aa60ca3e85df57ffacc794b8b6a2206b42197ac3"
TRANSFORM26485="transform_26485_runtime_shutter_full_fix_v1.py"
TRANSFORM26485_SHA="2e04a8e250d0fb64ca3e4a7763ed4943203d7f1ae740283018a7fb1b90c9a461"
TRANSFORM="transform_26486_full_bjzhou_censored_opponent_latency_v1.py"
TRANSFORM_SHA="a520de4ed11435fee2a9a43026c4513b183a9c56a5ddee44664b71fbe7ea1a65"

NEW_VERSION="0.9726486"
NEW_BUILD="26486"
OUTDIR="build_26486_outputs"
APK_NAME="IrisCamera-${NEW_VERSION}-${NEW_BUILD}-full-bjzhou-censored-opponent-latency-debug.apk"

fail(){ echo "FAIL: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }

REPO="$(pwd)"
rm -rf "$OUTDIR"
mkdir -p "$OUTDIR"
AUDIT="$OUTDIR/26486_source_audit.txt"
CANDLOG="$OUTDIR/26486_temporary_candidate_build.log"
FINALLOG="$OUTDIR/26486_final_build.log"
SHADERLOG="$OUTDIR/26486_shader_validation.txt"
REPORT="$OUTDIR/26486_build_report.txt"
PREPATCH="$OUTDIR/26486_pre_edit_exact_26485_binary.patch"
DELTAOUT="$OUTDIR/26486_delta_from_26485.patch"
SOURCEPATCH="$OUTDIR/26486_source.patch"
AFTERHASH="$OUTDIR/26486_after.sha256"
PREBUILDHASH="$OUTDIR/26486_prebuild_canonical.sha256"

exec > >(tee "$AUDIT") 2>&1
echo "=== 26486 FULL BJZHOU CENSORED OPPONENT + LATENCY ==="
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
"$TRANSFORM:$TRANSFORM_SHA"
do
    f="${spec%%:*}"; expected="${spec#*:}"
    [[ -f "$f" ]] || fail "missing infrastructure input $f"
    [[ "$(sha "$f")" == "$expected" ]] || fail "identity mismatch $f"
done
python3 -m py_compile "$TRANSFORM26485" "$TRANSFORM"
bash -n "$0"
pass "infrastructure syntax and identity"

# Hard pre-modification backup proof. No app transform/overlay occurs before this.
remote="$(git ls-remote origin "refs/heads/$BACKUP_BRANCH" | awk '{print $1}')"
[[ "$remote" == "$BACKUP_EXPECTED" ]] \
    || fail "backup branch $BACKUP_BRANCH=$remote expected=$BACKUP_EXPECTED"
pass "backup branch exact tested 26485 checkpoint"

TMP="$(mktemp -d)"
BASE="$TMP/base26485"
CAND="$TMP/candidate26486"
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

# Reconstruct the exact tested 26485 APPLICATION source by the same successful
# composition used by build 26485:
# protected app base -> exact 26483 -> exact 26484 delta -> exact 26485 transform.
# Infrastructure commits themselves intentionally never alter app/src/main.
reconstruct26485(){
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

        grep -q '^VERSION_NAME=0\.9726485$' app/version.properties
        grep -q '^VERSION_BUILD=26485$' app/version.properties
        grep -q 'IRIS_26485_FULL_PREBUFFER_AUTHORITATIVE_ZSL' \
            app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
        grep -q 'IRIS_26485_FULL_PREBUFFER_IMMEDIATE_PROCESS' \
            app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
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

reconstruct26485 "$BASE"
pass "exact tested 26485 application source reconstructed"

# Required binary backup patch BEFORE any 26486 modification.
(
    cd "$BASE"
    git add -N app/src/main app/version.properties >/dev/null 2>&1 || true
    git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties
) > "$PREPATCH"
[[ -s "$PREPATCH" ]] || fail "26486 pre-edit exact-26485 binary patch empty"
pass "binary pre-edit exact-26485 patch created before modification"

reconstruct26485 "$CAND"
python3 "$REPO/$TRANSFORM" "$CAND"
pass "26486 temporary candidate transform PASS"

cat > "$TMP/allow.txt" <<'EOF'
app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java
app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java
app/src/main/java/com/particlesdevs/photoncamera/processing/DefaultSaver.java
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java
app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl
app/src/main/assets/shaders/motionv2/mfsr_low_support_reference.glsl
app/src/main/assets/shaders/motionv2/mfsr_finalize.glsl
app/src/main/assets/shaders/motionv2/short_highlight_recover.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_unblocker.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_base.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_clipped_gaussian_h.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_clipped_gaussian_v.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_reduce4.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_bilateral.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_postprocess.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_dilate.glsl
EOF

# Exact changed-file allowlist relative to tested 26485.
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
    raise SystemExit("26486 changed-file allowlist mismatch changed="+repr(sorted(changed))+" expected="+repr(sorted(allow)))
print("26486 exact changed-file allowlist PASS")
PY

# Byte-protect every successful-26485 source file not intentionally changed.
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
        raise SystemExit("protected tested-26485 source changed: "+rel)
print("protected tested-26485 source hashes PASS")
PY

# No new whitespace damage: compare tested 26485 directly to 26486.
# git diff --no-index returns 1 merely because files differ, so fail only when
# --check actually emits a whitespace diagnostic.
set +e
iris26486_ws_out="$(git diff --no-index --check "$BASE/app/src/main" "$CAND/app/src/main" 2>&1)"
iris26486_ws_rc=$?
set -e
[[ "$iris26486_ws_rc" -eq 0 || "$iris26486_ws_rc" -eq 1 ]] \
    || fail "26486 scoped diff command failed rc=$iris26486_ws_rc"
[[ -z "$iris26486_ws_out" ]] || { echo "$iris26486_ws_out" >&2; fail "26486 new whitespace damage"; }
pass "scoped 26485-to-26486 whitespace/diff check"

CAP="$CAND/app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java"
BATCH="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java"
SAVER="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java"
DEFAULT="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/DefaultSaver.java"
HDRX="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java"
CR="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"
ACC="$CAND/app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl"
REFADD="$CAND/app/src/main/assets/shaders/motionv2/mfsr_low_support_reference.glsl"
FINAL="$CAND/app/src/main/assets/shaders/motionv2/mfsr_finalize.glsl"
SHORT="$CAND/app/src/main/assets/shaders/motionv2/short_highlight_recover.glsl"

# Preserve validated 26484/26485 architecture while requiring every 26486 owner.
for spec in \
"$CAP:IRIS_26484_IMMEDIATE_MOTION_SHUTTER_ACK" \
"$CAP:IRIS_26485_FULL_PREBUFFER_AUTHORITATIVE_ZSL" \
"$CAP:IRIS_26486_FREEZE_BUFFER_AT_SHUTTER_NO_TOPUP_WAIT" \
"$CAP:IRIS_26486_EXPOSURE_ENERGY_EV_GROUPING" \
"$CAP:IRIS_26486_WHOLE_GROUP_EXPOSURE_SPAN_PROOF" \
"$CAP:IRIS_26486_NONBLOCKING_SHORT_HIGHLIGHT_TICKET" \
"$CAP:IRIS_26486_BATCH_QUEUE_CAPTURE_OWNERSHIP" \
"$BATCH:IRIS_26486_ASYNC_SHORT_HIGHLIGHT_SLOT" \
"$SAVER:IRIS_26486_MOTIONBATCH_DIRECT_SAVER_HANDOFF" \
"$DEFAULT:IRIS_26486_DEFAULTSAVER_MOTIONBATCH_SOLE_OWNER" \
"$HDRX:IRIS_26486_HDRX_MOTIONBATCH_ENTRY" \
"$CR:IRIS_26484_BJZHOU_COUPLED_ALIGNMENT_REJECTION_OPPONENT_MERGE" \
"$CR:IRIS_26486_NO_IPOL_MONTE_CARLO_ACTIVE_PATH" \
"$CR:IRIS_26486_BJZHOU_REJECTION_GRAPH" \
"$CR:IRIS_26486_LATE_NONBLOCKING_SHORT_TAKE" \
"$ACC:IRIS_26486_BJZHOU_CENSORED_OPPONENT_DUAL_EVIDENCE" \
"$REFADD:IRIS_26486_BJZHOU_REFERENCE_CENSORED_OPPONENT_AUTHORITY" \
"$FINAL:IRIS_26486_CENSORED_OPPONENT_FINALIZE_REFERENCE_NEUTRAL" \
"$SHORT:IRIS_26486_SHORT_PHYSICAL_UP_OR_DOWN_REPLACEMENT"
do
    f="${spec%%:*}"; m="${spec#*:}"
    grep -q "$m" "$f" || fail "missing required marker $m"
done
pass "26486 lineage/ownership marker gates"

# Semantic source gates: these protect the actual six-part plan, not merely labels.
python3 - "$CAP" "$BATCH" "$SAVER" "$DEFAULT" "$HDRX" "$CR" "$ACC" "$SHORT" <<'PY'
from pathlib import Path
import re,sys
cap,batch,saver,default,hdrx,recon,acc,short=[Path(x).read_text() for x in sys.argv[1:]]
start=cap.index("    private void triggerZslCapture() {")
end=cap.index("    }    // IRIS_26343_GENERATION_SAFE_ZSL",start)
body=cap[start:end]
if "CaptureController.isProcessing" in body: raise SystemExit("Motion trigger still blocked by global isProcessing")
if "pollMotionTopUp();" in body: raise SystemExit("Motion trigger still enters top-up polling")
if "MOTION_26486_EXPOSURE_HALF_WINDOW_EV = 0.05" not in cap: raise SystemExit("0.05 EV half-window missing")
if "mMotionTopUpMinimumFrames = Math.min(mMotionTopUpTargetFrames, 2)" not in cap: raise SystemExit("two-frame minimum missing")
if "MOTION_26486_MAX_INFLIGHT_BATCHES = 2" not in cap: raise SystemExit("bounded queue missing")
if "iris26486ImageSaver.runMotionRaw" not in cap: raise SystemExit("shot-local saver missing")
if "SaverImplementation.IMAGE_BUFFER.addAll(iris26480ProcessingFrames)" in cap: raise SystemExit("capture still writes static Motion buffer")
rs=saver[saver.index("public void runMotionRaw"):saver.index("public void runRaw",saver.index("public void runMotionRaw"))]
if "IMAGE_BUFFER" in rs: raise SystemExit("ImageSaver Motion path still references static IMAGE_BUFFER")
rd=default[default.index("public void runMotionBatch"):default.index("public void runRaw",default.index("public void runMotionBatch"))]
if "IMAGE_BUFFER" in rd: raise SystemExit("DefaultSaver Motion path still references static IMAGE_BUFFER")
if "MotionV2IpolNoiseCurve" in recon: raise SystemExit("per-frame/reference IPOL Monte Carlo survived")
for old in ("mfsr_robustness_half","mfsr_robustness_erode"):
    if f'useAssetProgram("motionv2/{old}"' in recon: raise SystemExit("old hybrid robustness active: "+old)
for new in ("mfsr_bjzhou_unblocker","mfsr_bjzhou_rejection_base","mfsr_bjzhou_clipped_gaussian_h","mfsr_bjzhou_clipped_gaussian_v","mfsr_bjzhou_rejection_reduce4","mfsr_bjzhou_rejection_bilateral","mfsr_bjzhou_rejection_postprocess","mfsr_bjzhou_rejection_dilate"):
    if f'useAssetProgram("motionv2/{new}"' not in recon: raise SystemExit("missing rejection graph stage "+new)
if "physicalCfa" not in acc or "sharedChromaValidity" not in acc: raise SystemExit("censored physical opponent authority missing")
if "max(pow(max(o,0.0),power),fallback)" in short: raise SystemExit("one-sided short correction survived")
if "outc[c]=mix(normal[c],m.x,use);" not in short: raise SystemExit("bidirectional short replacement mix missing")
if "shortHighlightSlot.takeAndSeal()" not in recon: raise SystemExit("late optional short take missing")
print("26486 six-part semantic architecture gates PASS")
PY

# Java lexical/delimiter proof for every touched Java owner.
python3 - "$CAP" "$BATCH" "$SAVER" "$DEFAULT" "$HDRX" "$CR" <<'PY'
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
app/src/main/assets/shaders/motionv2/mfsr_mgc_covariance.glsl
app/src/main/assets/shaders/motionv2/mfsr_flow_expand.glsl
app/src/main/assets/shaders/motionv2/mfsr_lk_refine_level.glsl
app/src/main/assets/shaders/motionv2/mfsr_lk_select_candidate.glsl
app/src/main/assets/shaders/motionv2/mfsr_chroma_guide.glsl
app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl
app/src/main/assets/shaders/motionv2/mfsr_low_support_reference.glsl
app/src/main/assets/shaders/motionv2/mfsr_finalize.glsl
app/src/main/assets/shaders/motionv2/short_highlight_recover.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_unblocker.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_base.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_clipped_gaussian_h.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_clipped_gaussian_v.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_reduce4.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_bilateral.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_postprocess.glsl
app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_dilate.glsl
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
print("Photon runtime layout-parser compatibility PASS for 26486 shader graph")
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
if [[ "$shader_fail" -ne 0 ]]; then cat "$SHADERLOG"; fail "one or more 26486 shaders failed glslangValidator"; fi
pass "complete 26486 shader graph glslangValidator PASS"

while IFS= read -r rel; do
    f="$CAND/$rel"
    ! grep -Eq 'layout\((rg32f|rg16f|r16f)[^)]*\)[^;]*writeonly image2D' "$f" \
        || fail "Adreno hazardous writable format $(basename "$f")"
    ! grep -Eq '\b(float|vec[234]|int|ivec[234])\s+sample\b' "$f" \
        || fail "reserved GLSL identifier sample in $(basename "$f")"
done < "$TMP/shaders.txt"
pass "Adreno runtime-portability guards"

# Exact 26486 functional delta BEFORE version bump.
(
    cd "$CAND"
    git diff --binary -- app/src/main
) > "$DELTAOUT"
[[ -s "$DELTAOUT" ]] || fail "26486 functional delta empty"

# Version increment + candidate build proof.
bump "$CAND/app/version.properties" 0.9726485 26485 0.9726486 26486

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
[[ "${PIPESTATUS[0]}" -eq 0 ]] || fail "temporary 26486 candidate Gradle build"
(
    cd "$CAND"
    sha256sum -c "$TMP/candidate_prebuild.sha256" >/dev/null
) || fail "temporary Gradle mutated canonical candidate source"
pass "Temporary-copy validation: PASS"
pass "PRE-BUILD SAFETY PROOF PASSED"

# FINAL BUILD: reconstruct exact 26485 again in Action checkout, then overlay
# only the already-built 26486 allowlist. Version bump + APK build are one block.
git apply --check --binary "$BASE26483_PATCH"
git apply --binary "$BASE26483_PATCH"
sha256sum -c "$BASE26483_HASHES" >/dev/null
git apply --check --binary "$DELTA26484"
git apply --binary "$DELTA26484"
bump app/version.properties 0.9726483 26483 0.9726484 26484
python3 "$TRANSFORM26485" "$(pwd)"
bump app/version.properties 0.9726484 26484 0.9726485 26485
pass "final exact successful 26485 application graph reconstructed"

while IFS= read -r rel; do
    mkdir -p "$(dirname "$rel")"
    cp "$CAND/$rel" "$rel"
done < "$TMP/allow.txt"

{
bump app/version.properties 0.9726485 26485 0.9726486 26486

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
[[ -s "$SOURCEPATCH" ]] || fail "complete 26486 source patch empty"

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
[[ "${PIPESTATUS[0]}" -eq 0 ]] || fail "final 26486 Gradle build"
sha256sum -c "$PREBUILDHASH" >/dev/null || fail "final Gradle mutated canonical source"

mapfile -t apks < <(find app/build/outputs/apk -type f -name '*.apk' | sort)
[[ ${#apks[@]} -ge 1 ]] || fail "no APK output"
rm -f IrisCamera-0.9726486-26486-*.apk
cp "${apks[-1]}" "$APK_NAME"
[[ -s "$APK_NAME" ]] || fail "published 26486 APK missing"

mkdir -p "$OUTDIR/next_baseline_inputs"
cp "$SOURCEPATCH" "$OUTDIR/next_baseline_inputs/26486_successful_source.patch"
cp "$AFTERHASH" "$OUTDIR/next_baseline_inputs/26486_successful_after.sha256"
cp "$DELTAOUT" "$OUTDIR/next_baseline_inputs/26486_delta_from_26485.patch"
cp "$REPO/$TRANSFORM" "$OUTDIR/next_baseline_inputs/"

cat > "$REPORT" <<EOF
26486 FULL BJZHOU CENSORED OPPONENT + LATENCY V1
Version=$NEW_VERSION
Build=$NEW_BUILD
Branch=$BRANCH
BackupBranch=$BACKUP_BRANCH
BackupExpected=$BACKUP_EXPECTED
Base26483PatchSHA=$BASE26483_PATCH_SHA
Base26483ManifestSHA=$BASE26483_HASHES_SHA
Successful26484DeltaSHA=$DELTA26484_SHA
Successful26485TransformSHA=$TRANSFORM26485_SHA
Transform26486SHA=$TRANSFORM_SHA
APK=$APK_NAME
APK_SHA256=$(sha "$APK_NAME")
SourcePatchSHA256=$(sha "$SOURCEPATCH")
AfterManifestSHA256=$(sha "$AFTERHASH")
Capture=frame slider is maximum; zero normal top-up wait; >=2 equal-energy frames; whole group <=0.10 EV; short RAW non-blocking
Latency=per-reference/per-auxiliary IPOL Monte-Carlo removed from active reconstruction; Camera2 affine noise retained; full GPU rejection graph
Rejection=unblocker -> clipping-aware rejection -> clipped Gaussian H/V -> 4x reduce -> bilateral -> postprocess -> dilation -> final frame weight
Highlights=physical pre-WB/pre-repair saturation validity gates only opponent chroma; green/radiometric evidence retained; short may correct up or down
Ownership=MotionBatch sole RAW owner; no Motion static IMAGE_BUFFER handoff; max two in-flight batches; GPU processing remains serialized
BuildSafety=exact tested 26485 reconstruction, backup proof, binary pre-edit patch, strict allowlist, protected hashes, Java/GLSL/runtime-parser/Adreno gates, temporary Gradle, candidate/final parity
EOF

sha256sum "$APK_NAME" "$SOURCEPATCH" "$AFTERHASH" "$REPORT" "$DELTAOUT" \
    > "$OUTDIR/26486_artifact_hashes.sha256"

pass "26486 canonical checkpoint package created"
echo "26486_SOURCE_PATCH_SHA256=$(sha "$SOURCEPATCH")"
echo "26486_AFTER_MANIFEST_SHA256=$(sha "$AFTERHASH")"
echo "26486 BUILD SUCCESS"
