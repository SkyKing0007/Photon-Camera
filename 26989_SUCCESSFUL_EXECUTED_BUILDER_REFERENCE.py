#!/usr/bin/env python3
"""26989 guarded successor to successful 26988 V2. C Motion native RAW ownership and C ON newest highlights, HDR OFF; real compiler gates retained."""
import argparse,gzip,hashlib,io,json,os,pathlib,re,shutil,subprocess,sys,tarfile,urllib.request,zipfile
R=pathlib.Path(__file__).resolve().parent
SHADER_COUNT=299 # exact current 26989 physical required shader inventory; not skip
TMP=R/'.photon_26989_work';OUT=R/'photon_26989_outputs'
ART=TMP/'26988-success.zip';BASE=TMP/'authority_26988';CAND=TMP/'candidate_26989'
REPO='SkyKing0007/Photon-Camera';BRANCH='experimental-clean-photon-rebuild'
RUN=45729853266;COMMIT='6b66aad8266ad6d993ab92d5a3fa44f716029167';ART_ID=15077480661
ART_SHA='0296c6e2cec6564af47834960eec05f06f077148d244b5a6010fcf9c1096bc45'
TAR_SHA='ed59b3b62cca9ef07188441ff966a0bb2bd9ceb63b0e9fd5534ed989c6535052'
BUILDER_SHA='5dabaa81e9929723f4918fc746e6664ac7cf5d779fa5f7d6333cca4439f968b3'
WORKFLOW_SHA='662c8f19906d319ee88992bd2fdcf2f81bd94df69e67f1cd5974abb7d209c3d0'
PRIOR_APK_SHA='72c71ad76d3114e16636f01bd186953bbe015132d7fb17b02bab447c706ec9be'
PRIOR_APK_NAME='IrisCamera-0.9726988-26988-iris-rawr-debug.apk'
APKNAME='IrisCamera-0.9726989-26989-iris-rawr-debug.apk'
NBASE=2659;NFILES=2660;NCHANGE=11;NADDED=1;NMODIFIED=10;NDELETED=0;NPROTECTED=2649
NATIVE_SHA={
 'lib/arm64-v8a/liblkrpipeline.so':'037a5f62649dcac7034c789c8e7ea2f250ca818d1c1c364e09a59f6897530105',
 'lib/arm64-v8a/libsrpipeline.so':'f87cc70ad12a69345392a4eb73b6ec33739577ce8c39b7a4916180c344f67069',
 'lib/armeabi-v7a/liblkrpipeline.so':'9297eb7c58ca242986bced32bf773dcc8d16c3beaa33c26142b152c585957b03',
 'lib/armeabi-v7a/libsrpipeline.so':'48788035080e66efa63b693e35f0587d2f02e851b818c367f3915b6154b47d68',
}
DONOR_SHA={
 'lib/arm64-v8a/libiris26972c129.so':'a70ba1b1e4e8c856b07c828bef4141d0097d19013a49f77c1f59e41ee0a52cae',
 'lib/arm64-v8a/libi72.so':'ab0698a4a7006564e22447402468a9e1ca349a9017180bc7767c4feec58e0331',
}
FILES=['26988_SUCCESSFUL_EXECUTED_BUILDER_REFERENCE.py', '26988_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml', '26989_ADDED_RUNTIME_PATHS.txt', '26989_AUTHORITY_AND_SCOPE.json', '26989_BASE_26988_FULL_APP.sha256', '26989_CHANGED_RUNTIME_ALLOWLIST.txt', '26989_COMMIT_MESSAGE.txt', '26989_CON_SHADER_INVENTORY.json', '26989_DELETED_RUNTIME_PATHS.txt', '26989_EXPECTED_FULL_APP.sha256', '26989_FORWARD_FULLINDEX.patch', '26989_MODIFIED_ORIGINAL_PATHS.txt', '26989_NATIVE_SHADER_INVENTORY.json', '26989_PROTECTED_SOURCE.sha256', '26989_ROLLBACK_FULLINDEX.patch', '26989_STAGE_1_UPLOAD_PATHS.txt', '26989_STAGE_2_UPLOAD_PATHS.txt', '26989_STAGE_3_UPLOAD_PATHS.txt', '26989_V6_CURRENT_SHADER_INVENTORY.json', '26989_post_copy_records.json', 'README_PHOTON_26989.md', 'build_26989_incremental.py', 'compile_26989_con_shaders.sh', 'compile_26989_shaders.sh', 'test_26989_highlight_host.py', 'test_26989_latest_preflight.py', 'test_26989_patches.py', 'test_26989_raw_memory_host.py', 'test_26989_sealed_negatives.py', 'test_26989_source.py', 'test_26989_workflow_refs.py', 'verify_26989_con_glsl.py', 'verify_26989_native_glsl.py', 'verify_26989_preview_glsl.py', 'verify_26989_v6_current_glsl.py']
ALLOWED_MODIFIED=['app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_adapter.cpp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_finish.cpp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_full.cpp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_jni.cpp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_solver.cpp', 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26983COnLkrBridge.java', 'app/src/main/java/com/hinnka/mycamera/processor/Iris26972CCamera2ShutterSession.kt', 'app/src/main/java/com/hinnka/mycamera/processor/Iris26972CPhysicalRawSpool.kt', 'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java', 'app/version.properties']
ALLOWED_ADDED=['app/src/main/java/com/hinnka/mycamera/processor/Iris26989CRawMemory.kt']

def fail(msg):raise RuntimeError('26989 BLOCKED: '+str(msg))
def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def parse(path):
 d={}
 for line in path.read_text().splitlines():
  try:h,p=line.split('  ',1)
  except ValueError:fail('bad manifest '+str(path))
  if not re.fullmatch('[0-9a-f]{64}',h) or not p.startswith('app/') or '..' in pathlib.PurePosixPath(p).parts or p in d:fail('malformed/duplicate manifest '+p)
  d[p]=h
 return d
def scan(root):
 src=root/'app/src';required=[root/'app/build.gradle',root/'app/version.properties']
 if not src.is_dir() or not all(x.is_file() for x in required):fail('missing complete app/source/Gradle '+str(root))
 d={}
 for p in [*src.rglob('*'),*required]:
  if p.is_symlink():fail('source symlink '+str(p))
  if p.is_file():d[p.relative_to(root).as_posix()]=sha(p)
 return d
def exact(root,file,label):
 want=parse(R/file);got=scan(root)
 if got!=want:fail(label+f' missing={sorted(set(want)-set(got))[:8]} extra={sorted(set(got)-set(want))[:8]} mismatched={[p for p in want.keys()&got.keys() if want[p]!=got[p]][:8]}')
 print('PASS '+label+f': {len(got)} physical files')
 return got

def scope():
 a=parse(R/'26989_BASE_26988_FULL_APP.sha256');b=parse(R/'26989_EXPECTED_FULL_APP.sha256')
 changed=set((R/'26989_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
 added=set((R/'26989_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
 modified=set((R/'26989_MODIFIED_ORIGINAL_PATHS.txt').read_text().splitlines())
 deleted=set((R/'26989_DELETED_RUNTIME_PATHS.txt').read_text().splitlines())
 if (len(a),len(b),len(changed),len(added),len(modified),len(deleted))!=(NBASE,NFILES,NCHANGE,NADDED,NMODIFIED,NDELETED):fail('count/protected source regression')
 if changed!=added|modified or added&set(a) or modified-set(a) or set(b)!=(set(a)|added) or deleted:fail('unexpected runtime change/deletion')
 if {p for p in set(a)&set(b) if a[p]!=b[p]}!=modified:fail('original source edits outside allowlist')
 protected={p:h for p,h in a.items() if p not in changed}
 if len(protected)!=NPROTECTED or protected!=parse(R/'26989_PROTECTED_SOURCE.sha256'):fail('protected source failed')
 if sha(R/'26988_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml')!=WORKFLOW_SHA or sha(R/'26988_SUCCESSFUL_EXECUTED_BUILDER_REFERENCE.py')!=BUILDER_SHA:fail('26988 actual executed reference changed')
 if (R/'handoff_payload_26989/app/version.properties').read_text()!='VERSION_MAJOR=0\nVERSION_MINOR=9726440\nVERSION_NAME=0.9726989\nVERSION_BUILD=26989\n':fail('26989 version not exact')
 allowed_modified=set(json.loads((R/'26989_AUTHORITY_AND_SCOPE.json').read_text())['allowed_modified_exact'])
 if allowed_modified!=modified:fail('changed original paths not explicit')
 if modified!=set(ALLOWED_MODIFIED) or added!=set(ALLOWED_ADDED):fail('new scope not exact')
 if a['app/src/main/java/com/particlesdevs/photoncamera/util/SimpleStorageHelper.java']!=b['app/src/main/java/com/particlesdevs/photoncamera/util/SimpleStorageHelper.java']:fail('A/B gallery changed')
 return changed,a,b

def seal():
 changed,a,b=scope();wf='.github/workflows/build-26989-change-aware.yml';trigger='TRIGGER_26989.txt'
 expect=set(FILES)|{wf,trigger}|{'handoff_payload_26989/'+p for p in changed}
 sealed={}
 for line in (R/'26989_HANDOFF_HASHES.sha256').read_text().splitlines():
  try:h,p=line.split('  ',1)
  except ValueError:fail('bad handoff hash seal')
  if p in sealed or not (R/p).is_file() or sha(R/p)!=h:fail('missing/tampered handoff file '+p)
  sealed[p]=h
 if set(sealed)!=expect:fail('missing/extra handoff file set '+str(sorted(set(sealed)^expect)[:10]))
 stages=[(R/f'26989_STAGE_{i}_UPLOAD_PATHS.txt').read_text().splitlines() for i in (1,2,3)]
 if stages[0]!=sorted((expect|{'26989_HANDOFF_HASHES.sha256'})-{wf,trigger}) or stages[1]!=[wf] or stages[2]!=[trigger]:fail('three upload stages not strict')
 payload=R/'handoff_payload_26989'
 if {p.relative_to(payload).as_posix() for p in payload.rglob('*') if p.is_file()}!=changed:fail('payload missing/extra')
 for p in changed:
  if sha(payload/p)!=b[p]:fail('source input tampering '+p)
 if sha(R/'.github/workflows/build-26989-change-aware.yml')!=sealed[wf]:fail('workflow after seal changed')
 subprocess.run([sys.executable,'-S','test_26989_workflow_refs.py'],cwd=R,check=True)
 print(f'PASS 26989 three-stage SHA seal, {NPROTECTED} protected, {NCHANGE} source delta')

def fetch():
 seal();token=os.getenv('GITHUB_TOKEN','')
 if not token or os.getenv('GITHUB_REPOSITORY')!=REPO or os.getenv('GITHUB_REF_NAME')!=BRANCH:fail('Actions credentials/target branch unavailable')
 def get(endpoint):
  req=urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+endpoint,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'})
  with urllib.request.urlopen(req,timeout=120) as resp:return json.load(resp)
 run=get('actions/runs/'+str(RUN));art=get('actions/artifacts/'+str(ART_ID))
 if run.get('id')!=RUN or run.get('conclusion')!='success' or run.get('head_sha')!=COMMIT or run.get('head_branch')!=BRANCH:fail('26988 Actions run not successful/exact')
 if art.get('id')!=ART_ID or art.get('expired') or art.get('digest')!='sha256:'+ART_SHA or art.get('workflow_run',{}).get('id') not in (RUN,None):fail('26988 artifact identity/published digest')
 TMP.mkdir(parents=True,exist_ok=True)
 subprocess.run(['curl','--fail','--location','--retry','3','--silent','--show-error','-H','Authorization: Bearer '+token,'-H','Accept: application/vnd.github+json',f'https://api.github.com/repos/{REPO}/actions/artifacts/{ART_ID}/zip','-o',str(ART)],check=True)
 if sha(ART)!=ART_SHA:fail('downloaded successful 26988 ZIP mismatch')
 print('PASS exact successful 26988 Actions artifact fetched')

def prior_zip():
 if not ART.is_file() or sha(ART)!=ART_SHA:fail('successful 26988 ZIP inaccessible or wrong hash')
 return zipfile.ZipFile(ART)
def safe_extract_tar(data,dest):
 with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as t:
  for m in t:
   path=pathlib.PurePosixPath(m.name)
   if not m.isfile() or not path.parts or path.parts[0]!='app' or path.is_absolute() or '..' in path.parts or m.issym() or m.islnk():fail('unsafe 26988 compiled TAR entry '+m.name)
  t.extractall(dest,filter='data')

def recover():
 seal()
 for folder in (BASE,CAND):
  if folder.exists():shutil.rmtree(folder)
 BASE.mkdir(parents=True)
 with prior_zip() as z:
  if z.testzip():fail('26988 ZIP CRC invalid')
  def get(name):
   p='photon_26988_outputs/'+name
   if p not in z.namelist():fail('26988 successful compiled receipt missing '+p)
   return z.read(p)
  src=get('26988_candidate_app_source.tar.gz')
  if hashlib.sha256(src).hexdigest()!=TAR_SHA or get('26988_candidate_app_source.tar.gz.sha256')!=f'{TAR_SHA}  26988_candidate_app_source.tar.gz\n'.encode():fail('26988 actual compiled TAR mismatch')
  if get('26988_EXPECTED_FULL_APP.sha256')!=(R/'26989_BASE_26988_FULL_APP.sha256').read_bytes() or get('26988_PREBUILD_SEALED_APP.sha256')!=(R/'26989_BASE_26988_FULL_APP.sha256').read_bytes():fail('compiled source manifest authority differs')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build_26988_incremental.py')).hexdigest()!=BUILDER_SHA or BUILDER_SHA not in get('26988_ACTUAL_EXECUTED_BUILDER.sha256').decode():fail('successful executed builder not pinned')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build-26988-change-aware.yml')).hexdigest()!=WORKFLOW_SHA or WORKFLOW_SHA not in get('26988_ACTUAL_EXECUTED_WORKFLOW.sha256').decode():fail('successful executed workflow not pinned')
  if PRIOR_APK_NAME not in z.namelist() or PRIOR_APK_SHA not in get('26988_APK.sha256').decode() or hashlib.sha256(z.read(PRIOR_APK_NAME)).hexdigest()!=PRIOR_APK_SHA:fail('successful 26988 APK identity')
  identity=get('26988_ACTIONS_IDENTITY.txt').decode()
  if 'git_sha='+COMMIT not in identity or 'github_run_id='+str(RUN) not in identity:fail('26988 Actions job identity')
  compiler=get('26988_COMPILER_STATUS.txt').decode()
  for phrase in ('REAL PINNED GLSL COMPILE: PASS','REAL SPIR-V VALIDATION/OPTIMIZATION: PASS','REAL KOTLIN COMPILE: PASS','REAL JAVA COMPILE: PASS','REAL TWO-ABI NDK/CMake COMPILE: PASS','REAL ANDROID Gradle :app:assembleDebug: PASS','RUNTIME SOURCE INVARIANCE: PASS'):
   if phrase not in compiler:fail('26988 compiler proof absent: '+phrase)
  for task in (':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL'):
   if 'PASS '+task not in get('26988_REAL_GRADLE_TASKS.txt').decode():fail('26988 predecessor Gradle task absent: '+task)
  safe_extract_tar(src,BASE)
 exact(BASE,'26989_BASE_26988_FULL_APP.sha256','actual successful 26988 compiled source')
 shutil.copytree(BASE,CAND)
 changed,_,b=scope()
 for p in sorted(changed):
  dest=CAND/p;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/'handoff_payload_26989'/p,dest)
 exact(CAND,'26989_EXPECTED_FULL_APP.sha256','exact 26989 isolated candidate')
 print('PASS actual 26988 compiled authority and isolated 26989 candidate recovered')

def restore_live(root):
 if not (R/'gradlew').is_file() or not (R/'app/build.gradle').is_file():fail('live checkout missing real Gradle')
 if (R/'app/src').exists():shutil.rmtree(R/'app/src')
 shutil.copytree(root/'app/src',R/'app/src')
 shutil.copyfile(root/'app/version.properties',R/'app/version.properties')
 shutil.copyfile(root/'app/build.gradle',R/'app/build.gradle')
 if (R/'app/.cxx').exists():shutil.rmtree(R/'app/.cxx')

def prepare_base():
 # Single latest compiled runtime authority. No previous source reconstruction.
 recover();restore_live(BASE)
 exact(R,'26989_BASE_26988_FULL_APP.sha256','actual 26988 live predecessor restored')
 subprocess.run([sys.executable,'-S','test_26989_latest_preflight.py'],cwd=R,check=True)
 OUT.mkdir(parents=True,exist_ok=True)
 changed,_,_=scope()
 (OUT/'26989_SOURCE_SCOPE.txt').write_text(f'26988 Actions={RUN} commit={COMMIT} artifact={ART_ID} artifact_zip_sha={ART_SHA} actual_compiled_source_tar_sha={TAR_SHA}\nactual_runner_sha={BUILDER_SHA} actual_workflow_sha={WORKFLOW_SHA} prior_apk_sha={PRIOR_APK_SHA}\nbase={NBASE} candidate={NFILES} changes={NCHANGE} modified={NMODIFIED} added={NADDED} protected={NPROTECTED} deleted={NDELETED}\n'+''.join(p+'\n' for p in sorted(changed)))
 print('PASS latest-only 26988 authority, sparse historical fixtures and predecessor settings and source tests')

def install():
 seal();exact(BASE,'26989_BASE_26988_FULL_APP.sha256','26988 baseline before install')
 exact(CAND,'26989_EXPECTED_FULL_APP.sha256','26989 frozen candidate before install')
 old=OUT/'26988_SUCCESSFUL_REAL_GLSL_SPIRV_COMPILER.txt'
 # Historical 26904 checks have been run; require predecessor successful Actions compiler receipt too.
 with prior_zip() as z:
  source=z.read('photon_26988_outputs/26988_REAL_GLSL_SPIRV_COMPILER.txt').decode()
  if 'PASS actual 26974 24/24 C GLES' not in source or 'PASS inherited historical 24/24 and actual current 299/299 26988 donor/Iris C shader compilation' not in source:fail('26988 real pinned GLSL/SPIR-V receipt missing')
 (OUT/'26988_SUCCESSFUL_REAL_GLSL_SPIRV_COMPILER.txt').write_text(source)
 with prior_zip() as z:
  con=z.read('photon_26988_outputs/26988_CON_REAL_GLSL_SPIRV_COMPILER.txt').decode()
  if 'PASS 26988 C ON 14/14 static shader stages real GLSL/SPIR-V opt/val' not in con:fail('26988 real C ON shader proof absent')
 (OUT/'26988_SUCCESSFUL_CON_REAL_GLSL_SPIRV_COMPILER.txt').write_text(con)
 with prior_zip() as z:
  native=z.read('photon_26988_outputs/26988_NATIVE_REAL_GLSL_SPIRV_COMPILER.txt').decode()
  if 'PASS 47/47 private Vulkan variants real compile/opt/val' not in native:fail('26988 real native shader proof absent')
 (OUT/'26988_SUCCESSFUL_NATIVE_REAL_GLSL_SPIRV_COMPILER.txt').write_text(native)
 shutil.rmtree(R/'app/src');shutil.copytree(CAND/'app/src',R/'app/src')
 shutil.copyfile(CAND/'app/version.properties',R/'app/version.properties')
 shutil.copyfile(CAND/'app/build.gradle',R/'app/build.gradle')
 exact(R,'26989_EXPECTED_FULL_APP.sha256','live installed 26989 SHA source')
 print('PASS installed exact 26989 C Motion bounded memory and C ON latest highlight/HDR OFF source; production unapproved')

def regress():
 seal();exact(R,'26989_EXPECTED_FULL_APP.sha256','26989 live protected runtime')
 subprocess.run([sys.executable,'-S','test_26989_source.py','--live'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26987_color_host.py'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26988_exposure_host.py'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26989_raw_memory_host.py','--live'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26989_highlight_host.py','--live'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26982_integration_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26981_integration_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26979_integration_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26978_integration_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26977_integration_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26976_capture_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26975_gallery_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26986_crop_host.py'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','verify_26989_v6_current_glsl.py','--audit'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','verify_26989_native_glsl.py','--audit'],cwd=R,check=True)
 print('PASS live independent C exposure optimizer, exact frame replacement, tuning, protected A/B source invariance')

def stage_native():
 seal()
 with prior_zip() as z:
  with zipfile.ZipFile(io.BytesIO(z.read(PRIOR_APK_NAME))) as apk:
   if apk.testzip():fail('26988 published APK CRC')
   for p,want in NATIVE_SHA.items():
    data=apk.read(p)
    if hashlib.sha256(data).hexdigest()!=want:fail('successful native ABI hash regression '+p)
    dest=R/'app/build/verified_rawlens26931/jniLibs'/p.removeprefix('lib/')
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    if sha(dest)!=want:fail('staged native binary differs '+p)
 print('PASS exact successful 26988 dual ABI RawLens native binaries')

def verify_compiled():
 regress();success=OUT/'26988_SUCCESSFUL_REAL_GLSL_SPIRV_COMPILER.txt'
 current=OUT/'26989_REAL_GLSL_SPIRV_COMPILER.txt'
 if 'PASS 26988 C ON 14/14 static shader stages real GLSL/SPIR-V opt/val' not in (OUT/'26988_SUCCESSFUL_CON_REAL_GLSL_SPIRV_COMPILER.txt').read_text():fail('26988 predecessor C ON shader receipt missing')
 if not success.is_file() or 'PASS actual 26974 24/24 C GLES' not in success.read_text() or 'PASS inherited historical 24/24 and actual current 299/299 26988 donor/Iris C shader compilation' not in success.read_text():fail('26988 actual successful shader proof missing')
 if not current.is_file() or 'PASS actual 26974 24/24 C GLES' not in current.read_text() or 'PASS inherited historical 24/24 and actual current {SHADER_COUNT}/{SHADER_COUNT} 26989 donor/Iris C shader compilation'.format(SHADER_COUNT=SHADER_COUNT) not in current.read_text():fail('current Actions 24/24 + 26989 299/299 shader recompilation proof missing')
 con=OUT/'26989_CON_REAL_GLSL_SPIRV_COMPILER.txt'
 if not con.is_file() or 'PASS 26989 C ON 14/14 static shader stages real GLSL/SPIR-V opt/val' not in con.read_text():fail('new C ON real shader compiler proof missing')
 v6=OUT/'26989_V6_CURRENT_STATIC_GLSL_SPIRV_COMPILER.txt'
 if not v6.is_file() or f'PASS 26989 physical current {SHADER_COUNT}/{SHADER_COUNT} static donor/Iris C ESSL GLSL + SPIR-V opt/val' not in v6.read_text():fail('current C shader parser and SPIR-V optimizer must actually pass')
 for p,want in NATIVE_SHA.items():
  if sha(R/'app/build/verified_rawlens26931/jniLibs'/p.removeprefix('lib/'))!=want:fail('staged dual ABI LKR mismatch')
 for p,want in DONOR_SHA.items():
  if sha(R/'app/src/main/jniLibs'/p.removeprefix('lib/'))!=want:fail('original pinned donor sidecar mismatch')
 OUT.mkdir(exist_ok=True)
 (OUT/'26989_PREBUILD_SEALED_APP.sha256').write_bytes((R/'26989_EXPECTED_FULL_APP.sha256').read_bytes())
 if 'PASS 47/47 private Vulkan variants real compile/opt/val' not in (OUT/'26989_NATIVE_REAL_GLSL_SPIRV_COMPILER.txt').read_text():fail('missing actual private Vulkan compiler proof')
 if 'PASS exact 26989 runtime ESSL300 OES preview pair compile/link' not in (OUT/'26989_PREVIEW_REAL_GLSL.txt').read_text():fail('current real preview shader compile/link missing')
 print('PASS prebuild source seal + current actual pinned SPIR-V/GLSL + dual ABI native input')

def finalize():
 regress()
 if (OUT/'26989_PREBUILD_SEALED_APP.sha256').read_bytes()!=(R/'26989_EXPECTED_FULL_APP.sha256').read_bytes():fail('prebuild SHA seal absent')
 log=(OUT/'26989_gradle_assemble.log').read_text(errors='replace')
 tasks=(':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL')
 for task in tasks:
  if task not in log:fail('not proven actual Gradle task '+task)
 subprocess.run([sys.executable,'-S','verify_26906_native_cache.py','postflight'],cwd=R,check=True)
 apks=list((R/'app/build/outputs/apk').rglob('*.apk'))
 if len(apks)!=1:fail('exactly one newly assembled Android APK required')
 shutil.copy2(apks[0],R/APKNAME)
 if (R/APKNAME).stat().st_size<1_000_000:fail('suspicious APK size')
 with zipfile.ZipFile(R/APKNAME) as apk:
  if apk.testzip() or not {'AndroidManifest.xml','classes.dex'}<=set(apk.namelist()):fail('invalid Android output APK archive')
  for p,want in {**NATIVE_SHA,**DONOR_SHA}.items():
   if hashlib.sha256(apk.read(p)).hexdigest()!=want:fail('assembled APK native binary hash mismatch '+p)
  if not any(x.startswith('lib/arm64-v8a/libiris26972c.so') for x in apk.namelist()):fail('original C native library not linked')
  for abi in ('arm64-v8a','armeabi-v7a'):
   for lib in ('libiris26983conlkr.so','libiris26983conjpeg.so','libiris26985clkr2420.so'):
    if f'lib/{abi}/{lib}' not in apk.namelist():fail('C ON native link missing '+abi+'/'+lib)
   import tempfile
   with tempfile.TemporaryDirectory() as td:
    so=pathlib.Path(td)/'private.so';so.write_bytes(apk.read(f'lib/{abi}/libiris26985clkr2420.so'))
    deps=subprocess.check_output(['readelf','-d',str(so)],text=True)
    if any(lib in deps for lib in ('liblkrpipeline.so','libsrpipeline.so','libneuralnetworks.so')):fail('C native isolation failure '+abi)
    syms=subprocess.check_output(['readelf','-Ws',str(so)],text=True)
    if 'Java_com_hinnka_mycamera_processor_Iris26985CLkrNative_nativeMerge' not in syms:fail('private JNI missing '+abi)
 exact(R,'26989_EXPECTED_FULL_APP.sha256','actual assembled 26989 source unchanged')
 OUT.mkdir(exist_ok=True)
 (OUT/'26989_COMPILER_STATUS.txt').write_text('REAL PINNED GLSL COMPILE: PASS\nREAL SPIR-V VALIDATION/OPTIMIZATION: PASS\nREAL KOTLIN COMPILE: PASS\nREAL JAVA COMPILE: PASS\nREAL TWO-ABI NDK/CMake COMPILE: PASS\nREAL ANDROID Gradle :app:assembleDebug: PASS\nRUNTIME SOURCE INVARIANCE: PASS (2649 protected, 10 modified, 1 added)\nEXPERIMENT C CONTROLLED DEVICE TRIAL: ENABLED\nEXPERIMENT C PRODUCTION READY: NO\nDEVICE IQ VALIDATION: NOT RUN\n')
 (OUT/'26989_REAL_GRADLE_TASKS.txt').write_text(''.join('PASS '+p+'\n' for p in tasks))
 (OUT/'26989_APK.sha256').write_text(sha(R/APKNAME)+'  '+APKNAME+'\n')
 wf=R/'.github/workflows/build-26989-change-aware.yml'
 (OUT/'26989_ACTUAL_EXECUTED_BUILDER.sha256').write_text(sha(R/'build_26989_incremental.py')+'  build_26989_incremental.py\n')
 (OUT/'26989_ACTUAL_EXECUTED_WORKFLOW.sha256').write_text(sha(wf)+'  '+wf.relative_to(R).as_posix()+'\n')
 (OUT/'26989_ACTIONS_IDENTITY.txt').write_text('git_sha='+os.getenv('GITHUB_SHA','NOT_IN_ACTIONS')+'\ngithub_run_id='+os.getenv('GITHUB_RUN_ID','NOT_IN_ACTIONS')+'\n')
 for item in ('26989_BASE_26988_FULL_APP.sha256','26989_EXPECTED_FULL_APP.sha256','26989_PROTECTED_SOURCE.sha256','26989_CHANGED_RUNTIME_ALLOWLIST.txt','26989_ADDED_RUNTIME_PATHS.txt','26989_MODIFIED_ORIGINAL_PATHS.txt','26989_DELETED_RUNTIME_PATHS.txt','26989_AUTHORITY_AND_SCOPE.json'):
  shutil.copy2(R/item,OUT/item)
 shutil.copy2(R/'build_26989_incremental.py',OUT/'ACTUAL_EXECUTED_build_26989_incremental.py')
 shutil.copy2(wf,OUT/'ACTUAL_EXECUTED_build-26989-change-aware.yml')
 with (OUT/'26989_candidate_app_source.tar.gz').open('wb') as f:
  with gzip.GzipFile(filename='',mode='wb',compresslevel=1,mtime=0,fileobj=f) as gz:
   with tarfile.open(fileobj=gz,mode='w') as t:
    for rel in sorted(parse(R/'26989_EXPECTED_FULL_APP.sha256')):
     path=R/rel;m=t.gettarinfo(str(path),arcname=rel);m.uid=m.gid=0;m.uname=m.gname='';m.mtime=0
     with path.open('rb') as opened:t.addfile(m,opened)
 (OUT/'26989_candidate_app_source.tar.gz.sha256').write_text(sha(OUT/'26989_candidate_app_source.tar.gz')+'  26989_candidate_app_source.tar.gz\n')
 print('PASS real compiled 26989 source/APK SHA proof; IQ not proven until on-device')

if __name__=='__main__':
 try:
  parser=argparse.ArgumentParser();parser.add_argument('command',choices=('seal','fetch','prepare-base','install','regress','stage-native','verify-compiled','finalize'));args=parser.parse_args()
  globals()[args.command.replace('-','_')]()
 except Exception as e:print('26989 BUILD ERROR:',e,file=sys.stderr);sys.exit(1)
