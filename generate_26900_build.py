#!/usr/bin/env python3
'''SHA-pin and inherit ACTUAL successful 26899 V2 17-stage Actions runner.

Never rebuild from a similar generator or rewrite historical validators.
Historic 26899 operates on actual successful 26898/26899 archived sources.
Current 26900 operates only on the extracted successful 26899 candidate.
'''
from pathlib import Path
import hashlib,sys,re
R=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
parent=R/'build_26899_iris_rawr.sh'
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert parent.is_file() and H(parent)=='a253dd089fdbdb9fc0829d165a42a1645b35405427f8ae369cfa1e08233331d7','EXACT successful executed 26899 V2 runner required'
s=parent.read_text()
STAGES=('verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics',
'prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader',
'install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff',
'compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay')
rx=re.compile(r'(?m)^([a-z_]+)\(\)\{')
assert tuple(x for x in rx.findall(s) if x in STAGES)==STAGES

def once(a,b):
 global s
 assert s.count(a)==1,('anchor',a[:120],s.count(a))
 s=s.replace(a,b,1)
def section(name):
 a=s.index('\n'+name+'(){')+1
 b=s.index('\n}',a)+2
 return s[a:b]
def rewrite(name,new):
 global s
 old=section(name)
 assert new.startswith(name+'(){') and new.endswith('}') and old!=new,name
 s=s.replace(old,new,1)
def append(name,code):
 old=section(name)
 rewrite(name,old[:-2]+'\n'+code.strip('\n')+'\n}')

for a,b in [
 ('REPO_SCAFFOLD_BASE_COMMIT="94d8900987749c9ad0f7a18a64eeb0c7083e6d04"','REPO_SCAFFOLD_BASE_COMMIT="5a3e3eee6086398021f57f4b4f9de24ba125af24"'),
 ('RUNTIME_ARTIFACT_ID="13241316001"; RUNTIME_ACTIONS_RUN="41656090620"','RUNTIME_ARTIFACT_ID="13264802004"; RUNTIME_ACTIONS_RUN="41700527054"'),
 ('RUNTIME_AUTHORITY_COMMIT="94d8900987749c9ad0f7a18a64eeb0c7083e6d04"','RUNTIME_AUTHORITY_COMMIT="5a3e3eee6086398021f57f4b4f9de24ba125af24"'),
 ('RUNTIME_ARTIFACT_SHA="3fa6f669ecebd7e5c460ea1228d086b7422a93c95c8bbd950f5b4fe24bf53b97"','RUNTIME_ARTIFACT_SHA="de648a61f7c4639c84c384d2ff6cbec1d057d9377cb1b47a52e0d5bc34036ff9"'),
 ('RUNTIME_TAR_SHA="7ac15724f3cc30753f41f08038443e24b4931c8861fe10217cc4c3b059755a61"','RUNTIME_TAR_SHA="b468173a2eae7100f3180b8a178e37961dc1c0465560fad90113e8181507c80f"'),
 ('VERSION_NAME="0.9726899"; VERSION_BUILD="26899"','VERSION_NAME="0.9726900"; VERSION_BUILD="26900"'),
 ('OUT="$ROOT/build_26899_iris_rawr_outputs"; WORK="$ROOT/.build_26899_iris_rawr_work"','OUT="$ROOT/build_26900_iris_rawr_outputs"; WORK="$ROOT/.build_26900_iris_rawr_work"'),
 ('ARTZIP="$WORK/26898_artifact.zip"; ARTDIR="$WORK/artifact_26898"','ARTZIP="$WORK/26899_artifact.zip"; ARTDIR="$WORK/artifact_26899"'),
 ('BASE="$WORK/exact_successful_26898_compiled_candidate"; CAND="$WORK/candidate_26899"','BASE="$WORK/exact_successful_26899_compiled_candidate"; CAND="$WORK/candidate_26900"'),
 ('# IRIS_26899_AUTHORITATIVE_ACTIONS_STAGE_ORDER','# IRIS_26900_AUTHORITATIVE_ACTIONS_STAGE_ORDER'),
 ('# Successful 26889 Actions compiled candidate is runtime authority.','# Successful 26899 V2 compiled candidate is runtime authority.'),
]: once(a,b)
# Upgrade the output destination prefix only; historical source/patch receipt names
# remain unchanged and continue to be verified on their OWN historic bytes.
s=s.replace('$OUT/26899_','$OUT/26900_')
# Every $ARTDIR path must point into the ACTUAL parent archive root.
# In particular this fixes the exact stale-artifact SPIR-V bug that killed 26899 V1.
s=s.replace('$ARTDIR/build_26898_iris_rawr_outputs/','$ARTDIR/build_26899_iris_rawr_outputs/')
# Existing 26899 candidate/replay acts as historical regression.
old=section('make_candidate')
historical=old.replace('make_candidate(){','historical_26899_make_candidate(){',1)
new='''make_candidate(){
 local H98="$WORK/historical_26898_from_26899" H99="$WORK/historical_26899_replayed"
 mkdir -p "$H98"
 local T98="$ARTDIR/build_26899_iris_rawr_outputs/26898_historical_candidate_app_source.tar.gz"
 [[ -f "$T98" && "$(sha "$T98")" == '7ac15724f3cc30753f41f08038443e24b4931c8861fe10217cc4c3b059755a61' ]] || fail 'actual 26899 historical successful 26898 TAR mismatch'
 tar -xzf "$T98" -C "$H98"
 (cd "$H98" && sha256sum -c "$ROOT/26899_BASE_FULL_APP.sha256" >/dev/null) || fail '26899 historical 26898 source manifest wrong'
 (local BASE="$H98" CAND="$H99"; historical_26899_make_candidate)
 diff -qr "$H99/app" "$BASE/app" >/dev/null || fail 'historic derived 26899 candidate is not exact successful compiled runtime'
 python3 -S verify_26899.py candidate "$H98" "$H99"
 python3 -S verify_26899.py semantics "$H98" "$H99"
 python3 -S verify_26899.py patch "$H98" "$H99" 26899_FORWARD_FULL_INDEX.patch 26899_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26899.py tamper "$H98" "$H99"
 python3 -S test_26899_modes.py "$H99"
 python3 -S verify_26900.py candidate "$BASE" "$CAND" --transform
 python3 -S verify_26900.py semantics "$BASE" "$CAND"
 python3 -S test_26900_modes.py "$CAND"
}'''
assert old in s
s=s.replace(old,historical+'\n'+new,1)
H98='"$WORK/historical_26898_from_26899"';H99='"$WORK/historical_26899_replayed"'
for name in STAGES:
 if name in ('verify_scope','obtain_authority','make_candidate'):continue
 old=section(name);nn=old
 for kind in ('candidate','semantics','patch','tamper'):
  nn=nn.replace('verify_26899.py '+kind+' "$BASE" "$CAND"',
                'verify_26899.py '+kind+' '+H98+' '+H99)
 nn=nn.replace('test_26899_modes.py "$CAND"','test_26899_modes.py '+H99)
 for man in ('26899_UNCHANGED_PROTECTED.sha256','26899_EXPECTED_CANDIDATE_FULL_APP.sha256'):
  nn=nn.replace('(cd "$CAND" && sha256sum -c "$ROOT/'+man+'"',
                '(cd '+H99+' && sha256sum -c "$ROOT/'+man+'"')
 if name=='compile_modified_runtime_shaders':
  nn=nn.replace('S99="$CAND/app/src/main/assets/shaders/motionv2/iris26899_b_off_zoom_luma_sharpen.glsl"',
                'S99="$WORK/historical_26899_replayed/app/src/main/assets/shaders/motionv2/iris26899_b_off_zoom_luma_sharpen.glsl"')
 if name=='prebuild_safety':
  nn=nn.replace('"$CAND/app/version.properties"','"$WORK/historical_26899_replayed/app/version.properties"')
 if name=='postbuild_proof':
  nn=nn.replace('cp 26899_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26900_candidate_full_app.sha256"',
                'cp 26899_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26899_historical_candidate_full_app.sha256"')
  nn=nn.replace('"$OUT/26900_candidate_app_source.tar.gz','"$OUT/26899_historical_candidate_app_source.tar.gz')
  nn=nn.replace('(cd "$CAND" && tar --sort=name', '(cd '+H99+' && tar --sort=name')
 if name=='clean_extract_replay':
  nn=nn.replace('"$OUT/26900_candidate_app_source.tar.gz','"$OUT/26899_historical_candidate_app_source.tar.gz')
  nn=nn.replace('diff -qr "$CAND/app" "$exp99/app"','diff -qr '+H99+'/app "$exp99/app"')
 if name in ('verify_candidate_patches','prebuild_safety'):
  nn=nn.replace('"$OUT/26900_CURRENT_PATCH_PROOF.txt"','"$OUT/26899_HISTORICAL_PATCH_PROOF.txt"')
 if nn!=old:rewrite(name,nn)
# Historical parent safety text must not falsely claim the new candidate is 26897.
# Change only the current safety report header; original historical proofs stay.
safety=section('prebuild_safety')
newsafety=safety
for old_label,new_label in [
 ('runtime_authority=successful 26897 $RUNTIME_AUTHORITY_COMMIT run $RUNTIME_ACTIONS_RUN artifact $RUNTIME_ARTIFACT_ID',
  'runtime_authority=successful 26899 V2 $RUNTIME_AUTHORITY_COMMIT run $RUNTIME_ACTIONS_RUN artifact $RUNTIME_ARTIFACT_ID'),
 ('verification_mechanics=EXACT successful 26897 executed 17 stages, real compiler/NDK/assemble commands',
  'verification_mechanics=EXACT successful 26899 V2 executed 17 stages, real compiler/NDK/assemble commands'),
 ('runtime_changed_files=5 modified existing, 2020 protected; independent A DNG EGL context, early DNG-only stop, actual AHB GL receipts',
  'runtime_changed_files=4 modified existing, 2022 protected; B OFF bicubic luminance + scale-adaptive aggressive 26899 sharpening'),
 ('prior_files=2025\ncandidate_files=2025','prior_files=2026\ncandidate_files=2026'),
 ('protected_source=2020 files byte-identical to successful 26897 compiled candidate; original DNG writer/Sabre math/A/Night/LONG/UHDR/vendor/GLSL protected',
  'protected_source=2022 files byte-identical to successful 26899 V2 compiled candidate; DNG/native/vendor/A/Night/LONG/UHDR protected'),
 ('infrastructure_delta=one strict successor workflow/trigger + source validators; exact 26894 inherited 17-stage compiler+freeze+assemble mechanics',
  'infrastructure_delta=one strict successor workflow/trigger + source validators; exact successful 26899 V2 inherited 17-stage compiler+freeze+assemble mechanics')
]:
 assert old_label in newsafety,old_label
 newsafety=newsafety.replace(old_label,new_label,1)
rewrite('prebuild_safety',newsafety)
rewrite('verify_scope','''verify_scope(){
 [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail 'wrong Photon Actions branch'
 git merge-base --is-ancestor "$REPO_SCAFFOLD_BASE_COMMIT" HEAD || fail '26899 successful commit not ancestor'
 [[ -z "$(git diff --name-only "$REPO_SCAFFOLD_BASE_COMMIT"..HEAD -- app/src app/version.properties)" ]] || fail 'unexpected live source modifications'
 [[ -z "$(git status --porcelain -- app/src app/version.properties)" ]] || fail 'uncommitted live runtime source modifications'
 diff -u 26900_REPOSITORY_UPLOAD_ALLOWLIST.txt <(git diff --name-only "$REPO_SCAFFOLD_BASE_COMMIT"..HEAD | LC_ALL=C sort) >/dev/null || fail '26900 upload scope differs from frozen handoff'
 [[ "$(sha build_26899_iris_rawr.sh)" == 'a253dd089fdbdb9fc0829d165a42a1645b35405427f8ae369cfa1e08233331d7' ]] || fail '26899 actual successful executed runner drift'
 pass '26900 exact successful 26899 parent and repository source/infrastructure delta'
}''')
rewrite('obtain_authority','''obtain_authority(){
 [[ -n "$TOKEN" ]] || fail 'GITHUB_TOKEN missing'
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
   "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/runs/${RUNTIME_ACTIONS_RUN}" -o "$WORK/26899_run.json"
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
   "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}" -o "$WORK/26899_artifact_metadata.json"
 python3 -S - "$WORK/26899_run.json" "$WORK/26899_artifact_metadata.json" <<'PY_AUTH_26900'
import json,sys
run=json.load(open(sys.argv[1]));art=json.load(open(sys.argv[2]))
assert run['id']==41700527054 and run['conclusion']=='success' and run['head_sha']=='5a3e3eee6086398021f57f4b4f9de24ba125af24' and run['head_branch']=='experimental-clean-photon-rebuild'
assert art['id']==13264802004 and art.get('expired') is False and art.get('digest')=='sha256:de648a61f7c4639c84c384d2ff6cbec1d057d9377cb1b47a52e0d5bc34036ff9'
print('PASS exact successful 26899 V2 Actions run/artifact digest')
PY_AUTH_26900
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
   "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"
 [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail 'actual successful 26899 ZIP SHA mismatch'
 unzip -q "$ARTZIP" -d "$ARTDIR"
 local T="$ARTDIR/build_26899_iris_rawr_outputs/26899_candidate_app_source.tar.gz"
 [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail '26899 successful compiled TAR mismatch'
 local EXEC="$ARTDIR/build_26899_iris_rawr_outputs/exact_generated_runner/build_26899_iris_rawr.sh"
 [[ -f "$EXEC" && "$(sha "$EXEC")" == 'a253dd089fdbdb9fc0829d165a42a1645b35405427f8ae369cfa1e08233331d7' ]] || fail '26899 actual executed runner mismatch'
 cmp -s "$EXEC" "$ROOT/build_26899_iris_rawr.sh" || fail 'new generated historic 26899 runner not actual Actions executed bytes'
 test -f "$ARTDIR/build_26899_iris_rawr_outputs/exact_generated_runner/SUCCESSFUL_ACTIONS_EVIDENCE.json" || fail '26899 executed runner receipt missing'
 for k in 'REAL GLSL COMPILE: PASS' 'REAL SPIR-V VALIDATION: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS';do
   grep -F "$k" "$ARTDIR/build_26899_iris_rawr_outputs/26899_COMPILER_STATUS.txt" >/dev/null || fail "26899 successful real compiler proof missing $k"
 done
 mkdir -p "$BASE";tar -xzf "$T" -C "$BASE"
 [[ "$(find "$BASE/app" -type f | wc -l)" -eq 2026 ]] || fail '26899 source universe count'
 (cd "$BASE" && sha256sum -c "$ROOT/26900_BASE_FULL_APP.sha256" >/dev/null) || fail '26899 compiled source full manifest mismatch'
 cmp -s "$ARTDIR/build_26899_iris_rawr_outputs/26899_candidate_full_app.sha256" "$ROOT/26900_BASE_FULL_APP.sha256" || fail '26900 base manifest differs from actual successful source'
 # Exact artifact-root audit, INCLUDING original 26899 V1 stale path failure.
 python3 -S verify_26900.py artifact "$ARTDIR" "$ROOT/build_26900_iris_rawr.sh"
 pass '26899 V2 real successful candidate, executed runner, compilers, artifact references validated'
}''')
append('verify_package','''
 python3 -S stage_26900_root.py
 sha256sum -c 26900_HANDOFF_HASHES.sha256 >/dev/null || fail '26900 final sealed handoff bytes differ'
 python3 -S test_26900_three_stage_negatives.py
 test -f TRIGGER_26900.txt && grep -Fx 'RUN_26900_B_OFF_BICUBIC_SCALE_AWARE_LUMA_SHARPEN_V1' TRIGGER_26900.txt >/dev/null || fail '26900 immutable trigger mismatch'
''')
append('compile_modified_runtime_shaders','''
 mkdir -p "$OUT/26900_exact_real_essl310"
 # The two modified shader sources are really compiled BEFORE Kotlin/Gradle,
 # with the actual runtime #version 310 es and #line 1 injection.
 for name in render iris26899_b_off_zoom_luma_sharpen;do
   local S="$CAND/app/src/main/assets/shaders/motionv2/$name.glsl"
   local E="$OUT/26900_exact_real_essl310/$name.frag"
   { printf '#version 310 es\\n\\n#line 1\\n';cat "$S"; } > "$E"
   python3 -S verify_26900.py shader "$E"
   "$IRIS26864_GLSLANG" -S frag "$E" > "$OUT/26900_GLSLANG_${name}.txt" 2>&1 || fail "26900 real PINNED GLSLANG 16.5.0 ESSL310 compile failed: $name"
   sha256sum "$E" "$S" >> "$OUT/26900_NEW_SHADER_SHA256.txt"
 done
 echo 'PASS 26900 TWO EXACT runtime-expanded ESSL310 shaders REAL PINNED GLSLANG 16.5.0' | tee "$OUT/26900_CURRENT_GLSL_REAL_COMPILER_RECEIPT.txt"
 python3 -S verify_26900.py semantics "$BASE" "$CAND"
''')
append('verify_candidate_patches','''
 python3 -S verify_26900.py candidate "$BASE" "$CAND"
 python3 -S verify_26900.py semantics "$BASE" "$CAND"
 python3 -S verify_26900.py patch "$BASE" "$CAND" 26900_FORWARD_FULL_INDEX.patch 26900_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26900_CURRENT_PATCH_PROOF.txt"
 python3 -S verify_26900.py tamper "$BASE" "$CAND"
''')
append('prebuild_safety','''
 test -s "$OUT/26900_CURRENT_GLSL_REAL_COMPILER_RECEIPT.txt" && grep -Fx 'PASS 26900 TWO EXACT runtime-expanded ESSL310 shaders REAL PINNED GLSLANG 16.5.0' "$OUT/26900_CURRENT_GLSL_REAL_COMPILER_RECEIPT.txt" >/dev/null || fail '26900 real changed ESSL compiler proof missing'
 python3 -S verify_26900.py candidate "$BASE" "$CAND"
 python3 -S verify_26900.py semantics "$BASE" "$CAND"
 (cd "$CAND" && sha256sum -c "$ROOT/26900_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26900 protected files changed'
 grep -Fx 'VERSION_NAME=0.9726900' "$CAND/app/version.properties" >/dev/null
 grep -Fx 'VERSION_BUILD=26900' "$CAND/app/version.properties" >/dev/null
 test -s "$OUT/26900_CURRENT_PATCH_PROOF.txt" || fail '26900 actual current patches not executed'
 cat >> "$OUT/26900_PREBUILD_SAFETY.txt" <<'EOF_26900_SAFETY'
26900_parent=26899 V2 successful run 41700527054 job 126142291738 commit 5a3e3eee6086398021f57f4b4f9de24ba125af24 artifact 13264802004
26900_parent_artifact_digest=de648a61f7c4639c84c384d2ff6cbec1d057d9377cb1b47a52e0d5bc34036ff9
26900_parent_compiled_source_tar_sha256=b468173a2eae7100f3180b8a178e37961dc1c0465560fad90113e8181507c80f
26900_parent_executed_runner_sha256=a253dd089fdbdb9fc0829d165a42a1645b35405427f8ae369cfa1e08233331d7
26900_scope=only shutter-selected B Super Res OFF global >=1.10, 2 existing shaders + MotionV2Render + version
26900_curve=26899 original global +100...+200 unchanged, larger luma radius uses actual rendering pixel scale
26900_bicubic=Catmull-Rom luma on final RGB enlargement with original bilinear chroma; no new RAW/CFA/motion processing
26900_noises=no new noise reduction; old 26899 low-contrast suppression removed; clipping/halo guards retained
26900_protected=2022 identical other runtime sources, no adds/deletions, native/DNG/vendor/A/AB/SuperResON/Night/LONG/Spektra/UHDR algorithm unchanged
26900_compilers=real two changed ESSL310 pinned glslang and prior 17-stage real Kotlin/Java/NDK/Gradle assembly required
EOF_26900_SAFETY
''')
append('postbuild_proof','''
 python3 -S verify_26900.py candidate "$BASE" "$CAND"
 python3 -S verify_26900.py semantics "$BASE" "$CAND"
 (cd "$CAND" && sha256sum -c "$ROOT/26900_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null) || fail '26900 final source drift after compile'
 (cd "$CAND" && sha256sum -c "$ROOT/26900_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26900 postbuild protected drift'
 cp 26900_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26900_candidate_full_app.sha256"
 cp 26900_FORWARD_FULL_INDEX.patch 26900_ROLLBACK_FULL_INDEX.patch 26900_CHANGED_ALLOWLIST.txt 26900_ADDITIONS.txt 26900_DELETIONS.txt 26900_UNCHANGED_PROTECTED.sha256 "$OUT/"
 (cd "$CAND" && tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26900_candidate_app_source.tar.gz" app)
 sha256sum "$OUT/26900_candidate_app_source.tar.gz" > "$OUT/26900_candidate_app_source.tar.gz.sha256"
''')
append('clean_extract_replay','''
 python3 -S verify_26900.py candidate "$BASE" "$CAND"
 python3 -S verify_26900.py semantics "$BASE" "$CAND"
 python3 -S verify_26900.py patch "$BASE" "$CAND" 26900_FORWARD_FULL_INDEX.patch 26900_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26900.py tamper "$BASE" "$CAND"
 python3 -S test_26900_three_stage_negatives.py
 python3 -S test_26900_modes.py "$CAND"
 (cd "$CAND" && sha256sum -c "$ROOT/26900_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 (cd "$CAND" && sha256sum -c "$ROOT/26900_UNCHANGED_PROTECTED.sha256" >/dev/null)
 sha256sum -c "$OUT/26900_candidate_app_source.tar.gz.sha256" >/dev/null
 local exp00="$WORK/extracted_actual_26900_candidate_tar";rm -rf "$exp00";mkdir -p "$exp00"
 tar -xzf "$OUT/26900_candidate_app_source.tar.gz" -C "$exp00"
 diff -qr "$CAND/app" "$exp00/app" >/dev/null || fail '26900 candidate TAR not byte-identical'
 (cd "$exp00" && sha256sum -c "$ROOT/26900_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 pass '26900 original 17 stages + two exact pinned ESSL310 shaders + 2022 protected and clean extract'
''')
# Eliminate a historical inherited banner incorrectly labeling a 26900 success as 26871.
once("pass '26871 ALL 17 INHERITED GUARDED STAGES PASSED'",
     "pass '26900 ALL 17 INHERITED GUARDED STAGES PASSED'")
# Parent runner compiler and assemble commands must remain byte-for-byte (except output paths).
assert tuple(n for n in rx.findall(s) if n in STAGES)==STAGES
for n,cli in [('compile_languages','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace'),
 ('compile_native',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace"),
 ('assemble','./gradlew :app:assembleDebug --stacktrace')]:
 assert section(n).count(cli)==1,(n,cli)
# Every archived path is checked against the parent archive later by the same
# executed artifact-aware verifier; ban obsolete V1 artifact directory operands.
assert '$ARTDIR/build_26898_iris_rawr_outputs/' not in s
assert '$ARTDIR/build_26897_iris_rawr_outputs/' not in s
assert 'verify_26889_compiled_push_abi.py "$ARTDIR/build_26899_iris_rawr_outputs/26888_modified_shader_spirv/' in s
assert 'verify_26899.py patch '+H98+' '+H99 in s
assert 'verify_26900.py patch "$BASE" "$CAND" 26900_FORWARD_FULL_INDEX.patch 26900_ROLLBACK_FULL_INDEX.patch' in s
out=R/'build_26900_iris_rawr.sh';out.write_text(s);out.chmod(0o755)
print('PASS exact successful 26899 V2 -> 26900 SHA',H(out),'lines',len(s.splitlines()),'17 stages/real compiler commands unchanged')
