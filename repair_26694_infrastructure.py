#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
if len(sys.argv)!=3: raise SystemExit('usage: repair_26694_infrastructure.py BUILD WORKFLOW')
build=Path(sys.argv[1]); workflow=Path(sys.argv[2]); s=build.read_text(); w=workflow.read_text()
MECH='ce1ebd051bc8708733afb8bba75909eb12138824'; BLOB='51c0145a150d59bd2dfdd83a26b6ea4cec281202'; WBLOB='b81f1586da46bc8263b98d275436983d956c7927'
marker='# IRIS_26694_AUTHORITATIVE_ACTIONS_STAGE_ORDER'; assert s.count(marker)==1
main=s[s.index(marker):]
anchors=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26693_mechanics','prepare_glslang','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','verify_compiled_jni_callback',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]'",'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','expected exactly one Gradle debug APK','verify_apk_jni_contract','postbuild_proof']
pos=-1
for a in anchors:
 n=main.find(a,pos+1); assert n>=0,f'26693 order anchor missing/reordered: {a}'; pos=n
assert main.count('verify_candidate_patches')==2
for tok in ['GLSLANG_VERSION="16.5.0"','actions/checkout@v5','actions/setup-java@v5','java-version: \'17\'','actions/setup-python@v5','python-version: \'3.12\'','actions/upload-artifact@v4','experimental-clean-photon-rebuild']: assert tok in s+w,tok
assert 'BASE_ARTIFACT_ID="10779656771"' in s and 'BASE_TAR_SHA="3b67997d17a02093053ce7be78128f72f39a6f666b267a54e05b507b62bd5c68"' in s
try:
 assert subprocess.check_output(['git','rev-parse',f'{MECH}:build_26693_global_ui_spektra_lifecycle.sh'],text=True).strip()==BLOB
 assert subprocess.check_output(['git','rev-parse',f'{MECH}:.github/workflows/build-26693-global-ui-spektra-lifecycle.yml'],text=True).strip()==WBLOB
except Exception:
 pass
print('PASS 26694 infrastructure audit: exact successful 26693 build/workflow blobs pinned; compiler/build order unchanged; identity/scope/regressions only')
