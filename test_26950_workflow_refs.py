#!/usr/bin/env python3
"""Exact successful 26949 historical prefix + full 26950 executable/Android graph."""
import pathlib,hashlib,re,sys
from build_26950_incremental import R,fail
previous=R/'.github/workflows/build-26949-change-aware.yml';actual=R/'.github/workflows/build-26950-change-aware.yml'
if not previous.is_file() or hashlib.sha256(previous.read_bytes()).hexdigest()!='2e269b44b79b0c9c7e5030bf64232c49083944fb04c68d926d4315f67be9a58a':fail('26949 successful workflow changed')
old=previous.read_text();new=actual.read_text()
marker='      - name: Fetch SUCCESSFUL 26948 Actions run'
if old.count(marker)!=1:fail('26949 historical workflow anchor missing')
prefix=old[:old.index(marker)].replace('name: Photon 26949 - B OFF original RAWR AMaZE and two-pass FCC restoration','name: Photon 26950 - B OFF and B Night original RAWR HDRQ strength 11').replace('      - TRIGGER_26949.txt','      - TRIGGER_26950.txt')
if not new.startswith(prefix):fail('successful 26949 historical step/command graph changed')
if new.count('actions/upload-artifact@v4')!=1 or new.count('./gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace')!=1:fail('must compile/package exactly once')
if 'TRIGGER_26950.txt' not in new.split('jobs:',1)[0] or 'TRIGGER_26949.txt' in new.split('jobs:',1)[0]:fail('stale trigger')
if 'compile_26949_shaders.sh' in new:fail('26949 live validator collision still present')
if new.count('python3 -S test_26950_source.py --preseed')!=1 or new.index('python3 -S test_26950_source.py --preseed')>new.index('build_26950_incremental.py fetch'):fail('vendor-free source preflight not executed before authority reconstruction')
for ref in ('replay_26950_inherited_26949_glsl.py','replay_26950_inherited_26948_glsl.py','replay_26950_inherited_26943_glsl.py','replay_26950_inherited_26944_glsl.py','compile_26950_shaders.sh','compile_26950_sdr_shaders.sh','test_26950_highlight.py --live','test_26950_source.py --live','test_26950_math.py --live','test_26950_patch_proof.py --live',
 'build_26950_incremental.py fetch','build_26950_incremental.py prepare','build_26950_incremental.py verify-compiled','build_26950_incremental.py finalize','test_26931_native_integrity.py --cmake','verify_26906_native_cache.py postflight'):
 if ref not in new:fail('missing mandatory new/old regression '+ref)
listed=(R/'26950_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines()
if len(listed)!=len(set(listed)):fail('duplicate executable manifest')
invoked=set(re.findall(r'\b(?:python3\s+-S\s+|bash\s+|\./)([\w.-]+\.(?:py|sh))\b',new))
if set(listed)!=invoked:fail('missing/unused executable list '+repr(sorted(invoked-set(listed)))+' '+repr(sorted(set(listed)-invoked)))
if '--on-actions' in sys.argv:
 for p in listed:
  if not (R/p).is_file():fail('missing actual executable '+p)
# 26904 V2 historical SPIR-V optimizer failure reproduced in 26950 V3.
# The real optimizer rejects a separated --target-env argument, treating the
# value as an additional input filename. The correct format is --target-env=NAME.
# Unlike a file-seal alone, this preseed check rejects even a newly sealed
# but semantically invalid compiler command BEFORE fetching a 26949 artifact.
def require_spirv_cli(src, env, label):
    cmds=[l.strip() for l in src.splitlines() if re.match(r'^\s*spirv-opt\s+',l)]
    calls=[l for l in cmds if '--version' not in l]
    if len(calls)!=1:fail('missing/duplicate SPIR-V optimizer call '+label)
    cmd=calls[0]
    expected=r'^spirv-opt\s+--target-env='+re.escape(env)+r'\s+-O\s+\S+\s+-o\s+\S+$'
    if not re.fullmatch(expected,cmd):fail('26904 V2 optimizer CLI regression or obsolete target env '+label+' '+cmd)
    if not re.search(r'^\s*spirv-val\s+--target-env\s+'+re.escape(env)+r'\s+',src,re.M):
        fail('SPIR-V validator gate absent '+label)
for filename,env in (('compile_26950_shaders.sh','vulkan1.1'),('compile_26950_sdr_shaders.sh','opengl4.5')):
    source=(R/filename).read_text()
    require_spirv_cli(source,env,filename)
    # Negative: model the exact broken 26950 V3 command even if future
    # metadata or SHA files are re-sealed to conceal this regression.
    mutated=source.replace('spirv-opt --target-env='+env,'spirv-opt --target-env '+env,1)
    if mutated==source:fail('could not construct historical 26904 V2 negative '+filename)
    try:require_spirv_cli(mutated,env,filename+' NEGATIVE')
    except RuntimeError:pass
    else:fail('26904 V2 optimizer CLI negative unexpectedly accepted '+filename)
    import subprocess
    syntax=subprocess.run(['bash','-n',str(R/filename)],capture_output=True,text=True)
    if syntax.returncode:fail('current compiler bash syntax invalid '+filename+' '+syntax.stderr)
print('PASS 26950 both real SPIR-V optimizer CLI forms; historic 26904 V2 positional failures rejected, bash syntax')
print('PASS exact successful 26949 workflow historical prefix, no stale refs, real 26950 GLSL/NDK/Kotlin/Java/full assemble')
