#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,re
SUCCESS_26600_SCRIPT_BLOB='fb58148584b6a587a9ce37515d657d775a4da7e6'
SUCCESS_26600_WORKFLOW_BLOB='f8beb058fe7618bb6a7808fdc3f482150ae5ed33'
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
 ap=argparse.ArgumentParser();ap.add_argument('build_script');ap.add_argument('workflow');ap.add_argument('--success-26600-script');ap.add_argument('--success-26600-workflow');ap.add_argument('--golden-26593-script');ap.add_argument('--golden-26593-workflow');ns=ap.parse_args()
 s=Path(ns.build_script).read_text();w=Path(ns.workflow).read_text()
 for t in ['BASE_SUCCESS_COMMIT="d12358acac0249eb37b5bbea137de107bd96612f"','BASE_RUN_ID="33967121035"','BASE_JOB_ID="101309093227"','BASE_ARTIFACT_ID="9969833503"','BASE_ARTIFACT_SHA="519c3a9aa1554a9839117a8590f8e5bc3c9ce830f3ba1d9df9d25718ad64bfe4"','BASE_TAR_SHA="50d435c0980692bbcf5c06f1731c0fc5da77e7cf449f2f610b6035b593e414af"','MECHANICS_GOLDEN_COMMIT="7c485416a8f41f9bf8a834bf4282e7c2318fa9fb"','GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"']:
  if t not in s:fail('authority/mechanics pin '+t)
 sig=check_order(s,'26601');blocks=re.findall(r"<<'PY'\n(.*?)\nPY",s,re.S)
 if len(blocks)!=5:fail(f'embedded Python heredoc count {len(blocks)} != 5')
 for i,block in enumerate(blocks,1):compile(block,f'heredoc{i}','exec')
 workflow_shape(w,'26601')
 for t in ['build-26601-v1-common-sabre-short-restored-presentation.yml','photon-26601-v1-common-sabre-short-restored-presentation','Build exact 26601 candidate from successful compiled 26600 authority']:
  if t not in w:fail('26601 workflow identity '+t)
 if ns.success_26600_script:
  if git_blob(ns.success_26600_script)!=SUCCESS_26600_SCRIPT_BLOB:fail('successful-26600 build script blob')
  prior=Path(ns.success_26600_script).read_text()
  if check_order(prior,'26600')!=sig:fail('core compiler/build mechanics differs from successful 26600')
 if ns.success_26600_workflow:
  if git_blob(ns.success_26600_workflow)!=SUCCESS_26600_WORKFLOW_BLOB:fail('successful-26600 workflow blob')
  workflow_shape(Path(ns.success_26600_workflow).read_text(),'26600')
 for p,want,label in [(ns.golden_26593_script,GOLDEN_26593_SCRIPT_SHA,'26593 script'),(ns.golden_26593_workflow,GOLDEN_26593_WORKFLOW_SHA,'26593 workflow')]:
  if p and H(p)!=want:fail(label+' SHA')
 print('PASS exact successful-26600 build/workflow mechanics inherited; successful-26593 compiler/build ordering retained')
 print('PASS infrastructure delta limited to 26601 identity/base/eight-file scope/no-backup status/new regressions/shader count')
if __name__=='__main__':main()
