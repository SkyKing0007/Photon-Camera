#!/usr/bin/env python3
"""26885 ONLY Experiment B Super Res ON; historical white regression on 26884 bytes."""
from pathlib import Path
import sys,hashlib,subprocess
R=Path(__file__).resolve().parent; B=Path(sys.argv[1]);C=Path(sys.argv[2]);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(n):return {k:h for h,k in (r.split('  ',1) for r in (R/n).read_text().splitlines())}
old=manifest('26885_BASE_26884_FULL_APP.sha256');new=manifest('26885_EXPECTED_CANDIDATE_FULL_APP.sha256')
allow=(R/'26885_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert len(old)==2009 and len(new)==2010 and len(allow)==8
assert set(allow)==set(k for k in set(old)|set(new) if old.get(k)!=new.get(k))
assert all(old[k]==new[k] and sha(B/k)==sha(C/k)==old[k] for k in set(old)-set(allow))
assert (C/'app/version.properties').read_text().splitlines()[-2:]==['VERSION_NAME=0.9726885','VERSION_BUILD=26885']
assert all(not k.startswith('app/src/main/java/') for k in allow)
assert (C/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt').read_bytes()==(B/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt').read_bytes()
assert 'original 1.2.5' not in '\n'.join(allow)
new_shader=C/'app/src/main/cpp/iris26864/Iris26885WronskiChromaGuide.comp'
assert new_shader.exists() and new_shader.read_text().startswith('#version 450')
interop=(C/'app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc').read_text()
assert 'if(sr) bOnChromaEvidence.reset(' in interop and 'bWavelet->record(cmd,rgb.view(),result.outputView' in interop
bridge=(C/'app/src/main/cpp/iris26864/Iris26864Wronski2xSingleOwnerBridge.cpp').read_text()
assert bridge.index('packedKernel.record(')<bridge.index('amaze.record(')<bridge.index('chromaGuide.record(')
assert bridge.count('computeWriteReadBarrier(cmd);')>=4
print('PASS 26885 2009->2010 exact source, 8 allowed, 2002 protected incl 26884 white and Spektra, B ON ownership')
