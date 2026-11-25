from pathlib import Path
import sys
R=Path(__file__).resolve().parent
old=(R/'26984_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_text()
marker='      - name: Fetch ONLY actual successful 26983 Actions artifact 14982944252\n'
a,b=old.split(marker)
prefix=a.replace(a.splitlines()[0],'name: Photon 26985 V2 - C private RawLens 2.4.20 LK-R 50MP JPG Linear DNG HDR Auto',1).replace('      - TRIGGER_26984.txt','      - TRIGGER_26985.txt',1)
step='      - name: Seal exact 26985 C private LK-R source and single-reconstruction outputs\n        run: |\n          python3 -S build_26985_incremental.py seal\n          python3 -S test_26985_source.py --payload\n          python3 -S test_26985_patches.py --payload\n          python3 -S test_26985_sealed_negatives.py\n          python3 -S test_26985_workflow_refs.py\n'
tail=(marker+b).replace('26984','26985').replace('26983','26984').replace('14982944252','14987424135').replace('2481 protected','2474 protected').replace('C settings correction','C private LK-R 2.4.20 source').replace('photon-26985-c-mgc-slider-settings','photon-26985-c-lkr2420-linear-dng')
tail=tail.replace('          bash compile_26985_con_shaders.sh\n','          bash compile_26985_con_shaders.sh\n          python3 -S verify_26985_native_glsl.py --compile\n')
tail=tail.replace('          python3 -S build_26985_incremental.py regress\n','          python3 -S build_26985_incremental.py regress\n          python3 -S test_26985_native_host.py\n',1)
expected=prefix+step+tail
wf=R/'.github/workflows/build-26985-change-aware.yml'
if '--emit' in sys.argv:wf.parent.mkdir(parents=True,exist_ok=True);wf.write_text(expected)
else:
 assert wf.read_text()==expected,'historical prefix or compiler/assemble/publish tail changed'
 assert expected.count('actions/upload-artifact@v4')==1
 builder=(R/'build_26985_incremental.py').read_text()
 assert builder.count('actions/artifacts/{ART_ID}/zip')==1 and 'ART_ID=14987424135' in builder
 print('PASS exact 26984 V2 workflow historical prefix and compiler/assembly tail plus private Vulkan gate')
