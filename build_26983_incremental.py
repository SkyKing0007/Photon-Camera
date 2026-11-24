#!/usr/bin/env python3
"""26983 guarded 3-stage successor to actual successful 26982 Actions.

Installs ONLY the full SHA-pinned independent C ON and B/C preview 26983 candidate atop actual successful
26982 compiled source TAR. Never retrieves source from a mutable dev HEAD.
No commit, push, partial compilation, platform verification bypass or A/B fallback.
"""
import argparse,gzip,hashlib,io,json,os,pathlib,re,shutil,subprocess,sys,tarfile,urllib.request,zipfile
R=pathlib.Path(__file__).resolve().parent
SHADER_COUNT=151 # exact current 26983 physical required shader inventory; not skip
TMP=R/'.photon_26983_work';OUT=R/'photon_26983_outputs'
ART=TMP/'26982-success.zip';BASE=TMP/'authority_26982';CAND=TMP/'candidate_26983'
REPO='SkyKing0007/Photon-Camera';BRANCH='experimental-clean-photon-rebuild'
RUN=45478582046;COMMIT='b783a667fbf91b053d1bc390a72d056cfe4a9abc';ART_ID=14960894133
ART_SHA='40a96436790965fcf75e0ab49ec79f33ac9c634f7fc351625e73bee15de28983'
TAR_SHA='7b2f69c96d9259ea22c88697185ea1c25b55d4ef87b053dab60ab03b2a3a6d2d'
BUILDER_SHA='995a2161edc3f0f264a22c1284999e5e681447dd1faa67c74c291afa7b68c974'
WORKFLOW_SHA='4955b3162cfd9155efaa3563a959f6160e72f3c91f0bbc152cfe64da7b9fb235'
PRIOR_APK_SHA='2e9efb2276c1348678e8f1f079e6d07367ad13ed8255a39280530b846b9fa9ad'
PRIOR_APK_NAME='IrisCamera-0.9726982-26982-iris-rawr-debug.apk'
APKNAME='IrisCamera-0.9726983-26983-iris-rawr-debug.apk'
NBASE=2413;NFILES=2486;NCHANGE=91;NADDED=73;NMODIFIED=18;NDELETED=0;NPROTECTED=2395
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
FILES=['26982_SUCCESSFUL_EXECUTED_BUILDER_REFERENCE.py', '26982_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml', '26983_ADDED_RUNTIME_PATHS.txt', '26983_AUTHORITY_AND_SCOPE.json', '26983_BASE_26982_FULL_APP.sha256', '26983_CHANGED_RUNTIME_ALLOWLIST.txt', '26983_COMMIT_MESSAGE.txt', '26983_CON_SHADER_INVENTORY.json', '26983_DELETED_RUNTIME_PATHS.txt', '26983_EXPECTED_ACTION_EXECUTABLES.txt', '26983_EXPECTED_FULL_APP.sha256', '26983_FORWARD_FULLINDEX.patch', '26983_LOCAL_VERIFICATION.txt', '26983_MODIFIED_ORIGINAL_PATHS.txt', '26983_PROTECTED_SOURCE.sha256', '26983_ROLLBACK_FULLINDEX.patch', '26983_STAGE_1_UPLOAD_PATHS.txt', '26983_STAGE_2_UPLOAD_PATHS.txt', '26983_STAGE_3_UPLOAD_PATHS.txt', '26983_V6_CURRENT_SHADER_INVENTORY.json', '26983_copy_records.json', '26983_post_copy_records.json', 'README_PHOTON_26983.md', 'advance_post_26983.py', 'build_26983_incremental.py', 'compile_26983_con_shaders.sh', 'compile_26983_shaders.sh', 'test_26983_capture_policy_host.py', 'test_26983_con_host.py', 'test_26983_gpu_glsl_mesa.py', 'test_26983_gpu_host.py', 'test_26983_integrated_host.py', 'test_26983_motion_ingress_host.py', 'test_26983_orchestration_host.py', 'test_26983_patches.py', 'test_26983_post_host.py', 'test_26983_sealed_negatives.py', 'test_26983_settings_host.py', 'test_26983_source.py', 'test_26983_workflow_refs.py', 'verify_26983_con_glsl.py', 'verify_26983_v6_current_glsl.py']
ALLOWED_MODIFIED=['app/src/main/cpp/CMakeLists.txt', 'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java', 'app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26935BOnProcessingRelay.java', 'app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26935BOnSession.java', 'app/src/main/java/com/particlesdevs/photoncamera/processing/DefaultSaver.java', 'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java', 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt', 'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java', 'app/src/main/java/com/particlesdevs/photoncamera/settings/Iris26982CSharpenSettings.java', 'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java', 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java', 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java', 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/GLPreview.java', 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java', 'app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java', 'app/src/main/res/layout/layout_main_viewfinder.xml', 'app/src/main/res/xml/preferences.xml', 'app/version.properties']
ALLOWED_ADDED=['app/src/main/assets/iris26983/con/lab/lab_defringe_common.glsl', 'app/src/main/assets/iris26983/con/lab/lab_defringe_prepare.comp', 'app/src/main/assets/iris26983/con/lab/lab_defringe_reconstruct.comp', 'app/src/main/assets/iris26983/con/lab/lab_defringe_reduce.comp', 'app/src/main/assets/shaders/iris26983/con_fused_final_p3_gain.frag', 'app/src/main/assets/shaders/iris26983/con_post/addwatermark_rotate.glsl', 'app/src/main/assets/shaders/iris26983/con_post/color_transform.glsl', 'app/src/main/assets/shaders/iris26983/con_post/display_exposure.glsl', 'app/src/main/assets/shaders/iris26983/con_post/false_color_classify_26800.glsl', 'app/src/main/assets/shaders/iris26983/con_post/false_color_propagate_26799.glsl', 'app/src/main/assets/shaders/iris26983/con_post/gainmap.glsl', 'app/src/main/assets/shaders/iris26983/con_post/iris26899_b_off_zoom_luma_sharpen.glsl', 'app/src/main/assets/shaders/iris26983/con_post/iris_tone_controls.glsl', 'app/src/main/assets/shaders/iris26983/con_post/local_laplacian_accumulate_26621.glsl', 'app/src/main/assets/shaders/iris26983/con_post/local_laplacian_downsample_26621.glsl', 'app/src/main/assets/shaders/iris26983/con_post/local_laplacian_global_log_26621.glsl', 'app/src/main/assets/shaders/iris26983/con_post/local_laplacian_reconstruct_26621.glsl', 'app/src/main/assets/shaders/iris26983/con_post/local_laplacian_remap_26621.glsl', 'app/src/main/assets/shaders/iris26983/con_post/preview_hue_match_26907.glsl', 'app/src/main/assets/shaders/iris26983/con_post/render.glsl', 'app/src/main/cpp/iris26864/Iris26983COnGlAhbBinding.cpp', 'app/src/main/cpp/iris26864/Iris26983COnGuidePack.h', 'app/src/main/cpp/iris26864/Iris26983COnLkrAndroidInterop.cpp', 'app/src/main/cpp/iris26864/Iris26983COnRgba16fCarrier.cpp', 'app/src/main/cpp/iris26983_con_jpeg_writer.cpp', 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26983COnColorContract.kt', 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26983COnFrozenRawIngress.kt', 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26983COnGpuMerge.kt', 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26983COnGpuSharpest.kt', 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26983COnGuidePublication.kt', 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26983COnHighlightReference.kt', 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26983COnLabDefringe.kt', 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26983COnLkrBridge.java', 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26983COnMotionIngress.kt', 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26983COnPipeline.kt', 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26983COnRawLensMedian.kt', 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26983COnRawrFalseColor.kt', 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26983COnSceneMotion.kt', 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26983COnSmoothWhite.kt', 'app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26983COnCaptureSafety.java', 'app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26983COnContinuity.java', 'app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26983COnProcessingRelay.java', 'app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26983COnSession.java', 'app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26983COnShutterIsoMath.java', 'app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26983DirectPreviewFence.java', 'app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26983DirectPreviewPlan.java', 'app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26983DirectPreviewRequests.java', 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Iris26983COnAcr3Curve.java', 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Iris26983COnColorTransform.java', 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Iris26983COnDisplayExposure.java', 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Iris26983COnExposureMatcher.java', 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Iris26983COnGainMapNative.java', 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Iris26983COnHighlightAnalysis.java', 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Iris26983COnPostPipeline.java', 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Iris26983COnPreviewHueCalibration.java', 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Iris26983COnPreviewHueMatch.java', 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Iris26983COnPublicationTone.java', 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Iris26983COnRender.java', 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Iris26983COnRgbInput.java', 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Iris26983COnRotateWatermark.java', 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Iris26983COnToneControls.java', 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/Iris26983COnBatchPublication.java', 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/Iris26983COnCapturePreparation.java', 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/Iris26983COnPhotoPublication.java', 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/Iris26983COnRgba16fCarrier.java', 'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/Iris26983COnEncoder.java', 'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/Iris26983COnFinalRgbaGainCarrier.java', 'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/Iris26983COnGlAhbBinding.java', 'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/Iris26983COnGpuFinalRenderer.java', 'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/Iris26983COnJpegPublisher.java', 'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/Iris26983COnUltraHdr.java', 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/Iris26983DirectGeometry.java', 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/Iris26983DirectPreviewView.java']

def fail(msg):raise RuntimeError('26983 BLOCKED: '+str(msg))
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
 a=parse(R/'26983_BASE_26982_FULL_APP.sha256');b=parse(R/'26983_EXPECTED_FULL_APP.sha256')
 changed=set((R/'26983_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
 added=set((R/'26983_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
 modified=set((R/'26983_MODIFIED_ORIGINAL_PATHS.txt').read_text().splitlines())
 deleted=set((R/'26983_DELETED_RUNTIME_PATHS.txt').read_text().splitlines())
 if (len(a),len(b),len(changed),len(added),len(modified),len(deleted))!=(NBASE,NFILES,NCHANGE,NADDED,NMODIFIED,NDELETED):fail('count/protected source regression')
 if changed!=added|modified or added&set(a) or modified-set(a) or set(b)!=(set(a)|added) or deleted:fail('unexpected runtime change/deletion')
 if {p for p in set(a)&set(b) if a[p]!=b[p]}!=modified:fail('original source edits outside allowlist')
 protected={p:h for p,h in a.items() if p not in changed}
 if len(protected)!=NPROTECTED or protected!=parse(R/'26983_PROTECTED_SOURCE.sha256'):fail('protected source failed')
 if sha(R/'26982_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml')!=WORKFLOW_SHA or sha(R/'26982_SUCCESSFUL_EXECUTED_BUILDER_REFERENCE.py')!=BUILDER_SHA:fail('26982 actual executed reference changed')
 if (R/'handoff_payload_26983/app/version.properties').read_text()!='VERSION_MAJOR=0\nVERSION_MINOR=9726440\nVERSION_NAME=0.9726983\nVERSION_BUILD=26983\n':fail('26983 version not exact')
 allowed_modified=set(json.loads((R/'26983_AUTHORITY_AND_SCOPE.json').read_text())['allowed_modified_exact'])
 if allowed_modified!=modified:fail('changed original paths not explicit')
 if modified!=set(ALLOWED_MODIFIED) or added!=set(ALLOWED_ADDED):fail('new scope not exact')
 if a['app/src/main/java/com/particlesdevs/photoncamera/util/SimpleStorageHelper.java']!=b['app/src/main/java/com/particlesdevs/photoncamera/util/SimpleStorageHelper.java']:fail('A/B gallery changed')
 return changed,a,b

def seal():
 changed,a,b=scope();wf='.github/workflows/build-26983-change-aware.yml';trigger='TRIGGER_26983.txt'
 expect=set(FILES)|{wf,trigger}|{'handoff_payload_26983/'+p for p in changed}
 sealed={}
 for line in (R/'26983_HANDOFF_HASHES.sha256').read_text().splitlines():
  try:h,p=line.split('  ',1)
  except ValueError:fail('bad handoff hash seal')
  if p in sealed or not (R/p).is_file() or sha(R/p)!=h:fail('missing/tampered handoff file '+p)
  sealed[p]=h
 if set(sealed)!=expect:fail('missing/extra handoff file set '+str(sorted(set(sealed)^expect)[:10]))
 stages=[(R/f'26983_STAGE_{i}_UPLOAD_PATHS.txt').read_text().splitlines() for i in (1,2,3)]
 if stages[0]!=sorted((expect|{'26983_HANDOFF_HASHES.sha256'})-{wf,trigger}) or stages[1]!=[wf] or stages[2]!=[trigger]:fail('three upload stages not strict')
 payload=R/'handoff_payload_26983'
 if {p.relative_to(payload).as_posix() for p in payload.rglob('*') if p.is_file()}!=changed:fail('payload missing/extra')
 for p in changed:
  if sha(payload/p)!=b[p]:fail('source input tampering '+p)
 if sha(R/'.github/workflows/build-26983-change-aware.yml')!=sealed[wf]:fail('workflow after seal changed')
 subprocess.run([sys.executable,'-S','test_26983_workflow_refs.py'],cwd=R,check=True)
 print(f'PASS 26983 three-stage SHA seal, {NPROTECTED} protected, {NCHANGE} source delta')

def fetch():
 seal();token=os.getenv('GITHUB_TOKEN','')
 if not token or os.getenv('GITHUB_REPOSITORY')!=REPO or os.getenv('GITHUB_REF_NAME')!=BRANCH:fail('Actions credentials/target branch unavailable')
 def get(endpoint):
  req=urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+endpoint,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'})
  with urllib.request.urlopen(req,timeout=120) as resp:return json.load(resp)
 run=get('actions/runs/'+str(RUN));art=get('actions/artifacts/'+str(ART_ID))
 if run.get('id')!=RUN or run.get('conclusion')!='success' or run.get('head_sha')!=COMMIT or run.get('head_branch')!=BRANCH:fail('26982 Actions run not successful/exact')
 if art.get('id')!=ART_ID or art.get('expired') or art.get('digest')!='sha256:'+ART_SHA or art.get('workflow_run',{}).get('id') not in (RUN,None):fail('26982 artifact identity/published digest')
 TMP.mkdir(parents=True,exist_ok=True)
 subprocess.run(['curl','--fail','--location','--retry','3','--silent','--show-error','-H','Authorization: Bearer '+token,'-H','Accept: application/vnd.github+json',f'https://api.github.com/repos/{REPO}/actions/artifacts/{ART_ID}/zip','-o',str(ART)],check=True)
 if sha(ART)!=ART_SHA:fail('downloaded successful 26982 ZIP mismatch')
 print('PASS exact successful 26982 Actions artifact fetched')

def prior_zip():
 if not ART.is_file() or sha(ART)!=ART_SHA:fail('successful 26982 ZIP inaccessible or wrong hash')
 return zipfile.ZipFile(ART)
def safe_extract_tar(data,dest):
 with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as t:
  for m in t:
   path=pathlib.PurePosixPath(m.name)
   if not m.isfile() or not path.parts or path.parts[0]!='app' or path.is_absolute() or '..' in path.parts or m.issym() or m.islnk():fail('unsafe 26982 compiled TAR entry '+m.name)
  t.extractall(dest,filter='data')

def prepare_base():
 seal()
 for folder in (BASE,CAND):
  if folder.exists():shutil.rmtree(folder)
 BASE.mkdir(parents=True)
 with prior_zip() as z:
  if z.testzip():fail('26982 ZIP CRC invalid')
  def get(name):
   p='photon_26982_outputs/'+name
   if p not in z.namelist():fail('26982 successful compiled receipt missing '+p)
   return z.read(p)
  src=get('26982_candidate_app_source.tar.gz')
  if hashlib.sha256(src).hexdigest()!=TAR_SHA or get('26982_candidate_app_source.tar.gz.sha256')!=f'{TAR_SHA}  26982_candidate_app_source.tar.gz\n'.encode():fail('26982 actual compiled TAR mismatch')
  if get('26982_EXPECTED_FULL_APP.sha256')!=(R/'26983_BASE_26982_FULL_APP.sha256').read_bytes() or get('26982_PREBUILD_SEALED_APP.sha256')!=(R/'26983_BASE_26982_FULL_APP.sha256').read_bytes():fail('compiled source manifest authority differs')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build_26982_incremental.py')).hexdigest()!=BUILDER_SHA or BUILDER_SHA not in get('26982_ACTUAL_EXECUTED_BUILDER.sha256').decode():fail('successful executed builder not pinned')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build-26982-change-aware.yml')).hexdigest()!=WORKFLOW_SHA or WORKFLOW_SHA not in get('26982_ACTUAL_EXECUTED_WORKFLOW.sha256').decode():fail('successful executed workflow not pinned')
  if PRIOR_APK_NAME not in z.namelist() or PRIOR_APK_SHA not in get('26982_APK.sha256').decode() or hashlib.sha256(z.read(PRIOR_APK_NAME)).hexdigest()!=PRIOR_APK_SHA:fail('successful 26982 APK identity')
  identity=get('26982_ACTIONS_IDENTITY.txt').decode()
  if 'git_sha='+COMMIT not in identity or 'github_run_id='+str(RUN) not in identity:fail('26982 Actions job identity')
  compiler=get('26982_COMPILER_STATUS.txt').decode()
  for phrase in ('REAL PINNED GLSL COMPILE: PASS','REAL SPIR-V VALIDATION/OPTIMIZATION: PASS','REAL KOTLIN COMPILE: PASS','REAL JAVA COMPILE: PASS','REAL TWO-ABI NDK/CMake COMPILE: PASS','REAL ANDROID Gradle :app:assembleDebug: PASS','RUNTIME SOURCE INVARIANCE: PASS'):
   if phrase not in compiler:fail('26982 compiler proof absent: '+phrase)
  for task in (':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL'):
   if 'PASS '+task not in get('26982_REAL_GRADLE_TASKS.txt').decode():fail('26982 predecessor Gradle task absent: '+task)
  safe_extract_tar(src,BASE)
 exact(BASE,'26983_BASE_26982_FULL_APP.sha256','actual successful 26982 compiled source')
 shutil.copytree(BASE,CAND)
 changed,_,b=scope()
 for p in sorted(changed):
  dest=CAND/p;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/'handoff_payload_26983'/p,dest)
 exact(CAND,'26983_EXPECTED_FULL_APP.sha256','exact 26983 isolated candidate')
 if not (R/'gradlew').is_file() or not (R/'app/build.gradle').is_file():fail('live checkout missing real Gradle')
 if (R/'app/src').exists():shutil.rmtree(R/'app/src')
 shutil.copytree(BASE/'app/src',R/'app/src')
 shutil.copyfile(BASE/'app/version.properties',R/'app/version.properties')
 shutil.copyfile(BASE/'app/build.gradle',R/'app/build.gradle')
 if (R/'app/.cxx').exists():shutil.rmtree(R/'app/.cxx')
 exact(R,'26983_BASE_26982_FULL_APP.sha256','historical preflight source restored')
 # Exact historical checks run against actual successful 26982 source.
 subprocess.run([sys.executable,'-S','test_26982_source.py','--live'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26982_settings_java.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26982_integration_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26975_v5_asset_host.py','--live'],cwd=R,check=True)
 # V10/V4 intentionally pin the pre-26982 bridge. Replay unchanged legacy tests
 # on their sealed historical payload, never on the deliberately evolved bridge.
 # Exact 26982 live source is verified above; current source/host guards run below.
 subprocess.run([sys.executable,'-S','build_26975_incremental.py','seal'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26975_v10_minimal_core.py','--payload'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26975_v4_capture_host.py','--root',str(R/'handoff_payload_26975/app')],cwd=R,check=True)
 # Preserve the full live V10 core and shader reachability checks against an
 # isolated copy of the exact predecessor, substituting only its historical
 # bridge (already verified by the historical seal) for the old bridge pin.
 import tempfile
 with tempfile.TemporaryDirectory(prefix='26983_v10_') as td:
  t=pathlib.Path(td);shutil.copytree(R/'app',t/'app',ignore=shutil.ignore_patterns('build','.cxx'))
  for name in ('test_26975_v10_minimal_core.py','26975_V10_MINIMAL_LUT_REACHABILITY_PROOF.json','26975_V6_CURRENT_SHADER_INVENTORY.json'):
   shutil.copyfile(R/name,t/name)
  bridge='app/src/main/java/com/hinnka/mycamera/processor/experimentc/Iris26975CPinnedDonorProEngine.kt'
  shutil.copyfile(R/'handoff_payload_26975'/bridge,t/bridge)
  # 26982 deliberately evolved the encoder for shared EXIF. The unchanged V10 test
  # expects its historical exact bytes; replay them only in this temporary fixture.
  encoder='app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/gallery/Jpeg444ExportEncoder.kt'
  shutil.copyfile(R/'handoff_payload_26975'/encoder,t/encoder)
  subprocess.run([sys.executable,'-S','test_26975_v10_minimal_core.py','--live'],cwd=t,check=True)
 # No creative LUT may enter the actual successor bridge.
 for root in (BASE,CAND):
  bridge=(root/'app/src/main/java/com/hinnka/mycamera/processor/experimentc/Iris26975CPinnedDonorProEngine.kt').read_text()
  if any(x in bridge for x in ('LutImageProcessor','applyLutStack','LutConfig','samplerExternalOES')):fail('unexpected creative LUT bridge')
 exact(R,'26983_BASE_26982_FULL_APP.sha256','live predecessor unchanged after historical fixture replay')
 subprocess.run([sys.executable,'-S','verify_26982_v6_current_glsl.py','--audit'],cwd=R,check=True)
 OUT.mkdir(parents=True,exist_ok=True)
 (OUT/'26983_SOURCE_SCOPE.txt').write_text(f'26982 Actions={RUN} commit={COMMIT} artifact={ART_ID} artifact_zip_sha={ART_SHA} actual_compiled_source_tar_sha={TAR_SHA}\nactual_runner_sha={BUILDER_SHA} actual_workflow_sha={WORKFLOW_SHA} prior_apk_sha={PRIOR_APK_SHA}\nbase={NBASE} candidate={NFILES} changes={NCHANGE} modified={NMODIFIED} added={NADDED} protected={NPROTECTED} deleted={NDELETED}\n'+''.join(p+'\n' for p in sorted(changed)))
 subprocess.run([sys.executable,'-S','test_26983_integrated_host.py','--base',str(BASE),'--candidate',str(CAND)],cwd=R,check=True)
 print('PASS 26982 compiled baseline reconstructed; isolated 26983 candidate ready')

def install():
 seal();exact(BASE,'26983_BASE_26982_FULL_APP.sha256','26982 baseline before install')
 exact(CAND,'26983_EXPECTED_FULL_APP.sha256','26983 frozen candidate before install')
 old=OUT/'26982_SUCCESSFUL_REAL_GLSL_SPIRV_COMPILER.txt'
 # Historical 26904 checks have been run; require predecessor successful Actions compiler receipt too.
 with prior_zip() as z:
  source=z.read('photon_26982_outputs/26982_REAL_GLSL_SPIRV_COMPILER.txt').decode()
  if 'PASS actual 26974 24/24 C GLES' not in source or 'PASS inherited historical 24/24 and actual current 151/151 26982 donor/Iris C shader compilation' not in source:fail('26982 real pinned GLSL/SPIR-V receipt missing')
 (OUT/'26982_SUCCESSFUL_REAL_GLSL_SPIRV_COMPILER.txt').write_text(source)
 shutil.rmtree(R/'app/src');shutil.copytree(CAND/'app/src',R/'app/src')
 shutil.copyfile(CAND/'app/version.properties',R/'app/version.properties')
 shutil.copyfile(CAND/'app/build.gradle',R/'app/build.gradle')
 exact(R,'26983_EXPECTED_FULL_APP.sha256','live installed 26983 SHA source')
 print('PASS installed exact 26983 C-only Pro Sabre source; production unapproved')

def regress():
 seal();exact(R,'26983_EXPECTED_FULL_APP.sha256','26983 live protected runtime')
 subprocess.run([sys.executable,'-S','test_26983_source.py','--live'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26982_integration_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26983_settings_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26981_integration_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26979_integration_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26978_integration_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26977_integration_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26976_capture_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26975_gallery_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','verify_26983_v6_current_glsl.py','--audit'],cwd=R,check=True)
 print('PASS live independent C exposure optimizer, exact frame replacement, tuning, protected A/B source invariance')

def stage_native():
 seal()
 with prior_zip() as z:
  with zipfile.ZipFile(io.BytesIO(z.read(PRIOR_APK_NAME))) as apk:
   if apk.testzip():fail('26982 published APK CRC')
   for p,want in NATIVE_SHA.items():
    data=apk.read(p)
    if hashlib.sha256(data).hexdigest()!=want:fail('successful native ABI hash regression '+p)
    dest=R/'app/build/verified_rawlens26931/jniLibs'/p.removeprefix('lib/')
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    if sha(dest)!=want:fail('staged native binary differs '+p)
 print('PASS exact successful 26982 dual ABI RawLens native binaries')

def verify_compiled():
 regress();success=OUT/'26982_SUCCESSFUL_REAL_GLSL_SPIRV_COMPILER.txt'
 current=OUT/'26983_REAL_GLSL_SPIRV_COMPILER.txt'
 if not success.is_file() or 'PASS actual 26974 24/24 C GLES' not in success.read_text() or 'PASS inherited historical 24/24 and actual current 151/151 26982 donor/Iris C shader compilation' not in success.read_text():fail('26982 actual successful shader proof missing')
 if not current.is_file() or 'PASS actual 26974 24/24 C GLES' not in current.read_text() or 'PASS inherited historical 24/24 and actual current {SHADER_COUNT}/{SHADER_COUNT} 26983 donor/Iris C shader compilation'.format(SHADER_COUNT=SHADER_COUNT) not in current.read_text():fail('current Actions 24/24 + 26983 151/151 shader recompilation proof missing')
 con=OUT/'26983_CON_REAL_GLSL_SPIRV_COMPILER.txt'
 if not con.is_file() or 'PASS 26983 C ON 13/13 static shader stages real GLSL/SPIR-V opt/val' not in con.read_text():fail('new C ON real shader compiler proof missing')
 v6=OUT/'26983_V6_CURRENT_STATIC_GLSL_SPIRV_COMPILER.txt'
 if not v6.is_file() or f'PASS 26983 physical current {SHADER_COUNT}/{SHADER_COUNT} static donor/Iris C ESSL GLSL + SPIR-V opt/val' not in v6.read_text():fail('current C shader parser and SPIR-V optimizer must actually pass')
 for p,want in NATIVE_SHA.items():
  if sha(R/'app/build/verified_rawlens26931/jniLibs'/p.removeprefix('lib/'))!=want:fail('staged dual ABI LKR mismatch')
 for p,want in DONOR_SHA.items():
  if sha(R/'app/src/main/jniLibs'/p.removeprefix('lib/'))!=want:fail('original pinned donor sidecar mismatch')
 OUT.mkdir(exist_ok=True)
 (OUT/'26983_PREBUILD_SEALED_APP.sha256').write_bytes((R/'26983_EXPECTED_FULL_APP.sha256').read_bytes())
 print('PASS prebuild source seal + current actual pinned SPIR-V/GLSL + dual ABI native input')

def finalize():
 regress()
 if (OUT/'26983_PREBUILD_SEALED_APP.sha256').read_bytes()!=(R/'26983_EXPECTED_FULL_APP.sha256').read_bytes():fail('prebuild SHA seal absent')
 log=(OUT/'26983_gradle_assemble.log').read_text(errors='replace')
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
   for lib in ('libiris26983conlkr.so','libiris26983conjpeg.so'):
    if f'lib/{abi}/{lib}' not in apk.namelist():fail('C ON native link missing '+abi+'/'+lib)
 exact(R,'26983_EXPECTED_FULL_APP.sha256','actual assembled 26983 source unchanged')
 OUT.mkdir(exist_ok=True)
 (OUT/'26983_COMPILER_STATUS.txt').write_text('REAL PINNED GLSL COMPILE: PASS\nREAL SPIR-V VALIDATION/OPTIMIZATION: PASS\nREAL KOTLIN COMPILE: PASS\nREAL JAVA COMPILE: PASS\nREAL TWO-ABI NDK/CMake COMPILE: PASS\nREAL ANDROID Gradle :app:assembleDebug: PASS\nRUNTIME SOURCE INVARIANCE: PASS (2395 protected, 18 modified, 73 added)\nEXPERIMENT C CONTROLLED DEVICE TRIAL: ENABLED\nEXPERIMENT C PRODUCTION READY: NO\nDEVICE IQ VALIDATION: NOT RUN\n')
 (OUT/'26983_REAL_GRADLE_TASKS.txt').write_text(''.join('PASS '+p+'\n' for p in tasks))
 (OUT/'26983_APK.sha256').write_text(sha(R/APKNAME)+'  '+APKNAME+'\n')
 wf=R/'.github/workflows/build-26983-change-aware.yml'
 (OUT/'26983_ACTUAL_EXECUTED_BUILDER.sha256').write_text(sha(R/'build_26983_incremental.py')+'  build_26983_incremental.py\n')
 (OUT/'26983_ACTUAL_EXECUTED_WORKFLOW.sha256').write_text(sha(wf)+'  '+wf.relative_to(R).as_posix()+'\n')
 (OUT/'26983_ACTIONS_IDENTITY.txt').write_text('git_sha='+os.getenv('GITHUB_SHA','NOT_IN_ACTIONS')+'\ngithub_run_id='+os.getenv('GITHUB_RUN_ID','NOT_IN_ACTIONS')+'\n')
 for item in ('26983_BASE_26982_FULL_APP.sha256','26983_EXPECTED_FULL_APP.sha256','26983_PROTECTED_SOURCE.sha256','26983_CHANGED_RUNTIME_ALLOWLIST.txt','26983_ADDED_RUNTIME_PATHS.txt','26983_MODIFIED_ORIGINAL_PATHS.txt','26983_DELETED_RUNTIME_PATHS.txt','26983_AUTHORITY_AND_SCOPE.json'):
  shutil.copy2(R/item,OUT/item)
 shutil.copy2(R/'build_26983_incremental.py',OUT/'ACTUAL_EXECUTED_build_26983_incremental.py')
 shutil.copy2(wf,OUT/'ACTUAL_EXECUTED_build-26983-change-aware.yml')
 with (OUT/'26983_candidate_app_source.tar.gz').open('wb') as f:
  with gzip.GzipFile(filename='',mode='wb',compresslevel=1,mtime=0,fileobj=f) as gz:
   with tarfile.open(fileobj=gz,mode='w') as t:
    for rel in sorted(parse(R/'26983_EXPECTED_FULL_APP.sha256')):
     path=R/rel;m=t.gettarinfo(str(path),arcname=rel);m.uid=m.gid=0;m.uname=m.gname='';m.mtime=0
     with path.open('rb') as opened:t.addfile(m,opened)
 (OUT/'26983_candidate_app_source.tar.gz.sha256').write_text(sha(OUT/'26983_candidate_app_source.tar.gz')+'  26983_candidate_app_source.tar.gz\n')
 print('PASS real compiled 26983 source/APK SHA proof; IQ not proven until on-device')

if __name__=='__main__':
 try:
  parser=argparse.ArgumentParser();parser.add_argument('command',choices=('seal','fetch','prepare-base','install','regress','stage-native','verify-compiled','finalize'));args=parser.parse_args()
  globals()[args.command.replace('-','_')]()
 except Exception as e:print('26983 BUILD ERROR:',e,file=sys.stderr);sys.exit(1)
