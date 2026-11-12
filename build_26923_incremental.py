#!/usr/bin/env python3
"""26923 guarded Actions builder, candidate-first exact successful 26922 compiled runtime.
The toolchain, full Android Gradle APK, shaders, historical failures and native guards
remain inherited from 26922/26920 V5; this script never commits or pushes source.
"""
from __future__ import annotations
import argparse,gzip,hashlib,json,os,pathlib,shutil,subprocess,sys,tarfile,urllib.request,zipfile
R=pathlib.Path(__file__).resolve().parent
TMP=R/'.photon_26923_work';OUT=R/'photon_26923_outputs'
ART=TMP/'26922-success.zip';BASE=TMP/'authority_26922';CAND=TMP/'candidate_26923'
RUN=43244491393;COMMIT='dba91b24382137beaf5efdb55c52b0a64a50a787';ART_ID=13955994080
ART_SHA='d837101a7fa13baee243502568e489907834668bc346bbbfa0f85a6184ba9eba'
TAR_SHA='1dd8cdbc7ccebb70d7866c1a25edaca3e8d0c8840aeb5724dd2076628ee0f53c'
BUILDER_SHA='8e4391d2904438608556d2152bf4377ee258a6b6cfdd959438572579cd89f0e0'
WORKFLOW_SHA='abba4ac893f9ba9592b767597ccac99bcfc7442cd51b59cac3fb08933baf8312'
PRIOR_APK_SHA='ae698e313b587bef33ae51d976e7cc280b16f0f0f42554c1e3834bb0de4e3973'
REPO='SkyKing0007/Photon-Camera';BRANCH='experimental-clean-photon-rebuild'
APKNAME='IrisCamera-0.9726923-26923-iris-rawr-debug.apk'
CHANGE={
 'app/src/main/cpp/iris26864/Iris26864FrozenDirectRawrRunner.cpp',
 'app/src/main/cpp/iris26864/Iris26864RealRawrCoordinator.cpp',
 'app/src/main/cpp/iris26864/Iris26864VendorRawr.cmake',
 'app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqCoordinator.cpp',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
 'app/src/main/java/com/hinnka/mycamera/processor/Iris26920NativeProbe.java',
 'app/version.properties',
}
ADDED={'app/src/main/cpp/iris26864/bridge/Iris26923WronskiFinalize.comp'}
NBASE=2038;NFILES=2039

def fail(s):raise RuntimeError('26923 BLOCKED: '+str(s))
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
 return h.hexdigest()
def parse(p):
 d={}
 for line in p.read_text().splitlines():
  h,name=line.split('  ',1)
  if len(h)!=64 or name in d or not name.startswith('app/') or '..' in pathlib.PurePosixPath(name).parts:fail('invalid manifest '+line)
  d[name]=h
 return d
def scan(root):
 result={}
 for p in [*list((root/'app/src').rglob('*')),root/'app/build.gradle',root/'app/version.properties']:
  if p.is_symlink():fail('source symlink '+str(p))
  if p.is_file():result[p.relative_to(root).as_posix()]=sha(p)
 return result
def exact(root,manifest,label):
 exp=parse(R/manifest);got=scan(root)
 if exp!=got:fail(f'{label}: missing={sorted(exp.keys()-got.keys())[:8]} extra={sorted(got.keys()-exp.keys())[:8]} wrong={[p for p in exp if got.get(p)!=exp[p]][:8]}')
 print('PASS',label,len(got));return got
def border(root):
 for p,h in parse(R/'26923_FROZEN_26917_BORDER.sha256').items():
  if not (root/p).is_file() or sha(root/p)!=h:fail('26917 physical CFA border altered '+p)
def seal():
 lines=(R/'26923_HANDOFF_HASHES.sha256').read_text().splitlines()
 if not lines:fail('empty sealed manifest')
 files={}
 for line in lines:
  h,p=line.split('  ',1)
  if p in files:fail('duplicate sealed path '+p)
  f=R/p
  if not f.is_file() or sha(f)!=h:fail('staged hash mismatch '+p)
  files[p]=h
 if set((R/'26923_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())!=CHANGE:fail('incorrect runtime allowlist')
 old=parse(R/'26923_BASE_26922_FULL_APP.sha256');new=parse(R/'26923_EXPECTED_FULL_APP.sha256')
 if len(old)!=NBASE or len(new)!=NFILES or set(new)-set(old)!=ADDED or set(old)-set(new):fail('incorrect added/removed 26923 scope')
 if {p for p in old if old[p]!=new[p]}!=CHANGE:fail('incorrect 7 changed 26923 scope')
 if set((R/'26923_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())!=ADDED or (R/'26923_DELETED_RUNTIME_PATHS.txt').read_text():fail('incorrect new shader or deleted path')
 if parse(R/'26923_PROTECTED_SOURCE.sha256')!={p:h for p,h in old.items() if p not in CHANGE}:fail('2031 protected-path mismatch')
 if '26923_FORWARD_FULLINDEX.patch' not in files or 'compile_26923_shaders.sh' not in files or 'compile_26923_lk_shaders.py' not in files:fail('missing mandatory compiler or patch')
 if files.get('.github/workflows/build-26923-change-aware.yml')!=sha(R/'.github/workflows/build-26923-change-aware.yml'):fail('workflow mutation')
 print('PASS 26923 sealed three-stage upload, 2039 sources, 7 changed, 1 new, 2031 protected')
def fetch():
 seal();token=os.getenv('GITHUB_TOKEN','')
 if not token:fail('Actions credential unavailable')
 if os.getenv('GITHUB_REPOSITORY',REPO)!=REPO or os.getenv('GITHUB_REF_NAME',BRANCH)!=BRANCH:fail('wrong Actions repo/branch')
 def gh(path):
  req=urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+path,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'})
  with urllib.request.urlopen(req,timeout=120) as f:return json.load(f)
 run=gh('actions/runs/'+str(RUN));art=gh('actions/artifacts/'+str(ART_ID))
 if run.get('id')!=RUN or run.get('conclusion')!='success' or run.get('head_sha')!=COMMIT or run.get('head_branch')!=BRANCH:fail('26922 Actions success provenance')
 if art.get('id')!=ART_ID or art.get('expired') or art.get('digest')!='sha256:'+ART_SHA:fail('26922 published digest')
 TMP.mkdir(exist_ok=True)
 subprocess.run(['curl','--fail','--location','--retry','3','--silent','--show-error','-H','Authorization: Bearer '+token,'-H','Accept: application/vnd.github+json',f'https://api.github.com/repos/{REPO}/actions/artifacts/{ART_ID}/zip','-o',str(ART)],check=True)
 if sha(ART)!=ART_SHA:fail('26922 downloaded artifact corrupt')
 print('PASS exact successful 26922 Actions runtime authority, builder, workflow and artifact')
def safe_tar(p,d):
 with tarfile.open(p,'r:gz') as tar:
  for m in tar:
   x=pathlib.PurePosixPath(m.name)
   if x.is_absolute() or '..' in x.parts or not x.parts or x.parts[0]!='app' or not(m.isfile() or m.isdir()):fail('unsafe TAR '+m.name)
  tar.extractall(d,filter='data')
def prepare():
 seal()
 if not ART.is_file() or sha(ART)!=ART_SHA:fail('26922 artifact missing or corrupted')
 for d in (BASE,CAND):
  if d.exists():shutil.rmtree(d)
 BASE.mkdir(parents=True)
 with zipfile.ZipFile(ART) as z:
  def get(name):
   p='photon_26922_outputs/'+name
   if p not in z.namelist():fail('26922 authority receipt missing '+p)
   return z.read(p)
  body=get('26922_candidate_app_source.tar.gz')
  if hashlib.sha256(body).hexdigest()!=TAR_SHA:fail('26922 exact source TAR differs')
  if get('26922_PREBUILD_SEALED_APP.sha256')!=(R/'26923_BASE_26922_FULL_APP.sha256').read_bytes():fail('26922 compiled source manifest does not match')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build_26922_incremental.py')).hexdigest()!=BUILDER_SHA or BUILDER_SHA not in get('26922_ACTUAL_EXECUTED_BUILDER.sha256').decode():fail('26922 executed builder differs')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build-26922-change-aware.yml')).hexdigest()!=WORKFLOW_SHA or WORKFLOW_SHA not in get('26922_ACTUAL_EXECUTED_WORKFLOW.sha256').decode():fail('26922 executed workflow differs')
  if PRIOR_APK_SHA not in get('26922_APK.sha256').decode():fail('26922 APK not published')
  for x in ['REAL PINNED GLSL COMPILE: PASS','REAL SPIR-V VALIDATION: PASS','REAL KOTLIN COMPILE: PASS','REAL JAVA COMPILE: PASS','NATIVE/NDK COMPILE: PASS','REAL ANDROID Gradle :app:assembleDebug: PASS','RUNTIME SOURCE INVARIANCE: PASS']:
   if x not in get('26922_COMPILER_STATUS.txt').decode():fail('26922 compiler receipt lacks '+x)
  (TMP/'26922_candidate.tar.gz').write_bytes(body)
 safe_tar(TMP/'26922_candidate.tar.gz',BASE)
 exact(BASE,'26923_BASE_26922_FULL_APP.sha256','actual 26922 compiled authority')
 border(BASE);shutil.copytree(BASE,CAND)
 for p in sorted(CHANGE | ADDED):
  source=R/'handoff_payload_26923'/p;target=CAND/p
  if not source.is_file() or (p in CHANGE and not target.is_file()) or (p in ADDED and target.exists()):fail('invalid candidate overlay '+p)
  target.parent.mkdir(parents=True,exist_ok=True)
  shutil.copy2(source,target)
 exact(CAND,'26923_EXPECTED_FULL_APP.sha256','candidate-first 26923 correction')
 border(CAND)
 if not (R/'gradlew').is_file() or not (R/'app/build.gradle').is_file():fail('existing Gradle project absent')
 if (R/'app/src').exists():shutil.rmtree(R/'app/src')
 shutil.copytree(CAND/'app/src',R/'app/src')
 shutil.copy2(CAND/'app/version.properties',R/'app/version.properties')
 shutil.copy2(CAND/'app/build.gradle',R/'app/build.gradle')
 exact(R,'26923_EXPECTED_FULL_APP.sha256','live seeded Android candidate')
 border(R);OUT.mkdir(exist_ok=True)
 (OUT/'26923_SOURCE_SCOPE.txt').write_text(f'base=26922 Actions run={RUN} commit={COMMIT} artifact={ART_ID} sha256={ART_SHA} tar_sha256={TAR_SHA}\nsource=2039 changed=7 protected=2031 added=1 deleted=0 infrastructure_delta=new versioned runner+workflow+validators+manifest+trigger only\n'+'\n'.join(sorted(CHANGE))+'\n')
 print('PASS candidate-first reconstruction from 26922, original inherited 26920 V5 NDK shader/cache/build procedure preserved')
def regress():
 seal();exact(R,'26923_EXPECTED_FULL_APP.sha256','26923 current live source')
 subprocess.run(['python3','-S','test_26923_source.py','--live'],cwd=R,check=True)
 subprocess.run(['python3','-S','test_26923_math_host.py','--live'],cwd=R,check=True)
 border(R)
 print('PASS 26923 active paths B ON, B OFF frozen, 26922 reference provenance')
def verify_compiled():
 regress()
 for p in ['photon_26920_outputs/26920_LK_GLSL_SPIRV_REAL_COMPILER.txt','photon_26917_outputs/26917_AMAZE_IMPORT_SHADER_REAL_COMPILER.txt','photon_26917_outputs/26917_AMAZE_IMPORT_SPIRV_VALIDATED.txt','photon_26906_outputs/26906_TONE_SHADER_REAL_COMPILER.txt','photon_26923_outputs/26923_SHADER_REAL_COMPILER.txt']:
  if not (R/p).is_file():fail('real compiler receipt missing '+p)
 text=(R/'photon_26920_outputs/26920_LK_GLSL_SPIRV_REAL_COMPILER.txt').read_text()
 if '16.5.0' not in text:fail('pinned 26920 GLSL compiler altered')
 for p in ['app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/alignment/shaders/lk_refine.comp','app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/merge_wronski/shaders/robust_photometric.comp']:
  if sha(R/p) not in text:fail('26920 LK compiler hash does not match current source '+p)
 for variant in ('prod','trace'):
  for name in ('lk_refine','robust_photometric'):
   for suffix in ('.spv','.opt.spv'):
    p=R/f'photon_26920_outputs/26920_lk_shaders/{name}_{variant}{suffix}'
    if not p.is_file() or p.stat().st_size<256 or sha(p) not in text:fail('missing current LK SPIR-V proof '+str(p))
 shader_text=(R/'photon_26923_outputs/26923_SHADER_REAL_COMPILER.txt').read_text()
 for p in ('app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag','app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt'):
  if sha(R/p) not in shader_text:fail('compiled 26923 shader source hash not recorded '+p)
 
 proof=R/'photon_26923_outputs/26923_WRONSKI_HR_SPIRV_REAL_COMPILER.txt'
 if not proof.is_file() or sha(R/'app/src/main/cpp/iris26864/bridge/Iris26923WronskiFinalize.comp') not in proof.read_text():
  fail('26923 real shader optimizer/validator receipt missing')
 (OUT/'26923_PREBUILD_SEALED_APP.sha256').write_bytes((R/'26923_EXPECTED_FULL_APP.sha256').read_bytes())
 print('PASS real pinned current SR shader/SPIR-V + historical shader full compile + exact prebuild freeze')
def finalize():
 regress()
 if (OUT/'26923_PREBUILD_SEALED_APP.sha256').read_bytes()!=(R/'26923_EXPECTED_FULL_APP.sha256').read_bytes():fail('prebuild frozen source not identical')
 logf=OUT/'26923_gradle_assemble.log'
 if not logf.is_file():fail('real Android Gradle output absent')
 log=logf.read_text(errors='replace')
 tasks=[':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL']
 for task in tasks:
  if task not in log:fail('real Android compiler/assembly gate missing '+task)
 apks=list((R/'app/build/outputs/apk').rglob('*.apk'))
 if len(apks)!=1:fail('exactly one APK required '+repr(apks))
 shutil.copy2(apks[0],R/APKNAME)
 if (R/APKNAME).stat().st_size<1_000_000:fail('APK suspiciously small')
 (OUT/'26923_COMPILER_STATUS.txt').write_text('REAL PINNED GLSL COMPILE: PASS\nREAL SPIR-V VALIDATION: PASS\nREAL KOTLIN COMPILE: PASS\nREAL JAVA COMPILE: PASS\nNATIVE/NDK COMPILE: PASS (arm64-v8a, armeabi-v7a)\nREAL ANDROID Gradle :app:assembleDebug: PASS\nRUNTIME SOURCE INVARIANCE: PASS\nDEVICE IMAGE QUALITY: NOT RUN\n')
 (OUT/'26923_REAL_GRADLE_TASKS.txt').write_text(''.join('PASS '+task+'\n' for task in tasks))
 (OUT/'26923_APK.sha256').write_text(sha(R/APKNAME)+'  '+APKNAME+'\n')
 (OUT/'26923_ACTUAL_EXECUTED_BUILDER.sha256').write_text(sha(R/'build_26923_incremental.py')+'  build_26923_incremental.py\n')
 wf=R/'.github/workflows/build-26923-change-aware.yml'
 (OUT/'26923_ACTUAL_EXECUTED_WORKFLOW.sha256').write_text(sha(wf)+'  .github/workflows/build-26923-change-aware.yml\n')
 (OUT/'26923_ACTIONS_IDENTITY.txt').write_text('git_sha='+os.getenv('GITHUB_SHA','unknown')+'\ngithub_run_id='+os.getenv('GITHUB_RUN_ID','unknown')+'\n')
 for p in ['26923_BASE_26922_FULL_APP.sha256','26923_EXPECTED_FULL_APP.sha256','26923_PROTECTED_SOURCE.sha256','26923_CHANGED_RUNTIME_ALLOWLIST.txt','26923_ADDED_RUNTIME_PATHS.txt']:shutil.copy2(R/p,OUT/p)
 shutil.copy2(R/'build_26923_incremental.py',OUT/'ACTUAL_EXECUTED_build_26923_incremental.py')
 shutil.copy2(wf,OUT/'ACTUAL_EXECUTED_build-26923-change-aware.yml')
 with (OUT/'26923_candidate_app_source.tar.gz').open('wb') as raw:
  with gzip.GzipFile(filename='',mode='wb',compresslevel=1,mtime=0,fileobj=raw) as compressed:
   with tarfile.open(fileobj=compressed,mode='w') as tar:
    for p in sorted(parse(R/'26923_EXPECTED_FULL_APP.sha256')):
     f=R/p;info=tar.gettarinfo(str(f),arcname=p);info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
     with f.open('rb') as source:tar.addfile(info,source)
 (OUT/'26923_candidate_app_source.tar.gz.sha256').write_text(sha(OUT/'26923_candidate_app_source.tar.gz')+'  26923_candidate_app_source.tar.gz\n')
 print('PASS 26923 real built APK, exact 7-path candidate TAR and compiler/action receipts')
if __name__=='__main__':
 try:
  parser=argparse.ArgumentParser();parser.add_argument('command',choices=['seal','fetch','prepare','regress','verify-compiled','finalize']);mode=parser.parse_args().command
  globals()[mode.replace('-','_')]()
 except Exception as e:print('ERROR',e,file=sys.stderr);sys.exit(1)
