#!/usr/bin/env python3
"""26886 successor of the EXACT successful 26885 V2 17-stage runner.

The previous runner is never overwritten, and its SHA is mandatory. The
previous 26885 V2 40604341240 regression is preserved on exact historical
26884/26885 bytes, not accidentally fed the modified 26886 candidate.
"""
from pathlib import Path
import hashlib,re,sys,difflib
R=(Path(sys.argv[1]) if len(sys.argv)>1 else Path('.')).resolve()
old_path=R/'build_26885_iris_rawr.sh'
assert old_path.is_file(),'must FIRST reconstruct actual successful 26885 V2 runner'
original=old_path.read_text()
old_sha=hashlib.sha256(original.encode()).hexdigest()
assert old_sha=='2138db01cbfb3a8421c12e54ba29d4f0a893d1cdd4a219ee34a40a4dc0c54379',('WRONG 26885 V2 verification mechanics',old_sha)
body=original.replace('26885','26886').replace('0.9726885','0.9726886')
# Historic 26885 V2 checks with their own pinned source and self-contained
# regressions are NEVER renamed to missing imaginary 26886 validators.
for old,new in (
 ('26886_actions_40604341240_historical_scope.py','26885_actions_40604341240_historical_scope.py'),
 ('26886_wronski_chroma_evidence.py','26885_wronski_chroma_evidence.py'),
 ('26886_universal_pattern_controls.py','26885_universal_pattern_controls.py'),
 ('_26886_vector_math.py','_26885_vector_math.py'),
):
 body=body.replace(old,new)
# Previous 26885 source-level chroma regression supplied (new,old), whereas
# the 26886 true successor regression strictly requires (old,new).
for old,new in (
 ('regressions/26886_chroma_controls.py "$CAND" "$BASE"','regressions/26886_chroma_controls.py "$BASE" "$CAND"'),
 ('regressions/26886_chroma_controls.py "$exp" "$BASE"','regressions/26886_chroma_controls.py "$BASE" "$exp"'),
):
 body=body.replace(old,new)

STAGES=('verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay')
def stage_text(s,n):
 a=s.index('\n'+n+'(){')+1;b=s.index('\n}',a)+2;return s[a:b]
def edit(n,fn):
 global body
 a=body.index('\n'+n+'(){')+1;b=body.index('\n}',a)+2
 was=body[a:b];now=fn(was)
 assert now.endswith('}') and now!=was,n
 body=body[:a]+now+body[b:]
def append(s,commands):
 assert s.endswith('\n}')
 return s[:-2]+'\n'+commands.rstrip()+'\n}'
def once(s,old,new):
 assert s.count(old)==1,('missing or duplicated actual 26885 runner anchor',old,s.count(old))
 return s.replace(old,new,1)
# Exact successful Actions 26885 compiled source is NEW runtime authority.
for a,b in (
 ('REPO_SCAFFOLD_BASE_COMMIT="fb905234c419b0f1592c941d702531494e64f8fa"','REPO_SCAFFOLD_BASE_COMMIT="a46d0f7491a2c19b7d93ac69813f6b04073697cc"'),
 ('RUNTIME_AUTHORITY_COMMIT="fb905234c419b0f1592c941d702531494e64f8fa"','RUNTIME_AUTHORITY_COMMIT="a46d0f7491a2c19b7d93ac69813f6b04073697cc"'),
 ('RUNTIME_ARTIFACT_ID="12747046415"; RUNTIME_ACTIONS_RUN="40529418596"','RUNTIME_ARTIFACT_ID="12783521315"; RUNTIME_ACTIONS_RUN="40610009610"'),
 ('RUNTIME_ARTIFACT_SHA="f34b031585f35dd5a11e494483ac1e99884fe10307861ffa05f729e5b849ccc1"','RUNTIME_ARTIFACT_SHA="a738a2fbd2bcc0f9d9031696b2bf6f64cc58232a23201bf7a650d9cee60d9988"'),
 ('RUNTIME_TAR_SHA="83a5fecf3dbb3d9669a68df84bd374178c4493dfabbf2fb0cf474cce9a135d33"','RUNTIME_TAR_SHA="0d87c877a0184d7679a832b0a0ada7dc0b5a65e53cbce31ab78beb28f3fe017f"'),
 ('MECHANICS_GIT_BLOB="04b69c26de71543217fc800c1340a937c45c198f"','MECHANICS_GIT_BLOB="8a0216fc6d8e1465517cd6a80b62645dbc544e38"'),
 ('ARTZIP="$WORK/26884_artifact.zip"; ARTDIR="$WORK/artifact_26884"','ARTZIP="$WORK/26885_artifact.zip"; ARTDIR="$WORK/artifact_26885"'),
 ('BASE="$WORK/exact_successful_26884_compiled_candidate"','BASE="$WORK/exact_successful_26885_compiled_candidate"'),
):
 body=once(body,a,b)
# Metadata in obtain_authority uses GitHub REST envelope and must stay pinned.
def authority(s):
 s=once(s,"x['head_sha']=='fb905234c419b0f1592c941d702531494e64f8fa'","x['head_sha']=='a46d0f7491a2c19b7d93ac69813f6b04073697cc'")
 s=once(s,"'id':12747046415","'id':12783521315")
 s=once(s,'photon-26884-experiment-b-original-rawr-highlight-off','photon-26885-b-on-wronski-rgb-chroma-consistency')
 s=s.replace('sha256:f34b031585f35dd5a11e494483ac1e99884fe10307861ffa05f729e5b849ccc1','sha256:a738a2fbd2bcc0f9d9031696b2bf6f64cc58232a23201bf7a650d9cee60d9988')
 s=s.replace('mechanics_generated_script_sha256=f8aff63b074ee6195d6b137858ad5a3f23cb149a40c9f72cb69b51f315b4679f','mechanics_generated_script_sha256='+old_sha)
 assert '12783521315' in s and '40610009610' in body
 return s
edit('obtain_authority',authority)
# Explicitly inherit previous runtime mechanics and sealed generator, no reroute.
def mechanics(s):
 # Permanent regression: Actions 40621816379/job 122597388924 exposed two
 # legitimate parent-runner references. Preserve the successful 26885 V2
 # stage's complete replacement semantics, NEVER require a single occurrence.
 # Check observed exact parent cardinality; preserve all other stage bytes.
 anchors=(
  ('build_26884_iris_rawr.sh','build_26885_iris_rawr.sh'),
  ('generate_26884_build.py','generate_26885_build.py'),
  ('f8aff63b074ee6195d6b137858ad5a3f23cb149a40c9f72cb69b51f315b4679f',old_sha),
 )
 assert s.count(anchors[0][0])==2,('26885 V2 actual historical runner changed; check both references before replacing',s.count(anchors[0][0]))
 for before,after in anchors:
  assert before in s,('missing successful V2 mechanics reference',before)
  s=s.replace(before,after) # successful 26885 V2 used full replace, not once
 assert all(old not in s for old,_ in anchors),'unmigrated active mechanics reference'
 return s
edit('verify_successful_mechanics',mechanics)
def scope(s):
 s=s.replace('build_26884_iris_rawr.sh','build_26885_iris_rawr.sh').replace('generate_26884_build.py','generate_26885_build.py')
 assert 'build_26885_iris_rawr.sh' in s
 return s.replace('f8aff63b074ee6195d6b137858ad5a3f23cb149a40c9f72cb69b51f315b4679f',old_sha)
edit('verify_scope',scope)
# Recover real 26884 historical universe FROM 26885 compiled candidate by
# deterministic successful 26885 full-index rollback. Other old historical
# 26883/26882/26880 commands must then read their original correct bytes.
def historical(s):
 insert=''' local H84="$WORK/historical_26884_from_26885"
 cp -a "$BASE" "$H84";git -C "$H84" init -q
 (cd "$H84" && git apply --check --reverse "$ROOT/26885_FORWARD_FULL_INDEX.patch" &&
 git apply --reverse "$ROOT/26885_FORWARD_FULL_INDEX.patch" &&
 sha256sum -c "$ROOT/26885_BASE_26884_FULL_APP.sha256" >/dev/null) || fail 'exact successful 26885->26884 historical rollback failed'
'''
 s=once(s,' local H83="$WORK/historical_26883_from_26884"',insert+' local H83="$WORK/historical_26883_from_26884"')
 s=once(s,'cp -a "$BASE" "$H83"','cp -a "$H84" "$H83"')
 return s
edit('make_candidate',historical)
# Historical source hash predicates MUST never receive new 26886 bytes.
# Update source operand ONLY, NOT the old validators or compiler options.
def route_historical(s,name):
 # The historical variable must be quoted as a *complete* shell operand.
 # Exact failed Actions 40623130600 would create: "$H84 "$BASE".
 historic_var=('$H84' if name=='make_candidate' else '$WORK/historical_26884_from_26885')
 historic='"'+historic_var+'"'
 historic_app='"'+historic_var+'/app"'
 if name in ('make_candidate','compile_modified_runtime_shaders','clean_extract_replay'):
  lines=s.splitlines(keepends=True)
  matches=[i for i,x in enumerate(lines) if re.search(r'\bpython3 -S verify_26880_rawr_shader_universe\.py\b',x)]
  assert len(matches)==1,('26880 old real validator count',name,matches)
  i=matches[0]
  assert '"$BASE/app"' in lines[i],('unexpected 26885 V2 validator source binding',name,lines[i])
  lines[i]=lines[i].replace('"$BASE/app"',historic_app,1)
  s=''.join(lines)
 lines=s.splitlines(keepends=True)
 for i,line in enumerate(lines):
  if re.search(r'\b(?:python3 -S )?(?:verify_26884_|regressions/26884_)',line):
   lines[i]=line.replace('"$BASE"',historic).replace('"$exp"',historic)
 matches=[i for i,line in enumerate(lines)
          if 'python3 -S regressions/26885_actions_40604341240_historical_scope.py' in line]
 assert len(matches)==1,('expected one inherited 26885 historical CMake checker',name,matches)
 i=matches[0];line=lines[i]
 expected='"$BASE" "$exp"' if name=='clean_extract_replay' else '"$BASE" "$CAND"'
 assert expected in line,('historical CMake checker source changed',name,line)
 assert 'build_26886_iris_rawr.sh' in line,('historical CMake checker runner changed',name,line)
 line=line.replace(expected,historic+' "$BASE"',1)
 line=line.replace('build_26886_iris_rawr.sh','build_26885_iris_rawr.sh',1)
 import shlex
 parsed=shlex.split(line.strip())
 expected_args=['python3','-S','regressions/26885_actions_40604341240_historical_scope.py',
                historic_var,'$BASE','$ROOT/build_26885_iris_rawr.sh']
 assert parsed==expected_args,(name,'malformed historical validator invocation',parsed,expected_args)
 lines[i]=line
 return ''.join(lines)
for n in ('make_candidate','compile_modified_runtime_shaders','clean_extract_replay'):
 edit(n,lambda s,n=n:route_historical(s,n))
# The former 26885 standalone new shader controls have been renamed by the
# build-identity change to 26886. Add the ORIGINAL 26885 checks on real old
# 26884/26885 bytes, so they are NOT erased by successor validation.
def previous_source(s,stage):
 if stage=='make_candidate':
  z=''' python3 -S verify_26885_candidate.py "$H84" "$BASE"
 python3 -S verify_26885_semantics.py "$H84" "$BASE"
 python3 -S regressions/26885_chroma_controls.py "$BASE" "$H84"
 python3 -S verify_26885_expanded_glsl.py "$BASE"
 python3 -S regressions/26886_historical_scope_all_stages.py "$H84" "$BASE" "$CAND" "$ROOT/build_26885_iris_rawr.sh" "$ROOT/build_26886_iris_rawr.sh"'''
 elif stage=='compile_modified_runtime_shaders':
  z=''' python3 -S regressions/26885_chroma_controls.py "$BASE" "$WORK/historical_26884_from_26885"
 python3 -S verify_26885_expanded_glsl.py "$BASE" --compiler "$IRIS26864_GLSLANG" --spirv-val "$(command -v spirv-val)" --spirv-opt "$(command -v spirv-opt)" --out "$OUT/26886_historical_26885_chroma_spirv"
 python3 -S regressions/26886_historical_scope_all_stages.py "$WORK/historical_26884_from_26885" "$BASE" "$CAND" "$ROOT/build_26885_iris_rawr.sh" "$ROOT/build_26886_iris_rawr.sh"'''
 else:
  z=''' python3 -S verify_26885_candidate.py "$WORK/historical_26884_from_26885" "$BASE"
 python3 -S verify_26885_semantics.py "$WORK/historical_26884_from_26885" "$BASE"
 python3 -S regressions/26885_chroma_controls.py "$BASE" "$WORK/historical_26884_from_26885"
 python3 -S verify_26885_expanded_glsl.py "$BASE"
 python3 -S regressions/26886_historical_scope_all_stages.py "$WORK/historical_26884_from_26885" "$BASE" "$exp" "$ROOT/build_26885_iris_rawr.sh" "$ROOT/build_26886_iris_rawr.sh"'''
 return append(s,z)
for n in ('make_candidate','compile_modified_runtime_shaders','clean_extract_replay'):
 edit(n,lambda s,n=n:previous_source(s,n))
# Prior 26885 V2 compiler, language, native CMake, freeze and assemble commands
# cannot be edited beyond required version label replacement.
for n in ('prepare_glslang','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','assemble','postbuild_proof'):
 assert stage_text(body,n)==stage_text(original.replace('26885','26886').replace('0.9726885','0.9726886'),n),('protected core stage changed',n)
# The new 26886 package still does all strictly required real shader gates;
# the 26885 V2 failure's original 26880 source never changes.
def package(s):
 # The inherited package counted EIGHT 26885 handoff files; successor has TWO.
 # This is an identity/scope update only, not relaxation of the allowlist.
 s=s.replace('-eq 8 ]]','-eq 2 ]]').replace('8-file','2-file').replace('8-source','2-source')
 # Real 26886 trigger is unchanged V1 plus a repair nonce. Do not let the
 # previous 26885 V2 *caption* become the 26886 trigger token.
 s=s.replace('RUN_26886_B_ON_WRONSKI_RGB_CHROMA_CONSISTENCY_V2_SCOPE_REPAIR',
             'RUN_26886_B_ON_WRONSKI_CHROMA_NOISE_ALIAS_V1')
 # Inherited 26885 *package checks* are historical validators, not current
 # 26886 validators. Restore them exactly, then append 26886 scope checks.
 old_current=''' python3 -S -m py_compile verify_26886_candidate.py verify_26886_patches.py verify_26886_expanded_glsl.py verify_26886_semantics.py stage_26886_root.py regressions/26886_successor_contract.py regressions/26886_chroma_controls.py
 python3 -S stage_26886_root.py
 python3 -S regressions/26886_successor_contract.py
'''
 historic=''' python3 -S -m py_compile verify_26885_candidate.py verify_26885_patches.py verify_26885_expanded_glsl.py verify_26885_semantics.py stage_26885_root.py regressions/26885_successor_contract.py regressions/26885_chroma_controls.py
 python3 -S stage_26885_root.py
 python3 -S regressions/26885_successor_contract.py
'''
 assert s.count(old_current)==1,('renamed prior 26885 package checks expected once',s.count(old_current))
 assert historic in stage_text(original,'verify_package'),'prior 26885 V2 historical package checks must be exact'
 s=s.replace(old_current,historic,1)
 assert "python3 -S stage_26885_root.py" in s
 return append(s,''' python3 -S stage_26886_root.py
 python3 -S -m py_compile generate_26886_build.py stage_26886_root.py verify_26886_candidate.py verify_26886_patches.py verify_26886_expanded_glsl.py verify_26886_semantics.py regressions/26886_chroma_controls.py regressions/26886_successor_contract.py regressions/26886_historical_scope_all_stages.py
 python3 -S regressions/26886_successor_contract.py
''')
edit('verify_package',package)
def safety(s):
 s=s.replace('runtime_changed_files=8 (7 changed native B Super Res ON files incl one NEW shader, plus version); 2002 protected, Spektra/white/B OFF/DNG/UHDR unchanged','runtime_changed_files=2 (one B Super Res ON existing chroma-guide shader, plus version); 2008 protected, Spektra/white/B OFF/DNG/UHDR unchanged')
 s=s.replace('runtime_changed_files=8','runtime_changed_files=2').replace('prior_files=2009','prior_files=2010').replace('protected_source=2002','protected_source=2008').replace('8-file','2-file')
 return s.replace('candidate_files=2010','candidate_files=2010')
edit('prebuild_safety',safety)
def patches(s):
 return s.replace('8-file','2-file')
edit('verify_candidate_patches',patches)
# Stage ordering and old successful compiler command invariants cannot drift.
get=lambda s:[m.group(1) for m in re.finditer(r'\n([a-z_]+)\(\)\{',s)]
assert get(original)==get(body) and [n for n in get(body) if n in STAGES]==list(STAGES)
for command in ('./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace'):
 assert command in original and command in body,('real compiler or full APK build absent',command)
assert 'GLSLANG_VERSION="16.5.0"' in body and 'PRE-BUILD SAFETY PROOF PASSED' in body
for stage in ('make_candidate','compile_modified_runtime_shaders','clean_extract_replay'):
 s=stage_text(body,stage)
 calls=[line for line in s.splitlines() if 'python3 -S verify_26880_rawr_shader_universe.py' in line]
 assert len(calls)==1 and ('"$H84/app"' if stage=='make_candidate' else '"$WORK/historical_26884_from_26885/app"') in calls[0],(stage,'historical 26880 hash-scope regression',calls)
 assert 'regressions/26886_historical_scope_all_stages.py' in s
 # No sealed 26884/26885 source predicate may silently read the 26886
 # candidate (or current final export) after renaming a historical runner.
 for line in s.splitlines():
  if 'python3 -S verify_26884_' in line or 'python3 -S regressions/26884_' in line:
   assert '"$BASE"' not in line and '"$CAND"' not in line and '"$exp"' not in line,(stage,'26884 historical-domain leak',line)
  if 'python3 -S regressions/26885_chroma_controls.py' in line:
   assert '"$CAND"' not in line and '"$exp"' not in line,(stage,'26885 chroma regression rebound to 26886',line)
 legacy=[line for line in s.splitlines() if 'python3 -S regressions/26885_actions_40604341240_historical_scope.py' in line]
 assert len(legacy)==1,(stage,'historical 26885 CMake regression missing or duplicate',legacy)
 expected='"$H84" "$BASE"' if stage=='make_candidate' else '"$WORK/historical_26884_from_26885" "$BASE"'
 assert expected in legacy[0] and '"$ROOT/build_26885_iris_rawr.sh"' in legacy[0],(stage,legacy[0])
assert 'verify_26886_expanded_glsl.py "$CAND" --compiler "$IRIS26864_GLSLANG"' in body
pkg=stage_text(body,'verify_package')
assert 'RUN_26886_B_ON_WRONSKI_CHROMA_NOISE_ALIAS_V1' in pkg
assert 'RUN_26886_B_ON_WRONSKI_RGB_CHROMA_CONSISTENCY_V2_SCOPE_REPAIR' not in pkg
assert pkg.count('python3 -S stage_26885_root.py')==1
assert pkg.count('python3 -S stage_26886_root.py')==1
assert pkg.index('python3 -S stage_26885_root.py') < pkg.index('python3 -S stage_26886_root.py')
assert 'python3 -S regressions/26885_successor_contract.py' in pkg
assert 'verify_26886_candidate.py' in body and 'verify_26886_patches.py' in body
(R/'build_26886_iris_rawr.sh').write_text(body)
newhash=hashlib.sha256(body.encode()).hexdigest()
(R/'26886_GENERATED_BUILD_SHA256.txt').write_text(newhash+'  build_26886_iris_rawr.sh\n')
(R/'26886_BUILD_INFRASTRUCTURE_DIFF.txt').write_text(''.join(difflib.unified_diff(original.splitlines(True),body.splitlines(True),fromfile='ACTUAL_SUCCESSFUL_26885_SHA_'+old_sha,tofile='26886_INHERITED_17_STAGES')))
print('PASS 26886 successor EXACT successful 26885 V2 17 stages; prior',old_sha,'new',newhash)
