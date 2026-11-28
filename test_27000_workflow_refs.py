from pathlib import Path
import re
R=Path(__file__).resolve().parent
def expected():
 old=(R/'26999_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_text()
 marker='      - name: Fetch ONLY actual successful 26998 Actions artifact 15217638463\n'
 a,b=old.split(marker)
 prefix=a.replace(a.splitlines()[0],'name: Photon 27000 - C OFF Sabre chroma and lens sensitivity',1).replace('      - TRIGGER_26999.txt','      - TRIGGER_27000.txt',1)
 step='      - name: Seal exact 27000 C OFF and settings handoff\n        run: |\n          python3 -S build_27000_incremental.py seal\n          python3 -S test_27000_source.py --payload\n          python3 -S test_27000_patches.py --payload\n          python3 -S test_27000_sealed_negatives.py\n          python3 -S test_27000_workflow_refs.py\n'
 tail=re.sub(r'26998|26999',lambda m:{'26998':'26999','26999':'27000'}[m[0]],marker+b).replace('15217638463','15223663522').replace('2696 protected','2697 protected').replace('0.9726999-27000','0.9727000-27000').replace('photon-27000-ui-xml-configs','photon-27000-c-off-sabre-lens-sensitivity').replace('UI and XML configuration source','C OFF Sabre chroma and lens sensitivity source')
 return prefix+step+tail
if __name__=='__main__':
 e=expected();assert (R/'.github/workflows/build-27000-change-aware.yml').read_text()==e
 assert e.count('actions/upload-artifact@v4')==1 and e.count(':app:assembleDebug --stacktrace')==1 and e.count('      - TRIGGER_27000.txt')==1 and 'ART_ID=15223663522' in (R/'build_27000_incremental.py').read_text()
 print('PASS exact successful 26999 historical workflow prefix and preserved compiler/cache/assembly gates')
