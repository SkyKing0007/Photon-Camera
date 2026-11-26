from pathlib import Path
import re
R=Path(__file__).resolve().parent
old=(R/'26987_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_text()
marker='      - name: Fetch ONLY actual successful 26986 Actions artifact 15043211082\n'
a,b=old.split(marker)
prefix=a.replace(a.splitlines()[0],'name: Photon 26988 V2 - C OFF exposure and C ON legacy native highlight trial',1).replace('      - TRIGGER_26987.txt','      - TRIGGER_26988.txt',1)
step='      - name: Seal exact 26988 V2 C OFF exposure and C ON legacy highlights\n        run: |\n          python3 -S build_26988_incremental.py seal\n          python3 -S test_26988_source.py --payload\n          python3 -S test_26988_legacy_highlight_host.py --payload\n          python3 -S test_26988_patches.py --payload\n          python3 -S test_26988_sealed_negatives.py\n          python3 -S test_26988_workflow_refs.py\n'
tail=re.sub(r'26986|26987',lambda m:{'26986':'26987','26987':'26988'}[m[0]],marker+b).replace('15043211082','15052860769').replace('2650 protected','2647 protected').replace('photon-26988-c-rawlens-color-reference','photon-26988-v2-c-exposure-legacy-highlights').replace('0.9726987-26988','0.9726988-26988').replace('test_26987_native_host.py','test_26986_native_host.py').replace('          python3 -S verify_26988_native_glsl.py --compile\n','          python3 -S verify_26988_native_glsl.py --compile\n          python3 -S verify_26988_preview_glsl.py --compile\n')
expected=prefix+step+tail
assert (R/'.github/workflows/build-26988-change-aware.yml').read_text()==expected
assert expected.count('actions/upload-artifact@v4')==1
assert 'ART_ID=15052860769' in (R/'build_26988_incremental.py').read_text()
print('PASS exact 26987 historical prefix and mandatory original real compiler/cache/artifact gates plus new preview compiler gate')
