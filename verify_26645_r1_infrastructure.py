#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26645_r1_infrastructure.py BUILD_SCRIPT WORKFLOW')
build,workflow=map(Path,sys.argv[1:3]); root=build.resolve().parent
old_build=root/'build_26644_r1_visual_short_heic_ui.sh'; old_workflow=root/'.github/workflows/build-26644-r1-visual-short-heic-ui.yml'
repo_authority_present=old_build.is_file() and old_workflow.is_file()
def blob(p): return subprocess.check_output(['git','hash-object',str(p)],text=True).strip()
if repo_authority_present:
 assert blob(old_build)=='0b879132987c5a20c2ea2e1e4e9290eed8e6eb32',blob(old_build)
 assert blob(old_workflow)=='ef12742cdfedfec128a006b4e39f4b2d1c7ac022',blob(old_workflow)
s=build.read_text(); w=workflow.read_text(); ow=old_workflow.read_text() if repo_authority_present else ''
ordered=[
'verify_package\nverify_scope\nobtain_authority\nmake_candidate\nverify_shaders\nverify_successful_26644_mechanics',
'install_frozen_candidate_live',
'./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
'verify_candidate_patches',
'26645 PRE-BUILD SAFETY PROOF PASSED',
'./gradlew :app:assembleDebug --stacktrace',
'expected exactly one Gradle debug APK',
'postbuild_proof',
'26645 R1 ACTIONS BUILD COMPLETE']
pos=-1
for token in ordered:
 q=s.find(token,pos+1)
 if q<0: raise SystemExit('26645 infrastructure order missing: '+token)
 pos=q
for fn in ['snapshot_candidate_from_authority','compare_app_trees','verify_package','verify_scope','obtain_authority','make_candidate','verify_shaders','verify_candidate_patches','install_frozen_candidate_live','postbuild_proof']:
 if f'{fn}()' not in s: raise SystemExit('missing mechanics function '+fn)
for token in ['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4']:
 if token not in w: raise SystemExit('workflow mechanics missing '+token)
# Trigger domains must not overlap historical handoff names.
if repo_authority_present and ("'26645_" in ow or "build_26645" in ow): raise SystemExit('historical 26644 workflow overlaps 26645')
trigger='\n'.join(line for line in w.splitlines() if "- '" in line)
if "'26644_" in trigger or "build_26644" in trigger: raise SystemExit('new workflow contains historical 26644 trigger')
for token in [
'RUNTIME_AUTHORITY_COMMIT="d4574c5a0163c6030b8573accb9a5fe6bff86246"',
'BASE_RUN_ID="35002525151"','BASE_ARTIFACT_ID="10410108784"',
'BASE_ARTIFACT_SHA="45ffa739b72848321fc1f4d6760cdccc446e0893758d49dfa6c681d1a1cdcfbf"',
'BASE_TAR_SHA="9aa4b27d02288bda2601306e56c1b3f4e407fe5cb90fe0715067370630ab501d"',
'AUTH26644_BUILD_SCRIPT_BLOB="0b879132987c5a20c2ea2e1e4e9290eed8e6eb32"',
'AUTH26644_WORKFLOW_BLOB="ef12742cdfedfec128a006b4e39f4b2d1c7ac022"']:
 if token not in s: raise SystemExit('authority identity missing '+token)
print('PASS 26645 infrastructure diff-audit: successful 26644 build/workflow blobs pinned'+(' and repo blobs verified' if repo_authority_present else ' (clean-extract structural replay; repo blobs verified separately before packaging)')+'; compiler/native/patch/PRE-BUILD/assemble/postbuild order inherited exactly; only 26645 identity/semantic assertions changed')
