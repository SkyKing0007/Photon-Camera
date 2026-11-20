#!/usr/bin/env python3
"""26968 exact successful 26965 compiled authority; early B preview anti-banding, hidden HDR+ chroma UI and +0.30 photo Shadows processing.
Preserve 26965 RAW fusion, reconstruction, denoise, color science, SDR/UHDR, Night, native and vendor source.
Fail closed: exact source + prior artifact + real current shaders, dual ABI NDK, Kotlin/Java, full assembleDebug.
Does not modify dev or commit/push anything.
"""
import argparse,gzip,hashlib,io,json,os,pathlib,re,shutil,subprocess,sys,tarfile,urllib.request,zipfile
R=pathlib.Path(__file__).resolve().parent
TMP=R/'.photon_26968_work';OUT=R/'photon_26968_outputs'
ART=TMP/'26965-success.zip';BASE=TMP/'authority_26965';CAND=TMP/'candidate_26968'
REPO='SkyKing0007/Photon-Camera';BRANCH='experimental-clean-photon-rebuild'
RUN=44594363634;COMMIT='096e5a516f7b83cd1209d4342e002b0dccf3efa5';ART_ID=14564574142
ART_SHA='363d800157dede2f8052cf55526aaccdd82483dbc99aeedc043a55db97ca32c1'
TAR_SHA='fd3a0b7480c8a42a6dbf0b28f1f8f5f953cf456c673b2f97ea528ade6b2f7414'
BUILDER_SHA='755ca41f3fbc214c9286a987801328fc9f2554a73cc89523d1d54be78ea77909'
WORKFLOW_SHA='23c64356dab6c179e1d37344d50e4735df091bfda842b992b54d45e55f76094d'
PRIOR_APK_SHA='c234d9200fbdede8c4cddcf75137c2231ad4248712f198ad8f21ff6e7c7b906d'
PRIOR_APK_NAME='IrisCamera-0.9726965-26965-iris-rawr-debug.apk'
APKNAME='IrisCamera-0.9726968-26968-iris-rawr-debug.apk'
NBASE=NFILES=2055;NCHANGE=6;NADDED=NDELETED=0;NPROTECTED=2049
REQUIRED=set('''
app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26909ShutterIsoMath.java
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java
app/src/main/res/xml/preferences.xml
app/version.properties'''.strip().splitlines())
NATIVE_SHA={
 'lib/arm64-v8a/liblkrpipeline.so':'037a5f62649dcac7034c789c8e7ea2f250ca818d1c1c364e09a59f6897530105',
 'lib/arm64-v8a/libsrpipeline.so':'f87cc70ad12a69345392a4eb73b6ec33739577ce8c39b7a4916180c344f67069',
 'lib/armeabi-v7a/liblkrpipeline.so':'9297eb7c58ca242986bced32bf773dcc8d16c3beaa33c26142b152c585957b03',
 'lib/armeabi-v7a/libsrpipeline.so':'48788035080e66efa63b693e35f0587d2f02e851b818c367f3915b6154b47d68',
}
FILES=['README_PHOTON_26968.md','26968_COMMIT_MESSAGE.txt','26968_LOCAL_VERIFICATION.txt',
 '26965_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml','build_26968_incremental.py',
 'test_26968_source.py','test_26968_flicker_math.py','test_26968_shadows_menu.py',
 'test_26968_patches.py','test_26968_sealed_negatives.py','test_26968_workflow_refs.py',
 'compile_26968_shaders.sh','26968_BASE_26965_FULL_APP.sha256','26968_EXPECTED_FULL_APP.sha256',
 '26968_PROTECTED_SOURCE.sha256','26968_RAWR_LATEST_SOURCE_PROVENANCE.json',
 '26968_BASELINE_AND_SCOPE.json','26968_CHANGED_RUNTIME_ALLOWLIST.txt',
 '26968_ADDED_RUNTIME_PATHS.txt','26968_DELETED_RUNTIME_PATHS.txt',
 '26968_NATIVE_RELEASE_ALLOWLIST.txt','26968_FORWARD_FULLINDEX.patch','26968_ROLLBACK_FULLINDEX.patch',
 '26968_STAGE_1_UPLOAD_PATHS.txt','26968_STAGE_2_UPLOAD_PATHS.txt',
 '26968_STAGE_3_UPLOAD_PATHS.txt','26968_EXPECTED_ACTION_EXECUTABLES.txt']

def fail(s):raise RuntimeError('26968 BLOCKED: '+str(s))
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def parse(p):
 d={}
 for line in p.read_text().splitlines():
  try:h,path=line.split('  ',1)
  except ValueError:fail('invalid manifest '+str(p))
  if not re.fullmatch('[0-9a-f]{64}',h) or not path.startswith('app/') or '..' in pathlib.PurePosixPath(path).parts or path in d:fail('bad or duplicate manifest entry '+path)
  d[path]=h
 return d
def scan(root):
 d={}
 for p in [*(root/'app/src').rglob('*'),root/'app/build.gradle',root/'app/version.properties']:
  if p.is_symlink():fail('symlink in source '+str(p))
  if p.is_file():d[p.relative_to(root).as_posix()]=sha(p)
 return d
def exact(root,manifest,label):
 want=parse(R/manifest);got=scan(root)
 if want!=got:
  missing=sorted(set(want)-set(got));added=sorted(set(got)-set(want));wrong=sorted(x for x in set(want)&set(got) if want[x]!=got[x]);fail(label+f' missing={missing[:3]} added={added[:3]} wrong={wrong[:4]}')
 print('PASS '+label+' '+str(len(got)))
 return got
def scope():
 a=parse(R/'26968_BASE_26965_FULL_APP.sha256');b=parse(R/'26968_EXPECTED_FULL_APP.sha256')
 changed=set((R/'26968_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines());added=set((R/'26968_ADDED_RUNTIME_PATHS.txt').read_text().splitlines());deleted=set((R/'26968_DELETED_RUNTIME_PATHS.txt').read_text().splitlines())
 if (len(a),len(b),len(changed),len(added),len(deleted),len(a)-len(changed))!=(NBASE,NFILES,NCHANGE,NADDED,NDELETED,NPROTECTED):fail('source count change or unauthorized file count')
 if changed!=REQUIRED or added or deleted or set(a)!=set(b) or {p for p in a if a[p]!=b[p]}!=REQUIRED:fail('unexpected runtime source change')
 if parse(R/'26968_PROTECTED_SOURCE.sha256')!={p:h for p,h in a.items() if p not in REQUIRED}:fail('protected hash mismatch')
 source=json.loads((R/'26968_RAWR_LATEST_SOURCE_PROVENANCE.json').read_text())
 if source.get('rawr_github_commit')!='b6c05a0c79ad2430ec8f57d41e643c9a2d0df72b' or source.get('rawr_debug_apk_sha256')!='6a991d6d6693dd499c31596f97eb700a118cca87b9788fd21f6ae4753cb3d30b' or source.get('rawr_motion_gate') != [1.6,2.6] or source.get('rawr_reference_shrink')!=1.0:fail('RAWR latest source anchor changed')
 if a['app/build.gradle']!=b['app/build.gradle']:fail('app/build.gradle not protected')
 if set((R/'26968_NATIVE_RELEASE_ALLOWLIST.txt').read_text().splitlines()) != {'app/build/verified_rawlens26931/jniLibs/'+k.removeprefix('lib/') for k in NATIVE_SHA}:fail('native allowlist changed')
 return changed,a,b

def seal():
 changed,a,b=scope(); sealed={}
 for line in (R/'26968_HANDOFF_HASHES.sha256').read_text().splitlines():
  try:h,p=line.split('  ',1)
  except ValueError:fail('invalid handoff hash list')
  if p in sealed or not (R/p).is_file() or sha(R/p)!=h:fail('missing or altered sealed file '+p)
  sealed[p]=h
 wf='.github/workflows/build-26968-change-aware.yml';trigger='TRIGGER_26968.txt'
 expect=set(FILES)|{wf,trigger}|{'handoff_payload_26968/'+p for p in changed}
 if set(sealed)!=expect:fail('sealed file universe differs '+str(sorted(set(sealed)^expect)[:7]))
 stages=[(R/f'26968_STAGE_{i}_UPLOAD_PATHS.txt').read_text().splitlines() for i in (1,2,3)]
 if stages[0]!=sorted((expect|{'26968_HANDOFF_HASHES.sha256'})-{wf,trigger}) or stages[1]!=[wf] or stages[2]!=[trigger]:fail('three-stage upload ordering')
 payload=R/'handoff_payload_26968'
 if {p.relative_to(payload).as_posix() for p in payload.rglob('*') if p.is_file()} != changed:fail('overlay scope differs')
 if any(sha(payload/p)!=b[p] for p in changed):fail('staged overlay hash differs from frozen candidate')
 if sha(R/'26965_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml')!=WORKFLOW_SHA:fail('last actual executed workflow reference differs')
 subprocess.run([sys.executable,'-S','test_26968_workflow_refs.py'],cwd=R,check=True)
 print('PASS 26968 sealed 2049 protected; B startup HAL anti-banding, retired UI only and photo +0.30 Shadows, native/vendor untouched')

def fetch():
 seal();token=os.getenv('GITHUB_TOKEN','')
 if not token or os.getenv('GITHUB_REPOSITORY')!=REPO or os.getenv('GITHUB_REF_NAME')!=BRANCH:fail('Actions token/branch missing')
 def get(endpoint):
  req=urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+endpoint,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'})
  with urllib.request.urlopen(req,timeout=120) as resp:return json.load(resp)
 run=get('actions/runs/'+str(RUN));artifact=get('actions/artifacts/'+str(ART_ID))
 if run.get('id')!=RUN or run.get('conclusion')!='success' or run.get('head_sha')!=COMMIT or run.get('head_branch')!=BRANCH:fail('successful Actions run identity changed')
 if artifact.get('id')!=ART_ID or artifact.get('expired') or artifact.get('digest')!='sha256:'+ART_SHA or artifact.get('workflow_run',{}).get('id') not in (RUN,None):fail('successful artifact identity changed')
 TMP.mkdir(parents=True,exist_ok=True)
 subprocess.run(['curl','--fail','--location','--retry','3','--silent','--show-error','-H','Authorization: Bearer '+token,'-H','Accept: application/vnd.github+json', 'https://api.github.com/repos/'+REPO+'/actions/artifacts/'+str(ART_ID)+'/zip','-o',str(ART)],check=True)
 if sha(ART)!=ART_SHA:fail('downloaded successful 26965 artifact SHA mismatch')
 print('PASS real successful 26965 published artifact')

def safe_tar(data,root):
 with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as t:
  for m in t:
   p=pathlib.PurePosixPath(m.name)
   if not m.isfile() or not p.parts or p.parts[0]!='app' or p.is_absolute() or '..' in p.parts or m.issym() or m.islnk():fail('unsafe 26965 source tar '+str(p))
  t.extractall(root,filter='data')
def prior_zip():
 if not ART.is_file() or sha(ART)!=ART_SHA:fail('missing exact published successful 26965 ZIP')
 return zipfile.ZipFile(ART)
def prepare_base():
 seal()
 for folder in (BASE,CAND):
  if folder.exists():shutil.rmtree(folder)
 BASE.mkdir(parents=True)
 with prior_zip() as z:
  if z.testzip():fail('26965 predecessor ZIP CRC')
  def get(name):
   p='photon_26965_outputs/'+name
   if p not in z.namelist():fail('prior compiled receipt missing '+p)
   return z.read(p)
  src=get('26965_candidate_app_source.tar.gz')
  if hashlib.sha256(src).hexdigest()!=TAR_SHA or get('26965_candidate_app_source.tar.gz.sha256')!=f'{TAR_SHA}  26965_candidate_app_source.tar.gz\n'.encode():fail('26965 compiled TAR differs')
  before=(R/'26968_BASE_26965_FULL_APP.sha256').read_bytes()
  for name in ('26965_EXPECTED_FULL_APP.sha256','26965_PREBUILD_SEALED_APP.sha256'):
   if get(name)!=before:fail('26965 compiled source manifest mismatch '+name)
  if hashlib.sha256(get('ACTUAL_EXECUTED_build_26965_incremental.py')).hexdigest()!=BUILDER_SHA or BUILDER_SHA not in get('26965_ACTUAL_EXECUTED_BUILDER.sha256').decode():fail('26965 actual builder mismatch')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build-26965-change-aware.yml')).hexdigest()!=WORKFLOW_SHA or WORKFLOW_SHA not in get('26965_ACTUAL_EXECUTED_WORKFLOW.sha256').decode():fail('26965 actual workflow mismatch')
  if PRIOR_APK_NAME not in z.namelist() or PRIOR_APK_SHA not in get('26965_APK.sha256').decode() or hashlib.sha256(z.read(PRIOR_APK_NAME)).hexdigest()!=PRIOR_APK_SHA:fail('26965 actual APK mismatch')
  ident=get('26965_ACTIONS_IDENTITY.txt').decode()
  if 'git_sha='+COMMIT not in ident or 'github_run_id='+str(RUN) not in ident:fail('26965 Actions identity mismatch')
  compiler=get('26965_COMPILER_STATUS.txt').decode()
  for phrase in ('REAL PINNED GLSL COMPILE: PASS','REAL SPIR-V VALIDATION/OPTIMIZATION: PASS','REAL KOTLIN COMPILE: PASS','REAL JAVA COMPILE: PASS','REAL TWO-ABI NDK/CMake COMPILE: PASS','REAL ANDROID Gradle :app:assembleDebug: PASS','RUNTIME SOURCE INVARIANCE: PASS'):
   if phrase not in compiler:fail('26965 predecessor real compiler receipt missing '+phrase)
  for task in (':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL'):
   if 'PASS '+task not in get('26965_REAL_GRADLE_TASKS.txt').decode():fail('26965 real Gradle task receipt missing '+task)
  safe_tar(src,BASE)
 exact(BASE,'26968_BASE_26965_FULL_APP.sha256','last successful 26965 compiled source')
 shutil.copytree(BASE,CAND)
 for rel in sorted(REQUIRED):
  dest=CAND/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/'handoff_payload_26968'/rel,dest)
 exact(CAND,'26968_EXPECTED_FULL_APP.sha256','frozen candidate 26968')
 if not (R/'gradlew').is_file() or not (R/'app/build.gradle').is_file():fail('real checkout Gradle missing')
 if (R/'app/src').exists():shutil.rmtree(R/'app/src')
 shutil.copytree(BASE/'app/src',R/'app/src')
 shutil.copy2(BASE/'app/version.properties',R/'app/version.properties')
 shutil.copy2(BASE/'app/build.gradle',R/'app/build.gradle')
 if (R/'app/.cxx').exists():shutil.rmtree(R/'app/.cxx')
 exact(R,'26968_BASE_26965_FULL_APP.sha256','live actual 26965 for historical source and compiler')
 OUT.mkdir(parents=True,exist_ok=True)
 (OUT/'26968_SOURCE_SCOPE.txt').write_text(f'26965 successful run={RUN} commit={COMMIT} artifact={ART_ID} sha256={ART_SHA} actual compiled tar={TAR_SHA}\nactual builder sha={BUILDER_SHA} workflow sha={WORKFLOW_SHA} APK sha={PRIOR_APK_SHA}\nsource base={NBASE} candidate={NFILES} changes={NCHANGE} protected={NPROTECTED} infrastructure=26968 successor guarded workflow/builder/tests; B HAL AUTO anti-banding until verified period, UI-only HDR+ chroma removal, A/B photo +0.30 Shadows slider-to-processing bias; original 26965 SDR/UHDR retained\n'+''.join(x+'\n' for x in sorted(REQUIRED)))
 print('PASS 26965 compiled authority and isolated 26968 flicker/settings candidate, no stale repo source')

def install():
 seal();exact(R,'26968_BASE_26965_FULL_APP.sha256','preinstall original 26965');exact(CAND,'26968_EXPECTED_FULL_APP.sha256','isolated 26968')
 if not (OUT/'26968_HISTORICAL_SHADER_PROOF.txt').is_file():fail('actual prior shader source compile not completed')
 shutil.rmtree(R/'app/src');shutil.copytree(CAND/'app/src',R/'app/src')
 shutil.copy2(CAND/'app/version.properties',R/'app/version.properties')
 exact(R,'26968_EXPECTED_FULL_APP.sha256','live 26968 after historical shader')
 print('PASS 26968 2049 protected source after install')

def regress():
 seal();exact(R,'26968_EXPECTED_FULL_APP.sha256','live 26968')
 for name in ('test_26968_source.py','test_26968_flicker_math.py','test_26968_shadows_menu.py','test_26968_patches.py'):
  subprocess.run([sys.executable,'-S',name,'--live'],cwd=R,check=True)
 print('PASS 26965 protected RAW/SDR/UHDR, B flicker-safe preview, UI cleanup, A/B photo Shadows bias')

def stage_native():
 seal()
 with prior_zip() as z:
  with zipfile.ZipFile(io.BytesIO(z.read(PRIOR_APK_NAME))) as apk:
   if apk.testzip():fail('actual previous APK CRC failed')
   for path,want in NATIVE_SHA.items():
    raw=apk.read(path)
    if hashlib.sha256(raw).hexdigest()!=want:fail('native LKR binary differs from proven 26965 '+path)
    dest=R/'app/build/verified_rawlens26931/jniLibs'/path.removeprefix('lib/')
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    if sha(dest)!=want:fail('staged native byte mismatch '+path)
 print('PASS exact successful 26965 official LKR dual-ABI 4 binaries')

def verify_compiled():
 regress();receipt=OUT/'26968_REAL_GLSL_SPIRV_COMPILER.txt'
 if not receipt.is_file() or 'PASS actual 26968 current ESSL300/310 + Vulkan 1.1, SPIR-V opt/val' not in receipt.read_text():fail('missing actual new current shader compiler proof')
 for src in ('app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl','app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932RawLensMedian.kt','app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqMerge.comp','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqMismatchNorm.comp'):
  if sha(R/src) not in receipt.read_text():fail('current pinned shader input not compiled '+src)
 for path,want in NATIVE_SHA.items():
  if sha(R/'app/build/verified_rawlens26931/jniLibs'/path.removeprefix('lib/'))!=want:fail('native blob not staged '+path)
 (OUT/'26968_PREBUILD_SEALED_APP.sha256').write_bytes((R/'26968_EXPECTED_FULL_APP.sha256').read_bytes())
 print('PASS current pinned real GLSL SPIR-V and exact dual ABI native staged')

def finalize():
 regress();expected=(R/'26968_EXPECTED_FULL_APP.sha256').read_bytes()
 if (OUT/'26968_PREBUILD_SEALED_APP.sha256').read_bytes()!=expected:fail('actual prebuild source manifest missing')
 log=(OUT/'26968_gradle_assemble.log').read_text(errors='replace')
 tasks=(':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL')
 if any(x not in log for x in tasks):fail('actual real Android compiler/build task not proven')
 subprocess.run([sys.executable,'-S','verify_26906_native_cache.py','postflight'],cwd=R,check=True)
 apks=list((R/'app/build/outputs/apk').rglob('*.apk'))
 if len(apks)!=1:fail('not exactly one actual assembled APK')
 shutil.copy2(apks[0],R/APKNAME)
 if (R/APKNAME).stat().st_size<1_000_000:fail('small or invalid assembled APK')
 with zipfile.ZipFile(R/APKNAME) as apk:
  if apk.testzip() or not {'AndroidManifest.xml','classes.dex'}<=set(apk.namelist()):fail('invalid built APK archive')
  for name,want in NATIVE_SHA.items():
   if hashlib.sha256(apk.read(name)).hexdigest()!=want:fail('native LKR in APK not proven release '+name)
 exact(R,'26968_EXPECTED_FULL_APP.sha256','final exact 26968 compiled candidate')
 (OUT/'26968_COMPILER_STATUS.txt').write_text('REAL PINNED GLSL COMPILE: PASS\nREAL SPIR-V VALIDATION/OPTIMIZATION: PASS\nREAL KOTLIN COMPILE: PASS\nREAL JAVA COMPILE: PASS\nREAL TWO-ABI NDK/CMake COMPILE: PASS\nREAL ANDROID Gradle :app:assembleDebug: PASS\nEXACT SUCCESSFUL 26965 DUAL ABI LKR: PASS\nRUNTIME SOURCE INVARIANCE: PASS (2049 protected)\nDEVICE IQ VALIDATION: NOT RUN\n')
 (OUT/'26968_REAL_GRADLE_TASKS.txt').write_text(''.join('PASS '+x+'\n' for x in tasks))
 (OUT/'26968_APK.sha256').write_text(sha(R/APKNAME)+'  '+APKNAME+'\n')
 wf=R/'.github/workflows/build-26968-change-aware.yml'
 (OUT/'26968_ACTUAL_EXECUTED_BUILDER.sha256').write_text(sha(R/'build_26968_incremental.py')+'  build_26968_incremental.py\n')
 (OUT/'26968_ACTUAL_EXECUTED_WORKFLOW.sha256').write_text(sha(wf)+'  '+wf.relative_to(R).as_posix()+'\n')
 (OUT/'26968_ACTIONS_IDENTITY.txt').write_text('git_sha='+os.getenv('GITHUB_SHA','NOT_IN_ACTIONS')+'\ngithub_run_id='+os.getenv('GITHUB_RUN_ID','NOT_IN_ACTIONS')+'\n')
 for item in ('26968_BASE_26965_FULL_APP.sha256','26968_EXPECTED_FULL_APP.sha256','26968_PROTECTED_SOURCE.sha256','26968_CHANGED_RUNTIME_ALLOWLIST.txt','26968_ADDED_RUNTIME_PATHS.txt','26968_DELETED_RUNTIME_PATHS.txt','26968_NATIVE_RELEASE_ALLOWLIST.txt','26968_RAWR_LATEST_SOURCE_PROVENANCE.json','26968_BASELINE_AND_SCOPE.json'):
  shutil.copy2(R/item,OUT/item)
 shutil.copy2(R/'build_26968_incremental.py',OUT/'ACTUAL_EXECUTED_build_26968_incremental.py')
 shutil.copy2(wf,OUT/'ACTUAL_EXECUTED_build-26968-change-aware.yml')
 with (OUT/'26968_candidate_app_source.tar.gz').open('wb') as f:
  with gzip.GzipFile(filename='',mode='wb',compresslevel=1,mtime=0,fileobj=f) as gz:
   with tarfile.open(fileobj=gz,mode='w') as t:
    for path in sorted(parse(R/'26968_EXPECTED_FULL_APP.sha256')):
     src=R/path;item=t.gettarinfo(str(src),arcname=path);item.uid=item.gid=0;item.uname=item.gname='';item.mtime=0
     with src.open('rb') as opened:t.addfile(item,opened)
 (OUT/'26968_candidate_app_source.tar.gz.sha256').write_text(sha(OUT/'26968_candidate_app_source.tar.gz')+'  26968_candidate_app_source.tar.gz\n')
 print('PASS actual 26968 compiled APK/source TAR, 2049 protected and exact real compiler proof')

if __name__=='__main__':
 try:
  parser=argparse.ArgumentParser();parser.add_argument('command',choices=('seal','fetch','prepare-base','install','regress','stage-native','verify-compiled','finalize'));args=parser.parse_args()
  globals()[args.command.replace('-','_')]()
 except Exception as e:print('26968 BUILD ERROR: '+str(e),file=sys.stderr);sys.exit(1)
