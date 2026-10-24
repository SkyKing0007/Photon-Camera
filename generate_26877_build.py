#!/usr/bin/env python3
"""26877: preserve exact successful 26876 guarded 17-stage mechanics.
Only identity/source-domain/regression changes; all compilers and order retained.
"""
import hashlib,re,difflib,sys
from pathlib import Path
p=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path('.').resolve()
prior=(p/'build_26876_iris_rawr.sh').read_text()
PARENT_SHA='525ce763e63ae2b8aa0a9a27d1da810e8969d855ea930552e45976d741c3b912'
PARENT_GIT_BLOB='7ac7ffe6ff0e8d6fce47060676c0b9531b8b77d4'
assert hashlib.sha256(prior.encode()).hexdigest()==PARENT_SHA, 'exact successful 26876 build mechanics mismatch; never substitute stale generator'
assert re.fullmatch('[a-f0-9]{40}',PARENT_GIT_BLOB)
body=prior.replace('26876','26877').replace('0.9726876','0.9726877')

def edit(name,func):
 global body
 start=body.index('\n'+name+'(){')+1
 end=body.index('\n}',start)+2
 old=body[start:end];new=func(old)
 assert new!=old,(name,'stage not changed as expected')
 body=body[:start]+new+body[end:]

def once(s,old,new):
 assert s.count(old)==1,(old,'missing/duplicate',s.count(old))
 return s.replace(old,new,1)

# Authority identity only; no change to native/GLSL/Kotlin/Java/assemble commands.
for old,new in (
 ('REPO_SCAFFOLD_BASE_COMMIT="c3ad383c9d4b3695b6a3ef65b7837d23029903d3"', 'REPO_SCAFFOLD_BASE_COMMIT="23cb092331c7ba71f8dd52373357663054789784"'),
 ('RUNTIME_AUTHORITY_COMMIT="23c3f94222e6585690aee866277ed2ca82cca61c"', 'RUNTIME_AUTHORITY_COMMIT="23cb092331c7ba71f8dd52373357663054789784"'),
 ('RUNTIME_ARTIFACT_ID="12544774681"; RUNTIME_ACTIONS_RUN="40054980042"', 'RUNTIME_ARTIFACT_ID="12572550739"; RUNTIME_ACTIONS_RUN="40122514448"'),
 ('RUNTIME_ARTIFACT_SHA="afd2efb8b8512bdff721809d9a15898821c1cdd2f37c9542a8101afe528997f7"', 'RUNTIME_ARTIFACT_SHA="f057f62e69325acfc5d87b743dc52609138995e2df8d85423101842cf9776336"'),
 ('RUNTIME_TAR_SHA="41207fa5316469d9cd9a0f6d6844671db01ea05091322f749a49ab0a5ac5b775"', 'RUNTIME_TAR_SHA="c377625dba427dfe7506dcb8c3414e948e043a842b4df67657a5804ef5b2e7a1"'),
 ('MECHANICS_GIT_BLOB="4894b6ebeae1434d7713b690f218062c0e62f71b"',f'MECHANICS_GIT_BLOB="{PARENT_GIT_BLOB}"'),
 ('ARTZIP="$WORK/26875_artifact.zip"; ARTDIR="$WORK/artifact_26875"', 'ARTZIP="$WORK/26876_artifact.zip"; ARTDIR="$WORK/artifact_26876"'),
 ('BASE="$WORK/exact_successful_26875_compiled_candidate"', 'BASE="$WORK/exact_successful_26876_compiled_candidate"'),
):
 body=once(body,old,new)

def pkg(s):
 s=s.replace('regressions/26877_superres_ownership.py','regressions/26877_runtime_ownership_spektra.py')
 s=s.replace('verify_26877_expanded_shaders.py','verify_26876_expanded_shaders.py')
 s=s.replace('RUN_26877_B_50MP_WRONSKI_FAST_V2','RUN_26877_B_SR_OWNER_SPEKTRA_VIEWPORT_V1')
 s=s.replace('-eq 16 ]] || fail','-eq 4 ]] || fail')
 s=s.replace('sixteen-file','four-file').replace('16-file','4-file')
 s=s.replace('successful 26875','successful 26876')
 return s
edit('verify_package',pkg)

def scope(s):
 s=s.replace('$RUNTIME_AUTHORITY_COMMIT:generate_26875_build.py','$RUNTIME_AUTHORITY_COMMIT:generate_26876_build.py')
 s=s.replace('build_26875_iris_rawr.sh','build_26876_iris_rawr.sh')
 s=s.replace('b6c6f1db9f9910a0bff2175af756e3e92896d33eb6a82776de746eda645fa7a1',PARENT_SHA)
 s=s.replace('successful 26875','successful 26876').replace('26875 authority','26876 authority')
 return s
edit('verify_scope',scope)

def authority(s):
 # Only this function is about the preceding compiled artifact, build 26876.
 s=s.replace('build_26877_iris_rawr_outputs/26877_candidate_app_source.tar.gz',
             'build_26876_iris_rawr_outputs/26876_candidate_app_source.tar.gz')
 s=s.replace('26875','26876')
 s=s.replace("'id':12544774681","'id':12572550739")
 s=s.replace("'name':'photon-26876-b-device-correction'","'name':'photon-26876-b-true50mp-wronski-fast'")
 s=s.replace('sha256:afd2efb8b8512bdff721809d9a15898821c1cdd2f37c9542a8101afe528997f7',
             'sha256:f057f62e69325acfc5d87b743dc52609138995e2df8d85423101842cf9776336')
 s=s.replace('build_26877_iris_rawr_outputs/','build_26876_iris_rawr_outputs/')
 s=s.replace('26877_candidate_app_source.tar.gz','26876_candidate_app_source.tar.gz')
 # IRIS_26877_AUTHORITY_UNIVERSE: 26876 compiled candidate contains 2001,
 # not the 1997 files of the historical 26875 artifact.
 s=s.replace('1997 ]] || fail','2001 ]] || fail')
 s=s.replace('26876 successful artifact metadata mismatch','26876 successful artifact metadata mismatch')
 # Validate successful 26876 artifact identity, manifest and compiled status.
 for marker in ('12572550739','photon-26876-b-true50mp-wronski-fast',
                'sha256:f057f62e69325acfc5d87b743dc52609138995e2df8d85423101842cf9776336',
                'build_26876_iris_rawr_outputs/26876_candidate_app_source.tar.gz'):
  assert marker in s,('stale successful 26876 artifact',marker)
 assert '12544774681' not in s,'stale 26875 artifact ID'
 return s
edit('obtain_authority',authority)

def candidate(s):
 # Reconstruct all historical candidates from real successful 26876 universe.
 # A real 26876 -> 26875 inverse precedes inherited 26875 -> 26874 ->...
 marker='local H74="$WORK/historical_26874_from_26875"'
 assert marker in s,'26876 inherited history predecessor missing'
 extra='''local H75="$WORK/historical_26875_from_26876"
 cp -a "$BASE" "$H75";git -C "$H75" init -q
 (cd "$H75" && git apply --check --reverse "$ROOT/26876_FORWARD_FULL_INDEX.patch" &&
  git apply --reverse "$ROOT/26876_FORWARD_FULL_INDEX.patch" &&
  sha256sum -c "$ROOT/26876_BASE_26875_FULL_APP.sha256" >/dev/null) || fail 'real 26876->26875 rollback failed'
 '''
 s=s.replace(marker,extra+marker,1)
 s=once(s,'cp -a "$BASE" "$H74"','cp -a "$H75" "$H74"')
 s=s.replace('regressions/26875_device_failures.py "$H74" "$BASE"',
             'regressions/26875_device_failures.py "$H74" "$H75"')
 # Preserve the exact 26876 B routing regression against genuine old/new 26875/26876.
 s=s.replace('regressions/26877_superres_ownership.py "$BASE" "$CAND"',
 '''regressions/26876_superres_ownership.py "$H75" "$BASE"
 python3 -S regressions/26877_runtime_ownership_spektra.py "$BASE" "$CAND"''')
 s=s.replace('verify_26877_expanded_shaders.py "$CAND"','verify_26876_expanded_shaders.py "$CAND"')
 assert 'regressions/26877_runtime_ownership_spektra.py "$BASE" "$CAND"' in s
 assert 'verify_26877_candidate.py "$BASE" "$CAND"' in s
 return s
edit('make_candidate',candidate)

def mechanics(s):
 s=s.replace('$RUNTIME_AUTHORITY_COMMIT:generate_26875_build.py','$RUNTIME_AUTHORITY_COMMIT:generate_26876_build.py')
 s=s.replace('build_26875_iris_rawr.sh','build_26876_iris_rawr.sh')
 s=s.replace('b6c6f1db9f9910a0bff2175af756e3e92896d33eb6a82776de746eda645fa7a1',PARENT_SHA)
 s=s.replace('successful 26875','successful 26876')
 s=s.replace('regressions/26877_superres_ownership.py','regressions/26877_runtime_ownership_spektra.py')
 return s
edit('verify_successful_mechanics',mechanics)

def shaders(s):
 # The 26877 runtime change has ZERO modified GLSL/GLSL ES sources;
 # replay the real inherited 26876 expanded shaders with exactly the pinned
 # compiler already discovered by prepare_glslang. No new compiler lookup.
 s=s.replace('verify_26877_expanded_shaders.py','verify_26876_expanded_shaders.py')
 assert 'export IRIS_PINNED_GLSLANG_VALIDATOR="$IRIS26864_GLSLANG"' in s
 assert 'command -v glslangValidator' not in s
 return s
edit('compile_modified_runtime_shaders',shaders)

def safety(s):
 s=s.replace('runtime_changed_files=16','runtime_changed_files=4')
 s=s.replace('prior_files=1997','prior_files=2001')
 s=s.replace('candidate_files=2001','candidate_files=2001')
 s=s.replace('protected_source=1994 files byte-identical to successful 26875',
             'protected_source=1997 files byte-identical to successful 26876')
 s=s.replace('only B single-merge 50MP GPU/clip/private JPEG-R + exact guarded version',
             'only B 1x RGB/clip lifetime + Spektra surface geometry + guarded version')
 s=s.replace('successful 26875','successful 26876')
 return s
edit('prebuild_safety',safety)

def replay(s):
 s=s.replace('regressions/26877_superres_ownership.py "$BASE" "$exp"',
 '''regressions/26876_superres_ownership.py "$WORK/historical_26875_from_26876" "$BASE"
 python3 -S regressions/26877_runtime_ownership_spektra.py "$BASE" "$exp"''')
 s=s.replace('regressions/26875_device_failures.py "$WORK/historical_26874_from_26875" "$BASE"',
             'regressions/26875_device_failures.py "$WORK/historical_26874_from_26875" "$WORK/historical_26875_from_26876"')
 s=s.replace('verify_26877_expanded_shaders.py','verify_26876_expanded_shaders.py')
 assert 'regressions/26877_runtime_ownership_spektra.py "$BASE" "$exp"' in s
 assert 'verify_26877_candidate.py "$BASE" "$exp"' in s
 return s
edit('clean_extract_replay',replay)
# Freeze proven 17 ordered functions and unchanged real project compilers.
STAGES=['verify_package','verify_scope','obtain_authority','make_candidate',
'verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders',
'compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages',
'verify_native_glslang_handoff','compile_native','verify_candidate_patches',
'prebuild_safety','assemble','postbuild_proof','clean_extract_replay']
old=[x.group(1) for x in re.finditer(r'\n([a-z_]+)\(\)\{',prior)]
new=[x.group(1) for x in re.finditer(r'\n([a-z_]+)\(\)\{',body)]
assert old==new and [x for x in new if x in STAGES]==STAGES,(old,new)
for cmd in ('./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
            "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
            './gradlew :app:assembleDebug --stacktrace'):
 assert cmd in prior and cmd in body,('inherited real compiler changed',cmd)
for marker in ('snapshot_live_authority_seeded','GLSLANG_VERSION="16.5.0"',
               'PRE-BUILD SAFETY PROOF PASSED','RUNTIME_ARTIFACT_ID="12572550739"',
               'VERSION_NAME="0.9726877"','verify_26877_candidate.py "$BASE" "$CAND"',
               'regressions/26877_runtime_ownership_spektra.py "$BASE" "$CAND"',
               'export IRIS_PINNED_GLSLANG_VALIDATOR="$IRIS26864_GLSLANG"'):
 assert marker in body,('missing verified stage',marker)
assert 'verify_26877_expanded_shaders.py' not in body
assert 'command -v glslangValidator' not in body
(p/'build_26877_iris_rawr.sh').write_text(body)
(p/'26877_BUILD_INFRASTRUCTURE_DIFF.txt').write_text(''.join(difflib.unified_diff(
 prior.splitlines(True),body.splitlines(True),fromfile='successful_26876_exact_17_stage_runner',
 tofile='26877_inherited_17_stage_runner')))
(p/'26877_GENERATED_BUILD_SHA256.txt').write_text(hashlib.sha256(body.encode()).hexdigest()+'  build_26877_iris_rawr.sh\n')
print('PASS 26877 exact successful 26876 17-stage mechanics inherited, real compiler commands unchanged, infrastructure diff documented; generated_sha256',hashlib.sha256(body.encode()).hexdigest())
