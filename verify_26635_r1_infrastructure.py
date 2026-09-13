#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv) not in (3,6): raise SystemExit('usage: verify_26635_r1_infrastructure.py BUILD WORKFLOW [PREV_BUILD PREV_WORKFLOW PREV_TRANSFORM]')
b=Path(sys.argv[1]).read_text(); w=Path(sys.argv[2]).read_text()
def order(s,toks,label):
    pos=-1
    for t in toks:
        n=s.find(t,pos+1)
        if n<0: raise SystemExit(f'FAIL {label} missing {t}')
        if n<=pos: raise SystemExit(f'FAIL {label} order {t}')
        pos=n
order(b,['verify_package','verify_scope','obtain_authority','make_candidate','verify_shaders','verify_successful_26634_mechanics','install_and_build'], 'top sequence')
order(b,['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','after_language_compiler_snapshot',"':app:buildCMakeDebug[arm64-v8a]'",'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','expected exactly one Gradle debug APK','snapshot_candidate_from_authority \"$BASE\" \"$ROOT\" \"$POST\"','candidate_app_source.tar.gz'], 'compiler/build sequence')
for t in ['GLSLANG_VERSION="16.5.0"','b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657','git diff --name-only "$HANDOFF_PARENT_COMMIT"..HEAD','snapshot_candidate_from_authority','--compiler "$compiler"']:
    if t not in b: raise SystemExit(f'FAIL build mechanics missing {t}')
order(w,['actions/checkout@v5','actions/setup-java@v5','actions/setup-python@v5','Verify sealed 26635','Build exact 26635','actions/upload-artifact@v4'],'workflow sequence')
for t in ["java-version: '17'",'ubuntu-24.04','fetch-depth: 0']:
    if t not in w: raise SystemExit(f'FAIL workflow mechanics missing {t}')
if len(sys.argv)==6:
    pb=Path(sys.argv[3]).read_text(); pw=Path(sys.argv[4]).read_text(); pt=Path(sys.argv[5]).read_text()
    # Successful 26634 core language/NDK/patch/PRE-BUILD/assemble/invariance ordering remains the authority.
    order(pb,['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','after_language_compiler_snapshot',"':app:buildCMakeDebug[arm64-v8a]'",'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','expected exactly one Gradle debug APK','snapshot_candidate_from_authority \"$BASE\" \"$ROOT\" \"$POST\"','candidate_app_source.tar.gz'],'successful 26634 sequence')
    order(pw,['actions/checkout@v5','actions/setup-java@v5','actions/setup-python@v5','actions/upload-artifact@v4'],'successful 26634 workflow')
    if 'PASS 26634 deterministic candidate transform' not in pt: raise SystemExit('FAIL successful 26634 transform authority')
print('PASS 26635 infrastructure: exact successful-26634 ordering/isolation/Kotlin-Java/NDK/patch/PRE-BUILD/assemble/invariance preserved; applicable pinned-glslang gate restored from successful shader builds')
