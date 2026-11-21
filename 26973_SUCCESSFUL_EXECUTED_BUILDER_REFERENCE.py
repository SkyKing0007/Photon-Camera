#!/usr/bin/env python3
"""26973 successor of ACTUAL successful 26972 guarded builder.

Exact 26972 executed workflow/build and published compiled TAR are immutable
references. Reconstruct candidate first; no stale repository sources, no
compiler bypasses, no pushes/commits, fail on any unexplained app source.
"""
import argparse,gzip,hashlib,io,json,os,pathlib,re,shutil,subprocess,sys,tarfile,urllib.request,zipfile
R=pathlib.Path(__file__).resolve().parent
TMP=R/'.photon_26973_work';OUT=R/'photon_26973_outputs'
ART=TMP/'26972-success.zip';BASE=TMP/'authority_26972';CAND=TMP/'candidate_26973'
REPO='SkyKing0007/Photon-Camera';BRANCH='experimental-clean-photon-rebuild'
RUN=44923896617;COMMIT='583b87148fa21d49df4b359991439e1d475ac526';ART_ID=14715277974
ART_SHA='3c9dee79f816eb1ef2cd7e62e1b88c2556a86ee2d53b95984bb8b7486fb12921'
TAR_SHA='0ce0b5910f379011db3dc9fc8db7eee093fcf22bf746595bc69bd96f9667271f'
BUILDER_SHA='39eb9bedafc467e1faeb98c7a9c94c4ac20151fdce6fb53a2930a5b97cf26137'
WORKFLOW_SHA='60b71ec1c86f3e809aebcdefa0008502277fa1d7e5d63648affe6012191dcc08'
PRIOR_APK_SHA='6c56cfa3ef71508c4e454e81978e39fe4a7ce24b5acd05c8baa2c5ef4546dacc'
PRIOR_APK_NAME='IrisCamera-0.9726972-26972-iris-rawr-debug.apk'
APKNAME='IrisCamera-0.9726973-26973-iris-rawr-debug.apk'
NBASE=2132;NFILES=2132;NCHANGE=11;NADDED=0;NMODIFIED=11;NDELETED=0;NPROTECTED=2121
MODIFIED={
 'app/src/main/java/com/hinnka/mycamera/processor/Iris26972CCamera2ShutterSession.kt',
 'app/src/main/java/com/hinnka/mycamera/processor/Iris26972CCaptureToGallery.kt',
 'app/src/main/java/com/hinnka/mycamera/processor/Iris26972CStreamingFinish.kt',
 'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/experimentc/Iris26972CContract.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/experimentc/Iris26972CJpeg444.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/experimentc/Iris26972CMediaStorePublisher.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/experimentc/Iris26972CModeGate.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/experimentc/Iris26972CUltraHdr.java',
 'app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java',
 'app/version.properties',
}
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
FILES=['README_PHOTON_26973.md','26973_COMMIT_MESSAGE.txt','26973_LOCAL_VERIFICATION.txt','26972_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml','26972_SUCCESSFUL_EXECUTED_BUILDER_REFERENCE.py','26972_EXPECTED_FULL_APP.sha256','build_26973_incremental.py','test_26973_source.py','test_26973_patches.py','test_26973_sealed_negatives.py','test_26973_workflow_refs.py','compile_26973_shaders.sh','26973_BASE_26972_FULL_APP.sha256','26973_EXPECTED_FULL_APP.sha256','26973_PROTECTED_SOURCE.sha256','26973_AUTHORITY_AND_SCOPE.json','26973_CHANGED_RUNTIME_ALLOWLIST.txt','26973_MODIFIED_ORIGINAL_PATHS.txt','26973_ADDED_RUNTIME_PATHS.txt','26973_DELETED_RUNTIME_PATHS.txt','26973_NATIVE_RELEASE_ALLOWLIST.txt','26973_FORWARD_FULLINDEX.patch','26973_ROLLBACK_FULLINDEX.patch','26973_EXPANDED_SHADER_HASHES.sha256','26973_STAGE_1_UPLOAD_PATHS.txt','26973_STAGE_2_UPLOAD_PATHS.txt','26973_STAGE_3_UPLOAD_PATHS.txt','26973_EXPECTED_ACTION_EXECUTABLES.txt']

def fail(msg):raise RuntimeError('26973 BLOCKED: '+str(msg))
def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def parse(path,prefix='app/'):
 d={}
 for line in path.read_text().splitlines():
  try:h,p=line.split('  ',1)
  except ValueError:fail('bad manifest '+str(path))
  if not re.fullmatch(r'[0-9a-f]{64}',h) or not p.startswith(prefix) or '..' in pathlib.PurePosixPath(p).parts or p in d:fail('malformed/duplicate manifest path '+p)
  d[p]=h
 return d
def scan(root):
 src=root/'app/src';required=[root/'app/build.gradle',root/'app/version.properties']
 if not src.is_dir() or not all(x.is_file() for x in required):fail('app source/build/version incomplete '+str(root))
 d={}
 for p in [*src.rglob('*'),*required]:
  if p.is_symlink():fail('source symlink '+str(p))
  if p.is_file():d[p.relative_to(root).as_posix()]=sha(p)
 return d
def exact(root,file,label):
 want=parse(R/file);got=scan(root)
 if want!=got:
  fail(label+f' missing={sorted(set(want)-set(got))[:5]} extra={sorted(set(got)-set(want))[:5]} mismatched={[x for x in want.keys() & got.keys() if want[x]!=got[x]][:5]}')
 print('PASS '+label+' '+str(len(got))+' files')
 return got

def scope():
 a=parse(R/'26973_BASE_26972_FULL_APP.sha256');b=parse(R/'26973_EXPECTED_FULL_APP.sha256')
 changed=set((R/'26973_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
 added=set((R/'26973_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
 modified=set((R/'26973_MODIFIED_ORIGINAL_PATHS.txt').read_text().splitlines())
 deleted=set((R/'26973_DELETED_RUNTIME_PATHS.txt').read_text().splitlines())
 if (len(a),len(b),len(changed),len(added),len(modified),len(deleted))!=(NBASE,NFILES,NCHANGE,NADDED,NMODIFIED,NDELETED):fail('incorrect source counts')
 if modified!=MODIFIED or changed!=(modified|added) or added & set(a) or set(b)!=(set(a)|added) or deleted:fail('source allowlist/unexpected deletion')
 if {p for p in set(a)&set(b) if a[p]!=b[p]}!=modified:fail('original source changed-file delta')
 protected={p:h for p,h in a.items() if p not in changed}
 if len(protected)!=NPROTECTED or parse(R/'26973_PROTECTED_SOURCE.sha256')!=protected:fail('protected source hash list')
 if sha(R/'26972_EXPECTED_FULL_APP.sha256')!=sha(R/'26973_BASE_26972_FULL_APP.sha256'):fail('26972 authority and base differ')
 if a['app/build.gradle']!=b['app/build.gradle']:fail('Gradle source config not protected')
 if set((R/'26973_NATIVE_RELEASE_ALLOWLIST.txt').read_text().splitlines())!={'app/build/verified_rawlens26931/jniLibs/'+p.removeprefix('lib/') for p in NATIVE_SHA}:fail('native release allowlist differs')
 if (R/'handoff_payload_26973/app/version.properties').read_text()!='VERSION_MAJOR=0\nVERSION_MINOR=9726440\nVERSION_NAME=0.9726973\nVERSION_BUILD=26973\n':fail('version not exact 26973 successor')
 for p in added:
  if not (p.startswith('app/src/main/cpp/iris26972c/') or p=='app/src/main/assets/iris26972c/sRGB.icc' or (p.startswith('app/src/main/java/com/hinnka/mycamera/processor/Iris26972C') and p.endswith('.kt')) or p.startswith('app/src/main/java/com/particlesdevs/photoncamera/processing/experimentc/Iris26972C') or p in ('app/src/main/jniLibs/arm64-v8a/libiris26972c129.so','app/src/main/jniLibs/arm64-v8a/libi72.so')):fail('new runtime file outside C-only namespace '+p)
 return changed,a,b

def seal():
 changed,a,b=scope()
 wf='.github/workflows/build-26973-change-aware.yml';trigger='TRIGGER_26973.txt'
 expect=set(FILES)|{wf,trigger}|{'handoff_payload_26973/'+p for p in changed}|{'26973_EXACT_EXPANDED_C_SHADERS/'+p for p in parse(R/'26973_EXPANDED_SHADER_HASHES.sha256',prefix='').keys()}
 sealed={}
 for line in (R/'26973_HANDOFF_HASHES.sha256').read_text().splitlines():
  try:h,p=line.split('  ',1)
  except ValueError:fail('invalid handoff SHA seal')
  if p in sealed or not (R/p).is_file() or sha(R/p)!=h:fail('missing/tampered sealed file '+p)
  sealed[p]=h
 if set(sealed)!=expect:fail('sealed file set missing/extra '+str(sorted(set(sealed)^expect)[:10]))
 stages=[(R/f'26973_STAGE_{i}_UPLOAD_PATHS.txt').read_text().splitlines() for i in (1,2,3)]
 if stages[0]!=sorted((expect|{'26973_HANDOFF_HASHES.sha256'})-{wf,trigger}) or stages[1]!=[wf] or stages[2]!=[trigger]:fail('three-stage order/path mismatch')
 payload=R/'handoff_payload_26973'
 if {p.relative_to(payload).as_posix() for p in payload.rglob('*') if p.is_file()}!=changed:fail('overlay missing or extra file')
 for p in changed:
  if sha(payload/p)!=b[p]:fail('overlay hash not frozen '+p)
 shader_hashes=parse(R/'26973_EXPANDED_SHADER_HASHES.sha256',prefix='')
 if len(shader_hashes)!=24 or {p.name for p in (R/'26973_EXACT_EXPANDED_C_SHADERS').glob('*.frag')}!=set(shader_hashes):fail('shader set not exact 24')
 for name,h in shader_hashes.items():
  if sha(R/'26973_EXACT_EXPANDED_C_SHADERS'/name)!=h:fail('C shader reference mismatch '+name)
 if sha(R/'26972_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml')!=WORKFLOW_SHA or sha(R/'26972_SUCCESSFUL_EXECUTED_BUILDER_REFERENCE.py')!=BUILDER_SHA:fail('26972 V3 successful build mechanics altered')
 if sha(R/'.github/workflows/build-26973-change-aware.yml')!=sealed[wf]:fail('26973 proposed workflow mutated')
 subprocess.run([sys.executable,'-S','test_26973_workflow_refs.py'],cwd=R,check=True)
 print('PASS 26973 sealed three-stage physical files, 2121 protected, 11 exact scope, 24 pinned C shaders')

def fetch():
 seal();token=os.getenv('GITHUB_TOKEN','')
 if not token or os.getenv('GITHUB_REPOSITORY')!=REPO or os.getenv('GITHUB_REF_NAME')!=BRANCH:fail('Actions token/target branch missing')
 def get(endpoint):
  req=urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+endpoint,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'})
  with urllib.request.urlopen(req,timeout=120) as r:return json.load(r)
 run=get('actions/runs/'+str(RUN));art=get('actions/artifacts/'+str(ART_ID))
 if run.get('id')!=RUN or run.get('conclusion')!='success' or run.get('head_sha')!=COMMIT or run.get('head_branch')!=BRANCH:fail('26972 successful run identity')
 if art.get('id')!=ART_ID or art.get('expired') or art.get('digest')!='sha256:'+ART_SHA or art.get('workflow_run',{}).get('id') not in (RUN,None):fail('26972 published artifact identity')
 TMP.mkdir(parents=True,exist_ok=True)
 subprocess.run(['curl','--fail','--location','--retry','3','--silent','--show-error','-H','Authorization: Bearer '+token,'-H','Accept: application/vnd.github+json','https://api.github.com/repos/'+REPO+'/actions/artifacts/'+str(ART_ID)+'/zip','-o',str(ART)],check=True)
 if sha(ART)!=ART_SHA:fail('downloaded 26972 ZIP SHA mismatch')
 print('PASS exact successful 26972 artifact downloaded')

def prior_zip():
 if not ART.is_file() or sha(ART)!=ART_SHA:fail('missing exact successful 26972 ZIP')
 return zipfile.ZipFile(ART)
def safe_extract_tar(data,dest):
 with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as t:
  for m in t:
   path=pathlib.PurePosixPath(m.name)
   if not m.isfile() or not path.parts or path.parts[0]!='app' or path.is_absolute() or '..' in path.parts or m.issym() or m.islnk():fail('unsafe successful 26972 tar entry '+m.name)
  t.extractall(dest,filter='data')

def prepare_base():
 seal()
 for folder in (BASE,CAND):
  if folder.exists():shutil.rmtree(folder)
 BASE.mkdir(parents=True)
 with prior_zip() as z:
  if z.testzip():fail('26972 artifact ZIP CRC failed')
  def get(name):
   p='photon_26972_outputs/'+name
   if p not in z.namelist():fail('26972 receipt missing '+p)
   return z.read(p)
  src=get('26972_candidate_app_source.tar.gz')
  if hashlib.sha256(src).hexdigest()!=TAR_SHA or get('26972_candidate_app_source.tar.gz.sha256')!=f'{TAR_SHA}  26972_candidate_app_source.tar.gz\n'.encode():fail('26972 compiled TAR identity')
  OUT.mkdir(parents=True,exist_ok=True)
  (OUT/'26972_SUCCESSFUL_REAL_GLSL_SPIRV_COMPILER.txt').write_bytes(get('26972_REAL_GLSL_SPIRV_COMPILER.txt'))
  for name in ('26972_EXPECTED_FULL_APP.sha256','26972_PREBUILD_SEALED_APP.sha256'):
   if get(name)!=(R/'26973_BASE_26972_FULL_APP.sha256').read_bytes():fail('26972 compiled source SHA manifest differs '+name)
  if hashlib.sha256(get('ACTUAL_EXECUTED_build_26972_incremental.py')).hexdigest()!=BUILDER_SHA or BUILDER_SHA not in get('26972_ACTUAL_EXECUTED_BUILDER.sha256').decode():fail('26972 executed builder not verified')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build-26972-change-aware.yml')).hexdigest()!=WORKFLOW_SHA or WORKFLOW_SHA not in get('26972_ACTUAL_EXECUTED_WORKFLOW.sha256').decode():fail('26972 executed workflow not verified')
  if PRIOR_APK_NAME not in z.namelist() or PRIOR_APK_SHA not in get('26972_APK.sha256').decode() or hashlib.sha256(z.read(PRIOR_APK_NAME)).hexdigest()!=PRIOR_APK_SHA:fail('26972 actual published APK differs')
  identity=get('26972_ACTIONS_IDENTITY.txt').decode()
  if 'git_sha='+COMMIT not in identity or 'github_run_id='+str(RUN) not in identity:fail('26972 actual Actions job identity')
  compiler=get('26972_COMPILER_STATUS.txt').decode()
  for phrase in ('REAL PINNED GLSL COMPILE: PASS','REAL SPIR-V VALIDATION/OPTIMIZATION: PASS','REAL KOTLIN COMPILE: PASS','REAL JAVA COMPILE: PASS','REAL TWO-ABI NDK/CMake COMPILE: PASS','REAL ANDROID Gradle :app:assembleDebug: PASS','RUNTIME SOURCE INVARIANCE: PASS'):
   if phrase not in compiler:fail('26972 predecessor compiler receipt missing '+phrase)
  for task in (':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL'):
   if 'PASS '+task not in get('26972_REAL_GRADLE_TASKS.txt').decode():fail('26972 predecessor Gradle task receipt missing '+task)
  safe_extract_tar(src,BASE)
 exact(BASE,'26973_BASE_26972_FULL_APP.sha256','successful 26972 compiled source')
 shutil.copytree(BASE,CAND)
 changed,a,b=scope()
 for p in changed:
  dest=CAND/p;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/'handoff_payload_26973'/p,dest)
 exact(CAND,'26973_EXPECTED_FULL_APP.sha256','isolated frozen 26973 candidate')
 if not (R/'gradlew').is_file() or not (R/'app/build.gradle').is_file():fail('checkout missing real Gradle root')
 if (R/'app/src').exists():shutil.rmtree(R/'app/src')
 shutil.copytree(BASE/'app/src',R/'app/src')
 shutil.copyfile(BASE/'app/version.properties',R/'app/version.properties')
 shutil.copyfile(BASE/'app/build.gradle',R/'app/build.gradle')
 if (R/'app/.cxx').exists():shutil.rmtree(R/'app/.cxx')
 exact(R,'26973_BASE_26972_FULL_APP.sha256','live original 26972 before historical shaders')
 OUT.mkdir(parents=True,exist_ok=True)
 (OUT/'26973_SOURCE_SCOPE.txt').write_text(f'authority=26972 Actions={RUN} git={COMMIT} artifact={ART_ID} ZIP_SHA={ART_SHA} compiled_TAR_SHA={TAR_SHA}\nprior executed builder SHA={BUILDER_SHA}, workflow SHA={WORKFLOW_SHA}, published APK SHA={PRIOR_APK_SHA}\nsource base={NBASE} candidate={NFILES} changes={NCHANGE} original edits={NMODIFIED} additions={NADDED} protected={NPROTECTED} deletions={NDELETED}\n'+''.join(p+'\n' for p in sorted(changed)))
 print('PASS reconstructed 26972 baseline, exact C-only 26973 candidate and live pre-history source')

def install():
 seal()
 exact(BASE,'26973_BASE_26972_FULL_APP.sha256','successful 26972 baseline')
 exact(CAND,'26973_EXPECTED_FULL_APP.sha256','frozen 26973 before install')
 receipt=OUT/'26972_SUCCESSFUL_REAL_GLSL_SPIRV_COMPILER.txt'
 if not receipt.is_file() or 'PASS actual 26972 24/24 C GLES (19 ESSL300+310; 5 ESSL310-only) + OpenGL SPIR-V opt/val' not in receipt.read_text():fail('26972 historical shaders not actually compiled in current Actions job')
 shutil.rmtree(R/'app/src');shutil.copytree(CAND/'app/src',R/'app/src')
 shutil.copyfile(CAND/'app/version.properties',R/'app/version.properties')
 exact(R,'26973_EXPECTED_FULL_APP.sha256','live sealed 26973 source after install')
 print('PASS current 26973 installed, Experiment C controlled trial enabled; not production')

def regress():
 seal();exact(R,'26973_EXPECTED_FULL_APP.sha256','live 26973 regressions')
 for name in ('test_26973_source.py','test_26973_patches.py'):
  subprocess.run([sys.executable,'-S',name,'--live'],cwd=R,check=True)
 print('PASS protected A/B Night DNG and exact 26973 source/patch proof')

def stage_native():
 seal()
 with prior_zip() as z:
  with zipfile.ZipFile(io.BytesIO(z.read(PRIOR_APK_NAME))) as apk:
   if apk.testzip():fail('26972 actual APK ZIP CRC')
   for p,want in NATIVE_SHA.items():
    raw=apk.read(p)
    if hashlib.sha256(raw).hexdigest()!=want:fail('26972 native LKR binary differs '+p)
    dest=R/'app/build/verified_rawlens26931/jniLibs'/p.removeprefix('lib/')
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    if sha(dest)!=want:fail('staged verified native mismatch '+p)
 print('PASS 26972 original LKR arm64/v7 native binaries byte-exact')

def verify_compiled():
 regress()
 prior=OUT/'26972_SUCCESSFUL_REAL_GLSL_SPIRV_COMPILER.txt'
 receipt=OUT/'26973_REAL_GLSL_SPIRV_COMPILER.txt'
 if not prior.is_file() or 'PASS actual 26972 24/24 C GLES (19 ESSL300+310; 5 ESSL310-only) + OpenGL SPIR-V opt/val' not in prior.read_text():fail('26972 actual historical shader proof missing')
 if not receipt.is_file() or 'PASS actual 26973 24/24 C GLES (19 ESSL300+310; 5 ESSL310-only) + OpenGL SPIR-V opt/val' not in receipt.read_text():fail('26973 real pinned current shader proof missing')
 for name,want in parse(R/'26973_EXPANDED_SHADER_HASHES.sha256',prefix='').items():
  if f'{want}  {name}' not in receipt.read_text():fail('C shader not compiled '+name)
 for p,want in NATIVE_SHA.items():
  if sha(R/'app/build/verified_rawlens26931/jniLibs'/p.removeprefix('lib/'))!=want:fail('native LKR staged source differs '+p)
 for p,want in DONOR_SHA.items():
  if sha(R/'app/src/main/jniLibs'/p.removeprefix('lib/'))!=want:fail('C vendor sidecar differs '+p)
 (OUT/'26973_PREBUILD_SEALED_APP.sha256').write_bytes((R/'26973_EXPECTED_FULL_APP.sha256').read_bytes())
 print('PASS physical shader, current pinned optimizer, ABI and source safety prebuild')

def finalize():
 regress();want=(R/'26973_EXPECTED_FULL_APP.sha256').read_bytes()
 if (OUT/'26973_PREBUILD_SEALED_APP.sha256').read_bytes()!=want:fail('prebuild SHA seal missing')
 log=(OUT/'26973_gradle_assemble.log').read_text(errors='replace')
 tasks=(':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL')
 for task in tasks:
  if task not in log:fail('actual Gradle build task not proven '+task)
 subprocess.run([sys.executable,'-S','verify_26906_native_cache.py','postflight'],cwd=R,check=True)
 apks=list((R/'app/build/outputs/apk').rglob('*.apk'))
 if len(apks)!=1:fail('not exactly one freshly assembled Android APK')
 shutil.copy2(apks[0],R/APKNAME)
 if (R/APKNAME).stat().st_size<1_000_000:fail('compiled APK size suspicious')
 with zipfile.ZipFile(R/APKNAME) as apk:
  if apk.testzip() or not {'AndroidManifest.xml','classes.dex'}<=set(apk.namelist()):fail('invalid output APK archive')
  for p,wantnative in {**NATIVE_SHA,**DONOR_SHA}.items():
   if hashlib.sha256(apk.read(p)).hexdigest()!=wantnative:fail('APK native release mismatch '+p)
  if not any(p.startswith('lib/arm64-v8a/libiris26972c.so') for p in apk.namelist()):fail('C 64-bit native library absent')
  if not any(p.startswith('lib/armeabi-v7a/libiris26972c.so') for p in apk.namelist()):fail('C 32-bit native library absent')
 exact(R,'26973_EXPECTED_FULL_APP.sha256','actual 26973 compiled candidate integrity')
 (OUT/'26973_COMPILER_STATUS.txt').write_text('REAL PINNED GLSL COMPILE: PASS\nREAL SPIR-V VALIDATION/OPTIMIZATION: PASS\nREAL KOTLIN COMPILE: PASS\nREAL JAVA COMPILE: PASS\nREAL TWO-ABI NDK/CMake COMPILE: PASS\nREAL ANDROID Gradle :app:assembleDebug: PASS\nEXACT SUCCESSFUL 26972 DUAL ABI LKR: PASS\nRUNTIME SOURCE INVARIANCE: PASS (2121 protected, 11 original edits, 0 additions)\nEXPERIMENT C CONTROLLED DEVICE TRIAL: ENABLED\nEXPERIMENT C PRODUCTION READY: NO\nDEVICE IQ VALIDATION: NOT RUN\n')
 (OUT/'26973_REAL_GRADLE_TASKS.txt').write_text(''.join('PASS '+x+'\n' for x in tasks))
 (OUT/'26973_APK.sha256').write_text(sha(R/APKNAME)+'  '+APKNAME+'\n')
 wf=R/'.github/workflows/build-26973-change-aware.yml'
 (OUT/'26973_ACTUAL_EXECUTED_BUILDER.sha256').write_text(sha(R/'build_26973_incremental.py')+'  build_26973_incremental.py\n')
 (OUT/'26973_ACTUAL_EXECUTED_WORKFLOW.sha256').write_text(sha(wf)+'  '+wf.relative_to(R).as_posix()+'\n')
 (OUT/'26973_ACTIONS_IDENTITY.txt').write_text('git_sha='+os.getenv('GITHUB_SHA','NOT_IN_ACTIONS')+'\ngithub_run_id='+os.getenv('GITHUB_RUN_ID','NOT_IN_ACTIONS')+'\n')
 for item in ('26973_BASE_26972_FULL_APP.sha256','26973_EXPECTED_FULL_APP.sha256','26973_PROTECTED_SOURCE.sha256','26973_CHANGED_RUNTIME_ALLOWLIST.txt','26973_ADDED_RUNTIME_PATHS.txt','26973_MODIFIED_ORIGINAL_PATHS.txt','26973_DELETED_RUNTIME_PATHS.txt','26973_NATIVE_RELEASE_ALLOWLIST.txt','26973_AUTHORITY_AND_SCOPE.json'):
  shutil.copy2(R/item,OUT/item)
 shutil.copy2(R/'build_26973_incremental.py',OUT/'ACTUAL_EXECUTED_build_26973_incremental.py')
 shutil.copy2(wf,OUT/'ACTUAL_EXECUTED_build-26973-change-aware.yml')
 with (OUT/'26973_candidate_app_source.tar.gz').open('wb') as f:
  with gzip.GzipFile(filename='',mode='wb',compresslevel=1,mtime=0,fileobj=f) as gz:
   with tarfile.open(fileobj=gz,mode='w') as t:
    for path in sorted(parse(R/'26973_EXPECTED_FULL_APP.sha256')):
     src=R/path;m=t.gettarinfo(str(src),arcname=path);m.uid=m.gid=0;m.uname=m.gname='';m.mtime=0
     with src.open('rb') as opened:t.addfile(m,opened)
 (OUT/'26973_candidate_app_source.tar.gz.sha256').write_text(sha(OUT/'26973_candidate_app_source.tar.gz')+'  26973_candidate_app_source.tar.gz\n')
 print('PASS actual 26973 Android APK, published-source TAR, historical 26972 authority and protected source; controlled C trial / device IQ NOT RUN')

if __name__=='__main__':
 try:
  parser=argparse.ArgumentParser();parser.add_argument('command',choices=('seal','fetch','prepare-base','install','regress','stage-native','verify-compiled','finalize'));args=parser.parse_args()
  globals()[args.command.replace('-','_')]()
 except Exception as e:print('26973 BUILD ERROR:',e,file=sys.stderr);sys.exit(1)
