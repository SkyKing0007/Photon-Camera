from pathlib import Path
import re
R=Path(__file__).resolve().parent
old=(R/'26985_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_text()
marker='      - name: Fetch ONLY actual successful 26984 Actions artifact 14987424135\n'
a,b=old.split(marker)
prefix=a.replace(a.splitlines()[0],'name: Photon 26986 - C RawLens 2.4.20 fidelity and independent C OFF Bayer DNG',1).replace('      - TRIGGER_26985.txt','      - TRIGGER_26986.txt',1)
step='      - name: Seal 26986 C RawLens fidelity and OFF DNG source\n        run: |\n          python3 -S build_26986_incremental.py seal\n          python3 -S test_26986_source.py --payload\n          python3 -S test_26986_patches.py --payload\n          python3 -S test_26986_sealed_negatives.py\n          python3 -S test_26986_workflow_refs.py\n'
tail=re.sub(r'26984|26985',lambda m:{'26984':'26985','26985':'26986'}[m[0]],marker+b).replace('14987424135','14994528316').replace('2474 protected','2639 protected').replace('photon-26986-c-lkr2420-linear-dng','photon-26986-c-rawlens-fidelity-dng').replace('0.9726985-26986','0.9726986-26986')
expected=prefix+step+tail
assert (R/'.github/workflows/build-26986-change-aware.yml').read_text()==expected
assert expected.count('actions/upload-artifact@v4')==1
assert 'ART_ID=14994528316' in (R/'build_26986_incremental.py').read_text()
print('PASS exact successful 26985 V2 historical prefix and compiler, Gradle, cache and publication tail')
