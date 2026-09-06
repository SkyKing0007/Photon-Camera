#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,re
SUCCESS_26605_SCRIPT_BLOB='b3b79ef8f9a94a465c3d3877705c5235587e586c'
SUCCESS_26605_WORKFLOW_BLOB='073b8360693bad01b80940dcec2972260545c258'
GOLDEN_26593_SCRIPT_SHA='111d59850aa4a0dccef482bcf68ce7b9d93e76d99729fc2de810ff91b97f160f'
GOLDEN_26593_WORKFLOW_SHA='89083ed8892f18f93e50b35679beeba114674cacfcb4ad3ff79078ec130f43fc'
def fail(m):raise SystemExit('FAIL: '+m)
def H(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git_blob(p):
 b=Path(p).read_bytes();return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def function_body(s,name,next_name):
 a=s.index(name+'(){');b=s.index('\n}\n'+next_name,a);return s[a:b]
def check_order(s,label):
 tail=s[s.rfind('\nverify_package\n'):]
 top=['verify_package','verify_scope','obtain_authority','make_candidate','verify_shaders','install_and_build'];pos=[]
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
 keys=['actions/checkout@v5','actions/setup-java@v5','actions/setup-python@v5','sha256sum -c V1_','bash -n build_','python3 -S - <<\'PY\'','bash build_','actions/upload-artifact@v4'];p=[]
 for k in keys:
  i=w.find(k)
  if i<0:fail(label+' missing workflow mechanics '+k)
  p.append(i)
 if p!=sorted(p):fail(label+' workflow mechanics order changed')
 for t in ['runs-on: ubuntu-24.04','distribution: temurin',"java-version: '17'",'cache: gradle',"python-version: '3.12'",'retention-days: 90']:
  if t not in w:fail(label+' workflow pin '+t)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('build_script');ap.add_argument('workflow');ap.add_argument('--success-26605-script');ap.add_argument('--success-26605-workflow');ap.add_argument('--golden-26593-script');ap.add_argument('--golden-26593-workflow');ns=ap.parse_args()
 s=Path(ns.build_script).read_text();w=Path(ns.workflow).read_text()
 pins=['BASE_SUCCESS_COMMIT="7c6094a96d5339a12926d28ff341a94fc77da71f"','HANDOFF_PARENT_COMMIT="7c6094a96d5339a12926d28ff341a94fc77da71f"','BACKUP_BRANCH="backup-26605-v1-1-success-before-26606-short-rescue-architecture"','BACKUP_COMMIT="7c6094a96d5339a12926d28ff341a94fc77da71f"','BASE_RUN_ID="34008575432"','BASE_JOB_ID="101420189296"','BASE_ARTIFACT_ID="9981773630"','BASE_ARTIFACT_SHA="031958fe5da000c5f0442c1c742f5bec7077fc4710866cc1721edf1ff24980e5"','BASE_TAR_SHA="3a16b19c7f0cf66afcb4cb8ade2b9089e0f9bea5f176129a09cff108d7a2ccba"','MECHANICS_GOLDEN_COMMIT="7c485416a8f41f9bf8a834bf4282e7c2318fa9fb"','GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"']
 for t in pins:
  if t not in s:fail('authority/mechanics pin '+t)
 sig=check_order(s,'26606 V1');workflow_shape(w,'26606 V1')
 blocks=re.findall(r"<<'PY'\n(.*?)\nPY",s,re.S)
 if len(blocks)!=5:fail(f'embedded Python heredoc count {len(blocks)} != 5')
 for i,block in enumerate(blocks,1):compile(block,f'heredoc{i}','exec')
 for t in ['Build 26606 V1 SHORT Rescue Architecture','build-26606-v1-short-rescue-architecture.yml','photon-26606-v1-short-rescue-architecture','Build exact 26606 V1 candidate from successful compiled 26605 V1.1 authority']:
  if t not in w:fail('26606 workflow identity '+t)
 # Old 26605 workflow trigger families must not overlap with the new package.
 for stale in ["'26605_V1_1_README_UPLOAD.txt'","'V1_1_26605_*'","'build_26605_v1_1_compiler_correction.sh'","'handoff_payload_26605_v1_1/**'"]:
  if stale in w:fail('stale/overlapping 26605 trigger survived '+stale)
 if ns.success_26605_script:
  if git_blob(ns.success_26605_script)!=SUCCESS_26605_SCRIPT_BLOB:fail('successful-26605 V1.1 build script blob')
  prior=Path(ns.success_26605_script).read_text()
  if check_order(prior,'26605 V1.1')!=sig:fail('core compiler/build mechanics differs from successful 26605 V1.1')
  # Core candidate snapshot helper must remain byte-identical.
  a=next(line for line in prior.splitlines() if line.startswith('snapshot_candidate_from_authority(){'))
  b=next(line for line in s.splitlines() if line.startswith('snapshot_candidate_from_authority(){'))
  if a!=b:fail('snapshot_candidate_from_authority mechanics changed')
 if ns.success_26605_workflow:
  if git_blob(ns.success_26605_workflow)!=SUCCESS_26605_WORKFLOW_BLOB:fail('successful-26605 V1.1 workflow blob')
  workflow_shape(Path(ns.success_26605_workflow).read_text(),'26605 V1.1')
 for p,want,label in [(ns.golden_26593_script,GOLDEN_26593_SCRIPT_SHA,'26593 script'),(ns.golden_26593_workflow,GOLDEN_26593_WORKFLOW_SHA,'26593 workflow')]:
  if p and H(p)!=want:fail(label+' SHA')
 print('PASS exact successful-26605 V1.1 compiler/build/workflow order, action versions, glslang pin, language/NDK/full-assemble ordering and candidate freeze mechanics inherited')
 print('PASS infrastructure delta limited to 26606 identity, successful-26605 authority, required backup proof, 4-file scope, 36-shader coverage and SHORT-rescue semantic/regression gates')
if __name__=='__main__':main()
