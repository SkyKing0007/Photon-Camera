#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, re

SUCCESS_26598_SCRIPT_BLOB='1bfc9d6daa6707e2c8e5482f3837d7a7fccd658d'
SUCCESS_26598_WORKFLOW_BLOB='ea4aba2a156b740b6f6a90af7e2a466b003e993a'
GOLDEN_26593_SCRIPT_SHA='111d59850aa4a0dccef482bcf68ce7b9d93e76d99729fc2de810ff91b97f160f'
GOLDEN_26593_WORKFLOW_SHA='89083ed8892f18f93e50b35679beeba114674cacfcb4ad3ff79078ec130f43fc'

def fail(m): raise SystemExit('FAIL: '+m)
def H(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git_blob(p):
    b=Path(p).read_bytes(); return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()

def check_order(s,label):
    tail=s[s.rfind('\nverify_package\n'):]
    top=['verify_package','verify_scope','obtain_authority','make_candidate','verify_shaders','install_and_build']
    pos=[]
    for k in top:
        i=tail.find(k)
        if i<0: fail(label+' missing top-level mechanics token '+k)
        pos.append(i)
    if pos!=sorted(pos): fail(label+' top-level mechanics order changed')
    a=s.index('install_and_build(){'); b=s.index('\n}\nverify_package',a); body=s[a:b]
    keys=[
      'snapshot_candidate_from_authority "$BASE" "$ROOT" "$LIVE_CANON"',
      './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',
      "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",
      'verify_candidate_patches',
      'PRE-BUILD SAFETY PROOF PASSED',
      './gradlew :app:assembleDebug --stacktrace',
      'snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"',
      'candidate_app_source.tar.gz']
    pos=[]
    for k in keys:
        i=body.find(k)
        if i<0: fail(label+' missing install/build mechanics token '+k)
        pos.append(i)
    if pos!=sorted(pos): fail(label+' install/build mechanics order changed')
    return tuple(keys)

def workflow_shape(w,label):
    keys=['actions/checkout@v5','actions/setup-java@v5','actions/setup-python@v5',
          'sha256sum -c V1_','bash -n build_','python3 -S - <<\'PY\'',
          'bash build_','actions/upload-artifact@v4']
    pos=[]
    for k in keys:
        i=w.find(k)
        if i<0: fail(label+' missing workflow mechanics token '+k)
        pos.append(i)
    if pos!=sorted(pos): fail(label+' workflow mechanics order changed')
    return tuple(keys)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('build_script'); ap.add_argument('workflow')
    ap.add_argument('--success-26598-script'); ap.add_argument('--success-26598-workflow')
    ap.add_argument('--golden-26593-script'); ap.add_argument('--golden-26593-workflow'); ns=ap.parse_args()
    s=Path(ns.build_script).read_text(); w=Path(ns.workflow).read_text()
    for t in [
      'BASE_SUCCESS_COMMIT="4127027f5f862513034a22d4de17ad0b1575bae8"',
      'BASE_RUN_ID="33941164383"','BASE_JOB_ID="101238751503"','BASE_ARTIFACT_ID="9961914943"',
      'BASE_ARTIFACT_SHA="eeef32156285d100b14854797b37e85f35d9fd0eb55629bbc713cbcce307b2ce"',
      'BASE_TAR_SHA="a6f3287393a85b35d409ad7d17200715929b0e4646769f48e8fec0773160c7be"',
      'MECHANICS_GOLDEN_COMMIT="7c485416a8f41f9bf8a834bf4282e7c2318fa9fb"',
      'GLSLANG_VERSION="16.5.0"',
      'BACKUP_BRANCH="backup-26598-before-26599-hdr-tone-ownership"',
      'BACKUP_SHA="4127027f5f862513034a22d4de17ad0b1575bae8"',
      'GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"']:
        if t not in s: fail('authority/mechanics pin '+t)
    current_sig=check_order(s,'26599')
    blocks=re.findall(r"<<'PY'\n(.*?)\nPY",s,re.S)
    if len(blocks)!=5: fail(f'embedded Python heredoc count {len(blocks)} != 5')
    for i,block in enumerate(blocks,1):
        try: compile(block,f'{Path(ns.build_script).name}:heredoc{i}','exec')
        except SyntaxError as e: fail(f'embedded Python heredoc syntax {i}: {e.msg} line={e.lineno}')
    if "names.append('V1_26599_HANDOFF_HASHES.sha256')\nprint('\\n'.join(sorted(names)))" not in s:
        fail('escaped expected-scope join missing')
    workflow_shape(w,'26599')
    for t in ['build-26599-v1-effective-short-shared-hdr-tone.yml',
              'photon-26599-v1-effective-short-shared-hdr-tone',
              'Build exact 26599 candidate from successful compiled 26598 authority']:
        if t not in w: fail('26599 workflow identity/order token '+t)
    if ns.success_26598_script:
        if git_blob(ns.success_26598_script)!=SUCCESS_26598_SCRIPT_BLOB: fail('successful-26598 build script blob')
        prior=Path(ns.success_26598_script).read_text(); prior_sig=check_order(prior,'26598')
        if prior_sig!=current_sig: fail('core compiler/build mechanics signature differs from successful 26598')
        stable=['snapshot_candidate_from_authority','verify_candidate_patches','resolve_glslang_compiler',
                '--local-prebuild',
                ':app:compileDebugKotlin :app:compileDebugJavaWithJavac',
                ':app:buildCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug',
                "tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner"]
        for t in stable:
            if t not in prior or t not in s: fail('successful-26598 stable mechanics token '+t)
    if ns.success_26598_workflow:
        if git_blob(ns.success_26598_workflow)!=SUCCESS_26598_WORKFLOW_BLOB: fail('successful-26598 workflow blob')
        priorw=Path(ns.success_26598_workflow).read_text(); workflow_shape(priorw,'26598')
    pairs=[(ns.golden_26593_script,GOLDEN_26593_SCRIPT_SHA,'successful-26593 build script'),
           (ns.golden_26593_workflow,GOLDEN_26593_WORKFLOW_SHA,'successful-26593 workflow')]
    for path,want,label in pairs:
        if path and H(path)!=want: fail(label+' SHA')
    print('PASS exact successful-26598 runtime/mechanics pins + successful-26593 compiler/build ordering inherited')
    if ns.success_26598_script and ns.success_26598_workflow:
        print('PASS exact successful-26598 build/workflow blob audit; mechanics delta limited to 26599 V1 identity/base/eight-file scope/backup/effective-SHORT-tone regressions')
    else:
        print('PASS prior successful-26598 blob pins packaged; exact-source diff replay deferred to Actions')
if __name__=='__main__': main()
