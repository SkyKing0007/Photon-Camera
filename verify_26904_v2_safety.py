#!/usr/bin/env python3
"""26904 V2: fail-closed exactly two optimizer CLI fixes on top of successful 26904 V1 upload.

This is a NEW workflow, not the old 17-stage release runner; it does not edit runtime source.
"""
from pathlib import Path
import hashlib, os, shlex, subprocess, sys
R=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(x,msg):
    if not x:raise AssertionError('26904 V2 BLOCKED: '+msg)

ORIGINAL_SHA={'build_26904_incremental.py': '2c0d6edb0a70f1545713a767a5522b5744c382de915fa756e3ab280315add42d', 'compile_26904_shaders.sh': 'f99ec139b951f1c095b3212fc2f789ad1248c474b5446f913d2d3f5d5adcb4a8', '26904_STAGE1_PATHS.txt': '4cc22bca8ef0ea689d0175278803fe4ddb59146fcae7be4ae88febeb5911d193', '26904_HANDOFF_HASHES.sha256': '0a958b227487865ea43fa93353fa5d79c1d5b623047fb448a63ea21465a566e1', 'test_26904_changeaware.py': 'ba1cec8a591b2f29545a01620c32eae60124b733e51379df4037147ef842622e', '.github/workflows/build-26904-change-aware.yml': '092e539eee27eb4100aa86652643476561a2325f8644882da402fa92eaebaa31', 'TRIGGER_26904.txt': '944755e307f75173a45e19a292a6cdb49f4d2aca6330b6f85a225ae0d4b0ab9f'}
EXPECTED_TRIGGER=b'RUN_26904_V2_CHANGE_AWARE_SPIRV_OPT_CORRECT_CLI\n'
V1_WORKFLOW='.github/workflows/build-26904-change-aware.yml'
V2_WORKFLOW='.github/workflows/build-26904-v2-change-aware.yml'

def expect_v2_workflow(old):
    need(old.count('run: bash compile_26904_shaders.sh')==1,'old workflow compiler entry changed')
    need(old.count('      - TRIGGER_26904.txt')==1,'old V1 trigger filter changed')
    need('      - name: Verify standalone uploaded package before touching runtime\n' in old,'old first validation step moved')
    return (old.replace('Photon 26904 - independent change-aware Android build',
       'Photon 26904 V2 - independent change-aware Android build (SPIRV optimizer CLI)',1)
       .replace('      - TRIGGER_26904.txt','      - TRIGGER_26904_V2.txt',1)
       .replace('      - name: Verify standalone uploaded package before touching runtime\n',
         '      - name: Verify corrected SPIR-V optimizer CLI and V2 package\n'
         '        run: python3 -S verify_26904_v2_safety.py\n'
         '      - name: Verify standalone uploaded package before touching runtime\n',1)
       .replace('run: bash compile_26904_shaders.sh','run: bash compile_26904_shaders_v2.sh',1))

def run():
    if os.getenv('GITHUB_REPOSITORY'):
        need(os.environ['GITHUB_REPOSITORY']=='SkyKing0007/Photon-Camera','wrong repository')
        need(os.environ.get('GITHUB_REF_NAME')=='experimental-clean-photon-rebuild','wrong branch')
    for p,h in ORIGINAL_SHA.items():
        f=R/p
        need(f.is_file() and sha(f)==h,'changed original immutable 26904 file: '+p)
    need((R/'TRIGGER_26904.txt').read_bytes()==b'RUN_26904_CHANGE_AWARE_BORDER_AND_NIGHT_B_V1\n',
        'old exact-byte trigger altered')
    need((R/'TRIGGER_26904_V2.txt').read_bytes()==EXPECTED_TRIGGER,
        'V2 trigger bytes mismatch')
    paths=(R/'26904_V2_STAGE1_PATHS.txt').read_text().splitlines()
    need(paths==['compile_26904_shaders_v2.sh','verify_26904_v2_safety.py',
       '26904_V2_HANDOFF_HASHES.sha256','26904_V2_STAGE1_PATHS.txt'],
       'V2 exact Stage1 upload set changed')
    stamps={}
    for line in (R/'26904_V2_HANDOFF_HASHES.sha256').read_text().splitlines():
        h,p=line.split('  ',1)
        need(p not in stamps,'duplicate staged path')
        stamps[p]=h
    allowed=set(paths)-{'26904_V2_HANDOFF_HASHES.sha256'}
    allowed|={V2_WORKFLOW,'TRIGGER_26904_V2.txt'}
    need(set(stamps)==allowed,'V2 handoff seal scope changed')
    for p,h in stamps.items():
        need((R/p).is_file() and sha(R/p)==h,'tampered V2 uploaded file '+p)
    original=(R/'compile_26904_shaders.sh').read_text()
    repaired=(R/'compile_26904_shaders_v2.sh').read_text()
    need(original.count('spirv-opt --target-env opengl4.5')==1,
         'the actual first 26904 SPIRV optimizer regression missing')
    need(original.count('spirv-opt --target-env vulkan1.1')==1,
         'the actual second wrong optimizer invocation missing')
    need(original.count('spirv-val --target-env opengl4.5')==2
         and original.count('spirv-val --target-env vulkan1.1')==2,
         'original valid validator call changed')
    exact=(original.replace('spirv-opt --target-env opengl4.5','spirv-opt --target-env=opengl4.5')
                   .replace('spirv-opt --target-env vulkan1.1','spirv-opt --target-env=vulkan1.1'))
    need(repaired==exact,'V2 shader script changed anything besides two optimizer arguments')
    # Reproduce the original actual CLI parsing error against both source invocations.
    # spirv-opt v2025 accepts --target-env=<env>, unlike spirv-val's separated form.
    def opt_source_tokens(script):
        return [shlex.split(line.strip().replace('$TOOLS/','/tmp/tools/'))
                for line in script.splitlines() if line.lstrip().startswith('spirv-opt --target-env')]
    def input_count(argv):
        # The historical bug made opengl4.5/vulkan1.1 an extra positional SPV input.
        inputs=[]; skip=False
        for a in argv[1:]:
            if skip:skip=False;continue
            if a=='-o':skip=True;continue
            if a.startswith('-'):continue
            inputs.append(a)
        return inputs
    wrong=opt_source_tokens(original);fixed=opt_source_tokens(repaired)
    need(len(wrong)==len(fixed)==2,'optimizer command count changed')
    for i,(a,b) in enumerate(zip(wrong,fixed)):
        need(len(input_count(a))==2 and len(input_count(b))==1,
             'historical wrong-CLI/positive fix not reproduced for invocation '+str(i))
        need(any(x.startswith('--target-env=') for x in b),
             'optimizer target syntax invalid')
        need(any(x=='-O' for x in b) and '-o' in b,
             'optimizer compile output argument changed')
    old_w=(R/V1_WORKFLOW).read_text();new_w=(R/V2_WORKFLOW).read_text()
    need(new_w==expect_v2_workflow(old_w),
         'V2 workflow not exact V1 with single added guard, trigger and optimizer script swap')
    need(new_w.count('      - TRIGGER_26904_V2.txt')==1
         and '      - TRIGGER_26904.txt' not in new_w,
         'V2 workflow triggers old build')
    # Test original current-only builder too; it seals original first handoff completely.
    subprocess.run([sys.executable,'-S',str(R/'build_26904_incremental.py'),'seal'],cwd=R,check=True)
    subprocess.run(['bash','-n',str(R/'compile_26904_shaders_v2.sh')],check=True)
    print('PASS exact 26904 V1 successful-upload source preserved, V2 stage manifest, two real CLI failure reproductions and corrections, independent trigger')
if __name__=='__main__':
    try:run()
    except Exception as exc:
        print('26904 V2 FAIL:',exc,file=sys.stderr);sys.exit(1)
