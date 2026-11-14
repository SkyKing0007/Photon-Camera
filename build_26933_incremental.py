#!/usr/bin/env python3
"""Guarded 26933: latest PUBLISHED successful 26932 compiled source -> B SR ON only.
No prior APK build, no stale repository src, exact one real 26933 Actions assemble.
"""
import argparse,gzip,hashlib,json,os,pathlib,shutil,subprocess,sys,tarfile,urllib.request,zipfile
R=pathlib.Path(__file__).resolve().parent
TMP=R/'.photon_26933_incremental_work';OUT=R/'photon_26933_outputs'
ART=TMP/'26932-success.zip';BASE=TMP/'authority_26932';CAND=TMP/'candidate_26933'
RUN=43637936755; COMMIT='99330ae567d0c8909912bcdbaa4c3654bc439ab1'; ART_ID=14130857688
ART_SHA='8ae25bb66da406d5a6f0d7064a0e4f8da9b30ca710fb5acb75b5f3b1bebc2791'
TAR_SHA='8e1b24cd69273083ca4976cddc258c27988ad55c1cfb76ee06beecfe4a66298a'
BUILDER_SHA='a222dbccfb6c65d039eb670d06330f00aec09020c05f2e13a12d3317362a5c9a'
WORKFLOW_SHA='690c51d89695848b181e945cfd235d778c5ae9b1cd26b6f2297551c5062d3350'
PRIOR_APK_SHA='1ce485deaae3dc1a72b599c7ea6b2e3cae3a205cf27abc2cda9790af38fccd74'
REPO='SkyKing0007/Photon-Camera';BRANCH='experimental-clean-photon-rebuild'
APKNAME='IrisCamera-0.9726933-26933-iris-rawr-debug.apk'
NBASE=2048;NFILES=2048;NCHANGE=2;NADD=0;NPROTECTED=2046
REQUIRED={
 'app/version.properties',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932LkrSmoothWhite.kt',
}
ADDED=set()
STAGE1_FILES=[
 'README_PHOTON_26933_V1.md','build_26933_incremental.py',
 'test_26933_source.py','test_26933_shader_contract.py','test_26933_highlight_math.py',
 'test_26933_patch_proof.py','test_26933_sealed_negatives.py','test_26933_workflow_refs.py',
 'compile_26933_shaders.sh','26933_FORWARD_FULLINDEX.patch','26933_ROLLBACK_FULLINDEX.patch',
 '26933_BASE_26932_FULL_APP.sha256','26933_EXPECTED_FULL_APP.sha256','26933_PROTECTED_SOURCE.sha256',
 '26933_CHANGED_RUNTIME_ALLOWLIST.txt','26933_ADDED_RUNTIME_PATHS.txt',
 '26933_DELETED_RUNTIME_PATHS.txt','26933_EXPECTED_ACTION_EXECUTABLES.txt',
 '26933_V1_STAGE_1_UPLOAD_PATHS.txt','26933_V1_STAGE_2_UPLOAD_PATHS.txt',
 '26933_V1_STAGE_3_UPLOAD_PATHS.txt'
]

def fail(msg):raise RuntimeError('26933 BLOCKED: '+str(msg))
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
 old=parse(R/'26933_BASE_26932_FULL_APP.sha256');new=parse(R/'26933_EXPECTED_FULL_APP.sha256')
 ch=set((R/'26933_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
 ad=set((R/'26933_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
 dl=set((R/'26933_DELETED_RUNTIME_PATHS.txt').read_text().splitlines())
 if (len(old),len(new),len(ch),len(ad),len(old)-len(ch),len(dl))!=(NBASE,NFILES,NCHANGE,NADD,NPROTECTED,0):fail('source counts unexpectedly changed')
 if ch!=REQUIRED or ad!=ADDED or {p for p in old if old[p]!=new.get(p)}!=ch or set(new)-set(old) or set(old)-set(new):fail('unapproved source changes')
 if {p:h for p,h in old.items() if p not in ch}!=parse(R/'26933_PROTECTED_SOURCE.sha256'):fail('protected 26932 source mutated')
 for p in ch|ad:
  if '/vendor/' in p or '/jniLibs/' in p or p.endswith(('.so','.aar','.jar','.comp','.glsl')):fail('native/vendor/other shader modification outside allowlist '+p)
 if old['app/build.gradle']!=new['app/build.gradle']:fail('Gradle changed')
 return ch,ad,old,new

def seal():
 ch,ad,old,new=scope()
 sealed={}
 for l in (R/'26933_HANDOFF_HASHES.sha256').read_text().splitlines():
  h,k=l.split('  ',1)
  if k in sealed or not (R/k).is_file() or sha(R/k)!=h:fail('sealed staged file missing/tampered '+k)
  sealed[k]=h
 wf='.github/workflows/build-26933-change-aware.yml';tr='TRIGGER_26933.txt'
 need=set(STAGE1_FILES)|{wf,tr}|{'handoff_payload_26933/'+p for p in ch|ad}
 if set(sealed)!=need:fail('missing/unlisted handoff paths '+str(sorted(need-set(sealed)))+' extras '+str(sorted(set(sealed)-need)))
 stages=[(R/f'26933_V1_STAGE_{i}_UPLOAD_PATHS.txt').read_text().splitlines() for i in (1,2,3)]
 if stages[0]!=sorted((set(sealed)|{'26933_HANDOFF_HASHES.sha256'})-{wf,tr}) or stages[1]!=[wf] or stages[2]!=[tr]:fail('three-stage upload scope invalid')
 staged={p.relative_to(R/'handoff_payload_26933').as_posix() for p in (R/'handoff_payload_26933').rglob('*') if p.is_file()}
 if staged!=ch|ad:fail('missing/unused overlay files '+str(staged))
 for p in ch|ad:
  if sha(R/'handoff_payload_26933'/p)!=new[p]:fail('overlay source SHA mismatch '+p)
 s=(R/wf).read_text()
 pins=('verify_26904_v3_safety.py','verify_26904_v2_safety.py','test_26903_v3_archive_receipt.py',
   'test_26931_native_integrity.py --apk','build_26932_incremental.py seal',
   'test_26932_shader_contract.py --payload','build_26933_incremental.py fetch',
   'build_26933_incremental.py prepare','compile_26933_shaders.sh',
   'build_26933_incremental.py verify-compiled','build_26933_incremental.py finalize',
   ':app:assembleDebug')
 for p in pins:
  if p not in s:fail('missing inherited gate '+p)
 if s.count('actions/upload-artifact@v4')!=1 or s.count(':app:assembleDebug --stacktrace')!=1 or 'build_26932_incremental.py finalize' in s:fail('duplicate APK build or unsafe old APK recompile')
 subprocess.run([sys.executable,'-S','test_26933_workflow_refs.py']+([] if globals().get('PACKAGE_ONLY') else ['--on-actions']),cwd=R,check=True)
 print('PASS sealed 26932 compiled source '+str(NBASE)+' -> 26933 '+str(NFILES)+' two B ON changes, '+str(NPROTECTED)+' immutable')

def fetch():
 seal()
 token=os.getenv('GITHUB_TOKEN','')
 if not token or os.getenv('GITHUB_REPOSITORY')!=REPO or os.getenv('GITHUB_REF_NAME')!=BRANCH:fail('Actions repository/branch/token validation failed')
 def get(path):
  req=urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+path,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'})
  with urllib.request.urlopen(req,timeout=120) as resp:return json.load(resp)
 run=get('actions/runs/'+str(RUN));artifact=get('actions/artifacts/'+str(ART_ID))
 if run.get('id')!=RUN or run.get('conclusion')!='success' or run.get('head_sha')!=COMMIT or run.get('head_branch')!=BRANCH:fail('prior 26932 run not successful')
 if artifact.get('id')!=ART_ID or artifact.get('expired') or artifact.get('digest')!='sha256:'+ART_SHA or artifact.get('workflow_run',{}).get('id') not in (None,RUN):fail('prior 26932 artifact mismatch')
 TMP.mkdir(exist_ok=True)
 subprocess.run(['curl','--fail','--location','--retry','3','--silent','--show-error','-H','Authorization: Bearer '+token,'-H','Accept: application/vnd.github+json','https://api.github.com/repos/'+REPO+'/actions/artifacts/'+str(ART_ID)+'/zip','-o',str(ART)],check=True)
 if sha(ART)!=ART_SHA:fail('downloaded previous artifact SHA mismatch')
 print('PASS exact successful 26932 Actions artifact '+str(ART_ID)+' SHA verified')

def safe_tar(path,where):
 with tarfile.open(path,'r:gz') as f:
  for m in f:
   k=pathlib.PurePosixPath(m.name)
   if k.is_absolute() or '..' in k.parts or not k.parts or k.parts[0]!='app' or not (m.isfile() or m.isdir()):fail('unsafe compiled source TAR member '+m.name)
  f.extractall(where,filter='data')

def prepare():
 seal()
 if not ART.is_file() or sha(ART)!=ART_SHA:fail('latest SUCCESSFUL 26932 artifact not present')
 for p in (BASE,CAND):
  if p.exists():shutil.rmtree(p)
 BASE.mkdir(parents=True)
 with zipfile.ZipFile(ART) as z:
  def get(n):
   key='photon_26932_outputs/'+n
   if key not in z.namelist():fail('26932 published artifact missing '+n)
   return z.read(key)
  data=get('26932_candidate_app_source.tar.gz')
  if hashlib.sha256(data).hexdigest()!=TAR_SHA:fail('prior successful 26932 compiled source TAR SHA mismatch')
  if get('26932_PREBUILD_SEALED_APP.sha256')!=(R/'26933_BASE_26932_FULL_APP.sha256').read_bytes():fail('prior compiled manifest differs from 26932 authority')
  if get('26932_EXPECTED_FULL_APP.sha256')!=(R/'26933_BASE_26932_FULL_APP.sha256').read_bytes():fail('prior source unexpected')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build_26932_incremental.py')).hexdigest()!=BUILDER_SHA or BUILDER_SHA not in get('26932_ACTUAL_EXECUTED_BUILDER.sha256').decode():fail('26932 executed builder SHA mismatch')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build-26932-change-aware.yml')).hexdigest()!=WORKFLOW_SHA or WORKFLOW_SHA not in get('26932_ACTUAL_EXECUTED_WORKFLOW.sha256').decode():fail('26932 executed workflow SHA mismatch')
  if PRIOR_APK_SHA not in get('26932_APK.sha256').decode():fail('26932 actual APK SHA mismatch')
  ident=get('26932_ACTIONS_IDENTITY.txt').decode()
  if 'git_sha='+COMMIT not in ident or 'github_run_id='+str(RUN) not in ident:fail('26932 compiled artifact identity mismatch')
  for flag in ('REAL PINNED GLSL COMPILE: PASS','REAL SPIR-V VALIDATION: PASS','REAL KOTLIN COMPILE: PASS','REAL JAVA COMPILE: PASS','NATIVE/NDK COMPILE: PASS','REAL ANDROID Gradle :app:assembleDebug: PASS','RUNTIME SOURCE INVARIANCE: PASS'):
   if flag not in get('26932_COMPILER_STATUS.txt').decode():fail('26932 successful compiler receipt missing '+flag)
  for task in (':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL'):
   if 'PASS '+task not in get('26932_REAL_GRADLE_TASKS.txt').decode():fail('26932 actual compiler task failed '+task)
  for receipt in ('26932_REAL_GLSL_SPIRV_COMPILER.txt','26932_GLSLANG_VERSION.txt'):
   if not get(receipt):fail('missing actual pinned shader compiler receipt '+receipt)
  (TMP/'26932_candidate_app_source.tar.gz').write_bytes(data)
 safe_tar(TMP/'26932_candidate_app_source.tar.gz',BASE)
 exact(BASE,'26933_BASE_26932_FULL_APP.sha256','exact actual successful 26932 compiled source')
 shutil.copytree(BASE,CAND)
 ch,ad,_,_=scope()
 for p in sorted(ch|ad):
  src=R/'handoff_payload_26933'/p;dst=CAND/p
  if not src.is_file() or (p in ch and not dst.is_file()) or (p in ad and dst.exists()):fail('changed-file classification invalid '+p)
  dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
 exact(CAND,'26933_EXPECTED_FULL_APP.sha256','actual 26933 complete candidate source')
 if not (R/'gradlew').is_file() or not (R/'app/build.gradle').is_file():fail('Actions real Android checkout unavailable')
 if (R/'app/src').exists():shutil.rmtree(R/'app/src')
 shutil.copytree(CAND/'app/src',R/'app/src')
 shutil.copy2(CAND/'app/version.properties',R/'app/version.properties')
 shutil.copy2(CAND/'app/build.gradle',R/'app/build.gradle')
 if (R/'app/.cxx').exists():shutil.rmtree(R/'app/.cxx')
 exact(R,'26933_EXPECTED_FULL_APP.sha256','live exact 26933 compiled candidate')
 OUT.mkdir(exist_ok=True)
 (OUT/'26933_SOURCE_SCOPE.txt').write_text('FROM SUCCESSFUL 26932 V1 Actions run='+str(RUN)+' commit='+COMMIT+' artifact='+str(ART_ID)+'\nART_SHA='+ART_SHA+'\nTAR_SHA='+TAR_SHA+'\nBUILDER_SHA='+BUILDER_SHA+'\nWORKFLOW_SHA='+WORKFLOW_SHA+'\nPRIOR_APK_SHA='+PRIOR_APK_SHA+'\nsource=2048 changed=2 added=0 protected=2046\nB ON ONLY WB-domain and original physical clipped-white correction; B OFF SDR/UHDR bytes unchanged\n'+'\n'.join(sorted(ch))+'\n')
 print('PASS latest successful 26932 base ONLY, 26933 B/ON shader+version, no previous APK rebuild')

def regress():
 seal();exact(R,'26933_EXPECTED_FULL_APP.sha256','live 26933 source')
 for t in ('test_26933_source.py','test_26933_shader_contract.py','test_26933_highlight_math.py','test_26933_patch_proof.py'):
  subprocess.run([sys.executable,'-S',t,'--live'],cwd=R,check=True)
 print('PASS no B/OFF change, LKR 3x2 pinned unchanged, original clip binary untouched')

def verify_compiled():
 regress()
 rep=OUT/'26933_REAL_GLSL_SPIRV_COMPILER.txt'
 if not rep.is_file():fail('current 26933 real pinned compiler receipt missing')
 log=rep.read_text()
 if '16.5.0' not in log or 'PASS actual 26933 inline ESSL 300 310' not in log:fail('real GLSL/SPIR-V compiler did not pass')
 for name in ('raw_lens_median','lkr_smooth_white','motion_render','motion_gainmap','b_native_final'):
  for suffix in (('es310.frag',) if name=='b_native_final' else ('es300.frag','es310.frag')):
   f=OUT/('26933_'+name+'_'+suffix)
   if not f.is_file() or sha(f) not in log:fail('actual compiled shader source SHA mismatch '+name+' '+suffix)
 subprocess.run([sys.executable,'-S','test_26931_native_integrity.py','--native'],cwd=R,check=True)
 (OUT/'26933_PREBUILD_SEALED_APP.sha256').write_bytes((R/'26933_EXPECTED_FULL_APP.sha256').read_bytes())
 print('PASS real actual 26933 ESSL and SPIR-V compiler receipts, original RawLens both ABI SHA intact')

def finalize():
 regress()
 if (OUT/'26933_PREBUILD_SEALED_APP.sha256').read_bytes()!=(R/'26933_EXPECTED_FULL_APP.sha256').read_bytes():fail('changed source after real compiler')
 log=(OUT/'26933_gradle_assemble.log').read_text(errors='replace')
 tasks=(':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL')
 for k in tasks:
  if k not in log:fail('real Gradle task did not succeed '+k)
 for cmd in (('test_26931_native_integrity.py','--cmake'),('test_26931_native_integrity.py','--apk')):
  # APK integrity check runs after the staged output is copied, below.
  if cmd[1]=='--apk':continue
  subprocess.run([sys.executable,'-S',*cmd],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','verify_26906_native_cache.py','postflight'],cwd=R,check=True)
 apks=list((R/'app/build/outputs/apk').rglob('*.apk'))
 if len(apks)!=1:fail('exactly ONE new 26933 APK required')
 shutil.copy2(apks[0],R/APKNAME)
 if (R/APKNAME).stat().st_size<1_000_000:fail('new APK invalid length')
 subprocess.run([sys.executable,'-S','test_26931_native_integrity.py','--apk'],cwd=R,check=True)
 with zipfile.ZipFile(R/APKNAME) as z:
  if z.testzip():fail('APK contains invalid ZIP entry')
  for k in ('AndroidManifest.xml','classes.dex'):
   if k not in z.namelist():fail('APK missing '+k)
 (OUT/'26933_COMPILER_STATUS.txt').write_text('REAL PINNED GLSL COMPILE: PASS (26933 current live shader)\nREAL SPIR-V VALIDATION: PASS (real optimizer/validator)\nREAL KOTLIN COMPILE: PASS\nREAL JAVA COMPILE: PASS\nNATIVE/NDK COMPILE: PASS (arm64-v8a, armeabi-v7a)\nREAL ANDROID Gradle :app:assembleDebug: PASS\nORIGINAL RAWLENS LKR NATIVE: PASS\nRUNTIME SOURCE INVARIANCE: PASS\nDEVICE IMAGE QUALITY: NOT RUN\n')
 (OUT/'26933_REAL_GRADLE_TASKS.txt').write_text(''.join('PASS '+t+'\n' for t in tasks))
 (OUT/'26933_APK.sha256').write_text(sha(R/APKNAME)+'  '+APKNAME+'\n')
 wf=R/'.github/workflows/build-26933-change-aware.yml'
 (OUT/'26933_ACTUAL_EXECUTED_BUILDER.sha256').write_text(sha(R/'build_26933_incremental.py')+'  build_26933_incremental.py\n')
 (OUT/'26933_ACTUAL_EXECUTED_WORKFLOW.sha256').write_text(sha(wf)+'  .github/workflows/build-26933-change-aware.yml\n')
 (OUT/'26933_ACTIONS_IDENTITY.txt').write_text('git_sha='+os.getenv('GITHUB_SHA','NOT_IN_ACTIONS')+'\ngithub_run_id='+os.getenv('GITHUB_RUN_ID','NOT_IN_ACTIONS')+'\n')
 for p in ('26933_BASE_26932_FULL_APP.sha256','26933_EXPECTED_FULL_APP.sha256','26933_PROTECTED_SOURCE.sha256','26933_CHANGED_RUNTIME_ALLOWLIST.txt','26933_ADDED_RUNTIME_PATHS.txt','26933_DELETED_RUNTIME_PATHS.txt'):
  shutil.copy2(R/p,OUT/p)
 shutil.copy2(R/'build_26933_incremental.py',OUT/'ACTUAL_EXECUTED_build_26933_incremental.py')
 shutil.copy2(wf,OUT/'ACTUAL_EXECUTED_build-26933-change-aware.yml')
 with (OUT/'26933_candidate_app_source.tar.gz').open('wb') as file:
  with gzip.GzipFile(filename='',mode='wb',compresslevel=1,mtime=0,fileobj=file) as g:
   with tarfile.open(fileobj=g,mode='w') as t:
    for p in sorted(parse(R/'26933_EXPECTED_FULL_APP.sha256')):
     src=R/p;meta=t.gettarinfo(str(src),arcname=p)
     meta.uid=meta.gid=0;meta.uname=meta.gname='';meta.mtime=0
     with src.open('rb') as inp:t.addfile(meta,inp)
 (OUT/'26933_candidate_app_source.tar.gz.sha256').write_text(sha(OUT/'26933_candidate_app_source.tar.gz')+'  26933_candidate_app_source.tar.gz\n')
 print('PASS sole 26933 newly assembled APK, dual ABI, B OFF 2046 protected unchanged')

if __name__=='__main__':
 try:
  parser=argparse.ArgumentParser();parser.add_argument('command',choices=('seal','fetch','prepare','regress','verify-compiled','finalize'));parser.add_argument('--package-only',action='store_true');args=parser.parse_args()
  globals()['PACKAGE_ONLY']=args.package_only
  globals()[args.command.replace('-','_')]()
 except Exception as e:
  print(str(e),file=sys.stderr);sys.exit(1)
