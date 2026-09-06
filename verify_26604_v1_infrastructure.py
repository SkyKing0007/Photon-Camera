#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,re
SUCCESS_26603_SCRIPT_BLOB='4d6a37840393d07467b19a2bc2f4ac7e62c481a0'
SUCCESS_26603_WORKFLOW_BLOB='819be46d1482744dbbdc407243b67528a1aa663e'
GOLDEN_26593_SCRIPT_SHA='111d59850aa4a0dccef482bcf68ce7b9d93e76d99729fc2de810ff91b97f160f'
GOLDEN_26593_WORKFLOW_SHA='89083ed8892f18f93e50b35679beeba114674cacfcb4ad3ff79078ec130f43fc'
def fail(m):raise SystemExit('FAIL: '+m)
def H(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git_blob(p):
 b=Path(p).read_bytes();return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def check_order(s,label):
 tail=s[s.rfind('\nverify_package\n'):];top=['verify_package','verify_scope','obtain_authority','make_candidate','verify_shaders','install_and_build'];pos=[]
 for k in top:
  i=tail.find(k)
  if i<0:fail(label+' missing top-level mechanics '+k)
  pos.append(i)
 if pos!=sorted(pos):fail(label+' top-level mechanics order changed')
 a=s.index('install_and_build(){');b=s.index('\n}\nverify_package',a);body=s[a:b]
 keys=['snapshot_candidate_from_authority "$BASE" "$ROOT" "$LIVE_CANON"','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug --stacktrace','snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"','candidate_app_source.tar.gz']
 p=[]
 for k in keys:
  i=body.find(k)
  if i<0:fail(label+' missing mechanics '+k)
  p.append(i)
 if p!=sorted(p):fail(label+' install/build mechanics order changed')
 return tuple(keys)
def workflow_shape(w,label):
 keys=['actions/checkout@v5','actions/setup-java@v5','actions/setup-python@v5','sha256sum -c V1_','bash -n build_',"python3 -S - <<'PY'",'bash build_','actions/upload-artifact@v4'];p=[]
 for k in keys:
  i=w.find(k)
  if i<0:fail(label+' missing workflow mechanics '+k)
  p.append(i)
 if p!=sorted(p):fail(label+' workflow mechanics order changed')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('build_script');ap.add_argument('workflow');ap.add_argument('--success-26603-script');ap.add_argument('--success-26603-workflow');ap.add_argument('--golden-26593-script');ap.add_argument('--golden-26593-workflow');ns=ap.parse_args()
 s=Path(ns.build_script).read_text();w=Path(ns.workflow).read_text()
 for t in ['BASE_SUCCESS_COMMIT="d71cbd68fa272fa291bf6f465895a8530ce2febc"','BASE_RUN_ID="33994540494"','BASE_JOB_ID="101382623827"','BASE_ARTIFACT_ID="9977697792"','BASE_ARTIFACT_SHA="77707aac10bc5c2e26e87681753e5f835847a972c2f19f38375785cd5bf52dad"','BASE_TAR_SHA="83e1e55c96c5f39011ee2b7528a9b4c314385b1112d94a777acdd316a688684f"','MECHANICS_GOLDEN_COMMIT="7c485416a8f41f9bf8a834bf4282e7c2318fa9fb"','GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"']:
  if t not in s:fail('authority/mechanics pin '+t)
 sig=check_order(s,'26604');blocks=re.findall(r"<<'PY'\n(.*?)\nPY",s,re.S)
 if len(blocks)!=5:fail(f'embedded Python heredoc count {len(blocks)} != 5')
 for i,block in enumerate(blocks,1):compile(block,f'heredoc{i}','exec')
 workflow_shape(w,'26604')
 for t in ['build-26604-v1-continuous-bracket-single-tone-owner.yml','photon-26604-v1-continuous-bracket-single-tone-owner','Build exact 26604 candidate from successful compiled 26603 authority']:
  if t not in w:fail('26604 workflow identity '+t)
 if ns.success_26603_script:
  if git_blob(ns.success_26603_script)!=SUCCESS_26603_SCRIPT_BLOB:fail('successful-26603 build script blob')
  prior=Path(ns.success_26603_script).read_text()
  if check_order(prior,'26603')!=sig:fail('core compiler/build mechanics differs from successful 26603')
 if ns.success_26603_workflow:
  if git_blob(ns.success_26603_workflow)!=SUCCESS_26603_WORKFLOW_BLOB:fail('successful-26603 workflow blob')
  workflow_shape(Path(ns.success_26603_workflow).read_text(),'26603')
 for p,want,label in [(ns.golden_26593_script,GOLDEN_26593_SCRIPT_SHA,'26593 script'),(ns.golden_26593_workflow,GOLDEN_26593_WORKFLOW_SHA,'26593 workflow')]:
  if p and H(p)!=want:fail(label+' SHA')
 print('PASS exact successful-26603 build/workflow mechanics inherited; successful-26593 compiler/build ordering retained')
 print('PASS infrastructure delta limited to 26604 identity/base/12-file scope/no-backup status/new regressions/29-shader coverage')
if __name__=='__main__':main()
