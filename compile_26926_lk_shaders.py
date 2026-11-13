#!/usr/bin/env python3
"""26926: exact successful 26923 LK real shader compiler; current-source gate only is 26926.

Keep all 26920 V5 pinned glslang / spirv-val / spirv-opt / prod+trace /
Vulkan descriptor reflection commands intact. Historical 26920/26921 regressions
remain on their original payload. Original 26923 historical live run happens
before 26926 source overlay, in the unchanged historical Actions replay step.
Never use the current 26926 source with 26923's full-index source equality gate.
"""
from pathlib import Path
import hashlib,sys
R=Path(__file__).resolve().parent
OLD=R/'compile_26923_lk_shaders.py'
OLD26920=R/'compile_26920_lk_shaders.sh'

def git_blob_sha(data):
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
# Exact Git blob bytes from successful 26923 V4 commit 6513b326db863fd021da5796f9eefdf52a14b329.
assert OLD.is_file() and git_blob_sha(OLD.read_bytes())=='e08bafd95acf1e85b9385710b8633189561e4afb', 'original successful 26923 LK wrapper changed'
assert OLD26920.is_file() and git_blob_sha(OLD26920.read_bytes())=='222b8cee12924416159ee84123c540c39d66a1e1', 'original real 26920 LK/SPIR-V compiler changed'
s=OLD.read_text()
old='build_26923_incremental.py'; new='build_26926_incremental.py'
# Exactly 2 source-era assertions: preflight Python and generated shell.
# All actual real compiler flags, source filenames, output SPIR-V and ABI tests stay byte-identical.
assert s.count(old)==2 and s.count('python3 -S test_26920_source.py --payload')==1
assert s.count('python3 -S test_26921_guard.py --payload')==1
assert s.count('compile_26920_lk_shaders.sh')==1
assert s.count('test_26920_vulkan_abi.py')==1, 'original wrapped shader ABI reflection changed'
repaired=s.replace(old,new)
assert repaired.replace(new,old)==s
assert repaired.count('build_26923_incremental.py')==0 and repaired.count(new)==2
for needle in ("'spirv-val --target-env vulkan1.1'", "'spirv-opt --target-env=vulkan1.1 -O'", "'for variant in prod trace;'", "'for shader in lk_refine robust_photometric;'", "'python3 -S test_26920_vulkan_abi.py --live --compiled'"):
    assert needle in repaired, ('real 26920 compiler/ABI contract lost',needle)
assert 'python3 -S test_26920_source.py --live\n' in OLD26920.read_text()
if len(sys.argv)==2 and sys.argv[1]=='--preflight':
    print('PASS exact 26923 V4 and 26920 V5 pinned historical LK compiler SHA, both source-era replacements and all real compiler gates; no shaders compiled in preflight')
elif len(sys.argv)==1:
    # The actual successful 26923 wrapper is executed unchanged except the
    # two strictly source-era-dependent calls. It still compiles & reflects
    # both real production/trace 26920 Vulkan shaders on the 26926 candidate.
    exec(compile(repaired,str(OLD),'exec'),{'__name__':'__main__','__file__':str(OLD)})
    print('PASS 26926 source-matched 26923 actual full LK shader/SPIR-V compilation and ABI reflection')
else:
    raise SystemExit('Usage: python3 -S compile_26926_lk_shaders.py [--preflight]')
