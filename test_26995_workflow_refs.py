#!/usr/bin/env python3
from pathlib import Path
import re
R=Path(__file__).resolve().parent
def expected():
 old=(R/'26994_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_text()
 marker='      - name: Fetch ONLY actual successful 26993 Actions artifact 15158094133\n';a,b=old.split(marker)
 prefix=a.replace(a.splitlines()[0],'name: Photon 26995 - C ON RawLens 2.4.58 LK-R Lite',1).replace('      - TRIGGER_26994.txt','      - TRIGGER_26995.txt',1)
 step='      - name: Seal exact 26995 C ON LK-R Lite 2.4.58 only\n        run: |\n          python3 -S build_26995_incremental.py seal\n          python3 -S test_26995_source.py --payload\n          python3 -S test_26995_patches.py --payload\n          python3 -S test_26995_sealed_negatives.py\n          python3 -S test_26995_workflow_refs.py\n'
 tail=re.sub(r'26993|26994',lambda m:{'26993':'26994','26994':'26995'}[m[0]],marker+b).replace('15158094133','15160159682').replace('2656 protected','2621 protected').replace('0.9726994-26995','0.9726995-26995').replace('photon-26995-c-off-adaptive-watermark','photon-26995-c-on-rawlens-2458-lkr-lite').replace('C OFF adaptive watermark source','C ON LK-R Lite 2.4.58 source').replace('          python3 -S test_26986_native_host.py\n','          python3 -S test_26995_native_host.py\n')
 return prefix+step+tail
if __name__=='__main__':
 e=expected();assert (R/'.github/workflows/build-26995-change-aware.yml').read_text()==e
 assert e.count('actions/upload-artifact@v4')==1 and e.count(':app:assembleDebug --stacktrace')==1 and e.count('      - TRIGGER_26995.txt')==1 and 'ART_ID=15160159682' in (R/'build_26995_incremental.py').read_text()
 print('PASS exact successful 26994 historical workflow prefix and preserved compiler/cache/assembly gates')
