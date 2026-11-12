#!/usr/bin/env python3
"""26922 repeats byte-identical 26920 V5 real LK shader/SPIRV compiler invocations.
Historical 26920 source tested only against its own payload; 26922 live checked
against current 2038-file complete source. Regression for failed 26921 V1 replay.
"""
from pathlib import Path
import subprocess,hashlib
R=Path(__file__).resolve().parent
original=(R/'compile_26920_lk_shaders.sh').read_text()
old='python3 -S test_26920_source.py --live\n'
new=('python3 -S test_26920_source.py --payload\n'
     'python3 -S test_26921_guard.py --payload\n'
     'python3 -S build_26922_incremental.py regress\n')
assert original.count(old)==1
for gate in ('spirv-val --target-env vulkan1.1',
             'spirv-opt --target-env=vulkan1.1 -O',
             '"$COMPILER" -V --target-env vulkan1.1 -S comp',
             'python3 -S test_26920_vulkan_abi.py --live --compiled',
             'for variant in prod trace;',
             'for shader in lk_refine robust_photometric;'):
 assert gate in original,'historical shader compiler dropped gate: '+gate
candidate=original.replace(old,new,1)
assert candidate.replace(new,old,1)==original,'unexpected historical shader compiler modifications'
def manifest(name):
 return dict((p,h) for h,p in (line.split('  ',1) for line in (R/name).read_text().splitlines()))
a=manifest('26922_BASE_26921_FULL_APP.sha256')
b=manifest('26922_EXPECTED_FULL_APP.sha256')
allowed=set((R/'26922_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
assert len(a)==2038 and a.keys()==b.keys() and {p for p in a if a[p]!=b[p]}==allowed
for name in ('app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/alignment/shaders/lk_refine.comp',
             'app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/merge_wronski/shaders/robust_photometric.comp'):
 assert name not in allowed and a[name]==b[name]
 assert hashlib.sha256((R/name).read_bytes()).hexdigest()==a[name]
subprocess.run(['python3','-S','test_26920_source.py','--payload'],cwd=R,check=True)
subprocess.run(['python3','-S','test_26921_guard.py','--payload'],cwd=R,check=True)
subprocess.run(['python3','-S','build_26922_incremental.py','regress'],cwd=R,check=True)
out=R/'.photon_26922_lk_real_compiler.sh'
try:
 out.write_text(candidate)
 subprocess.run(['bash',str(out)],cwd=R,check=True)
finally:out.unlink(missing_ok=True)
print('PASS original real 26920 V5 LK prod/trace compilation/optimizer/ABI unchanged, historical version equality properly scoped')
