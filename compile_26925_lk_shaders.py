#!/usr/bin/env python3
"""Clone the SUCCESSFUL 26920 real pinned LK prod/trace compiler exactly;
only historical version predicates are scoped to their immutable payload,
with new live 26925 source+ABI gates executed in addition. No compiler skipped.
"""
from pathlib import Path
import subprocess,hashlib
R=Path(__file__).resolve().parent
orig=(R/'compile_26920_lk_shaders.sh').read_text()
old='python3 -S test_26920_source.py --live\n'
new=('python3 -S test_26920_source.py --payload\n'
     'python3 -S test_26921_guard.py --payload\n'
     'python3 -S build_26925_incremental.py regress\n')
assert orig.count(old)==1
trans=orig.replace(old,new,1)
old1='python3 -S test_26920_vulkan_abi.py --live\n'
new1=('python3 -S test_26920_vulkan_abi.py --payload\n'
      'python3 -S test_26925_shader_shadow.py --live\n')
assert trans.count(old1)==1
trans=trans.replace(old1,new1,1)
old2='python3 -S test_26920_vulkan_abi.py --live --compiled'
new2=('python3 -S test_26920_vulkan_abi.py --payload --compiled')
assert trans.count(old2)==1
trans=trans.replace(old2,new2,1)
for required in ('spirv-val --target-env vulkan1.1','spirv-opt --target-env=vulkan1.1 -O',
                 '"$COMPILER" -V --target-env vulkan1.1 -S comp',
                 'for variant in prod trace;','for shader in lk_refine robust_photometric;'):
 assert required in orig and required in trans,'successful 26920 real compiler stage removed: '+required
assert trans.replace(new,old,1).replace(new1,old1,1).replace(new2,old2,1)==orig
# Catch accidentally mutating the two original/vendor LK/robustness GPU shader bytes.
def parse(name):return dict((p,h) for h,p in (line.split('  ',1) for line in (R/name).read_text().splitlines()))
a,b=parse('26925_BASE_26923_FULL_APP.sha256'),parse('26925_EXPECTED_FULL_APP.sha256')
for p in ('app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/alignment/shaders/lk_refine.comp',
          'app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/merge_wronski/shaders/robust_photometric.comp'):
 assert a[p]==b[p] and hashlib.sha256((R/p).read_bytes()).hexdigest()==a[p],p
for cmd in (["python3","-S","test_26920_source.py","--payload"],["python3","-S","test_26921_guard.py","--payload"],["python3","-S","build_26925_incremental.py","regress"]):
 subprocess.run(cmd,cwd=R,check=True)
file=R/'.photon_26925_lk_real_compiler.sh'
try:
 file.write_text(trans)
 subprocess.run(['bash',str(file)],cwd=R,check=True)
finally:file.unlink(missing_ok=True)
src=(R/'photon_26920_outputs/26920_LK_GLSL_SPIRV_REAL_COMPILER.txt').read_text()
assert '16.5.0' in src
out=R/'photon_26925_outputs';out.mkdir(exist_ok=True)
(out/'26925_PINNED_LK_SPIRV_REAL_COMPILER.txt').write_text('PASS original 26920 real LK prod/trace SPIR-V compiler unchanged; historical source tests scoped to original immutable payload, new live 26925 owners verified\n'+src)
print('PASS 26925 original LK/robust production+trace shaders real 16.5.0, SPIR-V optimizer and validator, protected source hash')
