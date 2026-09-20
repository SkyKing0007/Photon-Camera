#!/usr/bin/env python3
from pathlib import Path
import sys
b=Path(sys.argv[1]).read_text();w=Path(sys.argv[2]).read_text()
for x in ['RUNTIME_AUTHORITY_COMMIT="101fb9ac90549d6053e15b2b9e97ba5835a14849"','BASE_RUN_ID="35524878349"','BASE_ARTIFACT_ID="10609466350"','BASE_ARTIFACT_SHA="cd39af098f884761301416e18e729d0107de1bcd23399289dcb3fc077c52977a"','BASE_TAR_SHA="dd09e9abb52fa688d59efc52eb3fac079d9f9f90ee62cbbb3479e2c3df6addf2"','VERSION_NAME="0.9726677"; VERSION_BUILD="26677"']:assert x in b,x
seq=['verify_package','verify_scope','obtain_authority','make_candidate','verify_shaders','verify_successful_26676_mechanics','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','postbuild_proof'];pos=-1
for x in seq:
 n=b.find(x,pos+1);assert n>=0,x;pos=n
for x in ['actions/checkout@v5','actions/setup-java@v5','actions/setup-python@v5','actions/upload-artifact@v4','build_26677_r1_watermark_correction.sh']:assert x in w,x
print('PASS 26677 infrastructure: successful-26676 build order retained; watermark-only scope')
