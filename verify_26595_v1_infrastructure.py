#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,re
SUCCESS_26594_SCRIPT_SHA='e7a54ecae1ad1a4b58be2c8773c75311e63f878f305e7bbcf1eb34b40c29318a'
SUCCESS_26594_WORKFLOW_SHA='056dbf1c68671cf7d3f8770668d5c5a4dd87b259a1baf6491af7d71781757d3b'
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
 ap=argparse.ArgumentParser(); ap.add_argument('build_script'); ap.add_argument('workflow'); ap.add_argument('--success-26594-script'); ap.add_argument('--success-26594-workflow'); ap.add_argument('--golden-26593-script'); ap.add_argument('--golden-26593-workflow'); ns=ap.parse_args()
 s=Path(ns.build_script).read_text(); w=Path(ns.workflow).read_text()
 for t in ['BASE_SUCCESS_COMMIT="43205d89cc9807e02b300e9f6ab9a10324bf4c75"','BASE_RUN_ID="33878860474"','BASE_JOB_ID="101042303061"','BASE_ARTIFACT_ID="9939113841"','BASE_ARTIFACT_SHA="2f6921ccb3c6b4cf71ddf2797e18f427e1dbe51204627e1278680fce90e20583"','BASE_TAR_SHA="5e17e6d92247cbaf3c139b1ace619a5a8d5b85a65517a346b6948f51c38cb2dc"','MECHANICS_GOLDEN_COMMIT="7c485416a8f41f9bf8a834bf4282e7c2318fa9fb"','GLSLANG_VERSION="16.5.0"']:
  if t not in s: fail('authority/mechanics pin '+t)
 check_order(s)
 blocks=re.findall(r"<<'PY'\n(.*?)\nPY",s,re.S)
 if len(blocks)!=5: fail(f'embedded Python heredoc count {len(blocks)} != 5')
 for i,block in enumerate(blocks,1):
  try: compile(block,f'{Path(ns.build_script).name}:heredoc{i}','exec')
  except SyntaxError as e: fail(f'embedded Python heredoc syntax {i}: {e.msg} line={e.lineno}')
 scope_fragment="names.append('V1_26595_HANDOFF_HASHES.sha256')\nprint('\\n'.join(sorted(names)))"
 if scope_fragment not in s: fail('26593-equivalent escaped expected-scope join missing')
 pairs=[(ns.success_26594_script,SUCCESS_26594_SCRIPT_SHA,'successful-26594 build script'),(ns.success_26594_workflow,SUCCESS_26594_WORKFLOW_SHA,'successful-26594 workflow'),(ns.golden_26593_script,GOLDEN_26593_SCRIPT_SHA,'successful-26593 build script'),(ns.golden_26593_workflow,GOLDEN_26593_WORKFLOW_SHA,'successful-26593 workflow')]
 for path,want,label in pairs:
  if path and H(path)!=want: fail(label+' SHA')
 for t in ['build-26595-v1-phase-coherent-short-sr-handoff.yml','photon-26595-v1-phase-coherent-short-sr-handoff','Build exact 26595 candidate from successful compiled 26594 authority']:
  if t not in w: fail('26595 workflow identity/order token '+t)
 print('PASS exact successful-26594 infrastructure pins + successful-26593 compiler/build ordering inherited')
 if all(x[0] for x in pairs): print('PASS exact successful-26594 and successful-26593 build script/workflow SHA audit')
 else: print('PASS prior infrastructure hash pins packaged; exact-source replay deferred to Actions')
if __name__=='__main__': main()
