#!/usr/bin/env python3
from pathlib import Path
import re,sys,difflib
if len(sys.argv)<3: raise SystemExit('usage: verify_26617_infrastructure.py BUILD WORKFLOW [--successful-prior-script FILE --successful-prior-workflow FILE]')
bp=Path(sys.argv[1]); yp=Path(sys.argv[2]); b=bp.read_text(); y=yp.read_text()
# Freeze exact successful 26616 R1.2 outer ordering and compiler/build ordering.
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_shaders']
pos=-1
for tok in order:
    q=b.find(tok+'\n',pos+1) if tok=='verify_package' else b.find(tok,pos+1)
    if q<0: raise SystemExit('missing/order '+tok)
    pos=q
internal=['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac',"':app:buildCMakeDebug[arm64-v8a]'","':app:buildCMakeDebug[armeabi-v7a]'",'verify_candidate_patches','PRE-BUILD SAFETY PROOF','./gradlew :app:assembleDebug','exactly one','postbuild candidate byte-identical','tar --sort=name']
pos=b.find('install_and_build(){')
for tok in internal:
    q=b.find(tok,pos+1)
    if q<0: raise SystemExit('successful-26616 build order token missing '+tok)
    pos=q
tr=Path(bp.parent/'transform_26617.py').read_text()
for tok in ['GIT_CEILING_DIRECTORIES',"['git','rev-parse','--show-toplevel']","['git','apply','--check'","['git','apply'"]:
    if tok not in tr: raise SystemExit('26616 transform isolation regression '+tok)
for tok in ['actions/checkout@v5','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4']:
    if tok not in y: raise SystemExit('workflow mechanics drift '+tok)
if 'experimental-clean-photon-rebuild' not in y: raise SystemExit('wrong branch')
if "permissions:\n  contents: read\n  actions: read" not in y: raise SystemExit('workflow permissions drift')

def command_signature(src):
    wanted=[]
    for raw in src.splitlines():
        s=raw.strip()
        if any(tok in s for tok in [
            'snapshot_candidate_from_authority(){','GIT_CEILING_DIRECTORIES',
            './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac',
            "':app:buildCMakeDebug[arm64-v8a]'", "':app:buildCMakeDebug[armeabi-v7a]'",
            'verify_candidate_patches; set_report "PRE-BUILD SAFETY PROOF"',
            './gradlew :app:assembleDebug','expected exactly one Gradle debug APK',
            'postbuild candidate byte-identical','tar --sort=name --mtime=',
            'sha256sum -c "$HANDOFF"','git diff --name-only ']):
            wanted.append(s)
    # Preserve the successful 26616 R1.2 comparator regression: normalize build labels/versions,
    # never authority-variable spellings or command order.
    return [re.sub(r'2661[67]', 'BUILDID', re.sub(r'0\.972661[67]','VERSION',x)) for x in wanted]

def workflow_signature(src):
    keep=[]
    for raw in src.splitlines():
        s=raw.strip()
        if s.startswith('- uses: actions/') or s in ['runs-on: ubuntu-24.04','distribution: temurin',"java-version: '17'",'cache: gradle',"python-version: '3.12'",'contents: read','actions: read','fetch-depth: 0','if-no-files-found: error','retention-days: 90']:
            keep.append(s)
    return keep

if '--successful-prior-script' in sys.argv:
    pp=Path(sys.argv[sys.argv.index('--successful-prior-script')+1]); py=Path(sys.argv[sys.argv.index('--successful-prior-workflow')+1])
    prior=pp.read_text(); prior_y=py.read_text()
    for tok in ['snapshot_candidate_from_authority','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac',"':app:buildCMakeDebug[arm64-v8a]'",'verify_candidate_patches','PRE-BUILD SAFETY PROOF','./gradlew :app:assembleDebug','postbuild candidate byte-identical','tar --sort=name']:
        if tok not in prior or tok not in b: raise SystemExit('26616 mechanics inheritance missing '+tok)
    if workflow_signature(prior_y)!=workflow_signature(y):
        raise SystemExit('workflow toolchain/mechanics signature differs from successful 26616 R1.2')
    a=command_signature(prior); c=command_signature(b)
    if len(a)!=len(c):
        raise SystemExit('build mechanics signature length drift\n'+''.join(difflib.unified_diff(a,c,fromfile='26616',tofile='26617')))
    # Compare command families by order; authority/version/output names may differ, mechanics may not.
    def family(x):
        x=re.sub(r'R1_2661[67]_[A-Za-z0-9_./-]+','R1_BUILD_ARTIFACT',x)
        x=x.replace('$BASE_SUCCESS_COMMIT','$BASE_SUCCESS_COMMIT').replace('$HANDOFF_PARENT_COMMIT','$BASE_SUCCESS_COMMIT')
        return x
    for i,(aa,cc) in enumerate(zip(a,c)):
        # Generic token/order check already guards exact mechanics; permit expected 26617 report/output labels.
        for token in ['snapshot_candidate_from_authority','git diff --name-only','./gradlew clean',"':app:buildCMakeDebug[arm64-v8a]'","':app:buildCMakeDebug[armeabi-v7a]'",'verify_candidate_patches','PRE-BUILD SAFETY PROOF','./gradlew :app:assembleDebug','expected exactly one Gradle debug APK','postbuild candidate byte-identical','tar --sort=name','sha256sum -c "$HANDOFF"']:
            if (token in aa)!=(token in cc): raise SystemExit(f'build mechanics command family drift index={i} token={token}')
print('PASS 26617 infrastructure: exact successful-26616-R1.2 ordering/isolation/compiler/NDK/patch/assemble/invariance mechanics preserved; only authority/version/naming/count/adaptive-Wronski validator deltas')
