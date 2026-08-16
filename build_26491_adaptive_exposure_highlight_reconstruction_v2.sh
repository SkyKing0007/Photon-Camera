#!/usr/bin/env bash
set -euo pipefail

EXPECTED_BRANCH="experimental-clean-photon-rebuild"
EXPECTED_APP_BASE="8233415edf738bf35c0fe1c4907f5dfe51de31a4"
SUCCESSFUL_26490_HEAD="07c406502f2c33d771c2cbfcb7bda97076f986e2"
BACKUP_BRANCH="backup-26490-v3-tested-before-26491-adaptive-exposure-highlight-reconstruction"
BASE_PATCH="26490_successful_source.patch"
BASE_PATCH_SHA="c589cc000047da6dd19c7b1ac71405fa635d75db37007fa526c60368001433ba"
BASE_HASHES="26490_successful_after.sha256"
BASE_HASHES_SHA="431a62d9e23cd17d71388d4b79ad0a0c548c58ae9eabb2ad1894ba9cad34322f"
TRANSFORM="transform_26491_adaptive_exposure_highlight_reconstruction_v2.py"
TRANSFORM_SHA="0d30ec19777e9d4da8d59acc998fc68135cb099e72b51a407d21ab8ee363e9eb"
NEW_VERSION="0.9726491"
NEW_BUILD="26491"
OUTDIR="build_26491_outputs"
APK_NAME="IrisCamera-${NEW_VERSION}-${NEW_BUILD}-adaptive-exposure-joint-short-highlight-debug.apk"

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

echo "=== 26491 DIRECT FROM SUCCESSFUL 26490: ADAPTIVE MIDTONE EXPOSURE + JOINT SHORT-HDR CFA RECONSTRUCTION ==="
date -Iseconds || true

# GATE 0 — exact successful 26490 package identity. No historical reconstruction.
BRANCH="${GITHUB_REF_NAME:-$(git branch --show-current)}"
[[ "$BRANCH" != "dev" ]] || fail "dev is protected"
[[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || fail "wrong branch: $BRANCH"
git cat-file -e "$EXPECTED_APP_BASE^{commit}" || fail "verified app-base commit unavailable"
git cat-file -e "$SUCCESSFUL_26490_HEAD^{commit}" || fail "successful 26490 infrastructure HEAD unavailable"
git merge-base --is-ancestor "$SUCCESSFUL_26490_HEAD" HEAD || fail "successful 26490 commit is not an ancestor of this build"
git diff --quiet "$EXPECTED_APP_BASE" -- app/src/main app/version.properties || \
  fail "committed app source no longer equals the protected application base"
[[ -f "$BASE_PATCH" && "$(sha "$BASE_PATCH")" == "$BASE_PATCH_SHA" ]] || fail "successful 26490 source patch identity mismatch"
[[ -f "$BASE_HASHES" && "$(sha "$BASE_HASHES")" == "$BASE_HASHES_SHA" ]] || fail "successful 26490 manifest identity mismatch"
[[ -f "$TRANSFORM" && "$(sha "$TRANSFORM")" == "$TRANSFORM_SHA" ]] || fail "26491 transform identity mismatch"
python3 -m py_compile "$TRANSFORM" || fail "26491 transform Python syntax"
python3 "$TRANSFORM" --self-test || fail "26491 transform self-test"
bash -n "$0" || fail "26491 build script syntax"
pass "exact successful-26490 direct-baseline package identity"

# GATE 1 — required pre-change backup exists and points to exact tested 26490.
remote="$(git ls-remote origin "refs/heads/$BACKUP_BRANCH" | awk '{print $1}')"
[[ "$remote" == "$SUCCESSFUL_26490_HEAD" ]] || \
  fail "backup branch $BACKUP_BRANCH=$remote expected=$SUCCESSFUL_26490_HEAD"
pass "fresh backup branch exact tested 26490 checkpoint"

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
app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java
EOF_ALLOWED

# GATE 3 — exact two-file functional scope and all other 26490 bytes protected.
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
print('changed-file allowlist PASS exactTwoFunctionalFiles=true')
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

# New 26491 owners.
grep -q 'IRIS_26491_MIDTONE_OWNS_GLOBAL_DISPLAY_GAIN' "$MERGER" || fail "26491 midtone exposure owner missing"
grep -q 'float gain = Math.max(1.0f, candidateGain);' "$MERGER" || fail "26491 global gain assignment missing"
! grep -q 'candidateGain \* adaptiveReduction' "$MERGER" || fail "highlight occupancy still globally darkens scene"
grep -q 'adaptiveReduction=' "$MERGER" || fail "highlight-pressure diagnostic telemetry removed"
grep -q 'IRIS_26491_JOINT_SHORT_HDR_CHROMATICITY' "$SHORT" || fail "26491 joint short-HDR marker missing"
grep -q 'vec4 useShort = normalClip \* (flowGate \* jointConfidence);' "$SHORT" || fail "joint scalar confidence gate missing"
! grep -q 'normalClip \* shortSafe' "$SHORT" || fail "independent per-CFA phase short substitution survived"
grep -q 'vec4 recovered = max(normal, recoveredEstimate);' "$SHORT" || fail "censored-normal lower bound lost"
grep -q 'selectedShort \* shortToNormalScale \* referenceExposureScale' "$SHORT" || fail "actual short radiometry scale lost"
grep -q 'float flowConfidence = (1.0 - cancelled) \* exp(-80.0 \* variation);' "$SHORT" || fail "26490 flow confidence math changed"
grep -q 'float flowGate = smoothstep(minimumFlowConfidence, 0.80, flowConfidence);' "$SHORT" || fail "26490 flow gate changed"

# Proven 26490 architecture remains byte-protected and semantically present.
grep -q 'IRIS_26490_RCD_EXPOSURE_DOMAIN' "$RCD" || fail "physical RCD exposure domain lost"
grep -q 'iris26490PhysicalSensorWhite = 1.0f' "$RCD" || fail "physical sensor white no longer 1.0"
grep -q 'IRIS_26490_BJZHOU_RCD_PHOTO_BORDER_MIRROR_1TO1' "$RCDW" || fail "four-edge mirror RCD border lost"
grep -q 'IRIS_26490_PHYSICAL_CENSORING_WITH_LOWER_BOUND' "$RCDP" || fail "RCD censor lower-bound contract lost"
grep -q 'IRIS_26480_MAX_RGB_HIGHLIGHT_TONE_GUIDE_V2' "$RENDER" || fail "extended-linear max-RGB highlight guide lost"
grep -q 'IRIS_26489_FUSED_BAYER_CANONICAL_POST_GRAPH' "$POST" || fail "canonical Motion post graph lost"
grep -q 'IRIS_26489_BJZHOU_PERSISTENT_BAYER_ACCUMULATOR_OWNER' "$CAND/app/src/main/assets/shaders/motionv2/mfsr_bayer_accumulate.glsl" || fail "persistent Bayer accumulator owner lost"
grep -q 'IRIS_26489_ACCUMULATOR_INVARIANT_PASS' "$RECON" || fail "admitted/contributed invariant lost"
grep -q 'IRIS_26490_SHORT_CAPTURE_STARTED_IDENTITY' "$CAP" || fail "exact short capture identity owner lost"
! grep -q 'add(new MotionV2Denoise());' "$POST" || fail "MotionV2Denoise re-enabled"
pass "control-loop + protected Motion architecture PASS"

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

# GATE 5 — lexical + real glslang compile for changed compute shader.
python3 - "$SHORT" "$TMP/26491_short.comp" > "$SHADERLOG" <<'PY_SHADER'
from pathlib import Path
import sys
src=Path(sys.argv[1]).read_text()
if src.count('{')!=src.count('}') or src.count('(')!=src.count(')'):
 raise SystemExit('short shader delimiter mismatch')
if '\x00' in src: raise SystemExit('NUL in short shader')
if src.count('void main()')!=1: raise SystemExit('short shader main count invalid')
needle='#define LAYOUT //\nLAYOUT\n'
if src.count(needle)!=1: raise SystemExit('Photon LAYOUT preamble changed')
compiled='#version 310 es\n'+src.replace(needle,'layout(local_size_x=8, local_size_y=8, local_size_z=1) in;\n',1)
Path(sys.argv[2]).write_text(compiled)
print('26491 short shader lexical/interface source generation PASS')
PY_SHADER
command -v glslangValidator >/dev/null 2>&1 || fail "glslangValidator unavailable; workflow must install glslang-tools"
glslangValidator -S comp "$TMP/26491_short.comp" >> "$SHADERLOG" 2>&1 || { cat "$SHADERLOG"; fail "26491 short shader glslang compile"; }
echo "COMPUTE PASS short_highlight_bayer_recover.glsl" >> "$SHADERLOG"
cat "$SHADERLOG"
pass "changed compute shader glslang PASS"

# GATE 6 — Java lexical sanity + parse/compile candidate before full candidate APK.
python3 - "$MERGER" <<'PY_JAVA'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text()
if s.count('{')!=s.count('}'): raise SystemExit('MotionV2Merger brace mismatch')
if 'IRIS_26491_MIDTONE_OWNS_GLOBAL_DISPLAY_GAIN' not in s: raise SystemExit('26491 marker absent')
if '\x00' in s: raise SystemExit('NUL in MotionV2Merger')
print('MotionV2Merger lexical sanity PASS')
PY_JAVA
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
git diff --check -- app/src/main app/version.properties || fail "git diff --check"
pass "candidate/source validation PASS"

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
print('live pre-version exact two-file functional scope PASS')
PY_LIVE

find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$PREBUILDHASH"
sha256sum app/version.properties >> "$PREBUILDHASH"

pass "PRE-BUILD SAFETY PROOF PASSED"
echo "  exact successful 26490 GitHub artifact baseline PASS"
echo "  fresh backup branch exact 26490 PASS"
echo "  binary pre-edit exact-26490 patch before source modification PASS"
echo "  temporary-copy transform PASS"
echo "  exact two-file functional allowlist PASS"
echo "  all unrelated 26490 canonical source byte-protected PASS"
echo "  p50/p90 scene body is sole global display-gain owner PASS"
echo "  highlight occupancy/true clipping are diagnostic-only for global exposure PASS"
echo "  joint short-HDR CFA decision replaces per-phase substitution PASS"
echo "  censored-normal radiance lower bound preserved PASS"
echo "  exact 26490 short flow/radiometry interface preserved PASS"
echo "  Wronski/R32F accumulator/rejection/15-frame invariant untouched PASS"
echo "  physical RCD sensor white + four-edge mirror border untouched PASS"
echo "  extended-linear render/UHDR path untouched PASS"
echo "  MotionV2Denoise/sharpening remain disabled PASS"
echo "  changed compute shader real glslang PASS"
echo "  candidate Javac + full candidate Gradle PASS"
echo "  candidate/source byte equality PASS"
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

# GATE 8 — post-build source immutability and exact final three-file delta.
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

cat > "$TMP/allowed-final.txt" <<'EOF_FINAL'
app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl
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
print('final exact three-file 26490->26491 delta PASS')
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
26491 ADAPTIVE EXPOSURE + JOINT SHORT-HIGHLIGHT RECONSTRUCTION
===============================================================
Version=$NEW_VERSION
Build=$NEW_BUILD
Successful26490Head=$SUCCESSFUL_26490_HEAD
Successful26490ArtifactPatchSHA256=$BASE_PATCH_SHA
Successful26490ArtifactManifestSHA256=$BASE_HASHES_SHA
TransformSHA256=$TRANSFORM_SHA
BackupBranch=$BACKUP_BRANCH
BaselineReplay=NONE_OLDER_THAN_SUCCESSFUL_26490_ARTIFACT
FunctionalFilesChanged=2
GlobalExposureOwner=p50_p90_scene_body
HighlightTailGlobalExposureAuthority=false
HighlightTailTelemetryPreserved=true
ShortHdrDecision=joint_coherent_CFA_vector
IndependentPerPhaseShortSubstitution=false
PartialCensoredNeighborSearch=3x3_packed_phase_safe_common_evidence_min2
CensoredNormalLowerBound=max_normal_recovered
ShortFlowMathChanged=false
ShortHostInterfaceChanged=false
WronskiMathChanged=false
AccumulatorInvariantChanged=false
RcdPhysicalDomainChanged=false
RcdBorderChanged=false
RenderExtendedHeadroomChanged=false
MotionV2Denoise=false
Sharpening=false
TemporaryCandidateJavac=true
TemporaryCandidateFullGradleBuild=true
CandidateFinalSourceByteEqual=true
APK=$APK_NAME
APK_SHA256=$APK_SHA
EOF_REPORT

mkdir -p "$OUTDIR/next_baseline_inputs"
cp "$TRANSFORM" "$OUTDIR/next_baseline_inputs/"
cp "$0" "$OUTDIR/next_baseline_inputs/build_26491_adaptive_exposure_highlight_reconstruction_v2.sh"
if [[ -f .github/workflows/build-26491-adaptive-exposure-highlight-reconstruction-v2.yml ]]; then
 cp .github/workflows/build-26491-adaptive-exposure-highlight-reconstruction-v2.yml "$OUTDIR/next_baseline_inputs/"
fi
cp "$DELTAPATCH" "$OUTDIR/next_baseline_inputs/26491_successful_source.patch"
cp "$AFTERHASH" "$OUTDIR/next_baseline_inputs/26491_successful_after.sha256"
sha256sum "$PREPATCH" "$DELTAPATCH" "$AFTERHASH" "$REPORT" "$JAVACLOG" "$CANDLOG" "$FINALLOG" "$SHADERLOG" > "$OUTDIR/26491_artifact_hashes.sha256"

echo "APK=$APK_NAME"
echo "SHA256=$APK_SHA"
echo "26491 BUILD SUCCESS"
