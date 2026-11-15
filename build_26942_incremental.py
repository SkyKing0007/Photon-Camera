#!/usr/bin/env python3
"""26942: exact successful 26941 V1 compiled authority, B/SR-OFF-only HDR+ four-pass GPU chunk coalescing.
Maintain 26941 inherited 141 historical regressions, real GLSL SPIR-V/NDK/Kotlin/Java/assemble.
"""
import argparse,gzip,hashlib,json,os,pathlib,shutil,subprocess,sys,tarfile,urllib.request,zipfile
R=pathlib.Path(__file__).resolve().parent
TMP=R/'.photon_26942_incremental_work';OUT=R/'photon_26942_outputs'
ART=TMP/'26941-success.zip';BASE=TMP/'authority_26941';CAND=TMP/'candidate_26942'
REPO='SkyKing0007/Photon-Camera';BRANCH='experimental-clean-photon-rebuild'
RUN=43744946760;COMMIT='05af6b7c0eb9ddeff59cf4947f8469b384cc8ed2';ART_ID=14174631230
ART_SHA='24069acd5c83482471e72f8af8211775335072e3876e93cd72a5de4cb71971f2'
TAR_SHA='ba1d5ce75a2a5dbc01fb0f6ed3b94193d9fbbf24fe033adc6c59ee6a46e31aa5'
BUILDER_SHA='bb86f4a5e65e07a0c1312b4efdc5c9f2866d056de87a7c9de0788dcd99072024'
WORKFLOW_SHA='18578ec9f6682cc35255691f66a8b8d41311609041c164835e8847d561e049d6'
PRIOR_APK_SHA='8fce2c03d78fcea209e86b47d75d25b0a010dca604e987ce3074298e02583648'
APKNAME='IrisCamera-0.9726942-26942-iris-rawr-debug.apk'
NBASE=NFILES=2050;NCHANGE=2;NPROTECTED=2048
REQUIRED={'app/version.properties',
 'app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqCoordinator.cpp'}
STAGE1_FILES=[
 'README_PHOTON_26942_V2.md','26942_LOCAL_VERIFICATION.txt','26942_COMMIT_MESSAGE.txt',
 'build_26942_incremental.py','test_26942_source.py','test_26942_native_host.py','test_26942_shader_contract.py',
 'compile_26942_shaders.sh',
 'test_26942_patch_proof.py','test_26942_sealed_negatives.py','test_26942_workflow_refs.py',
 'prepare_26942_lkr_from_successful_26941.py',
 '26942_FORWARD_FULLINDEX.patch','26942_ROLLBACK_FULLINDEX.patch',
 '26942_BASE_26941_FULL_APP.sha256','26942_EXPECTED_FULL_APP.sha256',
 '26942_PROTECTED_SOURCE.sha256','26942_CHANGED_RUNTIME_ALLOWLIST.txt',
 '26942_ADDED_RUNTIME_PATHS.txt','26942_DELETED_RUNTIME_PATHS.txt',
 '26942_EXPECTED_ACTION_EXECUTABLES.txt',
 '26942_V2_STAGE_1_UPLOAD_PATHS.txt','26942_V2_STAGE_2_UPLOAD_PATHS.txt',
 '26942_V2_STAGE_3_UPLOAD_PATHS.txt']

def fail(msg):raise RuntimeError('26942 BLOCKED: '+str(msg))
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
 old=parse(R/'26942_BASE_26941_FULL_APP.sha256');new=parse(R/'26942_EXPECTED_FULL_APP.sha256')
 ch=set((R/'26942_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
 ad=set((R/'26942_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
 dl=set((R/'26942_DELETED_RUNTIME_PATHS.txt').read_text().splitlines())
 if (len(old),len(new),len(ch),len(old)-len(ch))!=(NBASE,NFILES,NCHANGE,NPROTECTED):fail('unexpected source universe count')
 if ch!=REQUIRED or ad or dl or set(old)!=set(new) or {p for p in old if old[p]!=new[p]}!=ch:fail('changed-file allowlist or source add/delete mismatch')
 if {p:h for p,h in old.items() if p not in ch}!=parse(R/'26942_PROTECTED_SOURCE.sha256'):fail('2048 protected hashes invalid')
 for p in ch:
  if '/vendor/' in p or '/jniLibs/' in p or p.endswith(('.so','.comp','.frag','.spv','.kt','.jar','.aar')):fail('unauthorized source domain '+p)
 if old['app/build.gradle']!=new['app/build.gradle']:fail('Gradle changed')
 return ch,old,new

def seal():
 ch,old,new=scope()
 sealed={}
 for line in (R/'26942_HANDOFF_HASHES.sha256').read_text().splitlines():
  try:h,p=line.split('  ',1)
  except ValueError:fail('malformed handoff hash line')
  if p in sealed or not (R/p).is_file() or sha(R/p)!=h:fail('missing/tampered sealed file '+p)
  sealed[p]=h
 wf='.github/workflows/build-26942-change-aware.yml';trigger='TRIGGER_26942.txt'
 wanted=set(STAGE1_FILES)|{wf,trigger}|{'handoff_payload_26942/'+p for p in ch}
 if set(sealed)!=wanted:fail('sealed file set differs '+str(sorted(wanted^set(sealed))))
 st=[(R/f'26942_V2_STAGE_{i}_UPLOAD_PATHS.txt').read_text().splitlines() for i in (1,2,3)]
 if st[0]!=sorted((wanted|{'26942_HANDOFF_HASHES.sha256'})-{wf,trigger}) or st[1]!=[wf] or st[2]!=[trigger]:fail('three-stage upload sequence differs')
 overlay={p.relative_to(R/'handoff_payload_26942').as_posix() for p in (R/'handoff_payload_26942').rglob('*') if p.is_file()}
 if overlay!=ch:fail('overlay paths unexpectedly changed')
 for p in ch:
  if sha(R/'handoff_payload_26942'/p)!=new[p]:fail('source payload SHA mismatch '+p)
 s=(R/wf).read_text()
 for k in ('verify_26904_v3_safety.py','verify_26904_v2_safety.py','test_26903_v3_archive_receipt.py',
  'build_26941_incremental.py seal','test_26941_sealed_negatives.py',
  'build_26942_incremental.py seal','build_26942_incremental.py fetch',
  'build_26942_incremental.py prepare','test_26942_patch_proof.py --live',
  'prepare_26942_lkr_from_successful_26941.py',
  'compile_26904_shaders_v2.sh','compile_26939_shaders.sh','compile_26941_shaders.sh','compile_26942_shaders.sh',
  'test_26931_native_integrity.py --native','test_26931_native_integrity.py --cmake',
  'test_26931_native_integrity.py --apk',
  'build_26942_incremental.py verify-compiled','build_26942_incremental.py finalize',
  ':app:assembleDebug --stacktrace','actions/upload-artifact@v4'):
  if k not in s:fail('missing original mandatory Actions verification '+k)
 if s.count('actions/upload-artifact@v4')!=1 or s.count('./gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace')!=1:fail('not exactly one APK build/artifact')
 subprocess.run([sys.executable,'-S','test_26942_workflow_refs.py']+([] if globals().get('PACKAGE_ONLY') else ['--on-actions']),cwd=R,check=True)
 print('PASS seal successful 26941 compiled base 2050 -> 26942 2050, changed 2, protected 2048, source added/deleted 0')

def fetch():
 seal();token=os.getenv('GITHUB_TOKEN','')
 if not token or os.getenv('GITHUB_REPOSITORY')!=REPO or os.getenv('GITHUB_REF_NAME')!=BRANCH:fail('Actions token/branch/repository identity missing')
 def get(endpoint):
  req=urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+endpoint,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'})
  with urllib.request.urlopen(req,timeout=120) as resp:return json.load(resp)
 run=get('actions/runs/'+str(RUN));artifact=get('actions/artifacts/'+str(ART_ID))
 if run.get('id')!=RUN or run.get('conclusion')!='success' or run.get('head_branch')!=BRANCH or run.get('head_sha')!=COMMIT:fail('previous 26941 run not successful')
 if artifact.get('id')!=ART_ID or artifact.get('expired') or artifact.get('digest')!='sha256:'+ART_SHA or artifact.get('workflow_run',{}).get('id') not in (None,RUN):fail('26941 official artifact identity wrong')
 TMP.mkdir(exist_ok=True)
 subprocess.run(['curl','--fail','--location','--retry','3','--silent','--show-error','-H','Authorization: Bearer '+token,'-H','Accept: application/vnd.github+json','https://api.github.com/repos/'+REPO+'/actions/artifacts/'+str(ART_ID)+'/zip','-o',str(ART)],check=True)
 if sha(ART)!=ART_SHA:fail('prior 26941 official artifact archive SHA mismatch')
 print('PASS fetched exact successful 26941 V1 run/artifact SHA')

def safe_tar(tar_path,dst):
 with tarfile.open(tar_path,'r:gz') as t:
  for m in t:
   k=pathlib.PurePosixPath(m.name)
   if not k.parts or k.is_absolute() or k.parts[0]!='app' or '..' in k.parts or not (m.isfile() or m.isdir()) or m.issym() or m.islnk():fail('unsafe authority tar path '+m.name)
  t.extractall(dst,filter='data')

def prepare():
 seal()
 if not ART.is_file() or sha(ART)!=ART_SHA:fail('prior 26941 archive missing')
 for d in (BASE,CAND):
  if d.exists():shutil.rmtree(d)
 BASE.mkdir(parents=True)
 with zipfile.ZipFile(ART) as z:
  if z.testzip():fail('official prior artifact CRC failure')
  def get(n):
   p='photon_26941_outputs/'+n
   if p not in z.namelist():fail('missing 26941 published member '+p)
   return z.read(p)
  raw=get('26941_candidate_app_source.tar.gz')
  if hashlib.sha256(raw).hexdigest()!=TAR_SHA:fail('26941 actual compiled source tar mismatch')
  if get('26941_PREBUILD_SEALED_APP.sha256')!=(R/'26942_BASE_26941_FULL_APP.sha256').read_bytes():fail('26941 prebuild source manifest mismatch')
  if get('26941_EXPECTED_FULL_APP.sha256')!=(R/'26942_BASE_26941_FULL_APP.sha256').read_bytes():fail('26941 official source manifest mismatch')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build_26941_incremental.py')).hexdigest()!=BUILDER_SHA or BUILDER_SHA not in get('26941_ACTUAL_EXECUTED_BUILDER.sha256').decode():fail('26941 builder authority wrong')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build-26941-change-aware.yml')).hexdigest()!=WORKFLOW_SHA or WORKFLOW_SHA not in get('26941_ACTUAL_EXECUTED_WORKFLOW.sha256').decode():fail('26941 workflow authority wrong')
  if PRIOR_APK_SHA not in get('26941_APK.sha256').decode():fail('26941 actual APK SHA wrong')
  ident=get('26941_ACTIONS_IDENTITY.txt').decode()
  if 'git_sha='+COMMIT not in ident or 'github_run_id='+str(RUN) not in ident:fail('26941 runtime identity wrong')
  for flag in ('REAL PINNED GLSL COMPILE: PASS','REAL SPIR-V VALIDATION: PASS','REAL KOTLIN COMPILE: PASS','REAL JAVA COMPILE: PASS','NATIVE/NDK COMPILE: PASS','REAL ANDROID Gradle :app:assembleDebug: PASS','RUNTIME SOURCE INVARIANCE: PASS'):
   if flag not in get('26941_COMPILER_STATUS.txt').decode():fail('26941 full real compiler status missing '+flag)
  for task in (':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL'):
   if 'PASS '+task not in get('26941_REAL_GRADLE_TASKS.txt').decode():fail('26941 real compile task not confirmed '+task)
  for receipt in ('26941_COMPILER_STATUS.txt','26941_REAL_GRADLE_TASKS.txt'):
   if not get(receipt):fail('26941 successful compiler receipt absent '+receipt)
  TMP.mkdir(exist_ok=True)
  (TMP/'26941_candidate_app_source.tar.gz').write_bytes(raw)
 safe_tar(TMP/'26941_candidate_app_source.tar.gz',BASE)
 exact(BASE,'26942_BASE_26941_FULL_APP.sha256','exact actual successful 26941 compiled source')
 shutil.copytree(BASE,CAND)
 for p in sorted(REQUIRED):
  src=R/'handoff_payload_26942'/p;dst=CAND/p
  if not src.is_file() or not dst.is_file():fail('missing 26942 payload or authority '+p)
  shutil.copy2(src,dst)
 exact(CAND,'26942_EXPECTED_FULL_APP.sha256','strict 26942 full candidate')
 if not (R/'gradlew').is_file() or not (R/'app/build.gradle').is_file():fail('real Android checkout/SDK project unavailable')
 if (R/'app/src').exists():shutil.rmtree(R/'app/src')
 shutil.copytree(CAND/'app/src',R/'app/src')
 shutil.copy2(CAND/'app/version.properties',R/'app/version.properties')
 shutil.copy2(CAND/'app/build.gradle',R/'app/build.gradle')
 if (R/'app/.cxx').exists():shutil.rmtree(R/'app/.cxx')
 exact(R,'26942_EXPECTED_FULL_APP.sha256','live 26942 compiled candidate source')
 OUT.mkdir(exist_ok=True)
 (OUT/'26942_SOURCE_SCOPE.txt').write_text(f'PRIOR SUCCESS 26941 V1 run={RUN} commit={COMMIT} artifact={ART_ID}\nART_SHA={ART_SHA}\nTAR_SHA={TAR_SHA}\nBUILDER_SHA={BUILDER_SHA}\nWORKFLOW_SHA={WORKFLOW_SHA}\nPRIOR_APK_SHA={PRIOR_APK_SHA}\n2050 source changed=2 protected=2048 added=0 deleted=0; B HDR+ SR OFF zoom<1.10 batched later-pass pad+frequency merge only, 42 fewer GPU submissions for 15 frames; all other modes unchanged; SR ON, A, A+B, Motion, Night, LONG, DNG, Spektra and vendor unchanged\n'+''.join(x+'\n' for x in sorted(REQUIRED)))
 print('PASS exact 26941 compiled authority reconstructed, candidate-first source, unchanged 2048 protected')

def regress():
 seal();exact(R,'26942_EXPECTED_FULL_APP.sha256','26942 live candidate')
 for t in ('test_26942_source.py','test_26942_native_host.py',
           'test_26942_shader_contract.py','test_26942_patch_proof.py'):
  subprocess.run([sys.executable,'-S',t,'--live'],cwd=R,check=True)
 print('PASS B OFF guarded nonaligning pass pad+merge batching, all 15 frames, unchanged RAWR math and SDR/UHDR, exact patches; exact patches')

def verify_compiled():
 regress()
 receipt=OUT/'26942_REAL_GLSL_SPIRV_COMPILER.txt'
 if not receipt.is_file() or '16.5.0' not in receipt.read_text() or 'PASS actual 26942 inline ESSL 300 310' not in receipt.read_text():fail('mandatory current real glslang optimizer compiler receipt absent')
 for p in ('raw_lens_median','lkr_smooth_white','motion_render','motion_gainmap','b_native_final'):
  for x in (('es310.frag',) if p=='b_native_final' else ('es300.frag','es310.frag')):
   f=OUT/('26942_'+p+'_'+x)
   if not f.is_file() or sha(f) not in receipt.read_text():fail('real shader digest not bound to compiled file '+str(f))
 subprocess.run([sys.executable,'-S','test_26931_native_integrity.py','--native'],cwd=R,check=True)
 r=OUT/'26942_INHERITED_LKR_NATIVE_RECEIPT.txt'
 if not r.is_file() or 'SUCCESSFUL 26941 Actions run='+str(RUN) not in r.read_text():fail('wrong RawLens native provenance')
 (OUT/'26942_PREBUILD_SEALED_APP.sha256').write_bytes((R/'26942_EXPECTED_FULL_APP.sha256').read_bytes())
 print('PASS current 26942 inherited ESSL, real glslang 16.5 and SPIR-V compiler, LKR provenance, source sealed')

def finalize():
 regress()
 if (OUT/'26942_PREBUILD_SEALED_APP.sha256').read_bytes()!=(R/'26942_EXPECTED_FULL_APP.sha256').read_bytes():fail('unsealed actual source after compiler')
 log=(OUT/'26942_gradle_assemble.log').read_text(errors='replace')
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
 (OUT/'26942_COMPILER_STATUS.txt').write_text('REAL PINNED GLSL COMPILE: PASS (actual current 26942 inherited authoritative SDR/UHDR GLSL unchanged, genuinely recompiled)\nREAL SPIR-V VALIDATION: PASS\nREAL KOTLIN COMPILE: PASS\nREAL JAVA COMPILE: PASS\nNATIVE/NDK COMPILE: PASS (both ABIs)\nREAL ANDROID Gradle :app:assembleDebug: PASS\nORIGINAL RAWLENS LKR NATIVE: PASS (26941 published APK offline)\nRUNTIME SOURCE INVARIANCE: PASS\nDEVICE IMAGE QUALITY: NOT RUN\n')
 (OUT/'26942_REAL_GRADLE_TASKS.txt').write_text(''.join('PASS '+t+'\n' for t in tasks))
 (OUT/'26942_APK.sha256').write_text(sha(R/APKNAME)+'  '+APKNAME+'\n')
 wf=R/'.github/workflows/build-26942-change-aware.yml'
 (OUT/'26942_ACTUAL_EXECUTED_BUILDER.sha256').write_text(sha(R/'build_26942_incremental.py')+'  build_26942_incremental.py\n')
 (OUT/'26942_ACTUAL_EXECUTED_WORKFLOW.sha256').write_text(sha(wf)+'  .github/workflows/build-26942-change-aware.yml\n')
 (OUT/'26942_ACTIONS_IDENTITY.txt').write_text('git_sha='+os.getenv('GITHUB_SHA','NOT_IN_ACTIONS')+'\ngithub_run_id='+os.getenv('GITHUB_RUN_ID','NOT_IN_ACTIONS')+'\n')
 for p in ('26942_BASE_26941_FULL_APP.sha256','26942_EXPECTED_FULL_APP.sha256','26942_PROTECTED_SOURCE.sha256','26942_CHANGED_RUNTIME_ALLOWLIST.txt','26942_ADDED_RUNTIME_PATHS.txt','26942_DELETED_RUNTIME_PATHS.txt'):
  shutil.copy2(R/p,OUT/p)
 shutil.copy2(R/'build_26942_incremental.py',OUT/'ACTUAL_EXECUTED_build_26942_incremental.py')
 shutil.copy2(wf,OUT/'ACTUAL_EXECUTED_build-26942-change-aware.yml')
 with (OUT/'26942_candidate_app_source.tar.gz').open('wb') as file:
  with gzip.GzipFile(filename='',mode='wb',compresslevel=1,mtime=0,fileobj=file) as g:
   with tarfile.open(fileobj=g,mode='w') as t:
    for p in sorted(parse(R/'26942_EXPECTED_FULL_APP.sha256')):
     src=R/p;meta=t.gettarinfo(str(src),arcname=p)
     meta.uid=meta.gid=0;meta.uname=meta.gname='';meta.mtime=0
     with src.open('rb') as inp:t.addfile(meta,inp)
 (OUT/'26942_candidate_app_source.tar.gz.sha256').write_text(sha(OUT/'26942_candidate_app_source.tar.gz')+'  26942_candidate_app_source.tar.gz\n')
 print('PASS 26942 final actual real compiled APK, 2048 protected SHA invariant, actual tar+apk checksums')

if __name__=='__main__':
 try:
  p=argparse.ArgumentParser();p.add_argument('command',choices=('seal','fetch','prepare','regress','verify-compiled','finalize'));p.add_argument('--package-only',action='store_true');a=p.parse_args()
  globals()['PACKAGE_ONLY']=a.package_only
  globals()[a.command.replace('-','_')]()
 except Exception as error:
  print(str(error),file=sys.stderr);sys.exit(1)
