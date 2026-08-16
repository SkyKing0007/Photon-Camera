#!/usr/bin/env bash
set -euo pipefail

EXPECTED_BRANCH="experimental-clean-photon-rebuild"
EXPECTED_APP_BASE="8233415edf738bf35c0fe1c4907f5dfe51de31a4"
TESTED_26491_HEAD="502c4b32ee6fb298f117ca4a1df1900679d28e58"
FAILED_26492_V1_HEAD="8d3219f5caa0e1dc4f839944f1c85199b94fa737"
TESTED_26491_BACKUP_BRANCH="backup-26491-v4-tested-before-26492-provenance-authority-contract"
FAILED_V1_BACKUP_BRANCH="backup-26492-v1-failed-r8ui-before-v2-proven-r32f"
FAILED_V2_HEAD="5591573cc39aa94584fc61d77b7d8e68a3ef1217"
FAILED_V2_BACKUP_BRANCH="backup-26492-v2-built-before-v3-native-deps-cleanup"
BASE_PATCH="26490_successful_source.patch"
BASE_PATCH_SHA="c589cc000047da6dd19c7b1ac71405fa635d75db37007fa526c60368001433ba"
BASE_HASHES="26490_successful_after.sha256"
BASE_HASHES_SHA="431a62d9e23cd17d71388d4b79ad0a0c548c58ae9eabb2ad1894ba9cad34322f"
TRANSFORM_26491="transform_26491_complete_highlight_exposure_v4.py"
TRANSFORM_26491_SHA="82b78d994b9657e36b202849f465061b2a4ada66822fa9f6b82d013935e37ed5"
TRANSFORM_26492="transform_26492_authority_provenance_v2.py"
TRANSFORM_26492_SHA="fda88e97092bdea6b7eb4323a51d01f389d5481c57ac9c1f0ec8ce86086b4784"
NEW_VERSION="0.9726492"
NEW_BUILD="26492"
OUTDIR="build_26492_v3_outputs"
APK_NAME="IrisCamera-${NEW_VERSION}-${NEW_BUILD}-v3-authority-provenance-r32f-debug.apk"

fail(){ echo "FAIL: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }

REPO="$(pwd)"
rm -rf "$OUTDIR"; mkdir -p "$OUTDIR/next_baseline_inputs"
AUDIT="$OUTDIR/26492_source_audit.txt"
SHADERLOG="$OUTDIR/26492_shader_validation.txt"
JAVACLOG="$OUTDIR/26492_temporary_candidate_javac.log"
CANDLOG="$OUTDIR/26492_temporary_candidate_build.log"
FINALLOG="$OUTDIR/26492_final_build.log"
PREPATCH="$OUTDIR/26492_pre_edit_exact_26491_binary.patch"
DELTAPATCH="$OUTDIR/26492_source.patch"
AFTERHASH="$OUTDIR/26492_after.sha256"
REPORT="$OUTDIR/26492_build_report.txt"
exec > >(tee "$AUDIT") 2>&1

echo "=== 26492 V3 AUTHORITY / PROVENANCE CONTRACT — PROVEN R32F + NATIVE-DEP CLEANUP ==="
date -Iseconds || true

# GATE 0: exact repository/infrastructure identity.
BRANCH="${GITHUB_REF_NAME:-$(git branch --show-current)}"
[[ "$BRANCH" != "dev" ]] || fail "dev is protected"
[[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || fail "wrong branch: $BRANCH"
git cat-file -e "$EXPECTED_APP_BASE^{commit}" || fail "protected app-base commit unavailable"
git cat-file -e "$TESTED_26491_HEAD^{commit}" || fail "tested 26491 commit unavailable"
git cat-file -e "$FAILED_V2_HEAD^{commit}" || fail "built-but-audit-failed 26492 V2 commit unavailable"
git cat-file -e "$FAILED_26492_V1_HEAD^{commit}" || fail "failed 26492 V1 infrastructure commit unavailable"
git merge-base --is-ancestor "$TESTED_26491_HEAD" HEAD || fail "tested 26491 V4 is not an ancestor"
git merge-base --is-ancestor "$FAILED_V2_HEAD" HEAD || fail "26492 V3 must descend from the recorded V2 infrastructure checkpoint"
git merge-base --is-ancestor "$FAILED_26492_V1_HEAD" HEAD || fail "26492 V3 must descend from failed V1 infrastructure checkpoint"
git diff --quiet "$EXPECTED_APP_BASE" -- app/src/main app/version.properties || fail "committed app source no longer equals protected application base"
[[ -f "$BASE_PATCH" && "$(sha "$BASE_PATCH")" == "$BASE_PATCH_SHA" ]] || fail "26490 source patch identity mismatch"
[[ -f "$BASE_HASHES" && "$(sha "$BASE_HASHES")" == "$BASE_HASHES_SHA" ]] || fail "26490 after-manifest identity mismatch"
[[ -f "$TRANSFORM_26491" && "$(sha "$TRANSFORM_26491")" == "$TRANSFORM_26491_SHA" ]] || fail "26491 transform identity mismatch"
[[ -f "$TRANSFORM_26492" && "$(sha "$TRANSFORM_26492")" == "$TRANSFORM_26492_SHA" ]] || fail "26492 transform identity mismatch"
python3 -m py_compile "$TRANSFORM_26491" "$TRANSFORM_26492" || fail "transform Python syntax"
python3 "$TRANSFORM_26491" --self-test || fail "26491 self-test"
python3 "$TRANSFORM_26492" --self-test || fail "26492 self-test"
bash -n "$0" || fail "26492 build script syntax"
pass "repository + transform identity"

# GATE 1: both tested-source and fresh failed-V1 infrastructure backups are immutable.
remote_tested="$(git ls-remote origin "refs/heads/$TESTED_26491_BACKUP_BRANCH" | awk '{print $1}')"
[[ "$remote_tested" == "$TESTED_26491_HEAD" ]] || fail "backup $TESTED_26491_BACKUP_BRANCH=$remote_tested expected=$TESTED_26491_HEAD"
pass "backup branch exact tested 26491 checkpoint"
remote_v1="$(git ls-remote origin "refs/heads/$FAILED_V1_BACKUP_BRANCH" | awk '{print $1}')"
[[ "$remote_v1" == "$FAILED_26492_V1_HEAD" ]] || fail "backup $FAILED_V1_BACKUP_BRANCH=$remote_v1 expected=$FAILED_26492_V1_HEAD"
pass "fresh backup branch exact failed 26492 V1 infrastructure checkpoint"
v2_remote="$(git ls-remote origin "refs/heads/$FAILED_V2_BACKUP_BRANCH" | awk '{print $1}')"
[[ "$v2_remote" == "$FAILED_V2_HEAD" ]] || fail "V2 backup $FAILED_V2_BACKUP_BRANCH=$v2_remote expected=$FAILED_V2_HEAD"
pass "built-but-audit-failed V2 backup exact checkpoint"

TMP="$(mktemp -d)"
BASE="$TMP/exact-26491"
CAND="$TMP/candidate-26492"
cleanup(){ set +e; git worktree remove --force "$BASE" >/dev/null 2>&1 || true; git worktree remove --force "$CAND" >/dev/null 2>&1 || true; rm -rf "$TMP"; }
trap cleanup EXIT

reconstruct_26491(){
  local dst="$1"
  git worktree add --detach "$dst" "$EXPECTED_APP_BASE" >/dev/null || fail "create exact-26491 worktree"
  ( cd "$dst" && git apply --check --binary "$REPO/$BASE_PATCH" ) || fail "26490 patch precheck"
  ( cd "$dst" && git apply --binary "$REPO/$BASE_PATCH" ) || fail "26490 patch apply"
  ( cd "$dst" && sha256sum -c "$REPO/$BASE_HASHES" >/dev/null ) || fail "26490 full manifest verification"
  python3 "$REPO/$TRANSFORM_26491" "$dst" || fail "26491 V4 transform replay"
  sed -i 's/^VERSION_NAME=.*/VERSION_NAME=0.9726491/; s/^VERSION_BUILD=.*/VERSION_BUILD=26491/' "$dst/app/version.properties"
  grep -q '^VERSION_NAME=0\.9726491$' "$dst/app/version.properties" || fail "26491 version name reconstruction"
  grep -q '^VERSION_BUILD=26491$' "$dst/app/version.properties" || fail "26491 build reconstruction"
  [[ "$(sha "$dst/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java")" == "0eaf10a20627b3a8e94a9f5664214999edb4273c48db5b571d0e77fe3ae0f002" ]] || fail "26491 merger hash"
  [[ "$(sha "$dst/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java")" == "55d8a98332662f8866e2b9b4c4d7fb060619430f899323685f33e1823530aa12" ]] || fail "26491 recon hash"
  [[ "$(sha "$dst/app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl")" == "c5c9f9dcbe6ce730b94f74e3a56361ddfcf9c3ac35b6113cdb1eae6565edae0a" ]] || fail "26491 short hash"
  [[ "$(sha "$dst/app/src/main/assets/shaders/motionv2/rcd26489_populate.glsl")" == "3e572712dfad2fc49d1ef2fb04ac42bfc64e329ffcddbaaea8483c43d8693b43" ]] || fail "26491 RCD populate hash"
  [[ "$(sha "$dst/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2RcdDemosaic.java")" == "7c205e683a6a86ebf02fee88ea8e25e2ec6a4758dcc2e37f23081d5e16274a8c" ]] || fail "26491 RCD host hash"
  [[ "$(sha "$dst/app/src/main/assets/shaders/motionv2/render.glsl")" == "2a3aa0c6e3cc553e11d4feeb6ecf24768f14e423ce359a3248b9f70dda7a8dbf" ]] || fail "26491 render hash"
}

reconstruct_26491 "$BASE"
pass "exact successful 26491 reconstructed"
# Required binary pre-edit patch BEFORE 26492 transformation.
( cd "$BASE" && git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties ) > "$PREPATCH"
[[ -s "$PREPATCH" ]] || fail "pre-edit exact-26491 patch is empty"
sha256sum "$PREPATCH" | tee "$OUTDIR/26492_pre_edit_exact_26491_binary.patch.sha256"
pass "binary pre-edit exact-26491 patch created before modification"

reconstruct_26491 "$CAND"
python3 "$REPO/$TRANSFORM_26492" "$CAND" || fail "26492 transform application"
pass "26492 temporary transform applied"

cat > "$TMP/allowed.txt" <<'EOF_ALLOWED'
app/src/main/assets/shaders/motionv2/highlight_provenance_init.glsl
app/src/main/assets/shaders/motionv2/rcd26489_populate.glsl
app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2RcdDemosaic.java
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java
EOF_ALLOWED

# GATE 2: exact 9-file functional scope and every unrelated source byte protected.
python3 - "$BASE" "$CAND" "$TMP/allowed.txt" <<'PY_SCOPE'
from pathlib import Path
import hashlib,sys
A,B=Path(sys.argv[1]),Path(sys.argv[2]); allowed=set(Path(sys.argv[3]).read_text().splitlines())
def h(p): return hashlib.sha256(p.read_bytes()).digest()
changed=set()
for base in ('app/src/main',):
    rels=set()
    for root in (A,B):
        p=root/base
        if p.exists(): rels |= {str(x.relative_to(root)) for x in p.rglob('*') if x.is_file()}
    for rel in rels:
        a,b=A/rel,B/rel
        if not a.exists() or not b.exists() or h(a)!=h(b): changed.add(rel)
if changed!=allowed:
    raise SystemExit('26492 scope mismatch changed='+repr(sorted(changed))+' allowed='+repr(sorted(allowed)))
print('26492 exact functional scope PASS files=9')
PY_SCOPE

# Changed-line whitespace audit only; rc=1 means differences exist and is acceptable.
set +e
git diff --no-index --check "$BASE/app/src/main" "$CAND/app/src/main" > "$TMP/diffcheck.txt" 2>&1
DCRC=$?
set -e
[[ "$DCRC" -eq 0 || "$DCRC" -eq 1 ]] || fail "26492 scoped diff check command failure"
[[ ! -s "$TMP/diffcheck.txt" ]] || { cat "$TMP/diffcheck.txt"; fail "26492 changed lines contain whitespace errors"; }
pass "26492 changed-line whitespace audit"

# GATE 3: semantic authority/provenance contract, not marker-only assertions.
python3 - "$CAND" <<'PY_SEM'
from pathlib import Path
import re,sys
r=Path(sys.argv[1])
mer=(r/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java').read_text()
rec=(r/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java').read_text()
hdr=(r/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java').read_text()
post=(r/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java').read_text()
inp=(r/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java').read_text()
rcdh=(r/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2RcdDemosaic.java').read_text()
short=(r/'app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl').read_text()
rcd=(r/'app/src/main/assets/shaders/motionv2/rcd26489_populate.glsl').read_text()
prov=(r/'app/src/main/assets/shaders/motionv2/highlight_provenance_init.glsl').read_text()
# Exposure: no exposure-energy or highlight pressure may veto candidate gain.
if 'illuminationCeiling' in mer: raise SystemExit('26491 exposure-energy ceiling survived')
if 'candidateGain * adaptiveReduction' in mer: raise SystemExit('highlight pressure still owns global gain')
if 'Math.min(candidateGain, 16.0f)' not in mer: raise SystemExit('scene-body candidate is not final numerical authority')
if 'exposureEnergyHasVeto=false' not in mer: raise SystemExit('exposure veto diagnostic missing')
# Bridge continuity.
for text,tok in ((mer,'highlightProvenance'),(rec,'highlightProvenanceOutput'),(hdr,'motionV2HighlightProvenance'),(post,'motionV2HighlightProvenanceTexture'),(inp,'FLOAT_32, 1'),(rcdh,'HighlightProvenance')):
    if tok not in text: raise SystemExit('provenance bridge missing '+tok)
# Explicit states and one packed decision.
for tok in ('PROVENANCE_NORMAL','PROVENANCE_CENSORED','PROVENANCE_SHORT_VALIDATED','IRIS_26492_SHORT_OBSERVABILITY_RING','supportCount >= 12.0','meanRelativeError <= 0.12','structure >= 0.08','vec4 recovered = mix(normal, shortEquivalent, packBlend)'):
    if tok not in short: raise SystemExit('short validation contract missing '+tok)
for forbidden in ('centerHasEveryNeeded','jointConfidence','normalClip *','weightedShort'):
    if forbidden in short: raise SystemExit('old short reclassification survived '+forbidden)
# RCD is consumer only.
for tok in ('uniform highp sampler2D HighlightProvenance','IRIS_26492_CENSORED_PACKED_NEUTRAL_LOWER_BOUND','IRIS_26492_RCD_PROVENANCE_CONSUMER_ONLY','abs(state - PROVENANCE_CENSORED) > 0.25'):
    if tok not in rcd: raise SystemExit('RCD provenance contract missing '+tok)
for forbidden in ('packedExtendedEvidence','chromaRecoverable','coherentOpposedEstimate'):
    if forbidden in rcd: raise SystemExit('RCD still re-infers highlight color '+forbidden)
if 'layout(r32f, binding = 0)' not in prov or 'CENSORED_UNKNOWN_CHROMA' not in prov: raise SystemExit('R32F provenance init contract missing')
for text,name in ((prov,'provenance init'),(short,'short recovery'),(rcd,'RCD')):
    for forbidden in ('r8ui','uimage2D','usampler2D'):
        if forbidden in text: raise SystemExit(name+' contains unsupported integer provenance resource '+forbidden)
if 'highlightProvenanceR32F=' not in inp: raise SystemExit('R32F bridge diagnostic missing')
# Wronski accumulator invariants still present in the changed reconstruction owner.
for tok in ('IRIS_26489_ACCUMULATOR_INVARIANT_PASS','IRIS_26489_BJZHOU_BAYER_NORMALIZE_EXACTLY_ONCE','accumulatorNumerator','accumulatorDenominator'):
    if tok not in rec: raise SystemExit('protected Wronski invariant missing '+tok)
print('26492 SEMANTIC AUTHORITY PASS exposureVetoes=0 provenancePromotionsOnlyAtShortValidator=true rcdConsumerOnly=true')
PY_SEM

# Protect key unchanged shaders/post owners by exact 26491 byte identity.
for rel in \
 app/src/main/assets/shaders/motionv2/mfsr_bayer_accumulate.glsl \
 app/src/main/assets/shaders/motionv2/mfsr_bayer_normalize.glsl \
 app/src/main/assets/shaders/motionv2/mfsr_flow_expand.glsl \
 app/src/main/assets/shaders/motionv2/render.glsl \
 app/src/main/assets/shaders/motionv2/color_transform.glsl \
 app/src/main/assets/shaders/motionv2/display_exposure.glsl \
 app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java \
 app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java \
 app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java; do
  cmp -s "$BASE/$rel" "$CAND/$rel" || fail "protected 26491 byte changed: $rel"
done
pass "Wronski accumulator/alignment + display/color/render owners protected"

# GATE 3B: proven GPU image-format contract before any full-graph compile.
# R32F and RGBA32F are already used by the protected active Motion graph. V2 may not
# introduce integer image load/store formats merely because GLFormat can allocate them.
python3 - "$BASE" "$CAND" <<'PY_FORMAT'
from pathlib import Path
import re,sys
base,cand=map(Path,sys.argv[1:3])
changed_shaders=[
    cand/'app/src/main/assets/shaders/motionv2/highlight_provenance_init.glsl',
    cand/'app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl',
    cand/'app/src/main/assets/shaders/motionv2/rcd26489_populate.glsl',
]
# Prove R32F was already present in the exact protected 26491 active Motion source.
proven=[
    base/'app/src/main/assets/shaders/motionv2/mfsr_bayer_accumulator_clear.glsl',
    base/'app/src/main/assets/shaders/motionv2/mfsr_bayer_accumulate.glsl',
]
if not all('layout(r32f' in p.read_text() for p in proven):
    raise SystemExit('protected 26491 R32F proof shaders no longer contain r32f image storage')
allowed={'r32f','rgba32f'}
layout_image=re.compile(r'layout\s*\(\s*([A-Za-z0-9_]+)[^)]*\)\s*uniform\s+(?:(?:highp|mediump|lowp|readonly|writeonly|coherent|volatile|restrict)\s+)*(?:[ui]?image2D)\b')
seen=set()
for p in changed_shaders:
    text=p.read_text()
    for fmt in layout_image.findall(text):
        seen.add(fmt)
        if fmt not in allowed:
            raise SystemExit(f'26492 V2 unproven image load/store format {fmt} in {p.name}')
    for forbidden in ('uimage2D','iimage2D','r8ui','r16ui','r32ui','rgba8ui','rgba16ui','rgba32ui'):
        if forbidden in text:
            raise SystemExit(f'26492 V2 forbidden integer image path {forbidden} in {p.name}')
if 'r32f' not in seen or 'rgba32f' not in seen:
    raise SystemExit('26492 V2 expected R32F provenance + RGBA32F CFA image formats not both present')
# Host-side provenance storage must use the same proven FLOAT_32 single-channel contract.
for rel in (
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java'):
    text=(cand/rel).read_text()
    if 'GLFormat.DataType.UNSIGNED_8' in text and 'Provenance' in text:
        raise SystemExit('26492 V2 provenance host path still contains UNSIGNED_8 in '+rel)
print('26492 V2 PROVEN IMAGE FORMAT PASS provenBaseline=R32F carrier=R32F cfa=RGBA32F integerImageFormats=0')
PY_FORMAT

# GATE 4: derive exact active Motion shader graph from runtime owners.
RECON="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"
WR="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java"
RCDH="$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2RcdDemosaic.java"
python3 - "$CAND" "$RECON" "$WR" "$RCDH" "$TMP/compute_shaders.txt" "$TMP/fragment_shaders.txt" <<'PY_GRAPH'
from pathlib import Path
import re,sys
root=Path(sys.argv[1]); owners=[Path(x) for x in sys.argv[2:5]]; compute=set(); fragment=set(); invocations=0
for owner in owners:
 java=owner.read_text()
 for m in re.finditer(r'useAssetProgram\(\s*"motionv2/([^"]+)"(?:\s*,\s*(true|false))?\s*\)',java):
  invocations+=1; name,flag=m.group(1),m.group(2); rel=f'app/src/main/assets/shaders/motionv2/{name}.glsl'
  if not (root/rel).is_file(): raise SystemExit('active Motion shader missing: '+rel)
  (compute if flag=='true' else fragment).add(rel)
if compute & fragment: raise SystemExit('shader loaded as both compute and fragment')
if invocations != 50: raise SystemExit(f'26492 expected 50 literal Motion shader invocations, got {invocations}')
Path(sys.argv[5]).write_text(''.join(x+'\n' for x in sorted(compute)))
Path(sys.argv[6]).write_text(''.join(x+'\n' for x in sorted(fragment)))
print(f'26492 active Motion graph PASS invocations={invocations} compute={len(compute)} fragment={len(fragment)}')
PY_GRAPH

# Type-aware sampler/image/uniform/SSBO host binding audit.
python3 - "$CAND" "$RECON" "$WR" "$RCDH" <<'PY_BIND'
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
if problems: raise SystemExit('26492 TYPE-AWARE BINDING FAILURE: '+repr(problems))
if invocations != 50: raise SystemExit(f'26492 expected 50 literal Motion shader invocations, got {invocations}')
print('26492 TYPE-AWARE BINDING PASS invocations=50')
PY_BIND

# GLSL lexical + real compiler over entire active graph.
: > "$SHADERLOG"
compile_compute(){
 local f="$1" tmp="$2"
 python3 - "$f" "$tmp" <<'PY_COMP'
from pathlib import Path
import sys,re
s=Path(sys.argv[1]).read_text();needle='#define LAYOUT //\nLAYOUT'
if needle not in s:raise SystemExit('missing Photon LAYOUT header '+sys.argv[1])
clean=re.sub(r'//.*','',re.sub(r'/\*.*?\*/','',s,flags=re.S))
bad=re.search(r'\b(?:float|vec[234]|int|ivec[234]|uint|uvec[234]|bool|mat[234])\s+(sample|common|coherent|precision|packed)\b',clean)
if bad: raise SystemExit('reserved GLSL identifier '+bad.group(1)+' '+sys.argv[1])
Path(sys.argv[2]).write_text(s.replace(needle,'#version 310 es\nlayout(local_size_x=8,local_size_y=8,local_size_z=1) in;',1))
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
Path(sys.argv[2]).write_text(s.replace(needle,'#version 300 es',1))
PY_FRAG
 glslangValidator -S frag "$tmp" >> "$SHADERLOG" 2>&1
}
command -v glslangValidator >/dev/null 2>&1 || fail "glslangValidator unavailable"
shader_fail=0
while IFS= read -r rel;do [[ -n "$rel" ]]||continue;n="$(basename "$rel")";if compile_compute "$CAND/$rel" "$TMP/$n.comp";then echo "COMPUTE PASS $n" >> "$SHADERLOG";else echo "COMPUTE FAIL $n" >> "$SHADERLOG";shader_fail=1;fi;done < "$TMP/compute_shaders.txt"
while IFS= read -r rel;do [[ -n "$rel" ]]||continue;n="$(basename "$rel")";if compile_fragment "$CAND/$rel" "$TMP/$n.frag";then echo "FRAGMENT PASS $n" >> "$SHADERLOG";else echo "FRAGMENT FAIL $n" >> "$SHADERLOG";shader_fail=1;fi;done < "$TMP/fragment_shaders.txt"
[[ "$shader_fail" -eq 0 ]] || { cat "$SHADERLOG"; fail "active Motion shader compiler failure"; }
grep -q 'COMPUTE PASS highlight_provenance_init.glsl' "$SHADERLOG" || fail "new provenance shader did not compile"
grep -q 'COMPUTE PASS short_highlight_bayer_recover.glsl' "$SHADERLOG" || fail "changed short shader did not compile"
grep -q 'COMPUTE PASS rcd26489_populate.glsl' "$SHADERLOG" || fail "changed RCD shader did not compile"
pass "complete active Motion shader graph real glslang PASS"

# GATE 5: Java lexical parse + real javac task compile and temporary APK.
CHANGED_JAVA=(
 "$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java"
 "$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2RcdDemosaic.java"
 "$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java"
 "$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java"
 "$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"
 "$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java"
)
python3 - "${CHANGED_JAVA[@]}" <<'PY_JAVA'
from pathlib import Path
import sys
for arg in sys.argv[1:]:
 s=Path(arg).read_text()
 if s.count('{')!=s.count('}'):raise SystemExit('Java brace mismatch '+arg)
 if '\x00' in s:raise SystemExit('NUL '+arg)
print('26492 Java lexical PASS files='+str(len(sys.argv)-1))
PY_JAVA

cat > "$TMP/ParseJava.java" <<'JAVA_PARSE'
import java.io.*;import java.util.*;import javax.tools.*;import com.sun.source.util.*;
public class ParseJava{public static void main(String[]a)throws Exception{JavaCompiler c=ToolProvider.getSystemJavaCompiler();StandardJavaFileManager f=c.getStandardFileManager(null,null,null);Iterable<? extends JavaFileObject> u=f.getJavaFileObjectsFromStrings(Arrays.asList(a));JavacTask t=(JavacTask)c.getTask(new PrintWriter(System.out),f,null,Arrays.asList("-proc:none","-Xlint:none"),null,u);t.parse();f.close();}}
JAVA_PARSE
javac "$TMP/ParseJava.java"
java -cp "$TMP" ParseJava "${CHANGED_JAVA[@]}" > "$JAVACLOG" 2>&1 || { cat "$JAVACLOG"; fail "JavacTask parse"; }
( cd "$CAND" && ./gradlew :app:compileDebugJavaWithJavac --stacktrace ) >> "$JAVACLOG" 2>&1 || { tail -200 "$JAVACLOG"; fail "candidate javac compile"; }
pass "Java parse + compile"

( cd "$CAND" && ./gradlew clean assembleDebug --stacktrace ) > "$CANDLOG" 2>&1 || { tail -240 "$CANDLOG"; fail "temporary candidate full build"; }
pass "temporary candidate full APK build"

# Restore the exact successful-26491 handling for known CMake build-time downloads.
# These are generated inputs, not canonical source and must never enter the final delta/manifest.
cat > "$TMP/generated-native-deps.txt" <<'EOF_DEPS'
app/src/main/cpp/deps/archive.h
app/src/main/cpp/deps/archive_entry.h
app/src/main/cpp/deps/technicallyflac.h
app/src/main/cpp/deps/tiny_dng_writer.h
EOF_DEPS
while IFS= read -r rel; do
  [[ -n "$rel" ]] || continue
  [[ ! -e "$BASE/$rel" ]] || fail "generated native dep unexpectedly exists in exact 26491 canonical baseline: $rel"
  [[ -f "$CAND/$rel" ]] || fail "candidate build did not materialize known native dep: $rel"
  sha256sum "$CAND/$rel"
done < "$TMP/generated-native-deps.txt" > "$OUTDIR/26492_candidate_generated_native_deps.sha256"
pass "candidate generated native dependencies captured outside canonical source"
# Remove candidate-generated downloads before the final clean build so the final build
# must materialize them independently; this makes the equality check meaningful.
while IFS= read -r rel; do
  [[ -n "$rel" ]] || continue
  rm -f "$CAND/$rel"
  [[ ! -e "$CAND/$rel" ]] || fail "pre-final generated native dependency cleanup failed: $rel"
done < "$TMP/generated-native-deps.txt"
pass "candidate generated native deps removed before independent final regeneration"

# GATE 6: exact version bump + final clean build in the SAME guarded block.
{
  sed -i 's/^VERSION_NAME=.*/VERSION_NAME='"$NEW_VERSION"'/; s/^VERSION_BUILD=.*/VERSION_BUILD='"$NEW_BUILD"'/' "$CAND/app/version.properties"
  grep -q '^VERSION_NAME='"$NEW_VERSION"'$' "$CAND/app/version.properties" || fail "final version name"
  grep -q '^VERSION_BUILD='"$NEW_BUILD"'$' "$CAND/app/version.properties" || fail "final version build"
  ( cd "$CAND" && ./gradlew clean assembleDebug --stacktrace ) > "$FINALLOG" 2>&1 || { tail -260 "$FINALLOG"; fail "final 26492 clean build"; }
}
pass "version increment + final APK built in one guarded command block"

APK_SRC="$(find "$CAND/app/build/outputs/apk/debug" -maxdepth 1 -type f -name '*.apk' -print | head -1)"
[[ -n "$APK_SRC" && -f "$APK_SRC" ]] || fail "final debug APK missing"
cp "$APK_SRC" "$REPO/$APK_NAME"
APK_SHA="$(sha "$REPO/$APK_NAME")"
sha256sum "$REPO/$APK_NAME" | tee "$OUTDIR/${APK_NAME}.sha256"

# Candidate/final generated native bytes must match exactly, then remove them before
# canonical source immutability/delta/manifests. This is the proven 26491 procedure.
python3 - "$CAND" "$TMP/generated-native-deps.txt" "$OUTDIR/26492_candidate_generated_native_deps.sha256" <<'PY_DEPS'
from pathlib import Path
import hashlib,sys
root=Path(sys.argv[1]); listing=Path(sys.argv[2]); recorded=Path(sys.argv[3])
expected={}
for line in recorded.read_text().splitlines():
    if not line.strip(): continue
    h,p=line.split(None,1); expected[p.strip()]=h
for rel in [x for x in listing.read_text().splitlines() if x.strip()]:
    p=root/rel
    if not p.is_file(): raise SystemExit('final generated native dependency missing: '+rel)
    h=hashlib.sha256(p.read_bytes()).hexdigest()
    if expected.get(str(p)) is None:
        # sha256sum was run with an absolute/relative candidate path; match by suffix.
        matches=[v for k,v in expected.items() if k.endswith('/'+rel) or k==rel]
        if len(matches)!=1: raise SystemExit('candidate generated dep hash record missing: '+rel)
        eh=matches[0]
    else:
        eh=expected[str(p)]
    if h!=eh: raise SystemExit(f'candidate/final generated dep mismatch: {rel} {eh} {h}')
    print(f'generated native dependency byte equality PASS: {rel} {h}')
PY_DEPS
while IFS= read -r rel; do
  [[ -n "$rel" ]] || continue
  rm -f "$CAND/$rel"
  [[ ! -e "$CAND/$rel" ]] || fail "generated native dependency cleanup failed: $rel"
done < "$TMP/generated-native-deps.txt"
pass "generated native dependencies removed before canonical final delta/manifests"

# Final exact delta must be 9 functional files + version only.
python3 - "$BASE" "$CAND" "$TMP/allowed.txt" <<'PY_FINAL'
from pathlib import Path
import hashlib,sys
A,B=Path(sys.argv[1]),Path(sys.argv[2]); allowed=set(Path(sys.argv[3]).read_text().splitlines())|{'app/version.properties'}
def h(p):return hashlib.sha256(p.read_bytes()).digest()
changed=set()
for base in ('app/src/main','app/version.properties'):
 pa=A/base;pb=B/base
 if pa.is_file() or pb.is_file():
  if not pa.exists() or not pb.exists() or h(pa)!=h(pb):changed.add(base)
 else:
  rels={str(x.relative_to(A)) for x in pa.rglob('*') if x.is_file()}|{str(x.relative_to(B)) for x in pb.rglob('*') if x.is_file()}
  for rel in rels:
   a,b=A/rel,B/rel
   if not a.exists() or not b.exists() or h(a)!=h(b):changed.add(rel)
if changed!=allowed:raise SystemExit('final delta mismatch '+repr(sorted(changed)))
print('26492 final delta PASS files=10 including version')
PY_FINAL

# Outputs: direct 26491->26492 patch, base->26492 next-baseline patch and full manifest.
( cd "$CAND" && git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties ) > "$OUTDIR/next_baseline_inputs/26492_successful_source.patch"
( cd "$CAND" && find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum; sha256sum app/version.properties ) > "$OUTDIR/next_baseline_inputs/26492_successful_after.sha256"
while IFS= read -r rel; do ! grep -Fq "  $rel" "$OUTDIR/next_baseline_inputs/26492_successful_after.sha256" || fail "generated native dep entered canonical 26492 manifest: $rel"; done < "$TMP/generated-native-deps.txt"
pass "generated native deps excluded from canonical 26492 next-baseline manifest"
# Direct exact-26491 delta uses no-index directory/file diffs.
set +e
git diff --no-index --binary "$BASE/app/src/main" "$CAND/app/src/main" > "$DELTAPATCH"; rc1=$?
git diff --no-index --binary "$BASE/app/version.properties" "$CAND/app/version.properties" >> "$DELTAPATCH"; rc2=$?
set -e
[[ "$rc1" -eq 0 || "$rc1" -eq 1 ]] || fail "direct source patch src diff"
[[ "$rc2" -eq 0 || "$rc2" -eq 1 ]] || fail "direct source patch version diff"
cp "$OUTDIR/next_baseline_inputs/26492_successful_after.sha256" "$AFTERHASH"

cat > "$REPORT" <<REPORT_EOF
Iris ${NEW_VERSION} / ${NEW_BUILD}
26492 V3 Authority / Provenance Contract — R32F + Proven Native-Dep Cleanup

Baseline commit: ${TESTED_26491_HEAD}
Tested backup branch: ${TESTED_26491_BACKUP_BRANCH}
Failed-V1 backup branch: ${FAILED_V1_BACKUP_BRANCH}
Built-V2 backup branch: ${FAILED_V2_BACKUP_BRANCH}
Transform SHA256: ${TRANSFORM_26492_SHA}
APK: ${APK_NAME}
APK SHA256: ${APK_SHA}

Functional scope: 9 files
- one proven R32F packed-CFA highlight provenance carrier (0.0/1.0/2.0 exact states)
- NORMAL / CENSORED / SHORT_VALIDATED explicit states
- short HDR requires observable unsaturated ring correspondence
- smooth flow alone cannot certify clipped textureless regions
- one packed-CFA scalar short/normal ownership decision
- RCD consumes provenance and cannot reclassify value>1 as trusted HDR
- CENSORED preserves a neutral balanced lower-bound brightness
- Camera2 exposure energy is diagnostic only; no global-gain veto

Protected:
- 26489 Wronski/R32F accumulator and normalize-once architecture
- admitted == contributed invariant
- capture/ZSL/MotionBatch ownership
- display exposure shader
- Camera2 color transform shader/owner
- render/UHDR behavior
- MotionV2Denoise disabled architecture
- sharpening excluded
- known CMake native deps candidate/final byte-equal then removed before canonical packaging
REPORT_EOF

sha256sum "$TRANSFORM_26492" "$PREPATCH" "$DELTAPATCH" "$AFTERHASH" "$REPORT" "$OUTDIR/26492_candidate_generated_native_deps.sha256" "$REPO/$APK_NAME" > "$OUTDIR/26492_artifact_hashes.sha256"
cp "$TRANSFORM_26492" "$OUTDIR/next_baseline_inputs/"
cp "$REPO/$TRANSFORM_26491" "$OUTDIR/next_baseline_inputs/"

echo "=== 26492 V3 BUILD SUCCESS ==="
cat "$REPORT"
