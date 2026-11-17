#!/usr/bin/env python3
"""Keep entire successful 26948 historical workflow prefix unchanged and append full 26949 compiler graph."""
import pathlib,hashlib,re,sys
R=pathlib.Path(__file__).resolve().parent
P=R/'.github/workflows/build-26948-change-aware.yml'
W=R/'.github/workflows/build-26949-change-aware.yml'
previous='b5e17631bd2af89d73b984a9124cd840d33494a1abe80cd5fbd464bccd637fc5'
if not P.exists() or hashlib.sha256(P.read_bytes()).hexdigest()!=previous:
 raise SystemExit('26949 BLOCKED: successful 26948 workflow changed in checkout')
a=P.read_text();b=W.read_text()
orig=a[:a.index('      - name: Fetch successful 26947 Actions run')]
orig=orig.replace('name: Photon 26948 - B-only SDR highlight fidelity and guarded flicker control','name: Photon 26949 - B OFF original RAWR AMaZE and two-pass FCC restoration')
orig=orig.replace('      - TRIGGER_26948.txt','      - TRIGGER_26949.txt')
assert b.startswith(orig),'original 26948 historical workflow graph was altered'
assert 'bash compile_26948_shaders.sh' not in b, 'old 26948 --live source-only gate cannot be executed on a 26949 live candidate'
assert b.count('python3 -S replay_26949_inherited_26948_glsl.py\n')==1
assert b.count('python3 -S replay_26949_inherited_26948_glsl.py --preflight')==1
assert b.count('actions/upload-artifact@v4')==1
assert b.count('./gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace')==1
assert b.count('build_26949_incremental.py prepare')==1
for s in ['verify_26904_v3_safety.py','verify_26904_v2_safety.py','test_26903_v3_archive_receipt.py',
 'test_26931_native_integrity.py --native','test_26931_native_integrity.py --cmake','test_26931_native_integrity.py --apk',
 'verify_26906_native_cache.py preflight','verify_26906_native_cache.py postflight',
 'compile_26939_shaders.sh','compile_26941_shaders.sh','compile_26942_shaders.sh','compile_26943_shaders.sh','compile_26944_shaders.sh','replay_26949_inherited_26948_glsl.py','compile_26949_shaders.sh',
 'test_26948_v2_shader_compat.py --payload --on-actions','test_26949_restore.py --payload','test_26949_restore.py --live','test_26949_patch_proof.py --live','test_26949_sealed_negatives.py',
 'build_26949_incremental.py fetch','build_26949_incremental.py verify-compiled','build_26949_incremental.py finalize']:
 assert s in b,'required historical/current gate missing '+s
assert 'TRIGGER_26949.txt' in b.split('jobs:',1)[0]
assert 'TRIGGER_26948.txt' not in b.split('jobs:',1)[0]
# Audit ALL executable references (not merely a selected subset).
manifest=R/'26949_EXPECTED_ACTION_EXECUTABLES.txt'
listed=[x.strip() for x in manifest.read_text().splitlines() if x.strip() and not x.lstrip().startswith('#')]
assert len(listed)==len(set(listed))
assert all(re.fullmatch(r'[A-Za-z0-9_.-]+\.(?:py|sh)',p) for p in listed)
invoked=set(re.findall(r'\b(?:python3\s+-S\s+|bash\s+|\./)([\w.-]+\.(?:py|sh))\b',b))
assert invoked==set(listed),('missing/obsolete/unused executable references',sorted(invoked-set(listed)),sorted(set(listed)-invoked))
if '--on-actions' in sys.argv:
 missing=[p for p in listed if not (R/p).is_file()]
 assert not missing,('missing executable in live checkout',missing)
assert b.count('runs-on: ubuntu-24.04')==1
assert 'timeout-minutes: 120' in b
print('PASS successful 26948 historical prefix IDENTICAL; full inherited real GLSL via sealed 26948 payload; exact executable references; real native/assemble')
