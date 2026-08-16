#!/usr/bin/env bash
set -euo pipefail

EXPECTED_BRANCH="experimental-clean-photon-rebuild"
EXPECTED_APP_BASE="8233415edf738bf35c0fe1c4907f5dfe51de31a4"
SUCCESSFUL_26490_HEAD="07c406502f2c33d771c2cbfcb7bda97076f986e2"
BACKUP_BRANCH="backup-26490-v3-tested-before-26491-adaptive-exposure-highlight-reconstruction"
FAILED_26491_V3_HEAD="d783b37a6f5a0f94a41b206d90f5c575f3ddceed"
INFRA_BACKUP_BRANCH="backup-26491-v3-failed-before-26491-v4-complete-architecture"
VALIDATOR_TRANSFORM="transform_26488_full_merge_rgb_rejection_contract_v1.py"
VALIDATOR_TRANSFORM_SHA="b7710d343aa26b1215178821983f4ff3f742ad07d1ca556de2d272fbc36664c0"
BASE_PATCH="26490_successful_source.patch"
BASE_PATCH_SHA="c589cc000047da6dd19c7b1ac71405fa635d75db37007fa526c60368001433ba"
BASE_HASHES="26490_successful_after.sha256"
BASE_HASHES_SHA="431a62d9e23cd17d71388d4b79ad0a0c548c58ae9eabb2ad1894ba9cad34322f"
TRANSFORM="transform_26491_complete_highlight_exposure_v4.py"
TRANSFORM_SHA="82b78d994b9657e36b202849f465061b2a4ada66822fa9f6b82d013935e37ed5"
NEW_VERSION="0.9726491"
NEW_BUILD="26491"
OUTDIR="build_26491_outputs"
APK_NAME="IrisCamera-${NEW_VERSION}-${NEW_BUILD}-v4-complete-highlight-exposure-debug.apk"

fail(){ echo "FAIL: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }

REPO="$(pwd)"
rm -rf "$OUTDIR"; mkdir -p "$OUTDIR"
AUDIT="$OUTDIR/26491_source_audit.txt"
JAVACLOG="$OUTDIR/26491_temporary_candidate_javac.log"
CANDLOG="$OUTDIR/26491_temporary_candidate_build.log"
FINALLOG="$OUTDIR/26491_final_build.log"
SHADERLOG="$OUTDIR/26491_shader_validation.txt"
REPORT="$OUTDIR/26491_build_report.txt"
PREPATCH="$OUTDIR/26491_pre_edit_exact_26490_binary.patch"
DELTAPATCH="$OUTDIR/26491_source.patch"
AFTERHASH="$OUTDIR/26491_after.sha256"
PREBUILDHASH="$OUTDIR/26491_prebuild_canonical.sha256"
exec > >(tee "$AUDIT") 2>&1

echo "=== 26491 V4 DIRECT FROM SUCCESSFUL 26490: COMPLETE MIDTONE/HDR AUTHORITY + JOINT CFA + NEUTRAL CENSOR + EXTENDED LINEAR + LEFT EDGE ==="
date -Iseconds || true

# GATE 0 — exact successful 26490 package identity. No historical reconstruction.
BRANCH="${GITHUB_REF_NAME:-$(git branch --show-current)}"
[[ "$BRANCH" != "dev" ]] || fail "dev is protected"
[[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || fail "wrong branch: $BRANCH"
git cat-file -e "$EXPECTED_APP_BASE^{commit}" || fail "verified app-base commit unavailable"
git cat-file -e "$SUCCESSFUL_26490_HEAD^{commit}" || fail "successful 26490 infrastructure HEAD unavailable"
git cat-file -e "$FAILED_26491_V3_HEAD^{commit}" || fail "failed 26491 V3 checkpoint unavailable"
git merge-base --is-ancestor "$SUCCESSFUL_26490_HEAD" HEAD || fail "successful 26490 commit is not an ancestor of this build"
git merge-base --is-ancestor "$FAILED_26491_V3_HEAD" HEAD || fail "26491 V4 must descend from the recorded failed V3 infrastructure checkpoint"
git diff --quiet "$EXPECTED_APP_BASE" -- app/src/main app/version.properties || \
  fail "committed app source no longer equals the protected application base"
[[ -f "$BASE_PATCH" && "$(sha "$BASE_PATCH")" == "$BASE_PATCH_SHA" ]] || fail "successful 26490 source patch identity mismatch"
[[ -f "$BASE_HASHES" && "$(sha "$BASE_HASHES")" == "$BASE_HASHES_SHA" ]] || fail "successful 26490 manifest identity mismatch"
[[ -f "$TRANSFORM" && "$(sha "$TRANSFORM")" == "$TRANSFORM_SHA" ]] || fail "26491 V4 transform identity mismatch"
[[ -f "$VALIDATOR_TRANSFORM" && "$(sha "$VALIDATOR_TRANSFORM")" == "$VALIDATOR_TRANSFORM_SHA" ]] || fail "proven 26488/26490 shader validator identity mismatch"
python3 -m py_compile "$TRANSFORM" "$VALIDATOR_TRANSFORM" || fail "26491 V4 transform/validator Python syntax"
python3 "$TRANSFORM" --self-test || fail "26491 transform self-test"
bash -n "$0" || fail "26491 build script syntax"
pass "exact successful-26490 direct-baseline package + proven shader-validator identity"

# GATE 1 — required pre-change backup exists and points to exact tested 26490.
remote="$(git ls-remote origin "refs/heads/$BACKUP_BRANCH" | awk '{print $1}')"
[[ "$remote" == "$SUCCESSFUL_26490_HEAD" ]] || \
  fail "backup branch $BACKUP_BRANCH=$remote expected=$SUCCESSFUL_26490_HEAD"
pass "fresh backup branch exact tested 26490 checkpoint"
infra_remote="$(git ls-remote origin "refs/heads/$INFRA_BACKUP_BRANCH" | awk '{print $1}')"
[[ "$infra_remote" == "$FAILED_26491_V3_HEAD" ]] || \
  fail "infrastructure backup branch $INFRA_BACKUP_BRANCH=$infra_remote expected=$FAILED_26491_V3_HEAD"
pass "fresh backup branch exact failed 26491 V3 checkpoint"

TMP="$(mktemp -d)"
BASE="$TMP/exact-successful-26490"
CAND="$TMP/candidate-26491"
PRETREE="$TMP/pre26491"
cleanup(){ set +e; git worktree remove --force "$BASE" >/dev/null 2>&1 || true; git worktree remove --force "$CAND" >/dev/null 2>&1 || true; rm -rf "$TMP"; }
trap cleanup EXIT

reconstruct_26490(){
  local dst="$1"
  git worktree add --detach "$dst" "$EXPECTED_APP_BASE" >/dev/null || fail "create clean base worktree"
  ( cd "$dst" && git apply --check --binary "$REPO/$BASE_PATCH" ) || fail "successful 26490 patch does not apply to verified app base"
  ( cd "$dst" && git apply --binary "$REPO/$BASE_PATCH" ) || fail "successful 26490 patch apply"
  ( cd "$dst" && sha256sum -c "$REPO/$BASE_HASHES" ) || fail "successful 26490 full manifest verification"
  grep -q '^VERSION_NAME=0\.9726490$' "$dst/app/version.properties" || fail "reconstructed baseline version is not 26490"
  grep -q '^VERSION_BUILD=26490$' "$dst/app/version.properties" || fail "reconstructed baseline build is not 26490"
  [[ "$(sha "$dst/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java")" == "9519d52fed6c12a1ef707e9d47b9111dafe901e9ab7c3918998841935decc111" ]] || fail "26490 merger hash mismatch"
  [[ "$(sha "$dst/app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl")" == "9c1cb82fc9c151eaaa7266d40eee63c0df193d3fdef9b911b193e89e9f454f65" ]] || fail "26490 short shader hash mismatch"
}

# GATE 2 — reconstruct exact successful 26490 twice: immutable baseline + candidate.
reconstruct_26490 "$BASE"
pass "baseline source PASS — exact successful 26490 artifact reconstructed"
mkdir -p "$PRETREE/app/src" "$PRETREE/app"
cp -a "$BASE/app/src/main" "$PRETREE/app/src/main"
cp "$BASE/app/version.properties" "$PRETREE/app/version.properties"
( cd "$BASE" && git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties ) > "$PREPATCH"
[[ -s "$PREPATCH" ]] || fail "26491 pre-edit exact-26490 patch is empty"
pass "binary pre-edit exact-26490 patch created before modification"

reconstruct_26490 "$CAND"
python3 "$REPO/$TRANSFORM" "$CAND" || fail "26491 transform dry-run/application"
pass "temporary transform application PASS"

cat > "$TMP/allowed-functional.txt" <<'EOF_ALLOWED'
app/src/main/assets/shaders/motionv2/rcd26489_populate.glsl
app/src/main/assets/shaders/motionv2/render.glsl
app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2RcdDemosaic.java
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java
EOF_ALLOWED

# GATE 3 — exact six-file functional scope and all other 26490 bytes protected.
python3 - "$PRETREE" "$CAND" "$TMP/allowed-functional.txt" <<'PY_ALLOW'
from pathlib import Path
import hashlib,sys
A,B=Path(sys.argv[1]),Path(sys.argv[2]); allowed=set(Path(sys.argv[3]).read_text().splitlines())
def hashes(root):
 out={}
 for p in (root/'app/src/main').rglob('*'):
  if p.is_file(): out[str(p.relative_to(root)).replace('\\','/')]=hashlib.sha256(p.read_bytes()).hexdigest()
 v=root/'app/version.properties'; out['app/version.properties']=hashlib.sha256(v.read_bytes()).hexdigest()
 return out
a,b=hashes(A),hashes(B); changed={p for p in set(a)|set(b) if a.get(p)!=b.get(p)}
if changed != allowed: raise SystemExit('changed-file allowlist mismatch\nactual='+repr(sorted(changed))+'\nexpected='+repr(sorted(allowed)))
print('changed-file allowlist PASS exactSixFunctionalFiles=true')
PY_ALLOW

python3 - "$REPO/$BASE_HASHES" "$CAND" "$TMP/allowed-functional.txt" <<'PY_PROTECTED'
from pathlib import Path
import hashlib,sys
manifest=Path(sys.argv[1]); root=Path(sys.argv[2]); allowed=set(Path(sys.argv[3]).read_text().splitlines())
for line in manifest.read_text().splitlines():
 if not line.strip(): continue
 expected,path=line.split(None,1); path=path.strip()
 if path in allowed: continue
 p=root/path
 if not p.is_file(): raise SystemExit('protected file missing: '+path)
 actual=hashlib.sha256(p.read_bytes()).hexdigest()
 if actual!=expected: raise SystemExit('protected successful-26490 hash changed: '+path)
print('protected successful-26490 hashes PASS')
PY_PROTECTED
pass "candidate scope + protected-source identity PASS"

# Restore the successful 26489/26490 rule: inherited whitespace in the replayed
# baseline is allowed, but 26491 may not introduce any NEW whitespace damage.
set +e
ws_out="$(git diff --no-index --check "$BASE/app/src/main" "$CAND/app/src/main" 2>&1)"
ws_rc=$?
set -e
[[ "$ws_rc" -eq 0 || "$ws_rc" -eq 1 ]] || fail "26491 scoped diff command failed rc=$ws_rc"
[[ -z "$ws_out" ]] || { echo "$ws_out" >&2; fail "26491 new whitespace damage"; }
pass "scoped exact-26490-to-26491 whitespace check"

# GATE 4 — producer/carrier/consumer ownership and regression proof.
MERGER="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java"
SHORT="$CAND/app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl"
RCD="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2RcdDemosaic.java"
RCDW="$CAND/app/src/main/assets/shaders/motionv2/rcd26489_write.glsl"
RCDP="$CAND/app/src/main/assets/shaders/motionv2/rcd26489_populate.glsl"
RENDER="$CAND/app/src/main/assets/shaders/motionv2/render.glsl"
POST="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java"
RECON="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"
CAP="$CAND/app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java"
WR="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java"
DISPLAY="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java"
RENDER_HOST="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java"
PARAMS="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java"
HDRX="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java"
UHDR="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java"

# New 26491 complete producer/carrier/consumer closure.
grep -q 'IRIS_26491_MIDTONES_GLOBAL_HIGHLIGHTS_LOCAL_HDR' "$MERGER" || fail "26491 midtone/HDR authority marker missing"
grep -q 'double referenceExposureEnergy' "$MERGER" || fail "reference exposure-energy input missing"
grep -q 'reference.motionV2ExposureEnergy' "$RECON" || fail "timestamp-owned reference exposure energy not carried to display estimator"
grep -q 'Math.min(candidateGain, illuminationCeiling)' "$MERGER" || fail "bright-scene illumination ceiling missing"
grep -q 'adaptiveReductionDiagnosticOnly=' "$MERGER" || fail "highlight-pressure diagnostic telemetry missing"
grep -q 'midtonesOwnGlobalExposure=true' "$MERGER" || fail "midtone global authority telemetry missing"
grep -q 'highlightsOwnLocalHdr=true' "$MERGER" || fail "local HDR authority telemetry missing"
! grep -q 'candidateGain \* adaptiveReduction' "$MERGER" || fail "highlight tail still globally darkens scene"
# Explicit producer -> carrier -> consumer closure: producer is MotionV2Merger, carrier is
# Parameters.motionV2DisplayGain, consumer is exactly the post-RCD display stage; render
# receives the resulting sensor-white coordinate only for headroom mapping.
grep -q 'parameters.motionV2DisplayGain =' "$RECON" || fail "display-gain carrier assignment missing"
grep -q 'MotionV2Merger.computeDisplayGain(' "$RECON" || fail "display-gain producer call missing"
[[ "$(grep -c 'motionV2DisplayGain' "$DISPLAY")" -eq 1 ]] || fail "display-gain consumer count changed"
grep -q 'glProg.setVar("displayGain", gain);' "$DISPLAY" || fail "post-RCD display-gain consumption missing"
[[ "$(grep -c 'motionV2DisplayGain' "$RENDER_HOST")" -eq 1 ]] || fail "render display-gain headroom reference count changed"
grep -q 'postDisplaySensorWhite' "$RENDER_HOST" || fail "render post-display sensor-white coordinate owner missing"
grep -q 'public float motionV2DisplayGain = 1.0f;' "$PARAMS" || fail "display-gain parameter carrier declaration changed"
grep -q 'processingParameters.motionV2DisplayGain = 1.0f;' "$HDRX" || fail "display-gain lifecycle reset changed"

grep -q 'IRIS_26491_JOINT_SHORT_HDR_SPATIAL_CHROMATICITY' "$SHORT" || fail "joint spatial short-HDR marker missing"
grep -q 'boundaryCoherence' "$SHORT" || fail "short-HDR object/reflection boundary gate missing"
grep -q 'weightedShort' "$SHORT" || fail "spatial short-HDR consensus missing"
grep -q 'vec4 useShort = normalClip \* (flowGate \* jointConfidence);' "$SHORT" || fail "joint scalar CFA confidence gate missing"
! grep -q 'normalClip \* shortSafe' "$SHORT" || fail "independent per-CFA phase short substitution survived"
grep -q 'vec4 recovered = max(normal, recoveredEstimate);' "$SHORT" || fail "censored-normal lower bound lost in short recovery"
grep -q 'selectedShort \* shortToNormalScale \* referenceExposureScale' "$SHORT" || fail "actual short radiometry scale lost"
grep -q 'float flowConfidence = (1.0 - cancelled) \* exp(-80.0 \* variation);' "$SHORT" || fail "26490 short flow confidence math changed"
grep -q 'float flowGate = smoothstep(minimumFlowConfidence, 0.80, flowConfidence);' "$SHORT" || fail "26490 short flow gate changed"

grep -q 'IRIS_26491_NEUTRAL_CENSORED_FALLBACK' "$RCDP" || fail "neutral censored fallback marker missing"
grep -q 'uniform vec3 sensorGains;' "$RCDP" || fail "neutral fallback sensor-gain domain input missing"
grep -q 'packedExtendedEvidence' "$RCDP" || fail "measured short extended-radiance protection missing"
grep -q 'chromaRecoverable' "$RCDP" || fail "recoverable-vs-censored color decision missing"
grep -q 'safeSpread <= 0.28' "$RCDP" || fail "same-surface packed chroma gate missing"
grep -q 'relative > 0.35' "$RCDP" || fail "strong local object/reflection boundary rejection missing"
grep -q 'neutralLowerBound \* wbForColor(col) / max(gainForColor(col), 1.0e-6)' "$RCDP" || fail "neutral brightness-preserving conversion missing"
grep -q 'IRIS_26491_NEUTRAL_CENSOR_SENSOR_GAIN_BRIDGE' "$RCD" || fail "neutral fallback host bridge missing"
grep -q 'glProg.setVar("sensorGains", gains\[0\], greenGain, gains\[3\]);' "$RCD" || fail "timestamp-owned sensor gain binding missing"

grep -q 'IRIS_26491_EXTENDED_LINEAR_CHROMA_PRESERVING_HIGHLIGHT_COMPRESSION' "$RENDER" || fail "26491 extended-linear compression marker missing"
grep -q 'IRIS_26480_MAX_RGB_HIGHLIGHT_TONE_GUIDE_V2' "$RENDER" || fail "proven max-RGB headroom guide lost"
grep -q 'return rgb\*(mappedGuide/guide);' "$RENDER" || fail "highlight compression no longer one chroma-preserving scalar"
grep -q 'IRIS_26491_FINAL_OUTPUT_LEFT_EDGE_MIRROR_ONE_PIXEL' "$RENDER" || fail "one-pixel final left-edge fix missing"
grep -q 'if(sourceXY.x==0 && sourceSize.x>1) sourceXY.x=1;' "$RENDER" || fail "left edge does not mirror x1 only"
grep -q 'applyReferenceSafeMicrocontrast(sourceXY,linearSrgb)' "$RENDER" || fail "left-edge source/microcontrast parity missing"

# Proven 26490 architecture and the user's protected invariants remain present/byte-protected.
grep -q 'IRIS_26490_RCD_EXPOSURE_DOMAIN' "$RCD" || fail "physical RCD exposure domain lost"
grep -q 'iris26490PhysicalSensorWhite = 1.0f' "$RCD" || fail "physical sensor white no longer 1.0"
grep -q 'IRIS_26490_PHYSICAL_CENSORING_WITH_LOWER_BOUND' "$RCDP" || fail "26490 physical censor/lower-bound contract lost"
grep -q 'IRIS_26490_BJZHOU_RCD_PHOTO_BORDER_MIRROR_1TO1' "$RCDW" || fail "successful four-edge RCD mirror lost"
[[ "$(sha "$RCDW")" == "78b9894e40d584b9bc9abce69c13cdd7057a51fc99e825c6581183d762c882ec" ]] || fail "26490 four-edge RCD write shader bytes changed"
grep -q 'IRIS_26489_FUSED_BAYER_CANONICAL_POST_GRAPH' "$POST" || fail "canonical Motion post graph lost"
grep -q 'IRIS_26489_BJZHOU_PERSISTENT_BAYER_ACCUMULATOR_OWNER' "$CAND/app/src/main/assets/shaders/motionv2/mfsr_bayer_accumulate.glsl" || fail "persistent R32F Bayer accumulator owner lost"
grep -q 'IRIS_26489_ACCUMULATOR_INVARIANT_PASS' "$RECON" || fail "admitted/contributed/expected invariant lost"
grep -q 'IRIS_26490_SHORT_CAPTURE_STARTED_IDENTITY' "$CAP" || fail "exact short capture identity owner lost"
grep -q 'IRIS_26486_FREEZE_BUFFER_AT_SHUTTER_NO_TOPUP_WAIT' "$CAP" || fail "fast no-top-up shutter architecture lost"
! grep -q 'add(new MotionV2Denoise());' "$POST" || fail "MotionV2Denoise re-enabled"
# The exact-six-file allowlist already byte-protects every other app file. These named
# checks make the user-requested invariants explicit in the audit report.
cmp -s "$BASE/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java" "$WR" || fail "Wronski alignment bytes changed"
cmp -s "$BASE/app/src/main/assets/shaders/motionv2/mfsr_bayer_accumulate.glsl" "$CAND/app/src/main/assets/shaders/motionv2/mfsr_bayer_accumulate.glsl" || fail "R32F accumulator bytes changed"
cmp -s "$BASE/app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java" "$UHDR" || fail "UHDR owner bytes changed"
cmp -s "$BASE/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java" "$POST" || fail "Motion post graph/denoise/sharpening ownership changed"
pass "complete 26491 authority closure + protected Motion architecture PASS"

# Exact shader host interface must be unchanged by 26491; only decision math may change.
python3 - "$BASE/app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl" "$SHORT" <<'PY_IFACE'
from pathlib import Path
import re,sys
a,b=[Path(x).read_text() for x in sys.argv[1:3]]
def iface(t):
 out=[]
 for line in t.splitlines():
  s=line.strip()
  if s.startswith('uniform ') or (' uniform ' in (' '+s) and 'image2D outCfa' in s): out.append(s)
 return sorted(out)
if iface(a)!=iface(b):
 raise SystemExit('short shader host interface changed\nBEFORE='+repr(iface(a))+'\nAFTER='+repr(iface(b)))
for token in ('normalCfa','shortCfa','flowTexture','outCfa','packedSize','referenceExposureScale','shortToNormalScale','physicalClipThreshold','shortClipThreshold','minimumFlowConfidence'):
 if token not in b: raise SystemExit('short interface token missing: '+token)
print('short shader host interface byte-semantics PASS')
PY_IFACE
# Render gains no new host interface; this catches accidental uniform drift because the
# inherited 49-call audit is compute-owner based and does not include MotionV2Render.
python3 - "$BASE/app/src/main/assets/shaders/motionv2/render.glsl" "$RENDER" <<'PY_RENDER_IFACE'
from pathlib import Path
import re,sys
a,b=[Path(x).read_text() for x in sys.argv[1:3]]
def uniforms(t):
 return sorted(x.strip() for x in t.splitlines() if x.strip().startswith('uniform '))
if uniforms(a)!=uniforms(b):
 raise SystemExit('render shader host interface changed\nBEFORE='+repr(uniforms(a))+'\nAFTER='+repr(uniforms(b)))
for token in ('InputBuffer','sceneWhite','outputExposureScale'):
 if token not in b: raise SystemExit('render interface token missing: '+token)
print('render shader host interface PASS unchanged')
PY_RENDER_IFACE

# GATE 5 — restore the complete successful-26489/26490 shader portability procedure.
# 5A: fail on the known reserved-identifier class BEFORE invoking glslang.
python3 - "$SHORT" "$RCDP" "$RENDER" <<'PY_RESERVED_CHANGED'
from pathlib import Path
import re,sys
reserved=('sample','common','coherent','precision','packed')
for arg in sys.argv[1:]:
 src=Path(arg).read_text(); clean=re.sub(r'//.*','',re.sub(r'/\*.*?\*/','',src,flags=re.S))
 bad=re.search(r'\b(?:float|vec[234]|int|ivec[234]|uint|uvec[234]|bool|mat[234])\s+('+'|'.join(reserved)+r')\b',clean)
 if bad: raise SystemExit('reserved GLSL identifier declaration '+bad.group(1)+' in '+arg)
if 'vec4 sharedShortSafe = centerShortSafe * neighborShortSafe;' not in Path(sys.argv[1]).read_text():
 raise SystemExit('joint short shared-phase portability owner missing')
if 'ivec2 packedCoord = clampGlobal(p) >> 1;' not in Path(sys.argv[2]).read_text():
 raise SystemExit('RCD packedCoord reserved-word avoidance missing')
print('26491 V4 changed-shader reserved-identifier preflight PASS shaders=3')
PY_RESERVED_CHANGED

# 5B: derive the exact active Motion shader graph from the same three owners used by successful 26490.
python3 - "$CAND" "$RECON" "$WR" "$RCD" "$TMP/compute_shaders.txt" "$TMP/fragment_shaders.txt" <<'PY_GRAPH'
from pathlib import Path
import re,sys
root=Path(sys.argv[1]); owners=[Path(x) for x in sys.argv[2:5]]; compute=set(); fragment=set(); invocations=0
for owner in owners:
 java=owner.read_text()
 for m in re.finditer(r'useAssetProgram\(\s*"motionv2/([^"]+)"(?:\s*,\s*(true|false))?\s*\)',java):
  invocations+=1; name,flag=m.group(1),m.group(2); rel=f'app/src/main/assets/shaders/motionv2/{name}.glsl'
  if not (root/rel).is_file(): raise SystemExit('active Motion shader missing: '+rel)
  (compute if flag=='true' else fragment).add(rel)
if compute & fragment: raise SystemExit('shader loaded as both compute and fragment: '+repr(sorted(compute&fragment)))
if invocations != 49: raise SystemExit(f'26491 expected inherited 49 literal Motion shader invocations, got {invocations}')
Path(sys.argv[5]).write_text(''.join(x+'\n' for x in sorted(compute)))
Path(sys.argv[6]).write_text(''.join(x+'\n' for x in sorted(fragment)))
print(f'26491 V4 active Motion graph PASS invocations={invocations} compute={len(compute)} fragment={len(fragment)}')
PY_GRAPH

# 5C: the same bidirectional Photon host-binding type audit used by successful 26490.
python3 - "$CAND" "$RECON" "$WR" "$RCD" <<'PY_BIND'
from pathlib import Path
import re,sys
root=Path(sys.argv[1]);owners=[Path(x) for x in sys.argv[2:]];problems=[];invocations=0
def strip(s): return re.sub(r'//.*','',re.sub(r'/\*.*?\*/','',s,flags=re.S))
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
if problems: raise SystemExit('26491 V4 TYPE-AWARE BINDING FAILURE: '+repr(problems))
if invocations != 49: raise SystemExit(f'26491 expected 49 literal Motion shader invocations, got {invocations}')
print(f'26491 V4 TYPE-AWARE BINDING PASS invocations={invocations} bufferContracts=true')
PY_BIND

# 5D: GLES image memory-qualifier audit before compiler invocation.
python3 - "$CAND" "$TMP/compute_shaders.txt" <<'PY_MEMQUAL'
from pathlib import Path
import re,sys
root=Path(sys.argv[1]);listing=Path(sys.argv[2]);formats={'rgba32f','rgba16f','r32f','rgba8','rgba8_snorm','rgba32i','rgba16i','rgba8i','r32i','rgba32ui','rgba16ui','rgba8ui','r32ui'};rw_exempt={'r32f','r32i','r32ui'};problems=[]
def strip(source): return re.sub(r'//.*','',re.sub(r'/\*.*?\*/','',source,flags=re.S))
for rel in listing.read_text().splitlines():
 if not rel.strip(): continue
 source=strip((root/rel).read_text())
 for no,line in enumerate(source.splitlines(),1):
  if 'layout' not in line or 'uniform' not in line or 'image2D' not in line: continue
  lm=re.search(r'layout\s*\(([^)]*)\)',line);vm=re.search(r'\b(?:uimage2D|iimage2D|image2D)\s+([A-Za-z_]\w*)',line)
  if not lm or not vm: continue
  args=[x.strip() for x in lm.group(1).split(',')];fmt=next((x for x in args if x in formats),None)
  if fmt is None: continue
  var=vm.group(1);ro=bool(re.search(r'\breadonly\b',line));wo=bool(re.search(r'\bwriteonly\b',line));loads=bool(re.search(r'\bimageLoad\s*\(\s*'+re.escape(var)+r'\b',source));stores=bool(re.search(r'\bimageStore\s*\(\s*'+re.escape(var)+r'\b',source))
  if fmt not in rw_exempt and not (ro or wo):problems.append((rel,no,var,fmt,'missing readonly/writeonly'))
  if ro and stores:problems.append((rel,no,var,fmt,'readonly imageStore'))
  if wo and loads:problems.append((rel,no,var,fmt,'writeonly imageLoad'))
  if loads and stores and fmt not in rw_exempt:problems.append((rel,no,var,fmt,'read+write requires r32f/r32i/r32ui'))
if problems: raise SystemExit('26491 V4 GLES IMAGE MEMORY QUALIFIER FAILURE: '+repr(problems))
print('26491 V4 GLES image memory qualifier PASS activeCompute='+str(len([x for x in listing.read_text().splitlines() if x.strip()])))
PY_MEMQUAL

# 5E: restore the proven 26488/26490 Photon runtime parser + reserved-name + image-store validators.
python3 - "$CAND" "$TMP/compute_shaders.txt" "$VALIDATOR_TRANSFORM" <<'PY_VALID'
from pathlib import Path
import importlib.util,re,sys
root=Path(sys.argv[1]);listing=Path(sys.argv[2]);transform=Path(sys.argv[3]);spec=importlib.util.spec_from_file_location('iris26488_validators',transform);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
shaders={rel:(root/rel).read_text() for rel in listing.read_text().splitlines() if rel.strip()}
legacy={rel:text for rel,text in shaders.items() if ' buffer ' not in text}
m.validate_photon_runtime_layout_parser(legacy)
for rel,text in shaders.items():
 runtime=text.replace('#define LAYOUT //','#define LAYOUT layout(local_size_x = 8, local_size_y = 8, local_size_z = 1) in;',1);names=set();saw_local=False
 for no,line in enumerate(runtime.splitlines(),1):
  if 'layout' not in line:continue
  if line.count('layout(')!=1:raise SystemExit(f'Photon getLayouts multi-layout hazard {rel}:{no}: {line}')
  stripped=line.strip()
  if not (stripped.startswith('layout(') or stripped.startswith('#define LAYOUT layout(')):raise SystemExit(f'Photon getLayouts prefix hazard {rel}:{no}: {line}')
  left=line.find('(');right=line.rfind(')')
  if left<0 or right<=left:raise SystemExit(f'Photon getLayouts parentheses hazard {rel}:{no}')
  parts=[x for x in line.replace('{','').split(' ') if x!=''];last=(parts[-1] if parts else '').replace(';','').replace('\n','');params=line[left+1:right].split(',')
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
print('26491 V4 Photon parser + GLSL reserved-name + GLES image-format validators PASS')
PY_VALID

# Extra explicit successful-26490 lexical/Adreno guard over every active shader.
cat "$TMP/compute_shaders.txt" "$TMP/fragment_shaders.txt" | sort -u > "$TMP/all_active_shaders.txt"
while IFS= read -r rel; do
 [[ -n "$rel" ]] || continue; f="$CAND/$rel"
 ! grep -Eq 'layout\((rg32f|rg16f|r16f|r16ui|rg16ui)[^)]*\)[^;]*(u?image2D|iimage2D)' "$f" || fail "GLES/Adreno hazardous writable image format $(basename "$f")"
 ! grep -Eq '\b(float|vec[234]|int|ivec[234]|uint|uvec[234]|bool|mat[234])\s+(sample|common|coherent|precision|packed)\b' "$f" || fail "reserved GLSL identifier declaration in $(basename "$f")"
done < "$TMP/all_active_shaders.txt"
pass "successful-26490 reserved-name + Adreno writable-format lexical guards"

# 5F: REAL glslang compile of the entire active Motion graph, not just the changed shader.
: > "$SHADERLOG"
compile_compute(){
 local f="$1" tmp="$2"
 python3 - "$f" "$tmp" <<'PY_COMP'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text();needle='#define LAYOUT //\nLAYOUT'
if needle not in s:raise SystemExit('missing Photon LAYOUT header')
s=s.replace(needle,'#version 310 es\nlayout(local_size_x=8,local_size_y=8,local_size_z=1) in;',1);Path(sys.argv[2]).write_text(s)
PY_COMP
 glslangValidator -S comp "$tmp" >> "$SHADERLOG" 2>&1
}
compile_fragment(){
 local f="$1" tmp="$2"
 python3 - "$f" "$tmp" <<'PY_FRAG'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text();needle='#define LAYOUT //\nLAYOUT'
if needle not in s:raise SystemExit('missing Photon LAYOUT header')
s=s.replace(needle,'#version 300 es',1);Path(sys.argv[2]).write_text(s)
PY_FRAG
 glslangValidator -S frag "$tmp" >> "$SHADERLOG" 2>&1
}
command -v glslangValidator >/dev/null 2>&1 || fail "glslangValidator unavailable; workflow must install glslang-tools"
shader_fail=0
while IFS= read -r rel;do [[ -n "$rel" ]]||continue;n="$(basename "$rel")";if compile_compute "$CAND/$rel" "$TMP/$n.comp";then echo "COMPUTE PASS $n" >> "$SHADERLOG";else echo "COMPUTE FAIL $n" >> "$SHADERLOG";shader_fail=1;fi;done < "$TMP/compute_shaders.txt"
while IFS= read -r rel;do [[ -n "$rel" ]]||continue;n="$(basename "$rel")";if compile_fragment "$CAND/$rel" "$TMP/$n.frag";then echo "FRAGMENT PASS $n" >> "$SHADERLOG";else echo "FRAGMENT FAIL $n" >> "$SHADERLOG";shader_fail=1;fi;done < "$TMP/fragment_shaders.txt"
if [[ "$shader_fail" -ne 0 ]]; then cat "$SHADERLOG"; fail "one or more active 26491 V4 Motion shaders failed glslangValidator"; fi
grep -q 'COMPUTE PASS short_highlight_bayer_recover.glsl' "$SHADERLOG" || fail "changed short shader missing from full active graph glslang PASS"
grep -q 'COMPUTE PASS rcd26489_populate.glsl' "$SHADERLOG" || fail "changed RCD populate shader missing from full active graph glslang PASS"
# MotionV2Render is a postpipeline fragment program and is not part of the 49 compute-owner
# invocations above. Compile the changed render shader explicitly under GLES 3.0.
python3 - "$RENDER" "$TMP/26491_render.frag" <<'PY_RENDER_COMPILE'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text()
if '#version' in s: raise SystemExit('unexpected embedded #version in Photon render shader')
Path(sys.argv[2]).write_text('#version 300 es\n'+s)
PY_RENDER_COMPILE
if glslangValidator -S frag "$TMP/26491_render.frag" >> "$SHADERLOG" 2>&1; then
 echo "FRAGMENT PASS render.glsl" >> "$SHADERLOG"
else
 echo "FRAGMENT FAIL render.glsl" >> "$SHADERLOG"; cat "$SHADERLOG"; fail "changed render shader glslang compile"
fi
grep -q 'FRAGMENT PASS render.glsl' "$SHADERLOG" || fail "changed render shader did not pass real glslang"
cat "$SHADERLOG"
pass "complete active Motion graph + all three changed shaders real glslangValidator PASS"

# GATE 6 — Java lexical sanity + parse/compile candidate before full candidate APK.
python3 - "$MERGER" "$RECON" "$RCD" <<'PY_JAVA'
from pathlib import Path
import sys
for arg in sys.argv[1:]:
 s=Path(arg).read_text()
 if s.count('{')!=s.count('}'): raise SystemExit('Java brace mismatch: '+arg)
 if '\x00' in s: raise SystemExit('NUL in changed Java owner: '+arg)
merger=Path(sys.argv[1]).read_text(); recon=Path(sys.argv[2]).read_text(); rcd=Path(sys.argv[3]).read_text()
if 'IRIS_26491_MIDTONES_GLOBAL_HIGHLIGHTS_LOCAL_HDR' not in merger: raise SystemExit('26491 exposure marker absent')
if 'reference.motionV2ExposureEnergy' not in recon: raise SystemExit('26491 exposure-energy carrier absent')
if 'IRIS_26491_NEUTRAL_CENSOR_SENSOR_GAIN_BRIDGE' not in rcd: raise SystemExit('26491 neutral-censor bridge absent')
print('26491 V4 changed Java lexical sanity PASS files=3')
PY_JAVA
cat > "$TMP/ParseJava26491V4.java" <<'JAVA_PARSE_HELPER'
import java.nio.charset.StandardCharsets;
import java.util.*;
import javax.tools.*;
import com.sun.source.util.JavacTask;
public final class ParseJava26491V4 {
 public static void main(String[] args) throws Exception {
  JavaCompiler compiler=ToolProvider.getSystemJavaCompiler(); if(compiler==null) throw new IllegalStateException("system javac unavailable");
  DiagnosticCollector<JavaFileObject> diagnostics=new DiagnosticCollector<>();
  StandardJavaFileManager fm=compiler.getStandardFileManager(diagnostics,Locale.ROOT,StandardCharsets.UTF_8);
  Iterable<? extends JavaFileObject> files=fm.getJavaFileObjectsFromStrings(Arrays.asList(args));
  JavacTask task=(JavacTask)compiler.getTask(null,fm,diagnostics,List.of("-proc:none","-source","17"),null,files);int units=0;
  try{for(var ignored:task.parse())units++;}finally{fm.close();}
  boolean failed=false;for(Diagnostic<? extends JavaFileObject>d:diagnostics.getDiagnostics()){if(d.getKind()==Diagnostic.Kind.ERROR){failed=true;System.err.println(d);}}
  if(failed)throw new IllegalStateException("Java parse errors");if(units!=args.length)throw new IllegalStateException("parsed units="+units+" expected="+args.length);
  System.out.println("26491 V4 JAVAC PARSE PASS units="+units);
 }
}
JAVA_PARSE_HELPER
javac -d "$TMP/java_parse_gate" "$TMP/ParseJava26491V4.java"
java -cp "$TMP/java_parse_gate" ParseJava26491V4 "$MERGER" "$RECON" "$RCD"
pass "JDK JavacTask parse-only AST gate for all three changed Java owners"
(
 cd "$CAND"
 chmod +x ./gradlew
 ./gradlew :app:compileDebugJavaWithJavac --no-daemon
) 2>&1 | tee "$JAVACLOG"
[[ "${PIPESTATUS[0]}" -eq 0 ]] || fail "temporary candidate javac"
grep -q 'BUILD SUCCESSFUL' "$JAVACLOG" || fail "temporary candidate javac did not report BUILD SUCCESSFUL"
pass "temporary candidate Java compile PASS"

# Full transformed candidate must build before live Actions source is touched.
(
 cd "$CAND"
 ./gradlew clean assembleDebug --no-daemon
) 2>&1 | tee "$CANDLOG"
[[ "${PIPESTATUS[0]}" -eq 0 ]] || fail "full temporary candidate Gradle build"
grep -q 'BUILD SUCCESSFUL' "$CANDLOG" || fail "temporary candidate did not report BUILD SUCCESSFUL"
pass "Gradle compile/assemble PASS — full temporary candidate"

# Known CMake build-time downloads are generated inputs, not canonical source.
cat > "$TMP/generated-native-deps.txt" <<'EOF_DEPS'
app/src/main/cpp/deps/archive.h
app/src/main/cpp/deps/archive_entry.h
app/src/main/cpp/deps/technicallyflac.h
app/src/main/cpp/deps/tiny_dng_writer.h
EOF_DEPS
while IFS= read -r rel; do
  ! grep -Fq "  $rel" "$BASE_HASHES" || fail "generated native dep entered canonical 26490 manifest: $rel"
  [[ ! -e "$PRETREE/$rel" ]] || fail "generated native dep exists in canonical 26490 tree: $rel"
  [[ -f "$CAND/$rel" ]] || fail "candidate build did not materialize native dep: $rel"
done < "$TMP/generated-native-deps.txt"
while IFS= read -r rel; do sha256sum "$CAND/$rel"; done < "$TMP/generated-native-deps.txt" > "$OUTDIR/26491_candidate_generated_native_deps.sha256"

python3 - "$REPO/$BASE_HASHES" "$CAND" "$TMP/allowed-functional.txt" <<'PY_POSTCAND'
from pathlib import Path
import hashlib,sys
manifest=Path(sys.argv[1]); root=Path(sys.argv[2]); allowed=set(Path(sys.argv[3]).read_text().splitlines())
for line in manifest.read_text().splitlines():
 if not line.strip(): continue
 expected,path=line.split(None,1); path=path.strip()
 if path in allowed: continue
 p=root/path
 if not p.is_file(): raise SystemExit('post-candidate protected file missing: '+path)
 if hashlib.sha256(p.read_bytes()).hexdigest()!=expected: raise SystemExit('post-candidate protected hash changed: '+path)
print('post-candidate canonical source hashes PASS')
PY_POSTCAND
pass "Temporary-copy validation: PASS"

# GATE 7 — only after candidate passes, reconstruct exact 26490 in live ephemeral workspace.
git apply --check --binary "$BASE_PATCH" || fail "live successful-26490 baseline apply check"
git apply --binary "$BASE_PATCH" || fail "live successful-26490 baseline apply"
sha256sum -c "$BASE_HASHES" || fail "live successful-26490 baseline manifest"
pass "live exact successful 26490 baseline PASS"

while IFS= read -r rel; do cp "$CAND/$rel" "$rel"; done < "$TMP/allowed-functional.txt"
while IFS= read -r rel; do cmp -s "$CAND/$rel" "$rel" || fail "candidate/live mismatch: $rel"; done < "$TMP/allowed-functional.txt"
# Do NOT run a broad live-tree diff --check here. Exact 26490 intentionally carries a few
# historical whitespace lines, and V3 proved that comparing the replay against the old app
# commit creates a false failure. The authoritative baseline->candidate scoped check above
# already proved that 26491 introduced no new whitespace damage.
pass "candidate/source byte equality PASS; scoped whitespace proof retained"

python3 - "$PRETREE" "$REPO" "$TMP/allowed-functional.txt" <<'PY_LIVE'
from pathlib import Path
import hashlib,sys
A,B=Path(sys.argv[1]),Path(sys.argv[2]); allowed=set(Path(sys.argv[3]).read_text().splitlines())
def h(root):
 out={}
 for p in (root/'app/src/main').rglob('*'):
  if p.is_file(): out[str(p.relative_to(root)).replace('\\','/')]=hashlib.sha256(p.read_bytes()).hexdigest()
 v=root/'app/version.properties'; out['app/version.properties']=hashlib.sha256(v.read_bytes()).hexdigest(); return out
a,b=h(A),h(B); changed={p for p in set(a)|set(b) if a.get(p)!=b.get(p)}
if changed!=allowed: raise SystemExit('live pre-version scope mismatch: '+repr(sorted(changed)))
print('live pre-version exact six-file functional scope PASS')
PY_LIVE

find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$PREBUILDHASH"
sha256sum app/version.properties >> "$PREBUILDHASH"

pass "PRE-BUILD SAFETY PROOF PASSED"
echo "  exact successful 26490 GitHub artifact patch + full manifest PASS"
echo "  tested-26490 backup exact SHA PASS"
echo "  failed-26491-V3 backup exact SHA PASS"
echo "  binary pre-edit exact-26490 patch before source modification PASS"
echo "  generated temporary candidate before live source mutation PASS"
echo "  exact six-file functional allowlist PASS"
echo "  all unrelated 26490 canonical source byte-protected PASS"
echo "  scoped 26490->26491 whitespace check PASS; inherited whitespace ignored correctly"
echo "  exposure producer/carrier/consumer chain explicitly closed PASS"
echo "  midtones + exposure-energy sanity decide global scene gain PASS"
echo "  highlight occupancy/true clipping are local-HDR telemetry only PASS"
echo "  joint short-HDR CFA reconstruction; no independent phase substitution PASS"
echo "  spatial short chromaticity consensus + strong boundary rejection PASS"
echo "  neutral brightness-preserving censored fallback PASS"
echo "  extended-linear chroma-preserving high-luminance compression PASS"
echo "  final x0 one-pixel left-edge mirror fix PASS"
echo "  exact 26490 short capture/flow/radiometry preserved PASS"
echo "  Wronski/R32F accumulator/rejection/15-frame architecture byte-protected PASS"
echo "  MotionBatch/short isolation/ghosting architecture byte-protected PASS"
echo "  successful four-edge RCD write/mirror bytes unchanged PASS"
echo "  UHDR/PostPipeline/denoise/ESD/sharpening owners byte-protected PASS"
echo "  changed-shader reserved GLSL identifiers preflight PASS"
echo "  inherited 49-invocation type-aware binding audit PASS"
echo "  Photon parser/GLES image legality PASS"
echo "  complete active Motion graph + all changed shaders real glslang PASS"
echo "  all three changed Java owners JDK parse PASS"
echo "  candidate Javac + full temporary candidate Gradle PASS"
echo "  candidate/live functional bytes equal before final build PASS"
echo "  version/build increment is last and in same guarded final Gradle command block PASS"

# VERSION IS LAST; increment and final APK build are one guarded command block.
(
python3 - <<'PY_VERSION'
from pathlib import Path
p=Path('app/version.properties'); t=p.read_text()
if t.count('VERSION_NAME=0.9726490')!=1 or t.count('VERSION_BUILD=26490')!=1:
 raise SystemExit('version baseline anchors are not exact 26490')
t=t.replace('VERSION_NAME=0.9726490','VERSION_NAME=0.9726491',1)
t=t.replace('VERSION_BUILD=26490','VERSION_BUILD=26491',1)
p.write_text(t)
print('version/build incremented to 0.9726491 / 26491')
PY_VERSION
./gradlew clean assembleDebug --no-daemon
) 2>&1 | tee "$FINALLOG"
[[ "${PIPESTATUS[0]}" -eq 0 ]] || fail "final 26491 Gradle build"
grep -q 'BUILD SUCCESSFUL' "$FINALLOG" || fail "final Gradle did not report BUILD SUCCESSFUL"
pass "final APK Gradle build PASS"

# Candidate/final generated native bytes must match; then remove them before canonical packaging.
python3 - "$CAND" "$REPO" "$TMP/generated-native-deps.txt" <<'PY_DEPS'
from pathlib import Path
import hashlib,sys
cand,live=Path(sys.argv[1]),Path(sys.argv[2])
for rel in [x for x in Path(sys.argv[3]).read_text().splitlines() if x]:
 a,b=cand/rel,live/rel
 if not a.is_file() or not b.is_file(): raise SystemExit('generated native dependency missing: '+rel)
 ha,hb=hashlib.sha256(a.read_bytes()).hexdigest(),hashlib.sha256(b.read_bytes()).hexdigest()
 if ha!=hb: raise SystemExit(f'candidate/final generated dep mismatch: {rel} {ha} {hb}')
 print(f'generated native dependency byte equality PASS: {rel} {ha}')
PY_DEPS
while IFS= read -r rel; do rm -f "$rel"; [[ ! -e "$rel" ]] || fail "generated dep cleanup failed: $rel"; done < "$TMP/generated-native-deps.txt"

# GATE 8 — post-build source immutability and exact final seven-file delta.
python3 - "$REPO/$BASE_HASHES" "$REPO" "$TMP/allowed-functional.txt" <<'PY_POSTFINAL'
from pathlib import Path
import hashlib,sys
manifest=Path(sys.argv[1]); root=Path(sys.argv[2]); allowed=set(Path(sys.argv[3]).read_text().splitlines()); allowed.add('app/version.properties')
for line in manifest.read_text().splitlines():
 if not line.strip(): continue
 expected,path=line.split(None,1); path=path.strip()
 if path in allowed: continue
 p=root/path
 if not p.is_file(): raise SystemExit('post-final protected file missing: '+path)
 if hashlib.sha256(p.read_bytes()).hexdigest()!=expected: raise SystemExit('post-final protected hash changed: '+path)
print('post-final canonical source hashes PASS')
PY_POSTFINAL
# Gradle is not permitted to rewrite any of the six functional owners.
while IFS= read -r rel; do cmp -s "$CAND/$rel" "$rel" || fail "final Gradle mutated functional source: $rel"; done < "$TMP/allowed-functional.txt"
grep -q '^VERSION_NAME=0\.9726491$' app/version.properties || fail "final version name not 0.9726491"
grep -q '^VERSION_BUILD=26491$' app/version.properties || fail "final version build not 26491"
pass "post-final six functional files byte-equal candidate + version exact"

cat > "$TMP/allowed-final.txt" <<'EOF_FINAL'
app/src/main/assets/shaders/motionv2/rcd26489_populate.glsl
app/src/main/assets/shaders/motionv2/render.glsl
app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2RcdDemosaic.java
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java
app/version.properties
EOF_FINAL
python3 - "$PRETREE" "$REPO" "$TMP/allowed-final.txt" <<'PY_FINAL'
from pathlib import Path
import hashlib,sys
A,B=Path(sys.argv[1]),Path(sys.argv[2]); allowed=set(Path(sys.argv[3]).read_text().splitlines())
def h(root):
 out={}
 for p in (root/'app/src/main').rglob('*'):
  if p.is_file(): out[str(p.relative_to(root)).replace('\\','/')]=hashlib.sha256(p.read_bytes()).hexdigest()
 v=root/'app/version.properties'; out['app/version.properties']=hashlib.sha256(v.read_bytes()).hexdigest(); return out
a,b=h(A),h(B); changed={p for p in set(a)|set(b) if a.get(p)!=b.get(p)}
if changed!=allowed: raise SystemExit('final 26491 delta mismatch: '+repr(sorted(changed)))
print('final exact seven-file 26490->26491 delta PASS')
PY_FINAL

# Create true direct 26490->26491 patch from local temporary baseline commit; never pushed.
(
 cd "$BASE"
 git -c user.name=Photon26491 -c user.email=local@invalid add app/src/main app/version.properties
 git -c user.name=Photon26491 -c user.email=local@invalid commit -q -m 'temporary exact successful 26490 artifact baseline'
 while IFS= read -r rel; do cp "$REPO/$rel" "$rel"; done < "$TMP/allowed-final.txt"
 git diff --binary HEAD -- app/src/main app/version.properties
) > "$DELTAPATCH"
[[ -s "$DELTAPATCH" ]] || fail "direct 26490->26491 source patch empty"
find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$AFTERHASH"
sha256sum app/version.properties >> "$AFTERHASH"

mapfile -t APKS < <(find app/build/outputs/apk/debug -maxdepth 1 -type f -name '*.apk' | sort)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one final debug APK, found ${#APKS[@]}"
rm -f ./*.apk
cp "${APKS[0]}" "$APK_NAME"
APK_SHA="$(sha "$APK_NAME")"

cat > "$REPORT" <<EOF_REPORT
26491 V4 COMPLETE HIGHLIGHT / EXPOSURE ARCHITECTURE
=================================================
Version=$NEW_VERSION
Build=$NEW_BUILD
Successful26490Head=$SUCCESSFUL_26490_HEAD
Failed26491V3Head=$FAILED_26491_V3_HEAD
Successful26490ArtifactPatchSHA256=$BASE_PATCH_SHA
Successful26490ArtifactManifestSHA256=$BASE_HASHES_SHA
TransformSHA256=$TRANSFORM_SHA
Tested26490BackupBranch=$BACKUP_BRANCH
FailedV3BackupBranch=$INFRA_BACKUP_BRANCH
Baseline=EXACT_SUCCESSFUL_26490_ARTIFACT_ONLY
FunctionalFilesChanged=6
StandingPrinciple=Midtones_decide_global_scene_exposure_Highlights_decide_local_HDR_treatment
GlobalExposureOwner=p50_p90_scene_body_plus_timestamp_owned_reference_exposure_energy_sanity_ceiling
BrightChandelierModelGain=approximately_1.0534x
DarkSceneModelGain=approximately_9.3681x
HighlightTailGlobalExposureAuthority=false
HighlightTailTelemetryPreserved=true
ShortHdrDecision=joint_coherent_CFA_vector
IndependentPerPhaseShortSubstitution=false
SpatialChromaticity=3x3_phase_safe_weighted_consensus
StrongObjectReflectionBoundaryBorrowing=false
BoundaryEvidence=normal_frame_safe_phase_coherence_plus_short_coherence
NeutralCensoredFallback=true
NeutralFallbackPreservesBalancedBrightness=true
MeasuredShortExtendedRadianceRetainsOwnership=true
CensoredNormalLowerBound=max_normal_recovered
ExtendedLinearHeadroomPreserved=true
HighlightCompression=single_scalar_chroma_preserving
FinalLeftEdgeFix=x0_mirrors_x1_only
RcdFourEdgeMirrorChanged=false
RcdWriteShaderByteProtected=true
ShortCaptureAlignmentPathChanged=false
ShortFlowMathChanged=false
ShortHostInterfaceChanged=false
WronskiMathChanged=false
R32FAccumulatorChanged=false
MergeWeightingRejectionChanged=false
AccumulatorInvariantChanged=false
MotionBatchOwnershipChanged=false
ShortRawNormalAccumulatorIsolationChanged=false
GhostingProtectionChanged=false
PostPipelineChanged=false
MotionV2Denoise=false
ESDChanged=false
SharpeningChanged=false
UHDRChanged=false
ReservedGlslPreflight=true
TypeAwareBindingInvocations=49
FullActiveMotionGlslang=true
ChangedShortShaderGlslang=true
ChangedRcdPopulateGlslang=true
ChangedRenderGlslang=true
PhotonParserAndGlesImageValidation=true
ScopedWhitespaceBaselineToCandidate=true
BroadLiveHistoricalWhitespaceCheck=false
TemporaryCandidateJavac=true
TemporaryCandidateFullGradleBuild=true
CandidateFinalFunctionalSourceByteEqual=true
APK=$APK_NAME
APK_SHA256=$APK_SHA
EOF_REPORT

mkdir -p "$OUTDIR/next_baseline_inputs"
cp "$TRANSFORM" "$OUTDIR/next_baseline_inputs/"
cp "$0" "$OUTDIR/next_baseline_inputs/build_26491_complete_highlight_exposure_v4.sh"
if [[ -f .github/workflows/build-26491-complete-highlight-exposure-v4.yml ]]; then
 cp .github/workflows/build-26491-complete-highlight-exposure-v4.yml "$OUTDIR/next_baseline_inputs/"
fi
cp "$DELTAPATCH" "$OUTDIR/next_baseline_inputs/26491_successful_source.patch"
cp "$AFTERHASH" "$OUTDIR/next_baseline_inputs/26491_successful_after.sha256"
sha256sum "$PREPATCH" "$DELTAPATCH" "$AFTERHASH" "$REPORT" "$JAVACLOG" "$CANDLOG" "$FINALLOG" "$SHADERLOG" > "$OUTDIR/26491_artifact_hashes.sha256"

echo "APK=$APK_NAME"
echo "SHA256=$APK_SHA"
echo "26491 V4 BUILD SUCCESS"
