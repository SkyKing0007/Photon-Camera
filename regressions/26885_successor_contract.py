#!/usr/bin/env python3
"""26885 permanent source/trigger/runner regression on EXACT 26884 mechanics."""
from pathlib import Path
import ast,hashlib,re,sys,tempfile,subprocess
R=Path(__file__).resolve().parents[1]
g=R/'generate_26885_build.py';s=g.read_text();ast.parse(s)
assert "prior_sha=='f8aff63b074ee6195d6b137858ad5a3f23cb149a40c9f72cb69b51f315b4679f'" in s
assert "original.replace('26884','26885')" in s
for k in ('12747046415','40529418596','fb905234c419b0f1592c941d702531494e64f8fa','f34b031585f35dd5a11e494483ac1e99884fe10307861ffa05f729e5b849ccc1','83a5fecf3dbb3d9669a68df84bd374178c4493dfabbf2fb0cf474cce9a135d33'):
 assert k in s,('missing authority',k)
for stage in ('verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','compile_modified_runtime_shaders','verify_candidate_patches','prebuild_safety','clean_extract_replay'):
 assert "edit('"+stage+"'," in s,stage
assert not any("edit('"+n+"'," in s for n in ['prepare_glslang','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','assemble','postbuild_proof'])
w=(R/'.github/workflows/build-26885-iris-rawr.yml').read_text()
assert "      - 'TRIGGER_26885.txt'" in w and "      - 'TRIGGER_26884.txt'" not in w
assert 'test "$(sha256sum build_26884_iris_rawr.sh | awk' in w
assert 'sha256sum -c 26884_GENERATED_BUILD_SHA256.txt' in w and 'sha256sum -c 26885_GENERATED_BUILD_SHA256.txt' in w
assert w.count('bash build_26885_iris_rawr.sh')==1 and w.count('bash build_26884_iris_rawr.sh')==0
assert 'python3 -S stage_26885_root.py' in w and 'python3 -S generate_26885_build.py .' in w
line=next(x.strip() for x in w.splitlines() if x.strip().startswith('test -f TRIGGER_26885.txt') and 'grep -Fx' in x)
with tempfile.TemporaryDirectory(prefix='26885_real_trigger_') as td:
 for content,ok in [('RUN_26885_B_ON_WRONSKI_RGB_CHROMA_CONSISTENCY_V1\n',True),('RUN_26884_RAWR_HIGHLIGHT_OFF_SHARED_B_V1\n',False),('RUN_26885_WRONG\n',False),(None,False)]:
  p=Path(td)/'TRIGGER_26885.txt'
  if content is None:p.unlink(missing_ok=True)
  else:p.write_text(content)
  t=subprocess.run(['bash','-c','set -euo pipefail\n'+line+'\n'],cwd=td,capture_output=True)
  assert (t.returncode==0)==ok,content
prior=R/'build_26884_iris_rawr.sh';current=R/'build_26885_iris_rawr.sh'
if prior.exists() and current.exists():
 a=prior.read_text();b=current.read_text()
 assert hashlib.sha256(a.encode()).hexdigest()=='f8aff63b074ee6195d6b137858ad5a3f23cb149a40c9f72cb69b51f315b4679f'
 stages=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay']
 found=lambda t:[z.group(1) for z in re.finditer(r'\n([a-z_]+)\(\)\{',t) if z.group(1) in stages]
 assert found(a)==found(b)==stages
 for name in ('prepare_glslang','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','assemble','postbuild_proof'):
  def block(text):
   q=text.index('\n'+name+'(){');t=text.index('\n}',q)+2;return text[q:t]
  assert block(b)==block(a.replace('26884','26885').replace('0.9726884','0.9726885')),name
 for command in ('./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace'):
  assert command in a and command in b
 assert 'verify_26884_semantics.py "$H83" "$BASE"' in b
 assert 'verify_26885_semantics.py "$BASE" "$CAND"' in b
 assert 'verify_26885_expanded_glsl.py "$CAND" --compiler "$IRIS26864_GLSLANG"' in b
 assert 'PRE-BUILD SAFETY PROOF PASSED' in b and 'snapshot_live_authority_seeded' in b
 assert 'regressions/26877_superres_ownership.py' not in b
print('PASS 26885 exact 26884 runner mechanics/stages/compiler+freeze continuity, source-domain and trigger negative tests')
