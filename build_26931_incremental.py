#!/usr/bin/env python3
"""26931 candidate-first guarded LKR 2.2.86 from actual successful 26930 V1 compiled source.
No source commits, pushes or rebuild of 26930 APK. Only Actions compiles Iris 26931.
"""
from __future__ import annotations
import argparse,gzip,hashlib,json,os,pathlib,shutil,subprocess,sys,tarfile,urllib.request,zipfile
R=pathlib.Path(__file__).resolve().parent
TMP=R/'.photon_26931_work';OUT=R/'photon_26931_outputs'
ART=TMP/'26930-success.zip';BASE=TMP/'authority_26930';CAND=TMP/'candidate_26931'
RUN=43598629771;COMMIT='3c30cc4a94c6532707413352508b635db276cd75';ART_ID=14114749743
ART_SHA='545aab95f97674ed442677e27f577a44437b8683c6ef0aec56779d6b28a31dd6'
TAR_SHA='b922479f7c105c172211d2aed02fa4b8a76d7b5f5407328f39b5ed8531015044'
BUILDER_SHA='9cde95348023a89632d8262093e80d481664018e78ecb5269df48503a43ba9e6'
WORKFLOW_SHA='e3193d32d2f9b4b995cca9087be076efbe98017465b20338117773844af1f7d2'
PRIOR_APK_SHA='7807fde72a8e9672016dffdee457d4a5867983eac75a089600512bd6014a12ca'
REPO='SkyKing0007/Photon-Camera';BRANCH='experimental-clean-photon-rebuild'
APKNAME='IrisCamera-0.9726931-26931-iris-rawr-debug.apk'
NBASE=2041;NFILES=2046;NCHANGE=5;NADD=5;NPROTECTED=2036
REQUIRED={'app/build.gradle','app/version.properties',
          'app/src/main/cpp/CMakeLists.txt',
          'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
          'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'}
ADDED={'app/src/main/assets/licenses/rawlens_2_2_86_lkr_apache_notice.txt',
       'app/src/main/cpp/iris26864/Iris26931LkrAndroidInterop.cpp',
       'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26931LkrBridge.java',
       'app/src/main/java/com/matthew/rawlens/LkrBridge.java',
       'app/src/main/java/com/rawlens/srpipeline/SrpBridge.java'}
HISTORICAL=['verify_26904_v3_safety.py','verify_26904_v2_safety.py',
 'verify_26906_native_cache.py','test_26925_shader_abi.py',
 'test_26930_shader_contract.py','test_26930_shader_shadow.py',
 'test_26930_patch_proof.py','test_26930_sealed_negatives.py']
GLSL=['26930_CURRENT_GLSL_SPIRV_REAL_COMPILER.txt','26930_WRONSKI_SPIRV_REAL_COMPILER.txt']

def fail(s):raise RuntimeError('26931 BLOCKED: '+str(s))
def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def parse(p):
 out={}
 for line in p.read_text().splitlines():
  h,k=line.split('  ',1)
  if len(h)!=64 or not k.startswith('app/') or k in out or '..' in pathlib.PurePosixPath(k).parts:fail('bad manifest '+line)
  out[k]=h
 return out
def scan(root):
 out={}
 for p in [*(root/'app/src').rglob('*'),root/'app/build.gradle',root/'app/version.properties']:
  if p.is_symlink():fail('symlink within app source '+str(p))
  if p.is_file():out[p.relative_to(root).as_posix()]=sha(p)
 return out
def exact(root,name,label):
 exp=parse(R/name);actual=scan(root)
 if actual!=exp:
  fail(label+' mismatch missing='+str(sorted(exp.keys()-actual.keys())[:5])+ ' extra='+str(sorted(actual.keys()-exp.keys())[:5])+ ' changed='+str([p for p in exp if actual.get(p)!=exp[p]][:5]))
 print('PASS '+label+' '+str(len(actual)));return actual
def scope():
 base=parse(R/'26931_BASE_26930_FULL_APP.sha256');new=parse(R/'26931_EXPECTED_FULL_APP.sha256')
 changed=set((R/'26931_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
 added=set((R/'26931_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
 deleted=(R/'26931_DELETED_RUNTIME_PATHS.txt').read_text().strip()
 if (len(base),len(new),len(changed),len(added),len(base)-len(changed),bool(deleted))!=(NBASE,NFILES,NCHANGE,NADD,NPROTECTED,False):fail('scope counts invalid')
 if changed!=REQUIRED or added!=ADDED or {k for k in base if new.get(k)!=base[k]}!=changed or set(new)-set(base)!=added or set(base)-set(new):fail('source allowlist/protected exactly mismatched')
 protected={k:v for k,v in base.items() if k not in changed}
 if parse(R/'26931_PROTECTED_SOURCE.sha256')!=protected or len(protected)!=NPROTECTED:fail('protected bytes not frozen')
 for p in changed|added:
  if '/vendor/' in p or '/jniLibs/' in p or p.endswith(('.so','.jar','.aar')):fail('mutated protected vendor/native artifact '+p)
 if not (R/'handoff_payload_26931/app/version.properties').is_file():fail('version required')
 return changed,added,base,new

def seal():
 changed,added,_,_=scope()
 rows={}
 for line in (R/'26931_HANDOFF_HASHES.sha256').read_text().splitlines():
  h,k=line.split('  ',1);p=R/k
  if k in rows or not p.is_file() or sha(p)!=h:fail('handoff tampering / missing staged file '+k)
  rows[k]=h
 essential={'build_26931_incremental.py','prepare_26931_rawlens_binaries.py',
  'test_26931_source.py','test_26931_patch_proof.py','test_26931_abi_routes.py',
  'test_26931_shader_contract.py','compile_26931_lkr_gles.sh',
  'test_26931_native_integrity.py','test_26931_sealed_negatives.py','test_26931_workflow_refs.py',
  '26931_FORWARD_FULLINDEX.patch','26931_ROLLBACK_FULLINDEX.patch',
  '26931_BASE_26930_FULL_APP.sha256','26931_EXPECTED_FULL_APP.sha256',
  '26931_PROTECTED_SOURCE.sha256','26931_CHANGED_RUNTIME_ALLOWLIST.txt',
  '26931_ADDED_RUNTIME_PATHS.txt','26931_DELETED_RUNTIME_PATHS.txt',
  '26931_EXPECTED_ACTION_EXECUTABLES.txt','TRIGGER_26931.txt',
  '.github/workflows/build-26931-change-aware.yml',
  '26931_V1_STAGE_1_UPLOAD_PATHS.txt','26931_V1_STAGE_2_UPLOAD_PATHS.txt',
  '26931_V1_STAGE_3_UPLOAD_PATHS.txt'}
 if not essential.issubset(rows):fail('essential handoff files missing '+str(sorted(essential-set(rows))))
 stages=[(R/f'26931_V1_STAGE_{i}_UPLOAD_PATHS.txt').read_text().splitlines() for i in (1,2,3)]
 for s in stages:
  if s!=sorted(s) or len(s)!=len(set(s)):fail('unsorted/duplicate upload stage')
 wf='.github/workflows/build-26931-change-aware.yml';tr='TRIGGER_26931.txt'
 if stages[1]!=[wf] or stages[2]!=[tr] or set(stages[0]) != (set(rows)|{'26931_HANDOFF_HASHES.sha256'})-{wf,tr}:fail('three-stage upload coverage/order')
 staged={k.removeprefix('handoff_payload_26931/') for k in rows if k.startswith('handoff_payload_26931/')}
 actual={p.relative_to(R/'handoff_payload_26931').as_posix() for p in (R/'handoff_payload_26931').rglob('*') if p.is_file()}
 if staged!=changed|added or actual!=staged:fail('runtime source overlay mismatch')
 for p in changed|added:
  if sha(R/'handoff_payload_26931'/p)!=parse(R/'26931_EXPECTED_FULL_APP.sha256')[p]:fail('changed source hash '+p)
 text=(R/wf).read_text()
 for pin in HISTORICAL+['build_26931_incremental.py prepare','build_26931_incremental.py finalize',
     ':app:assembleDebug','prepare_26931_rawlens_binaries.py','test_26931_native_integrity.py --apk','compile_26931_lkr_gles.sh',
     '26930 V1','rawLens','26931']:
  if pin not in text:fail('workflow missing required historical/current gate '+pin)
 if text.count('actions/upload-artifact@v4')!=1 or 'build_26930_incremental.py finalize' in text:fail('workflow rebuilds previous 26930 APK or extra publish')
 if text.index('build_26930_incremental.py verify-compiled')>=text.index('build_26931_incremental.py prepare') or text.index('build_26931_incremental.py verify-compiled') >= text.rfind('./gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace'):fail('wrong authority/overlay/compiler order')
 if not globals().get('PACKAGE_ONLY',False):
  for script in HISTORICAL:
   if not (R/script).is_file():fail('historical script absent from root GitHub checkout '+script)
 subprocess.run(['python3','-S','test_26931_workflow_refs.py']+([] if globals().get('PACKAGE_ONLY',False) else ['--on-actions']),cwd=R,check=True)
 print(f'PASS source-sealed 26930->26931 exactly {NBASE}->{NFILES}, {NCHANGE} changed, {NADD} added, {NPROTECTED} protected, no deletion')

def fetch():
 seal()
 token=os.getenv('GITHUB_TOKEN','')
 if not token:fail('GitHub Actions token absent')
 if os.getenv('GITHUB_REPOSITORY')!=REPO or os.getenv('GITHUB_REF_NAME')!=BRANCH:fail('wrong Actions project/branch')
 def gh(path):
  req=urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+path,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'})
  with urllib.request.urlopen(req,timeout=120) as rsp:return json.load(rsp)
 run=gh('actions/runs/'+str(RUN));art=gh('actions/artifacts/'+str(ART_ID))
 if run.get('id')!=RUN or run.get('conclusion')!='success' or run.get('head_sha')!=COMMIT or run.get('head_branch')!=BRANCH:fail('not exact successful 26930 V1 GitHub Actions run')
 if art.get('id')!=ART_ID or art.get('expired') or art.get('digest')!='sha256:'+ART_SHA:fail('published 26930 artifact invalid or expired')
 TMP.mkdir(exist_ok=True)
 subprocess.run(['curl','--fail','--location','--retry','3','--silent','--show-error',
  '-H','Authorization: Bearer '+token,'-H','Accept: application/vnd.github+json',
  'https://api.github.com/repos/'+REPO+'/actions/artifacts/'+str(ART_ID)+'/zip','-o',str(ART)],check=True)
 if sha(ART)!=ART_SHA:fail('26930 Actions artifact downloaded SHA mismatch')
 print('PASS exact 26930 V1 Actions successful run, published artifact, SHA')

def safe_tar(path,where):
 with tarfile.open(path,'r:gz') as t:
  for entry in t:
   p=pathlib.PurePosixPath(entry.name)
   if not p.parts or p.parts[0]!='app' or p.is_absolute() or '..' in p.parts or not(entry.isfile() or entry.isdir()):fail('unsafe candidate tar member '+entry.name)
  t.extractall(where,filter='data')

def prepare():
 seal()
 if not ART.is_file() or sha(ART)!=ART_SHA:fail('successful 26930 artifact absent')
 for p in (BASE,CAND):
  if p.exists():shutil.rmtree(p)
 BASE.mkdir(parents=True)
 with zipfile.ZipFile(ART) as zipped:
  def get(name):
   path='photon_26930_outputs/'+name
   if path not in zipped.namelist():fail('26930 artifact missing '+name)
   return zipped.read(path)
  data=get('26930_candidate_app_source.tar.gz')
  if hashlib.sha256(data).hexdigest()!=TAR_SHA:fail('26930 original compiled candidate TAR SHA mismatch')
  if get('26930_PREBUILD_SEALED_APP.sha256')!=(R/'26931_BASE_26930_FULL_APP.sha256').read_bytes():fail('successful 26930 original compiled manifest does not match')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build_26930_incremental.py')).hexdigest()!=BUILDER_SHA or BUILDER_SHA not in get('26930_ACTUAL_EXECUTED_BUILDER.sha256').decode():fail('26930 actual builder SHA')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build-26930-change-aware.yml')).hexdigest()!=WORKFLOW_SHA or WORKFLOW_SHA not in get('26930_ACTUAL_EXECUTED_WORKFLOW.sha256').decode():fail('26930 actual workflow SHA')
  if PRIOR_APK_SHA not in get('26930_APK.sha256').decode():fail('26930 actually published APK hash')
  tasks=get('26930_REAL_GRADLE_TASKS.txt').decode()
  for task in (':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',
               ':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',
               ':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',
               ':app:assembleDebug','BUILD SUCCESSFUL'):
   if 'PASS '+task not in tasks:fail('26930 successful Android compiler authority absent '+task)
  if 'BUILD SUCCESSFUL' not in get('26930_gradle_assemble.log').decode(errors='replace'):fail('26930 real Gradle authority failed')
  for flag in ('REAL PINNED GLSL COMPILE: PASS','REAL SPIR-V VALIDATION: PASS','REAL KOTLIN COMPILE: PASS',
               'REAL JAVA COMPILE: PASS','NATIVE/NDK COMPILE: PASS','REAL ANDROID Gradle :app:assembleDebug: PASS',
               'RUNTIME SOURCE INVARIANCE: PASS'):
   if flag not in get('26930_COMPILER_STATUS.txt').decode():fail('26930 verification not proven '+flag)
  (TMP/'26930_candidate_app_source.tar.gz').write_bytes(data)
 safe_tar(TMP/'26930_candidate_app_source.tar.gz',BASE)
 exact(BASE,'26931_BASE_26930_FULL_APP.sha256','26930 V1 compiled authority')
 shutil.copytree(BASE,CAND)
 changed,added,_,_=scope()
 for k in sorted(changed|added):
  original=R/'handoff_payload_26931'/k;dest=CAND/k
  if not original.is_file() or (k in changed and not dest.is_file()) or (k in added and dest.exists()):fail('overlay misclassified '+k)
  dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(original,dest)
 exact(CAND,'26931_EXPECTED_FULL_APP.sha256','26931 candidate overlay')
 if not (R/'gradlew').is_file() or not (R/'app/build.gradle').is_file():fail('actual Android repo checkout unavailable')
 if (R/'app/src').exists():shutil.rmtree(R/'app/src')
 shutil.copytree(CAND/'app/src',R/'app/src')
 shutil.copy2(CAND/'app/version.properties',R/'app/version.properties')
 shutil.copy2(CAND/'app/build.gradle',R/'app/build.gradle')
 if (R/'app/.cxx').exists():shutil.rmtree(R/'app/.cxx')
 exact(R,'26931_EXPECTED_FULL_APP.sha256','26931 LIVE before compiler')
 OUT.mkdir(exist_ok=True)
 (OUT/'26931_SOURCE_SCOPE.txt').write_text(
  f'base=26930 V1 run={RUN} commit={COMMIT} artifact={ART_ID}\n'+
  f'ZIP_SHA={ART_SHA} TAR_SHA={TAR_SHA} BUILDER_SHA={BUILDER_SHA} WORKFLOW_SHA={WORKFLOW_SHA} APK_SHA={PRIOR_APK_SHA}\n'+
  f'files={NFILES} changed={NCHANGE} added={NADD} protected={NPROTECTED} deleted=0\n'+
  'RAWLENS_2_2_86 EXACT native stage, iris B SR ON 3x2, 1x framing 2x output, full 50MP\n'+
  '\n'.join(sorted(changed|added))+'\n')
 print('PASS candidate first, no stale repository app/src or 26930 APK recompile')

def regress():
 seal();exact(R,'26931_EXPECTED_FULL_APP.sha256','live 26931 protected source')
 for s in ('test_26931_source.py','test_26931_abi_routes.py','test_26931_patch_proof.py'):
  subprocess.run(['python3','-S',s,'--live'],cwd=R,check=True)
 print('PASS 26931 complete LKR source route, user 3x2, unchanged other modes, rollback')

def verify_compiled():
 regress()
 for key in GLSL:
  current=R/'photon_26930_outputs'/key
  if not current.is_file() or '16.5.0' not in current.read_text() or 'PASS' not in current.read_text():fail('inherited 26930 real unchanged shaders not compiled '+key)
 # 26931 introduces THREE newly active ESSL paths, so they must be compiled
 # with the real pinned 16.5 compiler and optimized/validated OpenGL SPIR-V.
 report=OUT/'26931_LKR_GLES_SPIRV_REAL_COMPILER.txt'
 if not report.is_file() or '16.5.0' not in report.read_text() or 'PASS' not in report.read_text():fail('new 26931 real LKR ESSL300/310/SPIR-V compiler proof missing')
 for label in ('lkr_temporary_wb','lkr_physical_lsc','lkr_2x_guide'):
  if not (OUT/f'26931_{label}_es300.frag').is_file() or not (OUT/f'26931_{label}_es310.frag').is_file():fail('new LKR shader expanded source missing '+label)
  if sha(OUT/f'26931_{label}_es300.frag') not in report.read_text():fail('new active LKR shader source not compiled '+label)
 # 26930 also verified all its original old shaders before 26931 overlay.
 # Native original LKR upstream GPU shaders are embedded in exact-release
 # ELF bytes and validated by SHA before shipping, not substituted by mocks.
 base=parse(R/'26931_BASE_26930_FULL_APP.sha256');new=parse(R/'26931_EXPECTED_FULL_APP.sha256')
 for p in base:
  if p.endswith(('.comp','.frag','.glsl','.vert')) and base[p]!=new[p]:fail('unexpected shader change, real shader compile proof invalid '+p)
 subprocess.run(['python3','-S','test_26931_shader_contract.py','--live'],cwd=R,check=True)
 subprocess.run(['python3','-S','test_26931_native_integrity.py','--native'],cwd=R,check=True)
 (OUT/'26931_PREBUILD_SEALED_APP.sha256').write_bytes((R/'26931_EXPECTED_FULL_APP.sha256').read_bytes())
 (OUT/'26931_GLSL_INHERITED_PARITY.txt').write_text('PASS 26930 V1 pinned real GLSL16.5, ESSL300/310, Vulkan prod/trace and SPIR-V optimizer/validator compiled on exact protected-identical original shader source BEFORE 26931 overlay\nPASS all 26931 protected GLSL source sha unchanged\nPASS original released RawLens SPIR-V is inside SHA-256 proven LKR binary, not synthesized\n')
 print('PASS current 26931 same GL shader bytes previously actually compiled, original LKR native libs both ABIs checked; real JNI NDK compile required next')

def finalize():
 regress()
 if not (OUT/'26931_PREBUILD_SEALED_APP.sha256').is_file() or (OUT/'26931_PREBUILD_SEALED_APP.sha256').read_bytes()!=(R/'26931_EXPECTED_FULL_APP.sha256').read_bytes():fail('26931 source mutated after native/GPU pre-build seal')
 log=(OUT/'26931_gradle_assemble.log').read_text(errors='replace')
 tasks=[':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',
        ':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',
        ':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',
        ':app:assembleDebug','BUILD SUCCESSFUL']
 for task in tasks:
  if task not in log:fail('actual Android NDK/Kotlin/Java/assemble compiler task absent '+task)
 subprocess.run(['python3','-S','test_26931_native_integrity.py','--cmake'],cwd=R,check=True)
 subprocess.run(['python3','-S','verify_26906_native_cache.py','postflight'],cwd=R,check=True)
 apks=list((R/'app/build/outputs/apk').rglob('*.apk'))
 if len(apks)!=1:fail('single assembled Android APK required '+str(apks))
 shutil.copy2(apks[0],R/APKNAME)
 if (R/APKNAME).stat().st_size<1_000_000:fail('suspicious Android build size')
 subprocess.run(['python3','-S','test_26931_native_integrity.py','--apk'],cwd=R,check=True)
 (OUT/'26931_COMPILER_STATUS.txt').write_text('REAL PINNED GLSL COMPILE: PASS (source identical to actually compiled 26930 V1)\nREAL SPIR-V VALIDATION: PASS (26930 protected GL shaders, original SHA-locked RawLens SPIR-V native)\nREAL KOTLIN COMPILE: PASS\nREAL JAVA COMPILE: PASS\nNATIVE/NDK COMPILE: PASS (arm64-v8a, armeabi-v7a)\nREAL ANDROID Gradle :app:assembleDebug: PASS\nORIGINAL RAWLENS LKR SHARED NATIVE: PASS (both ABIs)\nRUNTIME SOURCE INVARIANCE: PASS\nDEVICE IMAGE QUALITY: NOT RUN\n')
 (OUT/'26931_REAL_GRADLE_TASKS.txt').write_text(''.join('PASS '+task+'\n' for task in tasks))
 (OUT/'26931_APK.sha256').write_text(sha(R/APKNAME)+'  '+APKNAME+'\n')
 wf=R/'.github/workflows/build-26931-change-aware.yml'
 (OUT/'26931_ACTUAL_EXECUTED_BUILDER.sha256').write_text(sha(R/'build_26931_incremental.py')+'  build_26931_incremental.py\n')
 (OUT/'26931_ACTUAL_EXECUTED_WORKFLOW.sha256').write_text(sha(wf)+'  .github/workflows/build-26931-change-aware.yml\n')
 (OUT/'26931_ACTIONS_IDENTITY.txt').write_text('git_sha='+os.getenv('GITHUB_SHA','NOT_IN_ACTIONS')+'\ngithub_run_id='+os.getenv('GITHUB_RUN_ID','NOT_IN_ACTIONS')+'\n')
 for name in ('26931_BASE_26930_FULL_APP.sha256','26931_EXPECTED_FULL_APP.sha256',
   '26931_PROTECTED_SOURCE.sha256','26931_CHANGED_RUNTIME_ALLOWLIST.txt','26931_ADDED_RUNTIME_PATHS.txt','26931_DELETED_RUNTIME_PATHS.txt'):
  shutil.copy2(R/name,OUT/name)
 shutil.copy2(R/'build_26931_incremental.py',OUT/'ACTUAL_EXECUTED_build_26931_incremental.py')
 shutil.copy2(wf,OUT/'ACTUAL_EXECUTED_build-26931-change-aware.yml')
 with (OUT/'26931_candidate_app_source.tar.gz').open('wb') as target:
  with gzip.GzipFile(filename='',mode='wb',compresslevel=1,mtime=0,fileobj=target) as gz:
   with tarfile.open(fileobj=gz,mode='w') as t:
    for key in sorted(parse(R/'26931_EXPECTED_FULL_APP.sha256')):
     p=R/key;meta=t.gettarinfo(str(p),arcname=key)
     meta.uid=meta.gid=0;meta.uname=meta.gname='';meta.mtime=0
     with p.open('rb') as source:t.addfile(meta,source)
 (OUT/'26931_candidate_app_source.tar.gz.sha256').write_text(sha(OUT/'26931_candidate_app_source.tar.gz')+'  26931_candidate_app_source.tar.gz\n')
 print('PASS one genuine 26931 Actions APK build, current compiled source, all receipts, original RawLens native 2 ABIs')

if __name__=='__main__':
 try:
  p=argparse.ArgumentParser();p.add_argument('command',choices=('seal','fetch','prepare','regress','verify-compiled','finalize'));p.add_argument('--package-only',action='store_true')
  args=p.parse_args();globals()['PACKAGE_ONLY']=args.package_only
  globals()[args.command.replace('-','_')]()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
