#!/usr/bin/env python3
"""Enforce exact successful 26949 inherited Actions graph + 26951 references and real compiler order."""
import hashlib,pathlib,re,sys,subprocess
from build_26951_incremental import R,fail,STAGE1_FILES
SHA_26949_WORKFLOW='2e269b44b79b0c9c7e5030bf64232c49083944fb04c68d926d4315f67be9a58a'
reference=R/'26949_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml'
if not reference.is_file() or hashlib.sha256(reference.read_bytes()).hexdigest()!=SHA_26949_WORKFLOW:fail('successful 26949 actual executed workflow reference missing/tampered')
original=reference.read_text()
actual=R/'.github/workflows/build-26951-change-aware.yml'
if not actual.is_file():fail('26951 Actions workflow missing')
new=actual.read_text()
name='name: Photon 26949 - B OFF original RAWR AMaZE and two-pass FCC restoration'
marker='      - name: Fetch SUCCESSFUL 26948 Actions run'
if original.count(marker)!=1 or original.count(name)!=1:fail('successful 26949 historical workflow anchor missing')
prefix=original[:original.index(marker)].replace(name,'name: Photon 26951 - successful 26949 RAWR HDRQ compatibility and matched SDR').replace('      - TRIGGER_26949.txt','      - TRIGGER_26951.txt')
if not new.startswith(prefix):fail('successful 26949 historical 26904-26949 executor graph changed')
if '--on-actions' in sys.argv:
 original_repo=R/'.github/workflows/build-26949-change-aware.yml'
 if not original_repo.is_file() or original_repo.read_bytes()!=reference.read_bytes():fail('successful 26949 workflow in repository differs from its published executed SHA')
if new.count('actions/upload-artifact@v4')!=1 or new.count('./gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace')!=1:fail('must have ONE real compile and artifact')
header=new.split('jobs:',1)[0]
if 'TRIGGER_26951.txt' not in header or 'TRIGGER_26949.txt' in header or 'TRIGGER_26950.txt' in header:fail('new build trigger stale or wrong')
if re.search(r'\b(?:compile_26949_shaders\.sh|compile_26943_shaders\.sh|compile_26944_shaders\.sh)\b',new[len(prefix):]):fail('unwrapped historical GLSL script conflicts with current HDRQ ABI')
if 'build_26950_incremental.py' in new or 'compile_26950_shaders.sh' in new or 'replay_26950_' in new:fail('failed 26950 direct executable still referenced')
for ref in ('test_26951_source.py --preseed','test_26951_source.py --payload','test_26951_descriptor_abi.py --payload',
 'test_26951_source.py --live','test_26951_math.py --live','test_26951_descriptor_abi.py --live',
 'test_26951_highlight.py --live','test_26951_patch_proof.py --live','test_26951_sealed_negatives.py',
 'replay_26951_inherited_26949_glsl.py --preflight','replay_26951_inherited_26948_glsl.py --preflight',
 'replay_26951_inherited_26943_glsl.py','replay_26951_inherited_26944_glsl.py',
 'compile_26951_shaders.sh','compile_26951_sdr_shaders.sh',
 'build_26951_incremental.py fetch','build_26951_incremental.py prepare','build_26951_incremental.py verify-compiled','build_26951_incremental.py finalize',
 'test_26931_native_integrity.py --cmake','verify_26906_native_cache.py postflight',
 'test_26903_modes.py .', 'actions/cache/restore@v4','actions/cache/save@v4',
 'compile_26904_shaders_v2.sh', 'verify_26904_v3_cmake_handoff.py --handoff',
 'prepare_26951_lkr_from_successful_26949.py'):
 if ref not in new:fail('mandatory historical/current executable/check missing '+ref)
if new.index('test_26951_source.py --preseed')>new.index('build_26951_incremental.py fetch'):fail('vendor-free source check must precede artifact fetch')
if new.index('compile_26951_sdr_shaders.sh')>new.index('build_26951_incremental.py verify-compiled'):fail('real shader compile occurs too late')
if new.index('build_26951_incremental.py verify-compiled')>new.index(':app:assembleDebug --stacktrace'):fail('real prebuild proof occurs too late')
if new.index('build_26951_incremental.py finalize')<new.index(':app:assembleDebug --stacktrace'):fail('finalization preceding real compile')
# Complete *actual* executable list. Every invocation must have a file in
# checkout; no listed script can be orphaned. Exact list is included in seal.
invoked=set(re.findall(r'\b(?:python3\s+-S\s+|bash\s+|\./)([\w.-]+\.(?:py|sh))\b',new))
listed=(R/'26951_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines()
if len(listed)!=len(set(listed)) or set(listed)!=invoked:fail('stale/missing/unused workflow script reference '+repr(sorted(invoked-set(listed)))+' '+repr(sorted(set(listed)-invoked)))
if '--on-actions' in sys.argv:
 for name in listed:
  if not (R/name).is_file():fail('missing actual runner executable '+name)
# Original 26904 failure regressions: positional --target-env breaks spirv-opt;
# exact deployed CLI must pass equals-sign binding before any build is triggered.
def check_optimizer(file,env):
 src=(R/file).read_text()
 if not re.search(r'^\s*spirv-val\s+--target-env\s+'+re.escape(env)+r'\s+',src,re.M):fail('shader validator not present '+file)
 lines=[v.strip() for v in src.splitlines() if re.match(r'^\s*spirv-opt\s+',v) and '--version' not in v]
 if len(lines)!=1:fail('exactly one optimizer call required '+file)
 expected=r'^spirv-opt\s+--target-env='+re.escape(env)+r'\s+-O\s+\S+\s+-o\s+\S+$'
 if not re.fullmatch(expected,lines[0]):fail('26904 V1/V2 SPIR-V optimizer positional argument regression '+file+' '+lines[0])
 return src
for name,env in (('compile_26951_shaders.sh','vulkan1.1'),('compile_26951_sdr_shaders.sh','opengl4.5')):
 src=check_optimizer(name,env)
 mutant=src.replace('spirv-opt --target-env='+env,'spirv-opt --target-env '+env,1)
 if mutant==src or re.search(r'^\s*spirv-opt\s+--target-env='+re.escape(env),mutant,re.M):fail('unable to reproduce exact optimizer negative')
 r=subprocess.run(['bash','-n',str(R/name)],capture_output=True,text=True)
 if r.returncode:fail('bash shell syntax invalid '+name+' '+r.stderr)
print('PASS 26951 exact successful 26949 historical workflow prefix; no missing/unused/stale references, pinned GLSL CLI negatives')
