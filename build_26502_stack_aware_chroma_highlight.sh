#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
assert_no_patch_artifacts(){
  local label="$1"
  local report="$OUT/${label}_patch_artifacts.txt"
  find "$CAND/app" -type f \( -name '*.orig' -o -name '*.rej' \) -print | LC_ALL=C sort > "$report"
  if [[ -s "$report" ]]; then
    cat "$report" >&2
    fail "$label emitted forbidden .orig/.rej patch artifacts"
  fi
  echo "PASS: $label emitted no .orig/.rej patch artifacts"
}
ROOT="$(pwd)"
OUT="$ROOT/build_26502_stack_aware_chroma_highlight_outputs"
WORK="$ROOT/.build_26502_stack_aware_chroma_highlight_work"
BASE="$WORK/base26499"
CAND="$WORK/candidate26502"
PATCH_26501="$ROOT/26501_proper_per_frame_spatial_rgb_runtime.patch"
V6_PATCH="$ROOT/26501_v6_glsl_portability_runtime_fix.patch"
PATCH_26502="$ROOT/26502_v1_stack_aware_chroma_highlight_runtime.patch"
PRECHANGE="$ROOT/26502_PRECHANGE_26501_V6_PATCH_CHECKPOINT.txt"
BASE_TAR="$ROOT/26499_v7_successful_app_source.tar.gz"
BASE_MANIFEST="$ROOT/26499_v7_successful_after.sha256"
VALIDATOR_26501="$ROOT/validate_26501_proper_spatial_rgb.py"
VALIDATOR_26502="$ROOT/validate_26502_stack_aware_chroma_highlight.py"
INTEGRITY="$ROOT/verify_26501_source_integrity.py"
V7_SHA="ed5470179aea9514c15d52dcb35613c7925778c6"
V6_HEAD="c6415d57a0d276b6ba7d4948df45ed15ea88a410"
BACKUP_BRANCH="backup-26501-v6-before-26502-20260818"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
BASE_TAR_SHA="ce5be58fa20b9e28786b9c6e4355743066fe92e78791b50b5ee2df568c5ae9e1"
BASE_MANIFEST_SHA="9af4b1cf5411b5cae445c3e2b782e07d824c3d4a2bcd16f3c7cf28ba79b5a74f"
PATCH_26501_SHA="49dfedc17f93c636f90140125ee127a2429f3afb3c365832d97bb74e40318386"
V6_PATCH_SHA="db574aec0e3b67504fddf64d2129cb7a2a782f27eba3271f730acb1fa05df0e6"
PATCH_26502_SHA="2725bb41bdc867b2f7dfbcb41f7373ca16e00e0eb75c4acefbc8d43fb478eb28"
PRECHANGE_SHA="2f245ab137209df59838951828bb011269b45f7ea51eed808199eec70a1cc64a"
VALIDATOR_26502_SHA="34d8eca362acbf6c0d57b70b3a85f8a2d73be9e48c6e2b95865d81fe40f8beef"
rm -rf "$OUT" "$WORK"; mkdir -p "$OUT" "$BASE" "$CAND"; exec > >(tee "$OUT/26502_build.log") 2>&1

echo "=== 26502 GATE 1: BRANCH / V6 BACKUP / HANDOFF IDENTITY ==="
BRANCH="$(git branch --show-current)"; [[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || fail "branch=$BRANCH expected=$EXPECTED_BRANCH"; [[ "$BRANCH" != "dev" ]] || fail "refusing dev"
git merge-base --is-ancestor "$V7_SHA" HEAD || fail "26499/V7 commit is not an ancestor of HEAD"
git merge-base --is-ancestor "$V6_HEAD" HEAD || fail "26501 V6 commit is not an ancestor of HEAD"
git rev-parse --verify "origin/$BACKUP_BRANCH" >/dev/null 2>&1 || fail "verified V6 backup branch is missing from origin"
[[ "$(git rev-parse "origin/$BACKUP_BRANCH")" == "$V6_HEAD" ]] || fail "V6 backup branch no longer points to exact V6 commit"
DIRECT_RUNTIME_DIFF="$OUT/26502_direct_runtime_diff.txt"; git diff --name-only "$V7_SHA"..HEAD -- app/src/main app/version.properties > "$DIRECT_RUNTIME_DIFF"
if [[ -s "$DIRECT_RUNTIME_DIFF" ]]; then git diff --name-status "$V7_SHA"..HEAD -- app/src/main app/version.properties >&2 || true; fail "handoff commit directly modified runtime app source"; fi
for f in "$PATCH_26501" "$V6_PATCH" "$PATCH_26502" "$PRECHANGE" "$BASE_TAR" "$BASE_MANIFEST" "$VALIDATOR_26501" "$VALIDATOR_26502" "$INTEGRITY"; do [[ -f "$f" ]] || fail "missing handoff file: $(basename "$f")"; done
[[ "$(sha "$BASE_TAR")" == "$BASE_TAR_SHA" ]] || fail "26499 successful source tar hash mismatch"
[[ "$(sha "$BASE_MANIFEST")" == "$BASE_MANIFEST_SHA" ]] || fail "26499 successful manifest hash mismatch"
[[ "$(sha "$PATCH_26501")" == "$PATCH_26501_SHA" ]] || fail "26501 runtime patch hash mismatch"
[[ "$(sha "$V6_PATCH")" == "$V6_PATCH_SHA" ]] || fail "26501 V6 portability patch hash mismatch"
[[ "$(sha "$PATCH_26502")" == "$PATCH_26502_SHA" ]] || fail "26502 runtime patch hash mismatch"
[[ "$(sha "$PRECHANGE")" == "$PRECHANGE_SHA" ]] || fail "26502 pre-change checkpoint hash mismatch"
[[ "$(sha "$VALIDATOR_26502")" == "$VALIDATOR_26502_SHA" ]] || fail "26502 validator hash mismatch"
echo "PASS: exact tested 26501 V6 backup + patch checkpoint verified before source transform"

echo "=== 26502 GATE 2: RECONSTRUCT EXACT SUCCESSFUL 26499 SOURCE ==="
tar -xzf "$BASE_TAR" -C "$BASE"; [[ -f "$BASE/app/version.properties" ]] || fail "base extraction missing version"
( cd "$BASE" && sha256sum -c "$BASE_MANIFEST" ) > "$OUT/26499_manifest_check.txt"
[[ "$(wc -l < "$BASE_MANIFEST")" -eq 865 ]] || fail "26499 manifest count must be 865"
BASE_COUNT="$({ find "$BASE/app/src/main" -type f -print; echo "$BASE/app/version.properties"; } | wc -l)"; [[ "$BASE_COUNT" -eq 865 ]] || fail "26499 extracted file count=$BASE_COUNT expected=865"
[[ "$(grep '^VERSION_NAME=' "$BASE/app/version.properties" | cut -d= -f2)" == "0.9726499" ]] || fail "base version name is not 26499"
[[ "$(grep '^VERSION_BUILD=' "$BASE/app/version.properties" | cut -d= -f2)" == "26499" ]] || fail "base version build is not 26499"
cp -a "$BASE/app" "$CAND/app"; echo "PASS: exact successful 26499 source reconstructed and hash-verified (865/865)"

echo "=== 26502 GATE 3: REBUILD TESTED V6, THEN APPLY ONLY NARROW 26502 DELTA ==="
patch --dry-run --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 -d "$CAND" < "$PATCH_26501" > "$OUT/26501_patch_dry_run.txt"; patch --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 -d "$CAND" < "$PATCH_26501" > "$OUT/26501_patch_apply.txt"
assert_no_patch_artifacts "26501_runtime_patch"
V6_SHADER_REL="app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_contribute_26501.glsl"; cp "$CAND/$V6_SHADER_REL" "$OUT/26501_v5_contribute_pre_v6.glsl"
patch --dry-run --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 -d "$CAND" < "$V6_PATCH" > "$OUT/26501_v6_glsl_patch_dry_run.txt"; patch --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 -d "$CAND" < "$V6_PATCH" > "$OUT/26501_v6_glsl_patch_apply.txt"
assert_no_patch_artifacts "26501_v6_glsl_patch"
python3 - "$OUT/26501_v5_contribute_pre_v6.glsl" "$CAND/$V6_SHADER_REL" <<'PY'
from pathlib import Path
import sys
before=Path(sys.argv[1]).read_text(); after=Path(sys.argv[2]).read_text(); restored=after.replace('ownedPixel','sample').replace('precisionMatrix','precision').replace('packedCoord','packed')
if restored!=before: raise SystemExit('V6 GLSL portability patch changed more than reserved identifier names')
print('PASS: V6 GLSL portability patch is identifier-only; reconstruction math is byte-equivalent')
PY
python3 "$VALIDATOR_26501" "$CAND" --base "$BASE" | tee "$OUT/26501_v6_prechange_validator.txt"
python3 - "$BASE/app" "$CAND/app" "$OUT/26501_v6_scope.txt" <<'PY'
from pathlib import Path
import hashlib,sys,json
b,c,o=map(Path,sys.argv[1:]); h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest(); bf={p.relative_to(b).as_posix():p for p in b.rglob('*') if p.is_file()}; cf={p.relative_to(c).as_posix():p for p in c.rglob('*') if p.is_file()}
new=sorted(set(cf)-set(bf)); rem=sorted(set(bf)-set(cf)); mod=sorted(k for k in bf.keys()&cf.keys() if h(bf[k])!=h(cf[k])); o.write_text('MODIFIED\n'+'\n'.join(mod)+'\nNEW\n'+'\n'.join(new)+'\nREMOVED\n'+'\n'.join(rem)+'\n'); assert len(mod)==5,(len(mod),mod); assert len(new)==4,(len(new),new); assert not rem,rem
Path(str(o)+'.json').write_text(json.dumps({k:h(v) for k,v in cf.items()},sort_keys=True,indent=2)); print('PASS: exact tested V6 runtime reconstructed: 5 modified + 4 new')
PY
patch --dry-run --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 -d "$CAND" < "$PATCH_26502" > "$OUT/26502_patch_dry_run.txt"; patch --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 -d "$CAND" < "$PATCH_26502" > "$OUT/26502_patch_apply.txt"
assert_no_patch_artifacts "26502_runtime_patch"
python3 "$VALIDATOR_26502" "$CAND" --patch "$PATCH_26502" | tee "$OUT/26502_prebuild_validator.txt"
python3 - "$CAND/app" "$OUT/26501_v6_scope.txt.json" "$OUT/26502_delta_scope.txt" <<'PY'
from pathlib import Path
import hashlib,json,sys
root,snap_path,out=Path(sys.argv[1]),Path(sys.argv[2]),Path(sys.argv[3]); h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest(); before=json.loads(snap_path.read_text()); after={p.relative_to(root).as_posix():h(p) for p in root.rglob('*') if p.is_file()}
new=sorted(set(after)-set(before)); rem=sorted(set(before)-set(after)); mod=sorted(k for k in before.keys()&after.keys() if before[k]!=after[k]); expected=['src/main/assets/shaders/motionv2/mfsr_spatial_rgb_normalize_26501.glsl','src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java']
out.write_text('MODIFIED_FROM_V6\n'+'\n'.join(mod)+'\nNEW_FROM_V6\n'+'\n'.join(new)+'\nREMOVED_FROM_V6\n'+'\n'.join(rem)+'\n'); assert mod==expected,(mod,expected); assert not new,new; assert not rem,rem; print('PASS: 26502 delta from tested V6 is exactly two modified files, zero new/removed')
PY
python3 - "$BASE/app" "$CAND/app" "$OUT/26502_final_scope_from_26499.txt" <<'PY'
from pathlib import Path
import hashlib,sys
b,c,o=map(Path,sys.argv[1:]); h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest(); bf={p.relative_to(b).as_posix():p for p in b.rglob('*') if p.is_file()}; cf={p.relative_to(c).as_posix():p for p in c.rglob('*') if p.is_file()}; new=sorted(set(cf)-set(bf)); rem=sorted(set(bf)-set(cf)); mod=sorted(k for k in bf.keys()&cf.keys() if h(bf[k])!=h(cf[k])); o.write_text('MODIFIED\n'+'\n'.join(mod)+'\nNEW\n'+'\n'.join(new)+'\nREMOVED\n'+'\n'.join(rem)+'\n'); assert len(mod)==5,(len(mod),mod); assert len(new)==4,(len(new),new); assert not rem,rem; print('PASS: final 26502 remains inside V6 5-modified + 4-new architecture envelope')
PY

assert_no_patch_artifacts "26502_preflight_final_candidate"
echo "=== 26502 GATE 4: REAL GLSL / JAVA / FROZEN-PATH PREFLIGHT ==="
command -v glslangValidator >/dev/null 2>&1 || fail "glslangValidator missing on runner"
python3 - "$CAND" "$OUT" <<'PY'
from pathlib import Path
import subprocess,sys,re
root,out=Path(sys.argv[1]),Path(sys.argv[2]); items=[('app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_chroma_guide_26501.glsl','frag'),('app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_contribute_26501.glsl','frag'),('app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_normalize_26501.glsl','frag'),('app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_short_weight_26501.glsl','comp'),('app/src/main/assets/shaders/motionv2/shadow_aux_bayer_fuse.glsl','comp'),('app/src/main/assets/shaders/motionv2/render.glsl','frag'),('app/src/main/assets/shaders/motionv2/mfsr_mgc_covariance.glsl','comp')]
reserved={'sample','precision','packed','common','partition','active','asm','class','union','enum','typedef','template','this','resource','goto','inline','noinline','public','static','extern','external','interface','long','short','half','fixed','unsigned','superp','input','output','hvec2','hvec3','hvec4','fvec2','fvec3','fvec4','sampler3DRect','filter','sizeof','cast','namespace','using','row_major'}; type_re=r'(?:bool|int|uint|float|double|vec[234]|ivec[234]|uvec[234]|bvec[234]|dvec[234]|mat[234](?:x[234])?|dmat[234](?:x[234])?|[iu]?sampler\w+|[iu]?image\w+)'; log=[]
for rel,stage in items:
 src=(root/rel).read_text(); clean=re.sub(r'/\*.*?\*/',' ',src,flags=re.S); clean=re.sub(r'//.*',' ',clean); hits=[]
 for m in re.finditer(r'\b'+type_re+r'\s+([A-Za-z_]\w*)',clean):
  if m.group(1) in reserved: hits.append((clean.count('\n',0,m.start())+1,m.group(1)))
 if hits: raise SystemExit(f'{rel}: GLSL reserved declared identifiers: {hits}')
 p=root/rel
 if stage=='comp':
  if not src.startswith('#define LAYOUT //'): raise SystemExit(f'{rel}: missing Photon LAYOUT define')
  src=src.replace('#define LAYOUT //','#define LAYOUT layout(local_size_x=8, local_size_y=8, local_size_z=1) in;',1)
 tmp=out/(p.name+'.'+stage); tmp.write_text('#version 310 es\n'+src); cp=subprocess.run(['glslangValidator','-S',stage,str(tmp)],capture_output=True,text=True); diagnostic=f'{rel}: rc={cp.returncode}\n{cp.stdout}{cp.stderr}'; log.append(diagnostic)
 if cp.returncode: (out/'26502_glsl_validation.txt').write_text('\n'.join(log)); print(diagnostic,file=sys.stderr); raise SystemExit(cp.returncode)
 for lineno,line in enumerate((root/rel).read_text().splitlines(),1):
  if 'layout' not in line: continue
  if line.count('layout(')>1: raise SystemExit(f'{rel}:{lineno}: multiple layout declarations on one physical line')
  l=line.find('('); r=line.rfind(')')
  if l<0 or r<l: raise SystemExit(f'{rel}:{lineno}: malformed layout declaration')
  for param in line[l+1:r].split(','):
   if '=' in param:
    key,val=param.replace(' ','').split('=',1)
    if key in {'binding','location','local_size_x','local_size_y','local_size_z'}: int(val)
(out/'26502_glsl_validation.txt').write_text('\n'.join(log)); print('PASS: seven active V6/26502 shaders compile with real glslang and Photon layout parser')
PY
javac -proc:none -Xmaxerrs 10000 -d "$WORK/javac_parse" "$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java" "$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java" "$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java" > "$OUT/26502_javac_parse.log" 2>&1 || true
python3 - "$OUT/26502_javac_parse.log" <<'PY'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text(errors='replace'); patterns=['; expected','illegal start of','reached end of file while parsing',"')' expected",chr(125)+"' expected",'not a statement','class, interface, enum, or record expected','unclosed']; hits=[line for line in s.splitlines() if any(p in line for p in patterns)]
if hits: raise SystemExit('Java parse diagnostics: '+repr(hits[:20]))
print('PASS: modified Java files contain no javac syntax/parse diagnostics')
PY
grep -Fxq 'src/main/assets/shaders/motionv2/mfsr_spatial_rgb_normalize_26501.glsl' "$OUT/26502_delta_scope.txt"; grep -Fxq 'src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java' "$OUT/26502_delta_scope.txt"
if grep -E 'GalleryManager|Dng|Capture|capture|render\.glsl|PostPipeline|MotionV2CfaInput' "$OUT/26502_delta_scope.txt"; then fail "forbidden RAW/capture/render/post path changed in 26502 delta"; fi
[[ "$(grep '^VERSION_NAME=' "$CAND/app/version.properties" | cut -d= -f2)" == "0.9726499" ]] || fail "version changed before safety proof"; [[ "$(grep '^VERSION_BUILD=' "$CAND/app/version.properties" | cut -d= -f2)" == "26499" ]] || fail "build changed before safety proof"
echo "PRE-BUILD SAFETY PROOF PASSED"

echo "=== 26502 GATE 5: VERSION BUMP + EXACT CANDIDATE OVERLAY ==="
python3 - "$CAND/app/version.properties" <<'PY'
from pathlib import Path
import re,sys
p=Path(sys.argv[1]); s=p.read_text(); s=re.sub(r'^VERSION_NAME=.*$','VERSION_NAME=0.9726502',s,flags=re.M); s=re.sub(r'^VERSION_BUILD=.*$','VERSION_BUILD=26502',s,flags=re.M); p.write_text(s)
PY
[[ -f "$ROOT/app/build.gradle" ]] || fail "app/build.gradle missing before overlay"; find "$ROOT/app" -maxdepth 1 -type f ! -name version.properties -print0 | sort -z | xargs -0 sha256sum > "$OUT/app_module_shell_before.sha256"; rm -rf "$ROOT/app/src/main"; rm -f "$ROOT/app/version.properties"; cp -a "$CAND/app/src/main" "$ROOT/app/src/main"; cp -a "$CAND/app/version.properties" "$ROOT/app/version.properties"; find "$ROOT/app" -maxdepth 1 -type f ! -name version.properties -print0 | sort -z | xargs -0 sha256sum > "$OUT/app_module_shell_after.sha256"; diff -u "$OUT/app_module_shell_before.sha256" "$OUT/app_module_shell_after.sha256" > "$OUT/app_module_shell_diff.txt" || fail "Android app module shell changed"
[[ "$(grep '^VERSION_NAME=' app/version.properties | cut -d= -f2)" == "0.9726502" ]] || fail "version bump failed"; [[ "$(grep '^VERSION_BUILD=' app/version.properties | cut -d= -f2)" == "26502" ]] || fail "build bump failed"
python3 - "$CAND" "$ROOT" <<'PY'
from pathlib import Path
import hashlib,sys
a,b=Path(sys.argv[1]),Path(sys.argv[2])
def collect(root):
 out={}
 for p in (root/'app/src/main').rglob('*'):
  if p.is_file(): out[p.relative_to(root).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
 p=root/'app/version.properties'; out[p.relative_to(root).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest(); return out
x,y=collect(a),collect(b)
if x!=y:
 bad=sorted(k for k in set(x)|set(y) if x.get(k)!=y.get(k)); raise SystemExit('candidate/final canonical source mismatch: '+repr(bad[:50]))
print('PASS: full candidate/final canonical source parity before Gradle')
PY
echo "PASS: version 0.9726502 / 26502 applied only after safety proof"

echo "=== 26502 GATE 6: REAL APP BUILD IN SAME GUARDED SCRIPT ==="
python3 "$INTEGRITY" snapshot "$ROOT/app" "$OUT/26502_pre_gradle_app_manifest.json"; chmod +x ./gradlew; ./gradlew clean :app:assembleDebug --stacktrace; python3 "$INTEGRITY" verify "$ROOT/app" "$OUT/26502_pre_gradle_app_manifest.json" | tee "$OUT/26502_post_gradle_integrity.txt"
mapfile -t APKS < <(find app/build -type f -name '*.apk' 2>/dev/null | sort); [[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one APK under app/build, found ${#APKS[@]}: ${APKS[*]-}"; APK_BASENAME="$(basename "${APKS[0]}")"; [[ "$APK_BASENAME" == "IrisCamera-0.9726502-26502-debug.apk" ]] || fail "unexpected APK identity: $APK_BASENAME"
FINAL="$ROOT/IrisCamera-0.9726502-26502-stack-aware-chroma-highlight-debug.apk"; rm -f "$ROOT"/*.apk; cp "${APKS[0]}" "$FINAL"; sha256sum "$FINAL" > "$OUT/26502_apk.sha256"; echo "PASS: :app:assembleDebug produced exactly one expected 26502 APK"

echo "=== 26502 GATE 7: EMIT CLEAN SUCCESSFUL SOURCE CHECKPOINT ==="
( cd "$CAND" && tar --sort=name --mtime='UTC 2026-08-18 00:00:00' --owner=0 --group=0 --numeric-owner -czf "$OUT/26502_successful_app_source.tar.gz" app/src/main app/version.properties )
( cd "$CAND" && { find app/src/main -type f -print; echo app/version.properties; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done ) > "$OUT/26502_successful_after.sha256"; [[ "$(wc -l < "$OUT/26502_successful_after.sha256")" -eq 869 ]] || fail "26502 successful source manifest expected 869 files"
SUCCESS_TAR_LIST="$OUT/26502_successful_app_source.list"; tar -tzf "$OUT/26502_successful_app_source.tar.gz" > "$SUCCESS_TAR_LIST"; for generated in archive.h archive_entry.h technicallyflac.h tiny_dng_writer.h; do if grep -Fxq "app/src/main/cpp/deps/$generated" "$SUCCESS_TAR_LIST"; then fail "generated dependency leaked into successful source: $generated"; fi; done
sha256sum "$PATCH_26501" "$V6_PATCH" "$PATCH_26502" "$PRECHANGE" "$BASE_TAR" "$BASE_MANIFEST" "$FINAL" "$OUT/26502_successful_app_source.tar.gz" > "$OUT/26502_artifact_hashes.sha256"
cat > "$OUT/26502_build_report.txt" <<EOF
26502 Stack-Aware Chroma + Continuous Highlight Reliability
Branch: $BRANCH
Tested V6 checkpoint: $V6_HEAD
Verified V6 backup branch: $BACKUP_BRANCH
Rollback/base source: $V7_SHA (26499/V7) + exact 26501/V6 patchset
Version: 0.9726502 / 26502
APK: $(basename "$FINAL")
APK SHA256: $(sha "$FINAL")
26502 delta from V6: exactly 2 modified files; 0 new; 0 removed
RAW/DNG export: unchanged; no computational-RAW conversion
Capture/ZSL/frame roles: unchanged; no shadow-long capture added
Wronski alignment/rejection: unchanged
Short-A validation/admission: unchanged
Semantic accumulation: unchanged; G/R-G/B-G V6 owner preserved
Shadow cleanup: low-signal R-G/B-G only, support-aware and green-edge-aware before display lift
Luma/green structure: no spatial luma blur added
Highlight behavior: packed censor state is reliability only; supported RGB is repaired from already-admitted neighboring semantic evidence
True exhausted highlights: still converge to phase-invariant neutral endpoint
Lens shading -> calculation-WB removal -> Camera2 color transform order: unchanged
Render shoulder / tone / UHDR geometry: unchanged
Sharpening / ESD / ABLC / ADRC / old Photon noise model: unchanged/off
EOF
echo "PASS: APK built exactly once and clean successful-source checkpoint emitted"; echo "PASS: 26502 STACK-AWARE CHROMA + HIGHLIGHT BUILD COMPLETE: $FINAL"
