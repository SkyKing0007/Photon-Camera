#!/usr/bin/env python3
"""Exact 40392745967 historical artifact-name failure regression.

The source of truth is the real generate_26881_build.py AST/function. This
fixture reproduces the exact original 26880 predecessor metadata, including
both the earlier 26879 artifact identity and original run-event SHA check.
The SHA-pinned real generated runner is checked against the exact full parent
runner, not against source text occurrence counts.
"""
from pathlib import Path
import ast,hashlib,sys,re
R=Path(__file__).resolve().parents[1]
src=(R/'generate_26881_build.py').read_text()
module=ast.parse(src)
functions=[n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='authority']
assert len(functions)==1
isolated=ast.Module(body=functions,type_ignores=[]);ast.fix_missing_locations(isolated)
namespace={'PARENT':'312bc023047ea13752efc46c6ad030e34d63441c807f55873266417fa113c21a'}
exec(compile(isolated,str(R/'generate_26881_build.py'),'exec'),namespace)
prior='[[ $(find "$BASE/app" -type f | wc -l) -eq 2001 ]]\nassert x[\'id\']==int(sys.argv[3]) and x[\'head_sha\']==sys.argv[2]\nassert x[\'id\']==12600241817\nassert x[\'name\']==\'photon-26879-b-50mp-neon-spektra-fov\'\nassert x[\'digest\']==\'sha256:bf060a690ee8792e0d3ab4fd58d25cabb2c0a2d35d6ffcd8a186508bb7132930\'\nmechanics_generated_script_sha256=985e5f03c620deef3a42b0b50424776e6208e85b62ff5d26e16a7579940d0c19\n'
now=namespace['authority'](prior)
for required in [
 "12658293287",
 "photon-26880-original-spektra125-rawwavelet-highlights",
 'sha256:5516d6deffd486de6d5dd18a51ebeb6d216883b7a4df325cc70ad09d80bee455',
 ' -eq 2015 ]]',
 'mechanics_generated_script_sha256=312bc023047ea13752efc46c6ad030e34d63441c807f55873266417fa113c21a',
 "x['head_sha']=='675d28299d9264baad1a549946661c57388e5cf8' and x.get('run_attempt',0)>=4",
]:
 assert now.count(required)==1,('missing exact successful 26880 authority proof',required,now)
for banned in ["photon-26880-b-50mp-neon-spektra-fov", "12600241817",' -eq 2001 ]]']:
 assert banned not in now,('stale prior authority remains',banned)
assert namespace['authority'](prior)==now,'nondeterministic successful-artifact migration'
# Permanent exact 40396314031 regression: R1 counted TEXT occurrences
# rather than the executable Gradle invocation in the owning Bash function.
# Extra identical text in a harmless comment is legal; a second invocation
# within the same stage must be rejected.
cmd='./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace'
fixture=f"compile_languages(){{\n {cmd} 2>&1 | tee compiler.log\n}}\n# reminder: {cmd}\n"
assert fixture.count(cmd)==2, 'R1 exact false-error condition not reproduced'
get_calls=lambda body:[line.strip() for line in body.splitlines() if re.match(r'^\s*\./gradlew\s',line)]
m=re.findall(r'(?ms)^compile_languages\(\)\{(.*?)^\}',fixture)
assert len(m)==1 and len(get_calls(m[0]))==1 and get_calls(m[0])[0].startswith(cmd)
unsafe=fixture.replace(' 2>&1 | tee compiler.log',f'\n {cmd} 2>&1 | tee compiler.log')
m=re.findall(r'(?ms)^compile_languages\(\)\{(.*?)^\}',unsafe)
assert len(m)==1 and len(get_calls(m[0]))==2, 'duplicate compiler invocation negative fixture not detected'
# The broken handoff fixture would silently keep the wrong name and must be rejected.
broken=prior.replace('26879','26880').replace("photon-26879-b-50mp-neon-spektra-fov","photon-26880-original-spektra125-rawwavelet-highlights")
assert "photon-26880-b-50mp-neon-spektra-fov" in broken
assert "photon-26880-original-spektra125-rawwavelet-highlights" not in broken
if len(sys.argv)>1:
 actual=Path(sys.argv[1]).resolve()
 runner=actual.read_text()
 parent=actual.with_name('build_26880_iris_rawr.sh')
 assert parent.is_file(),('missing ACTUAL successful 26880 runner',parent)
 predecessor=parent.read_text()
 assert hashlib.sha256(predecessor.encode()).hexdigest()=='312bc023047ea13752efc46c6ad030e34d63441c807f55873266417fa113c21a'
 assert 'GLSLANG_VERSION="16.5.0"' in runner
 assert 'PRE-BUILD SAFETY PROOF PASSED' in runner
 assert 'snapshot_live_authority_seeded' in runner
 stages=('verify_package','verify_scope','obtain_authority','make_candidate',
         'verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders',
         'compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages',
         'verify_native_glslang_handoff','compile_native','verify_candidate_patches',
         'prebuild_safety','assemble','postbuild_proof','clean_extract_replay')
 present=re.findall(r'(?m)^([a-z_]+)\(\)\{',runner)
 assert [x for x in present if x in stages]==list(stages),('17-stage order changed',present)
 def stage_body(script,name):
  matches=re.findall(r'(?ms)^'+re.escape(name)+r'\(\)\{(.*?)^\}',script)
  assert len(matches)==1,('missing/duplicate real stage function',name,len(matches))
  return matches[0]
 # Compile only the real executable command lines inside their actual stage,
 # not arbitrary mentions in comments, heredocs, or the runner's preflight assertions.
 # The historical successful runner may legitimately repeat the command text
 # elsewhere. 2015-file compiled prior is the authority, not text count one.
 commands={
  'compile_languages':'./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
  'compile_native':"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
  'assemble':'./gradlew :app:assembleDebug --stacktrace',
 }
 def actual_calls(body):
  return [line.strip() for line in body.splitlines() if re.match(r'^\s*\./gradlew\s',line)]
 for stage,command in commands.items():
  current=actual_calls(stage_body(runner,stage))
  inherited=actual_calls(stage_body(predecessor,stage))
  assert inherited,('prior successful stage contains no real compiler calls',stage)
  # Versioned output log filenames legitimately differ; executable Gradle
  # invocation, ABI targets, stream redirection and tee path ownership MUST NOT.
  normalized=[line.replace('$OUT/26881_','$OUT/26880_') for line in current]
  assert normalized==inherited,('modified real compiler command sequence',stage,current,inherited)
  assert sum(x.startswith(command) for x in current)==1,('missing/duplicate executable project compiler',stage,command,current)
 # The 40399946468 failure is reproduced: the real source generated
 # version 26881 log path while the correct predecessor wrote 26880 logs.
 sample_prior='./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26880_gradle_language_compilers.log"'
 sample_new=sample_prior.replace('26880_gradle','26881_gradle')
 assert sample_new!=sample_prior
 assert sample_new.replace('$OUT/26881_','$OUT/26880_')==sample_prior
 assert sample_new.replace('compileDebugKotlin','compileReleaseKotlin').replace('$OUT/26881_','$OUT/26880_')!=sample_prior
 assert (sample_new+'\n'+sample_new).count('./gradlew ')==2
 # New candidate belongs only in 26881 checks. The original vendor ABI,
 # altered highlight and 26880 history must be validated on historical bytes.
 for stage in ('make_candidate','compile_modified_runtime_shaders','clean_extract_replay'):
  frag=stage_body(runner,stage)
  if stage=='make_candidate':
   for required in ('verify_26880_spektra_abi.py "$BASE/app"',
                    'verify_26880_highlight_runtime_shader.py "$BASE"',
                    'regressions/26880_runtime_ownership_spektra.py "$H79" "$BASE"',
                    'regressions/26881_spektra_chroma_clip.py "$BASE" "$CAND"',
                    'verify_26881_expanded_glsl.py "$CAND"'):
    assert required in frag,('missing guarded active/historical semantic owner',stage,required)
  if stage=='compile_modified_runtime_shaders':
   assert 'verify_26881_expanded_glsl.py "$CAND" --compiler "$IRIS26864_GLSLANG"' in frag
   # R2 did not catch this real Bash set -u failure: H79 was declared local
   # in make_candidate; no later stage may access it as an unbound variable.
   assert '$H79' not in frag, 'cross-stage local H79 leaked into shader stage'
   assert 'verify_26880_runtime_glsl_scope.py "$WORK/historical_26879_from_26880" "$BASE"' in frag
  if stage=='clean_extract_replay':
   assert 'verify_26881_expanded_glsl.py "$exp"' in frag
   assert 'verify_26880_spektra_abi.py "$BASE/app"' in frag
 # Unedited high-risk mechanics must remain EXACT original implementation,
 # with only the version's output names advanced. Check whole function bodies.
 untouched=('prepare_glslang','compile_spektra_raw_shader','install_frozen_candidate_live',
            'compile_languages','verify_native_glslang_handoff','compile_native',
            'assemble','postbuild_proof')
 for stage in untouched:
  current=stage_body(runner,stage)
  old=stage_body(predecessor,stage)
  assert current.replace('26881','26880').replace('0.9726881','0.9726880')==old,('successful stage mechanics unexpectedly changed',stage)
 # Verify no stage-level commands escaped into the top-level script.
 # The successful predecessor defines the same 17 invoked stages at the end.
 calls='\n'+'\n'.join(stages)+'\n'
 assert runner.count(calls)==1 and predecessor.count(calls)==1,('stage invocation suffix missing/duplicated',)
 assert runner.split(calls,1)[1]==predecessor.split(calls,1)[1].replace('26880','26881'), 'unexpected top-level shell code after stage sequence'
 marker='\nobtain_authority(){'
 assert runner.count(marker)==1
 frag=stage_body(runner,'obtain_authority')
 for required in (
   '12658293287','photon-26880-original-spektra125-rawwavelet-highlights',
   '5516d6deffd486de6d5dd18a51ebeb6d216883b7a4df325cc70ad09d80bee455',
   ' -eq 2015 ]]','675d28299d9264baad1a549946661c57388e5cf8',
   'run_attempt',
 ):
  assert required in frag,('generated exact authority token missing',required)
 for forbidden in ('photon-26880-b-50mp-neon-spektra-fov',
                   'sha256:bf060a690ee8792e0d3ab4fd58d25cabb2c0a2d35d6ffcd8a186508bb7132930',
                   "'id':12600241817",' -eq 2001 ]]'):
  assert forbidden not in frag,('stale authority token in generated runner',forbidden)
 # Permanent reference-domain check: historical validators must keep their
 # REAL successful 26880 filenames and must never be substituted by invented
 # non-existent 26881 variants from a blind global-version replace.
 retired=(
  'verify_26881_native_shaders.py','verify_26881_spektra_abi.py',
  'verify_26881_rawr_shader_universe.py','verify_26881_runtime_glsl_scope.py',
  'verify_26881_highlight_runtime_shader.py',
  'regressions/26881_runtime_ownership_spektra.py',
  'regressions/26881_wr_no_fit_optional_wavelet.py',
 )
 executed='\n'.join(line for line in runner.splitlines()
                    if re.search(r'^\s*python3\s+-S\s',line))
 for old in retired:
  assert old not in executed,('stale fabricated historical validator reference',old)
 for historical in ('verify_26880_spektra_abi.py','verify_26880_runtime_glsl_scope.py',
                    'verify_26880_highlight_runtime_shader.py'):
  assert historical in executed,('inherited successful validator accidentally retired',historical)
 assert runner.count('regressions/26881_spektra_chroma_clip.py')>=1
 assert 'regressions/26877_superres_ownership.py' not in runner
 print('PASS R2 exact successful 26880 parent; executable per-stage compiler commands preserved; all 17 stages; historical/candidate ownership; no escaped stage execution')
print('PASS 26881 original 40392745967 artifact-name failure reproduced and corrected; exact parent/metadata and attempt-4 SHA proof retained')
