#!/usr/bin/env python3
"""Reference and workflow provenance, preserved successful 26965 historical prefix."""
import pathlib,hashlib,sys
R=pathlib.Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ref=R/'26965_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml';wf=R/'.github/workflows/build-26968-change-aware.yml'
assert sha(ref)=='23c64356dab6c179e1d37344d50e4735df091bfda842b992b54d45e55f76094d'
assert wf.is_file();original=ref.read_text();now=wf.read_text()
a='      - name: Checkout intended experimental branch'
b='      - name: Fetch only exact successful 26964 Actions artifact 14543555009'
assert a in original and a in now and b in original
prefix=original[original.index(a):original.index(b)]
assert prefix in now,'successful 26965 historical steps changed; must remain byte-identical'
assert '      - name: Fetch only exact successful 26965 Actions artifact 14564574142' in now
assert now.count('      - name: One mandatory real 26968 Android NDK dual-ABI Kotlin Java and full app assembleDebug')==1
assert now.count('      - name: Publish exactly one verified 26968 APK and actual compiled source TAR')==1
assert 'bash compile_26968_shaders.sh' in now and 'bash compile_26965_shaders.sh' in now
assert 'python3 -S verify_26904_v3_cmake_handoff.py --handoff' in now
assert 'bash compile_26904_shaders_v2.sh' in now
assert 'python3 -S test_26968_flicker_math.py --live' in now
assert 'python3 -S test_26968_shadows_menu.py --live' in now
assert 'TRIGGER_26968.txt' in now and 'branches:\n      - experimental-clean-photon-rebuild' in now
assert now.count('actions/upload-artifact@v4')==1 and 'photon_26968_outputs/' in now
assert 'app/.cxx' in now and "hashFiles('app/src/main/cpp/**/*'" in now
assert 'GITHUB_TOKEN: ${{ github.token }}' in now
print('PASS 26968 workflow preserves exact historical prefix, pinned current compilers, current source and correct unique trigger')
