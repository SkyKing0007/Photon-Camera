#!/usr/bin/env python3
"""Inherit exactly the successful 26875 17-stage runner; B-only SR 26876 gates."""
import hashlib,re,difflib,sys,subprocess
from pathlib import Path
p=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path('.').resolve()
prior=(p/'build_26875_iris_rawr.sh').read_text()
PARENT_SHA='b6c6f1db9f9910a0bff2175af756e3e92896d33eb6a82776de746eda645fa7a1'
assert hashlib.sha256(prior.encode()).hexdigest()==PARENT_SHA,'exact successful 26875 17-stage runner mismatch'
# IRIS_26876_REGRESSION_GITHUB_FAILED_RUN_40060844244
# The 26875 successful build-script SHA256 and committed generator Git blob
# are different identities. Never hash build_26875_iris_rawr.sh and claim it
# is the committed generate_26875_build.py blob.
PARENT_GIT_BLOB='4894b6ebeae1434d7713b690f218062c0e62f71b'
assert re.fullmatch(r'[a-f0-9]{40}',PARENT_GIT_BLOB)
body=prior.replace('26875','26876').replace('0.9726875','0.9726876')
def edit(fn,transform):
 global body
 start=body.index('\n'+fn+'(){')+1;end=body.index('\n}',start)+2
 original=body[start:end];changed=transform(original)
 assert changed!=original,(fn,'no change')
 body=body[:start]+changed+body[end:]
def replace_anchor(s,old,new,label):
 assert old in s,(label,old)
 return s.replace(old,new)
# Identity substitutions only; no compiler, NDK, assembler or stage reordering.
for before,after in (
 ('REPO_SCAFFOLD_BASE_COMMIT="d69751ed0aaf4ef3597fb1af5ce274deeee17928"','REPO_SCAFFOLD_BASE_COMMIT="c3ad383c9d4b3695b6a3ef65b7837d23029903d3"'),
 ('RUNTIME_AUTHORITY_COMMIT="d69751ed0aaf4ef3597fb1af5ce274deeee17928"','RUNTIME_AUTHORITY_COMMIT="23c3f94222e6585690aee866277ed2ca82cca61c"'),
 ('RUNTIME_ARTIFACT_ID="12543720749"; RUNTIME_ACTIONS_RUN="40050271749"','RUNTIME_ARTIFACT_ID="12544774681"; RUNTIME_ACTIONS_RUN="40054980042"'),
 ('RUNTIME_ARTIFACT_SHA="d95e693fe840c956cc03df456d6dc3417ba82740ca0eff6ef9a5a12c353f5b5b"','RUNTIME_ARTIFACT_SHA="afd2efb8b8512bdff721809d9a15898821c1cdd2f37c9542a8101afe528997f7"'),
 ('RUNTIME_TAR_SHA="223676c4a1ac0ac5c583e7504bbce361f8eef8eecaa28b96f708d2db2b1b322c"','RUNTIME_TAR_SHA="41207fa5316469d9cd9a0f6d6844671db01ea05091322f749a49ab0a5ac5b775"'),
 ('MECHANICS_GIT_BLOB="8445762e87ddd9314fb88d24581554ad9a1e5c5d"',f'MECHANICS_GIT_BLOB="{PARENT_GIT_BLOB}"'),
 ('ARTZIP="$WORK/26874_artifact.zip"; ARTDIR="$WORK/artifact_26874"','ARTZIP="$WORK/26875_artifact.zip"; ARTDIR="$WORK/artifact_26875"'),
 ('BASE="$WORK/exact_successful_26874_compiled_candidate"','BASE="$WORK/exact_successful_26875_compiled_candidate"'),
):
 assert before in body,before
 body=body.replace(before,after)

def pkg(s):
 s=s.replace('regressions/26876_device_failures.py','regressions/26876_superres_ownership.py')
 s=s.replace('RUN_26876_B_DEVICE_CORRECTION','RUN_26876_B_50MP_WRONSKI_FAST_V2')
 # exact 16-file allowlist for 1997-file successful 26875 compiled candidate
 s=s.replace('-eq 3 ]] || fail', '-eq 16 ]] || fail')
 s=s.replace('three-file strict runtime upload scope','sixteen-file strict runtime upload scope')
 return s
edit('verify_package',pkg)
def scope(s):
 s=s.replace('26874 authority not ancestor','26875 authority not ancestor')
 s=s.replace('$RUNTIME_AUTHORITY_COMMIT:generate_26874_build.py','$RUNTIME_AUTHORITY_COMMIT:generate_26875_build.py')
 s=s.replace('build_26874_iris_rawr.sh','build_26875_iris_rawr.sh')
 s=s.replace('3b48818fd6cd6376f97cecca5a34b85ce4788e10a37435e3273beb2eddf3282a',PARENT_SHA)
 s=s.replace('successful 26874','successful 26875')
 return s
edit('verify_scope',scope)
def authority(s):
 # The current runtime artifact is 26875, although the NEW runner is 26876.
 s=s.replace('build_26876_iris_rawr_outputs/26876_candidate_app_source.tar.gz',
             'build_26875_iris_rawr_outputs/26875_candidate_app_source.tar.gz')
 s=s.replace('photon-26874-b-native-jpeg','photon-26875-b-device-correction')
 s=s.replace('26874','26875')  # this stage is solely the preceding runtime artifact
 s=s.replace('26876_candidate_app_source.tar.gz','26875_candidate_app_source.tar.gz')
 s=s.replace('build_26876_iris_rawr_outputs/','build_26875_iris_rawr_outputs/')
 s=s.replace('1997 ]] || fail','1997 ]] || fail')
 return s
edit('obtain_authority',authority)
def candidate(s):
 # Reconstruct historical predecessors from the REAL 26875 compiled source.
 # Old 26874 -> 26873 -> 26872 replay remains completely inherited.
 marker='local H73="$WORK/historical_26873_from_26874"'
 assert marker in s, 'historical 26875->26874 rollback anchor missing'
 extra='''local H74="$WORK/historical_26874_from_26875"
 cp -a "$BASE" "$H74";git -C "$H74" init -q
 (cd "$H74" && git apply --check --reverse "$ROOT/26875_FORWARD_FULL_INDEX.patch" &&
  git apply --reverse "$ROOT/26875_FORWARD_FULL_INDEX.patch" &&
  sha256sum -c "$ROOT/26875_BASE_26874_FULL_APP.sha256" >/dev/null) || fail 'real 26875->26874 rollback failed'
 '''
 s=s.replace(marker,extra+marker,1)
 s=s.replace('cp -a "$BASE" "$H73"','cp -a "$H74" "$H73"',1)
 s=s.replace('regressions/26874_b_jpeg_owner.py "$H73" "$BASE"',
             'regressions/26874_b_jpeg_owner.py "$H73" "$H74"')
 # Direct device owner: test exact real before/after 26875, not new version.
 s=s.replace('regressions/26876_device_failures.py "$BASE" "$CAND"',
 '''regressions/26875_device_failures.py "$H74" "$BASE"
 python3 -S regressions/26876_superres_ownership.py "$BASE" "$CAND"
 python3 -S verify_26876_candidate.py "$BASE" "$CAND"
 python3 -S verify_26876_expanded_shaders.py "$CAND" --source-only''')
 assert 'verify_26876_candidate.py "$BASE" "$CAND"' in s
 return s
edit('make_candidate',candidate)
def mechanics(s):
 s=s.replace('build_26874_iris_rawr.sh','build_26875_iris_rawr.sh')
 s=s.replace('3b48818fd6cd6376f97cecca5a34b85ce4788e10a37435e3273beb2eddf3282a',PARENT_SHA)
 s=s.replace('$RUNTIME_AUTHORITY_COMMIT:generate_26874_build.py','$RUNTIME_AUTHORITY_COMMIT:generate_26875_build.py')
 s=s.replace('successful 26874','successful 26875')
 s=s.replace('regressions/26876_device_failures.py','regressions/26876_superres_ownership.py')
 return s
edit('verify_successful_mechanics',mechanics)
def shaders(s):
 # Keep every inherited 26875 shader/compiler invocation first and in the
 # same stage, then validate EXACT runtime expanded new 26876 sources with
 # pinned real glslang 16.5, never with a mock or static-only parser.
 needle='\n}'
 assert s.endswith(needle)
 insert='''
 local realGlslang=""
 realGlslang="$(command -v glslangValidator || true)"
 if [[ -z "$realGlslang" ]]; then
  realGlslang="$(find "$WORK" -type f -name glslangValidator -perm /111 -print -quit)"
 fi
 [[ -n "$realGlslang" && -x "$realGlslang" ]] || fail '26876 pinned real glslangValidator unavailable'
 export IRIS_PINNED_GLSLANG_VALIDATOR="$realGlslang"
 python3 -S verify_26876_expanded_shaders.py "$CAND" || fail '26876 true runtime-expanded GLSL failed pinned compiler'
'''
 return s[:-len(needle)]+insert+needle
edit('compile_modified_runtime_shaders',shaders)
def patches(s):
 s=s.replace('exact 26876 3-file binary','exact 26876 16-file binary')
 return s+'\n' if False else s.replace('verify_26876_patches.py', 'verify_26876_patches.py')+'\n' if False else s
# Inherited patch stage unchanged except global 26876 version and exact new patch inputs.
def safety(s):
 s=s.replace('successful 26874','successful 26875')
 s=s.replace('only B JPEG publication + true2x WB/highlight routing + guarded version',
             'only B single-merge 50MP GPU/clip/private JPEG-R + exact guarded version')
 s=s.replace('runtime_changed_files=3','runtime_changed_files=16')
 s=s.replace('candidate_files=1997','candidate_files=2001')
 s=s.replace('protected_source=1994 files byte-identical to successful 26874',
             'protected_source=1985 files byte-identical to successful 26875')
 return s
edit('prebuild_safety',safety)
def replay(s):
 s=s.replace('regressions/26876_device_failures.py', 'regressions/26876_superres_ownership.py')
 s=s.replace('regressions/26874_b_jpeg_owner.py "$WORK/historical_26873_from_26874" "$BASE"',
 '''regressions/26874_b_jpeg_owner.py "$WORK/historical_26873_from_26874" "$WORK/historical_26874_from_26875"
 python3 -S regressions/26875_device_failures.py "$WORK/historical_26874_from_26875" "$BASE"''')
 s=s.replace('regressions/26876_superres_ownership.py "$BASE" "$exp"',
 '''regressions/26876_superres_ownership.py "$BASE" "$exp"
 python3 -S verify_26876_candidate.py "$BASE" "$exp"
 python3 -S verify_26876_expanded_shaders.py "$exp"''')
 return s
edit('clean_extract_replay',replay)
# Fail if inherited 17-stage mechanics/order or exact project compilers differ.
STAGES=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay']
old=[m.group(1) for m in re.finditer(r'\n([a-z_]+)\(\)\{',prior)]
new=[m.group(1) for m in re.finditer(r'\n([a-z_]+)\(\)\{',body)]
assert old==new and [x for x in new if x in STAGES]==STAGES,(old,new)
for cmd in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace']:
 assert cmd in prior and cmd in body,'real inherited compiler/assemble invocation missing'
for marker in ('snapshot_live_authority_seeded','GLSLANG_VERSION="16.5.0"','PRE-BUILD SAFETY PROOF PASSED','RUNTIME_ARTIFACT_ID="12544774681"','VERSION_NAME="0.9726876"','verify_26876_candidate.py "$BASE" "$CAND"'):
 assert marker in body,marker
(p/'build_26876_iris_rawr.sh').write_text(body)
diff=''.join(difflib.unified_diff(prior.splitlines(True),body.splitlines(True),fromfile='successful_26875_exact_17_stage_runner',tofile='26876_inherited_17_stage_runner'))
(p/'26876_BUILD_INFRASTRUCTURE_DIFF.txt').write_text(diff)
(p/'26876_GENERATED_BUILD_SHA256.txt').write_text(hashlib.sha256(body.encode()).hexdigest()+'  build_26876_iris_rawr.sh\n')
print('PASS 26876 exact 26875 17-stage ordered mechanics, all real compiler commands, sha256',hashlib.sha256(body.encode()).hexdigest())
