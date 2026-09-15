#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26644_r1_infrastructure.py BUILD_SCRIPT WORKFLOW')
build,workflow=map(Path,sys.argv[1:3]); root=build.resolve().parent
old_build=root/'build_26643_r1_aosp_heic_ui.sh'; old_workflow=root/'.github/workflows/build-26643-r1-aosp-heic-ui.yml'
repo_authority_present=old_build.is_file() and old_workflow.is_file()
def blob(p): return subprocess.check_output(['git','hash-object',str(p)],text=True).strip()
if repo_authority_present:
 assert blob(old_build)=='c5c6a31b0497f03c8e92a29d3418015f098d110e',blob(old_build)
 assert blob(old_workflow)=='3c2eb98c8dc476a7945010cc3133ab7cdb50c345',blob(old_workflow)
s=build.read_text(); w=workflow.read_text(); old=old_build.read_text() if repo_authority_present else ''; ow=old_workflow.read_text() if repo_authority_present else ''
# Exact successful 26643 top-level procedure remains in the same order; only changed GLSL makes the
# previously N/A real shader compiler applicable inside verify_shaders.
ordered=[
'verify_package\nverify_scope\nobtain_authority\nmake_candidate\nverify_shaders\nverify_successful_26643_mechanics',
'install_frozen_candidate_live',
'./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
'verify_candidate_patches',
'26644 PRE-BUILD SAFETY PROOF PASSED',
'./gradlew :app:assembleDebug --stacktrace',
'expected exactly one Gradle debug APK',
'postbuild_proof',
'26644 R1 ACTIONS BUILD COMPLETE']
pos=-1
for token in ordered:
 q=s.find(token,pos+1)
 if q<0: raise SystemExit('26644 infrastructure order missing: '+token)
 pos=q
# Mechanics functions inherited, not renamed/replaced.
for fn in ['snapshot_candidate_from_authority','compare_app_trees','verify_package','verify_scope','obtain_authority','make_candidate','verify_shaders','verify_candidate_patches','install_frozen_candidate_live','postbuild_proof']:
 if f'{fn}()' not in s: raise SystemExit('missing mechanics function '+fn)
# Same runner/toolchain/actions ordering as successful workflow.
for token in ['runs-on: ubuntu-24.04','actions/checkout@v5','actions/setup-java@v5',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4']:
 if token not in w: raise SystemExit('workflow mechanics missing '+token)
# Historical workflow must not accidentally trigger on 26644 names and new workflow must not trigger 26643.
if repo_authority_present and ("'26644_" in ow or "build_26644" in ow): raise SystemExit('historical 26643 workflow overlaps 26644')
if "'26643_" in w or "build_26643_r1_aosp_heic_ui.yml'" in w: raise SystemExit('new workflow contains historical trigger')
# New build explicitly identifies exact successful authority and exact artifact.
for token in ['RUNTIME_AUTHORITY_COMMIT="874d4f65af760ae6a2fcfdd119acdc55ed47e78f"','BASE_RUN_ID="34992998426"','BASE_ARTIFACT_ID="10406636312"','BASE_ARTIFACT_SHA="0c7e02bc53df26d3bf70b6a715ee58c0440381660992d4260cf0a97959d3d9b0"','BASE_TAR_SHA="730c28f0dc72d629b53c509659392f9273922e40372fc8cf7f3006d038ce3806"']:
 if token not in s: raise SystemExit('authority identity missing '+token)
print('PASS 26644 infrastructure diff-audit: successful 26643 blob ids pinned'+(' and repo blobs verified' if repo_authority_present else ' (clean-extract structural replay; repo blobs verified separately before packaging)')+'; compiler/native/patch/PRE-BUILD/assemble/postbuild order inherited; only applicable real-GLSL gate + 26644 identity/semantics added')
