#!/usr/bin/env python3
"""Photon 26906 strict candidate-first change-aware Actions release runner.
Source authority: 26905 successful published Actions artifact, NEVER repository source.
Scope: nine exact runtime paths. Real shader and Android compile occurs in Actions.
"""
from __future__ import annotations
import argparse,hashlib,json,os,pathlib,shutil,subprocess,sys,tarfile,urllib.request,zipfile
R=pathlib.Path(__file__).resolve().parent
WORK=R/'.photon_26906_work';OUT=R/'photon_26906_outputs'
ART=WORK/'26905_success.zip';BASE=WORK/'authority_26905';CAND=WORK/'candidate_26906'
REPO='SkyKing0007/Photon-Camera';BRANCH='experimental-clean-photon-rebuild'
RUN=42291116167;COMMIT='31e4b07ee73794b7ecc668d2120b067dcc10922b';ART_ID=13540785740
ART_SHA='25cf2435d68250b7e127e34ddb31e669a211f0baa07b2942e355e24faaa20ea0'
TAR_SHA='41a3b7c885c52582821917d143376b64acd962878292f7da166d2dd5c2dbba0d'
BUILDER_SHA='4cf16fed62efc325840ce49d888605e9b7e73de297d17b99e742485005b3e70c'
WORKFLOW_SHA='fc57c6abf04dfb62b0cba69061009101175f97237aafdcb5e8c69a71e6e0c2da'
GENERATED='app/src/main/assets/iris26856/rawr/amaze/spv/amaze_export.spv'
APKNAME='IrisCamera-0.9726906-26906-iris-rawr-debug.apk'

def fail(msg):raise RuntimeError('26906 BLOCKED: '+str(msg))
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
 # Exact 26905 compiled-source universe: app/src, build.gradle, version.properties.
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
 hfile=R/'26906_HANDOFF_HASHES.sha256';entries={}
 for ln in hfile.read_text().splitlines():
  h,name=ln.split('  ',1)
  if name in entries or not (R/name).is_file() or sha(R/name)!=h:fail('staged tamper '+name)
  entries[name]=h
 stage1=(R/'26906_STAGE1_PATHS.txt').read_text().splitlines()
 if len(stage1)!=len(set(stage1)) or '26906_HANDOFF_HASHES.sha256' not in stage1:fail('invalid Stage1 paths')
 want=set(stage1)-{'26906_HANDOFF_HASHES.sha256'}
 want|={'.github/workflows/build-26906-change-aware.yml','TRIGGER_26906.txt'}
 if set(entries)!=want:fail('wrong stage bundle scope')
 if (R/'TRIGGER_26906.txt').read_bytes()!=b'RUN_26906_B_VISUAL_MIDTONE_TOE_NIGHT_EXPOSURE_V2_SOURCE_SCOPE_FIX\n':fail('trigger bytes')
 changed=(R/'26906_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
 if len(changed)!=9 or len(set(changed))!=9:fail('scope list not nine')
 if {p for p in want if p.startswith('handoff_payload_26906/')}!= {'handoff_payload_26906/'+p for p in changed}:fail('runtime payload not exact allowlist')
 print('PASS 26906 exact Stage1/2/3 seal',len(want),'files, trigger changed')

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
 if sha(ART)!=ART_SHA:fail('downloaded 26905 artifact ZIP hash mismatch')
 print('PASS latest successful 26905 run, artifact and ZIP SHA',ART_SHA)

def safe_tar(tarpath,dest):
 with tarfile.open(tarpath,'r:gz') as t:
  for m in t.getmembers():
   p=pathlib.PurePosixPath(m.name)
   if p.is_absolute() or not p.parts or p.parts[0]!='app' or '..' in p.parts or not(m.isfile() or m.isdir()):fail('bad tar member '+m.name)
  t.extractall(dest,filter='data')
def prepare():
 seal()
 if not ART.is_file() or sha(ART)!=ART_SHA:fail('26905 real successful ZIP missing or digest mismatch')
 for x in (BASE,CAND):
  if x.exists():shutil.rmtree(x)
 BASE.mkdir(parents=True)
 with zipfile.ZipFile(ART) as z:
  prefix='photon_26905_incremental_outputs/'
  def get(n):
   p=prefix+n
   if p not in z.namelist():fail('missing prior artifact receipt '+p)
   return z.read(p)
  b=get('26905_candidate_app_source.tar.gz')
  if hashlib.sha256(b).hexdigest()!=TAR_SHA:fail('26905 actual compiled TAR mismatches authority')
  if get('26905_PREBUILD_SEALED_APP.sha256')!=(R/'26906_BASE_26905_FULL_APP.sha256').read_bytes():fail('prior manifest differs')
  if BUILDER_SHA not in get('26905_ACTUAL_EXECUTED_BUILDER.sha256').decode():fail('prior builder receipt SHA mismatch')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build_26905_incremental.py')).hexdigest()!=BUILDER_SHA:fail('prior builder bytes mismatch')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build_26905-change-aware.yml')).hexdigest()!=WORKFLOW_SHA:fail('prior workflow bytes mismatch')
  status=get('26905_COMPILER_STATUS.txt').decode()
  for required in ['REAL PINNED GLSL COMPILE: PASS','REAL SPIR-V VALIDATION: PASS','REAL KOTLIN COMPILE: PASS','REAL JAVA COMPILE: PASS','NATIVE/NDK COMPILE: PASS','REAL ANDROID Gradle :app:assembleDebug: PASS','RUNTIME SOURCE INVARIANCE: PASS']:
   if required not in status:fail('prior successful compiler proof incomplete: '+required)
  temp=WORK/'26905_candidate.tar.gz';temp.write_bytes(b)
 safe_tar(temp,BASE)
 exact(BASE,R/'26906_BASE_26905_FULL_APP.sha256','actual successful 26905 compiled source')
 shutil.copytree(BASE,CAND)
 changes=(R/'26906_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
 for p in changes:
  f=R/'handoff_payload_26906'/p;target=CAND/p
  if not f.is_file() or not target.is_file():fail('missing approved overlay '+p)
  shutil.copy2(f,target)
 before=parse(R/'26906_BASE_26905_FULL_APP.sha256');after=exact(CAND,R/'26906_PRECOMPILE_EXPECTED_FULL_APP.sha256','26906 candidate source SHA')
 if before.keys()!=after.keys() or {p for p in before if before[p]!=after[p]}!=set(changes):fail('extra source modification')
 if 'VERSION_BUILD=26906' not in (CAND/'app/version.properties').read_text():fail('wrong version')
 if not (R/'gradlew').is_file() or not (R/'app').is_dir():fail('checkout Android Gradle project unavailable')
 live=R/'app'
 if (live/'src').exists():shutil.rmtree(live/'src')
 shutil.copytree(CAND/'app/src',live/'src')
 shutil.copy2(CAND/'app/version.properties',live/'version.properties')
 shutil.copy2(CAND/'app/build.gradle',live/'build.gradle')
 exact(R,R/'26906_PRECOMPILE_EXPECTED_FULL_APP.sha256','authority-seeded live Android source')
 OUT.mkdir(exist_ok=True)
 (OUT/'26906_SOURCE_SCOPE.txt').write_text('BASE=26905-success run='+str(RUN)+' commit='+COMMIT+' artifact='+str(ART_ID)+'\nsource=2027 runtime_changed=9 protected=2018 added=0 deleted=0\nchanged='+'\n'.join(changes)+'\n')
 print('PASS safe authority-seeded Android source; untouched A/native/vendor before Android build')

def verify_compiled():
 seal();baseline=parse(R/'26906_PRECOMPILE_EXPECTED_FULL_APP.sha256')
 exact(R,R/'26906_PRECOMPILE_EXPECTED_FULL_APP.sha256','post shader source immutability')
 for path in (OUT/'26906_TONE_SHADER_REAL_COMPILER.txt',OUT/'26906_TONE_SHADER_SPIRV_VALIDATED.txt'):
  if not path.is_file() or not path.stat().st_size or 'PASS' not in path.read_text():fail('missing genuine new shader compiler/spirv receipt '+str(path))
 for path in ['26904_GLSL_REAL_COMPILER.txt','26904_SPIRV_VALIDATED.txt','26904_SPEKTRA_GLSLANG_CMAKE_HANDOFF.txt']:
  if not (R/'photon_26904_incremental_outputs'/path).is_file():fail('26904 inherited actual compiler/handoff receipt missing '+path)
 if baseline[GENERATED]!='5853f1a0da12bab4b8c9489b6b298f3710f90fb6e51660204ed43f49963809f1':fail('pinned AMaZE SPV drift')
 OUT.mkdir(exist_ok=True)
 (OUT/'26906_PREBUILD_SEALED_APP.sha256').write_text(''.join(f'{baseline[p]}  {p}\n' for p in sorted(baseline)))
 print('PASS 26906 exact source bytes, 3 modified real GLES compilers, original native SPV validated')

def finalize():
 expected=exact(R,OUT/'26906_PREBUILD_SEALED_APP.sha256','post full assemble frozen source')
 apks=list((R/'app/build/outputs/apk').rglob('*.apk'))
 if len(apks)!=1:fail('exactly one APK required got '+repr(apks))
 shutil.copy2(apks[0],R/APKNAME)
 if (R/APKNAME).stat().st_size<1_000_000:fail('APK invalid/small')
 gradle=(OUT/'26906_gradle_assemble.log')
 if not gradle.is_file():fail('missing real Gradle log')
 log=gradle.read_text(errors='replace')
 tasks=[':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL']
 if any(t not in log for t in tasks):fail('missing actual native/Kotlin/Javac/assemble task '+str([t for t in tasks if t not in log]))
 (OUT/'26906_REAL_GRADLE_TASKS.txt').write_text(''.join('PASS '+t+'\n' for t in tasks))
 (OUT/'26906_COMPILER_STATUS.txt').write_text('REAL PINNED GLSL COMPILE: PASS (26906 modified ESSL310 shaders)\nREAL SPIR-V VALIDATION: PASS\nREAL KOTLIN COMPILE: PASS\nREAL JAVA COMPILE: PASS\nNATIVE/NDK COMPILE: PASS (arm64-v8a and armeabi-v7a)\nREAL ANDROID Gradle :app:assembleDebug: PASS\nRUNTIME SOURCE INVARIANCE: PASS\nAPK '+APKNAME+' SHA256 '+sha(R/APKNAME)+'\n')
 (OUT/'26906_APK.sha256').write_text(sha(R/APKNAME)+'  '+APKNAME+'\n')
 (OUT/'26906_ACTUAL_EXECUTED_BUILDER.sha256').write_text(sha(R/'build_26906_incremental.py')+'  build_26906_incremental.py\n')
 (OUT/'26906_ACTIONS_IDENTITY.txt').write_text('git_sha='+os.getenv('GITHUB_SHA','local')+'\ngithub_run_id='+os.getenv('GITHUB_RUN_ID','local')+'\ngithub_job='+os.getenv('GITHUB_JOB','local')+'\n')
 workflow=R/'.github/workflows/build-26906-change-aware.yml'
 shutil.copy2(R/'build_26906_incremental.py',OUT/'ACTUAL_EXECUTED_build_26906_incremental.py')
 shutil.copy2(workflow,OUT/'ACTUAL_EXECUTED_build-26906-change-aware.yml')
 (OUT/'26906_ACTUAL_EXECUTED_WORKFLOW.sha256').write_text(sha(workflow)+'  .github/workflows/build-26906-change-aware.yml\n')
 base=parse(R/'26906_BASE_26905_FULL_APP.sha256');modified=set((R/'26906_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
 (OUT/'26906_PROTECTED_SOURCE.sha256').write_text(''.join(f'{base[p]}  {p}\n' for p in sorted(base) if p not in modified))
 (OUT/'26906_BASE_26905_FULL_APP.sha256').write_bytes((R/'26906_BASE_26905_FULL_APP.sha256').read_bytes())
 (OUT/'26906_CHANGED_RUNTIME_ALLOWLIST.txt').write_bytes((R/'26906_CHANGED_RUNTIME_ALLOWLIST.txt').read_bytes())
 (OUT/'26906_VERSION.txt').write_text('VERSION_NAME=0.9726906\nVERSION_BUILD=26906\n')
 tar=OUT/'26906_candidate_app_source.tar.gz'
 with tarfile.open(tar,'w:gz',compresslevel=1) as z:
  for p in sorted(expected):
   f=R/p;info=z.gettarinfo(str(f),arcname=p);info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
   with f.open('rb') as inp:z.addfile(info,inp)
 (OUT/'26906_candidate_app_source.tar.gz.sha256').write_text(sha(tar)+'  26906_candidate_app_source.tar.gz\n')
 print('PASS one real 26906 Android APK, all 2018 protected source files, actual executed builder+workflow',sha(R/APKNAME))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['seal','fetch','prepare','verify-compiled','finalize']);args=p.parse_args()
 try:globals()[args.command.replace('-','_')]()
 except Exception as e:print('ERROR',str(e),file=sys.stderr);sys.exit(1)
