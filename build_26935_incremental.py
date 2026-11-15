#!/usr/bin/env python3
"""Guarded 26935: latest PUBLISHED successful 26934 compiled source -> B SR ON only.
No prior APK build, no stale repository src, exact one real 26935 Actions assemble.
"""
import argparse,gzip,hashlib,json,os,pathlib,shutil,subprocess,sys,tarfile,urllib.request,zipfile
R=pathlib.Path(__file__).resolve().parent
TMP=R/'.photon_26935_incremental_work';OUT=R/'photon_26935_outputs'
ART=TMP/'26934-success.zip';BASE=TMP/'authority_26934';CAND=TMP/'candidate_26935'
RUN=43655649685; COMMIT='f206f5f0eb23f8a64e88c82abdbe8df362b99230'; ART_ID=14138156573
ART_SHA='011e7c9f225e142a7a04f589c6548832eb544dfb8e9b722c69b4166768ecee17'
TAR_SHA='fdc9d7d9335ea27ee9858760a7db8225240a49574481e7228b54d27dd671cd13'
BUILDER_SHA='345d34aaa45b23c4e6b0ebc7756387478644c9b098ba4ef3493ab9b344bf2116'
WORKFLOW_SHA='3cb9871bfd2619361e6858758f36035abca2550516a1fbc0c4b39629599494ea'
PRIOR_APK_SHA='8d7348e7e58ee00cee42ef2a32fe3b0cfb0161e2564286f4aba994fc1555f865'
REPO='SkyKing0007/Photon-Camera';BRANCH='experimental-clean-photon-rebuild'
APKNAME='IrisCamera-0.9726935-26935-iris-rawr-debug.apk'
NBASE=2048;NFILES=2050;NCHANGE=6;NADD=2;NPROTECTED=2042
REQUIRED={
 'app/version.properties',
 'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java',
 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java',
 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java',
 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java',
}
ADDED={
 'app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26935BOnSession.java',
 'app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26935BOnProcessingRelay.java',
}
STAGE1_FILES=['README_PHOTON_26935_V1.md', '26935_LOCAL_VERIFICATION.txt', '26935_COMMIT_MESSAGE.txt', 'build_26935_incremental.py', 'test_26935_source.py', 'test_26935_guard_host.py', 'test_26935_patch_proof.py', 'test_26935_sealed_negatives.py', 'test_26935_workflow_refs.py', 'compile_26935_shaders.sh', 'prepare_26935_lkr_from_successful_26934.py', '26935_FORWARD_FULLINDEX.patch', '26935_ROLLBACK_FULLINDEX.patch', '26935_BASE_26934_FULL_APP.sha256', '26935_EXPECTED_FULL_APP.sha256', '26935_PROTECTED_SOURCE.sha256', '26935_CHANGED_RUNTIME_ALLOWLIST.txt', '26935_ADDED_RUNTIME_PATHS.txt', '26935_DELETED_RUNTIME_PATHS.txt', '26935_EXPECTED_ACTION_EXECUTABLES.txt', '26935_V1_STAGE_1_UPLOAD_PATHS.txt', '26935_V1_STAGE_2_UPLOAD_PATHS.txt', '26935_V1_STAGE_3_UPLOAD_PATHS.txt']

def fail(msg):raise RuntimeError('26935 BLOCKED: '+str(msg))
def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
 return h.hexdigest()
def parse(p):
 d={}
 for line in p.read_text().splitlines():
  try:h,key=line.split('  ',1)
  except ValueError:fail('bad manifest line '+line)
  if len(h)!=64 or len(key)<4 or not key.startswith('app/') or '..' in pathlib.PurePosixPath(key).parts or key in d:fail('malformed manifest '+key)
  d[key]=h
 return d
def scan(root):
 out={}
 for p in [*(root/'app/src').rglob('*'),root/'app/build.gradle',root/'app/version.properties']:
  if p.is_symlink():fail('symlink source '+str(p))
  if p.is_file():out[p.relative_to(root).as_posix()]=sha(p)
 return out
def exact(root,man,label):
 expected=parse(R/man);actual=scan(root)
 if actual!=expected:
  missing=sorted(expected.keys()-actual.keys());extra=sorted(actual.keys()-expected.keys())
  mismatch=sorted(p for p in expected.keys()&actual.keys() if expected[p]!=actual[p])
  fail(f'{label} mismatch: missing={missing[:4]} extra={extra[:4]} changed={mismatch[:5]}')
 print('PASS',label,len(actual));return actual

def scope():
 old=parse(R/'26935_BASE_26934_FULL_APP.sha256');new=parse(R/'26935_EXPECTED_FULL_APP.sha256')
 ch=set((R/'26935_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
 ad=set((R/'26935_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
 dl=set((R/'26935_DELETED_RUNTIME_PATHS.txt').read_text().splitlines())
 if (len(old),len(new),len(ch),len(ad),len(old)-len(ch),len(dl))!=(NBASE,NFILES,NCHANGE,NADD,NPROTECTED,0):fail('source counts unexpectedly changed')
 if ch!=REQUIRED or ad!=ADDED or {p for p in old if old[p]!=new.get(p)}!=ch or set(new)-set(old)!=ad or set(old)-set(new):fail('unapproved source changes')
 if {p:h for p,h in old.items() if p not in ch}!=parse(R/'26935_PROTECTED_SOURCE.sha256'):fail('protected 26934 source mutated')
 for p in ch|ad:
  if '/vendor/' in p or '/jniLibs/' in p or p.endswith(('.so','.aar','.jar','.comp','.glsl')):fail('native/vendor/other shader modification outside allowlist '+p)
 if old['app/build.gradle']!=new['app/build.gradle']:fail('Gradle changed')
 return ch,ad,old,new

def seal():
 ch,ad,old,new=scope()
 sealed={}
 for l in (R/'26935_HANDOFF_HASHES.sha256').read_text().splitlines():
  h,k=l.split('  ',1)
  if k in sealed or not (R/k).is_file() or sha(R/k)!=h:fail('sealed staged file missing/tampered '+k)
  sealed[k]=h
 wf='.github/workflows/build-26935-change-aware.yml';tr='TRIGGER_26935.txt'
 need=set(STAGE1_FILES)|{wf,tr}|{'handoff_payload_26935/'+p for p in ch|ad}
 if set(sealed)!=need:fail('missing/unlisted handoff paths '+str(sorted(need-set(sealed)))+' extras '+str(sorted(set(sealed)-need)))
 stages=[(R/f'26935_V1_STAGE_{i}_UPLOAD_PATHS.txt').read_text().splitlines() for i in (1,2,3)]
 if stages[0]!=sorted((set(sealed)|{'26935_HANDOFF_HASHES.sha256'})-{wf,tr}) or stages[1]!=[wf] or stages[2]!=[tr]:fail('three-stage upload scope invalid')
 staged={p.relative_to(R/'handoff_payload_26935').as_posix() for p in (R/'handoff_payload_26935').rglob('*') if p.is_file()}
 if staged!=ch|ad:fail('missing/unused overlay files '+str(staged))
 for p in ch|ad:
  if sha(R/'handoff_payload_26935'/p)!=new[p]:fail('overlay source SHA mismatch '+p)
 s=(R/wf).read_text()
 pins=('verify_26904_v3_safety.py','verify_26904_v2_safety.py',
       'test_26903_v3_archive_receipt.py','test_26931_native_integrity.py --apk',
       'build_26932_incremental.py seal','build_26933_incremental.py seal',
       'build_26934_incremental.py seal','test_26934_shader_contract.py --payload',
       'test_26932_shader_contract.py --payload','test_26933_shader_contract.py --payload',
       'build_26935_incremental.py fetch','build_26935_incremental.py prepare',
       'prepare_26935_lkr_from_successful_26934.py',
       'test_26931_native_integrity.py --native','compile_26935_shaders.sh',
       'test_26935_guard_host.py','test_26935_patch_proof.py',
       'build_26935_incremental.py verify-compiled','build_26935_incremental.py finalize',
       ':app:assembleDebug')
 for p in pins:
  if p not in s:fail('missing inherited gate '+p)
 if s.count('actions/upload-artifact@v4')!=1 or s.count(':app:assembleDebug --stacktrace')!=1 or 'build_26932_incremental.py finalize' in s:fail('duplicate APK build or unsafe old APK recompile')
 subprocess.run([sys.executable,'-S','test_26935_workflow_refs.py']+([] if globals().get('PACKAGE_ONLY') else ['--on-actions']),cwd=R,check=True)
 print('PASS sealed 26934 compiled source '+str(NBASE)+' -> 26935 '+str(NFILES)+' six changed + two added B ON scoped improvements, '+str(NPROTECTED)+' immutable')

def fetch():
 seal()
 token=os.getenv('GITHUB_TOKEN','')
 if not token or os.getenv('GITHUB_REPOSITORY')!=REPO or os.getenv('GITHUB_REF_NAME')!=BRANCH:fail('Actions repository/branch/token validation failed')
 def get(path):
  req=urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+path,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'})
  with urllib.request.urlopen(req,timeout=120) as resp:return json.load(resp)
 run=get('actions/runs/'+str(RUN));artifact=get('actions/artifacts/'+str(ART_ID))
 if run.get('id')!=RUN or run.get('conclusion')!='success' or run.get('head_sha')!=COMMIT or run.get('head_branch')!=BRANCH:fail('prior 26934 run not successful')
 if artifact.get('id')!=ART_ID or artifact.get('expired') or artifact.get('digest')!='sha256:'+ART_SHA or artifact.get('workflow_run',{}).get('id') not in (None,RUN):fail('prior 26934 artifact mismatch')
 TMP.mkdir(exist_ok=True)
 subprocess.run(['curl','--fail','--location','--retry','3','--silent','--show-error','-H','Authorization: Bearer '+token,'-H','Accept: application/vnd.github+json','https://api.github.com/repos/'+REPO+'/actions/artifacts/'+str(ART_ID)+'/zip','-o',str(ART)],check=True)
 if sha(ART)!=ART_SHA:fail('downloaded previous artifact SHA mismatch')
 print('PASS exact successful 26934 Actions artifact '+str(ART_ID)+' SHA verified')

def safe_tar(path,where):
 with tarfile.open(path,'r:gz') as f:
  for m in f:
   k=pathlib.PurePosixPath(m.name)
   if k.is_absolute() or '..' in k.parts or not k.parts or k.parts[0]!='app' or not (m.isfile() or m.isdir()):fail('unsafe compiled source TAR member '+m.name)
  f.extractall(where,filter='data')

def prepare():
 seal()
 if not ART.is_file() or sha(ART)!=ART_SHA:fail('latest SUCCESSFUL 26934 artifact not present')
 for p in (BASE,CAND):
  if p.exists():shutil.rmtree(p)
 BASE.mkdir(parents=True)
 with zipfile.ZipFile(ART) as z:
  def get(n):
   key='photon_26934_outputs/'+n
   if key not in z.namelist():fail('26934 published artifact missing '+n)
   return z.read(key)
  data=get('26934_candidate_app_source.tar.gz')
  if hashlib.sha256(data).hexdigest()!=TAR_SHA:fail('prior successful 26934 compiled source TAR SHA mismatch')
  if get('26934_PREBUILD_SEALED_APP.sha256')!=(R/'26935_BASE_26934_FULL_APP.sha256').read_bytes():fail('prior compiled manifest differs from 26934 authority')
  if get('26934_EXPECTED_FULL_APP.sha256')!=(R/'26935_BASE_26934_FULL_APP.sha256').read_bytes():fail('prior source unexpected')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build_26934_incremental.py')).hexdigest()!=BUILDER_SHA or BUILDER_SHA not in get('26934_ACTUAL_EXECUTED_BUILDER.sha256').decode():fail('26934 executed builder SHA mismatch')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build-26934-change-aware.yml')).hexdigest()!=WORKFLOW_SHA or WORKFLOW_SHA not in get('26934_ACTUAL_EXECUTED_WORKFLOW.sha256').decode():fail('26934 executed workflow SHA mismatch')
  if PRIOR_APK_SHA not in get('26934_APK.sha256').decode():fail('26934 actual APK SHA mismatch')
  ident=get('26934_ACTIONS_IDENTITY.txt').decode()
  if 'git_sha='+COMMIT not in ident or 'github_run_id='+str(RUN) not in ident:fail('26934 compiled artifact identity mismatch')
  for flag in ('REAL PINNED GLSL COMPILE: PASS','REAL SPIR-V VALIDATION: PASS','REAL KOTLIN COMPILE: PASS','REAL JAVA COMPILE: PASS','NATIVE/NDK COMPILE: PASS','REAL ANDROID Gradle :app:assembleDebug: PASS','RUNTIME SOURCE INVARIANCE: PASS'):
   if flag not in get('26934_COMPILER_STATUS.txt').decode():fail('26934 successful compiler receipt missing '+flag)
  for task in (':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL'):
   if 'PASS '+task not in get('26934_REAL_GRADLE_TASKS.txt').decode():fail('26934 actual compiler task failed '+task)
  for receipt in ('26934_REAL_GLSL_SPIRV_COMPILER.txt','26934_GLSLANG_VERSION.txt'):
   if not get(receipt):fail('missing actual pinned shader compiler receipt '+receipt)
  (TMP/'26934_candidate_app_source.tar.gz').write_bytes(data)
 safe_tar(TMP/'26934_candidate_app_source.tar.gz',BASE)
 exact(BASE,'26935_BASE_26934_FULL_APP.sha256','exact actual successful 26934 compiled source')
 shutil.copytree(BASE,CAND)
 ch,ad,_,_=scope()
 for p in sorted(ch|ad):
  src=R/'handoff_payload_26935'/p;dst=CAND/p
  if not src.is_file() or (p in ch and not dst.is_file()) or (p in ad and dst.exists()):fail('changed-file classification invalid '+p)
  dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
 exact(CAND,'26935_EXPECTED_FULL_APP.sha256','actual 26935 complete candidate source')
 if not (R/'gradlew').is_file() or not (R/'app/build.gradle').is_file():fail('Actions real Android checkout unavailable')
 if (R/'app/src').exists():shutil.rmtree(R/'app/src')
 shutil.copytree(CAND/'app/src',R/'app/src')
 shutil.copy2(CAND/'app/version.properties',R/'app/version.properties')
 shutil.copy2(CAND/'app/build.gradle',R/'app/build.gradle')
 if (R/'app/.cxx').exists():shutil.rmtree(R/'app/.cxx')
 exact(R,'26935_EXPECTED_FULL_APP.sha256','live exact 26935 compiled candidate')
 OUT.mkdir(exist_ok=True)
 (OUT/'26935_SOURCE_SCOPE.txt').write_text('FROM SUCCESSFUL 26934 V1 R2 Actions run='+str(RUN)+' commit='+COMMIT+' artifact='+str(ART_ID)+'\nART_SHA='+ART_SHA+'\nTAR_SHA='+TAR_SHA+'\nBUILDER_SHA='+BUILDER_SHA+'\nWORKFLOW_SHA='+WORKFLOW_SHA+'\nPRIOR_APK_SHA='+PRIOR_APK_SHA+'\nsource=2050 changed=6 added=2 protected=2042\nB ON ONLY 15-RAW JPEG gated shutter + measured preview readback budget; preserved 26934 white highlights / B OFF SDR-UHDR / original LKR3x2 unchanged\n'+'\n'.join(sorted(ch))+'\n')
 print('PASS latest successful 26934 base ONLY, 26935 B/ON guarded preview lifecycle/shutter+version, protected 26934 visual-white, no previous APK rebuild')

def regress():
 seal();exact(R,'26935_EXPECTED_FULL_APP.sha256','live 26935 source')
 for t in ('test_26935_source.py','test_26935_guard_host.py','test_26935_patch_proof.py'):
  subprocess.run([sys.executable,'-S',t,'--live'],cwd=R,check=True)
 print('PASS no B/OFF change, LKR 3x2 pinned unchanged, original clip binary untouched')

def verify_inherited_native_receipt():
 rec=OUT/'26935_INHERITED_LKR_NATIVE_RECEIPT.txt'
 if not rec.is_file():fail('missing original RawLens LKR reuse receipt from authenticated 26934 published APK')
 r=rec.read_text()
 for phrase in ('origin=SUCCESSFUL 26934 Actions run='+str(RUN),
                '26934 artifact sha256='+ART_SHA,
                '26934 prior APK sha256='+PRIOR_APK_SHA,
                'external GitHub release API/download=NOT USED',
                'previous APK rebuild=NOT USED'):
  if phrase not in r:fail('invalid 26934 inherited native provenance receipt '+phrase)
 for abi,lib,hashvalue in (("arm64-v8a","liblkrpipeline.so","af1d4caff00b3b189d23d1d53c7c9d11256f5b050af2590c5407191ce32cd39b"),
                           ("arm64-v8a","libsrpipeline.so","a91e0a33226db0e08b5355e2fac189cc9b91af7106530f6577d5084f1f39865d"),
                           ("armeabi-v7a","liblkrpipeline.so","46de04ea3b1d37fbcc9bb380f94d56e7d7ad74d110e990e8413589e4e7eb8450"),
                           ("armeabi-v7a","libsrpipeline.so","61fdaab8881684999c03bf6d9a3cbe1d9b3da63effe0f364eaca103f97efe78c")):
  if 'PASS original RawLens 2.2.86 lib/'+abi+'/'+lib+' sha256='+hashvalue not in r:
   fail('missing inherited native binary SHA receipt '+abi+'/'+lib)
  p=R/'app/build/verified_rawlens26931/jniLibs'/abi/lib
  if not p.is_file() or sha(p)!=hashvalue:fail('original LKR ABI library missing/modified '+abi+'/'+lib)
 print('PASS rawLens 2.2.86 verified binaries from successful 26934 APK, both ABIs, offline')

def verify_compiled():
 regress()
 rep=OUT/'26935_REAL_GLSL_SPIRV_COMPILER.txt'
 if not rep.is_file():fail('current 26935 real pinned compiler receipt missing')
 log=rep.read_text()
 if '16.5.0' not in log or 'PASS actual 26935 inline ESSL 300 310' not in log:fail('real GLSL/SPIR-V compiler did not pass')
 for name in ('raw_lens_median','lkr_smooth_white','motion_render','motion_gainmap','b_native_final'):
  for suffix in (('es310.frag',) if name=='b_native_final' else ('es300.frag','es310.frag')):
   f=R/'photon_26934_outputs'/('26934_'+name+'_'+suffix)
   if not f.is_file() or sha(f) not in log:fail('actual compiled shader source SHA mismatch '+name+' '+suffix)
 verify_inherited_native_receipt()
 subprocess.run([sys.executable,'-S','test_26931_native_integrity.py','--native'],cwd=R,check=True)
 (OUT/'26935_PREBUILD_SEALED_APP.sha256').write_bytes((R/'26935_EXPECTED_FULL_APP.sha256').read_bytes())
 print('PASS real actual 26935 ESSL and SPIR-V compiler receipts, original RawLens both ABI SHA intact')

def finalize():
 regress()
 if (OUT/'26935_PREBUILD_SEALED_APP.sha256').read_bytes()!=(R/'26935_EXPECTED_FULL_APP.sha256').read_bytes():fail('changed source after real compiler')
 log=(OUT/'26935_gradle_assemble.log').read_text(errors='replace')
 tasks=(':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL')
 for k in tasks:
  if k not in log:fail('real Gradle task did not succeed '+k)
 for cmd in (('test_26931_native_integrity.py','--cmake'),('test_26931_native_integrity.py','--apk')):
  # APK integrity check runs after the staged output is copied, below.
  if cmd[1]=='--apk':continue
  subprocess.run([sys.executable,'-S',*cmd],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','verify_26906_native_cache.py','postflight'],cwd=R,check=True)
 apks=list((R/'app/build/outputs/apk').rglob('*.apk'))
 if len(apks)!=1:fail('exactly ONE new 26935 APK required')
 shutil.copy2(apks[0],R/APKNAME)
 if (R/APKNAME).stat().st_size<1_000_000:fail('new APK invalid length')
 subprocess.run([sys.executable,'-S','test_26931_native_integrity.py','--apk'],cwd=R,check=True)
 with zipfile.ZipFile(R/APKNAME) as z:
  if z.testzip():fail('APK contains invalid ZIP entry')
  for k in ('AndroidManifest.xml','classes.dex'):
   if k not in z.namelist():fail('APK missing '+k)
 verify_inherited_native_receipt()
 (OUT/'26935_COMPILER_STATUS.txt').write_text('REAL PINNED GLSL COMPILE: PASS (26935 current live shader)\nREAL SPIR-V VALIDATION: PASS (real optimizer/validator)\nREAL KOTLIN COMPILE: PASS\nREAL JAVA COMPILE: PASS\nNATIVE/NDK COMPILE: PASS (arm64-v8a, armeabi-v7a)\nREAL ANDROID Gradle :app:assembleDebug: PASS\nORIGINAL RAWLENS LKR NATIVE: PASS (26934 published APK offline reuse)\nRUNTIME SOURCE INVARIANCE: PASS\nDEVICE IMAGE QUALITY: NOT RUN\n')
 (OUT/'26935_REAL_GRADLE_TASKS.txt').write_text(''.join('PASS '+t+'\n' for t in tasks))
 (OUT/'26935_APK.sha256').write_text(sha(R/APKNAME)+'  '+APKNAME+'\n')
 wf=R/'.github/workflows/build-26935-change-aware.yml'
 (OUT/'26935_ACTUAL_EXECUTED_BUILDER.sha256').write_text(sha(R/'build_26935_incremental.py')+'  build_26935_incremental.py\n')
 (OUT/'26935_ACTUAL_EXECUTED_WORKFLOW.sha256').write_text(sha(wf)+'  .github/workflows/build-26935-change-aware.yml\n')
 (OUT/'26935_ACTIONS_IDENTITY.txt').write_text('git_sha='+os.getenv('GITHUB_SHA','NOT_IN_ACTIONS')+'\ngithub_run_id='+os.getenv('GITHUB_RUN_ID','NOT_IN_ACTIONS')+'\n')
 for p in ('26935_BASE_26934_FULL_APP.sha256','26935_EXPECTED_FULL_APP.sha256','26935_PROTECTED_SOURCE.sha256','26935_CHANGED_RUNTIME_ALLOWLIST.txt','26935_ADDED_RUNTIME_PATHS.txt','26935_DELETED_RUNTIME_PATHS.txt'):
  shutil.copy2(R/p,OUT/p)
 shutil.copy2(R/'build_26935_incremental.py',OUT/'ACTUAL_EXECUTED_build_26935_incremental.py')
 shutil.copy2(wf,OUT/'ACTUAL_EXECUTED_build-26935-change-aware.yml')
 with (OUT/'26935_candidate_app_source.tar.gz').open('wb') as file:
  with gzip.GzipFile(filename='',mode='wb',compresslevel=1,mtime=0,fileobj=file) as g:
   with tarfile.open(fileobj=g,mode='w') as t:
    for p in sorted(parse(R/'26935_EXPECTED_FULL_APP.sha256')):
     src=R/p;meta=t.gettarinfo(str(src),arcname=p)
     meta.uid=meta.gid=0;meta.uname=meta.gname='';meta.mtime=0
     with src.open('rb') as inp:t.addfile(meta,inp)
 (OUT/'26935_candidate_app_source.tar.gz.sha256').write_text(sha(OUT/'26935_candidate_app_source.tar.gz')+'  26935_candidate_app_source.tar.gz\n')
 print('PASS sole 26935 newly assembled APK, dual ABI, B OFF 2042 protected unchanged')

if __name__=='__main__':
 try:
  parser=argparse.ArgumentParser();parser.add_argument('command',choices=('seal','fetch','prepare','regress','verify-compiled','finalize'));parser.add_argument('--package-only',action='store_true');args=parser.parse_args()
  globals()['PACKAGE_ONLY']=args.package_only
  globals()[args.command.replace('-','_')]()
 except Exception as e:
  print(str(e),file=sys.stderr);sys.exit(1)
