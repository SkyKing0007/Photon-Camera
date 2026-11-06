#!/usr/bin/env python3
"""Photon 26904 change-scoped authority-seeded Android build (not 17-stage historical runner).

Every invocation fails closed; the first transition obtains the *latest successful 26903*
compiled source TAR from the actual Actions artifact. Only explicitly SHA-sealed 26904
files may differ. Standard Gradle caching handles correct transitive invalidation;
no APK binary patching, no substitution of stale repository app/src.
"""
from __future__ import annotations
import argparse, hashlib, io, json, os, pathlib, shutil, stat, subprocess, sys, tarfile, tempfile, urllib.request, zipfile

ROOT = pathlib.Path(__file__).resolve().parent
WORK = ROOT / '.photon_26904_incremental_work'
OUT = ROOT / 'photon_26904_incremental_outputs'
BASE = WORK / 'authority_26903'
CAND = WORK / 'candidate_26904'
ARTZIP = WORK / '26903_successful_actions_artifact.zip'
REPO = 'SkyKing0007/Photon-Camera'
BRANCH = 'experimental-clean-photon-rebuild'
RUN_ID = 42064099430
COMMIT = '4a809afa81b885d2d47f27885d378763601fb667'
ART_ID = 13433183917
ART_SHA = 'ff8c629e520c1afe96613a0d4295949852661dff6817d362bc99e188635a21aa'
TAR_SHA = 'da7773b9554c4db903e961a12a524e6990c3630295ce7c37efa23f8251ce561d'
RUNNER_SHA = 'a5e9b4923325a13d3ab54fbfe233f3fca0d79b3a6f43ae194fa5edcb1ab67b44'
VERSION = '26904'
VERSION_NAME = '0.9726904'
BASE_MANIFEST = ROOT/'26904_BASE_26903_FULL_APP.sha256'
PRE_MANIFEST = ROOT/'26904_PRECOMPILE_EXPECTED_FULL_APP.sha256'
CHANGES = ROOT/'26904_CHANGED_RUNTIME_ALLOWLIST.txt'
GENERATED = 'app/src/main/assets/iris26856/rawr/amaze/spv/amaze_export.spv'
APK_NAME = f'IrisCamera-{VERSION_NAME}-{VERSION}-iris-rawr-debug.apk'


def fail(message): raise RuntimeError('26904 BLOCKED: '+str(message))

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
    for line in (ROOT/'26904_HANDOFF_HASHES.sha256').read_text().splitlines():
        if not line.strip(): continue
        h,p=line.split('  ',1)
        f=ROOT/p
        if not f.is_file() or sha(f)!=h:fail('tampered staged file '+p)
        if p in entries:fail('duplicate seal '+p)
        entries[p]=h
    wanted=set((ROOT/'26904_STAGE1_PATHS.txt').read_text().splitlines())
    if '26904_HANDOFF_HASHES.sha256' not in wanted:fail('seal must itself be uploaded in Stage1')
    wanted.remove('26904_HANDOFF_HASHES.sha256')
    # Stage2 & Stage3 are deliberately absent from Stage1 only during manual upload;
    # when Actions starts they must be present and hash-verified.
    wanted.update(['.github/workflows/build-26904-change-aware.yml','TRIGGER_26904.txt'])
    if set(entries)!=wanted:fail('staged sha set differs from exact frozen upload list')
    if (ROOT/'TRIGGER_26904.txt').read_bytes()!=b'RUN_26904_CHANGE_AWARE_BORDER_AND_NIGHT_B_V1\n':fail('trigger content changed')
    for p in wanted:
        if p.startswith('handoff_payload_26904') and not p.startswith('handoff_payload_26904/app/'):
            fail('unexpected runtime payload path')
    actual_payload={p for p in wanted if p.startswith('handoff_payload_26904/app/')}
    expected_payload={'handoff_payload_26904/'+p for p in (ROOT/'26904_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()}
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
        fail('26903 authority run is not the pinned successful branch/commit')
    if art.get('id')!=ART_ID or art.get('expired') or art.get('digest')!='sha256:'+ART_SHA:
        fail('26903 authority artifact missing, expired or changed')
    WORK.mkdir(exist_ok=True)
    import urllib.error
    # curl follows the GitHub artifact signed download while downloading to disk.
    command=['curl','--fail','--location','--retry','3','--silent','--show-error',
             '-H','Authorization: Bearer '+token,
             '-H','Accept: application/vnd.github+json',
             f'https://api.github.com/repos/{REPO}/actions/artifacts/{ART_ID}/zip',
             '--output',str(ARTZIP)]
    subprocess.run(command,check=True)
    if sha(ARTZIP)!=ART_SHA:fail('26903 downloaded artifact ZIP SHA mismatch')
    print('PASS successful 26903 run/artifact/digest and verified ZIP bytes',ART_SHA)


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
    if not ARTZIP.is_file() or sha(ARTZIP)!=ART_SHA:fail('verified successful 26903 ZIP unavailable')
    if BASE.exists():shutil.rmtree(BASE)
    if CAND.exists():shutil.rmtree(CAND)
    BASE.mkdir(parents=True)
    with zipfile.ZipFile(ARTZIP) as archive:
        prefix='build_26903_iris_rawr_outputs/'
        tar_name=prefix+'26903_candidate_app_source.tar.gz'
        manifest_name=prefix+'26903_candidate_full_app.sha256'
        receipt_name=prefix+'exact_generated_runner/EXACT_EXECUTED_RUNNER.sha256'
        compiler_name=prefix+'26903_COMPILER_STATUS.txt'
        for x in (tar_name,manifest_name,receipt_name,compiler_name):
            if x not in archive.namelist():fail('successful 26903 artifact missing '+x)
        old_manifest=archive.read(manifest_name)
        if old_manifest!=BASE_MANIFEST.read_bytes():fail('26903 successful manifest differs from frozen handoff')
        runner=archive.read(receipt_name).decode()
        if RUNNER_SHA not in runner:fail('actual executed successful 26903 runner does not match SHA')
        status=archive.read(compiler_name).decode()
        for token in ('REAL GLSL COMPILE: PASS','REAL SPIR-V VALIDATION: PASS',
                      'REAL KOTLIN COMPILE: PASS','REAL JAVA COMPILE: PASS',
                      'NATIVE/NDK COMPILE: PASS','FULL ANDROID ASSEMBLE: PASS'):
            if token not in status:fail('26903 successful artifact missing compiler receipt '+token)
        temp=WORK/'26903_tar.gz'
        with archive.open(tar_name) as src,open(temp,'wb') as out:shutil.copyfileobj(src,out)
    if sha(temp)!=TAR_SHA:fail('actual successful 26903 candidate internal TAR mismatch')
    safe_extract_tar(temp,BASE)
    exact_manifest(BASE,BASE_MANIFEST,'actual successful 26903 compiled authority')
    shutil.copytree(BASE,CAND)
    changes=(ROOT/'26904_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
    if not changes or len(changes)!=len(set(changes)):fail('bad changed allowlist')
    for item in changes:
        a=ROOT/'handoff_payload_26904'/item
        b=CAND/item
        if not a.is_file() or not b.is_file():fail('missing overlay '+item)
        shutil.copy2(a,b)
    exact_manifest(CAND,PRE_MANIFEST,'26904 changed-file-only precompile candidate')
    before=parse_sha(BASE_MANIFEST)
    after=parse_sha(PRE_MANIFEST)
    scope={p for p in before.keys()&after.keys() if before[p]!=after[p]}
    if scope!=set(changes) or before.keys()!=after.keys():fail('unplanned add/delete/runtime differences')
    if (CAND/'app/version.properties').read_text().find('VERSION_BUILD=26904')<0:fail('version not advanced')
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
    (OUT/'26904_SOURCE_SCOPE.txt').write_text('base_run='+str(RUN_ID)+'\nbase_commit='+COMMIT+'\nbase_artifact='+str(ART_ID)+'\nbase_tar_sha='+TAR_SHA+'\nbase_files=2027\nintentional_runtime_changes='+str(len(changes))+'\n'+ '\n'.join(changes)+'\nGENERATED SPIR-V: '+GENERATED+'\n')
    print('PASS authority-seeded live source exact precompile/changed allowlist, 2027 files')


def verify_compiled():
    # The pinned real shader compiler replaces one known generated AMaZE asset.
    if not (OUT/'26904_GLSL_REAL_COMPILER.txt').is_file():fail('real GLSL compiler receipt missing')
    if not (OUT/'26904_SPIRV_VALIDATED.txt').is_file():fail('real SPIR-V validation receipt missing')
    compiled=ROOT/GENERATED
    if not compiled.is_file() or compiled.read_bytes()[:4]!=b'\x03\x02\x23\x07':
        fail('compiled AMaZE SPIR-V missing/wrong magic')
    before=parse_sha(PRE_MANIFEST)
    cur={p:sha(ROOT/p) for p in before}
    diff={p for p in before if cur[p]!=before[p]}
    if diff!={GENERATED}:fail('shader compiler modified unexpected live source: '+repr(diff))
    # More current source can be generated by Gradle inside build dirs only.
    snapshot=OUT/'26904_PREBUILD_SEALED_APP.sha256'
    snapshot.write_text(''.join(f'{cur[p]}  {p}\n' for p in sorted(cur)))
    # Include the exact modified shader asset+receipt SHA, not an uncompiled stub.
    (OUT/'26904_GENERATED_AMAZE_EXPORT_SPV.sha256').write_text(sha(compiled)+'  '+GENERATED+'\n')
    print('PASS pinned compiled SPIR-V and source scope (only one generated asset)')


def finalize():
    manifest=OUT/'26904_PREBUILD_SEALED_APP.sha256'
    if not manifest.is_file():fail('missing prebuild frozen compiled source manifest')
    expected=parse_sha(manifest)
    cur={p:sha(ROOT/p) for p in expected}
    if cur!=expected:fail('Android Gradle build changed frozen runtime source')
    apks=list((ROOT/'app/build/outputs/apk').rglob('*.apk'))
    if len(apks)!=1:fail('expected one intended APK, got '+repr(apks))
    apk=apks[0]; final=ROOT/APK_NAME
    shutil.copy2(apk,final)
    if not final.is_file() or final.stat().st_size<1_000_000:fail('Android APK missing/too small')
    status=OUT/'26904_COMPILER_STATUS.txt'
    status.write_text('REAL PINNED GLSL COMPILE: PASS (26904 modified shaders)\n'
        'REAL SPIR-V VALIDATION: PASS\n'
        'REAL ANDROID Gradle :app:assembleDebug: PASS (includes Kotlin/Javac/native ABIs)\n'
        'RUNTIME SOURCE INVARIANCE: PASS\n'
        f'APK {APK_NAME} SHA256 {sha(final)}\n')
    (OUT/'26904_APK.sha256').write_text(sha(final)+'  '+APK_NAME+'\n')
    (OUT/'26904_VERSION.txt').write_text('VERSION_NAME='+VERSION_NAME+'\nVERSION_BUILD='+VERSION+'\n')
    (OUT/'26904_ACTUAL_EXECUTED_BUILDER.sha256').write_text(sha(ROOT/'build_26904_incremental.py')+'  build_26904_incremental.py\n')
    (OUT/'26904_ACTIONS_IDENTITY.txt').write_text('git_sha='+os.getenv('GITHUB_SHA','local')+'\ngithub_run_id='+os.getenv('GITHUB_RUN_ID','local')+'\ngithub_ref='+os.getenv('GITHUB_REF','local')+'\n')
    tarpath=OUT/'26904_candidate_app_source.tar.gz'
    with tarfile.open(tarpath,'w:gz',compresslevel=1) as tar:
        for p in sorted(expected):
            file=ROOT/p
            ti=tar.gettarinfo(str(file),arcname=p)
            ti.uid=ti.gid=0;ti.uname=ti.gname='';ti.mtime=0
            with file.open('rb') as src:tar.addfile(ti,src)
    (OUT/'26904_candidate_app_source.tar.gz.sha256').write_text(sha(tarpath)+'  26904_candidate_app_source.tar.gz\n')
    print('PASS one APK source invariance & concise 26904 standalone proof bundle',sha(final))


def main():
    actions={'seal':seal_staging,'fetch':fetch,'prepare':prepare,'verify-compiled':verify_compiled,'finalize':finalize}
    p=argparse.ArgumentParser();p.add_argument('command',choices=list(actions));a=p.parse_args()
    actions[a.command]()
if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('ERROR',str(exc),file=sys.stderr)
        sys.exit(1)
