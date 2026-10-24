#!/usr/bin/env python3
"""Advance exact successful 26874 generated 17-stage guarded runner to 26875.
Only authority/version, exact three-file B runtime scope and real-device regressions advance;
compiler/shader/NDK/assemble order and inherited handoff ownership stay fixed.
"""
from pathlib import Path
import sys, hashlib, re, difflib
p=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path('.').resolve()
original=(p/'build_26874_iris_rawr.sh').read_text()
assert hashlib.sha256(original.encode()).hexdigest()=='3b48818fd6cd6376f97cecca5a34b85ce4788e10a37435e3273beb2eddf3282a', 'successful 26874 mechanics source mismatch'
body=original.replace('26874','26875').replace('0.9726874','0.9726875')
def once(old,new):
 global body
 assert body.count(old)==1,(old,body.count(old));body=body.replace(old,new)
def edit(name,change):
 global body
 start=body.index('\n'+name+'(){')+1;end=body.index('\n}',start)+2
 old=body[start:end];new=change(old)
 assert new!=old,(name,'unchanged');body=body[:start]+new+body[end:]
# Exact successful compiled-candidate authority, from successful Actions 40050271749.
for old,new in [
 ('Successful 26873 Actions compiled candidate','Successful 26874 Actions compiled candidate'),
 ('# Keep successful 26873 17-stage verification mechanics unchanged by default.','# Keep successful 26874 17-stage verification mechanics unchanged by default.'),
 ('REPO_SCAFFOLD_BASE_COMMIT="bd9404291b96c45e2956d8c81c512462bca2558d"','REPO_SCAFFOLD_BASE_COMMIT="d69751ed0aaf4ef3597fb1af5ce274deeee17928"'),
 ('RUNTIME_AUTHORITY_COMMIT="bd9404291b96c45e2956d8c81c512462bca2558d"','RUNTIME_AUTHORITY_COMMIT="d69751ed0aaf4ef3597fb1af5ce274deeee17928"'),
 ('RUNTIME_ARTIFACT_ID="12538711334"; RUNTIME_ACTIONS_RUN="40038942350"','RUNTIME_ARTIFACT_ID="12543720749"; RUNTIME_ACTIONS_RUN="40050271749"'),
 ('RUNTIME_ARTIFACT_SHA="f5a695cdba483f956eb63d6ad941d8442d39a0be990653a39c9473270f3f3ae6"','RUNTIME_ARTIFACT_SHA="d95e693fe840c956cc03df456d6dc3417ba82740ca0eff6ef9a5a12c353f5b5b"'),
 ('RUNTIME_TAR_SHA="4cbd5e84c06c0e0b560c46d4bbbf360bf18c9d637496be022bb43ecf186c9d75"','RUNTIME_TAR_SHA="223676c4a1ac0ac5c583e7504bbce361f8eef8eecaa28b96f708d2db2b1b322c"'),
 ('MECHANICS_GIT_BLOB="d3559f83e63fdd3d4cd9be3dda225c5360c9b101"','MECHANICS_GIT_BLOB="8445762e87ddd9314fb88d24581554ad9a1e5c5d"'),
 ('ARTZIP="$WORK/26873_artifact.zip"; ARTDIR="$WORK/artifact_26873"','ARTZIP="$WORK/26874_artifact.zip"; ARTDIR="$WORK/artifact_26874"'),
 ('BASE="$WORK/exact_successful_26873_compiled_candidate"','BASE="$WORK/exact_successful_26874_compiled_candidate"')]:once(old,new)

def pkg(s):
 s=s.replace('regressions/26875_b_jpeg_owner.py','regressions/26875_device_failures.py')
 s=s.replace("-eq 7 ]] || fail 'seven-file strict runtime upload scope'","-eq 3 ]] || fail 'three-file strict runtime upload scope'")
 s=s.replace('seven-file and inherited 26873','three-file and inherited 26874')
 s=s.replace('RUN_26875_B_JPEG_OWNER','RUN_26875_B_DEVICE_CORRECTION')
 return s
edit('verify_package',pkg)

def scope(s):
 s=s.replace('26873 authority not ancestor','26874 authority not ancestor')
 s=s.replace('$RUNTIME_AUTHORITY_COMMIT:generate_26873_build.py','$RUNTIME_AUTHORITY_COMMIT:generate_26874_build.py')
 s=s.replace('build_26873_iris_rawr.sh','build_26874_iris_rawr.sh')
 s=s.replace('121323a5eba3dca75ffb6f05089f73b180a6e692015895237cd780babb92aaa4','3b48818fd6cd6376f97cecca5a34b85ce4788e10a37435e3273beb2eddf3282a')
 s=s.replace('successful 26873','successful 26874')
 return s
edit('verify_scope',scope)

def auth(s):
 s=s.replace('26873','26874')
 s=s.replace('12538711334','12543720749').replace('photon-26874-b-gpu-resident','photon-26874-b-native-jpeg')
 s=s.replace('f5a695cdba483f956eb63d6ad941d8442d39a0be990653a39c9473270f3f3ae6','d95e693fe840c956cc03df456d6dc3417ba82740ca0eff6ef9a5a12c353f5b5b')
 s=s.replace('121323a5eba3dca75ffb6f05089f73b180a6e692015895237cd780babb92aaa4','3b48818fd6cd6376f97cecca5a34b85ce4788e10a37435e3273beb2eddf3282a')
 s=s.replace('1995 ]] || fail','1997 ]] || fail')
 return s
edit('obtain_authority',auth)

def cand(s):
 s=s.replace('''local H72="$WORK/historical_26872_from_26873"
 cp -a "$BASE" "$H72";git -C "$H72" init -q''','''local H73="$WORK/historical_26873_from_26874"
 cp -a "$BASE" "$H73";git -C "$H73" init -q
 (cd "$H73" && git apply --check --reverse "$ROOT/26874_FORWARD_FULL_INDEX.patch" &&
  git apply --reverse "$ROOT/26874_FORWARD_FULL_INDEX.patch" && sha256sum -c "$ROOT/26874_BASE_26873_FULL_APP.sha256" >/dev/null) || fail 'real 26874->26873 rollback failed'
 local H72="$WORK/historical_26872_from_26873"
 cp -a "$H73" "$H72";rm -rf "$H72/.git";git -C "$H72" init -q''')
 s=s.replace('regressions/26873_gpu_resident_owner.py "$H72" "$BASE"','regressions/26873_gpu_resident_owner.py "$H72" "$H73"')
 s=s.replace('regressions/26875_b_jpeg_owner.py "$BASE" "$CAND"', '''regressions/26874_b_jpeg_owner.py "$H73" "$BASE"
 python3 -S regressions/26875_device_failures.py "$BASE" "$CAND"''')
 s=s.replace('real 26873->26872','real 26874->26873->26872')
 assert '26874_FORWARD_FULL_INDEX.patch' in s
 assert 'regressions/26874_b_jpeg_owner.py "$H73" "$BASE"' in s
 return s
edit('make_candidate',cand)

def mechanics(s):
 s=s.replace('build_26873_iris_rawr.sh','build_26874_iris_rawr.sh')
 s=s.replace('121323a5eba3dca75ffb6f05089f73b180a6e692015895237cd780babb92aaa4','3b48818fd6cd6376f97cecca5a34b85ce4788e10a37435e3273beb2eddf3282a')
 s=s.replace('$RUNTIME_AUTHORITY_COMMIT:generate_26873_build.py','$RUNTIME_AUTHORITY_COMMIT:generate_26874_build.py')
 s=s.replace('successful 26873','successful 26874')
 s=s.replace('for validator in regressions/26873_gpu_resident_owner.py','for validator in regressions/26874_b_jpeg_owner.py regressions/26873_gpu_resident_owner.py')
 s=s.replace('B-only native input diff audited','B-only device correction diff audited')
 return s
edit('verify_successful_mechanics',mechanics)

def patch(s):return s.replace('exact 26875 6-file binary','exact 26875 3-file binary')
edit('verify_candidate_patches',patch)

def safety(s):
 s=s.replace('successful 26873','successful 26874')
 s=s.replace('runtime_changed_files=7, only B JPEG publisher/routing/private codec and guarded version','runtime_changed_files=3, only B JPEG publication + true2x WB/highlight routing + guarded version')
 s=s.replace('infrastructure_delta=explicit 26875 workflow/generator/manifests/B JPEG regression; identical inherited 17 compiler stages','infrastructure_delta=26875 workflow/generator/manifests/device-failure regression; exact inherited 17 compiler stages')
 s=s.replace('prior_files=1995','prior_files=1997').replace('candidate_files=1997','candidate_files=1997')
 s=s.replace('protected_source=1990 files byte-identical to successful 26874','protected_source=1994 files byte-identical to successful 26874')
 return s
edit('prebuild_safety',safety)

def replay(s):
 s=s.replace('regressions/26875_b_jpeg_owner.py','regressions/26875_device_failures.py')
 s=s.replace('regressions/26873_gpu_resident_owner.py "$WORK/historical_26872_from_26873" "$BASE"', 'regressions/26873_gpu_resident_owner.py "$WORK/historical_26872_from_26873" "$WORK/historical_26873_from_26874"')
 s=s.replace('regressions/26875_device_failures.py "$BASE" "$exp"', '''regressions/26874_b_jpeg_owner.py "$WORK/historical_26873_from_26874" "$BASE"
 python3 -S regressions/26875_device_failures.py "$BASE" "$exp"''')
 return s
edit('clean_extract_replay',replay)
# The successful runner's function inventory/order (including the canonical snapshot helper)
# and exact real compiler commands must not be redesigned.
stages=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay']
old=[m.group(1) for m in re.finditer(r'\n([a-z_]+)\(\)\{',original)]
new=[m.group(1) for m in re.finditer(r'\n([a-z_]+)\(\)\{',body)]
assert old==new and [x for x in new if x in stages]==stages
for cmd in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace']:
 assert cmd in original and cmd in body
for key in ('snapshot_live_authority_seeded','GLSLANG_VERSION="16.5.0"','PRE-BUILD SAFETY PROOF PASSED','RUNTIME_ARTIFACT_ID="12543720749"','VERSION_NAME="0.9726875"','regressions/26875_device_failures.py "$BASE" "$CAND"'):
 assert key in body,key
assert 'regressions/26875_b_jpeg_owner.py' not in body
out=p/'build_26875_iris_rawr.sh';out.write_text(body)
diff=''.join(difflib.unified_diff(original.splitlines(keepends=True),body.splitlines(keepends=True),fromfile='successful_26874_exact_17_stage_runner',tofile='26875_guarded_17_stage_runner'))
(p/'26875_BUILD_INFRASTRUCTURE_DIFF.txt').write_text(diff)
(p/'26875_GENERATED_BUILD_SHA256.txt').write_text(hashlib.sha256(body.encode()).hexdigest()+'  build_26875_iris_rawr.sh\n')
print('PASS 26875 17 original functions, exact real compiler commands, infrastructure diff; sha256',hashlib.sha256(body.encode()).hexdigest())
