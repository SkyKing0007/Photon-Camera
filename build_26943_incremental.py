#!/usr/bin/env python3
"""26943: exact successful 26942 V2 compiled authority, complete B-only RAW GPU staging + spatial motion protection + RAWR EXIF timings.
Maintain 26942 inherited 141 historical regressions, real GLSL SPIR-V/NDK/Kotlin/Java/assemble.
"""
import argparse,gzip,hashlib,json,os,pathlib,shutil,subprocess,sys,tarfile,urllib.request,zipfile
R=pathlib.Path(__file__).resolve().parent
TMP=R/'.photon_26943_incremental_work';OUT=R/'photon_26943_outputs'
ART=TMP/'26942-success.zip';BASE=TMP/'authority_26942';CAND=TMP/'candidate_26943'
REPO='SkyKing0007/Photon-Camera';BRANCH='experimental-clean-photon-rebuild'
RUN=43772082845;COMMIT='514c3caca5f56b3fe289ec2220be520eb61fa096';ART_ID=14185016520
ART_SHA='08ed272d964bc0f0e3987ddf5315abb74c9dc8cf6a22a8ade108527f9a571040'
TAR_SHA='91ad16f7f4e1b529124c60b09ceacaf6b600cd9ebca0f7ca0224636aaaf98b91'
BUILDER_SHA='602bac28864953f5c819beee5df799132ff0ecdc2b3d1361f3a6295987de6af7'
WORKFLOW_SHA='9a72ae2b1223e83796196f456b2a0fc0ce47f7332610acd024c274f7ccde594b'
PRIOR_APK_SHA='144fc0141dd6705558586056623415f465dcd670d698495b9978cfe05d3060b2'
APKNAME='IrisCamera-0.9726943-26943-iris-rawr-debug.apk'
NBASE=2050;NFILES=2054;NCHANGE=18;NADDED=4;NPROTECTED=2032
REQUIRED={
 'app/src/main/cpp/CMakeLists.txt',
 'app/src/main/cpp/iris26856/amaze/include/amaze/VulkanDeviceOwner.hpp',
 'app/src/main/cpp/iris26856/amaze/src/VulkanDeviceOwner.cpp',
 'app/src/main/cpp/iris26864/Iris26864FrozenDirectRawrRunner.cpp',
 'app/src/main/cpp/iris26864/Iris26864FrozenDirectRawrRunner.hpp',
 'app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc',
 'app/src/main/cpp/iris26864/Iris26864RealRawrCoordinator.cpp',
 'app/src/main/cpp/iris26864/Iris26864RealRawrCoordinator.hpp',
 'app/src/main/cpp/iris26864/Iris26864TwoSlotRaw16Uploader.hpp',
 'app/src/main/cpp/iris26864/Iris26864VendorRawr.cmake',
 'app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqRecorder.cpp',
 'app/src/main/cpp/iris26864/bridge/Iris26888BOffVulkanExecutor.cpp',
 'app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqMismatch.comp',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26864NativeRawr.java',
 'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
 'app/version.properties',
}
ADDED={
 'app/src/main/cpp/iris26864/Iris26943GpuZslRing.cpp',
 'app/src/main/cpp/iris26864/Iris26943GpuZslRing.hpp',
 'app/src/main/cpp/iris26864/Iris26943RawAhbIngress.cpp',
 'app/src/main/cpp/iris26864/bridge/Iris26943BOffHdrqBorder.comp',
}
STAGE1_FILES=['README_PHOTON_26943_V1.md', '26943_LOCAL_VERIFICATION.txt', '26943_COMMIT_MESSAGE.txt', 'build_26943_incremental.py', 'test_26943_source.py', 'test_26943_native_host.py', 'test_26943_shader_contract.py', 'test_26943_java_contract.py', 'compile_26943_shaders.sh', 'test_26943_patch_proof.py', 'test_26943_sealed_negatives.py', 'test_26943_workflow_refs.py', 'prepare_26943_lkr_from_successful_26942.py', '26943_FORWARD_FULLINDEX.patch', '26943_ROLLBACK_FULLINDEX.patch', '26943_BASE_26942_FULL_APP.sha256', '26943_EXPECTED_FULL_APP.sha256', '26943_PROTECTED_SOURCE.sha256', '26943_CHANGED_RUNTIME_ALLOWLIST.txt', '26943_ADDED_RUNTIME_PATHS.txt', '26943_DELETED_RUNTIME_PATHS.txt', '26943_EXPECTED_ACTION_EXECUTABLES.txt', '26943_V1_STAGE_1_UPLOAD_PATHS.txt', '26943_V1_STAGE_2_UPLOAD_PATHS.txt', '26943_V1_STAGE_3_UPLOAD_PATHS.txt']

def fail(msg):raise RuntimeError('26943 BLOCKED: '+str(msg))
def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
 return h.hexdigest()
def parse(path):
 d={}
 for line in path.read_text().splitlines():
  try:h,p=line.split('  ',1)
  except ValueError:fail('malformed manifest line')
  if len(h)!=64 or any(c not in '0123456789abcdef' for c in h) or not p.startswith('app/') or '..' in pathlib.PurePosixPath(p).parts or p in d:fail('malformed/duplicate manifest path '+p)
  d[p]=h
 return d
def scan(root):
 paths=[*(root/'app/src').rglob('*'),root/'app/build.gradle',root/'app/version.properties']
 out={}
 for p in paths:
  if p.is_symlink():fail('symlink in source '+str(p))
  if p.is_file():out[p.relative_to(root).as_posix()]=sha(p)
 return out
def exact(root,man,label):
 want=parse(R/man);got=scan(root)
 if want!=got:
  missing=sorted(want.keys()-got.keys());extra=sorted(got.keys()-want.keys())
  wrong=sorted(p for p in want.keys()&got.keys() if want[p]!=got[p])
  fail(f'{label} source mismatch missing={missing[:4]} added={extra[:4]} changed={wrong[:6]}')
 print('PASS',label,len(got));return got

def scope():
 old=parse(R/'26943_BASE_26942_FULL_APP.sha256');new=parse(R/'26943_EXPECTED_FULL_APP.sha256')
 ch=set((R/'26943_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
 ad=set((R/'26943_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
 dl=set((R/'26943_DELETED_RUNTIME_PATHS.txt').read_text().splitlines())
 if (len(old),len(new),len(ch),len(ad),len(old)-len(ch))!=(NBASE,NFILES,NCHANGE,NADDED,NPROTECTED):fail('incorrect source universe counts')
 if ch!=REQUIRED or ad!=ADDED or dl or set(new)!=set(old)|ad or any(p in old for p in ad) or any(p not in old for p in ch):fail('invalid existing/add/delete source allowlist')
 if {p for p in old if old[p]!=new[p]}!=ch:fail('unapproved changed source or missing overlay')
 if {p:h for p,h in old.items() if p not in ch}!=parse(R/'26943_PROTECTED_SOURCE.sha256'):fail('2032 protected hashes invalid')
 for p in ch|ad:
  if '/vendor/' in p or '/jniLibs/' in p or p.endswith(('.so','.jar','.aar','.spv')):fail('protected source domain '+p)
 if old['app/build.gradle']!=new['app/build.gradle']:fail('Gradle changed')
 return ch|ad,old,new

def seal():
 ch,old,new=scope()
 sealed={}
 for line in (R/'26943_HANDOFF_HASHES.sha256').read_text().splitlines():
  try:h,p=line.split('  ',1)
  except ValueError:fail('malformed handoff hash line')
  if p in sealed or not (R/p).is_file() or sha(R/p)!=h:fail('missing/tampered sealed file '+p)
  sealed[p]=h
 wf='.github/workflows/build-26943-change-aware.yml';trigger='TRIGGER_26943.txt'
 wanted=set(STAGE1_FILES)|{wf,trigger}|{'handoff_payload_26943/'+p for p in ch}
 if set(sealed)!=wanted:fail('sealed file set differs '+str(sorted(wanted^set(sealed))))
 st=[(R/f'26943_V1_STAGE_{i}_UPLOAD_PATHS.txt').read_text().splitlines() for i in (1,2,3)]
 if st[0]!=sorted((wanted|{'26943_HANDOFF_HASHES.sha256'})-{wf,trigger}) or st[1]!=[wf] or st[2]!=[trigger]:fail('three-stage upload sequence differs')
 overlay={p.relative_to(R/'handoff_payload_26943').as_posix() for p in (R/'handoff_payload_26943').rglob('*') if p.is_file()}
 if overlay!=ch:fail('overlay paths unexpectedly changed')
 for p in ch:
  if sha(R/'handoff_payload_26943'/p)!=new[p]:fail('source payload SHA mismatch '+p)
 s=(R/wf).read_text()
 for k in ('verify_26904_v3_safety.py','verify_26904_v2_safety.py','test_26903_v3_archive_receipt.py',
  'build_26942_incremental.py seal','test_26942_sealed_negatives.py',
  'build_26943_incremental.py seal','build_26943_incremental.py fetch',
  'build_26943_incremental.py prepare','test_26943_patch_proof.py --live',
  'prepare_26943_lkr_from_successful_26942.py',
  'compile_26904_shaders_v2.sh','compile_26939_shaders.sh','compile_26941_shaders.sh','compile_26942_shaders.sh','compile_26943_shaders.sh',
  'test_26931_native_integrity.py --native','test_26931_native_integrity.py --cmake',
  'test_26931_native_integrity.py --apk',
  'build_26943_incremental.py verify-compiled','build_26943_incremental.py finalize',
  ':app:assembleDebug --stacktrace','actions/upload-artifact@v4'):
  if k not in s:fail('missing original mandatory Actions verification '+k)
 if s.count('actions/upload-artifact@v4')!=1 or s.count('./gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace')!=1:fail('not exactly one APK build/artifact')
 subprocess.run([sys.executable,'-S','test_26943_workflow_refs.py']+([] if globals().get('PACKAGE_ONLY') else ['--on-actions']),cwd=R,check=True)
 print('PASS seal successful 26942 compiled base 2050 -> 26943 2054, changed 18, protected 2032, source added 4 / deleted 0')

def fetch():
 seal();token=os.getenv('GITHUB_TOKEN','')
 if not token or os.getenv('GITHUB_REPOSITORY')!=REPO or os.getenv('GITHUB_REF_NAME')!=BRANCH:fail('Actions token/branch/repository identity missing')
 def get(endpoint):
  req=urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+endpoint,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'})
  with urllib.request.urlopen(req,timeout=120) as resp:return json.load(resp)
 run=get('actions/runs/'+str(RUN));artifact=get('actions/artifacts/'+str(ART_ID))
 if run.get('id')!=RUN or run.get('conclusion')!='success' or run.get('head_branch')!=BRANCH or run.get('head_sha')!=COMMIT:fail('previous 26942 run not successful')
 if artifact.get('id')!=ART_ID or artifact.get('expired') or artifact.get('digest')!='sha256:'+ART_SHA or artifact.get('workflow_run',{}).get('id') not in (None,RUN):fail('26942 official artifact identity wrong')
 TMP.mkdir(exist_ok=True)
 subprocess.run(['curl','--fail','--location','--retry','3','--silent','--show-error','-H','Authorization: Bearer '+token,'-H','Accept: application/vnd.github+json','https://api.github.com/repos/'+REPO+'/actions/artifacts/'+str(ART_ID)+'/zip','-o',str(ART)],check=True)
 if sha(ART)!=ART_SHA:fail('prior 26942 official artifact archive SHA mismatch')
 print('PASS fetched exact successful 26942 V2 run/artifact SHA')

def safe_tar(tar_path,dst):
 with tarfile.open(tar_path,'r:gz') as t:
  for m in t:
   k=pathlib.PurePosixPath(m.name)
   if not k.parts or k.is_absolute() or k.parts[0]!='app' or '..' in k.parts or not (m.isfile() or m.isdir()) or m.issym() or m.islnk():fail('unsafe authority tar path '+m.name)
  t.extractall(dst,filter='data')

def prepare():
 seal()
 if not ART.is_file() or sha(ART)!=ART_SHA:fail('prior 26942 archive missing')
 for d in (BASE,CAND):
  if d.exists():shutil.rmtree(d)
 BASE.mkdir(parents=True)
 with zipfile.ZipFile(ART) as z:
  if z.testzip():fail('official prior artifact CRC failure')
  def get(n):
   p='photon_26942_outputs/'+n
   if p not in z.namelist():fail('missing 26942 published member '+p)
   return z.read(p)
  raw=get('26942_candidate_app_source.tar.gz')
  if hashlib.sha256(raw).hexdigest()!=TAR_SHA:fail('26942 actual compiled source tar mismatch')
  if get('26942_PREBUILD_SEALED_APP.sha256')!=(R/'26943_BASE_26942_FULL_APP.sha256').read_bytes():fail('26942 prebuild source manifest mismatch')
  if get('26942_EXPECTED_FULL_APP.sha256')!=(R/'26943_BASE_26942_FULL_APP.sha256').read_bytes():fail('26942 official source manifest mismatch')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build_26942_incremental.py')).hexdigest()!=BUILDER_SHA or BUILDER_SHA not in get('26942_ACTUAL_EXECUTED_BUILDER.sha256').decode():fail('26942 builder authority wrong')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build-26942-change-aware.yml')).hexdigest()!=WORKFLOW_SHA or WORKFLOW_SHA not in get('26942_ACTUAL_EXECUTED_WORKFLOW.sha256').decode():fail('26942 workflow authority wrong')
  if PRIOR_APK_SHA not in get('26942_APK.sha256').decode():fail('26942 actual APK SHA wrong')
  ident=get('26942_ACTIONS_IDENTITY.txt').decode()
  if 'git_sha='+COMMIT not in ident or 'github_run_id='+str(RUN) not in ident:fail('26942 runtime identity wrong')
  for flag in ('REAL PINNED GLSL COMPILE: PASS','REAL SPIR-V VALIDATION: PASS','REAL KOTLIN COMPILE: PASS','REAL JAVA COMPILE: PASS','NATIVE/NDK COMPILE: PASS','REAL ANDROID Gradle :app:assembleDebug: PASS','RUNTIME SOURCE INVARIANCE: PASS'):
   if flag not in get('26942_COMPILER_STATUS.txt').decode():fail('26942 full real compiler status missing '+flag)
  for task in (':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL'):
   if 'PASS '+task not in get('26942_REAL_GRADLE_TASKS.txt').decode():fail('26942 real compile task not confirmed '+task)
  for receipt in ('26942_COMPILER_STATUS.txt','26942_REAL_GRADLE_TASKS.txt'):
   if not get(receipt):fail('26942 successful compiler receipt absent '+receipt)
  TMP.mkdir(exist_ok=True)
  (TMP/'26942_candidate_app_source.tar.gz').write_bytes(raw)
 safe_tar(TMP/'26942_candidate_app_source.tar.gz',BASE)
 exact(BASE,'26943_BASE_26942_FULL_APP.sha256','exact actual successful 26942 compiled source')
 shutil.copytree(BASE,CAND)
 for p in sorted(REQUIRED|ADDED):
  src=R/'handoff_payload_26943'/p;dst=CAND/p
  if not src.is_file() or (p in REQUIRED and not dst.is_file()) or (p in ADDED and dst.exists()):fail('missing/duplicate 26943 source overlay '+p)
  dst.parent.mkdir(parents=True,exist_ok=True)
  shutil.copy2(src,dst)
 exact(CAND,'26943_EXPECTED_FULL_APP.sha256','strict 26943 full candidate')
 if not (R/'gradlew').is_file() or not (R/'app/build.gradle').is_file():fail('real Android checkout/SDK project unavailable')
 if (R/'app/src').exists():shutil.rmtree(R/'app/src')
 shutil.copytree(CAND/'app/src',R/'app/src')
 shutil.copy2(CAND/'app/version.properties',R/'app/version.properties')
 shutil.copy2(CAND/'app/build.gradle',R/'app/build.gradle')
 if (R/'app/.cxx').exists():shutil.rmtree(R/'app/.cxx')
 exact(R,'26943_EXPECTED_FULL_APP.sha256','live 26943 compiled candidate source')
 OUT.mkdir(exist_ok=True)
 (OUT/'26943_SOURCE_SCOPE.txt').write_text(f'PRIOR SUCCESS 26942 V2 run={RUN} commit={COMMIT} artifact={ART_ID}\nART_SHA={ART_SHA}\nTAR_SHA={TAR_SHA}\nBUILDER_SHA={BUILDER_SHA}\nWORKFLOW_SHA={WORKFLOW_SHA}\nPRIOR_APK_SHA={PRIOR_APK_SHA}\n2050 -> 2054 source changed=18 protected=2032 added=4 deleted=0; B Photo HDR+ SR OFF zoom<1.10 only; optional camera-time AHB GPU ring, exact 15-frame matching, GPU queue separation, motion-aware reference restoration and RAWR stage EXIF; 26942 B OFF chunk scheduling retained, unmodified 2032 source files protected; SR ON, A, A+B, Night, LONG, DNG, Spektra and pinned vendor unchanged\n'+''.join(x+'\n' for x in sorted(REQUIRED)))
 print('PASS exact 26942 compiled authority reconstructed, candidate-first source, unchanged 2032 protected')

def regress():
 seal();exact(R,'26943_EXPECTED_FULL_APP.sha256','26943 live candidate')
 for t in ('test_26943_source.py','test_26943_native_host.py',
           'test_26943_shader_contract.py','test_26943_java_contract.py',
           'test_26943_patch_proof.py'):
  subprocess.run([sys.executable,'-S',t,'--live'],cwd=R,check=True)
 print('PASS 26943 optional GPU-ZSL exact matched inputs, motion reliable reference, RAWR timing, source/patch invariance')

def verify_compiled():
 regress()
 receipt=OUT/'26943_REAL_GLSL_SPIRV_COMPILER.txt'
 if not receipt.is_file() or '16.5.0' not in receipt.read_text() or 'PASS actual 26943 inline ESSL 300 310' not in receipt.read_text():fail('mandatory current real glslang optimizer compiler receipt absent')
 for p in ('raw_lens_median','lkr_smooth_white','motion_render','motion_gainmap','b_native_final'):
  for x in (('es310.frag',) if p=='b_native_final' else ('es300.frag','es310.frag')):
   f=OUT/('26943_'+p+'_'+x)
   if not f.is_file() or sha(f) not in receipt.read_text():fail('real shader digest not bound to compiled file '+str(f))
 subprocess.run([sys.executable,'-S','test_26931_native_integrity.py','--native'],cwd=R,check=True)
 r=OUT/'26943_INHERITED_LKR_NATIVE_RECEIPT.txt'
 if not r.is_file() or 'SUCCESSFUL 26942 Actions run='+str(RUN) not in r.read_text():fail('wrong RawLens native provenance')
 (OUT/'26943_PREBUILD_SEALED_APP.sha256').write_bytes((R/'26943_EXPECTED_FULL_APP.sha256').read_bytes())
 print('PASS current 26943 inherited ESSL, real glslang 16.5 and SPIR-V compiler, LKR provenance, source sealed')

def finalize():
 regress()
 if (OUT/'26943_PREBUILD_SEALED_APP.sha256').read_bytes()!=(R/'26943_EXPECTED_FULL_APP.sha256').read_bytes():fail('unsealed actual source after compiler')
 log=(OUT/'26943_gradle_assemble.log').read_text(errors='replace')
 tasks=(':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL')
 for t in tasks:
  if t not in log:fail('actual Gradle task absent '+t)
 subprocess.run([sys.executable,'-S','test_26931_native_integrity.py','--cmake'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','verify_26906_native_cache.py','postflight'],cwd=R,check=True)
 apks=list((R/'app/build/outputs/apk').rglob('*.apk'))
 if len(apks)!=1:fail('expected precisely one actual assembled APK, got '+str(len(apks)))
 shutil.copy2(apks[0],R/APKNAME)
 if (R/APKNAME).stat().st_size<1000000:fail('invalid compiled APK')
 subprocess.run([sys.executable,'-S','test_26931_native_integrity.py','--apk'],cwd=R,check=True)
 with zipfile.ZipFile(R/APKNAME) as z:
  if z.testzip() or not {'AndroidManifest.xml','classes.dex'}<=set(z.namelist()):fail('incomplete APK ZIP')
 (OUT/'26943_COMPILER_STATUS.txt').write_text('REAL PINNED GLSL COMPILE: PASS (actual current 26943 inherited authoritative SDR/UHDR GLSL unchanged, genuinely recompiled)\nREAL SPIR-V VALIDATION: PASS\nREAL KOTLIN COMPILE: PASS\nREAL JAVA COMPILE: PASS\nNATIVE/NDK COMPILE: PASS (both ABIs)\nREAL ANDROID Gradle :app:assembleDebug: PASS\nORIGINAL RAWLENS LKR NATIVE: PASS (26942 published APK offline)\nRUNTIME SOURCE INVARIANCE: PASS\nDEVICE IMAGE QUALITY: NOT RUN\n')
 (OUT/'26943_REAL_GRADLE_TASKS.txt').write_text(''.join('PASS '+t+'\n' for t in tasks))
 (OUT/'26943_APK.sha256').write_text(sha(R/APKNAME)+'  '+APKNAME+'\n')
 wf=R/'.github/workflows/build-26943-change-aware.yml'
 (OUT/'26943_ACTUAL_EXECUTED_BUILDER.sha256').write_text(sha(R/'build_26943_incremental.py')+'  build_26943_incremental.py\n')
 (OUT/'26943_ACTUAL_EXECUTED_WORKFLOW.sha256').write_text(sha(wf)+'  .github/workflows/build-26943-change-aware.yml\n')
 (OUT/'26943_ACTIONS_IDENTITY.txt').write_text('git_sha='+os.getenv('GITHUB_SHA','NOT_IN_ACTIONS')+'\ngithub_run_id='+os.getenv('GITHUB_RUN_ID','NOT_IN_ACTIONS')+'\n')
 for p in ('26943_BASE_26942_FULL_APP.sha256','26943_EXPECTED_FULL_APP.sha256','26943_PROTECTED_SOURCE.sha256','26943_CHANGED_RUNTIME_ALLOWLIST.txt','26943_ADDED_RUNTIME_PATHS.txt','26943_DELETED_RUNTIME_PATHS.txt'):
  shutil.copy2(R/p,OUT/p)
 shutil.copy2(R/'build_26943_incremental.py',OUT/'ACTUAL_EXECUTED_build_26943_incremental.py')
 shutil.copy2(wf,OUT/'ACTUAL_EXECUTED_build-26943-change-aware.yml')
 with (OUT/'26943_candidate_app_source.tar.gz').open('wb') as file:
  with gzip.GzipFile(filename='',mode='wb',compresslevel=1,mtime=0,fileobj=file) as g:
   with tarfile.open(fileobj=g,mode='w') as t:
    for p in sorted(parse(R/'26943_EXPECTED_FULL_APP.sha256')):
     src=R/p;meta=t.gettarinfo(str(src),arcname=p)
     meta.uid=meta.gid=0;meta.uname=meta.gname='';meta.mtime=0
     with src.open('rb') as inp:t.addfile(meta,inp)
 (OUT/'26943_candidate_app_source.tar.gz.sha256').write_text(sha(OUT/'26943_candidate_app_source.tar.gz')+'  26943_candidate_app_source.tar.gz\n')
 print('PASS 26943 final actual real compiled APK, 2032 protected SHA invariant, actual tar+apk checksums')

if __name__=='__main__':
 try:
  p=argparse.ArgumentParser();p.add_argument('command',choices=('seal','fetch','prepare','regress','verify-compiled','finalize'));p.add_argument('--package-only',action='store_true');a=p.parse_args()
  globals()['PACKAGE_ONLY']=a.package_only
  globals()[a.command.replace('-','_')]()
 except Exception as error:
  print(str(error),file=sys.stderr);sys.exit(1)
