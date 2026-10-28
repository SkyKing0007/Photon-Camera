#!/usr/bin/env python3
"""Permanent 26885 failed CMake/history regression, extended across 26886 stages.

All 26880 historical predicates run on real exact 26884 CMake, never 26886
candidate or 26885 CMake. Original validator code and compiler invocation
are retained unchanged; historical 26885 regression runs on actual H84/BASE.
"""
from pathlib import Path
import hashlib,re,sys,shlex
assert len(sys.argv)==6,'usage: historical26884 successful26885 candidate26886 exact26885runner generated26886runner'
H84,B,C,OLD,NEW=map(Path,sys.argv[1:]);sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
rel='app/src/main/cpp/iris26864/Iris26864VendorRawr.cmake'
assert sha(H84/rel)=='e897cba110ccd5a4326c774f3d247282181c409488d82745ac3a63ada25ab409'
assert sha(B/rel)==sha(C/rel)=='8fd4ca201b80a70a662f3828a2579e2f6cbd291cb62a8ef1709c4a4c107cfc94'
assert sha(OLD)=='2138db01cbfb3a8421c12e54ba29d4f0a893d1cdd4a219ee34a40a4dc0c54379'
s=OLD.read_text();t=NEW.read_text();stages=('make_candidate','compile_modified_runtime_shaders','clean_extract_replay')
def block(txt,name):
 a=txt.index('\n'+name+'(){')+1;b=txt.index('\n}',a)+2;return txt[a:b]
for name in stages:
 old=block(s,name);new=block(t,name)
 a=[x for x in old.splitlines() if 'python3 -S verify_26880_rawr_shader_universe.py' in x]
 b=[x for x in new.splitlines() if 'python3 -S verify_26880_rawr_shader_universe.py' in x]
 expected_domain=('"$H84/app"' if name=='make_candidate' else '"$WORK/historical_26884_from_26885/app"')
 assert len(a)==len(b)==1 and '"$BASE/app"' in a[0] and expected_domain in b[0]
 normalized=b[0].replace(expected_domain,'"$BASE/app"',1)
 assert normalized==a[0].replace('26885','26886') or normalized==a[0],(name,'unexpected historical command/options change')
 assert 'regressions/26886_historical_scope_all_stages.py' in new
 assert 'regressions/26885_actions_40604341240_historical_scope.py' in new
 # Actions 40623130600: actual malformed `"$H84 "$BASE"` must never be generated.
 legacy=[line.strip() for line in new.splitlines() if 'python3 -S regressions/26885_actions_40604341240_historical_scope.py' in line]
 assert len(legacy)==1,(name,'inherited historical invocation missing/duplicated',legacy)
 hist_var='$H84' if name=='make_candidate' else '$WORK/historical_26884_from_26885'
 expected=['python3','-S','regressions/26885_actions_40604341240_historical_scope.py',hist_var,'$BASE','$ROOT/build_26885_iris_rawr.sh']
 assert shlex.split(legacy[0])==expected,(name,'bad historical validator shell tokenization',legacy[0])
 try: shlex.split('python3 -S regressions/26885_actions_40604341240_historical_scope.py "$H84 "$BASE" "$ROOT/build_26885_iris_rawr.sh"')
 except ValueError: pass
 else: raise AssertionError('40623130600 malformed shell quoting was not reproduced')
 assert 'regressions/26885_chroma_controls.py' in new
 if name=='compile_modified_runtime_shaders':
  def multiline(block,needle):
   ls=block.splitlines();idx=next(i for i,l in enumerate(ls) if needle in l)
   ret=[]
   while True:
    ret.append(ls[idx]);
    if not ls[idx].rstrip().endswith('\\'):break
    idx+=1;assert idx<len(ls)
   return '\n'.join(ret)
  for flag in ('--compile','--spirv-val','--spirv-opt','--out'):
   assert flag in multiline(new,'python3 -S verify_26880_rawr_shader_universe.py')
for n in ('prepare_glslang','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','assemble','postbuild_proof'):
 assert block(s,n).replace('26885','26886').replace('0.9726885','0.9726886')==block(t,n),('original compiler/freeze/assemble drifted',n)
assert 'verify_26886_expanded_glsl.py "$CAND" --compiler "$IRIS26864_GLSLANG"' in t
assert 'PRE-BUILD SAFETY PROOF PASSED' in t
print('PASS 26886 exact 26885 V2 CMake mismatch regression preserved across candidate, real shader compile, clean-extract; historical validators untouched')
