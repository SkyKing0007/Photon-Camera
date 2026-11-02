#!/usr/bin/env python3
"""Deterministic guarded 26896 successor of EXACT successful 26895 Actions runner.
Preserve every inherited successful compiler/native/assemble stage and replay
historical 26895 verification on its own successful 26894/26895 bytes.
"""
from pathlib import Path
import hashlib,re,sys
R=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
P=R/'build_26895_iris_rawr.sh'
H=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
EXACT='a6c341d9389887329a55545c78c5c25e727655fbae73ccedc2c353d321165b2b'
assert P.is_file() and H(P)==EXACT,'successful 26895 ACTUAL executed 17-stage runner missing/mismatch'
s=P.read_text()
STAGES=('verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay')
rx=re.compile(r'\n([a-z_]+)\(\)\{')
assert tuple(x for x in rx.findall(s) if x in STAGES)==STAGES

def once(a,b):
 global s
 assert s.count(a)==1,(a[:120],s.count(a));s=s.replace(a,b,1)
def sec(name):
 start=s.index('\n'+name+'(){')+1;end=s.index('\n}',start)+2
 return s[start:end]
def rewrite(name,f):
 global s
 old=sec(name);new=f(old)
 assert new!=old and new.startswith(name+'(){') and new.endswith('}'),name
 s=s.replace(old,new,1)
def append(old,code):return old[:-2]+'\n'+code.strip('\n')+'\n}'

# Successor metadata advancement ONLY: the entire inherited guarded script
# body/17-stage procedure is retained and stage boundaries extended.
for a,b in [
 ('REPO_SCAFFOLD_BASE_COMMIT="cbddb97efbdb1afb21b0fc5ba232f3b39b878bda"','REPO_SCAFFOLD_BASE_COMMIT="b7b89a46e679fc68543af91792396b75e0e68fbb"'),
 ('RUNTIME_ARTIFACT_ID="13063845124"; RUNTIME_ACTIONS_RUN="41254753045"','RUNTIME_ARTIFACT_ID="13094804636"; RUNTIME_ACTIONS_RUN="41334644093"'),
 ('RUNTIME_AUTHORITY_COMMIT="cbddb97efbdb1afb21b0fc5ba232f3b39b878bda"','RUNTIME_AUTHORITY_COMMIT="b7b89a46e679fc68543af91792396b75e0e68fbb"'),
 ('RUNTIME_ARTIFACT_SHA="9c11c0941ca6800adb8555336bcbbe5e615e9d8fb47f68598a1129ad6e18385d"','RUNTIME_ARTIFACT_SHA="a7e91e76204268d14d32449d9906a192b3e1e76bbd67852d02f6576d8df43b76"'),
 ('RUNTIME_TAR_SHA="3051678a91741a07ac4aa8829d35bd2de135b1c6a69b2dff7d5a55ada1e139db"','RUNTIME_TAR_SHA="9df70bdc87756847b7c5a479cb3b22fee7a47920ac277a70d14a5402e3cb6942"'),
 ('VERSION_NAME="0.9726895"; VERSION_BUILD="26895"','VERSION_NAME="0.9726896"; VERSION_BUILD="26896"'),
 ('OUT="$ROOT/build_26895_iris_rawr_outputs"; WORK="$ROOT/.build_26895_iris_rawr_work"','OUT="$ROOT/build_26896_iris_rawr_outputs"; WORK="$ROOT/.build_26896_iris_rawr_work"'),
 ('ARTZIP="$WORK/26894_artifact.zip"; ARTDIR="$WORK/artifact_26894"','ARTZIP="$WORK/26895_artifact.zip"; ARTDIR="$WORK/artifact_26895"'),
 ('BASE="$WORK/exact_successful_26894_compiled_candidate"; CAND="$WORK/candidate_26895"','BASE="$WORK/exact_successful_26895_compiled_candidate"; CAND="$WORK/candidate_26896"'),
 ('# IRIS_26895_AUTHORITATIVE_ACTIONS_STAGE_ORDER','# IRIS_26896_AUTHORITATIVE_ACTIONS_STAGE_ORDER'),
]:once(a,b)
# Redirect current output receipts into current 26896 proof directory; names
# of original 26895 historical source, scripts, patches and tests remain intact.
s=s.replace('$OUT/26895_','$OUT/26896_')
# 26889 pinned shader archive must come from ACTUAL successful parent artifact.
once('"$ARTDIR/build_26894_iris_rawr_outputs/26888_modified_shader_spirv/Iris26887BOffHdrqMerge_prod.spv"',
     '"$ARTDIR/build_26895_iris_rawr_outputs/26888_modified_shader_spirv/Iris26887BOffHdrqMerge_prod.spv"')

old=sec('make_candidate')
assert 'python3 -S verify_26895.py candidate "$BASE" "$CAND" --transform' in old
hist=old.replace('make_candidate(){','historical_26895_make_candidate(){',1)
new='''make_candidate(){
 local H94="$WORK/historical_26894_from_26895" H95="$WORK/historical_26895_replayed"
 cp -a "$BASE" "$H94"; git -C "$H94" init -q
 (cd "$H94" && git apply --check --reverse "$ROOT/26895_FORWARD_FULL_INDEX.patch" && \\
  git apply --reverse "$ROOT/26895_FORWARD_FULL_INDEX.patch" && \\
  sha256sum -c "$ROOT/26895_BASE_FULL_APP.sha256" >/dev/null) || fail 'successful 26895 2025 source cannot reverse to exact successful 26894'
 rm -rf "$H94/.git"
 (local BASE="$H94" CAND="$H95"; historical_26895_make_candidate)
 diff -qr "$BASE/app" "$H95/app" >/dev/null || fail 'historical exact 26895 generator differs from successful compiled 26895 authority'
 python3 -S verify_26895.py candidate "$H94" "$H95"
 python3 -S verify_26895.py semantics "$H94" "$H95"
 python3 -S verify_26895.py patch "$H94" "$H95" 26895_FORWARD_FULL_INDEX.patch 26895_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26895.py tamper "$H94" "$H95"
 python3 -S verify_26896.py candidate "$BASE" "$CAND" --transform
 python3 -S verify_26896.py semantics "$BASE" "$CAND"
}'''
assert s.count(old)==1;s=s.replace(old,hist+'\n'+new,1)
H94='"$WORK/historical_26894_from_26895"';H95='"$WORK/historical_26895_replayed"'
# Every earlier 26895 candidate verifier runs against its ORIGINAL successful
# source bytes, not the intentionally changed 26896 C++/Java/Kotlin candidate.
for name in STAGES:
 if name in ('verify_scope','obtain_authority','make_candidate'):continue
 old=sec(name);new=old
 for kind in ('candidate','semantics','patch','tamper'):
  new=new.replace('verify_26895.py '+kind+' "$BASE" "$CAND"','verify_26895.py '+kind+' '+H94+' '+H95)
 new=new.replace('verify_26895.py shader "$CAND"','verify_26895.py shader '+H95)
 # 26895 source/protection hashes always apply to 26895 historical snapshot.
 new=new.replace('(cd "$CAND" && sha256sum -c "$ROOT/26895_UNCHANGED_PROTECTED.sha256"','(cd '+H95+' && sha256sum -c "$ROOT/26895_UNCHANGED_PROTECTED.sha256"')
 new=new.replace('(cd "$CAND" && sha256sum -c "$ROOT/26895_EXPECTED_CANDIDATE_FULL_APP.sha256"','(cd '+H95+' && sha256sum -c "$ROOT/26895_EXPECTED_CANDIDATE_FULL_APP.sha256"')
 if name=='prebuild_safety':
  new=new.replace('"$CAND/app/version.properties"','"$WORK/historical_26895_replayed/app/version.properties"')
 if name=='postbuild_proof':
  # Only historical 26895 archive exports 26895 source from this stage.
  new=new.replace('(cd "$CAND" && tar --sort=name','(cd '+H95+' && tar --sort=name')
 if name=='clean_extract_replay':
  new=new.replace('verify_26895.py candidate "$BASE" "$replay" --transform','verify_26895.py candidate '+H94+' "$replay" --transform')
  new=new.replace('diff -qr "$CAND/app" "$replay/app" >/dev/null','diff -qr '+H95+'/app "$replay/app" >/dev/null')
  new=new.replace('diff -qr "$CAND/app" "$exp95/app" >/dev/null','diff -qr '+H95+'/app "$exp95/app" >/dev/null')
 if new!=old:s=s.replace(old,new,1)

# The newest successful Actions artifact is runtime/runner authority (not raw
# repo app/src). Use exact ID/digest/job/sha/compiler receipts and a verified
# internal 26895 TAR before touching any current 26896 source.
rewrite('verify_scope',lambda _:'''verify_scope(){
 [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail 'wrong build branch'
 git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD || fail 'successful 26895 not ancestor'
 [[ -z "$(git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD -- app/src app/version.properties)" ]] || fail 'unexpected committed real runtime source'
 [[ -z "$(git status --porcelain -- app/src app/version.properties)" ]] || fail 'uncommitted real runtime source drift'
 diff -u 26896_REPOSITORY_UPLOAD_ALLOWLIST.txt <(git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | LC_ALL=C sort) >/dev/null || fail '26896 exact stage-only Git scope mismatch'
 [[ "$(sha build_26895_iris_rawr.sh)" == 'a6c341d9389887329a55545c78c5c25e727655fbae73ccedc2c353d321165b2b' ]] || fail 'actual successful 26895 runner drift'
 pass '26896 successful 26895 guarded runner frozen, single new workflow trigger, zero live app edits'
}''')
rewrite('obtain_authority',lambda _:'''obtain_authority(){
 [[ -n "$TOKEN" ]] || fail 'GITHUB_TOKEN missing'
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
  "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/runs/${RUNTIME_ACTIONS_RUN}" -o "$WORK/26895_run.json"
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
  "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}" -o "$WORK/26895_artifact_metadata.json"
 python3 -S - "$WORK/26895_run.json" "$WORK/26895_artifact_metadata.json" <<'PY_AUTH_96'
import json,sys
run=json.load(open(sys.argv[1]));art=json.load(open(sys.argv[2]))
assert run['id']==41334644093 and run['conclusion']=='success' and run['head_sha']=='b7b89a46e679fc68543af91792396b75e0e68fbb' and run['head_branch']=='experimental-clean-photon-rebuild'
assert art['id']==13094804636 and art.get('expired') is False and art.get('digest')=='sha256:a7e91e76204268d14d32449d9906a192b3e1e76bbd67852d02f6576d8df43b76'
print('PASS actual latest successful 26895 run, immutable artifact ID/digest/commit')
PY_AUTH_96
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
  "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"
 [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail 'actual successful 26895 artifact ZIP digest mismatch'
 unzip -q "$ARTZIP" -d "$ARTDIR"
 local T="$ARTDIR/build_26895_iris_rawr_outputs/26895_candidate_app_source.tar.gz"
 [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail 'ACTUAL successful 26895 internal compiled TAR mismatch'
 local EXEC="$ARTDIR/build_26895_iris_rawr_outputs/exact_generated_runner/build_26895_iris_rawr.sh"
 [[ -f "$EXEC" && "$(sha "$EXEC")" == 'a6c341d9389887329a55545c78c5c25e727655fbae73ccedc2c353d321165b2b' ]] || fail 'ACTUAL successful 26895 runner missing/mismatch'
 cmp -s "$EXEC" "$ROOT/build_26895_iris_rawr.sh" || fail 'generated 26895 differs from ACTUAL executed runner'
 test -f "$ARTDIR/build_26895_iris_rawr_outputs/exact_generated_runner/SUCCESSFUL_ACTIONS_EVIDENCE.json" || fail '26895 executed runner evidence missing'
 for k in 'REAL GLSL COMPILE: PASS' 'REAL SPIR-V VALIDATION: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS';do
  grep -F "$k" "$ARTDIR/build_26895_iris_rawr_outputs/26895_COMPILER_STATUS.txt" >/dev/null || fail "actual 26895 compiler receipt missing: $k"
 done
 mkdir -p "$BASE";tar -xzf "$T" -C "$BASE"
 [[ "$(find "$BASE/app" -type f | wc -l)" -eq 2025 ]] || fail 'successful 26895 source file count mismatch'
 (cd "$BASE" && sha256sum -c "$ROOT/26896_BASE_FULL_APP.sha256" >/dev/null) || fail 'successful 26895 full manifest mismatch'
 cmp -s "$ARTDIR/build_26895_iris_rawr_outputs/26895_candidate_full_app.sha256" "$ROOT/26896_BASE_FULL_APP.sha256" || fail 'successful 26895 compiled candidate manifest differs'
 pass '26895 successful 2025 compiled-source TAR, actual executed runner, compiler receipts and full manifest matched'
}''')

rewrite('verify_package',lambda old:append(old,''' test -f TRIGGER_26896.txt && grep -Fx 'RUN_26896_PIXEL_MOTION_GPU_BUDGET_SPEKTRA_NATIVE_RES_AND_SAVE_V1' TRIGGER_26896.txt >/dev/null || fail '26896 immutable sole trigger drift'
 python3 -S stage_26896_root.py
 sha256sum -c 26896_HANDOFF_HASHES.sha256 >/dev/null || fail '26896 final staged upload bytes drift'
 python3 -S -m py_compile generate_26896_build.py verify_26896.py stage_26896_root.py test_26896_three_stage_negatives.py test_26896_java_selection.py
 test "$(find handoff_payload_26896 -type f | wc -l)" -eq 11 || fail '26896 11-file B/Spektra exact allowlist drift'
'''))
rewrite('verify_successful_mechanics',lambda old:append(old,''' python3 -S verify_26896.py candidate "$BASE" "$CAND"
 python3 -S verify_26896.py semantics "$BASE" "$CAND"
 python3 -S test_26896_java_selection.py "$CAND"
'''))
# No GLSL source is modified by 26896: inherit all 26895 real pinned
# historical compiler calls; expressly guard runtime shader bytes.
rewrite('compile_modified_runtime_shaders',lambda old:append(old,''' (cd "$CAND" && sha256sum -c "$ROOT/26896_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26896 current unchanged shaders/protected source differs before real pinned compilers'
'''))
rewrite('verify_candidate_patches',lambda old:append(old,''' python3 -S verify_26896.py candidate "$BASE" "$CAND"
 python3 -S verify_26896.py semantics "$BASE" "$CAND"
 python3 -S verify_26896.py patch "$BASE" "$CAND" 26896_FORWARD_FULL_INDEX.patch 26896_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26896_PATCH_VALIDATION.txt"
 python3 -S verify_26896.py tamper "$BASE" "$CAND"
'''))
rewrite('prebuild_safety',lambda old:append(old,''' python3 -S verify_26896.py candidate "$BASE" "$CAND"
 python3 -S verify_26896.py semantics "$BASE" "$CAND"
 (cd "$CAND" && sha256sum -c "$ROOT/26896_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26896 protected prebuild source invariant failure'
 test "$(grep -Fc 'VERSION_BUILD=26896' "$CAND/app/version.properties")" -eq 1 || fail '26896 wrong version before assemble'
 test -s "$OUT/26896_PATCH_VALIDATION.txt" || fail '26896 real four-operand current patch proof required'
 cat >> "$OUT/26896_PREBUILD_SAFETY.txt" <<'EOF_26896_SAFETY'
26896_actual_successful_26895_compiled_TAR=9df70bdc87756847b7c5a479cb3b22fee7a47920ac277a70d14a5402e3cb6942
26896_successful_26895_runner_SHA=a6c341d9389887329a55545c78c5c25e727655fbae73ccedc2c353d321165b2b
26896_runtime=2025 source files, 11 modified, 2014 protected, zero additions/deletions
26896_spektra=OFF normal RAW, ON genuine advertised maximum RAW; immutable shutter stream; independent from B Wronski
26896_save=accepted developed bitmap transaction persists after Camera2 lifecycle release and closes after JPEG worker drain
26896_motion=Vulkan resident input requires real heapBudget-heapUsage, otherwise fenced two-slot; full frames preserved; Android previous native process exit reasons + bounded native phases
26896_compiler_gate=current Java/Kotlin/native+NDK ABIs mandatory; all GLSL owners protected hash-identical from successful 26895
26896_pixel_device_verification=NOT RUN - real Pixel must confirm native exit cause and Motion completion
EOF_26896_SAFETY
'''))
# Adjust inherited descriptive header (not any compiler command) to current authority.
def safety_header(o):
 start=o.index('runtime_authority=successful 26894 $RUNTIME_AUTHORITY_COMMIT');end=o.index('EOF_SAFETY',start)
 old=o[start:end]
 new=old.replace('runtime_authority=successful 26894','runtime_authority=successful 26895')
 new=new.replace('verification_mechanics=EXACT successful 26894 executed 17 stages','verification_mechanics=EXACT successful 26895 executed 17 stages')
 new=new.replace('runtime_changed_files=5 (4 modified existing plus one deleted 26894 scene shader), 2021 protected; candidate byte-identical to successful 26893 except Java saturation and version','runtime_changed_files=11 modified existing, 2014 protected; explicit Pixel B memory-budget and diagnostics plus isolated Spektra capture/save fixes')
 new=new.replace('prior_files=2026\ncandidate_files=2025','prior_files=2025\ncandidate_files=2025')
 new=new.replace('protected_source=2021 files byte-identical to successful 26894 compiled candidate; Spektra/A/A+B/Night/LONG/DNG/UHDR and vendor protected','protected_source=2014 files byte-identical to successful 26895 compiled candidate; A/A+B/Night/LONG/DNG/UHDR/vendor/GLSL protected')
 assert old!=new;return o[:start]+new+o[end:]
rewrite('prebuild_safety',safety_header)
# Historical 26895 source archive is separate from CURRENT compiled 26896.
rewrite('postbuild_proof',lambda old:append(old,''' python3 -S verify_26896.py candidate "$BASE" "$CAND"
 python3 -S verify_26896.py semantics "$BASE" "$CAND"
 (cd "$CAND" && sha256sum -c "$ROOT/26896_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26896 protected postbuild source mismatch'
 (cd "$CAND" && sha256sum -c "$ROOT/26896_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null) || fail '26896 final compiled candidate mismatch'
 cp 26896_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26896_candidate_full_app.sha256"
 cp 26896_FORWARD_FULL_INDEX.patch 26896_ROLLBACK_FULL_INDEX.patch 26896_CHANGED_ALLOWLIST.txt 26896_ADDITIONS.txt 26896_DELETIONS.txt 26896_UNCHANGED_PROTECTED.sha256 "$OUT/"
 (cd "$CAND" && tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26896_candidate_app_source.tar.gz" app)
 sha256sum "$OUT/26896_candidate_app_source.tar.gz" > "$OUT/26896_candidate_app_source.tar.gz.sha256"
'''))
# The inherited 26895 proof follows historical 26895; never allow it to
# accidentally treat 26896's TAR or 26896's runtime as 26895.
for name in ('postbuild_proof','clean_extract_replay'):
 def fix_historical(o):
  mark=' python3 -S verify_26896.py candidate "$BASE" "$CAND"'
  if name=='postbuild_proof':
   assert o.count(mark)==1
   pre,post=o.split(mark,1)
  else:
   pre,post=o,''
  # In postbuild, original current-26895 TAR is historic and must keep own label.
  if name=='postbuild_proof':
   assert pre.count('$OUT/26896_candidate_app_source.tar.gz')==0
   assert pre.count('$OUT/26895_candidate_app_source.tar.gz')==0  # replaced by global $OUT advancement
  return pre+(mark+post if name=='postbuild_proof' else '')
 # historical 26895 tar paths already globally renamed to $OUT/26896_candidate...,
 # so segregate BEFORE current successor block's last occurrence.
 if name=='postbuild_proof':
  old=sec(name)
  pivot=old.index(' python3 -S verify_26896.py candidate "$BASE" "$CAND"')
  pre,post=old[:pivot],old[pivot:]
  assert pre.count('$OUT/26896_candidate_app_source.tar.gz')>=2
  pre=pre.replace('$OUT/26896_candidate_app_source.tar.gz','$OUT/26895_historical_candidate_app_source.tar.gz')
  pre=pre.replace('$OUT/26896_candidate_full_app.sha256','$OUT/26895_historical_candidate_full_app.sha256')
  s=s.replace(old,pre+post,1)
 else:
  old=sec(name)
  assert old.count('$OUT/26896_candidate_app_source.tar.gz')>=2
  new=old.replace('$OUT/26896_candidate_app_source.tar.gz','$OUT/26895_historical_candidate_app_source.tar.gz')
  s=s.replace(old,new,1)
# Existing inherited 26895 output receipt name above was changed by global
# renaming: restore historical-specific test path in old clean-extract stage.
rewrite('clean_extract_replay',lambda old:append(old,''' python3 -S verify_26896.py candidate "$BASE" "$CAND"
 python3 -S verify_26896.py semantics "$BASE" "$CAND"
 python3 -S verify_26896.py patch "$BASE" "$CAND" 26896_FORWARD_FULL_INDEX.patch 26896_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26896.py tamper "$BASE" "$CAND"
 python3 -S test_26896_three_stage_negatives.py
 python3 -S test_26896_java_selection.py "$CAND"
 (cd "$CAND" && sha256sum -c "$ROOT/26896_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 (cd "$CAND" && sha256sum -c "$ROOT/26896_UNCHANGED_PROTECTED.sha256" >/dev/null)
 sha256sum -c "$OUT/26896_candidate_app_source.tar.gz.sha256" >/dev/null
 local exp96="$WORK/extracted_actual_26896_compiled_tar";rm -rf "$exp96";mkdir -p "$exp96"
 tar -xzf "$OUT/26896_candidate_app_source.tar.gz" -C "$exp96"
 diff -qr "$CAND/app" "$exp96/app" >/dev/null || fail 'final actual 26896 compiled TAR differs from built candidate'
 grep -Fx 'VERSION_NAME=0.9726896' "$exp96/app/version.properties" >/dev/null || fail '26896 clean-extract version name mismatch'
 grep -Fx 'VERSION_BUILD=26896' "$exp96/app/version.properties" >/dev/null || fail '26896 clean-extract version build mismatch'
 (cd "$exp96" && sha256sum -c "$ROOT/26896_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 pass '26896 inherited exact seventeen-stage real Actions build, byte-perfect sealed candidate, 11-source ownership, actual compiler receipts and final replay'
'''))
# Inherited 26895 prebuild historic `test -s $OUT/26896_RESTORED...` is correct
# since it was a historical compiler receipt written to this OUT.
# The original historical 26895 output archive must be checked as historic.
assert '26895_historical_candidate_app_source.tar.gz' in sec('postbuild_proof')
assert '26895_historical_candidate_app_source.tar.gz' in sec('clean_extract_replay')
assert sec('clean_extract_replay').count('26896_candidate_app_source.tar.gz')>=2
assert tuple(x for x in rx.findall(s) if x in STAGES)==STAGES
for section,cmd in [('compile_languages','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac'),
            ('compile_native',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]'"),
            ('assemble','./gradlew :app:assembleDebug --stacktrace 2>&1 | tee')]:
 assert sec(section).count(cmd)==1,(section,cmd,sec(section).count(cmd))
assert s.count('python3 -S verify_26889_compiled_push_abi.py ')==1
assert s.count('python3 -S verify_26896.py patch "$BASE" "$CAND" 26896_FORWARD_FULL_INDEX.patch 26896_ROLLBACK_FULL_INDEX.patch')==2
assert sec('clean_extract_replay').count("VERSION_BUILD=26895")==1
assert sec('clean_extract_replay').count("VERSION_BUILD=26896")==1
out=R/'build_26896_iris_rawr.sh';out.write_text(s)
(R/'26896_GENERATED_BUILD_SHA256.txt').write_text(H(out)+'  build_26896_iris_rawr.sh\n')
print('PASS deterministic 26896 from successful ACTUAL 26895 Actions executed runner; unchanged 17 stages and exact compiler+assemble commands; SHA',H(out),'lines',len(s.splitlines()))
