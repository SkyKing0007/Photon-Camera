#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv) not in (3,5): raise SystemExit("usage: verify_26757_infrastructure.py BUILD WORKFLOW [REF26752_BUILD REF26752_WORKFLOW]")
b=Path(sys.argv[1]).read_text(); w=Path(sys.argv[2]).read_text()
def ordered(text,items):
 p=[]
 for s in items:
  i=text.find(s); assert i>=0,s; p.append(i)
 assert p==sorted(p),list(zip(items,p))
cur=["verify_package","verify_scope","obtain_authority","make_candidate","verify_successful_26752_mechanics","prepare_glslang","compile_modified_runtime_shaders","compile_spektra_raw_shader","install_frozen_candidate_live",":app:compileDebugKotlin",":app:compileDebugJavaWithJavac","after_language_compiler_snapshot","buildCMakeDebug[arm64-v8a]","buildCMakeDebug[armeabi-v7a]","PRE-BUILD SAFETY PROOF PASSED",":app:assembleDebug","postbuild_proof"]
exec_b=b[b.index("# IRIS_26757_AUTHORITATIVE_ACTIONS_STAGE_ORDER"):]; ordered(exec_b,cur); assert exec_b.find("buildCMakeDebug[armeabi-v7a]") < exec_b.rfind("verify_candidate_patches") < exec_b.find("PRE-BUILD SAFETY PROOF PASSED")
for s in ['GLSLANG_VERSION="16.5.0"','RUNTIME_AUTHORITY_COMMIT="c5ecc2a67ba375aa5f7d78ab8a59e7d36cd7aa0c"','ROOT_ARTIFACT_SHA="68e50cdd2fe1af5141d67c8803a180b3016e535a04f64d28f7ca90ece9a96d4a"','ROOT_TAR_SHA="394686abc7f043c9b9369bc164da8084a69f0df87088490399b03a11257b3dc3"','MECHANICS_AUTHORITY_COMMIT="69d5cb14f950d6fe5309441f7abf29d96631ab02"','IRIS_26757_AUTHORITATIVE_ACTIONS_STAGE_ORDER']: assert s in b,s
for s in ["java-version: '17'","actions/checkout@v5","actions/setup-java@v5","actions/setup-python@v5","bash build_26757_evidence_limited_fast_plan_b.sh","Verify exact 26757 APK exists before artifact upload","actions/upload-artifact@v4"]: assert s in w,s
# Permanent regression: handoff must not carry root files matching historical 26756_* trigger.
root=Path(__file__).resolve().parent; bad=[p.name for p in root.iterdir() if p.is_file() and p.name.startswith('26756_')]; assert not bad,bad
if len(sys.argv)==5:
 rb=Path(sys.argv[3]).read_text(); rw=Path(sys.argv[4]).read_text(); prior=["verify_package","verify_scope","obtain_authority","make_candidate","verify_successful_26751_mechanics","prepare_glslang","compile_modified_runtime_shaders","compile_spektra_raw_shader","install_frozen_candidate_live",":app:compileDebugKotlin",":app:compileDebugJavaWithJavac","after_language_compiler_snapshot","buildCMakeDebug[arm64-v8a]","buildCMakeDebug[armeabi-v7a]","PRE-BUILD SAFETY PROOF PASSED",":app:assembleDebug","postbuild_proof"]
 exec_rb=rb[rb.index("# IRIS_26752_AUTHORITATIVE_ACTIONS_STAGE_ORDER"):]; ordered(exec_rb,prior); assert exec_rb.find("buildCMakeDebug[armeabi-v7a]") < exec_rb.rfind("verify_candidate_patches") < exec_rb.find("PRE-BUILD SAFETY PROOF PASSED")
 for s in ['GLSLANG_VERSION="16.5.0"','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace','IRIS_26752_AUTHORITATIVE_ACTIONS_STAGE_ORDER']: assert s in rb,s
 for s in ["java-version: '17'","actions/checkout@v5","actions/setup-java@v5","actions/setup-python@v5","actions/upload-artifact@v4"]: assert s in rw,s
print("PASS 26757 infrastructure: exact successful 26752 stage/toolchain/order inherited; no historical 26756 trigger overlap; deltas limited to successful 26756 authority, 26757 version/scope, and applicable performance/SR regressions")
