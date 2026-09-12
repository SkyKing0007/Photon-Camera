#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26632_r1_infrastructure.py BUILD WORKFLOW')
b=Path(sys.argv[1]).read_text(); w=Path(sys.argv[2]).read_text(); root=Path(__file__).resolve().parent
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_shaders','verify_successful_26631_mechanics']
pos=[]
for t in order:
 i=b.rfind('\n'+t+'\n')
 if i<0: raise SystemExit(f'FAIL build final invocation missing {t}')
 pos.append(i)
if pos!=sorted(pos): raise SystemExit('FAIL build gate order changed')
for token in [
'GLSLANG_VERSION="16.5.0"','b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657',
':app:compileDebugKotlin :app:compileDebugJavaWithJavac',"':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]'",':app:assembleDebug',
'PRE-BUILD SAFETY PROOF PASSED','snapshot_candidate_from_authority',"tar --sort=name --mtime='UTC 1970-01-01'",
'R1_26632_RUNTIME_DELTA_FROM_26631_R1.patch','R1_26632_RUNTIME_ROLLBACK_TO_26631_R1.patch',
'SUCCESS_26631_BUILD_SHA="08911dd9d9a836e62c9cb0e75dd2292bdb36964b740efc1ecb54b9f6c21d8c75"',
'SUCCESS_26631_WORKFLOW_SHA="8351117cfbb111a879c80401b3b96f4a98aef8c96663c61677bab9177816c051"',
'SUCCESS_26631_TRANSFORM_SHA="a02d805ff3fd4383aec2f06d57bfb83b4a9162c9f362a9a8cd43f81ae4ae8c09"']:
 if token not in b: raise SystemExit(f'FAIL successful-26631 mechanic absent: {token}')
if 'core.abbrev=7/12/40' not in (root/'verify_26632_r1_patches.py').read_text(): raise SystemExit('FAIL deterministic patch mechanics text')
for token in ['actions/checkout@v5','actions/setup-java@v5',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4']:
 if token not in w: raise SystemExit(f'FAIL workflow toolchain/order token {token}')
# No alternate build or compiler sequence allowed.
if w.count('bash build_26632_r1_output_referred_uhdr_sdr_rolloff.sh')!=1: raise SystemExit('FAIL workflow build invocation count')
print('PASS 26632 infrastructure: exact successful-26631 ordering/isolation/compiler/NDK/patch/PRE-BUILD/assemble/postbuild mechanics preserved; identity/26631 authority/8-path validators/new regressions only')
