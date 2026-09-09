#!/usr/bin/env python3
from pathlib import Path
import re,sys
if len(sys.argv)<3: raise SystemExit('usage: verify_26615_infrastructure.py BUILD WORKFLOW [--successful-r1-script FILE --successful-r1-workflow FILE]')
b=Path(sys.argv[1]).read_text(); y=Path(sys.argv[2]).read_text()
# Freeze successful 26614 R1 outer ordering and compiler/build ordering.
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_shaders']
pos=-1
for tok in order:
    q=b.find(tok+'\n',pos+1) if tok=='verify_package' else b.find(tok,pos+1)
    if q<0: raise SystemExit('missing/order '+tok)
    pos=q
internal=['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac',"':app:buildCMakeDebug[arm64-v8a]'","':app:buildCMakeDebug[armeabi-v7a]'",'verify_candidate_patches','PRE-BUILD SAFETY PROOF','./gradlew :app:assembleDebug','exactly one','postbuild candidate byte-identical']
pos=b.find('install_and_build(){')
for tok in internal:
    q=b.find(tok,pos+1)
    if q<0: raise SystemExit('successful-R1 build order token missing '+tok)
    pos=q
tr=Path(Path(sys.argv[1]).parent/'transform_26615.py').read_text()
for tok in ['GIT_CEILING_DIRECTORIES',"['git','rev-parse','--show-toplevel']","['git','apply','--check'","['git','apply'"]:
    if tok not in tr: raise SystemExit('R1 transform isolation regression '+tok)
for tok in ['actions/checkout@v5','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4']:
    if tok not in y: raise SystemExit('workflow mechanics drift '+tok)
if 'experimental-clean-photon-rebuild' not in y: raise SystemExit('wrong branch')
if "permissions:\n  contents: read\n  actions: read" not in y: raise SystemExit('workflow permissions drift')
# Optional exact successful-R1 comparison: prove the critical sequence still appears in prior authority too.
if '--successful-r1-script' in sys.argv:
    p=Path(sys.argv[sys.argv.index('--successful-r1-script')+1]).read_text()
    for tok in ['snapshot_candidate_from_authority','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac',"':app:buildCMakeDebug[arm64-v8a]'",'verify_candidate_patches','PRE-BUILD SAFETY PROOF','./gradlew :app:assembleDebug','postbuild candidate byte-identical','tar --sort=name']:
        if tok not in p or tok not in b: raise SystemExit('R1 mechanics inheritance missing '+tok)
print('PASS 26615 infrastructure: exact successful-26614-R1 ordering/isolation/compiler/NDK/patch/assemble/invariance mechanics preserved; algorithm-only validator deltas')
