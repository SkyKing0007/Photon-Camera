#!/usr/bin/env python3
"""Exact executed 26989 historical prefix, unchanged compiler/cache/artifact tail except version and additive gates."""
from pathlib import Path
import re,sys
R=Path(__file__).resolve().parent

def expected():
 old=(R/'26989_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_text()
 marker='      - name: Fetch ONLY actual successful 26988 Actions artifact 15077480661\n'
 a,b=old.split(marker)
 prefix=a.replace(a.splitlines()[0],'name: Photon 26990 - C legacy highlights HDR OFF and C default',1).replace('      - TRIGGER_26989.txt','      - TRIGGER_26990.txt',1)
 step='''      - name: Seal exact 26990 C legacy highlights and default C without HDR brackets
        run: |
          python3 -S build_26990_incremental.py seal
          python3 -S test_26990_source.py --payload
          python3 -S test_26990_settings_host.py --payload
          python3 -S test_26990_patches.py --payload
          python3 -S test_26990_sealed_negatives.py
          python3 -S test_26990_workflow_refs.py
'''
 tail=re.sub(r'26988|26989',lambda m:{'26988':'26989','26989':'26990'}[m[0]],marker+b).replace('15077480661','15089832905').replace('2649 protected','2653 protected').replace('photon-26990-c-memory-raw-hdr-off','photon-26990-c-legacy-highlights-hdr-off-default-c').replace('0.9726989-26990','0.9726990-26990')
 # Reuse exact previous compiler scripts/inventories (all shader bytes invariant).
 # The sealed wrapper replaces only the current source guard; all real compiler commands are retained.
 prev='''          bash compile_26990_shaders.sh
          bash compile_26990_con_shaders.sh
          python3 -S verify_26990_native_glsl.py --compile
          python3 -S verify_26990_preview_glsl.py --compile'''
 assert tail.count(prev)==1;tail=tail.replace(prev,'          python3 -S compile_26990_all.py')
 return prefix+step+tail
if __name__=='__main__':
 e=expected();actual=(R/'.github/workflows/build-26990-change-aware.yml').read_text();assert actual==e
 assert e.count('actions/upload-artifact@v4')==1 and e.count(':app:assembleDebug --stacktrace')==1
 assert e.count('      - TRIGGER_26990.txt')==1 and 'ART_ID=15089832905' in (R/'build_26990_incremental.py').read_text()
 print('PASS exact 26989 executed historical prefix and compiler/cache/artifact tail, additive 26990 gates')
