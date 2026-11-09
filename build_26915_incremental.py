#!/usr/bin/env python3
"""Photon 26915 candidate-first, real Actions guarded successor.
Successful runtime authority: exact 26914 V2 compiled candidate, NOT repository app/src.
Changes: B Photo SR ON all NORMAL, strict early frozen exposure, stride-aware 1x
RGBA16F guide (NOT Wronski or AMaZE algorithm changes); 7-path allowlist.
"""
from __future__ import annotations
import argparse,hashlib,json,os,pathlib,shutil,subprocess,sys,tarfile,urllib.request,zipfile
R=pathlib.Path(__file__).resolve().parent
WORK=R/'.photon_26915_work';OUT=R/'photon_26915_outputs'
ART=WORK/'26914_v2_success.zip';BASE=WORK/'authority_26914_v2';CAND=WORK/'candidate_26915'
REPO='SkyKing0007/Photon-Camera';BRANCH='experimental-clean-photon-rebuild'
RUN=42679211318;COMMIT='dddbf99a1a6977fc02e973fce1631195e822f264';ART_ID=13703245819
ART_SHA='09cf9bf689eb1c2111aa75c8837f733a094e0c8d546653fe4f852eaea6ecaa15'
TAR_SHA='bf735dc2c49730d65f11c1272e7443a5c41215c1964b2e3cffcf97e135b39631'
BUILDER_SHA='0cc4c6c6d4829f89fe5a7e8d22f5585ada746b36a66893470dc1351cae374376'
WORKFLOW_SHA='5f5af7aab0a46fdf71abc2c89e4bfb3803321fd93424723ce2a6717b5c90cc84'
PRIOR_APK_SHA='3c658efb315e2a648379116609c750e2c2d6c28ee793892f9b5edf046cc0ec7f'
GENERATED='app/src/main/assets/iris26856/rawr/amaze/spv/amaze_export.spv'
APKNAME='IrisCamera-0.9726915-26915-iris-rawr-debug.apk'

def fail(msg):raise RuntimeError('26915 BLOCKED: '+str(msg))
def sha(p):
 d=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):d.update(b)
 return d.hexdigest()
def parse(p):
 d={}
 for ln in p.read_text().splitlines():
  h,name=ln.split('  ',1)
  if name in d or len(h)!=64 or not name.startswith('app/') or '..' in pathlib.PurePosixPath(name).parts:fail('bad SHA row '+ln)
  d[name]=h
 return d
def scan(src):
 d={}
 root=src/'app/src'
 if root.is_symlink() or not root.is_dir():fail('Android runtime source missing/symlinked')
 source_files=list(root.rglob('*'))
 source_files.extend([src/'app/build.gradle',src/'app/version.properties'])
 for p in source_files:
  if p.is_symlink():fail('runtime source symlink '+str(p))
  if p.is_file():d[p.relative_to(src).as_posix()]=sha(p)
 return d
def exact(src,manifest,title):
 expected=parse(manifest);actual=scan(src)
 if expected!=actual:
  miss=sorted(expected.keys()-actual.keys());extra=sorted(actual.keys()-expected.keys());wrong=sorted(p for p in expected.keys()&actual.keys() if expected[p]!=actual[p]);fail(f'{title}: missing={miss[:5]} extra={extra[:5]} wrong={wrong[:9]}')
 print('PASS',title,len(expected),'source files');return expected

def seal():
 from verify_26915_handoff import verify
 verify()
 print('PASS 26915 sealed seven-path successor to successful 26914 V2')

def gh(path,token):
 req=urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+path,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'})
 with urllib.request.urlopen(req,timeout=100) as q:return json.load(q)
def fetch():
 seal();tok=os.getenv('GITHUB_TOKEN','')
 if not tok:fail('missing GitHub token for actual successful 26914 V2 artifact')
 if os.getenv('GITHUB_REPOSITORY',REPO)!=REPO or os.getenv('GITHUB_REF_NAME',BRANCH)!=BRANCH:fail('unexpected repo/branch')
 run=gh('actions/runs/'+str(RUN),tok);art=gh('actions/artifacts/'+str(ART_ID),tok)
 if run.get('conclusion')!='success' or run.get('head_sha')!=COMMIT or run.get('head_branch')!=BRANCH or run.get('id')!=RUN:fail('wrong last successful run')
 if art.get('id')!=ART_ID or art.get('expired') or art.get('digest')!='sha256:'+ART_SHA:fail('wrong last successful artifact')
 WORK.mkdir(exist_ok=True)
 subprocess.run(['curl','--fail','--location','--retry','3','--silent','--show-error',
                 '-H','Authorization: Bearer '+tok,'-H','Accept: application/vnd.github+json',
                 f'https://api.github.com/repos/{REPO}/actions/artifacts/{ART_ID}/zip','-o',str(ART)],check=True)
 if sha(ART)!=ART_SHA:fail('26914 V2 downloaded ZIP hash mismatch')
 print('PASS successful 26914 V2 run, actual artifact and digest',ART_SHA)

def safe_tar(tarpath,dest):
 with tarfile.open(tarpath,'r:gz') as t:
  for m in t.getmembers():
   p=pathlib.PurePosixPath(m.name)
   if p.is_absolute() or not p.parts or p.parts[0]!='app' or '..' in p.parts or not(m.isfile() or m.isdir()):fail('bad TAR member '+m.name)
  t.extractall(dest,filter='data')
def prepare():
 seal()
 if not ART.is_file() or sha(ART)!=ART_SHA:fail('successfully compiled 26914 V2 ZIP missing/hash mismatch')
 for x in (BASE,CAND):
  if x.exists():shutil.rmtree(x)
 BASE.mkdir(parents=True)
 with zipfile.ZipFile(ART) as z:
  prefix='photon_26914_v2_outputs/'
  def get(n):
   p=prefix+n
   if p not in z.namelist():fail('missing actual previous Actions receipt '+p)
   return z.read(p)
  b=get('26914_v2_candidate_app_source.tar.gz')
  if hashlib.sha256(b).hexdigest()!=TAR_SHA:fail('26914 V2 compiled TAR hash mismatch')
  if get('26914_V2_PREBUILD_SEALED_APP.sha256')!=(R/'26915_BASE_26914_V2_FULL_APP.sha256').read_bytes():fail('compiled prior manifest differs')
  if BUILDER_SHA not in get('26914_V2_ACTUAL_EXECUTED_BUILDER.sha256').decode():fail('prior successful builder receipt SHA mismatch')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build_26914_v2_incremental.py')).hexdigest()!=BUILDER_SHA:fail('prior builder bytes mismatch')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build-26914-v2-change-aware.yml')).hexdigest()!=WORKFLOW_SHA:fail('prior workflow bytes mismatch')
  if PRIOR_APK_SHA not in get('26914_V2_APK.sha256').decode():fail('prior APK receipt mismatch')
  for marker in ['REAL PINNED GLSL COMPILE: PASS','REAL SPIR-V VALIDATION: PASS','REAL KOTLIN COMPILE: PASS','REAL JAVA COMPILE: PASS','NATIVE/NDK COMPILE: PASS','REAL ANDROID Gradle :app:assembleDebug: PASS','RUNTIME SOURCE INVARIANCE: PASS']:
   if marker not in get('26914_V2_COMPILER_STATUS.txt').decode():fail('26914 V2 compiler receipt incomplete '+marker)
  temp=WORK/'26914_v2_candidate.tar.gz';temp.write_bytes(b)
 safe_tar(temp,BASE)
 exact(BASE,R/'26915_BASE_26914_V2_FULL_APP.sha256','actual 26914 V2 compiled source')
 shutil.copytree(BASE,CAND)
 changes=(R/'26915_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
 added=set((R/'26915_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
 deleted=set((R/'26915_DELETED_RUNTIME_PATHS.txt').read_text().splitlines())
 if len(changes)!=7 or len(added)!=1 or deleted:fail('wrong 26915 frozen changed/added/deleted scope')
 for p in changes:
  target=CAND/p
  f=R/'handoff_payload_26915'/p
  if not f.is_file() or (p not in added and not target.is_file()) or (p in added and target.exists()):fail('missing/incorrect approved overlay '+p)
  target.parent.mkdir(parents=True,exist_ok=True)
  shutil.copy2(f,target)
 before=parse(R/'26915_BASE_26914_V2_FULL_APP.sha256')
 after=exact(CAND,R/'26915_PRECOMPILE_EXPECTED_FULL_APP.sha256','26915 candidate-first exact transformation')
 if set(after)-set(before)!=added or set(before)-set(after)!=set() or {p for p in before if p in after and before[p]!=after[p]}!=(set(changes)-added):fail('unexpected source changed')
 for p in before:
  if p.startswith(('app/src/main/assets/','app/src/main/jniLibs/','app/src/main/cpp/iris26864/vendor/')) and (p not in after or before[p]!=after[p]):fail('vendor/native asset mutation '+p)
 if 'VERSION_BUILD=26915' not in (CAND/'app/version.properties').read_text():fail('wrong version')
 if not (R/'gradlew').is_file() or not (R/'app').is_dir():fail('checkout Android Gradle project unavailable')
 live=R/'app'
 if (live/'src').exists():shutil.rmtree(live/'src')
 shutil.copytree(CAND/'app/src',live/'src')
 shutil.copy2(CAND/'app/version.properties',live/'version.properties')
 shutil.copy2(CAND/'app/build.gradle',live/'build.gradle')
 exact(R,R/'26915_PRECOMPILE_EXPECTED_FULL_APP.sha256','26915 authority-seeded live source')
 OUT.mkdir(exist_ok=True)
 (OUT/'26915_SOURCE_SCOPE.txt').write_text('BASE=26914-V2-success run='+str(RUN)+' commit='+COMMIT+' artifact='+str(ART_ID)+'\nsource=2036 runtime_changed=7 protected=2029 added=1 deleted=0\nchanged='+'\n'.join(changes)+'\n')
 print('PASS 26915 exact authority-seeded runtime; C++ guide, Java pair, Kotlin consumer and B SR normal budget only')

def verify_compiled():
 seal();baseline=parse(R/'26915_PRECOMPILE_EXPECTED_FULL_APP.sha256')
 exact(R,R/'26915_PRECOMPILE_EXPECTED_FULL_APP.sha256','26915 post shader source immutability')
 for path in (R/'photon_26907_outputs/26907_HUE_SHADER_REAL_COMPILER.txt',R/'photon_26907_outputs/26907_HUE_SHADER_SPIRV_VALIDATED.txt'):
  if not path.is_file() or not path.stat().st_size or 'PASS' not in path.read_text():fail('missing real 26907 compiler receipt '+str(path))
 for path in (R/'photon_26908_outputs/26908_RENDER_SHADER_REAL_COMPILER.txt',R/'photon_26908_outputs/26908_RENDER_SHADER_SPIRV_VALIDATED.txt'):
  if not path.is_file() or 'PASS' not in path.read_text():fail('missing genuine 26908 real render shader compiler '+str(path))
 for path in ['26904_GLSL_REAL_COMPILER.txt','26904_SPIRV_VALIDATED.txt','26904_SPEKTRA_GLSLANG_CMAKE_HANDOFF.txt']:
  if not (R/'photon_26904_incremental_outputs'/path).is_file():fail('26904 inherited actual shader/NDK handoff missing '+path)
 for path in ('26906_TONE_SHADER_REAL_COMPILER.txt','26906_TONE_SHADER_SPIRV_VALIDATED.txt'):
  if not (R/'photon_26906_outputs'/path).is_file():fail('26906 inherited actual shader receipt missing '+path)
 if baseline[GENERATED]!='5853f1a0da12bab4b8c9489b6b298f3710f90fb6e51660204ed43f49963809f1':fail('pinned AMaZE SPV drift')
 OUT.mkdir(exist_ok=True)
 (OUT/'26915_PREBUILD_SEALED_APP.sha256').write_text(''.join(f'{baseline[p]}  {p}\n' for p in sorted(baseline)))
 print('PASS sealed 26915 shader source, exact ESSL310/SPIR-V, previous historical shader/NDK receipt replay')

def finalize():
 expected=exact(R,OUT/'26915_PREBUILD_SEALED_APP.sha256','26915 full assemble postbuild frozen source')
 apks=list((R/'app/build/outputs/apk').rglob('*.apk'))
 if len(apks)!=1:fail('exactly one APK required '+repr(apks))
 shutil.copy2(apks[0],R/APKNAME)
 if (R/APKNAME).stat().st_size<1_000_000:fail('APK invalid/small')
 gradle=OUT/'26915_gradle_assemble.log'
 if not gradle.is_file():fail('missing real Gradle build log')
 log=gradle.read_text(errors='replace')
 tasks=[':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL']
 if any(t not in log for t in tasks):fail('missing actual Kotlin/Java/NDK/assemble task '+str([t for t in tasks if t not in log]))
 (OUT/'26915_REAL_GRADLE_TASKS.txt').write_text(''.join('PASS '+t+'\n' for t in tasks))
 (OUT/'26915_COMPILER_STATUS.txt').write_text('REAL PINNED GLSL COMPILE: PASS (unchanged 26908 render/26907 hue ESSL310)\nREAL SPIR-V VALIDATION: PASS\nREAL KOTLIN COMPILE: PASS\nREAL JAVA COMPILE: PASS\nNATIVE/NDK COMPILE: PASS (arm64-v8a and armeabi-v7a, NEW guide JNI/header)\nREAL ANDROID Gradle :app:assembleDebug: PASS\nRUNTIME SOURCE INVARIANCE: PASS\nAPK '+APKNAME+' SHA256 '+sha(R/APKNAME)+'\n')
 (OUT/'26915_APK.sha256').write_text(sha(R/APKNAME)+'  '+APKNAME+'\n')
 (OUT/'26915_ACTUAL_EXECUTED_BUILDER.sha256').write_text(sha(R/'build_26915_incremental.py')+'  build_26915_incremental.py\n')
 native_receipt=R/'photon_26906_outputs/26906_NATIVE_CACHE_PATCH_REPLAY.json'
 if not native_receipt.is_file():fail('native cache patch replay gate missing')
 native=json.loads(native_receipt.read_text())
 if native.get('script_sha256')!=sha(R/'verify_26906_native_cache.py') or native.get('mode') not in ('cold','cached-replay'):fail('native cache replay receipt mismatch')
 if native['mode']=='cached-replay' and len(native.get('sources',[]))!=2:fail('invalid native ABI replay')
 shutil.copy2(native_receipt,OUT/'26915_NATIVE_CACHE_PATCH_REPLAY.json')
 (OUT/'26915_ACTIONS_IDENTITY.txt').write_text('git_sha='+os.getenv('GITHUB_SHA','local')+'\ngithub_run_id='+os.getenv('GITHUB_RUN_ID','local')+'\ngithub_job='+os.getenv('GITHUB_JOB','local')+'\n')
 workflow=R/'.github/workflows/build-26915-change-aware.yml'
 shutil.copy2(R/'build_26915_incremental.py',OUT/'ACTUAL_EXECUTED_build_26915_incremental.py')
 shutil.copy2(workflow,OUT/'ACTUAL_EXECUTED_build-26915-change-aware.yml')
 (OUT/'26915_ACTUAL_EXECUTED_WORKFLOW.sha256').write_text(sha(workflow)+'  .github/workflows/build-26915-change-aware.yml\n')
 base=parse(R/'26915_BASE_26914_V2_FULL_APP.sha256');modified=set((R/'26915_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
 (OUT/'26915_PROTECTED_SOURCE.sha256').write_text(''.join(f'{base[p]}  {p}\n' for p in sorted(base) if p not in modified))
 (OUT/'26915_BASE_26914_V2_FULL_APP.sha256').write_bytes((R/'26915_BASE_26914_V2_FULL_APP.sha256').read_bytes())
 (OUT/'26915_CHANGED_RUNTIME_ALLOWLIST.txt').write_bytes((R/'26915_CHANGED_RUNTIME_ALLOWLIST.txt').read_bytes())
 (OUT/'26915_VERSION.txt').write_text('VERSION_NAME=0.9726915\nVERSION_BUILD=26915\n')
 tar=OUT/'26915_candidate_app_source.tar.gz'
 with tarfile.open(tar,'w:gz',compresslevel=1) as z:
  for p in sorted(expected):
   f=R/p;info=z.gettarinfo(str(f),arcname=p);info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
   with f.open('rb') as inp:z.addfile(info,inp)
 (OUT/'26915_candidate_app_source.tar.gz.sha256').write_text(sha(tar)+'  26915_candidate_app_source.tar.gz\n')
 print('PASS one actual 26915 APK, compiled source TAR, 2029 protected source hashes and executed runner/workflow',sha(R/APKNAME))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['seal','fetch','prepare','verify-compiled','finalize']);args=p.parse_args()
 try:globals()[args.command.replace('-','_')]()
 except Exception as e:print('ERROR',str(e),file=sys.stderr);sys.exit(1)
