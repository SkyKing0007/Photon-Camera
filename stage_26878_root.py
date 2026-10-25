#!/usr/bin/env python3
"""26878 flat-root upload staging; verified original 26877 historical validator migration."""
from pathlib import Path
from hashlib import sha256
ROOT=Path(__file__).resolve().parent
EXPECTED = {
    'ImageSaver.java': ('handoff_payload_26878/app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java', '32639d8da660d37f4f9697e33651384e411bccf0d9b19774cf678a6223b828f2'),
    'PhotonMotionMgc1271Bridge.kt': ('handoff_payload_26878/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt', '614ac6387a618352286b22f9acf248b32d1cf79438d8028d7ce2234fd373196a'),
    'FrameGeometrySnapshot.kt': ('handoff_payload_26878/app/src/main/java/com/unspektrawesome/capture/FrameGeometrySnapshot.kt', '88e0036c0a7e2257c274206c1ed4c07c4643fb723aaed54ecc252890925fb8c3'),
    'RawVulkanPreviewController.kt': ('handoff_payload_26878/app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt', 'c28aa2169c86e8e6bce2df3ca772df4885a0f2917c95accb6c4cd5530b3377c6'),
    'version.properties': ('handoff_payload_26878/app/version.properties', '1006ebccb33ab228b3a601c81de3f5feb2e236d951e56e6be52993f17db80d8b'),
    '26877_runtime_ownership_spektra.py': ('regressions/26877_runtime_ownership_spektra.py','493253d77e249aa3a921d2501a5467832a0dd5d5f1c8713b5bcbd022442cecb5'),
    '26878_runtime_ownership_spektra.py': ('regressions/26878_runtime_ownership_spektra.py', '4523ea5cecfa85672fd530442a729b72c73238a9049e8aa91a456d5778245ae1'),
}
assert len(EXPECTED)==7
for src_name,(dest_name,pin) in EXPECTED.items():
    src=ROOT/src_name;dst=ROOT/dest_name
    assert src.is_file() and not src.is_symlink(),('missing root source, never synthesize',src_name)
    assert sha256(src.read_bytes()).hexdigest()==pin,('flat source hash mismatch',src_name)
    assert not dst.is_symlink(),('target symbolic link',dest_name)
    if dst.exists():
        assert dst.is_file() and dst.read_bytes()==src.read_bytes(),('staged collision',dest_name)
    else:
        dst.parent.mkdir(parents=True,exist_ok=True)
        dst.write_bytes(src.read_bytes())
    assert sha256(dst.read_bytes()).hexdigest()==pin
assert len([x for x in (ROOT/'handoff_payload_26878').rglob('*') if x.is_file()])==5
assert not any(x.is_relative_to(ROOT/'app') for x in (ROOT/'handoff_payload_26878').rglob('*'))
print('PASS 26878 five runtime root-drop and SHA-pinned historical 26877 validator migration')
