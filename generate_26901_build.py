#!/usr/bin/env python3
"""SHA-pinned exact successful Photon 26900 17-stage runner successor.
Historical 26900 runs on its original successful 26899/26900 sources, never on
new 26901 bytes. All compiler/assemble/historical commands remain inherited.
"""
from pathlib import Path
import hashlib,re,sys
R=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve();parent=R/'build_26900_iris_rawr.sh'
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert parent.is_file() and H(parent)=='1671e0a86fb85573da2cfbffa1c12502cf4153e4e15e548d0bc9bf4a15254cf6','EXACT successful executed 26900 runner required'
s=parent.read_text()
STAGES=('verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics',
'prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader',
'install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff',
'compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay')
assert tuple(x for x in re.findall(r'(?m)^([a-z_]+)\(\)\{',s) if x in STAGES)==STAGES

def once(a,b):
 global s
 assert s.count(a)==1,('anchor',a[:100],s.count(a))
 s=s.replace(a,b,1)
def section(n):
 a=s.index('\n'+n+'(){')+1;b=s.index('\n}',a)+2
 return s[a:b]
def rewrite(n,v):
 global s
 old=section(n);assert v.startswith(n+'(){') and v.endswith('}') and v!=old,n
 s=s.replace(old,v,1)
def append(n,txt):
 old=section(n);rewrite(n,old[:-2]+'\n'+txt.strip('\n')+'\n}')

for a,b in [
 ('REPO_SCAFFOLD_BASE_COMMIT="5a3e3eee6086398021f57f4b4f9de24ba125af24"','REPO_SCAFFOLD_BASE_COMMIT="7eadca372ef38f5d02b36f5ce7ebedc358f4ae25"'),
 ('RUNTIME_ARTIFACT_ID="13264802004"; RUNTIME_ACTIONS_RUN="41700527054"','RUNTIME_ARTIFACT_ID="13290914419"; RUNTIME_ACTIONS_RUN="41761560619"'),
 ('RUNTIME_AUTHORITY_COMMIT="5a3e3eee6086398021f57f4b4f9de24ba125af24"','RUNTIME_AUTHORITY_COMMIT="7eadca372ef38f5d02b36f5ce7ebedc358f4ae25"'),
 ('RUNTIME_ARTIFACT_SHA="de648a61f7c4639c84c384d2ff6cbec1d057d9377cb1b47a52e0d5bc34036ff9"','RUNTIME_ARTIFACT_SHA="4f2fe4f5e2a3a5b3425556ffb6c917ade61224176d932f58d72d1fc1dde914ca"'),
 ('RUNTIME_TAR_SHA="b468173a2eae7100f3180b8a178e37961dc1c0465560fad90113e8181507c80f"','RUNTIME_TAR_SHA="f629f785bbcf89bef05bb13e0d3398f5e513847c40f7aa22d907fc0781b867fd"'),
 ('VERSION_NAME="0.9726900"; VERSION_BUILD="26900"','VERSION_NAME="0.9726901"; VERSION_BUILD="26901"'),
 ('OUT="$ROOT/build_26900_iris_rawr_outputs"; WORK="$ROOT/.build_26900_iris_rawr_work"','OUT="$ROOT/build_26901_iris_rawr_outputs"; WORK="$ROOT/.build_26901_iris_rawr_work"'),
 ('ARTZIP="$WORK/26899_artifact.zip"; ARTDIR="$WORK/artifact_26899"','ARTZIP="$WORK/26900_artifact.zip"; ARTDIR="$WORK/artifact_26900"'),
 ('BASE="$WORK/exact_successful_26899_compiled_candidate"; CAND="$WORK/candidate_26900"','BASE="$WORK/exact_successful_26900_compiled_candidate"; CAND="$WORK/candidate_26901"'),
 ('# IRIS_26900_AUTHORITATIVE_ACTIONS_STAGE_ORDER','# IRIS_26901_AUTHORITATIVE_ACTIONS_STAGE_ORDER'),
 ('# Successful 26899 V2 compiled candidate is runtime authority.','# Successful 26900 compiled candidate is runtime authority.'),
]:once(a,b)
# Successor-specific output names, never change historical source/test names.
s=s.replace('$OUT/26900_','$OUT/26901_')
# The ACTUAL successful parent artifact's internal upload root is 26900.
# This rewrites ALL old historical static operands, including the V1 SPV path.
s=s.replace('$ARTDIR/build_26899_iris_rawr_outputs/','$ARTDIR/build_26900_iris_rawr_outputs/')
# Make the original, unchanged 26900 candidate transform historical only.
old=section('make_candidate')
historical=old.replace('make_candidate(){','historical_26900_make_candidate(){',1)
new='''make_candidate(){
 local H99="$WORK/historical_26899_from_26900" H00="$WORK/historical_26900_replayed"
 mkdir -p "$H99"
 local T99="$ARTDIR/build_26900_iris_rawr_outputs/26899_historical_candidate_app_source.tar.gz"
 [[ -f "$T99" && "$(sha "$T99")" == 'b468173a2eae7100f3180b8a178e37961dc1c0465560fad90113e8181507c80f' ]] || fail 'actual 26900 historical successful 26899 TAR mismatch'
 tar -xzf "$T99" -C "$H99"
 (cd "$H99" && sha256sum -c "$ROOT/26900_BASE_FULL_APP.sha256" >/dev/null) || fail 'historical 26900 source must use original successful 26899 bytes'
 (local BASE="$H99" CAND="$H00"; historical_26900_make_candidate)
 diff -qr "$H00/app" "$BASE/app" >/dev/null || fail 'historical derived 26900 not identical to exact successful compiled 26900'
 python3 -S verify_26900.py candidate "$H99" "$H00"
 python3 -S verify_26900.py semantics "$H99" "$H00"
 python3 -S verify_26900.py patch "$H99" "$H00" 26900_FORWARD_FULL_INDEX.patch 26900_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26900.py tamper "$H99" "$H00"
 python3 -S test_26900_modes.py "$H00"
 python3 -S verify_26901.py candidate "$BASE" "$CAND" --transform
 python3 -S verify_26901.py semantics "$BASE" "$CAND"
 python3 -S test_26901_modes.py "$CAND"
}'''
assert old in s;s=s.replace(old,historical+'\n'+new,1)
H99='"$WORK/historical_26899_from_26900"';H00='"$WORK/historical_26900_replayed"'
for name in STAGES:
 if name in ('verify_scope','obtain_authority','make_candidate'):continue
 old=section(name);nn=old
 # Running 26900 historical proofs on ACTUAL old 26899/26900 bytes, not new candidate.
 for kind in ('candidate','semantics','patch','tamper'):
  nn=nn.replace('verify_26900.py '+kind+' "$BASE" "$CAND"',
                'verify_26900.py '+kind+' '+H99+' '+H00)
 nn=nn.replace('test_26900_modes.py "$CAND"','test_26900_modes.py '+H00)
 for man in ('26900_UNCHANGED_PROTECTED.sha256','26900_EXPECTED_CANDIDATE_FULL_APP.sha256'):
  nn=nn.replace('(cd "$CAND" && sha256sum -c "$ROOT/'+man+'"',
                '(cd '+H00+' && sha256sum -c "$ROOT/'+man+'"')
 if name=='compile_modified_runtime_shaders':
  nn=nn.replace('S="$CAND/app/src/main/assets/shaders/motionv2/$name.glsl"',
                'S="$WORK/historical_26900_replayed/app/src/main/assets/shaders/motionv2/$name.glsl"')
  nn=nn.replace('26901_CURRENT_GLSL_REAL_COMPILER_RECEIPT.txt','26900_HISTORICAL_GLSL_REAL_COMPILER_RECEIPT.txt')
  # Keep historical real GLSL compiler results separate from the new shader outputs.
  nn=nn.replace('$OUT/26901_exact_real_essl310','$OUT/26900_historical_exact_real_essl310')
  nn=nn.replace('$OUT/26901_GLSLANG_${name}.txt','$OUT/26900_HISTORICAL_GLSLANG_${name}.txt')
  nn=nn.replace('sha256sum "$E" "$S" >> "$OUT/26901_NEW_SHADER_SHA256.txt"',
                'sha256sum "$E" "$S" >> "$OUT/26900_HISTORICAL_NEW_SHADER_SHA256.txt"')
  nn=nn.replace('26901_NEW_SHADER_GLSLANG_16_5_0.txt','26899_HISTORICAL_GLSLANG_16_5_0.txt')
  nn=nn.replace('sha256sum "$E99" "$S99" > "$OUT/26901_NEW_SHADER_SHA256.txt"',
                'sha256sum "$E99" "$S99" > "$OUT/26899_HISTORICAL_NEW_SHADER_SHA256.txt"')
 if name=='prebuild_safety':
  nn=nn.replace('"$CAND/app/version.properties"','"$WORK/historical_26900_replayed/app/version.properties"')
  nn=nn.replace('26901_NEW_SHADER_GLSLANG_16_5_0.txt','26899_HISTORICAL_GLSLANG_16_5_0.txt')
  nn=nn.replace('26901_CURRENT_GLSL_REAL_COMPILER_RECEIPT.txt','26900_HISTORICAL_GLSL_REAL_COMPILER_RECEIPT.txt')
  nn=nn.replace('26901_CURRENT_PATCH_PROOF.txt','26900_HISTORICAL_PATCH_PROOF.txt')
 if name=='verify_candidate_patches':
  nn=nn.replace('26901_CURRENT_PATCH_PROOF.txt','26900_HISTORICAL_PATCH_PROOF.txt')
 if name=='postbuild_proof':
  nn=nn.replace('cp 26900_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26901_candidate_full_app.sha256"',
                'cp 26900_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26900_historical_candidate_full_app.sha256"')
  nn=nn.replace('"$OUT/26901_candidate_app_source.tar.gz','"$OUT/26900_historical_candidate_app_source.tar.gz')
  nn=nn.replace('(cd "$CAND" && tar --sort=name','(cd '+H00+' && tar --sort=name')
 if name=='clean_extract_replay':
  nn=nn.replace('"$OUT/26901_candidate_app_source.tar.gz','"$OUT/26900_historical_candidate_app_source.tar.gz')
  nn=nn.replace('diff -qr "$CAND/app" "$exp00/app"', 'diff -qr '+H00+'/app "$exp00/app"')
 if nn!=old:rewrite(name,nn)
# Inherited historical safety descriptions must not misidentify NEW source authority.
ps=section('prebuild_safety');updated=ps
for a,b in [
 ('runtime_authority=successful 26899 V2 $RUNTIME_AUTHORITY_COMMIT run $RUNTIME_ACTIONS_RUN artifact $RUNTIME_ARTIFACT_ID',
  'runtime_authority=successful 26900 $RUNTIME_AUTHORITY_COMMIT run $RUNTIME_ACTIONS_RUN artifact $RUNTIME_ARTIFACT_ID'),
 ('verification_mechanics=EXACT successful 26899 V2 executed 17 stages, real compiler/NDK/assemble commands',
  'verification_mechanics=EXACT successful 26900 executed 17 stages, real compiler/NDK/assemble commands'),
 ('runtime_changed_files=4 modified existing, 2022 protected; B OFF bicubic luminance + scale-adaptive aggressive 26899 sharpening',
  'runtime_changed_files=6 modified existing, 2020 protected; B OFF RGB bicubic, universal optical gate and displayed zoom sampling'),
 ('protected_source=2022 files byte-identical to successful 26899 V2 compiled candidate; DNG/native/vendor/A/Night/LONG/UHDR protected',
  'protected_source=2020 files byte-identical to successful 26900 compiled candidate; DNG/native/vendor/A/Night/LONG/UHDR protected'),
 ('infrastructure_delta=one strict successor workflow/trigger + source validators; exact successful 26899 V2 inherited 17-stage compiler+freeze+assemble mechanics',
  'infrastructure_delta=one strict successor workflow/trigger + source validators; exact successful 26900 inherited 17-stage compiler+freeze+assemble mechanics')]:
 assert a in updated,('safety anchor',a);updated=updated.replace(a,b,1)
rewrite('prebuild_safety',updated)

rewrite('verify_scope','''verify_scope(){
 [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail 'wrong Photon Actions branch'
 git merge-base --is-ancestor "$REPO_SCAFFOLD_BASE_COMMIT" HEAD || fail '26900 successful commit not ancestor'
 [[ -z "$(git diff --name-only "$REPO_SCAFFOLD_BASE_COMMIT"..HEAD -- app/src app/version.properties)" ]] || fail 'unexpected live source modifications'
 [[ -z "$(git status --porcelain -- app/src app/version.properties)" ]] || fail 'uncommitted runtime source modifications'
 diff -u 26901_REPOSITORY_UPLOAD_ALLOWLIST.txt <(git diff --name-only "$REPO_SCAFFOLD_BASE_COMMIT"..HEAD | LC_ALL=C sort) >/dev/null || fail '26901 uploaded repository path scope changed'
 [[ "$(sha build_26900_iris_rawr.sh)" == '1671e0a86fb85573da2cfbffa1c12502cf4153e4e15e548d0bc9bf4a15254cf6' ]] || fail '26900 actual successful parent runner drift'
 pass '26901 actual successful 26900 runner plus exact frozen repository delta'
}''')
rewrite('obtain_authority','''obtain_authority(){
 [[ -n "$TOKEN" ]] || fail 'GITHUB_TOKEN missing'
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
   "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/runs/${RUNTIME_ACTIONS_RUN}" -o "$WORK/26900_run.json"
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
   "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}" -o "$WORK/26900_artifact_metadata.json"
 python3 -S - "$WORK/26900_run.json" "$WORK/26900_artifact_metadata.json" <<'PY_AUTH_26901'
import json,sys
run=json.load(open(sys.argv[1]));art=json.load(open(sys.argv[2]))
assert run['id']==41761560619 and run['conclusion']=='success' and run['head_sha']=='7eadca372ef38f5d02b36f5ce7ebedc358f4ae25' and run['head_branch']=='experimental-clean-photon-rebuild'
assert art['id']==13290914419 and art.get('expired') is False and art.get('digest')=='sha256:4f2fe4f5e2a3a5b3425556ffb6c917ade61224176d932f58d72d1fc1dde914ca'
print('PASS exact successful 26900 Actions run/artifact digest')
PY_AUTH_26901
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
   "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"
 [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail 'real successful 26900 artifact ZIP SHA mismatch'
 unzip -q "$ARTZIP" -d "$ARTDIR"
 local T="$ARTDIR/build_26900_iris_rawr_outputs/26900_candidate_app_source.tar.gz"
 [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail 'exact successful compiled 26900 TAR mismatch'
 local EXEC="$ARTDIR/build_26900_iris_rawr_outputs/exact_generated_runner/build_26900_iris_rawr.sh"
 [[ -f "$EXEC" && "$(sha "$EXEC")" == '1671e0a86fb85573da2cfbffa1c12502cf4153e4e15e548d0bc9bf4a15254cf6' ]] || fail '26900 actual executed runner mismatched'
 cmp -s "$EXEC" "$ROOT/build_26900_iris_rawr.sh" || fail 'generated historical 26900 runner not exact successful Actions bytes'
 test -f "$ARTDIR/build_26900_iris_rawr_outputs/exact_generated_runner/SUCCESSFUL_ACTIONS_EVIDENCE.json" || fail '26900 executed runner receipt missing'
 for k in 'REAL GLSL COMPILE: PASS' 'REAL SPIR-V VALIDATION: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS';do
   grep -F "$k" "$ARTDIR/build_26900_iris_rawr_outputs/26900_COMPILER_STATUS.txt" >/dev/null || fail "26900 successful real compiler proof missing $k"
 done
 mkdir -p "$BASE";tar -xzf "$T" -C "$BASE"
 [[ "$(find "$BASE/app" -type f | wc -l)" -eq 2026 ]] || fail '26900 source count wrong'
 (cd "$BASE" && sha256sum -c "$ROOT/26901_BASE_FULL_APP.sha256" >/dev/null) || fail '26900 compiled source full manifest mismatch'
 cmp -s "$ARTDIR/build_26900_iris_rawr_outputs/26900_candidate_full_app.sha256" "$ROOT/26901_BASE_FULL_APP.sha256" || fail '26901 base manifest not exact successful Actions bytes'
 python3 -S verify_26901.py artifact "$ARTDIR" "$ROOT/build_26901_iris_rawr.sh"
 pass '26900 exact successful candidate/executed runner/GLES310/native/Kotlin/Java/assemble/artifact references'
}''')

append('verify_package','''
 python3 -S stage_26901_root.py
 sha256sum -c 26901_HANDOFF_HASHES.sha256 >/dev/null || fail '26901 sealed staged handoff drift'
 python3 -S test_26901_three_stage_negatives.py
 test -f TRIGGER_26901.txt && grep -Fx 'RUN_26901_B_OFF_FULL_RGB_BICUBIC_UNIVERSAL_LENS_GATE_V1' TRIGGER_26901.txt >/dev/null || fail '26901 exact trigger mismatch'
''')
append('compile_modified_runtime_shaders','''
 mkdir -p "$OUT/26901_exact_real_essl310"
 for name in render iris26899_b_off_zoom_luma_sharpen;do
   local S="$CAND/app/src/main/assets/shaders/motionv2/$name.glsl"
   local E="$OUT/26901_exact_real_essl310/$name.frag"
   { printf '#version 310 es\\n\\n#line 1\\n';cat "$S"; } > "$E"
   python3 -S verify_26901.py shader "$E"
   "$IRIS26864_GLSLANG" -S frag "$E" > "$OUT/26901_GLSLANG_${name}.txt" 2>&1 || fail "26901 real PINNED GLSLANG 16.5.0 ESSL310 compile failed: $name"
   sha256sum "$E" "$S" >> "$OUT/26901_NEW_SHADER_SHA256.txt"
 done
 echo 'PASS 26901 TWO EXACT runtime-expanded ESSL310 shaders REAL PINNED GLSLANG 16.5.0' | tee "$OUT/26901_CURRENT_GLSL_REAL_COMPILER_RECEIPT.txt"
 python3 -S verify_26901.py semantics "$BASE" "$CAND"
''')
append('verify_candidate_patches','''
 python3 -S verify_26901.py candidate "$BASE" "$CAND"
 python3 -S verify_26901.py semantics "$BASE" "$CAND"
 python3 -S verify_26901.py patch "$BASE" "$CAND" 26901_FORWARD_FULL_INDEX.patch 26901_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26901_CURRENT_PATCH_PROOF.txt"
 python3 -S verify_26901.py tamper "$BASE" "$CAND"
''')
append('prebuild_safety','''
 test -s "$OUT/26901_CURRENT_GLSL_REAL_COMPILER_RECEIPT.txt" && grep -Fx 'PASS 26901 TWO EXACT runtime-expanded ESSL310 shaders REAL PINNED GLSLANG 16.5.0' "$OUT/26901_CURRENT_GLSL_REAL_COMPILER_RECEIPT.txt" >/dev/null || fail '26901 real changed shader compiler proof missing'
 python3 -S verify_26901.py candidate "$BASE" "$CAND"
 python3 -S verify_26901.py semantics "$BASE" "$CAND"
 (cd "$CAND" && sha256sum -c "$ROOT/26901_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26901 protected file mutation'
 grep -Fx 'VERSION_NAME=0.9726901' "$CAND/app/version.properties" >/dev/null
 grep -Fx 'VERSION_BUILD=26901' "$CAND/app/version.properties" >/dev/null
 test -s "$OUT/26901_CURRENT_PATCH_PROOF.txt" || fail '26901 full-index real patch proof missing'
 cat >> "$OUT/26901_PREBUILD_SAFETY.txt" <<'EOF_26901_SAFETY'
26901_parent=26900 successful run 41761560619 job 126350185660 commit 7eadca372ef38f5d02b36f5ce7ebedc358f4ae25 artifact 13290914419
26901_parent_artifact_digest=4f2fe4f5e2a3a5b3425556ffb6c917ade61224176d932f58d72d1fc1dde914ca
26901_parent_compiled_tar_sha256=f629f785bbcf89bef05bb13e0d3398f5e513847c40f7aa22d907fc0781b867fd
26901_parent_executed_runner_sha256=1671e0a86fb85573da2cfbffa1c12502cf4153e4e15e548d0bc9bf4a15254cf6
26901_scope=only shutter selected B Super Res OFF active physical lens outputLocalZoom >=1.10; no native optical sharpening
26901_curve=total displayed global zoom original 26899/26900 +100...+200 and SAME displayed total zoom drives two-scale radius
26901_bicubic=independent full RGB 4x4 Catmull-Rom final crop enlargement, per-channel central extrema clamp; no extra processing stage
26901_noise=no added noise suppression; original temporal fusion/Sabre/RAWR/demosaic unchanged
26901_protected=2020 source files unchanged from real 26900 successful compiled authority, no add/delete, native/vendor/DNG/A/AB/B-SR-ON/Night/LONG/Spektra/UHDR untouched
26901_compilers=real pinned ESSL310 shader compiles and inherited 17-stage language/NDK/full APK must PASS in Actions
EOF_26901_SAFETY
''')
append('postbuild_proof','''
 python3 -S verify_26901.py candidate "$BASE" "$CAND"
 python3 -S verify_26901.py semantics "$BASE" "$CAND"
 (cd "$CAND" && sha256sum -c "$ROOT/26901_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null) || fail '26901 candidate source drift'
 (cd "$CAND" && sha256sum -c "$ROOT/26901_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26901 postbuild protected drift'
 cp 26901_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26901_candidate_full_app.sha256"
 cp 26901_FORWARD_FULL_INDEX.patch 26901_ROLLBACK_FULL_INDEX.patch 26901_CHANGED_ALLOWLIST.txt 26901_ADDITIONS.txt 26901_DELETIONS.txt 26901_UNCHANGED_PROTECTED.sha256 "$OUT/"
 (cd "$CAND" && tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26901_candidate_app_source.tar.gz" app)
 sha256sum "$OUT/26901_candidate_app_source.tar.gz" > "$OUT/26901_candidate_app_source.tar.gz.sha256"
''')
append('clean_extract_replay','''
 python3 -S verify_26901.py candidate "$BASE" "$CAND"
 python3 -S verify_26901.py semantics "$BASE" "$CAND"
 python3 -S verify_26901.py patch "$BASE" "$CAND" 26901_FORWARD_FULL_INDEX.patch 26901_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26901.py tamper "$BASE" "$CAND"
 python3 -S test_26901_three_stage_negatives.py
 python3 -S test_26901_modes.py "$CAND"
 (cd "$CAND" && sha256sum -c "$ROOT/26901_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 (cd "$CAND" && sha256sum -c "$ROOT/26901_UNCHANGED_PROTECTED.sha256" >/dev/null)
 sha256sum -c "$OUT/26901_candidate_app_source.tar.gz.sha256" >/dev/null
 local exp01="$WORK/extracted_actual_26901_candidate_tar";rm -rf "$exp01";mkdir -p "$exp01"
 tar -xzf "$OUT/26901_candidate_app_source.tar.gz" -C "$exp01"
 diff -qr "$CAND/app" "$exp01/app" >/dev/null || fail '26901 compiled candidate TAR changed'
 (cd "$exp01" && sha256sum -c "$ROOT/26901_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 pass '26901 exact 17-stage successful 26900 inherited; six scoped runtime changes; 2020 protected; real two ESSL310 compilers and final clean extract'
''')
# All 17 original stage CALLS and order MUST remain as successful Actions.
assert tuple(x for x in re.findall(r'(?m)^([a-z_]+)\(\)\{',s) if x in STAGES)==STAGES
for cmd in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace']:
 assert s.count(cmd)>=1,cmd
assert '$ARTDIR/build_26899_iris_rawr_outputs/' not in s
assert s.count('verify_26901.py patch "$BASE" "$CAND" 26901_FORWARD_FULL_INDEX.patch 26901_ROLLBACK_FULL_INDEX.patch')>=2
# Historical successful 26900 shader still compiled using its OWN successful source.
assert 'historical_26900_make_candidate(){' in s
assert '26900_HISTORICAL_GLSL_REAL_COMPILER_RECEIPT.txt' in s
assert '26901_CURRENT_GLSL_REAL_COMPILER_RECEIPT.txt' in s
assert '26901_candidate_app_source.tar.gz' in s
once("pass '26900 ALL 17 INHERITED GUARDED STAGES PASSED'","pass '26901 ALL 17 INHERITED GUARDED STAGES PASSED'")
p=R/'build_26901_iris_rawr.sh';p.write_text(s)
print(H(p)+'  build_26901_iris_rawr.sh')
