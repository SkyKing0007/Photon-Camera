#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,re
SUCCESS_26595_SCRIPT_SHA='ced008c4ff098d96208528b01b413d546c2ffdf27eb2dfc652ec5c016b8ccb9b'
SUCCESS_26595_WORKFLOW_SHA='76d7e47cfb576384df1930ab25f32b38b88a9b47308ae0dce7d2ce2fa2a3a557'
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
 ap=argparse.ArgumentParser(); ap.add_argument('build_script'); ap.add_argument('workflow'); ap.add_argument('--success-26595-script'); ap.add_argument('--success-26595-workflow'); ap.add_argument('--golden-26593-script'); ap.add_argument('--golden-26593-workflow'); ns=ap.parse_args()
 s=Path(ns.build_script).read_text(); w=Path(ns.workflow).read_text()
 for t in ['BASE_SUCCESS_COMMIT="7fd605dbbf02c394432108fd259ace19f0d33b93"','BASE_RUN_ID="33900804690"','BASE_JOB_ID="101114167335"','BASE_ARTIFACT_ID="9947679988"','BASE_ARTIFACT_SHA="cf80293af3aa9afde49ab69c5af0f9573a9f531b973c0d621da2126ac1b67fec"','BASE_TAR_SHA="57f9aecf8f92fad6eb5868f95317f32ffaab2b88cc31eccb4dfc9380e5565453"','MECHANICS_GOLDEN_COMMIT="7c485416a8f41f9bf8a834bf4282e7c2318fa9fb"','GLSLANG_VERSION="16.5.0"']:
  if t not in s: fail('authority/mechanics pin '+t)
 check_order(s)
 blocks=re.findall(r"<<'PY'\n(.*?)\nPY",s,re.S)
 if len(blocks)!=5: fail(f'embedded Python heredoc count {len(blocks)} != 5')
 for i,block in enumerate(blocks,1):
  try: compile(block,f'{Path(ns.build_script).name}:heredoc{i}','exec')
  except SyntaxError as e: fail(f'embedded Python heredoc syntax {i}: {e.msg} line={e.lineno}')
 scope_fragment="names.append('V1_26596_HANDOFF_HASHES.sha256')\nprint('\\n'.join(sorted(names)))"
 if scope_fragment not in s: fail('26593-equivalent escaped expected-scope join missing')
 pairs=[(ns.success_26595_script,SUCCESS_26595_SCRIPT_SHA,'successful-26595 build script'),(ns.success_26595_workflow,SUCCESS_26595_WORKFLOW_SHA,'successful-26595 workflow'),(ns.golden_26593_script,GOLDEN_26593_SCRIPT_SHA,'successful-26593 build script'),(ns.golden_26593_workflow,GOLDEN_26593_WORKFLOW_SHA,'successful-26593 workflow')]
 for path,want,label in pairs:
  if path and H(path)!=want: fail(label+' SHA')
 for t in ['build-26596-v1-phase-complete-short-uhdr-sr-handoff.yml','photon-26596-v1-phase-complete-short-uhdr-sr-handoff','Build exact 26596 candidate from successful compiled 26595 authority']:
  if t not in w: fail('26596 workflow identity/order token '+t)
 print('PASS exact successful-26595 infrastructure pins + successful-26593 compiler/build ordering inherited')
 if all(x[0] for x in pairs): print('PASS exact successful-26595 and successful-26593 build script/workflow SHA audit')
 else: print('PASS prior infrastructure hash pins packaged; exact-source replay deferred to Actions')
if __name__=='__main__': main()
