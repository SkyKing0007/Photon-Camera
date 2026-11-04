#!/usr/bin/env python3
"""Deterministic exact 26901-successful 17-stage successor: Photon 26902.
Only the B/SR-OFF lens-relative sharpening curve/radius and version change;
all historical and real compiler/NDK/assemble commands inherited in order.
"""
from pathlib import Path
import hashlib,re,sys
R=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
parent=R/'build_26901_iris_rawr.sh'
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
SHA01='bcdd8bb524e5410808b4ecf2ef27760c1c28412d18389ee676c55be3509db6d9'
assert parent.is_file() and H(parent)==SHA01,'MUST use EXACT executed successful 26901 runner'
s=parent.read_text()
STAGES=('verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay')
assert tuple(x for x in re.findall(r'(?m)^([a-z_]+)\(\)\{',s) if x in STAGES)==STAGES

def once(a,b):
 global s
 n=s.count(a);assert n==1,('anchor count',n,a[:140]);s=s.replace(a,b,1)
def section(n):
 a=s.index('\n'+n+'(){')+1;b=s.index('\n}',a)+2;return s[a:b]
def rewrite(n,v):
 global s
 old=section(n);assert v.startswith(n+'(){') and v.endswith('}') and v!=old,n
 s=s.replace(old,v,1)
def append(n,src):
 old=section(n);rewrite(n,old[:-2]+'\n'+src.strip('\n')+'\n}')
# Version/runtime authorities: successful 26901 HEAD, API run, artifact metadata and
# internal exact compiled TAR reconstructed with matching actual Actions TAR SHA.
for a,b in [
 ('REPO_SCAFFOLD_BASE_COMMIT="7eadca372ef38f5d02b36f5ce7ebedc358f4ae25"','REPO_SCAFFOLD_BASE_COMMIT="ee59eeb6f4fec16af10969ed7fbf90269b11a16a"'),
 ('RUNTIME_ARTIFACT_ID="13290914419"; RUNTIME_ACTIONS_RUN="41761560619"','RUNTIME_ARTIFACT_ID="13297535320"; RUNTIME_ACTIONS_RUN="41774585178"'),
 ('RUNTIME_AUTHORITY_COMMIT="7eadca372ef38f5d02b36f5ce7ebedc358f4ae25"','RUNTIME_AUTHORITY_COMMIT="ee59eeb6f4fec16af10969ed7fbf90269b11a16a"'),
 ('RUNTIME_ARTIFACT_SHA="4f2fe4f5e2a3a5b3425556ffb6c917ade61224176d932f58d72d1fc1dde914ca"','RUNTIME_ARTIFACT_SHA="6de45e5fa5c26e581c9d010175ed8691941ce14122b64ef13fee2020e70c68a5"'),
 ('RUNTIME_TAR_SHA="f629f785bbcf89bef05bb13e0d3398f5e513847c40f7aa22d907fc0781b867fd"','RUNTIME_TAR_SHA="759109721bfc05c70c85d215542333a667107f0e652531ec9966768e8658a615"'),
 ('VERSION_NAME="0.9726901"; VERSION_BUILD="26901"','VERSION_NAME="0.9726902"; VERSION_BUILD="26902"'),
 ('OUT="$ROOT/build_26901_iris_rawr_outputs"; WORK="$ROOT/.build_26901_iris_rawr_work"','OUT="$ROOT/build_26902_iris_rawr_outputs"; WORK="$ROOT/.build_26902_iris_rawr_work"'),
 ('ARTZIP="$WORK/26900_artifact.zip"; ARTDIR="$WORK/artifact_26900"','ARTZIP="$WORK/26901_artifact.zip"; ARTDIR="$WORK/artifact_26901"'),
 ('BASE="$WORK/exact_successful_26900_compiled_candidate"; CAND="$WORK/candidate_26901"','BASE="$WORK/exact_successful_26901_compiled_candidate"; CAND="$WORK/candidate_26902"'),
 ('# IRIS_26901_AUTHORITATIVE_ACTIONS_STAGE_ORDER','# IRIS_26902_AUTHORITATIVE_ACTIONS_STAGE_ORDER'),
 ('# Successful 26900 compiled candidate is runtime authority.','# Successful 26901 compiled candidate is runtime authority.'),
]:once(a,b)
s=s.replace('$OUT/26901_','$OUT/26902_')
s=s.replace('$ARTDIR/build_26900_iris_rawr_outputs/','$ARTDIR/build_26901_iris_rawr_outputs/')

# Retain the entire original 26901 successful transform, including unchanged
# historical 26900/26899 generators, then replay 26901 on its OWN 26900 base.
old=section('make_candidate')
hist=old.replace('make_candidate(){','historical_26901_make_candidate(){',1)
new='''make_candidate(){
 local H00="$WORK/historical_26900_from_26901" H01="$WORK/historical_26901_replayed"
 mkdir -p "$H00"
 local T00="$ARTDIR/build_26901_iris_rawr_outputs/26900_historical_candidate_app_source.tar.gz"
 [[ -f "$T00" && "$(sha "$T00")" == 'f629f785bbcf89bef05bb13e0d3398f5e513847c40f7aa22d907fc0781b867fd' ]] || fail 'successful 26901 artifact historical compiled 26900 TAR missing or SHA wrong'
 tar -xzf "$T00" -C "$H00"
 (cd "$H00" && sha256sum -c "$ROOT/26901_BASE_FULL_APP.sha256" >/dev/null) || fail '26901 historical source is not original successful compiled 26900'
 (local BASE="$H00" CAND="$H01"; historical_26901_make_candidate)
 diff -qr "$H01/app" "$BASE/app" >/dev/null || fail 'replayed 26901 source differs successful compiled 26901'
 (cd "$H01" && sha256sum -c "$ROOT/26902_BASE_FULL_APP.sha256" >/dev/null) || fail 'historical 26901 must exactly reproduce current parent compiled source'
 python3 -S verify_26901.py candidate "$H00" "$H01"
 python3 -S verify_26901.py semantics "$H00" "$H01"
 python3 -S verify_26901.py patch "$H00" "$H01" 26901_FORWARD_FULL_INDEX.patch 26901_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26901.py tamper "$H00" "$H01"
 python3 -S test_26901_modes.py "$H01"
 python3 -S verify_26902.py candidate "$BASE" "$CAND" --transform
 python3 -S verify_26902.py semantics "$BASE" "$CAND"
 python3 -S test_26902_modes.py "$CAND"
}'''
assert old in s;s=s.replace(old,hist+'\n'+new,1)
H00='"$WORK/historical_26900_from_26901"';H01='"$WORK/historical_26901_replayed"'
# Keep real historical validators on historical successful sources and output
# receipts separate from current 26902 source compilation and patch proof.
for name in STAGES:
 if name in ('verify_scope','obtain_authority','make_candidate'):continue
 old=section(name);nn=old
 for kind in ('candidate','semantics','patch','tamper'):
  nn=nn.replace('verify_26901.py '+kind+' "$BASE" "$CAND"','verify_26901.py '+kind+' '+H00+' '+H01)
 nn=nn.replace('test_26901_modes.py "$CAND"','test_26901_modes.py '+H01)
 for man in ('26901_UNCHANGED_PROTECTED.sha256','26901_EXPECTED_CANDIDATE_FULL_APP.sha256'):
  nn=nn.replace('(cd "$CAND" && sha256sum -c "$ROOT/'+man+'"','(cd '+H01+' && sha256sum -c "$ROOT/'+man+'"')
 if name=='compile_modified_runtime_shaders':
  nn=nn.replace('local S="$CAND/app/src/main/assets/shaders/motionv2/$name.glsl"','local S="$WORK/historical_26901_replayed/app/src/main/assets/shaders/motionv2/$name.glsl"')
  nn=nn.replace('26902_exact_real_essl310','26901_historical_exact_real_essl310')
  nn=nn.replace('26902_GLSLANG_${name}.txt','26901_HISTORICAL_GLSLANG_${name}.txt')
  nn=nn.replace('26902_NEW_SHADER_SHA256.txt','26901_HISTORICAL_NEW_SHADER_SHA256.txt')
  nn=nn.replace('26902_CURRENT_GLSL_REAL_COMPILER_RECEIPT.txt','26901_HISTORICAL_GLSL_REAL_COMPILER_RECEIPT.txt')
  nn=nn.replace('python3 -S verify_26901.py shader','python3 -S verify_26901.py shader')
 if name=='prebuild_safety':
  nn=nn.replace('"$CAND/app/version.properties"','"$WORK/historical_26901_replayed/app/version.properties"')
  nn=nn.replace('26902_CURRENT_GLSL_REAL_COMPILER_RECEIPT.txt','26901_HISTORICAL_GLSL_REAL_COMPILER_RECEIPT.txt')
  nn=nn.replace('26902_CURRENT_PATCH_PROOF.txt','26901_HISTORICAL_PATCH_PROOF.txt')
 if name=='verify_candidate_patches':
  nn=nn.replace('26902_CURRENT_PATCH_PROOF.txt','26901_HISTORICAL_PATCH_PROOF.txt')
 if name=='postbuild_proof':
  nn=nn.replace('cp 26901_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26902_candidate_full_app.sha256"',
                'cp 26901_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26901_historical_candidate_full_app.sha256"')
  nn=nn.replace('"$OUT/26902_candidate_app_source.tar.gz','"$OUT/26901_historical_candidate_app_source.tar.gz')
  nn=nn.replace('(cd "$CAND" && tar --sort=name','(cd '+H01+' && tar --sort=name')
 if name=='clean_extract_replay':
  nn=nn.replace('"$OUT/26902_candidate_app_source.tar.gz','"$OUT/26901_historical_candidate_app_source.tar.gz')
  nn=nn.replace('diff -qr "$CAND/app" "$exp01/app"','diff -qr '+H01+'/app "$exp01/app"')
 if nn!=old:rewrite(name,nn)
# The original completed 26901 proof is required, but now as historical 26901.
ps=section('prebuild_safety');update=ps
for a,b in [
 ('runtime_authority=successful 26900 $RUNTIME_AUTHORITY_COMMIT run $RUNTIME_ACTIONS_RUN artifact $RUNTIME_ARTIFACT_ID',
  'runtime_authority=successful 26901 $RUNTIME_AUTHORITY_COMMIT run $RUNTIME_ACTIONS_RUN artifact $RUNTIME_ARTIFACT_ID'),
 ('verification_mechanics=EXACT successful 26900 executed 17 stages, real compiler/NDK/assemble commands',
  'verification_mechanics=EXACT successful 26901 executed 17 stages, real compiler/NDK/assemble commands'),
 ('runtime_changed_files=6 modified existing, 2020 protected; B OFF RGB bicubic, universal optical gate and displayed zoom sampling',
  'runtime_changed_files=3 modified existing, 2023 protected; B OFF lens-local strength/radius correction, full RGB bicubic unchanged'),
 ('protected_source=2020 files byte-identical to successful 26900 compiled candidate; DNG/native/vendor/A/Night/LONG/UHDR protected',
  'protected_source=2023 files byte-identical to successful 26901 compiled candidate; DNG/native/vendor/A/Night/LONG/UHDR protected'),
 ('infrastructure_delta=one strict successor workflow/trigger + source validators; exact successful 26900 inherited 17-stage compiler+freeze+assemble mechanics',
  'infrastructure_delta=one strict successor workflow/trigger + source validators; exact successful 26901 inherited 17-stage compiler+freeze+assemble mechanics'),
]:
 assert a in update,('safety anchor',a);update=update.replace(a,b,1)
rewrite('prebuild_safety',update)

rewrite('verify_scope','''verify_scope(){
 [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail 'wrong Photon Actions branch'
 git merge-base --is-ancestor "$REPO_SCAFFOLD_BASE_COMMIT" HEAD || fail 'successful 26901 commit not ancestor'
 [[ -z "$(git diff --name-only "$REPO_SCAFFOLD_BASE_COMMIT"..HEAD -- app/src app/version.properties)" ]] || fail 'unexpected live source mutations'
 [[ -z "$(git status --porcelain -- app/src app/version.properties)" ]] || fail 'uncommitted runtime source mutations'
 diff -u 26902_REPOSITORY_UPLOAD_ALLOWLIST.txt <(git diff --name-only "$REPO_SCAFFOLD_BASE_COMMIT"..HEAD | LC_ALL=C sort) >/dev/null || fail '26902 uploaded repository path scope changed'
 [[ "$(sha build_26901_iris_rawr.sh)" == 'bcdd8bb524e5410808b4ecf2ef27760c1c28412d18389ee676c55be3509db6d9' ]] || fail 'actual successful 26901 parent runner drift'
 pass '26902 exact successful 26901 runner plus exact uploaded repository scope'
}''')

rewrite('obtain_authority','''obtain_authority(){
 [[ -n "$TOKEN" ]] || fail 'GITHUB_TOKEN missing'
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
   "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/runs/${RUNTIME_ACTIONS_RUN}" -o "$WORK/26901_run.json"
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
   "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}" -o "$WORK/26901_artifact_metadata.json"
 python3 -S - "$WORK/26901_run.json" "$WORK/26901_artifact_metadata.json" <<'PY_AUTH_26902'
import json,sys
run=json.load(open(sys.argv[1]));art=json.load(open(sys.argv[2]))
assert run['id']==41774585178 and run['conclusion']=='success' and run['head_sha']=='ee59eeb6f4fec16af10969ed7fbf90269b11a16a' and run['head_branch']=='experimental-clean-photon-rebuild'
assert art['id']==13297535320 and art.get('expired') is False and art.get('digest')=='sha256:6de45e5fa5c26e581c9d010175ed8691941ce14122b64ef13fee2020e70c68a5'
print('PASS actual successful 26901 Actions run and artifact digest')
PY_AUTH_26902
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
   "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"
 [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail 'real successful 26901 artifact ZIP SHA mismatch'
 unzip -q "$ARTZIP" -d "$ARTDIR"
 local T="$ARTDIR/build_26901_iris_rawr_outputs/26901_candidate_app_source.tar.gz"
 [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail 'exact successful compiled 26901 TAR mismatch'
 local EXEC="$ARTDIR/build_26901_iris_rawr_outputs/exact_generated_runner/build_26901_iris_rawr.sh"
 [[ -f "$EXEC" && "$(sha "$EXEC")" == 'bcdd8bb524e5410808b4ecf2ef27760c1c28412d18389ee676c55be3509db6d9' ]] || fail '26901 executed runner mismatched'
 cmp -s "$EXEC" "$ROOT/build_26901_iris_rawr.sh" || fail 'replayed 26901 runner not exact successful Actions bytes'
 test -f "$ARTDIR/build_26901_iris_rawr_outputs/exact_generated_runner/SUCCESSFUL_ACTIONS_EVIDENCE.json" || fail '26901 executed runner receipt missing'
 for k in 'REAL GLSL COMPILE: PASS' 'REAL SPIR-V VALIDATION: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS';do
   grep -F "$k" "$ARTDIR/build_26901_iris_rawr_outputs/26901_COMPILER_STATUS.txt" >/dev/null || fail "26901 successful compiler receipt missing $k"
 done
 mkdir -p "$BASE";tar -xzf "$T" -C "$BASE"
 [[ "$(find "$BASE/app" -type f | wc -l)" -eq 2026 ]] || fail '26901 compiled candidate source count wrong'
 (cd "$BASE" && sha256sum -c "$ROOT/26902_BASE_FULL_APP.sha256" >/dev/null) || fail '26901 compiled candidate source full SHA mismatch'
 cmp -s "$ARTDIR/build_26901_iris_rawr_outputs/26901_candidate_full_app.sha256" "$ROOT/26902_BASE_FULL_APP.sha256" || fail 'base manifest not actual successful 26901 bytes'
 python3 -S verify_26902.py artifact "$ARTDIR" "$ROOT/build_26902_iris_rawr.sh"
 pass '26901 actual success, compiled source TAR, 17-stage runner, full manifests and real compiler receipts'
}''')

append('verify_package','''
 python3 -S stage_26902_root.py
 sha256sum -c 26902_HANDOFF_HASHES.sha256 >/dev/null || fail '26902 sealed staged payload drift'
 python3 -S test_26902_three_stage_negatives.py
 test -f TRIGGER_26902.txt && grep -Fx 'RUN_26902_B_OFF_LENS_RELATIVE_GENTLE_SHARPEN_V1' TRIGGER_26902.txt >/dev/null || fail '26902 immutable trigger bytes mismatch'
''')
append('compile_modified_runtime_shaders','''
 mkdir -p "$OUT/26902_exact_real_essl310"
 local S02="$CAND/app/src/main/assets/shaders/motionv2/iris26899_b_off_zoom_luma_sharpen.glsl"
 local E02="$OUT/26902_exact_real_essl310/iris26899_b_off_zoom_luma_sharpen.frag"
 { printf '#version 310 es\\n\\n#line 1\\n';cat "$S02"; } > "$E02"
 python3 -S verify_26902.py shader "$E02"
 "$IRIS26864_GLSLANG" -S frag "$E02" > "$OUT/26902_GLSLANG_iris26899_b_off_zoom_luma_sharpen.txt" 2>&1 || fail '26902 actual runtime-expanded shader must PASS pinned glslang 16.5.0'
 sha256sum "$E02" "$S02" > "$OUT/26902_NEW_SHADER_SHA256.txt"
 echo 'PASS 26902 EXACT runtime-expanded ESSL310 shader REAL PINNED GLSLANG 16.5.0' | tee "$OUT/26902_CURRENT_GLSL_REAL_COMPILER_RECEIPT.txt"
 python3 -S verify_26902.py semantics "$BASE" "$CAND"
''')
append('verify_candidate_patches','''
 python3 -S verify_26902.py candidate "$BASE" "$CAND"
 python3 -S verify_26902.py semantics "$BASE" "$CAND"
 python3 -S verify_26902.py patch "$BASE" "$CAND" 26902_FORWARD_FULL_INDEX.patch 26902_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26902_CURRENT_PATCH_PROOF.txt"
 python3 -S verify_26902.py tamper "$BASE" "$CAND"
''')
append('prebuild_safety','''
 test -s "$OUT/26901_HISTORICAL_GLSL_REAL_COMPILER_RECEIPT.txt" && grep -Fx 'PASS 26901 TWO EXACT runtime-expanded ESSL310 shaders REAL PINNED GLSLANG 16.5.0' "$OUT/26901_HISTORICAL_GLSL_REAL_COMPILER_RECEIPT.txt" >/dev/null || fail '26901 historical REAL compiled shaders missing'
 test -s "$OUT/26902_CURRENT_GLSL_REAL_COMPILER_RECEIPT.txt" && grep -Fx 'PASS 26902 EXACT runtime-expanded ESSL310 shader REAL PINNED GLSLANG 16.5.0' "$OUT/26902_CURRENT_GLSL_REAL_COMPILER_RECEIPT.txt" >/dev/null || fail '26902 changed shader REAL compiler proof missing'
 python3 -S verify_26902.py candidate "$BASE" "$CAND"
 python3 -S verify_26902.py semantics "$BASE" "$CAND"
 (cd "$CAND" && sha256sum -c "$ROOT/26902_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26902 protected source changed'
 grep -Fx 'VERSION_NAME=0.9726902' "$CAND/app/version.properties" >/dev/null
 grep -Fx 'VERSION_BUILD=26902' "$CAND/app/version.properties" >/dev/null
 test -s "$OUT/26902_CURRENT_PATCH_PROOF.txt" || fail '26902 exact current forward/rollback proof missing'
 cat >> "$OUT/26902_PREBUILD_SAFETY.txt" <<'EOF_26902_SAFETY'
26902_parent=26901 successful Actions run 41774585178 job 126391861885 commit ee59eeb6f4fec16af10969ed7fbf90269b11a16a artifact 13297535320
26902_parent_artifact_digest=6de45e5fa5c26e581c9d010175ed8691941ce14122b64ef13fee2020e70c68a5
26902_parent_compiled_tar_sha256=759109721bfc05c70c85d215542333a667107f0e652531ec9966768e8658a615
26902_parent_executed_runner_sha256=bcdd8bb524e5410808b4ecf2ef27760c1c28412d18389ee676c55be3509db6d9
26902_scope=ONLY B Super Res OFF active physical lens local zoom >=1.10 for every Android device; native optical OFF
26902_gain=lens local <=2.5 35%; <=5 40%; <=10 55%; <=15 60%; <=20 70%; (20,30] 100 to 150; >=30 150
26902_radius=uses lens-local zoom, not total Iris displayed zoom, same prior two-scale sampling formula; viewfinder unmodified
26902_bicubic=original successful 26901 independent full RGB Catmull-Rom unchanged; no denoising/blur added
26902_protected=2023 unchanged from successful 26901 compiled source; native/vendor/DNG/RAW/Sabre/Wronski/A/AB/B-ON/Night/LONG/Spektra/UHDR/50MP unchanged
26902_compilers=real pinned GLSLANG ESSL310, historical GLSL/SPIRV, Kotlin/Java, NDK and APK must pass in real Actions
EOF_26902_SAFETY
''')
append('postbuild_proof','''
 python3 -S verify_26902.py candidate "$BASE" "$CAND"
 python3 -S verify_26902.py semantics "$BASE" "$CAND"
 (cd "$CAND" && sha256sum -c "$ROOT/26902_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null) || fail '26902 candidate source changed after compilation'
 (cd "$CAND" && sha256sum -c "$ROOT/26902_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26902 postbuild protected drift'
 cp 26902_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26902_candidate_full_app.sha256"
 cp 26902_FORWARD_FULL_INDEX.patch 26902_ROLLBACK_FULL_INDEX.patch 26902_CHANGED_ALLOWLIST.txt 26902_ADDITIONS.txt 26902_DELETIONS.txt 26902_UNCHANGED_PROTECTED.sha256 "$OUT/"
 (cd "$CAND" && tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26902_candidate_app_source.tar.gz" app)
 sha256sum "$OUT/26902_candidate_app_source.tar.gz" > "$OUT/26902_candidate_app_source.tar.gz.sha256"
''')
append('clean_extract_replay','''
 python3 -S verify_26902.py candidate "$BASE" "$CAND"
 python3 -S verify_26902.py semantics "$BASE" "$CAND"
 python3 -S verify_26902.py patch "$BASE" "$CAND" 26902_FORWARD_FULL_INDEX.patch 26902_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26902.py tamper "$BASE" "$CAND"
 python3 -S test_26902_three_stage_negatives.py
 python3 -S test_26902_modes.py "$CAND"
 (cd "$CAND" && sha256sum -c "$ROOT/26902_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 (cd "$CAND" && sha256sum -c "$ROOT/26902_UNCHANGED_PROTECTED.sha256" >/dev/null)
 sha256sum -c "$OUT/26902_candidate_app_source.tar.gz.sha256" >/dev/null
 local exp02="$WORK/extracted_actual_26902_candidate_tar";rm -rf "$exp02";mkdir -p "$exp02"
 tar -xzf "$OUT/26902_candidate_app_source.tar.gz" -C "$exp02"
 diff -qr "$CAND/app" "$exp02/app" >/dev/null || fail '26902 candidate actual compiled TAR/source mismatch'
 (cd "$exp02" && sha256sum -c "$ROOT/26902_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 pass '26902 inherited exact successful 26901 17-stage order; three changed, 2023 protected, real pinned shader compiler, clean extract'
''')
assert tuple(x for x in re.findall(r'(?m)^([a-z_]+)\(\)\{',s) if x in STAGES)==STAGES
for cmd in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
 "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
 './gradlew :app:assembleDebug --stacktrace']:
 assert s.count(cmd)>=1,cmd
assert '$ARTDIR/build_26900_iris_rawr_outputs/' not in s
assert s.count('verify_26902.py patch "$BASE" "$CAND" 26902_FORWARD_FULL_INDEX.patch 26902_ROLLBACK_FULL_INDEX.patch')>=2
assert 'historical_26901_make_candidate(){' in s
assert '26901_HISTORICAL_GLSL_REAL_COMPILER_RECEIPT.txt' in s
assert '26902_CURRENT_GLSL_REAL_COMPILER_RECEIPT.txt' in s
assert '26902_candidate_app_source.tar.gz' in s
once("pass '26901 ALL 17 INHERITED GUARDED STAGES PASSED'","pass '26902 ALL 17 INHERITED GUARDED STAGES PASSED'")
p=R/'build_26902_iris_rawr.sh';p.write_text(s)
print(H(p)+'  build_26902_iris_rawr.sh')
