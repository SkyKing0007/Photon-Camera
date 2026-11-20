#!/usr/bin/env python3
"""Successor workflow preserves every executed 26968 historical prerequisite."""
import pathlib,hashlib
R=pathlib.Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=R/'26968_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml';q=R/'26968_SUCCESSFUL_EXECUTED_BUILDER_REFERENCE.py';w=R/'.github/workflows/build-26969-change-aware.yml'
assert sha(p)=='76a025b5b96ad09096769e0a24692fe0aafff93280aa2f187f59087b6002408c'
assert sha(q)=='4b041348ea83896de290e619453146792e08721840d2f968b7c4b00e315e7c24'
original=p.read_text();new=w.read_text()
a='      - name: Checkout intended experimental branch'
b='      - name: Fetch only exact successful 26965 Actions artifact 14564574142'
c='      - name: Seal exact successful 26968 current source and 26969 controlled AE + noise evening'
assert a in original and a in new and b in original and c in new
assert original[original.index(a):original.index(b)]==new[new.index(a):new.index(c)],'historical steps changed'
for needle in ('TRIGGER_26969.txt','python3 -S build_26969_incremental.py fetch','python3 -S build_26969_incremental.py prepare-base','bash compile_26968_shaders.sh','bash compile_26969_shaders.sh','bash compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff','test_26903_v3_archive_receipt.py','test_26969_ae_host.py --live','test_26969_shader_contract.py --live','test_26969_patches.py --live','one mandatory'.title() if False else 'One mandatory real 26969 Android NDK dual-ABI Kotlin Java and full app assembleDebug','steps.runner_image_26969.outputs.image',':app:assembleDebug','actions/upload-artifact@v4','photon_26969_outputs/','actions/cache/restore@v4'):
 assert needle in new,needle
assert new.count('actions/upload-artifact@v4')==1
assert new.count('      - name: One mandatory real 26969 Android NDK dual-ABI Kotlin Java and full app assembleDebug')==1
assert 'branches:\n      - experimental-clean-photon-rebuild' in new
assert 'GITHUB_TOKEN: ${{ github.token }}' in new
assert 'app/.cxx' in new
assert 'hashFiles(\'app/src/main/cpp/**/*\'' in new
assert 'photon-26969-26968-rawr-ae-grain-evening' in new
print('PASS executed 26968 historical prefix byte-identical; 26969 real compiler, exact artifact and three-stage trigger guards')
