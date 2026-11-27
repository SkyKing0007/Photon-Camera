#!/usr/bin/env python3
from pathlib import Path
import re
R=Path(__file__).resolve().parent
def expected():
 old=(R/'26997_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_text()
 marker='      - name: Fetch ONLY actual successful 26996 Actions artifact 15171988393\n'
 a,b=old.split(marker)
 prefix=a.replace(a.splitlines()[0],'name: Photon 26998 - C OFF bjzhou 1.29.1 denoise and color',1).replace('      - TRIGGER_26997.txt','      - TRIGGER_26998.txt',1)
 step='      - name: Seal exact 26998 C OFF donor upgrade\n        run: |\n          python3 -S build_26998_incremental.py seal\n          python3 -S test_26998_source.py --payload\n          python3 -S test_26998_patches.py --payload\n          python3 -S test_26998_sealed_negatives.py\n          python3 -S test_26998_workflow_refs.py\n'
 tail=re.sub(r'26996|26997',lambda m:{'26996':'26997','26997':'26998'}[m[0]],marker+b).replace('15171988393','15207204004').replace('2671 protected','2661 protected').replace('0.9726997-26998','0.9726998-26998').replace('photon-26998-c-on-shutter-noise-telemetry','photon-26998-c-off-bjzhou-1291-denoise-color').replace('C ON shutter and noise telemetry source','C OFF bjzhou 1.29.1 denoise and color source')
 return prefix+step+tail
if __name__=='__main__':
 e=expected();assert (R/'.github/workflows/build-26998-change-aware.yml').read_text()==e
 assert e.count('actions/upload-artifact@v4')==1 and e.count(':app:assembleDebug --stacktrace')==1 and e.count('      - TRIGGER_26998.txt')==1 and 'ART_ID=15207204004' in (R/'build_26998_incremental.py').read_text()
 print('PASS exact successful 26997 historical workflow prefix and preserved compiler/cache/assembly gates')
