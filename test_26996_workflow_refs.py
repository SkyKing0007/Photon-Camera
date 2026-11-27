#!/usr/bin/env python3
from pathlib import Path
import re
R=Path(__file__).resolve().parent
def expected():
 old=(R/'26995_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_text()
 marker='      - name: Fetch ONLY actual successful 26995 Actions artifact 15165115817\n'
 oldmarker='      - name: Fetch ONLY actual successful 26994 Actions artifact 15160159682\n'
 a,b=old.split(oldmarker)
 prefix=a.replace(a.splitlines()[0],'name: Photon 26996 - C shutter and RawLens learned noise',1).replace('      - TRIGGER_26995.txt','      - TRIGGER_26996.txt',1)
 step='      - name: Seal exact 26996 C shutter and RawLens learned noise\n        run: |\n          python3 -S build_26996_incremental.py seal\n          python3 -S test_26996_source.py --payload\n          python3 -S test_26996_patches.py --payload\n          python3 -S test_26996_sealed_negatives.py\n          python3 -S test_26996_workflow_refs.py\n'
 tail=re.sub(r'26994|26995',lambda m:{'26994':'26995','26995':'26996'}[m[0]],oldmarker+b).replace('15160159682','15165115817').replace('2621 protected','2666 protected').replace('0.9726995-26996','0.9726996-26996').replace('photon-26996-c-on-rawlens-2458-lkr-lite','photon-26996-c-shutter-rawlens-noise').replace('C ON LK-R Lite 2.4.58 source','C shutter and learned noise source').replace('          python3 -S test_26996_native_host.py\n','          python3 -S test_26995_native_host.py\n')
 assert tail.startswith(marker)
 return prefix+step+tail
if __name__=='__main__':
 e=expected();assert (R/'.github/workflows/build-26996-change-aware.yml').read_text()==e
 assert e.count('actions/upload-artifact@v4')==1 and e.count(':app:assembleDebug --stacktrace')==1 and e.count('      - TRIGGER_26996.txt')==1 and 'ART_ID=15165115817' in (R/'build_26996_incremental.py').read_text()
 print('PASS exact successful 26995 historical workflow prefix and preserved compiler/cache/assembly gates')
