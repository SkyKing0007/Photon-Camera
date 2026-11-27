#!/usr/bin/env python3
from pathlib import Path
import re
R=Path(__file__).resolve().parent
def expected():
 old=(R/'26996_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_text()
 marker='      - name: Fetch ONLY actual successful 26996 Actions artifact 15171988393\n'
 oldmarker='      - name: Fetch ONLY actual successful 26995 Actions artifact 15165115817\n'
 a,b=old.split(oldmarker)
 prefix=a.replace(a.splitlines()[0],'name: Photon 26997 - C ON shutter and noise telemetry',1).replace('      - TRIGGER_26996.txt','      - TRIGGER_26997.txt',1)
 step='      - name: Seal exact 26997 C ON shutter and noise telemetry\n        run: |\n          python3 -S build_26997_incremental.py seal\n          python3 -S test_26997_source.py --payload\n          python3 -S test_26997_patches.py --payload\n          python3 -S test_26997_sealed_negatives.py\n          python3 -S test_26997_workflow_refs.py\n'
 tail=re.sub(r'26995|26996',lambda m:{'26995':'26996','26996':'26997'}[m[0]],oldmarker+b).replace('15165115817','15171988393').replace('2666 protected','2671 protected').replace('0.9726996-26997','0.9726997-26997').replace('photon-26997-c-shutter-rawlens-noise','photon-26997-c-on-shutter-noise-telemetry').replace('C shutter and learned noise source','C ON shutter and noise telemetry source').replace('          python3 -S test_26996_native_host.py\n','          python3 -S test_26995_native_host.py\n')
 assert tail.startswith(marker)
 return prefix+step+tail
if __name__=='__main__':
 e=expected();assert (R/'.github/workflows/build-26997-change-aware.yml').read_text()==e
 assert e.count('actions/upload-artifact@v4')==1 and e.count(':app:assembleDebug --stacktrace')==1 and e.count('      - TRIGGER_26997.txt')==1 and 'ART_ID=15171988393' in (R/'build_26997_incremental.py').read_text()
 print('PASS exact successful 26996 historical workflow prefix and preserved compiler/cache/assembly gates')
