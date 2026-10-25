#!/usr/bin/env python3
"""26878: inherit exact successful 26877 guarded 17-stage mechanics.
Only version, runtime authority, strict five-file ownership and permanent regressions advance.
"""
import hashlib,re,difflib,sys
from pathlib import Path
P=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path('.').resolve()
prior=(P/'build_26877_iris_rawr.sh').read_text()
PARENT_SHA='bbda162004a0aa4b262a3df3547c47601df5ccb93cfb966a2dbd0a78a09e7dff'
PARENT_GIT_BLOB='eb6bdf755a9c8a080746f9f9a175a450d644bfa6'
assert hashlib.sha256(prior.encode()).hexdigest()==PARENT_SHA, 'exact successful 26877 17-stage runner mismatch'
body=prior.replace('26877','26878').replace('0.9726877','0.9726878')
def edit(name,fun):
 global body
 a=body.index('\n'+name+'(){')+1;b=body.index('\n}',a)+2
 old=body[a:b];new=fun(old)
 assert new!=old,(name,'no change')
 body=body[:a]+new+body[b:]
def one(s,old,new):
 assert s.count(old)==1,(old,s.count(old))
 return s.replace(old,new,1)
for old,new in (
 ('REPO_SCAFFOLD_BASE_COMMIT="23cb092331c7ba71f8dd52373357663054789784"','REPO_SCAFFOLD_BASE_COMMIT="42bbcd628f80c1bd9a0a80e7b1d4b7fee8fabf85"'),
 ('RUNTIME_AUTHORITY_COMMIT="23cb092331c7ba71f8dd52373357663054789784"','RUNTIME_AUTHORITY_COMMIT="42bbcd628f80c1bd9a0a80e7b1d4b7fee8fabf85"'),
 ('RUNTIME_ARTIFACT_ID="12572550739"; RUNTIME_ACTIONS_RUN="40122514448"','RUNTIME_ARTIFACT_ID="12577917317"; RUNTIME_ACTIONS_RUN="40137408646"'),
 ('RUNTIME_ARTIFACT_SHA="f057f62e69325acfc5d87b743dc52609138995e2df8d85423101842cf9776336"','RUNTIME_ARTIFACT_SHA="f9777891ec0a6476e4bbd3c56b755b050e15bc5270309eb97f1463b015768a98"'),
 ('RUNTIME_TAR_SHA="c377625dba427dfe7506dcb8c3414e948e043a842b4df67657a5804ef5b2e7a1"','RUNTIME_TAR_SHA="375f8a4a4f79e16d4b47a3191525b83b811e17406fdf6cae5d1fb53e61ee84b4"'),
 ('MECHANICS_GIT_BLOB="7ac7ffe6ff0e8d6fce47060676c0b9531b8b77d4"',f'MECHANICS_GIT_BLOB="{PARENT_GIT_BLOB}"'),
 ('ARTZIP="$WORK/26876_artifact.zip"; ARTDIR="$WORK/artifact_26876"','ARTZIP="$WORK/26877_artifact.zip"; ARTDIR="$WORK/artifact_26877"'),
 ('BASE="$WORK/exact_successful_26876_compiled_candidate"','BASE="$WORK/exact_successful_26877_compiled_candidate"'),
):body=one(body,old,new)

def pack(s):
 s=one(s,"-eq 4 ]] || fail","-eq 5 ]] || fail")
 s=s.replace('four-file','five-file').replace('4-file','5-file').replace('successful 26876','successful 26877')
 s=s.replace('RUN_26878_B_SR_OWNER_SPEKTRA_VIEWPORT_V1','RUN_26878_B_SR_GUIDE_SPEKTRA_FULL_ACTIVE_V1')
 s=s.replace('regressions/26878_runtime_ownership_spektra.py','regressions/26878_runtime_ownership_spektra.py regressions/26877_runtime_ownership_spektra.py')
 return s
edit('verify_package',pack)

def scope(s):
 s=s.replace('$RUNTIME_AUTHORITY_COMMIT:generate_26876_build.py','$RUNTIME_AUTHORITY_COMMIT:generate_26877_build.py')
 s=s.replace('build_26876_iris_rawr.sh','build_26877_iris_rawr.sh')
 s=s.replace('525ce763e63ae2b8aa0a9a27d1da810e8969d855ea930552e45976d741c3b912',PARENT_SHA)
 s=s.replace('successful 26876','successful 26877')
 return s
edit('verify_scope',scope)

def authority(s):
 # This stage alone advances the last successful artifact source from 26876 to 26877.
 s=s.replace('26876','26877')
 s=s.replace("'id':12572550739","'id':12577917317")
 s=s.replace("'name':'photon-26876-b-true50mp-wronski-fast'","'name':'photon-26877-b-sr-owner-spektra-viewfinder'")
 s=s.replace("'name':'photon-26877-b-true50mp-wronski-fast'","'name':'photon-26877-b-sr-owner-spektra-viewfinder'")
 s=s.replace('sha256:f057f62e69325acfc5d87b743dc52609138995e2df8d85423101842cf9776336','sha256:f9777891ec0a6476e4bbd3c56b755b050e15bc5270309eb97f1463b015768a98')
 s=s.replace('mechanics_generated_script_sha256=3b48818fd6cd6376f97cecca5a34b85ce4788e10a37435e3273beb2eddf3282a',f'mechanics_generated_script_sha256={PARENT_SHA}')
 assert all(x in s for x in ['12577917317','photon-26877-b-sr-owner-spektra-viewfinder','build_26877_iris_rawr_outputs/26877_candidate_app_source.tar.gz'])
 assert '12572550739' not in s
 return s
edit('obtain_authority',authority)

def candidate(s):
 # Reconstruct 26876 from the REAL compiled 26877 source, before inheriting
 # all prior candidate-universe rollback/replay gates without reordering.
 marker='local H75="$WORK/historical_26875_from_26876"'
 assert marker in s
 intro='''local H76="$WORK/historical_26876_from_26877"
 cp -a "$BASE" "$H76";git -C "$H76" init -q
 (cd "$H76" && git apply --check --reverse "$ROOT/26877_FORWARD_FULL_INDEX.patch" &&
  git apply --reverse "$ROOT/26877_FORWARD_FULL_INDEX.patch" &&
  sha256sum -c "$ROOT/26877_BASE_26876_FULL_APP.sha256" >/dev/null) || fail 'real 26877->26876 rollback failed'
 '''
 s=one(s,marker,intro+marker)
 s=one(s,'cp -a "$BASE" "$H75"','cp -a "$H76" "$H75"')
 s=one(s,'regressions/26876_superres_ownership.py "$H75" "$BASE"', 'regressions/26876_superres_ownership.py "$H75" "$H76"')
 s=one(s,'regressions/26878_runtime_ownership_spektra.py "$BASE" "$CAND"',
 '''regressions/26877_runtime_ownership_spektra.py "$H76" "$BASE"
 python3 -S regressions/26878_runtime_ownership_spektra.py "$BASE" "$CAND"''')
 assert 'verify_26878_candidate.py "$BASE" "$CAND"' in s
 return s
edit('make_candidate',candidate)

def mechanics(s):
 s=s.replace('build_26876_iris_rawr.sh','build_26877_iris_rawr.sh')
 s=s.replace('$RUNTIME_AUTHORITY_COMMIT:generate_26876_build.py','$RUNTIME_AUTHORITY_COMMIT:generate_26877_build.py')
 s=s.replace('525ce763e63ae2b8aa0a9a27d1da810e8969d855ea930552e45976d741c3b912',PARENT_SHA)
 s=s.replace('successful 26876','successful 26877')
 return s
edit('verify_successful_mechanics',mechanics)

def patch_stage(s):
 s=s.replace('exact 26878 3-file binary','exact 26878 5-file binary')
 return s
edit('verify_candidate_patches',patch_stage)

def safety(s):
 s=s.replace('runtime_changed_files=4','runtime_changed_files=5')
 s=s.replace('only B 1x RGB/clip lifetime + Spektra surface geometry + guarded version',
             'only B 1x RGB/clip bridge and EXIF + Spektra full-active preview and native surface extent + version')
 s=s.replace('1997 files byte-identical to successful 26876','1996 files byte-identical to successful 26877')
 s=s.replace('successful 26876','successful 26877')
 return s
edit('prebuild_safety',safety)

def replay(s):
 s=s.replace('regressions/26876_superres_ownership.py "$WORK/historical_26875_from_26876" "$BASE"',
             'regressions/26876_superres_ownership.py "$WORK/historical_26875_from_26876" "$WORK/historical_26876_from_26877"')
 s=s.replace('regressions/26878_runtime_ownership_spektra.py "$BASE" "$exp"',
             '''regressions/26877_runtime_ownership_spektra.py "$WORK/historical_26876_from_26877" "$BASE"
 python3 -S regressions/26878_runtime_ownership_spektra.py "$BASE" "$exp"''')
 s=s.replace('verify_26878_candidate.py verify_26878_patches.py regressions/26878_runtime_ownership_spektra.py',
             'verify_26878_candidate.py verify_26878_patches.py regressions/26877_runtime_ownership_spektra.py regressions/26878_runtime_ownership_spektra.py')
 assert 'regressions/26877_runtime_ownership_spektra.py "$WORK/historical_26876_from_26877" "$BASE"' in s
 return s
edit('clean_extract_replay',replay)
# Fail generation before build if any referenced successor validator is absent.
refs=set(re.findall(r'(?<![A-Za-z0-9_./])(?:regressions/)?[A-Za-z0-9_]*26878[A-Za-z0-9_]*\.py\b',body))
required={'verify_26878_candidate.py','verify_26878_patches.py','regressions/26878_runtime_ownership_spektra.py'}
assert required<=refs,(required-refs,refs)
for rel in refs|{'regressions/26877_runtime_ownership_spektra.py'}:
 assert (P/rel).is_file(),('missing source referenced by generated runner',rel)
assert 'regressions/26877_runtime_ownership_spektra.py "$WORK/historical_26876_from_26877" "$BASE"' in body
assert 'regressions/26878_runtime_ownership_spektra.py "$BASE" "$exp"' in body
# Full inherited 17-stage verification mechanics and actual real compilers fixed.
stages=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay']
def names(src):return [x.group(1) for x in re.finditer(r'\n([a-z_]+)\(\)\{',src)]
assert names(prior)==names(body) and [x for x in names(body) if x in stages]==stages
for cmd in ('./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace'):
 assert cmd in prior and cmd in body,('inherited real compiler replaced',cmd)
for m in ('GLSLANG_VERSION="16.5.0"','PRE-BUILD SAFETY PROOF PASSED','snapshot_live_authority_seeded','verify_26878_candidate.py "$BASE" "$CAND"','RUNTIME_ARTIFACT_ID="12577917317"','VERSION_NAME="0.9726878"','runtime_changed_files=5'):
 assert m in body,m
assert 'regressions/26877_superres_ownership.py' not in body
(P/'build_26878_iris_rawr.sh').write_text(body)
(P/'26878_BUILD_INFRASTRUCTURE_DIFF.txt').write_text(''.join(difflib.unified_diff(prior.splitlines(True),body.splitlines(True),fromfile='exact_successful_26877_17_stage_runner',tofile='26878_inherited_17_stage_runner')))
(P/'26878_GENERATED_BUILD_SHA256.txt').write_text(hashlib.sha256(body.encode()).hexdigest()+'  build_26878_iris_rawr.sh\n')
print('PASS 26878 inherits EXACT successful 26877 17-stage real compiler & assemble mechanics; runner sha256',hashlib.sha256(body.encode()).hexdigest())
