#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,re
SUCCESS_26596_SCRIPT_SHA='a6ae1c00e5a08fb5c90e1762e7a571d4237112e384a197eb03f9def04c6e8bb0'
SUCCESS_26596_WORKFLOW_SHA='0ba8a0d3134b1ba2fd38a3797fc85fae36597bffc3f453729cabc05d4cb94077'
GOLDEN_26593_SCRIPT_SHA='111d59850aa4a0dccef482bcf68ce7b9d93e76d99729fc2de810ff91b97f160f'
GOLDEN_26593_WORKFLOW_SHA='89083ed8892f18f93e50b35679beeba114674cacfcb4ad3ff79078ec130f43fc'
def fail(m): raise SystemExit('FAIL: '+m)
def H(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check_order(s):
    tail=s[s.rfind('\nverify_package\n'):]
    top=['verify_package','verify_scope','obtain_authority','make_candidate','verify_shaders','install_and_build']
    pos=[]
    for k in top:
        i=tail.find(k)
        if i<0: fail('missing top-level mechanics token '+k)
        pos.append(i)
    if pos!=sorted(pos): fail('successful-26593 top-level mechanics order changed')
    a=s.index('install_and_build(){'); b=s.index('\n}\nverify_package',a); body=s[a:b]
    keys=['snapshot_candidate_from_authority "$BASE" "$ROOT" "$LIVE_CANON"','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"','candidate_app_source.tar.gz']
    pos=[]
    for k in keys:
        i=body.find(k)
        if i<0: fail('missing install/build mechanics token '+k)
        pos.append(i)
    if pos!=sorted(pos): fail('successful-26593 install/build mechanics order changed')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('build_script');ap.add_argument('workflow');ap.add_argument('--success-26596-script');ap.add_argument('--success-26596-workflow');ap.add_argument('--golden-26593-script');ap.add_argument('--golden-26593-workflow');ns=ap.parse_args()
    s=Path(ns.build_script).read_text();w=Path(ns.workflow).read_text()
    for t in ['BASE_SUCCESS_COMMIT="00084c9ef2135c92f708441e9e64e33d22e48e5b"','BASE_RUN_ID="33908848179"','BASE_JOB_ID="101140212956"','BASE_ARTIFACT_ID="9950655842"','BASE_ARTIFACT_SHA="216f52c154f7d7c7fd0693c9dc3b61453dfb80a3b4fd8c312b9ebfb3cfd647b6"','BASE_TAR_SHA="2e799f9510ad9b4f1ddd4f247ad6c6ef1ee4bd083e2923fd9642b573cc9427ec"','MECHANICS_GOLDEN_COMMIT="7c485416a8f41f9bf8a834bf4282e7c2318fa9fb"','GLSLANG_VERSION="16.5.0"']:
        if t not in s: fail('authority/mechanics pin '+t)
    check_order(s)
    blocks=re.findall(r"<<'PY'\n(.*?)\nPY",s,re.S)
    if len(blocks)!=5: fail(f'embedded Python heredoc count {len(blocks)} != 5')
    for i,block in enumerate(blocks,1):
        try: compile(block,f'{Path(ns.build_script).name}:heredoc{i}','exec')
        except SyntaxError as e: fail(f'embedded Python heredoc syntax {i}: {e.msg} line={e.lineno}')
    if "names.append('V1_26597_HANDOFF_HASHES.sha256')\nprint('\\n'.join(sorted(names)))" not in s: fail('26593-equivalent escaped expected-scope join missing')
    pairs=[(ns.success_26596_script,SUCCESS_26596_SCRIPT_SHA,'successful-26596 build script'),(ns.success_26596_workflow,SUCCESS_26596_WORKFLOW_SHA,'successful-26596 workflow'),(ns.golden_26593_script,GOLDEN_26593_SCRIPT_SHA,'successful-26593 build script'),(ns.golden_26593_workflow,GOLDEN_26593_WORKFLOW_SHA,'successful-26593 workflow')]
    for path,want,label in pairs:
        if path and H(path)!=want: fail(label+' SHA')
    for t in ['build-26597-v1-universal-highlight-preservation.yml','photon-26597-v1-1-universal-highlight-preservation','Build exact 26597 candidate from successful compiled 26596 authority']:
        if t not in w: fail('26597 workflow identity/order token '+t)
    print('PASS exact successful-26596 infrastructure pins + successful-26593 compiler/build ordering inherited')
    if all(x[0] for x in pairs): print('PASS exact successful-26596 and successful-26593 build script/workflow SHA audit')
    else: print('PASS prior infrastructure hash pins packaged; exact-source replay deferred to Actions')
if __name__=='__main__':main()
