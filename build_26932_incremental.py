#!/usr/bin/env python3
"""Photon 26932 3-stage, candidate-first, source-sealed, exact successful 26931 Actions runtime.
Never rebuild a previously published APK, use repository app/src as authority, or write Git refs.
Only a new 26932 GitHub Actions workflow executes the Android build compilers.
"""
from __future__ import annotations
import argparse,gzip,hashlib,json,os,pathlib,shutil,subprocess,sys,tarfile,urllib.request,zipfile
R=pathlib.Path(__file__).resolve().parent
TMP=R/'.photon_26932_work';OUT=R/'photon_26932_outputs'
ART=TMP/'26931-success.zip';BASE=TMP/'authority_26931';CAND=TMP/'candidate_26932'
RUN=43624345777; COMMIT='ac52ab1080cf655b485f446c7ae0977f0dc1af61'; ART_ID=14125593433
ART_SHA='59c4808d945d08ff480f52871b51518efb0cbbd36ad431675eaf08e63744d054'
TAR_SHA='fdf1b24f91839a7270232befaadd6e1b6b19c5185dd2b15cae625a8d54e1e43c'
BUILDER_SHA='97a20ba33245eeea95553e7964455c9cac62f7c30974906371de73bc8361774c'
WORKFLOW_SHA='c23ce88c65823bc1d746892c4c7e61af1f2ef0463c25dfcee55f2ebaa2e1a3ea'
PRIOR_APK_SHA='44ff78f491eaa44ee8a985f9e36421f8322decb285671f980fcf44a5b2ed65f6'
REPO='SkyKing0007/Photon-Camera';BRANCH='experimental-clean-photon-rebuild'
APKNAME='IrisCamera-0.9726932-26932-iris-rawr-debug.apk'
NBASE=2046;NFILES=2048;NCHANGE=7;NADD=2;NPROTECTED=2039
REQUIRED={
 'app/version.properties',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/Iris26876BGpuFinalRenderer.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
 'app/src/main/assets/shaders/motionv2/render.glsl',
 'app/src/main/assets/shaders/motionv2/gainmap.glsl',
 'app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag'}
ADDED={
 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932RawLensMedian.kt',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932LkrSmoothWhite.kt'}
STAGE1_FILES=['README_PHOTON_26932_V1.md','build_26932_incremental.py','test_26932_source.py','test_26932_shader_contract.py',
 'test_26932_math.py','test_26932_patch_proof.py','test_26932_sealed_negatives.py',
 'test_26932_workflow_refs.py','compile_26932_shaders.sh',
 '26932_FORWARD_FULLINDEX.patch','26932_ROLLBACK_FULLINDEX.patch',
 '26932_BASE_26931_FULL_APP.sha256','26932_EXPECTED_FULL_APP.sha256',
 '26932_PROTECTED_SOURCE.sha256','26932_CHANGED_RUNTIME_ALLOWLIST.txt',
 '26932_ADDED_RUNTIME_PATHS.txt','26932_DELETED_RUNTIME_PATHS.txt',
 '26932_EXPECTED_ACTION_EXECUTABLES.txt','26932_V1_STAGE_1_UPLOAD_PATHS.txt',
 '26932_V1_STAGE_2_UPLOAD_PATHS.txt','26932_V1_STAGE_3_UPLOAD_PATHS.txt']

def fail(s):raise RuntimeError('26932 BLOCKED: '+str(s))
def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def parse(path):
 d={}
 for l in path.read_text().splitlines():
  h,k=l.split('  ',1)
  if len(h)!=64 or len(k)<4 or not k.startswith('app/') or k in d or '..' in pathlib.PurePosixPath(k).parts:fail('bad manifest entry '+l)
  d[k]=h
 return d
def scan(root):
 d={}
 for p in [*(root/'app/src').rglob('*'),root/'app/build.gradle',root/'app/version.properties']:
  if p.is_symlink():fail('source symlink '+str(p))
  if p.is_file():d[p.relative_to(root).as_posix()]=sha(p)
 return d
def exact(root,name,label):
 a=scan(root);b=parse(R/name)
 if a!=b:
  missing=sorted(b.keys()-a.keys());unexpected=sorted(a.keys()-b.keys())
  modified=[p for p in b if p in a and b[p]!=a[p]]
  fail(f'{label}: missing={missing[:5]}, unexpected={unexpected[:5]}, mismatches={modified[:6]}')
 print('PASS',label,'files',len(a));return a

def scope():
 b=parse(R/'26932_BASE_26931_FULL_APP.sha256');n=parse(R/'26932_EXPECTED_FULL_APP.sha256')
 ch=set((R/'26932_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
 ad=set((R/'26932_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
 dl=set((R/'26932_DELETED_RUNTIME_PATHS.txt').read_text().splitlines())
 if (len(b),len(n),len(ch),len(ad),len(b)-len(ch),len(dl))!=(NBASE,NFILES,NCHANGE,NADD,NPROTECTED,0):fail('wrong source counts')
 if ch!=REQUIRED or ad!=ADDED or {k for k in b if n.get(k)!=b[k]}!=ch or set(n)-set(b)!=ad or set(b)-set(n):fail('changed/added allowlist not exhaustive and immutable')
 protected={k:v for k,v in b.items() if k not in ch}
 if protected!=parse(R/'26932_PROTECTED_SOURCE.sha256'):fail('protected source modified')
 for k in ch|ad:
  if '/vendor/' in k or '/jniLibs/' in k or k.endswith(('.so','.jar','.aar')):fail('native/vendor modification prohibited '+k)
 return ch,ad,b,n

def seal():
 ch,ad,b,n=scope()
 files={}
 for l in (R/'26932_HANDOFF_HASHES.sha256').read_text().splitlines():
  h,p=l.split('  ',1)
  if p in files or not (R/p).is_file() or sha(R/p)!=h:fail('sealed staged file missing/tampered '+p)
  files[p]=h
 wf='.github/workflows/build-26932-change-aware.yml';tr='TRIGGER_26932.txt'
 essential=set(STAGE1_FILES)|{wf,tr}|{'handoff_payload_26932/'+k for k in ch|ad}
 if set(files)!=essential:fail('sealed file universe wrong, missing='+str(sorted(essential-files.keys())[:10])+' extra='+str(sorted(files.keys()-essential)[:10]))
 stages=[(R/f'26932_V1_STAGE_{i}_UPLOAD_PATHS.txt').read_text().splitlines() for i in (1,2,3)]
 if stages[1]!=[wf] or stages[2]!=[tr] or stages[0]!=sorted((set(files)|{'26932_HANDOFF_HASHES.sha256'})-{wf,tr}):fail('three-stage upload scope/order incorrect')
 actual={p.relative_to(R/'handoff_payload_26932').as_posix() for p in (R/'handoff_payload_26932').rglob('*') if p.is_file()}
 if actual!=ch|ad:fail('runtime overlay missing or added source')
 for p in ch|ad:
  if sha(R/'handoff_payload_26932'/p)!=n[p]:fail('overlay byte hash mismatch '+p)
 s=(R/wf).read_text()
 for pin in ('verify_26904_v3_safety.py','verify_26904_v2_safety.py','test_26903_v3_archive_receipt.py',
    'test_26931_native_integrity.py --cmake','test_26931_native_integrity.py --apk',
    'build_26931_incremental.py verify-compiled','build_26932_incremental.py fetch',
    'build_26932_incremental.py prepare','compile_26932_shaders.sh',
    'build_26932_incremental.py verify-compiled','build_26932_incremental.py finalize',
    ':app:assembleDebug'):
  if pin not in s:fail('missing historical or real compiler gate '+pin)
 if 'build_26931_incremental.py finalize' in s or s.count('actions/upload-artifact@v4')!=1 or s.count(':app:assembleDebug --stacktrace')!=1:fail('rebuild prior APK or duplicate final publisher')
 subprocess.run(['python3','-S','test_26932_workflow_refs.py']+([] if globals().get('PACKAGE_ONLY') else ['--on-actions']),cwd=R,check=True)
 print('PASS SEALED 26931 successful compiled source 2046 -> 26932 2048; changed 7, new 2, protected 2039')

def fetch():
 seal()
 token=os.getenv('GITHUB_TOKEN','')
 if not token:fail('GitHub Actions token missing')
 if os.getenv('GITHUB_REPOSITORY')!=REPO or os.getenv('GITHUB_REF_NAME')!=BRANCH:fail('branch/repo not approved')
 def gh(path):
  request=urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+path,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'})
  with urllib.request.urlopen(request,timeout=120) as r:return json.load(r)
 run=gh('actions/runs/'+str(RUN));art=gh('actions/artifacts/'+str(ART_ID))
 if run.get('id')!=RUN or run.get('conclusion')!='success' or run.get('head_sha')!=COMMIT or run.get('head_branch')!=BRANCH:fail('not exact successful 26931 GitHub run')
 if art.get('id')!=ART_ID or art.get('expired') or art.get('digest')!='sha256:'+ART_SHA:fail('missing 26931 published artifact')
 TMP.mkdir(exist_ok=True)
 subprocess.run(['curl','--fail','--location','--retry','3','--silent','--show-error',
  '-H','Authorization: Bearer '+token,'-H','Accept: application/vnd.github+json',
  'https://api.github.com/repos/'+REPO+'/actions/artifacts/'+str(ART_ID)+'/zip','-o',str(ART)],check=True)
 if sha(ART)!=ART_SHA:fail('26931 artifact downloaded bytes SHA mismatch')
 print('PASS 26931 run 43624345777 and published artifact 14125593433 sha256 verified')

def safe_tar(path,where):
 with tarfile.open(path,'r:gz') as tar:
  for item in tar:
   name=pathlib.PurePosixPath(item.name)
   if name.is_absolute() or '..' in name.parts or not name.parts or name.parts[0]!='app' or not(item.isfile() or item.isdir()):fail('unsafe source TAR member '+item.name)
  tar.extractall(where,filter='data')

def prepare():
 seal()
 if not ART.is_file() or sha(ART)!=ART_SHA:fail('no exact latest successful 26931 artifact')
 for p in (BASE,CAND):
  if p.exists():shutil.rmtree(p)
 BASE.mkdir(parents=True)
 with zipfile.ZipFile(ART) as zipped:
  def get(n):
   key='photon_26931_outputs/'+n
   if key not in zipped.namelist():fail('latest 26931 artifact missing '+n)
   return zipped.read(key)
  data=get('26931_candidate_app_source.tar.gz')
  if hashlib.sha256(data).hexdigest()!=TAR_SHA:fail('exact source TAR SHA mismatch')
  if get('26931_PREBUILD_SEALED_APP.sha256')!=(R/'26932_BASE_26931_FULL_APP.sha256').read_bytes():fail('26931 compiled full manifest mismatch')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build_26931_incremental.py')).hexdigest()!=BUILDER_SHA or BUILDER_SHA not in get('26931_ACTUAL_EXECUTED_BUILDER.sha256').decode():fail('executed 26931 builder not genuine')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build-26931-change-aware.yml')).hexdigest()!=WORKFLOW_SHA or WORKFLOW_SHA not in get('26931_ACTUAL_EXECUTED_WORKFLOW.sha256').decode():fail('executed 26931 workflow not genuine')
  if PRIOR_APK_SHA not in get('26931_APK.sha256').decode():fail('26931 actual prior APK SHA missing')
  if 'git_sha='+COMMIT not in get('26931_ACTIONS_IDENTITY.txt').decode() or 'github_run_id='+str(RUN) not in get('26931_ACTIONS_IDENTITY.txt').decode():fail('26931 Actions actual source identity not genuine')
  for n in ('26931_LKR_GLES_SPIRV_REAL_COMPILER.txt','26931_GLSL_INHERITED_PARITY.txt','26931_ORIGINAL_LKR_NATIVE_RECEIPT.txt'):
   d=get(n).decode(errors='replace')
   if 'PASS' not in d:fail('26931 compiled shader/native receipt missing '+n)
  for task in (':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',
   ':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',
   ':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',
   ':app:assembleDebug','BUILD SUCCESSFUL'):
   if 'PASS '+task not in get('26931_REAL_GRADLE_TASKS.txt').decode():fail('26931 actual prior compiler did not pass '+task)
  for flag in ('REAL PINNED GLSL COMPILE: PASS','REAL SPIR-V VALIDATION: PASS',
   'REAL KOTLIN COMPILE: PASS','REAL JAVA COMPILE: PASS','NATIVE/NDK COMPILE: PASS',
   'REAL ANDROID Gradle :app:assembleDebug: PASS','RUNTIME SOURCE INVARIANCE: PASS'):
   if flag not in get('26931_COMPILER_STATUS.txt').decode():fail('26931 compiler authority missing '+flag)
  (TMP/'26931_candidate_app_source.tar.gz').write_bytes(data)
 safe_tar(TMP/'26931_candidate_app_source.tar.gz',BASE)
 exact(BASE,'26932_BASE_26931_FULL_APP.sha256','actual 26931 published compiled source')
 shutil.copytree(BASE,CAND)
 ch,ad,_,_=scope()
 for p in sorted(ch|ad):
  src=R/'handoff_payload_26932'/p;dst=CAND/p
  if not src.is_file() or (p in ch and not dst.is_file()) or (p in ad and dst.exists()):fail('runtime overlay misclassified '+p)
  dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
 exact(CAND,'26932_EXPECTED_FULL_APP.sha256','26932 candidate source')
 if not (R/'gradlew').is_file() or not (R/'app/build.gradle').is_file():fail('Android checkout absent')
 if (R/'app/src').exists():shutil.rmtree(R/'app/src')
 shutil.copytree(CAND/'app/src',R/'app/src')
 shutil.copy2(CAND/'app/version.properties',R/'app/version.properties')
 shutil.copy2(CAND/'app/build.gradle',R/'app/build.gradle')
 if (R/'app/.cxx').exists():shutil.rmtree(R/'app/.cxx')
 exact(R,'26932_EXPECTED_FULL_APP.sha256','live 26932 source after authority seed')
 OUT.mkdir(exist_ok=True)
 (OUT/'26932_SOURCE_SCOPE.txt').write_text(f'base=26931 V1 run={RUN} commit={COMMIT} artifact={ART_ID}\n'
  f'ART_SHA={ART_SHA}\nTAR_SHA={TAR_SHA}\nBUILDER_SHA={BUILDER_SHA}\nWORKFLOW_SHA={WORKFLOW_SHA}\nAPK_SHA={PRIOR_APK_SHA}\n'
  f'base={NBASE} current={NFILES} changed={NCHANGE} added={NADD} protected={NPROTECTED} deleted=0\n'
  'B/SR ON single RawLens 3x3 chroma median + B/SR ON only saturation/toe/contrast/white; B/SR OFF only SDR/gainmap rebase\n'
  '\n'.join(sorted(ch|ad))+'\n')
 print('PASS 26932 actual successful artifact candidate-first; no stale checkout or 26931 APK recompile')

def regress():
 seal();exact(R,'26932_EXPECTED_FULL_APP.sha256','live 26932 source')
 for f in ('test_26932_source.py','test_26932_shader_contract.py','test_26932_math.py','test_26932_patch_proof.py'):
  subprocess.run(['python3','-S',f,'--live'],cwd=R,check=True)
 print('PASS B ON/OFF isolated, 3x2 unchanged, HDR quotient, shader reserved tokens, exact rollback')

def verify_compiled():
 regress()
 report=OUT/'26932_REAL_GLSL_SPIRV_COMPILER.txt'
 if not report.is_file():fail('26932 actual real shader compiler report absent')
 text=report.read_text()
 if '16.5.0' not in text or 'PASS current real shader compile' not in text:fail('26932 live GLSL/SPIRV/optimizer failure')
 for label in ('raw_lens_median','lkr_smooth_white','motion_render','motion_gainmap','b_native_final'):
  p=OUT/f'26932_{label}_es310.frag'
  if not p.is_file() or sha(p) not in text:fail('new live shader was not real compiled '+label)
 subprocess.run(['python3','-S','test_26931_native_integrity.py','--native'],cwd=R,check=True)
 (OUT/'26932_PREBUILD_SEALED_APP.sha256').write_bytes((R/'26932_EXPECTED_FULL_APP.sha256').read_bytes())
 print('PASS all actual 26932 active source shader compilers; unchanged original RawLens native SHA locked')

def finalize():
 regress()
 if (OUT/'26932_PREBUILD_SEALED_APP.sha256').read_bytes()!=(R/'26932_EXPECTED_FULL_APP.sha256').read_bytes():fail('source changed after real compile')
 log=(OUT/'26932_gradle_assemble.log').read_text(errors='replace')
 tasks=[':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',
   ':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',
   ':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',
   ':app:assembleDebug','BUILD SUCCESSFUL']
 for task in tasks:
  if task not in log:fail('real NDK/Kotlin/Java/assemble task missing '+task)
 subprocess.run(['python3','-S','test_26931_native_integrity.py','--cmake'],cwd=R,check=True)
 subprocess.run(['python3','-S','verify_26906_native_cache.py','postflight'],cwd=R,check=True)
 apks=list((R/'app/build/outputs/apk').rglob('*.apk'))
 if len(apks)!=1:fail('expected exactly one new APK')
 shutil.copy2(apks[0],R/APKNAME)
 if (R/APKNAME).stat().st_size<1_000_000:fail('new APK implausible')
 subprocess.run(['python3','-S','test_26931_native_integrity.py','--apk'],cwd=R,check=True)
 with zipfile.ZipFile(R/APKNAME) as apk:
  if apk.testzip() is not None:fail('new APK corrupt')
  for n in ('classes.dex','AndroidManifest.xml'):
   if n not in apk.namelist():fail('new APK missing '+n)
 (OUT/'26932_COMPILER_STATUS.txt').write_text('REAL PINNED GLSL COMPILE: PASS (all 26932 changed shaders live)\n'
  'REAL SPIR-V VALIDATION: PASS (all 26932 active GLSL with optimizer and validator)\n'
  'REAL KOTLIN COMPILE: PASS\nREAL JAVA COMPILE: PASS\nNATIVE/NDK COMPILE: PASS (arm64-v8a, armeabi-v7a)\n'
  'REAL ANDROID Gradle :app:assembleDebug: PASS\nORIGINAL RAWLENS LKR NATIVE: PASS (2 ABIs)\n'
  'RUNTIME SOURCE INVARIANCE: PASS\nDEVICE IMAGE QUALITY: NOT RUN\n')
 (OUT/'26932_REAL_GRADLE_TASKS.txt').write_text(''.join('PASS '+t+'\n' for t in tasks))
 (OUT/'26932_APK.sha256').write_text(sha(R/APKNAME)+'  '+APKNAME+'\n')
 wf=R/'.github/workflows/build-26932-change-aware.yml'
 (OUT/'26932_ACTUAL_EXECUTED_BUILDER.sha256').write_text(sha(R/'build_26932_incremental.py')+'  build_26932_incremental.py\n')
 (OUT/'26932_ACTUAL_EXECUTED_WORKFLOW.sha256').write_text(sha(wf)+'  .github/workflows/build-26932-change-aware.yml\n')
 (OUT/'26932_ACTIONS_IDENTITY.txt').write_text('git_sha='+os.getenv('GITHUB_SHA','NOT_IN_ACTIONS')+'\ngithub_run_id='+os.getenv('GITHUB_RUN_ID','NOT_IN_ACTIONS')+'\n')
 for f in ('26932_BASE_26931_FULL_APP.sha256','26932_EXPECTED_FULL_APP.sha256',
   '26932_PROTECTED_SOURCE.sha256','26932_CHANGED_RUNTIME_ALLOWLIST.txt','26932_ADDED_RUNTIME_PATHS.txt',
   '26932_DELETED_RUNTIME_PATHS.txt'):
  shutil.copy2(R/f,OUT/f)
 shutil.copy2(R/'build_26932_incremental.py',OUT/'ACTUAL_EXECUTED_build_26932_incremental.py')
 shutil.copy2(wf,OUT/'ACTUAL_EXECUTED_build-26932-change-aware.yml')
 with (OUT/'26932_candidate_app_source.tar.gz').open('wb') as f:
  with gzip.GzipFile(filename='',mode='wb',compresslevel=1,mtime=0,fileobj=f) as g:
   with tarfile.open(fileobj=g,mode='w') as tar:
    for p in sorted(parse(R/'26932_EXPECTED_FULL_APP.sha256')):
     src=R/p;meta=tar.gettarinfo(str(src),arcname=p);meta.uid=meta.gid=0;meta.uname=meta.gname='';meta.mtime=0
     with src.open('rb') as x:tar.addfile(meta,x)
 (OUT/'26932_candidate_app_source.tar.gz.sha256').write_text(sha(OUT/'26932_candidate_app_source.tar.gz')+'  26932_candidate_app_source.tar.gz\n')
 print('PASS newly assembled ONLY 26932 APK, dual-ABI NDK, original LKR and actual source retained')

if __name__=='__main__':
 try:
  p=argparse.ArgumentParser();p.add_argument('command',choices=('seal','fetch','prepare','regress','verify-compiled','finalize'))
  p.add_argument('--package-only',action='store_true');args=p.parse_args()
  globals()['PACKAGE_ONLY']=args.package_only
  globals()[args.command.replace('-','_')]()
 except Exception as e:
  print(str(e),file=sys.stderr);sys.exit(1)
