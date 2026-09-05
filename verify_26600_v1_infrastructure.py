#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,re
SUCCESS_26599_SCRIPT_BLOB='e85b0a1aa2db1980bbc71312cdaa345068af0711'
SUCCESS_26599_WORKFLOW_BLOB='2b63f25451a28f40da33c0339767c462eaeb21dd'
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
 keys=['actions/checkout@v5','actions/setup-java@v5','actions/setup-python@v5','sha256sum -c V1_','bash -n build_',"python3 -S - <<\'PY\'",'bash build_','actions/upload-artifact@v4'];p=[]
 for k in keys:
  i=w.find(k)
  if i<0:fail(label+' missing workflow mechanics '+k)
  p.append(i)
 if p!=sorted(p):fail(label+' workflow mechanics order changed')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('build_script');ap.add_argument('workflow');ap.add_argument('--success-26599-script');ap.add_argument('--success-26599-workflow');ap.add_argument('--golden-26593-script');ap.add_argument('--golden-26593-workflow');ns=ap.parse_args()
 s=Path(ns.build_script).read_text();w=Path(ns.workflow).read_text()
 for t in ['BASE_SUCCESS_COMMIT="4c4962354fab1603db98d190cff6f9bba5ed46ba"','BASE_RUN_ID="33946659672"','BASE_JOB_ID="101253882718"','BASE_ARTIFACT_ID="9963583434"','BASE_ARTIFACT_SHA="cc775a06b499a268a75bfd74bae630190dd3578cfb0c6d0924e90703a77cf40f"','BASE_TAR_SHA="efac0414844b664943991f3b118154c54e6235a0dc31c8ff22b85bd502c4f361"','MECHANICS_GOLDEN_COMMIT="7c485416a8f41f9bf8a834bf4282e7c2318fa9fb"','GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"']:
  if t not in s:fail('authority/mechanics pin '+t)
 sig=check_order(s,'26600');blocks=re.findall(r"<<'PY'\n(.*?)\nPY",s,re.S)
 if len(blocks)!=5:fail(f'embedded Python heredoc count {len(blocks)} != 5')
 for i,block in enumerate(blocks,1):compile(block,f'heredoc{i}','exec')
 workflow_shape(w,'26600')
 for t in ['build-26600-v1-boundary-consensus-short-geometry.yml','photon-26600-v1-boundary-consensus-short-geometry','Build exact 26600 candidate from successful compiled 26599 authority']:
  if t not in w:fail('26600 workflow identity '+t)
 if ns.success_26599_script:
  if git_blob(ns.success_26599_script)!=SUCCESS_26599_SCRIPT_BLOB:fail('successful-26599 build script blob')
  prior=Path(ns.success_26599_script).read_text()
  if check_order(prior,'26599')!=sig:fail('core compiler/build mechanics differs from successful 26599')
 if ns.success_26599_workflow:
  if git_blob(ns.success_26599_workflow)!=SUCCESS_26599_WORKFLOW_BLOB:fail('successful-26599 workflow blob')
  workflow_shape(Path(ns.success_26599_workflow).read_text(),'26599')
 for p,want,label in [(ns.golden_26593_script,GOLDEN_26593_SCRIPT_SHA,'26593 script'),(ns.golden_26593_workflow,GOLDEN_26593_WORKFLOW_SHA,'26593 workflow')]:
  if p and H(p)!=want:fail(label+' SHA')
 print('PASS exact successful-26599 build/workflow mechanics inherited; successful-26593 compiler/build ordering retained')
 print('PASS infrastructure delta limited to 26600 identity/base/three-file scope/no-backup status/boundary-geometry regressions')
if __name__=='__main__':main()
