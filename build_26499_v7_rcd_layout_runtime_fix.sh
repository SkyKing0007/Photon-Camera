#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
OUT="$ROOT/build_26499_v7_rcd_layout_runtime_fix_outputs"
rm -rf "$OUT" && mkdir -p "$OUT"
LOG="$OUT/26499_v7_rcd_layout_runtime_fix_build.log"
exec > >(tee "$LOG") 2>&1

BASE_SHA="ce75a5c0bb206e0ad35ea3e963cf60208c53acc9"
PROVEN_V6_EFFECTIVE_SHA="7fd2298ad060988b4d24fd8dbe4803439741f4f2b1e899879df5966cc91de7e2"
TESTED_26497="00deeae2c82518511988ca6267b2e6071300cba6"
BACKUP_V13="backup-26498-v1.1-before-v1.3-daylight-root-fixes"
BACKUP_26497="backup-26497-tested-regression-before-26498-root-architecture"
BACKUP_V6="backup-26498-v1.3-recovery-v6-before-v7-rcd-layout-fix"
V6_INFRA_SHA="3756e4323594a5d61fe66cf0cca9694ae8543495"
V7_PATCH="26498_V1_3_RECOVERY_V7_RCD_LAYOUT_FIX.patch"
EXPECTED_V7_PATCH="7f28e8f65fd78ba1d92f3fc53155156419bd38b4878438c1f5bb0f1f2ac9be23"
CANON_TAR="26494_successful_app_source.tar.gz"
CANON_MAN="26494_successful_after.sha256"
ROOT_PATCH="26498_source_delta_from_exact_26494.patch"
ORIG_VALIDATOR="validate_26498_root_architecture.py"
V13_TRANSFORM="transform_26498_v1_3_daylight_root_fixes.py"
V13_VALIDATOR="validate_26498_v1_3.py"
EXPECTED_TAR="ee4ccb614d9cb216e2e39a76adc8f72ce9fe2a07daa75eb6f705e958502e010b"
EXPECTED_MAN="939a7555adaf1b9859e8fc9e40798b38ac5b85343dfbdb45cfe34a4a88b500c7"
EXPECTED_ROOT_PATCH="988691939ff9ac70a6c0ece1eae03a44c5d0f46cb4a541448c94bd10ad0106a3"
EXPECTED_ORIG_VALIDATOR="cf0a86765bb078c5f7c611b3d20b3a9cada1a42e5bd623ee98ac0da84cc14f83"

fail(){ echo "ERROR: $*" >&2; exit 1; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
require_hash(){ [[ -f "$1" ]] || fail "missing $1"; [[ "$(sha "$1")" == "$2" ]] || fail "hash mismatch: $1"; }

BRANCH="$(git branch --show-current)"
[[ "$BRANCH" == "experimental-clean-photon-rebuild" ]] || fail "wrong branch: $BRANCH"
[[ "$BRANCH" != "dev" ]] || fail "refusing dev"
git merge-base --is-ancestor "$BASE_SHA" HEAD || fail "HEAD is not an infrastructure-only descendant of $BASE_SHA"
git merge-base --is-ancestor "$V6_INFRA_SHA" HEAD || fail "HEAD does not contain exact V6 infrastructure checkpoint"
git diff --quiet "$BASE_SHA" HEAD -- app || fail "app/ differs from guarded $BASE_SHA before V7 build"

git fetch --quiet origin "$BACKUP_V13" "$BACKUP_26497" "$BACKUP_V6" || fail "required runtime backup fetch failed"
[[ "$(git rev-parse "origin/$BACKUP_V13")" == "$BASE_SHA" ]] || fail "$BACKUP_V13 does not point to $BASE_SHA"
[[ "$(git rev-parse "origin/$BACKUP_26497")" == "$TESTED_26497" ]] || fail "$BACKUP_26497 does not point to tested 26497"
[[ "$(git rev-parse "origin/$BACKUP_V6")" == "$V6_INFRA_SHA" ]] || fail "$BACKUP_V6 does not point to exact V6 checkpoint"
echo "PASS: branch/lineage/dev protection and V6 pre-V7 backup"

require_hash "$CANON_TAR" "$EXPECTED_TAR"
require_hash "$CANON_MAN" "$EXPECTED_MAN"
require_hash "$ROOT_PATCH" "$EXPECTED_ROOT_PATCH"
require_hash "$ORIG_VALIDATOR" "$EXPECTED_ORIG_VALIDATOR"
require_hash "$V7_PATCH" "$EXPECTED_V7_PATCH"
[[ -f "$V13_TRANSFORM" && -f "$V13_VALIDATOR" ]] || fail "V1.3 handoff files missing"
echo "PASS: immutable 26494 + original 26498 identities + exact V7 runtime patch"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
BASE="$TMP/base26494"
CAND="$TMP/candidate"
PREV13="$TMP/pre_v13"
mkdir -p "$BASE" "$CAND"
tar -xzf "$CANON_TAR" -C "$BASE"
[[ "$(find "$BASE/app" -type f | wc -l)" -eq 856 ]] || fail "canonical file count != 856"
( cd "$BASE" && sha256sum -c "$ROOT/$CANON_MAN" ) > "$OUT/26494_manifest_check.txt"
BASE_MANIFEST_OK_COUNT="$(grep -c ': OK$' "$OUT/26494_manifest_check.txt")"
[[ "$BASE_MANIFEST_OK_COUNT" -eq 856 ]] || fail "26494 baseline manifest pass count=$BASE_MANIFEST_OK_COUNT expected=856"
cp -a "$BASE/." "$CAND/"
echo "PASS: exact 856-file 26494 baseline reconstructed"

snapshot_patch(){
  local src="$1" out="$2"
  : > "$out"
  (
    cd "$src"
    while IFS= read -r -d '' f; do
      local_rc=0
      git diff --no-index --binary -- /dev/null "$f" >> "$out" || local_rc=$?
      [[ "$local_rc" -eq 0 || "$local_rc" -eq 1 ]] || exit "$local_rc"
    done < <(find app -type f -print0 | sort -z)
  )
}
# Complete immutable baseline patch BEFORE candidate source edits.
snapshot_patch "$CAND" "$OUT/26498_v1_3_pre_edit_exact_26494_complete_binary.patch"
sha256sum "$OUT/26498_v1_3_pre_edit_exact_26494_complete_binary.patch" > "$OUT/26498_v1_3_pre_edit_exact_26494_complete_binary.patch.sha256"
[[ -s "$OUT/26498_v1_3_pre_edit_exact_26494_complete_binary.patch" ]] || fail "canonical pre-edit patch empty"
# Complete current checked-out app snapshot before any repo app replacement.
snapshot_patch "$ROOT" "$OUT/26498_v1_3_repo_pre_edit_complete_binary.patch"
sha256sum "$OUT/26498_v1_3_repo_pre_edit_complete_binary.patch" > "$OUT/26498_v1_3_repo_pre_edit_complete_binary.patch.sha256"
[[ -s "$OUT/26498_v1_3_repo_pre_edit_complete_binary.patch" ]] || fail "repo pre-edit patch empty"
echo "PASS: complete binary pre-edit patches created before source modification"

( cd "$CAND" && git apply --check "$ROOT/$ROOT_PATCH" && git apply "$ROOT/$ROOT_PATCH" )
python - "$BASE/app" "$CAND/app" <<'PY' | tee "$OUT/26498_original_patch_scope.txt"
from pathlib import Path
import hashlib,sys
A,B=map(Path,sys.argv[1:])
def h(root): return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
a,b=h(A),h(B)
changed=sorted(k for k in a.keys()&b.keys() if a[k]!=b[k]); new=sorted(b.keys()-a); removed=sorted(a.keys()-b)
print('modified',len(changed)); print('new',len(new)); print('removed',len(removed));
for x in changed: print('M',x)
for x in new: print('A',x)
for x in removed: print('D',x)
assert len(changed)==8, changed
assert len(new)==8, new
assert not removed, removed
assert sum(1 for k in a if k in b and a[k]==b[k])==848
PY
python "$ORIG_VALIDATOR" | tee "$OUT/26498_original_synthetic_validation.txt"
echo "PASS: immutable original 26498 root patch cleanly reapplied with exact 8M+8A scope"

cp -a "$CAND" "$PREV13"
python "$V13_TRANSFORM" --self-test | tee "$OUT/26498_v1_3_transform_selftest.txt"
python "$V13_TRANSFORM" "$CAND" | tee "$OUT/26498_v1_3_transform.txt"
python - "$PREV13/app" "$CAND/app" <<'PY' | tee "$OUT/26498_v1_3_scope.txt"
from pathlib import Path
import hashlib,sys
A,B=map(Path,sys.argv[1:])
def h(root): return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
a,b=h(A),h(B)
changed=sorted(k for k in a.keys()&b.keys() if a[k]!=b[k]); new=sorted(b.keys()-a); removed=sorted(a.keys()-b)
exp_changed=sorted([
 'src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl',
 'src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
 'src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java',
 'src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java'])
exp_new=['src/main/assets/shaders/motionv2/shadow_aux_bayer_fuse.glsl']
print('modified',changed); print('new',new); print('removed',removed)
assert changed==exp_changed,(changed,exp_changed)
assert new==exp_new,(new,exp_new)
assert not removed,removed
PY
python "$V13_VALIDATOR" "$CAND" --full | tee "$OUT/26498_v1_3_validation.txt"
echo "PASS: exact V1.3 source scope + ownership validator"

# V7 runtime-portability correction. Formatting-only: every GLSL token/math operation
# is preserved while new 26498 resource declarations are made compatible with
# Photon's line-oriented GLInterface.getLayouts() parser.
PREV7="$TMP/pre_v7"
cp -a "$CAND" "$PREV7"
( cd "$CAND" && git apply --check "$ROOT/$V7_PATCH" && git apply "$ROOT/$V7_PATCH" )
python - "$PREV7/app" "$CAND/app" <<'PYV7SCOPE'
from pathlib import Path
import hashlib,re,sys
A,B=map(Path,sys.argv[1:])
expected=sorted([
 'src/main/assets/shaders/motionv2/rcd26498_diag_residual.glsl',
 'src/main/assets/shaders/motionv2/rcd26498_green.glsl',
 'src/main/assets/shaders/motionv2/rcd26498_green_rb.glsl',
 'src/main/assets/shaders/motionv2/rcd26498_lpf.glsl',
 'src/main/assets/shaders/motionv2/rcd26498_opposite.glsl',
 'src/main/assets/shaders/motionv2/rcd26498_populate.glsl',
 'src/main/assets/shaders/motionv2/rcd26498_vh_direction.glsl',
 'src/main/assets/shaders/motionv2/rcd26498_write.glsl',
 'src/main/assets/shaders/motionv2/shadow_aux_bayer_fuse.glsl',
])
def hashes(root):
    return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}
a,b=hashes(A),hashes(B)
changed=sorted(k for k in a.keys()&b.keys() if a[k]!=b[k])
new=sorted(b.keys()-a); removed=sorted(a.keys()-b)
assert changed==expected,(changed,expected)
assert not new,new
assert not removed,removed
for rel in expected:
    before=(A/rel).read_text(); after=(B/rel).read_text()
    assert re.sub(r'\s+','',before)==re.sub(r'\s+','',after), rel
    print('PASS token-equivalent formatting-only',rel)
print('PASS: exact 9-file V7 scope; zero semantic GLSL-token changes')
PYV7SCOPE

python - "$CAND/app/src/main/assets/shaders/motionv2" <<'PYV7PARSER'
from pathlib import Path
import sys
root=Path(sys.argv[1])
expected={
 'rcd26498_populate.glsl': {'CfaBuf':0,'RedBuf':1,'GreenBuf':2,'BlueBuf':3,'TrustBuf':9},
 'rcd26498_green.glsl': {'CfaBuf':0,'GreenBuf':2,'VhBuf':4,'LpfBuf':5,'TrustBuf':9},
 'rcd26498_lpf.glsl': {'CfaBuf':0,'LpfBuf':5,'TrustBuf':9},
 'rcd26498_vh_direction.glsl': {'CfaBuf':0,'VhBuf':4,'TrustBuf':9},
 'rcd26498_diag_residual.glsl': {'CfaBuf':0,'PBuf':6,'QBuf':7,'TrustBuf':9},
 'rcd26498_green_rb.glsl': {'RedBuf':1,'GreenBuf':2,'BlueBuf':3,'VhBuf':4,'TrustBuf':9},
 'rcd26498_opposite.glsl': {'RedBuf':1,'GreenBuf':2,'BlueBuf':3,'PqBuf':8,'TrustBuf':9},
 'rcd26498_write.glsl': {'RedBuf':1,'GreenBuf':2,'BlueBuf':3,'OutputRgb':9},
 'shadow_aux_bayer_fuse.glsl': {'outCfa':0,'ShadowDiagBuf':3},
}
def get_parameter(parts,name):
    for x in parts:
        pv=x.replace(' ','').split('=')
        if len(pv)>=2 and pv[0]==name:
            return int(pv[1])
    return 0
def parse(src):
    out={}
    for val in src.splitlines():
        if 'layout' not in val: continue
        assert val.count('layout(')<=1, val
        left=val.find('('); right=val.rfind(')')
        if left<0 or right<left: continue
        divided=val.replace('{','').split(' ')
        while divided and divided[-1]=='': divided.pop()  # Java String.split drops trailing empties
        last=divided[-1].replace(';','').replace('\n','') if divided else ''
        params=val[left+1:right].split(',')
        if last=='in': continue
        out[last]=get_parameter(params,'binding')
    return out
for name,want in expected.items():
    src=(root/name).read_text(); got=parse(src)
    for k,v in want.items(): assert got.get(k)==v,(name,k,v,got)
    for line in src.splitlines():
        if 'layout(' in line and 'buffer ' in line:
            assert line.rstrip().endswith('{'),(name,line)
    print('PASS Photon parser',name,want)
print('PASS: all V7 RCD/shadow layouts are discoverable by GLInterface.getLayouts()')
PYV7PARSER

echo "PASS: V7 formatting-only RCD/shadow parser correction + exact Java-parser emulation"

# Protected architecture hashes: V1.3 may not touch these from successful 26494.
python - "$BASE/app" "$CAND/app" <<'PY' | tee "$OUT/26498_v1_3_protected_hashes.txt"
from pathlib import Path
import hashlib,sys
A,B=map(Path,sys.argv[1:])
protected=[
 'src/main/assets/shaders/motionv2/mfsr_bayer_accumulate.glsl',
 'src/main/assets/shaders/motionv2/mfsr_bayer_normalize.glsl',
 'src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java',
 'src/main/assets/shaders/motionv2/render.glsl',
 'src/main/assets/shaders/motionv2/color_transform.glsl',
 'src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java']
protected += sorted(p.relative_to(A).as_posix() for p in A.rglob('rcd26489*.glsl'))
for rel in protected:
    pa,pb=A/rel,B/rel
    assert pa.is_file() and pb.is_file(), rel
    ha=hashlib.sha256(pa.read_bytes()).hexdigest(); hb=hashlib.sha256(pb.read_bytes()).hexdigest()
    assert ha==hb,(rel,ha,hb)
    print('PASS',rel,ha)
PY

# Structural Short-A owner proof; legacy method may exist but cannot have a call site.
python - "$CAND/app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java" <<'PY' | tee "$OUT/26498_v1_3_short_owner.txt"
from pathlib import Path
import re,sys
s=Path(sys.argv[1]).read_text()
name='applyMotion26486ExplicitShortCaptureIfNeeded'
defs=len(re.findall(r'private\s+boolean\s+'+name+r'\s*\(',s))
mentions=len(re.findall(r'\b'+name+r'\s*\(',s))
assert defs==1,(defs,mentions)
assert mentions==2,(defs,mentions) # definition + exactly one active call
assert s.count('MOTION_26480_SHORT_TAG')>=2
assert 'MOTION_26480_SHORT_PROTECTION_EV = 2.5' in s or 'MOTION_26480_SHORT_PROTECTION_EV=2.5' in s
print('PASS: active Short-A definitions=1 calls=1; -2.5 EV policy retained')
PY

# Normal cohort / shadow negative ownership proofs.
python - "$PREV13/app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java" "$CAND/app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java" <<'PY' | tee "$OUT/26498_v1_3_cohort_proof.txt"
from pathlib import Path
import re,sys
pre,post=map(lambda x:Path(x).read_text(),sys.argv[1:])
for token in ['MOTION_26486_EXPOSURE_HALF_WINDOW_EV = 0.05','MOTION_26486_MAX_GROUP_SPAN_EV']:
    assert token in pre and token in post,token
# The normal candidate admission predicate remains present exactly once.
for token in ['motionExposurePairMatches(frameResult, bestExposureGroup)','selected.add(frame);']:
    assert post.count(token)==pre.count(token),(token,pre.count(token),post.count(token))
assert post.count('shadowAuxSlot.offer(irisV13ShadowAuxFrame)')==1
assert 'shortNeverNormalFusion=true shadowNeverNormalFusion=true' in post
print('PASS: normal cohort constants/admission path retained; shadow auxiliary not admitted')
PY

# Version remains unmodified until ALL pre-build safety checks pass.
[[ "$(grep '^VERSION_NAME=' "$CAND/app/version.properties" | cut -d= -f2)" == "0.9726494" ]] || fail "candidate version changed before safety proof"
[[ "$(grep '^VERSION_BUILD=' "$CAND/app/version.properties" | cut -d= -f2)" == "26494" ]] || fail "candidate build changed before safety proof"

echo "PRE-BUILD SAFETY PROOF PASSED"

# Faithful Photon LAYOUT GLSL preflight for every GLSL path changed by original 26498 + V1.3.
if command -v glslangValidator >/dev/null 2>&1; then
  python - "$ROOT_PATCH" "$CAND" "$OUT" <<'PY'
from pathlib import Path
import re,sys,subprocess
patch=Path(sys.argv[1]).read_text(); root=Path(sys.argv[2]); out=Path(sys.argv[3])
paths=set(re.findall(r'^\+\+\+ b/(app/src/main/assets/shaders/motionv2/[^\s]+\.glsl)$',patch,re.M))
paths.add('app/src/main/assets/shaders/motionv2/shadow_aux_bayer_fuse.glsl')
paths.add('app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl')
log=[]
for rel in sorted(paths):
    p=root/rel
    if not p.is_file(): continue
    src=p.read_text()
    compute='gl_GlobalInvocationID' in src or 'gl_GlobalInvocationID' in src
    if src.startswith('#define LAYOUT //'):
        repl='#define LAYOUT layout(local_size_x=8, local_size_y=8, local_size_z=1) in;' if compute else '#define LAYOUT'
        src=src.replace('#define LAYOUT //',repl,1)
    wrapper='#version 310 es\n'+src
    ext='.comp' if compute else '.frag'
    tmp=out/(p.name+ext)
    tmp.write_text(wrapper)
    cp=subprocess.run(['glslangValidator','-S','comp' if compute else 'frag',str(tmp)],capture_output=True,text=True)
    log.append(f'{rel}: rc={cp.returncode}\n{cp.stdout}{cp.stderr}')
    if cp.returncode: raise SystemExit('\n'.join(log))
(out/'26498_v1_3_glsl_validation.txt').write_text('\n'.join(log))
print(f'PASS: GLSL preflight compiled {len(paths)} changed/new shader paths with Photon LAYOUT invocation preserved')
PY
else
  echo "ERROR: glslangValidator missing on runner"; exit 1
fi

# Only now bump version and replace checkout app source.
python - "$CAND/app/version.properties" <<'PY'
from pathlib import Path
import sys,re
p=Path(sys.argv[1]); s=p.read_text()
s=re.sub(r'^VERSION_NAME=.*$', 'VERSION_NAME=0.9726499', s, flags=re.M)
s=re.sub(r'^VERSION_BUILD=.*$', 'VERSION_BUILD=26499', s, flags=re.M)
p.write_text(s)
PY
# Preserve the complete checked-out Android app module shell.  The canonical 26494
# bundle intentionally owns only app/src/main + app/version.properties (856 files);
# it does NOT contain app/build.gradle or other module-level Gradle scaffolding.
[[ -f "$ROOT/app/build.gradle" ]] || fail "app/build.gradle missing before canonical runtime-source overlay"
find "$ROOT/app" -maxdepth 1 -type f ! -name 'version.properties' -print0 | sort -z | \
  xargs -0 sha256sum > "$OUT/26498_v1_3_app_module_shell_before.sha256"
rm -rf "$ROOT/app/src/main"
rm -f "$ROOT/app/version.properties"
cp -a "$CAND/app/src/main" "$ROOT/app/src/main"
cp -a "$CAND/app/version.properties" "$ROOT/app/version.properties"
[[ -f "$ROOT/app/build.gradle" ]] || fail "app/build.gradle lost during canonical runtime-source overlay"
find "$ROOT/app" -maxdepth 1 -type f ! -name 'version.properties' -print0 | sort -z | \
  xargs -0 sha256sum > "$OUT/26498_v1_3_app_module_shell_after.sha256"
diff -u "$OUT/26498_v1_3_app_module_shell_before.sha256" \
        "$OUT/26498_v1_3_app_module_shell_after.sha256" \
  > "$OUT/26498_v1_3_app_module_shell_diff.txt" || fail "app module shell changed during runtime-source overlay"
echo "PASS: preserved full app Gradle module shell while overlaying canonical runtime source"

echo "PASS: version bumped to 0.9726499 / 26499 only after safety proof"

# Build in the SAME guarded script/command block.
# The exact candidate-owned runtime set is 865 files. Gradle is allowed to download
# only its four gitignored native dependency headers; every pre-existing app file
# remains hash-protected.
CAND_OWNED_COUNT="$(
  { find "$CAND/app/src/main" -type f -print; echo "$CAND/app/version.properties"; } | wc -l
)"
[[ "$CAND_OWNED_COUNT" -eq 865 ]] || fail "pre-Gradle candidate-owned file count=$CAND_OWNED_COUNT expected=865"
python3 "$ROOT/verify_26498_v1_3_recovery_v5_source_integrity.py" snapshot \
  "$ROOT/app" "$OUT/26498_v1_3_pre_gradle_app_manifest.json"
chmod +x ./gradlew
# Explicitly require the Android application module. A root-level assembleDebug may
# otherwise report BUILD SUCCESSFUL after assembling only circularbarlib.
./gradlew clean :app:assembleDebug --stacktrace
python3 "$ROOT/verify_26498_v1_3_recovery_v5_source_integrity.py" verify \
  "$ROOT/app" "$OUT/26498_v1_3_pre_gradle_app_manifest.json" \
  | tee "$OUT/26498_v1_3_post_gradle_integrity.txt"
echo "PASS: Gradle preserved all pre-existing app files; only expected ignored native deps were generated"

mapfile -t APKS < <(find app/build -type f -name '*.apk' 2>/dev/null | sort)
if [[ "${#APKS[@]}" -ne 1 ]]; then
  echo "APK DISCOVERY DIAGNOSTICS: expected one APK beneath app/build" >&2
  if [[ -d app/build ]]; then
    find app/build -maxdepth 8 -type f | sort | tail -200 >&2 || true
  else
    echo "app/build does not exist" >&2
  fi
  fail "expected exactly one app APK, found ${#APKS[@]}: ${APKS[*]-}"
fi
APK_BASENAME="$(basename "${APKS[0]}")"
[[ "$APK_BASENAME" == "IrisCamera-0.9726499-26499-debug.apk" ]] || \
  fail "unexpected app APK identity: $APK_BASENAME"
echo "PASS: :app:assembleDebug produced exactly one expected APK: ${APKS[0]}"
FINAL="$ROOT/IrisCamera-0.9726499-26499-v7-rcd-layout-runtime-fix-debug.apk"
rm -f "$ROOT"/*.apk
cp "${APKS[0]}" "$FINAL"
sha256sum "$FINAL" > "$OUT/26498_v1_3_apk.sha256"

# Emit exact successful SOURCE bundle/manifest from the preserved CLEAN candidate,
# never from the Gradle-augmented checkout. This guarantees generated cpp/deps headers
# cannot leak into the next canonical source baseline.
( cd "$CAND" && \
  tar --sort=name --mtime='UTC 2026-08-17 00:00:00' --owner=0 --group=0 --numeric-owner \
      -czf "$OUT/26498_v1_3_successful_app_source.tar.gz" app/src/main app/version.properties )
( cd "$CAND" && \
  { find app/src/main -type f -print; echo app/version.properties; } | LC_ALL=C sort | \
  while read -r f; do sha256sum "$f"; done ) > "$OUT/26498_v1_3_successful_after.sha256"
[[ "$(wc -l < "$OUT/26498_v1_3_successful_after.sha256")" -eq 865 ]] || \
  fail "successful canonical runtime-source manifest must contain exactly 865 files"
for generated in archive.h archive_entry.h technicallyflac.h tiny_dng_writer.h; do
  ! tar -tzf "$OUT/26498_v1_3_successful_app_source.tar.gz" | \
    grep -qx "app/src/main/cpp/deps/$generated" || \
    fail "generated dependency leaked into successful source archive: $generated"
done
( cd "$BASE" && git diff --no-index --binary -- app "$CAND/app" || [[ $? -eq 1 ]] ) > "$OUT/26498_v1_3_complete_binary_delta_from_26494.patch"
sha256sum "$OUT"/* "$FINAL" > "$OUT/26498_v1_3_artifact_hashes.sha256" || true

cat > "$OUT/26498_v1_3_build_report.txt" <<EOF
26499 V7 RCD layout runtime-portability correction over 26498 V1.3
Branch: $BRANCH
Lineage base: $BASE_SHA
Proven V6 effective-script SHA256: $PROVEN_V6_EFFECTIVE_SHA
Backup V6: $BACKUP_V6 -> $V6_INFRA_SHA
Version: 0.9726499 / 26499
APK: $(basename "$FINAL")
APK SHA256: $(sha "$FINAL")
Normal exposure cohort: unchanged +/-0.05 EV, <=0.10 EV group span
Short A: one owner, -2.5 EV, Wronski-reference-owned correspondence; merged CFA final need/target
Shadow auxiliary: max one, pre-shutter frozen ring, newest qualifying 1.5x-4x exposure energy, separate slot, same Wronski reference, exposure/support gated, max blend 0.20, no generic Photon noiseS ownership
V7 runtime fix: formatting-only GLInterface layout compatibility across 8 rcd26498 shaders + shadow_aux_bayer_fuse; GLSL tokens unchanged
Extra GPU drain: none
Second temporal stack/demosaic: none
EOF

echo "PASS: APK built exactly once and checkpoint artifacts emitted"
echo "PASS: 26499 V7 RCD LAYOUT RUNTIME FIX BUILD COMPLETE: $FINAL"
