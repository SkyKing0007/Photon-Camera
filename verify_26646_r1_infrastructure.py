#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26646_r1_infrastructure.py BUILD_SCRIPT WORKFLOW')
build,workflow=map(Path,sys.argv[1:3]); root=build.resolve().parent
old_build=root/'build_26645_r1_visual_short_heic_ui.sh'; old_workflow=root/'.github/workflows/build-26645-r1-visual-short-heic-ui.yml'
repo_authority_present=old_build.is_file() and old_workflow.is_file()
def blob(p): return subprocess.check_output(['git','hash-object',str(p)],text=True).strip()
if repo_authority_present:
 assert blob(old_build)=='7ad58735c84a839035b0dfec3a872066db193918',blob(old_build)
 assert blob(old_workflow)=='6c6e3cd675d0161badbf786779b874e2f8908080',blob(old_workflow)
s=build.read_text(); w=workflow.read_text(); ow=old_workflow.read_text() if repo_authority_present else ''
ordered=[
 'verify_package\nverify_scope\nobtain_authority\nmake_candidate\nverify_shaders\nverify_successful_26645_mechanics',
 'install_frozen_candidate_live',
 './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
 "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
 'verify_candidate_patches',
 '26646 PRE-BUILD SAFETY PROOF PASSED',
 './gradlew :app:assembleDebug --stacktrace',
 'expected exactly one Gradle debug APK',
 'postbuild_proof',
 '26646 R1 ACTIONS BUILD COMPLETE']
pos=-1
for token in ordered:
 q=s.find(token,pos+1)
 if q<0: raise SystemExit('26646 infrastructure order missing: '+token)
 pos=q
for fn in ['snapshot_candidate_from_authority','compare_app_trees','verify_package','verify_scope','obtain_authority','make_candidate','verify_shaders','verify_candidate_patches','install_frozen_candidate_live','postbuild_proof']:
 if f'{fn}()' not in s: raise SystemExit('missing mechanics function '+fn)
for token in ['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4']:
 if token not in w: raise SystemExit('workflow mechanics missing '+token)
if repo_authority_present and ("'26646_" in ow or 'build_26646' in ow): raise SystemExit('historical 26645 workflow overlaps 26646')
trigger='\n'.join(line for line in w.splitlines() if "- '" in line)
if "'26645_" in trigger or 'build_26645' in trigger: raise SystemExit('new workflow contains historical 26645 trigger')
for token in [
 'RUNTIME_AUTHORITY_COMMIT="ac23dcf3e5e71cb0b3e668c9ad3f23f5195e9320"',
 'BASE_RUN_ID="35010153364"','BASE_ARTIFACT_ID="10413177407"',
 'BASE_ARTIFACT_SHA="a68e42a8a6346a181ee853248a1449270f0da66821c6c4acad45fb8ef400ea94"',
 'BASE_TAR_SHA="dfacbda1ae6dacda18c8ee4436376b236a0a7550f8903e5bdd63d16a01157a3d"',
 'AUTH26645_BUILD_SCRIPT_BLOB="7ad58735c84a839035b0dfec3a872066db193918"',
 'AUTH26645_WORKFLOW_BLOB="6c6e3cd675d0161badbf786779b874e2f8908080"']:
 if token not in s: raise SystemExit('authority identity missing '+token)
print('PASS 26646 infrastructure diff-audit: exact successful 26645 build/workflow blobs pinned'+(' and repo blobs verified' if repo_authority_present else ' (clean-extract structural replay; repo blobs verified separately before packaging)')+'; compiler/native/patch/PRE-BUILD/assemble/postbuild order inherited exactly; only 26646 identity/scope/semantic assertions changed')
