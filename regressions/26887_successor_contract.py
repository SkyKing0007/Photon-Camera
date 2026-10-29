#!/usr/bin/env python3
"""26887 exact successful V6 predecessor and release successor source contract.

This is an auxiliary guard, never a substitute for real runner execution.
"""
from pathlib import Path
import hashlib,re,sys,shlex
R=Path(__file__).resolve().parent.parent
assert sys.argv[1:] in ([],['--generated'])
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
parent=R/'build_26886_iris_rawr.sh'
assert parent.is_file(),'missing exact successful V6 runner'
assert sha(parent)=='3f816088f564bfd575d5dc8e1681b9b1b18ec435de41ed34f2c22df866c5e8fa'
script=(R/'generate_26887_build.py').read_text()
assert 'STAGES=(' in script and '26887_GENERATED_BUILD_SHA256.txt' in script
assert '26887_FORWARD_FULL_INDEX.patch 26887_ROLLBACK_FULL_INDEX.patch' in script
assert "RUNTIME_TAR_SHA=\"e2a03925cafa2196884fff02d9320f6ac4020823130b896de7166eb77ded144b\"" in script
assert '2138db01cbfb3a8421c12e54ba29d4f0a893d1cdd4a219ee34a40a4dc0c54379' in script
assert "GLSLANG_VERSION=\"16.5.0\"" in script
assert "'compile_native'" not in script or 'compile_native' in script
assert (R/'26887_CHANGED_ALLOWLIST.txt').read_text().count('\n')==17
w=(R/'.github/workflows/build-26887-iris-rawr.yml').read_text()
assert w.count('python3 -S generate_26886_build.py .')==2
assert w.count('python3 -S generate_26887_build.py .')==2
assert w.count('sha256sum -c 26887_GENERATED_BUILD_SHA256.txt')==1
assert w.count('bash build_26887_iris_rawr.sh')==1
assert w.count('TRIGGER_26887.txt')>=1
old=(R/'.github/workflows/build-26886-iris-rawr.yml').read_text()
assert hashlib.sha256(old.encode()).hexdigest()=='6935d2cf2c87bcb601dcc3492cdafe29d2edb0c3e6d92cecb02b2f0e668270a4', 'successful V6 workflow byte drift'
start='          test -f TRIGGER_26882.txt'
end='          test "$(find handoff_payload_26886 -type f | wc -l)" -eq 2'
assert w.split(start,1)[1].split(end,1)[0]==old.split(start,1)[1].split(end,1)[0]
STAGES=('verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay')
rx=re.compile(r'\n([a-z_]+)\(\)\{')
base=parent.read_text()
assert [n for n in rx.findall(base) if n in STAGES]==list(STAGES)
if sys.argv[1:]==['--generated']:
 child=R/'build_26887_iris_rawr.sh'
 assert child.is_file(),'missing generated successor'
 assert sha(child)==(R/'26887_GENERATED_BUILD_SHA256.txt').read_text().split()[0]
 s=child.read_text()
 assert rx.findall(s)==rx.findall(base)
 for x in ('./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace'):
  assert x in base and x in s
 assert 'GLSLANG_VERSION="16.5.0"' in s
 for stage in ('make_candidate','compile_modified_runtime_shaders','clean_extract_replay'):
  block=s[s.index('\n'+stage+'(){')+1:s.index('\n}',s.index('\n'+stage+'(){')+1)+2]
  assert 'verify_26887_expanded_glsl.py' in block,(stage,'shader guard absent')
 check=s[s.index('\nverify_candidate_patches(){')+1:s.index('\n}',s.index('\nverify_candidate_patches(){')+1)+2]
 line=[k for k in check.splitlines() if 'python3 -S verify_26887_patches.py' in k]
 assert len(line)>=1
 assert shlex.split(line[-1])==['python3','-S','verify_26887_patches.py','$BASE','$CAND','26887_FORWARD_FULL_INDEX.patch','26887_ROLLBACK_FULL_INDEX.patch']
 print('PASS 26887 generated runner inherited exact 17 stages and actual current patch CLI, exact compiler/assemble commands')
else:print('PASS V6 successful parent runner identity and successor stage preconditions; generated 26887 runner NOT RUN')
