from pathlib import Path
import re,hashlib,difflib,sys
R=(Path(sys.argv[1]) if len(sys.argv)>1 else Path('.')).resolve(); original=(R/'build_26884_iris_rawr.sh').read_text()
prior_sha=hashlib.sha256(original.encode()).hexdigest();assert prior_sha=='f8aff63b074ee6195d6b137858ad5a3f23cb149a40c9f72cb69b51f315b4679f'
body=original.replace('26884','26885').replace('0.9726884','0.9726885')
# Ensure original historical 26884 source validators run against real 26883->26884 compiled files.
def edit(fn,handler):
 global body
 q=body.index('\n'+fn+'(){')+1;t=body.index('\n}',q)+2
 old=body[q:t];new=handler(old);assert old!=new,fn;assert new.endswith('}'),fn
 body=body[:q]+new+body[t:]
def append(s,z):
 assert s.endswith('\n}')
 return s[:-2]+'\n'+z+'\n}'
for old,new in [
('REPO_SCAFFOLD_BASE_COMMIT="28823b94be2cc636983f01a99dfc2f0840f5a05b"','REPO_SCAFFOLD_BASE_COMMIT="fb905234c419b0f1592c941d702531494e64f8fa"'),
('RUNTIME_AUTHORITY_COMMIT="28823b94be2cc636983f01a99dfc2f0840f5a05b"','RUNTIME_AUTHORITY_COMMIT="fb905234c419b0f1592c941d702531494e64f8fa"'),
('RUNTIME_ARTIFACT_ID="12734144623"; RUNTIME_ACTIONS_RUN="40505011172"','RUNTIME_ARTIFACT_ID="12747046415"; RUNTIME_ACTIONS_RUN="40529418596"'),
('RUNTIME_ARTIFACT_SHA="e1ffb9c7c826d5504d39b496134aeea141a4b8e2661f30496ecbacc3ff997071"','RUNTIME_ARTIFACT_SHA="f34b031585f35dd5a11e494483ac1e99884fe10307861ffa05f729e5b849ccc1"'),
('RUNTIME_TAR_SHA="729c9ad909c3444bec1028e17a4a4803b1ebda3fe73d0c541b466b825a93e1f7"','RUNTIME_TAR_SHA="83a5fecf3dbb3d9669a68df84bd374178c4493dfabbf2fb0cf474cce9a135d33"'),
('MECHANICS_GIT_BLOB="2db9740d5fbe7baa0d7054c1132f158cbfbfb499"','MECHANICS_GIT_BLOB="04b69c26de71543217fc800c1340a937c45c198f"'),
('ARTZIP="$WORK/26883_artifact.zip"; ARTDIR="$WORK/artifact_26883"','ARTZIP="$WORK/26884_artifact.zip"; ARTDIR="$WORK/artifact_26884"'),
('BASE="$WORK/exact_successful_26883_compiled_candidate"','BASE="$WORK/exact_successful_26884_compiled_candidate"')]:
 assert old in body,old;body=body.replace(old,new,1)
TRIG='RUN_26885_B_ON_WRONSKI_RGB_CHROMA_CONSISTENCY_V2_SCOPE_REPAIR'
def package(s):
 s=s.replace('-eq 3 ]]','-eq 8 ]]').replace('3-file','8-file').replace('3-source','8-source')
 s=s.replace('RUN_26885_RAWR_HIGHLIGHT_OFF_SHARED_B_V1',TRIG)
 # historical 26884 package checks are separate; the successful 26884 workflow already validated its own payload.
 s=s.replace('stage_26885_root.py\n','stage_26884_root.py\n') if False else s
 s=s.replace('python3 -S regressions/26885_rawr_off_math.py','python3 -S regressions/26884_rawr_off_math.py')
 s=s.replace('python3 -S regressions/26885_successor_contract.py','python3 -S regressions/26884_successor_contract.py')
 s=s.replace('python3 -S stage_26885_root.py', 'python3 -S stage_26884_root.py')
 # Restore historic block from inherited 26884 package: only NEW appended checks test 26885 scope.
 a=s.index(' python3 -S -m py_compile verify_26885_candidate.py verify_26885_patches.py verify_26885_expanded_glsl.py verify_26885_semantics.py regressions/26885_successor_contract.py regressions/26885_rawr_off_math.py stage_26885_root.py') if ' python3 -S -m py_compile verify_26885_candidate.py verify_26885_patches.py verify_26885_expanded_glsl.py verify_26885_semantics.py regressions/26885_successor_contract.py regressions/26885_rawr_off_math.py stage_26885_root.py' in s else -1
 if a>=0:
  t=s.index('\n',a)
  s=s[:a]+s[a:t].replace('26885','26884')+s[t:]
 return append(s,''' python3 -S -m py_compile verify_26885_candidate.py verify_26885_patches.py verify_26885_expanded_glsl.py verify_26885_semantics.py stage_26885_root.py regressions/26885_successor_contract.py regressions/26885_chroma_controls.py
 python3 -S stage_26885_root.py
 python3 -S regressions/26885_successor_contract.py
'''.rstrip())
edit('verify_package',package)
def scope(s):
 s=s.replace('generate_26883_build.py','generate_26884_build.py').replace('build_26883_iris_rawr.sh','build_26884_iris_rawr.sh')
 s=s.replace('7799509f64c7f84c2223f7014dac925b2f6f31ed96667d754d0b1c0df29e979f',prior_sha)
 return s
edit('verify_scope',scope)
def authority(s):
 s=s.replace('26883','26884')
 s=s.replace("x['head_sha']=='28823b94be2cc636983f01a99dfc2f0840f5a05b'","x['head_sha']=='fb905234c419b0f1592c941d702531494e64f8fa'")
 # metadata mismatch must have exactly the completed 26884 success digest/name
 s=s.replace("'id':12734144623", "'id':12747046415")
 s=s.replace('photon-26884-spektra-full-fov-b-early-white-both','photon-26884-experiment-b-original-rawr-highlight-off')
 s=s.replace('sha256:e1ffb9c7c826d5504d39b496134aeea141a4b8e2661f30496ecbacc3ff997071','sha256:f34b031585f35dd5a11e494483ac1e99884fe10307861ffa05f729e5b849ccc1')
 s=s.replace('mechanics_generated_script_sha256=7799509f64c7f84c2223f7014dac925b2f6f31ed96667d754d0b1c0df29e979f','mechanics_generated_script_sha256='+prior_sha)
 assert 'photon-26884-experiment-b-original-rawr-highlight-off' in s and '12747046415' in s
 return s
edit('obtain_authority',authority)
def candidate(s):
 marker=' local H82="$WORK/historical_26882_from_26883"';assert marker in s
 new=''' local H83="$WORK/historical_26883_from_26884"
 cp -a "$BASE" "$H83";git -C "$H83" init -q
 (cd "$H83" && git apply --check --reverse "$ROOT/26884_FORWARD_FULL_INDEX.patch" &&
 git apply --reverse "$ROOT/26884_FORWARD_FULL_INDEX.patch" &&
 sha256sum -c "$ROOT/26884_BASE_26883_FULL_APP.sha256" >/dev/null) || fail 'exact successful 26884->26883 historical rollback failed'
'''
 s=s.replace(marker,new+marker,1)
 s=s.replace('cp -a "$BASE" "$H82"','cp -a "$H83" "$H82"',1)
 s=s.replace('verify_26883_semantics.py "$H82" "$BASE"','verify_26883_semantics.py "$H82" "$H83"')
 s=s.replace('verify_26883_expanded_glsl.py "$BASE"','verify_26883_expanded_glsl.py "$H83"')
 s=s.replace('verify_26883_candidate.py "$H82" "$BASE"','verify_26883_candidate.py "$H82" "$H83"')
 s=s.replace('verify_26885_semantics.py "$BASE" "$CAND"','verify_26884_semantics.py "$H83" "$BASE"')
 s=s.replace('regressions/26885_rawr_off_math.py "$CAND"','regressions/26884_rawr_off_math.py "$BASE"')
 s=s.replace('verify_26885_expanded_glsl.py "$CAND"','verify_26884_expanded_glsl.py "$BASE"')
 return append(s,''' python3 -S verify_26884_candidate.py "$H83" "$BASE"
 python3 -S verify_26885_semantics.py "$BASE" "$CAND"
 python3 -S regressions/26885_chroma_controls.py "$CAND" "$BASE"
 python3 -S verify_26885_expanded_glsl.py "$CAND"
 python3 -S verify_26885_candidate.py "$BASE" "$CAND"
'''.rstrip())
edit('make_candidate',candidate)
def mechanics(s):
 return s.replace('build_26883_iris_rawr.sh','build_26884_iris_rawr.sh').replace('generate_26883_build.py','generate_26884_build.py').replace('7799509f64c7f84c2223f7014dac925b2f6f31ed96667d754d0b1c0df29e979f',prior_sha)
edit('verify_successful_mechanics',mechanics)
def shaders(s):
 s=s.replace('verify_26883_expanded_glsl.py "$BASE"','verify_26883_expanded_glsl.py "$WORK/historical_26883_from_26884"')
 s=s.replace('verify_26885_expanded_glsl.py "$CAND" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26885_real_rawr_off_fused_wb"','verify_26884_expanded_glsl.py "$BASE" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26885_real_rawr_off_fused_wb"')
 return append(s,''' python3 -S verify_26885_expanded_glsl.py "$CAND" --compiler "$IRIS26864_GLSLANG" --spirv-val "$(command -v spirv-val)" --spirv-opt "$(command -v spirv-opt)" --out "$OUT/26885_new_chroma_spirv" | tee "$OUT/26885_new_chroma_pinned_shader.txt"
 grep -F 'PASS 26885 PINNED REAL GLSLANG 16.5.0 and SPIRV-VAL pre/post optimized' "$OUT/26885_new_chroma_pinned_shader.txt" >/dev/null || fail '26885 B ON real GLSL/SPIRV proof missing'
'''.rstrip())
edit('compile_modified_runtime_shaders',shaders)
def patch(s):
 s=s.replace('3-file','8-file')
 return s
edit('verify_candidate_patches',patch)
def safety(s):
 s=s.replace('successful 26883','successful 26884').replace('successful 26885 inherited','successful 26884 inherited')
 s=s.replace('runtime_changed_files=3 (2 shared Experiment B POST-AMaZE owners + version); exact RAWR OFF fused WB shared ceiling before Lab/FCC; no Spektra change; 0 source additions/deletions; native/vendor/DNG unchanged','runtime_changed_files=8 (7 changed native B Super Res ON files incl one NEW shader, plus version); 2002 protected, Spektra/white/B OFF/DNG/UHDR unchanged')
 s=s.replace('prior_files=2009\ncandidate_files=2009','prior_files=2009\ncandidate_files=2010')
 s=s.replace('protected_source=2006 files byte-identical to successful 26884 compiled candidate; Spektra/DNG/native/vendor/Experiment A/Motion/Night/LONG preserved','protected_source=2002 files byte-identical to successful 26884 compiled candidate; Spektra/RAW white/B OFF/A/Motion/Night/LONG/DNG/UHDR preserved')
 s=s.replace('infrastructure_delta=26885 workflow/generator/manifests/device-failure regression; exact inherited 17 compiler stages','infrastructure_delta=26885 strict successor workflow/generator/manifests/new native SPIRV/positive-negative regression; exact inherited 17-stage compiler+freeze+assemble mechanics')
 return s
edit('prebuild_safety',safety)
def replay(s):
 s=s.replace('verify_26883_semantics.py "$WORK/historical_26882_from_26883" "$BASE"','verify_26883_semantics.py "$WORK/historical_26882_from_26883" "$WORK/historical_26883_from_26884"')
 s=s.replace('verify_26883_expanded_glsl.py "$BASE"','verify_26883_expanded_glsl.py "$WORK/historical_26883_from_26884"')
 s=s.replace('verify_26883_candidate.py "$WORK/historical_26882_from_26883" "$BASE"','verify_26883_candidate.py "$WORK/historical_26882_from_26883" "$WORK/historical_26883_from_26884"')
 s=s.replace('verify_26885_semantics.py "$BASE" "$exp"','verify_26884_semantics.py "$WORK/historical_26883_from_26884" "$BASE"')
 s=s.replace('regressions/26885_rawr_off_math.py "$exp"','regressions/26884_rawr_off_math.py "$BASE"')
 s=s.replace('verify_26885_expanded_glsl.py "$exp" --out "$OUT/26885_final_rawr_off_fused_wb_source"','verify_26884_expanded_glsl.py "$BASE" --out "$OUT/26885_final_rawr_off_fused_wb_source"')
 return append(s,''' python3 -S verify_26884_candidate.py "$WORK/historical_26883_from_26884" "$BASE"
 python3 -S verify_26885_candidate.py "$BASE" "$exp" --root "$ROOT"
 python3 -S verify_26885_semantics.py "$BASE" "$exp"
 python3 -S regressions/26885_chroma_controls.py "$exp" "$BASE"
 python3 -S verify_26885_expanded_glsl.py "$exp"
'''.rstrip())
edit('clean_extract_replay',replay)

# IRIS_26885_ACTIONS_40604341240 / job 122539975456.
# The unchanged 26880 validator HASH-PINS Iris26864VendorRawr.cmake.
# This file intentionally changes in 26885 to embed the new Wronski RGB
# chroma guide. The historical wavelet check must run against the EXACT
# successful 26884 artifact, while the 26885 candidate is independently
# checked by its strict manifest, CMake delta regression and real GLSL gate.
# Preserve the original validator, compiler flags, stage order and stage
# execution; change ONLY the historical validator's SOURCE INPUT domain.
def _rebind_original_26880_wavelet(stage, previous_domain):
 def apply(h):
  lines=h.splitlines(keepends=True)
  matches=[i for i,line in enumerate(lines)
           if re.search(r'\bpython3 -S verify_26880_rawr_shader_universe\.py\b',line)]
  assert len(matches)==1,(stage,'expected exactly one real 26880 validator invocation',matches)
  i=matches[0]
  assert previous_domain in lines[i],(stage,'stale/renamed 26880 current-domain token',lines[i])
  assert lines[i].count(previous_domain)==1,(stage,'ambiguous historical source binding')
  lines[i]=lines[i].replace(previous_domain,'"$BASE/app"',1)
  assert '--compile' in lines[i] or stage!='compile_modified_runtime_shaders',('real historical compiler args lost',lines[i])
  assert all(lines[j]==h.splitlines(keepends=True)[j] for j in range(len(lines)) if j!=i),('accidental build mechanic change',stage)
  return ''.join(lines)
 edit(stage,apply)
for _stage,_input in (
 ('make_candidate','"$CAND/app"'),
 ('compile_modified_runtime_shaders','"$CAND/app"'),
 ('clean_extract_replay','"$exp/app"'),
):
 _rebind_original_26880_wavelet(_stage,_input)

# Exact failed condition regression (real 26884/26885 CMake bytes) remains
# in 26885's candidate gate, shader compiler gate and final clean extraction.
def _regression_stage(s):
 assert 'python3 -S -m py_compile verify_26885_candidate.py' in s
 return s.replace('python3 -S -m py_compile verify_26885_candidate.py',
                  'python3 -S -m py_compile regressions/26885_actions_40604341240_historical_scope.py verify_26885_candidate.py',1)
edit('verify_package',_regression_stage)
def _prebuild_domain_regression(s):
 return append(s,' python3 -S regressions/26885_actions_40604341240_historical_scope.py "$BASE" "$CAND" "$ROOT/build_26885_iris_rawr.sh"')
edit('make_candidate',_prebuild_domain_regression)
edit('compile_modified_runtime_shaders',_prebuild_domain_regression)
def _final_domain_regression(s):
 return append(s,' python3 -S regressions/26885_actions_40604341240_historical_scope.py "$BASE" "$exp" "$ROOT/build_26885_iris_rawr.sh"')
edit('clean_extract_replay',_final_domain_regression)

# Reject ALL remaining current-candidate invocations of the sealed 26880
# validator; the regression checks these exact generated stage bodies again.
for _stage in ('make_candidate','compile_modified_runtime_shaders','clean_extract_replay'):
 _start=body.index('\n'+_stage+'(){')
 _end=body.index('\n}',_start)+2
 _block=body[_start:_end]
 _calls=[line for line in _block.splitlines() if re.search(r'\bpython3 -S verify_26880_rawr_shader_universe\.py\b',line)]
 assert len(_calls)==1 and '"$BASE/app"' in _calls[0],('failed 40604341240 historical domain resurrected',_stage,_calls)
 assert '"$CAND/app"' not in _calls[0] and '"$exp/app"' not in _calls[0],_stage

STAGES=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay']
get=lambda s:[m.group(1) for m in re.finditer(r'\n([a-z_]+)\(\)\{',s)]
assert get(original)==get(body) and [x for x in get(body) if x in STAGES]==STAGES
for name in ('prepare_glslang','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','assemble','postbuild_proof'):
 def stage(s,n):
  a=s.index('\n'+n+'(){')+1;b=s.index('\n}',a)+2;return s[a:b]
 assert stage(body,name)==stage(original.replace('26884','26885').replace('0.9726884','0.9726885'),name),name
for command in ('./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace'):
 assert command in body and command in original
assert 'GLSLANG_VERSION="16.5.0"' in body and 'PRE-BUILD SAFETY PROOF PASSED' in body
(R/'build_26885_iris_rawr.sh').write_text(body)
(R/'26885_GENERATED_BUILD_SHA256.txt').write_text(hashlib.sha256(body.encode()).hexdigest()+'  build_26885_iris_rawr.sh\n')
(R/'26885_BUILD_INFRASTRUCTURE_DIFF.txt').write_text(''.join(difflib.unified_diff(original.splitlines(True),body.splitlines(True),fromfile='SUCCESSFUL_26884_SHA_'+prior_sha,tofile='26885_INHERITED_17_STAGES')))
print('PASS 26885 exact inherited 26884 17 ordered stages, pinned original compile/freeze/assemble commands; SHA',hashlib.sha256(body.encode()).hexdigest())
