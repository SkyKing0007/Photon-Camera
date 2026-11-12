#!/usr/bin/env python3
"""Run 26920 V5's actual four-variant LK GLSL/SPIR-V compiler unchanged
except for the version-scoped historical source equality invocation.

26920's --live equality requires 26920 version/native bytes; it must NEVER
be used to certify the 26921 two-file runtime candidate. Keep the historical
check against its original sealed payload, require 26921 exact live equality,
and preserve every GLSL/SPIR-V command and descriptor-ABI test verbatim.
"""
from pathlib import Path
import hashlib, subprocess, sys
R=Path(__file__).resolve().parent
orig=R/'compile_26920_lk_shaders.sh'
s=orig.read_text()
old='python3 -S test_26920_source.py --live\n'
new=('python3 -S test_26920_source.py --payload\n'
     'python3 -S test_26921_guard.py --live\n'
     'python3 -S build_26921_incremental.py regress\n')
if s.count(old)!=1 or s.count('python3 -S test_26920_vulkan_abi.py --live')!=2:
    raise SystemExit('BLOCKED: historical 26920 shader compiler changed unexpectedly')
# Check all original compile/validation/reflection commands are identical.
for required in ('spirv-val --target-env vulkan1.1',
                 'spirv-opt --target-env=vulkan1.1 -O',
                 '"$COMPILER" -V --target-env vulkan1.1 -S comp',
                 'python3 -S test_26920_vulkan_abi.py --live --compiled',
                 'for variant in prod trace;',
                 'for shader in lk_refine robust_photometric;'):
    if required not in s:raise SystemExit('BLOCKED: missing inherited shader gate '+required)
effective=s.replace(old,new,1)
if effective.replace(new,old,1)!=s:raise SystemExit('BLOCKED: shader procedure differed')
# Verify the unchanged old candidate is still the parent of the current full
# manifest, and no 26920 shaders have been modified (independently of checks).
def manifest(p):
    return dict((name,h) for h,name in (line.split('  ',1) for line in p.read_text().splitlines()))
base=manifest(R/'26921_BASE_26920_FULL_APP.sha256')
cur=manifest(R/'26921_EXPECTED_FULL_APP.sha256')
allowed=set((R/'26921_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
if len(base)!=2038 or set(base)!=set(cur) or {p for p in base if base[p]!=cur[p]}!=allowed:
    raise SystemExit('BLOCKED: source change allowlist drift')
for p in ('app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/alignment/shaders/lk_refine.comp',
          'app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/merge_wronski/shaders/robust_photometric.comp'):
    if p in allowed or base[p]!=cur[p] or hashlib.sha256((R/p).read_bytes()).hexdigest()!=base[p]:
        raise SystemExit('BLOCKED: active inherited shader changed '+p)
subprocess.run(['python3','-S','test_26920_source.py','--payload'],cwd=R,check=True)
subprocess.run(['python3','-S','build_26921_incremental.py','regress'],cwd=R,check=True)
# Only version-scoped source identity line is adapted. No changed shader flags,
# compiler binaries, SPIR-V optimizers, reflection commands or generated names.
out=R/'.photon_26921_lk_original_compiler_with_current_authority.sh'
try:
    out.write_text(effective)
    subprocess.run(['bash',str(out)],cwd=R,check=True)
finally:
    out.unlink(missing_ok=True)
print('PASS 26921 actual 26920 V5 LK prod/trace compile identical except historical 26920 payload versus exact 26921 live authority guard')
