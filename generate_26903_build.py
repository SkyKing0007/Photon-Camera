#!/usr/bin/env python3
"""Exact 26902 successful 17-stage successor. Photon 26903 only Night B isolated owner.
The original runner, historical validators/compilers/stage order are preserved exactly;
new current-source and shader/DNG/50MP Night B gates append within their original stages.
"""
import hashlib,re,sys
from pathlib import Path
R=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
p=R/'build_26902_iris_rawr.sh'
H=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
SHA02='348b2d617ed36b40744d15eeba762bb64c589e45327f60f18454d54cbc4c64dc'
assert p.is_file() and H(p)==SHA02,'BLOCK: actual successful Actions 26902 executed runner SHA mismatch'
s=p.read_text()
STAGES=('verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay')
assert tuple(x for x in re.findall(r'(?m)^([a-z_]+)\(\)\{',s) if x in STAGES)==STAGES

def once(a,b):
 global s
 assert s.count(a)==1,('26903 anchor cardinality',s.count(a),a[:100])
 s=s.replace(a,b,1)
def section(name):
 a=s.index('\n'+name+'(){')+1;b=s.index('\n}',a)+2;return s[a:b]
def rewrite(name,new):
 global s
 old=section(name);assert new.startswith(name+'(){') and new.endswith('}') and old!=new,name
 s=s.replace(old,new,1)
def append(name,code):
 old=section(name);rewrite(name,old[:-2]+'\n'+code.strip('\n')+'\n}')
# The latest verified successful 26902 job/artifact/compiled source/runner; no fixed 26900/01 parent references.
replacements=[
('REPO_SCAFFOLD_BASE_COMMIT="ee59eeb6f4fec16af10969ed7fbf90269b11a16a"','REPO_SCAFFOLD_BASE_COMMIT="27ee39533f9160f0221acae11cd52984561476e9"'),
('RUNTIME_ARTIFACT_ID="13297535320"; RUNTIME_ACTIONS_RUN="41774585178"','RUNTIME_ARTIFACT_ID="13328138747"; RUNTIME_ACTIONS_RUN="41838095787"'),
('RUNTIME_AUTHORITY_COMMIT="ee59eeb6f4fec16af10969ed7fbf90269b11a16a"','RUNTIME_AUTHORITY_COMMIT="27ee39533f9160f0221acae11cd52984561476e9"'),
('RUNTIME_ARTIFACT_SHA="6de45e5fa5c26e581c9d010175ed8691941ce14122b64ef13fee2020e70c68a5"','RUNTIME_ARTIFACT_SHA="9557d9c70fa28b0a8257f5f111da0751a0de990aec0211906a3bb8c7e17d9717"'),
('RUNTIME_TAR_SHA="759109721bfc05c70c85d215542333a667107f0e652531ec9966768e8658a615"','RUNTIME_TAR_SHA="f51edc65a064f8ab81e796af032090013fa34ab6bcefc965892f812a9df42961"'),
('VERSION_NAME="0.9726902"; VERSION_BUILD="26902"','VERSION_NAME="0.9726903"; VERSION_BUILD="26903"'),
('OUT="$ROOT/build_26902_iris_rawr_outputs"; WORK="$ROOT/.build_26902_iris_rawr_work"','OUT="$ROOT/build_26903_iris_rawr_outputs"; WORK="$ROOT/.build_26903_iris_rawr_work"'),
('ARTZIP="$WORK/26901_artifact.zip"; ARTDIR="$WORK/artifact_26901"','ARTZIP="$WORK/26902_artifact.zip"; ARTDIR="$WORK/artifact_26902"'),
('BASE="$WORK/exact_successful_26901_compiled_candidate"; CAND="$WORK/candidate_26902"','BASE="$WORK/exact_successful_26902_compiled_candidate"; CAND="$WORK/candidate_26903"'),
('# IRIS_26902_AUTHORITATIVE_ACTIONS_STAGE_ORDER','# IRIS_26903_AUTHORITATIVE_ACTIONS_STAGE_ORDER'),
('# Successful 26901 compiled candidate is runtime authority.','# Successful 26902 compiled candidate is runtime authority.'),
]
for a,b in replacements:once(a,b)
s=s.replace('$OUT/26902_','$OUT/26903_')
s=s.replace('$ARTDIR/build_26901_iris_rawr_outputs/','$ARTDIR/build_26902_iris_rawr_outputs/')
# Parent 26902 real-history candidate must run using its own real successful 26901 source,
# which is explicitly archived in successful 26902 Actions artifact (not current 26903).
old=section('make_candidate');hist=old.replace('make_candidate(){','historical_26902_make_candidate(){',1)
new='''make_candidate(){
 local H01="$WORK/historical_26901_from_26902" H02="$WORK/historical_26902_replayed"
 mkdir -p "$H01"
 local T01="$ARTDIR/build_26902_iris_rawr_outputs/26901_historical_candidate_app_source.tar.gz"
 [[ -s "$T01" ]] || fail '26902 successful artifact lacks 26901 original historical candidate archive'
 (cd "$ARTDIR/build_26902_iris_rawr_outputs" && sha256sum -c 26901_historical_candidate_app_source.tar.gz.sha256 >/dev/null) || fail 'historical 26901 archive corrupted'
 tar -xzf "$T01" -C "$H01"
 (cd "$H01" && sha256sum -c "$ROOT/26902_BASE_FULL_APP.sha256" >/dev/null) || fail '26902 historical base is NOT original successful 26901 source bytes'
 (local BASE="$H01" CAND="$H02"; historical_26902_make_candidate)
 (cd "$H02" && sha256sum -c "$ROOT/26903_BASE_FULL_APP.sha256" >/dev/null) || fail '26902 historical replay not identical successful compiled 26902 source'
 python3 -S verify_26902.py candidate "$H01" "$H02"
 python3 -S verify_26902.py semantics "$H01" "$H02"
 python3 -S verify_26902.py patch "$H01" "$H02" 26902_FORWARD_FULL_INDEX.patch 26902_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26902.py tamper "$H01" "$H02"
 python3 -S test_26902_modes.py "$H02"
 python3 -S verify_26903.py candidate "$BASE" "$CAND" --transform
 python3 -S verify_26903.py semantics "$BASE" "$CAND"
 python3 -S test_26903_modes.py "$CAND"
}'''
assert old in s;s=s.replace(old,hist+'\n'+new,1)
H01='"$WORK/historical_26901_from_26902"';H02='"$WORK/historical_26902_replayed"'
# Old 26902 historical validators must always consume *their own* source, not new candidate.
for name in STAGES:
 if name in ('verify_scope','obtain_authority','make_candidate'):continue
 old=section(name);nn=old
 for mode in ('candidate','semantics','patch','tamper'):
  nn=nn.replace('verify_26902.py '+mode+' "$BASE" "$CAND"','verify_26902.py '+mode+' '+H01+' '+H02)
 nn=nn.replace('test_26902_modes.py "$CAND"','test_26902_modes.py '+H02)
 for man in ('26902_UNCHANGED_PROTECTED.sha256','26902_EXPECTED_CANDIDATE_FULL_APP.sha256'):
  nn=nn.replace('(cd "$CAND" && sha256sum -c "$ROOT/'+man+'"','(cd '+H02+' && sha256sum -c "$ROOT/'+man+'"')
 if name=='compile_modified_runtime_shaders':
  nn=nn.replace('local S02="$CAND/app/src/main/assets/shaders/motionv2/iris26899_b_off_zoom_luma_sharpen.glsl"',
     'local S02="$WORK/historical_26902_replayed/app/src/main/assets/shaders/motionv2/iris26899_b_off_zoom_luma_sharpen.glsl"')
 if name=='prebuild_safety':
  nn=nn.replace('"$CAND/app/version.properties"','"$WORK/historical_26902_replayed/app/version.properties"')
  # Historical 26902 compiler and patch proof must not be conflated with the new 26903 ones.
  nn=nn.replace('26903_CURRENT_GLSL_REAL_COMPILER_RECEIPT.txt','26902_HISTORICAL_GLSL_REAL_COMPILER_RECEIPT.txt')
  nn=nn.replace('26903_CURRENT_PATCH_PROOF.txt','26902_HISTORICAL_PATCH_PROOF.txt')
 if name=='compile_modified_runtime_shaders':
  nn=nn.replace('26903_CURRENT_GLSL_REAL_COMPILER_RECEIPT.txt','26902_HISTORICAL_GLSL_REAL_COMPILER_RECEIPT.txt')
 if name=='verify_candidate_patches':
  nn=nn.replace('26903_CURRENT_PATCH_PROOF.txt','26902_HISTORICAL_PATCH_PROOF.txt')
 if name=='postbuild_proof':
  nn=nn.replace('cp 26902_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26903_candidate_full_app.sha256"',
      'cp 26902_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26902_historical_candidate_full_app.sha256"')
  nn=nn.replace('"$OUT/26903_candidate_app_source.tar.gz"','"$OUT/26902_historical_candidate_app_source.tar.gz"')
  nn=nn.replace('(cd "$CAND" && tar --sort=name','(cd '+H02+' && tar --sort=name')
  nn=nn.replace('> "$OUT/26903_candidate_app_source.tar.gz.sha256"', '> "$OUT/26902_historical_candidate_app_source.tar.gz.sha256"')
 if name=='clean_extract_replay':
  nn=nn.replace('"$OUT/26903_candidate_app_source.tar.gz"','"$OUT/26902_historical_candidate_app_source.tar.gz"')
  nn=nn.replace('diff -qr "$CAND/app" "$exp02/app"','diff -qr '+H02+'/app "$exp02/app"')
  nn=nn.replace('sha256sum -c "$OUT/26903_candidate_app_source.tar.gz.sha256"', 'sha256sum -c "$OUT/26902_historical_candidate_app_source.tar.gz.sha256"')
 if nn!=old:rewrite(name,nn)
# Maintain original successful compiler command list/arguments and all 17 stages.
rewrite('verify_scope','''verify_scope(){
 [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail '26903 wrong Photon Actions branch'
 git merge-base --is-ancestor "$REPO_SCAFFOLD_BASE_COMMIT" HEAD || fail '26903 successful 26902 parent not ancestor'
 [[ "$(sha build_26902_iris_rawr.sh)" == '348b2d617ed36b40744d15eeba762bb64c589e45327f60f18454d54cbc4c64dc' ]] || fail '26902 actual executed runner mismatch'
 diff -u 26903_REPOSITORY_UPLOAD_ALLOWLIST.txt <(git diff --name-only "$REPO_SCAFFOLD_BASE_COMMIT"..HEAD | LC_ALL=C sort) >/dev/null || fail '26903 uploaded repository file scope unexpected: no backup/early workflow/foreign source allowed'
 pass '26903 branch/commit exact successful 26902 runner and three-stage one-trigger scope'
}''')
rewrite('obtain_authority','''obtain_authority(){
 [[ -n "$TOKEN" ]] || fail 'GITHUB_TOKEN missing'
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
   "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/runs/${RUNTIME_ACTIONS_RUN}" -o "$WORK/26902_run.json"
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
   "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}" -o "$WORK/26902_artifact_metadata.json"
 python3 -S - "$WORK/26902_run.json" "$WORK/26902_artifact_metadata.json" <<'PY_AUTH_26903'
import json,sys
run=json.load(open(sys.argv[1]));art=json.load(open(sys.argv[2]))
assert run['id']==41838095787 and run['conclusion']=='success' and run['head_sha']=='27ee39533f9160f0221acae11cd52984561476e9' and run['head_branch']=='experimental-clean-photon-rebuild'
assert art['id']==13328138747 and art.get('expired') is False and art.get('digest')=='sha256:9557d9c70fa28b0a8257f5f111da0751a0de990aec0211906a3bb8c7e17d9717'
assert art.get('workflow_run',{}).get('head_sha')=='27ee39533f9160f0221acae11cd52984561476e9'
print('PASS 26902 latest successful run/job source and artifact metadata digest')
PY_AUTH_26903
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
   "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"
 [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail '26902 SUCCESS artifact ZIP digest wrong'
 unzip -q "$ARTZIP" -d "$ARTDIR"
 local T="$ARTDIR/build_26902_iris_rawr_outputs/26902_candidate_app_source.tar.gz"
 [[ -s "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail '26902 internal actual compiled source TAR SHA mismatch'
 local E="$ARTDIR/build_26902_iris_rawr_outputs/exact_generated_runner/build_26902_iris_rawr.sh"
 [[ -s "$E" && "$(sha "$E")" == '348b2d617ed36b40744d15eeba762bb64c589e45327f60f18454d54cbc4c64dc' ]] || fail '26902 original successfully executed runner mismatch'
 cmp -s "$E" "$ROOT/build_26902_iris_rawr.sh" || fail 'replayed 26902 generator output not EXACT originally executed Actions runner'
 test -s "$ARTDIR/build_26902_iris_rawr_outputs/exact_generated_runner/SUCCESSFUL_ACTIONS_EVIDENCE.json" || fail 'actual successful parent runner receipt missing'
 for k in 'REAL GLSL COMPILE: PASS' 'REAL SPIR-V VALIDATION: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS';do
  grep -F "$k" "$ARTDIR/build_26902_iris_rawr_outputs/26902_COMPILER_STATUS.txt" >/dev/null || fail "26902 actual successful compiler receipt lacks $k"
 done
 mkdir -p "$BASE";tar -xzf "$T" -C "$BASE"
 [[ "$(find "$BASE/app" -type f | wc -l)" -eq 2026 ]] || fail '26902 compiled source file universe not 2026'
 (cd "$BASE" && sha256sum -c "$ROOT/26903_BASE_FULL_APP.sha256" >/dev/null) || fail '26902 actual compiled source hash count/bytes wrong'
 cmp -s "$ARTDIR/build_26902_iris_rawr_outputs/26902_candidate_full_app.sha256" "$ROOT/26903_BASE_FULL_APP.sha256" || fail 'successful 26902 complete published manifest not same frozen base'
 # Explicit historical 26899 V1 wrong-root SPV and stale compiler/TAR path rejection.
 for rel in \\
  26888_modified_shader_spirv/Iris26887BOffHdrqMerge_prod.spv \\
  26901_historical_candidate_app_source.tar.gz \\
  26902_candidate_app_source.tar.gz \\
  26902_candidate_full_app.sha256 \\
  26902_COMPILER_STATUS.txt \\
  exact_generated_runner/build_26902_iris_rawr.sh \\
  exact_generated_runner/SUCCESSFUL_ACTIONS_EVIDENCE.json;do
    [[ -s "$ARTDIR/build_26902_iris_rawr_outputs/$rel" ]] || fail "26903 stale/missing 26902 artifact operand $rel"
 done
 python3 -S verify_26903.py candidate "$BASE" "$WORK/safeguarded_source_probe" --transform
 pass '26903 ACTUAL successful 26902 Action artifact bytes/internal TAR/2026 manifests/executed runner/compiler receipts'
}''')
# Keep original parent historical source validators including all failures 26886-26899.
append('verify_package','''
 python3 -S stage_26903_root.py
 sha256sum -c 26903_HANDOFF_HASHES.sha256 >/dev/null || fail '26903 final exact three-stage staged file hashes drift'
 python3 -S test_26903_three_stage_negatives.py
 test -f TRIGGER_26903.txt
 [[ "$(sha TRIGGER_26903.txt)" == "$(printf 'RUN_26903_B_NIGHT_NORMAL_RAWR_JIN_50MP_DNG_FIRST_V1\\n' | sha256sum | awk '{print $1}')" ]] || fail '26903 exact trigger mutated'
''')
append('compile_modified_runtime_shaders','''
 # Original successfully-compiled 26902 two-scale shader is compiled above against
 # 26902's OWN successful bytes; the new NIGHT B optional 50MP fused final shader
 # is compiled using the original exact GLSL ES 3.10 file (no macro/import expansion).
 local S03="$CAND/app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag"
 local E03="$OUT/26903_exact_runtime_essl310/b_fused_final_p3_gain.frag"
 mkdir -p "$(dirname "$E03")";cp "$S03" "$E03"
 cmp -s "$S03" "$E03" || fail '26903 shader expanded source differs frozen actual runtime'
 python3 -S verify_26903.py shader "$E03"
 "$IRIS26864_GLSLANG" -S frag "$E03" > "$OUT/26903_GLSLANG_B_FUSED_FINAL_50MP.txt" 2>&1 || fail '26903 Night B final shader MUST real compile under PINNED GLSLANG 16.5.0'
 sha256sum "$S03" "$E03" > "$OUT/26903_NIGHT_B_FINAL_SHADER.sha256"
 echo 'PASS 26903 ACTUAL B Night optional Jin 50MP fused final ESSL310 REAL PINNED GLSLANG 16.5.0' | tee "$OUT/26903_CURRENT_GLSL_REAL_COMPILER_RECEIPT.txt"
 python3 -S verify_26903.py semantics "$BASE" "$CAND"
''')
append('verify_candidate_patches','''
 python3 -S verify_26903.py candidate "$BASE" "$CAND"
 python3 -S verify_26903.py semantics "$BASE" "$CAND"
 python3 -S verify_26903.py patch "$BASE" "$CAND" 26903_FORWARD_FULL_INDEX.patch 26903_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26903_CURRENT_PATCH_PROOF.txt"
 python3 -S verify_26903.py tamper "$BASE" "$CAND"
''')
# Original inherited 26902 prebuild proof must remain but refer to original 26902
# source H02 (it does after historic replacements), not 26903. New 26903 proof
# runs after old and before exact successful full assemble.
append('prebuild_safety','''
 test -s "$OUT/26903_CURRENT_GLSL_REAL_COMPILER_RECEIPT.txt" && grep -Fx 'PASS 26903 ACTUAL B Night optional Jin 50MP fused final ESSL310 REAL PINNED GLSLANG 16.5.0' "$OUT/26903_CURRENT_GLSL_REAL_COMPILER_RECEIPT.txt" >/dev/null || fail '26903 actual modified production shader uncompiled'
 python3 -S verify_26903.py candidate "$BASE" "$CAND"
 python3 -S verify_26903.py semantics "$BASE" "$CAND"
 python3 -S test_26903_modes.py "$CAND"
 (cd "$CAND" && sha256sum -c "$ROOT/26903_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '2014 protected source files not identical successful 26902'
 grep -Fx 'VERSION_NAME=0.9726903' "$CAND/app/version.properties" >/dev/null || fail 'guarded version NAME wrong'
 grep -Fx 'VERSION_BUILD=26903' "$CAND/app/version.properties" >/dev/null || fail 'guarded version BUILD wrong'
 test -s "$OUT/26903_CURRENT_PATCH_PROOF.txt" || fail '26903 full-index patch reversal proof missing'
 cat >> "$OUT/26903_PREBUILD_SAFETY.txt" <<'EOF_26903_SAFETY'
PRE-BUILD SAFETY PROOF PASSED
26903_parent_success=26902 Actions 41838095787 job 126602158976 commit 27ee39533f9160f0221acae11cd52984561476e9 artifact 13328138747
26903_parent_artifact_digest=9557d9c70fa28b0a8257f5f111da0751a0de990aec0211906a3bb8c7e17d9717
26903_parent_actual_internal_source_tar=f51edc65a064f8ab81e796af032090013fa34ab6bcefc965892f812a9df42961
26903_parent_actual_executed_runner=348b2d617ed36b40744d15eeba762bb64c589e45327f60f18454d54cbc4c64dc
26903_source=2026 successful actual parent -> 2027 frozen new, exactly 12 changed existing + 1 added NightB processor, 0 deletions, 2014 protected unchanged
26903_scope=EXPERIMENT B selected inside existing NIGHT ONLY; normal A Night/Photo B/50MP/native/vendor/DNG/Spektra source algorithms unchanged
26903_NightB=Night shutter min practical ISO and motion-safe SS, exactly N NORMAL frames, B zoom with original Photo B reconstruction, Jin 1x/real 50MP, DNG first independent, RAW-only bypass B GPU and Jin
26903_compilers=REAL pinned ESSL310 GLSLANG, historical SPIRV, Kotlin+Java, NDK 2 ABI and full assemble performed before APK upload
26903_patch=full index 7/12/40 forward rollback fuzz0 bytes identical
26903_trigger=EXACT immutable root TRIGGER_26903.txt upload LAST, no workflow recursion
EOF_26903_SAFETY
''')
# Original inherited assemble requires 26902 named prebuild receipts; retain those
# as verified historical receipts, additionally check current Night B PREBUILD before call.
a=section('assemble')
rewrite('assemble',a.replace('assemble(){','assemble(){\n test -s "$OUT/26903_PREBUILD_SAFETY.txt" && grep -Fx \'PRE-BUILD SAFETY PROOF PASSED\' "$OUT/26903_PREBUILD_SAFETY.txt" >/dev/null || fail \'26903 build without real Night B prebuild proof\'',1))
append('postbuild_proof','''
 python3 -S verify_26903.py candidate "$BASE" "$CAND"
 python3 -S verify_26903.py semantics "$BASE" "$CAND"
 (cd "$CAND" && sha256sum -c "$ROOT/26903_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null) || fail '26903 actual compiled final source mutated'
 (cd "$CAND" && sha256sum -c "$ROOT/26903_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26903 protected native/DNG/Spektra/other mode hashes changed after APK assembly'
 cp 26903_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26903_candidate_full_app.sha256"
 cp 26903_FORWARD_FULL_INDEX.patch 26903_ROLLBACK_FULL_INDEX.patch 26903_CHANGED_ALLOWLIST.txt 26903_ADDITIONS.txt 26903_DELETIONS.txt 26903_UNCHANGED_PROTECTED.sha256 "$OUT/"
 (cd "$CAND" && tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26903_candidate_app_source.tar.gz" app)
 sha256sum "$OUT/26903_candidate_app_source.tar.gz" > "$OUT/26903_candidate_app_source.tar.gz.sha256"
''')
append('clean_extract_replay','''
 python3 -S verify_26903.py candidate "$BASE" "$CAND"
 python3 -S verify_26903.py semantics "$BASE" "$CAND"
 python3 -S verify_26903.py patch "$BASE" "$CAND" 26903_FORWARD_FULL_INDEX.patch 26903_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26903.py tamper "$BASE" "$CAND"
 python3 -S test_26903_modes.py "$CAND"
 python3 -S test_26903_three_stage_negatives.py
 (cd "$CAND" && sha256sum -c "$ROOT/26903_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 (cd "$CAND" && sha256sum -c "$ROOT/26903_UNCHANGED_PROTECTED.sha256" >/dev/null)
 sha256sum -c "$OUT/26903_candidate_app_source.tar.gz.sha256" >/dev/null
 local exp03="$WORK/extracted_actual_26903_candidate_tar";rm -rf "$exp03";mkdir -p "$exp03"
 tar -xzf "$OUT/26903_candidate_app_source.tar.gz" -C "$exp03"
 diff -qr "$CAND/app" "$exp03/app" >/dev/null || fail '26903 actual assembled source TAR differs compiler source'
 (cd "$exp03" && sha256sum -c "$ROOT/26903_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 (cd "$exp03" && sha256sum -c "$ROOT/26903_UNCHANGED_PROTECTED.sha256" >/dev/null)
 pass '26903 exact inherited successful 26902 17-stage compilers and full assemble, 12 changes + 1 new, 2014 protected; real B Night source and actual final clean-extract proof'
''')
# Historical 26902 PREBUILD original references '$CAND/app/version...' rewritten H02; verify.
assert tuple(x for x in re.findall(r'(?m)^([a-z_]+)\(\)\{',s) if x in STAGES)==STAGES
for command in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
  "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
  './gradlew :app:assembleDebug --stacktrace']:
 assert command in s,('inherited compiler lost',command)
assert '$ARTDIR/build_26901_iris_rawr_outputs/' not in s,'stale artifact root V1 regression'
assert '$ARTDIR/build_26900_iris_rawr_outputs/' not in s,'stale artifact root V1 regression'
assert 'historical_26902_make_candidate(){' in s and '26903_candidate_app_source.tar.gz' in s
once("pass '26902 ALL 17 INHERITED GUARDED STAGES PASSED'","pass '26903 ALL 17 INHERITED GUARDED STAGES PASSED'")
# At end of original successful 17 stages the runner's exact bytes are sealed by workflow
# **after** compiler+single APK proof and **before** upload into existing output folder.
out=R/'build_26903_iris_rawr.sh';out.write_text(s)
print(H(out)+'  build_26903_iris_rawr.sh')
