#!/usr/bin/env python3
"""26874 deterministic 17-stage generator from the EXACT SUCCESSFUL 26873 script.
No compiler/NDK/GLSL/assemble stage substitution, no new backup or build mode.
Runtime source is 26873 successful compiled artifact, not GitHub app/src.
"""
from pathlib import Path
import sys, re, hashlib, difflib
p=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path('.').resolve()
oldfile=p/'build_26873_iris_rawr.sh';original=oldfile.read_text()
assert hashlib.sha256(original.encode()).hexdigest()=='121323a5eba3dca75ffb6f05089f73b180a6e692015895237cd780babb92aaa4', 'exact successful 26873 mechanics SHA'
body=original.replace('26873','26874')
stages=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay']
# Use exact successful 26873 functions, edit only version/authority/scope/new regression.
def fun(t,name):
 start=t.index('\n'+name+'(){')+1
 end=t.find('\n}',start);assert end>start
 return t[start:end+2]
def change_fun(name,fn):
 global body
 before=fun(body,name)
 after=fn(before)
 assert after!=before or name in ('prepare_glslang','compile_modified_runtime_shaders')
 assert body.count(before)==1
 body=body.replace(before,after)
def single(s,old,new):
 assert s.count(old)==1,(old,s.count(old))
 return s.replace(old,new)
# All prior historic 26870/71/72 texts remain intact; only 26873 tokens were promoted by version replacement.
body=single(body,'# Successful 26872 Actions compiled candidate is runtime authority.',
            '# Successful 26873 Actions compiled candidate is runtime authority.')
body=single(body,'# Keep successful 26872 17-stage verification mechanics unchanged by default.',
            '# Keep successful 26873 17-stage verification mechanics unchanged by default.')
for k,old,new in [
 ('REPO_SCAFFOLD_BASE_COMMIT','"7007f9cdf0d3fb8f5662467f82d394f5b41e256e"','"bd9404291b96c45e2956d8c81c512462bca2558d"'),
 ('RUNTIME_AUTHORITY_COMMIT','"7007f9cdf0d3fb8f5662467f82d394f5b41e256e"','"bd9404291b96c45e2956d8c81c512462bca2558d"'),
 ('RUNTIME_ARTIFACT_SHA','"b5aa31aa25946f0f1376f8d0fdbead6446a0f119492b6bd7d8bd2fb602fdbb30"','"f5a695cdba483f956eb63d6ad941d8442d39a0be990653a39c9473270f3f3ae6"'),
 ('RUNTIME_TAR_SHA','"663cd8ebaf42adc7748efff3acbe5a9bf02e4d5b647911578df028579b908c4d"','"4cbd5e84c06c0e0b560c46d4bbbf360bf18c9d637496be022bb43ecf186c9d75"'),
 ('MECHANICS_GIT_BLOB','"08c6094dd0a9ef2f1373c58cade7690690e0ffc2"','"d3559f83e63fdd3d4cd9be3dda225c5360c9b101"')]:
 line=f'{k}={old}'
 body=single(body,line,f'{k}={new}')
body=single(body,'RUNTIME_ARTIFACT_ID="12528194015"; RUNTIME_ACTIONS_RUN="40016268244"',
            'RUNTIME_ARTIFACT_ID="12538711334"; RUNTIME_ACTIONS_RUN="40038942350"')
body=single(body,'VERSION_NAME="0.9726874"; VERSION_BUILD="26874"',
            'VERSION_NAME="0.9726874"; VERSION_BUILD="26874"')
body=single(body,'ARTZIP="$WORK/26872_artifact.zip"; ARTDIR="$WORK/artifact_26872"',
            'ARTZIP="$WORK/26873_artifact.zip"; ARTDIR="$WORK/artifact_26873"')
body=single(body,'BASE="$WORK/exact_successful_26872_compiled_candidate"',
            'BASE="$WORK/exact_successful_26873_compiled_candidate"')

# Package validation: exact sealed seven-file candidate and inherited original runner.
def package(s):
 s=s.replace('regressions/26874_gpu_resident_owner.py','regressions/26874_b_jpeg_owner.py')
 s=single(s,'-eq 6 ]] || fail \'six-file strict runtime upload scope\'','-eq 7 ]] || fail \'seven-file strict runtime upload scope\'')
 s=s.replace('six-file and inherited 26872','seven-file and inherited 26873')
 s=s.replace('RUN_26874_B_GPU_RESIDENT','RUN_26874_B_JPEG_OWNER')
 return s
change_fun('verify_package',package)

def scope(s):
 s=single(s,'$RUNTIME_AUTHORITY_COMMIT:generate_26872_build.py','$RUNTIME_AUTHORITY_COMMIT:generate_26873_build.py')
 s=single(s,'successful 26872 mechanics generator','successful 26873 mechanics generator')
 s=s.replace('build_26872_iris_rawr.sh','build_26873_iris_rawr.sh')
 s=single(s,'042f4550b60ba7efb8e363230a76931969e98c2ffacda3fa310895e98f40b7db','121323a5eba3dca75ffb6f05089f73b180a6e692015895237cd780babb92aaa4')
 s=s.replace('successful 26872 17-stage','successful 26873 17-stage')
 s=s.replace('exact 26872 build','exact 26873 build').replace('26872 authority not ancestor','26873 authority not ancestor')
 return s
change_fun('verify_scope',scope)

def authority(s):
 s=s.replace('26872_', '26873_')
 s=s.replace('26872 ', '26873 ')
 s=s.replace('26872->', '26873->')
 s=s.replace('12528194015','12538711334')
 s=s.replace('photon-26872-b-preview-stripe','photon-26873-b-gpu-resident')
 s=s.replace('sha256:b5aa31aa25946f0f1376f8d0fdbead6446a0f119492b6bd7d8bd2fb602fdbb30',
             'sha256:f5a695cdba483f956eb63d6ad941d8442d39a0be990653a39c9473270f3f3ae6')
 s=s.replace('1995 ]] || fail \'not successful 26873', '1995 ]] || fail \'not successful 26873')
 s=s.replace('mechanics_generated_script_sha256=042f4550b60ba7efb8e363230a76931969e98c2ffacda3fa310895e98f40b7db',
             'mechanics_generated_script_sha256=121323a5eba3dca75ffb6f05089f73b180a6e692015895237cd780babb92aaa4')
 return s
change_fun('obtain_authority',authority)

def candidate(s):
 # Candidate transform must only overlay seven allowlisted files on exact 26873 candidate.
 s=single(s,'local H71="$WORK/historical_26871_from_26872"', '''local H72="$WORK/historical_26872_from_26873"
 cp -a "$BASE" "$H72";git -C "$H72" init -q
 (cd "$H72" && git apply --check --reverse "$ROOT/26873_FORWARD_FULL_INDEX.patch" &&
  git apply --reverse "$ROOT/26873_FORWARD_FULL_INDEX.patch" && sha256sum -c "$ROOT/26873_BASE_26872_FULL_APP.sha256" >/dev/null) || fail 'real 26873->26872 rollback failed'
 local H71="$WORK/historical_26871_from_26872"''')
 s=single(s,'cp -a "$BASE" "$H71"','cp -a "$H72" "$H71"')
 s=single(s,'regressions/26872_b_preview_only.py "$H71" "$BASE"','regressions/26872_b_preview_only.py "$H71" "$H72"')
 s=single(s,'regressions/26874_gpu_resident_owner.py "$BASE" "$CAND"',
          '''regressions/26873_gpu_resident_owner.py "$H72" "$BASE"
 python3 -S regressions/26874_b_jpeg_owner.py "$BASE" "$CAND"''')
 s=s.replace('real 26871->26870->','real 26873->26872->26871->26870->')
 return s
change_fun('make_candidate',candidate)

def mechanics(s):
 s=s.replace('build_26872_iris_rawr.sh','build_26873_iris_rawr.sh')
 s=single(s,'042f4550b60ba7efb8e363230a76931969e98c2ffacda3fa310895e98f40b7db','121323a5eba3dca75ffb6f05089f73b180a6e692015895237cd780babb92aaa4')
 s=single(s,'$RUNTIME_AUTHORITY_COMMIT:generate_26872_build.py','$RUNTIME_AUTHORITY_COMMIT:generate_26873_build.py')
 s=s.replace('successful 26872','successful 26873')
 s=s.replace('for validator in ','for validator in regressions/26873_gpu_resident_owner.py ',1)
 s=single(s,'"$ROOT/build_26872_iris_rawr.sh"','"$ROOT/build_26873_iris_rawr.sh"') if '"$ROOT/build_26872_iris_rawr.sh"' in s else s
 return s
change_fun('verify_successful_mechanics',mechanics)

def prebuild(s):
 s=s.replace('runtime_authority=successful 26872 ','runtime_authority=successful 26873 ')
 s=s.replace('verification_mechanics=exact successful 26872 ','verification_mechanics=exact successful 26873 ')
 s=s.replace('runtime_changed_files=6, all B native RAW input ownership plus guarded version',
             'runtime_changed_files=7, only B JPEG publisher/routing/private codec and guarded version')
 s=s.replace('infrastructure_delta=explicit 26874 workflow generator validators manifests and native-owner regression; compiler mechanics identical',
             'infrastructure_delta=explicit 26874 workflow/generator/manifests/B JPEG regression; identical inherited 17 compiler stages')
 s=s.replace('prior_files=1995\ncandidate_files=1995','prior_files=1995\ncandidate_files=1997')
 s=s.replace('protected_source=1989 files byte-identical to successful 26872; all GLSL/Java/AE/DNG/vendor untouched',
             'protected_source=1990 files byte-identical to successful 26873; GLSL/AE/DNG/vendor/old native JPEG unchanged')
 return s
change_fun('prebuild_safety',prebuild)

def replay(s):
 s=s.replace('regressions/26874_gpu_resident_owner.py','regressions/26874_b_jpeg_owner.py')
 s=s.replace('regressions/26872_b_preview_only.py "$WORK/historical_26871_from_26872" "$BASE"',
             'regressions/26872_b_preview_only.py "$WORK/historical_26871_from_26872" "$WORK/historical_26872_from_26873"')
 s=single(s,'regressions/26874_b_jpeg_owner.py "$BASE" "$exp"',
          '''regressions/26873_gpu_resident_owner.py "$WORK/historical_26872_from_26873" "$BASE"
 python3 -S regressions/26874_b_jpeg_owner.py "$BASE" "$exp"''')
 s=s.replace('VERSION_NAME=0.9726873','VERSION_NAME=0.9726874')
 return s
change_fun('clean_extract_replay',replay)
# Promote the rest of current report filename prefixes mechanically, but not historical validators.
# Verify that compiler commands, order and source-reconstruction machinery are inherited exactly.
for stage in stages:
 assert body.count('\n'+stage+'(){')==1,(stage,'missing/duplicate')
old_order=[m.group(1) for m in re.finditer(r'\n([a-z_]+)\(\)\{',original)]
new_order=[m.group(1) for m in re.finditer(r'\n([a-z_]+)\(\)\{',body)]
assert old_order==new_order and [x for x in new_order if x in stages]==stages
assert [x for x in new_order if x not in stages]==[x for x in old_order if x not in stages]
for cmd in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
 "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
 './gradlew :app:assembleDebug --stacktrace']:
 assert cmd in original and cmd in body
assert 'RUNTIME_ARTIFACT_ID="12538711334"' in body
assert 'VERSION_NAME="0.9726874"; VERSION_BUILD="26874"' in body
assert 'FULL ANDROID ASSEMBLE: NOT RUN YET' in body
assert 'real 26873->26872 rollback failed' in body
assert 'regressions/26873_gpu_resident_owner.py "$H72" "$BASE"' in body
assert 'regressions/26874_b_jpeg_owner.py "$BASE" "$CAND"' in body
assert 'regressions/26874_b_jpeg_owner.py "$BASE" "$exp"' in body
assert 'snapshot_live_authority_seeded' in body
assert 'regressions/26874_gpu_resident_owner.py' not in body
assert '26874_BASE_26872_FULL_APP' not in body
out=p/'build_26874_iris_rawr.sh';out.write_text(body)
diff=''.join(difflib.unified_diff(original.splitlines(keepends=True),body.splitlines(keepends=True),fromfile='exact_successful_26873_guarded_17_stages',tofile='26874_guarded_17_stages'))
(p/'26874_BUILD_INFRASTRUCTURE_DIFF.txt').write_text(diff)
(p/'26874_GENERATED_BUILD_SHA256.txt').write_text(hashlib.sha256(body.encode()).hexdigest()+'  build_26874_iris_rawr.sh\n')
print('PASS 26874 generated from exact successful 26873 17-stage script, same compiler and native/assemble order, audit diff')
print('script sha256',hashlib.sha256(body.encode()).hexdigest())
