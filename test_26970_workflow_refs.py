#!/usr/bin/env python3
"""26970 new workflow must contain exact successful 26968 historical prefix and mandatory real build gates."""
from pathlib import Path
import hashlib
R=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ref=R/'26968_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml'
wf=R/'.github/workflows/build-26970-change-aware.yml'
assert sha(ref)=='76a025b5b96ad09096769e0a24692fe0aafff93280aa2f187f59087b6002408c'
a='      - name: Checkout intended experimental branch'
b='      - name: Seal exact successful 26965 artifact and 26968 six-file B flicker and Shadows candidate'
c='      - name: Seal 26970 exact successful 26968 source, 2044 protected, and inherited historical workflow'
orig=ref.read_text();now=wf.read_text();assert a in orig and a in now and b in orig and c in now
assert orig[orig.index(a):orig.index(b)]==now[now.index(a):now.index('      - name: Preserve successful 26968 exact six-file handoff')],'successful 26968 historical prefix changed'
assert '      - TRIGGER_26970.txt' in now and '      - TRIGGER_26968.txt' not in now[:now.index(a)]
assert '      - experimental-clean-photon-rebuild' in now
assert 'python3 -S build_26968_incremental.py seal' in now
assert 'python3 -S test_26968_patches.py --payload' in now
assert 'Fetch ONLY exact successful 26968 Actions artifact 14601236629' in now
assert 'Compile exact successful 26968 current shaders before changed 26970 source' in now
assert 'bash compile_26968_shaders.sh' in now and 'bash compile_26970_shaders.sh' in now
assert 'python3 -S test_26970_glsl_preflight.py --live' in now
assert 'python3 -S test_26970_hdrq_native_preflight.py --live' in now
assert 'python3 -S test_26970_hdrq_native_preflight.py --payload' in now
assert 'bash compile_26904_shaders_v2.sh' in now and 'python3 -S verify_26904_v3_cmake_handoff.py --handoff' in now
assert 'python3 -S test_26903_modes.py .' in now
assert now.count('      - name: One mandatory real 26970 Android NDK dual-ABI Kotlin Java and full app assembleDebug')==1
assert now.count('      - name: Publish exactly one verified 26970 APK and actual compiled source TAR')==1
assert now.count('actions/upload-artifact@v4')==1
assert 'hashFiles(\'app/src/main/cpp/**/*\'' in now and 'app/.cxx' in now
assert 'GITHUB_TOKEN: ${{ github.token }}' in now
assert 'python3 -S build_26970_incremental.py finalize' in now
assert 'python3 -S test_26970_patches.py --payload' in now
print('PASS 26970 byte-identical inherited historical 26968 guarded workflow prefix, mandatory prior/current GLSL+NDK+assemble+artifact gates')
