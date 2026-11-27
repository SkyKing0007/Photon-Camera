#!/usr/bin/env python3
"""26998 guarded successor to successful 26997. C OFF bjzhou 1.29.1 denoise and color only; real compiler gates retained."""
import argparse,gzip,hashlib,io,json,os,pathlib,re,shutil,subprocess,sys,tarfile,urllib.request,zipfile
R=pathlib.Path(__file__).resolve().parent
SHADER_COUNT=340 # exact current 26998 physical required shader inventory; not skip
TMP=R/'.photon_26998_work';OUT=R/'photon_26998_outputs'
ART=TMP/'26997-success.zip';BASE=TMP/'authority_26997';CAND=TMP/'candidate_26998'
REPO='SkyKing0007/Photon-Camera';BRANCH='experimental-clean-photon-rebuild'
RUN=46017752224;COMMIT='5acd9b48be7800db762293da8aaac01e67684265';ART_ID=15207204004
ART_SHA='ab050c4157a01770e3abcf84b7626fd66751898b5204f268d26cf836b425d315'
TAR_SHA='8b6d707e406a242d2c24e5c2dfc02c2e9b9bf447def3bf060498c56d93ce4a1e'
BUILDER_SHA='1e2bed2fa6f43aed1c1fa48b76f8cd9e03a65339c2dda7db589e38ec06837d98'
WORKFLOW_SHA='ba2b9f98f6e6f216924ff4cdde8c7ffa5a9c0c10872903f8f4b6c4fe97df31ef'
PRIOR_APK_SHA='e14248a54a19ac104764d24e0cf0b97eaf885681c322d6886174fd9dbdf5cefd'
PRIOR_APK_NAME='IrisCamera-0.9726997-26997-iris-rawr-debug.apk'
APKNAME='IrisCamera-0.9726998-26998-iris-rawr-debug.apk'
NBASE=2676;NFILES=2708;NCHANGE=47;NADDED=32;NMODIFIED=15;NDELETED=0;NPROTECTED=2661
NATIVE_SHA={'lib/arm64-v8a/liblkrpipeline.so': '037a5f62649dcac7034c789c8e7ea2f250ca818d1c1c364e09a59f6897530105', 'lib/arm64-v8a/libsrpipeline.so': 'f87cc70ad12a69345392a4eb73b6ec33739577ce8c39b7a4916180c344f67069', 'lib/armeabi-v7a/liblkrpipeline.so': '9297eb7c58ca242986bced32bf773dcc8d16c3beaa33c26142b152c585957b03', 'lib/armeabi-v7a/libsrpipeline.so': '48788035080e66efa63b693e35f0587d2f02e851b818c367f3915b6154b47d68'}
DONOR_SHA={
 'lib/arm64-v8a/libiris26972c129.so':'a70ba1b1e4e8c856b07c828bef4141d0097d19013a49f77c1f59e41ee0a52cae',
 'lib/arm64-v8a/libi72.so':'ab0698a4a7006564e22447402468a9e1ca349a9017180bc7767c4feec58e0331',
}
FILES=['26997_SUCCESSFUL_EXECUTED_BUILDER_REFERENCE.py', '26997_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml', '26998_ADDED_RUNTIME_PATHS.txt', '26998_AUTHORITY_AND_SCOPE.json', '26998_BASE_26997_FULL_APP.sha256', '26998_CHANGED_RUNTIME_ALLOWLIST.txt', '26998_COMMIT_MESSAGE.txt', '26998_DELETED_RUNTIME_PATHS.txt', '26998_EXPANDED_SHADER.sha256', '26998_EXPECTED_FULL_APP.sha256', '26998_FORWARD_FULLINDEX.patch', '26998_LEGACY_NATIVE.sha256', '26998_LOCAL_26997_REGRESSION.log', '26998_LOCAL_HOST.log', '26998_LOCAL_KOTLIN_SYNTAX.log', '26998_LOCAL_MESA_GLES.log', '26998_LOCAL_PATCH.log', '26998_MODIFIED_ORIGINAL_PATHS.txt', '26998_NATIVE_SHADER_INVENTORY.json', '26998_PROTECTED_SOURCE.sha256', '26998_REUSED_EXECUTABLES.json', '26998_ROLLBACK_FULLINDEX.patch', '26998_SHADER_KOTLIN_FILES.txt', '26998_SHADER_OBJECTS.txt', '26998_STAGE_1_UPLOAD_PATHS.txt', '26998_STAGE_2_UPLOAD_PATHS.txt', '26998_STAGE_3_UPLOAD_PATHS.txt', '26998_UPSTREAM_SOURCE_MAP.json', '26998_V6_CURRENT_SHADER_INVENTORY.json', 'Emit26998.kt', 'Parse26998Java.java', 'README_PHOTON_26998.md', 'Test26998Snr.kt', 'build_26998_incremental.py', 'compile_26998_all.py', 'compile_26998_expanded.py', 'compile_26998_shaders.sh', 'compile_26998_shadow_expanded.py', 'test_26998_host.py', 'test_26998_latest_preflight.py', 'test_26998_patches.py', 'test_26998_sealed_negatives.py', 'test_26998_source.py', 'test_26998_workflow_refs.py', 'verify_26998_native_glsl.py', 'verify_26998_v6_current_glsl.py']
ALLOWED_MODIFIED=['app/src/main/java/com/hinnka/mycamera/processor/Iris26972CCamera2ShutterSession.kt', 'app/src/main/java/com/hinnka/mycamera/processor/Iris26972CCaptureToGallery.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/Iris26975CPinnedDonorProEngine.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/camera/CameraMetadataReader.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/processor/GlesMgcRawFusion.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/processor/GlesMgcRawSabreProcessor.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/processor/MultiFrameStacker.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/RawDemosaicProcessor.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/RawMetadata.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/utils/RawProcessor.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/utils/SuperResolutionDngWriter.kt', 'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java', 'app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java', 'app/src/main/res/xml/preferences.xml', 'app/version.properties']
ALLOWED_ADDED=['app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/processor/GlesMgcRawChromaReconstructionShaders.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/processor/GlesMgcRawHotPixelShaders.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/processor/GlesMgcSpatialNoiseModelShaders.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/processor/GlesMgcSpatialNoiseReductionShaders.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/processor/GlesMgcSpatialNoiseStrengthShader.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/processor/GlesMgcSpatialSignalShaders.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/processor/Iris26998GlesMgcRawSpatialShaders.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/processor/Iris26998GlesMgcRawSpatialStacker.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/processor/Iris26998GlesMgcSabreResolveShaders.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/processor/Iris26998GlesMgcSpatialRgbMergeShaders.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/processor/Iris26998MgcSpatialDiagnosticGeometry.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/processor/Iris26998MgcSpatialStrengthAtlasLayout.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/processor/MgcSpatialNoiseStatistics.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/GlesMgcBitmapStrengthMapShader.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/GlesMgcChromaDenoiseShaders.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/GlesMgcDenoise.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/GlesMgcLumaDenoiseShaders.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/GlesMgcMeasureMoireShaders.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/GlesMgcRawNoiseTiles.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/Iris26998DngSdkColorSpec.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/Iris26998ForwardMatrixPolicy.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/Iris26998MgcGpuDenoiseConfig.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/Iris26998RawColorCalibrationPolicy.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/Iris26998RawHotPixelShaders.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/MgcChromaNoiseModel.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/MgcLumaNoiseModel.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/MgcRawMaxDenoiseTuning.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/MgcRawStackNoiseObservation.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/OplusIspColorTransform.kt', 'app/src/main/java/com/particlesdevs/photoncamera/settings/Iris26998CDenoiseSettings.java', 'app/src/main/java/com/particlesdevs/photoncamera/ui/settings/custompreferences/Iris26998CAdvancedDenoisePreference.java', 'app/src/main/res/layout/preference_26998_c_mgc_band1_seekbar.xml']

def fail(msg):raise RuntimeError('26998 BLOCKED: '+str(msg))
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
 a=parse(R/'26998_BASE_26997_FULL_APP.sha256');b=parse(R/'26998_EXPECTED_FULL_APP.sha256')
 changed=set((R/'26998_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
 added=set((R/'26998_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
 modified=set((R/'26998_MODIFIED_ORIGINAL_PATHS.txt').read_text().splitlines())
 deleted=set((R/'26998_DELETED_RUNTIME_PATHS.txt').read_text().splitlines())
 if (len(a),len(b),len(changed),len(added),len(modified),len(deleted))!=(NBASE,NFILES,NCHANGE,NADDED,NMODIFIED,NDELETED):fail('count/protected source regression')
 if changed!=added|modified or added&set(a) or modified-set(a) or set(b)!=(set(a)|added) or deleted:fail('unexpected runtime change/deletion')
 if {p for p in set(a)&set(b) if a[p]!=b[p]}!=modified:fail('original source edits outside allowlist')
 protected={p:h for p,h in a.items() if p not in changed}
 if len(protected)!=NPROTECTED or protected!=parse(R/'26998_PROTECTED_SOURCE.sha256'):fail('protected source failed')
 if sha(R/'26997_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml')!=WORKFLOW_SHA or sha(R/'26997_SUCCESSFUL_EXECUTED_BUILDER_REFERENCE.py')!=BUILDER_SHA:fail('26997 actual executed reference changed')
 if (R/'handoff_payload_26998/app/version.properties').read_text()!='VERSION_MAJOR=0\nVERSION_MINOR=9726440\nVERSION_NAME=0.9726998\nVERSION_BUILD=26998\n':fail('26998 version not exact')
 allowed_modified=set(json.loads((R/'26998_AUTHORITY_AND_SCOPE.json').read_text())['allowed_modified_exact'])
 if allowed_modified!=modified:fail('changed original paths not explicit')
 if modified!=set(ALLOWED_MODIFIED) or added!=set(ALLOWED_ADDED):fail('new scope not exact')
 legacy=parse(R/'26998_LEGACY_NATIVE.sha256')
 if len(legacy)!=6 or any(a.get(p)!=h for p,h in legacy.items()) or any(b.get(p)!=h for p,h in legacy.items() if p not in modified):fail('exact predecessor C native source authority mismatch')
 if a['app/src/main/java/com/particlesdevs/photoncamera/util/SimpleStorageHelper.java']!=b['app/src/main/java/com/particlesdevs/photoncamera/util/SimpleStorageHelper.java']:fail('A/B gallery changed')
 return changed,a,b

def seal():
 changed,a,b=scope();wf='.github/workflows/build-26998-change-aware.yml';trigger='TRIGGER_26998.txt'
 expect=set(FILES)|{wf,trigger}|{'handoff_payload_26998/'+p for p in changed}
 sealed={}
 for line in (R/'26998_HANDOFF_HASHES.sha256').read_text().splitlines():
  try:h,p=line.split('  ',1)
  except ValueError:fail('bad handoff hash seal')
  if p in sealed or not (R/p).is_file() or sha(R/p)!=h:fail('missing/tampered handoff file '+p)
  sealed[p]=h
 if set(sealed)!=expect:fail('missing/extra handoff file set '+str(sorted(set(sealed)^expect)[:10]))
 stages=[(R/f'26998_STAGE_{i}_UPLOAD_PATHS.txt').read_text().splitlines() for i in (1,2,3)]
 if stages[0]!=sorted((expect|{'26998_HANDOFF_HASHES.sha256'})-{wf,trigger}) or stages[1]!=[wf] or stages[2]!=[trigger]:fail('three upload stages not strict')
 payload=R/'handoff_payload_26998'
 if {p.relative_to(payload).as_posix() for p in payload.rglob('*') if p.is_file()}!=changed:fail('payload missing/extra')
 for p in changed:
  if sha(payload/p)!=b[p]:fail('source input tampering '+p)
 if sha(R/'.github/workflows/build-26998-change-aware.yml')!=sealed[wf]:fail('workflow after seal changed')
 subprocess.run([sys.executable,'-S','test_26998_workflow_refs.py'],cwd=R,check=True)
 if os.getenv('GITHUB_ACTIONS')=='true':
  from compile_26998_all import verify_reused,verify_compiler_transform
  verify_reused();verify_compiler_transform(R/'compile_26989_shaders.sh')
 print(f'PASS 26998 three-stage SHA seal, {NPROTECTED} protected, {NCHANGE} source delta')

def fetch():
 seal();token=os.getenv('GITHUB_TOKEN','')
 if not token or os.getenv('GITHUB_REPOSITORY')!=REPO or os.getenv('GITHUB_REF_NAME')!=BRANCH:fail('Actions credentials/target branch unavailable')
 def get(endpoint):
  req=urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+endpoint,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'})
  with urllib.request.urlopen(req,timeout=120) as resp:return json.load(resp)
 run=get('actions/runs/'+str(RUN));art=get('actions/artifacts/'+str(ART_ID))
 if run.get('id')!=RUN or run.get('conclusion')!='success' or run.get('head_sha')!=COMMIT or run.get('head_branch')!=BRANCH:fail('26997 Actions run not successful/exact')
 if art.get('id')!=ART_ID or art.get('expired') or art.get('digest')!='sha256:'+ART_SHA or art.get('workflow_run',{}).get('id') not in (RUN,None):fail('26997 artifact identity/published digest')
 TMP.mkdir(parents=True,exist_ok=True)
 subprocess.run(['curl','--fail','--location','--retry','3','--silent','--show-error','-H','Authorization: Bearer '+token,'-H','Accept: application/vnd.github+json',f'https://api.github.com/repos/{REPO}/actions/artifacts/{ART_ID}/zip','-o',str(ART)],check=True)
 if sha(ART)!=ART_SHA:fail('downloaded successful 26997 ZIP mismatch')
 print('PASS exact successful 26997 Actions artifact fetched')

def prior_zip():
 if not ART.is_file() or sha(ART)!=ART_SHA:fail('successful 26997 ZIP inaccessible or wrong hash')
 return zipfile.ZipFile(ART)
def safe_extract_tar(data,dest):
 with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as t:
  for m in t:
   path=pathlib.PurePosixPath(m.name)
   if not m.isfile() or not path.parts or path.parts[0]!='app' or path.is_absolute() or '..' in path.parts or m.issym() or m.islnk():fail('unsafe 26997 compiled TAR entry '+m.name)
  t.extractall(dest,filter='data')

def recover():
 seal()
 for folder in (BASE,CAND):
  if folder.exists():shutil.rmtree(folder)
 BASE.mkdir(parents=True)
 with prior_zip() as z:
  if z.testzip():fail('26997 ZIP CRC invalid')
  def get(name):
   p='photon_26997_outputs/'+name
   if p not in z.namelist():fail('26997 successful compiled receipt missing '+p)
   return z.read(p)
  src=get('26997_candidate_app_source.tar.gz')
  if hashlib.sha256(src).hexdigest()!=TAR_SHA or get('26997_candidate_app_source.tar.gz.sha256')!=f'{TAR_SHA}  26997_candidate_app_source.tar.gz\n'.encode():fail('26997 actual compiled TAR mismatch')
  if get('26997_EXPECTED_FULL_APP.sha256')!=(R/'26998_BASE_26997_FULL_APP.sha256').read_bytes() or get('26997_PREBUILD_SEALED_APP.sha256')!=(R/'26998_BASE_26997_FULL_APP.sha256').read_bytes():fail('compiled source manifest authority differs')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build_26997_incremental.py')).hexdigest()!=BUILDER_SHA or BUILDER_SHA not in get('26997_ACTUAL_EXECUTED_BUILDER.sha256').decode():fail('successful executed builder not pinned')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build-26997-change-aware.yml')).hexdigest()!=WORKFLOW_SHA or WORKFLOW_SHA not in get('26997_ACTUAL_EXECUTED_WORKFLOW.sha256').decode():fail('successful executed workflow not pinned')
  if PRIOR_APK_NAME not in z.namelist() or PRIOR_APK_SHA not in get('26997_APK.sha256').decode() or hashlib.sha256(z.read(PRIOR_APK_NAME)).hexdigest()!=PRIOR_APK_SHA:fail('successful 26997 APK identity')
  identity=get('26997_ACTIONS_IDENTITY.txt').decode()
  if 'git_sha='+COMMIT not in identity or 'github_run_id='+str(RUN) not in identity:fail('26997 Actions job identity')
  compiler=get('26997_COMPILER_STATUS.txt').decode()
  for phrase in ('REAL PINNED GLSL COMPILE: PASS','REAL SPIR-V VALIDATION/OPTIMIZATION: PASS','REAL KOTLIN COMPILE: PASS','REAL JAVA COMPILE: PASS','REAL TWO-ABI NDK/CMake COMPILE: PASS','REAL ANDROID Gradle :app:assembleDebug: PASS','RUNTIME SOURCE INVARIANCE: PASS'):
   if phrase not in compiler:fail('26997 compiler proof absent: '+phrase)
  for task in (':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL'):
   if 'PASS '+task not in get('26997_REAL_GRADLE_TASKS.txt').decode():fail('26997 predecessor Gradle task absent: '+task)
  safe_extract_tar(src,BASE)
 exact(BASE,'26998_BASE_26997_FULL_APP.sha256','actual successful 26997 compiled source')
 shutil.copytree(BASE,CAND)
 changed,_,b=scope()
 for p in sorted(changed):
  dest=CAND/p;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/'handoff_payload_26998'/p,dest)
 exact(CAND,'26998_EXPECTED_FULL_APP.sha256','exact 26998 isolated candidate')
 print('PASS actual 26997 compiled authority and isolated 26998 candidate recovered')

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
 exact(R,'26998_BASE_26997_FULL_APP.sha256','actual 26997 live predecessor restored')
 subprocess.run([sys.executable,'-S','test_26998_latest_preflight.py'],cwd=R,check=True)
 OUT.mkdir(parents=True,exist_ok=True)
 changed,_,_=scope()
 (OUT/'26998_SOURCE_SCOPE.txt').write_text(f'26997 Actions={RUN} commit={COMMIT} artifact={ART_ID} artifact_zip_sha={ART_SHA} actual_compiled_source_tar_sha={TAR_SHA}\nactual_runner_sha={BUILDER_SHA} actual_workflow_sha={WORKFLOW_SHA} prior_apk_sha={PRIOR_APK_SHA}\nbase={NBASE} candidate={NFILES} changes={NCHANGE} modified={NMODIFIED} added={NADDED} protected={NPROTECTED} deleted={NDELETED}\n'+''.join(p+'\n' for p in sorted(changed)))
 print('PASS latest-only 26997 authority, sparse historical fixtures and predecessor settings and source tests')

def install():
 seal();exact(BASE,'26998_BASE_26997_FULL_APP.sha256','26997 baseline before install')
 exact(CAND,'26998_EXPECTED_FULL_APP.sha256','26998 frozen candidate before install')
 old=OUT/'26997_SUCCESSFUL_REAL_GLSL_SPIRV_COMPILER.txt'
 # Historical 26904 checks have been run; require predecessor successful Actions compiler receipt too.
 with prior_zip() as z:
  source=z.read('photon_26997_outputs/26997_REAL_GLSL_SPIRV_COMPILER.txt').decode()
  if 'PASS actual 26974 24/24 C GLES' not in source or 'PASS inherited historical 24/24 and actual current 299/299 26989 donor/Iris C shader compilation' not in source:fail('26997 real pinned GLSL/SPIR-V receipt missing')
 (OUT/'26997_SUCCESSFUL_REAL_GLSL_SPIRV_COMPILER.txt').write_text(source)
 with prior_zip() as z:
  con=z.read('photon_26997_outputs/26997_CON_REAL_GLSL_SPIRV_COMPILER.txt').decode()
  if 'PASS 26989 C ON 14/14 static shader stages real GLSL/SPIR-V opt/val' not in con:fail('26997 real C ON shader proof absent')
 (OUT/'26997_SUCCESSFUL_CON_REAL_GLSL_SPIRV_COMPILER.txt').write_text(con)
 with prior_zip() as z:
  native=z.read('photon_26997_outputs/26997_NATIVE_REAL_GLSL_SPIRV_COMPILER.txt').decode()
  if 'PASS 59/59 private Vulkan variants real compile/opt/val' not in native:fail('26997 real native shader proof absent')
 (OUT/'26997_SUCCESSFUL_NATIVE_REAL_GLSL_SPIRV_COMPILER.txt').write_text(native)
 shutil.rmtree(R/'app/src');shutil.copytree(CAND/'app/src',R/'app/src')
 shutil.copyfile(CAND/'app/version.properties',R/'app/version.properties')
 shutil.copyfile(CAND/'app/build.gradle',R/'app/build.gradle')
 exact(R,'26998_EXPECTED_FULL_APP.sha256','live installed 26998 SHA source')
 print('PASS installed exact 26998 C OFF bjzhou 1.29.1 denoise and color source; production unapproved')

def regress():
 seal();exact(R,'26998_EXPECTED_FULL_APP.sha256','26998 live protected runtime')
 subprocess.run([sys.executable,'-S','test_26998_source.py','--live'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26994_watermark_host.py'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26995_lkr_host.py'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26998_host.py'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','verify_26998_v6_current_glsl.py','--audit'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','verify_26998_native_glsl.py','--audit'],cwd=R,check=True)
 exact(R,'26998_EXPECTED_FULL_APP.sha256','26998 live after host tests')
 (OUT/'26998_HOST_TEST_SOURCE_SEAL.txt').write_text(sha(R/'26998_EXPECTED_FULL_APP.sha256')+'\n')

def verified_regress():
 seal();exact(R,'26998_EXPECTED_FULL_APP.sha256','26998 live protected runtime')
 if (OUT/'26998_HOST_TEST_SOURCE_SEAL.txt').read_text()!=sha(R/'26998_EXPECTED_FULL_APP.sha256')+'\n':fail('current host execution receipt missing')
 subprocess.run([sys.executable,'-S','test_26998_source.py','--live'],cwd=R,check=True)

def stage_native():
 seal()
 with prior_zip() as z:
  with zipfile.ZipFile(io.BytesIO(z.read(PRIOR_APK_NAME))) as apk:
   if apk.testzip():fail('26997 published APK CRC')
   for p,want in NATIVE_SHA.items():
    data=apk.read(p)
    if hashlib.sha256(data).hexdigest()!=want:fail('successful native ABI hash regression '+p)
    dest=R/'app/build/verified_rawlens26931/jniLibs'/p.removeprefix('lib/')
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    if sha(dest)!=want:fail('staged native binary differs '+p)
 print('PASS exact successful 26997 dual ABI RawLens native binaries')

def verify_compiled():
 verified_regress();from compile_26998_all import verify_receipts
 verify_receipts();success=OUT/'26997_SUCCESSFUL_REAL_GLSL_SPIRV_COMPILER.txt'
 current=OUT/'26998_REAL_GLSL_SPIRV_COMPILER.txt'
 if 'PASS 26989 C ON 14/14 static shader stages real GLSL/SPIR-V opt/val' not in (OUT/'26997_SUCCESSFUL_CON_REAL_GLSL_SPIRV_COMPILER.txt').read_text():fail('26997 predecessor C ON shader receipt missing')
 if not success.is_file() or 'PASS actual 26974 24/24 C GLES' not in success.read_text() or 'PASS inherited historical 24/24 and actual current 299/299 26989 donor/Iris C shader compilation' not in success.read_text():fail('26997 actual successful shader proof missing')
 if not current.is_file() or 'PASS actual 26974 24/24 C GLES' not in current.read_text() or 'PASS inherited historical 24/24 and actual current {SHADER_COUNT}/{SHADER_COUNT} 26989 donor/Iris C shader compilation'.format(SHADER_COUNT=SHADER_COUNT) not in current.read_text():fail('current Actions 24/24 + 26998 340/340 shader recompilation proof missing')
 con=OUT/'26998_CON_REAL_GLSL_SPIRV_COMPILER.txt'
 if not con.is_file() or 'PASS 26989 C ON 14/14 static shader stages real GLSL/SPIR-V opt/val' not in con.read_text():fail('new C ON real shader compiler proof missing')
 v6=OUT/'26998_V6_CURRENT_STATIC_GLSL_SPIRV_COMPILER.txt'
 if not v6.is_file() or f'PASS 26989 physical current {SHADER_COUNT}/{SHADER_COUNT} static donor/Iris C ESSL GLSL + SPIR-V opt/val' not in v6.read_text():fail('current C shader parser and SPIR-V optimizer must actually pass')
 for p,want in NATIVE_SHA.items():
  if sha(R/'app/build/verified_rawlens26931/jniLibs'/p.removeprefix('lib/'))!=want:fail('staged dual ABI LKR mismatch')
 for p,want in DONOR_SHA.items():
  if sha(R/'app/src/main/jniLibs'/p.removeprefix('lib/'))!=want:fail('original pinned donor sidecar mismatch')
 OUT.mkdir(exist_ok=True)
 (OUT/'26998_PREBUILD_SEALED_APP.sha256').write_bytes((R/'26998_EXPECTED_FULL_APP.sha256').read_bytes())
 if 'PASS 59/59 private Vulkan variants real compile/opt/val' not in (OUT/'26998_NATIVE_REAL_GLSL_SPIRV_COMPILER.txt').read_text():fail('missing actual private Vulkan compiler proof')
 if 'PASS 26998 expanded RAW adjustment pair original/310 GLSL and SPIR-V opt/val' not in (OUT/'26998_SHADOW_REAL_GLSL_SPIRV.txt').read_text():fail('missing new expanded shadow shader proof')
 if 'PASS exact 26989 runtime ESSL300 OES preview pair compile/link' not in (OUT/'26998_PREVIEW_REAL_GLSL.txt').read_text():fail('current real preview shader compile/link missing')
 print('PASS prebuild source seal + current actual pinned SPIR-V/GLSL + dual ABI native input')

def finalize():
 verified_regress();from compile_26998_all import verify_receipts
 verify_receipts()
 if (OUT/'26998_PREBUILD_SEALED_APP.sha256').read_bytes()!=(R/'26998_EXPECTED_FULL_APP.sha256').read_bytes():fail('prebuild SHA seal absent')
 log=(OUT/'26998_gradle_assemble.log').read_text(errors='replace')
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
    if any('Java_com_hinnka_mycamera_processor_Iris26985CLkrNative_'+m not in syms for m in ('nativeMerge','nativeSetDenoise','nativeFree','nativeSetNoiseModel','nativeRecordRawNoise')):fail('private JNI missing '+abi)
    interop=pathlib.Path(td)/'interop.so';interop.write_bytes(apk.read(f'lib/{abi}/libiris26983conlkr.so'))
    syms=subprocess.check_output(['readelf','-Ws',str(interop)],text=True)
    for method in ('nativePrepare','nativePublishRgba16f','nativePublishClipR16f'):
     if 'Java_com_hinnka_mycamera_processor_GlesIris26983COnLkrBridge_'+method not in syms:fail('C private interop JNI missing '+abi+'/'+method)
 exact(R,'26998_EXPECTED_FULL_APP.sha256','actual assembled 26998 source unchanged')
 OUT.mkdir(exist_ok=True)
 (OUT/'26998_COMPILER_STATUS.txt').write_text('REAL PINNED GLSL COMPILE: PASS\nREAL SPIR-V VALIDATION/OPTIMIZATION: PASS\nREAL KOTLIN COMPILE: PASS\nREAL JAVA COMPILE: PASS\nREAL TWO-ABI NDK/CMake COMPILE: PASS\nREAL ANDROID Gradle :app:assembleDebug: PASS\nRUNTIME SOURCE INVARIANCE: PASS (2661 protected, 15 modified, 32 added)\nEXPERIMENT C CONTROLLED DEVICE TRIAL: ENABLED\nEXPERIMENT C PRODUCTION READY: NO\nDEVICE IQ VALIDATION: NOT RUN\n')
 (OUT/'26998_REAL_GRADLE_TASKS.txt').write_text(''.join('PASS '+p+'\n' for p in tasks))
 (OUT/'26998_APK.sha256').write_text(sha(R/APKNAME)+'  '+APKNAME+'\n')
 wf=R/'.github/workflows/build-26998-change-aware.yml'
 (OUT/'26998_ACTUAL_EXECUTED_BUILDER.sha256').write_text(sha(R/'build_26998_incremental.py')+'  build_26998_incremental.py\n')
 (OUT/'26998_ACTUAL_EXECUTED_WORKFLOW.sha256').write_text(sha(wf)+'  '+wf.relative_to(R).as_posix()+'\n')
 (OUT/'26998_ACTIONS_IDENTITY.txt').write_text('git_sha='+os.getenv('GITHUB_SHA','NOT_IN_ACTIONS')+'\ngithub_run_id='+os.getenv('GITHUB_RUN_ID','NOT_IN_ACTIONS')+'\n')
 for item in ('26998_BASE_26997_FULL_APP.sha256','26998_EXPECTED_FULL_APP.sha256','26998_PROTECTED_SOURCE.sha256','26998_CHANGED_RUNTIME_ALLOWLIST.txt','26998_ADDED_RUNTIME_PATHS.txt','26998_MODIFIED_ORIGINAL_PATHS.txt','26998_DELETED_RUNTIME_PATHS.txt','26998_AUTHORITY_AND_SCOPE.json'):
  shutil.copy2(R/item,OUT/item)
 shutil.copy2(R/'build_26998_incremental.py',OUT/'ACTUAL_EXECUTED_build_26998_incremental.py')
 shutil.copy2(wf,OUT/'ACTUAL_EXECUTED_build-26998-change-aware.yml')
 with (OUT/'26998_candidate_app_source.tar.gz').open('wb') as f:
  with gzip.GzipFile(filename='',mode='wb',compresslevel=1,mtime=0,fileobj=f) as gz:
   with tarfile.open(fileobj=gz,mode='w') as t:
    for rel in sorted(parse(R/'26998_EXPECTED_FULL_APP.sha256')):
     path=R/rel;m=t.gettarinfo(str(path),arcname=rel);m.uid=m.gid=0;m.uname=m.gname='';m.mtime=0
     with path.open('rb') as opened:t.addfile(m,opened)
 (OUT/'26998_candidate_app_source.tar.gz.sha256').write_text(sha(OUT/'26998_candidate_app_source.tar.gz')+'  26998_candidate_app_source.tar.gz\n')
 print('PASS real compiled 26998 source/APK SHA proof; IQ not proven until on-device')

if __name__=='__main__':
 try:
  parser=argparse.ArgumentParser();parser.add_argument('command',choices=('seal','fetch','prepare-base','install','regress','stage-native','verify-compiled','finalize'));args=parser.parse_args()
  globals()[args.command.replace('-','_')]()
 except Exception as e:print('26998 BUILD ERROR:',e,file=sys.stderr);sys.exit(1)
