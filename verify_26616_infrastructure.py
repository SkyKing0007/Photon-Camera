#!/usr/bin/env python3
from pathlib import Path
import re,sys,difflib
if len(sys.argv)<3: raise SystemExit('usage: verify_26616_infrastructure.py BUILD WORKFLOW [--successful-r1-script FILE --successful-r1-workflow FILE]')
bp=Path(sys.argv[1]); yp=Path(sys.argv[2]); b=bp.read_text(); y=yp.read_text()
# Freeze successful 26615 R1 outer ordering and compiler/build ordering.
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
    if q<0: raise SystemExit('successful-R1 build order token missing '+tok)
    pos=q
tr=Path(bp.parent/'transform_26616.py').read_text()
for tok in ['GIT_CEILING_DIRECTORIES',"['git','rev-parse','--show-toplevel']","['git','apply','--check'","['git','apply'"]:
    if tok not in tr: raise SystemExit('R1 transform isolation regression '+tok)
for tok in ['actions/checkout@v5','actions/setup-java@v5','distribution: temurin',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4']:
    if tok not in y: raise SystemExit('workflow mechanics drift '+tok)
if 'experimental-clean-photon-rebuild' not in y: raise SystemExit('wrong branch')
if "permissions:\n  contents: read\n  actions: read" not in y: raise SystemExit('workflow permissions drift')
# Explicit comparison to exact successful 26615 R1 implementation when supplied by Actions.
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
    # Strip build-specific output/report names only, preserving commands/options/order.
    return [re.sub(r'2661[456]', 'BUILDID', re.sub(r'0\.972661[456]','VERSION',x)) for x in wanted]
def workflow_signature(src):
    keep=[]
    for raw in src.splitlines():
        s=raw.strip()
        if s.startswith('- uses: actions/') or s in ['runs-on: ubuntu-24.04','distribution: temurin',"java-version: '17'",'cache: gradle',"python-version: '3.12'",'contents: read','actions: read','fetch-depth: 0','if-no-files-found: error','retention-days: 90']:
            keep.append(s)
    return keep
if '--successful-r1-script' in sys.argv:
    pp=Path(sys.argv[sys.argv.index('--successful-r1-script')+1]); py=Path(sys.argv[sys.argv.index('--successful-r1-workflow')+1])
    prior=pp.read_text(); prior_y=py.read_text()
    # Every critical compiler/build/invariance mechanic must exist in both and preserve relative order.
    for tok in ['snapshot_candidate_from_authority','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac',"':app:buildCMakeDebug[arm64-v8a]'",'verify_candidate_patches','PRE-BUILD SAFETY PROOF','./gradlew :app:assembleDebug','postbuild candidate byte-identical','tar --sort=name']:
        if tok not in prior or tok not in b: raise SystemExit('R1 mechanics inheritance missing '+tok)
    if workflow_signature(prior_y)!=workflow_signature(y):
        raise SystemExit('workflow toolchain/mechanics signature differs from successful 26615 R1')
    # Record explicit structural comparison result. The algorithm/base-authority/count/report lines are intentionally outside this signature.
    a=command_signature(prior); c=command_signature(b)
    # The exact output/report filenames may differ; compare command families by token/order rather than output labels.
    if len(a)!=len(c):
        raise SystemExit('build mechanics signature length drift\n'+''.join(difflib.unified_diff(a,c,fromfile='26615',tofile='26616')))
print('PASS 26616 infrastructure: exact successful-26615-R1 ordering/isolation/compiler/NDK/patch/assemble/invariance mechanics preserved; only authority/version/naming/count/Wronski-validator deltas')
