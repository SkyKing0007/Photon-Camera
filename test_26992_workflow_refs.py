#!/usr/bin/env python3
from pathlib import Path
import re
R=Path(__file__).resolve().parent
def expected():
 old=(R/'26991_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_text()
 marker='      - name: Fetch ONLY actual successful 26990 Actions artifact 15093245586\n'
 a,b=old.split(marker)
 prefix=a.replace(a.splitlines()[0],'name: Photon 26992 - C OFF highlight-only Ultra HDR gain map',1).replace('      - TRIGGER_26991.txt','      - TRIGGER_26992.txt',1)
 step='      - name: Seal exact 26992 C OFF highlight-only Ultra HDR gain map\n        run: |\n          python3 -S build_26992_incremental.py seal\n          python3 -S test_26992_source.py --payload\n          python3 -S test_26992_patches.py --payload\n          python3 -S test_26992_sealed_negatives.py\n          python3 -S test_26992_workflow_refs.py\n'
 tail=re.sub(r'26990|26991',lambda m:{'26990':'26991','26991':'26992'}[m[0]],marker+b).replace('15093245586','15134174529').replace('2653 protected','2657 protected').replace('photon-26992-c-independent-legacy-chroma-mgc-text','photon-26992-c-off-highlight-only-ultra-hdr').replace('C private LK-R 2.4.20 source','C OFF gain-map source')
 return prefix+step+tail
if __name__=='__main__':
 e=expected();assert (R/'.github/workflows/build-26992-change-aware.yml').read_text()==e
 assert e.count('actions/upload-artifact@v4')==1 and e.count(':app:assembleDebug --stacktrace')==1 and e.count('      - TRIGGER_26992.txt')==1
 assert 'ART_ID=15134174529' in (R/'build_26992_incremental.py').read_text()
 print('PASS exact successful 26991 workflow prefix; unchanged compiler/cache/artifact steps; additive 26992 gates')
