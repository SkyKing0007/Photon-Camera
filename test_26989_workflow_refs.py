from pathlib import Path
import re
R=Path(__file__).resolve().parent
old=(R/'26988_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_text()
marker='      - name: Fetch ONLY actual successful 26987 Actions artifact 15052860769\n'
a,b=old.split(marker)
prefix=a.replace(a.splitlines()[0],'name: Photon 26989 - C Motion memory RAW and C ON HDR OFF',1).replace('      - TRIGGER_26988.txt','      - TRIGGER_26989.txt',1)
step='      - name: Seal exact 26989 C Motion memory RAW and C ON latest highlight HDR OFF\n        run: |\n          python3 -S build_26989_incremental.py seal\n          python3 -S test_26989_source.py --payload\n          python3 -S test_26989_raw_memory_host.py --payload\n          python3 -S test_26989_highlight_host.py --payload\n          python3 -S test_26989_patches.py --payload\n          python3 -S test_26989_sealed_negatives.py\n          python3 -S test_26989_workflow_refs.py\n'
tail=re.sub(r'26987|26988',lambda m:{'26987':'26988','26988':'26989'}[m[0]],marker+b).replace('15052860769','15077480661').replace('2647 protected','2649 protected').replace('photon-26989-v2-c-exposure-legacy-highlights','photon-26989-c-memory-raw-hdr-off').replace('0.9726988-26989','0.9726989-26989')
expected=prefix+step+tail
assert (R/'.github/workflows/build-26989-change-aware.yml').read_text()==expected
assert expected.count('actions/upload-artifact@v4')==1
assert 'ART_ID=15077480661' in (R/'build_26989_incremental.py').read_text()
print('PASS exact successful 26988 historical prefix, all prior gates retained, additive 26989 host checks')
