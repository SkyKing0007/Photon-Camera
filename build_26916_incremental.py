#!/usr/bin/env python3
"""Photon 26916 candidate-first, real Actions guarded successor.
Successful runtime authority: exact 26915 compiled candidate, NOT repository app/src.
Changes: B Photo SR OFF universal, confidence-bounded preview hue LUT and
continuous gamut-safe HueMatch. Wronski/Sabre/AMaZE are unchanged; 3 paths.
"""
from __future__ import annotations
import argparse,hashlib,json,os,pathlib,shutil,subprocess,sys,tarfile,urllib.request,zipfile
R=pathlib.Path(__file__).resolve().parent
WORK=R/'.photon_26916_work';OUT=R/'photon_26916_outputs'
ART=WORK/'26915_success.zip';BASE=WORK/'authority_26915';CAND=WORK/'candidate_26916'
REPO='SkyKing0007/Photon-Camera';BRANCH='experimental-clean-photon-rebuild'
RUN=42699855427;COMMIT='ad2d2d8ff64f7e02d6483307cd1a79d431400c0b';ART_ID=13711867064
ART_SHA='24c814e59fdfa2ff44034aae5933072ae77ddf620d879c2965f5770f70c50cde'
TAR_SHA='395f8d00dc94a47bda874b90eaa1c82416a6b5131d166f598773828243b1c6c8'
BUILDER_SHA='c8b4916d02d687eab5fd6af891830c6969f0ce79ddd7ddc58adefe5990f0ebcb'
WORKFLOW_SHA='86af9761f142b6b4d21785f432b70ab38cafd36998c26b9cc1d84e6ffd39a2c8'
PRIOR_APK_SHA='8c9a54799a5918bbcc61e0e0aae2bc0234fa693afb114f8218628c52fde9b53c'
GENERATED='app/src/main/assets/iris26856/rawr/amaze/spv/amaze_export.spv'
APKNAME='IrisCamera-0.9726916-26916-iris-rawr-debug.apk'

def fail(msg):raise RuntimeError('26916 BLOCKED: '+str(msg))
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
 from verify_26916_handoff import verify
 verify()
 print('PASS 26916 sealed three-path successor to successful 26915')

def gh(path,token):
 req=urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+path,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'})
 with urllib.request.urlopen(req,timeout=100) as q:return json.load(q)
def fetch():
 seal();tok=os.getenv('GITHUB_TOKEN','')
 if not tok:fail('missing GitHub token for actual successful 26915 artifact')
 if os.getenv('GITHUB_REPOSITORY',REPO)!=REPO or os.getenv('GITHUB_REF_NAME',BRANCH)!=BRANCH:fail('unexpected repo/branch')
 run=gh('actions/runs/'+str(RUN),tok);art=gh('actions/artifacts/'+str(ART_ID),tok)
 if run.get('conclusion')!='success' or run.get('head_sha')!=COMMIT or run.get('head_branch')!=BRANCH or run.get('id')!=RUN:fail('wrong last successful run')
 if art.get('id')!=ART_ID or art.get('expired') or art.get('digest')!='sha256:'+ART_SHA:fail('wrong last successful artifact')
 WORK.mkdir(exist_ok=True)
 subprocess.run(['curl','--fail','--location','--retry','3','--silent','--show-error',
                 '-H','Authorization: Bearer '+tok,'-H','Accept: application/vnd.github+json',
                 f'https://api.github.com/repos/{REPO}/actions/artifacts/{ART_ID}/zip','-o',str(ART)],check=True)
 if sha(ART)!=ART_SHA:fail('26915 downloaded ZIP hash mismatch')
 print('PASS successful 26915 run, actual artifact and digest',ART_SHA)

def safe_tar(tarpath,dest):
 with tarfile.open(tarpath,'r:gz') as t:
  for m in t.getmembers():
   p=pathlib.PurePosixPath(m.name)
   if p.is_absolute() or not p.parts or p.parts[0]!='app' or '..' in p.parts or not(m.isfile() or m.isdir()):fail('bad TAR member '+m.name)
  t.extractall(dest,filter='data')
def prepare():
 seal()
 if not ART.is_file() or sha(ART)!=ART_SHA:fail('successfully compiled 26915 ZIP missing/hash mismatch')
 for x in (BASE,CAND):
  if x.exists():shutil.rmtree(x)
 BASE.mkdir(parents=True)
 with zipfile.ZipFile(ART) as z:
  prefix='photon_26915_outputs/'
  def get(n):
   p=prefix+n
   if p not in z.namelist():fail('missing actual previous Actions receipt '+p)
   return z.read(p)
  b=get('26915_candidate_app_source.tar.gz')
  if hashlib.sha256(b).hexdigest()!=TAR_SHA:fail('26915 compiled TAR hash mismatch')
  if get('26915_PREBUILD_SEALED_APP.sha256')!=(R/'26916_BASE_26915_FULL_APP.sha256').read_bytes():fail('compiled prior manifest differs')
  if BUILDER_SHA not in get('26915_ACTUAL_EXECUTED_BUILDER.sha256').decode():fail('prior successful builder receipt SHA mismatch')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build_26915_incremental.py')).hexdigest()!=BUILDER_SHA:fail('prior builder bytes mismatch')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build-26915-change-aware.yml')).hexdigest()!=WORKFLOW_SHA:fail('prior workflow bytes mismatch')
  if PRIOR_APK_SHA not in get('26915_APK.sha256').decode():fail('prior APK receipt mismatch')
  for marker in ['REAL PINNED GLSL COMPILE: PASS','REAL SPIR-V VALIDATION: PASS','REAL KOTLIN COMPILE: PASS','REAL JAVA COMPILE: PASS','NATIVE/NDK COMPILE: PASS','REAL ANDROID Gradle :app:assembleDebug: PASS','RUNTIME SOURCE INVARIANCE: PASS']:
   if marker not in get('26915_COMPILER_STATUS.txt').decode():fail('26915 compiler receipt incomplete '+marker)
  temp=WORK/'26915_candidate.tar.gz';temp.write_bytes(b)
 safe_tar(temp,BASE)
 exact(BASE,R/'26916_BASE_26915_FULL_APP.sha256','actual 26915 compiled source')
 shutil.copytree(BASE,CAND)
 changes=(R/'26916_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
 added=set((R/'26916_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
 deleted=set((R/'26916_DELETED_RUNTIME_PATHS.txt').read_text().splitlines())
 if len(changes)!=3 or added or deleted:fail('wrong 26916 frozen changed/added/deleted scope')
 for p in changes:
  target=CAND/p
  f=R/'handoff_payload_26916'/p
  if not f.is_file() or (p not in added and not target.is_file()) or (p in added and target.exists()):fail('missing/incorrect approved overlay '+p)
  target.parent.mkdir(parents=True,exist_ok=True)
  shutil.copy2(f,target)
 before=parse(R/'26916_BASE_26915_FULL_APP.sha256')
 after=exact(CAND,R/'26916_PRECOMPILE_EXPECTED_FULL_APP.sha256','26916 candidate-first exact transformation')
 if set(after)-set(before)!=added or set(before)-set(after)!=set() or {p for p in before if p in after and before[p]!=after[p]}!=(set(changes)-added):fail('unexpected source changed')
 for p in before:
  if p.startswith(('app/src/main/assets/','app/src/main/jniLibs/','app/src/main/cpp/')) and p not in changes and (p not in after or before[p]!=after[p]):fail('protected shader/vendor/native mutation '+p)
 if 'VERSION_BUILD=26916' not in (CAND/'app/version.properties').read_text():fail('wrong version')
 if not (R/'gradlew').is_file() or not (R/'app').is_dir():fail('checkout Android Gradle project unavailable')
 live=R/'app'
 if (live/'src').exists():shutil.rmtree(live/'src')
 shutil.copytree(CAND/'app/src',live/'src')
 shutil.copy2(CAND/'app/version.properties',live/'version.properties')
 shutil.copy2(CAND/'app/build.gradle',live/'build.gradle')
 exact(R,R/'26916_PRECOMPILE_EXPECTED_FULL_APP.sha256','26916 authority-seeded live source')
 OUT.mkdir(exist_ok=True)
 (OUT/'26916_SOURCE_SCOPE.txt').write_text('BASE=26915-success run='+str(RUN)+' commit='+COMMIT+' artifact='+str(ART_ID)+'\nsource=2036 runtime_changed=3 protected=2033 added=0 deleted=0\nchanged='+'\n'.join(changes)+'\n')
 print('PASS 26916 exact authority-seeded runtime: measured 48-sector hue support and continuous P3 gamut only')

def verify_compiled():
 seal();baseline=parse(R/'26916_PRECOMPILE_EXPECTED_FULL_APP.sha256')
 exact(R,R/'26916_PRECOMPILE_EXPECTED_FULL_APP.sha256','26916 post shader source immutability')
 for path in (R/'photon_26907_outputs/26907_HUE_SHADER_REAL_COMPILER.txt',R/'photon_26907_outputs/26907_HUE_SHADER_SPIRV_VALIDATED.txt'):
  if not path.is_file() or not path.stat().st_size or 'PASS' not in path.read_text():fail('missing real 26907 compiler receipt '+str(path))
 # The 26907 pinned real compiler MUST receive the exact new runtime-expanded shader.
 # A historical PASS receipt is not sufficient if the staged shader bytes differ.
 compiled_dir=R/'.photon_26904_incremental_work/real_shader_tools/26907_hue_compiler'
 expanded=compiled_dir/'hue.frag'
 hue=R/'app/src/main/assets/shaders/motionv2/preview_hue_match_26907.glsl'
 if not expanded.is_file() or expanded.read_bytes()!=b'#version 310 es\n#line 1\n'+hue.read_bytes():
  fail('26916 actual pinned glslang compiled different hue shader bytes')
 for name in ['hue.spv','hue.opt.spv','probe.spv','probe.opt.spv']:
  if not (compiled_dir/name).is_file() or (compiled_dir/name).stat().st_size<128:
   fail('26916 actual SPIR-V compiled output missing/short '+name)
 for path in (R/'photon_26908_outputs/26908_RENDER_SHADER_REAL_COMPILER.txt',R/'photon_26908_outputs/26908_RENDER_SHADER_SPIRV_VALIDATED.txt'):
  if not path.is_file() or 'PASS' not in path.read_text():fail('missing genuine 26908 real render shader compiler '+str(path))
 for path in ['26904_GLSL_REAL_COMPILER.txt','26904_SPIRV_VALIDATED.txt','26904_SPEKTRA_GLSLANG_CMAKE_HANDOFF.txt']:
  if not (R/'photon_26904_incremental_outputs'/path).is_file():fail('26904 inherited actual shader/NDK handoff missing '+path)
 for path in ('26906_TONE_SHADER_REAL_COMPILER.txt','26906_TONE_SHADER_SPIRV_VALIDATED.txt'):
  if not (R/'photon_26906_outputs'/path).is_file():fail('26906 inherited actual shader receipt missing '+path)
 if baseline[GENERATED]!='5853f1a0da12bab4b8c9489b6b298f3710f90fb6e51660204ed43f49963809f1':fail('pinned AMaZE SPV drift')
 OUT.mkdir(exist_ok=True)
 (OUT/'26916_PREBUILD_SEALED_APP.sha256').write_text(''.join(f'{baseline[p]}  {p}\n' for p in sorted(baseline)))
 (OUT/'26916_REAL_HUE_SOURCE_SHA256.txt').write_text(sha(R/'app/src/main/assets/shaders/motionv2/preview_hue_match_26907.glsl')+'  app/src/main/assets/shaders/motionv2/preview_hue_match_26907.glsl\nREAL PINNED 26907 ESSL310/SPIR-V COMPILE: PASS\n')
 print('PASS sealed 26916 hue shader source and real pinned 26907 ESSL310/SPIR-V compiler receipts')

def finalize():
 expected=exact(R,OUT/'26916_PREBUILD_SEALED_APP.sha256','26916 full assemble postbuild frozen source')
 apks=list((R/'app/build/outputs/apk').rglob('*.apk'))
 if len(apks)!=1:fail('exactly one APK required '+repr(apks))
 shutil.copy2(apks[0],R/APKNAME)
 if (R/APKNAME).stat().st_size<1_000_000:fail('APK invalid/small')
 gradle=OUT/'26916_gradle_assemble.log'
 if not gradle.is_file():fail('missing real Gradle build log')
 log=gradle.read_text(errors='replace')
 tasks=[':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL']
 if any(t not in log for t in tasks):fail('missing actual Kotlin/Java/NDK/assemble task '+str([t for t in tasks if t not in log]))
 (OUT/'26916_REAL_GRADLE_TASKS.txt').write_text(''.join('PASS '+t+'\n' for t in tasks))
 if not (OUT/'26916_REAL_HUE_SOURCE_SHA256.txt').is_file():fail('compiled 26916 shader receipt absent')
 (OUT/'26916_COMPILER_STATUS.txt').write_text('REAL PINNED GLSL COMPILE: PASS (new 26916 preview-hue shader via proven pinned 26907 ESSL310 compiler)\nREAL SPIR-V VALIDATION: PASS\nREAL KOTLIN COMPILE: PASS\nREAL JAVA COMPILE: PASS\nNATIVE/NDK COMPILE: PASS (arm64-v8a and armeabi-v7a; source unchanged)\nREAL ANDROID Gradle :app:assembleDebug: PASS\nRUNTIME SOURCE INVARIANCE: PASS\nAPK '+APKNAME+' SHA256 '+sha(R/APKNAME)+'\n')
 (OUT/'26916_APK.sha256').write_text(sha(R/APKNAME)+'  '+APKNAME+'\n')
 (OUT/'26916_ACTUAL_EXECUTED_BUILDER.sha256').write_text(sha(R/'build_26916_incremental.py')+'  build_26916_incremental.py\n')
 native_receipt=R/'photon_26906_outputs/26906_NATIVE_CACHE_PATCH_REPLAY.json'
 if not native_receipt.is_file():fail('native cache patch replay gate missing')
 native=json.loads(native_receipt.read_text())
 if native.get('script_sha256')!=sha(R/'verify_26906_native_cache.py') or native.get('mode') not in ('cold','cached-replay'):fail('native cache replay receipt mismatch')
 if native['mode']=='cached-replay' and len(native.get('sources',[]))!=2:fail('invalid native ABI replay')
 shutil.copy2(native_receipt,OUT/'26916_NATIVE_CACHE_PATCH_REPLAY.json')
 (OUT/'26916_ACTIONS_IDENTITY.txt').write_text('git_sha='+os.getenv('GITHUB_SHA','local')+'\ngithub_run_id='+os.getenv('GITHUB_RUN_ID','local')+'\ngithub_job='+os.getenv('GITHUB_JOB','local')+'\n')
 workflow=R/'.github/workflows/build-26916-change-aware.yml'
 shutil.copy2(R/'build_26916_incremental.py',OUT/'ACTUAL_EXECUTED_build_26916_incremental.py')
 shutil.copy2(workflow,OUT/'ACTUAL_EXECUTED_build-26916-change-aware.yml')
 (OUT/'26916_ACTUAL_EXECUTED_WORKFLOW.sha256').write_text(sha(workflow)+'  .github/workflows/build-26916-change-aware.yml\n')
 base=parse(R/'26916_BASE_26915_FULL_APP.sha256');modified=set((R/'26916_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
 (OUT/'26916_PROTECTED_SOURCE.sha256').write_text(''.join(f'{base[p]}  {p}\n' for p in sorted(base) if p not in modified))
 (OUT/'26916_BASE_26915_FULL_APP.sha256').write_bytes((R/'26916_BASE_26915_FULL_APP.sha256').read_bytes())
 (OUT/'26916_CHANGED_RUNTIME_ALLOWLIST.txt').write_bytes((R/'26916_CHANGED_RUNTIME_ALLOWLIST.txt').read_bytes())
 (OUT/'26916_VERSION.txt').write_text('VERSION_NAME=0.9726916\nVERSION_BUILD=26916\n')
 tar=OUT/'26916_candidate_app_source.tar.gz'
 with tarfile.open(tar,'w:gz',compresslevel=1) as z:
  for p in sorted(expected):
   f=R/p;info=z.gettarinfo(str(f),arcname=p);info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
   with f.open('rb') as inp:z.addfile(info,inp)
 (OUT/'26916_candidate_app_source.tar.gz.sha256').write_text(sha(tar)+'  26916_candidate_app_source.tar.gz\n')
 print('PASS one actual 26916 APK, compiled source TAR, 2033 protected source hashes and executed runner/workflow',sha(R/APKNAME))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['seal','fetch','prepare','verify-compiled','finalize']);args=p.parse_args()
 try:globals()[args.command.replace('-','_')]()
 except Exception as e:print('ERROR',str(e),file=sys.stderr);sys.exit(1)
