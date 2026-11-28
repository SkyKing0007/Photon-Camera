#!/usr/bin/env python3
"""27000 guarded successor to successful 26999. C OFF Sabre chroma and lens sensitivity only; real compiler gates retained."""
import argparse,gzip,hashlib,io,json,os,pathlib,re,shutil,subprocess,sys,tarfile,urllib.request,zipfile
R=pathlib.Path(__file__).resolve().parent
SHADER_COUNT=341 # exact current 27000 physical required shader inventory; not skip
TMP=R/'.photon_27000_work';OUT=R/'photon_27000_outputs'
ART=TMP/'26999-success.zip';BASE=TMP/'authority_26999';CAND=TMP/'candidate_27000'
REPO='SkyKing0007/Photon-Camera';BRANCH='experimental-clean-photon-rebuild'
RUN=46048295285;COMMIT='1fbec1b4b0a314b034026ed1a483f7bf6a77ba50';ART_ID=15223663522
ART_SHA='7923a4fc5110eff374c5b874c9d7edf6cf202d8d0637f5b1fb43c073195539df'
TAR_SHA='41112b63a8759b47417b59af1d73569617c3e93732a95d9efaec50b89e24410c'
BUILDER_SHA='cb2d21bb8c8cbd556eab51d79e066adc14e7e2060382ffe4fa9bac85e73a098e'
WORKFLOW_SHA='a0044fc2bf3c96a4143482e32cb940a7f75c1d9b9332bd1d47e82016b350fca0'
PRIOR_APK_SHA='9706fca285f4cd4a8568ff61fc4e21fdfb9b2b11a64a4e28f78ca4360eace6f6'
PRIOR_APK_NAME='IrisCamera-0.9726999-26999-iris-rawr-debug.apk'
APKNAME='IrisCamera-0.9727000-27000-iris-rawr-debug.apk'
NBASE=2709;NFILES=2709;NCHANGE=12;NADDED=0;NMODIFIED=12;NDELETED=0;NPROTECTED=2697
NATIVE_SHA={'lib/arm64-v8a/liblkrpipeline.so': '037a5f62649dcac7034c789c8e7ea2f250ca818d1c1c364e09a59f6897530105', 'lib/arm64-v8a/libsrpipeline.so': 'f87cc70ad12a69345392a4eb73b6ec33739577ce8c39b7a4916180c344f67069', 'lib/armeabi-v7a/liblkrpipeline.so': '9297eb7c58ca242986bced32bf773dcc8d16c3beaa33c26142b152c585957b03', 'lib/armeabi-v7a/libsrpipeline.so': '48788035080e66efa63b693e35f0587d2f02e851b818c367f3915b6154b47d68'}
DONOR_SHA={
 'lib/arm64-v8a/libiris26972c129.so':'a70ba1b1e4e8c856b07c828bef4141d0097d19013a49f77c1f59e41ee0a52cae',
 'lib/arm64-v8a/libi72.so':'ab0698a4a7006564e22447402468a9e1ca349a9017180bc7767c4feec58e0331',
}
FILES=['26999_SUCCESSFUL_EXECUTED_BUILDER_REFERENCE.py', '26999_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml', '27000_ADDED_RUNTIME_PATHS.txt', '27000_AUTHORITY_AND_SCOPE.json', '27000_BASE_26999_FULL_APP.sha256', '27000_CHANGED_RUNTIME_ALLOWLIST.txt', '27000_COMMIT_MESSAGE.txt', '27000_DELETED_RUNTIME_PATHS.txt', '27000_EXPANDED_SHADER.sha256', '27000_EXPECTED_FULL_APP.sha256', '27000_FORWARD_FULLINDEX.patch', '27000_LEGACY_NATIVE.sha256', '27000_LOCAL_VERIFICATION.log', '27000_MODIFIED_ORIGINAL_PATHS.txt', '27000_NATIVE_SHADER_INVENTORY.json', '27000_PROTECTED_SOURCE.sha256', '27000_REUSED_EXECUTABLES.json', '27000_ROLLBACK_FULLINDEX.patch', '27000_SHADER_KOTLIN_FILES.txt', '27000_SHADER_OBJECTS.txt', '27000_STAGE_1_UPLOAD_PATHS.txt', '27000_STAGE_2_UPLOAD_PATHS.txt', '27000_STAGE_3_UPLOAD_PATHS.txt', '27000_UPSTREAM_SOURCE_MAP.json', '27000_V6_CURRENT_SHADER_INVENTORY.json', 'Emit27000.kt', 'Parse27000Java.java', 'README_PHOTON_27000.md', 'build_27000_incremental.py', 'compile_27000_all.py', 'compile_27000_expanded.py', 'compile_27000_shaders.sh', 'compile_27000_shadow_expanded.py', 'test_27000_host.py', 'test_27000_latest_preflight.py', 'test_27000_patches.py', 'test_27000_sealed_negatives.py', 'test_27000_source.py', 'test_27000_math.py', 'test_27000_workflow_refs.py', 'verify_27000_native_glsl.py', 'verify_27000_v6_current_glsl.py']
ALLOWED_MODIFIED=['app/src/main/java/com/hinnka/mycamera/processor/experimentc/Iris26975CPinnedDonorProEngine.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/processor/GlesMgcRawChromaReconstructionShaders.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/processor/Iris26998GlesMgcRawSpatialStacker.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/RawCaptureProfileCoordinator.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/RawDemosaicProcessor.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/RawSceneExposureEstimator.kt', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/RawSceneExposureMatcher.kt', 'app/src/main/java/com/particlesdevs/photoncamera/ui/settings/custompreferences/Iris26998CAdvancedDenoisePreference.java', 'app/src/main/java/com/particlesdevs/photoncamera/ui/settings/custompreferences/MotionIqLabSeekBarPreference.java', 'app/src/main/java/com/particlesdevs/photoncamera/ui/settings/custompreferences/TunableSeekBarPreference.java', 'app/src/main/java/com/particlesdevs/photoncamera/ui/settings/custompreferences/UniversalSeekBarPreference.java', 'app/version.properties']
ALLOWED_ADDED=[]

def fail(msg):raise RuntimeError('27000 BLOCKED: '+str(msg))
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
 a=parse(R/'27000_BASE_26999_FULL_APP.sha256');b=parse(R/'27000_EXPECTED_FULL_APP.sha256')
 changed=set((R/'27000_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
 added=set((R/'27000_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
 modified=set((R/'27000_MODIFIED_ORIGINAL_PATHS.txt').read_text().splitlines())
 deleted=set((R/'27000_DELETED_RUNTIME_PATHS.txt').read_text().splitlines())
 if (len(a),len(b),len(changed),len(added),len(modified),len(deleted))!=(NBASE,NFILES,NCHANGE,NADDED,NMODIFIED,NDELETED):fail('count/protected source regression')
 if changed!=added|modified or added&set(a) or modified-set(a) or set(b)!=(set(a)|added) or deleted:fail('unexpected runtime change/deletion')
 if {p for p in set(a)&set(b) if a[p]!=b[p]}!=modified:fail('original source edits outside allowlist')
 protected={p:h for p,h in a.items() if p not in changed}
 if len(protected)!=NPROTECTED or protected!=parse(R/'27000_PROTECTED_SOURCE.sha256'):fail('protected source failed')
 if sha(R/'26999_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml')!=WORKFLOW_SHA or sha(R/'26999_SUCCESSFUL_EXECUTED_BUILDER_REFERENCE.py')!=BUILDER_SHA:fail('26999 actual executed reference changed')
 if (R/'handoff_payload_27000/app/version.properties').read_text()!='VERSION_MAJOR=0\nVERSION_MINOR=9726440\nVERSION_NAME=0.9727000\nVERSION_BUILD=27000\n':fail('27000 version not exact')
 allowed_modified=set(json.loads((R/'27000_AUTHORITY_AND_SCOPE.json').read_text())['allowed_modified_exact'])
 if allowed_modified!=modified:fail('changed original paths not explicit')
 if modified!=set(ALLOWED_MODIFIED) or added!=set(ALLOWED_ADDED):fail('new scope not exact')
 legacy=parse(R/'27000_LEGACY_NATIVE.sha256')
 if len(legacy)!=6 or any(a.get(p)!=h for p,h in legacy.items()) or any(b.get(p)!=h for p,h in legacy.items() if p not in modified):fail('exact predecessor C native source authority mismatch')
 if any('/cpp/' in p or '/jniLibs/' in p or '/assets/' in p or '/processing/' in p for p in changed):fail('runtime processing/source isolation violated')
 return changed,a,b

def seal():
 changed,a,b=scope();wf='.github/workflows/build-27000-change-aware.yml';trigger='TRIGGER_27000.txt'
 expect=set(FILES)|{wf,trigger}|{'handoff_payload_27000/'+p for p in changed}
 sealed={}
 for line in (R/'27000_HANDOFF_HASHES.sha256').read_text().splitlines():
  try:h,p=line.split('  ',1)
  except ValueError:fail('bad handoff hash seal')
  if p in sealed or not (R/p).is_file() or sha(R/p)!=h:fail('missing/tampered handoff file '+p)
  sealed[p]=h
 if set(sealed)!=expect:fail('missing/extra handoff file set '+str(sorted(set(sealed)^expect)[:10]))
 stages=[(R/f'27000_STAGE_{i}_UPLOAD_PATHS.txt').read_text().splitlines() for i in (1,2,3)]
 if stages[0]!=sorted((expect|{'27000_HANDOFF_HASHES.sha256'})-{wf,trigger}) or stages[1]!=[wf] or stages[2]!=[trigger]:fail('three upload stages not strict')
 payload=R/'handoff_payload_27000'
 if {p.relative_to(payload).as_posix() for p in payload.rglob('*') if p.is_file()}!=changed:fail('payload missing/extra')
 for p in changed:
  if sha(payload/p)!=b[p]:fail('source input tampering '+p)
 if sha(R/'.github/workflows/build-27000-change-aware.yml')!=sealed[wf]:fail('workflow after seal changed')
 subprocess.run([sys.executable,'-S','test_27000_workflow_refs.py'],cwd=R,check=True)
 if os.getenv('GITHUB_ACTIONS')=='true':
  from compile_27000_all import verify_reused,verify_compiler_transform
  verify_reused();verify_compiler_transform(R/'compile_26989_shaders.sh')
 print(f'PASS 27000 three-stage SHA seal, {NPROTECTED} protected, {NCHANGE} source delta')

def fetch():
 seal();token=os.getenv('GITHUB_TOKEN','')
 if not token or os.getenv('GITHUB_REPOSITORY')!=REPO or os.getenv('GITHUB_REF_NAME')!=BRANCH:fail('Actions credentials/target branch unavailable')
 def get(endpoint):
  req=urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+endpoint,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'})
  with urllib.request.urlopen(req,timeout=120) as resp:return json.load(resp)
 run=get('actions/runs/'+str(RUN));art=get('actions/artifacts/'+str(ART_ID))
 if run.get('id')!=RUN or run.get('conclusion')!='success' or run.get('head_sha')!=COMMIT or run.get('head_branch')!=BRANCH:fail('26999 Actions run not successful/exact')
 if art.get('id')!=ART_ID or art.get('expired') or art.get('digest')!='sha256:'+ART_SHA or art.get('workflow_run',{}).get('id') not in (RUN,None):fail('26999 artifact identity/published digest')
 TMP.mkdir(parents=True,exist_ok=True)
 subprocess.run(['curl','--fail','--location','--retry','3','--silent','--show-error','-H','Authorization: Bearer '+token,'-H','Accept: application/vnd.github+json',f'https://api.github.com/repos/{REPO}/actions/artifacts/{ART_ID}/zip','-o',str(ART)],check=True)
 if sha(ART)!=ART_SHA:fail('downloaded successful 26999 ZIP mismatch')
 print('PASS exact successful 26999 Actions artifact fetched')

def prior_zip():
 if not ART.is_file() or sha(ART)!=ART_SHA:fail('successful 26999 ZIP inaccessible or wrong hash')
 return zipfile.ZipFile(ART)
def safe_extract_tar(data,dest):
 with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as t:
  for m in t:
   path=pathlib.PurePosixPath(m.name)
   if not m.isfile() or not path.parts or path.parts[0]!='app' or path.is_absolute() or '..' in path.parts or m.issym() or m.islnk():fail('unsafe 26999 compiled TAR entry '+m.name)
  t.extractall(dest,filter='data')

def recover():
 seal()
 for folder in (BASE,CAND):
  if folder.exists():shutil.rmtree(folder)
 BASE.mkdir(parents=True)
 with prior_zip() as z:
  if z.testzip():fail('26999 ZIP CRC invalid')
  def get(name):
   p='photon_26999_outputs/'+name
   if p not in z.namelist():fail('26999 successful compiled receipt missing '+p)
   return z.read(p)
  src=get('26999_candidate_app_source.tar.gz')
  if hashlib.sha256(src).hexdigest()!=TAR_SHA or get('26999_candidate_app_source.tar.gz.sha256')!=f'{TAR_SHA}  26999_candidate_app_source.tar.gz\n'.encode():fail('26999 actual compiled TAR mismatch')
  if get('26999_EXPECTED_FULL_APP.sha256')!=(R/'27000_BASE_26999_FULL_APP.sha256').read_bytes() or get('26999_PREBUILD_SEALED_APP.sha256')!=(R/'27000_BASE_26999_FULL_APP.sha256').read_bytes():fail('compiled source manifest authority differs')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build_26999_incremental.py')).hexdigest()!=BUILDER_SHA or BUILDER_SHA not in get('26999_ACTUAL_EXECUTED_BUILDER.sha256').decode():fail('successful executed builder not pinned')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build-26999-change-aware.yml')).hexdigest()!=WORKFLOW_SHA or WORKFLOW_SHA not in get('26999_ACTUAL_EXECUTED_WORKFLOW.sha256').decode():fail('successful executed workflow not pinned')
  if PRIOR_APK_NAME not in z.namelist() or PRIOR_APK_SHA not in get('26999_APK.sha256').decode() or hashlib.sha256(z.read(PRIOR_APK_NAME)).hexdigest()!=PRIOR_APK_SHA:fail('successful 26999 APK identity')
  identity=get('26999_ACTIONS_IDENTITY.txt').decode()
  if 'git_sha='+COMMIT not in identity or 'github_run_id='+str(RUN) not in identity:fail('26999 Actions job identity')
  compiler=get('26999_COMPILER_STATUS.txt').decode()
  for phrase in ('REAL PINNED GLSL COMPILE: PASS','REAL SPIR-V VALIDATION/OPTIMIZATION: PASS','REAL KOTLIN COMPILE: PASS','REAL JAVA COMPILE: PASS','REAL TWO-ABI NDK/CMake COMPILE: PASS','REAL ANDROID Gradle :app:assembleDebug: PASS','RUNTIME SOURCE INVARIANCE: PASS'):
   if phrase not in compiler:fail('26999 compiler proof absent: '+phrase)
  for task in (':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL'):
   if 'PASS '+task not in get('26999_REAL_GRADLE_TASKS.txt').decode():fail('26999 predecessor Gradle task absent: '+task)
  safe_extract_tar(src,BASE)
 exact(BASE,'27000_BASE_26999_FULL_APP.sha256','actual successful 26999 compiled source')
 shutil.copytree(BASE,CAND)
 changed,_,b=scope()
 for p in sorted(changed):
  dest=CAND/p;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/'handoff_payload_27000'/p,dest)
 exact(CAND,'27000_EXPECTED_FULL_APP.sha256','exact 27000 isolated candidate')
 print('PASS actual 26999 compiled authority and isolated 27000 candidate recovered')

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
 exact(R,'27000_BASE_26999_FULL_APP.sha256','actual 26999 live predecessor restored')
 subprocess.run([sys.executable,'-S','test_27000_latest_preflight.py'],cwd=R,check=True)
 OUT.mkdir(parents=True,exist_ok=True)
 changed,_,_=scope()
 (OUT/'27000_SOURCE_SCOPE.txt').write_text(f'26999 Actions={RUN} commit={COMMIT} artifact={ART_ID} artifact_zip_sha={ART_SHA} actual_compiled_source_tar_sha={TAR_SHA}\nactual_runner_sha={BUILDER_SHA} actual_workflow_sha={WORKFLOW_SHA} prior_apk_sha={PRIOR_APK_SHA}\nbase={NBASE} candidate={NFILES} changes={NCHANGE} modified={NMODIFIED} added={NADDED} protected={NPROTECTED} deleted={NDELETED}\n'+''.join(p+'\n' for p in sorted(changed)))
 print('PASS latest-only 26999 authority, sparse historical fixtures and predecessor settings and source tests')

def install():
 seal();exact(BASE,'27000_BASE_26999_FULL_APP.sha256','26999 baseline before install')
 exact(CAND,'27000_EXPECTED_FULL_APP.sha256','27000 frozen candidate before install')
 old=OUT/'26999_SUCCESSFUL_REAL_GLSL_SPIRV_COMPILER.txt'
 # Historical 26904 checks have been run; require predecessor successful Actions compiler receipt too.
 with prior_zip() as z:
  source=z.read('photon_26999_outputs/26999_REAL_GLSL_SPIRV_COMPILER.txt').decode()
  if 'PASS actual 26974 24/24 C GLES' not in source or 'PASS inherited historical 24/24 and actual current 340/340 26989 donor/Iris C shader compilation' not in source:fail('26999 real pinned GLSL/SPIR-V receipt missing')
 (OUT/'26999_SUCCESSFUL_REAL_GLSL_SPIRV_COMPILER.txt').write_text(source)
 with prior_zip() as z:
  con=z.read('photon_26999_outputs/26999_CON_REAL_GLSL_SPIRV_COMPILER.txt').decode()
  if 'PASS 26989 C ON 14/14 static shader stages real GLSL/SPIR-V opt/val' not in con:fail('26999 real C ON shader proof absent')
 (OUT/'26999_SUCCESSFUL_CON_REAL_GLSL_SPIRV_COMPILER.txt').write_text(con)
 with prior_zip() as z:
  native=z.read('photon_26999_outputs/26999_NATIVE_REAL_GLSL_SPIRV_COMPILER.txt').decode()
  if 'PASS 59/59 private Vulkan variants real compile/opt/val' not in native:fail('26999 real native shader proof absent')
 (OUT/'26999_SUCCESSFUL_NATIVE_REAL_GLSL_SPIRV_COMPILER.txt').write_text(native)
 with prior_zip() as z:
  for name, phrase in (('26999_EXPANDED_REAL_GLSL_SPIRV.txt','PASS 26999 exact expanded donor shader GLSL/SPIR-V compile/opt/val and pair link'),('26999_SHADOW_REAL_GLSL_SPIRV.txt','PASS 26999 expanded RAW adjustment pair original/310 GLSL and SPIR-V opt/val')):
   receipt=z.read('photon_26999_outputs/'+name).decode()
   if phrase not in receipt:fail('26999 predecessor expanded shader proof missing '+name)
   (OUT/('26999_SUCCESSFUL_'+name.removeprefix('26999_'))).write_text(receipt)
 shutil.rmtree(R/'app/src');shutil.copytree(CAND/'app/src',R/'app/src')
 shutil.copyfile(CAND/'app/version.properties',R/'app/version.properties')
 shutil.copyfile(CAND/'app/build.gradle',R/'app/build.gradle')
 exact(R,'27000_EXPECTED_FULL_APP.sha256','live installed 27000 SHA source')
 print('PASS installed exact 27000 C OFF Sabre chroma and lens sensitivity source; production unapproved')

def regress():
 seal();exact(R,'27000_EXPECTED_FULL_APP.sha256','27000 live protected runtime')
 subprocess.run([sys.executable,'-S','test_27000_source.py','--live'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26994_watermark_host.py'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26995_lkr_host.py'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_27000_host.py'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','verify_27000_v6_current_glsl.py','--audit'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','verify_27000_native_glsl.py','--audit'],cwd=R,check=True)
 exact(R,'27000_EXPECTED_FULL_APP.sha256','27000 live after host tests')
 (OUT/'27000_HOST_TEST_SOURCE_SEAL.txt').write_text(sha(R/'27000_EXPECTED_FULL_APP.sha256')+'\n')

def verified_regress():
 seal();exact(R,'27000_EXPECTED_FULL_APP.sha256','27000 live protected runtime')
 if (OUT/'27000_HOST_TEST_SOURCE_SEAL.txt').read_text()!=sha(R/'27000_EXPECTED_FULL_APP.sha256')+'\n':fail('current host execution receipt missing')
 subprocess.run([sys.executable,'-S','test_27000_source.py','--live'],cwd=R,check=True)

def stage_native():
 seal()
 with prior_zip() as z:
  with zipfile.ZipFile(io.BytesIO(z.read(PRIOR_APK_NAME))) as apk:
   if apk.testzip():fail('26999 published APK CRC')
   for p,want in NATIVE_SHA.items():
    data=apk.read(p)
    if hashlib.sha256(data).hexdigest()!=want:fail('successful native ABI hash regression '+p)
    dest=R/'app/build/verified_rawlens26931/jniLibs'/p.removeprefix('lib/')
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    if sha(dest)!=want:fail('staged native binary differs '+p)
 print('PASS exact successful 26999 dual ABI RawLens native binaries')

def verify_compiled():
 verified_regress();from compile_27000_all import verify_receipts
 verify_receipts();success=OUT/'26999_SUCCESSFUL_REAL_GLSL_SPIRV_COMPILER.txt'
 current=OUT/'27000_REAL_GLSL_SPIRV_COMPILER.txt'
 if 'PASS 26989 C ON 14/14 static shader stages real GLSL/SPIR-V opt/val' not in (OUT/'26999_SUCCESSFUL_CON_REAL_GLSL_SPIRV_COMPILER.txt').read_text():fail('26999 predecessor C ON shader receipt missing')
 if not success.is_file() or 'PASS actual 26974 24/24 C GLES' not in success.read_text() or 'PASS inherited historical 24/24 and actual current 340/340 26989 donor/Iris C shader compilation' not in success.read_text():fail('26999 actual successful shader proof missing')
 if not current.is_file() or 'PASS actual 26974 24/24 C GLES' not in current.read_text() or 'PASS inherited historical 24/24 and actual current {SHADER_COUNT}/{SHADER_COUNT} 26989 donor/Iris C shader compilation'.format(SHADER_COUNT=SHADER_COUNT) not in current.read_text():fail('current Actions 24/24 + 27000 341/341 shader recompilation proof missing')
 con=OUT/'27000_CON_REAL_GLSL_SPIRV_COMPILER.txt'
 if not con.is_file() or 'PASS 26989 C ON 14/14 static shader stages real GLSL/SPIR-V opt/val' not in con.read_text():fail('new C ON real shader compiler proof missing')
 v6=OUT/'27000_V6_CURRENT_STATIC_GLSL_SPIRV_COMPILER.txt'
 if not v6.is_file() or f'PASS 26989 physical current {SHADER_COUNT}/{SHADER_COUNT} static donor/Iris C ESSL GLSL + SPIR-V opt/val' not in v6.read_text():fail('current C shader parser and SPIR-V optimizer must actually pass')
 for p,want in NATIVE_SHA.items():
  if sha(R/'app/build/verified_rawlens26931/jniLibs'/p.removeprefix('lib/'))!=want:fail('staged dual ABI LKR mismatch')
 for p,want in DONOR_SHA.items():
  if sha(R/'app/src/main/jniLibs'/p.removeprefix('lib/'))!=want:fail('original pinned donor sidecar mismatch')
 OUT.mkdir(exist_ok=True)
 (OUT/'27000_PREBUILD_SEALED_APP.sha256').write_bytes((R/'27000_EXPECTED_FULL_APP.sha256').read_bytes())
 if 'PASS 59/59 private Vulkan variants real compile/opt/val' not in (OUT/'27000_NATIVE_REAL_GLSL_SPIRV_COMPILER.txt').read_text():fail('missing actual private Vulkan compiler proof')
 if 'PASS 27000 expanded RAW adjustment pair original/310 GLSL and SPIR-V opt/val' not in (OUT/'27000_SHADOW_REAL_GLSL_SPIRV.txt').read_text():fail('missing new expanded shadow shader proof')
 if 'PASS exact 26989 runtime ESSL300 OES preview pair compile/link' not in (OUT/'27000_PREVIEW_REAL_GLSL.txt').read_text():fail('current real preview shader compile/link missing')
 print('PASS prebuild source seal + current actual pinned SPIR-V/GLSL + dual ABI native input')

def finalize():
 verified_regress();from compile_27000_all import verify_receipts
 verify_receipts()
 if (OUT/'27000_PREBUILD_SEALED_APP.sha256').read_bytes()!=(R/'27000_EXPECTED_FULL_APP.sha256').read_bytes():fail('prebuild SHA seal absent')
 log=(OUT/'27000_gradle_assemble.log').read_text(errors='replace')
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
 exact(R,'27000_EXPECTED_FULL_APP.sha256','actual assembled 27000 source unchanged')
 OUT.mkdir(exist_ok=True)
 (OUT/'27000_COMPILER_STATUS.txt').write_text('REAL PINNED GLSL COMPILE: PASS\nREAL SPIR-V VALIDATION/OPTIMIZATION: PASS\nREAL KOTLIN COMPILE: PASS\nREAL JAVA COMPILE: PASS\nREAL TWO-ABI NDK/CMake COMPILE: PASS\nREAL ANDROID Gradle :app:assembleDebug: PASS\nRUNTIME SOURCE INVARIANCE: PASS (2697 protected, 12 modified, 0 added)\nEXPERIMENT C CONTROLLED DEVICE TRIAL: ENABLED\nEXPERIMENT C PRODUCTION READY: NO\nDEVICE IQ VALIDATION: NOT RUN\n')
 (OUT/'27000_REAL_GRADLE_TASKS.txt').write_text(''.join('PASS '+p+'\n' for p in tasks))
 (OUT/'27000_APK.sha256').write_text(sha(R/APKNAME)+'  '+APKNAME+'\n')
 wf=R/'.github/workflows/build-27000-change-aware.yml'
 (OUT/'27000_ACTUAL_EXECUTED_BUILDER.sha256').write_text(sha(R/'build_27000_incremental.py')+'  build_27000_incremental.py\n')
 (OUT/'27000_ACTUAL_EXECUTED_WORKFLOW.sha256').write_text(sha(wf)+'  '+wf.relative_to(R).as_posix()+'\n')
 (OUT/'27000_ACTIONS_IDENTITY.txt').write_text('git_sha='+os.getenv('GITHUB_SHA','NOT_IN_ACTIONS')+'\ngithub_run_id='+os.getenv('GITHUB_RUN_ID','NOT_IN_ACTIONS')+'\n')
 for item in ('27000_BASE_26999_FULL_APP.sha256','27000_EXPECTED_FULL_APP.sha256','27000_PROTECTED_SOURCE.sha256','27000_CHANGED_RUNTIME_ALLOWLIST.txt','27000_ADDED_RUNTIME_PATHS.txt','27000_MODIFIED_ORIGINAL_PATHS.txt','27000_DELETED_RUNTIME_PATHS.txt','27000_AUTHORITY_AND_SCOPE.json'):
  shutil.copy2(R/item,OUT/item)
 shutil.copy2(R/'build_27000_incremental.py',OUT/'ACTUAL_EXECUTED_build_27000_incremental.py')
 shutil.copy2(wf,OUT/'ACTUAL_EXECUTED_build-27000-change-aware.yml')
 with (OUT/'27000_candidate_app_source.tar.gz').open('wb') as f:
  with gzip.GzipFile(filename='',mode='wb',compresslevel=1,mtime=0,fileobj=f) as gz:
   with tarfile.open(fileobj=gz,mode='w') as t:
    for rel in sorted(parse(R/'27000_EXPECTED_FULL_APP.sha256')):
     path=R/rel;m=t.gettarinfo(str(path),arcname=rel);m.uid=m.gid=0;m.uname=m.gname='';m.mtime=0
     with path.open('rb') as opened:t.addfile(m,opened)
 (OUT/'27000_candidate_app_source.tar.gz.sha256').write_text(sha(OUT/'27000_candidate_app_source.tar.gz')+'  27000_candidate_app_source.tar.gz\n')
 print('PASS real compiled 27000 source/APK SHA proof; IQ not proven until on-device')

if __name__=='__main__':
 try:
  parser=argparse.ArgumentParser();parser.add_argument('command',choices=('seal','fetch','prepare-base','install','regress','stage-native','verify-compiled','finalize'));args=parser.parse_args()
  globals()[args.command.replace('-','_')]()
 except Exception as e:print('27000 BUILD ERROR:',e,file=sys.stderr);sys.exit(1)
