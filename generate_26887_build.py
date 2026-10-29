#!/usr/bin/env python3
"""26887 successor, ONLY from exact successful 26886 17-stage runner.

Fail closed on unavailable 26886 runner. Inherit compiler, native and full
assemble stages, changing identity only; append 26887 candidate, shader,
patch, historical and package checks in established stages.
DO NOT call this validator or output build-proven until its exact generated
commands are replayed on successful historical and frozen candidate bytes.
"""
from pathlib import Path
import hashlib, re, sys, difflib
R=(Path(sys.argv[1]) if len(sys.argv)>1 else Path('.')).resolve()
parent=R/'build_26886_iris_rawr.sh'
assert parent.is_file(), 'missing EXACT GitHub-successful 26886 generated runner'
original=parent.read_text()
old_sha=hashlib.sha256(original.encode()).hexdigest()
assert old_sha=='3f816088f564bfd575d5dc8e1681b9b1b18ec435de41ed34f2c22df866c5e8fa',('26886 successful runner mismatch',old_sha)
STAGES=('verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay')
stage_re=re.compile(r'\n([a-z_]+)\(\)\{')
stages=lambda src:stage_re.findall(src)
assert [x for x in stages(original) if x in STAGES]==list(STAGES)
body=original.replace('26886','26887').replace('0.9726886','0.9726887')

def stage(src,n):
 a=src.index('\n'+n+'(){')+1;b=src.index('\n}',a)+2
 return src[a:b]
def edit(n,fn):
 global body
 a=body.index('\n'+n+'(){')+1;b=body.index('\n}',a)+2
 before=body[a:b];after=fn(before)
 assert after.endswith('}') and after!=before,('stage unchanged',n)
 body=body[:a]+after+body[b:]
def append(s,cmd):
 assert s.endswith('\n}')
 return s[:-2]+'\n'+cmd.strip('\n')+'\n}'
def once(s,a,b):
 assert s.count(a)==1,('unexpected old anchor',a,s.count(a))
 return s.replace(a,b,1)

# Advance ONLY active runtime authority from the successful 26885 artifact to
# the proven 26886 V6 artifact and exact COMPILED-candidate TAR. Literal
# predecessor historical validator sources stay sealed and distinct.
for a,b in (
 ('REPO_SCAFFOLD_BASE_COMMIT="a46d0f7491a2c19b7d93ac69813f6b04073697cc"','REPO_SCAFFOLD_BASE_COMMIT="97bc96161da6854ef5fcaca16b2a1ae9c020f58d"'),
 ('RUNTIME_AUTHORITY_COMMIT="a46d0f7491a2c19b7d93ac69813f6b04073697cc"','RUNTIME_AUTHORITY_COMMIT="97bc96161da6854ef5fcaca16b2a1ae9c020f58d"'),
 ('RUNTIME_ARTIFACT_ID="12783521315"; RUNTIME_ACTIONS_RUN="40610009610"','RUNTIME_ARTIFACT_ID="12792447816"; RUNTIME_ACTIONS_RUN="40633283908"'),
 ('RUNTIME_ARTIFACT_SHA="a738a2fbd2bcc0f9d9031696b2bf6f64cc58232a23201bf7a650d9cee60d9988"','RUNTIME_ARTIFACT_SHA="1a2dbc35cf738be42270cb156b083015b323b3829cae67c3ab33e91de5831335"'),
 ('RUNTIME_TAR_SHA="0d87c877a0184d7679a832b0a0ada7dc0b5a65e53cbce31ab78beb28f3fe017f"','RUNTIME_TAR_SHA="e2a03925cafa2196884fff02d9320f6ac4020823130b896de7166eb77ded144b"'),
 ('MECHANICS_GIT_BLOB="8a0216fc6d8e1465517cd6a80b62645dbc544e38"','MECHANICS_GIT_BLOB="d043b05d58a3d63b8fb48af5fadde2e8a59712ba"'),
 ('ARTZIP="$WORK/26885_artifact.zip"; ARTDIR="$WORK/artifact_26885"','ARTZIP="$WORK/26886_artifact.zip"; ARTDIR="$WORK/artifact_26886"'),
 ('BASE="$WORK/exact_successful_26885_compiled_candidate"','BASE="$WORK/exact_successful_26886_compiled_candidate"'),
): body=once(body,a,b)

def authority(s):
 for a,b in (
  ("x['head_sha']=='a46d0f7491a2c19b7d93ac69813f6b04073697cc'","x['head_sha']=='97bc96161da6854ef5fcaca16b2a1ae9c020f58d'"),
  ("'id':12783521315","'id':12792447816"),
  ('photon-26885-b-on-wronski-rgb-chroma-consistency','photon-26886-b-on-rawr-chroma-denoise-false-color'),
  ('sha256:a738a2fbd2bcc0f9d9031696b2bf6f64cc58232a23201bf7a650d9cee60d9988','sha256:1a2dbc35cf738be42270cb156b083015b323b3829cae67c3ab33e91de5831335'),
  ('build_26885_iris_rawr_outputs/26885_candidate_app_source.tar.gz','build_26886_iris_rawr_outputs/26886_candidate_app_source.tar.gz'),
  ('build_26885_iris_rawr_outputs/26885_COMPILER_STATUS.txt','build_26886_iris_rawr_outputs/26886_COMPILER_STATUS.txt'),
  ('26887_BASE_26885_FULL_APP.sha256','26887_BASE_26886_FULL_APP.sha256'),
  ('26885_run.json','26886_run.json'),
  ('26885_artifact_metadata.json','26886_artifact_metadata.json'),
 ):
  assert a in s,('active authority missing',a)
  s=s.replace(a,b)
 # Prove real 26886 2010-file authority, not an old 26885 2010-file dump.
 assert 'build_26886_iris_rawr_outputs/26886_candidate_app_source.tar.gz' in s
 assert '26887_BASE_26886_FULL_APP.sha256' in s
 assert '-eq 2010' in s
 return s
edit('obtain_authority',authority)

# Historical 26886 V6 checker gets the actual previous 26885 universe,
# recovered from 26886 by deterministic rollback. Historical 26885 V2
# checkers retain their original 26884/26885 paths, never today's source.
def old_history(s):
 assert 'local H84="$WORK/historical_26884_from_26885"' in s
 prefix=''' local H85="$WORK/historical_26885_from_26886"
 cp -a "$BASE" "$H85"; git -C "$H85" init -q
 (cd "$H85" && git apply --check --reverse "$ROOT/26886_FORWARD_FULL_INDEX.patch" &&
 git apply --reverse "$ROOT/26886_FORWARD_FULL_INDEX.patch" &&
 sha256sum -c "$ROOT/26886_BASE_26885_FULL_APP.sha256" >/dev/null) || fail 'exact successful 26886->26885 historical rollback failed'
'''
 s=once(s,' local H84="$WORK/historical_26884_from_26885"',prefix+' local H84="$WORK/historical_26884_from_26885"')
 s=once(s,'cp -a "$BASE" "$H84"','cp -a "$H85" "$H84"')
 return s
edit('make_candidate',old_history)

# Refuse historical 26885 checker rebinding caused by treating today's
# successful 26886 BASE as the previously successful 26885 source.
for n in ('make_candidate','compile_modified_runtime_shaders','clean_extract_replay'):
 def guard_history(s,n=n):
  if n=='make_candidate':
   old='"$BASE"';new='"$H85"'
  else:
   old='"$BASE"';new='"$WORK/historical_26885_from_26886"'
  lines=s.splitlines(keepends=True)
  for i,line in enumerate(lines):
   if ('verify_26885_' in line or 'regressions/26885_' in line):
    # Do not reroute current 26887 predicate. Rebind ONLY historical 26885.
    lines[i]=line.replace(old,new)
  after=''.join(lines)
  assert after!=s,('no actual historical source rerouting',n)
  return after
 edit(n,guard_history)

# Maintain historical 26886 V6 predicates on their real 26885/26886
# source universes; they must never receive today's 26887 candidate.
for n in ('make_candidate','compile_modified_runtime_shaders','clean_extract_replay'):
 def v6_history(s,n=n):
  lines=[]
  for line in s.splitlines(keepends=True):
   if 'regressions/26887_historical_scope_all_stages.py' in line:
    line=line.replace('regressions/26887_historical_scope_all_stages.py',
                      'regressions/26886_historical_scope_all_stages.py')
    line=line.replace('"$ROOT/build_26887_iris_rawr.sh"',
                      '"$ROOT/build_26886_iris_rawr.sh"')
    if n=='make_candidate':
     line=line.replace('"$H84" "$BASE" "$CAND"', '"$H84" "$H85" "$BASE"')
    else:
     line=line.replace('"$WORK/historical_26884_from_26885" "$BASE" "$CAND"',
                       '"$WORK/historical_26884_from_26885" "$WORK/historical_26885_from_26886" "$BASE"')
     line=line.replace('"$WORK/historical_26884_from_26885" "$BASE" "$exp"',
                       '"$WORK/historical_26884_from_26885" "$WORK/historical_26885_from_26886" "$BASE"')
   if 'regressions/26887_chroma_controls.py' in line:
    line=line.replace('regressions/26887_chroma_controls.py','regressions/26886_chroma_controls.py')
    if n=='make_candidate':line=line.replace('"$BASE" "$CAND"','"$H85" "$BASE"')
    else:line=line.replace('"$BASE" "$CAND"','"$WORK/historical_26885_from_26886" "$BASE"').replace('"$BASE" "$exp"','"$WORK/historical_26885_from_26886" "$BASE"')
   lines.append(line)
  out=''.join(lines)
  assert 'regressions/26887_historical_scope_all_stages.py' not in out
  assert 'regressions/26887_chroma_controls.py' not in out
  if n=='make_candidate':
   hist=''' python3 -S verify_26886_candidate.py "$H85" "$BASE"
 python3 -S verify_26886_semantics.py "$H85" "$BASE"
 python3 -S verify_26886_expanded_glsl.py "$BASE"
 python3 -S verify_26886_patches.py "$H85" "$BASE" 26886_FORWARD_FULL_INDEX.patch 26886_ROLLBACK_FULL_INDEX.patch'''
  else:
   hist=''' python3 -S verify_26886_candidate.py "$WORK/historical_26885_from_26886" "$BASE"
 python3 -S verify_26886_semantics.py "$WORK/historical_26885_from_26886" "$BASE"
 python3 -S verify_26886_expanded_glsl.py "$BASE"'''
  return append(out,hist)
 edit(n,v6_history)

# Exact inherited successful 26886 mechanics name and SHA remain a hard gate.
# Previous successful renderer and all compiler/assemble shell commands must
# stay the same after identity-only conversion, notwithstanding new checks.
def mechanics(s):
 assert s.count('build_26885_iris_rawr.sh')==2,('26886 V6 V1 two-runner-anchor cardinality changed',s.count('build_26885_iris_rawr.sh'))
 assert 'generate_26885_build.py' in s
 return s.replace('build_26885_iris_rawr.sh','build_26886_iris_rawr.sh').replace('generate_26885_build.py','generate_26886_build.py').replace('2138db01cbfb3a8421c12e54ba29d4f0a893d1cdd4a219ee34a40a4dc0c54379',old_sha)
edit('verify_successful_mechanics',mechanics)

def package(s):
 # The exact original V6 package checks, historical validators, trigger and
 # V1–V5 regressions must remain on V6 bytes, NOT be renamed to V7.
 historical=stage(original,'verify_package')
 assert 'python3 -S stage_26886_root.py' in historical
 assert 'regressions/26886_successor_contract.py' in historical
 # Add the 26887 package beside the byte-identical original V6 checks.
 return append(historical,'''
 test -f TRIGGER_26887.txt
 grep -Fx 'RUN_26887_B_OFF_RAW_WITNESS_HDRQ_MOTION_V1' TRIGGER_26887.txt
 python3 -S stage_26887_root.py
 python3 -S -m py_compile generate_26887_build.py verify_26887_candidate.py verify_26887_semantics.py verify_26887_patches.py verify_26887_expanded_glsl.py stage_26887_root.py regressions/26887_successor_contract.py
 python3 -S regressions/26887_successor_contract.py''')
edit('verify_package',package)

def candidate(s):
 return append(s,''' python3 -S verify_26887_candidate.py "$BASE" "$CAND"
 python3 -S verify_26887_semantics.py "$BASE" "$CAND"
 python3 -S verify_26887_expanded_glsl.py "$CAND"''')
edit('make_candidate',candidate)

def shader(s):
 # Actual 40804993462 Stage 7 regression: inherited CURRENT 26887 validator
 # compiled 11 real SPIR-V variants, but its 26885-style grep looked for a
 # success sentence that the 26887 validator never emits. Keep the pinned
 # compiler command and its tee receipt, correcting ONLY the proof consumer.
 # Match the actual inherited 26885/V6 guard as a complete line, refusing
 # a changed callsite or a second guard rather than silently skipping either.
 lines=s.splitlines(keepends=True)
 failing=[i for i,line in enumerate(lines) if 'B ON real GLSL/SPIRV proof missing' in line]
 assert len(failing)==1,('40804993462 wrong number of inherited B-ON receipt guards',failing)
 i=failing[0]
 assert "grep -F 'PASS 26887 PINNED REAL GLSLANG 16.5.0 and SPIRV-VAL pre/post optimized'" in lines[i],('changed inherited receipt command',lines[i])
 assert '26887_new_chroma_pinned_shader.txt' in lines[i]
 assert s.count('26887_new_chroma_spirv')==1 and s.count('26887_new_chroma_pinned_shader.txt')==2,('current compiler output anchors changed',s.count('26887_new_chroma_spirv'),s.count('26887_new_chroma_pinned_shader.txt'))
 assert s.count('verify_26887_expanded_glsl.py "$CAND" --compiler')==1,('current real pinned 26887 compiler call count',s.count('verify_26887_expanded_glsl.py "$CAND" --compiler'))
 # The old verifier already compiles all eleven 26887 real SPIR-V variants;
 # DO NOT append a duplicate compiler invocation after its failing check.
 line=lines[i].replace('PASS 26887 PINNED REAL GLSLANG 16.5.0 and SPIRV-VAL pre/post optimized',
  'PASS pinned REAL glslang 16.5.0/spirv-val/spirv-opt 11 compiled 26887 shader variants')
 assert line!=lines[i] and "|| fail '26887 B ON real GLSL/SPIRV proof missing'" in line
 line=line.replace('26887 B ON real GLSL/SPIRV proof missing','26887 current shader real GLSL/SPIR-V proof missing')
 lines[i]=line
 s=''.join(lines)
 s=s.replace('26887_new_chroma_spirv','26887_modified_shader_spirv')
 s=s.replace('26887_new_chroma_pinned_shader.txt','26887_modified_shader_compile_receipt.txt')
 # Validate the precise compiled SPIR-V receipt, not just echoed stdout.
 proof=""" python3 -S - "$OUT/26887_modified_shader_spirv" <<'PY_26887_SHADER_RECEIPT'
import hashlib,pathlib,sys
p=pathlib.Path(sys.argv[1]); m=p/'26887_REAL_COMPILED_SHADER_SHA256.txt'
assert m.is_file(),('26887 real compiler manifest missing',m)
lines=m.read_text().splitlines()
assert len(lines)==11,('26887 wrong number of compiled shader variants',len(lines))
names=set()
for line in lines:
 h,sep,name=line.partition('  ')
 assert sep=='  ' and len(h)==64 and all(c in '0123456789abcdef' for c in h)
 assert name not in names and name.endswith('.spv') and '/' not in name and '..' not in name,(name,'duplicate or unsafe path')
 names.add(name); b=(p/name).read_bytes()
 assert len(b)>=84 and b[:4]==bytes.fromhex('03022307'),('26887 invalid SPIR-V',name)
 assert hashlib.sha256(b).hexdigest()==h,('26887 compiled SPIR-V hash drift',name)
assert len(list(p.glob('*.spv')))==11,('26887 additional/untracked SPIR-V')
print('PASS 26887 B ON actual pinned compiler receipt: 11 unique SPIR-V variants and byte-matched SHA-256')
PY_26887_SHADER_RECEIPT"""
 return append(s,proof)
edit('compile_modified_runtime_shaders',shader)

def patch(s):
 return append(s,''' python3 -S verify_26887_patches.py "$BASE" "$CAND" 26887_FORWARD_FULL_INDEX.patch 26887_ROLLBACK_FULL_INDEX.patch''')
edit('verify_candidate_patches',patch)

def clean(s):
 return append(s,''' python3 -S verify_26887_candidate.py "$BASE" "$exp"
 python3 -S verify_26887_semantics.py "$BASE" "$exp"
 python3 -S verify_26887_expanded_glsl.py "$exp"
 python3 -S verify_26887_patches.py "$BASE" "$exp" 26887_FORWARD_FULL_INDEX.patch 26887_ROLLBACK_FULL_INDEX.patch''')
edit('clean_extract_replay',clean)

# Update only current source counts: original 2010-file BASE is unchanged.
# 26887 candidate contains 2020 files and 17 intended changed paths.
def source_counts(s):
 s=s.replace('2-file','17-file').replace('2-source','17-source')
 s=s.replace('2008 protected','2003 protected').replace('protected_source=2008','protected_source=2003')
 s=s.replace('runtime_changed_files=2','runtime_changed_files=17')
 s=s.replace('candidate_files=2010','candidate_files=2020')
 return s
for n in ('verify_scope','verify_candidate_patches','prebuild_safety','postbuild_proof','clean_extract_replay'):
 a=body.index('\n'+n+'(){')+1;b=body.index('\n}',a)+2
 body=body[:a]+source_counts(body[a:b])+body[b:]

# Scope and authority receipts must advance to the successful V6 generator,
# not the 26885 predecessor. This is an active-owner update only: historical
# 26885 validators above stay pinned on their original universes.
def current_mechanics_scope(s):
 s=once(s,'$RUNTIME_AUTHORITY_COMMIT:generate_26885_build.py','$RUNTIME_AUTHORITY_COMMIT:generate_26886_build.py')
 s=once(s,'sha build_26885_iris_rawr.sh','sha build_26886_iris_rawr.sh')
 s=once(s,'2138db01cbfb3a8421c12e54ba29d4f0a893d1cdd4a219ee34a40a4dc0c54379','3f816088f564bfd575d5dc8e1681b9b1b18ec435de41ed34f2c22df866c5e8fa')
 return s
edit('verify_scope',current_mechanics_scope)

# Precisely recognize the already-committed, SHA-pinned runner-recovery workflow.
def recovered_runner_infrastructure(s):
 old=' diff -u 26887_REPOSITORY_UPLOAD_ALLOWLIST.txt <(git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | LC_ALL=C sort) >/dev/null || fail \'unexpected uploaded infrastructure/source file\''
 new=' [[ "$(git rev-parse HEAD:.github/workflows/recover-26886-runner.yml)" == \'0a03cd0d75b6ee3d70f8fe10d581789d396d7350\' ]] || fail \'exact successful 26886 runner-recovery workflow changed or missing\'\n diff -u <( { cat 26887_REPOSITORY_UPLOAD_ALLOWLIST.txt; printf \'%s\\n\' \'.github/workflows/recover-26886-runner.yml\'; } | LC_ALL=C sort) <(git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | LC_ALL=C sort) >/dev/null || fail \'unexpected uploaded infrastructure/source file including exact runner recovery\''
 assert s.count(old)==1,("repository scope anchor drift",s.count(old))
 return s.replace(old,new,1)
edit('verify_scope',recovered_runner_infrastructure)

# Rename stale ACTIVE authority labels; preserve historical commands/receipts.
def current_scope_labels(s):
 for a,b in (
  ("fail '26876 authority not ancestor'", "fail '26886 authority not ancestor'"),
  ("fail 'successful 26878 mechanics generator blob mismatch'", "fail 'successful 26886 mechanics generator blob mismatch'"),
  ("fail 'successful 26878 17-stage source script drift'", "fail 'successful 26886 17-stage source script drift'"),
  ("pass '26887 branch/HEAD, exact successful 26878 build and strict no-live-source/upload scope'", "pass '26887 branch/HEAD, exact successful 26886 V6 mechanics and strict no-live-source/upload scope'"),
 ): s=once(s,a,b)
 return s
edit('verify_scope',current_scope_labels)
body=once(body,'# Successful 26874 Actions compiled candidate is runtime authority.','# Successful 26886 V6 Actions compiled candidate is runtime authority.')
body=once(body,'# Keep successful 26874 17-stage verification mechanics unchanged by default.','# Keep successful 26886 V6 17-stage verification mechanics unchanged by default.')

def current_authority_receipt(s):
 s=once(s,'mechanics_generated_script_sha256=2138db01cbfb3a8421c12e54ba29d4f0a893d1cdd4a219ee34a40a4dc0c54379','mechanics_generated_script_sha256=3f816088f564bfd575d5dc8e1681b9b1b18ec435de41ed34f2c22df866c5e8fa')
 s=s.replace('26885 prior compiler authority','26886 prior compiler authority').replace('26885 successful','26886 successful').replace('26885 authority','26886 authority').replace('successful 26885','successful 26886').replace('not successful 26885','not successful 26886')
 return s
edit('obtain_authority',current_authority_receipt)

def current_safety_receipt(s):
 s=s.replace('successful 26885','successful 26886')
 s=s.replace('one B Super Res ON existing chroma-guide shader, plus version','7 modified existing files (including version), 10 new B-only runtime files')
 s=s.replace('Spektra/white/B OFF/DNG/UHDR unchanged','Spektra/DNG/UHDR and non-B owners unchanged')
 s=s.replace('Spektra/RAW white/B OFF/A/Motion/Night/LONG/DNG/UHDR preserved','Spektra/A/A+B/Night/LONG/DNG/UHDR protected, B OFF intended changes')
 return s
edit('prebuild_safety',current_safety_receipt)

# All 17 inherited stage declarations and real project commands remain.
assert stages(original)==stages(body)
assert [x for x in stages(body) if x in STAGES]==list(STAGES)
for n in ('prepare_glslang','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','assemble','postbuild_proof'):
 assert stage(body,n)==stage(original,n).replace('26886','26887').replace('0.9726886','0.9726887'),('inherited compiler/freeze/assemble stage altered',n)
for cmd in ('./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace'):
 assert cmd in original and cmd in body
assert 'GLSLANG_VERSION="16.5.0"' in body and 'PRE-BUILD SAFETY PROOF PASSED' in body
for n in ('make_candidate','compile_modified_runtime_shaders','clean_extract_replay'):
 assert 'verify_26887_expanded_glsl.py' in stage(body,n)
assert stage(body,'compile_modified_runtime_shaders').count('verify_26887_expanded_glsl.py "$CAND" --compiler')==1
assert 'PASS pinned REAL glslang 16.5.0/spirv-val/spirv-opt 11 compiled 26887 shader variants' in stage(body,'compile_modified_runtime_shaders')
assert '26887_REAL_COMPILED_SHADER_SHA256.txt' in stage(body,'compile_modified_runtime_shaders')
assert 'PY_26887_SHADER_RECEIPT' in stage(body,'compile_modified_runtime_shaders')
assert stage(body,'compile_modified_runtime_shaders').count('26887_modified_shader_spirv')==2, 'current shader output directory must appear in compiler and receipt validator'
assert '0a03cd0d75b6ee3d70f8fe10d581789d396d7350' in stage(body,'verify_scope')
assert 'verify_26887_patches.py "$BASE" "$CAND" 26887_FORWARD_FULL_INDEX.patch 26887_ROLLBACK_FULL_INDEX.patch' in body
assert 'verify_26887_patches.py "$BASE" "$exp" 26887_FORWARD_FULL_INDEX.patch 26887_ROLLBACK_FULL_INDEX.patch' in body
assert 'RUNTIME_TAR_SHA="e2a03925cafa2196884fff02d9320f6ac4020823130b896de7166eb77ded144b"' in body
assert '\"$H84 $BASE\"' not in body and '\"$H84 \"$BASE\"' not in body,'V2 malformed historical quoting'
assert 'build_26886_iris_rawr_outputs/26886_candidate_app_source.tar.gz' in stage(body,'obtain_authority')
assert 'build_26886_iris_rawr_outputs/26886_COMPILER_STATUS.txt' in stage(body,'obtain_authority')
assert '26887_BASE_26886_FULL_APP.sha256' in stage(body,'obtain_authority')
assert '-eq 2010' in stage(body,'obtain_authority')
assert 'regressions/26887_historical_scope_all_stages.py' not in body
assert 'regressions/26887_chroma_controls.py' not in body
out=R/'build_26887_iris_rawr.sh';out.write_text(body)
new_sha=hashlib.sha256(body.encode()).hexdigest()
(R/'26887_GENERATED_BUILD_SHA256.txt').write_text(new_sha+'  '+out.name+'\n')
(R/'26887_BUILD_INFRASTRUCTURE_DIFF.txt').write_text(''.join(difflib.unified_diff(original.splitlines(True),body.splitlines(True),fromfile='SUCCESSFUL_26886_SHA_'+old_sha,tofile='26887_SUCCESSOR_17_STAGES')))
print('PASS generated 26887 exact-successful-26886 parent SHA, inherited 17 stage order; new',new_sha)
# 26887 V4 trigger repair: retain generated runner bytes; touch this watched generator on the same push as workflow self-path activation.
