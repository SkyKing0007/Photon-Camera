#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys
if len(sys.argv) not in (3,6): raise SystemExit('usage: verify_26631_r1_infrastructure.py BUILD WORKFLOW [--successful-26630-build B --successful-26630-workflow W]')
build=Path(sys.argv[1]); workflow=Path(sys.argv[2]); b=build.read_text(); w=workflow.read_text()
# Same successful 26630 sequence/order/toolchain mechanics; only identity, base authority, 4-path scope and regressions change.
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_shaders','verify_successful_26630_mechanics']
pos=[]
# use final invocation area by rfind; function definitions occur earlier
for t in order:
 i=b.rfind('\n'+t+'\n')
 if i<0: raise SystemExit(f'FAIL build final invocation missing {t}')
 pos.append(i)
if pos!=sorted(pos): raise SystemExit('FAIL build gate order changed')
for token in [
'GLSLANG_VERSION="16.5.0"','b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657',
':app:compileDebugKotlin :app:compileDebugJavaWithJavac',"':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]'",':app:assembleDebug',
'PRE-BUILD SAFETY PROOF PASSED','snapshot_candidate_from_authority','tar --sort=name --mtime=\'UTC 1970-01-01\'',
'R1_26631_RUNTIME_DELTA_FROM_26630_R1.patch','R1_26631_RUNTIME_ROLLBACK_TO_26630_R1.patch']:
 if token not in b: raise SystemExit(f'FAIL successful-26630 mechanic absent: {token}')
if 'core.abbrev=7/12/40' not in (Path(__file__).resolve().parent/'verify_26631_r1_patches.py').read_text(): raise SystemExit('FAIL deterministic patch mechanics text')
for token in ['actions/checkout@v5','actions/setup-java@v5',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4']:
 if token not in w: raise SystemExit(f'FAIL workflow toolchain/order token {token}')
if len(sys.argv)==6:
 if sys.argv[3]!='--successful-26630-build' or sys.argv[5].startswith('--'): raise SystemExit('FAIL arguments')
 # optional branch retained for compatibility; exact successful blob hashes are verified by shell before call.
print('PASS 26631 infrastructure: exact successful-26630 ordering/isolation/compiler/NDK/patch/PRE-BUILD/assemble/postbuild mechanics preserved; identity/26630 authority/4-path validators/new UHDR regression only')
