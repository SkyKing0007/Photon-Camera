#!/usr/bin/env python3
"""Permanent 26884 real failure regression: stale artifact/source-stage and trigger errors.
The successful 26883 runner's source and stage order must not be reinterpreted.
"""
from pathlib import Path
import ast,hashlib,re,tempfile,subprocess,sys
R=Path(__file__).resolve().parents[1];G=R/'generate_26884_build.py'
s=G.read_text();ast.parse(s)
assert "PARENT='7799509f64c7f84c2223f7014dac925b2f6f31ed96667d754d0b1c0df29e979f'" in s
assert "prior.replace('26883','26884')" in s
for v in ('12734144623','40505011172','28823b94be2cc636983f01a99dfc2f0840f5a05b',
'e1ffb9c7c826d5504d39b496134aeea141a4b8e2661f30496ecbacc3ff997071',
'729c9ad909c3444bec1028e17a4a4803b1ebda3fe73d0c541b466b825a93e1f7'):
 assert v in s,('stale artifact identity',v)
assert 'historical_26882_from_26883' in s and '26883_BASE_26882_FULL_APP.sha256' in s
editnames=re.findall(r"edit\('([a-z_]+)',",s)
assert len(editnames)==len(set(editnames))
assert not set(editnames)&{'compile_languages','compile_native','assemble','install_frozen_candidate_live','postbuild_proof','prepare_glslang','verify_native_glslang_handoff','compile_spektra_raw_shader'}
for v in ('verify_26883_candidate.py "$H82" "$BASE"',
'verify_26883_semantics.py "$H82" "$BASE"',
'verify_26883_expanded_glsl.py "$BASE"',
'verify_26884_semantics.py "$BASE" "$CAND"',
'verify_26884_expanded_glsl.py "$CAND" --compiler "$IRIS26864_GLSLANG"',
'protected_source=2006 files byte-identical to successful 26883'):
 assert v in s,v
w=(R/'.github/workflows/build-26884-iris-rawr.yml').read_text()
assert "      - 'TRIGGER_26884.txt'" in w and "      - 'TRIGGER_26883.txt'" not in w
assert 'test -f TRIGGER_26884.txt && grep -Fx' in w
assert w.count('bash build_26884_iris_rawr.sh')==1 and 'bash build_26883_iris_rawr.sh' not in w
assert "test \"$(sha256sum build_26883_iris_rawr.sh | awk '{print $1}')\" = '7799509f64c7f84c2223f7014dac925b2f6f31ed96667d754d0b1c0df29e979f'" in w
assert 'sha256sum -c 26883_GENERATED_BUILD_SHA256.txt' in w
assert 'sha256sum -c 26884_GENERATED_BUILD_SHA256.txt' in w
assert 'bash -n build_26884_iris_rawr.sh' in w
assert 'generate_26883_build.py .' in w and 'generate_26884_build.py .' in w
assert w.count("test \"$(find handoff_payload_26884 -type f | wc -l)\" -eq 3")==1
# Test exactly the same Bash trigger expression Actions will execute.
line=next(x.strip() for x in w.splitlines() if x.strip().startswith('test -f TRIGGER_26884.txt') and 'grep -Fx' in x)
assert 'RUN_26884_RAWR_HIGHLIGHT_OFF_SHARED_B_V1' in line
with tempfile.TemporaryDirectory(prefix='26884_real_trigger_') as td:
 for name,content,success in [('valid','RUN_26884_RAWR_HIGHLIGHT_OFF_SHARED_B_V1\n',True),('old','RUN_26883_SPEKTRA_FULL_FOV_1920_B_EARLY_WHITE_ON_OFF_V1\n',False),('wrong','RUN_26884_NOT_THE_REAL_BUILD\n',False),('missing',None,False)]:
  p=Path(td)/'TRIGGER_26884.txt'
  if content is None:p.unlink(missing_ok=True)
  else:p.write_text(content)
  test=subprocess.run(['bash','-c','set -euo pipefail\n'+line+'\n'],cwd=td,capture_output=True)
  assert (test.returncode==0)==success,name
# Exact successful 26883 runner is required; only development successor differs.
prior=R/'build_26883_iris_rawr.sh';current=R/'build_26884_iris_rawr.sh'
if prior.exists() and current.exists():
 assert hashlib.sha256(prior.read_bytes()).hexdigest()=='7799509f64c7f84c2223f7014dac925b2f6f31ed96667d754d0b1c0df29e979f'
 a=prior.read_text();b=current.read_text()
 stages=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay']
 def items(x):return [z.group(1) for z in re.finditer(r'\n([a-z_]+)\(\)\{',x) if z.group(1) in stages]
 assert items(a)==items(b)==stages
 for name in ('prepare_glslang','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','assemble','postbuild_proof'):
  def segment(x):
   q=x.index('\n'+name+'(){');r=x.index('\n}',q)+2;return x[q:r]
  assert segment(b)==segment(a.replace('26883','26884').replace('0.9726883','0.9726884')),(name,'unexpected compiler or freeze mechanics change')
 assert all(x in b for x in ('./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace'))
print('PASS 26884 exact historical 26883 runner, actual 17 stages and compiler/freeze commands, artifact references, prior validator ownership and isolated trigger negative tests')
