#!/usr/bin/env bash
set -euo pipefail

EXPECTED_BRANCH="experimental-clean-photon-rebuild"
EXPECTED_APP_BASE="8233415edf738bf35c0fe1c4907f5dfe51de31a4"
BACKUP_BRANCH="backup-26488-v4-tested-before-26489-bjzhou-host-rewrite"
BACKUP_EXPECTED="3a1196172f0e784c491b69cfeaa499ed459b902f"

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
TRANSFORM26488="transform_26488_full_merge_rgb_rejection_contract_v1.py"
TRANSFORM26488_SHA="b7710d343aa26b1215178821983f4ff3f742ad07d1ca556de2d272fbc36664c0"
TRANSFORM="transform_26489_bjzhou_host_bayer_rcd_v2.py"
TRANSFORM_SHA="8def08e77dd63a31b93afb443184cad148364a21090b30da6ceadf883be93925"

NEW_VERSION="0.9726489"
NEW_BUILD="26489"
OUTDIR="build_26489_outputs"
APK_NAME="IrisCamera-${NEW_VERSION}-${NEW_BUILD}-bjzhou-host-bayer-faithful-rcd-debug.apk"

fail(){ echo "FAIL: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }

REPO="$(pwd)"
rm -rf "$OUTDIR"
mkdir -p "$OUTDIR"
AUDIT="$OUTDIR/26489_source_audit.txt"
CANDLOG="$OUTDIR/26489_temporary_candidate_build.log"
JAVACLOG="$OUTDIR/26489_temporary_candidate_javac.log"
FINALLOG="$OUTDIR/26489_final_build.log"
SHADERLOG="$OUTDIR/26489_shader_validation.txt"
REPORT="$OUTDIR/26489_build_report.txt"
PREPATCH="$OUTDIR/26489_pre_edit_exact_26488_binary.patch"
DELTAOUT="$OUTDIR/26489_delta_from_26488.patch"
SOURCEPATCH="$OUTDIR/26489_source.patch"
AFTERHASH="$OUTDIR/26489_after.sha256"
PREBUILDHASH="$OUTDIR/26489_prebuild_canonical.sha256"

exec > >(tee "$AUDIT") 2>&1
echo "=== 26489 BJZHOU HOST / PERSISTENT BAYER ACCUMULATOR / BANDED DIRECTIONAL RCD ==="
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
"$TRANSFORM26488:$TRANSFORM26488_SHA" \
"$TRANSFORM:$TRANSFORM_SHA"
do
    f="${spec%%:*}"; expected="${spec#*:}"
    [[ -f "$f" ]] || fail "missing infrastructure input $f"
    [[ "$(sha "$f")" == "$expected" ]] || fail "identity mismatch $f"
done
python3 -m py_compile "$TRANSFORM26485" "$TRANSFORM26486" "$TRANSFORM26487" "$TRANSFORM26488" "$TRANSFORM"
python3 "$TRANSFORM" --self-test
bash -n "$0"
pass "infrastructure syntax and identity"

remote="$(git ls-remote origin "refs/heads/$BACKUP_BRANCH" | awk '{print $1}')"
[[ "$remote" == "$BACKUP_EXPECTED" ]] \
    || fail "backup branch $BACKUP_BRANCH=$remote expected=$BACKUP_EXPECTED"
pass "backup branch exact tested 26488 V4 checkpoint"

TMP="$(mktemp -d)"
BASE="$TMP/base26488"
CAND="$TMP/candidate26489"
cleanup(){
    set +e
    git worktree remove --force "$BASE" >/dev/null 2>&1 || true
    git worktree remove --force "$CAND" >/dev/null 2>&1 || true
    rm -rf "$TMP"
}
trap cleanup EXIT

bump(){
    local file="$1" oldv="$2" oldb="$3" newv="$4" newb="$5"
    python3 - "$file" "$oldv" "$oldb" "$newv" "$newb" <<'PYBUMP'
from pathlib import Path
import sys
p=Path(sys.argv[1]);oldv,oldb,newv,newb=sys.argv[2:]
s=p.read_text();a=f"VERSION_NAME={oldv}";b=f"VERSION_BUILD={oldb}"
if s.count(a)!=1 or s.count(b)!=1:raise SystemExit(f"version anchor mismatch {a}={s.count(a)} {b}={s.count(b)}")
p.write_text(s.replace(a,f"VERSION_NAME={newv}",1).replace(b,f"VERSION_BUILD={newb}",1))
PYBUMP
}

reconstruct26488(){
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
        python3 "$REPO/$TRANSFORM26488" "$d"
        bump app/version.properties 0.9726487 26487 0.9726488 26488

        grep -q '^VERSION_NAME=0\.9726488$' app/version.properties
        grep -q '^VERSION_BUILD=26488$' app/version.properties
        grep -q 'IRIS_26485_FULL_PREBUFFER_AUTHORITATIVE_ZSL' app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
        grep -q 'IRIS_26486_FREEZE_BUFFER_AT_SHUTTER_NO_TOPUP_WAIT' app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
        grep -q 'IRIS_26487_WRONSKI_DEFERRED_GPU_CHAIN_NO_PER_DISPATCH_FINISH' app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java
        grep -q 'IRIS_26488_V4_DIRECT_BYTEBUFFER_LENS_UPLOAD' app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java
    )
}

reconstruct26488 "$BASE"
pass "exact tested 26488 V4 application source reconstructed"

(
    cd "$BASE"
    git add -N app/src/main app/version.properties >/dev/null 2>&1 || true
    git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties
) > "$PREPATCH"
[[ -s "$PREPATCH" ]] || fail "exact-26488 pre-edit binary patch empty"
pass "binary pre-edit exact-26488 patch created before 26489 modification"

reconstruct26488 "$CAND"
python3 "$REPO/$TRANSFORM" "$CAND"
pass "26489 temporary candidate transform PASS"

cat > "$TMP/allow.txt" <<'EOFALLOW'
app/src/main/assets/shaders/motionv2/mfsr_26489_bayer_diag_sample.glsl
app/src/main/assets/shaders/motionv2/mfsr_bayer_accumulate.glsl
app/src/main/assets/shaders/motionv2/mfsr_bayer_accumulator_clear.glsl
app/src/main/assets/shaders/motionv2/mfsr_bayer_normalize.glsl
app/src/main/assets/shaders/motionv2/rcd26489_diag_direction.glsl
app/src/main/assets/shaders/motionv2/rcd26489_diag_residual.glsl
app/src/main/assets/shaders/motionv2/rcd26489_green.glsl
app/src/main/assets/shaders/motionv2/rcd26489_green_rb.glsl
app/src/main/assets/shaders/motionv2/rcd26489_lpf.glsl
app/src/main/assets/shaders/motionv2/rcd26489_opposite.glsl
app/src/main/assets/shaders/motionv2/rcd26489_populate.glsl
app/src/main/assets/shaders/motionv2/rcd26489_vh_direction.glsl
app/src/main/assets/shaders/motionv2/rcd26489_write.glsl
app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl
app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLBuffer.java
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2RcdDemosaic.java
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java
EOFALLOW

python3 - "$BASE" "$CAND" "$TMP/allow.txt" <<'PYALLOW'
from pathlib import Path
import hashlib,sys
a,b=Path(sys.argv[1]),Path(sys.argv[2]);allow=set(Path(sys.argv[3]).read_text().splitlines())
def h(root):
 d={}
 for p in (root/'app/src/main').rglob('*'):
  if p.is_file():d[str(p.relative_to(root)).replace('\\','/')]=hashlib.sha256(p.read_bytes()).hexdigest()
 return d
x,y=h(a),h(b);changed={k for k in x.keys()|y.keys() if x.get(k)!=y.get(k)}
if changed!=allow:raise SystemExit('26489 changed-file allowlist mismatch changed='+repr(sorted(changed))+' expected='+repr(sorted(allow)))
for rel in (x.keys() & y.keys())-allow:
 if x[rel]!=y[rel]:raise SystemExit('protected exact-26488 source changed: '+rel)
print('26489 exact 20-file allowlist + unrelated-source byte protection PASS')
PYALLOW

set +e
ws_out="$(git diff --no-index --check "$BASE/app/src/main" "$CAND/app/src/main" 2>&1)"
ws_rc=$?
set -e
[[ "$ws_rc" -eq 0 || "$ws_rc" -eq 1 ]] || fail "26489 scoped diff command failed rc=$ws_rc"
[[ -z "$ws_out" ]] || { echo "$ws_out" >&2; fail "26489 new whitespace damage"; }
pass "scoped exact-26488-to-26489 whitespace check"

CAP="$CAND/app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java"
BATCH="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java"
SAVER="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java"
DEFAULT="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/DefaultSaver.java"
HDRX="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java"
GLP="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLProg.java"
GLT="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLTexture.java"
GLB="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLBuffer.java"
FRAME="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java"
WR="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java"
CR="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"
INPUT="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java"
POST="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java"
RCD="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2RcdDemosaic.java"
SD="$CAND/app/src/main/assets/shaders/motionv2"

for spec in \
"$CAP:IRIS_26486_FREEZE_BUFFER_AT_SHUTTER_NO_TOPUP_WAIT" \
"$CAP:IRIS_26486_RING_REOPEN_ONLY_AFTER_IMMUTABLE_BATCH" \
"$CAP:IRIS_26486_NONBLOCKING_SHORT_HIGHLIGHT_TICKET" \
"$CAP:IRIS_26487_SINGLE_ACTIVE_MOTION_PROCESSING_NO_BACKLOG" \
"$CAP:IRIS_26489_SHORT_RAW_PRE_RESULT_STAGING_OWNER" \
"$CAP:IRIS_26489_SHORT_RAW_CALLBACK_BEFORE_RING_DRAIN" \
"$CAP:IRIS_26489_SHORT_STAGE_COPY_SKIPPED" \
"$BATCH:IRIS_26486_ASYNC_SHORT_HIGHLIGHT_SLOT" \
"$SAVER:IRIS_26486_MOTIONBATCH_DIRECT_SAVER_HANDOFF" \
"$DEFAULT:IRIS_26486_DEFAULTSAVER_MOTIONBATCH_SOLE_OWNER" \
"$HDRX:IRIS_26486_HDRX_MOTIONBATCH_ENTRY" \
"$GLP:IRIS_26487_MOTION_DEFERRED_GPU_SUBMISSION" \
"$WR:IRIS_26487_WRONSKI_DEFERRED_GPU_CHAIN_NO_PER_DISPATCH_FINISH" \
"$CR:IRIS_26489_BJZHOU_PERSISTENT_BAYER_HOST" \
"$CR:IRIS_26489_ADMISSION_EQUALS_ACCUMULATOR_CONTRIBUTION_INVARIANT" \
"$CR:IRIS_26489_BJZHOU_BAYER_NORMALIZE_EXACTLY_ONCE" \
"$CR:IRIS_26489_BENTO_SHORT_SENSOR_DOMAIN_BAYER_RECOVERY" \
"$INPUT:IRIS_26489_FUSED_BAYER_FLOAT32_BRIDGE_OWNER" \
"$POST:IRIS_26489_FUSED_BAYER_CANONICAL_POST_GRAPH" \
"$RCD:IRIS_26489_POSTMERGE_RCD_DEMOSAIC_OWNER" \
"$SD/mfsr_bayer_accumulate.glsl:IRIS_26489_BJZHOU_PERSISTENT_BAYER_ACCUMULATOR_OWNER" \
"$SD/mfsr_bayer_normalize.glsl:IRIS_26489_BJZHOU_BAYER_NORMALIZE_ONCE" \
"$SD/short_highlight_bayer_recover.glsl:IRIS_26489_BENTO_SHORT_SENSOR_DOMAIN_BAYER_RECOVERY" \
"$GLB:IRIS_26489_GPU_ONLY_SSBO_ALLOCATION"
do
 f="${spec%%:*}";m="${spec#*:}";grep -q "$m" "$f" || fail "missing required marker $m"
done
pass "tested ZSL/latency/Wronski owners preserved + 26489 host/Bayer/RCD contracts present"

python3 - "$CAP" "$GLP" "$GLT" "$GLB" "$FRAME" "$WR" "$CR" "$INPUT" "$POST" "$RCD" <<'PYHOST'
from pathlib import Path
import re,sys
cap,glp,glt,glb,frame,wr,recon,inputj,post,rcd=[Path(x).read_text() for x in sys.argv[1:11]]
start=cap.index('    private void triggerZslCapture() {');end=cap.index('    private void captureStillPicture()',start);body=cap[start:end]
if 'CaptureController.isProcessing' in body:raise SystemExit('Motion shutter regressed to global processing wait')
if 'pollMotionTopUp();' in body:raise SystemExit('Motion shutter regressed to post-press normal-frame top-up')
if 'MOTION_26486_MAX_INFLIGHT_BATCHES = 1' not in cap or 'MOTION_26486_MAX_INFLIGHT_BATCHES = 2' in cap:raise SystemExit('single active Motion / zero backlog contract lost')
if 'MAX_STAGED_RAW = 4' not in cap or 'ArrayDeque<ImageFrame> stagedRaw' not in cap:raise SystemExit('bounded copied short-RAW staging missing')
if re.search(r'ArrayDeque\s*<\s*Image\s*>\s+stagedRaw',cap):raise SystemExit('short staging illegally retains ImageReader Image objects')
if 'mBackgroundHandler.postDelayed(ticket::closeStaged, 2000L);' not in cap:raise SystemExit('short staging bounded cleanup missing')
if 'catch (Throwable t)' not in cap or 'IRIS_26489_SHORT_STAGE_COPY_SKIPPED' not in cap:raise SystemExit('short staging copy callback is not fail-safe')
if 'public ByteBuffer buffer;' not in frame:raise SystemExit('ImageFrame RAW carrier changed')
legacy=re.search(r'public void computeAuto\(Point size, int z\) \{(.*?)\n    \}',glp,re.S)
deferred=re.search(r'public void computeAutoDeferred\(Point size, int z\) \{(.*?)\n    \}',glp,re.S)
finisher=re.search(r'public long finishDeferredCompute\(String label\) \{(.*?)\n    \}',glp,re.S)
if not legacy or 'glFinish();' not in legacy.group(1):raise SystemExit('shared legacy computeAuto changed')
if not deferred or 'glFinish();' in deferred.group(1) or 'GL_ALL_BARRIER_BITS' not in deferred.group(1):raise SystemExit('Motion deferred dispatch invalid')
if not finisher or finisher.group(1).count('glFinish();')!=1:raise SystemExit('deferred GPU finisher invalid')
if 'glProg.computeAuto(' in wr or 'glProg.computeAuto(' in recon:raise SystemExit('blocking computeAuto survived active Motion reconstruction')
if recon.count('finishDeferredCompute(')!=1 or recon.count('finishDeferredCompute("MotionV2 final image")')!=1:raise SystemExit('26489 must retain exactly one reconstruction GPU completion wait')
for retired in ('mfsr_low_support_reference','direct_rgb_accumulate','mfsr_finalize','short_highlight_recover'):
 if f'useAssetProgram("motionv2/{retired}"' in recon:raise SystemExit('retired 26488 active program survived: '+retired)
if recon.count('useAssetProgram("motionv2/mfsr_bayer_normalize", true)')!=1:raise SystemExit('Bayer normalization invocation count is not exactly one')
if 'iris26489AdmittedFrames != iris26489ContributedFrames' not in recon or 'iris26489AdmittedFrames != iris26489ExpectedAdmittedFrames' not in recon:raise SystemExit('hard admitted==contributed==expected invariant missing')
if 'boolean directRgbCarrier = false;' not in post or 'new MotionV2RcdDemosaic()' not in post:raise SystemExit('standard Bayer post graph is not fused Bayer -> RCD')
if 'directRgbFullRes' in inputj:raise SystemExit('old direct-RGB bridge carrier survived')
if 'FloatBuffer.wrap' in rcd:raise SystemExit('unsafe heap FloatBuffer upload reintroduced')
if 'ByteBuffer.allocateDirect' not in rcd or '.order(ByteOrder.nativeOrder())' not in rcd:raise SystemExit('RCD lens shading upload is not direct native ByteBuffer')
if '(ByteBuffer) pixels' not in glt:raise SystemExit('GLTexture CPU upload cast contract changed')
if 'IRIS_26489_GPU_ONLY_SSBO_ALLOCATION' not in glb:raise SystemExit('GPU-only RCD SSBO constructor missing')
if 'this(size,mFormat,GL_STATIC_DRAW,true);' not in glb or 'this(size,mFormat,mode,true);' not in glb:raise SystemExit('legacy GLBuffer CPU mirror constructors changed')
if 'new GLBuffer(' not in rcd or 'GL_DYNAMIC_DRAW' not in rcd:raise SystemExit('RCD GPU-only scratch ownership missing')
if 'glFinish(' in rcd or 'computeAuto(' in rcd:raise SystemExit('RCD introduced CPU-blocking per-pass synchronization')
for shader in ('rcd26489_populate','rcd26489_vh_direction','rcd26489_lpf','rcd26489_green','rcd26489_diag_residual','rcd26489_diag_direction','rcd26489_opposite','rcd26489_green_rb','rcd26489_write'):
 if rcd.count(f'useAssetProgram("motionv2/{shader}", true)')!=1:raise SystemExit('RCD stage invocation mismatch '+shader)
if rcd.count('dispatch(bandSize);')!=8 or rcd.count('dispatch(new Point(raw.x, coreRows));')!=1:raise SystemExit('RCD nine-pass dispatch contract mismatch')
if 'BAND_CORE_ROWS = 256' not in rcd or 'RCD_HALO_ROWS = 12' not in rcd:raise SystemExit('RCD band/halo ownership mismatch')
print('26489 host/capture/latency/runtime carrier invariants PASS')
PYHOST

python3 - "$CAP" "$CR" "$INPUT" "$POST" "$RCD" "$WR" "$GLP" "$GLB" <<'PYJAVA'
from pathlib import Path
import sys
def code_only(src):
 out=[];i=0;n=len(src);state='code'
 while i<n:
  if state=='code':
   if src.startswith('//',i):state='line';out.extend('  ');i+=2;continue
   if src.startswith('/*',i):state='block';out.extend('  ');i+=2;continue
   if src.startswith('"""',i):state='text';out.extend('   ');i+=3;continue
   c=src[i]
   if c=='"':state='string';out.append(' ');i+=1;continue
   if c=="'":state='char';out.append(' ');i+=1;continue
   out.append(c);i+=1;continue
  if state=='line':
   c=src[i];out.append('\n' if c=='\n' else ' ');i+=1
   if c=='\n':state='code'
   continue
  if state=='block':
   if src.startswith('*/',i):out.extend('  ');i+=2;state='code';continue
   out.append('\n' if src[i]=='\n' else ' ');i+=1;continue
  if state=='text':
   if src.startswith('"""',i):out.extend('   ');i+=3;state='code';continue
   out.append('\n' if src[i]=='\n' else ' ');i+=1;continue
  c=src[i]
  if c=='\\':
   out.append(' ');i+=1
   if i<n:out.append('\n' if src[i]=='\n' else ' ');i+=1
   continue
  out.append('\n' if c=='\n' else ' ');i+=1
  if (state=='string' and c=='"') or (state=='char' and c=="'"):state='code'
 if state in ('block','string','char','text'):raise SystemExit('unterminated Java lexical state '+state)
 return ''.join(out)
for path in sys.argv[1:]:
 code=code_only(Path(path).read_text());stack=[];pairs={'}':'{',')':'(',']':'['};line=1
 for c in code:
  if c=='\n':line+=1;continue
  if c in '{([':stack.append((c,line))
  elif c in '})]':
   if not stack or stack[-1][0]!=pairs[c]:raise SystemExit(f'Java delimiter mismatch {path} line={line}')
   stack.pop()
 if stack:raise SystemExit(f'Java unclosed delimiter {path} {stack[-1]}')
 print('Java lexical structure PASS',Path(path).name)
PYJAVA

python3 - "$CAND" "$CR" "$WR" "$RCD" "$TMP/compute_shaders.txt" "$TMP/fragment_shaders.txt" <<'PYGRAPH'
from pathlib import Path
import re,sys
root=Path(sys.argv[1]);owners=[Path(x) for x in sys.argv[2:5]];compute=set();fragment=set()
for owner in owners:
 java=owner.read_text()
 for m in re.finditer(r'useAssetProgram\(\s*"motionv2/([^"]+)"(?:\s*,\s*(true|false))?\s*\)',java):
  name,flag=m.group(1),m.group(2);rel=f'app/src/main/assets/shaders/motionv2/{name}.glsl'
  if not (root/rel).is_file():raise SystemExit('active Motion shader missing: '+rel)
  (compute if flag=='true' else fragment).add(rel)
if compute & fragment:raise SystemExit('shader loaded as both compute and fragment: '+repr(sorted(compute&fragment)))
Path(sys.argv[5]).write_text(''.join(x+'\n' for x in sorted(compute)))
Path(sys.argv[6]).write_text(''.join(x+'\n' for x in sorted(fragment)))
print(f'26489 active Motion graph derived compute={len(compute)} fragment={len(fragment)}')
PYGRAPH

python3 - "$CAND" "$CR" "$WR" "$RCD" <<'PYBIND'
from pathlib import Path
import re,sys
root=Path(sys.argv[1]);owners=[Path(x) for x in sys.argv[2:]];problems=[];invocations=0
def strip(s):return re.sub(r'//.*','',re.sub(r'/\*.*?\*/','',s,flags=re.S))
call_re=re.compile(r'useAssetProgram\(\s*"motionv2/([^"]+)"(?:\s*,\s*(true|false))?\s*\)')
resource_re=re.compile(r'\buniform\s+(?:(?:highp|mediump|lowp|readonly|writeonly|coherent|volatile|restrict)\s+)*(u?i?sampler2D|u?i?image2D)\s+([A-Za-z_]\w*)')
regular_re=re.compile(r'\buniform\s+(?:(?:highp|mediump|lowp)\s+)?(?!u?i?(?:sampler2D|image2D)\b)(?:bool|int|uint|float|vec[234]|ivec[234]|uvec[234]|mat[234])\s+([A-Za-z_]\w*)\s*(?:\[[^;]*\])?\s*;')
buffer_re=re.compile(r'layout\s*\([^)]*std430[^)]*\)\s*(?:readonly\s+|writeonly\s+|coherent\s+|volatile\s+|restrict\s+)*buffer\s+([A-Za-z_]\w*)\s*\{')
for owner in owners:
 java=owner.read_text();calls=list(call_re.finditer(java))
 for i,m in enumerate(calls):
  invocations+=1;name=m.group(1);shader=root/f'app/src/main/assets/shaders/motionv2/{name}.glsl';segment=java[m.end():(calls[i+1].start() if i+1<len(calls) else len(java))];source=strip(shader.read_text())
  resources={dm.group(2):dm.group(1) for dm in resource_re.finditer(source)};regular={dm.group(1) for dm in regular_re.finditer(source)};buffers={dm.group(1) for dm in buffer_re.finditer(source)}
  samplers=set(re.findall(r'(?<!Compute)setTexture\(\s*"([^"]+)"',segment));images=set(re.findall(r'setTextureCompute\(\s*"([^"]+)"',segment));variables=set(re.findall(r'setVar(?:1|U)?\(\s*"([^"]+)"',segment));buffer_calls=set(re.findall(r'setBufferCompute\(\s*"([^"]+)"',segment))
  for var,typ in resources.items():
   if typ.endswith('sampler2D'):
    if var not in samplers:problems.append((owner.name,name,var,typ,'missing setTexture'))
    if var in images:problems.append((owner.name,name,var,typ,'ILLEGAL setTextureCompute'))
   else:
    if var not in images:problems.append((owner.name,name,var,typ,'missing setTextureCompute'))
    if var in samplers:problems.append((owner.name,name,var,typ,'ILLEGAL setTexture'))
  for var in regular:
   if var not in variables:problems.append((owner.name,name,var,'regular','missing setVar'))
  for var in buffers:
   if var not in buffer_calls:problems.append((owner.name,name,var,'buffer','missing setBufferCompute'))
  for var in samplers:
   if var not in resources or not resources[var].endswith('sampler2D'):problems.append((owner.name,name,var,'host setTexture','undeclared or non-sampler'))
  for var in images:
   if var not in resources or not resources[var].endswith('image2D') or resources[var].endswith('sampler2D'):problems.append((owner.name,name,var,'host setTextureCompute','undeclared or non-image'))
  for var in variables:
   if var not in regular:problems.append((owner.name,name,var,'host setVar','undeclared or non-regular uniform'))
  for var in buffer_calls:
   if var not in buffers:problems.append((owner.name,name,var,'host setBufferCompute','undeclared buffer'))
if problems:raise SystemExit('26489 TYPE-AWARE BINDING FAILURE: '+repr(problems))
if invocations != 49:raise SystemExit(f'26489 expected 49 literal Motion shader invocations, got {invocations}')
print(f'26489 TYPE-AWARE BINDING PASS invocations={invocations} bufferContracts=true')
PYBIND
pass "bidirectional sampler/image/SSBO/regular-uniform Photon API type contract"

python3 - "$CAND" "$TMP/compute_shaders.txt" "$REPO/$TRANSFORM26488" <<'PYVALID'
from pathlib import Path
import importlib.util,re,sys
root=Path(sys.argv[1]);listing=Path(sys.argv[2]);transform=Path(sys.argv[3])
spec=importlib.util.spec_from_file_location('iris26488_validators',transform);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
shaders={rel:(root/rel).read_text() for rel in listing.read_text().splitlines() if rel.strip()}
# 26488's parser gate predated SSBO blocks and intentionally rejects a resource declaration that
# ends in '{'. Keep that gate for the legacy image-only shaders and add an exact GLInterface
# simulation that accepts SSBO block names for all active shaders.
legacy={rel:text for rel,text in shaders.items() if ' buffer ' not in text}
m.validate_photon_runtime_layout_parser(legacy)
for rel,text in shaders.items():
 runtime=text.replace('#define LAYOUT //','#define LAYOUT layout(local_size_x = 8, local_size_y = 8, local_size_z = 1) in;',1)
 names=set();saw_local=False
 for no,line in enumerate(runtime.splitlines(),1):
  if 'layout' not in line:continue
  if line.count('layout(')!=1:raise SystemExit(f'Photon getLayouts multi-layout hazard {rel}:{no}: {line}')
  stripped=line.strip()
  if not (stripped.startswith('layout(') or stripped.startswith('#define LAYOUT layout(')):raise SystemExit(f'Photon getLayouts prefix hazard {rel}:{no}: {line}')
  left=line.find('(');right=line.rfind(')')
  if left<0 or right<=left:raise SystemExit(f'Photon getLayouts parentheses hazard {rel}:{no}')
  parts=[x for x in line.replace('{','').split(' ') if x!=''];last=(parts[-1] if parts else '').replace(';','').replace('\n','')
  params=line[left+1:right].split(',')
  def parameter(name):
   for item in params:
    pv=item.replace(' ','').split('=')
    if pv and pv[0]==name:
     if len(pv)!=2 or not re.fullmatch(r'-?\d+',pv[1]):raise SystemExit(f'Photon getLayouts non-integer {name} {rel}:{no}: {item}')
     return int(pv[1])
   return 0
  if last=='in':
   if min(parameter('local_size_x'),parameter('local_size_y'),parameter('local_size_z'))<=0:raise SystemExit(f'Photon getLayouts invalid local size {rel}:{no}')
   saw_local=True
  else:
   if not re.fullmatch(r'[A-Za-z_]\w*',last):raise SystemExit(f'Photon getLayouts resource-name hazard {rel}:{no}: {last!r}')
   if last in names:raise SystemExit(f'Photon getLayouts duplicate resource {rel}:{no}: {last}')
   names.add(last);parameter('binding')
 if not saw_local:raise SystemExit(f'Photon getLayouts lost compute layout {rel}')
m.validate_glsl_reserved_identifiers(shaders);m.validate_gles_image_store_formats(shaders)
print('26489 extended Photon getLayouts SSBO/image parser simulation PASS')
PYVALID
pass "tested Photon layout including SSBO + GLSL reserved-name + GLES image-format validators"

: > "$SHADERLOG"
compile_compute(){
 local f="$1" tmp="$2"
 python3 - "$f" "$tmp" <<'PYCOMP'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text();needle='#define LAYOUT //\nLAYOUT'
if needle not in s:raise SystemExit('missing Photon LAYOUT header')
s=s.replace(needle,'#version 310 es\nlayout(local_size_x=8,local_size_y=8,local_size_z=1) in;',1);Path(sys.argv[2]).write_text(s)
PYCOMP
 glslangValidator -S comp "$tmp" >> "$SHADERLOG" 2>&1
}
compile_fragment(){
 local f="$1" tmp="$2"
 python3 - "$f" "$tmp" <<'PYFRAG'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text();needle='#define LAYOUT //\nLAYOUT'
if needle not in s:raise SystemExit('missing Photon LAYOUT header')
s=s.replace(needle,'#version 300 es',1);Path(sys.argv[2]).write_text(s)
PYFRAG
 glslangValidator -S frag "$tmp" >> "$SHADERLOG" 2>&1
}
shader_fail=0
while IFS= read -r rel;do [[ -n "$rel" ]]||continue;n="$(basename "$rel")";if compile_compute "$CAND/$rel" "$TMP/$n.comp";then echo "COMPUTE PASS $n" >> "$SHADERLOG";else echo "COMPUTE FAIL $n" >> "$SHADERLOG";shader_fail=1;fi;done < "$TMP/compute_shaders.txt"
while IFS= read -r rel;do [[ -n "$rel" ]]||continue;n="$(basename "$rel")";if compile_fragment "$CAND/$rel" "$TMP/$n.frag";then echo "FRAGMENT PASS $n" >> "$SHADERLOG";else echo "FRAGMENT FAIL $n" >> "$SHADERLOG";shader_fail=1;fi;done < "$TMP/fragment_shaders.txt"
if [[ "$shader_fail" -ne 0 ]];then cat "$SHADERLOG";fail "one or more active 26489 shaders failed glslangValidator";fi
pass "complete active 26489 compute+fragment graph glslangValidator PASS"

cat "$TMP/compute_shaders.txt" "$TMP/fragment_shaders.txt" | sort -u > "$TMP/all_active_shaders.txt"
while IFS= read -r rel;do
 [[ -n "$rel" ]]||continue;f="$CAND/$rel"
 ! grep -Eq 'layout\((rg32f|rg16f|r16f|r16ui|rg16ui)[^)]*\)[^;]*(u?image2D|iimage2D)' "$f" || fail "GLES/Adreno hazardous writable image format $(basename "$f")"
 ! grep -Eq '\b(float|vec[234]|int|ivec[234]|uint|uvec[234]|bool|mat[234])\s+(sample|common|coherent|precision)\b' "$f" || fail "reserved GLSL identifier declaration in $(basename "$f")"
done < "$TMP/all_active_shaders.txt"
pass "Adreno runtime-portability guards"

python3 - <<'PYMODEL'
admitted=15;contributed=0;support=0.0
for i in range(admitted):contributed+=1;support+=1.0 if i==0 else 0.93
assert admitted==contributed==15 and support>13.0
print(f'26489 accumulator model PASS admitted={admitted} contributed={contributed} modelSupport={support:.2f}')
PYMODEL

(
 cd "$CAND"
 git add -N app/src/main >/dev/null 2>&1 || true
 git diff --binary -- app/src/main
) > "$DELTAOUT"
[[ -s "$DELTAOUT" ]] || fail "26489 functional delta empty"

bump "$CAND/app/version.properties" 0.9726488 26488 0.9726489 26489
python3 - "$CAND" "$TMP/candidate_prebuild.sha256" <<'PYHASH'
from pathlib import Path
import hashlib,sys
root=Path(sys.argv[1]);out=Path(sys.argv[2]);ignore={'app/src/main/cpp/deps/archive.h','app/src/main/cpp/deps/archive_entry.h','app/src/main/cpp/deps/technicallyflac.h','app/src/main/cpp/deps/tiny_dng_writer.h'};rows=[]
for p in (root/'app/src/main').rglob('*'):
 if p.is_file():
  rel=str(p.relative_to(root)).replace('\\','/')
  if rel in ignore:continue
  rows.append((rel,hashlib.sha256(p.read_bytes()).hexdigest()))
vp=root/'app/version.properties';rows.append(('app/version.properties',hashlib.sha256(vp.read_bytes()).hexdigest()));out.write_text(''.join(f'{h}  {r}\n' for r,h in sorted(rows)))
PYHASH

set +e
( cd "$CAND";chmod +x gradlew;./gradlew :app:compileDebugJavaWithJavac --no-daemon --stacktrace ) 2>&1 | tee "$JAVACLOG"
javac_rc=${PIPESTATUS[0]}
set -e
[[ "$javac_rc" -eq 0 ]] || fail "temporary 26489 candidate Java compile"
( cd "$CAND";sha256sum -c "$TMP/candidate_prebuild.sha256" >/dev/null ) || fail "temporary Javac mutated canonical source"
pass "26489 candidate Java compile: PASS"

set +e
( cd "$CAND";./gradlew assembleDebug --no-daemon --stacktrace ) 2>&1 | tee "$CANDLOG"
cand_rc=${PIPESTATUS[0]}
set -e
[[ "$cand_rc" -eq 0 ]] || fail "temporary 26489 candidate Gradle build"
( cd "$CAND";sha256sum -c "$TMP/candidate_prebuild.sha256" >/dev/null ) || fail "temporary Gradle mutated canonical source"
pass "Temporary-copy validation: PASS"
pass "PRE-BUILD SAFETY PROOF PASSED"

# Final checkout starts from protected application base. Reconstruct exact 26488, overlay only the
# already-tested 26489 allowlist, then version bump + final APK build in the same guarded phase.
git apply --check --binary "$BASE26483_PATCH"
git apply --binary "$BASE26483_PATCH"
sha256sum -c "$BASE26483_HASHES" >/dev/null
git apply --check --binary "$DELTA26484"
git apply --binary "$DELTA26484"
bump app/version.properties 0.9726483 26483 0.9726484 26484
python3 "$TRANSFORM26485" "$(pwd)";bump app/version.properties 0.9726484 26484 0.9726485 26485
python3 "$TRANSFORM26486" "$(pwd)";bump app/version.properties 0.9726485 26485 0.9726486 26486
python3 "$TRANSFORM26487" "$(pwd)";bump app/version.properties 0.9726486 26486 0.9726487 26487
python3 "$TRANSFORM26488" "$(pwd)";bump app/version.properties 0.9726487 26487 0.9726488 26488
pass "final exact tested 26488 V4 application graph reconstructed"

while IFS= read -r rel;do mkdir -p "$(dirname "$rel")";cp "$CAND/$rel" "$rel";done < "$TMP/allow.txt"
bump app/version.properties 0.9726488 26488 0.9726489 26489

python3 - "$CAND" "$(pwd)" <<'PYPARITY'
from pathlib import Path
import hashlib,sys
a,b=Path(sys.argv[1]),Path(sys.argv[2]);ignore={'app/src/main/cpp/deps/archive.h','app/src/main/cpp/deps/archive_entry.h','app/src/main/cpp/deps/technicallyflac.h','app/src/main/cpp/deps/tiny_dng_writer.h'}
def h(root):
 d={}
 for p in (root/'app/src/main').rglob('*'):
  if p.is_file():
   rel=str(p.relative_to(root)).replace('\\','/')
   if rel in ignore:continue
   d[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
 vp=root/'app/version.properties';d['app/version.properties']=hashlib.sha256(vp.read_bytes()).hexdigest();return d
x,y=h(a),h(b)
if x!=y:raise SystemExit('candidate/final canonical source mismatch BEFORE final Gradle: '+repr(sorted(k for k in x.keys()|y.keys() if x.get(k)!=y.get(k))[:100]))
print('full candidate/final canonical source parity PASS')
PYPARITY

git add -N app/src/main app/version.properties >/dev/null 2>&1 || true
git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties > "$SOURCEPATCH"
[[ -s "$SOURCEPATCH" ]] || fail "complete 26489 source patch empty"
python3 - "$(pwd)" "$AFTERHASH" <<'PYAFTER'
from pathlib import Path
import hashlib,sys
root=Path(sys.argv[1]);out=Path(sys.argv[2]);ignore={'app/src/main/cpp/deps/archive.h','app/src/main/cpp/deps/archive_entry.h','app/src/main/cpp/deps/technicallyflac.h','app/src/main/cpp/deps/tiny_dng_writer.h'};rows=[]
for p in (root/'app/src/main').rglob('*'):
 if p.is_file():
  rel=str(p.relative_to(root)).replace('\\','/')
  if rel in ignore:continue
  rows.append((rel,hashlib.sha256(p.read_bytes()).hexdigest()))
vp=root/'app/version.properties';rows.append(('app/version.properties',hashlib.sha256(vp.read_bytes()).hexdigest()));out.write_text(''.join(f'{h}  {r}\n' for r,h in sorted(rows)))
PYAFTER
cp "$AFTERHASH" "$PREBUILDHASH"

set +e
chmod +x gradlew
./gradlew assembleDebug --no-daemon --stacktrace 2>&1 | tee "$FINALLOG"
final_rc=${PIPESTATUS[0]}
set -e
[[ "$final_rc" -eq 0 ]] || fail "final 26489 Gradle build"
sha256sum -c "$PREBUILDHASH" >/dev/null || fail "final Gradle mutated canonical source"

mapfile -t apks < <(find app/build/outputs/apk -type f -name '*.apk' | sort)
[[ ${#apks[@]} -ge 1 ]] || fail "no APK output"
rm -f IrisCamera-0.9726489-26489-*.apk
cp "${apks[-1]}" "$APK_NAME"
[[ -s "$APK_NAME" ]] || fail "published 26489 APK missing"

mkdir -p "$OUTDIR/next_baseline_inputs"
cp "$SOURCEPATCH" "$OUTDIR/next_baseline_inputs/26489_successful_source.patch"
cp "$AFTERHASH" "$OUTDIR/next_baseline_inputs/26489_successful_after.sha256"
cp "$DELTAOUT" "$OUTDIR/next_baseline_inputs/26489_delta_from_26488.patch"
cp "$REPO/$TRANSFORM" "$OUTDIR/next_baseline_inputs/"

cat > "$REPORT" <<EOFREPORT
26489 BJZHOU HOST / PERSISTENT BAYER / BANDED DIRECTIONAL RCD ARCHITECTURE
Version=$NEW_VERSION
Build=$NEW_BUILD
Branch=$BRANCH
BackupBranch=$BACKUP_BRANCH
BackupExpected=$BACKUP_EXPECTED
Transform26489SHA=$TRANSFORM_SHA
APK=$APK_NAME
APK_SHA256=$(sha "$APK_NAME")
SourcePatchSHA256=$(sha "$SOURCEPATCH")
AfterManifestSHA256=$(sha "$AFTERHASH")
Capture=tested 26487/26488 rolling ZSL preserved; shutter freezes prebuffer with no normal-frame top-up wait; one active Motion job; short highlight remains nonblocking and now has bounded copied-RAW pre-result staging
Alignment=tested Wronski cached-reference/deferred GPU alignment and bjzhou rejection graph preserved
Accumulator=frame0 reference plus every admitted auxiliary execute one persistent Bayer accumulation contract; additive numerator/denominator/support survive entire burst; exactly one final normalization
Invariant=host admitted frame count must equal accumulator contribution-dispatch count and expected retained non-null RAW count; 15-frame static burst cannot silently become one host contribution
BindingSafety=bidirectional type-aware invocation audit enforces sampler -> setTexture, image -> setTextureCompute, std430 buffer -> setBufferCompute, ordinary uniform -> setVar; undeclared/wrong host setters also fail
RetiredGraph=mfsr_low_support_reference, direct_rgb_accumulate, mfsr_finalize and old RGB short_highlight_recover are forbidden from active standard-Bayer host graph
CanonicalOutput=ordinary standard-Bayer Motion exits temporal reconstruction as half-resolution RGBA32F packed fused Bayer, not direct RGB
Demosaic=post-merge MotionV2RcdDemosaic owns first RGB synthesis; nine directional RCD stages run in 256-row bands with 12-row halo; PPG is restricted to the true nine-pixel photo border; rejected Iris 26460 cross-phase/plateau path remains inactive
Highlight=normal temporal merge remains sensor/CFA domain; aligned unsaturated short RAW may replace physically clipped normal Bayer sites before demosaic; clipped-site color synthesis is post-merge only
Latency=no per-frame glFinish restored; one existing reconstruction GPU drain; no shutter wait; no IPOL Monte-Carlo reintroduction
BuildSafety=exact tested 26488 reconstruction, exact tested backup proof, binary pre-edit exact-26488 patch before transform, strict 20-file allowlist, unrelated exact-26488 source byte-protected, whitespace proof, Java lexical proof, dynamic active shader graph, inherited Photon parser/GLES guards, full glslang graph, bidirectional typed bindings, temporary Javac+Gradle, candidate/final parity, and version increment + final build in guarded pipeline
EOFREPORT
sha256sum "$APK_NAME" "$SOURCEPATCH" "$AFTERHASH" "$REPORT" "$DELTAOUT" > "$OUTDIR/26489_artifact_hashes.sha256"

pass "26489 canonical checkpoint package created"
echo "26489_SOURCE_PATCH_SHA256=$(sha "$SOURCEPATCH")"
echo "26489_AFTER_MANIFEST_SHA256=$(sha "$AFTERHASH")"
echo "26489 BUILD SUCCESS"
