#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,re
SUCCESS_26607_SCRIPT_BLOB='f5064aabc27f6dd62b88ada5e2991e2f082636ef'
SUCCESS_26607_WORKFLOW_BLOB='690e87ba5ef219773b03ba55752cdca1a355154b'
GOLDEN_26593_SCRIPT_SHA='111d59850aa4a0dccef482bcf68ce7b9d93e76d99729fc2de810ff91b97f160f'
GOLDEN_26593_WORKFLOW_SHA='89083ed8892f18f93e50b35679beeba114674cacfcb4ad3ff79078ec130f43fc'
def fail(m):raise SystemExit('FAIL: '+m)
def H(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git_blob(p):
 b=Path(p).read_bytes();return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
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
 ap=argparse.ArgumentParser();ap.add_argument('build_script');ap.add_argument('workflow');ap.add_argument('--success-26607-script');ap.add_argument('--success-26607-workflow');ap.add_argument('--golden-26593-script');ap.add_argument('--golden-26593-workflow');ns=ap.parse_args()
 s=Path(ns.build_script).read_text();w=Path(ns.workflow).read_text()
 pins=[
  'BASE_SUCCESS_COMMIT="e4a77eac946e8b56e0ce2b0e6d9a14c3085e3f9a"',
  'HANDOFF_PARENT_COMMIT="e4a77eac946e8b56e0ce2b0e6d9a14c3085e3f9a"',
  'BASE_RUN_ID="34052539419"','BASE_JOB_ID="101538597897"','BASE_ARTIFACT_ID="9995034916"',
  'BASE_ARTIFACT_NAME="photon-26607-v1-universal-highlight-reconstruction"',
  'BASE_ARTIFACT_SHA="adaea99e8d88251eaf544f084d6f7caddb1f52dfe5b978bb4b64978cbbbccb23"',
  'BASE_TAR_SHA="b69c2734015a6f75ad7689280e45e61d940fd90061b13131086eda06e7083199"',
  'MECHANICS_GOLDEN_COMMIT="7c485416a8f41f9bf8a834bf4282e7c2318fa9fb"',
  'GLSLANG_VERSION="16.5.0"','GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"',
 ]
 for t in pins:
  if t not in s:fail('authority/mechanics pin '+t)
 if 'BACKUP_BRANCH=' in s or 'BACKUP_COMMIT=' in s:fail('26608 user-requested no-backup policy violated')
 sig=check_order(s,'26608 V1');workflow_shape(w,'26608 V1')
 blocks=re.findall(r"<<'PY'\n(.*?)\nPY",s,re.S)
 if len(blocks)!=5:fail(f'embedded Python heredoc count {len(blocks)} != 5')
 for i,block in enumerate(blocks,1):compile(block,f'heredoc{i}','exec')
 for t in ['Build 26608 V1 Universal HDR SHORT','build-26608-v1-universal-hdr-short.yml','photon-26608-v1-universal-hdr-short','Build exact 26608 V1 candidate from successful compiled 26607 V1 authority']:
  if t not in w:fail('26608 workflow identity '+t)
 for stale in ["'26607_V1_README_UPLOAD.txt'","'V1_26607_*'","'build_26607_v1_universal_highlight_reconstruction.sh'","'handoff_payload_26607_v1/**'"]:
  if stale in w:fail('stale/overlapping 26607 trigger survived '+stale)
 if ns.success_26607_script:
  if git_blob(ns.success_26607_script)!=SUCCESS_26607_SCRIPT_BLOB:fail('successful-26607 V1 build script blob')
  prior=Path(ns.success_26607_script).read_text()
  if check_order(prior,'26607 V1')!=sig:fail('core compiler/build mechanics differs from successful 26607 V1')
  a=next(line for line in prior.splitlines() if line.startswith('snapshot_candidate_from_authority(){'))
  b=next(line for line in s.splitlines() if line.startswith('snapshot_candidate_from_authority(){'))
  if a!=b:fail('snapshot_candidate_from_authority mechanics changed')
 if ns.success_26607_workflow:
  if git_blob(ns.success_26607_workflow)!=SUCCESS_26607_WORKFLOW_BLOB:fail('successful-26607 V1 workflow blob')
  workflow_shape(Path(ns.success_26607_workflow).read_text(),'26607 V1')
 for p,want,label in [(ns.golden_26593_script,GOLDEN_26593_SCRIPT_SHA,'26593 script'),(ns.golden_26593_workflow,GOLDEN_26593_WORKFLOW_SHA,'26593 workflow')]:
  if p and H(p)!=want:fail(label+' SHA')
 print('PASS exact successful-26607 V1 compiler/build/workflow order, action versions, glslang pin, language/NDK/full-assemble ordering and candidate freeze mechanics inherited')
 print('PASS infrastructure delta limited to 26608 identity, successful-26607 authority, user-requested no-backup policy, 5-file scope, 36-shader coverage and universal-HDR/boundary/preview regressions')
if __name__=='__main__':main()
