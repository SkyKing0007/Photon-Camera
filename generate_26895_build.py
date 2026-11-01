#!/usr/bin/env python3
"""Deterministic 26895 successor from EXACT successful 26894 executed runner.
The entire historical 17-stage runner is inherited, replayed on its own
successful 26893/26894 historical compiled source, then current 26895 checks
run on latest compiled 26894 authority. No substitutions of compiler stages.
"""
from pathlib import Path
import hashlib,re,sys
R=(Path(sys.argv[1]) if len(sys.argv)>1 else Path('.')).resolve()
P=R/'build_26894_iris_rawr.sh'
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
EXPECTED='1f9dcc045b6ca5fa8928443dcc28b98907b7fad152546d802445b74207244be6'
assert P.is_file() and H(P)==EXPECTED,'26894 actual SUCCESSFUL executed Actions runner NOT VERIFIED'
s=P.read_text()
STAGES=('verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay')
rex=re.compile(r'\n([a-z_]+)\(\)\{')
assert tuple(x for x in rex.findall(s) if x in STAGES)==STAGES

def once(old,new):
 global s
 assert s.count(old)==1,(old[:160],s.count(old));s=s.replace(old,new,1)
def section(n):
 start=s.index('\n'+n+'(){')+1;end=s.index('\n}',start)+2
 return s[start:end]
def edit(n,f):
 global s
 old=section(n);new=f(old)
 assert old!=new and new.startswith(n+'(){') and new.endswith('}'),n
 s=s.replace(old,new,1)
def append(old,code):return old[:-2]+'\n'+code.strip('\n')+'\n}'

# Successor metadata changes are deliberate; pinned successful parent compiler,
# compiler order, generated original runner and preexisting historical stages stay.
for a,b in [
 ('REPO_SCAFFOLD_BASE_COMMIT="0e80de60417b0d86da76d34580850b6d06f8f919"','REPO_SCAFFOLD_BASE_COMMIT="cbddb97efbdb1afb21b0fc5ba232f3b39b878bda"'),
 ('RUNTIME_ARTIFACT_ID="13057770110"; RUNTIME_ACTIONS_RUN="41239754473"','RUNTIME_ARTIFACT_ID="13063845124"; RUNTIME_ACTIONS_RUN="41254753045"'),
 ('RUNTIME_AUTHORITY_COMMIT="0e80de60417b0d86da76d34580850b6d06f8f919"','RUNTIME_AUTHORITY_COMMIT="cbddb97efbdb1afb21b0fc5ba232f3b39b878bda"'),
 ('RUNTIME_ARTIFACT_SHA="41cbf627bdec83b145bf751ef10b1178a6eecb200c6820590da4530f6cc2cba7"','RUNTIME_ARTIFACT_SHA="9c11c0941ca6800adb8555336bcbbe5e615e9d8fb47f68598a1129ad6e18385d"'),
 ('RUNTIME_TAR_SHA="56c216da6a3fe895fed5eea04e70b3eaf4d3b7c534b6a89ba48d071e85c65d3b"','RUNTIME_TAR_SHA="3051678a91741a07ac4aa8829d35bd2de135b1c6a69b2dff7d5a55ada1e139db"'),
 ('VERSION_NAME="0.9726894"; VERSION_BUILD="26894"','VERSION_NAME="0.9726895"; VERSION_BUILD="26895"'),
 ('OUT="$ROOT/build_26894_iris_rawr_outputs"; WORK="$ROOT/.build_26894_iris_rawr_work"','OUT="$ROOT/build_26895_iris_rawr_outputs"; WORK="$ROOT/.build_26895_iris_rawr_work"'),
 ('ARTZIP="$WORK/26893_artifact.zip"; ARTDIR="$WORK/artifact_26893"','ARTZIP="$WORK/26894_artifact.zip"; ARTDIR="$WORK/artifact_26894"'),
 ('BASE="$WORK/exact_successful_26893_compiled_candidate"; CAND="$WORK/candidate_26894"','BASE="$WORK/exact_successful_26894_compiled_candidate"; CAND="$WORK/candidate_26895"'),
 ('# IRIS_26894_AUTHORITATIVE_ACTIONS_STAGE_ORDER','# IRIS_26895_AUTHORITATIVE_ACTIONS_STAGE_ORDER')]:once(a,b)
# Write current successor compiler records (old artifacts are kept separately).
s=s.replace('$OUT/26894_','$OUT/26895_')
# Historical 26889 shader ABI came from actual parent artifact 26894.
once('"$ARTDIR/build_26893_iris_rawr_outputs/26888_modified_shader_spirv/Iris26887BOffHdrqMerge_prod.spv"',
     '"$ARTDIR/build_26894_iris_rawr_outputs/26888_modified_shader_spirv/Iris26887BOffHdrqMerge_prod.spv"')
# Inherited original 26894 make_candidate is fully replayed on real compiled
# 26893 source recovered by reversing its exact successful 26894 patch.
parent=section('make_candidate')
history=parent.replace('make_candidate(){','historical_26894_make_candidate(){',1)
next_stage='''make_candidate(){
 local H93="$WORK/historical_26893_from_26894" H94="$WORK/historical_26894_replayed"
 cp -a "$BASE" "$H93"; git -C "$H93" init -q
 (cd "$H93" && git apply --check --reverse "$ROOT/26894_FORWARD_FULL_INDEX.patch" && \\
  git apply --reverse "$ROOT/26894_FORWARD_FULL_INDEX.patch" && \\
  sha256sum -c "$ROOT/26894_BASE_FULL_APP.sha256" >/dev/null) || fail '26894 compiled authority rollback to successful 26893 failed'
 rm -rf "$H93/.git"
 (local BASE="$H93" CAND="$H94"; historical_26894_make_candidate)
 diff -qr "$BASE/app" "$H94/app" >/dev/null || fail 'historical 26894 generated candidate differs from actual compiled 26894'
 python3 -S verify_26894.py candidate "$H93" "$H94"
 python3 -S verify_26894.py semantics "$H93" "$H94"
 python3 -S verify_26894.py tone
 python3 -S verify_26894.py patch "$H93" "$H94" 26894_FORWARD_FULL_INDEX.patch 26894_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26894.py tamper "$H93" "$H94"
 python3 -S verify_26895.py candidate "$BASE" "$CAND" --transform
 python3 -S verify_26895.py semantics "$BASE" "$CAND"
 python3 -S verify_26895.py shader "$CAND"
}'''
assert s.count(parent)==1
s=s.replace(parent,history+'\n'+next_stage,1)

# All 26894 tests run against the historical 26894 replay instead of current
# 26895: this is mandatory because reverting 26894 was explicitly requested.
H93='"$WORK/historical_26893_from_26894"';H94='"$WORK/historical_26894_replayed"'
for n in STAGES:
 if n in ('verify_scope','obtain_authority','make_candidate'):continue
 old=section(n);new=old
 new=new.replace('verify_26894.py candidate "$BASE" "$CAND"','verify_26894.py candidate '+H93+' '+H94)
 new=new.replace('verify_26894.py semantics "$BASE" "$CAND"','verify_26894.py semantics '+H93+' '+H94)
 new=new.replace('verify_26894.py patch "$BASE" "$CAND"','verify_26894.py patch '+H93+' '+H94)
 new=new.replace('verify_26894.py tamper "$BASE" "$CAND"','verify_26894.py tamper '+H93+' '+H94)
 new=new.replace('verify_26894.py shader "$CAND"','verify_26894.py shader '+H94)
 new=new.replace('(cd "$CAND" && sha256sum -c "$ROOT/26894_UNCHANGED_PROTECTED.sha256"','(cd '+H94+' && sha256sum -c "$ROOT/26894_UNCHANGED_PROTECTED.sha256"')
 new=new.replace('(cd "$CAND" && sha256sum -c "$ROOT/26894_EXPECTED_CANDIDATE_FULL_APP.sha256"','(cd '+H94+' && sha256sum -c "$ROOT/26894_EXPECTED_CANDIDATE_FULL_APP.sha256"')
 if n=='postbuild_proof':
  new=new.replace('(cd "$CAND" && tar --sort=name','(cd '+H94+' && tar --sort=name')
 if n=='clean_extract_replay':
  new=new.replace('verify_26894.py candidate "$BASE" "$replay" --transform','verify_26895.py candidate "$BASE" "$replay" --transform')
  new=new.replace('diff -qr "$CAND/app" "$exp/app" >/dev/null','diff -qr '+H94+'/app "$exp/app" >/dev/null')
 if new!=old:s=s.replace(old,new,1)

edit('verify_scope',lambda _:'''verify_scope(){
 [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail 'wrong branch'
 git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD || fail '26894 successful compiled authority not ancestor'
 [[ -z "$(git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD -- app/src app/version.properties)" ]] || fail 'unexpected live runtime drift'
 [[ -z "$(git status --porcelain -- app/src app/version.properties)" ]] || fail 'uncommitted live runtime drift'
 diff -u 26895_REPOSITORY_UPLOAD_ALLOWLIST.txt <(git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | LC_ALL=C sort) >/dev/null || fail '26895 committed exact stage-only scope drift'
 [[ "$(sha build_26894_iris_rawr.sh)" == '1f9dcc045b6ca5fa8928443dcc28b98907b7fad152546d802445b74207244be6' ]] || fail 'exact successful 26894 executed runner drift'
 pass '26895 exact successful 26894 runner, stage-only one trigger, 26893 source restoration baseline'
}''')
edit('obtain_authority',lambda _:'''obtain_authority(){
 [[ -n "$TOKEN" ]] || fail 'GITHUB_TOKEN missing'
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
  "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/runs/${RUNTIME_ACTIONS_RUN}" -o "$WORK/26894_run.json"
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
  "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}" -o "$WORK/26894_artifact_metadata.json"
 python3 -S - "$WORK/26894_run.json" "$WORK/26894_artifact_metadata.json" <<'PY_AUTH_95'
import json,sys
run=json.load(open(sys.argv[1]));art=json.load(open(sys.argv[2]))
assert run['id']==41254753045 and run['conclusion']=='success' and run['head_sha']=='cbddb97efbdb1afb21b0fc5ba232f3b39b878bda' and run['head_branch']=='experimental-clean-photon-rebuild'
assert art['id']==13063845124 and art.get('expired') is False and art.get('digest')=='sha256:9c11c0941ca6800adb8555336bcbbe5e615e9d8fb47f68598a1129ad6e18385d'
print('PASS actual latest 26894 successful Actions run + immutable artifact ID/digest')
PY_AUTH_95
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
  "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"
 [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail '26894 actual artifact archive digest mismatch'
 unzip -q "$ARTZIP" -d "$ARTDIR"
 local T="$ARTDIR/build_26894_iris_rawr_outputs/26894_candidate_app_source.tar.gz"
 [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail '26894 actual compiled source TAR mismatch'
 local EXEC="$ARTDIR/build_26894_iris_rawr_outputs/exact_generated_runner/build_26894_iris_rawr.sh"
 [[ -f "$EXEC" && "$(sha "$EXEC")" == '1f9dcc045b6ca5fa8928443dcc28b98907b7fad152546d802445b74207244be6' ]] || fail 'actual successful 26894 runner missing/mismatch'
 cmp -s "$EXEC" "$ROOT/build_26894_iris_rawr.sh" || fail 'original 26894 generator replay differs from Actions executed runner'
 test -f "$ARTDIR/build_26894_iris_rawr_outputs/exact_generated_runner/SUCCESSFUL_ACTIONS_EVIDENCE.json" || fail '26894 successful evidence missing'
 for k in 'REAL GLSL COMPILE: PASS' 'REAL SPIR-V VALIDATION: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS';do
  grep -F "$k" "$ARTDIR/build_26894_iris_rawr_outputs/26894_COMPILER_STATUS.txt" >/dev/null || fail "26894 actual successful compiler receipt missing: $k"
 done
 mkdir -p "$BASE";tar -xzf "$T" -C "$BASE"
 [[ "$(find "$BASE/app" -type f | wc -l)" -eq 2026 ]] || fail '26894 actual compiled source file count mismatch'
 (cd "$BASE" && sha256sum -c "$ROOT/26895_BASE_FULL_APP.sha256" >/dev/null) || fail '26894 full compiled authority hashes mismatch'
 cmp -s "$ARTDIR/build_26894_iris_rawr_outputs/26894_candidate_full_app.sha256" "$ROOT/26895_BASE_FULL_APP.sha256" || fail 'actual 26894 compiled source manifest receipt mismatch'
 pass '26894 successful compiled 2026 exact source + executed runner + real compiler receipts'
}''')
# Preserve inherited stages; add only current successor gates at stage boundaries.
edit('verify_package',lambda old:append(old,''' test -f TRIGGER_26895.txt && grep -Fx 'RUN_26895_26893_BASELINE_IRIS_SATURATION_1P14_V1' TRIGGER_26895.txt >/dev/null || fail '26895 new exact single trigger'
 python3 -S stage_26895_root.py
 sha256sum -c 26895_HANDOFF_HASHES.sha256 >/dev/null || fail '26895 staged bytes SHA seal drift'
 python3 -S -m py_compile generate_26895_build.py verify_26895.py stage_26895_root.py test_26895_three_stage_negatives.py
 test "$(find handoff_payload_26895 -type f | wc -l)" -eq 4 || fail '26895 four payload files + one shader deletion scope drift'
'''))
edit('verify_successful_mechanics',lambda old:append(old,''' python3 -S verify_26895.py candidate "$BASE" "$CAND"
 python3 -S verify_26895.py semantics "$BASE" "$CAND"
'''))
edit('compile_modified_runtime_shaders',lambda old:append(old,''' python3 -S verify_26895.py shader "$CAND" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26895_reverted_26893_GLES310" | tee "$OUT/26895_RESTORED_SHADER_COMPILER_RECEIPT.txt"
 grep -Fx 'PASS 26895 TWO exact restored 26893 GLES310 runtime programs REAL PINNED COMPILE PASS' "$OUT/26895_RESTORED_SHADER_COMPILER_RECEIPT.txt" >/dev/null || fail '26895 actual two restored shaders did not pass exact real pinned compiler'
'''))
edit('verify_candidate_patches',lambda old:append(old,''' python3 -S verify_26895.py candidate "$BASE" "$CAND"
 python3 -S verify_26895.py semantics "$BASE" "$CAND"
 python3 -S verify_26895.py patch "$BASE" "$CAND" 26895_FORWARD_FULL_INDEX.patch 26895_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26895_PATCH_VALIDATION.txt"
 python3 -S verify_26895.py tamper "$BASE" "$CAND"
'''))
edit('prebuild_safety',lambda old:append(old,''' python3 -S verify_26895.py candidate "$BASE" "$CAND"
 python3 -S verify_26895.py semantics "$BASE" "$CAND"
 (cd "$CAND" && sha256sum -c "$ROOT/26895_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26895 restored 26893 protected source drift'
 test -s "$OUT/26895_RESTORED_SHADER_COMPILER_RECEIPT.txt" && grep -Fx 'PASS 26895 TWO exact restored 26893 GLES310 runtime programs REAL PINNED COMPILE PASS' "$OUT/26895_RESTORED_SHADER_COMPILER_RECEIPT.txt" >/dev/null || fail '26895 final restored GLES310 real pinned compile mandatory'
 test "$(grep -Fc 'VERSION_BUILD=26895' "$CAND/app/version.properties")" -eq 1 || fail '26895 wrong version before assemble'
 cat >> "$OUT/26895_PREBUILD_SAFETY.txt" <<'EOF_26895_SAFETY'
26895_exact_successful_26894_runtime_TAR=3051678a91741a07ac4aa8829d35bd2de135b1c6a69b2dff7d5a55ada1e139db
26895_actual_successful_26894_runner=1f9dcc045b6ca5fa8928443dcc28b98907b7fad152546d802445b74207244be6
26895_runtime=26894 compiled 2026 to 26895 2025 files; EXACT 26893 runtime except Java saturation and version
26895_saturation=Iris per-lens 1.00 UI -> 1.14 effective; equals old 26893 1.20 UI * 0.95; Night unchanged
26895_26894_spatial_scene=DELETED; 26894 visual corrections fully reverted
26895_protected=2021 source hashes unchanged; 2 modified restored shaders REAL pinned compiled; actual Kotlin Java NDK and full assemble mandatory
EOF_26895_SAFETY
'''))
edit('postbuild_proof',lambda old:append(old,''' python3 -S verify_26895.py candidate "$BASE" "$CAND"
 python3 -S verify_26895.py semantics "$BASE" "$CAND"
 (cd "$CAND" && sha256sum -c "$ROOT/26895_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26895 protected postbuild mismatch'
 (cd "$CAND" && sha256sum -c "$ROOT/26895_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null) || fail '26895 full candidate postbuild mismatch'
 cp 26895_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26895_candidate_full_app.sha256"
 cp 26895_FORWARD_FULL_INDEX.patch 26895_ROLLBACK_FULL_INDEX.patch 26895_CHANGED_ALLOWLIST.txt 26895_DELETIONS.txt 26895_UNCHANGED_PROTECTED.sha256 "$OUT/"
 (cd "$CAND" && tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26895_candidate_app_source.tar.gz" app)
 sha256sum "$OUT/26895_candidate_app_source.tar.gz" > "$OUT/26895_candidate_app_source.tar.gz.sha256"
'''))
edit('clean_extract_replay',lambda old:append(old,''' python3 -S verify_26895.py candidate "$BASE" "$CAND"
 python3 -S verify_26895.py semantics "$BASE" "$CAND"
 python3 -S verify_26895.py shader "$CAND" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26895_final_restored_real_GLES310"
 python3 -S verify_26895.py patch "$BASE" "$CAND" 26895_FORWARD_FULL_INDEX.patch 26895_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26895.py tamper "$BASE" "$CAND"
 python3 -S test_26895_three_stage_negatives.py
 (cd "$CAND" && sha256sum -c "$ROOT/26895_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 (cd "$CAND" && sha256sum -c "$ROOT/26895_UNCHANGED_PROTECTED.sha256" >/dev/null)
 sha256sum -c "$OUT/26895_candidate_app_source.tar.gz.sha256" >/dev/null
 local exp95="$WORK/extracted_actual_26895_candidate_tar";rm -rf "$exp95";mkdir -p "$exp95"
 tar -xzf "$OUT/26895_candidate_app_source.tar.gz" -C "$exp95"
 diff -qr "$CAND/app" "$exp95/app" >/dev/null || fail '26895 clean extracted compiled source differs from frozen candidate'
 grep -Fx 'VERSION_NAME=0.9726895' "$exp95/app/version.properties" >/dev/null || fail '26895 clean-extract name version check'
 grep -Fx 'VERSION_BUILD=26895' "$exp95/app/version.properties" >/dev/null || fail '26895 clean-extract build version check'
 [[ ! -e "$exp95/app/src/main/assets/shaders/motionv2/spatial_scene_26894.glsl" ]] || fail '26894 scene correction not removed'
 (cd "$exp95" && sha256sum -c "$ROOT/26895_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 pass '26895 all real/locally applicable 17-stage gates inherited, clean-extract final candidate, 26893 runtime visual baseline, 1.14 saturation'
'''))
# Update inherited *descriptive* prebuild proof header to actual 26895,
# without replacing any historical runnable gate or compiler command.
def current_proof_header(o):
 start=o.index('runtime_authority=successful 26892 $RUNTIME_AUTHORITY_COMMIT')
 end=o.index('EOF_SAFETY',start)
 old=o[start:end]
 new=old.replace('runtime_authority=successful 26892 $RUNTIME_AUTHORITY_COMMIT','runtime_authority=successful 26894 $RUNTIME_AUTHORITY_COMMIT')
 new=new.replace('verification_mechanics=exact successful 26890 inherited 17 stages, real compiler/NDK/assemble commands','verification_mechanics=EXACT successful 26894 executed 17 stages, real compiler/NDK/assemble commands')
 new=new.replace('runtime_changed_files=4 (4 existing, 0 additions/deletions); 2021 protected, B-off ONLY calibrated backlit + darken-only scene contrast, 26892 HDRQ unchanged','runtime_changed_files=5 (4 modified existing plus one deleted 26894 scene shader), 2021 protected; candidate byte-identical to successful 26893 except Java saturation and version')
 new=new.replace('infrastructure_delta=26891 strict successor workflow single-trigger + source validators; exact inherited 17-stage compiler+freeze+assemble mechanics','infrastructure_delta=one strict successor workflow/trigger + source validators; exact 26894 inherited 17-stage compiler+freeze+assemble mechanics')
 new=new.replace('prior_files=2025\ncandidate_files=2025','prior_files=2026\ncandidate_files=2025')
 new=new.replace('protected_source=2021 files byte-identical to successful 26892 compiled candidate; Spektra/A/A+B/Night/LONG/DNG/UHDR and vendor protected','protected_source=2021 files byte-identical to successful 26894 compiled candidate; Spektra/A/A+B/Night/LONG/DNG/UHDR and vendor protected')
 assert old!=new
 return o[:start]+new+o[end:]
edit('prebuild_safety',current_proof_header)

# Preserve original successful 26894 historical compiled-source TAR separately
# from the NEW current 26895 compiled TAR; otherwise the old clean-extract
# version guard would silently test the new version and repeat the 26894 V1 bug.
for name in ('postbuild_proof','clean_extract_replay'):
 def historic_tar_only(o):
  marker=' python3 -S verify_26895.py candidate "$BASE" "$CAND"'
  assert o.count(marker)==1,(name,o.count(marker))
  pre,post=o.split(marker,1)
  assert pre.count('$OUT/26895_candidate_app_source.tar.gz')>=2
  pre=pre.replace('$OUT/26895_candidate_app_source.tar.gz', '$OUT/26894_historical_candidate_app_source.tar.gz')
  return pre+marker+post
 edit(name,historic_tar_only)
assert section('clean_extract_replay').count('26894_historical_candidate_app_source.tar.gz')>=3
assert section('clean_extract_replay').count('26895_candidate_app_source.tar.gz')>=2
assert section('postbuild_proof').count('26894_historical_candidate_app_source.tar.gz')>=4

# Prevent old historical metadata from being advertised as the new current artifact.
assert section('postbuild_proof').count('26895_candidate_app_source.tar.gz')>=2
assert section('clean_extract_replay').count("VERSION_NAME=0.9726895")==1
assert section('clean_extract_replay').count("VERSION_BUILD=26895")==1
assert tuple(x for x in rex.findall(s) if x in STAGES)==STAGES
for cmd in [' ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac',' ./gradlew \':app:buildCMakeDebug[arm64-v8a]\' \':app:buildCMakeDebug[armeabi-v7a]\'',' ./gradlew :app:assembleDebug --stacktrace 2>&1 | tee']:
 assert s.count(cmd)==1,(cmd,s.count(cmd))
assert s.count('python3 -S verify_26889_compiled_push_abi.py ')==1
assert 'build_26894_iris_rawr_outputs/26888_modified_shader_spirv/Iris26887BOffHdrqMerge_prod.spv' in s
assert 'VERSION_NAME="0.9726895"; VERSION_BUILD="26895"' in s
assert section('clean_extract_replay').count("grep -Fx 'VERSION_NAME=0.9726894'")==1
assert section('clean_extract_replay').count("grep -Fx 'VERSION_BUILD=26894'")==1
out=R/'build_26895_iris_rawr.sh';out.write_text(s)
sha=H(out)
(R/'26895_GENERATED_BUILD_SHA256.txt').write_text(sha+'  build_26895_iris_rawr.sh\n')
print('PASS deterministic 26895 from ACTUAL compiled successful 26894 executed runner; 17 identical stage order, 26893 runtime restored, 2 real shaders, SHA',sha,'lines',len(s.splitlines()))
