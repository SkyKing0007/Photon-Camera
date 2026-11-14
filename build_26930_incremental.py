#!/usr/bin/env python3
"""Photon 26930: 26929 V2 *successful compiled* candidate authority, never stale repo app/src.
Exact source allowlist, full pinned GLSL/NDK/Kotlin/Java, clean Actions artifact proof.
No sources are committed or pushed by this runner.
"""
from __future__ import annotations
import argparse,gzip,hashlib,json,os,pathlib,shutil,subprocess,sys,tarfile,urllib.request,zipfile
R=pathlib.Path(__file__).resolve().parent
TMP=R/'.photon_26930_work';OUT=R/'photon_26930_outputs'
ART=TMP/'26929-success.zip';BASE=TMP/'authority_26929';CAND=TMP/'candidate_26930'
RUN=43560611365;COMMIT='a64766fee30f2e331c93d4f58b5be09ca0f26187';ART_ID=14101225406
ART_SHA='3735f4c4f27499d544470705a90ad9443f8b181fab2351b4a3d3082f00fbab29'
TAR_SHA='6a87a98ea3e3e793e17f14082d58da58d56ceeb129abbf92f28205347f835353'
BUILDER_SHA='0de6d9d194723cee79d6ff16a9792ae81479c6390cf5cf7db62c15aa11a7765b'
WORKFLOW_SHA='4a8e582844d7df878f90806f9c3ad68831ba3775805edea6bae342a2ab26ed53'
PRIOR_APK_SHA='cf3cc017a322763a444cba582af18fb40c250cb0cd8dd715c65afdda850612d0'
REPO='SkyKing0007/Photon-Camera';BRANCH='experimental-clean-photon-rebuild'
APKNAME='IrisCamera-0.9726930-26930-iris-rawr-debug.apk'
NBASE=2041;NFILES=2041;NCHANGE=3;NADD=0;NPROTECTED=2038

def fail(s):raise RuntimeError('26930 BLOCKED: '+str(s))
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
 return h.hexdigest()
def parse(p):
 result={}
 for line in p.read_text().splitlines():
  h,name=line.split('  ',1)
  if len(h)!=64 or name in result or not name.startswith('app/') or '..' in pathlib.PurePosixPath(name).parts:fail('invalid manifest '+line)
  result[name]=h
 return result
def scan(root):
 d={}
 for p in [*(root/'app/src').rglob('*'),root/'app/build.gradle',root/'app/version.properties']:
  if p.is_symlink():fail('source symlink '+str(p))
  if p.is_file():d[p.relative_to(root).as_posix()]=sha(p)
 return d
def exact(root,manifest,label):
 actual=scan(root);expected=parse(R/manifest)
 if actual!=expected:fail(label+f' missing={sorted(expected.keys()-actual.keys())[:8]} extra={sorted(actual.keys()-expected.keys())[:8]} wrong={[k for k in expected if actual.get(k)!=expected[k]][:8]}')
 print('PASS',label,len(actual));return actual
def scope():
 original=parse(R/'26930_BASE_26929_FULL_APP.sha256');target=parse(R/'26930_EXPECTED_FULL_APP.sha256')
 changes=set((R/'26930_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
 added=set((R/'26930_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
 deleted=(R/'26930_DELETED_RUNTIME_PATHS.txt').read_text().strip()
 if (len(original),len(target),len(changes),len(added),bool(deleted))!=(NBASE,NFILES,NCHANGE,NADD,False):fail('source universe/count or deleted paths')
 if {k for k in original if target.get(k)!=original[k]}!=changes or set(target)-set(original)!=added or set(original)-set(target):fail('source allowlist exactly changed/added mismatch')
 protected={k:v for k,v in original.items() if k not in changes}
 if parse(R/'26930_PROTECTED_SOURCE.sha256')!=protected or len(protected)!=NPROTECTED:fail('2038 protected source mismatch')
 if 'app/version.properties' not in changes:fail('26930 version missing')
 for p in changes|added:
  if '/vendor/' in p or '/jniLibs/' in p or p.endswith('.so') or p.startswith('app/src/main/cpp/iris26864/vendor/'):fail('illegal vendor/native mutation '+p)
 return changes,added,original,target

def seal():
 changes,added,_,_=scope()
 lines=(R/'26930_HANDOFF_HASHES.sha256').read_text().splitlines()
 if not lines:fail('empty staged manifest')
 files={}
 for line in lines:
  h,path=line.split('  ',1)
  f=R/path
  if path in files or not f.is_file() or sha(f)!=h:fail('staged SHA mismatch or missing file '+path)
  files[path]=h
 essential={
  'build_26930_incremental.py','.github/workflows/build-26930-change-aware.yml',
  'test_26930_workflow_refs.py','test_26930_sealed_negatives.py','test_26930_source.py',
  'test_26930_chroma_math.py','test_26930_shader_contract.py','test_26930_shader_shadow.py',
  'test_26930_patch_proof.py','compile_26930_shaders.sh','compile_26930_hr_spirv.sh',
  '26930_FORWARD_FULLINDEX.patch','26930_ROLLBACK_FULLINDEX.patch',
  '26930_BASE_26929_FULL_APP.sha256','26930_EXPECTED_FULL_APP.sha256',
  '26930_PROTECTED_SOURCE.sha256','26930_CHANGED_RUNTIME_ALLOWLIST.txt',
  '26930_ADDED_RUNTIME_PATHS.txt','26930_DELETED_RUNTIME_PATHS.txt',
  '26930_EXPECTED_ACTION_EXECUTABLES.txt','TRIGGER_26930.txt',
  '26930_V1_STAGE_1_UPLOAD_PATHS.txt','26930_V1_STAGE_2_UPLOAD_PATHS.txt','26930_V1_STAGE_3_UPLOAD_PATHS.txt'}
 if not essential.issubset(files):fail('one or more 26930 mandatory verifier/compiler/trigger stages missing')
 # Stage 1 must contain EVERY uploaded file except the YAML and trigger;
 # stage 2 contains the YAML only; stage 3 contains the changed trigger only.
 stages=[(R/f'26930_V1_STAGE_{i}_UPLOAD_PATHS.txt').read_text().splitlines() for i in (1,2,3)]
 assert all(len(x)==len(set(x)) and x==sorted(x) for x in stages)
 wfpath='.github/workflows/build-26930-change-aware.yml'
 trigger='TRIGGER_26930.txt'
 sealed=set(files)|{'26930_HANDOFF_HASHES.sha256'}
 if stages[1]!=[wfpath] or stages[2]!=[trigger] or set(stages[0])!=sealed-{wfpath,trigger} or set(stages[0])&set(stages[1]+stages[2]):fail('26930 V1 three-stage upload path universe/ordering violates exactly 1=ALL, 2=YML, 3=TRIGGER')
 staged={k.removeprefix('handoff_payload_26930/') for k in files if k.startswith('handoff_payload_26930/')}
 actual={p.relative_to(R/'handoff_payload_26930').as_posix() for p in (R/'handoff_payload_26930').rglob('*') if p.is_file()}
 if staged!=(changes|added) or actual!=staged:fail('staged overlay differs from EXACT runtime changed-file scope')
 wf=(R/'.github/workflows/build-26930-change-aware.yml').read_text()
 for pin in ['TRIGGER_26930.txt','verify_26904_v3_safety.py','verify_26904_v2_safety.py','verify_26906_native_cache.py preflight',
             'test_26925_shader_abi.py --payload','test_26930_shader_shadow.py --live --cmake',
             'build_26930_incremental.py verify-compiled','build_26930_incremental.py finalize',':app:assembleDebug']:
  if pin not in wf:fail('historical/live proof missing from 26930 workflow '+pin)
 if wf.count('actions/upload-artifact@v4')!=1 or 'test_26922_guard.py' in wf:fail('unexpected upload/historical stale dependency')
 if 'test_26903_v3_sealed_negatives.py' in wf or 'build_26902_iris_rawr.sh' in wf:fail('not part of successful 26929 V2 change-aware procedure: obsolete runner dependency')
 if 'test_26903_v3_archive_receipt.py' not in wf or 'test_26903_modes.py .' not in wf:fail('26903 source/archive regression lost')
 # The original successful 26929 historical source and all its compiler gates
 # execute BEFORE the 26930 overlay. Native source/CMake inputs remain EXACT
 # SHA-protected 26929 bytes on both sides of the overlay; the original cache
 # key therefore remains valid and cannot cross an NDK input fingerprint.
 if wf.index('build_26930_incremental.py prepare') >= wf.index('id: native-cache-26930'):fail('new native cache restored before 26930 source overlay')
 if not (wf.index('build_26929_incremental.py verify-compiled') < wf.index('build_26930_incremental.py prepare') < wf.index('build_26930_incremental.py verify-compiled') < wf.rfind(':app:assembleDebug')):fail('26929 real compiler / 26930 overlay / APK gate order')
 if sha(R/'build_26930_incremental.py')!=files['build_26930_incremental.py'] or sha(R/'.github/workflows/build-26930-change-aware.yml')!=files['.github/workflows/build-26930-change-aware.yml']:fail('executed builder/workflow mutated')
 subprocess.run(['python3','-S','test_26930_workflow_refs.py'],cwd=R,check=True)
 print('PASS 26930 sealed 2041->2041, 3 changed, 0 added, 2038 protected, baseline exactly successful 26929 V2')

def fetch():
 seal();token=os.getenv('GITHUB_TOKEN','')
 if not token:fail('GitHub Actions token absent')
 if os.getenv('GITHUB_REPOSITORY',REPO)!=REPO or os.getenv('GITHUB_REF_NAME',BRANCH)!=BRANCH:fail('incorrect repository or branch')
 def gh(s):
  req=urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+s,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'})
  with urllib.request.urlopen(req,timeout=120) as f:return json.load(f)
 run=gh('actions/runs/'+str(RUN));art=gh('actions/artifacts/'+str(ART_ID))
 if run.get('conclusion')!='success' or run.get('id')!=RUN or run.get('head_sha')!=COMMIT or run.get('head_branch')!=BRANCH:fail('26929 V2 Actions runtime authority invalid')
 if art.get('expired') or art.get('id')!=ART_ID or art.get('digest')!='sha256:'+ART_SHA:fail('26929 V2 published artifact invalid')
 TMP.mkdir(exist_ok=True)
 subprocess.run(['curl','--fail','--location','--retry','3','--silent','--show-error','-H','Authorization: Bearer '+token,'-H','Accept: application/vnd.github+json',f'https://api.github.com/repos/{REPO}/actions/artifacts/{ART_ID}/zip','-o',str(ART)],check=True)
 if sha(ART)!=ART_SHA:fail('downloaded 26929 artifact SHA mismatch')
 print('PASS EXACT successful 26929 V2 run and published artifact SHA')
def safe_tar(path,destination):
 with tarfile.open(path,'r:gz') as tar:
  for m in tar:
   p=pathlib.PurePosixPath(m.name)
   if not p.parts or p.parts[0]!='app' or p.is_absolute() or '..' in p.parts or not(m.isfile() or m.isdir()):fail('unsafe baseline source TAR '+m.name)
  tar.extractall(destination,filter='data')
def prepare():
 seal()
 if not ART.is_file() or sha(ART)!=ART_SHA:fail('26929 artifact absent/corrupt; fetch first')
 for d in (BASE,CAND):
  if d.exists():shutil.rmtree(d)
 BASE.mkdir(parents=True)
 with zipfile.ZipFile(ART) as zip0:
  def get(name):
   path='photon_26929_outputs/'+name
   if path not in zip0.namelist():fail('26929 missing authority receipt '+path)
   return zip0.read(path)
  data=get('26929_candidate_app_source.tar.gz')
  if hashlib.sha256(data).hexdigest()!=TAR_SHA:fail('26929 compiled TAR hash')
  if get('26929_PREBUILD_SEALED_APP.sha256')!=(R/'26930_BASE_26929_FULL_APP.sha256').read_bytes():fail('26929 actual compiled source manifest mismatch')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build_26929_incremental.py')).hexdigest()!=BUILDER_SHA or BUILDER_SHA not in get('26929_ACTUAL_EXECUTED_BUILDER.sha256').decode():fail('actual 26929 executed builder changed')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build-26929-change-aware.yml')).hexdigest()!=WORKFLOW_SHA or WORKFLOW_SHA not in get('26929_ACTUAL_EXECUTED_WORKFLOW.sha256').decode():fail('actual 26929 workflow changed')
  if PRIOR_APK_SHA not in get('26929_APK.sha256').decode():fail('actual published 26929 APK receipt missing')
  prior_tasks=get('26929_REAL_GRADLE_TASKS.txt').decode()
  for t in [':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',
            ':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',
            ':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',
            ':app:assembleDebug','BUILD SUCCESSFUL']:
   if 'PASS '+t not in prior_tasks:fail('published 26929 missing genuine ABI/Kotlin/Java/assemble task '+t)
  if 'BUILD SUCCESSFUL' not in get('26929_gradle_assemble.log').decode(errors='replace'):
   fail('26929 published original real Gradle build not successful')

  for text in ['REAL PINNED GLSL COMPILE: PASS','REAL SPIR-V VALIDATION: PASS','REAL KOTLIN COMPILE: PASS','REAL JAVA COMPILE: PASS','NATIVE/NDK COMPILE: PASS','REAL ANDROID Gradle :app:assembleDebug: PASS','RUNTIME SOURCE INVARIANCE: PASS']:
   if text not in get('26929_COMPILER_STATUS.txt').decode():fail('successful 26929 lacks actual compiler '+text)
  (TMP/'26929_candidate.tar.gz').write_bytes(data)
 safe_tar(TMP/'26929_candidate.tar.gz',BASE)
 exact(BASE,'26930_BASE_26929_FULL_APP.sha256','real successful 26929 V2 source')
 changes,added,_,_=scope();shutil.copytree(BASE,CAND)
 for p in sorted(changes|added):
  src=R/'handoff_payload_26930'/p;dst=CAND/p
  if not src.is_file() or (p in changes and not dst.is_file()) or (p in added and dst.exists()):fail('overlay missing/misclassified '+p)
  dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
 exact(CAND,'26930_EXPECTED_FULL_APP.sha256','candidate-first 26930')
 if not (R/'gradlew').is_file() or not (R/'app/build.gradle').is_file():fail('Android checkout missing')
 if (R/'app/src').exists():shutil.rmtree(R/'app/src')
 shutil.copytree(CAND/'app/src',R/'app/src')
 shutil.copy2(CAND/'app/version.properties',R/'app/version.properties')
 shutil.copy2(CAND/'app/build.gradle',R/'app/build.gradle')
 if (R/'app/.cxx').exists():shutil.rmtree(R/'app/.cxx')
 exact(R,'26930_EXPECTED_FULL_APP.sha256','LIVE compiled candidate source before building')
 OUT.mkdir(exist_ok=True)
 (OUT/'26930_SOURCE_SCOPE.txt').write_text(f'base=26929 V2 run={RUN} commit={COMMIT} artifact={ART_ID}\nZIP_SHA={ART_SHA} TAR_SHA={TAR_SHA} ACTUAL_BUILDER_SHA={BUILDER_SHA} WORKFLOW_SHA={WORKFLOW_SHA} APK_SHA={PRIOR_APK_SHA}\nfiles={NFILES} changed={NCHANGE} added={NADD} protected={NPROTECTED} deleted=0\n'+ '\n'.join(sorted(changes|added))+'\n')
 print('PASS candidate-first actual compiled 26929 V2 authority, exact 26930 scope, no stale repository source')
def regress():
 seal();exact(R,'26930_EXPECTED_FULL_APP.sha256','live 26930 source')
 for cmd in [['python3','-S','test_26930_source.py','--live'],['python3','-S','test_26930_chroma_math.py','--live'],['python3','-S','test_26930_shader_shadow.py','--live'],['python3','-S','test_26930_patch_proof.py','--live']]:
  subprocess.run(cmd,cwd=R,check=True)
 print('PASS 26930 native B ON noise-domain chroma residual and original fine luminance; exact patch proof')
def verify_compiled():
 regress()
 for name in ['26930_CURRENT_GLSL_SPIRV_REAL_COMPILER.txt','26930_WRONSKI_SPIRV_REAL_COMPILER.txt']:
  report=OUT/name
  if not report.is_file() or '16.5.0' not in report.read_text() or 'PASS' not in report.read_text():fail('mandatory real pinned ESSL/SPIR-V proof missing '+name)
 for name in ['26930_current_chroma_es300.frag','26930_current_fcc_median_es300.frag','26930_current_fcc_reconstruct_es300.frag']:
  if not (OUT/name).is_file():fail('expanded real GLES ESSL shader missing '+name)
 native=OUT/'26930_WRONSKI_SPIRV_REAL_COMPILER.txt'
 for p in ['app/src/main/cpp/iris26864/bridge/Iris26923WronskiFinalize.comp','app/src/main/cpp/iris26864/Iris26885WronskiChromaGuide.comp','app/src/main/cpp/iris26864/Iris26880WaveletCopy.comp']:
  if sha(R/p) not in native.read_text():fail('current Vulkan shader bytes not compiled '+p)
 (OUT/'26930_PREBUILD_SEALED_APP.sha256').write_bytes((R/'26930_EXPECTED_FULL_APP.sha256').read_bytes())
 print('PASS all genuine pinned GLSL real compiler results and exact source prebuild seal')
def finalize():
 regress()
 if (OUT/'26930_PREBUILD_SEALED_APP.sha256').read_bytes()!=(R/'26930_EXPECTED_FULL_APP.sha256').read_bytes():fail('source modified after real shader compilation')
 log=(OUT/'26930_gradle_assemble.log').read_text(errors='replace')
 tasks=[':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL']
 for task in tasks:
  if task not in log:fail('actual Gradle compiler/assembly task absent '+task)
 for cmd in [['python3','-S','test_26930_shader_shadow.py','--live','--cmake'],['python3','-S','test_26920_vulkan_abi.py','--live','--cmake']]:
  subprocess.run(cmd,cwd=R,check=True)
 apks=list((R/'app/build/outputs/apk').rglob('*.apk'))
 if len(apks)!=1:fail('exactly ONE built APK required '+repr(apks))
 shutil.copy2(apks[0],R/APKNAME)
 if (R/APKNAME).stat().st_size<1_000_000:fail('APK suspicious size')
 (OUT/'26930_COMPILER_STATUS.txt').write_text('REAL PINNED GLSL COMPILE: PASS\nREAL SPIR-V VALIDATION: PASS\nREAL KOTLIN COMPILE: PASS\nREAL JAVA COMPILE: PASS\nNATIVE/NDK COMPILE: PASS (arm64-v8a, armeabi-v7a)\nREAL ANDROID Gradle :app:assembleDebug: PASS\nRUNTIME SOURCE INVARIANCE: PASS\nDEVICE IMAGE QUALITY: NOT RUN\n')
 (OUT/'26930_REAL_GRADLE_TASKS.txt').write_text(''.join('PASS '+task+'\n' for task in tasks))
 (OUT/'26930_APK.sha256').write_text(sha(R/APKNAME)+'  '+APKNAME+'\n')
 wf=R/'.github/workflows/build-26930-change-aware.yml'
 (OUT/'26930_ACTUAL_EXECUTED_BUILDER.sha256').write_text(sha(R/'build_26930_incremental.py')+'  build_26930_incremental.py\n')
 (OUT/'26930_ACTUAL_EXECUTED_WORKFLOW.sha256').write_text(sha(wf)+'  .github/workflows/build-26930-change-aware.yml\n')
 (OUT/'26930_ACTIONS_IDENTITY.txt').write_text('git_sha='+os.getenv('GITHUB_SHA','NOT_IN_ACTIONS')+'\ngithub_run_id='+os.getenv('GITHUB_RUN_ID','NOT_IN_ACTIONS')+'\n')
 for p in ['26930_BASE_26929_FULL_APP.sha256','26930_EXPECTED_FULL_APP.sha256','26930_PROTECTED_SOURCE.sha256','26930_CHANGED_RUNTIME_ALLOWLIST.txt','26930_ADDED_RUNTIME_PATHS.txt','26930_DELETED_RUNTIME_PATHS.txt']:
  shutil.copy2(R/p,OUT/p)
 shutil.copy2(R/'build_26930_incremental.py',OUT/'ACTUAL_EXECUTED_build_26930_incremental.py')
 shutil.copy2(wf,OUT/'ACTUAL_EXECUTED_build-26930-change-aware.yml')
 with (OUT/'26930_candidate_app_source.tar.gz').open('wb') as target:
  with gzip.GzipFile(filename='',mode='wb',compresslevel=1,mtime=0,fileobj=target) as gz:
   with tarfile.open(fileobj=gz,mode='w') as t:
    for path in sorted(parse(R/'26930_EXPECTED_FULL_APP.sha256')):
     src=R/path;info=t.gettarinfo(str(src),arcname=path);info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
     with src.open('rb') as fp:t.addfile(info,fp)
 (OUT/'26930_candidate_app_source.tar.gz.sha256').write_text(sha(OUT/'26930_candidate_app_source.tar.gz')+'  26930_candidate_app_source.tar.gz\n')
 print('PASS actual Android dual-ABI assembled 26930 APK, source TAR and final immutable proof')
if __name__=='__main__':
 try:
  p=argparse.ArgumentParser();p.add_argument('command',choices=('seal','fetch','prepare','regress','verify-compiled','finalize'));globals()[p.parse_args().command.replace('-','_')]()
 except Exception as e:print('ERROR',str(e),file=sys.stderr);sys.exit(1)
