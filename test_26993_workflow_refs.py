#!/usr/bin/env python3
from pathlib import Path
import re
R=Path(__file__).resolve().parent
def expected():
 old=(R/'26992_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_text()
 marker='      - name: Fetch ONLY actual successful 26991 Actions artifact 15134174529\n';a,b=old.split(marker)
 prefix=a.replace(a.splitlines()[0],'name: Photon 26993 - C shadows, physical RAW owner and Spektra binned',1).replace('      - TRIGGER_26992.txt','      - TRIGGER_26993.txt',1)
 step='      - name: Seal exact 26993 C shadows, physical RAW owner and Spektra binned capture\n        run: |\n          python3 -S build_26993_incremental.py seal\n          python3 -S test_26993_source.py --payload\n          python3 -S test_26993_patches.py --payload\n          python3 -S test_26993_sealed_negatives.py\n          python3 -S test_26993_workflow_refs.py\n'
 tail=re.sub(r'26991|26992',lambda m:{'26991':'26992','26992':'26993'}[m[0]],marker+b).replace('15134174529','15143754755').replace('2657 protected','2652 protected').replace('0.9726992-26993','0.9726993-26993').replace('photon-26993-c-off-highlight-only-ultra-hdr','photon-26993-c-shadows-pixel-owner-spektra-binned').replace('C OFF gain-map source','C shadows, physical owner and Spektra source')
 return prefix+step+tail
if __name__=='__main__':
 e=expected();assert (R/'.github/workflows/build-26993-change-aware.yml').read_text()==e
 assert e.count('actions/upload-artifact@v4')==1 and e.count(':app:assembleDebug --stacktrace')==1 and e.count('      - TRIGGER_26993.txt')==1 and 'ART_ID=15143754755' in (R/'build_26993_incremental.py').read_text()
 print('PASS exact successful 26992 workflow prefix; unchanged compiler/cache/artifact steps; additive 26993 gates')
