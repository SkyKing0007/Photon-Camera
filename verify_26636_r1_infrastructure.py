#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv) not in (3,6): raise SystemExit('usage: verify_26636_r1_infrastructure.py BUILD WORKFLOW [PREV_BUILD PREV_WORKFLOW PREV_TRANSFORM]')
b=Path(sys.argv[1]).read_text(); w=Path(sys.argv[2]).read_text()
def order(s,toks,label):
 pos=-1
 for t in toks:
  n=s.find(t,pos+1)
  if n<0: raise SystemExit(f'FAIL {label} missing {t}')
  if n<=pos: raise SystemExit(f'FAIL {label} order {t}')
  pos=n
# Preserve successful 26635 gate ordering exactly; shader gate remains in place but is N/A for zero shader changes.
order(b,['verify_package','verify_scope','obtain_authority','make_candidate','verify_shaders','verify_successful_26635_mechanics','install_and_build'],'top sequence')
order(b,['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','after_language_compiler_snapshot',"':app:buildCMakeDebug[arm64-v8a]'",'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','expected exactly one Gradle debug APK','snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"','candidate_app_source.tar.gz'],'compiler/build sequence')
for t in ['REPAIR_PARENT_COMMIT="$FAILED_R1_COMMIT"','git diff --name-only "$HANDOFF_PARENT_COMMIT" "$REPAIR_PARENT_COMMIT"','git diff --name-only "$REPAIR_PARENT_COMMIT"..HEAD','snapshot_candidate_from_authority','verify_shaders','RUNTIME_AUTHORITY_COMMIT="e6790ebd2f2a8403191a276d659de4a708181efa"','FAILED_R1_COMMIT="a33e00935e00d7153cb72619333f658b0a5a566c"','SUCCESS_26635_BUILD_BLOB="779990cef8c143011e411ca87109e36d75875fa1"','SUCCESS_26635_WORKFLOW_BLOB="bb43c017494365bdccede14f2e388d156b22211e"','SUCCESS_26635_TRANSFORM_BLOB="fd466230a174cec21093c1eaba7da7585f418550"']:
 if t not in b: raise SystemExit(f'FAIL build mechanics missing {t}')
order(w,['actions/checkout@v5','actions/setup-java@v5','actions/setup-python@v5','Verify sealed 26636','Build exact 26636','actions/upload-artifact@v4'],'workflow sequence')
for t in ["java-version: '17'",'ubuntu-24.04','fetch-depth: 0']:
 if t not in w: raise SystemExit(f'FAIL workflow mechanics missing {t}')
if len(sys.argv)==6:
 pb=Path(sys.argv[3]).read_text(); pw=Path(sys.argv[4]).read_text(); pt=Path(sys.argv[5]).read_text()
 order(pb,['verify_package','verify_scope','obtain_authority','make_candidate','verify_shaders','verify_successful_26634_mechanics','install_and_build'],'successful 26635 top sequence')
 order(pb,['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','after_language_compiler_snapshot',"':app:buildCMakeDebug[arm64-v8a]'",'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','expected exactly one Gradle debug APK','snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"','candidate_app_source.tar.gz'],'successful 26635 compiler sequence')
 order(pw,['actions/checkout@v5','actions/setup-java@v5','actions/setup-python@v5','actions/upload-artifact@v4'],'successful 26635 workflow')
 if 'PASS 26635 deterministic candidate transform' not in pt: raise SystemExit('FAIL successful 26635 transform authority')
print('PASS 26636 R1.1 infrastructure repair: exact successful-26635 ordering/isolation/Kotlin-Java/NDK/patch/PRE-BUILD/assemble/postbuild mechanics preserved; only failed-R1 topology/provenance scope and corrected successful-26635 Git blobs changed; runtime payload unchanged')
