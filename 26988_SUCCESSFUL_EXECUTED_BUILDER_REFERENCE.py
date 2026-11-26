#!/usr/bin/env python3
"""26988 guarded successor to successful 26987 V2. C OFF exposure/preview plus C ON legacy native highlights; real compiler gates retained."""
import argparse,gzip,hashlib,io,json,os,pathlib,re,shutil,subprocess,sys,tarfile,urllib.request,zipfile
R=pathlib.Path(__file__).resolve().parent
SHADER_COUNT=299 # exact current 26988 physical required shader inventory; not skip
TMP=R/'.photon_26988_work';OUT=R/'photon_26988_outputs'
ART=TMP/'26987-success.zip';BASE=TMP/'authority_26987';CAND=TMP/'candidate_26988'
REPO='SkyKing0007/Photon-Camera';BRANCH='experimental-clean-photon-rebuild'
RUN=45672716632;COMMIT='7c20cdba207a1a9e2f175741a916ec2e1e4c642c';ART_ID=15052860769
ART_SHA='a6523dfc67905e041a7457d2971df417c228aaabab0cc12ffab41acafcc0d2b4'
TAR_SHA='2b4a75e66b482832181d0df35802dcec45245011be6902a713b4578a8ed6dfbe'
BUILDER_SHA='27d0182104519da0f1b3ba4538effb7cf88ada0e5fd8e3c1e4abab7f1c38f5b9'
WORKFLOW_SHA='e606fb026ac9006dd03ea2ac7ef8b47f3d46ce649bb9daf2a1d62d3f69d4903d'
PRIOR_APK_SHA='4146478b4e86a4d22b0192e7125e6b781cd26a8d4c3d3056a5073fe0812fd707'
PRIOR_APK_NAME='IrisCamera-0.9726987-26987-iris-rawr-debug.apk'
APKNAME='IrisCamera-0.9726988-26988-iris-rawr-debug.apk'
NBASE=2657;NFILES=2659;NCHANGE=12;NADDED=2;NMODIFIED=10;NDELETED=0;NPROTECTED=2647
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
FILES=['26987_SUCCESSFUL_EXECUTED_BUILDER_REFERENCE.py', '26987_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml', '26988_ADDED_RUNTIME_PATHS.txt', '26988_AUTHORITY_AND_SCOPE.json', '26988_BASE_26987_FULL_APP.sha256', '26988_CHANGED_RUNTIME_ALLOWLIST.txt', '26988_COMMIT_MESSAGE.txt', '26988_CON_SHADER_INVENTORY.json', '26988_DELETED_RUNTIME_PATHS.txt', '26988_EXPECTED_FULL_APP.sha256', '26988_FORWARD_FULLINDEX.patch', '26988_MODIFIED_ORIGINAL_PATHS.txt', '26988_NATIVE_SHADER_INVENTORY.json', '26988_PROTECTED_SOURCE.sha256', '26988_ROLLBACK_FULLINDEX.patch', '26988_STAGE_1_UPLOAD_PATHS.txt', '26988_STAGE_2_UPLOAD_PATHS.txt', '26988_STAGE_3_UPLOAD_PATHS.txt', '26988_V6_CURRENT_SHADER_INVENTORY.json', '26988_post_copy_records.json', 'README_PHOTON_26988.md', 'build_26988_incremental.py', 'compile_26988_con_shaders.sh', 'compile_26988_shaders.sh', 'test_26988_exposure_host.py', 'test_26988_latest_preflight.py', 'test_26988_legacy_highlight_host.py', 'test_26988_patches.py', 'test_26988_sealed_negatives.py', 'test_26988_source.py', 'test_26988_workflow_refs.py', 'verify_26988_con_glsl.py', 'verify_26988_native_glsl.py', 'verify_26988_preview_glsl.py', 'verify_26988_v6_current_glsl.py']
ALLOWED_MODIFIED=['app/src/main/assets/shaders/preview/main_fs.glsl', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_adapter.cpp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_finish.cpp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_full.cpp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_jni.cpp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_solver.cpp', 'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java', 'app/src/main/java/com/particlesdevs/photoncamera/processing/experimentc/Iris26975CRawHighlightMeter.java', 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java', 'app/version.properties']
ALLOWED_ADDED=['app/src/main/java/com/particlesdevs/photoncamera/processing/experimentc/Iris26988CExposurePlan.java', 'app/src/main/java/com/particlesdevs/photoncamera/processing/experimentc/Iris26988CPreviewContinuity.java']

def fail(msg):raise RuntimeError('26988 BLOCKED: '+str(msg))
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
 a=parse(R/'26988_BASE_26987_FULL_APP.sha256');b=parse(R/'26988_EXPECTED_FULL_APP.sha256')
 changed=set((R/'26988_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
 added=set((R/'26988_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
 modified=set((R/'26988_MODIFIED_ORIGINAL_PATHS.txt').read_text().splitlines())
 deleted=set((R/'26988_DELETED_RUNTIME_PATHS.txt').read_text().splitlines())
 if (len(a),len(b),len(changed),len(added),len(modified),len(deleted))!=(NBASE,NFILES,NCHANGE,NADDED,NMODIFIED,NDELETED):fail('count/protected source regression')
 if changed!=added|modified or added&set(a) or modified-set(a) or set(b)!=(set(a)|added) or deleted:fail('unexpected runtime change/deletion')
 if {p for p in set(a)&set(b) if a[p]!=b[p]}!=modified:fail('original source edits outside allowlist')
 protected={p:h for p,h in a.items() if p not in changed}
 if len(protected)!=NPROTECTED or protected!=parse(R/'26988_PROTECTED_SOURCE.sha256'):fail('protected source failed')
 if sha(R/'26987_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml')!=WORKFLOW_SHA or sha(R/'26987_SUCCESSFUL_EXECUTED_BUILDER_REFERENCE.py')!=BUILDER_SHA:fail('26987 actual executed reference changed')
 if (R/'handoff_payload_26988/app/version.properties').read_text()!='VERSION_MAJOR=0\nVERSION_MINOR=9726440\nVERSION_NAME=0.9726988\nVERSION_BUILD=26988\n':fail('26988 version not exact')
 allowed_modified=set(json.loads((R/'26988_AUTHORITY_AND_SCOPE.json').read_text())['allowed_modified_exact'])
 if allowed_modified!=modified:fail('changed original paths not explicit')
 if modified!=set(ALLOWED_MODIFIED) or added!=set(ALLOWED_ADDED):fail('new scope not exact')
 if a['app/src/main/java/com/particlesdevs/photoncamera/util/SimpleStorageHelper.java']!=b['app/src/main/java/com/particlesdevs/photoncamera/util/SimpleStorageHelper.java']:fail('A/B gallery changed')
 return changed,a,b

def seal():
 changed,a,b=scope();wf='.github/workflows/build-26988-change-aware.yml';trigger='TRIGGER_26988.txt'
 expect=set(FILES)|{wf,trigger}|{'handoff_payload_26988/'+p for p in changed}
 sealed={}
 for line in (R/'26988_HANDOFF_HASHES.sha256').read_text().splitlines():
  try:h,p=line.split('  ',1)
  except ValueError:fail('bad handoff hash seal')
  if p in sealed or not (R/p).is_file() or sha(R/p)!=h:fail('missing/tampered handoff file '+p)
  sealed[p]=h
 if set(sealed)!=expect:fail('missing/extra handoff file set '+str(sorted(set(sealed)^expect)[:10]))
 stages=[(R/f'26988_STAGE_{i}_UPLOAD_PATHS.txt').read_text().splitlines() for i in (1,2,3)]
 if stages[0]!=sorted((expect|{'26988_HANDOFF_HASHES.sha256'})-{wf,trigger}) or stages[1]!=[wf] or stages[2]!=[trigger]:fail('three upload stages not strict')
 payload=R/'handoff_payload_26988'
 if {p.relative_to(payload).as_posix() for p in payload.rglob('*') if p.is_file()}!=changed:fail('payload missing/extra')
 for p in changed:
  if sha(payload/p)!=b[p]:fail('source input tampering '+p)
 if sha(R/'.github/workflows/build-26988-change-aware.yml')!=sealed[wf]:fail('workflow after seal changed')
 subprocess.run([sys.executable,'-S','test_26988_workflow_refs.py'],cwd=R,check=True)
 print(f'PASS 26988 three-stage SHA seal, {NPROTECTED} protected, {NCHANGE} source delta')

def fetch():
 seal();token=os.getenv('GITHUB_TOKEN','')
 if not token or os.getenv('GITHUB_REPOSITORY')!=REPO or os.getenv('GITHUB_REF_NAME')!=BRANCH:fail('Actions credentials/target branch unavailable')
 def get(endpoint):
  req=urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+endpoint,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'})
  with urllib.request.urlopen(req,timeout=120) as resp:return json.load(resp)
 run=get('actions/runs/'+str(RUN));art=get('actions/artifacts/'+str(ART_ID))
 if run.get('id')!=RUN or run.get('conclusion')!='success' or run.get('head_sha')!=COMMIT or run.get('head_branch')!=BRANCH:fail('26987 Actions run not successful/exact')
 if art.get('id')!=ART_ID or art.get('expired') or art.get('digest')!='sha256:'+ART_SHA or art.get('workflow_run',{}).get('id') not in (RUN,None):fail('26987 artifact identity/published digest')
 TMP.mkdir(parents=True,exist_ok=True)
 subprocess.run(['curl','--fail','--location','--retry','3','--silent','--show-error','-H','Authorization: Bearer '+token,'-H','Accept: application/vnd.github+json',f'https://api.github.com/repos/{REPO}/actions/artifacts/{ART_ID}/zip','-o',str(ART)],check=True)
 if sha(ART)!=ART_SHA:fail('downloaded successful 26987 ZIP mismatch')
 print('PASS exact successful 26987 Actions artifact fetched')

def prior_zip():
 if not ART.is_file() or sha(ART)!=ART_SHA:fail('successful 26987 ZIP inaccessible or wrong hash')
 return zipfile.ZipFile(ART)
def safe_extract_tar(data,dest):
 with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as t:
  for m in t:
   path=pathlib.PurePosixPath(m.name)
   if not m.isfile() or not path.parts or path.parts[0]!='app' or path.is_absolute() or '..' in path.parts or m.issym() or m.islnk():fail('unsafe 26987 compiled TAR entry '+m.name)
  t.extractall(dest,filter='data')

def recover():
 seal()
 for folder in (BASE,CAND):
  if folder.exists():shutil.rmtree(folder)
 BASE.mkdir(parents=True)
 with prior_zip() as z:
  if z.testzip():fail('26987 ZIP CRC invalid')
  def get(name):
   p='photon_26987_outputs/'+name
   if p not in z.namelist():fail('26987 successful compiled receipt missing '+p)
   return z.read(p)
  src=get('26987_candidate_app_source.tar.gz')
  if hashlib.sha256(src).hexdigest()!=TAR_SHA or get('26987_candidate_app_source.tar.gz.sha256')!=f'{TAR_SHA}  26987_candidate_app_source.tar.gz\n'.encode():fail('26987 actual compiled TAR mismatch')
  if get('26987_EXPECTED_FULL_APP.sha256')!=(R/'26988_BASE_26987_FULL_APP.sha256').read_bytes() or get('26987_PREBUILD_SEALED_APP.sha256')!=(R/'26988_BASE_26987_FULL_APP.sha256').read_bytes():fail('compiled source manifest authority differs')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build_26987_incremental.py')).hexdigest()!=BUILDER_SHA or BUILDER_SHA not in get('26987_ACTUAL_EXECUTED_BUILDER.sha256').decode():fail('successful executed builder not pinned')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build-26987-change-aware.yml')).hexdigest()!=WORKFLOW_SHA or WORKFLOW_SHA not in get('26987_ACTUAL_EXECUTED_WORKFLOW.sha256').decode():fail('successful executed workflow not pinned')
  if PRIOR_APK_NAME not in z.namelist() or PRIOR_APK_SHA not in get('26987_APK.sha256').decode() or hashlib.sha256(z.read(PRIOR_APK_NAME)).hexdigest()!=PRIOR_APK_SHA:fail('successful 26987 APK identity')
  identity=get('26987_ACTIONS_IDENTITY.txt').decode()
  if 'git_sha='+COMMIT not in identity or 'github_run_id='+str(RUN) not in identity:fail('26987 Actions job identity')
  compiler=get('26987_COMPILER_STATUS.txt').decode()
  for phrase in ('REAL PINNED GLSL COMPILE: PASS','REAL SPIR-V VALIDATION/OPTIMIZATION: PASS','REAL KOTLIN COMPILE: PASS','REAL JAVA COMPILE: PASS','REAL TWO-ABI NDK/CMake COMPILE: PASS','REAL ANDROID Gradle :app:assembleDebug: PASS','RUNTIME SOURCE INVARIANCE: PASS'):
   if phrase not in compiler:fail('26987 compiler proof absent: '+phrase)
  for task in (':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL'):
   if 'PASS '+task not in get('26987_REAL_GRADLE_TASKS.txt').decode():fail('26987 predecessor Gradle task absent: '+task)
  safe_extract_tar(src,BASE)
 exact(BASE,'26988_BASE_26987_FULL_APP.sha256','actual successful 26987 compiled source')
 shutil.copytree(BASE,CAND)
 changed,_,b=scope()
 for p in sorted(changed):
  dest=CAND/p;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/'handoff_payload_26988'/p,dest)
 exact(CAND,'26988_EXPECTED_FULL_APP.sha256','exact 26988 isolated candidate')
 print('PASS actual 26987 compiled authority and isolated 26988 candidate recovered')

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
 exact(R,'26988_BASE_26987_FULL_APP.sha256','actual 26987 live predecessor restored')
 subprocess.run([sys.executable,'-S','test_26988_latest_preflight.py'],cwd=R,check=True)
 OUT.mkdir(parents=True,exist_ok=True)
 changed,_,_=scope()
 (OUT/'26988_SOURCE_SCOPE.txt').write_text(f'26987 Actions={RUN} commit={COMMIT} artifact={ART_ID} artifact_zip_sha={ART_SHA} actual_compiled_source_tar_sha={TAR_SHA}\nactual_runner_sha={BUILDER_SHA} actual_workflow_sha={WORKFLOW_SHA} prior_apk_sha={PRIOR_APK_SHA}\nbase={NBASE} candidate={NFILES} changes={NCHANGE} modified={NMODIFIED} added={NADDED} protected={NPROTECTED} deleted={NDELETED}\n'+''.join(p+'\n' for p in sorted(changed)))
 print('PASS latest-only 26987 authority, sparse historical fixtures and predecessor settings and source tests')

def install():
 seal();exact(BASE,'26988_BASE_26987_FULL_APP.sha256','26987 baseline before install')
 exact(CAND,'26988_EXPECTED_FULL_APP.sha256','26988 frozen candidate before install')
 old=OUT/'26987_SUCCESSFUL_REAL_GLSL_SPIRV_COMPILER.txt'
 # Historical 26904 checks have been run; require predecessor successful Actions compiler receipt too.
 with prior_zip() as z:
  source=z.read('photon_26987_outputs/26987_REAL_GLSL_SPIRV_COMPILER.txt').decode()
  if 'PASS actual 26974 24/24 C GLES' not in source or 'PASS inherited historical 24/24 and actual current 299/299 26987 donor/Iris C shader compilation' not in source:fail('26987 real pinned GLSL/SPIR-V receipt missing')
 (OUT/'26987_SUCCESSFUL_REAL_GLSL_SPIRV_COMPILER.txt').write_text(source)
 with prior_zip() as z:
  con=z.read('photon_26987_outputs/26987_CON_REAL_GLSL_SPIRV_COMPILER.txt').decode()
  if 'PASS 26987 C ON 14/14 static shader stages real GLSL/SPIR-V opt/val' not in con:fail('26987 real C ON shader proof absent')
 (OUT/'26987_SUCCESSFUL_CON_REAL_GLSL_SPIRV_COMPILER.txt').write_text(con)
 with prior_zip() as z:
  native=z.read('photon_26987_outputs/26987_NATIVE_REAL_GLSL_SPIRV_COMPILER.txt').decode()
  if 'PASS 47/47 private Vulkan variants real compile/opt/val' not in native:fail('26987 real native shader proof absent')
 (OUT/'26987_SUCCESSFUL_NATIVE_REAL_GLSL_SPIRV_COMPILER.txt').write_text(native)
 shutil.rmtree(R/'app/src');shutil.copytree(CAND/'app/src',R/'app/src')
 shutil.copyfile(CAND/'app/version.properties',R/'app/version.properties')
 shutil.copyfile(CAND/'app/build.gradle',R/'app/build.gradle')
 exact(R,'26988_EXPECTED_FULL_APP.sha256','live installed 26988 SHA source')
 print('PASS installed exact 26988 C OFF exposure and C ON native highlight source; production unapproved')

def regress():
 seal();exact(R,'26988_EXPECTED_FULL_APP.sha256','26988 live protected runtime')
 subprocess.run([sys.executable,'-S','test_26988_source.py','--live'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26987_color_host.py'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26988_exposure_host.py'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26988_legacy_highlight_host.py','--live'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26982_integration_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26981_integration_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26979_integration_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26978_integration_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26977_integration_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26976_capture_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26975_gallery_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26986_crop_host.py'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','verify_26988_v6_current_glsl.py','--audit'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','verify_26988_native_glsl.py','--audit'],cwd=R,check=True)
 print('PASS live independent C exposure optimizer, exact frame replacement, tuning, protected A/B source invariance')

def stage_native():
 seal()
 with prior_zip() as z:
  with zipfile.ZipFile(io.BytesIO(z.read(PRIOR_APK_NAME))) as apk:
   if apk.testzip():fail('26987 published APK CRC')
   for p,want in NATIVE_SHA.items():
    data=apk.read(p)
    if hashlib.sha256(data).hexdigest()!=want:fail('successful native ABI hash regression '+p)
    dest=R/'app/build/verified_rawlens26931/jniLibs'/p.removeprefix('lib/')
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    if sha(dest)!=want:fail('staged native binary differs '+p)
 print('PASS exact successful 26987 dual ABI RawLens native binaries')

def verify_compiled():
 regress();success=OUT/'26987_SUCCESSFUL_REAL_GLSL_SPIRV_COMPILER.txt'
 current=OUT/'26988_REAL_GLSL_SPIRV_COMPILER.txt'
 if 'PASS 26987 C ON 14/14 static shader stages real GLSL/SPIR-V opt/val' not in (OUT/'26987_SUCCESSFUL_CON_REAL_GLSL_SPIRV_COMPILER.txt').read_text():fail('26987 predecessor C ON shader receipt missing')
 if not success.is_file() or 'PASS actual 26974 24/24 C GLES' not in success.read_text() or 'PASS inherited historical 24/24 and actual current 299/299 26987 donor/Iris C shader compilation' not in success.read_text():fail('26987 actual successful shader proof missing')
 if not current.is_file() or 'PASS actual 26974 24/24 C GLES' not in current.read_text() or 'PASS inherited historical 24/24 and actual current {SHADER_COUNT}/{SHADER_COUNT} 26988 donor/Iris C shader compilation'.format(SHADER_COUNT=SHADER_COUNT) not in current.read_text():fail('current Actions 24/24 + 26988 299/299 shader recompilation proof missing')
 con=OUT/'26988_CON_REAL_GLSL_SPIRV_COMPILER.txt'
 if not con.is_file() or 'PASS 26988 C ON 14/14 static shader stages real GLSL/SPIR-V opt/val' not in con.read_text():fail('new C ON real shader compiler proof missing')
 v6=OUT/'26988_V6_CURRENT_STATIC_GLSL_SPIRV_COMPILER.txt'
 if not v6.is_file() or f'PASS 26988 physical current {SHADER_COUNT}/{SHADER_COUNT} static donor/Iris C ESSL GLSL + SPIR-V opt/val' not in v6.read_text():fail('current C shader parser and SPIR-V optimizer must actually pass')
 for p,want in NATIVE_SHA.items():
  if sha(R/'app/build/verified_rawlens26931/jniLibs'/p.removeprefix('lib/'))!=want:fail('staged dual ABI LKR mismatch')
 for p,want in DONOR_SHA.items():
  if sha(R/'app/src/main/jniLibs'/p.removeprefix('lib/'))!=want:fail('original pinned donor sidecar mismatch')
 OUT.mkdir(exist_ok=True)
 (OUT/'26988_PREBUILD_SEALED_APP.sha256').write_bytes((R/'26988_EXPECTED_FULL_APP.sha256').read_bytes())
 if 'PASS 47/47 private Vulkan variants real compile/opt/val' not in (OUT/'26988_NATIVE_REAL_GLSL_SPIRV_COMPILER.txt').read_text():fail('missing actual private Vulkan compiler proof')
 if 'PASS exact 26988 runtime ESSL300 OES preview pair compile/link' not in (OUT/'26988_PREVIEW_REAL_GLSL.txt').read_text():fail('current real preview shader compile/link missing')
 print('PASS prebuild source seal + current actual pinned SPIR-V/GLSL + dual ABI native input')

def finalize():
 regress()
 if (OUT/'26988_PREBUILD_SEALED_APP.sha256').read_bytes()!=(R/'26988_EXPECTED_FULL_APP.sha256').read_bytes():fail('prebuild SHA seal absent')
 log=(OUT/'26988_gradle_assemble.log').read_text(errors='replace')
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
 exact(R,'26988_EXPECTED_FULL_APP.sha256','actual assembled 26988 source unchanged')
 OUT.mkdir(exist_ok=True)
 (OUT/'26988_COMPILER_STATUS.txt').write_text('REAL PINNED GLSL COMPILE: PASS\nREAL SPIR-V VALIDATION/OPTIMIZATION: PASS\nREAL KOTLIN COMPILE: PASS\nREAL JAVA COMPILE: PASS\nREAL TWO-ABI NDK/CMake COMPILE: PASS\nREAL ANDROID Gradle :app:assembleDebug: PASS\nRUNTIME SOURCE INVARIANCE: PASS (2647 protected, 10 modified, 2 added)\nEXPERIMENT C CONTROLLED DEVICE TRIAL: ENABLED\nEXPERIMENT C PRODUCTION READY: NO\nDEVICE IQ VALIDATION: NOT RUN\n')
 (OUT/'26988_REAL_GRADLE_TASKS.txt').write_text(''.join('PASS '+p+'\n' for p in tasks))
 (OUT/'26988_APK.sha256').write_text(sha(R/APKNAME)+'  '+APKNAME+'\n')
 wf=R/'.github/workflows/build-26988-change-aware.yml'
 (OUT/'26988_ACTUAL_EXECUTED_BUILDER.sha256').write_text(sha(R/'build_26988_incremental.py')+'  build_26988_incremental.py\n')
 (OUT/'26988_ACTUAL_EXECUTED_WORKFLOW.sha256').write_text(sha(wf)+'  '+wf.relative_to(R).as_posix()+'\n')
 (OUT/'26988_ACTIONS_IDENTITY.txt').write_text('git_sha='+os.getenv('GITHUB_SHA','NOT_IN_ACTIONS')+'\ngithub_run_id='+os.getenv('GITHUB_RUN_ID','NOT_IN_ACTIONS')+'\n')
 for item in ('26988_BASE_26987_FULL_APP.sha256','26988_EXPECTED_FULL_APP.sha256','26988_PROTECTED_SOURCE.sha256','26988_CHANGED_RUNTIME_ALLOWLIST.txt','26988_ADDED_RUNTIME_PATHS.txt','26988_MODIFIED_ORIGINAL_PATHS.txt','26988_DELETED_RUNTIME_PATHS.txt','26988_AUTHORITY_AND_SCOPE.json'):
  shutil.copy2(R/item,OUT/item)
 shutil.copy2(R/'build_26988_incremental.py',OUT/'ACTUAL_EXECUTED_build_26988_incremental.py')
 shutil.copy2(wf,OUT/'ACTUAL_EXECUTED_build-26988-change-aware.yml')
 with (OUT/'26988_candidate_app_source.tar.gz').open('wb') as f:
  with gzip.GzipFile(filename='',mode='wb',compresslevel=1,mtime=0,fileobj=f) as gz:
   with tarfile.open(fileobj=gz,mode='w') as t:
    for rel in sorted(parse(R/'26988_EXPECTED_FULL_APP.sha256')):
     path=R/rel;m=t.gettarinfo(str(path),arcname=rel);m.uid=m.gid=0;m.uname=m.gname='';m.mtime=0
     with path.open('rb') as opened:t.addfile(m,opened)
 (OUT/'26988_candidate_app_source.tar.gz.sha256').write_text(sha(OUT/'26988_candidate_app_source.tar.gz')+'  26988_candidate_app_source.tar.gz\n')
 print('PASS real compiled 26988 source/APK SHA proof; IQ not proven until on-device')

if __name__=='__main__':
 try:
  parser=argparse.ArgumentParser();parser.add_argument('command',choices=('seal','fetch','prepare-base','install','regress','stage-native','verify-compiled','finalize'));args=parser.parse_args()
  globals()[args.command.replace('-','_')]()
 except Exception as e:print('26988 BUILD ERROR:',e,file=sys.stderr);sys.exit(1)
