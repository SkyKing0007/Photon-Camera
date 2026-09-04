#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,re
PRIOR_SCRIPT_SHA='111d59850aa4a0dccef482bcf68ce7b9d93e76d99729fc2de810ff91b97f160f'
PRIOR_WORKFLOW_SHA='89083ed8892f18f93e50b35679beeba114674cacfcb4ad3ff79078ec130f43fc'
def fail(m):raise SystemExit('FAIL: '+m)
def H(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('build_script');ap.add_argument('workflow');ap.add_argument('--prior-script');ap.add_argument('--prior-workflow');ns=ap.parse_args();s=Path(ns.build_script).read_text();w=Path(ns.workflow).read_text()
 # Hard runtime authority and exact prior mechanics hashes.
 for t in ['BASE_SUCCESS_COMMIT="7c485416a8f41f9bf8a834bf4282e7c2318fa9fb"','BASE_RUN_ID="33835148507"','BASE_JOB_ID="100906020593"','BASE_ARTIFACT_ID="9923084840"','BASE_ARTIFACT_SHA="86e721369861a69b3237ff85bf1f2198f8c8cf3d1bfd8ad3d7cd06900c968bc1"','BASE_TAR_SHA="104a9e4fe55f34087458eeb69913c6a55b2298898ba97080cefce6415e0a2f11"','GLSLANG_VERSION="16.5.0"']:
  if t not in s:fail('authority/mechanics pin '+t)
 # Required successful-26593 top-level and install/build ordering preserved.
 tail=s[s.rfind('\nverify_package\n'):]
 top=['verify_package','verify_scope','obtain_authority','make_candidate','verify_shaders','install_and_build']
 pos=[]
 for k in top:
  i=tail.find(k)
  if i<0:fail('missing top-level mechanics token '+k)
  pos.append(i)
 if pos!=sorted(pos):fail('successful-26593 top-level mechanics order changed')
 a=s.index('install_and_build(){'); b=s.index('\n}\nverify_package',a); body=s[a:b]
 keys=['snapshot_candidate_from_authority "$BASE" "$ROOT" "$LIVE_CANON"','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"','candidate_app_source.tar.gz']
 pos=[]
 for k in keys:
  i=body.find(k)
  if i<0:fail('missing install/build mechanics token '+k)
  pos.append(i)
 if pos!=sorted(pos):fail('successful-26593 install/build mechanics order changed')
 # Permanent Actions regression 26594 V1: bash -n does not parse quoted Python heredocs.
 # Compile every embedded Python heredoc exactly as packaged before any branch-scope/runtime work.
 blocks=re.findall(r"<<'PY'\n(.*?)\nPY",s,re.S)
 if len(blocks)!=5:fail(f'embedded Python heredoc count {len(blocks)} != 5')
 for i,block in enumerate(blocks,1):
  try: compile(block,f'{Path(ns.build_script).name}:heredoc{i}','exec')
  except SyntaxError as e: fail(f'embedded Python heredoc syntax {i}: {e.msg} line={e.lineno}')
 scope_fragment="names.append('V1_26594_HANDOFF_HASHES.sha256')\nprint('\\n'.join(sorted(names)))"
 if scope_fragment not in s:fail('26593-equivalent escaped expected-scope join missing')
 if ns.prior_script and H(ns.prior_script)!=PRIOR_SCRIPT_SHA:fail('successful-26593 build script SHA')
 if ns.prior_workflow and H(ns.prior_workflow)!=PRIOR_WORKFLOW_SHA:fail('successful-26593 workflow SHA')
 if 'build-26594-v1-region-anchored-short-handoff.yml' not in w or 'photon-26594-v1-region-anchored-short-handoff' not in w:fail('26594 workflow identity')
 print('PASS successful-26593 authority pins and exact compiler/build ordering inherited')
 if ns.prior_script: print('PASS exact successful-26593 build script/workflow SHA audit')
 else: print('PASS prior infrastructure hash pins packaged; live exact-source replay deferred to Actions')
if __name__=='__main__':main()
