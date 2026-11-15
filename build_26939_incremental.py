"""Guarded Photon 26939: successful compiled 26938 authority; single B-ON early RawLens camera-linear white-window owner.
No old APK rebuild, no stale repository source, mandatory 141 historical commands and real Android compile.
"""
import argparse,gzip,hashlib,json,os,pathlib,shutil,subprocess,sys,tarfile,urllib.request,zipfile
R=pathlib.Path(__file__).resolve().parent
TMP=R/'.photon_26939_incremental_work';OUT=R/'photon_26939_outputs'
ART=TMP/'26938-success.zip';BASE=TMP/'authority_26938';CAND=TMP/'candidate_26939'
RUN=43683940732; COMMIT='0b6dc919f2e46c43599dbd8e0b542f3b98fc3230'; ART_ID=14149827963
ART_SHA='dbcd7943c5722674a1fb862f780091b17ae19962c8e591ac2f9010572293a3f0'
TAR_SHA='bbf3256b140d7f60190ebc20676207eb28692c8a14a350879bd51e0ebc3be770'
BUILDER_SHA='99703e2cf8c09df228492dfea958752f3d2e4eff41afc85e2bbd390343fdea53'
WORKFLOW_SHA='f0ba61a30528910756f0a2a490808e120acc53e9030762e3fca26b54e49f74b2'
PRIOR_APK_SHA='f11c05f0403a25c36b4b52c2e951018f1036ee652b008a08efe1995885976195'
REPO='SkyKing0007/Photon-Camera';BRANCH='experimental-clean-photon-rebuild'
APKNAME='IrisCamera-0.9726939-26939-iris-rawr-debug.apk'
NBASE=2050;NFILES=2050;NCHANGE=2;NADD=0;NPROTECTED=2048
REQUIRED={
 'app/version.properties',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932RawLensMedian.kt',
}
ADDED=set() # previously compiled shutter, preview, original native libraries are PROTECTED
STAGE1_FILES=[
 'README_PHOTON_26939_V1.md','26939_LOCAL_VERIFICATION.txt','26939_COMMIT_MESSAGE.txt',
 'build_26939_incremental.py','test_26939_source.py','test_26939_guard_host.py',
 'test_26939_highlight_math.py','test_26939_shader_contract.py',
 'test_26939_patch_proof.py','test_26939_sealed_negatives.py','test_26939_workflow_refs.py',
 'compile_26939_shaders.sh','prepare_26939_lkr_from_successful_26938.py',
 '26939_FORWARD_FULLINDEX.patch','26939_ROLLBACK_FULLINDEX.patch',
 '26939_BASE_26938_FULL_APP.sha256','26939_EXPECTED_FULL_APP.sha256',
 '26939_PROTECTED_SOURCE.sha256','26939_CHANGED_RUNTIME_ALLOWLIST.txt',
 '26939_ADDED_RUNTIME_PATHS.txt','26939_DELETED_RUNTIME_PATHS.txt',
 '26939_EXPECTED_ACTION_EXECUTABLES.txt',
 '26939_V1_STAGE_1_UPLOAD_PATHS.txt','26939_V1_STAGE_2_UPLOAD_PATHS.txt',
 '26939_V1_STAGE_3_UPLOAD_PATHS.txt',
]

def fail(msg):raise RuntimeError('26939 BLOCKED: '+str(msg))
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
  if len(h)!=64 or any(c not in '0123456789abcdef' for c in h) or len(key)<4 or not key.startswith('app/') or '..' in pathlib.PurePosixPath(key).parts or key in d:fail('malformed manifest '+key)
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
 old=parse(R/'26939_BASE_26938_FULL_APP.sha256');new=parse(R/'26939_EXPECTED_FULL_APP.sha256')
 ch=set((R/'26939_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
 ad=set((R/'26939_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
 dl=set((R/'26939_DELETED_RUNTIME_PATHS.txt').read_text().splitlines())
 if (len(old),len(new),len(ch),len(ad),len(old)-len(ch),len(dl))!=(NBASE,NFILES,NCHANGE,NADD,NPROTECTED,0):fail('source counts unexpectedly changed')
 if ch!=REQUIRED or ad!=ADDED or {p for p in old if old[p]!=new.get(p)}!=ch or set(new)-set(old)!=ad or set(old)-set(new):fail('unapproved source changes')
 if {p:h for p,h in old.items() if p not in ch}!=parse(R/'26939_PROTECTED_SOURCE.sha256'):fail('protected 26938 source mutated')
 for p in ch|ad:
  if '/vendor/' in p or '/jniLibs/' in p or p.endswith(('.so','.aar','.jar','.comp','.glsl')):fail('native/vendor/other shader modification outside allowlist '+p)
 if old['app/build.gradle']!=new['app/build.gradle']:fail('Gradle changed')
 return ch,ad,old,new

def seal():
 ch,ad,old,new=scope()
 sealed={}
 for l in (R/'26939_HANDOFF_HASHES.sha256').read_text().splitlines():
  h,k=l.split('  ',1)
  if k in sealed or not (R/k).is_file() or sha(R/k)!=h:fail('sealed staged file missing/tampered '+k)
  sealed[k]=h
 wf='.github/workflows/build-26939-change-aware.yml';tr='TRIGGER_26939.txt'
 need=set(STAGE1_FILES)|{wf,tr}|{'handoff_payload_26939/'+p for p in ch|ad}
 if set(sealed)!=need:fail('missing/unlisted handoff paths '+str(sorted(need-set(sealed)))+' extras '+str(sorted(set(sealed)-need)))
 stages=[(R/f'26939_V1_STAGE_{i}_UPLOAD_PATHS.txt').read_text().splitlines() for i in (1,2,3)]
 if stages[0]!=sorted((set(sealed)|{'26939_HANDOFF_HASHES.sha256'})-{wf,tr}) or stages[1]!=[wf] or stages[2]!=[tr]:fail('three-stage upload scope invalid')
 staged={p.relative_to(R/'handoff_payload_26939').as_posix() for p in (R/'handoff_payload_26939').rglob('*') if p.is_file()}
 if staged!=ch|ad:fail('missing/unused overlay files '+str(staged))
 for p in ch|ad:
  if sha(R/'handoff_payload_26939'/p)!=new[p]:fail('overlay source SHA mismatch '+p)
 s=(R/wf).read_text()
 pins=(
  'verify_26904_v3_safety.py','verify_26904_v2_safety.py',
  'test_26903_v3_archive_receipt.py','build_26936_incremental.py seal','build_26938_incremental.py seal',
  'test_26938_guard_host.py','build_26939_incremental.py seal',
  'test_26939_shader_contract.py --payload','test_26939_shader_contract.py --live',
  'test_26939_highlight_math.py','test_26939_guard_host.py',
  'test_26939_patch_proof.py',
  'build_26939_incremental.py fetch','build_26939_incremental.py prepare',
  'prepare_26939_lkr_from_successful_26938.py',
  'test_26931_native_integrity.py --native','compile_26939_shaders.sh',
  'build_26939_incremental.py verify-compiled','build_26939_incremental.py finalize',
  'test_26931_native_integrity.py --cmake','test_26931_native_integrity.py --apk',
  ':app:assembleDebug')
 for p in pins:
  if p not in s:fail('missing inherited gate '+p)
 if s.count('actions/upload-artifact@v4')!=1 or s.count(':app:assembleDebug --stacktrace')!=1 or 'build_26932_incremental.py finalize' in s:fail('duplicate APK build or unsafe old APK recompile')
 subprocess.run([sys.executable,'-S','test_26939_workflow_refs.py']+([] if globals().get('PACKAGE_ONLY') else ['--on-actions']),cwd=R,check=True)
 print('PASS sealed exact successful 26938 compiled source '+str(NBASE)+' -> 26939 '+str(NFILES)+' two changed, no added, '+str(NPROTECTED)+' immutable')

def fetch():
 seal()
 token=os.getenv('GITHUB_TOKEN','')
 if not token or os.getenv('GITHUB_REPOSITORY')!=REPO or os.getenv('GITHUB_REF_NAME')!=BRANCH:fail('Actions repository/branch/token validation failed')
 def get(path):
  req=urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+path,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'})
  with urllib.request.urlopen(req,timeout=120) as resp:return json.load(resp)
 run=get('actions/runs/'+str(RUN));artifact=get('actions/artifacts/'+str(ART_ID))
 if run.get('id')!=RUN or run.get('conclusion')!='success' or run.get('head_sha')!=COMMIT or run.get('head_branch')!=BRANCH:fail('prior 26938 run not successful')
 if artifact.get('id')!=ART_ID or artifact.get('expired') or artifact.get('digest')!='sha256:'+ART_SHA or artifact.get('workflow_run',{}).get('id') not in (None,RUN):fail('prior 26938 artifact mismatch')
 TMP.mkdir(exist_ok=True)
 subprocess.run(['curl','--fail','--location','--retry','3','--silent','--show-error','-H','Authorization: Bearer '+token,'-H','Accept: application/vnd.github+json','https://api.github.com/repos/'+REPO+'/actions/artifacts/'+str(ART_ID)+'/zip','-o',str(ART)],check=True)
 if sha(ART)!=ART_SHA:fail('downloaded previous artifact SHA mismatch')
 print('PASS exact successful 26938 Actions artifact '+str(ART_ID)+' SHA verified')

def safe_tar(path,where):
 with tarfile.open(path,'r:gz') as f:
  for m in f:
   k=pathlib.PurePosixPath(m.name)
   if k.is_absolute() or '..' in k.parts or not k.parts or k.parts[0]!='app' or not (m.isfile() or m.isdir()):fail('unsafe compiled source TAR member '+m.name)
  f.extractall(where,filter='data')

def prepare():
 seal()
 if not ART.is_file() or sha(ART)!=ART_SHA:fail('latest SUCCESSFUL 26938 artifact not present')
 for p in (BASE,CAND):
  if p.exists():shutil.rmtree(p)
 BASE.mkdir(parents=True)
 with zipfile.ZipFile(ART) as z:
  def get(n):
   key='photon_26938_outputs/'+n
   if key not in z.namelist():fail('26938 published artifact missing '+n)
   return z.read(key)
  data=get('26938_candidate_app_source.tar.gz')
  if hashlib.sha256(data).hexdigest()!=TAR_SHA:fail('prior successful 26938 compiled source TAR SHA mismatch')
  if get('26938_PREBUILD_SEALED_APP.sha256')!=(R/'26939_BASE_26938_FULL_APP.sha256').read_bytes():fail('prior compiled manifest differs from 26938 authority')
  if get('26938_EXPECTED_FULL_APP.sha256')!=(R/'26939_BASE_26938_FULL_APP.sha256').read_bytes():fail('prior source unexpected')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build_26938_incremental.py')).hexdigest()!=BUILDER_SHA or BUILDER_SHA not in get('26938_ACTUAL_EXECUTED_BUILDER.sha256').decode():fail('26938 executed builder SHA mismatch')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build-26938-change-aware.yml')).hexdigest()!=WORKFLOW_SHA or WORKFLOW_SHA not in get('26938_ACTUAL_EXECUTED_WORKFLOW.sha256').decode():fail('26938 executed workflow SHA mismatch')
  if PRIOR_APK_SHA not in get('26938_APK.sha256').decode():fail('26938 actual APK SHA mismatch')
  ident=get('26938_ACTIONS_IDENTITY.txt').decode()
  if 'git_sha='+COMMIT not in ident or 'github_run_id='+str(RUN) not in ident:fail('26938 compiled artifact identity mismatch')
  for flag in ('REAL PINNED GLSL COMPILE: PASS','REAL SPIR-V VALIDATION: PASS','REAL KOTLIN COMPILE: PASS','REAL JAVA COMPILE: PASS','NATIVE/NDK COMPILE: PASS','REAL ANDROID Gradle :app:assembleDebug: PASS','RUNTIME SOURCE INVARIANCE: PASS'):
   if flag not in get('26938_COMPILER_STATUS.txt').decode():fail('26938 successful compiler receipt missing '+flag)
  for task in (':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL'):
   if 'PASS '+task not in get('26938_REAL_GRADLE_TASKS.txt').decode():fail('26938 actual compiler task failed '+task)
  for receipt in ('26938_REAL_GLSL_SPIRV_COMPILER.txt','26938_GLSLANG_VERSION.txt'):
   if not get(receipt):fail('missing actual pinned shader compiler receipt '+receipt)
  (TMP/'26938_candidate_app_source.tar.gz').write_bytes(data)
 safe_tar(TMP/'26938_candidate_app_source.tar.gz',BASE)
 exact(BASE,'26939_BASE_26938_FULL_APP.sha256','exact actual successful 26938 compiled source')
 shutil.copytree(BASE,CAND)
 ch,ad,_,_=scope()
 for p in sorted(ch|ad):
  src=R/'handoff_payload_26939'/p;dst=CAND/p
  if not src.is_file() or (p in ch and not dst.is_file()) or (p in ad and dst.exists()):fail('changed-file classification invalid '+p)
  dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
 exact(CAND,'26939_EXPECTED_FULL_APP.sha256','actual 26939 complete candidate source')
 if not (R/'gradlew').is_file() or not (R/'app/build.gradle').is_file():fail('Actions real Android checkout unavailable')
 if (R/'app/src').exists():shutil.rmtree(R/'app/src')
 shutil.copytree(CAND/'app/src',R/'app/src')
 shutil.copy2(CAND/'app/version.properties',R/'app/version.properties')
 shutil.copy2(CAND/'app/build.gradle',R/'app/build.gradle')
 if (R/'app/.cxx').exists():shutil.rmtree(R/'app/.cxx')
 exact(R,'26939_EXPECTED_FULL_APP.sha256','live exact 26939 compiled candidate')
 OUT.mkdir(exist_ok=True)
 (OUT/'26939_SOURCE_SCOPE.txt').write_text(
  'FROM SUCCESSFUL 26938 V2 Actions run='+str(RUN)+' commit='+COMMIT+' artifact='+str(ART_ID)+
  '\nART_SHA='+ART_SHA+'\nTAR_SHA='+TAR_SHA+'\nBUILDER_SHA='+BUILDER_SHA+
  '\nWORKFLOW_SHA='+WORKFLOW_SHA+'\nPRIOR_APK_SHA='+PRIOR_APK_SHA+
  '\nsource=2050 changed=2 added=0 protected=2048\n'+
  'B ON exact RawLens 0.70..0.99 smooth white window without physical mask veto, targeting normalized shutter WB camera white inside original 19-exchange median; protected original LKR and 26938 preview/shutter/B OFF saturation.\n'+
  '\n'.join(sorted(ch))+'\n')
 print('PASS latest successful 26938 base ONLY, 26939 early RawLens camera-native white shoulder, protect 26938 QoS/B OFF saturation/shutter; no prior APK rebuild')

def regress():
 seal();exact(R,'26939_EXPECTED_FULL_APP.sha256','live 26939 source')
 for t in ('test_26939_source.py','test_26939_guard_host.py',
           'test_26939_highlight_math.py','test_26939_shader_contract.py',
           'test_26939_patch_proof.py'):
  subprocess.run([sys.executable,'-S',t,'--live'],cwd=R,check=True)
 print('PASS protected shutter, 15 RAW LKR T3 z2, original binary clip and native ABIs untouched')

def verify_inherited_native_receipt():
 rec=OUT/'26939_INHERITED_LKR_NATIVE_RECEIPT.txt'
 if not rec.is_file():fail('missing original RawLens LKR reuse receipt from authenticated 26938 published APK')
 r=rec.read_text()
 for phrase in ('origin=SUCCESSFUL 26938 Actions run='+str(RUN),
                '26938 artifact sha256='+ART_SHA,
                '26938 prior APK sha256='+PRIOR_APK_SHA,
                'external GitHub release API/download=NOT USED',
                'previous APK rebuild=NOT USED'):
  if phrase not in r:fail('invalid 26938 inherited native provenance receipt '+phrase)
 for abi,lib,hashvalue in (("arm64-v8a","liblkrpipeline.so","af1d4caff00b3b189d23d1d53c7c9d11256f5b050af2590c5407191ce32cd39b"),
                           ("arm64-v8a","libsrpipeline.so","a91e0a33226db0e08b5355e2fac189cc9b91af7106530f6577d5084f1f39865d"),
                           ("armeabi-v7a","liblkrpipeline.so","46de04ea3b1d37fbcc9bb380f94d56e7d7ad74d110e990e8413589e4e7eb8450"),
                           ("armeabi-v7a","libsrpipeline.so","61fdaab8881684999c03bf6d9a3cbe1d9b3da63effe0f364eaca103f97efe78c")):
  if 'PASS original RawLens 2.2.86 lib/'+abi+'/'+lib+' sha256='+hashvalue not in r:
   fail('missing inherited native binary SHA receipt '+abi+'/'+lib)
  p=R/'app/build/verified_rawlens26931/jniLibs'/abi/lib
  if not p.is_file() or sha(p)!=hashvalue:fail('original LKR ABI library missing/modified '+abi+'/'+lib)
 print('PASS rawLens 2.2.86 verified binaries from successful 26938 APK, both ABIs, offline')

def verify_compiled():
 regress()
 rep=OUT/'26939_REAL_GLSL_SPIRV_COMPILER.txt'
 if not rep.is_file():fail('current 26939 real pinned compiler receipt missing')
 log=rep.read_text()
 if '16.5.0' not in log or 'PASS actual 26939 inline ESSL 300 310' not in log:fail('real GLSL/SPIR-V compiler did not pass')
 for name in ('raw_lens_median','lkr_smooth_white','motion_render','motion_gainmap','b_native_final'):
  for suffix in (('es310.frag',) if name=='b_native_final' else ('es300.frag','es310.frag')):
   f=R/'photon_26939_outputs'/('26939_'+name+'_'+suffix)
   if not f.is_file() or sha(f) not in log:fail('actual compiled shader source SHA mismatch '+name+' '+suffix)
 verify_inherited_native_receipt()
 subprocess.run([sys.executable,'-S','test_26931_native_integrity.py','--native'],cwd=R,check=True)
 (OUT/'26939_PREBUILD_SEALED_APP.sha256').write_bytes((R/'26939_EXPECTED_FULL_APP.sha256').read_bytes())
 print('PASS real actual 26939 ESSL and SPIR-V compiler receipts, original RawLens both ABI SHA intact')

def finalize():
 regress()
 if (OUT/'26939_PREBUILD_SEALED_APP.sha256').read_bytes()!=(R/'26939_EXPECTED_FULL_APP.sha256').read_bytes():fail('changed source after real compiler')
 log=(OUT/'26939_gradle_assemble.log').read_text(errors='replace')
 tasks=(':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL')
 for k in tasks:
  if k not in log:fail('real Gradle task did not succeed '+k)
 for cmd in (('test_26931_native_integrity.py','--cmake'),('test_26931_native_integrity.py','--apk')):
  # APK integrity check runs after the staged output is copied, below.
  if cmd[1]=='--apk':continue
  subprocess.run([sys.executable,'-S',*cmd],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','verify_26906_native_cache.py','postflight'],cwd=R,check=True)
 apks=list((R/'app/build/outputs/apk').rglob('*.apk'))
 if len(apks)!=1:fail('exactly ONE new 26939 APK required')
 shutil.copy2(apks[0],R/APKNAME)
 if (R/APKNAME).stat().st_size<1_000_000:fail('new APK invalid length')
 subprocess.run([sys.executable,'-S','test_26931_native_integrity.py','--apk'],cwd=R,check=True)
 with zipfile.ZipFile(R/APKNAME) as z:
  if z.testzip():fail('APK contains invalid ZIP entry')
  for k in ('AndroidManifest.xml','classes.dex'):
   if k not in z.namelist():fail('APK missing '+k)
 verify_inherited_native_receipt()
 (OUT/'26939_COMPILER_STATUS.txt').write_text('REAL PINNED GLSL COMPILE: PASS (26939 current live shader)\nREAL SPIR-V VALIDATION: PASS (real optimizer/validator)\nREAL KOTLIN COMPILE: PASS\nREAL JAVA COMPILE: PASS\nNATIVE/NDK COMPILE: PASS (arm64-v8a, armeabi-v7a)\nREAL ANDROID Gradle :app:assembleDebug: PASS\nORIGINAL RAWLENS LKR NATIVE: PASS (successful 26938 published APK offline reuse)\nRUNTIME SOURCE INVARIANCE: PASS\nDEVICE IMAGE QUALITY: NOT RUN\n')
 (OUT/'26939_REAL_GRADLE_TASKS.txt').write_text(''.join('PASS '+t+'\n' for t in tasks))
 (OUT/'26939_APK.sha256').write_text(sha(R/APKNAME)+'  '+APKNAME+'\n')
 wf=R/'.github/workflows/build-26939-change-aware.yml'
 (OUT/'26939_ACTUAL_EXECUTED_BUILDER.sha256').write_text(sha(R/'build_26939_incremental.py')+'  build_26939_incremental.py\n')
 (OUT/'26939_ACTUAL_EXECUTED_WORKFLOW.sha256').write_text(sha(wf)+'  .github/workflows/build-26939-change-aware.yml\n')
 (OUT/'26939_ACTIONS_IDENTITY.txt').write_text('git_sha='+os.getenv('GITHUB_SHA','NOT_IN_ACTIONS')+'\ngithub_run_id='+os.getenv('GITHUB_RUN_ID','NOT_IN_ACTIONS')+'\n')
 for p in ('26939_BASE_26938_FULL_APP.sha256','26939_EXPECTED_FULL_APP.sha256','26939_PROTECTED_SOURCE.sha256','26939_CHANGED_RUNTIME_ALLOWLIST.txt','26939_ADDED_RUNTIME_PATHS.txt','26939_DELETED_RUNTIME_PATHS.txt'):
  shutil.copy2(R/p,OUT/p)
 shutil.copy2(R/'build_26939_incremental.py',OUT/'ACTUAL_EXECUTED_build_26939_incremental.py')
 shutil.copy2(wf,OUT/'ACTUAL_EXECUTED_build-26939-change-aware.yml')
 with (OUT/'26939_candidate_app_source.tar.gz').open('wb') as file:
  with gzip.GzipFile(filename='',mode='wb',compresslevel=1,mtime=0,fileobj=file) as g:
   with tarfile.open(fileobj=g,mode='w') as t:
    for p in sorted(parse(R/'26939_EXPECTED_FULL_APP.sha256')):
     src=R/p;meta=t.gettarinfo(str(src),arcname=p)
     meta.uid=meta.gid=0;meta.uname=meta.gname='';meta.mtime=0
     with src.open('rb') as inp:t.addfile(meta,inp)
 (OUT/'26939_candidate_app_source.tar.gz.sha256').write_text(sha(OUT/'26939_candidate_app_source.tar.gz')+'  26939_candidate_app_source.tar.gz\n')
 print('PASS sole 26939 assembled APK dual ABI, 2048 protected source invariant')

if __name__=='__main__':
 try:
  parser=argparse.ArgumentParser();parser.add_argument('command',choices=('seal','fetch','prepare','regress','verify-compiled','finalize'));parser.add_argument('--package-only',action='store_true');args=parser.parse_args()
  globals()['PACKAGE_ONLY']=args.package_only
  globals()[args.command.replace('-','_')]()
 except Exception as e:
  print(str(e),file=sys.stderr);sys.exit(1)
