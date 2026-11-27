#!/usr/bin/env python3
from pathlib import Path
import re
R=Path(__file__).resolve().parent
def expected():
 old=(R/'26998_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_text()
 marker='      - name: Fetch ONLY actual successful 26997 Actions artifact 15207204004\n'
 a,b=old.split(marker)
 prefix=a.replace(a.splitlines()[0],'name: Photon 26999 - UI and XML configuration',1).replace('      - TRIGGER_26998.txt','      - TRIGGER_26999.txt',1)
 step='      - name: Seal exact 26999 UI and XML configuration handoff\n        run: |\n          python3 -S build_26999_incremental.py seal\n          python3 -S test_26999_source.py --payload\n          python3 -S test_26999_patches.py --payload\n          python3 -S test_26999_sealed_negatives.py\n          python3 -S test_26999_workflow_refs.py\n'
 tail=re.sub(r'26997|26998',lambda m:{'26997':'26998','26998':'26999'}[m[0]],marker+b).replace('15207204004','15217638463').replace('2661 protected','2696 protected').replace('0.9726998-26999','0.9726999-26999').replace('photon-26999-c-off-bjzhou-1291-denoise-color','photon-26999-ui-xml-configs').replace('C OFF bjzhou 1.29.1 denoise and color source','UI and XML configuration source')
 return prefix+step+tail
if __name__=='__main__':
 e=expected();assert (R/'.github/workflows/build-26999-change-aware.yml').read_text()==e
 assert e.count('actions/upload-artifact@v4')==1 and e.count(':app:assembleDebug --stacktrace')==1 and e.count('      - TRIGGER_26999.txt')==1 and 'ART_ID=15217638463' in (R/'build_26999_incremental.py').read_text()
 print('PASS exact successful 26998 historical workflow prefix and preserved compiler/cache/assembly gates')
