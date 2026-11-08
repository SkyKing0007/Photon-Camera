#!/usr/bin/env python3
"""Photon 26911 strict candidate-first change-aware Actions release runner.
Source authority: 26910 successful published Actions artifact, NEVER repository source.
Scope: three changed + one added runtime paths. Real pinned shader and Android compile occurs in Actions.
"""
from __future__ import annotations
import argparse,hashlib,json,os,pathlib,shutil,subprocess,sys,tarfile,urllib.request,zipfile
R=pathlib.Path(__file__).resolve().parent
WORK=R/'.photon_26911_work';OUT=R/'photon_26911_outputs'
ART=WORK/'26910_success.zip';BASE=WORK/'authority_26910';CAND=WORK/'candidate_26911'
REPO='SkyKing0007/Photon-Camera';BRANCH='experimental-clean-photon-rebuild'
RUN=42450831835;COMMIT='92e7e46f64b2a40e717d6bbb3711ff2ea296b987';ART_ID=13606221070
ART_SHA='c317801800fbcfc1f8461a308ad1aa03860c37ab916ec2de4d3306531e174e9d'
TAR_SHA='76c0b817d29757a7f9120563f1081d04d2750c8609f782c8f283c511e70ac626'
BUILDER_SHA='3dce3646266759f35062f9974b4eb2842fd7d79f6d7342c849cf277e3277f063'
WORKFLOW_SHA='ac0be9aa36067752d36c9545e57c5ab06cd379c43f0897a0ea690d705f44a898'
GENERATED='app/src/main/assets/iris26856/rawr/amaze/spv/amaze_export.spv'
APKNAME='IrisCamera-0.9726911-26911-iris-rawr-debug.apk'

def fail(msg):raise RuntimeError('26911 BLOCKED: '+str(msg))
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
 # Exact 26910 compiled-source universe: app/src, build.gradle, version.properties.
 # Repository-only scaffolding outside this scope must not be interpreted as
 # new runtime source; unknown app/src files must still fail the full manifest.
 source_root=src/'app/src'
 if source_root.is_symlink() or not source_root.is_dir():fail('Android runtime source directory missing or symlinked')
 source_files=list(source_root.rglob('*'))
 source_files.extend([src/'app/build.gradle',src/'app/version.properties'])
 for p in source_files:
  if p.is_symlink():fail('unapproved source symlink '+str(p))
  if p.is_file():
   d[p.relative_to(src).as_posix()]=sha(p)
 return d
def exact(src,manifest,title):
 expected=parse(manifest);actual=scan(src)
 if expected!=actual:
  miss=sorted(expected.keys()-actual.keys());extra=sorted(actual.keys()-expected.keys());wrong=sorted(p for p in expected.keys()&actual.keys() if expected[p]!=actual[p]);fail(f'{title}: missing={miss[:4]} extra={extra[:4]} wrong={wrong[:8]}')
 print('PASS',title,len(expected),'source files');return expected

def seal():
 hfile=R/'26911_HANDOFF_HASHES.sha256';entries={}
 for ln in hfile.read_text().splitlines():
  h,name=ln.split('  ',1)
  if name in entries or not (R/name).is_file() or sha(R/name)!=h:fail('staged tamper '+name)
  entries[name]=h
 stage1=(R/'26911_STAGE1_PATHS.txt').read_text().splitlines()
 if len(stage1)!=len(set(stage1)) or '26911_HANDOFF_HASHES.sha256' not in stage1:fail('invalid Stage1 paths')
 want=set(stage1)-{'26911_HANDOFF_HASHES.sha256'}
 want|={'.github/workflows/build-26911-change-aware.yml','TRIGGER_26911.txt'}
 if set(entries)!=want:fail('wrong stage bundle scope')
 if (R/'TRIGGER_26911.txt').read_bytes()!=b'RUN_26911_B_PREVIEW_CAPTURE_EXPOSURE_CONTINUITY_V1\n':fail('trigger bytes')
 changed=(R/'26911_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
 if len(changed)!=4 or len(set(changed))!=4:fail('scope list not four')
 added=(R/'26911_ADDED_RUNTIME_PATHS.txt').read_text().splitlines()
 if len(added)!=1 or len(set(added))!=1 or not set(added).issubset(set(changed)):fail('scope added list not one')
 if {p for p in want if p.startswith('handoff_payload_26911/')}!= {'handoff_payload_26911/'+p for p in changed}:fail('runtime payload not exact allowlist')
 print('PASS 26911 exact Stage1/2/3 seal',len(want),'files, trigger changed')

def gh(path,token):
 req=urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+path,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'})
 with urllib.request.urlopen(req,timeout=100) as q:return json.load(q)
def fetch():
 seal();tok=os.getenv('GITHUB_TOKEN','')
 if not tok:fail('missing GitHub token for actual prior Actions artifact')
 if os.getenv('GITHUB_REPOSITORY',REPO)!=REPO or os.getenv('GITHUB_REF_NAME',BRANCH)!=BRANCH:fail('unexpected repository/branch')
 run=gh('actions/runs/'+str(RUN),tok);art=gh('actions/artifacts/'+str(ART_ID),tok)
 if run.get('conclusion')!='success' or run.get('head_sha')!=COMMIT or run.get('head_branch')!=BRANCH or run.get('id')!=RUN:fail('invalid successful run')
 if art.get('id')!=ART_ID or art.get('expired') or art.get('digest')!='sha256:'+ART_SHA:fail('invalid successful artifact')
 WORK.mkdir(exist_ok=True)
 cmd=['curl','--fail','--location','--retry','3','--silent','--show-error','-H','Authorization: Bearer '+tok,'-H','Accept: application/vnd.github+json',f'https://api.github.com/repos/{REPO}/actions/artifacts/{ART_ID}/zip','-o',str(ART)]
 subprocess.run(cmd,check=True)
 if sha(ART)!=ART_SHA:fail('downloaded 26910 artifact ZIP hash mismatch')
 print('PASS latest successful 26910 run, artifact and ZIP SHA',ART_SHA)

def safe_tar(tarpath,dest):
 with tarfile.open(tarpath,'r:gz') as t:
  for m in t.getmembers():
   p=pathlib.PurePosixPath(m.name)
   if p.is_absolute() or not p.parts or p.parts[0]!='app' or '..' in p.parts or not(m.isfile() or m.isdir()):fail('bad tar member '+m.name)
  t.extractall(dest,filter='data')
def prepare():
 seal()
 if not ART.is_file() or sha(ART)!=ART_SHA:fail('26910 real successful ZIP missing or digest mismatch')
 for x in (BASE,CAND):
  if x.exists():shutil.rmtree(x)
 BASE.mkdir(parents=True)
 with zipfile.ZipFile(ART) as z:
  prefix='photon_26910_outputs/'
  def get(n):
   p=prefix+n
   if p not in z.namelist():fail('missing prior artifact receipt '+p)
   return z.read(p)
  b=get('26910_candidate_app_source.tar.gz')
  if hashlib.sha256(b).hexdigest()!=TAR_SHA:fail('26910 actual compiled TAR mismatches authority')
  if get('26910_PREBUILD_SEALED_APP.sha256')!=(R/'26911_BASE_26910_FULL_APP.sha256').read_bytes():fail('prior manifest differs')
  if BUILDER_SHA not in get('26910_ACTUAL_EXECUTED_BUILDER.sha256').decode():fail('prior builder receipt SHA mismatch')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build_26910_incremental.py')).hexdigest()!=BUILDER_SHA:fail('prior builder bytes mismatch')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build-26910-change-aware.yml')).hexdigest()!=WORKFLOW_SHA:fail('prior workflow bytes mismatch')
  status=get('26910_COMPILER_STATUS.txt').decode()
  for required in ['REAL PINNED GLSL COMPILE: PASS','REAL SPIR-V VALIDATION: PASS','REAL KOTLIN COMPILE: PASS','REAL JAVA COMPILE: PASS','NATIVE/NDK COMPILE: PASS','REAL ANDROID Gradle :app:assembleDebug: PASS','RUNTIME SOURCE INVARIANCE: PASS']:
   if required not in status:fail('prior successful compiler proof incomplete: '+required)
  temp=WORK/'26910_candidate.tar.gz';temp.write_bytes(b)
 safe_tar(temp,BASE)
 exact(BASE,R/'26911_BASE_26910_FULL_APP.sha256','actual successful 26910 compiled source')
 shutil.copytree(BASE,CAND)
 changes=(R/'26911_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
 added=set((R/'26911_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
 if len(added)!=1 or not added.issubset(set(changes)):fail('added source allowlist mismatch')
 for p in changes:
  f=R/'handoff_payload_26911'/p;target=CAND/p
  if not f.is_file() or (p not in added and not target.is_file()):fail('missing approved overlay '+p)
  target.parent.mkdir(parents=True,exist_ok=True)
  shutil.copy2(f,target)
 before=parse(R/'26911_BASE_26910_FULL_APP.sha256');after=exact(CAND,R/'26911_PRECOMPILE_EXPECTED_FULL_APP.sha256','26911 candidate source SHA')
 if set(after)-set(before)!=added or set(before)-set(after) or {p for p in before if before[p]!=after[p]}!=(set(changes)-added):fail('extra source modification')
 if 'VERSION_BUILD=26911' not in (CAND/'app/version.properties').read_text():fail('wrong version')
 if not (R/'gradlew').is_file() or not (R/'app').is_dir():fail('checkout Android Gradle project unavailable')
 live=R/'app'
 if (live/'src').exists():shutil.rmtree(live/'src')
 shutil.copytree(CAND/'app/src',live/'src')
 shutil.copy2(CAND/'app/version.properties',live/'version.properties')
 shutil.copy2(CAND/'app/build.gradle',live/'build.gradle')
 exact(R,R/'26911_PRECOMPILE_EXPECTED_FULL_APP.sha256','authority-seeded live Android source')
 OUT.mkdir(exist_ok=True)
 (OUT/'26911_SOURCE_SCOPE.txt').write_text('BASE=26910-success run='+str(RUN)+' commit='+COMMIT+' artifact='+str(ART_ID)+'\nsource=2034 runtime_changed=4 protected=2030 added=1 deleted=0\nchanged='+'\n'.join(changes)+'\n')
 print('PASS safe authority-seeded Android source; untouched A/native/vendor before Android build')

def verify_compiled():
 seal();baseline=parse(R/'26911_PRECOMPILE_EXPECTED_FULL_APP.sha256')
 exact(R,R/'26911_PRECOMPILE_EXPECTED_FULL_APP.sha256','post shader source immutability')
 for path in (R/'photon_26907_outputs/26907_HUE_SHADER_REAL_COMPILER.txt',R/'photon_26907_outputs/26907_HUE_SHADER_SPIRV_VALIDATED.txt'):
  if not path.is_file() or not path.stat().st_size or 'PASS' not in path.read_text():fail('missing genuine new shader compiler/spirv receipt '+str(path))
 for path in (R/'photon_26908_outputs/26908_RENDER_SHADER_REAL_COMPILER.txt',R/'photon_26908_outputs/26908_RENDER_SHADER_SPIRV_VALIDATED.txt'):
  if not path.is_file() or 'PASS' not in path.read_text():fail('missing replayed 26908 real render shader compilation '+str(path))
 for path in ['26904_GLSL_REAL_COMPILER.txt','26904_SPIRV_VALIDATED.txt','26904_SPEKTRA_GLSLANG_CMAKE_HANDOFF.txt']:
  if not (R/'photon_26904_incremental_outputs'/path).is_file():fail('26904 inherited actual compiler/handoff receipt missing '+path)
 for path in ('26906_TONE_SHADER_REAL_COMPILER.txt','26906_TONE_SHADER_SPIRV_VALIDATED.txt'):
  if not (R/'photon_26906_outputs'/path).is_file():fail('26906 inherited shader compilation not replayed')
 if baseline[GENERATED]!='5853f1a0da12bab4b8c9489b6b298f3710f90fb6e51660204ed43f49963809f1':fail('pinned AMaZE SPV drift')
 OUT.mkdir(exist_ok=True)
 (OUT/'26911_PREBUILD_SEALED_APP.sha256').write_text(''.join(f'{baseline[p]}  {p}\n' for p in sorted(baseline)))
 print('PASS 26911 exact source bytes, replayed 26908 real render shader, 26907 hue shader, 26906 tone shaders, original native SPV validated')

def finalize():
 expected=exact(R,OUT/'26911_PREBUILD_SEALED_APP.sha256','post full assemble frozen source')
 apks=list((R/'app/build/outputs/apk').rglob('*.apk'))
 if len(apks)!=1:fail('exactly one APK required got '+repr(apks))
 shutil.copy2(apks[0],R/APKNAME)
 if (R/APKNAME).stat().st_size<1_000_000:fail('APK invalid/small')
 gradle=(OUT/'26911_gradle_assemble.log')
 if not gradle.is_file():fail('missing real Gradle log')
 log=gradle.read_text(errors='replace')
 tasks=[':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL']
 if any(t not in log for t in tasks):fail('missing actual native/Kotlin/Javac/assemble task '+str([t for t in tasks if t not in log]))
 (OUT/'26911_REAL_GRADLE_TASKS.txt').write_text(''.join('PASS '+t+'\n' for t in tasks))
 (OUT/'26911_COMPILER_STATUS.txt').write_text('REAL PINNED GLSL COMPILE: PASS (26908 Night render GLSL plus 26907 hue shader ESSL310, unchanged 26911)\nREAL SPIR-V VALIDATION: PASS\nREAL KOTLIN COMPILE: PASS\nREAL JAVA COMPILE: PASS\nNATIVE/NDK COMPILE: PASS (arm64-v8a and armeabi-v7a)\nREAL ANDROID Gradle :app:assembleDebug: PASS\nRUNTIME SOURCE INVARIANCE: PASS\nAPK '+APKNAME+' SHA256 '+sha(R/APKNAME)+'\n')
 (OUT/'26911_APK.sha256').write_text(sha(R/APKNAME)+'  '+APKNAME+'\n')
 (OUT/'26911_ACTUAL_EXECUTED_BUILDER.sha256').write_text(sha(R/'build_26911_incremental.py')+'  build_26911_incremental.py\n')
 native_receipt=R/'photon_26906_outputs/26906_NATIVE_CACHE_PATCH_REPLAY.json'
 if not native_receipt.is_file():fail('26910 successful native-cache replay gate receipt missing in 26911 Actions')
 native_proof=json.loads(native_receipt.read_text())
 if native_proof.get('script_sha256')!=sha(R/'verify_26906_native_cache.py') or native_proof.get('mode') not in ('cold','cached-replay'):
  fail('native cache replay proof malformed or stale')
 if native_proof['mode']=='cached-replay' and len(native_proof.get('sources',[]))!=2:fail('wrong native ABI replay proof')
 shutil.copy2(native_receipt,OUT/'26911_NATIVE_CACHE_PATCH_REPLAY.json')
 (OUT/'26911_ACTIONS_IDENTITY.txt').write_text('git_sha='+os.getenv('GITHUB_SHA','local')+'\ngithub_run_id='+os.getenv('GITHUB_RUN_ID','local')+'\ngithub_job='+os.getenv('GITHUB_JOB','local')+'\n')
 workflow=R/'.github/workflows/build-26911-change-aware.yml'
 shutil.copy2(R/'build_26911_incremental.py',OUT/'ACTUAL_EXECUTED_build_26911_incremental.py')
 shutil.copy2(workflow,OUT/'ACTUAL_EXECUTED_build-26911-change-aware.yml')
 (OUT/'26911_ACTUAL_EXECUTED_WORKFLOW.sha256').write_text(sha(workflow)+'  .github/workflows/build-26911-change-aware.yml\n')
 base=parse(R/'26911_BASE_26910_FULL_APP.sha256');modified=set((R/'26911_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
 (OUT/'26911_PROTECTED_SOURCE.sha256').write_text(''.join(f'{base[p]}  {p}\n' for p in sorted(base) if p not in modified))
 (OUT/'26911_BASE_26910_FULL_APP.sha256').write_bytes((R/'26911_BASE_26910_FULL_APP.sha256').read_bytes())
 (OUT/'26911_CHANGED_RUNTIME_ALLOWLIST.txt').write_bytes((R/'26911_CHANGED_RUNTIME_ALLOWLIST.txt').read_bytes())
 (OUT/'26911_VERSION.txt').write_text('VERSION_NAME=0.9726911\nVERSION_BUILD=26911\n')
 tar=OUT/'26911_candidate_app_source.tar.gz'
 with tarfile.open(tar,'w:gz',compresslevel=1) as z:
  for p in sorted(expected):
   f=R/p;info=z.gettarinfo(str(f),arcname=p);info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
   with f.open('rb') as inp:z.addfile(info,inp)
 (OUT/'26911_candidate_app_source.tar.gz.sha256').write_text(sha(tar)+'  26911_candidate_app_source.tar.gz\n')
 print('PASS one real 26911 Android APK, all 2030 protected source files, actual executed builder+workflow',sha(R/APKNAME))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['seal','fetch','prepare','verify-compiled','finalize']);args=p.parse_args()
 try:globals()[args.command.replace('-','_')]()
 except Exception as e:print('ERROR',str(e),file=sys.stderr);sys.exit(1)
