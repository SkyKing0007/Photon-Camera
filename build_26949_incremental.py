#!/usr/bin/env python3
"""Photon 26949: exact successful 26948 Actions candidate and change-aware three-stage release.
No downgrade to static validators. All true Android builds happen in the guarded Actions job.
"""
import argparse,gzip,hashlib,json,os,pathlib,re,shutil,subprocess,sys,tarfile,tempfile,urllib.request,zipfile
R=pathlib.Path(__file__).resolve().parent
TMP=R/'.photon_26949_incremental_work';OUT=R/'photon_26949_outputs'
ART=TMP/'26948-success.zip';BASE=TMP/'authority_26948';CAND=TMP/'candidate_26949'
REPO='SkyKing0007/Photon-Camera';BRANCH='experimental-clean-photon-rebuild'
RUN=43978332028;COMMIT='652dd7f9d3674aa9d4e0c3c4bcd779fef0987698';ART_ID=14281174777
ART_SHA='c827df119909d2a545cc56087a43ae14447367c501202d22dd244beae89c4cb0'
TAR_SHA='318911798c8a6f7de69352b9dcc8b44ba0d39fb3ade9503db2d2e14da598f041'
BUILDER_SHA='ec89476d37dcf14bac0b592e638dcdcb091e76881b5b797f4773414d84a39901'
WORKFLOW_SHA='b5e17631bd2af89d73b984a9124cd840d33494a1abe80cd5fbd464bccd637fc5'
PRIOR_APK_SHA='e7217479680d136ed07902162cbea83bc9d11310b437b85cc4df243b8bf7535a'
PRIOR_APK_NAME='IrisCamera-0.9726948-26948-iris-rawr-debug.apk'
APKNAME='IrisCamera-0.9726949-26949-iris-rawr-debug.apk'
NBASE=2054;NFILES=2054;NCHANGE=3;NPROTECTED=2051
REQUIRED={
 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
 'app/version.properties',
}
STAGE1_FILES=['README_PHOTON_26949.md', '26949_LOCAL_VERIFICATION.txt', '26949_COMMIT_MESSAGE.txt', 'build_26949_incremental.py', 'prepare_26949_lkr_from_successful_26948.py', 'test_26949_source.py', 'test_26949_restore.py', 'test_26949_patch_proof.py', 'test_26949_sealed_negatives.py', 'test_26949_workflow_refs.py', 'compile_26949_shaders.sh', 'replay_26949_inherited_26948_glsl.py', '26949_FORWARD_FULLINDEX.patch', '26949_ROLLBACK_FULLINDEX.patch', '26949_BASE_26948_FULL_APP.sha256', '26949_EXPECTED_FULL_APP.sha256', '26949_PROTECTED_SOURCE.sha256', '26949_CHANGED_RUNTIME_ALLOWLIST.txt', '26949_ADDED_RUNTIME_PATHS.txt', '26949_DELETED_RUNTIME_PATHS.txt', '26949_EXPECTED_ACTION_EXECUTABLES.txt', '26949_STAGE_1_UPLOAD_PATHS.txt', '26949_STAGE_2_UPLOAD_PATHS.txt', '26949_STAGE_3_UPLOAD_PATHS.txt']


def fail(msg):raise RuntimeError('26949 BLOCKED: '+str(msg))
def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def parse(path):
 d={}
 for line in path.read_text().splitlines():
  try:h,p=line.split('  ',1)
  except ValueError:fail('malformed manifest line')
  if len(h)!=64 or any(c not in '0123456789abcdef' for c in h) or not p.startswith('app/') or '..' in pathlib.PurePosixPath(p).parts or p in d:fail('invalid manifest path '+p)
  d[p]=h
 return d
def scan(root):
 paths=[*(root/'app/src').rglob('*'),root/'app/build.gradle',root/'app/version.properties']
 out={}
 for p in paths:
  if p.is_symlink():fail('source symlink '+str(p))
  if p.is_file():out[p.relative_to(root).as_posix()]=sha(p)
 return out
def exact(root,man,label):
 want=parse(R/man);got=scan(root)
 if want!=got:
  missing=sorted(want.keys()-got.keys());extra=sorted(got.keys()-want.keys())
  wrong=sorted(p for p in want.keys()&got.keys() if want[p]!=got[p])
  fail(f'{label} source mismatch missing={missing[:3]} added={extra[:3]} changed={wrong[:7]}')
 print('PASS',label,len(got));return got
def scope():
 old=parse(R/'26949_BASE_26948_FULL_APP.sha256');new=parse(R/'26949_EXPECTED_FULL_APP.sha256')
 ch=set((R/'26949_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
 ad=set((R/'26949_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
 dl=set((R/'26949_DELETED_RUNTIME_PATHS.txt').read_text().splitlines())
 if (len(old),len(new),len(ch),len(old)-len(ch))!=(NBASE,NFILES,NCHANGE,NPROTECTED):fail('universe/count mismatch')
 if ch!=REQUIRED or ad or dl or set(old)!=set(new) or {p for p in old if old[p]!=new[p]}!=ch:fail('exact changed-file allowlist mismatch')
 if {p:h for p,h in old.items() if p not in ch}!=parse(R/'26949_PROTECTED_SOURCE.sha256'):fail('2051 protected source hashes wrong')
 if old['app/build.gradle']!=new['app/build.gradle']:fail('Gradle scope changed')
 for p in ch:
  if any(k in p for k in ('/cpp/','/vendor/','/jniLibs/')) or p.endswith(('.so','.aar','.jar','.spv')):fail('native/vendor binary scope changed')
  if p.endswith(('.glsl','.frag','.kt','.java')) and p not in REQUIRED:fail('non-allowlisted runtime source changed')
 if new['app/version.properties']==old['app/version.properties']:fail('version unmodified')
 return ch,old,new

def seal():
 # Every locked authority digest must be a canonical SHA-256 before any artifact fetch.
 # 26945 V1 had a 65-character source-TAR literal; historical syntax checks did not
 # catch it, and genuine Actions stopped at the source restoration gate.
 for name in ('ART_SHA','TAR_SHA','BUILDER_SHA','WORKFLOW_SHA','PRIOR_APK_SHA'):
  val=globals()[name]
  if not isinstance(val,str) or not re.fullmatch(r'[0-9a-f]{64}',val):
   fail('noncanonical or stale authority SHA-256 '+name)
 ch,old,new=scope()
 sealed={}
 for line in (R/'26949_HANDOFF_HASHES.sha256').read_text().splitlines():
  try:h,p=line.split('  ',1)
  except ValueError:fail('malformed sealed SHA entry')
  if p in sealed or not (R/p).is_file() or sha(R/p)!=h:fail('tampered/missing staged file '+p)
  sealed[p]=h
 wf='.github/workflows/build-26949-change-aware.yml';trigger='TRIGGER_26949.txt'
 wanted=set(STAGE1_FILES)|{wf,trigger}|{'handoff_payload_26949/'+p for p in ch}
 if set(sealed)!=wanted:fail('unexpected/missing staged artifact '+str(sorted(set(sealed)^wanted)[:8]))
 stages=[(R/f'26949_STAGE_{i}_UPLOAD_PATHS.txt').read_text().splitlines() for i in (1,2,3)]
 if stages[0]!=sorted((wanted|{'26949_HANDOFF_HASHES.sha256'})-{wf,trigger}) or stages[1]!=[wf] or stages[2]!=[trigger]:fail('three-stage list mismatch')
 overlay={p.relative_to(R/'handoff_payload_26949').as_posix() for p in (R/'handoff_payload_26949').rglob('*') if p.is_file()}
 if overlay!=ch:fail('exact overlay allowlist mismatch')
 if any(sha(R/'handoff_payload_26949'/p)!=new[p] for p in ch):fail('source overlay checksum mismatch')
 workflow=(R/wf).read_text()
 for snippet in ('verify_26904_v3_safety.py', 'verify_26904_v2_safety.py', 'test_26903_v3_archive_receipt.py', 'build_26943_incremental.py seal', 'build_26944_incremental.py seal', 'build_26945_incremental.py seal', 'build_26946_incremental.py seal', 'build_26948_incremental.py seal', 'build_26949_incremental.py seal', 'test_26948_sealed_negatives.py', 'test_26948_patch_proof.py --payload', 'test_26949_patch_proof.py --live', 'test_26949_restore.py --live', 'test_26949_restore.py --payload', 'test_26949_restore.py --live', 'compile_26904_shaders_v2.sh', 'compile_26939_shaders.sh', 'compile_26941_shaders.sh', 'compile_26942_shaders.sh', 'compile_26943_shaders.sh', 'compile_26944_shaders.sh', 'replay_26949_inherited_26948_glsl.py', 'compile_26949_shaders.sh', 'prepare_26949_lkr_from_successful_26948.py', 'test_26931_native_integrity.py --native', 'test_26931_native_integrity.py --cmake', 'test_26931_native_integrity.py --apk', 'verify_26906_native_cache.py preflight', 'verify_26906_native_cache.py postflight', 'build_26949_incremental.py fetch', 'build_26949_incremental.py prepare', 'build_26949_incremental.py verify-compiled', 'build_26949_incremental.py finalize', ':app:assembleDebug --stacktrace', 'actions/upload-artifact@v4'):
  if snippet not in workflow:fail('inherited/added mandatory Actions check missing: '+snippet)
 if workflow.count('actions/upload-artifact@v4')!=1 or workflow.count('./gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace')!=1:fail('multiple builds/artifacts')
 if 'TRIGGER_26949.txt' not in workflow or 'TRIGGER_26948.txt' in workflow.split('paths:',1)[1].split('jobs:',1)[0]:fail('trigger gate not advanced')
 print('PASS three-stage SHA/source seal + successful 26948 and full historical regression graph')

def fetch():
 seal();token=os.getenv('GITHUB_TOKEN','')
 if not token or os.getenv('GITHUB_REPOSITORY')!=REPO or os.getenv('GITHUB_REF_NAME')!=BRANCH:fail('Actions token/branch/repository identity missing')
 def get(endpoint):
  req=urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+endpoint,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'})
  with urllib.request.urlopen(req,timeout=120) as resp:return json.load(resp)
 run=get('actions/runs/'+str(RUN));art=get('actions/artifacts/'+str(ART_ID))
 if run.get('id')!=RUN or run.get('conclusion')!='success' or run.get('head_branch')!=BRANCH or run.get('head_sha')!=COMMIT:fail('26948 successful Actions identity mismatch')
 if art.get('id')!=ART_ID or art.get('expired') or art.get('digest')!='sha256:'+ART_SHA or art.get('workflow_run',{}).get('id') not in (None,RUN):fail('26948 published artifact mismatch')
 TMP.mkdir(exist_ok=True)
 subprocess.run(['curl','--fail','--location','--retry','3','--silent','--show-error','-H','Authorization: Bearer '+token,'-H','Accept: application/vnd.github+json','https://api.github.com/repos/'+REPO+'/actions/artifacts/'+str(ART_ID)+'/zip','-o',str(ART)],check=True)
 if sha(ART)!=ART_SHA:fail('26948 downloaded artifact ZIP SHA mismatch')
 with zipfile.ZipFile(ART) as z:
  if z.testzip():fail('26948 published artifact ZIP CRC failed')
  tarname='photon_26948_outputs/26948_candidate_app_source.tar.gz'
  receiptname=tarname+'.sha256'
  if tarname not in z.namelist() or receiptname not in z.namelist():fail('compiled 26948 source TAR or receipt missing')
  if z.read(receiptname).decode('ascii')!=TAR_SHA+'  26948_candidate_app_source.tar.gz\n':fail('26948 published source TAR SHA receipt invalid')
  with z.open(tarname) as f:
   h=hashlib.sha256()
   for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
   if h.hexdigest()!=TAR_SHA:fail('26948 published source TAR actual bytes SHA differs')
 print('PASS exact successful published 26948 GitHub Actions, artifact, source TAR and source receipt bytes')

def safe_tar(blob,dst):
 with tarfile.open(fileobj=blob,mode='r:gz') as t:
  for m in t:
   p=pathlib.PurePosixPath(m.name)
   if not p.parts or p.is_absolute() or p.parts[0]!='app' or '..' in p.parts or not(m.isfile() or m.isdir()) or m.issym() or m.islnk():fail('unsafe prior source TAR path '+m.name)
  t.extractall(dst,filter='data')

def prepare():
 seal()
 if not ART.is_file() or sha(ART)!=ART_SHA:fail('successful 26948 published artifact not fetched')
 for d in (BASE,CAND):
  if d.exists():shutil.rmtree(d)
 BASE.mkdir(parents=True)
 with zipfile.ZipFile(ART) as z:
  if z.testzip():fail('26948 artifact ZIP CRC fail')
  def get(n):
   p='photon_26948_outputs/'+n
   if p not in z.namelist():fail('missing published 26948 member '+p)
   return z.read(p)
  raw=get('26948_candidate_app_source.tar.gz')
  reported=get('26948_candidate_app_source.tar.gz.sha256').decode('ascii')
  if reported!=TAR_SHA+'  26948_candidate_app_source.tar.gz\n':
   fail('successful 26948 source TAR published receipt differs from locked SHA')
  actual_tar_sha=hashlib.sha256(raw).hexdigest()
  if actual_tar_sha!=TAR_SHA:fail('actual compiled 26948 source TAR wrong: actual='+actual_tar_sha+' expected='+TAR_SHA)
  expected=(R/'26949_BASE_26948_FULL_APP.sha256').read_bytes()
  if get('26948_PREBUILD_SEALED_APP.sha256')!=expected or get('26948_EXPECTED_FULL_APP.sha256')!=expected:fail('26948 source manifest mismatch')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build_26948_incremental.py')).hexdigest()!=BUILDER_SHA or BUILDER_SHA not in get('26948_ACTUAL_EXECUTED_BUILDER.sha256').decode():fail('26948 executed builder wrong')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build-26948-change-aware.yml')).hexdigest()!=WORKFLOW_SHA or WORKFLOW_SHA not in get('26948_ACTUAL_EXECUTED_WORKFLOW.sha256').decode():fail('26948 executed workflow wrong')
  if PRIOR_APK_SHA not in get('26948_APK.sha256').decode() or PRIOR_APK_NAME not in z.namelist():fail('26948 APK/receipt absent')
  ident=get('26948_ACTIONS_IDENTITY.txt').decode()
  if 'git_sha='+COMMIT not in ident or 'github_run_id='+str(RUN) not in ident:fail('26948 Actions receipt mismatch')
  for word in ('REAL PINNED GLSL COMPILE: PASS','REAL SPIR-V VALIDATION: PASS','REAL KOTLIN COMPILE: PASS','REAL JAVA COMPILE: PASS','NATIVE/NDK COMPILE: PASS','REAL ANDROID Gradle :app:assembleDebug: PASS','RUNTIME SOURCE INVARIANCE: PASS'):
   if word not in get('26948_COMPILER_STATUS.txt').decode():fail('26948 compiler authority missing '+word)
  for task in (':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL'):
   if 'PASS '+task not in get('26948_REAL_GRADLE_TASKS.txt').decode():fail('26948 compiled task receipt missing '+task)
  # The already validated tarball is extracted once from the actual published artifact.
  import io
  safe_tar(io.BytesIO(raw),BASE)
 exact(BASE,'26949_BASE_26948_FULL_APP.sha256','26948 actual compiled candidate restored')
 shutil.copytree(BASE,CAND)
 for p in sorted(REQUIRED):
  src=R/'handoff_payload_26949'/p;dst=CAND/p
  if not src.is_file() or not dst.is_file():fail('missing 26949 overlay '+p)
  shutil.copy2(src,dst)
 exact(CAND,'26949_EXPECTED_FULL_APP.sha256','candidate-first 26949 reconstructed')
 if not (R/'gradlew').is_file() or not (R/'app/build.gradle').is_file():fail('real Gradle project checkout absent')
 if (R/'app/src').exists():shutil.rmtree(R/'app/src')
 shutil.copytree(CAND/'app/src',R/'app/src')
 shutil.copy2(CAND/'app/version.properties',R/'app/version.properties')
 shutil.copy2(CAND/'app/build.gradle',R/'app/build.gradle')
 if (R/'app/.cxx').exists():shutil.rmtree(R/'app/.cxx')
 exact(R,'26949_EXPECTED_FULL_APP.sha256','live 26949 identical candidate')
 OUT.mkdir(exist_ok=True)
 (OUT/'26949_SOURCE_SCOPE.txt').write_text(f'Authority SUCCESSFUL 26948 run={RUN} commit={COMMIT} artifact={ART_ID} artifact_sha={ART_SHA} actual_TAR_sha={TAR_SHA}\nActual 26948 executed builder={BUILDER_SHA} workflow={WORKFLOW_SHA} APK={PRIOR_APK_SHA}\nsource universe=2054 changed=3 protected=2051 new=0 deleted=0; B OFF original RAWR AMaZE handoff/FCC restoration; Experiment A/native/vendor protected.\n'+''.join(x+'\n' for x in sorted(REQUIRED)))
 print('PASS authority seeded three-file 26949 source, 2051 protected')

def regress():
 seal();exact(R,'26949_EXPECTED_FULL_APP.sha256','26949 current live source')
 for t in ('test_26949_source.py','test_26949_restore.py','test_26949_patch_proof.py'):
  subprocess.run([sys.executable,'-S',t,'--live'],cwd=R,check=True)
 print('PASS 26949 original B OFF RAWR AMaZE/FCC branches, source and rollback')

def verify_compiled():
 regress()
 # Replay successful unchanged shader and Vulkan receipts rather than
 # accepting a static-only validator as proof of updated B OFF shader.
 c=R/'photon_26944_outputs/26944_REAL_GLSL_SPIRV_COMPILER.txt'
 if not c.is_file() or 'PASS 26944 real pinned shader and SPIR-V' not in c.read_text():fail('26944 inherited real pinned GLSL compiler receipt missing')
 if '16.5.0' not in (R/'photon_26944_outputs/26944_GLSLANG_VERSION.txt').read_text():fail('26944 pinned glslang version differs')
 for name in ('Iris26888BOffHdrqMismatch.comp','Iris26887BOffHdrqMerge.comp'):
  p=R/'app/src/main/cpp/iris26864/bridge'/name
  if sha(p) not in c.read_text():fail('actual unchanged native GLSL SHA absent from pinned receipt: '+name)
 original=R/'photon_26948_outputs/26948_REAL_GLSL_SPIRV_COMPILER.txt'
 if not original.is_file() or 'PASS 26948 real pinned GLES/SPIR-V current three shader sources' not in original.read_text():fail('inherited 26948 real pinned shader compiler receipt missing')
 for path in ('app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl','app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag'):
  if sha(R/path) not in original.read_text():fail('unchanged 26948 compiled GLSL SHA differs '+path)
 target=R/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt'
 receipt=OUT/'26949_REAL_GLSL_COMPILER.txt'
 if not receipt.is_file() or 'PASS 26949 real pinned runtime-expanded GLES300 post-AMaZE shader' not in receipt.read_text() or sha(target) not in receipt.read_text():fail('26949 changed real B OFF shader not compiled by pinned glslang')
 subprocess.run([sys.executable,'-S','test_26931_native_integrity.py','--native'],cwd=R,check=True)
 n=OUT/'26949_INHERITED_LKR_NATIVE_RECEIPT.txt'
 if not n.is_file() or 'SUCCESSFUL 26948 Actions run='+str(RUN) not in n.read_text():fail('26948 original LKR dual-ABI provenance not proven')
 (OUT/'26949_PREBUILD_SEALED_APP.sha256').write_bytes((R/'26949_EXPECTED_FULL_APP.sha256').read_bytes())
 shutil.copy2(c,OUT/'26949_INHERITED_26944_GLSL_SPIRV_COMPILER.txt')
 print('PASS original 26948 pinned/native receipt and ACTUAL new 26949 shader compiler, 2051 source protected')

def finalize():
 regress()
 if (OUT/'26949_PREBUILD_SEALED_APP.sha256').read_bytes()!=(R/'26949_EXPECTED_FULL_APP.sha256').read_bytes():fail('compiler did not seal actual source')
 log=(OUT/'26949_gradle_assemble.log').read_text(errors='replace')
 tasks=(':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL')
 for t in tasks:
  if t not in log:fail('real Gradle task missing '+t)
 subprocess.run([sys.executable,'-S','test_26931_native_integrity.py','--cmake'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','verify_26906_native_cache.py','postflight'],cwd=R,check=True)
 apks=list((R/'app/build/outputs/apk').rglob('*.apk'))
 if len(apks)!=1:fail('not exactly one new APK')
 shutil.copy2(apks[0],R/APKNAME)
 if (R/APKNAME).stat().st_size<1000000:fail('APK unexpectedly small')
 subprocess.run([sys.executable,'-S','test_26931_native_integrity.py','--apk'],cwd=R,check=True)
 with zipfile.ZipFile(R/APKNAME) as z:
  if z.testzip() or not {'AndroidManifest.xml','classes.dex'}<=set(z.namelist()):fail('APK content invalid')
 (OUT/'26949_COMPILER_STATUS.txt').write_text('REAL PINNED GLSL COMPILE: PASS (actual 26949 edited B shaders)\nREAL SPIR-V VALIDATION: PASS\nREAL KOTLIN COMPILE: PASS\nREAL JAVA COMPILE: PASS\nNATIVE/NDK COMPILE: PASS (two ABIs)\nREAL ANDROID Gradle :app:assembleDebug: PASS\nORIGINAL RAWLENS NATIVE: PASS (from successful 26948 APK)\nRUNTIME SOURCE INVARIANCE: PASS (2051 protected)\nDEVICE IMAGE QUALITY: NOT RUN\n')
 (OUT/'26949_REAL_GRADLE_TASKS.txt').write_text(''.join('PASS '+t+'\n' for t in tasks))
 (OUT/'26949_APK.sha256').write_text(sha(R/APKNAME)+'  '+APKNAME+'\n')
 wf=R/'.github/workflows/build-26949-change-aware.yml'
 (OUT/'26949_ACTUAL_EXECUTED_BUILDER.sha256').write_text(sha(R/'build_26949_incremental.py')+'  build_26949_incremental.py\n')
 (OUT/'26949_ACTUAL_EXECUTED_WORKFLOW.sha256').write_text(sha(wf)+'  .github/workflows/build-26949-change-aware.yml\n')
 (OUT/'26949_ACTIONS_IDENTITY.txt').write_text('git_sha='+os.getenv('GITHUB_SHA','NOT_IN_ACTIONS')+'\ngithub_run_id='+os.getenv('GITHUB_RUN_ID','NOT_IN_ACTIONS')+'\n')
 for p in ('26949_BASE_26948_FULL_APP.sha256','26949_EXPECTED_FULL_APP.sha256','26949_PROTECTED_SOURCE.sha256','26949_CHANGED_RUNTIME_ALLOWLIST.txt','26949_ADDED_RUNTIME_PATHS.txt','26949_DELETED_RUNTIME_PATHS.txt'):
  shutil.copy2(R/p,OUT/p)
 shutil.copy2(R/'build_26949_incremental.py',OUT/'ACTUAL_EXECUTED_build_26949_incremental.py')
 shutil.copy2(wf,OUT/'ACTUAL_EXECUTED_build-26949-change-aware.yml')
 with (OUT/'26949_candidate_app_source.tar.gz').open('wb') as file:
  with gzip.GzipFile(filename='',mode='wb',compresslevel=1,mtime=0,fileobj=file) as g:
   with tarfile.open(fileobj=g,mode='w') as t:
    for p in sorted(parse(R/'26949_EXPECTED_FULL_APP.sha256')):
     src=R/p;meta=t.gettarinfo(str(src),arcname=p)
     meta.uid=meta.gid=0;meta.uname=meta.gname='';meta.mtime=0
     with src.open('rb') as inp:t.addfile(meta,inp)
 (OUT/'26949_candidate_app_source.tar.gz.sha256').write_text(sha(OUT/'26949_candidate_app_source.tar.gz')+'  26949_candidate_app_source.tar.gz\n')
 print('PASS actual 26949 one APK, two ABI real compile, 2051 protected sources, Actions TAR/receipt')

if __name__=='__main__':
 try:
  parser=argparse.ArgumentParser();parser.add_argument('command',choices=['seal','fetch','prepare','regress','verify-compiled','finalize']);parser.add_argument('--package-only',action='store_true');a=parser.parse_args()
  globals()['PACKAGE_ONLY']=a.package_only
  globals()[a.command.replace('-','_')]()
 except Exception as e:
  print(str(e),file=sys.stderr);sys.exit(1)
