from pathlib import Path
import re
R=Path(__file__).resolve().parent
old=(R/'26986_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_text()
marker='      - name: Fetch ONLY actual successful 26985 Actions artifact 14994528316\n'
a,b=old.split(marker)
prefix=a.replace(a.splitlines()[0],'name: Photon 26987 - C RawLens 2.4.20 restore calibrated chroma protections',1).replace('      - TRIGGER_26986.txt','      - TRIGGER_26987.txt',1)
step='      - name: Seal 26987 C ON preserved Lab, white and reference calibration\n        run: |\n          python3 -S build_26987_incremental.py seal\n          python3 -S test_26987_source.py --payload\n          python3 -S test_26987_patches.py --payload\n          python3 -S test_26987_sealed_negatives.py\n          python3 -S test_26987_workflow_refs.py\n'
tail=re.sub(r'26985|26986',lambda m:{'26985':'26986','26986':'26987'}[m[0]],marker+b).replace('14994528316','15043211082').replace('2639 protected','2650 protected').replace('photon-26987-c-rawlens-fidelity-dng','photon-26987-c-rawlens-color-reference').replace('0.9726986-26987','0.9726987-26987').replace('test_26987_native_host.py','test_26986_native_host.py')
expected=prefix+step+tail
assert (R/'.github/workflows/build-26987-change-aware.yml').read_text()==expected
assert expected.count('actions/upload-artifact@v4')==1
assert 'ART_ID=15043211082' in (R/'build_26987_incremental.py').read_text()
print('PASS exact 26986 historical verification prefix, real shader/compiler/Gradle/cache/artifact gates retained')
