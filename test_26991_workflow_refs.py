#!/usr/bin/env python3
from pathlib import Path
import re
R=Path(__file__).resolve().parent
def expected():
 old=(R/'26990_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_text()
 marker='      - name: Fetch ONLY actual successful 26989 Actions artifact 15089832905\n'
 a,b=old.split(marker)
 prefix=a.replace(a.splitlines()[0],'name: Photon 26991 - C independent legacy chroma pipeline and MGC descriptions',1).replace('      - TRIGGER_26990.txt','      - TRIGGER_26991.txt',1)
 step='''      - name: Seal exact 26991 independent C legacy chroma processing and text-only MGC descriptions
        run: |
          python3 -S build_26991_incremental.py seal
          python3 -S test_26991_source.py --payload
          python3 -S test_26991_patches.py --payload
          python3 -S test_26991_sealed_negatives.py
          python3 -S test_26991_workflow_refs.py
'''
 tail=re.sub(r'26989|26990',lambda m:{'26989':'26990','26990':'26991'}[m[0]],marker+b).replace('15089832905','15093245586').replace('photon-26991-c-legacy-highlights-hdr-off-default-c','photon-26991-c-independent-legacy-chroma-mgc-text').replace('0.9726990-26990','0.9726991-26991')
 return prefix+step+tail
if __name__=='__main__':
 e=expected();actual=(R/'.github/workflows/build-26991-change-aware.yml').read_text();assert actual==e
 assert e.count('actions/upload-artifact@v4')==1 and e.count(':app:assembleDebug --stacktrace')==1
 assert e.count('      - TRIGGER_26991.txt')==1 and 'ART_ID=15093245586' in (R/'build_26991_incremental.py').read_text()
 print('PASS exact successful 26990 historical prefix; unchanged real compiler, cache and artifact procedure; additive 26991 gates')
