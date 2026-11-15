#!/usr/bin/env python3
"""26941: exact successful 26940 V1 compiled authority, B/SR-OFF-only HDR+ descriptor efficiency and SDR/UHDR tone.
Maintain 26940 inherited 141 historical regressions, real GLSL SPIR-V/NDK/Kotlin/Java/assemble.
"""
import argparse,gzip,hashlib,json,os,pathlib,shutil,subprocess,sys,tarfile,urllib.request,zipfile
R=pathlib.Path(__file__).resolve().parent
TMP=R/'.photon_26941_incremental_work';OUT=R/'photon_26941_outputs'
ART=TMP/'26940-success.zip';BASE=TMP/'authority_26940';CAND=TMP/'candidate_26941'
REPO='SkyKing0007/Photon-Camera';BRANCH='experimental-clean-photon-rebuild'
RUN=43737095231;COMMIT='29bdfb706442417664273de14cec8d28363a9e9d';ART_ID=14170559036
ART_SHA='404448bec80db528390f424d5b6610fac8a290d28812bb5a2bc896e6e8a83f0b'
TAR_SHA='0f102fdb0190fa5afa57a083e4d89d50e0fbaa4e1273078ccde0d0076d84d5a9'
BUILDER_SHA='7d8e025f5c47a72d3b579f93203bbb872ba714689a3251e2a60b6adabf6ffe11'
WORKFLOW_SHA='4eb334e0a1ecb6e1d3171b940f4eaf4fc98bf9dc9af749f754cd1065fe215d2b'
PRIOR_APK_SHA='fad1a78a71f808b44c57150b9abdfe8e0b048836555b4d78e810ed9356a3c748'
APKNAME='IrisCamera-0.9726941-26941-iris-rawr-debug.apk'
NBASE=NFILES=2050;NCHANGE=7;NPROTECTED=2043
REQUIRED={'app/version.properties',
 'app/src/main/cpp/iris26864/Iris26864RealRawrCoordinator.cpp',
 'app/src/main/cpp/iris26864/bridge/Iris26888BOffVulkanExecutor.cpp',
 'app/src/main/assets/shaders/motionv2/render.glsl',
 'app/src/main/assets/shaders/motionv2/gainmap.glsl',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
 'app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java'}
STAGE1_FILES=[
 'README_PHOTON_26941_V1.md','26941_LOCAL_VERIFICATION.txt','26941_COMMIT_MESSAGE.txt',
 'build_26941_incremental.py','test_26941_source.py','test_26941_native_host.py','test_26941_tone_math.py','test_26941_shader_contract.py',
 'compile_26941_shaders.sh',
 'test_26941_patch_proof.py','test_26941_sealed_negatives.py','test_26941_workflow_refs.py',
 'prepare_26941_lkr_from_successful_26940.py',
 '26941_FORWARD_FULLINDEX.patch','26941_ROLLBACK_FULLINDEX.patch',
 '26941_BASE_26940_FULL_APP.sha256','26941_EXPECTED_FULL_APP.sha256',
 '26941_PROTECTED_SOURCE.sha256','26941_CHANGED_RUNTIME_ALLOWLIST.txt',
 '26941_ADDED_RUNTIME_PATHS.txt','26941_DELETED_RUNTIME_PATHS.txt',
 '26941_EXPECTED_ACTION_EXECUTABLES.txt',
 '26941_V1_STAGE_1_UPLOAD_PATHS.txt','26941_V1_STAGE_2_UPLOAD_PATHS.txt',
 '26941_V1_STAGE_3_UPLOAD_PATHS.txt']

def fail(msg):raise RuntimeError('26941 BLOCKED: '+str(msg))
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
 old=parse(R/'26941_BASE_26940_FULL_APP.sha256');new=parse(R/'26941_EXPECTED_FULL_APP.sha256')
 ch=set((R/'26941_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
 ad=set((R/'26941_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
 dl=set((R/'26941_DELETED_RUNTIME_PATHS.txt').read_text().splitlines())
 if (len(old),len(new),len(ch),len(old)-len(ch))!=(NBASE,NFILES,NCHANGE,NPROTECTED):fail('unexpected source universe count')
 if ch!=REQUIRED or ad or dl or set(old)!=set(new) or {p for p in old if old[p]!=new[p]}!=ch:fail('changed-file allowlist or source add/delete mismatch')
 if {p:h for p,h in old.items() if p not in ch}!=parse(R/'26941_PROTECTED_SOURCE.sha256'):fail('2043 protected hashes invalid')
 for p in ch:
  if '/vendor/' in p or '/jniLibs/' in p or p.endswith(('.so','.comp','.frag','.spv','.kt','.jar','.aar')):fail('unauthorized source domain '+p)
 if old['app/build.gradle']!=new['app/build.gradle']:fail('Gradle changed')
 return ch,old,new

def seal():
 ch,old,new=scope()
 sealed={}
 for line in (R/'26941_HANDOFF_HASHES.sha256').read_text().splitlines():
  try:h,p=line.split('  ',1)
  except ValueError:fail('malformed handoff hash line')
  if p in sealed or not (R/p).is_file() or sha(R/p)!=h:fail('missing/tampered sealed file '+p)
  sealed[p]=h
 wf='.github/workflows/build-26941-change-aware.yml';trigger='TRIGGER_26941.txt'
 wanted=set(STAGE1_FILES)|{wf,trigger}|{'handoff_payload_26941/'+p for p in ch}
 if set(sealed)!=wanted:fail('sealed file set differs '+str(sorted(wanted^set(sealed))))
 st=[(R/f'26941_V1_STAGE_{i}_UPLOAD_PATHS.txt').read_text().splitlines() for i in (1,2,3)]
 if st[0]!=sorted((wanted|{'26941_HANDOFF_HASHES.sha256'})-{wf,trigger}) or st[1]!=[wf] or st[2]!=[trigger]:fail('three-stage upload sequence differs')
 overlay={p.relative_to(R/'handoff_payload_26941').as_posix() for p in (R/'handoff_payload_26941').rglob('*') if p.is_file()}
 if overlay!=ch:fail('overlay paths unexpectedly changed')
 for p in ch:
  if sha(R/'handoff_payload_26941'/p)!=new[p]:fail('source payload SHA mismatch '+p)
 s=(R/wf).read_text()
 for k in ('verify_26904_v3_safety.py','verify_26904_v2_safety.py','test_26903_v3_archive_receipt.py',
  'build_26940_incremental.py seal','test_26940_sealed_negatives.py',
  'build_26941_incremental.py seal','build_26941_incremental.py fetch',
  'build_26941_incremental.py prepare','test_26941_patch_proof.py --live',
  'prepare_26941_lkr_from_successful_26940.py',
  'compile_26904_shaders_v2.sh','compile_26939_shaders.sh','compile_26941_shaders.sh',
  'test_26931_native_integrity.py --native','test_26931_native_integrity.py --cmake',
  'test_26931_native_integrity.py --apk',
  'build_26941_incremental.py verify-compiled','build_26941_incremental.py finalize',
  ':app:assembleDebug --stacktrace','actions/upload-artifact@v4'):
  if k not in s:fail('missing original mandatory Actions verification '+k)
 if s.count('actions/upload-artifact@v4')!=1 or s.count('./gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace')!=1:fail('not exactly one APK build/artifact')
 subprocess.run([sys.executable,'-S','test_26941_workflow_refs.py']+([] if globals().get('PACKAGE_ONLY') else ['--on-actions']),cwd=R,check=True)
 print('PASS seal successful 26940 compiled base 2050 -> 26941 2050, changed 7, protected 2043, source added/deleted 0')

def fetch():
 seal();token=os.getenv('GITHUB_TOKEN','')
 if not token or os.getenv('GITHUB_REPOSITORY')!=REPO or os.getenv('GITHUB_REF_NAME')!=BRANCH:fail('Actions token/branch/repository identity missing')
 def get(endpoint):
  req=urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+endpoint,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'})
  with urllib.request.urlopen(req,timeout=120) as resp:return json.load(resp)
 run=get('actions/runs/'+str(RUN));artifact=get('actions/artifacts/'+str(ART_ID))
 if run.get('id')!=RUN or run.get('conclusion')!='success' or run.get('head_branch')!=BRANCH or run.get('head_sha')!=COMMIT:fail('previous 26940 run not successful')
 if artifact.get('id')!=ART_ID or artifact.get('expired') or artifact.get('digest')!='sha256:'+ART_SHA or artifact.get('workflow_run',{}).get('id') not in (None,RUN):fail('26940 official artifact identity wrong')
 TMP.mkdir(exist_ok=True)
 subprocess.run(['curl','--fail','--location','--retry','3','--silent','--show-error','-H','Authorization: Bearer '+token,'-H','Accept: application/vnd.github+json','https://api.github.com/repos/'+REPO+'/actions/artifacts/'+str(ART_ID)+'/zip','-o',str(ART)],check=True)
 if sha(ART)!=ART_SHA:fail('prior 26940 official artifact archive SHA mismatch')
 print('PASS fetched exact successful 26940 V1 run/artifact SHA')

def safe_tar(tar_path,dst):
 with tarfile.open(tar_path,'r:gz') as t:
  for m in t:
   k=pathlib.PurePosixPath(m.name)
   if not k.parts or k.is_absolute() or k.parts[0]!='app' or '..' in k.parts or not (m.isfile() or m.isdir()) or m.issym() or m.islnk():fail('unsafe authority tar path '+m.name)
  t.extractall(dst,filter='data')

def prepare():
 seal()
 if not ART.is_file() or sha(ART)!=ART_SHA:fail('prior 26940 archive missing')
 for d in (BASE,CAND):
  if d.exists():shutil.rmtree(d)
 BASE.mkdir(parents=True)
 with zipfile.ZipFile(ART) as z:
  if z.testzip():fail('official prior artifact CRC failure')
  def get(n):
   p='photon_26940_outputs/'+n
   if p not in z.namelist():fail('missing 26940 published member '+p)
   return z.read(p)
  raw=get('26940_candidate_app_source.tar.gz')
  if hashlib.sha256(raw).hexdigest()!=TAR_SHA:fail('26940 actual compiled source tar mismatch')
  if get('26940_PREBUILD_SEALED_APP.sha256')!=(R/'26941_BASE_26940_FULL_APP.sha256').read_bytes():fail('26940 prebuild source manifest mismatch')
  if get('26940_EXPECTED_FULL_APP.sha256')!=(R/'26941_BASE_26940_FULL_APP.sha256').read_bytes():fail('26940 official source manifest mismatch')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build_26940_incremental.py')).hexdigest()!=BUILDER_SHA or BUILDER_SHA not in get('26940_ACTUAL_EXECUTED_BUILDER.sha256').decode():fail('26940 builder authority wrong')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build-26940-change-aware.yml')).hexdigest()!=WORKFLOW_SHA or WORKFLOW_SHA not in get('26940_ACTUAL_EXECUTED_WORKFLOW.sha256').decode():fail('26940 workflow authority wrong')
  if PRIOR_APK_SHA not in get('26940_APK.sha256').decode():fail('26940 actual APK SHA wrong')
  ident=get('26940_ACTIONS_IDENTITY.txt').decode()
  if 'git_sha='+COMMIT not in ident or 'github_run_id='+str(RUN) not in ident:fail('26940 runtime identity wrong')
  for flag in ('REAL PINNED GLSL COMPILE: PASS','REAL SPIR-V VALIDATION: PASS','REAL KOTLIN COMPILE: PASS','REAL JAVA COMPILE: PASS','NATIVE/NDK COMPILE: PASS','REAL ANDROID Gradle :app:assembleDebug: PASS','RUNTIME SOURCE INVARIANCE: PASS'):
   if flag not in get('26940_COMPILER_STATUS.txt').decode():fail('26940 full real compiler status missing '+flag)
  for task in (':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL'):
   if 'PASS '+task not in get('26940_REAL_GRADLE_TASKS.txt').decode():fail('26940 real compile task not confirmed '+task)
  for receipt in ('26940_COMPILER_STATUS.txt','26940_REAL_GRADLE_TASKS.txt'):
   if not get(receipt):fail('26940 successful compiler receipt absent '+receipt)
  TMP.mkdir(exist_ok=True)
  (TMP/'26940_candidate_app_source.tar.gz').write_bytes(raw)
 safe_tar(TMP/'26940_candidate_app_source.tar.gz',BASE)
 exact(BASE,'26941_BASE_26940_FULL_APP.sha256','exact actual successful 26940 compiled source')
 shutil.copytree(BASE,CAND)
 for p in sorted(REQUIRED):
  src=R/'handoff_payload_26941'/p;dst=CAND/p
  if not src.is_file() or not dst.is_file():fail('missing 26941 payload or authority '+p)
  shutil.copy2(src,dst)
 exact(CAND,'26941_EXPECTED_FULL_APP.sha256','strict 26941 full candidate')
 if not (R/'gradlew').is_file() or not (R/'app/build.gradle').is_file():fail('real Android checkout/SDK project unavailable')
 if (R/'app/src').exists():shutil.rmtree(R/'app/src')
 shutil.copytree(CAND/'app/src',R/'app/src')
 shutil.copy2(CAND/'app/version.properties',R/'app/version.properties')
 shutil.copy2(CAND/'app/build.gradle',R/'app/build.gradle')
 if (R/'app/.cxx').exists():shutil.rmtree(R/'app/.cxx')
 exact(R,'26941_EXPECTED_FULL_APP.sha256','live 26941 compiled candidate source')
 OUT.mkdir(exist_ok=True)
 (OUT/'26941_SOURCE_SCOPE.txt').write_text(f'PRIOR SUCCESS 26940 V1 run={RUN} commit={COMMIT} artifact={ART_ID}\nART_SHA={ART_SHA}\nTAR_SHA={TAR_SHA}\nBUILDER_SHA={BUILDER_SHA}\nWORKFLOW_SHA={WORKFLOW_SHA}\nPRIOR_APK_SHA={PRIOR_APK_SHA}\n2050 source changed=7 protected=2043 added=0 deleted=0; B HDR+ SR OFF zoom<1.10 GPU-reset + SDR/UHDR primary only; SR ON, A, A+B, Motion, Night, LONG, DNG, Spektra and vendor unchanged\n'+''.join(x+'\n' for x in sorted(REQUIRED)))
 print('PASS exact 26940 compiled authority reconstructed, candidate-first source, unchanged 2043 protected')

def regress():
 seal();exact(R,'26941_EXPECTED_FULL_APP.sha256','26941 live candidate')
 for t in ('test_26941_source.py','test_26941_native_host.py','test_26941_tone_math.py',
           'test_26941_shader_contract.py','test_26941_patch_proof.py'):
  subprocess.run([sys.executable,'-S',t,'--live'],cwd=R,check=True)
 print('PASS B OFF isolated descriptor-on-use, matched SDR primary, gain-map bright-only, UI removal, RAWR math unchanged; exact patches')

def verify_compiled():
 regress()
 receipt=OUT/'26941_REAL_GLSL_SPIRV_COMPILER.txt'
 if not receipt.is_file() or '16.5.0' not in receipt.read_text() or 'PASS actual 26941 inline ESSL 300 310' not in receipt.read_text():fail('mandatory current real glslang optimizer compiler receipt absent')
 for p in ('raw_lens_median','lkr_smooth_white','motion_render','motion_gainmap','b_native_final'):
  for x in (('es310.frag',) if p=='b_native_final' else ('es300.frag','es310.frag')):
   f=OUT/('26941_'+p+'_'+x)
   if not f.is_file() or sha(f) not in receipt.read_text():fail('real shader digest not bound to compiled file '+str(f))
 subprocess.run([sys.executable,'-S','test_26931_native_integrity.py','--native'],cwd=R,check=True)
 r=OUT/'26941_INHERITED_LKR_NATIVE_RECEIPT.txt'
 if not r.is_file() or 'SUCCESSFUL 26940 Actions run='+str(RUN) not in r.read_text():fail('wrong RawLens native provenance')
 (OUT/'26941_PREBUILD_SEALED_APP.sha256').write_bytes((R/'26941_EXPECTED_FULL_APP.sha256').read_bytes())
 print('PASS current 26941 changed ESSL, real glslang 16.5 and SPIR-V compiler, LKR provenance, source sealed')

def finalize():
 regress()
 if (OUT/'26941_PREBUILD_SEALED_APP.sha256').read_bytes()!=(R/'26941_EXPECTED_FULL_APP.sha256').read_bytes():fail('unsealed actual source after compiler')
 log=(OUT/'26941_gradle_assemble.log').read_text(errors='replace')
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
 (OUT/'26941_COMPILER_STATUS.txt').write_text('REAL PINNED GLSL COMPILE: PASS (actual current 26941 changed SDR/UHDR GLSL)\nREAL SPIR-V VALIDATION: PASS\nREAL KOTLIN COMPILE: PASS\nREAL JAVA COMPILE: PASS\nNATIVE/NDK COMPILE: PASS (both ABIs)\nREAL ANDROID Gradle :app:assembleDebug: PASS\nORIGINAL RAWLENS LKR NATIVE: PASS (26940 published APK offline)\nRUNTIME SOURCE INVARIANCE: PASS\nDEVICE IMAGE QUALITY: NOT RUN\n')
 (OUT/'26941_REAL_GRADLE_TASKS.txt').write_text(''.join('PASS '+t+'\n' for t in tasks))
 (OUT/'26941_APK.sha256').write_text(sha(R/APKNAME)+'  '+APKNAME+'\n')
 wf=R/'.github/workflows/build-26941-change-aware.yml'
 (OUT/'26941_ACTUAL_EXECUTED_BUILDER.sha256').write_text(sha(R/'build_26941_incremental.py')+'  build_26941_incremental.py\n')
 (OUT/'26941_ACTUAL_EXECUTED_WORKFLOW.sha256').write_text(sha(wf)+'  .github/workflows/build-26941-change-aware.yml\n')
 (OUT/'26941_ACTIONS_IDENTITY.txt').write_text('git_sha='+os.getenv('GITHUB_SHA','NOT_IN_ACTIONS')+'\ngithub_run_id='+os.getenv('GITHUB_RUN_ID','NOT_IN_ACTIONS')+'\n')
 for p in ('26941_BASE_26940_FULL_APP.sha256','26941_EXPECTED_FULL_APP.sha256','26941_PROTECTED_SOURCE.sha256','26941_CHANGED_RUNTIME_ALLOWLIST.txt','26941_ADDED_RUNTIME_PATHS.txt','26941_DELETED_RUNTIME_PATHS.txt'):
  shutil.copy2(R/p,OUT/p)
 shutil.copy2(R/'build_26941_incremental.py',OUT/'ACTUAL_EXECUTED_build_26941_incremental.py')
 shutil.copy2(wf,OUT/'ACTUAL_EXECUTED_build-26941-change-aware.yml')
 with (OUT/'26941_candidate_app_source.tar.gz').open('wb') as file:
  with gzip.GzipFile(filename='',mode='wb',compresslevel=1,mtime=0,fileobj=file) as g:
   with tarfile.open(fileobj=g,mode='w') as t:
    for p in sorted(parse(R/'26941_EXPECTED_FULL_APP.sha256')):
     src=R/p;meta=t.gettarinfo(str(src),arcname=p)
     meta.uid=meta.gid=0;meta.uname=meta.gname='';meta.mtime=0
     with src.open('rb') as inp:t.addfile(meta,inp)
 (OUT/'26941_candidate_app_source.tar.gz.sha256').write_text(sha(OUT/'26941_candidate_app_source.tar.gz')+'  26941_candidate_app_source.tar.gz\n')
 print('PASS 26941 final actual real compiled APK, 2043 protected SHA invariant, actual tar+apk checksums')

if __name__=='__main__':
 try:
  p=argparse.ArgumentParser();p.add_argument('command',choices=('seal','fetch','prepare','regress','verify-compiled','finalize'));p.add_argument('--package-only',action='store_true');a=p.parse_args()
  globals()['PACKAGE_ONLY']=a.package_only
  globals()[a.command.replace('-','_')]()
 except Exception as error:
  print(str(error),file=sys.stderr);sys.exit(1)
