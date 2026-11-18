#!/usr/bin/env python3
"""Photon 26956: exact successful 26955 compiled candidate; B HDR+ Quality matched motion gate.
Keep all successful 26955 historical source/GLSL/NDK/Kotlin/Java/assemble checks and fail closed.
NEVER commit/push source or modify dev.
"""
import argparse,gzip,hashlib,io,json,os,pathlib,re,shutil,subprocess,sys,tarfile,urllib.request,zipfile
R=pathlib.Path(__file__).resolve().parent
TMP=R/'.photon_26956_work';OUT=R/'photon_26956_outputs'
ART=TMP/'26955-success.zip';BASE=TMP/'authority_26955';CAND=TMP/'candidate_26956'
REPO='SkyKing0007/Photon-Camera';BRANCH='experimental-clean-photon-rebuild'
RUN=44218679793;COMMIT='1dde0be73f42dbaf550f460f6de317afc59e0027';ART_ID=14389263287
ART_SHA='2bbf92a5c1733d5b417d0cc3e4b1b093fe1e7a34b5f31a872cc8955062e076a9'
TAR_SHA='6e0aae0e9b8003176f9b94cfd9ca71945702f663609a636648eca59f09db567b'
BUILDER_SHA='7246b9d0c522481a4aa600b7435a8bcd9ca51f251e4ab500cdc054ad5317a23e'
WORKFLOW_SHA='c8821ea4988680fc362b175d68c0b09669da86a7cbf2011fb9d3de8e7aa29c89'
PRIOR_APK_SHA='55003f86b5043fea4479f961f99ffc07d2fc52be17ceeaa9decca8c7b67e7d3d'
PRIOR_APK_NAME='IrisCamera-0.9726955-26955-iris-rawr-debug.apk'
APKNAME='IrisCamera-0.9726956-26956-iris-rawr-debug.apk'
NBASE=NFILES=2055;NCHANGE=8;NADDED=NDELETED=0;NPROTECTED=2047
REQUIRED={
 'app/src/main/cpp/iris26864/Iris26864RealRawrCoordinator.cpp',
 'app/src/main/cpp/iris26864/bridge/Iris26888BOffVulkanExecutor.cpp',
 'app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqMismatch.comp',
 'app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqPrivateHeader.hpp',
 'app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqRecorder.cpp',
 'app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqMerge.comp',
 'app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqCoordinator.cpp',
 'app/version.properties',
}

ADDED=set()
NATIVE_ALLOW={f'app/build/verified_rawlens26931/jniLibs/{abi}/{name}'
  for abi in ('arm64-v8a','armeabi-v7a') for name in ('liblkrpipeline.so','libsrpipeline.so')}
STAGE1_FILES=[
 'README_PHOTON_26956.md','26956_COMMIT_MESSAGE.txt','26956_LOCAL_VERIFICATION.txt',
 '26955_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml',
 'build_26956_incremental.py','prepare_26956_native.py','test_26956_native.py',
 'test_26956_source.py','test_26956_tone_math.py','test_26956_motion.py','test_26956_patches.py',
 'test_26956_sealed_negatives.py','test_26956_workflow_refs.py','compile_26956_shaders.sh',
 '26956_BASE_26955_FULL_APP.sha256','26956_EXPECTED_FULL_APP.sha256',
 '26956_PROTECTED_SOURCE.sha256','26956_CHANGED_RUNTIME_ALLOWLIST.txt',
 '26956_ADDED_RUNTIME_PATHS.txt','26956_DELETED_RUNTIME_PATHS.txt',
 '26956_NATIVE_RELEASE_ALLOWLIST.txt','26956_FORWARD_FULLINDEX.patch',
 '26956_ROLLBACK_FULLINDEX.patch','26956_STAGE_1_UPLOAD_PATHS.txt',
 '26956_STAGE_2_UPLOAD_PATHS.txt','26956_STAGE_3_UPLOAD_PATHS.txt',
 '26956_EXPECTED_ACTION_EXECUTABLES.txt'
]

def fail(s):raise RuntimeError('26956 BLOCKED: '+str(s))
def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for buf in iter(lambda:f.read(4*1024*1024),b''):h.update(buf)
 return h.hexdigest()
def parse(path):
 d={}
 for line in path.read_text().splitlines():
  try:h,p=line.split('  ',1)
  except ValueError:fail('invalid SHA256 list '+str(path))
  if not re.fullmatch('[0-9a-f]{64}',h) or not p.startswith('app/') or '..' in pathlib.PurePosixPath(p).parts or p in d:fail('invalid SHA entry '+p)
  d[p]=h
 return d
def scan(root):
 d={}
 for p in [*(root/'app/src').rglob('*'),root/'app/build.gradle',root/'app/version.properties']:
  if p.is_symlink():fail('symlink in app source '+str(p))
  if p.is_file():d[p.relative_to(root).as_posix()]=sha(p)
 return d
def exact(root,manifest,label):
 want=parse(R/manifest);got=scan(root)
 if want!=got:
  missing=sorted(set(want)-set(got));added=sorted(set(got)-set(want))
  wrong=sorted(p for p in got.keys()&want.keys() if got[p]!=want[p]);fail(f'{label} missing={missing[:4]} added={added[:4]} wrong={wrong[:4]}')
 print('PASS '+label+' '+str(len(got)));return got
def scope():
 old=parse(R/'26956_BASE_26955_FULL_APP.sha256');new=parse(R/'26956_EXPECTED_FULL_APP.sha256')
 changed=set((R/'26956_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines());added=set((R/'26956_ADDED_RUNTIME_PATHS.txt').read_text().splitlines());deleted=set((R/'26956_DELETED_RUNTIME_PATHS.txt').read_text().splitlines())
 if (len(old),len(new),len(changed),len(added),len(deleted),len(old)-len(changed))!=(NBASE,NFILES,NCHANGE,NADDED,NDELETED,NPROTECTED):fail('wrong protected/changed source counts')
 if changed!=REQUIRED or added!=ADDED or deleted or set(new)!=set(old) or {p for p in old if new[p]!=old[p]}!=REQUIRED:fail('source allowlist differs from eight B HDRQ-native-only paths')
 if parse(R/'26956_PROTECTED_SOURCE.sha256')!={p:h for p,h in old.items() if p not in REQUIRED}:fail('changed protected source manifest')
 if set((R/'26956_NATIVE_RELEASE_ALLOWLIST.txt').read_text().splitlines())!=NATIVE_ALLOW:fail('external JNI native integrity list changed')
 if old['app/build.gradle']!=new['app/build.gradle']:fail('app Gradle source changed')
 for p in changed:
  if '/vendor/' in p or '/jniLibs/' in p or p.endswith(('.so','.aar','.jar','.spv')):fail('sealed vendor/native binary protection violated')
 return changed,added,old,new

def seal():
 for name in ('ART_SHA','TAR_SHA','BUILDER_SHA','WORKFLOW_SHA','PRIOR_APK_SHA'):
  if not re.fullmatch('[0-9a-f]{64}',globals()[name]):fail('invalid predecessor authority hash '+name)
 changed,added,old,new=scope();sealed={}
 for line in (R/'26956_HANDOFF_HASHES.sha256').read_text().splitlines():
  try:h,p=line.split('  ',1)
  except ValueError:fail('bad sealed file list')
  if p in sealed or not (R/p).is_file() or sha(R/p)!=h:fail('missing/tampered sealed file '+p)
  sealed[p]=h
 wf='.github/workflows/build-26956-change-aware.yml';trigger='TRIGGER_26956.txt'
 want=set(STAGE1_FILES)|{wf,trigger}|{'handoff_payload_26956/'+p for p in changed|added}
 if set(sealed)!=want:fail('sealed universe missing/unused '+str(sorted(set(sealed)^want)[:8]))
 stages=[(R/f'26956_STAGE_{i}_UPLOAD_PATHS.txt').read_text().splitlines() for i in (1,2,3)]
 if stages[0]!=sorted((want|{'26956_HANDOFF_HASHES.sha256'})-{wf,trigger}) or stages[1]!=[wf] or stages[2]!=[trigger]:fail('three-stage manifest invalid')
 root=R/'handoff_payload_26956'
 paths={x.relative_to(root).as_posix() for x in root.rglob('*') if x.is_file()}
 if paths!=changed|added or any(sha(root/p)!=new[p] for p in paths):fail('source overlay not exact')
 if sha(R/'26955_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml')!=WORKFLOW_SHA:fail('compiled authority workflow reference changed')
 subprocess.run([sys.executable,'-S','test_26956_workflow_refs.py'],cwd=R,check=True)
 print('PASS complete 26956 3-stage seal + latest 26955 source, 2047 protected')

def fetch():
 seal();token=os.getenv('GITHUB_TOKEN','')
 if not token or os.getenv('GITHUB_REPOSITORY')!=REPO or os.getenv('GITHUB_REF_NAME')!=BRANCH:fail('Actions token or branch unavailable')
 def get(endpoint):
  req=urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+endpoint,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'})
  with urllib.request.urlopen(req,timeout=120) as res:return json.load(res)
 run=get('actions/runs/'+str(RUN));artifact=get('actions/artifacts/'+str(ART_ID))
 if run.get('id')!=RUN or run.get('conclusion')!='success' or run.get('head_sha')!=COMMIT or run.get('head_branch')!=BRANCH:fail('actual last successful 26955 run mismatch')
 if artifact.get('id')!=ART_ID or artifact.get('expired') or artifact.get('digest')!='sha256:'+ART_SHA or artifact.get('workflow_run',{}).get('id') not in (RUN,None):fail('actual last successful 26955 artifact mismatch')
 TMP.mkdir(parents=True,exist_ok=True)
 # EXACT cross-host artifact download command that succeeded in 26951 and 26955 successful.
 subprocess.run(['curl','--fail','--location','--retry','3','--silent','--show-error',
  '-H','Authorization: Bearer '+token,'-H','Accept: application/vnd.github+json',
  'https://api.github.com/repos/'+REPO+'/actions/artifacts/'+str(ART_ID)+'/zip','-o',str(ART)],check=True)
 if sha(ART)!=ART_SHA:fail('downloaded successful 26955 artifact SHA mismatch')
 print('PASS last successful published 26955 artifact sha256='+ART_SHA)

def safe_tar(data,root):
 with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as t:
  for m in t:
   p=pathlib.PurePosixPath(m.name)
   if not m.isfile() or not p.parts or p.parts[0]!='app' or p.is_absolute() or '..' in p.parts or m.issym() or m.islnk():fail('unsafe latest source TAR '+str(p))
  t.extractall(root,filter='data')
def prior_zip():
 if not ART.is_file() or sha(ART)!=ART_SHA:fail('exact successful 26955 published ZIP not available')
 return zipfile.ZipFile(ART)

def prepare_base():
 seal()
 for folder in (BASE,CAND):
  if folder.exists():shutil.rmtree(folder)
 BASE.mkdir(parents=True)
 with prior_zip() as z:
  if z.testzip():fail('prior ZIP CRC')
  def get(name):
   k='photon_26955_outputs/'+name
   if k not in z.namelist():fail('last successful 26955 receipt missing '+k)
   return z.read(k)
  data=get('26955_candidate_app_source.tar.gz')
  if hashlib.sha256(data).hexdigest()!=TAR_SHA or get('26955_candidate_app_source.tar.gz.sha256')!=f'{TAR_SHA}  26955_candidate_app_source.tar.gz\n'.encode():fail('actual 26955 compiled TAR wrong')
  before=(R/'26956_BASE_26955_FULL_APP.sha256').read_bytes()
  for name in ('26955_EXPECTED_FULL_APP.sha256','26955_PREBUILD_SEALED_APP.sha256'):
   if get(name)!=before:fail('successful source manifest not compiled candidate '+name)
  if hashlib.sha256(get('ACTUAL_EXECUTED_build_26955_incremental.py')).hexdigest()!=BUILDER_SHA or BUILDER_SHA not in get('26955_ACTUAL_EXECUTED_BUILDER.sha256').decode():fail('actually executed 26955 builder wrong')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build-26955-change-aware.yml')).hexdigest()!=WORKFLOW_SHA or WORKFLOW_SHA not in get('26955_ACTUAL_EXECUTED_WORKFLOW.sha256').decode():fail('actually executed 26955 workflow wrong')
  if PRIOR_APK_NAME not in z.namelist() or PRIOR_APK_SHA not in get('26955_APK.sha256').decode() or hashlib.sha256(z.read(PRIOR_APK_NAME)).hexdigest()!=PRIOR_APK_SHA:fail('published 26955 compiled APK SHA wrong')
  ident=get('26955_ACTIONS_IDENTITY.txt').decode()
  if 'git_sha='+COMMIT not in ident or 'github_run_id='+str(RUN) not in ident:fail('last 26955 Actions runtime identity changed')
  compiler=get('26955_COMPILER_STATUS.txt').decode()
  for phrase in ('REAL PINNED GLSL COMPILE: PASS','REAL SPIR-V VALIDATION/OPTIMIZATION: PASS','REAL KOTLIN COMPILE: PASS','REAL JAVA COMPILE: PASS','REAL TWO-ABI NDK/CMake COMPILE: PASS','REAL ANDROID Gradle :app:assembleDebug: PASS','RUNTIME SOURCE INVARIANCE: PASS'):
   if phrase not in compiler:fail('26955 successful predecessor compiler proof incomplete '+phrase)
  for task in (':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL'):
   if 'PASS '+task not in get('26955_REAL_GRADLE_TASKS.txt').decode():fail('last predecessor Gradle task missing '+task)
  safe_tar(data,BASE)
 exact(BASE,'26956_BASE_26955_FULL_APP.sha256','last successful compiled 26955 original')
 shutil.copytree(BASE,CAND)
 for p in sorted(REQUIRED):
  src=R/'handoff_payload_26956'/p;dst=CAND/p
  dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
 exact(CAND,'26956_EXPECTED_FULL_APP.sha256','candidate-first current 26956')
 if not (R/'gradlew').is_file() or not (R/'app/build.gradle').is_file():fail('real Actions Gradle checkout unavailable')
 if (R/'app/src').exists():shutil.rmtree(R/'app/src')
 shutil.copytree(BASE/'app/src',R/'app/src')
 shutil.copy2(BASE/'app/version.properties',R/'app/version.properties')
 shutil.copy2(BASE/'app/build.gradle',R/'app/build.gradle')
 if (R/'app/.cxx').exists():shutil.rmtree(R/'app/.cxx')
 exact(R,'26956_BASE_26955_FULL_APP.sha256','live original 26955 for full historical GLSL execution')
 OUT.mkdir(parents=True,exist_ok=True)
 (OUT/'26956_SOURCE_SCOPE.txt').write_text(f'LATEST SUCCESSFUL 26955 Actions run={RUN} commit={COMMIT} artifact={ART_ID} artifact_sha={ART_SHA} actual compiled TAR sha={TAR_SHA}\n26955 builder_sha={BUILDER_SHA} workflow_sha={WORKFLOW_SHA} apk_sha={PRIOR_APK_SHA}\nsource base={NBASE} current={NFILES} changed={NCHANGE} added={NADDED} protected={NPROTECTED}, 0 changed native vendor binaries; 7 changed native bridge source files, 4 exact same released LK-R native binaries\n'+''.join(x+'\n' for x in sorted(REQUIRED)))
 print('PASS latest successful 26955 seed and 26956 isolated candidate; no old build reconstructed')

def install():
 seal();exact(R,'26956_BASE_26955_FULL_APP.sha256','pre-install exact 26955 live')
 exact(CAND,'26956_EXPECTED_FULL_APP.sha256','pre-install isolated 26956 candidate')
 if not (OUT/'26956_HISTORICAL_SHADER_PROOF.txt').is_file():fail('real pinned predecessor current 26955 GLSL historical compilation not completed')
 shutil.rmtree(R/'app/src');shutil.copytree(CAND/'app/src',R/'app/src')
 shutil.copy2(CAND/'app/version.properties',R/'app/version.properties')
 exact(R,'26956_EXPECTED_FULL_APP.sha256','installed current 26956 after historical shader proof')
 print('PASS 2047 protected, eight exact B HDRQ-only native bridge/source paths installed')

def regress():
 seal();exact(R,'26956_EXPECTED_FULL_APP.sha256','live 26956 source full universe')
 for script in ('test_26956_source.py','test_26956_tone_math.py','test_26956_motion.py','test_26956_patches.py'):
  subprocess.run([sys.executable,'-S',script,'--live'],cwd=R,check=True)
 print('PASS matched native HDRQ B OFF/Night gate, protected +0.4EV and SR ON, exact rollback')

def verify_compiled():
 regress();p=OUT/'26956_REAL_GLSL_SPIRV_COMPILER.txt'
 if not p.is_file() or 'PASS actual 26956 current ESSL300/310 + Vulkan 1.1, SPIR-V opt/val' not in p.read_text():fail('genuine 26956 shader compile missing')
 actual=p.read_text()
 for source in ('app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl'):
  if sha(R/source) not in actual:fail('protected shader not in real glslang compile receipt '+source)
 for source in ('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932RawLensMedian.kt','app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqMerge.comp','app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqMismatch.comp'):
  if sha(R/source) not in actual:fail('active Vulkan/LKR shader actual compiler missing '+source)
 subprocess.run([sys.executable,'-S','test_26956_native.py','--native'],cwd=R,check=True)
 (OUT/'26956_PREBUILD_SEALED_APP.sha256').write_bytes((R/'26956_EXPECTED_FULL_APP.sha256').read_bytes())
 print('PASS mandatory real GLSL/SPIR-V, source ABI, original compiled native and 2047 protected')

def finalize():
 regress();expected=(R/'26956_EXPECTED_FULL_APP.sha256').read_bytes()
 if (OUT/'26956_PREBUILD_SEALED_APP.sha256').read_bytes()!=expected:fail('missing actual prebuild full source proof')
 log=(OUT/'26956_gradle_assemble.log').read_text(errors='replace')
 tasks=(':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL')
 for task in tasks:
  if task not in log:fail('actual Android Gradle task not present '+task)
 subprocess.run([sys.executable,'-S','test_26956_native.py','--cmake'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','verify_26906_native_cache.py','postflight'],cwd=R,check=True)
 apks=list((R/'app/build/outputs/apk').rglob('*.apk'))
 if len(apks)!=1:fail('expected exactly one real assembled APK')
 shutil.copy2(apks[0],R/APKNAME)
 if (R/APKNAME).stat().st_size<1000000:fail('real assembled APK size wrong')
 subprocess.run([sys.executable,'-S','test_26956_native.py','--apk'],cwd=R,check=True)
 with zipfile.ZipFile(R/APKNAME) as z:
  if z.testzip() or not {'AndroidManifest.xml','classes.dex'}<=set(z.namelist()):fail('actual APK invalid')
 exact(R,'26956_EXPECTED_FULL_APP.sha256','final exact source authority after compilation')
 (OUT/'26956_COMPILER_STATUS.txt').write_text('REAL PINNED GLSL COMPILE: PASS (historical 26955 successful + new 26956 current ESSL300/310/Vulkan)\nREAL SPIR-V VALIDATION/OPTIMIZATION: PASS\nREAL KOTLIN COMPILE: PASS\nREAL JAVA COMPILE: PASS\nREAL TWO-ABI NDK/CMake COMPILE: PASS\nREAL ANDROID Gradle :app:assembleDebug: PASS\nEXACT SUCCESSFUL 26955 DUAL ABI LKR: PASS\nRUNTIME SOURCE INVARIANCE: PASS (2047 protected)\nDEVICE HDR VISUAL PARITY: NOT RUN\n')
 (OUT/'26956_REAL_GRADLE_TASKS.txt').write_text(''.join('PASS '+t+'\n' for t in tasks))
 (OUT/'26956_APK.sha256').write_text(sha(R/APKNAME)+'  '+APKNAME+'\n')
 wf=R/'.github/workflows/build-26956-change-aware.yml'
 (OUT/'26956_ACTUAL_EXECUTED_BUILDER.sha256').write_text(sha(R/'build_26956_incremental.py')+'  build_26956_incremental.py\n')
 (OUT/'26956_ACTUAL_EXECUTED_WORKFLOW.sha256').write_text(sha(wf)+'  '+wf.relative_to(R).as_posix()+'\n')
 (OUT/'26956_ACTIONS_IDENTITY.txt').write_text('git_sha='+os.getenv('GITHUB_SHA','NOT_IN_ACTIONS')+'\ngithub_run_id='+os.getenv('GITHUB_RUN_ID','NOT_IN_ACTIONS')+'\n')
 for p in ('26956_BASE_26955_FULL_APP.sha256','26956_EXPECTED_FULL_APP.sha256','26956_PROTECTED_SOURCE.sha256','26956_CHANGED_RUNTIME_ALLOWLIST.txt','26956_ADDED_RUNTIME_PATHS.txt','26956_DELETED_RUNTIME_PATHS.txt','26956_NATIVE_RELEASE_ALLOWLIST.txt'):
  shutil.copy2(R/p,OUT/p)
 shutil.copy2(R/'build_26956_incremental.py',OUT/'ACTUAL_EXECUTED_build_26956_incremental.py')
 shutil.copy2(wf,OUT/'ACTUAL_EXECUTED_build-26956-change-aware.yml')
 with (OUT/'26956_candidate_app_source.tar.gz').open('wb') as f:
  with gzip.GzipFile(filename='',mode='wb',compresslevel=1,mtime=0,fileobj=f) as gz:
   with tarfile.open(fileobj=gz,mode='w') as t:
    for p in sorted(parse(R/'26956_EXPECTED_FULL_APP.sha256')):
     s=R/p;m=t.gettarinfo(str(s),arcname=p);m.uid=m.gid=0;m.uname=m.gname='';m.mtime=0
     with s.open('rb') as opened:t.addfile(m,opened)
 (OUT/'26956_candidate_app_source.tar.gz.sha256').write_text(sha(OUT/'26956_candidate_app_source.tar.gz')+'  26956_candidate_app_source.tar.gz\n')
 print('PASS actual 26956 assembled APK, 2047 protected, official original LK-R unchanged and exact compiled TAR')

if __name__=='__main__':
 try:
  parser=argparse.ArgumentParser();parser.add_argument('command',choices=('seal','fetch','prepare-base','install','regress','verify-compiled','finalize'));args=parser.parse_args()
  globals()[args.command.replace('-','_')]()
 except Exception as e:print('26956 BUILD ERROR: '+str(e),file=sys.stderr);sys.exit(1)
