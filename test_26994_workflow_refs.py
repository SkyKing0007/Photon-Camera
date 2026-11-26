#!/usr/bin/env python3
from pathlib import Path
import re
R=Path(__file__).resolve().parent
def expected():
 old=(R/'26993_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_text()
 marker='      - name: Fetch ONLY actual successful 26992 Actions artifact 15143754755\n';a,b=old.split(marker)
 prefix=a.replace(a.splitlines()[0],'name: Photon 26994 - C OFF adaptive watermark only',1).replace('      - TRIGGER_26993.txt','      - TRIGGER_26994.txt',1)
 step='      - name: Seal exact 26994 C OFF adaptive watermark only\n        run: |\n          python3 -S build_26994_incremental.py seal\n          python3 -S test_26994_source.py --payload\n          python3 -S test_26994_patches.py --payload\n          python3 -S test_26994_sealed_negatives.py\n          python3 -S test_26994_workflow_refs.py\n'
 tail=re.sub(r'26992|26993',lambda m:{'26992':'26993','26993':'26994'}[m[0]],marker+b).replace('15143754755','15158094133').replace('2652 protected','2656 protected').replace('0.9726993-26994','0.9726994-26994').replace('photon-26994-c-shadows-pixel-owner-spektra-binned','photon-26994-c-off-adaptive-watermark').replace('C shadows, physical owner and Spektra source','C OFF adaptive watermark source').replace('          python3 -S test_26975_v5_asset_host.py --live\n','')
 return prefix+step+tail
if __name__=='__main__':
 e=expected();assert (R/'.github/workflows/build-26994-change-aware.yml').read_text()==e
 assert e.count('actions/upload-artifact@v4')==1 and e.count(':app:assembleDebug --stacktrace')==1 and e.count('      - TRIGGER_26994.txt')==1 and 'ART_ID=15158094133' in (R/'build_26994_incremental.py').read_text()
 print('PASS exact successful 26993 historical workflow prefix and preserved compiler/cache/assembly gates')
