#!/usr/bin/env python3
"""26982 guarded 3-stage successor to actual successful 26981 Actions.

Installs ONLY the full SHA-pinned C-only 26982 candidate atop actual successful
26981 compiled source TAR. Never retrieves source from a mutable dev HEAD.
No commit, push, partial compilation, platform verification bypass or A/B fallback.
"""
import argparse,gzip,hashlib,io,json,os,pathlib,re,shutil,subprocess,sys,tarfile,urllib.request,zipfile
R=pathlib.Path(__file__).resolve().parent
SHADER_COUNT=151 # exact current 26982 physical required shader inventory; not skip
TMP=R/'.photon_26982_work';OUT=R/'photon_26982_outputs'
ART=TMP/'26981-success.zip';BASE=TMP/'authority_26981';CAND=TMP/'candidate_26982'
REPO='SkyKing0007/Photon-Camera';BRANCH='experimental-clean-photon-rebuild'
RUN=45455628213;COMMIT='ed3391ce54181741b3d9dd51398b63c485064a19';ART_ID=14949744442
ART_SHA='fc6f9664809ca5b414ac6503768ecdde8441de7a6bfcde4247d4feef180f0007'
TAR_SHA='6899ff075747133a3d03bb6b30b2b8725ffc3f91274fcf2e45d1d83d968eb164'
BUILDER_SHA='2c3df5d1ee241cb1c929dfa3d1bd3567305ba063d65fc5c8a977de3f742f37b9'
WORKFLOW_SHA='9db7734164092877604273bf54c1d1888634cc2738ef14f6868b9526374271a3'
PRIOR_APK_SHA='d45d82b983da7878db6630c88c9a4640c79e706a4799b7b3632dea9bd0c00116'
PRIOR_APK_NAME='IrisCamera-0.9726981-26981-iris-rawr-debug.apk'
APKNAME='IrisCamera-0.9726982-26982-iris-rawr-debug.apk'
NBASE=2411;NFILES=2413;NCHANGE=14;NADDED=2;NMODIFIED=12;NDELETED=0;NPROTECTED=2399
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
FILES=['README_PHOTON_26982.md', '26982_COMMIT_MESSAGE.txt', '26982_LOCAL_VERIFICATION.txt', '26981_SUCCESSFUL_EXECUTED_BUILDER_REFERENCE.py', '26981_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml', 'build_26982_incremental.py', 'compile_26982_shaders.sh', 'test_26982_source.py', 'test_26982_patches.py', 'test_26982_sealed_negatives.py', 'test_26982_workflow_refs.py', 'test_26982_integration_host.py', 'test_26982_settings_java.py', 'verify_26982_v6_current_glsl.py', '26982_V6_CURRENT_SHADER_INVENTORY.json', '26982_BASE_26981_FULL_APP.sha256', '26982_EXPECTED_FULL_APP.sha256', '26982_PROTECTED_SOURCE.sha256', '26982_AUTHORITY_AND_SCOPE.json', '26982_CHANGED_RUNTIME_ALLOWLIST.txt', '26982_MODIFIED_ORIGINAL_PATHS.txt', '26982_ADDED_RUNTIME_PATHS.txt', '26982_DELETED_RUNTIME_PATHS.txt', '26982_FORWARD_FULLINDEX.patch', '26982_ROLLBACK_FULLINDEX.patch', '26982_STAGE_1_UPLOAD_PATHS.txt', '26982_STAGE_2_UPLOAD_PATHS.txt', '26982_STAGE_3_UPLOAD_PATHS.txt', '26982_EXPECTED_ACTION_EXECUTABLES.txt']
ALLOWED_MODIFIED=['app/src/main/java/com/hinnka/mycamera/processor/Iris26972CCamera2ShutterSession.kt', 'app/src/main/java/com/hinnka/mycamera/processor/Iris26972CCaptureToGallery.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/Iris26975CPinnedDonorProEngine.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/processor/PhotonSharpenTuning.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/RawDemosaicProcessor.kt', 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisLiveHistogramView.java', 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/GLPreview.java', 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java', 'app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java', 'app/src/main/res/values/strings.xml', 'app/src/main/res/xml/preferences.xml', 'app/version.properties']
ALLOWED_ADDED=['app/src/main/java/com/particlesdevs/photoncamera/settings/Iris26982CSharpenSettings.java', 'app/src/main/java/com/particlesdevs/photoncamera/ui/settings/custompreferences/Iris26982CBandPreference.java']

def fail(msg):raise RuntimeError('26982 BLOCKED: '+str(msg))
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
 a=parse(R/'26982_BASE_26981_FULL_APP.sha256');b=parse(R/'26982_EXPECTED_FULL_APP.sha256')
 changed=set((R/'26982_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
 added=set((R/'26982_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
 modified=set((R/'26982_MODIFIED_ORIGINAL_PATHS.txt').read_text().splitlines())
 deleted=set((R/'26982_DELETED_RUNTIME_PATHS.txt').read_text().splitlines())
 if (len(a),len(b),len(changed),len(added),len(modified),len(deleted))!=(NBASE,NFILES,NCHANGE,NADDED,NMODIFIED,NDELETED):fail('count/protected source regression')
 if changed!=added|modified or added&set(a) or modified-set(a) or set(b)!=(set(a)|added) or deleted:fail('unexpected runtime change/deletion')
 if {p for p in set(a)&set(b) if a[p]!=b[p]}!=modified:fail('original source edits outside allowlist')
 protected={p:h for p,h in a.items() if p not in changed}
 if len(protected)!=NPROTECTED or protected!=parse(R/'26982_PROTECTED_SOURCE.sha256'):fail('protected source failed')
 if sha(R/'26981_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml')!=WORKFLOW_SHA or sha(R/'26981_SUCCESSFUL_EXECUTED_BUILDER_REFERENCE.py')!=BUILDER_SHA:fail('26981 actual executed reference changed')
 if (R/'handoff_payload_26982/app/version.properties').read_text()!='VERSION_MAJOR=0\nVERSION_MINOR=9726440\nVERSION_NAME=0.9726982\nVERSION_BUILD=26982\n':fail('26982 version not exact')
 allowed_modified=set(json.loads((R/'26982_AUTHORITY_AND_SCOPE.json').read_text())['allowed_modified_exact'])
 if allowed_modified!=modified:fail('changed original paths not explicit')
 if modified!=set(ALLOWED_MODIFIED) or added!=set(ALLOWED_ADDED):fail('new scope not exact')
 if a['app/src/main/java/com/particlesdevs/photoncamera/util/SimpleStorageHelper.java']!=b['app/src/main/java/com/particlesdevs/photoncamera/util/SimpleStorageHelper.java']:fail('A/B gallery changed')
 return changed,a,b

def seal():
 changed,a,b=scope();wf='.github/workflows/build-26982-change-aware.yml';trigger='TRIGGER_26982.txt'
 expect=set(FILES)|{wf,trigger}|{'handoff_payload_26982/'+p for p in changed}
 sealed={}
 for line in (R/'26982_HANDOFF_HASHES.sha256').read_text().splitlines():
  try:h,p=line.split('  ',1)
  except ValueError:fail('bad handoff hash seal')
  if p in sealed or not (R/p).is_file() or sha(R/p)!=h:fail('missing/tampered handoff file '+p)
  sealed[p]=h
 if set(sealed)!=expect:fail('missing/extra handoff file set '+str(sorted(set(sealed)^expect)[:10]))
 stages=[(R/f'26982_STAGE_{i}_UPLOAD_PATHS.txt').read_text().splitlines() for i in (1,2,3)]
 if stages[0]!=sorted((expect|{'26982_HANDOFF_HASHES.sha256'})-{wf,trigger}) or stages[1]!=[wf] or stages[2]!=[trigger]:fail('three upload stages not strict')
 payload=R/'handoff_payload_26982'
 if {p.relative_to(payload).as_posix() for p in payload.rglob('*') if p.is_file()}!=changed:fail('payload missing/extra')
 for p in changed:
  if sha(payload/p)!=b[p]:fail('source input tampering '+p)
 if sha(R/'.github/workflows/build-26982-change-aware.yml')!=sealed[wf]:fail('workflow after seal changed')
 subprocess.run([sys.executable,'-S','test_26982_workflow_refs.py'],cwd=R,check=True)
 print(f'PASS 26982 three-stage SHA seal, {NPROTECTED} protected, {NCHANGE} source delta')

def fetch():
 seal();token=os.getenv('GITHUB_TOKEN','')
 if not token or os.getenv('GITHUB_REPOSITORY')!=REPO or os.getenv('GITHUB_REF_NAME')!=BRANCH:fail('Actions credentials/target branch unavailable')
 def get(endpoint):
  req=urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+endpoint,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'})
  with urllib.request.urlopen(req,timeout=120) as resp:return json.load(resp)
 run=get('actions/runs/'+str(RUN));art=get('actions/artifacts/'+str(ART_ID))
 if run.get('id')!=RUN or run.get('conclusion')!='success' or run.get('head_sha')!=COMMIT or run.get('head_branch')!=BRANCH:fail('26981 Actions run not successful/exact')
 if art.get('id')!=ART_ID or art.get('expired') or art.get('digest')!='sha256:'+ART_SHA or art.get('workflow_run',{}).get('id') not in (RUN,None):fail('26981 artifact identity/published digest')
 TMP.mkdir(parents=True,exist_ok=True)
 subprocess.run(['curl','--fail','--location','--retry','3','--silent','--show-error','-H','Authorization: Bearer '+token,'-H','Accept: application/vnd.github+json',f'https://api.github.com/repos/{REPO}/actions/artifacts/{ART_ID}/zip','-o',str(ART)],check=True)
 if sha(ART)!=ART_SHA:fail('downloaded successful 26981 ZIP mismatch')
 print('PASS exact successful 26981 Actions artifact fetched')

def prior_zip():
 if not ART.is_file() or sha(ART)!=ART_SHA:fail('successful 26981 ZIP inaccessible or wrong hash')
 return zipfile.ZipFile(ART)
def safe_extract_tar(data,dest):
 with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as t:
  for m in t:
   path=pathlib.PurePosixPath(m.name)
   if not m.isfile() or not path.parts or path.parts[0]!='app' or path.is_absolute() or '..' in path.parts or m.issym() or m.islnk():fail('unsafe 26981 compiled TAR entry '+m.name)
  t.extractall(dest,filter='data')

def prepare_base():
 seal()
 for folder in (BASE,CAND):
  if folder.exists():shutil.rmtree(folder)
 BASE.mkdir(parents=True)
 with prior_zip() as z:
  if z.testzip():fail('26981 ZIP CRC invalid')
  def get(name):
   p='photon_26981_outputs/'+name
   if p not in z.namelist():fail('26981 successful compiled receipt missing '+p)
   return z.read(p)
  src=get('26981_candidate_app_source.tar.gz')
  if hashlib.sha256(src).hexdigest()!=TAR_SHA or get('26981_candidate_app_source.tar.gz.sha256')!=f'{TAR_SHA}  26981_candidate_app_source.tar.gz\n'.encode():fail('26981 actual compiled TAR mismatch')
  if get('26981_EXPECTED_FULL_APP.sha256')!=(R/'26982_BASE_26981_FULL_APP.sha256').read_bytes() or get('26981_PREBUILD_SEALED_APP.sha256')!=(R/'26982_BASE_26981_FULL_APP.sha256').read_bytes():fail('compiled source manifest authority differs')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build_26981_incremental.py')).hexdigest()!=BUILDER_SHA or BUILDER_SHA not in get('26981_ACTUAL_EXECUTED_BUILDER.sha256').decode():fail('successful executed builder not pinned')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build-26981-change-aware.yml')).hexdigest()!=WORKFLOW_SHA or WORKFLOW_SHA not in get('26981_ACTUAL_EXECUTED_WORKFLOW.sha256').decode():fail('successful executed workflow not pinned')
  if PRIOR_APK_NAME not in z.namelist() or PRIOR_APK_SHA not in get('26981_APK.sha256').decode() or hashlib.sha256(z.read(PRIOR_APK_NAME)).hexdigest()!=PRIOR_APK_SHA:fail('successful 26981 APK identity')
  identity=get('26981_ACTIONS_IDENTITY.txt').decode()
  if 'git_sha='+COMMIT not in identity or 'github_run_id='+str(RUN) not in identity:fail('26981 Actions job identity')
  compiler=get('26981_COMPILER_STATUS.txt').decode()
  for phrase in ('REAL PINNED GLSL COMPILE: PASS','REAL SPIR-V VALIDATION/OPTIMIZATION: PASS','REAL KOTLIN COMPILE: PASS','REAL JAVA COMPILE: PASS','REAL TWO-ABI NDK/CMake COMPILE: PASS','REAL ANDROID Gradle :app:assembleDebug: PASS','RUNTIME SOURCE INVARIANCE: PASS'):
   if phrase not in compiler:fail('26981 compiler proof absent: '+phrase)
  for task in (':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL'):
   if 'PASS '+task not in get('26981_REAL_GRADLE_TASKS.txt').decode():fail('26981 predecessor Gradle task absent: '+task)
  safe_extract_tar(src,BASE)
 exact(BASE,'26982_BASE_26981_FULL_APP.sha256','actual successful 26981 compiled source')
 shutil.copytree(BASE,CAND)
 changed,_,b=scope()
 for p in sorted(changed):
  dest=CAND/p;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/'handoff_payload_26982'/p,dest)
 exact(CAND,'26982_EXPECTED_FULL_APP.sha256','exact 26982 isolated candidate')
 if not (R/'gradlew').is_file() or not (R/'app/build.gradle').is_file():fail('live checkout missing real Gradle')
 if (R/'app/src').exists():shutil.rmtree(R/'app/src')
 shutil.copytree(BASE/'app/src',R/'app/src')
 shutil.copyfile(BASE/'app/version.properties',R/'app/version.properties')
 shutil.copyfile(BASE/'app/build.gradle',R/'app/build.gradle')
 if (R/'app/.cxx').exists():shutil.rmtree(R/'app/.cxx')
 exact(R,'26982_BASE_26981_FULL_APP.sha256','historical preflight source restored')
 # Exact historical checks run against actual successful 26981 source.
 subprocess.run([sys.executable,'-S','test_26981_source.py','--live'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26981_integration_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26975_v5_asset_host.py','--live'],cwd=R,check=True)
 # V10/V4 intentionally pin the pre-26981 bridge. Replay unchanged legacy tests
 # on their sealed historical payload, never on the deliberately evolved bridge.
 # Exact 26981 live source is verified above; current source/host guards run below.
 subprocess.run([sys.executable,'-S','build_26975_incremental.py','seal'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26975_v10_minimal_core.py','--payload'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26975_v4_capture_host.py','--root',str(R/'handoff_payload_26975/app')],cwd=R,check=True)
 # Preserve the full live V10 core and shader reachability checks against an
 # isolated copy of the exact predecessor, substituting only its historical
 # bridge (already verified by the historical seal) for the old bridge pin.
 import tempfile
 with tempfile.TemporaryDirectory(prefix='26982_v10_') as td:
  t=pathlib.Path(td);shutil.copytree(R/'app',t/'app',ignore=shutil.ignore_patterns('build','.cxx'))
  for name in ('test_26975_v10_minimal_core.py','26975_V10_MINIMAL_LUT_REACHABILITY_PROOF.json','26975_V6_CURRENT_SHADER_INVENTORY.json'):
   shutil.copyfile(R/name,t/name)
  bridge='app/src/main/java/com/hinnka/mycamera/processor/experimentc/Iris26975CPinnedDonorProEngine.kt'
  shutil.copyfile(R/'handoff_payload_26975'/bridge,t/bridge)
  # 26981 deliberately evolved the encoder for shared EXIF. The unchanged V10 test
  # expects its historical exact bytes; replay them only in this temporary fixture.
  encoder='app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/gallery/Jpeg444ExportEncoder.kt'
  shutil.copyfile(R/'handoff_payload_26975'/encoder,t/encoder)
  subprocess.run([sys.executable,'-S','test_26975_v10_minimal_core.py','--live'],cwd=t,check=True)
 # No creative LUT may enter the actual successor bridge.
 for root in (BASE,CAND):
  bridge=(root/'app/src/main/java/com/hinnka/mycamera/processor/experimentc/Iris26975CPinnedDonorProEngine.kt').read_text()
  if any(x in bridge for x in ('LutImageProcessor','applyLutStack','LutConfig','samplerExternalOES')):fail('unexpected creative LUT bridge')
 exact(R,'26982_BASE_26981_FULL_APP.sha256','live predecessor unchanged after historical fixture replay')
 subprocess.run([sys.executable,'-S','verify_26981_v6_current_glsl.py','--audit'],cwd=R,check=True)
 OUT.mkdir(parents=True,exist_ok=True)
 (OUT/'26982_SOURCE_SCOPE.txt').write_text(f'26981 Actions={RUN} commit={COMMIT} artifact={ART_ID} artifact_zip_sha={ART_SHA} actual_compiled_source_tar_sha={TAR_SHA}\nactual_runner_sha={BUILDER_SHA} actual_workflow_sha={WORKFLOW_SHA} prior_apk_sha={PRIOR_APK_SHA}\nbase={NBASE} candidate={NFILES} changes={NCHANGE} modified={NMODIFIED} added={NADDED} protected={NPROTECTED} deleted={NDELETED}\n'+''.join(p+'\n' for p in sorted(changed)))
 print('PASS 26981 compiled baseline reconstructed; isolated 26982 candidate ready')

def install():
 seal();exact(BASE,'26982_BASE_26981_FULL_APP.sha256','26981 baseline before install')
 exact(CAND,'26982_EXPECTED_FULL_APP.sha256','26982 frozen candidate before install')
 old=OUT/'26981_SUCCESSFUL_REAL_GLSL_SPIRV_COMPILER.txt'
 # Historical 26904 checks have been run; require predecessor successful Actions compiler receipt too.
 with prior_zip() as z:
  source=z.read('photon_26981_outputs/26981_REAL_GLSL_SPIRV_COMPILER.txt').decode()
  if 'PASS actual 26974 24/24 C GLES' not in source or 'PASS inherited historical 24/24 and actual current 151/151 26981 donor/Iris C shader compilation' not in source:fail('26981 real pinned GLSL/SPIR-V receipt missing')
 (OUT/'26981_SUCCESSFUL_REAL_GLSL_SPIRV_COMPILER.txt').write_text(source)
 shutil.rmtree(R/'app/src');shutil.copytree(CAND/'app/src',R/'app/src')
 shutil.copyfile(CAND/'app/version.properties',R/'app/version.properties')
 shutil.copyfile(CAND/'app/build.gradle',R/'app/build.gradle')
 exact(R,'26982_EXPECTED_FULL_APP.sha256','live installed 26982 SHA source')
 print('PASS installed exact 26982 C-only Pro Sabre source; production unapproved')

def regress():
 seal();exact(R,'26982_EXPECTED_FULL_APP.sha256','26982 live protected runtime')
 subprocess.run([sys.executable,'-S','test_26982_source.py','--live'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26982_integration_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26982_settings_java.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26981_integration_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26979_integration_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26978_integration_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26977_integration_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26976_capture_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26975_gallery_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','verify_26982_v6_current_glsl.py','--audit'],cwd=R,check=True)
 print('PASS live independent C exposure optimizer, exact frame replacement, tuning, protected A/B source invariance')

def stage_native():
 seal()
 with prior_zip() as z:
  with zipfile.ZipFile(io.BytesIO(z.read(PRIOR_APK_NAME))) as apk:
   if apk.testzip():fail('26981 published APK CRC')
   for p,want in NATIVE_SHA.items():
    data=apk.read(p)
    if hashlib.sha256(data).hexdigest()!=want:fail('successful native ABI hash regression '+p)
    dest=R/'app/build/verified_rawlens26931/jniLibs'/p.removeprefix('lib/')
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    if sha(dest)!=want:fail('staged native binary differs '+p)
 print('PASS exact successful 26981 dual ABI RawLens native binaries')

def verify_compiled():
 regress();success=OUT/'26981_SUCCESSFUL_REAL_GLSL_SPIRV_COMPILER.txt'
 current=OUT/'26982_REAL_GLSL_SPIRV_COMPILER.txt'
 if not success.is_file() or 'PASS actual 26974 24/24 C GLES' not in success.read_text() or 'PASS inherited historical 24/24 and actual current 151/151 26981 donor/Iris C shader compilation' not in success.read_text():fail('26981 actual successful shader proof missing')
 if not current.is_file() or 'PASS actual 26974 24/24 C GLES' not in current.read_text() or 'PASS inherited historical 24/24 and actual current {SHADER_COUNT}/{SHADER_COUNT} 26982 donor/Iris C shader compilation'.format(SHADER_COUNT=SHADER_COUNT) not in current.read_text():fail('current Actions 24/24 + 26982 151/151 shader recompilation proof missing')
 v6=OUT/'26982_V6_CURRENT_STATIC_GLSL_SPIRV_COMPILER.txt'
 if not v6.is_file() or f'PASS 26982 physical current {SHADER_COUNT}/{SHADER_COUNT} static donor/Iris C ESSL GLSL + SPIR-V opt/val' not in v6.read_text():fail('current C shader parser and SPIR-V optimizer must actually pass')
 for p,want in NATIVE_SHA.items():
  if sha(R/'app/build/verified_rawlens26931/jniLibs'/p.removeprefix('lib/'))!=want:fail('staged dual ABI LKR mismatch')
 for p,want in DONOR_SHA.items():
  if sha(R/'app/src/main/jniLibs'/p.removeprefix('lib/'))!=want:fail('original pinned donor sidecar mismatch')
 OUT.mkdir(exist_ok=True)
 (OUT/'26982_PREBUILD_SEALED_APP.sha256').write_bytes((R/'26982_EXPECTED_FULL_APP.sha256').read_bytes())
 print('PASS prebuild source seal + current actual pinned SPIR-V/GLSL + dual ABI native input')

def finalize():
 regress()
 if (OUT/'26982_PREBUILD_SEALED_APP.sha256').read_bytes()!=(R/'26982_EXPECTED_FULL_APP.sha256').read_bytes():fail('prebuild SHA seal absent')
 log=(OUT/'26982_gradle_assemble.log').read_text(errors='replace')
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
 exact(R,'26982_EXPECTED_FULL_APP.sha256','actual assembled 26982 source unchanged')
 OUT.mkdir(exist_ok=True)
 (OUT/'26982_COMPILER_STATUS.txt').write_text('REAL PINNED GLSL COMPILE: PASS\nREAL SPIR-V VALIDATION/OPTIMIZATION: PASS\nREAL KOTLIN COMPILE: PASS\nREAL JAVA COMPILE: PASS\nREAL TWO-ABI NDK/CMake COMPILE: PASS\nREAL ANDROID Gradle :app:assembleDebug: PASS\nRUNTIME SOURCE INVARIANCE: PASS (2399 protected, 12 modified, 2 added)\nEXPERIMENT C CONTROLLED DEVICE TRIAL: ENABLED\nEXPERIMENT C PRODUCTION READY: NO\nDEVICE IQ VALIDATION: NOT RUN\n')
 (OUT/'26982_REAL_GRADLE_TASKS.txt').write_text(''.join('PASS '+p+'\n' for p in tasks))
 (OUT/'26982_APK.sha256').write_text(sha(R/APKNAME)+'  '+APKNAME+'\n')
 wf=R/'.github/workflows/build-26982-change-aware.yml'
 (OUT/'26982_ACTUAL_EXECUTED_BUILDER.sha256').write_text(sha(R/'build_26982_incremental.py')+'  build_26982_incremental.py\n')
 (OUT/'26982_ACTUAL_EXECUTED_WORKFLOW.sha256').write_text(sha(wf)+'  '+wf.relative_to(R).as_posix()+'\n')
 (OUT/'26982_ACTIONS_IDENTITY.txt').write_text('git_sha='+os.getenv('GITHUB_SHA','NOT_IN_ACTIONS')+'\ngithub_run_id='+os.getenv('GITHUB_RUN_ID','NOT_IN_ACTIONS')+'\n')
 for item in ('26982_BASE_26981_FULL_APP.sha256','26982_EXPECTED_FULL_APP.sha256','26982_PROTECTED_SOURCE.sha256','26982_CHANGED_RUNTIME_ALLOWLIST.txt','26982_ADDED_RUNTIME_PATHS.txt','26982_MODIFIED_ORIGINAL_PATHS.txt','26982_DELETED_RUNTIME_PATHS.txt','26982_AUTHORITY_AND_SCOPE.json'):
  shutil.copy2(R/item,OUT/item)
 shutil.copy2(R/'build_26982_incremental.py',OUT/'ACTUAL_EXECUTED_build_26982_incremental.py')
 shutil.copy2(wf,OUT/'ACTUAL_EXECUTED_build-26982-change-aware.yml')
 with (OUT/'26982_candidate_app_source.tar.gz').open('wb') as f:
  with gzip.GzipFile(filename='',mode='wb',compresslevel=1,mtime=0,fileobj=f) as gz:
   with tarfile.open(fileobj=gz,mode='w') as t:
    for rel in sorted(parse(R/'26982_EXPECTED_FULL_APP.sha256')):
     path=R/rel;m=t.gettarinfo(str(path),arcname=rel);m.uid=m.gid=0;m.uname=m.gname='';m.mtime=0
     with path.open('rb') as opened:t.addfile(m,opened)
 (OUT/'26982_candidate_app_source.tar.gz.sha256').write_text(sha(OUT/'26982_candidate_app_source.tar.gz')+'  26982_candidate_app_source.tar.gz\n')
 print('PASS real compiled 26982 source/APK SHA proof; IQ not proven until on-device')

if __name__=='__main__':
 try:
  parser=argparse.ArgumentParser();parser.add_argument('command',choices=('seal','fetch','prepare-base','install','regress','stage-native','verify-compiled','finalize'));args=parser.parse_args()
  globals()[args.command.replace('-','_')]()
 except Exception as e:print('26982 BUILD ERROR:',e,file=sys.stderr);sys.exit(1)
