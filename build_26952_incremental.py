#!/usr/bin/env python3
"""Photon 26952: sealed successful 26951 Actions source, current RawLens two-radius chroma,
SDR bright-rim guard, and official sha-pinned 2.3.94 LKR dual-ABI upgrade.
ALL actual GPU shader, NDK, Kotlin, Java and APK compilation remains mandatory in Actions.
"""
import argparse,gzip,hashlib,io,json,os,pathlib,re,shutil,subprocess,sys,tarfile,tempfile,urllib.request,zipfile
R=pathlib.Path(__file__).resolve().parent
TMP=R/'.photon_26952_work';OUT=R/'photon_26952_outputs'
ART=TMP/'26951-success.zip';BASE=TMP/'authority_26951';CAND=TMP/'candidate_26952'
REPO='SkyKing0007/Photon-Camera';BRANCH='experimental-clean-photon-rebuild'
RUN=44140403857;COMMIT='bd3b116553f55317590e54978fe5f659398f9752';ART_ID=14355356084
ART_SHA='fc008cda622c805f89706894a1e32788a208027303e43e17a124aa6769c86988'
TAR_SHA='a03f03e3d66c89741c5e562fd36596492c49f1c631c9cf0e665ee6a164f78eab'
BUILDER_SHA='ec7b8baa6329a0c7c7181fb4e70479c27542b102b287bcd669c90e5bafdf5010'
WORKFLOW_SHA='40980c9badbe157fab569971f063966360ca9f0b6020792df1f1dd2be069966b'
PRIOR_APK_SHA='69dc07e3a90286cdf63ac99cae8fe07a15f300aa000a98e12aed2b42fedea4d3'
PRIOR_APK_NAME='IrisCamera-0.9726951-26951-iris-rawr-debug.apk'
APKNAME='IrisCamera-0.9726952-26952-iris-rawr-debug.apk'
NBASE=2054;NFILES=2055;NCHANGE=4;NADDED=1;NPROTECTED=2050
REQUIRED={
 'app/src/main/assets/shaders/motionv2/render.glsl',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932RawLensMedian.kt',
 'app/version.properties',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26931LkrBridge.java',
}
ADDED={'app/src/main/assets/licenses/rawlens_2_3_94_lkr_gpl_notice.txt'}
NATIVE_ALLOW={f'app/build/verified_rawlens26931/jniLibs/{abi}/{name}' for abi in ('arm64-v8a','armeabi-v7a') for name in ('liblkrpipeline.so','libsrpipeline.so')}
STAGE1_FILES=['README_PHOTON_26952.md','26952_COMMIT_MESSAGE.txt','26952_LOCAL_VERIFICATION.txt',
 '26951_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml','26952_BASE_LKR_NATIVE_BRIDGE_REFERENCE.java',
 'build_26952_incremental.py','prepare_26952_native.py','test_26952_native.py','test_26952_source.py',
 'test_26952_chroma.py','test_26952_halo.py','test_26952_patches.py','test_26952_sealed_negatives.py',
 'test_26952_workflow_refs.py','replay_26952_inherited_glsl.py','replay_26952_26943_contract.py','compile_26952_shaders.sh','26952_BASE_26951_FULL_APP.sha256',
 '26952_EXPECTED_FULL_APP.sha256','26952_PROTECTED_SOURCE.sha256','26952_CHANGED_RUNTIME_ALLOWLIST.txt',
 '26952_ADDED_RUNTIME_PATHS.txt','26952_DELETED_RUNTIME_PATHS.txt','26952_NATIVE_RELEASE_ALLOWLIST.txt',
 '26952_FORWARD_FULLINDEX.patch','26952_ROLLBACK_FULLINDEX.patch','26952_STAGE_1_UPLOAD_PATHS.txt',
 '26952_STAGE_2_UPLOAD_PATHS.txt','26952_STAGE_3_UPLOAD_PATHS.txt','26952_EXPECTED_ACTION_EXECUTABLES.txt']

def fail(msg):raise RuntimeError('26952 BLOCKED: '+str(msg))
def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def parse(path):
 d={}
 for line in path.read_text().splitlines():
  try:h,p=line.split('  ',1)
  except ValueError:fail('malformed SHA manifest')
  if not re.fullmatch('[0-9a-f]{64}',h) or not p.startswith('app/') or '..' in pathlib.PurePosixPath(p).parts or p in d:fail('invalid manifest entry '+p)
  d[p]=h
 return d
def scan(root):
 out={}
 for p in [*(root/'app/src').rglob('*'),root/'app/build.gradle',root/'app/version.properties']:
  if p.is_symlink():fail('source symlink '+str(p))
  if p.is_file():out[p.relative_to(root).as_posix()]=sha(p)
 return out
def exact(root,manifest,label):
 want=parse(R/manifest);got=scan(root)
 if want!=got:
  missing=sorted(set(want)-set(got));extra=sorted(set(got)-set(want));changed=sorted(k for k in want.keys()&got.keys() if want[k]!=got[k]);fail(f'{label}: missing={missing[:6]} added={extra[:6]} wrong={changed[:6]}')
 print('PASS',label,len(got));return got
def scope():
 old=parse(R/'26952_BASE_26951_FULL_APP.sha256');new=parse(R/'26952_EXPECTED_FULL_APP.sha256')
 changed=set((R/'26952_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines());added=set((R/'26952_ADDED_RUNTIME_PATHS.txt').read_text().splitlines());deleted=set((R/'26952_DELETED_RUNTIME_PATHS.txt').read_text().splitlines())
 if (len(old),len(new),len(changed),len(added),len(old)-len(changed))!=(NBASE,NFILES,NCHANGE,NADDED,NPROTECTED):fail('source counts wrong')
 if changed!=REQUIRED or added!=ADDED or deleted or set(new)!=set(old)|ADDED or {p for p in old if new.get(p)!=old[p]}!=REQUIRED:fail('source allowlist or diff wrong')
 if parse(R/'26952_PROTECTED_SOURCE.sha256')!={p:h for p,h in old.items() if p not in REQUIRED}:fail('protected source hash changed')
 if set((R/'26952_NATIVE_RELEASE_ALLOWLIST.txt').read_text().splitlines())!=NATIVE_ALLOW:fail('not exactly four binary upgrade paths')
 for p in changed|added:
  if '/vendor/' in p or '/jniLibs/' in p or p.endswith(('.so','.aar','.jar','.spv')):fail('source/vendor modification out of scope')
 if old['app/build.gradle']!=new['app/build.gradle']:fail('Gradle infrastructure source changed')
 if old['app/version.properties']==new['app/version.properties']:fail('version not advanced')
 return changed,added,old,new

def seal():
 for n in ('ART_SHA','TAR_SHA','BUILDER_SHA','WORKFLOW_SHA','PRIOR_APK_SHA'):
  if not re.fullmatch(r'[0-9a-f]{64}',globals()[n]):fail('noncanonical successful authority SHA '+n)
 changed,added,old,new=scope(); sealed={}
 for line in (R/'26952_HANDOFF_HASHES.sha256').read_text().splitlines():
  try:h,p=line.split('  ',1)
  except ValueError:fail('invalid seal line')
  if p in sealed or not (R/p).is_file() or sha(R/p)!=h:fail('missing/tampered staged file '+p)
  sealed[p]=h
 wf='.github/workflows/build-26952-change-aware.yml';trigger='TRIGGER_26952.txt'
 wanted=set(STAGE1_FILES)|{wf,trigger}|{'handoff_payload_26952/'+p for p in changed|added}
 if set(sealed)!=wanted:fail('seal universe mismatch '+repr(sorted(set(sealed)^wanted)[:12]))
 stages=[(R/f'26952_STAGE_{i}_UPLOAD_PATHS.txt').read_text().splitlines() for i in (1,2,3)]
 if stages[0]!=sorted((wanted|{'26952_HANDOFF_HASHES.sha256'})-{wf,trigger}) or stages[1]!=[wf] or stages[2]!=[trigger]:fail('three stage upload lists invalid')
 overlay={p.relative_to(R/'handoff_payload_26952').as_posix() for p in (R/'handoff_payload_26952').rglob('*') if p.is_file()}
 if overlay!=changed|added or any(sha(R/'handoff_payload_26952'/p)!=new[p] for p in changed|added):fail('overlay mismatch')
 subprocess.run([sys.executable,'-S','test_26952_workflow_refs.py'],cwd=R,check=True)
 print('PASS full three-stage seal, exact 26951 authority, 2050 protected source, four explicit external-native runtime paths')

def fetch():
 seal();token=os.getenv('GITHUB_TOKEN','')
 if not token or os.getenv('GITHUB_REPOSITORY')!=REPO or os.getenv('GITHUB_REF_NAME')!=BRANCH:fail('Actions token/repository/branch absent')
 def get(end):
  req=urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+end,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'})
  with urllib.request.urlopen(req,timeout=120) as res:return json.load(res)
 run=get('actions/runs/'+str(RUN));art=get('actions/artifacts/'+str(ART_ID))
 if run.get('id')!=RUN or run.get('conclusion')!='success' or run.get('head_sha')!=COMMIT or run.get('head_branch')!=BRANCH:fail('26951 successful run identity mismatch')
 if art.get('id')!=ART_ID or art.get('expired') or art.get('digest')!='sha256:'+ART_SHA or art.get('workflow_run',{}).get('id') not in (RUN,None):fail('26951 published artifact identity mismatch')
 TMP.mkdir(exist_ok=True)
 req=urllib.request.Request('https://api.github.com/repos/'+REPO+'/actions/artifacts/'+str(ART_ID)+'/zip',headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'})
 with urllib.request.urlopen(req,timeout=180) as src,ART.open('wb') as dst:shutil.copyfileobj(src,dst,length=4*1024*1024)
 if sha(ART)!=ART_SHA:fail('actual 26951 artifact download SHA mismatch')
 print('PASS EXACT successful 26951 published artifact sha256 '+ART_SHA)

def safe_tar(raw,dst):
 with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as tar:
  for m in tar:
   p=pathlib.PurePosixPath(m.name)
   if not p.parts or p.is_absolute() or p.parts[0]!='app' or '..' in p.parts or not m.isfile() or m.issym() or m.islnk():fail('unsafe 26951 TAR member '+m.name)
  tar.extractall(dst,filter='data')
def prior_artifact():
 if not ART.is_file() or sha(ART)!=ART_SHA:fail('26951 artifact missing/incorrect')
 return zipfile.ZipFile(ART)
def prepare():
 seal()
 for d in (BASE,CAND):
  if d.exists():shutil.rmtree(d)
 BASE.mkdir(parents=True)
 with prior_artifact() as z:
  if z.testzip():fail('26951 artifact ZIP CRC')
  def get(s):
   p='photon_26951_outputs/'+s
   if p not in z.namelist():fail('26951 receipt missing '+p)
   return z.read(p)
  raw=get('26951_candidate_app_source.tar.gz')
  if hashlib.sha256(raw).hexdigest()!=TAR_SHA or get('26951_candidate_app_source.tar.gz.sha256')!=f'{TAR_SHA}  26951_candidate_app_source.tar.gz\n'.encode():fail('26951 compiled TAR wrong')
  expected=(R/'26952_BASE_26951_FULL_APP.sha256').read_bytes()
  if get('26951_PREBUILD_SEALED_APP.sha256')!=expected or get('26951_EXPECTED_FULL_APP.sha256')!=expected:fail('26951 compiled source manifest wrong')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build_26951_incremental.py')).hexdigest()!=BUILDER_SHA or BUILDER_SHA not in get('26951_ACTUAL_EXECUTED_BUILDER.sha256').decode():fail('26951 actual executed builder SHA wrong')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build-26951-change-aware.yml')).hexdigest()!=WORKFLOW_SHA or WORKFLOW_SHA not in get('26951_ACTUAL_EXECUTED_WORKFLOW.sha256').decode():fail('26951 actual executed workflow SHA wrong')
  if PRIOR_APK_NAME not in z.namelist() or PRIOR_APK_SHA not in get('26951_APK.sha256').decode():fail('26951 APK receipt wrong')
  ident=get('26951_ACTIONS_IDENTITY.txt').decode()
  if 'git_sha='+COMMIT not in ident or 'github_run_id='+str(RUN) not in ident:fail('26951 Actions identity mismatch')
  for k in ('REAL PINNED GLSL COMPILE: PASS','REAL SPIR-V VALIDATION: PASS','REAL KOTLIN COMPILE: PASS','REAL JAVA COMPILE: PASS','NATIVE/NDK COMPILE: PASS','REAL ANDROID Gradle :app:assembleDebug: PASS','RUNTIME SOURCE INVARIANCE: PASS'):
   if k not in get('26951_COMPILER_STATUS.txt').decode():fail('not successful 26951 compiled authority '+k)
  for task in (':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL'):
   if 'PASS '+task not in get('26951_REAL_GRADLE_TASKS.txt').decode():fail('prior 26951 actual Gradle task missing '+task)
  safe_tar(raw,BASE)
 exact(BASE,'26952_BASE_26951_FULL_APP.sha256','SUCCESSFUL 26951 compiled authority restored')
 shutil.copytree(BASE,CAND)
 for p in sorted(REQUIRED|ADDED):
  src=R/'handoff_payload_26952'/p;dst=CAND/p
  if not src.is_file():fail('source overlay missing '+p)
  dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
 exact(CAND,'26952_EXPECTED_FULL_APP.sha256','candidate-first exact 26952')
 if not (R/'gradlew').is_file() or not (R/'app/build.gradle').is_file():fail('real Gradle project checkout absent')
 if (R/'app/src').exists():shutil.rmtree(R/'app/src')
 shutil.copytree(CAND/'app/src',R/'app/src')
 shutil.copy2(CAND/'app/version.properties',R/'app/version.properties')
 shutil.copy2(CAND/'app/build.gradle',R/'app/build.gradle')
 if (R/'app/.cxx').exists():shutil.rmtree(R/'app/.cxx')
 exact(R,'26952_EXPECTED_FULL_APP.sha256','live 26952 exact restored')
 OUT.mkdir(exist_ok=True)
 (OUT/'26952_SOURCE_SCOPE.txt').write_text(f'SUCCESSFUL 26951 run={RUN} commit={COMMIT} artifact={ART_ID} artifact_sha={ART_SHA} actual_source_TAR_sha={TAR_SHA}\n26951 builder_sha={BUILDER_SHA} workflow_sha={WORKFLOW_SHA} apk_sha={PRIOR_APK_SHA}\nsource base={NBASE} new={NFILES} changed={NCHANGE} added={NADDED} protected={NPROTECTED}; native release binary override exactly four external paths (not source-tree modifications)\n'+''.join(n+'\n' for n in sorted(REQUIRED|ADDED)))
 print('PASS 26951 authority -> 26952 candidate-first, 2050 protected source')

def regress():
 seal();exact(R,'26952_EXPECTED_FULL_APP.sha256','26952 actual live source')
 for script in ('test_26952_source.py','test_26952_chroma.py','test_26952_halo.py','test_26952_patches.py'):
  subprocess.run([sys.executable,'-S',script,'--live'],cwd=R,check=True)
 print('PASS current 26952 source, dual-radius chroma, isolated highlight rim and exact forward/rollback')

def verify_compiled():
 regress()
 comp=OUT/'26952_REAL_GLSL_SPIRV_COMPILER.txt'
 if not comp.is_file() or 'PASS 26952 real ESSL300/310 medians and B render, SPIR-V validator/optimizer' not in comp.read_text():fail('new shader actual GLSL gate absent')
 for p in ('app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932RawLensMedian.kt'):
  if sha(R/p) not in comp.read_text():fail('current edited shader missing real compile receipt '+p)
 for n in ('app/src/main/assets/shaders/motionv2/gainmap.glsl', 'app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqMerge.comp','app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqMismatch.comp'):
  if sha(R/n)!=parse(R/'26952_BASE_26951_FULL_APP.sha256')[n]:fail('protected original 26951 shader changed '+n)
 subprocess.run([sys.executable,'-S','test_26952_native.py','--native'],cwd=R,check=True)
 (OUT/'26952_PREBUILD_SEALED_APP.sha256').write_bytes((R/'26952_EXPECTED_FULL_APP.sha256').read_bytes())
 print('PASS current shader compile, original unchanged shaders, upgraded native and 2050 protected')

def finalize():
 regress()
 if (OUT/'26952_PREBUILD_SEALED_APP.sha256').read_bytes()!=(R/'26952_EXPECTED_FULL_APP.sha256').read_bytes():fail('prebuild source seal missing')
 log=(OUT/'26952_gradle_assemble.log').read_text(errors='replace')
 tasks=(':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL')
 for task in tasks:
  if task not in log:fail('actual Gradle task absent '+task)
 subprocess.run([sys.executable,'-S','test_26952_native.py','--cmake'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','verify_26906_native_cache.py','postflight'],cwd=R,check=True)
 apks=list((R/'app/build/outputs/apk').rglob('*.apk'))
 if len(apks)!=1:fail('not exactly one actual APK')
 shutil.copy2(apks[0],R/APKNAME)
 if (R/APKNAME).stat().st_size<1000000:fail('actual APK small')
 subprocess.run([sys.executable,'-S','test_26952_native.py','--apk'],cwd=R,check=True)
 with zipfile.ZipFile(R/APKNAME) as z:
  if z.testzip() or not {'AndroidManifest.xml','classes.dex'}<=set(z.namelist()):fail('APK bytes invalid')
 (OUT/'26952_COMPILER_STATUS.txt').write_text('REAL PINNED GLSL COMPILE: PASS (original 26951 HDRQ and live 26952 ESSL300/310 LKR median + B SDR)\nREAL SPIR-V VALIDATION/OPTIMIZATION: PASS\nREAL KOTLIN COMPILE: PASS\nREAL JAVA COMPILE: PASS\nREAL TWO-ABI NDK/CMake COMPILE: PASS\nREAL ANDROID Gradle :app:assembleDebug: PASS\nPINNED RAWLENS 2.3.94 DUAL ABI NATIVE: PASS (exact APK release digest)\nRUNTIME SOURCE INVARIANCE: PASS (2050 protected)\nDEVICE VISUAL/TIMING QUALITY: NOT RUN\n')
 (OUT/'26952_REAL_GRADLE_TASKS.txt').write_text(''.join('PASS '+s+'\n' for s in tasks))
 (OUT/'26952_APK.sha256').write_text(sha(R/APKNAME)+'  '+APKNAME+'\n')
 wf=R/'.github/workflows/build-26952-change-aware.yml'
 (OUT/'26952_ACTUAL_EXECUTED_BUILDER.sha256').write_text(sha(R/'build_26952_incremental.py')+'  build_26952_incremental.py\n')
 (OUT/'26952_ACTUAL_EXECUTED_WORKFLOW.sha256').write_text(sha(wf)+'  .github/workflows/build-26952-change-aware.yml\n')
 (OUT/'26952_ACTIONS_IDENTITY.txt').write_text('git_sha='+os.getenv('GITHUB_SHA','NOT_IN_ACTIONS')+'\ngithub_run_id='+os.getenv('GITHUB_RUN_ID','NOT_IN_ACTIONS')+'\n')
 for p in ('26952_BASE_26951_FULL_APP.sha256','26952_EXPECTED_FULL_APP.sha256','26952_PROTECTED_SOURCE.sha256','26952_CHANGED_RUNTIME_ALLOWLIST.txt','26952_ADDED_RUNTIME_PATHS.txt','26952_DELETED_RUNTIME_PATHS.txt','26952_NATIVE_RELEASE_ALLOWLIST.txt'):
  shutil.copy2(R/p,OUT/p)
 shutil.copy2(R/'build_26952_incremental.py',OUT/'ACTUAL_EXECUTED_build_26952_incremental.py');shutil.copy2(wf,OUT/'ACTUAL_EXECUTED_build-26952-change-aware.yml')
 with (OUT/'26952_candidate_app_source.tar.gz').open('wb') as target:
  with gzip.GzipFile(filename='',mode='wb',compresslevel=1,mtime=0,fileobj=target) as gz:
   with tarfile.open(fileobj=gz,mode='w') as tar:
    for p in sorted(parse(R/'26952_EXPECTED_FULL_APP.sha256')):
     src=R/p;m=tar.gettarinfo(str(src),arcname=p);m.uid=m.gid=0;m.uname=m.gname='';m.mtime=0
     with src.open('rb') as f:tar.addfile(m,f)
 (OUT/'26952_candidate_app_source.tar.gz.sha256').write_text(sha(OUT/'26952_candidate_app_source.tar.gz')+'  26952_candidate_app_source.tar.gz\n')
 print('PASS one real 26952 APK, original 26951 compiled authority, four pinned dual-ABI native binaries, 2050 protected')
if __name__=='__main__':
 try:
  p=argparse.ArgumentParser();p.add_argument('command',choices=('seal','fetch','prepare','regress','verify-compiled','finalize'));a=p.parse_args();globals()[a.command.replace('-','_')]()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
