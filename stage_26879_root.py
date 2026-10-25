#!/usr/bin/env python3
"""26879 deterministic 5 runtime flat-root files and all 3 real history validators.
Never modify app/src directly; transformed candidate first.
"""
from pathlib import Path
from hashlib import sha256
ROOT=Path(__file__).resolve().parent
EXPECTED = {'GlesIris26858BNoiseHighlight.kt': ('handoff_payload_26879/app/src/main/java/com/hinnka/mycamera/processor/GlesIris26858BNoiseHighlight.kt', '2089863802de66a6981ad53f45698226f5454f5907c389192cf612ecd744049c'), 'HdrxProcessor.java': ('handoff_payload_26879/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java', '1c237e6e1ec8fec06a45af7d67731c4fc722302a662036f99064305ecae82ef6'), 'SpektraModeController.java': ('handoff_payload_26879/app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraModeController.java', 'ccb7060c7be7210b83f157a4926027692f9fd0fbdeea5a5440c39e2bc2823df1'), 'RawPreviewPlanSelector.kt': ('handoff_payload_26879/app/src/main/java/com/unspektrawesome/preview/RawPreviewPlanSelector.kt', '7b603ae0337bedc693a9ed4057eb279eb3332b0a731fd51df3f3c5bfc76626bf'), 'version.properties': ('handoff_payload_26879/app/version.properties', 'a9b0c7065d83cbc378f2fb3bee2ef11265db845c5c2050884d7432a18f822aa5'), '26877_runtime_ownership_spektra.py': ('regressions/26877_runtime_ownership_spektra.py', '493253d77e249aa3a921d2501a5467832a0dd5d5f1c8713b5bcbd022442cecb5'), '26878_runtime_ownership_spektra.py': ('regressions/26878_runtime_ownership_spektra.py', '4523ea5cecfa85672fd530442a729b72c73238a9049e8aa91a456d5778245ae1'), '26879_runtime_ownership_spektra.py': ('regressions/26879_runtime_ownership_spektra.py', '60fa0a85a9606115e6fdd92d283e87a43abf87a9f5e51f0f661e476f351ffa26')}
assert len(EXPECTED)==8
for src_name,(dest_name,pin) in EXPECTED.items():
    src=ROOT/src_name;dst=ROOT/dest_name
    assert src.is_file() and not src.is_symlink(),('missing root source, never synthesize',src_name)
    assert sha256(src.read_bytes()).hexdigest()==pin,('flat source hash mismatch',src_name)
    assert not dst.is_symlink(),('target symbolic link',dest_name)
    if dst.exists():
        assert dst.is_file() and dst.read_bytes()==src.read_bytes(),('staged collision',dest_name)
    else:
        dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(src.read_bytes())
    assert sha256(dst.read_bytes()).hexdigest()==pin
assert len([x for x in (ROOT/'handoff_payload_26879').rglob('*') if x.is_file()])==5
assert not any(x.is_relative_to(ROOT/'app') for x in (ROOT/'handoff_payload_26879').rglob('*'))
print('PASS 26879 5 runtime root-drop and SHA-pinned 26877, 26878, 26879 validators')
