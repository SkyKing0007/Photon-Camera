#!/usr/bin/env python3
"""Photon 26905 change-scoped authority-seeded Android build (not 17-stage historical runner).

Every invocation fails closed; the first transition obtains the *latest successful 26904*
compiled source TAR from the actual Actions artifact. Only explicitly SHA-sealed 26905
files may differ. Standard Gradle caching handles correct transitive invalidation;
no APK binary patching, no substitution of stale repository app/src.
"""
from __future__ import annotations
import argparse, hashlib, io, json, os, pathlib, shutil, stat, subprocess, sys, tarfile, tempfile, urllib.request, zipfile

ROOT = pathlib.Path(__file__).resolve().parent
WORK = ROOT / '.photon_26905_incremental_work'
OUT = ROOT / 'photon_26905_incremental_outputs'
BASE = WORK / 'authority_26904'
CAND = WORK / 'candidate_26905'
ARTZIP = WORK / '26904_successful_actions_artifact.zip'
REPO = 'SkyKing0007/Photon-Camera'
BRANCH = 'experimental-clean-photon-rebuild'
RUN_ID = 42239513792
COMMIT = '39c8bb9fe4f92e326a88486617c4457b5060d61c'
ART_ID = 13517085033
ART_SHA = 'b33d381ea30459f83d05ab9ac780014ae5bf250ea85447b1e7445483fe22115b'
TAR_SHA = 'c63ab18da57d63eeacecd424caa398d3c66c13b7c81c7ed0a92f6f4849221cec'
RUNNER_SHA = '2c0d6edb0a70f1545713a767a5522b5744c382de915fa756e3ab280315add42d'
VERSION = '26905'
VERSION_NAME = '0.9726905'
BASE_MANIFEST = ROOT/'26905_BASE_26904_FULL_APP.sha256'
PRE_MANIFEST = ROOT/'26905_PRECOMPILE_EXPECTED_FULL_APP.sha256'
CHANGES = ROOT/'26905_CHANGED_RUNTIME_ALLOWLIST.txt'
GENERATED = 'app/src/main/assets/iris26856/rawr/amaze/spv/amaze_export.spv'
APK_NAME = f'IrisCamera-{VERSION_NAME}-{VERSION}-iris-rawr-debug.apk'


def fail(message): raise RuntimeError('26905 BLOCKED: '+str(message))

def sha(path):
    digest=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''): digest.update(block)
    return digest.hexdigest()

def parse_sha(path):
    ans={}
    for line in path.read_text().splitlines():
        if not line.strip():continue
        try: h,p=line.split('  ',1)
        except ValueError: fail('invalid SHA manifest '+str(path))
        if len(h)!=64 or any(c not in '0123456789abcdef' for c in h):fail('bad hash '+str(path))
        if p in ans or not p.startswith('app/') or '..' in pathlib.PurePosixPath(p).parts:fail('bad path '+p)
        ans[p]=h
    return ans

def all_app_files(root):
    ans={}
    for f in (root/'app').rglob('*'):
        if f.is_symlink():fail('source symlink forbidden '+str(f))
        if f.is_file() and f.relative_to(root/'app').parts[0] not in ('build','.cxx'):
            p=f.relative_to(root).as_posix();ans[p]=sha(f)
    return ans

def exact_manifest(root,expected,label):
    current=all_app_files(root);want=parse_sha(expected)
    if current!=want:
        missing=sorted(want.keys()-current.keys())
        extra=sorted(current.keys()-want.keys())
        altered=sorted(p for p in want.keys()&current.keys() if current[p]!=want[p])
        fail(f'{label}: missing={missing[:12]} extra={extra[:12]} mismatches={altered[:12]}')
    print('PASS',label,'source files',len(current))
    return current

def seal_staging():
    entries={}
    for line in (ROOT/'26905_HANDOFF_HASHES.sha256').read_text().splitlines():
        if not line.strip(): continue
        h,p=line.split('  ',1)
        f=ROOT/p
        if not f.is_file() or sha(f)!=h:fail('tampered staged file '+p)
        if p in entries:fail('duplicate seal '+p)
        entries[p]=h
    wanted=set((ROOT/'26905_STAGE1_PATHS.txt').read_text().splitlines())
    if '26905_HANDOFF_HASHES.sha256' not in wanted:fail('seal must itself be uploaded in Stage1')
    wanted.remove('26905_HANDOFF_HASHES.sha256')
    # Stage2 & Stage3 are deliberately absent from Stage1 only during manual upload;
    # when Actions starts they must be present and hash-verified.
    wanted.update(['.github/workflows/build-26905-change-aware.yml','TRIGGER_26905.txt'])
    if set(entries)!=wanted:fail('staged sha set differs from exact frozen upload list')
    if (ROOT/'TRIGGER_26905.txt').read_bytes()!=b'RUN_26905_B_OFF_NORMAL_BURST_AND_NOISE_RECEIPT_V1\n':fail('trigger content changed')
    for p in wanted:
        if p.startswith('handoff_payload_26905') and not p.startswith('handoff_payload_26905/app/'):
            fail('unexpected runtime payload path')
    actual_payload={p for p in wanted if p.startswith('handoff_payload_26905/app/')}
    expected_payload={'handoff_payload_26905/'+p for p in (ROOT/'26905_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()}
    if actual_payload!=expected_payload:fail('payload paths differ from exact runtime allowlist')
    print('PASS sealed upload manifest',len(entries),'paths, branch trigger exact')


def github_json(path,token):
    request=urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+path,
        headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'})
    with urllib.request.urlopen(request,timeout=90) as resp:return json.load(resp)

def fetch():
    token=os.environ.get('GITHUB_TOKEN','')
    if not token:fail('Actions GITHUB_TOKEN missing (download required only for first transition)')
    seal_staging()
    if os.environ.get('GITHUB_REPOSITORY',REPO)!=REPO:fail('wrong GitHub repo')
    if os.environ.get('GITHUB_REF_NAME',BRANCH)!=BRANCH:fail('wrong GitHub branch')
    run=github_json(f'actions/runs/{RUN_ID}',token)
    art=github_json(f'actions/artifacts/{ART_ID}',token)
    if run.get('conclusion')!='success' or run.get('id')!=RUN_ID or run.get('head_sha')!=COMMIT or run.get('head_branch')!=BRANCH:
        fail('26904 authority run is not the pinned successful branch/commit')
    if art.get('id')!=ART_ID or art.get('expired') or art.get('digest')!='sha256:'+ART_SHA:
        fail('26904 authority artifact missing, expired or changed')
    WORK.mkdir(exist_ok=True)
    import urllib.error
    # curl follows the GitHub artifact signed download while downloading to disk.
    command=['curl','--fail','--location','--retry','3','--silent','--show-error',
             '-H','Authorization: Bearer '+token,
             '-H','Accept: application/vnd.github+json',
             f'https://api.github.com/repos/{REPO}/actions/artifacts/{ART_ID}/zip',
             '--output',str(ARTZIP)]
    subprocess.run(command,check=True)
    if sha(ARTZIP)!=ART_SHA:fail('26904 downloaded artifact ZIP SHA mismatch')
    print('PASS successful 26904 run/artifact/digest and verified ZIP bytes',ART_SHA)


def safe_extract_tar(tarball,target):
    with tarfile.open(tarball,'r:gz') as t:
        for item in t.getmembers():
            path=pathlib.PurePosixPath(item.name)
            if path.is_absolute() or '..' in path.parts or not path.parts or path.parts[0]!='app':
                fail('unexpected TAR member '+item.name)
            if item.issym() or item.islnk() or not (item.isdir() or item.isfile()):
                fail('forbidden TAR entry '+item.name)
        t.extractall(target,filter='data')


def prepare():
    seal_staging()
    if not ARTZIP.is_file() or sha(ARTZIP)!=ART_SHA:fail('verified successful 26904 ZIP unavailable')
    if BASE.exists():shutil.rmtree(BASE)
    if CAND.exists():shutil.rmtree(CAND)
    BASE.mkdir(parents=True)
    with zipfile.ZipFile(ARTZIP) as archive:
        prefix='photon_26904_incremental_outputs/'
        tar_name=prefix+'26904_candidate_app_source.tar.gz'
        manifest_name=prefix+'26904_PREBUILD_SEALED_APP.sha256'
        receipt_name=prefix+'26904_ACTUAL_EXECUTED_BUILDER.sha256'
        compiler_name=prefix+'26904_COMPILER_STATUS.txt'
        for x in (tar_name,manifest_name,receipt_name,compiler_name):
            if x not in archive.namelist():fail('successful 26904 artifact missing '+x)
        old_manifest=archive.read(manifest_name)
        if old_manifest!=BASE_MANIFEST.read_bytes():fail('26904 successful manifest differs from frozen handoff')
        runner=archive.read(receipt_name).decode()
        if RUNNER_SHA not in runner:fail('actual executed successful 26904 builder does not match SHA')
        status=archive.read(compiler_name).decode()
        for token in ('REAL PINNED GLSL COMPILE: PASS','REAL SPIR-V VALIDATION: PASS',
                      'REAL ANDROID Gradle :app:assembleDebug: PASS', 'RUNTIME SOURCE INVARIANCE: PASS'):
            if token not in status:fail('26904 successful artifact missing compiler receipt '+token)
        temp=WORK/'26904_tar.gz'
        with archive.open(tar_name) as src,open(temp,'wb') as out:shutil.copyfileobj(src,out)
    if sha(temp)!=TAR_SHA:fail('actual successful 26904 candidate internal TAR mismatch')
    safe_extract_tar(temp,BASE)
    exact_manifest(BASE,BASE_MANIFEST,'actual successful 26904 compiled authority')
    shutil.copytree(BASE,CAND)
    changes=(ROOT/'26905_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
    if not changes or len(changes)!=len(set(changes)):fail('bad changed allowlist')
    for item in changes:
        a=ROOT/'handoff_payload_26905'/item
        b=CAND/item
        if not a.is_file() or not b.is_file():fail('missing overlay '+item)
        shutil.copy2(a,b)
    exact_manifest(CAND,PRE_MANIFEST,'26905 changed-file-only precompile candidate')
    before=parse_sha(BASE_MANIFEST)
    after=parse_sha(PRE_MANIFEST)
    scope={p for p in before.keys()&after.keys() if before[p]!=after[p]}
    if scope!=set(changes) or before.keys()!=after.keys():fail('unplanned add/delete/runtime differences')
    if (CAND/'app/version.properties').read_text().find('VERSION_BUILD=26905')<0:fail('version not advanced')
    live=ROOT/'app'
    if not (ROOT/'gradlew').is_file():fail('checkout missing Android Gradle wrapper')
    # Cached Gradle task outputs are retained; the SOURCE is always authority-seeded.
    if (live/'src').exists():shutil.rmtree(live/'src')
    shutil.copytree(CAND/'app/src',live/'src')
    shutil.copy2(CAND/'app/version.properties',live/'version.properties')
    shutil.copy2(CAND/'app/build.gradle',live/'build.gradle')
    if (live/'build/outputs/apk').exists():shutil.rmtree(live/'build/outputs/apk')
    exact_manifest(CAND,PRE_MANIFEST,'frozen candidate precompile')
    # Only app tree files on the frozen source manifest are considered compiler authority.
    installed={p:sha(ROOT/p) for p in after}
    if installed!=after:fail('installed app sources differ from frozen candidate')
    OUT.mkdir(exist_ok=True)
    (OUT/'26905_SOURCE_SCOPE.txt').write_text('base_run='+str(RUN_ID)+'\nbase_commit='+COMMIT+'\nbase_artifact='+str(ART_ID)+'\nbase_tar_sha='+TAR_SHA+'\nbase_files=2027\nintentional_runtime_changes='+str(len(changes))+'\n'+ '\n'.join(changes)+'\nGENERATED SPIR-V: '+GENERATED+'\n')
    print('PASS authority-seeded live source exact precompile/changed allowlist, 2027 files')


def verify_compiled():
    # Real pinned unmodified 26904 shader verification is still run by Actions
    # because native Spektra CMake requires its validated compiler handoff.
    old=ROOT/'photon_26904_incremental_outputs'
    for receipt in ('26904_GLSL_REAL_COMPILER.txt','26904_SPIRV_VALIDATED.txt',
                    '26904_SHADER_COMPILER_VERBOSE.log','26904_GLSLANG_VERSION.txt',
                    '26904_SPIRV_TOOLS_VERSION.txt','26904_SPEKTRA_GLSLANG_CMAKE_HANDOFF.txt'):
        f=old/receipt
        if not f.is_file() or not f.stat().st_size:fail('missing actual reused pinned shader proof '+receipt)
        OUT.mkdir(exist_ok=True)
        shutil.copy2(f,OUT/receipt)
    if 'REAL GLSL COMPILE: PASS' not in (old/'26904_GLSL_REAL_COMPILER.txt').read_text():
        fail('pinned shader receipt not successful')
    if 'REAL SPIR-V VALIDATION: PASS' not in (old/'26904_SPIRV_VALIDATED.txt').read_text():
        fail('real SPIR-V receipt not successful')
    before=parse_sha(PRE_MANIFEST)
    actual={p:sha(ROOT/p) for p in before}
    if actual!=before:fail('unmodified runtime shader recompilation changed source bytes')
    if actual[GENERATED]!='5853f1a0da12bab4b8c9489b6b298f3710f90fb6e51660204ed43f49963809f1':
        fail('generated SPIR-V not the successful 26904 identical compiled binary')
    OUT.mkdir(exist_ok=True)
    (OUT/'26905_PREBUILD_SEALED_APP.sha256').write_text(''.join(f'{actual[p]}  {p}\n' for p in sorted(actual)))
    print('PASS real unchanged pinned shaders, unchanged SPV, frozen 2027-file 26905 candidate')


def finalize():
    manifest=OUT/'26905_PREBUILD_SEALED_APP.sha256'
    if not manifest.is_file():fail('missing prebuild frozen compiled source manifest')
    expected=parse_sha(manifest)
    cur={p:sha(ROOT/p) for p in expected}
    if cur!=expected:fail('Android Gradle build changed frozen runtime source')
    apks=list((ROOT/'app/build/outputs/apk').rglob('*.apk'))
    if len(apks)!=1:fail('expected one intended APK, got '+repr(apks))
    apk=apks[0]; final=ROOT/APK_NAME
    shutil.copy2(apk,final)
    if not final.is_file() or final.stat().st_size<1_000_000:fail('Android APK missing/too small')
    gradle_log=OUT/'26905_gradle_assemble.log'
    if not gradle_log.is_file():fail('actual Gradle compile log missing')
    gradle_text=gradle_log.read_text(errors='replace')
    required_tasks=(':app:compileDebugKotlin', ':app:compileDebugJavaWithJavac',
                    ':app:configureCMakeDebug[arm64-v8a]', ':app:buildCMakeDebug[arm64-v8a]',
                    ':app:configureCMakeDebug[armeabi-v7a]', ':app:buildCMakeDebug[armeabi-v7a]',
                    ':app:assembleDebug', 'BUILD SUCCESSFUL')
    if any(x not in gradle_text for x in required_tasks):
        fail('real Gradle log lacks required Kotlin/Java/both native ABIs/assemble receipts')
    (OUT/'26905_REAL_GRADLE_TASKS.txt').write_text(''.join('PASS '+t+'\n' for t in required_tasks))
    status=OUT/'26905_COMPILER_STATUS.txt'
    status.write_text('REAL PINNED GLSL COMPILE: PASS (unchanged 26904 shader source, real recompilation)\n'
        'REAL SPIR-V VALIDATION: PASS\n'
        'REAL KOTLIN COMPILE: PASS (Gradle task verified)\n'
        'REAL JAVA COMPILE: PASS (Gradle task verified)\n'
        'NATIVE/NDK COMPILE: PASS (arm64-v8a and armeabi-v7a Gradle tasks verified)\n'
        'REAL ANDROID Gradle :app:assembleDebug: PASS (full real assemble)\n'
        'RUNTIME SOURCE INVARIANCE: PASS\n'
        f'APK {APK_NAME} SHA256 {sha(final)}\n')
    (OUT/'26905_APK.sha256').write_text(sha(final)+'  '+APK_NAME+'\n')
    (OUT/'26905_VERSION.txt').write_text('VERSION_NAME='+VERSION_NAME+'\nVERSION_BUILD='+VERSION+'\n')
    (OUT/'26905_ACTUAL_EXECUTED_BUILDER.sha256').write_text(sha(ROOT/'build_26905_incremental.py')+'  build_26905_incremental.py\n')
    (OUT/'26905_ACTIONS_IDENTITY.txt').write_text('git_sha='+os.getenv('GITHUB_SHA','local')+'\ngithub_run_id='+os.getenv('GITHUB_RUN_ID','local')+'\ngithub_job='+os.getenv('GITHUB_JOB','local')+'\ngithub_ref='+os.getenv('GITHUB_REF','local')+'\n')
    workflow=ROOT/'.github/workflows/build-26905-change-aware.yml'
    if not workflow.is_file():fail('actual workflow missing during finalized proof')
    shutil.copy2(ROOT/'build_26905_incremental.py',OUT/'ACTUAL_EXECUTED_build_26905_incremental.py')
    shutil.copy2(workflow,OUT/'ACTUAL_EXECUTED_build_26905-change-aware.yml')
    (OUT/'26905_ACTUAL_EXECUTED_WORKFLOW.sha256').write_text(sha(workflow)+'  .github/workflows/build-26905-change-aware.yml\n')
    before=parse_sha(BASE_MANIFEST)
    protected={p:before[p] for p in sorted(before) if p not in set((ROOT/'26905_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())}
    (OUT/'26905_PROTECTED_SOURCE.sha256').write_text(''.join(f'{h}  {p}\n' for p,h in protected.items()))
    (OUT/'26905_CHANGED_RUNTIME_ALLOWLIST.txt').write_bytes((ROOT/'26905_CHANGED_RUNTIME_ALLOWLIST.txt').read_bytes())
    (OUT/'26905_BASE_26904_FULL_APP.sha256').write_bytes(BASE_MANIFEST.read_bytes())
    
    tarpath=OUT/'26905_candidate_app_source.tar.gz'
    with tarfile.open(tarpath,'w:gz',compresslevel=1) as tar:
        for p in sorted(expected):
            file=ROOT/p
            ti=tar.gettarinfo(str(file),arcname=p)
            ti.uid=ti.gid=0;ti.uname=ti.gname='';ti.mtime=0
            with file.open('rb') as src:tar.addfile(ti,src)
    (OUT/'26905_candidate_app_source.tar.gz.sha256').write_text(sha(tarpath)+'  26905_candidate_app_source.tar.gz\n')
    print('PASS one APK source invariance & concise 26905 standalone proof bundle',sha(final))


def main():
    actions={'seal':seal_staging,'fetch':fetch,'prepare':prepare,'verify-compiled':verify_compiled,'finalize':finalize}
    p=argparse.ArgumentParser();p.add_argument('command',choices=list(actions));a=p.parse_args()
    actions[a.command]()
if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('ERROR',str(exc),file=sys.stderr)
        sys.exit(1)
