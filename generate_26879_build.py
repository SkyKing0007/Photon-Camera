#!/usr/bin/env python3
# 26879 exact successful 26878 guarded 17-stage mechanics, strict 5-file successor.
# No static mock replaces a language/native compiler or the real artifact replay.
from pathlib import Path
import hashlib,re,difflib,sys
P=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path('.').resolve()
prior=(P/'build_26878_iris_rawr.sh').read_text()
PARENT_SHA='53e570e4cc92ef5050f5f15953dd0fba88ec41cc2707c5eb79f1bc5994a531bb'
PARENT_GIT_BLOB='567d6e22d2100aac80e7bfd2c992340323958354'
assert hashlib.sha256(prior.encode()).hexdigest()==PARENT_SHA, 'not the exact successful 26878 17-stage runner'
body=prior.replace('26878','26879').replace('0.9726878','0.9726879')
def edit(name,fn):
 global body
 a=body.index('\n'+name+'(){')+1;b=body.index('\n}',a)+2
 old=body[a:b];new=fn(old)
 assert new!=old,(name,'unchanged')
 body=body[:a]+new+body[b:]
def one(s,old,new):
 assert s.count(old)==1,(old,s.count(old))
 return s.replace(old,new,1)
for old,new in (
 ('REPO_SCAFFOLD_BASE_COMMIT="42bbcd628f80c1bd9a0a80e7b1d4b7fee8fabf85"','REPO_SCAFFOLD_BASE_COMMIT="9318391f2da8a8a2ab92a3e85e3c01cb6533a55f"'),
 ('RUNTIME_AUTHORITY_COMMIT="42bbcd628f80c1bd9a0a80e7b1d4b7fee8fabf85"','RUNTIME_AUTHORITY_COMMIT="9318391f2da8a8a2ab92a3e85e3c01cb6533a55f"'),
 ('RUNTIME_ARTIFACT_ID="12577917317"; RUNTIME_ACTIONS_RUN="40137408646"','RUNTIME_ARTIFACT_ID="12586138690"; RUNTIME_ACTIONS_RUN="40160908258"'),
 ('RUNTIME_ARTIFACT_SHA="f9777891ec0a6476e4bbd3c56b755b050e15bc5270309eb97f1463b015768a98"','RUNTIME_ARTIFACT_SHA="254c63008636c721005dae80b4e4b9fffaf6252ac67a32f87f3238a1a0cec29d"'),
 ('RUNTIME_TAR_SHA="375f8a4a4f79e16d4b47a3191525b83b811e17406fdf6cae5d1fb53e61ee84b4"','RUNTIME_TAR_SHA="e3337188adc91ef89741dbe96f8384049304144cc9a358e8146631934149e849"'),
 ('MECHANICS_GIT_BLOB="eb6bdf755a9c8a080746f9f9a175a450d644bfa6"',f'MECHANICS_GIT_BLOB="{PARENT_GIT_BLOB}"'),
 ('ARTZIP="$WORK/26877_artifact.zip"; ARTDIR="$WORK/artifact_26877"','ARTZIP="$WORK/26878_artifact.zip"; ARTDIR="$WORK/artifact_26878"'),
 ('BASE="$WORK/exact_successful_26877_compiled_candidate"','BASE="$WORK/exact_successful_26878_compiled_candidate"'),
):body=one(body,old,new)
# Keep original 17-stage order. Only new authority/version and checks are amended.
def package(s):
 s=one(s,"regressions/26879_runtime_ownership_spektra.py regressions/26877_runtime_ownership_spektra.py",
       "regressions/26879_runtime_ownership_spektra.py regressions/26878_runtime_ownership_spektra.py regressions/26877_runtime_ownership_spektra.py")
 return s.replace('RUN_26879_B_SR_GUIDE_SPEKTRA_FULL_ACTIVE_V1','RUN_26879_B_50MP_NEON_SPEKTRA_FOV_V1')
edit('verify_package',package)
def scope(s):
 s=s.replace('generate_26877_build.py','generate_26878_build.py').replace('build_26877_iris_rawr.sh','build_26878_iris_rawr.sh')
 s=s.replace('bbda162004a0aa4b262a3df3547c47601df5ccb93cfb966a2dbd0a78a09e7dff',PARENT_SHA)
 return s.replace('successful 26877','successful 26878')
edit('verify_scope',scope)
def authority(s):
 s=s.replace('26877','26878')
 s=s.replace("'id':12577917317","'id':12586138690")
 s=s.replace("'name':'photon-26878-b-sr-owner-spektra-viewfinder'","'name':'photon-26878-b-sr-guide-spektra-full-active'")
 s=s.replace('sha256:f9777891ec0a6476e4bbd3c56b755b050e15bc5270309eb97f1463b015768a98','sha256:254c63008636c721005dae80b4e4b9fffaf6252ac67a32f87f3238a1a0cec29d')
 s=s.replace('mechanics_generated_script_sha256=bbda162004a0aa4b262a3df3547c47601df5ccb93cfb966a2dbd0a78a09e7dff','mechanics_generated_script_sha256='+PARENT_SHA)
 assert '12586138690' in s and 'photon-26878-b-sr-guide-spektra-full-active' in s
 return s
edit('obtain_authority',authority)
def candidate(s):
 marker='local H76="$WORK/historical_26876_from_26877"'
 assert marker in s
 intro='''local H77="$WORK/historical_26877_from_26878"
 cp -a "$BASE" "$H77";git -C "$H77" init -q
 (cd "$H77" && git apply --check --reverse "$ROOT/26878_FORWARD_FULL_INDEX.patch" &&
  git apply --reverse "$ROOT/26878_FORWARD_FULL_INDEX.patch" &&
  sha256sum -c "$ROOT/26878_BASE_26877_FULL_APP.sha256" >/dev/null) || fail 'real 26878->26877 rollback failed'
 '''
 s=one(s,marker,intro+marker)
 s=one(s,'cp -a "$BASE" "$H76"','cp -a "$H77" "$H76"')
 s=one(s,'regressions/26877_runtime_ownership_spektra.py "$H76" "$BASE"',
       '''regressions/26877_runtime_ownership_spektra.py "$H76" "$H77"
 python3 -S regressions/26878_runtime_ownership_spektra.py "$H77" "$BASE"''')
 s=one(s,'regressions/26879_runtime_ownership_spektra.py "$BASE" "$CAND"',
       'regressions/26879_runtime_ownership_spektra.py "$BASE" "$CAND"') if 'regressions/26879_runtime_ownership_spektra.py "$BASE" "$CAND"' in s else s
 assert 'regressions/26878_runtime_ownership_spektra.py "$H77" "$BASE"' in s
 return s
edit('make_candidate',candidate)
def mechanics(s):
 s=s.replace('build_26877_iris_rawr.sh','build_26878_iris_rawr.sh')
 s=s.replace('generate_26877_build.py','generate_26878_build.py')
 s=s.replace('bbda162004a0aa4b262a3df3547c47601df5ccb93cfb966a2dbd0a78a09e7dff',PARENT_SHA)
 return s
edit('verify_successful_mechanics',mechanics)
def safety(s):
 s=s.replace('only B 1x RGB/clip bridge and EXIF + Spektra full-active preview and native surface extent + version',
             'B 50MP GPU intent + B neon sensor clipping + Spektra capture-matched RAW and FULL-quality + version')
 s=s.replace('successful 26877','successful 26878')
 return s
edit('prebuild_safety',safety)
def replay(s):
 s=s.replace('regressions/26877_runtime_ownership_spektra.py "$WORK/historical_26876_from_26877" "$BASE"',
             'regressions/26877_runtime_ownership_spektra.py "$WORK/historical_26876_from_26877" "$WORK/historical_26877_from_26878"')
 s=s.replace('regressions/26879_runtime_ownership_spektra.py "$BASE" "$exp"',
             '''regressions/26878_runtime_ownership_spektra.py "$WORK/historical_26877_from_26878" "$BASE"
 python3 -S regressions/26879_runtime_ownership_spektra.py "$BASE" "$exp"''')
 s=s.replace('regressions/26877_runtime_ownership_spektra.py regressions/26879_runtime_ownership_spektra.py',
             'regressions/26877_runtime_ownership_spektra.py regressions/26878_runtime_ownership_spektra.py regressions/26879_runtime_ownership_spektra.py')
 return s
edit('clean_extract_replay',replay)
# Restore mandatory original history across successor.
assert 'regressions/26878_runtime_ownership_spektra.py "$WORK/historical_26877_from_26878" "$BASE"' in body
assert 'regressions/26879_runtime_ownership_spektra.py "$BASE" "$exp"' in body
# Same actual 17 stages and all compiler command lines as proven previous runner.
stages=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay']
def names(s):return [m.group(1) for m in re.finditer(r'\n([a-z_]+)\(\)\{',s)]
assert names(prior)==names(body) and [x for x in names(body) if x in stages]==stages
for cmd in ('./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace'):
 assert cmd in prior and cmd in body,cmd
for required in ('GLSLANG_VERSION="16.5.0"','PRE-BUILD SAFETY PROOF PASSED','snapshot_live_authority_seeded','RUNTIME_ARTIFACT_ID="12586138690"','runtime_changed_files=5'):
 assert required in body,required
assert 'regressions/26877_superres_ownership.py' not in body
for rel in {'verify_26879_candidate.py','verify_26879_patches.py','regressions/26879_runtime_ownership_spektra.py','regressions/26878_runtime_ownership_spektra.py','regressions/26877_runtime_ownership_spektra.py'}:
 assert (P/rel).is_file(),rel
(P/'build_26879_iris_rawr.sh').write_text(body)
(P/'26879_BUILD_INFRASTRUCTURE_DIFF.txt').write_text(''.join(difflib.unified_diff(prior.splitlines(True),body.splitlines(True),fromfile='exact_successful_26878_17_stage_runner',tofile='26879_inherited_17_stage_runner')))
(P/'26879_GENERATED_BUILD_SHA256.txt').write_text(hashlib.sha256(body.encode()).hexdigest()+'  build_26879_iris_rawr.sh\n')
print('PASS 26879 generated runner',hashlib.sha256(body.encode()).hexdigest(),'17 stage IDs',stages)
